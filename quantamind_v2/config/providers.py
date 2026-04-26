from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderSettings:
    model_default_provider: str = "mock_echo"
    model_fallback_provider: str = "mock_echo"
    model_default_name: str = "mock-echo-v1"
    gateway_base_url: str = "http://127.0.0.1:18790"

    def to_dict(self) -> dict:
        return {
            "model_default_provider": self.model_default_provider,
            "model_fallback_provider": self.model_fallback_provider,
            "model_default_name": self.model_default_name,
            "gateway_base_url": self.gateway_base_url,
        }
