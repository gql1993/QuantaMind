"""提取 105 比特设计文档中的表格数据"""
from docx import Document
import json

doc = Document("docs/QEDA/105比特可调耦合器量子芯片设计方案0120.docx")
tables_data = []
for i, table in enumerate(doc.tables):
    rows = []
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        rows.append(cells)
    if rows and any(any(c for c in r) for r in rows):
        tables_data.append({"table_index": i, "headers": rows[0], "rows": rows[1:], "row_count": len(rows) - 1})

with open("docs/105bit_tables.json", "w", encoding="utf-8") as f:
    json.dump(tables_data, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(tables_data)} tables")
for t in tables_data:
    h = t["headers"][:5]
    print(f"  Table {t['table_index']}: {h} ({t['row_count']} rows)")
