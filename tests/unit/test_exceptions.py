"""Unit test suite for WS-01.3A Core Base & Domain Exception Hierarchy."""

from src.exceptions import (
    ACCRMCBaseException,
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    InvalidBatchStateException,
    QualityDispositionException,
    RecipeComplianceException,
)


def test_base_exception_instantiation() -> None:
    exc = ACCRMCBaseException(
        message="System failure",
        error_code="ACC_SYS_TEST",
        details=[{"field": "db", "issue": "timeout"}],
        metadata={"node": "worker-1"},
    )
    assert isinstance(exc, Exception)
    assert exc.message == "System failure"
    assert exc.error_code == "ACC_SYS_TEST"
    assert exc.details[0]["field"] == "db"
    assert exc.metadata["node"] == "worker-1"
    assert str(exc) == "[ACC_SYS_TEST] System failure"
    assert exc.to_dict()["error_code"] == "ACC_SYS_TEST"


def test_invalid_batch_state_exception() -> None:
    exc = InvalidBatchStateException(current_state="CREATED", target_state="DELIVERED", batch_id="B-100")
    assert isinstance(exc, DomainException)
    assert isinstance(exc, ACCRMCBaseException)
    assert exc.error_code == "ACC_BATCH_INVALID_STATE"
    assert "Invalid batch state transition" in exc.message
    assert exc.metadata["current_state"] == "CREATED"
    assert exc.metadata["target_state"] == "DELIVERED"
    assert exc.metadata["batch_id"] == "B-100"


def test_quality_disposition_exception() -> None:
    exc = QualityDispositionException(characteristic_strength_mpa=30.0, actual_strength_mpa=26.5, specimen_ref="X257")
    assert isinstance(exc, DomainException)
    assert exc.error_code == "ACC_QA_DISPOSITION_REJECTED"
    assert exc.metadata["characteristic_strength_mpa"] == 30.0
    assert exc.metadata["actual_strength_mpa"] == 26.5
    assert exc.metadata["specimen_ref"] == "X257"


def test_recipe_compliance_exception() -> None:
    exc = RecipeComplianceException(material_type="OPC", target_kg=300.0, actual_kg=320.0, tolerance_pct=1.0)
    assert isinstance(exc, DomainException)
    assert exc.error_code == "ACC_BATCH_DOSING_VARIANCE_EXCEEDED"
    assert exc.metadata["material_type"] == "OPC"
    assert exc.metadata["tolerance_pct"] == 1.0


def test_duplicate_entity_exception() -> None:
    exc = DuplicateEntityException(entity_name="DeliveryChallan", key_name="challan_no", key_value="1749")
    assert isinstance(exc, DomainException)
    assert exc.error_code == "ACC_BATCH_DUPLICATE_CHALLAN"
    assert exc.metadata["key_value"] == "1749"


def test_entity_not_found_exception() -> None:
    exc = EntityNotFoundException(entity_name="Plant", identifier="P-01")
    assert isinstance(exc, DomainException)
    assert exc.error_code == "ACC_BATCH_NOT_FOUND"
    assert exc.metadata["identifier"] == "P-01"
