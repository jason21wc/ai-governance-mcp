#!/usr/bin/env python3
"""Feedback loop analysis for AI Governance MCP Server.

Reads the server's JSONL log files (governance_audit, governance_reasoning,
queries, feedback) and produces structured analysis: effectiveness metrics,
dead principle detection, false-positive patterns, retrieval gaps, maturity
proposals, and actionable recommendations.

Subsumes BACKLOG items #42, #22, #44, #153.

Usage:
    python scripts/analyze_feedback_loop.py [--log-dir PATH] [--index-dir PATH]
        [--output PATH] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--print-summary]
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Phase 1: Log reading and filtering
# ---------------------------------------------------------------------------


def read_jsonl_logs(log_dir: Path, log_name: str) -> list[dict]:
    """Read a JSONL log file and its rotated backups, merged chronologically.

    Reads {log_name}.jsonl.5 through .jsonl.1 (oldest first), then the
    primary {log_name}.jsonl. Skips malformed/empty lines.
    """
    log_dir = Path(log_dir)
    entries = []

    files = []
    for i in range(5, 0, -1):
        p = log_dir / f"{log_name}.jsonl.{i}"
        if p.exists():
            files.append(p)
    primary = log_dir / f"{log_name}.jsonl"
    if primary.exists():
        files.append(primary)

    for path in files:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue

    return entries


def filter_by_time_range(
    entries: list[dict],
    start: str | None = None,
    end: str | None = None,
    timestamp_field: str = "timestamp",
) -> list[dict]:
    """Filter entries by ISO timestamp range (lexicographic comparison)."""
    result = entries
    if start:
        result = [e for e in result if e.get(timestamp_field, "") >= start]
    if end:
        result = [e for e in result if e.get(timestamp_field, "") <= end]
    return result


# ---------------------------------------------------------------------------
# Phase 2: Effectiveness metrics
# ---------------------------------------------------------------------------

CONFIDENCE_SCORES = {"high": 1.0, "medium": 0.5, "low": 0.2}


def compute_m001_influence_rate(audit_entries: list[dict]) -> dict:
    """M-001: Governance Influence Rate.

    Fraction of evaluations where governance engaged with the decision:
    REVIEW + ESCALATE + retroactive PROCEED-with-principles.

    Methodology v2 (2026-05-08): REVIEW status added. Old PROCEED entries
    with non-empty principles_consulted are retroactively classified as
    influenced. Pre-v2 logs used PROCEED for both "nothing found" and
    "principles found" — the retroactive classification corrects this.
    """
    if not audit_entries:
        return {"value": None, "total": 0, "breakdown": {}, "insufficient_data": True}

    counts = Counter(e.get("assessment", "UNKNOWN") for e in audit_entries)
    total = len(audit_entries)

    # Count explicit REVIEW + backward-compat PROCEED_WITH_MODIFICATIONS + ESCALATE
    influenced = (
        counts.get("REVIEW", 0)
        + counts.get("PROCEED_WITH_MODIFICATIONS", 0)
        + counts.get("ESCALATE", 0)
    )

    # Retroactive: old PROCEED entries with principles_consulted are governance-engaged
    for entry in audit_entries:
        if entry.get("assessment") == "PROCEED" and entry.get("principles_consulted"):
            influenced += 1

    return {
        "value": influenced / total,
        "total": total,
        "breakdown": dict(counts),
        "methodology_version": 2,
        "insufficient_data": False,
    }


def compute_m003_relevance_trend(query_entries: list[dict]) -> dict:
    """M-003: Retrieval Relevance Trend.

    Maps top_confidence strings to numeric scores and computes trend
    by comparing first-half vs second-half averages.
    """
    scores = []
    for e in query_entries:
        conf = e.get("top_confidence")
        if conf in CONFIDENCE_SCORES:
            scores.append(CONFIDENCE_SCORES[conf])

    if not scores:
        return {
            "current_avg": None,
            "trend": None,
            "first_half_avg": None,
            "second_half_avg": None,
            "scored_entries": 0,
            "insufficient_data": True,
        }

    current_avg = sum(scores) / len(scores)

    mid = len(scores) // 2
    first_half = scores[:mid] if mid > 0 else scores
    second_half = scores[mid:] if mid > 0 else scores
    first_avg = sum(first_half) / len(first_half) if first_half else 0
    second_avg = sum(second_half) / len(second_half) if second_half else 0

    if first_avg == 0:
        trend = "stable"
    else:
        change = (second_avg - first_avg) / first_avg
        if change > 0.1:
            trend = "improving"
        elif change < -0.1:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "current_avg": current_avg,
        "trend": trend,
        "first_half_avg": first_avg,
        "second_half_avg": second_avg,
        "scored_entries": len(scores),
        "insufficient_data": False,
    }


def compute_m004_s_series_rate(audit_entries: list[dict]) -> dict:
    """M-004: S-Series Trip Rate.

    Fraction of evaluations where s_series_triggered is true,
    decomposed by principle ID.
    """
    if not audit_entries:
        return {
            "value": None,
            "total": 0,
            "triggered_count": 0,
            "by_principle": {},
            "insufficient_data": True,
        }

    total = len(audit_entries)
    triggered = [e for e in audit_entries if e.get("s_series_triggered")]
    by_principle: Counter = Counter()
    for e in triggered:
        for pid in e.get("principles_consulted", []):
            by_principle[pid] += 1

    return {
        "value": len(triggered) / total,
        "total": total,
        "triggered_count": len(triggered),
        "by_principle": dict(by_principle),
        "insufficient_data": False,
    }


# ---------------------------------------------------------------------------
# Phase 3: Pattern detection
# ---------------------------------------------------------------------------


def detect_dead_principles(
    query_entries: list[dict],
    all_principle_ids: set[str],
    days_threshold: int = 90,
) -> list[dict]:
    """Find principles in the index that are never or rarely retrieved."""
    if not all_principle_ids:
        return []

    last_seen: dict[str, str | None] = {pid: None for pid in all_principle_ids}

    for entry in query_entries:
        ts = entry.get("timestamp", "")
        for pid in entry.get("principles_returned", []):
            if pid in last_seen:
                if last_seen[pid] is None or ts > last_seen[pid]:
                    last_seen[pid] = ts

    insufficient = len(query_entries) == 0
    now_str = datetime.now(timezone.utc).isoformat()
    dead = []

    for pid, ts in sorted(last_seen.items()):
        if ts is None:
            dead.append(
                {
                    "id": pid,
                    "last_seen": None,
                    "days_inactive": None,
                    "insufficient_data": insufficient,
                }
            )
        else:
            try:
                last_dt = datetime.fromisoformat(ts)
                now_dt = datetime.fromisoformat(now_str)
                days_inactive = (now_dt - last_dt).days
                if days_inactive >= days_threshold:
                    dead.append(
                        {
                            "id": pid,
                            "last_seen": ts,
                            "days_inactive": days_inactive,
                            "insufficient_data": False,
                        }
                    )
            except (ValueError, TypeError):
                continue

    return dead


def detect_retrieval_gaps(
    query_entries: list[dict],
    min_occurrences: int = 3,
) -> list[dict]:
    """Find queries with consistently low confidence scores."""
    if not query_entries:
        return []

    grouped: dict[str, list] = defaultdict(list)
    for entry in query_entries:
        query = entry.get("query", "").strip().lower()
        conf = entry.get("top_confidence")
        if query and conf in CONFIDENCE_SCORES:
            grouped[query].append(CONFIDENCE_SCORES[conf])

    gaps = []
    for query_text, scores in sorted(grouped.items()):
        if len(scores) < min_occurrences:
            continue
        avg = sum(scores) / len(scores)
        if avg <= CONFIDENCE_SCORES["low"]:
            gaps.append(
                {
                    "query_pattern": query_text,
                    "avg_confidence": avg,
                    "count": len(scores),
                }
            )

    return gaps


def detect_false_positive_patterns(
    audit_entries: list[dict],
    reasoning_entries: list[dict],
    min_triggers: int = 3,
) -> list[dict]:
    """Find principles that repeatedly cause ESCALATE assessments."""
    if not audit_entries:
        return []

    escalate_principles: Counter = Counter()
    escalate_actions: dict[str, list[str]] = defaultdict(list)

    for entry in audit_entries:
        if entry.get("assessment") != "ESCALATE":
            continue
        if not entry.get("s_series_triggered"):
            continue
        action = entry.get("action", "")
        for pid in entry.get("principles_consulted", []):
            escalate_principles[pid] += 1
            escalate_actions[pid].append(action[:100])

    patterns = []
    for pid, count in escalate_principles.most_common():
        if count < min_triggers:
            break
        actions = escalate_actions.get(pid, [])
        patterns.append(
            {
                "principle_id": pid,
                "trigger_count": count,
                "sample_actions": actions[:5],
            }
        )

    return patterns


def compute_maturity_proposals(
    query_entries: list[dict],
    feedback_entries: list[dict],
    reference_entries: list[dict],
) -> dict:
    """Compute maturity promotion/demotion proposals for reference library entries.

    Uses retrieval frequency from queries.jsonl (references_returned field).
    Old log entries without the field are excluded from the denominator.
    Requires >=20 field-present entries before computing decay proposals.
    """
    MIN_ENTRIES_FOR_DECAY = 20
    PROMOTION_THRESHOLD = 3

    field_present = [e for e in query_entries if "references_returned" in e]
    field_present_count = len(field_present)

    retrieval_counts: dict[str, int] = {}
    for entry in field_present:
        for ref_id in entry.get("references_returned", []):
            retrieval_counts[ref_id] = retrieval_counts.get(ref_id, 0) + 1

    ref_index = {r["id"]: r for r in reference_entries}

    proposals: list[dict] = []

    for ref_id, count in retrieval_counts.items():
        ref = ref_index.get(ref_id)
        if ref and ref.get("maturity") == "seedling" and count >= PROMOTION_THRESHOLD:
            proposals.append(
                {
                    "type": "promotion",
                    "reference_id": ref_id,
                    "current_maturity": "seedling",
                    "proposed_maturity": "budding",
                    "evidence": f"Retrieved {count} times across {field_present_count} logged queries",
                }
            )

    if field_present_count >= MIN_ENTRIES_FOR_DECAY:
        for ref in reference_entries:
            ref_id = ref["id"]
            if retrieval_counts.get(ref_id, 0) == 0:
                proposals.append(
                    {
                        "type": "decay",
                        "reference_id": ref_id,
                        "current_maturity": ref.get("maturity", "unknown"),
                        "evidence": f"Not retrieved in any of {field_present_count} logged queries with reference tracking",
                    }
                )

    return {
        "proposals": proposals,
        "retrieval_counts": retrieval_counts,
        "field_present_entries": field_present_count,
    }


# ---------------------------------------------------------------------------
# Phase 4: Recommendations + pipeline
# ---------------------------------------------------------------------------


def generate_recommendations(analysis: dict) -> list[dict]:
    """Generate actionable recommendations from analysis results."""
    recs = []

    for dp in analysis.get("dead_principles", []):
        if dp.get("insufficient_data"):
            continue
        recs.append(
            {
                "type": "dead_principle",
                "action": "Review for removal or keyword update",
                "target": dp["id"],
                "evidence": f"Not retrieved in {dp.get('days_inactive', 'N/A')} days"
                if dp.get("days_inactive")
                else "Never retrieved in any logged query",
            }
        )

    for fp in analysis.get("false_positives", []):
        recs.append(
            {
                "type": "false_positive",
                "action": "Review S-Series threshold or keyword list",
                "target": fp["principle_id"],
                "evidence": f"Triggered ESCALATE {fp['trigger_count']} times",
            }
        )

    for gap in analysis.get("retrieval_gaps", []):
        recs.append(
            {
                "type": "retrieval_gap",
                "action": "Consider adding principles or improving keywords for this query pattern",
                "target": gap["query_pattern"],
                "evidence": f"Avg confidence {gap['avg_confidence']:.2f} across {gap['count']} occurrences",
            }
        )

    return recs


def _load_principle_ids(index_dir: Path) -> set[str]:
    """Load all principle IDs from the global index."""
    index_path = index_dir / "global_index.json"
    if not index_path.exists():
        return set()

    try:
        index = json.loads(index_path.read_text())
    except (json.JSONDecodeError, ValueError):
        return set()

    ids = set()
    for domain_data in index.get("domains", {}).values():
        if isinstance(domain_data, dict):
            for p in domain_data.get("principles", []):
                if isinstance(p, dict) and "id" in p:
                    ids.add(p["id"])
    return ids


def _load_reference_entries(index_dir: Path) -> list[dict]:
    """Load reference entries from the global index."""
    index_path = index_dir / "global_index.json"
    if not index_path.exists():
        return []

    try:
        index = json.loads(index_path.read_text())
    except (json.JSONDecodeError, ValueError):
        return []

    refs = []
    for domain_data in index.get("domains", {}).values():
        if isinstance(domain_data, dict):
            refs.extend(domain_data.get("references", []))
    return refs


def run_analysis(
    log_dir: Path,
    index_dir: Path,
    output_path: Path,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """Run the full feedback loop analysis pipeline."""
    log_dir = Path(log_dir)
    index_dir = Path(index_dir)
    output_path = Path(output_path)

    audit_entries = read_jsonl_logs(log_dir, "governance_audit")
    query_entries = read_jsonl_logs(log_dir, "queries")
    reasoning_entries = read_jsonl_logs(log_dir, "governance_reasoning")
    feedback_entries = read_jsonl_logs(log_dir, "feedback")

    if start or end:
        audit_entries = filter_by_time_range(audit_entries, start, end)
        query_entries = filter_by_time_range(query_entries, start, end)
        reasoning_entries = filter_by_time_range(reasoning_entries, start, end)
        feedback_entries = filter_by_time_range(feedback_entries, start, end)

    all_principle_ids = _load_principle_ids(index_dir)
    reference_entries = _load_reference_entries(index_dir)

    timestamps = [
        e.get("timestamp", "")
        for e in audit_entries + query_entries
        if e.get("timestamp")
    ]
    time_range_start = min(timestamps) if timestamps else None
    time_range_end = max(timestamps) if timestamps else None

    m001 = compute_m001_influence_rate(audit_entries)
    m003 = compute_m003_relevance_trend(query_entries)
    m004 = compute_m004_s_series_rate(audit_entries)

    dead = detect_dead_principles(query_entries, all_principle_ids)
    gaps = detect_retrieval_gaps(query_entries)
    fps = detect_false_positive_patterns(audit_entries, reasoning_entries)
    maturity = compute_maturity_proposals(
        query_entries, feedback_entries, reference_entries
    )

    analysis_for_recs = {
        "dead_principles": dead,
        "false_positives": fps,
        "retrieval_gaps": gaps,
    }
    recommendations = generate_recommendations(analysis_for_recs)

    result = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "time_range": {"start": time_range_start, "end": time_range_end},
        "log_stats": {
            "audit_entries": len(audit_entries),
            "query_entries": len(query_entries),
            "reasoning_entries": len(reasoning_entries),
            "feedback_entries": len(feedback_entries),
        },
        "effectiveness_metrics": {
            "m001_influence_rate": m001,
            "m003_relevance_trend": m003,
            "m004_s_series_rate": m004,
        },
        "dead_principles": dead,
        "false_positives": fps,
        "retrieval_gaps": gaps,
        "maturity_proposals": maturity,
        "actionable_recommendations": recommendations,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    return result


def _print_summary(result: dict) -> None:
    """Print a human-readable summary of the analysis."""
    stats = result["log_stats"]
    print(f"\n{'=' * 60}")
    print("FEEDBACK LOOP ANALYSIS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Computed: {result['computed_at']}")
    tr = result["time_range"]
    print(f"Range:    {tr['start'] or 'N/A'} to {tr['end'] or 'N/A'}")
    print(
        f"Entries:  {stats['audit_entries']} audit, {stats['query_entries']} query, "
        f"{stats['reasoning_entries']} reasoning, {stats['feedback_entries']} feedback"
    )

    print("\n--- Effectiveness Metrics ---")
    m = result["effectiveness_metrics"]
    m001 = m["m001_influence_rate"]
    if m001.get("insufficient_data"):
        print("M-001 Influence Rate:   insufficient data")
    else:
        print(
            f"M-001 Influence Rate:   {m001['value']:.1%} ({m001['total']} evaluations)"
        )
        for k, v in m001.get("breakdown", {}).items():
            print(f"  {k}: {v}")

    m003 = m["m003_relevance_trend"]
    if m003.get("insufficient_data"):
        print("M-003 Relevance Trend:  insufficient data")
    else:
        print(
            f"M-003 Relevance Trend:  {m003['current_avg']:.3f} avg, trend: {m003['trend']}"
        )

    m004 = m["m004_s_series_rate"]
    if m004.get("insufficient_data"):
        print("M-004 S-Series Rate:    insufficient data")
    else:
        print(
            f"M-004 S-Series Rate:    {m004['value']:.1%} ({m004['triggered_count']}/{m004['total']})"
        )
        for pid, count in sorted(
            m004.get("by_principle", {}).items(), key=lambda x: -x[1]
        )[:5]:
            print(f"  {pid}: {count}")

    dead = result["dead_principles"]
    print(f"\n--- Dead Principles: {len(dead)} ---")
    for d in dead[:10]:
        status = f"last seen {d['last_seen']}" if d["last_seen"] else "never retrieved"
        print(f"  {d['id']}: {status}")
    if len(dead) > 10:
        print(f"  ... and {len(dead) - 10} more")

    fps = result["false_positives"]
    print(f"\n--- False-Positive Patterns: {len(fps)} ---")
    for fp in fps[:5]:
        print(f"  {fp['principle_id']}: {fp['trigger_count']} ESCALATE triggers")

    gaps = result["retrieval_gaps"]
    print(f"\n--- Retrieval Gaps: {len(gaps)} ---")
    for g in gaps[:5]:
        print(
            f'  "{g["query_pattern"][:60]}": avg {g["avg_confidence"]:.2f} ({g["count"]}x)'
        )

    mat = result["maturity_proposals"]
    print("\n--- Maturity Proposals ---")
    if mat["proposals"]:
        for p in mat["proposals"]:
            print(f"  {p}")
    else:
        print(
            f"  No proposals ({mat.get('field_present_entries', 0)} entries with reference tracking)"
        )

    recs = result["actionable_recommendations"]
    print(f"\n--- Actionable Recommendations: {len(recs)} ---")
    for r in recs[:10]:
        print(f"  [{r['type']}] {r['action']}")
        print(f"    Target: {r['target']}")
        print(f"    Evidence: {r['evidence']}")

    print(f"\n{'=' * 60}\n")


def _find_project_root() -> Path:
    """Find the project root by looking for documents/domains.json."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "documents" / "domains.json").exists():
            return current
        current = current.parent
    return Path.cwd()


def main():
    project_root = _find_project_root()

    parser = argparse.ArgumentParser(
        description="Analyze AI Governance MCP Server feedback loop data."
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=project_root / "logs",
        help="Directory containing JSONL log files (default: {project}/logs)",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=project_root / "index",
        help="Directory containing global_index.json (default: {project}/index)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (default: {log-dir}/feedback_loop_analysis.json)",
    )
    parser.add_argument(
        "--start", type=str, default=None, help="Start date filter (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", type=str, default=None, help="End date filter (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--print-summary", action="store_true", help="Print human-readable summary"
    )

    args = parser.parse_args()
    output = args.output or (args.log_dir / "feedback_loop_analysis.json")

    result = run_analysis(args.log_dir, args.index_dir, output, args.start, args.end)

    if args.print_summary:
        _print_summary(result)
    else:
        print(f"Analysis written to {output}")


if __name__ == "__main__":
    main()
