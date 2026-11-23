"""Unit and Performance Test Suite for WS-03.4 Phase 1 Infrastructure."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import time
import unittest
from src.ingestion.excel import (
    DuplicateDetector,
    FileIngestionLifecycle,
    FileUploadTask,
    IngestionConfig,
    UploadSession,
    UploadSessionLifecycle,
    UploadSessionManager,
    UploadSessionSummaryContract,
    calculate_bytes_sha256,
)


class TestWS03_4Phase1Infrastructure(unittest.TestCase):
    """Test suite verifying WS-03.4 Phase 1 infrastructure, state machine transitions, configuration limits, and thread safety."""

    def setUp(self) -> None:
        self.config = IngestionConfig(
            max_files_per_session=5,
            max_file_size_bytes=10_000_000,
            allowed_extensions=[".xlsx", ".xls", ".csv"],
            duplicate_hash_check_enabled=True,
        )
        self.manager = UploadSessionManager(self.config)

    def test_configuration_validation(self) -> None:
        """Verify IngestionConfig model boundary enforcement."""
        cfg = IngestionConfig()
        self.assertEqual(cfg.max_files_per_session, 20)
        self.assertEqual(cfg.max_file_size_bytes, 104_857_600)
        self.assertIn(".xlsx", cfg.allowed_extensions)

        with self.assertRaises(ValueError):
            IngestionConfig(max_files_per_session=0)

        with self.assertRaises(ValueError):
            IngestionConfig(max_file_size_bytes=100)

    def test_session_creation(self) -> None:
        """Verify session creation and lookup."""
        session = self.manager.create_session(user_id="USER-OPERATOR-01")
        self.assertTrue(session.session_id.startswith("SES-"))
        self.assertEqual(session.user_id, "USER-OPERATOR-01")
        self.assertEqual(session.status, UploadSessionLifecycle.CREATED)

        fetched = self.manager.get_session(session.session_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.session_id, session.session_id)

    def test_enqueue_file_and_limits(self) -> None:
        """Verify file enqueueing and configuration limits."""
        session = self.manager.create_session(user_id="U1")

        # 1. Enqueue valid file
        task = self.manager.enqueue_file(
            session_id=session.session_id,
            filename="Plant_Mumbai_Aug2026.xlsx",
            file_size_bytes=1_000_000,
        )
        self.assertEqual(task.status, FileIngestionLifecycle.QUEUED)
        self.assertEqual(task.filename, "Plant_Mumbai_Aug2026.xlsx")

        # 2. Exceed file size limit
        with self.assertRaises(ValueError):
            self.manager.enqueue_file(
                session_id=session.session_id,
                filename="HugeFile.xlsx",
                file_size_bytes=50_000_000,
            )

        # 3. Invalid file extension
        with self.assertRaises(ValueError):
            self.manager.enqueue_file(
                session_id=session.session_id,
                filename="Report.pdf",
                file_size_bytes=1_000,
            )

    def test_sha256_duplicate_detection(self) -> None:
        """Verify SHA-256 calculation and duplicate file rejection."""
        session = self.manager.create_session(user_id="U1")
        file_bytes = b"BATCH_ID,PLANT_ID\nBAT-001,PLANT-MUM-01\n"

        # First file upload -> valid
        task1 = self.manager.enqueue_file(
            session_id=session.session_id,
            filename="Batch_File_1.csv",
            file_size_bytes=len(file_bytes),
            file_bytes=file_bytes,
        )
        self.assertEqual(task1.status, FileIngestionLifecycle.QUEUED)

        # Duplicate file upload -> DUPLICATE_REJECTED
        task2 = self.manager.enqueue_file(
            session_id=session.session_id,
            filename="Batch_File_1_Copy.csv",
            file_size_bytes=len(file_bytes),
            file_bytes=file_bytes,
        )
        self.assertEqual(task2.status, FileIngestionLifecycle.DUPLICATE_REJECTED)

    def test_state_transitions(self) -> None:
        """Verify 16-state lifecycle transition sequence."""
        session = self.manager.create_session(user_id="U1")
        task = self.manager.enqueue_file(session_id=session.session_id, filename="Test.xlsx", file_size_bytes=100)

        # Transition path: QUEUED -> UPLOADING -> UPLOAD_COMPLETED -> CHECKSUM_VERIFICATION -> SCANNING -> READING_WORKBOOK -> READING_WORKSHEETS -> MAPPING -> VALIDATING -> GENERATING_PREVIEW -> COMPLETED
        t1 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.assertEqual(t1.status, FileIngestionLifecycle.UPLOADING)

        t2 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.assertEqual(t2.status, FileIngestionLifecycle.UPLOAD_COMPLETED)

        t3 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        self.assertEqual(t3.status, FileIngestionLifecycle.CHECKSUM_VERIFICATION)

        t4 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.assertEqual(t4.status, FileIngestionLifecycle.SCANNING)

        t5 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        t6 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)
        t7 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.MAPPING)
        t8 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.VALIDATING)
        t9 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.GENERATING_PREVIEW)
        t10 = self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.COMPLETED, rows_found=100, rows_valid=100, quality_score=100.0)

        self.assertEqual(t10.status, FileIngestionLifecycle.COMPLETED)
        self.assertEqual(t10.rows_valid, 100)

        # Invalid transition: COMPLETED -> UPLOADING (terminal state guard)
        with self.assertRaises(ValueError):
            self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)

    def test_session_summary_generation(self) -> None:
        """Verify UploadSessionSummaryContract creation."""
        session = self.manager.create_session(user_id="OPERATOR-99")
        task = self.manager.enqueue_file(session_id=session.session_id, filename="Data.csv", file_size_bytes=500)

        # Run task to completion
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.MAPPING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.VALIDATING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.GENERATING_PREVIEW)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.COMPLETED, rows_found=500, rows_valid=490, rows_invalid=10, quality_score=98.0)

        summary = self.manager.generate_session_summary(session.session_id)
        self.assertEqual(summary.session_id, session.session_id)
        self.assertEqual(summary.total_files, 1)
        self.assertEqual(summary.completed_files, 1)
        self.assertEqual(summary.total_rows_processed, 500)
        self.assertEqual(summary.overall_quality_score, 98.0)

    def test_thread_safety(self) -> None:
        """Verify thread-safe session manager under concurrent file uploads."""
        session = self.manager.create_session(user_id="U-THREAD")

        def add_file(index: int) -> str:
            fname = f"File_{index}.xlsx"
            task = self.manager.enqueue_file(session_id=session.session_id, filename=fname, file_size_bytes=1000)
            return task.file_id

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(add_file, i) for i in range(5)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 5)
        updated_session = self.manager.get_session(session.session_id)
        self.assertEqual(len(updated_session.files), 5)

    def test_session_recovery_serialization(self) -> None:
        """Verify UploadSession serialization and reconstruction (roundtrip equality) for Phase 6 recovery support."""
        session = self.manager.create_session(user_id="U-RECOVERY")
        task = self.manager.enqueue_file(session_id=session.session_id, filename="RecoveryTest.xlsx", file_size_bytes=4096)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOADING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.UPLOAD_COMPLETED)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.CHECKSUM_VERIFICATION)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.SCANNING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKBOOK)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.READING_WORKSHEETS)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.MAPPING)
        self.manager.update_task_status(session.session_id, task.file_id, FileIngestionLifecycle.VALIDATING, progress=75.0)

        original_session = self.manager.get_session(session.session_id)
        self.assertIsNotNone(original_session)

        # 1. Serialize session to JSON string (simulating session state recovery storage)
        json_data = original_session.model_dump_json()
        self.assertIn("SES-", json_data)
        self.assertIn("RecoveryTest.xlsx", json_data)

        # 2. Reconstruct session from JSON string
        reconstructed_session = UploadSession.model_validate_json(json_data)

        # 3. Assert full roundtrip fidelity
        self.assertEqual(reconstructed_session.session_id, original_session.session_id)
        self.assertEqual(reconstructed_session.user_id, original_session.user_id)
        self.assertEqual(reconstructed_session.status, original_session.status)
        self.assertEqual(len(reconstructed_session.files), len(original_session.files))
        self.assertEqual(reconstructed_session.files[0].file_id, original_session.files[0].file_id)
        self.assertEqual(reconstructed_session.files[0].status, original_session.files[0].status)
        self.assertEqual(reconstructed_session.files[0].progress_percentage, 75.0)


    def test_performance_benchmarks(self) -> None:
        """Benchmark session creation, queue insertion, and duplicate hashing latencies."""
        bm_mgr = UploadSessionManager(IngestionConfig(max_files_per_session=50))
        # 1. Session Creation Latency
        t0 = time.perf_counter()
        session = bm_mgr.create_session(user_id="BENCHMARK-USER")
        t1 = time.perf_counter()
        session_ms = (t1 - t0) * 1000.0

        # 2. Queue Insertion Latency (20 files)
        file_bytes_list = [f"COL1,COL2\nVAL_{i},VAL_{i}\n".encode("utf-8") for i in range(20)]
        t2 = time.perf_counter()
        for idx, fb in enumerate(file_bytes_list):
            bm_mgr.enqueue_file(
                session_id=session.session_id,
                filename=f"Bench_File_{idx}.csv",
                file_size_bytes=len(fb),
                file_bytes=fb,
            )
        t3 = time.perf_counter()
        queue_20_ms = (t3 - t2) * 1000.0
        per_file_ms = queue_20_ms / 20.0

        print("\n========================================================================")
        print("WS-03.4 PHASE 1 INFRASTRUCTURE PERFORMANCE BENCHMARK RESULTS")
        print("========================================================================")
        print(f"Session Creation Latency   : {session_ms:.4f} ms")
        print(f"Queue Insertion (20 Files) : {queue_20_ms:.4f} ms total ({per_file_ms:.4f} ms/file)")
        print("========================================================================\n")

        self.assertLess(session_ms, 5.0)
        self.assertLess(per_file_ms, 1.0)


if __name__ == "__main__":
    unittest.main()
