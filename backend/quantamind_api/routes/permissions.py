from __future__ import annotations

from fastapi import APIRouter, Header, Request

from backend.quantamind_api.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


def _auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


@router.get("/me")
def current_user_permissions(request: Request, authorization: str | None = Header(default=None)) -> dict:
    return {"success": True, "data": _auth_service(request).permissions(authorization), "error": None}
