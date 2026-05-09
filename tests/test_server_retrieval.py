"""Tests for retrieval tool handlers.

Split from test_server.py during Phase 3 server decomposition.
Covers: query_governance (T13), get_principle (T14), list_domains (T15),
get_domain_summary (T16), log_feedback (T17), get_metrics (T18),
_format_retrieval_result.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from helpers import extract_json_from_response


# =============================================================================
# Tool Handler Tests - query_governance
# =============================================================================


class TestHandleQueryGovernance:
    """Tests for _handle_query_governance tool handler."""

    @pytest.mark.asyncio
    async def test_handle_query_governance_success(
        self, reset_server_state, sample_retrieval_result
    ):
        """query_governance should return formatted results."""
        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        result = await _handle_query_governance(mock_engine, {"query": "test query"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "test query" in result[0].text
        mock_engine.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_query_governance_empty_query(self, reset_server_state):
        """query_governance should return error for empty query."""
        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()
        result = await _handle_query_governance(mock_engine, {"query": ""})

        assert len(result) == 1
        assert "Error: query is required" in result[0].text
        mock_engine.retrieve.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_query_governance_updates_metrics(
        self, reset_server_state, sample_retrieval_result, test_settings
    ):
        """query_governance should update metrics after query."""
        import ai_governance_mcp.server as server_module

        server_module._state._settings = test_settings
        server_module._state._metrics = None

        from ai_governance_mcp.server import _handle_query_governance, get_metrics

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        await _handle_query_governance(mock_engine, {"query": "test"})

        metrics = get_metrics()
        assert metrics.total_queries == 1
        assert metrics.avg_retrieval_time_ms > 0

    @pytest.mark.asyncio
    async def test_handle_query_governance_s_series_triggered(
        self, reset_server_state, sample_retrieval_result, test_settings
    ):
        """query_governance should increment s_series_trigger_count when triggered."""
        import ai_governance_mcp.server as server_module

        server_module._state._settings = test_settings
        server_module._state._metrics = None

        from ai_governance_mcp.server import _handle_query_governance, get_metrics

        sample_retrieval_result.s_series_triggered = True

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        await _handle_query_governance(mock_engine, {"query": "safety concern"})

        metrics = get_metrics()
        assert metrics.s_series_trigger_count == 1

    @pytest.mark.asyncio
    async def test_handle_query_governance_logs_query(
        self, reset_server_state, sample_retrieval_result, test_settings
    ):
        """query_governance should log query to file."""
        import ai_governance_mcp.server as server_module

        server_module._state._settings = test_settings
        server_module._state._metrics = None

        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        await _handle_query_governance(mock_engine, {"query": "logged query"})

        log_file = test_settings.logs_path / "queries.jsonl"
        assert log_file.exists()
        content = log_file.read_text()
        assert "logged query" in content
        import json

        log_entry = json.loads(content.strip().split("\n")[-1])
        assert "references_returned" in log_entry
        assert "ref-ai-coding-test-pattern" in log_entry["references_returned"]

    @pytest.mark.asyncio
    async def test_handle_query_governance_with_domain_filter(
        self, reset_server_state, sample_retrieval_result
    ):
        """query_governance should pass domain parameter to retrieve."""
        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        await _handle_query_governance(
            mock_engine,
            {"query": "test", "domain": "ai-coding", "include_methods": True},
        )

        mock_engine.retrieve.assert_called_once_with(
            query="test",
            domain="ai-coding",
            include_constitution=True,
            include_methods=True,
            max_results=None,
        )


# =============================================================================
# Tool Handler Tests - get_principle
# =============================================================================


class TestHandleGetPrinciple:
    """Tests for _handle_get_principle tool handler."""

    @pytest.mark.asyncio
    async def test_handle_get_principle_found(
        self, reset_server_state, sample_principle
    ):
        """get_principle should return principle JSON when found."""
        from ai_governance_mcp.server import _handle_get_principle

        mock_engine = Mock()
        mock_engine.get_principle_by_id.return_value = sample_principle

        result = await _handle_get_principle(mock_engine, {"principle_id": "meta-C1"})

        assert len(result) == 1
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["id"] == "meta-C1"
        assert parsed["title"] == "Test Principle"
        assert "keywords" in parsed

    @pytest.mark.asyncio
    async def test_handle_get_principle_finds_method(self, reset_server_state):
        """get_principle should return method JSON when method ID is provided."""
        from ai_governance_mcp.models import Method
        from ai_governance_mcp.server import _handle_get_principle

        mock_method = Method(
            id="meta-method-test-method",
            domain="constitution",
            title="Test Method",
            content="This is test method content.",
            line_range=(1, 10),
            keywords=["test", "method"],
        )

        mock_engine = Mock()
        mock_engine.get_principle_by_id.return_value = None
        mock_engine.get_method_by_id.return_value = mock_method

        result = await _handle_get_principle(
            mock_engine, {"principle_id": "meta-method-test-method"}
        )

        assert len(result) == 1
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["id"] == "meta-method-test-method"
        assert parsed["type"] == "method"
        assert parsed["title"] == "Test Method"
        assert "test" in parsed["keywords"]

    @pytest.mark.asyncio
    async def test_handle_get_principle_not_found(self, reset_server_state):
        """get_principle should return ErrorResponse when not found."""
        from ai_governance_mcp.server import _handle_get_principle

        mock_engine = Mock()
        mock_engine.get_principle_by_id.return_value = None
        mock_engine.get_method_by_id.return_value = None

        result = await _handle_get_principle(mock_engine, {"principle_id": "meta-X99"})

        assert len(result) == 1
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "PRINCIPLE_NOT_FOUND"
        assert "meta-X99" in parsed["message"]

    @pytest.mark.asyncio
    async def test_handle_get_principle_empty_id(self, reset_server_state):
        """get_principle should return error for empty ID."""
        from ai_governance_mcp.server import _handle_get_principle

        mock_engine = Mock()
        result = await _handle_get_principle(mock_engine, {"principle_id": ""})

        assert len(result) == 1
        assert "Error: principle_id is required" in result[0].text


# =============================================================================
# Tool Handler Tests - list_domains
# =============================================================================


class TestHandleListDomains:
    """Tests for _handle_list_domains tool handler."""

    @pytest.mark.asyncio
    async def test_handle_list_domains_success(self, reset_server_state):
        """list_domains should return domain list."""
        from ai_governance_mcp.server import _handle_list_domains

        mock_domains = [
            {
                "name": "constitution",
                "display_name": "Constitution",
                "principles_count": 42,
            },
            {"name": "ai-coding", "display_name": "AI Coding", "principles_count": 12},
        ]

        mock_engine = Mock()
        mock_engine.list_domains.return_value = mock_domains

        result = await _handle_list_domains(mock_engine, {})

        assert len(result) == 1
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["total_domains"] == 2
        assert len(parsed["domains"]) == 2
        assert parsed["domains"][0]["name"] == "constitution"

    @pytest.mark.asyncio
    async def test_handle_list_domains_empty(self, reset_server_state):
        """list_domains should handle empty domain list."""
        from ai_governance_mcp.server import _handle_list_domains

        mock_engine = Mock()
        mock_engine.list_domains.return_value = []

        result = await _handle_list_domains(mock_engine, {})

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["total_domains"] == 0
        assert parsed["domains"] == []


# =============================================================================
# Tool Handler Tests - get_domain_summary
# =============================================================================


class TestHandleGetDomainSummary:
    """Tests for _handle_get_domain_summary tool handler."""

    @pytest.mark.asyncio
    async def test_handle_get_domain_summary_found(self, reset_server_state):
        """get_domain_summary should return domain details."""
        from ai_governance_mcp.server import _handle_get_domain_summary

        mock_summary = {
            "name": "ai-coding",
            "display_name": "AI Coding",
            "description": "Software development",
            "principles": [{"id": "coding-C1", "title": "Code Quality"}],
            "methods": [{"id": "coding-M1", "title": "Cold Start"}],
        }

        mock_engine = Mock()
        mock_engine.get_domain_summary.return_value = mock_summary

        result = await _handle_get_domain_summary(mock_engine, {"domain": "ai-coding"})

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["name"] == "ai-coding"
        assert len(parsed["principles"]) == 1

    @pytest.mark.asyncio
    async def test_handle_get_domain_summary_not_found(self, reset_server_state):
        """get_domain_summary should return error for invalid domain."""
        from ai_governance_mcp.server import _handle_get_domain_summary

        mock_engine = Mock()

        result = await _handle_get_domain_summary(mock_engine, {"domain": "invalid"})

        assert "Error: Invalid domain" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_get_domain_summary_empty_domain(self, reset_server_state):
        """get_domain_summary should return error for empty domain."""
        from ai_governance_mcp.server import _handle_get_domain_summary

        mock_engine = Mock()
        result = await _handle_get_domain_summary(mock_engine, {"domain": ""})

        assert "Error: domain is required" in result[0].text


# =============================================================================
# Tool Handler Tests - log_feedback
# =============================================================================


class TestHandleLogFeedback:
    """Tests for _handle_log_feedback tool handler."""

    @pytest.mark.asyncio
    async def test_handle_log_feedback_success(self, reset_server_state, test_settings):
        """log_feedback should log and update metrics."""
        import ai_governance_mcp.server as server_module

        server_module._state._settings = test_settings
        server_module._state._metrics = None

        from ai_governance_mcp.server import _handle_log_feedback, get_metrics

        result = await _handle_log_feedback(
            {
                "query": "test",
                "principle_id": "meta-C1",
                "rating": 5,
                "comment": "Very helpful",
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert "Thank you" in parsed["message"]

        metrics = get_metrics()
        assert metrics.feedback_count == 1
        assert metrics.avg_feedback_rating == 5.0

    @pytest.mark.asyncio
    async def test_handle_log_feedback_missing_fields(self, reset_server_state):
        """log_feedback should return error for missing required fields."""
        from ai_governance_mcp.server import _handle_log_feedback

        result = await _handle_log_feedback({"query": "test"})

        assert "Error:" in result[0].text
        assert "required" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_log_feedback_invalid_rating_low(self, reset_server_state):
        """log_feedback should reject rating below 1.

        Covers: FM-FEEDBACK-RATING-BOUNDS
        """
        from ai_governance_mcp.server import _handle_log_feedback

        result = await _handle_log_feedback(
            {
                "query": "test",
                "principle_id": "meta-C1",
                "rating": -1,
            }
        )

        assert "Error: rating must be 1-5" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_log_feedback_invalid_rating_high(self, reset_server_state):
        """log_feedback should reject rating above 5.

        Covers: FM-FEEDBACK-RATING-BOUNDS
        """
        from ai_governance_mcp.server import _handle_log_feedback

        result = await _handle_log_feedback(
            {
                "query": "test",
                "principle_id": "meta-C1",
                "rating": 6,
            }
        )

        assert "Error: rating must be 1-5" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_log_feedback_updates_avg_rating(
        self, reset_server_state, test_settings
    ):
        """log_feedback should calculate rolling average rating."""
        import ai_governance_mcp.server as server_module

        server_module._state._settings = test_settings
        server_module._state._metrics = None

        from ai_governance_mcp.server import _handle_log_feedback, get_metrics

        await _handle_log_feedback(
            {"query": "q1", "principle_id": "meta-C1", "rating": 4}
        )
        await _handle_log_feedback(
            {"query": "q2", "principle_id": "meta-C1", "rating": 2}
        )

        metrics = get_metrics()
        assert metrics.feedback_count == 2
        assert metrics.avg_feedback_rating == 3.0  # (4 + 2) / 2


# =============================================================================
# Tool Handler Tests - get_metrics
# =============================================================================


class TestHandleGetMetrics:
    """Tests for _handle_get_metrics tool handler."""

    @pytest.mark.asyncio
    async def test_handle_get_metrics_initial(self, reset_server_state):
        """get_metrics should return initial metrics."""
        from ai_governance_mcp.server import _handle_get_metrics

        result = await _handle_get_metrics({})

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["total_queries"] == 0
        assert parsed["avg_retrieval_time_ms"] == 0
        assert parsed["s_series_trigger_count"] == 0
        assert parsed["feedback_count"] == 0

    @pytest.mark.asyncio
    async def test_handle_get_metrics_after_queries(
        self, reset_server_state, test_settings
    ):
        """get_metrics should return updated metrics after queries."""
        import ai_governance_mcp.server as server_module
        from ai_governance_mcp.models import Metrics

        metrics = Metrics(
            total_queries=50,
            avg_retrieval_time_ms=42.5,
            s_series_trigger_count=5,
            domain_query_counts={"constitution": 50, "ai-coding": 30},
            confidence_distribution={"high": 20, "medium": 25, "low": 5},
            feedback_count=10,
            avg_feedback_rating=4.2,
        )
        server_module._state._metrics = metrics

        from ai_governance_mcp.server import _handle_get_metrics

        result = await _handle_get_metrics({})

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["total_queries"] == 50
        assert parsed["avg_retrieval_time_ms"] == 42.5
        assert parsed["s_series_trigger_count"] == 5
        assert parsed["domain_query_counts"]["ai-coding"] == 30
        assert parsed["avg_feedback_rating"] == 4.2


# =============================================================================
# Formatting Tests
# =============================================================================


class TestFormatRetrievalResult:
    """Tests for _format_retrieval_result() function."""

    def test_format_retrieval_result_basic(self, sample_retrieval_result):
        """Should format standard result as markdown."""
        from ai_governance_mcp.server import _format_retrieval_result

        output = _format_retrieval_result(sample_retrieval_result)

        assert "**Query:**" in output
        assert "test query" in output
        assert "**Domains Detected:**" in output
        assert "**Retrieval Time:**" in output
        assert "45.5ms" in output

    def test_format_retrieval_result_s_series_warning(self, sample_retrieval_result):
        """Should show S-Series warning when triggered."""
        from ai_governance_mcp.server import _format_retrieval_result

        sample_retrieval_result.s_series_triggered = True
        output = _format_retrieval_result(sample_retrieval_result)

        assert "S-SERIES TRIGGERED" in output
        assert "Safety/Ethics" in output

    def test_format_retrieval_result_no_results(self):
        """Should show no matching message for empty results."""
        from ai_governance_mcp.server import _format_retrieval_result
        from ai_governance_mcp.models import RetrievalResult

        empty_result = RetrievalResult(
            query="obscure query",
            domains_detected=[],
            constitution_principles=[],
            domain_principles=[],
            methods=[],
            s_series_triggered=False,
            retrieval_time_ms=10.0,
        )

        output = _format_retrieval_result(empty_result)

        assert "No matching principles found" in output

    def test_format_retrieval_result_truncates_content(self, scored_principle):
        """Should truncate content longer than 600 chars."""
        from ai_governance_mcp.server import _format_retrieval_result
        from ai_governance_mcp.models import RetrievalResult

        scored_principle.principle.content = "A" * 800

        result = RetrievalResult(
            query="test",
            domains_detected=["constitution"],
            constitution_principles=[scored_principle],
            domain_principles=[],
            methods=[],
            s_series_triggered=False,
            retrieval_time_ms=10.0,
        )

        output = _format_retrieval_result(result)

        assert "..." in output
        assert "A" * 700 not in output

    def test_format_retrieval_result_shows_domain_scores(self, sample_retrieval_result):
        """Should display domain routing scores."""
        from ai_governance_mcp.server import _format_retrieval_result

        output = _format_retrieval_result(sample_retrieval_result)

        assert "**Domain Scores:**" in output
        assert "constitution: 0.85" in output
        assert "ai-coding: 0.72" in output

    def test_format_retrieval_result_shows_methods(self, sample_retrieval_result):
        """Should show methods section when present."""
        from ai_governance_mcp.server import _format_retrieval_result

        output = _format_retrieval_result(sample_retrieval_result)

        assert "## Applicable Methods" in output
        assert "coding-M1" in output


class TestBestConfidence:
    """Tests for _best_confidence helper."""

    def test_returns_high_over_medium_and_low(self):
        from ai_governance_mcp.models import (
            ConfidenceLevel,
            Method,
            Principle,
            RetrievalResult,
            ScoredMethod,
            ScoredPrinciple,
        )
        from ai_governance_mcp.server.handlers.retrieval import _best_confidence

        p = Principle(
            id="test-p",
            domain="constitution",
            title="T",
            content="C",
            metadata={},
            line_range=[1, 10],
        )
        m = Method(
            id="test-m", domain="ai-coding", title="M", content="C", line_range=[1, 5]
        )
        result = RetrievalResult(
            query="test",
            domains_detected=["constitution"],
            constitution_principles=[
                ScoredPrinciple(
                    principle=p, confidence=ConfidenceLevel.LOW, combined_score=0.3
                )
            ],
            domain_principles=[
                ScoredPrinciple(
                    principle=p, confidence=ConfidenceLevel.MEDIUM, combined_score=0.5
                )
            ],
            methods=[
                ScoredMethod(
                    method=m, confidence=ConfidenceLevel.HIGH, combined_score=0.8
                )
            ],
        )
        assert _best_confidence(result) == ConfidenceLevel.HIGH

    def test_returns_none_when_empty(self):
        from ai_governance_mcp.models import RetrievalResult
        from ai_governance_mcp.server.handlers.retrieval import _best_confidence

        result = RetrievalResult(
            query="test",
            domains_detected=[],
            constitution_principles=[],
            domain_principles=[],
            methods=[],
        )
        assert _best_confidence(result) is None
