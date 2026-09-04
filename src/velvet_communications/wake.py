"""Bounded authority-free wake requests for Velvet body nodes.

A wake request is evidence that a reviewed node believes the sleeping body should
become available. It is not power authority, Court approval, owner identity, or
permission to perform any action after wake.

The request intentionally carries compact evidence references instead of large
artifacts such as video. A receiving power supervisor may apply its own fixed
allow-list, rate-limit, and hardware policy before pulsing a wake input.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple

from .contracts import Priority, V2VEnvelope


WAKE_REQUEST_SCHEMA = "velvet.communications.wake_request.v1"
WAKE_REQUEST_PAYLOAD_TYPE = WAKE_REQUEST_SCHEMA
MAX_WAKE_REQUEST_TTL_MS = 5 * 60 * 1000
MAX_WAKE_EVIDENCE_REFS = 8
MAX_WAKE_EVIDENCE_REF_CHARS = 160
MAX_WAKE_SUMMARY_CHARS = 256
MAX_WAKE_PAYLOAD_BYTES = 4096
_WAKE_HOP_LIMIT = 2
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class WakeReason(str, Enum):
    """Reviewed reason families that may be considered by power policy."""

    SECURITY_MOTION = "security_motion"
    SECURITY_TAMPER = "security_tamper"
    SECURITY_FORCED_ENTRY = "security_forced_entry"
    SECURITY_GLASS_BREAK = "security_glass_break"
    SECURITY_VIDEO_ANOMALY = "security_video_anomaly"
    MEDICAL_ALERT = "medical_alert"
    SAFETY_ALERT = "safety_alert"
    NODE_HEALTH = "node_health"
    OWNER_REQUEST = "owner_request"
    SCHEDULED = "scheduled"


class WakeSeverity(str, Enum):
    ATTENTION = "attention"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class WakeRequest:
    """One bounded request for a power supervisor to consider waking a body."""

    request_id: str
    source_peer_id: str
    target_body_id: str
    reason: WakeReason
    severity: WakeSeverity
    observed_at_ms: int
    expires_at_ms: int
    evidence_refs: Tuple[str, ...] = ()
    summary: str = ""
    schema: str = WAKE_REQUEST_SCHEMA
    canonical: bool = False
    grants_authority: bool = False
    grants_execution: bool = False
    grants_actuation: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        _identifier("request_id", self.request_id)
        _identifier("source_peer_id", self.source_peer_id)
        _identifier("target_body_id", self.target_body_id)
        if not isinstance(self.reason, WakeReason):
            raise TypeError("reason must be WakeReason")
        if not isinstance(self.severity, WakeSeverity):
            raise TypeError("severity must be WakeSeverity")
        for name, value in (
            ("observed_at_ms", self.observed_at_ms),
            ("expires_at_ms", self.expires_at_ms),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("%s must be a non-negative integer" % name)
        ttl = self.expires_at_ms - self.observed_at_ms
        if ttl < 1 or ttl > MAX_WAKE_REQUEST_TTL_MS:
            raise ValueError("wake request lifetime is outside the bounded limit")
        _evidence_refs(self.evidence_refs)
        _summary(self.summary)
        if self.schema != WAKE_REQUEST_SCHEMA:
            raise ValueError("wake request schema is unsupported")
        if self.canonical:
            raise ValueError("wake requests are non-canonical observations")
        if self.grants_authority or self.grants_execution or self.grants_actuation:
            raise ValueError("wake requests cannot grant authority, execution, or actuation")
        if self.authority != "none":
            raise ValueError("wake requests cannot carry authority")

    def is_expired(self, now_ms: int) -> bool:
        if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")
        return now_ms >= self.expires_at_ms

    def to_payload(self) -> bytes:
        raw = {
            "schema": self.schema,
            "request_id": self.request_id,
            "source_peer_id": self.source_peer_id,
            "target_body_id": self.target_body_id,
            "reason": self.reason.value,
            "severity": self.severity.value,
            "observed_at_ms": self.observed_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "evidence_refs": list(self.evidence_refs),
            "summary": self.summary,
            "canonical": False,
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
            "authority": "none",
        }
        encoded = json.dumps(
            raw,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_WAKE_PAYLOAD_BYTES:
            raise ValueError("wake request payload exceeds bounded size")
        return encoded

    @classmethod
    def from_payload(cls, payload: bytes) -> "WakeRequest":
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("wake request payload must be non-empty bytes")
        if len(payload) > MAX_WAKE_PAYLOAD_BYTES:
            raise ValueError("wake request payload exceeds bounded size")
        try:
            raw = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("wake request payload is not valid UTF-8 JSON") from exc
        if not isinstance(raw, Mapping):
            raise ValueError("wake request payload root must be a mapping")
        allowed = {
            "schema",
            "request_id",
            "source_peer_id",
            "target_body_id",
            "reason",
            "severity",
            "observed_at_ms",
            "expires_at_ms",
            "evidence_refs",
            "summary",
            "canonical",
            "grants_authority",
            "grants_execution",
            "grants_actuation",
            "authority",
        }
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError("wake request contains unsupported fields")
        if raw.get("schema") != WAKE_REQUEST_SCHEMA:
            raise ValueError("wake request schema is unsupported")
        if raw.get("canonical") is not False:
            raise ValueError("wake request canonical must be false")
        for key in ("grants_authority", "grants_execution", "grants_actuation"):
            if raw.get(key) is not False:
                raise ValueError("wake request %s must be false" % key)
        if raw.get("authority") != "none":
            raise ValueError("wake request authority must be none")
        refs = raw.get("evidence_refs", [])
        if not isinstance(refs, list):
            raise ValueError("evidence_refs must be a list")
        try:
            reason = WakeReason(_required_string(raw, "reason"))
            severity = WakeSeverity(_required_string(raw, "severity"))
        except ValueError as exc:
            raise ValueError("wake request reason or severity is unsupported") from exc
        return cls(
            request_id=_required_string(raw, "request_id"),
            source_peer_id=_required_string(raw, "source_peer_id"),
            target_body_id=_required_string(raw, "target_body_id"),
            reason=reason,
            severity=severity,
            observed_at_ms=_required_integer(raw, "observed_at_ms"),
            expires_at_ms=_required_integer(raw, "expires_at_ms"),
            evidence_refs=tuple(refs),
            summary=_optional_string(raw, "summary"),
        )


def new_wake_request(
    *,
    source_peer_id: str,
    target_body_id: str,
    reason: WakeReason,
    severity: WakeSeverity,
    observed_at_ms: int,
    ttl_ms: int = 30_000,
    evidence_refs: Sequence[str] = (),
    summary: str = "",
    request_id: Optional[str] = None,
) -> WakeRequest:
    if isinstance(ttl_ms, bool) or not isinstance(ttl_ms, int):
        raise ValueError("ttl_ms must be an integer")
    if ttl_ms < 1 or ttl_ms > MAX_WAKE_REQUEST_TTL_MS:
        raise ValueError("ttl_ms is outside the bounded wake-request limit")
    return WakeRequest(
        request_id=request_id or ("wake-" + uuid.uuid4().hex),
        source_peer_id=source_peer_id,
        target_body_id=target_body_id,
        reason=reason,
        severity=severity,
        observed_at_ms=observed_at_ms,
        expires_at_ms=observed_at_ms + ttl_ms,
        evidence_refs=tuple(evidence_refs),
        summary=summary,
    )


def build_wake_envelope(
    request: WakeRequest,
    *,
    destination_peer_id: str,
    message_id: Optional[str] = None,
) -> V2VEnvelope:
    if not isinstance(request, WakeRequest):
        raise TypeError("request must be WakeRequest")
    _identifier("destination_peer_id", destination_peer_id)
    ttl_ms = request.expires_at_ms - request.observed_at_ms
    priority = (
        Priority.IMPORTANT
        if request.severity is WakeSeverity.ATTENTION
        else Priority.URGENT
    )
    return V2VEnvelope(
        message_id=message_id or request.request_id,
        source_peer_id=request.source_peer_id,
        destination_peer_id=destination_peer_id,
        payload_type=WAKE_REQUEST_PAYLOAD_TYPE,
        payload=request.to_payload(),
        created_at_ms=request.observed_at_ms,
        ttl_ms=ttl_ms,
        priority=priority,
        ack_required=True,
        hop_limit=_WAKE_HOP_LIMIT,
    )


def wake_request_from_envelope(envelope: V2VEnvelope, *, now_ms: Optional[int] = None) -> WakeRequest:
    if not isinstance(envelope, V2VEnvelope):
        raise TypeError("envelope must be V2VEnvelope")
    if envelope.payload_type != WAKE_REQUEST_PAYLOAD_TYPE:
        raise ValueError("envelope does not contain a wake request")
    request = WakeRequest.from_payload(envelope.payload)
    if request.source_peer_id != envelope.source_peer_id:
        raise ValueError("wake request source does not match envelope source")
    if request.request_id != envelope.message_id:
        raise ValueError("wake request id does not match envelope message id")
    if now_ms is not None and request.is_expired(now_ms):
        raise ValueError("wake request is expired")
    return request


def _identifier(name: str, value: Any) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError("invalid %s" % name)
    return value


def _summary(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("summary must be text")
    if len(value) > MAX_WAKE_SUMMARY_CHARS:
        raise ValueError("summary exceeds bounded length")
    if any(ord(char) < 32 and char not in "\t" for char in value):
        raise ValueError("summary contains unsupported control characters")
    return value


def _evidence_refs(values: Any) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError("evidence_refs must be a tuple")
    if len(values) > MAX_WAKE_EVIDENCE_REFS:
        raise ValueError("too many wake evidence references")
    result = []
    for value in values:
        if not isinstance(value, str) or not value or len(value) > MAX_WAKE_EVIDENCE_REF_CHARS:
            raise ValueError("wake evidence reference is invalid")
        if any(ord(char) < 33 or ord(char) > 126 for char in value):
            raise ValueError("wake evidence references must be printable ASCII")
        result.append(value)
    if len(set(result)) != len(result):
        raise ValueError("wake evidence references cannot contain duplicates")
    return tuple(result)


def _required_string(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError("%s must be non-empty text" % key)
    return value


def _optional_string(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str):
        raise ValueError("%s must be text" % key)
    return value


def _required_integer(raw: Mapping[str, Any], key: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("%s must be a non-negative integer" % key)
    return value
