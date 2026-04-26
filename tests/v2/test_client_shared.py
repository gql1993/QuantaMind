from quantamind_v2.client.shared import build_shared_client_state


def test_build_shared_client_state_normalizes_counts():
    state = build_shared_client_state(
        runs=[
            {
                "run_id": "run-1",
                "run_type": "system_run",
                "state": "completed",
                "stage": "done",
                "owner_agent": "system",
                "status_message": "ok",
                "artifacts": ["artifact-1"],
                "updated_at": "2026-01-01T00:00:00Z",
                "metadata": {},
            }
        ],
        tasks=[
            {
                "task_id": "task-1",
                "task_name": "demo",
                "run_id": "run-1",
                "state": "running",
                "attempt": 1,
                "max_retries": 0,
                "budget_seconds": 2.0,
                "updated_at": "2026-01-01T00:00:00Z",
                "error": "",
                "result": None,
            }
        ],
        artifacts=[
            {
                "artifact_id": "artifact-1",
                "run_id": "run-1",
                "artifact_type": "system_diagnosis",
                "title": "diag",
                "summary": "ok",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        run_event_counts={"run-1": 3},
    )
    payload = state.to_dict()
    assert payload["summary"]["run_total"] == 1
    assert payload["summary"]["task_running"] == 1
    assert payload["summary"]["artifact_total"] == 1
    assert payload["runs"][0]["event_count"] == 3
