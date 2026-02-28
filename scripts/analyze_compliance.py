#!/usr/bin/env python3
"""Compliance analysis for Claude Code transcripts.

Parses JSONL transcripts to measure governance and context engine compliance rates.

Usage:
    python scripts/analyze_compliance.py <transcript_path_or_dir>
    python scripts/analyze_compliance.py <path1> <path2> ...

Outputs per-session and aggregate compliance metrics.
"""

import json
import sys
from pathlib import Path


GOV_TOOL = "mcp__ai-governance__evaluate_governance"
CE_TOOL = "mcp__context-engine__query_project"
FILE_MODIFYING_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit"}


def analyze_transcript(path: Path) -> dict:
    """Analyze a single transcript for compliance.

    Returns dict with:
        - gov_calls: number of evaluate_governance() calls
        - ce_calls: number of query_project() calls
        - file_mod_calls: number of file-modifying tool calls
        - gov_positions: list of line numbers where governance was called
        - ce_positions: list of line numbers where CE was called
        - file_mod_positions: list of line numbers where file-modifying tools were called
        - gaps: list of file-mod positions without a preceding governance/CE call within 200 lines
        - classification: COMPLIANT / PARTIAL / NON_COMPLIANT
    """
    gov_calls = 0
    ce_calls = 0
    file_mod_calls = 0
    gov_positions = []
    ce_positions = []
    file_mod_positions = []

    try:
        with open(path, "r") as f:
            for line_num, line in enumerate(f, 1):
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

                    name = block.get("name", "")

                    if name == GOV_TOOL:
                        gov_calls += 1
                        gov_positions.append(line_num)
                    elif name == CE_TOOL:
                        ce_calls += 1
                        ce_positions.append(line_num)

                    # Check if tool name matches file-modifying tools
                    # Tool names can be bare (Edit) or prefixed (mcp__...)
                    base_name = name.split("__")[-1] if "__" in name else name
                    if (
                        base_name in FILE_MODIFYING_TOOLS
                        or name in FILE_MODIFYING_TOOLS
                    ):
                        file_mod_calls += 1
                        file_mod_positions.append(line_num)

    except Exception as e:
        return {"error": str(e), "path": str(path)}

    # Classify compliance
    if file_mod_calls == 0:
        classification = "COMPLIANT"  # No file modifications = nothing to enforce
    elif gov_calls > 0 and ce_calls > 0:
        classification = "COMPLIANT"
    elif gov_calls > 0 or ce_calls > 0:
        classification = "PARTIAL"
    else:
        classification = "NON_COMPLIANT"

    # Recency analysis: find file-mod calls without recent governance/CE
    window = 200
    gaps = []
    for pos in file_mod_positions:
        gov_recent = any((pos - window) <= gp <= pos for gp in gov_positions)
        ce_recent = any((pos - window) <= cp <= pos for cp in ce_positions)
        if not gov_recent or not ce_recent:
            gaps.append(pos)

    return {
        "path": str(path),
        "gov_calls": gov_calls,
        "ce_calls": ce_calls,
        "file_mod_calls": file_mod_calls,
        "gov_positions": gov_positions,
        "ce_positions": ce_positions,
        "file_mod_positions": file_mod_positions,
        "gaps": gaps,
        "classification": classification,
    }


def print_report(results: list[dict]) -> None:
    """Print aggregate compliance report."""
    total = len(results)
    compliant = sum(1 for r in results if r.get("classification") == "COMPLIANT")
    partial = sum(1 for r in results if r.get("classification") == "PARTIAL")
    non_compliant = sum(
        1 for r in results if r.get("classification") == "NON_COMPLIANT"
    )
    errors = sum(1 for r in results if "error" in r)

    print("=" * 60)
    print("GOVERNANCE COMPLIANCE REPORT")
    print("=" * 60)
    print()

    for r in results:
        if "error" in r:
            print(f"  ERROR: {r['path']} — {r['error']}")
            continue
        path = Path(r["path"]).name
        cls = r["classification"]
        gov = r["gov_calls"]
        ce = r["ce_calls"]
        mods = r["file_mod_calls"]
        gaps = len(r["gaps"])
        print(
            f"  {cls:<15} {path}  (gov={gov}, ce={ce}, file_mods={mods}, gaps={gaps})"
        )

    print()
    print("-" * 60)
    print(f"  Total sessions:  {total}")
    print(
        f"  Compliant:       {compliant} ({compliant / total * 100:.0f}%)"
        if total
        else ""
    )
    print(
        f"  Partial:         {partial} ({partial / total * 100:.0f}%)" if total else ""
    )
    print(
        f"  Non-compliant:   {non_compliant} ({non_compliant / total * 100:.0f}%)"
        if total
        else ""
    )
    if errors:
        print(f"  Errors:          {errors}")
    print("-" * 60)

    # Output JSON for machine consumption
    summary = {
        "total_sessions": total,
        "compliant": compliant,
        "partial": partial,
        "non_compliant": non_compliant,
        "compliance_rate": compliant / total if total else 0,
        "sessions": results,
    }
    print()
    print("JSON summary:")
    print(json.dumps(summary, indent=2, default=str))


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/analyze_compliance.py <transcript_path_or_dir> ..."
        )
        sys.exit(1)

    paths = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.jsonl")))
        elif p.is_file():
            paths.append(p)
        else:
            print(f"Warning: {arg} not found, skipping")

    if not paths:
        print("No transcript files found.")
        sys.exit(1)

    results = [analyze_transcript(p) for p in paths]
    print_report(results)


if __name__ == "__main__":
    main()
