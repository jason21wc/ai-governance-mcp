"""Diagnostics distinguish work from idle without changing inference results."""

import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ai_governance_mcp import memory_diagnostics as diagnostics
from ai_governance_mcp import model_runtime as runtime
from ai_governance_mcp.embedding_ipc import EmbeddingServer
from ai_governance_mcp.context_engine.watcher_daemon import _record_memory_tick


@pytest.fixture
def records(monkeypatch):
    rows = []
    monkeypatch.setattr(diagnostics, "is_enabled", lambda: True)
    monkeypatch.setattr(
        diagnostics, "record", lambda event, **kw: rows.append((event, kw))
    )
    return rows


def test_model_observation_keeps_identity_and_omits_content(records):
    output = SimpleNamespace(nbytes=12)
    model = SimpleNamespace(
        device=SimpleNamespace(type="mps"), encode=Mock(return_value=output)
    )
    result = runtime.SerializedModel(model).encode(
        ["private query"], normalize_embeddings=True
    )
    assert result is output
    model.encode.assert_called_once_with(["private query"], normalize_embeddings=True)
    assert [r[0] for r in records] == ["inference_start", "inference_end"]
    assert records[0][1]["total_chars"] == 13
    assert records[0][1]["sample_mps"] is True
    assert records[1][1]["output_bytes"] == 12
    assert records[0][1]["call_id"] == records[1][1]["call_id"]
    assert "private query" not in repr(records)
    assert runtime.activity_snapshot()["active_inference"] == 0


def test_model_exception_survives_and_activity_is_cleared(records):
    failure = ValueError("private details")
    model = SimpleNamespace(
        device=SimpleNamespace(type="cpu"), predict=Mock(side_effect=failure)
    )
    with pytest.raises(ValueError) as raised:
        runtime.SerializedModel(model).predict([["query", "document"]])
    assert raised.value is failure
    assert records[-1][1]["outcome"] == "error"
    assert records[0][1]["sample_mps"] is False
    assert "private details" not in repr(records)
    assert runtime.activity_snapshot()["active_inference"] == 0


def test_index_lifetime_marks_active_and_preserves_result(records):
    output = SimpleNamespace(chunks=[1, 2, 3])

    @runtime.observe_indexing
    def index_project():
        assert runtime.activity_snapshot()["active_indexing"] == 1
        return output

    assert index_project() is output
    assert records[-1][1]["total_chunks"] == 3
    assert runtime.activity_snapshot()["active_indexing"] == 0


def test_index_failure_clears_activity_without_logging_error_text(records):
    @runtime.observe_indexing
    def incremental_update():
        raise RuntimeError("private filename")

    with pytest.raises(RuntimeError, match="private filename"):
        incremental_update()
    assert records[-1][1]["outcome"] == "error"
    assert runtime.activity_snapshot()["active_indexing"] == 0
    assert "private filename" not in repr(records)


def test_incremental_fallback_is_one_active_index_operation(records):
    @runtime.observe_indexing
    def index_project():
        assert runtime.activity_snapshot()["active_indexing"] == 1
        return SimpleNamespace(chunks=[])

    @runtime.observe_indexing
    def incremental_update():
        return index_project()

    incremental_update()
    assert [row[0] for row in records] == ["index_start", "index_end"]
    assert records[0][1]["operation"] == "incremental_update"


def test_tick_reports_corpus_and_queue_without_inference(records):
    server = EmbeddingServer(Mock())
    item = server._admit({"op": "encode", "texts": ["secret"]})
    manager = SimpleNamespace(
        _index_lock=threading.Lock(),
        _loaded_indexes={"private-path": SimpleNamespace(chunks=[1, 2])},
        _loaded_embeddings={"private-path": SimpleNamespace(nbytes=3072)},
    )
    _record_memory_tick(manager, server)
    fields = records[-1][1]
    assert fields["cached_chunks"] == 2
    assert fields["cached_embedding_bytes"] == 3072
    assert fields["ipc_queued_requests"] == 1
    assert fields["ipc_pending_bytes"] == item.size
    assert fields["active_indexing"] == fields["active_inference"] == 0
    server._encode_fn.assert_not_called()
    assert "secret" not in repr(records)
    assert "private-path" not in repr(records)
    server._discard_pending()
    assert server.diagnostic_snapshot()["ipc_pending_bytes"] == 0


def test_tick_does_not_wait_for_index_lock(records):
    lock = threading.Lock()
    lock.acquire()
    try:
        _record_memory_tick(SimpleNamespace(_index_lock=lock))
    finally:
        lock.release()
    assert records[-1][1]["index_snapshot_busy"] is True
    assert "cached_chunks" not in records[-1][1]
