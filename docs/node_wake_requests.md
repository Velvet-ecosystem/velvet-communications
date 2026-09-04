# Node wake requests

Velvet nodes may need to wake a sleeping Founder when something important happens while the primary Runtime is unavailable or suspended. Examples include a security-camera anomaly, tamper event, medical alert, safety condition, node-health failure, owner request, or scheduled work.

This feature deliberately separates **requesting wake** from **power authority**.

```text
sensor / camera / specialist node
        |
        | WakeRequest
        v
Velvet Communications
        |
        | authenticated carrier
        v
Power Supervisor policy
        |
        | fixed reviewed wake capability only
        v
Founder wake input / supported wake mechanism
```

A requesting node never receives Court authority, execution permission, GPIO ownership, relay ownership, or permission to perform work after Founder wakes.

## Request schema

Payload type:

```text
velvet.communications.wake_request.v1
```

A request contains:

- request ID
- source peer ID
- target body ID
- reviewed reason family
- severity
- observed and expiry timestamps
- up to eight compact evidence references
- optional bounded human-readable summary
- explicit non-canonical / no-authority flags

The payload is limited to 4 KiB and no request may live longer than five minutes.

## Reason families

The initial reviewed reasons are:

```text
security_motion
security_tamper
security_forced_entry
security_glass_break
security_video_anomaly
medical_alert
safety_alert
node_health
owner_request
scheduled
```

The reason is evidence for policy. It is not itself permission to wake hardware.

## Evidence references, not evidence payloads

Wake traffic should remain tiny. A camera node should not push a video clip inside the wake request.

Instead:

```text
reason: security_video_anomaly
evidence_refs:
  - video:clip-001
  - event:security-001
```

After Founder is awake, Runtime or Interface may request and display the referenced evidence through an approved read-only path. This keeps constrained carriers usable and avoids unnecessary private-data movement.

## Transport

`build_wake_envelope()` wraps the request in a normal V2V envelope:

- attention -> `IMPORTANT`
- urgent / emergency -> `URGENT`
- acknowledgement required
- hop limit 2
- request lifetime becomes the envelope TTL

Carrier authentication still comes from the selected Communications adapter. A valid wake payload on an unauthenticated path does not magically become trusted.

## Suspend versus fully off

Two hardware states must not be confused.

### Suspend / light sleep

If the platform supports a network or device wake mechanism while the main CPU is suspended, an authenticated node request may feed the reviewed wake path.

### Fully off

When Founder is truly off, Founder Runtime cannot evaluate anything. A separate always-on power supervisor or supported hardware wake controller must own the cold-wake decision and pulse.

That supervisor should have a very narrow fixed policy:

- configured source allow-list
- configured reason allow-list per source
- severity floor
- TTL check
- replay suppression
- rate limit / cooldown
- optional evidence-reference requirement for selected security reasons
- bounded wake pulse
- durable wake-reason record

It must not expose a generic relay command or become a back door around Court.

## Wake reason after boot

The eventual Runtime Power Supervisor should preserve the accepted request so Velvet can truthfully report why she woke, for example:

```text
Wake source: security-lyra-1
Reason: security_video_anomaly
Summary: Sustained motion at the driver-side glass.
Evidence: video:clip-001
```

The Interface may later surface that record on Velvet's existing screen. Headless nodes do not need their own display stack.
