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
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "session-start-cadence.sh"
CADENCE_LIB = REPO / ".claude" / "hooks" / "lib" / "cadence.sh"
DREAM_HOOK = REPO / ".claude" / "hooks" / "session-start-dream.sh"


def _iso(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def _ops(c078=None, c155=None, c109=None, c012="2099-01-01") -> str:
    """Build an OPERATIONS.md body with the four cadence sections.

    Each arg is a 'Next due' date (YYYY-MM-DD) or None to omit the line.

    c012 defaults to a far-future date rather than None on purpose. Every other
    cadence is opt-in per test, but the hook's fallback for a cadence with no
    resolvable date is to surface it anyway ("no due date found — verify in
    OPERATIONS.md"), which is correct fail-toward behaviour and would make every
    silence assertion in this file fail. Giving C-012 an explicit not-due date
    keeps it out of the way unless a test asks for it.
    """

    def section(anchor, title, due):
        due_line = f"**Next due:** ~{due}." if due else "**Cadence:** every 10-15 days."
        return f"### {anchor}. {title}\n**Cadence:** periodic.\n{due_line}\n\n---\n"

    return (
        "# Operations\n\n## Cadences\n\n"
        + section("C-078", "Governance Compliance Review", c078)
        + section("C-155", "Feedback Loop Analysis", c155)
        + section("C-109", "Deferred-cadence audit", c109)
        + section("C-012", "Security Posture Review", c012)
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


def run(source="startup", project_dir=None, env=None, transcript_path=None):
    payload = {"source": source}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    if transcript_path is not None:
        payload["transcript_path"] = str(transcript_path)
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

    def test_due_surfaces_from_ai_context_operations(self, tmp_path):
        """Unified layout (v2.62.0): OPERATIONS.md may live in _ai-context/ —
        the hook must fall back there when the root file is absent."""
        proj = make_project(tmp_path)
        (proj / "_ai-context").mkdir()
        (proj / "_ai-context" / "OPERATIONS.md").write_text(
            _ops(c078=_iso(-2), c155=_iso(100), c109=_iso(100))
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

    def test_c012_security_posture_is_registered(self, tmp_path):
        """C-012 must be surfaced like the other three.

        Regression guard for a real gap: OPERATIONS.md defined four cadences
        while the hook registered only three, so the security-currency review
        was the one cadence that never got surfaced — and went ~24 days past
        its threshold unnoticed. Session-267.
        """
        proj = make_project(
            tmp_path,
            ops_body=_ops(
                c078=_iso(100), c155=_iso(100), c109=_iso(100), c012=_iso(-1)
            ),
        )
        ctx = context(run(project_dir=proj)) or ""
        assert "C-012" in ctx
        # and it must not fire when it is not due
        not_due_root = tmp_path / "not-due"
        not_due_root.mkdir()
        proj2 = make_project(
            not_due_root,
            ops_body=_ops(
                c078=_iso(100), c155=_iso(100), c109=_iso(100), c012=_iso(100)
            ),
        )
        assert context(run(project_dir=proj2)) is None

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
        e.pop("GIT_DIR", None)
        e.pop("GIT_WORK_TREE", None)
        e["CLAUDE_PROJECT_DIR"] = str(proj)
        # Disable canonical_snapshot — the fixture is a non-git project, but in CI
        # git can discover the enclosing repo and read its real OPERATIONS.md dates.
        e["CADENCE_CANONICAL_REF"] = "0"
        for bad in ["", "not json", "{"]:
            r = subprocess.run(
                ["bash", str(HOOK)],
                input=bad,
                capture_output=True,
                text=True,
                env=e,
                cwd=str(proj),
                timeout=15,
            )
            assert r.returncode == 0
            assert r.stdout.strip() == ""


def _lib_call(snippet: str) -> str:
    script = f'source "{CADENCE_LIB}"; {snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    ).stdout.strip()


def _git_repo_with_commits(tmp_path, commits) -> Path:
    """Build a git repo. `commits` = list of (subject, YYYY-MM-DD, body_or_None),
    applied oldest-first. Each commit rewrites file content so none is empty."""
    repo = tmp_path / "gitrepo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    for i, (subject, iso, body) in enumerate(commits):
        when = iso + "T12:00:00"
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_DATE": when,
                "GIT_COMMITTER_DATE": when,
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        (repo / "f.txt").write_text(f"content {i}")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        args = ["git", "commit", "-q", "-m", subject]
        if body:
            args += ["-m", body]
        subprocess.run(args, cwd=repo, check=True, env=env)
    return repo


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

    # --- sessions_since (activity-based dream trigger) ---

    def test_sessions_since_counts_only_newer(self, tmp_path):
        d = tmp_path / "t"
        d.mkdir()
        base = datetime.now() - timedelta(days=5)
        for i, off_h in enumerate((-2, 1, 2)):  # 1 older, 2 newer than base
            f = d / f"s{i}.jsonl"
            f.write_text("{}")
            ts = (base + timedelta(hours=off_h)).timestamp()
            os.utime(f, (ts, ts))
        since = base.strftime("%Y-%m-%d %H:%M:%S")
        assert _lib_call(f'sessions_since "{since}" "{d}"') == "2"

    def test_sessions_since_ignores_subdir_jsonl(self, tmp_path):
        d = tmp_path / "t"
        (d / "sub").mkdir(parents=True)
        (d / "top.jsonl").write_text("{}")
        (d / "sub" / "deep.jsonl").write_text("{}")  # must NOT count (-maxdepth 1)
        since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        assert _lib_call(f'sessions_since "{since}" "{d}"') == "1"

    def test_sessions_since_missing_dir_is_sentinel(self, tmp_path):
        # Unreadable/missing dir -> -1 sentinel (DISTINCT from a real 0): under the
        # activity-only trigger the hook treats -1 as "cannot assess" and stays quiet.
        missing = tmp_path / "nope"
        assert _lib_call(f'sessions_since "2020-01-01 00:00:00" "{missing}"') == "-1"

    def test_sessions_since_zero_when_none_newer(self, tmp_path):
        d = tmp_path / "t"
        d.mkdir()
        f = d / "old.jsonl"
        f.write_text("{}")
        ts = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(f, (ts, ts))
        since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        assert _lib_call(f'sessions_since "{since}" "{d}"') == "0"

    # --- last_git_date (project-cadence git fallback; BACKLOG #167) ---

    def test_last_git_date_matches_subject_token(self, tmp_path):
        # Happy path: a genuine cadence commit (token in the SUBJECT) is found.
        repo = _git_repo_with_commits(
            tmp_path, [("compliance review #9", _iso(-30), None)]
        )
        assert _lib_call(f'last_git_date "{repo}" "compliance review"') == _iso(-30)

    def test_last_git_date_ignores_token_in_commit_body(self, tmp_path):
        # Sibling of the 2026-06-21 dream-hook token-in-body bug, on the project-cadence
        # git fallback. A genuine cadence commit (token in SUBJECT) 30d back, then a LATER
        # commit that merely NAMES the token in its BODY. Full-message `git log --grep`
        # matched the later body and returned its (recent) date -> the cadence looked more
        # recent than it was -> a due nudge got suppressed on the fallback path. SUBJECT-ONLY
        # matching must keep the date at the genuine commit.
        repo = _git_repo_with_commits(
            tmp_path,
            [
                ("compliance review #9", _iso(-30), None),
                (
                    "feat(cadence): tidy the surfacer hook",  # subject: NO token
                    _iso(-1),
                    "Explains how the compliance review cadence fallback works.",  # body: token
                ),
            ],
        )
        assert _lib_call(f'last_git_date "{repo}" "compliance review"') == _iso(-30)


def run_dream(source="startup", project_dir=None, env=None, transcript_path=None):
    payload = {"source": source}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    if transcript_path is not None:
        payload["transcript_path"] = str(transcript_path)
    e = os.environ.copy()
    for k in list(e):
        if k.startswith("DREAM_") or k == "CLAUDE_PROJECT_DIR":
            e.pop(k)
    # Never let a test fire land in the REAL ~/.claude fire log — that would
    # contaminate the fired-vs-ran compliance instrument on developer machines.
    e["DREAM_FIRE_LOG"] = str(Path(tempfile.mkdtemp()) / "dream-fires.log")
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


def _seed_transcripts(tdir, n_completed, base_dt):
    """Seed `n_completed` completed-session .jsonl (mtime just after base_dt) plus a
    current in-progress session file (newest). Returns the current session's path —
    pass it to run_dream(transcript_path=...) so the hook resolves THIS dir and the
    caller's -1 (exclude-current) is exercised. Mirrors production: the current
    session's transcript lives in the same dir, is counted, then subtracted."""
    tdir.mkdir(parents=True, exist_ok=True)
    for i in range(n_completed):
        f = tdir / f"sess-{i:02d}.jsonl"
        f.write_text('{"cwd":"p"}\n')
        ts = (base_dt + timedelta(hours=i + 1)).timestamp()
        os.utime(f, (ts, ts))
    cur = tdir / "current-session.jsonl"
    cur.write_text('{"cwd":"p"}\n')  # mtime = now -> newest; counted then subtracted
    return cur


class TestSessionStartDreamHook:
    """Covers the repo-canonical dream hook's ACTIVITY-ONLY control flow.

    The hook is now repo-canonical (.claude/hooks/session-start-dream.sh, symlinked
    into ~/.claude), so these run in CI. It fires on SESSION COUNT since the last /dream
    pass (transcripts), not calendar days. The shared lib is covered by TestCadenceLib.
    """

    _ID = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def _commit(self, repo, msg, when_dt=None, body=None):
        ge = os.environ.copy()
        ge.update(self._ID)
        if when_dt is not None:
            iso = when_dt.strftime("%Y-%m-%dT%H:%M:%S")  # local, no TZ
            ge.update({"GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso})
        (repo / "f.txt").write_text(
            msg + (body or "")
        )  # unique content -> non-empty commit
        cmd = ["git", "commit", "-q", "-m", msg]
        if body is not None:
            cmd += [
                "-m",
                body,
            ]  # a second -m becomes the commit BODY (separate paragraph)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=ge)
        subprocess.run(cmd, cwd=repo, check=True, env=ge)

    def _repo(self, tmp_path):
        d = tmp_path / "proj"
        d.mkdir()
        (d / "SESSION-STATE.md").write_text("# state\n")
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        self._commit(d, "initial commit")  # non-dream
        return d

    def test_fires_at_threshold_sessions(self, tmp_path):
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", 5, base)  # 5 completed + current
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None and "5 sessions" in ctx

    def test_silent_below_threshold(self, tmp_path):
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", 3, base)  # 3 completed < 5
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_silent_at_threshold_minus_one(self, tmp_path):
        # N = 4 (4 completed + current, minus current) < 5 -> silent. Pins the exact
        # off-by-one of the current-session subtraction, between fires@5 and silent@3.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", 4, base)  # 4 completed -> N=4
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_no_prior_dream_fires(self, tmp_path):
        repo = self._repo(tmp_path)  # only a non-dream commit
        ctx = context(run_dream(project_dir=repo))
        assert ctx is not None and "no prior" in ctx.lower()

    def test_boundary_grep_ignores_dream_feature_commit(self, tmp_path):
        # A real /dream pass 6 sessions back, then a LATER commit that merely mentions
        # /dream (a feature commit). The hardened grep must keep the boundary at the
        # pass, not reset to the feature commit (which would zero the count -> silent).
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo, "feat: improve /dream cadence hook", when_dt=base + timedelta(days=1)
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None and "6 sessions" in ctx

    def test_boundary_grep_ignores_token_in_commit_body(self, tmp_path):
        # The real recurrence: the commit that INTRODUCED the /dream-pass convention
        # names the literal token in its BODY while explaining it ("...the /dream pass
        # token..."), but NOT in its subject. Full-message `git log --grep` matched that
        # body and self-reset the boundary onto the feature commit (count -> 0 -> silent).
        # The prior test above only covered a feature commit that said "/dream" WITHOUT
        # the token, so it never caught this. SUBJECT-ONLY matching must keep the boundary
        # at the genuine pass (token in subject) -> count stays 6 -> nudge fires.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo,
            "feat(dream): activity-based trigger for the cadence hook",  # subject: NO token
            when_dt=base + timedelta(days=1),
            body="Boundary read live from the last /dream pass commit; "
            "the /dream pass token is load-bearing, not cosmetic.",  # body: token present
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None and "6 sessions" in ctx

    # --- Boundary channels (session-262) -------------------------------------
    # Observed failure: two GENUINE passes were committed as "docs(memory): dream pass
    # sessions 258-260" and "docs(memory): session-261 dream pass" (2aacd37 / 7b79349,
    # both 2026-07-24). The slash-anchored pattern missed both, so the hook counted from
    # a 3-day-older boundary and injected an AUTO-RUN directive claiming 7 unmined
    # sessions that had in fact already been mined. Fix = prose channel loosened (slash
    # optional, prefix-agnostic) with PRECISION moved to a `Dream-Pass:` git trailer.

    def test_boundary_accepts_slashless_subject(self, tmp_path):
        # The exact observed FN. Slashless pass is newer than every transcript, so a
        # recognized boundary means zero sessions since -> silence.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo,
            "docs(memory): dream pass sessions 258-260 — 14 proposals applied",
            when_dt=datetime.now() + timedelta(minutes=5),
        )
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_boundary_prose_is_prefix_agnostic(self, tmp_path):
        # Real passes have shipped under other prefixes too ("chore: apply /dream
        # findings" 6effe05, "docs(session-state): ... /dream pass summary" 931d1cb),
        # so the prose channel must not be fitted to `docs(memory):`.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo,
            "chore(memory): dream pass over sessions 262-264",
            when_dt=datetime.now() + timedelta(minutes=5),
        )
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_trailer_is_authoritative_over_later_prose_mention(self, tmp_path):
        # THE FALSE-POSITIVE DIRECTION — the one loosening the prose channel reopens.
        # A memory commit ABOUT dream passes (exactly what this session writes) carries
        # the phrase in its subject. Under prose-only matching it would self-reset the
        # boundary onto itself -> count ~0 -> the cadence goes permanently silent, and
        # silence is the lossy direction (sessions accumulated during it are discarded
        # by the last-3 mining cap; cf. the ~18-session incident, LEARNING-LOG
        # 2026-06-21). Once a `Dream-Pass:` trailer exists it is authoritative, so the
        # prose mention must NOT move the boundary: count stays 6 -> fires.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(
            repo,
            "docs(memory): mine sessions 250-252",
            when_dt=base,
            body="Dream-Pass: sessions 250-252",
        )
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo,
            "docs(memory): session-262 — false dream pass fire root cause + hook fix",
            when_dt=base + timedelta(days=1),
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None and "6 sessions" in ctx

    def test_trailer_sets_boundary(self, tmp_path):
        # Positive control for the trailer channel: a trailered pass newer than every
        # transcript silences the cadence even though its SUBJECT names no token at all.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        cur = _seed_transcripts(tmp_path / "tx", 6, base)
        self._commit(
            repo,
            "docs(memory): mine recent sessions",  # subject: no token whatsoever
            when_dt=datetime.now() + timedelta(minutes=5),
            body="Dream-Pass: sessions 259-261",
        )
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_unreadable_transcript_dir_stays_silent(self, tmp_path):
        # Cannot assess activity (no calendar floor) -> quiet, never nags.
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        missing = tmp_path / "nope" / "current.jsonl"
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=missing,
                    env={"DREAM_CADENCE_SESSIONS": "5"},
                )
            )
            is None
        )

    def test_compact_source_silent(self, tmp_path):
        repo = self._repo(tmp_path)
        assert context(run_dream(source="compact", project_dir=repo)) is None

    def test_no_memory_files_silent(self, tmp_path):
        d = tmp_path / "bare"
        d.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        assert context(run_dream(project_dir=d)) is None

    def test_skip_env_audited(self, tmp_path):
        repo = self._repo(tmp_path)
        audit = tmp_path / "b.log"
        r = run_dream(
            project_dir=repo,
            env={"DREAM_CADENCE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)},
        )
        assert r.returncode == 0 and r.stdout.strip() == ""
        assert audit.exists() and "DREAM_CADENCE_SKIP=1" in audit.read_text()

    def test_never_blocks(self, tmp_path):
        repo = self._repo(tmp_path)
        assert run_dream(project_dir=repo).returncode == 0

    # --- auto-run directive (session-241: trigger structural, execution
    # advisory-directive, measured via the fired-vs-ran instrument) ---

    def _due_repo(self, tmp_path, n_completed=5):
        repo = self._repo(tmp_path)
        base = datetime.now() - timedelta(days=10)
        self._commit(repo, "docs(memory): /dream pass over sessions", when_dt=base)
        cur = _seed_transcripts(tmp_path / "tx", n_completed, base)
        return repo, cur

    def test_threshold_fire_emits_autorun_directive(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None and "5 sessions" in ctx
        assert "AUTO-RUN" in ctx
        assert "dream/procedure.md" in ctx  # points at the procedure to execute
        assert "run_in_background" in ctx  # analysis must not block the user's task
        assert "last 4 sessions" in ctx  # per-pass cap stated in the directive itself
        assert "approv" in ctx  # proposals + commit stay user-approved
        assert "natural boundary" in ctx  # Phase 3 presentation timing
        assert "/dream pass" in ctx  # pre-commit boundary re-check reference
        assert "DREAM_AUTORUN=0" in ctx  # off-switch discoverable from the directive

    def test_default_threshold_is_four_aligned_to_mining_cap(self, tmp_path):
        # Fire at >=4 (no env override) so the last-4 per-pass cap mines
        # everything that accumulated — a lower default systematically skips
        # sessions per cycle.
        repo, cur = self._due_repo(tmp_path, n_completed=4)
        ctx = context(run_dream(project_dir=repo, transcript_path=cur))
        assert ctx is not None and "4 sessions" in ctx and "AUTO-RUN" in ctx

    def test_autorun_off_reverts_to_nudge(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_AUTORUN": "0"},
            )
        )
        assert ctx is not None and "5 sessions" in ctx
        assert "Consider running /dream" in ctx
        assert "AUTO-RUN" not in ctx

    def test_no_prior_pass_stays_advisory_nudge(self, tmp_path):
        # Cold-start branch: activity unassessable -> advisory nudge, never a directive.
        repo = self._repo(tmp_path)  # only a non-dream commit
        ctx = context(run_dream(project_dir=repo))
        assert ctx is not None and "no prior" in ctx.lower()
        assert "AUTO-RUN" not in ctx

    def test_threshold_fire_logs_directive_mode(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        log = tmp_path / "dream-fires.log"
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_FIRE_LOG": str(log)},
            )
        )
        assert ctx is not None
        lines = log.read_text().strip().splitlines()
        assert len(lines) == 1
        assert str(repo) in lines[0] and "directive" in lines[0]

    def test_threshold_fire_logs_nudge_mode_when_autorun_off(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        log = tmp_path / "dream-fires.log"
        run_dream(
            project_dir=repo,
            transcript_path=cur,
            env={
                "DREAM_CADENCE_SESSIONS": "5",
                "DREAM_AUTORUN": "0",
                "DREAM_FIRE_LOG": str(log),
            },
        )
        assert "nudge" in log.read_text()

    def test_cold_start_nudge_writes_no_fire_log(self, tmp_path):
        # No-prior-pass branch is not a threshold fire — must not log.
        repo = self._repo(tmp_path)
        log = tmp_path / "dream-fires.log"
        ctx = context(run_dream(project_dir=repo, env={"DREAM_FIRE_LOG": str(log)}))
        assert ctx is not None  # nudge fired
        assert not log.exists()

    def test_dream_fire_log_capped(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        log = tmp_path / "dream-fires.log"
        log.write_text(("x" * 100 + "\n") * 1100)  # ~111KB > 100KB cap
        before = log.stat().st_size
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_FIRE_LOG": str(log)},
            )
        )
        assert ctx is not None
        assert log.stat().st_size < before

    def test_dream_log_failure_does_not_block_injection(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        unwritable = tmp_path / "no-such-dir" / "fires.log"
        r = run_dream(
            project_dir=repo,
            transcript_path=cur,
            env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_FIRE_LOG": str(unwritable)},
        )
        assert r.returncode == 0
        assert context(r) is not None  # directive still injected

    def test_below_threshold_no_fire_log(self, tmp_path):
        repo, cur = self._due_repo(tmp_path, n_completed=3)
        log = tmp_path / "dream-fires.log"
        assert (
            context(
                run_dream(
                    project_dir=repo,
                    transcript_path=cur,
                    env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_FIRE_LOG": str(log)},
                )
            )
            is None
        )
        assert not log.exists()

    # --- concurrency check (session-278): dream worktree suppresses auto-run ---

    def test_concurrent_dream_worktree_suppresses_autorun(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        wt_path = tmp_path / "sibling-wt"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/dream-other", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None
        assert "AUTO-RUN" not in ctx
        assert "another session" in ctx.lower()
        assert str(wt_path) in ctx

    def test_concurrent_dream_worktree_logs_skipped_concurrent(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        wt_path = tmp_path / "sibling-wt"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/dream-other", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        log = tmp_path / "dream-fires.log"
        run_dream(
            project_dir=repo,
            transcript_path=cur,
            env={"DREAM_CADENCE_SESSIONS": "5", "DREAM_FIRE_LOG": str(log)},
        )
        assert log.exists()
        assert "skipped-concurrent" in log.read_text()

    def test_no_dream_worktree_fires_normally(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        wt_path = tmp_path / "sibling-wt"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/feature-xyz", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None
        assert "AUTO-RUN" in ctx

    def test_dream_in_worktree_path_but_not_branch_fires_normally(self, tmp_path):
        repo, cur = self._due_repo(tmp_path)
        wt_path = tmp_path / "dream-experiment-old"
        subprocess.run(
            ["git", "worktree", "add", "-b", "wt/feature-abc", str(wt_path)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        ctx = context(
            run_dream(
                project_dir=repo,
                transcript_path=cur,
                env={"DREAM_CADENCE_SESSIONS": "5"},
            )
        )
        assert ctx is not None
        assert "AUTO-RUN" in ctx


# ======================================================================================
# ROOT RESOLUTION — divergent payload cwd vs CLAUDE_PROJECT_DIR (BACKLOG #214)
#
# These MUST set the two roots to DIFFERENT directories. Every pre-existing test in
# this file sets `payload["cwd"]` and `CLAUDE_PROJECT_DIR` to the same path, so none
# of them can observe which one the hook actually used — the precedence bug was
# invisible to the suite for as long as it existed.
# ======================================================================================


def _run_divergent(hook, payload_cwd, env_project_dir, extra_env=None):
    """Run a SessionStart hook with the two candidate roots pointing APART."""
    e = os.environ.copy()
    for k in list(e):
        if k.startswith(("CADENCE_", "DREAM_")) or k == "CLAUDE_PROJECT_DIR":
            e.pop(k)
    e["CLAUDE_PROJECT_DIR"] = str(env_project_dir)
    e["DREAM_FIRE_LOG"] = str(Path(tempfile.mkdtemp()) / "fires.log")
    if extra_env:
        e.update(extra_env)
    return subprocess.run(
        ["bash", str(hook)],
        input=json.dumps({"source": "startup", "cwd": str(payload_cwd)}),
        capture_output=True,
        text=True,
        env=e,
        timeout=20,
    )


class TestSessionRootResolution:
    """The acting checkout wins; CLAUDE_PROJECT_DIR is a last-resort fallback.

    Premise that made the old order look reasonable — "CLAUDE_PROJECT_DIR is the
    primary checkout" — is false. The dream hook's own fire log recorded it
    resolving to three different worktrees (80 firings) and the primary (23).
    """

    def test_cadence_uses_payload_cwd_not_claude_project_dir(self, tmp_path):
        acting = tmp_path / "acting"
        acting.mkdir()
        (acting / "SESSION-STATE.md").write_text("# state\n")
        (acting / "OPERATIONS.md").write_text(
            _ops(c078=_iso(30), c155=_iso(30), c109=_iso(30))
        )  # NOT due

        other = tmp_path / "other"
        other.mkdir()
        (other / "SESSION-STATE.md").write_text("# state\n")
        (other / "OPERATIONS.md").write_text(
            _ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30))
        )  # OVERDUE

        r = _run_divergent(HOOK, acting, other)
        assert context(r) is None, (
            "cadence read CLAUDE_PROJECT_DIR's overdue date instead of the acting "
            "checkout's — this is the 2026-07-12 false-fire shape"
        )

    def test_cadence_reports_due_from_the_acting_checkout(self, tmp_path):
        # Mirror image: the acting tree IS overdue while the env root is not.
        # Guards the opposite error — silently ignoring a real due date.
        acting = tmp_path / "acting"
        acting.mkdir()
        (acting / "SESSION-STATE.md").write_text("# state\n")
        (acting / "OPERATIONS.md").write_text(
            _ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30))
        )

        other = tmp_path / "other"
        other.mkdir()
        (other / "SESSION-STATE.md").write_text("# state\n")
        (other / "OPERATIONS.md").write_text(
            _ops(c078=_iso(30), c155=_iso(30), c109=_iso(30))
        )

        ctx = context(_run_divergent(HOOK, acting, other))
        assert ctx is not None and "C-078" in ctx

    def test_dream_uses_payload_cwd_not_claude_project_dir(self, tmp_path):
        # The acting checkout has no memory files -> the hook must exit silent.
        # If it followed CLAUDE_PROJECT_DIR it would find them and proceed.
        acting = tmp_path / "acting"
        acting.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        (other / "AGENTS.md").write_text("# agents\n")
        (other / "SESSION-STATE.md").write_text("# state\n")

        r = _run_divergent(DREAM_HOOK, acting, other)
        assert r.stdout.strip() == "", (
            "dream read CLAUDE_PROJECT_DIR's memory files, not the acting checkout's"
        )


class TestCadenceCanonicalRef:
    """A cadence due-date is stored in a versioned file, so it is checkout-VARIANT.

    Reading it from a named canonical ref is what makes every worktree agree —
    the property the old primary-checkout shortcut was reaching for and missing.
    """

    def _git_project(self, tmp_path, committed_ops, working_ops=None):
        d = tmp_path / "proj"
        d.mkdir()
        (d / "SESSION-STATE.md").write_text("# state\n")
        (d / "OPERATIONS.md").write_text(committed_ops)
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "ops"], cwd=d, check=True, env=env)
        if working_ops is not None:
            (d / "OPERATIONS.md").write_text(working_ops)  # dirty the working copy
        return d

    def test_canonical_ref_beats_a_dirty_working_copy(self, tmp_path):
        # Committed: not due. Working copy: overdue. The ref must win -> silence.
        d = self._git_project(
            tmp_path,
            committed_ops=_ops(c078=_iso(30), c155=_iso(30), c109=_iso(30)),
            working_ops=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30)),
        )
        assert context(run(project_dir=d)) is None

    def test_opt_out_falls_back_to_the_working_copy(self, tmp_path):
        # Same tree, ref reading disabled -> the overdue working copy is read.
        # This is what proves the previous test was silenced BY the ref and not
        # by some unrelated early exit.
        d = self._git_project(
            tmp_path,
            committed_ops=_ops(c078=_iso(30), c155=_iso(30), c109=_iso(30)),
            working_ops=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30)),
        )
        ctx = context(run(project_dir=d, env={"CADENCE_CANONICAL_REF": "0"}))
        assert ctx is not None and "C-078" in ctx

    def test_non_git_project_still_works(self, tmp_path):
        # No repo at all -> no ref to read -> working copy, no crash.
        d = make_project(
            tmp_path, ops_body=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30))
        )
        ctx = context(run(project_dir=d))
        assert ctx is not None and "C-078" in ctx


class TestTranscriptDirSlug:
    """Claude Code's slug replaces BOTH `/` and `.` — the old one replaced only `/`."""

    def _slug(self, path):
        r = subprocess.run(
            [
                "bash",
                "-c",
                f'source "{REPO}/.claude/hooks/lib/repo-root.sh"; transcript_dir_slug "{path}"',
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.stdout.strip()

    def test_worktree_path_slug_matches_claude_codes_naming(self):
        # A worktree under .claude/worktrees/ must produce the DOUBLE dash. The
        # slash-only version produced `-mcp-.claude-...`, a path that never exists,
        # so the hook read "activity unassessable" and went quiet for the wrong reason.
        got = self._slug("/Users/x/dev/proj/.claude/worktrees/session-262")
        assert got == "-Users-x-dev-proj--claude-worktrees-session-262"
        assert ".claude" not in got

    def test_plain_repo_path_unchanged_in_shape(self):
        assert self._slug("/Users/x/dev/proj") == "-Users-x-dev-proj"


class TestCanonicalRefOrdering:
    """Local `main` is the authority, `origin/main` only a fallback.

    Both are repository-invariant (refs live in the shared git dir, so both read
    identically from every worktree — verified). Local main is additionally
    FRESHER. Ordering origin/main first would re-announce a cadence that is
    already done, every session, until someone pushes — and this project asks
    before every push, so committed-but-unpushed is the normal state, not an edge
    case. Caught by code-reviewer HIGH before it left the worktree.
    """

    _ID = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def _repo_with_remote(self, tmp_path, pushed_ops, local_ops):
        env = os.environ.copy()
        env.update(self._ID)
        bare = tmp_path / "remote.git"
        subprocess.run(
            ["git", "init", "-q", "--bare", "-b", "main", str(bare)],
            check=True,
            env=env,
        )
        d = tmp_path / "proj"
        d.mkdir()
        (d / "SESSION-STATE.md").write_text("# state\n")
        (d / "OPERATIONS.md").write_text(pushed_ops)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "pushed"], cwd=d, check=True, env=env
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(bare)], cwd=d, check=True, env=env
        )
        subprocess.run(
            ["git", "push", "-q", "origin", "main"], cwd=d, check=True, env=env
        )
        # Now the local-only commit: the completed cadence that has not been pushed.
        (d / "OPERATIONS.md").write_text(local_ops)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "cadence done, unpushed"],
            cwd=d,
            check=True,
            env=env,
        )
        return d

    def test_unpushed_completion_is_respected(self, tmp_path):
        # origin/main still says OVERDUE; local main says done. Must be SILENT.
        d = self._repo_with_remote(
            tmp_path,
            pushed_ops=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30)),
            local_ops=_ops(c078=_iso(30), c155=_iso(30), c109=_iso(30)),
        )
        assert context(run(project_dir=d)) is None, (
            "read origin/main over local main — a completed-but-unpushed cadence "
            "would re-fire every session until push"
        )

    def test_origin_main_is_still_a_fallback(self, tmp_path):
        # Delete local main's ref advantage by checking out a detached branch with
        # no OPERATIONS.md; origin/main must still supply the (overdue) answer.
        env = os.environ.copy()
        env.update(self._ID)
        d = self._repo_with_remote(
            tmp_path,
            pushed_ops=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30)),
            # Differ only in a comment so the second commit is non-empty; the dates
            # are identical, so this test isolates ref AVAILABILITY, not precedence.
            local_ops=_ops(c078=_iso(-5), c155=_iso(30), c109=_iso(30))
            + "\n<!-- x -->\n",
        )
        # Rename local main away: now only origin/main can answer.
        subprocess.run(
            ["git", "branch", "-m", "main", "side"], cwd=d, check=True, env=env
        )
        ctx = context(run(project_dir=d))
        assert ctx is not None and "C-078" in ctx


class TestResolverEdgeCases:
    """Contract details that are easy to 'simplify' away later."""

    def _resolver(self, script, env=None):
        e = os.environ.copy()
        e.pop("CLAUDE_PROJECT_DIR", None)
        if env:
            e.update(env)
        return subprocess.run(
            ["bash", "-c", f'source "{REPO}/.claude/hooks/lib/repo-root.sh"; {script}'],
            capture_output=True,
            text=True,
            env=e,
            timeout=15,
        )

    def test_safe_under_set_u(self):
        # The header makes a point of the set-globals contract; pin that a `set -u`
        # caller can read both globals even when resolution takes the fallback path.
        r = self._resolver(
            'set -u; resolve_session_root ""; echo "${SESSION_ROOT}|${SESSION_ROOT_PROVENANCE}"'
        )
        assert r.returncode == 0, r.stderr
        assert "|" in r.stdout and r.stdout.split("|")[1].strip()

    def test_claude_project_dir_is_the_last_resort(self, tmp_path):
        # No payload cwd AND no usable $PWD -> the env var is finally consulted.
        target = tmp_path / "envroot"
        target.mkdir()
        r = self._resolver(
            'PWD=/nonexistent-xyz; resolve_session_root ""; echo "$SESSION_ROOT"',
            env={"CLAUDE_PROJECT_DIR": str(target)},
        )
        assert r.stdout.strip() == str(target)

    def test_never_returns_empty(self):
        # Empty root made genesis test a RELATIVE .git and risk "new project
        # detected" inside a real one.
        r = self._resolver(
            'PWD=/nonexistent-xyz; resolve_session_root ""; echo "[$SESSION_ROOT]"'
        )
        assert r.stdout.strip() != "[]"

    def test_subdirectory_normalizes_to_worktree_root(self, tmp_path):
        # payload cwd deep in the tree must resolve to the repo root, or every
        # "$ROOT/_ai-context/..." lookup below it misses.
        env = os.environ.copy()
        env.update(TestCanonicalRefOrdering._ID)
        d = tmp_path / "proj"
        (d / "src" / "deep").mkdir(parents=True)
        (d / "SESSION-STATE.md").write_text("# state\n")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "c"], cwd=d, check=True, env=env)
        r = self._resolver(
            f'resolve_session_root \'{{"cwd": "{d / "src" / "deep"}"}}\'; echo "$SESSION_ROOT"'
        )
        assert Path(r.stdout.strip()).resolve() == d.resolve()

    def test_canonical_snapshot_reports_failure_for_a_missing_path(self, tmp_path):
        env = os.environ.copy()
        env.update(TestCanonicalRefOrdering._ID)
        d = tmp_path / "proj"
        d.mkdir()
        (d / "a.txt").write_text("x\n")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "c"], cwd=d, check=True, env=env)
        dest = tmp_path / "out"
        r = self._resolver(
            f'canonical_snapshot "{d}" "nope.md" "{dest}" && echo YES || echo NO'
        )
        assert r.stdout.strip() == "NO"

    def test_canonical_snapshot_rejects_an_empty_blob(self, tmp_path):
        # An existing-but-empty canonical file must not beat a working copy that
        # has content — it would yield "no due date found" against a file with dates.
        env = os.environ.copy()
        env.update(TestCanonicalRefOrdering._ID)
        d = tmp_path / "proj"
        d.mkdir()
        (d / "OPERATIONS.md").write_text("")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "empty"], cwd=d, check=True, env=env
        )
        dest = tmp_path / "out"
        r = self._resolver(
            f'canonical_snapshot "{d}" "OPERATIONS.md" "{dest}" && echo YES || echo NO'
        )
        assert r.stdout.strip() == "NO"


class TestCountBasedWatchSurfacing:
    """`check_watch` — the RW-series arm (BACKLOG-adjacent; added 2026-08-15).

    WHY IT EXISTS. OPERATIONS.md carries two kinds of item and the hook only knew
    one. Cadences are due on a DATE; observation windows (RW-series) are due after N
    SESSIONS. RW-313 therefore appeared in no list, was surfaced by nothing, and sat
    at "0 of 3" while sessions ran and closed — its tally only moved if a session
    remembered to hand-edit the file at its own close, which is the seam this hook's
    header already documents as unreliable.

    The contract these tests pin is deliberately modest: SURFACE the watch and the
    observed transcript activity, never assert the tally. The first live run printed
    a count that matched the hand-recorded tally while being made of the wrong
    sessions (it included the session immediately before the reset, and subtracting
    the in-progress session cancelled the error out). So "reports a number" is not
    the contract; "cannot go quiet" is.
    """

    # Every cadence far-future so the only thing that can speak is the watch — a
    # cadence with no resolvable date fails toward surfacing and would otherwise
    # supply the non-silence these tests are trying to attribute to check_watch.
    _QUIET = dict(c078="2099-01-01", c155="2099-01-01", c109="2099-01-01")

    @staticmethod
    def _ops_with_watch(*, since="2026-08-14", anchor="RW-313", extra=""):
        return (
            _ops(**TestCountBasedWatchSurfacing._QUIET, c012="2099-01-01")
            + f"### {anchor}. #313 migration rollback watch\n"
            + "**Status: 2 of 3.**\n"
            + (f"**Counting since: {since}**\n" if since else "")
            + extra
            + "\n---\n"
        )

    @staticmethod
    def _transcripts(tmp_path, n):
        """A transcript dir holding n *.jsonl files, all newer than the boundary."""
        d = tmp_path / "transcripts"
        d.mkdir()
        for i in range(n):
            (d / f"sess{i}.jsonl").write_text("{}\n")
        return d

    def test_open_watch_is_surfaced_with_the_observed_count(self, tmp_path):
        proj = make_project(tmp_path, ops_body=self._ops_with_watch())
        tdir = self._transcripts(tmp_path, 3)
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert ctx is not None, "an open watch must never be silent"
        assert "RW-313" in ctx
        # 3 transcripts minus the in-progress session = 2 observed.
        assert "~2 session(s)" in ctx, ctx
        assert "2026-08-14" in ctx

    def test_surfaces_every_session_not_only_when_the_window_fills(self, tmp_path):
        """The failure being fixed was silence, so a watch nowhere near full still
        reports. One transcript = zero observed prior sessions, and it STILL fires."""
        proj = make_project(tmp_path, ops_body=self._ops_with_watch())
        tdir = self._transcripts(tmp_path, 1)
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert ctx is not None and "RW-313" in ctx
        assert "~0 session(s)" in ctx, ctx

    def test_count_never_states_the_tally(self, tmp_path):
        """The observed count is transcript activity, not the watch's tally, and the
        message must not let a reader mistake one for the other."""
        proj = make_project(tmp_path, ops_body=self._ops_with_watch())
        tdir = self._transcripts(tmp_path, 3)
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert "approximate" in ctx, ctx
        assert "is the record, not this count" in ctx, ctx
        # The old wording; if it ever comes back, so does the false precision.
        assert "~2 of 3 sessions observed" not in ctx

    def test_full_window_asks_for_the_verdict(self, tmp_path):
        proj = make_project(tmp_path, ops_body=self._ops_with_watch())
        tdir = self._transcripts(tmp_path, 5)  # 4 observed >= window of 3
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert "window may be full" in ctx, ctx
        assert "record the verdict" in ctx, ctx

    def test_missing_section_is_silent(self, tmp_path):
        """Self-cleaning: discharge the watch by deleting its section and the
        surfacing stops on its own. This is the ONLY silent path."""
        proj = make_project(tmp_path, ops_body=_ops(**self._QUIET, c012="2099-01-01"))
        tdir = self._transcripts(tmp_path, 3)
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert ctx is None, ctx

    def test_section_without_a_start_date_surfaces_rather_than_going_quiet(
        self, tmp_path
    ):
        """Deleting or renaming the date line must not disable the surfacing
        silently — that is the original defect one level up."""
        proj = make_project(tmp_path, ops_body=self._ops_with_watch(since=None))
        tdir = self._transcripts(tmp_path, 3)
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tdir / "sess0.jsonl",
                env={"CADENCE_CANONICAL_REF": "0"},
            )
        )
        assert ctx is not None, "a dateless open watch must still be reported"
        assert "no machine-readable start date" in ctx, ctx

    def test_unreadable_transcript_dir_surfaces_as_unassessable(self, tmp_path):
        """Distinct from a real zero: the watch is still open and still reported."""
        proj = make_project(tmp_path, ops_body=self._ops_with_watch())
        ctx = context(
            run(
                project_dir=proj,
                transcript_path=tmp_path / "nope" / "sess.jsonl",
                env={
                    "CADENCE_CANONICAL_REF": "0",
                    "HOME": str(tmp_path / "empty-home"),
                },
            )
        )
        assert ctx is not None
        assert "UNASSESSABLE" in ctx, ctx
