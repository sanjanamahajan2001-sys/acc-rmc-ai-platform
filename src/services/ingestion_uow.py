"""
WS-03.6 Phase 2: IngestionUnitOfWork (Unit of Work Pattern).
Centralized, single owner of transaction lifecycle for canonical ingestion.
Manages begin, flush, commit, and rollback for atomic multi-table ingestion.
"""

from typing import Optional, Callable, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class IngestionUnitOfWork:
    """
    Unit of Work transaction coordinator for WS-03.6 Transactional Persistence.
    Ensures atomic commit/rollback across prd_batches, prd_batch_material_consumptions,
    lab_samples, lab_cube_sets, lab_cube_tests, lab_slump_tests, lab_ft7_certificates,
    and sys_ingestion_jobs.
    """

    def __init__(self, db: Session):
        self.db = db
        self._in_transaction = False

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.warning(f"Exception detected in IngestionUnitOfWork block: {exc_val}. Executing rollback.")
            self.rollback()
        else:
            try:
                self.commit()
            except Exception as e:
                logger.error(f"Error during IngestionUnitOfWork auto-commit: {e}. Executing rollback.")
                self.rollback()
                raise e

    def begin(self) -> None:
        """Begin or join transaction boundary."""
        if not self.db.in_transaction():
            self.db.begin()
        self._in_transaction = True

    def flush(self) -> None:
        """Flush pending ORM operations to populate database-generated attributes/foreign keys without committing."""
        try:
            self.db.flush()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError during UoW flush: {e}")
            raise e

    def commit(self) -> None:
        """Commit the atomic transaction with atomic cache token update and event journaling."""
        if self._in_transaction or self.db.in_transaction():
            try:
                # Atomic Cache Token Increment & Event Journaling inside transaction before commit
                try:
                    from src.database.services.cache_token_service import CacheTokenService
                    CacheTokenService.bump_token_and_journal(
                        db=self.db,
                        token_name="production_batch",
                        event_type="PRODUCTION_DATA_CHANGED",
                        scopes=["kpis", "materials", "mix_performance"],
                    )
                except Exception as token_err:
                    logger.debug("Cache token bump warning: %s", token_err)

                self.db.commit()
                self._in_transaction = False
                logger.info("IngestionUnitOfWork successfully committed transaction.")
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError during UoW commit: {e}. Executing rollback.")
                self.rollback()
                raise e

    def rollback(self) -> None:
        """Rollback all pending changes in the transaction."""
        try:
            self.db.rollback()
            self._in_transaction = False
            logger.info("IngestionUnitOfWork successfully rolled back transaction.")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError during UoW rollback: {e}")
            raise e

    def execute_in_transaction(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute a callable inside an explicit atomic transaction with auto-rollback on failure."""
        self.begin()
        try:
            result = func(*args, **kwargs)
            self.flush()
            self.commit()
            return result
        except Exception as e:
            self.rollback()
            raise e
