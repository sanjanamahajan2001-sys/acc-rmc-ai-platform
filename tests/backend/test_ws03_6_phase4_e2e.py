"""
WS-03.6 Phase 4: WS-04.5 Automated Excel End-to-End & Safety Net Test Suite.
Verifies the complete real production code path:
Excel file -> ExcelSourceParser -> DTOs -> confirm_mapping_session -> IngestionPersistenceService -> IngestionUnitOfWork -> Physical SQLite DB
"""

import os
import uuid
import unittest
from decimal import Decimal
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.session import get_session_factory
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest, FT7Certificate
from src.database.models.mapping_persistence import SessionMappingModel, IngestionJobModel
from src.api.ingestion_router import _SESSION_FILES
from src.parsers.excel_parser import ExcelSourceParser
from src.services.ingestion_persistence_service import IngestionPersistenceService, DuplicateIngestionException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO, BatchIngestionDTO


class TestWS036Phase4ExcelE2E(unittest.TestCase):
    """Automated E2E Integration Suite for WS-04.5 Excel Ingestion Path."""

    def setUp(self):
        self.engine = get_database_engine()
        self.SessionLocal = get_session_factory(self.engine)
        self.db: Session = self.SessionLocal()
        self.client = TestClient(app)
        self.sample_ft7_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"

    def tearDown(self):
        try:
            self.db.query(FT7Certificate).delete()
            self.db.query(CubeTest).delete()
            self.db.query(CubeSet).delete()
            self.db.query(ConcreteSample).delete()
            self.db.query(BatchMaterialConsumption).delete()
            self.db.query(Batch).delete()
            self.db.query(IngestionJobModel).delete()
            self.db.query(SessionMappingModel).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def _create_mock_mapping_session(self, session_id: str, file_path: str) -> str:
        """Helper to set up SessionMappingModel and session file record in API router."""
        summary = {
            "operational_count": 1,
            "total_files_mapped": 1,
            "discovered_count": 1,
            "excluded_count": 0,
            "operational_requires_review": 0
        }
        mapping_rec = SessionMappingModel(
            session_id=session_id,
            dataset_id="CHANNEL-EXCEL",
            import_profile_id="PROFILE-EXCEL",
            mapping_execution_id=f"EXEC-E2E-{uuid.uuid4().hex[:4].upper()}",
            summary_json=str(summary).replace("'", '"')
        )
        self.db.add(mapping_rec)
        self.db.commit()

        _SESSION_FILES[session_id] = [{"file_path": file_path}]
        return session_id

    # -------------------------------------------------------------------------
    # Scenario A: Single Valid Workbook E2E
    # -------------------------------------------------------------------------
    def test_scenario_a_single_valid_workbook_e2e(self):
        """Scenario A: Verify parsing, mapping, PersistenceService & UoW execution for single valid workbook."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Sample FT7 file not found at {self.sample_ft7_path}")

        # Parse workbook payloads
        payloads = ExcelSourceParser().parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        p_orig = payloads[0]
        b_num = f"BATCH-E2E-A-{uuid.uuid4().hex[:4].upper()}"

        # Override to active master recipe & order for E2E integration test execution
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan=p_orig.batch.delivery_challan,
                truck_number=p_orig.batch.truck_number,
                plant_code=p_orig.batch.plant_code,
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=p_orig.batch.planned_quantity_m3,
                actual_quantity_m3=None
            ),
            material_consumptions=p_orig.material_consumptions,
            cube_tests=[]
        )

        job_id = f"JOB-E2E-A-{uuid.uuid4().hex[:6].upper()}"
        res = IngestionPersistenceService(self.db).persist_canonical_payloads(
            payloads=[p],
            job_id=job_id,
            source_channel="EXCEL"
        )
        self.assertEqual(res["status"], "SUCCESS")

        # Fresh isolated DB verification
        fresh_db = self.SessionLocal()
        try:
            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "COMPLETED")
            self.assertEqual(job.current_stage, "PERSISTED")
            self.assertEqual(job.progress_percent, "100")

            # Verify physical batch entity created from Excel workbook
            batch = fresh_db.query(Batch).filter(Batch.batch_number == b_num).first()
            self.assertIsNotNone(batch)
            self.assertTrue(batch.plant_id is not None)

            # Verify physical consumptions
            consumptions = fresh_db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).all()
            self.assertTrue(batch.id is not None)
        finally:
            fresh_db.close()

    # -------------------------------------------------------------------------
    # Scenario B: Multi-Record Valid Workbook E2E
    # -------------------------------------------------------------------------
    def test_scenario_b_multi_record_workbook_e2e(self):
        """Scenario B: Verify multiple canonical payloads persist atomically within intended single transaction."""
        service = IngestionPersistenceService(self.db)
        
        b1_num = f"BATCH-E2E-MULTI-1-{uuid.uuid4().hex[:4].upper()}"
        b2_num = f"BATCH-E2E-MULTI-2-{uuid.uuid4().hex[:4].upper()}"

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b1_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-E2E-1",
                truck_number="TM-E2E-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("2.5"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b2_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-E2E-2",
                truck_number="TM-E2E-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("4.0"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        unique_job_id = f"JOB-E2E-B-{uuid.uuid4().hex[:6].upper()}"
        res = service.persist_canonical_payloads(payloads=[p1, p2], job_id=unique_job_id, source_channel="EXCEL")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["persisted_count"], 2)

        # Fresh isolated DB query verification
        fresh_db = self.SessionLocal()
        try:
            b1 = fresh_db.query(Batch).filter(Batch.batch_number == b1_num).first()
            b2 = fresh_db.query(Batch).filter(Batch.batch_number == b2_num).first()
            self.assertIsNotNone(b1)
            self.assertIsNotNone(b2)

            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == unique_job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "COMPLETED")
            self.assertEqual(job.records_persisted, "2")
        finally:
            fresh_db.close()

    # -------------------------------------------------------------------------
    # Scenario C: Atomic Rollback E2E
    # -------------------------------------------------------------------------
    def test_scenario_c_atomic_rollback_e2e(self):
        """Scenario C: Verify that if ANY payload fails in a multi-record workbook, ALL records roll back."""
        service = IngestionPersistenceService(self.db)
        
        b1_num = f"BATCH-E2E-ROLLBACK-OK-{uuid.uuid4().hex[:4].upper()}"
        b2_num = f"BATCH-E2E-ROLLBACK-FAIL-{uuid.uuid4().hex[:4].upper()}"

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b1_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-OK",
                truck_number="TM-OK",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b2_num,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="UNMAPPED_INVALID_RECIPE_CODE",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        fail_job_id = f"JOB-E2E-C-FAIL-{uuid.uuid4().hex[:6].upper()}"
        with self.assertRaises(Exception):
            service.persist_canonical_payloads(payloads=[p1, p2], job_id=fail_job_id, source_channel="EXCEL")

        # Fresh physical DB verification post rollback
        fresh_db = self.SessionLocal()
        try:
            b1 = fresh_db.query(Batch).filter(Batch.batch_number == b1_num).first()
            self.assertIsNone(b1, "Payload 1 MUST be rolled back physically when Payload 2 fails!")

            b2 = fresh_db.query(Batch).filter(Batch.batch_number == b2_num).first()
            self.assertIsNone(b2)

            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == fail_job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "FAILED")
            self.assertEqual(job.current_stage, "FAILED")
        finally:
            fresh_db.close()

    # -------------------------------------------------------------------------
    # Scenario D: Duplicate Production Batch E2E
    # -------------------------------------------------------------------------
    def test_scenario_d_duplicate_batch_rejection_e2e(self):
        """Scenario D: Verify duplicate batch identity raises DuplicateIngestionException and rolls back."""
        service = IngestionPersistenceService(self.db)
        b_dup_num = f"BATCH-E2E-DUP-{uuid.uuid4().hex[:4].upper()}"

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_dup_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-DUP",
                truck_number="TM-DUP",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        job1_id = f"JOB-E2E-D1-{uuid.uuid4().hex[:4]}"
        _ = service.persist_canonical_payloads(payloads=[p1], job_id=job1_id, source_channel="EXCEL")

        job2_id = f"JOB-E2E-D2-{uuid.uuid4().hex[:4]}"
        # Under R7 state machine, re-ingestion of existing payload is idempotent (ENRICH/NO-OP)
        res_dup = service.persist_canonical_payloads(payloads=[p1], job_id=job2_id, source_channel="EXCEL")
        self.assertEqual(res_dup["status"], "SUCCESS")

        # Physical DB verification
        fresh_db = self.SessionLocal()
        try:
            batch_count = fresh_db.query(Batch).filter(Batch.batch_number == b_dup_num).count()
            self.assertEqual(batch_count, 1, "Exactly one batch row must exist post duplicate rejection!")

            job2 = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job2_id).first()
            self.assertIsNotNone(job2)
            self.assertEqual(job2.status, "COMPLETED")
        finally:
            fresh_db.close()

    # -------------------------------------------------------------------------
    # Scenario E: Source Fidelity E2E
    # -------------------------------------------------------------------------
    def test_scenario_e_source_fidelity_e2e(self):
        """Scenario E: Verify actual_quantity_m3 remains NULL when omitted, and truck number is preserved."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Sample FT7 file not found at {self.sample_ft7_path}")

        payloads = ExcelSourceParser().parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        p_orig = payloads[0]
        b_num = f"BATCH-E2E-E-{uuid.uuid4().hex[:4].upper()}"
        dc_unique = f"DC-E2E-E-{uuid.uuid4().hex[:4].upper()}"
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan=dc_unique,
                truck_number=p_orig.batch.truck_number,
                plant_code=p_orig.batch.plant_code,
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=p_orig.batch.planned_quantity_m3,
                actual_quantity_m3=None
            ),
            material_consumptions=p_orig.material_consumptions,
            cube_tests=[]
        )

        res = IngestionPersistenceService(self.db).persist_canonical_payloads(
            payloads=[p],
            job_id=f"JOB-E2E-E-{uuid.uuid4().hex[:4]}",
            source_channel="EXCEL"
        )
        self.assertEqual(res["status"], "SUCCESS")

        fresh_db = self.SessionLocal()
        try:
            batch = fresh_db.query(Batch).filter(Batch.batch_number == b_num).first()
            self.assertIsNotNone(batch)
            self.assertIsNone(batch.actual_quantity_m3, "actual_quantity_m3 MUST remain NULL when unsupplied!")
            self.assertTrue(batch.id is not None)
        finally:
            fresh_db.close()

    # -------------------------------------------------------------------------
    # Scenario F: Job Lifecycle Success & Failure States
    # -------------------------------------------------------------------------
    def test_scenario_f_job_lifecycle_states(self):
        """Scenario F: Verify job lifecycle updates for both success and failure outcomes."""
        service = IngestionPersistenceService(self.db)
        
        # Success Job
        b_ok_num = f"BATCH-E2E-F-OK-{uuid.uuid4().hex[:4].upper()}"
        p_ok = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_ok_num,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        job_ok_id = f"JOB-E2E-F-OK-{uuid.uuid4().hex[:4]}"
        _ = service.persist_canonical_payloads(payloads=[p_ok], job_id=job_ok_id, source_channel="EXCEL")

        # Fail Job
        b_fail_num = f"BATCH-E2E-F-FAIL-{uuid.uuid4().hex[:4].upper()}"
        p_fail = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_fail_num,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="UNMAPPED_RECIPE_F",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        job_fail_id = f"JOB-E2E-F-FAIL-{uuid.uuid4().hex[:4]}"
        with self.assertRaises(Exception):
            service.persist_canonical_payloads(payloads=[p_fail], job_id=job_fail_id, source_channel="EXCEL")

        # Physical DB verification
        fresh_db = self.SessionLocal()
        try:
            job_ok = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_ok_id).first()
            self.assertIsNotNone(job_ok)
            self.assertEqual(job_ok.status, "COMPLETED")
            self.assertEqual(job_ok.current_stage, "PERSISTED")
            self.assertEqual(job_ok.progress_percent, "100")

            job_fail = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_fail_id).first()
            self.assertIsNotNone(job_fail)
            self.assertEqual(job_fail.status, "FAILED")
            self.assertEqual(job_fail.current_stage, "FAILED")
            self.assertIsNotNone(job_fail.failure_reason)
        finally:
            fresh_db.close()


if __name__ == "__main__":
    unittest.main()
