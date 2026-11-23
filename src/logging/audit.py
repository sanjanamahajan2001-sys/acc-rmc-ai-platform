from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
"""Immutable Audit Logger Engine.

This module provides the dedicated `get_audit_logger()` engine writing immutable,
structured security and business audit events exclusively to `runtime/logs/audit/audit.log`.
"""

from enum import Enum
import logging
from logging.handlers import RotatingFileHandler

def _get_default_base_dir() -> str:
    env_dir = os.environ.get("BASE_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir
    # Auto-detect from file location (src/logging/... -> root)
    detected = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.exists(detected):
        return detected
    return "/opt/apps/acc-rmc-ai-platform" if os.path.exists("/opt/apps/acc-rmc-ai-platform") else "/home/sanjana/acc-rmc-ai-platform"

import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import structlog
from src.logging.config import ensure_runtime_log_directories
from src.logging.context import get_log_context
from src.logging.processors import redact_sensitive_data_processor


class AuditEventType(str, Enum):
    """Standardized Immutable Audit Event Taxonomy."""

    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    ROLE_CHANGED = "ROLE_CHANGED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"
    BATCH_CREATED = "BATCH_CREATED"
    BATCH_UPDATED = "BATCH_UPDATED"
    BATCH_DELETED = "BATCH_DELETED"
    BATCH_DISPATCHED = "BATCH_DISPATCHED"
    DELIVERY_CREATED = "DELIVERY_CREATED"
    FT7_IMPORTED = "FT7_IMPORTED"
    LAB_RESULT_IMPORTED = "LAB_RESULT_IMPORTED"
    MIX_CREATED = "MIX_CREATED"
    MIX_UPDATED = "MIX_UPDATED"
    PREDICTION_GENERATED = "PREDICTION_GENERATED"
    PREDICTION_APPROVED = "PREDICTION_APPROVED"
    MODEL_TRAINED = "MODEL_TRAINED"
    MODEL_RETRAINED = "MODEL_RETRAINED"
    MODEL_DEPLOYED = "MODEL_DEPLOYED"
    IMPORT_STARTED = "IMPORT_STARTED"
    IMPORT_COMPLETED = "IMPORT_COMPLETED"
    IMPORT_FAILED = "IMPORT_FAILED"
    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_EXPORTED = "REPORT_EXPORTED"
    SYSTEM_CONFIGURATION_CHANGED = "SYSTEM_CONFIGURATION_CHANGED"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class AuditEvent(BaseModel):
    """Standardized Immutable Audit Event Payload Contract."""

    event_type: str = Field(description="Audit event taxonomy type string.")
    action: str = Field(description="Specific operational or security action description.")
    resource_type: str = Field(description="Target resource type (e.g., 'Batch', 'Model', 'User').")
    resource_id: str = Field(description="Unique identifier of target resource.")
    result: str = Field(default="SUCCESS", description="Execution result ('SUCCESS', 'FAILURE', 'DENIED').")
    message: str = Field(description="Human-readable audit summary.")
    correlation_id: Optional[str] = Field(default=None, description="Trace request identifier.")
    request_id: Optional[str] = Field(default=None, description="HTTP or API request ID.")
    plant_code: Optional[str] = Field(default=None, description="Plant facility code.")
    batch_id: Optional[str] = Field(default=None, description="Batch mixing cycle UUID.")
    challan_no: Optional[str] = Field(default=None, description="Delivery challan number.")
    user_id: Optional[str] = Field(default=None, description="User or operator identity.")
    component: Optional[str] = Field(default="security", description="Component module tag.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual state metadata.")


_AUDIT_LOGGER_INITIALIZED: bool = False
_AUDIT_LOGGER: Optional[structlog.BoundLogger] = None


def get_audit_logger(base_dir: Optional[str] = None) -> structlog.BoundLogger:
    if not base_dir:
        base_dir = _get_default_base_dir()
    """Return the dedicated immutable audit logger writing exclusively to audit.log."""
    global _AUDIT_LOGGER_INITIALIZED, _AUDIT_LOGGER
    if _AUDIT_LOGGER_INITIALIZED and _AUDIT_LOGGER is not None:
        return _AUDIT_LOGGER

    ensure_runtime_log_directories(base_dir=base_dir)

    audit_log_path = os.path.join(base_dir, "runtime", "logs", "audit", "audit.log")
    handler = RotatingFileHandler(
        audit_log_path, maxBytes=20 * 1024 * 1024, backupCount=10, encoding="utf-8"
    )
    handler.setLevel(logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        redact_sensitive_data_processor,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)

    audit_std_logger = logging.getLogger("acc_rmc_audit")
    audit_std_logger.setLevel(logging.INFO)
    audit_std_logger.addHandler(handler)
    audit_std_logger.propagate = False

    _AUDIT_LOGGER = structlog.wrap_logger(
        audit_std_logger,
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    _AUDIT_LOGGER_INITIALIZED = True
    return _AUDIT_LOGGER


def log_audit_event(
    event_type: AuditEventType,
    action: str,
    resource_type: str,
    resource_id: str,
    message: str,
    result: str = "SUCCESS",
    metadata: Optional[Dict[str, Any]] = None,
    base_dir: Optional[str] = None,
) -> AuditEvent:
    """Log an immutable audit event to audit.log incorporating active thread context.

    Args:
        event_type: AuditEventType enum taxonomy.
        action: Specific action performed.
        resource_type: Target resource category.
        resource_id: Target resource identifier.
        message: Human-readable explanation.
        result: Outcome string ('SUCCESS', 'FAILURE', 'DENIED').
        metadata: Optional contextual dictionary.
        base_dir: Platform root directory.

    Returns:
        AuditEvent: The logged immutable audit event instance.
    """
    logger = get_audit_logger(base_dir=base_dir)
    ctx = get_log_context()

    event = AuditEvent(
        event_type=event_type.value,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        message=message,
        correlation_id=ctx.get("correlation_id"),
        request_id=ctx.get("request_id"),
        plant_code=ctx.get("plant_code"),
        batch_id=ctx.get("batch_id"),
        challan_no=ctx.get("challan_no"),
        user_id=ctx.get("user_id"),
        component=ctx.get("component", "audit"),
        metadata=metadata if metadata is not None else {},
    )

    logger.info("audit_event", **event.model_dump())
    return event
