from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from quantamind_v2.client.desktop.models import DesktopCard, DesktopWorkspaceSnapshot


class DesktopWorkspaceShell:
    """Desktop workspace shell for V2 gateway snapshots."""

    def __init__(
        self,
        gateway_base: str = "http://127.0.0.1:18790",
        *,
        timeout: float = 5.0,
        panel_refresh_overrides: dict[str, int] | None = None,
    ) -> None:
        self.gateway_base = gateway_base.rstrip("/")
        self.timeout = timeout
        self.panel_refresh_overrides = dict(panel_refresh_overrides or {})

    def _get_json(self, path: str) -> tuple[int, dict[str, Any]]:
        url = self.gateway_base + path
        req = urllib.request.Request(url=url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                payload = json.loads(raw) if raw else {}
                return int(resp.getcode()), payload
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
            except Exception:  # noqa: BLE001
                payload = {"raw": raw}
            return int(exc.code), payload
        except Exception as exc:  # noqa: BLE001
            return 0, {"error": str(exc)}

    def collect_snapshot(self) -> DesktopWorkspaceSnapshot:
        snap = DesktopWorkspaceSnapshot(gateway_base=self.gateway_base)

        code, health_payload = self._get_json("/health")
        snap.health_ok = code == 200 and health_payload.get("status") == "ok"
        snap.health_payload = health_payload
        if not snap.health_ok:
            snap.warnings.append("gateway health probe failed")

        code, workspace_payload = self._get_json("/api/v2/client/workspace/snapshot?target=desktop")
        layout_payload = workspace_payload.get("layout", {}) if code == 200 else {}
        panels_payload = list(layout_payload.get("panels", [])) if isinstance(layout_payload, dict) else []
        if code == 200:
            snap.active_layout_id = str(layout_payload.get("layout_id", ""))
            snap.active_layout_name = str(layout_payload.get("name", ""))
            snap.active_panels = [str(item.get("panel_id", "")) for item in panels_payload if item.get("panel_id")]
            summary = (workspace_payload.get("state") or {}).get("summary") or {}
            snap.running_runs = int(summary.get("run_running", 0))
            snap.failed_runs = int(summary.get("run_failed", 0))
            snap.running_tasks = int(summary.get("task_running", 0))
            snap.artifacts_total = int(summary.get("artifact_total", 0))
        else:
            snap.warnings.append("cannot query /api/v2/client/workspace/snapshot?target=desktop")

        code, shared_payload = self._get_json("/api/v2/client/shared/state")
        if code == 200:
            summary = (shared_payload.get("state") or {}).get("summary") or {}
            if snap.running_runs == 0:
                snap.running_runs = int(summary.get("run_running", 0))
            if snap.failed_runs == 0:
                snap.failed_runs = int(summary.get("run_failed", 0))
            if snap.running_tasks == 0:
                snap.running_tasks = int(summary.get("task_running", 0))
            if snap.artifacts_total == 0:
                snap.artifacts_total = int(summary.get("artifact_total", 0))
        else:
            snap.warnings.append("cannot query /api/v2/client/shared/state")
            code, runs_payload = self._get_json("/api/v2/console/runs")
            if code == 200:
                items = runs_payload.get("items", [])
                snap.running_runs = sum(1 for item in items if (item.get("run") or {}).get("state") == "running")
                snap.failed_runs = sum(1 for item in items if (item.get("run") or {}).get("state") == "failed")
            else:
                snap.warnings.append("cannot query /api/v2/console/runs")

            code, tasks_payload = self._get_json("/api/v2/tasks?state=running")
            if code == 200:
                snap.running_tasks = len(tasks_payload.get("items", []))
            else:
                snap.warnings.append("cannot query running tasks")

            code, artifacts_payload = self._get_json("/api/v2/artifacts")
            if code == 200:
                snap.artifacts_total = len(artifacts_payload.get("items", []))
            else:
                snap.warnings.append("cannot query artifacts")

        code, approvals_payload = self._get_json("/api/v2/approvals?status=pending")
        if code == 200:
            snap.pending_approvals = len(approvals_payload.get("items", []))
        else:
            snap.warnings.append("cannot query pending approvals")

        panel_specs = panels_payload or [
            {"panel_id": "health", "title": "Gateway Health", "order": 1},
            {"panel_id": "runs", "title": "Run Console", "order": 2},
            {"panel_id": "tasks", "title": "Task Center", "order": 3},
            {"panel_id": "approvals", "title": "Approval Center", "order": 4},
            {"panel_id": "artifacts", "title": "Artifact Viewer", "order": 5},
        ]
        snap.cards = [self._build_panel_card(panel, snap, health_payload) for panel in panel_specs]
        return snap

    def _build_panel_card(self, panel: dict[str, Any], snap: DesktopWorkspaceSnapshot, health_payload: dict[str, Any]) -> DesktopCard:
        panel_id = str(panel.get("panel_id", "unknown"))
        title = str(panel.get("title", panel_id))
        refresh_seconds = self._get_refresh_interval(panel_id)
        if panel_id == "health":
            return DesktopCard(
                card_id=panel_id,
                title=title,
                level="ok" if snap.health_ok else "danger",
                summary="healthy" if snap.health_ok else "degraded",
                metadata={
                    "status": health_payload.get("status", "unknown"),
                    "refresh_interval_seconds": refresh_seconds,
                },
            )
        if panel_id == "runs":
            return DesktopCard(
                card_id=panel_id,
                title=title,
                level="danger" if snap.failed_runs > 0 else "ok",
                summary=f"running={snap.running_runs}, failed={snap.failed_runs}",
                metadata={
                    "running_runs": snap.running_runs,
                    "failed_runs": snap.failed_runs,
                    "refresh_interval_seconds": refresh_seconds,
                },
            )
        if panel_id == "tasks":
            return DesktopCard(
                card_id=panel_id,
                title=title,
                level="warn" if snap.running_tasks > 10 else "ok",
                summary=f"running tasks={snap.running_tasks}",
                metadata={
                    "running_tasks": snap.running_tasks,
                    "refresh_interval_seconds": refresh_seconds,
                },
            )
        if panel_id == "approvals":
            return DesktopCard(
                card_id=panel_id,
                title=title,
                level="warn" if snap.pending_approvals > 0 else "ok",
                summary=f"pending approvals={snap.pending_approvals}",
                metadata={
                    "pending_approvals": snap.pending_approvals,
                    "refresh_interval_seconds": refresh_seconds,
                },
            )
        if panel_id == "artifacts":
            return DesktopCard(
                card_id=panel_id,
                title=title,
                level="ok",
                summary=f"artifacts total={snap.artifacts_total}",
                metadata={
                    "artifacts_total": snap.artifacts_total,
                    "refresh_interval_seconds": refresh_seconds,
                },
            )
        return DesktopCard(
            card_id=panel_id,
            title=title,
            level="ok",
            summary="custom panel",
            metadata={"refresh_interval_seconds": refresh_seconds},
        )

    def _get_refresh_interval(self, panel_id: str) -> int:
        defaults = {
            "health": 10,
            "runs": 5,
            "tasks": 4,
            "approvals": 6,
            "artifacts": 12,
        }
        if panel_id in self.panel_refresh_overrides:
            return int(self.panel_refresh_overrides[panel_id])
        return int(defaults.get(panel_id, 8))
