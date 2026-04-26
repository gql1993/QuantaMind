import pytest

from quantamind_v2.runtimes.mcp import MCPHost, MCPToolSpec


@pytest.mark.asyncio
async def test_mcp_host_lists_builtin_tools():
    host = MCPHost()
    names = {item["name"] for item in host.list_tools()}
    assert "ping" in names
    assert "uppercase" in names
    assert "sleep_echo" in names


@pytest.mark.asyncio
async def test_mcp_host_invokes_builtin_tool():
    host = MCPHost()
    result = await host.invoke("uppercase", args={"text": "QuantaMind"})
    assert result.tool == "uppercase"
    assert result.output["text"] == "QUANTAMIND"


@pytest.mark.asyncio
async def test_mcp_host_supports_dynamic_registry_and_timeout():
    host = MCPHost()

    async def _delayed(value: str) -> dict:
        return {"value": value}

    host.register_tool(
        MCPToolSpec(
            name="delayed",
            description="delayed tool",
            handler=_delayed,
        )
    )
    ok = await host.invoke("delayed", args={"value": "ok"}, timeout_seconds=0.2)
    assert ok.output["value"] == "ok"

    with pytest.raises(TimeoutError):
        await host.invoke("sleep_echo", args={"text": "x", "delay_seconds": 0.1}, timeout_seconds=0.01)
