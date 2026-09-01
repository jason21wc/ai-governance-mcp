"""`_load_local_embedder` — interpreter legibility and offline resilience.

WHY THIS EXISTS. The canonical rebuild is documented in AGENTS.md as
`python -m ai_governance_mcp.extractor`. On this machine `python` resolves to
`/opt/anaconda3/bin/python3`, which happens to carry sentence-transformers, while
the project's own `.venv/bin/python` does **not** — measured, both. So the
documented command works by accident of PATH ordering, and when it fails it fails
with a bare `ModuleNotFoundError` naming neither the interpreter that ran nor the
remedy. A sibling session lost real time to exactly that, plus a Hugging Face
metadata 403 on a build whose model weights were already fully cached.

Same shape as the reason `content_patterns.py` exists: a missing
scientific-computing dependency quietly disabling something important. The fix in
both places is to make the failure name itself.

These tests assert the two failure paths, because the success path was already
working and is not what broke.
"""

from __future__ import annotations

import builtins
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from ai_governance_mcp.extractor import _load_local_embedder  # noqa: E402

MODEL = "BAAI/bge-small-en-v1.5"


# --------------------------------------------------------------------------
# Path 1 — the dependency is missing from THIS interpreter
# --------------------------------------------------------------------------


def test_missing_dependency_names_the_interpreter(monkeypatch):
    """A bare ModuleNotFoundError does not say which python ran. This must."""
    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "sentence_transformers":
            raise ModuleNotFoundError("No module named 'sentence_transformers'")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ModuleNotFoundError) as exc:
        _load_local_embedder(MODEL)

    msg = str(exc.value)
    assert sys.executable in msg, (
        "the error must name the interpreter that actually ran — that is the "
        "whole diagnostic, because the failure is a PATH-resolution problem"
    )
    assert "pip install" in msg, "the error must state the remedy, not just the fault"
    assert "sentence-transformers" in msg


def test_missing_dependency_preserves_the_original_cause(monkeypatch):
    """Chain the original error; a rewritten exception that loses __cause__
    makes the real traceback unrecoverable."""
    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "sentence_transformers":
            raise ModuleNotFoundError("No module named 'sentence_transformers'")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ModuleNotFoundError) as exc:
        _load_local_embedder(MODEL)
    assert exc.value.__cause__ is not None


# --------------------------------------------------------------------------
# Path 2 — the network fails but the model is cached
# --------------------------------------------------------------------------


def test_network_failure_retries_against_the_local_cache():
    """A metadata lookup must not fail a build that needs nothing from the network.

    sentence-transformers contacts Hugging Face for repo metadata even when every
    weight is cached, so a transient 403 or timeout can fail an otherwise-offline
    rebuild. First attempt fails, second must be local_files_only=True.
    """
    sentinel = Mock(name="cached-model")
    calls = []

    def fake_st(name, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise OSError(
                "403 Client Error: Forbidden for url: https://huggingface.co/..."
            )
        return sentinel

    with patch("sentence_transformers.SentenceTransformer", side_effect=fake_st):
        got = _load_local_embedder(MODEL)

    assert got is sentinel
    assert len(calls) == 2, "a cached model must be retried, not surfaced as failure"
    assert calls[0].get("local_files_only") is not True, (
        "the FIRST attempt must allow download — forcing local-only by default "
        "would break a first-time user who genuinely has no cached model"
    )
    assert calls[1].get("local_files_only") is True, (
        "the retry must be local-cache-only; that is what removes the "
        "unnecessary network dependency"
    )


def test_retry_still_raises_when_the_model_is_genuinely_absent():
    """The retry is resilience, not suppression. No cache => still an error."""

    def fake_st(name, **kwargs):
        raise OSError("model not found locally")

    with patch("sentence_transformers.SentenceTransformer", side_effect=fake_st):
        with pytest.raises(OSError):
            _load_local_embedder(MODEL)


def test_success_path_is_unchanged():
    """The working path must keep its existing contract."""
    sentinel = Mock(name="model")
    with patch(
        "sentence_transformers.SentenceTransformer", return_value=sentinel
    ) as mock_st:
        got = _load_local_embedder(MODEL)
    assert got is sentinel
    mock_st.assert_called_once()
    kwargs = mock_st.call_args.kwargs
    assert kwargs["trust_remote_code"] is False, "must not execute remote code"
    assert kwargs["model_kwargs"] == {"use_safetensors": True}
    assert "local_files_only" not in kwargs


# --------------------------------------------------------------------------
# The documented command and the environment it actually needs
# --------------------------------------------------------------------------


def test_agents_md_documents_the_interpreter_requirement():
    """AGENTS.md gives the rebuild command; it must not imply any `python` works.

    This is the assertion that would have caught the gap: the command was
    documented bare, so a reader with the project venv active gets a failure the
    docs never mentioned.
    """
    text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "python -m ai_governance_mcp.extractor" in text
    assert "sentence-transformers" in text, (
        "AGENTS.md documents the rebuild command but never states that it needs "
        "an interpreter carrying sentence-transformers"
    )
