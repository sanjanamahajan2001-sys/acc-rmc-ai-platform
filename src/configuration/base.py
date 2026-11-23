"""Base Platform Settings and Environment Profile Loader Engine.

This module provides `BasePlatformSettings` inheriting from `pydantic-settings`
and manages multi-environment profile loading (development, qa, staging, production).
"""

from enum import Enum
import os
from pathlib import Path
from typing import ClassVar, Dict, Set
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from src.configuration.paths import PlatformPaths
from src.exceptions.technical import InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.configuration.base", component="configuration")


class EnvironmentProfile(str, Enum):
    """Allowed Platform Environment Profiles."""

    DEVELOPMENT = "development"
    QA = "qa"
    STAGING = "staging"
    PRODUCTION = "production"


VALID_ENVIRONMENTS: Set[str] = {e.value for e in EnvironmentProfile}


class BasePlatformSettings(BaseSettings):
    """Base Platform Settings using pydantic-settings. Immutable (frozen=True)."""

    environment: EnvironmentProfile = Field(
        default=EnvironmentProfile.DEVELOPMENT,
        validation_alias="ACC_RMC_ENV",
        alias="environment",
        description="Active platform deployment environment profile.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )


_SETTINGS_SINGLETON: BasePlatformSettings | None = None
_PATHS_SINGLETON: PlatformPaths | None = None


def get_paths(root_override: Path | None = None) -> PlatformPaths:
    """Return singleton instance of dynamic PlatformPaths."""
    global _PATHS_SINGLETON
    if _PATHS_SINGLETON is None or root_override is not None:
        _PATHS_SINGLETON = PlatformPaths(root_override=root_override)
        _PATHS_SINGLETON.ensure_runtime_directories()
    return _PATHS_SINGLETON


def load_base_platform_settings(
    env_override: str | None = None,
    root_dir: Path | None = None,
) -> BasePlatformSettings:
    """Load BasePlatformSettings with dotenv precedence.

    Precedence:
        1. Explicit parameters / Environment Variables
        2. .env.<environment> file
        3. .env file
        4. Default fallback values
    """
    paths = get_paths(root_override=root_dir)
    env_name = (
        env_override.lower()
        if env_override
        else os.environ.get("ACC_RMC_ENV", "development").lower()
    )

    if env_name not in VALID_ENVIRONMENTS:
        raise InvalidConfigurationException(
            parameter_name="ACC_RMC_ENV",
            message=f"Invalid environment profile '{env_name}'. Allowed: {sorted(list(VALID_ENVIRONMENTS))}",
        )

    # Dotenv files precedence
    env_files = [
        paths.project_root / f".env.{env_name}",
        paths.project_root / ".env",
    ]
    existing_env_files = [str(f) for f in env_files if f.exists()]

    try:
        # Create settings instance with dotenv files and explicit environment parameter
        settings = BasePlatformSettings(
            environment=EnvironmentProfile(env_name),
            _env_file=existing_env_files if existing_env_files else None,
            _env_file_encoding="utf-8",
        )
        logger.info(
            "Base settings loaded",
            environment=settings.environment.value,
            env_files=existing_env_files,
        )
        return settings
    except Exception as err:
        raise InvalidConfigurationException(
            parameter_name="ACC_RMC_ENV",
            message=f"Failed to load platform settings: {err}",
        ) from err


def get_base_settings() -> BasePlatformSettings:
    """Return singleton instance of BasePlatformSettings."""
    global _SETTINGS_SINGLETON
    if _SETTINGS_SINGLETON is None:
        _SETTINGS_SINGLETON = load_base_platform_settings()
    return _SETTINGS_SINGLETON
