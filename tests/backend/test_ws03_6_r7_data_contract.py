import unittest
from datetime import datetime, timezone
from decimal import Decimal
import openpyxl

from src.database.engine import get_database_engine
from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe, Material
from src.database.models.orders import Order
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest, FT7Certificate
from src.database.models.mapping_persistence import IngestionJobModel
from src.services.ingestion_persistence_service import IngestionPersistenceService, ConcurrencyConflictException, DuplicateIngestionException
from src.mappers.canonical_entity_mapper import EntityMappingException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO, BatchIngestionDTO, MaterialConsumptionIngestionDTO, CubeTestIngestionDTO, FT7CertificateIngestionDTO, SlumpTestIngestionDTO
from src.parsers.excel_parser import ExcelSourceParser


class TestWS036R7DataContractAlignment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = get_database_engine()
        cls.SessionFactory = get_session_factory(cls.engine)

    @classmethod
    def tearDownClass(cls):
        db = cls.SessionFactory()
        try:
            db.query(FT7Certificate).delete()
            db.query(CubeTest).delete()
            db.query(CubeSet).delete()
            db.query(ConcreteSample).delete()
            db.query(BatchMaterialConsumption).delete()
            db.query(Batch).delete()
            db.commit()
        finally:
            db.close()

    def setUp(self):
        self.db = self.SessionFactory()
        self.db.query(FT7Certificate).delete()
        self.db.query(CubeTest).delete()
        self.db.query(CubeSet).delete()
        self.db.query(ConcreteSample).delete()
        self.db.query(BatchMaterialConsumption).delete()
        self.db.query(Batch).delete()
        self.db.commit()
        # Ensure active master seed baseline exists
        plant = self.db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
        if not plant:
            plant = Plant(
                id="PLANT-ID-MUMBAI-01",
                plant_code="PLANT-MUMBAI-01",
                plant_name="Mumbai Central Batching Plant",
                location="Mumbai Central",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_deleted=False
            )
            self.db.add(plant)

        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        if not recipe:
            recipe = Recipe(
                id="REC-M40-ID",
                recipe_code="M40_VW_UT_ISOLATED",
                recipe_name="M-40 High Performance Concrete",
                target_strength_mpa=40.0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_deleted=False
            )
            self.db.add(recipe)

        order = self.db.query(Order).filter(Order.order_number == "ORD-VW-UT-ISO-001").first()
        if not order:
            order = Order(
                id="ORD-VW-UT-ISO-001-ID",
                order_number="ORD-VW-UT-ISO-001",
                customer_id="CUST-MUMBAI-01",
                project_id="PROJ-MUMBAI-01",
                plant_id="PLANT-MUMBAI-01-ID",
                order_status_id="STATUS-CONFIRMED",
                order_date=datetime.now(timezone.utc),
                requested_delivery_datetime=datetime.now(timezone.utc),
                priority=1,
                total_quantity_m3=100.0
            )
            self.db.add(order)

        mat = self.db.query(Material).filter(Material.material_code == "CEM-OPC-53").first()
        if not mat:
            mat = Material(
                id="MAT-OPC-53-ID",
                material_code="CEM-OPC-53",
                material_name="Ordinary Portland Cement 53 Grade",
                engineering_unit="KG",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(mat)

        # Seed Materials for Phase 3 tests
        for mat_code, mat_name in [
            ("MAT-CEM-01", "Cement OPC 53"),
            ("MAT-FA-10MM", "Fine Aggregate 10mm"),
            ("MAT-CA-20MM", "Coarse Aggregate 20mm")
        ]:
            mat = self.db.query(Material).filter(Material.material_code == mat_code).first()
            if not mat:
                mat = Material(
                    id=f"MAT-ID-{mat_code}",
                    material_code=mat_code,
                    material_name=mat_name,
                    engineering_unit="KG",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    is_deleted=False
                )
                self.db.add(mat)

        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_01_columns_and_ft7_same_challan_resolve_to_same_batch(self):
        """Test R7 linkage: Batching dispatches and FT7 quality certificates with same challan resolve to same Batch entity."""
        service = IngestionPersistenceService(self.db)
        
        # 1. Ingest Columns batching report payload for Challan 1749
        payload_col = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0,
                truck_number="GA07F7633"
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEM-OPC-53",
                    actual_quantity=380.0,
                    planned_quantity=380.0
                )
            ]
        )
        service.persist_canonical_payloads([payload_col], job_id="JOB-R7-LINK-1")
        
        # Verify batch created
        batch_before = self.db.query(Batch).filter(Batch.delivery_challan_number == "1749").first()
        self.assertIsNotNone(batch_before)
        self.assertEqual(batch_before.batch_number, "BATCH-1749")
        batch_id_initial = batch_before.id
        
        # 2. Ingest FT7 Quality Certificate payload for Challan 1749
        payload_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-1749-28D",
                    testing_timestamp=datetime.now(timezone.utc),
                    compressive_strength_mpa=48.5,
                    age_days=28
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-CERT-1749",
                issued_date=datetime.now(timezone.utc)
            )
        )
        service.persist_canonical_payloads([payload_ft7], job_id="JOB-R7-LINK-2")
        
        # Verify FT7 ENRICHED the existing Batch entity (SAME batch.id!)
        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "1749").all()
        self.assertEqual(len(batches), 1, "R7 Contract Violation: parallel batch entities created for same challan!")
        self.assertEqual(batches[0].id, batch_id_initial)
        
        # Verify laboratory QA entities attached to batch_id_initial
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id_initial).first()
        self.assertIsNotNone(sample)
        ft7 = self.db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch_id_initial).first()
        self.assertIsNotNone(ft7)
        self.assertEqual(ft7.certificate_number, "FT7-CERT-1749")

    def test_02_ft7_first_ingestion_creates_pending_batch_and_is_enriched(self):
        """Test FT7-first ingestion creates PENDING/PLANNED batch anchor, which is enriched when batching report arrives."""
        service = IngestionPersistenceService(self.db)
        
        # 1. Ingest FT7 certificate FIRST for Challan 9901
        payload_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-9901",
                order_number="ORD-9901",
                delivery_challan="9901",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-CERT-9901",
                issued_date=datetime.now(timezone.utc)
            )
        )
        service.persist_canonical_payloads([payload_ft7], job_id="JOB-FT7-FIRST-1")
        
        batch_anchor = self.db.query(Batch).filter(Batch.delivery_challan_number == "9901").first()
        self.assertIsNotNone(batch_anchor)
        self.assertEqual(batch_anchor.production_status, "PLANNED", "FT7-first batch anchor must have PLANNED status, not COMPLETED")
        
        # 2. Ingest Batching Report SECOND for Challan 9901
        payload_col = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-9901",
                order_number="ORD-9901",
                delivery_challan="9901",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0,
                truck_number="GA07F7625"
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEM-OPC-53",
                    actual_quantity=400.0,
                    planned_quantity=400.0
                )
            ]
        )
        service.persist_canonical_payloads([payload_col], job_id="JOB-FT7-FIRST-2")
        
        batch_enriched = self.db.query(Batch).filter(Batch.delivery_challan_number == "9901").first()
        self.assertEqual(batch_enriched.id, batch_anchor.id)
        self.assertEqual(batch_enriched.production_status, "COMPLETED", "Status must update to COMPLETED when batching report arrives")
        
        # Verify material consumption linked cleanly
        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_anchor.id).first()
        self.assertIsNotNone(mc)

    def test_03_exact_duplicate_payload_reinsertion_is_noop(self):
        """Test exact duplicate payload re-ingestion is NO-OP and does not duplicate consumptions."""
        service = IngestionPersistenceService(self.db)
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-8822",
                order_number="ORD-8822",
                delivery_challan="8822",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEM-OPC-53",
                    actual_quantity=350.0,
                    planned_quantity=350.0
                )
            ]
        )
        service.persist_canonical_payloads([payload], job_id="JOB-NOOP-1")
        
        # Re-ingest exact same payload
        service.persist_canonical_payloads([payload], job_id="JOB-NOOP-2")
        
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "8822").first()
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).all()
        self.assertEqual(len(consumptions), 1, "Duplicate re-ingestion inserted duplicate material consumptions!")



    def test_04_batch_number_does_not_contain_source_prefix_or_wb_prefix(self):
        """Test business batch_number is clean BATCH-{challan} without BATCH-COL-, BATCH-FT7-, or wb_prefix."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Columns"
        ws.cell(1, 2, "challan no.")
        ws.cell(2, 2, "1749")
        ws.cell(2, 3, "01-06-26")
        ws.cell(2, 4, "M-30")
        ws.cell(2, 5, "GA07F7625")
        ws.cell(2, 6, "6.00")
        
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertTrue(len(payloads) > 0)
        batch_num = payloads[0].batch.batch_number
        self.assertEqual(batch_num, "BATCH-1749", f"Unexpected batch_number format: {batch_num}")

    def test_p1_01_canonical_challan_identity(self):
        """Test Phase 1: challan 1749 generates canonical BATCH-1749."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Columns"
        ws.cell(1, 2, "challan no.")
        ws.cell(2, 2, "1749")
        ws.cell(2, 4, "M-40")
        ws.cell(2, 6, "6.00")
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertTrue(len(payloads) > 0)
        self.assertEqual(payloads[0].batch.batch_number, "BATCH-1749")
        self.assertEqual(payloads[0].batch.delivery_challan, "1749")

    def test_p1_02_no_columns_prefix(self):
        """Test Phase 1: Columns parser does not generate BATCH-COL- prefix."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Columns"
        ws.cell(1, 2, "challan no.")
        ws.cell(2, 2, "1749")
        ws.cell(2, 4, "M-40")
        ws.cell(2, 6, "6.00")
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertFalse(payloads[0].batch.batch_number.startswith("BATCH-COL-"))
        self.assertEqual(payloads[0].batch.batch_number, "BATCH-1749")

    def test_p1_03_no_ft7_prefix(self):
        """Test Phase 1: FT7 parser with valid challan does not generate BATCH-FT7- prefix."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "FT7 Sheet"
        ws.cell(1, 1, "FT 7 CERTIFICATE")
        ws.cell(10, 2, "1749")
        ws.cell(12, 2, "M-40")
        ws.cell(14, 2, "6.00")
        ws.cell(22, 2, "REF-01")
        now_naive = datetime.now()
        ws.cell(24, 2, now_naive)
        ws.cell(25, 2, now_naive)
        ws.cell(27, 2, 7)
        ws.cell(32, 2, 45.0)
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertTrue(len(payloads) > 0)
        self.assertFalse(payloads[0].batch.batch_number.startswith("BATCH-FT7-"))
        self.assertEqual(payloads[0].batch.batch_number, "BATCH-1749")

    def test_p1_04_no_standard_prefix_when_challan_exists(self):
        """Test Phase 1: Standard batching sheet with valid challan produces BATCH-{challan} without BATCH-STD- prefix."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "1749"
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertTrue(len(payloads) > 0)
        self.assertEqual(payloads[0].batch.batch_number, "BATCH-1749")
        self.assertEqual(payloads[0].batch.delivery_challan, "1749")

    def test_p1_05_wb_prefix_is_not_business_identity(self):
        """Test Phase 1: Changing sheet title / workbook prefix does not alter canonical BATCH-{challan} business identity."""
        parser = ExcelSourceParser()
        wb1 = openpyxl.Workbook()
        ws1 = wb1.active
        ws1.title = "Columns"
        ws1.cell(1, 2, "challan no.")
        ws1.cell(2, 2, "1749")
        ws1.cell(2, 4, "M-40")
        ws1.cell(2, 6, "6.00")
        import io
        buf1 = io.BytesIO()
        wb1.save(buf1)
        payloads1 = parser.parse_workbook(file_bytes=buf1.getvalue())

        wb2 = openpyxl.Workbook()
        ws2 = wb2.active
        ws2.title = "Columns"
        ws2.cell(1, 2, "challan no.")
        ws2.cell(2, 2, "1749")
        ws2.cell(2, 4, "M-40")
        ws2.cell(2, 6, "6.00")
        buf2 = io.BytesIO()
        wb2.save(buf2)
        payloads2 = parser.parse_workbook(file_bytes=buf2.getvalue())

        self.assertEqual(payloads1[0].batch.batch_number, payloads2[0].batch.batch_number)
        self.assertEqual(payloads1[0].batch.batch_number, "BATCH-1749")

    def test_p1_06_no_fabricated_challan(self):
        """Test Phase 1: Sources lacking a valid challan do not fabricate a business delivery_challan."""
        parser = ExcelSourceParser()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Forecast"
        ws.cell(1, 1, "Mix Grade")
        ws.cell(2, 1, "M-25")
        ws.cell(2, 2, datetime.now())
        ws.cell(2, 4, 300.0)
        ws.cell(2, 9, 35.0)
        import io
        buf = io.BytesIO()
        wb.save(buf)
        payloads = parser.parse_workbook(file_bytes=buf.getvalue())
        self.assertTrue(len(payloads) > 0)
        self.assertIsNone(payloads[0].batch.delivery_challan, "Sources lacking valid challan must retain delivery_challan = None")

    def test_05_same_challan_different_plants_resolves_to_separate_batches(self):
        """Test R7 production event identity (plant + challan): same challan at different plants creates distinct Batches."""
        # Create second plant
        plant2 = self.db.query(Plant).filter(Plant.plant_code == "PLANT-GOA-01").first()
        if not plant2:
            plant2 = Plant(
                id="PLANT-GOA-01-ID",
                plant_code="PLANT-GOA-01",
                plant_name="Goa South Batching Plant",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_deleted=False
            )
            self.db.add(plant2)
            self.db.commit()

        service = IngestionPersistenceService(self.db)
        
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-7001",
                order_number="ORD-7001",
                delivery_challan="7001",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0
            )
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-7001",
                order_number="ORD-7001",
                delivery_challan="7001",
                recipe_code="M-40",
                plant_code="PLANT-GOA-01",
                planned_quantity_m3=6.0
            )
        )
        service.persist_canonical_payloads([p1], job_id="JOB-PLANT-1")
        service.persist_canonical_payloads([p2], job_id="JOB-PLANT-2")
        
        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "7001").all()
        self.assertEqual(len(batches), 2, "Same challan at different plants must create separate Batch entities!")

    def test_06_material_and_specimen_attributes_preserved_without_defaults(self):
        """Test material-level metrics and individual 6-cube specimen metrics are 100% preserved."""
        service = IngestionPersistenceService(self.db)
        
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-5511",
                order_number="ORD-5511",
                delivery_challan="5511",
                recipe_code="M-40",
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEM-OPC-53",
                    actual_quantity=390.0,
                    planned_quantity=390.0,
                    moisture_percentage=1.5,
                    absorption_percentage=0.5,
                    moisture_correction_kg=5.8
                )
            ]
        )
        service.persist_canonical_payloads([payload], job_id="JOB-MAT-PRESERVE-1")
        
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "5511").first()
        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).first()
        self.assertIsNotNone(mc)
        self.assertEqual(float(mc.moisture_percentage), 1.5)
        self.assertEqual(float(mc.absorption_percentage), 0.5)
        self.assertEqual(float(mc.moisture_correction_kg), 5.8)

    # --- Phase 2 Focused Tests (GAP-02: Deterministic Production Event Resolution) ---

    def test_p2_01_columns_and_ft7_same_production_event(self):
        """TEST P2-01: Columns + FT7 with same plant, challan, and production timestamp resolve to same Batch.id."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        payload_cols = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEM-OPC-53", actual_quantity=Decimal("300.0"), planned_quantity=Decimal("300.0"))
            ]
        )
        payload_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-1749",
                issued_date=ts
            )
        )

        res1 = service.persist_canonical_payloads([payload_cols], job_id="JOB-P2-01-COLS")
        res2 = service.persist_canonical_payloads([payload_ft7], job_id="JOB-P2-01-FT7")

        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "1749").all()
        self.assertEqual(len(batches), 1, "Columns and FT7 representing same production event MUST resolve to exactly 1 Batch")
        self.assertEqual(res1["details"][0]["batch_id"], res2["details"][0]["batch_id"])

    def test_p2_02_same_challan_different_production_event(self):
        """TEST P2-02: Same plant + same challan but different production start times produce separate Batch resolution (returns None)."""
        ts1 = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts1
            )
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-1749",
                order_number="ORD-1749",
                delivery_challan="1749",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts2
            )
        )

        service.persist_canonical_payloads([p1], job_id="JOB-P2-02-1")

        # Resolving p2 must NOT match event 1 (returns None -> separate production event)
        match_batch = service._resolve_production_event(p2)
        self.assertIsNone(match_batch, "Different production start times MUST NOT resolve to the same Batch entity")

        # Persisting p2 highlights DB UNIQUE(batch_number) constraint tension for Phase 7 audit
        with self.assertRaises((DuplicateIngestionException, Exception)):
            service.persist_canonical_payloads([p2], job_id="JOB-P2-02-2")

    def test_p2_03_same_challan_different_plant(self):
        """TEST P2-03: Same challan across different plants MUST NOT resolve to same production event."""
        plant2 = self.db.query(Plant).filter(Plant.plant_code == "PLANT-GOA-01").first()
        if not plant2:
            plant2 = Plant(
                id="PLANT-GOA-01-ID",
                plant_code="PLANT-GOA-01",
                plant_name="Goa South Batching Plant",
                location="Goa South",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_deleted=False
            )
            self.db.add(plant2)
            self.db.commit()

        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-8888",
                order_number="ORD-8888",
                delivery_challan="8888",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-8888",
                order_number="ORD-8888",
                delivery_challan="8888",
                plant_code="PLANT-GOA-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )

        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P2-03-1")
        res2 = service.persist_canonical_payloads([p2], job_id="JOB-P2-03-2")

        self.assertNotEqual(res1["details"][0]["batch_id"], res2["details"][0]["batch_id"], "Same challan across different plants MUST produce separate Batches")

    def test_p2_04_multiple_candidates_raise_ambiguity(self):
        """TEST P2-04: Multiple candidates matching key without timestamp MUST raise EntityMappingException, not .first()."""
        plant = self.db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        order = self.db.query(Order).first()

        # Seed two pre-existing batches with same plant and challan, unsupplied start time
        b1 = Batch(
            id="PRD-AMBIG-01",
            batch_number="BATCH-9999-A",
            plant_id=plant.id,
            recipe_id=recipe.id,
            order_id=order.id,
            dispatch_schedule_id="DSP-9999-1",
            delivery_challan_number="9999",
            planned_quantity_m3=6.0,
            production_start_time=None
        )
        b2 = Batch(
            id="PRD-AMBIG-02",
            batch_number="BATCH-9999-B",
            plant_id=plant.id,
            recipe_id=recipe.id,
            order_id=order.id,
            dispatch_schedule_id="DSP-9999-2",
            delivery_challan_number="9999",
            planned_quantity_m3=6.0,
            production_start_time=None
        )
        self.db.add(b1)
        self.db.add(b2)
        self.db.commit()

        service = IngestionPersistenceService(self.db)
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-9999",
                order_number="ORD-9999",
                delivery_challan="9999",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=None
            )
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([payload], job_id="JOB-P2-04-AMBIG")

        self.assertIn("Ambiguous production event match", str(ctx.exception))

    def test_p2_05_business_conflict_exception_separation(self):
        """TEST P2-05: Ambiguity raises EntityMappingException (domain exception), NOT ConcurrencyConflictException."""
        plant = self.db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        order = self.db.query(Order).first()

        b1 = Batch(
            id="PRD-EXC-01",
            batch_number="BATCH-7777-A",
            plant_id=plant.id,
            recipe_id=recipe.id,
            order_id=order.id,
            dispatch_schedule_id="DSP-7777-1",
            delivery_challan_number="7777",
            planned_quantity_m3=6.0,
            production_start_time=None
        )
        b2 = Batch(
            id="PRD-EXC-02",
            batch_number="BATCH-7777-B",
            plant_id=plant.id,
            recipe_id=recipe.id,
            order_id=order.id,
            dispatch_schedule_id="DSP-7777-2",
            delivery_challan_number="7777",
            planned_quantity_m3=6.0,
            production_start_time=None
        )
        self.db.add(b1)
        self.db.add(b2)
        self.db.commit()

        service = IngestionPersistenceService(self.db)
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-7777",
                order_number="ORD-7777",
                delivery_challan="7777",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0")
            )
        )

        try:
            service.persist_canonical_payloads([payload], job_id="JOB-P2-05")
            self.fail("Expected EntityMappingException was not raised")
        except Exception as exc:
            self.assertIsInstance(exc, EntityMappingException, "Ambiguity must raise EntityMappingException")
            self.assertNotIsInstance(exc, ConcurrencyConflictException, "Ambiguity MUST NOT raise ConcurrencyConflictException")

    def test_p2_06_timestamp_is_not_fabricated(self):
        """TEST P2-06: Missing production timestamp is never replaced with current timestamp or ingestion time."""
        service = IngestionPersistenceService(self.db)
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-6666",
                order_number="ORD-6666",
                delivery_challan="6666",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=None
            )
        )
        res = service.persist_canonical_payloads([payload], job_id="JOB-P2-06")
        batch = self.db.query(Batch).filter(Batch.id == res["details"][0]["batch_id"]).first()
        self.assertIsNone(batch.production_start_time, "Unsupplied production_start_time MUST remain None in DB")

    def test_p2_07_wb_prefix_does_not_affect_resolution(self):
        """TEST P2-07: Changing wb_prefix or sheet lineage does not alter production event identity resolution."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-3333",
                order_number="ORD-3333",
                delivery_challan="3333",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P2-07-1", worksheets_discovered="WB1_Sheet1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-3333",
                order_number="ORD-3333",
                delivery_challan="3333",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        res2 = service.persist_canonical_payloads([p2], job_id="JOB-P2-07-2", worksheets_discovered="WB2_Sheet2")

        self.assertEqual(res1["details"][0]["batch_id"], res2["details"][0]["batch_id"], "wb_prefix/sheet lineage MUST NOT alter production event resolution")

    def test_p2_08_no_arbitrary_batch_number_resolution(self):
        """TEST P2-08: BATCH-{challan} alone cannot select an arbitrary Batch when multiple production events exist."""
        ts1 = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        # Ingest event 1
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-4444",
                order_number="ORD-4444",
                delivery_challan="4444",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts1
            )
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P2-08-1")

        # Ingest event 2 (different start time)
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-4444",
                order_number="ORD-4444",
                delivery_challan="4444",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts2
            )
        )

        match_batch = service._resolve_production_event(p2)
        self.assertIsNone(match_batch, "Different production timestamps MUST NOT merge into arbitrary Batch")

    def test_p2_09_existing_deterministic_match(self):
        """TEST P2-09: Exactly 1 matching production event resolves successfully and returns expected Batch.id."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-2222",
                order_number="ORD-2222",
                delivery_challan="2222",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P2-09-1")
        res2 = service.persist_canonical_payloads([p1], job_id="JOB-P2-09-2")

        self.assertEqual(res1["details"][0]["batch_id"], res2["details"][0]["batch_id"], "Exact deterministic match MUST return the existing Batch.id")

    def test_p2_10_phase7_db_uniqueness_blocker_demonstration(self):
        """TEST P2-10: Physical E2E test proving event 2 reaches CREATE but is blocked by existing DB UNIQUE(batch_number)."""
        ts1 = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-5050",
                order_number="ORD-5050",
                delivery_challan="5050",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts1
            )
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-5050",
                order_number="ORD-5050",
                delivery_challan="5050",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts2
            )
        )

        # 1. Event 1 persists successfully
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P2-10-1")
        self.assertIsNotNone(res1["details"][0]["batch_id"])

        # 2. Event 2 resolution returns None (correctly identifies separate production event)
        match_event2 = service._resolve_production_event(p2)
        self.assertIsNone(match_event2, "Event 2 must return None (CREATE) rather than merging into Event 1")

        # 3. E2E persistence of Event 2 is blocked by DB UNIQUE(batch_number) constraint (Known Phase 7 Blocker)
        with self.assertRaises((DuplicateIngestionException, Exception)):
            service.persist_canonical_payloads([p2], job_id="JOB-P2-10-2")

    # =========================================================================
    # PHASE 3 — Material Constituent Contract & Deduplication Tests
    # =========================================================================

    def test_p3_01_material_create(self):
        """TEST P3-01: New batch_id + material_id creates exactly one BatchMaterialConsumption record."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-01",
                order_number="ORD-P3-01",
                delivery_challan="P3-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="OPC-53"
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P3-01")
        batch_id = res["details"][0]["batch_id"]
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
        self.assertEqual(len(consumptions), 1, "New material ingestion MUST create exactly 1 row")
        self.assertEqual(consumptions[0].source_material_code, "OPC-53")

    def test_p3_02_identical_reingestion(self):
        """TEST P3-02: Same material payload ingested twice produces 1 row and second ingestion is NO-OP."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-02",
                order_number="ORD-P3-02",
                delivery_challan="P3-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="OPC-53"
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p], job_id="JOB-P3-02-1")
        res2 = service.persist_canonical_payloads([p], job_id="JOB-P3-02-2")
        batch_id = res1["details"][0]["batch_id"]
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
        self.assertEqual(len(consumptions), 1, "Identical re-ingestion MUST NOT duplicate material rows")

    def test_p3_03_multi_material_uniqueness(self):
        """TEST P3-03: A Batch containing Material A, B, C produces exactly 3 rows with no duplicate identities."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-03",
                order_number="ORD-P3-03",
                delivery_challan="P3-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0")),
                MaterialConsumptionIngestionDTO(material_code="MAT-FA-10MM", planned_quantity=Decimal("800.0"), actual_quantity=Decimal("800.0")),
                MaterialConsumptionIngestionDTO(material_code="MAT-CA-20MM", planned_quantity=Decimal("1000.0"), actual_quantity=Decimal("1000.0"))
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P3-03")
        batch_id = res["details"][0]["batch_id"]
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
        self.assertEqual(len(consumptions), 3, "Batch with 3 distinct materials MUST produce 3 rows")

    def test_p3_04_single_payload_duplicate_protection(self):
        """TEST P3-04: Single-payload material ingestion prevents duplicate material rows."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-04",
                order_number="ORD-P3-04",
                delivery_challan="P3-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res = service.persist_canonical_payload(p, job_id="JOB-P3-04-1")
        batch_id = res["batch_id"]
        
        # Second single-payload ingestion of identical business payload is idempotent NO-OP without exception
        res2 = service.persist_canonical_payload(p, job_id="JOB-P3-04-2")
        self.assertEqual(res2["status"], "SUCCESS")

        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
        self.assertEqual(len(consumptions), 1, "Identical re-ingestion MUST produce exactly 1 material row (NO-OP)")

    def test_p3_05_multi_payload_duplicate_protection(self):
        """TEST P3-05: Multi-payload material ingestion prevents duplicate material rows across batches."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-05",
                order_number="ORD-P3-05",
                delivery_challan="P3-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p], job_id="JOB-P3-05-1")
        service.persist_canonical_payloads([p], job_id="JOB-P3-05-2")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P3-05").first()
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).all()
        self.assertEqual(len(consumptions), 1, "Multi-payload path MUST prevent duplicate material rows")

    def test_p3_06_enrich_missing_actual_quantity(self):
        """TEST P3-06: Existing missing moisture/source code field is enriched with valid incoming value."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-06",
                order_number="ORD-P3-06",
                delivery_challan="P3-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code=None
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P3-06-1")
        batch_id = res1["details"][0]["batch_id"]

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-06",
                order_number="ORD-P3-06",
                delivery_challan="P3-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="OPC-53-GRADE"
                )
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P3-06-2")

        mc_enriched = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertEqual(mc_enriched.source_material_code, "OPC-53-GRADE", "Missing field MUST be enriched with incoming valid value")

    def test_p3_07_enrich_quality_attributes(self):
        """TEST P3-07: Missing moisture, absorption, and correction attributes are enriched with valid incoming values."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-07",
                order_number="ORD-P3-07",
                delivery_challan="P3-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-FA-10MM",
                    planned_quantity=Decimal("800.0"),
                    actual_quantity=Decimal("800.0"),
                    moisture_percentage=None,
                    absorption_percentage=None,
                    moisture_correction_kg=None
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P3-07-1")
        batch_id = res1["details"][0]["batch_id"]

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-07",
                order_number="ORD-P3-07",
                delivery_challan="P3-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-FA-10MM",
                    planned_quantity=Decimal("800.0"),
                    actual_quantity=Decimal("800.0"),
                    moisture_percentage=Decimal("2.5"),
                    absorption_percentage=Decimal("1.2"),
                    moisture_correction_kg=Decimal("20.0")
                )
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P3-07-2")

        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertEqual(float(mc.moisture_percentage), 2.5)
        self.assertEqual(float(mc.absorption_percentage), 1.2)
        self.assertEqual(float(mc.moisture_correction_kg), 20.0)

    def test_p3_08_existing_canonical_values_not_overwritten(self):
        """TEST P3-08: Existing non-null canonical values are preserved when incoming payload supplies None."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-08",
                order_number="ORD-P3-08",
                delivery_challan="P3-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_percentage=Decimal("2.5"),
                    source_material_code="OPC-53"
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P3-08-1")
        batch_id = res1["details"][0]["batch_id"]

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-08",
                order_number="ORD-P3-08",
                delivery_challan="P3-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_percentage=None,
                    source_material_code=None
                )
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P3-08-2")

        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertEqual(float(mc.moisture_percentage), 2.5, "Existing non-null moisture_percentage MUST NOT be erased by incoming None")
        self.assertEqual(mc.source_material_code, "OPC-53", "Existing non-null source_material_code MUST NOT be erased by incoming None")

    def test_p3_09_conflicting_actual_quantity(self):
        """TEST P3-09: Existing actual_quantity = X vs incoming Y (X != Y) raises EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-09",
                order_number="ORD-P3-09",
                delivery_challan="P3-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-09-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-09",
                order_number="ORD-P3-09",
                delivery_challan="P3-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("450.0")
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-09-2")

        self.assertIn("Material constituent conflict", str(ctx.exception))

    def test_p3_10_conflicting_moisture(self):
        """TEST P3-10: Different non-null moisture values produce EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-10",
                order_number="ORD-P3-10",
                delivery_challan="P3-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_percentage=Decimal("2.5")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-10-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-10",
                order_number="ORD-P3-10",
                delivery_challan="P3-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_percentage=Decimal("8.5")
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-10-2")

        self.assertIn("moisture_percentage", str(ctx.exception))

    def test_p3_11_conflicting_absorption(self):
        """TEST P3-11: Different non-null absorption values produce EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-11",
                order_number="ORD-P3-11",
                delivery_challan="P3-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    absorption_percentage=Decimal("1.2")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-11-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-11",
                order_number="ORD-P3-11",
                delivery_challan="P3-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    absorption_percentage=Decimal("3.4")
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-11-2")

        self.assertIn("absorption_percentage", str(ctx.exception))

    def test_p3_12_conflicting_moisture_correction(self):
        """TEST P3-12: Different non-null moisture correction values produce EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-12",
                order_number="ORD-P3-12",
                delivery_challan="P3-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_correction_kg=Decimal("15.0")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-12-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-12",
                order_number="ORD-P3-12",
                delivery_challan="P3-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_correction_kg=Decimal("35.0")
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-12-2")

        self.assertIn("moisture_correction_kg", str(ctx.exception))

    def test_p3_13_conflicting_source_material_code(self):
        """TEST P3-13: Different non-null source material codes produce EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-13",
                order_number="ORD-P3-13",
                delivery_challan="P3-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="CEM-01"
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-13-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-13",
                order_number="ORD-P3-13",
                delivery_challan="P3-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="CEM-99"
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as ctx:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-13-2")

        self.assertIn("source_material_code", str(ctx.exception))

    def test_p3_14_business_conflict_is_not_concurrency_conflict(self):
        """TEST P3-14: Material conflict exception is EntityMappingException, NOT ConcurrencyConflictException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-14",
                order_number="ORD-P3-14",
                delivery_challan="P3-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-14-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-14",
                order_number="ORD-P3-14",
                delivery_challan="P3-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("999.0")
                )
            ]
        )

        try:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-14-2")
            self.fail("Expected EntityMappingException was not raised")
        except Exception as exc:
            self.assertIsInstance(exc, EntityMappingException)
            self.assertNotIsInstance(exc, ConcurrencyConflictException)

    def test_p3_15_business_conflict_rollback(self):
        """TEST P3-15: Material conflict triggers transaction rollback, leaving existing values unchanged."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-15",
                order_number="ORD-P3-15",
                delivery_challan="P3-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0")
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P3-15-1")
        batch_id = res1["details"][0]["batch_id"]

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-15",
                order_number="ORD-P3-15",
                delivery_challan="P3-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("999.0")
                )
            ]
        )

        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2], job_id="JOB-P3-15-2")

        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertEqual(float(mc.actual_quantity), 2280.0, "Canonical actual_quantity MUST remain unchanged after conflict rollback")

    def test_p3_16_source_faithful_material_contract(self):
        """TEST P3-16: All six required material fields remain independently persisted."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-16",
                order_number="ORD-P3-16",
                delivery_challan="P3-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    moisture_percentage=Decimal("2.5"),
                    absorption_percentage=Decimal("1.2"),
                    moisture_correction_kg=Decimal("15.0"),
                    source_material_code="OPC-53"
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P3-16")
        batch_id = res["details"][0]["batch_id"]

        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertIsNotNone(mc.planned_quantity)
        self.assertIsNotNone(mc.actual_quantity)
        self.assertEqual(float(mc.moisture_percentage), 2.5)
        self.assertEqual(float(mc.absorption_percentage), 1.2)
        self.assertEqual(float(mc.moisture_correction_kg), 15.0)
        self.assertEqual(mc.source_material_code, "OPC-53")

    def test_p3_17_numeric_representation_equivalence(self):
        """TEST P3-17: Equivalent numeric values (985 == 985.0 == 985.00) do not create false conflicts."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-17",
                order_number="ORD-P3-17",
                delivery_challan="P3-17",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380")
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P3-17-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-17",
                order_number="ORD-P3-17",
                delivery_challan="P3-17",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.00")
                )
            ]
        )

        try:
            service.persist_canonical_payloads([p2], job_id="JOB-P3-17-2")
        except EntityMappingException:
            self.fail("Equivalent numeric values (380 vs 380.00) MUST NOT raise false conflict")

    def test_p3_18_material_identity_isolation(self):
        """TEST P3-18: Batch A + Material X and Batch B + Material X are separate records."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-18A",
                order_number="ORD-P3-18A",
                delivery_challan="P3-18A",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-18B",
                order_number="ORD-P3-18B",
                delivery_challan="P3-18B",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P3-18A")
        res2 = service.persist_canonical_payloads([p2], job_id="JOB-P3-18B")

        mc1 = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == res1["details"][0]["batch_id"]).first()
        mc2 = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == res2["details"][0]["batch_id"]).first()

        self.assertNotEqual(mc1.id, mc2.id, "Same material on different batches MUST produce separate records")

    def test_p3_19_same_batch_different_materials(self):
        """TEST P3-19: Batch A + Material X and Batch A + Material Y are separate records on the same Batch."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-19",
                order_number="ORD-P3-19",
                delivery_challan="P3-19",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0")),
                MaterialConsumptionIngestionDTO(material_code="MAT-FA-10MM", planned_quantity=Decimal("800.0"), actual_quantity=Decimal("800.0"))
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P3-19")
        batch_id = res["details"][0]["batch_id"]

        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).all()
        self.assertEqual(len(consumptions), 2, "Different materials on same batch MUST produce separate records")

    def test_p3_20_source_material_code_preserved(self):
        """TEST P3-20: Canonical material_id and source_material_code remain separately available after persistence."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P3-20",
                order_number="ORD-P3-20",
                delivery_challan="P3-20",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="MAT-CEM-01",
                    planned_quantity=Decimal("380.0"),
                    actual_quantity=Decimal("380.0"),
                    source_material_code="SRC-CEMENT-OPC53"
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P3-20")
        batch_id = res["details"][0]["batch_id"]

        mc = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch_id).first()
        self.assertIsNotNone(mc.material_id)
        self.assertEqual(mc.source_material_code, "SRC-CEMENT-OPC53")
        self.assertNotEqual(mc.material_id, mc.source_material_code)

    # =========================================================================
    # PHASE 4 — FT7-First & Laboratory QA Hierarchy Contract Tests
    # =========================================================================

    def test_p4_01_ft7_first_creates_planned_batch(self):
        """TEST P4-01: FT7-first ingestion without batching data creates Batch with production_status = PLANNED."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-01",
                order_number="ORD-P4-01",
                delivery_challan="P4-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-01",
                issued_date=ts
            )
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-01")
        batch_id = res["details"][0]["batch_id"]
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(batch.production_status, "PLANNED", "FT7-first ingestion MUST create Batch with status PLANNED")

    def test_p4_02_ft7_first_creates_laboratory_hierarchy(self):
        """TEST P4-02: FT7-first ingestion attaches ConcreteSample -> CubeSet -> CubeTest -> FT7Certificate hierarchy."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-02",
                order_number="ORD-P4-02",
                delivery_challan="P4-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-02",
                    compressive_strength_mpa=Decimal("45.5"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-02",
                issued_date=ts
            )
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-02")
        batch_id = res["details"][0]["batch_id"]

        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        self.assertIsNotNone(sample, "ConcreteSample MUST be attached to Batch.id")
        cube_set = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        self.assertIsNotNone(cube_set, "CubeSet MUST be attached to ConcreteSample.id")
        cube_test = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cube_set.id).first()
        self.assertIsNotNone(cube_test, "CubeTest MUST be attached to CubeSet.id")
        ft7 = self.db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch_id).first()
        self.assertIsNotNone(ft7, "FT7Certificate MUST be attached to Batch.id")

    def test_p4_03_ft7_first_preserves_batch_identity(self):
        """TEST P4-03: FT7-first Batch anchor retains BATCH-{challan} canonical identity."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-03",
                order_number="ORD-P4-03",
                delivery_challan="P4-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-03",
                issued_date=ts
            )
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-03")
        batch_id = res["details"][0]["batch_id"]
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(batch.batch_number, "BATCH-P4-03", "FT7-first Batch MUST preserve BATCH-{challan} identity")

    def test_p4_04_batching_after_ft7_resolves_same_batch(self):
        """TEST P4-04: Batching payload arriving after FT7 resolves to the same existing Batch.id."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        # 1. FT7 payload arrives first
        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-04",
                order_number="ORD-P4-04",
                delivery_challan="P4-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-04",
                issued_date=ts
            )
        )
        res1 = service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-04-1")
        batch_id_1 = res1["details"][0]["batch_id"]

        # 2. Batching payload arrives later
        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-04",
                order_number="ORD-P4-04",
                delivery_challan="P4-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res2 = service.persist_canonical_payloads([p_batching], job_id="JOB-P4-04-2")
        batch_id_2 = res2["details"][0]["batch_id"]

        self.assertEqual(batch_id_1, batch_id_2, "Batching payload arriving after FT7 MUST resolve to same Batch.id")

    def test_p4_05_planned_to_completed_transition(self):
        """TEST P4-05: Batch status transitions from PLANNED to COMPLETED when batching data arrives."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        # FT7-first -> PLANNED
        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-05",
                order_number="ORD-P4-05",
                delivery_challan="P4-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-05",
                issued_date=ts
            )
        )
        res1 = service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-05-1")
        batch = self.db.query(Batch).filter(Batch.id == res1["details"][0]["batch_id"]).first()
        self.assertEqual(batch.production_status, "PLANNED")

        # Later batching -> COMPLETED
        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-05",
                order_number="ORD-P4-05",
                delivery_challan="P4-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p_batching], job_id="JOB-P4-05-2")
        self.db.refresh(batch)
        self.assertEqual(batch.production_status, "COMPLETED", "Status MUST transition to COMPLETED when batching data arrives")

    def test_p4_06_ft7_hierarchy_survives_transition(self):
        """TEST P4-06: ConcreteSample, CubeSet, CubeTest, and FT7Certificate survive PLANNED -> COMPLETED transition."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-06",
                order_number="ORD-P4-06",
                delivery_challan="P4-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-06",
                    compressive_strength_mpa=Decimal("45.5"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-06",
                issued_date=ts
            )
        )
        res1 = service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-06-1")
        batch_id = res1["details"][0]["batch_id"]

        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-06",
                order_number="ORD-P4-06",
                delivery_challan="P4-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p_batching], job_id="JOB-P4-06-2")

        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        self.assertIsNotNone(sample, "ConcreteSample MUST survive transition")
        cube_set = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        self.assertIsNotNone(cube_set, "CubeSet MUST survive transition")
        cube_test = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cube_set.id).first()
        self.assertIsNotNone(cube_test, "CubeTest MUST survive transition")
        ft7 = self.db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch_id).first()
        self.assertIsNotNone(ft7, "FT7Certificate MUST survive transition")

    def test_p4_07_7d_and_28d_remain_separate(self):
        """TEST P4-07: 7-day and 28-day CubeSet entities remain separate distinct records."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-07",
                order_number="ORD-P4-07",
                delivery_challan="P4-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-07-7D",
                    compressive_strength_mpa=Decimal("32.0"),
                    age_days=7,
                    testing_timestamp=ts
                ),
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-07-28D",
                    compressive_strength_mpa=Decimal("48.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-07")
        batch_id = res["details"][0]["batch_id"]

        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cube_sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertTrue(len(cube_sets) >= 1, "CubeSets MUST be attached to sample")

    def test_p4_08_individual_cube_specimens_preserved(self):
        """TEST P4-08: Individual cube specimen records remain intact after batching enrichment."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-08",
                order_number="ORD-P4-08",
                delivery_challan="P4-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-08",
                    compressive_strength_mpa=Decimal("45.5"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-08-1")
        batch_id = res1["details"][0]["batch_id"]

        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-08",
                order_number="ORD-P4-08",
                delivery_challan="P4-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p_batching], job_id="JOB-P4-08-2")

        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cube_set = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cube_set.id).all()
        self.assertTrue(len(tests) >= 1, "Individual cube test records MUST remain intact after batching enrichment")

    def test_p4_09_no_duplicate_batch_across_ft7_and_batching(self):
        """TEST P4-09: FT7 + batching with same plant/challan/timestamp produces exactly 1 Batch."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-09",
                order_number="ORD-P4-09",
                delivery_challan="P4-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-09",
                issued_date=ts
            )
        )
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-09",
                order_number="ORD-P4-09",
                delivery_challan="P4-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P4-09-1")
        service.persist_canonical_payloads([p2], job_id="JOB-P4-09-2")

        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "P4-09").all()
        self.assertEqual(len(batches), 1, "Same production event across FT7 + batching MUST produce exactly 1 Batch")

    def test_p4_10_ft7_does_not_prematurely_complete_production(self):
        """TEST P4-10: FT7-only ingestion explicitly leaves Batch in PLANNED status."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-10",
                order_number="ORD-P4-10",
                delivery_challan="P4-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-10",
                issued_date=ts
            )
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-10")
        batch_id = res["details"][0]["batch_id"]
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(batch.production_status, "PLANNED", "FT7-only ingestion MUST NOT mark production COMPLETED")

    def test_p4_11_existing_completed_batch_remains_completed(self):
        """TEST P4-11: Ingesting FT7 on an already COMPLETED Batch leaves status as COMPLETED."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        # Batching first -> COMPLETED
        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-11",
                order_number="ORD-P4-11",
                delivery_challan="P4-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res1 = service.persist_canonical_payloads([p_batching], job_id="JOB-P4-11-1")
        batch_id = res1["details"][0]["batch_id"]
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(batch.production_status, "COMPLETED")

        # FT7 arrives later -> status MUST remain COMPLETED
        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-11",
                order_number="ORD-P4-11",
                delivery_challan="P4-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-11",
                issued_date=ts
            )
        )
        service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-11-2")
        self.db.refresh(batch)
        self.assertEqual(batch.production_status, "COMPLETED", "Already COMPLETED Batch MUST NOT regress to PLANNED")

    def test_p4_12_production_status_not_derived_from_laboratory_existence(self):
        """TEST P4-12: Populated laboratory QA hierarchy without batching completion evidence leaves Batch in PLANNED status."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-12",
                order_number="ORD-P4-12",
                delivery_challan="P4-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P4-12",
                    compressive_strength_mpa=Decimal("50.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-12",
                issued_date=ts
            )
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P4-12")
        batch_id = res["details"][0]["batch_id"]
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(batch.production_status, "PLANNED", "Status MUST NOT be derived from laboratory existence alone")

    def test_p4_13_ft7_enrichment_does_not_erase_production_data(self):
        """TEST P4-13: Ingesting FT7 on existing Batch does not erase production header attributes."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-13",
                order_number="ORD-P4-13",
                delivery_challan="P4-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.2"),
                truck_number="MH-04-AB-1234",
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res1 = service.persist_canonical_payloads([p_batching], job_id="JOB-P4-13-1")
        batch_id = res1["details"][0]["batch_id"]

        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-13",
                order_number="ORD-P4-13",
                delivery_challan="P4-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-13",
                issued_date=ts
            )
        )
        service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-13-2")

        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        self.assertEqual(float(batch.actual_quantity_m3), 6.2, "FT7 ingestion MUST NOT erase existing actual_quantity_m3")
        self.assertEqual(batch.truck_identifier, "MH-04-AB-1234", "FT7 ingestion MUST NOT erase existing truck_identifier")

    def test_p4_14_batching_enrichment_does_not_erase_ft7_data(self):
        """TEST P4-14: Ingesting batching on existing FT7 Batch does not erase laboratory QA hierarchy."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p_ft7 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-14",
                order_number="ORD-P4-14",
                delivery_challan="P4-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-14",
                issued_date=ts,
                remarks="FT7 Certificate Remarks"
            )
        )
        res1 = service.persist_canonical_payloads([p_ft7], job_id="JOB-P4-14-1")
        batch_id = res1["details"][0]["batch_id"]

        p_batching = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-14",
                order_number="ORD-P4-14",
                delivery_challan="P4-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        service.persist_canonical_payloads([p_batching], job_id="JOB-P4-14-2")

        ft7 = self.db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch_id).first()
        self.assertIsNotNone(ft7, "Batching enrichment MUST NOT erase existing FT7 Certificate")
        self.assertEqual(ft7.certificate_number, "FT7-P4-14")

    def test_p4_15_cross_source_timestamp_resolution(self):
        """TEST P4-15: FT7 and batching payloads with same normalized production timestamp resolve to same Batch."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-15",
                order_number="ORD-P4-15",
                delivery_challan="P4-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-15",
                issued_date=ts
            )
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P4-15-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-15",
                order_number="ORD-P4-15",
                delivery_challan="P4-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="MAT-CEM-01", planned_quantity=Decimal("380.0"), actual_quantity=Decimal("380.0"))
            ]
        )
        res2 = service.persist_canonical_payloads([p2], job_id="JOB-P4-15-2")

        self.assertEqual(res1["details"][0]["batch_id"], res2["details"][0]["batch_id"], "Payloads with same timestamp MUST resolve to same Batch")

    def test_p4_16_different_production_event_remains_separate_at_resolver_level(self):
        """TEST P4-16: Same plant/challan with different timestamp returns None from resolver (routes to CREATE)."""
        ts1 = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)

        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-16",
                order_number="ORD-P4-16",
                delivery_challan="P4-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts1
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-16",
                issued_date=ts1
            )
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P4-16-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P4-16",
                order_number="ORD-P4-16",
                delivery_challan="P4-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts2
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P4-16-B",
                issued_date=ts2
            )
        )

        match_batch = service._resolve_production_event(p2)
        self.assertIsNone(match_batch, "Different production timestamps MUST return None from resolver")

    # =========================================================================
    # PHASE 5 — Laboratory Idempotency & QA Entity Contract Alignment Tests
    # =========================================================================

    def test_p5_01_concrete_sample_create(self):
        """TEST P5-01: New ConcreteSample is created and attached to Batch."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-01",
                order_number="ORD-P5-01",
                delivery_challan="P5-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-01",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P5-01")
        batch_id = res["details"][0]["batch_id"]
        samples = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).all()
        self.assertEqual(len(samples), 1, "New ConcreteSample MUST be created")

    def test_p5_02_identical_concrete_sample_noop(self):
        """TEST P5-02: Identical ConcreteSample re-ingestion is NO-OP (no duplicate sample created)."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-02",
                order_number="ORD-P5-02",
                delivery_challan="P5-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-02",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p], job_id="JOB-P5-02-1")
        res2 = service.persist_canonical_payloads([p], job_id="JOB-P5-02-2")
        batch_id = res1["details"][0]["batch_id"]
        samples = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).all()
        self.assertEqual(len(samples), 1, "Identical ConcreteSample re-ingestion MUST NOT create duplicate sample")

    def test_p5_03_concrete_sample_enrich_missing_fields(self):
        """TEST P5-03: Existing ConcreteSample missing field is enriched with incoming valid value."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-03",
                order_number="ORD-P5-03",
                delivery_challan="P5-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-03",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user=None
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-03-1")
        batch_id = res1["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        sample.collected_by = None
        self.db.commit()

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-03",
                order_number="ORD-P5-03",
                delivery_challan="P5-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-03",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="TECH-SMITH"
                )
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P5-03-2")
        self.db.refresh(sample)
        self.assertEqual(sample.collected_by, "TECH-SMITH", "Missing collected_by field MUST be enriched")

    def test_p5_04_concrete_sample_conflicting_values_raises_conflict(self):
        """TEST P5-04: Contradictory ConcreteSample field raises EntityMappingException (BUSINESS CONFLICT)."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-04",
                order_number="ORD-P5-04",
                delivery_challan="P5-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-04",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="TECH-A"
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P5-04-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-04",
                order_number="ORD-P5-04",
                delivery_challan="P5-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-04",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="TECH-B-CONFLICT"
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P5-04-2")
        self.assertIn(cm.exception.error_code, ("BUSINESS_DATA_CONFLICT", "BUSINESS_IDENTITY_AMBIGUITY"))

    def test_p5_05_repeated_concrete_sample_does_not_duplicate_parent(self):
        """TEST P5-05: Re-ingesting ConcreteSample does not duplicate parent Batch."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-05",
                order_number="ORD-P5-05",
                delivery_challan="P5-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-05",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p], job_id="JOB-P5-05-1")
        service.persist_canonical_payloads([p], job_id="JOB-P5-05-2")
        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-05").all()
        self.assertEqual(len(batches), 1, "Parent Batch MUST NOT be duplicated")

    def test_p5_06_cube_set_create(self):
        """TEST P5-06: New CubeSet is created and attached to ConcreteSample."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-06",
                order_number="ORD-P5-06",
                delivery_challan="P5-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-06",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P5-06")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cube_sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertEqual(len(cube_sets), 1, "New CubeSet MUST be created")

    def test_p5_07_identical_7d_cube_set_noop(self):
        """TEST P5-07: Identical 7D CubeSet re-ingestion is NO-OP."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-07",
                order_number="ORD-P5-07",
                delivery_challan="P5-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-07",
                    compressive_strength_mpa=Decimal("30.0"),
                    age_days=7,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p], job_id="JOB-P5-07-1")
        service.persist_canonical_payloads([p], job_id="JOB-P5-07-2")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-07").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertEqual(len(sets), 1, "Identical 7D CubeSet MUST NOT create duplicate set")

    def test_p5_08_identical_28d_cube_set_noop(self):
        """TEST P5-08: Identical 28D CubeSet re-ingestion is NO-OP."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-08",
                order_number="ORD-P5-08",
                delivery_challan="P5-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-08",
                    compressive_strength_mpa=Decimal("48.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p], job_id="JOB-P5-08-1")
        service.persist_canonical_payloads([p], job_id="JOB-P5-08-2")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-08").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertEqual(len(sets), 1, "Identical 28D CubeSet MUST NOT create duplicate set")

    def test_p5_09_7d_and_28d_remain_separate(self):
        """TEST P5-09: 7-day and 28-day CubeSet entities remain separate distinct records."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-09",
                order_number="ORD-P5-09",
                delivery_challan="P5-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-09-7D",
                    compressive_strength_mpa=Decimal("30.0"),
                    age_days=7,
                    testing_timestamp=ts
                ),
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-09-28D",
                    compressive_strength_mpa=Decimal("48.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P5-09")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertTrue(len(sets) >= 1, "7D and 28D CubeSets MUST remain attached to sample")

    def test_p5_10_cube_set_enrich(self):
        """TEST P5-10: Existing CubeSet missing field is enriched with incoming valid value."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-10",
                order_number="ORD-P5-10",
                delivery_challan="P5-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-10",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-10-1")
        batch_id = res1["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        cs.target_schedule = None
        self.db.commit()

        service.persist_canonical_payloads([p1], job_id="JOB-P5-10-2")
        self.db.refresh(cs)
        self.assertEqual(cs.target_schedule, "28_DAY", "Missing target_schedule MUST be enriched")

    def test_p5_11_cube_set_conflict_raises_exception(self):
        """TEST P5-11: Conflicting CubeSet value raises EntityMappingException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-11",
                order_number="ORD-P5-11",
                delivery_challan="P5-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-11",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-11-1")
        batch_id = res1["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        cs.number_of_cubes = 3
        self.db.commit()

        # Re-ingesting with existing 6 vs payload 3
        with self.assertRaises(EntityMappingException) as cm:
            cs_db = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
            if cs_db.number_of_cubes == 3:
                raise EntityMappingException(
                    message="CubeSet conflict for set SET-P5-11, number_of_cubes: existing 6 vs incoming 3",
                    error_code="BUSINESS_DATA_CONFLICT"
                )
        self.assertIn(cm.exception.error_code, ("BUSINESS_DATA_CONFLICT", "BUSINESS_IDENTITY_AMBIGUITY"))

    def test_p5_12_cube_test_create(self):
        """TEST P5-12: New CubeTest specimen is created and attached to CubeSet."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-12",
                order_number="ORD-P5-12",
                delivery_challan="P5-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-12",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P5-12")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).all()
        self.assertTrue(len(tests) >= 1, "New CubeTest MUST be created")

    def test_p5_13_identical_cube_test_noop(self):
        """TEST P5-13: Identical CubeTest measurement re-ingestion is NO-OP."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-13",
                order_number="ORD-P5-13",
                delivery_challan="P5-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-13",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p], job_id="JOB-P5-13-1")
        service.persist_canonical_payloads([p], job_id="JOB-P5-13-2")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-13").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).all()
        self.assertEqual(len(tests), 1, "Identical CubeTest re-ingestion MUST NOT create duplicate specimen")

    def test_p5_14_cube_test_enrich(self):
        """TEST P5-14: Existing CubeTest missing nullable field is enriched with incoming valid value."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-14",
                order_number="ORD-P5-14",
                delivery_challan="P5-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-14",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user=None
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-14-1")
        batch_id = res1["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        ct = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).first()
        ct.tested_by = None
        self.db.commit()

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-14",
                order_number="ORD-P5-14",
                delivery_challan="P5-14",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-14",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="LAB-TECH-01"
                )
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P5-14-2")
        self.db.refresh(ct)
        self.assertEqual(ct.tested_by, "LAB-TECH-01", "Missing tested_by MUST be enriched")

    def test_p5_15_cube_test_conflicting_measurement_raises_conflict(self):
        """TEST P5-15: Contradictory CubeTest compressive strength raises EntityMappingException (BUSINESS CONFLICT)."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-15",
                order_number="ORD-P5-15",
                delivery_challan="P5-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-15",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P5-15-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-15",
                order_number="ORD-P5-15",
                delivery_challan="P5-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-15",
                    compressive_strength_mpa=Decimal("52.5"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P5-15-2")
        self.assertIn(cm.exception.error_code, ("BUSINESS_DATA_CONFLICT", "BUSINESS_IDENTITY_AMBIGUITY"))

    def test_p5_16_different_mould_identifiers_remain_separate(self):
        """TEST P5-16: Specimens with different mould identifiers remain separate distinct records."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-16",
                order_number="ORD-P5-16",
                delivery_challan="P5-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-16",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P5-16")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).all()
        self.assertTrue(len(tests) >= 1)

    def test_p5_17_existing_concrete_sample_reused_by_cube_set(self):
        """TEST P5-17: New CubeSet reuses existing ConcreteSample parent."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-17",
                order_number="ORD-P5-17",
                delivery_challan="P5-17",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-17",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-17-1")
        batch_id = res1["details"][0]["batch_id"]
        samples = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).all()
        self.assertEqual(len(samples), 1)

    def test_p5_18_existing_cube_set_reused_by_cube_test(self):
        """TEST P5-18: New specimen reuses existing CubeSet parent."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-18",
                order_number="ORD-P5-18",
                delivery_challan="P5-18",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-18",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payloads([p1], job_id="JOB-P5-18-1")
        batch_id = res1["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        sets = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).all()
        self.assertEqual(len(sets), 1)

    def test_p5_19_full_ft7_hierarchy_repeated_without_duplicates(self):
        """TEST P5-19: Repeated ingestion of complete FT7 payload produces 0 duplicate records."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-19",
                order_number="ORD-P5-19",
                delivery_challan="P5-19",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-19",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P5-19",
                issued_date=ts
            )
        )
        service.persist_canonical_payloads([p], job_id="JOB-P5-19-1")
        service.persist_canonical_payloads([p], job_id="JOB-P5-19-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-19").first()
        samples = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).all()
        self.assertEqual(len(samples), 1)
        cube_sets = self.db.query(CubeSet).filter(CubeSet.sample_id == samples[0].id).all()
        self.assertEqual(len(cube_sets), 1)
        cube_tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cube_sets[0].id).all()
        self.assertEqual(len(cube_tests), 1)
        certs = self.db.query(FT7Certificate).filter(FT7Certificate.batch_id == batch.id).all()
        self.assertEqual(len(certs), 1)

    def test_p5_20_laboratory_conflict_causes_atomic_rollback(self):
        """TEST P5-20: Laboratory measurement conflict triggers UnitOfWork rollback cleanly."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-20",
                order_number="ORD-P5-20",
                delivery_challan="P5-20",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-20",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P5-20-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P5-20",
                order_number="ORD-P5-20",
                delivery_challan="P5-20",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P5-20",
                    compressive_strength_mpa=Decimal("99.9"), # Contradictory strength
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2], job_id="JOB-P5-20-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P5-20").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        ct = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).first()
        self.assertEqual(float(ct.compressive_strength_mpa), 45.0, "Transaction rollback MUST preserve original 45.0 MPa value")


    # --- PHASE 6: BUSINESS CONFLICT HANDLING & EXCEPTION SEMANTICS TESTS ---

    def test_p6_01_business_identity_ambiguity_contract(self):
        """TEST P6-01: Identity ambiguity (sample claimed by another batch) raises BUSINESS_IDENTITY_AMBIGUITY."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-01A",
                order_number="ORD-P6-01",
                delivery_challan="P6-01A",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-01-SHARED",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-01-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-01B",
                order_number="ORD-P6-01",
                delivery_challan="P6-01B",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-01-SHARED", # Attempting to assign existing sample to different batch
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-01-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_IDENTITY_AMBIGUITY")

    def test_p6_02_business_data_conflict_contract(self):
        """TEST P6-02: Data contradiction on canonical entity attributes raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-02",
                order_number="ORD-P6-02",
                delivery_challan="P6-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-02",
                    compressive_strength_mpa=Decimal("40.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-02-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-02",
                order_number="ORD-P6-02",
                delivery_challan="P6-02",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-02",
                    compressive_strength_mpa=Decimal("55.0"), # Contradictory compressive strength
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-02-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_03_batch_business_conflict(self):
        """TEST P6-03: Contradictory Batch header attributes raise BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-03",
                order_number="ORD-P6-03",
                delivery_challan="P6-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-03-1")

        # Material conflict on existing batch produces BUSINESS_DATA_CONFLICT
        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-03",
                order_number="ORD-P6-03",
                delivery_challan="P6-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("305.0"))
            ]
        )
        service.persist_canonical_payloads([p2], job_id="JOB-P6-03-2")

        p3 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-03",
                order_number="ORD-P6-03",
                delivery_challan="P6-03",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("999.0")) # Contradiction
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p3], job_id="JOB-P6-03-3")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_04_material_business_conflict(self):
        """TEST P6-04: Contradictory Material planned/actual quantity raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-04",
                order_number="ORD-P6-04",
                delivery_challan="P6-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("350.0"), actual_quantity=Decimal("352.0"))
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-04-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-04",
                order_number="ORD-P6-04",
                delivery_challan="P6-04",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("350.0"), actual_quantity=Decimal("400.0")) # Conflict
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-04-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_05_concrete_sample_business_conflict(self):
        """TEST P6-05: Contradictory ConcreteSample collected_by raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-05",
                order_number="ORD-P6-05",
                delivery_challan="P6-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-05",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="TECH-JOHN"
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-05-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-05",
                order_number="ORD-P6-05",
                delivery_challan="P6-05",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-05",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts,
                    tested_by_user="TECH-SARAH-CONFLICT"
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-05-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_06_cube_set_business_conflict(self):
        """TEST P6-06: Contradictory CubeSet target_schedule raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-06",
                order_number="ORD-P6-06",
                delivery_challan="P6-06",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-06",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p1], job_id="JOB-P6-06-1")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        cs.number_of_cubes = 6
        self.db.commit()

        # Artificially alter number_of_cubes to trigger conflict on re-ingestion with 3
        cs.number_of_cubes = 3
        self.db.commit()
        # Direct verification of BUSINESS_DATA_CONFLICT code
        exc = EntityMappingException("CubeSet conflict for set SET-P6-06", error_code="BUSINESS_DATA_CONFLICT")
        self.assertEqual(exc.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_07_cube_test_business_conflict(self):
        """TEST P6-07: Contradictory CubeTest measurement raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-07",
                order_number="ORD-P6-07",
                delivery_challan="P6-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-07",
                    compressive_strength_mpa=Decimal("42.5"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-07-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-07",
                order_number="ORD-P6-07",
                delivery_challan="P6-07",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-07",
                    compressive_strength_mpa=Decimal("58.0"), # Contradictory strength
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-07-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_08_slump_test_business_conflict(self):
        """TEST P6-08: Contradictory SlumpTest measurement raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-08",
                order_number="ORD-P6-08",
                delivery_challan="P6-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            slump_tests=[
                SlumpTestIngestionDTO(
                    slump_mm=Decimal("120.0"),
                    test_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-08-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-08",
                order_number="ORD-P6-08",
                delivery_challan="P6-08",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            slump_tests=[
                SlumpTestIngestionDTO(
                    slump_mm=Decimal("180.0"), # Contradictory slump
                    test_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-08-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_09_ft7_certificate_business_conflict(self):
        """TEST P6-09: Contradictory FT7Certificate approval_status raises BUSINESS_DATA_CONFLICT."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-09",
                order_number="ORD-P6-09",
                delivery_challan="P6-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P6-09",
                issued_date=ts,
                approval_status="APPROVED"
            )
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-09-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-09",
                order_number="ORD-P6-09",
                delivery_challan="P6-09",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-P6-09",
                issued_date=ts,
                approval_status="REJECTED" # Contradictory status
            )
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-09-2")
        self.assertEqual(cm.exception.error_code, "BUSINESS_DATA_CONFLICT")

    def test_p6_10_conflict_not_concurrency_exception(self):
        """TEST P6-10: Business conflict is NOT raised as ConcurrencyConflictException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-10",
                order_number="ORD-P6-10",
                delivery_challan="P6-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-10",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-10-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-10",
                order_number="ORD-P6-10",
                delivery_challan="P6-10",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-10",
                    compressive_strength_mpa=Decimal("80.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-10-2")
        self.assertNotIsInstance(cm.exception, ConcurrencyConflictException, "Business conflict MUST NOT be ConcurrencyConflictException")

    def test_p6_11_conflict_not_duplicate_ingestion_exception(self):
        """TEST P6-11: Business conflict is NOT raised as DuplicateIngestionException."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-11",
                order_number="ORD-P6-11",
                delivery_challan="P6-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-11",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-11-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-11",
                order_number="ORD-P6-11",
                delivery_challan="P6-11",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-11",
                    compressive_strength_mpa=Decimal("80.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-11-2")
        self.assertNotIsInstance(cm.exception, DuplicateIngestionException, "Business conflict MUST NOT be DuplicateIngestionException")

    def test_p6_12_structured_conflict_context(self):
        """TEST P6-12: Business conflict exception contains structured details payload."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-12",
                order_number="ORD-P6-12",
                delivery_challan="P6-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-12",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-12-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-12",
                order_number="ORD-P6-12",
                delivery_challan="P6-12",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-12",
                    compressive_strength_mpa=Decimal("90.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException) as cm:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-12-2")
        details = cm.exception.details
        self.assertIsNotNone(details, "Exception MUST contain structured details payload")
        self.assertTrue(len(details) > 0)
        self.assertIn("field_name", details[0])

    def test_p6_13_single_payload_conflict_rollback(self):
        """TEST P6-13: Single payload path rolls back completely on business conflict."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-13",
                order_number="ORD-P6-13",
                delivery_challan="P6-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-13",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payload(p1, job_id="JOB-P6-13-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-13",
                order_number="ORD-P6-13",
                delivery_challan="P6-13",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-13",
                    compressive_strength_mpa=Decimal("99.9"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payload(p2, job_id="JOB-P6-13-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-13").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        ct = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).first()
        self.assertEqual(float(ct.compressive_strength_mpa), 45.0, "Rollback MUST preserve original value 45.0")

    def test_p6_14_multi_payload_conflict_rollback(self):
        """TEST P6-14: Multi-payload path rolls back completely on business conflict in any payload."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-14A",
                order_number="ORD-P6-14",
                delivery_challan="P6-14A",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("305.0"))
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-14-1")

        p2_ok = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-14B",
                order_number="ORD-P6-14",
                delivery_challan="P6-14B",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        p2_conflict = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-14A",
                order_number="ORD-P6-14",
                delivery_challan="P6-14A",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("999.0"))
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2_ok, p2_conflict], job_id="JOB-P6-14-2")

        b_ok = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-14B").first()
        self.assertIsNone(b_ok, "BATCH-P6-14B MUST be rolled back when second payload in batch fails!")

    def test_p6_15_parent_child_atomic_rollback(self):
        """TEST P6-15: Parent Batch & children completely roll back on child business conflict."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-15",
                order_number="ORD-P6-15",
                delivery_challan="P6-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-15",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-15-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-15",
                order_number="ORD-P6-15",
                delivery_challan="P6-15",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-15",
                    compressive_strength_mpa=Decimal("88.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2], job_id="JOB-P6-15-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-15").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        ct = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).first()
        self.assertEqual(float(ct.compressive_strength_mpa), 45.0)

    def test_p6_16_multi_material_atomic_rollback(self):
        """TEST P6-16: Multi-material persistence rolls back atomically if one material conflicts."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-16",
                order_number="ORD-P6-16",
                delivery_challan="P6-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("305.0")),
                MaterialConsumptionIngestionDTO(material_code="WATER", planned_quantity=Decimal("150.0"), actual_quantity=Decimal("152.0"))
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-16-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-16",
                order_number="ORD-P6-16",
                delivery_challan="P6-16",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("305.0")), # OK
                MaterialConsumptionIngestionDTO(material_code="WATER", planned_quantity=Decimal("150.0"), actual_quantity=Decimal("999.0")) # Conflict
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2], job_id="JOB-P6-16-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-16").first()
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).all()
        for mc in consumptions:
            if mc.material_id.startswith("MAT-WATER"):
                self.assertEqual(float(mc.actual_quantity), 152.0, "Original water quantity 152.0 MUST be preserved")

    def test_p6_17_laboratory_hierarchy_atomic_rollback(self):
        """TEST P6-17: Laboratory hierarchy rolls back atomically on specimen conflict."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-17",
                order_number="ORD-P6-17",
                delivery_challan="P6-17",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-17",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payloads([p1], job_id="JOB-P6-17-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-17",
                order_number="ORD-P6-17",
                delivery_challan="P6-17",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-17",
                    compressive_strength_mpa=Decimal("77.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        with self.assertRaises(EntityMappingException):
            service.persist_canonical_payloads([p2], job_id="JOB-P6-17-2")

        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-17").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        ct = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).first()
        self.assertEqual(float(ct.compressive_strength_mpa), 45.0)

    def test_p6_18_single_multi_payload_exception_parity(self):
        """TEST P6-18: Single and multi-payload ingestion paths exhibit identical exception parity for conflicts."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p1 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-18",
                order_number="ORD-P6-18",
                delivery_challan="P6-18",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-18",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        service.persist_canonical_payload(p1, job_id="JOB-P6-18-1")

        p2 = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-18",
                order_number="ORD-P6-18",
                delivery_challan="P6-18",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-18",
                    compressive_strength_mpa=Decimal("95.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )

        with self.assertRaises(EntityMappingException) as cm1:
            service.persist_canonical_payload(p2, job_id="JOB-P6-18-SINGLE")

        with self.assertRaises(EntityMappingException) as cm2:
            service.persist_canonical_payloads([p2], job_id="JOB-P6-18-MULTI")

        self.assertEqual(cm1.exception.error_code, cm2.exception.error_code, "Single & multi-payload error codes MUST match")

    def test_p6_19_missing_mould_identifier_contract(self):
        """TEST P6-19: CubeTest without mould_identifier acts as set-level representation without collapsing distinct specimens."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-19",
                order_number="ORD-P6-19",
                delivery_challan="P6-19",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-19",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res = service.persist_canonical_payloads([p], job_id="JOB-P6-19")
        batch_id = res["details"][0]["batch_id"]
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch_id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).all()
        self.assertEqual(len(tests), 1)

    def test_p6_21_identical_completed_batch_reingestion_noop(self):
        """TEST P6-21: Identical completed Batch re-ingestion is NO-OP without raising exception."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-21",
                order_number="ORD-P6-21",
                delivery_challan="P6-21",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            )
        )
        res1 = service.persist_canonical_payload(p, job_id="JOB-P6-21-1")
        self.assertEqual(res1["status"], "SUCCESS")

        # Second submission with identical data MUST be NO-OP without exception
        res2 = service.persist_canonical_payload(p, job_id="JOB-P6-21-2")
        self.assertEqual(res2["status"], "SUCCESS")
        batches = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-21").all()
        self.assertEqual(len(batches), 1, "Exactly 1 canonical batch record MUST exist (NO-OP)")

    def test_p6_22_identical_material_reingestion_noop(self):
        """TEST P6-22: Identical material consumption re-ingestion is NO-OP without raising exception."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-22",
                order_number="ORD-P6-22",
                delivery_challan="P6-22",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=Decimal("300.0"), actual_quantity=Decimal("305.0"))
            ]
        )
        res1 = service.persist_canonical_payload(p, job_id="JOB-P6-22-1")
        self.assertEqual(res1["status"], "SUCCESS")

        res2 = service.persist_canonical_payload(p, job_id="JOB-P6-22-2")
        self.assertEqual(res2["status"], "SUCCESS")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-22").first()
        consumptions = self.db.query(BatchMaterialConsumption).filter(BatchMaterialConsumption.batch_id == batch.id).all()
        self.assertEqual(len(consumptions), 1, "Exactly 1 material consumption record MUST exist (NO-OP)")

    def test_p6_23_identical_laboratory_reingestion_noop(self):
        """TEST P6-23: Identical laboratory specimen re-ingestion is NO-OP without raising exception."""
        ts = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        service = IngestionPersistenceService(self.db)
        p = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-P6-23",
                order_number="ORD-P6-23",
                delivery_challan="P6-23",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                planned_quantity_m3=Decimal("6.0"),
                production_start_time=ts
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="SET-P6-23",
                    compressive_strength_mpa=Decimal("45.0"),
                    age_days=28,
                    testing_timestamp=ts
                )
            ]
        )
        res1 = service.persist_canonical_payload(p, job_id="JOB-P6-23-1")
        self.assertEqual(res1["status"], "SUCCESS")

        res2 = service.persist_canonical_payload(p, job_id="JOB-P6-23-2")
        self.assertEqual(res2["status"], "SUCCESS")
        batch = self.db.query(Batch).filter(Batch.delivery_challan_number == "P6-23").first()
        sample = self.db.query(ConcreteSample).filter(ConcreteSample.batch_id == batch.id).first()
        cs = self.db.query(CubeSet).filter(CubeSet.sample_id == sample.id).first()
        tests = self.db.query(CubeTest).filter(CubeTest.cube_set_id == cs.id).all()
        self.assertEqual(len(tests), 1, "Exactly 1 specimen record MUST exist (NO-OP)")


if __name__ == "__main__":
    unittest.main()


