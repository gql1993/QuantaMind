"""
真实芯片版图生成器
优先使用团队已生成的工业级 GDS，也支持运行版图代码重新生成
"""
import os
import sys
import json
import shutil
import logging
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_log = logging.getLogger("quantamind.real_chip_builder")

LAYOUT_SCRIPT = Path(__file__).parent / "layout_CT20QV2_01.py"
PARAMS_JSON = Path(__file__).parent / "CT20QV2_01.json"
OUTPUT_DIR = Path(os.path.expanduser("~/.quantamind/outputs/chip_designs")).resolve()

REAL_GDS_SOURCES = {
    "1bit": Path(r"E:\work\Quantumchipdesin\单比特\1bitV2.00\1bitV2.00.gds"),
    "2bit": Path(r"E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\output\2bits_coupler_V2_00.gds"),
    "20bit": Path(r"E:\work\Quantumchipdesin\CT20Q\CT20QV2_01_12.5mm_20260130\CT20QV2_01_12.5mm_20260130\CT20QV2_01-20260130.gds"),
    "105bit": Path(r"E:\work\Quantumchipdesin\105比特\FT105QV2_00_20260317.gds"),
}

REAL_GDS_INFO = {
    "1bit": {"name": "1bitV2.00", "qubits": 5, "size_mm": [10, 10], "shapes": 5122, "layers": 5},
    "2bit": {"name": "2bits_coupler_V2.00", "qubits": 4, "couplers": 2, "size_mm": [10, 10], "shapes": 366},
    "20bit": {"name": "CT20QV2_01", "qubits": 20, "couplers": 19, "size_mm": [12.5, 12.5], "shapes": 24888, "layers": 6, "cells": 6},
    "105bit": {"name": "FT105QV2_00", "qubits": 105, "shapes": 95238, "layers": 10, "cells": 18},
}


def build_real_chip(chip_type: str = "20bit", output_filename: str = None) -> dict:
    """
    使用团队已生成的工业级 GDS 文件。
    chip_type: "1bit" | "2bit" | "20bit" | "105bit"
    """
    if chip_type not in REAL_GDS_SOURCES:
        return {"error": f"Unknown chip type: {chip_type}", "available": list(REAL_GDS_SOURCES.keys())}

    src = REAL_GDS_SOURCES[chip_type]
    if not src.exists():
        return {"error": f"Source GDS not found: {src}"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_filename is None:
        output_filename = f"{REAL_GDS_INFO[chip_type]['name']}_real.gds"
    dst = OUTPUT_DIR / output_filename

    shutil.copy2(str(src), str(dst))
    file_size = os.path.getsize(dst)
    info = REAL_GDS_INFO[chip_type]

    _log.info("Real %s GDS deployed: %s (%s bytes, %s shapes)", chip_type, dst, f"{file_size:,}", info.get("shapes"))

    return {
        "success": True,
        "gds_file": str(dst),
        "source_gds": str(src),
        "file_size_bytes": file_size,
        "chip_type": chip_type,
        "chip_name": info["name"],
        "chip_size_mm": info.get("size_mm"),
        "total_qubits": info.get("qubits"),
        "total_couplers": info.get("couplers", 0),
        "total_shapes": info.get("shapes"),
        "total_layers": info.get("layers"),
        "total_cells": info.get("cells"),
        "backend": "real_team_gds",
        "note": f"Industrial-grade GDS from team's {info['name']} design (layout_CT20QV2_01.py + user_components)",
    }


def build_ct20q_real(output_filename: str = "CT20QV2_real.gds") -> dict:
    """使用团队真实 20 比特 GDS（24,888 shapes, 9.6MB）"""
    return build_real_chip("20bit", output_filename)


def build_100bit_reference(output_filename: str = "100bit_tunable_coupler.gds") -> dict:
    """
    生成 100 比特参考级 GDS（10x10 二维网格布局）。
    使用 gdstk 生成含 Xmon 比特、耦合器、谐振腔、焊盘的完整版图。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUT_DIR / output_filename)
    try:
        from quantamind.server.gds_generator import generate_chip_gds
        generate_chip_gds(
            output_path,
            num_qubits=100,
            chip_name="100bit_tunable_coupler",
            chip_size_x=20000,
            chip_size_y=20000,
            with_readout=True,
            with_labels=True,
        )
        file_size = os.path.getsize(output_path)
        _log.info("100-bit reference GDS: %s (%s bytes)", output_path, f"{file_size:,}")
        return {
            "success": True,
            "gds_file": output_path,
            "file_size_bytes": file_size,
            "chip_name": "100bit_tunable_coupler",
            "chip_size_mm": [20, 20],
            "total_qubits": 100,
            "layout": "10x10 grid",
            "backend": "gdstk_reference",
            "note": "Reference-grade 100-qubit GDS (10x10 grid, Xmon qubits, "
                    "tunable couplers, CPW routing, readout resonators, launchpads)",
        }
    except Exception as e:
        _log.error("100-bit GDS generation failed: %s", e)
        return {"error": f"100-bit GDS generation failed: {e}"}


def generate_ct20q_live(
    output_filename: str = "CT20QV2_industrial.gds",
    parameter_file: str = None,
    meander_length_list: list = None,
    jj_dict: dict = None,
    timeout: int = 900,
) -> dict:
    """
    运行团队版图代码 twenty_qubits_tunable_coupler_layout() 实时生成工业级 GDS。
    使用 NoopGUI（跳过 Qt）+ SafeRoutePathfinder（容错寻路）。
    在子进程中运行，segfault 时自动回退到中间检查点 GDS。

    Args:
        output_filename: GDS 输出文件名
        parameter_file:  组件参数 JSON 路径（默认 CT20QV2_01.json）
        meander_length_list: 可选的 20 个谐振腔蛇形线长度列表 (mm)
        jj_dict: 可选的每个比特约瑟夫森结 cell 名称字典
        timeout: 子进程超时秒数（默认 900 = 15 分钟）
    """
    from quantamind.server.industrial_layout_runner import generate_industrial_gds
    return generate_industrial_gds(
        output_filename=output_filename,
        parameter_file=parameter_file,
        meander_length_list=meander_length_list,
        jj_dict=jj_dict,
        timeout=timeout,
    )
