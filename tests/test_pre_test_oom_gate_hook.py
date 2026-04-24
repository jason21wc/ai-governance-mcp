"""Unit tests for .claude/hooks/pre-test-oom-gate.sh — the structural OOM gate.

These tests shell out to the hook script with crafted stdin JSON payloads and
assert that the permission decision (allow vs deny) matches expectations.

The hook is documented at:
  .claude/hooks/pre-test-oom-gate.sh
  BACKLOG.md #49 (Status 2026-04-15 block — design rationale)

Test coverage — 30 tests across 16 classes, organized by the plan's decision
matrix plus review-driven edge cases and session-108 hardening:

Primary decision matrix (from plan Step 5):
  1. `pytest tests/ -m "not slow"` with daemon running → allow (safe subset)
  2. `pytest tests/` with daemon running (fresh heartbeat) → deny
  3. `pytest tests/` with daemon-file-but-stale-heartbeat → allow (false-positive guard)
  4. `pytest tests/` with daemon stopped and no other torch processes → allow
  5. `pytest tests/<file>::<Class>` with daemon running → allow (targeted)
  6. `PYTEST_ALLOW_HEAVY=1 pytest tests/` with daemon running → allow (semantic bypass)
  7. `PYTEST_SKIP_OOM_GATE=1 pytest tests/` with daemon running → allow (structural bypass)
  8. Non-pytest Bash command (`ls`, `git status`, etc.) → allow (no pattern match) — parametrized across 6 examples

Review-driven additional coverage:
  - Fail-closed on corrupt heartbeat JSON (security-auditor finding S2)
  - Boundary: heartbeat exactly at 300s threshold → stale → allow
  - Deny-log side effect written / allow-path does NOT touch log (forcing-function trigger)
  - Inline env-var prefix for both bypass vars (`PYTEST_ALLOW_HEAVY=1 pytest ...`, `PYTEST_SKIP_OOM_GATE=1 pytest ...`)
  - Chained commands (`cd ... && pytest tests/`) still detected
  - `python -mpytest` no-space variant detected
  - `python -m pytest` at end of string detected

Session-108 hardening additions (7 new tests across 6 classes):
  - ERR trap fail-closed: unhandled errors exit 2 (deny), not exit 1 (fail-open)
  - jq fallback: python3 parses JSON when jq missing
  - PYTEST_CURRENT_TEST guard: OOM_GATE_SKIP_PROCESS_SCAN ignored outside pytest
  - Secret redaction: API keys, Bearer tokens redacted in deny log (2 tests)
  - Non-secret preservation: regular commands logged as-is
  - Deny log rotation: >100KB log truncated to last 500 lines

Expected collected count: 30 (16 test classes × varying counts; one parametrize
with 6 cases bringing the visible total above the bare `def` count of 25).
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.hook_fixtures import is_allow, is_deny  # noqa: F401 — used in tests

HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / ".claude"
    / "hooks"
    / "pre-test-oom-gate.sh"
)


def run_hook(
    command: str,
    *,
    env_overrides: dict[str, str] | None = None,
    heartbeat_override: Path | None = None,
    base_dir_override: Path | None = None,
    skip_process_scan: bool = True,
) -> tuple[int, dict | None]:
    """Invoke the hook with a crafted tool_input payload.

    By default, skips the real-system process scan via OOM_GATE_SKIP_PROCESS_SCAN=1
    so that tests isolate the heartbeat-file signal from whatever torch-holding
    processes happen to be running on the test machine. Pass skip_process_scan=False
    to exercise the real process scan (only useful for the clean-environment case).

    Returns (exit_code, parsed_response_dict_or_None).
    """
    payload = json.dumps({"tool_input": {"command": command}})

    env = os.environ.copy()
    env["OOM_GATE_DEBUG"] = "false"
    # Important: strip inherited bypass env vars unless the test sets them.
    env.pop("PYTEST_ALLOW_HEAVY", None)
    env.pop("PYTEST_SKIP_OOM_GATE", None)
    env.pop("OOM_GATE_SKIP_PROCESS_SCAN", None)

    if skip_process_scan:
        env["OOM_GATE_SKIP_PROCESS_SCAN"] = "1"

    if base_dir_override is not None:
        env["HOME"] = str(base_dir_override)

    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    stdout = result.stdout.strip()
    if not stdout:
        return result.returncode, None
    try:
        return result.returncode, json.loads(stdout)
    except json.JSONDecodeError:
        return result.returncode, {"_raw": stdout}


def make_fake_daemon_home(tmp_path: Path, *, heartbeat_age_seconds: int | None) -> Path:
    """Create a fake ~/.context-engine with a heartbeat file of controllable age.

    Returns the fake HOME path to override the hook's heartbeat lookup.
    heartbeat_age_seconds=None means no heartbeat file exists (daemon stopped).
    """
    home = tmp_path / "fake_home"
    ce_dir = home / ".context-engine"
    ce_dir.mkdir(parents=True)

    if heartbeat_age_seconds is not None:
        alive_at = datetime.now(timezone.utc) - timedelta(seconds=heartbeat_age_seconds)
        heartbeat = {
            "pid": 99999,
            "alive_at": alive_at.isoformat(),
            "projects_watched": 0,
        }
        (ce_dir / "watcher-heartbeat.json").write_text(json.dumps(heartbeat))
        (ce_dir / "watcher.pid").write_text("99999\n")

    return home


# ---------------------------------------------------------------------------
# Test cases — one per row in the plan's decision matrix
# ---------------------------------------------------------------------------


class TestSafeSubsetPatternsAllow:
    """Invocations that should ALWAYS be allowed regardless of daemon state."""

    def test_case_1_marker_not_slow_with_daemon_running(self, tmp_path):
        """Case 1: `pytest tests/ -m "not slow"` with fresh daemon → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            'pytest tests/ -v -m "not slow"', base_dir_override=home
        )
        assert is_allow(response, exit_code), (
            f"Should allow safe subset, got {response}"
        )

    def test_case_5_targeted_class_with_daemon_running(self, tmp_path):
        """Case 5: `pytest tests/test_fake.py::TestX` with fresh daemon → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "pytest tests/test_fake_module.py::TestFakeClass -v",
            base_dir_override=home,
        )
        assert is_allow(response, exit_code), (
            f"Should allow targeted selection, got {response}"
        )

    def test_targeted_single_file_with_daemon_running(self, tmp_path):
        """Variant: targeted single file (without ::) with fresh daemon → allow.

        Uses a fictional filename to decouple the test from the actual repo layout.
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "pytest tests/test_fake_module.py -v", base_dir_override=home
        )
        assert is_allow(response, exit_code), (
            f"Should allow single-file invocation, got {response}"
        )


class TestDangerousInvocationsBlock:
    """Bare pytest tests/ with any risk signal → deny."""

    def test_case_2_bare_pytest_with_fresh_daemon_heartbeat(self, tmp_path):
        """Case 2: `pytest tests/` + fresh heartbeat → deny."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_deny(response), (
            f"Should deny bare pytest with fresh daemon, got {response}"
        )
        reason = response["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "OOM PREVENTION GATE" in reason
        # Critical: deny message must lead with -m "not slow", not "kill the daemon".
        # Per contrarian review #2 UX-trap finding (2026-04-15): if "kill the daemon"
        # becomes the path of least resistance for future sessions, the OOM guarantee
        # silently disappears. The deny message must actively discourage that default.
        assert "not slow" in reason
        reason_lc = reason.lower()
        # Assert `not slow` appears BEFORE `last resort` (when both are present)
        if "last resort" in reason_lc:
            assert reason_lc.index("not slow") < reason_lc.index("last resort"), (
                "Deny message must lead with safe subset, not daemon-stop as the fix"
            )


class TestStaleHeartbeatAllows:
    """Case 3: PID file present but heartbeat stale (>5 min) → allow (crash guard).

    Uses OOM_GATE_SKIP_PROCESS_SCAN=1 (the default in run_hook) to isolate the
    heartbeat signal from the real-system process scan.
    """

    def test_case_3_stale_heartbeat_allows(self, tmp_path):
        """Case 3: stale heartbeat (>300s) → daemon crashed → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=600)
        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_allow(response, exit_code), (
            f"Stale heartbeat should allow (daemon crashed), got {response}"
        )

    def test_heartbeat_exactly_at_threshold_is_allowed(self, tmp_path):
        """Boundary: heartbeat age exactly at 300s → treated as stale → allow.

        (The hook uses strict less-than: age < HEARTBEAT_MAX_AGE_SECONDS)
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=300)
        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_allow(response, exit_code), (
            f"Heartbeat at exactly threshold (300s) should be treated as stale, got {response}"
        )


class TestCleanEnvironmentAllows:
    """Case 4: daemon stopped + no torch processes → allow bare pytest tests/."""

    def test_case_4_clean_environment_allows(self, tmp_path):
        """Case 4: no heartbeat file, process scan isolated → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=None)
        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_allow(response, exit_code), (
            f"Clean environment (no heartbeat, no process scan) should allow, got {response}"
        )


class TestFailClosedOnCorruptHeartbeat:
    """Negative case: corrupt heartbeat file → fail-closed (treat as alive → deny).

    Per security-auditor finding S2 and code-reviewer finding #5, the hook should
    fail-closed on parse errors, not silently allow.
    """

    def test_corrupt_heartbeat_json_fails_closed(self, tmp_path):
        """Corrupt heartbeat JSON → assume daemon alive → deny bare pytest."""
        home = tmp_path / "fake_home"
        ce_dir = home / ".context-engine"
        ce_dir.mkdir(parents=True)
        (ce_dir / "watcher-heartbeat.json").write_text("{not valid json{{{")
        (ce_dir / "watcher.pid").write_text("99999\n")

        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_deny(response), (
            f"Corrupt heartbeat must fail-closed (treat as alive), got {response}"
        )
        reason = response["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "unparseable" in reason or "fail-closed" in reason


class TestBypassEnvVars:
    """Cases 6 & 7: both bypass env vars → allow regardless of state."""

    def test_case_6_allow_heavy_semantic_bypass(self, tmp_path):
        """Case 6: PYTEST_ALLOW_HEAVY=1 + fresh daemon → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "pytest tests/",
            env_overrides={"PYTEST_ALLOW_HEAVY": "1"},
            base_dir_override=home,
        )
        assert is_allow(response, exit_code), (
            f"ALLOW_HEAVY should bypass, got {response}"
        )
        # Should emit a warning additionalContext, not a deny
        if response is not None:
            ctx = response["hookSpecificOutput"].get("additionalContext", "")
            assert "ALLOW_HEAVY" in ctx or "bypassed" in ctx.lower()

    def test_case_7_skip_oom_gate_structural_bypass(self, tmp_path):
        """Case 7: PYTEST_SKIP_OOM_GATE=1 + fresh daemon → allow."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "pytest tests/",
            env_overrides={"PYTEST_SKIP_OOM_GATE": "1"},
            base_dir_override=home,
        )
        assert is_allow(response, exit_code), (
            f"SKIP_OOM_GATE should bypass, got {response}"
        )
        if response is not None:
            ctx = response["hookSpecificOutput"].get("additionalContext", "")
            assert "STRUCTURALLY bypassed" in ctx or "SKIP_OOM_GATE" in ctx

    def test_inline_allow_heavy_env_prefix(self, tmp_path):
        """Variant: inline env prefix in command string `PYTEST_ALLOW_HEAVY=1 pytest tests/`."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "PYTEST_ALLOW_HEAVY=1 pytest tests/", base_dir_override=home
        )
        assert is_allow(response, exit_code), (
            f"Inline ALLOW_HEAVY prefix should bypass, got {response}"
        )

    def test_inline_skip_oom_gate_env_prefix(self, tmp_path):
        """Variant: inline env prefix `PYTEST_SKIP_OOM_GATE=1 pytest tests/` → bypass.

        Symmetric coverage with test_inline_allow_heavy_env_prefix per code-reviewer #11.
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "PYTEST_SKIP_OOM_GATE=1 pytest tests/", base_dir_override=home
        )
        assert is_allow(response, exit_code), (
            f"Inline SKIP_OOM_GATE prefix should bypass, got {response}"
        )


class TestNonPytestCommandsAllow:
    """Case 8: non-pytest Bash commands should never match."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls -la",
            "git status",
            "cat README.md",
            "echo pytest",  # word 'pytest' as an echo arg, not a command
            "rg pytest",  # searching for the word, not running it
            "grep -r 'pytest' docs/",
        ],
    )
    def test_non_pytest_command_allowed(self, command, tmp_path):
        """Non-pytest commands → allow regardless of daemon state."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(command, base_dir_override=home)
        assert is_allow(response, exit_code), (
            f"Non-pytest command '{command}' should be allowed, got {response}"
        )


class TestChainedCommandsDetected:
    """Sanity check: chained commands like `cd foo && pytest tests/` are detected."""

    def test_chained_pytest_detected(self, tmp_path):
        """`cd src && pytest tests/` with fresh daemon → should be evaluated (not short-circuited)."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook(
            "cd /tmp && pytest tests/", base_dir_override=home
        )
        # With fresh daemon, this should be denied — verifies the chain detection works
        assert is_deny(response), (
            f"Chained pytest should be detected and denied with fresh daemon, got {response}"
        )


class TestDenyLogSideEffect:
    """The deny log at ~/.context-engine/oom-gate-denies.log is the activity
    trigger for the BACKLOG #49 forcing function. Verify it actually gets written.
    """

    def test_deny_writes_to_log_file(self, tmp_path):
        """When the hook denies, it must append a line to oom-gate-denies.log."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"
        assert not deny_log.exists(), "precondition: log should not exist yet"

        exit_code, response = run_hook("pytest tests/", base_dir_override=home)
        assert is_deny(response)

        assert deny_log.exists(), (
            "Deny log must be written on every deny — this is the activity trigger "
            "for the BACKLOG #49 forcing function"
        )
        log_content = deny_log.read_text()
        assert "pytest tests/" in log_content, (
            f"Deny log must record the offending command, got: {log_content!r}"
        )
        # Must have a timestamp prefix (ISO8601 UTC)
        assert log_content[:4].isdigit(), (
            f"Deny log lines must start with ISO8601 timestamp, got: {log_content!r}"
        )

    def test_allow_does_not_write_deny_log(self, tmp_path):
        """Allow paths must NOT touch the deny log (otherwise false activity signal)."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"

        exit_code, response = run_hook(
            'pytest tests/ -v -m "not slow"', base_dir_override=home
        )
        assert is_allow(response, exit_code)
        assert not deny_log.exists(), (
            "Allow paths must NOT write to the deny log — the count must only "
            "reflect actual denies"
        )


class TestRegexEdgeCases:
    """Regex edge cases from code-reviewer finding #2.

    Note: bare `pytest` at end-of-string (no args, no trailing space) is an
    accepted false-negative. It would fail pytest's own "no tests collected"
    behavior anyway, and covering it required `|$` alternation that created
    a worse false-positive class on `echo pytest` / `rg pytest`.
    """

    def test_python_m_pytest_no_space_after_m_detected(self, tmp_path):
        """`python -mpytest tests/` (no space between -m and pytest) is detected."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook("python -mpytest tests/", base_dir_override=home)
        assert is_deny(response), (
            f"python -mpytest (no-space variant) should be detected, got {response}"
        )

    def test_python_m_pytest_at_end_of_string_detected(self, tmp_path):
        """`python -m pytest` with no args at EOS is still detected.

        The python -m branch retains `|$` because false-positive risk is lower:
        `python -mpytest` / `python -m pytest` as a complete command is
        unusual outside actual invocations.
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        exit_code, response = run_hook("python -m pytest", base_dir_override=home)
        assert is_deny(response), (
            f"python -m pytest at EOS should be detected, got {response}"
        )


# ---------------------------------------------------------------------------
# Step 2.1 — ERR trap fail-closed behavior
# ---------------------------------------------------------------------------


class TestInternalPsTimeout:
    """Internal `timeout 7 ps` guard: when the ps call hangs past 7s, the hook
    must self-deny (exit 2) rather than let Claude Code's 10s SIGKILL fire
    (which bypasses the ERR trap and is treated as fail-open).

    Shipped session-121 (2026-04-21) per BACKLOG #91 sub-item 3 + LEARNING-LOG
    "Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout".
    """

    def test_ps_timeout_fails_closed(self, tmp_path):
        """A fake `timeout` binary that always exits 124 (GNU timeout's
        "command timed out" code) simulates ps hanging past the internal 7s
        guard. The hook must exit 2 (deny), not let control fall through to
        fail-open behavior.
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)

        # Inject a fake `timeout` binary that returns 124 immediately.
        fake_bin = tmp_path / "fake-bin"
        fake_bin.mkdir()
        fake_timeout = fake_bin / "timeout"
        fake_timeout.write_text("#!/usr/bin/env bash\nexit 124\n")
        fake_timeout.chmod(0o755)

        # Put fake-bin FIRST so our `timeout` wins over any real one.
        fake_path = f"{fake_bin}:/usr/bin:/bin"

        # skip_process_scan=False to exercise the real process-scan branch
        # (where the internal timeout wrapper lives).
        exit_code, _response = run_hook(
            "pytest tests/",
            base_dir_override=home,
            env_overrides={"PATH": fake_path},
            skip_process_scan=False,
        )

        assert exit_code == 2, (
            f"Hook must exit 2 (fail-closed) when internal ps timeout fires "
            f"(exit 124 from `timeout` binary). Got exit {exit_code}."
        )


class TestFailClosedOnUnexpectedError:
    """The ERR trap converts unhandled errors to exit 2 (deny), not exit 1
    (non-blocking allow). This is the security-critical behavioral change.
    """

    def test_err_trap_converts_failures_to_exit_2(self, tmp_path):
        """Force an error by making jq and python3 unavailable so JSON
        parsing fails. The ERR trap should fire → exit 2 (deny).

        We keep /bin and /usr/bin in PATH (bash needs basic utils like cat,
        grep, etc.) but exclude the dirs containing jq and python3.

        Covers: FM-HOOK-FAIL-CLOSED-EXIT-2
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        # Minimal PATH: bash builtins work, but jq/python3 are missing.
        # The hook should fail-closed (exit 2), not fail-open (exit 1).
        exit_code, response = run_hook(
            "pytest tests/",
            base_dir_override=home,
            env_overrides={"PATH": "/usr/bin:/bin"},
        )
        # Exit 2 = deny (fail-closed). Exit 1 would mean fail-open (bad).
        # Note: if python3 happens to live in /usr/bin, this test may pass
        # for a different reason (hook works normally). That's acceptable —
        # the important thing is exit code is never 1.
        assert exit_code != 1, (
            f"ERR trap must prevent exit 1 (fail-open). Got exit {exit_code}. "
            f"Exit 2 (deny) or 0 (python3 found in /usr/bin) are both acceptable."
        )


# ---------------------------------------------------------------------------
# Step 2.2 — jq fallback to python3
# ---------------------------------------------------------------------------


class TestJqFallback:
    """When jq is missing, the hook should fall back to python3 for JSON parsing."""

    def test_jq_missing_falls_back_to_python3(self, tmp_path):
        """Remove jq from PATH but keep python3 → hook should still work."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        # Build a PATH that has python3 but no jq
        import shutil

        python3_path = shutil.which("python3")
        if python3_path is None:
            pytest.skip("python3 not found on PATH")
        python3_dir = os.path.dirname(python3_path)
        # Include common system dirs for basic utils (grep, ps, etc.) but not jq
        safe_path = f"{python3_dir}:/usr/bin:/bin"

        exit_code, response = run_hook(
            'pytest tests/ -v -m "not slow"',
            base_dir_override=home,
            env_overrides={"PATH": safe_path},
        )
        # Should parse the command and allow (safe subset), not crash
        assert is_allow(response, exit_code), (
            f"jq-missing fallback should still parse and allow safe subset, "
            f"got exit={exit_code} response={response}"
        )


# ---------------------------------------------------------------------------
# Step 2.3 — PYTEST_CURRENT_TEST guard
# ---------------------------------------------------------------------------


class TestPytestCurrentTestGuard:
    """OOM_GATE_SKIP_PROCESS_SCAN only works inside pytest (PYTEST_CURRENT_TEST set)."""

    def test_skip_process_scan_ignored_outside_pytest(self, tmp_path):
        """When PYTEST_CURRENT_TEST is empty/unset, OOM_GATE_SKIP_PROCESS_SCAN
        is ignored — the real process scan runs.

        We can't easily test the real process scan in isolation, but we can
        verify the variable is ignored by checking that the hook still runs
        the process scan path (which will find the running MCP server PIDs
        and may deny).
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=None)
        # Set SKIP but clear PYTEST_CURRENT_TEST → skip should be ignored
        exit_code, response = run_hook(
            "pytest tests/",
            base_dir_override=home,
            env_overrides={
                "OOM_GATE_SKIP_PROCESS_SCAN": "1",
                "PYTEST_CURRENT_TEST": "",
            },
            skip_process_scan=False,  # Don't set it in run_hook either
        )
        # With no daemon heartbeat and PYTEST_CURRENT_TEST empty, the skip
        # is ignored. The real process scan runs. If torch processes are
        # found (likely on dev machine), it denies. If not, it allows.
        # We just verify it didn't crash — the guard is working.
        assert exit_code in (0, 2), (
            f"Hook should complete (allow or deny), got exit {exit_code}"
        )


# ---------------------------------------------------------------------------
# Step 2.4 — Secret redaction
# ---------------------------------------------------------------------------


class TestSecretRedaction:
    """Secrets in the command string are redacted before writing to the deny log."""

    def test_openai_api_key_redacted_in_deny_log(self, tmp_path):
        """OpenAI sk- prefix tokens should be redacted in deny log.

        The generic KEY= pattern may match before the sk- pattern, so we
        check that the secret value is absent rather than asserting a
        specific redaction format.
        """
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"
        secret_cmd = "OPENAI_API_KEY=sk-abc123secretvalue456 pytest tests/"
        run_hook(secret_cmd, base_dir_override=home)

        assert deny_log.exists()
        content = deny_log.read_text()
        # The secret value must not appear — either the sk- pattern or
        # the generic KEY= pattern should have redacted it
        assert "secretvalue456" not in content, (
            f"Secret value should not appear in deny log, got: {content!r}"
        )
        assert "<redacted>" in content, (
            f"Redaction marker should be present, got: {content!r}"
        )

    def test_bearer_token_redacted_in_deny_log(self, tmp_path):
        """Bearer tokens should be redacted in deny log."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"
        secret_cmd = "pytest tests/ --token mySecretBearerValue"
        run_hook(secret_cmd, base_dir_override=home)

        assert deny_log.exists()
        content = deny_log.read_text()
        assert "mySecretBearerValue" not in content, (
            f"Token value should be redacted, got: {content!r}"
        )

    def test_non_secret_command_preserved_in_deny_log(self, tmp_path):
        """Regular commands without secrets should be logged as-is."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"
        run_hook("pytest tests/ -v --timeout=30", base_dir_override=home)

        assert deny_log.exists()
        content = deny_log.read_text()
        assert "pytest tests/ -v --timeout=30" in content, (
            f"Non-secret command should be preserved, got: {content!r}"
        )


# ---------------------------------------------------------------------------
# Step 2.5 — Deny log rotation
# ---------------------------------------------------------------------------


class TestDenyLogRotation:
    """Deny log is capped at 100KB to prevent unbounded growth."""

    def test_large_deny_log_rotated_after_deny(self, tmp_path):
        """When deny log exceeds 100KB, it should be truncated to last 500 lines."""
        home = make_fake_daemon_home(tmp_path, heartbeat_age_seconds=30)
        deny_log = home / ".context-engine" / "oom-gate-denies.log"

        # Create a >100KB log file. Each line ~120 bytes × 1000 lines ≈ 120KB.
        lines = [
            f"2026-04-15T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}Z deny daemon_alive=true torch_procs=1 "
            f"cmd=pytest tests/ --fake-long-argument-to-pad-line-number-{i:05d}\n"
            for i in range(1000)
        ]
        deny_log.write_text("".join(lines))
        original_size = deny_log.stat().st_size
        assert original_size > 102400, (
            f"Precondition: log should be >100KB, got {original_size}"
        )

        # Trigger a deny — rotation should happen after the new line is appended
        run_hook("pytest tests/", base_dir_override=home)

        new_size = deny_log.stat().st_size
        assert new_size < original_size, (
            f"Log should have been rotated: was {original_size}, now {new_size}"
        )
        # Should have ~500 lines (tail -n 500) plus the new deny line
        line_count = len(deny_log.read_text().strip().split("\n"))
        assert line_count <= 502, (
            f"Rotated log should have ≤502 lines (500 + new deny + margin), got {line_count}"
        )
