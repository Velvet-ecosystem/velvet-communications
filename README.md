# Velvet Communications

**Transport-neutral communications and Velvet-to-Velvet federation for the Velvet ecosystem.**

Velvet Communications is the layer that moves bounded Velvet messages between nodes, bodies, and deployments without confusing connectivity with trust or authority.

Its central rule is simple:

> **The message belongs to Velvet. The carrier is replaceable.**

A V2V envelope may travel over local Ethernet, Wi-Fi, Tailscale, direct LoRa, Meshtastic, a private LoRaWAN/ChirpStack deployment, serial, cellular, or another approved carrier. Changing the carrier must not silently change peer identity, trust, message meaning, execution authority, or disclosure scope.

## Privacy posture

Velvet's ability to use many carriers does **not** mean Velvet is always transmitting owner information.

> **Connectivity is a capability, not consent.**

Normal operation is private/local by default. A reachable cellular, Internet, Home, phone, mesh, or radio path does not authorize continuous location upload, owner tracking, cabin telemetry, medical-state export, route-history export, or background cloud reporting.

External transmission should happen because an enabled capability has a defined purpose, destination, disclosure class, lifetime, and policy basis.

A confirmed emergency may justify a narrowly scoped disclosure that would not be appropriate during ordinary operation. That exception is incident-scoped and should end at stand-down. It must not silently become permanent monitoring or a new standing telemetry relationship.

Beacon of Hope and Owner Emergency Bridge exist to provide **more ways to reach help, not more ways to track the owner**.

See [`docs/PRIVACY_AND_DISCLOSURE_DOCTRINE.md`](docs/PRIVACY_AND_DISCLOSURE_DOCTRINE.md).

## What this repository owns

- V2V transport-neutral envelopes
- peer addressing for delivery
- transport capability descriptions
- policy-driven transport selection
- constrained/degraded-link routing
- bounded retries, acknowledgements, TTL, and hop policy
- communications-layer duplicate/replay suppression
- bounded store-and-forward queues
- adapter contracts for IP, direct LoRa, Meshtastic, LoRaWAN, serial, and future carriers
- delivery/degradation evidence contracts

## What this repository does not own

- Event Protocol event meaning or local message-bus semantics
- Riven identity roots or continuity lineage
- Runtime coordination or Court authority
- capability grants or executor selection
- canonical Receipts
- physical control
- Home deployment policy
- radio hardware-specific wiring or regional RF configuration

`velvet-event-protocol` defines what a Velvet event means inside a governed body. `velvet-communications` defines how an approved payload can be carried between endpoints and separately governed bodies.

## V2V model

V2V means **verified peer-to-peer communication between compatible governed bodies**. It is federation, not body merging.

```text
Velvet body A
    |
Event Protocol / approved payload
    |
V2V envelope
    |
transport selection
    |
LAN / Tailscale / LoRa / Meshtastic / LoRaWAN / future carrier
    |
V2V envelope
    |
identity + relationship + Runtime/Court checks
    |
Velvet body B
```

Discovery is not trust. A heard radio node, visible LAN service, mesh participant, or reachable Tailscale peer is only a reachable endpoint until the normal Velvet identity and relationship path accepts it.

## Current foundation

The first implementation slice is intentionally transport-neutral. It provides:

- `V2VEnvelope`: bounded cross-node delivery metadata plus an opaque payload
- `TransportOffer`: one carrier's current capabilities and limits
- `TransportSelector`: chooses an eligible healthy carrier without granting authority
- `ReplayGuard`: bounded duplicate suppression at the communications boundary
- `StoreAndForwardQueue`: bounded expiring delivery when no suitable path exists
- `TransportAdapter`: protocol contract for concrete carrier adapters

There is deliberately no radio driver or network daemon in the foundation. Hardware adapters arrive only after the physical carrier is selected and tested.

## Intended transport families

### Local IP / secure overlay

Ethernet, Wi-Fi, and approved secure overlays such as Tailscale are preferred when healthy because they can carry richer payloads and larger transfers.

### Direct LoRa

A direct LoRa adapter can provide compact private point-to-point messaging when ordinary IP paths disappear. Velvet owns framing above the radio and must provide replay handling, addressing, bounded retries, and application protection appropriate to the deployment.

### Meshtastic

Meshtastic is an optional off-grid mesh carrier. Its node/channel objects stay behind an adapter. Velvet services should receive the same V2V envelope regardless of whether Meshtastic, direct LoRa, or IP carried it.

### Private LoRaWAN / ChirpStack

A private LoRaWAN deployment can support larger sensor estates and gateway-based coverage while keeping the network server local. LoRaWAN does not replace V2V peer semantics and does not automatically make end devices trusted Velvet peers.

## Degraded mode

Loss of bandwidth must reduce what can be carried, not increase authority.

When only a constrained radio path remains, Communications should favor compact traffic such as:

- health and heartbeat summaries
- short alerts and acknowledgements
- low-rate sensor observations
- presence/location beacons where policy permits
- rendezvous information
- store-and-forward coordination

Video, audio streams, bulk logs, model transfers, software updates, and tight control loops do not belong on a LoRa-class fallback path.

## Authority boundary

A valid communications envelope proves only that a packet passed the communications contract. It is **not** permission to act.

Incoming traffic remains untrusted input until the receiving body performs its normal identity, relationship, Event Protocol, Runtime, Court, capability, safety, and receipt checks.

A relay forwards. It does not inherit authority.

A gateway bridges. It does not upgrade trust.

A transport connects. It does not create membership.

## Relationship to Velvet Home

Velvet Home can host persistent V2V endpoints, rendezvous services, store-and-forward queues, Library services, and radio gateways. Those are deployment roles. Home does not own the shared V2V contracts.

Likewise, a vehicle, cyberdeck, mobile companion, SBC, reused laptop, or future body can implement the same Communications contracts with different physical carriers.

## Status

Private development repository while the V2V communications foundation is corrected, tested, and aligned with the existing Home/Event Protocol boundaries.

## License

GPLv3. Part of the Velvet ecosystem.
