"""Optional local FastAPI sidecar (QEDA design daemon, port 18800 by default)."""

from quantamind.server.sidecar.app import create_sidecar_app, run_sidecar

__all__ = ["create_sidecar_app", "run_sidecar"]
