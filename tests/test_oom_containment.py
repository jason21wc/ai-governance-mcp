"""OOM regressions without real models or memory-stress allocations."""

import builtins
import queue
import signal
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

if sys.platform == "win32":
    pytest.skip("POSIX watcher containment tests", allow_module_level=True)

import fcntl

from ai_governance_mcp import embedding_ipc as ipc
from ai_governance_mcp.context_engine import watcher_supervisor as supervisor
from ai_governance_mcp.model_runtime import (
    INFERENCE_LOCK,
    ModelServiceUnavailable,
    SerializedModel,
    require_local_opt_in,
)


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "bad", "255"])
def test_invalid_limit_never_disables_protection(monkeypatch, value):
    monkeypatch.setenv("AI_CONTEXT_ENGINE_WATCHER_MAX_MEMORY_MIB", value)
    with pytest.raises(ValueError):
        supervisor.memory_limit_bytes()


def test_default_limit(monkeypatch):
    monkeypatch.delenv("AI_CONTEXT_ENGINE_WATCHER_MAX_MEMORY_MIB", raising=False)
    assert supervisor.memory_limit_bytes() == 8 * 1024**3


@pytest.mark.parametrize(
    "footprint,pressure,reason",
    [(1024, 1, "memory_limit"), (1, 4, "critical_pressure")],
)
def test_bootstrap_is_monitored_before_readiness(footprint, pressure, reason):
    child = SimpleNamespace(pid=123, poll=lambda: None)
    probe = SimpleNamespace(footprint=lambda _: footprint, pressure=lambda: pressure)
    publish = Mock()
    assert (
        supervisor.monitor_worker(child, probe, 1024, threading.Event(), publish)
        == reason
    )
    publish.assert_called_once_with(reason, 123, footprint, pressure)


def test_metric_failure_is_not_a_zero_sample():
    child = SimpleNamespace(pid=123, poll=lambda: None)
    probe = SimpleNamespace(footprint=Mock(side_effect=OSError("denied")))
    with pytest.raises(OSError):
        supervisor.monitor_worker(child, probe, 1024, threading.Event(), Mock())


def test_default_cleanup_beats_launchd_deadline_and_spares_other_process():
    command = [
        sys.executable,
        "-c",
        "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(30)",
    ]
    child = subprocess.Popen(
        command, start_new_session=True, stdout=subprocess.PIPE, text=True
    )
    other = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True
    )
    try:
        assert child.stdout.readline().strip() == "ready"
        started = time.monotonic()
        supervisor.terminate_worker(child)
        # The installed launchd job allows five seconds before killing its parent.
        # Exercise the production default, leaving margin for supervisor cleanup.
        assert time.monotonic() - started < 4.0
        assert child.returncode == -signal.SIGKILL
        assert other.poll() is None
    finally:
        for proc in (child, other):
            if proc.poll() is None:
                supervisor.terminate_worker(proc, grace=0.1)
        child.stdout.close()


def test_supervisor_exception_cleans_child_and_backs_off(monkeypatch, tmp_path):
    stop = threading.Event()
    # Return the real event to the supervisor, but end on its backoff wait.
    original_wait = stop.wait

    def wait(delay):
        stop.set()
        return original_wait(0)

    monkeypatch.setattr(stop, "wait", wait)
    monkeypatch.setattr(supervisor.threading, "Event", lambda: stop)
    monkeypatch.setattr(
        supervisor, "MemoryProbe", lambda: SimpleNamespace(pressure=lambda: 1)
    )
    child = SimpleNamespace(pid=321)
    spawn = Mock(return_value=child)
    cleanup = Mock()
    monkeypatch.setattr(supervisor.subprocess, "Popen", spawn)
    monkeypatch.setattr(
        supervisor, "monitor_worker", Mock(side_effect=OSError("probe failed"))
    )
    monkeypatch.setattr(supervisor, "terminate_worker", cleanup)
    supervisor.supervise(tmp_path / "indexes", ["--all"])
    cleanup.assert_called_once_with(child)
    assert spawn.call_args.kwargs["start_new_session"] is True


def test_pressure_prevents_bootstrap(monkeypatch, tmp_path):
    stop = threading.Event()
    monkeypatch.setattr(stop, "wait", lambda _: stop.set())
    monkeypatch.setattr(supervisor.threading, "Event", lambda: stop)
    monkeypatch.setattr(
        supervisor, "MemoryProbe", lambda: SimpleNamespace(pressure=lambda: 4)
    )
    spawn = Mock()
    monkeypatch.setattr(supervisor.subprocess, "Popen", spawn)
    supervisor.supervise(tmp_path / "indexes", [])
    spawn.assert_not_called()


def test_duplicate_supervisor_cannot_spawn(monkeypatch, tmp_path):
    monkeypatch.setattr(supervisor, "MemoryProbe", Mock())
    spawn = Mock()
    monkeypatch.setattr(supervisor.subprocess, "Popen", spawn)
    with (tmp_path / "watcher-supervisor.lock").open("a") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="already owns"):
            supervisor.supervise(tmp_path / "indexes", [])
    spawn.assert_not_called()


@pytest.mark.parametrize("socket_value", ["", "/missing.sock"])
@pytest.mark.parametrize("consumer", ["embedder", "reranker", "indexer"])
def test_unavailable_service_never_imports_model(monkeypatch, socket_value, consumer):
    from ai_governance_mcp.retrieval import RetrievalEngine
    from ai_governance_mcp.context_engine.indexer import Indexer

    monkeypatch.setenv("AI_CONTEXT_ENGINE_EMBED_SOCKET", socket_value)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"sentence_transformers", "torch", "transformers"}:
            pytest.fail("unavailable daemon attempted a local model import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    if consumer == "indexer":
        engine = Indexer(storage=Mock())
        attr = "embedding_model"
    else:
        engine = RetrievalEngine.__new__(RetrievalEngine)
        engine._embedder = engine._reranker = None
        engine._model_lock = threading.Lock()
        monkeypatch.setattr(engine, "_try_embedding_client", lambda: False)
        monkeypatch.setattr(engine, "_try_reranker_client", lambda: False)
        attr = consumer
    with pytest.raises(ModelServiceUnavailable):
        getattr(engine, attr)


def test_explicit_standalone_opt_in(monkeypatch):
    monkeypatch.setenv("AI_CONTEXT_ENGINE_EMBED_SOCKET", "none")
    require_local_opt_in()


def make_server(monkeypatch, tmp_path, encode=None):
    monkeypatch.setattr(ipc, "CONTAINMENT_ROOT", tmp_path)
    return ipc.EmbeddingServer(encode or Mock(), socket_path=tmp_path / "test.sock")


def test_admission_bounds_and_shutdown_release(monkeypatch, tmp_path):
    server = make_server(monkeypatch, tmp_path)
    items = [server._admit({"op": "health"}) for _ in range(ipc.MAX_PENDING_REQUESTS)]
    with pytest.raises(queue.Full):
        server._admit({"op": "health"})
    assert server._pending_bytes > 0
    server.shutdown()
    assert server._pending_bytes == 0
    assert server._work_queue.empty()
    assert all(item.done.is_set() and item.cancelled.is_set() for item in items)


def test_byte_admission_and_invalid_input(monkeypatch, tmp_path):
    server = make_server(monkeypatch, tmp_path)
    monkeypatch.setattr(ipc, "MAX_PENDING_BYTES", 1)
    with pytest.raises(queue.Full):
        server._admit({"op": "encode", "texts": ["hello"]})
    with pytest.raises(ValueError):
        server._admit([])
    with pytest.raises(ValueError):
        server._admit({"op": "encode", "texts": ["x"] * 1001})
    assert server._pending_bytes == 0


def test_expired_request_waiting_for_indexer_lock_never_runs(monkeypatch, tmp_path):
    encode = Mock(return_value=np.zeros((1, 3)))
    server = make_server(monkeypatch, tmp_path, encode)
    item = server._admit({"op": "encode", "texts": ["hello"]})
    worker = threading.Thread(target=server._worker_loop)
    with INFERENCE_LOCK:
        worker.start()
        # The worker cannot dispatch while the direct indexer owns inference.
        item.deadline = time.monotonic() - 1
    try:
        assert item.done.wait(2)
        encode.assert_not_called()
        assert server._pending_bytes == 0
    finally:
        server._stop_event.set()
        worker.join(2)
        assert not worker.is_alive()


def test_cancelled_request_never_runs(monkeypatch, tmp_path):
    encode = Mock()
    server = make_server(monkeypatch, tmp_path, encode)
    item = server._admit({"op": "encode", "texts": ["hello"]})
    item.cancelled.set()
    worker = threading.Thread(target=server._worker_loop)
    worker.start()
    try:
        assert item.done.wait(2)
        encode.assert_not_called()
    finally:
        server._stop_event.set()
        worker.join(2)


def test_direct_model_and_ipc_share_inference_lock(monkeypatch, tmp_path):
    entered = threading.Event()
    release = threading.Event()
    ipc_called = threading.Event()

    def direct_encode(*args, **kwargs):
        entered.set()
        assert release.wait(2)

    model = SerializedModel(SimpleNamespace(encode=direct_encode))
    direct = threading.Thread(target=model.encode, args=(["index"],))

    def remote_encode(*args, **kwargs):
        ipc_called.set()
        return np.zeros((1, 3))

    server = make_server(monkeypatch, tmp_path, remote_encode)
    direct.start()
    assert entered.wait(2)
    item = server._admit({"op": "encode", "texts": ["query"]})
    worker = threading.Thread(target=server._worker_loop)
    worker.start()
    try:
        assert not ipc_called.wait(0.05)
        release.set()
        assert item.done.wait(2)
        assert ipc_called.is_set()
    finally:
        release.set()
        server._stop_event.set()
        worker.join(2)
        direct.join(2)


def test_parent_pipe_eof_kills_worker_and_descendant():
    import select
    import os

    read_fd, write_fd = os.pipe()
    code = """
import subprocess, sys, time
from ai_governance_mcp.context_engine.watcher_supervisor import watch_parent
subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
watch_parent(int(sys.argv[1]))
print("ready", flush=True)
time.sleep(30)
"""
    child = subprocess.Popen(
        [sys.executable, "-c", code, str(read_fd)],
        start_new_session=True,
        pass_fds=(read_fd,),
        stdout=subprocess.PIPE,
        text=True,
    )
    os.close(read_fd)
    try:
        assert child.stdout.readline().strip() == "ready"
        os.close(write_fd)
        write_fd = None
        assert child.wait(timeout=3) in (-signal.SIGKILL, 70)
        # The helper inherits stdout. EOF proves it closed too, without ps/PID guessing.
        assert select.select([child.stdout], [], [], 3)[0]
        assert child.stdout.read(1) == ""
    finally:
        if write_fd is not None:
            os.close(write_fd)
        supervisor.terminate_worker(child, grace=0.1)
        child.stdout.close()


def test_connection_cap_recovers_after_slot_is_released(monkeypatch):
    import socket
    import tempfile
    from pathlib import Path

    monkeypatch.setattr(ipc, "MAX_CONNECTIONS", 2)
    with tempfile.TemporaryDirectory(prefix="oom-ipc-") as directory:
        root = Path(directory)
        server = make_server(monkeypatch, root)
        sockets = []

        def connect():
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            conn.settimeout(2)
            conn.connect(str(server.socket_path))
            sockets.append(conn)
            return conn

        def health(conn):
            conn.sendall(ipc._encode_message({"op": "health"}))
            return ipc._decode_message(conn)

        server.start()
        try:
            first, second = connect(), connect()
            assert health(first)["ok"] and health(second)["ok"]
            excess = connect()
            assert excess.recv(1) == b""
            first.close()
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                with server._conns_lock:
                    if len(server._active_conns) == 1:
                        break
                time.sleep(0.01)
            assert health(connect())["ok"]
            with server._conns_lock:
                assert len(server._active_conns) == 2
        finally:
            for conn in sockets:
                conn.close()
            server.shutdown()


def test_cleanup_clears_only_owned_worker_markers(tmp_path):
    import json

    (tmp_path / "watcher.pid").write_text("123")
    (tmp_path / "watcher-heartbeat.json").write_text(json.dumps({"pid": 456}))
    supervisor.clear_worker_markers(tmp_path / "indexes", 123)
    assert not (tmp_path / "watcher.pid").exists()
    assert (tmp_path / "watcher-heartbeat.json").exists()
    supervisor.clear_worker_markers(tmp_path / "indexes", 456)
    assert not (tmp_path / "watcher-heartbeat.json").exists()
