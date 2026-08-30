"""Transport-neutral contracts for Velvet-to-Velvet communications."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


SCHEMA = "velvet.communications.v2v-envelope.v1"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class TransportKind(str, Enum):
    IP = "ip"
    LORA_P2P = "lora-p2p"
    MESHTASTIC = "meshtastic"
    LORAWAN = "lorawan"
    SERIAL = "serial"
    CELLULAR = "cellular"
    OTHER = "other"


class Priority(str, Enum):
    BULK = "bulk"
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


@dataclass(frozen=True)
class V2VEnvelope:
    """Carrier-independent envelope around an opaque approved Velvet payload.

    ``source_peer_id`` and ``destination_peer_id`` are routing identifiers. They
    are not Riven identity roots and do not prove trust or authority.
    """

    message_id: str
    source_peer_id: str
    destination_peer_id: str
    payload_type: str
    payload: bytes
    created_at_ms: int
    ttl_ms: int
    priority: Priority = Priority.NORMAL
    ack_required: bool = False
    hop_limit: int = 4
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        for name, value in (
            ("message_id", self.message_id),
            ("source_peer_id", self.source_peer_id),
            ("destination_peer_id", self.destination_peer_id),
            ("payload_type", self.payload_type),
        ):
            if not _ID_RE.fullmatch(value):
                raise ValueError(f"invalid {name}")
        if not isinstance(self.payload, bytes) or not self.payload:
            raise ValueError("payload must be non-empty bytes")
        if self.created_at_ms < 0:
            raise ValueError("created_at_ms must be non-negative")
        if self.ttl_ms < 1:
            raise ValueError("ttl_ms must be positive")
        if not 0 <= self.hop_limit <= 32:
            raise ValueError("hop_limit must be between 0 and 32")

    @property
    def payload_bytes(self) -> int:
        return len(self.payload)

    def is_expired(self, now_ms: int) -> bool:
        return now_ms >= self.created_at_ms + self.ttl_ms


@dataclass(frozen=True)
class TransportOffer:
    """Current bounded capability report for one carrier path."""

    name: str
    kind: TransportKind
    available: bool
    max_payload_bytes: int
    preference: int
    protected_path: bool
    supports_ack: bool = False
    supports_store_and_forward: bool = False

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.name):
            raise ValueError("invalid transport name")
        if self.max_payload_bytes < 1:
            raise ValueError("max_payload_bytes must be positive")
        if self.preference < 0:
            raise ValueError("preference must be non-negative")


@dataclass(frozen=True)
class DeliveryPlan:
    """A routing decision. It never grants message or execution authority."""

    message_id: str
    transport_name: str
    transport_kind: TransportKind
    degraded: bool
    authority: str = "none"


@dataclass(frozen=True)
class DeliveryReport:
    """Adapter result suitable for later health/event/receipt integration."""

    message_id: str
    transport_name: str
    accepted: bool
    acknowledged: bool = False
    detail: str = ""
    authority: str = "none"
