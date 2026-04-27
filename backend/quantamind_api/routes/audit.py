from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.quantamind_api.routes.dependencies import require_permission

router = APIRouter(
    prefix="/api/v1/admin/audit",
    tags=["admin-audit"],
    dependencies=[Depends(require_permission("admin:read"))],
)


APPROVALS = [
    {
        "approval_id": "approval-tool-risk-001",
        "title": "高风险设计智能体工具权限申请",
        "requester": "design_specialist",
        "approval_type": "tool_policy",
        "status": "pending",
        "risk_level": "high",
        "created_at": "2026-04-26T08:30:00Z",
    },
    {
        "approval_id": "approval-data-export-002",
        "title": "跨域数据摘要导出申请",
        "requester": "data_analyst",
        "approval_type": "data_export",
        "status": "approved",
        "risk_level": "medium",
        "created_at": "2026-04-25T18:12:00Z",
    },
]

AUDIT_EVENTS = [
    {
        "event_id": "audit-run-retry-001",
        "actor": "demo-user",
        "action": "run.retry",
        "target": "chat_run",
        "result": "success",
        "created_at": "2026-04-26T08:10:00Z",
    },
    {
        "event_id": "audit-permission-read-002",
        "actor": "demo-user",
        "action": "permissions.read",
        "target": "project-manager",
        "result": "success",
        "created_at": "2026-04-26T08:05:00Z",
    },
    {
        "event_id": "audit-agent-policy-003",
        "actor": "admin",
        "action": "agent.policy.review",
        "target": "design_specialist",
        "result": "pending",
        "created_at": "2026-04-26T07:55:00Z",
    },
]


@router.get("/approvals")
def list_approvals() -> dict:
    return {
        "success": True,
        "data": {"items": APPROVALS, "total": len(APPROVALS)},
        "error": None,
    }


@router.get("/events")
def list_audit_events() -> dict:
    return {
        "success": True,
        "data": {"items": AUDIT_EVENTS, "total": len(AUDIT_EVENTS)},
        "error": None,
    }


@router.get("/summary")
def audit_summary() -> dict:
    pending_count = len([item for item in APPROVALS if item["status"] == "pending"])
    high_risk_count = len([item for item in APPROVALS if item["risk_level"] == "high"])
    return {
        "success": True,
        "data": {
            "approval_count": len(APPROVALS),
            "pending_count": pending_count,
            "audit_event_count": len(AUDIT_EVENTS),
            "high_risk_count": high_risk_count,
        },
        "error": None,
    }
