"""`.claude/hooks/pre-commit-memory-size-guard.sh` — one arm blocks, two only report.

WHY THIS FILE EXISTS. The hook shipped with no test at all, and on 2026-08-13 its
BACKLOG check blocked a commit at 61 items against a limit of 60. The cheapest way to
clear a blocking COUNT is to merge entries that should have stayed separate, which is
what happened and had to be reverted the same day. The count was changed to advisory;
this file pins the asymmetry so a later edit cannot quietly restore the block.

SESSION-STATE joined the advisory arm on 2026-08-15 (user decision, BACKLOG #343 q3),
and the two tests that had pinned it as blocking were rewritten rather than repaired —
the contract changed on purpose, so the assertion was the thing that was now wrong. The
argument the old docstring made here ("fixed by condensing prose, which loses nothing")
was the part that did not survive: pruning SESSION-STATE means deciding what is stale
versus still live, and the cheapest way to satisfy a block on it is to delete something
a future session needed. Blocking bought a faster deletion, not a smaller file.

What remains blocking is LEARNING-LOG's active section, on the narrower ground that it
has a defined non-destructive outlet — graduate an entry to the Graduated Patterns
table, which stays in the file — so the cheap fix and the correct fix coincide. #343
owns whether even that should be demoted.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "pre-commit-memory-size-guard.sh"

# Mirrors the hook. Kept as literals rather than parsed out of the shell: a test that
# re-derives the threshold from the file under test would pass no matter what the
# threshold became.
BACKLOG_LIMIT = 60
SESSION_STATE_LIMIT = 300
LEARNING_LOG_LIMIT = 500


def _context(
    tmp_path: Path,
    *,
    backlog_items: int,
    session_state_lines: int,
    learning_log_active_lines: int = 3,
) -> Path:
    ctx = tmp_path / "_ai-context"
    ctx.mkdir(parents=True, exist_ok=True)
    (ctx / "BACKLOG.md").write_text(
        "# Backlog\n\n"
        + "".join(
            f"#### {i}. item {i} `D2 Fix`\n\nbody\n\n" for i in range(backlog_items)
        ),
        encoding="utf-8",
    )
    (ctx / "SESSION-STATE.md").write_text(
        "\n".join(f"line {i}" for i in range(session_state_lines)) + "\n",
        encoding="utf-8",
    )
    # The hook counts the ACTIVE section only — everything above `## Graduated`.
    (ctx / "LEARNING-LOG.md").write_text(
        "\n".join(f"lesson {i}" for i in range(learning_log_active_lines))
        + "\n## Graduated\n",
        encoding="utf-8",
    )
    # Return the PROJECT ROOT, which is what `_run` consumes — the hook appends
    # `_ai-context/` itself. Returning `ctx` forced every call site to remember
    # `.parent`, and a forgotten one points the hook at an empty path where the
    # three `out is None` assertions below still pass.
    return ctx.parent


def _run(
    tmp_path: Path, command: str = "git commit -m x", env_extra: dict | None = None
):
    payload = json.dumps({"cwd": str(tmp_path), "tool_input": {"command": command}})
    import os

    env = os.environ.copy()
    env.pop("MEMORY_SIZE_SKIP", None)
    env.update(env_extra or {})
    result = subprocess.run(
        ["bash", str(HOOK)], input=payload, capture_output=True, text=True, env=env
    )
    assert result.returncode == 0, f"hook must always exit 0; stderr={result.stderr}"
    out = result.stdout.strip()
    return json.loads(out) if out else None


def _run_direct(tmp_path: Path, env_extra: dict | None = None):
    """`--direct`: no stdin, no command detection, plain text, exit code carries it.

    This is the host-agnostic seam. The JSON path exists only for Claude Code's
    PreToolUse protocol; pre-commit is the seam every host honours.
    """
    import os

    env = os.environ.copy()
    env.pop("MEMORY_SIZE_SKIP", None)
    env.update(env_extra or {})
    return subprocess.run(
        ["bash", str(HOOK), "--direct"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=env,
    )


def test_direct_mode_blocks_with_a_NONZERO_exit_not_a_json_decision(tmp_path):
    """The point of --direct: pre-commit reads exit codes, not stdout JSON.

    The JSON path always exits 0 and refuses via {"decision":"block"}. No other host
    speaks that, so a Codex session committing in-session skipped this guard entirely
    — and BACKLOG #348's profile-based route lets Codex commit in-session.
    """
    root = _context(
        tmp_path,
        backlog_items=1,
        session_state_lines=1,
        learning_log_active_lines=LEARNING_LOG_LIMIT + 1,
    )
    result = _run_direct(root)
    assert result.returncode == 1, (
        "the blocking arm must fail the commit through the exit code"
    )
    assert "LEARNING-LOG active section" in result.stdout
    assert "decision" not in result.stdout, (
        "direct mode must not emit the JSON protocol"
    )


def test_direct_mode_keeps_the_advisory_arms_advisory(tmp_path):
    """Same asymmetry as the JSON path: count and snapshot size report, never block."""
    root = _context(
        tmp_path,
        backlog_items=BACKLOG_LIMIT + 5,
        session_state_lines=SESSION_STATE_LIMIT + 5,
    )
    result = _run_direct(root)
    assert result.returncode == 0, "advisory arms must not fail a commit"
    assert "BACKLOG is at" in result.stdout
    assert "SESSION-STATE is at" in result.stdout


def test_direct_mode_is_silent_when_everything_fits(tmp_path):
    root = _context(tmp_path, backlog_items=1, session_state_lines=1)
    result = _run_direct(root)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_direct_mode_honours_the_documented_bypass(tmp_path):
    root = _context(
        tmp_path,
        backlog_items=1,
        session_state_lines=1,
        learning_log_active_lines=LEARNING_LOG_LIMIT + 1,
    )
    result = _run_direct(root, {"MEMORY_SIZE_SKIP": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_the_guard_is_wired_into_a_host_agnostic_seam():
    """A guard only Claude can trigger is not a guard on the repository.

    Pins the WIRING, not just the capability: `--direct` working is useless if nothing
    invokes it. Reads the config as text so the test does not depend on PyYAML.
    """
    cfg = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "pre-commit-memory-size-guard.sh --direct" in cfg, (
        "the memory size guard must run at a seam every host honours, not only "
        "through Claude Code's PreToolUse protocol"
    )


def test_the_advisory_arms_actually_REACH_a_human_through_pre_commit(tmp_path):
    """`verbose: true`, without which the advisory arms are mute at this seam.

    pre-commit swallows a passing hook's stdout by default. The blocking arm was
    always fine — a non-zero exit is loud — but the backlog-count and SESSION-STATE
    notices exist ONLY to be read, and they reached nobody.

    HERMETIC ON PURPOSE, AND THE HISTORY IS THE REASON. The first version ran
    `pre-commit run` against the real repository and fell back to `pytest.skip` when
    that did not work. `conftest.py` redirects `$HOME` for every test, so pre-commit's
    store may be unreachable — and the test then SKIPPED rather than failed, which is
    a test quietly declining to check its own claim. It passed on one machine and
    skipped on another; the repo's unregistered-skip guard turned that into a red run.
    A skip branch in a verification test is the "could-not-run is not a pass" failure
    wearing a green tick.

    So: build a throwaway git repo with a `repo: local` config carrying only this
    hook, and run pre-commit there. No real `$HOME`, no shared store, no network, no
    downloaded environments (`language: system` runs in-place). If pre-commit itself
    is missing, that is a genuine environment gap and the test FAILS rather than
    skipping — the whole point is that this claim gets checked or the run goes red.
    """
    cfg = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    block = cfg.split("id: memory-size-guard", 1)[1].split("- id:", 1)[0]
    assert "verbose: true" in block, (
        "without verbose, a passing run prints only 'Passed' and the advisory "
        "notices are swallowed"
    )

    root = _context(tmp_path, backlog_items=BACKLOG_LIMIT + 5, session_state_lines=1)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: memory-size-guard\n"
        "        name: memory file size guard\n"
        f"        entry: bash {HOOK}\n"
        "        args: ['--direct']\n"
        "        language: system\n"
        "        pass_filenames: false\n"
        "        verbose: true\n"
        "        always_run: true\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True, capture_output=True)

    result = subprocess.run(
        ["pre-commit", "run", "memory-size-guard", "--all-files"],
        cwd=str(root),
        capture_output=True,
        text=True,
        env={**os.environ, "PRE_COMMIT_HOME": str(tmp_path / "pc-cache")},
    )
    assert "hook id: memory-size-guard" in result.stdout, (
        "verbose did not take effect — pre-commit printed no hook detail:\n"
        + result.stdout
        + result.stderr
    )
    assert "BACKLOG is at" in result.stdout, (
        "a PASSING run must still surface its advisory text, or the notices are "
        "mute at the seam that was supposed to carry them:\n" + result.stdout
    )


@pytest.mark.parametrize("over_by", [1, 25])
def test_backlog_over_limit_is_advisory_only(tmp_path, over_by):
    out = _run(
        _context(
            tmp_path, backlog_items=BACKLOG_LIMIT + over_by, session_state_lines=10
        )
    )
    assert out is not None, "an over-length backlog must still be REPORTED, not silent"
    assert "decision" not in out, f"backlog count must never block, got: {out}"
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert str(BACKLOG_LIMIT + over_by) in context
    # The notice must tell the agent what NOT to do, or the next session repeats the
    # merge-to-clear-the-number mistake this change was made to prevent.
    assert "do NOT merge" in context


def test_backlog_at_limit_is_silent(tmp_path):
    out = _run(_context(tmp_path, backlog_items=BACKLOG_LIMIT, session_state_lines=10))
    assert out is None, f"at the limit the hook should say nothing, got: {out}"


@pytest.mark.parametrize("over_by", [1, 50])
def test_session_state_over_limit_is_advisory_only(tmp_path, over_by):
    """Changed 2026-08-15 by user decision: reported, never blocking.

    The commit must go through. The number must still be said out loud — demoting the
    severity is not the same as removing the check, and a silent oversized file is the
    unbounded-growth condition this hook exists to prevent.
    """
    out = _run(
        _context(
            tmp_path,
            backlog_items=5,
            session_state_lines=SESSION_STATE_LIMIT + over_by,
        )
    )
    assert out is not None, "an oversized SESSION-STATE must still be REPORTED"
    assert "decision" not in out, f"SESSION-STATE size must not block, got: {out}"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "SESSION-STATE" in context
    # Pinned to a fixture-only number: if payload parsing fails, the hook falls back
    # to $PWD (the real repo, also over the limit) and this test would pass green
    # having never read tmp_path.
    assert str(SESSION_STATE_LIMIT + over_by) in context, context
    # The notice must carry the same do-not-do-the-cheap-thing warning the backlog arm
    # does, or demoting the block just relocates the delete-to-hit-the-number instinct.
    assert "rather than deleting them" in context, context


def test_learning_log_over_limit_still_blocks(tmp_path):
    """The one arm that keeps its teeth. If this ever goes quiet, the hook no longer
    blocks anything and the {"decision":"block"} emission path is dead code."""
    out = _run(
        _context(
            tmp_path,
            backlog_items=5,
            session_state_lines=10,
            learning_log_active_lines=LEARNING_LOG_LIMIT + 20,
        )
    )
    assert out is not None and out.get("decision") == "block", out
    assert "LEARNING-LOG" in out["reason"]
    assert str(LEARNING_LOG_LIMIT + 20) in out["reason"], out["reason"]


def test_blocking_reason_also_carries_the_advisory_notices(tmp_path):
    """A block must not swallow the advisories — otherwise the count and the
    SESSION-STATE size are invisible exactly when the memory files are in the worst
    shape."""
    out = _run(
        _context(
            tmp_path,
            backlog_items=BACKLOG_LIMIT + 5,
            session_state_lines=SESSION_STATE_LIMIT + 50,
            learning_log_active_lines=LEARNING_LOG_LIMIT + 20,
        )
    )
    assert out.get("decision") == "block"
    assert "LEARNING-LOG" in out["reason"]
    assert "BACKLOG is at" in out["reason"]
    assert "SESSION-STATE is at" in out["reason"]
    assert str(LEARNING_LOG_LIMIT + 20) in out["reason"], out["reason"]
    assert str(SESSION_STATE_LIMIT + 50) in out["reason"], out["reason"]
    assert str(BACKLOG_LIMIT + 5) in out["reason"], out["reason"]


def test_non_commit_command_is_ignored(tmp_path):
    out = _run(
        _context(tmp_path, backlog_items=BACKLOG_LIMIT + 20, session_state_lines=999),
        command="git status",
    )
    assert out is None, "the guard is scoped to `git commit`"


def test_skip_variable_silences_everything(tmp_path):
    out = _run(
        _context(tmp_path, backlog_items=BACKLOG_LIMIT + 20, session_state_lines=999),
        env_extra={"MEMORY_SIZE_SKIP": "1"},
    )
    assert out is None
