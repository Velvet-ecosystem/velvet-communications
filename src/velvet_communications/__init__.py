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
    BEACON_OF_HOPE_NAME,
    EMERGENCY_BEACON_PAYLOAD_TYPE,
    EMERGENCY_BROADCAST_DESTINATION,
    MAX_PUBLIC_EMERGENCY_HOPS,
    MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES,
    MAX_PUBLIC_EMERGENCY_TTL_MS,
    EmergencyFallbackPolicy,
    InvalidEmergencyBeacon,
)
from .local_ip import (
    AuthenticatedLocalIpAdapter,
    AuthenticatedLocalIpServer,
    LocalIpPeer,
    LocalIpTransportError,
    load_secret_file,
)
from .local_ip_rpc import (
    AuthenticatedLocalIpRequestAdapter,
    AuthenticatedLocalIpRequestServer,
    LocalIpReceiverReply,
    LocalIpRequestReport,
)
from .queueing import StoreAndForwardQueue
from .replay import ReplayGuard
from .routing import NoEligibleTransport, TransportSelector
from .wake import (
    MAX_WAKE_EVIDENCE_REF_CHARS,
    MAX_WAKE_EVIDENCE_REFS,
    MAX_WAKE_PAYLOAD_BYTES,
    MAX_WAKE_REQUEST_TTL_MS,
    MAX_WAKE_SUMMARY_CHARS,
    WAKE_REQUEST_PAYLOAD_TYPE,
    WAKE_REQUEST_SCHEMA,
    WakeReason,
    WakeRequest,
    WakeSeverity,
    build_wake_envelope,
    new_wake_request,
    wake_request_from_envelope,
)

__all__ = [
    "AuthenticatedLocalIpAdapter",
    "AuthenticatedLocalIpRequestAdapter",
    "AuthenticatedLocalIpRequestServer",
    "AuthenticatedLocalIpServer",
    "BEACON_OF_HOPE_NAME",
    "DeliveryPlan",
    "DeliveryReport",
    "EMERGENCY_BEACON_PAYLOAD_TYPE",
    "EMERGENCY_BROADCAST_DESTINATION",
    "EmergencyFallbackPolicy",
    "InvalidEmergencyBeacon",
    "LocalIpPeer",
    "LocalIpReceiverReply",
    "LocalIpRequestReport",
    "LocalIpTransportError",
    "MAX_PUBLIC_EMERGENCY_HOPS",
    "MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES",
    "MAX_PUBLIC_EMERGENCY_TTL_MS",
    "MAX_WAKE_EVIDENCE_REF_CHARS",
    "MAX_WAKE_EVIDENCE_REFS",
    "MAX_WAKE_PAYLOAD_BYTES",
    "MAX_WAKE_REQUEST_TTL_MS",
    "MAX_WAKE_SUMMARY_CHARS",
    "NoEligibleTransport",
    "Priority",
    "ReplayGuard",
    "StoreAndForwardQueue",
    "TransportAdapter",
    "TransportKind",
    "TransportOffer",
    "TransportSelector",
    "V2VEnvelope",
    "WAKE_REQUEST_PAYLOAD_TYPE",
    "WAKE_REQUEST_SCHEMA",
    "WakeReason",
    "WakeRequest",
    "WakeSeverity",
    "build_wake_envelope",
    "load_secret_file",
    "new_wake_request",
    "wake_request_from_envelope",
]
