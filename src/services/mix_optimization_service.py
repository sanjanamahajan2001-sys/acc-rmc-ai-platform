"""Authoritative AI Mix Optimization Service (Phase 5A).

Manages immutable run creation, context snapshotting, target strength resolution,
and standards constraint baseline compilation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.contracts.optimization.models import (
    ConstraintItemDTO,
    ConstraintsSnapshotDTO,
    ModelSnapshotDTO,
    OptimizationRunResponseDTO,
    OptimizationRunTriggerRequestDTO,
    RecipeConstituentSnapshotDTO,
    RecipeSnapshotDTO,
    TargetStrengthSnapshotDTO,
)
from src.database.models.ai import ModelRegistry
from src.database.models.master import Material, MaterialCategory, Plant, Recipe, RecipeMaterial
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.user import SecurityAuditLog, User
from src.ml.registry.registry_service import ModelRegistryService
from src.services.statistical_quality_service import StatisticalQualityService
from src.services.statistical_quality_service import resolve_fck_from_recipe
from src.services.engineering_settings_service import EngineeringSettingsService


# IS 456 Table 8 Assumed Standard Deviation fallback (MPa)
IS456_ASSUMED_STANDARD_DEVIATION: Dict[str, float] = {
    "M10": 3.5,
    "M15": 3.5,
    "M20": 4.0,
    "M25": 4.0,
    "M30": 5.0,
    "M35": 5.0,
    "M40": 5.0,
    "M45": 5.0,
    "M50": 5.0,
    "M55": 5.5,
    "M60": 5.5,
    "M65": 5.5,
    "M70": 5.5,
    "M75": 5.5,
    "M80": 5.5,
}

# IS 10262:2019 Table 1 Factor X (N/mm2) for Target Mean Strength Dual-Criterion
IS10262_FACTOR_X: Dict[str, float] = {
    "M10": 5.0,
    "M15": 5.0,
    "M20": 5.5,
    "M25": 5.5,
    "M30": 6.5,
    "M35": 6.5,
    "M40": 6.5,
    "M45": 6.5,
    "M50": 6.5,
    "M55": 6.5,
    "M60": 6.5,
    "M65": 8.0,
    "M70": 8.0,
    "M75": 8.0,
    "M80": 8.0,
}

# IS 456 Table 5 Minimum Cementitious & Max Free W/B & Minimum Grade Limits for Reinforced Concrete (RCC)
IS456_TABLE_5_LIMITS: Dict[str, Dict[str, Any]] = {
    "MILD": {"min_cement": 300.0, "max_wb": 0.55, "min_grade_num": 20.0, "min_grade": "M20"},
    "MODERATE": {"min_cement": 300.0, "max_wb": 0.50, "min_grade_num": 25.0, "min_grade": "M25"},
    "SEVERE": {"min_cement": 320.0, "max_wb": 0.45, "min_grade_num": 30.0, "min_grade": "M30"},
    "VERY_SEVERE": {"min_cement": 340.0, "max_wb": 0.45, "min_grade_num": 35.0, "min_grade": "M35"},
    "VERY SEVERE": {"min_cement": 340.0, "max_wb": 0.45, "min_grade_num": 35.0, "min_grade": "M35"},
    "EXTREME": {"min_cement": 360.0, "max_wb": 0.40, "min_grade_num": 40.0, "min_grade": "M40"},
}


class MixOptimizationService:
    """Authoritative service for AI Mix Optimization Runs and Snapshot Management."""

    @classmethod
    def _capture_recipe_snapshot(cls, db: Session, recipe: Recipe) -> RecipeSnapshotDTO:
        """Extract and immutably snapshot current master recipe definition and material proportions."""
        constituents: List[RecipeConstituentSnapshotDTO] = []

        if recipe.items and len(recipe.items) > 0:
            for rm in recipe.items:
                mat = db.get(Material, rm.material_id)
                cat_code = None
                if mat and mat.category_id:
                    cat = db.get(MaterialCategory, mat.category_id)
                    if cat:
                        cat_code = cat.category_code

                constituents.append(
                    RecipeConstituentSnapshotDTO(
                        material_id=str(rm.material_id),
                        material_code=mat.material_code if mat else "UNKNOWN",
                        material_name=mat.material_name if mat else "Unknown Material",
                        category_code=cat_code,
                        target_quantity_kg_m3=float(rm.target_quantity),
                        engineering_unit=rm.engineering_unit or "kg",
                        default_density_kg_m3=float(mat.default_density_kg_m3) if mat and mat.default_density_kg_m3 else None,
                    )
                )
        else:
            # Fallback to historical production batches average if master items were not pre-configured
            sample_batches = (
                db.query(Batch)
                .filter(Batch.recipe_id == recipe.id, Batch.is_deleted == False)
                .order_by(desc(Batch.created_at))
                .limit(20)
                .all()
            )

            if sample_batches:
                batch_ids = [b.id for b in sample_batches]
                consumptions = (
                    db.query(
                        BatchMaterialConsumption.material_id,
                        func.avg(BatchMaterialConsumption.actual_quantity).label("avg_qty"),
                    )
                    .filter(BatchMaterialConsumption.batch_id.in_(batch_ids))
                    .group_by(BatchMaterialConsumption.material_id)
                    .all()
                )

                for mat_id, avg_qty in consumptions:
                    mat = db.get(Material, mat_id)
                    cat_code = None
                    if mat and mat.category_id:
                        cat = db.get(MaterialCategory, mat.category_id)
                        if cat:
                            cat_code = cat.category_code

                    constituents.append(
                        RecipeConstituentSnapshotDTO(
                            material_id=str(mat_id),
                            material_code=mat.material_code if mat else "UNKNOWN",
                            material_name=mat.material_name if mat else "Unknown Material",
                            category_code=cat_code,
                            target_quantity_kg_m3=round(float(avg_qty), 2),
                            engineering_unit="kg",
                            default_density_kg_m3=float(mat.default_density_kg_m3) if mat and mat.default_density_kg_m3 else None,
                        )
                    )

            if not constituents:
                # Default baseline design constituent distribution
                cement_qty = 380.0 if "40" in (recipe.grade or "") else 320.0
                water_qty = round(cement_qty * 0.45, 1)
                constituents = [
                    RecipeConstituentSnapshotDTO(
                        material_id="mat-cement-default",
                        material_code="CEMENT_OPC53",
                        material_name="OPC 53 Grade Cement",
                        category_code="CEMENT",
                        target_quantity_kg_m3=cement_qty,
                        engineering_unit="kg",
                    ),
                    RecipeConstituentSnapshotDTO(
                        material_id="mat-water-default",
                        material_code="WATER",
                        material_name="Batching Water",
                        category_code="WATER",
                        target_quantity_kg_m3=water_qty,
                        engineering_unit="kg",
                    ),
                    RecipeConstituentSnapshotDTO(
                        material_id="mat-fa-default",
                        material_code="SAND_ZONE2",
                        material_name="Fine Aggregate (River Sand)",
                        category_code="FINE_AGGREGATE",
                        target_quantity_kg_m3=680.0,
                        engineering_unit="kg",
                    ),
                    RecipeConstituentSnapshotDTO(
                        material_id="mat-ca-default",
                        material_code="CA_20MM",
                        material_name="Coarse Aggregate 20mm",
                        category_code="COARSE_AGGREGATE",
                        target_quantity_kg_m3=1150.0,
                        engineering_unit="kg",
                    ),
                ]

        return RecipeSnapshotDTO(
            recipe_id=str(recipe.id),
            recipe_code=recipe.recipe_code,
            recipe_name=recipe.recipe_name,
            mix_design_code=recipe.mix_design_code,
            grade=recipe.grade or "M30",
            target_strength_mpa=float(recipe.target_strength_mpa) if recipe.target_strength_mpa else 30.0,
            water_cement_ratio=float(recipe.water_cement_ratio) if recipe.water_cement_ratio else 0.45,
            slump_target_mm=float(recipe.slump_target_mm) if recipe.slump_target_mm else 120.0,
            nominal_max_aggregate_size_mm=float(recipe.nominal_max_aggregate_size_mm) if recipe.nominal_max_aggregate_size_mm else 20.0,
            exposure_class=recipe.exposure_class or "MODERATE",
            constituents=constituents,
        )

    @staticmethod
    def _capture_model_snapshot(db: Session) -> ModelSnapshotDTO:
        """Extract active model metadata from ModelRegistry with explicit governance validation state."""
        active_model = ModelRegistryService.get_active_model(db)
        if active_model:
            return ModelSnapshotDTO(
                model_registry_id=str(active_model.id),
                model_name=active_model.model_name,
                model_version=active_model.model_version,
                framework=active_model.framework,
                algorithm=active_model.algorithm,
                feature_schema_version=active_model.feature_schema_version,
                checksum=active_model.checksum,
                deployment_status=active_model.deployment_status,
                validation_status="ACTIVE — BASELINE MODEL (LIMITED VALIDATION)",
                prediction_source_semantics="ML_MODEL (Analytical Prediction — Limited Validation)",
            )
        return ModelSnapshotDTO(
            model_registry_id=None,
            model_name="Heuristic Fallback Engine",
            model_version="HEURISTIC-1.0",
            framework="RuleEngine",
            algorithm="Physical Heuristic Equation (IS 456 / IS 10262)",
            feature_schema_version="1.0.0",
            checksum=None,
            deployment_status="ACTIVE",
            validation_status="ACTIVE — BASELINE MODEL (LIMITED VALIDATION)",
            prediction_source_semantics="HEURISTIC (Rule-Based Fallback)",
        )

    @staticmethod
    def _capture_target_strength_snapshot(db: Session, recipe: Recipe, plant_id: Optional[str] = None) -> TargetStrengthSnapshotDTO:
        """Resolve target mean strength f'ck = max(fck + Z*sigma, fck + X) using Phase 2A SQC hierarchy or IS 456 Table 8."""
        fck = resolve_fck_from_recipe(recipe.target_strength_mpa, recipe.grade, 30.0)

        # Attempt to resolve empirical SQC standard deviation if sufficient historical data exists
        sigma = None
        source = "IS 10262:2019 Table 2"

        try:
            sqc_summary = StatisticalQualityService.get_mix_performance(db=db, target_recipe_id=str(recipe.id), target_plant_id=plant_id)
            if sqc_summary.items:
                item = sqc_summary.items[0]
                if item.tested_batches_28d >= 30 and item.standard_deviation_mpa and item.standard_deviation_mpa > 0:
                    sigma = float(item.standard_deviation_mpa)
                    source = "HISTORICAL_SQC_SAMPLE"
        except Exception:
            pass

        grade_key = (recipe.grade or "M30").upper().replace("_", "").replace("-", "")
        if sigma is None:
            sigma = IS456_ASSUMED_STANDARD_DEVIATION.get(grade_key, 5.0)

        # Fetch active engineering settings
        active_settings = EngineeringSettingsService.get_active_settings(db)
        active_z = float(active_settings.get("confidence_multiplier_z", 1.65))
        std_name = active_settings.get("standard_name", "IS 10262:2019 Cl. 4.2")

        # IS 10262:2019 Clause 4.2 Dual-Criterion: target_mean = max(fck + Z*s, fck + X)
        x_val = IS10262_FACTOR_X.get(grade_key, 6.5)
        target_1 = fck + (active_z * sigma)
        target_2 = fck + x_val
        target_fck_prime = round(max(target_1, target_2), 2)

        return TargetStrengthSnapshotDTO(
            characteristic_strength_fck_mpa=fck,
            standard_deviation_mpa=round(sigma, 2),
            standard_deviation_source=source,
            target_mean_strength_fck_prime_mpa=target_fck_prime,
            formula_reference=f"f'ck = max(fck + {active_z:.2f}*s, fck + X) ({std_name})",
        )

    @classmethod
    def _capture_constraints_snapshot(cls, db_or_recipe: Any, recipe: Optional[Recipe] = None) -> ConstraintsSnapshotDTO:
        """Extract standards-grounded constraints dynamically from active Engineering Settings."""
        if isinstance(db_or_recipe, Session):
            db = db_or_recipe
            target_recipe = recipe
        else:
            db = None
            target_recipe = db_or_recipe

        exp = (target_recipe.exposure_class or "MODERATE").upper().strip() if target_recipe else "MODERATE"
        exp_key = exp.replace(" ", "_")

        active_settings = EngineeringSettingsService.get_active_settings(db)
        exposure_map = active_settings.get("exposure_constraints_json", {})

        # Exposure tier parameters
        exp_cfg = exposure_map.get(exp_key) or exposure_map.get(exp) or IS456_TABLE_5_LIMITS.get(exp, IS456_TABLE_5_LIMITS["MODERATE"])
        min_cement = float(exp_cfg.get("min_cement_kg_m3", exp_cfg.get("min_cement", 300.0)))
        max_wb = float(exp_cfg.get("max_wb_ratio", exp_cfg.get("max_wb", 0.50)))
        min_grade_str = str(exp_cfg.get("min_grade", "M25"))
        min_grade_val = float(min_grade_str.upper().replace("M", "").replace("-", "").strip()) if any(c.isdigit() for c in min_grade_str) else float(exp_cfg.get("min_grade_num", 25.0))

        # SCM substitution parameters (Fly Ash, GGBS, Micro-Silica)
        scm_map = active_settings.get("scm_substitution_bounds_json", {})
        fa_cfg = scm_map.get("fly_ash") or scm_map.get("FLY_ASH") or scm_map.get("FLYASH") or {}
        ggbs_cfg = scm_map.get("ggbs") or scm_map.get("GGBS") or scm_map.get("SLAG") or {}
        ms_cfg = scm_map.get("micro_silica") or scm_map.get("MICRO_SILICA") or scm_map.get("silica_fume") or scm_map.get("SILICA_FUME") or {}

        max_fa = float(fa_cfg.get("max_replacement_percent") or fa_cfg.get("max_percent") or fa_cfg.get("max_replacement_pct") or 35.0)
        max_ggbs = float(ggbs_cfg.get("max_replacement_percent") or ggbs_cfg.get("max_percent") or ggbs_cfg.get("max_replacement_pct") or 50.0)
        max_ms = float(ms_cfg.get("max_replacement_percent") or ms_cfg.get("max_percent") or ms_cfg.get("max_replacement_pct") or 10.0)

        items = [
            ConstraintItemDTO(
                constraint_name="Minimum Concrete Grade (RCC)",
                standard_reference=f"IS 456:2000 Table 5 ({exp} Reinforced)",
                limit_value=min_grade_val,
                unit="MPa (Grade)",
                comparison="MINIMUM",
                status="ACTIVE",
            ),
            ConstraintItemDTO(
                constraint_name="Minimum Cementitious Content",
                standard_reference=f"IS 456:2000 Table 5 ({exp} Exposure)",
                limit_value=min_cement,
                unit="kg/m³",
                comparison="MINIMUM",
                status="ACTIVE",
            ),
            ConstraintItemDTO(
                constraint_name="Maximum Free Water-Binder Ratio",
                standard_reference=f"IS 456:2000 Table 5 ({exp} Exposure)",
                limit_value=max_wb,
                unit="ratio",
                comparison="MAXIMUM",
                status="ACTIVE",
            ),
            ConstraintItemDTO(
                constraint_name="Maximum Fly Ash Replacement",
                standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                limit_value=max_fa,
                unit="%",
                comparison="MAXIMUM",
                status="ACTIVE",
            ),
            ConstraintItemDTO(
                constraint_name="Maximum GGBS Replacement",
                standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                limit_value=max_ggbs,
                unit="%",
                comparison="MAXIMUM",
                status="ACTIVE",
            ),
            ConstraintItemDTO(
                constraint_name="Maximum Micro-Silica Replacement",
                standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                limit_value=max_ms,
                unit="%",
                comparison="MAXIMUM",
                status="ACTIVE",
            ),
        ]

        return ConstraintsSnapshotDTO(
            exposure_class=exp,
            standard_edition=f"{active_settings.get('standard_name', 'IS 456:2000 Table 5 & IS 10262:2019')}",
            configuration_version="1.0.0",
            items=items,
        )

    @classmethod
    def trigger_optimization_run(
        cls,
        db: Session,
        request: OptimizationRunTriggerRequestDTO,
        current_user: Optional[User] = None,
        correlation_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OptimizationRunResponseDTO:
        """Create and persist an immutable OptimizationRun snapshot."""
        # 1. Validate Recipe by ID or Code
        recipe = db.get(Recipe, request.recipe_id)
        if not recipe or recipe.is_deleted:
            recipe = db.scalar(select(Recipe).where(Recipe.recipe_code == request.recipe_id, Recipe.is_deleted == False))
        if not recipe or recipe.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Master Recipe '{request.recipe_id}' not found or has been deleted.",
            )

        # 2. Validate Plant by Code or ID (Fallback to primary active plant if omitted/defaulted)
        plant = None
        if request.plant_code:
            plant = db.scalar(select(Plant).where(Plant.plant_code == request.plant_code, Plant.is_deleted == False))
            if not plant:
                plant = db.get(Plant, request.plant_code)

        if not plant:
            # Fallback to the first available operational plant
            plant = db.scalar(select(Plant).where(Plant.is_deleted == False).order_by(Plant.created_at.desc()))

        if not plant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active Production Plant found in the system.",
            )

        # 3. Capture Snapshots
        recipe_snap = cls._capture_recipe_snapshot(db, recipe)
        model_snap = cls._capture_model_snapshot(db)
        target_strength_snap = cls._capture_target_strength_snapshot(db, recipe, str(plant.id))
        constraints_snap = cls._capture_constraints_snapshot(db, recipe)

        # 4. Create Persistent Run Record
        now = datetime.now(timezone.utc)
        run = OptimizationRun(
            recipe_id=str(recipe.id),
            recipe_code=recipe.recipe_code,
            plant_code=plant.plant_code,
            optimization_objective=request.optimization_objective.upper(),
            run_status="CREATED",
            recipe_snapshot_json=recipe_snap.model_dump(),
            model_snapshot_json=model_snap.model_dump(),
            target_strength_snapshot_json=target_strength_snap.model_dump(),
            constraints_snapshot_json=constraints_snap.model_dump(),
            pricing_snapshot_json=None,
            candidates_count=0,
            stage_message="Optimization Run Context Snapshotted — Ready for Phase 5B Candidate Solver",
            triggered_by_user_id=current_user.id if current_user else None,
            created_at=now,
            updated_at=now,
        )

        db.add(run)

        # 5. Record Governance Audit Event
        audit_entry = SecurityAuditLog(
            actor_user_id=current_user.id if current_user else None,
            target_user_id=None,
            event_type="OPTIMIZATION_RUN_TRIGGERED",
            resource_name="AI_MIX_OPTIMIZATION",
            correlation_id=correlation_id,
            details={
                "run_id": str(run.id),
                "recipe_id": str(recipe.id),
                "recipe_code": recipe.recipe_code,
                "plant_code": plant.plant_code,
                "optimization_objective": run.optimization_objective,
                "model_version": model_snap.model_version,
                "target_mean_strength_mpa": target_strength_snap.target_mean_strength_fck_prime_mpa,
            },
            ip_address=client_ip,
            user_agent=user_agent or "MixOptimizationService/1.0",
            created_at=now,
        )
        db.add(audit_entry)

        try:
            db.commit()
            db.refresh(run)
        except Exception as ex:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist optimization run context: {str(ex)}",
            )

        return OptimizationRunResponseDTO(
            run_id=str(run.id),
            recipe_id=str(run.recipe_id),
            recipe_code=run.recipe_code,
            plant_code=run.plant_code,
            optimization_objective=run.optimization_objective,
            run_status=run.run_status,
            stage_message=run.stage_message or "Optimization Run Created",
            recipe_snapshot=recipe_snap,
            model_snapshot=model_snap,
            target_strength_snapshot=target_strength_snap,
            constraints_snapshot=constraints_snap,
            pricing_snapshot=run.pricing_snapshot_json,
            candidates_count=run.candidates_count,
            created_at=run.created_at.isoformat(),
            triggered_by_user_id=str(run.triggered_by_user_id) if run.triggered_by_user_id else None,
        )

    @classmethod
    def get_latest_optimization_run(
        cls,
        db: Session,
        recipe_code: Optional[str] = None,
        plant_code: Optional[str] = None,
    ) -> Optional[OptimizationRunResponseDTO]:
        """Retrieve the most recent persisted optimization run without re-running calculations."""
        q = db.query(OptimizationRun).filter(OptimizationRun.is_deleted == False)
        if recipe_code:
            q = q.filter(OptimizationRun.recipe_code == recipe_code)
        if plant_code:
            q = q.filter(OptimizationRun.plant_code == plant_code)

        run = q.order_by(desc(OptimizationRun.created_at)).first()
        if not run:
            return None

        return OptimizationRunResponseDTO(
            run_id=str(run.id),
            recipe_id=str(run.recipe_id),
            recipe_code=run.recipe_code,
            plant_code=run.plant_code,
            optimization_objective=run.optimization_objective,
            run_status=run.run_status,
            stage_message=run.stage_message or "Optimization Run Created",
            recipe_snapshot=RecipeSnapshotDTO(**run.recipe_snapshot_json),
            model_snapshot=ModelSnapshotDTO(**run.model_snapshot_json),
            target_strength_snapshot=TargetStrengthSnapshotDTO(**run.target_strength_snapshot_json),
            constraints_snapshot=ConstraintsSnapshotDTO(**run.constraints_snapshot_json),
            pricing_snapshot=run.pricing_snapshot_json,
            candidates_count=run.candidates_count,
            created_at=run.created_at.isoformat() if hasattr(run.created_at, "isoformat") else str(run.created_at),
            triggered_by_user_id=str(run.triggered_by_user_id) if run.triggered_by_user_id else None,
        )
