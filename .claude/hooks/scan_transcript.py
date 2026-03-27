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

Exit code: always 0 (fail-open on errors)
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


if __name__ == "__main__":
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
