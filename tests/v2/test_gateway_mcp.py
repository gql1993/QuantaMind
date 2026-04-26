from fastapi.testclient import TestClient

from quantamind_v2.core.gateway.app import create_app


def test_gateway_mcp_list_tools():
    client = TestClient(create_app())
    response = client.get("/api/v2/mcp/tools")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["items"]}
    assert "ping" in names
    assert "uppercase" in names


def test_gateway_mcp_invoke_success():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/mcp/invoke",
        json={"tool": "ping", "args": {"message": "ok"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tool"] == "ping"
    assert payload["output"]["message"] == "ok"


def test_gateway_mcp_invoke_unknown_tool_returns_404():
    client = TestClient(create_app())
    response = client.post("/api/v2/mcp/invoke", json={"tool": "not_exists"})
    assert response.status_code == 404


def test_gateway_mcp_invoke_timeout_returns_504():
    client = TestClient(create_app())
    response = client.post(
        "/api/v2/mcp/invoke",
        json={
            "tool": "sleep_echo",
            "args": {"text": "slow", "delay_seconds": 0.08},
            "timeout_seconds": 0.01,
        },
    )
    assert response.status_code == 504
