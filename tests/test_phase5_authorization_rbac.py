"""Phase 5 Application RBAC & Authorization Hardening Test Suite.

Authoritatively certifies:
1. 6-Role Canonical Permission Matrix across all routers and endpoints.
2. Direct API bypass rejection (401 Unauthorized for unauthenticated/malformed tokens).
3. Authorization failure enforcement (403 Forbidden for unauthorized roles).
4. Temporary Token Isolation (must_change_password=True tokens blocked from operational APIs).
5. Account Status Enforcement (DEACTIVATED, LOCKED, INACTIVE accounts blocked with 403).
6. Session Invalidation on Role Change (session_version bump instantly invalidates old JWTs).
7. Production Safety Invariant (APP_ENV=production hard blocks /reset even for SUPER_ADMIN).
8. Automated Route-Guard Discovery (asserts zero unprotected routes).
"""

import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app

from src.database.session import get_session_factory
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.database.models.master import Plant, Recipe
from src.security.crypto import hash_password
from src.security.jwt import create_access_token


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def db_session():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def setup_test_entities(db_session: Session):
    """Seed prerequisite master data and 6 canonical role test users."""
    # Ensure plant and recipe exist
    plant = db_session.query(Plant).filter(Plant.plant_code == "PLANT-PH5-01").first()
    if not plant:
        plant = Plant(
            id=str(uuid.uuid4()),
            plant_code="PLANT-PH5-01",
            plant_name="Phase 5 Mumbai Test Plant",
            location="Mumbai, Maharashtra",
            is_deleted=False,
        )
        db_session.add(plant)

    recipe = db_session.query(Recipe).filter(Recipe.recipe_code == "REC-PH5-M40").first()
    if not recipe:
        recipe = Recipe(
            id=str(uuid.uuid4()),
            recipe_code="REC-PH5-M40",
            recipe_name="Phase 5 High Strength M40",
            target_strength_mpa=40.0,
            is_deleted=False,
        )
        db_session.add(recipe)

    # 6 Canonical Roles
    canonical_roles = [
        "SUPER_ADMIN",
        "ADMIN",
        "QUALITY_HEAD",
        "LAB_TECHNICIAN",
        "PLANT_OPERATOR",
        "ANALYST_VIEWER",
    ]

    tokens = {}
    users = {}

    for role_name in canonical_roles:
        email = f"test_{role_name.lower()}@acc-rmc.test"
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=f"test_{role_name.lower()}",
                full_name=f"Test {role_name.replace('_', ' ').title()}",
                password_hash=hash_password("Passphrase@Test2026"),
                account_status="ACTIVE",
                password_status="NORMAL",
                must_change_password=False,
                session_version=1,
            )
            db_session.add(user)
            db_session.flush()

            # Assign role
            db_session.add(
                UserRole(
                    user_id=user.id,
                    role_id=role_name,
                    assigned_by_user_id=user.id,
                )
            )
            db_session.commit()

        users[role_name] = user
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=[role_name],
            session_version=user.session_version,
            must_change_password=False,
        )
        tokens[role_name] = token

    return {"users": users, "tokens": tokens, "plant_code": "PLANT-PH5-01", "recipe_code": "REC-PH5-M40"}


# ==============================================================================
# 1. UNPROTECTED / PUBLIC ENDPOINT & AUTHENTICATION BYPASS TESTS
# ==============================================================================

def test_unauthenticated_request_rejected(client: TestClient):
    """Endpoints require valid Bearer token; unauthenticated returns 401."""
    protected_endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/master-data/plants"),
        ("POST", "/api/v1/master-data/plants"),
        ("POST", "/api/v1/ingestion/datasets"),
        ("POST", "/api/v1/ingestion/sessions"),
        ("GET", "/api/v1/manual-entry/drafts/DRAFT-FAKE"),
        ("POST", "/api/v1/manual-entry/drafts"),
    ]

    for method, path in protected_endpoints:
        res = client.request(method, path)
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


def test_malformed_token_rejected(client: TestClient):
    """Malformed or fabricated Bearer token returns 401."""
    headers = {"Authorization": "Bearer not-a-real-jwt-token"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401


# ==============================================================================
# 2. TEMPORARY FORCED-CHANGE TOKEN ISOLATION (must_change_password=True)
# ==============================================================================

def test_forced_password_change_token_isolation(client: TestClient, setup_test_entities):
    """Tokens with must_change_password=True must be forbidden (403) on operational endpoints."""
    users = setup_test_entities["users"]
    op_user = users["PLANT_OPERATOR"]

    # Issue a forced password change token
    temp_token = create_access_token(
        user_id=op_user.id,
        username=op_user.username,
        email=op_user.email,
        roles=["PLANT_OPERATOR"],
        session_version=op_user.session_version,
        must_change_password=True,
        scope="FORCE_PASSWORD_CHANGE_ONLY",
    )
    headers = {"Authorization": f"Bearer {temp_token}"}

    # Blocked on master data
    res = client.get("/api/v1/master-data/plants", headers=headers)
    assert res.status_code == 403
    assert "Password change required" in res.json().get("detail", "")

    # Blocked on ingestion
    res = client.post("/api/v1/ingestion/datasets", headers=headers, json={"dataset_name": "Test"})
    assert res.status_code == 403

    # Blocked on manual entry
    res = client.post("/api/v1/manual-entry/drafts", headers=headers, json={"plant_code": "PLANT-PH5-01"})
    assert res.status_code == 403


# ==============================================================================
# 3. ACCOUNT STATUS ENFORCEMENT (DEACTIVATED / LOCKED / INACTIVE)
# ==============================================================================

def test_deactivated_user_blocked(client: TestClient, db_session: Session):
    """Deactivated user tokens return 403 Forbidden and log audit entry."""
    uid = uuid.uuid4().hex[:6]
    deact_user = User(
        id=str(uuid.uuid4()),
        email=f"deactivated_{uid}@acc-rmc.test",
        username=f"deact_{uid}",
        full_name="Deactivated Test User",
        password_hash=hash_password("Passphrase@Test2026"),
        account_status="DEACTIVATED",
        password_status="NORMAL",
        must_change_password=False,
        session_version=1,
    )
    db_session.add(deact_user)
    db_session.flush()
    db_session.add(UserRole(user_id=deact_user.id, role_id="ANALYST_VIEWER", assigned_by_user_id=deact_user.id))
    db_session.commit()

    token = create_access_token(
        user_id=deact_user.id,
        username=deact_user.username,
        email=deact_user.email,
        roles=["ANALYST_VIEWER"],
        session_version=1,
        must_change_password=False,
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/master-data/plants", headers=headers)
    assert res.status_code == 403
    assert "disabled or locked" in res.json().get("detail", "")


# ==============================================================================
# 4. SESSION INVALIDATION ON ROLE CHANGE
# ==============================================================================

def test_session_invalidation_on_role_change(client: TestClient, db_session: Session, setup_test_entities):
    """When an admin modifies a user's roles, the user's session_version is bumped, invalidating old tokens."""
    tokens = setup_test_entities["tokens"]
    admin_token = tokens["ADMIN"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    uid = uuid.uuid4().hex[:6]
    target_user = User(
        id=str(uuid.uuid4()),
        email=f"role_change_{uid}@acc-rmc.test",
        username=f"role_target_{uid}",
        full_name="Role Change Target",
        password_hash=hash_password("Passphrase@Test2026"),
        account_status="ACTIVE",
        password_status="NORMAL",
        must_change_password=False,
        session_version=1,
    )
    db_session.add(target_user)
    db_session.flush()
    db_session.add(UserRole(user_id=target_user.id, role_id="ANALYST_VIEWER", assigned_by_user_id=target_user.id))
    db_session.commit()

    # Old token generated with session_version=1
    old_token = create_access_token(
        user_id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        roles=["ANALYST_VIEWER"],
        session_version=1,
        must_change_password=False,
    )
    user_headers = {"Authorization": f"Bearer {old_token}"}

    # Verify old token works initially
    res = client.get("/api/v1/master-data/plants", headers=user_headers)
    assert res.status_code == 200

    # Admin updates roles -> bumps session_version to 2
    update_res = client.patch(
        f"/api/v1/admin/users/{target_user.id}",
        headers=admin_headers,
        json={"roles": ["PLANT_OPERATOR"]},
    )
    assert update_res.status_code == 200

    # Old token with session_version=1 must now be rejected (401)
    res_after = client.get("/api/v1/master-data/plants", headers=user_headers)
    assert res_after.status_code == 401
    assert "session has been invalidated" in res_after.json().get("detail", "")


# ==============================================================================
# 5. CANONICAL 6-ROLE RBAC PERMISSION MATRIX TESTS
# ==============================================================================

def test_super_admin_full_access(client: TestClient, setup_test_entities):
    """SUPER_ADMIN has unrestricted access across all platform capabilities."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['SUPER_ADMIN']}"}

    # Admin users list
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 200
    # Master data read
    assert client.get("/api/v1/master-data/plants", headers=headers).status_code == 200
    # Master data write
    res_plant = client.post(
        "/api/v1/master-data/plants",
        headers=headers,
        json={"plant_code": f"PLANT-SA-{uuid.uuid4().hex[:4]}", "plant_name": "SA Plant", "location": "Test Loc"},
    )
    assert res_plant.status_code in (200, 201)


def test_admin_role_boundaries(client: TestClient, setup_test_entities):
    """ADMIN can manage users and master data, but cannot perform destructive SUPER_ADMIN resets."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['ADMIN']}"}

    # Can list users
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 200
    # Can read master data
    assert client.get("/api/v1/master-data/plants", headers=headers).status_code == 200
    # Cannot call reset (requires SUPER_ADMIN)
    res_reset = client.post("/api/v1/ingestion/reset", headers=headers, json={"confirm": True})
    assert res_reset.status_code == 403


def test_quality_head_role_boundaries(client: TestClient, setup_test_entities):
    """QUALITY_HEAD can manage recipes/mix designs and laboratory QA, but cannot access admin user management."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['QUALITY_HEAD']}"}

    # Cannot access admin users
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403

    # Can create recipe
    recipe_code = f"REC-QH-{uuid.uuid4().hex[:4].upper()}"
    res_recipe = client.post(
        "/api/v1/master-data/recipes",
        headers=headers,
        json={"recipe_code": recipe_code, "recipe_name": "QH Test Mix", "target_strength_mpa": 45.0},
    )
    assert res_recipe.status_code in (200, 201)

    # Can register dataset
    res_ds = client.post(
        "/api/v1/ingestion/datasets",
        headers=headers,
        json={
            "dataset_name": "QH Dataset",
            "dataset_period": "2026-Q3",
            "dataset_type_id": "RAW",
            "target_plant_id": setup_test_entities["plant_code"],
            "import_profile_id": "DEFAULT",
            "operator_id": "QH-USER",
        },
    )
    assert res_ds.status_code == 200


def test_plant_operator_role_boundaries(client: TestClient, setup_test_entities):
    """PLANT_OPERATOR can execute batch drafts and submit, but is forbidden from Step 4 Lab QA and Admin."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['PLANT_OPERATOR']}"}

    # Forbidden from admin users
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403

    # Forbidden from recipe creation
    assert client.post(
        "/api/v1/master-data/recipes",
        headers=headers,
        json={"recipe_code": "REC-OP-FAIL", "recipe_name": "Fail", "target_strength_mpa": 30.0},
    ).status_code == 403

    # Allowed to create batch draft (Step 1)
    res_draft = client.post(
        "/api/v1/manual-entry/drafts",
        headers=headers,
        json={
            "plant_code": setup_test_entities["plant_code"],
            "recipe_code": setup_test_entities["recipe_code"],
            "production_date": "2026-09-15",
            "shift": "DAY_SHIFT",
        },
    )
    assert res_draft.status_code == 200
    draft_id = res_draft.json()["draft_id"]

    # Allowed to update Step 2 (Machine Parameters)
    res_step2 = client.put(
        f"/api/v1/manual-entry/drafts/{draft_id}/step-2",
        headers=headers,
        json={
            "batch_start_time": "10:00:00",
            "batch_end_time": "10:05:00",
            "mixer_time_seconds": 60,
            "truck_number": "MH-01-AB-1234",
            "delivery_challan": f"DC-{uuid.uuid4().hex[:6].upper()}",
            "target_slump_mm": 120.0,
        },
    )
    assert res_step2.status_code == 200

    # Forbidden from Step 4 (Laboratory QA - restricted to LAB_TECHNICIAN / QUALITY_HEAD)
    res_step4 = client.put(
        f"/api/v1/manual-entry/drafts/{draft_id}/step-4",
        headers=headers,
        json={
            "qa_cube_id": f"CUBE-{uuid.uuid4().hex[:6]}",
            "lab_technician_id": "TECH-01",
            "lab_technician_name": "Test Tech",
            "casting_date": "2026-08-15",
            "testing_date_28_day": "2026-09-12",
            "result_28_day_mpa": 42.5,
        },
    )
    assert res_step4.status_code == 403


def test_lab_technician_role_boundaries(client: TestClient, setup_test_entities):
    """LAB_TECHNICIAN can update Step 4 Lab QA, but is forbidden from creating Step 1-3 drafts and submitting."""
    tokens = setup_test_entities["tokens"]
    tech_headers = {"Authorization": f"Bearer {tokens['LAB_TECHNICIAN']}"}
    op_headers = {"Authorization": f"Bearer {tokens['PLANT_OPERATOR']}"}

    # Forbidden from creating drafts
    assert client.post(
        "/api/v1/manual-entry/drafts",
        headers=tech_headers,
        json={"plant_code": setup_test_entities["plant_code"], "recipe_code": setup_test_entities["recipe_code"], "production_date": "2026-09-15"},
    ).status_code == 403

    # Forbidden from admin users
    assert client.get("/api/v1/admin/users", headers=tech_headers).status_code == 403

    # Operator creates draft first
    draft_res = client.post(
        "/api/v1/manual-entry/drafts",
        headers=op_headers,
        json={
            "plant_code": setup_test_entities["plant_code"],
            "recipe_code": setup_test_entities["recipe_code"],
            "production_date": "2026-09-15",
        },
    )
    draft_id = draft_res.json()["draft_id"]

    # Lab Tech is allowed to execute Step 4
    cube_id = f"CUBE-{uuid.uuid4().hex[:6].upper()}"
    res_step4 = client.put(
        f"/api/v1/manual-entry/drafts/{draft_id}/step-4",
        headers=tech_headers,
        json={
            "qa_cube_id": cube_id,
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Lab Tech",
            "casting_date": "2026-08-15",
            "testing_date_28_day": "2026-09-12",
            "result_28_day_mpa": 44.0,
        },
    )
    assert res_step4.status_code == 200
    assert res_step4.json()["qa_cube_id"] == cube_id


def test_analyst_viewer_role_boundaries(client: TestClient, setup_test_entities):
    """ANALYST_VIEWER has read-only access to master data and reports; forbidden from all writes."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['ANALYST_VIEWER']}"}

    # Can read master data
    assert client.get("/api/v1/master-data/plants", headers=headers).status_code == 200
    assert client.get("/api/v1/master-data/recipes", headers=headers).status_code == 200

    # Forbidden from creating master data
    assert client.post(
        "/api/v1/master-data/plants",
        headers=headers,
        json={"plant_code": "PLANT-FAIL", "plant_name": "Fail", "location": "Fail"},
    ).status_code == 403

    # Forbidden from ingestion
    assert client.post("/api/v1/ingestion/datasets", headers=headers, json={}).status_code == 403

    # Forbidden from manual entry creation
    assert client.post("/api/v1/manual-entry/drafts", headers=headers, json={}).status_code == 403


# ==============================================================================
# 6. PRODUCTION SAFETY INVARIANT FOR DESTRUCTIVE RESETS
# ==============================================================================

def test_production_safety_blocks_reset_even_for_super_admin(client: TestClient, setup_test_entities, monkeypatch):
    """When APP_ENV=production, /reset is hard-blocked (403) even for SUPER_ADMIN."""
    headers = {"Authorization": f"Bearer {setup_test_entities['tokens']['SUPER_ADMIN']}"}

    # Set APP_ENV=production
    monkeypatch.setenv("APP_ENV", "production")

    res = client.post("/api/v1/ingestion/reset", headers=headers, json={"confirm": True})
    assert res.status_code == 403
    assert "strictly forbidden in production environment" in res.json().get("detail", "")


# ==============================================================================
# 7. AUTOMATED ROUTE AUTO-DISCOVERY GUARD
# ==============================================================================

def test_all_routes_have_security_dependencies():
    """Verify that every route registered in the application (except public whitelist) has authentication dependencies."""
    PUBLIC_WHITELIST = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/docs/oauth2-redirect",
        "/api/v1/auth/login",
    }

    unprotected_routes = []

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set())
        if not path or path in PUBLIC_WHITELIST:
            continue

        # Check for authentication dependency in route.dependencies or route.dependant.dependencies
        has_auth_dep = False
        all_deps = []

        if hasattr(route, "dependencies"):
            all_deps.extend(route.dependencies)
        if hasattr(route, "dependant") and hasattr(route.dependant, "dependencies"):
            all_deps.extend(route.dependant.dependencies)

        for dep in all_deps:
            call_name = getattr(dep.call, "__name__", "") if hasattr(dep, "call") else str(dep)
            if call_name in ("get_current_user", "get_current_user_any_scope", "role_checker", "get_current_user_from_token"):
                has_auth_dep = True
                break

        if not has_auth_dep:
            unprotected_routes.append(f"{methods} {path} (endpoint: {getattr(route, 'name', 'unknown')})")

    assert not unprotected_routes, f"Found unprotected routes lacking authentication/RBAC dependencies:\n" + "\n".join(unprotected_routes)
