from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _fake_intel_today(force: bool = False):
    return {
        "status": "sent",
        "summary": "fake intel digest sent",
        "report": {"report_id": "intel-console-001"},
        "force": force,
    }


def _fake_system_status(force: bool = False):
    return {
        "status": "ok",
        "summary": "系统状态：ok\n降级模式：否\n会话数：1",
        "payload": {"gateway": {"status": "ok", "degraded": False}},
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
    return TestClient(create_app(shortcut_registry=registry))


def test_v2_gateway_lists_shortcuts_for_launcher():
    client = _build_test_client()
    response = client.get("/api/v2/shortcuts")
    assert response.status_code == 200
    items = response.json()["items"]
    names = {item["name"] for item in items}
    assert "intel_today" in names
    assert "system_status" in names


def test_v2_gateway_exposes_run_events_and_snapshot():
    client = _build_test_client()
    run_response = client.post("/api/v2/shortcuts/intel_today", json={"origin": "test"})
    assert run_response.status_code == 200
    run = run_response.json()["run"]

    events_response = client.get(f"/api/v2/runs/{run['run_id']}/events")
    assert events_response.status_code == 200
    events = events_response.json()["items"]
    assert len(events) >= 3
    event_types = {event["event_type"] for event in events}
    assert "run_created" in event_types
    assert "run_transitioned" in event_types
    assert "artifact_attached" in event_types

    snapshot_response = client.get(f"/api/v2/runs/{run['run_id']}/snapshot")
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()["snapshot"]
    assert snapshot["run_id"] == run["run_id"]
    assert snapshot["state"] == "completed"
    assert "intel-console-001" in snapshot["artifacts"]


def test_v2_gateway_console_runs_supports_state_filter():
    client = _build_test_client()
    client.post("/api/v2/shortcuts/intel_today", json={"origin": "test"})
    client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})

    response = client.get("/api/v2/console/runs?state=completed")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 2
    assert all(item["run"]["state"] == "completed" for item in items)
    assert all(item["event_count"] >= 3 for item in items)
    assert all(item["artifact_count"] >= 1 for item in items)
