from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_model_providers_endpoint_lists_builtin_providers():
    client = TestClient(create_app())
    response = client.get("/api/v2/models/providers")
    assert response.status_code == 200
    items = response.json()["items"]
    names = {item["name"] for item in items}
    assert "mock_echo" in names
    assert "mock_summary" in names


def test_gateway_model_infer_endpoint_returns_text():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/models/infer",
        json={"provider": "mock_summary", "prompt": "line1\nline2"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_provider"] == "mock_summary"
    assert payload["response"]["text"].startswith("Summary:")


def test_gateway_model_infer_falls_back_for_missing_provider():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/models/infer",
        json={"provider": "provider_not_exists", "prompt": "hello"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_used"] is True
    assert payload["used_provider"] == "mock_echo"
