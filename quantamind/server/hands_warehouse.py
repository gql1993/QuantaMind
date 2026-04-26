# Hands 适配器：数据中台 OLAP 仓库（可配置为 Doris / SelectDB / PostgreSQL / ClickHouse 等）
# 职责：量子数据中台的核心存储与查询引擎
# 配置：`datacenter_warehouse` 覆盖 `datacenter_doris` 默认值（向后兼容）

from typing import Any, Dict, List, Optional
import logging

_log = logging.getLogger("quantamind.hands.warehouse")


def _warehouse_cfg() -> dict:
    from quantamind import config as app_config
    w = app_config.get_database_config("datacenter_warehouse")
    d = app_config.get_database_config("datacenter_doris")
    out = {**d, **w}
    if not out.get("engine"):
        out["engine"] = "doris"
    return out


def _engine() -> str:
    return str(_warehouse_cfg().get("engine", "doris")).lower()


def _http_base() -> str:
    return _warehouse_cfg().get("base_url", "http://localhost:8030").rstrip("/")


def _pg_cfg() -> dict:
    c = _warehouse_cfg()
    pg = c.get("postgresql")
    if isinstance(pg, dict) and pg.get("host"):
        return pg
    from quantamind import config as app_config
    return app_config.get_database_config("design_postgres")


def _pg_ping() -> bool:
    try:
        import psycopg
        c = _pg_cfg()
        with psycopg.connect(
            host=c["host"],
            port=c["port"],
            dbname=c["database"],
            user=c["user"],
            password=c.get("password") or "",
            connect_timeout=2,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _is_connected() -> bool:
    eng = _engine()
    try:
        if eng in ("doris", "selectdb"):
            import urllib.request
            req = urllib.request.Request(f"{_http_base()}/api/bootstrap", method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        if eng == "clickhouse":
            import urllib.request
            ch = str(_warehouse_cfg().get("clickhouse_http", "http://127.0.0.1:8123")).rstrip("/")
            req = urllib.request.Request(f"{ch}/ping", method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        if eng == "postgresql":
            return _pg_ping()
    except Exception:
        return False
    return False


def _warehouse_backend() -> str:
    return _engine() if _is_connected() else "mock"


def get_default_sink_label() -> str:
    c = _warehouse_cfg()
    if c.get("display_name"):
        return str(c["display_name"])
    return {
        "doris": "Apache Doris",
        "selectdb": "SelectDB",
        "postgresql": "PostgreSQL",
        "clickhouse": "ClickHouse",
    }.get(_engine(), "OLAP 仓库")

# ── Mock 数据模型（三大域表） ──
SCHEMA = {
    "design_domain": {
        "tables": {
            "chip_designs": {"columns": ["design_id", "chip_type", "qubit_count", "topology", "freq_allocation", "status", "created_at"], "rows": 45},
            "simulation_results": {"columns": ["sim_id", "design_id", "sim_type", "freq_ghz", "q_factor", "coupling_mhz", "created_at"], "rows": 230},
            "drc_reports": {"columns": ["drc_id", "design_id", "violations", "pass", "created_at"], "rows": 89},
            "gds_exports": {"columns": ["export_id", "design_id", "filename", "size_mb", "approved", "created_at"], "rows": 32},
        },
        "description": "芯片设计域：设计方案、仿真结果、DRC 报告、GDS 导出记录",
    },
    "manufacturing_domain": {
        "tables": {
            "lots": {"columns": ["lot_id", "product", "qty", "status", "current_step", "yield_pct", "created_at"], "rows": 156},
            "work_orders": {"columns": ["wo_id", "lot_id", "step", "equipment_id", "status", "operator", "start_time", "end_time"], "rows": 720},
            "yield_records": {"columns": ["record_id", "lot_id", "step", "yield_pct", "defects", "total", "measured_at"], "rows": 1840},
            "spc_data": {"columns": ["spc_id", "parameter", "value", "ucl", "lcl", "mean", "lot_id", "measured_at"], "rows": 15600},
            "equipment_events": {"columns": ["event_id", "equipment_id", "event_type", "alarm_id", "message", "timestamp"], "rows": 4200},
        },
        "description": "芯片制造域：批次、工单、良率、SPC、设备事件",
    },
    "measurement_domain": {
        "tables": {
            "qubit_characterization": {"columns": ["char_id", "chip_id", "qubit", "freq_ghz", "T1_us", "T2_us", "anharmonicity_mhz", "measured_at"], "rows": 980},
            "calibration_records": {"columns": ["cal_id", "chip_id", "qubit", "gate", "amplitude", "drag_beta", "fidelity_pct", "calibrated_at"], "rows": 2400},
            "gate_benchmarks": {"columns": ["bench_id", "chip_id", "gate_type", "fidelity_pct", "error_rate", "method", "measured_at"], "rows": 560},
            "error_mitigation_results": {"columns": ["mit_id", "circuit", "technique", "noisy_value", "mitigated_value", "improvement_pct", "created_at"], "rows": 340},
            "raw_measurements": {"columns": ["meas_id", "experiment", "run_id", "parameter", "value", "timestamp"], "rows": 125000},
        },
        "description": "芯片测控域：比特表征、校准记录、门基准、纠错结果、原始测量",
    },
}


def list_domains() -> Dict[str, Any]:
    """列出数据中台的数据域"""
    domains = []
    for domain_key, domain in SCHEMA.items():
        total_rows = sum(t["rows"] for t in domain["tables"].values())
        domains.append({"domain": domain_key, "description": domain["description"],
                        "tables": len(domain["tables"]), "total_rows": total_rows})
    return {"domains": domains, "backend": _warehouse_backend(), "engine": _engine()}


def list_tables(domain: Optional[str] = None) -> Dict[str, Any]:
    """列出数据表"""
    tables = []
    for dk, dv in SCHEMA.items():
        if domain and dk != domain:
            continue
        for tname, tinfo in dv["tables"].items():
            tables.append({"domain": dk, "table": tname, "columns": tinfo["columns"], "rows": tinfo["rows"]})
    return {"tables": tables, "count": len(tables), "backend": _warehouse_backend(), "engine": _engine()}


def _query_sql_postgresql(sql: str) -> Dict[str, Any]:
    import psycopg
    c = _pg_cfg()
    with psycopg.connect(
        host=c["host"],
        port=c["port"],
        dbname=c["database"],
        user=c["user"],
        password=c.get("password") or "",
        connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
                return {"sql": sql, "rows": rows, "row_count": len(rows), "backend": "postgresql"}
            return {"sql": sql, "rows": [], "row_count": 0, "backend": "postgresql"}


def _query_sql_clickhouse(sql: str) -> Dict[str, Any]:
    import json as _json
    import urllib.parse
    import urllib.request
    ch = str(_warehouse_cfg().get("clickhouse_http", "http://127.0.0.1:8123")).rstrip("/")
    q = urllib.parse.urlencode({"query": sql + " FORMAT JSON"})
    url = f"{ch}/?{q}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = _json.loads(resp.read().decode())
    rows = data.get("data") or []
    return {"sql": sql, "rows": rows, "row_count": len(rows), "backend": "clickhouse"}


def query_sql(sql: str) -> Dict[str, Any]:
    """执行 SQL（Doris/SelectDB HTTP、PostgreSQL、ClickHouse 或 Mock）"""
    eng = _engine()
    if _is_connected():
        try:
            if eng in ("doris", "selectdb"):
                import json
                import urllib.request
                body = json.dumps({"stmt": sql}).encode()
                cfg = _warehouse_cfg()
                cluster = cfg.get("cluster", "default_cluster")
                database = cfg.get("database", "quantum_data")
                req = urllib.request.Request(
                    f"{_http_base()}/api/query/{cluster}/{database}",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return {"result": json.loads(resp.read().decode()), "backend": eng}
            if eng == "postgresql":
                return _query_sql_postgresql(sql)
            if eng == "clickhouse":
                return _query_sql_clickhouse(sql)
        except Exception as e:
            return {"error": str(e), "backend": eng}
    import random
    random.seed(hash(sql))
    mock_rows = [{"col1": f"val_{i}", "col2": round(random.uniform(0, 100), 2)} for i in range(min(5, 20))]
    return {
        "sql": sql,
        "rows": mock_rows,
        "row_count": len(mock_rows),
        "backend": "mock",
        "note": "Mock：请在 config 中配置 datacenter_warehouse.engine 并连通真实库",
    }


def query_qubit_characterization(chip_id: Optional[str] = None, qubit: Optional[str] = None) -> Dict[str, Any]:
    """查询比特表征数据（跨域关联：测控域）"""
    if _is_connected():
        sql = "SELECT chip_id, qubit, freq_ghz, T1_us, T2_us, anharmonicity_mhz FROM qubit_characterization"
        conditions = []
        if chip_id:
            conditions.append(f"chip_id='{chip_id}'")
        if qubit:
            conditions.append(f"qubit='{qubit}'")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY measured_at DESC LIMIT 20"
        result = query_sql(sql)
        if result and "rows" in result:
            return {"data": result["rows"], "count": len(result["rows"]), "backend": _warehouse_backend()}
    import random
    random.seed(42)
    mock = [{"chip_id": chip_id or "Chip_2026A", "qubit": f"Q{i}", "freq_ghz": round(random.uniform(4.8, 5.3), 4),
             "T1_us": round(random.uniform(30, 60), 1), "T2_us": round(random.uniform(15, 40), 1),
             "anharmonicity_mhz": round(random.uniform(-350, -280), 1)} for i in range(5)]
    if qubit:
        mock = [m for m in mock if m["qubit"] == qubit]
    return {"data": mock, "count": len(mock), "backend": "mock"}


def query_yield_trend(product: Optional[str] = None, last_n: int = 10) -> Dict[str, Any]:
    """查询良率趋势（跨域关联：制造域）"""
    import random
    random.seed(43)
    mock = [{"lot_id": f"LOT-2026-{300 - i:04d}", "product": product or "5Q-Transmon",
             "yield_pct": round(random.uniform(85, 97), 1), "defects": random.randint(0, 4)} for i in range(last_n)]
    avg = round(sum(m["yield_pct"] for m in mock) / len(mock), 1)
    return {"data": mock, "average_yield_pct": avg, "count": len(mock), "backend": "mock"}


def query_design_simulation_summary(design_id: Optional[str] = None) -> Dict[str, Any]:
    """查询设计与仿真摘要（跨域关联：设计域）"""
    import random
    random.seed(44)
    mock = [{"design_id": design_id or f"design_{i:03d}", "chip_type": "transmon", "qubit_count": 5,
             "sim_count": random.randint(3, 12), "avg_freq_ghz": round(random.uniform(4.9, 5.2), 3),
             "drc_pass": random.choice([True, True, True, False])} for i in range(3)]
    return {"data": mock, "count": len(mock), "backend": "mock"}


def cross_domain_query(query_type: str) -> Dict[str, Any]:
    """跨域关联查询：设计→制造→测控全链路追溯"""
    if query_type == "design_to_measurement":
        return {
            "query": "设计→测控追溯",
            "pipeline": "chip_designs → lots → qubit_characterization",
            "example_result": {"design_id": "design_001", "lot_id": "LOT-2026-0301", "chip_id": "Chip_2026A",
                               "Q0_freq_ghz": 5.012, "Q0_T1_us": 48.5, "yield_pct": 91.7},
            "backend": "mock",
        }
    elif query_type == "yield_vs_calibration":
        return {
            "query": "良率与校准关联",
            "pipeline": "yield_records JOIN calibration_records ON chip_id",
            "example_result": {"correlation": "高良率批次的平均校准保真度 99.2%，低良率批次 97.8%"},
            "backend": "mock",
        }
    return {"error": f"未知查询类型 {query_type}"}


# ── 流水线数据存储（内存版，生产换 Doris 表） ──
_pipeline_records: List[dict] = []
_step_records: List[dict] = []


def save_pipeline_run(pipeline_id: str, pipeline_data: dict) -> Dict[str, Any]:
    """将流水线整体信息写入数据中台"""
    record = {
        "pipeline_id": pipeline_id,
        "name": pipeline_data.get("name", ""),
        "template": pipeline_data.get("template", ""),
        "status": pipeline_data.get("status", ""),
        "total_steps": len(pipeline_data.get("steps", [])),
        "completed_steps": sum(1 for s in pipeline_data.get("steps", []) if s["status"] == "completed"),
        "failed_steps": sum(1 for s in pipeline_data.get("steps", []) if s["status"] == "failed"),
        "created_at": pipeline_data.get("created_at", ""),
        "completed_at": pipeline_data.get("completed_at", ""),
        "chip_spec": pipeline_data.get("chip_spec"),
    }
    _pipeline_records.append(record)
    SCHEMA.setdefault("pipeline_domain", {
        "tables": {
            "pipeline_runs": {"columns": ["pipeline_id", "name", "template", "status", "total_steps", "completed_steps", "failed_steps", "created_at", "completed_at"], "rows": 0},
            "pipeline_steps": {"columns": ["step_id", "pipeline_id", "stage", "agent", "title", "tool", "args_json", "result_json", "status", "started_at", "completed_at"], "rows": 0},
            "design_params": {"columns": ["pipeline_id", "qubit_id", "freq_ghz", "res_design_ghz", "res_sim_ghz", "Ec_mhz", "Lj_nH", "coupling_mhz"], "rows": 0},
            "calibration_params": {"columns": ["pipeline_id", "qubit_id", "freq_ghz", "amplitude", "drag_beta", "readout_fidelity_pct", "calibrated_at"], "rows": 0},
            "measurement_results": {"columns": ["pipeline_id", "qubit_id", "measurement_type", "value", "unit", "measured_at"], "rows": 0},
            "fabrication_records": {"columns": ["pipeline_id", "step_name", "equipment_id", "status", "defects", "timestamp"], "rows": 0},
        },
        "description": "流水线执行域：流水线运行记录、步骤详情、设计参数、校准参数、测量结果、制造记录",
    })
    SCHEMA["pipeline_domain"]["tables"]["pipeline_runs"]["rows"] = len(_pipeline_records)
    return {"saved": pipeline_id, "record_count": len(_pipeline_records), "backend": _warehouse_backend()}


def save_pipeline_steps(pipeline_id: str, steps: List[dict]) -> Dict[str, Any]:
    """将流水线所有步骤写入数据中台"""
    import json as _json
    count = 0
    for i, s in enumerate(steps):
        record = {
            "step_id": f"{pipeline_id}_S{i+1:03d}",
            "pipeline_id": pipeline_id,
            "stage": s.get("stage"),
            "agent": s.get("agent", ""),
            "title": s.get("title", ""),
            "tool": s.get("tool", ""),
            "args_json": _json.dumps(s.get("args", {}), ensure_ascii=False, default=str)[:2000],
            "result_json": _json.dumps(s.get("result", {}), ensure_ascii=False, default=str)[:4000],
            "status": s.get("status", ""),
            "started_at": s.get("started_at", ""),
            "completed_at": s.get("completed_at", ""),
        }
        _step_records.append(record)
        count += 1
    SCHEMA["pipeline_domain"]["tables"]["pipeline_steps"]["rows"] = len(_step_records)
    return {"pipeline_id": pipeline_id, "steps_saved": count, "total_step_records": len(_step_records), "backend": _warehouse_backend()}


_design_records: List[dict] = []

def save_design_params(pipeline_id: str, qubits: List[dict]) -> Dict[str, Any]:
    """将芯片设计参数写入数据中台（独立存储，不混入步骤记录）"""
    count = 0
    for q in qubits:
        record = {"pipeline_id": pipeline_id, **q}
        _design_records.append(record)
        count += 1
    SCHEMA.setdefault("pipeline_domain", {"tables": {}})
    SCHEMA["pipeline_domain"]["tables"].setdefault("design_params", {"columns": [], "rows": 0})
    SCHEMA["pipeline_domain"]["tables"]["design_params"]["rows"] = len(_design_records)
    return {"pipeline_id": pipeline_id, "design_params_saved": count}


def save_measurement_results(pipeline_id: str, measurements: List[dict]) -> Dict[str, Any]:
    """将测量结果写入数据中台"""
    count = len(measurements)
    SCHEMA["pipeline_domain"]["tables"]["measurement_results"]["rows"] += count
    return {"pipeline_id": pipeline_id, "measurements_saved": count}


def query_pipeline_history(last_n: int = 10) -> Dict[str, Any]:
    """查询历史流水线运行记录"""
    records = _pipeline_records[-last_n:]
    return {"records": records, "total": len(_pipeline_records), "backend": _warehouse_backend()}


def query_step_records(pipeline_id: Optional[str] = None, agent: Optional[str] = None,
                       tool: Optional[str] = None) -> Dict[str, Any]:
    """查询步骤记录（支持按流水线/Agent/工具筛选）"""
    filtered = _step_records
    if pipeline_id:
        filtered = [r for r in filtered if r.get("pipeline_id") == pipeline_id]
    if agent:
        filtered = [r for r in filtered if agent in r.get("agent", "")]
    if tool:
        filtered = [r for r in filtered if tool in r.get("tool", "")]
    return {"records": filtered[-50:], "total": len(filtered), "backend": _warehouse_backend()}


def export_training_dataset(domain: str = "all", format: str = "json") -> Dict[str, Any]:
    """导出 AI 训练数据集（供模型学习迭代）"""
    dataset = {
        "pipeline_runs": _pipeline_records,
        "steps": _step_records[-200:],
        "schema": {k: {"tables": list(v["tables"].keys()), "desc": v["description"]} for k, v in SCHEMA.items()},
        "stats": {
            "total_pipelines": len(_pipeline_records),
            "total_steps": len(_step_records),
            "domains": list(SCHEMA.keys()),
        },
    }
    if domain != "all":
        dataset = {k: v for k, v in dataset.items() if domain in str(k)}
    return {"dataset": dataset, "format": format, "record_count": len(_pipeline_records) + len(_step_records),
            "usage": "可用于微调 LLM、训练参数预测模型、构建经验知识库",
            "backend": _warehouse_backend()}


def get_capabilities() -> Dict[str, Any]:
    total_rows = sum(t["rows"] for d in SCHEMA.values() for t in d["tables"].values())
    eng = _engine()
    label = get_default_sink_label()
    feats = [
        "三大数据域存储（设计/制造/测控）",
        "流水线执行数据存储",
        "SQL 查询（引擎依配置）",
        "跨域关联分析",
        "AI 训练数据集导出",
    ]
    if eng in ("doris", "selectdb"):
        feats.extend(["MPP 列式 OLAP", "Doris HTTP 查询 API"])
    elif eng == "postgresql":
        feats.append("PostgreSQL 协议 / psql")
    elif eng == "clickhouse":
        feats.append("ClickHouse HTTP 接口")
    return {
        "source": label,
        "engine": eng,
        "role": "OLAP / 分析型数据仓库（数据中台核心）",
        "features": feats,
        "domains": list(SCHEMA.keys()),
        "total_tables": sum(len(d["tables"]) for d in SCHEMA.values()),
        "total_rows": total_rows,
        "connected": _is_connected(),
    }
