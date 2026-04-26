# Hands 适配器：OpenMES（开源 MES 业务底座）
# 职责：工艺路线、工单/批次管理、良率统计、SPC 看板数据
# OpenMES 为 Java/Spring Boot 服务，本适配器通过 REST API 对接
# 未部署时使用 Mock 数据

from typing import Any, Dict, List, Optional
import logging
import urllib.request
import json

_log = logging.getLogger("quantamind.hands.openmes")


def _openmes_base() -> str:
    from quantamind import config as app_config
    return app_config.get_database_config("mes_openmes").get("base_url", "http://localhost:8080/api").rstrip("/")


def _is_connected() -> bool:
    try:
        req = urllib.request.Request(f"{_openmes_base()}/system/health", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _api_get(path: str) -> Optional[dict]:
    if not _is_connected():
        return None
    try:
        req = urllib.request.Request(f"{_openmes_base()}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ── Mock 数据 ──
_MOCK_ROUTES = [
    {"route_id": "RT-001", "name": "Transmon 全流程", "steps": ["衬底清洗", "Nb 溅射", "光刻", "刻蚀", "JJ 制备(Dolan)", "布线", "封装"], "product": "5Q-Transmon"},
    {"route_id": "RT-002", "name": "JJ 单步", "steps": ["清洗", "EBL 曝光", "双角蒸镀", "Lift-off", "检测"], "product": "JJ-Test"},
]
_MOCK_LOTS = [
    {"lot_id": "LOT-2026-0301", "product": "5Q-Transmon", "qty": 24, "status": "processing", "current_step": "光刻", "yield_pct": None},
    {"lot_id": "LOT-2026-0285", "product": "5Q-Transmon", "qty": 24, "status": "completed", "current_step": "封装", "yield_pct": 91.7},
    {"lot_id": "LOT-2026-0302", "product": "JJ-Test", "qty": 48, "status": "queued", "current_step": "清洗", "yield_pct": None},
]
_MOCK_WORK_ORDERS = [
    {"wo_id": "WO-20260310-001", "lot_id": "LOT-2026-0301", "step": "光刻", "equipment": "LITHO-03", "status": "in_progress", "operator": "张三"},
    {"wo_id": "WO-20260310-002", "lot_id": "LOT-2026-0301", "step": "刻蚀", "equipment": "ETCH-02", "status": "queued", "operator": None},
]
_MOCK_YIELD = [
    {"lot_id": "LOT-2026-0285", "yield_pct": 91.7, "defects": 2, "total": 24},
    {"lot_id": "LOT-2026-0270", "yield_pct": 87.5, "defects": 3, "total": 24},
    {"lot_id": "LOT-2026-0255", "yield_pct": 95.8, "defects": 1, "total": 24},
]


def list_process_routes() -> Dict[str, Any]:
    """查询工艺路线列表"""
    data = _api_get("/mes/routes")
    if data:
        return {"routes": data, "backend": "openmes"}
    return {"routes": _MOCK_ROUTES, "backend": "mock"}


def get_process_route(route_id: str) -> Dict[str, Any]:
    """查询工艺路线详情"""
    data = _api_get(f"/mes/routes/{route_id}")
    if data:
        return {**data, "backend": "openmes"}
    for r in _MOCK_ROUTES:
        if r["route_id"] == route_id:
            return {**r, "backend": "mock"}
    return {"error": f"工艺路线 {route_id} 不存在"}


def list_lots(status: Optional[str] = None) -> Dict[str, Any]:
    """查询批次列表（可按状态筛选：queued / processing / completed）"""
    data = _api_get(f"/mes/lots" + (f"?status={status}" if status else ""))
    if data:
        return {"lots": data, "backend": "openmes"}
    lots = _MOCK_LOTS if not status else [l for l in _MOCK_LOTS if l["status"] == status]
    return {"lots": lots, "backend": "mock"}


def get_lot(lot_id: str) -> Dict[str, Any]:
    """查询批次详情"""
    data = _api_get(f"/mes/lots/{lot_id}")
    if data:
        return {**data, "backend": "openmes"}
    for l in _MOCK_LOTS:
        if l["lot_id"] == lot_id:
            return {**l, "backend": "mock"}
    return {"error": f"批次 {lot_id} 不存在"}


def list_work_orders(lot_id: Optional[str] = None) -> Dict[str, Any]:
    """查询工单列表"""
    data = _api_get(f"/mes/workorders" + (f"?lot_id={lot_id}" if lot_id else ""))
    if data:
        return {"work_orders": data, "backend": "openmes"}
    wos = _MOCK_WORK_ORDERS if not lot_id else [w for w in _MOCK_WORK_ORDERS if w["lot_id"] == lot_id]
    return {"work_orders": wos, "backend": "mock"}


def query_yield(lot_id: Optional[str] = None, last_n: int = 10) -> Dict[str, Any]:
    """查询良率数据"""
    data = _api_get(f"/mes/yield" + (f"?lot_id={lot_id}" if lot_id else f"?last={last_n}"))
    if data:
        return {"yield_data": data, "backend": "openmes"}
    yd = _MOCK_YIELD if not lot_id else [y for y in _MOCK_YIELD if y["lot_id"] == lot_id]
    avg = sum(y["yield_pct"] for y in yd) / len(yd) if yd else 0
    result = {"yield_data": yd, "average_yield_pct": round(avg, 1), "backend": "mock"}
    try:
        from quantamind.server.output_manager import save_json_output
        save_json_output("yield_report.json", result, "制造数据")
    except Exception:
        pass
    return result


def query_spc(parameter: str = "JJ_Resistance", last_n: int = 30) -> Dict[str, Any]:
    """查询 SPC 统计过程控制数据"""
    data = _api_get(f"/mes/spc?parameter={parameter}&last={last_n}")
    if data:
        return {"parameter": parameter, "data": data, "backend": "openmes"}
    import random
    random.seed(42)
    mock_data = [{"lot": f"LOT-{i}", "value": round(random.gauss(150, 8), 1), "ucl": 174, "lcl": 126, "mean": 150} for i in range(last_n)]
    ooc = sum(1 for d in mock_data if d["value"] > d["ucl"] or d["value"] < d["lcl"])
    return {"parameter": parameter, "data": mock_data, "out_of_control": ooc, "total": last_n, "backend": "mock"}


def dispatch_lot(lot_id: str, step: str, equipment_id: str) -> Dict[str, Any]:
    """派工：将批次分配到指定设备的指定工步"""
    return {"lot_id": lot_id, "step": step, "equipment_id": equipment_id, "status": "dispatched", "backend": "mock"}


def report_work(wo_id: str, result: str = "pass", defects: int = 0) -> Dict[str, Any]:
    """报工：报告工单完成结果"""
    return {"wo_id": wo_id, "result": result, "defects": defects, "status": "reported", "backend": "mock"}


def get_capabilities() -> Dict[str, Any]:
    return {
        "source": "OpenMES（开源 MES）",
        "features": ["工艺路线管理", "批次/Lot 管理", "工单管理与派工", "良率查询与统计", "SPC 统计过程控制", "报工"],
        "connected": _is_connected(),
        "base_url": _openmes_base(),
    }
