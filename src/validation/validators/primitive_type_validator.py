"""Primitive Type Validator.

This module provides Tier 2 validation verifying primitive data type conformity for canonical values.
"""

from datetime import date, datetime, time
from decimal import Decimal
import math
from typing import Any, Optional
from src.database.dictionary import CanonicalFieldDefinition, CanonicalFieldID, DataTypeCategory, get_canonical_dictionary
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class PrimitiveTypeValidator(BaseValidationRule):
    """Tier 2 Validator verifying that canonical values match expected primitive Python types."""

    def __init__(self, target_field_id: str) -> None:
        self.target_field_id = target_field_id
        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T2_PRIM_{target_field_id}",
            rule_name=f"Primitive Type Validator [{target_field_id}]",
            description=f"Verifies canonical value primitive type conformity for '{target_field_id}'.",
            tier=ValidationTier.TIER_2_PRIMITIVES,
            category=ValidationCategory.PRODUCTION,
            severity=ValidationSeverity.ERROR,
            version="1.0.0",
            execution_priority=10,
            tags=["primitive", "tier2", target_field_id.lower()],
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
        """Validate primitive type conformity of canonical value."""
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
            return None  # Null checks are handled by Tier 1 RequiredFieldValidator

        if self._field_def is None:
            return None

        cat = self._field_def.category
        cat_str = cat.name if hasattr(cat, "name") else str(cat)

        # Numeric / Decimal validation
        if "NUMERIC" in cat_str or "DECIMAL" in cat_str or "QUANTITY" in cat_str or "STRENGTH" in cat_str:
            if not isinstance(val, (Decimal, int, float)) or isinstance(val, bool):
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    original_header=orig_header,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_PRIMITIVE_NOT_DECIMAL",
                    message=f"Value for '{self.target_field_id}' must be a numeric Decimal/float, got '{type(val).__name__}'.",
                    invalid_value=val,
                    category=self.validation_category,
                )

            # Reject NaN, Infinity, -Infinity
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    return FieldErrorDetail(
                        field_id=self.target_field_id,
                        original_header=orig_header,
                        rule_id=self.rule_id,
                        tier=self.validation_tier,
                        severity=self.severity,
                        error_code="ACC_VAL_NUMERIC_NAN_INF",
                        message=f"Numeric value for '{self.target_field_id}' cannot be NaN or Infinity.",
                        invalid_value=str(val),
                        category=self.validation_category,
                    )
            elif isinstance(val, Decimal):
                if val.is_nan() or val.is_infinite():
                    return FieldErrorDetail(
                        field_id=self.target_field_id,
                        original_header=orig_header,
                        rule_id=self.rule_id,
                        tier=self.validation_tier,
                        severity=self.severity,
                        error_code="ACC_VAL_NUMERIC_NAN_INF",
                        message=f"Numeric Decimal value for '{self.target_field_id}' cannot be NaN or Infinity.",
                        invalid_value=str(val),
                        category=self.validation_category,
                    )

        # Integer validation
        elif "INTEGER" in cat_str or "COUNT" in cat_str:
            if not isinstance(val, int) or isinstance(val, bool):
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    original_header=orig_header,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_PRIMITIVE_NOT_INTEGER",
                    message=f"Value for '{self.target_field_id}' must be an Integer, got '{type(val).__name__}'.",
                    invalid_value=val,
                    category=self.validation_category,
                )

        # Datetime validation
        elif "DATETIME" in cat_str or "TIMESTAMP" in cat_str:
            if not isinstance(val, (datetime, date)):
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    original_header=orig_header,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_PRIMITIVE_NOT_DATETIME",
                    message=f"Value for '{self.target_field_id}' must be a valid UTC datetime object, got '{type(val).__name__}'.",
                    invalid_value=val,
                    category=self.validation_category,
                )

        # String validation
        elif "STRING" in cat_str or "CODE" in cat_str or "TEXT" in cat_str or "IDENTIFIER" in cat_str:
            if not isinstance(val, str):
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    original_header=orig_header,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_PRIMITIVE_NOT_STRING",
                    message=f"Value for '{self.target_field_id}' must be a string, got '{type(val).__name__}'.",
                    invalid_value=val,
                    category=self.validation_category,
                )

        return None
