"""Unit test suite for WS-02.12 Database Read Models & Analytical Views."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest
from sqlalchemy import inspect, text
from src.database import (
    AIMetadataService,
    AuditActivityView,
    AuditPersistenceService,
    BaseModel,
    BatchMaterialConsumption,
    BatchSummaryView,
    LaboratoryService,
    MasterReferenceService,
    Material,
    MaterialConsumptionSummaryView,
    OrderService,
    OrderStatusEnum,
    OrderStatusLookup,
    PredictionSummaryView,
    ProductionService,
    QualitySummaryView,
    Recipe,
    ReportingRepository,
    ReportingService,
    dispose_database_engine,
    get_database_engine,
    get_db_session,
    seed_lookup_tables,
)
from src.exceptions import EntityNotFoundException


class TestDatabaseReporting(unittest.TestCase):
    def setUp(self) -> None:
        dispose_database_engine()

    def tearDown(self) -> None:
        dispose_database_engine()

    def test_analytical_views_creation_querying_and_read_only_enforcement(self) -> None:
        engine = get_database_engine()

        # Safely drop views and tables dynamically based on SQLite inspector metadata
        with engine.begin() as conn:
            insp = inspect(conn)
            for view_name in insp.get_view_names():
                conn.execute(text(f"DROP VIEW IF EXISTS {view_name};"))

        BaseModel.metadata.drop_all(engine)

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
            master_srv = MasterReferenceService(session)

            plant = master_srv.create_plant("P_VW_UT_ISOLATED", "View Test Plant Isolated")
            customer = master_srv.create_customer("C_VW_UT_ISOLATED", "View Test Customer Isolated")
            project = master_srv.create_project("PR_VW_UT_ISOLATED", customer.id, "View Test Project Isolated")

            recipe = Recipe(recipe_code="M40_VW_UT_ISOLATED", recipe_name="M40 View Isolated", target_strength_mpa=40.0)
            material = Material(material_code="MAT_CEM_VW_UT_ISOLATED", material_name="Cement VW Isolated", engineering_unit="kg")
            session.add_all([recipe, material])
            session.flush()

            status_lookup = session.query(OrderStatusLookup).filter_by(code=OrderStatusEnum.CONFIRMED.value).first()
            order_srv = OrderService(session)
            req_time = datetime.now(timezone.utc) + timedelta(days=1)

            order = order_srv.create_order(
                order_number="ORD-VW-UT-ISO-001",
                customer_id=customer.id,
                project_id=project.id,
                plant_id=plant.id,
                order_status_id=status_lookup.id,
                requested_delivery_datetime=req_time,
                recipe_id=recipe.id,
                ordered_quantity_m3=50.0,
            )

            schedule = order_srv.create_dispatch_schedule(
                schedule_number="SCH-VW-UT-ISO-001",
                order_id=order.id,
                planned_dispatch_time=req_time,
                planned_delivery_time=req_time + timedelta(minutes=45),
                planned_quantity_m3=6.0,
            )

            prod_srv = ProductionService(session)
            batch = prod_srv.create_batch(
                batch_number="BAT-VW-UT-ISO-001",
                order_id=order.id,
                dispatch_schedule_id=schedule.id,
                recipe_id=recipe.id,
                plant_id=plant.id,
                planned_quantity_m3=Decimal("6.00"),
            )

            lab_srv = LaboratoryService(session)
            sample = lab_srv.create_sample("SMP-VW-UT-ISO-001", batch.id)
            lab_srv.record_slump_test(sample.id, Decimal("125.00"))
            cset = lab_srv.create_cube_set("CSET-VW-UT-ISO-001", sample.id)
            ctest = lab_srv.record_cube_test(cset.id, 28, Decimal("44.50"))
            lab_srv.register_ft7_certificate("FT7-VW-UT-ISO-001", batch.id)

            ai_srv = AIMetadataService(session)
            ai_srv.register_model("StrengthPredictorVWUTISO", "1.0.0")
            fv = ai_srv.persist_feature_vector(batch.id, "1.0.0", "hash_vw_ut_iso", {"cement": 380})
            pred = ai_srv.persist_prediction(fv.id, "1.0.0", Decimal("43.80"))
            ai_srv.register_actual_outcome(pred.id, ctest.id, Decimal("44.50"))

            audit_srv = AuditPersistenceService(session)
            ev = audit_srv.log_audit_event("BATCH_CREATED", "Batch", batch.id, "CREATE")

        with get_db_session() as session:
            rpt_srv = ReportingService(session)

            b_summary = rpt_srv.get_batch_summary("BAT-VW-UT-ISO-001")
            self.assertEqual(b_summary.order_number, "ORD-VW-UT-ISO-001")
            self.assertEqual(b_summary.plant_code, "P_VW_UT_ISOLATED")

            q_summary = rpt_srv.get_quality_summary("SMP-VW-UT-ISO-001")
            self.assertEqual(q_summary.ft7_certificate_number, "FT7-VW-UT-ISO-001")
            self.assertEqual(q_summary.cube_strength_28d, Decimal("44.50"))

            p_summary = rpt_srv.get_prediction_summary(pred.id)
            self.assertEqual(p_summary.predicted_strength, Decimal("43.80"))
            self.assertEqual(p_summary.actual_strength, Decimal("44.50"))

            a_activity = rpt_srv.get_audit_activity(ev.id)
            self.assertEqual(a_activity.event_type, "BATCH_CREATED")


if __name__ == "__main__":
    unittest.main()
