# Public Release Readiness and Record

Velvet Communications is published as a transport-neutral alpha foundation without pretending that every physical carrier has already been implemented or validated.

## Public release boundary

The public foundation includes:

- bounded V2V delivery envelopes;
- transport capability descriptions and selection;
- degraded-link routing policy;
- bounded retries, TTL, hop limits, replay suppression, and store-and-forward behavior;
- carrier-neutral adapter contracts;
- direct LoRa, Meshtastic, private LoRaWAN/ChirpStack, local IP, secure-overlay, serial, cellular, and future-carrier architecture boundaries;
- Beacon of Hope emergency-fallback contracts and truth semantics;
- privacy and disclosure doctrine;
- explicit separation between connectivity, peer reachability, trust, and execution authority;
- public-safe security and contribution guidance.

## What public release does not claim

Publishing this repository does **not** claim:

- a finished LoRa, Meshtastic, LoRaWAN, cellular, or other physical carrier driver;
- universal RF configuration or regulatory suitability;
- production deployment readiness for every transport;
- responder, owner, or peer identity merely because a network endpoint is reachable;
- Runtime or Court authority;
- vehicle, Home, radio, or other physical-control authority;
- proof that an emergency destination received a message merely because a carrier attempted transmission.

The architecture is intentionally useful before the first physical radio adapter lands. Concrete adapters must preserve these contracts rather than redefine them.

## Privacy release posture

The public doctrine is deliberately explicit:

**Connectivity is a capability, not consent.**

Public source code does not imply public owner data. Deployment credentials, private peer relationships, location histories, medical state, private traffic captures, runtime queues, secrets, and deployment-local topology do not belong in repository history.

See:

- `SECURITY.md`
- `docs/PRIVACY_AND_DISCLOSURE_DOCTRINE.md`

## Release verification

Completed:

- [x] V2V/transport mission corrected and documented
- [x] Event Protocol, Runtime/Court, Receipts, Riven, Home, and physical-control ownership boundaries documented
- [x] privacy-by-default communications doctrine present
- [x] public-safe `SECURITY.md`
- [x] public-safe `CONTRIBUTING.md`
- [x] GPLv3 license present
- [x] package metadata describes the current V2V transport role
- [x] emergency fallback semantics distinguish send, heard/relay, and upstream acknowledgement truth
- [x] future Owner Emergency Bridge is tracked as roadmap work rather than represented as implemented
- [x] current release posture makes physical-carrier limitations explicit
- [x] obsolete merged development branches removed before release
- [x] fresh full-history TruffleHog scan run against release-prepped `main`
- [x] scan result: 0 verified secrets and 0 unverified secrets
- [x] repository visibility changed to public
- [x] public README and release-facing repository content verified

Post-release housekeeping:

- [ ] remove the temporary `security/final-public-history-scan-20260831` branch after preserving the scan result in PR #11
- [ ] apply/verify the intended `main` protection posture for this public repository

The final scan used TruffleHog 3.97.1 with full Git history (`fetch-depth: 0`), `--results=verified,unknown`, and `--fail`. It scanned 63 chunks / 115,509 bytes and reported 0 verified secrets and 0 unverified secrets.

A code-search result was not used as a substitute for the full-history secret scan.

## Open roadmap is allowed

Public release does not require every planned carrier or emergency feature to be finished.

In particular, the future Owner Emergency Bridge may remain an open issue. It is a roadmap capability with explicit authority and privacy boundaries, not evidence of an incomplete release contract.

Likewise, physical LoRa/Meshtastic proof is a valuable next validation milestone but is not required to publish the transport-neutral architecture honestly.

## Release law

**Publish the contract we can defend, label the hardware we have not yet proved, and never let connectivity masquerade as authority or consent.**
