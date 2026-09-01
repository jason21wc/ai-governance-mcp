"""Tests for the repo-canonical journal-reminder hook (UserPromptSubmit).

The hook (`.claude/hooks/journal-reminder.sh`) is the Layer-2 memory-maintenance
trigger (title-10 §7.11.3): on each user prompt it checks whether the session
transcript has grown long with NO recent memory-file writes, and if so injects
a JOURNAL directive telling the session to spawn a background analysis subagent.
Repo-canonical, symlinked into ~/.claude/hooks and ~/.codex/hooks (registration stays user-level
only). It must never block a prompt (always exit 0).

Also covers the fired-vs-ran instrument's FIRE half: every injection appends one
line to $JOURNAL_FIRE_LOG (default ~/.claude/journal-reminder-fires.log, capped).

TestSessionRootResolution covers BACKLOG #230(c): the hook used to gate its marker
check on raw `$PWD`, so an identical violating transcript fired from the repo root
and was SILENT from `src/` or `tests/`. It now resolves the acting checkout through
the shared `lib/repo-root.sh` (BACKLOG #214), which normalizes any subdirectory to
its worktree root.
"""

import json
import re
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "journal-reminder.sh"

MEMORY_FILES = [
    "SESSION-STATE.md",
    "PROJECT-MEMORY.md",
    "LEARNING-LOG.md",
    "BACKLOG.md",
    "OPERATIONS.md",
    "ARCHITECTURE.md",
]


def make_project(tmp_path, marker="SESSION-STATE.md"):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    if marker:
        (d / marker).write_text("# marker\n")
    return d


requires_git = pytest.mark.skipif(
    shutil.which("git") is None, reason="root resolution needs git rev-parse"
)


def make_git_project(tmp_path, marker="AGENTS.md", subdir="src"):
    """A real git worktree with the marker at its ROOT and an empty subdirectory.

    The subdirectory is the whole point: it is where a session actually sits when
    it is working on code, and where the hook used to fall silent.
    """
    d = tmp_path / "repo"
    (d / subdir).mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", str(d)], check=True, capture_output=True, timeout=30
    )
    if marker:
        marker_path = d / marker
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("# marker\n")
    return d


def make_transcript(tmp_path, lines=300, memory_write_at_end=False):
    """Synthetic session transcript JSONL."""
    rows = ['{"type":"user","message":{"content":"hello"}}'] * lines
    if memory_write_at_end:
        rows.append(
            json.dumps(
                {
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Edit",
                                "input": {"file_path": "/p/SESSION-STATE.md"},
                            }
                        ]
                    }
                }
            )
        )
    f = tmp_path / "transcript.jsonl"
    f.write_text("\n".join(rows) + "\n")
    return f


def run_hook(
    project_dir, transcript=None, env=None, raw_stdin=None, payload_cwd=None, hook=HOOK
):
    """Run the hook with process cwd=project_dir.

    `payload_cwd` populates the JSON `cwd` field Claude Code sends, which the
    shared resolver prefers over `$PWD`. `hook` allows pointing at a copy of the
    script (used to exercise the missing-lib fallback).
    """
    if raw_stdin is not None:
        stdin = raw_stdin
    else:
        payload = {"transcript_path": str(transcript)}
        if payload_cwd is not None:
            payload["cwd"] = str(payload_cwd)
        stdin = json.dumps(payload)
    e = os.environ.copy()
    for k in list(e):
        if k.startswith("JOURNAL_"):
            e.pop(k)
    # GIT_DIR/GIT_WORK_TREE would redirect the resolver's `git rev-parse` away
    # from the tmp repo (they are set when a suite runs from inside a git hook).
    for k in ("GIT_DIR", "GIT_WORK_TREE", "CLAUDE_PROJECT_DIR"):
        e.pop(k, None)
    # Never let a test fire land in the REAL ~/.claude fire log — that would
    # contaminate the fired-vs-ran compliance instrument on developer machines.
    e["JOURNAL_FIRE_LOG"] = str(Path(tempfile.mkdtemp()) / "fires.log")
    if env:
        e.update(env)
    return subprocess.run(
        ["bash", str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        env=e,
        cwd=project_dir,
        timeout=15,
    )


def context(result):
    """Injected additionalContext, or None if silent.

    Asserts the UserPromptSubmit OUTPUT CONTRACT: nested `hookSpecificOutput`
    envelope (a flat `{"additionalContext"}` is silently dropped by Claude Code —
    FM-HOOK-OUTPUT-ENVELOPE).
    """
    out = result.stdout.strip()
    if not out:
        return None
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "UserPromptSubmit"
    return hso.get("additionalContext")


class TestJournalReminderHook:
    def test_fires_long_session_without_memory_writes(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        r = run_hook(proj, tx)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None and "JOURNAL" in ctx

    def test_message_carries_all_711_3_routes(self, tmp_path):
        """§7.11.3 drift regression: the directive must name all six memory files
        AND the Reference Library route via capture_reference, with the capture
        human-gated (user approval), per the plan's HITL decision #4."""
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        ctx = context(run_hook(proj, tx)) or ""
        for mf in MEMORY_FILES:
            assert mf in ctx, f"directive missing memory file {mf}"
        assert "Reference Library" in ctx
        assert "capture_reference" in ctx
        assert "approval" in ctx  # human-gated captures

    def test_silent_when_memory_recently_written(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300, memory_write_at_end=True)
        r = run_hook(proj, tx)
        assert r.returncode == 0
        assert context(r) is None

    def test_silent_below_min_lines(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=100)
        assert context(run_hook(proj, tx)) is None

    def test_silent_without_marker(self, tmp_path):
        proj = make_project(tmp_path, marker=None)
        tx = make_transcript(tmp_path, lines=300)
        assert context(run_hook(proj, tx)) is None

    def test_agents_md_marker_suffices(self, tmp_path):
        proj = make_project(tmp_path, marker="AGENTS.md")
        tx = make_transcript(tmp_path, lines=300)
        assert context(run_hook(proj, tx)) is not None

    def test_skip_env_silent(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        r = run_hook(proj, tx, env={"JOURNAL_SKIP": "true"})
        assert r.returncode == 0
        assert context(r) is None

    def test_missing_transcript_silent(self, tmp_path):
        proj = make_project(tmp_path)
        missing = tmp_path / "nope.jsonl"
        r = run_hook(proj, missing)
        assert r.returncode == 0
        assert context(r) is None

    def test_malformed_stdin_never_crashes(self, tmp_path):
        proj = make_project(tmp_path)
        for bad in ["", "not json", "{"]:
            r = run_hook(proj, raw_stdin=bad)
            assert r.returncode == 0
            assert r.stdout.strip() == ""

    # --- fired-vs-ran instrument: the FIRE half ---

    def test_fire_appends_one_log_line(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        log = tmp_path / "fires.log"
        r = run_hook(proj, tx, env={"JOURNAL_FIRE_LOG": str(log)})
        assert context(r) is not None
        assert log.exists()
        lines = log.read_text().strip().splitlines()
        assert len(lines) == 1
        assert str(proj) in lines[0]  # which project fired

    def test_no_fire_no_log_line(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=100)  # below min -> silent
        log = tmp_path / "fires.log"
        run_hook(proj, tx, env={"JOURNAL_FIRE_LOG": str(log)})
        assert not log.exists()

    def test_fire_log_capped(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        log = tmp_path / "fires.log"
        # Pre-fill past the 100KB cap; a fire must trim it (tail-keep), not grow it.
        log.write_text(("x" * 100 + "\n") * 1100)  # ~111KB
        before = log.stat().st_size
        r = run_hook(proj, tx, env={"JOURNAL_FIRE_LOG": str(log)})
        assert context(r) is not None
        assert log.stat().st_size < before

    def test_log_failure_does_not_block_injection(self, tmp_path):
        proj = make_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        unwritable = tmp_path / "no-such-dir" / "fires.log"
        r = run_hook(proj, tx, env={"JOURNAL_FIRE_LOG": str(unwritable)})
        assert r.returncode == 0
        assert context(r) is not None  # directive still injected


@requires_git
class TestDreamWorktreeSuppression:
    """Session-278: journal suppressed when a dream worktree exists.

    Dream mines all recent sessions more thoroughly than journal mines the
    current one. Running both wastes tokens and risks conflicting edits.
    """

    def test_dream_worktree_suppresses_journal(self, tmp_path):
        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        wt_path = tmp_path / "dream-sibling"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/dream-other", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        assert context(run_hook(repo, tx)) is None

    def test_non_dream_worktree_does_not_suppress(self, tmp_path):
        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        wt_path = tmp_path / "feature-sibling"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/feature-xyz", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        ctx = context(run_hook(repo, tx))
        assert ctx is not None and "JOURNAL" in ctx

    def test_dream_in_branch_name_matches(self, tmp_path):
        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        wt_path = tmp_path / "other-session"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/dream-aug5", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        assert context(run_hook(repo, tx)) is None


@requires_git
class TestSessionRootResolution:
    """BACKLOG #230(c) — the marker gate reads the acting CHECKOUT, not raw `$PWD`.

    The defect's failure direction was SILENCE, which is the expensive one here:
    a hook that only speaks when the session happens to sit at the repo root
    stops speaking exactly when the session is deepest in the code, and the
    memory maintenance it exists to trigger simply never happens. Nothing in the
    transcript differs between the two runs — only the cwd does.
    """

    def test_fires_from_subdirectory_of_repo(self, tmp_path):
        """The defect, stated as a test: same transcript, cwd one level down."""
        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        assert context(run_hook(repo, tx)) is not None, "control: root must fire"
        ctx = context(run_hook(repo / "src", tx))
        assert ctx is not None and "JOURNAL" in ctx

    def test_fires_from_deeply_nested_subdirectory(self, tmp_path):
        repo = make_git_project(tmp_path)
        deep = repo / "src" / "a" / "b" / "c"
        deep.mkdir(parents=True)
        assert context(run_hook(deep, make_transcript(tmp_path, lines=300))) is not None

    def test_payload_cwd_subdirectory_wins_over_process_cwd(self, tmp_path):
        """Claude Code sends `cwd` in the payload; the resolver prefers it.

        Process cwd is a NON-marker directory outside the repo, so a pass here
        can only come from the payload field.
        """
        repo = make_git_project(tmp_path)
        outside = tmp_path / "elsewhere"
        outside.mkdir()
        tx = make_transcript(tmp_path, lines=300)
        assert context(run_hook(outside, tx)) is None  # control: no payload cwd
        assert context(run_hook(outside, tx, payload_cwd=repo / "src")) is not None

    def test_subdirectory_of_unmarked_repo_stays_silent(self, tmp_path):
        """No new false positives: walking up must find markers, not invent them."""
        repo = make_git_project(tmp_path, marker=None)
        r = run_hook(repo / "src", make_transcript(tmp_path, lines=300))
        assert r.returncode == 0
        assert context(r) is None

    def test_subdirectory_still_respects_recent_memory_write(self, tmp_path):
        """The root fix must not bypass the other gates.

        Carries its own control so it discriminates in both directions: the same
        subdirectory, same everything, differing only in whether memory was
        written, must fire in one case and not the other.
        """
        repo = make_git_project(tmp_path)
        written = make_transcript(tmp_path, lines=300, memory_write_at_end=True)
        assert context(run_hook(repo / "src", written)) is None
        (tmp_path / "b").mkdir()
        not_written = make_transcript(tmp_path / "b", lines=300)
        assert context(run_hook(repo / "src", not_written)) is not None

    def test_non_git_directory_without_marker_stays_silent(self, tmp_path):
        """Non-git candidates are used as-is — no upward walk, so still silent."""
        plain = tmp_path / "plain" / "nested"
        plain.mkdir(parents=True)
        assert context(run_hook(plain, make_transcript(tmp_path, lines=300))) is None

    def test_fire_log_records_repo_root_not_subdirectory(self, tmp_path):
        """The fired-vs-ran instrument counts fires PER PROJECT.

        Logging raw cwd would split one repo into as many identities as the
        session visited subdirectories, silently inflating the fire count.
        """
        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        log = tmp_path / "fires.log"
        r = run_hook(repo / "src", tx, env={"JOURNAL_FIRE_LOG": str(log)})
        assert context(r) is not None
        line = log.read_text().strip()
        assert os.path.realpath(repo) in line
        assert os.path.realpath(repo / "src") not in line

    def test_ai_context_layout_marker_is_recognised(self, tmp_path):
        """The memory files moved to `_ai-context/` in v2.62.0.

        A gate that only probes the root path is half dead: this repo passes it
        solely because a root AGENTS.md happens to exist. A governed project on
        the unified layout without one was silent — the same failure direction
        the rest of this class is about.
        """
        repo = make_git_project(tmp_path, marker="_ai-context/SESSION-STATE.md")
        assert not (repo / "AGENTS.md").exists()
        assert not (repo / "SESSION-STATE.md").exists()
        tx = make_transcript(tmp_path, lines=300)
        assert context(run_hook(repo, tx)) is not None
        assert context(run_hook(repo / "src", tx)) is not None

    def test_corrupt_lib_degrades_instead_of_blocking_the_prompt(self, tmp_path):
        """A TRUNCATED lib must not take the prompt down with it.

        A truncated or missing lib is the realistic corruption now: `lib/` is one symlink into the checkout, so a moved or renamed repo removes it outright (BACKLOG #226/#236).
        Under `set -e` a parse error in a sourced file kills the parent with exit
        2 — and for UserPromptSubmit, exit 2 BLOCKS the user's prompt and shows
        stderr. That is far worse than the silence this whole change removes, so
        the lib is validated before it is sourced. `|| true` does NOT cover this
        case; the abort happens during parsing, before the hook can catch it.
        """
        hooks = tmp_path / "hooks-corrupt-lib"
        (hooks / "lib").mkdir(parents=True)
        shutil.copy(HOOK, hooks / "journal-reminder.sh")
        (hooks / "lib" / "repo-root.sh").write_text(
            "resolve_session_root() {\n if [ \n"
        )

        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        r = run_hook(repo, tx, hook=hooks / "journal-reminder.sh")
        assert r.returncode == 0, f"exit {r.returncode} would block the prompt"
        assert context(r) is not None, "must degrade to root-only, not to silence"

    def test_missing_lib_degrades_to_root_only_not_to_silence(self, tmp_path):
        """Lib-unavailable fallback (~/.claude, ~/.codex symlink to this file; `lib/` can go missing).

        The dream hook exits 0 when lib/repo-root.sh is absent because silence is
        its designed direction. Silence is this hook's DEFECT, so a mirror without
        the lib must degrade to the old raw-`$PWD` behaviour instead: still fires
        from the root, merely loses the subdirectory case.
        """
        lonely_dir = tmp_path / "hooks-no-lib"
        lonely_dir.mkdir()
        lonely = lonely_dir / "journal-reminder.sh"
        shutil.copy(HOOK, lonely)
        assert not (lonely_dir / "lib").exists()

        repo = make_git_project(tmp_path)
        tx = make_transcript(tmp_path, lines=300)
        r_root = run_hook(repo, tx, hook=lonely)
        assert r_root.returncode == 0
        assert context(r_root) is not None, "fallback must not go silent at the root"
        assert context(run_hook(repo / "src", tx, hook=lonely)) is None  # known loss


class TestMarkerListParity:
    """The fallback marker list must not drift from the shared one (BACKLOG #238).

    `has_memory_markers` is defined TWICE: canonically in `lib/repo-root.sh`, and
    again inside `journal-reminder.sh` guarded by `declare -F`, which runs only
    when the lib could not be loaded.

    WHY THE DUPLICATE IS KEPT RATHER THAN DELETED. If the lib is missing and the
    hook calls an undefined function, bash returns 127; the call site is
    `if ! has_memory_markers ...`, and negating 127 yields TRUE — read as "no
    markers", so the hook exits 0 and silently disables itself in every project.
    Silence is this hook's worst direction, and as a UserPromptSubmit hook a
    nonzero exit BLOCKS the user's prompt, so it must degrade rather than die.
    Any offline fallback has to hardcode: if `lib/` is gone, a data file beside
    it is gone too. So the choice is not "one list or two" — it is "two lists
    that are checked, or one list plus a new silent-failure mode."

    WHY THIS TEST EXISTS. Two hand-kept lists already drifted once: this hook
    learned about the `_ai-context/` layout in v2.62.0 and `session-start-dream.sh`
    did not, which silently disabled the dream cadence for every migrated project
    without a root `AGENTS.md`. This repo masked it because a root `AGENTS.md`
    still exists here. The lists are now pinned to each other, so that drift
    fails at authoring time instead of going unnoticed for a release.

    NEITHER LIST IS RESTATED HERE. Both are extracted from source and compared,
    per `ref-ai-coding-derive-guards-from-source-of-truth`: a test that hardcodes
    the expected markers would be a THIRD hand-synced copy, which is the defect
    it is meant to catch. A legitimate change to the markers passes this test as
    long as both copies change together — which is the whole contract.
    """

    LIB = REPO / ".claude" / "hooks" / "lib" / "repo-root.sh"

    @staticmethod
    def _marker_paths(source: str) -> list[str]:
        """Ordered `$root/...` paths tested inside `has_memory_markers`."""
        body = re.search(r"has_memory_markers\(\)\s*\{(.*?)\n\s*\}", source, re.DOTALL)
        assert body, "has_memory_markers definition not found — did it get renamed?"
        return re.findall(r'\[\s*-f\s*"\$root/([^"]+)"\s*\]', body.group(1))

    def test_both_definitions_exist(self):
        """Guards the extraction itself: a silent no-match would pass vacuously."""
        assert self._marker_paths(self.LIB.read_text()), "no markers found in the lib"
        assert self._marker_paths(HOOK.read_text()), "no markers found in the fallback"

    def test_fallback_list_matches_the_shared_list_exactly(self):
        lib_markers = self._marker_paths(self.LIB.read_text())
        fallback_markers = self._marker_paths(HOOK.read_text())
        assert fallback_markers == lib_markers, (
            "journal-reminder.sh's lib-unavailable fallback has drifted from "
            f"lib/repo-root.sh.\n  lib:      {lib_markers}\n  fallback: "
            f"{fallback_markers}\nChange both together, or delete the fallback "
            "and handle the undefined-function case at the call site."
        )

    # DELETED: `test_order_is_pinned_not_just_membership`.
    #
    # It asserted `lib_markers == sorted(lib_markers, key=lib_markers.index)`,
    # which is TRUE FOR EVERY LIST — `x.index(e)` is the element's own position,
    # so the sort is the identity. A tautology dressed as a check, green for the
    # wrong reason, in the same session that closed four defects of exactly that
    # shape. Caught by a fresh-context code review, not by re-reading it.
    #
    # Its premise was also wrong: it claimed the sibling test was a set
    # comparison that a reorder could slip past. `==` on two lists is
    # order-sensitive, so ordering is already pinned by
    # `test_fallback_list_matches_the_shared_list_exactly`. Deleted rather than
    # repaired — a redundant test that reads as coverage is worse than none.
