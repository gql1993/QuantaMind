from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_v2_gateway_exposes_renderer_registry_loader_and_active_map():
    client = TestClient(create_app())
    response = client.get("/api/v2/artifacts/renderers/registry")
    assert response.status_code == 200
    payload = response.json()
    assert "loader" in payload
    assert "active_renderers" in payload
    active = payload["active_renderers"]
    assert isinstance(active, dict)
    assert "coordination_report" in active


def test_v2_gateway_renderer_registry_reports_invalid_config_warning(tmp_path):
    broken = tmp_path / "broken_registry.json"
    broken.write_text('{"renderers": {"unknown_type": "x:y"}}', encoding="utf-8")
    client = TestClient(create_app(renderer_registry_config=str(broken)))
    response = client.get("/api/v2/artifacts/renderers/registry")
    assert response.status_code == 200
    payload = response.json()
    warnings = payload["loader"].get("warnings", [])
    assert any("unknown artifact type" in item for item in warnings)
