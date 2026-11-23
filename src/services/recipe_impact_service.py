"""Enterprise AI Mix Optimization Recipe Impact and Comparison Service (Phase 5C).

Provides traceable, auditable comparison between immutable Phase 5A Master Recipe
Snapshot and persisted Phase 5B Candidate Recipe without modifying frozen Phase 5B logic.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.contracts.optimization.impact_models import (
    CandidateEvaluationSummaryDTO,
    ConstituentImpactItemDTO,
    RecipeImpactResponseDTO,
    RecipeImpactSummaryDTO,
)
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import User


class RecipeImpactService:
    """Computes deterministic engineering deltas and volume balance comparison for recipe candidates."""

    DEFAULT_SPECIFIC_GRAVITIES = {
        "CEMENT": 3.15,
        "OPC": 3.15,
        "PPC": 3.00,
        "FLY_ASH": 2.20,
        "FLYASH": 2.20,
        "GGBS": 2.90,
        "SLAG": 2.90,
        "MICRO_SILICA": 2.20,
        "WATER": 1.00,
        "COARSE_AGGREGATE": 2.68,
        "CA": 2.68,
        "FINE_AGGREGATE": 2.65,
        "FA": 2.65,
        "SAND": 2.65,
        "ADMIXTURE": 1.15,
        "SUPERPLASTICIZER": 1.15,
        "OTHER": 2.65,
    }

    # Authoritative alias mapping between legacy generic labels and canonical engineering codes
    CANONICAL_CODE_ALIASES = {
        "CEMENT": ["CEMENT", "CEM-OPC", "CEM-OPC-53", "CEM-OPC-43", "CEM-PPC", "OPC_53", "OPC_43", "CEMENT_OPC53"],
        "FLY_ASH": ["FLY_ASH", "FLYASH", "MAT-FA", "FA-CLASS-F", "FA_CLASS_F", "POZZOLANA"],
        "GGBS": ["GGBS", "SLAG", "MAT-GGBS", "GGBS-GRADE-1", "GGBS_120", "GGBFS"],
        "WATER": ["WATER", "MAT-WTR", "WATER-TAP", "BATCH_WATER", "MIXING_WATER"],
        "COARSE_AGGREGATE": ["COARSE_AGGREGATE", "AGGREGATE_COARSE", "CA", "MAT-CA", "MAT-CA-20", "CA-20MM", "CA_20MM", "CA-10MM", "CA_10MM"],
        "FINE_AGGREGATE": ["FINE_AGGREGATE", "AGGREGATE_FINE", "FA", "MAT-FA-SAND", "FA-SAND", "RIVER_SAND", "M_SAND"],
        "ADMIXTURE": ["ADMIXTURE", "MAT-ADM", "MAT-ADM-PCE", "ADM-SP", "ADM_PCE", "SUPERPLASTICIZER"],
    }

    @classmethod
    def _infer_canonical_category(
        cls,
        category_code: Optional[str],
        material_code: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> str:
        """Deterministically infer canonical material category from category code, material code, or name."""
        cat_u = (category_code or "").strip().upper()
        code_u = (material_code or "").strip().upper()
        name_u = (material_name or "").strip().upper()

        # 1. Direct category mapping
        if cat_u in ["CEMENT", "OPC", "PPC"]:
            return "CEMENT"
        if cat_u in ["FLY_ASH", "FLYASH", "FA_POZZOLANA"]:
            return "FLY_ASH"
        if cat_u in ["GGBS", "SLAG", "GGBFS"]:
            return "GGBS"
        if cat_u in ["WATER", "MIXING_WATER"]:
            return "WATER"
        if cat_u in ["COARSE_AGGREGATE", "CA", "AGGREGATE_COARSE", "AGG_COARSE"]:
            return "COARSE_AGGREGATE"
        if cat_u in ["FINE_AGGREGATE", "FA", "SAND", "AGGREGATE_FINE", "AGG_FINE"]:
            return "FINE_AGGREGATE"
        if cat_u in ["ADMIXTURE", "SUPERPLASTICIZER", "CHEMICAL_ADMIXTURE", "ADMIX"]:
            return "ADMIXTURE"

        # 2. Inspect code and name against known aliases
        combined = f"{code_u} {name_u}"
        if any(k in combined for k in ["CEMENT", "OPC", "PPC"]):
            return "CEMENT"
        if any(k in combined for k in ["FLY ASH", "FLYASH", "FLY_ASH", "CLASS F", "CLASS C", "POZZOLANA"]):
            return "FLY_ASH"
        if any(k in combined for k in ["GGBS", "SLAG", "GGBFS"]):
            return "GGBS"
        if any(k in combined for k in ["WATER", "TAP WATER", "MIXING WATER"]):
            return "WATER"
        if any(k in combined for k in ["COARSE", "10/20", "20MM", "10MM", "CA_", "CA-", "AGGREGATE_COARSE", "AGG_COARSE"]):
            return "COARSE_AGGREGATE"
        if any(k in combined for k in ["FINE", "SAND", "FA_", "FA-", "RIVER SAND", "M-SAND", "AGGREGATE_FINE", "AGG_FINE"]):
            return "FINE_AGGREGATE"
        if any(k in combined for k in ["ADMIX", "SUPERPLASTICIZER", "PLASTICIZER", "RETARDER", "PCE", "SP-"]):
            return "ADMIXTURE"

        return cat_u if cat_u else "OTHER"

    @classmethod
    def _resolve_sg(
        cls,
        category_code: Optional[str],
        material_code: Optional[str] = None,
        default_density: Optional[float] = None,
    ) -> float:
        """Resolve authoritative Specific Gravity from density or standard engineering tables."""
        if default_density and default_density > 0:
            if default_density > 100:
                return round(default_density / 1000.0, 3)
            return round(default_density, 3)

        cat_canonical = cls._infer_canonical_category(category_code, material_code)
        return cls.DEFAULT_SPECIFIC_GRAVITIES.get(cat_canonical, 2.65)

    @classmethod
    def get_candidate_impact(
        cls,
        db: Session,
        run_id: str,
        candidate_id: str,
        current_user: Optional[User] = None,
    ) -> RecipeImpactResponseDTO:
        """Retrieve authoritative Phase 5A baseline and Phase 5B candidate, validating access and computing deltas."""
        # 1. Authorization check
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required to access recipe impact.",
            )
        if getattr(current_user, "account_status", "ACTIVE") != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is suspended or inactive.",
            )

        # 2. OptimizationRun existence & soft-delete validation
        run = db.get(OptimizationRun, run_id)
        if not run or getattr(run, "is_deleted", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization run '{run_id}' was not found or has been deleted.",
            )

        # 3. OptimizationCandidate existence & cross-run ownership validation
        candidate = db.get(OptimizationCandidate, candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate '{candidate_id}' was not found.",
            )

        if str(candidate.run_id) != str(run.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate '{candidate_id}' does not belong to run '{run_id}'. Cross-run access is rejected.",
            )

        # 4. Authoritative Phase 5A Snapshot Extraction
        recipe_snap = run.recipe_snapshot_json
        if not recipe_snap or not isinstance(recipe_snap, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Corrupt or missing immutable Phase 5A recipe snapshot in optimization run.",
            )

        raw_curr_constituents = recipe_snap.get("constituents", [])
        if not isinstance(raw_curr_constituents, list):
            raw_curr_constituents = []

        # Validate constituent values
        for c in raw_curr_constituents:
            qty = float(c.get("target_quantity_kg_m3", 0.0))
            if math.isnan(qty) or math.isinf(qty) or qty < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid negative or non-finite constituent quantity in baseline: {qty}",
                )

        # 5. Quantity-basis check & 1.0 m3 Normalization
        # Precedence:
        # 1. Explicit authoritative batch_volume_m3 from snapshot
        # 2. Physical constituent volume sum when multi-m3 batch captured
        air_volume_m3 = 0.010  # 1.0% entrapped air per IS 10262 Table 3
        raw_vol_sum = air_volume_m3
        for c in raw_curr_constituents:
            qty = float(c.get("target_quantity_kg_m3", 0.0))
            cat = cls._infer_canonical_category(c.get("category_code"), c.get("material_code"), c.get("material_name"))
            sg = cls._resolve_sg(cat, c.get("material_code"), c.get("default_density_kg_m3"))
            raw_vol_sum += qty / (sg * 1000.0)

        batch_vol = recipe_snap.get("batch_volume_m3") or recipe_snap.get("batch_size_m3")
        if batch_vol and float(batch_vol) > 0 and float(batch_vol) != 1.0:
            norm_factor = 1.0 / float(batch_vol)
        elif raw_vol_sum > 1.25 or (raw_vol_sum < 0.75 and raw_vol_sum > 0.15 and len(raw_curr_constituents) >= 4):
            norm_factor = 1.0 / raw_vol_sum
        else:
            norm_factor = 1.0

        # Build baseline constituent map
        curr_items: List[Dict[str, Any]] = []
        for c in raw_curr_constituents:
            mat_id = str(c.get("material_id")) if c.get("material_id") else None
            code = (c.get("material_code") or "").strip().upper()
            name = c.get("material_name") or code
            cat_canonical = cls._infer_canonical_category(c.get("category_code"), code, name)
            qty = round(float(c.get("target_quantity_kg_m3", 0.0)) * norm_factor, 1)
            sg = cls._resolve_sg(cat_canonical, code, c.get("default_density_kg_m3"))
            vol = qty / (sg * 1000.0)

            curr_items.append({
                "material_id": mat_id,
                "material_code": code,
                "material_name": name,
                "category_code": cat_canonical,
                "quantity": qty,
                "sg": sg,
                "volume": vol,
                "matched": False,
            })

        # 6. Authoritative Phase 5B Candidate Extraction
        cand_payload = candidate.constituent_payload_json or {}
        cand_constituents = cand_payload.get("constituents", [])
        if not isinstance(cand_constituents, list):
            cand_constituents = []

        cand_items: List[Dict[str, Any]] = []
        for c in cand_constituents:
            mat_id = str(c.get("material_id")) if c.get("material_id") else None
            code = (c.get("material_code") or "").strip().upper()
            name = c.get("material_name") or code
            cat_canonical = cls._infer_canonical_category(c.get("category_code"), code, name)
            qty = round(float(c.get("quantity_kg_m3", 0.0)), 1)
            if math.isnan(qty) or math.isinf(qty) or qty < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid negative or non-finite constituent quantity in candidate: {qty}",
                )
            sg = float(c.get("specific_gravity") or cls._resolve_sg(cat_canonical, code))
            vol = float(c.get("absolute_volume_m3") or (qty / (sg * 1000.0)))

            cand_items.append({
                "material_id": mat_id,
                "material_code": code,
                "material_name": name,
                "category_code": cat_canonical,
                "quantity": qty,
                "sg": sg,
                "volume": vol,
                "matched": False,
            })

        # 7. Strict Canonical Material Identity Resolution
        aligned_pairs: List[Dict[str, Any]] = []

        # Pass 1: Canonical material_id exact match
        for c_cand in cand_items:
            if c_cand["matched"] or not c_cand["material_id"]:
                continue
            for c_curr in curr_items:
                if c_curr["matched"] or not c_curr["material_id"]:
                    continue
                if c_cand["material_id"] == c_curr["material_id"]:
                    c_cand["matched"] = True
                    c_curr["matched"] = True
                    aligned_pairs.append({"curr": c_curr, "cand": c_cand})
                    break

        # Pass 2: Authoritative material_code exact match (provided IDs do not conflict)
        for c_cand in cand_items:
            if c_cand["matched"] or not c_cand["material_code"]:
                continue
            for c_curr in curr_items:
                if c_curr["matched"] or not c_curr["material_code"]:
                    continue
                # If both have explicit IDs that differ, do NOT match
                if c_cand["material_id"] and c_curr["material_id"] and c_cand["material_id"] != c_curr["material_id"]:
                    continue
                if c_cand["material_code"] == c_curr["material_code"] and c_cand["material_code"] not in ["UNKNOWN", "MAT-UNKNOWN"]:
                    c_cand["matched"] = True
                    c_curr["matched"] = True
                    aligned_pairs.append({"curr": c_curr, "cand": c_cand})
                    break

        # Pass 3: Authoritative legacy alias match (reconciling generic legacy names to candidate codes)
        for c_cand in cand_items:
            if c_cand["matched"]:
                continue
            for c_curr in curr_items:
                if c_curr["matched"]:
                    continue
                # If both have explicit IDs that differ, do NOT match
                if c_cand["material_id"] and c_curr["material_id"] and c_cand["material_id"] != c_curr["material_id"]:
                    continue

                # Check known category aliases
                cat = c_cand["category_code"]
                aliases = cls.CANONICAL_CODE_ALIASES.get(cat, [])
                curr_code = c_curr["material_code"]
                cand_code = c_cand["material_code"]

                # Match if both codes belong to the authoritative alias list for this engineering role
                if (curr_code in aliases or not curr_code) and (cand_code in aliases or not cand_code):
                    # Ensure no ambiguity (only match if single unmatched candidate and current for this category)
                    unmatched_cand_cat = [c for c in cand_items if not c["matched"] and c["category_code"] == cat]
                    unmatched_curr_cat = [c for c in curr_items if not c["matched"] and c["category_code"] == cat]
                    if len(unmatched_cand_cat) == 1 and len(unmatched_curr_cat) == 1:
                        c_cand["matched"] = True
                        c_curr["matched"] = True
                        aligned_pairs.append({"curr": c_curr, "cand": c_cand})
                        break

        # Pass 4: Collect unmatched candidate items (New constituents)
        for c_cand in cand_items:
            if not c_cand["matched"]:
                aligned_pairs.append({"curr": None, "cand": c_cand})

        # Pass 5: Collect unmatched current items (Removed constituents)
        for c_curr in curr_items:
            if not c_curr["matched"]:
                aligned_pairs.append({"curr": c_curr, "cand": None})

        # 8. Compute Constituent Deltas
        cat_order = {
            "CEMENT": 1,
            "FLY_ASH": 2,
            "GGBS": 3,
            "WATER": 4,
            "COARSE_AGGREGATE": 5,
            "FINE_AGGREGATE": 6,
            "ADMIXTURE": 7,
            "OTHER": 8,
        }

        impact_constituents: List[ConstituentImpactItemDTO] = []
        for pair in aligned_pairs:
            c_curr = pair["curr"]
            c_cand = pair["cand"]

            mat_id = (c_curr or c_cand).get("material_id")
            mat_code = (c_curr or c_cand).get("material_code") or "MAT-UNKNOWN"
            mat_name = (c_cand or c_curr).get("material_name", mat_code)
            cat_code = (c_cand or c_curr).get("category_code", "OTHER")

            curr_qty = round(float(c_curr["quantity"]), 1) if c_curr else 0.0
            cand_qty = round(float(c_cand["quantity"]), 1) if c_cand else 0.0
            abs_delta = round(cand_qty - curr_qty, 1)

            curr_sg = float(c_curr["sg"]) if c_curr else cls._resolve_sg(cat_code, mat_code)
            cand_sg = float(c_cand["sg"]) if c_cand else cls._resolve_sg(cat_code, mat_code)

            curr_vol = round(float(c_curr["volume"]), 4) if c_curr else 0.0
            cand_vol = round(float(c_cand["volume"]), 4) if c_cand else 0.0
            vol_delta = round(cand_vol - curr_vol, 4)

            # Zero-Baseline State Classification
            if curr_qty > 0 and cand_qty > 0:
                pct_delta = round(((cand_qty - curr_qty) / curr_qty) * 100.0, 1)
                status_lbl = "NORMAL"
            elif curr_qty == 0 and cand_qty > 0:
                pct_delta = None
                status_lbl = "NEW_CONSTITUENT"
            elif curr_qty > 0 and cand_qty == 0:
                pct_delta = -100.0
                status_lbl = "REMOVED_CONSTITUENT"
            else:
                pct_delta = None
                status_lbl = "NO_QUANTITY"

            impact_constituents.append(
                ConstituentImpactItemDTO(
                    material_id=str(mat_id) if mat_id else None,
                    material_code=mat_code,
                    material_name=mat_name,
                    category_code=cat_code,
                    current_quantity_kg_m3=curr_qty,
                    candidate_quantity_kg_m3=cand_qty,
                    absolute_delta_kg_m3=abs_delta,
                    percentage_delta=pct_delta,
                    current_specific_gravity=curr_sg,
                    candidate_specific_gravity=cand_sg,
                    current_volume_m3=curr_vol,
                    candidate_volume_m3=cand_vol,
                    volume_delta_m3=vol_delta,
                    status_label=status_lbl,
                )
            )

        # Sort constituents by canonical category sequence
        impact_constituents.sort(key=lambda item: (cat_order.get(item.category_code, 99), item.material_name))

        # 9. Recipe-Level Summary Delta Computation
        curr_b = sum(it.current_quantity_kg_m3 for it in impact_constituents if it.category_code in ["CEMENT", "FLY_ASH", "GGBS"])
        cand_b = sum(it.candidate_quantity_kg_m3 for it in impact_constituents if it.category_code in ["CEMENT", "FLY_ASH", "GGBS"])
        b_delta = round(cand_b - curr_b, 1)
        b_pct = round(((cand_b - curr_b) / curr_b) * 100.0, 1) if curr_b > 0 else None

        curr_w = sum(it.current_quantity_kg_m3 for it in impact_constituents if it.category_code == "WATER")
        cand_w = sum(it.candidate_quantity_kg_m3 for it in impact_constituents if it.category_code == "WATER")
        w_delta = round(cand_w - curr_w, 1)
        w_pct = round(((cand_w - curr_w) / curr_w) * 100.0, 1) if curr_w > 0 else None

        curr_wb = round(curr_w / curr_b, 3) if curr_b > 0 else 0.0
        cand_wb = round(cand_w / cand_b, 3) if cand_b > 0 else 0.0
        wb_delta = round(cand_wb - curr_wb, 3)

        curr_yield = round(sum(it.current_volume_m3 for it in impact_constituents) + air_volume_m3, 4)
        cand_yield = round(sum(it.candidate_volume_m3 for it in impact_constituents) + air_volume_m3, 4)
        yield_delta = round(cand_yield - curr_yield, 4)

        ca_delta = round(sum(it.absolute_delta_kg_m3 for it in impact_constituents if it.category_code == "COARSE_AGGREGATE"), 1)
        fa_delta = round(sum(it.absolute_delta_kg_m3 for it in impact_constituents if it.category_code == "FINE_AGGREGATE"), 1)
        adm_delta = round(sum(it.absolute_delta_kg_m3 for it in impact_constituents if it.category_code == "ADMIXTURE"), 2)

        impact_summary = RecipeImpactSummaryDTO(
            current_total_binder_kg_m3=round(curr_b, 1),
            candidate_total_binder_kg_m3=round(cand_b, 1),
            binder_delta_kg_m3=b_delta,
            binder_percentage_delta=b_pct,
            current_water_kg_m3=round(curr_w, 1),
            candidate_water_kg_m3=round(cand_w, 1),
            water_delta_kg_m3=w_delta,
            water_percentage_delta=w_pct,
            current_water_binder_ratio=curr_wb,
            candidate_water_binder_ratio=cand_wb,
            water_binder_ratio_delta=wb_delta,
            current_yield_m3=curr_yield,
            candidate_yield_m3=cand_yield,
            yield_delta_m3=yield_delta,
            coarse_aggregate_delta_kg_m3=ca_delta,
            fine_aggregate_delta_kg_m3=fa_delta,
            admixture_delta_kg_m3=adm_delta,
        )

        # 10. Candidate Evaluation Metrics Reuse from Phase 5B
        cand_eval = candidate.constraint_evaluation_json or {}
        candidate_eval_dto = CandidateEvaluationSummaryDTO(
            predicted_strength_mpa=float(candidate.predicted_strength_mpa or cand_eval.get("predicted_strength_mpa", 0.0)),
            target_mean_strength_mpa=float(cand_eval.get("target_mean_strength_mpa", 0.0)),
            strength_margin_mpa=float(cand_eval.get("strength_margin_mpa", 0.0)),
            is_feasible=bool(candidate.is_feasible),
            is_non_dominated=bool(cand_eval.get("is_non_dominated", False)),
            prediction_source=candidate.prediction_source or "ML_MODEL",
            prediction_source_semantics=cand_eval.get("prediction_source_semantics", "Analytical Prediction — Limited Validation"),
        )

        eval_time = None
        if hasattr(candidate, "created_at") and candidate.created_at:
            eval_time = candidate.created_at.isoformat()
        elif hasattr(run, "created_at") and run.created_at:
            eval_time = run.created_at.isoformat()
        else:
            eval_time = datetime.now(timezone.utc).isoformat()

        return RecipeImpactResponseDTO(
            run_id=str(run.id),
            candidate_id=str(candidate.id),
            candidate_identifier=candidate.candidate_identifier,
            recipe_code=run.recipe_code,
            grade=recipe_snap.get("grade", "M30"),
            exposure_class=run.constraints_snapshot_json.get("exposure_class", "MODERATE") if run.constraints_snapshot_json else "MODERATE",
            current_recipe_source="Phase 5A immutable recipe snapshot",
            candidate_recipe_source="Phase 5B persisted candidate",
            constituents=impact_constituents,
            impact_summary=impact_summary,
            candidate_evaluation=candidate_eval_dto,
            evaluated_at=eval_time,
        )
