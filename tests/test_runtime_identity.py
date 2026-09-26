"""#337: an editable checkout must not relabel an already-imported MCP server."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from ai_governance_mcp.server import _app, _runtime_identity as identity
from helpers import extract_json_from_response


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.check_output(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-C",
            str(root),
            *args,
        ],
        env=env,
        text=True,
        stderr=subprocess.PIPE,
    ).strip()


@pytest.fixture
def source_checkout(tmp_path):
    root = tmp_path / "checkout"
    package = root / "src" / "ai_governance_mcp"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "test"\n')
    git(root, "init")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initial source")
    return root, package


def test_source_digest_changes_for_dirty_source_without_new_revision(source_checkout):
    root, package = source_checkout
    initial = identity._source_snapshot(package)
    revision = git(root, "rev-parse", "HEAD")
    assert identity._git_snapshot(package)["package_dirty_at_import"] is False
    (package / "new_module.py").write_text("answer = 42\n")
    changed = identity._source_snapshot(package)
    context = identity._git_snapshot(package)
    assert initial["source_sha256_at_import"] != changed["source_sha256_at_import"]
    assert context["revision_at_import"] == revision
    assert context["package_dirty_at_import"] is True
    assert changed["file_count"] == 2


def test_git_is_source_anchored_and_ignores_callers_git_environment(
    source_checkout, tmp_path, monkeypatch
):
    root, package = source_checkout
    expected = git(root, "rev-parse", "HEAD")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    git(unrelated, "init")
    monkeypatch.chdir(unrelated)
    monkeypatch.setenv("GIT_DIR", str(unrelated / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(unrelated))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(unrelated))
    assert identity._git_snapshot(package)["revision_at_import"] == expected


def test_wheel_inside_unrelated_repository_does_not_claim_its_revision(source_checkout):
    root, _ = source_checkout
    wheel = root / ".venv" / "site-packages" / "ai_governance_mcp"
    wheel.mkdir(parents=True)
    (wheel / "__init__.py").write_text('__version__ = "wheel"\n')
    assert identity._source_snapshot(wheel)["status"] == "available"
    assert identity._git_snapshot(wheel) == {
        "status": "unavailable",
        "reason": "not_source_checkout",
    }


def test_untracked_src_layout_is_not_a_package_revision(source_checkout):
    root, _ = source_checkout
    other = root / "src" / "another_package"
    other.mkdir()
    (other / "__init__.py").write_text("")
    assert identity._git_snapshot(other)["status"] == "unavailable"


@pytest.mark.parametrize(
    "failure, reason",
    [
        (FileNotFoundError(), "git_observation_failed"),
        (subprocess.TimeoutExpired("git", 1), "git_timeout"),
        (PermissionError(), "git_observation_failed"),
    ],
)
def test_git_failure_is_explicit_and_does_not_break_source_observation(
    source_checkout, monkeypatch, failure, reason
):
    _, package = source_checkout

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(identity.subprocess, "run", fail)
    assert identity._git_snapshot(package) == {
        "status": "unavailable",
        "reason": reason,
    }
    assert identity._source_snapshot(package)["status"] == "available"


@pytest.mark.parametrize("limit", ["_MAX_BYTES", "_MAX_FILES", "_MAX_ENTRIES"])
def test_source_limits_never_return_partial_digest(source_checkout, monkeypatch, limit):
    _, package = source_checkout
    monkeypatch.setattr(identity, limit, 0)
    result = identity._source_snapshot(package)
    assert result == {"status": "unavailable", "reason": "source_limit_exceeded"}


def test_source_read_failure_never_returns_partial_digest(source_checkout, monkeypatch):
    _, package = source_checkout

    def fail(*args, **kwargs):
        raise PermissionError()

    monkeypatch.setattr(identity.os, "open", fail)
    assert identity._source_snapshot(package) == {
        "status": "unavailable",
        "reason": "source_read_failed",
    }


def test_source_symlinks_are_not_followed(source_checkout, tmp_path):
    _, package = source_checkout
    outside = tmp_path / "outside.py"
    outside.write_text("do_not_read = True\n")
    (package / "link.py").symlink_to(outside)
    assert identity._source_snapshot(package) == {
        "status": "unavailable",
        "reason": "source_not_regular",
    }


@pytest.mark.asyncio
async def test_metrics_reports_snapshot_without_filesystem_or_engine(
    monkeypatch, reset_server_state
):
    expected = identity.get_runtime_identity()

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Metrics must not initialize retrieval or recapture identity"
        )

    monkeypatch.setattr(identity, "_capture_identity", forbidden)
    monkeypatch.setattr(identity, "_source_snapshot", forbidden)
    monkeypatch.setattr(identity, "_git_snapshot", forbidden)
    monkeypatch.setattr(_app, "get_engine", forbidden)
    monkeypatch.setattr(_app, "_check_rate_limit", lambda: True)
    result = await _app.call_tool("get_metrics", {})
    payload = json.loads(extract_json_from_response(result[0].text))
    assert payload["runtime_identity"] == expected
    assert payload["total_queries"] == 0
    assert "_response_trust" in payload
    assert payload["runtime_identity"]["capture_phase"] == "server_package_import"
    copy = identity.get_runtime_identity()
    copy["source"]["status"] = "tampered"
    assert identity.get_runtime_identity() == expected


def test_first_metrics_after_source_commit_keeps_import_identity(tmp_path):
    """Real import + edit + commit before first dispatch; restart must see new bytes."""
    root = tmp_path / "real_checkout"
    package = root / "src" / "ai_governance_mcp"
    shutil.copytree(
        Path(identity.__file__).parents[1],
        package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    git(root, "init")
    git(root, "add", ".")
    git(root, "commit", "-m", "Before process import")
    before_revision = git(root, "rev-parse", "HEAD")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    observe = """
import asyncio, json
from ai_governance_mcp.server import _app
result = asyncio.run(_app.call_tool("get_metrics", {}))
print(result[0].text)
"""
    edit_then_observe = (
        """
from ai_governance_mcp.server import _app
from pathlib import Path
import subprocess
p = Path("src/ai_governance_mcp/__init__.py")
p.write_text(p.read_text() + "\\n# change after this process imported the server\\n")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "user.name=Test",
                "-c", "user.email=test@example.invalid", "commit", "-qm", "After import"], check=True)
"""
        + observe
    )
    old = subprocess.run(
        [sys.executable, "-c", edit_then_observe],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    after_revision = git(root, "rev-parse", "HEAD")
    fresh = subprocess.run(
        [sys.executable, "-c", observe],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    old_id = json.loads(extract_json_from_response(old.stdout))["runtime_identity"]
    new_id = json.loads(extract_json_from_response(fresh.stdout))["runtime_identity"]
    assert old_id["git"]["revision_at_import"] == before_revision
    assert new_id["git"]["revision_at_import"] == after_revision != before_revision
    assert (
        old_id["source"]["source_sha256_at_import"]
        != new_id["source"]["source_sha256_at_import"]
    )
    assert old_id["pid"] != new_id["pid"]
    assert old_id["package_path"] == new_id["package_path"] == str(package)
