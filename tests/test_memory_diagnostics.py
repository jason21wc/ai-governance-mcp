"""Diagnostic measurements must never turn into another memory hazard."""

import builtins
import json
import sys
import threading
import subprocess
import os
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ai_governance_mcp import memory_diagnostics as diagnostics


@pytest.fixture(autouse=True)
def clean_diagnostics(monkeypatch):
    shutdown_writer()
    monkeypatch.setattr(diagnostics, "_failures", 0)
    monkeypatch.setattr(
        diagnostics, "_probe", SimpleNamespace(footprint=lambda pid: 1024)
    )
    monkeypatch.setattr(diagnostics.tracemalloc, "is_tracing", lambda: False)
    yield
    shutdown_writer()


def shutdown_writer():
    diagnostics.close()
    if diagnostics._writer is not None:
        diagnostics._writer.thread.join(timeout=1)
        assert not diagnostics._writer.thread.is_alive()


def records(path):
    assert diagnostics._wait_for_idle()
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_disabled_has_no_probe_or_file_side_effects(monkeypatch, tmp_path):
    probe = Mock(side_effect=AssertionError("must stay disabled"))
    monkeypatch.setattr(diagnostics, "_get_probe", probe)
    assert not diagnostics.is_enabled()
    diagnostics.record("heartbeat")
    probe.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_record_includes_metrics_and_never_imports_heavy_dependencies(
    monkeypatch, tmp_path
):
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"torch", "numpy", "sentence_transformers"}
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    assert diagnostics.is_enabled()
    diagnostics.record(
        "inference_start", operation="encode", input_items=3, sample_mps=True
    )
    row = records(path)[0]
    assert row["physical_footprint_bytes"] == 1024
    assert row["input_items"] == 3
    assert row["operation"] == "encode"
    assert row["pid"] > 0 and row["monotonic_seconds"] > 0
    assert row["python_traced_current_bytes"] is None
    assert row["mps_current_bytes"] is None
    assert "sample_mps" not in row
    assert row["telemetry_failures"] == 0


def test_mps_is_opt_in_and_uses_only_counters(monkeypatch, tmp_path):
    mps = SimpleNamespace(
        current_allocated_memory=Mock(return_value=10),
        driver_allocated_memory=Mock(return_value=20),
        synchronize=Mock(side_effect=AssertionError),
        empty_cache=Mock(side_effect=AssertionError),
    )
    torch = SimpleNamespace(
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: True)),
        mps=mps,
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    mps.current_allocated_memory.assert_not_called()
    diagnostics.record("inference_end", sample_mps=True)
    row = records(path)[1]
    assert row["mps_current_bytes"] == 10
    assert row["mps_driver_bytes"] == 20
    mps.synchronize.assert_not_called()
    mps.empty_cache.assert_not_called()


def test_metric_failure_is_null_with_fixed_label_never_exception_text(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        diagnostics, "_get_probe", Mock(side_effect=OSError("sensitive exception body"))
    )
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    row = records(path)[0]
    assert row["physical_footprint_bytes"] is None
    assert row["footprint_error"] == "unavailable"
    assert row["metric_error_count"] == 1
    assert "sensitive" not in path.read_text()


def test_existing_tracing_is_sampled_but_never_started(monkeypatch, tmp_path):
    monkeypatch.setattr(diagnostics.tracemalloc, "is_tracing", lambda: True)
    monkeypatch.setattr(
        diagnostics.tracemalloc, "get_traced_memory", lambda: (100, 200)
    )
    start = Mock(side_effect=AssertionError)
    monkeypatch.setattr(diagnostics.tracemalloc, "start", start)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    row = records(path)[0]
    assert row["python_traced_current_bytes"] == 100
    assert row["python_traced_peak_bytes"] == 200
    start.assert_not_called()


def test_sink_write_error_is_counted_on_recovery(tmp_path, capsys):
    path = tmp_path / "missing" / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    assert diagnostics._wait_for_idle()
    assert diagnostics._failures == 1
    path.parent.mkdir()
    diagnostics.record("heartbeat")
    assert records(path)[0]["telemetry_failures"] == 1
    assert capsys.readouterr().err == ""


def test_constructor_failure_is_nonfatal_and_visible_after_reconfigure(
    monkeypatch, tmp_path
):
    handler = diagnostics._RotatingSink
    monkeypatch.setattr(
        diagnostics, "_RotatingSink", Mock(side_effect=OSError("private details"))
    )
    diagnostics.configure(tmp_path / "metrics.jsonl")
    diagnostics._writer.thread.join(timeout=1)
    diagnostics.record("heartbeat")
    monkeypatch.setattr(diagnostics, "_RotatingSink", handler)
    path = tmp_path / "recovered.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    assert records(path)[0]["telemetry_failures"] == 2


def test_rotation_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostics, "MAX_BYTES", 2048)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    for number in range(50):
        diagnostics.record("heartbeat", sequence=number)
    assert diagnostics._wait_for_idle()
    files = list(tmp_path.iterdir())
    assert len(files) == 3
    assert {file.name for file in files} == {
        "metrics.jsonl",
        "metrics.jsonl.1",
        "metrics.jsonl.2",
    }
    assert all(file.stat().st_size <= 2048 for file in files)
    assert records(path)[-1]["sequence"] == 49


def test_private_and_invalid_fields_are_dropped_and_reserved_metrics_protected(
    tmp_path,
):
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record(
        "heartbeat",
        content="secret user content",
        raw={"text": "private"},
        nonfinite=float("nan"),
        physical_footprint_bytes=999,
    )
    row = records(path)[0]
    assert row["physical_footprint_bytes"] == 1024
    assert row["telemetry_failures"] == 3
    assert not {"content", "raw", "nonfinite"}.intersection(row)
    assert "secret" not in path.read_text()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("abc", {"input_items": 1, "total_chars": 3, "max_chars": 3, "sampled": False}),
        (
            ["abc", "xy"],
            {"input_items": 2, "total_chars": 5, "max_chars": 3, "sampled": False},
        ),
        (
            [("abc", "xy"), ("z", "abcd")],
            {"input_items": 2, "total_chars": 10, "max_chars": 4, "sampled": False},
        ),
    ],
)
def test_summary_contains_only_counts(value, expected):
    assert diagnostics.summarize_inputs(value) == expected


def test_summary_stops_at_scan_budget_and_never_consumes_generators(monkeypatch):
    monkeypatch.setattr(diagnostics, "SCAN_LIMIT", 4)
    row = diagnostics.summarize_inputs(["a"] * 10)
    assert row["sampled"] is True
    assert row["total_chars"] <= 4
    assert row["input_items"] == 10
    iterator = iter(["private"])
    assert diagnostics.summarize_inputs(iterator)["sampled"] is True
    assert next(iterator) == "private"


def test_real_lazy_probe_import_does_not_load_models(monkeypatch, tmp_path):
    monkeypatch.setattr(diagnostics, "_probe", None)
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"torch", "numpy", "sentence_transformers"}
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    assert records(path)[0]["event"] == "heartbeat"
    diagnostics.close()
    diagnostics.record("shutdown")
    assert len(records(path)) == 1


def test_mps_counter_failure_does_not_drop_other_measurements(monkeypatch, tmp_path):
    mps = SimpleNamespace(
        current_allocated_memory=Mock(side_effect=RuntimeError("private")),
        driver_allocated_memory=lambda: 42,
    )
    torch = SimpleNamespace(
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: True)),
        mps=mps,
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("inference_end", sample_mps=True)
    row = records(path)[0]
    assert row["mps_current_bytes"] is None
    assert row["mps_driver_bytes"] == 42
    assert row["mps_current_bytes_error"] == "unavailable"
    assert row["metric_error_count"] == 1
    assert "private" not in path.read_text()


def test_blocked_file_io_never_blocks_producer_and_queue_is_bounded(
    monkeypatch, tmp_path
):
    entered = threading.Event()
    release = threading.Event()
    completed = threading.Event()
    original_emit = diagnostics._RotatingSink.emit

    def blocked_emit(handler, log_record):
        entered.set()
        assert release.wait(timeout=3)
        original_emit(handler, log_record)

    monkeypatch.setattr(diagnostics._RotatingSink, "emit", blocked_emit)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat")
    assert entered.wait(timeout=1)

    def produce():
        for sequence in range(diagnostics.QUEUE_LIMIT * 2):
            diagnostics.record("heartbeat", sequence=sequence)
        completed.set()

    producer = threading.Thread(target=produce, daemon=True)
    try:
        producer.start()
        assert completed.wait(timeout=1), "producer waited for blocked file I/O"
        assert diagnostics._writer.queue.qsize() == diagnostics.QUEUE_LIMIT
        assert diagnostics._failures == diagnostics.QUEUE_LIMIT
    finally:
        release.set()
        producer.join(timeout=1)
    assert diagnostics._wait_for_idle()
    diagnostics.record("heartbeat")
    assert records(path)[-1]["telemetry_failures"] == diagnostics.QUEUE_LIMIT


def test_close_and_reconfigure_never_wait_or_create_second_blocked_writer(
    monkeypatch, tmp_path
):
    entered = threading.Event()
    release = threading.Event()
    completed = threading.Event()
    original_emit = diagnostics._RotatingSink.emit

    def blocked_emit(handler, log_record):
        entered.set()
        assert release.wait(timeout=3)
        original_emit(handler, log_record)

    monkeypatch.setattr(diagnostics._RotatingSink, "emit", blocked_emit)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    first_writer = diagnostics._writer
    diagnostics.configure(path)
    assert diagnostics._writer is first_writer
    diagnostics.record("heartbeat")
    assert entered.wait(timeout=1)

    def close_and_reconfigure():
        diagnostics.close()
        diagnostics.configure(path)
        diagnostics.configure(tmp_path / "other.jsonl")
        completed.set()

    producer = threading.Thread(target=close_and_reconfigure, daemon=True)
    try:
        producer.start()
        assert completed.wait(timeout=1), "close waited for blocked file I/O"
        assert diagnostics._writer is first_writer
        assert not diagnostics.is_enabled()
        assert diagnostics._failures == 2
    finally:
        release.set()
        producer.join(timeout=1)
    first_writer.thread.join(timeout=1)
    assert not first_writer.thread.is_alive()
    diagnostics.configure(path)
    assert diagnostics._writer is not first_writer
    diagnostics.record("heartbeat")
    assert records(path)[-1]["telemetry_failures"] == 2


def test_blocked_writer_does_not_block_normal_interpreter_exit(tmp_path):
    # A subprocess is essential: a daemon alone is insufficient if its sink
    # registers logging.shutdown cleanup in the main interpreter thread.
    script = textwrap.dedent("""
        import os
        import sys
        import threading
        from pathlib import Path
        from ai_governance_mcp import memory_diagnostics as diagnostics

        blocked = threading.Event()
        never_released = threading.Event()
        original_write = os.write

        def stalled_write(fd, data):
            blocked.set()
            never_released.wait(30)
            return original_write(fd, data)

        diagnostics._metrics = lambda _: {}
        diagnostics.os.write = stalled_write
        diagnostics.configure(Path(sys.argv[1]))
        diagnostics.record("heartbeat")
        assert blocked.wait(1)
        diagnostics.close()
        # Exit normally without ever releasing the writer's stalled syscall.
    """)
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path / "metrics.jsonl")],
        env={
            **os.environ,
            "PYTHONPATH": str(Path(diagnostics.__file__).parents[1]),
        },
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert result.returncode == 0, result.stderr


def test_raw_sink_handles_partial_writes_and_private_creation(monkeypatch, tmp_path):
    original_write = diagnostics.os.write

    def short_write(fd, data):
        return original_write(fd, data[:7])

    monkeypatch.setattr(diagnostics.os, "write", short_write)
    path = tmp_path / "metrics.jsonl"
    diagnostics.configure(path)
    diagnostics.record("heartbeat", sequence=1)
    assert records(path)[0]["sequence"] == 1
    assert path.stat().st_mode & 0o777 == 0o600
