"""Policy-light transport selection for V2V envelopes."""
from __future__ import annotations

from typing import Iterable

from .contracts import DeliveryPlan, TransportKind, TransportOffer, V2VEnvelope


CONSTRAINED_KINDS = {
    TransportKind.LORA_P2P,
    TransportKind.MESHTASTIC,
    TransportKind.LORAWAN,
}


class NoEligibleTransport(RuntimeError):
    """Raised when no healthy carrier can safely accept an envelope."""


class TransportSelector:
    """Choose a carrier without changing identity, trust, or authority."""

    def select(
        self,
        envelope: V2VEnvelope,
        offers: Iterable[TransportOffer],
        *,
        require_protected_path: bool = True,
    ) -> DeliveryPlan:
        eligible = []
        for offer in offers:
            if not offer.available:
                continue
            if envelope.payload_bytes > offer.max_payload_bytes:
                continue
            if require_protected_path and not offer.protected_path:
                continue
            if envelope.ack_required and not offer.supports_ack:
                continue
            eligible.append(offer)

        if not eligible:
            raise NoEligibleTransport("no eligible transport for envelope")

        offer = min(eligible, key=lambda item: (item.preference, item.name))
        return DeliveryPlan(
            message_id=envelope.message_id,
            transport_name=offer.name,
            transport_kind=offer.kind,
            degraded=offer.kind in CONSTRAINED_KINDS,
        )
