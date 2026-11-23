import json

with open('/home/sanjana/acc-rmc-ai-platform/data/raw/inspection_summary.json') as f:
    data = json.load(f)

for path, wb in data.items():
    print('========================================')
    print('WORKBOOK:', path)
    for sname, sinfo in wb['sheet_details'].items():
        print(f'--- Sheet: {sname} ---')
        for r in sinfo['sample_rows'][:5]:
            cell_strs = []
            for c in r['cells']:
                cell_strs.append(f"C{c['col']}({c['col_letter']}): {c['raw_value']}")
            row_str = " | ".join(cell_strs)
            print(f"Row {r['row']}: {row_str[:250]}")
