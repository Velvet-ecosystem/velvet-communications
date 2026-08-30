# Transport Adapters

Concrete carriers implement the shared `TransportAdapter` boundary. Higher Velvet logic should not depend directly on Meshtastic objects, LoRaWAN gateway APIs, socket details, serial device paths, or modem-specific state.

## Adapter contract

An adapter exposes two basic operations:

- `offer()` reports current bounded carrier capability and health through `TransportOffer`.
- `send(envelope)` attempts delivery and returns a `DeliveryReport` without interpreting payload authority.

Future receive-side adapters should reconstruct the same `V2VEnvelope` before handing traffic upward.

## Direct LoRa / P2P

Expected responsibilities include:

- carrier-specific framing beneath the V2V envelope;
- explicit regional configuration supplied by deployment policy;
- bounded packet fragmentation only if deliberately specified;
- retries and acknowledgements within declared limits;
- application protection appropriate to the deployment;
- health/degradation reporting;
- no automatic peer trust from hearing a radio address.

The shared repository must not hard-code a worldwide frequency, radio chipset, USB/serial path, antenna, or transmit power.

## Meshtastic

A Meshtastic adapter may use supported serial, TCP, BLE, or other client interfaces, but Meshtastic node/channel concepts stay behind the adapter boundary.

The adapter should map current carrier facts into `TransportOffer` and deliver/reconstruct V2V envelopes. Mesh discovery remains discovery only. Meshtastic membership does not automatically establish Velvet peer trust.

## Private LoRaWAN / ChirpStack

A LoRaWAN adapter may integrate with a local/private ChirpStack deployment for gateway and low-power sensor coverage.

LoRaWAN device identity and network admission are not automatically equivalent to a V2V peer relationship. Sensor-only endpoints may remain bounded devices rather than full peer bodies.

## IP / secure overlay

An IP adapter can represent local Ethernet/Wi-Fi or a protected overlay such as Tailscale. IP is normally preferred for larger payloads and richer service interactions when healthy.

Transport reachability still does not create Velvet trust. A reachable IP endpoint must pass the same peer relationship and receiving-body validation as a radio endpoint.

## Adapter promotion tests

A concrete adapter should not be promoted merely because two machines exchange bytes. At minimum, test:

- send/receive of a V2V envelope;
- peer routing identity surviving carrier changes;
- maximum payload enforcement;
- duplicate/replay handling;
- bounded retry behavior;
- bounded queue behavior when unavailable;
- loss/recovery health evidence;
- ACK behavior where declared;
- no authority expansion during fallback;
- no automatic registration of unknown peers;
- reconnect without duplicate consequential action after Runtime validation.
