"""Alembic Database Migration Service & Command Runner Engine.

This module provides programmatic Alembic migration execution (`upgrade()`, `downgrade()`,
`generate_revision()`) with thread serialization locking, integrated with PlatformSettings and structlog telemetry.
"""

from pathlib import Path
import threading
from typing import Any, Dict, Optional
from alembic import command
from alembic.config import Config
from src.configuration import get_paths, get_platform_settings
from src.exceptions.technical import DatabaseException
from src.logging import get_logger

logger = get_logger("src.database.migration", component="database")

_MIGRATION_LOCK: threading.Lock = threading.Lock()


class MigrationService:
    """Programmatic Alembic Migration Engine with thread serialization locking."""

    def __init__(self, alembic_ini_path: Optional[Path] = None) -> None:
        paths = get_paths()
        self._ini_path = alembic_ini_path if alembic_ini_path is not None else paths.project_root / "alembic.ini"

    def get_alembic_config(self) -> Config:
        """Construct Alembic Config object dynamically pointing to active database_url."""
        settings = get_platform_settings()
        cfg = Config(str(self._ini_path))
        cfg.set_main_option("sqlalchemy.url", settings.database.database_url)
        cfg.set_main_option("script_location", str(get_paths().project_root / "alembic"))
        return cfg

    def upgrade(self, revision: str = "head") -> None:
        """Run database migration upgrade to specified revision with thread serialization locking."""
        with _MIGRATION_LOCK:
            cfg = self.get_alembic_config()
            logger.info("Executing database migration upgrade", revision=revision)
            try:
                command.upgrade(cfg, revision)
                logger.info("Database migration upgrade completed successfully", revision=revision)
            except Exception as err:
                logger.error("Database migration upgrade failed", revision=revision, error=str(err))
                raise DatabaseException(message=f"Migration upgrade failed: {err}") from err

    def downgrade(self, revision: str = "base") -> None:
        """Run database migration downgrade to specified revision with thread serialization locking."""
        with _MIGRATION_LOCK:
            cfg = self.get_alembic_config()
            logger.info("Executing database migration downgrade", revision=revision)
            try:
                command.downgrade(cfg, revision)
                logger.info("Database migration downgrade completed successfully", revision=revision)
            except Exception as err:
                logger.error("Database migration downgrade failed", revision=revision, error=str(err))
                raise DatabaseException(message=f"Migration downgrade failed: {err}") from err

    def generate_revision(self, message: str, autogenerate: bool = True) -> None:
        """Generate a new migration revision script."""
        with _MIGRATION_LOCK:
            cfg = self.get_alembic_config()
            logger.info("Generating migration revision script", message=message, autogenerate=autogenerate)
            try:
                command.revision(cfg, message=message, autogenerate=autogenerate)
                logger.info("Migration revision script generated successfully", message=message)
            except Exception as err:
                logger.error("Migration revision script generation failed", message=message, error=str(err))
                raise DatabaseException(message=f"Revision generation failed: {err}") from err
