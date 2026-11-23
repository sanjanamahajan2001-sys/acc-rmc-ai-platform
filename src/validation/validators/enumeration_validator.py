"""Enumeration Validator.

This module provides Tier 3 validation verifying canonical enum values match allowed set definitions.
"""

from enum import Enum
from typing import Any, List, Optional, Type
from src.validation.base_rule import BaseValidationRule
from src.validation.contracts import FieldErrorDetail
from src.validation.enums import ValidationCategory, ValidationSeverity, ValidationTier
from src.validation.metadata import RuleMetadata
from src.validation.rule_context import RuleExecutionContext


class EnumerationValidator(BaseValidationRule):
    """Tier 3 Validator verifying that string/enum values belong strictly to permitted enumeration sets."""

    def __init__(
        self,
        target_field_id: str,
        allowed_values: Optional[List[str]] = None,
        enum_cls: Optional[Type[Enum]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        self.target_field_id = target_field_id
        self.allowed_values = [v.upper() for v in allowed_values] if allowed_values else []
        if enum_cls is not None:
            self.allowed_values.extend([e.name.upper() for e in enum_cls] + [str(e.value).upper() for e in enum_cls])
        self.allowed_values = list(set(self.allowed_values))

        metadata = RuleMetadata(
            rule_id=f"ACC_VAL_T3_ENUM_{target_field_id}",
            rule_name=f"Enumeration Validator [{target_field_id}]",
            description=f"Verifies canonical value belongs to permitted enumeration set for '{target_field_id}'.",
            tier=ValidationTier.TIER_3_RANGES_ENUMS,
            category=ValidationCategory.PRODUCTION,
            severity=severity,
            version="1.0.0",
            execution_priority=20,
            tags=["enum", "tier3", target_field_id.lower()],
        )
        super().__init__(metadata)

    def supports(self, field_id: str) -> bool:
        return field_id == self.target_field_id

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        """Validate string or enum value against permitted allowed values list."""
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

        val_str = str(val.name if isinstance(val, Enum) else val).strip().upper()

        if self.allowed_values and val_str not in self.allowed_values:
            return FieldErrorDetail(
                field_id=self.target_field_id,
                original_header=orig_header,
                rule_id=self.rule_id,
                tier=self.validation_tier,
                severity=self.severity,
                error_code="ACC_VAL_UNSUPPORTED_ENUM_VALUE",
                message=f"Value '{val}' for '{self.target_field_id}' is not in permitted enumeration list.",
                invalid_value=val,
                category=self.validation_category,
            )

        return None
