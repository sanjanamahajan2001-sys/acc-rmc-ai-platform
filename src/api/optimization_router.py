"""FastAPI Router for AI Mix Optimization Endpoints (Phase 5A, 5B, 5C, 5D, and 5E)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from src.contracts.optimization.cost_models import CostImpactResponseDTO
from src.contracts.optimization.governance_models import (
    CandidateGovernanceItemDTO,
    CandidateReviewActionRequestDTO,
    RunGovernanceResponseDTO,
)
from src.contracts.optimization.impact_models import RecipeImpactResponseDTO
from src.contracts.optimization.models import (
    CandidateEvaluationResponseDTO,
    OptimizationCandidateDTO,
    OptimizationRunResponseDTO,
    OptimizationRunTriggerRequestDTO,
)
from src.database.models.user import User
from src.security.dependencies import _extract_client_ip, get_current_user, get_db, require_roles
from src.services.candidate_solver_service import CandidateSolverService
from src.services.cost_impact_service import CostImpactService
from src.services.mix_optimization_service import MixOptimizationService
from src.services.recipe_impact_service import RecipeImpactService
from src.services.recommendation_governance_service import RecommendationGovernanceService

router = APIRouter(prefix="/api/v1/optimization", tags=["AI Mix Optimization"])


@router.post(
    "/runs/trigger",
    response_model=OptimizationRunResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an explicit AI Mix Optimization Run snapshot (Phase 5A)",
)
def trigger_optimization_run(
    request_dto: OptimizationRunTriggerRequestDTO,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("QUALITY_ENGINEER", "PLANT_MANAGER", "ADMIN", "SUPER_ADMIN", "DISPATCHER", "OPERATOR")
    ),
) -> OptimizationRunResponseDTO:
    """Explicitly trigger a new optimization run context, capturing immutable snapshots of recipe and model state."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-request-id")

    return MixOptimizationService.trigger_optimization_run(
        db=db,
        request=request_dto,
        current_user=current_user,
        correlation_id=correlation_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.get(
    "/runs/latest",
    response_model=Optional[OptimizationRunResponseDTO],
    summary="Retrieve the most recent optimization run without recomputing",
)
def get_latest_optimization_run(
    recipe_code: Optional[str] = Query(None, description="Filter by Master Recipe Code"),
    plant_code: Optional[str] = Query(None, description="Filter by Plant Code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[OptimizationRunResponseDTO]:
    """Fetch the latest persisted optimization run for a given recipe/plant."""
    return MixOptimizationService.get_latest_optimization_run(
        db=db,
        recipe_code=recipe_code,
        plant_code=plant_code,
    )


@router.post(
    "/runs/{run_id}/evaluate",
    response_model=CandidateEvaluationResponseDTO,
    summary="Evaluate candidate mix alternatives with physical validation and Pareto classification (Phase 5B)",
)
def evaluate_optimization_candidates(
    run_id: str = Path(..., description="OptimizationRun UUID to evaluate"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("QUALITY_ENGINEER", "PLANT_MANAGER", "ADMIN", "SUPER_ADMIN", "DISPATCHER", "OPERATOR")
    ),
) -> CandidateEvaluationResponseDTO:
    """Execute bounded candidate solver, physical balance, ML inference, and Pareto classification."""
    client_ip = _extract_client_ip(request) if request else None
    user_agent = request.headers.get("user-agent") if request else None
    correlation_id = (request.headers.get("X-Correlation-ID") or request.headers.get("x-request-id")) if request else None

    return CandidateSolverService.evaluate_run_candidates(
        db=db,
        run_id=run_id,
        current_user=current_user,
        correlation_id=correlation_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.get(
    "/runs/{run_id}/candidates",
    response_model=List[OptimizationCandidateDTO],
    summary="Retrieve persisted evaluated candidates for a specific optimization run",
)
def get_run_candidates(
    run_id: str = Path(..., description="OptimizationRun UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[OptimizationCandidateDTO]:
    """Fetch all persisted evaluated candidate mixes with full engineering diagnostics."""
    res = CandidateSolverService.evaluate_run_candidates(
        db=db,
        run_id=run_id,
        current_user=current_user,
    )
    return res.candidates


@router.get(
    "/runs/{run_id}/candidates/{candidate_id}/impact",
    response_model=RecipeImpactResponseDTO,
    summary="Retrieve side-by-side recipe impact and constituent comparison (Phase 5C)",
)
def get_candidate_recipe_impact(
    run_id: str = Path(..., description="OptimizationRun UUID"),
    candidate_id: str = Path(..., description="OptimizationCandidate UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeImpactResponseDTO:
    """Retrieve deterministic comparison between immutable Phase 5A baseline and Phase 5B candidate."""
    return RecipeImpactService.get_candidate_impact(
        db=db,
        run_id=run_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )


@router.get(
    "/runs/{run_id}/candidates/{candidate_id}/cost-impact",
    response_model=CostImpactResponseDTO,
    summary="Retrieve itemized cost and commercial feasibility comparison (Phase 5D)",
)
def get_candidate_cost_impact(
    run_id: str = Path(..., description="OptimizationRun UUID"),
    candidate_id: str = Path(..., description="OptimizationCandidate UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CostImpactResponseDTO:
    """Retrieve deterministic cost comparison, per-m3 deltas, and volume impacts between master recipe and candidate mix."""
    return CostImpactService.get_candidate_cost_impact(
        db=db,
        run_id=run_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )


@router.get(
    "/runs/{run_id}/governance",
    response_model=RunGovernanceResponseDTO,
    summary="Retrieve recommendation governance state and human review lifecycle (Phase 5E)",
)
def get_run_governance(
    run_id: str = Path(..., description="OptimizationRun UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunGovernanceResponseDTO:
    """Retrieve recommendation governance summary, eligibility gating, and human review status."""
    return RecommendationGovernanceService.get_run_governance(
        db=db,
        run_id=run_id,
        current_user=current_user,
    )


@router.post(
    "/runs/{run_id}/candidates/{candidate_id}/review",
    response_model=CandidateGovernanceItemDTO,
    summary="Submit an authoritative human review decision on an optimization candidate (Phase 5E)",
)
def review_optimization_candidate(
    request_dto: CandidateReviewActionRequestDTO,
    request: Request,
    run_id: str = Path(..., description="OptimizationRun UUID"),
    candidate_id: str = Path(..., description="OptimizationCandidate UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CandidateGovernanceItemDTO:
    """Record an authoritative human review decision (ACCEPT, REJECT, RESET) with full audit logging."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-request-id")

    return RecommendationGovernanceService.review_candidate(
        db=db,
        run_id=run_id,
        candidate_id=candidate_id,
        request_dto=request_dto,
        current_user=current_user,
        correlation_id=correlation_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )
