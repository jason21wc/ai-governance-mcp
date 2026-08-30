"""Hermetic behavior tests for the host-aware worktree preparation state machine."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "global-skills"
    / "start-worktree"
    / "prepare.sh"
)
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_TERMINAL_PROMPT": "0",
}
JOURNAL_V2_KEYS = [
    "version",
    "host",
    "lifecycle_owner",
    "path",
    "branch",
    "base_sha",
    "default_ref",
    "owner_pid",
    "session_id",
    "task_key",
    "parallel_task",
    "state",
    "updated_at",
]


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
    cwd: Path,
    *args: str,
    setup_ok: bool = False,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(GIT_ENV)
    if setup_ok:
        env["AI_TEST_SETUP_OK"] = "1"
    env.update(env_overrides or {})
    return subprocess.run(  # nosec B603 B607
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        check=False,
        timeout=30,
    )


def _state_file(worktree: Path) -> Path:
    gitdir = Path(_git(worktree, "rev-parse", "--git-dir"))
    if not gitdir.is_absolute():
        gitdir = worktree / gitdir
    return gitdir / "ai-worktree-state"


def _state_values(worktree: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in _state_file(worktree).read_text().splitlines()
    )


def _rewrite_as_v1(worktree: Path) -> None:
    lines = _state_file(worktree).read_text().splitlines()
    kept = [
        "version=1" if line == "version=2" else line
        for line in lines
        if not line.startswith(("task_key=", "parallel_task="))
    ]
    _state_file(worktree).write_text("\n".join(kept) + "\n")


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


def _create_args(path: Path, owner_pid: int | None = None) -> tuple[str, ...]:
    return (
        "codex-cli-create",
        "--slug",
        "demo",
        "--nonce",
        "n1",
        "--path",
        str(path),
        "--base",
        "main",
        "--default-ref",
        "main",
        "--owner-pid",
        str(owner_pid or os.getpid()),
    )


def test_framework_create_publishes_locks_and_records_ready(repo: Path):
    target = repo.parent / "wt-ready"
    result = _run(repo, *_create_args(target))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "codex-cli-validate --path" in result.stdout
    assert str(target) in result.stdout
    assert "anchor every subsequent tool" in result.stdout
    assert "ordinary-shell bootstrap only" in result.stdout
    assert "state=ready" in _state_file(target).read_text()
    state_lines = _state_file(target).read_text().splitlines()
    assert [line.split("=", 1)[0] for line in state_lines] == JOURNAL_V2_KEYS
    assert _state_values(target)["version"] == "2"
    assert _state_values(target)["task_key"] == "slug:demo"
    assert _state_values(target)["parallel_task"] == "0"
    assert _git(target, "branch", "--show-current") == "wt/demo-n1"
    assert (
        _git(target, "rev-parse", "--abbrev-ref", "@{upstream}") == "origin/wt/demo-n1"
    )
    block = _git(repo, "worktree", "list", "--porcelain")
    assert "locked ai-worktree-v2 host=codex-cli lifecycle=framework" in block

    again = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert again.returncode == 0, again.stdout
    assert "state=ready" in _state_file(target).read_text()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda lines: [lines[0], lines[2], lines[1], *lines[3:]],
        lambda lines: [*lines, "state=ready"],
        lambda lines: [*lines[:10], "unexpected=0", *lines[11:]],
        lambda lines: [
            *(
                "task_key=INVALID" if line.startswith("task_key=") else line
                for line in lines
            )
        ],
        lambda lines: [
            *(
                "parallel_task=2" if line.startswith("parallel_task=") else line
                for line in lines
            )
        ],
        lambda lines: [
            *(
                f"base_sha={'a' * 41}" if line.startswith("base_sha=") else line
                for line in lines
            )
        ],
        lambda lines: [
            *(
                "session_id=bad\tvalue" if line.startswith("session_id=") else line
                for line in lines
            )
        ],
    ],
    ids=[
        "reordered",
        "duplicate",
        "unknown",
        "bad-task",
        "bad-parallel",
        "bad-sha-length",
        "control-char",
    ],
)
def test_continue_refuses_malformed_v2_journal(repo: Path, mutate):
    target = repo.parent / "wt-malformed"
    assert _run(repo, *_create_args(target)).returncode == 0
    state_file = _state_file(target)
    state_file.write_text("\n".join(mutate(state_file.read_text().splitlines())) + "\n")

    result = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert result.returncode == 2, result.stdout
    assert "malformed or unsupported" in result.stdout


@pytest.mark.parametrize("task_key", ["Upper", "-leading", "space key", "x" * 129])
def test_create_rejects_invalid_task_keys(repo: Path, task_key: str):
    target = repo.parent / "wt-invalid-task"
    result = _run(repo, *_create_args(target), "--task-key", task_key)
    assert result.returncode == 2, result.stdout
    assert "task key" in result.stdout.lower()
    assert not target.exists()


def test_parallel_override_requires_explicit_task_key(repo: Path):
    target = repo.parent / "wt-implicit-parallel"
    result = _run(repo, *_create_args(target), "--allow-parallel-task")
    assert result.returncode == 2, result.stdout
    assert "requires an explicit --task-key" in result.stdout
    assert not target.exists()


def test_create_rejects_malformed_default_ref_before_mutation(repo: Path):
    target = repo.parent / "wt-invalid-default"
    args = list(_create_args(target))
    args[args.index("main", args.index("--default-ref"))] = "bad ref"
    result = _run(repo, *args, "--allow-local-only")
    assert result.returncode == 2, result.stdout
    assert "invalid default ref" in result.stdout
    assert not target.exists()


def test_writer_refuses_control_characters_in_journal_values(repo: Path):
    target = repo.parent / "wt-invalid-session"
    result = _run(repo, *_create_args(target), "--session-id", "bad\tvalue")
    assert result.returncode == 2, result.stdout
    assert "violate the v2 journal schema" in result.stdout
    assert not _state_file(target).exists()


def test_sequential_duplicate_task_key_refuses_second_worktree(repo: Path):
    first = repo.parent / "wt-task-first"
    second = repo.parent / "wt-task-second"
    assert _run(repo, *_create_args(first), "--task-key", "issue:359").returncode == 0
    args = list(_create_args(second))
    args[args.index("n1")] = "n2"
    result = _run(repo, *args, "--task-key", "issue:359")
    assert result.returncode == 1, result.stdout
    assert "already has an active worktree" in result.stdout
    assert str(first) in result.stdout
    assert not second.exists()


def test_explicit_parallel_task_key_allows_second_worktree(repo: Path):
    first = repo.parent / "wt-parallel-first"
    second = repo.parent / "wt-parallel-second"
    assert _run(repo, *_create_args(first), "--task-key", "issue:359").returncode == 0
    args = list(_create_args(second))
    args[args.index("n1")] = "n2"
    result = _run(
        repo,
        *args,
        "--task-key",
        "issue:359",
        "--allow-parallel-task",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state_values(second)["task_key"] == "issue:359"
    assert _state_values(second)["parallel_task"] == "1"


def test_recognizable_v1_generated_nonce_blocks_same_default_task(repo: Path):
    first = repo.parent / "wt-v1-recognized"
    args = list(_create_args(first))
    args[args.index("n1")] = "deadbeef"
    assert _run(repo, *args).returncode == 0
    _rewrite_as_v1(first)

    second = repo.parent / "wt-v1-second"
    args = list(_create_args(second))
    args[args.index("n1")] = "cafebabe"
    result = _run(repo, *args)
    assert result.returncode == 1, result.stdout
    assert "already has an active worktree" in result.stdout


def test_legacy_v1_journal_and_lock_remain_continuable(repo: Path):
    target = repo.parent / "wt-v1-continue"
    args = list(_create_args(target))
    args[args.index("n1")] = "deadbeef"
    assert _run(repo, *args).returncode == 0
    state = _state_values(target)
    _rewrite_as_v1(target)
    _git(repo, "worktree", "unlock", str(target))
    reason = (
        "ai-worktree-v1 host=codex-cli lifecycle=framework "
        f"branch={state['branch']} default=main base={state['base_sha']} "
        f"pid={os.getpid()} start=2026-08-28T00:00:00Z"
    )
    _git(repo, "worktree", "lock", "--reason", reason, str(target))

    resumed = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "READY" in resumed.stdout


def test_continue_refuses_v2_lock_with_unexpected_fields(repo: Path):
    """Covers: FM-WORKTREE-JOURNAL-V2-STRICT."""
    target = repo.parent / "wt-v2-malformed-lock"
    assert _run(repo, *_create_args(target)).returncode == 0
    state = _state_values(target)
    _git(repo, "worktree", "unlock", str(target))
    reason = (
        "ai-worktree-v2 host=codex-cli lifecycle=framework "
        f"branch={state['branch']} default=main base={state['base_sha']} "
        f"pid={os.getpid()} task=slug:demo parallel=0 unexpected=value "
        "start=2026-08-28T00:00:00Z"
    )
    _git(repo, "worktree", "lock", "--reason", reason, str(target))

    resumed = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert resumed.returncode == 2, resumed.stdout + resumed.stderr
    assert "malformed or has unexpected fields" in resumed.stdout


def test_noncanonical_v1_same_slug_is_ambiguous_not_inferred(repo: Path):
    first = repo.parent / "wt-v1-ambiguous"
    assert _run(repo, *_create_args(first)).returncode == 0
    _rewrite_as_v1(first)

    second = repo.parent / "wt-v1-second"
    args = list(_create_args(second))
    args[args.index("n1")] = "n2"
    result = _run(repo, *args)
    assert result.returncode == 2, result.stdout
    assert "legacy same-slug branch" in result.stdout


def test_post_create_race_marks_loser_conflicted_and_continue_can_resolve(
    repo: Path, tmp_path: Path
):
    """Covers: FM-WORKTREE-DUPLICATE-TASK."""
    target = repo.parent / "wt-race-z"
    peer = repo.parent / "wt-race-a"
    base_sha = _git(repo, "rev-parse", "main")
    bin_dir = tmp_path / "fake-git-race"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    real_git = shutil.which("git")
    assert real_git
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'case " $* " in\n'
        '  *" worktree add --lock "*" -b wt/demo-n1 "*)\n'
        f'    "{real_git}" "$@" || exit $?\n'
        f'    "{real_git}" -C "{repo}" worktree add --lock '
        '--reason "ai-worktree-v2 host=codex-cli lifecycle=framework '
        f"branch=wt/demo-deadbeef default=main base={base_sha} pid={os.getpid()} "
        'task=slug:demo parallel=0 start=2026-08-28T00:00:00Z" '
        "-b wt/demo-deadbeef "
        f'"{peer}" main || exit $?\n'
        f'    gd=$("{real_git}" -C "{peer}" rev-parse --git-dir) || exit $?\n'
        f'    case "$gd" in /*) ;; *) gd="{peer}/$gd" ;; esac\n'
        "    {\n"
        "      printf '%s\\n' 'version=2' 'host=codex-cli' "
        "'lifecycle_owner=framework' "
        f"'path={peer}' 'branch=wt/demo-deadbeef' 'base_sha={base_sha}' "
        f"'default_ref=main' 'owner_pid={os.getpid()}' 'session_id=' "
        "'task_key=slug:demo' 'parallel_task=0' 'state=ready' "
        "'updated_at=2026-08-28T00:00:00Z'\n"
        '    } >"$gd/ai-worktree-state"\n'
        "    exit 0\n"
        "    ;;\n"
        "esac\n"
        f'exec "{real_git}" "$@"\n'
    )
    wrapper.chmod(0o755)

    raced = _run(
        repo,
        *_create_args(target),
        env_overrides={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )
    assert raced.returncode == 1, raced.stdout + raced.stderr
    assert _state_values(target)["state"] == "task-conflict"
    assert "won" in raced.stdout
    assert _git(repo, "branch", "-r", "--list", "origin/wt/demo-n1") == ""

    refused = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert refused.returncode == 1, refused.stdout
    assert "task-conflict is non-ready" in refused.stdout

    # A conflicted loser is still an active task record. Remove only the
    # synthetic winner, then prove a third sequential start remains blocked by
    # the loser until its owner explicitly resolves or abandons it.
    _git(repo, "worktree", "unlock", str(peer))
    _git(repo, "worktree", "remove", "--force", str(peer))
    _git(repo, "branch", "-D", "wt/demo-deadbeef")
    third = repo.parent / "wt-race-third"
    third_args = list(_create_args(third))
    third_args[third_args.index("n1")] = "n3"
    blocked = _run(repo, *third_args)
    assert blocked.returncode == 1, blocked.stdout
    assert "state task-conflict" in blocked.stdout
    assert not third.exists()

    recovered = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
        "--allow-parallel-task",
    )
    assert recovered.returncode == 0, recovered.stdout + recovered.stderr
    state = _state_values(target)
    assert state["state"] == "ready"
    assert state["parallel_task"] == "1"


def test_publication_failure_reports_continue_instead_of_second_create(
    repo: Path, tmp_path: Path
):
    target = repo.parent / "wt-push-failure"
    bin_dir = tmp_path / "fake-git-push"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    real_git = shutil.which("git")
    assert real_git
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'case " $* " in *" push -u origin wt/demo-n1 "*) exit 55 ;; esac\n'
        f'exec "{real_git}" "$@"\n'
    )
    wrapper.chmod(0o755)

    first = _run(
        repo,
        *_create_args(target),
        env_overrides={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )
    assert first.returncode == 2, first.stdout
    assert "state remains created" in first.stdout
    assert f"continue --path '{target}'" in first.stdout
    assert f"--owner-pid '{os.getpid()}'" in first.stdout
    assert "run codex-cli-create" not in first.stdout

    resumed = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "state=ready" in _state_file(target).read_text()


def test_failed_setup_is_preserved_and_continue_reaches_ready(repo: Path):
    hook_dir = repo / ".ai-worktree"
    hook_dir.mkdir()
    setup = hook_dir / "setup.sh"
    setup.write_text('#!/usr/bin/env bash\n[ "${AI_TEST_SETUP_OK:-}" = "1" ]\n')
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add setup hook")
    _git(repo, "push", "-q", "origin", "main")

    target = repo.parent / "wt-retry"
    first = _run(repo, *_create_args(target))
    assert first.returncode == 2, first.stdout
    assert "state=setup-failed" in _state_file(target).read_text()
    assert str(target) in _git(repo, "worktree", "list", "--porcelain")

    resumed = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
        setup_ok=True,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "state=ready" in _state_file(target).read_text()


def test_continue_refuses_a_different_live_recorded_owner(repo: Path):
    owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])  # nosec B603
    try:
        target = repo.parent / "wt-owned"
        created = _run(repo, *_create_args(target, owner.pid))
        assert created.returncode == 0, created.stdout
        other = _run(
            repo,
            "continue",
            "--path",
            str(target),
            "--owner-pid",
            str(os.getpid()),
        )
        assert other.returncode == 1, other.stdout
        assert "still live" in other.stdout.lower()
    finally:
        owner.terminate()
        owner.wait(timeout=5)


def test_codex_cli_validate_requires_isolated_published_locked_tree(repo: Path):
    target = repo.parent / "wt-validate"
    assert _run(repo, *_create_args(target)).returncode == 0
    valid = _run(target, "codex-cli-validate", "--owner-pid", str(os.getpid()))
    assert valid.returncode == 0, valid.stdout
    primary = _run(repo, "codex-cli-validate", "--owner-pid", str(os.getpid()))
    assert primary.returncode == 1
    assert "primary checkout" in primary.stdout
    assert "run codex-cli-create before validation" in primary.stdout


def test_codex_cli_validate_refuses_downgraded_v1_lock(repo: Path):
    target = repo.parent / "wt-validate-v1-lock"
    assert _run(repo, *_create_args(target)).returncode == 0
    state = _state_values(target)
    _git(repo, "worktree", "unlock", str(target))
    reason = (
        "ai-worktree-v1 host=codex-cli lifecycle=framework "
        f"branch={state['branch']} default=main base={state['base_sha']} "
        f"pid={os.getpid()} start=2026-08-28T00:00:00Z"
    )
    _git(repo, "worktree", "lock", "--reason", reason, str(target))

    out = _run(target, "codex-cli-validate", "--owner-pid", str(os.getpid()))
    assert out.returncode == 2, out.stdout
    assert "does not exactly match v2" in out.stdout


def test_codex_cli_validate_refuses_claude_state(repo: Path):
    target = repo.parent / "wt-claude"
    args = list(_create_args(target))
    args[0] = "claude-create"
    assert _run(repo, *args).returncode == 0
    out = _run(target, "codex-cli-validate", "--owner-pid", str(os.getpid()))
    assert out.returncode == 1, out.stdout
    assert "host/owner" in out.stdout


def test_codex_cli_validate_refuses_foreign_owner_and_wrong_upstream(repo: Path):
    owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])  # nosec B603
    try:
        target = repo.parent / "wt-validate-owner"
        assert _run(repo, *_create_args(target, owner.pid)).returncode == 0
        foreign = _run(target, "codex-cli-validate", "--owner-pid", str(os.getpid()))
        assert foreign.returncode == 1, foreign.stdout
        assert "owner pid" in foreign.stdout

        _git(target, "branch", "--set-upstream-to", "origin/main")
        wrong_upstream = _run(
            target, "codex-cli-validate", "--owner-pid", str(owner.pid)
        )
        assert wrong_upstream.returncode == 2, wrong_upstream.stdout
        assert "upstream" in wrong_upstream.stdout
    finally:
        owner.terminate()
        owner.wait(timeout=5)


@pytest.mark.parametrize("state", ["created", "published", "locked", "setup-failed"])
def test_codex_cli_validate_refuses_every_non_ready_state(repo: Path, state: str):
    target = repo.parent / f"wt-not-ready-{state}"
    args = list(_create_args(target))
    args[args.index("n1")] = state
    assert _run(repo, *args).returncode == 0
    state_file = _state_file(target)
    state_file.write_text(
        state_file.read_text().replace("state=ready", f"state={state}")
    )

    out = _run(target, "codex-cli-validate", "--owner-pid", str(os.getpid()))
    assert out.returncode == 1, out.stdout
    assert "not ready" in out.stdout


def test_create_retry_refuses_cross_host_reclassification(repo: Path):
    target = repo.parent / "wt-cross-host-retry"
    args = list(_create_args(target))
    args[0] = "claude-create"
    assert _run(repo, *args).returncode == 0

    args[0] = "codex-cli-create"
    out = _run(repo, *args)
    assert out.returncode == 1, out.stdout
    assert "does not match this create request" in out.stdout
    assert "host=claude" in _state_file(target).read_text()


def test_framework_creation_recovers_if_state_write_is_interrupted(
    repo: Path, tmp_path: Path
):
    target = repo.parent / "wt-interrupted"
    bin_dir = tmp_path / "fake-mv"
    bin_dir.mkdir()
    wrapper = bin_dir / "mv"
    real_mv = shutil.which("mv")
    assert real_mv
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'case "${2:-}" in *ai-worktree-state) exit 55 ;; esac\n'
        f'exec "{real_mv}" "$@"\n'
    )
    wrapper.chmod(0o755)
    first = _run(
        repo,
        *_create_args(target),
        "--task-key",
        "issue:359",
        env_overrides={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )
    assert first.returncode == 2, first.stdout
    assert not _state_file(target).exists()
    assert "atomic recovery lock" in first.stdout

    resumed = _run(
        repo,
        "continue",
        "--path",
        str(target),
        "--owner-pid",
        str(os.getpid()),
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "Recovered the creation journal" in resumed.stdout
    assert "state=ready" in _state_file(target).read_text()
    assert _state_values(target)["task_key"] == "issue:359"


def test_state_less_atomic_creation_lock_blocks_a_foreign_live_owner(
    repo: Path, tmp_path: Path
):
    owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])  # nosec B603
    try:
        target = repo.parent / "wt-interrupted-owned"
        bin_dir = tmp_path / "fake-mv-owned"
        bin_dir.mkdir()
        wrapper = bin_dir / "mv"
        real_mv = shutil.which("mv")
        assert real_mv
        wrapper.write_text(
            "#!/usr/bin/env bash\n"
            'case "${2:-}" in *ai-worktree-state) exit 55 ;; esac\n'
            f'exec "{real_mv}" "$@"\n'
        )
        wrapper.chmod(0o755)
        first = _run(
            repo,
            *_create_args(target, owner.pid),
            env_overrides={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )
        assert first.returncode == 2, first.stdout

        foreign = _run(
            repo,
            "continue",
            "--path",
            str(target),
            "--owner-pid",
            str(os.getpid()),
        )
        assert foreign.returncode == 1, foreign.stdout
        assert "another live owner" in foreign.stdout
        assert not _state_file(target).exists()
    finally:
        owner.terminate()
        owner.wait(timeout=5)


def test_codex_desktop_adoption_attaches_branch_without_framework_lock(repo: Path):
    target = repo.parent / "desktop-native"
    _git(repo, "worktree", "add", "--detach", str(target), "main")
    result = _run(
        target,
        "codex-desktop-adopt",
        "--slug",
        "desktop",
        "--nonce",
        "n1",
        "--default-ref",
        "main",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _git(target, "branch", "--show-current") == "wt/desktop-n1"
    state = _state_file(target).read_text()
    assert "lifecycle_owner=codex-desktop" in state
    assert "state=ready" in state
    block = _git(repo, "worktree", "list", "--porcelain")
    target_block = block.split(f"worktree {target}", 1)[1].split("\n\n", 1)[0]
    assert "locked" not in target_block


def test_codex_desktop_adoption_retries_after_switch_failure(
    repo: Path, tmp_path: Path
):
    target = repo.parent / "desktop-interrupted"
    _git(repo, "worktree", "add", "--detach", str(target), "main")
    bin_dir = tmp_path / "fake-git"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    real_git = shutil.which("git")
    assert real_git
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'case " $* " in *" switch -c "*) exit 55 ;; esac\n'
        f'exec "{real_git}" "$@"\n'
    )
    wrapper.chmod(0o755)
    first = _run(
        target,
        "codex-desktop-adopt",
        "--slug",
        "desktop",
        "--nonce",
        "retry",
        "--default-ref",
        "main",
        env_overrides={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )
    assert first.returncode == 2, first.stdout
    assert "state=attached" in _state_file(target).read_text()
    assert _git(target, "branch", "--show-current") == ""

    resumed = _run(target, "codex-desktop-adopt")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert _git(target, "branch", "--show-current") == "wt/desktop-retry"
    assert "state=ready" in _state_file(target).read_text()


def test_codex_desktop_adoption_refuses_stale_detached_base(repo: Path):
    target = repo.parent / "desktop-stale"
    _git(repo, "worktree", "add", "--detach", str(target), "main")
    (repo / "advance.txt").write_text("new live base\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "advance main")
    _git(repo, "push", "-q", "origin", "main")

    out = _run(
        target,
        "codex-desktop-adopt",
        "--slug",
        "desktop",
        "--nonce",
        "stale",
        "--default-ref",
        "main",
    )
    assert out.returncode == 1, out.stdout
    assert "stale" in out.stdout.lower()
    assert _git(target, "branch", "--show-current") == ""
    assert not _state_file(target).exists()


def test_codex_desktop_adoption_refuses_a_live_nondefault_branch(repo: Path):
    _git(repo, "branch", "develop", "main")
    _git(repo, "push", "-q", "origin", "develop")
    target = repo.parent / "desktop-wrong-default"
    _git(repo, "worktree", "add", "--detach", str(target), "develop")

    out = _run(
        target,
        "codex-desktop-adopt",
        "--slug",
        "desktop",
        "--nonce",
        "wrong-default",
        "--default-ref",
        "develop",
    )
    assert out.returncode == 2, out.stdout
    assert "not the live origin default" in out.stdout
    assert _git(target, "branch", "--show-current") == ""
