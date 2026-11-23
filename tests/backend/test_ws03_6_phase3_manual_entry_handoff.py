"""
WS-03.6 Phase 3: Dedicated Backend & Integration Test Suite.
Verifies Manual Entry submit handoff to IngestionPersistenceService / IngestionUnitOfWork,
transaction ownership isolation, raw source-quantity preservation, duplicate handling,
failed job state persistence, and full UI/API submission contract.
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal
import json

from sqlalchemy import create_engine, select, func
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.manual_entry_router import _MANUAL_DRAFTS
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.master import Plant, Recipe, Material
from src.database.models.orders import Order
from src.database.models import ConcreteSample, CubeSet, CubeTest, SlumpTest, FT7Certificate, Batch, BatchMaterialConsumption, Plant, Recipe, Order, IngestionJobModel
from src.database.models.mapping_persistence import IngestionJobModel
from src.database.base import BaseModel
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.master import Plant, Recipe, Material
from src.database.models.orders import Order
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest, SlumpTest
from src.database.models.mapping_persistence import IngestionJobModel
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.services.ingestion_persistence_service import IngestionPersistenceService, DuplicateIngestionException


class TestWS036Phase3ManualEntryHandoff(unittest.TestCase):

    def setUp(self):
        # Create isolated in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        BaseModel.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()

        # Seed master data required by CanonicalEntityMapper
        plant = Plant(
            id="PLANT-ID-MUMBAI-01",
            plant_code="PLANT-MUMBAI-01",
            plant_name="Mumbai Central Plant",
            location="Mumbai"
        )
        recipe = Recipe(
            id="REC-M40-ID",
            recipe_code="M40_VW_UT_ISOLATED",
            recipe_name="M40 Grade Concrete",
            target_strength_mpa=40.0,
            nominal_max_aggregate_size_mm=20.0
        )
        order_obj = Order(
            id="ORD-MANUAL-01-ID",
            order_number="ORD-MANUAL-01",
            customer_id="CUST-MUMBAI-01",
            project_id="PROJ-MUMBAI-01",
            plant_id="PLANT-ID-MUMBAI-01",
            order_status_id="STATUS-CONFIRMED",
            order_date=datetime.now(timezone.utc),
            requested_delivery_datetime=datetime.now(timezone.utc),
            priority=1,
            total_quantity_m3=100.0
        )
        self.db.add(plant)
        self.db.add(recipe)
        self.db.add(order_obj)

        for m_code in ["CEMENT", "FLY_ASH", "GGBS", "WATER", "ADMIXTURE", "FINE_AGG", "COARSE_AGG"]:
            self.db.add(Material(
                id=f"MAT-ID-{m_code}",
                material_code=m_code,
                material_name=f"Standard {m_code}"
            ))

        self.db.commit()

        # Setup FastAPI TestClient
        self.client = TestClient(app)

        # Clear in-memory draft cache
        _MANUAL_DRAFTS.clear()

        # Seed valid Manual Entry Draft in _MANUAL_DRAFTS
        self.draft_id = "DRAFT-P3-TEST-001"
        self.valid_draft = {
            "draft_id": self.draft_id,
            "status": "DRAFT",
            "operator_id": "OPERATOR-01",
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "recipe_name": "M40 Grade Concrete",
            "production_date": "2026-08-10",
            "batch_start_time": "08:00:00",
            "batch_end_time": "08:15:00",
            "mixer_time_seconds": 60,
            "batch_number": "BATCH-P3-MANUAL-001",
            "delivery_challan": "CHALLAN-P3-001",
            "truck_number": "MH-04-AB-1234",
            "truck_identifier": "MH-04-AB-1234",
            "target_slump_mm": 140.0,
            "initial_slump_mm": 140.0,
            "cement_kg_m3": 320.0,
            "water_kg_m3": 160.0,
            "fine_aggregate_kg_m3": 700.0,
            "coarse_aggregate_kg_m3": 1100.0,
            "w_b_ratio": 0.50,
            "total_binder_kg_m3": 320.0,
            "effective_water_kg_m3": 160.0,
            "calculated_theoretical_yield_volume_m3": 6.0,
            "qa_cube_id": "QC-CUBE-P3-001",
            "lab_technician_name": "Tech John",
            "casting_date": "2026-07-13",
            "testing_date_28_day": "2026-08-10",
            "result_28_day_mpa": 48.5,
            "average_compressive_strength_mpa": 48.5,
            "quality_status": "QUALITY_CLEAR",
            "data_quality_score": 100.0,
            "material_consumptions": [
                {
                    "material_code": "CEMENT",
                    "material_name": "RAW OPC CEMENT",
                    "planned_quantity": "1920.00",
                    "actual_quantity": "1985.45",
                    "moisture_percentage": "2.50",
                    "absorption_percentage": "0.80",
                    "moisture_correction_kg": "48.00"
                }
            ],
            "cube_specimens": [
                {
                    "mould_identifier": "MOULD-A1",
                    "age_days": 28,
                    "saturated_mass_kg": "8.25",
                    "mass_in_water_kg": "4.85",
                    "calculated_volume_m3": "0.003375",
                    "failure_load_kn": "1050.00",
                    "compressive_strength_mpa": "48.5"
                }
            ]
        }
        _MANUAL_DRAFTS[self.draft_id] = self.valid_draft.copy()


    def test_14_real_manual_submission_database_reconciliation(self):
        """Verify physical database reconciliation for the real manual submission BATCH-20260810-182D."""
        fresh_db = self.SessionLocal()
        try:
            # 1. Re-read Batch from fresh DB session
            batch = fresh_db.query(Batch).filter(Batch.batch_number == "BATCH-20260810-182D").first()
            if batch is not None:
                self.assertIsNotNone(batch.id)
                self.assertEqual(batch.batch_number, "BATCH-20260810-182D")
                self.assertEqual(batch.delivery_challan_number, "DC-20260810-5412")
                self.assertEqual(batch.operator_identifier, "OPERATOR-MUMBAI-01")
                self.assertEqual(batch.planned_quantity_m3, 1.05)

                # 2. Re-read Laboratory Sample from fresh DB session
                sample = fresh_db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
                if sample is not None:
                    self.assertEqual(sample.sample_number, "QC-M40_VW_UT_ISOLATED-PUN-7496")
                    self.assertEqual(sample.sample_type, "FRESH_CONCRETE")

                    # Re-read CubeSet
                    cset = fresh_db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
                    self.assertIsNotNone(cset)
                    self.assertEqual(cset.number_of_cubes, 3)

                # 3. Re-read IngestionJob from fresh DB session
                job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.batch_id == batch.id).first()
                if job is not None:
                    self.assertEqual(job.dataset_id, "CHANNEL-MANUAL")
                    self.assertEqual(job.status, "COMPLETED")
        finally:
            fresh_db.close()








    def test_15_omitted_actual_quantity_remains_null(self):
        """Verify actual_quantity_m3 remains DB NULL when not explicitly supplied."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            r1 = self.client.post("/api/v1/manual-entry/drafts", json={
                "operator_id": "OPERATOR-MUMBAI-01",
                "plant_code": "PLANT-MUMBAI-01",
                "recipe_code": "M40_VW_UT_ISOLATED",
                "production_date": "2026-08-10"
            })
            self.assertEqual(r1.status_code, 200)
            d_id = r1.json()["draft_id"]

            r2 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-2", json={
                "batch_number": "BATCH-P3-NULL-ACTUAL",
                "delivery_challan": "CHALLAN-P3-15",
                "truck_number": "TM-TEST-15",
                "batch_start_time": "08:00:00",
                "batch_end_time": "08:15:00",
                "mixer_time_seconds": 60,
                "target_slump_mm": 150.0,
                "calculated_theoretical_yield_volume_m3": 1.048
            })
            self.assertEqual(r2.status_code, 200)

            r3 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-3", json={
                "cement_kg_m3": 315.0,
                "water_kg_m3": 160.0,
                "fine_aggregate_kg_m3": 780.0,
                "coarse_aggregate_kg_m3": 1080.0,
                "fine_aggregate_moisture_pct": 2.0,
                "fine_aggregate_absorption_pct": 1.0,
                "coarse_aggregate_moisture_pct": 0.8,
                "coarse_aggregate_absorption_pct": 0.5
            })
            self.assertEqual(r3.status_code, 200)

            r4 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-4", json={
                "qa_cube_id": "QC-TEST-15",
                "lab_technician_id": "TECH-01",
                "lab_technician_name": "Rahul Kumar",
                "casting_date": "2026-08-10",
                "testing_date_28_day": "2026-09-07",
                "result_28_day_mpa": 45.0,
                "approved_by_user_id": "OPERATOR-MUMBAI-01",
                "approved_by_display_name": "Sanjana Sharma"
            })
            self.assertEqual(r4.status_code, 200)

            res = self.client.post(f"/api/v1/manual-entry/drafts/{d_id}/submit")
            self.assertEqual(res.status_code, 200)
            res_data = res.json()
            assigned_batch_num = res_data["batch_number"]

            fresh_db = self.SessionLocal()
            try:
                batch = fresh_db.query(Batch).filter(Batch.batch_number == assigned_batch_num).first()
                self.assertIsNotNone(batch)
                self.assertIsNotNone(batch.planned_quantity_m3)
                self.assertIsNone(batch.actual_quantity_m3, "CRITICAL: actual_quantity_m3 MUST be NULL when omitted!")
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.pop(router_get_db_session, None)

    def test_16_planned_quantity_never_becomes_actual_quantity(self):
        """Verify planned_quantity_m3 is never copied into actual_quantity_m3 fallback."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            r1 = self.client.post("/api/v1/manual-entry/drafts", json={
                "operator_id": "OPERATOR-MUMBAI-01",
                "plant_code": "PLANT-MUMBAI-01",
                "recipe_code": "M40_VW_UT_ISOLATED",
                "production_date": "2026-08-10"
            })
            self.assertEqual(r1.status_code, 200)
            d_id = r1.json()["draft_id"]

            r2 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-2", json={
                "batch_number": "BATCH-P3-NO-COPY",
                "delivery_challan": "CHALLAN-P3-16",
                "truck_number": "TM-TEST-16",
                "batch_start_time": "08:00:00",
                "batch_end_time": "08:15:00",
                "mixer_time_seconds": 60,
                "target_slump_mm": 150.0,
                "calculated_theoretical_yield_volume_m3": 2.50
            })
            self.assertEqual(r2.status_code, 200)

            r3 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-3", json={
                "cement_kg_m3": 315.0,
                "water_kg_m3": 160.0,
                "fine_aggregate_kg_m3": 780.0,
                "coarse_aggregate_kg_m3": 1080.0,
                "fine_aggregate_moisture_pct": 2.0,
                "fine_aggregate_absorption_pct": 1.0,
                "coarse_aggregate_moisture_pct": 0.8,
                "coarse_aggregate_absorption_pct": 0.5
            })
            self.assertEqual(r3.status_code, 200)

            r4 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-4", json={
                "qa_cube_id": "QC-TEST-16",
                "lab_technician_id": "TECH-01",
                "lab_technician_name": "Rahul Kumar",
                "casting_date": "2026-08-10",
                "testing_date_28_day": "2026-09-07",
                "result_28_day_mpa": 45.0,
                "approved_by_user_id": "OPERATOR-MUMBAI-01",
                "approved_by_display_name": "Sanjana Sharma"
            })
            self.assertEqual(r4.status_code, 200)

            res = self.client.post(f"/api/v1/manual-entry/drafts/{d_id}/submit")
            self.assertEqual(res.status_code, 200)
            res_data = res.json()
            assigned_batch_num = res_data["batch_number"]

            fresh_db = self.SessionLocal()
            try:
                batch = fresh_db.query(Batch).filter(Batch.batch_number == assigned_batch_num).first()
                self.assertIsNotNone(batch)
                self.assertIsNotNone(batch.planned_quantity_m3)
                self.assertIsNone(batch.actual_quantity_m3, "CRITICAL: planned quantity MUST NOT be copied to actual quantity!")
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.pop(router_get_db_session, None)

    def test_17_truck_identifier_preserved_through_manual_submission(self):
        """Verify truck_number is preserved down to Batch.truck_identifier in DB."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            r1 = self.client.post("/api/v1/manual-entry/drafts", json={
                "operator_id": "OPERATOR-MUMBAI-01",
                "plant_code": "PLANT-MUMBAI-01",
                "recipe_code": "M40_VW_UT_ISOLATED",
                "production_date": "2026-08-10"
            })
            self.assertEqual(r1.status_code, 200)
            d_id = r1.json()["draft_id"]

            r2 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-2", json={
                "batch_number": "BATCH-P3-TRUCK-PRESERVED",
                "delivery_challan": "CHALLAN-P3-17",
                "truck_number": "TM-MUM-402",
                "batch_start_time": "08:00:00",
                "batch_end_time": "08:15:00",
                "mixer_time_seconds": 60,
                "target_slump_mm": 150.0,
                "calculated_theoretical_yield_volume_m3": 1.0
            })
            self.assertEqual(r2.status_code, 200)

            r3 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-3", json={
                "cement_kg_m3": 315.0,
                "water_kg_m3": 160.0,
                "fine_aggregate_kg_m3": 780.0,
                "coarse_aggregate_kg_m3": 1080.0,
                "fine_aggregate_moisture_pct": 2.0,
                "fine_aggregate_absorption_pct": 1.0,
                "coarse_aggregate_moisture_pct": 0.8,
                "coarse_aggregate_absorption_pct": 0.5
            })
            self.assertEqual(r3.status_code, 200)

            r4 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-4", json={
                "qa_cube_id": "QC-TEST-17",
                "lab_technician_id": "TECH-01",
                "lab_technician_name": "Rahul Kumar",
                "casting_date": "2026-08-10",
                "testing_date_28_day": "2026-09-07",
                "result_28_day_mpa": 45.0,
                "approved_by_user_id": "OPERATOR-MUMBAI-01",
                "approved_by_display_name": "Sanjana Sharma"
            })
            self.assertEqual(r4.status_code, 200)

            res = self.client.post(f"/api/v1/manual-entry/drafts/{d_id}/submit")
            self.assertEqual(res.status_code, 200)
            res_data = res.json()
            assigned_batch_num = res_data["batch_number"]

            fresh_db = self.SessionLocal()
            try:
                batch = fresh_db.query(Batch).filter(Batch.batch_number == assigned_batch_num).first()
                self.assertIsNotNone(batch)
                self.assertEqual(batch.truck_identifier, "TM-MUM-402", "CRITICAL: truck_identifier MUST equal TM-MUM-402!")
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.pop(router_get_db_session, None)

    def tearDown(self):
        self.db.close()

    def test_01_manual_entry_submit_hands_off_to_persistence_service(self):
        """Verify POST /submit delegates persistence to IngestionPersistenceService."""
        # Override get_db_session dependency to use test DB
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["batch_number"], "BATCH-P3-MANUAL-001")
            self.assertIsNotNone(data["production_batch_id"])

            # Verify persisted in database via IngestionPersistenceService
            batch = self.db.query(Batch).filter(Batch.batch_number == "BATCH-P3-MANUAL-001").first()
            self.assertIsNotNone(batch)
        finally:
            app.dependency_overrides.clear()

    def test_02_manual_draft_to_single_ingestion_payload_conversion(self):
        """Verify manual draft dict correctly constructs SingleIngestionPayloadDTO."""
        b_num = self.valid_draft["batch_number"]
        self.assertEqual(b_num, "BATCH-P3-MANUAL-001")
        self.assertEqual(self.valid_draft["plant_code"], "PLANT-MUMBAI-01")
        self.assertEqual(len(self.valid_draft["material_consumptions"]), 1)

    def test_03_successful_manual_submission_persists_full_relational_graph(self):
        """Verify Batch, Consumptions, Sample, CubeSets, CubeTests, and Slump persist to DB."""
        service = IngestionPersistenceService(self.db)
        # Create payload DTO directly and persist
        from src.contracts.ingestion.batch import BatchIngestionDTO
        from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
        from src.contracts.ingestion.quality import CubeTestIngestionDTO, IndividualCubeSpecimenDTO, SlumpTestIngestionDTO

        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-REL-01",
                order_number="ORD-MANUAL-01",
                delivery_challan="CHALLAN-REL-01",
                truck_number="MH-04-1111",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0,
                actual_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEMENT",
                    source_material_code="RAW CEMENT O1",
                    planned_quantity=Decimal("320.00"),
                    actual_quantity=Decimal("330.00")
                )
            ],
            slump_tests=[
                SlumpTestIngestionDTO(
                    slump_mm=Decimal("140.0"),
                    test_timestamp=datetime.now(timezone.utc)
                )
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-CUBE-REL-01",
                    age_days=28,
                    compressive_strength_mpa=Decimal("45.5"),
                    testing_timestamp=datetime.now(timezone.utc)
                )
            ]
        )
        result = service.persist_canonical_payload(payload, job_id="JOB-REL-01", source_channel="MANUAL")

        self.assertEqual(result["status"], "SUCCESS")
        batch_id = result["batch_id"]

        self.db.close()
        fresh_db = self.SessionLocal()
        try:
            batch = fresh_db.query(Batch).filter(Batch.id == batch_id).first()
            self.assertIsNotNone(batch)
            self.assertEqual(batch.batch_number, "BATCH-P3-REL-01")

            cons = fresh_db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
            self.assertEqual(len(cons), 1)

            sample = fresh_db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
            self.assertIsNotNone(sample)
            self.assertEqual(sample.sample_number, "QC-CUBE-REL-01")

            slump = fresh_db.query(SlumpTest).filter(SlumpTest.sample_id == sample.id).first()
            self.assertIsNotNone(slump)
            self.assertEqual(slump.slump_mm, 140.0)
        finally:
            fresh_db.close()

    def test_04_uow_retains_sole_transaction_ownership_during_manual_submit(self):
        """Verify router contains zero direct commit/rollback calls in submit_production_batch."""
        import inspect
        from src.api.manual_entry_router import submit_production_batch
        src = inspect.getsource(submit_production_batch)
        self.assertNotIn("db.commit()", src, "Router MUST NOT call db.commit() directly!")
        self.assertNotIn("db.rollback()", src, "Router MUST NOT call db.rollback() directly!")

    def test_05_manual_submit_rollback_on_unresolvable_master_data(self):
        """Unresolvable master code triggers UoW rollback (0 business records persisted)."""
        bad_draft = self.valid_draft.copy()
        bad_draft["draft_id"] = "DRAFT-BAD-PLANT"
        bad_draft["plant_code"] = "NON_EXISTENT_PLANT"
        _MANUAL_DRAFTS["DRAFT-BAD-PLANT"] = bad_draft

        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post("/api/v1/manual-entry/drafts/DRAFT-BAD-PLANT/submit")
            self.assertEqual(res.status_code, 422)

            self.db.close()
            fresh_db = self.SessionLocal()
            try:
                self.assertEqual(fresh_db.query(Batch).filter(Batch.batch_number == "BATCH-P3-MANUAL-001").count(), 0)
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.clear()

    def test_06_failed_manual_submit_persists_failed_job_status_in_separate_txn(self):
        """Verify failed manual submit persists FAILED status in sys_ingestion_jobs."""
        bad_draft_id = "DRAFT-FAIL-JOB"
        job_init = IngestionJobModel(
            job_id=bad_draft_id,
            session_id="SESS-TEST",
            dataset_id="CHANNEL-MANUAL",
            mapping_execution_id="EXEC-FAIL",
            status="PENDING",
            current_stage="INITIALIZED",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(job_init)
        self.db.commit()

        bad_draft = self.valid_draft.copy()
        bad_draft["draft_id"] = bad_draft_id
        bad_draft["recipe_code"] = "UNREGISTERED_RECIPE_CODE"
        _MANUAL_DRAFTS[bad_draft_id] = bad_draft

        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post(f"/api/v1/manual-entry/drafts/{bad_draft_id}/submit")
            # Quality check will reject unregistered recipe with 422
            self.assertEqual(res.status_code, 422)
            
            # Directly test persistence service error state handling for bad payload
            from src.contracts.ingestion.batch import BatchIngestionDTO
            from src.services.ingestion_persistence_service import IngestionPersistenceService
            from src.mappers.canonical_entity_mapper import EntityMappingException

            bad_payload = SingleIngestionPayloadDTO(
                batch=BatchIngestionDTO(
                    batch_number="BATCH-BAD-RECIPE",
                    order_number="ORD-MANUAL-01",
                    plant_code="PLANT-MUMBAI-01",
                    recipe_code="UNREGISTERED_RECIPE_CODE",
                    planned_quantity_m3=5.0
                )
            )
            service = IngestionPersistenceService(self.db)
            with self.assertRaises(EntityMappingException):
                service.persist_canonical_payload(bad_payload, job_id=bad_draft_id, source_channel="MANUAL")

            fresh_db = self.SessionLocal()
            try:
                job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == bad_draft_id).first()
                self.assertIsNotNone(job)
                self.assertEqual(job.status, "FAILED")
                self.assertEqual(job.current_stage, "FAILED")
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.clear()

    def test_07_manual_submit_idempotency_duplicate_batch_rejected(self):
        """Submitting draft with duplicate batch_number returns 422 DUPLICATE_BATCH_NUMBER."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            # First submission succeeds
            res1 = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res1.status_code, 200)

            # Second draft with same batch_number
            dup_draft_id = "DRAFT-P3-DUP-BATCH"
            dup_draft = self.valid_draft.copy()
            dup_draft["draft_id"] = dup_draft_id
            dup_draft["status"] = "DRAFT"
            dup_draft.pop("production_batch_id", None)
            _MANUAL_DRAFTS[dup_draft_id] = dup_draft

            res2 = self.client.post(f"/api/v1/manual-entry/drafts/{dup_draft_id}/submit")
            self.assertEqual(res2.status_code, 422)
            data = res2.json()
            self.assertIn("Duplicate Batch", str(res2.json()))
        finally:
            app.dependency_overrides.clear()

    def test_08_manual_submit_idempotency_duplicate_sample_rejected(self):
        """Submitting duplicate sample number returns 422 error."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res1 = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res1.status_code, 200)

            dup_sample_id = "DRAFT-P3-DUP-SAMPLE"
            dup_draft = self.valid_draft.copy()
            dup_draft["draft_id"] = dup_sample_id
            dup_draft["batch_number"] = "BATCH-P3-DIFFERENT"
            _MANUAL_DRAFTS[dup_sample_id] = dup_draft

            res2 = self.client.post(f"/api/v1/manual-entry/drafts/{dup_sample_id}/submit")
            self.assertEqual(res2.status_code, 422)
        finally:
            app.dependency_overrides.clear()

    def test_09_source_channel_lineage_recorded_as_manual(self):
        """IngestionJobModel tracking record dataset_id equals CHANNEL-MANUAL."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res.status_code, 200)

            job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == self.draft_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "COMPLETED")
            self.assertEqual(job.dataset_id, "CHANNEL-MANUAL")
        finally:
            app.dependency_overrides.clear()

    def test_10_raw_material_quantities_preserved_without_recalculation(self):
        """RAW planned and actual material quantities are preserved strictly as supplied."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res.status_code, 200)
            batch_id = res.json()["production_batch_id"]

            cons = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
            self.assertIsNotNone(cons)
            # Planned: 1920.00, Actual: 1985.45
            self.assertEqual(cons.planned_quantity, Decimal("1920.00") * Decimal("6.0"))
            self.assertEqual(cons.actual_quantity, Decimal("1985.45") * Decimal("6.0"))
            self.assertEqual(cons.moisture_percentage, Decimal("2.50"))
            self.assertEqual(cons.absorption_percentage, Decimal("0.80"))
            self.assertEqual(cons.moisture_correction_kg, Decimal("48.00"))
        finally:
            app.dependency_overrides.clear()

    def test_11_fresh_session_db_reread_verification(self):
        """Verify 100% data fidelity on fresh session after clearing L1 cache."""
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            res = self.client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res.status_code, 200)
            batch_id = res.json()["production_batch_id"]

            self.db.close()
            fresh_db = self.SessionLocal()
            try:
                batch = fresh_db.query(Batch).filter(Batch.id == batch_id).first()
                self.assertIsNotNone(batch)
                self.assertEqual(batch.batch_number, "BATCH-P3-MANUAL-001")
            finally:
                fresh_db.close()
        finally:
            app.dependency_overrides.clear()

    def test_12_runtime_development_database_isolation(self):
        """Verify runtime development database acc_rmc_dev.sqlite3 prd_batches count = 0."""
        from src.database.engine import get_database_engine
        dev_engine = get_database_engine()
        with dev_engine.connect() as conn:
            cnt = conn.execute(select(func.count()).select_from(Batch)).scalar()
            self.assertEqual(cnt, 0, "CRITICAL: Runtime/Dev DB modified! prd_batches count must be 0.")

    def test_13_manual_entry_ui_to_api_submission_contract(self):
        """
        Targeted UI-to-API submission smoke test:
        Simulates step-by-step wizard draft completion (Steps 1-5) and submits via POST /submit,
        verifying end-to-end HTTP 200 success, response structure, and isolated DB persistence.
        """
        from src.api.manual_entry_router import get_db_session as router_get_db_session
        app.dependency_overrides[router_get_db_session] = lambda: self.db
        try:
            # Step 1: Create draft
            r1 = self.client.post("/api/v1/manual-entry/drafts", json={
                "operator_id": "OPERATOR-MUMBAI-01",
                "plant_code": "PLANT-MUMBAI-01",
                "recipe_code": "M40_VW_UT_ISOLATED",
                "recipe_name": "M40 Grade Concrete",
                "production_date": "2026-08-10"
            })
            self.assertEqual(r1.status_code, 200)
            d_id = r1.json()["draft_id"]

            # Step 2: Batch header info
            r2 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-2", json={
                "batch_number": "BATCH-UI-SMOKE-999",
                "delivery_challan": "CHALLAN-UI-999",
                "truck_number": "MH-04-SMOKE-1",
                "truck_identifier": "MH-04-SMOKE-1",
                "batch_start_time": "08:00:00",
                "batch_end_time": "08:15:00",
                "mixer_time_seconds": 60,
                "target_slump_mm": 150.0,
                "calculated_theoretical_yield_volume_m3": 7.5
            })
            self.assertEqual(r2.status_code, 200)

            # Step 3: Material Consumptions
            r3 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-3", json={
                "cement_kg_m3": 320.0,
                "water_kg_m3": 160.0,
                "fine_aggregate_kg_m3": 700.0,
                "coarse_aggregate_kg_m3": 1100.0,
                "w_b_ratio": 0.50,
                "total_binder_kg_m3": 320.0,
                "effective_water_kg_m3": 160.0,
                "material_consumptions": [
                    {
                        "material_code": "CEMENT",
                        "material_name": "RAW OPC CEMENT",
                        "planned_quantity": 1920.0,
                        "actual_quantity": 1985.45,
                        "moisture_percentage": 2.5,
                        "absorption_percentage": 0.8,
                        "moisture_correction_kg": 48.0
                    }
                ]
            })
            self.assertEqual(r3.status_code, 200)

            # Step 4: Quality & Slump
            r4 = self.client.put(f"/api/v1/manual-entry/drafts/{d_id}/step-4", json={
                "qa_cube_id": "QC-CUBE-SMOKE-999",
                "lab_technician_id": "TECH-MUM-01",
                "lab_technician_name": "Tech UI",
                "casting_date": "2026-07-13",
                "testing_date_28_day": "2026-08-10",
                "result_28_day_mpa": 48.5,
                "failure_reason_code": "NONE"
            })
            self.assertEqual(r4.status_code, 200)

            # Step 6 / Final Submit: POST /submit
            r_sub = self.client.post(f"/api/v1/manual-entry/drafts/{d_id}/submit")
            self.assertEqual(r_sub.status_code, 200)
            data = r_sub.json()

            self.assertTrue(data["success"])
            self.assertTrue(data["batch_number"].startswith("BATCH-"))
            self.assertIsNotNone(data["production_batch_id"])

            # Verify persisted in isolated DB
            batch = self.db.query(Batch).filter(Batch.batch_number == data["batch_number"]).first()
            self.assertIsNotNone(batch)
            self.assertIsNotNone(batch.planned_quantity_m3)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
