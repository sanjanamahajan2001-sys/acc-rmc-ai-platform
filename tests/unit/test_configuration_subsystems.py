"""Unit test suite for WS-01.5B Subsystem Settings Schemas."""

import pytest
from src.configuration import (
    AISettings,
    ApplicationSettings,
    DashboardSettings,
    DatabaseSettings,
    DatabaseType,
    DuplicatePolicy,
    ImportSettings,
    LoggingSettings,
    PlatformSettings,
    ReportingSettings,
    SchedulerSettings,
    SecuritySettings,
    get_platform_settings,
)


def test_database_settings_url_construction() -> None:
    sqlite_db = DatabaseSettings(database_type=DatabaseType.SQLITE, sqlite_path="runtime/test.sqlite3")
    assert sqlite_db.database_url.startswith("sqlite:///")
    assert "test.sqlite3" in sqlite_db.database_url

    pg_db = DatabaseSettings(
        database_type=DatabaseType.POSTGRESQL,
        postgresql_host="10.0.0.1",
        postgresql_port=5432,
        postgresql_database="acc_prod",
        postgresql_username="acc_admin",
        postgresql_password="SecretPassword123",
    )
    assert pg_db.database_url == "postgresql://acc_admin:SecretPassword123@10.0.0.1:5432/acc_prod"


def test_subsystem_default_values() -> None:
    app = ApplicationSettings()
    assert app.app_name == "ACC RMC AI Platform"

    sec = SecuritySettings()
    assert sec.jwt_algorithm == "HS256"

    ai = AISettings()
    assert ai.inference_batch_size == 64

    imp = ImportSettings()
    assert imp.duplicate_policy == DuplicatePolicy.QUARANTINE


def test_platform_settings_composition() -> None:
    ps = get_platform_settings()
    assert isinstance(ps, PlatformSettings)
    assert isinstance(ps.database, DatabaseSettings)
    assert isinstance(ps.security, SecuritySettings)
    assert isinstance(ps.ai, AISettings)


def test_subsystem_immutability() -> None:
    app = ApplicationSettings()
    with pytest.raises(TypeError):
        app.app_name = "New Name"  # type: ignore

    ps = get_platform_settings()
    with pytest.raises(TypeError):
        ps.app = ApplicationSettings()  # type: ignore
