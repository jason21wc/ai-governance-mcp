"""Hermetic tests for optimistic concurrent worktree closeout."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "global-skills"
    / "completion-sequence"
    / "integrate.sh"
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


def _run(
    repo: Path, mode: str, *, env_overrides: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(GIT_ENV)
    env.update(env_overrides or {})
    return subprocess.run(  # nosec B603 B607
        ["bash", str(SCRIPT), mode, "--default-ref", "main"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )


@pytest.fixture
def fleet(tmp_path: Path) -> tuple[Path, Path, Path]:
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "-q", "--bare", "-b", "main")
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    (primary / "base.txt").write_text("base\n")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-q", "-m", "init")
    _git(primary, "remote", "add", "origin", str(origin))
    _git(primary, "push", "-q", "-u", "origin", "main")
    topic = tmp_path / "topic"
    _git(primary, "worktree", "add", "-q", "-b", "wt/topic", str(topic), "main")
    (topic / "topic.txt").write_text("topic\n")
    _git(topic, "add", "-A")
    _git(topic, "commit", "-q", "-m", "topic")
    _git(topic, "push", "-q", "-u", "origin", "wt/topic")
    sibling = tmp_path / "sibling"
    _git(tmp_path, "clone", "-q", str(origin), str(sibling))
    return primary, topic, sibling


def _advance_main(repo: Path, filename: str = "sibling.txt") -> str:
    (repo / filename).write_text("advanced\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"advance {filename}")
    _git(repo, "push", "-q", "origin", "main")
    return _git(repo, "rev-parse", "HEAD")


def test_refresh_integrates_live_origin_default(fleet):
    _, topic, sibling = fleet
    main_sha = _advance_main(sibling)
    out = _run(topic, "refresh")
    assert out.returncode == 0, out.stdout + out.stderr
    assert _git(topic, "merge-base", "--is-ancestor", main_sha, "HEAD") == ""


def test_publish_fast_forwards_default(fleet):
    _, topic, _ = fleet
    out = _run(topic, "publish")
    assert out.returncode == 0, out.stdout + out.stderr
    live = _git(topic, "ls-remote", "origin", "refs/heads/main").split()[0]
    assert live == _git(topic, "rev-parse", "HEAD")


def test_dirty_topic_refuses_before_fetch_or_merge(fleet):
    _, topic, _ = fleet
    (topic / "dirty.txt").write_text("dirty\n")
    out = _run(topic, "refresh")
    assert out.returncode == 1
    assert "not clean" in out.stdout


def test_publish_returns_retry_when_sibling_wins_race(fleet, tmp_path):
    _, topic, sibling = fleet
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    real_git = shutil.which("git")
    assert real_git
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1 $2 $3" = "push origin HEAD:refs/heads/main" ]; then\n'
        '  printf "race\\n" > "$RACE_REPO/race.txt"\n'
        '  "$REAL_GIT" -C "$RACE_REPO" add -A\n'
        '  "$REAL_GIT" -C "$RACE_REPO" commit -q -m "win race"\n'
        '  "$REAL_GIT" -C "$RACE_REPO" push -q origin main\n'
        "fi\n"
        'exec "$REAL_GIT" "$@"\n'
    )
    wrapper.chmod(0o755)
    out = _run(
        topic,
        "publish",
        env_overrides={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "REAL_GIT": real_git,
            "RACE_REPO": str(sibling),
        },
    )
    assert out.returncode == 3, out.stdout + out.stderr
    assert "RETRY" in out.stdout
    assert "advanced during publish" in out.stdout


def test_publish_accepts_sibling_fast_forward_after_success(fleet, tmp_path):
    _, topic, sibling = fleet
    bin_dir = tmp_path / "fake-bin-after-success"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    real_git = shutil.which("git")
    assert real_git
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1 $2 $3" = "push origin HEAD:refs/heads/main" ]; then\n'
        '  "$REAL_GIT" "$@" || exit $?\n'
        '  "$REAL_GIT" -C "$RACE_REPO" pull -q --ff-only origin main\n'
        '  printf "later\n" > "$RACE_REPO/later.txt"\n'
        '  "$REAL_GIT" -C "$RACE_REPO" add -A\n'
        '  "$REAL_GIT" -C "$RACE_REPO" commit -q -m "advance after success"\n'
        '  "$REAL_GIT" -C "$RACE_REPO" push -q origin main\n'
        "  exit 0\n"
        "fi\n"
        'exec "$REAL_GIT" "$@"\n'
    )
    wrapper.chmod(0o755)
    out = _run(
        topic,
        "publish",
        env_overrides={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "REAL_GIT": real_git,
            "RACE_REPO": str(sibling),
        },
    )
    assert out.returncode == 0, out.stdout + out.stderr
    assert "subsequently advanced" in out.stdout
    live = _git(topic, "ls-remote", "origin", "refs/heads/main").split()[0]
    assert live == _git(sibling, "rev-parse", "HEAD")
    assert (
        _git(
            topic, "merge-base", "--is-ancestor", _git(topic, "rev-parse", "HEAD"), live
        )
        == ""
    )
