import json
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from quantamind import config
from quantamind.server import database_connections as dbc, resource_registry as rr, heartbeat as hb

router = APIRouter()
_ctx: Dict[str, Any] = {}


def bind_context(ctx: Dict[str, Any]) -> None:
    _ctx.clear()
    _ctx.update(ctx)


def _require(name: str):
    return _ctx[name]


class DiscoveryHandleAction(BaseModel):
    handled: bool = True
    handled_by: Optional[str] = None
    resolution: Optional[str] = None
    linked_task_id: Optional[str] = None
    action_note: Optional[str] = None


class DiscoveryTaskCreateRequest(BaseModel):
    title: Optional[str] = None
    task_type: Optional[str] = "discovery_followup"
    needs_approval: bool = True
    session_id: Optional[str] = None
    created_by: Optional[str] = None
    action_note: Optional[str] = None


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class DatabaseConfigsUpdate(BaseModel):
    configs: Dict[str, Dict[str, Any]]


class IntelConfigUpdate(BaseModel):
    intel_feishu_webhook: Optional[str] = None
    intel_feishu_keyword: Optional[str] = None
    intel_feishu_app_id: Optional[str] = None
    intel_feishu_app_secret: Optional[str] = None
    intel_schedule_hour: Optional[int] = None
    intel_schedule_minute: Optional[int] = None


def _mask_webhook_preview(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if len(u) <= 40:
        return u[:10] + "…" + u[-8:]
    return u[:16] + "…" + u[-12:]


class TaxonomyPendingReviewAction(BaseModel):
    reviewer: Optional[str] = None
    note: Optional[str] = None


@router.get("/health")
async def health():
    return {"status": "ok", "service": "QuantaMind Gateway"}


@router.get("/api/v1/status")
async def get_status():
    sessions = _require("sessions")
    tasks = _require("tasks")
    get_heartbeat = _require("get_heartbeat")
    hands = _require("hands")
    skills_loader = _require("skills_loader")
    state_store = _require("state_store")
    pending = sum(1 for t in tasks.values() if t.get("status") == _require("TaskStatus").PENDING)
    running = sum(1 for t in tasks.values() if t.get("status") == _require("TaskStatus").RUNNING)
    completed = sum(1 for t in tasks.values() if t.get("status") == _require("TaskStatus").COMPLETED)
    pending_approval = sum(1 for t in tasks.values() if t.get("needs_approval"))
    h = get_heartbeat()
    skills_list = skills_loader.list_skills()
    tools_list = hands.list_tools()
    store_health = state_store.get_health()
    platforms = {
        "qeda": {"name": "Q-EDA 设计", "status": "ok", "message": "就绪"},
        "mes": {"name": "墨子 MES", "status": "ok", "message": "就绪"},
        "measure": {"name": "悬镜 测控", "status": "ok", "message": "就绪"},
        "data_platform": {"name": "数据中台（QCoDeS+SeaTunnel+OLAP+qData）", "status": "ok", "message": "就绪"},
        "gewu": {"name": "格物 材料", "status": "mock", "message": "Mock"},
        "tianyuan": {"name": "天元 云", "status": "mock", "message": "Mock"},
        "kaiwu": {"name": "开物 QML", "status": "mock", "message": "Mock"},
    }
    return {
        "gateway": {
            "status": "ok",
            "service": "QuantaMind Gateway",
            "degraded": not store_health.get("available", True),
            "state_store": store_health,
        },
        "sessions_count": len(sessions),
        "tasks": {
            "total": len(tasks),
            "pending": pending,
            "running": running,
            "completed": completed,
            "pending_approval": pending_approval,
        },
        "heartbeat": {
            "level": h.get("level", "multi"),
            "interval_minutes": h.get("interval_minutes", config.HEARTBEAT_INTERVAL_MINUTES),
            "last_run": h.get("last_run"),
            "next_run": h.get("next_run"),
            "running": h.get("running", False),
        },
        "skills_count": len(skills_list),
        "tools_count": len(tools_list),
        "platforms": platforms,
    }


@router.get("/api/v1/heartbeat/discoveries")
def list_discoveries(type: Optional[str] = None, category: Optional[str] = None):
    hb = _require("hb")
    demo_discoveries = _require("DEMO_DISCOVERIES")
    live = hb.get_discoveries(category_filter=category, type_filter=type)
    if live:
        return {"discoveries": live, "source": "heartbeat"}
    demo = list(demo_discoveries)
    if category:
        demo = [d for d in demo if d.get("category") == category]
    if type:
        demo = [d for d in demo if d.get("type") == type]
    demo.sort(key=lambda d: d.get("time_iso", ""), reverse=True)
    return {"discoveries": demo, "source": "demo"}


@router.post("/api/v1/heartbeat/discoveries/{discovery_id}/handle")
def mark_discovery_handled(discovery_id: str, body: DiscoveryHandleAction):
    hb = _require("hb")
    demo_discoveries = _require("DEMO_DISCOVERIES")
    now_iso = _require("_now_iso")
    result = hb.mark_discovery_handled(
        discovery_id,
        handled=body.handled,
        handled_by=body.handled_by,
        resolution=body.resolution,
        linked_task_id=body.linked_task_id,
        action_note=body.action_note,
    )
    if "error" in result:
        for item in demo_discoveries:
            if item.get("id") == discovery_id:
                item["handled"] = body.handled
                item["handled_at"] = now_iso() if body.handled else None
                item["handled_by"] = body.handled_by if body.handled else None
                item["resolution"] = body.resolution if body.handled else None
                item["linked_task_id"] = body.linked_task_id if body.handled else None
                item["action_note"] = body.action_note if body.handled else None
                item["status"] = "handled" if body.handled else "active"
                return item
    return result


@router.get("/api/v1/heartbeat/discoveries/{discovery_id}/events")
def list_discovery_events(discovery_id: str, limit: int = 50):
    hb = _require("hb")
    return {"discovery_id": discovery_id, "events": hb.list_discovery_events(discovery_id, limit=limit)}


@router.get("/api/v1/intel/taxonomy/pending-updates")
def list_taxonomy_pending_updates(topic: Optional[str] = None):
    arxiv_intel = _require("arxiv_intel")
    updates = arxiv_intel.list_taxonomy_pending_updates(topic_id=topic)
    return {"updates": updates, "count": len(updates)}


@router.post("/api/v1/intel/taxonomy/pending-updates/{update_id}/approve")
def approve_taxonomy_pending_update(update_id: str, body: TaxonomyPendingReviewAction):
    from fastapi import HTTPException

    arxiv_intel = _require("arxiv_intel")
    result = arxiv_intel.approve_taxonomy_pending_update(update_id, reviewer=body.reviewer, note=body.note)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/api/v1/intel/taxonomy/pending-updates/{update_id}/reject")
def reject_taxonomy_pending_update(update_id: str, body: TaxonomyPendingReviewAction):
    from fastapi import HTTPException

    arxiv_intel = _require("arxiv_intel")
    result = arxiv_intel.reject_taxonomy_pending_update(update_id, reviewer=body.reviewer, note=body.note)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/api/v1/heartbeat/discoveries/{discovery_id}/create-task")
def create_task_from_discovery(discovery_id: str, body: DiscoveryTaskCreateRequest):
    hb = _require("hb")
    tasks = _require("tasks")
    task_status = _require("TaskStatus")
    now_iso = _require("_now_iso")
    logger = _require("_gateway_logger")
    state_store = _require("state_store")
    demo_discoveries = _require("DEMO_DISCOVERIES")

    discovery = hb.get_discovery_by_id(discovery_id)
    is_demo = False
    if not discovery:
        discovery = next((item for item in demo_discoveries if item.get("id") == discovery_id), None)
        is_demo = discovery is not None
    if not discovery:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="discovery not found")

    existing_task_id = discovery.get("linked_task_id")
    if existing_task_id and existing_task_id in tasks:
        return {
            "result": "existing",
            "task_id": existing_task_id,
            "task": tasks[existing_task_id],
            "discovery_id": discovery_id,
        }

    task_id = "disc_task_" + uuid.uuid4().hex[:10]
    title = body.title or ("跟进发现：" + (discovery.get("title") or discovery_id))
    task_payload = {
        "task_id": task_id,
        "status": task_status.PENDING,
        "title": title,
        "task_type": body.task_type or "discovery_followup",
        "created_at": now_iso(),
        "session_id": body.session_id,
        "needs_approval": body.needs_approval,
        "result": {
            "source": "discovery",
            "discovery_id": discovery_id,
            "fingerprint": discovery.get("fingerprint"),
            "recommended_action": discovery.get("recommended_action"),
            "category": discovery.get("category"),
            "severity": discovery.get("severity"),
        },
        "error": None,
        "source_discovery_id": discovery_id,
        "created_by": body.created_by,
    }
    tasks[task_id] = task_payload
    state_store.upsert_task(task_id, task_payload)

    if is_demo:
        discovery["linked_task_id"] = task_id
        if body.action_note:
            discovery["action_note"] = body.action_note
        discovery["last_task_linked_at"] = now_iso()
    else:
        hb.link_discovery_task(
            discovery_id,
            task_id,
            action_note=body.action_note,
            created_by=body.created_by,
            task_title=title,
            task_type=task_payload["task_type"],
            needs_approval=body.needs_approval,
        )
    logger.info("Discovery %s 已创建跟进任务 %s", discovery_id, task_id)
    return {
        "result": "created",
        "task_id": task_id,
        "task": task_payload,
        "discovery_id": discovery_id,
    }


@router.get("/api/v1/heartbeat/discoveries/stats")
def discovery_stats():
    return _require("state_store").discovery_counts()


@router.get("/api/v1/debug/status")
def debug_status():
    sessions = _require("sessions")
    tasks = _require("tasks")
    AGENTS = _require("AGENTS")
    skills_loader = _require("skills_loader")
    hands = _require("hands")
    log_buffer = _require("_LOG_BUFFER")
    start_time = _require("_STARTUP_TIME")
    state_store = _require("state_store")
    uptime_s = time.time() - start_time
    store_health = state_store.get_health()
    return {
        "uptime_seconds": round(uptime_s, 1),
        "uptime_human": f"{int(uptime_s // 3600)}h {int((uptime_s % 3600) // 60)}m {int(uptime_s % 60)}s",
        "sessions_count": len(sessions),
        "tasks_count": len(tasks),
        "agents_count": len(AGENTS),
        "skills_count": len(skills_loader.list_skills()),
        "tools_count": len(hands.list_tools()),
        "log_buffer_size": len(log_buffer),
        "python_version": __import__("sys").version,
        "gateway_port": config.GATEWAY_PORT,
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": config.LLM_MODEL,
        "state_store": store_health,
    }


@router.get("/api/v1/debug/health")
def debug_health():
    orchestrator = _require("orchestrator_getter")()
    state_store = _require("state_store")
    store_health = state_store.get_health()
    checks = {
        "gateway": "ok",
        "orchestrator": "ok" if orchestrator else "error",
        "memory": "ok",
        "hands": "ok",
        "skills_loader": "ok",
        "state_store": "ok" if store_health.get("available", True) else "degraded",
    }
    return {"health": checks, "overall": "ok" if all(v == "ok" for v in checks.values()) else "degraded"}


@router.get("/api/v1/config/llm")
def get_llm_config():
    return {
        "provider": config.LLM_PROVIDER,
        "api_base": config.LLM_API_BASE,
        "api_key": ("*" * 8 + config.LLM_API_KEY[-4:]) if len(config.LLM_API_KEY) > 4 else ("已设置" if config.LLM_API_KEY else "未设置"),
        "model": config.LLM_MODEL,
        "supported_providers": ["ollama", "openai", "deepseek", "qwen", "kimi", "zhipu", "yi"],
    }


@router.get("/api/v1/config/intel")
def get_intel_config():
    """情报日报飞书推送与每日定时（本地时区）。"""
    st = hb.get_status()
    return {
        "intel_feishu_webhook_configured": bool((config.INTEL_FEISHU_WEBHOOK or "").strip()),
        "intel_feishu_webhook_preview": _mask_webhook_preview(config.INTEL_FEISHU_WEBHOOK),
        "intel_feishu_keyword": config.INTEL_FEISHU_KEYWORD or "",
        "intel_feishu_app_id": config.INTEL_FEISHU_APP_ID or "",
        "intel_feishu_app_secret_set": bool((config.INTEL_FEISHU_APP_SECRET or "").strip()),
        "intel_schedule_hour": config.INTEL_SCHEDULE_HOUR,
        "intel_schedule_minute": config.INTEL_SCHEDULE_MINUTE,
        "next_intel_run": st.get("next_intel_run"),
        "schedule_note": "每日到点由 Gateway 内情报定时任务触发；需保持本进程常开。环境变量 QUANTAMIND_INTEL_SCHEDULE_* 优先于 config.json。",
    }


@router.post("/api/v1/config/intel")
def update_intel_config(body: IntelConfigUpdate):
    logger = _require("_gateway_logger")
    config.update_intel_delivery(
        feishu_webhook=body.intel_feishu_webhook,
        feishu_keyword=body.intel_feishu_keyword,
        feishu_app_id=body.intel_feishu_app_id,
        feishu_app_secret=body.intel_feishu_app_secret,
        schedule_hour=body.intel_schedule_hour,
        schedule_minute=body.intel_schedule_minute,
    )
    logger.info(
        "情报配置已更新: feishu=%s 每日=%02d:%02d",
        bool((config.INTEL_FEISHU_WEBHOOK or "").strip()),
        config.INTEL_SCHEDULE_HOUR,
        config.INTEL_SCHEDULE_MINUTE,
    )
    return get_intel_config()


@router.post("/api/v1/config/llm")
def update_llm_config(body: LLMConfigUpdate):
    logger = _require("_gateway_logger")
    rebuild_orchestrator = _require("rebuild_orchestrator")
    if body.provider is not None:
        config.LLM_PROVIDER = body.provider
    if body.api_base is not None:
        config.LLM_API_BASE = body.api_base
    if body.api_key is not None:
        config.LLM_API_KEY = body.api_key
    if body.model is not None:
        config.LLM_MODEL = body.model
    config.save_persistent_config()
    rebuild_orchestrator()
    logger.info("LLM 配置已更新并持久化: provider=%s model=%s", config.LLM_PROVIDER, config.LLM_MODEL)
    return {"result": "ok", "provider": config.LLM_PROVIDER, "model": config.LLM_MODEL}


@router.get("/api/v1/config/databases")
def get_database_configs():
    return dbc.list_configs()


@router.post("/api/v1/config/databases")
def update_database_configs(body: DatabaseConfigsUpdate):
    logger = _require("_gateway_logger")
    result = dbc.update_configs(body.configs)
    logger.info("数据库连接配置已更新: %s", ",".join(sorted(body.configs.keys())))
    return result


@router.get("/api/v1/config/databases/status")
def get_database_statuses():
    return dbc.get_statuses()


@router.get("/api/v1/resources")
def list_resources():
    return rr.list_resources(mask_secrets=False)


@router.get("/api/v1/resources/status")
def get_resource_statuses():
    return rr.get_resource_statuses()


@router.post("/api/v1/state-store/recover")
def recover_state_store():
    state_store = _require("state_store")
    state_store.ensure_schema()
    return {"result": "ok", "state_store": state_store.get_health()}


@router.get("/api/v1/state/pulse-calibration-history")
def get_pulse_calibration_history(limit: int = 50):
    from quantamind.server import hands_qiskit_pulse as pulse_mod
    return pulse_mod.get_calibration_history(limit=limit)


@router.get("/api/v1/state/pipeline-history")
def get_state_pipeline_history(limit: int = 50):
    return {"records": _require("state_store").get_pipeline_history(limit=limit)}


@router.get("/api/v1/state/pipeline-step-history")
def get_state_pipeline_step_history(limit: int = 100, pipeline_id: Optional[str] = None,
                                    agent: Optional[str] = None, tool: Optional[str] = None):
    return {
        "records": _require("state_store").get_pipeline_steps(
            limit=limit,
            pipeline_id=pipeline_id,
            agent=agent,
            tool=tool,
        )
    }


@router.get("/api/v1/state/library-ingest-jobs")
def get_library_ingest_jobs(limit: int = 50, status: Optional[str] = None):
    return {"records": _require("state_store").list_library_ingest_jobs(limit=limit, status=status)}
