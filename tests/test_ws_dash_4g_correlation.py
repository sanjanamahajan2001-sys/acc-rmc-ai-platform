"""WS-DASH-4G: Global Canonical Identity Resolution & Reconciliation Tests."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session
from src.database.engine import get_database_engine
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest, FT7Certificate
from src.database.models.master import Plant, Material, Recipe
from src.contracts.ingestion.batch import BatchIngestionDTO
from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
from src.contracts.ingestion.quality import CubeTestIngestionDTO, IndividualCubeSpecimenDTO, FT7CertificateIngestionDTO
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.services.ingestion_persistence_service import IngestionPersistenceService
from src.services.canonical_reconciliation_service import CanonicalReconciliationService
from src.mappers.canonical_entity_mapper import EntityMappingException


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session
        session.rollback()


def test_tier1_exact_timestamp_resolution(db_session):
    """Tier 1: Exactly matching plant + challan + timestamp resolves to same batch."""
    now_dt = datetime(2026, 5, 15, 13, 37, 18, tzinfo=timezone.utc)
    ch = f"TEST-CH-{uuid.uuid4().hex[:6]}"
    
    # 1. Ingest batch with materials
    p1 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-BR-{ch}",
            order_number=f"ORD-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            actual_quantity_m3=Decimal("6.0"),
            dataset_origin="OPERATIONAL_ACTUAL",
            production_start_time=now_dt
        ),
        material_consumptions=[
            MaterialConsumptionIngestionDTO(
                material_code="SAND 2",
                source_material_code="SAND 2",
                planned_quantity=Decimal("4500.0"),
                actual_quantity=Decimal("4520.0")
            )
        ]
    )
    svc = IngestionPersistenceService(db_session)
    res1 = svc.persist_canonical_payload(p1)
    batch_id_1 = res1["batch_id"]

    # 2. Ingest FT7 certificate with exact same timestamp
    p2 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-FT7-{ch}",
            order_number=f"ORD-FT7-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            production_start_time=now_dt
        ),
        cube_tests=[
            CubeTestIngestionDTO(
                cube_set_number=f"QC-SET-{ch}-28D",
                age_days=28,
                compressive_strength_mpa=Decimal("42.50"),
                testing_timestamp=now_dt
            )
        ]
    )
    res2 = svc.persist_canonical_payload(p2)
    assert res2["batch_id"] == batch_id_1, "Tier 1 exact timestamp must resolve to the same batch."


def test_tier2_calendar_date_resolution(db_session):
    """Tier 2: Different timestamps (e.g. 13:37:18 vs 00:00:00) on same calendar day resolve to unique candidate."""
    prod_time = datetime(2026, 5, 15, 13, 37, 18, tzinfo=timezone.utc)
    cast_date = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    ch = f"TEST-CH-{uuid.uuid4().hex[:6]}"

    p1 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-BR-{ch}",
            order_number=f"ORD-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            actual_quantity_m3=Decimal("6.0"),
            dataset_origin="OPERATIONAL_ACTUAL",
            production_start_time=prod_time
        ),
        material_consumptions=[
            MaterialConsumptionIngestionDTO(
                material_code="SAND 2",
                source_material_code="SAND 2",
                planned_quantity=Decimal("4500.0"),
                actual_quantity=Decimal("4520.0")
            )
        ]
    )
    svc = IngestionPersistenceService(db_session)
    res1 = svc.persist_canonical_payload(p1)
    batch_id_1 = res1["batch_id"]

    # Ingest FT7 with 00:00:00 casting timestamp
    p2 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-FT7-{ch}",
            order_number=f"ORD-FT7-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            production_start_time=cast_date
        ),
        cube_tests=[
            CubeTestIngestionDTO(
                cube_set_number=f"QC-SET-{ch}-28D",
                age_days=28,
                compressive_strength_mpa=Decimal("42.50"),
                testing_timestamp=cast_date
            )
        ]
    )
    res2 = svc.persist_canonical_payload(p2)
    assert res2["batch_id"] == batch_id_1, "Tier 2 calendar date match must resolve to unique existing parent batch."


def test_cross_plant_isolation(db_session):
    """Same challan on different plants must NOT merge."""
    now_dt = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc)
    ch = f"TEST-CH-{uuid.uuid4().hex[:6]}"

    svc = IngestionPersistenceService(db_session)

    p1 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-P1-{ch}",
            order_number=f"ORD-P1-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-ALPHA",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            production_start_time=now_dt
        )
    )
    res1 = svc.persist_canonical_payload(p1)

    p2 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-P2-{ch}",
            order_number=f"ORD-P2-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-BETA",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            production_start_time=now_dt
        )
    )
    res2 = svc.persist_canonical_payload(p2)
    assert res1["batch_id"] != res2["batch_id"], "Different plants with same challan must remain isolated."


def test_header_resolver_global_materials_and_aggregates():
    """Verify that all operational batching headers, aggregates, water, admixtures, and plant codes resolve canonically."""
    from src.mapping.engine import HeaderResolver
    from src.database.dictionary import CanonicalFieldID

    resolver = HeaderResolver()

    cases = [
        ("Water", CanonicalFieldID.FIELD_ACTUAL_WATER_KG),
        ("Admixture", CanonicalFieldID.FIELD_ACTUAL_ADMIXTURE_KG),
        ("SAND 1", CanonicalFieldID.FIELD_ACTUAL_SAND_KG),
        ("SAND 2", CanonicalFieldID.FIELD_ACTUAL_SAND_KG),
        ("10 MM", CanonicalFieldID.FIELD_ACTUAL_AGGREGATE_10MM_KG),
        ("20 MM", CanonicalFieldID.FIELD_ACTUAL_AGGREGATE_20MM_KG),
        ("Challan no. (Editable)", CanonicalFieldID.FIELD_DELIVERY_NOTE_ID),
        ("Plant Code", CanonicalFieldID.FIELD_PLANT_CODE),
        ("NS70", CanonicalFieldID.FIELD_PLANT_CODE),
        ("CEMENT 3", CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG),
        ("GGBS(Cement 1) Brand", CanonicalFieldID.FIELD_ACTUAL_GGBS_KG),
        ("Cement (2,3) Brand", CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG),
    ]

    for raw_header, expected_fid in cases:
        res = resolver.resolve_header(raw_header)
        assert res.canonical_field_id == expected_fid, (
            f"Expected header '{raw_header}' to resolve to {expected_fid}, got {res.canonical_field_id} (strategy: {res.resolution_strategy})"
        )


def test_multiple_batch_drops_same_challan_distinct_entities(db_session):
    """Verify that multiple scale batch drops under the same delivery challan are preserved as distinct entities without material conflict."""
    ch = f"TEST-7285-{uuid.uuid4().hex[:4]}"
    ts1 = datetime(2026, 2, 3, 12, 45, 10, tzinfo=timezone.utc)
    ts2 = datetime(2026, 2, 3, 12, 48, 30, tzinfo=timezone.utc)
    
    p1 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-BR-3091-{ch}",
            order_number=f"ORD-3091-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("6.0"),
            production_start_time=ts1
        ),
        material_consumptions=[
            MaterialConsumptionIngestionDTO(
                material_code="SAND 2",
                source_material_code="SAND 2",
                planned_quantity=Decimal("2790.0"),
                actual_quantity=Decimal("2790.0")
            )
        ]
    )
    
    p2 = SingleIngestionPayloadDTO(
        batch=BatchIngestionDTO(
            batch_number=f"BATCH-BR-3092-{ch}",
            order_number=f"ORD-3092-{ch}",
            delivery_challan=ch,
            plant_code="PLANT-NS70",
            recipe_code="M-30",
            planned_quantity_m3=Decimal("4.0"),
            production_start_time=ts2
        ),
        material_consumptions=[
            MaterialConsumptionIngestionDTO(
                material_code="SAND 2",
                source_material_code="SAND 2",
                planned_quantity=Decimal("1780.0"),
                actual_quantity=Decimal("1765.0")
            )
        ]
    )
    
    svc = IngestionPersistenceService(db_session)
    res1 = svc.persist_canonical_payload(p1)
    res2 = svc.persist_canonical_payload(p2)
    assert res1["batch_id"] != res2["batch_id"], "Separate scale batch drops must be preserved as distinct batch entities."


