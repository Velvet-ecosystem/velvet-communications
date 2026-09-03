"""Bounded store-and-forward queue for temporarily unreachable peers."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from .contracts import V2VEnvelope


@dataclass(frozen=True)
class QueuedEnvelope:
    envelope: V2VEnvelope
    queued_at_ms: int


class StoreAndForwardQueue:
    def __init__(self, capacity: int = 128, max_payload_bytes: int = 256 * 1024) -> None:
        if capacity < 1 or max_payload_bytes < 1:
            raise ValueError("queue limits must be positive")
        self.capacity = capacity
        self.max_payload_bytes = max_payload_bytes
        self._items: Deque[QueuedEnvelope] = deque()

    def enqueue(self, envelope: V2VEnvelope, now_ms: int) -> None:
        self.prune(now_ms)
        if envelope.is_expired(now_ms):
            raise ValueError("cannot queue expired envelope")
        if envelope.payload_bytes > self.max_payload_bytes:
            raise ValueError("envelope exceeds queue payload limit")
        if len(self._items) >= self.capacity:
            raise OverflowError("store-and-forward queue is full")
        self._items.append(QueuedEnvelope(envelope=envelope, queued_at_ms=now_ms))

    def prune(self, now_ms: int) -> int:
        before = len(self._items)
        self._items = deque(
            item for item in self._items if not item.envelope.is_expired(now_ms)
        )
        return before - len(self._items)

    def pop_next(self, now_ms: int) -> Optional[V2VEnvelope]:
        self.prune(now_ms)
        if not self._items:
            return None
        return self._items.popleft().envelope

    def __len__(self) -> int:
        return len(self._items)
