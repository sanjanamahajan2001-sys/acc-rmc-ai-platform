"""Enterprise AI Mix Optimization Recommendation Governance & Human Review Service (Phase 5E).

Implements deterministic governance gating, human review lifecycle transitions,
role-based authorization checks, and security audit traceability over certified optimization outputs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.contracts.optimization.governance_models import (
    CandidateGovernanceItemDTO,
    CandidateReviewActionRequestDTO,
    RunGovernanceResponseDTO,
)
from src.database.models.optimization import OptimizationCandidate, OptimizationRun
from src.database.models.user import SecurityAuditLog, User
from src.services.cost_impact_service import CostImpactService
from src.services.recipe_impact_service import RecipeImpactService

AUTHORIZED_REVIEW_ROLES = {
    "SUPER_ADMIN",
    "ADMIN",
    "QUALITY_HEAD",
    "QUALITY_ENGINEER",
    "PLANT_MANAGER",
}


class RecommendationGovernanceService:
    """Deterministic governance service managing human review gates and recommendation policy."""

    @classmethod
    def _is_user_authorized_for_review(cls, user: Optional[User]) -> bool:
        """Check if user has authoritative domain roles required to make governance decisions."""
        if not user:
            return False
        user_roles = {r.role_id for r in user.role_assignments}
        if "SUPER_ADMIN" in user_roles:
            return True
        return bool(user_roles.intersection(AUTHORIZED_REVIEW_ROLES))

    @classmethod
    def _get_user_primary_role(cls, user: Optional[User]) -> str:
        """Resolve highest active role identifier for the user."""
        if not user:
            return "ANONYMOUS"
        user_roles = {r.role_id for r in user.role_assignments}
        for r in ["SUPER_ADMIN", "ADMIN", "QUALITY_HEAD", "QUALITY_ENGINEER", "PLANT_MANAGER", "LAB_TECHNICIAN", "PLANT_OPERATOR", "ANALYST_VIEWER"]:
            if r in user_roles:
                return r
        return list(user_roles)[0] if user_roles else "VIEWER"

    @classmethod
    def get_run_governance(
        cls,
        db: Session,
        run_id: str,
        current_user: Optional[User] = None,
    ) -> RunGovernanceResponseDTO:
        """
        Evaluate and return the complete governance status for an optimization run.
        
        Consumes existing persisted candidates and certified Phase 5C/5D outputs.
        Does NOT recompute engineering simulations or pricing models.
        """
        run = db.get(OptimizationRun, run_id)
        if not run or run.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationRun with ID '{run_id}' not found.",
            )

        candidates = db.scalars(
            select(OptimizationCandidate)
            .where(OptimizationCandidate.run_id == run_id)
            .order_by(OptimizationCandidate.candidate_identifier.asc())
        ).all()

        user_can_review = cls._is_user_authorized_for_review(current_user)
        user_role = cls._get_user_primary_role(current_user)

        # Load snapshots & pricing context
        pricing_snap = run.pricing_snapshot_json
        model_snap = run.model_snapshot_json or {}
        target_strength_snap = run.target_strength_snapshot_json or {}

        model_name = model_snap.get("model_name", "Enterprise Concrete Strength Predictor")
        model_ver = model_snap.get("model_version", "Active")
        model_lineage = f"{model_name} (Ver: {model_ver})"

        is_pricing_configured = bool(
            pricing_snap and isinstance(pricing_snap, dict) and pricing_snap.get("is_configured")
        )
        cost_status_overall = "CONFIGURED" if is_pricing_configured else "NOT_CONFIGURED"
        price_source_display = (
            f"Pricing Source: {pricing_snap.get('price_source_name', 'Procurement Snapshot')}"
            if is_pricing_configured
            else "Pricing Source: Not Configured"
        )

        governance_items: List[CandidateGovernanceItemDTO] = []
        feasible_count = 0
        pareto_count = 0
        eligible_count = 0
        accepted_count = 0
        rejected_count = 0

        target_mean_fck = float(target_strength_snap.get("target_mean_strength_fck_prime_mpa", 0.0)) or None
        char_fck = float(target_strength_snap.get("characteristic_strength_fck_mpa", 0.0)) or None

        for cand in candidates:
            c_eval = cand.constraint_evaluation_json or {}
            c_payload = cand.constituent_payload_json or {}
            
            is_feasible = bool(cand.is_feasible)
            is_pareto = bool(c_eval.get("is_non_dominated", False))

            if is_feasible:
                feasible_count += 1
            if is_pareto:
                pareto_count += 1

            # Resolve yield and W/B from persisted payloads
            phys_diag = c_eval.get("physical_volume_diagnostic", {})
            yield_m3 = phys_diag.get("volume_balance_actual_m3")
            wb_ratio = float(c_payload.get("water_binder_ratio", 0.0))
            pred_str = float(cand.predicted_strength_mpa) if cand.predicted_strength_mpa is not None else None
            margin = float(c_eval.get("strength_margin_mpa")) if c_eval.get("strength_margin_mpa") is not None else (
                round(pred_str - target_mean_fck, 2) if (pred_str is not None and target_mean_fck is not None) else None
            )

            # Resolve Cost Status per Candidate from Phase 5D
            cand_cost_status = cost_status_overall
            cand_cost_per_m3 = float(cand.cost_per_m3) if (cand.cost_per_m3 is not None and is_pricing_configured) else None
            cand_cost_delta = None
            cand_cost_pct = None

            # Attempt to fetch detailed cost impact if configured
            if is_pricing_configured:
                try:
                    cost_impact = CostImpactService.get_candidate_cost_impact(
                        db=db, run_id=run_id, candidate_id=str(cand.id), current_user=current_user
                    )
                    cand_cost_status = cost_impact.cost_summary.cost_status
                    cand_cost_per_m3 = cost_impact.cost_summary.candidate_cost_per_m3
                    cand_cost_delta = cost_impact.cost_summary.cost_delta_per_m3
                    cand_cost_pct = cost_impact.cost_summary.cost_delta_percent
                except Exception:
                    pass

            # Governance Eligibility Gating
            if not is_feasible:
                eligibility_status = "NOT_ELIGIBLE_INFEASIBLE"
                eligibility_reason_code = "INFEASIBLE_CANDIDATE"
                eligibility_reason_description = (
                    "Candidate violates physical volume or IS standard engineering constraints. Quarantined for diagnostic inspection only."
                )
                allowed_actions = []
            elif is_feasible and is_pareto:
                eligibility_status = "ELIGIBLE_FOR_HUMAN_REVIEW"
                eligibility_reason_code = "ELIGIBLE_FOR_HUMAN_REVIEW"
                eligibility_reason_description = (
                    "Candidate satisfies all engineering constraints and lies on the Pareto-optimal frontier."
                )
                eligible_count += 1
                allowed_actions = ["ACCEPT", "REJECT", "RESET"] if user_can_review else []
            else:
                eligibility_status = "NOT_ELIGIBLE_NON_PARETO"
                eligibility_reason_code = "NON_PARETO_OPTIMAL"
                eligibility_reason_description = (
                    "Candidate is engineering feasible but dominated by another alternative with superior performance."
                )
                allowed_actions = ["ACCEPT", "REJECT", "RESET"] if user_can_review else []

            # Review Lifecycle State
            review_status = c_eval.get("review_status", "PENDING_REVIEW")
            if review_status == "ACCEPTED":
                accepted_count += 1
            elif review_status == "REJECTED":
                rejected_count += 1

            governance_items.append(
                CandidateGovernanceItemDTO(
                    candidate_id=str(cand.id),
                    candidate_identifier=cand.candidate_identifier,
                    is_feasible=is_feasible,
                    is_pareto_optimal=is_pareto,
                    predicted_strength_mpa=pred_str,
                    target_mean_strength_mpa=target_mean_fck,
                    characteristic_strength_fck_mpa=char_fck,
                    strength_margin_mpa=margin,
                    binder_intensity_kg_m3=float(cand.binder_intensity or 0.0),
                    water_binder_ratio=wb_ratio,
                    yield_m3=yield_m3,
                    cost_status=cand_cost_status,
                    cost_per_m3=cand_cost_per_m3,
                    cost_delta_per_m3=cand_cost_delta,
                    cost_delta_percent=cand_cost_pct,
                    eligibility_status=eligibility_status,
                    eligibility_reason_code=eligibility_reason_code,
                    eligibility_reason_description=eligibility_reason_description,
                    review_status=review_status,
                    reviewed_by_user_id=c_eval.get("reviewed_by_user_id"),
                    reviewed_by_username=c_eval.get("reviewed_by_username"),
                    reviewed_at=c_eval.get("reviewed_at"),
                    review_decision_reason=c_eval.get("review_decision_reason"),
                    review_comments=c_eval.get("review_comments"),
                    model_lineage_description=model_lineage,
                    allowed_actions=allowed_actions,
                )
            )

        # Governance Message
        has_feasible = (feasible_count > 0)
        if not has_feasible:
            gov_message = "No feasible candidate is currently available for human review."
        elif eligible_count > 0:
            gov_message = f"{eligible_count} candidate(s) are eligible for human engineering review. Production activation is outside the current phase."
        else:
            gov_message = "Evaluated candidates do not meet Pareto optimality criteria for review."

        return RunGovernanceResponseDTO(
            run_id=str(run.id),
            recipe_code=run.recipe_code,
            grade=target_strength_snap.get("grade", "N/A"),
            plant_code=run.plant_code,
            run_status=run.run_status,
            total_candidates=len(candidates),
            feasible_candidates_count=feasible_count,
            pareto_optimal_count=pareto_count,
            eligible_for_review_count=eligible_count,
            reviewed_accepted_count=accepted_count,
            reviewed_rejected_count=rejected_count,
            has_feasible_candidates=has_feasible,
            governance_message=gov_message,
            cost_status=cost_status_overall,
            price_source_description=price_source_display,
            user_can_review=user_can_review,
            user_role=user_role,
            production_activation_status="PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE",
            candidates=governance_items,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def review_candidate(
        cls,
        db: Session,
        run_id: str,
        candidate_id: str,
        request_dto: CandidateReviewActionRequestDTO,
        current_user: User,
        correlation_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CandidateGovernanceItemDTO:
        """
        Record an authoritative human review decision on an optimization candidate.
        
        Strictly enforces:
        1. Role authorization (Quality Head, Admin, Super Admin, Quality Engineer, Plant Manager)
        2. Infeasible candidates cannot be accepted
        3. Traceable immutable SecurityAuditLog event recording
        """
        # 1. Role Authorization Check
        if not cls._is_user_authorized_for_review(current_user):
            # Log security violation
            try:
                db.add(
                    SecurityAuditLog(
                        actor_user_id=current_user.id,
                        target_user_id=None,
                        event_type="ACCESS_DENIED_UNAUTHORIZED_REVIEW_ACTION",
                        resource_name="AI_MIX_OPTIMIZATION_GOVERNANCE",
                        details={
                            "run_id": run_id,
                            "candidate_id": candidate_id,
                            "requested_action": request_dto.action,
                            "user_roles": [r.role_id for r in current_user.role_assignments],
                        },
                        ip_address=client_ip,
                        user_agent=user_agent or "RecommendationGovernanceService/1.0",
                        created_at=datetime.now(timezone.utc),
                    )
                )
                db.commit()
            except Exception:
                db.rollback()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have authorization to perform human review decisions. Authorized roles: QUALITY_HEAD, ADMIN, SUPER_ADMIN, QUALITY_ENGINEER, PLANT_MANAGER.",
            )

        # 2. Fetch Run and Candidate
        run = db.get(OptimizationRun, run_id)
        if not run or run.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationRun with ID '{run_id}' not found.",
            )

        candidate = db.get(OptimizationCandidate, candidate_id)
        if not candidate or str(candidate.run_id) != str(run.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptimizationCandidate with ID '{candidate_id}' not found in run '{run_id}'.",
            )

        action = request_dto.action.upper().strip()
        if action not in ("ACCEPT", "REJECT", "RESET"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid review action '{request_dto.action}'. Must be one of: ACCEPT, REJECT, RESET.",
            )

        # 3. Infeasible Candidate Quarantine Guard
        if action == "ACCEPT" and not candidate.is_feasible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot accept an engineering infeasible candidate. Infeasible candidates are quarantined for diagnostic analysis only.",
            )

        now = datetime.now(timezone.utc)
        c_eval = dict(candidate.constraint_evaluation_json or {})
        prev_status = c_eval.get("review_status", "PENDING_REVIEW")

        if action == "ACCEPT":
            new_status = "ACCEPTED"
            candidate.is_recommended = True
            c_eval["review_status"] = "ACCEPTED"
            c_eval["reviewed_by_user_id"] = str(current_user.id)
            c_eval["reviewed_by_username"] = current_user.username
            c_eval["reviewed_at"] = now.isoformat()
            c_eval["review_decision_reason"] = request_dto.reason_code
            c_eval["review_comments"] = request_dto.comments
        elif action == "REJECT":
            new_status = "REJECTED"
            candidate.is_recommended = False
            c_eval["review_status"] = "REJECTED"
            c_eval["reviewed_by_user_id"] = str(current_user.id)
            c_eval["reviewed_by_username"] = current_user.username
            c_eval["reviewed_at"] = now.isoformat()
            c_eval["review_decision_reason"] = request_dto.reason_code
            c_eval["review_comments"] = request_dto.comments
        else:  # RESET
            new_status = "PENDING_REVIEW"
            candidate.is_recommended = False
            c_eval["review_status"] = "PENDING_REVIEW"
            c_eval.pop("reviewed_by_user_id", None)
            c_eval.pop("reviewed_by_username", None)
            c_eval.pop("reviewed_at", None)
            c_eval.pop("review_decision_reason", None)
            c_eval.pop("review_comments", None)

        candidate.constraint_evaluation_json = c_eval
        candidate.updated_at = now

        # 4. Immutable Security Audit Trail
        audit_entry = SecurityAuditLog(
            actor_user_id=current_user.id,
            target_user_id=None,
            event_type="OPTIMIZATION_CANDIDATE_REVIEW_DECISION",
            resource_name="AI_MIX_OPTIMIZATION_GOVERNANCE",
            correlation_id=correlation_id,
            details={
                "run_id": str(run.id),
                "candidate_id": str(candidate.id),
                "candidate_identifier": candidate.candidate_identifier,
                "action": action,
                "reason_code": request_dto.reason_code,
                "comments": request_dto.comments,
                "is_feasible": candidate.is_feasible,
                "previous_review_status": prev_status,
                "new_review_status": new_status,
                "plant_code": run.plant_code,
                "recipe_code": run.recipe_code,
            },
            ip_address=client_ip,
            user_agent=user_agent or "RecommendationGovernanceService/1.0",
            created_at=now,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(candidate)

        # 5. Return updated single item governance response
        run_gov = cls.get_run_governance(db=db, run_id=run_id, current_user=current_user)
        for item in run_gov.candidates:
            if item.candidate_id == str(candidate.id):
                return item

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated governance item after review.",
        )
