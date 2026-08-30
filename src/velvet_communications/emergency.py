"""Bounded emergency fallback routing for degraded/off-grid incidents.

This module does not define medical semantics or authorize any action. It only
constrains when a deliberately public emergency beacon may fall back to an
explicitly enabled unprotected constrained carrier.
"""
from __future__ import annotations

from typing import Iterable

from .contracts import DeliveryPlan, Priority, TransportKind, TransportOffer, V2VEnvelope
from .routing import NoEligibleTransport, TransportSelector


EMERGENCY_BEACON_PAYLOAD_TYPE = "velvet.emergency.beacon.v1"
EMERGENCY_BROADCAST_DESTINATION = "broadcast.emergency"
MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES = 384
MAX_PUBLIC_EMERGENCY_TTL_MS = 5 * 60 * 1000
MAX_PUBLIC_EMERGENCY_HOPS = 3

_OPEN_FALLBACK_KINDS = {
    TransportKind.LORA_P2P,
    TransportKind.MESHTASTIC,
    TransportKind.LORAWAN,
}


class InvalidEmergencyBeacon(ValueError):
    """Raised when an envelope is not safe for public emergency fallback."""


class EmergencyFallbackPolicy:
    """Select a best-effort emergency carrier without weakening normal policy.

    Protected transports are always attempted first. An unprotected radio path
    is considered only when ``allow_unprotected_broadcast`` is explicitly true
    and the envelope satisfies the narrow public-beacon contract.

    Selection means only that Communications found a carrier to try. It does
    not mean the beacon reached a responder, emergency service, or any receiver.
    """

    def validate_public_beacon(self, envelope: V2VEnvelope) -> None:
        if envelope.payload_type != EMERGENCY_BEACON_PAYLOAD_TYPE:
            raise InvalidEmergencyBeacon("unexpected emergency payload type")
        if envelope.destination_peer_id != EMERGENCY_BROADCAST_DESTINATION:
            raise InvalidEmergencyBeacon("emergency beacon must use broadcast destination")
        if envelope.priority is not Priority.URGENT:
            raise InvalidEmergencyBeacon("emergency beacon must be urgent")
        if envelope.payload_bytes > MAX_PUBLIC_EMERGENCY_PAYLOAD_BYTES:
            raise InvalidEmergencyBeacon("emergency beacon exceeds public payload limit")
        if envelope.ttl_ms > MAX_PUBLIC_EMERGENCY_TTL_MS:
            raise InvalidEmergencyBeacon("emergency beacon TTL is too long")
        if envelope.hop_limit > MAX_PUBLIC_EMERGENCY_HOPS:
            raise InvalidEmergencyBeacon("emergency beacon hop limit is too high")

    def select(
        self,
        envelope: V2VEnvelope,
        offers: Iterable[TransportOffer],
        *,
        allow_unprotected_broadcast: bool = False,
    ) -> DeliveryPlan:
        self.validate_public_beacon(envelope)
        available = tuple(offers)
        selector = TransportSelector()

        # Prefer a normally protected route whenever one exists.
        try:
            return selector.select(envelope, available, require_protected_path=True)
        except NoEligibleTransport:
            pass

        if not allow_unprotected_broadcast:
            raise NoEligibleTransport("no protected emergency transport available")

        # The public exception is deliberately narrow: constrained radio only.
        radio_offers = tuple(
            offer for offer in available if offer.kind in _OPEN_FALLBACK_KINDS
        )
        if not radio_offers:
            raise NoEligibleTransport("no eligible open emergency radio transport")

        return selector.select(
            envelope,
            radio_offers,
            require_protected_path=False,
        )
