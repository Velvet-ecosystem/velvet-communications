# Authenticated local-IP request/reply

The ordinary Velvet local-IP carrier is delivery-oriented: send one V2V envelope and receive an authenticated acknowledgement.

Some reviewed headless-node protocols need a small structured response body. Distributed Runtime registration and work coordination are examples. `local_ip_rpc.py` adds that response body without creating a second authority model or a second network security scheme.

## Boundary

```text
V2V request envelope
  -> existing HMAC-authenticated local-IP delivery frame
  -> reviewed receiver
  -> bounded reply bytes
  -> HMAC-authenticated acknowledgement containing reply bytes
```

The reply is transport data only. It never grants Runtime, Court, execution, or actuation authority.

## Limits

- existing request payload limit remains in force
- default reply payload limit is 64 KiB
- reply size must fit inside the configured signed frame after base64 expansion
- reply detail is limited to 256 characters
- request IDs remain replay/content bound

A duplicate request with identical content returns the cached original reply without calling the receiver again. Reusing a message ID with different content is rejected.

## Security posture

Request and reply bytes are authenticated and integrity protected with the same per-peer HMAC secret as the local-IP carrier. They are not encrypted by HMAC. Confidentiality still requires a reviewed encrypted underlay such as WireGuard/Tailscale or another encrypted transport path.

## Intended use

This mechanism is intended for compact machine protocols such as Runtime's existing distributed-work RPC. It is not a general remote shell, file transfer channel, browser API, or arbitrary command tunnel.
