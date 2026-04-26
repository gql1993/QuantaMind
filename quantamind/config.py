# QuantaMind 配置（持久化到 ~/.quantamind/config.json）

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ENV_FILE = PROJECT_ROOT / ".quantamind.local.env"


def _load_project_env_file() -> None:
    """从项目根目录加载本地 env 文件，不覆盖已有环境变量。"""
    if not PROJECT_ENV_FILE.exists():
        return
    try:
        for raw_line in PROJECT_ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ[key] = value
    except Exception:
        pass


_load_project_env_file()


def _env_first(*keys: str) -> Optional[str]:
    for k in keys:
        v = os.environ.get(k)
        if v is not None and v != "":
            return v
    return None


def _default_data_root() -> Path:
    explicit = _env_first("QUANTAMIND_ROOT", "AETHERQ_ROOT")
    if explicit:
        return Path(explicit).resolve()
    home = Path.home()
    p_new = home / ".quantamind"
    p_old = home / ".aetherq"
    if p_old.exists() and not p_new.exists():
        return p_old.resolve()
    return p_new.resolve()


DEFAULT_ROOT = _default_data_root()
MEMORY_DIR = DEFAULT_ROOT / "memory"
PROJECTS_DIR = MEMORY_DIR / "projects"
SKILLS_DIR = DEFAULT_ROOT / "skills"
CONFIG_FILE = DEFAULT_ROOT / "config.json"

# Gateway（支持旧环境变量名 AETHERQ_* 作为回退）
GATEWAY_HOST = _env_first("QUANTAMIND_GATEWAY_HOST", "AETHERQ_GATEWAY_HOST") or "0.0.0.0"
_p_gw = _env_first("QUANTAMIND_GATEWAY_PORT", "AETHERQ_GATEWAY_PORT")
GATEWAY_PORT = int(_p_gw) if _p_gw else 18789
GATEWAY_WS_PATH = "/ws"

# LLM 默认值（环境变量 > config.json > 下方默认值）
LLM_PROVIDER = _env_first("QUANTAMIND_LLM_PROVIDER", "AETHERQ_LLM_PROVIDER") or "ollama"
LLM_MODEL = _env_first("QUANTAMIND_LLM_MODEL", "AETHERQ_LLM_MODEL") or "qwen2.5:7b"
LLM_API_BASE = _env_first("QUANTAMIND_LLM_API_BASE", "AETHERQ_LLM_API_BASE") or "http://localhost:11434"
LLM_API_KEY = _env_first("QUANTAMIND_LLM_API_KEY", "AETHERQ_LLM_API_KEY") or ""

# Heartbeat
_hb = _env_first("QUANTAMIND_HEARTBEAT_INTERVAL", "AETHERQ_HEARTBEAT_INTERVAL")
HEARTBEAT_INTERVAL_MINUTES = int(_hb) if _hb else 30

# Intelligence / arXiv digest
INTEL_FEISHU_WEBHOOK = _env_first("QUANTAMIND_FEISHU_WEBHOOK", "FEISHU_WEBHOOK") or ""
INTEL_FEISHU_KEYWORD = _env_first("QUANTAMIND_FEISHU_KEYWORD", "FEISHU_KEYWORD") or ""
INTEL_FEISHU_APP_ID = _env_first("QUANTAMIND_FEISHU_APP_ID", "FEISHU_APP_ID") or ""
INTEL_FEISHU_APP_SECRET = _env_first("QUANTAMIND_FEISHU_APP_SECRET", "FEISHU_APP_SECRET") or ""
_intel_days = _env_first("QUANTAMIND_INTEL_LOOKBACK_DAYS")
INTEL_LOOKBACK_DAYS = int(_intel_days) if _intel_days else 2
_intel_max = _env_first("QUANTAMIND_INTEL_MAX_PAPERS")
INTEL_MAX_PAPERS = int(_intel_max) if _intel_max else 12
_intel_hour = _env_first("QUANTAMIND_INTEL_SCHEDULE_HOUR")
INTEL_SCHEDULE_HOUR = int(_intel_hour) if _intel_hour else 9
_intel_minute = _env_first("QUANTAMIND_INTEL_SCHEDULE_MINUTE")
INTEL_SCHEDULE_MINUTE = int(_intel_minute) if _intel_minute else 0
_intel_cache_warm = _env_first("QUANTAMIND_INTEL_CACHE_WARM_INTERVAL_MINUTES")
INTEL_CACHE_WARM_INTERVAL_MINUTES = int(_intel_cache_warm) if _intel_cache_warm else 180
_intel_cache_days = _env_first("QUANTAMIND_INTEL_CACHE_WARM_LOOKBACK_DAYS")
INTEL_CACHE_WARM_LOOKBACK_DAYS = int(_intel_cache_days) if _intel_cache_days else 5
_intel_taxonomy_interval = _env_first("QUANTAMIND_INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES")
INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES = int(_intel_taxonomy_interval) if _intel_taxonomy_interval else 720

DEFAULT_DATABASE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "design_postgres": {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "quantamind_design",
        "user": "postgres",
        "password": "",
    },
    "mes_sqlserver": {
        "host": "127.0.0.1",
        "port": 1433,
        "database": "chipmesdb",
        "user": "sa",
        "password": "123456",
    },
    "mes_chipmes": {
        "base_url": "http://127.0.0.1:8082",
    },
    "mes_openmes": {
        "base_url": "http://localhost:8080/api",
    },
    "mes_grafana": {
        "base_url": "http://localhost:3000",
        "token": "",
    },
    "datacenter_doris": {
        "base_url": "http://localhost:8030",
        "mysql_port": 9030,
        "cluster": "default_cluster",
        "database": "quantum_data",
    },
    # 覆盖 datacenter_doris 的同名字段；engine 决定健康检查与 query_sql 路径
    "datacenter_warehouse": {
        "engine": "postgresql",
        "display_name": "PostgreSQL（分析库）",
        "base_url": "http://localhost:8030",
        "mysql_port": 9030,
        "cluster": "default_cluster",
        "database": "quantum_data",
        "clickhouse_http": "http://127.0.0.1:8123",
    },
    "datacenter_qdata": {
        "base_url": "http://localhost:8180",
    },
    "datacenter_seatunnel": {
        "base_url": "http://localhost:8090",
        "paths_running_jobs": [
            "/api/v1/running-jobs",
            "/hazelcast/rest/maps/running-jobs",
        ],
        # 非空时覆盖 UI 中「目标（Sink）」与任务名里的 Doris 替换文案（默认用 datacenter_warehouse.display_name）
        "sink_display_override": "",
    },
    "storage_minio": {
        "endpoint": "http://127.0.0.1:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "bucket": "quantamind",
    },
    "ai_pgvector": {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "quantamind_design",
        "user": "postgres",
        "password": "postgres123",
        "table": "knowledge_chunks",
        "dimensions": 64,
    },
}
DATABASE_CONFIGS: Dict[str, Dict[str, Any]] = copy.deepcopy(DEFAULT_DATABASE_CONFIGS)


def ensure_dirs() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def load_persistent_config() -> None:
    """启动时从 config.json 加载已保存的配置（环境变量优先级更高）"""
    global LLM_PROVIDER, LLM_MODEL, LLM_API_BASE, LLM_API_KEY
    global DATABASE_CONFIGS, INTEL_FEISHU_WEBHOOK, INTEL_FEISHU_KEYWORD, INTEL_FEISHU_APP_ID, INTEL_FEISHU_APP_SECRET
    global INTEL_CACHE_WARM_INTERVAL_MINUTES, INTEL_CACHE_WARM_LOOKBACK_DAYS, INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES
    global INTEL_SCHEDULE_HOUR, INTEL_SCHEDULE_MINUTE
    if not CONFIG_FILE.exists():
        return
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not _env_first("QUANTAMIND_LLM_PROVIDER", "AETHERQ_LLM_PROVIDER") and data.get("llm_provider"):
            LLM_PROVIDER = data["llm_provider"]
        if not _env_first("QUANTAMIND_LLM_MODEL", "AETHERQ_LLM_MODEL") and data.get("llm_model"):
            LLM_MODEL = data["llm_model"]
        if not _env_first("QUANTAMIND_LLM_API_BASE", "AETHERQ_LLM_API_BASE") and data.get("llm_api_base"):
            LLM_API_BASE = data["llm_api_base"]
        if not _env_first("QUANTAMIND_LLM_API_KEY", "AETHERQ_LLM_API_KEY") and data.get("llm_api_key"):
            LLM_API_KEY = data["llm_api_key"]
        if not _env_first("QUANTAMIND_FEISHU_WEBHOOK", "FEISHU_WEBHOOK") and data.get("intel_feishu_webhook"):
            INTEL_FEISHU_WEBHOOK = data["intel_feishu_webhook"]
        if not _env_first("QUANTAMIND_FEISHU_KEYWORD", "FEISHU_KEYWORD") and data.get("intel_feishu_keyword"):
            INTEL_FEISHU_KEYWORD = data["intel_feishu_keyword"]
        if not _env_first("QUANTAMIND_FEISHU_APP_ID", "FEISHU_APP_ID") and data.get("intel_feishu_app_id"):
            INTEL_FEISHU_APP_ID = data["intel_feishu_app_id"]
        if not _env_first("QUANTAMIND_FEISHU_APP_SECRET", "FEISHU_APP_SECRET") and data.get("intel_feishu_app_secret"):
            INTEL_FEISHU_APP_SECRET = data["intel_feishu_app_secret"]
        if not _env_first("QUANTAMIND_INTEL_CACHE_WARM_INTERVAL_MINUTES") and data.get("intel_cache_warm_interval_minutes"):
            INTEL_CACHE_WARM_INTERVAL_MINUTES = int(data["intel_cache_warm_interval_minutes"])
        if not _env_first("QUANTAMIND_INTEL_CACHE_WARM_LOOKBACK_DAYS") and data.get("intel_cache_warm_lookback_days"):
            INTEL_CACHE_WARM_LOOKBACK_DAYS = int(data["intel_cache_warm_lookback_days"])
        if not _env_first("QUANTAMIND_INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES") and data.get("intel_taxonomy_update_interval_minutes"):
            INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES = int(data["intel_taxonomy_update_interval_minutes"])
        if not _env_first("QUANTAMIND_INTEL_SCHEDULE_HOUR") and data.get("intel_schedule_hour") is not None:
            try:
                INTEL_SCHEDULE_HOUR = max(0, min(23, int(data["intel_schedule_hour"])))
            except (TypeError, ValueError):
                pass
        if not _env_first("QUANTAMIND_INTEL_SCHEDULE_MINUTE") and data.get("intel_schedule_minute") is not None:
            try:
                INTEL_SCHEDULE_MINUTE = max(0, min(59, int(data["intel_schedule_minute"])))
            except (TypeError, ValueError):
                pass
        if isinstance(data.get("databases"), dict):
            for key, value in data["databases"].items():
                if key in DATABASE_CONFIGS and isinstance(value, dict):
                    DATABASE_CONFIGS[key].update(value)
    except Exception:
        pass


def save_persistent_config() -> None:
    """将当前 LLM 配置写入 config.json，重启后自动恢复"""
    ensure_dirs()
    data = {}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    data.update({
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL,
        "llm_api_base": LLM_API_BASE,
        "llm_api_key": LLM_API_KEY,
        "intel_feishu_webhook": INTEL_FEISHU_WEBHOOK,
        "intel_feishu_keyword": INTEL_FEISHU_KEYWORD,
        "intel_feishu_app_id": INTEL_FEISHU_APP_ID,
        "intel_feishu_app_secret": INTEL_FEISHU_APP_SECRET,
        "intel_cache_warm_interval_minutes": INTEL_CACHE_WARM_INTERVAL_MINUTES,
        "intel_cache_warm_lookback_days": INTEL_CACHE_WARM_LOOKBACK_DAYS,
        "intel_taxonomy_update_interval_minutes": INTEL_TAXONOMY_UPDATE_INTERVAL_MINUTES,
        "intel_schedule_hour": INTEL_SCHEDULE_HOUR,
        "intel_schedule_minute": INTEL_SCHEDULE_MINUTE,
        "databases": DATABASE_CONFIGS,
    })
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_database_config(name: str) -> Dict[str, Any]:
    return copy.deepcopy(DATABASE_CONFIGS.get(name, {}))


def get_database_configs(mask_secrets: bool = False) -> Dict[str, Dict[str, Any]]:
    data = copy.deepcopy(DATABASE_CONFIGS)
    if not mask_secrets:
        return data
    for cfg in data.values():
        for field in ("password", "secret_key", "access_key", "token"):
            if cfg.get(field):
                cfg[field] = "*" * 8
    return data


def update_database_configs(updates: Dict[str, Dict[str, Any]]) -> None:
    for key, value in updates.items():
        if key not in DATABASE_CONFIGS or not isinstance(value, dict):
            continue
        DATABASE_CONFIGS[key].update(value)


def update_intel_delivery(feishu_webhook: Optional[str] = None,
                          feishu_keyword: Optional[str] = None,
                          feishu_app_id: Optional[str] = None,
                          feishu_app_secret: Optional[str] = None,
                          schedule_hour: Optional[int] = None,
                          schedule_minute: Optional[int] = None) -> None:
    global INTEL_FEISHU_WEBHOOK, INTEL_FEISHU_KEYWORD, INTEL_FEISHU_APP_ID, INTEL_FEISHU_APP_SECRET
    global INTEL_SCHEDULE_HOUR, INTEL_SCHEDULE_MINUTE
    if feishu_webhook is not None:
        INTEL_FEISHU_WEBHOOK = feishu_webhook.strip()
    if feishu_keyword is not None:
        INTEL_FEISHU_KEYWORD = feishu_keyword.strip()
    if feishu_app_id is not None:
        INTEL_FEISHU_APP_ID = feishu_app_id.strip()
    if feishu_app_secret is not None:
        INTEL_FEISHU_APP_SECRET = feishu_app_secret.strip()
    if schedule_hour is not None:
        INTEL_SCHEDULE_HOUR = max(0, min(23, int(schedule_hour)))
    if schedule_minute is not None:
        INTEL_SCHEDULE_MINUTE = max(0, min(59, int(schedule_minute)))
    save_persistent_config()


# 启动时自动加载
load_persistent_config()
