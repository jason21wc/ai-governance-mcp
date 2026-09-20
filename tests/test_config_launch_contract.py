"""Contracts for the release launch gate's dependency and readiness evidence."""

import logging
import os
from pathlib import Path

import pytest
import conftest
import test_config_launch_integration as launch
from ai_governance_mcp.retrieval import INDEX_READINESS_FORMAT


@pytest.mark.parametrize("rows,canaries", [(356, 3), (1, 1)])
def test_emitted_format_round_trips_through_parser(caplog, rows, canaries):
    with caplog.at_level(logging.INFO):
        logging.getLogger("ai_governance_mcp").info(
            INDEX_READINESS_FORMAT, rows, canaries
        )
    launch._assert_semantic_ready(caplog.records[-1].getMessage())


@pytest.mark.parametrize(
    "message",
    [
        "",
        "Loaded content embeddings: (356, 384)",
        INDEX_READINESS_FORMAT % (0, 3),
        INDEX_READINESS_FORMAT % (356, 0),
        INDEX_READINESS_FORMAT % (-1, 3),
        (INDEX_READINESS_FORMAT % (356, 3)) + "junk",
        (INDEX_READINESS_FORMAT % (356, 3)).replace("356", "3.56"),
        "\n".join([INDEX_READINESS_FORMAT % (356, 3), INDEX_READINESS_FORMAT % (0, 3)]),
    ],
)
def test_missing_or_degraded_observation_cannot_pass(message):
    with pytest.raises(AssertionError, match="No positive post-validation"):
        launch._assert_semantic_ready(message)


def test_parser_accepts_real_logging_prefix():
    launch._assert_semantic_ready(
        "2026-09-07 15:00:00,000 - ai_governance_mcp - INFO - "
        + INDEX_READINESS_FORMAT % (356, 3)
    )


@pytest.mark.parametrize(
    "outcome,rc,label",
    [
        ("timeout", -9, "[server did not respond within 300s — killed]"),
        (
            "exited",
            1,
            "[server exited rc=1 without answering id=2 — it did NOT time out",
        ),
    ],
)
def test_outcome_label_survives_long_stderr(monkeypatch, tmp_path, outcome, rc, label):
    monkeypatch.setattr(
        launch, "call_and_collect", lambda *a, **kw: ("", "x" * 10000, outcome, rc)
    )
    out, err = launch._run({"command": "python", "args": [], "env": {}}, tmp_path)
    assert label in err[-2000:]
    with pytest.raises(AssertionError) as raised:
        launch._assert_content(out, err)
    assert label in str(raised.value)


def test_child_cache_overrides_do_not_mutate_parent(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_HUB_CACHE", "/parent/cache")
    monkeypatch.setenv("PYTHONPATH", "src")
    seen = {}

    def collect(*args, **kwargs):
        seen.update(kwargs)
        return "response", "stderr", "answered", 0

    monkeypatch.setattr(launch, "call_and_collect", collect)
    cache = tmp_path / "isolated"
    launch._run({"command": "python", "args": [], "env": {}}, tmp_path, cache)
    for key in (
        "HF_HUB_CACHE",
        "HUGGINGFACE_HUB_CACHE",
        "SENTENCE_TRANSFORMERS_HOME",
        "TRANSFORMERS_CACHE",
    ):
        assert seen["env"][key] == str(cache)
    assert seen["env"]["HF_HUB_OFFLINE"] == "1"
    assert seen["env"]["TRANSFORMERS_OFFLINE"] == "1"
    assert seen["env"]["HOME"] == os.environ["HOME"]
    assert os.environ["HF_HUB_CACHE"] == "/parent/cache"
    assert seen["env"]["PYTHONPATH"] == str(
        Path(launch.__file__).resolve().parents[1] / "src"
    )
    assert seen["timeout_s"] == 300


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ({}, "/original/.cache/huggingface/hub"),
        ({"XDG_CACHE_HOME": "/xdg"}, "/xdg/huggingface/hub"),
        ({"HF_HOME": "/hf", "XDG_CACHE_HOME": "/xdg"}, "/hf/hub"),
        ({"HUGGINGFACE_HUB_CACHE": "/legacy", "HF_HOME": "/hf"}, "/legacy"),
        ({"HF_HUB_CACHE": "/hub", "HUGGINGFACE_HUB_CACHE": "/legacy"}, "/hub"),
        ({"SENTENCE_TRANSFORMERS_HOME": "/st", "HF_HUB_CACHE": "/hub"}, "/st"),
    ],
)
def test_source_cache_precedence(overrides, expected):
    assert conftest._resolve_launch_cache({"HOME": "/original", **overrides}) == Path(
        expected
    )


def _fake_source(tmp_path):
    source = tmp_path / "source"
    model = source / "models--BAAI--bge-small-en-v1.5"
    snapshot = model / "snapshots" / "abc123"
    snapshot.mkdir(parents=True)
    (model / "refs").mkdir()
    (model / "refs" / "main").write_text("abc123")
    (model / "blobs").mkdir()
    (model / "blobs" / "weights").write_bytes(b"original weights")
    (snapshot / "model.safetensors").symlink_to("../../blobs/weights")
    for name in ("modules.json", "config.json"):
        (snapshot / name).write_text("{}")
    return source, snapshot


def test_seed_copies_only_model_artifacts_and_dereferences_links(tmp_path):
    source, snapshot = _fake_source(tmp_path)
    (source / "unrelated-account-data").write_text("do not copy")
    destination = tmp_path / "disposable"
    conftest._seed_launch_cache(source, destination, "BAAI/bge-small-en-v1.5")
    copied = destination / snapshot.relative_to(source) / "model.safetensors"
    assert not copied.is_symlink()
    assert copied.read_bytes() == b"original weights"
    copied.write_bytes(b"test mutation")
    assert (snapshot / "model.safetensors").read_bytes() == b"original weights"
    assert not (destination / "unrelated-account-data").exists()


@pytest.mark.parametrize(
    "defect",
    ["missing", "incomplete", "escaping_link", "escaping_ref", "directory_link"],
)
def test_invalid_cache_fails_with_prerequisite_not_skip(tmp_path, defect):
    source, snapshot = _fake_source(tmp_path)
    if defect == "missing":
        source = tmp_path / "absent"
    elif defect == "incomplete":
        (snapshot / "modules.json").unlink()
    elif defect == "directory_link":
        nested = snapshot.parent.parent / "nested"
        nested.mkdir()
        outside = tmp_path / "outside"
        outside.write_text("must not copy")
        (nested / "escape").symlink_to(outside)
        (snapshot / "nested").symlink_to(nested, target_is_directory=True)
    else:
        outside = tmp_path / "outside"
        outside.write_text("abc123")
        target = (
            snapshot / "config.json"
            if defect == "escaping_link"
            else snapshot.parent.parent / "refs" / "main"
        )
        target.unlink()
        target.symlink_to(outside)
    with pytest.raises(
        RuntimeError, match="Launch-test model prerequisite unavailable"
    ):
        conftest._seed_launch_cache(
            source, tmp_path / "disposable", "BAAI/bge-small-en-v1.5"
        )


@pytest.mark.parametrize(
    "alias",
    [
        "TRANSFORMERS_CACHE",
        "PYTORCH_TRANSFORMERS_CACHE",
        "PYTORCH_PRETRAINED_BERT_CACHE",
    ],
)
def test_split_legacy_cache_requires_explicit_unified_provisioning(alias):
    with pytest.raises(RuntimeError, match="Set SENTENCE_TRANSFORMERS_HOME"):
        conftest._validate_launch_cache_policy({alias: "/split"}, Path("/hub"))
    conftest._validate_launch_cache_policy({alias: "/hub"}, Path("/hub"))
    conftest._validate_launch_cache_policy(
        {alias: "/split", "SENTENCE_TRANSFORMERS_HOME": "/unified"}, Path("/unified")
    )
