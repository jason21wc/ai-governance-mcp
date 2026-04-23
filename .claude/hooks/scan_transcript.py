#!/usr/bin/env python3
"""Shared transcript scanner for governance and context engine compliance hooks.

Scans a Claude Code transcript (JSONL) for tool_use entries matching target
tool names. Supports a recency window to expire old calls.

Usage (governance mode):
    python3 scan_transcript.py <gov_tool_name> <ce_tool_name> <transcript_path> [window_size]
    Output: one of: both | gov_only | ce_only | neither

Usage (pattern mode):
    python3 scan_transcript.py --pattern <pattern> <transcript_path> [window_size]
    Output: true | false

Usage (contrarian-after-last-plan mode, for pre-exit-plan-mode-gate hook):
    python3 scan_transcript.py --contrarian-after-last-plan <transcript_path>
    Output: one of: allow | deny | bootstrap | error
      - allow: contrarian-reviewer tool_use found AFTER most recent prior ExitPlanMode
      - deny: prior ExitPlanMode exists but no contrarian invocation follows it
      - bootstrap: no prior ExitPlanMode in transcript (first plan of session)
      - error: read/parse failure (hook should treat as deny, fail-closed)

Exit code: always 0 (decision encoded in stdout; hook interprets)
"""

import json
import sys
from collections import deque


def scan_transcript(
    gov_target: str, ce_target: str, transcript_path: str, window_size: int = 0
) -> str:
    """Scan transcript for governance and CE tool calls.

    Args:
        gov_target: Tool name to match for governance (e.g. mcp__ai-governance__evaluate_governance)
        ce_target: Tool name to match for CE (e.g. mcp__context-engine__query_project)
        transcript_path: Path to JSONL transcript file
        window_size: If >0, only scan the last N lines (recency window). 0 = scan all.

    Returns:
        "both", "gov_only", "ce_only", or "neither"
    """
    gov_found = False
    ce_found = False

    try:
        with open(transcript_path, "r") as f:
            if window_size > 0:
                lines = deque(f, maxlen=window_size)
            else:
                lines = f

            for line in lines:
                # Fast pre-filter: skip lines that contain neither target
                if gov_target not in line and ce_target not in line:
                    continue
                # Only parse lines that contain at least one target string
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                # Check assistant tool_use entries
                msg = entry.get("message", {})
                if not isinstance(msg, dict):
                    continue
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name", "")
                        if name == gov_target:
                            gov_found = True
                        elif name == ce_target:
                            ce_found = True
                # Early exit if both found
                if gov_found and ce_found:
                    break
    except Exception:
        pass

    if gov_found and ce_found:
        return "both"
    elif gov_found:
        return "gov_only"
    elif ce_found:
        return "ce_only"
    else:
        return "neither"


def scan_for_pattern(
    pattern: str, transcript_path: str, window_size: int = 500
) -> bool:
    """Scan transcript for any line containing a pattern string.

    General-purpose pattern matching for quality gate checks.
    Used by pre-push-quality-gate.sh to check for test runs, subagent invocations, etc.

    Args:
        pattern: String to search for in transcript lines
        transcript_path: Path to JSONL transcript file
        window_size: Only scan last N lines (default 500)

    Returns:
        True if pattern found, False otherwise
    """
    try:
        with open(transcript_path, "r") as f:
            lines = deque(f, maxlen=window_size) if window_size > 0 else f
            for line in lines:
                if pattern in line:
                    return True
    except Exception:
        pass
    return False


def scan_contrarian_after_last_plan(transcript_path: str) -> str:
    """Check if contrarian-reviewer was invoked since the most recent prior ExitPlanMode.

    Fires in support of the pre-exit-plan-mode-gate hook. The hook runs BEFORE
    the current ExitPlanMode call, so the transcript contains PAST ExitPlanMode
    entries but not the one about to fire.

    Args:
        transcript_path: Path to JSONL transcript file.

    Returns:
        "allow"     — contrarian-reviewer tool_use found AFTER most recent prior
                      ExitPlanMode (or anywhere in bootstrap case).
        "deny"      — prior ExitPlanMode exists but no contrarian invocation since.
        "bootstrap" — no prior ExitPlanMode in transcript (first plan of session).
        "error"     — read/parse failure (hook should treat as deny per fail-closed).
    """
    contrarian_names = ("contrarian-reviewer", "contrarian_reviewer")

    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return "error"

    # Pass 1: find index of most recent ExitPlanMode tool_use
    last_exit_plan_idx = -1
    for idx, line in enumerate(lines):
        if "ExitPlanMode" not in line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "ExitPlanMode":
                last_exit_plan_idx = idx

    # Bootstrap case: no prior ExitPlanMode means this is the session's first plan.
    if last_exit_plan_idx == -1:
        return "bootstrap"

    # Pass 2: search for contrarian Task tool_use AFTER the anchor.
    # Scans from (anchor + 1) to EOF — never matches the anchor itself or earlier.
    for line in lines[last_exit_plan_idx + 1 :]:
        if "contrarian" not in line:  # fast pre-filter
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            # Task subagent_type form (standard path)
            if block.get("name") == "Task":
                inp = block.get("input", {})
                if isinstance(inp, dict):
                    st = inp.get("subagent_type", "")
                    if st in contrarian_names:
                        return "allow"
            # Direct-name form (MCP subagent or future variants)
            elif block.get("name", "") in contrarian_names:
                return "allow"

    return "deny"


if __name__ == "__main__":
    # Contrarian-after-last-plan mode: --contrarian-after-last-plan <transcript>
    if len(sys.argv) >= 3 and sys.argv[1] == "--contrarian-after-last-plan":
        transcript = sys.argv[2]
        print(scan_contrarian_after_last_plan(transcript))
        sys.exit(0)

    # Pattern mode: --pattern <pattern> <transcript> [window]
    if len(sys.argv) >= 4 and sys.argv[1] == "--pattern":
        pattern = sys.argv[2]
        transcript = sys.argv[3]
        try:
            window = int(sys.argv[4]) if len(sys.argv) > 4 else 500
        except (ValueError, TypeError):
            window = 500
        print("true" if scan_for_pattern(pattern, transcript, window) else "false")
        sys.exit(0)

    # Governance mode: <gov_tool> <ce_tool> <transcript> [window]
    if len(sys.argv) < 4:
        print("neither")
        sys.exit(0)

    gov_tool = sys.argv[1]
    ce_tool = sys.argv[2]
    transcript = sys.argv[3]
    try:
        window = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    except (ValueError, TypeError):
        window = 0

    print(scan_transcript(gov_tool, ce_tool, transcript, window))
