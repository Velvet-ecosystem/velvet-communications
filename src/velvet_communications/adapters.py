"""Adapter protocol for concrete Velvet communications carriers."""
from __future__ import annotations

from typing import Protocol

from .contracts import DeliveryReport, TransportOffer, V2VEnvelope


class TransportAdapter(Protocol):
    """Carrier adapter boundary.

    Implementations may wrap IP sockets, Tailscale-visible services, direct
    LoRa radios, Meshtastic clients, LoRaWAN gateways, serial links, or future
    transports. Higher layers should depend on this protocol, not carrier APIs.
    """

    def offer(self) -> TransportOffer:
        """Return current bounded carrier capabilities and health."""

    def send(self, envelope: V2VEnvelope) -> DeliveryReport:
        """Attempt delivery without interpreting payload authority."""
