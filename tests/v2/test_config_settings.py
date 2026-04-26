from quantamind_v2.config import AppSettings, merge_settings_overrides


def test_app_settings_from_dict_and_to_dict_roundtrip():
    payload = {
        "app_name": "QuantaMind V2 Test",
        "app_version": "0.3.0-test",
        "feature_flags": {"enable_mcp_runtime": False},
        "runtime_limits": {"default_model_timeout_seconds": 9.5},
        "providers": {"model_default_provider": "mock_summary"},
        "coordination": {
            "default_conflict_strategy": "queue",
            "audit_export_limit_max": 50,
            "audit_retention_max_events": 300,
            "audit_rotate_max_bytes": 2048,
            "audit_rotate_interval_seconds": 3600,
            "dual_write_enabled": True,
            "database_read_preferred": True,
            "database_read_fallback_to_file": True,
            "database_read_profile_allowlist": ["alpha", "beta"],
            "database_read_rollout_percentage": 25,
            "database_path": ".tmp/coordination-state/coordination.db",
            "state_dir": ".tmp/coordination-state",
        },
    }
    settings = AppSettings.from_dict(payload)
    dumped = settings.to_dict()
    assert dumped["app_name"] == "QuantaMind V2 Test"
    assert dumped["feature_flags"]["enable_mcp_runtime"] is False
    assert dumped["runtime_limits"]["default_model_timeout_seconds"] == 9.5
    assert dumped["providers"]["model_default_provider"] == "mock_summary"
    assert dumped["coordination"]["default_conflict_strategy"] == "queue"
    assert dumped["coordination"]["audit_export_limit_max"] == 50
    assert dumped["coordination"]["audit_rotate_max_bytes"] == 2048
    assert dumped["coordination"]["audit_rotate_interval_seconds"] == 3600
    assert dumped["coordination"]["dual_write_enabled"] is True
    assert dumped["coordination"]["database_read_preferred"] is True
    assert dumped["coordination"]["database_read_fallback_to_file"] is True
    assert dumped["coordination"]["database_read_profile_allowlist"] == ["alpha", "beta"]
    assert dumped["coordination"]["database_read_rollout_percentage"] == 25
    assert dumped["coordination"]["database_path"] == ".tmp/coordination-state/coordination.db"
    assert dumped["coordination"]["state_dir"] == ".tmp/coordination-state"


def test_merge_settings_overrides_updates_nested_fields():
    base = AppSettings()
    merged = merge_settings_overrides(
        base,
        {
            "feature_flags": {"enable_integrations_api": False},
            "runtime_limits": {"default_prompt_budget_chars": 4096},
            "coordination": {"audit_export_limit_max": 40},
        },
    )
    assert merged.feature_flags.enable_integrations_api is False
    assert merged.runtime_limits.default_prompt_budget_chars == 4096
    assert merged.coordination.audit_export_limit_max == 40
