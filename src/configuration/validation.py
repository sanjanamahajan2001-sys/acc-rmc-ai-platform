"""Startup Configuration Validation Gate and Self-Health Diagnostic.

This module provides the mandatory `validate_platform_configuration()` gate executed
before application startup in `server.py` or systemd, and the `run_platform_self_health_check()`
diagnostic reporter.
"""

import os
from pathlib import Path
import sys
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from src.configuration.base import VALID_ENVIRONMENTS, get_paths
from src.configuration.subsystems import DatabaseType, PlatformSettings, get_platform_settings
from src.exceptions.technical import (
    ConfigurationException,
    InvalidConfigurationException,
    MissingEnvironmentVariableException,
)
from src.logging import get_logger

logger = get_logger("src.configuration.validation", component="configuration")


class ComponentHealthStatus(BaseModel):
    """Component-level health status contract."""

    component: str = Field(description="Subsystem component name.")
    status: str = Field(description="Health status ('OK', 'WARNING', 'ERROR').")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic details.")


class PlatformHealthReport(BaseModel):
    """Structured platform self-health diagnostic report."""

    overall_status: str = Field(description="Overall platform health ('HEALTHY', 'UNHEALTHY').")
    environment: str = Field(description="Active environment profile.")
    python_version: str = Field(description="Python runtime version.")
    components: List[ComponentHealthStatus] = Field(default_factory=list, description="Subsystem health results.")


def _validate_runtime_directories() -> None:
    """Validate all platform paths exist, are directories, and have read/write permissions."""
    paths = get_paths()
    paths.ensure_runtime_directories()

    for path in paths.get_all_runtime_directories():
        if not path.exists():
            raise InvalidConfigurationException(
                parameter_name="runtime_path",
                message=f"Runtime directory does not exist: '{path}'",
            )
        if not path.is_dir():
            raise InvalidConfigurationException(
                parameter_name="runtime_path",
                message=f"Path exists but is not a directory: '{path}'",
            )
        if not os.access(path, os.R_OK):
            raise ConfigurationException(
                message=f"Directory is not readable: '{path}'",
                error_code="ACC_CONFIG_PATH_NOT_READABLE",
            )
        if not os.access(path, os.W_OK):
            raise ConfigurationException(
                message=f"Directory is not writable: '{path}'",
                error_code="ACC_CONFIG_PATH_NOT_WRITABLE",
            )


def validate_platform_configuration(settings: PlatformSettings | None = None) -> None:
    """Validate platform configuration and environment readiness before application startup.

    Raises:
        InvalidConfigurationException: If settings parameter or value validation fails.
        ConfigurationException: If environment, permissions, or system prerequisites fail.
    """
    logger.info("Startup platform configuration validation started")

    target_settings = settings if settings is not None else get_platform_settings()

    # 1. Python Version Check (>= 3.12)
    if sys.version_info < (3, 12):
        raise ConfigurationException(
            message=f"Unsupported Python version {sys.version_split()[0]}. Python 3.12+ required.",
            error_code="ACC_CONFIG_UNSUPPORTED_PYTHON",
        )

    # 2. Environment Profile Check
    env = target_settings.base.environment.value.lower()
    if env not in VALID_ENVIRONMENTS:
        raise InvalidConfigurationException(
            parameter_name="environment",
            message=f"Invalid environment profile '{env}'.",
        )

    # 3. Path Registry & Directory Permissions Check
    _validate_runtime_directories()

    # 4. Security Settings Validation
    sec = target_settings.security
    if not sec.jwt_secret_key:
        raise MissingEnvironmentVariableException(
            env_var_name="JWT_SECRET_KEY",
            message="JWT secret key must be configured.",
        )
    if env == "production" and (
        sec.jwt_secret_key == "CHANGE_ME_PRODUCTION_JWT_SECRET_32_CHARS_MIN"
        or len(sec.jwt_secret_key) < 32
    ):
        raise InvalidConfigurationException(
            parameter_name="jwt_secret_key",
            message="Production JWT secret key must be at least 32 characters long and not use default.",
        )
    if sec.jwt_algorithm not in ["HS256", "HS384", "HS512", "RS256"]:
        raise InvalidConfigurationException(
            parameter_name="jwt_algorithm",
            message=f"Unsupported JWT algorithm '{sec.jwt_algorithm}'.",
        )

    # 5. Database Settings Validation
    db = target_settings.database
    if db.database_type == DatabaseType.SQLITE and not db.sqlite_path:
        raise InvalidConfigurationException(
            parameter_name="sqlite_path",
            message="SQLite path must be configured when database_type is sqlite.",
        )
    if db.database_type == DatabaseType.POSTGRESQL and not db.postgresql_host:
        raise InvalidConfigurationException(
            parameter_name="postgresql_host",
            message="PostgreSQL host must be configured when database_type is postgresql.",
        )

    # 6. Logging Settings Validation
    log_cfg = target_settings.logging
    if log_cfg.log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise InvalidConfigurationException(
            parameter_name="log_level",
            message=f"Invalid log level '{log_cfg.log_level}'.",
        )

    # 7. Subsystem Threshold Sanity Checks
    if target_settings.ingestion.max_upload_size_mb <= 0:
        raise InvalidConfigurationException(
            parameter_name="max_upload_size_mb",
            message="max_upload_size_mb must be greater than 0.",
        )
    if target_settings.ai.prediction_timeout_sec <= 0:
        raise InvalidConfigurationException(
            parameter_name="prediction_timeout_sec",
            message="prediction_timeout_sec must be greater than 0.",
        )

    logger.info(
        "Startup platform configuration validation passed successfully",
        environment=env,
        database_type=db.database_type.value,
        log_level=log_cfg.log_level,
    )


def run_platform_self_health_check(settings: PlatformSettings | None = None) -> PlatformHealthReport:
    """Run platform self-health diagnostic and return structured report."""
    target_settings = settings if settings is not None else get_platform_settings()
    env = target_settings.base.environment.value
    components_health: List[ComponentHealthStatus] = []
    is_healthy = True

    # 1. Configuration Validation Diagnostic
    try:
        validate_platform_configuration(target_settings)
        components_health.append(
            ComponentHealthStatus(
                component="configuration",
                status="OK",
                details={"message": "All configuration schemas and permissions valid."},
            )
        )
    except Exception as err:
        is_healthy = False
        components_health.append(
            ComponentHealthStatus(
                component="configuration",
                status="ERROR",
                details={"error": str(err)},
            )
        )

    # 2. Paths Diagnostic
    paths = get_paths()
    components_health.append(
        ComponentHealthStatus(
            component="paths",
            status="OK",
            details={
                "project_root": str(paths.project_root),
                "runtime_dirs_count": len(paths.get_all_runtime_directories()),
            },
        )
    )

    # 3. Database Config Readiness
    components_health.append(
        ComponentHealthStatus(
            component="database_config",
            status="OK",
            details={
                "engine": target_settings.database.database_type.value,
                "dsn_configured": bool(target_settings.database.database_url),
            },
        )
    )

    # 4. Feature Flags Readiness
    components_health.append(
        ComponentHealthStatus(
            component="feature_flags",
            status="OK",
            details={"flags_count": len(target_settings.feature_flags.model_dump())},
        )
    )

    report = PlatformHealthReport(
        overall_status="HEALTHY" if is_healthy else "UNHEALTHY",
        environment=env,
        python_version=sys.version.split()[0],
        components=components_health,
    )

    logger.info(
        "Platform self-health check completed",
        overall_status=report.overall_status,
        environment=report.environment,
    )
    return report
