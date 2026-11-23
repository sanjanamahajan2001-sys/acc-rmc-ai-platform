"""Enterprise AI Mix Optimization Recommendation Governance & Human Review Gate Tests (Phase 5E).

Verifies deterministic governance gating, role-based authorization, infeasible quarantine,
human review transitions, audit logging, partial pricing, and frozen boundary preservation.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api.main import app
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import Role, SecurityAuditLog, User, UserRole
from src.database.session import get_session_factory
from src.security.crypto import hash_password
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
def quality_head_user(db_session):
    user = db_session.query(User).filter(User.username == "test_quality_head_5e").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="test_quality_head_5e",
            email="qualityhead5e@acc-rmc.in",
            full_name="Quality Head Reviewer",
            password_hash=hash_password("Pass@123456"),
            account_status="ACTIVE",
            password_status="NORMAL",
            must_change_password=False,
            session_version=1,
        )
        db_session.add(user)
        db_session.flush()

        role = db_session.query(Role).filter(Role.id == "QUALITY_HEAD").first()
        if not role:
            role = Role(id="QUALITY_HEAD", name="Quality Head", is_system_role=True)
            db_session.add(role)
            db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id="QUALITY_HEAD"))
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = db_session.query(User).filter(User.username == "test_admin_5e").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="test_admin_5e",
            email="admin5e@acc-rmc.in",
            full_name="Plant Admin Reviewer",
            password_hash=hash_password("Pass@123456"),
            account_status="ACTIVE",
            password_status="NORMAL",
            must_change_password=False,
            session_version=1,
        )
        db_session.add(user)
        db_session.flush()

        role = db_session.query(Role).filter(Role.id == "ADMIN").first()
        if not role:
            role = Role(id="ADMIN", name="Admin", is_system_role=True)
            db_session.add(role)
            db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id="ADMIN"))
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session):
    user = db_session.query(User).filter(User.username == "test_viewer_5e").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="test_viewer_5e",
            email="viewer5e@acc-rmc.in",
            full_name="Viewer Analyst",
            password_hash=hash_password("Pass@123456"),
            account_status="ACTIVE",
            password_status="NORMAL",
            must_change_password=False,
            session_version=1,
        )
        db_session.add(user)
        db_session.flush()

        role = db_session.query(Role).filter(Role.id == "ANALYST_VIEWER").first()
        if not role:
            role = Role(id="ANALYST_VIEWER", name="Analyst Viewer", is_system_role=True)
            db_session.add(role)
            db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id="ANALYST_VIEWER"))
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def quality_head_token(quality_head_user):
    return create_access_token(
        user_id=str(quality_head_user.id),
        username=quality_head_user.username,
        email=quality_head_user.email,
        roles=["QUALITY_HEAD"],
        session_version=quality_head_user.session_version,
    )


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(
        user_id=str(admin_user.id),
        username=admin_user.username,
        email=admin_user.email,
        roles=["ADMIN"],
        session_version=admin_user.session_version,
    )


@pytest.fixture
def viewer_token(viewer_user):
    return create_access_token(
        user_id=str(viewer_user.id),
        username=viewer_user.username,
        email=viewer_user.email,
        roles=["ANALYST_VIEWER"],
        session_version=viewer_user.session_version,
    )


@pytest.fixture
def sample_optimization_run(db_session, quality_head_user):
    """Create a persistent OptimizationRun with feasible, non-Pareto, and infeasible candidates."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    run = OptimizationRun(
        id=run_id,
        recipe_id=str(uuid.uuid4()),
        recipe_code="M30-PUMP-5E",
        plant_code="PLANT-KUDL-01",
        optimization_objective="MINIMIZE_COST",
        run_status="SUCCESS",
        recipe_snapshot_json={
            "recipe_id": str(uuid.uuid4()),
            "recipe_code": "M30-PUMP-5E",
            "plant_code": "PLANT-KUDL-01",
            "grade": "M30",
            "exposure_class": "NORMAL",
            "nominal_max_aggregate_size_mm": 20.0,
            "target_slump_mm": 120.0,
            "air_content_pct": 1.5,
            "constituents": [
                {
                    "material_id": str(uuid.uuid4()),
                    "material_code": "CEM-OPC-53",
                    "material_name": "OPC 53 Grade Cement",
                    "category_code": "CEMENT",
                    "quantity_kg_m3": 350.0,
                    "specific_gravity": 3.15,
                    "moisture_pct": 0.0,
                    "water_absorption_pct": 0.0,
                    "source_location": "PLANT_SILO_1",
                    "is_active": True,
                },
                {
                    "material_id": str(uuid.uuid4()),
                    "material_code": "MAT-WTR",
                    "material_name": "Batching Water",
                    "category_code": "WATER",
                    "quantity_kg_m3": 175.0,
                    "specific_gravity": 1.0,
                    "moisture_pct": 0.0,
                    "water_absorption_pct": 0.0,
                    "source_location": "MAINS",
                    "is_active": True,
                },
            ],
            "total_binder_kg_m3": 350.0,
            "water_binder_ratio": 0.50,
            "water_cement_ratio": 0.50,
            "wet_density_kg_m3": 2400.0,
            "captured_at": now.isoformat(),
        },
        model_snapshot_json={
            "model_id": "model-concrete-xgb-v3",
            "model_name": "ACC Multi-Task Gradient Boosted Regressor",
            "model_version": "3.4.2",
            "active_since": "2026-01-01T00:00:00Z",
        },
        target_strength_snapshot_json={
            "grade": "M30",
            "characteristic_strength_fck_mpa": 30.0,
            "standard_deviation_s_mpa": 5.0,
            "risk_factor_k": 1.65,
            "target_mean_strength_fck_prime_mpa": 38.25,
            "calculated_at": now.isoformat(),
        },
        constraints_snapshot_json={
            "min_cement_kg_m3": 250.0,
            "max_water_binder_ratio": 0.50,
            "min_grade_strength_mpa": 30.0,
            "target_strength_fck_prime_mpa": 38.25,
        },
        pricing_snapshot_json=None,  # Unconfigured by default
        candidates_count=3,
        stage_message="Evaluated 3 candidates",
        triggered_by_user_id=quality_head_user.id,
    )
    db_session.add(run)

    # 1. Feasible & Pareto Optimal Candidate
    cand_1 = OptimizationCandidate(
        id=str(uuid.uuid4()),
        run_id=run.id,
        candidate_identifier="CAND-01",
        is_recommended=False,
        is_feasible=True,
        predicted_strength_mpa=Decimal("41.50"),
        prediction_source="ML_MODEL",
        cost_per_m3=None,
        binder_intensity=Decimal("330.0"),
        constituent_payload_json={
            "water_binder_ratio": 0.45,
            "water_cement_ratio": 0.45,
            "constituents": [],
        },
        constraint_evaluation_json={
            "is_non_dominated": True,
            "strength_margin_mpa": 3.25,
            "strength_gate_status": "PASSED",
            "physical_volume_diagnostic": {
                "volume_balance_actual_m3": 1.000,
            },
            "constraint_diagnostics": [],
        },
    )

    # 2. Feasible but Non-Pareto Candidate
    cand_2 = OptimizationCandidate(
        id=str(uuid.uuid4()),
        run_id=run.id,
        candidate_identifier="CAND-02",
        is_recommended=False,
        is_feasible=True,
        predicted_strength_mpa=Decimal("39.00"),
        prediction_source="ML_MODEL",
        cost_per_m3=None,
        binder_intensity=Decimal("345.0"),
        constituent_payload_json={
            "water_binder_ratio": 0.48,
            "water_cement_ratio": 0.48,
            "constituents": [],
        },
        constraint_evaluation_json={
            "is_non_dominated": False,
            "strength_margin_mpa": 0.75,
            "strength_gate_status": "PASSED",
            "physical_volume_diagnostic": {
                "volume_balance_actual_m3": 1.002,
            },
            "constraint_diagnostics": [],
        },
    )

    # 3. Infeasible Candidate
    cand_3 = OptimizationCandidate(
        id=str(uuid.uuid4()),
        run_id=run.id,
        candidate_identifier="CAND-03",
        is_recommended=False,
        is_feasible=False,
        predicted_strength_mpa=Decimal("36.00"),
        prediction_source="ML_MODEL",
        cost_per_m3=None,
        binder_intensity=Decimal("290.0"),
        constituent_payload_json={
            "water_binder_ratio": 0.55,
            "water_cement_ratio": 0.55,
            "constituents": [],
        },
        constraint_evaluation_json={
            "is_non_dominated": False,
            "strength_margin_mpa": -2.25,
            "strength_gate_status": "FAILED",
            "physical_volume_diagnostic": {
                "volume_balance_actual_m3": 0.980,
            },
            "constraint_diagnostics": [],
        },
    )

    db_session.add_all([cand_1, cand_2, cand_3])
    db_session.commit()
    db_session.refresh(run)

    return {
        "run": run,
        "cand_pareto": cand_1,
        "cand_non_pareto": cand_2,
        "cand_infeasible": cand_3,
    }


def test_01_get_run_governance_structure(client, quality_head_token, sample_optimization_run):
    """Test retrieving complete run governance response with correct counts and metadata."""
    run_id = str(sample_optimization_run["run"].id)
    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["run_id"] == run_id
    assert data["total_candidates"] == 3
    assert data["feasible_candidates_count"] == 2
    assert data["pareto_optimal_count"] == 1
    assert data["eligible_for_review_count"] == 1
    assert data["has_feasible_candidates"] is True
    assert data["production_activation_status"] == "PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE"
    assert len(data["candidates"]) == 3


def test_02_feasible_pareto_candidate_eligibility(client, quality_head_token, sample_optimization_run):
    """Test that a feasible + Pareto optimal candidate is flagged ELIGIBLE_FOR_HUMAN_REVIEW."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    cand_1 = next(c for c in data["candidates"] if c["candidate_id"] == cand_1_id)
    assert cand_1["is_feasible"] is True
    assert cand_1["is_pareto_optimal"] is True
    assert cand_1["eligibility_status"] == "ELIGIBLE_FOR_HUMAN_REVIEW"
    assert cand_1["eligibility_reason_code"] == "ELIGIBLE_FOR_HUMAN_REVIEW"
    assert "ACCEPT" in cand_1["allowed_actions"]
    assert "REJECT" in cand_1["allowed_actions"]


def test_03_infeasible_candidate_quarantine(client, quality_head_token, sample_optimization_run):
    """Test that an infeasible candidate is quarantined and has no review actions."""
    run_id = str(sample_optimization_run["run"].id)
    cand_3_id = str(sample_optimization_run["cand_infeasible"].id)

    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    cand_3 = next(c for c in data["candidates"] if c["candidate_id"] == cand_3_id)
    assert cand_3["is_feasible"] is False
    assert cand_3["eligibility_status"] == "NOT_ELIGIBLE_INFEASIBLE"
    assert cand_3["eligibility_reason_code"] == "INFEASIBLE_CANDIDATE"
    assert cand_3["allowed_actions"] == []


def test_04_non_pareto_candidate_classification(client, quality_head_token, sample_optimization_run):
    """Test that a feasible but non-Pareto candidate is marked NOT_ELIGIBLE_NON_PARETO."""
    run_id = str(sample_optimization_run["run"].id)
    cand_2_id = str(sample_optimization_run["cand_non_pareto"].id)

    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    cand_2 = next(c for c in data["candidates"] if c["candidate_id"] == cand_2_id)
    assert cand_2["is_feasible"] is True
    assert cand_2["is_pareto_optimal"] is False
    assert cand_2["eligibility_status"] == "NOT_ELIGIBLE_NON_PARETO"
    assert cand_2["eligibility_reason_code"] == "NON_PARETO_OPTIMAL"


def test_05_cost_not_configured_preservation(client, quality_head_token, sample_optimization_run):
    """Test that unconfigured pricing is reported factually with cost_status = NOT_CONFIGURED and no fake numbers."""
    run_id = str(sample_optimization_run["run"].id)
    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["cost_status"] == "NOT_CONFIGURED"
    assert "Pricing Source: Not Configured" in data["price_source_description"]
    for c in data["candidates"]:
        assert c["cost_status"] == "NOT_CONFIGURED"
        assert c["cost_per_m3"] is None
        assert c["cost_delta_per_m3"] is None


def test_06_unauthorized_user_review_forbidden(client, viewer_token, sample_optimization_run):
    """Test that an unauthorized user (ANALYST_VIEWER) receives 403 Forbidden when attempting to review."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={
            "action": "ACCEPT",
            "reason_code": "TECHNICAL_VALIDATION_CONFIRMED",
            "comments": "Attempt by viewer",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403, resp.text
    assert "authorization" in resp.json()["detail"].lower()


def test_07_authorized_human_review_accept(client, quality_head_token, sample_optimization_run, db_session):
    """Test that an authorized user (QUALITY_HEAD) can ACCEPT an eligible candidate and audit log is recorded."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={
            "action": "ACCEPT",
            "reason_code": "TECHNICAL_VALIDATION_CONFIRMED",
            "comments": "Approved by QC Head for secondary lab trial batching.",
        },
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200, resp.text
    item = resp.json()

    assert item["candidate_id"] == cand_1_id
    assert item["review_status"] == "ACCEPTED"
    assert item["reviewed_by_username"] == "test_quality_head_5e"
    assert item["review_decision_reason"] == "TECHNICAL_VALIDATION_CONFIRMED"
    assert item["review_comments"] == "Approved by QC Head for secondary lab trial batching."
    assert item["reviewed_at"] is not None

    # Verify audit trail
    audit = db_session.scalars(
        select(SecurityAuditLog)
        .where(
            SecurityAuditLog.event_type == "OPTIMIZATION_CANDIDATE_REVIEW_DECISION",
            SecurityAuditLog.resource_name == "AI_MIX_OPTIMIZATION_GOVERNANCE",
        )
        .order_by(SecurityAuditLog.created_at.desc())
    ).first()
    assert audit is not None
    assert audit.details["action"] == "ACCEPT"
    assert audit.details["candidate_identifier"] == "CAND-01"


def test_08_cannot_accept_infeasible_candidate(client, quality_head_token, sample_optimization_run):
    """Test that the system strictly forbids accepting an infeasible candidate."""
    run_id = str(sample_optimization_run["run"].id)
    cand_3_id = str(sample_optimization_run["cand_infeasible"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_3_id}/review",
        json={
            "action": "ACCEPT",
            "reason_code": "FORCE_APPROVAL_ATTEMPT",
            "comments": "Should be blocked",
        },
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 400, resp.text
    assert "infeasible" in resp.json()["detail"].lower()


def test_09_authorized_human_review_reject(client, quality_head_token, sample_optimization_run):
    """Test that an authorized user can REJECT a candidate."""
    run_id = str(sample_optimization_run["run"].id)
    cand_2_id = str(sample_optimization_run["cand_non_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_2_id}/review",
        json={
            "action": "REJECT",
            "reason_code": "PLANT_RAW_MATERIAL_CONSTRAINTS",
            "comments": "Non-Pareto candidate rejected due to higher cement content.",
        },
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200, resp.text
    item = resp.json()

    assert item["review_status"] == "REJECTED"
    assert item["review_decision_reason"] == "PLANT_RAW_MATERIAL_CONSTRAINTS"


def test_10_authorized_human_review_reset(client, quality_head_token, sample_optimization_run):
    """Test that resetting a candidate returns review_status to PENDING_REVIEW."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    # First Accept
    client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={"action": "ACCEPT", "reason_code": "TEMP_ACCEPT"},
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )

    # Then Reset
    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={"action": "RESET", "reason_code": "RESET_FOR_NEW_RUN"},
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["review_status"] == "PENDING_REVIEW"
    assert item["reviewed_by_username"] is None
    assert item["reviewed_at"] is None


def test_11_cross_run_ownership_rejection(client, quality_head_token, sample_optimization_run):
    """Test that mismatched run_id and candidate_id returns 404."""
    other_run_id = str(uuid.uuid4())
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{other_run_id}/candidates/{cand_1_id}/review",
        json={"action": "ACCEPT", "reason_code": "TEST"},
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 404


def test_12_zero_feasible_candidates_handling(client, quality_head_token, db_session):
    """Test that a run with 0 feasible candidates returns explicit message without fabricated recommendations."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    run = OptimizationRun(
        id=run_id,
        recipe_id=str(uuid.uuid4()),
        recipe_code="M20-ZERO-FEASIBLE",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="NO_FEASIBLE_CANDIDATES",
        recipe_snapshot_json={"recipe_code": "M20-ZERO-FEASIBLE", "grade": "M20", "total_binder_kg_m3": 300.0},
        model_snapshot_json={"model_name": "Concrete Predictor"},
        target_strength_snapshot_json={"grade": "M20", "characteristic_strength_fck_mpa": 20.0},
        constraints_snapshot_json={},
        pricing_snapshot_json=None,
        candidates_count=1,
        stage_message="No feasible candidates found",
    )
    db_session.add(run)

    cand_infeasible = OptimizationCandidate(
        id=str(uuid.uuid4()),
        run_id=run.id,
        candidate_identifier="CAND-INF-01",
        is_recommended=False,
        is_feasible=False,
        predicted_strength_mpa=Decimal("18.00"),
        prediction_source="ML_MODEL",
        binder_intensity=Decimal("250.0"),
        constituent_payload_json={"water_binder_ratio": 0.60},
        constraint_evaluation_json={"is_non_dominated": False},
    )
    db_session.add(cand_infeasible)
    db_session.commit()

    resp = client.get(
        f"/api/v1/optimization/runs/{run_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["has_feasible_candidates"] is False
    assert data["feasible_candidates_count"] == 0
    assert data["eligible_for_review_count"] == 0
    assert data["governance_message"] == "No feasible candidate is currently available for human review."


def test_13_admin_role_can_review(client, admin_token, sample_optimization_run):
    """Test that ADMIN role can also execute review decisions."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={"action": "ACCEPT", "reason_code": "ADMIN_OVERRIDE_CONFIRMED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["review_status"] == "ACCEPTED"
    assert item["reviewed_by_username"] == "test_admin_5e"


def test_14_invalid_action_rejected(client, quality_head_token, sample_optimization_run):
    """Test that invalid action strings like 'PUBLISH' or 'ACTIVATE' are rejected with 400."""
    run_id = str(sample_optimization_run["run"].id)
    cand_1_id = str(sample_optimization_run["cand_pareto"].id)

    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{cand_1_id}/review",
        json={"action": "ACTIVATE_FOR_PRODUCTION", "reason_code": "INVALID"},
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 400


def test_15_nonexistent_run_404(client, quality_head_token):
    """Test that requesting governance for a nonexistent run returns 404."""
    nonexistent_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/v1/optimization/runs/{nonexistent_id}/governance",
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 404


def test_16_nonexistent_candidate_404(client, quality_head_token, sample_optimization_run):
    """Test that reviewing a nonexistent candidate returns 404."""
    run_id = str(sample_optimization_run["run"].id)
    nonexistent_cand_id = str(uuid.uuid4())
    resp = client.post(
        f"/api/v1/optimization/runs/{run_id}/candidates/{nonexistent_cand_id}/review",
        json={"action": "ACCEPT", "reason_code": "TEST"},
        headers={"Authorization": f"Bearer {quality_head_token}"},
    )
    assert resp.status_code == 404
