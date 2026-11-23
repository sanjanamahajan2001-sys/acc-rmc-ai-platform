"""Unit and Benchmark Test Suite for WS-03.3 Phase 6 SharedValidationEngine, Orchestrator, Quality Score, and Quarantine Payload Contract."""

from datetime import datetime, timezone
from decimal import Decimal
import time
import unittest
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation import (
    DatasetValidationResult,
    DatasetValidator,
    FieldErrorDetail,
    QualityScoreCalculator,
    QuarantinePayloadContract,
    RuleExecutionContext,
    SharedValidationEngine,
    ValidationContext,
    ValidationResultAggregator,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationTier,
    register_all_validation_rules,
)


class TestSharedValidationEngine(unittest.TestCase):
    """Unit, regression, integration, and performance benchmark test suite for Phase 6 SharedValidationEngine."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_all_validation_rules(self.registry)
        self.engine = SharedValidationEngine(self.registry)

    def test_shared_validation_engine_valid_dataset(self) -> None:
        valid_rows = [
            CanonicalRow(
                row_index=i,
                fields={
                    "FIELD_BATCH_ID": f"BAT-MUM-{i:04d}",
                    "FIELD_PLANT_ID": "PLANT-MUM-01",
                    "FIELD_RECIPE_ID": "REC-M40",
                    "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                    "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                    "FIELD_WATER_CEMENT_RATIO": 0.40,
                    "FIELD_SLUMP_MM": 150.0,
                    "FIELD_BATCH_STATUS": "COMPLETED",
                },
            )
            for i in range(5)
        ]

        dataset = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=valid_rows)

        result, output = self.engine.validate_dataset(dataset)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.summary.total_records, 5)
        self.assertEqual(result.summary.valid_records_count, 5)
        self.assertEqual(result.summary.critical_errors_count, 0)
        self.assertEqual(result.summary.quality_score, 100.0)

        self.assertIsInstance(output, CanonicalDataset)
        self.assertEqual(len(output.rows), 5)

    def test_shared_validation_engine_quarantine_trigger(self) -> None:
        rows = [
            # Valid row
            CanonicalRow(
                row_index=0,
                fields={
                    "FIELD_BATCH_ID": "BAT-001",
                    "FIELD_PLANT_ID": "PLANT-MUM-01",
                    "FIELD_RECIPE_ID": "REC-M40",
                    "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                    "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                },
            ),
            # Invalid row (Missing required FIELD_BATCH_ID -> CRITICAL)
            CanonicalRow(
                row_index=1,
                fields={
                    "FIELD_PLANT_ID": "PLANT-MUM-01",
                    "FIELD_RECIPE_ID": "REC-M40",
                    "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                    "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                },
            ),
        ]

        dataset = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=rows)

        result, output = self.engine.validate_dataset(dataset)

        self.assertFalse(result.is_valid)
        self.assertGreater(result.summary.critical_errors_count, 0)
        self.assertLess(result.summary.quality_score, 100.0)

        # Output MUST be QuarantinePayloadContract
        self.assertIsInstance(output, QuarantinePayloadContract)
        self.assertGreater(len(output.critical_errors), 0)

    def test_dataset_validator_duplicate_batch_id(self) -> None:
        val_dup = DatasetValidator()
        rows = [
            CanonicalRow(row_index=0, fields={"FIELD_BATCH_ID": "BAT-DUP-001"}),
            CanonicalRow(row_index=1, fields={"FIELD_BATCH_ID": "BAT-DUP-001"}),  # Duplicate!
        ]
        dataset = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=rows)

        exec_ctx = RuleExecutionContext(dataset=dataset, context=ValidationContext(source_channel="DATASET"))
        err = val_dup.validate(None, exec_ctx)

        self.assertIsNotNone(err)
        self.assertEqual(err.severity, ValidationSeverity.CRITICAL)
        self.assertEqual(err.error_code, "ACC_VAL_DUPLICATE_BATCH_ID")

    def test_quality_score_calculator(self) -> None:
        err_crit = FieldErrorDetail(field_id="F1", rule_id="R1", tier=ValidationTier.TIER_1_STRUCTURAL, severity=ValidationSeverity.CRITICAL, error_code="E1", message="M1")
        err_warn = FieldErrorDetail(field_id="F2", rule_id="R2", tier=ValidationTier.TIER_3_RANGES_ENUMS, severity=ValidationSeverity.WARNING, error_code="E2", message="M2")

        # 1 record, 1 warning (penalty 5.0) -> Score 95.0
        score1 = QualityScoreCalculator.calculate_score(1, [err_warn])
        self.assertEqual(score1, 95.0)

        # 1 record, 1 critical (penalty 100.0) -> Score 0.0
        score2 = QualityScoreCalculator.calculate_score(1, [err_crit])
        self.assertEqual(score2, 0.0)

    def test_shared_validation_engine_performance_benchmark(self) -> None:
        benchmark_results = []

        for row_count in [10, 1000, 10000]:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-{i:05d}",
                        "FIELD_PLANT_ID": "PLANT-MUM-01",
                        "FIELD_RECIPE_ID": "REC-M40",
                        "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                        "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                        "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                        "FIELD_WATER_CEMENT_RATIO": 0.40,
                        "FIELD_SLUMP_MM": 150.0,
                        "FIELD_BATCH_STATUS": "COMPLETED",
                    },
                )
                for i in range(row_count)
            ]
            dataset = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=rows)

            t0 = time.perf_counter()
            result, output = self.engine.validate_dataset(dataset)
            t1 = time.perf_counter()

            total_ms = (t1 - t0) * 1000.0
            per_row_ms = total_ms / row_count
            pass_status = "PASS" if per_row_ms < 0.50 else "FAIL"

            benchmark_results.append((row_count, total_ms, per_row_ms, pass_status))
            self.assertTrue(result.is_valid)
            self.assertLess(per_row_ms, 0.50, f"Engine validation speed for {row_count} rows exceeded limit: {per_row_ms:.4f} ms/row")

        print("\n==========================================================================================")
        print("SHARED VALIDATION ENGINE (PHASE 6) PERFORMANCE BENCHMARK RESULTS")
        print("==========================================================================================")
        print(f"{'Row Count':<12} | {'Total Time (ms)':<18} | {'Speed (ms/row)':<18} | {'Requirement':<15} | {'Status':<8}")
        print("------------------------------------------------------------------------------------------")
        for count, total, speed, status in benchmark_results:
            print(f"{count:<12} | {total:<18.2f} | {speed:<18.4f} | {'< 0.50 ms/row':<15} | {status:<8}")
        print("==========================================================================================\n")


if __name__ == "__main__":
    unittest.main()
