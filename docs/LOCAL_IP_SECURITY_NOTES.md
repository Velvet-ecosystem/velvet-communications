# Local-IP Security Notes

The initial authenticated local-IP carrier is a deliberately small first transport for physical headless nodes.

HMAC-SHA256 provides peer-secret authentication and frame integrity. It does not provide confidentiality. The adapter therefore reports `protected_path=false` on raw Ethernet and may report `protected_path=true` only when configuration explicitly declares that the connection is already carried inside a reviewed confidential underlay.

This distinction is intentional. A reachable private LAN is not automatically a privacy boundary, and communications reachability never creates body membership or execution authority.

Deployment secrets must remain outside the repository and locked to the service identity. Long-term deployments may replace the symmetric carrier with mutually authenticated TLS, WireGuard/Tailscale identity, hardware-backed keys, or another reviewed carrier while retaining the same V2V envelope and Runtime authority boundaries.
