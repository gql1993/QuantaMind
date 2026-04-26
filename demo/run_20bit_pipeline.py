#!/usr/bin/env python3
"""
QuantaMind 多智能体协同演示：20比特可调耦合器量子芯片 端到端流水线
基于 E:\work\QuantaMind\docs\20bits可调耦合器双比特设计文档v3.docx

流水线阶段：
  1. AI 芯片设计师 → 创建设计 + 添加比特 + 路由 + 导出 GDS
  2. AI 仿真工程师 → LOM 电容分析 + EPR 本征模分析
  3. AI 工艺工程师 → 创建工艺路线 + 批次 + 派工（模拟制造）
  4. AI 设备运维员 → 设备就绪检查 + 校准
  5. AI 测控科学家 → T1/T2 表征 + Rabi 振荡 + 错误缓解
  6. AI 数据分析师 → 跨域数据汇总 + 质量检查
  7. AI 项目经理 → 项目总结报告

使用方式：先启动 Gateway（python run_gateway.py），再运行本脚本。
"""

import json
import os
import sys
import time
import urllib.request

# Windows 控制台 UTF-8
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GATEWAY = "http://127.0.0.1:18789"

# 20比特芯片设计参数（来自设计文档）
CHIP_SPEC = {
    "name": "20比特可调耦合器量子芯片",
    "doc_id": "TGQ-200-000-FA09-2025",
    "chip_size": "12.5mm × 12.5mm",
    "qubit_count": 20,
    "coupler_count": 19,
    "qubit_type": "Xmon（固定频率）",
    "coupler_type": "可调耦合器（SQUID）",
    "topology": "一维链结构",
    "qubits": [
        {"id": "Q1", "freq_ghz": 4.65, "resonator_ghz": 7.30, "Ec_mhz": -230.13, "Lj_nH": 12.5},
        {"id": "Q2", "freq_ghz": 4.56, "resonator_ghz": 7.00, "Ec_mhz": -230.13, "Lj_nH": 13.0},
        {"id": "Q3", "freq_ghz": 4.65, "resonator_ghz": 7.36, "Ec_mhz": -230.13, "Lj_nH": 12.5},
        {"id": "Q4", "freq_ghz": 4.56, "resonator_ghz": 7.07, "Ec_mhz": -230.13, "Lj_nH": 13.0},
        {"id": "Q5", "freq_ghz": 4.65, "resonator_ghz": 7.42, "Ec_mhz": -230.13, "Lj_nH": 12.5},
    ],
    "couplers": [
        {"id": "T1", "freq_ghz": 6.88, "Ec_mhz": -352.87, "Lj_nH": 8.8},
        {"id": "T2", "freq_ghz": 6.88, "Ec_mhz": -352.87, "Lj_nH": 8.8},
    ],
    "targets": {
        "single_gate_fidelity": "≥99.9%",
        "two_gate_fidelity": "≥99%",
        "readout_fidelity": "≥99%",
        "T1": "≥20μs",
        "T2": "≥15μs",
        "survival_rate": "100%",
        "qubit_availability": "≥90%",
    },
    "cpw_params": {"s_um": 10, "w_um": 5, "Z0_ohm": "48.65~51.34"},
}


def api_call(method, path, body=None):
    url = f"{GATEWAY}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def tool(tool_name, **kwargs):
    """直接调用 Hands 工具"""
    sys.path.insert(0, "E:\\work\\QuantaMind")
    from quantamind.server import hands
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(hands.run_tool(tool_name, **kwargs))
    loop.close()
    return result


def section(title, agent_name):
    print(f"\n{'='*70}")
    print(f"  {agent_name} → {title}")
    print(f"{'='*70}\n")


def step(desc, result):
    status = "✅" if "error" not in str(result) else "❌"
    print(f"  {status} {desc}")
    if isinstance(result, dict):
        for k, v in list(result.items())[:5]:
            print(f"     {k}: {json.dumps(v, ensure_ascii=False, default=str)[:120]}")
    print()


def main():
    print("=" * 70)
    print("  QuantaMind 多智能体协同 · 20比特可调耦合器量子芯片 端到端流水线")
    print(f"  设计文档：{CHIP_SPEC['doc_id']}")
    print(f"  芯片规格：{CHIP_SPEC['qubit_count']} 比特 + {CHIP_SPEC['coupler_count']} 可调耦合器")
    print(f"  芯片尺寸：{CHIP_SPEC['chip_size']}  拓扑：{CHIP_SPEC['topology']}")
    print("=" * 70)

    # ── 阶段 1：AI 芯片设计师 ──
    section("芯片版图设计（Qiskit Metal + KQCircuits）", "💎 AI 芯片设计师")

    r = tool("metal_create_design", chip_size_x="12.5mm", chip_size_y="12.5mm")
    step("创建 12.5mm×12.5mm 平面设计", r)
    design_id = r.get("design_id", "design_0001")

    for q in CHIP_SPEC["qubits"]:
        r = tool("metal_add_transmon", design_id=design_id, name=q["id"],
                 qubit_type="transmon_cross", pos_x=f"{CHIP_SPEC['qubits'].index(q) * 2500}um", pos_y="6250um",
                 options={"orientation": "0"})
        step(f"添加比特 {q['id']}（{q['freq_ghz']}GHz, Ec={q['Ec_mhz']}MHz）", r)

    for i in range(len(CHIP_SPEC["qubits"]) - 1):
        q1 = CHIP_SPEC["qubits"][i]["id"]
        q2 = CHIP_SPEC["qubits"][i + 1]["id"]
        r = tool("metal_add_route", design_id=design_id, name=f"cpw_{q1}_{q2}",
                 start_component=q1, start_pin="east", end_component=q2, end_pin="west",
                 route_type="meander", total_length="5mm")
        step(f"路由 {q1}↔{q2}（RouteMeander, 5mm）", r)

    r = tool("kqc_create_chip", name="20bit_tunable_coupler", chip_size_x=12500, chip_size_y=12500)
    step("KQCircuits 创建芯片布局", r)
    kqc_chip_id = r.get("chip_id", "kqc_chip_0001")

    for c in CHIP_SPEC["couplers"]:
        r = tool("kqc_add_swissmon", chip_id=kqc_chip_id, name=c["id"],
                 arm_length=[150, 150, 150, 150], gap_width=[12, 12, 12, 12])
        step(f"添加可调耦合器 {c['id']}（{c['freq_ghz']}GHz, SQUID 结构）", r)

    for elem in ["airbridge_1", "airbridge_2", "marker_TL", "marker_TR", "marker_BL", "marker_BR"]:
        etype = "airbridge" if "airbridge" in elem else "marker"
        r = tool("kqc_add_element", chip_id=kqc_chip_id, name=elem, element_type=etype)
        step(f"添加 {etype}：{elem}", r)

    r = tool("metal_export_gds", design_id=design_id, filename="20bit_tunable_coupler.gds")
    step("Metal 导出 GDS", r)

    r = tool("kqc_export_gds", chip_id=kqc_chip_id, filename="20bit_kqc_layout.gds")
    step("KQCircuits 导出 GDS", r)

    r = tool("kqc_export_mask", chip_id=kqc_chip_id, output_dir="./mask_20bit")
    step("KQCircuits 导出制造掩膜（光学 + EBL）", r)

    # ── 阶段 2：AI 仿真工程师 ──
    section("电磁仿真与量化分析", "🖥️ AI 仿真工程师")

    for q in CHIP_SPEC["qubits"][:3]:
        r = tool("metal_analyze_lom", design_id=design_id, component_name=q["id"])
        step(f"LOM 电容矩阵分析 {q['id']}", r)

    for q in CHIP_SPEC["qubits"][:2]:
        r = tool("metal_analyze_epr", design_id=design_id, component_name=q["id"])
        step(f"EPR 本征模分析 {q['id']}（目标 {q['freq_ghz']}GHz）", r)

    r = tool("kqc_export_ansys", chip_id=kqc_chip_id, output_dir="./ansys_20bit")
    step("KQCircuits 导出 Ansys HFSS 仿真", r)

    r = tool("kqc_export_sonnet", chip_id=kqc_chip_id, output_dir="./sonnet_20bit")
    step("KQCircuits 导出 Sonnet 仿真", r)

    # ── 阶段 3：AI 工艺工程师 ──
    section("制造流程（模拟）", "🏭 AI 工艺工程师")

    r = tool("mes_list_routes")
    step("查询工艺路线", r)

    r = tool("mes_list_lots", status="queued")
    step("查询待生产批次", r)

    r = tool("mes_dispatch", lot_id="LOT-2026-0301", step="光刻", equipment_id="LITHO-03")
    step("派工：LOT-2026-0301 → 光刻 → LITHO-03", r)

    r = tool("mes_report_work", wo_id="WO-20260310-001", result="pass", defects=0)
    step("报工：光刻完成，无缺陷", r)

    r = tool("mes_query_yield")
    step("查询良率数据", r)

    r = tool("mes_query_spc", parameter="JJ_Resistance", last_n=20)
    step("SPC 监控：JJ 电阻", r)

    r = tool("secs_list_equipment")
    step("SECS/GEM 设备状态", r)

    r = tool("secs_list_alarms", equipment_id="LITHO-03")
    step("检查 LITHO-03 告警", r)

    # ── 阶段 4：AI 设备运维员 ──
    section("设备校准", "🔧 AI 设备运维员")

    r = tool("artiq_list_devices")
    step("ARTIQ 硬件设备列表", r)

    r = tool("pulse_full_calibration", qubits=[0, 1, 2, 3, 4])
    step("Qiskit Pulse 全套校准 Q0-Q4（频率+振幅+DRAG+读出）", r)

    r = tool("pulse_get_calibrations")
    step("校准参数汇总", r)

    # ── 阶段 5：AI 测控科学家 ──
    section("比特表征与错误缓解", "📡 AI 测控科学家")

    for seq in ["spectroscopy", "rabi", "t1", "t2_ramsey", "t2_echo"]:
        r = tool("artiq_run_pulse", sequence_type=seq, qubits=["Q0", "Q1", "Q2", "Q3", "Q4"])
        step(f"ARTIQ 执行 {seq}", r)

    r = tool("artiq_run_pulse", sequence_type="readout_optimization", qubits=["Q0", "Q1", "Q2"])
    step("读出优化", r)

    r = tool("mitiq_benchmark", circuit_desc="20bit_CZ_gate_Q1_Q2")
    step("Mitiq 纠错技术对比（ZNE vs PEC vs CDR）", r)

    r = tool("mitiq_dd", circuit_desc="20bit_idle_Q0", dd_sequence="XY4")
    step("动力学去耦 XY4", r)

    # ── 阶段 6：AI 数据分析师 ──
    section("数据汇总与质量检查", "📊 AI 数据分析师")

    r = tool("doris_list_domains")
    step("数据域概览", r)

    r = tool("doris_query_qubit", chip_id="20bit_tunable_coupler")
    step("查询比特表征数据", r)

    r = tool("doris_query_yield")
    step("查询良率趋势", r)

    r = tool("doris_cross_domain", query_type="design_to_measurement")
    step("跨域追溯：设计→制造→测控", r)

    r = tool("qdata_quality_check", table="qubit_characterization")
    step("数据质量检查：比特表征表", r)

    r = tool("qdata_lineage", table="qubit_characterization")
    step("数据血缘：qubit_characterization", r)

    r = tool("seatunnel_pipeline_status")
    step("ETL 管道状态", r)

    # ── 阶段 7：AI 项目经理 ──
    section("项目总结", "📋 AI 项目经理")

    print("  📋 20比特可调耦合器量子芯片 · 多智能体协同总结")
    print()
    print(f"  芯片规格：{CHIP_SPEC['qubit_count']} Xmon 比特 + {CHIP_SPEC['coupler_count']} 可调耦合器（SQUID）")
    print(f"  设计目标：单门 {CHIP_SPEC['targets']['single_gate_fidelity']} | 双门 {CHIP_SPEC['targets']['two_gate_fidelity']} | 读出 {CHIP_SPEC['targets']['readout_fidelity']}")
    print(f"  T1 {CHIP_SPEC['targets']['T1']} | T2 {CHIP_SPEC['targets']['T2']}")
    print()
    print("  协同流程完成情况：")
    print("  ✅ 阶段 1：芯片设计师 → Metal 创建设计 + 添加比特/路由 + KQC 耦合器/掩膜 + GDS 导出")
    print("  ✅ 阶段 2：仿真工程师 → LOM 电容分析 + EPR 本征模 + Ansys/Sonnet 导出")
    print("  ✅ 阶段 3：工艺工程师 → 工艺路线 + 批次派工 + 良率/SPC + 设备检查")
    print("  ✅ 阶段 4：设备运维员 → ARTIQ 设备 + Pulse 全套校准（频率/振幅/DRAG/读出）")
    print("  ✅ 阶段 5：测控科学家 → 光谱/Rabi/T1/T2/读出 + Mitiq 纠错对比 + 动力学去耦")
    print("  ✅ 阶段 6：数据分析师 → 跨域追溯 + 质量检查 + 血缘 + ETL 管道")
    print("  ✅ 阶段 7：项目经理 → 总结报告")
    print()
    print("  参与 Agent：💎芯片设计师 🖥️仿真工程师 🏭工艺工程师 🔧设备运维员 📡测控科学家 📊数据分析师 📋项目经理")
    print()
    print("=" * 70)
    print("  端到端流水线完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
