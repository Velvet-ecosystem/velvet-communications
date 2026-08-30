import pytest

from velvet_communications import (
    EMERGENCY_BEACON_PAYLOAD_TYPE,
    EMERGENCY_BROADCAST_DESTINATION,
    EmergencyFallbackPolicy,
    InvalidEmergencyBeacon,
    NoEligibleTransport,
    Priority,
    TransportKind,
    TransportOffer,
    V2VEnvelope,
)


def beacon(**overrides):
    values = {
        "message_id": "incident-001-beacon-1",
        "source_peer_id": "tibby-founder",
        "destination_peer_id": EMERGENCY_BROADCAST_DESTINATION,
        "payload_type": EMERGENCY_BEACON_PAYLOAD_TYPE,
        "payload": b'{"kind":"medical-help","location":"available"}',
        "created_at_ms": 1_000,
        "ttl_ms": 120_000,
        "priority": Priority.URGENT,
        "ack_required": False,
        "hop_limit": 2,
    }
    values.update(overrides)
    return V2VEnvelope(**values)


def offer(name, kind, preference, **overrides):
    values = {
        "name": name,
        "kind": kind,
        "available": True,
        "max_payload_bytes": 512,
        "preference": preference,
        "protected_path": True,
        "supports_ack": False,
    }
    values.update(overrides)
    return TransportOffer(**values)


def test_protected_route_is_preferred_over_open_radio():
    plan = EmergencyFallbackPolicy().select(
        beacon(),
        (
            offer("open-lora", TransportKind.LORA_P2P, 1, protected_path=False),
            offer("protected-mesh", TransportKind.MESHTASTIC, 50, protected_path=True),
        ),
        allow_unprotected_broadcast=True,
    )
    assert plan.transport_name == "protected-mesh"
    assert plan.authority == "none"


def test_open_lora_requires_explicit_emergency_opt_in():
    path = (offer("open-lora", TransportKind.LORA_P2P, 1, protected_path=False),)
    with pytest.raises(NoEligibleTransport):
        EmergencyFallbackPolicy().select(beacon(), path)

    plan = EmergencyFallbackPolicy().select(
        beacon(),
        path,
        allow_unprotected_broadcast=True,
    )
    assert plan.transport_name == "open-lora"
    assert plan.degraded is True
    assert plan.authority == "none"


def test_unprotected_generic_ip_is_not_an_open_emergency_fallback():
    with pytest.raises(NoEligibleTransport):
        EmergencyFallbackPolicy().select(
            beacon(),
            (offer("open-wifi", TransportKind.IP, 1, protected_path=False),),
            allow_unprotected_broadcast=True,
        )


def test_public_beacon_is_tightly_bounded():
    policy = EmergencyFallbackPolicy()
    with pytest.raises(InvalidEmergencyBeacon):
        policy.validate_public_beacon(beacon(priority=Priority.NORMAL))
    with pytest.raises(InvalidEmergencyBeacon):
        policy.validate_public_beacon(beacon(ttl_ms=300_001))
    with pytest.raises(InvalidEmergencyBeacon):
        policy.validate_public_beacon(beacon(hop_limit=4))
    with pytest.raises(InvalidEmergencyBeacon):
        policy.validate_public_beacon(beacon(payload=b"x" * 385))


def test_non_emergency_payload_cannot_use_public_exception():
    with pytest.raises(InvalidEmergencyBeacon):
        EmergencyFallbackPolicy().select(
            beacon(payload_type="velvet.event.v1"),
            (offer("open-lora", TransportKind.LORA_P2P, 1, protected_path=False),),
            allow_unprotected_broadcast=True,
        )


def test_broadcast_destination_is_required():
    with pytest.raises(InvalidEmergencyBeacon):
        EmergencyFallbackPolicy().validate_public_beacon(
            beacon(destination_peer_id="some-random-peer")
        )
