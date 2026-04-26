"""
Shared component-local geometry cache for canvas/export reuse.
"""

from __future__ import annotations

import copy
import json
import threading
from collections import OrderedDict
from typing import Any

from quantamind.server.geometry.engine import GeometryResult


class GeometryCache:
    def __init__(self, max_entries: int = 2048) -> None:
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, GeometryResult] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): self._normalize_value(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
        if isinstance(value, (list, tuple)):
            return [self._normalize_value(v) for v in value]
        if isinstance(value, float):
            return round(value, 6)
        return value

    def key_for(self, payload: dict[str, Any]) -> str:
        return json.dumps(self._normalize_value(payload), ensure_ascii=True, sort_keys=True)

    def get(self, key: str) -> GeometryResult | None:
        with self._lock:
            value = self._cache.get(key)
            if value is None:
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return copy.deepcopy(value)

    def set(self, key: str, value: GeometryResult) -> GeometryResult:
        with self._lock:
            self._cache[key] = copy.deepcopy(value)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)
            return copy.deepcopy(value)

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "max_entries": self._max_entries,
            }


_CACHE = GeometryCache()


def get_geometry_cache() -> GeometryCache:
    return _CACHE

