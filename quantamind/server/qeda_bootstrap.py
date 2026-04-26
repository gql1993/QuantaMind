"""
Minimal QEDA-compatible settings for migrated services (sidecar, simulation bridge).

Avoids pulling the full QEDA YAML config stack from EDA-Q-main.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SidecarConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 18800
    ws_path: str = "/ws"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    workers: int = 1
    log_level: str = "info"


class SimulationConfig(BaseModel):
    ansys_version: str = "2024.1"
    max_concurrent_jobs: int = 4
    timeout_seconds: int = 7200


class QuantaMindBridgeConfig(BaseModel):
    gateway_url: str = "http://127.0.0.1:18789"
    gateway_ws_url: str = "ws://127.0.0.1:18789/ws"
    api_prefix: str = "/api/v1"
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 20
    heartbeat_interval: float = 300.0
    session_timeout: float = 3600.0
    tool_call_timeout: float = 120.0


class QEDACompatSettings(BaseModel):
    sidecar: SidecarConfig = Field(default_factory=SidecarConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    quantamind: QuantaMindBridgeConfig = Field(default_factory=QuantaMindBridgeConfig)


_settings = QEDACompatSettings()


def get_qeda_config() -> QEDACompatSettings:
    return _settings
