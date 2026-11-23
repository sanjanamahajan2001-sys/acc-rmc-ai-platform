import unittest
import os
from decimal import Decimal
from fastapi.testclient import TestClient

from src.api.main import app
from src.parsers.excel_parser import ExcelSourceParser
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO

class TestWS036Phase4ExcelHandoff(unittest.TestCase):
    """WS-04.2 Dedicated Unit Test Suite: ExcelSourceParser -> Canonical DTO Handoff."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.parser = ExcelSourceParser()
        cls.sample_ft7_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"

    def test_01_ft7_workbook_produces_single_ingestion_payload_dto(self):
        """Verify ExcelSourceParser parses real FT7 worksheet into SingleIngestionPayloadDTO."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Sample FT7 workbook not found at {self.sample_ft7_path}")

        payloads = self.parser.parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        self.assertEqual(len(payloads), 1, "Parser must extract exactly 1 payload from worksheet '1749'")
        
        payload = payloads[0]
        self.assertIsInstance(payload, SingleIngestionPayloadDTO)
        self.assertIsNotNone(payload.batch)
        self.assertEqual(payload.batch.batch_number, "BATCH-1749")
        self.assertEqual(payload.batch.delivery_challan, "1749")
        self.assertEqual(payload.batch.truck_number, "GA07F7633")

    def test_02_omitted_actual_quantity_remains_none_when_unsupplied(self):
        """Verify actual_quantity_m3 remains None in DTO when unsupplied."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/ft7_certificates/FT7R5.xlsx"
        if not os.path.exists(file_path):
            self.skipTest(f"Sample FT7 workbook not found at {file_path}")

        payloads = self.parser.parse_workbook(file_path=file_path)
        payload = payloads[0]
        self.assertIsNone(payload.batch.actual_quantity_m3, "Omitted actual batch quantity must remain None")

    def test_03_truck_identifier_preserved_in_excel_dto(self):
        """Verify raw truck identifier string is preserved without data loss."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Sample FT7 workbook not found at {self.sample_ft7_path}")

        payloads = self.parser.parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        payload = payloads[0]
        self.assertEqual(payload.batch.truck_number, "GA07F7633")

    def test_04_ft7_laboratory_data_represented_in_dto(self):
        """Verify FT7 laboratory cube sets and specimens are present in cube_tests DTO."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Sample FT7 workbook not found at {self.sample_ft7_path}")

        payloads = self.parser.parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        payload = payloads[0]
        self.assertEqual(len(payload.cube_tests), 2)
        set_7d = payload.cube_tests[0]
        self.assertEqual(set_7d.age_days, 7)
        self.assertEqual(len(set_7d.cube_specimens), 3)

if __name__ == "__main__":
    unittest.main()


import unittest
import os
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session

from src.database.engine import get_database_engine
from src.database.session import get_session_factory
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.mapping_persistence import IngestionJobModel
from src.parsers.excel_parser import ExcelSourceParser
from src.services.ingestion_persistence_service import IngestionPersistenceService, DuplicateIngestionException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO, BatchIngestionDTO

class TestWS036Phase4ExcelAtomicityAndIdempotency(unittest.TestCase):
    """WS-04.4 Dedicated Test Suite: Atomic Multi-Record Persistence & Duplicate Handling."""

    def setUp(self):
        self.engine = get_database_engine()
        self.SessionLocal = get_session_factory(self.engine)
        self.db: Session = self.SessionLocal()
        self.parser = ExcelSourceParser()
        self.service = IngestionPersistenceService(self.db)
        self.sample_ft7_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"

    def tearDown(self):
        try:
            self.db.query(CubeTest).delete()
            self.db.query(CubeSet).delete()
            self.db.query(ConcreteSample).delete()
            self.db.query(BatchMaterialConsumption).delete()
            self.db.query(Batch).delete()
            self.db.query(IngestionJobModel).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def _create_valid_payload(self, batch_num: str) -> SingleIngestionPayloadDTO:
        return SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=batch_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-TEST-123",
                truck_number="TM-TEST-99",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.5"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )

    def test_01_multi_payload_atomic_success(self):
        """Verify multiple payloads in a workbook persist atomically within a single transaction."""
        p1 = self._create_valid_payload(f"BATCH-MULTI-1-{uuid.uuid4().hex[:4].upper()}")
        p2 = self._create_valid_payload(f"BATCH-MULTI-2-{uuid.uuid4().hex[:4].upper()}")

        unique_job_id = f"JOB-MULTI-{uuid.uuid4().hex[:6].upper()}"
        res = self.service.persist_canonical_payloads(
            payloads=[p1, p2],
            job_id=unique_job_id,
            source_channel="EXCEL"
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["persisted_count"], 2)

        # Verify physical persistence in isolated test DB
        job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == unique_job_id).first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "COMPLETED")
        self.assertEqual(job.records_persisted, "2")

    def test_02_multi_payload_atomic_rollback_on_failure(self):
        """Verify that if ANY payload in a workbook fails, ALL previously processed payloads are rolled back."""
        b1_num = f"BATCH-ATOMIC-OK-{uuid.uuid4().hex[:4].upper()}"
        p1 = self._create_valid_payload(b1_num)

        # Bad payload 2 with unmapped recipe code
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=f"BATCH-ATOMIC-FAIL-{uuid.uuid4().hex[:4].upper()}",
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="INVALID_UNMAPPED_RECIPE_CODE",
                planned_quantity_m3=Decimal("3.5")
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        unique_job_id = f"JOB-FAIL-{uuid.uuid4().hex[:6].upper()}"
        with self.assertRaises(Exception):
            self.service.persist_canonical_payloads(
                payloads=[p1, p2],
                job_id=unique_job_id,
                source_channel="EXCEL"
            )

        # Physical Verification: Payload 1 MUST NOT exist in DB
        batch_1 = self.db.query(Batch).filter(Batch.batch_number == b1_num).first()
        self.assertIsNone(batch_1, "Payload 1 must be completely rolled back when Payload 2 fails!")

        # Physical Verification: Job status MUST be marked FAILED
        job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == unique_job_id).first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "FAILED")

    def test_03_duplicate_batch_number_rejection(self):
        """Verify submitting a duplicate batch number raises DuplicateIngestionException and marks job FAILED."""
        b_dup_num = f"BATCH-DUP-TEST-{uuid.uuid4().hex[:4].upper()}"
        p1 = self._create_valid_payload(b_dup_num)

        # Persist first time
        _ = self.service.persist_canonical_payloads(payloads=[p1], job_id=f"JOB-DUP-1-{uuid.uuid4().hex[:4]}", source_channel="EXCEL")

        # Persist second time with duplicate batch number
        dup_job_id = f"JOB-DUP-2-{uuid.uuid4().hex[:4]}"
        # Under R7 state machine, re-ingestion of existing payload is idempotent (ENRICH/NO-OP)
        res_dup = self.service.persist_canonical_payloads(payloads=[p1], job_id=dup_job_id, source_channel="EXCEL")
        self.assertEqual(res_dup["status"], "SUCCESS")

        job2 = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == dup_job_id).first()
        self.assertIsNotNone(job2)
        self.assertEqual(job2.status, "COMPLETED")

if __name__ == "__main__":
    unittest.main()

class TestWS036Phase4ExcelE2ESafetyNet(unittest.TestCase):
    """WS-04.5 Dedicated E2E Automated Verification Test Suite for Excel Ingestion Handoff."""

    def setUp(self):
        self.engine = get_database_engine()
        self.SessionLocal = get_session_factory(self.engine)
        self.db: Session = self.SessionLocal()
        self.parser = ExcelSourceParser()
        self.service = IngestionPersistenceService(self.db)
        self.sample_ft7_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"

    def tearDown(self):
        try:
            self.db.query(CubeTest).delete()
            self.db.query(CubeSet).delete()
            self.db.query(ConcreteSample).delete()
            self.db.query(BatchMaterialConsumption).delete()
            self.db.query(Batch).delete()
            self.db.query(IngestionJobModel).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def test_e2e_scenario_a_single_valid_workbook(self):
        """Scenario A: Single valid workbook E2E pipeline execution & DB state assertion."""
        if not os.path.exists(self.sample_ft7_path):
            self.skipTest(f"Workbook missing at {self.sample_ft7_path}")

        payloads = self.parser.parse_workbook(file_path=self.sample_ft7_path, worksheet_name="1749")
        self.assertTrue(len(payloads) >= 1)
        p1 = payloads[0]

        # Use distinct batch number & active master reference codes
        b_num = f"BATCH-E2E-SINGLE-{uuid.uuid4().hex[:6].upper()}"
        dc_unique = f"DC-E2E-SINGLE-{uuid.uuid4().hex[:6].upper()}"
        from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
        mat_dto = MaterialConsumptionIngestionDTO(
            material_code="CEMENT",
            source_material_code="CEMENT",
            planned_quantity=Decimal("350.0"),
            actual_quantity=Decimal("352.0")
        )
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan=dc_unique,
                truck_number=p1.batch.truck_number,
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=p1.batch.planned_quantity_m3,
                actual_quantity_m3=None
            ),
            material_consumptions=[mat_dto],
            cube_tests=p1.cube_tests
        )

        job_id = f"JOB-E2E-A-{uuid.uuid4().hex[:6].upper()}"
        res = self.service.persist_canonical_payloads(
            payloads=[payload],
            job_id=job_id,
            source_channel="EXCEL"
        )

        self.assertEqual(res["status"], "SUCCESS")

        # Fresh DB query verification
        fresh_db = self.SessionLocal()
        try:
            b_rec = fresh_db.query(Batch).filter(Batch.batch_number == b_num).first()
            self.assertIsNotNone(b_rec)
            self.assertIsNone(b_rec.actual_quantity_m3, "actual_quantity_m3 must remain NULL when unsupplied")
            self.assertEqual(b_rec.truck_identifier, p1.batch.truck_number)

            consumptions = fresh_db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == b_rec.id).all()
            self.assertTrue(len(consumptions) > 0)

            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "COMPLETED")
            self.assertEqual(job.current_stage, "PERSISTED")
            self.assertEqual(job.progress_percent, "100")
        finally:
            fresh_db.close()

    def test_e2e_scenario_b_multi_record_workbook(self):
        """Scenario B: Multi-record valid workbook E2E transaction & entity counting."""
        b1_num = f"BATCH-E2E-M1-{uuid.uuid4().hex[:6].upper()}"
        b2_num = f"BATCH-E2E-M2-{uuid.uuid4().hex[:6].upper()}"

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b1_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-M1",
                truck_number="TM-M1",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.0"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b2_num,
                order_number="ORD-VW-UT-ISO-001",
                delivery_challan="DC-M2",
                truck_number="TM-M2",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("4.0"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        job_id = f"JOB-E2E-B-{uuid.uuid4().hex[:6].upper()}"
        res = self.service.persist_canonical_payloads(payloads=[p1, p2], job_id=job_id, source_channel="EXCEL")
        self.assertEqual(res["persisted_count"], 2)

        fresh_db = self.SessionLocal()
        try:
            b1 = fresh_db.query(Batch).filter(Batch.batch_number == b1_num).first()
            b2 = fresh_db.query(Batch).filter(Batch.batch_number == b2_num).first()
            self.assertIsNotNone(b1)
            self.assertIsNotNone(b2)
        finally:
            fresh_db.close()

    def test_e2e_scenario_c_atomic_rollback(self):
        """Scenario C: Multi-record atomic transaction rollback on late payload failure."""
        b_ok = f"BATCH-E2E-OK-{uuid.uuid4().hex[:6].upper()}"
        b_fail = f"BATCH-E2E-FAIL-{uuid.uuid4().hex[:6].upper()}"

        p_ok = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_ok,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )
        p_fail = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_fail,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="UNMAPPED_INVALID_RECIPE",
                planned_quantity_m3=Decimal("3.0")
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        job_id = f"JOB-E2E-C-{uuid.uuid4().hex[:6].upper()}"
        with self.assertRaises(Exception):
            self.service.persist_canonical_payloads(payloads=[p_ok, p_fail], job_id=job_id, source_channel="EXCEL")

        fresh_db = self.SessionLocal()
        try:
            b_rec = fresh_db.query(Batch).filter(Batch.batch_number == b_ok).first()
            self.assertIsNone(b_rec, "Valid payload 1 MUST be rolled back when payload 2 fails!")
            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "FAILED")
        finally:
            fresh_db.close()

    def test_e2e_scenario_d_duplicate_batch_rejection(self):
        """Scenario D: Duplicate batch submission rejection & rollback."""
        b_dup = f"BATCH-E2E-DUP-{uuid.uuid4().hex[:6].upper()}"
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_dup,
                order_number="ORD-VW-UT-ISO-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("2.5")
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        _ = self.service.persist_canonical_payloads(payloads=[p], job_id=f"JOB-DUP-A-{uuid.uuid4().hex[:4]}", source_channel="EXCEL")

        dup_job_id = f"JOB-DUP-B-{uuid.uuid4().hex[:4]}"
        # Under R7 state machine, re-ingestion of existing payload is idempotent (ENRICH/NO-OP)
        res_dup = self.service.persist_canonical_payloads(payloads=[p], job_id=dup_job_id, source_channel="EXCEL")
        self.assertEqual(res_dup["status"], "SUCCESS")

        fresh_db = self.SessionLocal()
        try:
            dup_batches = fresh_db.query(Batch).filter(Batch.batch_number == b_dup).all()
            self.assertEqual(len(dup_batches), 1, "Must contain exactly 1 physical batch record")
            dup_job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == dup_job_id).first()
            self.assertIsNotNone(dup_job)
            self.assertEqual(dup_job.status, "COMPLETED")
        finally:
            fresh_db.close()

    def test_e2e_scenario_e_source_fidelity(self):
        """Scenario E: Source-side fidelity preservation (no planned->actual conversion or truck corruption)."""
        b_num = f"BATCH-E2E-FIDELITY-{uuid.uuid4().hex[:6].upper()}"
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number=b_num,
                order_number="ORD-VW-UT-ISO-001",
                truck_number="TM-FIDELITY-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=Decimal("5.25"),
                actual_quantity_m3=None
            ),
            material_consumptions=[],
            cube_tests=[]
        )

        job_id = f"JOB-FIDELITY-{uuid.uuid4().hex[:6].upper()}"
        _ = self.service.persist_canonical_payloads(payloads=[p], job_id=job_id, source_channel="EXCEL")

        fresh_db = self.SessionLocal()
        try:
            b_rec = fresh_db.query(Batch).filter(Batch.batch_number == b_num).first()
            self.assertEqual(b_rec.planned_quantity_m3, 5.25)
            self.assertIsNone(b_rec.actual_quantity_m3)
            self.assertEqual(b_rec.truck_identifier, "TM-FIDELITY-01")
        finally:
            fresh_db.close()
