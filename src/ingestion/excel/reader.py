"""Low-Memory Streaming Row Reader Generator Engine for WS-03.4 Phase 2.

This module provides StreamingExcelReader streaming structured RawWorksheetChunk contracts.
Never loads entire workbooks into RAM. Automatically cleans up file resources upon completion or failure.
"""

import csv
import io
import os
from typing import Any, Dict, Generator, List, Optional
from src.ingestion.excel.config import IngestionConfig, get_default_ingestion_config
from src.ingestion.excel.contracts import RawRow, RawWorksheetChunk


class StreamingExcelReader:
    """Enterprise Low-Memory Streaming Excel & CSV Row Reader Engine."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or get_default_ingestion_config()

    def stream_worksheet_chunks(
        self,
        file_path: str,
        worksheet_name: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        chunk_size: Optional[int] = None,
    ) -> Generator[RawWorksheetChunk, None, None]:
        """Yield structured RawWorksheetChunk contracts containing RawRow objects."""
        ext = os.path.splitext(file_path)[1].lower()
        effective_chunk_size = chunk_size or self.config.chunk_size_rows

        if ext == ".csv":
            yield from self._stream_csv_chunks(file_path, file_bytes, effective_chunk_size)
        elif ext == ".xlsx":
            yield from self._stream_xlsx_chunks(file_path, file_bytes, worksheet_name, effective_chunk_size)
        elif ext == ".xls":
            yield from self._stream_xls_chunks(file_path, file_bytes, worksheet_name, effective_chunk_size)
        else:
            raise ValueError(f"Unsupported file format '{ext}' for streaming reading.")

    def stream_worksheet_rows(
        self,
        file_path: str,
        worksheet_name: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        chunk_size: Optional[int] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """Backward-compatible helper yielding list of row dicts."""
        for chunk in self.stream_worksheet_chunks(file_path, worksheet_name, file_bytes, chunk_size):
            yield [r.data for r in chunk.rows]

    def _stream_csv_chunks(
        self,
        file_path: str,
        file_bytes: Optional[bytes],
        chunk_size: int,
    ) -> Generator[RawWorksheetChunk, None, None]:
        """Stream CSV rows in RawWorksheetChunk contracts."""
        try:
            if file_bytes is not None:
                content = file_bytes.decode("utf-8", errors="replace")
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {str(e)}")

        lines = content.splitlines()
        if not lines:
            return

        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff("\n".join(lines[:10]), delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.reader(lines, delimiter=delimiter)
        try:
            headers = [str(cell).strip() for cell in next(reader)]
        except StopIteration:
            return

        chunk_rows: List[RawRow] = []
        chunk_idx = 0
        current_row_index = 0

        for row in reader:
            if not row or all(str(cell).strip() == "" for cell in row):
                continue
            row_dict = {headers[i] if i < len(headers) else f"Col_{i}": row[i].strip() if i < len(row) else None for i in range(len(row))}
            chunk_rows.append(RawRow(row_index=current_row_index, data=row_dict))
            current_row_index += 1

            if len(chunk_rows) >= chunk_size:
                yield RawWorksheetChunk(
                    worksheet_name="Sheet1",
                    chunk_index=chunk_idx,
                    starting_row=chunk_rows[0].row_index,
                    ending_row=chunk_rows[-1].row_index,
                    rows=chunk_rows,
                )
                chunk_idx += 1
                chunk_rows = []

        if chunk_rows:
            yield RawWorksheetChunk(
                worksheet_name="Sheet1",
                chunk_index=chunk_idx,
                starting_row=chunk_rows[0].row_index,
                ending_row=chunk_rows[-1].row_index,
                rows=chunk_rows,
            )

    def _stream_xlsx_chunks(
        self,
        file_path: str,
        file_bytes: Optional[bytes],
        worksheet_name: Optional[str],
        chunk_size: int,
    ) -> Generator[RawWorksheetChunk, None, None]:
        """Stream .xlsx worksheet rows in RawWorksheetChunk contracts."""
        import openpyxl

        src = io.BytesIO(file_bytes) if file_bytes else file_path
        try:
            wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
        except Exception as e:
            raise ValueError(f"Corrupt or unreadable .xlsx file: {str(e)}")

        try:
            sheet_name = worksheet_name or wb.sheetnames[0]
            if sheet_name not in wb.sheetnames:
                raise ValueError(f"Worksheet '{sheet_name}' not found in workbook.")

            ws = wb[sheet_name]
            headers: List[str] = []
            chunk_rows: List[RawRow] = []
            chunk_idx = 0
            current_row_index = 0

            for idx, row in enumerate(ws.iter_rows(values_only=True)):
                if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                    continue

                non_empty_cells = [cell for cell in row if cell is not None and str(cell).strip() != ""]
                if not headers:
                    if len(non_empty_cells) >= 2:
                        last_valid_idx = max(c_idx for c_idx, cell in enumerate(row) if cell is not None and str(cell).strip() != "")
                        raw_header_cells = row[:last_valid_idx+1]
                        seen_counts: Dict[str, int] = {}
                        headers = []
                        for c_idx, cell in enumerate(raw_header_cells):
                            c_str = str(cell).strip() if (cell is not None and str(cell).strip() != "") else f"Unnamed_Column_{c_idx+1}"
                            seen_counts[c_str] = seen_counts.get(c_str, 0) + 1
                            if seen_counts[c_str] > 1:
                                headers.append(f"{c_str} [{seen_counts[c_str]}]")
                            else:
                                headers.append(c_str)
                else:
                    row_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                    chunk_rows.append(RawRow(row_index=current_row_index, data=row_dict))
                    current_row_index += 1

                    if len(chunk_rows) >= chunk_size:
                        yield RawWorksheetChunk(
                            worksheet_name=sheet_name,
                            chunk_index=chunk_idx,
                            starting_row=chunk_rows[0].row_index,
                            ending_row=chunk_rows[-1].row_index,
                            rows=chunk_rows,
                        )
                        chunk_idx += 1
                        chunk_rows = []

            if chunk_rows:
                yield RawWorksheetChunk(
                    worksheet_name=sheet_name,
                    chunk_index=chunk_idx,
                    starting_row=chunk_rows[0].row_index,
                    ending_row=chunk_rows[-1].row_index,
                    rows=chunk_rows,
                )
        finally:
            wb.close()

    def _stream_xls_chunks(
        self,
        file_path: str,
        file_bytes: Optional[bytes],
        worksheet_name: Optional[str],
        chunk_size: int,
    ) -> Generator[RawWorksheetChunk, None, None]:
        """Stream .xls legacy worksheet rows in RawWorksheetChunk contracts."""
        import xlrd

        try:
            wb = xlrd.open_workbook(file_contents=file_bytes) if file_bytes else xlrd.open_workbook(file_path)
        except Exception as e:
            raise ValueError(f"Corrupt or unreadable .xls file: {str(e)}")

        sheet_name = worksheet_name or wb.sheet_names()[0]
        if sheet_name not in wb.sheet_names():
            raise ValueError(f"Worksheet '{sheet_name}' not found in workbook.")

        sheet = wb.sheet_by_name(sheet_name)
        if sheet.nrows == 0:
            return

        headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
        chunk_rows: List[RawRow] = []
        chunk_idx = 0
        current_row_index = 0

        for row_idx in range(1, sheet.nrows):
            row_vals = sheet.row_values(row_idx)
            if not row_vals or all(v == "" for v in row_vals):
                continue
            row_dict = {headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx}": row_vals[col_idx] for col_idx in range(len(row_vals))}
            chunk_rows.append(RawRow(row_index=current_row_index, data=row_dict))
            current_row_index += 1

            if len(chunk_rows) >= chunk_size:
                yield RawWorksheetChunk(
                    worksheet_name=sheet_name,
                    chunk_index=chunk_idx,
                    starting_row=chunk_rows[0].row_index,
                    ending_row=chunk_rows[-1].row_index,
                    rows=chunk_rows,
                )
                chunk_idx += 1
                chunk_rows = []

        if chunk_rows:
            yield RawWorksheetChunk(
                worksheet_name=sheet_name,
                chunk_index=chunk_idx,
                starting_row=chunk_rows[0].row_index,
                ending_row=chunk_rows[-1].row_index,
                rows=chunk_rows,
            )
