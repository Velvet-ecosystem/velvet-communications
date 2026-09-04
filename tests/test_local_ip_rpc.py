import threading
import time

from velvet_communications import Priority, V2VEnvelope
from velvet_communications.local_ip import LocalIpPeer
from velvet_communications.local_ip_rpc import (
    AuthenticatedLocalIpRequestAdapter,
    AuthenticatedLocalIpRequestServer,
    LocalIpReceiverReply,
)


SECRET = b"r" * 32


def envelope(message_id="rpc-1", payload=b"request"):
    now_ms = int(time.time() * 1000)
    return V2VEnvelope(
        message_id=message_id,
        source_peer_id="velour-lyra-1",
        destination_peer_id="founder",
        payload_type="velvet.runtime.rpc.v1",
        payload=payload,
        created_at_ms=now_ms,
        ttl_ms=30_000,
        priority=Priority.NORMAL,
        ack_required=True,
    )


def start_server(receiver):
    server = AuthenticatedLocalIpRequestServer(
        local_peer_id="founder",
        peer_secrets={"velour-lyra-1": SECRET},
        receiver=receiver,
        bind_host="127.0.0.1",
        port=0,
        accept_timeout_seconds=0.05,
    )
    server.bind()
    return server


def adapter_for(server, *, secret=SECRET):
    host, port = server.address
    return AuthenticatedLocalIpRequestAdapter(
        local_peer_id="velour-lyra-1",
        remote=LocalIpPeer(peer_id="founder", host=host, port=port),
        secret=secret,
        timeout_seconds=1.0,
    )


def serve_count(server, count):
    for _ in range(count):
        while not server.serve_once():
            pass


def test_authenticated_request_returns_signed_reply_payload():
    received = []
    server = start_server(
        lambda item: received.append(item) or LocalIpReceiverReply(
            accepted=True,
            payload=b'{"result":"ok"}',
            detail="runtime replied",
        )
    )
    thread = threading.Thread(target=serve_count, args=(server, 1), daemon=True)
    thread.start()
    try:
        report = adapter_for(server).request(envelope())
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert report.accepted is True
    assert report.acknowledged is True
    assert report.reply_payload == b'{"result":"ok"}'
    assert report.detail == "runtime replied"
    assert report.authority == "none"
    assert len(received) == 1


def test_duplicate_request_replays_cached_reply_without_redelivery():
    received = []
    server = start_server(
        lambda item: received.append(item) or LocalIpReceiverReply(
            accepted=True,
            payload=b"first-result",
            detail="accepted",
        )
    )
    thread = threading.Thread(target=serve_count, args=(server, 2), daemon=True)
    thread.start()
    try:
        adapter = adapter_for(server)
        item = envelope("same-rpc")
        first = adapter.request(item)
        second = adapter.request(item)
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert first.accepted is True
    assert second.accepted is True
    assert first.reply_payload == b"first-result"
    assert second.reply_payload == first.reply_payload
    assert second.detail == first.detail
    assert len(received) == 1


def test_message_id_reuse_with_different_content_is_rejected():
    received = []
    server = start_server(
        lambda item: received.append(item) or LocalIpReceiverReply(
            accepted=True,
            payload=b"ok",
        )
    )
    thread = threading.Thread(target=serve_count, args=(server, 2), daemon=True)
    thread.start()
    try:
        adapter = adapter_for(server)
        first_item = envelope("reuse-rpc", b"first")
        second_item = V2VEnvelope(
            message_id=first_item.message_id,
            source_peer_id=first_item.source_peer_id,
            destination_peer_id=first_item.destination_peer_id,
            payload_type=first_item.payload_type,
            payload=b"changed",
            created_at_ms=first_item.created_at_ms,
            ttl_ms=first_item.ttl_ms,
            priority=first_item.priority,
            ack_required=True,
        )
        first = adapter.request(first_item)
        second = adapter.request(second_item)
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert first.accepted is True
    assert second.accepted is False
    assert second.acknowledged is True
    assert second.reply_payload == b""
    assert "different content" in second.detail
    assert len(received) == 1


def test_receiver_rejection_can_return_bounded_error_payload():
    server = start_server(
        lambda _item: LocalIpReceiverReply(
            accepted=False,
            payload=b'{"error":"policy"}',
            detail="rejected",
        )
    )
    thread = threading.Thread(target=serve_count, args=(server, 1), daemon=True)
    thread.start()
    try:
        report = adapter_for(server).request(envelope("reject-rpc"))
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert report.accepted is False
    assert report.acknowledged is True
    assert report.reply_payload == b'{"error":"policy"}'


def test_wrong_secret_cannot_recover_reply_payload():
    server = start_server(
        lambda _item: LocalIpReceiverReply(accepted=True, payload=b"secret-result")
    )
    thread = threading.Thread(target=serve_count, args=(server, 1), daemon=True)
    thread.start()
    try:
        report = adapter_for(server, secret=b"x" * 32).request(envelope("wrong-secret"))
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert report.accepted is False
    assert report.acknowledged is False
    assert report.reply_payload == b""
