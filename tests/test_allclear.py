"""Tests for the all-clear skill — fleet-level close-out check.

Canonical location: global-skills/all-clear/allclear.sh

Follows the hermetic-git-repo fixture pattern from test_cleanup_worktree.py and
test_repo_hygiene.py. Every test builds disposable repos in tmp_path; no mocking,
no network, and the real script is executed.

WHAT THIS SUITE IS PROTECTING
-----------------------------
The tool answers one question — "is every parallel session's work in?" — and it
answers it by COMPUTING, never by recalling. The failure it exists to prevent is a
hand-written "nothing pending" that outlives the state it described. So the tests
that matter most are the ones asserting it does not go green while something is
actually outstanding, and — equally — that it CAN go green, because a check that
never passes stops being read (T-169).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "global-skills"
    / "all-clear"
    / "allclear.sh"
)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_TERMINAL_PROMPT": "0",
    # The measuring instrument must not perturb what it measures.
    # `test_run_changes_nothing` snapshots the index mtime, and a bare
    # `git status` REFRESHES the index — so the test's own two probes moved the
    # mtime and the assertion failed no matter what the script did. Pinning it
    # here means an index write observed by that test is the script's, which is
    # the property being asserted.
    "GIT_OPTIONAL_LOCKS": "0",
}


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(GIT_ENV)
    r = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return r.stdout.strip()


def _run(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(GIT_ENV)
    # GIT_OPTIONAL_LOCKS is deliberately REMOVED for the script's own environment.
    # It belongs to the test's probe calls (see GIT_ENV), and leaving it here let
    # the script inherit the property it is supposed to set for itself — with the
    # export commented out of allclear.sh, test_run_changes_nothing still passed.
    # A test that supplies the behaviour it is asserting proves nothing.
    env.pop("GIT_OPTIONAL_LOCKS", None)
    return subprocess.run(  # nosec B603 B607
        ["bash", str(SCRIPT), "--repo", str(repo), *extra],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=60,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with a real bare origin and main pushed."""
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
    _git(r, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return r


def _worktree(repo: Path, name: str = "wt/task") -> Path:
    wt = repo.parent / "worktrees" / name.replace("/", "-")
    wt.parent.mkdir(exist_ok=True)
    _git(repo, "worktree", "add", "-q", "-b", name, str(wt))
    _git(repo, "push", "-q", "-u", "origin", name)
    return wt


def _commit_in(wt: Path, body: str = "work") -> None:
    (wt / "n.txt").write_text(body)
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", f"feat: {body}")


def _write_v2_journal(
    repo: Path,
    wt: Path,
    *,
    task_key: str,
    parallel: str = "0",
    state: str = "locked",
) -> Path:
    gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
    if not gitdir.is_absolute():
        gitdir = wt / gitdir
    branch = _git(wt, "branch", "--show-current")
    base = _git(repo, "rev-parse", "HEAD")
    pid = str(os.getpid())
    journal = gitdir / "ai-worktree-state"
    journal.write_text(
        "\n".join(
            [
                "version=2",
                "host=codex-cli",
                "lifecycle_owner=framework",
                f"path={wt}",
                f"branch={branch}",
                f"base_sha={base}",
                "default_ref=main",
                f"owner_pid={pid}",
                "session_id=test-session",
                f"task_key={task_key}",
                f"parallel_task={parallel}",
                f"state={state}",
                "updated_at=2026-08-28T22:00:00Z",
            ]
        )
        + "\n"
    )
    reason = (
        "ai-worktree-v2 host=codex-cli lifecycle=framework "
        f"branch={branch} default=main base={base} pid={pid} "
        f"task={task_key} parallel={parallel} start=2026-08-28T22:00:00Z"
    )
    _git(repo, "worktree", "lock", "--reason", reason, str(wt))
    return journal


class TestScript:
    def test_exists_and_executable(self):
        assert SCRIPT.exists()
        assert os.access(SCRIPT, os.X_OK)

    def test_help_exits_zero(self, repo):
        r = _run(repo, "--help")
        assert r.returncode == 0
        assert "all clear" in r.stdout.lower()

    def test_not_a_git_repo_exits_3(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        r = _run(plain)
        assert r.returncode == 3


class TestVerdict:
    def test_clean_repo_is_all_clear(self, repo):
        """It must be POSSIBLE to go green. A check that never passes gets
        ignored, which is the failure mode this whole family guards against."""
        r = _run(repo)
        assert r.returncode == 0, r.stdout
        assert "ALL CLEAR" in r.stdout

    def test_unlanded_session_branch_blocks_all_clear(self, repo):
        wt = _worktree(repo, "wt/unlanded")
        _commit_in(wt)
        _git(wt, "push", "-q", "origin", "wt/unlanded")
        r = _run(repo)
        assert r.returncode == 1, r.stdout
        assert "wt/unlanded" in r.stdout
        assert "ALL CLEAR" not in r.stdout

    def test_dirty_worktree_blocks_all_clear(self, repo):
        wt = _worktree(repo, "wt/dirty")
        (wt / "scratch.txt").write_text("uncommitted")
        r = _run(repo)
        assert r.returncode == 1, r.stdout
        assert "DIRTY" in r.stdout

    def test_local_only_commits_reported(self, repo):
        """Committed but on no remote — still one disk. The n=2 work-destruction
        class this repo has already been bitten by twice."""
        wt = _worktree(repo, "wt/localonly")
        _commit_in(wt)  # committed, deliberately NOT pushed
        r = _run(repo)
        assert r.returncode == 1, r.stdout
        assert "NO remote" in r.stdout or "LOCAL" in r.stdout

    def test_stash_blocks_all_clear(self, repo):
        (repo / "f.txt").write_text("modified")
        _git(repo, "stash", "push", "-q", "-m", "held work")
        r = _run(repo)
        assert r.returncode == 1, r.stdout
        assert "STASH" in r.stdout

    def test_landed_branch_is_not_reported_unlanded(self, repo):
        wt = _worktree(repo, "wt/landed")
        _commit_in(wt)
        _git(repo, "push", "-q", "origin", "wt/landed:main")
        _git(repo, "fetch", "-q", "origin")
        r = _run(repo)
        # The branch is landed; the only remaining note is that its worktree can
        # now be removed — a finding, but the branch itself must not be flagged.
        assert "not in origin/main" not in r.stdout

    def test_squash_landed_not_reported_unlanded(self, repo):
        """Ancestry lies after a squash. Reporting squash-merged work as unlanded
        is the false-alarm direction, and false alarms get the tool bypassed."""
        wt = _worktree(repo, "wt/squashed")
        _commit_in(wt, body="squashed content")
        _git(wt, "push", "-q", "origin", "wt/squashed")
        (repo / "n.txt").write_text("squashed content")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "squash: feature")
        _git(repo, "push", "-q", "origin", "main")
        _git(repo, "fetch", "-q", "origin")
        r = _run(repo)
        # An `or` here would pass for the wrong reason. Assert the specific line
        # that would appear if the content arm failed.
        assert "OPEN  wt/squashed" not in r.stdout, r.stdout
        assert "not in origin/main" not in r.stdout, r.stdout


class TestPresenceNotFinding:
    def test_live_session_worktree_is_presence(self, repo):
        """A teammate mid-flight is not residue. Flagging it as one trains the
        reader to ignore the report — repo_hygiene.py made the same call."""
        wt = _worktree(repo, "wt/live")
        _git(repo, "push", "-q", "origin", "wt/live:main")
        _git(repo, "fetch", "-q", "origin")
        reason = f"claude session test (pid {os.getpid()} start 2026-01-01T00:00:00Z)"
        _git(repo, "worktree", "lock", "--reason", reason, str(wt))
        r = _run(repo)
        assert "live" in r.stdout
        assert "still live" in r.stdout


class TestTaskCoordinationDiagnostics:
    def test_duplicate_legacy_owner_is_undetermined(self, repo):
        wt = _worktree(repo, "wt/legacy-owner-a1b2c3d4")
        gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
        (gitdir / "ai-worktree-state").write_text(
            f"version=1\nowner_pid={os.getpid() + 100000}\nowner_pid={os.getpid()}\n"
        )

        result = _run(repo)
        assert result.returncode == 2, result.stdout
        assert "owner_pid must appear exactly once" in result.stdout
        assert "UNDETERMINED" in result.stdout

    def test_desktop_v2_path_mismatch_is_undetermined(self, repo):
        wt = _worktree(repo, "wt/desktop-path-a1b2c3d4")
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

        result = _run(repo)
        assert result.returncode == 2, result.stdout
        assert "Desktop v2 journal does not match" in result.stdout

    def test_legacy_desktop_empty_owner_is_not_malformed(self, repo):
        wt = _worktree(repo, "wt/desktop-v1-a1b2c3d4")
        gitdir = Path(_git(wt, "rev-parse", "--git-dir"))
        (gitdir / "ai-worktree-state").write_text(
            "version=1\n"
            "host=codex-desktop\n"
            "lifecycle_owner=codex-desktop\n"
            "owner_pid=\n"
            "default_ref=main\n"
            "state=ready\n"
        )

        result = _run(repo)
        assert "legacy journal owner_pid" not in result.stdout
        assert "UNDETERMINED" not in result.stdout

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
    def test_malformed_v2_journal_is_undetermined(self, repo, mutation):
        wt = _worktree(repo, f"wt/malformed-{mutation}-a1b2c3d4")
        journal = _write_v2_journal(repo, wt, task_key=f"slug:{mutation}")
        lines = journal.read_text().splitlines()
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
        journal.write_text("\n".join(lines) + "\n")

        result = _run(repo)
        assert result.returncode == 2, result.stdout
        assert "malformed v2 ai-worktree-state" in result.stdout
        assert "UNDETERMINED" in result.stdout

    def test_unexpected_duplicate_task_key_is_a_finding(self, repo):
        for suffix in ("a1b2c3d4", "b2c3d4e5"):
            wt = _worktree(repo, f"wt/same-{suffix}")
            _write_v2_journal(repo, wt, task_key="slug:same")
        result = _run(repo)
        assert result.returncode == 1, result.stdout
        assert "COLLISION slug:same" in result.stdout
        assert "without explicit parallel authorization" in result.stdout

    @pytest.mark.parametrize(
        "corruption", ["wrong-task", "extra", "duplicate", "malformed-timestamp"]
    )
    def test_v2_journal_lock_mismatch_is_undetermined(self, repo, corruption):
        wt = _worktree(repo, "wt/mismatch-a1b2c3d4")
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
        result = _run(repo)
        assert result.returncode == 2, result.stdout
        assert "does not match its exact ai-worktree-v2 Git lock" in result.stdout

    def test_intentional_parallel_task_is_visible_but_not_red(self, repo):
        for suffix, parallel in (("a1b2c3d4", "0"), ("b2c3d4e5", "1")):
            wt = _worktree(repo, f"wt/parallel-{suffix}")
            _write_v2_journal(repo, wt, task_key="slug:parallel", parallel=parallel)
        result = _run(repo)
        assert result.returncode == 0, result.stdout
        assert "parallel slug:parallel" in result.stdout
        assert "one baseline and 1 explicitly authorized" in result.stdout

    def test_parallel_member_cannot_hide_unresolved_task_conflict(self, repo):
        members = (
            ("a1b2c3d4", "0", "ready"),
            ("b2c3d4e5", "0", "task-conflict"),
            ("c3d4e5f6", "1", "ready"),
        )
        for suffix, parallel, state in members:
            wt = _worktree(repo, f"wt/conflicted-{suffix}")
            _write_v2_journal(
                repo,
                wt,
                task_key="slug:conflicted",
                parallel=parallel,
                state=state,
            )
        result = _run(repo)
        assert result.returncode == 1, result.stdout
        assert "COLLISION slug:conflicted" in result.stdout
        assert "state=task-conflict" in result.stdout

    def test_legacy_ambiguity_requires_generated_eight_hex_suffix(self, repo):
        _worktree(repo, "wt/legacy-a1b2c3d4")
        _worktree(repo, "wt/legacy-b2c3d4e5")
        result = _run(repo)
        assert "COLLISION slug:legacy" in result.stdout
        assert "legacy worktrees share a generated slug" in result.stdout

    def test_arbitrary_hyphenated_legacy_branches_are_never_guessed(self, repo):
        _worktree(repo, "wt/release-alpha")
        _worktree(repo, "wt/release-beta")
        result = _run(repo)
        assert "slug:release" not in result.stdout
        assert "TASK COORDINATION" not in result.stdout


class TestScopeHonesty:
    def test_foreign_remote_branch_does_not_gate_verdict(self, repo):
        """A dependabot/collaborator branch is not this fleet's work. If it gated
        the verdict, 'all clear' could never go green in a real repo."""
        wt = _worktree(repo, "feature/somebody-else")
        _commit_in(wt)
        _git(wt, "push", "-q", "origin", "feature/somebody-else")
        _git(repo, "worktree", "remove", "--force", str(wt))
        _git(repo, "branch", "-D", "feature/somebody-else")
        r = _run(repo)
        assert r.returncode == 0, r.stdout
        assert "not a session branch" in r.stdout

    def test_prefix_is_configurable(self, repo):
        wt = _worktree(repo, "feature/mine")
        _commit_in(wt)
        _git(wt, "push", "-q", "origin", "feature/mine")
        r = _run(repo, "--prefix", "feature/")
        assert r.returncode == 1, r.stdout
        assert "feature/mine" in r.stdout

    def test_missing_repo_hygiene_states_scope_not_clean(self, repo):
        """Absence of the richer script must be SAID, not silently treated as
        having checked those surfaces."""
        r = _run(repo)
        assert "scope" in r.stdout
        assert "NOT examined" in r.stdout

    def test_unresolvable_default_branch_is_undetermined(self, tmp_path):
        """A surface this tool DOES claim. Unknown merge state is not 'clear'.

        Asserts the SPECIFIC arm, not just the verdict word: `UNDETERMINED` is
        emitted for any of several unrelated causes, so a verdict-only assertion
        would still pass if this arm broke and a different one fired. Flagged in
        review 2026-08-14 as a test that could pass for the wrong reason.
        """
        r_ = tmp_path / "solo"
        r_.mkdir()
        _git(r_, "init", "-q", "-b", "trunk")
        (r_ / "f.txt").write_text("one")
        _git(r_, "add", "-A")
        _git(r_, "commit", "-q", "-m", "init")
        out = _run(r_)
        assert out.returncode == 2, out.stdout
        assert "could not resolve a default branch" in out.stdout, out.stdout
        assert "UNDETERMINED" in out.stdout


class TestGitFailureIsNotClean:
    """Reproduced 2026-08-14: git failures were coerced to benign values, so the
    tool could print ALL CLEAR having examined nothing. Four call sites had the
    shape; these pin the two that are reachable without breaking the repo."""

    def test_missing_worktree_dir_is_not_reported_clean(self, repo):
        """A worktree whose directory is gone but which is not yet pruned. The old
        code ran `git status | grep -c . || true`, got 0 from the failure, and
        printed 'clean and landed; the worktree can be removed'."""
        wt = _worktree(repo, "wt/vanished")
        _git(repo, "push", "-q", "origin", "wt/vanished:main")
        _git(repo, "fetch", "-q", "origin")
        shutil.rmtree(wt)
        r = _run(repo)
        assert "clean and landed" not in r.stdout, r.stdout
        assert "could NOT read the working tree" in r.stdout, r.stdout
        assert r.returncode == 2, r.stdout

    def test_undetermined_beats_all_clear(self, repo):
        """The verdict must never read ALL CLEAR when a check did not run."""
        wt = _worktree(repo, "wt/vanished2")
        _git(repo, "push", "-q", "origin", "wt/vanished2:main")
        _git(repo, "fetch", "-q", "origin")
        shutil.rmtree(wt)
        r = _run(repo)
        assert "ALL CLEAR" not in r.stdout, r.stdout


class TestArgumentParsing:
    """H-1, reproduced 2026-08-14: `shift 2` with one arg left returns 1 without
    shifting, and `|| true` swallowed it — the parse loop span forever with no
    output, before any git call."""

    @pytest.mark.parametrize("flag", ["--repo", "--prefix"])
    def test_flag_without_value_exits_not_hangs(self, flag):
        env = os.environ.copy()
        env.update(GIT_ENV)
        r = subprocess.run(  # nosec B603 B607
            ["bash", str(SCRIPT), flag],
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=15,  # a hang shows up here as TimeoutExpired, i.e. a failure
        )
        assert r.returncode == 2, r.stdout
        assert "requires a value" in r.stdout


class TestMemoryFreshness:
    """The skill CHECKS whether the written handoff is behind the work; it never
    writes it. Freshness is derivable (commits since the memory dir was last
    touched); whether the prose is any good is a judgment call the completion
    sequence owns. Asked for directly: "does all-clear update _ai-context so I can
    pick up where I left off?" — it does not, and it now says so out loud."""

    def _with_memory(self, repo: Path) -> None:
        mem = repo / "_ai-context"
        mem.mkdir()
        (mem / "SESSION-STATE.md").write_text("# state\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "memory")

    def test_current_memory_is_reported_ok(self, repo):
        self._with_memory(repo)
        r = _run(repo)
        assert "_ai-context is current with HEAD" in r.stdout, r.stdout

    def test_memory_behind_head_is_a_finding(self, repo):
        self._with_memory(repo)
        (repo / "code.py").write_text("print('later work')\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "work after the handoff was written")
        r = _run(repo)
        assert r.returncode == 1, r.stdout
        assert "STALE" in r.stdout, r.stdout
        assert "1 commit(s) behind HEAD" in r.stdout, r.stdout

    def test_stale_memory_does_not_block_all_clear_wrongly(self, repo):
        """Sanity in the other direction: with memory current and nothing else
        outstanding, the verdict must still be able to go green."""
        self._with_memory(repo)
        r = _run(repo)
        assert r.returncode == 0, r.stdout
        assert "ALL CLEAR" in r.stdout

    def test_absent_memory_dir_is_silently_skipped(self, repo):
        """Most repos keep no such directory. A check that fires where it does not
        apply gets tuned out (T-169)."""
        r = _run(repo)
        assert "MEMORY" not in r.stdout, r.stdout
        assert r.returncode == 0, r.stdout

    def test_memory_dir_is_configurable(self, repo):
        mem = repo / "docs-handoff"
        mem.mkdir()
        (mem / "notes.md").write_text("# notes\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "handoff")
        (repo / "code.py").write_text("x = 1\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "later work")
        r = _run(repo, "--memory", "docs-handoff")
        assert r.returncode == 1, r.stdout
        assert "docs-handoff is 1 commit(s) behind" in r.stdout, r.stdout

    def test_it_still_writes_nothing(self, repo):
        """The memory check must not tempt the tool into writing memory."""
        self._with_memory(repo)
        before = (repo / "_ai-context" / "SESSION-STATE.md").read_text()
        _run(repo)
        assert (repo / "_ai-context" / "SESSION-STATE.md").read_text() == before


class TestNeverMutates:
    def test_run_changes_nothing(self, repo):
        """The invariant that lets this be run freely: it prints commands, it
        does not execute them. Per-push authorization is a deliberate gate."""
        wt = _worktree(repo, "wt/untouched")
        _commit_in(wt)

        def snapshot():
            # Broadened after review: the original four probes could not see config
            # writes, reflog appends, or index rewrites. The last one was real —
            # `git status` refreshes the stat cache and takes index.lock, which is
            # both a mutation and a contention hazard against live sibling
            # sessions. The script now passes --no-optional-locks; this asserts it.
            return (
                _git(repo, "worktree", "list", "--porcelain"),
                _git(repo, "for-each-ref", "--format=%(refname) %(objectname)"),
                _git(repo, "status", "--porcelain"),
                _git(repo, "stash", "list"),
                _git(repo, "config", "--local", "--list"),
                _git(repo, "reflog", "--all"),
                (repo / ".git" / "index").stat().st_mtime_ns,
            )

        before = snapshot()
        _run(repo)
        assert snapshot() == before

    def test_offers_no_delete_command_for_unlanded_branch(self, repo):
        """Ancestry lies after a rebase or squash. A tool that proposes deletion
        on it is either useless or destructive — `--no-merged` once called three
        branches unmerged when every file was byte-identical to main."""
        wt = _worktree(repo, "wt/keepme")
        _commit_in(wt)
        _git(wt, "push", "-q", "origin", "wt/keepme")
        r = _run(repo)
        assert "branch -D" not in r.stdout
        assert "--delete" not in r.stdout
