# Headless Local-IP Carrier

The first headless-node IP carrier is intentionally small and transport-only. It is intended for Velvet specialist nodes such as Luckfox Lyra-class Linux organs that need to exchange bounded V2V envelopes with Founder without acquiring Runtime, Court, or physical-control authority.

## What it provides

`AuthenticatedLocalIpAdapter` and `AuthenticatedLocalIpServer` provide:

- TCP delivery over a configured local/private IP path;
- HMAC-SHA256 peer authentication and frame integrity;
- bounded length-prefixed canonical JSON frames;
- per-message TTL and clock-skew checks;
- communications-layer duplicate suppression;
- authenticated acknowledgements;
- locked deployment-local peer-secret loading;
- Python 3.8-compatible standard-library implementation.

No network discovery is performed. Peer ID, host, port, and secret material are explicitly provisioned.

## What it does not provide

HMAC does **not** encrypt the payload. Therefore raw Ethernet should not be presented to higher layers as a confidential/protected path.

`AuthenticatedLocalIpAdapter(..., confidential_underlay=False)` advertises:

```text
protected_path = false
```

Set `confidential_underlay=True` only when the TCP connection is already carried by a reviewed confidential underlay such as Tailscale, WireGuard, a VPN, or another encrypted transport appropriate to the deployment.

The carrier never grants:

- body membership;
- Riven identity;
- Court approval;
- Runtime authority;
- execution or actuation permission.

## Secret files

Peer secrets belong outside Git. `load_secret_file()` requires a regular, non-symlink file with no group or other permission bits and a secret between 32 and 4096 bytes.

Example deployment shape:

```text
/var/lib/velvet/secrets/communications/
  founder--velour-lyra-1.secret   mode 0600
```

The same secret must be provisioned at both ends for this initial symmetric peer channel. Later certificate or hardware-backed identity adapters may replace this carrier without changing V2V envelope semantics.

## Headless-node posture

The carrier deliberately has no GUI, HTTP dashboard, browser dependency, service discovery daemon, model runtime, or external Python dependency. Node state can later be surfaced through Founder/Velvet's normal UI when desired.

The next integration layer is Runtime-over-Communications: existing Runtime specialist RPC payloads are carried as opaque approved V2V payloads so a physical headless node no longer depends on Founder's AF_UNIX socket being on the same host.
