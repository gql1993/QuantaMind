import asyncio

import pytest

from quantamind_v2.runtimes.models import (
    ModelRequest,
    ModelResponse,
    ModelRuntimePolicy,
    ModelRuntimeRouter,
    make_provider_spec,
)


@pytest.mark.asyncio
async def test_model_runtime_builtin_echo_provider():
    runtime = ModelRuntimeRouter()
    result = await runtime.generate(ModelRequest(prompt="hello quantamind"))
    assert result.used_provider == "mock_echo"
    assert result.response.text == "hello quantamind"
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_model_runtime_falls_back_when_requested_provider_missing():
    policy = ModelRuntimePolicy(default_provider="mock_summary", fallback_provider="mock_echo", allow_provider_fallback=True)
    runtime = ModelRuntimeRouter(policy=policy)
    request = ModelRequest(provider="missing_provider", prompt="fallback me")
    result = await runtime.generate(request)
    assert result.used_provider == "mock_echo"
    assert result.fallback_used is True
    assert result.response.metadata["requested_provider"] == "missing_provider"


@pytest.mark.asyncio
async def test_model_runtime_timeout_error_without_fallback():
    async def _slow_provider(request: ModelRequest) -> ModelResponse:
        await asyncio.sleep(0.12)
        return ModelResponse(provider="slow", model="slow-v1", text=request.prompt)

    policy = ModelRuntimePolicy(
        default_provider="slow_provider",
        fallback_provider="",
        allow_provider_fallback=False,
        request_timeout_seconds=0.05,
    )
    runtime = ModelRuntimeRouter(policy=policy)
    runtime.register_provider(
        make_provider_spec(
            name="slow_provider",
            handler=_slow_provider,
            default_model="slow-v1",
            description="slow provider for timeout tests",
        )
    )
    with pytest.raises(TimeoutError):
        await runtime.generate(ModelRequest(prompt="this should timeout"))
