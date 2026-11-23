"""Rules package init file."""

from typing import Any, List, Optional
from src.validation.rules.tier1_rules import register_tier1_rules
from src.validation.rules.tier2_rules import register_tier2_rules
from src.validation.rules.tier3_rules import register_tier3_rules
from src.validation.rules.tier4_rules import register_tier4_rules
from src.validation.rules.tier5_rules import register_tier5_rules


def register_all_validation_rules(registry: Optional[Any] = None) -> List[str]:
    """Convenience helper to register all Tier 1 through Tier 5 validation rules."""
    ids: List[str] = []
    ids.extend(register_tier1_rules(registry))
    ids.extend(register_tier2_rules(registry))
    ids.extend(register_tier3_rules(registry))
    ids.extend(register_tier4_rules(registry))
    ids.extend(register_tier5_rules(registry))
    return ids


__all__ = [
    "register_tier1_rules",
    "register_tier2_rules",
    "register_tier3_rules",
    "register_tier4_rules",
    "register_tier5_rules",
    "register_all_validation_rules",
]
