"""Tests for Claude Code hook scripts.

Subprocess-based tests that verify hook behavior for governance and
context engine compliance enforcement.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.hook_fixtures import (  # noqa: F401 — imported for use in tests
    create_transcript,
    make_exit_plan_entry,
    make_task_entry,
)


# Hook script paths
PROJECT_DIR = Path(__file__).parent.parent
PRETOOL_HOOK = PROJECT_DIR / ".claude" / "hooks" / "pre-tool-governance-check.sh"
PROMPT_HOOK = PROJECT_DIR / ".claude" / "hooks" / "user-prompt-governance-inject.sh"
SCANNER = PROJECT_DIR / ".claude" / "hooks" / "scan_transcript.py"


def make_tool_use_entry(tool_name: str) -> dict:
    """Create a transcript entry for a tool_use call."""
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "test-id",
                    "name": tool_name,
                    "input": {"planned_action": "test"},
                }
            ],
        }
    }


def make_filler_entry() -> dict:
    """Create a non-tool-use transcript entry (filler for recency window tests)."""
    return {
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "filler"}],
        }
    }


def run_hook(
    script: Path, stdin_data: str, env_overrides: dict | None = None
) -> subprocess.CompletedProcess:
    """Run a hook script via subprocess.

    Returns CompletedProcess with stdout, stderr, returncode.
    """
    env = os.environ.copy()
    # Suppress debug logging unless explicitly testing it
    env["GOVERNANCE_HOOK_DEBUG"] = "false"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(script)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


# ---------------------------------------------------------------------------
# Shared Scanner Tests
# ---------------------------------------------------------------------------


class TestScannerModule:
    """Tests for scan_transcript.py shared scanner."""

    def test_scanner_finds_both(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
                make_tool_use_entry("mcp__context-engine__query_project"),
            ]
        )
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "both"
        finally:
            os.unlink(transcript_path)

    def test_scanner_finds_gov_only(self):
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__ai-governance__evaluate_governance")]
        )
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "gov_only"
        finally:
            os.unlink(transcript_path)

    def test_scanner_finds_ce_only(self):
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "ce_only"
        finally:
            os.unlink(transcript_path)

    def test_scanner_finds_neither(self):
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "neither"
        finally:
            os.unlink(transcript_path)

    def test_scanner_recency_window_includes_recent(self):
        """Governance call within window is found."""
        entries = [make_filler_entry() for _ in range(5)]
        entries.append(make_tool_use_entry("mcp__ai-governance__evaluate_governance"))
        entries.append(make_tool_use_entry("mcp__context-engine__query_project"))
        transcript_path = create_transcript(entries)
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                    "10",  # window of 10 lines
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "both"
        finally:
            os.unlink(transcript_path)

    def test_scanner_recency_window_excludes_old(self):
        """Governance call outside window is NOT found."""
        entries = [
            make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            make_tool_use_entry("mcp__context-engine__query_project"),
        ]
        # Add enough filler to push tool calls outside the window
        entries.extend([make_filler_entry() for _ in range(20)])
        transcript_path = create_transcript(entries)
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                    "5",  # window of 5 lines — tool calls are at lines 1-2
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "neither"
        finally:
            os.unlink(transcript_path)

    def test_scanner_window_zero_scans_all(self):
        """Window size 0 scans entire transcript."""
        entries = [
            make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            make_tool_use_entry("mcp__context-engine__query_project"),
        ]
        entries.extend([make_filler_entry() for _ in range(50)])
        transcript_path = create_transcript(entries)
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                    "0",  # 0 = scan all
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "both"
        finally:
            os.unlink(transcript_path)

    def test_scanner_non_numeric_window_defaults_to_zero(self):
        """Non-numeric window argument defaults to 0 (scan all)."""
        entries = [
            make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            make_tool_use_entry("mcp__context-engine__query_project"),
        ]
        entries.extend([make_filler_entry() for _ in range(50)])
        transcript_path = create_transcript(entries)
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "mcp__ai-governance__evaluate_governance",
                    "mcp__context-engine__query_project",
                    transcript_path,
                    "not_a_number",  # invalid window
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Should fall back to 0 (scan all) and find both
            assert result.stdout.strip() == "both"
            assert result.returncode == 0
        finally:
            os.unlink(transcript_path)

    def test_scanner_no_args_returns_neither(self):
        """No arguments returns 'neither' gracefully."""
        result = subprocess.run(
            ["python3", str(SCANNER)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.stdout.strip() == "neither"
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Scanner: --contrarian-after-last-plan mode
# ---------------------------------------------------------------------------


def make_agent_entry(subagent_type: str) -> dict:
    """Create an Agent tool_use transcript entry (Claude Code's Agent-tool variant of Task).

    Same shape as make_task_entry but with name='Agent'. Added session-123 to
    cover the Agent-tool invocation form alongside Task; scanner must accept both.
    """
    entry = make_task_entry(subagent_type)
    entry["message"]["content"][0]["name"] = "Agent"
    entry["message"]["content"][0]["id"] = "agent-id"
    return entry


def make_tool_result_entry(text: str) -> dict:
    """Create a tool_result entry containing arbitrary text.

    Used to simulate file-read results whose content mentions 'contrarian-reviewer'
    without being an actual Task invocation — verifies parse-based matching.
    """
    return {
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "content": text}],
        }
    }


def _run_contrarian_scan(transcript_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "python3",
            str(SCANNER),
            "--contrarian-after-last-plan",
            transcript_path,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestContrarianAfterLastPlan:
    """Tests for scan_contrarian_after_last_plan mode used by pre-exit-plan-mode-gate hook."""

    def test_allow_when_contrarian_follows_prior_exit_plan(self):
        """Contrarian Task tool_use after a prior ExitPlanMode → allow."""
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_task_entry("contrarian-reviewer"),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "allow"
            assert result.returncode == 0
        finally:
            os.unlink(transcript_path)

    def test_deny_when_prior_exit_plan_but_no_contrarian_after(self):
        """Prior ExitPlanMode exists, no contrarian since → deny."""
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_filler_entry(),
                make_filler_entry(),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "deny"
        finally:
            os.unlink(transcript_path)

    def test_bootstrap_when_no_prior_exit_plan(self):
        """No ExitPlanMode in transcript → bootstrap (first plan of session)."""
        transcript_path = create_transcript(
            [
                make_filler_entry(),
                make_task_entry("some-other-subagent"),
                make_filler_entry(),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "bootstrap"
        finally:
            os.unlink(transcript_path)

    def test_deny_when_contrarian_is_stale(self):
        """Contrarian BEFORE the most recent ExitPlanMode → deny (stale for new plan)."""
        transcript_path = create_transcript(
            [
                make_task_entry("contrarian-reviewer"),  # for plan 1
                make_exit_plan_entry(),  # plan 1 approved
                make_filler_entry(),  # plan 2 work, no contrarian
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "deny"
        finally:
            os.unlink(transcript_path)

    def test_allow_with_underscore_variant(self):
        """Subagent_type `contrarian_reviewer` (underscore) also counts."""
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_task_entry("contrarian_reviewer"),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "allow"
        finally:
            os.unlink(transcript_path)

    def test_deny_on_substring_false_match(self):
        """Content mentioning 'contrarian-reviewer' (e.g., file read) but no tool_use → deny.

        Guards against false-allows when the assistant reads BACKLOG.md or
        LEARNING-LOG.md (which mention contrarian-reviewer) without actually
        invoking the subagent.

        Covers: FM-SCANNER-SUBSTRING-FALSE-MATCH
        """
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_tool_result_entry(
                    "BACKLOG.md content: ... contrarian-reviewer was invoked "
                    "in prior session ... contrarian-reviewer appears here "
                    "multiple times ..."
                ),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            # Scanner must parse tool_use blocks, not substring match
            assert result.stdout.strip() == "deny"
        finally:
            os.unlink(transcript_path)

    def test_error_when_transcript_missing(self):
        """Non-existent transcript path → error (fail-closed signal for hook)."""
        result = _run_contrarian_scan("/nonexistent/path/transcript.jsonl")
        assert result.stdout.strip() == "error"
        assert result.returncode == 0  # exit 0 always; decision in stdout

    def test_corrupt_jsonl_skipped_gracefully(self):
        """Corrupt JSONL lines are skipped; valid entries still evaluated."""
        # Write a mix of valid and corrupt lines
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(json.dumps(make_exit_plan_entry()) + "\n")
                f.write("{not valid json\n")
                f.write("another {{{corrupt line\n")
                f.write(json.dumps(make_task_entry("contrarian-reviewer")) + "\n")
            result = _run_contrarian_scan(path)
            # Valid entries yielded ExitPlanMode + contrarian after → allow
            assert result.stdout.strip() == "allow"
        finally:
            os.unlink(path)

    def test_allow_with_agent_tool_variant(self):
        """Agent-tool contrarian invocation (same shape as Task, different name) → allow.

        Closes the gap that blocked session-123's first plan approval — Claude
        Code's Agent tool has the same input.subagent_type shape as Task but
        name='Agent'. Scanner must accept both tool names.

        Covers: FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE
        """
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_agent_entry("contrarian-reviewer"),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "allow"
        finally:
            os.unlink(transcript_path)

    def test_allow_with_agent_tool_underscore_variant(self):
        """Agent(subagent_type='contrarian_reviewer') underscore alias also counts.

        Locks the contract that the underscore alias works for Agent just like
        Task. Cheap insurance per contrarian MEDIUM-1, session-123.
        """
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_agent_entry("contrarian_reviewer"),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "allow"
        finally:
            os.unlink(transcript_path)

    def test_deny_when_agent_tool_has_wrong_subagent_type(self):
        """Agent tool after ExitPlanMode but with non-contrarian subagent_type → deny.

        Symmetric negative test per contrarian HIGH-1, session-123: widening the
        name-check to ('Task', 'Agent') without this test would let a regression
        to unconditional-allow pass CI.
        """
        transcript_path = create_transcript(
            [
                make_exit_plan_entry(),
                make_agent_entry("some-other-subagent"),
            ]
        )
        try:
            result = _run_contrarian_scan(transcript_path)
            assert result.stdout.strip() == "deny"
        finally:
            os.unlink(transcript_path)


# ---------------------------------------------------------------------------
# PreToolUse Hook Tests — Hard Mode Default
# ---------------------------------------------------------------------------


class TestPreToolAllowsWhenBothPresent:
    """When both governance and CE calls exist in transcript, hook allows."""

    def test_pretool_allows_when_both_present(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
                make_tool_use_entry("mcp__context-engine__query_project"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            # Should produce no output (silent allow)
            assert result.stdout.strip() == ""
        finally:
            os.unlink(transcript_path)


class TestPreToolDeniesGovernanceMissing:
    """Default hard mode blocks when governance is missing."""

    def test_pretool_denies_governance_missing(self):
        """Hard-mode hook denies when evaluate_governance() not in transcript.

        Covers: FM-HOOK-GOVERNANCE-GATE-REQUIRED
        """
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__context-engine__query_project"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
        finally:
            os.unlink(transcript_path)


class TestPreToolDeniesCEMissing:
    """Default hard mode blocks when CE query is missing."""

    def test_pretool_denies_ce_missing(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                "CONTEXT ENGINE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
        finally:
            os.unlink(transcript_path)


class TestPreToolDeniesBothMissing:
    """Default hard mode blocks when neither tool is found."""

    def test_pretool_denies_both_missing(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("some_other_tool"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
            assert (
                "CONTEXT ENGINE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
        finally:
            os.unlink(transcript_path)


class TestPreToolSoftModeOverride:
    """GOVERNANCE_SOFT_MODE / CE_SOFT_MODE reverts to advisory reminders."""

    def test_pretool_soft_mode_governance_warns(self):
        """Soft mode for governance: warns instead of blocking."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "GOVERNANCE_SOFT_MODE": "true",
                    "CE_SOFT_MODE": "true",
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "additionalContext" in output
            assert "GOVERNANCE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)

    def test_pretool_soft_mode_ce_warns(self):
        """Soft mode for CE: warns instead of blocking."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__ai-governance__evaluate_governance")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "GOVERNANCE_SOFT_MODE": "true",
                    "CE_SOFT_MODE": "true",
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "additionalContext" in output
            assert "CONTEXT ENGINE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)

    def test_pretool_legacy_hard_mode_false_is_soft(self):
        """Legacy GOVERNANCE_HARD_MODE=false triggers soft mode."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "GOVERNANCE_HARD_MODE": "false",
                    "CE_HARD_MODE": "false",
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "additionalContext" in output
            assert "GOVERNANCE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestPreToolMixedEnforcementModes:
    """Mixed modes: one tool hard, the other soft."""

    def test_gov_hard_ce_soft_missing_gov_denies(self):
        """Gov hard + CE soft: missing governance = deny."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"CE_SOFT_MODE": "true"},
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
        finally:
            os.unlink(transcript_path)

    def test_gov_soft_ce_hard_missing_ce_denies(self):
        """Gov soft + CE hard: missing CE = deny."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__ai-governance__evaluate_governance")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_SOFT_MODE": "true"},
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                "CONTEXT ENGINE NOT DETECTED"
                in output["hookSpecificOutput"]["permissionDecisionReason"]
            )
        finally:
            os.unlink(transcript_path)

    def test_gov_hard_ce_soft_missing_ce_warns(self):
        """Gov hard + CE soft: missing CE = warn (soft), not deny."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__ai-governance__evaluate_governance")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"CE_SOFT_MODE": "true"},
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            # CE is soft, so should be additionalContext (warn), not deny
            assert "additionalContext" in output
            assert "CONTEXT ENGINE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)

    def test_gov_soft_ce_hard_missing_gov_warns(self):
        """Gov soft + CE hard: missing gov = warn (soft), not deny."""
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_SOFT_MODE": "true"},
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            # Gov is soft, so should be additionalContext (warn), not deny
            assert "additionalContext" in output
            assert "GOVERNANCE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestPreToolRecencyWindow:
    """Recency window controls which transcript entries are scanned."""

    def test_pretool_recent_calls_pass(self):
        """Tool calls within the recency window are accepted."""
        entries = [make_filler_entry() for _ in range(5)]
        entries.append(make_tool_use_entry("mcp__ai-governance__evaluate_governance"))
        entries.append(make_tool_use_entry("mcp__context-engine__query_project"))
        transcript_path = create_transcript(entries)
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_RECENCY_WINDOW": "10"},
            )
            assert result.returncode == 0
            assert result.stdout.strip() == ""
        finally:
            os.unlink(transcript_path)

    def test_pretool_old_calls_denied(self):
        """Tool calls outside the recency window are treated as missing."""
        entries = [
            make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            make_tool_use_entry("mcp__context-engine__query_project"),
        ]
        entries.extend([make_filler_entry() for _ in range(30)])
        transcript_path = create_transcript(entries)
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_RECENCY_WINDOW": "5"},
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)


class TestPreToolHardModeMissingTranscript:
    """Hard mode (default) with missing transcript blocks (fail-closed)."""

    def test_pretool_hard_mode_missing_transcript(self):
        hook_input = json.dumps({"transcript_path": "/nonexistent/path.jsonl"})
        result = run_hook(PRETOOL_HOOK, hook_input)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPreToolSoftModeMissingTranscript:
    """Both soft mode with missing transcript allows silently (fail-open)."""

    def test_pretool_soft_mode_missing_transcript(self):
        hook_input = json.dumps({"transcript_path": "/nonexistent/path.jsonl"})
        result = run_hook(
            PRETOOL_HOOK,
            hook_input,
            env_overrides={
                "GOVERNANCE_SOFT_MODE": "true",
                "CE_SOFT_MODE": "true",
            },
        )
        assert result.returncode == 0
        # Fail-open: no output (silent allow)
        assert result.stdout.strip() == ""


class TestPreToolValidJSONOutput:
    """All hook outputs must be valid JSON."""

    def test_pretool_valid_json_when_missing_both(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            # Default hard mode — should deny with valid JSON
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
            assert "hookSpecificOutput" in parsed
            assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_pretool_valid_json_soft_mode(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "GOVERNANCE_SOFT_MODE": "true",
                    "CE_SOFT_MODE": "true",
                },
            )
            assert result.returncode == 0
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
            assert "additionalContext" in parsed
        finally:
            os.unlink(transcript_path)


class TestPreToolMalformedTranscript:
    """Scanner handles malformed JSONL lines gracefully."""

    def test_pretool_malformed_jsonl_lines_skipped(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write("this is not json\n")
            f.write('{"incomplete": true\n')  # missing closing brace
            f.write(
                json.dumps(
                    make_tool_use_entry("mcp__ai-governance__evaluate_governance")
                )
                + "\n"
            )
            f.write("\x00\x01\x02\n")  # binary garbage
            f.write(
                json.dumps(make_tool_use_entry("mcp__context-engine__query_project"))
                + "\n"
            )
        try:
            hook_input = json.dumps({"transcript_path": path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            # Should find both despite malformed lines
            assert result.stdout.strip() == ""
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# UserPromptSubmit Hook Tests
# ---------------------------------------------------------------------------


class TestPromptHookSuppressesWhenCompliant:
    """UserPromptSubmit hook suppresses when both tools are present."""

    def test_prompt_hook_silent_when_compliant(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
                make_tool_use_entry("mcp__context-engine__query_project"),
                # Startup reads — hook checks for PROJECT-MEMORY and LEARNING-LOG in early session
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "r1",
                                "name": "Read",
                                "input": {"file_path": "PROJECT-MEMORY.md"},
                            }
                        ],
                    }
                },
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "r2",
                                "name": "Read",
                                "input": {"file_path": "LEARNING-LOG.md"},
                            }
                        ],
                    }
                },
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PROMPT_HOOK, hook_input)
            assert result.returncode == 0
            # Should produce no output (suppressed)
            assert result.stdout.strip() == ""
        finally:
            os.unlink(transcript_path)


class TestPromptHookInjectsWhenNonCompliant:
    """UserPromptSubmit hook injects reminder when tools are missing."""

    def test_prompt_hook_injects_when_not_compliant(self):
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PROMPT_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "additionalContext" in output
            context = output["additionalContext"]
            assert "evaluate_governance()" in context
            assert "query_project()" in context
            assert "hard-mode hook" in context
        finally:
            os.unlink(transcript_path)

    def test_prompt_hook_injects_without_transcript(self):
        """Without transcript path, inject reminder."""
        result = run_hook(PROMPT_HOOK, "test prompt without json")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "additionalContext" in output
        assert "evaluate_governance()" in output["additionalContext"]


class TestPromptHookShortenedReminder:
    """UserPromptSubmit reminder is shorter than before (~50 tokens vs ~128)."""

    def test_prompt_hook_reminder_is_concise(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PROMPT_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            context = output["additionalContext"]
            # Should be significantly shorter than old 225-char reminder
            assert len(context) < 200
            # Should mention enforcement
            assert "enforced" in context.lower()
        finally:
            os.unlink(transcript_path)


class TestGovernanceFileDetection:
    """Tests for pre-push governance content file detection regex.

    The pre-push quality gate uses grep -E to identify governance principle
    files that require subagent review. This tests the regex pattern.
    """

    GOVERNANCE_REGEX = r"(constitution\.md|title-\d+-[a-z][-a-z]*(?<!-cfr)\.md)$"

    @pytest.mark.parametrize(
        "path,should_match",
        [
            # Should match — governance principle files (Constitutional naming)
            ("documents/constitution.md", True),
            ("documents/title-10-ai-coding.md", True),
            ("documents/title-20-multi-agent.md", True),
            ("documents/title-30-storytelling.md", True),
            ("documents/title-15-ui-ux.md", True),
            ("documents/title-25-kmpd.md", True),
            ("documents/title-40-multimodal-rag.md", True),
            # Should NOT match — CFR/methods files (high frequency, exempt)
            ("documents/title-10-ai-coding-cfr.md", False),
            ("documents/rules-of-procedure.md", False),
            ("documents/title-20-multi-agent-cfr.md", False),
            # Should NOT match — other docs
            ("SESSION-STATE.md", False),
            ("README.md", False),
            ("API.md", False),
            ("COMPLETION-CHECKLIST.md", False),
            # Should NOT match — code
            ("src/ai_governance_mcp/server.py", False),
            ("tests/test_server.py", False),
        ],
    )
    def test_governance_regex_matches_correctly(self, path, should_match):
        """Governance file regex should match principle files only."""
        import re

        matched = bool(re.search(self.GOVERNANCE_REGEX, path))
        assert matched == should_match, (
            f"{'Expected match' if should_match else 'Unexpected match'} "
            f"for path: {path}"
        )


class TestPromptHookValidJSON:
    """UserPromptSubmit hook always outputs valid JSON (or nothing)."""

    def test_prompt_hook_valid_json_when_injecting(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PROMPT_HOOK, hook_input)
            assert result.returncode == 0
            if result.stdout.strip():
                parsed = json.loads(result.stdout)
                assert isinstance(parsed, dict)
        finally:
            os.unlink(transcript_path)
