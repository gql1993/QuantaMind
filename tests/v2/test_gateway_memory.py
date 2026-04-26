from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _build_client() -> TestClient:
    registry = ShortcutRegistry()

    def _ok(force: bool = False) -> dict:
        return {
            "status": "ok",
            "summary": "system ok",
            "report": {"report_id": "system-report-001"},
            "force": force,
        }

    registry.register(
        ShortcutDefinition(
            name="system_status",
            description="system",
            handler=_ok,
            triggers=["系统状态"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    return TestClient(create_app(shortcut_registry=registry))


def test_gateway_memory_project_note_and_query():
    client = _build_client()
    post_resp = client.post(
        "/api/v2/memory/projects/demo/notes",
        json={"content": "first note", "source": "test"},
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["note"]["project_id"] == "demo"
    get_resp = client.get("/api/v2/memory/projects/demo")
    assert get_resp.status_code == 200
    assert get_resp.json()["count"] >= 1


def test_gateway_memory_sync_run_and_artifact():
    client = _build_client()
    shortcut_resp = client.post("/api/v2/shortcuts/system_status", json={"force": False, "origin": "test"})
    assert shortcut_resp.status_code == 200
    run = shortcut_resp.json()["run"]
    run_id = run["run_id"]
    assert run["artifacts"]
    artifact_id = run["artifacts"][0]

    sync_run_resp = client.post(f"/api/v2/memory/sync/runs/{run_id}")
    assert sync_run_resp.status_code == 200
    run_memory_resp = client.get(f"/api/v2/memory/runs/{run_id}")
    assert run_memory_resp.status_code == 200
    assert run_memory_resp.json()["run_id"] == run_id

    sync_artifact_resp = client.post(f"/api/v2/memory/sync/artifacts/{artifact_id}")
    assert sync_artifact_resp.status_code == 200
    artifact_memory_resp = client.get(f"/api/v2/memory/artifacts/{artifact_id}")
    assert artifact_memory_resp.status_code == 200
    assert artifact_memory_resp.json()["artifact_id"] == artifact_id

    list_resp = client.get(f"/api/v2/memory/artifacts?run_id={run_id}")
    assert list_resp.status_code == 200
    assert any(item["artifact_id"] == artifact_id for item in list_resp.json()["items"])
