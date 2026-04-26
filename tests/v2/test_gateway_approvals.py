from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _fake_system_status(force: bool = False):
    return {
        "status": "ok",
        "summary": "system status ok",
        "payload": {"gateway": {"status": "ok"}},
        "force": force,
    }


def _build_test_client():
    registry = ShortcutRegistry()
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


def test_v2_gateway_approval_create_list_and_get():
    client = _build_test_client()
    run_response = client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})
    assert run_response.status_code == 200
    run_id = run_response.json()["run"]["run_id"]

    create_response = client.post(
        "/api/v2/approvals",
        json={
            "run_id": run_id,
            "approval_type": "external_delivery",
            "summary": "发送飞书日报需要审批",
            "details": {"channel": "feishu"},
        },
    )
    assert create_response.status_code == 200
    approval = create_response.json()["approval"]
    assert approval["status"] == "pending"
    assert approval["run_id"] == run_id

    list_response = client.get("/api/v2/approvals?status=pending")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(item["approval_id"] == approval["approval_id"] for item in items)

    get_response = client.get(f"/api/v2/approvals/{approval['approval_id']}")
    assert get_response.status_code == 200
    got = get_response.json()
    assert got["summary"] == "发送飞书日报需要审批"
    assert got["details"]["channel"] == "feishu"


def test_v2_gateway_approval_approve_updates_run_event():
    client = _build_test_client()
    run_response = client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})
    run_id = run_response.json()["run"]["run_id"]
    create_response = client.post(
        "/api/v2/approvals",
        json={
            "run_id": run_id,
            "approval_type": "mes_operation",
            "summary": "执行关键 MES 操作",
        },
    )
    approval_id = create_response.json()["approval"]["approval_id"]

    approve_response = client.post(
        f"/api/v2/approvals/{approval_id}/approve",
        json={"reviewer": "alice", "comment": "ok"},
    )
    assert approve_response.status_code == 200
    approval = approve_response.json()["approval"]
    assert approval["status"] == "approved"
    assert approval["reviewer"] == "alice"
    assert approval["resolved_at"] is not None

    run_response = client.get(f"/api/v2/runs/{run_id}")
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["stage"] == "approval_approved"
    assert run["metadata"]["last_approval_id"] == approval_id

    events_response = client.get(f"/api/v2/runs/{run_id}/events")
    assert events_response.status_code == 200
    event_types = [item["event_type"] for item in events_response.json()["items"]]
    assert "approval_requested" in event_types
    assert "approval_approved" in event_types


def test_v2_gateway_approval_reject_and_second_resolve_rejected():
    client = _build_test_client()
    run_response = client.post("/api/v2/shortcuts/system_status", json={"origin": "test"})
    run_id = run_response.json()["run"]["run_id"]
    create_response = client.post(
        "/api/v2/approvals",
        json={
            "run_id": run_id,
            "approval_type": "device_command",
            "summary": "下发设备命令",
        },
    )
    approval_id = create_response.json()["approval"]["approval_id"]

    reject_response = client.post(
        f"/api/v2/approvals/{approval_id}/reject",
        json={"reviewer": "bob", "comment": "risk too high"},
    )
    assert reject_response.status_code == 200
    rejected = reject_response.json()["approval"]
    assert rejected["status"] == "rejected"

    run_response = client.get(f"/api/v2/runs/{run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["stage"] == "approval_rejected"

    second_response = client.post(
        f"/api/v2/approvals/{approval_id}/approve",
        json={"reviewer": "carol"},
    )
    assert second_response.status_code == 400
