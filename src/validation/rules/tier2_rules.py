"""Tier 2 Validation Rules Registration Module.

This module provides factory functions to instantiate and register all Tier 2 primitive type and engineering unit rules.
"""

from typing import List, Optional
from src.database.dictionary import CanonicalFieldID, get_canonical_dictionary
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.validators.engineering_unit_validator import EngineeringUnitValidator
from src.validation.validators.primitive_type_validator import PrimitiveTypeValidator


def register_tier2_rules(registry: Optional[ValidationRuleRegistry] = None) -> List[str]:
    """Instantiate and register all Tier 2 primitive type and engineering unit rules into target registry.

    Returns list of registered rule IDs.
    """
    target_reg = registry or get_default_validation_registry()
    dictionary = get_canonical_dictionary()
    registered_ids: List[str] = []

    fields = dictionary.get_all_fields()

    for f_def in fields:
        fid_val = f_def.field_id.value

        # 1. Primitive Type Validator (Priority 10)
        prim_val = PrimitiveTypeValidator(target_field_id=fid_val)
        try:
            target_reg.register_rule(prim_val)
            registered_ids.append(prim_val.rule_id)
        except Exception:
            pass

        # 2. Engineering Unit Validator (Priority 20) if field has a canonical unit
        if f_def.unit is not None:
            unit_val = EngineeringUnitValidator(target_field_id=fid_val)
            try:
                target_reg.register_rule(unit_val)
                registered_ids.append(unit_val.rule_id)
            except Exception:
                pass

    return registered_ids
