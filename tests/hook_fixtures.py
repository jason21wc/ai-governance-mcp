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
