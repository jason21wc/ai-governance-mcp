"""Hermetic tests for live-remote worktree preflight checks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "global-skills"
    / "start-worktree"
    / "preflight.sh"
)
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_TERMINAL_PROMPT": "0",
}


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(GIT_ENV)
    result = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _run(repo: Path, branch: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(GIT_ENV)
    return subprocess.run(  # nosec B603 B607
        ["bash", str(SCRIPT), branch],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "-q", "--bare", "-b", "main")
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    (root / "README.md").write_text("base\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "-u", "origin", "main")
    _git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return root


def test_clean_preflight_compares_cached_default_to_live_sha(repo: Path):
    out = _run(repo, "wt/new")
    assert out.returncode == 0, out.stdout
    assert "match the LIVE origin SHA" in out.stdout


def test_remote_only_branch_collision_blocks(repo: Path):
    _git(repo, "push", "-q", "origin", "main:refs/heads/wt/taken")
    out = _run(repo, "wt/taken")
    assert out.returncode == 1, out.stdout
    assert "remote branch 'origin/wt/taken' already exists" in out.stdout


def test_remote_branch_with_same_prefix_does_not_collide(repo: Path):
    _git(repo, "push", "-q", "origin", "main:refs/heads/wt/newer")
    out = _run(repo, "wt/new")
    assert out.returncode == 0, out.stdout


def test_live_remote_advance_makes_stale_tracking_ref_undetermined(
    repo: Path, tmp_path: Path
):
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(repo.parent / "origin.git"), str(other))
    (other / "remote.txt").write_text("advanced elsewhere\n")
    _git(other, "add", "-A")
    _git(other, "commit", "-q", "-m", "advance remote")
    _git(other, "push", "-q", "origin", "main")

    out = _run(repo, "wt/new")
    assert out.returncode == 2, out.stdout
    assert "is stale" in out.stdout
    assert "fetch before creating" in out.stdout
