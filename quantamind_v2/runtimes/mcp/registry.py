from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


MCPToolHandler = Callable[..., Any | Awaitable[Any]]


@dataclass(slots=True)
class MCPToolSpec:
    name: str
    description: str
    handler: MCPToolHandler
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPToolRegistry:
    """In-memory MCP tool registry."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPToolSpec] = {}

    def register(self, spec: MCPToolSpec, *, replace: bool = False) -> None:
        name = spec.name.strip().lower()
        if not name:
            raise ValueError("mcp tool name cannot be empty")
        if name in self._tools and not replace:
            raise ValueError(f"mcp tool already exists: {name}")
        self._tools[name] = MCPToolSpec(
            name=name,
            description=spec.description,
            handler=spec.handler,
            metadata=dict(spec.metadata or {}),
        )

    def get(self, name: str) -> MCPToolSpec | None:
        return self._tools.get(name.strip().lower())

    def list(self) -> list[MCPToolSpec]:
        return list(self._tools.values())

    def has(self, name: str) -> bool:
        return self.get(name) is not None


async def invoke_handler(handler: MCPToolHandler, **kwargs: Any) -> Any:
    value = handler(**kwargs)
    if inspect.isawaitable(value):
        value = await value
    return value
