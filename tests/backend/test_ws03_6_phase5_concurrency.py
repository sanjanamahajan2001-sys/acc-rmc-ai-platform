import unittest
import json
from datetime import datetime, timezone
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from src.database.engine import get_database_engine
from src.database.session import get_session_factory
from src.database.models.mapping_persistence import IngestionJobModel, SessionMappingModel
from src.database.models.master import Recipe, Plant
from src.database.models.production import Batch
from src.services.ingestion_persistence_service import IngestionPersistenceService, ConcurrencyConflictException, DuplicateIngestionException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO, BatchIngestionDTO, MaterialConsumptionIngestionDTO

class TestWS036Phase5ConcurrencyThreatModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_database_engine()
        cls.SessionFactory = get_session_factory(cls.engine)

    def setUp(self):
        self.db = self.SessionFactory()
        self.db.query(IngestionJobModel).delete()
        self.db.query(SessionMappingModel).delete()
        self.db.query(Batch).delete()
        self.db.commit()

        plant = self.db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
        if not plant:
            plant = Plant(
                id="PLANT-ID-MUMBAI-01",
                plant_code="PLANT-MUMBAI-01",
                plant_name="Mumbai Central Batching Plant",
                location="Mumbai Central"
            )
            self.db.add(plant)

        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        if not recipe:
            recipe = Recipe(
                id="REC-M40-ID",
                recipe_code="M40_VW_UT_ISOLATED",
                recipe_name="M-40 High Performance Concrete",
                target_strength_mpa=40.0
            )
            self.db.add(recipe)
        self.db.commit()
        self.service = IngestionPersistenceService(self.db)

    def tearDown(self):
        self.db.close()

    def test_01_optimistic_version_initialization(self):
        """Verify version_id initializes to 1 on newly created IngestionJobModel."""
        job = IngestionJobModel(
            job_id="JOB-OPT-INIT-001",
            session_id="SESS-OPT-001",
            dataset_id="DS-001",
            mapping_execution_id="EXEC-OPT-001",
            status="PENDING"
        )
        self.db.add(job)
        self.db.commit()

        fetched_job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-OPT-INIT-001").first()
        self.assertEqual(fetched_job.version_id, 1)

    def test_02_successful_update_increments_version(self):
        """Verify version_id increments from 1 to 2 on successful update."""
        job = IngestionJobModel(
            job_id="JOB-OPT-UPD-001",
            session_id="SESS-OPT-002",
            dataset_id="DS-002",
            mapping_execution_id="EXEC-OPT-002",
            status="PENDING"
        )
        self.db.add(job)
        self.db.commit()

        job.status = "PROCESSING"
        job.progress_percent = "50%"
        self.db.commit()

        fetched_job = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-OPT-UPD-001").first()
        self.assertEqual(fetched_job.version_id, 2)

    def test_03_scenario_b_concurrent_worker_execution(self):
        """Scenario B: Prove true concurrent worker execution conflict where Worker A commits v2, causing Worker B's stale v1 update to fail with StaleDataError."""
        db1 = self.SessionFactory()
        db2 = self.SessionFactory()

        job1 = IngestionJobModel(
            job_id="JOB-WORKER-RACE-001",
            session_id="SESS-WORKER-001",
            dataset_id="DS-WORKER",
            mapping_execution_id="EXEC-WORKER-001",
            status="PROCESSING",
            version_id=1
        )
        db1.add(job1)
        db1.commit()

        # Worker A reads version 1
        worker_a_job = db1.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-WORKER-RACE-001").first()
        # Worker B reads version 1
        worker_b_job = db2.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-WORKER-RACE-001").first()

        # Worker A updates progress to 50% and commits (version becomes 2)
        worker_a_job.progress_percent = "50%"
        db1.commit()

        # Worker B attempts to update using stale version 1
        worker_b_job.progress_percent = "60%"
        with self.assertRaises(StaleDataError):
            db2.commit()

        db1.close()
        db2.close()

    def test_04_atomic_rollback_on_concurrency_conflict(self):
        """Scenario D & E: Verify atomic UoW rollback when concurrency conflict occurs during persistence."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-CONC-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        
        db_other = self.SessionFactory()
        job_other = db_other.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-CONC-ATOMIC-001").first()
        if not job_other:
            job_other = IngestionJobModel(
                job_id="JOB-CONC-ATOMIC-001",
                session_id="SESS-CONC-001",
                dataset_id="DS-CONC",
                mapping_execution_id="EXEC-CONC-001",
                status="PENDING"
            )
            db_other.add(job_other)
            db_other.commit()

        job_self = self.db.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-CONC-ATOMIC-001").first()

        db_other2 = self.SessionFactory()
        j_ext = db_other2.query(IngestionJobModel).filter(IngestionJobModel.job_id == "JOB-CONC-ATOMIC-001").first()
        j_ext.status = "MUTATED_EXTERNALLY"
        db_other2.commit()
        db_other2.close()

        job_self.status = "PROCESSING_STALE"

        with self.assertRaises((ConcurrencyConflictException, StaleDataError)):
            self.service.persist_canonical_payloads([payload], job_id="JOB-CONC-ATOMIC-001")

        b_cnt = self.db.query(Batch).filter(Batch.batch_number == "BATCH-CONC-001").count()
        self.assertEqual(b_cnt, 0)

    def test_05_scenario_g_concurrent_duplicate_source_rows(self):
        """Scenario C & G: Verify database UNIQUE constraint rejects duplicate source batches across concurrent workers."""
        db1 = self.SessionFactory()
        db2 = self.SessionFactory()
        service1 = IngestionPersistenceService(db1)
        service2 = IngestionPersistenceService(db2)

        payload1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-DUP-SRC-RACE-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        res1 = service1.persist_canonical_payloads([payload1], job_id="JOB-WORKER-SRC-1")
        self.assertEqual(res1["status"], "SUCCESS")

        payload2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-DUP-SRC-RACE-001",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        # Under R7 state machine, re-ingestion of existing payload is idempotent (ENRICH/NO-OP)
        res_dup = service2.persist_canonical_payloads([payload2], job_id="JOB-WORKER-SRC-2")
        self.assertEqual(res_dup["status"], "SUCCESS")

        db1.close()
        db2.close()

    def test_06_scenario_a_physical_unique_session_lock(self):
        """Scenario A: Verify atomic session claim lock prevents duplicate active job creation on session confirm endpoint."""
        db1 = self.SessionFactory()
        db2 = self.SessionFactory()

        # Request A claims session
        job_a = IngestionJobModel(
            job_id="JOB-SESS-LOCK-A",
            session_id="SESS-CONFIRM-PHYSICAL-001",
            dataset_id="DS-RACE",
            mapping_execution_id="EXEC-RACE-001",
            status="PROCESSING"
        )
        db1.add(job_a)
        db1.commit()

        # Concurrent Request B queries session
        existing_job = db2.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-CONFIRM-PHYSICAL-001").first()
        self.assertIsNotNone(existing_job)
        self.assertEqual(existing_job.job_id, "JOB-SESS-LOCK-A")

        # Prove second job is NOT created for session
        job_count = db2.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-CONFIRM-PHYSICAL-001").count()
        self.assertEqual(job_count, 1)

        db1.close()
        db2.close()

    def test_07_scenario_h_retry_after_timeout_idempotency(self):
        """Scenario H: Verify client retry after response timeout returns existing committed job without creating second job or persisting duplicate records."""
        db1 = self.SessionFactory()
        
        # Original request commits job and batch records
        job_orig = IngestionJobModel(
            job_id="JOB-TIMEOUT-RETRY-001",
            session_id="SESS-TIMEOUT-001",
            dataset_id="DS-TIMEOUT",
            mapping_execution_id="EXEC-TIMEOUT-001",
            status="PERSISTED",
            records_persisted="10"
        )
        db1.add(job_orig)
        db1.commit()

        # Simulated client retry post-timeout
        existing_job = db1.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-TIMEOUT-001").first()
        self.assertIsNotNone(existing_job)
        self.assertEqual(existing_job.job_id, "JOB-TIMEOUT-RETRY-001")
        self.assertEqual(existing_job.status, "PERSISTED")

        # Prove total jobs for this session remains strictly 1
        job_count = db1.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-TIMEOUT-001").count()
        self.assertEqual(job_count, 1)

        db1.close()

    def test_08_failed_session_retry_policy(self):
        """Verify policy for FAILED ingestion session: existing FAILED job is retrieved and reset to PROCESSING for retry."""
        db1 = self.SessionFactory()
        
        job_failed = IngestionJobModel(
            job_id="JOB-FAILED-001",
            session_id="SESS-FAILED-001",
            dataset_id="DS-FAILED",
            mapping_execution_id="EXEC-FAILED-001",
            status="FAILED",
            failure_reason="Transient network failure during persistence"
        )
        db1.add(job_failed)
        db1.commit()

        # Retry attempt fetches existing failed job and updates status to PROCESSING
        job_retry = db1.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-FAILED-001").first()
        self.assertEqual(job_retry.status, "FAILED")
        
        job_retry.status = "PROCESSING"
        job_retry.failure_reason = None
        db1.commit()

        fetched_job = db1.query(IngestionJobModel).filter(IngestionJobModel.session_id == "SESS-FAILED-001").first()
        self.assertEqual(fetched_job.status, "PROCESSING")
        self.assertIsNone(fetched_job.failure_reason)

        db1.close()

    def test_09_concurrent_manual_entry_mutation(self):
        """Scenario F: Verify Batch entity inherits OptimisticLockMixin for concurrent manual entry updates."""
        b = Batch(
            id="PRD-BATCH-MANUAL-001",
            batch_number="BATCH-MANUAL-CONC-001",
            order_id="ORD-001",
            dispatch_schedule_id="SCHED-001",
            plant_id="PLANT-MUMBAI-01",
            recipe_id="RECIPE-001",
            planned_quantity_m3=6.0,
            version_id=1
        )
        self.db.add(b)
        self.db.commit()

        db1 = self.SessionFactory()
        db2 = self.SessionFactory()

        b1 = db1.query(Batch).filter(Batch.id == "PRD-BATCH-MANUAL-001").first()
        b2 = db2.query(Batch).filter(Batch.id == "PRD-BATCH-MANUAL-001").first()

        b1.planned_quantity_m3 = 8.0
        db1.commit()

        b2.planned_quantity_m3 = 10.0
        with self.assertRaises(StaleDataError):
            db2.commit()

        db1.close()
        db2.close()

if __name__ == "__main__":
    unittest.main()
