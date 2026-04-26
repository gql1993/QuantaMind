# Hands 适配器：QEDA 团队的真实设计代码
# 将 docs/QEDA/ 中的 Python 代码封装为可调用工具
# 包括：约瑟夫森结参数生成、芯片规格查询

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger("quantamind.hands.qeda_code")

# 加载芯片规格
SPECS = {}
try:
    from quantamind.server.chip_20bit_spec import CHIP_SPEC
    SPECS["20bit"] = CHIP_SPEC
except Exception:
    pass
try:
    from quantamind.server.chip_105bit_spec import CHIP_105BIT_SPEC
    SPECS["105bit"] = CHIP_105BIT_SPEC
except Exception:
    pass

# 加载真实芯片设计资料
try:
    from quantamind.server.chip_real_designs import ALL_REAL_DESIGNS, CHIP_1BIT, CHIP_2BIT, CHIP_CT20Q, CHIP_105BIT
    SPECS["1bit_real"] = CHIP_1BIT
    SPECS["2bit_real"] = CHIP_2BIT
    SPECS["20bit_ct20q"] = CHIP_CT20Q
    SPECS["105bit_real"] = CHIP_105BIT
    _log.info("已加载 %d 个真实芯片设计资料", len(ALL_REAL_DESIGNS))
except Exception as e:
    _log.warning("加载真实设计资料失败: %s", e)

# 加载约瑟夫森结参数
QEDA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "QEDA"

def get_junction_params(jj_type: str = "Single_Manhattan") -> Dict[str, Any]:
    """获取约瑟夫森结设计参数（来自设计团队 junction_generator.py）"""
    params = {
        "Single_Manhattan": {
            "type": "单结曼哈顿型",
            "JJ_pad_lower_width": "6um", "JJ_pad_lower_height": "8.8um",
            "JJ_pad_up_width": "10um", "JJ_pad_up_height": "5.2um",
            "finger_lower_width": "0.18um", "finger_lower_height": "7.767um",
            "finger_up_width": "0.18um", "finger_up_height": "8.017um",
            "extension": "2.6um",
        },
        "Squid_Manhattan": {
            "type": "SQUID 曼哈顿型",
            "JJ_pad_lower_width": "10um", "JJ_pad_lower_height": "11um",
            "JJ_pad_up_width": "7um", "JJ_pad_up_height": "9.0um",
            "finger_left_lower_width": "0.18um", "finger_right_lower_width": "0.18um",
            "finger_lower_height": "5.8um", "finger_up_height": "4.372um",
            "JJ_space": "5.6um", "extension": "1.7228um",
        },
        "SquidFlip_Manhattan": {
            "type": "翻转 SQUID 曼哈顿型",
            "JJ_pad_lower_width": "10um", "JJ_pad_lower_height": "5.2um",
            "JJ_pad_up_width": "5.5um", "JJ_pad_up_height": "13.55um",
        },
    }
    if jj_type in params:
        return {"jj_type": jj_type, "params": params[jj_type],
                "source": "docs/QEDA/junction_generator.py",
                "available_types": list(params.keys())}
    return {"error": f"未知类型 {jj_type}", "available_types": list(params.keys())}


def list_chip_specs() -> Dict[str, Any]:
    """列出所有可用的芯片规格"""
    result = []
    for key, spec in SPECS.items():
        result.append({
            "key": key,
            "name": spec.get("name", key),
            "doc_id": spec.get("doc_id", ""),
            "total_qubits": spec.get("total_qubits", len(spec.get("qubits", []))),
            "total_couplers": spec.get("total_couplers", len(spec.get("couplers", []))),
            "topology": spec.get("topology", ""),
        })
    return {"specs": result, "count": len(result)}


def get_chip_spec(chip_key: str = "20bit") -> Dict[str, Any]:
    """获取指定芯片的完整规格（含全部比特参数）"""
    if chip_key in SPECS:
        spec = SPECS[chip_key]
        return {
            "name": spec.get("name"),
            "doc_id": spec.get("doc_id"),
            "total_qubits": spec.get("total_qubits", len(spec.get("qubits", []))),
            "targets": spec.get("targets", {}),
            "qubits_count": len(spec.get("qubits", [])),
            "qubits_sample": spec.get("qubits", [])[:5],
            "source": "设计文档自动提取",
        }
    return {"error": f"芯片 {chip_key} 不存在", "available": list(SPECS.keys())}


def get_qubit_params(chip_key: str = "20bit", qubit_id: Optional[str] = None) -> Dict[str, Any]:
    """查询指定芯片中某个比特的设计参数"""
    if chip_key not in SPECS:
        return {"error": f"芯片 {chip_key} 不存在", "available": list(SPECS.keys())}
    qubits = SPECS[chip_key].get("qubits", [])
    if qubit_id:
        for q in qubits:
            if q.get("id") == qubit_id:
                return {"chip": chip_key, "qubit": q}
        return {"error": f"比特 {qubit_id} 不存在"}
    return {"chip": chip_key, "qubits": qubits, "count": len(qubits)}


def list_qeda_code_files() -> Dict[str, Any]:
    """列出 QEDA 团队提供的所有文件（代码/文档/教程）"""
    files = []
    if QEDA_DIR.exists():
        for f in sorted(QEDA_DIR.iterdir()):
            if f.is_file() and not f.name.startswith("~$"):
                files.append({"filename": f.name, "ext": f.suffix, "size_kb": round(f.stat().st_size / 1024, 1)})
    return {"files": files, "count": len(files), "path": str(QEDA_DIR)}


# ── QEDA 资料目录（芯片设计团队共享知识） ──
QEDA_CATALOG = [
    {"file": "100比特设计规范.docx", "type": "设计规范", "desc": "100 比特级芯片设计规范文档，定义总体设计约束和标准"},
    {"file": "105比特可调耦合器量子芯片设计方案0120.docx", "type": "设计方案", "desc": "105 比特可调耦合器芯片完整设计方案，含比特参数表、谐振腔设计、耦合器结构、封装设计"},
    {"file": "20比特可调耦合器双比特设计方案.docx", "type": "设计方案", "desc": "20 比特可调耦合器双比特芯片设计方案"},
    {"file": "芯片版图设计教程V03.pptx", "type": "教程", "desc": "Q-EDA 芯片版图设计培训教程（PPT），含设计流程和工具使用"},
    {"file": "quantum_chip_layout.py", "type": "核心代码", "desc": "Q-EDA 版图布局核心引擎（1900+行），支持 Xmon 阵列、Flip-chip、自动布线、LaunchPad 排列"},
    {"file": "junction_generator.py", "type": "工具代码", "desc": "约瑟夫森结参数生成器，支持 Single_Manhattan / Squid_Manhattan / SquidFlip_Manhattan 三种类型"},
    {"file": "junction_windows.py", "type": "工具代码", "desc": "约瑟夫森结生成工具 GUI 界面"},
    {"file": "qubit_layout_windows.py", "type": "工具代码", "desc": "量子比特版图生成 GUI 界面"},
    {"file": "auto routing.ipynb", "type": "教程笔记本", "desc": "自动布线教程，演示 Qiskit Metal RouteMeander / RoutePathfinder 用法"},
    {"file": "可调耦合器超导量子标准单元设计.ipynb", "type": "教程笔记本", "desc": "可调耦合器标准单元的完整设计流程（1.8MB），含参数推导和仿真"},
    {"file": "标准单元单比特版图设计.ipynb", "type": "教程笔记本", "desc": "单比特标准单元版图设计教程"},
    {"file": "标准单元双比特版图设计.ipynb", "type": "教程笔记本", "desc": "双比特标准单元版图设计教程"},
    {"file": "约瑟夫森结生成工具使用文档.docx", "type": "工具文档", "desc": "约瑟夫森结生成工具的使用说明书"},
    {"file": "约瑟夫森结生成工具使用文档.pdf", "type": "工具文档", "desc": "同上 PDF 版本"},
    {"file": "芯片设计参数表.docx", "type": "参数文档", "desc": "芯片设计参数汇总表"},
    {"file": "量子芯片超导线路结构设计总结.docx", "type": "设计总结", "desc": "超导线路结构（CPW/谐振腔/控制线/读取线）的设计经验总结"},
    {"file": "user_components.7z", "type": "组件库", "desc": "Qiskit Metal 自定义组件库（压缩包），含团队开发的专用 QComponent"},
]


def get_real_design(design_key: str = "2bit") -> Dict[str, Any]:
    """获取真实芯片设计的完整资料（来自 Quantumchipdesin 目录）"""
    try:
        from quantamind.server.chip_real_designs import ALL_REAL_DESIGNS
    except ImportError:
        return {"error": "real designs module not loaded"}
    if design_key in ALL_REAL_DESIGNS:
        design = ALL_REAL_DESIGNS[design_key]
        import os
        files_status = {}
        for fk, fp in design.get("files", {}).items():
            files_status[fk] = {"path": fp, "exists": os.path.exists(fp)}
        return {
            "design_key": design_key,
            "name": design.get("name"),
            "doc_id": design.get("doc_id"),
            "chip_size_mm": design.get("chip_size_mm"),
            "total_qubits": design.get("total_qubits"),
            "total_couplers": design.get("total_couplers", 0),
            "topology": design.get("topology"),
            "qubit_type": design.get("qubit_type"),
            "qubits": design.get("qubits", [])[:6],
            "design_goals": design.get("design_goals", []),
            "files": files_status,
            "layout_code": design.get("layout_code"),
        }
    return {
        "error": f"Design '{design_key}' not found",
        "available": list(ALL_REAL_DESIGNS.keys()),
    }


def get_qeda_catalog() -> Dict[str, Any]:
    """获取 QEDA 芯片设计团队的完整资料目录（含每份文件的内容说明）"""
    catalog = []
    for item in QEDA_CATALOG:
        fpath = QEDA_DIR / item["file"]
        exists = fpath.exists()
        entry = {**item, "exists": exists}
        if exists:
            entry["size_kb"] = round(fpath.stat().st_size / 1024, 1)
        catalog.append(entry)
    by_type = {}
    for c in catalog:
        t = c["type"]
        by_type.setdefault(t, []).append(c["file"])
    return {"catalog": catalog, "count": len(catalog), "by_type": by_type,
            "summary": f"QEDA 团队共享 {len(catalog)} 份资料，涵盖设计规范/方案、核心代码、教程笔记本、工具文档、组件库"}
