# Heartbeat — 自主科研心跳引擎（多层级定时任务）
# L0 实时监控(5min) / L1 数据(6h) / L2 实验(12h) / L3 洞察(24h) / L4 情报(24h)

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from quantamind import config
from quantamind.server import state_store

_log = logging.getLogger("quantamind.heartbeat")

# 发现存储（Gateway 从这里读取，替代硬编码）
discoveries: List[Dict[str, Any]] = []
_last_run: Optional[str] = None
_running = False
_last_intel_report_id: Optional[str] = None
_intel_scheduler_running = False
_next_intel_run: Optional[str] = None
_intel_cache_warmer_running = False
_next_intel_cache_warm: Optional[str] = None
_taxonomy_engineer_running = False
_next_taxonomy_engineer_run: Optional[str] = None

HEARTBEAT_LEVELS = [
    {"level": "L0", "name": "实时监控", "interval_minutes": 5, "tasks": ["检查设备告警", "检查任务队列", "检查 ETL 管道状态"]},
    {"level": "L1", "name": "数据巡检", "interval_minutes": 360, "tasks": ["数据质量巡检", "新测量数据检查", "良率趋势分析"]},
    {"level": "L2", "name": "实验建议", "interval_minutes": 720, "tasks": ["基于最新数据生成实验建议", "校准状态评估"]},
    {"level": "L3", "name": "假设与洞察", "interval_minutes": 1440, "tasks": ["假设挖掘", "跨域关联分析", "周报草稿"]},
    {"level": "L4", "name": "外部情报", "interval_minutes": 1440, "tasks": ["arXiv 检索", "技术路线提炼", "知识入库", "飞书日报推送", "技术体系补树"]},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _severity_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "info": 2}.get(value or "info", 9)


def _discovery_fingerprint(category: str, type: str, title: str, source: str,
                           entity_type: str = "", entity_id: str = "") -> str:
    raw = "||".join([
        category or "",
        type or "",
        title or "",
        source or "",
        entity_type or "",
        entity_id or "",
    ])
    return "dfp_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_discovery_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(item)
    normalized["id"] = normalized.get("id") or f"d_{uuid.uuid4().hex[:10]}"
    normalized["fingerprint"] = normalized.get("fingerprint") or _discovery_fingerprint(
        normalized.get("category", ""),
        normalized.get("type", ""),
        normalized.get("title", ""),
        normalized.get("source", ""),
        normalized.get("entity_type", ""),
        normalized.get("entity_id", ""),
    )
    normalized["time_iso"] = normalized.get("time_iso") or _now_iso()
    normalized["first_seen_at"] = normalized.get("first_seen_at") or normalized["time_iso"]
    normalized["last_seen_at"] = normalized.get("last_seen_at") or normalized["time_iso"]
    normalized["occurrence_count"] = int(normalized.get("occurrence_count", 1) or 1)
    normalized["handled"] = bool(normalized.get("handled", False))
    normalized["handled_at"] = normalized.get("handled_at")
    normalized["handled_by"] = normalized.get("handled_by")
    normalized["resolution"] = normalized.get("resolution")
    normalized["linked_task_id"] = normalized.get("linked_task_id")
    normalized["action_note"] = normalized.get("action_note")
    normalized["status"] = "handled" if normalized["handled"] else "active"
    return normalized


def _merge_duplicate_loaded_discoveries(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    active_by_fingerprint: Dict[str, Dict[str, Any]] = {}
    duplicate_ids: List[str] = []

    for raw_item in items:
        item = _normalize_discovery_payload(raw_item)
        fp = item["fingerprint"]
        if item.get("handled"):
            merged.append(item)
            continue
        existing = active_by_fingerprint.get(fp)
        if not existing:
            active_by_fingerprint[fp] = item
            merged.append(item)
            continue

        existing["occurrence_count"] = int(existing.get("occurrence_count", 1) or 1) + int(
            item.get("occurrence_count", 1) or 1
        )
        existing["first_seen_at"] = min(existing.get("first_seen_at") or item["first_seen_at"], item["first_seen_at"])
        existing["last_seen_at"] = max(existing.get("last_seen_at") or item["last_seen_at"], item["last_seen_at"])
        existing["time_iso"] = max(existing.get("time_iso") or item["time_iso"], item["time_iso"])
        existing["time"] = item.get("time") or existing.get("time")
        existing["title"] = item.get("title") or existing.get("title")
        existing["summary"] = item.get("summary") or existing.get("summary")
        existing["recommended_action"] = item.get("recommended_action") or existing.get("recommended_action")
        if _severity_rank(item.get("severity", "info")) < _severity_rank(existing.get("severity", "info")):
            existing["severity"] = item.get("severity", existing.get("severity"))
        duplicate_ids.append(item["id"])

    for duplicate_id in duplicate_ids:
        try:
            state_store.delete_discovery(duplicate_id)
        except Exception as e:
            _log.warning("删除重复 discovery 失败 %s: %s", duplicate_id, e)

    for item in merged:
        try:
            state_store.upsert_discovery(item["id"], item)
        except Exception as e:
            _log.warning("回写聚合后的 discovery 失败 %s: %s", item["id"], e)
    return merged


def _find_active_discovery_by_fingerprint(fingerprint: str) -> Optional[Dict[str, Any]]:
    for item in discoveries:
        if item.get("fingerprint") == fingerprint and not item.get("handled", False):
            return item
    return None


def _append_discovery_event(discovery_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    try:
        state_store.append_discovery_event(discovery_id, event_type, payload)
    except Exception as e:
        _log.warning("记录 discovery event 失败 %s/%s: %s", discovery_id, event_type, e)


def _add_discovery(category: str, type: str, title: str, summary: str, level: str, source: str,
                   severity: str = "info", entity_type: str = "", entity_id: str = "",
                   recommended_action: str = "") -> None:
    """添加一条自主发现"""
    now_iso = _now_iso()
    fingerprint = _discovery_fingerprint(category, type, title, source, entity_type, entity_id)
    existing = _find_active_discovery_by_fingerprint(fingerprint)
    if existing:
        previous_count = int(existing.get("occurrence_count", 1) or 1)
        existing["category"] = category
        existing["type"] = type
        existing["title"] = title
        existing["summary"] = summary
        existing["level"] = level
        existing["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing["time_iso"] = now_iso
        existing["last_seen_at"] = now_iso
        existing["source"] = source
        if _severity_rank(severity) < _severity_rank(existing.get("severity", "info")):
            existing["severity"] = severity
        existing["entity_type"] = entity_type
        existing["entity_id"] = entity_id
        existing["recommended_action"] = recommended_action
        existing["occurrence_count"] = previous_count + 1
        existing["status"] = "active"
        payload = existing
        discovery_id = existing["id"]
        log_action = "更新"
        event_type = "reoccurred"
    else:
        d = {
            "id": f"d_{uuid.uuid4().hex[:10]}",
            "fingerprint": fingerprint,
            "category": category,
            "type": type,
            "title": title,
            "summary": summary,
            "level": level,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "time_iso": now_iso,
            "first_seen_at": now_iso,
            "last_seen_at": now_iso,
            "source": source,
            "severity": severity,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "recommended_action": recommended_action,
            "occurrence_count": 1,
            "handled": False,
            "handled_at": None,
            "handled_by": None,
            "resolution": None,
            "linked_task_id": None,
            "action_note": None,
            "status": "active",
        }
        discoveries.append(d)
        payload = d
        discovery_id = d["id"]
        log_action = "新增"
        event_type = "created"
    try:
        state_store.upsert_discovery(discovery_id, payload)
    except Exception as e:
        _log.warning("保存 discovery 失败 %s: %s", discovery_id, e)
    _append_discovery_event(discovery_id, event_type, {
        "level": level,
        "category": category,
        "type": type,
        "title": title,
        "severity": severity,
        "source": source,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "occurrence_count": payload.get("occurrence_count", 1),
        "time_iso": now_iso,
    })
    _log.info("Heartbeat %s发现: [%s/%s] %s - %s", log_action, level, category, type, title)


def load_persistent_discoveries() -> None:
    global discoveries
    try:
        discoveries = _merge_duplicate_loaded_discoveries(state_store.load_discoveries())
    except Exception as e:
        _log.warning("加载持久化 discoveries 失败: %s", e)


async def run_l0_realtime() -> None:
    """L0 实时监控：设备告警、任务队列、ETL 管道"""
    from quantamind.server import hands_secsgem as secs, hands_seatunnel as st
    equip = await asyncio.to_thread(secs.list_equipment)
    for e in equip.get("equipment", []):
        if e.get("alarms_count", 0) > 0:
            _add_discovery("告警", "设备告警", f"{e['equipment_id']} 有 {e['alarms_count']} 条告警",
                          f"设备 {e['equipment_id']} 检测到告警，当前状态 {e.get('state', '未知')}，建议检查。",
                          "L0", "Heartbeat 实时监控", severity="high",
                          entity_type="equipment", entity_id=e["equipment_id"],
                          recommended_action=f"检查设备 {e['equipment_id']} 的告警详情，并确认是否需要停机或切换配方。")
    pipeline = await asyncio.to_thread(st.get_pipeline_status)
    if pipeline.get("running", 0) < pipeline.get("total_jobs", 0):
        stopped = pipeline["total_jobs"] - pipeline["running"]
        if stopped > 0:
            _add_discovery("告警", "管道异常", f"{stopped} 个 ETL 管道未运行",
                          f"SeaTunnel 共 {pipeline['total_jobs']} 个管道，{pipeline['running']} 个运行中，{stopped} 个停止。建议检查。",
                          "L0", "Heartbeat 实时监控", severity="medium",
                          entity_type="pipeline", entity_id="seatunnel",
                          recommended_action="检查 SeaTunnel 管道状态，优先恢复停止或延迟的同步任务。")


async def run_l1_data_patrol() -> None:
    """L1 数据巡检：质量检查、新数据检查"""
    from quantamind.server import hands_qdata as qd, hands_warehouse as doris
    for table in ["qubit_characterization", "yield_records", "calibration_records"]:
        qc = await asyncio.to_thread(qd.run_quality_check, table)
        if qc.get("quality_score", 100) < 90:
            _add_discovery("数据", "数据质量", f"{table} 质量得分 {qc['quality_score']}",
                          f"表 {table} 检测到 {qc.get('issues_found', 0)} 个问题，质量得分 {qc['quality_score']}%，建议排查。",
                          "L1", "Heartbeat 数据巡检", severity="medium",
                          entity_type="table", entity_id=table,
                          recommended_action=f"查看表 {table} 的质量问题明细，确认是否存在空值、范围异常或格式错误。")
    yield_data = await asyncio.to_thread(doris.query_yield_trend, None, 5)
    avg = yield_data.get("average_yield_pct", 100)
    if avg < 90:
        _add_discovery("数据", "良率预警", f"近期良率均值 {avg}%，低于 90% 阈值",
                      f"最近 5 批良率均值 {avg}%，建议分析根因。",
                      "L1", "Heartbeat 数据巡检", severity="high",
                      entity_type="yield", entity_id="recent_batches",
                      recommended_action="优先查看良率趋势与缺陷分布，联动制造批次、设备与校准记录做根因分析。")


async def run_l2_experiment_suggestion() -> None:
    """L2 实验建议：基于最新测控数据给出下一步建议"""
    from quantamind.server import hands_warehouse as doris
    qubit_data = await asyncio.to_thread(doris.query_qubit_characterization)
    for q in qubit_data.get("data", []):
        if q.get("T1_us", 999) < 35:
            _add_discovery("实验", "实验建议", f"{q['qubit']} T1 偏低（{q['T1_us']}μs）",
                          f"{q['qubit']} 的 T1={q['T1_us']}μs 低于 35μs 阈值，建议重新校准或检查微波环境噪声。",
                          "L2", "Heartbeat 实验建议", severity="medium",
                          entity_type="qubit", entity_id=q["qubit"],
                          recommended_action=f"对 {q['qubit']} 追加 T1/T2、Readout、Ramsey 和噪声来源分析实验。")


async def run_l3_insight() -> None:
    """L3 假设与洞察：跨域关联分析"""
    from quantamind.server import hands_warehouse as doris
    cross = await asyncio.to_thread(doris.cross_domain_query, "yield_vs_calibration")
    if "correlation" in str(cross):
        _add_discovery("假设", "跨域洞察", "良率与校准保真度关联分析",
                      cross.get("example_result", {}).get("correlation", "分析结果待确认"),
                      "L3", "Heartbeat 假设挖掘", severity="info",
                      entity_type="cross_domain", entity_id="yield_vs_calibration",
                      recommended_action="继续做设计、制造、校准三域关联分析，确认是否存在可重复的因果关系。")


async def run_l4_intel_digest() -> None:
    """L4 外部情报：每日 arXiv 情报检索、入库与推送"""
    global _last_intel_report_id
    from quantamind.server import arxiv_intel

    result = await asyncio.to_thread(arxiv_intel.run_daily_digest, False)
    status = result.get("status")
    if status == "exists":
        return
    report = result.get("report") or {}
    report_id = report.get("report_id")
    if not report_id:
        return
    if report_id == _last_intel_report_id:
        return
    _last_intel_report_id = report_id

    papers_count = report.get("papers_count", 0)
    delivery = ((report.get("delivery") or {}).get("feishu") or {}).get("status", "unknown")
    topics = report.get("topic_counts", {})
    _add_discovery(
        "情报",
        "论文日报",
        f"{report.get('report_date', '')} arXiv 情报日报",
        f"已生成外部情报日报，收录 {papers_count} 篇近期论文。主题分布：{topics}。飞书推送状态：{delivery}。",
        "L4",
        "Heartbeat 外部情报",
        severity="info",
        entity_type="intel_report",
        entity_id=report_id,
        recommended_action="由知识工程师复核重点论文，将高价值论文转化为专题知识卡片和技术路线图。",
    )


async def run_intel_cache_warm() -> None:
    from quantamind.server import arxiv_intel

    result = await asyncio.to_thread(
        arxiv_intel.warm_recent_cache,
        config.INTEL_CACHE_WARM_LOOKBACK_DAYS,
        6,
    )
    _log.info(
        "情报缓存预热完成: status=%s records=%s live=%s backends=%s",
        result.get("status"),
        result.get("records_count"),
        result.get("live_records_count"),
        result.get("backends"),
    )


async def run_taxonomy_engineer_warm() -> None:
    from quantamind.server import arxiv_intel

    result = await asyncio.to_thread(arxiv_intel.run_taxonomy_engineer_update, False)
    _log.info(
        "技术体系工程师更新完成: status=%s libraries=%s updated_points=%s",
        result.get("status"),
        result.get("libraries"),
        result.get("updated_points"),
    )
    if result.get("status") == "updated":
        _add_discovery(
            "情报",
            "技术体系补树",
            "技术体系工程师完成一次补树更新",
            f"已更新 {result.get('libraries', 0)} 条体系库，补充 {result.get('updated_points', 0)} 个技术点证据与补充词。",
            "L4",
            "Heartbeat 技术体系工程师",
            severity="info",
            entity_type="taxonomy_engineer",
            entity_id=result.get("updated_at", ""),
            recommended_action="知识工程师可抽查新增证据词，确认是否需要升级为正式技术点或新模块。",
        )


async def run_heartbeat_once() -> None:
    """执行一次完整心跳（所有层级）"""
    global _last_run
    _log.info("Heartbeat 执行开始")
    try:
        await run_l0_realtime()
        await run_l1_data_patrol()
        await run_l2_experiment_suggestion()
        await run_l3_insight()
    except Exception as e:
        _log.error("Heartbeat 执行异常: %s", e)
    _last_run = _now_iso()
    _log.info("Heartbeat 执行完成，共 %d 条发现", len(discoveries))


async def heartbeat_loop(interval_minutes: Optional[int] = None) -> None:
    """持续运行心跳循环"""
    global _running
    if _running:
        return
    _running = True
    interval = (interval_minutes or config.HEARTBEAT_INTERVAL_MINUTES) * 60

    _log.info("Heartbeat 循环启动，间隔 %d 秒", interval)
    # 启动时立即执行一次
    await run_heartbeat_once()

    while _running:
        await asyncio.sleep(interval)
        await run_heartbeat_once()


def _compute_next_intel_run(now: Optional[datetime] = None) -> datetime:
    current = now or datetime.now().astimezone()
    next_run = current.replace(
        hour=config.INTEL_SCHEDULE_HOUR,
        minute=config.INTEL_SCHEDULE_MINUTE,
        second=0,
        microsecond=0,
    )
    if current >= next_run:
        next_run += timedelta(days=1)
    return next_run


def _scheduled_intel_time_for_day(now: Optional[datetime] = None) -> datetime:
    current = now or datetime.now().astimezone()
    return current.replace(
        hour=config.INTEL_SCHEDULE_HOUR,
        minute=config.INTEL_SCHEDULE_MINUTE,
        second=0,
        microsecond=0,
    )


def _should_run_startup_intel_catchup(now: Optional[datetime] = None) -> bool:
    current = now or datetime.now().astimezone()
    scheduled = _scheduled_intel_time_for_day(current)
    if current < scheduled:
        return False
    if not state_store.get_health().get("available", False):
        _log.warning("State store 不可用，跳过启动补发，避免重复生成当日报告")
        return False
    report_id = f"intel-{current.strftime('%Y-%m-%d')}"
    existing = state_store.get_intel_report(report_id)
    return not bool(existing or _last_intel_report_id == report_id)


async def intel_scheduler_loop() -> None:
    global _intel_scheduler_running, _next_intel_run
    if _intel_scheduler_running:
        return
    _intel_scheduler_running = True
    _log.info("情报员定时任务已启动，每日 %02d:%02d 执行", config.INTEL_SCHEDULE_HOUR, config.INTEL_SCHEDULE_MINUTE)
    while not _running:
        await asyncio.sleep(1.0)
    from quantamind.server import arxiv_intel

    await asyncio.to_thread(arxiv_intel.flush_pending_feishu_for_today)
    if _should_run_startup_intel_catchup():
        _log.info("检测到今日 %02d:%02d 日报未发送，启动后自动补发一次", config.INTEL_SCHEDULE_HOUR, config.INTEL_SCHEDULE_MINUTE)
        await run_l4_intel_digest()
    while _running:
        next_run = _compute_next_intel_run()
        _next_intel_run = next_run.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        wait_seconds = max((next_run - datetime.now().astimezone()).total_seconds(), 1.0)
        await asyncio.sleep(wait_seconds)
        if not _running:
            break
        await run_l4_intel_digest()


async def intel_cache_warmer_loop() -> None:
    global _intel_cache_warmer_running, _next_intel_cache_warm
    if _intel_cache_warmer_running:
        return
    _intel_cache_warmer_running = True
    interval_seconds = max(config.INTEL_CACHE_WARM_INTERVAL_MINUTES, 30) * 60
    _log.info(
        "情报缓存预热任务已启动，每 %d 分钟预热近 %d 天缓存",
        config.INTEL_CACHE_WARM_INTERVAL_MINUTES,
        config.INTEL_CACHE_WARM_LOOKBACK_DAYS,
    )
    while not _running:
        await asyncio.sleep(1.0)
    while _running:
        next_run = datetime.now().astimezone() + timedelta(seconds=interval_seconds)
        _next_intel_cache_warm = next_run.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        await asyncio.sleep(interval_seconds)
        if not _running:
            break
        await run_intel_cache_warm()


async def taxonomy_engineer_loop() -> None:
    global _taxonomy_engineer_running, _next_taxonomy_engineer_run
    if _taxonomy_engineer_running:
        return
    _taxonomy_engineer_running = True
    interval_seconds = max(config.INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES, 60) * 60
    _log.info("技术体系工程师任务已启动，每 %d 分钟补树一次", config.INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES)
    while not _running:
        await asyncio.sleep(1.0)
    while _running:
        next_run = datetime.now().astimezone() + timedelta(seconds=interval_seconds)
        _next_taxonomy_engineer_run = next_run.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        await asyncio.sleep(interval_seconds)
        if not _running:
            break
        await run_taxonomy_engineer_warm()


def get_status() -> Dict[str, Any]:
    return {
        "running": _running,
        "last_run": _last_run,
        "discoveries_count": len(discoveries),
        "levels": HEARTBEAT_LEVELS,
        "next_intel_run": _next_intel_run,
        "next_intel_cache_warm": _next_intel_cache_warm,
        "next_taxonomy_engineer_run": _next_taxonomy_engineer_run,
        "last_intel_report_id": _last_intel_report_id,
    }


def get_discoveries(category_filter: Optional[str] = None, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list(discoveries)
    if category_filter:
        items = [d for d in items if d.get("category") == category_filter]
    if type_filter:
        items = [d for d in items if d.get("type") == type_filter]
    items.sort(key=lambda d: d.get("last_seen_at") or d.get("time_iso", ""), reverse=True)
    return items


def list_discovery_events(discovery_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    return state_store.list_discovery_events(discovery_id, limit=limit)


def get_discovery_by_id(discovery_id: str) -> Optional[Dict[str, Any]]:
    for item in discoveries:
        if item.get("id") == discovery_id:
            return item
    return None


def link_discovery_task(discovery_id: str, task_id: str,
                        action_note: Optional[str] = None,
                        created_by: Optional[str] = None,
                        task_title: Optional[str] = None,
                        task_type: Optional[str] = None,
                        needs_approval: Optional[bool] = None) -> Dict[str, Any]:
    item = get_discovery_by_id(discovery_id)
    if not item:
        return {"error": f"discovery {discovery_id} not found"}
    item["linked_task_id"] = task_id
    if action_note:
        item["action_note"] = action_note
    item["last_task_linked_at"] = _now_iso()
    try:
        state_store.upsert_discovery(discovery_id, item)
    except Exception as e:
        _log.warning("更新 discovery 任务关联失败 %s: %s", discovery_id, e)
    _append_discovery_event(discovery_id, "task_linked", {
        "task_id": task_id,
        "created_by": created_by,
        "action_note": action_note,
        "task_title": task_title,
        "task_type": task_type,
        "needs_approval": needs_approval,
        "time_iso": _now_iso(),
    })
    return item


def mark_discovery_handled(discovery_id: str, handled: bool = True,
                          handled_by: Optional[str] = None,
                          resolution: Optional[str] = None,
                          linked_task_id: Optional[str] = None,
                          action_note: Optional[str] = None) -> Dict[str, Any]:
    for item in discoveries:
        if item.get("id") == discovery_id:
            item["handled"] = handled
            item["handled_at"] = _now_iso() if handled else None
            item["handled_by"] = handled_by if handled else None
            item["resolution"] = resolution if handled else None
            item["linked_task_id"] = linked_task_id if handled else None
            item["action_note"] = action_note if handled else None
            item["status"] = "handled" if handled else "active"
            try:
                state_store.upsert_discovery(discovery_id, item)
            except Exception as e:
                _log.warning("更新 discovery handled 状态失败 %s: %s", discovery_id, e)
            _append_discovery_event(discovery_id, "handled" if handled else "reopened", {
                "handled": handled,
                "handled_at": item.get("handled_at"),
                "handled_by": handled_by,
                "resolution": resolution,
                "linked_task_id": linked_task_id,
                "action_note": action_note,
                "time_iso": _now_iso(),
            })
            return item
    return {"error": f"discovery {discovery_id} not found"}
