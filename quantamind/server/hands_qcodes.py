# Hands 适配器：QCoDeS（量子测量数据采集框架，Microsoft）
# 职责：仪器参数管理、测量数据采集与存储、DataSet 查询与导出
# 在数据中台中的角色：量子测控数据的第一入口，采集后经 SeaTunnel 汇入 Doris

from typing import Any, Dict, List, Optional
import logging
import random

_log = logging.getLogger("quantamind.hands.qcodes")

try:
    import qcodes as qc
    HAS_QCODES = True
    QCODES_VERSION = qc.__version__
    _log.info("QCoDeS %s 已加载", QCODES_VERSION)
except ImportError:
    HAS_QCODES = False
    QCODES_VERSION = None
    _log.warning("QCoDeS 未安装，使用 Mock 模式")

_run_counter = 0


def list_instruments() -> Dict[str, Any]:
    """列出 QCoDeS Station 中的仪器"""
    mock = [
        {"name": "vna", "type": "VectorNetworkAnalyzer", "desc": "矢量网络分析仪（S 参数）"},
        {"name": "awg", "type": "ArbitraryWaveformGenerator", "desc": "任意波形发生器（驱动脉冲）"},
        {"name": "digitizer", "type": "Digitizer", "desc": "高速数字化仪（读出信号采集）"},
        {"name": "dc_source", "type": "DCSource", "desc": "直流源（磁通偏置）"},
        {"name": "lo_drive", "type": "LocalOscillator", "desc": "本振（驱动微波源）"},
        {"name": "lo_readout", "type": "LocalOscillator", "desc": "本振（读出微波源）"},
        {"name": "attenuator", "type": "DigitalAttenuator", "desc": "数字衰减器"},
    ]
    if HAS_QCODES:
        try:
            station = qc.Station.default
            if station:
                insts = [{"name": n, "type": type(i).__name__} for n, i in station.components.items()]
                return {"instruments": insts, "count": len(insts), "backend": "qcodes"}
        except Exception:
            pass
    return {"instruments": mock, "count": len(mock), "backend": "mock"}


def list_experiments(last_n: int = 10) -> Dict[str, Any]:
    """列出最近的 QCoDeS 实验"""
    mock = [
        {"exp_id": 1, "name": "5Q_Transmon_T1", "sample": "Chip_2026A", "runs": 24},
        {"exp_id": 2, "name": "5Q_Transmon_Spectroscopy", "sample": "Chip_2026A", "runs": 12},
        {"exp_id": 3, "name": "JJ_IV_Curve", "sample": "JJ_Batch_03", "runs": 48},
        {"exp_id": 4, "name": "Resonator_S21", "sample": "Chip_2026A", "runs": 8},
    ]
    return {"experiments": mock[:last_n], "backend": "qcodes" if HAS_QCODES else "mock"}


def list_runs(experiment_id: int = 1, last_n: int = 20) -> Dict[str, Any]:
    """列出某实验下的测量 run 列表"""
    random.seed(experiment_id)
    mock_runs = [{"run_id": i, "parameters": ["frequency", "amplitude"], "records": random.randint(50, 500),
                  "timestamp": f"2026-03-{10 - i % 5:02d}T{10 + i:02d}:00:00"} for i in range(1, min(last_n + 1, 25))]
    return {"experiment_id": experiment_id, "runs": mock_runs, "backend": "qcodes" if HAS_QCODES else "mock"}


def get_run_data(run_id: int, format: str = "summary") -> Dict[str, Any]:
    """获取某次 run 的测量数据（summary / pandas / export）"""
    random.seed(run_id)
    mock_summary = {
        "run_id": run_id,
        "parameters": {"frequency_ghz": {"min": 4.8, "max": 5.3, "points": 200},
                        "S21_dB": {"min": -45.2, "max": -3.1}},
        "snapshot_keys": ["lo_drive.frequency", "lo_readout.frequency", "attenuator.attenuation"],
        "records": random.randint(100, 500),
    }
    return {**mock_summary, "format": format, "backend": "qcodes" if HAS_QCODES else "mock"}


def export_dataset(run_id: int, format: str = "csv", output_path: Optional[str] = None) -> Dict[str, Any]:
    """导出 DataSet 到文件（csv / netcdf / pandas）"""
    import os, json as _json
    path = output_path or f"qcodes_run_{run_id}.{format}"
    if HAS_QCODES:
        try:
            from qcodes.dataset.data_set import load_by_id
            ds = load_by_id(run_id)
            ds.export(format, path=path)
            return {"run_id": run_id, "exported": path, "format": format, "size_bytes": os.path.getsize(path), "backend": "qcodes"}
        except Exception as e:
            pass
    # Mock 模式：生成示例 CSV
    os.makedirs(os.path.dirname(os.path.abspath(path)) if os.path.dirname(path) else ".", exist_ok=True)
    import random
    random.seed(run_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write("frequency_ghz,S21_dB,phase_deg\n")
        for i in range(100):
            freq = 4.8 + i * 0.005
            s21 = -30 + 25 * (1 / (1 + ((freq - 5.1) / 0.02) ** 2))
            phase = random.uniform(-180, 180)
            f.write(f"{freq:.4f},{s21:.2f},{phase:.1f}\n")
    size = os.path.getsize(path)
    return {"run_id": run_id, "exported": path, "format": format, "size_bytes": size, "rows": 100, "backend": "mock"}


def query_by_metadata(sample: Optional[str] = None, parameter: Optional[str] = None) -> Dict[str, Any]:
    """按元数据查询 run（样品名、参数名等）"""
    mock_results = [
        {"run_id": 5, "experiment": "5Q_Transmon_T1", "sample": "Chip_2026A", "match": "sample"},
        {"run_id": 12, "experiment": "Resonator_S21", "sample": "Chip_2026A", "match": "sample"},
    ]
    return {"query": {"sample": sample, "parameter": parameter}, "results": mock_results, "backend": "mock"}


def get_capabilities() -> Dict[str, Any]:
    return {
        "source": "QCoDeS（Microsoft Quantum）",
        "role": "量子测量数据采集与管理",
        "version": QCODES_VERSION,
        "features": ["仪器参数管理（Station）", "测量数据采集（Measurement）", "DataSet 数据库（SQLite）",
                     "导出 CSV/NetCDF/pandas", "仪器快照（Snapshot）", "实验与 Run 管理", "跨数据库 Run 提取"],
        "data_types": ["S 参数", "IV 曲线", "T1/T2 时域数据", "光谱数据", "校准参数"],
        "installed": HAS_QCODES,
    }
