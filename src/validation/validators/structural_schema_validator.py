"""Structural Schema Validator.

This module provides Tier 1 validation enforcing structural integrity for CanonicalRow and CanonicalDataset objects.
"""

from typing import Any, Optional
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class StructuralSchemaValidator(BaseValidationRule):
    """Tier 1 Validator verifying fundamental CanonicalRow and CanonicalDataset structural shape."""

    def __init__(self) -> None:
        metadata = RuleMetadata(
            rule_id="ACC_VAL_T1_STRUCTURAL",
            rule_name="Structural Schema Validator",
            description="Verifies non-null payload shapes, required CanonicalRow dicts, and valid dataset collection containers.",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.PRODUCTION,
            severity=ValidationSeverity.CRITICAL,
            version="1.0.0",
            execution_priority=10,
            tags=["structural", "tier1", "schema"],
        )
        super().__init__(metadata)

    def supports(self, field_id: str) -> bool:
        return field_id == "__ROW_STRUCTURE__" or field_id == "__DATASET_STRUCTURE__"

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate structural shape of row or dataset container."""
        # 1. Dataset Level Structural Check
        if context.dataset is not None:
            if not isinstance(context.dataset, CanonicalDataset):
                return FieldErrorDetail(
                    field_id="__DATASET_STRUCTURE__",
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_INVALID_DATASET_STRUCTURE",
                    message="Payload is not a valid CanonicalDataset container.",
                    invalid_value=type(context.dataset).__name__,
                    category=self.validation_category,
                )
            if context.dataset.rows is None or not isinstance(context.dataset.rows, list):
                return FieldErrorDetail(
                    field_id="__DATASET_STRUCTURE__",
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_MISSING_DATASET_ROWS",
                    message="CanonicalDataset rows collection is missing or malformed.",
                    invalid_value=None,
                    category=self.validation_category,
                )

        # 2. Row Level Structural Check
        if context.row is not None:
            if not isinstance(context.row, CanonicalRow):
                return FieldErrorDetail(
                    field_id="__ROW_STRUCTURE__",
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_INVALID_ROW_STRUCTURE",
                    message="Row payload is not a valid CanonicalRow object.",
                    invalid_value=type(context.row).__name__,
                    category=self.validation_category,
                )
            if context.row.fields is None or not isinstance(context.row.fields, dict):
                return FieldErrorDetail(
                    field_id="__ROW_STRUCTURE__",
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_MALFORMED_ROW_FIELDS",
                    message="CanonicalRow fields map is missing or malformed.",
                    invalid_value=None,
                    category=self.validation_category,
                )

        return None
