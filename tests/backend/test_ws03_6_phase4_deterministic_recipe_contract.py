import unittest
from datetime import datetime, timezone
from src.database.engine import get_database_engine
from src.database.session import get_session_factory
from src.database.models.master import Recipe, Plant
from src.database.models.orders import Order
from src.mappers.canonical_entity_mapper import CanonicalEntityMapper, EntityMappingException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO, BatchIngestionDTO

class TestDeterministicActiveRecipeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_database_engine()
        cls.SessionFactory = get_session_factory(cls.engine)

    def setUp(self):
        self.db = self.SessionFactory()
        # Seed M25_VW_UT_ISOLATED if missing
        r_m25 = self.db.query(Recipe).filter(Recipe.recipe_code == "M25_VW_UT_ISOLATED").first()
        if not r_m25:
            r_m25 = Recipe(
                id="rec-m25-test-001",
                recipe_code="M25_VW_UT_ISOLATED",
                recipe_name="Standard M25 Grade",
                target_strength_mpa=25.0,
                is_deleted=False
            )
            self.db.add(r_m25)
            self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_01_m40_approved_alias_resolves_to_exact_canonical(self):
        """M-40 resolves deterministically to M40_VW_UT_ISOLATED."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-M40",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-40",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        batch = CanonicalEntityMapper.map_batch(payload, self.db)
        recipe = self.db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
        self.assertEqual(recipe.recipe_code, "M40_VW_UT_ISOLATED")

    def test_02_additional_approved_alias_resolves_correctly(self):
        """M-25 resolves deterministically to M25_VW_UT_ISOLATED."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-M25",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-25",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        batch = CanonicalEntityMapper.map_batch(payload, self.db)
        recipe = self.db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
        self.assertEqual(recipe.recipe_code, "M25_VW_UT_ISOLATED")

    def test_03_exact_canonical_code_direct_resolution(self):
        """Direct canonical recipe_code resolution."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-EXACT",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        batch = CanonicalEntityMapper.map_batch(payload, self.db)
        recipe = self.db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
        self.assertEqual(recipe.recipe_code, "M40_VW_UT_ISOLATED")

    def test_04_m999_unmapped_code_rejected(self):
        """M-999 raises EntityMappingException."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-M999",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-999",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        with self.assertRaises(EntityMappingException):
            CanonicalEntityMapper.map_batch(payload, self.db)

    def test_05_non_existent_recipe_rejected(self):
        """NON_EXISTENT_RECIPE raises EntityMappingException."""
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-UNK",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="NON_EXISTENT_RECIPE",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        with self.assertRaises(EntityMappingException):
            CanonicalEntityMapper.map_batch(payload, self.db)

    def test_06_inactive_soft_deleted_recipe_not_resolved(self):
        """Inactive (is_deleted=True) recipe does not resolve."""
        inactive_recipe = Recipe(
            id="rec-test-inactive-001",
            recipe_code="INACTIVE_RECIPE_CODE",
            recipe_name="Inactive Test Recipe",
            target_strength_mpa=30.0,
            is_deleted=True
        )
        self.db.add(inactive_recipe)
        self.db.flush()

        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-INACTIVE",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="INACTIVE_RECIPE_CODE",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        try:
            with self.assertRaises(EntityMappingException):
                CanonicalEntityMapper.map_batch(payload, self.db)
        finally:
            self.db.rollback()

    def test_07_ambiguous_multiple_matches_rejected(self):
        """Multiple active matches raise EntityMappingException (no arbitrary .first())."""
        r1 = Recipe(
            id="rec-test-ambig-001",
            recipe_code="M-AMBIG",
            recipe_name="Ambiguous Recipe 1",
            target_strength_mpa=30.0,
            is_deleted=False
        )
        r2 = Recipe(
            id="rec-test-ambig-002",
            recipe_code="M_AMBIG",
            recipe_name="Ambiguous Recipe 2",
            target_strength_mpa=30.0,
            is_deleted=False
        )
        self.db.add(r1)
        self.db.add(r2)
        self.db.flush()

        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="TEST-DET-AMBIG",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M-AMBIG",
                order_number="ORD-VW-UT-ISO-001",
                planned_quantity_m3=6.0
            )
        )
        try:
            with self.assertRaises(EntityMappingException):
                CanonicalEntityMapper.map_batch(payload, self.db)
        finally:
            self.db.rollback()

if __name__ == "__main__":
    unittest.main()
