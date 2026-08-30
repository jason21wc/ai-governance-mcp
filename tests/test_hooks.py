"""Tests for Claude Code hook scripts.

Subprocess-based tests that verify hook behavior for governance and
context engine compliance enforcement.
"""

import json
import os
import subprocess
import sys
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
    # Pin MCP-availability auto-degrade OFF by default so enforcement-mode
    # tests are deterministic regardless of the host's MCP configuration
    # (CI runners have no ~/.claude.json and would otherwise auto-degrade).
    # TestPreToolMcpAutoDegrade opts back in explicitly.
    env["MCP_DETECT_SKIP"] = "true"
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
# Scanner: --pattern mode (self-satisfaction prevention, #231)
# ---------------------------------------------------------------------------


class TestSubagentDispatchMode:
    """`--subagent` requires a real dispatch, where `--pattern` accepted a mention.

    BACKLOG #334. Check 2/3 of the pre-push gate used `--pattern code-reviewer`, which
    matches a string against the serialised input of ANY tool call — so writing the words
    into a memory file, grepping the hook, or describing planned work to
    `evaluate_governance` all satisfied the gate that requires a review.
    """

    def _scan(self, mode, target, transcript_path):
        return subprocess.run(
            ["python3", str(SCANNER), mode, target, transcript_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _mention_only_transcript(self):
        """Edit + Bash + evaluate_governance that name a reviewer. No dispatch."""

        def tu(name, inp):
            return {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": "x", "name": name, "input": inp}
                    ],
                }
            }

        return create_transcript(
            [
                tu("Edit", {"file_path": "/n.md", "new_string": "run code-reviewer"}),
                tu("Bash", {"command": "grep -rn 'code-reviewer' .claude/hooks/"}),
                tu(
                    "mcp__ai-governance__evaluate_governance",
                    {"planned_action": "dispatch code-reviewer on the delta"},
                ),
            ]
        )

    def test_mentions_alone_no_longer_satisfy_the_review_gate(self):
        """THE regression this change exists for — and it asserts the contrast.

        Both assertions matter. If `--pattern` ever stops returning true here, the
        fixture has drifted and no longer reproduces the defect, so the second
        assertion would pass for the wrong reason.
        """
        path = self._mention_only_transcript()
        try:
            assert self._scan("--pattern", "code-reviewer", path).stdout.strip() == (
                "true"
            ), "fixture no longer reproduces the mention hole — fix the fixture"
            assert self._scan("--subagent", "code-reviewer", path).stdout.strip() == (
                "false"
            ), "a mention satisfied --subagent; the hole is not closed"
        finally:
            os.unlink(path)

    @pytest.mark.parametrize("tool_name", ["Agent", "Task"])
    def test_real_dispatch_matches_under_either_tool_name(self, tool_name):
        """Production emits `Agent`; `Task` is kept so a harness rename fails closed."""
        entry = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "d",
                        "name": tool_name,
                        "input": {"description": "r", "subagent_type": "code-reviewer"},
                    }
                ],
            }
        }
        path = create_transcript([entry])
        try:
            assert self._scan("--subagent", "code-reviewer", path).stdout.strip() == (
                "true"
            )
        finally:
            os.unlink(path)

    def test_a_different_subagent_does_not_satisfy(self):
        """An Explore dispatch is not a code review."""
        path = create_transcript([make_task_entry("Explore")])
        try:
            assert self._scan("--subagent", "code-reviewer", path).stdout.strip() == (
                "false"
            )
        finally:
            os.unlink(path)

    def test_no_recency_window_so_an_early_dispatch_still_counts(self):
        """The window's false-FAIL direction, which shipping without it would keep.

        A real dispatch happens once and early, then scrolls out of a 500-line window;
        `--pattern` returns false here even though the review genuinely happened. That
        asymmetry is why the matcher change and the window removal are one change:
        measured over the corpus, narrowing while keeping the window flips 87 push
        events to deny. Reproduce with `scripts/measure_review_gate.py`.
        """
        filler = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "f",
                        "name": "Bash",
                        "input": {"command": "echo filler"},
                    }
                ],
            }
        }
        path = create_transcript([make_task_entry("code-reviewer")] + [filler] * 1500)
        try:
            assert self._scan("--subagent", "code-reviewer", path).stdout.strip() == (
                "true"
            ), "no-window scan missed a dispatch at the start of the transcript"
            assert self._scan("--pattern", "code-reviewer", path).stdout.strip() == (
                "false"
            ), "fixture no longer demonstrates the window's false-fail"
        finally:
            os.unlink(path)

    def test_malformed_and_missing_input_return_false_never_crash(self):
        """Read/parse failure must be false (gate blocks) and must not traceback."""
        bad = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        bad.write('not json\n{"message":{"role":"assistant","content":"notalist"}}\n')
        bad.close()
        try:
            r = self._scan("--subagent", "code-reviewer", bad.name)
            assert r.stdout.strip() == "false"
            assert "Traceback" not in r.stderr
        finally:
            os.unlink(bad.name)

        r = self._scan("--subagent", "code-reviewer", "/nonexistent/none.jsonl")
        assert r.stdout.strip() == "false"
        assert "Traceback" not in r.stderr

    def test_argv_arity_error_does_not_fall_through_to_governance_mode(self):
        """A malformed call must not print `neither`.

        Governance mode is the fall-through, and it prints `neither` — which the gate
        reads as false and blocks on, with no diagnostic saying the caller was wrong.
        A silent misroute is the failure class this mode exists to remove.
        """
        r = subprocess.run(
            ["python3", str(SCANNER), "--subagent", "onlyonearg"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.stdout.strip() == "false"
        assert "neither" not in r.stdout
        assert "error:" in r.stderr

    def test_bare_invocation_still_reports_neither_without_crashing(self):
        """Guards a regression introduced while writing this change.

        The first draft indexed `sys.argv[1]` before checking length, so calling the
        scanner with no arguments raised IndexError instead of printing `neither`.
        """
        r = subprocess.run(
            ["python3", str(SCANNER)], capture_output=True, text=True, timeout=10
        )
        assert r.stdout.strip() == "neither"
        assert "Traceback" not in r.stderr


class TestPatternModeSelfSatisfaction:
    """The hook's own deny text must NOT satisfy the check on retry (#231).

    scan_for_pattern now matches only assistant tool_use entries, not arbitrary
    transcript text. The deny message re-enters as a user/tool_result entry and
    must be invisible to the scanner.
    """

    def test_deny_text_does_not_self_satisfy(self):
        """A transcript containing ONLY the hook's deny text → false."""
        deny_text = (
            "Tests not run this session. Run pytest before pushing. "
            "Risky changes without subagent review. Run code-reviewer. "
            "Run contrarian-reviewer, coherence-auditor, or validator. "
            "completion-sequence-aigov"
        )
        transcript_path = create_transcript([make_tool_result_entry(deny_text)])
        try:
            for pattern in [
                "pytest",
                "code-reviewer",
                "contrarian-reviewer",
                "validator",
                "completion-sequence-aigov",
            ]:
                result = subprocess.run(
                    [
                        "python3",
                        str(SCANNER),
                        "--pattern",
                        pattern,
                        transcript_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                assert result.stdout.strip() == "false", (
                    f"Pattern '{pattern}' self-satisfied from deny text"
                )
        finally:
            os.unlink(transcript_path)

    def test_legitimate_tool_use_matches(self):
        """A Bash tool_use containing 'pytest' → true."""
        entry = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "test-id",
                        "name": "Bash",
                        "input": {"command": "pytest tests/ -v"},
                    }
                ],
            }
        }
        transcript_path = create_transcript([entry])
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "--pattern",
                    "pytest",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "true"
        finally:
            os.unlink(transcript_path)

    def test_agent_subagent_type_matches(self):
        """An Agent tool_use with subagent_type 'code-reviewer' → true."""
        entry = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "test-id",
                        "name": "Agent",
                        "input": {
                            "prompt": "Review the code",
                            "subagent_type": "code-reviewer",
                        },
                    }
                ],
            }
        }
        transcript_path = create_transcript([entry])
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "--pattern",
                    "code-reviewer",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "true"
        finally:
            os.unlink(transcript_path)

    def test_pattern_in_user_message_does_not_match(self):
        """Pattern in a user message (not tool_use) → false."""
        entry = {
            "message": {
                "role": "user",
                "content": "I ran pytest and code-reviewer already",
            }
        }
        transcript_path = create_transcript([entry])
        try:
            for pattern in ["pytest", "code-reviewer"]:
                result = subprocess.run(
                    [
                        "python3",
                        str(SCANNER),
                        "--pattern",
                        pattern,
                        transcript_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                assert result.stdout.strip() == "false", (
                    f"Pattern '{pattern}' matched in user message"
                )
        finally:
            os.unlink(transcript_path)

    def test_check3_validator_substring_does_not_match_imports(self):
        """'validator' in a tool_result mentioning pydantic → false (#231 Check 3)."""
        entry = {
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "content": "from pydantic import field_validator",
                    }
                ],
            }
        }
        transcript_path = create_transcript([entry])
        try:
            result = subprocess.run(
                [
                    "python3",
                    str(SCANNER),
                    "--pattern",
                    "validator",
                    transcript_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.stdout.strip() == "false"
        finally:
            os.unlink(transcript_path)


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
            "documents/foo.md\n.claude/skills/bar/checklist.md\n.claude/hooks/baz.sh\n"
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
            assert "additionalContext" in output["hookSpecificOutput"]
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["additionalContext"]
            )
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
            assert "additionalContext" in output["hookSpecificOutput"]
            assert (
                "CONTEXT ENGINE NOT DETECTED"
                in output["hookSpecificOutput"]["additionalContext"]
            )
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
            assert "additionalContext" in output["hookSpecificOutput"]
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["additionalContext"]
            )
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
            assert "additionalContext" in output["hookSpecificOutput"]
            assert (
                "CONTEXT ENGINE NOT DETECTED"
                in output["hookSpecificOutput"]["additionalContext"]
            )
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
            assert "additionalContext" in output["hookSpecificOutput"]
            assert (
                "GOVERNANCE NOT DETECTED"
                in output["hookSpecificOutput"]["additionalContext"]
            )
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
        """Soft-mode reminder is valid JSON in the nested consumer shape.

        Covers: FM-HOOK-OUTPUT-ENVELOPE
        """
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
            assert "additionalContext" in parsed["hookSpecificOutput"]
            assert parsed["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
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

    def test_readonly_gh_pr_view_allows_without_governance(self):
        """gh pr view is read-only — should allow without governance (BACKLOG #56).

        Covers: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="gh pr view 5 --json title"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_gh_repo_view_allows_without_governance(self):
        """gh repo view is read-only — should allow without governance (BACKLOG #56).

        Covers: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="gh repo view"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_gh_run_list_allows_without_governance(self):
        """gh run list is read-only — should allow without governance (BACKLOG #56).

        Covers: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="gh run list --branch main --limit 5"
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_gh_api_get_allows_without_governance(self):
        """gh api with no method-mutating flags is a GET — should allow (BACKLOG #56).

        Covers: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="gh api repos/owner/repo/commits"
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_write_gh_pr_merge_still_requires_governance(self):
        """gh pr merge mutates remote state — should deny without governance (BACKLOG #56)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="gh pr merge 5 --squash"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_gh_pr_create_still_requires_governance(self):
        """gh pr create mutates remote state — should deny without governance (BACKLOG #56)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command='gh pr create --title "x"'),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_gh_repo_delete_still_requires_governance(self):
        """gh repo delete mutates remote state — should deny without governance (BACKLOG #56)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="gh repo delete owner/repo --yes"
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_gh_api_post_still_requires_governance(self):
        """gh api with -f (POST field) mutates remote state — should deny without governance (BACKLOG #56)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path,
                    command="gh api repos/owner/repo/issues -f title=bug",
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
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

    def test_readonly_git_stash_list_allows_without_governance(self):
        """git stash list is read-only — should allow without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash list"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_stash_show_allows_without_governance(self):
        """git stash show is read-only — should allow without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash show -p"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_write_git_stash_bare_still_requires_governance(self):
        """Bare git stash MUTATES the working tree — should deny without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_stash_pop_still_requires_governance(self):
        """git stash pop mutates the working tree — should deny without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash pop"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_stash_drop_still_requires_governance(self):
        """git stash drop destroys stashed state — should deny without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash drop stash@{0}"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_stash_apply_still_requires_governance(self):
        """git stash apply mutates the working tree — should deny without governance (BACKLOG #62)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git stash apply"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_branch_bare_allows_without_governance(self):
        """git branch is read-only — should allow without governance (BACKLOG #62 class)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git branch"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_branch_all_allows_without_governance(self):
        """git branch -a is read-only — should allow without governance (BACKLOG #62 class)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git branch -a"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_tag_list_allows_without_governance(self):
        """git tag -l is read-only — should allow without governance (BACKLOG #62 class)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git tag -l"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_remote_verbose_allows_without_governance(self):
        """git remote -v is read-only — should allow without governance (BACKLOG #62 class)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git remote -v"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_git_remote_show_allows_without_governance(self):
        """git remote show origin is read-only — should allow without governance (BACKLOG #62 class)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git remote show origin"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_write_git_branch_force_delete_still_requires_governance(self):
        """git branch -D feature mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git branch -D feature"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_branch_create_still_requires_governance(self):
        """git branch newfeature mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git branch newfeature"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_tag_delete_still_requires_governance(self):
        """git tag -d v1.0 mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git tag -d v1.0"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_tag_create_still_requires_governance(self):
        """git tag v2.0 mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git tag v2.0"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_remote_remove_still_requires_governance(self):
        """git remote remove origin mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="git remote remove origin"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_write_git_remote_add_still_requires_governance(self):
        """git remote add up https://example.com/x.git mutates state — should deny without governance (BACKLOG #62 class).

        Covers: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path,
                    command="git remote add up https://example.com/x.git",
                ),
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

    def test_readonly_grep_with_stderr_redirect(self):
        """grep with 2>/dev/null is read-only — should allow without governance.

        Regression: stderr-stripping regex must handle 2>/dev/null, not just 2>&1.
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="grep -r 'pattern' src/ 2>/dev/null"
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_find_with_stderr_redirect(self):
        """find with 2>/dev/null is read-only — should allow without governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command='find . -name "*.py" 2>/dev/null'
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_readonly_stderr_to_stdout_regression(self):
        """grep with 2>&1 is read-only — should allow (regression lock)."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="grep -r 'pattern' src/ 2>&1"
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_stdout_redirect_still_denied(self):
        """stdout redirect (not stderr) must still require governance."""
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="grep 'foo' bar > output.txt"
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_find_delete_denied(self):
        """find -delete mutates the filesystem — must deny (BACKLOG #230a).

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command='find . -name "*.tmp" -delete'
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_find_exec_denied(self):
        """find -exec runs arbitrary commands — must deny (BACKLOG #230a).

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="find . -exec rm {} +"),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_find_execdir_denied(self):
        """find -execdir runs commands from matched dir — must deny.

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="find . -execdir chmod 777 {} \\;"
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_sort_output_flag_denied(self):
        """sort -o writes to file — must deny (BACKLOG #230a).

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="sort -o victim.txt victim.txt"
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_sort_long_output_flag_denied(self):
        """sort --output writes to file — must deny.

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command="sort --output=sorted.txt data.txt"
                ),
            )
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_find_readonly_still_allows(self):
        """Plain read-only find (no mutation flags) must still allow.

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(
                    transcript_path, command='find . -name "*.py" -type f'
                ),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)

    def test_sort_readonly_still_allows(self):
        """Plain sort (no -o flag) must still allow.

        Covers: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
        """
        transcript_path = create_transcript([make_tool_use_entry("some_other_tool")])
        try:
            result = run_hook(
                PRETOOL_HOOK,
                self._hook_input(transcript_path, command="sort -u data.txt"),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == "" or "deny" not in result.stdout
        finally:
            os.unlink(transcript_path)


# ---------------------------------------------------------------------------
# UserPromptSubmit Hook Tests
# ---------------------------------------------------------------------------


class TestPromptHookFrameWhenCompliant:
    """UserPromptSubmit hook injects the FRAME (turn-start re-anchor) even when compliant; no gov reminder."""

    def test_frame_injected_when_compliant(self):
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
            # FRAME injects on every prompt (turn-start re-anchor), even when compliant
            context = json.loads(result.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            assert "FRAME" in context
            assert "meta-core-systemic-thinking" in context
            # Compliant → no governance/CE reminder appended
            assert "hard-mode hook" not in context
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
            assert "additionalContext" in output["hookSpecificOutput"]
            context = output["hookSpecificOutput"]["additionalContext"]
            assert "evaluate_governance()" in context
            assert "query_project()" in context
            assert "hard-mode hook" in context
            # FRAME is prepended on every prompt, including non-compliant ones
            assert "FRAME" in context
            assert "meta-core-systemic-thinking" in context
        finally:
            os.unlink(transcript_path)

    def test_prompt_hook_injects_without_transcript(self):
        """Without transcript path, inject reminder."""
        result = run_hook(PROMPT_HOOK, "test prompt without json")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "additionalContext" in output["hookSpecificOutput"]
        assert (
            "evaluate_governance()" in output["hookSpecificOutput"]["additionalContext"]
        )


class TestPromptHookShortenedReminder:
    """UserPromptSubmit reminder is shorter than before (~50 tokens vs ~128)."""

    def test_prompt_hook_reminder_is_concise(self):
        transcript_path = create_transcript([])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(PROMPT_HOOK, hook_input)
            assert result.returncode == 0
            output = json.loads(result.stdout)
            context = output["hookSpecificOutput"]["additionalContext"]
            # FRAME (turn-start re-anchor) is prepended on every prompt, so total length grows;
            # the governance-reminder portion stays concise. Assert both present + a sane bound.
            assert "enforced" in context.lower()
            assert "FRAME" in context
            assert len(context) < 900
        finally:
            os.unlink(transcript_path)


class TestFrameInjection:
    """UserPromptSubmit hook injects the reasoning FRAME on every prompt (turn-start re-anchor).

    Replaces the former long-convo-only critical-5 string: the FRAME now fires every prompt
    (short AND long), complementing the gov-call critical_5 scaffolds per EXECUTION-FRAMEWORK §8.4.
    """

    def _make_compliant_transcript(self, line_count):
        """Create a compliant transcript (gov+CE+PM+LL reads) padded to line_count."""
        entries = [
            make_tool_use_entry("mcp__ai-governance__evaluate_governance"),
            make_tool_use_entry("mcp__context-engine__query_project"),
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
        entries.extend([make_filler_entry() for _ in range(line_count - len(entries))])
        return create_transcript(entries)

    def test_frame_injected_in_long_conversation(self):
        """Long compliant conversation gets the FRAME (replaces the old long-convo critical-5 string)."""
        transcript_path = self._make_compliant_transcript(150)
        try:
            result = run_hook(
                PROMPT_HOOK, json.dumps({"transcript_path": transcript_path})
            )
            assert result.returncode == 0
            context = json.loads(result.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            assert "FRAME" in context
            assert "meta-core-systemic-thinking" in context
        finally:
            os.unlink(transcript_path)

    def test_frame_injected_in_short_conversation(self):
        """Short compliant conversation also gets the FRAME (no longer silent)."""
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK, json.dumps({"transcript_path": transcript_path})
            )
            assert result.returncode == 0
            context = json.loads(result.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            assert "FRAME" in context
        finally:
            os.unlink(transcript_path)

    def test_frame_disabled_via_env(self):
        """FRAME_INJECT_INTERVAL=0 disables the FRAME; a compliant turn then stays silent."""
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK,
                json.dumps({"transcript_path": transcript_path}),
                env_overrides={"FRAME_INJECT_INTERVAL": "0"},
            )
            assert result.returncode == 0
            assert result.stdout.strip() == ""
        finally:
            os.unlink(transcript_path)

    def test_frame_contains_principle_refs(self):
        """FRAME carries canonical refs (constitution effect) for the directives."""
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK, json.dumps({"transcript_path": transcript_path})
            )
            context = json.loads(result.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            for ref in (
                "meta-core-systemic-thinking",
                "meta-quality-verification-validation",
                "meta-safety-transparent-limitations",
                "recommend-not-ask",
                "proportional-rigor",
            ):
                assert ref in context, f"missing ref: {ref}"
            assert "dogfood" in context.lower()
            assert "intent-over-literal" in context
        finally:
            os.unlink(transcript_path)

    def test_frame_outputs_valid_json(self):
        """FRAME injection output is valid JSON with a string additionalContext.

        Covers: FM-HOOK-OUTPUT-ENVELOPE
        """
        transcript_path = self._make_compliant_transcript(120)
        try:
            result = run_hook(
                PROMPT_HOOK, json.dumps({"transcript_path": transcript_path})
            )
            assert result.returncode == 0
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)
            assert isinstance(parsed["hookSpecificOutput"]["additionalContext"], str)
            assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        finally:
            os.unlink(transcript_path)

    def test_frame_injected_under_c_locale(self):
        """FRAME is ASCII-only, so it injects even under a non-UTF-8 locale (no silent drop)."""
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK,
                json.dumps({"transcript_path": transcript_path}),
                env_overrides={"LC_ALL": "C", "LANG": "C"},
            )
            assert result.returncode == 0
            assert (
                "FRAME"
                in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            )
        finally:
            os.unlink(transcript_path)

    def test_frame_non_numeric_interval_still_injects(self):
        """Any non-zero FRAME_INJECT_INTERVAL (incl. non-numeric) injects every prompt (documented v1)."""
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK,
                json.dumps({"transcript_path": transcript_path}),
                env_overrides={"FRAME_INJECT_INTERVAL": "abc"},
            )
            assert result.returncode == 0
            assert (
                "FRAME"
                in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            )
        finally:
            os.unlink(transcript_path)

    def test_frame_uses_nested_userpromptsubmit_envelope(self):
        """Regression guard: the FRAME must ship in the NESTED hookSpecificOutput envelope.

        A flat top-level {'additionalContext': ...} is valid JSON but the harness does not
        extract it for UserPromptSubmit, so the payload is silently dropped and the FRAME
        never reaches context (the session-206 no-op, fired zero times). The other FRAME
        tests read the nested path so they fail-loud on a flat revert; this test additionally
        pins the flat key ABSENT so a *dual*-emit (both shapes) can't sneak the bug back in.
        """
        transcript_path = self._make_compliant_transcript(80)
        try:
            result = run_hook(
                PROMPT_HOOK, json.dumps({"transcript_path": transcript_path})
            )
            assert result.returncode == 0
            out = json.loads(result.stdout)
            # Payload lives under hookSpecificOutput, NOT at the top level.
            assert "additionalContext" not in out, "flat envelope is a silent no-op"
            assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
            assert "FRAME" in out["hookSpecificOutput"]["additionalContext"]
        finally:
            os.unlink(transcript_path)


class TestGovernanceFileDetection:
    """Tests for pre-push governance content file detection (BACKLOG #221).

    The pre-push quality gate uses grep -E to identify governance files that
    require subagent review (contrarian / coherence-auditor / validator).

    **This class reads the pattern OUT of the hook rather than restating it.**
    The previous version hard-coded its own Python copy of the regex, which had
    two consequences: the copy could drift from the shell source silently, and —
    because the copy was authored from the same wrong premise — the test asserted
    ``documents/rules-of-procedure.md`` should NOT match. It encoded the defect as
    expected behaviour, so the gap was invisible for as long as the test passed.
    Same class as the index defect: two artifacts that must agree, paired by
    convention instead of by identity.
    """

    #: Documents deliberately NOT gated, with the reason. An exclusion has to be
    #: named here to exist — that is what stops a silent pattern gap recurring.
    UNGATED_DOCUMENTS = {
        # Test-to-failure-mode mapping: engineering metadata, not binding content.
        "test-failure-mode-map.md",
    }

    @staticmethod
    def _hook_matcher():
        """Extract the live GOVERNANCE_FILES pipeline from the hook source.

        Returns a predicate mirroring `grep -E <pattern> | grep -v '\\-cfr\\.md'`.
        """
        import re

        hook = (
            PROJECT_DIR / ".claude" / "hooks" / "pre-push-quality-gate.sh"
        ).read_text()
        line = next(
            ln for ln in hook.splitlines() if ln.startswith("GOVERNANCE_FILES=")
        )
        pattern = re.search(r"grep -E '([^']+)'", line).group(1)
        assert "-cfr" in line, "cfr exclusion disappeared from the pipeline"
        compiled = re.compile(pattern)

        def matches(path):
            return bool(compiled.search(path)) and "-cfr.md" not in path

        return matches

    @pytest.mark.parametrize(
        "path,should_match",
        [
            # Governance principle files (Constitutional naming)
            ("documents/constitution.md", True),
            ("documents/title-10-ai-coding.md", True),
            ("documents/title-20-multi-agent.md", True),
            ("documents/title-30-storytelling.md", True),
            ("documents/title-15-ui-ux.md", True),
            ("documents/title-25-kmpd.md", True),
            ("documents/title-40-multimodal-rag.md", True),
            # BACKLOG #221 — named core documents that used to fall through.
            # rules-of-procedure carries the framework's binding procedural law
            # and is the file a fabricated governance audit ID was found in.
            ("documents/rules-of-procedure.md", True),
            ("documents/ai-instructions.md", True),
            ("documents/failure-mode-registry.md", True),
            ("INFLUENCES.md", True),
            # Still exempt — CFR/methods files (high frequency)
            ("documents/title-10-ai-coding-cfr.md", False),
            ("documents/title-20-multi-agent-cfr.md", False),
            # Not governance content
            ("documents/test-failure-mode-map.md", False),
            ("SESSION-STATE.md", False),
            ("README.md", False),
            ("API.md", False),
            ("COMPLETION-CHECKLIST.md", False),
            ("src/ai_governance_mcp/server.py", False),
            ("tests/test_server.py", False),
        ],
    )
    def test_governance_regex_matches_correctly(self, path, should_match):
        """The hook's own pattern must classify these paths correctly."""
        matched = self._hook_matcher()(path)
        assert matched == should_match, (
            f"{'Expected match' if should_match else 'Unexpected match'} "
            f"for path: {path}"
        )

    def test_every_corpus_document_is_classified(self):
        """Every non-CFR document in the corpus is gated, or explicitly excused.

        This is the structural half of the #221 fix. The old pattern was a SHAPE
        heuristic (`title-N-*`), but the corpus's core documents are NAMED, so a
        new one lands outside the shape and escapes review with no signal at all.
        Deriving the expectation from the filesystem means the next core document
        added fails HERE — loudly, at authoring time — instead of silently
        skipping Check 3 forever.
        """
        matches = self._hook_matcher()
        docs = sorted(
            p.name
            for p in (PROJECT_DIR / "documents").glob("*.md")
            if not p.name.endswith("-cfr.md")
        )
        assert docs, "corpus document scan found nothing — wrong root?"
        unclassified = [
            name
            for name in docs
            if name not in self.UNGATED_DOCUMENTS and not matches(f"documents/{name}")
        ]
        assert not unclassified, (
            "These corpus documents are neither gated by the pre-push governance "
            f"matcher nor listed in UNGATED_DOCUMENTS: {unclassified}. Add them to "
            "the hook's GOVERNANCE_FILES pattern, or excuse them explicitly with a "
            "reason."
        )
        # And the excusals must be real files, so the list cannot rot silently.
        stale = [n for n in self.UNGATED_DOCUMENTS if n not in docs]
        assert not stale, f"UNGATED_DOCUMENTS names non-existent documents: {stale}"


class TestBypassAuditLog:
    """All bypass envvars in pre-tool-governance-check.sh write to unified audit log."""

    def test_governance_soft_mode_writes_audit(self, tmp_path):
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__context-engine__query_project")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "GOVERNANCE_SOFT_MODE": "true",
                    "HOME": str(tmp_path),
                },
            )
            log_file = tmp_path / ".claude" / "hook-bypass-audit.log"
            assert log_file.exists(), (
                "GOVERNANCE_SOFT_MODE should write to bypass audit log"
            )
            content = log_file.read_text()
            assert "pre-tool-governance-check" in content
            assert "GOVERNANCE_SOFT_MODE=true" in content
        finally:
            os.unlink(transcript_path)

    def test_ce_soft_mode_writes_audit(self, tmp_path):
        transcript_path = create_transcript(
            [make_tool_use_entry("mcp__ai-governance__evaluate_governance")]
        )
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "CE_SOFT_MODE": "true",
                    "HOME": str(tmp_path),
                },
            )
            log_file = tmp_path / ".claude" / "hook-bypass-audit.log"
            assert log_file.exists(), "CE_SOFT_MODE should write to bypass audit log"
            content = log_file.read_text()
            assert "CE_SOFT_MODE=true" in content
        finally:
            os.unlink(transcript_path)

    def test_quality_gate_skip_writes_audit(self, tmp_path):
        quality_gate = PROJECT_DIR / ".claude" / "hooks" / "pre-push-quality-gate.sh"
        hook_input = json.dumps(
            {
                "tool_input": {"command": "git push origin main"},
            }
        )
        result = run_hook(
            quality_gate,
            hook_input,
            env_overrides={
                "QUALITY_GATE_SKIP": "true",
                "HOME": str(tmp_path),
            },
        )
        assert result.returncode == 0
        log_file = tmp_path / ".claude" / "hook-bypass-audit.log"
        assert log_file.exists(), "QUALITY_GATE_SKIP should write to bypass audit log"
        content = log_file.read_text()
        assert "pre-push-quality-gate" in content
        assert "QUALITY_GATE_SKIP=true" in content

    # --- Pushing-worktree resolution (session-262) --------------------------
    # Observed 2026-07-24: the gate mixed two trees in one decision. The commit
    # RANGE came from the process cwd (the pushing worktree, which had unpushed
    # work), while Check 8 ran the generator resolved from $0 — the PRIMARY
    # checkout. A concurrent session's UNCOMMITTED work in the primary checkout
    # therefore denied an unrelated worktree's push, and the only escape
    # (QUALITY_GATE_SKIP=true) exits at the top of the file and disables the
    # secret scanner. Every check must now read the tree being pushed.

    def _push_repo(self, root, gen_stub_body):
        """A minimal git repo with 2 commits and a stub scripts/gen_quick_reference.py."""
        root.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
        (root / "scripts").mkdir(exist_ok=True)
        (root / "scripts" / "gen_quick_reference.py").write_text(gen_stub_body)
        for i in range(2):
            (root / f"f{i}.txt").write_text(str(i))
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
            subprocess.run(
                ["git", "commit", "-q", "-m", f"c{i}"], cwd=root, check=True, env=env
            )
        return root

    def _gate(self, tmp_path, cwd, extra_env=None):
        quality_gate = PROJECT_DIR / ".claude" / "hooks" / "pre-push-quality-gate.sh"
        transcript = tmp_path / "t.jsonl"
        transcript.write_text('{"role":"assistant"}\n')
        hook_input = json.dumps(
            {
                "tool_input": {"command": "git push origin feature"},
                "transcript_path": str(transcript),
                "cwd": str(cwd),
            }
        )
        # The row-identity probe deliberately skips when numpy is unavailable.
        # Run hook subprocesses with the same Python installation as pytest so a
        # test of the probe cannot silently become a test of that skip branch.
        env = {
            "HOME": str(tmp_path),
            "PATH": f"{Path(sys.executable).parent}:{os.environ.get('PATH', '')}",
        }
        env.update(extra_env or {})
        return run_hook(quality_gate, hook_input, env_overrides=env)

    def _deny_reason(self, result):
        try:
            payload = json.loads(result.stdout)
        except (ValueError, TypeError):
            return None
        out = payload.get("hookSpecificOutput", {})
        if out.get("permissionDecision") != "deny":
            return None
        return out.get("permissionDecisionReason", "")

    # --- Check 2 requires a DISPATCH, not a mention (BACKLOG #334) -----------

    def _gate_with_transcript(self, tmp_path, cwd, entries):
        """`_gate`, but the caller supplies the transcript contents."""
        quality_gate = PROJECT_DIR / ".claude" / "hooks" / "pre-push-quality-gate.sh"
        transcript = tmp_path / "t2.jsonl"
        transcript.write_text("".join(json.dumps(e) + "\n" for e in entries))
        hook_input = json.dumps(
            {
                "tool_input": {"command": "git push origin feature"},
                "transcript_path": str(transcript),
                "cwd": str(cwd),
            }
        )
        return run_hook(quality_gate, hook_input, env_overrides={"HOME": str(tmp_path)})

    def _risky_repo(self, root):
        """A repo whose latest commit touches a real RISKY_FILES match.

        `config.py` is deliberate: the hook's RISKY_FILES grep is
        `(server|extractor|retrieval|config)\\.py$`. An earlier draft of this change
        proposed self-checking with `scan_transcript.py`, which matches NONE of those —
        so Check 2 would never have fired and the check could not have proven anything.
        """
        ok = "import sys\nsys.exit(0)\n"
        self._push_repo(root, ok)
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        target = root / "src" / "ai_governance_mcp"
        target.mkdir(parents=True, exist_ok=True)
        (target / "config.py").write_text("SETTING = 1\n")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "touch config.py"],
            cwd=root,
            check=True,
            env=env,
        )
        return root

    # Must DISCRIMINATE Check 2 from Check 3 — the new Check 3 message also contains
    # "without subagent review", so the short phrase would let a Check 3 deny satisfy a
    # Check 2 assertion if the fixture ever picked up a governance-named file.
    _CHECK2_PHRASE = (
        "Risky changes (core code or new src files) without subagent review"
    )

    def test_check2_denies_when_only_mentions_are_present(self, tmp_path):
        """A transcript that only TALKS about a reviewer must not satisfy Check 2."""
        repo = self._risky_repo(tmp_path / "wt_mention")
        entries = [
            {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "m",
                            "name": "Edit",
                            "input": {
                                "file_path": "/n.md",
                                "new_string": "next: run code-reviewer and security-auditor",
                            },
                        }
                    ],
                }
            }
        ]
        reason = self._deny_reason(self._gate_with_transcript(tmp_path, repo, entries))
        assert reason is not None, "a risky change with no review must deny"
        assert self._CHECK2_PHRASE in reason, (
            f"Check 2 did not fire on a mention-only transcript; reason was: {reason}"
        )

    def test_check2_is_satisfied_by_a_real_dispatch(self, tmp_path):
        """The must-PASS case, asserted on the REASON rather than on allow.

        Deliberately not `assert allow`. Checks 1 (pytest) and 4 (completion checklist)
        append to the same `$ISSUES` string and share one `emit_deny`, so a transcript
        carrying only a reviewer dispatch still denies — for reasons unrelated to this
        change. Asserting allow would fail misleadingly; asserting Check 2's phrase is
        ABSENT tests exactly what changed.
        """
        repo = self._risky_repo(tmp_path / "wt_dispatch")
        reason = self._deny_reason(
            self._gate_with_transcript(
                tmp_path, repo, [make_task_entry("code-reviewer")]
            )
        )
        # Assert the deny EXISTS before asserting what is absent from it. Guarding the
        # only assertion behind `if reason is not None` let this pass vacuously — and the
        # environment that makes it do so is real: these tests use `run_hook`, which does
        # NOT scrub bypass vars the way `hook_fixtures.run_gate` does, so running the
        # suite with QUALITY_GATE_SKIP=true exported would allow the push and this test
        # would assert nothing while its partner correctly went red.
        assert reason is not None, (
            "expected a deny from Checks 1/4 (this transcript has no pytest run and no "
            "checklist consult) — without one, the absence check below proves nothing"
        )
        assert self._CHECK2_PHRASE not in reason, (
            f"a real code-reviewer dispatch did not satisfy Check 2; reason was: {reason}"
        )

    _CHECK3_PHRASE = "Governance principle files changed without subagent review"

    def _governance_repo(self, root):
        """A repo whose latest commit touches a GOVERNANCE_FILES match.

        Note `-cfr.md` is excluded by the hook's own grep, so a CFR edit would NOT
        trigger Check 3 — `rules-of-procedure.md` does.
        """
        self._push_repo(root, "import sys\nsys.exit(0)\n")
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        docs = root / "documents"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "rules-of-procedure.md").write_text("# rop\n")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "touch rop"], cwd=root, check=True, env=env
        )
        return root

    def test_check3_denies_on_mention_and_passes_on_dispatch(self, tmp_path):
        """Check 3 switched to --subagent with NO test; a typo would block silently.

        Its agent list also dropped the underscore aliases the old --pattern loop
        carried (`contrarian_reviewer`, `coherence_auditor`). That is correct —
        `subagent_type` matching is exact and every agent in `.claude/agents/` is
        hyphen-named — but nothing asserted it, so a typo in the loop would have blocked
        every governance-file push forever with a green suite.
        """
        mention = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "m",
                        "name": "Edit",
                        "input": {
                            "file_path": "/n.md",
                            "new_string": "run contrarian-reviewer and validator",
                        },
                    }
                ],
            }
        }
        repo = self._governance_repo(tmp_path / "wt_gov_mention")
        reason = self._deny_reason(
            self._gate_with_transcript(tmp_path, repo, [mention])
        )
        assert reason is not None, "a governance change with no review must deny"
        assert self._CHECK3_PHRASE in reason, (
            f"Check 3 did not fire on a mention-only transcript; reason was: {reason}"
        )

        repo2 = self._governance_repo(tmp_path / "wt_gov_dispatch")
        reason2 = self._deny_reason(
            self._gate_with_transcript(tmp_path, repo2, [make_task_entry("validator")])
        )
        assert reason2 is not None, "Checks 1/4 should still deny on this transcript"
        assert self._CHECK3_PHRASE not in reason2, (
            f"a real validator dispatch did not satisfy Check 3; reason was: {reason2}"
        )

    def test_check8_runs_generator_from_pushing_worktree_not_hook_dir(self, tmp_path):
        # The generator derives its repo root from __file__, so WHICH copy runs decides
        # WHICH tree is validated. A stub that can only exist in the pushing worktree
        # proves resolution followed the payload cwd rather than $0/HOOK_DIR.
        repo = self._push_repo(
            tmp_path / "wt",
            "import sys\nsys.stderr.write('SENTINEL_PUSHING_TREE_DRIFT\\n')\nsys.exit(1)\n",
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None, "drift in the pushing worktree must still deny"
        assert "SENTINEL_PUSHING_TREE_DRIFT" in reason, (
            "Check 8 ran a generator other than the pushing worktree's — the primary-"
            "checkout resolution bug is back, and a sibling session's dirty tree can "
            "again block this push."
        )

    def test_check8_clean_pushing_worktree_is_not_denied(self, tmp_path):
        # The false-positive direction: an in-sync pushing tree must pass Check 8 even
        # though the primary checkout (this repo, during a concurrent session) may drift.
        repo = self._push_repo(tmp_path / "wt", "import sys\nsys.exit(0)\n")
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None or "derived-count drift" not in reason, (
            f"clean pushing worktree denied on count drift: {reason}"
        )

    def test_check8_drift_message_reports_the_actual_checker_output(self, tmp_path):
        # rc 1 covers TWO drifts (generated SESSION-STATE block AND the hand-curated
        # README domain table) and only the first is fixed by running the generator.
        # The old message asserted the first unconditionally, which looped a real push:
        # "run the generator" -> "already current" -> still denied.
        repo = self._push_repo(
            tmp_path / "wt",
            "import sys\n"
            "sys.stderr.write(\"DRIFT: README 'Constitution' row: 24p/241m vs index 24p/242m\\n\")\n"
            "sys.exit(1)\n",
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None
        assert "README" in reason and "242m" in reason, (
            f"deny message did not surface the checker's own reason: {reason}"
        )

    # --- Check 10: index row-identity probe (BACKLOG #219) -------------------
    # The row-misattribution defect reached origin/main and served every query
    # against the wrong document for six days. The CI job built for exactly this
    # class never ran — CI dies in 3-4s on the exhausted Actions quota (T-169),
    # so its red was indistinguishable from the expected red. These tests pin the
    # local mirror of that guard, in BOTH directions: a broken index must deny,
    # and a healthy one must not (a false positive here trains QUALITY_GATE_SKIP,
    # which also disables the secret scanner).

    def _repo_with_index(
        self,
        root,
        *,
        ids,
        n_rows,
        domain_ids=None,
        n_domains=2,
        padding_paths=0,
    ):
        import numpy as np

        repo = self._push_repo(root, "import sys\nsys.exit(0)\n")
        (repo / "index").mkdir(exist_ok=True)
        index = {
            "domains": {
                "alpha": {
                    "principles": [{"embedding_id": i} for i in ids],
                    "methods": [],
                    "references": [],
                }
            },
            "domain_configs": [
                {"embedding_id": d} for d in (domain_ids or list(range(n_domains)))
            ],
        }
        (repo / "index" / "global_index.json").write_text(json.dumps(index))
        np.save(repo / "index" / "content_embeddings.npy", np.zeros((n_rows, 4)))
        np.save(repo / "index" / "domain_embeddings.npy", np.zeros((n_domains, 4)))
        if padding_paths:
            padding = repo / "padding"
            padding.mkdir()
            suffix = "x" * 180
            for i in range(padding_paths):
                (padding / f"{i:04d}-{suffix}").write_text("")
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "rebuild index"],
            cwd=repo,
            check=True,
            env=env,
        )
        return repo

    def _commit_all(self, repo, message):
        import os
        import subprocess

        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", message], cwd=repo, check=True, env=env
        )

    def test_check10_denies_push_of_non_bijective_index(self, tmp_path):
        """Duplicate ids leave a hole: some row is owned by nobody.

        Covers: FM-HOOK-PIPEFAIL-EARLY-CONSUMER
        """
        repo = self._repo_with_index(
            tmp_path / "wt", ids=[0, 0], n_rows=2, padding_paths=384
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None, "a broken index must not reach the remote"
        assert "which item owns which embedding row" in reason, (
            f"denied for the wrong reason: {reason}"
        )

    def test_check10_denies_push_of_non_bijective_domain_index(self, tmp_path):
        """The routing matrix gets the same check (BACKLOG #218 sibling).

        Covers: FM-HOOK-PIPEFAIL-EARLY-CONSUMER
        """
        repo = self._repo_with_index(
            tmp_path / "wt",
            ids=[0, 1],
            n_rows=2,
            domain_ids=[0, 0],
            padding_paths=384,
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        # Assert on text ONLY the domain branch emits — "embedding row" appears in
        # the static deny message, so it would pass if the content branch fired.
        assert reason is not None and "domain_configs" in reason, (
            f"broken domain routing ids were not caught by the domain branch: {reason}"
        )

    def test_check10_passes_healthy_index(self, tmp_path):
        """The false-positive direction — this is what keeps the gate trusted.

        Covers: FM-HOOK-PIPEFAIL-EARLY-CONSUMER
        """
        repo = self._repo_with_index(
            tmp_path / "wt", ids=[0, 1], n_rows=2, padding_paths=384
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None or "embedding row" not in reason, (
            f"healthy index denied by the row-identity probe: {reason}"
        )

    def test_check10_ignores_pushes_that_do_not_touch_the_index(self, tmp_path):
        """Scoped to index/ changes — it must not run on every push.

        The index here is COMPLETE and BROKEN, and a later commit touches an
        unrelated file. If the shell-builtin index-path scoping guard were deleted,
        the probe would run and deny — so this test fails when the scoping is
        lost. An earlier version left the .npy absent, which made the probe
        short-circuit on its own existence check and proved nothing.
        """
        import os
        import subprocess

        repo = self._repo_with_index(tmp_path / "wt", ids=[0, 0], n_rows=2)
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
        )
        (repo / "unrelated.txt").write_text("no index here")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "docs only"], cwd=repo, check=True, env=env
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None or "embedding row" not in reason, (
            f"probe fired on a push whose commit range does not touch index/: {reason}"
        )

    def test_check10_skips_rather_than_denies_on_malformed_index(self, tmp_path):
        """Fail SAFE: a structurally surprising artifact must skip, not block.

        Over-blocking trains QUALITY_GATE_SKIP=true, which also disables the
        secret scanner — strictly worse than missing one broken index.
        """
        import numpy as np

        repo = self._repo_with_index(tmp_path / "wt", ids=[0, 1], n_rows=2)
        # `domains` is a list, not a mapping — .values() would raise.
        (repo / "index" / "global_index.json").write_text(json.dumps({"domains": []}))
        np.save(repo / "index" / "content_embeddings.npy", np.zeros((2, 4)))
        self._commit_all(repo, "break the index shape")
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None or "embedding row" not in reason, (
            f"malformed index DENIED the push instead of skipping: {reason}"
        )

    @pytest.mark.parametrize(
        "command,should_gate",
        [
            # These bypassed the ENTIRE gate — all eleven checks, including the
            # force-push block and the secret scanner — because the entry test
            # was anchored at start-of-string.
            ("git -C /some/path push --force origin main", True),
            ("cd /tmp && git push --force", True),
            ("(git push --force origin main)", True),
            ("git -c user.name=x push origin main", True),
            ("git --git-dir=/p/.git push origin main", True),
            # Ordinary form must still gate.
            ("git push origin main", True),
            # And prose about a push must NOT gate — quoted regions are stripped,
            # so a commit message or a grep pattern is not a push.
            ("git commit -m 'prep for git push later'", False),
            ('grep -rn "git push" docs/', False),
            ("git status", False),
            ("echo 'remember to git push'", False),
        ],
    )
    def test_gate_entry_matches_push_in_any_command_position(
        self, tmp_path, command, should_gate
    ):
        """The gate must recognise a push wherever it sits in the command.

        A start-of-string anchor is not a security boundary: anything before
        `git` defeats it. `git -C <path> push` is a normal thing to type when
        working across worktrees, not an exotic evasion, and it skipped every
        check in this file.
        """
        # A THROWAWAY repo with a pending commit — never PROJECT_DIR. Pointing at
        # the real repo made the result depend on whether anything was unpushed:
        # after a push the gate exits at "no changed files" and produces no output,
        # so the test flipped from pass to fail on an unrelated `git push`. A test
        # whose verdict depends on the developer's push state is not a test.
        repo = self._push_repo(tmp_path / "wt", "import sys\nsys.exit(0)\n")
        transcript = tmp_path / "t.jsonl"
        transcript.write_text('{"role":"assistant"}\n')
        hook_input = json.dumps(
            {
                "tool_input": {"command": command},
                "transcript_path": str(transcript),
                "cwd": str(repo),
            }
        )
        result = run_hook(
            PROJECT_DIR / ".claude" / "hooks" / "pre-push-quality-gate.sh",
            hook_input,
            env_overrides={"HOME": str(tmp_path)},
        )
        gated = bool(result.stdout.strip())
        assert gated == should_gate, (
            f"{command!r}: expected {'gated' if should_gate else 'not gated'}, "
            f"got {'gated' if gated else 'not gated'}"
        )

    def test_check11_denies_a_known_red_record(self, tmp_path):
        """Check 11 must be able to DENY. It shipped dead and nothing noticed.

        An incomplete rename left the matcher reading an unassigned variable.
        Under `set -u` the subshell died, but the reference sits inside
        `$(...) 2>/dev/null || echo ""`, so the failure was swallowed and the
        result was empty on every push — a check that always allows, which is
        indistinguishable from a check that finds nothing.

        It had been probed by hand when first written, and passed. The refactor
        came later. That is the whole argument for this test: a hand-probe
        certifies a moment, a test certifies every commit after it.
        """
        import json as _json

        repo = self._push_repo(tmp_path / "wt", "import sys\nsys.exit(0)\n")
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (repo / "logs").mkdir(exist_ok=True)
        (repo / "logs" / "check-runs.jsonl").write_text(
            _json.dumps(
                {
                    "ts": "t",
                    "commit": sha,
                    "mode": "normal",
                    "pass": 1,
                    "fail": 2,
                    "could_not_run": 0,
                    "seconds": 1,
                    "checks": [
                        {
                            "check": "alpha",
                            "status": "fail",
                            "seconds": 1,
                            "detail": "",
                        },
                        {"check": "beta", "status": "fail", "seconds": 1, "detail": ""},
                    ],
                }
            )
            + "\n"
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None, "known-red record did not deny"
        assert "local check run" in reason, f"denied for the wrong reason: {reason}"
        assert "alpha" in reason, "the deny message does not name the failing checks"

    def test_check11_allows_a_clean_record(self, tmp_path):
        """The false-positive direction — a green record must not deny."""
        import json as _json

        repo = self._push_repo(tmp_path / "wt", "import sys\nsys.exit(0)\n")
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
        ).stdout.strip()
        (repo / "logs").mkdir(exist_ok=True)
        (repo / "logs" / "check-runs.jsonl").write_text(
            _json.dumps(
                {
                    "ts": "t",
                    "commit": sha,
                    "mode": "normal",
                    "pass": 3,
                    "fail": 0,
                    "could_not_run": 0,
                    "seconds": 1,
                    "checks": [],
                }
            )
            + "\n"
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None or "local check run" not in reason, (
            f"clean record denied by Check 11: {reason}"
        )

    # --- Check 6: diff secret-scan vs the docs-only hatch (BACKLOG #232b) -----
    # The scan used to sit ~330 lines BELOW the docs-only escape hatch, so a push
    # whose changed files were all `.md`/`.json` exited at the hatch and was never
    # scanned. Measured 2026-07-25 by mutation probe: the SAME AWS key denied in a
    # `.py` file and ALLOWED in `creds.json` — and `.json` is where credentials
    # actually live. These tests pin the scan's POSITION by observing behaviour:
    # move the block back below the hatch and the first two go red.

    #: Built by concatenation on purpose. This very file is scanned by the gate
    #: under test, and a literal `AKIA…` here would deny the push that ships the
    #: fix. tests/test_enforcement.py uses the same split-construction dodge;
    #: tests/test_codex_hooks.py uses a bare literal — that one predates the gate
    #: covering its own repo, and this file cannot afford it.
    AWS_KEY_FIXTURE = "AKIA" + "IOSFODNN7EXAMPLE"

    def _repo_with_final_commit(
        self, root, files, gen_stub="import sys\nsys.exit(0)\n"
    ):
        """A push repo whose LAST commit touches exactly `files` (name -> content).

        The commit range the gate computes is HEAD~1..HEAD (no upstream, no
        origin/main), so `files` is precisely what the hook sees as changed.
        """
        repo = self._push_repo(root, gen_stub)
        for name, body in files.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        self._commit_all(repo, "final")
        return repo

    def test_check6_denies_credential_in_json_only_push(self, tmp_path):
        """The #232b regression: a config-only push must be scanned.

        `.json` is the highest-likelihood carrier — service-account blobs,
        `*.credentials.json`, an MCP config with an inline token — and it was
        the one shape the scanner could never see.
        """
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {"creds.json": '{"aws_access_key_id": "%s"}\n' % self.AWS_KEY_FIXTURE},
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None, (
            "a credential in a .json-only push was ALLOWED — the secret scan is "
            "below the docs-only hatch again (BACKLOG #232b)"
        )
        assert "Potential secret" in reason, f"denied for the wrong reason: {reason}"

    def test_check6_denies_credential_in_markdown_only_push(self, tmp_path):
        """Same hole, `.md` side: a pasted key in a runbook is docs-only too."""
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {"docs/runbook.md": "Set the key to %s\n" % self.AWS_KEY_FIXTURE},
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None and "Potential secret" in reason, (
            f"a credential in a .md-only push was not caught: {reason}"
        )

    def test_check6_still_denies_credential_in_code_push(self, tmp_path):
        """The behaviour that already worked must survive the move."""
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {"leak.py": 'AWS = "%s"\n' % self.AWS_KEY_FIXTURE},
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None and "Potential secret" in reason, (
            f"the pre-existing non-docs secret deny regressed: {reason}"
        )

    def test_check6_clean_docs_only_push_is_still_allowed(self, tmp_path):
        """The false-positive direction — the hatch itself must be intact.

        Blocking a clean docs push would train QUALITY_GATE_SKIP=true, which
        exits at the top of the hook and disables this very scanner. The content
        deliberately mentions key names and the string `AKIA` without a key-shaped
        value, because that is what real release notes look like.
        """
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {
                "README.md": (
                    "Use the env var AWS_ACCESS_KEY_ID; never commit a literal "
                    "key. Access-key ids start with AKIA followed by 16 chars.\n"
                ),
                "settings.json": '{"model": "claude-opus", "timeout_ms": 30000}\n',
            },
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is None, (
            f"a clean docs-only push was blocked — new false positive: {reason}"
        )

    def test_check6_credential_is_not_masked_by_a_cheaper_check(self, tmp_path):
        """Ordering claim, pinned: the strongest check reports first.

        This repo trips BOTH Check 8 (the generator stub reports count drift)
        and Check 6. If the secret scan sat after Check 8, the push would be
        denied for cosmetic drift and the credential would never be named — the
        user would fix the counts and push the key on the retry.
        """
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {"creds.json": '{"key": "%s"}\n' % self.AWS_KEY_FIXTURE},
            gen_stub="import sys\nsys.stderr.write('DRIFT: counts\\n')\nsys.exit(1)\n",
        )
        reason = self._deny_reason(self._gate(tmp_path, repo))
        assert reason is not None and "Potential secret" in reason, (
            "a cheaper check pre-empted the credential report — the user fixes "
            f"that instead and pushes the key on the retry: {reason}"
        )

    def test_check6_survives_a_large_matching_diff(self, tmp_path):
        """The scanner must not die between DETECTING a secret and REPORTING it.

        Found while reviewing the move (not by the move): the preview pipeline
        `echo "$SECRETS_FOUND" | head -1 | cut … | tr …` had no `|| true`. Under
        `set -euo pipefail`, `head -1` exits while `echo` still has data to write,
        the write takes SIGPIPE, and the whole hook dies at exit 141 — emitting
        NOTHING, which the host reads as ALLOW. The push then ships the very
        credential the scan just matched.

        The trigger is an ordinary minified `.json` (one long line), which is
        exactly the file shape this whole check exists to cover. Measured
        2026-07-25: with the guard removed this test's fixture reproduces exit
        141 and an empty stdout.
        """
        key = self.AWS_KEY_FIXTURE
        pad = "y" * 500_000
        repo = self._repo_with_final_commit(
            tmp_path / "wt",
            {
                # Three MATCHING added lines, the first two huge, so `head -1`
                # leaves ~500KB unwritten in the upstream `echo`.
                "bulk1.json": '{"pad":"%s","k":"%s"}\n' % (pad, key),
                "bulk2.json": '{"pad":"%s","k":"%s"}\n' % (pad, key),
                "creds.json": '{"k":"%s"}\n' % key,
            },
        )
        result = self._gate(tmp_path, repo)
        assert result.stdout.strip(), (
            "the hook emitted nothing on a large secret-bearing diff — it died "
            "mid-decision and the push would be ALLOWED (fail-open)"
        )
        reason = self._deny_reason(result)
        assert reason is not None and "Potential secret" in reason, (
            f"large diff was not denied for the secret it contains: {reason}"
        )

    def test_content_security_skip_writes_audit(self, tmp_path):
        content_security = (
            PROJECT_DIR / ".claude" / "hooks" / "pre-tool-content-security.sh"
        )
        hook_input = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "cat ~/.ssh/id_rsa"},
            }
        )
        result = run_hook(
            content_security,
            hook_input,
            env_overrides={
                "CONTENT_SECURITY_SKIP": "1",
                "HOME": str(tmp_path),
            },
        )
        assert result.returncode == 0
        log_file = tmp_path / ".claude" / "hook-bypass-audit.log"
        assert log_file.exists(), (
            "CONTENT_SECURITY_SKIP should write to bypass audit log"
        )
        content = log_file.read_text()
        assert "pre-tool-content-security" in content
        assert "CONTENT_SECURITY_SKIP=1" in content

    def test_audit_log_rotation(self, tmp_path):
        """Unified bypass audit log rotates at 100KB."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)
        log_file = claude_dir / "hook-bypass-audit.log"
        filler_line = "x" * 59 + "\n"
        log_file.write_text(filler_line * 2000)
        initial_size = log_file.stat().st_size
        assert initial_size > 100_000

        content_security = (
            PROJECT_DIR / ".claude" / "hooks" / "pre-tool-content-security.sh"
        )
        hook_input = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "cat ~/.ssh/id_rsa"},
            }
        )
        run_hook(
            content_security,
            hook_input,
            env_overrides={
                "CONTENT_SECURITY_SKIP": "1",
                "HOME": str(tmp_path),
            },
        )
        final_size = log_file.stat().st_size
        assert final_size < initial_size, (
            f"log should have been rotated; initial={initial_size}, final={final_size}"
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


# ---------------------------------------------------------------------------
# MCP availability auto-degrade (cloud/CCR sessions)
# ---------------------------------------------------------------------------


class TestPreToolMcpAutoDegrade:
    """When the gated MCP servers are not configured in any session config
    surface, the hard-mode gate auto-degrades to advisory — a session that
    cannot call the tools cannot satisfy a fail-closed gate (cloud/CCR clone).

    Covers: FM-HOOK-GOVERNANCE-GATE-REQUIRED (degrade path)
    """

    def _empty_home(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        return str(home)

    def _sandbox_project(self, tmp_path):
        """Empty project root so detection never reads the real repo's config
        surfaces (hermeticity: the real repo could gain a .mcp.json or quoted
        server keys later and silently flip these tests)."""
        proj = tmp_path / "proj"
        proj.mkdir()
        return str(proj)

    def _configured_home(self, tmp_path):
        home = tmp_path / "home"
        home.mkdir()
        (home / ".claude.json").write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "ai-governance": {"command": "x"},
                        "context-engine": {"command": "x"},
                    }
                }
            )
        )
        return str(home)

    def test_unconfigured_session_degrades_to_advisory(self, tmp_path):
        """No MCP config anywhere -> reminder via additionalContext, not deny."""
        transcript_path = create_transcript([make_filler_entry()])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "MCP_DETECT_SKIP": "false",
                    "HOME": self._empty_home(tmp_path),
                    "GOVERNANCE_PROJECT_ROOT": self._sandbox_project(tmp_path),
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert "additionalContext" in output["hookSpecificOutput"]
            assert "permissionDecision" not in output["hookSpecificOutput"]
            assert "auto-degraded" in output["hookSpecificOutput"]["additionalContext"]
        finally:
            os.unlink(transcript_path)

    def test_configured_home_stays_fail_closed(self, tmp_path):
        """Servers configured in ~/.claude.json -> hard mode preserved (deny)."""
        transcript_path = create_transcript([make_filler_entry()])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "MCP_DETECT_SKIP": "false",
                    "HOME": self._configured_home(tmp_path),
                    "GOVERNANCE_PROJECT_ROOT": self._sandbox_project(tmp_path),
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_detect_skip_restores_fail_closed(self, tmp_path):
        """MCP_DETECT_SKIP=true -> strict hard mode even when unconfigured."""
        transcript_path = create_transcript([make_filler_entry()])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "MCP_DETECT_SKIP": "true",
                    "HOME": self._empty_home(tmp_path),
                    "GOVERNANCE_PROJECT_ROOT": self._sandbox_project(tmp_path),
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        finally:
            os.unlink(transcript_path)

    def test_partial_config_keeps_configured_tool_hard(self, tmp_path):
        """Gov configured but NOT called; CE unconfigured -> DENY (gov gate
        stayed hard) while the reminder carries the CE auto-degrade note.

        This pins the per-tool asymmetry: a configured tool's gate must not
        ride along with an unconfigured sibling's degrade.
        """
        home = tmp_path / "home"
        home.mkdir()
        (home / ".claude.json").write_text(
            json.dumps({"mcpServers": {"ai-governance": {"command": "x"}}})
        )
        transcript_path = create_transcript([make_filler_entry()])
        try:
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = run_hook(
                PRETOOL_HOOK,
                hook_input,
                env_overrides={
                    "MCP_DETECT_SKIP": "false",
                    "HOME": str(home),
                    "GOVERNANCE_PROJECT_ROOT": self._sandbox_project(tmp_path),
                },
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            reason = output["hookSpecificOutput"]["permissionDecisionReason"]
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert "GOVERNANCE NOT DETECTED" in reason
            assert "auto-degraded" in reason
        finally:
            os.unlink(transcript_path)

    def test_home_unset_does_not_abort_fail_open(self, tmp_path):
        """Unset HOME must not abort the script under set -u (an abort with
        no JSON output is fail-OPEN in PreToolUse semantics). Detection
        proceeds with the HOME surface absent -> advisory output, exit 0."""
        transcript_path = create_transcript([make_filler_entry()])
        try:
            env = os.environ.copy()
            env.pop("HOME", None)
            env["GOVERNANCE_HOOK_DEBUG"] = "false"
            env["MCP_DETECT_SKIP"] = "false"
            env["GOVERNANCE_PROJECT_ROOT"] = self._sandbox_project(tmp_path)
            hook_input = json.dumps({"transcript_path": transcript_path})
            result = subprocess.run(
                ["bash", str(PRETOOL_HOOK)],
                input=hook_input,
                capture_output=True,
                text=True,
                env=env,
                timeout=15,
            )
            assert result.returncode == 0, result.stderr
            output = json.loads(result.stdout)
            assert "additionalContext" in output["hookSpecificOutput"]
        finally:
            os.unlink(transcript_path)
