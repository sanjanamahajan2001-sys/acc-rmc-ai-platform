"""Engineering Unit Validator.

This module provides Tier 2 validation verifying correctness of canonical engineering units.
"""

from typing import Any, Optional
from src.database.dictionary import CanonicalFieldDefinition, CanonicalFieldID, get_canonical_dictionary
from src.database.types import EngineeringUnit
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class EngineeringUnitValidator(BaseValidationRule):
    """Tier 2 Validator verifying that canonical engineering unit metadata matches dictionary definitions."""

    def __init__(self, target_field_id: str) -> None:
        self.target_field_id = target_field_id
        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T2_UNIT_{target_field_id}",
            rule_name=f"Engineering Unit Validator [{target_field_id}]",
            description=f"Verifies canonical engineering unit metadata correctness for '{target_field_id}'.",
            tier=ValidationTier.TIER_2_PRIMITIVES,
            category=ValidationCategory.PRODUCTION,
            severity=ValidationSeverity.ERROR,
            version="1.0.0",
            execution_priority=20,
            tags=["unit", "tier2", target_field_id.lower()],
        )
        super().__init__(metadata)
        self._registry = get_canonical_dictionary()
        self._field_def: Optional[CanonicalFieldDefinition] = None

        # Resolve field definition safely from enum or string key
        try:
            enum_key = CanonicalFieldID[target_field_id] if isinstance(target_field_id, str) and target_field_id in CanonicalFieldID.__members__ else target_field_id
            if self._registry.has_field(enum_key):  # type: ignore
                self._field_def = self._registry.get_field(enum_key)  # type: ignore
        except Exception:
            pass

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate engineering unit metadata against canonical dictionary."""
        if self._field_def is None or self._field_def.unit is None:
            return None

        target_unit_enum = self._field_def.unit
        target_unit_str = target_unit_enum.value.lower()
        orig_header: Optional[str] = None
        actual_unit: Optional[str] = None

        if context.row is not None and context.row.audit_records:
            for audit in context.row.audit_records:
                if audit.canonical_field_id == self.target_field_id:
                    orig_header = audit.original_header
                    actual_unit = audit.canonical_unit
                    break

        if actual_unit is None:
            return None  # Unit metadata not attached

        clean_actual = actual_unit.strip().lower()

        # Check unit equality
        if clean_actual != target_unit_str:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_INCOMPATIBLE_UNIT",
                message=f"Canonical unit for '{self.target_field_id}' must be '{target_unit_enum.value}', got '{actual_unit}'.",
                invalid_value=actual_unit,
                category=self.validation_category,
            )

        return None
