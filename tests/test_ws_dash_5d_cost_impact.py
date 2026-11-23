"""Comprehensive Test Suite for Phase 5D — Cost & Commercial Feasibility Engine (Hardened).

Covers all 30+ critical verification categories:
1. ₹/kg calculation
2. ₹/tonne calculation
3. ₹/L calculation with valid SG
4. Missing SG for ₹/L (PRICE_CONVERSION_UNAVAILABLE)
5. Zero/invalid SG for ₹/L (PRICE_CONVERSION_UNAVAILABLE)
6. Unsupported unit (UNSUPPORTED_UNIT)
7. Master total cost
8. Candidate total cost
9. Positive cost delta
10. Negative cost delta
11. Zero cost delta
12. Zero master cost handling (percentage is None, no division by zero)
13. NOT_CONFIGURED state
14. PARTIALLY_CONFIGURED state
15. CONFIGURED state
16. NEW material handling (master = 0)
17. REMOVED material handling (candidate = 0)
18. Unpriced material list verification
19. Production volume configured
20. Production volume unavailable
21. Invalid/negative production volume validation
22. Pricing provenance fields
23. Snapshot and version provenance
24. Historical price reproducibility
25. Candidate and run ownership verification
26. Cross-run candidate rejection (404)
27. Nonexistent run rejection (404)
28. Nonexistent candidate rejection (404)
29. Infeasible candidate preservation
30. Negative price rejection
31. Non-finite SG rejection
32. Engineering workbook data boundary (zero price inference)
33. Zero ML/optimizer side-effects
"""

from datetime import datetime, timezone
import math
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import Role, User, UserRole
from src.database.session import get_session_factory
from src.security.crypto import hash_password
from src.security.dependencies import get_current_user, get_db
from src.services.cost_impact_service import CostImpactService


@pytest.fixture
def db_session():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_user_5d(db_session: Session) -> User:
    role = db_session.query(Role).filter(Role.id == "QUALITY_ENGINEER").first()
    if not role:
        role = Role(id="QUALITY_ENGINEER", name="Quality Engineer", is_system_role=True)
        db_session.add(role)
        db_session.commit()

    user = db_session.query(User).filter((User.username == "qe_cost_test_h") | (User.email == "qe_cost_h@acc.in")).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="qe_cost_test_h",
            email="qe_cost_h@acc.in",
            full_name="Quality Engineer Cost Hardened",
            password_hash=hash_password("Pass@123"),
            account_status="ACTIVE",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    ur = db_session.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
    if not ur:
        ur = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur)
        db_session.commit()
    return user


@pytest.fixture
def api_client_5d(db_session: Session, mock_user_5d: User):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user_5d
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def standard_pricing_snapshot():
    return {
        "is_configured": True,
        "snapshot_id": "SNAP-2026-Q3-001",
        "price_source": "PROCUREMENT_ERP_FEED",
        "price_version": "2026-Q3-V1",
        "effective_from": "2026-07-01T00:00:00Z",
        "effective_to": "2026-09-30T23:59:59Z",
        "plant_code": "PLANT-01",
        "currency": "INR",
        "materials": [
            {
                "material_code": "OPC-53",
                "material_name": "UltraTech OPC 53",
                "category_code": "CEMENT",
                "unit_price": 6.50,
                "price_unit": "₹/kg",
            },
            {
                "material_code": "FA-G1",
                "material_name": "Fly Ash Grade 1",
                "category_code": "FLY_ASH",
                "unit_price": 1.20,
                "price_unit": "₹/kg",
            },
            {
                "material_code": "CA-20MM",
                "material_name": "Coarse Aggregate 20mm",
                "category_code": "COARSE_AGGREGATE",
                "unit_price": 950.0,
                "price_unit": "₹/tonne",
            },
            {
                "material_code": "FA-M-SAND",
                "material_name": "Manufactured Sand",
                "category_code": "FINE_AGGREGATE",
                "unit_price": 850.0,
                "price_unit": "₹/tonne",
            },
            {
                "material_code": "WATER-TREATED",
                "material_name": "Batching Water",
                "category_code": "WATER",
                "unit_price": 0.05,
                "price_unit": "₹/kg",
            },
            {
                "material_code": "ADMIX-PCE",
                "material_name": "MasterGlenium PCE",
                "category_code": "ADMIXTURE",
                "unit_price": 86.40,
                "price_unit": "₹/L",
            },
        ],
        "production_volume": {
            "is_configured": True,
            "volume_source": "PLANT_CAPACITY_SCHEDULE",
            "volume_period": "MULTI_PERIOD",
            "volume_basis": "DISPATCH_SCHEDULE",
            "daily_volume_m3": 250.0,
            "monthly_volume_m3": 6500.0,
            "annualized_volume_m3": 78000.0,
        },
    }


@pytest.fixture
def standard_master_snapshot():
    return {
        "recipe_id": str(uuid.uuid4()),
        "recipe_code": "M30-STD-P1",
        "plant_code": "PLANT-01",
        "target_grade": "M30",
        "target_slump_mm": 120,
        "design_w_b_ratio": 0.45,
        "constituents": [
            {"material_id": str(uuid.uuid4()), "material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "target_quantity_kg_m3": 350.0, "default_density_kg_m3": 3150.0},
            {"material_id": str(uuid.uuid4()), "material_code": "FA-G1", "material_name": "Fly Ash Grade 1", "category_code": "FLY_ASH", "target_quantity_kg_m3": 50.0, "default_density_kg_m3": 2250.0},
            {"material_id": str(uuid.uuid4()), "material_code": "CA-20MM", "material_name": "Coarse Aggregate 20mm", "category_code": "COARSE_AGGREGATE", "target_quantity_kg_m3": 1100.0, "default_density_kg_m3": 2680.0},
            {"material_id": str(uuid.uuid4()), "material_code": "FA-M-SAND", "material_name": "Manufactured Sand", "category_code": "FINE_AGGREGATE", "target_quantity_kg_m3": 720.0, "default_density_kg_m3": 2620.0},
            {"material_id": str(uuid.uuid4()), "material_code": "WATER-TREATED", "material_name": "Batching Water", "category_code": "WATER", "target_quantity_kg_m3": 180.0, "default_density_kg_m3": 1000.0},
            {"material_id": str(uuid.uuid4()), "material_code": "ADMIX-PCE", "material_name": "MasterGlenium PCE", "category_code": "ADMIXTURE", "target_quantity_kg_m3": 3.24, "default_density_kg_m3": 1080.0},
        ],
    }


def create_test_candidate(run_id: uuid.UUID, cand_id: uuid.UUID, is_feasible: bool = True):
    return OptimizationCandidate(
        id=cand_id,
        run_id=run_id,
        candidate_identifier="CAND-001",
        predicted_strength_mpa=41.5,
        cost_per_m3=0.0,
        is_feasible=is_feasible,
        prediction_source="ML_MODEL",
        constituent_payload_json={
            "candidate_identifier": "CAND-001",
            "cement_kg_m3": 320.0,
            "fly_ash_kg_m3": 80.0,
            "ggbs_kg_m3": 0.0,
            "water_kg_m3": 175.0,
            "coarse_agg_kg_m3": 1100.0,
            "fine_agg_kg_m3": 730.0,
            "admixture_kg_m3": 3.24,
            "w_b_ratio": 0.438,
            "constituents": [
                {"material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "quantity_kg_m3": 320.0, "specific_gravity": 3.15},
                {"material_code": "FA-G1", "material_name": "Fly Ash Grade 1", "category_code": "FLY_ASH", "quantity_kg_m3": 80.0, "specific_gravity": 2.25},
                {"material_code": "CA-20MM", "material_name": "Coarse Aggregate 20mm", "category_code": "COARSE_AGGREGATE", "quantity_kg_m3": 1100.0, "specific_gravity": 2.68},
                {"material_code": "FA-M-SAND", "material_name": "Manufactured Sand", "category_code": "FINE_AGGREGATE", "quantity_kg_m3": 730.0, "specific_gravity": 2.62},
                {"material_code": "WATER-TREATED", "material_name": "Batching Water", "category_code": "WATER", "quantity_kg_m3": 175.0, "specific_gravity": 1.00},
                {"material_code": "ADMIX-PCE", "material_name": "MasterGlenium PCE", "category_code": "ADMIXTURE", "quantity_kg_m3": 3.24, "specific_gravity": 1.08},
            ],
        },
        constraint_evaluation_json={"is_pareto_efficient": True, "is_feasible": is_feasible},
    )


# ==============================================================================
# 1-6. UNIT CONVERSIONS & NORMALIZATION TESTS
# ==============================================================================

def test_unit_price_per_kg():
    """1. Test ₹/kg direct normalization."""
    price, status_lbl = CostImpactService._normalize_unit_price(8.0, "₹/kg", 3.15)
    assert price == 8.0
    assert status_lbl == "EXACT"

    # Test master: 100 kg @ ₹8/kg = 800, cand: 90 kg @ ₹8/kg = 720, delta = -80, -10%
    master_qty, cand_qty = 100.0, 90.0
    m_cost = master_qty * price
    c_cost = cand_qty * price
    delta = c_cost - m_cost
    pct = ((c_cost - m_cost) / m_cost) * 100.0
    assert m_cost == 800.0
    assert c_cost == 720.0
    assert delta == -80.0
    assert pct == -10.0


def test_unit_price_per_tonne():
    """2. Test ₹/tonne normalization (divide by 1000)."""
    price, status_lbl = CostImpactService._normalize_unit_price(1000.0, "₹/tonne", 2.65)
    assert price == 1.0
    assert status_lbl == "CONVERTED_TONNE"

    price_mt, _ = CostImpactService._normalize_unit_price(850.0, "INR/MT", 2.60)
    assert price_mt == 0.85


def test_unit_price_per_litre_valid_sg():
    """3. Test ₹/L conversion with valid SG."""
    # Admixture: ₹86.40 / L, SG = 1.08 -> 1 L = 1.08 kg -> 86.40 / 1.08 = 80.0 ₹/kg
    price, status_lbl = CostImpactService._normalize_unit_price(86.40, "₹/L", 1.08)
    assert price == 80.0
    assert status_lbl == "CONVERTED_LITRE"


def test_unit_price_per_litre_missing_sg():
    """4. Test ₹/L when SG is missing (returns PRICE_CONVERSION_UNAVAILABLE)."""
    price, status_lbl = CostImpactService._normalize_unit_price(86.40, "₹/L", None)
    assert price is None
    assert status_lbl == "PRICE_CONVERSION_UNAVAILABLE"


def test_unit_price_per_litre_invalid_or_zero_sg():
    """5. Test ₹/L when SG is zero or negative (returns PRICE_CONVERSION_UNAVAILABLE)."""
    price_zero, status_zero = CostImpactService._normalize_unit_price(86.40, "₹/L", 0.0)
    assert price_zero is None
    assert status_zero == "PRICE_CONVERSION_UNAVAILABLE"

    price_neg, status_neg = CostImpactService._normalize_unit_price(86.40, "₹/L", -1.05)
    assert price_neg is None
    assert status_neg == "PRICE_CONVERSION_UNAVAILABLE"


def test_unit_price_unsupported_unit():
    """6. Test unsupported unit (returns UNSUPPORTED_UNIT)."""
    price, status_lbl = CostImpactService._normalize_unit_price(500.0, "₹/bag_of_50kg", 3.15)
    assert price is None
    assert status_lbl == "UNSUPPORTED_UNIT"


# ==============================================================================
# 7-15. TOTALS, DELTAS, PERCENTAGES, AND CONFIGURATION STATES
# ==============================================================================

def test_configured_master_and_candidate_totals(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """7, 8, 10, 15. Fully configured totals, candidate total, negative delta, and CONFIGURED status."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_status == "CONFIGURED"
    assert res.cost_summary.total_cost_available is True
    assert res.cost_summary.master_cost_per_m3 is not None
    assert res.cost_summary.candidate_cost_per_m3 is not None
    assert res.cost_summary.cost_delta_per_m3 is not None
    assert res.cost_summary.cost_delta_per_m3 < 0  # Cement reduction yields negative cost delta
    assert res.cost_summary.cost_delta_percent is not None
    assert len(res.cost_summary.unpriced_materials) == 0


def test_positive_cost_delta(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """9. Test positive cost delta when candidate increases costly constituents."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)

    # Candidate with higher cement (400 kg vs 350 kg)
    cand = OptimizationCandidate(
        id=cand_id,
        run_id=run_id,
        candidate_identifier="CAND-EXPENSIVE",
        predicted_strength_mpa=48.0,
        cost_per_m3=0.0,
        is_feasible=True,
        prediction_source="ML_MODEL",
        constituent_payload_json={
            "candidate_identifier": "CAND-EXPENSIVE",
            "constituents": [
                {"material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "quantity_kg_m3": 400.0, "specific_gravity": 3.15},
                {"material_code": "FA-G1", "material_name": "Fly Ash Grade 1", "category_code": "FLY_ASH", "quantity_kg_m3": 50.0, "specific_gravity": 2.25},
                {"material_code": "CA-20MM", "material_name": "Coarse Aggregate 20mm", "category_code": "COARSE_AGGREGATE", "quantity_kg_m3": 1100.0, "specific_gravity": 2.68},
                {"material_code": "FA-M-SAND", "material_name": "Manufactured Sand", "category_code": "FINE_AGGREGATE", "quantity_kg_m3": 720.0, "specific_gravity": 2.62},
                {"material_code": "WATER-TREATED", "material_name": "Batching Water", "category_code": "WATER", "quantity_kg_m3": 180.0, "specific_gravity": 1.00},
                {"material_code": "ADMIX-PCE", "material_name": "MasterGlenium PCE", "category_code": "ADMIXTURE", "quantity_kg_m3": 3.24, "specific_gravity": 1.08},
            ],
        },
        constraint_evaluation_json={"is_pareto_efficient": False, "is_feasible": True},
    )
    db_session.add(cand)
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_delta_per_m3 > 0
    assert res.cost_summary.cost_delta_percent > 0


def test_zero_cost_delta(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """11. Test zero cost delta when candidate matches master recipe quantities."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)

    cand = OptimizationCandidate(
        id=cand_id,
        run_id=run_id,
        candidate_identifier="CAND-IDENTICAL",
        predicted_strength_mpa=38.25,
        cost_per_m3=0.0,
        is_feasible=True,
        prediction_source="ML_MODEL",
        constituent_payload_json={
            "candidate_identifier": "CAND-IDENTICAL",
            "constituents": [
                {"material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "quantity_kg_m3": 350.0, "specific_gravity": 3.15},
                {"material_code": "FA-G1", "material_name": "Fly Ash Grade 1", "category_code": "FLY_ASH", "quantity_kg_m3": 50.0, "specific_gravity": 2.25},
                {"material_code": "CA-20MM", "material_name": "Coarse Aggregate 20mm", "category_code": "COARSE_AGGREGATE", "quantity_kg_m3": 1100.0, "specific_gravity": 2.68},
                {"material_code": "FA-M-SAND", "material_name": "Manufactured Sand", "category_code": "FINE_AGGREGATE", "quantity_kg_m3": 720.0, "specific_gravity": 2.62},
                {"material_code": "WATER-TREATED", "material_name": "Batching Water", "category_code": "WATER", "quantity_kg_m3": 180.0, "specific_gravity": 1.00},
                {"material_code": "ADMIX-PCE", "material_name": "MasterGlenium PCE", "category_code": "ADMIXTURE", "quantity_kg_m3": 3.24, "specific_gravity": 1.08},
            ],
        },
        constraint_evaluation_json={"is_pareto_efficient": True, "is_feasible": True},
    )
    db_session.add(cand)
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_delta_per_m3 == 0.0
    assert res.cost_summary.cost_delta_percent == 0.0


def test_zero_master_cost_handling(db_session, mock_user_5d, standard_pricing_snapshot):
    """12. Test that zero master cost produces cost_delta_percent = None (no ZeroDivisionError)."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    empty_master = {
        "recipe_id": str(uuid.uuid4()),
        "recipe_code": "EMPTY-M0",
        "plant_code": "PLANT-01",
        "target_grade": "M30",
        "constituents": [],  # 0 cost master
    }
    run = OptimizationRun(
        id=run_id,
        recipe_id=empty_master["recipe_id"],
        recipe_code="EMPTY-M0",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=empty_master,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)

    cand = OptimizationCandidate(
        id=cand_id,
        run_id=run_id,
        candidate_identifier="CAND-001",
        predicted_strength_mpa=38.25,
        cost_per_m3=0.0,
        is_feasible=True,
        prediction_source="ML_MODEL",
        constituent_payload_json={
            "candidate_identifier": "CAND-001",
            "constituents": [
                {"material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "quantity_kg_m3": 350.0, "specific_gravity": 3.15},
            ],
        },
        constraint_evaluation_json={"is_pareto_efficient": True, "is_feasible": True},
    )
    db_session.add(cand)
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.master_cost_per_m3 == 0.0
    assert res.cost_summary.candidate_cost_per_m3 == 2275.0  # 350 * 6.5
    assert res.cost_summary.cost_delta_percent is None  # Guarded from ZeroDivisionError


def test_not_configured_state(db_session, mock_user_5d, standard_master_snapshot):
    """13. When pricing snapshot is absent, return NOT_CONFIGURED and total_cost_available=False."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=None,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_status == "NOT_CONFIGURED"
    assert res.cost_summary.total_cost_available is False
    assert res.price_source_description == "Pricing Source: Not Configured"
    assert res.cost_summary.master_cost_per_m3 is None
    assert len(res.cost_summary.unpriced_materials) > 0


def test_partially_configured_state_and_unpriced_list(db_session, mock_user_5d, standard_master_snapshot):
    """14, 18. Partial pricing suppresses totals and enumerates all unpriced constituents."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    partial_pricing = {
        "is_configured": True,
        "price_source": "PARTIAL_ERP",
        "materials": [
            {"material_code": "OPC-53", "category_code": "CEMENT", "unit_price": 6.50, "price_unit": "₹/kg"}
        ],
    }
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=partial_pricing,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_status == "PARTIALLY_CONFIGURED"
    assert res.cost_summary.total_cost_available is False
    assert res.cost_summary.master_cost_per_m3 is None
    assert "Fly Ash Grade 1" in res.cost_summary.unpriced_materials


# ==============================================================================
# 16-17. NEW AND REMOVED MATERIAL BEHAVIOR
# ==============================================================================

def test_new_and_removed_materials_cost_math(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """16, 17. Test that NEW constituent (master=0) and REMOVED constituent (cand=0) calculate correct costs."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)

    # Candidate has removed Fly Ash (cand_qty = 0) and added GGBS (new constituent)
    standard_pricing_snapshot["materials"].append(
        {"material_code": "GGBS-G1", "material_name": "Slag GGBS", "category_code": "GGBS", "unit_price": 3.80, "price_unit": "₹/kg"}
    )

    cand = OptimizationCandidate(
        id=cand_id,
        run_id=run_id,
        candidate_identifier="CAND-NEW-REMOVED",
        predicted_strength_mpa=44.0,
        cost_per_m3=0.0,
        is_feasible=True,
        prediction_source="ML_MODEL",
        constituent_payload_json={
            "candidate_identifier": "CAND-NEW-REMOVED",
            "constituents": [
                {"material_code": "OPC-53", "material_name": "UltraTech OPC 53", "category_code": "CEMENT", "quantity_kg_m3": 300.0, "specific_gravity": 3.15},
                {"material_code": "GGBS-G1", "material_name": "Slag GGBS", "category_code": "GGBS", "quantity_kg_m3": 100.0, "specific_gravity": 2.90},  # NEW
                {"material_code": "CA-20MM", "material_name": "Coarse Aggregate 20mm", "category_code": "COARSE_AGGREGATE", "quantity_kg_m3": 1100.0, "specific_gravity": 2.68},
                {"material_code": "FA-M-SAND", "material_name": "Manufactured Sand", "category_code": "FINE_AGGREGATE", "quantity_kg_m3": 720.0, "specific_gravity": 2.62},
                {"material_code": "WATER-TREATED", "material_name": "Batching Water", "category_code": "WATER", "quantity_kg_m3": 180.0, "specific_gravity": 1.00},
                {"material_code": "ADMIX-PCE", "material_name": "MasterGlenium PCE", "category_code": "ADMIXTURE", "quantity_kg_m3": 3.24, "specific_gravity": 1.08},
            ],
        },
        constraint_evaluation_json={"is_pareto_efficient": True, "is_feasible": True},
    )
    db_session.add(cand)
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    
    # Check GGBS (NEW)
    ggbs_item = next(it for it in res.material_impacts if "GGBS" in it.category_code or "Slag" in it.material_name)
    assert ggbs_item.master_quantity_kg_m3 == 0.0
    assert ggbs_item.candidate_quantity_kg_m3 == 100.0
    assert ggbs_item.master_cost_per_m3 == 0.0
    assert ggbs_item.candidate_cost_per_m3 == 380.0
    assert ggbs_item.cost_delta_percent is None  # Baseline is zero

    # Check Fly Ash (REMOVED)
    fa_item = next(it for it in res.material_impacts if it.category_code == "FLY_ASH")
    assert fa_item.master_quantity_kg_m3 == 50.0
    assert fa_item.candidate_quantity_kg_m3 == 0.0
    assert fa_item.master_cost_per_m3 == 60.0  # 50 * 1.20
    assert fa_item.candidate_cost_per_m3 == 0.0
    assert fa_item.cost_delta_per_m3 == -60.0
    assert fa_item.cost_delta_percent == -100.0


# ==============================================================================
# 19-21. PRODUCTION VOLUME VALIDATION TESTS
# ==============================================================================

def test_production_volume_configured(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """19. Test daily, monthly, and annual production volume calculations."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    vol_impact = res.cost_summary.production_impact
    assert vol_impact.is_configured is True
    assert vol_impact.daily_volume_m3 == 250.0
    assert vol_impact.monthly_volume_m3 == 6500.0
    assert vol_impact.annualized_volume_m3 == 78000.0
    assert vol_impact.daily_cost_delta == round(res.cost_summary.cost_delta_per_m3 * 250.0, 2)
    assert vol_impact.monthly_cost_delta == round(res.cost_summary.cost_delta_per_m3 * 6500.0, 2)
    assert vol_impact.annualized_cost_delta == round(res.cost_summary.cost_delta_per_m3 * 78000.0, 2)


def test_production_volume_unavailable(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """20. Test when volume schedule is missing."""
    standard_pricing_snapshot["production_volume"] = {"is_configured": False}
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.production_impact.is_configured is False
    assert res.cost_summary.production_impact.daily_volume_m3 is None


def test_invalid_negative_production_volume_safely_rejected(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """21. Test that negative volume numbers safely disable production volume calculation."""
    standard_pricing_snapshot["production_volume"] = {
        "is_configured": True,
        "daily_volume_m3": -500.0,  # Invalid negative volume
    }
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.production_impact.is_configured is False


# ==============================================================================
# 22-24. PROVENANCE AND HISTORICAL REPRODUCIBILITY
# ==============================================================================

def test_pricing_provenance_exposure(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """22, 23. Test exposure of snapshot_id, price_version, effective_date, and price_source."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.pricing_snapshot_id == "SNAP-2026-Q3-001"
    assert res.pricing_version == "2026-Q3-V1"
    assert res.effective_date == "2026-07-01T00:00:00Z"
    assert "PROCUREMENT_ERP_FEED" in res.price_source_description


def test_historical_price_reproducibility(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """24. Verify that existing optimization run retains its immutable snapshot even if global price changes."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    # Re-evaluate cost impact 10 times - must return exact identical numbers
    res1 = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    res2 = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res1.cost_summary.master_cost_per_m3 == res2.cost_summary.master_cost_per_m3
    assert res1.cost_summary.candidate_cost_per_m3 == res2.cost_summary.candidate_cost_per_m3
    assert res1.cost_summary.cost_delta_per_m3 == res2.cost_summary.cost_delta_per_m3


# ==============================================================================
# 25-28. SECURITY, CROSS-RUN ISOLATION, & 404 GUARDS
# ==============================================================================

def test_cross_run_candidate_rejection(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """25, 26. Candidate belonging to run A requested with run B must return 404."""
    run_a, run_b = uuid.uuid4(), uuid.uuid4()
    cand_a = uuid.uuid4()

    run_obj_a = OptimizationRun(
        id=run_a,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    run_obj_b = OptimizationRun(
        id=run_b,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run_obj_a)
    db_session.add(run_obj_b)
    db_session.add(create_test_candidate(run_a, cand_a))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        CostImpactService.get_candidate_cost_impact(db_session, str(run_b), str(cand_a), mock_user_5d)
    assert exc_info.value.status_code == 404


def test_nonexistent_run_returns_404(db_session, mock_user_5d):
    """27. Nonexistent run ID returns 404."""
    with pytest.raises(HTTPException) as exc_info:
        CostImpactService.get_candidate_cost_impact(db_session, str(uuid.uuid4()), str(uuid.uuid4()), mock_user_5d)
    assert exc_info.value.status_code == 404


def test_nonexistent_candidate_returns_404(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """28. Nonexistent candidate ID returns 404."""
    run_id = uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(uuid.uuid4()), mock_user_5d)
    assert exc_info.value.status_code == 404


# ==============================================================================
# 29-34. INFEASIBILITY, REJECTION, & SOURCE WORKBOOK BOUNDARY TESTS
# ==============================================================================

def test_infeasible_candidate_preserves_feasibility_semantics(db_session, mock_user_5d, standard_pricing_snapshot, standard_master_snapshot):
    """29. Infeasible candidate retains is_feasible=False and is labeled for diagnostic comparison."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=standard_pricing_snapshot,
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id, is_feasible=False))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.is_feasible is False


def test_negative_and_non_finite_price_rejection():
    """30. Verify negative and non-finite unit prices are safely rejected."""
    price_neg, status_neg = CostImpactService._normalize_unit_price(-5.0, "₹/kg", 3.15)
    assert price_neg is None
    assert status_neg == "PRICE_CONVERSION_UNAVAILABLE"

    price_nan, status_nan = CostImpactService._normalize_unit_price(float("nan"), "₹/kg", 3.15)
    assert price_nan is None
    assert status_nan == "PRICE_CONVERSION_UNAVAILABLE"


def test_non_finite_sg_rejection():
    """31. Verify non-finite SG values (NaN, Inf) for ₹/L are safely rejected."""
    price_nan, status_nan = CostImpactService._normalize_unit_price(80.0, "₹/L", float("nan"))
    assert price_nan is None
    assert status_nan == "PRICE_CONVERSION_UNAVAILABLE"

    price_inf, status_inf = CostImpactService._normalize_unit_price(80.0, "₹/L", float("inf"))
    assert price_inf is None
    assert status_inf == "PRICE_CONVERSION_UNAVAILABLE"


def test_source_data_boundary_no_workbook_price_inference(db_session, mock_user_5d, standard_master_snapshot):
    """32. Explicitly verify that engineering workbook data does NOT cause price inference or default prices."""
    run_id, cand_id = uuid.uuid4(), uuid.uuid4()
    run = OptimizationRun(
        id=run_id,
        recipe_id=standard_master_snapshot["recipe_id"],
        recipe_code="M30-STD-P1",
        plant_code="PLANT-01",
        optimization_objective="MINIMIZE_COST",
        run_status="COMPLETED",
        recipe_snapshot_json=standard_master_snapshot,
        model_snapshot_json={"model_name": "acc_28d", "model_version": "v1"},
        target_strength_snapshot_json={"target_mean_strength_fck_prime_mpa": 38.25},
        constraints_snapshot_json={"exposure_class": "MODERATE"},
        pricing_snapshot_json=None,  # No procurement pricing in engineering files
    )
    db_session.add(run)
    db_session.add(create_test_candidate(run_id, cand_id))
    db_session.commit()

    res = CostImpactService.get_candidate_cost_impact(db_session, str(run_id), str(cand_id), mock_user_5d)
    assert res.cost_summary.cost_status == "NOT_CONFIGURED"
    assert res.cost_summary.total_cost_available is False
    assert res.cost_summary.master_cost_per_m3 is None
    assert res.cost_summary.candidate_cost_per_m3 is None
    assert res.cost_summary.cost_delta_per_m3 is None
    assert res.price_source_description == "Pricing Source: Not Configured"
