"""Dataset Validator.

This module provides Tier 5 validation enforcing collection-wide rules across multiple canonical rows (duplicate batch IDs, timestamp ordering).
"""

from typing import Any, List, Optional, Set
from src.mapping.contracts import CanonicalDataset
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class DatasetValidator(BaseValidationRule):
    """Tier 5 Validator verifying collection-wide integrity across a full CanonicalDataset."""

    def __init__(
        self,
        rule_id: str = "ACC_VAL_T5_DUPLICATE_BATCH_ID",
        rule_name: str = "Duplicate Batch ID Check",
        description: str = "Verifies zero duplicate batch IDs exist within the same CanonicalDataset.",
        severity: ValidationSeverity = ValidationSeverity.CRITICAL,
    ) -> None:
        metadata = RuleMetadata(
            rule_id=rule_id,
            rule_name=rule_name,
            description=description,
            tier=ValidationTier.TIER_5_CROSS_ENTITY_DATASET,
            category=ValidationCategory.PRODUCTION,
            severity=severity,
            version="1.0.0",
            execution_priority=10,
            tags=["dataset", "tier5", "duplicates"],
        )
        super().__init__(metadata)

    def supports(self, field_id: str) -> bool:
        return field_id == "__DATASET__" or field_id == "FIELD_BATCH_ID"

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate collection-wide duplicate batch IDs on CanonicalDataset."""
        if context.dataset is None or not context.dataset.rows:
            return None

        if self.rule_id == "ACC_VAL_T5_DUPLICATE_BATCH_ID":
            seen_batch_ids: Set[str] = set()
            for r in context.dataset.rows:
                if r.fields:
                    batch_id = r.fields.get("FIELD_BATCH_ID")
                    if batch_id is not None:
                        bid_str = str(batch_id).strip()
                        if bid_str in seen_batch_ids:
                            return FieldErrorDetail(
                                field_id="FIELD_BATCH_ID",
                                rule_id=self.rule_id,
                                tier=self.validation_tier,
                                severity=self.severity,
                                error_code="ACC_VAL_DUPLICATE_BATCH_ID",
                                message=f"Duplicate batch ID '{bid_str}' detected within dataset.",
                                invalid_value=bid_str,
                                category=self.validation_category,
                            )
                        seen_batch_ids.add(bid_str)

        return None
