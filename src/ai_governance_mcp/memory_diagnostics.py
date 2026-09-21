"""Bounded, best-effort watcher measurements; never records model inputs.

Importing this module neither loads a model nor opens a file. Callers supply
only numeric values and fixed labels, never paths, exceptions, or user text.
Physical footprint includes native allocations; Python block counts and already
active tracemalloc measurements describe different, overlapping quantities.
"""

import json
import math
import os
from pathlib import Path
import re
import queue
import sys
import threading
import time
import tracemalloc
from datetime import datetime, timezone

MAX_BYTES = 1024 * 1024
BACKUP_COUNT = 2
SCAN_LIMIT = 10_000
QUEUE_LIMIT = 128
_LABEL = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]{0,63}\Z")
_lock = threading.RLock()
_writer = None
_enabled = False
_failures = 0
_probe = None


class _RotatingSink:
    """Writer-owned raw file descriptor, with no interpreter shutdown hooks.

    Buffered/logging file handlers register cleanup that can block normal exit
    behind a stalled daemon thread. Raw descriptors avoid that coupling; the OS
    closes any remaining descriptor when the worker process exits.
    """

    def __init__(self, path, max_bytes, backup_count):
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.fd = None

    def _open(self):
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)

    def emit(self, message):
        data = (message + "\n").encode("utf-8")
        if self.fd is None:
            self._open()
        size = os.fstat(self.fd).st_size
        if size and size + len(data) > self.max_bytes:
            self.close()
            for number in range(self.backup_count, 0, -1):
                source = self.path if number == 1 else Path(f"{self.path}.{number - 1}")
                destination = Path(f"{self.path}.{number}")
                try:
                    os.replace(source, destination)
                except FileNotFoundError:
                    pass
            self._open()
        remaining = memoryview(data)
        while remaining:
            written = os.write(self.fd, remaining)
            if written <= 0:
                raise OSError("diagnostic write made no progress")
            remaining = remaining[written:]

    def handle(self, message):
        try:
            self.emit(message)
        except Exception:
            _count_failure()

    def close(self):
        if self.fd is not None:
            descriptor, self.fd = self.fd, None
            os.close(descriptor)


class _Writer:
    """One daemon owns all file I/O; a stalled disk cannot stall producers."""

    def __init__(self, path):
        self.path = path
        self.accepting = True
        self.queue = queue.Queue(maxsize=QUEUE_LIMIT)
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=self.run, name="memory-diagnostics", daemon=True
        )

    def run(self):
        handler = None
        try:
            handler = _RotatingSink(self.path, MAX_BYTES, BACKUP_COUNT)
            while True:
                try:
                    message = self.queue.get(timeout=0.05)
                except queue.Empty:
                    if self.stop.is_set():
                        break
                    continue
                try:
                    handler.handle(message)
                except Exception:
                    _count_failure()
                finally:
                    self.queue.task_done()
        except Exception:
            _count_failure()
        finally:
            with _lock:
                self.accepting = False
            # Constructor errors must not strand queue bookkeeping or records.
            while True:
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
                else:
                    _count_failure()
                    self.queue.task_done()
            if handler is not None:
                try:
                    handler.close()
                except Exception:
                    _count_failure()


def _count_failure():
    global _failures
    with _lock:
        _failures += 1


def configure(path: Path) -> None:
    """Enable bounded JSONL recording; never create a second live writer.

    Repeating the active path is idempotent. A different configuration while a
    writer is alive (including stalled/closing) is refused and counted. Retry
    only after that writer exits; close itself never waits for filesystem I/O.
    """
    global _writer, _enabled
    with _lock:
        try:
            path = Path(path)
            if _writer is not None and _writer.thread.is_alive():
                if _enabled and path == _writer.path:
                    return
                _count_failure()
                return
            _writer = _Writer(path)
            _enabled = True
            _writer.thread.start()
        except Exception:
            _enabled = False
            _count_failure()


def is_enabled() -> bool:
    """Whether diagnostic recording was explicitly configured."""
    return _enabled


def close() -> None:
    """Disable enqueueing and request drain/close without joining the writer."""
    global _enabled
    with _lock:
        _enabled = False
        if _writer is not None:
            _writer.stop.set()


def _wait_for_idle(timeout=1.0):
    """Bounded test/inspection aid, never called by inference or heartbeat."""
    writer = _writer
    if writer is None:
        return True
    with writer.queue.all_tasks_done:
        return writer.queue.all_tasks_done.wait_for(
            lambda: writer.queue.unfinished_tasks == 0,
            timeout=timeout,
        )


def _get_probe():
    global _probe
    if _probe is None:
        # POSIX-only supervisor imports fcntl. Unsupported hosts remain usable
        # with an explicitly unavailable metric instead of failing startup.
        from .context_engine.watcher_supervisor import MemoryProbe

        _probe = MemoryProbe()
    return _probe


def _metrics(sample_mps):
    values = {
        "physical_footprint_bytes": None,
        "footprint_kind": "darwin_physical"
        if sys.platform == "darwin"
        else "rss_plus_swap",
        "python_allocated_blocks": None,
        "python_traced_current_bytes": None,
        "python_traced_peak_bytes": None,
        "mps_current_bytes": None,
        "mps_driver_bytes": None,
        "metric_error_count": 0,
    }

    def failure(label):
        values[label] = "unavailable"
        values["metric_error_count"] += 1

    try:
        values["physical_footprint_bytes"] = _get_probe().footprint(os.getpid())
    except Exception:
        failure("footprint_error")
    try:
        values["python_allocated_blocks"] = sys.getallocatedblocks()
    except Exception:
        failure("python_blocks_error")
    try:
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            values["python_traced_current_bytes"] = current
            values["python_traced_peak_bytes"] = peak
    except Exception:
        failure("python_traced_error")
    if sample_mps:
        torch = sys.modules.get("torch")
        try:
            available = torch is not None and torch.backends.mps.is_available()
        except Exception:
            available = False
            failure("mps_availability_error")
        if available:
            for field, method in (
                ("mps_current_bytes", "current_allocated_memory"),
                ("mps_driver_bytes", "driver_allocated_memory"),
            ):
                try:
                    values[field] = getattr(torch.mps, method)()
                except Exception:
                    failure(field + "_error")
    return values


def record(event: str, **fields) -> None:
    """Enqueue one measurement without waiting on file I/O. Queue overflow drops
    the newest record and increments the cumulative failure count.

    ``sample_mps=True`` asks for already-loaded torch's allocation counters. It
    does not synchronize MPS, empty its cache, start tracing, or import torch.
    ``telemetry_failures`` is a cumulative count, including failed writes and dropped records.
    Invalid fields are omitted and counted; labels are bounded, not free text.
    """
    global _failures
    with _lock:
        if not _enabled:
            return
        try:
            if not isinstance(event, str) or not _LABEL.fullmatch(event):
                _failures += 1
                return
            sample_mps = fields.pop("sample_mps", False) is True
            payload = {}
            for key, value in list(fields.items())[:32]:
                valid_key = isinstance(key, str) and _LABEL.fullmatch(key)
                valid_value = (
                    value is None
                    or isinstance(value, bool)
                    or (isinstance(value, (int, float)) and math.isfinite(value))
                    or (isinstance(value, str) and _LABEL.fullmatch(value))
                )
                if valid_key and valid_value:
                    payload[key] = value
                else:
                    _failures += 1
            if len(fields) > 32:
                _failures += 1
            # Reserved measurements cannot be overwritten by caller fields.
            payload.update(_metrics(sample_mps))
            payload.update(
                timestamp=datetime.now(timezone.utc).isoformat(),
                monotonic_seconds=time.monotonic(),
                pid=os.getpid(),
                event=event,
                telemetry_failures=_failures,
            )
            if (
                _writer is None
                or not _writer.accepting
                or not _writer.thread.is_alive()
            ):
                _failures += 1
                return
            message = json.dumps(payload, allow_nan=False, separators=(",", ":"))
            try:
                _writer.queue.put_nowait(message)
            except queue.Full:
                _failures += 1
        except Exception:
            _failures += 1


def summarize_inputs(value):
    """Count string lengths without copying/retaining text or consuming iterators.

    For prediction pairs, inspect two container levels. ``input_items`` is the
    outer batch length; character counts cover at most SCAN_LIMIT visited values.
    ``sampled`` marks truncated or unsupported shapes, so partial counts cannot
    be mistaken for the complete workload. No object stringification occurs.
    """
    result = {"input_items": 0, "total_chars": 0, "max_chars": 0, "sampled": False}
    if isinstance(value, str):
        result.update(input_items=1, total_chars=len(value), max_chars=len(value))
        return result
    if not isinstance(value, (list, tuple)):
        result["sampled"] = True
        return result
    result["input_items"] = len(value)
    remaining = SCAN_LIMIT
    for item in value:
        if remaining <= 0:
            result["sampled"] = True
            break
        remaining -= 1
        parts = item if isinstance(item, (list, tuple)) else (item,)
        for part in parts:
            if remaining <= 0:
                result["sampled"] = True
                break
            remaining -= 1
            if isinstance(part, str):
                size = len(part)
                result["total_chars"] += size
                result["max_chars"] = max(result["max_chars"], size)
            else:
                result["sampled"] = True
    return result
