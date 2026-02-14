#!/usr/bin/env python3
"""Evaluate embedding models for Context Engine retrieval quality.

Runs benchmark queries against multiple embedding models and reports
MRR, Recall@5, Recall@10, load time, and model size.

Usage:
    python scripts/evaluate_embeddings.py [--models MODEL1 MODEL2 ...]
    python scripts/evaluate_embeddings.py --sweep-weights

Examples:
    # Compare default candidates
    python scripts/evaluate_embeddings.py

    # Compare specific models
    python scripts/evaluate_embeddings.py --models BAAI/bge-small-en-v1.5 BAAI/bge-base-en-v1.5

    # Grid search semantic_weight with current model
    python scripts/evaluate_embeddings.py --sweep-weights
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DEFAULT_CANDIDATES = [
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/all-mpnet-base-v2",
]

WEIGHT_SWEEP_RANGE = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]


def load_benchmark():
    benchmark_path = (
        Path(__file__).parent.parent
        / "tests"
        / "benchmarks"
        / "context_engine_quality.json"
    )
    with open(benchmark_path) as f:
        return json.load(f)


def calculate_mrr(ranks):
    if not ranks:
        return 0.0
    rr = []
    for r in ranks:
        rr.append(1.0 / r if r is not None and r > 0 else 0.0)
    return sum(rr) / len(rr)


def calculate_recall_at_k(found_counts, k=10):
    if not found_counts:
        return 0.0
    total_found = sum(f for f, _ in found_counts)
    total_expected = sum(e for _, e in found_counts)
    return total_found / total_expected if total_expected > 0 else 0.0


def evaluate_model(model_name, project_root, benchmark, semantic_weight=0.6):
    """Evaluate a single model against benchmark queries."""
    from ai_governance_mcp.context_engine.project_manager import ProjectManager
    from ai_governance_mcp.context_engine.storage.filesystem import FilesystemStorage

    # Use temporary storage to avoid polluting real index
    tmp_dir = tempfile.mkdtemp(prefix="ce_eval_")
    try:
        storage = FilesystemStorage(base_path=Path(tmp_dir))

        # Auto-detect dimensions after model loads
        load_start = time.time()
        pm = ProjectManager(
            storage=storage,
            embedding_model=model_name,
            embedding_dimensions=384,  # Will be corrected below
            semantic_weight=semantic_weight,
        )

        # Detect actual dimensions from loaded model
        model = pm._indexer.embedding_model
        actual_dims = model.get_sentence_embedding_dimension()
        pm.embedding_dimensions = actual_dims
        pm._indexer.embedding_dimensions = actual_dims

        load_time = time.time() - load_start

        # Index project
        index_start = time.time()
        pm.get_or_create_index(project_root)
        index_time = time.time() - index_start

        # Run benchmark queries
        ranks = []
        recall5_counts = []
        recall10_counts = []

        for case in benchmark["test_cases"]:
            result = pm.query_project(
                query=case["query"],
                project_path=project_root,
                max_results=10,
            )
            result_files = [r.chunk.source_path for r in result.results]

            # MRR
            rank = None
            for ef in case["expected_files"]:
                if ef in result_files:
                    r = result_files.index(ef) + 1
                    if rank is None or r < rank:
                        rank = r
            ranks.append(rank)

            # Recall
            found_5 = sum(1 for ef in case["expected_files"] if ef in result_files[:5])
            found_10 = sum(1 for ef in case["expected_files"] if ef in result_files)
            recall5_counts.append((found_5, len(case["expected_files"])))
            recall10_counts.append((found_10, len(case["expected_files"])))

        mrr = calculate_mrr(ranks)
        recall_5 = calculate_recall_at_k(recall5_counts, k=5)
        recall_10 = calculate_recall_at_k(recall10_counts, k=10)

        return {
            "model": model_name,
            "dimensions": actual_dims,
            "load_time_s": round(load_time, 2),
            "index_time_s": round(index_time, 2),
            "mrr": round(mrr, 3),
            "recall_at_5": round(recall_5, 3),
            "recall_at_10": round(recall_10, 3),
            "semantic_weight": semantic_weight,
            "individual_ranks": ranks,
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def print_comparison_table(results):
    """Print a formatted comparison table."""
    print("\n" + "=" * 90)
    print(f"{'Model':<40} {'Dims':>5} {'Load(s)':>8} {'MRR':>6} {'R@5':>6} {'R@10':>6}")
    print("-" * 90)
    for r in results:
        print(
            f"{r['model']:<40} {r['dimensions']:>5} "
            f"{r['load_time_s']:>8.2f} {r['mrr']:>6.3f} "
            f"{r['recall_at_5']:>6.3f} {r['recall_at_10']:>6.3f}"
        )
    print("=" * 90)


def print_weight_sweep_table(results):
    """Print weight sweep results."""
    print("\n" + "=" * 70)
    print(f"{'Weight':>8} {'MRR':>8} {'R@5':>8} {'R@10':>8}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['semantic_weight']:>8.2f} {r['mrr']:>8.3f} "
            f"{r['recall_at_5']:>8.3f} {r['recall_at_10']:>8.3f}"
        )
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Evaluate embedding models")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_CANDIDATES,
        help="Models to evaluate",
    )
    parser.add_argument(
        "--sweep-weights",
        action="store_true",
        help="Grid search semantic_weight with current model",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    benchmark = load_benchmark()

    print(f"Project root: {project_root}")
    print(f"Benchmark queries: {len(benchmark['test_cases'])}")

    if args.sweep_weights:
        print("\nSweeping semantic_weight values...")
        results = []
        for weight in WEIGHT_SWEEP_RANGE:
            print(f"  Testing weight={weight}...")
            r = evaluate_model(
                "BAAI/bge-small-en-v1.5",
                project_root,
                benchmark,
                semantic_weight=weight,
            )
            results.append(r)
        print_weight_sweep_table(results)
    else:
        print(f"\nEvaluating {len(args.models)} models...")
        results = []
        for model in args.models:
            print(f"\n  Evaluating: {model}")
            r = evaluate_model(model, project_root, benchmark)
            results.append(r)
            print(
                f"    MRR={r['mrr']:.3f}, R@5={r['recall_at_5']:.3f}, R@10={r['recall_at_10']:.3f}"
            )

        print_comparison_table(results)

        # Save results
        output_path = project_root / "tests" / "benchmarks" / "model_comparison.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
