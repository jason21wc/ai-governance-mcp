#!/usr/bin/env python3
"""Compliance analysis for Claude Code transcripts.

Parses JSONL transcripts to measure governance and context engine compliance rates.

Usage:
    python scripts/analyze_compliance.py analyze <transcript_path_or_dir> ...
    python scripts/analyze_compliance.py baseline <path_or_dir> ... [--output FILE] [--label TEXT] [--deployment-date YYYY-MM-DD]
    python scripts/analyze_compliance.py compare <baseline_a> <baseline_b>

Subcommands:
    analyze   Run analysis and print enhanced report (default if no subcommand)
    baseline  Run analysis and save structured JSON snapshot
    compare   Load two baseline JSONs, compute deltas, print comparison
"""

import argparse
import json
import os
import statistics
import sys
from datetime import date, datetime
from pathlib import Path


GOV_TOOL = "mcp__ai-governance__evaluate_governance"
CE_TOOL = "mcp__context-engine__query_project"
FILE_MODIFYING_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit"}
RECENCY_WINDOW = 200

BUCKET_RANGES = {
    "trivial": (0, 0),
    "short": (1, 10),
    "medium": (11, 50),
    "long": (51, 100),
    "very_long": (101, float("inf")),
}


def _classify_bucket(file_mod_calls: int) -> str:
    """Classify session into a length bucket based on file modification count."""
    for bucket, (lo, hi) in BUCKET_RANGES.items():
        if lo <= file_mod_calls <= hi:
            return bucket
    return "very_long"  # unreachable for non-negative inputs; defensive fallback


def _classify_quality(
    combined_gap_rate: float, file_mod_calls: int, gov_calls: int, ce_calls: int
) -> str:
    """Classify compliance quality based on behavioral heuristics."""
    if file_mod_calls == 0:
        return "high"
    if gov_calls == 0 and ce_calls == 0:
        return "low"
    if combined_gap_rate > 0.7:
        return "low"
    if combined_gap_rate < 0.3:
        return "high"
    return "moderate"


def _nearest_preceding(pos: int, positions: list[int]) -> int | None:
    """Find the nearest preceding position from a sorted list.

    Returns the distance (pos - nearest) or None if no preceding position exists.
    """
    best = None
    for p in positions:
        if p <= pos:
            best = p
        else:
            break
    return (pos - best) if best is not None else None


def _compute_avg_proximity(
    file_mod_positions: list[int], call_positions: list[int]
) -> float | None:
    """Compute average line distance from file-mods to nearest preceding call."""
    if not call_positions or not file_mod_positions:
        return None
    distances = []
    for pos in file_mod_positions:
        dist = _nearest_preceding(pos, call_positions)
        if dist is not None:
            distances.append(dist)
    return statistics.mean(distances) if distances else None


def analyze_transcript(
    path: Path,
    deployment_date: date | None = None,
    recency_window: int = RECENCY_WINDOW,
) -> dict:
    """Analyze a single transcript for compliance.

    Returns dict with core fields (gov_calls, ce_calls, file_mod_calls, etc.)
    plus enhanced fields (gov_gaps, ce_gaps, gap rates, proximity, bucket, quality).
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
        classification = "COMPLIANT"
    elif gov_calls > 0 and ce_calls > 0:
        classification = "COMPLIANT"
    elif gov_calls > 0 or ce_calls > 0:
        classification = "PARTIAL"
    else:
        classification = "NON_COMPLIANT"

    # Recency analysis: find file-mod calls without recent governance/CE
    gaps = []
    gov_gaps = []
    ce_gaps = []
    for pos in file_mod_positions:
        gov_recent = any((pos - recency_window) <= gp <= pos for gp in gov_positions)
        ce_recent = any((pos - recency_window) <= cp <= pos for cp in ce_positions)
        if not gov_recent:
            gov_gaps.append(pos)
        if not ce_recent:
            ce_gaps.append(pos)
        # Combined gap = missing EITHER gov or CE (union of gov_gaps and ce_gaps)
        if not gov_recent or not ce_recent:
            gaps.append(pos)

    # Gap rates
    gov_gap_rate = len(gov_gaps) / file_mod_calls if file_mod_calls else 0.0
    ce_gap_rate = len(ce_gaps) / file_mod_calls if file_mod_calls else 0.0
    combined_gap_rate = len(gaps) / file_mod_calls if file_mod_calls else 0.0

    # Proximity
    avg_gov_proximity = _compute_avg_proximity(file_mod_positions, gov_positions)
    avg_ce_proximity = _compute_avg_proximity(file_mod_positions, ce_positions)

    # Session bucket
    session_bucket = _classify_bucket(file_mod_calls)

    # Compliance quality
    compliance_quality = _classify_quality(
        combined_gap_rate, file_mod_calls, gov_calls, ce_calls
    )

    # Enforcement era
    if deployment_date is not None:
        try:
            mtime = os.path.getmtime(path)
            file_date = datetime.fromtimestamp(mtime).date()
            enforcement_era = "pre" if file_date < deployment_date else "post"
        except OSError:
            enforcement_era = "unknown"
    else:
        enforcement_era = "unknown"

    return {
        "path": str(path),
        "gov_calls": gov_calls,
        "ce_calls": ce_calls,
        "file_mod_calls": file_mod_calls,
        "gov_positions": gov_positions,
        "ce_positions": ce_positions,
        "file_mod_positions": file_mod_positions,
        "gaps": gaps,
        "gov_gaps": gov_gaps,
        "ce_gaps": ce_gaps,
        "classification": classification,
        "gov_gap_rate": gov_gap_rate,
        "ce_gap_rate": ce_gap_rate,
        "combined_gap_rate": combined_gap_rate,
        "avg_gov_proximity": avg_gov_proximity,
        "avg_ce_proximity": avg_ce_proximity,
        "session_bucket": session_bucket,
        "compliance_quality": compliance_quality,
        "enforcement_era": enforcement_era,
    }


def _compute_aggregates(results: list[dict]) -> dict:
    """Compute aggregate metrics from a list of analysis results."""
    valid = [r for r in results if "error" not in r]
    total = len(valid)
    compliant = sum(1 for r in valid if r["classification"] == "COMPLIANT")

    total_file_mods = sum(r["file_mod_calls"] for r in valid)
    total_gaps = sum(len(r["gaps"]) for r in valid)
    total_gov_gaps = sum(len(r.get("gov_gaps", [])) for r in valid)
    total_ce_gaps = sum(len(r.get("ce_gaps", [])) for r in valid)

    gap_rate = total_gaps / total_file_mods if total_file_mods else 0.0
    gov_gap_rate = total_gov_gaps / total_file_mods if total_file_mods else 0.0
    ce_gap_rate = total_ce_gaps / total_file_mods if total_file_mods else 0.0

    # Per-session gap rates for median
    session_gap_rates = [
        r["combined_gap_rate"] for r in valid if r["file_mod_calls"] > 0
    ]
    median_gap_rate = statistics.median(session_gap_rates) if session_gap_rates else 0.0

    # By bucket
    by_bucket = {}
    for bucket in BUCKET_RANGES:
        bucket_sessions = [r for r in valid if r.get("session_bucket") == bucket]
        bucket_mods = sum(r["file_mod_calls"] for r in bucket_sessions)
        bucket_gaps = sum(len(r["gaps"]) for r in bucket_sessions)
        by_bucket[bucket] = {
            "count": len(bucket_sessions),
            "gap_rate": round(bucket_gaps / bucket_mods, 4) if bucket_mods else 0.0,
        }

    # By compliance quality
    by_quality = {}
    for quality in ("high", "moderate", "low"):
        q_sessions = [r for r in valid if r.get("compliance_quality") == quality]
        q_mods = sum(r["file_mod_calls"] for r in q_sessions)
        q_gaps = sum(len(r["gaps"]) for r in q_sessions)
        by_quality[quality] = {
            "count": len(q_sessions),
            "gap_rate": round(q_gaps / q_mods, 4) if q_mods else 0.0,
        }

    return {
        "total_sessions": total,
        "compliant": compliant,
        "compliance_rate": round(compliant / total, 4) if total else 0.0,
        "gap_rate": round(gap_rate, 4),
        "median_gap_rate": round(median_gap_rate, 4),
        "gov_gap_rate": round(gov_gap_rate, 4),
        "ce_gap_rate": round(ce_gap_rate, 4),
        "total_file_mods": total_file_mods,
        "total_gaps": total_gaps,
        "total_gov_gaps": total_gov_gaps,
        "total_ce_gaps": total_ce_gaps,
        "by_bucket": by_bucket,
        "by_compliance_quality": by_quality,
    }


def print_report(results: list[dict]) -> None:
    """Print aggregate compliance report with enhanced breakdowns."""
    valid = [r for r in results if "error" not in r]
    total = len(results)
    compliant = sum(1 for r in valid if r["classification"] == "COMPLIANT")
    partial = sum(1 for r in valid if r["classification"] == "PARTIAL")
    non_compliant = sum(1 for r in valid if r["classification"] == "NON_COMPLIANT")
    errors = sum(1 for r in results if "error" in r)

    print("=" * 64)
    print("GOVERNANCE COMPLIANCE REPORT")
    print("=" * 64)
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
        gap_count = len(r["gaps"])
        print(
            f"  {cls:<15} {path}  (gov={gov}, ce={ce}, file_mods={mods}, gaps={gap_count})"
        )

    print()
    print("-" * 64)
    print(f"  Total sessions:  {total}")
    if total:
        print(f"  Compliant:       {compliant} ({compliant / total * 100:.0f}%)")
        print(f"  Partial:         {partial} ({partial / total * 100:.0f}%)")
        print(
            f"  Non-compliant:   {non_compliant} ({non_compliant / total * 100:.0f}%)"
        )
    if errors:
        print(f"  Errors:          {errors}")
    print("-" * 64)

    # Enhanced breakdowns
    agg = _compute_aggregates(results)

    print()
    print("BREAKDOWN BY SESSION LENGTH")
    bucket_labels = {
        "trivial": "Trivial (0 mods)",
        "short": "Short (1-10 mods)",
        "medium": "Medium (11-50)",
        "long": "Long (51-100)",
        "very_long": "Very long (101+)",
    }
    for bucket, label in bucket_labels.items():
        info = agg["by_bucket"][bucket]
        if info["count"] == 0:
            print(f"  {label:<22} {info['count']:>3} sessions")
        else:
            rate_str = (
                f"gap_rate: {info['gap_rate']:.2f}" if bucket != "trivial" else ""
            )
            print(f"  {label:<22} {info['count']:>3} sessions  {rate_str}")

    print()
    print("BREAKDOWN BY COMPLIANCE QUALITY")
    for quality in ("high", "moderate", "low"):
        info = agg["by_compliance_quality"][quality]
        cap = quality.capitalize()
        print(
            f"  {cap + ':':<12} {info['count']:>3} sessions — avg_gap_rate: {info['gap_rate']:.2f}"
        )

    # Split gap rates (from aggregates — no re-computation)
    total_mods = agg["total_file_mods"]
    total_gov_gaps = agg["total_gov_gaps"]
    total_ce_gaps = agg["total_ce_gaps"]
    total_combined_gaps = agg["total_gaps"]

    print()
    print("SPLIT GAP RATES")
    print(
        f"  Combined gaps:    {total_combined_gaps}/{total_mods} = {agg['gap_rate'] * 100:.1f}%"
        f"  (median per-session: {agg['median_gap_rate']:.2f})"
    )
    print(
        f"  Governance gaps:  {total_gov_gaps}/{total_mods} = {agg['gov_gap_rate'] * 100:.1f}%"
    )
    print(
        f"  Context Engine:   {total_ce_gaps}/{total_mods} = {agg['ce_gap_rate'] * 100:.1f}%"
    )


def save_baseline(
    results: list[dict],
    output_path: Path,
    label: str = "",
    deployment_date: str | None = None,
    recency_window: int = RECENCY_WINDOW,
) -> None:
    """Save analysis results as a structured baseline JSON."""
    agg = _compute_aggregates(results)

    # Compact session records (strip position lists for storage)
    sessions = []
    for r in results:
        if "error" in r:
            sessions.append({"session": Path(r["path"]).stem, "error": r["error"]})
            continue
        sessions.append(
            {
                "session": Path(r["path"]).stem,
                "classification": r["classification"],
                "gov_calls": r["gov_calls"],
                "ce_calls": r["ce_calls"],
                "file_mod_calls": r["file_mod_calls"],
                "gap_count": len(r["gaps"]),
                "gov_gap_count": len(r.get("gov_gaps", [])),
                "ce_gap_count": len(r.get("ce_gaps", [])),
                "combined_gap_rate": r.get("combined_gap_rate", 0.0),
                "gov_gap_rate": r.get("gov_gap_rate", 0.0),
                "ce_gap_rate": r.get("ce_gap_rate", 0.0),
                "session_bucket": r.get("session_bucket", "unknown"),
                "compliance_quality": r.get("compliance_quality", "unknown"),
                "enforcement_era": r.get("enforcement_era", "unknown"),
                "avg_gov_proximity": r.get("avg_gov_proximity"),
                "avg_ce_proximity": r.get("avg_ce_proximity"),
            }
        )

    baseline = {
        "description": f"Compliance baseline{': ' + label if label else ''}",
        "date": date.today().isoformat(),
        "label": label,
        "deployment_date": deployment_date,
        "recency_window": recency_window,
        "aggregate": agg,
        "sessions": sessions,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2, default=str)
    print(f"Baseline saved to {output_path}")
    print(
        f"  Sessions: {agg['total_sessions']}, Gap rate: {agg['gap_rate']:.4f}, "
        f"Compliance rate: {agg['compliance_rate']:.4f}"
    )


def _fmt_pct(value: float | None) -> str:
    """Format a float as percentage string, or N/A if None."""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _fmt_delta(before: float | None, after: float | None) -> str:
    """Format delta between two values as percentage points."""
    if before is None or after is None:
        return "—"
    delta = (after - before) * 100
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:.1f}pp"


def compare_baselines(path_a: Path, path_b: Path) -> None:
    """Load two baseline JSONs and print a comparison report."""
    with open(path_a) as f:
        baseline_a = json.load(f)
    with open(path_b) as f:
        baseline_b = json.load(f)

    agg_a = baseline_a.get("aggregate", {})
    agg_b = baseline_b.get("aggregate", {})

    label_a = baseline_a.get("label") or baseline_a.get("date", "before")
    label_b = baseline_b.get("label") or baseline_b.get("date", "after")

    print(f"COMPLIANCE COMPARISON: {label_a} -> {label_b}")
    print("=" * 64)

    # Header
    print(f"{'':25} {'Before':>12} {'After':>12} {'Delta':>12}")

    # Sessions
    sa = agg_a.get("total_sessions", 0)
    sb = agg_b.get("total_sessions", 0)
    print(f"{'Sessions:':<25} {sa:>12} {sb:>12} {sb - sa:>+12}")

    # Total file mods
    ma = agg_a.get("total_file_mods", agg_a.get("total_file_mod_calls", 0))
    mb = agg_b.get("total_file_mods", agg_b.get("total_file_mod_calls", 0))
    print(f"{'Total file mods:':<25} {ma:>12} {mb:>12} {mb - ma:>+12}")

    # Gap rate (primary metric)
    gr_a = agg_a.get("gap_rate")
    gr_b = agg_b.get("gap_rate")
    print(
        f"{'Gap rate (primary):':<25} {_fmt_pct(gr_a):>12} {_fmt_pct(gr_b):>12} {_fmt_delta(gr_a, gr_b):>12}"
    )

    # Median per-session gap rate
    mgr_a = agg_a.get("median_gap_rate")
    mgr_b = agg_b.get("median_gap_rate")
    print(
        f"{'  Median per-session:':<25} {_fmt_pct(mgr_a):>12} {_fmt_pct(mgr_b):>12} {_fmt_delta(mgr_a, mgr_b):>12}"
    )

    # Gov gap rate
    ggr_a = agg_a.get("gov_gap_rate")
    ggr_b = agg_b.get("gov_gap_rate")
    print(
        f"{'Gov gap rate:':<25} {_fmt_pct(ggr_a):>12} {_fmt_pct(ggr_b):>12} {_fmt_delta(ggr_a, ggr_b):>12}"
    )

    # CE gap rate
    cgr_a = agg_a.get("ce_gap_rate")
    cgr_b = agg_b.get("ce_gap_rate")
    print(
        f"{'CE gap rate:':<25} {_fmt_pct(cgr_a):>12} {_fmt_pct(cgr_b):>12} {_fmt_delta(cgr_a, cgr_b):>12}"
    )

    # Compliance rate
    cr_a = agg_a.get("compliance_rate")
    cr_b = agg_b.get("compliance_rate")
    print(
        f"{'Compliance rate:':<25} {_fmt_pct(cr_a):>12} {_fmt_pct(cr_b):>12} {_fmt_delta(cr_a, cr_b):>12}"
    )

    # By session length
    bkt_a = agg_a.get("by_bucket", {})
    bkt_b = agg_b.get("by_bucket", {})
    if bkt_a or bkt_b:
        print()
        print("BY SESSION LENGTH:")
        bucket_labels = {
            "short": "Short (1-10)",
            "medium": "Medium (11-50)",
            "long": "Long (51-100)",
            "very_long": "Very long (101+)",
        }
        for bucket, label in bucket_labels.items():
            ba = bkt_a.get(bucket, {}).get("gap_rate")
            bb = bkt_b.get(bucket, {}).get("gap_rate")
            print(
                f"  {label + ':':<22} {_fmt_pct(ba):>8} -> {_fmt_pct(bb):>8}  {_fmt_delta(ba, bb):>10}"
            )

    # Notes about missing fields
    notes = []
    if ggr_a is None and ggr_b is not None:
        notes.append(
            "Gov/CE split not available in 'before' baseline (merged gap_count only)."
        )
    if not bkt_a and bkt_b:
        notes.append("Session buckets not available in 'before' baseline.")
    if notes:
        print()
        for note in notes:
            print(f"* {note}")
        print("  Regenerate with: analyze_compliance.py baseline <old_transcripts>")


def _resolve_paths(path_args: list[str]) -> list[Path]:
    """Resolve path arguments to a list of transcript file paths."""
    paths = []
    for arg in path_args:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.jsonl")))
        elif p.is_file():
            paths.append(p)
        else:
            print(f"Warning: {arg} not found, skipping")
    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Compliance analysis for Claude Code transcripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze", help="Run analysis and print enhanced report"
    )
    analyze_parser.add_argument(
        "paths", nargs="+", help="Transcript files or directories"
    )

    # baseline subcommand
    baseline_parser = subparsers.add_parser(
        "baseline", help="Run analysis and save structured JSON snapshot"
    )
    baseline_parser.add_argument(
        "paths", nargs="+", help="Transcript files or directories"
    )
    baseline_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output path (default: tests/benchmarks/compliance_baseline_<date>.json)",
    )
    baseline_parser.add_argument("--label", "-l", type=str, default="")
    baseline_parser.add_argument(
        "--deployment-date",
        type=str,
        default=None,
        help="Deployment date (YYYY-MM-DD) for pre/post era classification",
    )

    # compare subcommand
    compare_parser = subparsers.add_parser(
        "compare", help="Compare two baseline JSON files"
    )
    compare_parser.add_argument("baseline_a", help="First baseline JSON")
    compare_parser.add_argument("baseline_b", help="Second baseline JSON")

    args = parser.parse_args()

    # Default to analyze if no subcommand (backward compat)
    if args.command is None:
        # Check if raw args look like paths (no subcommand given)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            args.command = "analyze"
            args.paths = sys.argv[1:]
        else:
            parser.print_help()
            sys.exit(1)

    if args.command == "analyze":
        paths = _resolve_paths(args.paths)
        if not paths:
            print("No transcript files found.")
            sys.exit(1)
        results = [analyze_transcript(p) for p in paths]
        print_report(results)

    elif args.command == "baseline":
        deployment = None
        if args.deployment_date:
            deployment = date.fromisoformat(args.deployment_date)

        paths = _resolve_paths(args.paths)
        if not paths:
            print("No transcript files found.")
            sys.exit(1)

        results = [analyze_transcript(p, deployment_date=deployment) for p in paths]
        print_report(results)

        output = Path(
            args.output
            or f"tests/benchmarks/compliance_baseline_{date.today().isoformat()}.json"
        )
        save_baseline(
            results,
            output,
            label=args.label,
            deployment_date=args.deployment_date,
        )

    elif args.command == "compare":
        compare_baselines(Path(args.baseline_a), Path(args.baseline_b))


if __name__ == "__main__":
    main()
