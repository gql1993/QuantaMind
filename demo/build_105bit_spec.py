"""从 105 比特设计文档提取参数并生成芯片规格文件"""
import json

with open("docs/105bit_tables.json", "r", encoding="utf-8") as f:
    tables = json.load(f)

# Table 12: 比特完整参数（107 行 = 1 header + 1 unit + 105 data rows）
t12 = [t for t in tables if t["table_index"] == 12][0]
headers_raw = t12["headers"]
rows = t12["rows"]

# 跳过单位行
unit_row = rows[0] if rows and rows[0][0] == "" else None
data_rows = rows[1:] if unit_row else rows

qubits = []
couplers = []
for row in data_rows:
    if len(row) < 5:
        continue
    idx = row[0].strip()
    name = row[1].strip()
    bit_id = row[2].strip() if len(row) > 2 else ""
    freq = row[3].strip() if len(row) > 3 else ""
    res_freq = row[4].strip() if len(row) > 4 else ""
    res_q = row[5].strip() if len(row) > 5 else ""

    if not name:
        continue

    try:
        freq_val = float(freq) if freq and freq != "-" else None
    except ValueError:
        freq_val = None

    try:
        res_freq_val = float(res_freq) if res_freq and res_freq != "-" else None
    except ValueError:
        res_freq_val = None

    if name.startswith("Q"):
        qubits.append({
            "id": name, "bit_id": bit_id, "freq_ghz": freq_val,
            "res_freq_ghz": res_freq_val, "res_q": res_q,
        })
    elif "耦合" in name or name.startswith("C") or name.startswith("T"):
        couplers.append({
            "id": name, "freq_ghz": freq_val,
        })

# Table 9: 谐振腔详细参数
t9 = [t for t in tables if t["table_index"] == 9][0]
resonators = {}
for row in t9["rows"][1:]:  # skip unit row
    if len(row) >= 5 and row[0].startswith("Q"):
        try:
            resonators[row[0]] = {
                "target_freq_ghz": float(row[1]) if row[1] else None,
                "sim_freq_ghz": float(row[2]) if row[2] else None,
                "q_value": float(row[3]) if row[3] and row[3] != "\\" else None,
                "total_length_um": float(row[4]) if row[4] else None,
            }
        except (ValueError, IndexError):
            pass

# 合并谐振腔数据到 qubits
for q in qubits:
    if q["id"] in resonators:
        q.update(resonators[q["id"]])

spec = {
    "doc_id": "GJQ-200-000-FA09-2025",
    "name": "105比特可调耦合器超导量子芯片",
    "total_qubits": len(qubits),
    "total_couplers": len(couplers),
    "topology": "二维网格结构（2D grid）",
    "qubit_type": "Xmon（固定频率）",
    "coupler_type": "可调耦合器（Transmon + SQUID）",
    "targets": {
        "qubit_count": 105,
        "coupler_count": "≥180",
        "single_gate_fidelity": "99%（≥70比特）",
        "two_gate_fidelity": "99%（≥70比特）",
        "readout_fidelity": "95%（≥70比特）",
        "T1_avg_us": "≥50",
        "T2_avg_us": "≥30",
        "freq_error": "≤3%",
        "resonator_freq_error": "≤3%",
        "film": "钽膜 Tc≥1.2K",
    },
    "qubits": qubits,
    "couplers": couplers,
}

out_path = "quantamind/server/chip_105bit_spec.py"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# 105比特可调耦合器量子芯片规格（自动从设计文档提取）\n\n")
    f.write("CHIP_105BIT_SPEC = ")
    f.write(json.dumps(spec, ensure_ascii=False, indent=2))
    f.write("\n")

print(f"Generated: {out_path}")
print(f"  Qubits: {len(qubits)}")
print(f"  Couplers: {len(couplers)}")
print(f"  Resonators with sim data: {len(resonators)}")
for q in qubits[:5]:
    print(f"    {q['id']}: {q.get('freq_ghz')}GHz, res={q.get('res_freq_ghz')}GHz")
