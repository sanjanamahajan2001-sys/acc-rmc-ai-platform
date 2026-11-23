"""Unit and Benchmark Test Suite for WS-03.3 Phase 5 Tier 3 & Tier 4 Business Validators."""

from datetime import datetime, timezone
from decimal import Decimal
import time
import unittest
from src.mapping.contracts import CanonicalRow
from src.validation import (
    CrossFieldValidator,
    EnumerationValidator,
    FieldErrorDetail,
    NumericRangeValidator,
    ReferentialIntegrityValidator,
    RuleExecutionContext,
    ValidationContext,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationTier,
    register_tier3_rules,
    register_tier4_rules,
)


class TestTier3Tier4Validators(unittest.TestCase):
    """Unit, regression, registry integration, and performance benchmark test suite for Tier 3 and Tier 4 validators."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_tier3_rules(self.registry)
        register_tier4_rules(self.registry)
        self.val_ctx = ValidationContext(profile_id="PROF-TEST-T3T4", source_channel="EXCEL")

    def test_numeric_range_validator_boundaries(self) -> None:
        val_slump = NumericRangeValidator("FIELD_SLUMP_MM", min_value=0.0, max_value=280.0)

        # Valid
        row_valid = CanonicalRow(row_index=0, fields={"FIELD_SLUMP_MM": 150.0})
        ctx_valid = RuleExecutionContext(row=row_valid, context=self.val_ctx)
        self.assertIsNone(val_slump.validate(150.0, ctx_valid))

        # Below minimum
        row_low = CanonicalRow(row_index=0, fields={"FIELD_SLUMP_MM": -10.0})
        ctx_low = RuleExecutionContext(row=row_low, context=self.val_ctx)
        err_low = val_slump.validate(-10.0, ctx_low)
        self.assertIsNotNone(err_low)
        self.assertEqual(err_low.error_code, "ACC_VAL_BELOW_MINIMUM")

        # Above maximum
        row_high = CanonicalRow(row_index=0, fields={"FIELD_SLUMP_MM": 350.0})
        ctx_high = RuleExecutionContext(row=row_high, context=self.val_ctx)
        err_high = val_slump.validate(350.0, ctx_high)
        self.assertIsNotNone(err_high)
        self.assertEqual(err_high.error_code, "ACC_VAL_ABOVE_MAXIMUM")

    def test_enumeration_validator(self) -> None:
        val_status = EnumerationValidator("FIELD_BATCH_STATUS", allowed_values=["COMPLETED", "IN_PROGRESS", "REJECTED"])

        # Valid
        row = CanonicalRow(row_index=0, fields={"FIELD_BATCH_STATUS": "COMPLETED"})
        ctx = RuleExecutionContext(row=row, context=self.val_ctx)
        self.assertIsNone(val_status.validate("COMPLETED", ctx))

        # Invalid
        row_bad = CanonicalRow(row_index=0, fields={"FIELD_BATCH_STATUS": "UNKNOWN_STATUS"})
        ctx_bad = RuleExecutionContext(row=row_bad, context=self.val_ctx)
        err = val_status.validate("UNKNOWN_STATUS", ctx_bad)
        self.assertIsNotNone(err)
        self.assertEqual(err.error_code, "ACC_VAL_UNSUPPORTED_ENUM_VALUE")

    def test_cross_field_validator_wc_ratio(self) -> None:
        val_wc = CrossFieldValidator(
            rule_id="ACC_VAL_T4_WC_RATIO_CHECK",
            rule_name="W/C Check",
            description="Verify W/C ratio math",
            target_field_id="FIELD_WATER_CEMENT_RATIO",
        )

        # Valid relationship (160 / 400 = 0.40)
        row_valid = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": 400.0, "FIELD_ACTUAL_WATER_KG": 160.0, "FIELD_WATER_CEMENT_RATIO": 0.40})
        ctx_valid = RuleExecutionContext(row=row_valid, context=self.val_ctx)
        self.assertIsNone(val_wc.validate(None, ctx_valid))

        # Inconsistent relationship (160 / 400 = 0.40, reported 0.65)
        row_bad = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": 400.0, "FIELD_ACTUAL_WATER_KG": 160.0, "FIELD_WATER_CEMENT_RATIO": 0.65})
        ctx_bad = RuleExecutionContext(row=row_bad, context=self.val_ctx)
        err = val_wc.validate(None, ctx_bad)
        self.assertIsNotNone(err)
        self.assertEqual(err.error_code, "ACC_VAL_CROSS_FIELD_WC_MISMATCH")

    def test_referential_integrity_validator(self) -> None:
        val_ref = ReferentialIntegrityValidator("FIELD_PLANT_ID", valid_keys_set={"PLANT-MUM-01", "PLANT-DEL-02"})

        # Valid reference
        row_valid = CanonicalRow(row_index=0, fields={"FIELD_PLANT_ID": "PLANT-MUM-01"})
        ctx_valid = RuleExecutionContext(row=row_valid, context=self.val_ctx)
        self.assertIsNone(val_ref.validate("PLANT-MUM-01", ctx_valid))

        # Missing foreign key reference
        row_bad = CanonicalRow(row_index=0, fields={"FIELD_PLANT_ID": "PLANT-INVALID"})
        ctx_bad = RuleExecutionContext(row=row_bad, context=self.val_ctx)
        err = val_ref.validate("PLANT-INVALID", ctx_bad)
        self.assertIsNotNone(err)
        self.assertEqual(err.error_code, "ACC_VAL_FOREIGN_KEY_NOT_FOUND")

    def test_tier3_tier4_performance_benchmark(self) -> None:
        t3_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_3_RANGES_ENUMS)
        t4_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_4_CROSS_FIELD_REFERENTIAL)
        all_rules = t3_rules + t4_rules

        benchmark_results = []

        for row_count in [10, 1000, 10000]:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-{i:05d}",
                        "FIELD_PLANT_ID": "PLANT-MUM-01",
                        "FIELD_SLUMP_MM": 150.0,
                        "FIELD_ACTUAL_CEMENT_KG": 400.0,
                        "FIELD_ACTUAL_WATER_KG": 160.0,
                        "FIELD_WATER_CEMENT_RATIO": 0.40,
                        "FIELD_BATCH_STATUS": "COMPLETED",
                    },
                )
                for i in range(row_count)
            ]

            t0 = time.perf_counter()
            error_count = 0
            val_options_ctx = ValidationContext(profile_id="P1", options={"FIELD_PLANT_ID": ["PLANT-MUM-01"]})

            for r in rows:
                exec_ctx = RuleExecutionContext(row=r, context=val_options_ctx)
                for rule in all_rules:
                    val = r.fields.get(rule.target_field_id) if hasattr(rule, "target_field_id") else None
                    res = rule.validate(val, exec_ctx)
                    if res is not None:
                        error_count += 1
            t1 = time.perf_counter()

            total_ms = (t1 - t0) * 1000.0
            per_row_ms = total_ms / row_count
            pass_status = "PASS" if per_row_ms < 0.50 else "FAIL"

            benchmark_results.append((row_count, total_ms, per_row_ms, pass_status))
            self.assertEqual(error_count, 0)
            self.assertLess(per_row_ms, 0.50, f"Tier 3 & 4 validation speed for {row_count} rows exceeded limit: {per_row_ms:.4f} ms/row")

        print("\n==========================================================================================")
        print("TIER 3 & TIER 4 PERFORMANCE BENCHMARK RESULTS")
        print("==========================================================================================")
        print(f"{'Row Count':<12} | {'Total Time (ms)':<18} | {'Speed (ms/row)':<18} | {'Requirement':<15} | {'Status':<8}")
        print("------------------------------------------------------------------------------------------")
        for count, total, speed, status in benchmark_results:
            print(f"{count:<12} | {total:<18.2f} | {speed:<18.4f} | {'< 0.50 ms/row':<15} | {status:<8}")
        print("==========================================================================================\n")


if __name__ == "__main__":
    unittest.main()
