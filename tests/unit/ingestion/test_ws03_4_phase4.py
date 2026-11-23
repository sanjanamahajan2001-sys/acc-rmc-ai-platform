"""Unit, Integration, and Performance Benchmarking Test Suite for WS-03.4 Phase 4 Validation Integration & Preview Generation."""

import csv
import os
import tempfile
import time
import unittest
from src.ingestion.excel import (
    ExcelMappingService,
    ExcelValidationService,
    FileIngestionLifecycle,
    IngestionConfig,
    UploadSessionManager,
    ValidatedWorksheetChunk,
    ValidationPreview,
    ValidationSummary,
)
from src.mapping.models import ImportColumnMapping, ImportProfile


class TestWS03_4Phase4ValidationIntegrationAndPreview(unittest.TestCase):
    """Test suite verifying WS-03.4 Phase 4 ExcelValidationService, Tiers 1-5 validation, preview contracts, and benchmarks."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = IngestionConfig(chunk_size_rows=100)
        self.session_manager = UploadSessionManager(self.config)
        self.mapping_service = ExcelMappingService(self.session_manager)
        self.validation_service = ExcelValidationService(self.session_manager)

        # Profile mapping vendor columns to canonical fields
        self.profile = ImportProfile(
            profile_name="Validation Ingestion Profile",
            profile_version="1.0.0",
            vendor_code="VAL_VENDOR",
            description="Profile for validation testing",
            mappings=[
                ImportColumnMapping(external_header="Batch_No", target_canonical_id="FIELD_BATCH_ID"),
                ImportColumnMapping(external_header="Cement_Kg", target_canonical_id="FIELD_ACTUAL_CEMENT_KG"),
                ImportColumnMapping(external_header="Water_Kg", target_canonical_id="FIELD_ACTUAL_WATER_KG"),
            ],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_sample_csv(self, filename: str, valid_rows: int, invalid_rows: int) -> str:
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Batch_No", "Cement_Kg", "Water_Kg"])

            # Write valid rows
            for i in range(valid_rows):
                writer.writerow([f"BAT-{i:06d}", 420.0, 168.0])

            # Write invalid rows (e.g., negative cement, non-numeric water, missing batch ID)
            for i in range(invalid_rows):
                writer.writerow(["", -50.0, "INVALID_NUM"])

        return path

    def test_multi_tier_validation_and_preview_generation(self) -> None:
        """Verify executing Tiers 1-5 validation and generating ValidationPreview with correct Excel row numbers."""
        csv_path = self._create_sample_csv("val_test.csv", valid_rows=10, invalid_rows=2)

        # Map file first
        mapping_summary = self.mapping_service.map_file(file_path=csv_path, profile=self.profile)

        # Validate summary
        preview = self.validation_service.validate_summary(mapping_summary)

        self.assertIsInstance(preview, ValidationPreview)
        self.assertEqual(len(preview.preview_rows), 12)

        # Check valid row preview
        row1 = preview.preview_rows[0]
        self.assertEqual(row1.excel_row_number, 2)  # Row 1 is header, data row 0 is physical row 2
        self.assertTrue(row1.is_valid)
        self.assertEqual(row1.validation_status, "PASSED")
        self.assertFalse(row1.quarantine_recommended)

        # Check invalid row preview
        row11 = preview.preview_rows[10]
        self.assertEqual(row11.excel_row_number, 12)

        # Verify summary statistics
        stats = preview.summary.statistics
        self.assertEqual(stats.total_rows_evaluated, 12)

    def test_session_lifecycle_state_transitions(self) -> None:
        """Verify task lifecycle advances strictly through VALIDATING -> GENERATING_PREVIEW and STOPS."""
        session = self.session_manager.create_session(user_id="OPERATOR-PHASE4")
        task = self.session_manager.enqueue_file(session_id=session.session_id, filename="StateVal.csv", file_size_bytes=400)

        # Advance lifecycle to READING_WORKSHEETS
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)

        csv_path = self._create_sample_csv("StateVal.csv", valid_rows=5, invalid_rows=0)
        mapping_summary = self.mapping_service.map_file(
            file_path=csv_path,
            profile=self.profile,
            session_id=session.session_id,
            file_id=task.file_id,
        )

        preview = self.validation_service.validate_summary(mapping_summary)

        # Assert final task status is GENERATING_PREVIEW
        updated_session = self.session_manager.get_session(session.session_id)
        updated_task = updated_session.files[0]
        self.assertEqual(updated_task.status, FileIngestionLifecycle.GENERATING_PREVIEW)
        self.assertEqual(updated_task.current_step_description, "Compiling Immutable Validation Preview Contracts")

    def test_validation_performance_and_preview_scaling_benchmark(self) -> None:
        """Benchmark multi-tier validation latency and preview generation across 10, 1,000, 10,000, and 100,000 rows."""
        row_counts = [10, 1000, 10000, 100000]

        print("\n========================================================================================================")
        print("WS-03.4 PHASE 4 VALIDATION ENGINE & PREVIEW GENERATION SCALING BENCHMARKS")
        print("========================================================================================================")
        print(f"{'Row Count':<12} | {'Validation Latency (ms)':<24} | {'Preview Gen (ms)':<18} | {'Throughput (rows/sec)':<22} | {'Quality Score':<14}")
        print("--------------------------------------------------------------------------------------------------------")

        for count in row_counts:
            csv_path = self._create_sample_csv(f"val_bench_{count}.csv", valid_rows=count, invalid_rows=0)
            mapping_summary = self.mapping_service.map_file(file_path=csv_path, profile=self.profile, chunk_size=1000)

            t0 = time.perf_counter()
            preview = self.validation_service.validate_summary(mapping_summary)
            t1 = time.perf_counter()

            stats = preview.summary.statistics
            total_ms = (t1 - t0) * 1000.0

            print(
                f"{count:<12} | {stats.validation_duration_ms:<24.2f} | {stats.preview_generation_duration_ms:<18.2f} | {stats.rows_per_second:<22.2f} | {stats.overall_quality_score:<14.2f}"
            )
            self.assertEqual(stats.total_rows_evaluated, count)
            self.assertEqual(stats.valid_rows_count, count)

        print("========================================================================================================\n")


if __name__ == "__main__":
    unittest.main()
