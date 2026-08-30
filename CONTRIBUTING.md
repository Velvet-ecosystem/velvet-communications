# Contributing

Velvet Communications is the shared transport-neutral layer for Velvet-to-Velvet and cross-node communication.

Contributions must preserve these boundaries:

- Event Protocol owns event/message meaning inside a governed body;
- Runtime and Court own coordination and authority;
- Riven/Continuity owns identity lineage;
- Receipts owns canonical evidence;
- Home, vehicle, cyberdeck, and other bodies may host adapters but do not fork the shared Communications contracts;
- transport discovery never implies trust or membership;
- transport fallback never expands authority;
- relays and gateways do not inherit message authority;
- communications replay suppression does not replace Runtime consequential-action replay protection.

Transport adapters should expose carrier capabilities behind the common interface rather than leak Meshtastic-, LoRaWAN-, modem-, socket-, or radio-specific objects into higher Velvet logic.

New carrier integrations should include tests for payload limits, unavailable/degraded paths, duplicate handling, bounded retries or queue behavior, and safe failure. Public examples must use synthetic peer identities, addresses, keys, and traffic.
