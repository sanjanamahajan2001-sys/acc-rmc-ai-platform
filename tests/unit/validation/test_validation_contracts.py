"""Unit test suite for WS-03.3 Phase 1 Validation Foundation & Contract Layer."""

from datetime import datetime, timezone
import json
import unittest
from pydantic import ValidationError
from src.validation import (
    DEFAULT_SLUMP_MAX_MM,
    DEFAULT_SLUMP_MIN_MM,
    DatasetValidationResult,
    FieldErrorDetail,
    RowValidationResult,
    ValidationCategory,
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
    ValidationSummaryReport,
    ValidationTier,
)


class TestValidationPhase1Contracts(unittest.TestCase):
    """Unit test suite verifying Phase 1 contracts, immutability, serialization, and layer isolation."""

    def test_field_error_detail_immutability(self) -> None:
        err = FieldErrorDetail(
            field_id="FIELD_SLUMP_MM",
            original_header="Slump (mm)",
            rule_id="ACC_VAL_001",
            tier=ValidationTier.TIER_3_RANGES_ENUMS,
            severity=ValidationSeverity.ERROR,
            error_code="ACC_VAL_RANGE_EXCEEDED",
            message="Slump value 300mm exceeds maximum threshold of 280mm.",
            invalid_value=300.0,
            category=ValidationCategory.CONCRETE,
        )

        self.assertEqual(err.field_id, "FIELD_SLUMP_MM")
        self.assertEqual(err.severity, ValidationSeverity.ERROR)
        self.assertEqual(err.tier, ValidationTier.TIER_3_RANGES_ENUMS)
        self.assertEqual(err.category, ValidationCategory.CONCRETE)

        # Immutability check
        with self.assertRaises(ValidationError):
            err.severity = ValidationSeverity.CRITICAL  # type: ignore

    def test_validation_context_default_factory(self) -> None:
        ctx = ValidationContext(profile_id="PROF-001", plant_id="PLANT-MUM-01")
        self.assertEqual(ctx.profile_id, "PROF-001")
        self.assertEqual(ctx.source_channel, "EXCEL")
        self.assertIsInstance(ctx.execution_time, datetime)

    def test_row_and_dataset_validation_result_serialization(self) -> None:
        err = FieldErrorDetail(
            field_id="FIELD_BATCH_ID",
            rule_id="ACC_VAL_REQ_01",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            severity=ValidationSeverity.CRITICAL,
            error_code="ACC_VAL_REQUIRED_MISSING",
            message="Batch ID is required.",
        )

        row_res = RowValidationResult(row_index=0, is_valid=False, has_warnings=False, errors=[err])

        summary = ValidationSummaryReport(
            total_records=1,
            valid_records_count=0,
            critical_errors_count=1,
            error_count=0,
            warning_count=0,
            info_count=0,
            quality_score=0.0,
        )

        dataset_res = DatasetValidationResult(
            dataset_id="DS-VAL-TEST-001",
            is_valid=False,
            summary=summary,
            row_results=[row_res],
        )

        # JSON Roundtrip test
        json_str = dataset_res.model_dump_json()
        data = json.loads(json_str)
        self.assertEqual(data["dataset_id"], "DS-VAL-TEST-001")
        self.assertFalse(data["is_valid"])
        self.assertEqual(data["summary"]["critical_errors_count"], 1)

        # JSON schema generation test
        schema = DatasetValidationResult.model_json_schema()
        self.assertIn("properties", schema)
        self.assertIn("dataset_id", schema["properties"])

    def test_constants_definitions(self) -> None:
        self.assertEqual(DEFAULT_SLUMP_MIN_MM, 0.0)
        self.assertEqual(DEFAULT_SLUMP_MAX_MM, 280.0)


if __name__ == "__main__":
    unittest.main()
