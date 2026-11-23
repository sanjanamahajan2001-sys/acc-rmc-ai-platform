"""Cross-Field Validator.

This module provides Tier 4 configuration-driven validation verifying internal mathematical, logical, and ratio relationships between fields in a single row.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class CrossFieldValidator(BaseValidationRule):
    """Tier 4 Configuration-Driven Validator verifying multi-field relationships within a single CanonicalRow."""

    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        description: str,
        target_field_id: str,
        required_fields: Optional[List[str]] = None,
        operator: str = "RATIO_TOLERANCE",
        tolerance: float = 0.05,
        comparator_fn: Optional[Callable[[Dict[str, Any], float], Optional[str]]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        self.target_field_id = target_field_id
        self.required_fields = required_fields or []
        self.operator = operator.upper()
        self.tolerance = tolerance
        self.comparator_fn = comparator_fn

        metadata = RuleMetadata(
            rule_id=rule_id,
            rule_name=rule_name,
            description=description,
            tier=ValidationTier.TIER_4_CROSS_FIELD_REFERENTIAL,
            category=ValidationCategory.CONCRETE,
            severity=severity,
            version="1.0.0",
            execution_priority=10,
            tags=["cross_field", "tier4"],
        )
        super().__init__(metadata)

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id or field_id == "__ROW__"

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate cross-field relationships using configuration-driven operator and tolerance settings."""
        if context.row is None or not context.row.fields:
            return None

        fields = context.row.fields

        # Check required fields presence for rule calculation
        if self.required_fields:
            for req in self.required_fields:
                if req not in fields or fields[req] is None:
                    return None  # Skip if required input fields missing

        # Custom comparator function override
        if self.comparator_fn is not None:
            msg = self.comparator_fn(fields, self.tolerance)
            if msg:
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code=f"ACC_VAL_CROSS_FIELD_{self.rule_id}",
                    message=msg,
                    invalid_value=fields.get(self.target_field_id),
                    category=self.validation_category,
                )
            return None

        # Operator: RATIO_TOLERANCE (e.g. W/C Ratio: |Water / Cement - Reported| <= Tolerance)
        if self.operator == "RATIO_TOLERANCE":
            c_val = fields.get("FIELD_ACTUAL_CEMENT_KG")
            w_val = fields.get("FIELD_ACTUAL_WATER_KG")
            wc_val = fields.get("FIELD_WATER_CEMENT_RATIO")

            if c_val is not None and w_val is not None and wc_val is not None:
                try:
                    c_num = float(c_val)
                    w_num = float(w_val)
                    reported_wc = float(wc_val)
                    calc_wc = w_num / c_num if c_num > 0 else 0.0

                    if abs(calc_wc - reported_wc) > self.tolerance:
                        return FieldErrorDetail(
                            field_id=self.target_field_id,
                            rule_id=self.rule_id,
                            tier=self.validation_tier,
                            severity=self.severity,
                            error_code="ACC_VAL_CROSS_FIELD_WC_MISMATCH",
                            message=f"Calculated W/C ratio ({calc_wc:.3f}) mismatches reported ratio ({reported_wc:.3f}) by > {self.tolerance}.",
                            invalid_value=reported_wc,
                            category=self.validation_category,
                        )
                except Exception:
                    pass

        # Operator: DATETIME_ORDER (e.g. Start <= End)
        elif self.operator == "DATETIME_ORDER":
            start_dt = fields.get("FIELD_BATCH_DATETIME")
            end_dt = fields.get("FIELD_DISPATCH_DATETIME")

            if isinstance(start_dt, datetime) and isinstance(end_dt, datetime):
                if start_dt > end_dt:
                    return FieldErrorDetail(
                        field_id=self.target_field_id,
                        rule_id=self.rule_id,
                        tier=self.validation_tier,
                        severity=self.severity,
                        error_code="ACC_VAL_CROSS_FIELD_TIMESTAMP_ORDER",
                        message=f"Batch start datetime '{start_dt}' cannot be after dispatch datetime '{end_dt}'.",
                        invalid_value=str(end_dt),
                        category=self.validation_category,
                    )

        # Operator: LESS_THAN_OR_EQUAL (e.g. FieldA <= FieldB)
        elif self.operator == "LESS_THAN_OR_EQUAL" and len(self.required_fields) >= 2:
            val_a = fields.get(self.required_fields[0])
            val_b = fields.get(self.required_fields[1])

            if val_a is not None and val_b is not None:
                try:
                    if float(val_a) > float(val_b) + self.tolerance:
                        return FieldErrorDetail(
                            field_id=self.target_field_id,
                            rule_id=self.rule_id,
                            tier=self.validation_tier,
                            severity=self.severity,
                            error_code="ACC_VAL_CROSS_FIELD_VALUE_EXCEEDED",
                            message=f"Field '{self.required_fields[0]}' ({val_a}) exceeds '{self.required_fields[1]}' ({val_b}) + tolerance ({self.tolerance}).",
                            invalid_value=val_a,
                            category=self.validation_category,
                        )
                except Exception:
                    pass

        return None
