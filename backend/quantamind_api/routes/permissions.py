from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


MENU_ITEMS = [
    {"key": "workspace.overview", "label": "工作台总览", "path": "/workspace", "scope": "workspace", "end": True},
    {"key": "workspace.roles", "label": "角色首页", "path": "/workspace/roles", "scope": "workspace"},
    {"key": "workspace.ai", "label": "AI 工作台", "path": "/workspace/ai", "scope": "workspace"},
    {"key": "workspace.tasks", "label": "我的任务", "path": "/workspace/tasks", "scope": "workspace"},
    {"key": "workspace.artifacts", "label": "产物中心", "path": "/workspace/artifacts", "scope": "workspace"},
    {"key": "workspace.data", "label": "数据中心", "path": "/workspace/data", "scope": "workspace"},
    {"key": "workspace.knowledge", "label": "知识库/记忆", "path": "/workspace/knowledge", "scope": "workspace"},
    {"key": "workspace.agents", "label": "智能体", "path": "/workspace/agents", "scope": "workspace"},
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
        "permissions": ["run:read", "run:create", "artifact:read", "agent:read", "chat:use"],
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
            "admin.runs",
            "admin.system",
        ],
        "permissions": [
            "run:read",
            "run:create",
            "run:retry",
            "artifact:read",
            "agent:read",
            "chat:use",
            "admin:read",
        ],
    },
}


@router.get("/me")
def current_user_permissions() -> dict:
    # Demo identity until authentication is introduced.
    role_id = "project-manager"
    policy = ROLE_POLICIES[role_id]
    allowed = set(policy["menu_keys"])
    visible_menus = [item for item in MENU_ITEMS if item["key"] in allowed]
    restricted_menus = [item for item in MENU_ITEMS if item["key"] not in allowed]

    return {
        "success": True,
        "data": {
            "user": {
                "user_id": "demo-user",
                "display_name": "量智大脑演示用户",
                "role_id": role_id,
                "role_label": policy["label"],
            },
            "permissions": policy["permissions"],
            "menus": visible_menus,
            "restricted_menus": restricted_menus,
        },
        "error": None,
    }
