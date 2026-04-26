#!/usr/bin/env python3
"""A/B benchmark for template improvement plan Step 0.

Compares two interventions against the baseline:
  A: Add **Applies To:** metadata to 10 methods (content change, BM25 path)
  B: Extract subheaders/bold from full content in BM25 (code change)

Note: Semantic embeddings are loaded from disk and NOT regenerated.
This means we are testing BM25 improvements only (40% of hybrid score).
For a full test of semantic impact, we would need to regenerate embeddings.

Usage:
    python staging/benchmark_ab_test.py
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.config import Settings
from ai_governance_mcp.retrieval import RetrievalEngine


def load_benchmark():
    path = (
        Path(__file__).parent.parent / "tests" / "benchmarks" / "retrieval_quality.json"
    )
    with open(path) as f:
        return json.load(f)


def run_method_benchmark(engine, benchmark):
    results = {}
    for case in benchmark["test_cases"]["methods"]:
        query = case["query"]
        expected_id = case["expected_ids"][0]

        result = engine.retrieve(query, include_methods=True)

        rank = None
        score = None
        for i, m in enumerate(result.methods):
            if m.method.id == expected_id:
                rank = i + 1
                score = m.combined_score
                break

        results[case["id"]] = {
            "query": query,
            "expected": expected_id,
            "rank": rank,
            "score": float(score) if score else None,
        }

    ranks = [r["rank"] for r in results.values()]
    mrr = sum(1.0 / r for r in ranks if r is not None) / len(ranks)
    recall = sum(1 for r in ranks if r is not None and r <= 10) / len(ranks)

    return {"mrr": mrr, "recall_at_10": recall, "details": results}


INTERVENTION_A_ENTRIES = {
    "coding-method-calibration-questions": [
        "project",
        "complexity",
        "assessment",
        "initial",
        "setup",
        "difficulty",
        "estimation",
        "scaling",
        "rigor",
        "scope",
    ],
    "coding-method-cognitive-memory-types": [
        "session",
        "state",
        "management",
        "project",
        "memory",
        "architecture",
        "learning",
        "design",
        "organization",
        "persistence",
    ],
    "multi-method-governance-agent-pattern": [
        "governance",
        "enforcement",
        "multi",
        "agent",
        "orchestrator",
        "design",
        "compliance",
        "checking",
        "coordination",
    ],
    "coding-method-production-audit-logging": [
        "production",
        "observability",
        "compliance",
        "audit",
        "trails",
        "security",
        "event",
        "logging",
        "structured",
        "retention",
    ],
    "coding-method-service-identity-and-credential-lifecycle": [
        "management",
        "secret",
        "rotation",
        "credential",
        "vault",
        "integration",
        "service",
        "account",
        "provisioning",
        "expiry",
    ],
    "coding-method-diagnostic-block-requirement": [
        "debugging",
        "methodology",
        "root",
        "cause",
        "analysis",
        "instrumentation",
        "diagnosis",
        "hypothesis",
        "investigation",
    ],
    "multi-method-governance-enforcement-architecture": [
        "enforcement",
        "layers",
        "hook",
        "compliance",
        "proxy",
        "governance",
        "advisory",
        "structural",
        "skip",
    ],
    "kmpd-method-when-content-arrives-out-of-order": [
        "unstructured",
        "content",
        "processing",
        "curriculum",
        "sequencing",
        "prerequisite",
        "mapping",
        "reorganization",
        "knowledge",
    ],
    "meta-method-applying-the-framework-authoring-vs-review": [
        "content",
        "quality",
        "evaluation",
        "principle",
        "authoring",
        "framework",
        "review",
        "process",
        "admission",
        "selection",
    ],
    "coding-method-test-organization-patterns": [
        "test",
        "file",
        "structure",
        "pytest",
        "organization",
        "discovery",
        "fixture",
        "patterns",
        "naming",
        "conftest",
    ],
}


def apply_intervention_a(engine):
    """Add Applies To metadata to 10 methods in the loaded index."""
    modified = 0
    for domain_name, domain_idx in engine.index.domains.items():
        for m in domain_idx.methods:
            if m.id in INTERVENTION_A_ENTRIES:
                m.metadata.applies_to = INTERVENTION_A_ENTRIES[m.id]
                modified += 1
    return modified


def apply_intervention_b(engine):
    """Monkey-patch _get_method_bm25_text to extract from full content."""
    original_fn = engine._get_method_bm25_text

    def enhanced_bm25_text(method):
        base = original_fn(method)

        if len(method.content) > 1500:
            overflow = method.content[1500:]
            subheaders = re.findall(r"^#{3,4}\s+(.+)$", overflow, re.MULTILINE)
            header_words = []
            for h in subheaders[:10]:
                header_words.extend(w.lower() for w in h.split() if len(w) > 3)

            bold_terms = re.findall(r"\*\*([^*]+)\*\*", overflow)
            bold_words = []
            for b in bold_terms[:10]:
                if len(b.split()) <= 4 and len(b) > 5:
                    bold_words.append(b.lower())

            extra = " ".join(header_words[:15] + bold_words[:10])
            if extra:
                base = base + " " + extra

        return base

    engine._get_method_bm25_text = enhanced_bm25_text
    return original_fn


def main():
    print("=" * 70)
    print("STEP 0: A/B RETRIEVAL BENCHMARK")
    print("=" * 70)
    print("NOTE: Testing BM25 path only (40%% of hybrid score).")
    print("Semantic embeddings loaded from disk, not regenerated.")
    print()

    benchmark = load_benchmark()
    settings = Settings()

    # === BASELINE ===
    print("--- BASELINE ---")
    engine_base = RetrievalEngine(settings)
    baseline = run_method_benchmark(engine_base, benchmark)
    print("  Method MRR:      %.4f" % baseline["mrr"])
    print("  Method Recall@10: %.4f" % baseline["recall_at_10"])

    # === INTERVENTION A ===
    print("\n--- INTERVENTION A (Add Applies To metadata to 10 methods) ---")
    engine_a = RetrievalEngine(settings)
    modified = apply_intervention_a(engine_a)
    engine_a._build_bm25_index()
    print("  Modified %d methods" % modified)
    result_a = run_method_benchmark(engine_a, benchmark)
    print(
        "  Method MRR:      %.4f (delta: %+.4f)"
        % (result_a["mrr"], result_a["mrr"] - baseline["mrr"])
    )
    print(
        "  Method Recall@10: %.4f (delta: %+.4f)"
        % (
            result_a["recall_at_10"],
            result_a["recall_at_10"] - baseline["recall_at_10"],
        )
    )

    # === INTERVENTION B ===
    print("\n--- INTERVENTION B (Extract subheaders/bold from full content) ---")
    engine_b = RetrievalEngine(settings)
    apply_intervention_b(engine_b)
    engine_b._build_bm25_index()
    result_b = run_method_benchmark(engine_b, benchmark)
    print(
        "  Method MRR:      %.4f (delta: %+.4f)"
        % (result_b["mrr"], result_b["mrr"] - baseline["mrr"])
    )
    print(
        "  Method Recall@10: %.4f (delta: %+.4f)"
        % (
            result_b["recall_at_10"],
            result_b["recall_at_10"] - baseline["recall_at_10"],
        )
    )

    # === INTERVENTION A+B ===
    print("\n--- INTERVENTION A+B (Both combined) ---")
    engine_ab = RetrievalEngine(settings)
    apply_intervention_a(engine_ab)
    apply_intervention_b(engine_ab)
    engine_ab._build_bm25_index()
    result_ab = run_method_benchmark(engine_ab, benchmark)
    print(
        "  Method MRR:      %.4f (delta: %+.4f)"
        % (result_ab["mrr"], result_ab["mrr"] - baseline["mrr"])
    )
    print(
        "  Method Recall@10: %.4f (delta: %+.4f)"
        % (
            result_ab["recall_at_10"],
            result_ab["recall_at_10"] - baseline["recall_at_10"],
        )
    )

    # === PER-METHOD TABLE ===
    print("\n" + "=" * 70)
    print("PER-METHOD RANK COMPARISON")
    print("=" * 70)
    print(
        "%-12s %-6s %-6s %-6s %-6s  %-5s %s"
        % ("Method", "Base", "IntA", "IntB", "A+B", "Len", "Query")
    )
    print("-" * 90)

    # Build a length lookup
    lengths = {}
    for case in benchmark["test_cases"]["methods"]:
        eid = case["expected_ids"][0]
        for dn, di in engine_base.index.domains.items():
            for m in di.methods:
                if m.id == eid:
                    lengths[case["id"]] = len(m.content)

    for case in benchmark["test_cases"]["methods"]:
        mid = case["id"]
        b_rank = baseline["details"][mid]["rank"] or "MISS"
        a_rank = result_a["details"][mid]["rank"] or "MISS"
        b2_rank = result_b["details"][mid]["rank"] or "MISS"
        ab_rank = result_ab["details"][mid]["rank"] or "MISS"
        length = lengths.get(mid, 0)
        query = case["query"][:35]
        print(
            "%-12s %-6s %-6s %-6s %-6s  %-5d %s"
            % (mid, b_rank, a_rank, b2_rank, ab_rank, length, query)
        )

    # === DECISION ===
    print("\n" + "=" * 70)
    print("DECISION MATRIX")
    print("=" * 70)
    a_delta = result_a["mrr"] - baseline["mrr"]
    b_delta = result_b["mrr"] - baseline["mrr"]
    ab_delta = result_ab["mrr"] - baseline["mrr"]

    print("Baseline MRR:     %.4f" % baseline["mrr"])
    print("A delta (content): %+.4f" % a_delta)
    print("B delta (code):    %+.4f" % b_delta)
    print("A+B delta (both):  %+.4f" % ab_delta)
    print()

    threshold = 0.01
    a_wins = a_delta > threshold
    b_wins = b_delta > threshold

    if a_wins and b_wins:
        verdict = "BOTH: Both interventions improve retrieval. Do both."
    elif a_wins:
        verdict = "A WINS: Proceed with template change + backfill."
    elif b_wins:
        verdict = "B WINS: File code fix. Template change Recommended, not Required."
    else:
        verdict = "NEITHER: No material improvement. Close task or investigate other approaches."

    print("VERDICT: %s" % verdict)

    # Save
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "note": "BM25 path only (40% of hybrid). Semantic embeddings not regenerated.",
        "baseline": {"mrr": baseline["mrr"], "recall_at_10": baseline["recall_at_10"]},
        "intervention_a": {
            "mrr": result_a["mrr"],
            "recall_at_10": result_a["recall_at_10"],
            "delta_mrr": a_delta,
        },
        "intervention_b": {
            "mrr": result_b["mrr"],
            "recall_at_10": result_b["recall_at_10"],
            "delta_mrr": b_delta,
        },
        "intervention_ab": {
            "mrr": result_ab["mrr"],
            "recall_at_10": result_ab["recall_at_10"],
            "delta_mrr": ab_delta,
        },
        "verdict": verdict,
        "per_method": {},
    }
    for case in benchmark["test_cases"]["methods"]:
        mid = case["id"]
        output["per_method"][mid] = {
            "query": case["query"],
            "method_length": lengths.get(mid, 0),
            "baseline_rank": baseline["details"][mid]["rank"],
            "a_rank": result_a["details"][mid]["rank"],
            "b_rank": result_b["details"][mid]["rank"],
            "ab_rank": result_ab["details"][mid]["rank"],
            "baseline_score": baseline["details"][mid]["score"],
            "a_score": result_a["details"][mid]["score"],
            "b_score": result_b["details"][mid]["score"],
            "ab_score": result_ab["details"][mid]["score"],
        }

    out_path = Path(__file__).parent / "benchmark_ab_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print("\nResults saved to: %s" % out_path)


if __name__ == "__main__":
    main()
