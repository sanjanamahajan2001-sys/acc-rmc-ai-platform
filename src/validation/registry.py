"""Validation Rule Registry.

This module provides the thread-safe ValidationRuleRegistry managing registration, lookup, ordering, and filtering.
"""

from threading import RLock
from typing import Dict, List, Optional, Tuple
from src.logging import get_logger
from src.validation.base_rule import BaseValidationRule
from src.validation.enums import ValidationCategory, ValidationTier
from src.validation.exceptions import (
    DuplicateRuleException,
    InvalidRuleConfigurationException,
    RuleRegistrationException,
    UnknownRuleException,
)

logger = get_logger("src.validation.registry", component="validation")


class ValidationRuleRegistry:
    """Thread-safe, version-aware registry for managing validation rules."""

    def __init__(self) -> None:
        self._lock = RLock()
        # Storage keyed by (rule_id, version)
        self._rules: Dict[Tuple[str, str], BaseValidationRule] = {}

    def register_rule(self, rule: BaseValidationRule) -> None:
        """Register a validation rule. Raises DuplicateRuleException if (rule_id, version) already exists."""
        if not isinstance(rule, BaseValidationRule):
            raise RuleRegistrationException("Object to register must inherit from BaseValidationRule.")

        key = (rule.rule_id, rule.version)
        with self._lock:
            if key in self._rules:
                raise DuplicateRuleException(rule.rule_id, rule.version)

            self._rules[key] = rule
            logger.info("Validation rule registered successfully", rule_id=rule.rule_id, version=rule.version, tier=rule.validation_tier.value)

    def unregister_rule(self, rule_id: str, version: str = "1.0.0") -> None:
        """Unregister a rule by rule_id and version."""
        key = (rule_id, version)
        with self._lock:
            if key not in self._rules:
                raise UnknownRuleException(rule_id)
            del self._rules[key]
            logger.info("Validation rule unregistered", rule_id=rule_id, version=version)

    def get_rule(self, rule_id: str, version: Optional[str] = None) -> BaseValidationRule:
        """Retrieve rule by rule_id. If version is None, retrieves latest version."""
        with self._lock:
            if version is not None:
                key = (rule_id, version)
                if key not in self._rules:
                    raise UnknownRuleException(rule_id)
                return self._rules[key]

            # Find latest version matching rule_id
            matching = [r for (rid, ver), r in self._rules.items() if rid == rule_id]
            if not matching:
                raise UnknownRuleException(rule_id)

            # Return rule with highest version string
            matching.sort(key=lambda r: r.version, reverse=True)
            return matching[0]

    def get_rules(self) -> List[BaseValidationRule]:
        """Return all registered rules."""
        with self._lock:
            return list(self._rules.values())

    def get_enabled_rules(self) -> List[BaseValidationRule]:
        """Return all enabled rules ordered deterministically."""
        with self._lock:
            enabled = [r for r in self._rules.values() if r.enabled]
            return self._sort_rules_deterministically(enabled)

    def get_rules_for_tier(self, tier: ValidationTier) -> List[BaseValidationRule]:
        """Return all enabled rules matching specified ValidationTier."""
        with self._lock:
            matching = [r for r in self._rules.values() if r.enabled and r.validation_tier == tier]
            return self._sort_rules_deterministically(matching)

    def get_rules_for_category(self, category: ValidationCategory) -> List[BaseValidationRule]:
        """Return all enabled rules matching specified ValidationCategory."""
        with self._lock:
            matching = [r for r in self._rules.values() if r.enabled and r.validation_category == category]
            return self._sort_rules_deterministically(matching)

    def get_execution_order(self) -> List[BaseValidationRule]:
        """Return all active enabled rules sorted deterministically by Tier -> Execution Priority -> Rule ID."""
        with self._lock:
            enabled = [r for r in self._rules.values() if r.enabled]
            return self._sort_rules_deterministically(enabled)

    def _sort_rules_deterministically(self, rules: List[BaseValidationRule]) -> List[BaseValidationRule]:
        """Sort rules deterministically: Tier Order -> Execution Priority -> Rule ID."""
        tier_order_map = {
            ValidationTier.TIER_1_STRUCTURAL: 1,
            ValidationTier.TIER_2_PRIMITIVES: 2,
            ValidationTier.TIER_3_RANGES_ENUMS: 3,
            ValidationTier.TIER_4_CROSS_FIELD_REFERENTIAL: 4,
            ValidationTier.TIER_5_CROSS_ENTITY_DATASET: 5,
        }

        return sorted(
            rules,
            key=lambda r: (
                tier_order_map.get(r.validation_tier, 99),
                r.execution_priority,
                r.rule_id,
                r.version,
            ),
        )


# Global singleton registry instance
_global_registry = ValidationRuleRegistry()


def get_default_validation_registry() -> ValidationRuleRegistry:
    """Return the global default ValidationRuleRegistry singleton."""
    return _global_registry
