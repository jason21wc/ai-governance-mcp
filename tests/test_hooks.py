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

        Covers: FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE
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

        Covers: FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE
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
# Plan-Action-Atomicity Scanner Tests (Commit 6 of Superpowers plan)
# ---------------------------------------------------------------------------


def _run_atomicity_scan_stdin(plan_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCANNER), "--plan-action-atomicity", "-"],
        input=plan_text,
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestPlanActionAtomicity:
    """Tests for scan_plan_action_atomicity used by pre-exit-plan-mode-gate WARN integration."""

    def test_pass_when_all_tasks_atomic(self):
        """All tasks name single category + have Files/Verification → pass."""
        plan = """# Test Plan

## Recommended Approach

### Task 1 — write failing test for new behavior
**Files:** tests/test_foo.py
**Verification:** `pytest tests/test_foo.py::test_new -v` returns FAILED

### Task 2 — implement minimal code to satisfy Task 1
**Files:** src/foo.py
**Verification:** Task 1's test passes
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "pass"

    def test_warn_on_combined_action_in_title(self):
        """Title containing two action categories → warn (combined-action signal)."""
        plan = """## Recommended Approach

### Task 1 — implement minimal code and run test for X
**Files:** src/x.py
**Verification:** `pytest`
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "warn"
        # combined-action message includes both categories
        assert "combines" in result.stderr or "implement minimal code" in result.stderr

    def test_warn_on_vague_verb_in_title(self):
        """Title with vague verb (no category) → warn with vague-verb message."""
        plan = """## Recommended Approach

### Task 1 — update X module to handle Y
**Files:** src/x.py
**Verification:** `pytest`
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "warn"
        assert "vague verb" in result.stderr or "update" in result.stderr

    def test_warn_on_missing_files_line(self):
        """Task missing **Files:** line → warn."""
        plan = """## Recommended Approach

### Task 1 — write failing test for new behavior
**Verification:** `pytest tests/test_foo.py -v`
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "warn"
        assert "Files:" in result.stderr

    def test_warn_on_missing_verification_line(self):
        """Task missing **Verification:** line → warn."""
        plan = """## Recommended Approach

### Task 1 — write failing test for new behavior
**Files:** tests/test_foo.py
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "warn"
        assert "Verification:" in result.stderr

    def test_skip_when_no_recommended_approach_section(self):
        """Plan with no Recommended Approach heading → skip (out of scope)."""
        plan = """# Just Some Notes

## Context
Some prose, no plan structure.
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "skip"

    def test_skip_when_recommended_approach_has_no_task_entries(self):
        """Recommended Approach section without ### Task headings → skip (free-form prose plan)."""
        plan = """## Recommended Approach

We're going to refactor the whole system. Trust me.

## Verification
Run all tests.
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "skip"

    def test_pass_with_commit_style_entries(self):
        """Plan using ### Commit instead of ### Task is also accepted."""
        plan = """## Recommended Approach

### Commit 1 — write failing test for X
**Files:** tests/test_x.py
**Verification:** `pytest tests/test_x.py -v` FAILED

### Commit 2 — implement minimal code
**Files:** src/x.py
**Verification:** `pytest tests/test_x.py -v` PASSED
"""
        result = _run_atomicity_scan_stdin(plan)
        assert result.stdout.strip() == "pass"

    def test_error_on_empty_input(self):
        """Empty stdin → error (signals bad input to caller)."""
        result = _run_atomicity_scan_stdin("")
        assert result.stdout.strip() == "error"


# ---------------------------------------------------------------------------
# TDD-Test-Existence Scanner Tests (Commit 6 of Superpowers plan)
# ---------------------------------------------------------------------------


def _run_tdd_scan_stdin(
    file_list: str, cwd: str | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCANNER), "--tdd-test-existence", "-"],
        input=file_list,
        capture_output=True,
        text=True,
        cwd=cwd or str(PROJECT_DIR),
        timeout=10,
    )


class TestTddTestExistence:
    """Tests for scan_tdd_test_existence used by pre-push-quality-gate WARN integration."""

    def test_pass_when_all_src_files_have_test_pairs(self, tmp_path):
        """Every new src/*.py has paired tests/test_*.py → pass."""
        # Set up minimal repo layout
        (tmp_path / "src" / "ai_governance_mcp").mkdir(parents=True)
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "ai_governance_mcp" / "foo.py").write_text("# stub")
        (tmp_path / "tests" / "test_foo.py").write_text("# test stub")
        result = _run_tdd_scan_stdin(
            "src/ai_governance_mcp/foo.py\n", cwd=str(tmp_path)
        )
        assert result.stdout.strip() == "pass"

    def test_warn_when_src_file_missing_test_pair(self, tmp_path):
        """New src/*.py without paired tests/test_*.py → warn."""
        (tmp_path / "src" / "ai_governance_mcp").mkdir(parents=True)
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "ai_governance_mcp" / "orphan.py").write_text("# stub")
        # NOT creating tests/test_orphan.py
        result = _run_tdd_scan_stdin(
            "src/ai_governance_mcp/orphan.py\n", cwd=str(tmp_path)
        )
        assert result.stdout.strip() == "warn"
        assert "orphan" in result.stderr
        assert "test_orphan.py" in result.stderr

    def test_skip_when_no_src_py_files(self):
        """File list with no src/*.py entries → skip (out of scope)."""
        result = _run_tdd_scan_stdin(
            "documents/foo.md\nworkflows/bar.md\n.claude/hooks/baz.sh\n"
        )
        assert result.stdout.strip() == "skip"

    def test_skip_when_only_init_files_in_src(self, tmp_path):
        """Only __init__.py changes don't trigger TDD scan (boilerplate, not behavior)."""
        result = _run_tdd_scan_stdin(
            "src/ai_governance_mcp/__init__.py\n", cwd=str(tmp_path)
        )
        assert result.stdout.strip() == "skip"

    def test_skip_on_empty_input(self):
        """Empty stdin → skip (no files to evaluate)."""
        result = _run_tdd_scan_stdin("")
        assert result.stdout.strip() == "skip"


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
        """Hard-mode hook denies when query_project() not in transcript.

        Covers: FM-HOOK-GOVERNANCE-GATE-REQUIRED
        """
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
        """Hard-mode hook denies when both evaluate_governance and query_project absent.

        Covers: FM-HOOK-GOVERNANCE-GATE-REQUIRED
        """
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
# Read-Only Bash Allowlist Tests (pre-tool-governance-check.sh)
# ---------------------------------------------------------------------------


class TestPreToolReadOnlyBashAllowlist:
    """Read-only Bash commands skip governance check; write commands still require it."""

    def _hook_input(
        self, transcript_path: str, tool_name: str = "Bash", command: str = ""
    ) -> str:
        payload = {"transcript_path": transcript_path, "tool_name": tool_name}
        if command:
            payload["tool_input"] = {"command": command}
        return json.dumps(payload)

    def test_readonly_git_log_allows_without_governance(self):
        """git log is read-only — should allow even without governance calls.

        Covers: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log --oneline -10"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_ls_allows_without_governance(self):
        """ls is read-only — should allow without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="ls -la /tmp"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_find_allows_without_governance(self):
        """find is read-only — should allow without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command='find . -name "*.py"'),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_grep_allows_without_governance(self):
        """grep is read-only — should allow without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="grep -r 'pattern' src/"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_piped_command_allows(self):
        """Piped read-only commands should allow."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="git log --oneline | head -20"
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_write_git_commit_still_requires_governance(self):
        """git commit is a mutation — should deny without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command='git commit -m "test"'),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_rm_still_requires_governance(self):
        """rm is a mutation — should deny without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="rm -rf /tmp/test"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_compound_command_still_requires_governance(self):
        """Commands with && chaining are not read-only — should deny."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log && rm file"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_redirect_still_requires_governance(self):
        """Commands with output redirects are not read-only — should deny."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log > output.txt"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_edit_tool_still_requires_governance(self):
        """Edit tool (non-Bash) should still require governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            hook_input = json.dumps(
                {
                    "transcript_path": transcript_path,
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": "/tmp/test.py",
                        "old_string": "a",
                        "new_string": "b",
                    },
                }
            )
            result = run_hook(PRETOOL_HOOK, hook_input)
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_tool_still_requires_governance(self):
        """Write tool (non-Bash) should still require governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            hook_input = json.dumps(
                {
                    "transcript_path": transcript_path,
                    "tool_name": "Write",
                    "tool_input": {"file_path": "/tmp/test.py", "content": "hello"},
                }
            )
            result = run_hook(PRETOOL_HOOK, hook_input)
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_readonly_bash_with_governance_still_allows(self):
        """Read-only Bash with governance calls: should allow (happy path)."""
        transcript_path = create_transcript(
            [
                make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
                make_tool_use_entry("mcp__context-engine__query_project"),
            ]
        )
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log --oneline"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == ""
        finally:
            os.unlink(transcript_path)

    def test_readonly_bash_skip_env_var(self):
        """READONLY_BASH_SKIP=true disables the allowlist — read-only Bash denied."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log --oneline"),
                env_overrides={"READONLY_BASH_SKIP": "true"},
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_semicolon_chaining_requires_governance(self):
        """Commands with ; chaining are not read-only — should deny."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log; rm file"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_or_chaining_requires_governance(self):
        """Commands with || chaining are not read-only — should deny."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git log || echo fallback"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_git_status_allows(self):
        """git status is read-only — should allow."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git status"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_wc_allows(self):
        """wc is read-only — should allow."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="wc -l src/server.py"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_python3_requires_governance(self):
        """python3 is ambiguous — should require governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command='python3 -c "print(1)"'),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_no_tool_input_falls_through(self):
        """Bash call without tool_input.command falls through to normal check."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            hook_input = json.dumps(
                {
                    "transcript_path": transcript_path,
                    "tool_name": "Bash",
                }
            )
            result = run_hook(PRETOOL_HOOK, hook_input)
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)


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
