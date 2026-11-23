"""Unit and Contract Test Suite for WS-03.1 Ingestion DTOs and Schemas."""

from datetime import datetime, timezone
from decimal import Decimal
import json
import unittest
from pydantic import ValidationError
from src.contracts.ingestion import (
    CONTRACT_VERSION,
    BatchIngestionDTO,
    CubeTestIngestionDTO,
    FT7CertificateIngestionDTO,
    IngestionBatchPayloadDTO,
    IngestionResultResponseDTO,
    MaterialConsumptionIngestionDTO,
    ProductionEventIngestionDTO,
    SingleIngestionPayloadDTO,
    SlumpTestIngestionDTO,
    ValidationDiagnosticDTO,
    WeighingLogIngestionDTO,
)


class TestIngestionContracts(unittest.TestCase):
    def test_version_constant(self) -> None:
        self.assertEqual(CONTRACT_VERSION, "1.0.0")

    def test_batch_ingestion_dto_valid_and_invalid(self) -> None:
        valid_batch = BatchIngestionDTO(
            batch_number="BAT-001",
            order_number="ORD-001",
            plant_code="P001",
            recipe_code="M40_REC",
            planned_quantity_m3=Decimal("6.00"),
            actual_quantity_m3=Decimal("5.95"),
        )
        self.assertEqual(valid_batch.batch_number, "BAT-001")
        self.assertEqual(valid_batch.planned_quantity_m3, Decimal("6.00"))

        # Test immutability in Pydantic V2 raises ValidationError with frozen_instance type
        with self.assertRaises(ValidationError) as ctx:
            valid_batch.batch_number = "NEW-BAT"
        self.assertIn("frozen", str(ctx.exception).lower())

        # Test invalid negative quantity
        with self.assertRaises(ValidationError):
            BatchIngestionDTO(
                batch_number="BAT-001",
                order_number="ORD-001",
                plant_code="P001",
                recipe_code="M40_REC",
                planned_quantity_m3=Decimal("-1.00"),
            )

    def test_material_consumption_dto_variance_calculation(self) -> None:
        mat = MaterialConsumptionIngestionDTO(
            material_code="MAT_CEMENT",
            planned_quantity=Decimal("2000.00"),
            actual_quantity=Decimal("1990.00"),
        )
        self.assertEqual(mat.variance_quantity, Decimal("-10.00"))
        self.assertEqual(mat.variance_percentage, Decimal("-0.50"))

    def test_quality_dtos(self) -> None:
        now = datetime.now(timezone.utc)
        slump = SlumpTestIngestionDTO(slump_mm=Decimal("120.00"), test_timestamp=now)
        self.assertEqual(slump.slump_mm, Decimal("120.00"))

        cube = CubeTestIngestionDTO(
            cube_set_number="CS-01",
            age_days=28,
            compressive_strength_mpa=Decimal("45.50"),
            testing_timestamp=now,
        )
        self.assertEqual(cube.age_days, 28)

        ft7 = FT7CertificateIngestionDTO(certificate_number="FT7-100", issued_date=now)
        self.assertEqual(ft7.certificate_number, "FT7-100")

    def test_single_and_batch_payload_dtos(self) -> None:
        now = datetime.now(timezone.utc)
        batch = BatchIngestionDTO(
            batch_number="BAT-002",
            order_number="ORD-002",
            plant_code="P001",
            recipe_code="M30_REC",
            planned_quantity_m3=Decimal("6.00"),
        )
        mat = MaterialConsumptionIngestionDTO(
            material_code="MAT_CEM",
            planned_quantity=Decimal("1500.00"),
            actual_quantity=Decimal("1505.00"),
        )

        payload = SingleIngestionPayloadDTO(batch=batch, material_consumptions=[mat])
        self.assertEqual(payload.batch.batch_number, "BAT-002")
        self.assertEqual(len(payload.material_consumptions), 1)

        batch_payload = IngestionBatchPayloadDTO(
            source_channel="EXCEL_IMPORT",
            payloads=[payload],
        )
        self.assertEqual(batch_payload.source_channel, "EXCEL_IMPORT")
        self.assertEqual(len(batch_payload.payloads), 1)

    def test_serialization_and_deserialization_canonical(self) -> None:
        batch = BatchIngestionDTO(
            batch_number="BAT-SERIAL",
            order_number="ORD-SERIAL",
            plant_code="P001",
            recipe_code="REC_SERIAL",
            planned_quantity_m3=Decimal("12.50"),
        )

        json_str = batch.model_dump_json_canonical()
        data = json.loads(json_str)
        self.assertEqual(data["batch_number"], "BAT-SERIAL")
        self.assertEqual(data["planned_quantity_m3"], "12.50")

        reconstructed = BatchIngestionDTO.model_validate_json(json_str)
        self.assertEqual(reconstructed.batch_number, "BAT-SERIAL")
        self.assertEqual(reconstructed.planned_quantity_m3, Decimal("12.50"))

    def test_response_and_diagnostic_dtos(self) -> None:
        diag = ValidationDiagnosticDTO(
            field_name="slump_mm",
            error_code="RANGE_EXCEEDED",
            message="Slump value exceeds maximum allowed 300mm",
            severity="CRITICAL",
        )
        resp = IngestionResultResponseDTO(
            ingestion_status="QUARANTINED",
            records_processed=1,
            diagnostics=[diag],
        )
        self.assertEqual(resp.ingestion_status, "QUARANTINED")
        self.assertEqual(resp.diagnostics[0].field_name, "slump_mm")


if __name__ == "__main__":
    unittest.main()
