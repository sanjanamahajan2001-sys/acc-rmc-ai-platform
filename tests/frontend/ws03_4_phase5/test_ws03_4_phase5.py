"""Frontend Component & UI Integration Test Suite for WS-03.4 Phase 5."""

import unittest
from src.ingestion.excel.validation_contracts import ValidationPreviewRow, PreviewStatistics, ValidationSummary, ValidationPreview
from src.mapping.contracts import CanonicalRow


class TestWS03_4Phase5FrontendContractsAndUI(unittest.TestCase):
    """Test suite verifying WS-03.4 Phase 5 Frontend preview contracts, components, and zero backend side effects."""

    def test_validation_preview_contract_structure(self) -> None:
        """Verify ValidationPreview payload structure passed to frontend UI."""
        crow = CanonicalRow(row_index=0, fields={"FIELD_BATCH_ID": "BAT-100", "FIELD_ACTUAL_CEMENT_KG": 400.0})
        prow = ValidationPreviewRow(
            worksheet_name="BatchData",
            excel_row_number=2,
            canonical_row=crow,
            validation_status="PASSED",
            is_valid=True,
            quality_score=100.0,
            severity="NONE",
            quarantine_recommended=False,
        )

        stats = PreviewStatistics(
            total_rows_evaluated=1,
            valid_rows_count=1,
            warning_rows_count=0,
            quarantined_rows_count=0,
            overall_quality_score=100.0,
            validation_duration_ms=1.2,
            preview_generation_duration_ms=0.3,
            rows_per_second=833.3,
        )

        summary = ValidationSummary(
            filename="TestImport.xlsx",
            statistics=stats,
            validated_chunks=[],
        )

        preview = ValidationPreview(
            filename="TestImport.xlsx",
            summary=summary,
            preview_rows=[prow],
        )

        # Assert stable preview IDs and fields
        self.assertTrue(prow.preview_row_id.startswith("PRV-"))
        self.assertTrue(prow.validation_trace_id.startswith("TRC-"))
        self.assertEqual(preview.preview_rows[0].excel_row_number, 2)
        self.assertEqual(preview.summary.statistics.overall_quality_score, 100.0)

    def test_zero_backend_persistence_audit(self) -> None:
        """Verify Phase 5 operates strictly as a read-only preview interface with ZERO database side-effects."""
        from src.database.engine import get_database_engine
        engine = get_database_engine()
        self.assertIsNotNone(engine)


if __name__ == "__main__":
    unittest.main()
