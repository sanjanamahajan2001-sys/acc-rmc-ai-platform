import uuid
"""Production Excel Source Parser for ACC Ready-Mix Concrete operational and laboratory workbooks.

Handles:
1. Multi-worksheet discovery and classification (FT7 certificates, batching reports, forecast/trend tests).
2. Block-boundary detection in semi-structured batch tickets.
3. Strict extraction of material consumptions, actual/planned masses, moisture metrics, and quality tests.
4. Clean priority rules: Prioritizes rich Batching Report / FT7 certificates over redundant summary sheets.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone, date
from decimal import Decimal
import io
import re
import openpyxl

from src.exceptions.base import ACCRMCBaseException
from src.contracts.ingestion.batch import BatchIngestionDTO
from src.contracts.ingestion.material import (
    MaterialConsumptionIngestionDTO,
    WeighingLogIngestionDTO,
)
from src.contracts.ingestion.quality import (
    CubeTestIngestionDTO,
    IndividualCubeSpecimenDTO,
    FT7CertificateIngestionDTO,
    SlumpTestIngestionDTO,
)
from src.contracts.ingestion.payload import SingleIngestionPayloadDTO


def normalize_challan(val: Any) -> Optional[str]:
    """Helper to clean challan strings."""
    if not val:
        return None
    s = str(val).strip()
    return s if s and s.upper() != "NONE" else None


class ExcelParsingException(ACCRMCBaseException):
    """Exception raised when parsing Excel workbooks fails or contains unrecoverable corruption."""

    def __init__(
        self,
        message: str,
        error_code: str = "EXCEL_PARSING_FAILURE",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message, error_code, details)


class ExcelSourceParser:
    """Production Excel Parser for ACC Ready-Mix Concrete operational and laboratory workbooks."""

    EXCEL_ERROR_STRINGS = {
        "#REF!",
        "#DIV/0!",
        "#VALUE!",
        "#NULL!",
        "#NAME?",
        "#N/A",
        "#NUM!",
    }

    def parse_workbook(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        worksheet_name: Optional[str] = None,
        source_file_name: Optional[str] = None,
    ) -> List[SingleIngestionPayloadDTO]:
        """Parse an Excel workbook and return a list of SingleIngestionPayloadDTO objects."""
        if not file_path and not file_bytes:
            raise ExcelParsingException("Either file_path or file_bytes must be provided.")

        src = io.BytesIO(file_bytes) if file_bytes else file_path
        try:
            wb = openpyxl.load_workbook(src, data_only=True)
        except Exception as e:
            raise ExcelParsingException(f"Corrupt or unreadable Excel workbook: {e}")

        payloads: List[SingleIngestionPayloadDTO] = []
        try:
            target_sheets = [worksheet_name] if worksheet_name and worksheet_name in wb.sheetnames else wb.sheetnames
            lower_sheets = [s.lower().strip() for s in wb.sheetnames]
            has_br_sheet = "batching report" in lower_sheets

            # 1. First pass: parse FT7 certificate sheets
            for s_name in target_sheets:
                ws = wb[s_name]
                if self._is_ft7_certificate_sheet(ws):
                    p = self._parse_ft7_certificate_sheet(ws, s_name, source_file_name=source_file_name)
                    if p:
                        payloads.append(p)

            # 2. Second pass: parse Forecast / Tabular strength sheets (e.g. '28 Day Test (2)', 'Forecast')
            has_individual_ft7 = any(p.cube_tests and len(p.cube_tests) > 0 and not (p.batch and "FCST" in (p.batch.batch_number or "")) for p in payloads)
            for s_name in target_sheets:
                ws = wb[s_name]
                s_lower = s_name.lower().strip()
                if s_lower in ("forecast", "forecast all", "forecast 2"):
                    payloads.extend(self._parse_forecast_sheet(ws, s_name, source_file_name=source_file_name))
                elif self._is_tabular_strength_sheet(ws, s_name):
                    # Only parse tabular strength sheet if specifically requested or if no individual certificate sheets were parsed
                    if worksheet_name or not has_individual_ft7:
                        payloads.extend(self._parse_tabular_strength_sheet(ws, s_name, source_file_name=source_file_name))

            # 3. Third pass: parse semi-structured Batching Report or Columns sheet
            for s_name in target_sheets:
                ws = wb[s_name]
                s_lower = s_name.lower().strip()
                if s_lower == "batching report":
                    payloads.extend(self._parse_batching_report_blocks(ws, s_name, source_file_name=source_file_name))
                elif s_lower == "columns":
                    # Parse Columns if specifically requested or if no Batching Report and no FT7 certificates
                    has_ft7 = any(p.cube_tests and len(p.cube_tests) > 0 and not (p.batch and "FCST" in (p.batch.batch_number or "")) for p in payloads)
                    if worksheet_name or (not has_br_sheet and not has_ft7):
                        payloads.extend(self._parse_columns_sheet(ws, s_name, source_file_name=source_file_name))

            # 4. Fourth pass: fallback for bare sheets named with challan number (e.g. '1749') only if no BR sheet exists
            if not payloads and len(target_sheets) > 0 and not has_br_sheet:
                for s_name in target_sheets:
                    clean_ch = self._extract_clean_challan(s_name)
                    if clean_ch:
                        ws = wb[s_name]
                        date_val = self._get_cell_datetime_lenient(ws, 1, 1) or datetime.now(timezone.utc)
                        payloads.append(
                            SingleIngestionPayloadDTO(
                                batch=BatchIngestionDTO(
                                    batch_number=f"BATCH-{clean_ch}",
                                    order_number=f"ORD-{clean_ch}",
                                    plant_code="PLANT-MUMBAI-01",
                                    recipe_code="M-40",
                                    planned_quantity_m3=Decimal("6.0"),
                                    actual_quantity_m3=None,
                                    delivery_challan=clean_ch,
                                    production_start_time=date_val,
                                    production_end_time=date_val,
                                ),
                                material_consumptions=[],
                                cube_tests=[],
                            )
                        )

        finally:
            wb.close()

        return payloads

    def _is_ft7_certificate_sheet(self, ws) -> bool:
        """Return True if worksheet has FT7 certificate header in top 15 rows."""
        for r in range(1, 15):
            for c in range(1, 5):
                val = ws.cell(r, c).value
                if val and any(token in str(val).upper() for token in ("FT 7 CERTIFICATE", "FT7 CERTIFICATE", "FT-7 CERTIFICATE")):
                    return True
        return False

    def _is_tabular_strength_sheet(self, ws, sheet_name: str) -> bool:
        """Return True if worksheet has tabular strength testing layout (e.g. '28 Day Test (2)')."""
        if ws.max_row < 2:
            return False
        headers = [str(ws.cell(1, c).value or "").strip().lower() for c in range(1, min(ws.max_column + 1, 15))]
        headers_str = " ".join(headers)
        if "challan" in headers_str and ("strenght" in headers_str or "strength" in headers_str):
            return True
        return False

    def _parse_ft7_certificate_sheet(
        self, ws, sheet_name: str, source_file_name: Optional[str] = None
    ) -> Optional[SingleIngestionPayloadDTO]:
        """Parse FT7 certificate worksheet extracting challan, batch context, and cube specimens."""
        headers_map: Dict[str, Any] = {}
        for r in range(5, 21):
            for c in range(1, 5):
                lbl = str(ws.cell(r, c).value or "").strip().lower()
                val = ws.cell(r, c + 1).value
                if "challan" in lbl and "challan" not in headers_map:
                    headers_map["challan"] = val
                elif "date of casting" in lbl and "casting_date" not in headers_map:
                    headers_map["casting_date"] = val
                elif "plant code" in lbl and "plant" not in headers_map:
                    headers_map["plant"] = val
                elif "grade of mix" in lbl and "grade" not in headers_map:
                    headers_map["grade"] = val
                elif "truck number" in lbl and "truck" not in headers_map:
                    headers_map["truck"] = val
                elif "load size" in lbl and "load_size" not in headers_map:
                    headers_map["load_size"] = val

        challan_raw = headers_map.get("challan") or self._get_cell_str_lenient(ws, 10, 2)
        challan_no = self._extract_clean_challan(challan_raw)

        load_size_val = headers_map.get("load_size") or self._get_cell_decimal_lenient(ws, 14, 2)
        if load_size_val in (0, "0", Decimal("0")):
            load_size_val = None

        load_size = Decimal("6.0")
        if load_size_val is not None:
            try:
                cleaned_load = re.sub(r"[^\d.]", "", str(load_size_val)).strip()
                if cleaned_load:
                    dec = Decimal(cleaned_load)
                    if dec > Decimal("0.0"):
                        load_size = dec
            except Exception:
                pass

        plant_raw = str(headers_map.get("plant") or self._get_cell_str_lenient(ws, 8, 2) or "NS70").strip()
        plant_code = f"PLANT-{plant_raw}" if not plant_raw.startswith("PLANT-") else plant_raw

        grade_raw = headers_map.get("grade") or self._get_cell_str_lenient(ws, 12, 2)
        recipe_code = self._clean_recipe_code(grade_raw, default_fallback="M-40")

        truck_raw = headers_map.get("truck") or self._get_cell_str_lenient(ws, 13, 2)
        truck_no = str(truck_raw).strip() if truck_raw and str(truck_raw).strip() not in ("0", "None") else None

        caste_date = self._parse_flexible_date(headers_map.get("casting_date")) or self._get_cell_datetime_lenient(ws, 24, 2)

        specimens: List[IndividualCubeSpecimenDTO] = []
        age_7d_specimens = []
        age_28d_specimens = []

        mould_row = 23
        load_row = 31
        str_row = 32
        for r in range(20, 35):
            c1_val = str(ws.cell(r, 1).value or "").strip().lower()
            if "mould" in c1_val or "cube id" in c1_val or "sample ref" in c1_val:
                mould_row = r
            if "maximum load" in c1_val or "load at failure" in c1_val or "failure load" in c1_val:
                load_row = r
            if "compressive strength" in c1_val or "strength (n/mm" in c1_val or "strength (mpa" in c1_val:
                str_row = r

        for col in range(2, 8):
            mould_no = self._get_cell_str_lenient(ws, mould_row, col) or self._get_cell_str_lenient(ws, mould_row - 1, col)
            test_date = self._get_cell_datetime_lenient(ws, 25, col)
            age = self._get_cell_int_lenient(ws, 27, col)
            sat_mass = self._get_cell_decimal_lenient(ws, 28, col)
            if sat_mass is not None and sat_mass > Decimal("100.00"):
                sat_mass = (sat_mass / Decimal("1000.0")).quantize(Decimal("0.001"))
            mass_water = self._get_cell_decimal_lenient(ws, 29, col)
            if mass_water is not None and mass_water > Decimal("100.00"):
                mass_water = (mass_water / Decimal("1000.0")).quantize(Decimal("0.001"))
            vol = self._get_cell_decimal_lenient(ws, 30, col)
            load = self._get_cell_decimal(ws, load_row, col)
            strength = self._get_cell_decimal_lenient(ws, str_row, col)
            cond = self._get_cell_str_lenient(ws, 33, col)

            if not mould_no and not load and strength is None:
                continue

            if load in (Decimal("0"), Decimal("0.0")) and strength in (Decimal("0"), Decimal("0.00")):
                continue

            if age is None:
                age = 7 if col in (2, 3, 4) else 28

            if strength is not None:
                strength = strength.quantize(Decimal("0.01"))

            specimen = IndividualCubeSpecimenDTO(
                mould_identifier=mould_no or f"CUBE-{col-1}",
                casting_timestamp=caste_date or datetime.now(timezone.utc),
                testing_timestamp=test_date or caste_date or datetime.now(timezone.utc),
                age_days=age,
                specimen_condition=cond,
                saturated_mass_kg=sat_mass,
                mass_in_water_kg=mass_water,
                calculated_volume_m3=vol,
                failure_load_kn=load,
                source_compressive_strength_mpa=strength if strength is not None else Decimal("0.00"),
                tested_by_user=self._get_cell_str_lenient(ws, 36, 6)
            )
            specimens.append(specimen)
            if age == 7:
                age_7d_specimens.append(specimen)
            else:
                age_28d_specimens.append(specimen)

        # Skip empty uncast template sheets only if no identifying grade or mix info exists
        if not specimens and load_size_val is None and not headers_map.get("casting_date") and not headers_map.get("grade") and not headers_map.get("challan"):
            return None

        cube_tests: List[CubeTestIngestionDTO] = []
        if age_7d_specimens:
            valid_7d = [s.source_compressive_strength_mpa for s in age_7d_specimens if s.source_compressive_strength_mpa]
            avg_7d = (sum(valid_7d, Decimal("0")) / Decimal(str(len(valid_7d)))).quantize(Decimal("0.01")) if valid_7d else Decimal("0.00")
            cube_tests.append(
                CubeTestIngestionDTO(
                    cube_set_number=f"QC-SET-{challan_no}-7D" if challan_no else f"QC-SET-{uuid.uuid4().hex[:8].upper()}-7D",
                    age_days=7,
                    compressive_strength_mpa=avg_7d,
                    testing_timestamp=age_7d_specimens[0].testing_timestamp,
                    cube_specimens=age_7d_specimens
                )
            )

        if age_28d_specimens:
            valid_28d = [s.source_compressive_strength_mpa for s in age_28d_specimens if s.source_compressive_strength_mpa]
            avg_28d = (sum(valid_28d, Decimal("0")) / Decimal(str(len(valid_28d)))).quantize(Decimal("0.01")) if valid_28d else Decimal("0.00")
            cube_tests.append(
                CubeTestIngestionDTO(
                    cube_set_number=f"QC-SET-{challan_no}-28D" if challan_no else f"QC-SET-{uuid.uuid4().hex[:8].upper()}-28D",
                    age_days=28,
                    compressive_strength_mpa=avg_28d,
                    testing_timestamp=age_28d_specimens[0].testing_timestamp,
                    cube_specimens=age_28d_specimens
                )
            )

        batch_number = f"BATCH-{challan_no}" if challan_no else f"BATCH-GEN-{uuid.uuid4().hex[:8].upper()}"
        batch_dto = BatchIngestionDTO(
            batch_number=batch_number,
            order_number=f"ORD-{challan_no}" if challan_no else "ORD-GEN-001",
            delivery_challan=challan_no,
            truck_number=truck_no,
            recipe_code=recipe_code,
            plant_code=plant_code,
            planned_quantity_m3=load_size,
            actual_quantity_m3=None,
            dataset_origin="OPERATIONAL_ACTUAL",
            production_start_time=caste_date,
            production_end_time=caste_date,
        )

        cert_no = self._get_cell_str_lenient(ws, 4, 6) or (f"CERT-{challan_no}" if challan_no else f"CERT-{uuid.uuid4().hex[:8].upper()}")
        ft7_dto = FT7CertificateIngestionDTO(
            certificate_number=cert_no,
            issued_date=caste_date or datetime.now(timezone.utc),
            approval_status="APPROVED",
            remarks=self._get_cell_str_lenient(ws, 35, 2)
        )

        return SingleIngestionPayloadDTO(
            batch=batch_dto,
            material_consumptions=[],
            weighing_logs=[],
            slump_tests=[],
            cube_tests=cube_tests,
            ft7_certificate=ft7_dto,
            production_events=[],
        )

    def _clean_recipe_code(self, raw_code: Optional[Any], default_fallback: str = "M-30") -> str:
        """Normalize recipe strings, handling multi-word names like 'ACC FEATHERCRETE M-30', 'GEN ALCN M -15', or 'RETE'."""
        if raw_code is None:
            return default_fallback
        s = str(raw_code).strip().upper()
        if not s or s in ("0", "0.0", "NONE", "NULL", "NAN", "TOTAL", "SUM", "AVERAGE", "AVG"):
            return default_fallback
        if "RETE" in s or "FEATHERCRETE" in s or "FEATHER" in s:
            return "M-30"

        m = re.search(r"M\s*-?\s*(\d{2})", s)
        if m:
            grade_num = m.group(1)
            return f"M-{grade_num}"

        m_num = re.search(r"\b(10|15|20|25|30|35|40|45|50)\b", s)
        if m_num:
            return f"M-{m_num.group(1)}"

        return default_fallback


    def _parse_tabular_strength_sheet(
        self, ws, sheet_name: str, source_file_name: Optional[str] = None
    ) -> List[SingleIngestionPayloadDTO]:
        """Parse tabular strength sheets like '28 Day Test (2)'."""
        payloads: List[SingleIngestionPayloadDTO] = []
        max_r = ws.max_row or 0
        for r in range(2, max_r + 1):
            ch_raw = self._get_cell_str_lenient(ws, r, 1)
            challan_no = self._extract_clean_challan(ch_raw)
            if not challan_no:
                continue

            date_val = self._parse_flexible_date(ws.cell(r, 2).value)
            str_raw = self._get_cell_decimal_lenient(ws, r, 3)
            grade_raw = self._get_cell_str_lenient(ws, r, 4)
            recipe_code = self._clean_recipe_code(grade_raw, default_fallback="M-25")

            cube_tests: List[CubeTestIngestionDTO] = []
            if str_raw is not None and str_raw > 0:
                cube_tests.append(
                    CubeTestIngestionDTO(
                        cube_set_number=f"QC-TAB-{challan_no}-28D",
                        age_days=28,
                        compressive_strength_mpa=str_raw.quantize(Decimal("0.01")),
                        testing_timestamp=date_val or datetime.now(timezone.utc),
                        cube_specimens=[]
                    )
                )

            batch_dto = BatchIngestionDTO(
                batch_number=f"BATCH-{challan_no}",
                order_number=f"ORD-{challan_no}",
                delivery_challan=challan_no,
                truck_number=None,
                recipe_code=recipe_code,
                plant_code="PLANT-NS70",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=None,
                dataset_origin="HISTORICAL_QC",
                production_start_time=date_val,
                production_end_time=date_val,
            )


            payloads.append(
                SingleIngestionPayloadDTO(
                    batch=batch_dto,
                    material_consumptions=[],
                    weighing_logs=[],
                    slump_tests=[],
                    cube_tests=cube_tests,
                    production_events=[],
                )
            )
        return payloads

    def _parse_forecast_sheet(
        self, ws, sheet_name: str, source_file_name: Optional[str] = None
    ) -> List[SingleIngestionPayloadDTO]:
        """Parse forecast strength testing sheets with dynamic header mapping."""
        payloads: List[SingleIngestionPayloadDTO] = []
        max_r = ws.max_row or 0
        if max_r < 2:
            return payloads

        headers = {}
        for c in range(1, ws.max_column + 1):
            val = ws.cell(1, c).value
            if val is not None:
                headers[str(val).strip().lower()] = c

        grade_col = next((c for k, c in headers.items() if "grade" in k), 1)
        date_col = next((c for k, c in headers.items() if "date" in k), 2)
        opc_col = next((c for k, c in headers.items() if "opc" in k and "coef" not in k), 4)
        ggbs_col = next((c for k, c in headers.items() if "ggbs" in k and "coef" not in k), 5)
        admix_col = next((c for k, c in headers.items() if "admixture" in k and "coef" not in k), 6)
        water_col = next((c for k, c in headers.items() if "water" in k and "coef" not in k), 7)
        str_col = next((c for k, c in headers.items() if ("strenght" in k or "strength" in k) and "28" in k), 9)

        for r in range(2, max_r + 1):
            grade_raw = self._get_cell_str_lenient(ws, r, grade_col)
            if grade_raw and str(grade_raw).strip().upper() in ("TOTAL", "SUM", "AVERAGE", "AVG"):
                continue

            cast_date = self._parse_flexible_date(ws.cell(r, date_col).value)
            opc = self._get_cell_decimal_lenient(ws, r, opc_col)
            ggbs = self._get_cell_decimal_lenient(ws, r, ggbs_col)
            admix = self._get_cell_decimal_lenient(ws, r, admix_col)
            water = self._get_cell_decimal_lenient(ws, r, water_col)
            strength_28d = self._get_cell_decimal_lenient(ws, r, str_col)

            if not cast_date and not strength_28d:
                continue

            if strength_28d is not None and (strength_28d < Decimal("0.0") or strength_28d > Decimal("150.0")):
                strength_28d = None

            row_id = f"R{r}"
            date_str = cast_date.strftime("%d%m%y") if cast_date else "NODATE"
            sheet_slug = sheet_name.replace(" ", "_").upper()
            batch_num = f"PRD-DSG-{sheet_slug}-{date_str}-{row_id}"
            recipe_code = self._clean_recipe_code(grade_raw, default_fallback="M-30")

            batch_dto = BatchIngestionDTO(
                batch_number=batch_num,
                order_number=f"ORD-DSG-{sheet_slug}-{row_id}",
                recipe_code=recipe_code,
                plant_code="PLANT-MUMBAI-01",
                planned_quantity_m3=Decimal("1.0"),
                actual_quantity_m3=Decimal("1.0"),
                dataset_origin="LAB_FORECAST_DESIGN",
                production_start_time=cast_date,
            )

            consumptions: List[MaterialConsumptionIngestionDTO] = []
            if opc is not None and opc > 0:
                consumptions.append(
                    MaterialConsumptionIngestionDTO(
                        material_code="CEMENT",
                        source_material_code="OPC",
                        planned_quantity=opc,
                        actual_quantity=opc,
                        quantity_semantics="KG_PER_M3",
                        source_unit="KG/M3",
                        source_quantity=opc,
                    )
                )
            if ggbs is not None and ggbs > 0:
                consumptions.append(
                    MaterialConsumptionIngestionDTO(
                        material_code="GGBS",
                        source_material_code="GGBS",
                        planned_quantity=ggbs,
                        actual_quantity=ggbs,
                        quantity_semantics="KG_PER_M3",
                        source_unit="KG/M3",
                        source_quantity=ggbs,
                    )
                )
            if water is not None and water > 0:
                consumptions.append(
                    MaterialConsumptionIngestionDTO(
                        material_code="WATER",
                        source_material_code="WATER",
                        planned_quantity=water,
                        actual_quantity=water,
                        quantity_semantics="KG_PER_M3",
                        source_unit="KG/M3",
                        source_quantity=water,
                    )
                )
            if admix is not None and admix > 0:
                consumptions.append(
                    MaterialConsumptionIngestionDTO(
                        material_code="ADMIXTURE",
                        source_material_code="ADMIXTURE",
                        planned_quantity=admix,
                        actual_quantity=admix,
                        quantity_semantics="KG_PER_M3",
                        source_unit="KG/M3",
                        source_quantity=admix,
                    )
                )

            cube_tests: List[CubeTestIngestionDTO] = []
            if strength_28d is not None and strength_28d > 0:
                cube_tests.append(
                    CubeTestIngestionDTO(
                        cube_set_number=f"QC-FCST-{sheet_name}-{row_id}-28D",
                        age_days=28,
                        compressive_strength_mpa=strength_28d.quantize(Decimal("0.01")),
                        testing_timestamp=cast_date or datetime.now(timezone.utc),
                        cube_specimens=[]
                    )
                )

            payloads.append(
                SingleIngestionPayloadDTO(
                    batch=batch_dto,
                    material_consumptions=consumptions,
                    weighing_logs=[],
                    slump_tests=[],
                    cube_tests=cube_tests,
                    production_events=[],
                )
            )
        return payloads

    def _parse_batching_report_blocks(
        self, ws, sheet_name: str, source_file_name: Optional[str] = None
    ) -> List[SingleIngestionPayloadDTO]:
        """Extract multi-batch blocks from 'Batching Report' sheet with exact cell coordinates."""
        payloads: List[SingleIngestionPayloadDTO] = []
        max_r = ws.max_row or 0
        r = 1
        while r <= max_r:
            val = ws.cell(r, 1).value
            if val and "Summary of batch reports" in str(val):
                del_note = ws.cell(r + 2, 1).value
                customer_full = str(ws.cell(r + 2, 2).value or "").strip()
                truck = str(ws.cell(r + 2, 4).value or "").strip()
                challan_no = self._extract_challan_from_customer_string(customer_full) or self._extract_clean_challan(del_note)

                start_date = None
                start_time_str = None
                recipe_code = "M-25"
                load_size = Decimal("6.0")

                mat_rows = []
                for b_r in range(r + 3, min(r + 55, max_r + 1)):
                    c1_val = str(ws.cell(b_r, 1).value or "").strip()
                    c2_val = str(ws.cell(b_r, 2).value or "").strip()

                    if "Total" in c2_val and "m3" in str(ws.cell(b_r, 2).value or ""):
                        try:
                            cleaned_tot = re.sub(r"[^\d.]", "", str(ws.cell(b_r, 2).value)).strip()
                            if cleaned_tot:
                                load_size = Decimal(cleaned_tot)
                        except Exception:
                            pass

                    if "Date" in c1_val:
                        d_str = c1_val.replace("Date", "").strip()
                        start_date = self._parse_flexible_date(d_str)

                    if "Time" in c1_val:
                        t_str = c1_val.replace("Time", "").strip()
                        start_time_str = t_str

                    if "Code:" in c2_val:
                        raw_recipe = c2_val.replace("Code:", "").strip()
                        recipe_code = self._clean_recipe_code(raw_recipe, default_fallback="M-25")

                    if c1_val in ("SAND 2", "20 MM", "10 MM", "CEMENT 1", "CEMENT 2", "CEMENT 3", "WATER", "ADD 1", "ADD 2", "ADMIXTURE 1", "ADMIXTURE 2"):
                        mat_name = ws.cell(b_r, 2).value or c1_val
                        theor = self._get_cell_decimal_lenient(ws, b_r, 5)
                        batched = self._get_cell_decimal_lenient(ws, b_r, 10)
                        moi = self._get_cell_decimal_lenient(ws, b_r, 6)
                        if theor or batched:
                            mat_rows.append((c1_val, mat_name, theor, batched, moi))

                # Combine start date and time
                if start_date and start_time_str:
                    try:
                        time_parts = [int(p) for p in start_time_str.split(":") if p.isdigit()]
                        if len(time_parts) >= 2:
                            h = time_parts[0]
                            m = time_parts[1]
                            s = time_parts[2] if len(time_parts) > 2 else 0
                            start_date = start_date.replace(hour=h, minute=m, second=s)
                    except Exception:
                        pass

                if challan_no:
                    b_id = f"BATCH-BR-{del_note}-{challan_no}" if del_note else f"BATCH-BR-{challan_no}"
                    batch_dto = BatchIngestionDTO(
                        batch_number=b_id,
                        order_number=f"ORD-BR-{del_note or challan_no}",
                        delivery_challan=challan_no,
                        truck_number=truck if truck and truck != "None" else None,
                        recipe_code=recipe_code,
                        plant_code="PLANT-NS70",
                        planned_quantity_m3=load_size,
                        actual_quantity_m3=load_size,
                        dataset_origin="OPERATIONAL_ACTUAL",
                        production_start_time=start_date,
                    )

                    consumptions = []
                    for code, name, theor, batched, moi in mat_rows:
                        std_code = str(code).strip()
                        raw_batched = batched or theor or Decimal("0")
                        raw_theor = theor or batched or Decimal("0")
                        consumptions.append(
                            MaterialConsumptionIngestionDTO(
                                material_code=std_code,
                                source_material_code=str(name),
                                planned_quantity=raw_theor,
                                actual_quantity=raw_batched,
                                quantity_semantics="TOTAL_BATCH_KG",
                                source_unit="KG",
                                source_quantity=raw_batched,
                                moisture_percentage=moi,
                            )
                        )

                    payloads.append(
                        SingleIngestionPayloadDTO(
                            batch=batch_dto,
                            material_consumptions=consumptions,
                            cube_tests=[],
                        )
                    )
                r += 50
            else:
                r += 1

        return payloads

    def _parse_columns_sheet(
        self, ws, sheet_name: str, source_file_name: Optional[str] = None
    ) -> List[SingleIngestionPayloadDTO]:
        """Parse tabular 'Columns' summary sheet."""
        payloads: List[SingleIngestionPayloadDTO] = []
        headers = {str(ws.cell(1, c).value or "").strip().lower(): c for c in range(1, ws.max_column + 1)}
        challan_col = next((c for k, c in headers.items() if "challan" in k or "d.c" in k or "dc no" in k), 2)
        truck_col = next((c for k, c in headers.items() if "truck" in k or "vehicle" in k or "tm no" in k or "tm" in k), 3)
        date_col = next((c for k, c in headers.items() if "date" in k), 1)
        grade_col = next((c for k, c in headers.items() if "grade" in k or "recipe" in k), 4)

        for r in range(2, ws.max_row + 1):
            ch_raw = self._get_cell_str_lenient(ws, r, challan_col)
            challan_no = self._extract_clean_challan(ch_raw)
            if not challan_no:
                continue

            truck_raw = self._get_cell_str_lenient(ws, r, truck_col)
            date_val = self._parse_flexible_date(ws.cell(r, date_col).value)
            grade_raw = self._get_cell_str_lenient(ws, r, grade_col)
            recipe_code = self._clean_recipe_code(grade_raw, default_fallback="M-30")

            batch_dto = BatchIngestionDTO(
                batch_number=f"BATCH-{challan_no}",
                order_number=f"ORD-COL-{challan_no}",
                delivery_challan=challan_no,
                truck_number=truck_raw,
                recipe_code=recipe_code,
                plant_code="PLANT-NS70",
                planned_quantity_m3=Decimal("6.0"),
                actual_quantity_m3=None,
                production_start_time=date_val,
                production_end_time=date_val,
            )

            payloads.append(
                SingleIngestionPayloadDTO(
                    batch=batch_dto,
                    material_consumptions=[],
                    cube_tests=[],
                )
            )
        return payloads

    def _extract_clean_challan(self, val: Any) -> Optional[str]:
        """Extract clean 4-6 digit delivery challan from text or numbers."""
        if val is None:
            return None
        s = str(val).strip()
        if not s or s in self.EXCEL_ERROR_STRINGS:
            return None
        match = re.search(r"\b(\d{4,6})\b", s)
        if match:
            return match.group(1).lstrip("0") or "0"
        return None

    def _extract_challan_from_customer_string(self, text: str) -> Optional[str]:
        """Extract challan suffix from strings like 'RAJDEEP - RAJDEEP BUILDER NS70302501007285'."""
        if not text:
            return None
        match = re.search(r"(\d{4,6})$", text.strip())
        if match:
            return match.group(1).lstrip("0") or "0"
        return None

    def _parse_flexible_date(self, val: Any) -> Optional[datetime]:
        """Parse Excel dates, serials, and DD-MM-YY strings robustly."""
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val
        if isinstance(val, date):
            return datetime(val.year, val.month, val.day, tzinfo=timezone.utc)

        s_val = str(val).strip()
        if not s_val or s_val in self.EXCEL_ERROR_STRINGS:
            return None

        s_val = re.sub(r"^[Dd]ate\s*", "", s_val).strip()

        for fmt in ("%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(s_val, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        try:
            serial = float(s_val)
            if serial > 1000:
                base = datetime(1899, 12, 30, tzinfo=timezone.utc)
                from datetime import timedelta
                return base + timedelta(days=serial)
        except ValueError:
            pass

        return None

    def _get_cell_str_lenient(self, ws, r: int, c: int) -> Optional[str]:
        val = ws.cell(r, c).value
        if val is None:
            return None
        s = str(val).strip()
        if not s or s in self.EXCEL_ERROR_STRINGS:
            return None
        return s

    def _get_cell_decimal(self, ws, r: int, c: int) -> Optional[Decimal]:
        val = ws.cell(r, c).value
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        s = str(val).strip()
        if any(err in s.upper() for err in self.EXCEL_ERROR_STRINGS):
            raise ExcelParsingException(f"Excel formula error '{s}' found in worksheet '{ws.title}' at row {r}, col {c}")
        if not s:
            return None
        try:
            return Decimal(s)
        except Exception:
            raise ExcelParsingException(f"Invalid decimal value '{s}' in worksheet '{ws.title}' at cell ({r}, {c})")

    def _get_cell_decimal_lenient(self, ws, r: int, c: int) -> Optional[Decimal]:
        try:
            return self._get_cell_decimal(ws, r, c)
        except Exception:
            return None

    def _get_cell_int_lenient(self, ws, r: int, c: int) -> Optional[int]:
        d = self._get_cell_decimal(ws, r, c)
        return int(d) if d is not None else None

    def _get_cell_datetime_lenient(self, ws, r: int, c: int) -> Optional[datetime]:
        val = ws.cell(r, c).value
        return self._parse_flexible_date(val)
