import pytest

from velvet_communications import (
    NoEligibleTransport,
    Priority,
    ReplayGuard,
    StoreAndForwardQueue,
    TransportKind,
    TransportOffer,
    TransportSelector,
    V2VEnvelope,
)


def envelope(**overrides):
    values = {
        "message_id": "msg-001",
        "source_peer_id": "tibby-founder",
        "destination_peer_id": "home-founder",
        "payload_type": "velvet.event.v1",
        "payload": b'{"type":"HEALTH"}',
        "created_at_ms": 1_000,
        "ttl_ms": 10_000,
        "priority": Priority.NORMAL,
    }
    values.update(overrides)
    return V2VEnvelope(**values)


def offer(name, kind, preference, **overrides):
    values = {
        "name": name,
        "kind": kind,
        "available": True,
        "max_payload_bytes": 4096,
        "preference": preference,
        "protected_path": True,
        "supports_ack": True,
    }
    values.update(overrides)
    return TransportOffer(**values)


def test_ip_is_preferred_when_healthy():
    plan = TransportSelector().select(
        envelope(),
        (
            offer("lora-backup", TransportKind.LORA_P2P, 40),
            offer("tailscale", TransportKind.IP, 10),
        ),
    )
    assert plan.transport_name == "tailscale"
    assert plan.degraded is False
    assert plan.authority == "none"


def test_lora_fallback_is_degraded_not_more_authoritative():
    plan = TransportSelector().select(
        envelope(),
        (
            offer("ethernet", TransportKind.IP, 1, available=False),
            offer("lora-backup", TransportKind.LORA_P2P, 50),
        ),
    )
    assert plan.transport_name == "lora-backup"
    assert plan.degraded is True
    assert plan.authority == "none"


def test_payload_limit_blocks_constrained_carrier():
    with pytest.raises(NoEligibleTransport):
        TransportSelector().select(
            envelope(payload=b"x" * 512),
            (offer("meshtastic", TransportKind.MESHTASTIC, 10, max_payload_bytes=128),),
        )


def test_ack_required_rejects_carrier_without_ack_support():
    with pytest.raises(NoEligibleTransport):
        TransportSelector().select(
            envelope(ack_required=True),
            (offer("radio", TransportKind.LORA_P2P, 1, supports_ack=False),),
        )


def test_unprotected_path_rejected_by_default():
    with pytest.raises(NoEligibleTransport):
        TransportSelector().select(
            envelope(),
            (offer("open-radio", TransportKind.LORA_P2P, 1, protected_path=False),),
        )


def test_envelope_expiry_is_transport_independent():
    msg = envelope(created_at_ms=1000, ttl_ms=5000)
    assert msg.is_expired(5999) is False
    assert msg.is_expired(6000) is True


def test_replay_guard_rejects_duplicate_and_is_bounded():
    guard = ReplayGuard(capacity=2)
    assert guard.accept("m1") is True
    assert guard.accept("m1") is False
    assert guard.accept("m2") is True
    assert guard.accept("m3") is True
    assert len(guard) == 2
    assert guard.accept("m1") is True


def test_store_and_forward_queue_is_bounded_and_prunes_expired():
    queue = StoreAndForwardQueue(capacity=1, max_payload_bytes=1024)
    queue.enqueue(envelope(message_id="m1", created_at_ms=1000, ttl_ms=1000), 1100)
    with pytest.raises(OverflowError):
        queue.enqueue(envelope(message_id="m2"), 1100)
    assert queue.prune(2000) == 1
    queue.enqueue(envelope(message_id="m2"), 2000)
    assert queue.pop_next(2000).message_id == "m2"


def test_invalid_peer_identifier_is_rejected():
    with pytest.raises(ValueError):
        envelope(source_peer_id="not a valid peer id")
