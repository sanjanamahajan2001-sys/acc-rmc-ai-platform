"""Tier 1 Validation Rules Registration Module.

This module provides factory functions to instantiate and register all Tier 1 structural and required field rules.
"""

from typing import List, Optional
from src.database.dictionary import CanonicalFieldID
from src.validation.enums import ValidationSeverity
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.validators.required_field_validator import RequiredFieldValidator
from src.validation.validators.structural_schema_validator import StructuralSchemaValidator


def register_tier1_rules(registry: Optional[ValidationRuleRegistry] = None) -> List[str]:
    """Instantiate and register all Tier 1 structural and required field rules into target registry.

    Returns list of registered rule IDs.
    """
    target_reg = registry or get_default_validation_registry()
    registered_ids: List[str] = []

    # 1. Register Structural Schema Validator
    struct_val = StructuralSchemaValidator()
    try:
        target_reg.register_rule(struct_val)
        registered_ids.append(struct_val.rule_id)
    except Exception:  # Handle already registered gracefully
        pass

    # 2. Register Mandatory Required Field Validators
    mandatory_fields = [
        ("FIELD_BATCH_ID", ValidationSeverity.CRITICAL),
        ("FIELD_PLANT_ID", ValidationSeverity.CRITICAL),
        ("FIELD_RECIPE_ID", ValidationSeverity.CRITICAL),
        ("FIELD_BATCH_DATETIME", ValidationSeverity.CRITICAL),
        ("FIELD_ACTUAL_CEMENT_KG", ValidationSeverity.ERROR),
        ("FIELD_ACTUAL_WATER_KG", ValidationSeverity.ERROR),
    ]

    for fid, sev in mandatory_fields:
        req_val = RequiredFieldValidator(target_field_id=fid, severity=sev)
        try:
            target_reg.register_rule(req_val)
            registered_ids.append(req_val.rule_id)
        except Exception:
            pass

    return registered_ids
