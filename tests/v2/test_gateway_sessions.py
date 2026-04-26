from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_session_lease_flow():
    client = TestClient(create_app())
    open_resp = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "alice",
            "client_type": "web",
            "client_id": "web-main",
            "lease_seconds": 60,
        },
    )
    assert open_resp.status_code == 200
    session = open_resp.json()["session"]
    session_id = session["session_id"]

    get_resp = client.get(f"/api/v2/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["profile_id"] == "alice"

    heartbeat_resp = client.post(
        f"/api/v2/sessions/{session_id}/heartbeat",
        json={"lease_seconds": 90},
    )
    assert heartbeat_resp.status_code == 200
    assert heartbeat_resp.json()["session"]["status"] == "active"

    list_resp = client.get("/api/v2/sessions?profile_id=alice")
    assert list_resp.status_code == 200
    assert any(item["session_id"] == session_id for item in list_resp.json()["items"])

    release_resp = client.post(f"/api/v2/sessions/{session_id}/release?reason=logout")
    assert release_resp.status_code == 200
    assert release_resp.json()["session"]["status"] == "released"

    events_resp = client.get(f"/api/v2/sessions/{session_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    event_types = [item["event_type"] for item in events]
    assert "session_opened" in event_types
    assert "session_heartbeat" in event_types
    assert "session_released" in event_types
    assert all(item["event_id"].startswith("sevt-") for item in events)

    audit_resp = client.get("/api/v2/sessions/audit/events?source=session&operation=session.heartbeat")
    assert audit_resp.status_code == 200
    audit_items = audit_resp.json()["items"]
    assert any(item["event_type"] == "session_heartbeat" for item in audit_items)

    export_resp = client.get("/api/v2/sessions/audit/export?source=session")
    assert export_resp.status_code == 200
    exported = export_resp.json()
    assert exported["summary"]["total"] >= 3


def test_gateway_session_writer_conflict_and_handover():
    client = TestClient(create_app())
    open_writer_1 = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "writer_team",
            "client_type": "web",
            "client_id": "web-writer",
            "access_mode": "writer",
            "lease_seconds": 60,
        },
    )
    assert open_writer_1.status_code == 200
    s1 = open_writer_1.json()["session"]["session_id"]

    conflict_resp = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "writer_team",
            "client_type": "desktop",
            "client_id": "desktop-writer",
            "access_mode": "writer",
            "lease_seconds": 60,
        },
    )
    assert conflict_resp.status_code == 409

    handover_resp = client.post(
        "/api/v2/sessions/leases",
        json={
            "profile_id": "writer_team",
            "client_type": "desktop",
            "client_id": "desktop-writer",
            "access_mode": "writer",
            "allow_handover": True,
            "lease_seconds": 60,
        },
    )
    assert handover_resp.status_code == 200
    s2 = handover_resp.json()["session"]["session_id"]
    assert s1 != s2

    old_session_resp = client.get(f"/api/v2/sessions/{s1}")
    assert old_session_resp.status_code == 200
    assert old_session_resp.json()["status"] == "released"

    handover_audit_resp = client.get("/api/v2/sessions/audit/events?operation=session.open.handover")
    assert handover_audit_resp.status_code == 200
    assert any(item["event_type"] == "session_handover" for item in handover_audit_resp.json()["items"])
