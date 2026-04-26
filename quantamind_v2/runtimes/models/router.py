from __future__ import annotations

from dataclasses import dataclass

from quantamind_v2.runtimes.models.policies import ModelRuntimePolicy, apply_prompt_budget
from quantamind_v2.runtimes.models.providers import (
    ModelProvider,
    ModelProviderRegistry,
    ModelRequest,
    ModelResponse,
    ProviderSpec,
    build_mock_echo_provider,
    build_mock_summary_provider,
    invoke_provider,
)
from quantamind_v2.runtimes.models.timeouts import run_with_timeout


@dataclass(slots=True)
class ModelRuntimeResult:
    response: ModelResponse
    requested_provider: str
    used_provider: str
    fallback_used: bool = False


class ModelRuntimeRouter:
    """Minimal provider-based model runtime for V2."""

    def __init__(
        self,
        *,
        registry: ModelProviderRegistry | None = None,
        policy: ModelRuntimePolicy | None = None,
    ) -> None:
        self.registry = registry or ModelProviderRegistry()
        self.policy = policy or ModelRuntimePolicy()
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        if not self.registry.has("mock_echo"):
            self.registry.register(
                ProviderSpec(
                    name="mock_echo",
                    handler=build_mock_echo_provider(),
                    default_model="mock-echo-v1",
                    description="Built-in deterministic echo provider for tests and local dev.",
                )
            )
        if not self.registry.has("mock_summary"):
            self.registry.register(
                ProviderSpec(
                    name="mock_summary",
                    handler=build_mock_summary_provider(),
                    default_model="mock-summary-v1",
                    description="Built-in deterministic summary provider for tests and local dev.",
                )
            )

    def register_provider(self, spec: ProviderSpec, *, replace: bool = False) -> None:
        self.registry.register(spec, replace=replace)

    def list_providers(self) -> list[dict]:
        return [
            {
                "name": spec.name,
                "default_model": spec.default_model,
                "description": spec.description,
                "metadata": dict(spec.metadata or {}),
            }
            for spec in self.registry.list()
        ]

    async def generate(self, request: ModelRequest, *, timeout_seconds: float | None = None) -> ModelRuntimeResult:
        timeout = self.policy.request_timeout_seconds if timeout_seconds is None else timeout_seconds
        bounded = apply_prompt_budget(request, self.policy.max_prompt_chars)
        requested_provider = (bounded.provider or self.policy.default_provider).strip().lower()
        fallback_provider = self.policy.fallback_provider.strip().lower()
        providers_to_try: list[str] = [requested_provider]
        if (
            self.policy.allow_provider_fallback
            and fallback_provider
            and fallback_provider not in providers_to_try
        ):
            providers_to_try.append(fallback_provider)
        last_error: Exception | None = None
        for idx, provider_name in enumerate(providers_to_try):
            spec = self.registry.get(provider_name)
            if spec is None:
                last_error = ValueError(f"model provider not found: {provider_name}")
                continue
            call_request = ModelRequest(
                provider=spec.name,
                model=bounded.model or spec.default_model,
                prompt=bounded.prompt,
                messages=list(bounded.messages),
                temperature=bounded.temperature,
                max_tokens=bounded.max_tokens,
                metadata=dict(bounded.metadata or {}),
            )
            try:
                response = await run_with_timeout(invoke_provider(spec.handler, call_request), timeout)
                response.metadata = dict(response.metadata or {})
                response.metadata["requested_provider"] = requested_provider
                response.metadata["fallback_used"] = idx > 0
                return ModelRuntimeResult(
                    response=response,
                    requested_provider=requested_provider,
                    used_provider=spec.name,
                    fallback_used=idx > 0,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("model runtime failed without provider attempts")


def make_provider_spec(
    *,
    name: str,
    handler: ModelProvider,
    default_model: str,
    description: str = "",
    metadata: dict | None = None,
) -> ProviderSpec:
    return ProviderSpec(
        name=name,
        handler=handler,
        default_model=default_model,
        description=description,
        metadata=dict(metadata or {}),
    )
