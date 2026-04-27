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

    login = client.post("/api/v1/auth/login", json={"role_id": "chip-designer"})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    scoped_permissions = client.get("/api/v1/permissions/me", headers={"Authorization": f"Bearer {token}"})
    assert scoped_permissions.status_code == 200
    scoped_data = scoped_permissions.json()["data"]
    assert scoped_data["user"]["role_id"] == "chip-designer"
    assert not any(item["path"].startswith("/admin") for item in scoped_data["menus"])

    forbidden_admin = client.get("/api/v1/admin/agents", headers={"Authorization": f"Bearer {token}"})
    assert forbidden_admin.status_code == 403

    chip_run = client.post(
        "/api/v1/runs",
        json={"run_type": "chat_run", "origin": "test", "status_message": "chip designer can create runs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert chip_run.status_code == 200
    run_id = chip_run.json()["data"]["run_id"]

    forbidden_cancel = client.post(f"/api/v1/runs/{run_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    assert forbidden_cancel.status_code == 403

    forbidden_retry = client.post(f"/api/v1/runs/{run_id}/retry", headers={"Authorization": f"Bearer {token}"})
    assert forbidden_retry.status_code == 403

    artifacts = client.get("/api/v1/artifacts", headers={"Authorization": f"Bearer {token}"})
    assert artifacts.status_code == 200
    artifact_id = artifacts.json()["data"]["items"][0]["artifact_id"]

    preview = client.get(f"/api/v1/artifacts/{artifact_id}/preview", headers={"Authorization": f"Bearer {token}"})
    assert preview.status_code == 200

    forbidden_export = client.post(f"/api/v1/artifacts/{artifact_id}/export", headers={"Authorization": f"Bearer {token}"})
    assert forbidden_export.status_code == 403

    for role_id in ["test-engineer", "data-analyst", "project-manager"]:
        role_login = client.post("/api/v1/auth/login", json={"role_id": role_id})
        assert role_login.status_code == 200
        role_token = role_login.json()["data"]["access_token"]
        role_permissions = client.get("/api/v1/permissions/me", headers={"Authorization": f"Bearer {role_token}"})
        assert role_permissions.status_code == 200
        assert role_permissions.json()["data"]["user"]["role_id"] == role_id

    analyst_login = client.post("/api/v1/auth/login", json={"role_id": "data-analyst"})
    analyst_token = analyst_login.json()["data"]["access_token"]
    analyst_export = client.post(
        f"/api/v1/artifacts/{artifact_id}/export",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert analyst_export.status_code == 200

    analyst_archive = client.post(
        f"/api/v1/artifacts/{artifact_id}/archive",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert analyst_archive.status_code == 403

    test_login = client.post("/api/v1/auth/login", json={"role_id": "test-engineer"})
    test_token = test_login.json()["data"]["access_token"]
    test_data = client.get("/api/v1/data/catalog", headers={"Authorization": f"Bearer {test_token}"})
    assert test_data.status_code == 200
    test_chat = client.post("/api/v1/chat", json={"message": "hello"}, headers={"Authorization": f"Bearer {test_token}"})
    assert test_chat.status_code == 403
    test_knowledge = client.get("/api/v1/knowledge/items", headers={"Authorization": f"Bearer {test_token}"})
    assert test_knowledge.status_code == 403


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
