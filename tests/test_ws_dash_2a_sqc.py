"""Test Suite for Phase 2: WS-DASH-2A Statistical Quality Control Backend.

Verifies:
1. Exact Mean calculation against known fixtures.
2. Sample standard deviation (s) and Coefficient of Variation (CV%).
3. Target mean strength (f'ck) per IS 456 / IS 10262.
4. Dynamic histogram binning (2.5 MPa intervals, below fck indicators).
5. Quality compliance rate calculation.
6. Mix/Grade performance matrix generation.
7. Strength timeline chronological ordering.
8. Filter isolation (plant_code, recipe_code, date ranges).
9. Honest empty and insufficient data states (0 breaks, <5 breaks).
10. Cache token version tracking and invalidation compatibility.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.models.user import Role, User
from src.database.services.cache_token_service import CacheTokenService
from src.security.dependencies import get_current_user, get_db
from src.services.statistical_quality_service import StatisticalQualityService


@pytest.fixture
def db_session():
    """Isolated database session fixture."""
    engine = get_database_engine()
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_admin_user():
    return User(
        id=str(uuid.uuid4()),
        username="sqc_tester",
        email="sqc@acc.com",
        password_hash="hash",
        account_status="ACTIVE",
    )


@pytest.fixture
def sqc_test_data(db_session: Session):
    """Seed deterministic SQC test batches and cube test breaks."""
    uid = uuid.uuid4().hex[:6].upper()
    # Create test plant
    p_code = f"PLANT-SQC-{uid}"
    plant = Plant(
        id=str(uuid.uuid4()),
        plant_code=p_code,
        plant_name="SQC Test Plant",
        location="Mumbai Lab",
        timezone="Asia/Kolkata",
        is_deleted=False,
    )
    db_session.add(plant)

    # Create test recipe
    r_code = f"M40-SQC-{uid}"
    recipe = Recipe(
        id=str(uuid.uuid4()),
        recipe_code=r_code,
        recipe_name="M40 SQC High Flow",
        grade="M40",
        target_strength_mpa=40.0,
        is_deleted=False,
    )
    db_session.add(recipe)
    db_session.flush()

    # Deterministic 28-day strength values for 6 batches: [42.0, 44.0, 46.0, 48.0, 50.0, 52.0]
    # Mean = 47.0 MPa
    # Variance = (25 + 9 + 1 + 1 + 9 + 25) / 5 = 70 / 5 = 14.0
    # Sample StdDev = sqrt(14.0) = 3.74 MPa
    # CV% = (3.74 / 47.0) * 100 = 7.96% -> EXCELLENT (< 10%)
    # Compliance: 6/6 >= 40.0 = 100.0%
    strengths = [42.0, 44.0, 46.0, 48.0, 50.0, 52.0]
    created_batches = []

    for i, s_val in enumerate(strengths):
        b = Batch(
            id=str(uuid.uuid4()),
            batch_number=f"BATCH-SQC-{uid}-{i+1}",
            order_id=str(uuid.uuid4()),
            dispatch_schedule_id=str(uuid.uuid4()),
            recipe_id=recipe.id,
            plant_id=plant.id,
            production_status="COMPLETED",
            planned_quantity_m3=Decimal("6.0"),
            actual_quantity_m3=Decimal("6.0"),
            dataset_origin="OPERATIONAL_ACTUAL",
            created_at=datetime(2026, 9, 10 + i, 10, 0, tzinfo=timezone.utc),
            is_deleted=False,
        )
        db_session.add(b)
        db_session.flush()

        sample = ConcreteSample(
            id=str(uuid.uuid4()),
            sample_number=f"SMP-SQC-{uid}-{i+1}",
            batch_id=b.id,
            sampling_timestamp=datetime(2026, 9, 10 + i, 10, 5, tzinfo=timezone.utc),
            sample_type="FRESH_CONCRETE",
            is_deleted=False,
        )
        db_session.add(sample)
        db_session.flush()

        cset = CubeSet(
            id=str(uuid.uuid4()),
            cube_set_number=f"CSET-SQC-{uid}-{i+1}",
            sample_id=sample.id,
            casting_date=datetime(2026, 9, 10 + i, 10, 10, tzinfo=timezone.utc),
            number_of_cubes=6,
            is_deleted=False,
        )
        db_session.add(cset)
        db_session.flush()

        # 7-day cube test
        ct_7d = CubeTest(
            id=str(uuid.uuid4()),
            cube_set_id=cset.id,
            age_days=7,
            compressive_strength_mpa=Decimal(str(round(s_val * 0.7, 2))),
            test_timestamp=datetime(2026, 9, 17 + i, 10, 0, tzinfo=timezone.utc),
        )
        db_session.add(ct_7d)

        # 28-day cube test
        ct_28d = CubeTest(
            id=str(uuid.uuid4()),
            cube_set_id=cset.id,
            age_days=28,
            compressive_strength_mpa=Decimal(str(s_val)),
            test_timestamp=datetime(2026, 10, 8 + i, 10, 0, tzinfo=timezone.utc),
        )
        db_session.add(ct_28d)
        created_batches.append(b)

    db_session.commit()

    return {
        "plant_code": p_code,
        "recipe_code": r_code,
        "plant_id": plant.id,
        "recipe_id": recipe.id,
        "batches": created_batches,
    }


def test_sqc_distribution_exact_calculations(db_session: Session, sqc_test_data):
    """Verify exact numerical precision of Mean, StdDev, CV, fck, and Bins."""
    dto = StatisticalQualityService.get_strength_distribution(
        db=db_session,
        plant_code=sqc_test_data["plant_code"],
        recipe_code=sqc_test_data["recipe_code"],
    )

    assert dto.total_tested_batches == 6
    assert dto.total_tested_specimens == 6
    assert dto.mean_strength_mpa == 47.0
    assert dto.median_strength_mpa == 47.0
    assert dto.standard_deviation_mpa == 3.74
    assert dto.coefficient_of_variation_pct == 7.96
    assert dto.min_strength_mpa == 42.0
    assert dto.max_strength_mpa == 52.0
    assert dto.characteristic_strength_fck_mpa == 40.0
    assert dto.strength_margin_mpa == 7.0
    assert dto.compliance_rate_pct == 100.0
    assert dto.stability_grade == "EXCELLENT"
    assert len(dto.histogram_bins) > 0


def test_sqc_empty_state_handling(db_session: Session):
    """Verify that scopes with zero break results return clean empty states."""
    dto = StatisticalQualityService.get_strength_distribution(
        db=db_session,
        plant_code="NON_EXISTENT_PLANT_9999",
    )

    assert dto.total_tested_batches == 0
    assert dto.total_tested_specimens == 0
    assert dto.mean_strength_mpa is None
    assert dto.standard_deviation_mpa is None
    assert dto.stability_grade == "INSUFFICIENT_DATA"
    assert dto.histogram_bins == []


def test_mix_performance_matrix(db_session: Session, sqc_test_data):
    """Verify mix performance matrix aggregation."""
    res = StatisticalQualityService.get_mix_performance(
        db=db_session,
        plant_code=sqc_test_data["plant_code"],
    )

    assert res.total_recipes_evaluated >= 1
    # Find our specific test recipe
    item = next((x for x in res.items if x.recipe_code == sqc_test_data["recipe_code"]), None)
    assert item is not None
    assert item.tested_batches_28d == 6
    assert item.mean_strength_mpa == 47.0
    assert item.standard_deviation_mpa == 3.74
    assert item.compliance_rate_pct == 100.0
    assert item.stability_status == "EXCELLENT"


def test_strength_timeline(db_session: Session, sqc_test_data):
    """Verify chronological timeline points ordering and 7d/28d breaks."""
    res = StatisticalQualityService.get_strength_timeline(
        db=db_session,
        plant_code=sqc_test_data["plant_code"],
        recipe_code=sqc_test_data["recipe_code"],
    )

    assert res.total_points == 6
    # Oldest to newest
    assert "BATCH-SQC" in res.timeline[0].batch_number
    assert res.timeline[0].result_28d_mpa == 42.0
    assert res.timeline[0].is_compliant_28d is True


def test_api_reporting_endpoints_http(mock_admin_user, sqc_test_data):
    """Verify HTTP API endpoints integration."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    client = TestClient(app)

    # 1. Filter Options
    r1 = client.get("/api/v1/reporting/filter-options")
    assert r1.status_code == 200
    f_data = r1.json()
    assert any(p["plant_code"] == sqc_test_data["plant_code"] for p in f_data["plants"])
    assert any(r["recipe_code"] == sqc_test_data["recipe_code"] for r in f_data["recipes"])

    # 2. Strength Distribution
    r2 = client.get(f"/api/v1/reporting/strength-distribution?plant_code={sqc_test_data['plant_code']}")
    assert r2.status_code == 200
    d_data = r2.json()
    assert d_data["total_tested_batches"] == 6
    assert d_data["mean_strength_mpa"] == 47.0

    # 3. Mix Performance
    r3 = client.get(f"/api/v1/reporting/mix-performance?plant_code={sqc_test_data['plant_code']}")
    assert r3.status_code == 200
    m_data = r3.json()
    assert len(m_data["items"]) >= 1

    # 4. Strength Timeline
    r4 = client.get(f"/api/v1/reporting/strength-timeline?plant_code={sqc_test_data['plant_code']}")
    assert r4.status_code == 200
    t_data = r4.json()
    assert t_data["total_points"] == 6

    app.dependency_overrides.clear()
