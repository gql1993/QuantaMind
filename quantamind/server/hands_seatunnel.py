# Hands：Apache SeaTunnel（ETL）。优先从 SeaTunnel REST 拉取运行中任务，失败时回退示例数据。
from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

_log = logging.getLogger("quantamind.hands.seatunnel")

_last_jobs_cache: List[dict] = []
_MOCK_JOBS_EXTRA: List[dict] = []


def _seatunnel_cfg() -> dict:
    from quantamind import config as app_config
    return app_config.get_database_config("datacenter_seatunnel")


def _seatunnel_base() -> str:
    return str(_seatunnel_cfg().get("base_url", "http://localhost:8090")).rstrip("/")


def _running_job_paths() -> List[str]:
    c = _seatunnel_cfg()
    custom = c.get("paths_running_jobs")
    if isinstance(custom, list) and custom:
        return [str(p) for p in custom]
    return [
        "/api/v1/running-jobs",
        "/hazelcast/rest/maps/running-jobs",
    ]


def _is_overview_ok() -> bool:
    try:
        req = urllib.request.Request(f"{_seatunnel_base()}/api/v1/overview", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _http_get_json(url: str, timeout: float = 8.0) -> Any:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _vertex_sources_sinks(job: dict) -> tuple[str, str]:
    dag = job.get("jobDag") or job.get("job_dag") or {}
    verts = dag.get("vertexInfoMap") or dag.get("vertex_info_map") or []
    if isinstance(verts, dict):
        verts = list(verts.values())
    sources: List[str] = []
    sinks: List[str] = []
    for v in verts:
        if not isinstance(v, dict):
            continue
        t = str(v.get("type") or "").upper()
        name = str(v.get("vertexName") or v.get("vertex_name") or "")
        if "SOURCE" in t or t == "SOURCE":
            sources.append(name or "?")
        elif "SINK" in t or t == "SINK" or "TRANSFORM" in t:
            if "SINK" in t or t == "SINK":
                sinks.append(name or "?")
    src = sources[0] if sources else "—"
    snk = sinks[0] if sinks else "—"
    return src, snk


def _normalize_job(j: dict, idx: int) -> dict:
    job_id = str(j.get("jobId") or j.get("job_id") or j.get("id") or f"ST-{idx:03d}")
    name = str(j.get("jobName") or j.get("name") or job_id)
    status = str(j.get("jobStatus") or j.get("status") or "unknown").lower()
    metrics = j.get("metrics") or {}
    if isinstance(metrics, str):
        metrics = {}
    rec = 0
    for key in ("sinkWriteCount", "SinkWriteCount", "sourceReceivedCount", "SourceReceivedCount"):
        v = metrics.get(key)
        if v is not None and str(v).isdigit():
            rec = max(rec, int(v))
        elif isinstance(v, (int, float)):
            rec = max(rec, int(v))
    env = j.get("envOptions") or j.get("env") or {}
    sync_type = "streaming"
    if isinstance(env, dict):
        mode = str(env.get("job.mode") or env.get("job.mode".lower()) or "").lower()
        if mode in ("batch", "streaming"):
            sync_type = mode
    src, snk = _vertex_sources_sinks(j)
    return {
        "job_id": job_id,
        "name": name,
        "source": src,
        "sink": snk,
        "status": status,
        "sync_type": sync_type,
        "records_synced": rec,
    }


def _parse_jobs_payload(data: Any) -> List[dict]:
    if data is None:
        return []
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        if "jobs" in data and isinstance(data["jobs"], list):
            raw = data["jobs"]
        elif "data" in data and isinstance(data["data"], list):
            raw = data["data"]
        else:
            raw = []
    else:
        return []
    out: List[dict] = []
    for i, j in enumerate(raw):
        if isinstance(j, dict):
            out.append(_normalize_job(j, i + 1))
    return out


def _fetch_running_jobs_from_api() -> tuple[List[dict], Optional[str], bool]:
    """返回 (jobs, error, api_ok)。任一路径返回 HTTP 200 且解析成功则 api_ok=True（任务列表可为空）。"""
    base = _seatunnel_base()
    last_err: Optional[str] = None
    for path in _running_job_paths():
        url = base + path
        try:
            data = _http_get_json(url)
            parsed = _parse_jobs_payload(data)
            return parsed, None, True
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code} {path}"
        except Exception as e:
            last_err = str(e)
    return [], last_err, False


def _sink_label() -> str:
    try:
        from quantamind.server.hands_warehouse import get_default_sink_label
        return get_default_sink_label()
    except Exception:
        return "PostgreSQL"


def _ui_olap_label() -> str:
    """SeaTunnel 表格「目标」列与任务名中替代 Doris 的展示文案。"""
    c = _seatunnel_cfg()
    ov = c.get("sink_display_override")
    if isinstance(ov, str) and ov.strip():
        return ov.strip()
    return _sink_label()


def _rewrite_job_title(name: str, label: str) -> str:
    """将历史/集群中的「→ Doris」「Doris」换成当前 OLAP 展示名。"""
    if not name:
        return name
    n = re.sub(r"(→\s*)Doris(\s*（)", r"\1" + label + r"\2", name, flags=re.IGNORECASE)
    n = re.sub(r"(→\s*)Doris(\b)", r"\1" + label + r"\2", n, flags=re.IGNORECASE)
    if re.search(r"\bDoris\b", n, re.IGNORECASE):
        n = re.sub(r"\bDoris\b", label, n, flags=re.IGNORECASE)
    return n


def _rewrite_sink_display(raw: Optional[str]) -> str:
    """Sink 列：SeaTunnel 常返回插件名 doris / Doris-xxx，统一成配置中的 OLAP 名称。"""
    label = _ui_olap_label()
    if raw is None:
        return label
    s = str(raw).strip()
    if not s or s in ("—", "?"):
        return label
    sl = s.lower()
    if "doris" in sl:
        return label
    return s


def _rewrite_jobs_for_ui(jobs: List[dict]) -> List[dict]:
    label = _ui_olap_label()
    out: List[dict] = []
    for j in jobs:
        d = dict(j)
        d["sink"] = _rewrite_sink_display(d.get("sink"))
        nm = d.get("name")
        if isinstance(nm, str):
            d["name"] = _rewrite_job_title(nm, label)
        out.append(d)
    return out


def _fallback_mock_jobs() -> List[dict]:
    sink = _sink_label()
    return [
        {
            "job_id": "ST-001",
            "name": f"QCoDeS → {sink}（测控数据）",
            "source": "qcodes_sqlite",
            "sink": sink,
            "status": "running",
            "sync_type": "incremental",
            "records_synced": 12450,
        },
        {
            "job_id": "ST-002",
            "name": f"OpenMES → {sink}（产线数据）",
            "source": "mysql(openmes)",
            "sink": sink,
            "status": "running",
            "sync_type": "cdc",
            "records_synced": 8320,
        },
        {
            "job_id": "ST-003",
            "name": f"QuantaMind API → {sink}（设计元数据）",
            "source": "http(quantamind_gateway)",
            "sink": sink,
            "status": "completed",
            "sync_type": "batch",
            "records_synced": 156,
        },
        {
            "job_id": "ST-004",
            "name": f"Grafana InfluxDB → {sink}（设备时序）",
            "source": "influxdb",
            "sink": sink,
            "status": "running",
            "sync_type": "realtime",
            "records_synced": 98700,
        },
    ] + _MOCK_JOBS_EXTRA


def list_jobs() -> Dict[str, Any]:
    """列出同步任务：优先 SeaTunnel API，失败则返回与当前仓库 sink 一致的示例数据。"""
    global _last_jobs_cache
    jobs, api_err, api_ok = _fetch_running_jobs_from_api()
    if api_ok:
        jobs = _rewrite_jobs_for_ui(jobs)
        _last_jobs_cache = jobs
        return {
            "jobs": jobs,
            "count": len(jobs),
            "backend": "seatunnel",
            "api_error": None,
            "olap_display": _ui_olap_label(),
        }
    merged = _rewrite_jobs_for_ui(_fallback_mock_jobs())
    _last_jobs_cache = merged
    return {
        "jobs": merged,
        "count": len(merged),
        "backend": "mock",
        "api_error": api_err,
        "note": "SeaTunnel API 不可达（已展示与当前 OLAP 配置一致的示例）。",
        "olap_display": _ui_olap_label(),
    }


def get_job(job_id: str) -> Dict[str, Any]:
    """查询任务详情：先查缓存，再请求 job-info REST。"""
    for j in _last_jobs_cache:
        if j.get("job_id") == job_id:
            fixed = _rewrite_jobs_for_ui([j])[0]
            return {**fixed, "backend": "seatunnel" if _is_overview_ok() else "mock"}
    base = _seatunnel_base()
    for path in (f"/hazelcast/rest/maps/job-info/{job_id}", f"/api/v1/job/{job_id}"):
        try:
            data = _http_get_json(base + path)
            if isinstance(data, dict) and (data.get("jobId") or data.get("job_id")):
                parsed = _rewrite_jobs_for_ui([_normalize_job(data, 1)])[0]
                return {**parsed, "backend": "seatunnel", "raw": data}
        except Exception:
            continue
    return {"error": f"任务 {job_id} 不存在"}


def submit_sync_job(
    name: str,
    source_type: str,
    source_config: Dict,
    sink_type: str = "",
    sink_config: Optional[Dict] = None,
    sync_type: str = "batch",
) -> Dict[str, Any]:
    """登记一条同步任务（本地登记；真实提交需调用 SeaTunnel submit-job API）。"""
    sink = sink_type or _sink_label()
    job_id = f"ST-{len(_last_jobs_cache) + len(_MOCK_JOBS_EXTRA) + 1:03d}"
    job = {
        "job_id": job_id,
        "name": name,
        "source": source_type,
        "sink": sink,
        "status": "submitted",
        "sync_type": sync_type,
        "records_synced": 0,
    }
    _MOCK_JOBS_EXTRA.append(job)
    return {**job, "backend": "seatunnel" if _is_overview_ok() else "mock"}


def sync_qcodes_to_warehouse(experiment_name: Optional[str] = None) -> Dict[str, Any]:
    return submit_sync_job(
        name=f"QCoDeS → {_sink_label()}（{experiment_name or '全部'}）",
        source_type="qcodes_sqlite",
        source_config={"db_path": "~/.qcodes/experiments.db", "experiment": experiment_name},
        sync_type="incremental",
    )


def sync_mes_to_warehouse() -> Dict[str, Any]:
    return submit_sync_job(
        name=f"OpenMES → {_sink_label()}（产线 CDC）",
        source_type="mysql",
        source_config={"host": "localhost", "port": 3306, "database": "openmes"},
        sync_type="cdc",
    )


def sync_design_to_warehouse() -> Dict[str, Any]:
    return submit_sync_job(
        name=f"设计元数据 → {_sink_label()}",
        source_type="http",
        source_config={"url": "http://127.0.0.1:18789/api/v1/tasks?filter=completed"},
        sync_type="batch",
    )


# 向后兼容旧工具名
sync_qcodes_to_doris = sync_qcodes_to_warehouse
sync_mes_to_doris = sync_mes_to_warehouse
sync_design_to_doris = sync_design_to_warehouse


def get_pipeline_status() -> Dict[str, Any]:
    jobs = list_jobs().get("jobs") or []
    running = sum(1 for j in jobs if str(j.get("status", "")).lower() in ("running", "active", "running_job"))
    total_records = sum(int(j.get("records_synced") or 0) for j in jobs)
    return {
        "total_jobs": len(jobs),
        "running": running,
        "total_records_synced": total_records,
        "domains": {"设计域": 1, "制造域": 1, "测控域": 1, "设备时序": 1},
        "backend": "seatunnel" if _is_overview_ok() else "mock",
    }


def get_capabilities() -> Dict[str, Any]:
    sink = _sink_label()
    return {
        "source": "Apache SeaTunnel",
        "role": "数据集成 / ETL 管道",
        "features": [
            "100+ 数据源连接器",
            "批量 / 实时 / CDC",
            f"REST 拉取运行中任务（/api/v1/running-jobs 与 Hazelcast 兼容路径）",
            f"默认 sink 指向 OLAP：{sink}",
        ],
        "supported_sources": ["QCoDeS SQLite", "MySQL(OpenMES)", "HTTP(QuantaMind Gateway)", "InfluxDB", "PostgreSQL", "Kafka"],
        "supported_sinks": [sink, "ClickHouse", "PostgreSQL", "Kafka", "HTTP"],
        "connected": _is_overview_ok(),
    }
