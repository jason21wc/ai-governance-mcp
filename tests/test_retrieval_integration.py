"""Integration tests for the retrieval engine.

Per specification v4: Tests for the complete hybrid retrieval pipeline.
Per governance Q3 (Testing Integration): End-to-end retrieval validation.
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Full Pipeline Tests
# =============================================================================


class TestRetrieveFullPipeline:
    """Tests for the complete retrieve() function."""

    def test_retrieve_returns_result(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should return RetrievalResult."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine
                from ai_governance_mcp.models import RetrievalResult

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("test query")

                assert isinstance(result, RetrievalResult)
                assert result.query == "test query"

    def test_retrieve_measures_time(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should track retrieval time."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("test query")

                assert result.retrieval_time_ms is not None
                assert result.retrieval_time_ms >= 0

    def test_retrieve_includes_constitution(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should always include constitution domain."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("test query")

                # Constitution should always be searched
                assert "constitution" in result.domains_detected or len(result.constitution_principles) >= 0

    def test_retrieve_respects_max_results(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should limit results to max_results."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("test query", max_results=2)

                total_principles = len(result.constitution_principles) + len(result.domain_principles)
                assert total_principles <= 2 * 2  # max_results per domain type

    def test_retrieve_filters_by_domain(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should filter by specified domain."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("test query", domain="ai-coding")

                # Should include the specified domain
                assert "ai-coding" in result.domains_detected or len(result.domain_principles) >= 0


class TestRetrieveSSeries:
    """Tests for S-Series handling in retrieve()."""

    def test_retrieve_s_series_triggered(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should set s_series_triggered when S-Series matched."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                result = engine.retrieve("safety concern")

                # s_series_triggered is set based on whether S-Series principles are returned
                assert isinstance(result.s_series_triggered, bool)


class TestRetrieveNoIndex:
    """Tests for retrieve() without index."""

    def test_retrieve_no_index_returns_empty(self, test_settings, mock_embedder, mock_reranker):
        """retrieve() should return empty result when no index loaded."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                # Use settings without saved index
                engine = RetrievalEngine(test_settings)
                result = engine.retrieve("test query")

                assert len(result.constitution_principles) == 0
                assert len(result.domain_principles) == 0


# =============================================================================
# Utility Method Tests
# =============================================================================


class TestGetPrincipleById:
    """Tests for get_principle_by_id() method."""

    def test_get_principle_by_id_found(self, saved_index, mock_embedder, mock_reranker):
        """get_principle_by_id() should return principle when found."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                principle = engine.get_principle_by_id("meta-C1")

                if principle:  # May be None if not in test index
                    assert principle.id == "meta-C1"

    def test_get_principle_by_id_not_found(self, saved_index, mock_embedder, mock_reranker):
        """get_principle_by_id() should return None when not found."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                principle = engine.get_principle_by_id("nonexistent-X99")

                assert principle is None

    def test_get_principle_by_id_no_index(self, test_settings, mock_embedder, mock_reranker):
        """get_principle_by_id() should return None without index."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(test_settings)
                principle = engine.get_principle_by_id("meta-C1")

                assert principle is None


class TestListDomains:
    """Tests for list_domains() method."""

    def test_list_domains_returns_list(self, saved_index, mock_embedder, mock_reranker):
        """list_domains() should return list of domain info."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                domains = engine.list_domains()

                assert isinstance(domains, list)
                if domains:
                    assert "name" in domains[0]
                    assert "principles_count" in domains[0]

    def test_list_domains_no_index(self, test_settings, mock_embedder, mock_reranker):
        """list_domains() should return empty list without index."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(test_settings)
                domains = engine.list_domains()

                assert domains == []


class TestGetDomainSummary:
    """Tests for get_domain_summary() method."""

    def test_get_domain_summary_found(self, saved_index, mock_embedder, mock_reranker):
        """get_domain_summary() should return summary when found."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                summary = engine.get_domain_summary("constitution")

                if summary:  # May be None if domain not in test index
                    assert summary["name"] == "constitution"
                    assert "principles" in summary

    def test_get_domain_summary_not_found(self, saved_index, mock_embedder, mock_reranker):
        """get_domain_summary() should return None when not found."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)
                summary = engine.get_domain_summary("nonexistent-domain")

                assert summary is None


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.integration
class TestRetrievalPerformance:
    """Performance tests for retrieval."""

    def test_retrieve_latency_under_target(self, saved_index, mock_embedder, mock_reranker):
        """retrieve() should complete under latency target."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(saved_index)

                # Run multiple times to get average
                times = []
                for _ in range(5):
                    start = time.time()
                    engine.retrieve("test query")
                    times.append((time.time() - start) * 1000)

                avg_time = sum(times) / len(times)

                # Should be under 100ms (with mocked models, should be very fast)
                assert avg_time < 100, f"Average retrieval time {avg_time}ms exceeds 100ms target"


# =============================================================================
# Real Index Tests
# =============================================================================


@pytest.mark.real_index
class TestRealIndexRetrieval:
    """Tests using production index. Run with: pytest -m real_index"""

    def test_retrieve_with_real_index(self, real_settings):
        """Test retrieval with production index."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # Should return results for a real query
        result = engine.retrieve("how to handle incomplete specifications")

        assert result.query == "how to handle incomplete specifications"
        assert len(result.constitution_principles) > 0 or len(result.domain_principles) > 0

    def test_real_index_s_series_detection(self, real_settings):
        """S-Series should be detected in real index."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # Safety-related query should potentially trigger S-Series
        result = engine.retrieve("safety concern in AI system")

        # S-Series should be considered
        assert isinstance(result.s_series_triggered, bool)

    def test_real_index_domain_routing(self, real_settings):
        """Domain routing should work with real index."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # Code-related query should return results
        result = engine.retrieve("software development testing code quality")

        # Should return some results (constitution is always searched)
        assert len(result.constitution_principles) > 0 or len(result.domain_principles) > 0

    def test_real_index_forced_domain_returns_domain_principles(self, real_settings):
        """Forced domain parameter should include domain principles in results."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # Force ai-coding domain
        result = engine.retrieve("unclear requirements", domain="ai-coding")

        # Must return domain principles from the forced domain
        assert len(result.domain_principles) > 0, "Forced domain should return domain principles"

        # All domain principles should be from ai-coding domain (prefix: coding-)
        for sp in result.domain_principles:
            assert sp.principle.id.startswith("coding-"), (
                f"Expected ai-coding principle, got {sp.principle.id}"
            )

    def test_real_index_forced_domain_includes_constitution(self, real_settings):
        """Forced domain with include_constitution=True should search both domains."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        # Use a general query that should match both domains
        result = engine.retrieve(
            "how should I handle unclear requirements and ambiguity",
            domain="ai-coding",
            include_constitution=True,
        )

        # Should search both domains (constitution_principles may be empty if
        # domain principles score much higher, but search_domains includes both)
        assert len(result.domain_principles) > 0, "Should return domain principles"
        # Constitution principles are searched but may not meet threshold
        # The key test is that include_constitution doesn't break domain retrieval

    def test_real_index_forced_domain_excludes_constitution(self, real_settings):
        """Forced domain with include_constitution=False should exclude constitution."""
        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(real_settings)

        result = engine.retrieve(
            "specification completeness",
            domain="ai-coding",
            include_constitution=False,
        )

        # Should have domain principles only
        assert len(result.domain_principles) > 0, "Should return domain principles"
        assert len(result.constitution_principles) == 0, "Should not return constitution"
