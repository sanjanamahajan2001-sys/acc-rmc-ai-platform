"""Unit test suite for WS-01.4D Immutable Audit Logger Engine."""

import os
from src.logging import (
    AuditEvent,
    AuditEventType,
    bind_log_context,
    clear_log_context,
    get_audit_logger,
    log_audit_event,
)


def test_audit_event_type_taxonomy() -> None:
    assert AuditEventType.USER_LOGIN.value == "USER_LOGIN"
    assert AuditEventType.BATCH_CREATED.value == "BATCH_CREATED"
    assert AuditEventType.PREDICTION_APPROVED.value == "PREDICTION_APPROVED"
    assert AuditEventType.FT7_IMPORTED.value == "FT7_IMPORTED"


def test_log_audit_event_creation() -> None:
    clear_log_context()
    bind_log_context(correlation_id="cid-9999", plant_code="PLANT-K01", user_id="usr-admin")

    event = log_audit_event(
        event_type=AuditEventType.BATCH_CREATED,
        action="CREATE_BATCH_CYCLE",
        resource_type="Batch",
        resource_id="B-100",
        message="Batch created successfully",
        metadata={"mix_grade": "M30"},
    )

    assert isinstance(event, AuditEvent)
    assert event.event_type == "BATCH_CREATED"
    assert event.correlation_id == "cid-9999"
    assert event.plant_code == "PLANT-K01"
    assert event.user_id == "usr-admin"
    assert event.metadata["mix_grade"] == "M30"


def test_audit_log_file_written() -> None:
    audit_file = "/home/sanjana/acc-rmc-ai-platform/runtime/logs/audit/audit.log"

    log_audit_event(
        event_type=AuditEventType.USER_LOGIN,
        action="AUTHENTICATE_USER",
        resource_type="User",
        resource_id="usr-101",
        message="User logged in",
    )

    assert os.path.exists(audit_file) is True
