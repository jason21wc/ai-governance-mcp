"""Tests for the pre-exit-plan-mode-gate hook.

Per BACKLOG #116 / V-004 escalation: structural enforcement that contrarian-reviewer
is invoked for the current plan before ExitPlanMode fires. Scanner-level logic
(plan-scoped anchor, tool_use parsing) is covered in test_hooks.py::TestContrarianAfterLastPlan.
This file tests the HOOK's contract: payload parsing, env bypasses, timeout guards,
ERR trap, and JSON output format.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


PROJECT_DIR = Path(__file__).parent.parent
HOOK_PATH = PROJECT_DIR / ".claude" / "hooks" / "pre-exit-plan-mode-gate.sh"


def create_transcript(entries: list[dict]) -> str:
    """Write JSONL transcript from entries; return path."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return path


def make_exit_plan_entry() -> dict:
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "epm",
                    "name": "ExitPlanMode",
                    "input": {"plan": "test"},
                }
            ],
        }
    }


def make_task_entry(subagent_type: str) -> dict:
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "t1",
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


def run_hook(
    transcript_path: str | None,
    *,
    env_overrides: dict[str, str] | None = None,
    timeout_seconds: int = 10,
) -> tuple[int, dict | None, str]:
    """Invoke the hook with a PreToolUse ExitPlanMode-style payload.

    Returns (exit_code, parsed_stdout_json_or_None, stderr).
    """
    payload_obj = {
        "hook_event_name": "PreToolUse",
        "tool_name": "ExitPlanMode",
        "tool_input": {"plan": "example"},
    }
    if transcript_path is not None:
        payload_obj["transcript_path"] = transcript_path
    payload = json.dumps(payload_obj)

    env = os.environ.copy()
    env["PLAN_CONTRARIAN_DEBUG"] = "false"
    # Strip inherited bypass vars unless test sets them
    env.pop("PLAN_CONTRARIAN_CONFIRMED", None)
    env.pop("PLAN_CONTRARIAN_SKIP_HOOK", None)
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout_seconds,
    )

    stdout = result.stdout.strip()
    if not stdout:
        return result.returncode, None, result.stderr
    try:
        return result.returncode, json.loads(stdout), result.stderr
    except json.JSONDecodeError:
        return result.returncode, {"_raw": stdout}, result.stderr


def is_deny(response: dict | None) -> bool:
    if not response:
        return False
    return response.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def is_allow(response: dict | None, exit_code: int) -> bool:
    """Allow means exit 0 AND (no JSON output OR output isn't a deny)."""
    if exit_code != 0:
        return False
    if response is None:
        return True
    return response.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"


# ---------------------------------------------------------------------------
# Allow-path tests
# ---------------------------------------------------------------------------


class TestAllowPath:
    """Hook emits allow when contrarian was properly invoked."""

    def test_allow_when_contrarian_followed_prior_exit_plan(self):
        path = create_transcript(
            [make_exit_plan_entry(), make_task_entry("contrarian-reviewer")]
        )
        try:
            rc, response, _ = run_hook(path)
            assert is_allow(response, rc), f"expected allow, got {response!r}"
        finally:
            os.unlink(path)

    def test_allow_bootstrap_when_no_prior_exit_plan(self):
        """No prior ExitPlanMode means this is the session's first plan — allow."""
        path = create_transcript([make_task_entry("some-other-agent")])
        try:
            rc, response, stderr = run_hook(path)
            assert is_allow(response, rc), f"expected bootstrap allow, got {response!r}"
            assert "bootstrap" in stderr.lower()
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Deny-path tests
# ---------------------------------------------------------------------------


class TestDenyPath:
    """Hook emits deny when contrarian is missing."""

    def test_deny_when_prior_exit_plan_and_no_contrarian(self):
        path = create_transcript([make_exit_plan_entry()])
        try:
            rc, response, _ = run_hook(path)
            assert is_deny(response), f"expected deny, got {response!r}"
            reason = response["hookSpecificOutput"]["permissionDecisionReason"]
            assert "contrarian-reviewer" in reason
        finally:
            os.unlink(path)

    def test_deny_message_quality(self):
        """Deny message leads with preferred remediation, not escape hatch."""
        path = create_transcript([make_exit_plan_entry()])
        try:
            _, response, _ = run_hook(path)
            reason = response["hookSpecificOutput"]["permissionDecisionReason"]
            reason_lc = reason.lower()
            # Assert preferred remediation (invoke contrarian) appears before
            # the structural bypass env var — so users don't default to bypass.
            invoke_idx = reason_lc.find("invoke")
            skip_idx = reason_lc.find("plan_contrarian_skip_hook")
            assert invoke_idx >= 0, (
                "deny message must tell user how to invoke contrarian"
            )
            assert skip_idx >= 0, "deny message must document the escape hatch"
            assert invoke_idx < skip_idx, (
                "deny message should lead with preferred remediation, not bypass"
            )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Env bypass tests
# ---------------------------------------------------------------------------


class TestEnvBypasses:
    """PLAN_CONTRARIAN_CONFIRMED (semantic) + PLAN_CONTRARIAN_SKIP_HOOK (structural)."""

    def test_semantic_bypass_allows_without_contrarian(self):
        path = create_transcript([make_exit_plan_entry()])
        try:
            rc, response, stderr = run_hook(
                path, env_overrides={"PLAN_CONTRARIAN_CONFIRMED": "1"}
            )
            assert is_allow(response, rc), f"expected allow, got {response!r}"
            assert "SEMANTIC BYPASS" in stderr
        finally:
            os.unlink(path)

    def test_structural_bypass_allows_and_logs_audit(self):
        path = create_transcript([make_exit_plan_entry()])
        try:
            rc, response, stderr = run_hook(
                path, env_overrides={"PLAN_CONTRARIAN_SKIP_HOOK": "1"}
            )
            assert is_allow(response, rc), f"expected allow, got {response!r}"
            assert "STRUCTURAL BYPASS" in stderr
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Payload / transcript failure tests
# ---------------------------------------------------------------------------


class TestPayloadFailures:
    """Hook fails closed on malformed payload or missing transcript."""

    def test_deny_when_transcript_path_missing_from_payload(self):
        """No transcript_path in JSON payload → fail-closed deny with distinct message."""
        rc, response, _ = run_hook(None)  # run_hook(None) omits transcript_path field
        assert is_deny(response), f"expected deny, got {response!r}"
        reason = response["hookSpecificOutput"]["permissionDecisionReason"]
        assert (
            "missing transcript_path" in reason.lower() or "malformed" in reason.lower()
        )

    def test_deny_when_transcript_file_absent(self):
        """transcript_path provided but file doesn't exist → fail-closed deny."""
        rc, response, _ = run_hook("/nonexistent/transcript.jsonl")
        assert is_deny(response), f"expected deny, got {response!r}"
        reason = response["hookSpecificOutput"]["permissionDecisionReason"]
        assert "not found" in reason.lower() or "first action" in reason.lower()


# ---------------------------------------------------------------------------
# Substring false-match guard
# ---------------------------------------------------------------------------


class TestFalseMatchGuard:
    """Transcript containing 'contrarian-reviewer' in tool_result text but
    NOT as a Task invocation → hook must deny (scanner parses tool_use, not substring)."""

    def test_deny_on_file_read_mentioning_contrarian(self):
        fake_read = {
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "content": (
                            "BACKLOG.md: ...contrarian-reviewer was invoked "
                            "in session 121... contrarian-reviewer appears "
                            "multiple times in this file..."
                        ),
                    }
                ],
            }
        }
        path = create_transcript([make_exit_plan_entry(), fake_read])
        try:
            _, response, _ = run_hook(path)
            assert is_deny(response), (
                f"substring match should not satisfy contrarian check; got {response!r}"
            )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Debug-mode + audit-log + timeout-binary-absent tests (post-commit double-check)
# ---------------------------------------------------------------------------


class TestDebugMode:
    """PLAN_CONTRARIAN_DEBUG=true emits [plan-contrarian-gate] traces to stderr."""

    def test_debug_mode_emits_stderr_traces(self, tmp_path):
        path = create_transcript(
            [make_exit_plan_entry(), make_task_entry("contrarian-reviewer")]
        )
        try:
            rc, _, stderr = run_hook(
                path,
                env_overrides={
                    "PLAN_CONTRARIAN_DEBUG": "true",
                    "HOME": str(tmp_path),
                },
            )
            assert rc == 0, f"hook should exit 0 on allow, got {rc}"
            assert "[plan-contrarian-gate]" in stderr, (
                f"expected [plan-contrarian-gate] prefix in stderr with DEBUG=true, got: {stderr!r}"
            )
        finally:
            os.unlink(path)


class TestAuditLog:
    """Hook writes audit-log entries for deny, semantic-bypass, structural-bypass.
    Supports V-006 instrumentation (hook-denial rate trending to zero over sessions)."""

    def test_deny_writes_audit_entry(self, tmp_path):
        path = create_transcript([make_exit_plan_entry()])
        try:
            rc, response, _ = run_hook(path, env_overrides={"HOME": str(tmp_path)})
            assert is_deny(response), f"expected deny, got {response!r}"
            log_file = tmp_path / ".context-engine" / "plan-contrarian-denies.log"
            assert log_file.exists(), "deny should create audit log"
            content = log_file.read_text()
            assert " deny " in content, f"deny tag missing from audit log: {content!r}"
        finally:
            os.unlink(path)

    def test_semantic_bypass_writes_audit_entry(self, tmp_path):
        path = create_transcript([make_exit_plan_entry()])
        try:
            rc, _, _ = run_hook(
                path,
                env_overrides={
                    "PLAN_CONTRARIAN_CONFIRMED": "1",
                    "HOME": str(tmp_path),
                },
            )
            assert rc == 0
            log_file = tmp_path / ".context-engine" / "plan-contrarian-denies.log"
            assert log_file.exists(), "semantic bypass should create audit log"
            content = log_file.read_text()
            assert "semantic-bypass" in content, (
                f"semantic-bypass tag missing: {content!r}"
            )
        finally:
            os.unlink(path)

    def test_log_rotation_caps_at_100kb(self, tmp_path):
        """Audit log rotates (via tail -n 500) when it exceeds 100KB.

        Mirrors pre-test-oom-gate.sh rotation pattern — prevents unbounded
        growth if bypass envs are left set in a shell rc (per post-commit
        security-audit MEDIUM finding).
        """
        home = tmp_path
        ce_dir = home / ".context-engine"
        ce_dir.mkdir(parents=True)
        log_file = ce_dir / "plan-contrarian-denies.log"
        # Seed with >100KB AND > 500 lines so `tail -n 500` actually trims.
        # 2000 lines × ~60 bytes = ~120KB; after rotation retain last 500 lines.
        filler_line = "x" * 59 + "\n"
        log_file.write_text(filler_line * 2000)  # ~120KB, 2000 lines
        initial_size = log_file.stat().st_size
        assert initial_size > 100_000, "test fixture must exceed cap threshold"

        path = create_transcript([make_exit_plan_entry()])
        try:
            run_hook(path, env_overrides={"HOME": str(home)})
            final_size = log_file.stat().st_size
            assert final_size < initial_size, (
                f"log should have been rotated; initial={initial_size}, final={final_size}"
            )
        finally:
            os.unlink(path)


class TestTimeoutBinaryFallback:
    """If neither `timeout` nor `gtimeout` is in PATH, hook logs a WARNING
    to stderr and runs scanner unguarded (graceful degradation per
    CFR §9.3.10 step 5 self-diagnosing fallback)."""

    def test_warning_when_no_timeout_binary(self, tmp_path):
        python3 = shutil.which("python3")
        assert python3, "test requires python3 to be discoverable"
        python_dir = str(Path(python3).parent)
        # Minimal PATH — excludes coreutils locations (no /opt/homebrew/bin or /opt/local/bin)
        minimal_path = f"{python_dir}:/usr/bin:/bin"

        path = create_transcript(
            [make_exit_plan_entry(), make_task_entry("contrarian-reviewer")]
        )
        try:
            _, _, stderr = run_hook(
                path,
                env_overrides={"PATH": minimal_path, "HOME": str(tmp_path)},
            )
            if "WARNING" in stderr:
                assert "timeout" in stderr.lower() or "coreutils" in stderr.lower(), (
                    f"warning should mention timeout/coreutils: {stderr!r}"
                )
            else:
                # Host PATH includes timeout (e.g., Linux /usr/bin/timeout) —
                # fallback branch not exercised on this host.
                pytest.skip(
                    "PATH includes timeout binary; fallback warning branch not reachable"
                )
        finally:
            os.unlink(path)
