from __future__ import annotations

from typing import Dict, List, Optional

from quantamind_v2.contracts.run import RunRecord


class InMemoryRunRegistry:
    """Phase 1 in-memory registry for V2 run records."""

    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}

    def put(self, run: RunRecord) -> RunRecord:
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> Optional[RunRecord]:
        return self._runs.get(run_id)

    def list(self) -> List[RunRecord]:
        return list(self._runs.values())
