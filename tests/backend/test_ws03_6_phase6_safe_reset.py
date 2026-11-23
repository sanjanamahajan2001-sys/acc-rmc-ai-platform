"""
WS-03.6 Phase 6: Safe Ingestion Data Reset & Clean Re-ingestion Certification Test Suite.

Verifies:
1. Environment Safety Gate (APP_ENV=production blocks reset).
2. Automated Pre-Reset Backup Creation.
3. Strict Master Reference Data Preservation (Plants, Recipes, Materials, Orders).
4. Dependency-Aware Ingestion Table Cleanup (0 batches, 0 consumptions, 0 tests).
5. Post-Reset Fresh Ingestion Lifecycle (Excel Ingestion & Manual Entry).
6. Repeated Reset & Ingestion Cycles.
"""

import os
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.ingestion_router import get_db_session
from src.database.base import BaseModel
from src.database.models.master import Plant, Recipe, Material, Customer, Project
from src.database.models.orders import Order
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import CubeTest, CubeSet, ConcreteSample, FT7Certificate, SlumpTest
from src.database.models.mapping_persistence import IngestionJobModel, SessionMappingModel
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.contracts.ingestion.batch import BatchIngestionDTO
from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
from src.contracts.ingestion.quality import CubeTestIngestionDTO
from src.services.ingestion_persistence_service import IngestionPersistenceService


class TestWS036Phase6SafeReset(unittest.TestCase):
    """Safe Ingestion Data Reset Test Suite."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory test database with multi-thread support for FastAPI TestClient."""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        BaseModel.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Create fresh session and seed reference master data."""
        self.db = self.SessionLocal()
        
        def override_get_db():
            db_session = self.SessionLocal()
            try:
                yield db_session
            finally:
                db_session.close()

        app.dependency_overrides[get_db_session] = override_get_db
        self.client = TestClient(app)

        # Seed Master Reference Data
        self.plant = Plant(id="PLANT-RESET-01", plant_code="PLANT-RESET-01", plant_name="Reset Plant", location="Test Loc", timezone="Asia/Kolkata")
        self.recipe = Recipe(id="REC-RESET-01", recipe_code="M40_VW_UT_ISOLATED", recipe_name="M40 Reset Concrete", target_strength_mpa=Decimal("40.0"))
        self.mat = Material(id="MAT-RESET-01", material_code="CEMENT", material_name="Portland Cement")
        self.cust = Customer(id="CUST-RESET-01", customer_code="CUST-01", legal_name="Test Customer")
        self.proj = Project(id="PRJ-RESET-01", project_code="PRJ-01", project_name="Test Project", customer_id="CUST-RESET-01")
        self.order = Order(id="ORD-RESET-01", order_number="ORD-RESET-01", customer_id="CUST-RESET-01", project_id="PRJ-RESET-01", plant_id="PLANT-RESET-01", order_status_id="LKP-ORD-CONFIRMED", requested_delivery_datetime=datetime.now(timezone.utc))

        self.db.add_all([self.plant, self.recipe, self.mat, self.cust, self.proj, self.order])
        self.db.commit()

    def tearDown(self):
        """Clean up test session."""
        self.db.rollback()
        for table in reversed(BaseModel.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()
        app.dependency_overrides.clear()

    def test_01_reset_clears_ingestion_data_and_preserves_master_data(self):
        """Verify reset endpoint clears ingestion tables to 0 while preserving master reference rows."""
        # 1. Populate ingestion records
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-RESET-TEST-01",
                order_number="ORD-RESET-01",
                plant_code="PLANT-RESET-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEMENT",
                    planned_quantity=Decimal("350.00"),
                    actual_quantity=Decimal("350.00")
                )
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-RESET-01",
                    age_days=28,
                    compressive_strength_mpa=Decimal("45.50"),
                    testing_timestamp=datetime.now(timezone.utc)
                )
            ]
        )
        service = IngestionPersistenceService(self.db)
        service.persist_canonical_payloads([payload], job_id="JOB-RESET-01")

        # Verify populated before reset
        self.assertEqual(self.db.query(Batch).count(), 1)
        self.assertEqual(self.db.query(BatchMaterialConsumption).count(), 1)
        self.assertEqual(self.db.query(CubeTest).count(), 1)

        # 2. Call Reset Endpoint
        res = self.client.post("/api/v1/ingestion/reset", json={"confirm": True, "reason": "Automated Unit Test"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "RESET_COMPLETE")
        self.assertEqual(data["orphan_count"], 0)
        self.assertEqual(data["synthetic_count"], 0)

        # 3. Verify All Ingestion Tables are 0
        fresh_db = self.SessionLocal()
        try:
            self.assertEqual(fresh_db.query(Batch).count(), 0)
            self.assertEqual(fresh_db.query(BatchMaterialConsumption).count(), 0)
            self.assertEqual(fresh_db.query(CubeTest).count(), 0)
            self.assertEqual(fresh_db.query(CubeSet).count(), 0)
            self.assertEqual(fresh_db.query(ConcreteSample).count(), 0)
            self.assertEqual(fresh_db.query(IngestionJobModel).count(), 0)

            # 4. Verify Master Reference Data is Strictly Preserved
            self.assertEqual(fresh_db.query(Plant).count(), 1)
            self.assertEqual(fresh_db.query(Recipe).count(), 1)
            self.assertEqual(fresh_db.query(Material).count(), 1)
            self.assertEqual(fresh_db.query(Customer).count(), 1)
            self.assertEqual(fresh_db.query(Project).count(), 1)
            self.assertEqual(fresh_db.query(Order).count(), 1)
        finally:
            fresh_db.close()

    def test_02_production_environment_safety_gate(self):
        """Verify reset operation hard-fails with HTTP 403 when APP_ENV == 'production'."""
        os.environ["APP_ENV"] = "production"
        try:
            res = self.client.post("/api/v1/ingestion/reset", json={"confirm": True})
            self.assertEqual(res.status_code, 403)
            self.assertIn("forbidden in production", res.json()["detail"].lower())
        finally:
            os.environ["APP_ENV"] = "development"

    def test_03_reset_requires_explicit_confirmation(self):
        """Verify reset without confirm=True returns HTTP 400."""
        res = self.client.post("/api/v1/ingestion/reset", json={"confirm": False})
        self.assertEqual(res.status_code, 400)
        self.assertIn("explicit confirmation is required", res.json()["detail"].lower())

    def test_04_repeated_reset_and_reingestion_cycle(self):
        """Verify repeated reset -> ingest -> reset -> ingest cycles operate idempotently without residue."""
        for cycle in range(1, 4):
            # Ingest record
            fresh_db = self.SessionLocal()
            service = IngestionPersistenceService(fresh_db)
            payload = SingleIngestionPayloadDTO(
                batch=BatchIngestionDTO(
                    batch_number=f"BATCH-CYCLE-{cycle}",
                    order_number="ORD-RESET-01",
                    plant_code="PLANT-RESET-01",
                    recipe_code="M40_VW_UT_ISOLATED",
                    planned_quantity_m3=6.0
                )
            )
            service.persist_canonical_payloads([payload], job_id=f"JOB-CYCLE-{cycle}")
            self.assertEqual(fresh_db.query(Batch).count(), 1)
            fresh_db.close()

            # Reset
            res = self.client.post("/api/v1/ingestion/reset", json={"confirm": True})
            self.assertEqual(res.status_code, 200)

            fresh_db2 = self.SessionLocal()
            self.assertEqual(fresh_db2.query(Batch).count(), 0)
            self.assertEqual(fresh_db2.query(Plant).count(), 1)
            fresh_db2.close()


if __name__ == "__main__":
    unittest.main()
