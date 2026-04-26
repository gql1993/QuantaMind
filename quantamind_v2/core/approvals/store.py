from __future__ import annotations

from typing import Dict, List

from quantamind_v2.contracts.approval import ApprovalRequest
from quantamind_v2.contracts.approval import ApprovalStatus


class InMemoryApprovalStore:
    """Minimal in-memory approval request store."""

    def __init__(self) -> None:
        self._items: Dict[str, ApprovalRequest] = {}

    def put(self, approval: ApprovalRequest) -> ApprovalRequest:
        self._items[approval.approval_id] = approval
        return approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._items.get(approval_id)

    def list(self, status: ApprovalStatus | None = None) -> List[ApprovalRequest]:
        values = list(self._items.values())
        if status is None:
            return values
        return [item for item in values if item.status == status]
