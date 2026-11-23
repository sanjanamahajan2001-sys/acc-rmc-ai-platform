"""Unit test suite for WS-01.5C Typed Feature Flag Engine & Toggle Registry."""

import os
import pytest
from src.configuration import (
    FeatureFlag,
    FeatureFlagsSettings,
    disable_feature,
    enable_feature,
    get_feature_flags,
    is_feature_enabled,
    reset_runtime_feature_flags,
)
from src.exceptions import ConfigurationException, InvalidConfigurationException


def setup_function() -> None:
    reset_runtime_feature_flags()


def test_feature_flag_enum_registry() -> None:
    assert FeatureFlag.ENABLE_AI.value == "enable_ai"
    assert FeatureFlag.ENABLE_DASHBOARD.value == "enable_dashboard"
    assert FeatureFlag.ENABLE_SCHEDULER.value == "enable_scheduler"
    assert FeatureFlag.ENABLE_FT7_IMPORT.value == "enable_ft7_import"


def test_feature_evaluation() -> None:
    assert is_feature_enabled(FeatureFlag.ENABLE_AI) is True
    assert is_feature_enabled(FeatureFlag.ENABLE_DASHBOARD) is True


def test_runtime_toggle_in_test_environment() -> None:
    disable_feature(FeatureFlag.ENABLE_DASHBOARD, environment="test")
    assert is_feature_enabled(FeatureFlag.ENABLE_DASHBOARD) is False

    enable_feature(FeatureFlag.ENABLE_DASHBOARD, environment="test")
    assert is_feature_enabled(FeatureFlag.ENABLE_DASHBOARD) is True


def test_prohibit_runtime_toggle_in_production() -> None:
    with pytest.raises(ConfigurationException) as exc_info:
        disable_feature(FeatureFlag.ENABLE_AI, environment="production")
    assert exc_info.value.error_code == "ACC_CONFIG_PROHIBITED_MUTATION"


def test_invalid_feature_flag_rejection() -> None:
    with pytest.raises(InvalidConfigurationException):
        is_feature_enabled("invalid_flag_string")  # type: ignore
