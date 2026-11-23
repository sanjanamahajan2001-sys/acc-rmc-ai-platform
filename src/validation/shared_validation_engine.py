"""Shared Validation Engine Orchestrator.

This module provides the central SharedValidationEngine orchestrating multi-tier validation pipelines with optional profiling.
"""

from typing import Dict, List, Optional, Tuple, Union
from src.logging import get_logger
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation.contracts import (
    DatasetValidationResult,
    FieldErrorDetail,
    RowValidationResult,
    ValidationContext,
    ValidationResult,
)
from src.validation.enums import ValidationSeverity
from src.validation.execution_report import ValidationConfigurationSnapshot, ValidationExecutionReport
from src.validation.performance_profiler import ValidationPerformanceProfiler
from src.validation.quarantine_contract import QuarantinePayloadContract
from src.validation.registry import ValidationRuleRegistry, get_default_validation_registry
from src.validation.result_aggregator import ValidationResultAggregator
from src.validation.validation_pipeline import ValidationPipeline
from src.validation.version import RULE_REGISTRY_VERSION, VALIDATION_ENGINE_VERSION

logger = get_logger("src.validation.engine", component="validation")


class SharedValidationEngine:
    """Thread-safe orchestrator for multi-tier ingestion data validation."""

    def __init__(self, registry: Optional[ValidationRuleRegistry] = None, enable_profiling: bool = False) -> None:
        self._registry = registry or get_default_validation_registry()
        self._pipeline = ValidationPipeline(self._registry)
        self.enable_profiling = enable_profiling

    def validate_row(
        self,
        row: CanonicalRow,
        context: Optional[ValidationContext] = None,
    ) -> RowValidationResult:
        """Validate a single CanonicalRow through Tiers 1–4."""
        ctx = context or ValidationContext(source_channel="SINGLE_ROW")
        return self._pipeline.execute_row_pipeline(row, None, ctx)

    def validate_dataset(
        self,
        dataset: CanonicalDataset,
        context: Optional[ValidationContext] = None,
    ) -> Tuple[DatasetValidationResult, Union[CanonicalDataset, QuarantinePayloadContract]]:
        """Validate a full CanonicalDataset through Tiers 1–5.

        Returns tuple of (DatasetValidationResult, ValidatedDataset OR QuarantinePayloadContract).
        """
        ctx = context or ValidationContext(
            profile_id=dataset.profile_id,
            profile_version=dataset.profile_version,
            source_channel="DATASET",
        )

        profiler = ValidationPerformanceProfiler(enabled=self.enable_profiling)
        profiler.start()

        row_results: List[RowValidationResult] = []
        valid_rows: List[CanonicalRow] = []
        failed_rows: List[CanonicalRow] = []

        # 1. Execute Tiers 1-4 on each row
        with profiler.profile_tier("TIER_1_TO_4_ROWS"):
            for row in dataset.rows:
                rr = self._pipeline.execute_row_pipeline(row, dataset, ctx)
                row_results.append(rr)
                if rr.is_valid:
                    valid_rows.append(row)
                else:
                    failed_rows.append(row)

        # 2. Execute Tier 5 Dataset-level validation
        with profiler.profile_tier("TIER_5_DATASET"):
            dataset_errors = self._pipeline.execute_dataset_tier5(dataset, ctx)

        dataset_id = getattr(dataset, "dataset_id", f"DS-EVAL-{id(dataset)}")

        # 3. Aggregate results and compute Quality Score
        result = ValidationResultAggregator.aggregate(
            dataset_id=dataset_id,
            total_records=len(dataset.rows),
            row_results=row_results,
            dataset_errors=dataset_errors,
        )

        total_duration_ms = profiler.stop()
        total_rows = len(dataset.rows)

        if self.enable_profiling and total_duration_ms > 0:
            rows_per_sec = (total_rows / (total_duration_ms / 1000.0)) if total_duration_ms > 0 else 0.0
            config_snap = ValidationConfigurationSnapshot(
                engine_version=VALIDATION_ENGINE_VERSION,
                enabled_tiers=["TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5"],
                rule_registry_version=RULE_REGISTRY_VERSION,
                rule_count=len(self._registry.get_rules()),
                profiling_enabled=self.enable_profiling,
                execution_mode="SINGLE_THREADED",
            )
            exec_report = ValidationExecutionReport(
                dataset_id=dataset_id,
                total_rows=total_rows,
                valid_rows=len(valid_rows),
                invalid_rows=len(failed_rows),
                rows_passed_tier1=len(valid_rows),
                rows_passed_tier2=len(valid_rows),
                rows_passed_tier3=len(valid_rows),
                rows_passed_tier4=len(valid_rows),
                rows_passed_tier5=len(valid_rows),
                rows_quarantined=len(failed_rows),
                quality_score=result.summary.quality_score,
                per_tier_duration_ms=profiler.tier_durations_ms,
                total_execution_duration_ms=total_duration_ms,
                rows_per_second=rows_per_sec,
                config_snapshot=config_snap,
            )
            logger.info("Validation operational execution report generated", report=exec_report.model_dump())

        logger.info(
            "Dataset validation execution complete",
            dataset_id=dataset_id,
            is_valid=result.is_valid,
            quality_score=result.summary.quality_score,
            critical_count=result.summary.critical_errors_count,
        )

        # 4. Route decision: Validated Dataset OR Quarantine Payload Contract
        if result.is_valid:
            clean_dataset = CanonicalDataset(
                profile_id=dataset.profile_id,
                profile_version=dataset.profile_version,
                rows=valid_rows,
            )
            return result, clean_dataset
        else:
            all_criticals: List[FieldErrorDetail] = [
                e for rr in row_results for e in rr.errors if e.severity == ValidationSeverity.CRITICAL
            ] + [e for e in dataset_errors if e.severity == ValidationSeverity.CRITICAL]

            quarantine_payload = QuarantinePayloadContract(
                dataset_id=dataset_id,
                import_profile_id=dataset.profile_id,
                source_channel=ctx.source_channel,
                failed_rows=failed_rows,
                critical_errors=all_criticals,
                validation_result=result,
            )
            return result, quarantine_payload
