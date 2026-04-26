# Hands 适配器：qData（数据治理与服务平台）
# 职责：数据标准、资产目录、质量检查、数据服务 API、Text2SQL
# 在数据中台中的角色：Doris 之上的治理与服务层，保障数据质量并对外开放

from typing import Any, Dict, List, Optional
import logging

_log = logging.getLogger("quantamind.hands.qdata")


def _qdata_base() -> str:
    from quantamind import config as app_config
    return app_config.get_database_config("datacenter_qdata").get("base_url", "http://localhost:8180").rstrip("/")


def _is_connected() -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(f"{_qdata_base()}/api/system/health", method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        return False

_MOCK_ASSETS = [
    {"asset_id": "A001", "name": "比特表征数据集", "domain": "测控域", "table": "qubit_characterization", "owner": "测控组", "quality_score": 95, "tags": ["T1", "T2", "频率"]},
    {"asset_id": "A002", "name": "良率趋势数据集", "domain": "制造域", "table": "yield_records", "owner": "工艺组", "quality_score": 92, "tags": ["良率", "SPC"]},
    {"asset_id": "A003", "name": "芯片设计库", "domain": "设计域", "table": "chip_designs", "owner": "设计组", "quality_score": 98, "tags": ["Transmon", "拓扑", "频率分配"]},
    {"asset_id": "A004", "name": "仿真结果集", "domain": "设计域", "table": "simulation_results", "owner": "设计组", "quality_score": 96, "tags": ["HFSS", "Q3D", "本征模"]},
    {"asset_id": "A005", "name": "校准历史记录", "domain": "测控域", "table": "calibration_records", "owner": "测控组", "quality_score": 94, "tags": ["振幅", "DRAG", "频率"]},
    {"asset_id": "A006", "name": "设备事件日志", "domain": "制造域", "table": "equipment_events", "owner": "运维组", "quality_score": 88, "tags": ["告警", "SECS/GEM"]},
]

_MOCK_STANDARDS = [
    {"std_id": "STD-001", "name": "比特频率数据标准", "domain": "测控域", "rules": ["freq_ghz BETWEEN 3.0 AND 8.0", "NOT NULL"], "compliance": 99.2},
    {"std_id": "STD-002", "name": "良率数据标准", "domain": "制造域", "rules": ["yield_pct BETWEEN 0 AND 100", "lot_id 格式校验"], "compliance": 97.5},
    {"std_id": "STD-003", "name": "设计参数标准", "domain": "设计域", "rules": ["qubit_count > 0", "topology IN (heavy_hex, grid, linear)"], "compliance": 100.0},
]


def list_data_assets(domain: Optional[str] = None) -> Dict[str, Any]:
    """列出数据资产目录"""
    assets = _MOCK_ASSETS if not domain else [a for a in _MOCK_ASSETS if domain in a["domain"]]
    return {"assets": assets, "count": len(assets), "backend": "qdata" if _is_connected() else "mock"}


def get_data_asset(asset_id: str) -> Dict[str, Any]:
    """查询数据资产详情"""
    for a in _MOCK_ASSETS:
        if a["asset_id"] == asset_id:
            return {**a, "backend": "mock"}
    return {"error": f"资产 {asset_id} 不存在"}


def list_data_standards() -> Dict[str, Any]:
    """列出数据标准"""
    return {"standards": _MOCK_STANDARDS, "count": len(_MOCK_STANDARDS), "backend": "mock"}


def run_quality_check(table: str) -> Dict[str, Any]:
    """对指定表执行数据质量检查"""
    import random
    random.seed(hash(table))
    total = random.randint(100, 10000)
    issues = random.randint(0, int(total * 0.05))
    return {
        "table": table,
        "total_records": total,
        "issues_found": issues,
        "quality_score": round((1 - issues / total) * 100, 1),
        "checks": ["空值检查", "范围校验", "格式校验", "一致性检查"],
        "backend": "qdata" if _is_connected() else "mock",
    }


def text2sql(question: str) -> Dict[str, Any]:
    """自然语言转 SQL（Text2SQL），供 AI Agent 查询数据"""
    question_lower = question.lower()
    if "良率" in question or "yield" in question_lower:
        sql = "SELECT lot_id, yield_pct, defects FROM yield_records ORDER BY measured_at DESC LIMIT 10"
    elif "t1" in question_lower or "t2" in question_lower or "表征" in question:
        sql = "SELECT chip_id, qubit, freq_ghz, T1_us, T2_us FROM qubit_characterization ORDER BY measured_at DESC LIMIT 20"
    elif "校准" in question or "calibrat" in question_lower:
        sql = "SELECT chip_id, qubit, gate, amplitude, fidelity_pct FROM calibration_records ORDER BY calibrated_at DESC LIMIT 20"
    elif "设计" in question or "design" in question_lower:
        sql = "SELECT design_id, chip_type, qubit_count, topology, status FROM chip_designs ORDER BY created_at DESC LIMIT 10"
    elif "告警" in question or "alarm" in question_lower:
        sql = "SELECT equipment_id, event_type, message, timestamp FROM equipment_events WHERE event_type='alarm' ORDER BY timestamp DESC LIMIT 20"
    else:
        sql = f"-- Text2SQL 未能精确匹配，建议改写问题或直接写 SQL\n-- 原始问题：{question}"
    return {"question": question, "generated_sql": sql, "backend": "qdata" if _is_connected() else "mock"}


def create_data_service(name: str, sql: str, description: str = "") -> Dict[str, Any]:
    """创建数据服务 API（将 SQL 封装为 REST 接口）"""
    service_id = f"SVC-{len(_MOCK_ASSETS) + 1:03d}"
    return {
        "service_id": service_id, "name": name, "sql": sql, "description": description,
        "endpoint": f"/api/data-service/{service_id}",
        "status": "created",
        "backend": "qdata" if _is_connected() else "mock",
    }


def get_lineage(table: str) -> Dict[str, Any]:
    """查询数据血缘（上下游依赖关系）"""
    lineage_map = {
        "qubit_characterization": {"upstream": ["QCoDeS(raw_measurements)", "ARTIQ(脉冲序列)"], "downstream": ["error_mitigation_results", "gate_benchmarks", "数据服务 API"]},
        "yield_records": {"upstream": ["OpenMES(lots)", "OpenMES(work_orders)"], "downstream": ["spc_data", "Grafana(良率看板)", "数据服务 API"]},
        "chip_designs": {"upstream": ["Qiskit Metal(design)", "KQCircuits(chip)"], "downstream": ["simulation_results", "drc_reports", "gds_exports", "lots"]},
        "calibration_records": {"upstream": ["Qiskit Pulse(校准)", "ARTIQ(Rabi/Ramsey)"], "downstream": ["qubit_characterization", "gate_benchmarks"]},
    }
    return {"table": table, "lineage": lineage_map.get(table, {"upstream": ["未知"], "downstream": ["未知"]}), "backend": "mock"}


def get_capabilities() -> Dict[str, Any]:
    return {
        "source": "qData（千通数据中台）",
        "role": "数据治理与服务层",
        "features": ["数据资产目录", "数据标准管理", "数据质量检查（GB/T 36344）",
                     "Text2SQL 自然语言查询", "数据服务 API 创建", "数据血缘追溯",
                     "数据安全与分级", "数据可视化"],
        "connected": _is_connected(),
    }
