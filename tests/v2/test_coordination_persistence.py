from pathlib import Path

from quantamind_v2.core.coordination.persistence import (
    DualWriteCoordinationAuditStore,
    DualWriteCoordinationPolicyStore,
    FileBackedCoordinationAuditStore,
    FileBackedCoordinationPolicyStore,
    SQLiteCoordinationAuditStore,
    SQLiteCoordinationPolicyStore,
)


def test_file_backed_coordination_audit_store_cross_instance_visibility(tmp_path: Path):
    path = tmp_path / "coordination_audit.jsonl"
    writer = FileBackedCoordinationAuditStore(path, max_items=100)
    reader = FileBackedCoordinationAuditStore(path, max_items=100)
    writer.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="conflict exists",
    )
    items = reader.list_events(profile_id="alice")
    assert len(items) == 1
    assert items[0].strategy == "queue"
    assert items[0].event_id.startswith("caev-")


def test_file_backed_coordination_policy_store_cross_instance_visibility(tmp_path: Path):
    path = tmp_path / "coordination_policy.json"
    writer = FileBackedCoordinationPolicyStore(path)
    reader = FileBackedCoordinationPolicyStore(path)
    writer.set_strategy(profile_id="alice", strategy="reject", source="test")
    strategy = reader.get_strategy("alice")
    assert strategy == "reject"


def test_file_backed_coordination_audit_store_startup_recovery_and_compaction(tmp_path: Path):
    path = tmp_path / "coordination_audit.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"event_id":"ok-1","event_type":"coordination_conflict_decided","profile_id":"alice","strategy":"queue","outcome":"queued","reason":"r1","payload":{},"created_at":"2026-01-01T00:00:00Z"}',
                "not-a-json-line",
                '{"event_id":"ok-2","event_type":"coordination_conflict_decided","profile_id":"alice","strategy":"reject","outcome":"rejected","reason":"r2","payload":{},"created_at":"2026-01-01T00:00:01Z"}',
            ]
        ),
        encoding="utf-8",
    )
    store = FileBackedCoordinationAuditStore(path, max_items=100)
    health = store.get_health_report()
    assert health["status"] == "recovered"
    assert health["last_backup_file"] is not None
    items = store.list_events(profile_id="alice", limit=10)
    assert len(items) == 2
    # File has been rewritten without broken lines.
    assert "not-a-json-line" not in path.read_text(encoding="utf-8")


def test_file_backed_coordination_policy_store_startup_recovery(tmp_path: Path):
    path = tmp_path / "coordination_policy.json"
    path.write_text("{broken-json", encoding="utf-8")
    store = FileBackedCoordinationPolicyStore(path)
    health = store.get_health_report()
    assert health["status"] == "recovered"
    assert health["last_backup_file"] is not None
    assert store.get_strategy("alice") is None


def test_file_backed_coordination_audit_store_rotates_by_size_and_writes_archive_index(tmp_path: Path):
    path = tmp_path / "coordination_audit.jsonl"
    archive_index = tmp_path / "coordination_audit_archives.json"
    store = FileBackedCoordinationAuditStore(
        path,
        max_items=100,
        rotate_max_bytes=1,
        rotate_interval_seconds=3600,
        archive_index_path=archive_index,
    )
    store.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="rotation-size",
    )
    archives = store.list_archives(limit=10)
    assert len(archives) >= 1
    assert any(item["reason"] == "size" for item in archives)


def test_file_backed_coordination_audit_store_rotates_by_time(tmp_path: Path):
    path = tmp_path / "coordination_audit.jsonl"
    store = FileBackedCoordinationAuditStore(
        path,
        max_items=100,
        rotate_max_bytes=10_000,
        rotate_interval_seconds=3600,
    )
    store._last_rotation_epoch = 0  # noqa: SLF001
    store.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="rotation-time",
    )
    archives = store.list_archives(limit=10)
    assert len(archives) >= 1
    assert any(item["reason"] == "time" for item in archives)


def test_sqlite_coordination_stores_basic_flow(tmp_path: Path):
    db_path = tmp_path / "coordination.db"
    audit = SQLiteCoordinationAuditStore(db_path)
    policy = SQLiteCoordinationPolicyStore(db_path)
    audit.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="sqlite",
    )
    rows = audit.list_events(profile_id="alice")
    assert len(rows) == 1
    assert rows[0].strategy == "queue"
    record = policy.set_strategy(profile_id="alice", strategy="reject", source="test")
    assert record["strategy"] == "reject"
    assert policy.get_strategy("alice") == "reject"


def test_dual_write_coordination_stores_write_secondary(tmp_path: Path):
    state_dir = tmp_path / "coordination-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(primary_audit, secondary_audit, enabled=True)
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="dual-write",
    )
    secondary_rows = secondary_audit.list_events(profile_id="alice")
    assert len(secondary_rows) == 1

    primary_policy = FileBackedCoordinationPolicyStore(state_dir / "policy.json")
    secondary_policy = SQLiteCoordinationPolicyStore(db_path)
    dual_policy = DualWriteCoordinationPolicyStore(primary_policy, secondary_policy, enabled=True)
    dual_policy.set_strategy(profile_id="alice", strategy="degrade_single_agent", source="test")
    assert secondary_policy.get_strategy("alice") == "degrade_single_agent"


def test_dual_write_consistency_reports_are_consistent(tmp_path: Path):
    state_dir = tmp_path / "coordination-consistency"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(primary_audit, secondary_audit, enabled=True)
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="consistent",
    )
    audit_report = dual_audit.compare_consistency(profile_id="alice", window_limit=20)
    assert audit_report["status"] == "consistent"
    assert audit_report["difference_count"] == 0

    primary_policy = FileBackedCoordinationPolicyStore(state_dir / "policy.json")
    secondary_policy = SQLiteCoordinationPolicyStore(db_path)
    dual_policy = DualWriteCoordinationPolicyStore(primary_policy, secondary_policy, enabled=True)
    dual_policy.set_strategy(profile_id="alice", strategy="queue", source="test")
    policy_report = dual_policy.compare_consistency(limit=20)
    assert policy_report["status"] == "consistent"
    assert policy_report["difference_count"] == 0


def test_dual_write_read_prefer_sqlite_with_fallback_drill(tmp_path: Path):
    state_dir = tmp_path / "coordination-cutover"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(
        primary_audit,
        secondary_audit,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
    )
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="drill",
    )
    items = dual_audit.list_events(profile_id="alice", limit=10)
    assert len(items) == 1
    drill_ok = dual_audit.drill_read(profile_id="alice", window_limit=10)
    assert drill_ok["status"] == "ok"
    assert drill_ok["selected_backend"] == "secondary_sqlite"
    drill_degraded = dual_audit.drill_read(
        profile_id="alice",
        window_limit=10,
        simulate_secondary_failure=True,
    )
    assert drill_degraded["status"] == "degraded"
    assert drill_degraded["selected_backend"] == "primary_file_fallback"
    assert drill_degraded["fallback_used"] is True

    primary_policy = FileBackedCoordinationPolicyStore(state_dir / "policy.json")
    secondary_policy = SQLiteCoordinationPolicyStore(db_path)
    dual_policy = DualWriteCoordinationPolicyStore(
        primary_policy,
        secondary_policy,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
    )
    dual_policy.set_strategy(profile_id="alice", strategy="queue", source="test")
    assert dual_policy.get_strategy("alice") == "queue"
    policy_ok = dual_policy.drill_read(profile_id="alice")
    assert policy_ok["status"] == "ok"
    assert policy_ok["selected_backend"] == "secondary_sqlite"
    policy_degraded = dual_policy.drill_read(profile_id="alice", simulate_secondary_failure=True)
    assert policy_degraded["status"] == "degraded"
    assert policy_degraded["selected_backend"] == "primary_file_fallback"


def test_dual_write_read_gray_release_allowlist_and_rollout(tmp_path: Path):
    state_dir = tmp_path / "coordination-gray"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(
        primary_audit,
        secondary_audit,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
        profile_allowlist=["allow_user"],
        rollout_percentage=50,
    )
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="allow_user",
        strategy="queue",
        outcome="queued",
        reason="allowlist",
    )
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="rollout_user",
        strategy="queue",
        outcome="queued",
        reason="rollout",
    )
    allow_drill = dual_audit.drill_read(profile_id="allow_user", window_limit=10)
    assert allow_drill["selected_backend"] == "secondary_sqlite"
    assert allow_drill["routing_reason"] == "allowlist"
    assert allow_drill["allowlist_hit"] is True

    rollout_drill = dual_audit.drill_read(profile_id="rollout_user", window_limit=10)
    rollout_bucket = int(rollout_drill["rollout_bucket"])
    if rollout_bucket < 50:
        assert rollout_drill["selected_backend"] == "secondary_sqlite"
        assert rollout_drill["routing_reason"] == "rollout_percentage"
    else:
        assert rollout_drill["selected_backend"] == "primary_file"
        assert rollout_drill["routing_reason"] == "rollout_excluded"

    primary_policy = FileBackedCoordinationPolicyStore(state_dir / "policy.json")
    secondary_policy = SQLiteCoordinationPolicyStore(db_path)
    dual_policy = DualWriteCoordinationPolicyStore(
        primary_policy,
        secondary_policy,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
        profile_allowlist=["allow_user"],
        rollout_percentage=50,
    )
    dual_policy.set_strategy(profile_id="allow_user", strategy="queue", source="test")
    dual_policy.set_strategy(profile_id="rollout_user", strategy="reject", source="test")
    allow_policy_drill = dual_policy.drill_read(profile_id="allow_user")
    assert allow_policy_drill["selected_backend"] == "secondary_sqlite"
    assert allow_policy_drill["routing_reason"] == "allowlist"

    rollout_policy_drill = dual_policy.drill_read(profile_id="rollout_user")
    rollout_policy_bucket = int(rollout_policy_drill["rollout_bucket"])
    if rollout_policy_bucket < 50:
        assert rollout_policy_drill["selected_backend"] == "secondary_sqlite"
        assert rollout_policy_drill["routing_reason"] == "rollout_percentage"
    else:
        assert rollout_policy_drill["selected_backend"] == "primary_file"
        assert rollout_policy_drill["routing_reason"] == "rollout_excluded"

    audit_health = dual_audit.get_health_report()
    assert audit_health["read_observability"]["total_reads"] >= 2
    assert audit_health["read_observability"]["tracked_profiles_total"] >= 2
    assert any(item["profile_id"] == "allow_user" for item in audit_health["read_observability"]["profile_hits"])

    policy_health = dual_policy.get_health_report()
    assert policy_health["read_observability"]["total_reads"] >= 2
    assert any(item["profile_id"] == "allow_user" for item in policy_health["read_observability"]["profile_hits"])


def test_dual_write_read_observability_counts_fallback_anomalies(tmp_path: Path):
    state_dir = tmp_path / "coordination-observability"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(
        primary_audit,
        secondary_audit,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
        profile_allowlist=["alice"],
    )
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="alice",
        strategy="queue",
        outcome="queued",
        reason="fallback",
    )
    dual_audit.drill_read(profile_id="alice", window_limit=10, simulate_secondary_failure=True)
    report = dual_audit.get_health_report()["read_observability"]
    assert report["fallback_anomaly_count"] == 1
    assert report["file_reads"] >= 1
    assert any(
        item["profile_id"] == "alice" and item["fallback_anomaly_count"] == 1 for item in report["profile_hits"]
    )


def test_dual_write_read_controls_can_update_runtime_gray_release(tmp_path: Path):
    state_dir = tmp_path / "coordination-controls"
    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "coordination.db"
    primary_audit = FileBackedCoordinationAuditStore(state_dir / "audit.jsonl", max_items=100)
    secondary_audit = SQLiteCoordinationAuditStore(db_path)
    dual_audit = DualWriteCoordinationAuditStore(
        primary_audit,
        secondary_audit,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
        profile_allowlist=["alpha"],
        rollout_percentage=0,
    )
    dual_audit.append(
        event_type="coordination_conflict_decided",
        profile_id="beta",
        strategy="queue",
        outcome="queued",
        reason="controls",
    )
    before = dual_audit.drill_read(profile_id="beta", window_limit=10)
    assert before["selected_backend"] == "primary_file"

    updated = dual_audit.update_read_routing_controls(
        profile_allowlist=["beta"],
        rollout_percentage=100,
        source="test-runtime",
    )
    assert updated["profile_allowlist"] == ["beta"]
    assert updated["rollout_percentage"] == 100
    assert updated["source"] == "test-runtime"

    after = dual_audit.drill_read(profile_id="beta", window_limit=10)
    assert after["selected_backend"] == "secondary_sqlite"
    assert after["routing_reason"] == "allowlist"

    primary_policy = FileBackedCoordinationPolicyStore(state_dir / "policy.json")
    secondary_policy = SQLiteCoordinationPolicyStore(db_path)
    dual_policy = DualWriteCoordinationPolicyStore(
        primary_policy,
        secondary_policy,
        enabled=True,
        read_preferred_backend="sqlite",
        fallback_to_primary=True,
        profile_allowlist=["alpha"],
        rollout_percentage=0,
    )
    dual_policy.set_strategy(profile_id="beta", strategy="queue", source="test")
    policy_before = dual_policy.drill_read(profile_id="beta")
    assert policy_before["selected_backend"] == "primary_file"
    policy_updated = dual_policy.update_read_routing_controls(
        profile_allowlist=["beta"],
        rollout_percentage=100,
        source="test-runtime",
    )
    assert policy_updated["profile_allowlist"] == ["beta"]
    policy_after = dual_policy.drill_read(profile_id="beta")
    assert policy_after["selected_backend"] == "secondary_sqlite"
    assert policy_after["routing_reason"] == "allowlist"
