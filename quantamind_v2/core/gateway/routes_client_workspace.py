from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from quantamind_v2.client.shared import WorkspaceLayout, WorkspacePanel, build_shared_client_state
from quantamind_v2.core.gateway.deps import GatewayDeps
from quantamind_v2.core.gateway.schemas import (
    ClientLayoutSyncRequest,
    ClientShortcutsPreferenceRequest,
    WorkspaceRecoveryCreateRequest,
    WorkspaceLayoutCreateRequest,
)


def build_client_workspace_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    def _append_workspace_audit(
        *,
        session_id: str | None,
        event_type: str,
        operation: str,
        target: str,
        profile_id: str,
        payload: dict,
    ) -> None:
        if not session_id:
            return
        session = deps.session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=400, detail=f"invalid session_id: {session_id}")
        deps.session_transcript.append(
            session_id,
            event_type,
            {
                **payload,
                "profile_id": profile_id,
                "client_type": session.client_type,
                "client_id": session.client_id,
            },
            actor=session.client_id,
            operation=operation,
            target=target,
            source="workspace",
            tags=["workspace", session.client_type],
        )

    def _enforce_profile_writer_lock(
        *,
        profile_id: str,
        session_id: str | None,
        operation: str,
        target: str,
    ) -> None:
        # Phase 16-4 follow-up: single-writer policy applies to workspace mutation operations.
        active_writers = [
            item
            for item in deps.session_manager.list_sessions(profile_id=profile_id, include_expired=False)
            if item.access_mode == "writer"
        ]
        if not active_writers:
            return
        active_writer = active_writers[0]
        if not session_id:
            deps.session_transcript.append(
                active_writer.session_id,
                "workspace_write_conflict",
                {
                    "profile_id": profile_id,
                    "operation": operation,
                    "target": target,
                    "reason": "writer_session_required",
                },
                actor="unknown",
                operation="workspace.write.conflict",
                target=target,
                source="workspace",
                severity="warn",
                tags=["workspace", "conflict", "writer"],
            )
            raise HTTPException(
                status_code=409,
                detail=f"writer lock active for profile `{profile_id}`; session_id is required",
            )
        caller = deps.session_manager.get_session(session_id)
        if caller is None:
            raise HTTPException(status_code=400, detail=f"invalid session_id: {session_id}")
        if caller.profile_id != profile_id:
            raise HTTPException(status_code=400, detail="session profile does not match profile_id")
        if caller.status != "active":
            raise HTTPException(status_code=409, detail=f"session is not active: {caller.status}")
        if caller.access_mode != "writer" or caller.session_id != active_writer.session_id:
            deps.session_transcript.append(
                active_writer.session_id,
                "workspace_write_conflict",
                {
                    "profile_id": profile_id,
                    "operation": operation,
                    "target": target,
                    "request_session_id": caller.session_id,
                    "active_writer_session_id": active_writer.session_id,
                },
                actor=caller.client_id,
                operation="workspace.write.conflict",
                target=target,
                source="workspace",
                severity="warn",
                tags=["workspace", "conflict", "writer"],
            )
            raise HTTPException(
                status_code=409,
                detail=f"writer lock active for profile `{profile_id}`; active writer session is `{active_writer.session_id}`",
            )

    @router.get("/api/v2/client/workspace/layouts")
    async def list_workspace_layouts(target: str | None = Query(default=None)) -> dict:
        items = deps.workspace_layouts.list_layouts(target=target)
        return {"items": [item.to_dict() for item in items]}

    @router.get("/api/v2/client/workspace/layouts/{layout_id}")
    async def get_workspace_layout(layout_id: str) -> dict:
        layout = deps.workspace_layouts.get_layout(layout_id)
        if layout is None:
            raise HTTPException(status_code=404, detail=f"layout not found: {layout_id}")
        return layout.to_dict()

    @router.post("/api/v2/client/workspace/layouts")
    async def create_workspace_layout(body: WorkspaceLayoutCreateRequest) -> dict:
        layout = WorkspaceLayout(
            layout_id=body.layout_id.strip(),
            name=body.name.strip(),
            target=body.target.strip().lower() or "web",
            panels=[
                WorkspacePanel(
                    panel_id=item.panel_id,
                    title=item.title,
                    order=item.order,
                    visible=item.visible,
                    source=item.source,
                    metadata=dict(item.metadata or {}),
                )
                for item in body.panels
            ],
        )
        try:
            stored = deps.workspace_layouts.save_layout(layout)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"layout": stored.to_dict()}

    @router.post("/api/v2/client/workspace/layouts/{layout_id}/activate")
    async def activate_workspace_layout(
        layout_id: str,
        target: str | None = Query(default=None),
        profile_id: str = Query(default="default"),
        session_id: str | None = Query(default=None),
    ) -> dict:
        _enforce_profile_writer_lock(
            profile_id=profile_id,
            session_id=session_id,
            operation="workspace.layout.activate",
            target=layout_id,
        )
        try:
            layout = deps.workspace_layouts.activate_layout(layout_id, target=target)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        active_target = (target or layout.target).strip().lower() or layout.target
        prefs = deps.client_preferences.set_active_layout(
            profile_id=profile_id,
            target=active_target,
            layout_id=layout.layout_id,
        )
        _append_workspace_audit(
            session_id=session_id,
            event_type="workspace_layout_activated",
            operation="workspace.layout.activate",
            target=layout.layout_id,
            profile_id=profile_id,
            payload={"active_target": active_target},
        )
        return {"active_target": active_target, "layout": layout.to_dict(), "preferences": prefs.to_dict()}

    @router.get("/api/v2/client/workspace/active-layout")
    async def get_active_layout(target: str = Query(default="web"), profile_id: str = Query(default="default")) -> dict:
        prefs = deps.client_preferences.get_or_create(profile_id)
        preferred_layout_id = prefs.active_layout_by_target.get(target.strip().lower())
        layout = deps.workspace_layouts.get_layout(preferred_layout_id) if preferred_layout_id else None
        if layout is None:
            layout = deps.workspace_layouts.get_active_layout(target=target)
        if layout is None:
            raise HTTPException(status_code=404, detail=f"active layout not found: {target}")
        return layout.to_dict()

    @router.get("/api/v2/client/workspace/snapshot")
    async def get_workspace_snapshot(target: str = Query(default="web"), profile_id: str = Query(default="default")) -> dict:
        prefs = deps.client_preferences.get_or_create(profile_id)
        preferred_layout_id = prefs.active_layout_by_target.get(target.strip().lower())
        layout = deps.workspace_layouts.get_layout(preferred_layout_id) if preferred_layout_id else None
        if layout is None:
            layout = deps.workspace_layouts.get_active_layout(target=target)
        if layout is None:
            raise HTTPException(status_code=404, detail=f"active layout not found: {target}")
        runs = sorted(deps.coordinator.list_runs(), key=lambda item: item.updated_at, reverse=True)
        tasks_items = sorted(deps.tasks.list(), key=lambda item: item.updated_at, reverse=True)
        artifact_items = sorted(deps.artifacts.list(), key=lambda item: item.created_at, reverse=True)
        state = build_shared_client_state(
            runs=[item.model_dump() for item in runs],
            tasks=[item.model_dump() for item in tasks_items],
            artifacts=[item.model_dump() for item in artifact_items],
            run_event_counts={run.run_id: len(deps.coordinator.list_events(run.run_id)) for run in runs},
        )
        latest = deps.workspace_recovery.latest(profile_id=profile_id, target=target.strip().lower() or "web")
        active_sessions = deps.session_manager.list_sessions(profile_id=profile_id, include_expired=False)
        session_items = [item.to_dict() for item in active_sessions]
        by_client_type: dict[str, int] = {}
        expiring_soon_count = 0
        soon_deadline = datetime.now(timezone.utc) + timedelta(seconds=15)
        for item in session_items:
            client_type = str(item.get("client_type", "unknown"))
            by_client_type[client_type] = by_client_type.get(client_type, 0) + 1
            lease_until_raw = str(item.get("lease_until", ""))
            try:
                lease_until = datetime.fromisoformat(lease_until_raw.replace("Z", "+00:00"))
            except ValueError:
                lease_until = None
            if lease_until is not None and lease_until <= soon_deadline:
                expiring_soon_count += 1
        return {
            "target": target,
            "profile_id": profile_id,
            "layout": layout.to_dict(),
            "state": state.to_dict(),
            "preferences": prefs.to_dict(),
            "latest_recovery_point": latest.to_dict() if latest else None,
            "session_presence": {
                "active_total": len(session_items),
                "by_client_type": by_client_type,
                "expiring_soon_count": expiring_soon_count,
                "items": session_items,
            },
        }

    @router.get("/api/v2/client/preferences/{profile_id}")
    async def get_client_preferences(profile_id: str) -> dict:
        prefs = deps.client_preferences.get_or_create(profile_id)
        return prefs.to_dict()

    @router.post("/api/v2/client/preferences/{profile_id}/shortcuts")
    async def update_client_shortcuts(
        profile_id: str,
        body: ClientShortcutsPreferenceRequest,
        session_id: str | None = Query(default=None),
    ) -> dict:
        _enforce_profile_writer_lock(
            profile_id=profile_id,
            session_id=session_id,
            operation="workspace.shortcuts.update",
            target=profile_id,
        )
        prefs = deps.client_preferences.set_pinned_shortcuts(
            profile_id=profile_id,
            shortcuts=list(body.pinned_shortcuts),
        )
        _append_workspace_audit(
            session_id=session_id,
            event_type="workspace_shortcuts_updated",
            operation="workspace.shortcuts.update",
            target=profile_id,
            profile_id=profile_id,
            payload={"count": len(prefs.pinned_shortcuts)},
        )
        return {"preferences": prefs.to_dict()}

    @router.post("/api/v2/client/preferences/{profile_id}/sync-layouts")
    async def sync_client_layout_preferences(
        profile_id: str,
        body: ClientLayoutSyncRequest,
        session_id: str | None = Query(default=None),
    ) -> dict:
        _enforce_profile_writer_lock(
            profile_id=profile_id,
            session_id=session_id,
            operation="workspace.layout.sync",
            target=body.target,
        )
        try:
            prefs = deps.client_preferences.sync_active_layout(
                profile_id=profile_id,
                source_target=body.source_target,
                target=body.target,
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        _append_workspace_audit(
            session_id=session_id,
            event_type="workspace_layout_synced",
            operation="workspace.layout.sync",
            target=body.target,
            profile_id=profile_id,
            payload={"source_target": body.source_target, "target": body.target},
        )
        return {"preferences": prefs.to_dict()}

    @router.post("/api/v2/client/workspace/recovery-points")
    async def create_recovery_point(
        body: WorkspaceRecoveryCreateRequest,
        target: str = Query(default="web"),
        profile_id: str = Query(default="default"),
        session_id: str | None = Query(default=None),
    ) -> dict:
        _enforce_profile_writer_lock(
            profile_id=profile_id,
            session_id=session_id,
            operation="workspace.recovery.create",
            target=target,
        )
        target_name = target.strip().lower() or "web"
        prefs = deps.client_preferences.get_or_create(profile_id)
        active_layout = prefs.active_layout_by_target.get(target_name)
        if not active_layout:
            layout = deps.workspace_layouts.get_active_layout(target=target_name)
            if layout is None:
                raise HTTPException(status_code=404, detail=f"active layout not found: {target_name}")
            active_layout = layout.layout_id
        point = deps.workspace_recovery.create(
            profile_id=profile_id,
            target=target_name,
            layout_id=active_layout,
            run_id=body.run_id,
            task_id=body.task_id,
            artifact_id=body.artifact_id,
            note=body.note,
            metadata=dict(body.metadata or {}),
        )
        _append_workspace_audit(
            session_id=session_id,
            event_type="workspace_recovery_point_created",
            operation="workspace.recovery.create",
            target=point.point_id,
            profile_id=profile_id,
            payload={"target": target_name, "layout_id": active_layout},
        )
        return {"recovery_point": point.to_dict()}

    @router.get("/api/v2/client/workspace/recovery-points")
    async def list_recovery_points(
        target: str | None = Query(default=None),
        profile_id: str = Query(default="default"),
        limit: int = Query(default=20),
    ) -> dict:
        target_name = target.strip().lower() if target else None
        items = deps.workspace_recovery.list(
            profile_id=profile_id,
            target=target_name,
            limit=limit,
        )
        return {"items": [item.to_dict() for item in items]}

    @router.get("/api/v2/client/workspace/recovery-points/latest")
    async def get_latest_recovery_point(target: str = Query(default="web"), profile_id: str = Query(default="default")) -> dict:
        target_name = target.strip().lower() or "web"
        point = deps.workspace_recovery.latest(profile_id=profile_id, target=target_name)
        if point is None:
            raise HTTPException(status_code=404, detail=f"latest recovery point not found: {target_name}")
        return point.to_dict()

    @router.post("/api/v2/client/workspace/recovery-points/{point_id}/activate")
    async def activate_recovery_point(
        point_id: str,
        profile_id: str = Query(default="default"),
        session_id: str | None = Query(default=None),
    ) -> dict:
        _enforce_profile_writer_lock(
            profile_id=profile_id,
            session_id=session_id,
            operation="workspace.recovery.activate",
            target=point_id,
        )
        point = deps.workspace_recovery.get(point_id)
        if point is None:
            raise HTTPException(status_code=404, detail=f"recovery point not found: {point_id}")
        if point.profile_id != profile_id:
            raise HTTPException(status_code=400, detail="profile_id does not match recovery point owner")
        try:
            layout = deps.workspace_layouts.activate_layout(point.layout_id, target=point.target)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        prefs = deps.client_preferences.set_active_layout(
            profile_id=profile_id,
            target=point.target,
            layout_id=layout.layout_id,
        )
        _append_workspace_audit(
            session_id=session_id,
            event_type="workspace_recovery_point_activated",
            operation="workspace.recovery.activate",
            target=point.point_id,
            profile_id=profile_id,
            payload={"layout_id": layout.layout_id, "target": point.target},
        )
        return {"recovery_point": point.to_dict(), "layout": layout.to_dict(), "preferences": prefs.to_dict()}

    return router
