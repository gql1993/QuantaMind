from quantamind_v2.core.sessions import SessionPresenceManager
from quantamind_v2.core.sessions import SessionConflictError


def test_session_presence_open_heartbeat_release():
    manager = SessionPresenceManager()
    session = manager.open_session(
        profile_id="alice",
        client_type="web",
        client_id="web-1",
        lease_seconds=60,
    )
    assert session.profile_id == "alice"
    assert session.status == "active"
    refreshed = manager.heartbeat(session.session_id, lease_seconds=120)
    assert refreshed.status == "active"
    released = manager.release(session.session_id, reason="switch_device")
    assert released.status == "released"
    assert released.metadata["release_reason"] == "switch_device"


def test_session_presence_list_filters_expired():
    manager = SessionPresenceManager()
    active = manager.open_session(profile_id="default", client_type="web", client_id="w1", lease_seconds=60)
    expired = manager.open_session(profile_id="default", client_type="desktop", client_id="d1", lease_seconds=1)
    manager._items[expired.session_id].lease_until = "2000-01-01T00:00:00Z"  # noqa: SLF001
    visible = manager.list_sessions(profile_id="default", include_expired=False)
    assert any(item.session_id == active.session_id for item in visible)
    assert all(item.session_id != expired.session_id for item in visible)
    all_items = manager.list_sessions(profile_id="default", include_expired=True)
    assert any(item.session_id == expired.session_id for item in all_items)


def test_session_presence_single_writer_conflict_and_handover():
    manager = SessionPresenceManager()
    writer1 = manager.open_session(
        profile_id="teamA",
        client_type="web",
        client_id="web-writer",
        access_mode="writer",
        lease_seconds=60,
    )
    assert writer1.access_mode == "writer"
    try:
        manager.open_session(
            profile_id="teamA",
            client_type="desktop",
            client_id="desktop-writer",
            access_mode="writer",
            lease_seconds=60,
        )
        raised = False
    except SessionConflictError:
        raised = True
    assert raised is True

    writer2 = manager.open_session(
        profile_id="teamA",
        client_type="desktop",
        client_id="desktop-writer",
        access_mode="writer",
        allow_handover=True,
        lease_seconds=60,
    )
    assert writer2.access_mode == "writer"
    old = manager.get_session(writer1.session_id)
    assert old is not None
    assert old.status == "released"
