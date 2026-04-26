from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_workspace_layout_crud_and_activate():
    client = TestClient(create_app())
    create_resp = client.post(
        "/api/v2/client/workspace/layouts",
        json={
            "layout_id": "layout-web-custom-001",
            "name": "Custom Layout",
            "target": "web",
            "panels": [
                {"panel_id": "run-console", "title": "Run Console", "order": 1},
                {"panel_id": "task-center", "title": "Task Center", "order": 2},
            ],
        },
    )
    assert create_resp.status_code == 200
    get_resp = client.get("/api/v2/client/workspace/layouts/layout-web-custom-001")
    assert get_resp.status_code == 200
    activate_resp = client.post("/api/v2/client/workspace/layouts/layout-web-custom-001/activate?target=web&profile_id=alice")
    assert activate_resp.status_code == 200
    active_resp = client.get("/api/v2/client/workspace/active-layout?target=web&profile_id=alice")
    assert active_resp.status_code == 200
    assert active_resp.json()["layout_id"] == "layout-web-custom-001"
    prefs_resp = client.get("/api/v2/client/preferences/alice")
    assert prefs_resp.status_code == 200
    assert prefs_resp.json()["active_layout_by_target"]["web"] == "layout-web-custom-001"


def test_gateway_workspace_snapshot_returns_layout_and_state():
    client = TestClient(create_app())
    session_resp = client.post(
        "/api/v2/sessions/leases",
        json={"profile_id": "default", "client_type": "web", "client_id": "web-main", "lease_seconds": 60},
    )
    assert session_resp.status_code == 200
    response = client.get("/api/v2/client/workspace/snapshot?target=web")
    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == "web"
    assert "layout" in payload
    assert "state" in payload
    assert "summary" in payload["state"]
    assert "latest_recovery_point" in payload
    assert "session_presence" in payload
    assert payload["session_presence"]["active_total"] >= 1
    assert payload["session_presence"]["by_client_type"]["web"] >= 1


def test_gateway_client_preferences_shortcuts_and_sync_layouts():
    client = TestClient(create_app())
    create_resp = client.post(
        "/api/v2/client/workspace/layouts",
        json={
            "layout_id": "layout-web-sync-001",
            "name": "Sync Source",
            "target": "web",
            "panels": [{"panel_id": "run-console", "title": "Run Console", "order": 1}],
        },
    )
    assert create_resp.status_code == 200
    activate_resp = client.post("/api/v2/client/workspace/layouts/layout-web-sync-001/activate?target=web&profile_id=sync_user")
    assert activate_resp.status_code == 200
    shortcuts_resp = client.post(
        "/api/v2/client/preferences/sync_user/shortcuts",
        json={"pinned_shortcuts": ["intel_today", "system_status", "intel_today"]},
    )
    assert shortcuts_resp.status_code == 200
    sync_resp = client.post(
        "/api/v2/client/preferences/sync_user/sync-layouts",
        json={"source_target": "web", "target": "desktop"},
    )
    assert sync_resp.status_code == 200
    prefs = client.get("/api/v2/client/preferences/sync_user").json()
    assert prefs["pinned_shortcuts"] == ["intel_today", "system_status"]
    assert prefs["active_layout_by_target"]["desktop"] == "layout-web-sync-001"


def test_gateway_workspace_recovery_points_flow():
    client = TestClient(create_app())
    session_resp = client.post(
        "/api/v2/sessions/leases",
        json={"profile_id": "recover_user", "client_type": "web", "client_id": "web-recover", "lease_seconds": 60},
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session"]["session_id"]
    create_layout_resp = client.post(
        "/api/v2/client/workspace/layouts",
        json={
            "layout_id": "layout-web-recovery-001",
            "name": "Recovery Layout",
            "target": "web",
            "panels": [{"panel_id": "run-console", "title": "Run Console", "order": 1}],
        },
    )
    assert create_layout_resp.status_code == 200
    activate_resp = client.post(
        f"/api/v2/client/workspace/layouts/layout-web-recovery-001/activate?target=web&profile_id=recover_user&session_id={session_id}"
    )
    assert activate_resp.status_code == 200
    create_point_resp = client.post(
        f"/api/v2/client/workspace/recovery-points?target=web&profile_id=recover_user&session_id={session_id}",
        json={"run_id": "run-recovery-1", "note": "before switching context"},
    )
    assert create_point_resp.status_code == 200
    point_id = create_point_resp.json()["recovery_point"]["point_id"]
    list_resp = client.get("/api/v2/client/workspace/recovery-points?target=web&profile_id=recover_user")
    assert list_resp.status_code == 200
    assert any(item["point_id"] == point_id for item in list_resp.json()["items"])
    latest_resp = client.get("/api/v2/client/workspace/recovery-points/latest?target=web&profile_id=recover_user")
    assert latest_resp.status_code == 200
    assert latest_resp.json()["point_id"] == point_id
    restore_resp = client.post(
        f"/api/v2/client/workspace/recovery-points/{point_id}/activate?profile_id=recover_user&session_id={session_id}"
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["layout"]["layout_id"] == "layout-web-recovery-001"
    audit_resp = client.get(f"/api/v2/sessions/{session_id}/events?source=workspace")
    assert audit_resp.status_code == 200
    operations = {item["operation"] for item in audit_resp.json()["items"]}
    assert "workspace.layout.activate" in operations
    assert "workspace.recovery.create" in operations
    assert "workspace.recovery.activate" in operations


def test_gateway_workspace_writer_lock_blocks_non_writer_mutation():
    client = TestClient(create_app())
    create_layout_resp = client.post(
        "/api/v2/client/workspace/layouts",
        json={
            "layout_id": "layout-web-writer-lock-001",
            "name": "Writer Lock Layout",
            "target": "web",
            "panels": [{"panel_id": "run-console", "title": "Run Console", "order": 1}],
        },
    )
    assert create_layout_resp.status_code == 200

    writer_resp = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "lock_user",
            "client_type": "web",
            "client_id": "writer-client",
            "access_mode": "writer",
            "lease_seconds": 60,
        },
    )
    assert writer_resp.status_code == 200
    writer_session_id = writer_resp.json()["session"]["session_id"]

    reader_resp = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "lock_user",
            "client_type": "desktop",
            "client_id": "reader-client",
            "access_mode": "reader",
            "lease_seconds": 60,
        },
    )
    assert reader_resp.status_code == 200
    reader_session_id = reader_resp.json()["session"]["session_id"]

    missing_session_resp = client.post(
        "/api/v2/client/workspace/layouts/layout-web-writer-lock-001/activate?target=web&profile_id=lock_user"
    )
    assert missing_session_resp.status_code == 409

    reader_activate_resp = client.post(
        "/api/v2/client/workspace/layouts/layout-web-writer-lock-001/activate"
        f"?target=web&profile_id=lock_user&session_id={reader_session_id}"
    )
    assert reader_activate_resp.status_code == 409

    writer_activate_resp = client.post(
        "/api/v2/client/workspace/layouts/layout-web-writer-lock-001/activate"
        f"?target=web&profile_id=lock_user&session_id={writer_session_id}"
    )
    assert writer_activate_resp.status_code == 200

    audit_resp = client.get(f"/api/v2/sessions/{writer_session_id}/events?operation=workspace.write.conflict")
    assert audit_resp.status_code == 200
    conflict_types = [item["event_type"] for item in audit_resp.json()["items"]]
    assert "workspace_write_conflict" in conflict_types
