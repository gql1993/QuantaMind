from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MENU_ITEMS = [
    {"key": "workspace.overview", "label": "工作台总览", "path": "/workspace", "scope": "workspace", "end": True},
    {"key": "workspace.roles", "label": "角色首页", "path": "/workspace/roles", "scope": "workspace"},
    {"key": "workspace.ai", "label": "AI 工作台", "path": "/workspace/ai", "scope": "workspace"},
    {"key": "workspace.tasks", "label": "我的任务", "path": "/workspace/tasks", "scope": "workspace"},
    {"key": "workspace.artifacts", "label": "产物中心", "path": "/workspace/artifacts", "scope": "workspace"},
    {"key": "workspace.data", "label": "数据中心", "path": "/workspace/data", "scope": "workspace"},
    {"key": "workspace.knowledge", "label": "知识库/记忆", "path": "/workspace/knowledge", "scope": "workspace"},
    {"key": "workspace.agents", "label": "智能体", "path": "/workspace/agents", "scope": "workspace"},
    {"key": "admin.agents", "label": "后台智能体治理", "path": "/admin/agents", "scope": "admin"},
    {"key": "admin.audit", "label": "审批/审计", "path": "/admin/audit", "scope": "admin"},
    {"key": "admin.runs", "label": "后台 Run 控制台", "path": "/admin/runs", "scope": "admin"},
    {"key": "admin.system", "label": "后台系统监控", "path": "/admin/system", "scope": "admin"},
]


ROLE_POLICIES = {
    "chip-designer": {
        "label": "芯片设计人员",
        "menu_keys": [
            "workspace.overview",
            "workspace.roles",
            "workspace.ai",
            "workspace.tasks",
            "workspace.artifacts",
            "workspace.data",
            "workspace.knowledge",
            "workspace.agents",
        ],
        "permissions": [
            "run:read",
            "run:create",
            "artifact:read",
            "agent:read",
            "chat:use",
            "data:read",
            "knowledge:read",
        ],
    },
    "test-engineer": {
        "label": "测控人员",
        "menu_keys": [
            "workspace.overview",
            "workspace.roles",
            "workspace.tasks",
            "workspace.artifacts",
            "workspace.data",
            "workspace.agents",
        ],
        "permissions": ["run:read", "run:create", "artifact:read", "agent:read", "data:read"],
    },
    "data-analyst": {
        "label": "数据分析人员",
        "menu_keys": [
            "workspace.overview",
            "workspace.roles",
            "workspace.ai",
            "workspace.tasks",
            "workspace.artifacts",
            "workspace.data",
            "workspace.knowledge",
            "workspace.agents",
        ],
        "permissions": [
            "run:read",
            "run:create",
            "artifact:read",
            "artifact:export",
            "agent:read",
            "chat:use",
            "data:read",
            "knowledge:read",
        ],
    },
    "project-manager": {
        "label": "项目经理",
        "menu_keys": [
            "workspace.overview",
            "workspace.roles",
            "workspace.ai",
            "workspace.tasks",
            "workspace.artifacts",
            "workspace.data",
            "workspace.knowledge",
            "workspace.agents",
            "admin.agents",
            "admin.audit",
            "admin.runs",
            "admin.system",
        ],
        "permissions": [
            "run:read",
            "run:create",
            "run:cancel",
            "run:retry",
            "artifact:read",
            "artifact:export",
            "artifact:share",
            "artifact:archive",
            "agent:read",
            "chat:use",
            "data:read",
            "knowledge:read",
            "admin:read",
        ],
    },
}


@dataclass(frozen=True)
class DemoUser:
    user_id: str
    display_name: str
    role_id: str


class AuthService:
    """Demo auth service that can be replaced by real users, tokens, and RBAC tables."""

    default_role_id = "project-manager"

    def authenticate(self, role_id: str | None = None) -> dict[str, Any]:
        role_id = role_id if role_id in ROLE_POLICIES else self.default_role_id
        user = self._build_user(role_id)
        return {
            "access_token": f"demo:{role_id}",
            "token_type": "bearer",
            "user": self._user_payload(user),
        }

    def current_user(self, authorization: str | None = None) -> dict[str, Any]:
        user = self._build_user(self._role_from_authorization(authorization))
        return self._user_payload(user)

    def permissions(self, authorization: str | None = None) -> dict[str, Any]:
        user = self._build_user(self._role_from_authorization(authorization))
        policy = ROLE_POLICIES[user.role_id]
        allowed = set(policy["menu_keys"])
        visible_menus = [item for item in MENU_ITEMS if item["key"] in allowed]
        restricted_menus = [item for item in MENU_ITEMS if item["key"] not in allowed]
        return {
            "user": self._user_payload(user),
            "permissions": policy["permissions"],
            "menus": visible_menus,
            "restricted_menus": restricted_menus,
        }

    def has_permission(self, permission: str, authorization: str | None = None) -> bool:
        role_id = self._role_from_authorization(authorization)
        return permission in ROLE_POLICIES[role_id]["permissions"]

    def _role_from_authorization(self, authorization: str | None) -> str:
        if authorization and authorization.startswith("Bearer demo:"):
            role_id = authorization.removeprefix("Bearer demo:")
            if role_id in ROLE_POLICIES:
                return role_id
        return self.default_role_id

    def _build_user(self, role_id: str) -> DemoUser:
        return DemoUser(
            user_id="demo-user",
            display_name="量智大脑演示用户",
            role_id=role_id,
        )

    def _user_payload(self, user: DemoUser) -> dict[str, str]:
        policy = ROLE_POLICIES[user.role_id]
        return {
            "user_id": user.user_id,
            "display_name": user.display_name,
            "role_id": user.role_id,
            "role_label": policy["label"],
        }
