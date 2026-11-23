"""Database Session Factory and Session Manager Infrastructure.

This module provides scoped session creation, context-managed transactions (`get_db_session()`),
commit/rollback error handling, and session leak prevention.
"""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker
from src.database.engine import get_database_engine
from src.exceptions.technical import DatabaseException
from src.logging import get_logger

logger = get_logger("src.database.session", component="database")

_SESSION_FACTORY: Optional[sessionmaker[Session]] = None


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker[Session]:
    """Return sessionmaker factory instance for building database sessions."""
    global _SESSION_FACTORY
    target_engine = engine if engine is not None else get_database_engine()
    if _SESSION_FACTORY is None or engine is not None:
        _SESSION_FACTORY = sessionmaker(
            bind=target_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Context manager producing transactional database session with auto-commit/rollback.

    Guarantees session cleanup in finally block preventing session leaks.
    """
    factory = get_session_factory(engine=engine)
    session: Session = factory()
    logger.info("Database session created")
    try:
        yield session
        session.commit()
        logger.info("Database transaction committed successfully")
    except Exception as err:
        session.rollback()
        logger.warning("Database transaction rolled back due to error", error=str(err))
        if isinstance(err, DatabaseException):
            raise
        raise DatabaseException(message=f"Database transaction error: {err}") from err
    finally:
        session.close()
        logger.info("Database session closed")


@contextmanager
def get_read_only_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Context manager producing read-only session for querying."""
    factory = get_session_factory(engine=engine)
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()
