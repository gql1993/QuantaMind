from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_planning_preview_returns_plan_and_heuristics():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/planning/preview",
        json={
            "message": "请让设计与工艺团队协同分析这个问题",
            "priority": "normal",
            "budget_seconds": 10,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_result"]["mode"] == "multi_agent_plan"
    assert payload["heuristics"]["complexity"] in {"high", "medium"}
    assert payload["heuristics"]["budget_risk"] == "high"
    assert payload["heuristics"]["effective_priority"] == "high"
    assert payload["plan"]["mode"] == "multi_agent_plan"
    assert payload["plan"]["scheduling"]["priority"] == "high"
    assert payload["plan"]["scheduling"]["budget_seconds"] == 10


def test_gateway_filesystem_and_knowledge_integrations():
    client = TestClient(create_app())
    list_resp = client.get("/api/v2/integrations/filesystem/list?relative_path=docs&limit=10")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) >= 1

    index_resp = client.post(
        "/api/v2/integrations/knowledge/index",
        json={
            "title": "daily note",
            "content": "system status remains stable",
            "source": "test",
        },
    )
    assert index_resp.status_code == 200
    entry_id = index_resp.json()["entry"]["entry_id"]
    assert entry_id.startswith("kentry-")

    search_resp = client.get("/api/v2/integrations/knowledge/search?q=stable")
    assert search_resp.status_code == 200
    assert any(item["entry_id"] == entry_id for item in search_resp.json()["items"])
