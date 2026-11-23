"""Unit test suite for WS-01.5A Dynamic Path Registry & BaseSettings Engine."""

import os
from pathlib import Path
import pytest
from src.configuration import (
    BasePlatformSettings,
    EnvironmentProfile,
    PlatformPaths,
    get_base_settings,
    get_paths,
    load_base_platform_settings,
)
from src.exceptions import InvalidConfigurationException


def test_dynamic_path_registry() -> None:
    paths = get_paths()
    assert isinstance(paths.project_root, Path)
    assert paths.project_root.name == "acc-rmc-ai-platform"

    # Repository paths
    assert paths.config_dir == paths.project_root / "config"
    assert paths.src_dir == paths.project_root / "src"
    assert paths.tests_dir == paths.project_root / "tests"

    # Runtime paths
    assert paths.runtime_dir == paths.project_root / "runtime"
    assert paths.logs_dir == paths.project_root / "runtime" / "logs"
    assert paths.reports_dir == paths.project_root / "runtime" / "reports"
    assert paths.cache_dir == paths.project_root / "runtime" / "cache"
    assert paths.temp_dir == paths.project_root / "runtime" / "temp"
    assert paths.backups_dir == paths.project_root / "runtime" / "backups"
    assert paths.pid_dir == paths.project_root / "runtime" / "pid"
    assert paths.sockets_dir == paths.project_root / "runtime" / "sockets"


def test_idempotent_directory_initialization() -> None:
    paths = get_paths()
    paths.ensure_runtime_directories()
    for dir_path in paths.get_all_runtime_directories():
        assert dir_path.exists() is True


def test_environment_profile_resolution() -> None:
    settings = load_base_platform_settings(env_override="qa")
    assert settings.environment == EnvironmentProfile.QA

    with pytest.raises(InvalidConfigurationException):
        load_base_platform_settings(env_override="invalid_env")


def test_immutable_settings_model() -> None:
    settings = get_base_settings()
    with pytest.raises(TypeError):
        settings.environment = EnvironmentProfile.PRODUCTION  # type: ignore
