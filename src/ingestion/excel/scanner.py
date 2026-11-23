"""Workbook Scanning & Discovery Metadata Models for WS-03.4 Phase 2.

This module provides the WorkbookMetadata immutable contract and WorkbookScanner discovery engine.
"""

from datetime import datetime, timezone

import csv
import io
import os
import time
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from src.ingestion.excel.config import IngestionConfig, get_default_ingestion_config


class WorkbookMetadata(BaseModel):
    """Immutable contract carrying metadata discovered during workbook scanning."""

    filename: str = Field(..., description="Original file name.")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes.")
    workbook_type: str = Field(..., description="Format identifier (.xlsx, .xls, .csv).")
    worksheet_names: List[str] = Field(default_factory=list, description="Discovered worksheet tab names.")
    worksheet_count: int = Field(..., ge=0, description="Count of worksheets found.")
    detected_headers: Dict[str, List[str]] = Field(default_factory=dict, description="Header column names per worksheet.")
    estimated_row_counts: Dict[str, int] = Field(default_factory=dict, description="Estimated row count per worksheet.")
    scan_duration_ms: float = Field(..., ge=0.0, description="Scan latency in milliseconds.")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 hash reference.")
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC scan timestamp.")

    model_config = ConfigDict(frozen=True, extra="forbid")


class WorkbookScanner:
    """Enterprise Workbook Scanner for discovering sheet inventory, header names, row counts, and corrupt file detection."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or get_default_ingestion_config()

    def scan_file(
        self,
        file_path: str,
        file_bytes: Optional[bytes] = None,
        checksum_sha256: Optional[str] = None,
    ) -> WorkbookMetadata:
        """Scan Excel workbook or CSV file, return WorkbookMetadata."""
        t0 = time.perf_counter()
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in self.config.allowed_extensions:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed extensions: {self.config.allowed_extensions}")

        file_size = len(file_bytes) if file_bytes is not None else (os.path.getsize(file_path) if os.path.exists(file_path) else 0)
        if file_size > self.config.max_file_size_bytes:
            raise ValueError(f"File size {file_size} bytes exceeds maximum limit {self.config.max_file_size_bytes} bytes.")

        sheet_names: List[str] = []
        headers_map: Dict[str, List[str]] = {}
        row_counts_map: Dict[str, int] = {}

        if ext == ".csv":
            sheet_names = ["Sheet1"]
            headers, count = self._scan_csv(file_path, file_bytes)
            headers_map["Sheet1"] = headers
            row_counts_map["Sheet1"] = count
        elif ext == ".xlsx":
            sheet_names, headers_map, row_counts_map = self._scan_xlsx(file_path, file_bytes)
        elif ext == ".xls":
            sheet_names, headers_map, row_counts_map = self._scan_xls(file_path, file_bytes)

        if len(sheet_names) > self.config.max_worksheets_per_file:
            raise ValueError(f"Worksheet count {len(sheet_names)} exceeds limit {self.config.max_worksheets_per_file}.")

        t1 = time.perf_counter()
        scan_duration = (t1 - t0) * 1000.0

        return WorkbookMetadata(
            filename=os.path.basename(file_path),
            file_size_bytes=file_size,
            workbook_type=ext,
            worksheet_names=sheet_names,
            worksheet_count=len(sheet_names),
            detected_headers=headers_map,
            estimated_row_counts=row_counts_map,
            scan_duration_ms=scan_duration,
            checksum_sha256=checksum_sha256,
            scanned_at=datetime.now(timezone.utc),
        )

    def _scan_csv(self, file_path: str, file_bytes: Optional[bytes]) -> Tuple[List[str], int]:
        """Scan CSV file headers and row count using Sniffer auto-delimiter detection."""
        try:
            if file_bytes is not None:
                content = file_bytes.decode("utf-8", errors="replace")
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

        lines = content.splitlines()
        if not lines:
            return [], 0

        # Auto-detect delimiter
        sample = "\n".join(lines[:10])
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.reader(lines, delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return [], 0

        headers = [str(cell).strip() for cell in rows[0]]
        data_rows_count = max(0, len(rows) - 1)
        return headers, data_rows_count

    def _scan_xlsx(self, file_path: str, file_bytes: Optional[bytes]) -> Tuple[List[str], Dict[str, List[str]], Dict[str, int]]:
        """Scan .xlsx workbook in read-only mode with openpyxl."""
        import openpyxl

        src = io.BytesIO(file_bytes) if file_bytes else file_path
        try:
            wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
        except Exception as e:
            raise ValueError(f"Corrupt or unreadable .xlsx file: {str(e)}")

        sheet_names = wb.sheetnames
        headers_map: Dict[str, List[str]] = {}
        row_counts_map: Dict[str, int] = {}

        try:
            for name in sheet_names:
                ws = wb[name]
                headers = []
                count = 0
                for idx, row in enumerate(ws.iter_rows(values_only=True)):
                    if idx == 0:
                        headers = [str(cell).strip() if cell is not None else f"Column_{c_idx}" for c_idx, cell in enumerate(row)]
                    else:
                        count += 1
                headers_map[name] = headers
                row_counts_map[name] = count
        finally:
            wb.close()

        return sheet_names, headers_map, row_counts_map

    def _scan_xls(self, file_path: str, file_bytes: Optional[bytes]) -> Tuple[List[str], Dict[str, List[str]], Dict[str, int]]:
        """Scan .xls legacy workbook with xlrd."""
        import xlrd

        try:
            wb = xlrd.open_workbook(file_contents=file_bytes) if file_bytes else xlrd.open_workbook(file_path)
        except Exception as e:
            raise ValueError(f"Corrupt or unreadable .xls file: {str(e)}")

        sheet_names = wb.sheet_names()
        headers_map: Dict[str, List[str]] = {}
        row_counts_map: Dict[str, int] = {}

        for name in sheet_names:
            sheet = wb.sheet_by_name(name)
            headers = []
            if sheet.nrows > 0:
                headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
            headers_map[name] = headers
            row_counts_map[name] = max(0, sheet.nrows - 1)

        return sheet_names, headers_map, row_counts_map
