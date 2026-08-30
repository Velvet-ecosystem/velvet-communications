# Beacon of Hope

## Canonical name

**Beacon of Hope** is the human-facing name for Velvet's off-grid emergency fallback path.

The stable wire contract remains `velvet.emergency.beacon.v1`; naming the capability does not change the protocol schema, routing destination, authority model, or interoperability rules.

## Purpose

Velvet Communications may provide a best-effort degraded emergency path when normal cellular, Internet, trusted-IP, or known-peer routes are unavailable.

The fallback is intended for compact distress traffic over explicitly enabled constrained carriers such as direct LoRa, Meshtastic, or private LoRaWAN/ChirpStack paths.

It is not a substitute for emergency-service networks and does not imply that a public-safety agency can receive arbitrary LoRa traffic.

## Core rule

**No acknowledgement means no delivery claim.**

A successful adapter send means only that Velvet attempted transmission through that carrier. Velvet must not say that emergency services, a responder, or another person received the message unless an acknowledgement or other receipt proves it.

## Route order

For an active incident, higher layers should normally prefer:

1. configured cellular or Internet emergency path;
2. protected local/trusted IP;
3. known trusted V2V peers or gateways;
4. protected constrained radio paths;
5. explicitly enabled public Beacon of Hope fallback.

Deployment policy may attempt more than one eligible route when an incident justifies redundancy, but each route remains separately bounded and receipted.

## Public emergency beacon exception

Normal Communications traffic requires a protected path by default. The public Beacon of Hope exception is deliberately narrower.

An unprotected constrained carrier may be considered only when all of the following are true:

- the owning emergency domain has created a deliberately public-safe beacon payload;
- the payload type is `velvet.emergency.beacon.v1`;
- the routing destination is `broadcast.emergency`;
- the message priority is `urgent`;
- payload size is at most 384 bytes;
- TTL is at most five minutes;
- hop limit is at most three;
- deployment policy explicitly enables unprotected emergency broadcast;
- the concrete adapter is configured for the legal regional radio plan and local duty-cycle/power limits.

This exception does not apply to arbitrary V2V events, general IP traffic, model data, medical records, raw media, owner identity data, or control requests.

## What may be public

Communications treats the payload as opaque. The owning medical/incident domain must ensure that a public beacon contains only the minimum information intentionally approved for open transmission.

Typical public-safe content may include an ephemeral incident identifier, distress category, timestamp, location at the configured emergency precision, vehicle description, assistance requested, and a request for compatible relays.

Names, detailed medical history, medications, credentials, general memory, raw cabin media, and unrelated receipts should remain off an unprotected carrier unless a separate explicit emergency-disclosure policy says otherwise.

## Relay behavior

A compatible Velvet peer may receive a Beacon of Hope and, if its own policy permits, relay it through a healthier carrier. Relay does not make the sender trusted and does not authorize any action on the receiving body.

A relay should preserve the original incident/message identity, bounded TTL, and provenance, and should emit its own delivery evidence. Relays must not silently enlarge the payload, retention, authority, or disclosure scope.

Future relay acknowledgement may distinguish:

- `heard`: compatible peer received the beacon;
- `relay-accepted`: peer accepted it for bounded forwarding;
- `upstream-acknowledged`: a configured destination acknowledged the relayed request.

Only the last category can support a claim that an upstream configured destination actually received it.

## Cancellation and expiry

Beacon of Hope transmissions must expire quickly. Stand-down, incident cancellation, a successful authoritative emergency contact, or policy change should stop new fallback attempts where safe to do so.

Radio retries remain adapter/deployment policy because legal airtime and duty-cycle limits vary by region and carrier. Shared Communications code must not hard-code a worldwide frequency, transmit power, cadence, spreading factor, or channel.

## Security and privacy

Open fallback is an exposure decision, not a trust decision.

The path must preserve these boundaries:

- open radio does not grant responder identity;
- hearing a beacon does not grant access to the vehicle;
- a relay does not receive Runtime/Court authority;
- a radio address does not become a permanent person or vehicle identity;
- consequential response still requires normal receiving-body validation;
- incident evidence records attempts and acknowledgements truthfully.

## Validation

Before a concrete emergency radio adapter is promoted, test at minimum:

- protected route preferred when healthy;
- open radio unavailable unless explicitly enabled;
- ordinary payload cannot use the exception;
- oversized, long-lived, or over-hopped beacons are refused;
- open IP does not become a generic emergency bypass;
- no ACK produces no delivery claim;
- duplicate/replay suppression survives carrier retries;
- bounded retries obey deployment airtime policy;
- relay preserves TTL and incident identity;
- stand-down stops further attempts;
- failover never expands vehicle or medical authority.
