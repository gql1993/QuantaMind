"""MCP runtime primitives for QuantaMind V2."""

from .adapters import tool_ping, tool_sleep_echo, tool_uppercase
from .client import MCPCallResult, MCPClient
from .host import MCPHost, MCPHostPolicy
from .registry import MCPToolRegistry, MCPToolSpec

__all__ = [
    "MCPCallResult",
    "MCPClient",
    "MCPHost",
    "MCPHostPolicy",
    "MCPToolRegistry",
    "MCPToolSpec",
    "tool_ping",
    "tool_sleep_echo",
    "tool_uppercase",
]
