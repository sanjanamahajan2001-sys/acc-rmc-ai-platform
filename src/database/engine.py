"""Database Engine Factory and Singleton Connection Infrastructure.

This module provides the SQLAlchemy 2.0 engine factory with lazy creation, dual engine support
(SQLite vs PostgreSQL), connection retry policy, pool health checks, engine event hooks, and disposal.
"""

import time
from typing import Optional
from sqlalchemy import Engine, create_engine, event, select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from src.configuration import DatabaseType, PlatformSettings, get_platform_settings
from src.exceptions.technical import DatabaseConnectionException, DatabaseException
from src.logging import get_logger

logger = get_logger("src.database.engine", component="database")

_ENGINE_SINGLETON: Optional[Engine] = None


def _setup_engine_event_hooks(engine: Engine) -> None:
    """Attach SQLAlchemy event hooks for connection checkout, checkin, and connect telemetry."""
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.info("Database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Database connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logger.debug("Database connection checked in to pool")


def create_database_engine(
    settings: Optional[PlatformSettings] = None,
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
) -> Engine:
    """Create a SQLAlchemy 2.0 Database Engine based on PlatformSettings configuration.

    Supports SQLite (dev/test) and PostgreSQL (production) with pre-ping validation,
    configurable pooling, event hooks, and retry logic.
    """
    target_settings = settings if settings is not None else get_platform_settings()
    db_cfg = target_settings.database

    url = db_cfg.database_url
    engine_type = db_cfg.database_type

    retries = max_retries if max_retries is not None else db_cfg.connection_retry_count
    delay = retry_delay if retry_delay is not None else db_cfg.connection_retry_delay

    logger.info("Initializing database engine", engine_type=engine_type.value)

    engine_kwargs = {
        "echo": db_cfg.echo,
        "pool_pre_ping": True,
    }

    if engine_type == DatabaseType.SQLITE:
        engine_kwargs["connect_args"] = {"timeout": 30}

    if engine_type == DatabaseType.POSTGRESQL:
        engine_kwargs.update(
            {
                "pool_size": db_cfg.pool_size,
                "max_overflow": db_cfg.max_overflow,
                "pool_timeout": db_cfg.pool_timeout,
            }
        )

    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            engine = create_engine(url, **engine_kwargs)
            _setup_engine_event_hooks(engine)
            # Test engine connectivity
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database engine initialized successfully", engine_type=engine_type.value, attempt=attempt)
            return engine
        except (OperationalError, SQLAlchemyError, Exception) as err:
            last_error = err
            logger.warning(
                "Database engine connection attempt failed",
                attempt=attempt,
                max_retries=retries,
                error=str(err),
            )
            if attempt < retries:
                time.sleep(delay)

    raise DatabaseConnectionException(
        message=f"Failed to connect to database after {retries} attempts: {last_error}",
        metadata={"engine_type": engine_type.value},
    )


def get_database_engine(settings: Optional[PlatformSettings] = None) -> Engine:
    """Return singleton instance of SQLAlchemy Engine."""
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is None:
        _ENGINE_SINGLETON = create_database_engine(settings=settings)
    return _ENGINE_SINGLETON


def dispose_database_engine() -> None:
    """Dispose singleton database engine connection pool gracefully."""
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is not None:
        logger.info("Disposing database engine connection pool")
        _ENGINE_SINGLETON.dispose()
        _ENGINE_SINGLETON = None
