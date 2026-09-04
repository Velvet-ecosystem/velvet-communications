"""Authenticated bounded local-IP carrier for headless Velvet nodes.

This adapter supplies peer authentication, frame integrity, replay suppression,
and bounded request/ack exchange using only the Python standard library. It does
not encrypt payloads. ``protected_path`` is therefore advertised only when the
operator explicitly states that a confidential underlay such as Tailscale,
WireGuard, or another reviewed encrypted link is carrying the TCP connection.

A carrier connection never creates Runtime/Court authority or body membership.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import socket
import stat
import struct
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Tuple, Union

from .contracts import DeliveryReport, Priority, TransportKind, TransportOffer, V2VEnvelope

LOCAL_IP_SCHEMA = "velvet.communications.local_ip.v1"
DEFAULT_MAX_FRAME_BYTES = 256 * 1024
DEFAULT_MAX_PAYLOAD_BYTES = 192 * 1024
DEFAULT_CLOCK_SKEW_MS = 30_000
DEFAULT_TIMEOUT_SECONDS = 2.0
MIN_SECRET_BYTES = 32
MAX_SECRET_BYTES = 4096
_HEADER = struct.Struct("!I")


class LocalIpTransportError(RuntimeError):
    """Authenticated local-IP delivery failed before a valid acknowledgement."""


@dataclass(frozen=True)
class LocalIpPeer:
    peer_id: str
    host: str
    port: int

    def __post_init__(self) -> None:
        _peer_id(self.peer_id)
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("host must be non-empty text")
        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise ValueError("port must be an integer")
        if not 1 <= self.port <= 65535:
            raise ValueError("remote port must be between 1 and 65535")


class AuthenticatedLocalIpAdapter:
    """One authenticated TCP delivery path to a configured Velvet peer."""

    def __init__(
        self,
        *,
        local_peer_id: str,
        remote: LocalIpPeer,
        secret: bytes,
        name: str = "local-ip",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        preference: int = 10,
        confidential_underlay: bool = False,
    ) -> None:
        self.local_peer_id = _peer_id(local_peer_id)
        if not isinstance(remote, LocalIpPeer):
            raise TypeError("remote must be LocalIpPeer")
        self.remote = remote
        self.secret = _secret(secret)
        self.name = _transport_name(name)
        self.timeout_seconds = _positive_number("timeout_seconds", timeout_seconds)
        self.max_frame_bytes = _frame_limit(max_frame_bytes)
        self.max_payload_bytes = _payload_limit(max_payload_bytes, self.max_frame_bytes)
        if isinstance(preference, bool) or not isinstance(preference, int) or preference < 0:
            raise ValueError("preference must be a non-negative integer")
        if not isinstance(confidential_underlay, bool):
            raise TypeError("confidential_underlay must be boolean")
        self.preference = preference
        self.confidential_underlay = confidential_underlay

    def offer(self) -> TransportOffer:
        return TransportOffer(
            name=self.name,
            kind=TransportKind.IP,
            available=True,
            max_payload_bytes=self.max_payload_bytes,
            preference=self.preference,
            protected_path=self.confidential_underlay,
            supports_ack=True,
            supports_store_and_forward=False,
        )

    def send(self, envelope: V2VEnvelope) -> DeliveryReport:
        if not isinstance(envelope, V2VEnvelope):
            raise TypeError("envelope must be V2VEnvelope")
        if envelope.source_peer_id != self.local_peer_id:
            raise ValueError("envelope source does not match configured local peer")
        if envelope.destination_peer_id != self.remote.peer_id:
            raise ValueError("envelope destination does not match configured remote peer")
        if envelope.payload_bytes > self.max_payload_bytes:
            raise ValueError("envelope exceeds local-IP payload limit")
        now_ms = _now_ms()
        if envelope.is_expired(now_ms):
            return DeliveryReport(
                message_id=envelope.message_id,
                transport_name=self.name,
                accepted=False,
                acknowledged=False,
                detail="envelope expired before local-IP delivery",
            )

        nonce = uuid.uuid4().hex
        frame = _delivery_frame(envelope, nonce=nonce, sent_at_ms=now_ms, secret=self.secret)
        try:
            with socket.create_connection(
                (self.remote.host, self.remote.port), timeout=self.timeout_seconds
            ) as connection:
                connection.settimeout(self.timeout_seconds)
                _send_frame(connection, frame, self.max_frame_bytes)
                ack = _receive_frame(connection, self.max_frame_bytes)
            accepted, detail = _validate_ack(
                ack,
                secret=self.secret,
                message_id=envelope.message_id,
                request_nonce=nonce,
            )
        except (OSError, TimeoutError, LocalIpTransportError) as exc:
            return DeliveryReport(
                message_id=envelope.message_id,
                transport_name=self.name,
                accepted=False,
                acknowledged=False,
                detail="local-IP delivery failed: %s" % exc,
            )

        return DeliveryReport(
            message_id=envelope.message_id,
            transport_name=self.name,
            accepted=accepted,
            acknowledged=True,
            detail=detail,
        )


class AuthenticatedLocalIpServer:
    """Bounded receiver for authenticated local-IP V2V envelopes."""

    def __init__(
        self,
        *,
        local_peer_id: str,
        peer_secrets: Mapping[str, bytes],
        receiver: Callable[[V2VEnvelope], bool],
        bind_host: str = "127.0.0.1",
        port: int = 0,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        max_clock_skew_ms: int = DEFAULT_CLOCK_SKEW_MS,
        replay_capacity: int = 1024,
        accept_timeout_seconds: float = 0.1,
    ) -> None:
        self.local_peer_id = _peer_id(local_peer_id)
        if not isinstance(peer_secrets, Mapping) or not peer_secrets:
            raise ValueError("peer_secrets must contain at least one configured peer")
        normalized: Dict[str, bytes] = {}
        for peer_id, secret in peer_secrets.items():
            normalized[_peer_id(peer_id)] = _secret(secret)
        if not callable(receiver):
            raise TypeError("receiver must be callable")
        if not isinstance(bind_host, str) or not bind_host.strip():
            raise ValueError("bind_host must be non-empty text")
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        if isinstance(max_clock_skew_ms, bool) or not isinstance(max_clock_skew_ms, int):
            raise ValueError("max_clock_skew_ms must be an integer")
        if max_clock_skew_ms < 1:
            raise ValueError("max_clock_skew_ms must be positive")
        if isinstance(replay_capacity, bool) or not isinstance(replay_capacity, int):
            raise ValueError("replay_capacity must be an integer")
        if replay_capacity < 1:
            raise ValueError("replay_capacity must be positive")
        self.peer_secrets = normalized
        self.receiver = receiver
        self.bind_host = bind_host.strip()
        self.port = port
        self.max_frame_bytes = _frame_limit(max_frame_bytes)
        self.max_payload_bytes = _payload_limit(max_payload_bytes, self.max_frame_bytes)
        self.max_clock_skew_ms = max_clock_skew_ms
        self.replay_capacity = replay_capacity
        self.accept_timeout_seconds = _positive_number(
            "accept_timeout_seconds", accept_timeout_seconds
        )
        self._delivery_cache = OrderedDict()
        self._listener: Optional[socket.socket] = None

    @property
    def address(self) -> Tuple[str, int]:
        if self._listener is None:
            return self.bind_host, self.port
        host, port = self._listener.getsockname()[:2]
        return str(host), int(port)

    def bind(self) -> None:
        if self._listener is not None:
            raise RuntimeError("local-IP server is already bound")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.bind_host, self.port))
            listener.listen(8)
            listener.settimeout(self.accept_timeout_seconds)
        except Exception:
            listener.close()
            raise
        self._listener = listener

    def serve_once(self) -> bool:
        if self._listener is None:
            raise RuntimeError("local-IP server is not bound")
        try:
            connection, _address = self._listener.accept()
        except socket.timeout:
            return False
        with connection:
            connection.settimeout(max(1.0, self.accept_timeout_seconds * 10.0))
            try:
                frame = _receive_frame(connection, self.max_frame_bytes)
                source_peer_id = _delivery_source_peer(frame)
                secret = self.peer_secrets.get(source_peer_id)
                if secret is None:
                    raise LocalIpTransportError("source peer is not provisioned")
                envelope, nonce = _validate_delivery(
                    frame,
                    secret=secret,
                    expected_destination=self.local_peer_id,
                    max_payload_bytes=self.max_payload_bytes,
                    max_clock_skew_ms=self.max_clock_skew_ms,
                )
                fingerprint = hashlib.sha256(
                    _canonical_bytes(_envelope_to_dict(envelope))
                ).hexdigest()
                cached = self._delivery_cache.get(envelope.message_id)
                if cached is not None:
                    cached_fingerprint, accepted, detail = cached
                    self._delivery_cache.move_to_end(envelope.message_id)
                    if cached_fingerprint != fingerprint:
                        accepted = False
                        detail = "message_id reused with different content"
                else:
                    accepted = bool(self.receiver(envelope))
                    detail = (
                        "accepted by local receiver"
                        if accepted
                        else "rejected by local receiver"
                    )
                    self._delivery_cache[envelope.message_id] = (
                        fingerprint,
                        accepted,
                        detail,
                    )
                    self._delivery_cache.move_to_end(envelope.message_id)
                    while len(self._delivery_cache) > self.replay_capacity:
                        self._delivery_cache.popitem(last=False)
                ack = _ack_frame(
                    message_id=envelope.message_id,
                    request_nonce=nonce,
                    accepted=accepted,
                    detail=detail,
                    secret=secret,
                )
            except Exception as exc:
                # If the peer cannot be authenticated there is no safe secret with
                # which to create an authenticated error response. Close silently.
                try:
                    source_peer_id = _delivery_source_peer(frame)  # type: ignore[name-defined]
                    secret = self.peer_secrets.get(source_peer_id)
                except Exception:
                    secret = None
                if secret is None:
                    return True
                message_id = "unknown"
                nonce = "unknown"
                try:
                    message_id = str(frame.get("envelope", {}).get("message_id", "unknown"))
                    nonce = str(frame.get("nonce", "unknown"))
                except Exception:
                    pass
                ack = _ack_frame(
                    message_id=message_id,
                    request_nonce=nonce,
                    accepted=False,
                    detail=(str(exc) or type(exc).__name__)[:256],
                    secret=secret,
                )
            try:
                _send_frame(connection, ack, self.max_frame_bytes)
            except (OSError, LocalIpTransportError):
                pass
        return True

    def close(self) -> None:
        listener = self._listener
        self._listener = None
        if listener is not None:
            listener.close()


def load_secret_file(path: Union[str, Path]) -> bytes:
    """Load one deployment-local peer secret from a locked regular file."""

    secret_path = Path(path)
    try:
        node = secret_path.lstat()
    except OSError as exc:
        raise LocalIpTransportError("peer secret file is unavailable") from exc
    if stat.S_ISLNK(node.st_mode) or not stat.S_ISREG(node.st_mode):
        raise LocalIpTransportError("peer secret path must be a regular non-symlink file")
    if stat.S_IMODE(node.st_mode) & 0o077:
        raise LocalIpTransportError("peer secret file must not be accessible to group/other")
    try:
        data = secret_path.read_bytes().strip()
    except OSError as exc:
        raise LocalIpTransportError("peer secret file could not be read") from exc
    return _secret(data)


def _delivery_frame(
    envelope: V2VEnvelope,
    *,
    nonce: str,
    sent_at_ms: int,
    secret: bytes,
) -> Mapping[str, object]:
    unsigned = {
        "schema": LOCAL_IP_SCHEMA,
        "kind": "delivery",
        "nonce": _nonce(nonce),
        "sent_at_ms": int(sent_at_ms),
        "envelope": _envelope_to_dict(envelope),
        "authority": "none",
    }
    return dict(unsigned, signature=_signature(unsigned, secret))


def _ack_frame(
    *,
    message_id: str,
    request_nonce: str,
    accepted: bool,
    detail: str,
    secret: bytes,
) -> Mapping[str, object]:
    unsigned = {
        "schema": LOCAL_IP_SCHEMA,
        "kind": "ack",
        "message_id": str(message_id)[:128],
        "request_nonce": str(request_nonce)[:128],
        "accepted": bool(accepted),
        "detail": str(detail)[:256],
        "authority": "none",
    }
    return dict(unsigned, signature=_signature(unsigned, secret))


def _validate_delivery(
    frame: Mapping[str, object],
    *,
    secret: bytes,
    expected_destination: str,
    max_payload_bytes: int,
    max_clock_skew_ms: int,
) -> Tuple[V2VEnvelope, str]:
    _validate_signed_frame(frame, secret, "delivery")
    nonce = _nonce(frame.get("nonce"))
    sent_at_ms = frame.get("sent_at_ms")
    if isinstance(sent_at_ms, bool) or not isinstance(sent_at_ms, int) or sent_at_ms < 0:
        raise LocalIpTransportError("delivery sent_at_ms is invalid")
    if abs(_now_ms() - sent_at_ms) > max_clock_skew_ms:
        raise LocalIpTransportError("delivery timestamp is outside allowed clock skew")
    raw_envelope = frame.get("envelope")
    if not isinstance(raw_envelope, Mapping):
        raise LocalIpTransportError("delivery envelope must be a mapping")
    envelope = _envelope_from_dict(raw_envelope)
    if envelope.destination_peer_id != expected_destination:
        raise LocalIpTransportError("delivery destination does not match this peer")
    if envelope.payload_bytes > max_payload_bytes:
        raise LocalIpTransportError("delivery payload exceeds receiver limit")
    if envelope.is_expired(_now_ms()):
        raise LocalIpTransportError("delivery envelope is expired")
    return envelope, nonce


def _validate_ack(
    frame: Mapping[str, object],
    *,
    secret: bytes,
    message_id: str,
    request_nonce: str,
) -> Tuple[bool, str]:
    _validate_signed_frame(frame, secret, "ack")
    if frame.get("message_id") != message_id:
        raise LocalIpTransportError("ack message_id mismatch")
    if frame.get("request_nonce") != request_nonce:
        raise LocalIpTransportError("ack nonce mismatch")
    accepted = frame.get("accepted")
    if not isinstance(accepted, bool):
        raise LocalIpTransportError("ack accepted field must be boolean")
    detail = frame.get("detail", "")
    if not isinstance(detail, str):
        raise LocalIpTransportError("ack detail must be text")
    return accepted, detail[:256]


def _validate_signed_frame(frame: Mapping[str, object], secret: bytes, kind: str) -> None:
    if not isinstance(frame, Mapping):
        raise LocalIpTransportError("local-IP frame must be a mapping")
    if frame.get("schema") != LOCAL_IP_SCHEMA or frame.get("kind") != kind:
        raise LocalIpTransportError("unsupported local-IP frame")
    if frame.get("authority") != "none":
        raise LocalIpTransportError("local-IP frame cannot carry authority")
    signature = frame.get("signature")
    if not isinstance(signature, str) or len(signature) != 64:
        raise LocalIpTransportError("local-IP signature is invalid")
    unsigned = dict(frame)
    unsigned.pop("signature", None)
    expected = _signature(unsigned, secret)
    if not hmac.compare_digest(signature, expected):
        raise LocalIpTransportError("local-IP signature mismatch")


def _delivery_source_peer(frame: Mapping[str, object]) -> str:
    if not isinstance(frame, Mapping):
        raise LocalIpTransportError("local-IP frame must be a mapping")
    envelope = frame.get("envelope")
    if not isinstance(envelope, Mapping):
        raise LocalIpTransportError("delivery envelope is unavailable")
    return _peer_id(envelope.get("source_peer_id"))


def _envelope_to_dict(envelope: V2VEnvelope) -> Mapping[str, object]:
    return {
        "schema": envelope.schema,
        "message_id": envelope.message_id,
        "source_peer_id": envelope.source_peer_id,
        "destination_peer_id": envelope.destination_peer_id,
        "payload_type": envelope.payload_type,
        "payload_b64": base64.b64encode(envelope.payload).decode("ascii"),
        "created_at_ms": envelope.created_at_ms,
        "ttl_ms": envelope.ttl_ms,
        "priority": envelope.priority.value,
        "ack_required": envelope.ack_required,
        "hop_limit": envelope.hop_limit,
    }


def _envelope_from_dict(raw: Mapping[str, object]) -> V2VEnvelope:
    payload_b64 = raw.get("payload_b64")
    if not isinstance(payload_b64, str):
        raise LocalIpTransportError("payload_b64 must be text")
    try:
        payload = base64.b64decode(payload_b64.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise LocalIpTransportError("payload_b64 is invalid") from exc
    try:
        priority = Priority(str(raw.get("priority")))
    except ValueError as exc:
        raise LocalIpTransportError("priority is unsupported") from exc
    ack_required = raw.get("ack_required")
    if not isinstance(ack_required, bool):
        raise LocalIpTransportError("ack_required must be boolean")
    return V2VEnvelope(
        schema=str(raw.get("schema")),
        message_id=str(raw.get("message_id")),
        source_peer_id=str(raw.get("source_peer_id")),
        destination_peer_id=str(raw.get("destination_peer_id")),
        payload_type=str(raw.get("payload_type")),
        payload=payload,
        created_at_ms=_integer(raw.get("created_at_ms"), "created_at_ms"),
        ttl_ms=_integer(raw.get("ttl_ms"), "ttl_ms"),
        priority=priority,
        ack_required=ack_required,
        hop_limit=_integer(raw.get("hop_limit"), "hop_limit"),
    )


def _signature(message: Mapping[str, object], secret: bytes) -> str:
    return hmac.new(secret, _canonical_bytes(message), hashlib.sha256).hexdigest()


def _canonical_bytes(message: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            message,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LocalIpTransportError("local-IP frame is not canonical JSON data") from exc


def _send_frame(connection: socket.socket, frame: Mapping[str, object], limit: int) -> None:
    payload = _canonical_bytes(frame)
    if len(payload) < 2 or len(payload) > limit:
        raise LocalIpTransportError("local-IP frame exceeds configured limit")
    connection.sendall(_HEADER.pack(len(payload)) + payload)


def _receive_frame(connection: socket.socket, limit: int) -> Mapping[str, object]:
    header = _receive_exact(connection, _HEADER.size)
    size = _HEADER.unpack(header)[0]
    if size < 2 or size > limit:
        raise LocalIpTransportError("local-IP frame length is invalid")
    raw = _receive_exact(connection, size)
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalIpTransportError("local-IP frame is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, Mapping):
        raise LocalIpTransportError("local-IP frame root must be a mapping")
    return decoded


def _receive_exact(connection: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise LocalIpTransportError("connection closed mid-frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _secret(value: bytes) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError("peer secret must be bytes")
    if not MIN_SECRET_BYTES <= len(value) <= MAX_SECRET_BYTES:
        raise ValueError("peer secret must be between 32 and 4096 bytes")
    return bytes(value)


def _peer_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("peer_id must be non-empty text")
    text = value.strip()
    if len(text) > 128 or not text.isascii():
        raise ValueError("peer_id must be ASCII up to 128 characters")
    if any(not (char.isalnum() or char in "._:-") for char in text):
        raise ValueError("peer_id contains unsupported characters")
    return text


def _transport_name(value: object) -> str:
    return _peer_id(value)


def _nonce(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise LocalIpTransportError("nonce must be non-empty text")
    if len(value) > 128 or not value.isascii() or any(ord(char) < 33 for char in value):
        raise LocalIpTransportError("nonce must be printable ASCII up to 128 characters")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LocalIpTransportError("%s must be an integer" % name)
    return value


def _positive_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0.0:
        raise ValueError("%s must be positive" % name)
    return float(value)


def _frame_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 4096:
        raise ValueError("max_frame_bytes must be an integer of at least 4096")
    return value


def _payload_limit(value: object, frame_limit: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("max_payload_bytes must be a positive integer")
    if value >= frame_limit:
        raise ValueError("max_payload_bytes must be smaller than max_frame_bytes")
    return value


def _now_ms() -> int:
    return int(time.time() * 1000)
