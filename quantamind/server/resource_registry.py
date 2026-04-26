import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Iterable

from quantamind import config


RESOURCE_CATALOG: Dict[str, Dict[str, Any]] = {
    "design_postgres": {
        "label": "芯片设计主库",
        "kind": "postgresql",
        "category": "database",
        "description": "承载设计项目、资料索引与 QuantaMind 状态持久化。",
    },
    "mes_sqlserver": {
        "label": "MES 业务库",
        "kind": "sqlserver",
        "category": "database",
        "description": "承载 CHIPMES / MES 业务表、工单、批次、良率与设备数据。",
    },
    "mes_chipmes": {
        "label": "CHIPMES 服务",
        "kind": "http",
        "category": "service",
        "description": "制造执行系统主服务入口。",
    },
    "mes_openmes": {
        "label": "OpenMES 服务",
        "kind": "http",
        "category": "service",
        "description": "制造业务补充服务入口。",
    },
    "mes_grafana": {
        "label": "Grafana",
        "kind": "http",
        "category": "service",
        "description": "制造与设备看板服务。",
    },
    "datacenter_doris": {
        "label": "OLAP 仓库（Doris/SelectDB/PG/CH）",
        "kind": "http",
        "category": "analytics",
        "description": "分析型数据仓库 HTTP 入口（与 datacenter_warehouse.engine 配合）。",
    },
    "datacenter_qdata": {
        "label": "qData",
        "kind": "http",
        "category": "governance",
        "description": "数据治理与服务平台入口。",
    },
    "datacenter_seatunnel": {
        "label": "SeaTunnel",
        "kind": "http",
        "category": "pipeline",
        "description": "数据同步与 ETL 管道入口。",
    },
    "storage_minio": {
        "label": "MinIO",
        "kind": "http",
        "category": "storage",
        "description": "对象存储服务，承载文档、报告、版图和资料资产。",
    },
    "ai_pgvector": {
        "label": "pgvector",
        "kind": "postgresql-extension",
        "category": "vector",
        "description": "QuantaMind 知识检索与向量搜索层。",
    },
}
_STATUS_CACHE: Dict[str, Any] = {"statuses": {}, "checked_at": None}
_CACHE_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _http_status(base_url: str, paths: Iterable[str], timeout: int = 3) -> Dict[str, Any]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    checked = []
    for path in paths:
        url = base_url.rstrip("/") + path
        try:
            req = urllib.request.Request(url, method="GET")
            with opener.open(req, timeout=timeout) as resp:
                checked.append({"url": url, "status_code": resp.status})
                if resp.status < 500:
                    return {"connected": True, "detail": f"HTTP {resp.status}", "checked": checked}
        except urllib.error.HTTPError as e:
            checked.append({"url": url, "status_code": e.code})
            if e.code < 500:
                return {"connected": True, "detail": f"HTTP {e.code}", "checked": checked}
        except Exception as e:
            checked.append({"url": url, "error": str(e)})
    return {"connected": False, "detail": "unreachable", "checked": checked}


def _socket_status(host: str, port: int, timeout: int = 3) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return {"connected": True, "detail": f"TCP {host}:{port}"}
    except Exception as e:
        return {"connected": False, "detail": str(e)}


def _pgvector_status(cfg: Dict[str, Any]) -> Dict[str, Any]:
    base = _socket_status(cfg["host"], cfg["port"])
    if not base["connected"]:
        return base
    try:
        import psycopg

        with psycopg.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=3,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                row = cur.fetchone()
                if row:
                    return {"connected": True, "detail": f"pgvector {row[0]}"}
                return {"connected": False, "detail": "PostgreSQL 已连接，但未安装 pgvector 扩展"}
    except Exception as e:
        return {"connected": False, "detail": str(e)}


def list_resources(mask_secrets: bool = False) -> Dict[str, Any]:
    return {
        "catalog": RESOURCE_CATALOG,
        "configs": config.get_database_configs(mask_secrets=mask_secrets),
    }


def update_resources(updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    config.update_database_configs(updates)
    config.save_persistent_config()
    return list_resources(mask_secrets=False)


def _compute_resource_statuses() -> Dict[str, Any]:
    cfg = config.get_database_configs(mask_secrets=False)
    checked_at = _now_iso()
    probes = {
        "design_postgres": lambda: _socket_status(cfg["design_postgres"]["host"], cfg["design_postgres"]["port"], timeout=1),
        "mes_sqlserver": lambda: _socket_status(cfg["mes_sqlserver"]["host"], cfg["mes_sqlserver"]["port"], timeout=1),
        "mes_chipmes": lambda: _http_status(cfg["mes_chipmes"]["base_url"], ["/actuator/info", "/actuator/health", "/doc.html", "/"], timeout=1),
        "mes_openmes": lambda: _http_status(cfg["mes_openmes"]["base_url"], ["/system/health"], timeout=1),
        "mes_grafana": lambda: _http_status(cfg["mes_grafana"]["base_url"], ["/api/health"], timeout=1),
        "datacenter_doris": lambda: _http_status(cfg["datacenter_doris"]["base_url"], ["/api/bootstrap"], timeout=1),
        "datacenter_qdata": lambda: _http_status(cfg["datacenter_qdata"]["base_url"], ["/api/system/health"], timeout=1),
        "datacenter_seatunnel": lambda: _http_status(cfg["datacenter_seatunnel"]["base_url"], ["/api/v1/overview"], timeout=1),
        "storage_minio": lambda: _http_status(cfg["storage_minio"]["endpoint"], ["/minio/health/live", "/"], timeout=1),
        "ai_pgvector": lambda: _pgvector_status(cfg["ai_pgvector"]),
    }
    statuses: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(probes))) as pool:
        futures = {name: pool.submit(fn) for name, fn in probes.items()}
        for key, fut in futures.items():
            try:
                statuses[key] = fut.result(timeout=2)
            except Exception as e:
                statuses[key] = {"connected": False, "detail": str(e)}
    for key, status in statuses.items():
        status["label"] = RESOURCE_CATALOG[key]["label"]
        status["kind"] = RESOURCE_CATALOG[key]["kind"]
        status["category"] = RESOURCE_CATALOG[key]["category"]
        status["description"] = RESOURCE_CATALOG[key]["description"]
        status["checked_at"] = checked_at
    return {"statuses": statuses, "checked_at": checked_at}


def get_resource_statuses(force_refresh: bool = True) -> Dict[str, Any]:
    if force_refresh:
        data = _compute_resource_statuses()
        with _CACHE_LOCK:
            _STATUS_CACHE.update(data)
        return data
    with _CACHE_LOCK:
        if _STATUS_CACHE.get("statuses"):
            return dict(_STATUS_CACHE)
    data = _compute_resource_statuses()
    with _CACHE_LOCK:
        _STATUS_CACHE.update(data)
    return data
