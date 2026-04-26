from fastapi.testclient import TestClient

from quantamind_v2.config import AppSettings
from quantamind_v2.core.gateway.app import create_app


def test_gateway_config_summary_endpoint_reflects_settings():
    settings = AppSettings.from_dict(
        {
            "app_name": "QuantaMind Gateway V2 ConfigTest",
            "app_version": "0.2.1-test",
            "runtime_limits": {"default_model_timeout_seconds": 7.0},
            "providers": {"model_default_provider": "mock_summary"},
            "coordination": {
                "default_conflict_strategy": "queue",
                "audit_export_limit_max": 20,
                "audit_rotate_max_bytes": 2048,
                "dual_write_enabled": True,
                "database_read_preferred": True,
                "database_read_fallback_to_file": True,
                "database_read_profile_allowlist": ["alpha"],
                "database_read_rollout_percentage": 15,
                "database_path": ".tmp/coordination-state/coordination.db",
            },
        }
    )
    client = TestClient(create_app(settings=settings))
    response = client.get("/api/v2/config/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "QuantaMind Gateway V2 ConfigTest"
    assert payload["app_version"] == "0.2.1-test"
    assert payload["runtime_limits"]["default_model_timeout_seconds"] == 7.0
    assert payload["providers"]["model_default_provider"] == "mock_summary"
    assert payload["coordination"]["default_conflict_strategy"] == "queue"
    assert payload["coordination"]["audit_export_limit_max"] == 20
    assert payload["coordination"]["audit_rotate_max_bytes"] == 2048
    assert payload["coordination"]["dual_write_enabled"] is True
    assert payload["coordination"]["database_read_preferred"] is True
    assert payload["coordination"]["database_read_fallback_to_file"] is True
    assert payload["coordination"]["database_read_profile_allowlist"] == ["alpha"]
    assert payload["coordination"]["database_read_rollout_percentage"] == 15
    assert payload["coordination"]["database_path"] == ".tmp/coordination-state/coordination.db"


def test_gateway_openapi_info_uses_settings_title_and_version():
    settings = AppSettings.from_dict({"app_name": "QuantaMind API", "app_version": "9.9.9"})
    client = TestClient(create_app(settings=settings))
    response = client.get("/openapi.json")
    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == "QuantaMind API"
    assert info["version"] == "9.9.9"
