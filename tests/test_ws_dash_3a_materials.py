"""Unit and Integration Tests for WS-DASH-3A Backend Workstream.

Tests:
1. Canonical Material Classification & Unknown Material Handling
2. Material Consumption Aggregation & Densities (kg/m3)
3. Batch Variance Analysis & IS 4926:2003 Annex E / Clause E-1 Compliance
4. Water/Moisture Telemetry Data Quality Status (LIMITED vs COMPLETE)
5. W/B, W/C Ratios & Authoritative Binder Intensity Index (kg/m3/MPa)
6. Scope Filters & Honest Empty Dataset Handling
7. Population Reconciliation (1,898 total vs 1,699 produced vs 199 planned vs 1,165 tested)
8. FastAPI HTTP Reporting API Endpoints
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
from src.database.models.master import Material, Plant, Recipe
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.user import User
from src.security.dependencies import get_current_user, get_db
from src.services.material_consumption_service import (
    BroadCategoryEnum,
    MaterialCategoryEnum,
    MaterialConsumptionService,
    classify_material_code,
)


# =========================================================================
# TEST FIXTURES
# =========================================================================

@pytest.fixture
def db_session():
    """Isolated database session fixture."""
    engine = get_database_engine()
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_admin_user():
    """Mock authenticated admin user."""
    return User(
        id=str(uuid.uuid4()),
        username="materials_tester",
        email="materials@acc.com",
        password_hash="hash",
        account_status="ACTIVE",
    )


@pytest.fixture
def setup_test_materials(db_session: Session):
    """Set up plants, recipes, materials, batches, consumptions, and cube break tests."""
    uid = uuid.uuid4().hex[:8]

    plant = Plant(
        id=str(uuid.uuid4()),
        plant_code=f"PLANT-{uid}",
        plant_name="Test Plant Phase 3",
        location="Mumbai Lab",
        timezone="Asia/Kolkata",
        is_deleted=False,
    )
    db_session.add(plant)

    # 1. Recipes
    recipe_m30 = Recipe(
        id=str(uuid.uuid4()),
        recipe_code=f"REC-M30-{uid}",
        recipe_name="M30 Standard Grade",
        grade="M-30",
        target_strength_mpa=30.0,
        is_deleted=False,
    )
    recipe_m40 = Recipe(
        id=str(uuid.uuid4()),
        recipe_code=f"REC-M40-{uid}",
        recipe_name="M40 High Flow",
        grade="M-40",
        target_strength_mpa=40.0,
        is_deleted=False,
    )
    db_session.add_all([recipe_m30, recipe_m40])
    db_session.flush()

    # 2. Materials (Standard Canonical Codes)
    mat_defs = [
        ("CEMENT", "OPC 53 Grade Cement"),
        ("GGBS", "Ground Granulated Blast Furnace Slag"),
        ("AGGREGATE_COARSE", "20mm Coarse Aggregate"),
        ("AGGREGATE_FINE", "Crushed Sand (M-Sand)"),
        ("WATER", "Batch Mixing Water"),
        ("ADMIXTURE", "PCE Superplasticizer"),
        (f"SPECIAL_FIBER_{uid.upper()}", "Polymer Micro Fiber"),
    ]

    materials = {}
    for code, name in mat_defs:
        # Check if already exists in DB from another test fixture
        existing = db_session.query(Material).filter(Material.material_code == code, Material.is_deleted == False).first()
        if existing:
            materials[code] = existing
        else:
            m = Material(id=str(uuid.uuid4()), material_code=code, material_name=name, engineering_unit="kg", is_deleted=False)
            db_session.add(m)
            materials[code] = m

    db_session.flush()

    # 3. Batches
    # Batch 1: Completed, 1.0 m3 of M30 on Sep 16
    b1 = Batch(
        id=str(uuid.uuid4()),
        batch_number=f"B1-{uid}",
        order_id=str(uuid.uuid4()),
        dispatch_schedule_id=str(uuid.uuid4()),
        recipe_id=recipe_m30.id,
        plant_id=plant.id,
        production_status="COMPLETED",
        planned_quantity_m3=Decimal("1.0"),
        actual_quantity_m3=Decimal("1.0"),
        dataset_origin="OPERATIONAL_ACTUAL",
        created_at=datetime(2026, 9, 16, 10, 0, 0, tzinfo=timezone.utc),
        is_deleted=False,
    )

    # Batch 2: Completed, 2.0 m3 of M40 on Sep 17
    b2 = Batch(
        id=str(uuid.uuid4()),
        batch_number=f"B2-{uid}",
        order_id=str(uuid.uuid4()),
        dispatch_schedule_id=str(uuid.uuid4()),
        recipe_id=recipe_m40.id,
        plant_id=plant.id,
        production_status="COMPLETED",
        planned_quantity_m3=Decimal("2.0"),
        actual_quantity_m3=Decimal("2.0"),
        dataset_origin="OPERATIONAL_ACTUAL",
        created_at=datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc),
        is_deleted=False,
    )
    db_session.add_all([b1, b2])
    db_session.flush()

    unknown_key = f"SPECIAL_FIBER_{uid.upper()}"

    # 4. Material Consumptions for Batch 1 (1.0 m3) - All compliant with IS 4926 tolerances
    c1_items = [
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["CEMENT"].id, planned_quantity=Decimal("250.0"), actual_quantity=Decimal("252.0"), variance_quantity=Decimal("2.0"), variance_percentage=Decimal("0.80")),  # +0.8% <= 2% (PASS)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["GGBS"].id, planned_quantity=Decimal("100.0"), actual_quantity=Decimal("100.0"), variance_quantity=Decimal("0.0"), variance_percentage=Decimal("0.0")),     # 0.0% <= 2% (PASS)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["AGGREGATE_COARSE"].id, planned_quantity=Decimal("1100.0"), actual_quantity=Decimal("1115.0"), variance_quantity=Decimal("15.0"), variance_percentage=Decimal("1.36")),  # +1.36% <= 3% (PASS)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["AGGREGATE_FINE"].id, planned_quantity=Decimal("750.0"), actual_quantity=Decimal("740.0"), variance_quantity=Decimal("-10.0"), variance_percentage=Decimal("-1.33")), # -1.33% <= 3% (PASS)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["WATER"].id, planned_quantity=Decimal("140.0"), actual_quantity=Decimal("142.0"), variance_quantity=Decimal("2.0"), variance_percentage=Decimal("1.43"), moisture_percentage=Decimal("2.5")), # +1.43% <= 3% (PASS), has moisture probe
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b1.id, material_id=materials["ADMIXTURE"].id, planned_quantity=Decimal("3.5"), actual_quantity=Decimal("3.5"), variance_quantity=Decimal("0.0"), variance_percentage=Decimal("0.0")),     # 0.0% <= 3% (PASS)
    ]
    db_session.add_all(c1_items)

    # 5. Material Consumptions for Batch 2 (2.0 m3) - Breaches intentionally introduced
    c2_items = [
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b2.id, material_id=materials["CEMENT"].id, planned_quantity=Decimal("700.0"), actual_quantity=Decimal("725.0"), variance_quantity=Decimal("25.0"), variance_percentage=Decimal("3.57")),  # +3.57% > 2% (BREACH)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b2.id, material_id=materials["GGBS"].id, planned_quantity=Decimal("200.0"), actual_quantity=Decimal("198.0"), variance_quantity=Decimal("-2.0"), variance_percentage=Decimal("-1.00")), # -1.0% <= 2% (PASS)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b2.id, material_id=materials["AGGREGATE_COARSE"].id, planned_quantity=Decimal("2200.0"), actual_quantity=Decimal("2300.0"), variance_quantity=Decimal("100.0"), variance_percentage=Decimal("4.55")), # +4.55% > 3% (BREACH)
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b2.id, material_id=materials["WATER"].id, planned_quantity=Decimal("300.0"), actual_quantity=Decimal("320.0"), variance_quantity=Decimal("20.0"), variance_percentage=Decimal("6.67")), # +6.67% > 3% (BREACH), NO moisture probe
        BatchMaterialConsumption(id=str(uuid.uuid4()), batch_id=b2.id, material_id=materials[unknown_key].id, planned_quantity=Decimal("10.0"), actual_quantity=Decimal("10.0"), variance_quantity=Decimal("0.0"), variance_percentage=Decimal("0.0")),    # UNKNOWN material -> NOT_CLASSIFIABLE
    ]
    db_session.add_all(c2_items)

    # 6. QC Tests for B1 (28-day break = 38.5 MPa) and B2 (28-day break = 50.0 MPa)
    samp1 = ConcreteSample(id=str(uuid.uuid4()), sample_number=f"SMP1-{uid}", batch_id=b1.id, is_deleted=False)
    db_session.add(samp1)
    db_session.flush()
    cs1 = CubeSet(id=str(uuid.uuid4()), cube_set_number=f"CS1-{uid}", sample_id=samp1.id, number_of_cubes=3, is_deleted=False)
    db_session.add(cs1)
    db_session.flush()
    ct1 = CubeTest(id=str(uuid.uuid4()), cube_set_id=cs1.id, age_days=28, compressive_strength_mpa=Decimal("38.50"))
    db_session.add(ct1)

    samp2 = ConcreteSample(id=str(uuid.uuid4()), sample_number=f"SMP2-{uid}", batch_id=b2.id, is_deleted=False)
    db_session.add(samp2)
    db_session.flush()
    cs2 = CubeSet(id=str(uuid.uuid4()), cube_set_number=f"CS2-{uid}", sample_id=samp2.id, number_of_cubes=3, is_deleted=False)
    db_session.add(cs2)
    db_session.flush()
    ct2 = CubeTest(id=str(uuid.uuid4()), cube_set_id=cs2.id, age_days=28, compressive_strength_mpa=Decimal("50.00"))
    db_session.add(ct2)

    db_session.commit()

    return {
        "plant": plant,
        "recipe_m30": recipe_m30,
        "recipe_m40": recipe_m40,
        "materials": materials,
        "b1": b1,
        "b2": b2,
        "uid": uid,
    }


# =========================================================================
# TEST SUITE
# =========================================================================

def test_canonical_material_classification():
    """Verify authoritative classification of standard and non-standard material codes."""
    # 1. Binders (Cement)
    c_code, b_cat, tol, clause, is_annex_e = classify_material_code("CEMENT")
    assert c_code == MaterialCategoryEnum.CEMENT
    assert b_cat == BroadCategoryEnum.BINDER
    assert tol == 2.0
    assert "Cement ±2%" in clause
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code("OPC")
    assert c_code == MaterialCategoryEnum.CEMENT
    assert tol == 2.0
    assert is_annex_e == "CLASSIFIABLE"

    # 2. Mineral Admixtures (GGBS, Fly Ash, Micro Silica)
    c_code, b_cat, tol, _, is_annex_e = classify_material_code("GGBS")
    assert c_code == MaterialCategoryEnum.GGBS
    assert b_cat == BroadCategoryEnum.MINERAL_ADMIXTURE
    assert tol == 2.0
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code("FLY_ASH")
    assert c_code == MaterialCategoryEnum.FLY_ASH
    assert tol == 2.0
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code("MICRO_SILICA")
    assert c_code == MaterialCategoryEnum.MICRO_SILICA
    assert tol == 2.0
    assert is_annex_e == "CLASSIFIABLE"

    # 3. Aggregates, Water & Chemical Admixtures (±3%)
    c_code, b_cat, tol, _, is_annex_e = classify_material_code("AGGREGATE_COARSE")
    assert c_code == MaterialCategoryEnum.AGGREGATE_COARSE
    assert b_cat == BroadCategoryEnum.AGGREGATE
    assert tol == 3.0
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code("SAND")
    assert c_code == MaterialCategoryEnum.AGGREGATE_FINE
    assert tol == 3.0
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, clause, is_annex_e = classify_material_code("WATER")
    assert c_code == MaterialCategoryEnum.WATER
    assert b_cat == BroadCategoryEnum.WATER
    assert tol == 3.0
    assert "Weighing Accuracy" in clause
    assert is_annex_e == "CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code("ADMIXTURE")
    assert c_code == MaterialCategoryEnum.ADMIXTURE
    assert b_cat == BroadCategoryEnum.CHEMICAL_ADMIXTURE
    assert tol == 3.0
    assert is_annex_e == "CLASSIFIABLE"

    # 4. Unknown Material Handling (Strict NOT_CLASSIFIABLE, tol is None)
    c_code, b_cat, tol, clause, is_annex_e = classify_material_code("RANDOM_FIBER_X")
    assert c_code == MaterialCategoryEnum.UNKNOWN
    assert b_cat == BroadCategoryEnum.UNKNOWN
    assert tol is None
    assert clause is None
    assert is_annex_e == "NOT_CLASSIFIABLE"

    c_code, b_cat, tol, _, is_annex_e = classify_material_code(None)
    assert c_code == MaterialCategoryEnum.UNKNOWN
    assert is_annex_e == "NOT_CLASSIFIABLE"


def test_material_consumption_aggregation(db_session: Session, setup_test_materials):
    """Verify material consumption summary endpoint calculations & density per m3."""
    ctx = setup_test_materials
    plant_cd = ctx["plant"].plant_code

    summary = MaterialConsumptionService.get_material_summary(
        db=db_session,
        plant_code=plant_cd,
    )

    assert summary.total_batches == 2
    assert summary.total_produced_batches == 2
    assert summary.material_consumption_batch_count == 2
    assert summary.total_volume_m3 == 3.0  # 1.0 m3 + 2.0 m3

    # Total planned: 5753.5 kg, Total actual: 5905.5 kg
    assert summary.total_planned_material_kg == 5753.5
    assert summary.total_actual_material_kg == 5905.5
    assert summary.total_variance_kg == 152.0
    assert summary.overall_variance_percentage == pytest.approx(2.64, rel=1e-2)

    # Check total binder and water consumption
    # Binders actual: 252 (cem1) + 100 (ggbs1) + 725 (cem2) + 198 (ggbs2) = 1275.0 kg
    assert summary.total_binder_consumption_kg == 1275.0
    # Water actual: 142 + 320 = 462.0 kg
    assert summary.total_water_consumption_kg == 462.0

    # Verify per-item densities: Cement actual = 977 kg / 3 m3 = 325.67 kg/m3
    cem_item = next(i for i in summary.items if i.material_code == "CEMENT")
    assert cem_item.actual_quantity_kg == 977.0
    assert cem_item.consumption_kg_per_m3 == pytest.approx(325.67, rel=1e-2)


def test_batch_variance_is4926_compliance(db_session: Session, setup_test_materials):
    """Verify IS 4926:2003 Annex E weighing accuracy tolerances and breach reporting."""
    ctx = setup_test_materials
    plant_cd = ctx["plant"].plant_code

    variance_resp = MaterialConsumptionService.get_batch_variance_analysis(
        db=db_session,
        plant_code=plant_cd,
    )

    # 11 total material records across 2 batches (10 classifiable, 1 unknown)
    assert variance_resp.overall_summary.total_weighments == 11
    assert variance_resp.overall_summary.classifiable_weighments == 10
    assert variance_resp.overall_summary.annex_e_weighment_batch_count == 2
    # B1 has 6 compliant weighments.
    # B2: Cement (+3.57% > 2%), Water (+6.67% > 3%), CA (+4.55% > 3%) are non-compliant; GGBS (-1%) is compliant; Unknown is NOT_CLASSIFIABLE.
    # Total compliant = 6 + 1 = 7; non-compliant = 3; unclassified = 1
    assert variance_resp.overall_summary.compliant_weighments == 7
    assert variance_resp.overall_summary.non_compliant_weighments == 3
    assert variance_resp.overall_summary.unclassified_record_count == 1
    assert len(variance_resp.overall_summary.unclassified_material_codes) == 1
    assert variance_resp.overall_summary.annex_e_compliance_rate_pct == pytest.approx(70.0, rel=1e-2)

    # Verify Cement category
    cem_cat = next(c for c in variance_resp.categories if c.category_code == "BINDER")
    assert cem_cat.is4926_tolerance_pct == 2.0
    assert cem_cat.record_count == 2
    assert cem_cat.compliant_count == 1
    assert cem_cat.non_compliant_count == 1
    assert cem_cat.compliance_rate_pct == 50.0

    # Verify Mineral Admixture (GGBS) category
    min_cat = next(c for c in variance_resp.categories if c.category_code == "MINERAL_ADMIXTURE")
    assert min_cat.is4926_tolerance_pct == 2.0
    assert min_cat.record_count == 2
    assert min_cat.compliant_count == 2
    assert min_cat.compliance_rate_pct == 100.0

    # Verify Water / Moisture Data Quality Status
    wat_analysis = variance_resp.water_moisture_analysis
    assert wat_analysis.planned_water_kg == 440.0
    assert wat_analysis.actual_water_kg == 462.0
    assert wat_analysis.moisture_probe_records_count == 1
    assert wat_analysis.total_water_records_count == 2
    assert wat_analysis.data_quality_status == "LIMITED"  # 1/2 = 50% < 80%


def test_binder_efficiency_and_wb_ratios(db_session: Session, setup_test_materials):
    """Verify Water-to-Binder, Water-to-Cement, and Binder Intensity Index (kg/m3/MPa)."""
    ctx = setup_test_materials
    plant_cd = ctx["plant"].plant_code

    eff_resp = MaterialConsumptionService.get_efficiency_metrics(
        db=db_session,
        plant_code=plant_cd,
    )

    assert len(eff_resp.recipes) == 2
    assert eff_resp.fleet_summary.total_production_batches == 2
    assert eff_resp.fleet_summary.total_tested_batches_28d == 2
    assert eff_resp.fleet_summary.tested_28d_batch_count == 2

    # 1. Recipe M30:
    # Volume: 1.0 m3. Cement: 252 kg, Binder: 352 kg, Water: 142 kg. 28d Strength: 38.5 MPa
    # Actual W/B = 142 / 352 = 0.4034 -> 0.403
    # Actual W/C = 142 / 252 = 0.5635 -> 0.564
    # Binder Intensity = 352.0 / 38.5 = 9.14 kg/m3/MPa
    # Cement Intensity = 252.0 / 38.5 = 6.55 kg/m3/MPa
    r_m30 = next(r for r in eff_resp.recipes if r.grade == "M-30")
    assert r_m30.total_batches == 1
    assert r_m30.tested_batches_28d == 1
    assert r_m30.total_binder_content_kg_m3 == 352.0
    assert r_m30.cement_content_kg_m3 == 252.0
    assert r_m30.actual_wb_ratio == pytest.approx(0.403, rel=1e-2)
    assert r_m30.actual_wc_ratio == pytest.approx(0.564, rel=1e-2)
    assert r_m30.mean_28d_strength_mpa == 38.5
    assert r_m30.binder_intensity_index_kg_m3_per_mpa == pytest.approx(9.14, rel=1e-2)
    assert r_m30.cement_intensity_index_kg_m3_per_mpa == pytest.approx(6.55, rel=1e-2)
    assert r_m30.is_statistically_reliable is False
    assert r_m30.sample_size_status == "VERY_LOW"  # 1 test < 5

    # 2. Recipe M40:
    # Volume: 2.0 m3. Cement: 725 kg (362.5 kg/m3), Binder: 923 kg (461.5 kg/m3), Water: 320 kg (160 kg/m3).
    # Actual W/B = 320 / 923 = 0.3467 -> 0.347
    # 28d Strength = 50.0 MPa
    # Binder Intensity = 461.5 / 50.0 = 9.23 kg/m3/MPa
    r_m40 = next(r for r in eff_resp.recipes if r.grade == "M-40")
    assert r_m40.total_batches == 1
    assert r_m40.total_binder_content_kg_m3 == 461.5
    assert r_m40.actual_wb_ratio == pytest.approx(0.347, rel=1e-2)
    assert r_m40.mean_28d_strength_mpa == 50.0
    assert r_m40.binder_intensity_index_kg_m3_per_mpa == pytest.approx(9.23, rel=1e-2)

    # Fleet Mean Binder Intensity = Mean of per-batch intensities: (9.142857 + 9.23) / 2 = 9.19
    assert eff_resp.fleet_summary.fleet_avg_binder_intensity == pytest.approx(9.19, rel=1e-2)


def test_population_reconciliation_and_distinction(db_session: Session, setup_test_materials):
    """Verify distinction between total system batches, planned batches, and produced batches."""
    ctx = setup_test_materials
    plant = ctx["plant"]
    r30 = ctx["recipe_m30"]

    # Add 1 PLANNED unbatched order (no actual volume, no material records)
    b_planned = Batch(
        id=str(uuid.uuid4()),
        batch_number=f"B-PLANNED-{ctx['uid']}",
        order_id=str(uuid.uuid4()),
        dispatch_schedule_id=str(uuid.uuid4()),
        recipe_id=r30.id,
        plant_id=plant.id,
        production_status="PLANNED",
        planned_quantity_m3=Decimal("6.0"),
        actual_quantity_m3=None,
        dataset_origin="OPERATIONAL_ACTUAL",
        created_at=datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc),
        is_deleted=False,
    )
    db_session.add(b_planned)
    db_session.commit()

    # Material consumption should count produced batches (2) and note scheduled batches (1)
    summary = MaterialConsumptionService.get_material_summary(
        db=db_session,
        plant_code=plant.plant_code,
    )
    assert summary.total_produced_batches == 2
    assert summary.total_scheduled_batches == 1
    assert summary.total_batches == 2
    assert summary.material_consumption_batch_count == 2
    assert summary.total_volume_m3 == 3.0

    # Batch variance evaluates only the 2 completed batches with weighments
    var_resp = MaterialConsumptionService.get_batch_variance_analysis(
        db=db_session,
        plant_code=plant.plant_code,
    )
    assert var_resp.overall_summary.annex_e_weighment_batch_count == 2

    # Binder efficiency evaluates the 2 completed batches
    eff_resp = MaterialConsumptionService.get_efficiency_metrics(
        db=db_session,
        plant_code=plant.plant_code,
    )
    assert eff_resp.fleet_summary.total_production_batches == 2
    assert eff_resp.fleet_summary.tested_28d_batch_count == 2


def test_filters_and_empty_dataset_handling(db_session: Session, setup_test_materials):
    """Verify plant, recipe, and date filters, and honest empty states."""
    ctx = setup_test_materials
    plant_cd = ctx["plant"].plant_code
    r30_cd = ctx["recipe_m30"].recipe_code

    # 1. Recipe Filter for M30
    summary_m30 = MaterialConsumptionService.get_material_summary(
        db=db_session,
        plant_code=plant_cd,
        recipe_code=r30_cd,
    )
    assert summary_m30.total_batches == 1
    assert summary_m30.total_volume_m3 == 1.0
    assert summary_m30.total_binder_consumption_kg == 352.0

    # 2. Date Filter with plant isolation
    summary_date = MaterialConsumptionService.get_material_summary(
        db=db_session,
        plant_code=plant_cd,
        date_from=date(2026, 9, 17),
        date_to=date(2026, 9, 17),
    )
    # Only B2 was created on Sep 17 in this plant
    assert summary_date.total_batches == 1
    assert summary_date.total_volume_m3 == 2.0

    # 3. Non-matching Filter -> Honest Empty State (No errors)
    empty_summary = MaterialConsumptionService.get_material_summary(
        db=db_session,
        plant_code="NON_EXISTENT_PLANT_XYZ",
    )
    assert empty_summary.total_batches == 0
    assert empty_summary.total_volume_m3 == 0.0
    assert empty_summary.items == []
    assert empty_summary.total_actual_material_kg == 0.0

    empty_var = MaterialConsumptionService.get_batch_variance_analysis(
        db=db_session,
        plant_code="NON_EXISTENT_PLANT_XYZ",
    )
    assert empty_var.overall_summary.total_weighments == 0
    assert empty_var.overall_summary.annex_e_compliance_rate_pct == 0.0
    assert empty_var.categories == []

    empty_eff = MaterialConsumptionService.get_efficiency_metrics(
        db=db_session,
        plant_code="NON_EXISTENT_PLANT_XYZ",
    )
    assert empty_eff.fleet_summary.total_production_batches == 0
    assert empty_eff.recipes == []


def test_api_endpoints_via_testclient(db_session: Session, mock_admin_user, setup_test_materials):
    """Verify HTTP API route responses and status codes for all Phase 3 endpoints."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    app.dependency_overrides[get_db] = lambda: db_session

    client = TestClient(app)
    ctx = setup_test_materials
    plant_cd = ctx["plant"].plant_code

    try:
        # 1. GET /api/v1/reporting/material-consumption
        res_mat = client.get(f"/api/v1/reporting/material-consumption?plant_code={plant_cd}")
        assert res_mat.status_code == 200
        data_mat = res_mat.json()
        assert "items" in data_mat
        assert data_mat["total_batches"] == 2
        assert data_mat["total_produced_batches"] == 2
        assert data_mat["total_volume_m3"] == 3.0
        assert data_mat["scope_metadata"]["plant_code"] == plant_cd

        # 2. GET /api/v1/reporting/batch-variance
        res_var = client.get(f"/api/v1/reporting/batch-variance?plant_code={plant_cd}")
        assert res_var.status_code == 200
        data_var = res_var.json()
        assert "categories" in data_var
        assert "overall_summary" in data_var
        assert data_var["overall_summary"]["total_weighments"] == 11
        assert data_var["overall_summary"]["annex_e_weighment_batch_count"] == 2
        assert "standard_reference" in data_var["categories"][0]
        assert data_var["categories"][0]["standard_reference"]["standard"] == "IS 4926:2003"

        # 3. GET /api/v1/reporting/binder-efficiency
        res_eff = client.get(f"/api/v1/reporting/binder-efficiency?plant_code={plant_cd}")
        assert res_eff.status_code == 200
        data_eff = res_eff.json()
        assert "recipes" in data_eff
        assert "fleet_summary" in data_eff
        assert len(data_eff["recipes"]) == 2
        assert data_eff["fleet_summary"]["total_production_batches"] == 2
        assert data_eff["fleet_summary"]["tested_28d_batch_count"] == 2
        assert data_eff["recipes"][0]["binder_intensity_index_kg_m3_per_mpa"] is not None

    finally:
        app.dependency_overrides.clear()
