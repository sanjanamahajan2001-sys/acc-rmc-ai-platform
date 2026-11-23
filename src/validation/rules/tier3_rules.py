"""Tier 3 Validation Rules Registration Module.

This module provides factory functions to instantiate and register all Tier 3 numeric range and enumeration rules.
"""

from typing import List, Optional
from src.database.dictionary import get_canonical_dictionary
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
)
from src.validation.enums import ValidationSeverity
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.validators.enumeration_validator import EnumerationValidator
from src.validation.validators.numeric_range_validator import NumericRangeValidator


def register_tier3_rules(registry: Optional[ValidationRuleRegistry] = None) -> List[str]:
    """Instantiate and register all Tier 3 range and enum rules into target registry.

    Returns list of registered rule IDs.
    """
    target_reg = registry or get_default_validation_registry()
    registered_ids: List[str] = []

    # 1. Register Physical Boundary Numeric Range Rules
    range_configs = [
        ("FIELD_SLUMP_MM", DEFAULT_SLUMP_MIN_MM, DEFAULT_SLUMP_MAX_MM, ValidationSeverity.WARNING),
        ("FIELD_WATER_CEMENT_RATIO", DEFAULT_WC_RATIO_MIN, DEFAULT_WC_RATIO_MAX, ValidationSeverity.ERROR),
        ("FIELD_ACTUAL_CEMENT_KG", DEFAULT_CEMENT_MIN_KG, DEFAULT_CEMENT_MAX_KG, ValidationSeverity.CRITICAL),
        ("FIELD_ACTUAL_WATER_KG", DEFAULT_WATER_MIN_KG, DEFAULT_WATER_MAX_KG, ValidationSeverity.CRITICAL),
        ("FIELD_CUBE_STRENGTH_28D_MPA", DEFAULT_STRENGTH_28D_MIN_MPA, DEFAULT_STRENGTH_28D_MAX_MPA, ValidationSeverity.ERROR),
        ("FIELD_CONCRETE_TEMP_C", DEFAULT_TEMP_MIN_C, DEFAULT_TEMP_MAX_C, ValidationSeverity.WARNING),
    ]

    for fid, min_v, max_v, sev in range_configs:
        rng_val = NumericRangeValidator(target_field_id=fid, min_value=min_v, max_value=max_v, severity=sev)
        try:
            target_reg.register_rule(rng_val)
            registered_ids.append(rng_val.rule_id)
        except Exception:
            pass

    # 2. Register Enumeration Rules
    enum_configs = [
        ("FIELD_BATCH_STATUS", ["COMPLETED", "IN_PROGRESS", "REJECTED", "CANCELLED"]),
        ("FIELD_PLANT_STATUS", ["ACTIVE", "INACTIVE", "MAINTENANCE"]),
    ]

    for fid, allowed in enum_configs:
        enum_val = EnumerationValidator(target_field_id=fid, allowed_values=allowed)
        try:
            target_reg.register_rule(enum_val)
            registered_ids.append(enum_val.rule_id)
        except Exception:
            pass

    return registered_ids
