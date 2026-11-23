"""Unit test suite for WS-01.5D Startup Configuration Validation Gate & Self-Health Diagnostic."""

import os
from pathlib import Path
import pytest
from src.configuration import (
    BasePlatformSettings,
    EnvironmentProfile,
    PlatformHealthReport,
    PlatformSettings,
    SecuritySettings,
    get_platform_settings,
    run_platform_self_health_check,
    validate_platform_configuration,
)
from src.exceptions import ConfigurationException, InvalidConfigurationException


def test_successful_startup_validation() -> None:
    settings = get_platform_settings()
    validate_platform_configuration(settings)


def test_production_jwt_secret_validation() -> None:
    base_prod = BasePlatformSettings(environment=EnvironmentProfile.PRODUCTION)
    sec_short = SecuritySettings(jwt_secret_key="short_secret")

    prod_settings = PlatformSettings(base=base_prod, security=sec_short)

    with pytest.raises(InvalidConfigurationException) as exc_info:
        validate_platform_configuration(prod_settings)
    assert exc_info.value.metadata["parameter_name"] == "jwt_secret_key"


def test_invalid_log_level_validation() -> None:
    ps = get_platform_settings()
    invalid_log = ps.model_copy(update={"logging": ps.logging.model_copy(update={"log_level": "INVALID_LEVEL"})})

    with pytest.raises(InvalidConfigurationException) as exc_info:
        validate_platform_configuration(invalid_log)
    assert exc_info.value.metadata["parameter_name"] == "log_level"


def test_invalid_subsystem_threshold_validation() -> None:
    ps = get_platform_settings()
    invalid_upload = ps.model_copy(update={"ingestion": ps.ingestion.model_copy(update={"max_upload_size_mb": 0})})

    with pytest.raises(InvalidConfigurationException) as exc_info:
        validate_platform_configuration(invalid_upload)
    assert exc_info.value.metadata["parameter_name"] == "max_upload_size_mb"


def test_platform_self_health_check() -> None:
    report = run_platform_self_health_check()
    assert isinstance(report, PlatformHealthReport)
    assert report.overall_status == "HEALTHY"
    assert len(report.components) >= 4
