"""Model runtime primitives for QuantaMind V2."""

from .client_ollama import build_ollama_provider
from .client_openai_compat import build_openai_compat_provider
from .policies import ModelRuntimePolicy, apply_prompt_budget
from .providers import (
    ModelMessage,
    ModelProviderRegistry,
    ModelRequest,
    ModelResponse,
    ProviderSpec,
    build_mock_echo_provider,
    build_mock_summary_provider,
    sleep_then_echo,
)
from .router import ModelRuntimeResult, ModelRuntimeRouter, make_provider_spec
from .timeouts import ModelRuntimeTimeoutError, run_with_timeout

__all__ = [
    "ModelMessage",
    "ModelProviderRegistry",
    "ModelRequest",
    "ModelResponse",
    "ModelRuntimePolicy",
    "ModelRuntimeResult",
    "ModelRuntimeRouter",
    "ModelRuntimeTimeoutError",
    "ProviderSpec",
    "apply_prompt_budget",
    "build_mock_echo_provider",
    "build_mock_summary_provider",
    "build_ollama_provider",
    "build_openai_compat_provider",
    "make_provider_spec",
    "run_with_timeout",
    "sleep_then_echo",
]
