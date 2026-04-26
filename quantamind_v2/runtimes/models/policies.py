from __future__ import annotations

from dataclasses import dataclass

from quantamind_v2.runtimes.models.providers import ModelRequest


@dataclass(slots=True)
class ModelRuntimePolicy:
    default_provider: str = "mock_echo"
    fallback_provider: str = "mock_echo"
    request_timeout_seconds: float = 15.0
    allow_provider_fallback: bool = True
    max_prompt_chars: int = 12000


def apply_prompt_budget(request: ModelRequest, max_prompt_chars: int) -> ModelRequest:
    if max_prompt_chars <= 0:
        return request
    if len(request.prompt) <= max_prompt_chars:
        return request
    trimmed = request.prompt[: max_prompt_chars - 3] + "..."
    return ModelRequest(
        provider=request.provider,
        model=request.model,
        prompt=trimmed,
        messages=list(request.messages),
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        metadata=dict(request.metadata or {}),
    )
