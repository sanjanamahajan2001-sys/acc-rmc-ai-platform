"""Enterprise AI Mix Optimization Candidate Solver Service.

This service implements bounded candidate generation, physical volume / yield validation,
IS 456 Table 5 / IS 10262 engineering constraint checking, active ML model inference,
target strength gating, multi-objective evaluation, and formal Pareto non-dominance classification.
"""

from datetime import datetime, timezone
from decimal import Decimal
import math
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.contracts.optimization.models import (
    BaselineRecipeCoordinatesDTO,
    CandidateConstituentDTO,
    CandidateEvaluationResponseDTO,
    ConstraintDiagnosticItemDTO,
    OptimizationCandidateDTO,
    PhysicalVolumeDiagnosticDTO,
    RecipeConstituentSnapshotDTO,
    RecipeSnapshotDTO,
    TargetStrengthSnapshotDTO,
)
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import SecurityAuditLog, User
from src.ml.inference.inference_service import MLInferenceService, PredictionRequestDTO
from src.services.engineering_settings_service import EngineeringSettingsService


class CandidateSolverService:
    """Service handling bounded candidate generation, physical validation, and Pareto analysis."""

    # Authoritative Standard Specific Gravities (g/cm3 or ton/m3) - Hardcoded fallback constants
    DEFAULT_SPECIFIC_GRAVITIES = {
        "CEMENT": 3.15,
        "OPC": 3.15,
        "PPC": 3.00,
        "FLYASH": 2.20,
        "FLY_ASH": 2.20,
        "GGBS": 2.90,
        "SLAG": 2.90,
        "MICRO_SILICA": 2.20,
        "SILICA_FUME": 2.20,
        "WATER": 1.00,
        "COARSE_AGGREGATE": 2.68,
        "CA": 2.68,
        "FINE_AGGREGATE": 2.65,
        "FA": 2.65,
        "SAND": 2.65,
        "ADMIXTURE": 1.15,
        "SUPERPLASTICIZER": 1.15,
    }

    @classmethod
    def _resolve_sg(
        cls,
        category_code: Optional[str],
        material_code: str,
        default_density: Optional[float] = None,
        eng_sg_config: Optional[Dict[str, float]] = None,
    ) -> float:
        """Resolve specific gravity using 3-tier precedence:
        1. Material Master brand-level override (if default_density is explicitly provided and non-zero)
        2. Active Admin Engineering Settings baseline (specific_gravities_json)
        3. Standard engineering fallback constants (DEFAULT_SPECIFIC_GRAVITIES)
        """
        # 1. Tier 1: Material Master Override
        if default_density and default_density > 0:
            if default_density > 100:
                return round(default_density / 1000.0, 3)
            return round(default_density, 3)

        code_upper = (material_code or "").upper()
        cat_upper = (category_code or "").upper()

        # 2. Tier 2: Active Admin Engineering Settings
        if eng_sg_config and isinstance(eng_sg_config, dict):
            # Check direct exact keys first
            for key, sg_val in eng_sg_config.items():
                if sg_val and float(sg_val) > 0:
                    k_upper = key.upper()
                    if k_upper == cat_upper or k_upper == code_upper:
                        return round(float(sg_val), 3)
            # Check substring matches in eng_sg_config
            for key, sg_val in eng_sg_config.items():
                if sg_val and float(sg_val) > 0:
                    k_upper = key.upper()
                    if k_upper in cat_upper or k_upper in code_upper or (cat_upper and cat_upper in k_upper):
                        return round(float(sg_val), 3)

        # 3. Tier 3: Standard Hardcoded Fallback Constants
        for key, sg in cls.DEFAULT_SPECIFIC_GRAVITIES.items():
            if key in cat_upper or key in code_upper:
                return sg

        # Category general fallbacks
        if "CEMENT" in cat_upper or "BINDER" in cat_upper:
            return 3.15
        if "FLYASH" in cat_upper or "FLY_ASH" in cat_upper:
            return 2.20
        if "GGBS" in cat_upper or "SLAG" in cat_upper:
            return 2.90
        if "SILICA" in cat_upper or "FUME" in cat_upper:
            return 2.20
        if "AGG" in cat_upper:
            return 2.67
        if "WATER" in cat_upper:
            return 1.00
        if "ADMIX" in cat_upper or "CHEM" in cat_upper:
            return 1.15

        return 2.65

    @classmethod
    def _categorize_constituents(cls, constituents: List[RecipeConstituentSnapshotDTO]) -> Dict[str, Any]:
        """Classify master recipe constituents into binder, water, aggregates, and admixture roles."""
        categorized = {
            "cement": None,
            "fly_ash": None,
            "ggbs": None,
            "micro_silica": None,
            "water": None,
            "coarse_agg": None,
            "fine_agg": None,
            "admixture": None,
            "other": [],
        }

        for c in constituents:
            cat = (c.category_code or "").upper()
            code = (c.material_code or "").upper()
            name = (c.material_name or "").upper()

            if "CEMENT" in cat or "OPC" in code or "CEMENT" in name:
                if not categorized["cement"]:
                    categorized["cement"] = c
                else:
                    categorized["other"].append(c)
            elif "FLYASH" in cat or "FLY_ASH" in cat or "FLYASH" in code or "FLY ASH" in name:
                categorized["fly_ash"] = c
            elif "GGBS" in cat or "SLAG" in cat or "GGBS" in code or "SLAG" in name:
                categorized["ggbs"] = c
            elif "SILICA" in cat or "FUME" in cat or "SILICA" in code or "FUME" in name:
                categorized["micro_silica"] = c
            elif "WATER" in cat or "WATER" in code or "WATER" in name:
                categorized["water"] = c
            elif "COARSE" in cat or "CA" in code or "20MM" in code or "10MM" in code or "COARSE" in name:
                categorized["coarse_agg"] = c
            elif "FINE" in cat or "FA" in code or "SAND" in code or "FINE" in name:
                categorized["fine_agg"] = c
            elif "ADMIX" in cat or "CHEM" in cat or "ADMIXTURE" in code or "PLASTICIZER" in name:
                categorized["admixture"] = c
            else:
                categorized["other"].append(c)

        return categorized

    @classmethod
    def generate_bounded_candidate_proportions(
        cls,
        recipe_snap: RecipeSnapshotDTO,
        constraints_snap: Dict[str, Any],
        target_strength_snap: TargetStrengthSnapshotDTO,
    ) -> List[Dict[str, Any]]:
        """Generate a deterministic, bounded matrix of candidate mix proportions based on master recipe."""
        if isinstance(recipe_snap, dict):
            recipe_snap = RecipeSnapshotDTO.model_validate(recipe_snap)
        if isinstance(target_strength_snap, dict):
            target_strength_snap = TargetStrengthSnapshotDTO.model_validate(target_strength_snap)
        constituents = recipe_snap.constituents
        cat_map = cls._categorize_constituents(constituents)

        # Raw baseline quantities
        c_raw = cat_map["cement"].target_quantity_kg_m3 if cat_map["cement"] else 350.0
        fa_raw = cat_map["fly_ash"].target_quantity_kg_m3 if cat_map["fly_ash"] else 0.0
        ggbs_raw = cat_map["ggbs"].target_quantity_kg_m3 if cat_map["ggbs"] else 0.0
        ms_raw = cat_map["micro_silica"].target_quantity_kg_m3 if cat_map["micro_silica"] else 0.0
        w_raw = cat_map["water"].target_quantity_kg_m3 if cat_map["water"] else 175.0
        ca_raw = cat_map["coarse_agg"].target_quantity_kg_m3 if cat_map["coarse_agg"] else 1100.0
        fa_agg_raw = cat_map["fine_agg"].target_quantity_kg_m3 if cat_map["fine_agg"] else 750.0
        admix_raw = cat_map["admixture"].target_quantity_kg_m3 if cat_map["admixture"] else 3.5

        # Extract active engineering settings specific gravities & air volume fraction
        eng_settings = getattr(cls, "_active_eng_settings", None) or {}
        eng_sg_config = eng_settings.get("specific_gravities_json", {})
        air_volume_m3 = float(eng_settings.get("air_volume_fraction", 0.010))

        # Specific Gravities using 3-tier precedence
        sg_c = cls._resolve_sg(
            cat_map["cement"].category_code if cat_map["cement"] else None,
            cat_map["cement"].material_code if cat_map["cement"] else "CEMENT",
            getattr(cat_map["cement"], "specific_gravity", None) if cat_map["cement"] else None,
            eng_sg_config,
        )
        sg_fa = cls._resolve_sg(
            cat_map["fly_ash"].category_code if cat_map["fly_ash"] else None,
            cat_map["fly_ash"].material_code if cat_map["fly_ash"] else "FLYASH",
            getattr(cat_map["fly_ash"], "specific_gravity", None) if cat_map["fly_ash"] else None,
            eng_sg_config,
        )
        sg_ggbs = cls._resolve_sg(
            cat_map["ggbs"].category_code if cat_map["ggbs"] else None,
            cat_map["ggbs"].material_code if cat_map["ggbs"] else "GGBS",
            getattr(cat_map["ggbs"], "specific_gravity", None) if cat_map["ggbs"] else None,
            eng_sg_config,
        )
        sg_ms = cls._resolve_sg(
            cat_map["micro_silica"].category_code if cat_map["micro_silica"] else None,
            cat_map["micro_silica"].material_code if cat_map["micro_silica"] else "MICRO_SILICA",
            getattr(cat_map["micro_silica"], "specific_gravity", None) if cat_map["micro_silica"] else None,
            eng_sg_config,
        )
        sg_w = cls._resolve_sg(
            cat_map["water"].category_code if cat_map["water"] else None,
            cat_map["water"].material_code if cat_map["water"] else "WATER",
            getattr(cat_map["water"], "specific_gravity", None) if cat_map["water"] else None,
            eng_sg_config,
        )
        sg_ca = cls._resolve_sg(
            cat_map["coarse_agg"].category_code if cat_map["coarse_agg"] else None,
            cat_map["coarse_agg"].material_code if cat_map["coarse_agg"] else "COARSE_AGGREGATE",
            getattr(cat_map["coarse_agg"], "specific_gravity", None) if cat_map["coarse_agg"] else None,
            eng_sg_config,
        )
        sg_fa_agg = cls._resolve_sg(
            cat_map["fine_agg"].category_code if cat_map["fine_agg"] else None,
            cat_map["fine_agg"].material_code if cat_map["fine_agg"] else "FINE_AGGREGATE",
            getattr(cat_map["fine_agg"], "specific_gravity", None) if cat_map["fine_agg"] else None,
            eng_sg_config,
        )
        sg_admix = cls._resolve_sg(
            cat_map["admixture"].category_code if cat_map["admixture"] else None,
            cat_map["admixture"].material_code if cat_map["admixture"] else "ADMIXTURE",
            getattr(cat_map["admixture"], "specific_gravity", None) if cat_map["admixture"] else None,
            eng_sg_config,
        )

        # Calculate initial baseline volume to normalize multi-m3 batch entries down to standard 1 m3 basis
        raw_vol = (
            c_raw / (sg_c * 1000.0)
            + fa_raw / (sg_fa * 1000.0)
            + ggbs_raw / (sg_ggbs * 1000.0)
            + ms_raw / (sg_ms * 1000.0)
            + w_raw / (sg_w * 1000.0)
            + ca_raw / (sg_ca * 1000.0)
            + fa_agg_raw / (sg_fa_agg * 1000.0)
            + admix_raw / (sg_admix * 1000.0)
            + air_volume_m3
        )
        norm_factor = (1.0 / raw_vol) if (raw_vol > 1.25 or raw_vol < 0.75) else 1.0

        c_base = c_raw * norm_factor
        fa_base = fa_raw * norm_factor
        ggbs_base = ggbs_raw * norm_factor
        ms_base = ms_raw * norm_factor
        w_base = w_raw * norm_factor
        ca_base = ca_raw * norm_factor
        fa_agg_base = fa_agg_raw * norm_factor
        admix_base = admix_raw * norm_factor

        b_base = c_base + fa_base + ggbs_base + ms_base

        # Extract limits from constraints snapshot
        min_binder_req = 300.0
        max_fa_limit = 35.0
        max_ggbs_limit = 50.0
        max_ms_limit = 10.0

        if constraints_snap and isinstance(constraints_snap, dict):
            for it in constraints_snap.get("items", []):
                name = it.get("constraint_name", "")
                if ("Binder" in name or "Cementitious" in name) and "Water" not in name:
                    min_binder_req = float(it.get("limit_value", 300.0))
                elif "Fly Ash" in name:
                    max_fa_limit = float(it.get("limit_value", 35.0))
                elif "GGBS" in name:
                    max_ggbs_limit = float(it.get("limit_value", 50.0))
                elif "Micro-Silica" in name or "Silica Fume" in name:
                    max_ms_limit = float(it.get("limit_value", 10.0))

        # Dynamic SCM options scaled proportionally to active snapshot limits
        fa_max_frac = max_fa_limit / 100.0
        ggbs_max_frac = max_ggbs_limit / 100.0
        ms_max_frac = max_ms_limit / 100.0

        scm_options = [
            ("BASE", fa_base / b_base if b_base > 0 else 0.0, ggbs_base / b_base if b_base > 0 else 0.0, ms_base / b_base if b_base > 0 else 0.0),
            ("MOD_FA", min(fa_max_frac * 0.70, 0.25), 0.0, 0.0),
            ("HIGH_FA", min(fa_max_frac * 0.95, fa_max_frac), 0.0, 0.0),
            ("MAX_FA", fa_max_frac, 0.0, 0.0),
            ("MOD_GGBS", 0.0, min(ggbs_max_frac * 0.70, 0.35), 0.0),
            ("HIGH_GGBS", 0.0, min(ggbs_max_frac * 0.95, ggbs_max_frac), 0.0),
            ("MAX_GGBS", 0.0, ggbs_max_frac, 0.0),
            ("TERNARY", min(fa_max_frac * 0.50, 0.15), min(ggbs_max_frac * 0.50, 0.20), 0.0),
            ("MOD_MS", 0.0, 0.0, min(ms_max_frac * 0.70, 0.05)),
            ("HIGH_MS", 0.0, 0.0, min(ms_max_frac * 0.95, ms_max_frac)),
            ("MAX_MS", 0.0, 0.0, ms_max_frac),
        ]

        # Systematic matrix of candidate binder targets, SCM strategies, and W/B ratios
        binder_targets = [
            (min_binder_req - 20.0, "BASE", 0.52, 0.90),
            (min_binder_req - 10.0, "MOD_FA", 0.50, 0.95),
            (min_binder_req - 5.0, "BASE", 0.48, 0.95),
            (min_binder_req, "BASE", 0.48, 1.00),
            (min_binder_req + 5.0, "MOD_FA", 0.45, 1.00),
            (min_binder_req + 10.0, "MOD_GGBS", 0.42, 1.00),
            (min_binder_req + 15.0, "BASE", 0.43, 1.00),
            (min_binder_req + 20.0, "MOD_FA", 0.40, 1.05),
            (min_binder_req + 25.0, "HIGH_FA", 0.40, 1.10),
            (min_binder_req + 30.0, "MOD_GGBS", 0.41, 1.00),
            (min_binder_req + 35.0, "BASE", 0.42, 1.00),
            (min_binder_req + 40.0, "MOD_FA", 0.39, 1.05),
            (min_binder_req + 45.0, "TERNARY", 0.39, 1.10),
            (min_binder_req + 50.0, "HIGH_GGBS", 0.40, 1.05),
            (min_binder_req + 55.0, "BASE", 0.40, 1.00),
            (min_binder_req + 60.0, "MOD_FA", 0.38, 1.05),
            (min_binder_req + 65.0, "MOD_GGBS", 0.39, 1.05),
            (min_binder_req + 70.0, "HIGH_FA", 0.38, 1.10),
            (min_binder_req + 75.0, "MAX_FA", 0.38, 1.10),
            (min_binder_req + 80.0, "BASE", 0.38, 1.00),
            (min_binder_req + 85.0, "MAX_GGBS", 0.37, 1.10),
            (min_binder_req + 90.0, "MOD_GGBS", 0.37, 1.10),
            (min_binder_req + 95.0, "MOD_MS", 0.36, 1.05),
            (min_binder_req + 100.0, "HIGH_MS", 0.36, 1.10),
            (min_binder_req + 105.0, "MAX_MS", 0.35, 1.10),
        ]

        # Aggregate volume ratio
        vol_ca_base = ca_base / (sg_ca * 1000.0)
        vol_fa_base = fa_agg_base / (sg_fa_agg * 1000.0)
        total_agg_vol_base = vol_ca_base + vol_fa_base
        r_ca = vol_ca_base / total_agg_vol_base if total_agg_vol_base > 0 else 0.60

        candidates_data: List[Dict[str, Any]] = []
        cand_idx = 1

        for target_b, scm_tag, wb_ratio, adm_factor in binder_targets:
            total_b = round(target_b, 1)

            # Resolve SCM proportions
            fa_pct = 0.0
            ggbs_pct = 0.0
            ms_pct = 0.0
            for tag, f_r, g_r, m_r in scm_options:
                if tag == scm_tag:
                    fa_pct = f_r
                    ggbs_pct = g_r
                    ms_pct = m_r
                    break

            fa_kg = round(total_b * fa_pct, 1)
            ggbs_kg = round(total_b * ggbs_pct, 1)
            ms_kg = round(total_b * ms_pct, 1)
            c_kg = round(total_b - fa_kg - ggbs_kg - ms_kg, 1)

            wb = round(wb_ratio, 3)
            w_kg = round(total_b * wb, 1)
            adm_kg = round(max(2.0, admix_base * adm_factor), 2)

            # Absolute volume of paste + air
            vol_c = c_kg / (sg_c * 1000.0)
            vol_fa = fa_kg / (sg_fa * 1000.0)
            vol_ggbs = ggbs_kg / (sg_ggbs * 1000.0)
            vol_ms = ms_kg / (sg_ms * 1000.0)
            vol_w = w_kg / (sg_w * 1000.0)
            vol_adm = adm_kg / (sg_admix * 1000.0)

            vol_paste_and_air = vol_c + vol_fa + vol_ggbs + vol_ms + vol_w + vol_adm + air_volume_m3
            vol_agg_needed = max(0.0, 1.000 - vol_paste_and_air)

            vol_ca = vol_agg_needed * r_ca
            vol_fa_agg = vol_agg_needed * (1.0 - r_ca)

            ca_kg = round(vol_ca * sg_ca * 1000.0, 1)
            fa_agg_kg = round(vol_fa_agg * sg_fa_agg * 1000.0, 1)

            # Constituents list for this candidate
            cand_constituents = [
                {
                    "material_code": cat_map["cement"].material_code if cat_map["cement"] else "CEM-OPC",
                    "material_name": cat_map["cement"].material_name if cat_map["cement"] else "OPC 53 Grade Cement",
                    "category_code": "CEMENT",
                    "quantity_kg_m3": c_kg,
                    "specific_gravity": sg_c,
                    "absolute_volume_m3": round(vol_c, 4),
                }
            ]
            if fa_kg > 0:
                cand_constituents.append({
                    "material_code": cat_map["fly_ash"].material_code if cat_map["fly_ash"] else "MAT-FA",
                    "material_name": cat_map["fly_ash"].material_name if cat_map["fly_ash"] else "Fly Ash Class F",
                    "category_code": "FLY_ASH",
                    "quantity_kg_m3": fa_kg,
                    "specific_gravity": sg_fa,
                    "absolute_volume_m3": round(vol_fa, 4),
                })
            if ggbs_kg > 0:
                cand_constituents.append({
                    "material_code": cat_map["ggbs"].material_code if cat_map["ggbs"] else "MAT-GGBS",
                    "material_name": cat_map["ggbs"].material_name if cat_map["ggbs"] else "GGBS Ground Granulated Slag",
                    "category_code": "GGBS",
                    "quantity_kg_m3": ggbs_kg,
                    "specific_gravity": sg_ggbs,
                    "absolute_volume_m3": round(vol_ggbs, 4),
                })
            if ms_kg > 0:
                cand_constituents.append({
                    "material_code": cat_map["micro_silica"].material_code if cat_map["micro_silica"] else "MAT-MS",
                    "material_name": cat_map["micro_silica"].material_name if cat_map["micro_silica"] else "Micro-Silica / Silica Fume",
                    "category_code": "MICRO_SILICA",
                    "quantity_kg_m3": ms_kg,
                    "specific_gravity": sg_ms,
                    "absolute_volume_m3": round(vol_ms, 4),
                })
            cand_constituents.extend([
                {
                    "material_code": cat_map["water"].material_code if cat_map["water"] else "MAT-WTR",
                    "material_name": cat_map["water"].material_name if cat_map["water"] else "Batching Water",
                    "category_code": "WATER",
                    "quantity_kg_m3": w_kg,
                    "specific_gravity": sg_w,
                    "absolute_volume_m3": round(vol_w, 4),
                },
                {
                    "material_code": cat_map["coarse_agg"].material_code if cat_map["coarse_agg"] else "MAT-CA-20",
                    "material_name": cat_map["coarse_agg"].material_name if cat_map["coarse_agg"] else "Coarse Aggregate 20mm",
                    "category_code": "COARSE_AGGREGATE",
                    "quantity_kg_m3": ca_kg,
                    "specific_gravity": sg_ca,
                    "absolute_volume_m3": round(vol_ca, 4),
                },
                {
                    "material_code": cat_map["fine_agg"].material_code if cat_map["fine_agg"] else "MAT-FA-SAND",
                    "material_name": cat_map["fine_agg"].material_name if cat_map["fine_agg"] else "Fine Aggregate (River Sand)",
                    "category_code": "FINE_AGGREGATE",
                    "quantity_kg_m3": fa_agg_kg,
                    "specific_gravity": sg_fa_agg,
                    "absolute_volume_m3": round(vol_fa_agg, 4),
                },
                {
                    "material_code": cat_map["admixture"].material_code if cat_map["admixture"] else "MAT-ADM-PCE",
                    "material_name": cat_map["admixture"].material_name if cat_map["admixture"] else "PCE High-Range Superplasticizer",
                    "category_code": "ADMIXTURE",
                    "quantity_kg_m3": adm_kg,
                    "specific_gravity": sg_admix,
                    "absolute_volume_m3": round(vol_adm, 4),
                },
            ])

            candidates_data.append({
                "candidate_identifier": f"CAND-{cand_idx:02d}",
                "cement_kg_m3": c_kg,
                "flyash_kg_m3": fa_kg,
                "ggbs_kg_m3": ggbs_kg,
                "micro_silica_kg_m3": ms_kg,
                "water_kg_m3": w_kg,
                "fine_aggregate_kg_m3": fa_agg_kg,
                "coarse_aggregate_kg_m3": ca_kg,
                "admixture_kg_m3": adm_kg,
                "total_binder_kg_m3": total_b,
                "binder_intensity_kg_m3": total_b,
                "water_binder_ratio": wb,
                "water_cement_ratio": round(w_kg / c_kg, 3) if c_kg > 0 else 0.0,
                "sg_c": sg_c,
                "sg_fa": sg_fa,
                "sg_ggbs": sg_ggbs,
                "sg_ms": sg_ms,
                "sg_w": sg_w,
                "sg_ca": sg_ca,
                "sg_fa_agg": sg_fa_agg,
                "sg_admix": sg_admix,
                "air_volume_m3": air_volume_m3,
                "fck": target_strength_snap.characteristic_strength_fck_mpa,
                "grade": recipe_snap.grade,
                "constituents": cand_constituents,
            })
            cand_idx += 1

        return candidates_data

    @classmethod
    def evaluate_physics_and_constraints(
        cls,
        cand: Dict[str, Any],
        constraints_snap: Dict[str, Any],
    ) -> Tuple[PhysicalVolumeDiagnosticDTO, List[ConstraintDiagnosticItemDTO], bool]:
        """Validate physical absolute volume and IS 456 / IS 10262 engineering constraints."""
        c_kg = cand["cement_kg_m3"]
        fa_kg = cand["flyash_kg_m3"]
        ggbs_kg = cand["ggbs_kg_m3"]
        ms_kg = cand.get("micro_silica_kg_m3", 0.0)
        w_kg = cand["water_kg_m3"]
        ca_kg = cand["coarse_aggregate_kg_m3"]
        fa_agg_kg = cand["fine_aggregate_kg_m3"]
        adm_kg = cand["admixture_kg_m3"]
        total_b = cand["total_binder_kg_m3"]
        wb = cand["water_binder_ratio"]

        # 1. Physical Absolute Volume
        v_c = c_kg / (cand["sg_c"] * 1000.0)
        v_fa = fa_kg / (cand["sg_fa"] * 1000.0)
        v_ggbs = ggbs_kg / (cand["sg_ggbs"] * 1000.0)
        v_ms = ms_kg / (cand.get("sg_ms", 2.20) * 1000.0) if ms_kg > 0 else 0.0
        v_w = w_kg / (cand["sg_w"] * 1000.0)
        v_ca = ca_kg / (cand["sg_ca"] * 1000.0)
        v_fa_agg = fa_agg_kg / (cand["sg_fa_agg"] * 1000.0)
        v_adm = adm_kg / (cand["sg_admix"] * 1000.0)
        v_air = cand["air_volume_m3"]

        actual_vol = round(v_c + v_fa + v_ggbs + v_ms + v_w + v_ca + v_fa_agg + v_adm + v_air, 4)
        vol_deviation = round(abs(actual_vol - 1.000), 4)
        vol_status = "PASSED" if vol_deviation <= 0.010 else "FAILED"

        vol_diag = PhysicalVolumeDiagnosticDTO(
            volume_balance_actual_m3=actual_vol,
            volume_balance_target_m3=1.000,
            volume_balance_deviation_m3=vol_deviation,
            volume_tolerance_limit_m3=0.010,
            air_volume_m3=v_air,
            validation_status=vol_status,
        )

        # 2. Engineering Constraints
        diagnostics: List[ConstraintDiagnosticItemDTO] = []
        is_all_eng_passed = (vol_status == "PASSED")

        items = constraints_snap.get("items", [])
        exposure = constraints_snap.get("exposure_class", "Moderate")

        # Map limits
        min_grade_limit = None
        min_cement_limit = 300.0
        max_wb_limit = 0.50
        max_fa_limit = 35.0
        max_ggbs_limit = 50.0
        max_ms_limit = 10.0

        for it in items:
            name = it.get("constraint_name", "")
            if "Grade" in name:
                min_grade_limit = it.get("limit_value")
            elif ("Binder" in name or "Cementitious" in name or "Cement" in name) and "Water" not in name:
                min_cement_limit = it.get("limit_value", 300.0)
            elif "Water-Binder" in name or "Water-Cement" in name or "Water" in name:
                max_wb_limit = it.get("limit_value", 0.50)
            elif "Fly Ash" in name:
                max_fa_limit = it.get("limit_value", 35.0)
            elif "GGBS" in name:
                max_ggbs_limit = it.get("limit_value", 50.0)
            elif "Micro-Silica" in name or "Silica Fume" in name:
                max_ms_limit = it.get("limit_value", 10.0)

        # Minimum Concrete Grade Check (IS 456:2000 Table 5 RCC Requirement)
        if min_grade_limit is not None and "fck" in cand:
            recipe_fck = float(cand["fck"])
            grade_passed = bool(recipe_fck >= float(min_grade_limit))
            grade_margin = round(recipe_fck - float(min_grade_limit), 1)
            diagnostics.append(
                ConstraintDiagnosticItemDTO(
                    constraint_name="Minimum Concrete Grade (RCC)",
                    standard_reference=f"IS 456:2000 Table 5 ({exposure} Reinforced)",
                    limit_value=float(min_grade_limit),
                    actual_value=recipe_fck,
                    unit="MPa (Grade)",
                    comparison="MINIMUM",
                    status="PASSED" if grade_passed else "FAILED",
                    margin=grade_margin,
                )
            )
            if not grade_passed:
                is_all_eng_passed = False

        # Min Binder Check
        b_margin = round(total_b - min_cement_limit, 2)
        b_passed = (b_margin >= 0)
        diagnostics.append(
            ConstraintDiagnosticItemDTO(
                constraint_name="Minimum Cementitious Content",
                standard_reference=f"IS 456:2000 Table 5 ({exposure} RCC Exposure)",
                limit_value=min_cement_limit,
                actual_value=total_b,
                unit="kg/m³",
                comparison="MINIMUM",
                status="PASSED" if b_passed else "FAILED",
                margin=b_margin,
            )
        )
        if not b_passed:
            is_all_eng_passed = False

        # Max W/B Check - Full-Precision Strict Numeric Validation
        actual_wb = (w_kg / total_b) if total_b > 0 else 0.0
        # Strict inequality with zero artificial slack: 0.5009677 > 0.50 MUST FAIL
        wb_passed = bool(actual_wb <= max_wb_limit)
        wb_margin = round(max_wb_limit - actual_wb, 4)
        diagnostics.append(
            ConstraintDiagnosticItemDTO(
                constraint_name="Maximum Free Water-Binder Ratio",
                standard_reference=f"IS 456:2000 Table 5 ({exposure} RCC Exposure)",
                limit_value=max_wb_limit,
                actual_value=round(actual_wb, 3),
                unit="ratio",
                comparison="MAXIMUM",
                status="PASSED" if wb_passed else "FAILED",
                margin=wb_margin,
            )
        )
        if not wb_passed:
            is_all_eng_passed = False

        # Fly Ash % Check
        actual_fa_pct = round((fa_kg / total_b) * 100.0, 1) if total_b > 0 else 0.0
        fa_margin = round(max_fa_limit - actual_fa_pct, 1)
        fa_passed = (fa_margin >= 0)
        diagnostics.append(
            ConstraintDiagnosticItemDTO(
                constraint_name="Maximum Fly Ash Replacement",
                standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                limit_value=max_fa_limit,
                actual_value=actual_fa_pct,
                unit="%",
                comparison="MAXIMUM",
                status="PASSED" if fa_passed else "FAILED",
                margin=fa_margin,
            )
        )
        if not fa_passed:
            is_all_eng_passed = False

        # GGBS % Check
        actual_ggbs_pct = round((ggbs_kg / total_b) * 100.0, 1) if total_b > 0 else 0.0
        ggbs_margin = round(max_ggbs_limit - actual_ggbs_pct, 1)
        ggbs_passed = (ggbs_margin >= 0)
        diagnostics.append(
            ConstraintDiagnosticItemDTO(
                constraint_name="Maximum GGBS Replacement",
                standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                limit_value=max_ggbs_limit,
                actual_value=actual_ggbs_pct,
                unit="%",
                comparison="MAXIMUM",
                status="PASSED" if ggbs_passed else "FAILED",
                margin=ggbs_margin,
            )
        )
        if not ggbs_passed:
            is_all_eng_passed = False

        # Micro-Silica % Check
        if ms_kg > 0:
            actual_ms_pct = round((ms_kg / total_b) * 100.0, 1) if total_b > 0 else 0.0
            ms_margin = round(max_ms_limit - actual_ms_pct, 1)
            ms_passed = (ms_margin >= 0)
            diagnostics.append(
                ConstraintDiagnosticItemDTO(
                    constraint_name="Maximum Micro-Silica Replacement",
                    standard_reference="Plant Engineering Specification / IS 10262:2019 Cl. 5.2",
                    limit_value=max_ms_limit,
                    actual_value=actual_ms_pct,
                    unit="%",
                    comparison="MAXIMUM",
                    status="PASSED" if ms_passed else "FAILED",
                    margin=ms_margin,
                )
            )
            if not ms_passed:
                is_all_eng_passed = False

        return vol_diag, diagnostics, is_all_eng_passed

    @classmethod
    def evaluate_run_candidates(
        cls,
        db: Session,
        run_id: str,
        current_user: Optional[User] = None,
        correlation_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CandidateEvaluationResponseDTO:
        cls._active_eng_settings = EngineeringSettingsService.get_active_settings(db)
        """Execute candidate generation, ML inference, physical balance, and Pareto classification for a given run."""
        start_eval_time = time.time()
        now = datetime.now(timezone.utc)

        # 1. Fetch OptimizationRun
        run = db.get(OptimizationRun, run_id)
        if not run or run.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationRun with ID '{run_id}' not found.",
            )

        # 2. Idempotency & Status Checks
        if run.run_status == "EVALUATING" or run.run_status == "RUNNING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidate evaluation is already running for this optimization run.",
            )
        if run.run_status in ("SUCCESS", "NO_FEASIBLE_CANDIDATES") and run.candidates_count > 0:
            existing_candidates = db.scalars(
                select(OptimizationCandidate).where(OptimizationCandidate.run_id == run_id)
            ).all()
            if existing_candidates:
                return cls._build_response_from_persisted(run, existing_candidates)

        # Mark Run as EVALUATING
        run.run_status = "EVALUATING"
        run.stage_message = "Generating and evaluating bounded candidate mixes against IS standards & active ML model"
        run.updated_at = now
        db.commit()

        try:
            # 3. Load immutable snapshots
            recipe_snap = RecipeSnapshotDTO(**run.recipe_snapshot_json)
            constraints_snap = run.constraints_snapshot_json
            target_strength_snap = TargetStrengthSnapshotDTO(**run.target_strength_snapshot_json)
            pricing_snap = run.pricing_snapshot_json
            objective = run.optimization_objective

            cost_configured = bool(pricing_snap and isinstance(pricing_snap, dict) and pricing_snap.get("is_configured"))
            objective_configured = True
            if objective == "MINIMIZE_COST" and not cost_configured:
                objective_configured = False
            elif objective == "BALANCED":
                objective_configured = False

            # 4. Generate Bounded Candidate Proportions
            candidates_raw = cls.generate_bounded_candidate_proportions(
                recipe_snap=recipe_snap,
                constraints_snap=constraints_snap,
                target_strength_snap=target_strength_snap,
            )

            # 5. ML Model Inference Batch Evaluation
            evaluated_candidates: List[OptimizationCandidateDTO] = []
            db_candidates_to_persist: List[OptimizationCandidate] = []

            for cand_raw in candidates_raw:
                vol_diag, constr_diags, is_eng_passed = cls.evaluate_physics_and_constraints(
                    cand=cand_raw,
                    constraints_snap=constraints_snap,
                )

                pred_req = PredictionRequestDTO(
                    cement_kg_m3=cand_raw["cement_kg_m3"],
                    flyash_kg_m3=cand_raw["flyash_kg_m3"],
                    ggbs_kg_m3=cand_raw["ggbs_kg_m3"],
                    water_kg_m3=cand_raw["water_kg_m3"],
                    admixture_kg_m3=cand_raw["admixture_kg_m3"],
                    fine_aggregate_kg_m3=cand_raw["fine_aggregate_kg_m3"],
                    coarse_aggregate_kg_m3=cand_raw["coarse_aggregate_kg_m3"],
                    total_binder_kg_m3=cand_raw["total_binder_kg_m3"],
                    water_binder_ratio=cand_raw["water_binder_ratio"],
                    water_cement_ratio=cand_raw["water_cement_ratio"],
                    plant_code=run.plant_code,
                    recipe_code=run.recipe_code,
                )

                pred_result = MLInferenceService.predict_strength(
                    db=db,
                    request=pred_req,
                    actor_user_id=str(current_user.id) if current_user else None,
                    correlation_id=correlation_id,
                )

                pred_str = pred_result.predicted_strength_mpa
                target_fck_prime = target_strength_snap.target_mean_strength_fck_prime_mpa
                fck = target_strength_snap.characteristic_strength_fck_mpa
                strength_margin = round(pred_str - target_fck_prime, 2)
                strength_passed = (strength_margin >= 0.0)

                is_feasible = is_eng_passed and strength_passed

                semantics = (
                    "Analytical Prediction — Limited Validation"
                    if pred_result.prediction_source == "ML_MODEL"
                    else "Physical Heuristic Equation"
                )

                constituents_dto: List[CandidateConstituentDTO] = [
                    CandidateConstituentDTO(**c) for c in cand_raw.get("constituents", [])
                ]

                cand_dto = OptimizationCandidateDTO(
                    id="",
                    candidate_identifier=cand_raw.get("candidate_identifier", cand_raw.get("identifier")),
                    predicted_strength_mpa=pred_str,
                    target_mean_strength_mpa=target_fck_prime,
                    characteristic_strength_fck_mpa=fck,
                    strength_margin_mpa=strength_margin,
                    strength_gate_status="PASSED" if strength_passed else "FAILED",
                    prediction_source=pred_result.prediction_source,
                    prediction_source_semantics=semantics,
                    model_name=pred_result.model_name,
                    model_version=pred_result.model_version,
                    binder_intensity_kg_m3=cand_raw["total_binder_kg_m3"],
                    cost_per_m3=None,
                    water_binder_ratio=cand_raw["water_binder_ratio"],
                    water_cement_ratio=cand_raw["water_cement_ratio"],
                    is_feasible=is_feasible,
                    is_non_dominated=False,
                    is_recommended=None,
                    physical_volume_diagnostic=vol_diag,
                    constraint_diagnostics=constr_diags,
                    constituents=constituents_dto,
                )
                evaluated_candidates.append(cand_dto)

            # 6. Pareto Non-Dominance Classification (Strength vs Binder)
            feasible_candidates = [c for c in evaluated_candidates if c.is_feasible]
            
            for c_a in feasible_candidates:
                dominated = False
                for c_b in feasible_candidates:
                    if c_a.candidate_identifier == c_b.candidate_identifier:
                        continue
                    b_better_or_equal = (
                        c_b.predicted_strength_mpa >= c_a.predicted_strength_mpa
                        and c_b.binder_intensity_kg_m3 <= c_a.binder_intensity_kg_m3
                    )
                    b_strictly_better = (
                        c_b.predicted_strength_mpa > c_a.predicted_strength_mpa
                        or c_b.binder_intensity_kg_m3 < c_a.binder_intensity_kg_m3
                    )
                    if b_better_or_equal and b_strictly_better:
                        dominated = True
                        break
                c_a.is_non_dominated = not dominated

            # 7. Baseline Recipe Coordinates
            base_cat_map = cls._categorize_constituents(recipe_snap.constituents)
            c_base_val = base_cat_map["cement"].target_quantity_kg_m3 if base_cat_map["cement"] else 350.0
            fa_base_val = base_cat_map["fly_ash"].target_quantity_kg_m3 if base_cat_map["fly_ash"] else 0.0
            ggbs_base_val = base_cat_map["ggbs"].target_quantity_kg_m3 if base_cat_map["ggbs"] else 0.0
            w_base_val = base_cat_map["water"].target_quantity_kg_m3 if base_cat_map["water"] else 175.0
            adm_base_val = base_cat_map["admixture"].target_quantity_kg_m3 if base_cat_map["admixture"] else 3.5
            fa_agg_base_val = base_cat_map["fine_agg"].target_quantity_kg_m3 if base_cat_map["fine_agg"] else 750.0
            ca_base_val = base_cat_map["coarse_agg"].target_quantity_kg_m3 if base_cat_map["coarse_agg"] else 1100.0

            # Normalize multi-m3 batch quantities down to 1 m3 basis for feature inference
            raw_b_vol = (
                c_base_val / (3150.0)
                + fa_base_val / (2200.0)
                + ggbs_base_val / (2900.0)
                + w_base_val / (1000.0)
                + ca_base_val / (2680.0)
                + fa_agg_base_val / (2650.0)
                + adm_base_val / (1150.0)
                + 0.010
            )
            base_norm = (1.0 / raw_b_vol) if (raw_b_vol > 1.25 or raw_b_vol < 0.75) else 1.0

            c_pred = round(min(950.0, max(150.0, c_base_val * base_norm)), 1)
            fa_pred = round(min(400.0, max(0.0, fa_base_val * base_norm)), 1)
            ggbs_pred = round(min(400.0, max(0.0, ggbs_base_val * base_norm)), 1)
            w_pred = round(min(450.0, max(100.0, w_base_val * base_norm)), 1)
            adm_pred = round(min(40.0, max(0.0, adm_base_val * base_norm)), 2)
            fa_agg_pred = round(min(1800.0, max(300.0, fa_agg_base_val * base_norm)), 1)
            ca_pred = round(min(1800.0, max(400.0, ca_base_val * base_norm)), 1)

            base_pred_req = PredictionRequestDTO(
                cement_kg_m3=c_pred,
                flyash_kg_m3=fa_pred,
                ggbs_kg_m3=ggbs_pred,
                water_kg_m3=w_pred,
                admixture_kg_m3=adm_pred,
                fine_aggregate_kg_m3=fa_agg_pred,
                coarse_aggregate_kg_m3=ca_pred,
                plant_code=run.plant_code,
                recipe_code=run.recipe_code,
            )
            base_pred_res = MLInferenceService.predict_strength(db=db, request=base_pred_req)
            total_b_base = c_pred + fa_pred + ggbs_pred

            baseline_coords = BaselineRecipeCoordinatesDTO(
                recipe_code=recipe_snap.recipe_code,
                grade=recipe_snap.grade,
                characteristic_strength_fck_mpa=target_strength_snap.characteristic_strength_fck_mpa,
                target_mean_strength_fck_prime_mpa=target_strength_snap.target_mean_strength_fck_prime_mpa,
                predicted_strength_mpa=base_pred_res.predicted_strength_mpa,
                binder_intensity_kg_m3=round(total_b_base, 1),
                cost_per_m3=None,
                water_binder_ratio=round(w_pred / total_b_base, 3) if total_b_base > 0 else 0.50,
            )

            # 8. Persist All Evaluated Candidates to DB
            for cand in evaluated_candidates:
                orm_cand = OptimizationCandidate(
                    run_id=run.id,
                    candidate_identifier=cand.candidate_identifier,
                    is_recommended=False,
                    is_feasible=cand.is_feasible,
                    predicted_strength_mpa=Decimal(str(cand.predicted_strength_mpa)),
                    prediction_source=cand.prediction_source,
                    cost_per_m3=Decimal(str(cand.cost_per_m3)) if cand.cost_per_m3 is not None else None,
                    binder_intensity=Decimal(str(cand.binder_intensity_kg_m3)),
                    constituent_payload_json={
                        "constituents": [c.model_dump() for c in cand.constituents],
                        "water_binder_ratio": cand.water_binder_ratio,
                        "water_cement_ratio": cand.water_cement_ratio,
                    },
                    constraint_evaluation_json={
                        "physical_volume_diagnostic": cand.physical_volume_diagnostic.model_dump(),
                        "constraint_diagnostics": [c.model_dump() for c in cand.constraint_diagnostics],
                        "is_non_dominated": cand.is_non_dominated,
                        "strength_margin_mpa": cand.strength_margin_mpa,
                        "strength_gate_status": cand.strength_gate_status,
                        "target_mean_strength_mpa": cand.target_mean_strength_mpa,
                        "characteristic_strength_fck_mpa": cand.characteristic_strength_fck_mpa,
                    },
                    created_at=now,
                    updated_at=now,
                )
                db.add(orm_cand)
                db_candidates_to_persist.append(orm_cand)

            feasible_count = len(feasible_candidates)
            pareto_count = len([c for c in feasible_candidates if c.is_non_dominated])

            if feasible_count == 0:
                run.run_status = "NO_FEASIBLE_CANDIDATES"
                run.stage_message = "Candidate Solver Completed — No Feasible Candidates Met All Engineering & Target Strength Constraints"
            else:
                run.run_status = "SUCCESS"
                run.stage_message = f"Candidate Solver Completed — {feasible_count} Feasible, {pareto_count} Pareto-Optimal Candidates Identified"

            run.candidates_count = len(evaluated_candidates)
            run.updated_at = now

            audit_entry = SecurityAuditLog(
                actor_user_id=current_user.id if current_user else None,
                target_user_id=None,
                event_type="OPTIMIZATION_CANDIDATES_EVALUATED",
                resource_name="AI_MIX_OPTIMIZATION",
                correlation_id=correlation_id,
                details={
                    "run_id": str(run.id),
                    "recipe_code": run.recipe_code,
                    "plant_code": run.plant_code,
                    "total_candidates": len(evaluated_candidates),
                    "feasible_candidates": feasible_count,
                    "pareto_candidates": pareto_count,
                    "run_status": run.run_status,
                },
                ip_address=client_ip,
                user_agent=user_agent or "CandidateSolverService/1.0",
                created_at=now,
            )
            db.add(audit_entry)

            db.commit()
            db.refresh(run)

            for dto, orm in zip(evaluated_candidates, db_candidates_to_persist):
                dto.id = str(orm.id)

            duration_ms = round((time.time() - start_eval_time) * 1000, 2)

            return CandidateEvaluationResponseDTO(
                run_id=str(run.id),
                recipe_code=run.recipe_code,
                plant_code=run.plant_code,
                optimization_objective=run.optimization_objective,
                run_status=run.run_status,
                stage_message=run.stage_message or "Candidate Evaluation Complete",
                total_candidates=len(evaluated_candidates),
                feasible_candidates_count=feasible_count,
                pareto_candidates_count=pareto_count,
                cost_configured=cost_configured,
                objective_configured=objective_configured,
                baseline_coordinates=baseline_coords,
                candidates=evaluated_candidates,
                evaluation_duration_ms=duration_ms,
                evaluated_at=now.isoformat(),
            )

        except Exception as ex:
            db.rollback()
            try:
                run.run_status = "FAILED"
                run.stage_message = f"Candidate Solver Evaluation Failed: {str(ex)}"
                run.updated_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Candidate solver evaluation failed: {str(ex)}",
            )

    @classmethod
    def _build_response_from_persisted(
        cls, run: OptimizationRun, candidates: List[OptimizationCandidate]
    ) -> CandidateEvaluationResponseDTO:
        """Construct response DTO from previously persisted database rows to ensure idempotency."""
        recipe_snap = RecipeSnapshotDTO(**run.recipe_snapshot_json)
        target_snap = TargetStrengthSnapshotDTO(**run.target_strength_snapshot_json)
        pricing_snap = run.pricing_snapshot_json
        cost_configured = bool(pricing_snap and isinstance(pricing_snap, dict) and pricing_snap.get("is_configured"))
        objective_configured = (run.optimization_objective != "BALANCED") and (
            run.optimization_objective != "MINIMIZE_COST" or cost_configured
        )

        dtos: List[OptimizationCandidateDTO] = []
        for c in candidates:
            payload = c.constituent_payload_json or {}
            eval_json = c.constraint_evaluation_json or {}
            vol_json = eval_json.get("physical_volume_diagnostic", {})
            constr_list = eval_json.get("constraint_diagnostics", [])

            vol_diag = PhysicalVolumeDiagnosticDTO(
                volume_balance_actual_m3=vol_json.get("volume_balance_actual_m3", 1.0),
                volume_balance_target_m3=vol_json.get("volume_balance_target_m3", 1.0),
                volume_balance_deviation_m3=vol_json.get("volume_balance_deviation_m3", 0.0),
                volume_tolerance_limit_m3=vol_json.get("volume_tolerance_limit_m3", 0.010),
                air_volume_m3=vol_json.get("air_volume_m3", 0.010),
                validation_status=vol_json.get("validation_status", "PASSED"),
            )

            diagnostics = [ConstraintDiagnosticItemDTO(**it) for it in constr_list]
            constituents = [CandidateConstituentDTO(**it) for it in payload.get("constituents", [])]

            pred_str = float(c.predicted_strength_mpa) if c.predicted_strength_mpa is not None else 0.0
            target_fck_prime = eval_json.get("target_mean_strength_mpa", target_snap.target_mean_strength_fck_prime_mpa)
            fck = eval_json.get("characteristic_strength_fck_mpa", target_snap.characteristic_strength_fck_mpa)
            strength_margin = eval_json.get("strength_margin_mpa", round(pred_str - target_fck_prime, 2))
            strength_gate_status = eval_json.get("strength_gate_status", "PASSED" if strength_margin >= 0 else "FAILED")

            dtos.append(
                OptimizationCandidateDTO(
                    id=str(c.id),
                    candidate_identifier=c.candidate_identifier,
                    predicted_strength_mpa=pred_str,
                    target_mean_strength_mpa=target_fck_prime,
                    characteristic_strength_fck_mpa=fck,
                    strength_margin_mpa=strength_margin,
                    strength_gate_status=strength_gate_status,
                    prediction_source=c.prediction_source,
                    prediction_source_semantics="Analytical Prediction — Limited Validation" if c.prediction_source == "ML_MODEL" else "Physical Heuristic Equation",
                    model_name="acc_concrete_28d_strength",
                    model_version="1.0.0",
                    binder_intensity_kg_m3=float(c.binder_intensity) if c.binder_intensity is not None else 0.0,
                    cost_per_m3=float(c.cost_per_m3) if c.cost_per_m3 is not None else None,
                    water_binder_ratio=payload.get("water_binder_ratio", 0.50),
                    water_cement_ratio=payload.get("water_cement_ratio", 0.50),
                    is_feasible=c.is_feasible,
                    is_non_dominated=eval_json.get("is_non_dominated", False),
                    is_recommended=None,
                    physical_volume_diagnostic=vol_diag,
                    constraint_diagnostics=diagnostics,
                    constituents=constituents,
                )
            )

        feasible_count = len([d for d in dtos if d.is_feasible])
        pareto_count = len([d for d in dtos if d.is_feasible and d.is_non_dominated])

        base_binder = sum([c.target_quantity_kg_m3 for c in recipe_snap.constituents if "CEMENT" in (c.category_code or "").upper() or "FLYASH" in (c.category_code or "").upper() or "GGBS" in (c.category_code or "").upper()])
        base_water = sum([c.target_quantity_kg_m3 for c in recipe_snap.constituents if "WATER" in (c.category_code or "").upper()])

        baseline_coords = BaselineRecipeCoordinatesDTO(
            recipe_code=recipe_snap.recipe_code,
            grade=recipe_snap.grade,
            characteristic_strength_fck_mpa=target_snap.characteristic_strength_fck_mpa,
            target_mean_strength_fck_prime_mpa=target_snap.target_mean_strength_fck_prime_mpa,
            predicted_strength_mpa=round(recipe_snap.target_strength_mpa, 1),
            binder_intensity_kg_m3=round(base_binder, 1) if base_binder > 0 else 360.0,
            cost_per_m3=None,
            water_binder_ratio=round(base_water / base_binder, 3) if base_binder > 0 else 0.50,
        )

        return CandidateEvaluationResponseDTO(
            run_id=str(run.id),
            recipe_code=run.recipe_code,
            plant_code=run.plant_code,
            optimization_objective=run.optimization_objective,
            run_status=run.run_status,
            stage_message=run.stage_message or "Candidate Evaluation Complete",
            total_candidates=len(dtos),
            feasible_candidates_count=feasible_count,
            pareto_candidates_count=pareto_count,
            cost_configured=cost_configured,
            objective_configured=objective_configured,
            baseline_coordinates=baseline_coords,
            candidates=dtos,
            evaluation_duration_ms=0.0,
            evaluated_at=run.updated_at.isoformat() if hasattr(run.updated_at, "isoformat") else str(run.updated_at),
        )
