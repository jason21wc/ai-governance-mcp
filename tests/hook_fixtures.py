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
