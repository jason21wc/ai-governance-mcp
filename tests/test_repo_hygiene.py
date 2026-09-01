"""Tests for scripts/repo_hygiene.py — the computed close-out inventory (BACKLOG #200).

THE ASYMMETRY THIS CORPUS DEFENDS
---------------------------------
This is NOT a safety gate, so the FP/FN asymmetry runs the opposite way from
`test_hook_shell_scan.py`. Here:

  * A false NEGATIVE (missing a real loose end) is the whole failure this tool exists
    to prevent — 30 sessions of silent residue.
  * A false POSITIVE is worse than annoying: it is FATAL to the mechanism. A checker
    that chirps on a clean repo gets tuned out, and this repo has the scar (T-169: a
    genuinely red CI job dismissed for days behind an "expected background" label).
    A prior design of this tool measured ~260 false positives against 3 real findings
    and was cut for exactly that reason.

  So: loud when the repo is dirty, SILENT when it is clean. Both directions are pinned.

THE INVARIANT THAT PROTECTS USER WORK
-------------------------------------
The tool must NEVER emit a destructive command. `git branch --no-merged` LIED about all
three of session-250's branches — it called them unmerged when their work was fully
landed. Ancestry cannot distinguish "safe to delete" from "would destroy work", so the
tool reports EVIDENCE and the human adjudicates. `test_stale_branch_never_proposes_delete`
is the test that keeps that true.

Hermetic: real temp git repos (house convention — no git mocking), and `classify()` is
pure so every decision is tested offline with no network and no mocks.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - test-local git fixtures, fixed argv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import repo_hygiene as rh  # noqa: E402


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        }
    )
    r = subprocess.run(  # nosec B603 B607 - fixed argv, test-local
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return r.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    (r / "f.txt").write_text("one")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "init")
    return r


def _v2_journal_text(
    *,
    path: Path,
    branch: str,
    base: str,
    task_key: str,
    parallel: str = "0",
    state: str = "locked",
) -> str:
    return (
        "\n".join(
            [
                "version=2",
                "host=codex-cli",
                "lifecycle_owner=framework",
                f"path={path}",
                f"branch={branch}",
                f"base_sha={base}",
                "default_ref=main",
                f"owner_pid={os.getpid()}",
                "session_id=test-session",
                f"task_key={task_key}",
                f"parallel_task={parallel}",
                f"state={state}",
                "updated_at=2026-08-28T22:00:00Z",
            ]
        )
        + "\n"
    )


def _write_v2_journal(
    repo: Path,
    wt: Path,
    *,
    task_key: str,
    parallel: str = "0",
    state: str = "locked",
) -> Path:
    branch = _git(wt, "branch", "--show-current")
    base = _git(repo, "rev-parse", "HEAD")
    gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
    if not gitdir.is_absolute():
        gitdir = wt / gitdir
    journal = gitdir / "ai-worktree-state"
    journal.write_text(
        _v2_journal_text(
            path=wt,
            branch=branch,
            base=base,
            task_key=task_key,
            parallel=parallel,
            state=state,
        )
    )
    reason = (
        "ai-worktree-v2 host=codex-cli lifecycle=framework "
        f"branch={branch} default=main base={base} pid={os.getpid()} "
        f"task={task_key} parallel={parallel} start=2026-08-28T22:00:00Z"
    )
    _git(repo, "worktree", "lock", "--reason", reason, str(wt))
    return journal


class TestTaskCoordinationDiagnostics:
    def test_duplicate_legacy_owner_is_unknown_and_non_destructive(
        self, repo, tmp_path
    ):
        wt = tmp_path / "wt-legacy-owner"
        _git(repo, "worktree", "add", "-q", "-b", "wt/legacy-a1b2c3d4", str(wt))
        gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
        (gitdir / "ai-worktree-state").write_text(
            f"version=1\nowner_pid={os.getpid() + 100000}\nowner_pid={os.getpid()}\n"
        )

        facts = rh.collect_local_facts(repo)
        owned = next(item for item in facts["worktrees"] if item["path"] == str(wt))
        assert owned["ownership"] == "unknown"
        findings = rh.classify(facts, None)
        malformed = [f for f in findings if f.check == "malformed_worktree_journal"]
        assert len(malformed) == 1
        assert malformed[0].command is None

    def test_desktop_v2_path_mismatch_is_reported(self, repo, tmp_path):
        wt = tmp_path / "wt-desktop-path"
        _git(repo, "worktree", "add", "-q", "-b", "wt/desktop-a1b2c3d4", str(wt))
        journal = _write_v2_journal(repo, wt, task_key="slug:desktop")
        _git(repo, "worktree", "unlock", str(wt))
        text = journal.read_text()
        text = text.replace("host=codex-cli", "host=codex-desktop")
        text = text.replace(
            "lifecycle_owner=framework", "lifecycle_owner=codex-desktop"
        )
        text = text.replace(f"path={wt}", f"path={wt}-wrong")
        text = text.replace(f"owner_pid={os.getpid()}", "owner_pid=")
        journal.write_text(text)

        facts = rh.collect_local_facts(repo)
        assert facts["active_task_entries"] == []
        errors = facts["worktree_journal_errors"]
        assert len(errors) == 1
        assert errors[0]["kind"] == "lock-mismatch"

    def test_legacy_desktop_empty_owner_is_valid_compatibility(self, repo, tmp_path):
        wt = tmp_path / "wt-desktop-v1"
        _git(repo, "worktree", "add", "-q", "-b", "wt/desktop-v1-a1b2c3d4", str(wt))
        gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
        (gitdir / "ai-worktree-state").write_text(
            "version=1\n"
            "host=codex-desktop\n"
            "lifecycle_owner=codex-desktop\n"
            "owner_pid=\n"
            "default_ref=main\n"
            "state=ready\n"
        )

        facts = rh.collect_local_facts(repo)
        owned = next(item for item in facts["worktrees"] if item["path"] == str(wt))
        assert owned["journal"]["valid"] is True
        assert owned["ownership"] == "unknown"
        assert facts["worktree_journal_errors"] == []

    @pytest.mark.parametrize(
        "mutation",
        [
            "missing",
            "missing-version",
            "duplicate",
            "unknown",
            "reordered",
            "control",
            "sha41",
        ],
    )
    def test_v2_parser_rejects_structural_corruption(self, tmp_path, mutation):
        text = _v2_journal_text(
            path=tmp_path,
            branch="wt/probe-a1b2c3d4",
            base="a" * 40,
            task_key="slug:probe",
        )
        lines = text.splitlines()
        if mutation == "missing":
            lines = [line for line in lines if not line.startswith("session_id=")]
        elif mutation == "missing-version":
            lines = lines[1:]
        elif mutation == "duplicate":
            lines.insert(10, lines[9])
        elif mutation == "unknown":
            lines.insert(9, "mystery=value")
        elif mutation == "reordered":
            lines[9], lines[10] = lines[10], lines[9]
        elif mutation == "control":
            lines[9] += "\tbad"
        else:
            lines[5] = "base_sha=" + "a" * 41
        parsed = rh._parse_worktree_journal_text("\n".join(lines) + "\n")
        assert parsed["format"] == "v2"
        assert parsed["valid"] is False

    def test_duplicate_task_key_is_high_and_never_offers_removal(self, repo, tmp_path):
        for name in ("wt/same-a1b2c3d4", "wt/same-b2c3d4e5"):
            wt = tmp_path / name.replace("/", "-")
            _git(repo, "worktree", "add", "-q", "-b", name, str(wt))
            _write_v2_journal(repo, wt, task_key="slug:same")

        facts = rh.collect_local_facts(repo)
        collisions = [
            f for f in rh.classify(facts, None) if f.check == "task_key_collision"
        ]
        assert len(collisions) == 1
        assert collisions[0].severity == "high"
        assert collisions[0].command is None
        assert len(collisions[0].evidence["worktrees"]) == 2

    @pytest.mark.parametrize(
        "corruption", ["wrong-task", "extra", "duplicate", "malformed-timestamp"]
    )
    def test_v2_task_identity_requires_matching_git_lock(
        self, repo, tmp_path, corruption
    ):
        wt = tmp_path / "wt-mismatch-a1b2c3d4"
        _git(repo, "worktree", "add", "-q", "-b", "wt/mismatch-a1b2c3d4", str(wt))
        _write_v2_journal(repo, wt, task_key="slug:mismatch")
        _git(repo, "worktree", "unlock", str(wt))
        reason = (
            "ai-worktree-v2 host=codex-cli lifecycle=framework "
            f"branch=wt/mismatch-a1b2c3d4 default=main "
            f"base={_git(repo, 'rev-parse', 'HEAD')} pid={os.getpid()} "
            "task=slug:mismatch parallel=0 start=2026-08-28T22:00:00Z"
        )
        if corruption == "wrong-task":
            reason = reason.replace("task=slug:mismatch", "task=slug:other")
        elif corruption == "extra":
            reason += " extra=1"
        elif corruption == "duplicate":
            reason = reason.replace(
                " task=slug:mismatch", " task=slug:mismatch task=slug:mismatch"
            )
        else:
            reason = reason.replace("2026-08-28T22:00:00Z", "2026-08-28 22:00:00")
        _git(
            repo,
            "worktree",
            "lock",
            "--reason",
            reason,
            str(wt),
        )
        facts = rh.collect_local_facts(repo)
        assert facts["active_task_entries"] == []
        findings = rh.classify(facts, None)
        mismatch = [f for f in findings if f.check == "worktree_lifecycle_mismatch"]
        assert len(mismatch) == 1
        assert mismatch[0].command is None
        assert "does not match" in mismatch[0].title

    def test_intentional_parallel_task_is_visible_presence_not_alarm(
        self, repo, tmp_path
    ):
        for name, parallel in (
            ("wt/parallel-a1b2c3d4", "0"),
            ("wt/parallel-b2c3d4e5", "1"),
        ):
            wt = tmp_path / name.replace("/", "-")
            _git(repo, "worktree", "add", "-q", "-b", name, str(wt))
            _write_v2_journal(repo, wt, task_key="slug:parallel", parallel=parallel)

        report = rh.summarize(rh.classify(rh.collect_local_facts(repo), None), "warn")
        assert report["clean"] is True
        assert report["counts"]["presence"] == 1
        assert "Intentional parallel task 'slug:parallel'" in rh.render(
            report, network_ok=False
        )

    def test_parallel_member_cannot_hide_task_conflict(self, repo, tmp_path):
        members = (
            ("wt/conflicted-a1b2c3d4", "0", "ready"),
            ("wt/conflicted-b2c3d4e5", "0", "task-conflict"),
            ("wt/conflicted-c3d4e5f6", "1", "ready"),
        )
        for name, parallel, state in members:
            wt = tmp_path / name.replace("/", "-")
            _git(repo, "worktree", "add", "-q", "-b", name, str(wt))
            _write_v2_journal(
                repo,
                wt,
                task_key="slug:conflicted",
                parallel=parallel,
                state=state,
            )

        findings = rh.classify(rh.collect_local_facts(repo), None)
        collision = [f for f in findings if f.check == "task_key_collision"]
        assert len(collision) == 1
        assert collision[0].ref == "slug:conflicted"

    def test_legacy_derivation_never_guesses_arbitrary_hyphenated_slug(
        self, repo, tmp_path
    ):
        for name in ("wt/release-alpha", "wt/release-beta"):
            wt = tmp_path / name.replace("/", "-")
            _git(repo, "worktree", "add", "-q", "-b", name, str(wt))
        facts = rh.collect_local_facts(repo)
        assert facts["active_task_entries"] == []


# ======================================================================================
# THE CORE SAFETY INVARIANT — the tool must never be able to destroy work
# ======================================================================================


def test_stale_branch_never_proposes_delete():
    """A stale branch gets `investigate`, NEVER `delete`.

    This is the test that stands between the user and lost work. Ancestry lies (see
    test_ancestry_lies_but_evidence_does_not), so no automated verdict is trustworthy
    enough to carry a destructive command.
    """
    local = {
        "default_branch": "main",
        "branches": [{"ref": "origin/old", "short": "old", "date": _iso(60)}],
        "keep_markers": {},
    }
    findings = rh.classify(local, {"prs": []})
    stale = [f for f in findings if f.check == "stale_branch"]
    assert stale, "a 60-day-old branch with no PR must be reported"
    for f in stale:
        assert f.disposition == "investigate", (
            f"disposition was {f.disposition!r} — must be investigate"
        )
        assert f.command is None, f"a destructive command was emitted: {f.command!r}"


def test_no_branch_action_when_remote_facts_unavailable():
    """With gh down we cannot know whether a branch carries an open PR.

    Deleting the Dependabot branch would CLOSE PR #14 and Dependabot would recreate it.
    So when remote facts are unavailable, branches are not reported at all — a hard
    interlock, not a heuristic.
    """
    local = {
        "default_branch": "main",
        "branches": [{"ref": "origin/old", "short": "old", "date": _iso(60)}],
        "keep_markers": {},
    }
    findings = rh.classify(local, None)
    assert not [f for f in findings if f.check == "stale_branch"]


def test_branch_with_open_pr_is_never_reported_stale():
    """PR #14's branch looked stale and was not. Deleting it would have closed the PR."""
    local = {
        "default_branch": "main",
        "branches": [
            {"ref": "origin/dependabot/x", "short": "dependabot/x", "date": _iso(90)}
        ],
        "keep_markers": {},
    }
    remote = {
        "prs": [
            {
                "number": 14,
                "title": "bump",
                "headRefName": "dependabot/x",
                "createdAt": _iso(3) + "T00:00:00Z",
            }
        ]
    }
    findings = rh.classify(local, remote)
    assert not [f for f in findings if f.check == "stale_branch"]


# ======================================================================================
# GROUND TRUTH — ancestry lies. Pinned against two REAL commits in this repo's history.
# ======================================================================================

# The BASE side of that pinning (session-262). `ff0a0f3` is the #200 commit that
# established the two expectations below; a moving ref here makes the assertions decay
# as unrelated edits land on files the fixture branches touched. See the test docstring.
GROUND_TRUTH_BASE = "ff0a0f3"


@pytest.mark.parametrize(
    "tag,expect_substantive",
    [
        ("fixture/semantic-rank-landed", False),  # work was squash-landed: safe
        ("fixture/probe-diverged", True),  # graders were REFACTORED, not copied: unsafe
    ],
)
def test_ancestry_lies_but_evidence_does_not(tag, expect_substantive):
    """`git merge-base --is-ancestor` says UNMERGED for BOTH. Only one was safe to delete.

    That is the entire thesis. A tool trusting ancestry is useless or destructive; the
    per-file evidence layer separates them. These tags are permanent (session-250 pinned
    them because both objects were unreferenced and gc-prunable).

    BOTH SIDES of the comparison must be pinned — session-262. Only the branch side was
    (via the fixture tags); the base was the moving `main`, and `branch_evidence` compares
    each touched path's blob on the branch against that path's blob on the base. So the
    premise "this branch's work landed" silently decayed into "no one has edited those
    files since": session-261's wholly legitimate `2a0cebd` (a non-git guard added to 7
    global skills) edited `global-skills/source-review/SKILL.md`, a file the landed branch
    also touched, and the expectation flipped to substantive-divergence with no defect
    anywhere. Same family as the 2026-07-19 "Two Derived Artifacts Can Cross-Validate in
    False Equilibrium" lesson: a reference point that drifts with the thing it measures.

    Do NOT change BASE back to `main` to "keep it current" — currency is precisely the
    bug. The pin is `ff0a0f3`, the commit that ESTABLISHED these expectations (#200,
    2026-07-13), chosen for that provenance rather than for making the assertion pass;
    both parametrized cases were verified against it and against several nearby commits.
    The question this test asks is historical ("was the classifier right about these two
    branches?"), so its base belongs at the moment the question was asked.
    """
    if not (REPO / ".git").exists():
        pytest.skip("not a git checkout")

    def _resolves(ref: str) -> bool:
        return (
            subprocess.run(  # nosec B603 B607 - fixed argv
                ["git", "-C", str(REPO), "rev-parse", "--verify", "--quiet", ref],
                capture_output=True,
                check=False,
                timeout=15,
            ).returncode
            == 0
        )

    # This is a GROUND-TRUTH check against two real historical commits — it needs full
    # history + the fixture tags + a resolvable default branch. A local full checkout has
    # all three; a shallow PR CI checkout (detached HEAD, no local `main`, truncated
    # history) does not. So SKIP where the environment cannot support it rather than fail:
    # the classifier logic is exercised hermetically by the parametrized/unit tests above;
    # this one adds the real-data confirmation wherever the data is present.
    if not _resolves(f"{tag}^{{commit}}"):
        pytest.skip(f"ground-truth fixture {tag} not present in this tree")
    # Pinned, not `main` — see the docstring. A shallow PR checkout may not have this
    # commit, which is the same environment-cannot-support-it case the tag check above
    # handles, so skip rather than fail.
    base = GROUND_TRUTH_BASE
    if not _resolves(f"{base}^{{commit}}"):
        pytest.skip(f"pinned ground-truth base {base} not present in this tree")

    ev = rh.branch_evidence(REPO, tag, base)
    if ev["unique_commits"] <= 0:
        # branch_evidence could not walk the history (shallow clone / unrelated base) — the
        # environment cannot compute the comparison. Not a regression; skip.
        pytest.skip(f"{tag}: history unavailable to compute evidence vs {base}")
    assert ev["ancestry_merged"] is False, (
        "precondition: ancestry reports unmerged for both"
    )
    substantive = [
        f for f in ev["files"] if f["state"] != "same" and not rh._is_churn(f["path"])
    ]
    assert bool(substantive) is expect_substantive, (
        f"{tag}: substantive divergence={bool(substantive)}, expected {expect_substantive}. "
        "If this flips, the classifier would hand a human the wrong call on real work."
    )


# ======================================================================================
# SILENT WHEN CLEAN — a checker that chirps on a tidy repo gets tuned out (T-169)
# ======================================================================================


def test_clean_repo_produces_no_findings_and_rc0(repo):
    local = rh.collect_local_facts(repo)
    report = rh.summarize(rh.classify(local, {"prs": []}), "warn")
    assert report["clean"] is True
    assert report["counts"]["alarming"] == 0
    assert rh.render(report, network_ok=True) == ""


def test_locked_worktree_is_in_use_not_residue(repo, tmp_path):
    """A LOCKED worktree is one a running agent is using right now. Never report it.

    Live FP caught by dogfooding: this tool flagged the worktree Claude Code had just
    handed to an active subagent (pid still running, lock held). A checker that nags
    about resources you are currently using gets tuned out — the T-169 failure in
    miniature. Locked == busy, not abandoned.
    """
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "-b", "side", str(wt))
    _git(repo, "worktree", "lock", str(wt))
    facts = rh.collect_local_facts(repo)
    assert facts["worktrees"] == [], (
        f"a locked (in-use) worktree was reported: {facts['worktrees']}"
    )

    _git(repo, "worktree", "unlock", str(wt))
    facts = rh.collect_local_facts(repo)
    assert len(facts["worktrees"]) == 1, (
        "an UNLOCKED extra worktree is real residue and must be reported"
    )


def test_fresh_unpushed_commits_are_info_not_warn():
    """Per-push authorization makes "unpushed" the NORMAL steady state.

    If fresh unpushed commits alarmed, the tool's first act every morning would be to
    complain about last night — and it would be ignored by the third day.
    """
    local = {
        "default_branch": "main",
        "unpushed_commits": [{"sha": "abc1234", "date": _iso(0)}],
        "keep_markers": {},
    }
    f = [x for x in rh.classify(local, None) if x.check == "unpushed_commits"][0]
    assert f.severity == "info"
    assert rh.summarize([f], "warn")["clean"] is True, (
        "a fresh commit must not raise the alarm"
    )


def test_aged_unpushed_commits_do_warn():
    local = {
        "default_branch": "main",
        "unpushed_commits": [{"sha": "abc1234", "date": _iso(9)}],
        "keep_markers": {},
    }
    f = [x for x in rh.classify(local, None) if x.check == "unpushed_commits"][0]
    assert f.severity == "warn"


# ======================================================================================
# LOCAL-ONLY COMMITS — the n=2 work-destruction class
#
# `unpushed_commits` above measures `@{u}..HEAD`: the current checkout, against an
# upstream it must already have. Both halves of that are blind spots, and both have now
# eaten real work:
#   * session-241 `ddbb1aa` — a follow-up commit on a worktree branch, lost when the
#     worktree was removed.
#   * session-255 x3 — a user-approved reference capture, BACKLOG #206 and an index fix,
#     discarded when `EnterWorktree` re-created an existing branch name from origin/main.
#     The hygiene inventory had reported the repo clean MINUTES EARLIER, from `main`,
#     where `@{u}..HEAD` is empty by construction.
#
# The 2026-07-10 rule was advisory — "record the unpushed SHA in SESSION-STATE". It was
# followed, and failed anyway: the record was written into the SESSION-STATE on the
# at-risk branch. These tests pin the computed replacement.
# ======================================================================================


@pytest.fixture
def repo_with_remote(tmp_path: Path) -> Path:
    """A repo whose `main` is genuinely pushed to a real bare origin."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "-q", "--bare", "-b", "main")
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    (r / "f.txt").write_text("one")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "init")
    _git(r, "remote", "add", "origin", str(origin))
    _git(r, "push", "-q", "-u", "origin", "main")
    return r


def test_fully_pushed_repo_reports_no_local_only_commits(repo_with_remote):
    """SILENT when clean. The FP direction is fatal to this tool, so it is pinned first."""
    facts = rh.collect_local_facts(repo_with_remote)
    assert facts["local_only_commits"] == {}
    assert [
        f for f in rh.classify(facts, None) if f.check == "local_only_commits"
    ] == []


def test_sibling_branch_commits_are_visible_from_main(repo_with_remote):
    """THE REGRESSION TEST — reproduces the session-255 incident exactly.

    Vantage point is `main`, which is where the SessionStart hook runs. That is precisely
    where the old fact sees nothing and reports the repo clean.
    """
    r = repo_with_remote
    _git(r, "checkout", "-q", "-b", "worktree-session-255")
    (r / "g.txt").write_text("user-approved capture")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "docs(reference): capture")
    _git(r, "checkout", "-q", "main")

    facts = rh.collect_local_facts(r)
    assert facts["unpushed_commits"] == [], (
        "precondition: from main, @{u}..HEAD is empty — this is the blind spot"
    )
    assert "worktree-session-255" in facts["local_only_commits"]

    f = [x for x in rh.classify(facts, None) if x.check == "local_only_commits"][0]
    assert f.ref == "worktree-session-255"
    assert f.evidence["count"] == 1
    assert f.evidence["is_current_checkout"] is False
    assert f.evidence["tip_sha"], (
        "the recovery handle must be recorded here, computed — NOT on the branch it describes"
    )


def test_current_branch_without_upstream_is_not_invisible(repo_with_remote):
    """The second blind spot: `git log @{u}..HEAD` errors on a branch with no upstream,
    so `unpushed_commits` comes back empty and reads as 'nothing pending'. A fresh
    worktree branch is exactly that shape.
    """
    r = repo_with_remote
    _git(r, "checkout", "-q", "-b", "fresh-worktree")
    (r / "g.txt").write_text("work")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "work with no upstream")

    facts = rh.collect_local_facts(r)
    assert facts["unpushed_commits"] == [], (
        "precondition: no upstream -> the old fact is blind even on the CURRENT branch"
    )
    f = [x for x in rh.classify(facts, None) if x.check == "local_only_commits"][0]
    assert f.ref == "fresh-worktree"
    assert f.evidence["is_current_checkout"] is True


def _local(**kw):
    base = {
        "default_branch": "main",
        "current_branch": "main",
        "all_worktree_branches": ["main"],
        "keep_markers": {},
    }
    base.update(kw)
    return base


def test_current_branch_suppressed_ONLY_when_other_finding_surfaces_at_same_floor():
    """Presence-based suppression was a FALSE NEGATIVE in the destruction class.

    `unpushed_commits` is `info` for same-day commits, and the hooks run at `warn`
    (session-start) or `high` (pre-push). Suppressing merely because that finding EXISTS
    meant a current branch with an upstream and fresh commits produced one `info` finding
    and the tool reported the repo CLEAN — the session-255 shape with an upstream
    present, i.e. the case that most needed to be loud.
    """
    fresh = _local(
        unpushed_commits=[{"sha": "abc1234", "date": _iso(0)}],
        local_only_commits={"main": [{"sha": "abc1234", "date": _iso(0)}]},
    )
    findings = rh.classify(fresh, None)
    assert [f for f in findings if f.check == "unpushed_commits"][0].severity == "info"
    assert [f for f in findings if f.check == "local_only_commits"], (
        "an `info` unpushed_commits must NOT silence this check"
    )
    assert rh.summarize(findings, "warn")["clean"] is False, (
        "the session-start hook runs at the warn floor and MUST see this"
    )

    # The genuine duplicate case: the other finding already surfaces at this floor.
    aged = _local(
        unpushed_commits=[{"sha": "abc1234", "date": _iso(9)}],
        local_only_commits={"main": [{"sha": "abc1234", "date": _iso(9)}]},
    )
    assert [f for f in rh.classify(aged, None) if f.check == "local_only_commits"] == []


def test_local_only_severity_warn_fresh_high_when_stranded_or_stale():
    def sev(days: int, **kw) -> str:
        local = _local(
            local_only_commits={"side": [{"sha": "a", "date": _iso(days)}]}, **kw
        )
        return [f for f in rh.classify(local, None) if f.check == "local_only_commits"][
            0
        ].severity

    assert sev(0) == "warn", (
        "same-day work is the normal steady state — HIGH here is wallpaper"
    )
    assert sev(3, all_worktree_branches=["main", "side"]) == "warn", (
        "a live worktree IS sitting on this branch — someone is working on it"
    )
    assert sev(3) == "high", (
        "nobody is on this branch and the work survived a day — that is stranded, and "
        "HIGH is what reaches the pre-push seam (--min-severity high)"
    )
    assert (
        sev(rh.STALE_BRANCH_DAYS, all_worktree_branches=["main", "side"]) == "high"
    ), "two weeks untouched is abandoned even with a worktree attached"


def test_locked_worktree_branch_counts_as_live_not_stranded():
    """`facts["worktrees"]` deliberately DROPS locked worktrees (locked == in active use)
    and the primary. Reusing that list to answer "is anyone on this branch?" would mark
    every actively-used worktree as stranded and fire HIGH on the normal case, so a
    separate `all_worktree_branches` fact exists. This pins the two apart.
    """
    local = _local(
        local_only_commits={"wt-session-255": [{"sha": "a", "date": _iso(3)}]},
        worktrees=[],  # locked + primary filtered out, as that fact intends
        all_worktree_branches=["main", "wt-session-255"],
    )
    f = [x for x in rh.classify(local, None) if x.check == "local_only_commits"][0]
    assert f.severity == "warn" and f.evidence["stranded"] is False


def test_commits_shared_across_branches_are_reported_once():
    """`git log <br> --not --remotes` returns everything absent from remotes, NOT commits
    unique to <br>. Three worktrees cut from an unpushed main hold the SAME commits;
    per-branch reporting would triple-count the steady state and emit a push command
    putting main's work on a stray remote branch. Count inflation is FP-fatal here.
    """
    same = [{"sha": "a", "date": _iso(0)}, {"sha": "b", "date": _iso(0)}]
    local = _local(
        local_only_commits={"main": list(same), "wt-1": list(same), "wt-2": list(same)},
        all_worktree_branches=["main", "wt-1", "wt-2"],
    )
    found = [f for f in rh.classify(local, None) if f.check == "local_only_commits"]
    assert len(found) == 1, f"expected one grouped finding, got {len(found)}"
    assert sorted(found[0].evidence["branches"]) == ["main", "wt-1", "wt-2"]
    assert found[0].command == "git push origin main", (
        "push the default branch that owns the commits, not a worktree branch"
    )


def test_unscannable_branch_is_a_finding_not_silence():
    """ "The tool broke" must never render as "the repo is clean" (the T-169 class)."""
    local = _local(local_only_scan_errors=["weird-branch"])
    f = [x for x in rh.classify(local, None) if x.check == "local_only_scan_failed"]
    assert f and f[0].severity == "warn"
    assert rh.summarize(rh.classify(local, None), "warn")["clean"] is False


def test_local_only_commits_never_proposes_a_destructive_command():
    """Same invariant as stale_branch: this tool hands over evidence, never a delete.

    The denylist screens the destructive forms of `git push` specifically — an earlier
    version of this test had been copied from the branch-deletion test and screened for
    `branch -d`/`reset`, verbs that cannot appear in a push command, so it was checking
    the wrong thing. A deleting refspec (`origin :branch`, `--delete`) and a force
    refspec (`+refs/heads/x`) are the shapes that matter here.
    """
    local = _local(local_only_commits={"side": [{"sha": "a", "date": _iso(0)}]})
    f = [x for x in rh.classify(local, None) if x.check == "local_only_commits"][0]
    assert f.disposition == "push"
    assert f.command == "git push origin side", (
        "pin the exact command — a future edit must consciously restate the contract"
    )
    for bad in ("--delete", " -d ", " :", "+refs/", "--force", "-f ", "reset", "clean"):
        assert bad not in (f.command or ""), (
            f"destructive form {bad!r} in {f.command!r}"
        )


def test_repo_with_no_remote_reports_no_local_only_commits(repo):
    """Explicitly pin the guard the corpus previously only caught INCIDENTALLY.

    Without it, `--not --remotes` excludes nothing (there are no remote refs), so every
    commit reads as local-only and the tool chirps at a clean repo while advising a push
    to a remote that does not exist. Two other tests would fail if the guard regressed,
    but nothing NAMED it — so an edit to those two could silently unpin it.
    """
    facts = rh.collect_local_facts(repo)
    assert facts["local_only_commits"] == {}
    assert facts["local_only_scan_errors"] == []


def test_branch_named_like_a_path_does_not_silently_vanish(repo_with_remote):
    """A bare short name in an argv slot makes git abort `ambiguous argument` when the
    name collides with a path in the tree — and the old code read rc!=0 as "clean".
    """
    r = repo_with_remote
    (r / "scripts").mkdir()
    (r / "scripts" / "f.txt").write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "add scripts dir")
    _git(r, "branch", "scripts")
    _git(r, "checkout", "-q", "scripts")
    (r / "g.txt").write_text("work")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "work on ambiguous branch")
    _git(r, "checkout", "-q", "main")

    facts = rh.collect_local_facts(r)
    assert "scripts" in facts["local_only_commits"], (
        "a branch whose name collides with a path must still be scanned"
    )
    assert facts["local_only_scan_errors"] == []


def test_dash_leading_branch_name_cannot_make_the_tool_write_a_file(
    repo_with_remote, tmp_path
):
    """INVARIANT 1: this tool never mutates anything.

    `git log` option-parses a leading-dash argument, so a branch named
    `--output=<path>` made the scan WRITE AND TRUNCATE that file. Such a ref cannot be
    made by `git branch` (it refuses) but arrives via `git update-ref` or a `git fetch`
    refspec. Passing full `refs/heads/<name>` removes the option-parsing entirely.
    """
    victim = tmp_path / "victim.txt"
    victim.write_text("PRECIOUS DATA THAT MUST SURVIVE")
    r = repo_with_remote
    _git(r, "update-ref", f"refs/heads/--output={victim}", "HEAD")

    facts = rh.collect_local_facts(r)

    assert victim.read_text() == "PRECIOUS DATA THAT MUST SURVIVE", (
        "the read-only inventory truncated a file — Invariant 1 is falsified"
    )
    assert isinstance(facts["local_only_commits"], dict)


# ======================================================================================
# THE "KEEP" MARKER — suppressed from the alarm, NEVER from the count, and it EXPIRES
# ======================================================================================


def test_backlog_keep_line_suppresses_the_alarm(repo):
    ctx = repo / "_ai-context"
    ctx.mkdir()
    (ctx / "BACKLOG.md").write_text("#### 48. probe\nkeep: origin/old\n")
    _git(repo, "add", "-A")  # else the new file is untracked -> dirty_tree alarms
    _git(repo, "commit", "-q", "-m", "backlog")
    local = rh.collect_local_facts(repo)
    local["branches"] = [{"ref": "origin/old", "short": "old", "date": _iso(30)}]
    report = rh.summarize(rh.classify(local, {"prs": []}), "warn")
    assert report["counts"]["alarming"] == 0, (
        f"a kept branch must not alarm; got {[f['title'] for f in report['findings']]}"
    )


def test_kept_finding_still_appears_in_the_count(repo):
    """RC11 Dropped Exception: an ack that removes the item from view is a MUTE BUTTON.

    Session-239 deliberately kept worktree-session-218. If that keep had made the branch
    INVISIBLE, session-250's cleanup would never have found it and the report would have
    read green. Kept != resolved.
    """
    ctx = repo / "_ai-context"
    ctx.mkdir()
    (ctx / "BACKLOG.md").write_text("keep: origin/old\n")
    local = rh.collect_local_facts(repo)
    local["branches"] = [{"ref": "origin/old", "short": "old", "date": _iso(30)}]
    report = rh.summarize(rh.classify(local, {"prs": []}), "warn")
    assert report["counts"]["kept"] == 1, "the keep must remain visible in the count"
    assert report["kept"][0]["ref"] == "origin/old"


def test_expired_keep_re_enters_the_alarm(repo):
    """The age IS the escalation. Without expiry, "kept" is a permanent mute."""
    ctx = repo / "_ai-context"
    ctx.mkdir()
    (ctx / "BACKLOG.md").write_text("keep: origin/old\n")
    local = rh.collect_local_facts(repo)
    local["branches"] = [
        {"ref": "origin/old", "short": "old", "date": _iso(rh.KEEP_EXPIRY_DAYS + 5)}
    ]
    findings = rh.classify(local, {"prs": []})
    expired = [f for f in findings if f.check == "keep_expired"]
    assert expired, "a keep older than KEEP_EXPIRY_DAYS must re-enter the alarm"
    assert expired[0].kept is False
    assert "Still?" in expired[0].title


def test_backlog_keep_pointing_at_a_dead_ref_is_itself_a_finding(repo):
    """The keep list is self-cleaning: a marker for a ref that no longer exists is noise."""
    ctx = repo / "_ai-context"
    ctx.mkdir()
    (ctx / "BACKLOG.md").write_text("keep: origin/vanished\n")
    local = rh.collect_local_facts(repo)
    findings = rh.classify(local, {"prs": []})
    assert [
        f
        for f in findings
        if f.check == "stale_keep_marker" and f.ref == "origin/vanished"
    ]


def test_keep_marker_ignores_the_word_keep_in_prose(repo):
    """A tiny schema, not an NLP problem.

    The prior design scanned memory-file prose and measured ~260 FPs vs 3 real findings.
    Only an exact `keep: <ref>` line counts — never a mention inside a sentence.
    """
    ctx = repo / "_ai-context"
    ctx.mkdir()
    (ctx / "BACKLOG.md").write_text(
        "We should keep: this in mind and keep origin/old around maybe.\n"
        "Discussion about whether to keep the branch origin/old alive.\n"
    )
    markers = rh.read_keep_markers(repo)
    assert "origin/old" not in markers, f"prose leaked into the keep markers: {markers}"


# ======================================================================================
# EXIT-CODE CONTRACT — "the tool broke" must NEVER read as "the repo is clean" (T-169)
# ======================================================================================


def test_not_a_git_repo_is_rc3_not_rc0(tmp_path):
    assert rh.main(["--repo", str(tmp_path)]) == 3


def test_findings_are_rc1(repo):
    (repo / "dirty.txt").write_text("x")
    assert rh.main(["--repo", str(repo), "--offline"]) == 1


def test_clean_is_rc0(repo):
    assert rh.main(["--repo", str(repo), "--offline"]) == 0


def test_classify_is_pure_offline():
    """No git, no network, no filesystem — classify() is decidable from facts alone.

    This is what makes every decision above testable with zero mocking.
    """
    local = {
        "default_branch": "main",
        "branches": [{"ref": "origin/x", "short": "x", "date": _iso(90)}],
        "unpushed_tags": ["v1"],
        "keep_markers": {},
    }
    findings = rh.classify(local, {"prs": []})
    assert {f.check for f in findings} == {"stale_branch", "unpushed_tag"}


def test_offline_report_says_what_it_could_not_check(repo):
    """Degrade like post-push-ci-check.sh: report partial, NEVER silently omit a section."""
    (repo / "dirty.txt").write_text("x")
    local = rh.collect_local_facts(repo)
    report = rh.summarize(rh.classify(local, None), "warn")
    out = rh.render(report, network_ok=False)
    assert "gh unavailable" in out, (
        "a skipped section must be announced, not silently dropped"
    )


# ---------------------------------------------------------------------------
# OWNERSHIP: whose branch is it, and is the owner still alive? (session-268)
#
# These pin the three behaviours fixed after a live measurement: run from
# session-267's checkout, this tool emitted
#   [WARN] 1 commit(s) on worktree-session-268 exist on no remote
#          -> git push origin worktree-session-268
# handing one session a command to push ANOTHER live session's branch. The data
# needed to prevent that (which worktree owns which branch, and whether its lock
# names a live pid) was collected and then discarded.
# ---------------------------------------------------------------------------


def _owners(**branches):
    """worktree_owners fact: {branch: {path, pid, alive, is_acting}}."""
    return {
        b: {"path": f"/tmp/{b}", "pid": 4242, "alive": alive, "is_acting": acting}
        for b, (alive, acting) in branches.items()
    }


def test_another_live_sessions_branch_is_presence_not_your_action_item():
    """The whole point: no push command for a branch you do not own.

    A command that crosses an ownership boundary is worse than no message — it
    contradicts the standing ask-before-push rule and invites one session to
    publish another's in-flight work.
    """
    local = _local(
        current_branch="main",
        local_only_commits={"wt-268": [{"sha": "a", "date": _iso(3)}]},
        all_worktree_branches=["main", "wt-268"],
        worktree_owners=_owners(**{"wt-268": (True, False)}),
    )
    findings = rh.classify(local, None)
    pushes = [f for f in findings if f.check == "local_only_commits"]
    presence = [f for f in findings if f.check == "sibling_session_active"]

    assert not pushes, f"emitted an action item for someone else's branch: {pushes}"
    assert len(presence) == 1, "the sibling should still be announced, once"
    assert presence[0].severity == "info"
    assert presence[0].command is None, "presence must never carry a command"


def test_your_own_branch_still_gets_the_push_command():
    """The fix must not silence the case it was built to protect (session-255)."""
    local = _local(
        current_branch="wt-268",
        local_only_commits={"wt-268": [{"sha": "a", "date": _iso(3)}]},
        all_worktree_branches=["main", "wt-268"],
        worktree_owners=_owners(**{"wt-268": (True, True)}),
    )
    findings = [f for f in rh.classify(local, None) if f.check == "local_only_commits"]
    assert len(findings) == 1 and findings[0].command, (
        "your own unpushed work must still be reported with its push command"
    )


def test_branch_owned_by_a_DEAD_session_is_still_your_problem():
    """Presence requires a LIVE owner. A dead session's stranded work is exactly the
    session-255 destruction class, and must not be excused as 'someone else's'."""
    local = _local(
        current_branch="main",
        local_only_commits={"wt-dead": [{"sha": "a", "date": _iso(3)}]},
        all_worktree_branches=["main", "wt-dead"],
        worktree_owners=_owners(**{"wt-dead": (False, False)}),
    )
    findings = rh.classify(local, None)
    assert [f for f in findings if f.check == "local_only_commits"], (
        "a dead owner's unpushed commits must stay a real finding"
    )
    assert not [f for f in findings if f.check == "sibling_session_active"]


def test_presence_never_makes_the_repo_unclean_at_any_floor():
    """A busy teammate is not a defect in your tree — including at --min-severity info,
    where an info-severity finding would otherwise count as alarming."""
    local = _local(
        current_branch="main",
        local_only_commits={"wt-268": [{"sha": "a", "date": _iso(3)}]},
        all_worktree_branches=["main", "wt-268"],
        worktree_owners=_owners(**{"wt-268": (True, False)}),
    )
    findings = rh.classify(local, None)
    for floor in ("info", "warn", "high"):
        rep = rh.summarize(findings, floor)
        assert rep["clean"] is True, f"presence made the repo unclean at floor={floor}"
        assert rep["counts"]["presence"] == 1
    assert "Another session is working here" in rh.render(
        rh.summarize(findings, "warn"), network_ok=True
    ), "the neutral line must survive the threshold the session-start hook uses"


def test_dead_lock_owner_is_residue_not_in_use(repo, tmp_path):
    """A lock is a LIVE-PROCESS claim that outlives the process.

    Discarding the lock reason meant a finished session's worktree stayed exempt
    from the orphan check forever — the inverse of the FP the exemption fixed, and
    invisible in both directions.
    """
    wt = tmp_path / "wt-dead"
    _git(repo, "worktree", "add", "-q", "-b", "abandoned", str(wt))
    dead = _a_dead_pid()
    _git(
        repo,
        "worktree",
        "lock",
        str(wt),
        "--reason",
        f"claude session s-999 (pid {dead} start Mon Jul 27 00:00:00 2026)",
    )
    facts = rh.collect_local_facts(repo)
    assert len(facts["worktrees"]) == 1, (
        "a lock naming a DEAD pid must not exempt the worktree from the orphan check"
    )

    _git(repo, "worktree", "unlock", str(wt))
    _git(
        repo,
        "worktree",
        "lock",
        str(wt),
        "--reason",
        f"claude session s-live (pid {os.getpid()} start now)",
    )
    facts = rh.collect_local_facts(repo)
    assert facts["worktrees"] == [], (
        "a lock naming a LIVE pid must still mean in-use, not residue"
    )


def test_unparseable_lock_reason_degrades_to_ASSUME_LIVE(repo, tmp_path):
    """Degrade toward the quiet failure. Telling someone their in-use worktree is
    residue hands them `git worktree remove` for a tree another session is writing
    to; failing to nag about a stale one is merely untidy."""
    wt = tmp_path / "wt-noreason"
    _git(repo, "worktree", "add", "-q", "-b", "noreason", str(wt))
    _git(repo, "worktree", "lock", str(wt), "--reason", "held by something")
    facts = rh.collect_local_facts(repo)
    assert facts["worktrees"] == [], "no parseable pid must mean assume-live"
    assert rh._pid_alive(None) is True


def test_landedness_is_computed_from_the_FULL_ref_not_the_short_name(repo, tmp_path):
    """The short branch name is LOSSY and resolves to nothing for `wt/`-style names.

    `worktree list --porcelain` emits `refs/heads/wt/foo`; the display name drops the
    `wt/`. Feeding that back to `rev-list` resolves nothing, so EVERY worktree in a
    project that namespaces its branches would read as "landedness undetermined".
    That fails SAFE — the command is withheld either way — which is exactly why it
    would never have been noticed: nothing looks broken, the gate just stops
    discriminating. Caught while writing the gate, 2026-08-23.
    """
    wt = tmp_path / "wt-slashed"
    _git(repo, "worktree", "add", "-q", "-b", "wt/slashed", str(wt))
    (wt / "new.txt").write_text("work that never landed")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "unlanded work")
    _git(
        repo,
        "worktree",
        "lock",
        str(wt),
        "--reason",
        f"claude session s-1 (pid {_a_dead_pid()} start now)",
    )

    facts = rh.collect_local_facts(repo)
    assert len(facts["worktrees"]) == 1
    w = facts["worktrees"][0]
    assert w["branch_ref"] == "refs/heads/wt/slashed", "the full ref must be preserved"
    assert w["branch"] == "slashed", "the short name stays lossy on purpose"
    assert w["unlanded_commits"] == 1, (
        "one commit is ahead of main and the gate must SEE it, not report -1"
    )

    findings = [f for f in rh.classify(facts, None) if f.check == "stale_worktree"]
    assert findings[0].command is None
    assert "never landed" in findings[0].title


def test_landedness_scan_cannot_be_TURNED_INTO_A_FILE_WRITE(repo, tmp_path):
    """Invariant 1: this tool NEVER mutates. A base name in an argv slot broke that.

    `default_branch()` returns a SHORT name read off the `origin/HEAD` symref target,
    and git OPTION-PARSES a leading-dash argument. Pointing `origin/HEAD` at a ref named
    `--output=PWNED` made the landedness scan write `<repo>/PWNED` — a read-only
    inventory tool creating and truncating an arbitrary file. Reproduced 2026-08-23
    against the first version of this gate; the pre-gate file did not write it, so the
    gate introduced it.

    The trailing `--` does NOT cover this: it closes pathspec parsing, not option
    parsing of an earlier argument. The fix is that every candidate ref is `refs/`-
    prefixed and verified to exist, so none can begin with `-`.

    Second-order, and the reason this is not merely cosmetic: git swallowed `--not` as
    part of the injected option, so the exclusion vanished and the count came back
    WRONG rather than failing safe.
    """
    wt = tmp_path / "wt-inj"
    _git(repo, "worktree", "add", "-q", "-b", "wt/inj", str(wt))
    _git(repo, "update-ref", "refs/remotes/origin/--output=PWNED", "HEAD")
    _git(
        repo,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/--output=PWNED",
    )
    assert rh.default_branch(repo) == "--output=PWNED", (
        "fixture must reproduce the name"
    )

    rh.collect_local_facts(repo)

    assert not (repo / "PWNED").exists(), (
        "the landedness scan wrote a file — Invariant 1 (never mutates) is broken"
    )
    # And the resolver must never hand back a bare, dash-leading name.
    ref = rh.resolve_base_ref(repo, rh.default_branch(repo))
    assert ref is None or ref.startswith("refs/"), (
        "a base ref that can begin with '-' is an option-injection slot"
    )


def test_landedness_is_not_MUTED_on_a_repo_without_origin_HEAD(repo, tmp_path):
    """`default_branch()` falls back to the literal "main". That mutes the whole gate.

    Any remote-less repo — and any `master` repo — gets `"main"`, which resolves to
    nothing, so `rev-list` fails and EVERY worktree reads -1 ("undetermined"). The
    command is then withheld always, and it degrades silently because -1 looks like an
    ordinary safe outcome. That is the mute-button failure: a gate that stops
    discriminating without ever reporting that it has.

    This repo is on `master` with no remote and the work IS merged, so the gate must
    resolve `refs/heads/master` and read 0 — not -1.
    """
    _git(repo, "branch", "-m", "main", "master")
    wt = tmp_path / "wt-m"
    _git(repo, "worktree", "add", "-q", "-b", "wt/m", str(wt))
    (wt / "n.txt").write_text("landed")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "landed")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge", "wt/m")
    _git(
        repo,
        "worktree",
        "lock",
        str(wt),
        "--reason",
        f"claude session s-3 (pid {_a_dead_pid()} start now)",
    )

    facts = rh.collect_local_facts(repo)
    assert rh.default_branch(repo) == "main", "fixture must reproduce the bad fallback"
    assert facts["landed_base_ref"] == "refs/heads/master", (
        "resolution must fall through to the primary checkout's own branch"
    )
    assert facts["worktrees"][0]["unlanded_commits"] == 0, (
        "merged work read as undetermined — the gate is muted on this repo shape"
    )
    # This test is about LANDEDNESS RESOLUTION, not about command emission: the
    # fixture has no cleanup.sh, and since the raw-removal fallback was deleted that
    # correctly yields no command. Assert the thing this test exists for.
    findings = [f for f in rh.classify(facts, None) if f.check == "stale_worktree"]
    assert "undetermined landedness" not in findings[0].title, (
        "the gate resolved the base and must not report itself blind"
    )
    assert findings[0].evidence["unlanded_commits"] == 0


def test_resolve_base_ref_returns_None_rather_than_GUESSING():
    """None is the safe answer and must stay the default.

    A wrongly-resolved base is the DESTRUCTIVE direction: it can read unlanded work as
    landed and license a removal command. So resolution never falls back to a branch
    merely because it exists.
    """
    import pathlib

    r = pathlib.Path("/nonexistent-repo-for-this-test")
    assert rh.resolve_base_ref(r, "main") is None
    assert rh.resolve_base_ref(r, "") is None


def test_landedness_reads_zero_once_the_work_is_merged(repo, tmp_path):
    """The gate must not be a mute button — merged work still gets its command."""
    wt = tmp_path / "wt-merged"
    _git(repo, "worktree", "add", "-q", "-b", "wt/merged", str(wt))
    (wt / "new.txt").write_text("work that landed")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "landed work")
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge", "wt/merged")
    _git(
        repo,
        "worktree",
        "lock",
        str(wt),
        "--reason",
        f"claude session s-2 (pid {_a_dead_pid()} start now)",
    )

    # The canonical gate must EXIST for a command to be offered at all, so put one
    # where collect_local_facts looks. Without this the assertion below would pass for
    # the wrong reason after the raw-fallback removal.
    gate = repo / "global-skills" / "start-worktree"
    gate.mkdir(parents=True, exist_ok=True)
    (gate / "cleanup.sh").write_text("#!/usr/bin/env bash\nexit 0\n")

    facts = rh.collect_local_facts(repo)
    w = facts["worktrees"][0]
    assert w["unlanded_commits"] == 0, "merged work must read as landed"
    assert facts["cleanup_script"], "fixture must provide the canonical gate"
    findings = [f for f in rh.classify(facts, None) if f.check == "stale_worktree"]
    assert findings[0].command is not None, (
        "withholding the command on genuinely landed work would make the gate useless"
    )
    assert findings[0].command.endswith(str(wt))
    assert "cleanup.sh" in findings[0].command, "must route through the canonical gate"
    assert "Orphan" in findings[0].title


def _a_dead_pid() -> int:
    """A pid that is definitively NOT running: spawn a process and reap it.

    A hardcoded large pid (999999) is only reliably absent on macOS, where
    `kern.maxproc` caps well below it. Linux `pid_max` defaults to 4194304, so the
    literal could name a live process and the test would flake — reading as a
    regression in the dead-owner path rather than as the fixture problem it is.
    """
    p = subprocess.Popen([sys.executable, "-c", "pass"])  # nosec B603 - fixed argv
    p.wait()
    return p.pid


def test_mixed_group_reports_YOUR_branch_and_announces_the_sibling():
    """THE REGRESSION THE FIRST FIX INTRODUCED. Suppressing per-GROUP instead of
    per-BRANCH hid your own actionable work.

    `git log <br> --not --remotes` returns everything absent from remotes, not commits
    unique to <br>, so a sibling's worktree cut from an unpushed `main` shares main's
    commit set exactly and lands in the SAME group. Short-circuiting on "any member is
    foreign" therefore dropped main's unpushed commits — a false negative in the
    work-destruction class, created by the fix for a false positive.
    """
    same = [{"sha": "a", "date": _iso(3)}]
    local = _local(
        current_branch="wt-mine",
        local_only_commits={"main": list(same), "wt-sibling": list(same)},
        all_worktree_branches=["main", "wt-sibling", "wt-mine"],
        worktree_owners=_owners(**{"wt-sibling": (True, False)}),
    )
    findings = rh.classify(local, None)
    pushes = [f for f in findings if f.check == "local_only_commits"]
    presence = [f for f in findings if f.check == "sibling_session_active"]

    assert len(presence) == 1, "the live sibling must still be announced"
    assert len(pushes) == 1, (
        "YOUR OWN main's unpushed commits must survive the sibling suppression"
    )
    assert pushes[0].command == "git push origin main"
    assert "wt-sibling" not in pushes[0].evidence["branches"], (
        "the sibling's branch must be dropped from the actionable set, not pushed"
    )


def test_unlocked_foreign_worktree_STAYS_actionable_but_is_labelled():
    """A DELIBERATE trade-off, pinned so it is not silently reversed.

    An unlocked worktree is indistinguishable from an abandoned one: a hand-run
    `git worktree add` takes no lock (AGENTS.md documents that path), and neither does
    a tree whose session died. The two errors are not symmetric —

      * treat it as a live sibling  -> stranded work goes unreported (session-255,
        the destruction class this module exists to prevent);
      * treat it as stranded        -> you may be offered a push for a branch someone
        is quietly working on (untidy, and the push is recoverable).

    So it stays actionable. What the tool CAN do honestly is say the work is not in
    your checkout, so the human decides with that in hand rather than assuming it is
    their own branch.
    """
    local = _local(
        current_branch="wt-mine",
        local_only_commits={"wt-manual": [{"sha": "a", "date": _iso(3)}]},
        all_worktree_branches=["wt-mine", "wt-manual"],
        worktree_owners={
            "wt-manual": {
                "path": "/tmp/wt-manual",
                "pid": None,
                "alive": False,
                "is_acting": False,
            }
        },
    )
    findings = [f for f in rh.classify(local, None) if f.check == "local_only_commits"]
    assert len(findings) == 1, "stranded work on an unlocked tree must stay visible"
    assert findings[0].evidence.get("other_checkout") == "/tmp/wt-manual", (
        "the human must be told this work lives in a different checkout before acting"
    )
    assert not [
        f for f in rh.classify(local, None) if f.check == "sibling_session_active"
    ], "no live owner means no presence claim — do not assert a teammate exists"


# ---------------------------------------------------------------------------
# stale_worktree: dirty vs clean split (session-278b)
# ---------------------------------------------------------------------------


def test_dirty_sibling_worktree_gets_no_removal_command():
    """THE INCIDENT THIS FIXES. Session-278b removed a worktree with ~80 lines of
    uncommitted code because this check called it "Orphan" and handed over
    `git worktree remove`. A worktree with uncommitted files is unfinished work,
    not an orphan — the tool must not suggest destroying it.
    """
    local = _local(
        worktrees=[
            {
                "path": "/tmp/wt-dirty",
                "branch": "wt/feature",
                "dirty_files": ["M src/a.py", "M src/b.py", "?? tests/test_new.py"],
            }
        ],
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert findings[0].command is None, (
        "a worktree with uncommitted files must NEVER suggest removal"
    )
    assert "uncommitted work" in findings[0].title.lower()
    assert "3 file(s)" in findings[0].title
    assert findings[0].evidence["dirty_count"] == 3
    assert findings[0].evidence["dirty_files"] == [
        "M src/a.py",
        "M src/b.py",
        "?? tests/test_new.py",
    ]
    assert findings[0].severity == "high", "unfinished work still needs attention"


def test_clean_LANDED_worktree_with_PROVED_DEAD_owner_keeps_removal_command():
    """All THREE must hold before "nothing to lose" is true: clean, dead owner, landed.

    This test previously asserted that clean + dead owner alone licensed removal, on
    the reasoning "nothing to lose". That reasoning was false and the test encoded it,
    which is why the defect survived a suite that passed — see the UNLANDED test below.
    """
    local = _local(
        worktrees=[
            {
                "path": "/tmp/wt-clean",
                "branch": "wt/done",
                "dirty_files": [],
                "ownership": "dead",
                "owner_pids": [424242],
                "unlanded_commits": 0,
            },
        ],
        cleanup_script="/repo/global-skills/start-worktree/cleanup.sh",
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert (
        findings[0].command
        == "/repo/global-skills/start-worktree/cleanup.sh /tmp/wt-clean"
    )
    assert "Orphan" in findings[0].title
    assert "uncommitted" not in findings[0].title.lower()


def test_dead_owner_with_UNLANDED_work_gets_NO_removal_command():
    """The 2026-08-23 incident, reproduced.

    A worktree was clean and its recorded owner (pid 93966) answered ESRCH, so the
    tool reported `[HIGH] Orphan worktree` and handed over `git worktree remove` —
    while the branch sat 23 commits ahead of `main`. Clean means no UNCOMMITTED files.
    It says nothing about whether the work ever landed. /all-clear names three axes —
    clean, durable, landed — and this arm was conflating the first with the third.
    """
    local = _local(
        worktrees=[
            {
                "path": "/tmp/wt-ahead",
                "branch": "wt/unlanded",
                "dirty_files": [],
                "ownership": "dead",
                "owner_pids": [93966],
                "unlanded_commits": 23,
            },
        ],
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert findings[0].command is None, (
        "work that never landed must never license a removal command"
    )
    assert "never landed" in findings[0].title
    assert "23 commit(s) not on main" in findings[0].title
    assert findings[0].evidence["unlanded_commits"] == 23
    assert findings[0].severity == "high", "unlanded work still needs attention"


def test_dead_owner_with_UNDETERMINED_landedness_gets_NO_removal_command():
    """DEGRADE TOWARD QUIET. -1 means the comparison could not be made at all.

    A worktree on a detached HEAD, or one whose rev-list failed, proves nothing about
    where its commits are. Withholding the command is untidy; attaching it on a fact we
    could not compute is the destructive direction. Absence of the key must read the
    same way — a caller that forgets to populate it must not get a removal command.
    """
    for wt in (
        {
            "path": "/tmp/wt-detached",
            "branch": None,
            "dirty_files": [],
            "ownership": "dead",
            "owner_pids": [424242],
            "unlanded_commits": -1,
        },
        {
            "path": "/tmp/wt-nokey",
            "branch": "wt/nokey",
            "dirty_files": [],
            "ownership": "dead",
            "owner_pids": [424242],
        },
    ):
        findings = [
            f
            for f in rh.classify(_local(worktrees=[wt]), None)
            if f.check == "stale_worktree"
        ]
        assert len(findings) == 1
        assert findings[0].command is None, (
            f"undetermined landedness must not license removal ({wt['path']})"
        )
        assert "undetermined landedness" in findings[0].title


def test_removal_command_routes_through_cleanup_script_when_available():
    """Prefer the canonical gate over a raw `git worktree remove`.

    repo_hygiene's facts are computed once and read later; cleanup.sh re-verifies
    ownership, durability, completeness, clean tree and irreplaceable ignored files at
    the moment the human actually runs it. Duplicating only part of that check here is
    what produced the defect the tests above pin.
    """
    wt = {
        "path": "/tmp/wt-clean",
        "branch": "wt/done",
        "dirty_files": [],
        "ownership": "dead",
        "owner_pids": [424242],
        "unlanded_commits": 0,
    }
    local = _local(worktrees=[wt], cleanup_script="/repo/global-skills/x/cleanup.sh")
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert findings[0].command == "/repo/global-skills/x/cleanup.sh /tmp/wt-clean"

    # ...and with no such script, NO command at all. See the next test.
    findings = [
        f
        for f in rh.classify(_local(worktrees=[wt]), None)
        if f.check == "stale_worktree"
    ]
    assert findings[0].command is None


def test_NO_raw_git_worktree_remove_fallback_when_the_canonical_gate_is_absent():
    """A diagnostic that cannot vouch for a destructive command must not offer one.

    This arm used to emit `git worktree remove <path>` wherever cleanup.sh was not
    present, reasoning that repo_hygiene must stay useful in any repository. The raw
    command skips execution-time ownership, durability on a remote, completeness, clean
    tree, and irreplaceable ignored files — the exact proof set whose absence produced
    the landedness defect these tests pin. Being useful in every repo is not worth
    handing over an unvetted destructive command in any of them.

    Withholding is this module's established shape: `stale_branch` never proposes
    delete, dirty gets no command, unknown ownership gets no command.

    RED BEFORE: against the previous file this asserts `command is None` and gets
    `git worktree remove /tmp/wt-orphan` instead.
    """
    local = _local(
        worktrees=[
            {
                "path": "/tmp/wt-orphan",
                "branch": "wt/done",
                "dirty_files": [],
                "ownership": "dead",
                "owner_pids": [424242],
                "unlanded_commits": 0,
            },
        ],
    )  # note: no cleanup_script key at all
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert findings[0].command is None, (
        "no canonical gate available — this must offer no removal command at all"
    )
    assert "git worktree remove" not in (findings[0].command or ""), (
        "the raw removal command must never be emitted"
    )
    # The finding is still reported, and says WHY it is offering nothing.
    assert findings[0].severity == "high"
    assert "no cleanup.sh is available" in findings[0].title


def test_clean_worktree_with_UNKNOWN_owner_gets_NO_removal_command():
    """The defect this tri-state exists for.

    A clean worktree that names no owner is not proved abandoned. This tool
    reported exactly such a checkout as `[HIGH] Orphan worktree` with
    `git worktree remove` attached while a live Codex session was writing to it.
    Nothing proved that session gone; the tree simply carried no framework lock.
    Unknown must be reported and must NOT hand over a destructive command.
    """
    local = _local(
        worktrees=[
            {"path": "/tmp/wt-mystery", "branch": "wt/who", "dirty_files": []},
        ],
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert findings[0].command is None, (
        "unknown ownership must never license `git worktree remove`"
    )
    assert "Orphan" not in findings[0].title
    assert "ownership" in findings[0].title.lower()


def test_worktree_without_dirty_field_does_not_crash_or_claim_uncommitted_work():
    """Older callers that do not supply dirty_files must not crash.

    They also must not receive a removal command: absent fields are absent
    EVIDENCE, and the whole point of the tri-state is that missing evidence is
    not proof of death. This assertion was inverted when the command was handed
    out by default; the no-crash / no-false-label intent is unchanged.
    """
    local = _local(
        worktrees=[{"path": "/tmp/wt-old", "branch": "wt/legacy"}],
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert "uncommitted work" not in findings[0].title.lower()
    assert findings[0].command is None


def test_status_failure_degrades_to_dirty_not_clean():
    """DEGRADE TOWARD QUIET, same principle as _pid_alive.

    A false 'clean' hands someone `git worktree remove` for a tree that might
    have uncommitted work — the destructive direction. A false 'dirty' only
    suppresses the removal command — untidy, not destructive.
    """
    local = _local(
        worktrees=[
            {
                "path": "/tmp/wt-broken",
                "branch": "wt/broken",
                "dirty_files": ["<status check failed>"],
            }
        ],
    )
    findings = [f for f in rh.classify(local, None) if f.check == "stale_worktree"]
    assert len(findings) == 1
    assert findings[0].command is None, (
        "a failed status check must NOT suggest removal — degrade toward quiet"
    )
    assert "uncommitted work" in findings[0].title.lower()


def test_collect_populates_dirty_files_for_sibling_worktrees(repo, tmp_path):
    """Integration: collect_local_facts checks sibling worktrees' dirty state."""
    wt = tmp_path / "wt-sibling"
    _git(repo, "worktree", "add", "-q", "-b", "sibling", str(wt))
    (wt / "new_file.py").write_text("uncommitted")

    facts = rh.collect_local_facts(repo)
    sibling = [w for w in facts["worktrees"] if w.get("branch") == "sibling"]
    assert len(sibling) == 1
    assert len(sibling[0]["dirty_files"]) > 0, (
        "dirty files in a sibling worktree must be detected"
    )


def test_collect_clean_sibling_has_empty_dirty_files(repo, tmp_path):
    """Integration: a clean sibling worktree gets an empty dirty_files list."""
    wt = tmp_path / "wt-clean"
    _git(repo, "worktree", "add", "-q", "-b", "cleansibling", str(wt))

    facts = rh.collect_local_facts(repo)
    sibling = [w for w in facts["worktrees"] if w.get("branch") == "cleansibling"]
    assert len(sibling) == 1
    assert sibling[0]["dirty_files"] == []


# ---------------------------------------------------------------------------
# dirty_tree severity depends on WHICH tree is dirty
# ---------------------------------------------------------------------------


def test_dirty_worktree_stays_warn():
    """Uncommitted work in a worktree is ordinary mid-session state.

    Firing HIGH here would make the check noise on the normal steady state —
    the false-positive class that kills a tool, and in this repo the class that
    trains use of a bypass flag which also disables the secret scanner.
    """
    local = {
        "default_branch": "main",
        "branches": [],
        "keep_markers": {},
        "dirty_files": ["src/a.py", "src/b.py"],
        "acting_is_primary": False,
    }
    f = [x for x in rh.classify(local, None) if x.check == "dirty_tree"]
    assert len(f) == 1
    assert f[0].severity == "warn", "a dirty worktree must not fire HIGH"


def test_dirty_primary_checkout_is_high():
    """Uncommitted work in the shared integration point is a different animal.

    It belongs to no branch, blocks a sibling's fast-forward merge, and can go
    live machine-wide through the global skill/hook symlinks while still
    uncommitted. All three recorded work losses in this repo have that shape.
    """
    local = {
        "default_branch": "main",
        "branches": [],
        "keep_markers": {},
        "dirty_files": ["docs/x.md"],
        "acting_is_primary": True,
    }
    f = [x for x in rh.classify(local, None) if x.check == "dirty_tree"]
    assert len(f) == 1
    assert f[0].severity == "high", (
        "a dirty PRIMARY must clear the pre-push seam's --min-severity high floor; "
        "at 'warn' the most dangerous case is the one case that seam cannot see"
    )
    assert "PRIMARY" in f[0].title, "the report must say which tree is dirty"
    assert f[0].evidence.get("acting_is_primary") is True


def test_missing_acting_is_primary_defaults_to_warn():
    """An older caller that does not supply the fact must not silently escalate.

    Fail toward the quieter verdict: a spurious HIGH on every dirty tree would
    be worse than the status quo it replaces.
    """
    local = {
        "default_branch": "main",
        "branches": [],
        "keep_markers": {},
        "dirty_files": ["x"],
    }
    f = [x for x in rh.classify(local, None) if x.check == "dirty_tree"]
    assert f[0].severity == "warn"


def test_acting_is_primary_is_true_in_the_primary_and_false_in_a_worktree(
    repo, tmp_path
):
    """The fact itself, measured against real git — not asserted from a dict.

    `classify()` is pure, so the tests above prove the DECISION. This proves the
    INPUT, which is where a wrong-tree bug would actually live.
    """
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-b", "probe-branch", str(wt))

    primary_facts = rh.collect_local_facts(repo)
    assert primary_facts["acting_is_primary"] is True, (
        "standing in the primary checkout must report acting_is_primary True"
    )

    worktree_facts = rh.collect_local_facts(wt)
    assert worktree_facts["acting_is_primary"] is False, (
        "standing in a worktree must report acting_is_primary False"
    )


# =============================================================================
# Corpus fence parity (guards the extractor's structural-boundary detection)
# =============================================================================


def test_every_governance_document_has_balanced_code_fences():
    """An unbalanced fence in documents/ silently loses units at extraction.

    `_extract_principles` / `_extract_methods` skip the whole loop body while
    `in_fence` is true, so an unclosed fence stops header detection for the rest
    of the file: no further unit is opened and the last open unit absorbs the
    remainder. That is silent LOSS — strictly worse than the over-absorption bug
    the boundary fix removed, and `_refuse_silent_narrowing` only catches it if a
    whole category empties or drops >10%.

    Fence parity is therefore a load-bearing corpus invariant. The extractor logs
    a warning, but a warning arrives after the index is already wrong; this makes
    it a gate. Raised by code review of commit 5802cf8.
    """
    import re as _re
    from pathlib import Path as _Path

    fence_re = _re.compile(r"^[ \t]*(?:```|~~~)")
    docs = _Path(__file__).parent.parent / "documents"
    offenders = []
    for md in sorted(docs.glob("*.md")):
        count = sum(1 for line in md.read_text().splitlines() if fence_re.match(line))
        if count % 2:
            offenders.append(f"{md.name}: {count} fence lines (odd)")

    assert not offenders, (
        "unbalanced code fences would silently drop units at extraction:\n  "
        + "\n  ".join(offenders)
    )


def test_main_survives_an_unknown_ownership_worktree_end_to_end(repo, tmp_path):
    """Every severity classify() emits must exist in SEVERITY_ORDER.

    `medium` did not. classify() emitted it for an unknown-ownership worktree,
    `SEVERITY_ORDER[f.severity]` raised KeyError, and main() reported
    `internal error: 'medium'` with exit 2 and ZERO findings FOR THE WHOLE REPO —
    triggered by nothing more exotic than a plain `git worktree add`.

    This runs main() as a subprocess ON PURPOSE. 41 tests call classify()
    directly and never reach the summarize() lookup that crashed, which is why a
    green suite coexisted with a tool that produced no output. It also matters
    beyond the crash: the case for cleanup.sh being permissive when no ownership
    evidence exists is "the advisory tool still surfaces it" — and the advisory
    tool was dead in exactly that state.
    """
    wt = tmp_path / "plain-wt"
    _git(repo, "worktree", "add", "-q", "-b", "plain-side", str(wt))

    result = subprocess.run(  # nosec B603 B607
        [
            sys.executable,
            str(Path(__file__).resolve().parent.parent / "scripts" / "repo_hygiene.py"),
            "--repo",
            str(repo),
            "--min-severity",
            "info",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    combined = result.stdout + result.stderr
    assert "internal error" not in combined, combined
    assert result.returncode != 2, f"rc={result.returncode}\n{combined}"
    assert "unverifiable ownership" in combined, combined
    # Unknown ownership must never carry a removal command.
    assert "git worktree remove" not in combined, combined


def test_every_severity_is_validated_at_the_object_not_by_a_grep():
    """The guard is centralised, so no call site can outrun it.

    An earlier version of this test scanned the source for `severity="..."`
    literals. Independent review pointed out it misses the two other forms that
    occur in this file — `severity=sev` from a variable, and `f.severity = ...`
    reassignment after construction — and demonstrated it by mutating an
    assignment, which the scan waved through. A literal scan is a proxy for the
    property; `Finding.__setattr__` IS the property.
    """
    good = rh.Finding(
        check="c", ref="r", severity="high", title="t", disposition="investigate"
    )
    assert good.severity == "high"

    # Construction with an unrankable severity.
    with pytest.raises(ValueError, match="SEVERITY_ORDER"):
        rh.Finding(
            check="c",
            ref="r",
            severity="critical",
            title="t",
            disposition="investigate",
        )

    # Reassignment after construction — the form a literal scan cannot see.
    with pytest.raises(ValueError, match="SEVERITY_ORDER"):
        good.severity = "urgent"

    # And every severity the module actually emits must survive that guard.
    src = (
        Path(__file__).resolve().parent.parent / "scripts" / "repo_hygiene.py"
    ).read_text(encoding="utf-8")
    emitted = set(re.findall(r'severity\s*=\s*["\'](\w+)["\']', src))
    assert emitted, "no severity literals found — did the constructor change?"
    unrankable = sorted(s for s in emitted if s not in rh.SEVERITY_ORDER)
    assert not unrankable, f"classify() can emit {unrankable}, which cannot be ranked"
