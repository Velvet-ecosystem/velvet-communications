# Privacy and Disclosure Doctrine

## Purpose

Velvet Communications can move information across many carriers. That capability must never be confused with permission to transmit owner information.

Velvet is designed to remain useful while local, offline, disconnected, or selectively connected. A healthy network path is an available capability, not standing consent to upload.

## Core rules

**Connectivity is a capability, not consent.**

**Velvet may know locally without telling remotely.**

**Emergency urgency may change the permitted purpose of a disclosure. It does not transfer ownership of the owner's information to a carrier, vendor, relay, or service.**

## Private by default

Normal operation should keep owner, occupant, vehicle, location, health, conversation, and behavioral information local unless an enabled capability has an explicit reason to send a bounded payload to an approved destination.

Shared Communications contracts must not require:

- continuous cloud presence;
- periodic location upload;
- always-on owner or vehicle telemetry to a vendor;
- background export of cabin observations, conversations, health state, driving history, or general memory;
- a remote account merely to preserve core local/off-grid operation;
- carrier-specific analytics as a prerequisite for Velvet-to-Velvet communication.

A deployment may deliberately opt into remote services, but that choice should be explicit, scoped, inspectable, and revocable.

## No ambient tracking by transport

A transport adapter exists to carry approved traffic. It must not quietly become a tracking subsystem.

Merely having cellular, Wi-Fi, Tailscale, LoRa, Meshtastic, LoRaWAN, a paired phone, Home connectivity, or another reachable carrier does not authorize the adapter to publish:

- current or historical location;
- route history;
- owner identity;
- occupancy;
- medical state;
- cabin-derived observations;
- vehicle usage patterns;
- peer encounter history.

Discovery is not tracking permission. Reachability is not disclosure permission. Pairing is not blanket consent.

## Purpose-bound transmission

Every external transmission should be explainable in terms of:

1. what capability requested it;
2. why the transmission is needed;
3. which destination or audience is intended;
4. which disclosure class applies;
5. how long the message remains useful;
6. what acknowledgement, if any, proves reception.

Where practical, Receipts should preserve the fact, purpose, policy basis, destination class, timing, and outcome of a disclosure without unnecessarily duplicating sensitive payload contents.

## Emergency exception

A confirmed life-safety incident may justify transmitting information that Velvet would not ordinarily expose. This is an **incident-scoped disclosure exception**, not a switch into permanent remote monitoring.

The emergency path should disclose progressively:

1. first, the minimum information needed to summon or route help;
2. then, additional incident facts only when a responder, emergency destination, or configured policy legitimately needs them;
3. sensitive details over protected/authenticated paths whenever such a path is available;
4. public/open fallback only with the intentionally minimized public-safe payload.

For example, Beacon of Hope may expose a compact distress request and rescue location during a confirmed emergency while leaving names, general medical history, owner credentials, raw media, and unrelated memory local.

Owner Emergency Bridge may use the owner's phone as a carrier for a richer governed emergency session, but the phone does not gain independent authority to collect or disclose unrelated information.

## Emergency does not mean surveillance

Emergency activation must not silently enable:

- indefinite post-incident tracking;
- unrelated route-history upload;
- general memory export;
- permanent responder or relay trust;
- secondary use of medical or incident data for advertising, profiling, model training, or unrelated analytics;
- a new standing telemetry relationship after the incident ends.

Stand-down should terminate emergency-only disclosure behavior. Retained incident evidence remains governed by the owning domain's retention, export, redaction, and deletion policy.

## Carrier neutrality includes privacy

The rule **"The message belongs to Velvet. The carrier is replaceable."** has a privacy consequence: the carrier transports the approved message; it does not become entitled to the rest of Velvet's state.

Changing from local IP to cellular, an owner's phone, Home, another Velvet, LoRa, Meshtastic, LoRaWAN, or a future carrier must not silently broaden:

- the payload;
- the permitted recipient;
- retention;
- identity exposure;
- location exposure;
- authority;
- secondary use.

A degraded path may require a smaller payload. It must never use degraded connectivity as an excuse for broader disclosure.

## Owner choice

Where the owner is capable and the situation is not an emergency, externally connected features should follow configured owner choices.

Those choices should be understandable at the capability level rather than hidden behind one global "connected services" switch. Examples include separately controlling:

- remote Home access;
- owner-phone relay;
- V2V discovery;
- cooperative location sharing;
- cloud-assisted services;
- telemetry export;
- optional diagnostics upload.

Refusing one remote feature should not disable unrelated local safety or offline capability unless the feature technically requires that remote dependency.

## Truthfulness

Velvet should be able to state what happened without exaggeration:

- `kept local`;
- `prepared for disclosure`;
- `sent to configured destination`;
- `heard by relay`;
- `relay accepted`;
- `upstream acknowledged`;
- `unconfirmed`.

A network path being available is not proof that data was sent. A send attempt is not proof that anyone received it.

## Public-facing distinction

Velvet's off-grid and multi-carrier design should be described clearly:

> **Velvet is not always connected. Velvet is always prepared to communicate when policy and circumstance justify it.**

And the privacy promise underneath that statement is:

> **More ways to reach help do not mean more ways to track the owner.**
