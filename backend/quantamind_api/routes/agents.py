from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from quantamind_v2.agents import AgentRegistry

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def _registry(request: Request) -> AgentRegistry:
    return request.app.state.agent_registry


@router.get("")
def list_agents(request: Request) -> dict:
    agents = sorted(_registry(request).list(), key=lambda item: item.agent_id)
    return {
        "success": True,
        "data": {
            "items": [agent.to_dict() for agent in agents],
            "total": len(agents),
        },
        "error": None,
    }


@router.get("/{agent_id}")
def get_agent(request: Request, agent_id: str) -> dict:
    agent = _registry(request).get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"success": True, "data": agent.to_dict(), "error": None}
