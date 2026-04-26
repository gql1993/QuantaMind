from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _fake_intel_today(force: bool = False):
    return {
        "status": "sent",
        "summary": "fake intel digest sent",
        "report": {"report_id": "intel-test-001"},
        "force": force,
    }


def _fake_system_status(force: bool = False):
    return {
        "status": "ok",
        "summary": "系统状态：ok\n降级模式：否\n会话数：1",
        "payload": {"gateway": {"status": "ok", "degraded": False}},
        "force": force,
    }


def _fake_db_status(force: bool = False):
    return {
        "status": "ok",
        "summary": "设计主库：已连接\npgvector：已连接\nMES 业务库：已连接",
        "payload": {"statuses": {}},
        "force": force,
    }


def _build_test_client():
    registry = ShortcutRegistry()
    registry.register(
        ShortcutDefinition(
            name="intel_today",
            description="fake shortcut",
            handler=_fake_intel_today,
            triggers=["今天情报"],
            run_type=RunType.DIGEST,
            owner_agent="intel_officer",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="system_status",
            description="fake system status",
            handler=_fake_system_status,
            triggers=["系统状态"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="db_status",
            description="fake db status",
            handler=_fake_db_status,
            triggers=["数据库状态"],
            run_type=RunType.SYSTEM,
            owner_agent="data_analyst",
        )
    )
    return TestClient(create_app(shortcut_registry=registry))


def test_v2_gateway_health():
    client = _build_test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "QuantaMind Gateway V2"


def test_v2_shortcut_creates_completed_run():
    client = _build_test_client()
    response = client.post("/api/v2/shortcuts/intel_today", json={"force": False, "origin": "test"})
    assert response.status_code == 200
    run = response.json()["run"]
    assert run["run_type"] == "digest_run"
    assert run["origin"] == "test"
    assert run["state"] == "completed"
    assert run["owner_agent"] == "intel_officer"
    assert "intel-test-001" in run["artifacts"]


def test_v2_shortcut_writes_artifact_and_view():
    client = _build_test_client()
    response = client.post("/api/v2/shortcuts/intel_today", json={"force": False, "origin": "test"})
    assert response.status_code == 200
    run = response.json()["run"]
    artifact_id = run["artifacts"][0]

    artifact_response = client.get(f"/api/v2/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["run_id"] == run["run_id"]
    assert artifact["artifact_type"] == "intel_report"
    assert artifact["payload"]["shortcut"] == "intel_today"

    view_response = client.get(f"/api/v2/artifacts/{artifact_id}/view")
    assert view_response.status_code == 200
    view = view_response.json()
    assert view["artifact_id"] == artifact_id
    assert view["render_type"] == "text"
    assert "intel_today result" in view["content"]

    run_artifacts_response = client.get(f"/api/v2/runs/{run['run_id']}/artifacts")
    assert run_artifacts_response.status_code == 200
    run_artifacts = run_artifacts_response.json()["items"]
    assert len(run_artifacts) == 1
    assert run_artifacts[0]["artifact_id"] == artifact_id

    filtered_response = client.get(f"/api/v2/artifacts?run_id={run['run_id']}")
    assert filtered_response.status_code == 200
    filtered_items = filtered_response.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["artifact_id"] == artifact_id


def test_v2_runs_endpoint_lists_created_runs():
    client = _build_test_client()
    client.post("/api/v2/shortcuts/intel_today", json={"force": False, "origin": "test"})
    response = client.get("/api/v2/runs")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["runs"]) >= 1


def test_v2_system_status_shortcut():
    client = _build_test_client()
    response = client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})
    assert response.status_code == 200
    run = response.json()["run"]
    assert run["run_type"] == "system_run"
    assert run["owner_agent"] == "system"
    assert run["state"] == "completed"
    assert "系统状态" in run["status_message"]
    assert len(run["artifacts"]) == 1
    assert run["artifacts"][0].startswith("artifact-")


def test_v2_db_status_shortcut():
    client = _build_test_client()
    response = client.post("/api/v2/shortcuts/db_status", json={"origin": "test"})
    assert response.status_code == 200
    run = response.json()["run"]
    assert run["run_type"] == "system_run"
    assert run["owner_agent"] == "data_analyst"
    assert run["state"] == "completed"
    assert "设计主库" in run["status_message"]
