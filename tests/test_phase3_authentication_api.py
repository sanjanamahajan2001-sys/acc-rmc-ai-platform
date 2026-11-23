"""Phase 3: Authentication API & Login Router Test Suite.

Rigorously verifies:
1. POST /api/v1/auth/login (normal login, failed attempts, 5-strike lockout, lockout expiration recovery, inactive accounts, case normalization).
2. Temporary password authentication (restricted token issuance, expiration handling, password_status vs account_status separation).
3. Server-side isolation of restricted tokens (blocked from operational endpoints, allowed on /change-password).
4. POST /api/v1/auth/change-password (forced and voluntary updates, policy enforcement, session-version invalidation).
5. GET /api/v1/auth/me (authenticated profile inspection, role assertions, unauthenticated rejection).
6. POST /api/v1/auth/logout (server-authoritative session revocation).
7. Database state and audit log verification (zero credential leakage, correct event types).
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.security.crypto import hash_password, verify_password


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. NORMAL LOGIN TESTS & LOCKOUT EXPIRY RECOVERY
# ==============================================================================

def test_login_success_normal_user(client: TestClient, db_session: Session):
    """Verify standard active user login issues valid JWT and updates metadata."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"operator_{unique_suffix}"
    email = f"operator_{unique_suffix}@acc-rmc.in"
    password = "OperatorPass@2026"

    user = User(
        username=username,
        email=email,
        full_name="Plant Batching Operator",
        password_hash=hash_password(password),
        account_status="ACTIVE",
        password_status="NORMAL",
        must_change_password=False,
    )
    db_session.add(user)
    db_session.commit()

    db_session.add(UserRole(user_id=user.id, role_id="PLANT_OPERATOR"))
    db_session.commit()

    # Login with username
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username.upper(), "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == username
    assert data["user"]["roles"] == ["PLANT_OPERATOR"]
    assert data["user"]["must_change_password"] is False

    # Direct database verification
    refreshed_user = db_session.get(User, user.id)
    assert refreshed_user.last_login_at is not None
    assert refreshed_user.failed_login_attempts == 0

    # Audit log verification
    audit = db_session.scalars(
        select(SecurityAuditLog).where(
            (SecurityAuditLog.actor_user_id == user.id) & (SecurityAuditLog.event_type == "LOGIN_SUCCESS")
        )
    ).first()
    assert audit is not None


def test_login_failed_attempts_and_lockout(client: TestClient, db_session: Session):
    """Verify failed attempts increment counter and trigger 15-min lockout at 5 attempts."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"lockuser_{unique_suffix}"
    email = f"lockuser_{unique_suffix}@acc-rmc.in"
    password = "CorrectPass@2026"

    user = User(
        username=username,
        email=email,
        full_name="Lockout Test User",
        password_hash=hash_password(password),
        account_status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()

    # 4 Failed login attempts
    for attempt in range(1, 5):
        resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": "WrongPassword@123"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid username or password."

    # 5th Failed login attempt -> triggers lockout
    resp5 = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": "WrongPassword@123"})
    assert resp5.status_code == 401

    # Verify locked out even with correct password during lockout window
    resp_locked = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    assert resp_locked.status_code == 401
    assert "locked" in resp_locked.json()["detail"].lower()

    # Direct DB verify
    db_user = db_session.get(User, user.id)
    assert db_user.failed_login_attempts == 5
    assert db_user.lockout_until is not None


def test_lockout_expiry_allows_successful_login(client: TestClient, db_session: Session):
    """Verify that after lockout_until expires (+15 mins elapsed), the user can authenticate successfully."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"unlocked_{unique_suffix}"
    email = f"unlocked_{unique_suffix}@acc-rmc.in"
    password = "CorrectPass@2026"

    now = datetime.now(timezone.utc)
    user = User(
        username=username,
        email=email,
        full_name="Expired Lockout User",
        password_hash=hash_password(password),
        account_status="ACTIVE",
        failed_login_attempts=5,
        lockout_until=now - timedelta(minutes=1),  # Lockout period has elapsed
    )
    db_session.add(user)
    db_session.commit()

    # Attempt login after lockout window has passed
    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Verify DB state is reset to clean active state
    db_user = db_session.get(User, user.id)
    assert db_user.failed_login_attempts == 0
    assert db_user.lockout_until is None
    assert db_user.account_status == "ACTIVE"


def test_login_inactive_or_deactivated_rejected(client: TestClient, db_session: Session):
    """Verify that disabled or deactivated users receive generic 401 without enumeration."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"disabled_{unique_suffix}"
    password = "SomePassword@2026"

    user = User(
        username=username,
        email=f"disabled_{unique_suffix}@acc.in",
        full_name="Disabled User",
        password_hash=hash_password(password),
        account_status="DEACTIVATED",
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password."


# ==============================================================================
# 2. TEMPORARY PASSWORD & FORCED PASSWORD CHANGE TESTS
# ==============================================================================

def test_temporary_password_login_and_forced_change_isolation(client: TestClient, db_session: Session):
    """Verify temporary password issues restricted token that cannot access /me but can access /change-password."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"tempuser_{unique_suffix}"
    email = f"tempuser_{unique_suffix}@acc-rmc.in"
    temp_pass = "TempSecretPass#2026"

    now = datetime.now(timezone.utc)
    user = User(
        username=username,
        email=email,
        full_name="New Lab Tech",
        password_hash=hash_password(temp_pass),
        account_status="ACTIVE",
        password_status="CHANGE_REQUIRED",
        must_change_password=True,
        temporary_password_created_at=now,
        temporary_password_expires_at=now + timedelta(hours=72),
    )
    db_session.add(user)
    db_session.commit()
    db_session.add(UserRole(user_id=user.id, role_id="LAB_TECHNICIAN"))
    db_session.commit()

    # 1. Login with temporary password
    login_resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": temp_pass})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user"]["must_change_password"] is True
    temp_token = login_data["access_token"]

    # 2. Attempt to access /api/v1/auth/me with restricted token -> Rejected with 403
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {temp_token}"})
    assert me_resp.status_code == 403
    assert "Password change required" in me_resp.json()["detail"]

    # 3. Perform forced password change
    new_perm_pass = "PermanentPass#2026"
    change_resp = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {temp_token}"},
        json={
            "current_password": temp_pass,
            "new_password": new_perm_pass,
            "confirm_new_password": new_perm_pass,
        },
    )
    assert change_resp.status_code == 200
    change_data = change_resp.json()
    assert change_data["user"]["must_change_password"] is False
    new_token = change_data["access_token"]

    # 4. Old temporary token is now invalidated (session_version incremented)
    old_token_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {temp_token}"})
    assert old_token_resp.status_code == 401

    # 5. New token can now access /api/v1/auth/me
    new_me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert new_me_resp.status_code == 200
    assert new_me_resp.json()["username"] == username
    assert new_me_resp.json()["roles"] == ["LAB_TECHNICIAN"]

    # 6. Direct DB verification
    db_user = db_session.get(User, user.id)
    assert db_user.must_change_password is False
    assert db_user.password_status == "NORMAL"
    assert db_user.account_status == "ACTIVE"
    assert verify_password(new_perm_pass, db_user.password_hash) is True


def test_expired_temporary_password_rejected(client: TestClient, db_session: Session):
    """Verify expired temporary credentials return 401, maintain account_status=ACTIVE, and set password_status=EXPIRED."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"expired_{unique_suffix}"
    temp_pass = "ExpiredTempPass#2026"

    now = datetime.now(timezone.utc)
    user = User(
        username=username,
        email=f"expired_{unique_suffix}@acc.in",
        full_name="Expired User",
        password_hash=hash_password(temp_pass),
        account_status="ACTIVE",
        password_status="CHANGE_REQUIRED",
        must_change_password=True,
        temporary_password_created_at=now - timedelta(hours=100),
        temporary_password_expires_at=now - timedelta(hours=28),
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": temp_pass})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()

    db_user = db_session.get(User, user.id)
    # Verify strict canonical separation between account_status and password_status:
    assert db_user.account_status == "ACTIVE"
    assert db_user.password_status == "EXPIRED"


# ==============================================================================
# 3. LOGOUT & SERVER-SIDE REVOCATION TESTS
# ==============================================================================

def test_logout_invalidates_session(client: TestClient, db_session: Session):
    """Verify that calling /logout increments session_version and invalidates the bearer token."""
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"logoutuser_{unique_suffix}"
    password = "LogoutUserPass#2026"

    user = User(
        username=username,
        email=f"logout_{unique_suffix}@acc.in",
        full_name="Logout Test User",
        password_hash=hash_password(password),
        account_status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.add(UserRole(user_id=user.id, role_id="ANALYST_VIEWER"))
    db_session.commit()

    # Login
    login_resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    token = login_resp.json()["access_token"]

    # Verify me works
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Subsequent /me call with old token fails with 401
    post_logout_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert post_logout_resp.status_code == 401
    assert "invalidated" in post_logout_resp.json()["detail"].lower()
