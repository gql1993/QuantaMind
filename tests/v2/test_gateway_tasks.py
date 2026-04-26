import time

from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _fake_intel_today(force: bool = False):
    return {
        "status": "sent",
        "summary": "fake intel digest sent",
        "report": {"report_id": "intel-task-001"},
        "force": force,
    }


def _slow_shortcut(force: bool = False):
    time.sleep(0.3)
    return {
        "status": "ok",
        "summary": "slow shortcut finished",
        "report": {"report_id": "slow-task-001"},
        "force": force,
    }


def _failing_shortcut(force: bool = False):
    raise RuntimeError("shortcut failed")


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
            name="slow_shortcut",
            description="slow shortcut",
            handler=_slow_shortcut,
            triggers=["慢任务"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="failing_shortcut",
            description="failing shortcut",
            handler=_failing_shortcut,
            triggers=["失败任务"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    return TestClient(create_app(shortcut_registry=registry))


def _wait_for_task(client: TestClient, task_id: str, timeout_seconds: float = 2.0):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/api/v2/tasks/{task_id}")
        assert response.status_code == 200
        task = response.json()
        if task["state"] in {"completed", "failed", "cancelled", "timeout"}:
            return task
        time.sleep(0.03)
    return client.get(f"/api/v2/tasks/{task_id}").json()


def test_v2_gateway_background_shortcut_task_completes():
    client = _build_test_client()
    response = client.post("/api/v2/tasks/shortcuts/intel_today", json={"origin": "test"})
    assert response.status_code == 200
    task_id = response.json()["task"]["task_id"]

    done = _wait_for_task(client, task_id)
    assert done["state"] == "completed"

    list_response = client.get("/api/v2/tasks")
    assert list_response.status_code == 200
    ids = {item["task_id"] for item in list_response.json()["items"]}
    assert task_id in ids


def test_v2_gateway_background_task_retry():
    client = _build_test_client()
    response = client.post(
        "/api/v2/tasks/shortcuts/failing_shortcut",
        json={"origin": "test", "max_retries": 1},
    )
    assert response.status_code == 200
    first_task_id = response.json()["task"]["task_id"]
    first_done = _wait_for_task(client, first_task_id)
    assert first_done["state"] == "failed"

    retry_response = client.post(f"/api/v2/tasks/{first_task_id}/retry")
    assert retry_response.status_code == 200
    retry_task = retry_response.json()["task"]
    assert retry_task["attempt"] == 2
    assert retry_task["parent_task_id"] == first_task_id


def test_v2_gateway_background_task_cancel():
    client = _build_test_client()
    response = client.post("/api/v2/tasks/shortcuts/slow_shortcut", json={"origin": "test"})
    assert response.status_code == 200
    task_id = response.json()["task"]["task_id"]

    cancel_response = client.post(f"/api/v2/tasks/{task_id}/cancel")
    assert cancel_response.status_code == 200

    done = _wait_for_task(client, task_id)
    assert done["state"] in {"cancelled", "completed"}
