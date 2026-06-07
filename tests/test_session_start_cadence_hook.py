"""Tests for the SessionStart cadence-surfacer hook + shared cadence.sh library.

The hook (`.claude/hooks/session-start-cadence.sh`) is STATELESS: at session
start it reads each cadence's "Next due:" date live from a project's
OPERATIONS.md (git log as fallback) and injects ONE consolidated
`additionalContext` reminder for the cadences that are DUE/OVERDUE, staying
silent otherwise. It must never block startup (always exit 0).

Dates are generated relative to today so the tests don't rot.
"""

import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "session-start-cadence.sh"
CADENCE_LIB = REPO / ".claude" / "hooks" / "lib" / "cadence.sh"
DREAM_HOOK = Path.home() / ".claude" / "hooks" / "session-start-dream.sh"


def _iso(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def _ops(c078=None, c155=None, c109=None) -> str:
    """Build an OPERATIONS.md body with the three cadence sections.

    Each arg is a 'Next due' date (YYYY-MM-DD) or None to omit the line.
    """

    def section(anchor, title, due):
        due_line = f"**Next due:** ~{due}." if due else "**Cadence:** every 10-15 days."
        return f"### {anchor}. {title}\n**Cadence:** periodic.\n{due_line}\n\n---\n"

    return (
        "# Operations\n\n## Cadences\n\n"
        + section("C-078", "Governance Compliance Review", c078)
        + section("C-155", "Feedback Loop Analysis", c155)
        + section("C-109", "Deferred-cadence audit", c109)
    )


def make_project(tmp_path, *, ops_body=None, git=False) -> Path:
    d = tmp_path / "proj"
    d.mkdir()
    (d / "SESSION-STATE.md").write_text("# state\n")
    if ops_body is not None:
        (d / "OPERATIONS.md").write_text(ops_body)
    if git:
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    return d


def run(source="startup", project_dir=None, env=None):
    payload = {"source": source}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    e = os.environ.copy()
    # Strip inherited cadence env + the real repo's CLAUDE_PROJECT_DIR.
    for k in list(e):
        if k.startswith("CADENCE_") or k == "CLAUDE_PROJECT_DIR":
            e.pop(k)
    if project_dir is not None:
        e["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env:
        e.update(env)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=e,
        timeout=15,
    )


def context(result):
    """Return the injected additionalContext string, or None if the hook was silent.

    Asserts the SessionStart OUTPUT CONTRACT: the nested `hookSpecificOutput`
    envelope with `hookEventName == "SessionStart"`. A flat `{"additionalContext"}`
    is silently dropped by Claude Code for SessionStart, so parsing via this helper
    (not `.get("additionalContext")` on the top level) makes that regression fail.
    """
    out = result.stdout.strip()
    if not out:
        return None
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]  # KeyError if someone reverts to the flat form
    assert hso["hookEventName"] == "SessionStart"
    return hso.get("additionalContext")


class TestSessionStartCadenceHook:
    def test_due_surfaces_c078(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-2), c155=_iso(100), c109=_iso(100))
        )
        r = run(project_dir=proj)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None and "C-078" in ctx

    def test_not_due_silent(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(5), c155=_iso(100), c109=_iso(100))
        )
        r = run(project_dir=proj)
        assert r.returncode == 0
        assert context(r) is None

    def test_overdue_surfaces(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-30), c155=_iso(100), c109=_iso(100))
        )
        assert "C-078" in (context(run(project_dir=proj)) or "")

    def test_due_today_is_due(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(0), c155=_iso(100), c109=_iso(100))
        )
        assert "C-078" in (context(run(project_dir=proj)) or "")

    def test_multiple_due_one_block(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-1), c155=_iso(-1), c109=_iso(100))
        )
        ctx = context(
            run(project_dir=proj)
        )  # single JSON object => parse implies one block
        assert ctx is not None
        assert "C-078" in ctx and "C-155" in ctx

    @pytest.mark.parametrize("source", ["startup", "resume", "clear", ""])
    def test_fires_on_boundary_sources(self, tmp_path, source):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-2), c155=_iso(100), c109=_iso(100))
        )
        assert context(run(source=source, project_dir=proj)) is not None

    def test_compact_source_silent(self, tmp_path):
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-2), c155=_iso(100), c109=_iso(100))
        )
        assert context(run(source="compact", project_dir=proj)) is None

    def test_no_operations_silent(self, tmp_path):
        proj = make_project(tmp_path, ops_body=None)  # no OPERATIONS.md present
        r = run(project_dir=proj)
        assert r.returncode == 0
        assert context(r) is None

    def test_skip_env_silent_and_audited(self, tmp_path):
        proj = make_project(tmp_path, ops_body=_ops(c078=_iso(-2)))
        audit = tmp_path / "bypass.log"
        r = run(
            project_dir=proj, env={"CADENCE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)}
        )
        assert r.returncode == 0
        assert context(r) is None
        assert audit.exists() and "CADENCE_SKIP=1" in audit.read_text()

    def test_malformed_next_due_fails_toward_surfacing(self, tmp_path):
        body = "## Cadences\n### C-078. Governance Compliance Review\n**Next due:** soon.\n\n---\n"
        proj = make_project(tmp_path, ops_body=body)
        ctx = context(run(project_dir=proj))
        assert ctx is not None and "C-078" in ctx

    def test_git_fallback_when_no_due_date(self, tmp_path):
        body = "## Cadences\n### C-078. Governance Compliance Review\n**Cadence:** 10-15 days.\n\n---\n"
        proj = make_project(tmp_path, ops_body=body, git=True)
        old = _iso(-30) + "T12:00:00"
        gitenv = os.environ.copy()
        gitenv.update(
            {
                "GIT_AUTHOR_DATE": old,
                "GIT_COMMITTER_DATE": old,
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        (proj / "f.txt").write_text("x")
        subprocess.run(["git", "add", "-A"], cwd=proj, check=True, env=gitenv)
        subprocess.run(
            ["git", "commit", "-q", "-m", "compliance review #9"],
            cwd=proj,
            check=True,
            env=gitenv,
        )
        ctx = context(run(project_dir=proj))  # 30d ago, fallback window 10d => due
        assert ctx is not None and "C-078" in ctx

    def test_never_blocks(self, tmp_path):
        proj = make_project(tmp_path, ops_body=_ops(c078=_iso(-2)))
        assert run(project_dir=proj).returncode == 0

    def test_malformed_stdin_never_crashes(self, tmp_path):
        # Future dates => not due; malformed/empty/partial JSON must not crash or emit.
        proj = make_project(
            tmp_path, ops_body=_ops(c078=_iso(50), c155=_iso(100), c109=_iso(100))
        )
        e = os.environ.copy()
        for k in list(e):
            if k.startswith("CADENCE_") or k == "CLAUDE_PROJECT_DIR":
                e.pop(k)
        e["CLAUDE_PROJECT_DIR"] = str(proj)
        for bad in ["", "not json", "{"]:
            r = subprocess.run(
                ["bash", str(HOOK)],
                input=bad,
                capture_output=True,
                text=True,
                env=e,
                timeout=15,
            )
            assert r.returncode == 0
            assert r.stdout.strip() == ""


def _lib_call(snippet: str) -> str:
    script = f'source "{CADENCE_LIB}"; {snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    ).stdout.strip()


class TestCadenceLib:
    def test_days_until_future(self):
        assert _lib_call(f"days_until {_iso(10)}") == "10"

    def test_days_until_past(self):
        assert _lib_call(f"days_until {_iso(-5)}") == "-5"

    def test_days_until_malformed(self):
        assert _lib_call("days_until not-a-date") == "-99999"

    def test_next_due_parses_first_date_of_range(self, tmp_path):
        ops = tmp_path / "OPERATIONS.md"
        ops.write_text(
            "## Cadences\n### C-078. Review\n**Next due:** ~2026-06-01-2026-06-06.\n\n---\n"
        )
        assert _lib_call(f'next_due_from_operations "{ops}" C-078') == "2026-06-01"

    def test_next_due_absent_anchor(self, tmp_path):
        ops = tmp_path / "OPERATIONS.md"
        ops.write_text("## Cadences\n### C-999. X\n**Next due:** ~2026-06-01.\n\n---\n")
        assert _lib_call(f'next_due_from_operations "{ops}" C-078') == ""

    def test_next_due_section_isolation(self, tmp_path):
        # C-078 has no Next due; the parser must STOP at the section boundary and
        # not bleed into C-155's date.
        ops = tmp_path / "OPERATIONS.md"
        ops.write_text(
            "## Cadences\n### C-078. A\n**Cadence:** x.\n\n---\n"
            "### C-155. B\n**Next due:** ~2030-01-01.\n\n---\n"
        )
        assert _lib_call(f'next_due_from_operations "{ops}" C-078') == ""


def run_dream(source="startup", project_dir=None, env=None):
    payload = {"source": source}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    e = os.environ.copy()
    for k in list(e):
        if k.startswith("DREAM_CADENCE_") or k == "CLAUDE_PROJECT_DIR":
            e.pop(k)
    if project_dir is not None:
        e["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env:
        e.update(env)
    return subprocess.run(
        ["bash", str(DREAM_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=e,
        timeout=15,
    )


@pytest.mark.skipif(
    not DREAM_HOOK.exists(),
    reason="global dream hook is user-level (~/.claude/hooks); absent in CI",
)
class TestSessionStartDreamHook:
    """Covers the dream hook's own control flow (the shared lib is covered above).

    The dream hook lives at ~/.claude/hooks/session-start-dream.sh (user-level), so
    these run only where it is installed and skip in CI.
    """

    def _git_project(self, tmp_path, dream_days_ago=None):
        d = tmp_path / "proj"
        d.mkdir()
        (d / "SESSION-STATE.md").write_text("# state\n")
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        ge = os.environ.copy()
        ge.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        (d / "f.txt").write_text("x")
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=ge)
        msg = "initial commit"
        if dream_days_ago is not None:
            when = (
                date.today() - timedelta(days=dream_days_ago)
            ).isoformat() + "T12:00:00"
            ge.update({"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
            msg = "chore: apply /dream findings"
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=d, check=True, env=ge)
        return d

    def test_due_when_no_prior_dream(self, tmp_path):
        proj = self._git_project(tmp_path)  # only a non-dream commit
        ctx = context(run_dream(project_dir=proj))
        assert ctx is not None and "dream" in ctx.lower()

    def test_due_when_overdue(self, tmp_path):
        proj = self._git_project(tmp_path, dream_days_ago=30)
        assert context(run_dream(project_dir=proj)) is not None

    def test_silent_when_recent(self, tmp_path):
        proj = self._git_project(tmp_path, dream_days_ago=2)
        assert context(run_dream(project_dir=proj)) is None

    def test_compact_source_silent(self, tmp_path):
        proj = self._git_project(tmp_path)
        assert context(run_dream(source="compact", project_dir=proj)) is None

    def test_no_memory_files_silent(self, tmp_path):
        d = tmp_path / "bare"
        d.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        assert context(run_dream(project_dir=d)) is None

    def test_skip_env_audited(self, tmp_path):
        proj = self._git_project(tmp_path)
        audit = tmp_path / "b.log"
        r = run_dream(
            project_dir=proj,
            env={"DREAM_CADENCE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)},
        )
        assert r.returncode == 0 and r.stdout.strip() == ""
        assert audit.exists() and "DREAM_CADENCE_SKIP=1" in audit.read_text()

    def test_never_blocks(self, tmp_path):
        proj = self._git_project(tmp_path)
        assert run_dream(project_dir=proj).returncode == 0
