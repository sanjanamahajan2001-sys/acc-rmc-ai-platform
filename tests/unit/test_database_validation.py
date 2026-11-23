"""Unit test suite for WS-02.13 Database Migration Validation, Integrity Verification & Production Certification."""

import unittest
from sqlalchemy import text
from src.database import (
    BaseModel,
    DatabaseValidationRepository,
    DatabaseValidationService,
    dispose_database_engine,
    get_database_engine,
    get_db_session,
    seed_lookup_tables,
    validate_database_constraints,
    validate_database_indexes,
    validate_database_integrity,
    validate_database_schema,
    validate_database_seed_data,
    validate_database_views,
)


class TestDatabaseValidation(unittest.TestCase):
    def setUp(self) -> None:
        dispose_database_engine()

    def tearDown(self) -> None:
        dispose_database_engine()

    def test_database_validation_framework_and_integrity_verification(self) -> None:
        engine = get_database_engine()

        tables_to_create = [t for name, t in BaseModel.metadata.tables.items() if not name.startswith("vw_")]
        BaseModel.metadata.create_all(engine, tables=tables_to_create)

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                CREATE VIEW IF NOT EXISTS vw_batch_summary AS
                SELECT
                    b.batch_number AS batch_number,
                    o.order_number AS order_number,
                    p.plant_code AS plant_code,
                    r.recipe_code AS recipe_code,
                    b.production_status AS production_status,
                    b.planned_quantity_m3 AS planned_quantity,
                    b.actual_quantity_m3 AS actual_quantity,
                    b.production_start_time AS production_start_time,
                    b.production_end_time AS production_end_time
                FROM prd_batches b
                JOIN ord_orders o ON b.order_id = o.id
                JOIN mst_plants p ON b.plant_id = p.id
                JOIN mst_recipes r ON b.recipe_id = r.id;
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE VIEW IF NOT EXISTS vw_material_consumption_summary AS
                SELECT
                    b.batch_number AS batch_number,
                    m.material_code AS material_code,
                    c.planned_quantity AS planned_quantity,
                    c.actual_quantity AS actual_quantity,
                    c.variance_quantity AS variance_quantity,
                    c.variance_percentage AS variance_percentage
                FROM prd_batch_material_consumptions c
                JOIN prd_batches b ON c.batch_id = b.id
                JOIN mst_materials m ON c.material_id = m.id;
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE VIEW IF NOT EXISTS vw_quality_summary AS
                SELECT
                    s.sample_number AS sample_number,
                    b.batch_number AS batch_number,
                    (SELECT st.slump_mm FROM lab_slump_tests st WHERE st.sample_id = s.id ORDER BY st.test_timestamp DESC LIMIT 1) AS slump_mm,
                    (SELECT ct.compressive_strength_mpa FROM lab_cube_tests ct JOIN lab_cube_sets cs ON ct.cube_set_id = cs.id WHERE cs.sample_id = s.id AND ct.age_days = 7 LIMIT 1) AS cube_strength_7d,
                    (SELECT ct.compressive_strength_mpa FROM lab_cube_tests ct JOIN lab_cube_sets cs ON ct.cube_set_id = cs.id WHERE cs.sample_id = s.id AND ct.age_days = 28 LIMIT 1) AS cube_strength_28d,
                    (SELECT ft.certificate_number FROM lab_ft7_certificates ft WHERE ft.batch_id = b.id AND ft.is_deleted = 0 LIMIT 1) AS ft7_certificate_number
                FROM lab_samples s
                JOIN prd_batches b ON s.batch_id = b.id;
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE VIEW IF NOT EXISTS vw_prediction_summary AS
                SELECT
                    p.id AS prediction_id,
                    b.batch_number AS batch_number,
                    p.model_version AS model_version,
                    p.predicted_strength_mpa AS predicted_strength,
                    p.confidence_score AS confidence_score,
                    o.actual_strength_mpa AS actual_strength,
                    p.prediction_timestamp AS prediction_timestamp
                FROM ai_predictions p
                JOIN ai_feature_vectors fv ON p.feature_vector_id = fv.id
                JOIN prd_batches b ON fv.batch_id = b.id
                LEFT JOIN ai_actual_outcomes o ON o.prediction_id = p.id;
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE VIEW IF NOT EXISTS vw_audit_activity AS
                SELECT
                    id AS event_id,
                    event_timestamp AS timestamp,
                    event_type AS event_type,
                    entity_type AS entity_type,
                    action AS action,
                    performed_by_user AS performed_by,
                    severity AS severity,
                    result AS result
                FROM audit_events;
            """
                )
            )

        with get_db_session() as session:
            seed_lookup_tables(session)

        # 1. Direct validation functions
        schema_errs = validate_database_schema(engine)
        self.assertEqual(len(schema_errs), 0, f"Schema validation errors: {schema_errs}")

        index_errs = validate_database_indexes(engine)
        self.assertEqual(len(index_errs), 0, f"Index validation errors: {index_errs}")

        constraint_errs = validate_database_constraints(engine)
        self.assertEqual(len(constraint_errs), 0, f"Constraint validation errors: {constraint_errs}")

        view_errs = validate_database_views(engine)
        self.assertEqual(len(view_errs), 0, f"View validation errors: {view_errs}")

        seed_errs = validate_database_seed_data()
        self.assertEqual(len(seed_errs), 0, f"Seed validation errors: {seed_errs}")

        report = validate_database_integrity(engine)
        self.assertTrue(report.is_healthy)
        self.assertEqual(report.overall_status, "HEALTHY")

        # 2. DatabaseValidationRepository
        repo = DatabaseValidationRepository(engine=engine)
        self.assertGreater(len(repo.get_table_names()), 35)
        self.assertEqual(len(repo.get_view_names()), 5)
        self.assertEqual(len(repo.inspect_schema()), 0)

        # 3. DatabaseValidationService
        service = DatabaseValidationService(engine=engine)
        service_report = service.run_full_validation()
        self.assertTrue(service_report.is_healthy)

        health_integrated = service.get_integrated_health_report()
        self.assertTrue(health_integrated["is_healthy"])
        self.assertEqual(health_integrated["ping"]["status"], "UP")

        startup_report = service.enforce_healthy_startup()
        self.assertTrue(startup_report.is_healthy)


if __name__ == "__main__":
    unittest.main()
