import time

from fastapi.testclient import TestClient

from quantamind_v2.contracts.run import RunType
from quantamind_v2.core.gateway.app import create_app
from quantamind_v2.shortcuts.registry import ShortcutDefinition, ShortcutRegistry


def _ok(name: str):
    def _handler(force: bool = False):
        return {
            "status": "ok",
            "summary": f"{name} ok",
            "report": {"report_id": f"{name}-report"},
            "force": force,
        }

    return _handler


def _fail(force: bool = False):
    raise RuntimeError("db down")


def _build_client(*, fail_db: bool = False):
    registry = ShortcutRegistry()
    registry.register(
        ShortcutDefinition(
            name="system_status",
            description="system",
            handler=_ok("system_status"),
            triggers=["系统状态"],
            run_type=RunType.SYSTEM,
            owner_agent="system",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="db_status",
            description="db",
            handler=_fail if fail_db else _ok("db_status"),
            triggers=["数据库状态"],
            run_type=RunType.SYSTEM,
            owner_agent="data_analyst",
        )
    )
    registry.register(
        ShortcutDefinition(
            name="intel_today",
            description="intel",
            handler=_ok("intel_today"),
            triggers=["今天情报"],
            run_type=RunType.DIGEST,
            owner_agent="intel_officer",
        )
    )
    return TestClient(create_app(shortcut_registry=registry))


def _wait_for_task(client: TestClient, task_id: str, timeout_seconds: float = 3.0):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/api/v2/tasks/{task_id}")
        assert response.status_code == 200
        task = response.json()
        if task["state"] in {"completed", "failed", "cancelled", "timeout"}:
            return task
        time.sleep(0.03)
    return client.get(f"/api/v2/tasks/{task_id}").json()


def test_v2_pipeline_templates_and_execute_success():
    client = _build_client()

    templates_response = client.get("/api/v2/pipelines/templates")
    assert templates_response.status_code == 200
    templates = templates_response.json()["items"]
    assert any(item["template"] == "standard_daily_ops" for item in templates)

    execute_response = client.post(
        "/api/v2/pipelines/execute",
        json={"template": "standard_daily_ops", "origin": "test", "background": True},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()
    run_id = payload["run"]["run_id"]
    task_id = payload["task"]["task_id"]

    done = _wait_for_task(client, task_id)
    assert done["state"] == "completed"

    run_resp = client.get(f"/api/v2/runs/{run_id}")
    assert run_resp.status_code == 200
    run = run_resp.json()
    assert run["run_type"] == "pipeline_run"
    assert run["state"] == "completed"
    assert len(run["artifacts"]) >= 1

    artifact_resp = client.get(f"/api/v2/artifacts/{run['artifacts'][0]}")
    assert artifact_resp.status_code == 200
    assert artifact_resp.json()["artifact_type"] == "pipeline_report"

    runs_resp = client.get("/api/v2/runs")
    assert runs_resp.status_code == 200
    children = [item for item in runs_resp.json()["runs"] if item.get("parent_run_id") == run_id]
    assert len(children) == 3


def test_v2_pipeline_execute_failure_propagates():
    client = _build_client(fail_db=True)
    execute_response = client.post(
        "/api/v2/pipelines/execute",
        json={"template": "standard_daily_ops", "origin": "test", "background": True},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()
    run_id = payload["run"]["run_id"]
    task_id = payload["task"]["task_id"]

    done = _wait_for_task(client, task_id)
    assert done["state"] == "failed"

    run_resp = client.get(f"/api/v2/runs/{run_id}")
    assert run_resp.status_code == 200
    run = run_resp.json()
    assert run["state"] == "failed"
    assert len(run["artifacts"]) >= 1
