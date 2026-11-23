"""Tier 4 Validation Rules Registration Module.

This module provides factory functions to instantiate and register all Tier 4 cross-field and referential rules.
"""

from typing import List, Optional
from src.validation.enums import ValidationSeverity
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.validators.cross_field_validator import CrossFieldValidator
from src.validation.validators.referential_integrity_validator import ReferentialIntegrityValidator


def register_tier4_rules(registry: Optional[ValidationRuleRegistry] = None) -> List[str]:
    """Instantiate and register all Tier 4 cross-field and referential rules into target registry.

    Returns list of registered rule IDs.
    """
    target_reg = registry or get_default_validation_registry()
    registered_ids: List[str] = []

    # 1. Register Configuration-Driven Cross-Field Validators
    cf1 = CrossFieldValidator(
        rule_id="ACC_VAL_T4_WC_RATIO_CHECK",
        rule_name="W/C Ratio Consistency Check",
        description="Verifies reported water-cement ratio matches calculated water / cement value.",
        target_field_id="FIELD_WATER_CEMENT_RATIO",
        required_fields=["FIELD_ACTUAL_CEMENT_KG", "FIELD_ACTUAL_WATER_KG", "FIELD_WATER_CEMENT_RATIO"],
        operator="RATIO_TOLERANCE",
        tolerance=0.05,
        severity=ValidationSeverity.ERROR,
    )
    cf2 = CrossFieldValidator(
        rule_id="ACC_VAL_T4_TIMESTAMP_ORDER",
        rule_name="Batch/Dispatch Timestamp Sequence Check",
        description="Verifies batch datetime is earlier than or equal to dispatch datetime.",
        target_field_id="FIELD_DISPATCH_DATETIME",
        required_fields=["FIELD_BATCH_DATETIME", "FIELD_DISPATCH_DATETIME"],
        operator="DATETIME_ORDER",
        severity=ValidationSeverity.ERROR,
    )

    for cf in [cf1, cf2]:
        try:
            target_reg.register_rule(cf)
            registered_ids.append(cf.rule_id)
        except Exception:
            pass

    # 2. Register Referential Integrity Validators
    ref_fields = [
        "FIELD_PLANT_ID",
        "FIELD_RECIPE_ID",
        "FIELD_CUSTOMER_ID",
    ]

    for fid in ref_fields:
        ref_val = ReferentialIntegrityValidator(target_field_id=fid)
        try:
            target_reg.register_rule(ref_val)
            registered_ids.append(ref_val.rule_id)
        except Exception:
            pass

    return registered_ids
