from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    app_name: str = "QuantaMind API"
    app_version: str = "0.1.0"
    host: str = os.getenv("QUANTAMIND_GATEWAY_HOST", "0.0.0.0")
    port: int = int(os.getenv("QUANTAMIND_GATEWAY_PORT", "18789"))
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
