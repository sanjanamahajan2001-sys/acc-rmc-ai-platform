"""Unit, Integration, and Performance Benchmarking Test Suite for WS-03.4 Phase 3 WS-03.2 Mapping Integration."""

import csv
import os
import tempfile
import time
import unittest
import openpyxl
from src.ingestion.excel import (
    ExcelMappingService,
    FileIngestionLifecycle,
    IngestionConfig,
    MappedWorksheetChunk,
    MappingExecutionSummary,
    MappingStatistics,
    RawRow,
    RawWorksheetChunk,
    StreamingExcelReader,
    UploadSessionManager,
)
from src.mapping.models import ImportColumnMapping, ImportProfile


class TestWS03_4Phase3CanonicalMappingIntegration(unittest.TestCase):
    """Test suite verifying WS-03.4 Phase 3 ExcelMappingService, WS-03.2 integration, state transitions, and benchmarks."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = IngestionConfig(chunk_size_rows=100)
        self.session_manager = UploadSessionManager(self.config)
        self.mapping_service = ExcelMappingService(self.session_manager)

        # Create custom vendor import profile
        self.profile = ImportProfile(
            profile_name="Mumbai SCADA Profile",
            profile_version="1.0.0",
            vendor_code="MUMBAI_VENDOR",
            description="Profile mapping vendor columns",
            mappings=[
                ImportColumnMapping(external_header="Batch_No", target_canonical_id="FIELD_BATCH_ID"),
                ImportColumnMapping(external_header="Plant_Code", target_canonical_id="FIELD_PLANT_ID"),
                ImportColumnMapping(external_header="Cement_Kg", target_canonical_id="FIELD_ACTUAL_CEMENT_KG"),
                ImportColumnMapping(external_header="Water_Kg", target_canonical_id="FIELD_ACTUAL_WATER_KG"),
                ImportColumnMapping(external_header="Slump_Mm", target_canonical_id="FIELD_SLUMP_MM"),
            ],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_sample_csv(self, filename: str, row_count: int) -> str:
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Batch_No", "Plant_Code", "Cement_Kg", "Water_Kg", "Slump_Mm", "Unknown_Header_Col"])
            for i in range(row_count):
                writer.writerow([f"BAT-{i:06d}", "PLANT-MUM-01", 420.0, 168.0, 150.0, f"Extra_{i}"])
        return path

    def test_chunk_canonical_mapping(self) -> None:
        """Verify transforming RawWorksheetChunk into MappedWorksheetChunk with CanonicalRow objects."""
        raw_chunk = RawWorksheetChunk(
            worksheet_name="Sheet1",
            chunk_index=0,
            starting_row=0,
            ending_row=1,
            rows=[
                RawRow(
                    row_index=0,
                    data={
                        "Batch_No": "BAT-000001",
                        "Plant_Code": "PLANT-MUM-01",
                        "Cement_Kg": "420.00",
                        "Water_Kg": "168.00",
                        "Slump_Mm": "150.0",
                        "Unknown_Header_Col": "Dummy",
                    },
                ),
            ],
        )

        mapped_chunk = self.mapping_service.map_chunk(raw_chunk, profile=self.profile)

        self.assertIsInstance(mapped_chunk, MappedWorksheetChunk)
        self.assertEqual(mapped_chunk.worksheet_name, "Sheet1")
        self.assertEqual(len(mapped_chunk.canonical_rows), 1)

        canon_row = mapped_chunk.canonical_rows[0]
        self.assertEqual(canon_row.row_index, 0)
        self.assertEqual(canon_row.fields["FIELD_BATCH_ID"], "BAT-000001")
        self.assertEqual(canon_row.fields["FIELD_PLANT_ID"], "PLANT-MUM-01")

        # Verify unmapped headers capture
        self.assertIn("Unknown_Header_Col", mapped_chunk.unmapped_headers)

    def test_map_file_and_state_machine_transition(self) -> None:
        """Verify map_file streaming integration and advancing session state to MAPPING."""
        session = self.session_manager.create_session(user_id="OPERATOR-PHASE3")
        task = self.session_manager.enqueue_file(session_id=session.session_id, filename="MapTest.csv", file_size_bytes=500)

        # Advance lifecycle: QUEUED -> UPLOADING -> UPLOAD_COMPLETED -> CHECKSUM_VERIFICATION -> SCANNING -> READING_WORKBOOK -> READING_WORKSHEETS
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)

        csv_path = self._create_sample_csv("MapTest.csv", 150)
        summary = self.mapping_service.map_file(
            file_path=csv_path,
            profile=self.profile,
            session_id=session.session_id,
            file_id=task.file_id,
        )

        self.assertIsInstance(summary, MappingExecutionSummary)
        self.assertEqual(summary.statistics.processed_rows, 150)
        self.assertEqual(summary.statistics.mapped_rows, 150)

        # Assert session state advanced to MAPPING
        updated_session = self.session_manager.get_session(session.session_id)
        updated_task = updated_session.files[0]
        self.assertEqual(updated_task.status, FileIngestionLifecycle.MAPPING)
        self.assertEqual(updated_task.current_step_description, "Executing WS-03.2 Canonical Column Mapping")

    def test_unmapped_headers_and_fuzzy_fallback(self) -> None:
        """Verify handling of unknown headers and fallback mapping."""
        csv_path = self._create_sample_csv("Unmapped.csv", 10)
        summary = self.mapping_service.map_file(file_path=csv_path, profile=None)

        self.assertEqual(summary.statistics.processed_rows, 10)
        self.assertEqual(len(summary.worksheet_chunks), 1)
        self.assertIn("Unknown_Header_Col", summary.worksheet_chunks[0].unmapped_headers)

    def test_mapping_performance_scaling_benchmark(self) -> None:
        """Benchmark canonical mapping throughput and scaling across 10, 1,000, 10,000, and 100,000 rows."""
        row_counts = [10, 1000, 10000, 100000]
        results = []

        print("\n========================================================================================================")
        print("WS-03.4 PHASE 3 CANONICAL MAPPING ENGINE INTEGRATION SCALING BENCHMARKS")
        print("========================================================================================================")
        print(f"{'Row Count':<12} | {'Mapping Latency (ms)':<22} | {'Speed (ms/row)':<18} | {'Throughput (rows/sec)':<22} | {'Status':<8}")
        print("--------------------------------------------------------------------------------------------------------")

        for count in row_counts:
            csv_path = self._create_sample_csv(f"map_bench_{count}.csv", count)

            t0 = time.perf_counter()
            summary = self.mapping_service.map_file(file_path=csv_path, profile=self.profile, chunk_size=1000)
            t1 = time.perf_counter()

            total_ms = (t1 - t0) * 1000.0
            speed_per_row = total_ms / count
            throughput = (count / (total_ms / 1000.0)) if total_ms > 0 else 0.0
            pass_status = "PASS" if speed_per_row < 0.75 else "FAIL"

            results.append((count, total_ms, speed_per_row, throughput, pass_status))

            print(f"{count:<12} | {total_ms:<22.2f} | {speed_per_row:<18.4f} | {throughput:<22.2f} | {pass_status:<8}")
            self.assertEqual(summary.statistics.mapped_rows, count)

        print("========================================================================================================\n")


if __name__ == "__main__":
    unittest.main()
