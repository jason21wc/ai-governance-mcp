"""Client replication regressions: tiny indexes, no model loads or stress tests."""

import subprocess
import sys
import threading
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from ai_governance_mcp.context_engine import project_manager as pm_module
from ai_governance_mcp.context_engine.models import ContentChunk, ProjectIndex
from ai_governance_mcp.context_engine.storage.filesystem import FilesystemStorage
from ai_governance_mcp.context_engine.watcher import FileWatcher


@pytest.fixture
def storage(tmp_path, monkeypatch):
    # Replacing the Indexer constructor prevents even optional parser imports.
    monkeypatch.setattr(pm_module, "Indexer", Mock())
    return FilesystemStorage(tmp_path / "indexes")


def save_project(storage, path, revision="one", mode="ondemand"):
    path.mkdir(exist_ok=True)
    pid = storage.project_id_from_path(path)
    chunk = ContentChunk(
        content=f"{revision} content long enough for retrieval body filtering",
        source_path=f"{revision}.py",
        start_line=1,
        end_line=2,
        content_type="code",
        embedding_id=0,
    )
    index = ProjectIndex(
        project_id=pid,
        project_path=str(path),
        chunks=[chunk],
        created_at="2026-09-21T00:00:00+00:00",
        updated_at=revision,
        embedding_model="BAAI/bge-small-en-v1.5",
        index_mode=mode,
    )
    metadata = index.model_dump(exclude={"chunks"})
    storage.save_chunks(pid, [chunk.model_dump()])
    storage.save_embeddings(pid, np.array([[1.0, 0.0]]))
    storage.save_bm25_index(pid, {"tokenized_corpus": [[revision, "content"]]})
    storage.save_code_edges(
        pid,
        [
            {
                "source_path": f"{revision}.py",
                "source_symbol": revision,
                "target_path": "target.py",
                "target_symbol": "target",
                "edge_type": "calls",
            }
        ],
    )
    storage.save_metadata(pid, metadata)
    return index


def manager(storage, **kwargs):
    pm = pm_module.ProjectManager(
        storage=storage,
        max_loaded_projects=1,
        refresh_from_storage=True,
        reranking=False,
        **kwargs,
    )
    pm._semantic_search = Mock(return_value=np.array([1.0]))
    return pm


@pytest.mark.parametrize("entry", ["query", "references", "get", "reindex"])
def test_every_admission_evicts_complete_previous_project(storage, tmp_path, entry):
    paths = [tmp_path / "first", tmp_path / "second"]
    indexes = [save_project(storage, path) for path in paths]
    pm = manager(storage)
    pm.get_or_create_index(paths[0])
    old = indexes[0].project_id
    watcher = Mock()
    pm._watchers[old] = watcher
    pm._indexer.index_project.return_value = indexes[1]
    if entry == "query":
        pm.query_project("content", paths[1])
    elif entry == "references":
        pm.find_references("target", paths[1])
    elif entry == "get":
        pm.get_or_create_index(paths[1])
    else:
        pm.reindex_project(paths[1])
    assert list(pm._loaded_indexes) == [indexes[1].project_id]
    for cache in (pm._loaded_embeddings, pm._loaded_bm25, pm._loaded_code_edges):
        assert old not in cache
    assert old not in pm._watchers
    watcher.stop.assert_called_once()


@pytest.mark.parametrize("entry", ["query", "references", "get"])
def test_external_writer_refreshes_all_cached_search_data(storage, tmp_path, entry):
    path = tmp_path / "project"
    index = save_project(storage, path)
    pm = manager(storage, readonly=True)
    pm.get_or_create_index(path)
    old_bm25 = pm._loaded_bm25[index.project_id]
    save_project(storage, path, revision="two")
    storage.save_embeddings(index.project_id, np.array([[0.0, 1.0]]))
    if entry == "query":
        result = pm.query_project("content", path)
        assert result.results[0].chunk.source_path == "two.py"
    elif entry == "references":
        assert (
            pm.find_references("target", path)["callers"][0]["source_path"] == "two.py"
        )
    else:
        assert pm.get_or_create_index(path).chunks[0].source_path == "two.py"
    assert pm._loaded_indexes[index.project_id].updated_at == "two"
    assert pm._loaded_bm25[index.project_id] is not old_bm25
    assert pm._loaded_embeddings[index.project_id].tolist() == [[0.0, 1.0]]
    assert pm._loaded_code_edges[index.project_id][0]["source_path"] == "two.py"
    assert not pm._watchers


def test_cached_realtime_project_retries_unowned_watcher(storage, tmp_path):
    path = tmp_path / "project"
    save_project(storage, path, mode="realtime")
    pm = manager(storage)
    pm._start_watcher = Mock()  # Simulates another process holding ownership.
    pm.query_project("content", path)
    pm.query_project("content", path)
    assert pm._start_watcher.call_count == 2


def test_stdio_manager_starts_empty_with_one_project_budget(storage, monkeypatch):
    from ai_governance_mcp.context_engine import server

    monkeypatch.setenv("AI_CONTEXT_ENGINE_INDEX_PATH", str(storage.base_path))
    monkeypatch.setattr(server, "_detect_readonly_mode", lambda path: False)
    pm = server._create_project_manager()
    assert pm.max_loaded_projects == 1
    assert pm.refresh_from_storage
    assert not pm._loaded_indexes
    assert not pm._watchers


def test_stdio_main_never_bootstraps_shared_registry(monkeypatch):
    from ai_governance_mcp.context_engine import server

    pm = Mock(readonly=False)
    mcp = Mock(run=AsyncMock())

    @asynccontextmanager
    async def stdio():
        yield (object(), object())

    monkeypatch.setattr(server, "create_server", lambda: (mcp, pm))
    monkeypatch.setattr(server, "stdio_server", stdio)
    monkeypatch.setattr(server.signal, "signal", lambda *args: None)
    monkeypatch.setattr(server.os, "_exit", lambda code: None)
    server.main()
    pm.startup_watchers.assert_not_called()
    pm.shutdown.assert_called_once()


@pytest.fixture
def fake_observer(monkeypatch):
    import watchdog.observers

    observer = Mock()
    monkeypatch.setattr(watchdog.observers, "Observer", lambda: observer)
    return observer


def new_watcher(tmp_path, callback=None):
    return FileWatcher(
        tmp_path,
        callback or Mock(),
        ownership_path=tmp_path / "locks" / "one.lock",
        cooldown_seconds=0,
    )


def test_single_owner_releases_on_stop_without_unlink(tmp_path, fake_observer):
    first, second = new_watcher(tmp_path), new_watcher(tmp_path)
    try:
        first.start()
        second.start()
        assert first.is_running
        assert not second.is_running
        first.stop()
        assert first.ownership_path.exists()
        second.start()
        assert second.is_running
    finally:
        first.stop()
        second.stop()


def test_active_callback_retains_lease_after_stop(tmp_path, fake_observer):
    entered, finish = threading.Event(), threading.Event()

    def callback(changes):
        entered.set()
        assert finish.wait(5)

    first, second = new_watcher(tmp_path, callback), new_watcher(tmp_path)
    first.start()
    thread = threading.Thread(target=first.reconcile)
    thread.start()
    try:
        assert entered.wait(5)
        first.stop()  # Must return without waiting on the callback.
        second.start()
        assert not second.is_running
        finish.set()
        thread.join(5)
        assert not thread.is_alive()
        second.start()
        assert second.is_running
    finally:
        finish.set()
        thread.join(5)
        first.stop()
        second.stop()


def test_ownership_excludes_other_process(tmp_path, fake_observer):
    owner = new_watcher(tmp_path)
    script = """
import os, sys
with open(sys.argv[1], 'a+') as stream:
    try:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(7)
"""
    try:
        owner.start()
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(owner.ownership_path)], timeout=5
        )
        assert result.returncode == 7
        owner.stop()
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(owner.ownership_path)], timeout=5
        )
        assert result.returncode == 0
    finally:
        owner.stop()


def test_takeover_reconciles_and_evicted_callback_cannot_restore_cache(
    storage, tmp_path, fake_observer
):
    path = tmp_path / "project"
    original = save_project(storage, path, mode="realtime")
    pm = manager(storage)
    pm._indexer.load_ignore_patterns.return_value = None
    replacement = original.model_copy(update={"updated_at": "reconciled"})
    pm._indexer.incremental_update.return_value = replacement
    pm.get_or_create_index(path, index_mode="realtime")
    watcher = pm._watchers[original.project_id]
    pm._indexer.incremental_update.assert_called_once_with(
        path, original.project_id, [path]
    )
    assert pm._loaded_indexes[original.project_id] is replacement
    pm._unload_project(original.project_id)
    watcher.on_change([path / "late.py"])
    assert not pm._loaded_indexes
    assert pm._indexer.incremental_update.call_count == 1


def test_invalid_budget_rejected(storage):
    with pytest.raises(ValueError, match="at least one"):
        pm_module.ProjectManager(storage=storage, max_loaded_projects=0)


def test_windows_ownership_locks_same_byte_without_waiting(tmp_path, monkeypatch):
    from ai_governance_mcp.context_engine.watcher import _lock_ownership_file

    backend = SimpleNamespace(locking=Mock(), LK_NBLCK=2)
    monkeypatch.setitem(sys.modules, "msvcrt", backend)
    with (tmp_path / "lock").open("a+") as stream:
        stream.write("existing data")
        stream.flush()
        _lock_ownership_file(stream, windows=True)
        assert stream.tell() == 0
        backend.locking.assert_called_once_with(stream.fileno(), backend.LK_NBLCK, 1)


def test_ownership_backend_error_never_starts_observer(
    tmp_path, fake_observer, monkeypatch
):
    from ai_governance_mcp.context_engine import watcher as watcher_module

    monkeypatch.setattr(
        watcher_module, "_lock_ownership_file", Mock(side_effect=OSError("locked"))
    )
    watcher = new_watcher(tmp_path)
    watcher.start()
    assert not watcher.is_running
    assert watcher._ownership_file is None
    fake_observer.start.assert_not_called()


def test_failed_takeover_retries_without_another_file_event(
    storage, tmp_path, fake_observer, monkeypatch
):
    from ai_governance_mcp.context_engine import watcher as watcher_module

    monkeypatch.setattr(watcher_module.threading, "Timer", Mock())
    path = tmp_path / "project"
    index = save_project(storage, path, mode="realtime")
    pm = manager(storage)
    pm._indexer.load_ignore_patterns.return_value = None
    pm._indexer.incremental_update.side_effect = [RuntimeError("transient"), index]
    try:
        pm.get_or_create_index(path, index_mode="realtime")
        watcher = pm._watchers[index.project_id]
        assert path in watcher._pending_changes
        assert pm._watcher_failures[index.project_id] == 1
        watcher._flush_changes()
        assert pm._indexer.incremental_update.call_count == 2
        assert not watcher._pending_changes
        assert index.project_id not in pm._watcher_failures
    finally:
        pm.shutdown()


@pytest.mark.parametrize("entry", ["query", "references"])
def test_observer_failure_preserves_stored_reads_and_releases_lease(
    storage, tmp_path, fake_observer, entry
):
    path = tmp_path / "project"
    index = save_project(storage, path, mode="realtime")
    pm = manager(storage)
    pm._indexer.load_ignore_patterns.return_value = None
    fake_observer.start.side_effect = PermissionError("observer unavailable")
    if entry == "query":
        assert pm.query_project("content", path).results
    else:
        assert pm.find_references("target", path)["callers"]
    assert not pm._watchers
    assert pm.get_project_status(path).watcher_status == "stopped"
    # A failed start must not strand ownership or make the next attempt fail.
    fake_observer.start.side_effect = None
    pm._indexer.incremental_update.return_value = index
    try:
        pm.query_project("content", path)
        assert index.project_id in pm._watchers
    finally:
        pm.shutdown()


def test_busy_previous_update_defers_new_owner_reconciliation(
    storage, tmp_path, fake_observer, monkeypatch
):
    from ai_governance_mcp.context_engine import watcher as watcher_module

    monkeypatch.setattr(watcher_module.threading, "Timer", Mock())
    path = tmp_path / "project"
    index = save_project(storage, path, mode="realtime")
    pm = manager(storage)
    pm._indexer.load_ignore_patterns.return_value = None
    pm._indexer.incremental_update.return_value = index
    pm._watcher_update_lock.acquire()
    try:
        pm.get_or_create_index(path, index_mode="realtime")
        watcher = pm._watchers[index.project_id]
        pm._indexer.incremental_update.assert_not_called()
        assert path in watcher._pending_changes
    finally:
        pm._watcher_update_lock.release()
    try:
        watcher._flush_changes()
        pm._indexer.incremental_update.assert_called_once()
    finally:
        pm.shutdown()


@pytest.mark.parametrize("stored_mode", ["realtime", "ondemand"])
def test_daemon_recovers_client_lease_without_request_or_file_event(
    storage, tmp_path, fake_observer, stored_mode
):
    from ai_governance_mcp.context_engine.watcher_daemon import _watcher_ownership_loop

    path = tmp_path / "project"
    index = save_project(storage, path, mode=stored_mode)
    client, daemon = manager(storage), manager(storage)
    client._indexer.load_ignore_patterns.return_value = None
    client._indexer.incremental_update.return_value = index
    client.get_or_create_index(path, index_mode="realtime")
    daemon.get_or_create_index(path, index_mode="realtime")
    assert not daemon._watchers
    reconciled = threading.Event()

    def update(*args):
        reconciled.set()
        return index

    daemon._indexer.incremental_update.side_effect = update
    stop = threading.Event()
    thread = threading.Thread(
        target=_watcher_ownership_loop,
        args=(daemon, stop, frozenset({index.project_id}), 0.01),
        daemon=True,
    )
    try:
        client.shutdown()
        thread.start()
        assert reconciled.wait(2)
        with daemon._index_lock:
            assert daemon._watchers[index.project_id].is_running
            assert list(daemon._loaded_indexes) == [index.project_id]
    finally:
        stop.set()
        thread.join(2)
        client.shutdown()
        daemon.shutdown()
    assert not thread.is_alive()


def test_daemon_retry_respects_shutdown_after_waiting_for_index_lock(storage):
    from ai_governance_mcp.context_engine.watcher_daemon import _watcher_ownership_loop

    pm = manager(storage)
    stop = threading.Event()
    pm._ensure_watcher = Mock()
    # The loop has passed wait() but cannot take its project snapshot yet.
    waiting = threading.Event()
    real_wait = stop.wait

    def wait(timeout):
        result = real_wait(timeout)
        waiting.set()
        return result

    stop.wait = wait
    thread = threading.Thread(
        target=_watcher_ownership_loop,
        args=(pm, stop, frozenset({"id"}), 0.001),
        daemon=True,
    )
    with pm._index_lock:
        pm._loaded_indexes["id"] = SimpleNamespace(
            index_mode="realtime", project_path="/unused"
        )
        thread.start()
        assert waiting.wait(2)
        stop.set()
    thread.join(2)
    assert not thread.is_alive()
    pm._ensure_watcher.assert_not_called()


def test_daemon_retry_does_not_discover_unloaded_or_circuit_broken_projects(
    storage, tmp_path
):
    from ai_governance_mcp.context_engine.watcher_daemon import _watcher_ownership_loop

    loaded = save_project(storage, tmp_path / "loaded", mode="realtime")
    save_project(storage, tmp_path / "unloaded", mode="realtime")
    pm = manager(storage)
    pm._loaded_indexes[loaded.project_id] = loaded
    pm._circuit_broken.add(loaded.project_id)
    pm._start_watcher = Mock()
    stop = threading.Event()
    original = pm._ensure_watcher

    def ensure(path, project_id):
        original(path, project_id)
        stop.set()

    pm._ensure_watcher = ensure
    _watcher_ownership_loop(pm, stop, frozenset({loaded.project_id}), 0.001)
    pm._start_watcher.assert_not_called()
    assert list(pm._loaded_indexes) == [loaded.project_id]
