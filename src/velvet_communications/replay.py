"""Bounded communications-layer duplicate suppression."""
from __future__ import annotations

from collections import OrderedDict
from typing import MutableMapping, Optional


class ReplayGuard:
    """Remember recent message IDs without becoming Runtime's action replay ledger."""

    def __init__(self, capacity: int = 1024) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._seen: MutableMapping[str, Optional[object]] = OrderedDict()

    def accept(self, message_id: str) -> bool:
        if not message_id:
            raise ValueError("message_id is required")
        if message_id in self._seen:
            if isinstance(self._seen, OrderedDict):
                self._seen.move_to_end(message_id)
            return False
        self._seen[message_id] = None
        while len(self._seen) > self.capacity:
            if isinstance(self._seen, OrderedDict):
                self._seen.popitem(last=False)
            else:
                first = next(iter(self._seen))
                self._seen.pop(first, None)
        return True

    def __len__(self) -> int:
        return len(self._seen)
