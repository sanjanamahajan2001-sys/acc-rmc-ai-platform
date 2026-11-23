"""Unit and Benchmark Test Suite for WS-03.3 Phase 4 Tier 2 Primitive Type & Engineering Unit Validators."""

from datetime import datetime, timezone
from decimal import Decimal
import math
import time
import unittest
from src.mapping.contracts import CanonicalRow, MappingAuditRecord
from src.validation import (
    EngineeringUnitValidator,
    FieldErrorDetail,
    PrimitiveTypeValidator,
    RuleExecutionContext,
    ValidationContext,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationTier,
    register_tier2_rules,
)


class TestTier2Validators(unittest.TestCase):
    """Unit, regression, registry integration, and performance benchmark test suite for Tier 2 validators."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_tier2_rules(self.registry)
        self.val_ctx = ValidationContext(profile_id="PROF-TEST-T2", source_channel="EXCEL")

    def test_primitive_type_validator_valid(self) -> None:
        val_cement = PrimitiveTypeValidator("FIELD_ACTUAL_CEMENT_KG")
        row = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": Decimal("450.50")})
        ctx = RuleExecutionContext(row=row, context=self.val_ctx)

        err = val_cement.validate(Decimal("450.50"), ctx)
        self.assertIsNone(err)

    def test_primitive_type_validator_invalid_types(self) -> None:
        val_cement = PrimitiveTypeValidator("FIELD_ACTUAL_CEMENT_KG")
        row_invalid = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": "four_hundred_fifty"})
        ctx = RuleExecutionContext(row=row_invalid, context=self.val_ctx)

        err = val_cement.validate("four_hundred_fifty", ctx)
        self.assertIsNotNone(err)
        self.assertEqual(err.severity, ValidationSeverity.ERROR)
        self.assertEqual(err.error_code, "ACC_VAL_PRIMITIVE_NOT_DECIMAL")

    def test_primitive_type_validator_nan_infinity_rejection(self) -> None:
        val_cement = PrimitiveTypeValidator("FIELD_ACTUAL_CEMENT_KG")

        # Test float NaN
        row_nan = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": float("nan")})
        ctx_nan = RuleExecutionContext(row=row_nan, context=self.val_ctx)
        err_nan = val_cement.validate(float("nan"), ctx_nan)
        self.assertIsNotNone(err_nan)
        self.assertEqual(err_nan.error_code, "ACC_VAL_NUMERIC_NAN_INF")

        # Test float Infinity
        row_inf = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": float("inf")})
        ctx_inf = RuleExecutionContext(row=row_inf, context=self.val_ctx)
        err_inf = val_cement.validate(float("inf"), ctx_inf)
        self.assertIsNotNone(err_inf)
        self.assertEqual(err_inf.error_code, "ACC_VAL_NUMERIC_NAN_INF")

        # Test Decimal NaN
        row_dec_nan = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": Decimal("NaN")})
        ctx_dec_nan = RuleExecutionContext(row=row_dec_nan, context=self.val_ctx)
        err_dec_nan = val_cement.validate(Decimal("NaN"), ctx_dec_nan)
        self.assertIsNotNone(err_dec_nan)
        self.assertEqual(err_dec_nan.error_code, "ACC_VAL_NUMERIC_NAN_INF")

    def test_engineering_unit_validator_valid(self) -> None:
        val_unit = EngineeringUnitValidator("FIELD_ACTUAL_CEMENT_KG")
        audit = MappingAuditRecord(
            original_header="Cement (kg)",
            canonical_field_id="FIELD_ACTUAL_CEMENT_KG",
            resolution_strategy="EXACT",
            similarity_score=1.00,
            canonical_unit="kg",
        )
        row = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": Decimal("500.00")}, audit_records=[audit])
        ctx = RuleExecutionContext(row=row, context=self.val_ctx)

        err = val_unit.validate(Decimal("500.00"), ctx)
        self.assertIsNone(err)

    def test_engineering_unit_validator_incompatible_unit(self) -> None:
        val_unit = EngineeringUnitValidator("FIELD_ACTUAL_CEMENT_KG")
        audit = MappingAuditRecord(
            original_header="Cement (lbs)",
            canonical_field_id="FIELD_ACTUAL_CEMENT_KG",
            resolution_strategy="EXACT",
            similarity_score=1.00,
            canonical_unit="lbs",  # Wrong canonical unit!
        )
        row = CanonicalRow(row_index=0, fields={"FIELD_ACTUAL_CEMENT_KG": Decimal("500.00")}, audit_records=[audit])
        ctx = RuleExecutionContext(row=row, context=self.val_ctx)

        err = val_unit.validate(Decimal("500.00"), ctx)
        self.assertIsNotNone(err)
        self.assertEqual(err.severity, ValidationSeverity.ERROR)
        self.assertEqual(err.error_code, "ACC_VAL_INCOMPATIBLE_UNIT")

    def test_tier2_registry_integration_and_ordering(self) -> None:
        tier2_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_2_PRIMITIVES)
        self.assertGreater(len(tier2_rules), 0)

        # Verify priority ordering (PrimitiveTypeValidator priority 10 before EngineeringUnitValidator priority 20)
        prims = [r for r in tier2_rules if isinstance(r, PrimitiveTypeValidator)]
        units = [r for r in tier2_rules if isinstance(r, EngineeringUnitValidator)]

        self.assertEqual(prims[0].execution_priority, 10)
        self.assertEqual(units[0].execution_priority, 20)

    def test_tier2_performance_benchmark(self) -> None:
        tier2_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_2_PRIMITIVES)

        benchmark_results = []

        for row_count in [10, 1000, 10000]:
            audit = MappingAuditRecord(
                original_header="Actual Cement",
                canonical_field_id="FIELD_ACTUAL_CEMENT_KG",
                resolution_strategy="EXACT",
                similarity_score=1.00,
                canonical_unit="kg",
            )
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-{i:05d}",
                        "FIELD_ACTUAL_CEMENT_KG": Decimal("400.00"),
                        "FIELD_ACTUAL_WATER_KG": Decimal("160.00"),
                        "FIELD_BATCH_DATETIME": datetime.now(timezone.utc),
                    },
                    audit_records=[audit],
                )
                for i in range(row_count)
            ]

            t0 = time.perf_counter()
            error_count = 0
            for r in rows:
                exec_ctx = RuleExecutionContext(row=r, context=self.val_ctx)
                for rule in tier2_rules:
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
            self.assertLess(per_row_ms, 0.50, f"Tier 2 validation speed for {row_count} rows exceeded limit: {per_row_ms:.4f} ms/row")

        print("\n==========================================================================================")
        print("TIER 2 PERFORMANCE BENCHMARK RESULTS")
        print("==========================================================================================")
        print(f"{'Row Count':<12} | {'Total Time (ms)':<18} | {'Speed (ms/row)':<18} | {'Requirement':<15} | {'Status':<8}")
        print("------------------------------------------------------------------------------------------")
        for count, total, speed, status in benchmark_results:
            print(f"{count:<12} | {total:<18.2f} | {speed:<18.4f} | {'< 0.50 ms/row':<15} | {status:<8}")
        print("==========================================================================================\n")


if __name__ == "__main__":
    unittest.main()
