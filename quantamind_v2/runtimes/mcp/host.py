from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from quantamind_v2.runtimes.mcp.adapters import tool_ping, tool_sleep_echo, tool_uppercase
from quantamind_v2.runtimes.mcp.client import MCPCallResult, MCPClient
from quantamind_v2.runtimes.mcp.registry import MCPToolRegistry, MCPToolSpec


@dataclass(slots=True)
class MCPHostPolicy:
    default_timeout_seconds: float = 10.0


class MCPHost:
    """Minimal MCP host: registry + client + invoke with timeout."""

    def __init__(
        self,
        *,
        registry: MCPToolRegistry | None = None,
        policy: MCPHostPolicy | None = None,
    ) -> None:
        self.registry = registry or MCPToolRegistry()
        self.policy = policy or MCPHostPolicy()
        self.client = MCPClient(self.registry)
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        if not self.registry.has("ping"):
            self.register_tool(
                MCPToolSpec(
                    name="ping",
                    description="Basic MCP connectivity check.",
                    handler=tool_ping,
                    metadata={"category": "system"},
                )
            )
        if not self.registry.has("uppercase"):
            self.register_tool(
                MCPToolSpec(
                    name="uppercase",
                    description="Uppercase text utility.",
                    handler=tool_uppercase,
                    metadata={"category": "text"},
                )
            )
        if not self.registry.has("sleep_echo"):
            self.register_tool(
                MCPToolSpec(
                    name="sleep_echo",
                    description="Async echo tool for timeout tests.",
                    handler=tool_sleep_echo,
                    metadata={"category": "test"},
                )
            )

    def register_tool(self, spec: MCPToolSpec, *, replace: bool = False) -> None:
        self.registry.register(spec, replace=replace)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": item.name,
                "description": item.description,
                "metadata": dict(item.metadata or {}),
            }
            for item in self.registry.list()
        ]

    async def invoke(
        self,
        tool: str,
        *,
        args: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> MCPCallResult:
        timeout = self.policy.default_timeout_seconds if timeout_seconds is None else timeout_seconds
        if timeout is None or timeout <= 0:
            return await self.client.call_tool(tool, args=args)
        return await asyncio.wait_for(self.client.call_tool(tool, args=args), timeout=timeout)
