import time

from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def _build_client() -> TestClient:
    return TestClient(create_app())


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


def test_v2_library_upload_creates_import_run_task_and_artifact():
    client = _build_client()
    upload = client.post(
        "/api/v2/library/upload",
        files={"file": ("sample_notes.txt", b"hello\nquantamind\nv2")},
        data={"project_id": "default", "origin": "test"},
    )
    assert upload.status_code == 200
    payload = upload.json()
    run = payload["run"]
    task = payload["task"]
    uploaded_file = payload["file"]

    assert run["run_type"] == "import_run"
    assert run["state"] == "running"
    assert task["task_name"].startswith("library_ingest:")
    assert task["run_id"] == run["run_id"]
    assert uploaded_file["run_id"] == run["run_id"]
    assert uploaded_file["task_id"] == task["task_id"]

    done = _wait_for_task(client, task["task_id"])
    assert done["state"] == "completed"

    run_after = client.get(f"/api/v2/runs/{run['run_id']}")
    assert run_after.status_code == 200
    run_data = run_after.json()
    assert run_data["state"] == "completed"
    assert run_data["stage"] in {"import_indexed", "worker_completed"}
    assert len(run_data["artifacts"]) == 1

    artifact_id = run_data["artifacts"][0]
    artifact = client.get(f"/api/v2/artifacts/{artifact_id}")
    assert artifact.status_code == 200
    artifact_data = artifact.json()
    assert artifact_data["artifact_type"] == "library_ingest_report"
    assert artifact_data["payload"]["file"]["filename"] == "sample_notes.txt"


def test_v2_library_files_stats_and_search():
    client = _build_client()
    client.post(
        "/api/v2/library/upload",
        files={"file": ("chip_design.csv", b"freq,anharm\n5.0,-0.25\n")},
        data={"project_id": "default", "origin": "test"},
    )
    client.post(
        "/api/v2/library/upload",
        files={"file": ("readme.md", b"# project notes\n")},
        data={"project_id": "default", "origin": "test"},
    )

    # allow async workers to settle
    all_tasks = client.get("/api/v2/tasks").json()["items"]
    for item in all_tasks:
        _wait_for_task(client, item["task_id"])

    files_resp = client.get("/api/v2/library/files")
    assert files_resp.status_code == 200
    files_payload = files_resp.json()
    assert files_payload["count"] >= 2
    names = {item["filename"] for item in files_payload["files"]}
    assert "chip_design.csv" in names
    assert "readme.md" in names

    search_resp = client.get("/api/v2/library/files?search=chip_design")
    assert search_resp.status_code == 200
    search_files = search_resp.json()["files"]
    assert len(search_files) == 1
    assert search_files[0]["filename"] == "chip_design.csv"

    stats_resp = client.get("/api/v2/library/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_files"] >= 2
    assert stats["parsed"] >= 2
