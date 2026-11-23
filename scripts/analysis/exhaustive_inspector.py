import openpyxl
import glob
import os
import json

def inspect_file(filepath):
    print(f"Processing {filepath}...")
    wb_data = openpyxl.load_workbook(filepath, data_only=False)
    wb_val = openpyxl.load_workbook(filepath, data_only=True)
    
    file_info = {
        "file_name": os.path.basename(filepath),
        "relative_path": filepath,
        "sheet_count": len(wb_data.sheetnames),
        "sheet_names": wb_data.sheetnames,
        "named_ranges": list(wb_data.defined_names.keys()),
        "sheets": {}
    }
    
    for sheet_name in wb_data.sheetnames:
        ws_d = wb_data[sheet_name]
        ws_v = wb_val[sheet_name]
        
        merged_ranges = []
        for r in ws_d.merged_cells.ranges:
            merged_ranges.append({
                "range": str(r),
                "min_col": r.min_col,
                "min_row": r.min_row,
                "max_col": r.max_col,
                "max_row": r.max_row,
                "top_left_value": str(ws_v.cell(r.min_row, r.min_col).value) if ws_v.cell(r.min_row, r.min_col).value is not None else None
            })
            
        hidden_rows = [r for r, rd in ws_d.row_dimensions.items() if rd.hidden]
        hidden_cols = [c for c, cd in ws_d.column_dimensions.items() if cd.hidden]
        
        formulas = []
        rows_layout = {}
        columns_dict = {}
        
        max_r = ws_d.max_row
        max_c = ws_d.max_column
        
        for r in range(1, max_r + 1):
            row_cells = []
            non_empty_count = 0
            for c in range(1, max_c + 1):
                cell_d = ws_d.cell(r, c)
                cell_v = ws_v.cell(r, c)
                val_d = cell_d.value
                val_v = cell_v.value
                
                if val_d is not None or val_v is not None:
                    non_empty_count += 1
                    col_letter = openpyxl.utils.get_column_letter(c)
                    
                    is_formula = isinstance(val_d, str) and val_d.startswith("=")
                    if is_formula:
                        formulas.append({
                            "cell": f"{col_letter}{r}",
                            "formula": str(val_d),
                            "evaluated_value": str(val_v)
                        })
                        
                    cell_info = {
                        "cell": f"{col_letter}{r}",
                        "col": c,
                        "col_letter": col_letter,
                        "raw": str(val_d),
                        "eval": str(val_v),
                        "is_formula": is_formula,
                        "type": type(val_v if val_v is not None else val_d).__name__,
                        "number_format": cell_d.number_format
                    }
                    row_cells.append(cell_info)
                    
                    if c not in columns_dict:
                        columns_dict[c] = {
                            "col_index": c,
                            "col_letter": col_letter,
                            "sample_values": [],
                            "data_types": set(),
                            "has_formulas": False
                        }
                    if len(columns_dict[c]["sample_values"]) < 5 and val_v is not None:
                        columns_dict[c]["sample_values"].append(str(val_v))
                    columns_dict[c]["data_types"].add(type(val_v if val_v is not None else val_d).__name__)
                    if is_formula:
                        columns_dict[c]["has_formulas"] = True

            if row_cells:
                rows_layout[r] = {
                    "row_number": r,
                    "cell_count": non_empty_count,
                    "cells": row_cells
                }
                
        col_list = []
        for c in sorted(columns_dict.keys()):
            columns_dict[c]["data_types"] = list(columns_dict[c]["data_types"])
            col_list.append(columns_dict[c])
            
        file_info["sheets"][sheet_name] = {
            "sheet_name": sheet_name,
            "max_row": max_r,
            "max_column": max_c,
            "merged_ranges_count": len(merged_ranges),
            "merged_ranges": merged_ranges,
            "hidden_rows": hidden_rows,
            "hidden_cols": hidden_cols,
            "formula_count": len(formulas),
            "formulas": formulas,
            "columns": col_list,
            "rows_populated_count": len(rows_layout),
            "rows_layout": rows_layout
        }
        
    return file_info

files = glob.glob("/home/sanjana/acc-rmc-ai-platform/data/raw/**/*.xlsx", recursive=True)
full_report = {}
for f in sorted(files):
    rel = os.path.relpath(f, "/home/sanjana/acc-rmc-ai-platform/data/raw")
    full_report[rel] = inspect_file(f)

with open("/home/sanjana/acc-rmc-ai-platform/data/raw/exhaustive_inspection.json", "w") as out:
    json.dump(full_report, out, indent=2)

print("Exhaustive inspection completed successfully!")
