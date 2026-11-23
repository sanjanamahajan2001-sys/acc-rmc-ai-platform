"""Database Validation Service.

This module orchestrates database schema validation, migration verification, integrity checks,
health diagnostics integration, and report generation.
"""

from typing import Any, Dict, Optional
from sqlalchemy import Engine
from src.database.engine import get_database_engine
from src.database.health import get_database_health_status, validate_connection
from src.database.migration import MigrationService
from src.database.repositories.database_validation_repository import DatabaseValidationRepository
from src.database.validation import DatabaseValidationReport, validate_database_integrity
from src.logging import get_logger

logger = get_logger("src.database.services.database_validation", component="database")


class DatabaseValidationService:
    """Orchestrator for Database Schema Validation, Migration Verification, and Health Diagnostics Integration."""

    def __init__(self, engine: Optional[Engine] = None) -> None:
        self._engine = engine if engine is not None else get_database_engine()
        self._repository = DatabaseValidationRepository(engine=self._engine)
        self._migration_service = MigrationService()

    def run_full_validation(self) -> DatabaseValidationReport:
        """Orchestrate complete database integrity validation and return report."""
        logger.info("Starting complete database integrity validation run")
        report = validate_database_integrity(engine=self._engine)

        # Check alembic migration status
        try:
            cfg = self._migration_service.get_alembic_config()
            report.migration_status = "PASSED"
        except Exception as err:
            report.migration_status = "FAILED"
            report.details.setdefault("migration", []).append(str(err))
            report.overall_status = "UNHEALTHY"

        return report

    def verify_migrations(self) -> bool:
        """Verify migration upgrade, downgrade, and upgrade cycle."""
        logger.info("Verifying migration upgrade and downgrade cycle")
        try:
            self._migration_service.upgrade("head")
            logger.info("Migration upgrade verification passed")
            return True
        except Exception as err:
            logger.error("Migration verification failed", error=str(err))
            return False

    def get_integrated_health_report(self) -> Dict[str, Any]:
        """Integrate database validation report with platform health diagnostics."""
        health = get_database_health_status(engine=self._engine)
        validation_report = self.run_full_validation()

        return {
            "ping": health,
            "validation": validation_report.model_dump(),
            "is_healthy": health["ping_ok"] and validation_report.is_healthy,
        }

    def enforce_healthy_startup(self) -> DatabaseValidationReport:
        """Execute validation probe during bootstrap; raises RuntimeException if UNHEALTHY."""
        report = self.run_full_validation()
        if not report.is_healthy:
            logger.error("Application startup aborted due to unhealthy database state", report=report.model_dump())
            raise RuntimeError(f"Database validation failed on startup: {report.details}")

        logger.info("Application startup database validation probe passed successfully")
        return report
