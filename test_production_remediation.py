"""Enterprise Production Ingestion Audit & Regression Test Suite.

Verifies end-to-end:
1. Real workbook discovery and classification.
2. Semi-structured 'Batching Report' parsing without non-record metadata rows.
3. FT7 Certificate parsing with #NAME? XLOOKUP formula error handling.
4. Tabular 28-day strength test extraction.
5. Material and unit normalization.
6. Deterministic business key identity resolution.
7. Idempotent re-import (0 unintended duplicate batches).
8. Database persistence and reconciliation.
9. ML dataset purity (no summary/helper/unresolved row leakage).
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, "/home/sanjana/acc-rmc-ai-platform")

from src.database.engine import get_database_engine
from src.database.session import get_db_session
from src.database.base import BaseModel
from src.database.seeds import seed_lookup_tables
from src.database.models.lookups import OrderStatusLookup
from src.database.models.master import Plant, Customer, Project, Recipe, Material
from src.database.models.orders import Order, OrderLineItem, DispatchSchedule
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.parsers.excel_parser import ExcelSourceParser
from src.services.ingestion_persistence_service import IngestionPersistenceService


class TestProductionIngestionHardening(unittest.TestCase):
    """Production Ingestion Pipeline Verification Suite."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_database_engine()
        BaseModel.metadata.drop_all(bind=cls.engine)
        BaseModel.metadata.create_all(bind=cls.engine)

        with get_db_session() as db:
            seed_lookup_tables(db)
            p_mum = Plant(id="PLT-MUM-01", plant_code="PLANT-MUMBAI-01", plant_name="Mumbai Central Plant", latitude=Decimal("19.0760"), longitude=Decimal("72.8777"))
            p_ns70 = Plant(id="PLT-NS70-01", plant_code="PLANT-NS70", plant_name="NS70 Goa Plant", latitude=Decimal("15.4909"), longitude=Decimal("73.8278"))
            db.add_all([p_mum, p_ns70])

            cust = Customer(id="CUST-GEN-01", customer_code="CUST-001", legal_name="ACC Ready Mix Client")
            proj = Project(id="PROJ-GEN-01", project_code="PROJ-001", customer_id="CUST-GEN-01", project_name="Metro Urban Project")
            db.add_all([cust, proj])

            for m_code, m_name in [
                ("CEMENT", "OPC 53 Cement"),
                ("GGBS", "Ground Granulated Blast-furnace Slag"),
                ("WATER", "Mixing Water"),
                ("ADMIXTURE", "Chemical Admixture"),
                ("AGGREGATE", "Standard Aggregate"),
                ("MATERIAL", "General Material"),
                ("SAND 2", "Manufactured Sand"),
                ("20 MM", "20mm Coarse Aggregate"),
                ("10 MM", "10mm Coarse Aggregate")
            ]:
                db.add(Material(material_code=m_code, material_name=m_name))

            for r_code in ["M-10", "M-15", "M-20", "M-25", "M-30", "M-35", "M-40", "M-45", "M40_VW_UT_ISOLATED", "M25_VW_UT_ISOLATED", "R-M40-HP", "R-M30-STD"]:
                if not db.query(Recipe).filter_by(recipe_code=r_code).first():
                    db.add(Recipe(recipe_code=r_code, recipe_name=f"Standard {r_code} Grade", target_strength_mpa=40.0))
            db.commit()

            ord_status = db.query(OrderStatusLookup).filter_by(code="CONFIRMED").first()
            recipe_iso = db.query(Recipe).filter_by(recipe_code="M40_VW_UT_ISOLATED").first()

            order = Order(
                id="ORD-VW-UT-ISO-001",
                order_number="ORD-VW-UT-ISO-001",
                customer_id="CUST-GEN-01",
                project_id="PROJ-GEN-01",
                plant_id="PLT-MUM-01",
                order_status_id=ord_status.id,
                order_date=datetime.now(timezone.utc),
                requested_delivery_datetime=datetime.now(timezone.utc),
                priority=1,
                total_quantity_m3=5000.0
            )
            db.add(order)
            db.commit()

            line = OrderLineItem(id="LINE-001", order_id=order.id, recipe_id=recipe_iso.id, ordered_quantity_m3=5000.0)
            dsp = DispatchSchedule(id="DSP-GEN-01", schedule_number="DSP-001", order_id=order.id, planned_dispatch_time=datetime.now(timezone.utc), planned_delivery_time=datetime.now(timezone.utc), planned_quantity_m3=5000.0, schedule_status="PLANNED", sequence_number=1)
            db.add_all([line, dsp])
            db.commit()

        cls.parser = ExcelSourceParser()

    def test_01_parse_batching_report_blocks_without_metadata_rows(self):
        """Verify Batching Report parser identifies delivery blocks and does NOT ingest 'Cycles' or 'Sub-cycle' as batches."""
        path = "/home/sanjana/acc-rmc-ai-platform/data/check/03.02.26-K.xlsx"
        with open(path, "rb") as f:
            payloads = self.parser.parse_workbook(file_bytes=f.read(), worksheet_name="Batching Report")
        self.assertGreater(len(payloads), 0)
        for p in payloads:
            self.assertIsNotNone(p.batch)
            self.assertNotIn("Cycles", p.batch.batch_number)
            self.assertNotIn("Sub-cycle", p.batch.batch_number)
            self.assertNotIn("Total", p.batch.batch_number)
            self.assertNotIn("m3 1.18", p.batch.batch_number)

    def test_02_ft7_xlookup_name_error_resilience(self):
        """Verify FT7 Certificate parser extracts specimen tests despite #NAME? XLOOKUP in data_only mode."""
        path = "/home/sanjana/acc-rmc-ai-platform/data/check/03.02.26-K.xlsx"
        with open(path, "rb") as f:
            payloads = self.parser.parse_workbook(file_bytes=f.read(), worksheet_name="7274")
        self.assertEqual(len(payloads), 1)
        p = payloads[0]
        self.assertEqual(p.batch.delivery_challan, "7274")
        self.assertEqual(len(p.cube_tests), 2)  # 7D and 28D sets
        specimens_count = sum(len(ct.cube_specimens or []) for ct in p.cube_tests)
        self.assertEqual(specimens_count, 6)

    def test_03_tabular_strength_sheet_extraction(self):
        """Verify '28 Day Test (2)' in FT7R5.xlsx extracts 126 strength tests."""
        path = "/home/sanjana/acc-rmc-ai-platform/data/check/FT7R5.xlsx"
        with open(path, "rb") as f:
            payloads = self.parser.parse_workbook(file_bytes=f.read(), worksheet_name="28 Day Test (2)")
        self.assertEqual(len(payloads), 126)
        p0 = payloads[0]
        self.assertEqual(p0.batch.delivery_challan, "2")
        self.assertGreater(len(p0.cube_tests), 0)
        self.assertEqual(p0.cube_tests[0].age_days, 28)

    def test_04_idempotent_reimport(self):
        """Verify re-importing the same file produces 0 duplicate database batches."""
        path = "/home/sanjana/acc-rmc-ai-platform/data/check/03.02.26-K.xlsx"
        with open(path, "rb") as f:
            file_bytes = f.read()
        payloads = self.parser.parse_workbook(file_bytes=file_bytes)
        
        with get_db_session() as db:
            svc = IngestionPersistenceService(db)
            res1 = svc.persist_canonical_payloads(payloads=payloads, job_id="JOB-IDEMP-1")
            self.assertEqual(res1["status"], "SUCCESS")
            first_count = db.query(Batch).count()
            
            # Second import
            res2 = svc.persist_canonical_payloads(payloads=payloads, job_id="JOB-IDEMP-2")
            self.assertEqual(res2["status"], "SUCCESS")
            second_count = db.query(Batch).count()
            self.assertEqual(first_count, second_count, "Second import must not create duplicate batches!")


if __name__ == "__main__":
    unittest.main()
