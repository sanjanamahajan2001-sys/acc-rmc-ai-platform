"""Audit & Governance REST API Router.

Provides secure, paginated, filtered access to enterprise audit logs,
lineage correlation traces, operational compliance metrics, and sanitized CSV exports.
Strictly authorized to SUPER_ADMIN, ADMIN, and QUALITY_HEAD roles.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.schemas.audit import (
    AuditEventItemDTO,
    AuditEventListResponseDTO,
    AuditMetricsDTO,
    AuditCorrelationResponseDTO,
)
from src.security.dependencies import get_db, require_roles
from src.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Governance"])

AUDIT_AUTH_DEPENDENCY = require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")


def _extract_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/events", response_model=AuditEventListResponseDTO)
def list_audit_events(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Global search keyword"),
    module: Optional[str] = Query(None, description="Module filter (AUTH, DATA_INGESTION, MANUAL_ENTRY, QUALITY_QA, USER_ADMIN, SECURITY)"),
    event_type: Optional[str] = Query(None, description="Exact event type filter"),
    severity: Optional[str] = Query(None, description="Severity filter (INFO, WARNING, CRITICAL)"),
    result: Optional[str] = Query(None, description="Result filter (SUCCESS, FAILURE, DENIED, QUARANTINED)"),
    date_from: Optional[str] = Query(None, description="Start date ISO string"),
    date_to: Optional[str] = Query(None, description="End date ISO string"),
    actor_id: Optional[str] = Query(None, description="Actor User GUID filter"),
    correlation_id: Optional[str] = Query(None, description="Correlation trace ID filter"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_desc: bool = Query(True, description="Sort descending"),
    current_user: User = Depends(AUDIT_AUTH_DEPENDENCY),
    db: Session = Depends(get_db),
) -> AuditEventListResponseDTO:
    """Retrieve paginated, filtered audit events with server-side indexing."""
    return AuditService.get_events(
        db=db,
        page=page,
        page_size=page_size,
        q=q,
        module=module,
        event_type=event_type,
        severity=severity,
        result=result,
        date_from=date_from,
        date_to=date_to,
        actor_id=actor_id,
        correlation_id=correlation_id,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get("/metrics", response_model=AuditMetricsDTO)
def get_audit_metrics(
    current_user: User = Depends(AUDIT_AUTH_DEPENDENCY),
    db: Session = Depends(get_db),
) -> AuditMetricsDTO:
    """Retrieve live aggregated compliance and operational activity KPIs."""
    return AuditService.get_metrics(db=db)


@router.get("/correlation/{correlation_id}", response_model=AuditCorrelationResponseDTO)
def get_correlation_trace(
    correlation_id: str,
    current_user: User = Depends(AUDIT_AUTH_DEPENDENCY),
    db: Session = Depends(get_db),
) -> AuditCorrelationResponseDTO:
    """Retrieve end-to-end chronological lifecycle trace for a specific correlation ID."""
    return AuditService.get_correlation_trace(db=db, correlation_id=correlation_id)


@router.get("/events/{event_id}", response_model=AuditEventItemDTO)
def get_audit_event_detail(
    event_id: str,
    current_user: User = Depends(AUDIT_AUTH_DEPENDENCY),
    db: Session = Depends(get_db),
) -> AuditEventItemDTO:
    """Retrieve comprehensive details for a single audit event."""
    event = AuditService.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event '{event_id}' not found.",
        )
    return event


@router.get("/export")
def export_audit_logs(
    request: Request,
    format: str = Query("csv", description="Export format (csv)"),
    q: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    current_user: User = Depends(AUDIT_AUTH_DEPENDENCY),
    db: Session = Depends(get_db),
):
    """Generate and stream sanitized CSV audit logs."""
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    filters = {
        "q": q,
        "module": module,
        "event_type": event_type,
        "severity": severity,
        "result": result,
        "date_from": date_from,
        "date_to": date_to,
        "actor_id": actor_id,
        "correlation_id": correlation_id,
    }

    csv_data = AuditService.export_events_csv(db=db, filters=filters)

    # Self-Audit the export action
    try:
        AuditService.log_event(
            db=db,
            event_type="AUDIT_EXPORT_GENERATED",
            resource_name="SECURITY_AUDIT",
            actor_user_id=current_user.id,
            details={
                "exported_by": current_user.username,
                "format": format,
                "filters_applied": {k: v for k, v in filters.items() if v is not None},
            },
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except Exception:
        pass

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"acc_rmc_audit_export_{timestamp_str}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
