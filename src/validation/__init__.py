"""Shared Multi-Tier Data Quality & Validation Engine Package Exports.

This package provides foundational DTO contracts, enums, constants, execution contexts, rule registry, Tier 1-5 validators, orchestrator, and quarantine contract for WS-03.3.
"""

from src.validation.audit import ValidationExecutionReport as AuditValidationExecutionReport
from src.validation.base_rule import BaseValidationRule
from src.validation.constants import (
    DEFAULT_CEMENT_MAX_KG,
    DEFAULT_CEMENT_MIN_KG,
    DEFAULT_SLUMP_MAX_MM,
    DEFAULT_SLUMP_MIN_MM,
    DEFAULT_STRENGTH_28D_MAX_MPA,
    DEFAULT_STRENGTH_28D_MIN_MPA,
    DEFAULT_TEMP_MAX_C,
    DEFAULT_TEMP_MIN_C,
    DEFAULT_WATER_MAX_KG,
    DEFAULT_WATER_MIN_KG,
    DEFAULT_WC_RATIO_MAX,
    DEFAULT_WC_RATIO_MIN,
    ERR_CODE_PREFIX,
    WARN_CODE_PREFIX,
    WEIGHT_CRITICAL_PENALTY,
    WEIGHT_ERROR_PENALTY,
    WEIGHT_INFO_PENALTY,
    WEIGHT_WARNING_PENALTY,
)
from src.validation.contracts import (
    DatasetValidationResult,
    FieldErrorDetail,
    RowValidationResult,
    ValidationContext,
    ValidationResult,
    ValidationSummaryReport,
)
from src.validation.dataset_validator import DatasetValidator
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.exceptions import (
    DuplicateRuleException,
    InvalidRuleConfigurationException,
    RuleRegistrationException,
    UnknownRuleException,
    ValidationRegistryException,
)
from src.validation.execution_report import ValidationConfigurationSnapshot, ValidationExecutionReport
from src.validation.metadata import RuleMetadata
from src.validation.metrics import ValidationMetricsCollector
from src.validation.performance_profiler import ValidationPerformanceProfiler
from src.validation.quality_score import QualityScoreCalculator
from src.validation.quarantine_contract import QuarantinePayloadContract
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.result_aggregator import ValidationResultAggregator
from src.validation.rule_context import RuleExecutionContext
from src.validation.rules import (
    register_all_validation_rules,
    register_tier1_rules,
    register_tier2_rules,
    register_tier3_rules,
    register_tier4_rules,
    register_tier5_rules,
)
from src.validation.shared_validation_engine import SharedValidationEngine
from src.validation.statistics import ValidationStatisticsService
from src.validation.validation_pipeline import ValidationPipeline
from src.validation.validators.cross_field_validator import CrossFieldValidator
from src.validation.validators.engineering_unit_validator import EngineeringUnitValidator
from src.validation.validators.enumeration_validator import EnumerationValidator
from src.validation.validators.numeric_range_validator import NumericRangeValidator
from src.validation.validators.primitive_type_validator import PrimitiveTypeValidator
from src.validation.validators.referential_integrity_validator import ReferentialIntegrityValidator
from src.validation.validators.required_field_validator import RequiredFieldValidator
from src.validation.validators.structural_schema_validator import StructuralSchemaValidator
from src.validation.version import CONTRACTS_VERSION, RULE_REGISTRY_VERSION, VALIDATION_ENGINE_VERSION

__all__ = [
    # Contracts & Contexts
    "FieldErrorDetail",
    "ValidationContext",
    "RowValidationResult",
    "ValidationSummaryReport",
    "DatasetValidationResult",
    "ValidationResult",
    "RuleMetadata",
    "RuleExecutionContext",
    "QuarantinePayloadContract",

    # Orchestrator & Engine
    "SharedValidationEngine",
    "ValidationPipeline",
    "ValidationResultAggregator",
    "QualityScoreCalculator",

    # Performance, Diagnostics & Telemetry
    "ValidationPerformanceProfiler",
    "ValidationExecutionReport",
    "ValidationConfigurationSnapshot",
    "ValidationMetricsCollector",
    "ValidationStatisticsService",

    # Version Constants
    "VALIDATION_ENGINE_VERSION",
    "RULE_REGISTRY_VERSION",
    "CONTRACTS_VERSION",

    # Base Rule & Registry
    "BaseValidationRule",
    "ValidationRuleRegistry",
    "get_default_validation_registry",

    # Tier 1-5 Validators & Rules
    "StructuralSchemaValidator",
    "RequiredFieldValidator",
    "PrimitiveTypeValidator",
    "EngineeringUnitValidator",
    "NumericRangeValidator",
    "EnumerationValidator",
    "CrossFieldValidator",
    "ReferentialIntegrityValidator",
    "DatasetValidator",
    "register_tier1_rules",
    "register_tier2_rules",
    "register_tier3_rules",
    "register_tier4_rules",
    "register_tier5_rules",
    "register_all_validation_rules",

    # Exceptions
    "ValidationRegistryException",
    "DuplicateRuleException",
    "UnknownRuleException",
    "InvalidRuleConfigurationException",
    "RuleRegistrationException",

    # Enums
    "ValidationSeverity",
    "ValidationTier",
    "ValidationCategory",

    # Constants
    "ERR_CODE_PREFIX",
    "WARN_CODE_PREFIX",
    "WEIGHT_CRITICAL_PENALTY",
    "WEIGHT_ERROR_PENALTY",
    "WEIGHT_INFO_PENALTY",
    "WEIGHT_WARNING_PENALTY",
    "DEFAULT_SLUMP_MIN_MM",
    "DEFAULT_SLUMP_MAX_MM",
    "DEFAULT_WC_RATIO_MIN",
    "DEFAULT_WC_RATIO_MAX",
    "DEFAULT_CEMENT_MIN_KG",
    "DEFAULT_CEMENT_MAX_KG",
    "DEFAULT_WATER_MIN_KG",
    "DEFAULT_WATER_MAX_KG",
    "DEFAULT_STRENGTH_28D_MAX_MPA",
    "DEFAULT_STRENGTH_28D_MAX_MPA",
    "DEFAULT_TEMP_MIN_C",
    "DEFAULT_TEMP_MAX_C",
]
