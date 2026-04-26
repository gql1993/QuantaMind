from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass(slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(slots=True)
class ModelRequest:
    provider: str | None = None
    model: str | None = None
    prompt: str = ""
    messages: list[ModelMessage] = field(default_factory=list)
    temperature: float = 0.0
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelResponse:
    provider: str
    model: str
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


ModelProvider = Callable[[ModelRequest], ModelResponse | Awaitable[ModelResponse]]


@dataclass(slots=True)
class ProviderSpec:
    name: str
    handler: ModelProvider
    default_model: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProviderRegistry:
    """In-memory model provider registry for V2 runtime."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderSpec] = {}

    def register(self, spec: ProviderSpec, *, replace: bool = False) -> None:
        normalized = spec.name.strip().lower()
        if not normalized:
            raise ValueError("provider name cannot be empty")
        if normalized in self._providers and not replace:
            raise ValueError(f"provider already exists: {normalized}")
        self._providers[normalized] = ProviderSpec(
            name=normalized,
            handler=spec.handler,
            default_model=spec.default_model,
            description=spec.description,
            metadata=dict(spec.metadata or {}),
        )

    def get(self, name: str) -> ProviderSpec | None:
        return self._providers.get(name.strip().lower())

    def list(self) -> list[ProviderSpec]:
        return list(self._providers.values())

    def has(self, name: str) -> bool:
        return self.get(name) is not None


async def invoke_provider(handler: ModelProvider, request: ModelRequest) -> ModelResponse:
    result = handler(request)
    if inspect.isawaitable(result):
        result = await result
    if not isinstance(result, ModelResponse):
        raise TypeError("model provider must return ModelResponse")
    return result


def build_mock_echo_provider(*, max_echo_chars: int = 600) -> ModelProvider:
    def _provider(request: ModelRequest) -> ModelResponse:
        text = request.prompt.strip()
        if not text and request.messages:
            text = request.messages[-1].content
        if len(text) > max_echo_chars:
            text = text[: max_echo_chars - 3] + "..."
        model = request.model or "mock-echo-v1"
        return ModelResponse(
            provider="mock_echo",
            model=model,
            text=text or "(empty prompt)",
            usage={
                "prompt_chars": len(request.prompt or ""),
                "messages": len(request.messages),
            },
            raw={"mode": "echo"},
        )

    return _provider


def build_mock_summary_provider() -> ModelProvider:
    def _provider(request: ModelRequest) -> ModelResponse:
        text = request.prompt.strip()
        if not text and request.messages:
            text = request.messages[-1].content
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        preview = " | ".join(lines[:3]) if lines else "(empty)"
        model = request.model or "mock-summary-v1"
        return ModelResponse(
            provider="mock_summary",
            model=model,
            text=f"Summary: {preview}",
            usage={"prompt_chars": len(text), "lines": len(lines)},
            raw={"mode": "summary"},
        )

    return _provider


async def sleep_then_echo(delay_seconds: float, request: ModelRequest) -> ModelResponse:
    await asyncio.sleep(delay_seconds)
    return ModelResponse(
        provider=request.provider or "sleep_echo",
        model=request.model or "sleep-echo-v1",
        text=request.prompt,
        usage={"delay_seconds": delay_seconds},
    )
