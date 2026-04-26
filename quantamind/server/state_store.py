import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg

from quantamind import config

_log = logging.getLogger("quantamind.state_store")
_available = True
_last_error: Optional[str] = None


def _set_available() -> None:
    global _available, _last_error
    _available = True
    _last_error = None


def _set_unavailable(exc: Exception) -> None:
    global _available, _last_error
    _available = False
    _last_error = str(exc)
    _log.warning("State store unavailable, falling back to in-memory mode: %s", exc)


def get_health() -> Dict[str, Any]:
    return {"available": _available, "last_error": _last_error}


def _enabled() -> bool:
    return _available


def _db_cfg() -> Dict[str, Any]:
    return config.get_database_config("design_postgres")


def _conn():
    cfg = _db_cfg()
    return psycopg.connect(
        host=cfg.get("host", "127.0.0.1"),
        port=cfg.get("port", 5432),
        dbname=cfg.get("database", "quantamind_design"),
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        connect_timeout=3,
    )


def ensure_schema() -> None:
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quantamind_sessions (
                        session_id text PRIMARY KEY,
                        project_id text,
                        created_at text NOT NULL,
                        deleted boolean NOT NULL DEFAULT false,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE TABLE IF NOT EXISTS quantamind_chat_messages (
                        id bigserial PRIMARY KEY,
                        session_id text NOT NULL,
                        role text NOT NULL,
                        content text NOT NULL,
                        time text NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_chat_messages_session_id
                        ON quantamind_chat_messages(session_id, id);
                    CREATE TABLE IF NOT EXISTS quantamind_tasks (
                        task_id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE TABLE IF NOT EXISTS quantamind_pipelines (
                        pipeline_id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE TABLE IF NOT EXISTS quantamind_pipeline_steps (
                        step_key text PRIMARY KEY,
                        pipeline_id text NOT NULL,
                        ordinal int NOT NULL,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_pipeline_steps_pipeline
                        ON quantamind_pipeline_steps(pipeline_id, ordinal);
                    CREATE TABLE IF NOT EXISTS quantamind_pulse_calibration_latest (
                        calibration_key text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE TABLE IF NOT EXISTS quantamind_pulse_calibration_history (
                        id bigserial PRIMARY KEY,
                        calibration_key text NOT NULL,
                        payload jsonb NOT NULL,
                        recorded_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_pulse_calibration_history_key
                        ON quantamind_pulse_calibration_history(calibration_key, recorded_at DESC);
                    CREATE TABLE IF NOT EXISTS quantamind_discoveries (
                        discovery_id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_discoveries_updated_at
                        ON quantamind_discoveries(updated_at DESC);
                    CREATE TABLE IF NOT EXISTS quantamind_discovery_events (
                        id bigserial PRIMARY KEY,
                        discovery_id text NOT NULL,
                        event_type text NOT NULL,
                        payload jsonb NOT NULL,
                        created_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_discovery_events_discovery
                        ON quantamind_discovery_events(discovery_id, created_at DESC);
                    CREATE TABLE IF NOT EXISTS quantamind_library_ingest_jobs (
                        job_id text PRIMARY KEY,
                        file_id text NOT NULL,
                        filename text NOT NULL,
                        project_id text,
                        status text NOT NULL,
                        stage text NOT NULL,
                        attempts int NOT NULL DEFAULT 0,
                        error_message text,
                        payload jsonb,
                        created_at timestamptz NOT NULL DEFAULT now(),
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_library_ingest_jobs_file
                        ON quantamind_library_ingest_jobs(file_id, updated_at DESC);
                    CREATE TABLE IF NOT EXISTS quantamind_intel_papers (
                        paper_id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_intel_papers_updated_at
                        ON quantamind_intel_papers(updated_at DESC);
                    CREATE TABLE IF NOT EXISTS quantamind_intel_reports (
                        report_id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_quantamind_intel_reports_updated_at
                        ON quantamind_intel_reports(updated_at DESC);
                    """
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def load_sessions() -> Dict[str, dict]:
    if not _enabled():
        return {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT session_id, project_id, created_at FROM quantamind_sessions WHERE deleted = false ORDER BY created_at"
                )
                rows = cur.fetchall()
        _set_available()
        return {sid: {"project_id": project_id, "created_at": created_at} for sid, project_id, created_at in rows}
    except Exception as e:
        _set_unavailable(e)
        return {}


def upsert_session(session_id: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_sessions (session_id, project_id, created_at, deleted, updated_at)
                    VALUES (%s, %s, %s, false, now())
                    ON CONFLICT (session_id) DO UPDATE SET
                        project_id = EXCLUDED.project_id,
                        created_at = EXCLUDED.created_at,
                        deleted = false,
                        updated_at = now()
                    """,
                    (session_id, payload.get("project_id"), payload.get("created_at")),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def delete_session(session_id: str) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE quantamind_sessions SET deleted = true, updated_at = now() WHERE session_id = %s", (session_id,))
                cur.execute("DELETE FROM quantamind_chat_messages WHERE session_id = %s", (session_id,))
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def load_chat_histories() -> Dict[str, List[dict]]:
    if not _enabled():
        return {}
    histories: Dict[str, List[dict]] = {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT session_id, role, content, time FROM quantamind_chat_messages ORDER BY session_id, id"
                )
                for session_id, role, content, time in cur.fetchall():
                    histories.setdefault(session_id, []).append({"role": role, "content": content, "time": time})
        _set_available()
        return histories
    except Exception as e:
        _set_unavailable(e)
        return {}


def append_chat_message(session_id: str, message: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_chat_messages (session_id, role, content, time)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, message.get("role", ""), message.get("content", ""), message.get("time", "")),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def load_tasks() -> Dict[str, dict]:
    if not _enabled():
        return {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT task_id, payload FROM quantamind_tasks")
                rows = cur.fetchall()
        _set_available()
        return {task_id: payload for task_id, payload in rows}
    except Exception as e:
        _set_unavailable(e)
        return {}


def upsert_task(task_id: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_tasks (task_id, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (task_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (task_id, json.dumps(payload, ensure_ascii=False, default=str)),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def load_pipelines() -> Dict[str, dict]:
    if not _enabled():
        return {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pipeline_id, payload FROM quantamind_pipelines")
                rows = cur.fetchall()
        _set_available()
        return {pipeline_id: payload for pipeline_id, payload in rows}
    except Exception as e:
        _set_unavailable(e)
        return {}


def get_pipeline_history(limit: int = 50) -> List[dict]:
    if not _enabled():
        return []
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pipeline_id, payload, updated_at
                    FROM quantamind_pipelines
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        out = []
        for pipeline_id, payload, updated_at in rows:
            row = dict(payload)
            row["pipeline_id"] = row.get("pipeline_id", pipeline_id)
            row["updated_at"] = str(updated_at)
            out.append(row)
        _set_available()
        return out
    except Exception as e:
        _set_unavailable(e)
        return []


def _step_key(pipeline_id: str, ordinal: int, step: dict) -> str:
    return f"{pipeline_id}:{ordinal}:{step.get('stage','')}:{step.get('title','')}:{step.get('started_at','')}"


def get_pipeline_steps(limit: int = 100, pipeline_id: Optional[str] = None,
                       agent: Optional[str] = None, tool: Optional[str] = None) -> List[dict]:
    if not _enabled():
        return []
    try:
        sql = """
            SELECT step_key, pipeline_id, ordinal, payload, updated_at
            FROM quantamind_pipeline_steps
        """
        conditions = []
        params: List[Any] = []
        if pipeline_id:
            conditions.append("pipeline_id = %s")
            params.append(pipeline_id)
        if agent:
            conditions.append("payload ->> 'agent' ILIKE %s")
            params.append(f"%{agent}%")
        if tool:
            conditions.append("payload ->> 'tool' ILIKE %s")
            params.append(f"%{tool}%")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY updated_at DESC, ordinal DESC LIMIT %s"
        params.append(limit)
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        out = []
        for step_key, pipeline_id_val, ordinal, payload, updated_at in rows:
            row = dict(payload)
            row["step_key"] = step_key
            row["pipeline_id"] = pipeline_id_val
            row["ordinal"] = ordinal
            row["updated_at"] = str(updated_at)
            out.append(row)
        _set_available()
        return out
    except Exception as e:
        _set_unavailable(e)
        return []


def upsert_pipeline(pipeline_id: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_pipelines (pipeline_id, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (pipeline_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (pipeline_id, json.dumps(payload, ensure_ascii=False, default=str)),
                )
                cur.execute("DELETE FROM quantamind_pipeline_steps WHERE pipeline_id = %s", (pipeline_id,))
                for ordinal, step in enumerate(payload.get("steps", []), start=1):
                    cur.execute(
                        """
                        INSERT INTO quantamind_pipeline_steps (step_key, pipeline_id, ordinal, payload, updated_at)
                        VALUES (%s, %s, %s, %s::jsonb, now())
                        ON CONFLICT (step_key) DO UPDATE SET
                            payload = EXCLUDED.payload,
                            updated_at = now()
                        """,
                        (
                            _step_key(pipeline_id, ordinal, step),
                            pipeline_id,
                            ordinal,
                            json.dumps(step, ensure_ascii=False, default=str),
                        ),
                    )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def load_pulse_calibration_latest() -> Dict[str, dict]:
    if not _enabled():
        return {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT calibration_key, payload FROM quantamind_pulse_calibration_latest")
                rows = cur.fetchall()
        _set_available()
        return {key: payload for key, payload in rows}
    except Exception as e:
        _set_unavailable(e)
        return {}


def record_pulse_calibration(calibration_key: str, payload: dict) -> None:
    if not _enabled():
        return
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_pulse_calibration_latest (calibration_key, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (calibration_key) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (calibration_key, payload_json),
                )
                cur.execute(
                    """
                    INSERT INTO quantamind_pulse_calibration_history (calibration_key, payload, recorded_at)
                    VALUES (%s, %s::jsonb, now())
                    """,
                    (calibration_key, payload_json),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def get_pulse_calibration_history(limit: int = 200) -> List[dict]:
    if not _enabled():
        return []
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT calibration_key, payload, recorded_at
                    FROM quantamind_pulse_calibration_history
                    ORDER BY recorded_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        _set_available()
        return [{"calibration_key": key, "payload": payload, "recorded_at": str(recorded_at)} for key, payload, recorded_at in rows]
    except Exception as e:
        _set_unavailable(e)
        return []


def load_discoveries() -> List[dict]:
    if not _enabled():
        return []
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT discovery_id, payload
                    FROM quantamind_discoveries
                    ORDER BY updated_at DESC
                    """
                )
                rows = cur.fetchall()
        items = []
        for discovery_id, payload in rows:
            item = dict(payload)
            item["id"] = item.get("id", discovery_id)
            items.append(item)
        _set_available()
        return items
    except Exception as e:
        _set_unavailable(e)
        return []


def upsert_discovery(discovery_id: str, payload: dict) -> None:
    if not _enabled():
        return
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_discoveries (discovery_id, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (discovery_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (discovery_id, payload_json),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def delete_discovery(discovery_id: str) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM quantamind_discoveries WHERE discovery_id = %s", (discovery_id,))
                cur.execute("DELETE FROM quantamind_discovery_events WHERE discovery_id = %s", (discovery_id,))
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def append_discovery_event(discovery_id: str, event_type: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_discovery_events (discovery_id, event_type, payload, created_at)
                    VALUES (%s, %s, %s::jsonb, now())
                    """,
                    (discovery_id, event_type, json.dumps(payload, ensure_ascii=False, default=str)),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def list_discovery_events(discovery_id: str, limit: int = 50) -> List[dict]:
    if not _enabled():
        return []
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_type, payload, created_at
                    FROM quantamind_discovery_events
                    WHERE discovery_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (discovery_id, limit),
                )
                rows = cur.fetchall()
        _set_available()
        return [
            {
                "event_type": event_type,
                "payload": payload,
                "created_at": str(created_at),
            }
            for event_type, payload, created_at in rows
        ]
    except Exception as e:
        _set_unavailable(e)
        return []


def discovery_counts() -> Dict[str, Any]:
    items = load_discoveries()
    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    unhandled = 0
    repeated = 0
    for item in items:
        cat = item.get("category", "其他")
        by_category[cat] = by_category.get(cat, 0) + 1
        sev = item.get("severity", "info")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        if not item.get("handled", False):
            unhandled += 1
        if int(item.get("occurrence_count", 1) or 1) > 1:
            repeated += 1
    return {
        "total": len(items),
        "unhandled": unhandled,
        "repeated": repeated,
        "by_category": by_category,
        "by_severity": by_severity,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def upsert_library_ingest_job(job_id: str, file_id: str, filename: str, project_id: str,
                              status: str, stage: str, attempts: int = 0,
                              error_message: Optional[str] = None,
                              payload: Optional[dict] = None) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_library_ingest_jobs
                    (job_id, file_id, filename, project_id, status, stage, attempts, error_message, payload, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (job_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        stage = EXCLUDED.stage,
                        attempts = EXCLUDED.attempts,
                        error_message = EXCLUDED.error_message,
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (
                        job_id, file_id, filename, project_id, status, stage, attempts,
                        error_message, json.dumps(payload or {}, ensure_ascii=False, default=str),
                    ),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def list_library_ingest_jobs(limit: int = 50, status: Optional[str] = None) -> List[dict]:
    if not _enabled():
        return []
    try:
        sql = """
            SELECT job_id, file_id, filename, project_id, status, stage, attempts, error_message, payload, created_at, updated_at
            FROM quantamind_library_ingest_jobs
        """
        params: List[Any] = []
        if status:
            sql += " WHERE status = %s"
            params.append(status)
        sql += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        _set_available()
        return [
            {
                "job_id": job_id,
                "file_id": file_id,
                "filename": filename,
                "project_id": project_id,
                "status": st,
                "stage": stage,
                "attempts": attempts,
                "error_message": error_message,
                "payload": payload,
                "created_at": str(created_at),
                "updated_at": str(updated_at),
            }
            for job_id, file_id, filename, project_id, st, stage, attempts, error_message, payload, created_at, updated_at in rows
        ]
    except Exception as e:
        _set_unavailable(e)
        return []


def get_library_ingest_job(file_id: Optional[str] = None, job_id: Optional[str] = None) -> Optional[dict]:
    if not _enabled():
        return None
    if not file_id and not job_id:
        return None
    try:
        sql = """
            SELECT job_id, file_id, filename, project_id, status, stage, attempts, error_message, payload, created_at, updated_at
            FROM quantamind_library_ingest_jobs
        """
        params: List[Any] = []
        conditions = []
        if job_id:
            conditions.append("job_id = %s")
            params.append(job_id)
        if file_id:
            conditions.append("file_id = %s")
            params.append(file_id)
        sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY updated_at DESC LIMIT 1"
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
        _set_available()
        if not row:
            return None
        return {
            "job_id": row[0],
            "file_id": row[1],
            "filename": row[2],
            "project_id": row[3],
            "status": row[4],
            "stage": row[5],
            "attempts": row[6],
            "error_message": row[7],
            "payload": row[8],
            "created_at": str(row[9]),
            "updated_at": str(row[10]),
        }
    except Exception as e:
        _set_unavailable(e)
        return None


def get_latest_library_ingest_jobs(file_ids: List[str]) -> Dict[str, dict]:
    if not _enabled():
        return {}
    ids = [str(file_id) for file_id in file_ids if file_id]
    if not ids:
        return {}
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (file_id)
                        job_id, file_id, filename, project_id, status, stage, attempts, error_message, payload, created_at, updated_at
                    FROM quantamind_library_ingest_jobs
                    WHERE file_id = ANY(%s)
                    ORDER BY file_id, updated_at DESC
                    """,
                    (ids,),
                )
                rows = cur.fetchall()
        _set_available()
        return {
            row[1]: {
                "job_id": row[0],
                "file_id": row[1],
                "filename": row[2],
                "project_id": row[3],
                "status": row[4],
                "stage": row[5],
                "attempts": row[6],
                "error_message": row[7],
                "payload": row[8],
                "created_at": str(row[9]),
                "updated_at": str(row[10]),
            }
            for row in rows
        }
    except Exception as e:
        _set_unavailable(e)
        return {}


def upsert_intel_paper(paper_id: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_intel_papers (paper_id, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (paper_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (paper_id, json.dumps(payload, ensure_ascii=False, default=str)),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def get_intel_paper(paper_id: str) -> Optional[dict]:
    if not _enabled():
        return None
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT payload
                    FROM quantamind_intel_papers
                    WHERE paper_id = %s
                    LIMIT 1
                    """,
                    (paper_id,),
                )
                row = cur.fetchone()
        _set_available()
        return row[0] if row else None
    except Exception as e:
        _set_unavailable(e)
        return None


def list_intel_papers(limit: int = 50, topic: Optional[str] = None) -> List[dict]:
    if not _enabled():
        return []
    try:
        sql = """
            SELECT payload
            FROM quantamind_intel_papers
        """
        params: List[Any] = []
        if topic:
            sql += " WHERE payload->'matched_topics' ? %s"
            params.append(topic)
        sql += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        _set_available()
        return [row[0] for row in rows]
    except Exception as e:
        _set_unavailable(e)
        return []


def upsert_intel_report(report_id: str, payload: dict) -> None:
    if not _enabled():
        return
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quantamind_intel_reports (report_id, payload, updated_at)
                    VALUES (%s, %s::jsonb, now())
                    ON CONFLICT (report_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = now()
                    """,
                    (report_id, json.dumps(payload, ensure_ascii=False, default=str)),
                )
            conn.commit()
        _set_available()
    except Exception as e:
        _set_unavailable(e)


def get_intel_report(report_id: str) -> Optional[dict]:
    if not _enabled():
        return None
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT payload
                    FROM quantamind_intel_reports
                    WHERE report_id = %s
                    LIMIT 1
                    """,
                    (report_id,),
                )
                row = cur.fetchone()
        _set_available()
        return row[0] if row else None
    except Exception as e:
        _set_unavailable(e)
        return None


def list_intel_reports(limit: int = 20) -> List[dict]:
    if not _enabled():
        return []
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT payload
                    FROM quantamind_intel_reports
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        _set_available()
        return [row[0] for row in rows]
    except Exception as e:
        _set_unavailable(e)
        return []
