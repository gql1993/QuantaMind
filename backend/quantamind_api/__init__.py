"""Separated FastAPI entrypoint for QuantaMind."""

from backend.quantamind_api.app import app, create_app

__all__ = ["app", "create_app"]
