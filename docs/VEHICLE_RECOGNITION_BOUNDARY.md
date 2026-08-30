# Vehicle Recognition and Communications Boundary

## Purpose

Velvet Communications owns cooperative cross-node delivery and peer transport. It does **not** own passive tracking or visual re-identification of arbitrary vehicles.

This boundary is especially important for emergency-service awareness, where cooperative V2X information may be useful but must remain distinct from passive local recognition.

## Cooperative vehicle communication

Communications may carry or adapt approved standards-based or Velvet-native messages from vehicles that deliberately transmit compatible information, including future:

- Velvet-to-Velvet peer discovery and messaging;
- authenticated V2X safety messages;
- emergency-vehicle status or approach notifications;
- infrastructure or roadside safety messages;
- bounded service advertisements;
- acknowledgements, health, and store-and-forward traffic.

A received message is information, not authority.

## Non-cooperative vehicles

A vehicle that does not speak a compatible protocol is not a Communications peer merely because Velvet can see it, hear it, or infer that it has been encountered before.

Passive recognition belongs to perception/AI Core policy and must not be converted into:

- a synthetic V2V identity;
- a persistent communications peer record;
- a radio-address association database;
- a license-plate identity map;
- an owner identity lookup;
- a cross-session vehicle dossier.

## Emergency-service exception is about safety, not identity

Emergency-service recognition receives higher safety priority in the perception policy, but Communications still does not create permanent responder identities.

If an emergency vehicle transmits a compatible authenticated V2X message, Communications may carry that message and preserve the transmitting session/peer information required for bounded delivery and replay protection.

If the emergency vehicle does not transmit compatible data, passive local sensing may still classify or re-identify it for same-trip safety awareness, but that recognition remains outside Communications.

## Discovery law

**Discovery is not trust.**

For Velvet-native peers, discovery may reveal a candidate compatible endpoint. Stable trust requires a separate approved relationship process.

For standards-speaking non-Velvet vehicles, receipt of a valid standards message does not make that vehicle part of the local Velvet body.

For non-transmitting vehicles, there is no communications identity at all.

## Ephemeral identifiers

Communications should prefer short-lived session/routing identifiers wherever a stable relationship is not required.

Carrier addresses such as radio node IDs, network addresses, Meshtastic identifiers, temporary V2X identifiers, or future transport-specific addresses must not silently become long-term person/vehicle identities.

## Cross-repo ownership

- `velvet-ai-core`: passive encounter interpretation and privacy/retention policy.
- `velvet-event-protocol`: meaning and structure of governed events.
- `velvet-communications`: cooperative V2V/V2X envelope delivery, routing, retries, TTL, replay handling, store-and-forward, and transport adapters.
- Runtime/Court: consequential authority and action validation.
- Receipts: bounded evidence where required.

## Design law

**Communications recognizes peers that communicate. Perception recognizes things that are observed. Neither layer may quietly turn the other into persistent tracking.**
