from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantamind_v2.runtimes.mcp.registry import MCPToolRegistry, invoke_handler


@dataclass(slots=True)
class MCPCallResult:
    tool: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Minimal MCP client that invokes tools from a registry."""

    def __init__(self, registry: MCPToolRegistry) -> None:
        self.registry = registry

    async def call_tool(self, tool: str, *, args: dict[str, Any] | None = None) -> MCPCallResult:
        spec = self.registry.get(tool)
        if spec is None:
            raise ValueError(f"mcp tool not found: {tool}")
        payload = dict(args or {})
        output = await invoke_handler(spec.handler, **payload)
        return MCPCallResult(
            tool=spec.name,
            output=output,
            metadata={"tool_description": spec.description},
        )
