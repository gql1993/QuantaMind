from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/agents", tags=["admin-agents"])


AGENT_GOVERNANCE_ITEMS = [
    {
        "agent_id": "orchestrator",
        "display_name": "总控编排智能体",
        "status": "enabled",
        "version": "v2-demo",
        "risk_level": "medium",
        "tool_policy": "standard",
        "allowed_tools": ["run:create", "artifact:read", "memory:read"],
        "last_audit_at": "2026-04-26T08:20:00Z",
    },
    {
        "agent_id": "design_specialist",
        "display_name": "芯片设计专家",
        "status": "enabled",
        "version": "v2-demo",
        "risk_level": "high",
        "tool_policy": "restricted",
        "allowed_tools": ["simulation:read", "artifact:write", "knowledge:read"],
        "last_audit_at": "2026-04-26T07:40:00Z",
    },
    {
        "agent_id": "data_analyst",
        "display_name": "数据分析智能体",
        "status": "enabled",
        "version": "v2-demo",
        "risk_level": "medium",
        "tool_policy": "data-safe",
        "allowed_tools": ["data:read", "artifact:write", "knowledge:read"],
        "last_audit_at": "2026-04-25T22:10:00Z",
    },
]


@router.get("")
def list_agent_governance() -> dict:
    return {
        "success": True,
        "data": {
            "items": AGENT_GOVERNANCE_ITEMS,
            "total": len(AGENT_GOVERNANCE_ITEMS),
        },
        "error": None,
    }


@router.get("/summary")
def agent_governance_summary() -> dict:
    enabled_count = len([item for item in AGENT_GOVERNANCE_ITEMS if item["status"] == "enabled"])
    high_risk_count = len([item for item in AGENT_GOVERNANCE_ITEMS if item["risk_level"] == "high"])
    return {
        "success": True,
        "data": {
            "enabled_count": enabled_count,
            "disabled_count": len(AGENT_GOVERNANCE_ITEMS) - enabled_count,
            "high_risk_count": high_risk_count,
            "policy_count": len({item["tool_policy"] for item in AGENT_GOVERNANCE_ITEMS}),
        },
        "error": None,
    }
