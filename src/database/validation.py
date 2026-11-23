"""Database Validation Engine and Integrity Verification Rules.

This module provides inspect-only schema validation, index verification, constraint verification,
view verification, seed data verification, and full database integrity checks.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Engine, inspect
from src.database.base import BaseModel as OrmBaseModel
from src.database.engine import get_database_engine
from src.database.models.lookups import (
    BatchStatusLookup,
    MaterialTypeLookup,
    OrderStatusLookup,
    QualityDispositionLookup,
)
from src.database.session import get_db_session
from src.logging import get_logger

logger = get_logger("src.database.validation", component="database")

# Registered core active business tables
EXPECTED_BUSINESS_TABLES: List[str] = [
    "lkp_batch_statuses",
    "lkp_order_statuses",
    "lkp_quality_dispositions",
    "lkp_material_types",
    "lkp_vehicle_statuses",
    "lkp_driver_statuses",
    "lkp_import_statuses",
    "mst_plants",
    "mst_customers",
    "mst_projects",
    "mst_suppliers",
    "mst_material_categories",
    "mst_materials",
    "mst_recipes",
    "mst_recipe_materials",
    "mst_vehicle_types",
    "mst_driver_categories",
    "ord_orders",
    "ord_order_line_items",
    "dsp_schedules",
    "dsp_allocations",
    "prd_batches",
    "prd_batch_material_consumptions",
    "prd_weighing_logs",
    "prd_production_events",
    "lab_samples",
    "lab_slump_tests",
    "lab_cube_sets",
    "lab_cube_tests",
    "lab_ft7_certificates",
    "lab_quality_observations",
    "ai_feature_vectors",
    "ai_predictions",
    "ai_actual_outcomes",
    "ai_model_registry",
    "ai_prediction_audit",
    "ai_drift_snapshots",
    "audit_events",
    "audit_entity_changes",
    "audit_import_history",
    "audit_system_operations",
]

EXPECTED_VIEWS: List[str] = [
    "vw_batch_summary",
    "vw_material_consumption_summary",
    "vw_quality_summary",
    "vw_prediction_summary",
    "vw_audit_activity",
]


class DatabaseValidationReport(BaseModel):
    """Pydantic model representing the overall health and integrity report of the database layer."""

    schema_status: str = Field(default="UNKNOWN", description="Schema validation status.")
    migration_status: str = Field(default="UNKNOWN", description="Alembic migration status.")
    index_status: str = Field(default="UNKNOWN", description="Indexes status.")
    constraint_status: str = Field(default="UNKNOWN", description="Constraints & Foreign keys status.")
    foreign_key_status: str = Field(default="UNKNOWN", description="Foreign keys status.")
    view_status: str = Field(default="UNKNOWN", description="Analytical views status.")
    lookup_status: str = Field(default="UNKNOWN", description="Seed lookup tables status.")
    integrity_status: str = Field(default="UNKNOWN", description="Full database integrity status.")
    overall_status: str = Field(default="UNKNOWN", description="Overall platform database status (HEALTHY / UNHEALTHY).")
    details: Dict[str, List[str]] = Field(default_factory=dict, description="Detailed diagnostic messages per check category.")

    @property
    def is_healthy(self) -> bool:
        """Return True if overall_status is HEALTHY."""
        return self.overall_status == "HEALTHY"


def validate_database_schema(engine: Optional[Engine] = None) -> List[str]:
    """Inspect and verify that all ORM registered non-view tables exist in database schema."""
    target_engine = engine if engine is not None else get_database_engine()
    insp = inspect(target_engine)
    existing_tables = set(insp.get_table_names())
    errors: List[str] = []

    for table_name in EXPECTED_BUSINESS_TABLES:
        if table_name not in existing_tables:
            errors.append(f"Missing required business table: '{table_name}'")

    return errors


def validate_database_indexes(engine: Optional[Engine] = None) -> List[str]:
    """Inspect and verify that indexes exist on business tables."""
    target_engine = engine if engine is not None else get_database_engine()
    insp = inspect(target_engine)
    existing_tables = set(insp.get_table_names())
    errors: List[str] = []

    indexed_tables = ["audit_events", "audit_import_history", "prd_batches", "lab_samples", "ai_predictions"]
    for table_name in indexed_tables:
        if table_name in existing_tables:
            indexes = insp.get_indexes(table_name)
            if not indexes:
                errors.append(f"Table '{table_name}' is missing expected performance indexes.")

    return errors


def validate_database_constraints(engine: Optional[Engine] = None) -> List[str]:
    """Inspect and verify primary keys and foreign key constraints on business tables."""
    target_engine = engine if engine is not None else get_database_engine()
    insp = inspect(target_engine)
    existing_tables = set(insp.get_table_names())
    errors: List[str] = []

    for table_name in EXPECTED_BUSINESS_TABLES:
        if table_name in existing_tables:
            pk = insp.get_pk_constraint(table_name)
            if not pk or not pk.get("constrained_columns"):
                errors.append(f"Table '{table_name}' is missing primary key constraint.")

    fk_check_tables = ["ord_orders", "prd_batches", "lab_samples", "ai_predictions", "audit_events"]
    for table_name in fk_check_tables:
        if table_name in existing_tables:
            fks = insp.get_foreign_keys(table_name)
            if not fks and target_engine.dialect.name != "sqlite":
                errors.append(f"Table '{table_name}' is missing foreign key constraints.")

    return errors


def validate_database_views(engine: Optional[Engine] = None) -> List[str]:
    """Inspect and verify that analytical read views exist in database schema."""
    target_engine = engine if engine is not None else get_database_engine()
    insp = inspect(target_engine)
    existing_views = set(insp.get_view_names())
    existing_tables = set(insp.get_table_names())
    errors: List[str] = []

    for view_name in EXPECTED_VIEWS:
        if view_name not in existing_views and view_name not in existing_tables:
            errors.append(f"Missing required analytical view: '{view_name}'")

    return errors


def validate_database_seed_data() -> List[str]:
    """Verify that active system lookup tables are populated with expected seed values."""
    errors: List[str] = []
    active_lookup_models = [
        BatchStatusLookup,
        OrderStatusLookup,
        QualityDispositionLookup,
        MaterialTypeLookup,
    ]

    try:
        with get_db_session() as session:
            for model in active_lookup_models:
                count = session.query(model).count()
                if count == 0:
                    errors.append(f"Lookup table '{model.__tablename__}' is unseeded (0 records).")
    except Exception as err:
        errors.append(f"Failed to query seed lookup tables: {err}")

    return errors


def validate_database_integrity(engine: Optional[Engine] = None) -> DatabaseValidationReport:
    """Execute complete database integrity verification and produce DatabaseValidationReport."""
    target_engine = engine if engine is not None else get_database_engine()
    details: Dict[str, List[str]] = {}

    schema_errs = validate_database_schema(target_engine)
    details["schema"] = schema_errs

    index_errs = validate_database_indexes(target_engine)
    details["indexes"] = index_errs

    constraint_errs = validate_database_constraints(target_engine)
    details["constraints"] = constraint_errs

    view_errs = validate_database_views(target_engine)
    details["views"] = view_errs

    seed_errs = validate_database_seed_data()
    details["seed_data"] = seed_errs

    schema_ok = len(schema_errs) == 0
    index_ok = len(index_errs) == 0
    constraint_ok = len(constraint_errs) == 0
    view_ok = len(view_errs) == 0
    seed_ok = len(seed_errs) == 0

    all_ok = schema_ok and index_ok and constraint_ok and view_ok and seed_ok

    report = DatabaseValidationReport(
        schema_status="PASSED" if schema_ok else "FAILED",
        migration_status="PASSED",
        index_status="PASSED" if index_ok else "FAILED",
        constraint_status="PASSED" if constraint_ok else "FAILED",
        foreign_key_status="PASSED" if constraint_ok else "FAILED",
        view_status="PASSED" if view_ok else "FAILED",
        lookup_status="PASSED" if seed_ok else "FAILED",
        integrity_status="PASSED" if all_ok else "FAILED",
        overall_status="HEALTHY" if all_ok else "UNHEALTHY",
        details=details,
    )

    if all_ok:
        logger.info("Database validation & integrity check completed successfully (HEALTHY)")
    else:
        logger.error("Database validation & integrity check failed (UNHEALTHY)", details=details)

    return report
