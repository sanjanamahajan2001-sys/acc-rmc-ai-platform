"""Enterprise AI Mix Optimization Cost and Commercial Feasibility Service (Phase 5D Hardened).

Calculates deterministic material cost per m³, cost deltas, percentage changes,
and scaled production-volume impacts strictly against immutable pricing snapshots.
"""

from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.contracts.optimization.cost_models import (
    CostImpactResponseDTO,
    CostPriceProvenanceDTO,
    MaterialCostImpactDTO,
    ProductionVolumeImpactDTO,
    RecipeCostSummaryDTO,
)
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import User
from src.services.recipe_impact_service import RecipeImpactService


class CostImpactService:
    """Service for deterministic Commercial Feasibility & Cost Impact Analysis (Phase 5D)."""

    @classmethod
    def _normalize_unit_price(
        cls,
        unit_price: Optional[float],
        price_unit: str,
        specific_gravity: Optional[float],
    ) -> Tuple[Optional[float], str]:
        """
        Normalize price unit to ₹/kg.
        
        Rules:
        - ₹/kg or INR/kg -> 1.0 (EXACT)
        - ₹/tonne, INR/tonne, ₹/MT -> divide by 1000.0 (CONVERTED_TONNE)
        - ₹/L, INR/L -> convert using authoritative specific gravity (SG).
            1 Liter = SG kg (water = 1.0 kg/L).
            Price per kg = Price per Liter / SG.
            ONLY valid if specific_gravity is strictly positive (> 0.0) and finite.
            If SG is missing, <= 0, or invalid: returns (None, "PRICE_CONVERSION_UNAVAILABLE").
        - Unsupported unit -> (None, "UNSUPPORTED_UNIT").
        """
        if unit_price is None:
            return None, "UNPRICED"

        try:
            val = float(unit_price)
            if math.isnan(val) or math.isinf(val) or val < 0:
                return None, "PRICE_CONVERSION_UNAVAILABLE"
        except (ValueError, TypeError):
            return None, "PRICE_CONVERSION_UNAVAILABLE"

        u = (price_unit or "").strip().upper()
        # Remove common currency symbols for matching
        u_clean = u.replace("₹", "").replace("INR", "").replace("RS.", "").replace("RS", "").replace("/", "").strip()

        # 1. Per-KG basis
        if u_clean in ("KG", "KGS", ""):
            return round(val, 6), "EXACT"

        # 2. Per-Tonne / MT basis
        if u_clean in ("TONNE", "TONNES", "MT", "TON", "TONS"):
            return round(val / 1000.0, 6), "CONVERTED_TONNE"

        # 3. Per-Liter basis
        if u_clean in ("L", "LTR", "LITER", "LITRE", "LITRES", "LITERS"):
            if specific_gravity is not None:
                try:
                    sg_float = float(specific_gravity)
                    if not math.isnan(sg_float) and not math.isinf(sg_float) and sg_float > 0.0:
                        return round(val / sg_float, 6), "CONVERTED_LITRE"
                except (ValueError, TypeError):
                    pass
            return None, "PRICE_CONVERSION_UNAVAILABLE"

        # 4. Unknown / Unsupported
        return None, "UNSUPPORTED_UNIT"

    @classmethod
    def get_candidate_cost_impact(
        cls,
        db: Session,
        run_id: str,
        candidate_id: str,
        current_user: Optional[User] = None,
    ) -> CostImpactResponseDTO:
        """
        Calculate deterministic cost impact between immutable Phase 5A baseline and Phase 5B candidate.
        
        Strictly reuses Phase 5C canonical identity resolution and material impact comparison.
        """
        # 1. Fetch OptimizationRun
        run = db.query(OptimizationRun).filter(
            OptimizationRun.id == run_id,
            OptimizationRun.is_deleted == False if hasattr(OptimizationRun, "is_deleted") else True,
        ).first()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationRun with ID '{run_id}' not found.",
            )

        # 2. Fetch OptimizationCandidate & enforce run ownership
        candidate = db.query(OptimizationCandidate).filter(
            OptimizationCandidate.id == candidate_id,
            OptimizationCandidate.run_id == run_id,
        ).first()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationCandidate with ID '{candidate_id}' not found for run '{run_id}'.",
            )

        # 3. Obtain Phase 5C Recipe Impact baseline & constituent comparison
        impact_dto = RecipeImpactService.get_candidate_impact(
            db=db,
            run_id=run_id,
            candidate_id=candidate_id,
            current_user=current_user,
        )

        # 4. Extract authoritative immutable pricing snapshot
        pricing_snap = run.pricing_snapshot_json if isinstance(run.pricing_snapshot_json, dict) else None
        is_pricing_configured = bool(pricing_snap and pricing_snap.get("is_configured", False))

        snapshot_id = pricing_snap.get("snapshot_id") if pricing_snap else None
        price_source_name = pricing_snap.get("price_source") if pricing_snap else None
        price_version = pricing_snap.get("price_version") if pricing_snap else None
        effective_from = pricing_snap.get("effective_from") if pricing_snap else None
        effective_to = pricing_snap.get("effective_to") if pricing_snap else None
        currency = pricing_snap.get("currency", "INR") if pricing_snap else "INR"
        plant_code = pricing_snap.get("plant_code", run.plant_code) if pricing_snap else run.plant_code

        # Map material prices from pricing snapshot
        # Key precedence: material_id -> material_code -> category_code
        price_entries = pricing_snap.get("materials", []) if (is_pricing_configured and pricing_snap) else []
        price_map_by_id: Dict[str, Dict[str, Any]] = {}
        price_map_by_code: Dict[str, Dict[str, Any]] = {}
        price_map_by_cat: Dict[str, Dict[str, Any]] = {}

        for p in price_entries:
            p_mat_id = str(p.get("material_id")) if p.get("material_id") else None
            p_code = (p.get("material_code") or "").strip().upper()
            p_cat = RecipeImpactService._infer_canonical_category(p.get("category_code"), p_code, p.get("material_name"))

            if p_mat_id:
                price_map_by_id[p_mat_id] = p
            if p_code:
                price_map_by_code[p_code] = p
            if p_cat and p_cat != "OTHER":
                price_map_by_cat[p_cat] = p

        # 5. Itemize constituent costs
        material_impacts: List[MaterialCostImpactDTO] = []
        unpriced_materials: List[str] = []
        all_materials_priced = is_pricing_configured and len(price_entries) > 0

        for item in impact_dto.constituents:
            # Match price entry
            matched_price = None
            if item.material_id and item.material_id in price_map_by_id:
                matched_price = price_map_by_id[item.material_id]
            elif item.material_code and item.material_code.upper() in price_map_by_code:
                matched_price = price_map_by_code[item.material_code.upper()]
            elif item.category_code in price_map_by_cat:
                matched_price = price_map_by_cat[item.category_code]

            unit_price_raw = matched_price.get("unit_price") if matched_price else None
            price_unit = matched_price.get("price_unit", "₹/kg") if matched_price else "₹/kg"
            price_curr = matched_price.get("currency", currency) if matched_price else currency
            
            # Use specific gravity from candidate or master snapshot (do not assume fallback if absent)
            sg = item.candidate_specific_gravity or item.current_specific_gravity

            unit_price_per_kg, conv_status = cls._normalize_unit_price(unit_price_raw, price_unit, sg)
            is_price_available = unit_price_per_kg is not None

            # Check if active constituent is missing price or has invalid conversion
            is_active = (item.current_quantity_kg_m3 > 0 or item.candidate_quantity_kg_m3 > 0)
            if is_active and not is_price_available:
                all_materials_priced = False
                unpriced_materials.append(item.material_name)

            # Calculate item costs
            if is_price_available:
                m_cost = round(item.current_quantity_kg_m3 * unit_price_per_kg, 2)
                c_cost = round(item.candidate_quantity_kg_m3 * unit_price_per_kg, 2)
                c_delta = round(c_cost - m_cost, 2)
                c_pct = round(((c_cost - m_cost) / m_cost) * 100.0, 1) if m_cost > 0 else None
            else:
                m_cost = None
                c_cost = None
                c_delta = None
                c_pct = None

            price_prov = CostPriceProvenanceDTO(
                snapshot_id=snapshot_id,
                material_id=item.material_id,
                material_code=item.material_code,
                unit_price=unit_price_raw,
                price_unit=price_unit,
                currency=price_curr,
                price_source=price_source_name or "NOT_CONFIGURED",
                price_version=price_version,
                effective_from=effective_from,
                effective_to=effective_to,
                plant_code=plant_code,
                conversion_status=conv_status if is_price_available else conv_status,
                is_available=is_price_available,
            )

            # Determine status label
            status_lbl = item.status_label
            if status_lbl == "NORMAL":
                if not is_price_available and is_active:
                    status_lbl = conv_status if conv_status in ("PRICE_CONVERSION_UNAVAILABLE", "UNSUPPORTED_UNIT") else "UNPRICED"

            material_impacts.append(
                MaterialCostImpactDTO(
                    material_id=item.material_id,
                    material_code=item.material_code,
                    material_name=item.material_name,
                    category_code=item.category_code,
                    master_quantity_kg_m3=item.current_quantity_kg_m3,
                    candidate_quantity_kg_m3=item.candidate_quantity_kg_m3,
                    quantity_delta_kg_m3=item.absolute_delta_kg_m3,
                    unit_price_per_kg=unit_price_per_kg,
                    price_unit_display=price_unit,
                    currency=price_curr,
                    master_cost_per_m3=m_cost,
                    candidate_cost_per_m3=c_cost,
                    cost_delta_per_m3=c_delta,
                    cost_delta_percent=c_pct,
                    price_provenance=price_prov,
                    status_label=status_lbl,
                )
            )

        # 6. Recipe-Level Cost Summaries
        if all_materials_priced and is_pricing_configured:
            master_total_cost = round(sum(it.master_cost_per_m3 for it in material_impacts if it.master_cost_per_m3 is not None), 2)
            candidate_total_cost = round(sum(it.candidate_cost_per_m3 for it in material_impacts if it.candidate_cost_per_m3 is not None), 2)
            cost_delta = round(candidate_total_cost - master_total_cost, 2)
            cost_delta_pct = round(((candidate_total_cost - master_total_cost) / master_total_cost) * 100.0, 1) if master_total_cost > 0 else None
            cost_status = "CONFIGURED"
            total_cost_available = True
            provenance_display = f"Pricing Source: {price_source_name or 'Immutable Phase 5A Pricing Snapshot'}"
        elif is_pricing_configured:
            master_total_cost = None
            candidate_total_cost = None
            cost_delta = None
            cost_delta_pct = None
            cost_status = "PARTIALLY_CONFIGURED"
            total_cost_available = False
            provenance_display = f"Pricing Source: {price_source_name or 'Immutable Phase 5A Pricing Snapshot'} (Partial)"
        else:
            master_total_cost = None
            candidate_total_cost = None
            cost_delta = None
            cost_delta_pct = None
            cost_status = "NOT_CONFIGURED"
            total_cost_available = False
            provenance_display = "Pricing Source: Not Configured"

        # 7. Production Volume Impact Calculations & Validation
        vol_info = pricing_snap.get("production_volume", {}) if isinstance(pricing_snap, dict) else {}
        has_vol_flag = bool(vol_info.get("is_configured", False))

        daily_v_raw = vol_info.get("daily_volume_m3")
        monthly_v_raw = vol_info.get("monthly_volume_m3")
        annual_v_raw = vol_info.get("annualized_volume_m3")

        # Validate numeric positivity
        def _parse_vol(v: Any) -> Optional[float]:
            if v is None:
                return None
            try:
                vf = float(v)
                return vf if vf > 0 and not math.isnan(vf) and not math.isinf(vf) else None
            except (ValueError, TypeError):
                return None

        daily_v = _parse_vol(daily_v_raw)
        monthly_v = _parse_vol(monthly_v_raw)
        annual_v = _parse_vol(annual_v_raw)

        # If flagged as configured, ensure at least one valid positive period exists and no negative/impossible numbers
        has_invalid_numbers = (
            (daily_v_raw is not None and daily_v is None) or
            (monthly_v_raw is not None and monthly_v is None) or
            (annual_v_raw is not None and annual_v is None)
        )

        is_vol_configured = (
            has_vol_flag and
            not has_invalid_numbers and
            (daily_v is not None or monthly_v is not None or annual_v is not None) and
            cost_status == "CONFIGURED" and
            total_cost_available and
            cost_delta is not None
        )

        if is_vol_configured:
            prod_impact = ProductionVolumeImpactDTO(
                is_configured=True,
                volume_source=vol_info.get("volume_source", "PLANT_PRODUCTION_SCHEDULE"),
                volume_period=vol_info.get("volume_period", "MULTI_PERIOD"),
                volume_basis=vol_info.get("volume_basis", "ACTUAL_DISPATCH_OR_CAPACITY"),
                daily_volume_m3=daily_v,
                monthly_volume_m3=monthly_v,
                annualized_volume_m3=annual_v,
                daily_cost_delta=round(cost_delta * daily_v, 2) if daily_v is not None else None,
                monthly_cost_delta=round(cost_delta * monthly_v, 2) if monthly_v is not None else None,
                annualized_cost_delta=round(cost_delta * annual_v, 2) if annual_v is not None else None,
                currency=currency,
            )
        else:
            prod_impact = ProductionVolumeImpactDTO(
                is_configured=False,
                volume_source=None,
                volume_period=None,
                volume_basis=None,
                currency=currency,
            )

        cost_summary = RecipeCostSummaryDTO(
            cost_status=cost_status,
            total_cost_available=total_cost_available,
            currency=currency,
            master_cost_per_m3=master_total_cost,
            candidate_cost_per_m3=candidate_total_cost,
            cost_delta_per_m3=cost_delta,
            cost_delta_percent=cost_delta_pct,
            unpriced_materials=unpriced_materials,
            missing_price_constituents=unpriced_materials,
            production_impact=prod_impact,
        )

        return CostImpactResponseDTO(
            run_id=str(run.id),
            candidate_id=str(candidate.id),
            candidate_identifier=candidate.candidate_identifier,
            recipe_code=run.recipe_code,
            grade=impact_dto.grade,
            plant_code=run.plant_code,
            is_feasible=candidate.is_feasible,
            cost_summary=cost_summary,
            material_impacts=material_impacts,
            price_source_description=provenance_display,
            pricing_snapshot_id=snapshot_id,
            pricing_version=price_version,
            effective_date=effective_from,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )
