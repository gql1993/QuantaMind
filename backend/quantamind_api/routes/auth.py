from __future__ import annotations

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from backend.quantamind_api.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    role_id: str | None = None


def _auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


@router.post("/login")
def login(request: Request, payload: LoginRequest) -> dict:
    return {"success": True, "data": _auth_service(request).authenticate(payload.role_id), "error": None}


@router.get("/me")
def current_user(request: Request, authorization: str | None = Header(default=None)) -> dict:
    return {"success": True, "data": _auth_service(request).current_user(authorization), "error": None}
