# Headless Node Stack Boundary

A Velvet headless Linux organ should remain small and role-specific. The common stack is:

```text
minimal Linux
  -> Velvet specialist Runtime agent
  -> Velvet Communications carrier
  -> health/resource observations
  -> reviewed role handlers/adapters
```

The node does not need a desktop environment or local Velvet UI. Any operator-facing state may be surfaced later through Founder's normal interface.

## Ownership

- `velvet-runtime` owns specialist coordination, bounded work contracts, node health, resource observations, and local process lifecycle.
- `velvet-communications` owns the carrier that moves approved opaque payloads between physical hosts.
- Runtime/Court on the governing body retains authority and execution policy.
- Hardware-specific sensor/actuator adapters remain separate from transport and do not gain authority because they run on a node.

This allows the same deployment model to cover Lyra-class SBCs, Raspberry Pi-class nodes, reused laptops, mini-PCs, and future Velvet-specific Linux boards without hard-coding a board model into the protocol.
