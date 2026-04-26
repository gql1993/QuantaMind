from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_lists_agent_profiles():
    client = TestClient(create_app())
    response = client.get("/api/v2/agents/profiles")
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["agent_id"] for item in items}
    assert "planner" in ids
    assert "intel_officer" in ids


def test_planning_preview_includes_agent_selection():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/planning/preview",
        json={"message": "请发送今天情报"},
    )
    assert response.status_code == 200
    plan = response.json()["plan"]
    assert "agent_selection" in plan
    assert plan["agent_selection"]["primary_agent"] == "intel_officer"
