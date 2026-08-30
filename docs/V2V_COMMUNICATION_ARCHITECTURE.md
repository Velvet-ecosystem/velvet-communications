# V2V Communication Architecture

## Purpose

Velvet Communications provides the shared communications boundary between a governed Velvet payload and the carrier that moves it to another node or separately governed body.

The architecture separates four questions:

1. What does the payload mean? `velvet-event-protocol` and the owning domain define that.
2. Who is the peer? Identity/relationship systems establish that independently of network or radio addresses.
3. How can the payload move right now? `velvet-communications` selects and manages an eligible carrier.
4. May the receiver act on it? Runtime, Court, capability policy, safety, and executors decide that after receipt.

## Layering

```text
approved Velvet payload
        |
        v
V2VEnvelope
  message id
  source/destination peer routing ids
  payload type
  TTL / priority / ACK / hop limits
  opaque payload bytes
        |
        v
transport selection
        |
  +-----+---------+-------------+-------------+
  |     |         |             |             |
 IP  LoRa P2P  Meshtastic   LoRaWAN      future carrier
  |     |         |             |             |
  +-----+---------+-------------+-------------+
        |
        v
receiving communications boundary
  duplicate / expiry / size checks
        |
        v
normal receiving-body validation
  identity / relationship / Event Protocol / Runtime / Court
```

## Peer routing IDs

The envelope carries source and destination peer IDs so Communications can route a message without depending on carrier-specific addresses.

A peer routing ID is not a Riven identity root, credential, capability token, trust decision, or owner relationship. A concrete deployment may bind the routing ID to stronger identity evidence elsewhere.

This separation lets the same peer relationship survive a carrier change from Ethernet to Tailscale to LoRa without pretending a new radio address is a new identity.

## Transport offers

Each carrier reports a `TransportOffer` describing current bounded facts such as:

- carrier kind
- availability
- maximum accepted payload size
- preference order
- whether the configured path satisfies required communications protection
- acknowledgement support
- store-and-forward support

The selector may use those facts to choose a path. It does not infer trust or permission from them.

## Degraded links

Direct LoRa, Meshtastic, and LoRaWAN are treated as constrained links in the initial foundation. Selecting one marks the delivery plan as degraded so higher layers can reduce optional traffic without changing message authority.

An unavailable high-bandwidth path can therefore fall back to radio for eligible compact traffic while oversized or unsupported traffic fails bounded or enters store-and-forward policy.

## Replay and duplicate boundary

`ReplayGuard` suppresses duplicate message IDs at the Communications boundary. Its purpose is to avoid repeated delivery caused by carrier retries, reconnects, relays, or duplicate radio packets.

It is not the Runtime consequential-action replay ledger. If a received message requests an action, the receiving Runtime still applies its own replay/authorization controls.

## Store and forward

`StoreAndForwardQueue` is deliberately bounded by item count, payload size, and envelope TTL. It exists for intermittently reachable peers and degraded networks.

Queueing never extends an envelope's lifetime, raises priority, or grants authority. Expired messages are discarded rather than resurrected when connectivity returns.

## Relays and gateways

A future relay may forward an eligible V2V envelope without understanding or gaining its authority. A gateway may bridge two carriers without changing the peer relationship.

Relay is not authority. Gateway is not trust upgrade.

## Home relationship

Velvet Home may host persistent endpoints, gateways, rendezvous services, and store-and-forward queues because Home is often powered and reachable. Those are deployment roles. Shared V2V contracts remain owned by `velvet-communications` so vehicle, cyberdeck, mobile, Home, and future bodies can interoperate.
