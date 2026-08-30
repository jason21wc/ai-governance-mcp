"""Ownership of a worktree: who holds it, who may take it, and who may delete it.

These pin BACKLOG #349. The defect was one idea applied in four places: ownership
was inferred from the presence or absence of a single artifact, so absence of
evidence read as evidence of death.

The fix was subtraction. A contested-claim protocol used to live in prepare.sh and
was removed rather than repaired: it could not enforce anything (nothing stops a
process that never runs the script), and contention is prevented upstream anyway
because `claude-create` allocates a unique nonced path per worker. What is left is
ADVISORY evidence — the lifecycle journal, corroborated by the Git worktree lock —
read only to REFUSE, never to seize. So these tests assert refusal and its
tri-state input (live / proved-dead / unknown), not mutual exclusion; the
concurrency harnesses that pinned the deleted protocol went with it.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "global-skills"
PREPARE = SKILLS / "start-worktree" / "prepare.sh"
CLEANUP = SKILLS / "start-worktree" / "cleanup.sh"
ALLCLEAR = SKILLS / "all-clear" / "allclear.sh"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_TERMINAL_PROMPT": "0",
}


BEGIN = "# --- ai-worktree pid liveness — CANONICAL BLOCK"
END = "# --- end ai-worktree pid liveness"


def _env() -> dict:
    env = os.environ.copy()
    env.update(GIT_ENV)
    return env


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _journal(worktree: Path) -> Path:
    """The lifecycle journal — the single ownership record for a worktree."""
    gitdir = Path(_git(worktree, "rev-parse", "--git-dir"))
    if not gitdir.is_absolute():
        gitdir = worktree / gitdir
    return gitdir / "ai-worktree-state"


def _dead_pid() -> int:
    """A pid that is certainly gone: spawn, reap, reuse the number."""
    p = subprocess.Popen([sys.executable, "-c", ""])  # nosec B603
    p.wait()
    return p.pid


@pytest.fixture
def local_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    (root / "f").write_text("x\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _create_with_dead_owner(repo: Path, script: Path = PREPARE) -> Path:
    """A ready worktree whose recorded owner is already gone — the stale case."""
    r = subprocess.run(  # nosec B603 B607
        [
            "bash",
            str(script),
            "claude-create",
            "--slug",
            "demo",
            "--base",
            "HEAD",
            "--default-ref",
            "main",
            "--owner-pid",
            str(_dead_pid()),
            "--nonce",
            "n1",
            "--allow-local-only",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=_env(),
        check=False,
        timeout=60,
    )
    wt = repo / ".claude" / "worktrees" / "demo-n1"
    assert wt.is_dir(), f"setup failed: {r.stdout}\n{r.stderr}"
    return wt


def _lock_reason_pid_fn(script: Path) -> str:
    """Extract the `_lock_reason_pid` function body OUT of a shell script.

    Deriving it beats restating it: a regression in the script changes what this
    test runs, instead of leaving the test agreeing with a copy of the old code.
    """
    text = script.read_text(encoding="utf-8")
    m = re.search(r"^_lock_reason_pid\(\) \{.*?^\}", text, re.M | re.S)
    assert m, f"no _lock_reason_pid function found in {script.name}"
    return m.group(0)


def test_a_live_owner_cannot_be_displaced(local_repo: Path):
    """With a live winner, a later claimant refuses and cannot retry through it."""
    wt = _create_with_dead_owner(local_repo)
    holder = subprocess.Popen(  # nosec B603
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )
    try:
        first = subprocess.run(  # nosec B603 B607
            [
                "bash",
                str(PREPARE),
                "continue",
                "--path",
                str(wt),
                "--owner-pid",
                str(holder.pid),
            ],
            capture_output=True,
            text=True,
            cwd=str(local_repo),
            env=_env(),
            check=False,
            timeout=60,
        )
        assert first.returncode == 0 and "READY" in first.stdout, first.stdout

        other = subprocess.Popen(  # nosec B603
            [sys.executable, "-c", "import sys; sys.stdin.read()"],
            stdin=subprocess.PIPE,
        )
        try:
            second = subprocess.run(  # nosec B603 B607
                [
                    "bash",
                    str(PREPARE),
                    "continue",
                    "--path",
                    str(wt),
                    "--owner-pid",
                    str(other.pid),
                ],
                capture_output=True,
                text=True,
                cwd=str(local_repo),
                env=_env(),
                check=False,
                timeout=60,
            )
            assert second.returncode == 1, second.stdout
            assert "READY" not in second.stdout
            # Assert the DISTINCTIVE refusal, not a word several refusals share:
            # the journal's recorded owner is what turns this claimant away.
            assert f"recorded owner pid {holder.pid} is still live" in second.stdout
        finally:
            other.kill()
            other.wait()
    finally:
        holder.kill()
        holder.wait()


# --- one liveness rule, three consumers --------------------------------------


def _canonical_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index(BEGIN)
    end = text.index(END, start)
    return text[start:end]


def test_all_three_consumers_carry_a_byte_identical_liveness_rule():
    """One rule, duplicated on purpose, guarded so the copies cannot drift.

    It is duplicated rather than sourced because sync-global-skills.sh links each
    global-skills/<skill>/ directory individually and SKILLS_ONLY installs a
    subset — a cross-skill helper would be missing on a partial install and every
    consumer would break at once. Duplication is only safe with this guard.
    """
    blocks = {p.name: _canonical_block(p) for p in (PREPARE, CLEANUP, ALLCLEAR)}
    assert len(set(blocks.values())) == 1, (
        "pid-liveness blocks have drifted apart: "
        + ", ".join(f"{k} ({len(v)} chars)" for k, v in blocks.items())
    )


def _eval_pid_alive(script: Path, pid_arg: str) -> int:
    """Run just the canonical block from `script` against one argument."""
    snippet = _canonical_block(script) + f'\npid_alive "{pid_arg}"; echo "rc=$?"\n'
    r = subprocess.run(  # nosec B603 B607
        ["bash", "-c", snippet],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    m = re.search(r"rc=(\d+)", r.stdout)
    assert m, r.stdout + r.stderr
    return int(m.group(1))


@pytest.mark.parametrize("script", [PREPARE, CLEANUP, ALLCLEAR], ids=lambda p: p.name)
@pytest.mark.parametrize(
    "pid_arg",
    ["", "notanumber", "0", "1", "-5", "99999999999999999999"],
    ids=["empty", "text", "zero", "init-eperm", "negative", "overflow"],
)
def test_unknown_or_unsignalable_pid_never_reads_as_dead(script: Path, pid_arg: str):
    """Only ESRCH proves death; everything else degrades to alive.

    pid 1 is the EPERM case for a non-root test runner: the process plainly
    exists, `kill -0` still fails. Reading that as dead is the destructive
    direction — it hands out a removal command for a live tree.
    """
    assert _eval_pid_alive(script, pid_arg) == 0, (
        f"{script.name} reported PROVED DEAD for {pid_arg!r}"
    )


@pytest.mark.parametrize("script", [PREPARE, CLEANUP, ALLCLEAR], ids=lambda p: p.name)
def test_a_genuinely_gone_pid_is_proved_dead(script: Path):
    """The guard must still be able to say 'dead', or nothing is ever reclaimable."""
    assert _eval_pid_alive(script, str(_dead_pid())) == 1


# --- cleanup consults the journal, not just the lock -------------------------


def _run_cleanup(repo: Path, worktree: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 B607
        ["bash", str(CLEANUP), str(worktree), "--default-ref", "main"],
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=_env(),
        check=False,
        timeout=60,
    )


def test_matching_live_v2_owner_can_finalize_atomically(local_repo: Path):
    """Covers: FM-WORKTREE-OWNER-ACK-FINALIZE."""
    origin = local_repo.parent / "origin.git"
    origin.mkdir()
    _git(origin, "init", "-q", "--bare", "-b", "main")
    _git(local_repo, "remote", "add", "origin", str(origin))
    _git(local_repo, "push", "-q", "-u", "origin", "main")
    _git(
        local_repo,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    wt = _create_with_dead_owner(local_repo)

    resumed = subprocess.run(  # nosec B603 B607
        [
            "bash",
            str(PREPARE),
            "continue",
            "--path",
            str(wt),
            "--owner-pid",
            str(os.getpid()),
        ],
        capture_output=True,
        text=True,
        cwd=str(local_repo),
        env=_env(),
        check=False,
        timeout=60,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr

    removed = subprocess.run(  # nosec B603 B607
        [
            "bash",
            str(CLEANUP),
            str(wt),
            "--default-ref",
            "main",
            "--owner-pid",
            str(os.getpid()),
        ],
        capture_output=True,
        text=True,
        cwd=str(local_repo),
        env=_env(),
        check=False,
        timeout=60,
    )
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert "acknowledged finalization" in removed.stdout
    assert not wt.exists()


def test_unlocked_v2_worktree_fails_closed_on_missing_lock(local_repo: Path):
    """A v2 journal without its corroborating lock is invalid ownership evidence."""
    wt = _create_with_dead_owner(local_repo)
    holder = subprocess.Popen(  # nosec B603
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )
    try:
        journal = _journal(wt)
        journal.write_text(
            re.sub(
                r"^owner_pid=.*$",
                f"owner_pid={holder.pid}",
                journal.read_text(encoding="utf-8"),
                flags=re.M,
            ),
            encoding="utf-8",
        )
        _git(local_repo, "worktree", "unlock", str(wt))
        r = _run_cleanup(local_repo, wt)
        assert r.returncode == 1, r.stdout
        assert "framework v2 worktree is missing its Git lock" in r.stdout
        assert wt.is_dir(), "an unlocked but live worktree was removed"
    finally:
        holder.kill()
        holder.wait()


def test_conflicting_v2_journal_and_lock_fail_closed(local_repo: Path):
    """A v2 journal and lock must agree exactly; refuse rather than pick."""
    wt = _create_with_dead_owner(local_repo)
    journal = _journal(wt)
    other_dead = _dead_pid()
    journal.write_text(
        re.sub(
            r"^owner_pid=.*$",
            f"owner_pid={other_dead}",
            journal.read_text(encoding="utf-8"),
            flags=re.M,
        ),
        encoding="utf-8",
    )
    r = _run_cleanup(local_repo, wt)
    assert r.returncode == 1, r.stdout
    assert "Git lock does not match the journal" in r.stdout
    assert wt.is_dir()


# --- findings from the independent correctness review ------------------------


@pytest.mark.parametrize(
    "reason,expected",
    [
        # prepare.sh::framework_lock_reason writes `pid=N`.
        (
            "ai-worktree-v1 host=claude lifecycle=framework branch=wt/x "
            "default=main base=abc pid=12345 start=2026-01-01T00:00:00Z",
            12345,
        ),
        # Claude Code's native lock writes `pid N`.
        ("claude session wt/x (pid 6789 start 2026-01-01T00:00:00Z)", 6789),
    ],
    ids=["framework-equals", "claude-space"],
)
def test_lock_pid_is_extracted_from_both_reason_forms(reason: str, expected: int):
    """Every consumer must read BOTH lock-reason shapes, or a source goes dark.

    `repo_hygiene.py` matched `\\bpid\\s+(\\d+)` and `allclear.sh` matched a
    literal space, so neither could extract a pid from the framework's own
    `pid=N` reason — a `live`/`dead` decision that gates `git worktree remove`
    was reading an empty pid for exactly the worktrees this framework creates.
    Only `cleanup.sh` had it right. The byte-identical-block discipline guarded
    `pid_alive`, which never drifted; extraction, which did, was unguarded.

    THIS TEST CALLS THE SHIPPED CODE. Its first version re-inlined the Python
    regex and the sed expression, so regressing all three consumers back to
    `pid\\s+` left it green — a guard that restates the thing it guards, which
    is the defect `ref-ai-coding-derive-guards-from-source-of-truth` names and
    the one this very entry is about. Python goes through the named accessor;
    the shell expression is READ OUT OF THE SCRIPT and executed, so editing the
    script changes the test's input rather than leaving it agreeing with itself.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import repo_hygiene as rh  # noqa: PLC0415

    assert rh._parse_lock_pid(reason) == expected, "shipped python accessor"

    for script in (PREPARE, CLEANUP, ALLCLEAR):
        fn = _lock_reason_pid_fn(script)
        r = subprocess.run(  # nosec B603 B607
            ["bash", "-c", fn + '\n_lock_reason_pid "$1" || true', "_", reason],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert r.stdout.strip() == str(expected), (
            f"{script.name} extracts {r.stdout.strip()!r} from {reason!r}, "
            f"expected {expected} (function read from source)"
        )


def test_two_claimants_sharing_an_owner_pid_are_ONE_owner_by_design(local_repo: Path):
    """Documented limit, pinned so it cannot become a silent surprise.

    The owner pid IS the identity. `procedure.md` documents `--owner-pid "$PPID"`,
    so two workers under one parent share it and BOTH are granted the checkout.
    That is required — `continue` is a retry command, and a retry is a new process
    carrying the same session pid. It also means concurrent writers MUST pass
    distinct owner pids; no mutex can separate one identity from itself.
    """
    wt = _create_with_dead_owner(local_repo)
    holder = subprocess.Popen(  # nosec B603
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )
    try:
        runs = [
            subprocess.run(  # nosec B603 B607
                [
                    "bash",
                    str(PREPARE),
                    "continue",
                    "--path",
                    str(wt),
                    "--owner-pid",
                    str(holder.pid),
                ],
                capture_output=True,
                text=True,
                cwd=str(local_repo),
                env=_env(),
                check=False,
                timeout=60,
            )
            for _ in range(2)
        ]
    finally:
        holder.kill()
        holder.wait()
    assert all(r.returncode == 0 for r in runs), [r.stdout for r in runs]
    assert all("READY" in r.stdout for r in runs), (
        "a retry by the same owner must succeed; that is what re-entrancy is for"
    )


def test_two_pid_tokens_are_AMBIGUOUS_and_both_parsers_refuse(tmp_path: Path):
    """The two parsers used to disagree, and disagreement decides ownership.

    Python took the FIRST pid token in a lock reason; the shell's greedy sed took
    the LAST. One reason therefore named two different owners depending on which
    tool asked. Neither answer is defensible, so both now return nothing and the
    caller falls through to unknown — the non-destructive direction.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import repo_hygiene as rh  # noqa: PLC0415

    ambiguous = "ai-worktree-v1 pid=111 handed-off-from pid=222"
    assert rh._parse_lock_pid(ambiguous) is None

    for script in (PREPARE, CLEANUP, ALLCLEAR):
        fn = _lock_reason_pid_fn(script)
        r = subprocess.run(  # nosec B603 B607
            ["bash", "-c", fn + '\n_lock_reason_pid "$1" || true', "_", ambiguous],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert r.stdout.strip() == "", (
            f"{script.name} picked {r.stdout.strip()!r} from an ambiguous reason"
        )


def test_all_three_consumers_carry_a_byte_identical_lock_pid_parser():
    """The fourth consumer was missed, and being missed is the whole failure.

    `pid_alive` had a parity test; `_lock_reason_pid` did not. So when the
    first-vs-last ambiguity was fixed, it was fixed in the two shell scripts the
    tests happened to loop over and in the Python accessor — and `prepare.sh`,
    which was reading the pid with its own greedy sed, kept taking the LAST
    token. Nothing failed. A rule duplicated across N consumers needs a guard
    over all N, not over the N the tests already knew about.
    """
    blocks = {}
    for path in (PREPARE, CLEANUP, ALLCLEAR):
        m = re.search(
            r"^_lock_reason_pid\(\) \{.*?^\}",
            path.read_text(encoding="utf-8"),
            re.M | re.S,
        )
        assert m, f"{path.name} has no _lock_reason_pid"
        blocks[path.name] = m.group(0)
    assert len(set(blocks.values())) == 1, (
        "lock-pid parsers have drifted apart: "
        + ", ".join(f"{k} ({len(v)} chars)" for k, v in blocks.items())
    )


def test_prepare_lock_fields_ITSELF_refuses_an_ambiguous_pid(tmp_path: Path):
    """Exercise the CALL SITE, not just the function it is supposed to call.

    The first version of this coverage extracted `_lock_reason_pid` from
    prepare.sh and ran it directly. It passed — and restoring the greedy sed on
    the `LOCK_PID=` line still passed, because the function was present and
    correct while `lock_fields` quietly did not use it. Proving a helper exists
    and behaves is not proving the code path calls it, which is the same
    derive-from-source-of-truth defect one level up.

    Every LOCK_PID consumer fails safe on empty: state-less recovery requires it
    non-empty, the live-owner check treats empty as alive and refuses, and the
    Codex CLI path demands an exact match. So empty is the correct answer here.
    """
    text = PREPARE.read_text(encoding="utf-8")
    parts = []
    for name in ("_lock_reason_pid", "lock_fields"):
        m = re.search(rf"^{name}\(\) \{{.*?^\}}", text, re.M | re.S)
        assert m, f"prepare.sh has no {name}"
        parts.append(m.group(0))

    block = (
        "worktree /tmp/wt\n"
        "branch refs/heads/wt/demo\n"
        "locked ai-worktree-v1 host=claude lifecycle=framework branch=wt/demo "
        "default=main base=abc pid=111 handed-off-from pid=222 start=2026-01-01T00:00:00Z"
    )
    script = (
        "\n\n".join(parts)
        + '\nlock_fields "$1"\nprintf "PID=[%s] BRANCH=[%s]\\n" "$LOCK_PID" "$LOCK_BRANCH"\n'
    )
    r = subprocess.run(  # nosec B603 B607
        ["bash", "-c", script, "_", block],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert "PID=[]" in r.stdout, (
        f"lock_fields resolved an ambiguous reason to {r.stdout.strip()!r}; "
        "two pid tokens have no defensible answer and must yield none"
    )
    # The rest of the reason must still parse — this is a targeted refusal, not
    # a parser that gives up on the whole line.
    assert "BRANCH=[wt/demo]" in r.stdout, r.stdout


def test_prepare_lock_fields_still_reads_an_unambiguous_pid(tmp_path: Path):
    """The refusal above must not have broken the ordinary case."""
    text = PREPARE.read_text(encoding="utf-8")
    parts = [
        re.search(rf"^{n}\(\) \{{.*?^\}}", text, re.M | re.S).group(0)
        for n in ("_lock_reason_pid", "lock_fields")
    ]
    block = (
        "worktree /tmp/wt\nbranch refs/heads/wt/demo\n"
        "locked ai-worktree-v1 host=claude lifecycle=framework branch=wt/demo "
        "default=main base=abc pid=4242 start=2026-01-01T00:00:00Z"
    )
    script = (
        "\n\n".join(parts) + '\nlock_fields "$1"\nprintf "PID=[%s]\\n" "$LOCK_PID"\n'
    )
    r = subprocess.run(  # nosec B603 B607
        ["bash", "-c", script, "_", block],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert "PID=[4242]" in r.stdout, r.stdout


def test_unreadable_ownership_evidence_refuses_rather_than_reading_as_absent(
    local_repo: Path,
):
    """An UNREAD source is not an ABSENT source.

    A journal naming a LIVE owner that cannot be read was skipped, letting a
    readable claim naming a dead owner decide — and the worktree was removed
    with its branch while that live pid was still running.
    """
    wt = _create_with_dead_owner(local_repo)
    journal = _journal(wt)
    assert journal.exists()
    journal.chmod(0o000)
    try:
        r = subprocess.run(  # nosec B603 B607
            ["bash", str(CLEANUP), str(wt), "--default-ref", "main"],
            capture_output=True,
            text=True,
            cwd=str(local_repo),
            env=_env(),
            check=False,
            timeout=60,
        )
        assert r.returncode == 1, r.stdout
        assert "cannot be read" in r.stdout, r.stdout
        assert wt.is_dir(), "a worktree with unreadable ownership evidence was removed"
    finally:
        journal.chmod(0o600)


def test_conflicting_dead_owners_are_unknown_not_dead_in_repo_hygiene():
    """cleanup.sh refuses on conflicting evidence; hygiene used to hand over a command.

    Two sources naming different owners is incoherent regardless of liveness, so
    the advisory tool must not be more willing to destroy than the destructive one.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import repo_hygiene as rh  # noqa: PLC0415

    a, b = _dead_pid(), _dead_pid()
    assert a != b
    assert rh._ownership_state([a, b]) == "unknown"
    assert rh._ownership_state([a]) == "dead"


def test_a_reentrant_continue_leaves_the_lock_alone_and_reruns_no_setup_hook(
    local_repo: Path,
):
    """A retry by the live recorded owner is a no-op, not a re-preparation.

    `claim_framework_lock` returns early when the lock already names a LIVE
    OWNER_PID, leaving `LOCK_RECLAIMED` at 0 — which is the only signal
    `advance_existing` has that a `ready` checkout can short-circuit to
    `ready_report`. Deleting that early return still produces READY, so every
    happy-path assertion in this file passed while the setup hook silently
    re-ran on each retry. The hook is arbitrary project code; running it again
    under a live session is the destructive direction, so count the runs.
    """
    (local_repo / ".ai-worktree").mkdir()
    (local_repo / ".ai-worktree" / "setup.sh").write_text(
        'printf x >> "$AI_WORKTREE_PRIMARY/setup-runs"\n'
    )
    _git(local_repo, "add", "-A")
    _git(local_repo, "commit", "-q", "-m", "setup hook")

    wt = _create_with_dead_owner(local_repo)
    holder = subprocess.Popen(  # nosec B603
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )
    counter = local_repo / "setup-runs"
    try:
        counts = []
        for _ in range(3):
            r = subprocess.run(  # nosec B603 B607
                [
                    "bash",
                    str(PREPARE),
                    "continue",
                    "--path",
                    str(wt),
                    "--owner-pid",
                    str(holder.pid),
                ],
                capture_output=True,
                text=True,
                cwd=str(local_repo),
                env=_env(),
                check=False,
                timeout=60,
            )
            assert r.returncode == 0 and "READY" in r.stdout, r.stdout
            counts.append(len(counter.read_text()) if counter.exists() else 0)
        # The FIRST continue legitimately reclaims from the dead creator and so
        # re-prepares; every continue after it is the same live owner retrying
        # and must change nothing.
        assert counts[1] == counts[0] and counts[2] == counts[0], (
            f"setup hook run counts across three retries were {counts}; "
            "a re-entrant retry by the live recorded owner must not re-prepare"
        )
    finally:
        holder.kill()
        holder.wait()
