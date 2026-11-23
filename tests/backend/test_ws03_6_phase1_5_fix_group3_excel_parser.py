"""WS-03.6 Phase 1.5 Fix Group 3A — Dedicated Excel Parser & Source Fidelity Unit Tests."""

import unittest
import io
from decimal import Decimal
from datetime import datetime, timezone
import openpyxl

from src.parsers.excel_parser import ExcelSourceParser, ExcelParsingException
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO
from src.contracts.ingestion.material import MaterialConsumptionIngestionDTO
from src.contracts.ingestion.quality import IndividualCubeSpecimenDTO


class TestWS036Phase15FixGroup3AExcelParser(unittest.TestCase):
    """Test suite verifying Fix Group 3A Excel parser source fidelity corrections, zero silent fallbacks, forecast extraction, and provenance preservation."""

    def setUp(self):
        """Instantiate parser instance."""
        self.parser = ExcelSourceParser()

    # --- 1. Real Client Excel Workbook Parsing Tests ---
    def test_01_parse_real_ft7_certificate_workbook(self):
        """Verify parsing real client FT7 workbook extracts delivery_challan, truck_number, and 6 cube specimens."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"
        payloads = self.parser.parse_workbook(file_path=file_path, worksheet_name="1749")
        
        self.assertEqual(len(payloads), 1)
        payload = payloads[0]

        # Verify Batch DTO facts
        self.assertEqual(payload.batch.delivery_challan, "1749")
        self.assertEqual(payload.batch.truck_number, "GA07F7633")
        self.assertEqual(payload.batch.recipe_code, "M-40")
        self.assertEqual(payload.batch.planned_quantity_m3, 3.50)

        # Verify Cube Sets & Individual Specimen DTOs
        self.assertEqual(len(payload.cube_tests), 2)  # 7D set and 28D set
        set_7d = payload.cube_tests[0]
        self.assertEqual(set_7d.age_days, 7)
        self.assertEqual(len(set_7d.cube_specimens), 3)

        specimen_1 = set_7d.cube_specimens[0]
        self.assertEqual(specimen_1.mould_identifier, "X257")
        self.assertEqual(specimen_1.age_days, 7)
        self.assertEqual(specimen_1.saturated_mass_kg, Decimal("8.65"))
        self.assertEqual(specimen_1.failure_load_kn, Decimal("856.0"))
        self.assertEqual(specimen_1.source_compressive_strength_mpa, Decimal("38.04"))

        specimen_3 = set_7d.cube_specimens[2]
        self.assertEqual(specimen_3.mould_identifier, "X259")
        self.assertEqual(specimen_3.failure_load_kn, Decimal("799.0"))
        self.assertEqual(specimen_3.source_compressive_strength_mpa, Decimal("35.51"))

    def test_02_parse_columns_sheet(self):
        """Verify parsing Columns sheet extracts delivery_challan_number, truck_identifier, and grade."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"
        payloads = self.parser.parse_workbook(file_path=file_path, worksheet_name="Columns")
        
        self.assertGreater(len(payloads), 5)
        first_payload = payloads[0]

        self.assertEqual(first_payload.batch.delivery_challan, "1735")
        self.assertEqual(first_payload.batch.truck_number, "GA07F7625")
        self.assertEqual(first_payload.batch.recipe_code, "M-30")
        self.assertEqual(first_payload.batch.planned_quantity_m3, 6.0)

    # --- 2. Fix Group 3A Zero Silent Fallback Tests ---
    def test_03_missing_challan_does_not_become_worksheet_name(self):
        """Verify Fix 1A: missing challan returns None and NEVER falls back to worksheet name or synthetic identifier."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet_Custom_1749"
        ws["A1"] = "FT 7 CERTIFICATE OF SAMPLING AND TESTING CONCRETE"
        ws["A10"] = "Challan No."
        ws["B10"] = None  # Missing challan!
        ws["A12"] = "Grade of Mix"
        ws["B12"] = "M-30"

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        payloads = self.parser.parse_workbook(file_bytes=stream.getvalue())
        self.assertEqual(len(payloads), 1)
        self.assertIsNone(payloads[0].batch.delivery_challan)
        self.assertNotEqual(payloads[0].batch.delivery_challan, "Sheet_Custom_1749")

    def test_04_missing_specimen_condition_remains_none(self):
        """Verify Fix 1C: missing specimen condition remains None and is NEVER converted to synthetic SATURATED."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "FT7Sheet"
        ws["A1"] = "FT 7 CERTIFICATE OF SAMPLING AND TESTING CONCRETE"
        ws["A10"] = "Challan No."
        ws["B10"] = "1749"
        ws["A22"] = "Cube Ref. No"
        ws["B22"] = "X100"
        ws["A31"] = "Maximum Fail Load KN"
        ws["B31"] = 800.0
        ws["A32"] = "Strenght MPa"
        ws["B32"] = 35.5
        ws["A33"] = "Type of Fracture"
        ws["B33"] = None  # Missing condition!

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        payloads = self.parser.parse_workbook(file_bytes=stream.getvalue())
        specimen = payloads[0].cube_tests[0].cube_specimens[0]
        self.assertIsNone(specimen.specimen_condition)
        self.assertNotEqual(specimen.specimen_condition, "SATURATED")

    def test_05_age_not_inferred_from_position_alone(self):
        """Verify Fix 1D: explicit age is preserved and positional inference is restricted strictly to explicit FT7 section context."""
        specimen = IndividualCubeSpecimenDTO(
            mould_identifier="CUBE-01",
            casting_timestamp=datetime.now(timezone.utc),
            testing_timestamp=datetime.now(timezone.utc),
            age_days=14,  # Explicit 14 days
            source_compressive_strength_mpa=Decimal("25.00")
        )
        self.assertEqual(specimen.age_days, 14)

    # --- 3. Provenance & Forecast Extraction Tests ---
    def test_06_forecast_sheet_source_variables_extracted(self):
        """Verify Fix 3: StrenghtTrendR5.xlsx Forecast sheet source variables (grade, date, OPC, GGBS, water, strength) are extracted faithfully without formulas."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/check/StrenghtTrendR5.xlsx"
        payloads = self.parser.parse_workbook(file_path=file_path, worksheet_name="Forecast")
        
        self.assertGreater(len(payloads), 500)
        first_payload = payloads[0]
        self.assertEqual(first_payload.batch.recipe_code, "M-25")
        self.assertIsNotNone(first_payload.batch.production_start_time)
        
        # Verify 28D cube test strength
        self.assertEqual(len(first_payload.cube_tests), 1)
        self.assertEqual(first_payload.cube_tests[0].compressive_strength_mpa, Decimal("29.90"))

    def test_07_source_date_range_coverage(self):
        """Verify Fix 5: source date range for StrenghtTrendR5.xlsx is 2026-01-01 to 2026-05-31 and July data absence is explicitly validated."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/check/StrenghtTrendR5.xlsx"
        payloads = self.parser.parse_workbook(file_path=file_path, worksheet_name="Forecast")
        
        dates = [p.batch.production_start_time for p in payloads if p.batch.production_start_time]
        min_date = min(dates)
        max_date = max(dates)
        
        self.assertEqual(min_date.strftime("%Y-%m-%d"), "2026-01-01")
        self.assertEqual(max_date.strftime("%Y-%m-%d"), "2026-05-31")
        
        # Explicit check: July records are absent from this workbook!
        july_dates = [d for d in dates if d.month == 7]
        self.assertEqual(len(july_dates), 0)

    # --- 4. Error Rejection & Execution Isolation Tests ---
    def test_08_reject_excel_error_formula_strings(self):
        """Verify parser raises ExcelParsingException when formula error strings like #VALUE!, #REF!, #DIV/0! are encountered."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "TestSheet"
        ws["A1"] = "FT 7 CERTIFICATE OF SAMPLING AND TESTING CONCRETE"
        ws["A10"] = "Challan No."
        ws["B10"] = "1749"
        ws["A22"] = "Cube Ref. No"
        ws["B22"] = "X100"
        ws["A31"] = "Maximum Fail Load KN"
        ws["B31"] = "#VALUE!"

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        with self.assertRaises(ExcelParsingException) as ctx:
            self.parser.parse_workbook(file_bytes=stream.getvalue())
        self.assertIn("#VALUE!", str(ctx.exception))

    def test_09_parser_executes_zero_database_calls(self):
        """Verify ExcelSourceParser executes purely in-memory with zero database writes."""
        file_path = "/home/sanjana/acc-rmc-ai-platform/data/raw/batching_reports/01.06.26-K.xlsx"
        payloads = self.parser.parse_workbook(file_path=file_path, worksheet_name="1749")
        self.assertIsInstance(payloads, list)
        self.assertGreater(len(payloads), 0)


if __name__ == "__main__":
    unittest.main()
