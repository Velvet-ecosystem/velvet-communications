"""Authenticated bounded request/reply over the Velvet local-IP carrier.

The ordinary local-IP adapter intentionally exposes delivery plus acknowledgement.
Some headless-node protocols, including Runtime's existing distributed-work RPC,
need a small authenticated response body. This module adds that capability without
changing the V2V envelope or granting any new authority.

Request and reply frames reuse the same HMAC, clock-skew, envelope, and framing
rules as :mod:`velvet_communications.local_ip`. Reply bytes are carried inside the
signed acknowledgement and are separately bounded.
"""
from __future__ import annotations

import base64
import hashlib
import socket
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Tuple

from .contracts import V2VEnvelope
from .local_ip import (
    DEFAULT_CLOCK_SKEW_MS,
    DEFAULT_MAX_FRAME_BYTES,
    DEFAULT_MAX_PAYLOAD_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    LOCAL_IP_SCHEMA,
    LocalIpPeer,
    LocalIpTransportError,
    _canonical_bytes,
    _delivery_frame,
    _delivery_source_peer,
    _frame_limit,
    _now_ms,
    _payload_limit,
    _peer_id,
    _positive_number,
    _receive_frame,
    _secret,
    _send_frame,
    _signature,
    _validate_delivery,
    _validate_signed_frame,
)

DEFAULT_MAX_REPLY_BYTES = 64 * 1024
MAX_REPLY_DETAIL_CHARS = 256


@dataclass(frozen=True)
class LocalIpReceiverReply:
    """One bounded result returned by an authenticated local receiver."""

    accepted: bool
    payload: bytes = b""
    detail: str = ""
    authority: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be boolean")
        if not isinstance(self.payload, bytes):
            raise TypeError("reply payload must be bytes")
        if not isinstance(self.detail, str):
            raise TypeError("reply detail must be text")
        if len(self.detail) > MAX_REPLY_DETAIL_CHARS:
            raise ValueError("reply detail exceeds bounded length")
        if self.authority != "none":
            raise ValueError("request/reply carrier cannot carry authority")


@dataclass(frozen=True)
class LocalIpRequestReport:
    """Authenticated request/reply result returned to the calling node."""

    message_id: str
    transport_name: str
    accepted: bool
    acknowledged: bool
    reply_payload: bytes = b""
    detail: str = ""
    authority: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.message_id, str) or not self.message_id:
            raise ValueError("message_id must be non-empty text")
        if not isinstance(self.transport_name, str) or not self.transport_name:
            raise ValueError("transport_name must be non-empty text")
        if not isinstance(self.accepted, bool) or not isinstance(self.acknowledged, bool):
            raise TypeError("accepted and acknowledged must be boolean")
        if not isinstance(self.reply_payload, bytes):
            raise TypeError("reply_payload must be bytes")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be text")
        if self.authority != "none":
            raise ValueError("request/reply report cannot carry authority")


class AuthenticatedLocalIpRequestAdapter:
    """Send one V2V envelope and receive one signed bounded reply payload."""

    def __init__(
        self,
        *,
        local_peer_id: str,
        remote: LocalIpPeer,
        secret: bytes,
        name: str = "local-ip-rpc",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        max_reply_bytes: int = DEFAULT_MAX_REPLY_BYTES,
    ) -> None:
        self.local_peer_id = _peer_id(local_peer_id)
        if not isinstance(remote, LocalIpPeer):
            raise TypeError("remote must be LocalIpPeer")
        self.remote = remote
        self.secret = _secret(secret)
        self.name = _peer_id(name)
        self.timeout_seconds = _positive_number("timeout_seconds", timeout_seconds)
        self.max_frame_bytes = _frame_limit(max_frame_bytes)
        self.max_payload_bytes = _payload_limit(max_payload_bytes, self.max_frame_bytes)
        self.max_reply_bytes = _reply_limit(max_reply_bytes, self.max_frame_bytes)

    def request(self, envelope: V2VEnvelope) -> LocalIpRequestReport:
        if not isinstance(envelope, V2VEnvelope):
            raise TypeError("envelope must be V2VEnvelope")
        if envelope.source_peer_id != self.local_peer_id:
            raise ValueError("envelope source does not match configured local peer")
        if envelope.destination_peer_id != self.remote.peer_id:
            raise ValueError("envelope destination does not match configured remote peer")
        if envelope.payload_bytes > self.max_payload_bytes:
            raise ValueError("envelope exceeds local-IP request payload limit")
        now_ms = _now_ms()
        if envelope.is_expired(now_ms):
            return LocalIpRequestReport(
                message_id=envelope.message_id,
                transport_name=self.name,
                accepted=False,
                acknowledged=False,
                detail="envelope expired before local-IP request",
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
            accepted, detail, reply_payload = _validate_reply_ack(
                ack,
                secret=self.secret,
                message_id=envelope.message_id,
                request_nonce=nonce,
                max_reply_bytes=self.max_reply_bytes,
            )
        except (OSError, TimeoutError, LocalIpTransportError) as exc:
            return LocalIpRequestReport(
                message_id=envelope.message_id,
                transport_name=self.name,
                accepted=False,
                acknowledged=False,
                detail="local-IP request failed: %s" % exc,
            )

        return LocalIpRequestReport(
            message_id=envelope.message_id,
            transport_name=self.name,
            accepted=accepted,
            acknowledged=True,
            reply_payload=reply_payload,
            detail=detail,
        )


class AuthenticatedLocalIpRequestServer:
    """Authenticated local-IP receiver with replay-safe signed reply payloads."""

    def __init__(
        self,
        *,
        local_peer_id: str,
        peer_secrets: Mapping[str, bytes],
        receiver: Callable[[V2VEnvelope], LocalIpReceiverReply],
        bind_host: str = "127.0.0.1",
        port: int = 0,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        max_reply_bytes: int = DEFAULT_MAX_REPLY_BYTES,
        max_clock_skew_ms: int = DEFAULT_CLOCK_SKEW_MS,
        replay_capacity: int = 1024,
        accept_timeout_seconds: float = 0.1,
    ) -> None:
        self.local_peer_id = _peer_id(local_peer_id)
        if not isinstance(peer_secrets, Mapping) or not peer_secrets:
            raise ValueError("peer_secrets must contain at least one configured peer")
        normalized = {}
        for peer_id, secret in peer_secrets.items():
            normalized[_peer_id(peer_id)] = _secret(secret)
        if not callable(receiver):
            raise TypeError("receiver must be callable")
        if not isinstance(bind_host, str) or not bind_host.strip():
            raise ValueError("bind_host must be non-empty text")
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        if isinstance(max_clock_skew_ms, bool) or not isinstance(max_clock_skew_ms, int) or max_clock_skew_ms < 1:
            raise ValueError("max_clock_skew_ms must be a positive integer")
        if isinstance(replay_capacity, bool) or not isinstance(replay_capacity, int) or replay_capacity < 1:
            raise ValueError("replay_capacity must be a positive integer")
        self.peer_secrets = normalized
        self.receiver = receiver
        self.bind_host = bind_host.strip()
        self.port = port
        self.max_frame_bytes = _frame_limit(max_frame_bytes)
        self.max_payload_bytes = _payload_limit(max_payload_bytes, self.max_frame_bytes)
        self.max_reply_bytes = _reply_limit(max_reply_bytes, self.max_frame_bytes)
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
            raise RuntimeError("local-IP request server is already bound")
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
            raise RuntimeError("local-IP request server is not bound")
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
                    _canonical_bytes(_stable_envelope_fingerprint(envelope))
                ).hexdigest()
                cached = self._delivery_cache.get(envelope.message_id)
                if cached is not None:
                    cached_fingerprint, reply = cached
                    self._delivery_cache.move_to_end(envelope.message_id)
                    if cached_fingerprint != fingerprint:
                        reply = LocalIpReceiverReply(
                            accepted=False,
                            detail="message_id reused with different content",
                        )
                else:
                    reply = self.receiver(envelope)
                    if not isinstance(reply, LocalIpReceiverReply):
                        raise TypeError("request receiver must return LocalIpReceiverReply")
                    if len(reply.payload) > self.max_reply_bytes:
                        raise LocalIpTransportError("reply payload exceeds receiver limit")
                    self._delivery_cache[envelope.message_id] = (fingerprint, reply)
                    self._delivery_cache.move_to_end(envelope.message_id)
                    while len(self._delivery_cache) > self.replay_capacity:
                        self._delivery_cache.popitem(last=False)
                ack = _reply_ack_frame(
                    message_id=envelope.message_id,
                    request_nonce=nonce,
                    reply=reply,
                    secret=secret,
                )
            except Exception as exc:
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
                ack = _reply_ack_frame(
                    message_id=message_id,
                    request_nonce=nonce,
                    reply=LocalIpReceiverReply(
                        accepted=False,
                        detail=(str(exc) or type(exc).__name__)[:MAX_REPLY_DETAIL_CHARS],
                    ),
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


def _reply_ack_frame(
    *,
    message_id: str,
    request_nonce: str,
    reply: LocalIpReceiverReply,
    secret: bytes,
):
    unsigned = {
        "schema": LOCAL_IP_SCHEMA,
        "kind": "ack",
        "message_id": str(message_id)[:128],
        "request_nonce": str(request_nonce)[:128],
        "accepted": reply.accepted,
        "detail": reply.detail[:MAX_REPLY_DETAIL_CHARS],
        "reply_payload_b64": base64.b64encode(reply.payload).decode("ascii"),
        "authority": "none",
    }
    return dict(unsigned, signature=_signature(unsigned, secret))


def _validate_reply_ack(
    frame,
    *,
    secret: bytes,
    message_id: str,
    request_nonce: str,
    max_reply_bytes: int,
):
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
    encoded = frame.get("reply_payload_b64", "")
    if not isinstance(encoded, str):
        raise LocalIpTransportError("ack reply payload must be base64 text")
    try:
        payload = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise LocalIpTransportError("ack reply payload is invalid") from exc
    if len(payload) > max_reply_bytes:
        raise LocalIpTransportError("ack reply payload exceeds configured limit")
    return accepted, detail[:MAX_REPLY_DETAIL_CHARS], payload


def _reply_limit(value: int, frame_limit: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("max_reply_bytes must be a positive integer")
    # Base64 expands by roughly 4/3 and the signed JSON frame adds fixed overhead.
    if ((value + 2) // 3) * 4 + 2048 >= frame_limit:
        raise ValueError("max_reply_bytes is too large for max_frame_bytes")
    return value


def _stable_envelope_fingerprint(envelope: V2VEnvelope):
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
