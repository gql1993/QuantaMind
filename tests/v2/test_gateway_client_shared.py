from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _build_client() -> TestClient:
    registry = ShortcutRegistry()

    def _system(force: bool = False) -> dict:
        return {
            "status": "ok",
            "summary": "system ok",
            "report": {"report_id": "shared-state-report"},
            "force": force,
        }

    registry.register(
        ShortcutDefinition(
            name="system_status",
            description="system status",
            handler=_system,
            triggers=["系统状态"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    return TestClient(create_app(shortcut_registry=registry))


def test_gateway_client_shared_state_snapshot():
    client = _build_client()
    run_resp = client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})
    assert run_resp.status_code == 200

    state_resp = client.get("/api/v2/client/shared/state")
    assert state_resp.status_code == 200
    state = state_resp.json()["state"]
    assert "runs" in state
    assert "tasks" in state
    assert "artifacts" in state
    assert state["summary"]["run_total"] >= 1
    assert state["summary"]["artifact_total"] >= 1
