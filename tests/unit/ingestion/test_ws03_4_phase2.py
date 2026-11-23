"""Unit, Integration, Memory, and Performance Benchmarking Test Suite for WS-03.4 Phase 2."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import io
import os
import resource
import tempfile
import time
import unittest
import openpyxl
from src.ingestion.excel import (
    FileIngestionLifecycle,
    IngestionConfig,
    StreamingExcelReader,
    UploadSessionManager,
    WorkbookMetadata,
    WorkbookScanner,
)


class TestWS03_4Phase2StreamingReaderAndScanner(unittest.TestCase):
    """Test suite verifying WS-03.4 Phase 2 WorkbookScanner, StreamingExcelReader, low-memory streaming, and benchmarks."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = IngestionConfig(chunk_size_rows=100)
        self.scanner = WorkbookScanner(self.config)
        self.reader = StreamingExcelReader(self.config)
        self.session_manager = UploadSessionManager(self.config)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_sample_csv(self, filename: str, row_count: int, delimiter: str = ",") -> str:
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["BATCH_ID", "PLANT_ID", "CEMENT_KG", "WATER_KG", "SLUMP_MM"])
            for i in range(row_count):
                writer.writerow([f"BAT-{i:06d}", "PLANT-MUM-01", 400.0 + (i % 10), 160.0 + (i % 5), 150.0])
        return path

    def _create_sample_xlsx(self, filename: str, row_count: int, sheet_name: str = "BatchData") -> str:
        path = os.path.join(self.temp_dir.name, filename)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        ws.append(["BATCH_ID", "PLANT_ID", "CEMENT_KG", "WATER_KG", "SLUMP_MM"])
        for i in range(row_count):
            ws.append([f"BAT-{i:06d}", "PLANT-MUM-01", 400.0 + (i % 10), 160.0 + (i % 5), 150.0])
        wb.save(path)
        wb.close()
        return path

    def test_csv_scanning_and_delimiter_autodetect(self) -> None:
        """Verify CSV scanning, header extraction, row estimation, and auto-delimiter detection."""
        csv_path = self._create_sample_csv("test_semicolon.csv", 50, delimiter=";")
        meta = self.scanner.scan_file(csv_path)

        self.assertEqual(meta.workbook_type, ".csv")
        self.assertEqual(meta.worksheet_count, 1)
        self.assertEqual(meta.worksheet_names, ["Sheet1"])
        self.assertEqual(meta.detected_headers["Sheet1"], ["BATCH_ID", "PLANT_ID", "CEMENT_KG", "WATER_KG", "SLUMP_MM"])
        self.assertEqual(meta.estimated_row_counts["Sheet1"], 50)

    def test_xlsx_scanning_and_metadata(self) -> None:
        """Verify .xlsx scanning, sheet enumeration, and header extraction."""
        xlsx_path = self._create_sample_xlsx("test_batches.xlsx", 100, sheet_name="ProductionBatches")
        meta = self.scanner.scan_file(xlsx_path)

        self.assertEqual(meta.workbook_type, ".xlsx")
        self.assertEqual(meta.worksheet_count, 1)
        self.assertEqual(meta.worksheet_names, ["ProductionBatches"])
        self.assertEqual(meta.detected_headers["ProductionBatches"], ["BATCH_ID", "PLANT_ID", "CEMENT_KG", "WATER_KG", "SLUMP_MM"])
        self.assertEqual(meta.estimated_row_counts["ProductionBatches"], 100)

    def test_csv_chunked_streaming(self) -> None:
        """Verify StreamingExcelReader yielding chunked row dicts from CSV."""
        csv_path = self._create_sample_csv("test_stream.csv", 250)
        chunks = list(self.reader.stream_worksheet_rows(csv_path, chunk_size=100))

        self.assertEqual(len(chunks), 3)  # 100 + 100 + 50
        self.assertEqual(len(chunks[0]), 100)
        self.assertEqual(len(chunks[1]), 100)
        self.assertEqual(len(chunks[2]), 50)

        # Assert dictionary key structure
        first_row = chunks[0][0]
        self.assertEqual(first_row["BATCH_ID"], "BAT-000000")
        self.assertEqual(first_row["PLANT_ID"], "PLANT-MUM-01")

    def test_raw_worksheet_chunk_contract_streaming(self) -> None:
        """Verify StreamingExcelReader yielding structured RawWorksheetChunk contracts for Phase 3 mapping integration."""
        csv_path = self._create_sample_csv("test_chunk_contract.csv", 150)
        chunks = list(self.reader.stream_worksheet_chunks(csv_path, chunk_size=100))

        self.assertEqual(len(chunks), 2)
        chunk0 = chunks[0]
        self.assertEqual(chunk0.worksheet_name, "Sheet1")
        self.assertEqual(chunk0.chunk_index, 0)
        self.assertEqual(chunk0.starting_row, 0)
        self.assertEqual(chunk0.ending_row, 99)
        self.assertEqual(len(chunk0.rows), 100)
        self.assertEqual(chunk0.rows[0].row_index, 0)
        self.assertEqual(chunk0.rows[0].data["BATCH_ID"], "BAT-000000")

        chunk1 = chunks[1]
        self.assertEqual(chunk1.chunk_index, 1)
        self.assertEqual(chunk1.starting_row, 100)
        self.assertEqual(chunk1.ending_row, 149)
        self.assertEqual(len(chunk1.rows), 50)

    def test_xlsx_chunked_streaming(self) -> None:
        """Verify StreamingExcelReader yielding chunked row dicts from .xlsx."""
        xlsx_path = self._create_sample_xlsx("test_stream.xlsx", 150)
        chunks = list(self.reader.stream_worksheet_rows(xlsx_path, worksheet_name="BatchData", chunk_size=50))

        self.assertEqual(len(chunks), 3)  # 50 + 50 + 50
        self.assertEqual(len(chunks[0]), 50)
        self.assertEqual(chunks[0][0]["BATCH_ID"], "BAT-000000")

    def test_corrupt_file_handling(self) -> None:
        """Verify graceful error handling for corrupt / unreadable workbooks."""
        corrupt_path = os.path.join(self.temp_dir.name, "corrupt.xlsx")
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_REAL_EXCEL_FILE_DATA_BYTES")

        with self.assertRaises(ValueError):
            self.scanner.scan_file(corrupt_path)

        with self.assertRaises(ValueError):
            list(self.reader.stream_worksheet_rows(corrupt_path))

    def test_unsupported_extension_rejection(self) -> None:
        """Verify rejection of unsupported extensions."""
        bad_path = os.path.join(self.temp_dir.name, "unsupported.pdf")
        with open(bad_path, "w") as f:
            f.write("dummy")

        with self.assertRaises(ValueError):
            self.scanner.scan_file(bad_path)

    def test_session_lifecycle_integration_states(self) -> None:
        """Verify session integration advancing ONLY up to READING_WORKSHEETS."""
        session = self.session_manager.create_session(user_id="OPERATOR-PHASE2")
        task = self.session_manager.enqueue_file(session_id=session.session_id, filename="ScanTest.xlsx", file_size_bytes=1024)

        # Transition sequence: QUEUED -> UPLOADING -> UPLOAD_COMPLETED -> CHECKSUM_VERIFICATION -> SCANNING -> READING_WORKBOOK -> READING_WORKSHEETS
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        t_scan = self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.assertEqual(t_scan.status, FileIngestionLifecycle.SCANNING)

        t_wb = self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        self.assertEqual(t_wb.status, FileIngestionLifecycle.READING_WORKBOOK)

        t_ws = self.session_manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)
        self.assertEqual(t_ws.status, FileIngestionLifecycle.READING_WORKSHEETS)

    def test_performance_and_memory_benchmarks(self) -> None:
        """Benchmark scan latency, streaming throughput, and verify <50MB RAM target on 100,000 rows."""
        row_counts = [10, 1000, 10000, 100000]
        results = []

        print("\n========================================================================================================")
        print("WS-03.4 PHASE 2 STREAMING READER & WORKBOOK SCANNER SCALING BENCHMARKS")
        print("========================================================================================================")
        print(f"{'Row Count':<12} | {'Scan Latency (ms)':<20} | {'Stream Latency (ms)':<20} | {'Throughput (rows/sec)':<22} | {'RAM Used (MB)':<12}")
        print("--------------------------------------------------------------------------------------------------------")

        for count in row_counts:
            file_path = self._create_sample_csv(f"benchmark_{count}.csv", count)

            mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # MB on Linux

            # 1. Measure Scan Latency
            t0 = time.perf_counter()
            meta = self.scanner.scan_file(file_path)
            t1 = time.perf_counter()
            scan_ms = (t1 - t0) * 1000.0

            # 2. Measure Streaming Throughput
            t2 = time.perf_counter()
            total_read_rows = 0
            for chunk in self.reader.stream_worksheet_rows(file_path, chunk_size=1000):
                total_read_rows += len(chunk)
            t3 = time.perf_counter()
            stream_ms = (t3 - t2) * 1000.0

            mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            mem_used = max(0.1, mem_after - mem_before)

            throughput = (count / (stream_ms / 1000.0)) if stream_ms > 0 else 0.0
            results.append((count, scan_ms, stream_ms, throughput, mem_used))

            print(f"{count:<12} | {scan_ms:<20.2f} | {stream_ms:<20.2f} | {throughput:<22.2f} | {mem_used:<12.2f}")
            self.assertEqual(total_read_rows, count)

        print("========================================================================================================\n")

        # Assert memory usage target (<50MB) for 100,000 rows
        hundred_k_res = results[-1]
        self.assertLess(hundred_k_res[4], 50.0, "RAM usage exceeded 50MB target for 100,000-row streaming!")


if __name__ == "__main__":
    unittest.main()
