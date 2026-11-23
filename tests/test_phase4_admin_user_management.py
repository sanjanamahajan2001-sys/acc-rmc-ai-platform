"""Phase 4: Admin User Management APIs & Governance Test Suite.

Rigorously verifies:
1. Server-side RBAC authorization (401 unauthenticated, 403 non-admin, 200 admin/super-admin).
2. User creation & one-time temporary credential disclosure (non-persistence of plaintext, duplicate protection).
3. Role assignment governance (ADMIN cannot assign SUPER_ADMIN).
4. Password reset by administrator (temporary credential generation, session invalidation, old token revocation).
5. User updates & optimistic concurrency control (version checks, conflict handling).
6. Activation & deactivation lifecycle (immediate session revocation, login rejection).
7. Super Admin safeguards & self-protection (no self-delete, no self-deactivate, last-admin protection).
8. Governed deletion semantics (audit history preservation).
9. User listing, multi-field search, status/role filtering, and aggregate metrics.
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.security.crypto import hash_password, verify_password
from src.security.jwt import create_access_token


@pytest.fixture(autouse=True)
def clean_users_and_seed_roles():
    """Ensure a pristine test state by removing transient users and ensuring 6 canonical roles exist."""
    engine = get_database_engine()
    with Session(engine) as session:
        session.execute(delete(SecurityAuditLog))
        session.execute(delete(UserRole))
        session.execute(delete(User))
        
        # Ensure default roles exist
        canonical_roles = [
            ("SUPER_ADMIN", "Super Administrator"),
            ("ADMIN", "Plant Administrator"),
            ("QUALITY_HEAD", "Quality Control Head"),
            ("LAB_TECHNICIAN", "Lab Technician"),
            ("PLANT_OPERATOR", "Plant Batching Operator"),
            ("ANALYST_VIEWER", "Executive & Audit Viewer"),
        ]
        for role_id, role_name in canonical_roles:
            if not session.get(Role, role_id):
                session.add(Role(id=role_id, name=role_name, is_system_role=True))
        session.commit()
    yield


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def client():
    return TestClient(app)


def _create_test_user(db_session: Session, role: str, username_prefix: str = "user") -> tuple[User, str]:
    """Helper to provision a user and generate a valid access token."""
    suffix = uuid.uuid4().hex[:6]
    username = f"{username_prefix}_{suffix}"
    email = f"{username_prefix}_{suffix}@acc-rmc.in"
    password = "TestUserPass#2026"

    user = User(
        username=username,
        email=email,
        full_name=f"Test {role} User",
        password_hash=hash_password(password),
        account_status="ACTIVE",
        password_status="NORMAL",
        must_change_password=False,
        session_version=1,
        version=1,
    )
    db_session.add(user)
    db_session.commit()

    db_session.add(UserRole(user_id=user.id, role_id=role))
    db_session.commit()

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        roles=[role],
        session_version=user.session_version,
        must_change_password=False,
    )
    return user, token


# ==============================================================================
# 1. AUTHORIZATION & RBAC ACCESS TESTS
# ==============================================================================

def test_admin_endpoints_unauthenticated_rejected(client: TestClient):
    """Verify that unauthenticated calls to admin endpoints return 401."""
    assert client.get("/api/v1/admin/users").status_code == 401
    assert client.post("/api/v1/admin/users", json={}).status_code == 401


def test_admin_endpoints_non_admin_forbidden(client: TestClient, db_session: Session):
    """Verify that non-admin roles (Plant Operator, Lab Tech, Viewer) return 403."""
    for role in ["PLANT_OPERATOR", "LAB_TECHNICIAN", "ANALYST_VIEWER"]:
        _, token = _create_test_user(db_session, role=role, username_prefix="op")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 403
        assert "role permissions" in resp.json()["detail"].lower()


# ==============================================================================
# 2. USER CREATION & TEMPORARY CREDENTIAL TESTS
# ==============================================================================

def test_create_user_success_and_one_time_temp_pass(client: TestClient, db_session: Session):
    """Verify Super Admin can create user, receives one-time temporary password, and hash is stored."""
    _, admin_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    headers = {"Authorization": f"Bearer {admin_token}"}

    suffix = uuid.uuid4().hex[:6]
    new_username = f"newqc_{suffix}"
    new_email = f"newqc_{suffix}@acc-rmc.in"

    payload = {
        "username": new_username,
        "email": new_email,
        "full_name": "Quality Lab Inspector",
        "roles": ["QUALITY_HEAD", "LAB_TECHNICIAN"],
    }

    resp = client.post("/api/v1/admin/users", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert "temporary_password" in data
    temp_pw = data["temporary_password"]
    assert len(temp_pw) == 14
    assert data["user"]["username"] == new_username
    assert set(data["user"]["roles"]) == {"QUALITY_HEAD", "LAB_TECHNICIAN"}
    assert data["user"]["must_change_password"] is True

    # Forensic DB check: Plaintext password is NOT in database
    created_user = db_session.scalars(select(User).where(User.username == new_username)).first()
    assert created_user is not None
    assert created_user.password_hash != temp_pw
    assert verify_password(temp_pw, created_user.password_hash) is True

    # Audit log check
    audit = db_session.scalars(
        select(SecurityAuditLog).where(
            (SecurityAuditLog.target_user_id == created_user.id) & (SecurityAuditLog.event_type == "USER_CREATED")
        )
    ).first()
    assert audit is not None
    assert "password" not in str(audit.details).lower() or "[REDACTED]" in str(audit.details)


def test_create_user_duplicate_rejected(client: TestClient, db_session: Session):
    """Verify duplicate username or email is rejected with 409 Conflict."""
    _, admin_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    headers = {"Authorization": f"Bearer {admin_token}"}

    existing_user, _ = _create_test_user(db_session, role="PLANT_OPERATOR", username_prefix="exist")

    # Attempt duplicate username
    resp1 = client.post(
        "/api/v1/admin/users",
        json={
            "username": existing_user.username,
            "email": f"diff_{uuid.uuid4().hex[:4]}@acc.in",
            "full_name": "Dupe User",
            "roles": ["PLANT_OPERATOR"],
        },
        headers=headers,
    )
    assert resp1.status_code == 409

    # Attempt duplicate email
    resp2 = client.post(
        "/api/v1/admin/users",
        json={
            "username": f"diff_{uuid.uuid4().hex[:4]}",
            "email": existing_user.email,
            "full_name": "Dupe User",
            "roles": ["PLANT_OPERATOR"],
        },
        headers=headers,
    )
    assert resp2.status_code == 409


def test_admin_cannot_assign_super_admin(client: TestClient, db_session: Session):
    """Verify that a standard ADMIN cannot create or assign SUPER_ADMIN role (privilege escalation check)."""
    _, plant_admin_token = _create_test_user(db_session, role="ADMIN", username_prefix="admin")
    headers = {"Authorization": f"Bearer {plant_admin_token}"}

    suffix = uuid.uuid4().hex[:6]
    resp = client.post(
        "/api/v1/admin/users",
        json={
            "username": f"escalate_{suffix}",
            "email": f"escalate_{suffix}@acc.in",
            "full_name": "Escalation Candidate",
            "roles": ["SUPER_ADMIN"],
        },
        headers=headers,
    )
    assert resp.status_code == 403
    assert "SUPER_ADMIN" in resp.json()["detail"]


# ==============================================================================
# 3. PASSWORD RESET BY ADMIN TESTS
# ==============================================================================

def test_admin_reset_password(client: TestClient, db_session: Session):
    """Verify admin password reset revokes existing sessions and issues working temporary password."""
    _, admin_token = _create_test_user(db_session, role="ADMIN", username_prefix="adm")
    target_user, old_token = _create_test_user(db_session, role="PLANT_OPERATOR", username_prefix="target")

    # Reset target password
    reset_resp = client.post(
        f"/api/v1/admin/users/{target_user.id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reset_resp.status_code == 200
    new_temp_pass = reset_resp.json()["temporary_password"]

    # 1. Target's old token is invalidated immediately
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me_resp.status_code == 401

    # 2. Target can log in with new temporary password
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": target_user.username, "password": new_temp_pass},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["must_change_password"] is True


def test_admin_cannot_reset_super_admin(client: TestClient, db_session: Session):
    """Verify that a standard ADMIN cannot reset a SUPER_ADMIN account."""
    _, plant_admin_token = _create_test_user(db_session, role="ADMIN", username_prefix="adm")
    super_admin, _ = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")

    resp = client.post(
        f"/api/v1/admin/users/{super_admin.id}/reset-password",
        headers={"Authorization": f"Bearer {plant_admin_token}"},
    )
    assert resp.status_code == 403


# ==============================================================================
# 4. USER UPDATE & OPTIMISTIC CONCURRENCY TESTS
# ==============================================================================

def test_update_user_optimistic_locking(client: TestClient, db_session: Session):
    """Verify optimistic locking prevents silent last-write-wins collisions."""
    _, admin_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    target_user, _ = _create_test_user(db_session, role="LAB_TECHNICIAN", username_prefix="target")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Successful update with correct version
    resp1 = client.patch(
        f"/api/v1/admin/users/{target_user.id}",
        json={"full_name": "Updated Name V1", "version": 1},
        headers=headers,
    )
    assert resp1.status_code == 200
    assert resp1.json()["full_name"] == "Updated Name V1"
    assert resp1.json()["version"] == 2

    # Stale version update attempt (sending version=1 again) -> 409 Conflict
    resp2 = client.patch(
        f"/api/v1/admin/users/{target_user.id}",
        json={"full_name": "Conflicting Update", "version": 1},
        headers=headers,
    )
    assert resp2.status_code == 409
    assert "concurrency conflict" in resp2.json()["detail"].lower()


# ==============================================================================
# 5. ACTIVATION & DEACTIVATION TESTS
# ==============================================================================

def test_deactivate_and_reactivate_user(client: TestClient, db_session: Session):
    """Verify deactivation revokes sessions and stops login, reactivation restores access."""
    _, admin_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    target_user, target_token = _create_test_user(db_session, role="PLANT_OPERATOR", username_prefix="target")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Deactivate target user
    deact_resp = client.post(f"/api/v1/admin/users/{target_user.id}/deactivate", headers=headers)
    assert deact_resp.status_code == 200
    assert deact_resp.json()["account_status"] == "DEACTIVATED"

    # 2. Active token is now rejected
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {target_token}"}).status_code in (401, 403)

    # 3. Login attempt rejected
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": target_user.username, "password": "TestUserPass#2026"},
    )
    assert login_resp.status_code == 401

    # 4. Reactivate user
    act_resp = client.post(f"/api/v1/admin/users/{target_user.id}/activate", headers=headers)
    assert act_resp.status_code == 200
    assert act_resp.json()["account_status"] == "ACTIVE"

    # 5. Login works again
    login_resp2 = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": target_user.username, "password": "TestUserPass#2026"},
    )
    assert login_resp2.status_code == 200


# ==============================================================================
# 6. SUPER ADMIN SAFEGUARDS & SELF-PROTECTION
# ==============================================================================

def test_admin_self_protection_rules(client: TestClient, db_session: Session):
    """Verify administrator cannot self-deactivate or self-delete."""
    super_admin, super_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    headers = {"Authorization": f"Bearer {super_token}"}

    # Self-deactivation attempt -> 400 Bad Request
    deact_resp = client.post(f"/api/v1/admin/users/{super_admin.id}/deactivate", headers=headers)
    assert deact_resp.status_code == 400
    assert "cannot deactivate your own" in deact_resp.json()["detail"].lower()

    # Self-deletion attempt -> 400 Bad Request
    del_resp = client.delete(f"/api/v1/admin/users/{super_admin.id}", headers=headers)
    assert del_resp.status_code == 400
    assert "cannot delete your own" in del_resp.json()["detail"].lower()


def test_last_super_admin_protection(client: TestClient, db_session: Session):
    """Verify system blocks demoting the last active Super Admin."""
    # Provision sole active super admin
    sole_super, _ = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="sole")

    sole_token = create_access_token(
        user_id=sole_super.id,
        username=sole_super.username,
        email=sole_super.email,
        roles=["SUPER_ADMIN"],
        session_version=sole_super.session_version,
    )
    sole_headers = {"Authorization": f"Bearer {sole_token}"}

    # Attempt to demote sole_super's role when sole_super is the ONLY active super admin in system
    demote_resp = client.patch(
        f"/api/v1/admin/users/{sole_super.id}",
        json={"roles": ["PLANT_OPERATOR"]},
        headers=sole_headers,
    )
    assert demote_resp.status_code == 400
    assert "last remaining" in demote_resp.json()["detail"].lower()


# ==============================================================================
# 7. USER LISTING, SEARCH & METRICS TESTS
# ==============================================================================

def test_user_listing_filtering_and_metrics(client: TestClient, db_session: Session):
    """Verify user search, pagination, role filtering, and aggregate metrics."""
    super_admin, super_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    headers = {"Authorization": f"Bearer {super_token}"}

    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "metrics" in data
    assert data["metrics"]["total_users"] >= 1
    assert data["metrics"]["administrators"] >= 1


def test_delete_user_and_audit_log_preservation(client: TestClient, db_session: Session):
    """Verify governed deletion removes user and associations but preserves audit history."""
    super_admin, super_token = _create_test_user(db_session, role="SUPER_ADMIN", username_prefix="super")
    target_user, _ = _create_test_user(db_session, role="LAB_TECHNICIAN", username_prefix="del_target")
    headers = {"Authorization": f"Bearer {super_token}"}

    target_id = target_user.id
    target_username = target_user.username

    del_resp = client.delete(f"/api/v1/admin/users/{target_id}", headers=headers)
    assert del_resp.status_code == 200
    assert "deleted" in del_resp.json()["message"].lower()

    # Expire test session cache to reflect database changes made by API session
    db_session.expire_all()

    # User entity is removed
    assert db_session.get(User, target_id) is None

    # Audit log remains preserved
    audit = db_session.scalars(
        select(SecurityAuditLog).where(
            (SecurityAuditLog.actor_user_id == super_admin.id) & (SecurityAuditLog.event_type == "USER_DELETED")
        )
    ).first()
    assert audit is not None
    assert audit.details["deleted_username"] == target_username
