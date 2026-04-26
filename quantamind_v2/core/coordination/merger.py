from __future__ import annotations

from typing import Any, Dict, Iterable, List


class CoordinationMerger:
    """Phase 1 minimal merger for specialist outputs."""

    def merge(self, outputs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        collected: List[Dict[str, Any]] = list(outputs)
        summaries: List[str] = []
        for item in collected:
            text = (
                item.get("summary")
                or item.get("status_message")
                or item.get("content")
                or item.get("description")
                or ""
            )
            if text:
                summaries.append(str(text))
        return {
            "status": "ok",
            "count": len(collected),
            "summary": "\n".join(summaries[:8]),
            "outputs": collected,
        }
