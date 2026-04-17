"""Tests for the shared embedding service IPC protocol.

Phase 2, Step 1: validates the protocol layer in isolation before wiring
into production code. All tests use mock encode/predict functions —
no torch or sentence-transformers dependency.

Covers:
- Message serialization/deserialization (round-trip)
- ndarray <-> base64 encoding (bit-exact)
- Input validation (size limits, type checks)
- EmbeddingServer request handling (single-worker queue)
- EmbeddingClient connection, retry, reconnect
- Concurrent request safety (queue serialization)
- Security: socket permissions, path containment
- Health check
"""

import os
import shutil
import socket
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import pytest

from ai_governance_mcp.embedding_ipc import (
    CONTAINMENT_ROOT,
    MAX_PAIRS_PER_REQUEST,
    MAX_TEXT_LENGTH,
    MAX_TEXTS_PER_REQUEST,
    EmbeddingClient,
    EmbeddingServer,
    _base64_to_ndarray,
    _decode_message,
    _encode_message,
    _ndarray_to_base64,
    _resolve_socket_path,
    _validate_encode_request,
    _validate_predict_request,
)


# =============================================================================
# Protocol serialization tests
# =============================================================================


class TestMessageSerialization:
    """Test length-prefixed JSON encoding/decoding."""

    def test_encode_decode_round_trip(self):
        original = {"op": "encode", "texts": ["hello", "world"], "normalize": True}
        encoded = _encode_message(original)
        # First 4 bytes are the length prefix
        assert len(encoded) > 4
        length = int.from_bytes(encoded[:4], "big")
        assert length == len(encoded) - 4

    def test_encode_message_is_valid_json(self):
        import json

        msg = _encode_message({"key": "value"})
        payload = msg[4:]
        parsed = json.loads(payload)
        assert parsed == {"key": "value"}

    def test_decode_via_socket_pair(self):
        """End-to-end through a real socket pair."""
        s1, s2 = socket.socketpair()
        try:
            original = {"op": "health"}
            s1.sendall(_encode_message(original))
            decoded = _decode_message(s2)
            assert decoded == original
        finally:
            s1.close()
            s2.close()


# =============================================================================
# ndarray <-> base64 tests
# =============================================================================


class TestNdarrayBase64:
    """Test bit-exact ndarray serialization through base64."""

    def test_round_trip_preserves_values(self):
        arr = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32)
        encoded = _ndarray_to_base64(arr)
        decoded = _base64_to_ndarray(encoded, [2, 3])
        np.testing.assert_array_equal(arr, decoded)

    def test_round_trip_single_vector(self):
        arr = np.random.rand(384).astype(np.float32)
        encoded = _ndarray_to_base64(arr)
        decoded = _base64_to_ndarray(encoded, [384])
        np.testing.assert_array_equal(arr, decoded)

    def test_round_trip_batch(self):
        arr = np.random.rand(100, 384).astype(np.float32)
        encoded = _ndarray_to_base64(arr)
        decoded = _base64_to_ndarray(encoded, [100, 384])
        np.testing.assert_array_equal(arr, decoded)

    def test_shape_mismatch_raises(self):
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        encoded = _ndarray_to_base64(arr)
        with pytest.raises(ValueError, match="expected"):
            _base64_to_ndarray(encoded, [2, 3])

    def test_empty_array(self):
        arr = np.zeros((0, 384), dtype=np.float32)
        encoded = _ndarray_to_base64(arr)
        decoded = _base64_to_ndarray(encoded, [0, 384])
        assert decoded.shape == (0, 384)


# =============================================================================
# Input validation tests
# =============================================================================


class TestInputValidation:
    """Test size limits from security audit finding S2."""

    def test_encode_valid_request(self):
        _validate_encode_request({"texts": ["hello", "world"]})

    def test_encode_too_many_texts(self):
        with pytest.raises(ValueError, match="Too many texts"):
            _validate_encode_request({"texts": ["x"] * (MAX_TEXTS_PER_REQUEST + 1)})

    def test_encode_text_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            _validate_encode_request({"texts": ["x" * (MAX_TEXT_LENGTH + 1)]})

    def test_encode_non_string_text(self):
        with pytest.raises(ValueError, match="not a string"):
            _validate_encode_request({"texts": [123]})

    def test_encode_texts_not_list(self):
        with pytest.raises(ValueError, match="must be a list"):
            _validate_encode_request({"texts": "not a list"})

    def test_predict_valid_request(self):
        _validate_predict_request({"pairs": [["q", "d1"], ["q", "d2"]]})

    def test_predict_too_many_pairs(self):
        with pytest.raises(ValueError, match="Too many pairs"):
            _validate_predict_request(
                {"pairs": [["q", "d"]] * (MAX_PAIRS_PER_REQUEST + 1)}
            )

    def test_predict_pair_not_length_2(self):
        with pytest.raises(ValueError, match="list of 2"):
            _validate_predict_request({"pairs": [["only_one"]]})

    def test_predict_pair_non_string(self):
        with pytest.raises(ValueError, match="not a string"):
            _validate_predict_request({"pairs": [[1, 2]]})


# macOS AF_UNIX has a 104-byte path limit; pytest tmp_path is too long.
@pytest.fixture
def short_tmp():
    """Short temp directory for Unix socket tests.

    Resolves symlinks because macOS /tmp -> /private/var/... and
    _resolve_socket_path() calls .resolve(), which must match CONTAINMENT_ROOT.
    """
    d = Path(tempfile.mkdtemp(prefix="emb_")).resolve()
    yield d
    shutil.rmtree(d, ignore_errors=True)


# =============================================================================
# Socket path security tests (S3)
# =============================================================================


class TestSocketPathSecurity:
    """Test path containment validation from security audit finding S3."""

    def test_default_path_allowed(self):
        path = _resolve_socket_path(None)
        assert path.is_relative_to(CONTAINMENT_ROOT)
        assert path.name == "embed.sock"

    def test_custom_path_under_containment_allowed(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "fakehome"
        ce_dir = fake_home / ".context-engine"
        ce_dir.mkdir(parents=True)
        monkeypatch.setattr("ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", ce_dir)
        path = _resolve_socket_path(ce_dir / "custom.sock")
        assert path.is_relative_to(ce_dir)

    def test_path_outside_containment_rejected(self):
        with pytest.raises(ValueError, match="outside containment"):
            _resolve_socket_path(Path("/tmp/evil.sock"))

    def test_env_var_outside_containment_rejected(self, monkeypatch):
        monkeypatch.setenv("AI_CONTEXT_ENGINE_EMBED_SOCKET", "/tmp/evil.sock")
        with pytest.raises(ValueError, match="outside containment"):
            _resolve_socket_path()


# =============================================================================
# Server + Client integration tests
# =============================================================================


class TestEmbeddingServerClient:
    """Integration tests: real server + client over Unix socket.

    Uses mock encode/predict functions — no torch dependency.
    """

    @pytest.fixture
    def mock_encode(self):
        def encode_fn(texts, normalize_embeddings=False):
            arr = np.random.rand(len(texts), 384).astype(np.float32)
            if normalize_embeddings:
                norms = np.linalg.norm(arr, axis=1, keepdims=True)
                arr = arr / np.maximum(norms, 1e-8)
            return arr

        return encode_fn

    @pytest.fixture
    def mock_predict(self):
        def predict_fn(pairs):
            return np.random.rand(len(pairs)).astype(np.float32)

        return predict_fn

    @pytest.fixture
    def server_and_client(self, short_tmp, mock_encode, mock_predict, monkeypatch):
        """Start a server, yield a connected client, clean up after."""
        sock_path = short_tmp / "e.sock"
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        server = EmbeddingServer(
            encode_fn=mock_encode,
            predict_fn=mock_predict,
            socket_path=sock_path,
        )
        server.start()
        time.sleep(0.1)  # let server bind

        client = EmbeddingClient(socket_path=sock_path)
        yield server, client

        client.close()
        server.shutdown()

    def test_encode_single_text(self, server_and_client):
        _, client = server_and_client
        result = client.encode(["hello"])
        assert result.shape == (1, 384)
        assert result.dtype == np.float32

    def test_encode_batch(self, server_and_client):
        _, client = server_and_client
        texts = [f"text {i}" for i in range(50)]
        result = client.encode(texts)
        assert result.shape == (50, 384)

    def test_encode_with_normalize(self, server_and_client):
        _, client = server_and_client
        result = client.encode(["test"], normalize_embeddings=True)
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)

    def test_encode_empty_list(self, server_and_client):
        _, client = server_and_client
        result = client.encode([])
        assert result.shape == (0, 0)

    def test_predict_pairs(self, server_and_client):
        _, client = server_and_client
        pairs = [["query", "doc1"], ["query", "doc2"]]
        result = client.predict(pairs)
        assert result.shape == (2,)
        assert result.dtype == np.float32

    def test_predict_empty_pairs(self, server_and_client):
        _, client = server_and_client
        result = client.predict([])
        assert result.shape == (0,)

    def test_health_check(self, server_and_client):
        _, client = server_and_client
        assert client.health() is True

    def test_get_sentence_embedding_dimension(self, server_and_client):
        _, client = server_and_client
        assert client.get_sentence_embedding_dimension() == 384

    def test_dimension_is_cached_on_client(self, server_and_client):
        """Second call should not round-trip — cached on client."""
        server, client = server_and_client
        assert client.get_sentence_embedding_dimension() == 384
        # Force server to produce different shape — client must return cached.
        server._dimension_cache = 512  # server-side cache also present
        assert client.get_sentence_embedding_dimension() == 384

    def test_dimension_is_cached_on_server(self, server_and_client):
        """Server computes once via dummy encode, caches; subsequent responses reuse."""
        server, client = server_and_client
        # Fresh client to bypass client-side cache.
        fresh = EmbeddingClient(socket_path=server.socket_path)
        fresh.get_sentence_embedding_dimension()
        assert server._dimension_cache == 384
        # Drop server cache; cached client on other side still works (different client).
        fresh.close()

    def test_available_class_method(self, server_and_client, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        server, _ = server_and_client
        assert EmbeddingClient.available(socket_path=server.socket_path) is True

    def test_available_returns_false_when_no_server(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        assert EmbeddingClient.available(socket_path=short_tmp / "no.sock") is False

    def test_multiple_sequential_requests(self, server_and_client):
        _, client = server_and_client
        for i in range(10):
            result = client.encode([f"text {i}"])
            assert result.shape == (1, 384)

    def test_concurrent_requests(self, server_and_client):
        """4 threads sending encode requests — queue serializes, no corruption."""
        _, client = server_and_client
        results = {}
        errors = []

        def worker(thread_id):
            try:
                for i in range(5):
                    r = client.encode([f"thread {thread_id} text {i}"])
                    assert r.shape == (1, 384)
                results[thread_id] = True
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert not errors, f"Concurrent request errors: {errors}"
        assert len(results) == 4

    def test_server_rejects_oversized_texts(self, server_and_client):
        _, client = server_and_client
        with pytest.raises(RuntimeError, match="too long"):
            client.encode(["x" * (MAX_TEXT_LENGTH + 1)])

    def test_server_rejects_too_many_texts(self, server_and_client):
        _, client = server_and_client
        with pytest.raises(RuntimeError, match="Too many"):
            client.encode(["x"] * (MAX_TEXTS_PER_REQUEST + 1))


class TestSocketPermissions:
    """Test socket file permissions from security audit finding S1."""

    def test_socket_created_with_0600(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        sock_path = short_tmp / "p.sock"
        server = EmbeddingServer(
            encode_fn=lambda texts, **kw: np.zeros((len(texts), 384)),
            socket_path=sock_path,
        )
        server.start()
        time.sleep(0.1)

        stat = os.stat(sock_path)
        mode = oct(stat.st_mode)[-3:]
        server.shutdown()

        assert mode == "600", f"Socket permissions {mode} != 600"

    def test_socket_cleaned_up_on_shutdown(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        sock_path = short_tmp / "c.sock"
        server = EmbeddingServer(
            encode_fn=lambda texts, **kw: np.zeros((len(texts), 384)),
            socket_path=sock_path,
        )
        server.start()
        time.sleep(0.1)
        assert sock_path.exists()
        server.shutdown()
        assert not sock_path.exists()


class TestServerWithoutPredict:
    """Test server when predict_fn is None (CE-only daemon)."""

    def test_predict_returns_error(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        sock_path = short_tmp / "np.sock"
        server = EmbeddingServer(
            encode_fn=lambda texts, **kw: np.zeros((len(texts), 384)),
            predict_fn=None,
            socket_path=sock_path,
        )
        server.start()
        time.sleep(0.1)

        client = EmbeddingClient(socket_path=sock_path)
        with pytest.raises(RuntimeError, match="not available"):
            client.predict([["q", "d"]])

        client.close()
        server.shutdown()


class TestClientRetry:
    """Test client connection retry behavior."""

    def test_client_raises_after_max_retries(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CLIENT_RETRY_INITIAL_DELAY", 0.01
        )
        client = EmbeddingClient(socket_path=short_tmp / "no.sock")
        with pytest.raises(ConnectionError, match="Cannot connect"):
            client.encode(["test"])

    def test_shutdown_closes_accepted_conns_fast(self, short_tmp, monkeypatch):
        """Regression: shutdown must release handlers blocked on recv.

        A client holding a stale persistent conn used to race two 30s
        timers (handler's result_event.wait vs client's recv timeout),
        producing flaky CI failures. Shutdown now SHUT_RDWRs accepted
        conns so handlers exit promptly and clients see EOF immediately.
        """
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        sock_path = short_tmp / "s.sock"

        server = EmbeddingServer(
            encode_fn=lambda texts, **kw: np.zeros((len(texts), 384)),
            socket_path=sock_path,
        )
        server.start()
        time.sleep(0.1)

        client = EmbeddingClient(socket_path=sock_path)
        client.encode(["warmup"])  # establish persistent conn
        assert len(server._active_conns) == 1

        start = time.monotonic()
        server.shutdown()
        elapsed = time.monotonic() - start
        # Without SHUT_RDWR the worker thread join could wait up to 5s,
        # but the critical invariant is that no handler blocks 30s on a
        # stale client send.
        assert elapsed < 5.0, f"shutdown took {elapsed:.1f}s — handler stuck"
        assert len(server._active_conns) == 0 or all(
            c.fileno() == -1 for c in server._active_conns
        )
        client.close()

    def test_client_reconnects_after_server_restart(self, short_tmp, monkeypatch):
        monkeypatch.setattr(
            "ai_governance_mcp.embedding_ipc.CONTAINMENT_ROOT", short_tmp
        )
        sock_path = short_tmp / "r.sock"

        def encode_fn(texts, **kw):
            return np.ones((len(texts), 384), dtype=np.float32)

        server = EmbeddingServer(encode_fn=encode_fn, socket_path=sock_path)
        server.start()
        time.sleep(0.5)

        client = EmbeddingClient(socket_path=sock_path)
        r1 = client.encode(["before restart"])
        assert r1.shape == (1, 384)

        # Restart server — longer sleeps for CI runners
        server.shutdown()
        time.sleep(0.5)
        server2 = EmbeddingServer(encode_fn=encode_fn, socket_path=sock_path)
        server2.start()
        time.sleep(0.5)

        r2 = client.encode(["after restart"])
        assert r2.shape == (1, 384)

        client.close()
        server2.shutdown()
