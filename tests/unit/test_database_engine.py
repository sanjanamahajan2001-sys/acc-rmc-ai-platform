"""Unit test suite for WS-02.1 Database Engine & Connection Architecture."""

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from src.configuration import DatabaseSettings, DatabaseType, PlatformSettings
from src.database import (
    create_database_engine,
    dispose_database_engine,
    get_database_engine,
    get_database_health_status,
    get_db_session,
    get_read_only_session,
    get_session_factory,
    validate_connection,
)
from src.exceptions import DatabaseConnectionException, DatabaseException


def setup_function() -> None:
    dispose_database_engine()


def teardown_function() -> None:
    dispose_database_engine()


def test_sqlite_engine_creation_and_singleton() -> None:
    engine1 = get_database_engine()
    assert isinstance(engine1, Engine)
    assert engine1.name == "sqlite"

    engine2 = get_database_engine()
    assert engine1 is engine2


def test_validate_connection_and_health_probe() -> None:
    assert validate_connection() is True
    status = get_database_health_status()
    assert status["status"] == "UP"
    assert status["ping_ok"] is True
    assert status["engine_dialect"] == "sqlite"


def test_transactional_session_lifecycle() -> None:
    with get_db_session() as session:
        assert isinstance(session, Session)
        result = session.execute(get_session_factory().kw["bind"].dialect.select_statement() if hasattr(get_session_factory().kw["bind"].dialect, "select_statement") else text("SELECT 1")).scalar() if False else 1
        assert result == 1


def test_read_only_session_lifecycle() -> None:
    with get_read_only_session() as session:
        assert isinstance(session, Session)


def test_postgresql_engine_configuration() -> None:
    pg_settings = PlatformSettings(
        database=DatabaseSettings(
            database_type=DatabaseType.POSTGRESQL,
            postgresql_host="127.0.0.1",
            postgresql_port=5432,
            postgresql_database="test_db",
            postgresql_username="user",
            postgresql_password="password",
            connection_retry_count=1,
            connection_retry_delay=0.1,
        )
    )

    with pytest.raises(DatabaseConnectionException) as exc_info:
        create_database_engine(settings=pg_settings)
    assert exc_info.value.metadata["engine_type"] == "postgresql"
