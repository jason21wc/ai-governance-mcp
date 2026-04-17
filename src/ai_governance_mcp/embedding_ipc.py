"""Shared embedding service via Unix socket IPC.

Phase 2 of BACKLOG #49 (plan jiggly-honking-cascade.md). The watcher daemon
runs an EmbeddingServer; MCP server processes use EmbeddingClient to call it
instead of loading their own torch/sentence-transformers models.

Protocol: length-prefixed JSON over AF_UNIX socket.
- Request: 4-byte big-endian uint32 length + UTF-8 JSON
- Response: same framing
- Embedding vectors: base64-encoded float32 ndarray bytes
- No pickle (ADR-7). No authentication (local-only, 0o600 socket permissions).

Security (per audit findings S1-S3):
- Socket created with 0o600 permissions (S1)
- Input size limits matching indexer.py constants (S2)
- Socket path containment under ~/.context-engine/ (S3)

Thread safety (per contrarian Finding 4):
- Single-worker queue pattern — all encode/predict calls serialized through
  one worker thread. No concurrent SentenceTransformer.encode() calls.
"""

import base64
import json
import logging
import os
import queue
import socket
import struct
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("ai_governance_mcp.embedding_ipc")

DEFAULT_SOCKET_PATH = Path.home() / ".context-engine" / "embed.sock"
CONTAINMENT_ROOT = Path.home() / ".context-engine"

MAX_MESSAGE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_TEXTS_PER_REQUEST = 1000  # matches EMBEDDING_BATCH_SIZE
MAX_TEXT_LENGTH = 6000  # matches MAX_EMBEDDING_INPUT_CHARS
MAX_PAIRS_PER_REQUEST = 1000

HEADER_SIZE = 4  # uint32 big-endian
SOCKET_BACKLOG = 16
CONNECTION_TIMEOUT = 30.0
CLIENT_RETRY_ATTEMPTS = 5
CLIENT_RETRY_INITIAL_DELAY = 0.2


def _resolve_socket_path(path: str | Path | None = None) -> Path:
    """Resolve and validate the socket path.

    Security (S3): socket must be under ~/.context-engine/.
    """
    if path is None:
        env = os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip()
        # "none" is a magic disable signal, not a path literal. Callers gate
        # on it before instantiating the client; if they bypass, fall through
        # to the default path rather than treating "none" as a filename.
        if env and env.lower() != "none":
            path = Path(env).expanduser().resolve()
        else:
            path = DEFAULT_SOCKET_PATH
    else:
        path = Path(path).expanduser().resolve()

    if not path.is_relative_to(CONTAINMENT_ROOT):
        raise ValueError(
            f"Socket path {path} is outside containment root {CONTAINMENT_ROOT}. "
            f"Security policy requires sockets under ~/.context-engine/."
        )
    return path


def _encode_message(data: dict) -> bytes:
    """Serialize a dict to length-prefixed JSON bytes."""
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return struct.pack(">I", len(payload)) + payload


def _decode_message(sock: socket.socket) -> dict:
    """Read a length-prefixed JSON message from a socket."""
    header = _recv_exactly(sock, HEADER_SIZE)
    if header is None:
        raise ConnectionError("Connection closed while reading header")
    length = struct.unpack(">I", header)[0]
    if length > MAX_MESSAGE_BYTES:
        raise ValueError(f"Message too large: {length} > {MAX_MESSAGE_BYTES}")
    payload = _recv_exactly(sock, length)
    if payload is None:
        raise ConnectionError("Connection closed while reading payload")
    return json.loads(payload.decode("utf-8"))


def _recv_exactly(sock: socket.socket, n: int) -> bytes | None:
    """Read exactly n bytes from a socket. Returns None on EOF."""
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(min(remaining, 65536))
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _ndarray_to_base64(arr: np.ndarray) -> str:
    """Encode a float32 ndarray as base64 for JSON transport."""
    return base64.b64encode(arr.astype(np.float32).tobytes()).decode("ascii")


def _base64_to_ndarray(data: str, shape: list[int]) -> np.ndarray:
    """Decode base64 back to a float32 ndarray with shape validation."""
    raw = base64.b64decode(data)
    expected_bytes = 1
    for dim in shape:
        expected_bytes *= dim
    expected_bytes *= 4  # float32
    if len(raw) != expected_bytes:
        raise ValueError(
            f"base64 decoded {len(raw)} bytes, expected {expected_bytes} "
            f"for shape {shape} float32"
        )
    return np.frombuffer(raw, dtype=np.float32).reshape(shape)


def _validate_encode_request(data: dict) -> None:
    """Validate an encode request against size limits (S2)."""
    texts = data.get("texts", [])
    if not isinstance(texts, list):
        raise ValueError("'texts' must be a list")
    if len(texts) > MAX_TEXTS_PER_REQUEST:
        raise ValueError(f"Too many texts: {len(texts)} > {MAX_TEXTS_PER_REQUEST}")
    for i, t in enumerate(texts):
        if not isinstance(t, str):
            raise ValueError(f"texts[{i}] is not a string")
        if len(t) > MAX_TEXT_LENGTH:
            raise ValueError(f"texts[{i}] too long: {len(t)} > {MAX_TEXT_LENGTH}")


def _validate_predict_request(data: dict) -> None:
    """Validate a predict request against size limits (S2)."""
    pairs = data.get("pairs", [])
    if not isinstance(pairs, list):
        raise ValueError("'pairs' must be a list")
    if len(pairs) > MAX_PAIRS_PER_REQUEST:
        raise ValueError(f"Too many pairs: {len(pairs)} > {MAX_PAIRS_PER_REQUEST}")
    for i, pair in enumerate(pairs):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"pairs[{i}] must be a list of 2 strings")
        for j, s in enumerate(pair):
            if not isinstance(s, str):
                raise ValueError(f"pairs[{i}][{j}] is not a string")


# =============================================================================
# Server
# =============================================================================


class EmbeddingServer:
    """Unix socket server for shared embedding inference.

    Runs in the watcher daemon process. Accepts encode/predict requests,
    dispatches to a single worker thread that owns model access.

    Args:
        encode_fn: Callable matching SentenceTransformer.encode() signature.
            encode_fn(texts: list[str], normalize_embeddings: bool) -> np.ndarray
        predict_fn: Callable matching CrossEncoder.predict() signature.
            predict_fn(pairs: list[list[str]]) -> np.ndarray
            Can be None if reranking is not available (CE-only daemon).
        socket_path: Path for the Unix socket. Default ~/.context-engine/embed.sock.
    """

    def __init__(
        self,
        encode_fn,
        predict_fn=None,
        socket_path: str | Path | None = None,
    ):
        self._encode_fn = encode_fn
        self._predict_fn = predict_fn
        self._socket_path = _resolve_socket_path(socket_path)
        self._work_queue: queue.Queue = queue.Queue()
        self._server_socket: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._dimension_cache: int | None = None
        # Track accepted connections so shutdown can close them, releasing
        # handler threads blocked in recv. Without this, a client reusing
        # its persistent conn after the server shut down would deadlock:
        # the handler queues work to a dead worker, times out at 30s, and
        # sends a "Worker timeout" response — racing the client's own 30s
        # recv timeout and causing flaky failures on CI.
        self._active_conns: set[socket.socket] = set()
        self._conns_lock = threading.Lock()

    @property
    def socket_path(self) -> Path:
        return self._socket_path

    def start(self) -> None:
        """Start the server: bind socket, start worker + accept threads."""
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean up stale socket
        if self._socket_path.exists():
            try:
                self._socket_path.unlink()
            except OSError:
                pass

        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket.bind(str(self._socket_path))
        os.chmod(str(self._socket_path), 0o600)  # Security (S1)
        self._server_socket.listen(SOCKET_BACKLOG)
        self._server_socket.settimeout(1.0)

        self._stop_event.clear()

        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="embed-worker", daemon=True
        )
        self._worker_thread.start()

        self._accept_thread = threading.Thread(
            target=self._accept_loop, name="embed-accept", daemon=True
        )
        self._accept_thread.start()

        logger.info("EmbeddingServer started on %s", self._socket_path)

    def shutdown(self) -> None:
        """Stop the server: close socket, drain queue, join threads."""
        self._stop_event.set()

        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

        # Shut down accepted connections so handler threads unblock from
        # recv and exit promptly. Without this, a client reusing a stale
        # persistent conn after shutdown deadlocks the handler on a dead
        # worker for 30s and races the client's own recv timeout.
        with self._conns_lock:
            for conn in list(self._active_conns):
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

        if self._accept_thread and self._accept_thread.is_alive():
            self._accept_thread.join(timeout=5.0)
        if self._worker_thread and self._worker_thread.is_alive():
            self._work_queue.put(None)  # sentinel
            self._worker_thread.join(timeout=5.0)

        # Clean up socket file
        try:
            self._socket_path.unlink(missing_ok=True)
        except OSError:
            pass

        logger.info("EmbeddingServer stopped")

    def _accept_loop(self) -> None:
        """Accept connections and spawn handler threads."""
        while not self._stop_event.is_set():
            try:
                conn, _ = self._server_socket.accept()
                conn.settimeout(CONNECTION_TIMEOUT)
                # Register the conn before spawning the handler, but under
                # the same lock that shutdown uses — otherwise shutdown can
                # snapshot _active_conns between accept() returning and add(),
                # leaving this conn unreachable for SHUT_RDWR. Recheck
                # stop_event under the lock so a late arrival is released.
                with self._conns_lock:
                    if self._stop_event.is_set():
                        try:
                            conn.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                        try:
                            conn.close()
                        except OSError:
                            pass
                        break
                    self._active_conns.add(conn)
                handler = threading.Thread(
                    target=self._handle_connection,
                    args=(conn,),
                    daemon=True,
                )
                handler.start()
            except socket.timeout:
                continue
            except OSError:
                if not self._stop_event.is_set():
                    logger.warning("Accept error (server shutting down?)")
                break

    def _handle_connection(self, conn: socket.socket) -> None:
        """Handle a single client connection: read request, queue work, send response."""
        try:
            while not self._stop_event.is_set():
                try:
                    request = _decode_message(conn)
                except ConnectionError:
                    break
                except OSError as e:
                    # Shutdown SHUT_RDWR is expected; anything else is a mid-
                    # request network glitch we don't want to silently eat.
                    if not self._stop_event.is_set():
                        logger.debug("Connection error reading request: %s", e)
                    break
                except ValueError as e:
                    response = {"ok": False, "error": str(e)}
                    try:
                        conn.sendall(_encode_message(response))
                    except OSError:
                        pass
                    break

                # Don't queue work if the server is shutting down — the worker
                # may already be gone, which would cause a 30s handler timeout
                # that races the client's own recv timeout.
                if self._stop_event.is_set():
                    break

                result_event = threading.Event()
                result_holder: dict = {}

                self._work_queue.put((request, result_holder, result_event))
                result_event.wait(timeout=CONNECTION_TIMEOUT)

                if not result_event.is_set():
                    response = {"ok": False, "error": "Worker timeout"}
                else:
                    response = result_holder.get(
                        "response", {"ok": False, "error": "No response"}
                    )

                try:
                    conn.sendall(_encode_message(response))
                except OSError:
                    break
        finally:
            with self._conns_lock:
                self._active_conns.discard(conn)
            try:
                conn.close()
            except OSError:
                pass

    def _worker_loop(self) -> None:
        """Single worker thread that owns all model access. Serializes encode/predict."""
        while not self._stop_event.is_set():
            try:
                item = self._work_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if item is None:  # shutdown sentinel
                break

            request, result_holder, result_event = item
            try:
                response = self._dispatch(request)
            except Exception as e:
                logger.error("Worker error: %s", e)
                response = {"ok": False, "error": str(e)}
            result_holder["response"] = response
            result_event.set()

    def _dispatch(self, request: dict) -> dict:
        """Route a request to the appropriate handler."""
        op = request.get("op")
        if op == "encode":
            return self._handle_encode(request)
        elif op == "predict":
            return self._handle_predict(request)
        elif op == "dimension":
            return self._handle_dimension()
        elif op == "health":
            return {"ok": True, "status": "healthy"}
        else:
            return {"ok": False, "error": f"Unknown operation: {op}"}

    def _handle_dimension(self) -> dict:
        if self._dimension_cache is None:
            # Probe without normalize_embeddings — dimension is invariant
            # and the kwarg is not part of the encode_fn contract.
            probe = self._encode_fn(["."])
            self._dimension_cache = int(np.asarray(probe).shape[-1])
        return {"ok": True, "dimension": self._dimension_cache}

    def _handle_encode(self, request: dict) -> dict:
        _validate_encode_request(request)
        texts = request["texts"]
        normalize = request.get("normalize", False)
        if not texts:
            return {"ok": True, "data": "", "shape": [0, 0]}
        result = self._encode_fn(texts, normalize_embeddings=normalize)
        return {
            "ok": True,
            "data": _ndarray_to_base64(result),
            "shape": list(result.shape),
        }

    def _handle_predict(self, request: dict) -> dict:
        if self._predict_fn is None:
            return {"ok": False, "error": "Reranking not available on this server"}
        _validate_predict_request(request)
        pairs = request["pairs"]
        if not pairs:
            return {"ok": True, "data": "", "shape": [0]}
        result = self._predict_fn(pairs)
        arr = np.asarray(result, dtype=np.float32)
        return {
            "ok": True,
            "data": _ndarray_to_base64(arr),
            "shape": list(arr.shape),
        }


# =============================================================================
# Client
# =============================================================================


class EmbeddingClient:
    """Client for the shared embedding service.

    Connects to the watcher daemon's Unix socket and exposes .encode() and
    .predict() with signatures matching SentenceTransformer/CrossEncoder.

    When the socket is unavailable, raises ConnectionError. Callers should
    catch this and fall back to BM25-only search (NOT local model load).
    """

    def __init__(self, socket_path: str | Path | None = None):
        self._socket_path = _resolve_socket_path(socket_path)
        self._conn: socket.socket | None = None
        self._lock = threading.Lock()
        self._dimension_cache: int | None = None

    def _connect(self) -> socket.socket:
        """Connect to the server with retry + backoff."""
        delay = CLIENT_RETRY_INITIAL_DELAY
        last_error = None
        for attempt in range(CLIENT_RETRY_ATTEMPTS):
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(CONNECTION_TIMEOUT)
                sock.connect(str(self._socket_path))
                return sock
            except (OSError, ConnectionRefusedError) as e:
                last_error = e
                if attempt < CLIENT_RETRY_ATTEMPTS - 1:
                    time.sleep(delay)
                    delay *= 2
                try:
                    sock.close()
                except OSError:
                    pass
        raise ConnectionError(
            f"Cannot connect to embedding server at {self._socket_path} "
            f"after {CLIENT_RETRY_ATTEMPTS} attempts: {last_error}"
        )

    def _ensure_connected(self) -> socket.socket:
        """Get or create a connection (persistent per client instance)."""
        if self._conn is not None:
            return self._conn
        self._conn = self._connect()
        return self._conn

    def _request(self, data: dict) -> dict:
        """Send a request and receive a response. Reconnects on failure."""
        with self._lock:
            try:
                conn = self._ensure_connected()
                conn.sendall(_encode_message(data))
                response = _decode_message(conn)
            except (OSError, ConnectionError):
                self._close()
                conn = self._connect()
                self._conn = conn
                conn.sendall(_encode_message(data))
                response = _decode_message(conn)

        if not response.get("ok"):
            raise RuntimeError(
                f"Embedding server error: {response.get('error', 'unknown')}"
            )
        return response

    def _close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None

    def close(self) -> None:
        """Explicitly close the connection."""
        with self._lock:
            self._close()

    def encode(
        self,
        texts: list[str],
        normalize_embeddings: bool = False,
        show_progress_bar: bool = False,
        **kwargs,
    ) -> np.ndarray:
        """Encode texts to embeddings via the shared server.

        Matches SentenceTransformer.encode() signature for drop-in replacement.
        show_progress_bar is accepted but ignored (progress is server-side).
        """
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        response = self._request(
            {
                "op": "encode",
                "texts": texts,
                "normalize": normalize_embeddings,
            }
        )
        return _base64_to_ndarray(response["data"], response["shape"])

    def predict(self, pairs: list[list[str]], **kwargs) -> np.ndarray:
        """Score query-document pairs via the shared server.

        Matches CrossEncoder.predict() signature for drop-in replacement.
        """
        if not pairs:
            return np.zeros(0, dtype=np.float32)
        response = self._request(
            {
                "op": "predict",
                "pairs": pairs,
            }
        )
        return _base64_to_ndarray(response["data"], response["shape"])

    def health(self) -> bool:
        """Check if the server is responsive."""
        try:
            response = self._request({"op": "health"})
            return response.get("ok", False)
        except (ConnectionError, RuntimeError):
            return False

    def get_sentence_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by the server's model.

        Matches SentenceTransformer.get_sentence_embedding_dimension() so
        EmbeddingClient is a drop-in replacement. Cached after first call.
        """
        if self._dimension_cache is None:
            response = self._request({"op": "dimension"})
            self._dimension_cache = int(response["dimension"])
        return self._dimension_cache

    @classmethod
    def available(cls, socket_path: str | Path | None = None) -> bool:
        """Check if an embedding server is reachable at the socket path."""
        try:
            client = cls(socket_path=socket_path)
            result = client.health()
            client.close()
            return result
        except (ConnectionError, ValueError, OSError):
            return False
