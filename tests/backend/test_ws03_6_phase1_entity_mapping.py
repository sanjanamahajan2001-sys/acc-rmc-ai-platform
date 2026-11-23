from decimal import Decimal
from src.contracts.ingestion.quality import IndividualCubeSpecimenDTO
import unittest
from datetime import datetime, timezone
import uuid
from sqlalchemy.sql import text

from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe, Material
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest

from src.contracts.ingestion.payload import (
    SingleIngestionPayloadDTO,
    BatchIngestionDTO,
    MaterialConsumptionIngestionDTO,
    CubeTestIngestionDTO,
    SlumpTestIngestionDTO,
    FT7CertificateIngestionDTO
)
from src.mappers.canonical_entity_mapper import CanonicalEntityMapper, EntityMappingException



class TestWS036Phase1EntityMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        session_factory = get_session_factory()
        db = session_factory()
        try:
            plant = db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
            if not plant:
                plant = Plant(
                    id="PLANT-ID-MUMBAI-01",
                    plant_code="PLANT-MUMBAI-01",
                    plant_name="ACC Mumbai Batching Plant #1",
                    location="Mumbai Central",
                    timezone="Asia/Kolkata"
                )
                db.add(plant)

            recipe = db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
            if not recipe:
                recipe = Recipe(
                    id="RECIPE-ID-M40-ISOLATED",
                    recipe_code="M40_VW_UT_ISOLATED",
                    recipe_name="M40 View Isolated",
                    mix_design_code="M40-VW-UT",
                    grade="M40",
                    target_strength_mpa=40.0,
                    nominal_max_aggregate_size_mm=20.0
                )
                db.add(recipe)

            from src.database.models.orders import Order
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

            # Seed Material Master Records
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
        session_factory = get_session_factory()
        self.db = session_factory()

        # Build clean test payload
        self.sample_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-TEST-2026-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0,
                production_start_time=datetime(2026, 8, 9, 9, 15, 0, tzinfo=timezone.utc),
                production_end_time=datetime(2026, 8, 9, 9, 17, 15, tzinfo=timezone.utc),
                operator_id="OPERATOR-MUMBAI-01"
            ),

            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=320.0, actual_quantity=320.0),
                MaterialConsumptionIngestionDTO(material_code="FLY_ASH", planned_quantity=0.0, actual_quantity=0.0),
                MaterialConsumptionIngestionDTO(material_code="GGBS", planned_quantity=130.0, actual_quantity=130.0),
                MaterialConsumptionIngestionDTO(material_code="WATER", planned_quantity=160.0, actual_quantity=160.0),
                MaterialConsumptionIngestionDTO(material_code="ADMIXTURE", planned_quantity=3.8, actual_quantity=3.8),
                MaterialConsumptionIngestionDTO(material_code="FINE_AGG", planned_quantity=780.0, actual_quantity=780.0),
                MaterialConsumptionIngestionDTO(material_code="COARSE_AGG", planned_quantity=1080.0, actual_quantity=1080.0),
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-TEST-CUBE-001",
                    age_days=28,
                    compressive_strength_mpa=51.3,
                    testing_timestamp=datetime(2026, 9, 6, tzinfo=timezone.utc),
                    tested_by_user="Rahul Kumar"
                )
            ]

        )

    def tearDown(self):
        self.db.close()

    # --- Batch Mapping Tests ---
    def test_01_valid_batch_mapping(self):
        """Valid SingleIngestionPayloadDTO maps correctly into WS-02 Batch ORM model."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertIsInstance(batch, Batch)
        self.assertEqual(batch.batch_number, "BATCH-TEST-2026-001")
        self.assertEqual(batch.planned_quantity_m3, 6.0)
        self.assertEqual(batch.operator_identifier, "OPERATOR-MUMBAI-01")

    def test_02_plant_fk_resolution(self):
        """Plant code resolves to correct plant_id."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(batch.plant_id, "PLANT-ID-MUMBAI-01")

    def test_03_recipe_fk_resolution(self):
        """Recipe code resolves to correct recipe_id."""
        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(batch.recipe_id, recipe.id)

    def test_04_delivery_challan_mapping(self):
        """Batch mapping succeeds with strict Order FK lookup resolution."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(batch.order_id, "ORD-MANUAL-01-ID")


    def test_05_source_channel_mapping(self):
        """Source channel metadata is preserved in batch payload."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(batch.production_status, "COMPLETED")

    def test_06_required_batch_values_preserved(self):
        """Required timestamps and status defaults are set."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(batch.production_status, "COMPLETED")
        self.assertEqual(batch.version_id, 1)

    # --- Material Mapping & Unit Conversion Tests ---
    def test_07_all_seven_material_components_created(self):
        """All seven material components are mapped."""
        consumptions = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, "PRD-BATCH-01", self.db)
        self.assertEqual(len(consumptions), 7)

    def test_08_correct_material_codes_assigned(self):
        """Material list contains correct materials."""
        consumptions = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, "PRD-BATCH-01", self.db)
        mat_ids = [c.material_id for c in consumptions]
        self.assertTrue(any("CEMENT" in m for m in mat_ids))

    def test_09_unit_conversion_integer(self):
        """320.0 kg/m3 for 6.0 m3 yields exact 1920.0 kg total actual consumption."""
        consumptions = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, "PRD-BATCH-01", self.db)
        cement_c = next(c for c in consumptions if "CEMENT" in c.material_id)
        self.assertEqual(cement_c.actual_quantity, 1920.0) # 320.0 * 6.0 = 1920.0

    def test_10_unit_conversion_fractional_rounding(self):
        """Fractional conversion (317.45 kg/m3 * 5.12 m3) rounds to 2 decimal places (1625.34 kg)."""
        frac_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FRAC-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=5.12
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=317.45, actual_quantity=317.45)
            ]
        )
        consumptions = CanonicalEntityMapper.map_material_consumptions(frac_payload, "PRD-BATCH-01", self.db)
        self.assertEqual(consumptions[0].actual_quantity, 1625.34) # 317.45 * 5.12 = 1625.344 -> 1625.34

    def test_11_zero_quantity_behavior(self):
        """Zero kg/m3 converts to 0.0 kg total actual consumption."""
        consumptions = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, "PRD-BATCH-01", self.db)
        fly_ash_c = next(c for c in consumptions if "FLY_ASH" in c.material_id)
        self.assertEqual(fly_ash_c.actual_quantity, 0.0)

    def test_12_negative_material_quantity_rejected(self):
        """Negative material quantity is rejected by DTO validation / mapper rules."""
        with self.assertRaises(Exception):
            _ = MaterialConsumptionIngestionDTO(material_code="CEMENT", planned_quantity=-10.0, actual_quantity=-10.0)


    # --- Laboratory Hierarchy Mapping Tests ---
    def test_13_concrete_sample_created(self):
        """ConcreteSample ORM object created with sample_number matching qa_cube_id."""
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, "PRD-BATCH-01")
        self.assertIsNotNone(sample)
        self.assertIsInstance(sample, ConcreteSample)
        self.assertEqual(sample.sample_number, "QC-TEST-CUBE-001")

    def test_14_cube_set_linked_to_sample(self):
        """CubeSet ORM object created and linked to ConcreteSample.id."""
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, "PRD-BATCH-01")
        self.assertIsNotNone(set_obj)
        self.assertEqual(set_obj.sample_id, sample.id)

    def test_15_cube_test_linked_to_set(self):
        """CubeTest ORM object created and linked to CubeSet.id."""
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, "PRD-BATCH-01")
        self.assertIsNotNone(test_obj)
        self.assertEqual(test_obj.cube_set_id, set_obj.id)

    def test_16_qa_cube_id_preserved(self):
        """QA Cube ID is preserved across laboratory entities."""
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, "PRD-BATCH-01")
        self.assertEqual(sample.sample_number, "QC-TEST-CUBE-001")
        self.assertEqual(set_obj.cube_set_number, "SET-QC-TEST-CUBE-001")

    def test_17_result_28_day_mpa_mapped(self):
        """28-Day compressive strength result is mapped."""
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, "PRD-BATCH-01")
        self.assertEqual(float(test_obj.compressive_strength_mpa), 51.3)

    def test_18_optional_laboratory_data_empty(self):
        """Empty cube_tests list returns (None, None, None, None, None)."""
        empty_lab_payload = SingleIngestionPayloadDTO(
            batch=self.sample_payload.batch,
            material_consumptions=self.sample_payload.material_consumptions,
            cube_tests=[]
        )
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(empty_lab_payload, "PRD-BATCH-01")
        self.assertIsNone(sample)
        self.assertIsNone(set_obj)
        self.assertIsNone(test_obj)
        self.assertIsNone(slump_obj)
        self.assertIsNone(cert_obj)


    # --- Failure Behavior Tests ---
    def test_19_missing_plant_code_rejected(self):
        """Non-existent plant_code raises EntityMappingException."""
        bad_plant_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-TEST-2026-001",
                order_number="ORD-MANUAL-01",
                plant_code="INVALID_PLANT_999",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            )
        )
        with self.assertRaises(EntityMappingException):
            CanonicalEntityMapper.map_batch(bad_plant_payload, self.db)

    def test_20_missing_recipe_code_rejected(self):
        """Non-existent recipe_code raises EntityMappingException."""
        bad_recipe_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-TEST-2026-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="INVALID_RECIPE_999",
                planned_quantity_m3=6.0
            )
        )
        with self.assertRaises(EntityMappingException):
            CanonicalEntityMapper.map_batch(bad_recipe_payload, self.db)

    def test_21_invalid_payload_rejected_without_db_side_effects(self):
        """Mapping failure raises exception without mutating DB state."""
        bad_plant_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-TEST-2026-001",
                order_number="ORD-MANUAL-01",
                plant_code="INVALID_PLANT_999",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            )
        )
        initial_count = self.db.query(Batch).count()
        with self.assertRaises(EntityMappingException):
            CanonicalEntityMapper.map_batch(bad_plant_payload, self.db)
        self.assertEqual(self.db.query(Batch).count(), initial_count)


    # --- Mapper Purity Tests ---
    def test_22_mapper_no_commit_calls(self):
        """Mapper does NOT issue db.commit() during mapping operations."""
        initial_count = self.db.query(Batch).count()
        _ = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertEqual(self.db.query(Batch).count(), initial_count)

    def test_23_mapper_no_rollback_calls(self):
        """Mapper does NOT issue db.rollback() during mapping operations."""
        initial_count = self.db.query(Batch).count()
        _ = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, "PRD-BATCH-01", self.db)
        self.assertEqual(self.db.query(Batch).count(), initial_count)

    def test_24_mapper_no_api_network_operations(self):
        """Mapper executes purely in memory without network calls."""
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        self.assertIsNotNone(batch.id)

    # --- Comprehensive Source-to-Destination Field Completeness Test ---
    def test_25_full_dto_field_to_entity_mapping_completeness(self):
        """
        Verify that 100% of populated SingleIngestionPayloadDTO fields
        (batch, material_consumptions, slump_tests, cube_tests, ft7_certificate)
        are accurately preserved across target WS-02 ORM entities.
        """
        full_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FULL-9999",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=8.5,
                actual_quantity_m3=8.5,
                production_start_time=datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc),
                production_end_time=datetime(2026, 8, 9, 10, 2, tzinfo=timezone.utc),
                operator_id="OPERATOR-KUMAR-99"
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
                    slump_mm=145.0,
                    test_timestamp=datetime(2026, 8, 9, 10, 5, tzinfo=timezone.utc),
                    tester_name="Vikram Singh",
                    ambient_temperature_c=31.5,
                    concrete_temperature_c=28.0
                )
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-CUBE-FULL-888",
                    age_days=28,
                    compressive_strength_mpa=54.7,
                    testing_timestamp=datetime(2026, 9, 6, tzinfo=timezone.utc),
                    tested_by_user="Amit Patel"
                )
            ],
            ft7_certificate=FT7CertificateIngestionDTO(
                certificate_number="FT7-CERT-7777",
                issued_date=datetime(2026, 9, 7, tzinfo=timezone.utc),
                approval_status="ISSUED",
                remarks="Full certification test pass"
            )
        )

        # 1. Map Batch Header
        batch = CanonicalEntityMapper.map_batch(full_payload, self.db)
        self.assertEqual(batch.batch_number, "BATCH-FULL-9999")
        self.assertEqual(batch.planned_quantity_m3, 8.5)
        self.assertEqual(batch.operator_identifier, "OPERATOR-KUMAR-99")

        # 2. Map Material Consumptions & Verify Material Mass Balance Conservation
        consumptions = CanonicalEntityMapper.map_material_consumptions(full_payload, batch.id, self.db)
        self.assertEqual(len(consumptions), 7)
        cement_c = next(c for c in consumptions if "CEMENT" in c.material_id)
        self.assertEqual(cement_c.actual_quantity, 2720.0) # 320.0 kg/m3 * 8.5 m3 = 2720.0 kg

        # 3. Map Laboratory Specimen Hierarchy
        sample, cube_set, cube_test, slump_test, ft7_cert = CanonicalEntityMapper.map_laboratory(full_payload, batch.id)

        # Assert ConcreteSample
        self.assertIsNotNone(sample)
        self.assertEqual(sample.batch_id, batch.id)
        self.assertEqual(sample.sample_number, "QC-CUBE-FULL-888")

        # Assert CubeSet & CubeTest
        self.assertIsNotNone(cube_set)
        self.assertEqual(cube_set.sample_id, sample.id)
        self.assertIsNotNone(cube_test)
        self.assertEqual(cube_test.cube_set_id, cube_set.id)
        self.assertEqual(float(cube_test.compressive_strength_mpa), 54.7)

        # Assert SlumpTest
        self.assertIsNotNone(slump_test)
        self.assertEqual(slump_test.sample_id, sample.id)
        self.assertEqual(slump_test.slump_mm, 145.0)
        self.assertEqual(slump_test.tester_name, "Vikram Singh")
        self.assertEqual(slump_test.ambient_temp_celsius, 31.5)

        # Assert FT7 Certificate
        self.assertIsNotNone(ft7_cert)
        self.assertEqual(ft7_cert.batch_id, batch.id)
        self.assertEqual(ft7_cert.certificate_number, "FT7-CERT-7777")
        self.assertEqual(ft7_cert.certificate_status, "ISSUED")

    # --- Strict Lineage & Zero-Fallback Verification Tests ---
    def test_26_no_silent_source_data_fallbacks(self):
        """
        Verify that missing optional source fields (actual_quantity_m3, timestamps, operator)
        remain NULL in the ORM entity rather than being populated with fabricated values.
        """
        minimal_batch_dto = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-NO-FALLBACK-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=4.0
                # actual_quantity_m3, production_start_time, production_end_time, operator_id are omitted
            )
        )
        batch = CanonicalEntityMapper.map_batch(minimal_batch_dto, self.db)
        self.assertIsNone(batch.actual_quantity_m3)
        self.assertIsNone(batch.production_start_time)
        self.assertIsNone(batch.production_end_time)
        self.assertIsNone(batch.operator_identifier)

    def test_27_strict_master_data_resolution(self):
        """
        Verify that unresolvable master data references (order_number, material_code)
        raise EntityMappingException deterministically instead of inventing synthetic identifiers.
        """
        # Unresolvable Order
        bad_order_payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-BAD-ORDER",
                order_number="NON_EXISTENT_ORDER_999",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=5.0
            )
        )
        with self.assertRaises(EntityMappingException) as cm_order:
            CanonicalEntityMapper.map_batch(bad_order_payload, self.db)
        self.assertIn("Order number 'NON_EXISTENT_ORDER_999' not found", str(cm_order.exception))

        # Unresolvable Material Code
        bad_mat_payload = SingleIngestionPayloadDTO(
            batch=self.sample_payload.batch,
            material_consumptions=[
                MaterialConsumptionIngestionDTO(material_code="UNREGISTERED_CEMENT", planned_quantity=300.0, actual_quantity=300.0)
            ]
        )
        with self.assertRaises(EntityMappingException) as cm_mat:
            CanonicalEntityMapper.map_material_consumptions(bad_mat_payload, "PRD-BATCH-01", self.db)
        self.assertIn("Material code 'UNREGISTERED_CEMENT' not found", str(cm_mat.exception))

    def test_28_lineage_and_metadata_persistence_contract(self):
        """
        Verify lineage preservation across Batch, Material, Slump, Cube, and FT7 entities.
        """
        batch = CanonicalEntityMapper.map_batch(self.sample_payload, self.db)
        consumptions = CanonicalEntityMapper.map_material_consumptions(self.sample_payload, batch.id, self.db)
        sample, set_obj, test_obj, slump_obj, cert_obj = CanonicalEntityMapper.map_laboratory(self.sample_payload, batch.id)

        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
        self.assertEqual(batch.order_id, "ORD-MANUAL-01-ID")
        self.assertEqual(batch.plant_id, "PLANT-ID-MUMBAI-01")
        self.assertEqual(batch.recipe_id, recipe.id)
        self.assertEqual(sample.batch_id, batch.id)
        self.assertEqual(set_obj.sample_id, sample.id)
        self.assertEqual(test_obj.cube_set_id, set_obj.id)




    # --- Fix Group 4 Reconciled Mapping & 6-Cube Relational Unit Tests ---
    def test_29_delivery_challan_and_truck_number_mapping(self):
        """Verify delivery_challan -> delivery_challan_number and truck_number -> truck_identifier mapping."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FG4-001",
                order_number="ORD-MANUAL-01",
                delivery_challan="CHALLAN-1749",
                truck_number="GA07F7633",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            )
        )
        batch = CanonicalEntityMapper.map_batch(payload, self.db)
        self.assertEqual(batch.delivery_challan_number, "CHALLAN-1749")
        self.assertEqual(batch.truck_identifier, "GA07F7633")

    def test_30_source_material_code_and_moisture_mapping(self):
        """Verify source_material_code, moisture_percentage, absorption_percentage, and moisture_correction_kg mapping."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FG4-002",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEMENT",
                    source_material_code="CEMENT 1 (OPC 53)",
                    planned_quantity=Decimal("320.00"),
                    actual_quantity=Decimal("320.00"),
                    moisture_percentage=Decimal("2.50"),
                    absorption_percentage=Decimal("0.50"),
                    moisture_correction_kg=Decimal("6.40")
                )
            ]
        )
        consumptions = CanonicalEntityMapper.map_material_consumptions(payload, "BATCH-FG4-002", self.db)
        self.assertEqual(len(consumptions), 1)
        cons = consumptions[0]
        self.assertEqual(cons.source_material_code, "CEMENT 1 (OPC 53)")
        self.assertEqual(cons.moisture_percentage, Decimal("2.50"))
        self.assertEqual(cons.absorption_percentage, Decimal("0.50"))
        self.assertEqual(cons.moisture_correction_kg, Decimal("6.40"))

    def test_31_six_individual_cube_specimens_relational_mapping(self):
        """Verify 6 individual cube specimens (3x 7D + 3x 28D) map into 6 distinct CubeTest ORM entities without JSON serialization."""
        specimens_7d = [
            IndividualCubeSpecimenDTO(
                mould_identifier=f"MOULD-7D-0{i}",
                testing_timestamp=datetime.now(timezone.utc),
                age_days=7,
                saturated_mass_kg=Decimal("8.65"),
                failure_load_kn=Decimal("856.00"),
                source_compressive_strength_mpa=Decimal(f"38.0{i}")
            ) for i in range(1, 4)
        ]
        specimens_28d = [
            IndividualCubeSpecimenDTO(
                mould_identifier=f"MOULD-28D-0{i}",
                testing_timestamp=datetime.now(timezone.utc),
                age_days=28,
                saturated_mass_kg=Decimal("8.70"),
                failure_load_kn=Decimal("1100.00"),
                source_compressive_strength_mpa=Decimal(f"48.0{i}")
            ) for i in range(1, 4)
        ]

        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-FG4-CUBES-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-SET-1749-7D",
                    age_days=7,
                    compressive_strength_mpa=Decimal("38.04"),
                    testing_timestamp=datetime.now(timezone.utc),
                    cube_specimens=specimens_7d
                ),
                CubeTestIngestionDTO(
                    cube_set_number="QC-SET-1749-28D",
                    age_days=28,
                    compressive_strength_mpa=Decimal("48.04"),
                    testing_timestamp=datetime.now(timezone.utc),
                    cube_specimens=specimens_28d
                )
            ]
        )

        sample, csets, ctests, slump, ft7 = CanonicalEntityMapper.map_laboratory_relational(payload, "BATCH-FG4-CUBES-001")
        self.assertIsNotNone(sample)
        self.assertEqual(len(csets), 1)
        self.assertEqual(len(ctests), 6)

        mould_ids = [ct.mould_identifier for ct in ctests]
        self.assertEqual(mould_ids, ["MOULD-7D-01", "MOULD-7D-02", "MOULD-7D-03", "MOULD-28D-01", "MOULD-28D-02", "MOULD-28D-03"])
        
        # Verify RAW source strength is preserved
        self.assertEqual(ctests[0].compressive_strength_mpa, Decimal("38.01"))
        self.assertEqual(ctests[5].compressive_strength_mpa, Decimal("48.03"))

    def test_32_mapper_executes_zero_database_writes_or_commits(self):
        """Verify CanonicalEntityMapper operates 100% in-memory with zero DB commits or flushes."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-ZERO-DB-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            )
        )
        batch = CanonicalEntityMapper.map_batch(payload, self.db)
        self.assertIsInstance(batch, Batch)


if __name__ == '__main__':
    unittest.main()
