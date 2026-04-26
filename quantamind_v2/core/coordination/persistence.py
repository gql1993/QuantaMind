from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantamind_v2.contracts.run import utc_now_iso
from quantamind_v2.core.coordination.audit import CoordinationAuditEvent


def _normalize_profile_id(profile_id: str | None) -> str | None:
    if profile_id is None:
        return None
    normalized = str(profile_id).strip()
    return normalized or None


def _profile_rollout_bucket(profile_id: str) -> int:
    digest = hashlib.sha256(profile_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _new_read_observability_state() -> dict[str, Any]:
    return {
        "total_reads": 0,
        "sqlite_reads": 0,
        "file_reads": 0,
        "fallback_anomaly_count": 0,
        "allowlist_hits": 0,
        "rollout_hits": 0,
        "global_preferred_hits": 0,
        "rollout_excluded_reads": 0,
        "not_selected_reads": 0,
        "profile_required_reads": 0,
        "profiles": {},
    }


def _update_read_observability_state(
    state: dict[str, Any],
    *,
    profile_id: str | None,
    source: str,
    routing_reason: str,
    fallback_used: bool,
) -> None:
    state["total_reads"] = int(state.get("total_reads", 0)) + 1
    if source == "secondary_sqlite":
        state["sqlite_reads"] = int(state.get("sqlite_reads", 0)) + 1
    else:
        state["file_reads"] = int(state.get("file_reads", 0)) + 1
    if fallback_used:
        state["fallback_anomaly_count"] = int(state.get("fallback_anomaly_count", 0)) + 1
    if routing_reason == "allowlist":
        state["allowlist_hits"] = int(state.get("allowlist_hits", 0)) + 1
    elif routing_reason == "rollout_percentage":
        state["rollout_hits"] = int(state.get("rollout_hits", 0)) + 1
    elif routing_reason == "global_preferred":
        state["global_preferred_hits"] = int(state.get("global_preferred_hits", 0)) + 1
    elif routing_reason == "rollout_excluded":
        state["rollout_excluded_reads"] = int(state.get("rollout_excluded_reads", 0)) + 1
    elif routing_reason == "profile_required":
        state["profile_required_reads"] = int(state.get("profile_required_reads", 0)) + 1
    elif routing_reason == "not_selected":
        state["not_selected_reads"] = int(state.get("not_selected_reads", 0)) + 1
    normalized_profile_id = _normalize_profile_id(profile_id)
    if normalized_profile_id is None:
        return
    profiles = state.setdefault("profiles", {})
    profile_state = profiles.setdefault(
        normalized_profile_id,
        {
            "profile_id": normalized_profile_id,
            "reads": 0,
            "sqlite_reads": 0,
            "file_reads": 0,
            "fallback_anomaly_count": 0,
            "last_source": None,
            "last_routing_reason": None,
        },
    )
    profile_state["reads"] = int(profile_state.get("reads", 0)) + 1
    if source == "secondary_sqlite":
        profile_state["sqlite_reads"] = int(profile_state.get("sqlite_reads", 0)) + 1
    else:
        profile_state["file_reads"] = int(profile_state.get("file_reads", 0)) + 1
    if fallback_used:
        profile_state["fallback_anomaly_count"] = int(profile_state.get("fallback_anomaly_count", 0)) + 1
    profile_state["last_source"] = source
    profile_state["last_routing_reason"] = routing_reason


def _build_read_observability_report(state: dict[str, Any], *, profile_limit: int = 20) -> dict[str, Any]:
    total_reads = int(state.get("total_reads", 0))
    sqlite_reads = int(state.get("sqlite_reads", 0))
    file_reads = int(state.get("file_reads", 0))
    allowlist_hits = int(state.get("allowlist_hits", 0))
    rollout_hits = int(state.get("rollout_hits", 0))
    global_preferred_hits = int(state.get("global_preferred_hits", 0))
    fallback_anomaly_count = int(state.get("fallback_anomaly_count", 0))
    gray_selected_reads = allowlist_hits + rollout_hits
    profile_rows = list((state.get("profiles") or {}).values())
    profile_rows = sorted(
        profile_rows,
        key=lambda item: (-int(item.get("reads", 0)), str(item.get("profile_id", ""))),
    )[: max(int(profile_limit), 1)]
    return {
        "total_reads": total_reads,
        "sqlite_reads": sqlite_reads,
        "file_reads": file_reads,
        "database_coverage_ratio": round((sqlite_reads / total_reads), 4) if total_reads else 0.0,
        "gray_selected_reads": gray_selected_reads,
        "gray_coverage_ratio": round((gray_selected_reads / total_reads), 4) if total_reads else 0.0,
        "allowlist_hits": allowlist_hits,
        "rollout_hits": rollout_hits,
        "global_preferred_hits": global_preferred_hits,
        "rollout_excluded_reads": int(state.get("rollout_excluded_reads", 0)),
        "not_selected_reads": int(state.get("not_selected_reads", 0)),
        "profile_required_reads": int(state.get("profile_required_reads", 0)),
        "fallback_anomaly_count": fallback_anomaly_count,
        "tracked_profiles_total": len(state.get("profiles") or {}),
        "profile_hits": profile_rows,
    }


class FileBackedCoordinationAuditStore:
    """File-backed audit store with cross-process read visibility."""

    def __init__(
        self,
        file_path: Path,
        *,
        max_items: int = 2000,
        rotate_max_bytes: int = 1_000_000,
        rotate_interval_seconds: int = 86_400,
        archive_index_path: Path | None = None,
    ) -> None:
        self._path = file_path
        self._max_items = max(int(max_items), 100)
        self._rotate_max_bytes = max(int(rotate_max_bytes), 1)
        self._rotate_interval_seconds = max(int(rotate_interval_seconds), 1)
        self._archive_index_path = archive_index_path or self._path.with_name("coordination_audit_archives.json")
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")
        if not self._archive_index_path.exists():
            self._write_archive_index([])
        self._last_rotation_epoch = datetime.now(timezone.utc).timestamp()
        self._health: dict[str, Any] = {
            "file_path": str(self._path),
            "status": "ok",
            "max_items": self._max_items,
            "rotate_max_bytes": self._rotate_max_bytes,
            "rotate_interval_seconds": self._rotate_interval_seconds,
            "archive_index_path": str(self._archive_index_path),
            "retained_events": 0,
            "invalid_lines_detected": 0,
            "last_compacted_at": None,
            "last_backup_file": None,
            "last_rotated_at": None,
            "last_rotation_reason": None,
            "last_archive_file": None,
            "startup_checked_at": utc_now_iso(),
        }
        self._startup_recover()

    def append(
        self,
        *,
        event_type: str,
        profile_id: str,
        strategy: str,
        outcome: str,
        reason: str,
        run_id: str | None = None,
        conflict_run_id: str | None = None,
        route_mode: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CoordinationAuditEvent:
        event = CoordinationAuditEvent(
            event_id=f"caev-{uuid4().hex[:16]}",
            event_type=event_type,
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            reason=reason,
            run_id=run_id,
            conflict_run_id=conflict_run_id,
            route_mode=route_mode,
            payload=dict(payload or {}),
            created_at=utc_now_iso(),
        )
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), ensure_ascii=True) + "\n")
            self._compact_if_needed(trigger="append")
            self._rotate_if_needed(trigger="append")
        return event

    def list_events(
        self,
        *,
        profile_id: str | None = None,
        strategy: str | None = None,
        outcome: str | None = None,
        event_type: str | None = None,
        limit: int = 200,
    ) -> list[CoordinationAuditEvent]:
        items = self._read_all()
        if profile_id:
            items = [item for item in items if item.profile_id == profile_id]
        if strategy:
            items = [item for item in items if item.strategy == strategy]
        if outcome:
            items = [item for item in items if item.outcome == outcome]
        if event_type:
            items = [item for item in items if item.event_type == event_type]
        items = sorted(items, key=lambda item: item.created_at, reverse=True)
        return items[: max(int(limit), 1)]

    def _read_all(self) -> list[CoordinationAuditEvent]:
        if not self._path.exists():
            return []
        rows: list[CoordinationAuditEvent] = []
        invalid_lines = 0
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    invalid_lines += 1
                    continue
                if not isinstance(payload, dict):
                    invalid_lines += 1
                    continue
                try:
                    rows.append(
                        CoordinationAuditEvent(
                            event_id=str(payload.get("event_id", "")),
                            event_type=str(payload.get("event_type", "")),
                            profile_id=str(payload.get("profile_id", "")),
                            strategy=str(payload.get("strategy", "")),
                            outcome=str(payload.get("outcome", "")),
                            reason=str(payload.get("reason", "")),
                            run_id=str(payload["run_id"]) if payload.get("run_id") is not None else None,
                            conflict_run_id=(
                                str(payload["conflict_run_id"]) if payload.get("conflict_run_id") is not None else None
                            ),
                            route_mode=str(payload["route_mode"]) if payload.get("route_mode") is not None else None,
                            payload=dict(payload.get("payload") or {}),
                            created_at=str(payload.get("created_at", utc_now_iso())),
                        )
                    )
                except Exception:  # noqa: BLE001
                    invalid_lines += 1
                    continue
        trimmed = rows[-self._max_items :]
        self._health["retained_events"] = len(trimmed)
        self._health["invalid_lines_detected"] = invalid_lines
        if invalid_lines > 0:
            self._health["status"] = "warn"
        return trimmed

    def get_health_report(self) -> dict[str, Any]:
        report = dict(self._health)
        report["current_size_bytes"] = self._path.stat().st_size if self._path.exists() else 0
        return report

    def list_archives(self, *, limit: int = 100) -> list[dict[str, Any]]:
        items = self._read_archive_index()
        items = sorted(items, key=lambda item: str(item.get("rotated_at", "")), reverse=True)
        return items[: max(int(limit), 1)]

    def _startup_recover(self) -> None:
        with self._lock:
            self._compact_if_needed(trigger="startup")
            self._rotate_if_needed(trigger="startup")

    def _compact_if_needed(self, *, trigger: str) -> None:
        valid_events, invalid_lines = self._read_raw_events()
        needs_compact = invalid_lines > 0 or len(valid_events) > self._max_items
        retained = valid_events[-self._max_items :]
        self._health["retained_events"] = len(retained)
        self._health["invalid_lines_detected"] = invalid_lines
        if not needs_compact:
            self._health["status"] = "ok"
            return
        backup = self._create_backup_file()
        self._rewrite_events(retained)
        self._health["status"] = "recovered"
        self._health["last_compacted_at"] = utc_now_iso()
        self._health["last_backup_file"] = str(backup)
        self._health["last_compact_trigger"] = trigger
        self._health["invalid_lines_detected"] = 0

    def _rotate_if_needed(self, *, trigger: str) -> None:
        if not self._path.exists():
            return
        current_size = self._path.stat().st_size
        now_epoch = datetime.now(timezone.utc).timestamp()
        due_by_size = current_size >= self._rotate_max_bytes
        due_by_time = (now_epoch - self._last_rotation_epoch) >= self._rotate_interval_seconds
        if not due_by_size and not due_by_time:
            return
        raw = self._path.read_text(encoding="utf-8")
        if not raw.strip():
            self._last_rotation_epoch = now_epoch
            return
        reason = "size" if due_by_size else "time"
        stamp = utc_now_iso().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "Z")
        archive_file = self._path.with_name(f"{self._path.stem}.{stamp}.archive{self._path.suffix}")
        archive_file.write_text(raw, encoding="utf-8")
        event_lines = len([line for line in raw.splitlines() if line.strip()])
        self._path.write_text("", encoding="utf-8")
        self._append_archive_index(
            {
                "archive_file": str(archive_file),
                "rotated_at": utc_now_iso(),
                "reason": reason,
                "trigger": trigger,
                "size_bytes": len(raw.encode("utf-8")),
                "event_lines": event_lines,
            }
        )
        self._last_rotation_epoch = now_epoch
        self._health["last_rotated_at"] = utc_now_iso()
        self._health["last_rotation_reason"] = reason
        self._health["last_archive_file"] = str(archive_file)

    def _read_raw_events(self) -> tuple[list[CoordinationAuditEvent], int]:
        rows: list[CoordinationAuditEvent] = []
        invalid_lines = 0
        if not self._path.exists():
            return rows, invalid_lines
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    invalid_lines += 1
                    continue
                parsed = self._event_from_dict(payload)
                if parsed is None:
                    invalid_lines += 1
                    continue
                rows.append(parsed)
        return rows, invalid_lines

    def _event_from_dict(self, payload: Any) -> CoordinationAuditEvent | None:
        if not isinstance(payload, dict):
            return None
        try:
            return CoordinationAuditEvent(
                event_id=str(payload.get("event_id", "")),
                event_type=str(payload.get("event_type", "")),
                profile_id=str(payload.get("profile_id", "")),
                strategy=str(payload.get("strategy", "")),
                outcome=str(payload.get("outcome", "")),
                reason=str(payload.get("reason", "")),
                run_id=str(payload["run_id"]) if payload.get("run_id") is not None else None,
                conflict_run_id=str(payload["conflict_run_id"]) if payload.get("conflict_run_id") is not None else None,
                route_mode=str(payload["route_mode"]) if payload.get("route_mode") is not None else None,
                payload=dict(payload.get("payload") or {}),
                created_at=str(payload.get("created_at", utc_now_iso())),
            )
        except Exception:  # noqa: BLE001
            return None

    def _create_backup_file(self) -> Path:
        stamp = utc_now_iso().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "Z")
        backup = self._path.with_suffix(self._path.suffix + f".{stamp}.bak")
        backup.write_text(self._path.read_text(encoding="utf-8"), encoding="utf-8")
        return backup

    def _rewrite_events(self, events: list[CoordinationAuditEvent]) -> None:
        temp = self._path.with_suffix(self._path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as fh:
            for item in events:
                fh.write(json.dumps(item.to_dict(), ensure_ascii=True) + "\n")
        temp.replace(self._path)

    def _read_archive_index(self) -> list[dict[str, Any]]:
        if not self._archive_index_path.exists():
            return []
        try:
            payload = json.loads(self._archive_index_path.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        normalized: list[dict[str, Any]] = []
        for row in payload:
            if isinstance(row, dict):
                normalized.append(dict(row))
        return normalized

    def _append_archive_index(self, record: dict[str, Any]) -> None:
        rows = self._read_archive_index()
        rows.append(dict(record))
        self._write_archive_index(rows)

    def _write_archive_index(self, rows: list[dict[str, Any]]) -> None:
        temp = self._archive_index_path.with_suffix(self._archive_index_path.suffix + ".tmp")
        temp.write_text(json.dumps(rows, ensure_ascii=True, indent=2), encoding="utf-8")
        temp.replace(self._archive_index_path)


class FileBackedCoordinationPolicyStore:
    """File-backed profile policy overrides."""

    def __init__(self, file_path: Path) -> None:
        self._path = file_path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_map({})
        self._health: dict[str, Any] = {
            "file_path": str(self._path),
            "status": "ok",
            "profiles_count": 0,
            "startup_checked_at": utc_now_iso(),
            "last_recovered_at": None,
            "last_backup_file": None,
        }
        self._startup_recover()

    def get_strategy(self, profile_id: str) -> str | None:
        data = self._read_map()
        item = data.get(profile_id)
        if not isinstance(item, dict):
            return None
        strategy = item.get("strategy")
        return str(strategy) if strategy else None

    def set_strategy(self, *, profile_id: str, strategy: str, source: str = "manual") -> dict[str, str]:
        key = profile_id.strip() or "default"
        with self._lock:
            data = self._read_map()
            data[key] = {
                "profile_id": key,
                "strategy": strategy,
                "source": source,
                "updated_at": utc_now_iso(),
            }
            self._write_map(data)
        return dict(data[key])

    def list_policies(self, *, limit: int = 500) -> list[dict[str, str]]:
        data = self._read_map()
        items: list[dict[str, str]] = []
        for item in data.values():
            if isinstance(item, dict):
                items.append(
                    {
                        "profile_id": str(item.get("profile_id", "")),
                        "strategy": str(item.get("strategy", "")),
                        "source": str(item.get("source", "")),
                        "updated_at": str(item.get("updated_at", "")),
                    }
                )
        items = sorted(items, key=lambda row: row.get("updated_at", ""), reverse=True)
        return items[: max(int(limit), 1)]

    def _read_map(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        self._health["profiles_count"] = len(payload)
        return payload

    def _write_map(self, payload: dict[str, Any]) -> None:
        temp = self._path.with_suffix(self._path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        temp.replace(self._path)

    def get_health_report(self) -> dict[str, Any]:
        report = dict(self._health)
        report["current_size_bytes"] = self._path.stat().st_size if self._path.exists() else 0
        return report

    def _startup_recover(self) -> None:
        with self._lock:
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8") or "{}")
            except json.JSONDecodeError:
                backup = self._create_backup_file()
                self._write_map({})
                self._health["status"] = "recovered"
                self._health["last_recovered_at"] = utc_now_iso()
                self._health["last_backup_file"] = str(backup)
                self._health["profiles_count"] = 0
                return
            if not isinstance(payload, dict):
                backup = self._create_backup_file()
                self._write_map({})
                self._health["status"] = "recovered"
                self._health["last_recovered_at"] = utc_now_iso()
                self._health["last_backup_file"] = str(backup)
                self._health["profiles_count"] = 0
                return
            self._health["status"] = "ok"
            self._health["profiles_count"] = len(payload)

    def _create_backup_file(self) -> Path:
        stamp = utc_now_iso().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "Z")
        backup = self._path.with_suffix(self._path.suffix + f".{stamp}.bak")
        backup.write_text(self._path.read_text(encoding="utf-8"), encoding="utf-8")
        return backup


class SQLiteCoordinationAuditStore:
    """SQLite-backed audit store for dual-write baseline."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def append(
        self,
        *,
        event_type: str,
        profile_id: str,
        strategy: str,
        outcome: str,
        reason: str,
        run_id: str | None = None,
        conflict_run_id: str | None = None,
        route_mode: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CoordinationAuditEvent:
        event = CoordinationAuditEvent(
            event_id=f"caev-{uuid4().hex[:16]}",
            event_type=event_type,
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            reason=reason,
            run_id=run_id,
            conflict_run_id=conflict_run_id,
            route_mode=route_mode,
            payload=dict(payload or {}),
            created_at=utc_now_iso(),
        )
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coordination_audit_events(
                    event_id,event_type,profile_id,strategy,outcome,reason,
                    run_id,conflict_run_id,route_mode,payload_json,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.profile_id,
                    event.strategy,
                    event.outcome,
                    event.reason,
                    event.run_id,
                    event.conflict_run_id,
                    event.route_mode,
                    json.dumps(event.payload, ensure_ascii=True),
                    event.created_at,
                ),
            )
            conn.commit()
        return event

    def list_events(
        self,
        *,
        profile_id: str | None = None,
        strategy: str | None = None,
        outcome: str | None = None,
        event_type: str | None = None,
        limit: int = 200,
    ) -> list[CoordinationAuditEvent]:
        conditions: list[str] = []
        args: list[Any] = []
        if profile_id:
            conditions.append("profile_id = ?")
            args.append(profile_id)
        if strategy:
            conditions.append("strategy = ?")
            args.append(strategy)
        if outcome:
            conditions.append("outcome = ?")
            args.append(outcome)
        if event_type:
            conditions.append("event_type = ?")
            args.append(event_type)
        sql = "SELECT * FROM coordination_audit_events"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(max(int(limit), 1))
        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._event_from_row(row) for row in rows]

    def get_health_report(self) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(1) FROM coordination_audit_events").fetchone()[0]
        return {
            "file_path": str(self._db_path),
            "status": "ok",
            "backend": "sqlite",
            "total_rows": int(total),
            "current_size_bytes": self._db_path.stat().st_size if self._db_path.exists() else 0,
        }

    def list_archives(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return []

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coordination_audit_events(
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    run_id TEXT,
                    conflict_run_id TEXT,
                    route_mode TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_coord_audit_profile_created ON coordination_audit_events(profile_id, created_at)"
            )
            conn.commit()

    def _event_from_row(self, row: sqlite3.Row | tuple) -> CoordinationAuditEvent:
        # sqlite returns tuple by default in this module.
        payload_raw = row[9] if len(row) > 9 else "{}"
        try:
            payload = json.loads(payload_raw or "{}")
        except json.JSONDecodeError:
            payload = {}
        return CoordinationAuditEvent(
            event_id=str(row[0]),
            event_type=str(row[1]),
            profile_id=str(row[2]),
            strategy=str(row[3]),
            outcome=str(row[4]),
            reason=str(row[5]),
            run_id=str(row[6]) if row[6] is not None else None,
            conflict_run_id=str(row[7]) if row[7] is not None else None,
            route_mode=str(row[8]) if row[8] is not None else None,
            payload=dict(payload or {}),
            created_at=str(row[10]) if len(row) > 10 else utc_now_iso(),
        )


class SQLiteCoordinationPolicyStore:
    """SQLite-backed policy store for dual-write baseline."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_strategy(self, profile_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT strategy FROM coordination_conflict_policies WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()
        if row is None:
            return None
        return str(row[0])

    def set_strategy(self, *, profile_id: str, strategy: str, source: str = "manual") -> dict[str, str]:
        key = profile_id.strip() or "default"
        record = {
            "profile_id": key,
            "strategy": strategy,
            "source": source,
            "updated_at": utc_now_iso(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coordination_conflict_policies(profile_id,strategy,source,updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(profile_id) DO UPDATE SET
                    strategy=excluded.strategy,
                    source=excluded.source,
                    updated_at=excluded.updated_at
                """,
                (record["profile_id"], record["strategy"], record["source"], record["updated_at"]),
            )
            conn.commit()
        return record

    def list_policies(self, *, limit: int = 500) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT profile_id,strategy,source,updated_at
                FROM coordination_conflict_policies
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (max(int(limit), 1),),
            ).fetchall()
        return [
            {
                "profile_id": str(row[0]),
                "strategy": str(row[1]),
                "source": str(row[2]),
                "updated_at": str(row[3]),
            }
            for row in rows
        ]

    def get_health_report(self) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(1) FROM coordination_conflict_policies").fetchone()[0]
        return {
            "file_path": str(self._db_path),
            "status": "ok",
            "backend": "sqlite",
            "profiles_count": int(total),
            "current_size_bytes": self._db_path.stat().st_size if self._db_path.exists() else 0,
        }

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coordination_conflict_policies(
                    profile_id TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    source TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()


class DualWriteCoordinationAuditStore:
    """Primary file-backed + secondary sqlite dual-write wrapper."""

    def __init__(
        self,
        primary: Any,
        secondary: Any,
        *,
        enabled: bool = True,
        read_preferred_backend: str = "file",
        fallback_to_primary: bool = True,
        profile_allowlist: list[str] | None = None,
        rollout_percentage: int = 0,
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._enabled = bool(enabled)
        self._read_preferred_backend = "sqlite" if str(read_preferred_backend).lower() == "sqlite" else "file"
        self._fallback_to_primary = bool(fallback_to_primary)
        self._profile_allowlist = {_normalize_profile_id(item) for item in list(profile_allowlist or []) if _normalize_profile_id(item)}
        self._rollout_percentage = min(max(int(rollout_percentage), 0), 100)
        self._last_secondary_error: str | None = None
        self._last_read_source: str = "primary_file"
        self._last_read_fallback_reason: str | None = None
        self._last_routing_reason: str = "database_read_preferred_disabled"
        self._metrics_lock = threading.Lock()
        self._read_observability = _new_read_observability_state()
        self._controls_updated_at = utc_now_iso()
        self._controls_source = "settings_bootstrap"

    def append(self, **kwargs):
        event = self._primary.append(**kwargs)
        if self._enabled:
            try:
                self._secondary.append(**kwargs)
                self._last_secondary_error = None
            except Exception as exc:  # noqa: BLE001
                self._last_secondary_error = str(exc)
        return event

    def list_events(self, **kwargs):
        result = self._read_events_with_source(**kwargs)
        self._apply_read_result(
            profile_id=kwargs.get("profile_id"),
            source=str(result["source"]),
            fallback_reason=result["fallback_reason"],
            routing_reason=str(result["routing_reason"]),
            fallback_used=bool(result["fallback_used"]),
        )
        return result["items"]

    def list_archives(self, **kwargs):
        return self._primary.list_archives(**kwargs)

    def get_health_report(self) -> dict[str, Any]:
        primary = self._primary.get_health_report()
        secondary = self._secondary.get_health_report() if self._enabled else {"status": "disabled"}
        status = "ok"
        if str(primary.get("status", "ok")) != "ok":
            status = str(primary.get("status"))
        if self._last_secondary_error:
            status = "warn"
        return {
            **primary,
            "status": status,
            "dual_write_enabled": self._enabled,
            "read_preferred_backend": self._read_preferred_backend,
            "read_fallback_to_primary": self._fallback_to_primary,
            "database_read_profile_allowlist": sorted(self._profile_allowlist),
            "database_read_rollout_percentage": self._rollout_percentage,
            "last_read_source": self._last_read_source,
            "last_read_fallback_reason": self._last_read_fallback_reason,
            "last_routing_reason": self._last_routing_reason,
            "read_observability": self._get_read_observability_report(),
            "secondary": secondary,
            "secondary_last_error": self._last_secondary_error,
        }

    def get_read_routing_controls(self) -> dict[str, Any]:
        return {
            "preferred_backend": self._read_preferred_backend,
            "fallback_to_primary": self._fallback_to_primary,
            "profile_allowlist": sorted(self._profile_allowlist),
            "rollout_percentage": self._rollout_percentage,
            "updated_at": self._controls_updated_at,
            "source": self._controls_source,
        }

    def update_read_routing_controls(
        self,
        *,
        profile_allowlist: list[str] | None = None,
        rollout_percentage: int | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        if profile_allowlist is not None:
            self._profile_allowlist = {
                _normalize_profile_id(item) for item in list(profile_allowlist) if _normalize_profile_id(item)
            }
        if rollout_percentage is not None:
            self._rollout_percentage = min(max(int(rollout_percentage), 0), 100)
        self._controls_updated_at = utc_now_iso()
        self._controls_source = source or "manual"
        return self.get_read_routing_controls()

    def drill_read(
        self,
        *,
        profile_id: str | None = None,
        strategy: str | None = None,
        outcome: str | None = None,
        event_type: str | None = None,
        window_limit: int = 100,
        simulate_secondary_failure: bool = False,
    ) -> dict[str, Any]:
        result = self._read_events_with_source(
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            event_type=event_type,
            limit=max(int(window_limit), 1),
            simulate_secondary_failure=simulate_secondary_failure,
        )
        self._apply_read_result(
            profile_id=profile_id,
            source=str(result["source"]),
            fallback_reason=result["fallback_reason"],
            routing_reason=str(result["routing_reason"]),
            fallback_used=bool(result["fallback_used"]),
        )
        items = result["items"]
        return {
            "status": "ok" if not result["fallback_used"] else "degraded",
            "preferred_backend": self._read_preferred_backend,
            "selected_backend": result["source"],
            "fallback_used": bool(result["fallback_used"]),
            "fallback_reason": result["fallback_reason"],
            "routing_reason": result["routing_reason"],
            "allowlist_hit": bool(result["allowlist_hit"]),
            "rollout_percentage": self._rollout_percentage,
            "rollout_bucket": result["rollout_bucket"],
            "events_count": len(items),
            "sample_event_ids": [str(item.event_id) for item in items[:5]],
            "observability": self._get_read_observability_report(profile_limit=10),
        }

    def compare_consistency(
        self,
        *,
        profile_id: str | None = None,
        strategy: str | None = None,
        outcome: str | None = None,
        event_type: str | None = None,
        window_limit: int = 200,
    ) -> dict[str, Any]:
        if not self._enabled:
            return {
                "status": "disabled",
                "reason": "dual-write not enabled",
                "window_limit": max(int(window_limit), 1),
            }
        file_items = self._primary.list_events(
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            event_type=event_type,
            limit=window_limit,
        )
        sqlite_items = self._secondary.list_events(
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            event_type=event_type,
            limit=window_limit,
        )
        file_signatures = [self._event_signature(item) for item in file_items]
        sqlite_signatures = [self._event_signature(item) for item in sqlite_items]
        file_set = set(file_signatures)
        sqlite_set = set(sqlite_signatures)
        missing_in_sqlite = [sig for sig in file_signatures if sig not in sqlite_set]
        missing_in_file = [sig for sig in sqlite_signatures if sig not in file_set]
        status = "consistent" if not missing_in_sqlite and not missing_in_file else "mismatch"
        anomalies = []
        if missing_in_sqlite:
            anomalies.append(
                {"type": "missing_in_sqlite", "count": len(missing_in_sqlite), "samples": missing_in_sqlite[:20]}
            )
        if missing_in_file:
            anomalies.append({"type": "missing_in_file", "count": len(missing_in_file), "samples": missing_in_file[:20]})
        return {
            "status": status,
            "window_limit": max(int(window_limit), 1),
            "file_count": len(file_items),
            "sqlite_count": len(sqlite_items),
            "common_count": len(file_set & sqlite_set),
            "difference_count": len(missing_in_sqlite) + len(missing_in_file),
            "anomalies": anomalies,
        }

    def _event_signature(self, item: Any) -> str:
        payload = item.payload if hasattr(item, "payload") else {}
        data = {
            "event_type": str(getattr(item, "event_type", "")),
            "profile_id": str(getattr(item, "profile_id", "")),
            "strategy": str(getattr(item, "strategy", "")),
            "outcome": str(getattr(item, "outcome", "")),
            "reason": str(getattr(item, "reason", "")),
            "run_id": str(getattr(item, "run_id", "")),
            "conflict_run_id": str(getattr(item, "conflict_run_id", "")),
            "route_mode": str(getattr(item, "route_mode", "")),
            "payload": payload if isinstance(payload, dict) else {},
        }
        return json.dumps(data, ensure_ascii=True, sort_keys=True)

    def _read_events_with_source(self, **kwargs) -> dict[str, Any]:
        simulate_secondary_failure = bool(kwargs.pop("simulate_secondary_failure", False))
        profile_id = _normalize_profile_id(kwargs.get("profile_id"))
        route = self._resolve_read_route(profile_id)
        if route["use_database"] is not True:
            return {
                "items": self._primary.list_events(**kwargs),
                "source": "primary_file",
                "fallback_used": False,
                "fallback_reason": None,
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }
        try:
            if simulate_secondary_failure:
                raise RuntimeError("simulated secondary read failure")
            return {
                "items": self._secondary.list_events(**kwargs),
                "source": "secondary_sqlite",
                "fallback_used": False,
                "fallback_reason": None,
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }
        except Exception as exc:  # noqa: BLE001
            self._last_secondary_error = str(exc)
            if not self._fallback_to_primary:
                raise
            return {
                "items": self._primary.list_events(**kwargs),
                "source": "primary_file_fallback",
                "fallback_used": True,
                "fallback_reason": str(exc),
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }

    def _resolve_read_route(self, profile_id: str | None) -> dict[str, Any]:
        if not self._enabled or self._read_preferred_backend != "sqlite":
            return {
                "use_database": False,
                "reason": "database_read_preferred_disabled",
                "allowlist_hit": False,
                "rollout_bucket": None,
            }
        if not self._profile_allowlist and self._rollout_percentage <= 0:
            return {
                "use_database": True,
                "reason": "global_preferred",
                "allowlist_hit": False,
                "rollout_bucket": _profile_rollout_bucket(profile_id) if profile_id else None,
            }
        if profile_id in self._profile_allowlist:
            return {
                "use_database": True,
                "reason": "allowlist",
                "allowlist_hit": True,
                "rollout_bucket": _profile_rollout_bucket(profile_id) if profile_id else None,
            }
        if profile_id and self._rollout_percentage > 0:
            rollout_bucket = _profile_rollout_bucket(profile_id)
            if rollout_bucket < self._rollout_percentage:
                return {
                    "use_database": True,
                    "reason": "rollout_percentage",
                    "allowlist_hit": False,
                    "rollout_bucket": rollout_bucket,
                }
            return {
                "use_database": False,
                "reason": "rollout_excluded",
                "allowlist_hit": False,
                "rollout_bucket": rollout_bucket,
            }
        if profile_id is None:
            return {
                "use_database": False,
                "reason": "profile_required",
                "allowlist_hit": False,
                "rollout_bucket": None,
            }
        return {
            "use_database": False,
            "reason": "not_selected",
            "allowlist_hit": False,
            "rollout_bucket": _profile_rollout_bucket(profile_id),
        }

    def _apply_read_result(
        self,
        *,
        profile_id: str | None,
        source: str,
        fallback_reason: Any,
        routing_reason: str,
        fallback_used: bool,
    ) -> None:
        self._last_read_source = source
        self._last_read_fallback_reason = str(fallback_reason) if fallback_reason else None
        self._last_routing_reason = routing_reason
        with self._metrics_lock:
            _update_read_observability_state(
                self._read_observability,
                profile_id=profile_id,
                source=source,
                routing_reason=routing_reason,
                fallback_used=fallback_used,
            )

    def _get_read_observability_report(self, *, profile_limit: int = 20) -> dict[str, Any]:
        with self._metrics_lock:
            return _build_read_observability_report(self._read_observability, profile_limit=profile_limit)


class DualWriteCoordinationPolicyStore:
    """Primary file-backed + secondary sqlite dual-write wrapper."""

    def __init__(
        self,
        primary: Any,
        secondary: Any,
        *,
        enabled: bool = True,
        read_preferred_backend: str = "file",
        fallback_to_primary: bool = True,
        profile_allowlist: list[str] | None = None,
        rollout_percentage: int = 0,
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._enabled = bool(enabled)
        self._read_preferred_backend = "sqlite" if str(read_preferred_backend).lower() == "sqlite" else "file"
        self._fallback_to_primary = bool(fallback_to_primary)
        self._profile_allowlist = {_normalize_profile_id(item) for item in list(profile_allowlist or []) if _normalize_profile_id(item)}
        self._rollout_percentage = min(max(int(rollout_percentage), 0), 100)
        self._last_secondary_error: str | None = None
        self._last_read_source: str = "primary_file"
        self._last_read_fallback_reason: str | None = None
        self._last_routing_reason: str = "database_read_preferred_disabled"
        self._metrics_lock = threading.Lock()
        self._read_observability = _new_read_observability_state()
        self._controls_updated_at = utc_now_iso()
        self._controls_source = "settings_bootstrap"

    def get_strategy(self, profile_id: str) -> str | None:
        result = self._read_strategy_with_source(profile_id=profile_id)
        self._apply_read_result(
            profile_id=profile_id,
            source=str(result["source"]),
            fallback_reason=result["fallback_reason"],
            routing_reason=str(result["routing_reason"]),
            fallback_used=bool(result["fallback_used"]),
        )
        return result["strategy"]

    def set_strategy(self, *, profile_id: str, strategy: str, source: str = "manual") -> dict[str, str]:
        record = self._primary.set_strategy(profile_id=profile_id, strategy=strategy, source=source)
        if self._enabled:
            try:
                self._secondary.set_strategy(profile_id=profile_id, strategy=strategy, source=source)
                self._last_secondary_error = None
            except Exception as exc:  # noqa: BLE001
                self._last_secondary_error = str(exc)
        return record

    def get_health_report(self) -> dict[str, Any]:
        primary = self._primary.get_health_report()
        secondary = self._secondary.get_health_report() if self._enabled else {"status": "disabled"}
        status = "ok"
        if str(primary.get("status", "ok")) != "ok":
            status = str(primary.get("status"))
        if self._last_secondary_error:
            status = "warn"
        return {
            **primary,
            "status": status,
            "dual_write_enabled": self._enabled,
            "read_preferred_backend": self._read_preferred_backend,
            "read_fallback_to_primary": self._fallback_to_primary,
            "database_read_profile_allowlist": sorted(self._profile_allowlist),
            "database_read_rollout_percentage": self._rollout_percentage,
            "last_read_source": self._last_read_source,
            "last_read_fallback_reason": self._last_read_fallback_reason,
            "last_routing_reason": self._last_routing_reason,
            "read_observability": self._get_read_observability_report(),
            "secondary": secondary,
            "secondary_last_error": self._last_secondary_error,
        }

    def get_read_routing_controls(self) -> dict[str, Any]:
        return {
            "preferred_backend": self._read_preferred_backend,
            "fallback_to_primary": self._fallback_to_primary,
            "profile_allowlist": sorted(self._profile_allowlist),
            "rollout_percentage": self._rollout_percentage,
            "updated_at": self._controls_updated_at,
            "source": self._controls_source,
        }

    def update_read_routing_controls(
        self,
        *,
        profile_allowlist: list[str] | None = None,
        rollout_percentage: int | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        if profile_allowlist is not None:
            self._profile_allowlist = {
                _normalize_profile_id(item) for item in list(profile_allowlist) if _normalize_profile_id(item)
            }
        if rollout_percentage is not None:
            self._rollout_percentage = min(max(int(rollout_percentage), 0), 100)
        self._controls_updated_at = utc_now_iso()
        self._controls_source = source or "manual"
        return self.get_read_routing_controls()

    def drill_read(self, *, profile_id: str, simulate_secondary_failure: bool = False) -> dict[str, Any]:
        result = self._read_strategy_with_source(
            profile_id=profile_id,
            simulate_secondary_failure=simulate_secondary_failure,
        )
        self._apply_read_result(
            profile_id=profile_id,
            source=str(result["source"]),
            fallback_reason=result["fallback_reason"],
            routing_reason=str(result["routing_reason"]),
            fallback_used=bool(result["fallback_used"]),
        )
        return {
            "status": "ok" if not result["fallback_used"] else "degraded",
            "profile_id": profile_id,
            "preferred_backend": self._read_preferred_backend,
            "selected_backend": result["source"],
            "fallback_used": bool(result["fallback_used"]),
            "fallback_reason": result["fallback_reason"],
            "routing_reason": result["routing_reason"],
            "allowlist_hit": bool(result["allowlist_hit"]),
            "rollout_percentage": self._rollout_percentage,
            "rollout_bucket": result["rollout_bucket"],
            "strategy": result["strategy"],
            "observability": self._get_read_observability_report(profile_limit=10),
        }

    def compare_consistency(self, *, limit: int = 500) -> dict[str, Any]:
        if not self._enabled:
            return {
                "status": "disabled",
                "reason": "dual-write not enabled",
                "limit": max(int(limit), 1),
            }
        file_items = self._primary.list_policies(limit=limit)
        sqlite_items = self._secondary.list_policies(limit=limit)
        file_map = {item["profile_id"]: item for item in file_items}
        sqlite_map = {item["profile_id"]: item for item in sqlite_items}
        missing_in_sqlite: list[dict[str, str]] = []
        mismatched: list[dict[str, str]] = []
        for profile_id, file_item in file_map.items():
            sqlite_item = sqlite_map.get(profile_id)
            if sqlite_item is None:
                missing_in_sqlite.append({"profile_id": profile_id, "strategy": file_item.get("strategy", "")})
                continue
            if file_item.get("strategy") != sqlite_item.get("strategy"):
                mismatched.append(
                    {
                        "profile_id": profile_id,
                        "file_strategy": str(file_item.get("strategy", "")),
                        "sqlite_strategy": str(sqlite_item.get("strategy", "")),
                    }
                )
        missing_in_file = [
            {"profile_id": pid, "strategy": str(item.get("strategy", ""))}
            for pid, item in sqlite_map.items()
            if pid not in file_map
        ]
        status = "consistent"
        if missing_in_sqlite or missing_in_file or mismatched:
            status = "mismatch"
        anomalies = []
        if missing_in_sqlite:
            anomalies.append({"type": "missing_in_sqlite", "count": len(missing_in_sqlite), "samples": missing_in_sqlite[:20]})
        if missing_in_file:
            anomalies.append({"type": "missing_in_file", "count": len(missing_in_file), "samples": missing_in_file[:20]})
        if mismatched:
            anomalies.append({"type": "strategy_mismatch", "count": len(mismatched), "samples": mismatched[:20]})
        return {
            "status": status,
            "limit": max(int(limit), 1),
            "file_count": len(file_items),
            "sqlite_count": len(sqlite_items),
            "difference_count": len(missing_in_sqlite) + len(missing_in_file) + len(mismatched),
            "anomalies": anomalies,
        }

    def _read_strategy_with_source(self, *, profile_id: str, simulate_secondary_failure: bool = False) -> dict[str, Any]:
        normalized_profile_id = _normalize_profile_id(profile_id)
        route = self._resolve_read_route(normalized_profile_id)
        if route["use_database"] is not True:
            return {
                "strategy": self._primary.get_strategy(profile_id),
                "source": "primary_file",
                "fallback_used": False,
                "fallback_reason": None,
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }
        try:
            if simulate_secondary_failure:
                raise RuntimeError("simulated secondary read failure")
            return {
                "strategy": self._secondary.get_strategy(profile_id),
                "source": "secondary_sqlite",
                "fallback_used": False,
                "fallback_reason": None,
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }
        except Exception as exc:  # noqa: BLE001
            self._last_secondary_error = str(exc)
            if not self._fallback_to_primary:
                raise
            return {
                "strategy": self._primary.get_strategy(profile_id),
                "source": "primary_file_fallback",
                "fallback_used": True,
                "fallback_reason": str(exc),
                "routing_reason": route["reason"],
                "allowlist_hit": route["allowlist_hit"],
                "rollout_bucket": route["rollout_bucket"],
            }

    def _resolve_read_route(self, profile_id: str | None) -> dict[str, Any]:
        if not self._enabled or self._read_preferred_backend != "sqlite":
            return {
                "use_database": False,
                "reason": "database_read_preferred_disabled",
                "allowlist_hit": False,
                "rollout_bucket": None,
            }
        if not self._profile_allowlist and self._rollout_percentage <= 0:
            return {
                "use_database": True,
                "reason": "global_preferred",
                "allowlist_hit": False,
                "rollout_bucket": _profile_rollout_bucket(profile_id) if profile_id else None,
            }
        if profile_id in self._profile_allowlist:
            return {
                "use_database": True,
                "reason": "allowlist",
                "allowlist_hit": True,
                "rollout_bucket": _profile_rollout_bucket(profile_id) if profile_id else None,
            }
        if profile_id and self._rollout_percentage > 0:
            rollout_bucket = _profile_rollout_bucket(profile_id)
            if rollout_bucket < self._rollout_percentage:
                return {
                    "use_database": True,
                    "reason": "rollout_percentage",
                    "allowlist_hit": False,
                    "rollout_bucket": rollout_bucket,
                }
            return {
                "use_database": False,
                "reason": "rollout_excluded",
                "allowlist_hit": False,
                "rollout_bucket": rollout_bucket,
            }
        return {
            "use_database": False,
            "reason": "not_selected",
            "allowlist_hit": False,
            "rollout_bucket": _profile_rollout_bucket(profile_id) if profile_id else None,
        }

    def _apply_read_result(
        self,
        *,
        profile_id: str | None,
        source: str,
        fallback_reason: Any,
        routing_reason: str,
        fallback_used: bool,
    ) -> None:
        self._last_read_source = source
        self._last_read_fallback_reason = str(fallback_reason) if fallback_reason else None
        self._last_routing_reason = routing_reason
        with self._metrics_lock:
            _update_read_observability_state(
                self._read_observability,
                profile_id=profile_id,
                source=source,
                routing_reason=routing_reason,
                fallback_used=fallback_used,
            )

    def _get_read_observability_report(self, *, profile_limit: int = 20) -> dict[str, Any]:
        with self._metrics_lock:
            return _build_read_observability_report(self._read_observability, profile_limit=profile_limit)
