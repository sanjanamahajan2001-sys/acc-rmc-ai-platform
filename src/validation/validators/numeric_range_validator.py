"""Numeric Range Validator.

This module provides Tier 3 validation enforcing physical domain boundary limits for canonical numeric fields.
"""

from decimal import Decimal
from typing import Any, Optional
from src.database.dictionary import CanonicalFieldDefinition, CanonicalFieldID, get_canonical_dictionary
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class NumericRangeValidator(BaseValidationRule):
    """Tier 3 Validator verifying that canonical numeric values fall strictly within min/max domain limits."""

    def __init__(
        self,
        target_field_id: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        self.target_field_id = target_field_id
        self.min_value = min_value
        self.max_value = max_value
        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T3_RNG_{target_field_id}",
            rule_name=f"Numeric Range Validator [{target_field_id}]",
            description=f"Verifies canonical numeric value range boundaries for '{target_field_id}'.",
            tier=ValidationTier.TIER_3_RANGES_ENUMS,
            category=ValidationCategory.CONCRETE,
            severity=severity,
            version="1.0.0",
            execution_priority=10,
            tags=["range", "tier3", target_field_id.lower()],
        )
        super().__init__(metadata)
        self._registry = get_canonical_dictionary()
        self._field_def: Optional[CanonicalFieldDefinition] = None

        try:
            enum_key = CanonicalFieldID[target_field_id] if isinstance(target_field_id, str) and target_field_id in CanonicalFieldID.__members__ else target_field_id
            if self._registry.has_field(enum_key):  # type: ignore
                self._field_def = self._registry.get_field(enum_key)  # type: ignore
                if self.min_value is None and self._field_def.min_value is not None:
                    self.min_value = float(self._field_def.min_value)
                if self.max_value is None and self._field_def.max_value is not None:
                    self.max_value = float(self._field_def.max_value)
        except Exception:
            pass

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate numeric value against min/max boundary constraints."""
        val = value
        orig_header: Optional[str] = None

        if context.row is not None:
            if (val is None or val == "") and context.row.fields:
                val = context.row.fields.get(self.target_field_id)

            for audit in context.row.audit_records:
                if audit.canonical_field_id == self.target_field_id:
                    orig_header = audit.original_header
                    break

        if val is None:
            return None  # Null checks handled by Tier 1

        if not isinstance(val, (int, float, Decimal)) or isinstance(val, bool):
            return None  # Primitive type mismatch handled by Tier 2

        num_val = float(val)

        if self.min_value is not None and num_val < self.min_value:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_BELOW_MINIMUM",
                message=f"Value {num_val} for '{self.target_field_id}' is below minimum threshold of {self.min_value}.",
                invalid_value=val,
                category=self.validation_category,
            )

        if self.max_value is not None and num_val > self.max_value:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_ABOVE_MAXIMUM",
                message=f"Value {num_val} for '{self.target_field_id}' exceeds maximum threshold of {self.max_value}.",
                invalid_value=val,
                category=self.validation_category,
            )

        return None
