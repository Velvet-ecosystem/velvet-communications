"""Bounded communications-layer duplicate suppression."""
from __future__ import annotations

from collections import OrderedDict


class ReplayGuard:
    """Remember recent message IDs without becoming Runtime's action replay ledger."""

    def __init__(self, capacity: int = 1024) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._seen: OrderedDict[str, None] = OrderedDict()

    def accept(self, message_id: str) -> bool:
        if not message_id:
            raise ValueError("message_id is required")
        if message_id in self._seen:
            self._seen.move_to_end(message_id)
            return False
        self._seen[message_id] = None
        while len(self._seen) > self.capacity:
            self._seen.popitem(last=False)
        return True

    def __len__(self) -> int:
        return len(self._seen)
