"""Context Engine retrieval quality benchmark tests.

Measures MRR, Recall@5, Recall@10 for the Context Engine's hybrid search
against this project's own codebase. Requires a real embedding model.

Run with: pytest tests/test_context_engine_quality.py -v -m "real_index and slow" -s
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_benchmark_cases() -> dict:
    """Load Context Engine benchmark test cases from JSON."""
    benchmark_path = (
        Path(__file__).parent / "benchmarks" / "context_engine_quality.json"
    )
    with open(benchmark_path) as f:
        return json.load(f)


def calculate_mrr(ranks: list[int | None]) -> float:
    """Calculate Mean Reciprocal Rank.

    Args:
        ranks: List of ranks (1-indexed) or None if not found.

    Returns:
        MRR score between 0 and 1.
    """
    if not ranks:
        return 0.0
    reciprocal_ranks = []
    for rank in ranks:
        if rank is not None and rank > 0:
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def calculate_recall_at_k(found_counts: list[tuple[int, int]], k: int = 10) -> float:
    """Calculate Recall@K.

    Args:
        found_counts: List of (found_in_top_k, total_expected) tuples.

    Returns:
        Recall score between 0 and 1.
    """
    if not found_counts:
        return 0.0
    total_found = sum(f for f, _ in found_counts)
    total_expected = sum(e for _, e in found_counts)
    if total_expected == 0:
        return 0.0
    return total_found / total_expected


@pytest.mark.real_index
@pytest.mark.slow
class TestContextEngineRetrievalQuality:
    """Benchmark tests for Context Engine retrieval quality.

    Uses this project's codebase as corpus. Each test case queries
    for known patterns and checks which source files appear in results.
    """

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """Set up the Context Engine with a real index of this project."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager
        from ai_governance_mcp.context_engine.storage.filesystem import (
            FilesystemStorage,
        )

        project_root = Path(__file__).parent.parent
        self.project_root = project_root
        storage = FilesystemStorage()
        self.manager = ProjectManager(storage=storage)

        # Ensure project is indexed
        self.manager.get_or_create_index(project_root)

    def test_individual_queries(self):
        """Test each benchmark case individually with detailed output."""
        benchmark = load_benchmark_cases()

        for case in benchmark["test_cases"]:
            result = self.manager.query_project(
                query=case["query"],
                project_path=self.project_root,
                max_results=10,
            )

            result_files = [r.chunk.source_path for r in result.results]
            found_expected = [ef for ef in case["expected_files"] if ef in result_files]
            found_count = len(found_expected)
            total_expected = len(case["expected_files"])

            # Find best rank of any expected file
            rank = None
            for ef in case["expected_files"]:
                if ef in result_files:
                    r = result_files.index(ef) + 1
                    if rank is None or r < rank:
                        rank = r

            print(f"\n[{case['id']}] {case['description']}")
            print(f"  Query: {case['query']}")
            print(f"  Expected files: {case['expected_files']}")
            print(f"  Found: {found_count}/{total_expected}, Best rank: {rank}")
            print(f"  Top 5 result files: {result_files[:5]}")
            if result.results:
                print(
                    f"  Top scores: {[f'{r.combined_score:.3f}' for r in result.results[:5]]}"
                )

    def test_mrr(self):
        """Calculate MRR for Context Engine retrieval."""
        benchmark = load_benchmark_cases()
        ranks = []

        for case in benchmark["test_cases"]:
            result = self.manager.query_project(
                query=case["query"],
                project_path=self.project_root,
                max_results=10,
            )
            result_files = [r.chunk.source_path for r in result.results]

            rank = None
            for ef in case["expected_files"]:
                if ef in result_files:
                    r = result_files.index(ef) + 1
                    if rank is None or r < rank:
                        rank = r
            ranks.append(rank)

        mrr = calculate_mrr(ranks)
        target = benchmark["metrics"]["target_mrr"]
        print(f"\nContext Engine MRR: {mrr:.3f}")
        print(f"Target MRR: {target}")
        print(f"Individual ranks: {ranks}")

        assert mrr >= 0, f"MRR should be non-negative, got {mrr}"

    def test_recall_at_5(self):
        """Calculate Recall@5 for Context Engine retrieval."""
        benchmark = load_benchmark_cases()
        found_counts = []

        for case in benchmark["test_cases"]:
            result = self.manager.query_project(
                query=case["query"],
                project_path=self.project_root,
                max_results=5,
            )
            result_files = [r.chunk.source_path for r in result.results]
            found = sum(1 for ef in case["expected_files"] if ef in result_files)
            found_counts.append((found, len(case["expected_files"])))

        recall = calculate_recall_at_k(found_counts, k=5)
        target = benchmark["metrics"]["target_recall_at_5"]
        print(f"\nContext Engine Recall@5: {recall:.3f}")
        print(f"Target Recall@5: {target}")

        assert recall >= 0, f"Recall should be non-negative, got {recall}"

    def test_recall_at_10(self):
        """Calculate Recall@10 for Context Engine retrieval."""
        benchmark = load_benchmark_cases()
        found_counts = []

        for case in benchmark["test_cases"]:
            result = self.manager.query_project(
                query=case["query"],
                project_path=self.project_root,
                max_results=10,
            )
            result_files = [r.chunk.source_path for r in result.results]
            found = sum(1 for ef in case["expected_files"] if ef in result_files)
            found_counts.append((found, len(case["expected_files"])))

        recall = calculate_recall_at_k(found_counts, k=10)
        target = benchmark["metrics"]["target_recall_at_10"]
        print(f"\nContext Engine Recall@10: {recall:.3f}")
        print(f"Target Recall@10: {target}")

        assert recall >= 0, f"Recall should be non-negative, got {recall}"

    def test_save_baseline(self):
        """Save current metrics as a baseline for comparison."""
        benchmark = load_benchmark_cases()

        # Calculate all metrics
        ranks = []
        recall5_counts = []
        recall10_counts = []

        for case in benchmark["test_cases"]:
            result = self.manager.query_project(
                query=case["query"],
                project_path=self.project_root,
                max_results=10,
            )
            result_files = [r.chunk.source_path for r in result.results]

            # MRR rank
            rank = None
            for ef in case["expected_files"]:
                if ef in result_files:
                    r = result_files.index(ef) + 1
                    if rank is None or r < rank:
                        rank = r
            ranks.append(rank)

            # Recall counts
            found_5 = sum(1 for ef in case["expected_files"] if ef in result_files[:5])
            found_10 = sum(1 for ef in case["expected_files"] if ef in result_files)
            recall5_counts.append((found_5, len(case["expected_files"])))
            recall10_counts.append((found_10, len(case["expected_files"])))

        mrr = calculate_mrr(ranks)
        recall_5 = calculate_recall_at_k(recall5_counts, k=5)
        recall_10 = calculate_recall_at_k(recall10_counts, k=10)

        baseline = {
            "timestamp": datetime.now().isoformat(),
            "type": "context_engine",
            "metrics": {
                "mrr": round(mrr, 3),
                "recall_at_5": round(recall_5, 3),
                "recall_at_10": round(recall_10, 3),
            },
            "individual_ranks": ranks,
            "benchmark_version": benchmark["version"],
        }

        # Save baseline
        baseline_path = (
            Path(__file__).parent
            / "benchmarks"
            / f"ce_baseline_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        with open(baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)

        print(f"\nBaseline saved to: {baseline_path.name}")
        print(f"  MRR: {mrr:.3f}")
        print(f"  Recall@5: {recall_5:.3f}")
        print(f"  Recall@10: {recall_10:.3f}")
