"""Validation Result Aggregator.

This module provides aggregation utilities constructing ValidationSummaryReport and DatasetValidationResult objects.
"""

from datetime import datetime, timezone
from typing import List, Optional
from src.validation.contracts import (
    DatasetValidationResult,
    FieldErrorDetail,
    RowValidationResult,
    ValidationSummaryReport,
)
from src.validation.enums import ValidationSeverity
from src.validation.quality_score import QualityScoreCalculator


class ValidationResultAggregator:
    """Aggregates row-level validation results and field errors into final dataset reports."""

    @staticmethod
    def aggregate(
        dataset_id: str,
        total_records: int,
        row_results: List[RowValidationResult],
        dataset_errors: Optional[List[FieldErrorDetail]] = None,
    ) -> DatasetValidationResult:
        """Aggregate per-row results and dataset errors into a DatasetValidationResult."""
        all_errors: List[FieldErrorDetail] = list(dataset_errors or [])
        for rr in row_results:
            all_errors.extend(rr.errors)

        critical_count = sum(1 for e in all_errors if e.severity == ValidationSeverity.CRITICAL)
        error_count = sum(1 for e in all_errors if e.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for e in all_errors if e.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for e in all_errors if e.severity == ValidationSeverity.INFO)

        valid_records_count = sum(1 for rr in row_results if rr.is_valid)
        quality_score = QualityScoreCalculator.calculate_score(total_records, all_errors)
        is_dataset_valid = (critical_count == 0)

        summary = ValidationSummaryReport(
            total_records=total_records,
            valid_records_count=valid_records_count,
            critical_errors_count=critical_count,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            quality_score=quality_score,
        )

        return DatasetValidationResult(
            dataset_id=dataset_id,
            is_valid=is_dataset_valid,
            summary=summary,
            row_results=row_results,
            validated_at=datetime.now(timezone.utc),
        )
