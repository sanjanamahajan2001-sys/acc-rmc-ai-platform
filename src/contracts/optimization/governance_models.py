"""Enterprise AI Mix Optimization Recommendation Governance & Human Review Contracts (Phase 5E).

Establishes deterministic typed data contracts for human review gating,
governance state tracking, role-based action permissions, and audit provenance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CandidateGovernanceItemDTO(BaseModel):
    """Itemized governance evaluation and human review status for an optimization candidate."""

    candidate_id: str = Field(..., description="OptimizationCandidate UUID")
    candidate_identifier: str = Field(..., description="Human-readable candidate identifier (e.g. CAND-01)")
    
    # Authoritative Engineering Facts (Preserved from Phase 5B / 5C)
    is_feasible: bool = Field(..., description="Deterministic engineering feasibility from Phase 5B")
    is_pareto_optimal: bool = Field(..., description="Pareto non-dominated status from Phase 5B")
    predicted_strength_mpa: Optional[float] = Field(None, description="ML predicted 28-day strength in MPa")
    target_mean_strength_mpa: Optional[float] = Field(None, description="Target mean strength f'ck in MPa")
    characteristic_strength_fck_mpa: Optional[float] = Field(None, description="Characteristic strength fck in MPa")
    strength_margin_mpa: Optional[float] = Field(None, description="Strength margin above target in MPa")
    binder_intensity_kg_m3: float = Field(..., description="Total cementitious binder intensity in kg/m3")
    water_binder_ratio: float = Field(..., description="Water-to-binder ratio")
    yield_m3: Optional[float] = Field(None, description="Physical wet density volume balance in m3")
    
    # Authoritative Commercial Facts (Preserved from Phase 5D)
    cost_status: str = Field(..., description="Commercial pricing status: CONFIGURED, PARTIALLY_CONFIGURED, NOT_CONFIGURED")
    cost_per_m3: Optional[float] = Field(None, description="Candidate total material cost per m3 in INR")
    cost_delta_per_m3: Optional[float] = Field(None, description="Cost delta vs master baseline per m3 in INR")
    cost_delta_percent: Optional[float] = Field(None, description="Percentage cost change vs master baseline")
    
    # Governance State & Eligibility
    eligibility_status: str = Field(
        ...,
        description="Governance eligibility: ELIGIBLE_FOR_HUMAN_REVIEW, NOT_ELIGIBLE_INFEASIBLE, NOT_ELIGIBLE_NON_PARETO, NOT_ELIGIBLE_NO_FEASIBLE",
    )
    eligibility_reason_code: str = Field(..., description="Deterministic reason code for eligibility classification")
    eligibility_reason_description: str = Field(..., description="Human-readable explanation of governance eligibility")
    
    # Human Review Lifecycle State
    review_status: str = Field(
        default="PENDING_REVIEW",
        description="Review decision state: PENDING_REVIEW, ACCEPTED, REJECTED",
    )
    reviewed_by_user_id: Optional[str] = Field(None, description="UUID of user who performed review")
    reviewed_by_username: Optional[str] = Field(None, description="Username / full name of reviewer")
    reviewed_at: Optional[str] = Field(None, description="ISO timestamp of human review decision")
    review_decision_reason: Optional[str] = Field(None, description="Reason code supplied by human reviewer")
    review_comments: Optional[str] = Field(None, description="Optional engineering notes or comments from reviewer")
    
    # Lineage & Permissions
    model_lineage_description: str = Field(..., description="Active ML model and dataset provenance summary")
    allowed_actions: List[str] = Field(default_factory=list, description="Allowed governance actions: ACCEPT, REJECT, RESET")


class RunGovernanceResponseDTO(BaseModel):
    """Run-level governance summary and list of candidate governance items."""

    run_id: str = Field(..., description="OptimizationRun UUID")
    recipe_code: str = Field(..., description="Target master recipe code")
    grade: str = Field(..., description="Design strength grade (e.g. M20, M30)")
    plant_code: str = Field(..., description="Production plant code")
    run_status: str = Field(..., description="Optimization run execution status")
    
    # Candidate Counts
    total_candidates: int = Field(..., description="Total candidate mixes generated")
    feasible_candidates_count: int = Field(..., description="Count of engineering feasible candidates")
    pareto_optimal_count: int = Field(..., description="Count of Pareto optimal candidates")
    eligible_for_review_count: int = Field(..., description="Count of candidates eligible for human review")
    reviewed_accepted_count: int = Field(..., description="Count of accepted candidates")
    reviewed_rejected_count: int = Field(..., description="Count of rejected candidates")
    
    # State flags & summaries
    has_feasible_candidates: bool = Field(..., description="True if at least one feasible candidate exists")
    governance_message: str = Field(..., description="Authoritative summary banner message")
    cost_status: str = Field(..., description="Commercial pricing status: CONFIGURED, PARTIALLY_CONFIGURED, NOT_CONFIGURED")
    price_source_description: str = Field(..., description="Pricing provenance description")
    
    # Role & Disclaimer
    user_can_review: bool = Field(..., description="True if current authenticated user has review authorization")
    user_role: str = Field(..., description="Current user's active domain role")
    production_activation_status: str = Field(
        default="PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE",
        description="Explicit notice that plant batching activation is outside Phase 5E scope",
    )
    
    candidates: List[CandidateGovernanceItemDTO] = Field(
        default_factory=list,
        description="Ordered candidate governance items",
    )
    evaluated_at: str = Field(..., description="ISO timestamp of evaluation")


class CandidateReviewActionRequestDTO(BaseModel):
    """Payload for submitting a human review decision on an optimization candidate."""

    action: str = Field(
        ...,
        description="Governance action: ACCEPT, REJECT, RESET",
    )
    reason_code: str = Field(
        ...,
        description="Authoritative reason code for the decision (e.g. TECHNICAL_VALIDATION_CONFIRMED, LAB_TRIAL_REQUIRED)",
    )
    comments: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional engineering rationale notes",
    )
