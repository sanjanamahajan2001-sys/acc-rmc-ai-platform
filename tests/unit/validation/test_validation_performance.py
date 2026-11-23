"""Unit, Performance, Profiling, and Benchmark Test Suite for WS-03.3 Phase 7 Operational Diagnostics & Hardening."""

from datetime import datetime, timezone
from decimal import Decimal
import time
import unittest
from src.mapping.contracts import CanonicalDataset, CanonicalRow
from src.validation import (
    DatasetValidationResult,
    QuarantinePayloadContract,
    SharedValidationEngine,
    ValidationExecutionReport,
    ValidationMetricsCollector,
    ValidationPerformanceProfiler,
    ValidationRuleRegistry,
    ValidationStatisticsService,
    register_all_validation_rules,
)


class TestValidationPerformance(unittest.TestCase):
    """Unit, integration, performance, and scaling benchmark test suite for Phase 7."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_all_validation_rules(self.registry)
        self.engine = SharedValidationEngine(self.registry, enable_profiling=True)

    def test_performance_profiler_timing(self) -> None:
        profiler = ValidationPerformanceProfiler(enabled=True)
        profiler.start()

        with profiler.profile_tier("TIER_1"):
            time.sleep(0.01)

        total_ms = profiler.stop()
        self.assertGreater(total_ms, 5.0)
        self.assertIn("TIER_1", profiler.tier_durations_ms)
        self.assertGreater(profiler.tier_durations_ms["TIER_1"], 5.0)

    def test_metrics_collector(self) -> None:
        metrics = ValidationMetricsCollector()
        metrics.record_tier_execution("TIER_1", 100)
        metrics.record_validator_execution("ACC_VAL_T1_REQ_FIELD_BATCH_ID", 100)
        metrics.record_error("CRITICAL", 2)
        metrics.record_dataset_run(100)

        self.assertEqual(metrics.tier_execution_counts["TIER_1"], 100)
        self.assertEqual(metrics.validator_execution_counts["ACC_VAL_T1_REQ_FIELD_BATCH_ID"], 100)
        self.assertEqual(metrics.severity_error_counts["CRITICAL"], 2)
        self.assertEqual(metrics.total_datasets_processed, 1)
        self.assertEqual(metrics.total_rows_processed, 100)

    def test_statistics_service(self) -> None:
        r1 = ValidationExecutionReport(
            dataset_id="DS-1",
            total_rows=10,
            valid_rows=10,
            invalid_rows=0,
            rows_passed_tier1=10,
            rows_passed_tier2=10,
            rows_passed_tier3=10,
            rows_passed_tier4=10,
            rows_passed_tier5=10,
            rows_quarantined=0,
            quality_score=100.0,
            total_execution_duration_ms=10.0,
            rows_per_second=1000.0,
        )
        r2 = ValidationExecutionReport(
            dataset_id="DS-2",
            total_rows=10,
            valid_rows=10,
            invalid_rows=0,
            rows_passed_tier1=10,
            rows_passed_tier2=10,
            rows_passed_tier3=10,
            rows_passed_tier4=10,
            rows_passed_tier5=10,
            rows_quarantined=0,
            quality_score=100.0,
            total_execution_duration_ms=20.0,
            rows_per_second=500.0,
        )

        stats = ValidationStatisticsService.calculate_aggregate_statistics([r1, r2])
        self.assertEqual(stats["count"], 2.0)
        self.assertEqual(stats["mean_execution_time_ms"], 15.0)
        self.assertEqual(stats["median_execution_time_ms"], 15.0)
        self.assertEqual(stats["avg_rows_per_second"], 750.0)

    def test_phase7_scaling_performance_benchmark(self) -> None:
        benchmark_results = []

        for row_count in [10, 1000, 10000, 100000]:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-{i:06d}",
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
            self.assertLess(per_row_ms, 0.50, f"Engine scaling validation speed for {row_count} rows exceeded limit: {per_row_ms:.4f} ms/row")

        print("\n========================================================================================================")
        print("SHARED VALIDATION ENGINE PHASE 7 SCALING PERFORMANCE BENCHMARK RESULTS")
        print("========================================================================================================")
        print(f"{'Row Count':<12} | {'Total Time (ms)':<18} | {'Speed (ms/row)':<18} | {'Throughput (rows/sec)':<22} | {'Status':<8}")
        print("--------------------------------------------------------------------------------------------------------")
        for count, total, speed, throughput, status in benchmark_results:
            print(f"{count:<12} | {total:<18.2f} | {speed:<18.4f} | {throughput:<22.2f} | {status:<8}")
        print("========================================================================================================\n")


if __name__ == "__main__":
    unittest.main()
