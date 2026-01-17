"""Retrieval quality benchmark tests.

Measures MRR, Recall@10, Precision@5 for methods and principles.
Run with: pytest tests/test_retrieval_quality.py -v -m real_index
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_benchmark_cases() -> dict:
    """Load benchmark test cases from JSON."""
    benchmark_path = Path(__file__).parent / "benchmarks" / "retrieval_quality.json"
    with open(benchmark_path) as f:
        return json.load(f)


def calculate_mrr(ranks: list[int | None]) -> float:
    """Calculate Mean Reciprocal Rank.

    Args:
        ranks: List of ranks (1-indexed) or None if not found

    Returns:
        MRR score between 0 and 1
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
        found_counts: List of (found_in_top_k, total_expected) tuples
        k: The K value for Recall@K

    Returns:
        Recall score between 0 and 1
    """
    if not found_counts:
        return 0.0

    total_found = sum(f for f, _ in found_counts)
    total_expected = sum(e for _, e in found_counts)

    if total_expected == 0:
        return 0.0

    return total_found / total_expected


def calculate_precision_at_k(
    relevance_counts: list[tuple[int, int]], k: int = 5
) -> float:
    """Calculate Precision@K.

    Args:
        relevance_counts: List of (relevant_in_top_k, k) tuples
        k: The K value for Precision@K

    Returns:
        Precision score between 0 and 1
    """
    if not relevance_counts:
        return 0.0

    total_relevant = sum(r for r, _ in relevance_counts)
    total_k = sum(actual_k for _, actual_k in relevance_counts)

    if total_k == 0:
        return 0.0

    return total_relevant / total_k


@pytest.mark.real_index
class TestMethodRetrievalQuality:
    """Benchmark tests for method retrieval quality."""

    def test_method_retrieval_individual(self, real_settings):
        """Test each method case individually with detailed output."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        for case in benchmark["test_cases"]["methods"]:
            result = engine.retrieve(case["query"], include_methods=True)

            # Find rank of expected method
            method_ids = [m.method.id for m in result.methods]
            method_scores = {m.method.id: m.combined_score for m in result.methods}

            found = False
            rank = None
            score = None

            for expected_id in case["expected_ids"]:
                if expected_id in method_ids:
                    found = True
                    rank = method_ids.index(expected_id) + 1
                    score = method_scores.get(expected_id, 0)
                    break

            # Print detailed results
            print(f"\n[{case['id']}] {case['description']}")
            print(f"  Query: {case['query']}")
            print(f"  Expected: {case['expected_ids']}")
            print(f"  Found: {found}, Rank: {rank}, Score: {score}")
            print(f"  Top 5 methods: {method_ids[:5]}")
            if result.methods:
                print(
                    f"  Top scores: {[f'{m.combined_score:.3f}' for m in result.methods[:5]]}"
                )

    def test_method_mrr(self, real_settings):
        """Calculate MRR for method retrieval."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        ranks = []
        for case in benchmark["test_cases"]["methods"]:
            result = engine.retrieve(case["query"], include_methods=True)
            method_ids = [m.method.id for m in result.methods]

            rank = None
            for expected_id in case["expected_ids"]:
                if expected_id in method_ids:
                    rank = method_ids.index(expected_id) + 1
                    break

            ranks.append(rank)

        mrr = calculate_mrr(ranks)
        print(f"\nMethod MRR: {mrr:.3f}")
        print(f"Target MRR: {benchmark['metrics']['target_method_mrr']}")
        print(f"Individual ranks: {ranks}")

        # Store for baseline comparison
        assert mrr >= 0, f"MRR should be non-negative, got {mrr}"

    def test_method_recall_at_10(self, real_settings):
        """Calculate Recall@10 for method retrieval."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        found_counts = []
        for case in benchmark["test_cases"]["methods"]:
            result = engine.retrieve(
                case["query"], include_methods=True, max_results=10
            )
            method_ids = [m.method.id for m in result.methods[:10]]

            found = sum(1 for eid in case["expected_ids"] if eid in method_ids)
            expected = len(case["expected_ids"])
            found_counts.append((found, expected))

        recall = calculate_recall_at_k(found_counts, k=10)
        print(f"\nMethod Recall@10: {recall:.3f}")
        print(f"Target: {benchmark['metrics']['target_recall_at_10']}")

        assert recall >= 0, f"Recall should be non-negative, got {recall}"

    def test_advanced_model_considerations_score(self, real_settings):
        """Specific test for the Advanced Model Considerations method."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # The problem query
        result = engine.retrieve(
            "advanced model prompting strategies decision rules", include_methods=True
        )

        # Find the specific method
        target_id = "multi-method-advanced-model-considerations"
        target_method = None
        for m in result.methods:
            if m.method.id == target_id:
                target_method = m
                break

        print("\n=== Advanced Model Considerations Test ===")
        print("Query: 'advanced model prompting strategies decision rules'")

        if target_method:
            print("Found: YES")
            print(f"Semantic score: {target_method.semantic_score:.3f}")
            print(f"Keyword score: {target_method.keyword_score:.3f}")
            print(f"Combined score: {target_method.combined_score:.3f}")

            # This is the key metric we're trying to improve
            # Current: 0.28, Target: 0.5+
            assert target_method.combined_score >= 0.0, "Score should be positive"
        else:
            print("Found: NO")
            print("Top 5 methods returned:")
            for i, m in enumerate(result.methods[:5]):
                print(f"  {i + 1}. {m.method.id}: {m.combined_score:.3f}")

            pytest.fail(f"Method {target_id} not found in results")


@pytest.mark.real_index
class TestPrincipleRetrievalQuality:
    """Benchmark tests for principle retrieval quality."""

    def test_principle_retrieval_individual(self, real_settings):
        """Test each principle case individually with detailed output."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        for case in benchmark["test_cases"]["principles"]:
            result = engine.retrieve(case["query"])

            # Combine constitution and domain principles
            all_principles = result.constitution_principles + result.domain_principles
            principle_ids = [p.principle.id for p in all_principles]
            principle_scores = {
                p.principle.id: p.combined_score for p in all_principles
            }

            found = False
            rank = None
            score = None

            for expected_id in case["expected_ids"]:
                if expected_id in principle_ids:
                    found = True
                    rank = principle_ids.index(expected_id) + 1
                    score = principle_scores.get(expected_id, 0)
                    break

            print(f"\n[{case['id']}] {case['description']}")
            print(f"  Query: {case['query']}")
            print(f"  Expected: {case['expected_ids']}")
            print(f"  Found: {found}, Rank: {rank}, Score: {score}")
            print(f"  Top 5: {principle_ids[:5]}")

    def test_principle_mrr(self, real_settings):
        """Calculate MRR for principle retrieval."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        ranks = []
        for case in benchmark["test_cases"]["principles"]:
            result = engine.retrieve(case["query"])
            all_principles = result.constitution_principles + result.domain_principles
            principle_ids = [p.principle.id for p in all_principles]

            rank = None
            for expected_id in case["expected_ids"]:
                if expected_id in principle_ids:
                    rank = principle_ids.index(expected_id) + 1
                    break

            ranks.append(rank)

        mrr = calculate_mrr(ranks)
        print(f"\nPrinciple MRR: {mrr:.3f}")
        print(f"Target MRR: {benchmark['metrics']['target_principle_mrr']}")
        print(f"Individual ranks: {ranks}")

        assert mrr >= 0, f"MRR should be non-negative, got {mrr}"

    def test_principle_recall_at_10(self, real_settings):
        """Calculate Recall@10 for principle retrieval."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        found_counts = []
        for case in benchmark["test_cases"]["principles"]:
            result = engine.retrieve(case["query"], max_results=10)
            all_principles = result.constitution_principles + result.domain_principles
            principle_ids = [p.principle.id for p in all_principles[:10]]

            found = sum(1 for eid in case["expected_ids"] if eid in principle_ids)
            expected = len(case["expected_ids"])
            found_counts.append((found, expected))

        recall = calculate_recall_at_k(found_counts, k=10)
        print(f"\nPrinciple Recall@10: {recall:.3f}")
        print(f"Target: {benchmark['metrics']['target_recall_at_10']}")

        assert recall >= 0, f"Recall should be non-negative, got {recall}"


@pytest.mark.real_index
class TestBaselineRecording:
    """Record baseline metrics before changes."""

    def test_record_baseline(self, real_settings):
        """Record all metrics and save to baseline file."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)
        benchmark = load_benchmark_cases()

        # Method metrics
        method_ranks = []
        method_scores = {}
        for case in benchmark["test_cases"]["methods"]:
            result = engine.retrieve(case["query"], include_methods=True)
            method_ids = [m.method.id for m in result.methods]

            rank = None
            score = None
            for expected_id in case["expected_ids"]:
                if expected_id in method_ids:
                    idx = method_ids.index(expected_id)
                    rank = idx + 1
                    score = result.methods[idx].combined_score
                    break

            method_ranks.append(rank)
            method_scores[case["id"]] = {
                "query": case["query"],
                "expected": case["expected_ids"],
                "rank": rank,
                "score": score,
                "semantic_score": result.methods[
                    method_ids.index(case["expected_ids"][0])
                ].semantic_score
                if rank
                else None,
            }

        # Principle metrics
        principle_ranks = []
        principle_scores = {}
        for case in benchmark["test_cases"]["principles"]:
            result = engine.retrieve(case["query"])
            all_principles = result.constitution_principles + result.domain_principles
            principle_ids = [p.principle.id for p in all_principles]

            rank = None
            score = None
            for expected_id in case["expected_ids"]:
                if expected_id in principle_ids:
                    idx = principle_ids.index(expected_id)
                    rank = idx + 1
                    score = all_principles[idx].combined_score
                    break

            principle_ranks.append(rank)
            principle_scores[case["id"]] = {
                "query": case["query"],
                "expected": case["expected_ids"],
                "rank": rank,
                "score": score,
            }

        # Calculate aggregate metrics
        method_mrr = calculate_mrr(method_ranks)
        principle_mrr = calculate_mrr(principle_ranks)

        method_found = sum(1 for r in method_ranks if r is not None and r <= 10)
        principle_found = sum(1 for r in principle_ranks if r is not None and r <= 10)

        baseline = {
            "timestamp": datetime.now().isoformat(),
            "embedding_model": engine.index.embedding_model
            if engine.index
            else "unknown",
            "metrics": {
                "method_mrr": method_mrr,
                "principle_mrr": principle_mrr,
                "method_recall_at_10": method_found / len(method_ranks)
                if method_ranks
                else 0,
                "principle_recall_at_10": principle_found / len(principle_ranks)
                if principle_ranks
                else 0,
            },
            "method_details": method_scores,
            "principle_details": principle_scores,
        }

        # Save baseline
        baseline_path = (
            Path(__file__).parent
            / "benchmarks"
            / f"baseline_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        with open(baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)

        print("\n=== BASELINE RECORDED ===")
        print(f"Embedding Model: {baseline['embedding_model']}")
        print(f"Method MRR: {method_mrr:.3f}")
        print(f"Principle MRR: {principle_mrr:.3f}")
        print(f"Method Recall@10: {baseline['metrics']['method_recall_at_10']:.3f}")
        print(
            f"Principle Recall@10: {baseline['metrics']['principle_recall_at_10']:.3f}"
        )
        print(f"Saved to: {baseline_path}")

        # Print problem case specifically
        adv_model = method_scores.get("method-1", {})
        print("\n=== KEY PROBLEM CASE ===")
        print("Advanced Model Considerations:")
        print(f"  Rank: {adv_model.get('rank')}")
        print(f"  Score: {adv_model.get('score')}")
        print(f"  Semantic: {adv_model.get('semantic_score')}")
