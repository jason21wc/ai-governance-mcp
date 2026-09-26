"""Behavioral contract for the Context Engine's root ignore-file layers."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ai_governance_mcp.context_engine.indexer import Indexer


def test_discovery_combines_exclusions_and_explicit_reinclusions(tmp_path):
    """Adding context rules must not expose Git-ignored caches or secrets.

    Covers: FM-CONTEXT-IGNORE-LAYERING
    """
    (tmp_path / ".gitignore").write_text("cache/\ngenerated/\n")
    (tmp_path / ".contextignore").write_text(
        "drafts/\n!generated/keep.py\n!build/reference.py\n"
        "!.env.local\n!credentials.json\n!*.key\n"
    )
    for name in (
        "src/main.py",
        "cache/noise.py",
        "generated/noise.py",
        "generated/keep.py",
        "drafts/notes.md",
        "build/reference.py",
        "build/noise.py",
        ".env.local",
        "credentials.json",
        "server.key",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture content\n")

    indexer = Indexer(storage=Mock())
    spec = indexer.load_ignore_patterns(tmp_path)
    discovered = {
        path.relative_to(tmp_path).as_posix()
        for path in indexer._discover_files(tmp_path, spec)
    }

    assert discovered == {"src/main.py", "generated/keep.py", "build/reference.py"}
    # These assertions cover policy even for paths without an indexing connector.
    assert spec.match_file(".env.local")
    assert spec.match_file("credentials.json")
    assert spec.match_file("server.key")


@pytest.mark.parametrize("source", [None, ".gitignore", ".contextignore"])
def test_missing_layers_preserve_defaults_and_available_user_rules(tmp_path, source):
    """An absent ignore layer must not disable defaults or the remaining file."""
    if source:
        (tmp_path / source).write_text("private-notes/\n")

    spec = Indexer(storage=Mock()).load_ignore_patterns(tmp_path)

    assert spec.match_file("node_modules/package/index.js")
    assert spec.match_file(".env.production")
    assert not spec.match_file("src/main.py")
    assert bool(spec.match_file("private-notes/notes.md")) is (source is not None)


@pytest.mark.parametrize("bad_layer", [".gitignore", ".contextignore"])
@pytest.mark.parametrize("failure", ["oversized", "unreadable", "invalid_utf8"])
def test_failed_layer_keeps_other_exclusions(
    tmp_path, monkeypatch, caplog, bad_layer, failure
):
    """One unusable layer must not erase the other layer's exclusions.

    Covers: FM-CONTEXT-IGNORE-LAYERING
    """
    for name in (".gitignore", ".contextignore"):
        (tmp_path / name).write_text("retained/\n")
    bad_path = tmp_path / bad_layer
    if failure == "oversized":
        bad_path.write_text("#" * 1_048_577)
    elif failure == "invalid_utf8":
        bad_path.write_bytes(b"\xff\xfe")
    else:
        real_read_text = Path.read_text

        def read_text(path, *args, **kwargs):
            if path == bad_path:
                raise PermissionError("fixture denied")
            return real_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)

    spec = Indexer(storage=Mock()).load_ignore_patterns(tmp_path)

    assert spec.match_file("retained/file.py")
    assert spec.match_file("node_modules/package/index.js")
    assert spec.match_file(".env.local")
    assert not spec.match_file("src/main.py")
    assert bad_layer in caplog.text


@pytest.mark.parametrize("source", [".gitignore", ".contextignore"])
def test_ignore_file_at_size_limit_still_applies(tmp_path, source):
    """The size guard must not reject an allowed file exactly at its limit."""
    rule = "retained/\n"
    (tmp_path / source).write_text(rule + "#" * (1_048_576 - len(rule)))

    spec = Indexer(storage=Mock()).load_ignore_patterns(tmp_path)

    assert spec.match_file("retained/file.py")


@pytest.mark.parametrize("source", [".gitignore", ".contextignore"])
def test_malformed_ignore_pattern_is_not_silently_discarded(tmp_path, source):
    """Malformed exclusion policy must still fail instead of indexing broadly."""
    (tmp_path / source).write_text("!\n")

    with pytest.raises(ValueError):
        Indexer(storage=Mock()).load_ignore_patterns(tmp_path)


def test_layer_order_and_gitignore_whitespace_are_preserved(tmp_path):
    """Layering must preserve Git wildcards, root anchors, escapes and negation.

    Covers: FM-CONTEXT-IGNORE-LAYERING
    """
    (tmp_path / ".gitignore").write_text(
        "logs/**\n/root-only.py\n\\#literal.py\n\\!literal.py\n"
        " leading.py\ntrailing.py\\ \n*.tmp\n"
    )
    (tmp_path / ".contextignore").write_text("!logs/keep.py\n!*.lock\nlogs/secret.py\n")

    spec = Indexer(storage=Mock()).load_ignore_patterns(tmp_path)

    assert spec.match_file("logs/subdir/output.py")
    assert not spec.match_file("logs/keep.py")
    assert spec.match_file("logs/secret.py")
    assert not spec.match_file("package.lock")
    assert spec.match_file("root-only.py")
    assert not spec.match_file("nested/root-only.py")
    assert spec.match_file("#literal.py")
    assert spec.match_file("!literal.py")
    assert spec.match_file(" leading.py")
    assert not spec.match_file("leading.py")
    assert spec.match_file("trailing.py ")
    assert not spec.match_file("trailing.py")
    assert spec.match_file("nested/output.tmp")


def test_nested_ignore_files_do_not_change_root_policy(tmp_path):
    """Root-only loading must not accidentally interpret nested ignore files."""
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".gitignore").write_text("*.py\n")
    (nested / ".contextignore").write_text("*.md\n")

    spec = Indexer(storage=Mock()).load_ignore_patterns(tmp_path)

    assert not spec.match_file("nested/main.py")
    assert not spec.match_file("nested/README.md")
