"""Typed Feature Flag Engine & Toggle Registry.

This module provides the `FeatureFlag` enum taxonomy, immutable `FeatureFlagsSettings` model
with `ACC_RMC_ENABLE_*` environment variable override resolution, and the feature evaluation engine.
"""

from enum import Enum
from typing import ClassVar, Dict, Set
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from src.exceptions.technical import ConfigurationException, InvalidConfigurationException
from src.logging import get_logger

logger = get_logger("src.configuration.feature_flags", component="configuration")


class FeatureFlag(str, Enum):
    """Platform Typed Feature Flag Registry for compile-time safety and autocomplete."""

    ENABLE_AI = "enable_ai"
    ENABLE_ML_TRAINING = "enable_ml_training"
    ENABLE_MIX_OPTIMIZER = "enable_mix_optimizer"
    ENABLE_PREDICTIONS = "enable_predictions"
    ENABLE_DASHBOARD = "enable_dashboard"
    ENABLE_REPORTING = "enable_reporting"
    ENABLE_MANUAL_BATCH_ENTRY = "enable_manual_batch_entry"
    ENABLE_EXCEL_IMPORT = "enable_excel_import"
    ENABLE_FT7_IMPORT = "enable_ft7_import"
    ENABLE_AUDIT_LOGGING = "enable_audit_logging"
    ENABLE_SCHEDULER = "enable_scheduler"
    ENABLE_API_DOCS = "enable_api_docs"
    ENABLE_BACKGROUND_TASKS = "enable_background_tasks"
    ENABLE_CACHE = "enable_cache"
    ENABLE_STRICT_QA_GATE = "enable_strict_qa_gate"
    ENABLE_DRIFT_MONITORING = "enable_drift_monitoring"
    ENABLE_RETRAINING = "enable_retraining"


class FeatureFlagsSettings(BaseSettings):
    """Immutable Feature Flag Settings Model with ACC_RMC_ENABLE_* environment overrides."""

    enable_ai: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_AI")
    enable_ml_training: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_ML_TRAINING")
    enable_mix_optimizer: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_MIX_OPTIMIZER")
    enable_predictions: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_PREDICTIONS")
    enable_dashboard: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_DASHBOARD")
    enable_reporting: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_REPORTING")
    enable_manual_batch_entry: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_MANUAL_BATCH_ENTRY")
    enable_excel_import: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_EXCEL_IMPORT")
    enable_ft7_import: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_FT7_IMPORT")
    enable_audit_logging: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_AUDIT_LOGGING")
    enable_scheduler: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_SCHEDULER")
    enable_api_docs: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_API_DOCS")
    enable_background_tasks: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_BACKGROUND_TASKS")
    enable_cache: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_CACHE")
    enable_strict_qa_gate: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_STRICT_QA_GATE")
    enable_drift_monitoring: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_DRIFT_MONITORING")
    enable_retraining: bool = Field(default=True, validation_alias="ACC_RMC_ENABLE_RETRAINING")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="ignore",
        case_sensitive=False,
    )


_FEATURE_FLAGS_SINGLETON: FeatureFlagsSettings | None = None
_RUNTIME_MUTABLE_FLAGS: Dict[FeatureFlag, bool] = {}


def get_feature_flags() -> FeatureFlagsSettings:
    """Return singleton instance of FeatureFlagsSettings."""
    global _FEATURE_FLAGS_SINGLETON
    if _FEATURE_FLAGS_SINGLETON is None:
        _FEATURE_FLAGS_SINGLETON = FeatureFlagsSettings()
        logger.info("Feature flag settings initialized", summary=_FEATURE_FLAGS_SINGLETON.model_dump())
    return _FEATURE_FLAGS_SINGLETON


def is_feature_enabled(flag: FeatureFlag, environment: str = "production") -> bool:
    """Evaluate whether a feature flag is enabled.

    Args:
        flag: FeatureFlag enum taxonomy key.
        environment: Active environment profile string.

    Returns:
        bool: True if feature is enabled, False otherwise.
    """
    if not isinstance(flag, FeatureFlag):
        raise InvalidConfigurationException(
            parameter_name="flag",
            message=f"Invalid feature flag '{flag}'. Must be an instance of FeatureFlag enum.",
        )

    # Check runtime override dictionary if present
    if flag in _RUNTIME_MUTABLE_FLAGS:
        val = _RUNTIME_MUTABLE_FLAGS[flag]
        logger.info("Feature flag evaluated (runtime override)", flag=flag.value, enabled=val)
        return val

    flags_settings = get_feature_flags()
    val = getattr(flags_settings, flag.value, False)
    logger.info("Feature flag evaluated", flag=flag.value, enabled=val)
    return val


def enable_feature(flag: FeatureFlag, environment: str = "test") -> None:
    """Enable a feature flag at runtime (allowed in test/development environments only)."""
    if environment.lower() == "production":
        raise ConfigurationException(
            message="Runtime mutation of feature flags is prohibited in Production environment.",
            error_code="ACC_CONFIG_PROHIBITED_MUTATION",
        )
    if not isinstance(flag, FeatureFlag):
        raise InvalidConfigurationException(parameter_name="flag", message=f"Invalid feature flag '{flag}'.")
    _RUNTIME_MUTABLE_FLAGS[flag] = True
    logger.info("Feature flag enabled at runtime", flag=flag.value, environment=environment)


def disable_feature(flag: FeatureFlag, environment: str = "test") -> None:
    """Disable a feature flag at runtime (allowed in test/development environments only)."""
    if environment.lower() == "production":
        raise ConfigurationException(
            message="Runtime mutation of feature flags is prohibited in Production environment.",
            error_code="ACC_CONFIG_PROHIBITED_MUTATION",
        )
    if not isinstance(flag, FeatureFlag):
        raise InvalidConfigurationException(parameter_name="flag", message=f"Invalid feature flag '{flag}'.")
    _RUNTIME_MUTABLE_FLAGS[flag] = False
    logger.info("Feature flag disabled at runtime", flag=flag.value, environment=environment)


def reset_runtime_feature_flags() -> None:
    """Reset all runtime feature flag overrides (used in test suite teardown)."""
    global _RUNTIME_MUTABLE_FLAGS
    _RUNTIME_MUTABLE_FLAGS.clear()
