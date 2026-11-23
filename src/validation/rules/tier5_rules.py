"""Tier 5 Validation Rules Registration Module.

This module provides factory functions to instantiate and register all Tier 5 dataset-level rules.
"""

from typing import List, Optional
from src.validation.dataset_validator import DatasetValidator
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry


def register_tier5_rules(registry: Optional[ValidationRuleRegistry] = None) -> List[str]:
    """Instantiate and register all Tier 5 dataset rules into target registry.

    Returns list of registered rule IDs.
    """
    target_reg = registry or get_default_validation_registry()
    registered_ids: List[str] = []

    dup_val = DatasetValidator()
    try:
        target_reg.register_rule(dup_val)
        registered_ids.append(dup_val.rule_id)
    except Exception:
        pass

    return registered_ids
