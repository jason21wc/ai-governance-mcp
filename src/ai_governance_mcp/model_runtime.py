"""Lightweight policy and serialization shared by local model owners."""

import os
import threading
import time
from functools import wraps

from . import memory_diagnostics as diagnostics

INFERENCE_LOCK = threading.RLock()
_ACTIVITY_LOCK = threading.Lock()
_activity = {"active_inference": 0, "active_indexing": 0}
_sequence = 0
_index_scope = threading.local()


def activity_snapshot() -> dict:
    with _ACTIVITY_LOCK:
        return dict(_activity)


def _activity_change(key, delta):
    global _sequence
    with _ACTIVITY_LOCK:
        _activity[key] += delta
        if delta > 0:
            _sequence += 1
        return _sequence


def observe_indexing(method):
    """Observe indexing lifetime without retaining its inputs or results."""

    @wraps(method)
    def observed(*args, **kwargs):
        if not diagnostics.is_enabled() or getattr(_index_scope, "active", False):
            return method(*args, **kwargs)
        _index_scope.active = True
        call_id = _activity_change("active_indexing", 1)
        started = time.monotonic()
        diagnostics.record("index_start", operation=method.__name__, call_id=call_id)
        outcome = "error"
        chunks = None
        try:
            result = method(*args, **kwargs)
            try:
                chunks = len(result.chunks)
            except Exception:
                chunks = None  # preserve successful indexing if metadata fails
            outcome = "ok"
            return result
        finally:
            _index_scope.active = False
            _activity_change("active_indexing", -1)
            diagnostics.record(
                "index_end",
                operation=method.__name__,
                call_id=call_id,
                outcome=outcome,
                total_chunks=chunks,
                elapsed_seconds=time.monotonic() - started,
            )

    return observed


class ModelServiceUnavailable(RuntimeError):
    """Shared models are unavailable; implicit per-client loading is forbidden."""


def require_local_opt_in() -> None:
    if os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip().lower() != "none":
        raise ModelServiceUnavailable(
            "Shared embedding service unavailable; local model fallback disabled. "
            "Start the supervised context-engine-watcher. Explicit standalone use "
            "may set AI_CONTEXT_ENGINE_EMBED_SOCKET=none."
        )


class SerializedModel:
    """Serialize inference even through direct ProjectManager/indexer callers."""

    def __init__(self, model):
        self._model = model

    def encode(self, *args, **kwargs):
        with INFERENCE_LOCK:
            return self._invoke("encode", args, kwargs)

    def predict(self, *args, **kwargs):
        with INFERENCE_LOCK:
            return self._invoke("predict", args, kwargs)

    def _invoke(self, operation, args, kwargs):
        if not diagnostics.is_enabled():
            return getattr(self._model, operation)(*args, **kwargs)
        # Only fixed backend labels and numeric input sizes leave this boundary.
        try:
            device = getattr(self._model.device, "type", None)
        except Exception:
            device = None
        if device not in ("mps", "cpu", "cuda"):
            device = "unknown"
        inputs = args[0] if args else kwargs.get("sentences", kwargs.get("inputs", []))
        sizes = diagnostics.summarize_inputs(inputs)
        call_id = _activity_change("active_inference", 1)
        started = time.monotonic()
        diagnostics.record(
            "inference_start",
            operation=operation,
            call_id=call_id,
            device=device,
            sample_mps=device == "mps",
            **sizes,
        )
        outcome, output_bytes = "error", None
        try:
            result = getattr(self._model, operation)(*args, **kwargs)
            try:
                output_bytes = getattr(result, "nbytes", None)
            except Exception:
                output_bytes = None  # preserve successful inference if metadata fails
            outcome = "ok"
            return result
        finally:
            _activity_change("active_inference", -1)
            diagnostics.record(
                "inference_end",
                operation=operation,
                call_id=call_id,
                device=device,
                sample_mps=device == "mps",
                outcome=outcome,
                output_bytes=output_bytes,
                elapsed_seconds=time.monotonic() - started,
            )

    def __getattr__(self, name):
        return getattr(self._model, name)
