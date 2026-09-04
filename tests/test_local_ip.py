import threading
import time

import pytest

from velvet_communications import Priority, V2VEnvelope
from velvet_communications.local_ip import (
    AuthenticatedLocalIpAdapter,
    AuthenticatedLocalIpServer,
    LocalIpPeer,
    LocalIpTransportError,
    load_secret_file,
)


SECRET = b"v" * 32


def envelope(message_id="msg-1", payload=b"hello"):
    now_ms = int(time.time() * 1000)
    return V2VEnvelope(
        message_id=message_id,
        source_peer_id="velour-lyra-1",
        destination_peer_id="founder",
        payload_type="velvet.runtime.transport.v1",
        payload=payload,
        created_at_ms=now_ms,
        ttl_ms=30_000,
        priority=Priority.NORMAL,
        ack_required=True,
    )


def start_server(receiver, *, secret=SECRET):
    server = AuthenticatedLocalIpServer(
        local_peer_id="founder",
        peer_secrets={"velour-lyra-1": secret},
        receiver=receiver,
        bind_host="127.0.0.1",
        port=0,
        accept_timeout_seconds=0.05,
    )
    server.bind()
    return server


def adapter_for(server, *, secret=SECRET, confidential=False):
    host, port = server.address
    return AuthenticatedLocalIpAdapter(
        local_peer_id="velour-lyra-1",
        remote=LocalIpPeer(peer_id="founder", host=host, port=port),
        secret=secret,
        confidential_underlay=confidential,
        timeout_seconds=1.0,
    )


def serve_count(server, count):
    for _ in range(count):
        while not server.serve_once():
            pass


def test_authenticated_loopback_delivery_and_ack():
    received = []
    server = start_server(lambda item: received.append(item) or True)
    thread = threading.Thread(target=serve_count, args=(server, 1), daemon=True)
    thread.start()
    try:
        report = adapter_for(server).send(envelope())
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert report.accepted is True
    assert report.acknowledged is True
    assert len(received) == 1
    assert received[0].payload == b"hello"
    assert received[0].source_peer_id == "velour-lyra-1"
    assert report.authority == "none"


def test_duplicate_message_reuses_original_accepted_outcome_without_redelivery():
    received = []
    server = start_server(lambda item: received.append(item) or True)
    thread = threading.Thread(target=serve_count, args=(server, 2), daemon=True)
    thread.start()
    try:
        adapter = adapter_for(server)
        first = adapter.send(envelope("repeat-1"))
        second = adapter.send(envelope("repeat-1"))
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert first.accepted is True
    assert second.accepted is True
    assert second.acknowledged is True
    assert second.detail == first.detail
    assert len(received) == 1


def test_duplicate_message_reuses_original_rejection():
    received = []
    server = start_server(lambda item: received.append(item) or False)
    thread = threading.Thread(target=serve_count, args=(server, 2), daemon=True)
    thread.start()
    try:
        adapter = adapter_for(server)
        first = adapter.send(envelope("reject-1"))
        second = adapter.send(envelope("reject-1"))
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert first.accepted is False
    assert second.accepted is False
    assert second.acknowledged is True
    assert second.detail == "rejected by local receiver"
    assert len(received) == 1


def test_message_id_reuse_with_different_content_is_rejected():
    received = []
    server = start_server(lambda item: received.append(item) or True)
    thread = threading.Thread(target=serve_count, args=(server, 2), daemon=True)
    thread.start()
    try:
        adapter = adapter_for(server)
        first = adapter.send(envelope("same-id", b"first"))
        second = adapter.send(envelope("same-id", b"different"))
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert first.accepted is True
    assert second.accepted is False
    assert second.acknowledged is True
    assert "different content" in second.detail
    assert len(received) == 1


def test_wrong_peer_secret_is_not_accepted():
    server = start_server(lambda _item: True)
    thread = threading.Thread(target=serve_count, args=(server, 1), daemon=True)
    thread.start()
    try:
        report = adapter_for(server, secret=b"x" * 32).send(envelope())
    finally:
        thread.join(timeout=2.0)
        server.close()

    assert report.accepted is False
    assert report.acknowledged is False


def test_protected_path_requires_confidential_underlay_declaration():
    server = start_server(lambda _item: True)
    try:
        assert adapter_for(server, confidential=False).offer().protected_path is False
        assert adapter_for(server, confidential=True).offer().protected_path is True
    finally:
        server.close()


def test_locked_secret_file_loader(tmp_path):
    secret_path = tmp_path / "peer.secret"
    secret_path.write_bytes(SECRET + b"\n")
    secret_path.chmod(0o600)
    assert load_secret_file(secret_path) == SECRET

    secret_path.chmod(0o640)
    with pytest.raises(LocalIpTransportError, match="group/other"):
        load_secret_file(secret_path)


def test_secret_file_rejects_symlink(tmp_path):
    target = tmp_path / "target.secret"
    target.write_bytes(SECRET)
    target.chmod(0o600)
    link = tmp_path / "peer.secret"
    link.symlink_to(target)
    with pytest.raises(LocalIpTransportError, match="non-symlink"):
        load_secret_file(link)
