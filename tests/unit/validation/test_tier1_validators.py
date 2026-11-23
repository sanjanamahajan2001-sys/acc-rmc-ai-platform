"""Unit and Benchmark Test Suite for WS-03.3 Phase 3 Tier 1 Structural & Required Field Validators."""

import time
import unittest
from src.mapping.contracts import CanonicalDataset, CanonicalRow, MappingAuditRecord
from src.validation import (
    FieldErrorDetail,
    RequiredFieldValidator,
    RuleExecutionContext,
    StructuralSchemaValidator,
    ValidationContext,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationTier,
    register_tier1_rules,
)


class TestTier1Validators(unittest.TestCase):
    """Unit, regression, registry integration, and performance benchmark test suite for Tier 1 validators."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()
        register_tier1_rules(self.registry)
        self.val_ctx = ValidationContext(profile_id="PROF-TEST", source_channel="EXCEL")

    def test_structural_schema_validator_valid(self) -> None:
        validator = StructuralSchemaValidator()
        valid_row = CanonicalRow(row_index=0, fields={"FIELD_BATCH_ID": "BAT-001"})
        valid_ds = CanonicalDataset(profile_id="P1", profile_version="1.0.0", rows=[valid_row])
        exec_ctx = RuleExecutionContext(row=valid_row, dataset=valid_ds, context=self.val_ctx)

        err = validator.validate(None, exec_ctx)
        self.assertIsNone(err)

    def test_structural_schema_validator_malformed_row(self) -> None:
        validator = StructuralSchemaValidator()
        exec_ctx = RuleExecutionContext(row="invalid_string_instead_of_row", context=self.val_ctx)  # type: ignore

        err = validator.validate(None, exec_ctx)
        self.assertIsNotNone(err)
        self.assertEqual(err.severity, ValidationSeverity.CRITICAL)
        self.assertEqual(err.error_code, "ACC_VAL_INVALID_ROW_STRUCTURE")

    def test_required_field_validator_valid(self) -> None:
        validator = RequiredFieldValidator("FIELD_BATCH_ID", severity=ValidationSeverity.CRITICAL)
        row = CanonicalRow(row_index=0, fields={"FIELD_BATCH_ID": "BAT-VAL-100"})
        exec_ctx = RuleExecutionContext(row=row, context=self.val_ctx)

        err = validator.validate("BAT-VAL-100", exec_ctx)
        self.assertIsNone(err)

    def test_required_field_validator_missing_and_empty(self) -> None:
        validator = RequiredFieldValidator("FIELD_BATCH_ID", severity=ValidationSeverity.CRITICAL)

        # Missing / Null
        row_missing = CanonicalRow(row_index=0, fields={})
        ctx_missing = RuleExecutionContext(row=row_missing, context=self.val_ctx)
        err1 = validator.validate(None, ctx_missing)
        self.assertIsNotNone(err1)
        self.assertEqual(err1.error_code, "ACC_VAL_REQUIRED_FIELD_MISSING")
        self.assertEqual(err1.severity, ValidationSeverity.CRITICAL)

        # Empty / Whitespace-only
        row_empty = CanonicalRow(row_index=0, fields={"FIELD_BATCH_ID": "   "})
        ctx_empty = RuleExecutionContext(row=row_empty, context=self.val_ctx)
        err2 = validator.validate("   ", ctx_empty)
        self.assertIsNotNone(err2)
        self.assertEqual(err2.error_code, "ACC_VAL_REQUIRED_FIELD_EMPTY")

    def test_tier1_registry_integration_and_ordering(self) -> None:
        tier1_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_1_STRUCTURAL)
        self.assertGreaterEqual(len(tier1_rules), 7)  # Structural + 6 required fields

        # Verify priority ordering (Structural Schema priority 10 before Required Fields priority 20)
        self.assertEqual(tier1_rules[0].rule_id, "ACC_VAL_T1_STRUCTURAL")
        self.assertEqual(tier1_rules[0].execution_priority, 10)
        self.assertEqual(tier1_rules[1].execution_priority, 20)

    def test_tier1_performance_benchmark(self) -> None:
        # Benchmark over 10, 1000, 10,000 synthetic rows
        tier1_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_1_STRUCTURAL)

        for row_count in [10, 1000, 10000]:
            rows = [
                CanonicalRow(
                    row_index=i,
                    fields={
                        "FIELD_BATCH_ID": f"BAT-{i:05d}",
                        "FIELD_PLANT_ID": "PLANT-MUM",
                        "FIELD_RECIPE_ID": "REC-M40",
                        "FIELD_BATCH_DATETIME": "2026-08-07T12:00:00Z",
                        "FIELD_ACTUAL_CEMENT_KG": 400.0,
                        "FIELD_ACTUAL_WATER_KG": 160.0,
                    },
                )
                for i in range(row_count)
            ]

            t0 = time.perf_counter()
            error_count = 0
            for r in rows:
                exec_ctx = RuleExecutionContext(row=r, context=self.val_ctx)
                for rule in tier1_rules:
                    res = rule.validate(r.fields.get(rule.supports.__self__.target_field_id if hasattr(rule, "target_field_id") else ""), exec_ctx)
                    if res is not None:
                        error_count += 1
            t1 = time.perf_counter()

            total_ms = (t1 - t0) * 1000.0
            per_row_ms = total_ms / row_count

            self.assertEqual(error_count, 0)
            self.assertLess(per_row_ms, 0.50, f"Tier 1 validation speed for {row_count} rows exceeded limit: {per_row_ms:.4f} ms/row")
            print(f"\n[TIER 1 BENCHMARK] Rows: {row_count:5d} | Total Time: {total_ms:7.2f} ms | Speed: {per_row_ms:.4f} ms/row")


if __name__ == "__main__":
    unittest.main()
