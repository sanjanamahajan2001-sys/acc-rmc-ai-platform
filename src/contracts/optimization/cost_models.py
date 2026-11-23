"""Enterprise AI Mix Optimization Cost and Commercial Feasibility DTO Contracts (Phase 5D)."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CostPriceProvenanceDTO(BaseModel):
    """Authoritative price metadata and provenance for a single constituent material."""
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: Optional[str] = Field(default=None, description="Authoritative pricing snapshot UUID or reference")
    material_id: Optional[str] = Field(default=None, description="Authoritative Material UUID")
    material_code: str = Field(description="Canonical material code")
    unit_price: Optional[float] = Field(default=None, description="Authoritative unit price value as recorded in snapshot")
    price_unit: str = Field(default="₹/kg", description="Normalized price unit (e.g. ₹/kg, ₹/tonne, ₹/L)")
    currency: str = Field(default="INR", description="Currency code (e.g. INR, USD)")
    price_source: str = Field(default="NOT_CONFIGURED", description="Origin of pricing data")
    price_version: Optional[str] = Field(default=None, description="Price version/revision identifier")
    effective_from: Optional[str] = Field(default=None, description="Effective start date ISO string")
    effective_to: Optional[str] = Field(default=None, description="Effective end date ISO string if bounded")
    plant_code: Optional[str] = Field(default=None, description="Plant code associated with the price snapshot")
    conversion_status: str = Field(default="EXACT", description="EXACT, CONVERTED_TONNE, CONVERTED_LITRE, PRICE_CONVERSION_UNAVAILABLE, UNSUPPORTED_UNIT, UNPRICED")
    is_available: bool = Field(default=False, description="True if an authoritative price exists and was successfully converted")


class MaterialCostImpactDTO(BaseModel):
    """Itemized constituent material cost comparison and delta."""
    model_config = ConfigDict(from_attributes=True)

    material_id: Optional[str] = None
    material_code: str
    material_name: str
    category_code: str

    master_quantity_kg_m3: float = Field(description="Normalized quantity in master snapshot (kg/m³)")
    candidate_quantity_kg_m3: float = Field(description="Quantity in candidate mix (kg/m³)")
    quantity_delta_kg_m3: float = Field(description="candidate_qty - master_qty (kg/m³)")

    unit_price_per_kg: Optional[float] = Field(default=None, description="Authoritative unit price normalized to per-kg basis")
    price_unit_display: str = Field(default="₹/kg", description="Display price unit string")
    currency: str = Field(default="INR", description="Currency symbol/code")

    master_cost_per_m3: Optional[float] = Field(default=None, description="master_quantity × price_per_kg (₹/m³)")
    candidate_cost_per_m3: Optional[float] = Field(default=None, description="candidate_quantity × price_per_kg (₹/m³)")
    cost_delta_per_m3: Optional[float] = Field(default=None, description="candidate_cost - master_cost (₹/m³)")
    cost_delta_percent: Optional[float] = Field(default=None, description="Percentage change in cost or None if master_cost == 0")

    price_provenance: CostPriceProvenanceDTO
    status_label: str = Field(default="NORMAL", description="NORMAL, NEW_CONSTITUENT, REMOVED_CONSTITUENT, NO_QUANTITY, UNPRICED, PRICE_CONVERSION_UNAVAILABLE")


class ProductionVolumeImpactDTO(BaseModel):
    """Commercial cost impact scaled to authoritative production volume periods."""
    model_config = ConfigDict(from_attributes=True)

    is_configured: bool = Field(default=False, description="True if authoritative production volume is established and valid")
    volume_source: Optional[str] = Field(default=None, description="Origin of production volume schedule")
    volume_period: Optional[str] = Field(default=None, description="Periodicity of volume schedule (e.g. DAILY, MONTHLY, ANNUAL)")
    volume_basis: Optional[str] = Field(default=None, description="Basis of volume calculation")

    daily_volume_m3: Optional[float] = None
    monthly_volume_m3: Optional[float] = None
    annualized_volume_m3: Optional[float] = None

    daily_cost_delta: Optional[float] = None
    monthly_cost_delta: Optional[float] = None
    annualized_cost_delta: Optional[float] = None

    currency: str = "INR"


class RecipeCostSummaryDTO(BaseModel):
    """Aggregated recipe-level cost summary metrics."""
    model_config = ConfigDict(from_attributes=True)

    cost_status: str = Field(description="CONFIGURED, NOT_CONFIGURED, or PARTIALLY_CONFIGURED")
    total_cost_available: bool = Field(default=False, description="True ONLY when all active constituents are fully priced")
    currency: str = Field(default="INR")

    master_cost_per_m3: Optional[float] = Field(default=None, description="Total material cost for master recipe (₹/m³)")
    candidate_cost_per_m3: Optional[float] = Field(default=None, description="Total material cost for candidate mix (₹/m³)")
    cost_delta_per_m3: Optional[float] = Field(default=None, description="candidate_cost - master_cost (₹/m³)")
    cost_delta_percent: Optional[float] = Field(default=None, description="Percentage cost change or None if master_cost == 0")

    unpriced_materials: List[str] = Field(default_factory=list, description="List of material names lacking authoritative pricing or conversion")
    missing_price_constituents: List[str] = Field(default_factory=list, description="Backward compatibility synonym for unpriced_materials")
    production_impact: ProductionVolumeImpactDTO


class CostImpactResponseDTO(BaseModel):
    """Top-level response payload for Phase 5D Cost & Commercial Feasibility."""
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    candidate_id: str
    candidate_identifier: str
    recipe_code: str
    grade: str
    plant_code: str
    is_feasible: bool = Field(default=True, description="Feasibility classification from Phase 5B candidate evaluation")

    cost_summary: RecipeCostSummaryDTO
    material_impacts: List[MaterialCostImpactDTO]

    price_source_description: str = Field(description="Exact provenance description or 'Pricing Source: Not Configured'")
    pricing_snapshot_id: Optional[str] = None
    pricing_version: Optional[str] = None
    effective_date: Optional[str] = None
    calculated_at: str
