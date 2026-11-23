"""Required Field Validator.

This module provides Tier 1 validation verifying presence and non-emptiness of mandatory canonical fields.
"""

from typing import Any, List, Optional
from src.database.dictionary import CanonicalFieldID, get_canonical_dictionary
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class RequiredFieldValidator(BaseValidationRule):
    """Tier 1 Validator verifying presence, non-nullability, and non-emptiness of mandatory canonical fields."""

    def __init__(self, target_field_id: str, severity: ValidationSeverity = ValidationSeverity.CRITICAL) -> None:
        self.target_field_id = target_field_id
        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T1_REQ_{target_field_id}",
            rule_name=f"Required Field Validator [{target_field_id}]",
            description=f"Verifies mandatory canonical field '{target_field_id}' is present, non-null, and non-empty.",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.PRODUCTION,
            severity=severity,
            version="1.0.0",
            execution_priority=20,
            tags=["required", "tier1", target_field_id.lower()],
        )
        super().__init__(metadata)
        self._dictionary = get_canonical_dictionary()

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate value presence for target required field."""
        # Retrieve field value from row dict if not directly passed
        val = value
        orig_header: Optional[str] = None

        if context.row is not None:
            if val is None and context.row.fields:
                val = context.row.fields.get(self.target_field_id)

            # Attempt to find original header from audit records
            for audit in context.row.audit_records:
                if audit.canonical_field_id == self.target_field_id:
                    orig_header = audit.original_header
                    break

        # Check missing or null
        if val is None:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_REQUIRED_FIELD_MISSING",
                message=f"Mandatory canonical field '{self.target_field_id}' is missing or null.",
                invalid_value=None,
                category=self.validation_category,
            )

        # Check string empty or whitespace-only
        if isinstance(val, str):
            clean_str = val.strip()
            if clean_str == "":
                return FieldErrorDetail(
                    field_id=self.target_field_id,
                    original_header=orig_header,
                    rule_id=self.rule_id,
                    tier=self.validation_tier,
                    severity=self.severity,
                    error_code="ACC_VAL_REQUIRED_FIELD_EMPTY",
                    message=f"Mandatory canonical field '{self.target_field_id}' cannot be empty or whitespace-only.",
                    invalid_value=val,
                    category=self.validation_category,
                )

        return None
