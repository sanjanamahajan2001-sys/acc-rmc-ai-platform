import json

with open('/home/sanjana/acc-rmc-ai-platform/data/raw/exhaustive_inspection.json') as f:
    data = json.load(f)

for rel, wb in data.items():
    print('========================================')
    print('WORKBOOK:', rel)
    print('Total Sheets:', wb['sheet_count'])
    for sname, s in wb['sheets'].items():
        print(f"  Sheet [{sname}]: max_row={s['max_row']}, max_col={s['max_column']}, merged={s['merged_ranges_count']}, formulas={s['formula_count']}, pop_rows={s['rows_populated_count']}")
