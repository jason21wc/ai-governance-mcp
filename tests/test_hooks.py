"""Tests for Claude Code hook scripts.

Subprocess-based tests that verify hook behavior for governance and
context engine compliance enforcement.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path


# Hook script paths
PROJECT_DIR = Path(__file__).parent.parent
PRETOOL_HOOK = PROJECT_DIR / ".claude" / "hooks" / "pre-tool-governance-check.sh"
PROMPT_HOOK = PROJECT_DIR / ".claude" / "hooks" / "user-prompt-governance-inject.sh"


def create_transcript(entries: list[dict]) -> str:
    """Create a temporary JSONL transcript file from entries.

    Returns the path to the temporary file.
    """
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return path


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
# PreToolUse Hook Tests
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


class TestPreToolWarnsGovernanceMissing:
    """When only CE is present, hook warns about missing governance."""

    def test_pretool_warns_governance_missing(self):
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
            assert "additionalContext" in output
            assert "GOVERNANCE NOT DETECTED" in output["additionalContext"]
            # Should NOT mention CE since CE was found
            assert "CONTEXT ENGINE NOT DETECTED" not in output["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestPreToolWarnsCEMissing:
    """When only governance is present, hook warns about missing CE."""

    def test_pretool_warns_ce_missing(self):
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
            assert "additionalContext" in output
            assert "CONTEXT ENGINE NOT DETECTED" in output["additionalContext"]
            # Should NOT mention governance since governance was found
            assert "GOVERNANCE NOT DETECTED" not in output["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestPreToolWarnsBothMissing:
    """When neither tool is found, hook warns about both."""

    def test_pretool_warns_both_missing(self):
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
            assert "additionalContext" in output
            assert "GOVERNANCE NOT DETECTED" in output["additionalContext"]
            assert "CONTEXT ENGINE NOT DETECTED" in output["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestPreToolHardModeGovernanceDeny:
    """GOVERNANCE_HARD_MODE=true blocks when governance is missing."""

    def test_pretool_hard_mode_governance_deny(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__context-engine__query_project"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_HARD_MODE": "true"},
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


class TestPreToolHardModeCEDeny:
    """CE_HARD_MODE=true blocks when CE query is missing."""

    def test_pretool_hard_mode_ce_deny(self):
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            ]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"CE_HARD_MODE": "true"},
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


class TestPreToolSoftModeMissingTranscript:
    """Soft mode with missing transcript allows silently (fail-open)."""

    def test_pretool_soft_mode_missing_transcript(self):
        hook_input = json.dumps({"transcript_path": "/nonexistent/path.jsonl"})
        result = run_hook(PRETOOL_HOOK, hook_input)
        assert result.returncode == 0
        # Fail-open: no output (silent allow)
        assert result.stdout.strip() == ""


class TestPreToolHardModeMissingTranscript:
    """Hard mode with missing transcript blocks (fail-closed)."""

    def test_pretool_hard_mode_missing_transcript(self):
        hook_input = json.dumps({"transcript_path": "/nonexistent/path.jsonl"})
        result = run_hook(
            PRETOOL_HOOK,
            hook_input,
            env_overrides={"GOVERNANCE_HARD_MODE": "true"},
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_pretool_ce_hard_mode_missing_transcript(self):
        hook_input = json.dumps({"transcript_path": "/nonexistent/path.jsonl"})
        result = run_hook(
            PRETOOL_HOOK,
            hook_input,
            env_overrides={"CE_HARD_MODE": "true"},
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPreToolValidJSONOutput:
    """All hook outputs must be valid JSON."""

    def test_pretool_valid_json_when_missing_both(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PRETOOL_HOOK, hook_input)
            assert result.returncode == 0
            # Empty transcript means neither found — should produce reminder
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
            assert "additionalContext" in parsed
            assert "GOVERNANCE NOT DETECTED" in parsed["additionalContext"]
            assert "CONTEXT ENGINE NOT DETECTED" in parsed["additionalContext"]
        finally:
            os.unlink(transcript_path)

    def test_pretool_valid_json_hard_mode_deny(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={"GOVERNANCE_HARD_MODE": "true"},
            )
            assert result.returncode == 0
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
            assert "hookSpecificOutput" in parsed
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


class TestPromptHookIncludesGovernanceAndCE:
    """UserPromptSubmit hook mentions both governance and context engine."""

    def test_prompt_hook_includes_governance_and_ce(self):
        # UserPromptSubmit hooks receive prompt text on stdin
        result = run_hook(PROMPT_HOOK, "test prompt")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "additionalContext" in output
        context = output["additionalContext"]
        assert "evaluate_governance" in context
        assert "query_project" in context


class TestPromptHookValidJSON:
    """UserPromptSubmit hook always outputs valid JSON."""

    def test_prompt_hook_valid_json(self):
        result = run_hook(PROMPT_HOOK, "test prompt")
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)
        assert "additionalContext" in parsed
