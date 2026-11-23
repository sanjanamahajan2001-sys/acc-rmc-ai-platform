"""Unit & Integration Tests for Settings DB Preview & SQL Export."""

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.api.main import app
from src.database.session import get_session_factory
from src.database.models.user import User
from src.services.database_preview_service import DatabasePreviewService
from src.security.jwt import create_access_token


@pytest.fixture
def db_session():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(db_session: Session):
    admin = db_session.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = db_session.query(User).first()
    token = create_access_token(
        user_id=str(admin.id),
        username=admin.username,
        email=admin.email or "admin@acc-rmc.in",
        roles=["SUPER_ADMIN", "ADMIN"],
        session_version=admin.session_version,
    )
    return {"Authorization": f"Bearer {token}"}


class TestDatabasePreviewAndExport:
    """Test suite for live database introspection and DDL export."""

    def test_database_preview_service_introspection(self, db_session: Session):
        """Verify dynamic discovery of tables, columns, PKs, and FKs."""
        preview = DatabasePreviewService.get_database_preview(db=db_session)

        assert preview.overview.public_tables_count > 0
        assert preview.overview.total_columns_count > 0
        assert preview.overview.database_name is not None
        assert len(preview.tables) == preview.overview.public_tables_count

        # Check sample table structure
        table_names = [t.name for t in preview.tables]
        assert "usr_users" in table_names or "audit_logs" in table_names or "alembic_version" in table_names

        # Validate column structure
        for t in preview.tables:
            assert t.column_count == len(t.columns)
            assert t.foreign_relations_count == len(t.foreign_keys)
            for col in t.columns:
                assert col.name is not None
                assert col.type is not None

    def test_generate_sql_ddl_export(self, db_session: Session):
        """Verify dynamic generation of clean, valid SQL DDL."""
        export = DatabasePreviewService.generate_sql_ddl_export(db=db_session)

        assert export.tables_count > 0
        assert export.filename.endswith(".sql")
        assert len(export.sql_ddl) > 1000
        assert "CREATE TABLE IF NOT EXISTS" in export.sql_ddl
        assert "CONSTRAINT pk_" in export.sql_ddl

    def test_settings_api_preview_authenticated(self, client: TestClient, auth_headers: dict):
        """Verify GET /settings/database/preview returns 200 with valid structure."""
        resp = client.get(
            "/api/v1/settings/database/preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overview" in data
        assert "tables" in data
        assert data["overview"]["public_tables_count"] > 0
        assert len(data["tables"]) == data["overview"]["public_tables_count"]

    def test_settings_api_export_sql_authenticated(self, client: TestClient, auth_headers: dict):
        """Verify GET /settings/database/export/sql returns 200 with SQL DDL."""
        resp = client.get(
            "/api/v1/settings/database/export/sql",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sql_ddl" in data
        assert "filename" in data
        assert data["sql_ddl"].startswith("-- ==")

    def test_settings_api_export_sql_download(self, client: TestClient, auth_headers: dict):
        """Verify GET /settings/database/export/sql/download streams .sql attachment."""
        resp = client.get(
            "/api/v1/settings/database/export/sql/download",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "") or "application/sql" in resp.headers.get("content-type", "")
        assert "attachment; filename=" in resp.headers.get("content-disposition", "")
        assert len(resp.content) > 1000

    def test_settings_api_unauthorized_rejection(self, client: TestClient):
        """Verify unauthenticated requests are rejected with 401."""
        resp = client.get("/api/v1/settings/database/preview")
        assert resp.status_code in (401, 403)
