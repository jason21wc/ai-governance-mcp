"""Size is a quality-review signal, never a reason to block or mutate memory.

Both host protocols report the same canonical targets. LEARNING-LOG includes its
Graduated Patterns section: moving a lesson there must not hide file growth.
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
LEARNING_LOG_LIMIT = 200


def _context(
    tmp_path: Path,
    *,
    backlog_items: int,
    session_state_lines: int,
    learning_log_lines: int = 3,
    graduated_lines: int = 0,
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
    # Counts include the optional graduated heading and every row below it.
    lines = [f"lesson {i}" for i in range(learning_log_lines - graduated_lines)]
    if graduated_lines:
        lines += ["## Graduated Patterns"] + [
            f"graduated lesson {i}" for i in range(graduated_lines - 1)
        ]
    (ctx / "LEARNING-LOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    """`--direct`: no stdin or command detection; plain text and a passing exit.

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


@pytest.mark.parametrize("direct", [False, True])
@pytest.mark.parametrize("lines", [200, 201])
def test_learning_log_total_line_boundary_in_both_protocols(tmp_path, direct, lines):
    root = _context(
        tmp_path, backlog_items=1, session_state_lines=1, learning_log_lines=lines
    )
    if direct:
        result = _run_direct(root)
        assert result.returncode == 0, result.stderr
        notice = result.stdout
        assert "decision" not in notice
    else:
        out = _run(root)
        assert out is None or "decision" not in out
        notice = out["hookSpecificOutput"]["additionalContext"] if out else ""
    if lines == 200:
        assert not notice
    else:
        assert "201 total lines" in notice
        assert "target: 200" in notice
        assert "Review content quality" in notice
        assert "do NOT merge, delete, or graduate entries solely" in notice


@pytest.mark.parametrize("direct", [False, True])
def test_graduated_patterns_count_toward_total_without_mutation(tmp_path, direct):
    root = _context(
        tmp_path,
        backlog_items=1,
        session_state_lines=1,
        learning_log_lines=601,
        graduated_lines=598,
    )
    before = {p: p.read_bytes() for p in (root / "_ai-context").iterdir()}
    if direct:
        result = _run_direct(root)
        assert result.returncode == 0, result.stderr
        notice = result.stdout
    else:
        out = _run(root)
        assert "decision" not in out
        notice = out["hookSpecificOutput"]["additionalContext"]
    assert "601 total lines" in notice
    assert "including graduated patterns" in notice
    assert {p: p.read_bytes() for p in (root / "_ai-context").iterdir()} == before


def test_direct_mode_keeps_the_advisory_arms_advisory(tmp_path):
    """Count and snapshot size continue to report without blocking."""
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
        learning_log_lines=LEARNING_LOG_LIMIT + 1,
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


def test_the_advisory_arms_actually_REACH_a_human_through_pre_commit(
    tmp_path, monkeypatch
):
    """`verbose: true`, without which the advisory arms are mute at this seam.

    pre-commit swallows a passing hook's stdout by default. All three advisory
    notices must remain visible through the real pre-commit invocation.

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
    _installed_hook(tmp_path, monkeypatch)
    cfg = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    block = cfg.split("id: memory-size-guard", 1)[1].split("- id:", 1)[0]
    assert "verbose: true" in block, (
        "without verbose, a passing run prints only 'Passed' and the advisory "
        "notices are swallowed"
    )

    root = _context(
        tmp_path,
        backlog_items=BACKLOG_LIMIT + 5,
        session_state_lines=301,
        learning_log_lines=201,
    )
    ll = root / "_ai-context/LEARNING-LOG.md"
    ll.write_text(ll.read_text().replace("lesson 0\n", "### Delivered lesson\n", 1))
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
    assert result.returncode == 0, result.stdout + result.stderr
    for expected in (
        "BACKLOG is at 65",
        "SESSION-STATE is at",
        "201 total lines",
        "Largest Learning Log entries",
        "Delivered lesson",
    ):
        assert expected in result.stdout, result.stdout


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


@pytest.mark.parametrize("direct", [False, True])
def test_all_size_notices_are_reported_together_without_blocking(tmp_path, direct):
    root = _context(
        tmp_path,
        backlog_items=BACKLOG_LIMIT + 5,
        session_state_lines=SESSION_STATE_LIMIT + 50,
        learning_log_lines=LEARNING_LOG_LIMIT + 20,
    )
    if direct:
        result = _run_direct(root)
        assert result.returncode == 0, result.stderr
        notice = result.stdout
    else:
        out = _run(root)
        assert "decision" not in out
        assert "permissionDecision" not in out["hookSpecificOutput"]
        notice = out["hookSpecificOutput"]["additionalContext"]
    for expected in ("220 total lines", "BACKLOG is at 65", "SESSION-STATE is at"):
        assert expected in notice
    assert "350" in notice


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


@pytest.mark.parametrize("direct", [False, True])
def test_skip_is_still_audit_logged(tmp_path, direct):
    root = _context(
        tmp_path, backlog_items=65, session_state_lines=350, learning_log_lines=220
    )
    audit = tmp_path / "bypass.log"
    env = {"MEMORY_SIZE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)}
    if direct:
        result = _run_direct(root, env)
        assert result.returncode == 0
        assert not result.stdout
    else:
        assert _run(root, env_extra=env) is None
    assert (
        "pre-commit-memory-size-guard MEMORY_SIZE_SKIP=1 advisory-skip"
        in audit.read_text()
    )


# Entry reports describe length; they never establish a pruning threshold.
REPORTER = HOOK.parent / "lib" / "memory-entry-size.py"


def _git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )


def _lesson_root(tmp_path, text, *, tracked=False):
    root = _context(tmp_path, backlog_items=0, session_state_lines=1)
    (root / "_ai-context/LEARNING-LOG.md").write_text(text, encoding="utf-8")
    _git(root, "init", "-q")
    if tracked:
        _git(root, "add", "_ai-context")
        _git(
            root,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "fixture",
        )
    return root


def _notice(root, direct, env=None):
    if direct:
        result = _run_direct(root, env)
        assert result.returncode == 0, result.stderr
        return result.stdout
    out = _run(root, env_extra=env)
    assert out is None or "decision" not in out
    return out["hookSpecificOutput"]["additionalContext"] if out else ""


def _report(path):
    import sys

    result = subprocess.run(
        [sys.executable, str(REPORTER), str(path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("direct", [False, True])
@pytest.mark.parametrize("change", ["untracked", "staged", "unstaged"])
def test_below_trigger_changed_log_reports_largest_entries(tmp_path, direct, change):
    root = _lesson_root(tmp_path, "### Old\nold\n", tracked=change != "untracked")
    ll = root / "_ai-context/LEARNING-LOG.md"
    ll.write_text("### Changed below trigger\nA useful rule.\n", encoding="utf-8")
    if change == "staged":
        _git(root, "add", str(ll))
    before = ll.read_bytes()
    status = _git(root, "status", "--porcelain").stdout
    notice = _notice(root, direct)
    assert "Largest Learning Log entries" in notice
    assert "Changed below trigger" in notice
    assert "14 characters" in notice
    assert "total lines" not in notice
    assert ll.read_bytes() == before
    assert _git(root, "status", "--porcelain").stdout == status


@pytest.mark.parametrize("direct", [False, True])
def test_unchanged_below_trigger_log_is_silent(tmp_path, direct):
    root = _lesson_root(tmp_path, "### Existing\nA useful rule.\n", tracked=True)
    assert _notice(root, direct) == ""


@pytest.mark.parametrize("direct", [False, True])
def test_unchanged_over_trigger_log_still_reports_entries(tmp_path, direct):
    root = _lesson_root(
        tmp_path, "### Existing\nA useful rule.\n" + "\n" * 200, tracked=True
    )
    notice = _notice(root, direct)
    assert "total lines" in notice
    assert "Existing" in notice


def test_unconditional_helper_normalizes_wrapping_and_ranks_top_three_with_stable_ties(
    tmp_path,
):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_text(
        "### First\n alpha  beta\n gamma\n### Second\nalpha beta gamma\n"
        "### Short\nx\n### Largest\n" + "z" * 40 + "\n",
        encoding="utf-8",
    )
    notice = _report(ll)
    assert (
        notice.index("Largest —") < notice.index("First —") < notice.index("Second —")
    )
    assert notice.count("16 characters") == 2
    assert "Short" not in notice
    assert "line 1: First" in notice


def test_closing_hashes_and_long_internal_whitespace(tmp_path):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_text(
        "### Closed \t### \t\nbody\n### Literal###\nbody\n"
        + "### Long"
        + " " * 100_000
        + "tail\nbody\n",
        encoding="utf-8",
    )
    notice = _report(ll)
    assert "Closed — 4 characters" in notice
    assert "Literal### — 4 characters" in notice
    assert "line 5: Long" in notice


def test_heading_boundaries_fences_and_misplaced_entries(tmp_path):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_text(
        "### Before active\nbody\n## Active Lessons\n### Main\nx\n#### Subheading\ny\n"
        "~~~markdown\n### Fake\n~~~~\n## Graduated Patterns\n| row | ignored |\n"
        "### Misplaced\nkept\n# End\nexcluded trailing prose\n### Empty\n\n",
        encoding="utf-8",
    )
    notice = _report(ll)
    assert "Before active — 4 characters" in notice
    assert "Misplaced — 4 characters" in notice
    assert "Main —" in notice
    assert ": Fake" not in notice
    assert "Empty" not in notice
    assert "ignored" not in notice


@pytest.mark.parametrize("direct", [False, True])
def test_dynamic_headings_are_safe_bounded_and_preserve_unicode(tmp_path, direct):
    heading = 'Café "quoted" \\n literal\x1b[31m\x07\t\u202e ' + "x" * 180
    root = _lesson_root(tmp_path, "### " + heading + "\nbody\n")
    notice = _notice(root, direct)
    assert 'Café "quoted" \\n literal' in notice
    assert "\\x1b[31m\\x07\\x09\\u202e" in notice
    assert "x" * 101 not in notice
    assert "\x1b" not in notice and "\x07" not in notice and "\u202e" not in notice


@pytest.mark.parametrize(
    "text", ["", "# Log\n## Graduated Patterns\n| row | body |\n", "### Empty\n\n"]
)
def test_empty_logs_and_table_only_logs_are_quiet(tmp_path, text):
    root = _lesson_root(tmp_path, text)
    assert _notice(root, True) == ""
    assert _report(root / "_ai-context/LEARNING-LOG.md") == ""


def test_direct_outside_git_reports_but_claude_below_trigger_does_not(tmp_path):
    root = _context(tmp_path, backlog_items=0, session_state_lines=1)
    (root / "_ai-context/LEARNING-LOG.md").write_text("### Audit\nbody\n")
    assert "Audit" in _notice(root, True)
    assert _notice(root, False) == ""


def _installed_hook(tmp_path, monkeypatch):
    """Exercise the installed shape, not a helper from the source checkout."""
    import shutil

    installed = tmp_path / "hooks"
    shutil.copytree(HOOK.parent / "lib", installed / "lib")
    shutil.copy2(HOOK, installed / HOOK.name)
    monkeypatch.setitem(globals(), "HOOK", installed / HOOK.name)
    return installed


@pytest.mark.parametrize("direct", [False, True])
@pytest.mark.parametrize("failure", ["missing_helper", "read_error"])
def test_entry_report_failure_preserves_available_notices(
    tmp_path, monkeypatch, direct, failure
):
    installed = _installed_hook(tmp_path, monkeypatch)
    root = _lesson_root(tmp_path / "project", "### Rule\nbody\n" + "\n" * 201)
    if failure == "missing_helper":
        (installed / "lib/memory-entry-size.py").unlink(missing_ok=True)
    else:
        (root / "_ai-context/LEARNING-LOG.md").write_bytes(
            b"### Rule\n\xff\n" + b"\n" * 201
        )
    notice = _notice(root, direct)
    assert "entry report unavailable" in notice
    assert "total lines" in notice


def _shim(tmp_path, name, content):
    directory = tmp_path / "bin"
    directory.mkdir(exist_ok=True)
    script = directory / name
    script.write_text("#!/bin/bash\n" + content, encoding="utf-8")
    script.chmod(0o755)
    return {"PATH": str(directory) + os.pathsep + os.environ["PATH"]}


@pytest.mark.parametrize("direct", [False, True])
def test_git_status_failure_is_unknown_and_runs_ranking(tmp_path, direct):
    import shlex
    import shutil

    root = _lesson_root(
        tmp_path / "project", "### Must still inspect\nbody\n", tracked=True
    )
    git = shlex.quote(shutil.which("git"))
    env = _shim(
        tmp_path,
        "git",
        f'for arg; do if [[ "$arg" == status ]]; then exit 42; fi; done\nexec {git} "$@"\n',
    )
    notice = _notice(root, direct, env)
    assert "Git status unavailable" in notice
    assert "Must still inspect" in notice


def test_claude_without_python_never_measures_process_checkout(tmp_path):
    import shutil

    root = _lesson_root(tmp_path / "payload-root", "### Payload\nbody\n")
    directory = tmp_path / "no-python"
    directory.mkdir()
    for command in ("bash", "cat", "dirname", "jq", "git", "wc", "tr", "grep"):
        (directory / command).symlink_to(shutil.which(command))
    out = _run(root, env_extra={"PATH": str(directory)})
    notice = out["hookSpecificOutput"]["additionalContext"]
    assert "root inspection unavailable" in notice
    assert "total lines" not in notice
    assert "BACKLOG is at" not in notice


def test_neither_command_decoder_claims_no_commit_recognition(tmp_path):
    import shutil

    directory = tmp_path / "no-decoders"
    directory.mkdir()
    for command in ("bash", "cat", "dirname"):
        (directory / command).symlink_to(shutil.which(command))
    out = _run(tmp_path, env_extra={"PATH": str(directory)})
    assert (
        "command/root inspection unavailable"
        in out["hookSpecificOutput"]["additionalContext"]
    )


def test_failed_json_serializer_returns_fixed_valid_diagnostic(tmp_path):
    import shlex
    import shutil

    root = _lesson_root(tmp_path / "project", '### "Unsafe"\\n\nbody\n')
    python = shlex.quote(shutil.which("python3"))
    env = _shim(
        tmp_path,
        "python3",
        f'if [[ "${{2:-}}" == *json.dumps* ]]; then printf "partial unsafe output"; exit 42; fi\nexec {python} "$@"\n',
    )
    out = _run(root, env_extra=env)
    notice = out["hookSpecificOutput"]["additionalContext"]
    assert "output unavailable" in notice
    assert "Unsafe" not in notice
    assert "partial" not in notice


@pytest.mark.parametrize(
    "opening,wrong_close,closing",
    [
        ("````python", "```", "`````"),
        ("~~~", "```", "~~~"),
        ("   ```", "``` trailing", "   ```"),
    ],
)
def test_fences_cannot_manufacture_entries_or_end_on_wrong_marker(
    tmp_path, opening, wrong_close, closing
):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_text(
        f"{opening}\n### Fake one\nbody\n{wrong_close}\n### Fake two\nbody\n"
        f"{closing}\n### Real\nbody\n"
    )
    notice = _report(ll)
    assert "Real — 4 characters" in notice
    assert "Fake" not in notice


def test_markdown_body_syntax_urls_and_subheadings_count_as_text(tmp_path):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_text("### Rule\n**bold**\nhttps://example.test\n#### Detail\n")
    notice = _report(ll)
    assert "41 characters" in notice


def test_missing_log_is_quiet_for_helper_and_both_transports(tmp_path):
    root = _context(tmp_path, backlog_items=0, session_state_lines=1)
    ll = root / "_ai-context/LEARNING-LOG.md"
    ll.unlink()
    assert _report(ll) == ""
    assert _notice(root, True) == ""
    assert _notice(root, False) == ""


def test_direct_without_python_retains_counts_and_reports_unavailable_ranking(tmp_path):
    import shutil

    root = _lesson_root(tmp_path / "root", "### Entry\nbody\n" + "\n" * 201)
    directory = tmp_path / "no-python"
    directory.mkdir()
    for command in ("bash", "cat", "dirname", "git", "wc", "tr", "grep"):
        (directory / command).symlink_to(shutil.which(command))
    notice = _notice(root, True, {"PATH": str(directory)})
    assert "203 total lines" in notice
    assert "entry report unavailable" in notice


def test_claude_python_command_decoder_fallback(tmp_path):
    root = _lesson_root(tmp_path / "root", "### Decoder fallback\nbody\n")
    env = _shim(tmp_path, "jq", "exit 42\n")
    assert "Decoder fallback" in _notice(root, False, env)


@pytest.mark.parametrize("direct", [False, True])
def test_git_repository_inspection_failure_is_not_outside_git(tmp_path, direct):
    root = _lesson_root(
        tmp_path / "root", "### Inspect despite unknown\nbody\n", tracked=True
    )
    env = _shim(tmp_path, "git", "echo 'unexpected failure' >&2; exit 42\n")
    notice = _notice(root, direct, env)
    assert "Git status unavailable" in notice
    assert "Inspect despite unknown" in notice


def test_embedded_line_controls_do_not_manufacture_headings(tmp_path):
    ll = tmp_path / "LEARNING-LOG.md"
    ll.write_bytes(
        b"### Real\r### Injected\v### Also fake\x85literal\nbody\n".replace(
            b"\x85", "\u0085".encode()
        )
    )
    notice = _report(ll)
    assert "line 1: Real\\x0d### Injected\\x0b### Also fake\\x85literal" in notice
    assert notice.count("characters\n") == 1


def test_helper_reports_read_failure_as_unavailable(tmp_path):
    import sys

    result = subprocess.run(
        [sys.executable, str(REPORTER), str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert not result.stdout
    assert "entry report unavailable" in result.stderr


def test_direct_subdirectory_resolves_the_acting_worktree(tmp_path):
    root = _lesson_root(tmp_path, "### Worktree root\nbody\n")
    nested = root / "nested"
    nested.mkdir()
    assert "Worktree root" in _notice(nested, True)
