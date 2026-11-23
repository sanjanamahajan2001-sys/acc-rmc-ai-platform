"""Referential Integrity Validator.

This module provides Tier 4 validation verifying canonical master key presence against database lookup tables or repository interfaces.
"""

from typing import Any, List, Optional, Set
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class ReferentialIntegrityValidator(BaseValidationRule):
    """Tier 4 Validator verifying that master keys (plant_id, recipe_id, customer_id) exist in lookup tables."""

    def __init__(
        self,
        target_field_id: str,
        valid_keys_set: Optional[Set[str]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        self.target_field_id = target_field_id
        self.valid_keys_set = valid_keys_set or set()
        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T4_REF_{target_field_id}",
            rule_name=f"Referential Integrity Validator [{target_field_id}]",
            description=f"Verifies master key existence in database for '{target_field_id}'.",
            tier=ValidationTier.TIER_4_CROSS_FIELD_REFERENTIAL,
            category=ValidationCategory.PRODUCTION,
            severity=severity,
            version="1.0.0",
            execution_priority=20,
            tags=["referential", "tier4", target_field_id.lower()],
        )
        super().__init__(metadata)

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate foreign key presence against valid keys set or lookup context."""
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

        val_str = str(val).strip()

        # Check options context lookup set if provided dynamically
        lookup_set = self.valid_keys_set
        if context.context and context.context.options and self.target_field_id in context.context.options:
            lookup_set = set(context.context.options[self.target_field_id])

        if lookup_set and val_str not in lookup_set:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_FOREIGN_KEY_NOT_FOUND",
                message=f"Master key '{val_str}' for '{self.target_field_id}' does not exist in master lookup tables.",
                invalid_value=val_str,
                category=self.validation_category,
            )

        return None
