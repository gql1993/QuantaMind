from __future__ import annotations

from typing import Any, Dict

from quantamind.server import resource_registry
from quantamind.server.routes_system import get_status as get_v1_status


def get_system_status_summary() -> Dict[str, Any]:
    payload = get_v1_status()
    gateway = payload.get("gateway", {})
    tasks = payload.get("tasks", {})
    heartbeat = payload.get("heartbeat", {})
    summary = (
        f"系统状态：{gateway.get('status', 'unknown')}\n"
        f"降级模式：{'是' if gateway.get('degraded') else '否'}\n"
        f"会话数：{payload.get('sessions_count', 0)}\n"
        f"任务统计：总计 {tasks.get('total', 0)}，运行中 {tasks.get('running', 0)}，待审批 {tasks.get('pending_approval', 0)}\n"
        f"Heartbeat：level={heartbeat.get('level', 'unknown')}，running={heartbeat.get('running', False)}"
    )
    return {
        "status": "ok",
        "summary": summary,
        "payload": payload,
    }


def get_database_status_summary() -> Dict[str, Any]:
    payload = resource_registry.get_resource_statuses(force_refresh=True)
    statuses = payload.get("statuses", {})
    design = statuses.get("design_postgres", {})
    vector = statuses.get("ai_pgvector", {})
    mes = statuses.get("mes_sqlserver", {})
    summary = (
        f"设计主库：{'已连接' if design.get('connected') else '未连接'}"
        + (f"（{design.get('detail', '')}）" if design.get("detail") else "")
        + "\n"
        + f"pgvector：{'已连接' if vector.get('connected') else '未连接'}"
        + (f"（{vector.get('detail', '')}）" if vector.get("detail") else "")
        + "\n"
        + f"MES 业务库：{'已连接' if mes.get('connected') else '未连接'}"
        + (f"（{mes.get('detail', '')}）" if mes.get("detail") else "")
    )
    return {
        "status": "ok",
        "summary": summary,
        "payload": payload,
    }
