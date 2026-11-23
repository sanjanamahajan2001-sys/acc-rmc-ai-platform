"""End-to-End Integration, Concurrency, Regression, and Stress Test Suite for WS-03.3 Final Certification."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import os
import time
import unittest
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation import (
    DatasetValidationResult,
    QuarantinePayloadContract,
    SharedValidationEngine,
    ValidationRuleRegistry,
    register_all_validation_rules,
)


class TestWS03_3EndToEndCertification(unittest.TestCase):
    """Final End-to-End Production Certification Test Suite for WS-03.3."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_all_validation_rules(self.registry)
        self.engine = SharedValidationEngine(self.registry, enable_profiling=True)

    def test_e2e_valid_dataset_flow(self) -> None:
        valid_rows = [
            CanonicalRow(
                row_index=i,
                fields={
                    "FIELD_BATCH_ID": f"BAT-E2E-{i:05d}",
                    "FIELD_PLANT_ID": "PLANT-MUM-01",
                    "FIELD_RECIPE_ID": "REC-M40",
                    "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    "FIELD_ACTUAL_CEMENT_KG": Decimal("420.00"),
                    "FIELD_ACTUAL_WATER_KG": Decimal("168.00"),
                    "FIELD_WATER_CEMENT_RATIO": 0.40,
                    "FIELD_SLUMP_MM": 160.0,
                    "FIELD_BATCH_STATUS": "COMPLETED",
                },
            )
            for i in range(20)
        ]
        dataset = CanonicalDataset(profile_id="PROF-E2E-VALID", profile_version="1.0.0", rows=valid_rows)

        result, output = self.engine.validate_dataset(dataset)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.summary.total_records, 20)
        self.assertEqual(result.summary.valid_records_count, 20)
        self.assertEqual(result.summary.critical_errors_count, 0)
        self.assertEqual(result.summary.quality_score, 100.0)

        self.assertIsInstance(output, CanonicalDataset)
        self.assertEqual(len(output.rows), 20)

    def test_e2e_quarantine_payload_routing(self) -> None:
        rows = [
            # Valid row
            CanonicalRow(
                row_index=0,
                fields={
                    "FIELD_BATCH_ID": "BAT-E2E-FAIL-001",
                    "FIELD_PLANT_ID": "PLANT-MUM-01",
                    "FIELD_RECIPE_ID": "REC-M40",
                    "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                    "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                },
            ),
            # Invalid row (Missing required batch_id -> CRITICAL error)
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
        dataset = CanonicalDataset(profile_id="PROF-E2E-FAIL", profile_version="1.0.0", rows=rows)

        result, output = self.engine.validate_dataset(dataset)

        self.assertFalse(result.is_valid)
        self.assertGreater(result.summary.critical_errors_count, 0)
        self.assertLess(result.summary.quality_score, 100.0)

        self.assertIsInstance(output, QuarantinePayloadContract)
        self.assertEqual(len(output.failed_rows), 1)
        self.assertGreater(len(output.critical_errors), 0)

    def test_e2e_deterministic_repeatability(self) -> None:
        rows = [
            CanonicalRow(
                row_index=i,
                fields={
                    "FIELD_BATCH_ID": f"BAT-DET-{i:03d}",
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
            for i in range(10)
        ]
        dataset = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=rows)

        res1, _ = self.engine.validate_dataset(dataset)
        res2, _ = self.engine.validate_dataset(dataset)
        res3, _ = self.engine.validate_dataset(dataset)

        self.assertEqual(res1.summary.quality_score, res2.summary.quality_score)
        self.assertEqual(res2.summary.quality_score, res3.summary.quality_score)
        self.assertEqual(res1.summary.critical_errors_count, res2.summary.critical_errors_count)

    def test_e2e_thread_safe_concurrency(self) -> None:
        def run_validation(thread_id: int) -> bool:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-THREAD-{thread_id}-{i:03d}",
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
                for i in range(50)
            ]
            ds = CanonicalDataset(profile_id=f"P-THREAD-{thread_id}", profile_version="1.0.0", rows=rows)
            res, out = self.engine.validate_dataset(ds)
            return res.is_valid

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_validation, t_id) for t_id in range(16)]
            results = [f.result() for f in futures]

        self.assertTrue(all(results))

    def test_e2e_final_certification_scaling_benchmark(self) -> None:
        benchmark_results = []

        for row_count in [10, 1000, 10000, 100000]:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-BENCH-{i:06d}",
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
            rows_per_sec = (row_count / (total_ms / 1000.0)) if total_ms > 0 else 0.0
            pass_status = "PASS" if per_row_ms < 0.50 else "FAIL"

            benchmark_results.append((row_count, total_ms, per_row_ms, rows_per_sec, pass_status))
            self.assertTrue(result.is_valid)

        print("\n========================================================================================================")
        print("WS-03.3 FINAL END-TO-END PRODUCTION CERTIFICATION SCALING BENCHMARK")
        print("========================================================================================================")
        print(f"{'Row Count':<12} | {'Total Time (ms)':<18} | {'Speed (ms/row)':<18} | {'Throughput (rows/sec)':<22} | {'Status':<8}")
        print("--------------------------------------------------------------------------------------------------------")
        for count, total, speed, throughput, status in benchmark_results:
            print(f"{count:<12} | {total:<18.2f} | {speed:<18.4f} | {throughput:<22.2f} | {status:<8}")
        print("========================================================================================================\n")


if __name__ == "__main__":
    unittest.main()
