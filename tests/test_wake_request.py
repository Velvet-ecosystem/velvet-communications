import json

import pytest

from velvet_communications import Priority
from velvet_communications.wake import (
    MAX_WAKE_REQUEST_TTL_MS,
    WAKE_REQUEST_PAYLOAD_TYPE,
    WakeReason,
    WakeRequest,
    WakeSeverity,
    build_wake_envelope,
    new_wake_request,
    wake_request_from_envelope,
)


def request(**overrides):
    values = {
        "source_peer_id": "security-lyra-1",
        "target_body_id": "velvet-body",
        "reason": WakeReason.SECURITY_VIDEO_ANOMALY,
        "severity": WakeSeverity.URGENT,
        "observed_at_ms": 10_000,
        "ttl_ms": 30_000,
        "evidence_refs": ("video:clip-001", "event:security-001"),
        "summary": "Sustained motion at the driver-side glass.",
        "request_id": "wake-security-001",
    }
    values.update(overrides)
    return new_wake_request(**values)


def test_wake_request_round_trip_preserves_reason_and_evidence():
    original = request()
    decoded = WakeRequest.from_payload(original.to_payload())

    assert decoded == original
    assert decoded.reason is WakeReason.SECURITY_VIDEO_ANOMALY
    assert decoded.evidence_refs == ("video:clip-001", "event:security-001")
    assert decoded.authority == "none"
    assert decoded.grants_authority is False
    assert decoded.grants_execution is False
    assert decoded.grants_actuation is False


def test_wake_envelope_is_bounded_acknowledged_and_urgent():
    original = request()
    envelope = build_wake_envelope(original, destination_peer_id="power-supervisor")

    assert envelope.payload_type == WAKE_REQUEST_PAYLOAD_TYPE
    assert envelope.source_peer_id == "security-lyra-1"
    assert envelope.destination_peer_id == "power-supervisor"
    assert envelope.priority is Priority.URGENT
    assert envelope.ack_required is True
    assert envelope.hop_limit == 2
    assert wake_request_from_envelope(envelope, now_ms=20_000) == original


def test_attention_wake_uses_important_priority():
    envelope = build_wake_envelope(
        request(severity=WakeSeverity.ATTENTION),
        destination_peer_id="power-supervisor",
    )
    assert envelope.priority is Priority.IMPORTANT


def test_expired_wake_request_is_rejected_at_envelope_ingress():
    envelope = build_wake_envelope(request(), destination_peer_id="power-supervisor")
    with pytest.raises(ValueError, match="expired"):
        wake_request_from_envelope(envelope, now_ms=40_000)


def test_wake_request_ttl_is_capped():
    with pytest.raises(ValueError, match="ttl_ms"):
        request(ttl_ms=MAX_WAKE_REQUEST_TTL_MS + 1)


def test_payload_rejects_authority_smuggling():
    raw = json.loads(request().to_payload().decode("utf-8"))
    raw["grants_actuation"] = True
    payload = json.dumps(raw).encode("utf-8")

    with pytest.raises(ValueError, match="grants_actuation"):
        WakeRequest.from_payload(payload)


def test_payload_rejects_unknown_fields():
    raw = json.loads(request().to_payload().decode("utf-8"))
    raw["gpio"] = 17
    with pytest.raises(ValueError, match="unsupported fields"):
        WakeRequest.from_payload(json.dumps(raw).encode("utf-8"))


def test_evidence_references_are_compact_and_unique():
    with pytest.raises(ValueError, match="duplicates"):
        request(evidence_refs=("video:clip-001", "video:clip-001"))
    with pytest.raises(ValueError, match="invalid"):
        request(evidence_refs=("x" * 161,))


def test_source_and_request_id_must_match_envelope():
    envelope = build_wake_envelope(request(), destination_peer_id="power-supervisor")
    altered = type(envelope)(
        message_id=envelope.message_id,
        source_peer_id="other-node",
        destination_peer_id=envelope.destination_peer_id,
        payload_type=envelope.payload_type,
        payload=envelope.payload,
        created_at_ms=envelope.created_at_ms,
        ttl_ms=envelope.ttl_ms,
        priority=envelope.priority,
        ack_required=envelope.ack_required,
        hop_limit=envelope.hop_limit,
    )
    with pytest.raises(ValueError, match="source"):
        wake_request_from_envelope(altered)
