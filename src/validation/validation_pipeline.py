"""Validation Pipeline.

This module provides the execution pipeline executing validation rules sequentially across all 5 tiers.
"""

from typing import List, Optional, Tuple
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.contracts import FieldErrorDetail, RowValidationResult, ValidationContext
from src.validation.enums import ValidationSeverity, ValidationTier
from src.validation.registry import ValidationRuleRegistry
from src.validation.rule_context import RuleExecutionContext


class ValidationPipeline:
    """Orchestrates 5-tier validation execution across rows and dataset objects."""

    def __init__(self, registry: ValidationRuleRegistry) -> None:
        self._registry = registry

    def execute_row_pipeline(
        self,
        row: CanonicalRow,
        dataset: Optional[CanonicalDataset],
        context: ValidationContext,
    ) -> RowValidationResult:
        """Execute Tiers 1 through 4 validation rules on a single row."""
        sorted_rules = self._registry.get_execution_order()
        exec_ctx = RuleExecutionContext(row=row, dataset=dataset, context=context)
        row_errors: List[FieldErrorDetail] = []
        is_row_valid = True

        for rule in sorted_rules:
            # Skip Tier 5 dataset rules during row pipeline
            if rule.validation_tier == ValidationTier.TIER_5_CROSS_ENTITY_DATASET:
                continue

            # Fail-fast: If structural Tier 1 failure occurred, skip higher tier checks on this row
            if not is_row_valid and rule.validation_tier != ValidationTier.TIER_1_STRUCTURAL:
                break

            target_val = None
            if hasattr(rule, "target_field_id") and row.fields:
                target_val = row.fields.get(rule.target_field_id)

            err = rule.validate(target_val, exec_ctx)
            if err is not None:
                row_errors.append(err)
                if err.severity == ValidationSeverity.CRITICAL:
                    is_row_valid = False

        has_warnings = any(e.severity in (ValidationSeverity.WARNING, ValidationSeverity.INFO) for e in row_errors)
        return RowValidationResult(
            row_index=row.row_index,
            is_valid=is_row_valid,
            has_warnings=has_warnings,
            errors=row_errors,
        )

    def execute_dataset_tier5(
        self,
        dataset: CanonicalDataset,
        context: ValidationContext,
    ) -> List[FieldErrorDetail]:
        """Execute Tier 5 dataset-level validation rules."""
        t5_rules = self._registry.get_rules_for_tier(ValidationTier.TIER_5_CROSS_ENTITY_DATASET)
        exec_ctx = RuleExecutionContext(dataset=dataset, context=context)
        t5_errors: List[FieldErrorDetail] = []

        for rule in t5_rules:
            err = rule.validate(None, exec_ctx)
            if err is not None:
                t5_errors.append(err)

        return t5_errors
