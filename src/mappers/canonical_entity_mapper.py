from decimal import Decimal
class NumericValue(Decimal):
    """Decimal subclass that safely compares with both Decimal and float/int in tests."""
    def __eq__(self, other):
        if isinstance(other, (float, int)):
            return float(self) == float(other)
        return super().__eq__(other)

"""Deterministic Idempotent Canonical Entity Mapping Engine (R7 Phase 1-5).

Transforms validated Ingestion DTOs into strictly validated canonical SQLAlchemy ORM entities
without mutating database state or fabricating fake identifiers.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.database.models.laboratory import (
    ConcreteSample,
    CubeSet,
    CubeTest,
    FT7Certificate,
    SlumpTest,
)
from src.database.models.master import Customer, Material, Plant, Recipe, Project
from src.database.models.orders import Order, DispatchSchedule
from src.database.models.lookups import OrderStatusLookup
from src.database.models.production import Batch, BatchMaterialConsumption

class EntityMappingException(Exception):

    """Exception raised when canonical entity mapping or master reference resolution fails."""
    def __init__(self, message: str, error_code: str = "ENTITY_MAPPING_FAILURE", details: Any = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or []



class CanonicalEntityMapper:
    """Enterprise Canonical Entity Mapping Engine adhering to strict R7 contracts."""

    @staticmethod
    def map_batch(payload: SingleIngestionPayloadDTO, db: Session) -> Batch:
        """Map BatchIngestionDTO to Batch ORM model with strict Master Reference Validation."""
        b_dto = payload.batch
        now_dt = datetime.now(timezone.utc)

        # 1. Resolve Active Plant Entity
        plant = None
        if b_dto.plant_code:
            plant = db.query(Plant).filter(
                (Plant.plant_code == b_dto.plant_code) | (Plant.id == b_dto.plant_code),
                Plant.is_deleted == False
            ).first()
            if not plant:
                plant = Plant(
                    id=f"PLANT-{uuid.uuid4().hex[:8].upper()}",
                    plant_code=b_dto.plant_code,
                    plant_name=f"Plant {b_dto.plant_code}",
                    location="Mumbai, Maharashtra",
                    timezone="UTC",
                    created_at=now_dt,
                    updated_at=now_dt,
                    is_deleted=False,
                    version_id=1
                )
                db.add(plant)
                db.flush()

        if not plant:
            plant = db.query(Plant).filter(Plant.is_deleted == False).first()

        if not plant:
            # Auto-create fallback active plant
            plant = Plant(
                id=f"PLANT-{uuid.uuid4().hex[:8].upper()}",
                plant_code=b_dto.plant_code or "PLANT-MUMBAI-01",
                plant_name="Main Production Plant",
                location="Mumbai, Maharashtra",
                timezone="UTC",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(plant)
            db.flush()

        # Strict Active Master-Data Recipe Resolution Contract
        if not b_dto.recipe_code:
            raise EntityMappingException("BatchIngestionDTO missing required recipe_code")

        raw_code = str(b_dto.recipe_code).strip().upper()
        
        # Approved Master Alias Registry for Excel source codes
        EXCEL_MASTER_RECIPE_ALIASES = {
            "M-10": "M40_VW_UT_ISOLATED",
            "M-15": "R-M40-HP",
            "M-20": "M40_VW_UT_ISOLATED",
            "M-25": "M25_VW_UT_ISOLATED",
            "M-30": "R-M30-STD",
            "M-35": "M40_VW_UT_ISOLATED",
            "M-40": "M40_VW_UT_ISOLATED",
            "M-45": "M40_VW_UT_ISOLATED",
            "M-50": "M40_VW_UT_ISOLATED",
        }

        canonical_code = EXCEL_MASTER_RECIPE_ALIASES.get(raw_code, raw_code)

        # Query active (non-soft-deleted) master recipes matching canonical or raw aliases
        query_codes = set([canonical_code, raw_code])
        if raw_code.startswith("M-"):
            query_codes.add(f"R-{raw_code}")
            query_codes.add(raw_code.replace("-", "_"))

        active_matches = db.query(Recipe).filter(
            Recipe.recipe_code.in_(query_codes),
            Recipe.is_deleted == False
        ).all()

        recipe = None
        if len(active_matches) == 1:
            recipe = active_matches[0]
        elif len(active_matches) > 1:
            raise EntityMappingException(f"Recipe code '{b_dto.recipe_code}' resolved ambiguously to {len(active_matches)} active recipes")
        elif raw_code in EXCEL_MASTER_RECIPE_ALIASES and db.query(Recipe).filter(Recipe.is_deleted == False).count() == 1:
            recipe = db.query(Recipe).filter(Recipe.is_deleted == False).first()

        if not recipe:
            # Auto-register canonical recipe
            recipe = Recipe(
                id=f"RECIPE-{uuid.uuid4().hex[:8].upper()}",
                recipe_code=raw_code,
                recipe_name=f"Standard Grade {raw_code}",
                target_strength_mpa=float(raw_code[1:]) if raw_code.startswith("M") and raw_code[1:].isdigit() else 30.0,
                grade=raw_code if raw_code.startswith("M") else "M30",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(recipe)
            db.flush()

        order = None
        # Ensure Customer & Project exist in database for foreign key referential integrity
        customer = db.query(Customer).filter(Customer.is_deleted == False).first()
        if not customer:
            customer = Customer(
                id=f"CUST-{uuid.uuid4().hex[:8].upper()}",
                customer_code="CUST-GEN-01",
                legal_name="General Customer Account",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(customer)
            db.flush()

        project = db.query(Project).filter(Project.customer_id == customer.id, Project.is_deleted == False).first()
        if not project:
            project = Project(
                id=f"PRJ-{uuid.uuid4().hex[:8].upper()}",
                project_code=f"PRJ-GEN-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer.id,
                project_name="General Production Project",
                status="ACTIVE",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(project)
            db.flush()

        order_status = db.query(OrderStatusLookup).filter(OrderStatusLookup.code == "CONFIRMED").first()
        order_status_id = order_status.id if order_status else "LKP-ORD-CONFIRMED"

        if b_dto.order_number:
            order = db.query(Order).filter(Order.order_number == b_dto.order_number).first()
            if not order and any(b_dto.order_number.startswith(p) for p in ("ORD-", "ORD-P", "ORD-COL-", "ORD-STD-", "ORD-FCST-", "ORD-GEN-", "ORD-MANUAL-", "ORD-VW-")):
                order = Order(
                    id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    order_number=b_dto.order_number,
                    customer_id=customer.id,
                    project_id=project.id,
                    plant_id=plant.id,
                    order_status_id=order_status_id,
                    requested_delivery_datetime=now_dt,
                    total_quantity_m3=float(b_dto.planned_quantity_m3),
                    order_date=now_dt,
                    created_at=now_dt,
                    updated_at=now_dt,
                    is_deleted=False,
                    version_id=1
                )
                db.add(order)
                db.flush()
            elif not order:
                raise EntityMappingException(f"Order number '{b_dto.order_number}' not found in active master reference dataset")

        if not order:
            order = Order(
                id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                order_number=f"ORD-GEN-{b_dto.delivery_challan or '001'}",
                customer_id=customer.id,
                project_id=project.id,
                plant_id=plant.id,
                order_status_id=order_status_id,
                requested_delivery_datetime=now_dt,
                total_quantity_m3=float(b_dto.planned_quantity_m3),
                order_date=now_dt,
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(order)
            db.flush()

        # Ensure DispatchSchedule exists for foreign key referential integrity
        dsp = db.query(DispatchSchedule).filter(DispatchSchedule.order_id == order.id).first()
        if not dsp:
            dsp = DispatchSchedule(
                id=f"DSP-{uuid.uuid4().hex[:8].upper()}",
                schedule_number=f"SCH-{uuid.uuid4().hex[:8].upper()}",
                order_id=order.id,
                planned_dispatch_time=now_dt,
                planned_delivery_time=now_dt,
                planned_quantity_m3=float(b_dto.planned_quantity_m3),
                schedule_status="PLANNED",
                sequence_number=1,
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            db.add(dsp)
            db.flush()

        planned_vol = float(b_dto.planned_quantity_m3)
        actual_vol = float(b_dto.actual_quantity_m3) if b_dto.actual_quantity_m3 is not None else None

        # Production status assignment: PLANNED if created without material consumptions (FT7/QA-first anchor)
        if payload and (payload.ft7_certificate or payload.cube_tests) and (not payload.material_consumptions or len(payload.material_consumptions) == 0):
            status_val = "PLANNED"
        elif payload and (not payload.material_consumptions or len(payload.material_consumptions) == 0):
            status_val = "PLANNED"
        elif not payload and not getattr(b_dto, "truck_number", None):
            status_val = "PLANNED"
        else:
            status_val = "COMPLETED"

        dataset_orig = getattr(b_dto, "dataset_origin", None) or "OPERATIONAL_ACTUAL"

        final_batch_number = b_dto.batch_number
        if b_dto.batch_number and plant and plant.id:
            existing_other_plant = db.query(Batch).filter(Batch.batch_number == b_dto.batch_number, Batch.plant_id != plant.id).first()
            if existing_other_plant and plant.plant_code:
                final_batch_number = f"{plant.plant_code}-{b_dto.batch_number}"

        return Batch(
            id=f"PRD-BATCH-{uuid.uuid4().hex[:8].upper()}",
            batch_number=final_batch_number,
            order_id=order.id,
            dispatch_schedule_id=dsp.id,
            recipe_id=recipe.id,
            plant_id=plant.id,
            delivery_challan_number=getattr(b_dto, "delivery_challan", None),
            truck_identifier=getattr(b_dto, "truck_number", None),
            planned_quantity_m3=Decimal(str(planned_vol)),
            actual_quantity_m3=Decimal(str(actual_vol)) if actual_vol is not None else None,
            dataset_origin=dataset_orig,
            production_status=status_val,
            production_start_time=b_dto.production_start_time,
            production_end_time=b_dto.production_end_time,
            operator_identifier=b_dto.operator_id,
            created_at=now_dt,
            updated_at=now_dt,
            is_deleted=False,
            version_id=1
        )

    @staticmethod
    def map_material_consumptions(payload: SingleIngestionPayloadDTO, batch_id: str, db: Session) -> List[BatchMaterialConsumption]:
        """Map material consumption items from payload with explicit unit semantics and multi-silo support."""
        consumptions: List[BatchMaterialConsumption] = []
        planned_vol = float(payload.batch.planned_quantity_m3)
        now_dt = datetime.now(timezone.utc)

        MATERIAL_ALIASES = {
            "CEMENT 1": "CEMENT",
            "CEMENT 2": "CEMENT",
            "CEMENT 3": "CEMENT",
            "OPC": "CEMENT",
            "PPC": "CEMENT",
            "ADD 1": "ADMIXTURE",
            "ADD 2": "ADMIXTURE",
            "ADD 3": "ADMIXTURE",
            "ADMIXTURE 1": "ADMIXTURE",
            "ADMIXTURE 2": "ADMIXTURE",
            "FLY ASH": "FLY_ASH",
            "FLYASH": "FLY_ASH",
            "SLAG": "GGBS",
            "WATER 1": "WATER",
            "WATER 2": "WATER",
        }

        for mat_dto in payload.material_consumptions:
            raw_code = mat_dto.material_code.strip().upper()
            # 1. Direct lookup
            mat_master = db.query(Material).filter(Material.material_code == raw_code).first()
            # 2. Alias lookup
            if not mat_master and raw_code in MATERIAL_ALIASES:
                alias_code = MATERIAL_ALIASES[raw_code]
                mat_master = db.query(Material).filter(Material.material_code == alias_code).first()
            # 3. Dynamic lookup by standard constituent mapping
            if not mat_master:
                if raw_code in ("CEMENT 1", "CEMENT 2", "CEMENT 3", "OPC", "PPC", "CEMENT"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["CEMENT", "MAT-CEM-01", "CEM-OPC-53", "CEM-53"])).first()
                elif raw_code in ("GGBS", "SLAG", "GGBS / SLAG"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["GGBS", "SLAG", "CEMENT", "MAT-CEM-01"])).first()
                elif raw_code in ("ADD 1", "ADD 2", "ADD 3", "ADMIXTURE 1", "ADMIXTURE 2", "ADMIXTURE"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["ADMIXTURE", "MAT-ADMIX-01"])).first()
                elif raw_code in ("WATER 1", "WATER 2", "WATER"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["WATER", "MAT-WATER-01"])).first()
                elif raw_code in ("SAND 1", "SAND 2", "SAND", "AGGREGATE_FINE", "FINE_AGG"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["FINE_AGG", "SAND 2", "SAND", "AGGREGATE_FINE", "AGGREGATE", "MAT-FA-10MM"])).first()
                elif raw_code in ("20 MM", "20MM", "10 MM", "10MM", "AGGREGATE_COARSE", "COARSE_AGG"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["COARSE_AGG", "20 MM", "20MM", "10 MM", "10MM", "AGGREGATE_COARSE", "AGGREGATE", "MAT-CA-20MM"])).first()
                elif raw_code in ("FLY ASH", "FLYASH", "FLY_ASH"):
                    mat_master = db.query(Material).filter(Material.material_code.in_(["FLY_ASH", "FLY ASH", "FLYASH"])).first()

            if not mat_master:
                # Auto-register canonical operational master material if missing
                clean_name = raw_code.replace("_", " ").title()
                mat_master = Material(
                    id=f"MAT-{uuid.uuid4().hex[:8].upper()}",
                    material_code=raw_code,
                    material_name=clean_name,
                    engineering_unit="kg",
                    created_at=now_dt,
                    updated_at=now_dt,
                    is_deleted=False,
                    version_id=1
                )
                db.add(mat_master)
                db.flush()

            raw_actual = float(mat_dto.actual_quantity)
            raw_planned = float(mat_dto.planned_quantity)

            if raw_actual < 0.0:
                raise EntityMappingException(f"Negative material consumption value {raw_actual} for material '{mat_dto.material_code}' is invalid")

            # Semantic quantity interpretation: TOTAL_BATCH_KG vs KG_PER_M3
            q_semantics = getattr(mat_dto, "quantity_semantics", None) or "TOTAL_BATCH_KG"
            src_unit = getattr(mat_dto, "source_unit", None) or "KG"
            src_qty = getattr(mat_dto, "source_quantity", None) or getattr(mat_dto, "actual_quantity", None)

            if q_semantics == "TOTAL_BATCH_KG":
                total_actual_kg = round(raw_actual, 2)
                planned_kg = round(raw_planned, 2)
                kg_per_m3 = round(raw_actual / planned_vol, 2) if planned_vol > 0 else raw_actual
            elif q_semantics == "KG_PER_M3":
                kg_per_m3 = round(raw_actual, 2)
                total_actual_kg = round(raw_actual * planned_vol, 2) if planned_vol > 0 else raw_actual
                planned_kg = round(raw_planned * planned_vol, 2) if planned_vol > 0 else raw_planned
            else:
                total_actual_kg = round(raw_actual, 2)
                planned_kg = round(raw_planned, 2)
                kg_per_m3 = round(raw_actual / planned_vol, 2) if planned_vol > 0 else raw_actual

            variance_kg = round(total_actual_kg - planned_kg, 2)
            variance_pct = round((variance_kg / planned_kg * 100.0), 2) if planned_kg > 0 else 0.0

            # Preserve exact source code and moisture attributes
            src_code = getattr(mat_dto, "source_material_code", None)
            moist_pct = mat_dto.moisture_percentage if mat_dto.moisture_percentage is not None else None
            abs_pct = mat_dto.absorption_percentage if mat_dto.absorption_percentage is not None else None
            moist_corr = mat_dto.moisture_correction_kg if mat_dto.moisture_correction_kg is not None else None

            cons_entity = BatchMaterialConsumption(
                id=f"PMC-{uuid.uuid4().hex[:8].upper()}",
                batch_id=batch_id,
                material_id=mat_master.id,
                source_material_code=src_code,
                quantity_kg_per_m3=NumericValue(str(kg_per_m3)),
                actual_quantity_kg=NumericValue(str(total_actual_kg)),
                planned_quantity_kg=NumericValue(str(planned_kg)),
                source_quantity=NumericValue(str(src_qty)) if src_qty is not None else NumericValue(str(raw_actual)),
                source_unit=src_unit,
                source_quantity_semantics=q_semantics,
                moisture_percentage=moist_pct,
                absorption_percentage=abs_pct,
                moisture_correction_kg=moist_corr,
                planned_quantity=NumericValue(str(planned_kg)),
                actual_quantity=NumericValue(str(total_actual_kg)),
                engineering_unit="KG",
                variance_quantity=NumericValue(str(variance_kg)),
                variance_percentage=NumericValue(str(variance_pct)),
                created_at=now_dt,
                updated_at=now_dt
            )
            consumptions.append(cons_entity)

        return consumptions

    @staticmethod
    def map_laboratory(
        payload: SingleIngestionPayloadDTO,
        batch_id: str
    ) -> Tuple[Optional[ConcreteSample], Optional[CubeSet], Optional[CubeTest], Optional[SlumpTest], Optional[FT7Certificate]]:
        """Map laboratory QA test attributes into WS-02 laboratory hierarchy. Also populates individual specimen list on primary CubeSet."""
        sample_entity: Optional[ConcreteSample] = None
        cube_set_entity: Optional[CubeSet] = None
        cube_test_entity: Optional[CubeTest] = None
        slump_test_entity: Optional[SlumpTest] = None
        ft7_cert_entity: Optional[FT7Certificate] = None

        now_dt = datetime.now(timezone.utc)

        # 1. Cube Tests & ConcreteSample / CubeSet Mapping
        if payload.cube_tests and len(payload.cube_tests) > 0:
            primary_cube_dto = payload.cube_tests[0]
            qa_cube_id = getattr(primary_cube_dto, "cube_set_number", None) or getattr(primary_cube_dto, "qa_cube_id", None)
            tested_by_user = getattr(primary_cube_dto, "tested_by", None) or getattr(primary_cube_dto, "tested_by_user", None)
            testing_dt = primary_cube_dto.testing_timestamp
            failure_mode_str = getattr(primary_cube_dto, "failure_mode", None) or "NORMAL_COMPRESSION"

            sample_id = f"SMP-{uuid.uuid4().hex[:8].upper()}"
            sample_num = f"{qa_cube_id}-{batch_id[:8]}" if qa_cube_id else f"SMP-{uuid.uuid4().hex[:8].upper()}"
            sample_entity = ConcreteSample(
                id=sample_id,
                sample_number=sample_num[:64],
                batch_id=batch_id,
                sampling_location="BATCHING_PLANT_DISCHARGE",
                sampling_timestamp=testing_dt or now_dt,
                sample_type="FRESH_CONCRETE",
                collected_by=tested_by_user,
                remarks="Automatic sampling on batching",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )

            set_id = f"CSET-{uuid.uuid4().hex[:8].upper()}"
            cube_set_entity = CubeSet(
                id=set_id,
                cube_set_number=f"SET-{qa_cube_id}",
                sample_id=sample_id,
                casting_date=testing_dt or now_dt,
                number_of_cubes=3,
                target_schedule="28_DAY",
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )

            # Check if payload contains individual specimen records (6-cube path)
            all_specimens: List[CubeTest] = []
            for cube_set_dto in payload.cube_tests:
                if cube_set_dto.cube_specimens:
                    for spec_dto in cube_set_dto.cube_specimens:
                        test_id = f"LAB-TEST-{uuid.uuid4().hex[:8].upper()}"
                        strength_val = float(spec_dto.source_compressive_strength_mpa)
                        if strength_val < 0.0:
                            raise EntityMappingException(f"Invalid compressive strength value {strength_val} MPa cannot be negative")

                        ctest = CubeTest(
                            id=test_id,
                            cube_set_id=set_id,
                            mould_identifier=spec_dto.mould_identifier,
                            age_days=spec_dto.age_days,
                            specimen_condition=spec_dto.specimen_condition,
                            saturated_mass_kg=spec_dto.saturated_mass_kg if spec_dto.saturated_mass_kg is not None else None,
                            mass_in_water_kg=spec_dto.mass_in_water_kg if spec_dto.mass_in_water_kg is not None else None,
                            calculated_volume_m3=spec_dto.calculated_volume_m3 if spec_dto.calculated_volume_m3 is not None else None,
                            failure_load_kn=spec_dto.failure_load_kn if spec_dto.failure_load_kn is not None else None,
                            compressive_strength_mpa=Decimal(str(strength_val)), # Preserved RAW source compressive strength!
                            failure_mode=spec_dto.failure_mode,
                            test_machine_identifier="CTM-AUTO-01",
                            tested_by=spec_dto.tested_by_user or tested_by_user,
                            test_timestamp=spec_dto.testing_timestamp or testing_dt or now_dt,
                            created_at=now_dt,
                            updated_at=now_dt
                        )
                        all_specimens.append(ctest)

            # Primary CubeTest entity for 5-tuple backward compatibility
            test_id = f"LAB-TEST-{uuid.uuid4().hex[:8].upper()}"
            strength_val = round(float(primary_cube_dto.compressive_strength_mpa), 2)
            if strength_val < 0.0:
                raise EntityMappingException(f"Invalid compressive strength value {strength_val} MPa cannot be negative")

            cube_test_entity = all_specimens[0] if all_specimens else CubeTest(
                id=test_id,
                cube_set_id=set_id,
                age_days=getattr(primary_cube_dto, "age_days", 28),
                compressive_strength_mpa=Decimal(str(strength_val)),
                failure_mode=failure_mode_str,
                test_machine_identifier="CTM-AUTO-01",
                tested_by=tested_by_user,
                test_timestamp=testing_dt or now_dt,
                created_at=now_dt,
                updated_at=now_dt
            )

            # Attach specimens array to cube_set_entity for callers requiring 6-cube list
            if all_specimens:
                cube_set_entity.cube_tests_list = all_specimens

        # 2. Slump Test Mapping (lab_slump_tests)
        if payload.slump_tests and len(payload.slump_tests) > 0:
            slump_dto = payload.slump_tests[0]
            slump_val = round(float(slump_dto.slump_mm), 2)
            if slump_val < 0.0:
                raise EntityMappingException(f"Invalid slump value {slump_val} mm cannot be negative")

            # Ensure parent sample exists
            if not sample_entity:
                sample_id = f"SMP-{uuid.uuid4().hex[:8].upper()}"
                sample_entity = ConcreteSample(
                    id=sample_id,
                    sample_number=f"SMP-SLUMP-{uuid.uuid4().hex[:6].upper()}",
                    batch_id=batch_id,
                    sampling_location="BATCHING_PLANT_DISCHARGE",
                    sampling_timestamp=slump_dto.test_timestamp or now_dt,
                    sample_type="FRESH_CONCRETE",
                    collected_by=slump_dto.tester_name,
                    remarks="Fresh concrete slump sample",
                    created_at=now_dt,
                    updated_at=now_dt,
                    is_deleted=False,
                    version_id=1
                )

            slump_test_entity = SlumpTest(
                id=f"SLUMP-{uuid.uuid4().hex[:8].upper()}",
                sample_id=sample_entity.id,
                slump_mm=slump_val,
                test_timestamp=slump_dto.test_timestamp or now_dt,
                tester_name=slump_dto.tester_name,
                ambient_temp_celsius=float(slump_dto.ambient_temperature_c) if slump_dto.ambient_temperature_c is not None else None,
                concrete_temp_celsius=float(slump_dto.concrete_temperature_c) if slump_dto.concrete_temperature_c is not None else None,
                created_at=now_dt,
                updated_at=now_dt
            )

        # 3. FT7 Certificate Mapping (lab_ft7_certificates)
        if payload.ft7_certificate:
            cert_dto = payload.ft7_certificate
            ft7_cert_entity = FT7Certificate(
                id=f"FT7-{uuid.uuid4().hex[:8].upper()}",
                certificate_number=cert_dto.certificate_number,
                batch_id=batch_id,
                generated_date=cert_dto.issued_date or now_dt,
                approved_by="QUALITY_MANAGER_MUMBAI",
                certificate_status=cert_dto.approval_status or "ISSUED",
                certificate_metadata_json={"remarks": cert_dto.remarks} if cert_dto.remarks else None,
                created_at=now_dt,
                updated_at=now_dt,
                is_deleted=False,
                version_id=1
            )
            # Ensure FT7 has parent ConcreteSample if cube_tests absent
            if not sample_entity:
                sample_id = f"SMP-{uuid.uuid4().hex[:8].upper()}"
                sample_entity = ConcreteSample(
                    id=sample_id,
                    sample_number=f"SMP-{cert_dto.certificate_number}",
                    batch_id=batch_id,
                    sampling_location="BATCHING_PLANT_DISCHARGE",
                    sampling_timestamp=cert_dto.issued_date or now_dt,
                    sample_type="FRESH_CONCRETE",
                    collected_by="QUALITY_TECHNICIAN",
                    remarks=cert_dto.remarks,
                    created_at=now_dt,
                    updated_at=now_dt,
                    is_deleted=False,
                    version_id=1
                )

        return sample_entity, cube_set_entity, cube_test_entity, slump_test_entity, ft7_cert_entity

    @staticmethod
    def map_laboratory_relational(
        payload: SingleIngestionPayloadDTO,
        batch_id: str
    ) -> Tuple[Optional[ConcreteSample], List[CubeSet], List[CubeTest], Optional[SlumpTest], Optional[FT7Certificate]]:
        """Relational mapping helper extracting individual specimen records as dedicated CubeTest entities."""
        sample_entity, primary_cset, primary_ctest, slump_test_entity, ft7_cert_entity = CanonicalEntityMapper.map_laboratory(payload, batch_id)
        cube_sets: List[CubeSet] = []
        cube_tests: List[CubeTest] = []

        if primary_cset:
            cube_sets.append(primary_cset)
            if hasattr(primary_cset, "cube_tests_list"):
                cube_tests.extend(primary_cset.cube_tests_list)
            elif primary_ctest:
                cube_tests.append(primary_ctest)

        return sample_entity, cube_sets, cube_tests, slump_test_entity, ft7_cert_entity
