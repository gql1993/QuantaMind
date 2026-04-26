from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TypeVar


T = TypeVar("T")


class ModelRuntimeTimeoutError(TimeoutError):
    pass


async def run_with_timeout(awaitable: Awaitable[T], timeout_seconds: float | None) -> T:
    if timeout_seconds is None or timeout_seconds <= 0:
        return await awaitable
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise ModelRuntimeTimeoutError(f"model request timed out after {timeout_seconds:.2f}s") from exc
