"""Database Health Services and Readiness Diagnostic Probe.

This module provides validation probes (`validate_connection()`) to verify database engine
readiness without requiring ORM models or database migrations.
"""

from typing import Any, Dict, Optional
from sqlalchemy import Engine, text
from src.database.engine import get_database_engine
from src.exceptions.technical import DatabaseConnectionException
from src.logging import get_logger

logger = get_logger("src.database.health", component="database")


def validate_connection(engine: Optional[Engine] = None) -> bool:
    """Validate database engine connectivity by executing `SELECT 1`.

    Returns:
        bool: True if connection check succeeds, False otherwise.
    """
    target_engine = engine if engine is not None else get_database_engine()
    try:
        with target_engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                logger.info("Database health ping connection probe succeeded")
                return True
            return False
    except Exception as err:
        logger.error("Database health ping connection probe failed", error=str(err))
        return False


def get_database_health_status(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """Return diagnostic dictionary of database health status."""
    is_healthy = validate_connection(engine=engine)
    return {
        "status": "UP" if is_healthy else "DOWN",
        "engine_dialect": (engine or get_database_engine()).name if is_healthy else "unknown",
        "ping_ok": is_healthy,
    }
