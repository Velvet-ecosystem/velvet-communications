# Security Policy

Velvet Communications carries messages between nodes and separately governed bodies. Connectivity must never be treated as trust, membership, identity proof, or execution authority.

## Sensitive material

Do not commit:

- radio/network credentials, bearer tokens, private keys, certificates, channel secrets, or device provisioning material;
- private peer relationship records or owner-only policy;
- exact sensitive deployment topology, private addresses, live gateway credentials, or location data;
- runtime databases, queue spools, raw private traffic captures, or production logs;
- deployment-local regional RF configuration when it exposes operational details.

Local peer state, queue/spool data, credentials, and deployment configuration belong outside committed repository content.

## Communications boundary

A valid V2V envelope is transport acceptance only. It does not grant Runtime authority, Court approval, capability access, executor selection, physical-control permission, or membership in the receiving Velvet body.

Required security posture includes:

- stable peer/body identity independent of transport address;
- authenticated/protected application traffic appropriate to the selected carrier;
- bounded payload, queue, retry, TTL, and hop limits;
- duplicate/replay suppression at the communications boundary;
- no automatic trust promotion from discovery;
- no authority expansion when falling back from IP to radio;
- key material stored outside Git;
- explicit regional radio configuration rather than global transmit defaults.

Communications-layer replay handling does not replace Runtime's consequential-action replay protection.

## Reporting a vulnerability

Please avoid posting exploitable security details publicly before maintainers can review them. Use GitHub private vulnerability reporting when available. Otherwise contact maintainers through an appropriate private project channel and include the affected version, reproduction details, impact, and suggested mitigation if known.
