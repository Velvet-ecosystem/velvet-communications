"""Velvet Communications: transport-neutral V2V messaging."""

from .adapters import TransportAdapter
from .contracts import (
    DeliveryPlan,
    DeliveryReport,
    Priority,
    TransportKind,
    TransportOffer,
    V2VEnvelope,
)
from .emergency import (
    EMERGENCY_BEACON_PAYLOAD_TYPE,
    EMERGENCY_BROADCAST_DESTINATION,
    MAX_PUBLIC_EMERGENCY_HOPS,
    MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES,
    MAX_PUBLIC_EMERGENCY_TTL_MS,
    EmergencyFallbackPolicy,
    InvalidEmergencyBeacon,
)
from .queueing import StoreAndForwardQueue
from .replay import ReplayGuard
from .routing import NoEligibleTransport, TransportSelector

__all__ = [
    "DeliveryPlan",
    "DeliveryReport",
    "EMERGENCY_BEACON_PAYLOAD_TYPE",
    "EMERGENCY_BROADCAST_DESTINATION",
    "EmergencyFallbackPolicy",
    "InvalidEmergencyBeacon",
    "MAX_PUBLIC_EMERGENCY_HOPS",
    "MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES",
    "MAX_PUBLIC_EMERGENCY_TTL_MS",
    "NoEligibleTransport",
    "Priority",
    "ReplayGuard",
    "StoreAndForwardQueue",
    "TransportAdapter",
    "TransportKind",
    "TransportOffer",
    "TransportSelector",
    "V2VEnvelope",
]
