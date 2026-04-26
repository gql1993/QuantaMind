# 工具执行结果的结构化中文解释生成器
# 每个工具返回的 JSON 都会被翻译成人类可读的表格和说明

import json
from typing import Any, Dict, List, Tuple


def explain(tool_name: str, args: dict, result: Any) -> Dict[str, Any]:
    """为工具结果生成：data_table（表格数据）、explanation（中文解释）、data_format（数据格式说明）"""
    if not isinstance(result, dict):
        return {"explanation": str(result), "data_table": None, "data_format": "raw"}

    fn = EXPLAINERS.get(tool_name, _default_explain)
    return fn(args, result)


def _default_explain(args: dict, r: dict) -> dict:
    rows = [[k, json.dumps(v, ensure_ascii=False, default=str)[:200]] for k, v in r.items()]
    return {"explanation": "工具执行完成。", "data_table": {"headers": ["字段", "值"], "rows": rows}, "data_format": "JSON Key-Value"}


def _explain_metal_create_design(args, r):
    return {
        "explanation": f"已创建 Qiskit Metal 平面设计，设计 ID 为 {r.get('design_id')}，芯片尺寸 {r.get('size', ['?','?'])[0]} x {r.get('size', ['?','?'])[1]}。后端：{r.get('backend')}。",
        "data_table": {"headers": ["参数", "值"], "rows": [["设计 ID", r.get("design_id")], ["类型", r.get("type")], ["尺寸", f"{r.get('size', ['?','?'])[0]} x {r.get('size', ['?','?'])[1]}"], ["后端", r.get("backend")]]},
        "data_format": "设计元数据（design_id: str, type: str, size: [str, str], backend: str）",
    }


def _explain_metal_add_transmon(args, r):
    return {
        "explanation": f"已在设计中添加 {r.get('type')} 类型量子比特 {r.get('component')}，位置 ({r.get('position', ['?','?'])[0]}, {r.get('position', ['?','?'])[1]})。",
        "data_table": {"headers": ["参数", "值"], "rows": [["组件名", r.get("component")], ["类型", r.get("type")], ["X 坐标", r.get("position", ["?"])[0]], ["Y 坐标", r.get("position", ["?","?"])[1]], ["后端", r.get("backend")]]},
        "data_format": "组件信息（component: str, type: str, position: [str, str]）",
    }


def _explain_metal_add_route(args, r):
    return {
        "explanation": f"已添加 {r.get('type')} 类型 CPW 路由 {r.get('route')}，从 {r.get('from')} 到 {r.get('to')}。",
        "data_table": {"headers": ["参数", "值"], "rows": [["路由名", r.get("route")], ["类型", r.get("type")], ["起点", r.get("from")], ["终点", r.get("to")]]},
        "data_format": "路由信息（route: str, type: str, from: str, to: str）",
    }


def _explain_metal_analyze_lom(args, r):
    mock = r.get("mock_result", {})
    matrix = mock.get("C_matrix_fF", [])
    rows = []
    for i, row in enumerate(matrix):
        rows.append([f"C[{i}][j]"] + [f"{v:.1f} fF" for v in row])
    headers = [""] + [f"pad_{j}" for j in range(len(matrix))]
    return {
        "explanation": f"对组件 {r.get('component')} 执行 LOM（集总振荡模型）电容矩阵分析。对角线为自电容，非对角线为互电容（耦合强度）。电容值单位 fF（飞法拉）。",
        "data_table": {"headers": headers, "rows": rows} if rows else None,
        "data_format": "电容矩阵 C_matrix_fF: float[][]（单位 fF），对称矩阵",
    }


def _explain_metal_analyze_epr(args, r):
    mock = r.get("mock_result", {})
    return {
        "explanation": f"对组件 {r.get('component')} 执行 EPR（能量参与率）本征模分析。得到谐振频率 {mock.get('freq_ghz', '?')} GHz，非简谐性 {mock.get('anharmonicity_mhz', '?')} MHz，品质因子 Q={mock.get('Q_factor', '?')}。",
        "data_table": {"headers": ["指标", "值", "单位", "说明"], "rows": [
            ["谐振频率", str(mock.get("freq_ghz", "?")), "GHz", "量子比特基频"],
            ["非简谐性", str(mock.get("anharmonicity_mhz", "?")), "MHz", "Ec，用于区分量子态"],
            ["品质因子", str(mock.get("Q_factor", "?")), "", "越高表示损耗越低"],
        ]},
        "data_format": "EPR 结果（freq_ghz: float, anharmonicity_mhz: float, Q_factor: int）",
    }


def _explain_metal_export_gds(args, r):
    return {
        "explanation": f"已将设计导出为 GDS 文件：{r.get('exported')}。GDS 是半导体行业标准的版图交换格式，可用于流片制造。",
        "data_table": {"headers": ["参数", "值"], "rows": [["文件名", r.get("exported")], ["后端", r.get("backend")]]},
        "data_format": "文件路径（exported: str）",
    }


def _explain_kqc_create_chip(args, r):
    return {
        "explanation": f"已创建 KQCircuits 芯片布局 {r.get('name')}，尺寸 {r.get('size_um', ['?','?'])[0]}um x {r.get('size_um', ['?','?'])[1]}um。",
        "data_table": {"headers": ["参数", "值"], "rows": [["芯片 ID", r.get("chip_id")], ["名称", r.get("name")], ["尺寸", f"{r.get('size_um', ['?','?'])[0]} x {r.get('size_um', ['?','?'])[1]} um"]]},
        "data_format": "芯片元数据（chip_id: str, name: str, size_um: [float, float]）",
    }


def _explain_kqc_add_swissmon(args, r):
    params = r.get("params", {})
    return {
        "explanation": f"已添加 Swissmon（IQM 四臂 Transmon）量子比特 {r.get('element')}，臂长 {params.get('arm_length')} um，臂宽 {params.get('arm_width')} um，间距 {params.get('gap_width')} um。",
        "data_table": {"headers": ["参数", "值", "单位"], "rows": [
            ["元件名", r.get("element"), ""], ["臂长（WNES）", str(params.get("arm_length")), "um"],
            ["臂宽（WNES）", str(params.get("arm_width")), "um"], ["间距（WNES）", str(params.get("gap_width")), "um"],
        ]},
        "data_format": "Swissmon 参数（arm_length/arm_width/gap_width: float[4]，单位 um）",
    }


def _explain_mes_query_yield(args, r):
    data = r.get("yield_data", [])
    rows = [[d.get("lot_id", ""), f"{d.get('yield_pct', 0):.1f}%", str(d.get("defects", 0)), str(d.get("total", 0))] for d in data]
    return {
        "explanation": f"查询到 {len(data)} 条良率记录，平均良率 {r.get('average_yield_pct', '?')}%。良率 = (总数 - 缺陷数) / 总数 x 100%。",
        "data_table": {"headers": ["批次 ID", "良率", "缺陷数", "总数"], "rows": rows},
        "data_format": "良率记录（lot_id: str, yield_pct: float, defects: int, total: int）",
    }


def _explain_mes_query_spc(args, r):
    data = r.get("data", [])[:5]
    rows = [[d.get("lot", ""), f"{d.get('value', 0):.1f}", str(d.get("ucl")), str(d.get("lcl")), str(d.get("mean"))] for d in data]
    return {
        "explanation": f"SPC（统计过程控制）监控参数 {r.get('parameter')}，共 {r.get('total', 0)} 个数据点，{r.get('out_of_control', 0)} 个失控点。UCL=上控制限，LCL=下控制限。",
        "data_table": {"headers": ["批次", "测量值", "UCL", "LCL", "均值"], "rows": rows},
        "data_format": "SPC 数据（lot: str, value: float, ucl: float, lcl: float, mean: float）",
    }


def _explain_pulse_full_calibration(args, r):
    cal = r.get("full_calibration", {})
    rows = []
    for qkey, qval in cal.items():
        freq = qval.get("frequency", {}).get("precise_freq_ghz", "?")
        amp = qval.get("amplitude_X", {}).get("optimal_amp", "?")
        drag = qval.get("drag_X", {}).get("optimal_beta", "?")
        ro_fid = qval.get("readout", {}).get("readout_fidelity_pct", "?")
        rows.append([qkey, str(freq), str(amp), str(drag), f"{ro_fid}%"])
    return {
        "explanation": f"对 {len(cal)} 个比特执行全套校准：频率（Ramsey）→ 振幅（Rabi）→ DRAG → 读出优化。",
        "data_table": {"headers": ["比特", "频率 (GHz)", "X 门振幅", "DRAG beta", "读出保真度"], "rows": rows},
        "data_format": "校准参数（freq_ghz: float, amplitude: float, drag_beta: float, readout_fidelity_pct: float）",
    }


def _explain_artiq_run_pulse(args, r):
    seq = r.get("sequence", "")
    result = r.get("result", {})
    rows = [[k, str(v)] for k, v in result.items()]
    desc_map = {
        "spectroscopy": "量子比特频率光谱扫描，找到比特谐振频率。",
        "rabi": "Rabi 振荡测量，确定 pi 脉冲的最优驱动参数。",
        "t1": "T1 纵向弛豫时间测量，衡量比特能量衰减速度。",
        "t2_ramsey": "T2* Ramsey 退相干时间测量，衡量比特相位稳定性。",
        "t2_echo": "T2 Echo（Hahn Echo）测量，去除低频噪声后的退相干时间。",
        "readout_optimization": "读出参数优化，提高量子态 |0⟩ 和 |1⟩ 的区分度。",
    }
    return {
        "explanation": f"ARTIQ 执行脉冲序列 {seq}。{desc_map.get(seq, '')} 比特：{r.get('qubits', [])}。",
        "data_table": {"headers": ["测量指标", "值"], "rows": rows},
        "data_format": f"{seq} 结果（{', '.join(f'{k}: {type(v).__name__}' for k,v in result.items())}）",
    }


def _explain_mitiq_benchmark(args, r):
    bench = r.get("benchmark", [])
    rows = [[b.get("technique"), str(b.get("mitigated_value")), b.get("cost", "")] for b in bench]
    return {
        "explanation": f"对比 {len(bench)} 种量子错误缓解技术。推荐使用 {r.get('recommended', '?')}。原因：{r.get('reason', '')}。",
        "data_table": {"headers": ["技术", "缓解后期望值", "计算成本"], "rows": rows},
        "data_format": "基准测试（technique: str, mitigated_value: float, cost: str）",
    }


def _explain_mitiq_dd(args, r):
    return {
        "explanation": f"动力学去耦（{r.get('dd_sequence', 'XY4')}）：在空闲时间插入脉冲序列抑制退相干。T2 从 {r.get('T2_before_us', '?')}μs 提升到 {r.get('T2_after_us', '?')}μs，改善倍数 {r.get('improvement_factor', '?')}。",
        "data_table": {"headers": ["指标", "值", "单位"], "rows": [
            ["DD 序列", r.get("dd_sequence", ""), ""], ["T2（去耦前）", str(r.get("T2_before_us", "?")), "μs"],
            ["T2（去耦后）", str(r.get("T2_after_us", "?")), "μs"], ["改善倍数", str(r.get("improvement_factor", "?")), "x"],
        ]},
        "data_format": "DD 结果（T2_before_us: float, T2_after_us: float, improvement_factor: float）",
    }


def _explain_doris_cross_domain(args, r):
    ex = r.get("example_result", {})
    rows = [[k, str(v)] for k, v in ex.items()]
    return {
        "explanation": f"跨域关联查询（{r.get('query', '')}）：从设计追溯到制造批次再到测控表征结果，实现全链路数据贯通。",
        "data_table": {"headers": ["字段", "值"], "rows": rows},
        "data_format": "跨域关联（design_id → lot_id → chip_id → 表征数据）",
    }


def _explain_qdata_quality_check(args, r):
    return {
        "explanation": f"对表 {r.get('table')} 执行数据质量检查：共 {r.get('total_records', 0)} 条记录，发现 {r.get('issues_found', 0)} 个问题，质量得分 {r.get('quality_score', 0)}%。检查项包括：{', '.join(r.get('checks', []))}。",
        "data_table": {"headers": ["指标", "值"], "rows": [
            ["表名", r.get("table", "")], ["总记录数", str(r.get("total_records", 0))],
            ["问题数", str(r.get("issues_found", 0))], ["质量得分", f"{r.get('quality_score', 0)}%"],
        ]},
        "data_format": "质量报告（total_records: int, issues_found: int, quality_score: float）",
    }


def _explain_qexp_generic(args, r):
    rows = []
    for item in r.get("analysis", []):
        if isinstance(item, dict):
            rows.append([item.get("qubit", "")] + [str(v) for k, v in item.items() if k != "qubit"][:4])
    headers = ["比特", "指标1", "指标2", "指标3", "指标4"] if rows else None
    return {
        "explanation": f"{r.get('experiment_type', 'Qiskit Experiments')} 标准实验完成。实验类：{r.get('experiment_class', '')}。建议：{r.get('recommended_action', '')}",
        "data_table": {"headers": headers, "rows": rows} if rows else None,
        "data_format": "标准实验结果（experiment_type, experiment_class, analysis[], recommended_action）",
    }


EXPLAINERS = {
    "metal_create_design": _explain_metal_create_design,
    "metal_add_transmon": _explain_metal_add_transmon,
    "metal_add_route": _explain_metal_add_route,
    "metal_analyze_lom": _explain_metal_analyze_lom,
    "metal_analyze_epr": _explain_metal_analyze_epr,
    "metal_export_gds": _explain_metal_export_gds,
    "kqc_create_chip": _explain_kqc_create_chip,
    "kqc_add_swissmon": _explain_kqc_add_swissmon,
    "kqc_export_mask": lambda a, r: {"explanation": f"已导出制造掩膜（光学 + EBL）到 {r.get('exported')}。掩膜用于量子芯片的光刻和电子束曝光工艺。", "data_table": {"headers": ["参数", "值"], "rows": [["输出目录", r.get("exported", "")], ["格式", r.get("format", "")]]}, "data_format": "文件路径"},
    "kqc_export_ansys": lambda a, r: {"explanation": f"已导出 Ansys HFSS 仿真文件到 {r.get('exported')}。HFSS 用于电磁场全波仿真，提取谐振频率和品质因子。", "data_table": {"headers": ["参数", "值"], "rows": [["输出目录", r.get("exported", "")], ["格式", r.get("format", "")]]}, "data_format": "仿真文件路径"},
    "mes_list_routes": lambda a, r: {"explanation": f"查询到 {len(r.get('routes', []))} 条工艺路线。工艺路线定义了芯片从原材料到成品的全部工序。", "data_table": {"headers": ["路线 ID", "名称", "工序数", "产品"], "rows": [[rt.get("route_id"), rt.get("name"), str(len(rt.get("steps", []))), rt.get("product", "")] for rt in r.get("routes", [])]}, "data_format": "工艺路线（route_id, name, steps[], product）"},
    "mes_dispatch": lambda a, r: {"explanation": f"已将批次 {r.get('lot_id')} 派工到设备 {r.get('equipment_id')} 的 {r.get('step')} 工步。", "data_table": {"headers": ["参数", "值"], "rows": [["批次", r.get("lot_id", "")], ["工步", r.get("step", "")], ["设备", r.get("equipment_id", "")], ["状态", r.get("status", "")]]}, "data_format": "派工记录"},
    "mes_report_work": lambda a, r: {"explanation": f"工单 {r.get('wo_id')} 报工完成，结果 {r.get('result')}，缺陷数 {r.get('defects')}。", "data_table": {"headers": ["参数", "值"], "rows": [["工单", r.get("wo_id", "")], ["结果", r.get("result", "")], ["缺陷数", str(r.get("defects", 0))]]}, "data_format": "报工记录"},
    "mes_query_yield": _explain_mes_query_yield,
    "mes_query_spc": _explain_mes_query_spc,
    "secs_list_alarms": lambda a, r: {"explanation": f"设备 {r.get('equipment_id')} 告警列表：{len(r.get('alarms', []))} 条告警。", "data_table": {"headers": ["告警"], "rows": [[a] for a in r.get("alarms", [])]} if r.get("alarms") else None, "data_format": "告警列表"},
    "artiq_list_devices": lambda a, r: {"explanation": f"ARTIQ 硬件设备共 {r.get('count', 0)} 个。", "data_table": {"headers": ["设备名", "类型", "说明"], "rows": [[d.get("name"), d.get("type"), d.get("desc", "")] for d in r.get("devices", [])]}, "data_format": "设备列表（name, type, desc）"},
    "pulse_full_calibration": _explain_pulse_full_calibration,
    "artiq_run_pulse": _explain_artiq_run_pulse,
    "qexp_t1": _explain_qexp_generic,
    "qexp_ramsey": _explain_qexp_generic,
    "qexp_rabi": _explain_qexp_generic,
    "qexp_readout": _explain_qexp_generic,
    "qexp_drag": _explain_qexp_generic,
    "qexp_batch_characterization": lambda a, r: {"explanation": f"已执行 Qiskit Experiments 批量标准表征，覆盖 {len(r.get('qubits', []))} 个比特。建议：{r.get('recommended_action', '')}", "data_table": {"headers": ["实验", "后端"], "rows": [[k, v.get('backend', '')] for k, v in (r.get('experiments', {}) or {}).items()]}, "data_format": "批量标准表征结果（experiments: dict）"},
    "mitiq_benchmark": _explain_mitiq_benchmark,
    "mitiq_dd": _explain_mitiq_dd,
    "doris_list_domains": lambda a, r: {"explanation": f"数据中台共 {len(r.get('domains', []))} 个数据域。", "data_table": {"headers": ["域", "说明", "表数", "行数"], "rows": [[d.get("domain"), d.get("description", "")[:30], str(d.get("tables", 0)), str(d.get("total_rows", 0))] for d in r.get("domains", [])]}, "data_format": "数据域元数据"},
    "warehouse_list_domains": lambda a, r: {"explanation": f"数据中台（OLAP）共 {len(r.get('domains', []))} 个数据域。", "data_table": {"headers": ["域", "说明", "表数", "行数"], "rows": [[d.get("domain"), d.get("description", "")[:30], str(d.get("tables", 0)), str(d.get("total_rows", 0))] for d in r.get("domains", [])]}, "data_format": "数据域元数据"},
    "doris_cross_domain": _explain_doris_cross_domain,
    "warehouse_cross_domain": _explain_doris_cross_domain,
    "qdata_quality_check": _explain_qdata_quality_check,
    "seatunnel_pipeline_status": lambda a, r: {"explanation": f"ETL 管道共 {r.get('total_jobs', 0)} 个，{r.get('running', 0)} 个运行中，已同步 {r.get('total_records_synced', 0)} 条记录。", "data_table": {"headers": ["指标", "值"], "rows": [["总管道数", str(r.get("total_jobs", 0))], ["运行中", str(r.get("running", 0))], ["已同步记录", str(r.get("total_records_synced", 0))]]}, "data_format": "管道状态"},
}
