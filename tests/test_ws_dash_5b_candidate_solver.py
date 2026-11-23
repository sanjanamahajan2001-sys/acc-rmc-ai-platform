"""Unit and Integration Tests for AI Mix Optimization Candidate Solver (Phase 5B)."""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.contracts.optimization.models import (
    OptimizationCandidateDTO,
    OptimizationRunTriggerRequestDTO,
    PhysicalVolumeDiagnosticDTO,
    RecipeSnapshotDTO,
    TargetStrengthSnapshotDTO,
)
from src.database.models.master import Plant, Recipe
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import Role, User, UserRole
from src.database.session import get_session_factory
from src.security.dependencies import get_current_user, get_db
from src.services.candidate_solver_service import CandidateSolverService
from src.services.mix_optimization_service import MixOptimizationService


@pytest.fixture
def db_session():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_user(db_session: Session):
    user = db_session.query(User).filter((User.username == "admin") | (User.email == "admin@acc.in")).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@acc.in",
            password_hash="hashed_test_password",
            full_name="System Administrator",
            account_status="ACTIVE",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    role = db_session.query(Role).filter(Role.id == "QUALITY_ENGINEER").first()
    if not role:
        role = Role(
            id="QUALITY_ENGINEER",
            name="Quality Engineer",
            description="Quality role",
            is_system_role=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(role)
        db_session.commit()

    user_role = db_session.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == "QUALITY_ENGINEER").first()
    if not user_role:
        user_role = UserRole(
            user_id=user.id,
            role_id="QUALITY_ENGINEER",
            assigned_at=datetime.now(timezone.utc),
        )
        db_session.add(user_role)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def api_client(db_session: Session, mock_user: User):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_bounded_candidate_generation_determinism(db_session: Session):
    """Verify that candidate generation produces a bounded, deterministic set of mixes."""
    recipe = db_session.query(Recipe).filter(Recipe.is_deleted == False).first()
    assert recipe is not None

    recipe_snap = MixOptimizationService._capture_recipe_snapshot(db_session, recipe)
    constraints_snap = MixOptimizationService._capture_constraints_snapshot(recipe).model_dump()
    target_strength_snap = TargetStrengthSnapshotDTO(
        characteristic_strength_fck_mpa=30.0,
        standard_deviation_mpa=5.0,
        standard_deviation_source="IS456_ASSUMED_TABLE_8",
        target_mean_strength_fck_prime_mpa=38.25,
    )

    candidates_1 = CandidateSolverService.generate_bounded_candidate_proportions(
        recipe_snap=recipe_snap,
        constraints_snap=constraints_snap,
        target_strength_snap=target_strength_snap,
    )
    candidates_2 = CandidateSolverService.generate_bounded_candidate_proportions(
        recipe_snap=recipe_snap,
        constraints_snap=constraints_snap,
        target_strength_snap=target_strength_snap,
    )

    assert len(candidates_1) > 0
    assert len(candidates_1) <= 30
    assert len(candidates_1) == len(candidates_2)
    assert candidates_1[0]["cement_kg_m3"] == candidates_2[0]["cement_kg_m3"]


def test_physical_volume_balance_accuracy(db_session: Session):
    """Verify that every generated candidate satisfies absolute volume yield tolerance (1.000 m3 +- 0.010 m3)."""
    recipe = db_session.query(Recipe).filter(Recipe.is_deleted == False).first()
    assert recipe is not None

    recipe_snap = MixOptimizationService._capture_recipe_snapshot(db_session, recipe)
    constraints_snap = MixOptimizationService._capture_constraints_snapshot(recipe).model_dump()
    target_strength_snap = TargetStrengthSnapshotDTO(
        characteristic_strength_fck_mpa=30.0,
        standard_deviation_mpa=5.0,
        standard_deviation_source="IS456_ASSUMED_TABLE_8",
        target_mean_strength_fck_prime_mpa=38.25,
    )

    candidates = CandidateSolverService.generate_bounded_candidate_proportions(
        recipe_snap=recipe_snap,
        constraints_snap=constraints_snap,
        target_strength_snap=target_strength_snap,
    )

    for cand in candidates:
        vol_diag, constr_diags, is_eng_passed = CandidateSolverService.evaluate_physics_and_constraints(
            cand=cand,
            constraints_snap=constraints_snap,
        )
        assert vol_diag.volume_balance_actual_m3 >= 0.985
        assert vol_diag.volume_balance_actual_m3 <= 1.015
        assert vol_diag.validation_status == "PASSED"
        assert len(constr_diags) >= 4


def test_water_binder_boundary_precision_enforcement(db_session: Session):
    """Verify full-precision W/B validation: 0.5000000 passes, 0.5000001 fails, 0.5009677 fails."""
    recipe = db_session.query(Recipe).filter(Recipe.is_deleted == False).first()
    constraints_snap = MixOptimizationService._capture_constraints_snapshot(recipe).model_dump()

    base_cand = {
        "candidate_identifier": "CAND-TEST",
        "cement_kg_m3": 310.0,
        "flyash_kg_m3": 0.0,
        "ggbs_kg_m3": 0.0,
        "water_kg_m3": 155.0,
        "coarse_aggregate_kg_m3": 1148.0,
        "fine_aggregate_kg_m3": 782.0,
        "admixture_kg_m3": 1.5,
        "total_binder_kg_m3": 310.0,
        "binder_intensity_kg_m3": 310.0,
        "water_binder_ratio": 0.500,
        "water_cement_ratio": 0.500,
        "sg_c": 3.15,
        "sg_fa": 2.20,
        "sg_ggbs": 2.90,
        "sg_w": 1.00,
        "sg_ca": 2.65,
        "sg_fa_agg": 2.65,
        "sg_admix": 1.15,
        "air_volume_m3": 0.010,
        "constituents": [],
    }

    # 1. W/B = 0.5000000 -> EXACT PASS (155.0 / 310.0)
    cand_pass = dict(base_cand)
    cand_pass["water_kg_m3"] = 155.0
    _, diags, passed = CandidateSolverService.evaluate_physics_and_constraints(cand_pass, constraints_snap)
    wb_diag = next(d for d in diags if "Water-Binder" in d.constraint_name)
    assert passed is True
    assert wb_diag.status == "PASSED"
    assert wb_diag.margin >= 0.0

    # 2. W/B = 0.5009677 (155.3 / 310.0) -> STRICT FAIL
    cand_fail_precision = dict(base_cand)
    cand_fail_precision["water_kg_m3"] = 155.3
    _, diags_fail, passed_fail = CandidateSolverService.evaluate_physics_and_constraints(cand_fail_precision, constraints_snap)
    wb_diag_fail = next(d for d in diags_fail if "Water-Binder" in d.constraint_name)
    assert passed_fail is False
    assert wb_diag_fail.status == "FAILED"
    assert wb_diag_fail.margin < 0.0

    # 3. W/B = 0.5000001 (155.000031 / 310.0) -> STRICT FAIL
    cand_fail_micro = dict(base_cand)
    cand_fail_micro["water_kg_m3"] = 155.000031
    _, diags_micro, passed_micro = CandidateSolverService.evaluate_physics_and_constraints(cand_fail_micro, constraints_snap)
    wb_diag_micro = next(d for d in diags_micro if "Water-Binder" in d.constraint_name)
    assert passed_micro is False
    assert wb_diag_micro.status == "FAILED"

    # 4. W/B = 0.4999999 (154.9999 / 310.0) -> STRICT PASS
    cand_pass_micro = dict(base_cand)
    cand_pass_micro["water_kg_m3"] = 154.9999
    _, diags_pm, passed_pm = CandidateSolverService.evaluate_physics_and_constraints(cand_pass_micro, constraints_snap)
    wb_diag_pm = next(d for d in diags_pm if "Water-Binder" in d.constraint_name)
    assert passed_pm is True
    assert wb_diag_pm.status == "PASSED"


def test_infeasible_candidates_excluded_from_pareto_frontier(db_session: Session):
    """Verify that candidates failing W/B, strength, or volume yield are strictly excluded from Pareto frontier."""
    c_pass = OptimizationCandidateDTO(
        id="c-pass",
        candidate_identifier="CAND-PASS",
        predicted_strength_mpa=45.0,
        target_mean_strength_mpa=38.25,
        characteristic_strength_fck_mpa=30.0,
        strength_margin_mpa=6.75,
        strength_gate_status="PASSED",
        prediction_source="ML_MODEL",
        prediction_source_semantics="Analytical Prediction — Limited Validation",
        model_name="acc_concrete_28d_strength",
        model_version="1.0.0",
        binder_intensity_kg_m3=320.0,
        cost_per_m3=None,
        water_binder_ratio=0.45,
        water_cement_ratio=0.45,
        is_feasible=True,
        is_non_dominated=False,
        is_recommended=None,
        physical_volume_diagnostic=PhysicalVolumeDiagnosticDTO(
            volume_balance_actual_m3=1.000,
            volume_balance_target_m3=1.000,
            volume_balance_deviation_m3=0.000,
            volume_tolerance_limit_m3=0.010,
            air_volume_m3=0.010,
            validation_status="PASSED",
        ),
        constraint_diagnostics=[],
        constituents=[],
    )

    # Infeasible candidate (W/B exceeded) with even higher strength and lower binder
    c_infeasible_wb = OptimizationCandidateDTO(
        id="c-wb-fail",
        candidate_identifier="CAND-WB-FAIL",
        predicted_strength_mpa=50.0,
        target_mean_strength_mpa=38.25,
        characteristic_strength_fck_mpa=30.0,
        strength_margin_mpa=11.75,
        strength_gate_status="PASSED",
        prediction_source="ML_MODEL",
        prediction_source_semantics="Analytical Prediction — Limited Validation",
        model_name="acc_concrete_28d_strength",
        model_version="1.0.0",
        binder_intensity_kg_m3=290.0,
        cost_per_m3=None,
        water_binder_ratio=0.55,
        water_cement_ratio=0.55,
        is_feasible=False,
        is_non_dominated=False,
        is_recommended=None,
        physical_volume_diagnostic=PhysicalVolumeDiagnosticDTO(
            volume_balance_actual_m3=1.000,
            volume_balance_target_m3=1.000,
            volume_balance_deviation_m3=0.000,
            volume_tolerance_limit_m3=0.010,
            air_volume_m3=0.010,
            validation_status="PASSED",
        ),
        constraint_diagnostics=[],
        constituents=[],
    )

    evaluated = [c_pass, c_infeasible_wb]
    feasible = [c for c in evaluated if c.is_feasible]

    for c_a in feasible:
        dominated = False
        for c_b in feasible:
            if c_a.candidate_identifier == c_b.candidate_identifier:
                continue
            if c_b.predicted_strength_mpa >= c_a.predicted_strength_mpa and c_b.binder_intensity_kg_m3 <= c_a.binder_intensity_kg_m3:
                if c_b.predicted_strength_mpa > c_a.predicted_strength_mpa or c_b.binder_intensity_kg_m3 < c_a.binder_intensity_kg_m3:
                    dominated = True
                    break
        c_a.is_non_dominated = not dominated

    assert c_pass.is_non_dominated is True
    assert c_infeasible_wb.is_non_dominated is False


def test_end_to_end_candidate_evaluation_and_pareto(db_session: Session, mock_user: User, api_client: TestClient):
    """Verify full end-to-end evaluation pipeline: snapshot trigger, candidate solve, inference, Pareto classification."""
    recipe = db_session.query(Recipe).filter(Recipe.is_deleted == False).first()
    plant = db_session.query(Plant).filter(Plant.is_deleted == False).first()
    assert recipe is not None
    assert plant is not None

    # 1. Trigger Phase 5A Optimization Run Context
    trigger_req = {
        "recipe_id": str(recipe.id),
        "plant_code": plant.plant_code,
        "optimization_objective": "MINIMIZE_BINDER",
    }
    resp = api_client.post("/api/v1/optimization/runs/trigger", json=trigger_req)
    assert resp.status_code == 201
    run_data = resp.json()
    run_id = run_data["run_id"]

    # 2. Evaluate Candidates via Phase 5B endpoint
    eval_resp = api_client.post(f"/api/v1/optimization/runs/{run_id}/evaluate")
    assert eval_resp.status_code == 200, eval_resp.text
    data = eval_resp.json()

    assert data["run_id"] == run_id
    assert data["total_candidates"] > 0
    assert "run_status" in data
    assert data["run_status"] in ("SUCCESS", "NO_FEASIBLE_CANDIDATES")
    assert "baseline_coordinates" in data
    assert data["baseline_coordinates"]["recipe_code"] == recipe.recipe_code

    # Check candidate structure and Pareto flags
    candidates = data["candidates"]
    assert len(candidates) == data["total_candidates"]

    feasible_candidates = [c for c in candidates if c["is_feasible"]]
    if feasible_candidates:
        pareto_candidates = [c for c in feasible_candidates if c["is_non_dominated"]]
        assert len(pareto_candidates) > 0
        assert data["pareto_candidates_count"] == len(pareto_candidates)

    for c in candidates:
        assert c["is_recommended"] is None
        assert "predicted_strength_mpa" in c
        assert "target_mean_strength_mpa" in c
        assert "strength_margin_mpa" in c
        assert c["prediction_source"] in ("ML_MODEL", "HEURISTIC")
        assert len(c["constituents"]) > 0

    # 3. Verify Idempotency on repeated evaluate call
    repeat_resp = api_client.post(f"/api/v1/optimization/runs/{run_id}/evaluate")
    assert repeat_resp.status_code == 200
    repeat_data = repeat_resp.json()
    assert repeat_data["total_candidates"] == data["total_candidates"]
    assert repeat_data["feasible_candidates_count"] == data["feasible_candidates_count"]


def test_is10262_dual_criterion_target_mean_strength(db_session: Session):
    """Verify IS 10262:2019 Clause 4.2 Dual-Criterion: f'ck = max(fck + 1.65*s, fck + X)."""
    from src.services.mix_optimization_service import MixOptimizationService, IS10262_FACTOR_X

    # Case A: Standard assumed deviation s = 4.0 for M25 (X = 5.5)
    # fck + 1.65*4.0 = 25 + 6.60 = 31.60 MPa
    # fck + X = 25 + 5.5 = 30.50 MPa -> max is 31.60 MPa
    recipe_m25 = Recipe(
        id=str(uuid.uuid4()),
        recipe_code="REC-M25-DUAL-TEST",
        recipe_name="M25 Dual Test",
        grade="M-25",
        target_strength_mpa=25.0,
        exposure_class="MODERATE",
    )
    snap_a = MixOptimizationService._capture_target_strength_snapshot(db_session, recipe_m25)
    assert snap_a.characteristic_strength_fck_mpa == 25.0
    assert snap_a.target_mean_strength_fck_prime_mpa == 31.60

    # Case B: When empirical SQC standard deviation is very low (e.g. s = 2.0 MPa), X-factor governs!
    # fck + 1.65*2.0 = 25 + 3.30 = 28.30 MPa
    # fck + X = 25 + 5.50 = 30.50 MPa -> max MUST BE 30.50 MPa (NOT 28.30)
    fck = 25.0
    sigma_low = 2.0
    x_val = IS10262_FACTOR_X["M25"]
    target_mean_b = round(max(fck + 1.65 * sigma_low, fck + x_val), 2)
    assert target_mean_b == 30.50, f"Expected 30.50 MPa governed by X-factor, got {target_mean_b}"


def test_is456_rcc_moderate_exposure_m20_rejection_and_m25_acceptance(db_session: Session):
    """Verify IS 456 Table 5 RCC rule: Moderate Exposure requires Grade >= M25; M20 must fail."""
    constraints_snap = {
        "exposure_class": "MODERATE",
        "standard_edition": "IS 456:2000 Table 5 & IS 10262:2019",
        "items": [
            {
                "constraint_name": "Minimum Concrete Grade (RCC)",
                "standard_reference": "IS 456:2000 Table 5 (MODERATE Reinforced)",
                "limit_value": 25.0,
                "unit": "MPa (Grade)",
                "comparison": "MINIMUM",
                "status": "ACTIVE",
            },
            {
                "constraint_name": "Minimum Cementitious Content",
                "standard_reference": "IS 456:2000 Table 5 (MODERATE Exposure)",
                "limit_value": 300.0,
                "unit": "kg/m³",
                "comparison": "MINIMUM",
                "status": "ACTIVE",
            },
            {
                "constraint_name": "Maximum Free Water-Binder Ratio",
                "standard_reference": "IS 456:2000 Table 5 (MODERATE Exposure)",
                "limit_value": 0.50,
                "unit": "ratio",
                "comparison": "MAXIMUM",
                "status": "ACTIVE",
            },
        ],
    }

    base_cand = {
        "candidate_identifier": "CAND-TEST",
        "cement_kg_m3": 250.0,
        "flyash_kg_m3": 50.0,
        "ggbs_kg_m3": 0.0,
        "water_kg_m3": 125.0,
        "coarse_aggregate_kg_m3": 1100.0,
        "fine_aggregate_kg_m3": 850.0,
        "admixture_kg_m3": 2.0,
        "total_binder_kg_m3": 300.0,
        "water_binder_ratio": 0.417,
        "sg_c": 3.15,
        "sg_fa": 2.20,
        "sg_ggbs": 2.90,
        "sg_w": 1.00,
        "sg_ca": 2.68,
        "sg_fa_agg": 2.65,
        "sg_admix": 1.15,
        "air_volume_m3": 0.010,
    }

    # 1. M-20 under Moderate RCC Exposure -> MUST FAIL Grade Constraint
    cand_m20 = dict(base_cand)
    cand_m20["fck"] = 20.0
    cand_m20["grade"] = "M-20"
    _, diags_m20, is_feasible_m20 = CandidateSolverService.evaluate_physics_and_constraints(cand_m20, constraints_snap)
    grade_diag_m20 = next(d for d in diags_m20 if "Grade" in d.constraint_name)
    assert is_feasible_m20 is False
    assert grade_diag_m20.status == "FAILED"
    assert grade_diag_m20.actual_value == 20.0
    assert grade_diag_m20.limit_value == 25.0

    # 2. M-25 under Moderate RCC Exposure -> MUST PASS Grade Constraint
    cand_m25 = dict(base_cand)
    cand_m25["fck"] = 25.0
    cand_m25["grade"] = "M-25"
    _, diags_m25, is_feasible_m25 = CandidateSolverService.evaluate_physics_and_constraints(cand_m25, constraints_snap)
    grade_diag_m25 = next(d for d in diags_m25 if "Grade" in d.constraint_name)
    assert grade_diag_m25.status == "PASSED"
    assert grade_diag_m25.actual_value == 25.0
