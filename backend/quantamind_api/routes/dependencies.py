from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException, Request, status


def require_permission(permission: str) -> Callable[[Request, str | None], None]:
    def dependency(request: Request, authorization: str | None = Header(default=None)) -> None:
        auth_service = request.app.state.auth_service
        if not auth_service.has_permission(permission, authorization):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )

    return dependency
