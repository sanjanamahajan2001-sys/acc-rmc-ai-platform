"""
Excel Workbook Deep Inspector & Reverse Engineering Helper Utility
-------------------------------------------------------------------
This production-quality module inspects Excel workbooks, extracting sheet metadata,
cell ranges, merged regions, hidden states, formulas, named ranges, unique values,
and structural schemas for automated domain model discovery.
"""

import os
import glob
import json
from typing import Dict, Any, List
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

class WorkbookInspector:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.wb_data = openpyxl.load_workbook(file_path, data_only=False)
        self.wb_val = openpyxl.load_workbook(file_path, data_only=True)

    def get_workbook_metadata(self) -> Dict[str, Any]:
        """Extract high-level workbook metadata including sheet list, named ranges, protection."""
        named_ranges = list(self.wb_data.defined_names.keys())
        sheets = []
        for name in self.wb_data.sheetnames:
            ws = self.wb_data[name]
            sheets.append({
                "name": name,
                "state": ws.sheet_state,
                "max_row": ws.max_row,
                "max_column": ws.max_column,
                "merged_ranges_count": len(list(ws.merged_cells.ranges))
            })
        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "sheet_count": len(self.wb_data.sheetnames),
            "sheet_names": self.wb_data.sheetnames,
            "named_ranges": named_ranges,
            "sheets": sheets
        }

    def inspect_worksheet(self, sheet_name: str, max_inspect_rows: int = 100) -> Dict[str, Any]:
        """Deep inspect a single worksheet for headers, data types, formulas, merged cells, and hidden elements."""
        if sheet_name not in self.wb_data.sheetnames:
            raise ValueError(f"Sheet {sheet_name} not found in {self.file_name}")

        ws_data: Worksheet = self.wb_data[sheet_name]
        ws_val: Worksheet = self.wb_val[sheet_name]

        merged_cells = [str(r) for r in ws_data.merged_cells.ranges]
        
        # Hidden rows and columns
        hidden_rows = [r for r, rd in ws_data.row_dimensions.items() if rd.hidden]
        hidden_cols = [c for c, cd in ws_data.column_dimensions.items() if cd.hidden]

        rows_data = []
        rows_to_scan = min(ws_data.max_row, max_inspect_rows)

        for r in range(1, rows_to_scan + 1):
            row_cells = []
            for c in range(1, min(ws_data.max_column, 50) + 1):
                c_data = ws_data.cell(row=r, column=c)
                c_val = ws_val.cell(row=r, column=c)
                
                raw_val = c_data.value
                eval_val = c_val.value
                
                is_formula = isinstance(raw_val, str) and raw_val.startswith("=")
                
                if raw_val is not None or eval_val is not None:
                    row_cells.append({
                        "col": c,
                        "col_letter": openpyxl.utils.get_column_letter(c),
                        "raw_value": str(raw_val),
                        "eval_value": str(eval_val) if eval_val is not None else None,
                        "is_formula": is_formula,
                        "data_type": type(eval_val if eval_val is not None else raw_val).__name__,
                        "number_format": c_data.number_format
                    })
            if row_cells:
                rows_data.append({
                    "row": r,
                    "cells": row_cells
                })

        return {
            "sheet_name": sheet_name,
            "max_row": ws_data.max_row,
            "max_column": ws_data.max_column,
            "merged_cells": merged_cells,
            "hidden_rows": hidden_rows,
            "hidden_cols": hidden_cols,
            "sample_rows": rows_data
        }

def inspect_all_raw_workbooks(raw_dir: str) -> Dict[str, Any]:
    """Scan all raw workbooks in raw_dir and extract complete inspection payload."""
    files = glob.glob(os.path.join(raw_dir, "**/*.xlsx"), recursive=True)
    report = {}
    for f in sorted(files):
        rel_path = os.path.relpath(f, raw_dir)
        inspector = WorkbookInspector(f)
        meta = inspector.get_workbook_metadata()
        sheet_details = {}
        for s in meta["sheet_names"]:
            sheet_details[s] = inspector.inspect_worksheet(s, max_inspect_rows=150)
        meta["sheet_details"] = sheet_details
        report[rel_path] = meta
    return report

if __name__ == "__main__":
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/sanjana/acc-rmc-ai-platform/data/raw"
    res = inspect_all_raw_workbooks(target_dir)
    output_json = os.path.join(target_dir, "inspection_summary.json")
    with open(output_json, "w") as out:
        json.dump(res, out, indent=2)
    print(f"Inspection complete. Summary saved to {output_json}")
