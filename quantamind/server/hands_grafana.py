# Hands 适配器：Grafana（设备状态/参数大屏可视化）
# 职责：查询/创建看板、查询数据源、嵌入链接生成
# 通过 Grafana HTTP API 对接

from typing import Any, Dict, List, Optional
import json
import logging
import urllib.request
import urllib.error

_log = logging.getLogger("quantamind.hands.grafana")


def _grafana_base() -> str:
    from quantamind import config as app_config
    return app_config.get_database_config("mes_grafana").get("base_url", "http://localhost:3000").rstrip("/")


def _grafana_token() -> str:
    from quantamind import config as app_config
    return app_config.get_database_config("mes_grafana").get("token", "")


def _is_connected() -> bool:
    try:
        req = urllib.request.Request(f"{_grafana_base()}/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _api(method: str, path: str, body: Optional[dict] = None) -> Optional[dict]:
    if not _is_connected():
        return None
    try:
        headers = {"Content-Type": "application/json"}
        if _grafana_token():
            headers["Authorization"] = f"Bearer {_grafana_token()}"
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(f"{_grafana_base()}{path}", data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ── Mock 看板 ──
_MOCK_DASHBOARDS = [
    {"uid": "equip-overview", "title": "设备状态总览", "url": "/d/equip-overview", "tags": ["设备", "MES"], "panels": 6},
    {"uid": "yield-trend", "title": "良率趋势看板", "url": "/d/yield-trend", "tags": ["良率", "SPC"], "panels": 4},
    {"uid": "spc-monitor", "title": "SPC 过程监控", "url": "/d/spc-monitor", "tags": ["SPC", "参数"], "panels": 8},
    {"uid": "jj-params", "title": "JJ 参数实时监控", "url": "/d/jj-params", "tags": ["JJ", "测控"], "panels": 5},
]


def list_dashboards() -> Dict[str, Any]:
    """查询 Grafana 看板列表"""
    data = _api("GET", "/api/search?type=dash-db")
    if data:
        return {"dashboards": data, "backend": "grafana"}
    return {"dashboards": _MOCK_DASHBOARDS, "backend": "mock"}


def get_dashboard(uid: str) -> Dict[str, Any]:
    """查询看板详情"""
    data = _api("GET", f"/api/dashboards/uid/{uid}")
    if data:
        return {**data, "backend": "grafana"}
    for d in _MOCK_DASHBOARDS:
        if d["uid"] == uid:
            return {**d, "embed_url": f"{_grafana_base()}{d['url']}?orgId=1&kiosk", "backend": "mock"}
    return {"error": f"看板 {uid} 不存在"}


def get_embed_url(uid: str, panel_id: Optional[int] = None, from_time: str = "now-6h", to_time: str = "now") -> Dict[str, Any]:
    """生成看板或面板的嵌入 URL（可 iframe 嵌入客户端）"""
    base = f"{_grafana_base()}/d/{uid}"
    params = f"?orgId=1&from={from_time}&to={to_time}&kiosk"
    if panel_id is not None:
        base = f"{_grafana_base()}/d-solo/{uid}"
        params += f"&panelId={panel_id}"
    return {"uid": uid, "embed_url": base + params, "panel_id": panel_id}


def list_datasources() -> Dict[str, Any]:
    """查询 Grafana 数据源列表"""
    data = _api("GET", "/api/datasources")
    if data:
        return {"datasources": data, "backend": "grafana"}
    mock_ds = [
        {"id": 1, "name": "MES-PostgreSQL", "type": "postgres", "url": "localhost:5432"},
        {"id": 2, "name": "Equipment-InfluxDB", "type": "influxdb", "url": "localhost:8086"},
        {"id": 3, "name": "Prometheus-Metrics", "type": "prometheus", "url": "localhost:9090"},
    ]
    return {"datasources": mock_ds, "backend": "mock"}


def query_datasource(datasource_uid: str, query_expr: str, from_time: str = "now-1h", to_time: str = "now") -> Dict[str, Any]:
    """查询数据源（通过 Grafana 代理）"""
    body = {
        "queries": [{"refId": "A", "datasource": {"uid": datasource_uid}, "expr": query_expr}],
        "from": from_time, "to": to_time,
    }
    data = _api("POST", "/api/ds/query", body)
    if data:
        return {"result": data, "backend": "grafana"}
    return {"query": query_expr, "datasource": datasource_uid, "mock_result": {"series": [], "note": "Mock 模式：需部署 Grafana"}, "backend": "mock"}


def create_equipment_dashboard(equipment_ids: List[str]) -> Dict[str, Any]:
    """为指定设备创建/更新状态监控看板"""
    panels = []
    for i, eid in enumerate(equipment_ids):
        panels.append({"title": f"{eid} 状态", "type": "stat", "gridPos": {"h": 4, "w": 6, "x": (i % 4) * 6, "y": (i // 4) * 4}})
        panels.append({"title": f"{eid} 参数趋势", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20 + i * 8}})
    dashboard = {"dashboard": {"title": "QuantaMind 设备监控", "panels": panels, "tags": ["QuantaMind", "设备"]}, "overwrite": True}
    data = _api("POST", "/api/dashboards/db", dashboard)
    if data:
        return {"dashboard_url": data.get("url"), "backend": "grafana"}
    return {"equipment_ids": equipment_ids, "panels_count": len(panels), "status": "created", "backend": "mock"}


def get_capabilities() -> Dict[str, Any]:
    return {
        "source": "Grafana",
        "features": ["看板列表与详情", "嵌入 URL 生成（iframe）", "数据源查询", "自动创建设备监控看板"],
        "connected": _is_connected(),
        "base_url": _grafana_base(),
        "dashboards": ["设备状态总览", "良率趋势", "SPC 过程监控", "JJ 参数实时监控"],
    }
