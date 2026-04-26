from typing import Any, Dict

from quantamind.server import resource_registry as rr

DATABASE_CATALOG = rr.RESOURCE_CATALOG


def list_configs() -> Dict[str, Any]:
    return rr.list_resources(mask_secrets=False)


def update_configs(updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return rr.update_resources(updates)


def get_statuses() -> Dict[str, Any]:
    return rr.get_resource_statuses()
