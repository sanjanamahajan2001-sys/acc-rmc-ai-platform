"""Validation Package Enumerations.

This module provides standard enumerations for validation severity, pipeline execution tiers, and domain rule categories.
"""

from enum import Enum


class ValidationSeverity(str, Enum):
    """Validation failure severity level."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationTier(str, Enum):
    """Execution tier in the 5-tier validation pipeline."""

    TIER_1_STRUCTURAL = "TIER_1_STRUCTURAL"
    TIER_2_PRIMITIVES = "TIER_2_PRIMITIVES"
    TIER_3_RANGES_ENUMS = "TIER_3_RANGES_ENUMS"
    TIER_4_CROSS_FIELD_REFERENTIAL = "TIER_4_CROSS_FIELD_REFERENTIAL"
    TIER_5_CROSS_ENTITY_DATASET = "TIER_5_CROSS_ENTITY_DATASET"


class ValidationCategory(str, Enum):
    """Domain categorization for metadata tagging and rule filtering."""

    CONCRETE = "CONCRETE"
    LABORATORY = "LABORATORY"
    PRODUCTION = "PRODUCTION"
    SCADA = "SCADA"
    ERP = "ERP"
