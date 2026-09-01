"""Shared helpers for hook-script subprocess tests.

Consolidates transcript-building helpers that were previously duplicated across
test_hooks.py and test_pre_exit_plan_mode_gate_hook.py. Hook-specific `run_hook`
variants remain in their respective test files because their payload shapes,
env handling, and return tuples diverge per-hook.

Consolidated per session-123 Phase 2 (plan: snazzy-fluttering-whistle.md).
"""

import json
import os
import tempfile


def create_transcript(entries: list[dict]) -> str:
    """Write a JSONL transcript file from entries; return the path.

    Caller is responsible for os.unlink(path) in a finally block.
    """
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return path


def make_task_entry(subagent_type: str) -> dict:
    """Create a Task tool_use transcript entry with a given subagent_type."""
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "task-id",
                    "name": "Task",
                    "input": {
                        "description": "test",
                        "subagent_type": subagent_type,
                        "prompt": "test",
                    },
                }
            ],
        }
    }


def make_exit_plan_entry() -> dict:
    """Create an ExitPlanMode tool_use transcript entry."""
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "epm-id",
                    "name": "ExitPlanMode",
                    "input": {"plan": "test plan content"},
                }
            ],
        }
    }


# ---------------------------------------------------------------------------
# Hook decision parsers — shared by test_pre_exit_plan_mode_gate_hook.py
# and test_pre_test_oom_gate_hook.py. Consolidated session-123 Commit L
# (BACKLOG #122 Case 4): both files had byte-equivalent `is_allow`/`is_deny`
# with only stylistic differences (local-var extraction vs inline). Unified
# here so the hook-decision contract is single-sourced.
# ---------------------------------------------------------------------------


def is_deny(response: dict | None) -> bool:
    """True iff a hook JSON response carries permissionDecision=='deny'."""
    if not response:
        return False
    return response.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def is_allow(response: dict | None, exit_code: int) -> bool:
    """True iff exit 0 AND (no response OR response is not a deny).

    Per Claude Code hook contract: `allow` is exit 0 with either no JSON
    output or JSON output whose permissionDecision is anything other than
    'deny' (e.g. 'ask', absent, or additionalContext-only responses).
    """
    if exit_code != 0:
        return False
    if response is None:
        return True
    return response.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"


# ---------------------------------------------------------------------------
# Degraded-environment helpers for the PreToolUse GATES (BACKLOG #299)
# ---------------------------------------------------------------------------
# Every gate test to date varies the INPUT and holds the ENVIRONMENT fixed. The
# whole #298/#299 defect class lives on the environment axis — a missing lib, a
# silent interpreter, an unset variable — so nothing could express those cases
# and nothing caught them.
#
# `tests/test_session_start_lib_degradation.py` already does this for the
# SessionStart hooks. These helpers are the PreToolUse-gate counterpart and
# deliberately reuse its copy-then-delete shape rather than inventing a second
# one; the difference is that a gate has a DECISION to preserve, so the runner
# below returns the verdict, not just the exit code.


def gate_tree(dest_root, hook_name: str, *, drop_libs=()):
    """Copy a gate + everything it resolves from `$HOOK_DIR` into `dest_root`.

    Returns the path to the copied hook. Copy-then-delete, never
    delete-in-place: a test that mutates the tree it is testing is not a test.

    `scan_transcript.py` is copied too, and that is load-bearing rather than
    tidy. An earlier version copied only `lib/*.sh`, so every "missing lib" case
    for the push, governance and exit-plan gates ALSO removed the scanner — and
    a green there could not say which absence had been survived. Drop a lib
    deliberately via `drop_libs`; never by omission.
    """
    import shutil
    from pathlib import Path

    hooks = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
    dest = Path(dest_root) / "hooks"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "lib").mkdir(exist_ok=True)
    shutil.copy(hooks / hook_name, dest / hook_name)
    for lib in (hooks / "lib").glob("*.sh"):
        if lib.name in drop_libs:
            continue
        shutil.copy(lib, dest / "lib" / lib.name)
    for extra in hooks.glob("*.py"):
        shutil.copy(extra, dest / extra.name)
    return dest / hook_name


# The registered PreToolUse timeout per gate, read from `.claude/settings.json`.
# Tests must run each gate inside its REAL budget: a gate that takes 12s passes
# a 30s test harness and is SIGKILLed-and-ALLOWED in production, which is the
# documented worst path. Keep in sync with the settings file.
GATE_TIMEOUTS = {
    "pre-tool-content-security.sh": 5,
    "pre-test-oom-gate.sh": 10,
    "pre-tool-governance-check.sh": 10,
    "pre-exit-plan-mode-gate.sh": 10,
    "pre-push-quality-gate.sh": 15,
}


def stub_tool(dest_root, name: str, body: str):
    """A PATH directory whose `name` behaves as `body` says.

    Returns the directory to PREPEND to PATH. Used to simulate the measured
    failure shapes: an interpreter that exits 0 printing nothing, one that
    exits 127, one that truncates.
    """
    from pathlib import Path

    d = Path(dest_root) / f"stub-{name}"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body)
    p.chmod(0o755)
    return d


# The three shapes that matter, named once so every test uses the same ones.
STUB_SILENT = "#!/bin/sh\nexit 0\n"  # the #298 shape: succeeds, says nothing
STUB_BROKEN = "#!/bin/sh\nexit 127\n"  # absent-equivalent
STUB_TRUNCATED = "#!/bin/sh\nprintf 'PARTIAL'\nexit 3\n"


# Process-wide neutral-environment directory, created once in the system temp
# area and reused. Module-level so repeated run_gate calls do not each pay for a
# mkdir, and OUTSIDE the repo so nothing it contains can ever be committed.
_NEUTRAL_ENV_DIR = None


def _neutral_env_dir():
    """A PATH dir holding an empty-output `ps`. See run_gate's ambient_ps note."""
    global _NEUTRAL_ENV_DIR
    if _NEUTRAL_ENV_DIR is None:
        import tempfile
        from pathlib import Path as _P

        d = _P(tempfile.mkdtemp(prefix="hookgate-neutral-"))
        ps = d / "ps"
        ps.write_text("#!/bin/sh\nexit 0\n")
        ps.chmod(0o755)
        _NEUTRAL_ENV_DIR = d
    return _NEUTRAL_ENV_DIR


def run_gate(
    hook_path,
    command: str,
    *,
    env=None,
    path_prefix=None,
    timeout=None,
    payload=None,
    ambient_ps=False,
):
    """Invoke a PreToolUse gate with a Bash payload. Returns (denied, rc, stdout).

    `denied` follows the harness contract exactly, verified against CLI 2.1.220:
    a deny is exit 2, OR exit 0 with JSON carrying permissionDecision=deny.
    Everything else — exit 1, exit 127, a silent exit 0 — is an ALLOW. Encoding
    that here rather than in each test is the point: the bug being hunted is
    precisely a gate that "fails" in a way the harness reads as yes.

    `env` values of None UNSET the variable. That distinction is load-bearing:
    an unset `HOME` trips `set -u`, an EMPTY `HOME` does not, and the two
    produce different verdicts in the same gate. Tests must be able to say which
    one they mean.

    `timeout` defaults to the gate's REGISTERED budget, not an arbitrary 30s.
    A gate that overruns its real budget is SIGKILLed-and-ALLOWED in production;
    a generous test harness hides exactly that. Overrun raises here rather than
    silently passing.

    `payload` overrides the default Bash-shaped body — needed for gates whose
    matcher is not `Bash` (the exit-plan gate) or which read `transcript_path`.
    """
    import json as _json
    import os as _os
    import subprocess
    from pathlib import Path as _Path

    if timeout is None:
        timeout = GATE_TIMEOUTS.get(_Path(hook_path).name, 15)
    body = (
        _json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        if payload is None
        else _json.dumps(payload)
    )
    e = {**_os.environ}
    # SCRUB INHERITED BYPASS VARIABLES BEFORE ANYTHING ELSE.
    #
    # These tests assert that a gate DENIES. Every one of these variables makes a
    # gate allow by design, so inheriting one from the caller's shell turns a
    # must-deny assertion into a pass for the wrong reason and, worse, makes the
    # must-ALLOW anti-brick assertions vacuously true.
    #
    # Measured session-272: running the suite the documented way for a heavy run
    # (`PYTEST_ALLOW_HEAVY=1 pytest ...`) produced 8 failures that a clean run did
    # not have. A suite whose result depends on an inherited variable teaches
    # people to distrust its red. A test that needs one of these sets it
    # EXPLICITLY through `env`, which still works — the loop below runs after.
    for _bypass in (
        "PYTEST_ALLOW_HEAVY",
        "PYTEST_SKIP_OOM_GATE",
        "CONTENT_SECURITY_SKIP",
        "QUALITY_GATE_SKIP",
        "GOVERNANCE_SOFT_MODE",
        "CE_SOFT_MODE",
        "READONLY_BASH_SKIP",
        "MCP_DETECT_SKIP",
        "PLAN_CONTRARIAN_CONFIRMED",
        "PLAN_CONTRARIAN_SKIP_HOOK",
    ):
        e.pop(_bypass, None)
    for k, v in (env or {}).items():
        e.pop(k, None) if v is None else e.__setitem__(k, v)
    # NEUTRALIZE AMBIENT MACHINE STATE. This is the #304 fix and it is the
    # difference between a test that verifies the gate and one that verifies the
    # laptop.
    #
    # A gate's verdict can depend on signals the MACHINE supplies, not the test:
    # the OOM gate denies when `ps` shows torch-holding processes. A developer
    # box running the MCP servers has ~13 of them, so the gate denied on every
    # local run and the tests were green — while a SECOND, broken code path
    # (heartbeat age parsing to empty and falling through to "not blocking") sat
    # underneath, doing nothing, for five review rounds and a whole
    # GATES × DEGRADATIONS cross-product. A clean CI runner has no torch
    # processes, so it exercised the broken path and failed immediately.
    #
    # Measured: with `ps` stubbed empty, this machine reproduces the clean-runner
    # verdict exactly, and the pre-fix hook fails the test locally.
    #
    # So the harness supplies an EMPTY `ps` by default. A test then sees only the
    # state it establishes itself (e.g. `daemon_home()`), which is the property
    # that makes a result mean something. Pass `ambient_ps=True` to opt out — no
    # current test does, and a new one that needs it should say why.
    if not ambient_ps:
        # A TEMP DIR, NOT `hook_path.parent`. The first version of this wrote
        # `_neutral-env/ps` next to the hook — and 16 call sites pass the LIVE
        # `.claude/hooks/` directory, so the harness created a stub `ps` inside
        # the real repo and it was committed. A fake `ps` shipping in the
        # safety-hooks directory is exactly the kind of stray executable this
        # project's own content-security work exists to notice.
        #
        # Caught by the completion sequence, not by the suite: every test passed
        # either way, because the stub only ever affects the harness's own PATH.
        e["PATH"] = f"{_neutral_env_dir()}:{e.get('PATH', '')}"
    if path_prefix is not None:
        e["PATH"] = f"{path_prefix}:{e.get('PATH', '')}"
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=body,
        capture_output=True,
        text=True,
        env=e,
        timeout=timeout,
    )
    resp = None
    if r.stdout.strip():
        try:
            resp = _json.loads(r.stdout.strip())
        except _json.JSONDecodeError:
            pass
    return (r.returncode == 2 or is_deny(resp)), r.returncode, r.stdout


def daemon_home(dest_root):
    """A HOME carrying a FRESH watcher heartbeat — the OOM gate's deny precondition.

    THE DEFECT THIS EXISTS TO PREVENT, measured on CI 2026-08-02.

    The OOM gate does not deny `pytest tests/` because of the command. It denies
    because the command is dangerous ON A LOADED MACHINE — a live watcher daemon
    or other torch-holding processes. On a quiet machine it correctly ALLOWS.

    Six must-deny tests asserted a deny without establishing either signal. They
    passed on the author's Mac, where 13 torch-holding MCP processes fired the
    ps-based trigger, and failed the first time they ran on a clean CI runner.
    They were testing the machine, not the gate — and the pass was luck.

    Worse, that same masking hid a REAL fail-open in the gate for five review
    rounds: with python3 silent the heartbeat age parsed to empty, which took the
    "stale, not blocking" branch. The ps signal covered for it locally.

    So every OOM must-deny assertion establishes the precondition HERE, in one
    place. `ps`-detectable torch processes cannot be created portably by a test;
    a heartbeat file can, so the heartbeat is the testable signal.
    """
    import json as _json
    from datetime import datetime, timedelta, timezone
    from pathlib import Path as _Path

    home = _Path(dest_root) / "daemon-home"
    (home / ".context-engine").mkdir(parents=True, exist_ok=True)
    alive = datetime.now(timezone.utc) - timedelta(seconds=30)
    (home / ".context-engine" / "watcher-heartbeat.json").write_text(
        _json.dumps({"alive_at": alive.isoformat()})
    )
    return home
