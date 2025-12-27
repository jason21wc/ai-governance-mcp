"""Integration tests for the MCP server.

Per specification v4: Tests for full tool dispatch and server behavior.
Per governance Q3 (Testing Integration): End-to-end server validation.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# call_tool() Dispatcher Integration Tests
# =============================================================================


class TestCallToolDispatcher:
    """Tests for the call_tool() dispatcher routing to all tools."""

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_query_governance(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'query_governance' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("query_governance", {"query": "test query"})

                    assert len(result) == 1
                    assert "Query:" in result[0].text or "test query" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_get_principle(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'get_principle' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("get_principle", {"principle_id": "meta-C1"})

                    assert len(result) == 1
                    # Either found or not found response
                    assert "meta-C1" in result[0].text or "PRINCIPLE_NOT_FOUND" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_list_domains(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'list_domains' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("list_domains", {})

                    assert len(result) == 1
                    parsed = json.loads(result[0].text)
                    assert "total_domains" in parsed
                    assert "domains" in parsed

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_get_domain_summary(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'get_domain_summary' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("get_domain_summary", {"domain": "constitution"})

                    assert len(result) == 1
                    # Either found or not found
                    text = result[0].text
                    assert "constitution" in text or "DOMAIN_NOT_FOUND" in text

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_log_feedback(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'log_feedback' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "log_feedback",
                        {"query": "test", "principle_id": "meta-C1", "rating": 5},
                    )

                    assert len(result) == 1
                    parsed = json.loads(result[0].text)
                    assert parsed["status"] == "logged"

    @pytest.mark.asyncio
    async def test_call_tool_routes_to_get_metrics(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """call_tool should route 'get_metrics' to correct handler."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("get_metrics", {})

                    assert len(result) == 1
                    parsed = json.loads(result[0].text)
                    assert "total_queries" in parsed
                    assert "avg_retrieval_time_ms" in parsed


# =============================================================================
# End-to-End Flow Tests
# =============================================================================


class TestEndToEndFlow:
    """Tests for complete user workflows."""

    @pytest.mark.asyncio
    async def test_query_then_get_principle_flow(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """User flow: query for guidance, then get full principle."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Step 1: Query for governance guidance
                    query_result = await call_tool(
                        "query_governance", {"query": "how to handle specifications"}
                    )
                    assert len(query_result) == 1

                    # Step 2: Get a specific principle (simulated)
                    principle_result = await call_tool(
                        "get_principle", {"principle_id": "meta-C1"}
                    )
                    assert len(principle_result) == 1

    @pytest.mark.asyncio
    async def test_query_then_feedback_flow(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """User flow: query, then provide feedback."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, get_metrics

                    # Step 1: Query
                    await call_tool("query_governance", {"query": "test query"})

                    # Step 2: Provide feedback
                    feedback_result = await call_tool(
                        "log_feedback",
                        {"query": "test query", "principle_id": "meta-C1", "rating": 4},
                    )

                    parsed = json.loads(feedback_result[0].text)
                    assert parsed["status"] == "logged"

                    # Step 3: Check metrics updated
                    metrics = get_metrics()
                    assert metrics.feedback_count >= 1

    @pytest.mark.asyncio
    async def test_explore_domains_flow(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """User flow: list domains, then get domain summary."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Step 1: List available domains
                    list_result = await call_tool("list_domains", {})
                    domains_data = json.loads(list_result[0].text)

                    # Step 2: Get summary for first domain (if any)
                    if domains_data["domains"]:
                        domain_name = domains_data["domains"][0]["name"]
                        summary_result = await call_tool(
                            "get_domain_summary", {"domain": domain_name}
                        )
                        assert len(summary_result) == 1


# =============================================================================
# Metrics Accumulation Tests
# =============================================================================


class TestMetricsAccumulation:
    """Tests for metrics tracking across multiple queries."""

    @pytest.mark.asyncio
    async def test_metrics_accumulate_across_queries(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """Metrics should accumulate correctly across multiple queries."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, get_metrics

                    # Run 5 queries
                    for i in range(5):
                        await call_tool("query_governance", {"query": f"test query {i}"})

                    metrics = get_metrics()
                    assert metrics.total_queries == 5

    @pytest.mark.asyncio
    async def test_feedback_rating_average(
        self, reset_server_state, test_settings, saved_index, mock_embedder, mock_reranker
    ):
        """Average feedback rating should be calculated correctly."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("ai_governance_mcp.server.load_settings", return_value=test_settings):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, get_metrics

                    # Provide feedback with ratings: 5, 4, 3
                    ratings = [5, 4, 3]
                    for rating in ratings:
                        await call_tool(
                            "log_feedback",
                            {"query": "test", "principle_id": "meta-C1", "rating": rating},
                        )

                    metrics = get_metrics()
                    assert metrics.feedback_count == 3
                    assert metrics.avg_feedback_rating == 4.0  # (5+4+3)/3
