"""Unit test suite for WS-01.3C Error Code Taxonomy and Error Mapping Contracts."""

from src.contracts.responses import (
    ErrorDetail,
    ErrorResponse,
    get_http_status_for_exception,
    map_exception_to_error_response,
)
from src.exceptions import (
    ErrorCode,
    InvalidBatchStateException,
    EntityNotFoundException,
    QualityDispositionException,
    DatabaseConnectionException,
)


def test_error_code_enum_registry() -> None:
    assert ErrorCode.ACC_BATCH_INVALID_STATE.value == "ACC_BATCH_INVALID_STATE"
    assert ErrorCode.ACC_QA_DISPOSITION_REJECTED.value == "ACC_QA_DISPOSITION_REJECTED"


def test_http_status_mapping() -> None:
    exc1 = InvalidBatchStateException("CREATED", "DELIVERED")
    assert get_http_status_for_exception(exc1) == 400

    exc2 = EntityNotFoundException("Plant", "P-01")
    assert get_http_status_for_exception(exc2) == 404

    exc3 = QualityDispositionException(30.0, 25.0)
    assert get_http_status_for_exception(exc3) == 422

    exc4 = DatabaseConnectionException()
    assert get_http_status_for_exception(exc4) == 503


def test_map_exception_to_error_response() -> None:
    exc = InvalidBatchStateException("CREATED", "DELIVERED", batch_id="B-100")
    resp = map_exception_to_error_response(exc, correlation_id="req-1234")

    assert isinstance(resp, ErrorResponse)
    assert resp.error_code == "ACC_BATCH_INVALID_STATE"
    assert resp.http_status == 400
    assert resp.correlation_id == "req-1234"
    assert resp.metadata["batch_id"] == "B-100"


def test_map_standard_exception_to_error_response() -> None:
    exc = ValueError("Unexpected value")
    resp = map_exception_to_error_response(exc, correlation_id="req-999")

    assert resp.error_code == "ACC_SYS_INTERNAL_ERROR"
    assert resp.http_status == 500
    assert resp.correlation_id == "req-999"
