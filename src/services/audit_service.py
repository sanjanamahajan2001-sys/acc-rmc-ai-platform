"""Audit & Governance Service Layer.

Handles secure recording, normalization, querying, metrics aggregation,
and export of platform audit logs with automated secret redaction.
"""

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, desc, asc, or_, and_, not_
from sqlalchemy.orm import Session, joinedload

from src.database.models.user import SecurityAuditLog, User
from src.schemas.audit import (
    ActorInfoDTO,
    TargetInfoDTO,
    AuditEventItemDTO,
    AuditEventListResponseDTO,
    AuditMetricsDTO,
    AuditCorrelationResponseDTO,
)
from src.security.redaction import redact_sensitive_dict, redact_sensitive_string


def map_event_to_module_and_action(event_type: str, resource_name: str) -> Tuple[str, str, str, str]:
    """Derive canonical module, action, severity, and result from event type and resource.
    
    Returns: (module, action, severity, result)
    """
    ev_upper = event_type.upper()
    res_upper = resource_name.upper()

    # Determine Result
    if any(k in ev_upper for k in ["FAILURE", "FAILED", "ERROR", "REJECTED"]):
        result = "FAILURE"
    elif "DENIED" in ev_upper or "FORBIDDEN" in ev_upper:
        result = "DENIED"
    elif "LOCKED" in ev_upper:
        result = "FAILURE"
    elif "CONFLICT" in ev_upper or "QUARANTINED" in ev_upper:
        result = "QUARANTINED"
    else:
        result = "SUCCESS"

    # Determine Severity
    if result in ["DENIED", "QUARANTINED"] or "DELETE" in ev_upper or "RESET" in ev_upper or "LOCKED" in ev_upper:
        severity = "CRITICAL" if ("DELETE" in ev_upper or "RESET" in ev_upper) else "WARNING"
    elif result == "FAILURE":
        severity = "WARNING"
    else:
        severity = "INFO"

    # Determine Module & Action
    if "SECURITY" in res_upper or "RBAC" in res_upper or "DENIED" in ev_upper or "EXPORT" in ev_upper:
        module = "SECURITY"
        if "EXPORT" in ev_upper:
            action = "EXPORT"
        elif "DENIED" in ev_upper:
            action = "REJECT"
        else:
            action = "GOVERN"
    elif "USER" in ev_upper or "USER" in res_upper or "ROLE" in ev_upper:
        module = "USER_ADMIN"
        if "CREATE" in ev_upper:
            action = "CREATE"
        elif "DELETE" in ev_upper:
            action = "DELETE"
        elif "ASSIGN" in ev_upper or "REVOKE" in ev_upper or "UPDATE" in ev_upper or "STATUS" in ev_upper:
            action = "UPDATE"
        elif "RESET" in ev_upper:
            action = "RESET"
        else:
            action = "MANAGE"
    elif "INGESTION" in ev_upper or "DATASET" in ev_upper or "IMPORT" in res_upper or "EXCEL" in res_upper:
        module = "DATA_INGESTION"
        if "CREATE" in ev_upper or "START" in ev_upper:
            action = "CREATE"
        elif "MAP" in ev_upper:
            action = "VALIDATE"
        elif "PERSIST" in ev_upper:
            action = "IMPORT"
        elif "RESET" in ev_upper:
            action = "DELETE"
        else:
            action = "INGEST"
    elif "MANUAL" in ev_upper or "BATCH" in ev_upper or "PRODUCTION" in res_upper:
        module = "MANUAL_ENTRY"
        if "DRAFT" in ev_upper or "CREATE" in ev_upper:
            action = "CREATE"
        elif "MOISTURE" in ev_upper or "ADJUST" in ev_upper:
            action = "OVERRIDE"
        elif "COMMIT" in ev_upper:
            action = "CREATE"
        else:
            action = "EXECUTE"
    elif "QA" in ev_upper or "LAB" in ev_upper or "CUBE" in ev_upper or "SLUMP" in ev_upper or "QUALITY" in res_upper:
        module = "QUALITY_QA"
        if "REGISTER" in ev_upper or "CREATE" in ev_upper:
            action = "CREATE"
        elif "TEST" in ev_upper or "BREAK" in ev_upper:
            action = "VALIDATE"
        else:
            action = "INSPECT"
    elif "PLANT" in ev_upper or "RECIPE" in ev_upper or "CUSTOMER" in ev_upper or "MASTER" in res_upper:
        module = "MASTER_DATA"
        if "CREATE" in ev_upper:
            action = "CREATE"
        elif "DELETE" in ev_upper:
            action = "DELETE"
        else:
            action = "UPDATE"
    elif "ML" in ev_upper or "MODEL" in ev_upper or "TRAINING" in ev_upper or "INFERENCE" in ev_upper or "ML" in res_upper or "MODEL" in res_upper:
        module = "MODEL_TRAINING"
        if "ACTIVAT" in ev_upper:
            action = "PROMOTE"
        elif "ROLLBACK" in ev_upper or "REVERT" in ev_upper:
            action = "ROLLBACK"
        elif "REQUEST" in ev_upper or "TRAIN" in ev_upper or "JOB" in ev_upper:
            action = "TRAIN"
        elif "INFER" in ev_upper or "PREDICT" in ev_upper:
            action = "INFER"
        else:
            action = "EXECUTE"
    elif "SETTING" in ev_upper or "SETTING" in res_upper or "ENGINEERING" in ev_upper or "ENGINEERING" in res_upper or "CALIBRE" in ev_upper or "SCHEMA_EXPORT" in ev_upper or "DATABASE_PREVIEW" in ev_upper:
        module = "SETTINGS"
        if "UPDATE" in ev_upper or "CHANGE" in ev_upper:
            action = "UPDATE"
        elif "RESET" in ev_upper:
            action = "RESET"
        elif "EXPORT" in ev_upper:
            action = "EXPORT"
        else:
            action = "CONFIGURE"
    elif "OPTIMIZ" in ev_upper or "OPTIMIZ" in res_upper:
        module = "AI_MIX_OPTIMIZATION"
        if "TRIGGER" in ev_upper or "RUN" in ev_upper or "START" in ev_upper:
            action = "OPERATE"
        elif "EVALUAT" in ev_upper:
            action = "OPERATE"
        elif "APPROV" in ev_upper or "DECISION" in ev_upper:
            action = "APPROVE"
        elif "REJECT" in ev_upper:
            action = "REJECT"
        else:
            action = "OPTIMIZE"
    elif "LOGIN" in ev_upper or "LOGOUT" in ev_upper or "AUTH" in res_upper or "PASSWORD" in ev_upper:
        module = "AUTH"
        if "LOGIN" in ev_upper:
            action = "LOGIN"
        elif "LOGOUT" in ev_upper:
            action = "LOGOUT"
        elif "PASSWORD" in ev_upper:
            action = "UPDATE"
        else:
            action = "AUTHENTICATE"
    else:
        module = res_upper if res_upper else "SYSTEM"
        action = "OPERATE"
    return module, action, severity, result


class AuditService:
    """Enterprise service for logging and querying platform audit events."""

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        resource_name: str,
        actor_user_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SecurityAuditLog:
        """Safely record a sanitized audit event to usr_audit_logs."""
        clean_details = redact_sensitive_dict(details or {})
        clean_ip = redact_sensitive_string(ip_address) if ip_address else None
        clean_ua = (user_agent[:500] if user_agent else None)

        audit_entry = SecurityAuditLog(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            event_type=event_type,
            resource_name=resource_name,
            correlation_id=correlation_id,
            details=clean_details,
            ip_address=clean_ip,
            user_agent=clean_ua,
        )
        db.add(audit_entry)
        try:
            db.commit()
            db.refresh(audit_entry)
        except Exception:
            db.rollback()
            raise
        return audit_entry

    @staticmethod
    def to_dto(log: SecurityAuditLog) -> AuditEventItemDTO:
        """Transform ORM SecurityAuditLog entity into safe canonical DTO."""
        module, action, severity, result = map_event_to_module_and_action(log.event_type, log.resource_name)

        # Actor resolution
        actor_username = "SYSTEM"
        actor_email = None
        actor_fullname = None
        actor_roles: List[str] = []

        if log.actor:
            actor_username = log.actor.username
            actor_email = log.actor.email
            actor_fullname = log.actor.full_name
            actor_roles = [r.role_id for r in log.actor.role_assignments]
        elif log.details and isinstance(log.details, dict):
            if "actor_username" in log.details:
                actor_username = str(log.details["actor_username"])
            elif "username" in log.details and module in ["AUTH", "USER_ADMIN"]:
                actor_username = str(log.details["username"])
            elif "deleted_by" in log.details:
                actor_username = str(log.details["deleted_by"])
            elif "operator_id" in log.details:
                actor_username = str(log.details["operator_id"])

        actor_dto = ActorInfoDTO(
            user_id=str(log.actor_user_id) if log.actor_user_id else None,
            username=actor_username,
            email=actor_email,
            full_name=actor_fullname,
            roles=actor_roles,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
        )

        # Target resolution
        target_entity = "SYSTEM"
        target_id = "GLOBAL"
        target_name = None

        if log.target:
            target_entity = "User"
            target_id = str(log.target.id)
            target_name = log.target.username
        elif log.details and isinstance(log.details, dict):
            if "target_username" in log.details:
                target_entity = "User"
                target_name = str(log.details["target_username"])
                target_id = target_name
            elif "deleted_username" in log.details:
                target_entity = "User"
                target_name = str(log.details["deleted_username"])
                target_id = target_name
            elif "batch_number" in log.details:
                target_entity = "Batch"
                target_id = str(log.details["batch_number"])
                target_name = target_id
            elif "dataset_id" in log.details:
                target_entity = "Dataset"
                target_id = str(log.details["dataset_id"])
                target_name = target_id
            elif "session_id" in log.details:
                target_entity = "IngestionSession"
                target_id = str(log.details["session_id"])
                target_name = target_id
            elif "recipe_code" in log.details:
                target_entity = "Recipe"
                target_id = str(log.details["recipe_code"])
                target_name = target_id
            elif "plant_code" in log.details:
                target_entity = "Plant"
                target_id = str(log.details["plant_code"])
                target_name = target_id
            elif "sample_number" in log.details:
                target_entity = "LabSample"
                target_id = str(log.details["sample_number"])
                target_name = target_id
            elif "model_name" in log.details or "new_active_version" in log.details:
                target_entity = "MLModel"
                target_id = str(log.details.get("new_active_version") or log.details.get("restored_active_version") or log.details.get("model_id") or "ML_MODEL")
                target_name = str(log.details.get("model_name") or "Concrete ML Model")
            elif "job_id" in log.details or "dataset_fingerprint" in log.details:
                target_entity = "MLTrainingJob"
                target_id = str(log.details.get("job_id") or log.details.get("dataset_fingerprint") or "ML_TRAINING")
                target_name = "Model Training Run"
            elif "standard_code" in log.details or (isinstance(log.details, dict) and "CALIBRE" in str(log.details.get("action", ""))):
                target_entity = "EngineeringSettings"
                target_id = str(log.details.get("standard_code") or "IS 456 / IS 10262")
                target_name = "Engineering Standard & Calibre" 

        target_dto = TargetInfoDTO(
            entity_type=target_entity,
            entity_id=target_id,
            entity_name=target_name,
        )

        clean_details = redact_sensitive_dict(log.details or {})

        return AuditEventItemDTO(
            id=str(log.id),
            timestamp=log.created_at,
            module=module,
            event_type=log.event_type,
            action=action,
            severity=severity,
            result=result,
            actor=actor_dto,
            target=target_dto,
            correlation_id=log.correlation_id,
            details=clean_details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
        )

    @staticmethod
    def get_events(
        db: Session,
        page: int = 1,
        page_size: int = 25,
        q: Optional[str] = None,
        module: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        result: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> AuditEventListResponseDTO:
        """Query paginated and filtered audit events."""
        query = db.query(SecurityAuditLog).options(
            joinedload(SecurityAuditLog.actor).joinedload(User.role_assignments),
            joinedload(SecurityAuditLog.target),
        )

        # Filters
        if q:
            term = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    SecurityAuditLog.event_type.ilike(term),
                    SecurityAuditLog.resource_name.ilike(term),
                    SecurityAuditLog.correlation_id.ilike(term),
                    SecurityAuditLog.ip_address.ilike(term),
                )
            )

        if event_type:
            query = query.filter(SecurityAuditLog.event_type == event_type.strip())

        if correlation_id:
            query = query.filter(SecurityAuditLog.correlation_id == correlation_id.strip())

        if actor_id:
            query = query.filter(SecurityAuditLog.actor_user_id == actor_id.strip())

        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                query = query.filter(SecurityAuditLog.created_at >= dt_from)
            except Exception:
                pass

        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                query = query.filter(SecurityAuditLog.created_at <= dt_to)
            except Exception:
                pass

        # Module Filter (SQL level)
        if module:
            mod_up = module.strip().upper()
            if mod_up == "AUTH":
                query = query.filter(
                    and_(
                        or_(
                            SecurityAuditLog.event_type.ilike("%LOGIN%"),
                            SecurityAuditLog.event_type.ilike("%LOGOUT%"),
                            SecurityAuditLog.event_type.ilike("%PASSWORD%"),
                            SecurityAuditLog.resource_name.ilike("%AUTH%"),
                        ),
                        not_(SecurityAuditLog.event_type.ilike("%DENIED%")),
                        not_(SecurityAuditLog.resource_name.ilike("%RBAC%")),
                        not_(SecurityAuditLog.resource_name.ilike("%SECURITY%")),
                    )
                )
            elif mod_up == "USER_ADMIN":
                query = query.filter(
                    and_(
                        or_(
                            SecurityAuditLog.resource_name.ilike("%USER%"),
                            SecurityAuditLog.event_type.ilike("%USER%"),
                            SecurityAuditLog.event_type.ilike("%ROLE%"),
                        ),
                        not_(SecurityAuditLog.event_type.ilike("%DENIED%")),
                        not_(SecurityAuditLog.resource_name.ilike("%RBAC%")),
                    )
                )
            elif mod_up == "DATA_INGESTION":
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%INGEST%"),
                        SecurityAuditLog.event_type.ilike("%INGEST%"),
                        SecurityAuditLog.event_type.ilike("%DATASET%"),
                        SecurityAuditLog.event_type.ilike("%IMPORT%"),
                    )
                )
            elif mod_up == "MANUAL_ENTRY":
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%MANUAL%"),
                        SecurityAuditLog.event_type.ilike("%MANUAL%"),
                        SecurityAuditLog.event_type.ilike("%BATCH%"),
                        SecurityAuditLog.resource_name.ilike("%PRODUCTION%"),
                    )
                )
            elif mod_up == "QUALITY_QA":
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%QA%"),
                        SecurityAuditLog.resource_name.ilike("%LAB%"),
                        SecurityAuditLog.event_type.ilike("%CUBE%"),
                        SecurityAuditLog.event_type.ilike("%SLUMP%"),
                    )
                )
            elif mod_up == "MASTER_DATA":
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%MASTER%"),
                        SecurityAuditLog.event_type.ilike("%PLANT%"),
                        SecurityAuditLog.event_type.ilike("%RECIPE%"),
                        SecurityAuditLog.event_type.ilike("%CUSTOMER%"),
                    )
                )
            elif mod_up in ["MODEL_TRAINING", "ML_TRAINING", "ML_MODEL_REGISTRY", "ML_TRAINING_JOB"]:
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%ML%"),
                        SecurityAuditLog.resource_name.ilike("%MODEL%"),
                        SecurityAuditLog.event_type.ilike("%ML%"),
                        SecurityAuditLog.event_type.ilike("%MODEL%"),
                        SecurityAuditLog.event_type.ilike("%TRAIN%"),
                    )
                )
            elif mod_up in ["SETTINGS", "SETTINGS_GOVERNANCE", "CALIBRE", "ENGINEERING"]:
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%SETTING%"),
                        SecurityAuditLog.resource_name.ilike("%ENGINEERING%"),
                        SecurityAuditLog.resource_name.ilike("%CALIBRE%"),
                        SecurityAuditLog.event_type.ilike("%SETTING%"),
                        SecurityAuditLog.event_type.ilike("%ENGINEERING%"),
                        SecurityAuditLog.event_type.ilike("%CALIBRE%"),
                        SecurityAuditLog.event_type.ilike("%SCHEMA_EXPORT%"),
                        SecurityAuditLog.event_type.ilike("%DATABASE_PREVIEW%"),
                    )
                )
            elif mod_up in ["AI_MIX_OPTIMIZATION", "OPTIMIZATION", "MIX_OPTIMIZATION"]:
                query = query.filter(
                    and_(
                        or_(
                            SecurityAuditLog.resource_name.ilike("%OPTIMIZ%"),
                            SecurityAuditLog.event_type.ilike("%OPTIMIZ%"),
                        ),
                        not_(SecurityAuditLog.event_type.ilike("%DENIED%")),
                        not_(SecurityAuditLog.event_type.ilike("%FORBIDDEN%")),
                    )
                )
            elif mod_up == "SECURITY":
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike("%SECURITY%"),
                        SecurityAuditLog.resource_name.ilike("%RBAC%"),
                        SecurityAuditLog.event_type.ilike("%DENIED%"),
                        SecurityAuditLog.event_type.ilike("%EXPORT%"),
                    )
                )
            else:
                query = query.filter(
                    or_(
                        SecurityAuditLog.resource_name.ilike(f"%{mod_up}%"),
                        SecurityAuditLog.event_type.ilike(f"%{mod_up}%"),
                    )
                )

        # Result Filter (SQL level)
        if result:
            res_up = result.strip().upper()
            if res_up == "SUCCESS":
                query = query.filter(
                    and_(
                        not_(SecurityAuditLog.event_type.ilike("%FAIL%")),
                        not_(SecurityAuditLog.event_type.ilike("%DENIED%")),
                        not_(SecurityAuditLog.event_type.ilike("%LOCKED%")),
                        not_(SecurityAuditLog.event_type.ilike("%CONFLICT%")),
                        not_(SecurityAuditLog.event_type.ilike("%ERROR%")),
                    )
                )
            elif res_up == "FAILURE":
                query = query.filter(
                    or_(
                        SecurityAuditLog.event_type.ilike("%FAIL%"),
                        SecurityAuditLog.event_type.ilike("%ERROR%"),
                        SecurityAuditLog.event_type.ilike("%LOCKED%"),
                    )
                )
            elif res_up == "DENIED":
                query = query.filter(
                    or_(
                        SecurityAuditLog.event_type.ilike("%DENIED%"),
                        SecurityAuditLog.event_type.ilike("%FORBIDDEN%"),
                    )
                )
            elif res_up == "QUARANTINED":
                query = query.filter(
                    or_(
                        SecurityAuditLog.event_type.ilike("%CONFLICT%"),
                        SecurityAuditLog.event_type.ilike("%QUARANTINED%"),
                    )
                )

        # Total count after all SQL filters
        total = query.count()

        # Sorting
        sort_column = getattr(SecurityAuditLog, sort_by, SecurityAuditLog.created_at)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items = [AuditService.to_dto(r) for r in records]

        total_pages = max(1, (total + page_size - 1) // page_size)

        return AuditEventListResponseDTO(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_event_by_id(db: Session, event_id: str) -> Optional[AuditEventItemDTO]:
        """Fetch a single audit event by its GUID."""
        record = (
            db.query(SecurityAuditLog)
            .options(
                joinedload(SecurityAuditLog.actor).joinedload(User.role_assignments),
                joinedload(SecurityAuditLog.target),
            )
            .filter(SecurityAuditLog.id == event_id)
            .first()
        )
        if not record:
            return None
        return AuditService.to_dto(record)

    @staticmethod
    def get_metrics(db: Session) -> AuditMetricsDTO:
        """Aggregate high-level audit and compliance KPIs."""
        total = db.query(SecurityAuditLog).count()

        # 24h count
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        last_24h = db.query(SecurityAuditLog).filter(SecurityAuditLog.created_at >= cutoff_24h).count()

        # Denied
        denied = db.query(SecurityAuditLog).filter(
            or_(
                SecurityAuditLog.event_type.ilike("%DENIED%"),
                SecurityAuditLog.event_type.ilike("%FORBIDDEN%"),
            )
        ).count()

        # Failed
        failed = db.query(SecurityAuditLog).filter(
            or_(
                SecurityAuditLog.event_type.ilike("%FAILURE%"),
                SecurityAuditLog.event_type.ilike("%FAILED%"),
                SecurityAuditLog.event_type.ilike("%ERROR%"),
                SecurityAuditLog.event_type.ilike("%LOCKED%"),
            )
        ).count()

        successful = max(0, total - (failed + denied))

        # Module distribution
        modules: Dict[str, int] = {
            "AUTH": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.event_type.ilike("%LOGIN%"), SecurityAuditLog.event_type.ilike("%LOGOUT%"), SecurityAuditLog.event_type.ilike("%PASSWORD%"))).count(),
            "USER_ADMIN": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%USER%"), SecurityAuditLog.event_type.ilike("%USER%"), SecurityAuditLog.event_type.ilike("%ROLE%"))).count(),
            "DATA_INGESTION": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%INGEST%"), SecurityAuditLog.event_type.ilike("%INGEST%"), SecurityAuditLog.event_type.ilike("%DATASET%"))).count(),
            "MANUAL_ENTRY": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%MANUAL%"), SecurityAuditLog.event_type.ilike("%MANUAL%"), SecurityAuditLog.event_type.ilike("%BATCH%"))).count(),
            "QUALITY_QA": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%QA%"), SecurityAuditLog.resource_name.ilike("%LAB%"), SecurityAuditLog.event_type.ilike("%CUBE%"))).count(),
            "MODEL_TRAINING": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%ML%"), SecurityAuditLog.resource_name.ilike("%MODEL%"), SecurityAuditLog.event_type.ilike("%ML%"), SecurityAuditLog.event_type.ilike("%MODEL%"))).count(),
            "AI_MIX_OPTIMIZATION": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%OPTIMIZ%"), SecurityAuditLog.event_type.ilike("%OPTIMIZ%"))).count(),
            "SETTINGS": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%SETTING%"), SecurityAuditLog.resource_name.ilike("%ENGINEERING%"), SecurityAuditLog.event_type.ilike("%SETTING%"), SecurityAuditLog.event_type.ilike("%SCHEMA_EXPORT%"), SecurityAuditLog.event_type.ilike("%DATABASE_PREVIEW%"))).count(),
            "SECURITY": db.query(SecurityAuditLog).filter(or_(SecurityAuditLog.resource_name.ilike("%SECURITY%"), SecurityAuditLog.resource_name.ilike("%RBAC%"), SecurityAuditLog.event_type.ilike("%DENIED%"))).count(),
        }

        return AuditMetricsDTO(
            total_events=total,
            successful_events=successful,
            failed_events=failed,
            denied_events=denied,
            events_last_24h=last_24h,
            module_breakdown=modules,
        )

    @staticmethod
    def get_correlation_trace(db: Session, correlation_id: str) -> AuditCorrelationResponseDTO:
        """Fetch all audit events associated with a specific correlation_id in chronological order."""
        records = (
            db.query(SecurityAuditLog)
            .options(
                joinedload(SecurityAuditLog.actor).joinedload(User.role_assignments),
                joinedload(SecurityAuditLog.target),
            )
            .filter(SecurityAuditLog.correlation_id == correlation_id.strip())
            .order_by(asc(SecurityAuditLog.created_at))
            .all()
        )
        items = [AuditService.to_dto(r) for r in records]
        return AuditCorrelationResponseDTO(
            correlation_id=correlation_id,
            total_events=len(items),
            events=items,
        )

    @staticmethod
    def export_events_csv(db: Session, filters: Dict[str, Any]) -> str:
        """Generate sanitized CSV audit log export."""
        res = AuditService.get_events(db, page=1, page_size=1000, **filters)
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Event ID",
            "Timestamp (UTC)",
            "Module",
            "Event Type",
            "Action",
            "Severity",
            "Result",
            "Actor Username",
            "Actor Roles",
            "Target Type",
            "Target ID",
            "Correlation ID",
            "Client IP",
            "Details Summary",
        ])

        for item in res.items:
            details_str = json.dumps(item.details) if item.details else ""
            roles_str = ",".join(item.actor.roles) if item.actor.roles else ""
            writer.writerow([
                item.id,
                item.timestamp.isoformat() if hasattr(item.timestamp, "isoformat") else str(item.timestamp),
                item.module,
                item.event_type,
                item.action,
                item.severity,
                item.result,
                item.actor.username,
                roles_str,
                item.target.entity_type,
                item.target.entity_id,
                item.correlation_id or "",
                item.ip_address or "",
                details_str[:200],  # truncate long JSON for CSV readability
            ])

        return output.getvalue()
