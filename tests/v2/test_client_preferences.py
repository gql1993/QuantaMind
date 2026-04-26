from quantamind_v2.client.shared import InMemoryClientPreferencesStore


def test_client_preferences_set_shortcuts_and_layouts():
    store = InMemoryClientPreferencesStore()
    prefs = store.set_pinned_shortcuts(profile_id="alice", shortcuts=["intel_today", "system_status", "intel_today"])
    assert prefs.pinned_shortcuts == ["intel_today", "system_status"]
    prefs = store.set_active_layout(profile_id="alice", target="web", layout_id="layout-web-default")
    assert prefs.active_layout_by_target["web"] == "layout-web-default"


def test_client_preferences_sync_layout_between_targets():
    store = InMemoryClientPreferencesStore()
    store.set_active_layout(profile_id="bob", target="web", layout_id="layout-web-custom-1")
    synced = store.sync_active_layout(profile_id="bob", source_target="web", target="desktop")
    assert synced.active_layout_by_target["desktop"] == "layout-web-custom-1"
