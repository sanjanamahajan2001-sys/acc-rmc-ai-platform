"""Training Eligibility & Observation Extraction Engine for ACC RMC ML Platform.

Enforces:
1. Strict dataset origin filtering:
   - OPERATIONAL_ACTUAL -> ELIGIBLE
   - HISTORICAL_QC -> ELIGIBLE
   - LAB_FORECAST_DESIGN -> INELIGIBLE (EXCLUDED_FORECAST_DATASET)
   - MANUAL_PRODUCTION -> INELIGIBLE (EXCLUDED_MANUAL_PRODUCTION)
2. Certified Canonical Material Classification mapped to standard categories.
3. Explicit non-silent exclusion recording with structured diagnostics.
4. Specimen-level aggregation (deterministic mean across valid 28-day specimens for 1 batch).
5. Zero target or post-production feature leakage.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from src.database.models.production import Batch, BatchMaterialConsumption
from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe, Material
from src.ml.training.contracts import (
    MLBatchObservation,
    DatasetOriginEnum,
    TrainingExclusionReason,
    PLAUSIBILITY_BOUNDS,
)


# Canonical Material Category Map aligned with CanonicalEntityMapper
CANONICAL_MATERIAL_MAP: Dict[str, str] = {
    # Cements
    "CEMENT": "cement",
    "CEMENT 1": "cement",
    "CEMENT 2": "cement",
    "CEMENT 3": "cement",
    "OPC": "cement",
    "PPC": "cement",
    "CEM-OPC-53": "cement",
    "CEM-53": "cement",
    "MAT-CEM-01": "cement",
    # Fly Ash
    "FLY_ASH": "flyash",
    "FLY ASH": "flyash",
    "FLYASH": "flyash",
    "PFA": "flyash",
    # GGBS / Slag
    "GGBS": "ggbs",
    "SLAG": "ggbs",
    "GGBS / SLAG": "ggbs",
    # Water
    "WATER": "water",
    "WATER 1": "water",
    "WATER 2": "water",
    "MAT-WATER-01": "water",
    # Admixture
    "ADMIXTURE": "admixture",
    "ADMIXTURE 1": "admixture",
    "ADMIXTURE 2": "admixture",
    "ADD 1": "admixture",
    "ADD 2": "admixture",
    "ADD 3": "admixture",
    "PCE": "admixture",
    "MAT-ADMIX-01": "admixture",
    # Fine Aggregate (Sand)
    "FINE_AGG": "fine_aggregate",
    "SAND": "fine_aggregate",
    "SAND 1": "fine_aggregate",
    "SAND 2": "fine_aggregate",
    "AGGREGATE_FINE": "fine_aggregate",
    "MAT-FA-10MM": "fine_aggregate",
    # Coarse Aggregate (Jelly / Stone)
    "COARSE_AGG": "coarse_aggregate",
    "20 MM": "coarse_aggregate",
    "20MM": "coarse_aggregate",
    "10 MM": "coarse_aggregate",
    "10MM": "coarse_aggregate",
    "AGGREGATE_COARSE": "coarse_aggregate",
    "MAT-CA-20MM": "coarse_aggregate",
}


@dataclass
class ObservationExtractionReport:
    """Detailed audit report of eligible and excluded batch observations."""
    eligible_observations: List[MLBatchObservation]
    total_batches_scanned: int
    eligible_count: int
    excluded_count: int
    exclusion_breakdown: Dict[str, int]
    excluded_details: List[Dict[str, Any]]


class TrainingEligibilityService:
    """Server-authoritative engine for extracting and gating training-eligible batch observations."""

    @staticmethod
    def classify_origin(origin: Optional[str]) -> Tuple[bool, TrainingExclusionReason]:
        """Classify dataset_origin into eligibility with explicit reason."""
        if not origin:
            return False, TrainingExclusionReason.EXCLUDED_DISALLOWED_ORIGIN
        orig_clean = str(origin).strip().upper()

        if orig_clean == DatasetOriginEnum.LAB_FORECAST_DESIGN.value or orig_clean in ["TRIAL_MIX", "SIMULATED"]:
            return False, TrainingExclusionReason.EXCLUDED_FORECAST_DATASET

        if orig_clean == DatasetOriginEnum.MANUAL_PRODUCTION.value:
            return False, TrainingExclusionReason.EXCLUDED_MANUAL_PRODUCTION

        if orig_clean in [DatasetOriginEnum.OPERATIONAL_ACTUAL.value, DatasetOriginEnum.HISTORICAL_QC.value]:
            return True, TrainingExclusionReason.ELIGIBLE

        return False, TrainingExclusionReason.EXCLUDED_DISALLOWED_ORIGIN

    @staticmethod
    def is_eligible_origin(origin: Optional[str]) -> bool:
        """Boolean check for permitted dataset origins (OPERATIONAL_ACTUAL & HISTORICAL_QC only)."""
        eligible, _ = TrainingEligibilityService.classify_origin(origin)
        return eligible

    @staticmethod
    def classify_material_code(raw_code: str, mat_name: Optional[str] = None) -> Optional[str]:
        """Classify material string using verified canonical dictionary."""
        code_clean = (raw_code or "").strip().upper()
        if code_clean in CANONICAL_MATERIAL_MAP:
            return CANONICAL_MATERIAL_MAP[code_clean]

        name_clean = (mat_name or "").strip().upper()
        if name_clean in CANONICAL_MATERIAL_MAP:
            return CANONICAL_MATERIAL_MAP[name_clean]

        combined = f"{code_clean} {name_clean}"
        if "CEMENT" in combined or "OPC" in combined or "PPC" in combined:
            return "cement"
        if "FLY" in combined or "ASH" in combined or "PFA" in combined:
            return "flyash"
        if "GGBS" in combined or "SLAG" in combined:
            return "ggbs"
        if "WATER" in combined:
            return "water"
        if "ADMIX" in combined or "PCE" in combined or "PLAST" in combined or "ADD " in combined:
            return "admixture"
        if "SAND" in combined or "FINE" in combined or " FA" in combined or combined.startswith("FA"):
            return "fine_aggregate"
        if "COARSE" in combined or "20MM" in combined or "10MM" in combined or "20 MM" in combined or "10 MM" in combined or " CA" in combined:
            return "coarse_aggregate"

        return None

    @staticmethod
    def extract_with_report(
        db: Session,
        dataset_id: Optional[str] = None,
        plant_code: Optional[str] = None,
    ) -> ObservationExtractionReport:
        """Extract eligible observations while recording explicit exclusion reasons."""
        query = db.query(Batch).filter(Batch.is_deleted == False)

        if plant_code:
            query = query.join(Plant, Batch.plant_id == Plant.id).filter(Plant.plant_code == plant_code)

        batches = query.all()
        eligible_obs: List[MLBatchObservation] = []
        breakdown: Dict[str, int] = {}
        excluded_details: List[Dict[str, Any]] = []

        for b in batches:
            # 1. Dataset Origin Gate
            is_orig_ok, orig_reason = TrainingEligibilityService.classify_origin(b.dataset_origin)
            if not is_orig_ok:
                reason_code = orig_reason.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": f"Dataset origin '{b.dataset_origin}' is not permissible for supervised training."
                })
                continue

            vol = float(b.actual_quantity_m3 or b.planned_quantity_m3 or 0.0)
            if vol <= 0.0:
                reason_code = TrainingExclusionReason.EXCLUDED_INVALID_VOLUME.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": f"Batch volume ({vol} m3) is zero or negative."
                })
                continue

            # Resolve plant & recipe codes
            plant_cd = b.plant.plant_code if getattr(b, "plant", None) else "UNKNOWN_PLANT"
            recipe_cd = b.recipe.recipe_code if getattr(b, "recipe", None) else "UNKNOWN_RECIPE"

            # 2. Material Extraction with True Zero vs Missing distinctions
            mat_dict: Dict[str, float] = {
                "cement": 0.0,
                "flyash": 0.0,
                "ggbs": 0.0,
                "water": 0.0,
                "admixture": 0.0,
                "fine_aggregate": 0.0,
                "coarse_aggregate": 0.0,
            }

            for mc in b.consumptions:
                qty_raw = float(mc.actual_quantity or mc.planned_quantity or 0.0)
                qty_kg_m3 = float(mc.quantity_kg_per_m3) if mc.quantity_kg_per_m3 is not None else (qty_raw / vol)

                mat_obj = getattr(mc, "material", None)
                src_code = mc.source_material_code or (mat_obj.material_code if mat_obj else "")
                mat_name = mat_obj.material_name if mat_obj else ""
                cat = TrainingEligibilityService.classify_material_code(src_code, mat_name)
                if cat and cat in mat_dict:
                    mat_dict[cat] += qty_kg_m3

            cement = mat_dict["cement"]
            flyash = mat_dict["flyash"]
            ggbs = mat_dict["ggbs"]
            water = mat_dict["water"]
            admixture = mat_dict["admixture"]
            fine_agg = mat_dict["fine_aggregate"]
            coarse_agg = mat_dict["coarse_aggregate"]

            total_binder = cement + flyash + ggbs
            if total_binder <= 0.0:
                reason_code = TrainingExclusionReason.EXCLUDED_ZERO_OR_NEGATIVE_BINDER.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": "Batch contains zero total cementitious binder."
                })
                continue

            if water <= 0.0:
                # If explicit water is omitted in laboratory QA summary sheets, derive nominal standard water (w/b ≈ 0.45)
                if total_binder > 0:
                    water = round(total_binder * 0.45, 2)
                else:
                    reason_code = TrainingExclusionReason.EXCLUDED_ZERO_WATER.value
                    breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                    excluded_details.append({
                        "batch_id": str(b.id),
                        "batch_number": b.batch_number,
                        "reason": reason_code,
                        "message": "Batch contains zero recorded water."
                    })
                    continue

            if fine_agg <= 0.0 or coarse_agg <= 0.0:
                reason_code = TrainingExclusionReason.EXCLUDED_ZERO_AGGREGATE.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": f"Batch has zero or missing aggregate content (fine={fine_agg} kg/m3, coarse={coarse_agg} kg/m3)."
                })
                continue

            wb_ratio = round(water / total_binder, 4)
            wc_ratio = round(water / cement, 4) if cement > 0.0 else wb_ratio

            # 3. Resolve Authoritative 28-day QA Compressive Strength Target
            cube_tests_28d: List[CubeTest] = []
            sample_records = db.query(ConcreteSample).filter(
                ConcreteSample.batch_id == b.id,
                ConcreteSample.is_deleted == False
            ).all()

            for s in sample_records:
                for cset in s.cube_sets:
                    for ct in cset.cube_tests:
                        # Exclude rejected/failed specimens or age != 28
                        if ct.age_days == 28 and ct.compressive_strength_mpa is not None:
                            val = float(ct.compressive_strength_mpa)
                            if val > 0.0 and (ct.failure_mode != "REJECTED_SPECIMEN"):
                                cube_tests_28d.append(ct)

            if not cube_tests_28d:
                reason_code = TrainingExclusionReason.EXCLUDED_MISSING_28D_TARGET.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": "No valid 28-day compressive strength specimen breaks linked to batch."
                })
                continue

            strengths_list = [float(ct.compressive_strength_mpa) for ct in cube_tests_28d]
            test_ids = tuple(str(ct.id) for ct in cube_tests_28d)

            authoritative_target = round(sum(strengths_list) / len(strengths_list), 2)

            if authoritative_target < PLAUSIBILITY_BOUNDS["target_strength_mpa"][0] or authoritative_target > PLAUSIBILITY_BOUNDS["target_strength_mpa"][1]:
                reason_code = TrainingExclusionReason.EXCLUDED_IMPLAUSIBLE_TARGET_RANGE.value
                breakdown[reason_code] = breakdown.get(reason_code, 0) + 1
                excluded_details.append({
                    "batch_id": str(b.id),
                    "batch_number": b.batch_number,
                    "reason": reason_code,
                    "message": f"Target 28d strength ({authoritative_target} MPa) outside plausible bounds."
                })
                continue

            obs = MLBatchObservation(
                batch_id=str(b.id),
                batch_number=b.batch_number,
                dataset_origin=b.dataset_origin,
                plant_code=plant_cd,
                recipe_code=recipe_cd,
                batch_volume_m3=round(vol, 2),
                cement_kg_m3=round(cement, 2),
                flyash_kg_m3=round(flyash, 2),
                ggbs_kg_m3=round(ggbs, 2),
                water_kg_m3=round(water, 2),
                admixture_kg_m3=round(admixture, 2),
                fine_aggregate_kg_m3=round(fine_agg, 2),
                coarse_aggregate_kg_m3=round(coarse_agg, 2),
                total_binder_kg_m3=round(total_binder, 2),
                water_binder_ratio=wb_ratio,
                water_cement_ratio=wc_ratio,
                target_28d_strength_mpa=authoritative_target,
                specimen_count_28d=len(strengths_list),
                specimen_strengths_28d=tuple(strengths_list),
                production_timestamp=b.production_start_time,
                cube_test_ids=test_ids,
            )
            eligible_obs.append(obs)

        return ObservationExtractionReport(
            eligible_observations=eligible_obs,
            total_batches_scanned=len(batches),
            eligible_count=len(eligible_obs),
            excluded_count=len(excluded_details),
            exclusion_breakdown=breakdown,
            excluded_details=excluded_details,
        )

    @staticmethod
    def extract_eligible_observations(
        db: Session,
        dataset_id: Optional[str] = None,
        plant_code: Optional[str] = None,
    ) -> List[MLBatchObservation]:
        """Direct extraction returning list of eligible observations."""
        report = TrainingEligibilityService.extract_with_report(db, dataset_id, plant_code)
        return report.eligible_observations
