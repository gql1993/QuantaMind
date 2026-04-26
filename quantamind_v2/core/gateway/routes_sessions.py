from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from quantamind_v2.core.gateway.deps import GatewayDeps
from quantamind_v2.core.gateway.schemas import SessionHeartbeatRequest, SessionLeaseCreateRequest
from quantamind_v2.core.sessions import SessionConflictError


def build_sessions_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v2/sessions")
    async def list_sessions(
        profile_id: str | None = Query(default=None),
        include_expired: bool = Query(default=False),
    ) -> dict:
        items = deps.session_manager.list_sessions(profile_id=profile_id, include_expired=include_expired)
        return {"items": [item.to_dict() for item in items]}

    @router.post("/api/v2/sessions/leases")
    async def create_session_lease(body: SessionLeaseCreateRequest) -> dict:
        existing_writers = [
            item
            for item in deps.session_manager.list_sessions(profile_id=body.profile_id, include_expired=False)
            if item.access_mode == "writer"
        ]
        try:
            session = deps.session_manager.open_session(
                profile_id=body.profile_id,
                client_type=body.client_type,
                client_id=body.client_id,
                access_mode=body.access_mode,
                allow_handover=body.allow_handover,
                lease_seconds=body.lease_seconds,
                metadata=dict(body.metadata or {}),
            )
        except SessionConflictError as exc:
            session_id = existing_writers[0].session_id if existing_writers else "unknown"
            deps.session_transcript.append(
                session_id,
                "session_conflict",
                {
                    "profile_id": body.profile_id,
                    "requested_client_id": body.client_id,
                    "requested_mode": body.access_mode,
                    "reason": str(exc),
                },
                actor=body.client_id,
                operation="session.open.conflict",
                target=session_id,
                source="session",
                severity="warn",
                tags=["conflict", "lease"],
            )
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        deps.session_transcript.append(
            session.session_id,
            "session_opened",
            {
                "profile_id": session.profile_id,
                "client_type": session.client_type,
                "client_id": session.client_id,
                "access_mode": session.access_mode,
            },
            actor=session.client_id,
            operation="session.open",
            target=session.session_id,
            source="session",
            tags=["lease", session.client_type, session.access_mode],
        )
        if body.allow_handover and body.access_mode == "writer" and existing_writers:
            previous = existing_writers[0]
            deps.session_transcript.append(
                previous.session_id,
                "session_handover",
                {
                    "profile_id": body.profile_id,
                    "from_session_id": previous.session_id,
                    "to_session_id": session.session_id,
                    "to_client_id": session.client_id,
                },
                actor=session.client_id,
                operation="session.open.handover",
                target=previous.session_id,
                source="session",
                severity="warn",
                tags=["handover", "lease", "writer"],
            )
        return {"session": session.to_dict()}

    @router.get("/api/v2/sessions/audit/events")
    async def list_session_audit_events(
        profile_id: str | None = Query(default=None),
        source: str | None = Query(default=None),
        operation: str | None = Query(default=None),
        limit: int = Query(default=200),
    ) -> dict:
        items = deps.session_transcript.list_all(
            profile_id=profile_id,
            source=source,
            operation=operation,
            limit=limit,
        )
        return {"items": [item.to_dict() for item in items]}

    @router.get("/api/v2/sessions/audit/export")
    async def export_session_audit(
        profile_id: str | None = Query(default=None),
        source: str | None = Query(default=None),
        operation: str | None = Query(default=None),
        limit: int = Query(default=1000),
    ) -> dict:
        items = deps.session_transcript.list_all(
            profile_id=profile_id,
            source=source,
            operation=operation,
            limit=limit,
        )
        return {
            "summary": {
                "total": len(items),
                "profile_id": profile_id,
                "source": source,
                "operation": operation,
            },
            "items": [item.to_dict() for item in items],
        }

    @router.get("/api/v2/sessions/{session_id}")
    async def get_session(session_id: str) -> dict:
        session = deps.session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"session not found: {session_id}")
        return session.to_dict()

    @router.post("/api/v2/sessions/{session_id}/heartbeat")
    async def heartbeat_session(session_id: str, body: SessionHeartbeatRequest) -> dict:
        try:
            session = deps.session_manager.heartbeat(session_id, lease_seconds=body.lease_seconds)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        deps.session_transcript.append(
            session_id,
            "session_heartbeat",
            {
                "lease_seconds": body.lease_seconds,
                "profile_id": session.profile_id,
                "client_type": session.client_type,
                "client_id": session.client_id,
            },
            actor=session.client_id,
            operation="session.heartbeat",
            target=session.session_id,
            source="session",
            tags=["lease", session.client_type],
        )
        return {"session": session.to_dict()}

    @router.post("/api/v2/sessions/{session_id}/release")
    async def release_session(session_id: str, reason: str = Query(default="manual_release")) -> dict:
        try:
            session = deps.session_manager.release(session_id, reason=reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        deps.session_transcript.append(
            session_id,
            "session_released",
            {
                "reason": reason,
                "profile_id": session.profile_id,
                "client_type": session.client_type,
                "client_id": session.client_id,
            },
            actor=session.client_id,
            operation="session.release",
            target=session.session_id,
            source="session",
            tags=["lease", session.client_type],
        )
        return {"session": session.to_dict()}

    @router.get("/api/v2/sessions/{session_id}/events")
    async def list_session_events(
        session_id: str,
        event_type: str | None = Query(default=None),
        source: str | None = Query(default=None),
        operation: str | None = Query(default=None),
        limit: int = Query(default=200),
    ) -> dict:
        session = deps.session_manager.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"session not found: {session_id}")
        items = deps.session_transcript.list_events(
            session_id,
            event_type=event_type,
            source=source,
            operation=operation,
            limit=limit,
        )
        return {"items": [item.to_dict() for item in items]}

    return router
