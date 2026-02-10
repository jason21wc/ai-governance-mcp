"""Unit tests for the MCP server module.

Per specification v4: Tests for all 6 MCP tools and server infrastructure.
Per governance Q3 (Testing Integration): Comprehensive coverage for server.py.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def extract_json_from_response(text: str) -> str:
    """Extract JSON portion from response, stripping governance reminder.

    Tool responses include a governance reminder footer after the JSON/markdown content.
    This helper extracts just the primary content for JSON parsing in tests.
    """
    # The reminder starts with "\n\n---\n⚖️" (updated 2026-01-01)
    separator = "\n\n---\n⚖️"
    if separator in text:
        return text.split(separator)[0]
    return text


# =============================================================================
# Global State Tests
# =============================================================================


class TestGetEngine:
    """Tests for get_engine() singleton."""

    def test_get_engine_creates_singleton(
        self, reset_server_state, test_settings, saved_index
    ):
        """get_engine() should create engine on first call."""
        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer"):
                with patch("sentence_transformers.CrossEncoder"):
                    from ai_governance_mcp.server import get_engine

                    engine = get_engine()
                    assert engine is not None

    def test_get_engine_returns_same_instance(
        self, reset_server_state, test_settings, saved_index
    ):
        """Subsequent calls should return the same engine instance."""
        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer"):
                with patch("sentence_transformers.CrossEncoder"):
                    from ai_governance_mcp.server import get_engine

                    engine1 = get_engine()
                    engine2 = get_engine()
                    assert engine1 is engine2


class TestGetMetrics:
    """Tests for get_metrics() singleton."""

    def test_get_metrics_creates_singleton(self, reset_server_state):
        """get_metrics() should create Metrics on first call."""
        from ai_governance_mcp.server import get_metrics
        from ai_governance_mcp.models import Metrics

        metrics = get_metrics()
        assert isinstance(metrics, Metrics)

    def test_get_metrics_returns_same_instance(self, reset_server_state):
        """Subsequent calls should return the same Metrics instance."""
        from ai_governance_mcp.server import get_metrics

        metrics1 = get_metrics()
        metrics2 = get_metrics()
        assert metrics1 is metrics2

    def test_get_metrics_initial_values(self, reset_server_state):
        """New Metrics should have default initial values."""
        from ai_governance_mcp.server import get_metrics

        metrics = get_metrics()
        assert metrics.total_queries == 0
        assert metrics.avg_retrieval_time_ms == 0.0
        assert metrics.s_series_trigger_count == 0
        assert metrics.feedback_count == 0


# =============================================================================
# Logging Function Tests
# =============================================================================


class TestLogQuery:
    """Tests for log_query() function."""

    def test_log_query_writes_jsonl(
        self, reset_server_state, test_settings, sample_query_log
    ):
        """log_query() should append QueryLog as JSONL."""
        import ai_governance_mcp.server as server_module

        server_module._settings = test_settings

        from ai_governance_mcp.server import log_query

        log_query(sample_query_log)

        log_file = test_settings.logs_path / "queries.jsonl"
        assert log_file.exists()

        content = log_file.read_text()
        assert "test query" in content

        # Verify it's valid JSON
        parsed = json.loads(content.strip())
        assert parsed["query"] == "test query"

    def test_log_query_appends_multiple(
        self, reset_server_state, test_settings, sample_query_log
    ):
        """log_query() should append multiple entries."""
        import ai_governance_mcp.server as server_module

        server_module._settings = test_settings

        from ai_governance_mcp.server import log_query

        log_query(sample_query_log)
        log_query(sample_query_log)

        log_file = test_settings.logs_path / "queries.jsonl"
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_log_query_without_settings(self, reset_server_state):
        """log_query() should handle None settings gracefully."""
        import ai_governance_mcp.server as server_module
        from ai_governance_mcp.server import log_query
        from ai_governance_mcp.models import QueryLog

        server_module._settings = None

        query_log = QueryLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query="test",
            domains_detected=[],
        )

        # Should not raise
        log_query(query_log)


class TestLogFeedbackEntry:
    """Tests for log_feedback_entry() function."""

    def test_log_feedback_entry_writes_jsonl(
        self, reset_server_state, test_settings, sample_feedback
    ):
        """log_feedback_entry() should append Feedback as JSONL."""
        import ai_governance_mcp.server as server_module

        server_module._settings = test_settings

        from ai_governance_mcp.server import log_feedback_entry

        log_feedback_entry(sample_feedback)

        log_file = test_settings.logs_path / "feedback.jsonl"
        assert log_file.exists()

        content = log_file.read_text()
        assert "test query" in content
        assert "meta-C1" in content

    def test_log_feedback_entry_without_settings(
        self, reset_server_state, sample_feedback
    ):
        """log_feedback_entry() should handle None settings gracefully."""
        import ai_governance_mcp.server as server_module
        from ai_governance_mcp.server import log_feedback_entry

        server_module._settings = None

        # Should not raise
        log_feedback_entry(sample_feedback)


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

        server_module._settings = test_settings
        server_module._metrics = None

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

        server_module._settings = test_settings
        server_module._metrics = None

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

        server_module._settings = test_settings
        server_module._metrics = None

        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()
        mock_engine.retrieve.return_value = sample_retrieval_result

        await _handle_query_governance(mock_engine, {"query": "logged query"})

        log_file = test_settings.logs_path / "queries.jsonl"
        assert log_file.exists()
        content = log_file.read_text()
        assert "logged query" in content

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

        server_module._settings = test_settings
        server_module._metrics = None

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
        """log_feedback should reject rating below 1."""
        from ai_governance_mcp.server import _handle_log_feedback

        # Note: rating=0 is falsy in Python, so it triggers "required" check first
        # Testing with -1 instead to test the range check
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
        """log_feedback should reject rating above 5."""
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

        server_module._settings = test_settings
        server_module._metrics = None

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

        # Pre-populate metrics
        metrics = Metrics(
            total_queries=50,
            avg_retrieval_time_ms=42.5,
            s_series_trigger_count=5,
            domain_query_counts={"constitution": 50, "ai-coding": 30},
            confidence_distribution={"high": 20, "medium": 25, "low": 5},
            feedback_count=10,
            avg_feedback_rating=4.2,
        )
        server_module._metrics = metrics

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

        # Create principle with long content
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

        # Should contain truncated content with ellipsis
        assert "..." in output
        # Should not contain full 800 chars
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


# =============================================================================
# Call Tool Dispatcher Tests
# =============================================================================


class TestCallTool:
    """Tests for call_tool() dispatcher."""

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(
        self, reset_server_state, test_settings, saved_index
    ):
        """call_tool should return message for unknown tool."""
        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer"):
                with patch("sentence_transformers.CrossEncoder"):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("nonexistent_tool", {})

                    assert len(result) == 1
                    assert "Unknown tool: nonexistent_tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(
        self, reset_server_state, test_settings, saved_index
    ):
        """call_tool should return ErrorResponse on exception."""
        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer"):
                with patch("sentence_transformers.CrossEncoder"):
                    from ai_governance_mcp.server import call_tool

                    # Force an exception by passing invalid arguments
                    with patch(
                        "ai_governance_mcp.server._handle_query_governance",
                        side_effect=Exception("Test error"),
                    ):
                        result = await call_tool("query_governance", {"query": "test"})

                        parsed = json.loads(extract_json_from_response(result[0].text))
                        assert parsed["error_code"] == "TOOL_ERROR"
                        assert "Test error" in parsed["message"]

    @pytest.mark.asyncio
    async def test_call_tool_includes_governance_reminder(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """All tool responses should include governance reminder footer."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, GOVERNANCE_REMINDER

                    # Test multiple tools to verify reminder is appended consistently
                    tools_to_test = [
                        ("list_domains", {}),
                        ("get_metrics", {}),
                        ("query_governance", {"query": "test"}),
                    ]

                    for tool_name, args in tools_to_test:
                        result = await call_tool(tool_name, args)
                        assert GOVERNANCE_REMINDER in result[0].text, (
                            f"Governance reminder missing from {tool_name} response"
                        )


# =============================================================================
# Evaluate Governance Tests (Governance Agent)
# =============================================================================


class TestEvaluateGovernance:
    """Tests for evaluate_governance tool (Governance Agent).

    Per multi-method-governance-agent-pattern (§4.3).
    """

    @pytest.mark.asyncio
    async def test_evaluate_governance_returns_assessment_structure(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return proper assessment structure."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new logging function"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Verify structure
                    assert "action_reviewed" in parsed
                    assert "assessment" in parsed
                    assert "confidence" in parsed
                    assert "relevant_principles" in parsed
                    assert "relevant_methods" in parsed
                    assert "compliance_evaluation" in parsed
                    assert "s_series_check" in parsed
                    assert "rationale" in parsed

                    # Assessment should be one of the valid statuses
                    assert parsed["assessment"] in [
                        "PROCEED",
                        "PROCEED_WITH_MODIFICATIONS",
                        "ESCALATE",
                    ]

    @pytest.mark.asyncio
    async def test_evaluate_governance_detects_safety_keywords(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should trigger ESCALATE for safety keywords."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Action with safety keyword
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Delete user credentials from database"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # S-Series should be triggered
                    assert parsed["s_series_check"]["triggered"] is True
                    assert len(parsed["s_series_check"]["safety_concerns"]) > 0
                    # Assessment should be ESCALATE
                    assert parsed["assessment"] == "ESCALATE"
                    # Confidence should be HIGH (safety is not uncertain)
                    assert parsed["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_evaluate_governance_missing_planned_action(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return error if planned_action missing."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("evaluate_governance", {})

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
                    assert "planned_action" in parsed["message"]

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_context(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should accept optional context and concerns."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Refactor authentication module",
                            "context": "Legacy code needs modernization",
                            "concerns": "Breaking changes to API",
                        },
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Should process without error
                    assert "action_reviewed" in parsed
                    assert parsed["action_reviewed"] == "Refactor authentication module"

    @pytest.mark.asyncio
    async def test_evaluate_governance_normal_action_proceeds(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return PROCEED for normal actions without safety keywords."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Normal action without safety concerns - very neutral language
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Format code with prettier"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # No safety keyword concerns should be detected from the action
                    assert len(parsed["s_series_check"]["safety_concerns"]) == 0
                    # If no S-Series principles returned AND no keyword concerns,
                    # assessment should be PROCEED
                    if not parsed["s_series_check"]["principles"]:
                        assert parsed["assessment"] == "PROCEED"

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_principle_content(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include full principle content for AI reasoning (§4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement user authentication"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # If principles were found, verify content is included
                    if parsed["relevant_principles"]:
                        first_principle = parsed["relevant_principles"][0]
                        assert "content" in first_principle
                        assert len(first_principle["content"]) > 0
                        assert "domain" in first_principle
                        assert "series_code" in first_principle

    @pytest.mark.asyncio
    async def test_evaluate_governance_sets_requires_ai_judgment(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should set requires_ai_judgment for non-S-Series cases (§4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Non-safety action that should match principles
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor the code structure"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # If principles found and no S-Series, should require AI judgment
                    if (
                        parsed["relevant_principles"]
                        and not parsed["s_series_check"]["triggered"]
                    ):
                        assert parsed["requires_ai_judgment"] is True
                        assert parsed["ai_judgment_guidance"] is not None

    @pytest.mark.asyncio
    async def test_evaluate_governance_escalate_does_not_require_ai_judgment(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """S-Series ESCALATE should not require AI judgment (script-enforced, §4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Delete all user credentials"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # S-Series ESCALATE is script-enforced, not AI judgment
                    assert parsed["assessment"] == "ESCALATE"
                    assert parsed["requires_ai_judgment"] is False

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_methods(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include relevant_methods as a list."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement project initialization workflow"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # relevant_methods should always be present as a list
                    assert "relevant_methods" in parsed
                    assert isinstance(parsed["relevant_methods"], list)

                    # If methods were found, verify each entry has correct fields
                    for method in parsed["relevant_methods"]:
                        assert isinstance(method["id"], str)
                        assert isinstance(method["title"], str)
                        assert isinstance(method["domain"], str)
                        assert isinstance(method["score"], (int, float))
                        assert 0.0 <= method["score"] <= 1.0
                        assert method["confidence"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_evaluate_governance_methods_in_ai_guidance(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """ai_judgment_guidance should mention methods only when relevant_methods is non-empty."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor the authentication module"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    if parsed.get("ai_judgment_guidance"):
                        if parsed["relevant_methods"]:
                            # When methods present, guidance should mention them
                            assert "method" in parsed["ai_judgment_guidance"].lower()
                        else:
                            # When no methods, guidance should not mention them
                            assert (
                                "method" not in parsed["ai_judgment_guidance"].lower()
                            )


# =============================================================================
# Audit Log Tests (Phase 2: Governance Enforcement)
# =============================================================================


class TestGovernanceAuditLog:
    """Tests for governance audit logging functionality."""

    @pytest.fixture(autouse=True)
    def reset_audit_log(self):
        """Reset audit log before each test."""
        from ai_governance_mcp import server

        server._audit_log = []
        yield
        server._audit_log = []

    @pytest.mark.asyncio
    async def test_evaluate_governance_logs_audit(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should log audit entry."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, get_audit_log

                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement new feature"},
                    )

                    audit_log = get_audit_log()
                    assert len(audit_log) == 1
                    assert audit_log[0].action == "Implement new feature"
                    assert audit_log[0].audit_id.startswith("gov-")

    @pytest.mark.asyncio
    async def test_audit_log_captures_assessment_status(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Audit log should capture assessment status."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool, get_audit_log
                    from ai_governance_mcp.models import AssessmentStatus

                    # Normal action - should be PROCEED
                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Format code with prettier"},
                    )

                    audit_log = get_audit_log()
                    assert len(audit_log) == 1
                    # Assessment should be captured
                    assert audit_log[0].assessment in [
                        AssessmentStatus.PROCEED,
                        AssessmentStatus.PROCEED_WITH_MODIFICATIONS,
                        AssessmentStatus.ESCALATE,
                    ]


class TestVerifyGovernanceCompliance:
    """Tests for verify_governance_compliance tool."""

    @pytest.fixture(autouse=True)
    def reset_audit_log(self):
        """Reset audit log before each test."""
        from ai_governance_mcp import server

        server._audit_log = []
        yield
        server._audit_log = []

    @pytest.mark.asyncio
    async def test_verify_returns_non_compliant_when_no_audit(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should return NON_COMPLIANT when no audit log."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "verify_governance_compliance",
                        {"action_description": "Made some changes"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert parsed["status"] == "NON_COMPLIANT"
                    assert "No governance checks" in parsed["finding"]

    @pytest.mark.asyncio
    async def test_verify_returns_compliant_after_evaluate(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should return COMPLIANT after evaluate_governance."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # First, call evaluate_governance
                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement config generator feature"},
                    )

                    # Then verify compliance
                    result = await call_tool(
                        "verify_governance_compliance",
                        {"action_description": "Implemented config generator feature"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert parsed["status"] == "COMPLIANT"
                    assert parsed["matching_audit_id"] is not None

    @pytest.mark.asyncio
    async def test_verify_requires_action_description(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should require action_description."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "verify_governance_compliance",
                        {},  # Missing action_description
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert "error_code" in parsed
                    assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"


# =============================================================================
# Entry Point Tests
# =============================================================================


class TestMain:
    """Tests for main() entry point."""

    def test_main_test_mode(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        capsys,
        mock_embedder,
        mock_reranker,
    ):
        """main() with --test should run retrieve and print result."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    with patch("sys.argv", ["server", "--test"]):
                        from ai_governance_mcp.server import main

                        main()

                        captured = capsys.readouterr()
                        assert "Query:" in captured.out or "**Query:**" in captured.out

    def test_main_test_mode_custom_query(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        capsys,
        mock_embedder,
        mock_reranker,
    ):
        """main() with --test and custom query should use that query."""
        # Need to mock the actual model classes that get instantiated
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    with patch(
                        "sys.argv", ["server", "--test", "custom", "test", "query"]
                    ):
                        from ai_governance_mcp.server import main

                        main()

                        captured = capsys.readouterr()
                        # Output should contain some result (query info or "no matching")
                        assert len(captured.out) > 0


# =============================================================================
# List Tools Tests
# =============================================================================


class TestListTools:
    """Tests for list_tools() async function."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_eleven(self):
        """list_tools should return all 11 tools."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()

        assert len(tools) == 11
        tool_names = [t.name for t in tools]
        assert "query_governance" in tool_names
        assert "get_principle" in tool_names
        assert "list_domains" in tool_names
        assert "get_domain_summary" in tool_names
        assert "log_feedback" in tool_names
        assert "get_metrics" in tool_names
        assert "evaluate_governance" in tool_names
        assert "verify_governance_compliance" in tool_names
        assert "log_governance_reasoning" in tool_names
        assert "install_agent" in tool_names
        assert "uninstall_agent" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_have_input_schemas(self):
        """All tools should have valid input schemas."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()

        for tool in tools:
            assert tool.inputSchema is not None
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_query_governance_schema_requires_query(self):
        """query_governance should require 'query' parameter."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()
        query_tool = next(t for t in tools if t.name == "query_governance")

        assert "query" in query_tool.inputSchema.get("required", [])
        assert "query" in query_tool.inputSchema["properties"]


class TestInstallAgent:
    """Tests for install_agent tool."""

    @pytest.mark.asyncio
    async def test_install_agent_non_claude_environment(self, tmp_path, monkeypatch):
        """install_agent should return not_applicable for non-Claude environments."""
        from ai_governance_mcp.server import _handle_install_agent

        # Set cwd to temp path with no Claude indicators
        monkeypatch.chdir(tmp_path)

        result = await _handle_install_agent({"agent_name": "orchestrator"})

        assert len(result) == 1
        response = json.loads(
            result[0].text.split("---")[0]
        )  # Remove governance reminder
        assert response["status"] == "not_applicable"
        assert response["platform"] == "non-claude"
        assert "server instructions" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_install_agent_invalid_agent_name(self, tmp_path, monkeypatch):
        """install_agent should reject unknown agent names."""
        from ai_governance_mcp.server import _handle_install_agent

        monkeypatch.chdir(tmp_path)

        result = await _handle_install_agent({"agent_name": "unknown_agent"})

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_AGENT"
        assert "unknown_agent" in response["message"]

    @pytest.mark.asyncio
    async def test_install_agent_preview_in_claude_environment(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent should return preview when not confirmed in Claude environment."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment indicators
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        # Set up settings to point to real documents path (has agent templates)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator"}
        )

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["agent_name"] == "orchestrator"
        assert "explanation" in response
        assert "options" in response

    @pytest.mark.asyncio
    async def test_install_agent_manual_instructions(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent with show_manual should return installation instructions."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        # Set up settings to point to real documents path
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator", "show_manual": True}
        )

        assert len(result) == 1
        # Extract JSON before the governance reminder (starts with "\n\n---\n")
        text = result[0].text
        json_end = text.rfind("\n\n---\n")
        json_str = text[:json_end] if json_end > 0 else text
        response = json.loads(json_str)
        assert response["status"] == "manual_instructions"
        assert "content" in response
        assert "orchestrator" in response["content"].lower()

    @pytest.mark.asyncio
    async def test_install_agent_confirmed_creates_file(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent with confirmed=true should create the agent file."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        # Set up settings to point to real documents path
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator", "confirmed": True}
        )

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "installed"

        # Verify file was created
        agent_file = tmp_path / ".claude" / "agents" / "orchestrator.md"
        assert agent_file.exists()
        content = agent_file.read_text()
        assert "orchestrator" in content.lower()


class TestUninstallAgent:
    """Tests for uninstall_agent tool."""

    @pytest.mark.asyncio
    async def test_uninstall_agent_not_installed(self, tmp_path, monkeypatch):
        """uninstall_agent should report when agent is not installed."""
        from ai_governance_mcp.server import _handle_uninstall_agent

        monkeypatch.chdir(tmp_path)

        result = await _handle_uninstall_agent({"agent_name": "orchestrator"})

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "not_installed"

    @pytest.mark.asyncio
    async def test_uninstall_agent_invalid_agent_name(self, tmp_path, monkeypatch):
        """uninstall_agent should reject unknown agent names."""
        from ai_governance_mcp.server import _handle_uninstall_agent

        monkeypatch.chdir(tmp_path)

        result = await _handle_uninstall_agent({"agent_name": "unknown_agent"})

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_AGENT"

    @pytest.mark.asyncio
    async def test_uninstall_agent_confirm_prompt(self, tmp_path, monkeypatch):
        """uninstall_agent should prompt for confirmation when agent exists."""
        from ai_governance_mcp.server import _handle_uninstall_agent

        # Create installed agent
        agent_dir = tmp_path / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "orchestrator.md"
        agent_file.write_text("# Test Agent")
        monkeypatch.chdir(tmp_path)

        result = await _handle_uninstall_agent({"agent_name": "orchestrator"})

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "confirm_uninstall"
        assert "warning" in response

    @pytest.mark.asyncio
    async def test_uninstall_agent_confirmed_removes_file(self, tmp_path, monkeypatch):
        """uninstall_agent with confirmed=true should remove the agent file."""
        from ai_governance_mcp.server import _handle_uninstall_agent

        # Create installed agent
        agent_dir = tmp_path / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "orchestrator.md"
        agent_file.write_text("# Test Agent")
        monkeypatch.chdir(tmp_path)

        result = await _handle_uninstall_agent(
            {"agent_name": "orchestrator", "confirmed": True}
        )

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "uninstalled"

        # Verify file was removed
        assert not agent_file.exists()


class TestClaudeCodeDetection:
    """Tests for Claude Code environment detection."""

    def test_detect_claude_with_dot_claude_dir(self, tmp_path, monkeypatch):
        """Should detect Claude Code when .claude/ directory exists."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        (tmp_path / ".claude").mkdir()
        monkeypatch.chdir(tmp_path)

        assert _detect_claude_code_environment() is True

    def test_detect_claude_with_claude_md(self, tmp_path, monkeypatch):
        """Should detect Claude Code when CLAUDE.md exists."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        (tmp_path / "CLAUDE.md").write_text("# Test")
        monkeypatch.chdir(tmp_path)

        assert _detect_claude_code_environment() is True

    def test_detect_no_claude_indicators(self, tmp_path, monkeypatch):
        """Should not detect Claude Code when no indicators present."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        monkeypatch.chdir(tmp_path)

        assert _detect_claude_code_environment() is False


# =============================================================================
# Security Feature Tests (H4, M1, M4, M6)
# =============================================================================


class TestRateLimiting:
    """Tests for H4: Rate limiting (token bucket algorithm)."""

    def test_rate_limit_allows_initial_requests(self):
        """Initial requests should be allowed."""
        from ai_governance_mcp.server import _check_rate_limit

        # Reset rate limiter
        import ai_governance_mcp.server as server_module

        server_module._rate_limit_tokens = server_module.RATE_LIMIT_TOKENS

        assert _check_rate_limit() is True

    def test_rate_limit_exhaustion(self):
        """Rapid requests should eventually be rate limited."""
        import ai_governance_mcp.server as server_module
        from ai_governance_mcp.server import _check_rate_limit

        # Exhaust the token bucket
        server_module._rate_limit_tokens = 1
        assert _check_rate_limit() is True  # Uses last token
        assert _check_rate_limit() is False  # No tokens left

        # Reset for other tests
        server_module._rate_limit_tokens = server_module.RATE_LIMIT_TOKENS


class TestSecretsDetection:
    """Tests for M4: Secrets detection in queries."""

    def test_sanitize_redacts_api_keys(self):
        """API keys should be redacted from logging."""
        from ai_governance_mcp.server import _sanitize_for_logging

        content = "My api_key=sk_live_abc123xyz456789012345"
        sanitized = _sanitize_for_logging(content)
        assert "sk_live" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_redacts_passwords(self):
        """Passwords should be redacted from logging."""
        from ai_governance_mcp.server import _sanitize_for_logging

        content = "password=supersecret123"
        sanitized = _sanitize_for_logging(content)
        assert "supersecret123" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_redacts_bearer_tokens(self):
        """Bearer tokens should be redacted from logging."""
        from ai_governance_mcp.server import _sanitize_for_logging

        content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = _sanitize_for_logging(content)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_truncates_long_content(self):
        """Long content should be truncated."""
        from ai_governance_mcp.server import (
            _sanitize_for_logging,
            MAX_LOG_CONTENT_LENGTH,
        )

        # Use a pattern that won't match the generic 32+ char alphanumeric secret detector
        content = "Hello world. " * (MAX_LOG_CONTENT_LENGTH // 10)
        sanitized = _sanitize_for_logging(content)
        assert len(sanitized) < len(content)
        assert "TRUNCATED" in sanitized

    def test_sanitize_preserves_safe_content(self):
        """Safe content should be preserved."""
        from ai_governance_mcp.server import _sanitize_for_logging

        content = "How do I implement a login system?"
        sanitized = _sanitize_for_logging(content)
        assert sanitized == content


class TestErrorSanitization:
    """Tests for M6: Error message sanitization."""

    def test_sanitize_error_removes_absolute_paths(self):
        """Absolute paths should be removed from error messages."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("File not found: /Users/jason/secret/project/file.py")
        sanitized = _sanitize_error_message(error)
        assert "/Users/jason/secret/project" not in sanitized
        assert "file.py" in sanitized

    def test_sanitize_error_removes_line_numbers(self):
        """Line numbers should be removed from error messages."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("Error at script.py, line 42")
        sanitized = _sanitize_error_message(error)
        assert "line 42" not in sanitized

    def test_sanitize_error_removes_memory_addresses(self):
        """Memory addresses should be obscured in error messages."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("Object at 0x7f8b4c3d2e1a")
        sanitized = _sanitize_error_message(error)
        assert "0x7f8b4c3d2e1a" not in sanitized
        assert "0x***" in sanitized


class TestInputValidation:
    """Tests for M5: Type validation on MCP inputs."""

    @pytest.mark.asyncio
    async def test_query_length_validation(
        self, reset_server_state, test_settings, saved_index
    ):
        """Queries exceeding MAX_QUERY_LENGTH should be rejected."""
        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer"):
                with patch("sentence_transformers.CrossEncoder"):
                    from ai_governance_mcp.server import (
                        _handle_query_governance,
                        get_engine,
                        MAX_QUERY_LENGTH,
                    )

                    engine = get_engine()
                    long_query = "x" * (MAX_QUERY_LENGTH + 1)

                    result = await _handle_query_governance(
                        engine, {"query": long_query}
                    )
                    assert "exceeds maximum length" in result[0].text


class TestValidateLogPath:
    """Tests for M1 FIX: Log path containment validation."""

    def test_validate_log_path_accepts_project_root(self, tmp_path):
        """Paths within project root should be accepted."""
        from ai_governance_mcp.server import _validate_log_path

        # Get project root (where server.py is located, go up 3 levels)
        from pathlib import Path

        project_root = Path(__file__).parent.parent.resolve()
        log_path = project_root / "logs" / "test.jsonl"

        # Should not raise
        _validate_log_path(log_path)

    def test_validate_log_path_accepts_home_directory(self):
        """Paths within home directory should be accepted."""
        from ai_governance_mcp.server import _validate_log_path
        from pathlib import Path

        home_path = Path.home() / ".ai-governance" / "logs" / "test.jsonl"

        # Should not raise
        _validate_log_path(home_path)

    def test_validate_log_path_accepts_temp_directory(self, tmp_path):
        """Paths within temp directory should be accepted (for tests)."""
        from ai_governance_mcp.server import _validate_log_path

        log_path = tmp_path / "logs" / "test.jsonl"

        # Should not raise
        _validate_log_path(log_path)

    def test_validate_log_path_rejects_path_traversal(self, tmp_path):
        """Paths containing '..' should be rejected."""
        from ai_governance_mcp.server import _validate_log_path

        malicious_path = tmp_path / "logs" / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValueError, match="Path traversal sequence detected"):
            _validate_log_path(malicious_path)

    def test_validate_log_path_rejects_outside_boundaries(self):
        """Paths outside project/home/temp should be rejected."""
        from ai_governance_mcp.server import _validate_log_path
        from pathlib import Path

        # Use a path that's definitely outside boundaries
        outside_path = Path("/nonexistent/random/location/log.jsonl")

        with pytest.raises(ValueError, match="must be within"):
            _validate_log_path(outside_path)


class TestAgentOverwriteWarning:
    """Tests for M2 FIX: Agent overwrite content comparison."""

    @pytest.mark.asyncio
    async def test_install_agent_content_differs_when_different(
        self, tmp_path, monkeypatch, real_settings
    ):
        """content_differs should be True when existing file has different content."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment with existing agent file
        claude_dir = tmp_path / ".claude"
        agents_dir = claude_dir / "agents"
        agents_dir.mkdir(parents=True)

        # Create existing agent file with different content
        existing_file = agents_dir / "orchestrator.md"
        existing_file.write_text("# Old custom content\nThis is different.")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator"}
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["already_installed"] is True
        assert response["content_differs"] is True
        assert "warning" in response
        assert "different content" in response["warning"].lower()

    @pytest.mark.asyncio
    async def test_install_agent_content_differs_false_when_same(
        self, tmp_path, monkeypatch, real_settings
    ):
        """content_differs should be False when existing file has same content."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment
        claude_dir = tmp_path / ".claude"
        agents_dir = claude_dir / "agents"
        agents_dir.mkdir(parents=True)

        # Read template content and create identical file
        template_path = real_settings.documents_path / "agents" / "orchestrator.md"
        template_content = template_path.read_text()

        existing_file = agents_dir / "orchestrator.md"
        existing_file.write_text(template_content)

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator"}
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["already_installed"] is True
        assert response["content_differs"] is False
        assert "warning" not in response

    @pytest.mark.asyncio
    async def test_install_agent_no_content_differs_for_new_install(
        self, tmp_path, monkeypatch, real_settings
    ):
        """content_differs should be False for new installations."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment with no existing agent file
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator"}
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["already_installed"] is False
        assert response["content_differs"] is False
        assert "warning" not in response


class TestImprovedErrorSanitization:
    """Tests for M3 FIX: Improved error message sanitization."""

    def test_sanitize_error_removes_module_paths(self):
        """Module paths like foo.bar.baz should be sanitized."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("Error in ai_governance_mcp.server.retrieval.query_engine")
        sanitized = _sanitize_error_message(error)
        assert "ai_governance_mcp.server.retrieval.query_engine" not in sanitized
        assert "[module]" in sanitized

    def test_sanitize_error_removes_function_references(self):
        """Function references in tracebacks should be sanitized."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("Error occurred in process_query()")
        sanitized = _sanitize_error_message(error)
        assert "process_query(" not in sanitized
        assert "[func](" in sanitized

    def test_sanitize_error_removes_quoted_file_references(self):
        """Quoted file references from tracebacks should be sanitized."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("File '/path/to/module.py' caused error")
        sanitized = _sanitize_error_message(error)
        assert "'/path/to/module.py'" not in sanitized
        assert "File [redacted]" in sanitized

    def test_sanitize_error_removes_exception_chains(self):
        """Exception chain phrases should be sanitized."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("During handling of the above exception, another occurred")
        sanitized = _sanitize_error_message(error)
        assert "During handling of" not in sanitized
        assert "[exception chain]" in sanitized

    def test_sanitize_error_truncates_long_messages(self):
        """Very long error messages should be truncated."""
        from ai_governance_mcp.server import _sanitize_error_message

        # Create error with message over 500 chars
        long_message = "x" * 600
        error = Exception(long_message)
        sanitized = _sanitize_error_message(error)
        assert len(sanitized) <= 520  # 500 + "[truncated]" length
        assert "...[truncated]" in sanitized

    def test_sanitize_error_preserves_useful_content(self):
        """Sanitization should preserve useful error context."""
        from ai_governance_mcp.server import _sanitize_error_message

        error = Exception("Configuration error: missing required field 'name'")
        sanitized = _sanitize_error_message(error)
        # Should preserve the main error message
        assert "Configuration error" in sanitized
        assert "missing required field" in sanitized


# =============================================================================
# Governance Reasoning Externalization Tests
# =============================================================================


class TestLogGovernanceReasoning:
    """Tests for log_governance_reasoning tool."""

    @pytest.fixture(autouse=True)
    def reset_logs(self):
        """Reset audit and reasoning logs before each test."""
        from ai_governance_mcp import server

        server._audit_log.clear()
        server._reasoning_log.clear()
        yield
        server._audit_log.clear()
        server._reasoning_log.clear()

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_audit_id(self, reset_server_state):
        """Should return error when audit_id is missing."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning({})
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "audit_id" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_reasoning(self, reset_server_state):
        """Should return error when reasoning array is empty."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-123456789012",
                "reasoning": [],
                "final_decision": "PROCEED",
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "reasoning" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_final_decision(self, reset_server_state):
        """Should return error when final_decision is missing."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-123456789012",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Test",
                    }
                ],
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "final_decision" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_invalid_audit_id(self, reset_server_state):
        """Should return error when audit_id doesn't exist."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-nonexistent1",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Test",
                    }
                ],
                "final_decision": "PROCEED",
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "AUDIT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_log_reasoning_success(self, reset_server_state):
        """log_governance_reasoning should log reasoning trace successfully."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry directly (simpler than mocking full pipeline)
        audit_id = "gov-success12345"
        audit_entry = GovernanceAuditLog(
            audit_id=audit_id,
            timestamp="2026-01-01T00:00:00Z",
            action="Test action for reasoning",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Now call log_governance_reasoning with that audit_id
        result = await _handle_log_governance_reasoning(
            {
                "audit_id": audit_id,
                "reasoning": [
                    {
                        "principle_id": "meta-C1",
                        "status": "COMPLIES",
                        "reasoning": "Action follows quality standards.",
                    },
                    {
                        "principle_id": "coding-Q1",
                        "status": "NEEDS_MODIFICATION",
                        "reasoning": "Should add input validation.",
                    },
                ],
                "final_decision": "PROCEED_WITH_MODIFICATIONS",
                "modifications_applied": ["Added input validation"],
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert parsed["audit_id"] == audit_id
        assert parsed["entries_logged"] == 2
        assert parsed["final_decision"] == "PROCEED_WITH_MODIFICATIONS"
        assert parsed["modifications_count"] == 1

        # Verify reasoning log contains the entry
        reasoning_log = get_reasoning_log()
        assert len(reasoning_log) == 1
        assert reasoning_log[0].audit_id == audit_id
        assert len(reasoning_log[0].reasoning_entries) == 2
        assert reasoning_log[0].final_decision == "PROCEED_WITH_MODIFICATIONS"

    @pytest.mark.asyncio
    async def test_log_reasoning_sanitizes_input(self, reset_server_state):
        """Should sanitize reasoning text to prevent injection."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry directly
        audit_entry = GovernanceAuditLog(
            audit_id="gov-sanitize123",
            timestamp="2026-01-01T00:00:00Z",
            action="Test sanitization",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Call with potentially dangerous input
        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-sanitize123",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Normal text <script>alert('xss')</script> more text",
                    }
                ],
                "final_decision": "PROCEED",
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"

        # Verify the reasoning was logged (sanitization doesn't reject, just cleans)
        reasoning_log = get_reasoning_log()
        assert len(reasoning_log) == 1

    @pytest.mark.asyncio
    async def test_log_reasoning_limits_entries(self, reset_server_state):
        """Should limit reasoning entries to 20."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry
        audit_entry = GovernanceAuditLog(
            audit_id="gov-limit1234567",
            timestamp="2026-01-01T00:00:00Z",
            action="Test limits",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Create 25 reasoning entries
        many_entries = [
            {
                "principle_id": f"test-{i}",
                "status": "COMPLIES",
                "reasoning": f"Entry {i}",
            }
            for i in range(25)
        ]

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-limit1234567",
                "reasoning": many_entries,
                "final_decision": "PROCEED",
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert parsed["entries_logged"] == 20  # Limited to 20

        reasoning_log = get_reasoning_log()
        assert len(reasoning_log[0].reasoning_entries) == 20
