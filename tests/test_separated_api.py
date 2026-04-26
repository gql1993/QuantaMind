from fastapi.testclient import TestClient

from backend.quantamind_api.app import create_app


client = TestClient(create_app())


def test_separated_health_and_permissions_contracts():
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["data"]["status"] == "ok"

    permissions = client.get("/api/v1/permissions/me")
    assert permissions.status_code == 200
    data = permissions.json()["data"]
    assert data["user"]["role_id"]
    assert any(item["path"] == "/workspace/data" for item in data["menus"])


def test_data_and_knowledge_contracts():
    catalog = client.get("/api/v1/data/catalog")
    assert catalog.status_code == 200
    assert catalog.json()["data"]["total"] >= 1

    quality = client.get("/api/v1/data/quality")
    assert quality.status_code == 200
    assert "average_score" in quality.json()["data"]

    knowledge = client.get("/api/v1/knowledge/items")
    assert knowledge.status_code == 200
    assert knowledge.json()["data"]["total"] >= 1

    memories = client.get("/api/v1/knowledge/memories")
    assert memories.status_code == 200
    assert memories.json()["data"]["total"] >= 1


def test_admin_governance_and_audit_contracts():
    agents = client.get("/api/v1/admin/agents")
    assert agents.status_code == 200
    assert agents.json()["data"]["total"] >= 1

    agent_summary = client.get("/api/v1/admin/agents/summary")
    assert agent_summary.status_code == 200
    assert "enabled_count" in agent_summary.json()["data"]

    approvals = client.get("/api/v1/admin/audit/approvals")
    assert approvals.status_code == 200
    assert approvals.json()["data"]["total"] >= 1

    audit_summary = client.get("/api/v1/admin/audit/summary")
    assert audit_summary.status_code == 200
    assert "audit_event_count" in audit_summary.json()["data"]


def test_artifact_action_contracts():
    artifacts = client.get("/api/v1/artifacts")
    assert artifacts.status_code == 200
    artifact_id = artifacts.json()["data"]["items"][0]["artifact_id"]

    preview = client.get(f"/api/v1/artifacts/{artifact_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["data"]["preview_type"] == "json"

    export = client.post(f"/api/v1/artifacts/{artifact_id}/export")
    assert export.status_code == 200
    assert export.json()["data"]["action"] == "export"

    share = client.post(f"/api/v1/artifacts/{artifact_id}/share")
    assert share.status_code == 200
    assert share.json()["data"]["action"] == "share"

    archive = client.post(f"/api/v1/artifacts/{artifact_id}/archive")
    assert archive.status_code == 200
    assert archive.json()["data"]["status"] == "archived"
