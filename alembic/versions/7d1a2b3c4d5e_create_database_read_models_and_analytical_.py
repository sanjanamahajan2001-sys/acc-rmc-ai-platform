"""create database read models and analytical views

Revision ID: 7d1a2b3c4d5e
Revises: 5cec000e86e3
Create Date: 2026-08-07 20:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
import src.database.base

# revision identifiers, used by Alembic.
revision = '7d1a2b3c4d5e'
down_revision = '5cec000e86e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. vw_batch_summary
    op.execute("""
        CREATE VIEW vw_batch_summary AS
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
        JOIN mst_recipes r ON b.recipe_id = r.id
        WHERE b.is_deleted = 0;
    """)

    # 2. vw_material_consumption_summary
    op.execute("""
        CREATE VIEW vw_material_consumption_summary AS
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
    """)

    # 3. vw_quality_summary
    op.execute("""
        CREATE VIEW vw_quality_summary AS
        SELECT
            s.sample_number AS sample_number,
            b.batch_number AS batch_number,
            (SELECT st.slump_mm FROM lab_slump_tests st WHERE st.sample_id = s.id ORDER BY st.test_timestamp DESC LIMIT 1) AS slump_mm,
            (SELECT ct.compressive_strength_mpa FROM lab_cube_tests ct JOIN lab_cube_sets cs ON ct.cube_set_id = cs.id WHERE cs.sample_id = s.id AND ct.age_days = 7 LIMIT 1) AS cube_strength_7d,
            (SELECT ct.compressive_strength_mpa FROM lab_cube_tests ct JOIN lab_cube_sets cs ON ct.cube_set_id = cs.id WHERE cs.sample_id = s.id AND ct.age_days = 28 LIMIT 1) AS cube_strength_28d,
            (SELECT ft.certificate_number FROM lab_ft7_certificates ft WHERE ft.batch_id = b.id AND ft.is_deleted = 0 LIMIT 1) AS ft7_certificate_number
        FROM lab_samples s
        JOIN prd_batches b ON s.batch_id = b.id
        WHERE s.is_deleted = 0;
    """)

    # 4. vw_prediction_summary
    op.execute("""
        CREATE VIEW vw_prediction_summary AS
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
        LEFT JOIN ai_actual_outcomes o ON o.prediction_id = p.id
        WHERE p.is_deleted = 0;
    """)

    # 5. vw_audit_activity
    op.execute("""
        CREATE VIEW vw_audit_activity AS
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
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_audit_activity;")
    op.execute("DROP VIEW IF EXISTS vw_prediction_summary;")
    op.execute("DROP VIEW IF EXISTS vw_quality_summary;")
    op.execute("DROP VIEW IF EXISTS vw_material_consumption_summary;")
    op.execute("DROP VIEW IF EXISTS vw_batch_summary;")
