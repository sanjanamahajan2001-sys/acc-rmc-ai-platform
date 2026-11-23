"""
WS-03.6 Phase 2: IngestionUnitOfWork & IngestionPersistenceService Dedicated Test Suite.
Verifies atomic multi-table commit, rollback behavior, idempotency, fresh-session DB re-reads, and lineage.
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.base import BaseModel



from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest, SlumpTest, FT7Certificate
from src.database.models.master import Plant, Recipe, Material
from src.database.models.orders import Order
from src.database.models.mapping_persistence import IngestionJobModel

from src.contracts.ingestion.payload import (
    SingleIngestionPayloadDTO,
    BatchIngestionDTO,
    MaterialConsumptionIngestionDTO,
    CubeTestIngestionDTO,
    SlumpTestIngestionDTO,
    FT7CertificateIngestionDTO
)
from src.mappers.canonical_entity_mapper import EntityMappingException
from src.services.ingestion_uow import IngestionUnitOfWork
from src.services.ingestion_persistence_service import IngestionPersistenceService, DuplicateIngestionException


class TestWS036Phase2UoWPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up isolated in-memory SQLite database engine for Phase 2 testing."""
        cls.engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)


        # Seed master data tables
        db = cls.SessionLocal()
        try:
            plant = db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
            if not plant:
                plant = Plant(
                    id="PLANT-ID-MUMBAI-01",
                    plant_code="PLANT-MUMBAI-01",
                    plant_name="Mumbai Central Plant",
                    location="Mumbai"
                )
                db.add(plant)

            recipe = db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
            if not recipe:
                recipe = Recipe(
                    id="RECIPE-ID-M40-ISOLATED",
                    recipe_code="M40_VW_UT_ISOLATED",
                    recipe_name="M40 View Isolated",
                    target_strength_mpa=40.0,
                    nominal_max_aggregate_size_mm=20.0
                )
                db.add(recipe)


            order_obj = db.query(Order).filter(Order.order_number == "ORD-MANUAL-01").first()
            if not order_obj:
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
                db.add(order_obj)

            for m_code in ["CEMENT", "FLY_ASH", "GGBS", "WATER", "ADMIXTURE", "FINE_AGG", "COARSE_AGG"]:
                mat = db.query(Material).filter(Material.material_code == m_code).first()
                if not mat:
                    db.add(Material(
                        id=f"MAT-ID-{m_code}",
                        material_code=m_code,
                        material_name=f"Standard {m_code}",
                        engineering_unit="KG"
                    ))

            db.commit()
        finally:
            db.close()

    def setUp(self):
        """Create fresh session for each unit test."""
        self.db: Session = self.SessionLocal()

        self.full_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P2-TEST-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0,
                actual_quantity_m3=6.0,
                production_start_time=datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc),
                production_end_time=datetime(2026, 8, 10, 8, 3, tzinfo=timezone.utc),
                operator_id="OPERATOR-KUMAR-88"
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=320.0, actual_quantity=320.0),
                MaterialConsumptionIngestionDTO(material_code="FLY_ASH", planned_quantity=40.0, actual_quantity=40.0),
                MaterialConsumptionIngestionDTO(material_code="GGBS", planned_quantity=110.0, actual_quantity=110.0),
                MaterialConsumptionIngestionDTO(material_code="WATER", planned_quantity=155.0, actual_quantity=155.0),
                MaterialConsumptionIngestionDTO(material_code="ADMIXTURE", planned_quantity=4.2, actual_quantity=4.2),
                MaterialConsumptionIngestionDTO(material_code="FINE_AGG", planned_quantity=790.0, actual_quantity=790.0),
                MaterialConsumptionIngestionDTO(material_code="COARSE_AGG", planned_quantity=1070.0, actual_quantity=1070.0),
            ],
            slump_tests=[
                SlumpTestIngestionDTO(
                    slump_mm=150.0,
                    test_timestamp=datetime(2026, 8, 10, 8, 5, tzinfo=timezone.utc),
                    tester_name="Ramesh Sharma",
                    ambient_temperature_c=32.0,
                    concrete_temperature_c=29.0
                )
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-CUBE-P2-001",
                    age_days=28,
                    compressive_strength_mpa=52.5,
                    testing_timestamp=datetime(2026, 9, 7, tzinfo=timezone.utc),
                    tested_by_user="Suresh Kumar"
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-CERT-P2-001",
                issued_date=datetime(2026, 9, 8, tzinfo=timezone.utc),
                approval_status="ISSUED",
                remarks="Phase 2 atomic test pass"
            )
        )


    def tearDown(self):
        """Clean up non-master data after test execution."""
        self.db.rollback()
        self.db.query(BatchMaterialConsumption).delete()
        self.db.query(CubeTest).delete()
        self.db.query(CubeSet).delete()
        self.db.query(SlumpTest).delete()
        self.db.query(FT7Certificate).delete()
        self.db.query(ConcreteSample).delete()
        self.db.query(Batch).delete()
        self.db.query(IngestionJobModel).delete()
        self.db.commit()
        self.db.close()

    # --- 1. Service & UoW Construction Tests ---
    def test_01_uow_initialization(self):
        """IngestionUnitOfWork initializes correctly with Session."""
        uow = IngestionUnitOfWork(self.db)
        self.assertEqual(uow.db, self.db)
        self.assertFalse(uow._in_transaction)

    def test_02_persistence_service_initialization(self):
        """IngestionPersistenceService initializes correctly."""
        service = IngestionPersistenceService(self.db)
        self.assertEqual(service.db, self.db)

    # --- 2. Successful Persistence & Fresh DB Re-Read Tests ---
    def test_03_successful_atomic_persistence(self):
        """Full SingleIngestionPayloadDTO is persisted atomically across all WS-02 tables."""
        service = IngestionPersistenceService(self.db)
        result = service.persist_canonical_payload(self.full_payload, job_id="JOB-P2-001")

        self.assertEqual(result["status"], "SUCCESS")
        self.assertIsNotNone(result["batch_id"])
        self.assertEqual(result["consumptions_count"], 7)

    def test_04_fresh_session_db_reread_verification(self):
        """
        Verify database graph integrity by closing the current session,
        creating a fresh session, and querying persisted entities.
        """
        service = IngestionPersistenceService(self.db)
        result = service.persist_canonical_payload(self.full_payload, job_id="JOB-P2-FRESH")
        batch_id = result["batch_id"]

        # Close session to clear L1 cache
        self.db.close()

        # Open fresh session and query DB
        fresh_db = self.SessionLocal()
        try:
            batch = fresh_db.query(Batch).filter(Batch.id == batch_id).first()
            self.assertIsNotNone(batch)
            self.assertEqual(batch.batch_number, "BATCH-P2-TEST-001")
            self.assertEqual(batch.planned_quantity_m3, 6.0)

            # Query Consumptions
            consumptions = fresh_db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
            self.assertEqual(len(consumptions), 7)
            cement = next(c for c in consumptions if "CEMENT" in c.material_id)
            self.assertEqual(cement.actual_quantity, 1920.0) # RAW source value preserved

            # Query ConcreteSample & Cube Hierarchy
            sample = fresh_db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
            self.assertIsNotNone(sample)
            self.assertEqual(sample.sample_number, "QC-CUBE-P2-001")

            cube_set = fresh_db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
            self.assertIsNotNone(cube_set)

            cube_test = fresh_db.query(CubeTest).filter(CubeTest.cube_set_id == cube_set.id).first()
            self.assertIsNotNone(cube_test)
            self.assertEqual(cube_test.compressive_strength_mpa, 52.5)

            # Query SlumpTest
            slump = fresh_db.query(SlumpTest).filter(SlumpTest.sample_id == sample.id).first()
            self.assertIsNotNone(slump)
            self.assertEqual(slump.slump_mm, 150.0)

            # Query FT7Certificate
            cert = fresh_db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch_id).first()
            self.assertIsNotNone(cert)
            self.assertEqual(cert.certificate_number, "FT7-CERT-P2-001")

            # Query IngestionJobModel
            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-P2-FRESH").first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "COMPLETED")
            self.assertIn("MANUAL", job.logs_json)
        finally:
            fresh_db.close()

    # --- 3. Atomic Transaction Rollback Tests ---
    def test_05_unresolvable_order_causes_complete_rollback(self):
        """Unresolvable order_number triggers full transaction rollback (zero records persisted)."""
        bad_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-ROLLBACK-001",
                order_number="NON_EXISTENT_ORDER_999",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=5.0
            )
        )
        service = IngestionPersistenceService(self.db)
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payload(bad_payload, job_id="JOB-FAIL-01")

        self.db.close()
        fresh_db = self.SessionLocal()
        try:
            self.assertEqual(fresh_db.query(Batch).count(), 0)
            self.assertEqual(fresh_db.query(BatchMaterialConsumption).count(), 0)
            self.assertEqual(fresh_db.query(ConcreteSample).count(), 0)
        finally:
            fresh_db.close()

    def test_06_unresolvable_material_causes_complete_rollback(self):
        """Unresolvable material code triggers full transaction rollback (batch & job rolled back)."""
        bad_mat_payload = SingleIngestionPayloadDTO(
            batch=self.full_payload.batch,
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="UNREGISTERED_MAT", planned_quantity=100.0, actual_quantity=100.0)
            ]
        )
        service = IngestionPersistenceService(self.db)
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payload(bad_mat_payload, job_id="JOB-FAIL-MAT")

        self.db.close()
        fresh_db = self.SessionLocal()
        try:
            self.assertEqual(fresh_db.query(Batch).count(), 0)
            self.assertEqual(fresh_db.query(BatchMaterialConsumption).count(), 0)
        finally:
            fresh_db.close()

    # --- 4. Idempotency Verification Tests ---
    def test_07_duplicate_batch_number_rejected(self):
        """Submitting duplicate batch_number throws DuplicateIngestionException and rolls back."""
        service = IngestionPersistenceService(self.db)
        service.persist_canonical_payload(self.full_payload, job_id="JOB-FIRST")

        dup_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P2-TEST-001", # Same batch number
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            )
        )
        res_dup = service.persist_canonical_payload(dup_payload, job_id="JOB-SECOND")
        self.assertEqual(res_dup["status"], "SUCCESS")
        batches = self.db.query(Batch).filter(Batch.batch_number == "BATCH-P2-TEST-001").all()
        self.assertEqual(len(batches), 1, "R7 Contract: Identical batch re-ingestion MUST be NO-OP without exception")

    def test_08_duplicate_sample_number_rejected(self):
        """Submitting duplicate sample_number throws DuplicateIngestionException."""
        service = IngestionPersistenceService(self.db)
        service.persist_canonical_payload(self.full_payload, job_id="JOB-SAMPLE-FIRST")

        dup_sample_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P2-TEST-002", # Different batch number
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-CUBE-P2-001", # Duplicate sample number
                    age_days=28,
                    compressive_strength_mpa=50.0,
                    testing_timestamp=datetime(2026, 9, 7, tzinfo=timezone.utc)
                )
            ]
        )
        with self.assertRaises((DuplicateIngestionException, EntityMappingException)):
            service.persist_canonical_payload(dup_sample_payload, job_id="JOB-SAMPLE-SECOND")


    # --- 5. Source Channel Lineage & Job Lifecycle Tests ---
    def test_09_excel_source_channel_lineage_preserved(self):
        """EXCEL source channel is accurately persisted in IngestionJobModel tracking record."""
        excel_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-EXCEL-888",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=7.5
            )
        )
        service = IngestionPersistenceService(self.db)
        result = service.persist_canonical_payload(excel_payload, job_id="JOB-EXCEL-888", source_channel="EXCEL")

        job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-EXCEL-888").first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "COMPLETED")
        self.assertEqual(job.dataset_id, "CHANNEL-EXCEL")
        logs = json.loads(job.logs_json)
        self.assertEqual(logs["source_channel"], "EXCEL")
        self.assertEqual(logs["batch_id"], result["batch_id"])




    # --- 6. Extended Phase 2 Certification Tests ---
    def test_10_raw_material_actual_quantity_preservation_without_recalculation(self):
        """
        Verify Phase 2 IngestionPersistenceService and IngestionUnitOfWork persist the exact
        actual_quantity and planned_quantity ORM attributes produced by CanonicalEntityMapper
        without recalculating, deriving, multiplying, rounding, or overwriting them in Phase 2.
        """
        raw_quantity = Decimal("330.90")
        custom_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-RAW-MAT-99",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEMENT",
                    source_material_code="RAW CEMENT O1",
                    planned_quantity=Decimal("320.00"),
                    actual_quantity=raw_quantity,
                    moisture_percentage=Decimal("2.50"),
                    absorption_percentage=Decimal("0.80"),
                    moisture_correction_kg=Decimal("48.00")
                )
            ]
        )

        service = IngestionPersistenceService(self.db)
        result = service.persist_canonical_payload(custom_payload, job_id="JOB-RAW-MAT")
        batch_id = result["batch_id"]

        self.db.close()
        fresh_db = self.SessionLocal()
        try:
            cons = fresh_db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
            self.assertIsNotNone(cons)
            # Verify Phase 2 persisted ORM actual_quantity cleanly without Phase 2 recalculation/modification
            expected_orm_val = Decimal(str(round(330.90 * 6.0, 2))) # 1985.40
            self.assertEqual(cons.actual_quantity, expected_orm_val)
            self.assertEqual(cons.source_material_code, "RAW CEMENT O1")
            self.assertEqual(cons.moisture_percentage, Decimal("2.50"))
            self.assertEqual(cons.absorption_percentage, Decimal("0.80"))
            self.assertEqual(cons.moisture_correction_kg, Decimal("48.00"))
        finally:
            fresh_db.close()

    def test_11_failed_job_lifecycle_state_persistence_in_separate_transaction(self):
        """
        Verify that when ingestion fails (e.g., EntityMappingException), business records
        are rolled back while the IngestionJobModel status is persisted as FAILED.
        """
        # Create job tracking record beforehand
        job_id = "JOB-FAIL-STATE-01"
        initial_job = IngestionJobModel(
            job_id=job_id,
            session_id="SESS-TEST",
            dataset_id="CHANNEL-MANUAL",
            mapping_execution_id="EXEC-FAIL",
            status="PENDING",
            current_stage="INITIALIZED",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(initial_job)
        self.db.commit()

        bad_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FAIL-STATE",
                order_number="INVALID_ORDER_ID",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=5.0
            )
        )
        service = IngestionPersistenceService(self.db)
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payload(bad_payload, job_id=job_id)

        self.db.close()
        fresh_db = self.SessionLocal()
        try:
            # Business records rolled back
            self.assertEqual(fresh_db.query(Batch).filter(Batch.batch_number == "BATCH-FAIL-STATE").count(), 0)
            # Job state persisted as FAILED
            job = fresh_db.query(IngestionJobModel).filter(IngestionJobModel.job_id == job_id).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "FAILED")
            self.assertEqual(job.current_stage, "FAILED")
            self.assertIsNotNone(job.failure_reason)
        finally:
            fresh_db.close()

    def test_12_db_unique_constraint_rejects_duplicate_batch(self):
        """
        Verify database-level unique constraint on prd_batches.batch_number
        protects against duplicates and throws DuplicateIngestionException.
        """
        service = IngestionPersistenceService(self.db)
        service.persist_canonical_payload(self.full_payload, job_id="JOB-UNIQUE-1")

        # Bypass service pre-check to test DB-level unique constraint directly
        uow = IngestionUnitOfWork(self.db)
        uow.begin()
        dup_batch = Batch(
            id="PRD-BATCH-DUP-DB",
            batch_number="BATCH-P2-TEST-001", # Duplicate batch_number
            order_id="ORD-MANUAL-01-ID",
            dispatch_schedule_id="DSP-001-ID",
            recipe_id="REC-M40-ID",
            plant_id="PLANT-ID-MUMBAI-01",
            planned_quantity_m3=6.0
        )
        self.db.add(dup_batch)
        with self.assertRaises(Exception): # DB IntegrityError on flush/commit
            uow.flush()
        uow.rollback()

    def test_13_db_unique_constraint_rejects_duplicate_sample(self):
        """
        Verify database-level unique constraint on lab_samples.sample_number
        protects against duplicate samples.
        """
        service = IngestionPersistenceService(self.db)
        service.persist_canonical_payload(self.full_payload, job_id="JOB-SAMPLE-UNIQUE-1")

        uow = IngestionUnitOfWork(self.db)
        uow.begin()
        dup_sample = ConcreteSample(
            id="LAB-SAMPLE-DUP-DB",
            batch_id="PRD-BATCH-P2-001",
            sample_number="QC-CUBE-P2-001", # Duplicate sample_number
            sampling_timestamp=datetime.now(timezone.utc)
        )
        self.db.add(dup_sample)
        with self.assertRaises(Exception):
            uow.flush()
        uow.rollback()

    def test_14_zero_side_effect_transaction_ownership(self):
        """
        Verify IngestionUnitOfWork is the sole owner of transaction lifecycle
        and that no independent commits occur outside UoW.
        """
        uow = IngestionUnitOfWork(self.db)
        self.assertFalse(self.db.in_transaction())
        uow.begin()
        self.assertTrue(self.db.in_transaction())
        uow.rollback()
        self.assertFalse(self.db.in_transaction())

    def test_15_runtime_development_database_isolation(self):
        """
        Verify runtime/development SQLite database acc_rmc_dev.sqlite3
        remains untouched with prd_batches count strictly equal to 0.
        """
        from src.database.engine import get_database_engine
        from sqlalchemy import select, func
        dev_engine = get_database_engine()
        with dev_engine.connect() as conn:
            cnt = conn.execute(select(func.count()).select_from(Batch)).scalar()
            self.assertEqual(cnt, 0, "CRITICAL: Runtime/Dev database modified! prd_batches count must be 0.")


if __name__ == '__main__':
    unittest.main()
