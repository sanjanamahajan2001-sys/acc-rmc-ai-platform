"""WS-03.6 Phase 1.5 Fix Group 1 — Dedicated Source Contract & DTO Reconciliation Tests."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
from src.contracts.ingestion.quality import (
    CubeTestIngestionDTO,
    IndividualCubeSpecimenDTO,
    SlumpTestIngestionDTO,
    FT7CertificateIngestionDTO
)
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.contracts.ingestion.batch import BatchIngestionDTO


class TestWS036Phase15FixGroup1(unittest.TestCase):
    """Test suite verifying Fix Group 1 DTO additions, backward compatibility, and validation rules."""

    # --- 1. Material Consumption DTO Tests ---
    def test_01_material_dto_backward_compatibility(self):
        """Verify existing MaterialConsumptionIngestionDTO remains backward compatible with default fields."""
        dto = MaterialConsumptionIngestionDTO(
            material_code="CEMENT",
            planned_quantity=Decimal("320.00"),
            actual_quantity=Decimal("320.00")
        )
        self.assertEqual(dto.material_code, "CEMENT")
        self.assertIsNone(dto.source_material_code)
        self.assertIsNone(dto.moisture_percentage)
        self.assertIsNone(dto.absorption_percentage)
        self.assertIsNone(dto.moisture_correction_kg)
        self.assertEqual(dto.variance_quantity, Decimal("0.00"))

    def test_02_material_dto_accepts_reconciled_fields(self):
        """Verify MaterialConsumptionIngestionDTO accepts source_material_code, absorption_percentage, and correction."""
        dto = MaterialConsumptionIngestionDTO(
            material_code="CEMENT",
            source_material_code="CEMENT 1 (OPC 53)",
            planned_quantity=Decimal("300.00"),
            actual_quantity=Decimal("306.00"),
            moisture_percentage=Decimal("2.50"),
            absorption_percentage=Decimal("0.50"),
            moisture_correction_kg=Decimal("6.00")
        )
        self.assertEqual(dto.source_material_code, "CEMENT 1 (OPC 53)")
        self.assertEqual(dto.moisture_percentage, Decimal("2.50"))
        self.assertEqual(dto.absorption_percentage, Decimal("0.50"))
        self.assertEqual(dto.moisture_correction_kg, Decimal("6.00"))
        self.assertEqual(dto.variance_quantity, Decimal("6.00"))
        self.assertEqual(dto.variance_percentage, Decimal("2.00"))

    def test_03_material_dto_rejects_invalid_percentages(self):
        """Verify absorption_percentage rejects negative or >100 values."""
        with self.assertRaises(ValueError):
            MaterialConsumptionIngestionDTO(
                material_code="SAND",
                planned_quantity=Decimal("700.00"),
                actual_quantity=Decimal("700.00"),
                absorption_percentage=Decimal("-1.00")
            )
        with self.assertRaises(ValueError):
            MaterialConsumptionIngestionDTO(
                material_code="SAND",
                planned_quantity=Decimal("700.00"),
                actual_quantity=Decimal("700.00"),
                absorption_percentage=Decimal("105.00")
            )

    # --- 2. Individual Cube Specimen DTO Tests ---
    def test_04_individual_cube_specimen_dto_preserves_raw_fields(self):
        """Verify IndividualCubeSpecimenDTO preserves raw specimen physical facts exactly."""
        now_utc = datetime.now(timezone.utc)
        specimen = IndividualCubeSpecimenDTO(
            mould_identifier="MOULD-2026-01-A",
            casting_timestamp=now_utc,
            testing_timestamp=now_utc,
            age_days=7,
            specimen_condition="SATURATED",
            saturated_mass_kg=Decimal("8.250"),
            mass_in_water_kg=Decimal("4.950"),
            calculated_volume_m3=Decimal("0.003375"),
            failure_load_kn=Decimal("450.50"),
            source_compressive_strength_mpa=Decimal("52.50"),
            calculated_compressive_strength_mpa=Decimal("52.53"),
            failure_mode="NORMAL_FLAT",
            tested_by_user="Technician Ramesh"
        )
        self.assertEqual(specimen.mould_identifier, "MOULD-2026-01-A")
        self.assertEqual(specimen.saturated_mass_kg, Decimal("8.250"))
        self.assertEqual(specimen.mass_in_water_kg, Decimal("4.950"))
        self.assertEqual(specimen.calculated_volume_m3, Decimal("0.003375"))
        self.assertEqual(specimen.failure_load_kn, Decimal("450.50"))
        self.assertEqual(specimen.source_compressive_strength_mpa, Decimal("52.50"))
        self.assertEqual(specimen.calculated_compressive_strength_mpa, Decimal("52.53"))
        self.assertEqual(specimen.compressive_strength_mpa, Decimal("52.50"))
        self.assertEqual(specimen.specimen_condition, "SATURATED")

    def test_05_individual_cube_specimen_rejects_negative_mass_and_load(self):
        """Verify IndividualCubeSpecimenDTO rejects negative physical measurements."""
        now_utc = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            IndividualCubeSpecimenDTO(
                mould_identifier="MOULD-FAIL",
                testing_timestamp=now_utc,
                age_days=28,
                source_compressive_strength_mpa=Decimal("40.00"),
                saturated_mass_kg=Decimal("-5.00")
            )
        with self.assertRaises(ValueError):
            IndividualCubeSpecimenDTO(
                mould_identifier="MOULD-FAIL",
                testing_timestamp=now_utc,
                age_days=28,
                source_compressive_strength_mpa=Decimal("40.00"),
                failure_load_kn=Decimal("-10.00")
            )


    # --- 3. Six-Cube Specimen Model Array Tests ---
    def test_06_cube_test_dto_accepts_six_specimens(self):
        """Verify CubeTestIngestionDTO accepts 3 x 7D and 3 x 28D individual cube specimen arrays."""
        now_utc = datetime.now(timezone.utc)
        
        cubes_7d = [
            IndividualCubeSpecimenDTO(
                mould_identifier=f"MOULD-7D-0{i}",
                testing_timestamp=now_utc,
                age_days=7,
                source_compressive_strength_mpa=Decimal("35.00") + Decimal(str(i)),
                failure_load_kn=Decimal("300.00")
            )
            for i in range(1, 4)
        ]
        
        cubes_28d = [
            IndividualCubeSpecimenDTO(
                mould_identifier=f"MOULD-28D-0{i}",
                testing_timestamp=now_utc,
                age_days=28,
                source_compressive_strength_mpa=Decimal("50.00") + Decimal(str(i)),
                failure_load_kn=Decimal("450.00")
            )
            for i in range(1, 4)
        ]

        set_7d_dto = CubeTestIngestionDTO(
            cube_set_number="QC-SET-7D-001",
            age_days=7,
            compressive_strength_mpa=Decimal("36.00"),
            testing_timestamp=now_utc,
            cube_specimens=cubes_7d
        )
        set_28d_dto = CubeTestIngestionDTO(
            cube_set_number="QC-SET-28D-001",
            age_days=28,
            compressive_strength_mpa=Decimal("52.00"),
            testing_timestamp=now_utc,
            cube_specimens=cubes_28d
        )

        self.assertIsNotNone(set_7d_dto.cube_specimens)
        self.assertEqual(len(set_7d_dto.cube_specimens), 3)
        self.assertEqual(set_7d_dto.cube_specimens[0].mould_identifier, "MOULD-7D-01")

        self.assertIsNotNone(set_28d_dto.cube_specimens)
        self.assertEqual(len(set_28d_dto.cube_specimens), 3)
        self.assertEqual(set_28d_dto.cube_specimens[2].mould_identifier, "MOULD-28D-03")

    def test_07_single_ingestion_payload_integration(self):
        """Verify SingleIngestionPayloadDTO incorporates reconciled material and quality DTOs without breaking schema."""
        now_utc = datetime.now(timezone.utc)
        payload = SingleIngestionPayloadDTO(
            batch=BatchIngestionDTO(
                batch_number="BATCH-RECON-001",
                order_number="ORD-MANUAL-01",
                plant_code="PLANT-MUMBAI-01",
                recipe_code="M40_VW_UT_ISOLATED",
                planned_quantity_m3=6.0
            ),
            material_consumptions=[
                MaterialConsumptionIngestionDTO(
                    material_code="CEMENT",
                    source_material_code="CEMENT 1",
                    planned_quantity=Decimal("320.00"),
                    actual_quantity=Decimal("320.00"),
                    moisture_percentage=Decimal("0.00"),
                    absorption_percentage=Decimal("0.50")
                )
            ],
            cube_tests=[
                CubeTestIngestionDTO(
                    cube_set_number="QC-CUBE-SET-001",
                    age_days=28,
                    compressive_strength_mpa=Decimal("52.50"),
                    testing_timestamp=now_utc,
                    cube_specimens=[
                        IndividualCubeSpecimenDTO(
                            mould_identifier="CUBE-SPECIMEN-1",
                            testing_timestamp=now_utc,
                            age_days=28,
                            source_compressive_strength_mpa=Decimal("52.50")
                        )
                    ]
                )
            ]
        )
        self.assertEqual(payload.material_consumptions[0].source_material_code, "CEMENT 1")
        self.assertEqual(len(payload.cube_tests[0].cube_specimens), 1)
        self.assertEqual(payload.cube_tests[0].cube_specimens[0].mould_identifier, "CUBE-SPECIMEN-1")



if __name__ == "__main__":
    unittest.main()
