"""
QuantaMind WebSocket/REST client for Q-EDA.

Manages the persistent connection to QuantaMind Gateway, handles:
  - Session lifecycle (create, maintain, close)
  - Chat messaging (streaming SSE and WebSocket)
  - Tool call reception and execution
  - Tool registration on connect
  - Heartbeat reporting every 5 minutes
  - Automatic reconnection with exponential backoff
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Callable, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

from quantamind.client.qeda_bridge.protocol import (
    ChatMessage,
    HeartbeatPayload,
    MessageType,
    StreamChunk,
    ToolCallMessage,
    ToolResultMessage,
)
from quantamind.client.qeda_bridge.tool_registry import QEDAToolRegistry
from quantamind.server.qeda_bootstrap import get_qeda_config as get_config
from quantamind.server.events import (
    QuantaMindConnected,
    QuantaMindDisconnected,
    QuantaMindMessageEvent,
    QuantaMindToolCallEvent,
    get_event_bus,
)


def is_loopback_gateway_url(url: str) -> bool:
    """True when URL host is loopback; use with httpx trust_env=False to bypass system proxy."""
    try:
        host = urlparse(url).hostname
        if not host:
            return False
        h = host.lower()
        return h in ("localhost", "127.0.0.1", "::1") or h.startswith("127.")
    except Exception:
        return False


class QuantaMindClient:
    """
    Async client for QuantaMind Gateway communication.

    Lifecycle:
      1. connect() → creates session, registers tools, starts heartbeat
      2. chat() / chat_stream() → sends messages, receives responses
      3. Handles incoming tool_call messages via QEDAToolRegistry
      4. disconnect() → closes session and connections
    """

    def __init__(self, tool_registry: QEDAToolRegistry | None = None) -> None:
        cfg = get_config().quantamind
        self._base_url = cfg.gateway_url
        self._ws_url = cfg.gateway_ws_url
        self._api_prefix = cfg.api_prefix
        self._reconnect_interval = cfg.reconnect_interval
        self._max_reconnect = cfg.max_reconnect_attempts
        self._heartbeat_interval = cfg.heartbeat_interval

        self._tool_registry = tool_registry or QEDAToolRegistry()
        self._session_id: str = ""
        self._connected = False
        self._http: Optional[httpx.AsyncClient] = None
        self._ws: Any = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._ws_listener_task: Optional[asyncio.Task] = None

        self._on_message: list[Callable[[str, str], None]] = []
        self._on_tool_call: list[Callable[[ToolCallMessage], None]] = []

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def tool_registry(self) -> QEDAToolRegistry:
        return self._tool_registry

    # --- Connection ---

    async def connect(self) -> bool:
        """Connect to QuantaMind Gateway and establish a session."""
        try:
            client_kw: dict[str, Any] = {
                "base_url": self._base_url,
                "timeout": httpx.Timeout(30.0, connect=10.0),
            }
            if is_loopback_gateway_url(self._base_url):
                client_kw["trust_env"] = False
            self._http = httpx.AsyncClient(**client_kw)

            health = await self._http.get("/health")
            if health.status_code != 200:
                logger.error("QuantaMind Gateway health check failed: {}", health.status_code)
                return False

            resp = await self._http.post(
                f"{self._api_prefix}/sessions",
                json={"source": "qeda", "version": "7.0.0"},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                self._session_id = data.get("session_id", "")
                logger.info("QuantaMind session created: {}", self._session_id)
            else:
                logger.warning("Session creation returned {}, using default", resp.status_code)
                self._session_id = "qeda-local"

            await self._register_tools()

            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self._connected = True
            get_event_bus().publish(QuantaMindConnected(
                session_id=self._session_id,
                source="quantamind_client",
            ))

            logger.info("Connected to QuantaMind Gateway at {}", self._base_url)
            return True

        except Exception as e:
            logger.warning("Failed to connect to QuantaMind Gateway: {}", e)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Gracefully disconnect from QuantaMind Gateway."""
        self._connected = False

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()

        if self._ws_listener_task and not self._ws_listener_task.done():
            self._ws_listener_task.cancel()

        if self._session_id and self._http:
            try:
                await self._http.delete(
                    f"{self._api_prefix}/sessions/{self._session_id}"
                )
            except Exception:
                pass

        if self._http:
            await self._http.aclose()
            self._http = None

        get_event_bus().publish(QuantaMindDisconnected(
            reason="user_disconnect",
            source="quantamind_client",
        ))
        logger.info("Disconnected from QuantaMind Gateway")

    # --- Chat ---

    async def chat(self, message: str, agent: str | None = None) -> str:
        """Send a chat message and return the full response (non-streaming)."""
        if not self._http:
            raise ConnectionError("Not connected to QuantaMind")

        payload = ChatMessage(
            message=message,
            session_id=self._session_id,
            agent=agent,
            stream=False,
        )

        resp = await self._http.post(
            f"{self._api_prefix}/chat",
            json=payload.model_dump(mode="json"),
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()

        content = data.get("response", data.get("data", ""))

        get_event_bus().publish(QuantaMindMessageEvent(
            content=content,
            agent=data.get("agent", ""),
            source="quantamind_client",
        ))

        return content

    async def chat_stream(
        self, message: str, agent: str | None = None
    ) -> AsyncGenerator[str, None]:
        """Send a chat message and yield streaming response chunks."""
        if not self._http:
            raise ConnectionError("Not connected to QuantaMind")

        payload = ChatMessage(
            message=message,
            session_id=self._session_id,
            agent=agent,
            stream=True,
        )

        async with self._http.stream(
            "POST",
            f"{self._api_prefix}/chat",
            json=payload.model_dump(mode="json"),
            timeout=120.0,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        chunk = StreamChunk(**chunk_data)
                        if chunk.type == MessageType.CONTENT:
                            yield chunk.data
                        elif chunk.type == MessageType.DONE:
                            break
                    except json.JSONDecodeError:
                        yield data_str

    # --- Tool Calls ---

    async def handle_tool_call(self, msg: ToolCallMessage) -> ToolResultMessage:
        """Execute a tool call from QuantaMind and return the result."""
        get_event_bus().publish(QuantaMindToolCallEvent(
            agent=msg.agent,
            tool=msg.tool,
            params=msg.params,
            request_id=msg.request_id,
            source="quantamind_client",
        ))

        try:
            result = await self._tool_registry.execute(msg.tool, **msg.params)
            return ToolResultMessage(
                request_id=msg.request_id,
                tool=msg.tool,
                success=True,
                result=result,
            )
        except KeyError:
            return ToolResultMessage(
                request_id=msg.request_id,
                tool=msg.tool,
                success=False,
                error=f"Tool '{msg.tool}' not found in Q-EDA registry",
            )
        except Exception as e:
            logger.exception("Tool execution failed: {}", msg.tool)
            return ToolResultMessage(
                request_id=msg.request_id,
                tool=msg.tool,
                success=False,
                error=str(e),
            )

    # --- Internal ---

    async def _register_tools(self) -> None:
        """Register all Q-EDA tools with QuantaMind Gateway."""
        if not self._http:
            return

        registrations = self._tool_registry.get_registrations()
        logger.info("Registering {} tools with QuantaMind Gateway", len(registrations))

        for reg in registrations:
            try:
                await self._http.post(
                    f"{self._api_prefix}/tools",
                    json=reg.model_dump(mode="json"),
                )
            except Exception:
                logger.debug("Tool registration endpoint not available (non-critical)")
                break

    async def _heartbeat_loop(self) -> None:
        """Send heartbeat every N seconds (default 300s = 5min)."""
        while self._connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if not self._connected or not self._http:
                    break

                payload = HeartbeatPayload()
                await self._http.post(
                    f"{self._api_prefix}/heartbeat",
                    json=payload.model_dump(mode="json"),
                )
                logger.debug("Heartbeat sent")
            except asyncio.CancelledError:
                break
            except Exception:
                logger.debug("Heartbeat send failed (non-critical)")

    async def _reconnect(self) -> None:
        """Attempt reconnection with exponential backoff."""
        for attempt in range(self._max_reconnect):
            delay = min(self._reconnect_interval * (2 ** attempt), 60.0)
            logger.info("Reconnection attempt {}/{} in {:.0f}s", attempt + 1, self._max_reconnect, delay)
            await asyncio.sleep(delay)
            if await self.connect():
                return
        logger.error("Failed to reconnect after {} attempts", self._max_reconnect)
