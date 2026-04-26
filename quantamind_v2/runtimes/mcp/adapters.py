from __future__ import annotations

import asyncio
from typing import Any


def tool_ping(*, message: str = "pong") -> dict[str, Any]:
    return {"ok": True, "message": message}


def tool_uppercase(*, text: str) -> dict[str, Any]:
    return {"text": text.upper(), "length": len(text)}


async def tool_sleep_echo(*, text: str, delay_seconds: float = 0.02) -> dict[str, Any]:
    await asyncio.sleep(max(delay_seconds, 0.0))
    return {"text": text, "delay_seconds": delay_seconds}
