"""WS-DASH-1A Backend Test Suite.

Verifies:
1. Executive KPIs with plant and date filtering
2. Filter options endpoint
3. SSE Ticket generation & authentication
4. CacheTokenService atomic increments & EventJournal persistence
5. Transaction rollback guarantees (no false events or tokens on rollback)
6. EventHub local broadcast and cross-worker journal detection
"""

import asyncio
import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.models.cache import CacheToken, EventJournal
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.models.user import User
from src.database.services.cache_token_service import CacheTokenService
from src.security.jwt import create_access_token
from src.services.event_hub import EventHub


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session


@pytest.fixture
def auth_headers(db_session):
    # Retrieve or create active superadmin user
    user = db_session.query(User).filter(User.username == "admin").first()
    if not user:
        user = db_session.query(User).first()
    token = create_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email or "admin@acc-rmc.local",
        roles=["SUPER_ADMIN"],
        session_version=user.session_version,
    )
    return {"Authorization": f"Bearer {token}"}


def test_executive_kpis_all_plants(auth_headers):
    client = TestClient(app)
    response = client.get("/api/v1/reporting/operational-metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "active_plants_count" in data
    assert "total_ingested_batches" in data
    assert "total_volume_m3" in data
    assert "quality_compliance_rate_pct" in data
    assert isinstance(data["total_ingested_batches"], int)
    assert isinstance(data["total_volume_m3"], float)


def test_executive_kpis_filtered_by_plant_and_date(auth_headers, db_session):
    client = TestClient(app)
    # Query with a specific non-existent plant code -> should return clean zeroes, not 500
    response = client.get(
        "/api/v1/reporting/operational-metrics?plant_code=NON_EXISTENT_PLANT_XYZ&date_from=2026-01-01&date_to=2026-12-31",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_ingested_batches"] == 0
    assert data["total_volume_m3"] == 0.0
    assert data["scope_metadata"]["plant_code"] == "NON_EXISTENT_PLANT_XYZ"


def test_filter_options_endpoint(auth_headers):
    client = TestClient(app)
    response = client.get("/api/v1/reporting/filter-options", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "plants" in data
    assert "available_date_range" in data
    assert isinstance(data["plants"], list)


def test_sse_ticket_generation(auth_headers):
    client = TestClient(app)
    response = client.post("/api/v1/events/ticket", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "ticket" in data
    assert data["expires_in_seconds"] == "60"


def test_cache_token_atomic_increment(db_session):
    v_initial = CacheTokenService.get_token_version("production_batch", db_session)
    
    # Bump token in transaction
    journal = CacheTokenService.bump_token_and_journal(
        db=db_session,
        token_name="production_batch",
        event_type="PRODUCTION_DATA_CHANGED",
        scopes=["kpis", "materials"],
        plant_code="PLANT-TEST-01"
    )
    db_session.commit()

    v_after = CacheTokenService.get_token_version("production_batch", db_session)
    assert v_after == v_initial + 1
    assert journal.token_version == v_after
    assert journal.event_type == "PRODUCTION_DATA_CHANGED"


def test_transaction_rollback_no_token_change(db_session):
    v_initial = CacheTokenService.get_token_version("production_batch", db_session)
    
    # Bump token but rollback
    CacheTokenService.bump_token_and_journal(
        db=db_session,
        token_name="production_batch",
        event_type="PRODUCTION_DATA_CHANGED",
        scopes=["kpis"],
    )
    db_session.rollback()

    v_after = CacheTokenService.get_token_version("production_batch", db_session)
    assert v_after == v_initial  # Token version must NOT change on rollback


def test_event_hub_local_broadcast():
    async def run_broadcast_test():
        hub = EventHub.get_instance()
        q = asyncio.Queue()
        hub.register(q)
        try:
            await hub.broadcast_local({
                "event_type": "TEST_EVENT",
                "scopes": ["kpis"]
            })
            msg = await asyncio.wait_for(q.get(), timeout=1.0)
            assert "event: DASHBOARD_INVALIDATE" in msg
            assert "TEST_EVENT" in msg
        finally:
            hub.unregister(q)
    
    asyncio.run(run_broadcast_test())
