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
    """Tests for get_engine() singleton.

    Paired with `TestGetMetrics` for singleton-pattern coverage. Tests are
    NOT parametrized together — despite the surface similarity, the mock
    setup materially differs: `get_engine()` requires `test_settings`,
    `saved_index`, and nested patches on `load_settings` +
    `SentenceTransformer` + `CrossEncoder`; `get_metrics()` only requires
    `reset_server_state`. Forcing a shared parametrize obscures intent
    and adds conditional-patching complexity that hides per-service
    setup. Kept as separate classes per CFR §5.2.8 "when NOT to
    consolidate: contract tests that look meta" (BACKLOG #122 Case 6).
    """

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
    """Tests for get_metrics() singleton.

    Paired with `TestGetEngine`; see that class's docstring for why these
    are kept separate rather than parametrized. This class has the lighter
    fixture surface (only `reset_server_state`), reflecting `get_metrics()`'s
    simpler initialization path (no embedding/reranker loading).
    """

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


class TestJsonlLogRotation:
    """Tests for JSONL log rotation in _write_log_sync."""

    def test_rotation_triggers_at_max_bytes(
        self, reset_server_state, test_settings, sample_query_log
    ):
        """Rotation should occur when log file exceeds max_bytes."""
        import ai_governance_mcp.server as server_module

        test_settings.log_max_bytes = 500
        test_settings.log_backup_count = 3
        server_module._settings = test_settings

        from ai_governance_mcp.server import log_query

        for _ in range(20):
            log_query(sample_query_log)

        log_file = test_settings.logs_path / "queries.jsonl"
        backup1 = test_settings.logs_path / "queries.jsonl.1"

        assert log_file.exists()
        assert backup1.exists()

    def test_writes_succeed_after_rotation(
        self, reset_server_state, test_settings, sample_query_log
    ):
        """Writes must succeed after rotation occurs."""
        import ai_governance_mcp.server as server_module

        test_settings.log_max_bytes = 500
        test_settings.log_backup_count = 2
        server_module._settings = test_settings

        from ai_governance_mcp.server import log_query

        for _ in range(20):
            log_query(sample_query_log)

        log_file = test_settings.logs_path / "queries.jsonl"
        assert log_file.exists()
        content = log_file.read_text().strip()
        assert len(content) > 0
        for line in content.split("\n"):
            parsed = json.loads(line)
            assert parsed["query"] == "test query"

    def test_rotation_disabled_when_max_bytes_zero(
        self, reset_server_state, test_settings, sample_query_log
    ):
        """No rotation when log_max_bytes is 0 (disabled)."""
        import ai_governance_mcp.server as server_module

        test_settings.log_max_bytes = 0
        server_module._settings = test_settings

        from ai_governance_mcp.server import log_query

        for _ in range(10):
            log_query(sample_query_log)

        log_file = test_settings.logs_path / "queries.jsonl"
        backup1 = test_settings.logs_path / "queries.jsonl.1"
        assert log_file.exists()
        assert not backup1.exists()


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
        """log_feedback should reject rating below 1.

        Covers: FM-FEEDBACK-RATING-BOUNDS
        """
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

    # =========================================================================
    # FM-S-SERIES-KEYWORD-FALSE-POSITIVE coverage tests (BACKLOG #129).
    # Sentence-level safe-context allowlist; demotes CRITICAL keyword matches
    # to ADVISORY when (a) every sentence containing the keyword has a leader
    # phrase, AND (b) no imperative-action verb appears in the action.
    # Imperative + safe-context re-escalates (bypass guard).
    # =========================================================================

    @pytest.mark.asyncio
    async def test_evaluate_governance_safe_context_demotes_critical_keyword(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """CRITICAL keyword inside negation+meta-description envelope demotes.

        Asserts the keyword-side outcome: demotion correctly moves the keyword
        match out of `safety_concerns` and into `safety_warnings` with the
        demotion message. The `triggered` field may still be True if semantic
        retrieval independently matches an S-Series principle (semantic-side
        FP is BACKLOG #129 Path B, deferred to a separate fix surface).

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "Expand the docs section. No destructive implications. Purely content addition.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Keyword-side demotion: 'destructive' moved out of safety_concerns.
                    # Note: safety_warnings is only populated when keyword_only_warning
                    # holds (no semantic match + no critical keyword); semantic match
                    # in the mock index can still set s_series_triggered=True.
                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), (
                        f"keyword should be demoted out of safety_concerns; got {concerns}"
                    )

    @pytest.mark.asyncio
    async def test_evaluate_governance_meta_description_does_not_escalate(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """CRITICAL keyword in self-referential meta-description demotes.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "Description of a destructive-action FP class without intent or target parsing.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"keyword should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_destructive_implications_passes(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """LEARNING-LOG 2026-02-22 negation exemplar (CRITICAL variant) no longer FPs.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "No destructive implications. Purely content expansion.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"keyword should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_multi_word_critical_in_safe_context(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Multi-word CRITICAL keyword (api key) handled natively by sentence-level check.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "Description of api key rotation patterns. Purely architectural review. No destructive operations involved.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Both 'api key' and 'destructive' should be demoted.
                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "api key" in c and "requires safety review" in c
                        for c in concerns
                    ), f"'api key' should be demoted; got {concerns}"
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"'destructive' should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_imperative_overrides_safe_envelope(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Bypass guard: imperative-action verb re-escalates wrapped CRITICAL keyword.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "No destructive concerns. Then rm -rf the credentials directory anyway.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    @pytest.mark.asyncio
    async def test_evaluate_governance_partial_wrap_per_sentence_rule_fires(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Per-sentence rule: keyword in sentence WITHOUT a leader escalates even when other sentences are wrapped.

        Sentence 1 has leader (Description of) + keyword (credential). Sentence 2 has
        keyword (credential, via 'credential-stuff') but NO leader and NO imperative.
        Action-level imperative override does NOT fire here — only the per-sentence
        rule can escalate this case correctly.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "Description of credential rotation. Then we credential-stuff the production endpoint.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    @pytest.mark.asyncio
    async def test_evaluate_governance_imperative_inside_envelope_known_overtrigger(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Documented over-trigger: imperative verb anywhere in action blocks demotion.

        Even when the imperative verb sits INSIDE a meta-description envelope
        ('Description of the ship-to-prod deployment pattern'), the action-level
        imperative check fires and demotion is blocked. This is intentional
        conservative bias — bypass-vector defense over fine-grained accuracy.
        Documented for downstream review if real friction emerges.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Note: this asserts the conservative-bias behavior. If
                    # 'ship' (or another inside-envelope imperative) produces
                    # observable friction, scope the imperative check at the
                    # sentence level (matching keyword's host sentences only).
                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Description of the destructive ship-to-prod deployment pattern.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True

    @pytest.mark.asyncio
    async def test_evaluate_governance_em_dash_separates_sentences(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Em-dash with surrounding whitespace acts as sentence boundary.

        Adversarial: 'Discussion of credential-rotation hygiene — then nuke the keystore'
        is one sentence under [.!?]+ but two sentences under the widened
        boundary regex. The post-em-dash sentence has 'nuke' (imperative) which
        triggers the action-level override. Defense in depth.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "Discussion of credential-rotation hygiene — then nuke the keystore.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    def test_imperative_action_verbs_covers_common_mutations(self):
        """`_IMPERATIVE_ACTION_VERBS` must cover common mutation/disclosure verbs.

        Defends silent-FN class: a CRITICAL keyword wrapped in a safe-context
        sentence (no imperative verb in that sentence) but paired with a
        destructive action elsewhere in the action string. Per FM-S-SERIES
        co-evolution rule (registry description) — failure here forces
        deliberate audit when imperative list drifts.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        from ai_governance_mcp.server import _IMPERATIVE_ACTION_VERBS

        required_verbs = (
            "ship",
            "deploy",
            "delete",
            "drop",
            "truncate",
            "wipe",
            "rm",
            "erase",
            "purge",
            "kill",
            "nuke",
            "format",
            "chmod",
            "sudo",
            "flush",
            "revoke",
            "terminate",
            "rotate",
            "replace",
            "migrate",
            "modify",
            "restart",
            "restore",
            "clone",
            "expose",
            "leak",
            "dump",
        )
        for verb in required_verbs:
            assert _IMPERATIVE_ACTION_VERBS.search(verb), (
                f"common mutation/disclosure verb {verb!r} missing from "
                f"_IMPERATIVE_ACTION_VERBS — drift risks silent FN per "
                f"BACKLOG #129 post-arc contrarian audit a8e2e0926f756db45 HIGH #1"
            )

    def test_critical_safety_keywords_pinned_for_co_evolution(self):
        """Pin CRITICAL keyword set so growth forces imperative-list audit.

        When this test fails, the author MUST audit `_IMPERATIVE_ACTION_VERBS`
        for newly-needed mutation/disclosure verbs paired with the new CRITICAL
        keyword, then update both `expected_critical` here AND the imperative
        list in `server.py`. Per FM-S-SERIES co-evolution rule.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        from ai_governance_mcp.server import CRITICAL_SAFETY_KEYWORDS

        expected_critical = frozenset(
            {
                "credential",
                "password",
                "secret",
                "api key",
                "private key",
                "access token",
                "encryption key",
                "pii",
                "personal data",
                "irreversible",
                "destructive",
            }
        )
        actual = frozenset(CRITICAL_SAFETY_KEYWORDS)
        assert actual == expected_critical, (
            f"CRITICAL_SAFETY_KEYWORDS changed (added: {actual - expected_critical}, "
            f"removed: {expected_critical - actual}). Audit `_IMPERATIVE_ACTION_VERBS` "
            f"for newly-needed verbs paired with the change, then update both "
            f"expected_critical in this test AND the imperative list in server.py. "
            f"FM-S-SERIES co-evolution rule (registry description)."
        )

    @pytest.mark.asyncio
    async def test_evaluate_governance_field_bridging_does_not_demote(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Per-field calls prevent leader in `context` from covering keyword in `planned_action`.

        Without per-field call refactor (round-2 contrarian HIGH #1), a benign-
        looking 'Discussion of cleanup procedures' in `context` could silently
        cover a real CRITICAL keyword in `planned_action`. With per-field calls,
        each field is its own sentence stream — no bridging.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
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
                            "planned_action": "rm -rf /var/log/credentials",
                            "context": "Discussion of cleanup procedures.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"


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
    async def test_list_tools_returns_all_twelve(self):
        """list_tools should return all 12 tools."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()

        assert len(tools) == 13
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
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        result = await _handle_install_agent({"agent_name": "orchestrator"})

        assert len(result) == 1
        response = json.loads(
            result[0].text.split("---")[0]
        )  # Remove governance reminder
        assert response["status"] == "not_applicable"
        assert response["platform"] == "non-claude"
        assert response["agent_name"] == "orchestrator"
        assert "agent_content" in response
        assert "adaptation_guidance" in response

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
        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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

        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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


class TestResolveCallerProjectPath:
    """Tests for _resolve_caller_project_path (4-tier project path resolution)."""

    def _set_mock_roots(self, monkeypatch, side_effect=None, roots=None):
        """Set up mock MCP request context via the ContextVar."""
        import ai_governance_mcp.server as server_module
        from mcp.server.lowlevel.server import request_ctx

        # Reset roots cache so each test gets a fresh lookup
        server_module._cached_roots_path = None

        mock_session = Mock()
        if side_effect:
            mock_session.list_roots = Mock(side_effect=side_effect)
        elif roots is not None:

            async def mock_list_roots():
                result = Mock()
                result.roots = roots
                return result

            mock_session.list_roots = mock_list_roots
        else:
            mock_session.list_roots = Mock(side_effect=Exception("no roots"))

        mock_request_context = Mock()
        mock_request_context.session = mock_session
        request_ctx.set(mock_request_context)

    @pytest.mark.asyncio
    async def test_explicit_path_takes_priority(self, tmp_path, monkeypatch):
        """Explicit project_path argument should take priority over CWD."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        self._set_mock_roots(monkeypatch, side_effect=Exception("no roots"))
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {"project_path": str(tmp_path)}
        )
        assert result_path == tmp_path.resolve()
        assert used_fallback is False

    @pytest.mark.asyncio
    async def test_env_var_fallback(self, tmp_path, monkeypatch):
        """AI_GOVERNANCE_MCP_PROJECT env var should be used when no arg provided."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        self._set_mock_roots(monkeypatch, side_effect=Exception("no roots"))
        monkeypatch.setenv("AI_GOVERNANCE_MCP_PROJECT", str(tmp_path))

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {}
        )
        assert result_path == tmp_path.resolve()
        assert used_fallback is False

    @pytest.mark.asyncio
    async def test_cwd_fallback_with_warning(self, tmp_path, monkeypatch):
        """CWD fallback should return the path with used_cwd_fallback=True when CWD has project markers."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        self._set_mock_roots(monkeypatch, side_effect=Exception("no roots"))
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {}
        )
        assert result_path == Path.cwd()
        assert used_fallback is True

    @pytest.mark.asyncio
    async def test_cwd_without_markers_returns_none(self, tmp_path, monkeypatch):
        """CWD without project markers should return (None, False)."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        self._set_mock_roots(monkeypatch, side_effect=Exception("no roots"))
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)
        monkeypatch.chdir(tmp_path)

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {}
        )
        assert result_path is None
        assert used_fallback is False

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_path(self, monkeypatch):
        """Non-existent project_path should return (None, False)."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        self._set_mock_roots(monkeypatch, side_effect=Exception("no roots"))
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {"project_path": "/nonexistent/path/abc123"}
        )
        assert result_path is None
        assert used_fallback is False

    @pytest.mark.asyncio
    async def test_explicit_path_wins_over_roots(self, tmp_path, monkeypatch):
        """Explicit project_path argument should win over MCP roots."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        # Set up roots pointing to a different directory
        roots_dir = tmp_path / "roots_dir"
        roots_dir.mkdir()
        mock_root = Mock()
        mock_root.uri = f"file://{roots_dir}"
        self._set_mock_roots(monkeypatch, roots=[mock_root])

        # Explicit project_path should win
        explicit_dir = tmp_path / "explicit_dir"
        explicit_dir.mkdir()

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {"project_path": str(explicit_dir)}
        )
        assert result_path == explicit_dir.resolve()
        assert result_path != roots_dir.resolve()
        assert used_fallback is False

    @pytest.mark.asyncio
    async def test_mcp_roots_used_when_no_explicit_path(self, tmp_path, monkeypatch):
        """MCP roots should be used when no explicit project_path is provided."""
        import ai_governance_mcp.server as server_module  # noqa: F811

        mock_root = Mock()
        mock_root.uri = f"file://{tmp_path}"
        self._set_mock_roots(monkeypatch, roots=[mock_root])

        monkeypatch.setenv("AI_GOVERNANCE_MCP_PROJECT", "/some/other/path")

        result_path, used_fallback = await server_module._resolve_caller_project_path(
            {}
        )
        assert result_path == tmp_path.resolve()
        assert used_fallback is False


class TestInstallAgentProjectPath:
    """Tests for install_agent with explicit project_path (cross-project scenario)."""

    def _set_no_roots(self, monkeypatch):
        """Set up mock MCP context with no roots support."""
        import ai_governance_mcp.server as server_module
        from mcp.server.lowlevel.server import request_ctx

        server_module._cached_roots_path = None
        mock_session = Mock()
        mock_session.list_roots = Mock(side_effect=Exception("no roots"))
        mock_request_context = Mock()
        mock_request_context.session = mock_session
        request_ctx.set(mock_request_context)
        # ContextVar token is scoped to this test's async context

    @pytest.mark.asyncio
    async def test_install_uses_project_path_not_cwd(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent with project_path should write to that path, not CWD."""
        import ai_governance_mcp.server as server_module

        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        (project_dir / ".claude").mkdir()

        # CWD is NOT the project — this is the bug scenario
        server_cwd = tmp_path / "server_dir"
        server_cwd.mkdir()
        monkeypatch.chdir(server_cwd)

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {
                "agent_name": "orchestrator",
                "confirmed": True,
                "project_path": str(project_dir),
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "installed"

        # File must be in project_dir, NOT in server_cwd
        assert (project_dir / ".claude" / "agents" / "orchestrator.md").exists()
        assert not (server_cwd / ".claude" / "agents" / "orchestrator.md").exists()

    @pytest.mark.asyncio
    async def test_install_rejects_invalid_project_path(self, tmp_path, monkeypatch):
        """install_agent with invalid project_path should return error."""
        import ai_governance_mcp.server as server_module

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_install_agent(
            {
                "agent_name": "orchestrator",
                "project_path": "/nonexistent/path/abc123",
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_PROJECT_PATH"

    @pytest.mark.asyncio
    async def test_uninstall_uses_project_path(self, tmp_path, monkeypatch):
        """uninstall_agent with project_path should look in that path."""
        import ai_governance_mcp.server as server_module

        project_dir = tmp_path / "my_project"
        agent_dir = project_dir / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "orchestrator.md").write_text("# Test agent")

        server_cwd = tmp_path / "server_dir"
        server_cwd.mkdir()
        monkeypatch.chdir(server_cwd)

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_uninstall_agent(
            {
                "agent_name": "orchestrator",
                "confirmed": True,
                "project_path": str(project_dir),
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "uninstalled"
        assert not (agent_dir / "orchestrator.md").exists()

    @pytest.mark.asyncio
    async def test_install_cwd_fallback_includes_warning(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent with CWD fallback should include warning in response."""
        import ai_governance_mcp.server as server_module

        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude").mkdir()
        monkeypatch.chdir(tmp_path)

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator", "confirmed": True}
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "installed"
        assert "cwd_fallback_warning" in response


class TestClaudeCodeDetectionWithProjectPath:
    """Tests for _detect_claude_code_environment with explicit project_path."""

    def test_detect_claude_with_explicit_project_path(self, tmp_path):
        """Should detect Claude Code from project_path, not CWD."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        project = tmp_path / "project"
        project.mkdir()
        (project / ".claude").mkdir()

        # Don't chdir — pass project_path directly
        assert _detect_claude_code_environment(project) is True

    def test_detect_project_path_without_indicators(self, tmp_path):
        """Should return False when project_path has no Claude indicators."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        project = tmp_path / "plain_project"
        project.mkdir()

        assert _detect_claude_code_environment(project) is False

    def test_detect_claude_md_via_project_path(self, tmp_path):
        """Should detect CLAUDE.md via project_path."""
        from ai_governance_mcp.server import _detect_claude_code_environment

        project = tmp_path / "project"
        project.mkdir()
        (project / "CLAUDE.md").write_text("# Test")

        assert _detect_claude_code_environment(project) is True


# =============================================================================
# Security Feature Tests (H4, M1, M4, M6)
# =============================================================================


class TestRateLimiting:
    """Tests for H4: Rate limiting (token bucket algorithm)."""

    def test_rate_limit_allows_initial_requests(self):
        """Initial requests should be allowed (first N of token bucket).

        Covers: FM-RATE-LIMITER-BLOCKS-EXCESS
        """
        from ai_governance_mcp.server import _check_rate_limit

        # Reset rate limiter
        import ai_governance_mcp.server as server_module

        server_module._rate_limit_tokens = server_module.RATE_LIMIT_TOKENS

        assert _check_rate_limit() is True

    def test_rate_limit_exhaustion(self):
        """Rapid requests should eventually be rate limited (excess blocked).

        Covers: FM-RATE-LIMITER-BLOCKS-EXCESS
        """
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

        from ai_governance_mcp.config import _find_project_root

        project_root = _find_project_root().resolve()
        log_path = project_root / "logs" / "test.jsonl"

        # Should not raise
        _validate_log_path(log_path)

    def test_validate_log_path_accepts_cwd(self, tmp_path, monkeypatch):
        """Paths within CWD should be accepted (Docker /app scenario)."""
        from ai_governance_mcp.server import _validate_log_path

        # Simulate Docker: CWD is /app-like dir without pyproject.toml
        monkeypatch.chdir(tmp_path)
        log_path = tmp_path / "logs" / "governance_audit.jsonl"

        # Should not raise — CWD is an allowed directory
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

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        import ai_governance_mcp.server as server_module

        server_module._cached_roots_path = None
        yield
        server_module._cached_roots_path = None

    @pytest.mark.asyncio
    async def test_install_agent_content_differs_when_different(
        self, tmp_path, monkeypatch, real_settings
    ):
        """content_differs should be True when existing file has different content."""
        import ai_governance_mcp.server as server_module

        # Create Claude environment with existing agent file
        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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
        (tmp_path / ".git").mkdir()
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


# =============================================================================
# Governance Reminder CE Nudge Tests (Fix 3)
# =============================================================================


class TestGovernanceReminderCENudge:
    """Test that GOVERNANCE_REMINDER includes context engine nudge (Fix 3)."""

    def test_reminder_contains_ce_nudge(self):
        from ai_governance_mcp.server import GOVERNANCE_REMINDER

        assert "context engine" in GOVERNANCE_REMINDER.lower()
        assert "existing patterns" in GOVERNANCE_REMINDER.lower()

    def test_reminder_retains_governance_check(self):
        from ai_governance_mcp.server import GOVERNANCE_REMINDER

        assert "evaluate_governance()" in GOVERNANCE_REMINDER
        assert "S-Series = veto" in GOVERNANCE_REMINDER


# =============================================================================
# Required Actions CE Cross-Reference Tests (Fix 5)
# =============================================================================


class TestRequiredActionsCEReference:
    """Test that SERVER_INSTRUCTIONS includes CE cross-reference in Required Actions (Fix 5)."""

    def test_required_actions_contains_query_project(self):
        from ai_governance_mcp.server import SERVER_INSTRUCTIONS

        assert "query_project" in SERVER_INSTRUCTIONS
        assert "Context Engine MCP" in SERVER_INSTRUCTIONS

    def test_required_actions_has_five_items(self):
        from ai_governance_mcp.server import SERVER_INSTRUCTIONS

        # Slimmed to 5 items (removed project initialization as separate item)
        assert "5. **Query project context**" in SERVER_INSTRUCTIONS


# =============================================================================
# Multi-Agent Support Tests
# =============================================================================


class TestMultiAgentConsistency:
    """Tests for multi-agent installation support.

    Verifies that all 10 agents have consistent configuration:
    template files, hashes, metadata, and proper tool schema coverage.
    """

    def test_all_agents_have_template_files(self):
        """Every agent in AVAILABLE_AGENTS must have a template in documents/agents/."""
        from ai_governance_mcp.server import AVAILABLE_AGENTS

        project_root = Path(__file__).parent.parent
        agents_dir = project_root / "documents" / "agents"

        for agent_name in AVAILABLE_AGENTS:
            template = agents_dir / f"{agent_name}.md"
            assert template.exists(), f"Missing template for '{agent_name}': {template}"
            content = template.read_text()
            assert len(content) > 100, f"Template for '{agent_name}' seems empty"

    def test_all_agents_have_hashes(self):
        """Every agent in AVAILABLE_AGENTS must have a hash in AGENT_TEMPLATE_HASHES."""
        from ai_governance_mcp.server import AGENT_TEMPLATE_HASHES, AVAILABLE_AGENTS

        for agent_name in AVAILABLE_AGENTS:
            assert agent_name in AGENT_TEMPLATE_HASHES, (
                f"Missing hash for '{agent_name}' in AGENT_TEMPLATE_HASHES"
            )
            assert len(AGENT_TEMPLATE_HASHES[agent_name]) == 64, (
                f"Hash for '{agent_name}' is not a valid SHA-256 hex digest"
            )

    def test_all_agents_have_metadata(self):
        """Every agent in AVAILABLE_AGENTS must have metadata in AGENT_METADATA."""
        from ai_governance_mcp.server import AGENT_METADATA, AVAILABLE_AGENTS

        required_keys = {"short_description", "action_summary", "activation_message"}

        for agent_name in AVAILABLE_AGENTS:
            assert agent_name in AGENT_METADATA, (
                f"Missing metadata for '{agent_name}' in AGENT_METADATA"
            )
            for key in required_keys:
                assert key in AGENT_METADATA[agent_name], (
                    f"Missing '{key}' in AGENT_METADATA['{agent_name}']"
                )
                assert len(AGENT_METADATA[agent_name][key]) > 0, (
                    f"Empty '{key}' in AGENT_METADATA['{agent_name}']"
                )

    def test_available_agents_count(self):
        """There should be exactly 10 available agents."""
        from ai_governance_mcp.server import AVAILABLE_AGENTS

        assert len(AVAILABLE_AGENTS) == 10

    def test_template_hashes_match_files(self):
        """Stored hashes must match actual file content."""
        import hashlib

        from ai_governance_mcp.server import AGENT_TEMPLATE_HASHES, AVAILABLE_AGENTS

        project_root = Path(__file__).parent.parent
        agents_dir = project_root / "documents" / "agents"

        for agent_name in AVAILABLE_AGENTS:
            template = agents_dir / f"{agent_name}.md"
            if template.exists():
                content = template.read_text()
                actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                assert actual_hash == AGENT_TEMPLATE_HASHES[agent_name], (
                    f"Hash mismatch for '{agent_name}': "
                    f"expected {AGENT_TEMPLATE_HASHES[agent_name]}, got {actual_hash}"
                )

    def test_no_extra_hashes_without_agents(self):
        """AGENT_TEMPLATE_HASHES should not have entries for non-existent agents."""
        from ai_governance_mcp.server import AGENT_TEMPLATE_HASHES, AVAILABLE_AGENTS

        for agent_name in AGENT_TEMPLATE_HASHES:
            assert agent_name in AVAILABLE_AGENTS, (
                f"Hash exists for '{agent_name}' but it's not in AVAILABLE_AGENTS"
            )

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        import ai_governance_mcp.server as server_module

        server_module._cached_roots_path = None
        yield
        server_module._cached_roots_path = None

    @pytest.mark.asyncio
    async def test_non_claude_response_includes_agent_content(
        self, tmp_path, monkeypatch, real_settings
    ):
        """Non-Claude install_agent response should include agent definition content."""
        import ai_governance_mcp.server as server_module

        # No .claude dir → non-Claude environment
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        # But need settings so template path resolves
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "code-reviewer"}
        )

        assert len(result) == 1
        response = json.loads(extract_json_from_response(result[0].text))
        assert response["status"] == "not_applicable"
        assert response["agent_name"] == "code-reviewer"
        assert "agent_content" in response
        assert "Code Reviewer" in response["agent_content"]
        assert "adaptation_guidance" in response

    @pytest.mark.asyncio
    async def test_install_preview_works_for_non_orchestrator(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent preview should work for agents other than orchestrator."""
        import ai_governance_mcp.server as server_module

        (tmp_path / ".git").mkdir()
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "security-auditor"}
        )

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["agent_name"] == "security-auditor"
        assert (
            "OWASP" in response["action_summary"]
            or "vulnerability" in response["action_summary"].lower()
        )
        assert "explanation" in response

    @pytest.mark.asyncio
    async def test_install_confirmed_creates_non_orchestrator_file(
        self, tmp_path, monkeypatch, real_settings
    ):
        """install_agent confirmed should create files for non-orchestrator agents."""
        import ai_governance_mcp.server as server_module

        (tmp_path / ".git").mkdir()
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(server_module, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "code-reviewer", "confirmed": True}
        )

        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "installed"

        agent_file = tmp_path / ".claude" / "agents" / "code-reviewer.md"
        assert agent_file.exists()
        content = agent_file.read_text()
        assert "Code Reviewer" in content

    @pytest.mark.asyncio
    async def test_tool_schema_lists_all_agents(self):
        """install_agent and uninstall_agent tool schemas should list all agents."""
        from ai_governance_mcp.server import AVAILABLE_AGENTS, list_tools

        tools = await list_tools()
        install_tool = next(t for t in tools if t.name == "install_agent")
        uninstall_tool = next(t for t in tools if t.name == "uninstall_agent")

        install_enum = install_tool.inputSchema["properties"]["agent_name"]["enum"]
        uninstall_enum = uninstall_tool.inputSchema["properties"]["agent_name"]["enum"]

        assert set(install_enum) == AVAILABLE_AGENTS
        assert set(uninstall_enum) == AVAILABLE_AGENTS

    def test_agent_templates_synced_with_local(self):
        """documents/agents/ (canonical source) must match .claude/agents/ (local install).

        Two directories serve different purposes:
        - documents/agents/: Canonical distribution templates. The install_agent
          MCP tool reads from here. Indexed by Context Engine. Ships with package.
        - .claude/agents/: Local installation for Claude Code to use in this project.

        Both must stay in sync. Edit documents/agents/ first, then copy to .claude/agents/.
        """
        from ai_governance_mcp.server import AVAILABLE_AGENTS

        project_root = Path(__file__).parent.parent
        canonical_dir = project_root / "documents" / "agents"
        local_dir = project_root / ".claude" / "agents"

        assert canonical_dir.is_dir(), f"Canonical agents dir missing: {canonical_dir}"
        assert local_dir.is_dir(), f"Local agents dir missing: {local_dir}"

        drifted = []
        missing_local = []

        for agent_name in AVAILABLE_AGENTS:
            canonical = canonical_dir / f"{agent_name}.md"
            local = local_dir / f"{agent_name}.md"

            if not canonical.exists():
                continue  # Covered by test_all_agents_have_template_files

            if not local.exists():
                missing_local.append(agent_name)
                continue

            canonical_content = canonical.read_text()
            local_content = local.read_text()

            if canonical_content != local_content:
                drifted.append(agent_name)

        assert not missing_local, (
            f"Agents in documents/agents/ but missing from .claude/agents/: "
            f"{missing_local}. Copy from documents/agents/ (canonical source)."
        )
        assert not drifted, (
            f"Agent templates have drifted between documents/agents/ (canonical) "
            f"and .claude/agents/ (local): {drifted}. "
            f"Edit documents/agents/ first, then copy to .claude/agents/."
        )


# =============================================================================
# Universal Floor (Tier 1) Tests
# =============================================================================


class TestTiersConfig:
    """Tests for tiers.json loading and universal floor building."""

    def test_load_tiers_config_from_documents(self, reset_server_state, test_settings):
        """Should load tiers.json from documents directory."""
        import ai_governance_mcp.server as srv

        # Write a minimal tiers.json
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Are you honest?",
                            }
                        ],
                        "methods": [],
                    }
                }
            )
        )

        srv._settings = test_settings
        srv._tiers_config = None  # Reset cache

        config = srv._load_tiers_config()
        assert config is not None
        assert "universal_floor" in config
        assert len(config["universal_floor"]["principles"]) == 1

    def test_load_tiers_config_missing_file(self, reset_server_state, test_settings):
        """Should return None when tiers.json doesn't exist."""
        import ai_governance_mcp.server as srv

        srv._settings = test_settings
        srv._tiers_config = None

        config = srv._load_tiers_config()
        assert config is None

    def test_load_tiers_config_caches(self, reset_server_state, test_settings):
        """Should cache config after first load."""
        import ai_governance_mcp.server as srv

        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(json.dumps({"universal_floor": {"principles": []}}))

        srv._settings = test_settings
        srv._tiers_config = None

        config1 = srv._load_tiers_config()
        config2 = srv._load_tiers_config()
        assert config1 is config2  # Same object (cached)

    def test_load_tiers_config_invalid_json(self, reset_server_state, test_settings):
        """Should return None for invalid JSON."""
        import ai_governance_mcp.server as srv

        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text("not valid json{{{")

        srv._settings = test_settings
        srv._tiers_config = None

        config = srv._load_tiers_config()
        assert config is None

    def test_build_universal_floor_all_types(self):
        """Should build items for principles, methods, and subagent check."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "test-principle", "check": "Did you check?"}],
                "methods": [{"ref": "§7.8", "id": None, "check": "Proportional?"}],
                "subagent_check": {"check": "Would a subagent help?"},
            }
        }
        items = _build_universal_floor(config)

        assert len(items) == 3
        assert items[0]["type"] == "principle"
        assert items[0]["id"] == "test-principle"
        assert items[1]["type"] == "method"
        assert items[1]["ref"] == "§7.8"
        assert items[2]["type"] == "subagent_check"

    def test_build_universal_floor_empty_config(self):
        """Should return empty list for empty config."""
        from ai_governance_mcp.server import _build_universal_floor

        items = _build_universal_floor({})
        assert items == []

    def test_build_universal_floor_no_subagent(self):
        """Should work without subagent_check."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
            }
        }
        items = _build_universal_floor(config)
        assert len(items) == 1
        assert items[0]["type"] == "principle"

    def test_build_universal_floor_includes_behavioral(self):
        """Should include behavioral_floor directives with type 'behavioral'."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
            },
            "behavioral_floor": {
                "directives": [
                    {"id": "recommend-not-ask", "check": "Presenting recommendations?"},
                    {"id": "freeform-dialogue", "check": "Using natural dialogue?"},
                ]
            },
        }
        items = _build_universal_floor(config)
        assert len(items) == 3  # 1 principle + 2 behavioral
        behavioral = [i for i in items if i["type"] == "behavioral"]
        assert len(behavioral) == 2
        assert behavioral[0]["id"] == "recommend-not-ask"
        assert behavioral[1]["id"] == "freeform-dialogue"

    def test_build_universal_floor_no_behavioral(self):
        """Should work without behavioral_floor section (backward compatible)."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
                "subagent_check": {"check": "Would a subagent help?"},
            }
        }
        items = _build_universal_floor(config)
        assert len(items) == 2  # principle + subagent_check
        types = {i["type"] for i in items}
        assert "behavioral" not in types

    def test_build_universal_floor_empty_behavioral(self):
        """Should handle empty behavioral_floor directives list."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {"principles": [], "methods": []},
            "behavioral_floor": {"directives": []},
        }
        items = _build_universal_floor(config)
        assert items == []


class TestUniversalFloorInEvaluateGovernance:
    """Tests for universal floor injection in evaluate_governance responses."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_universal_floor(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include universal_floor when tiers.json exists."""
        # Write tiers.json to test documents dir
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Epistemic check",
                            }
                        ],
                        "methods": [
                            {"ref": "§7.8", "id": None, "check": "Proportional check"}
                        ],
                        "subagent_check": {"check": "Subagent check"},
                    }
                }
            )
        )

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
                        {"planned_action": "Add a new helper function"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    floor = parsed["universal_floor"]
                    assert len(floor) == 3
                    assert floor[0]["type"] == "principle"
                    assert floor[0]["check"] == "Epistemic check"
                    assert floor[1]["type"] == "method"
                    assert floor[2]["type"] == "subagent_check"

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_floor_without_tiers(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should not include universal_floor when tiers.json missing."""
        # No tiers.json written — should gracefully omit
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
                        {"planned_action": "Format code with prettier"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" not in parsed

    @pytest.mark.asyncio
    async def test_universal_floor_separate_from_max_results(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Universal floor items should NOT reduce the max_results=10 retrieval count."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {"id": "floor-p1", "check": "check1"},
                            {"id": "floor-p2", "check": "check2"},
                        ],
                        "methods": [],
                    }
                }
            )
        )

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
                        {"planned_action": "Refactor database module"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Floor items are separate
                    if "universal_floor" in parsed:
                        assert len(parsed["universal_floor"]) == 2

                    # relevant_principles still has up to 10
                    # (won't be reduced by floor items)
                    assert "relevant_principles" in parsed


class TestTiersPrincipleIdValidation:
    """CI validation: all principle IDs in tiers.json must exist in the index."""

    def test_tiers_principle_ids_exist_in_index(self):
        """Every principle ID in tiers.json must exist in the production index."""
        tiers_path = Path(__file__).parent.parent / "documents" / "tiers.json"
        index_path = Path(__file__).parent.parent / "index" / "global_index.json"

        if not tiers_path.exists():
            pytest.skip("tiers.json not found")
        if not index_path.exists():
            pytest.skip("Production index not found")

        with open(tiers_path) as f:
            tiers = json.load(f)
        with open(index_path) as f:
            index = json.load(f)

        # Collect all principle IDs from index
        all_ids = set()
        for domain_data in index.get("domains", {}).values():
            for p in domain_data.get("principles", []):
                all_ids.add(p["id"])

        # Validate tier principle IDs
        floor = tiers.get("universal_floor", {})
        missing = []
        for p in floor.get("principles", []):
            pid = p.get("id")
            if pid and pid not in all_ids:
                missing.append(pid)

        # Also validate method IDs that reference principles
        for m in floor.get("methods", []):
            mid = m.get("id")
            if mid and mid not in all_ids:
                missing.append(mid)

        assert not missing, (
            f"tiers.json references IDs not in index: {missing}. "
            f"Update tiers.json or rebuild index."
        )


# =============================================================================
# UI/UX Domain Integration Tests
# =============================================================================


class TestUiUxDomainIntegration:
    """Tests for UI/UX domain integration in server."""

    @pytest.mark.asyncio
    async def test_get_domain_summary_accepts_ui_ux(self, reset_server_state):
        """get_domain_summary should accept 'ui-ux' as a valid domain."""
        from ai_governance_mcp.server import _handle_get_domain_summary

        mock_summary = {
            "name": "ui-ux",
            "display_name": "UI/UX",
            "description": "Interactive software interfaces",
            "principles_count": 20,
            "methods_count": 0,
        }
        mock_engine = Mock()
        mock_engine.get_domain_summary.return_value = mock_summary

        result = await _handle_get_domain_summary(mock_engine, {"domain": "ui-ux"})

        assert len(result) == 1
        assert "ui-ux" in result[0].text or "UI/UX" in result[0].text

    @pytest.mark.asyncio
    async def test_query_governance_rejects_invalid_domain(self, reset_server_state):
        """query_governance should reject invalid domains but accept ui-ux."""
        from ai_governance_mcp.server import _handle_query_governance

        mock_engine = Mock()

        # Invalid domain should return error
        result = await _handle_query_governance(
            mock_engine,
            {"query": "test", "domain": "not-a-domain"},
        )
        assert "Error: Invalid domain" in result[0].text

        # ui-ux should NOT return an invalid domain error
        # (it will proceed past validation and call engine.retrieve, which is fine)
        mock_engine.retrieve.side_effect = Exception("past validation")
        try:
            await _handle_query_governance(
                mock_engine,
                {"query": "visual hierarchy", "domain": "ui-ux"},
            )
        except Exception as e:
            # If we get past the validation to hit the mock, that proves ui-ux is valid
            assert "past validation" in str(e)

    @pytest.mark.asyncio
    async def test_ui_ux_in_tool_schema_enum(self, reset_server_state):
        """ui-ux should be in the get_domain_summary tool schema enum."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()
        domain_summary_tool = None
        for tool in tools:
            if tool.name == "get_domain_summary":
                domain_summary_tool = tool
                break

        assert domain_summary_tool is not None, "get_domain_summary tool not found"
        schema = domain_summary_tool.inputSchema
        domain_enum = schema["properties"]["domain"]["enum"]
        assert "ui-ux" in domain_enum, f"ui-ux not in domain enum: {domain_enum}"


# =============================================================================
# AO-Series Production Index Validation
# =============================================================================


class TestAoSeriesProductionIndex:
    """Validate AO-Series principles exist in the production index."""

    def test_ao_series_principles_in_index(self):
        """Production index should contain AO-Series principles with correct series codes."""
        index_path = Path(__file__).parent.parent / "index" / "global_index.json"
        if not index_path.exists():
            pytest.skip("Production index not found")

        with open(index_path) as f:
            index = json.load(f)

        multi_agent = index.get("domains", {}).get("multi-agent", {})
        principles = multi_agent.get("principles", [])

        ao_principles = [p for p in principles if p.get("series_code") == "AO"]
        assert len(ao_principles) == 4, (
            f"Expected 4 AO-Series principles, got {len(ao_principles)}"
        )

        # Verify they have correct autonomous category
        for p in ao_principles:
            assert "autonomous" in p["id"], (
                f"AO principle ID should contain 'autonomous': {p['id']}"
            )


class TestScaffoldProject:
    """Tests for scaffold_project tool."""

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        import ai_governance_mcp.server as server_module

        server_module._cached_roots_path = None
        yield
        server_module._cached_roots_path = None

    @pytest.mark.asyncio
    async def test_preview_code_core(self, tmp_path, monkeypatch):
        """Preview mode for code/core should return 4-file manifest."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_name": "test-project",
                "project_type": "code",
                "kit_tier": "core",
            }
        )
        assert len(result) == 1
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["files_to_create"] == 4
        paths = [f["path"] for f in response["files"]]
        assert "SESSION-STATE.md" in paths
        assert "PROJECT-MEMORY.md" in paths
        assert "LEARNING-LOG.md" in paths
        assert "AGENTS.md" in paths

    @pytest.mark.asyncio
    async def test_preview_code_standard(self, tmp_path, monkeypatch):
        """Preview mode for code/standard should return 9-file manifest.

        Standard tier = 4 core + 5 extras (CLAUDE + ARCHITECTURE + SPECIFICATION
        + workflows/COMPLETION-CHECKLIST + BACKLOG). See server.py
        SCAFFOLD_STANDARD_EXTRAS comment for sync to
        title-10-ai-coding-cfr.md §1.5.2.
        """
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_type": "code",
                "kit_tier": "standard",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["files_to_create"] == 9
        paths = [f["path"] for f in response["files"]]
        assert "CLAUDE.md" in paths
        assert "ARCHITECTURE.md" in paths
        assert "SPECIFICATION.md" in paths
        assert "workflows/COMPLETION-CHECKLIST.md" in paths
        assert "BACKLOG.md" in paths

    @pytest.mark.asyncio
    async def test_preview_document_core(self, tmp_path, monkeypatch):
        """Preview for document/core should use _ai-context/ paths."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_type": "document",
                "kit_tier": "core",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["files_to_create"] == 4
        paths = [f["path"] for f in response["files"]]
        assert all("_ai-context/" in p for p in paths)

    @pytest.mark.asyncio
    async def test_confirmed_creates_files(self, tmp_path, monkeypatch):
        """Confirmed mode should create all core files."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_name": "my-project",
                "project_type": "code",
                "kit_tier": "core",
                "confirmed": True,
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "scaffolded"
        assert len(response["files_created"]) == 4
        # Verify files exist on disk
        assert (tmp_path / "SESSION-STATE.md").is_file()
        assert (tmp_path / "PROJECT-MEMORY.md").is_file()
        assert (tmp_path / "LEARNING-LOG.md").is_file()
        assert (tmp_path / "AGENTS.md").is_file()
        # Verify content has project name
        content = (tmp_path / "SESSION-STATE.md").read_text()
        assert "my-project" in content

    @pytest.mark.asyncio
    async def test_skips_existing_files(self, tmp_path, monkeypatch):
        """Confirmed mode should skip files that already exist."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        # Pre-create one file
        (tmp_path / "SESSION-STATE.md").write_text("existing content")

        result = await _handle_scaffold_project(
            {
                "project_type": "code",
                "kit_tier": "core",
                "confirmed": True,
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "scaffolded"
        assert len(response["files_created"]) == 3
        assert len(response["files_skipped"]) == 1
        # Original content preserved
        assert (tmp_path / "SESSION-STATE.md").read_text() == "existing content"

    @pytest.mark.asyncio
    async def test_all_files_exist_warning(self, tmp_path, monkeypatch):
        """Preview should warn when all files already exist."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        for name in [
            "SESSION-STATE.md",
            "PROJECT-MEMORY.md",
            "LEARNING-LOG.md",
            "AGENTS.md",
        ]:
            (tmp_path / name).write_text("exists")

        result = await _handle_scaffold_project(
            {
                "project_type": "code",
                "kit_tier": "core",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["files_to_create"] == 0
        assert "warning" in response

    @pytest.mark.asyncio
    async def test_invalid_project_type(self, tmp_path, monkeypatch):
        """Invalid project_type should return error."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project({"project_type": "invalid"})
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_PROJECT_TYPE"

    @pytest.mark.asyncio
    async def test_invalid_kit_tier(self, tmp_path, monkeypatch):
        """Invalid kit_tier should return error."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project({"kit_tier": "premium"})
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_KIT_TIER"

    @pytest.mark.asyncio
    async def test_default_project_name(self, tmp_path, monkeypatch):
        """Omitting project_name should use CWD name."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_type": "code",
                "kit_tier": "core",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["project_name"] == tmp_path.name

    @pytest.mark.asyncio
    async def test_document_creates_ai_context_dir(self, tmp_path, monkeypatch):
        """Document type should create _ai-context/ directory."""
        from ai_governance_mcp.server import _handle_scaffold_project

        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        result = await _handle_scaffold_project(
            {
                "project_type": "document",
                "kit_tier": "core",
                "confirmed": True,
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "scaffolded"
        assert (tmp_path / "_ai-context").is_dir()
        assert (tmp_path / "_ai-context" / "SESSION-STATE.md").is_file()
        assert (tmp_path / "_ai-context" / "README.md").is_file()


class TestScaffoldProjectPath:
    """Tests for scaffold_project with explicit project_path (cross-project scenario)."""

    def _set_no_roots(self, monkeypatch):
        """Set up mock MCP context with no roots support."""
        import ai_governance_mcp.server as server_module
        from mcp.server.lowlevel.server import request_ctx

        server_module._cached_roots_path = None
        mock_session = Mock()
        mock_session.list_roots = Mock(side_effect=Exception("no roots"))
        mock_request_context = Mock()
        mock_request_context.session = mock_session
        request_ctx.set(mock_request_context)

    @pytest.mark.asyncio
    async def test_scaffold_uses_project_path_not_cwd(self, tmp_path, monkeypatch):
        """scaffold_project with project_path should create files there, not CWD."""
        import ai_governance_mcp.server as server_module

        project_dir = tmp_path / "my_project"
        project_dir.mkdir()

        server_cwd = tmp_path / "server_dir"
        server_cwd.mkdir()
        monkeypatch.chdir(server_cwd)

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_scaffold_project(
            {
                "project_name": "test-project",
                "confirmed": True,
                "project_path": str(project_dir),
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "scaffolded"

        # Files must be in project_dir, NOT in server_cwd
        assert (project_dir / "SESSION-STATE.md").exists()
        assert not (server_cwd / "SESSION-STATE.md").exists()

    @pytest.mark.asyncio
    async def test_scaffold_default_name_from_project_path(self, tmp_path, monkeypatch):
        """scaffold_project should use project_path name as default, not CWD name."""
        import ai_governance_mcp.server as server_module

        project_dir = tmp_path / "cool-project"
        project_dir.mkdir()

        server_cwd = tmp_path / "server_dir"
        server_cwd.mkdir()
        monkeypatch.chdir(server_cwd)

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_scaffold_project(
            {
                "confirmed": True,
                "project_path": str(project_dir),
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["project_name"] == "cool-project"
        assert response["project_name"] != "server_dir"

    @pytest.mark.asyncio
    async def test_scaffold_rejects_invalid_project_path(self, tmp_path, monkeypatch):
        """scaffold_project with invalid project_path should return error."""
        import ai_governance_mcp.server as server_module

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_scaffold_project(
            {
                "project_path": "/nonexistent/path/abc123",
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_PROJECT_PATH"

    @pytest.mark.asyncio
    async def test_scaffold_show_manual_returns_content(self, tmp_path, monkeypatch):
        """show_manual=true should return file contents without writing."""
        import ai_governance_mcp.server as server_module

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)
        monkeypatch.chdir(tmp_path)

        result = await server_module._handle_scaffold_project(
            {
                "project_name": "test-manual",
                "project_type": "document",
                "kit_tier": "core",
                "show_manual": True,
            }
        )

        # show_manual content contains markdown --- separators in file content,
        # so find the JSON object boundary instead of splitting on ---
        text = result[0].text
        json_end = text.rfind("}") + 1
        response = json.loads(text[:json_end])
        assert response["status"] == "manual_instructions"
        assert response["project_name"] == "test-manual"
        assert len(response["files"]) == 4
        # Verify each file has path and content
        for f in response["files"]:
            assert "path" in f
            assert "content" in f
            assert f["content"]  # Non-empty
        # Verify no files were written to disk
        assert not (tmp_path / "_ai-context").exists()

    @pytest.mark.asyncio
    async def test_scaffold_show_manual_works_without_valid_path(self, monkeypatch):
        """show_manual should work even when project_path is invalid."""
        import ai_governance_mcp.server as server_module

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_scaffold_project(
            {
                "project_name": "sandbox-project",
                "project_path": "/nonexistent/sandbox/path",
                "project_type": "document",
                "kit_tier": "core",
                "show_manual": True,
            }
        )

        text = result[0].text
        json_end = text.rfind("}") + 1
        response = json.loads(text[:json_end])
        assert response["status"] == "manual_instructions"
        assert response["project_name"] == "sandbox-project"
        assert len(response["files"]) == 4

    @pytest.mark.asyncio
    async def test_scaffold_invalid_path_suggests_show_manual(self, monkeypatch):
        """Invalid project_path error should suggest show_manual."""
        import ai_governance_mcp.server as server_module

        self._set_no_roots(monkeypatch)
        monkeypatch.delenv("AI_GOVERNANCE_MCP_PROJECT", raising=False)

        result = await server_module._handle_scaffold_project(
            {
                "project_path": "/nonexistent/sandbox/path",
            }
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_PROJECT_PATH"
        assert any("show_manual" in s for s in response["suggestions"])


class TestCaptureReference:
    """Tests for capture_reference tool."""

    @pytest.mark.asyncio
    async def test_capture_direct_entry(self, tmp_path, monkeypatch):
        """Should create a reference library entry file."""
        from ai_governance_mcp.server import _handle_capture_reference

        monkeypatch.chdir(tmp_path)
        # Create marker so _find_project_root() resolves to tmp_path
        (tmp_path / "documents").mkdir()
        (tmp_path / "documents" / "domains.json").write_text("{}")
        result = await _handle_capture_reference(
            {
                "id": "ref-ai-coding-test-pattern",
                "title": "Test Pattern",
                "domain": "ai-coding",
                "tags": ["testing", "patterns"],
                "entry_type": "direct",
                "artifact": "```python\ndef test_example(): pass\n```",
                "summary": "A test pattern example",
                "context": "When writing tests",
                "lessons": "Keep it simple",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "captured"
        assert response["entry_id"] == "ref-ai-coding-test-pattern"

        # Verify file exists
        entry_file = (
            tmp_path
            / "reference-library"
            / "ai-coding"
            / "ref-ai-coding-test-pattern.md"
        )
        assert entry_file.is_file()
        content = entry_file.read_text()
        assert "Test Pattern" in content
        assert "testing" in content
        assert "def test_example" in content

    @pytest.mark.asyncio
    async def test_capture_reference_entry(self, tmp_path, monkeypatch):
        """Should create a reference entry with external fields."""
        from ai_governance_mcp.server import _handle_capture_reference

        monkeypatch.chdir(tmp_path)
        (tmp_path / "documents").mkdir(exist_ok=True)
        (tmp_path / "documents" / "domains.json").write_text("{}")
        result = await _handle_capture_reference(
            {
                "id": "ref-ai-coding-external-guide",
                "title": "External Guide",
                "domain": "ai-coding",
                "tags": ["guide"],
                "entry_type": "reference",
                "artifact": "Summary of the external resource",
                "external_url": "https://example.com/guide",
                "external_author": "Jane Doe",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "captured"
        assert response["entry_type"] == "reference"

        content = (
            tmp_path
            / "reference-library"
            / "ai-coding"
            / "ref-ai-coding-external-guide.md"
        ).read_text()
        assert "external_url" in content
        assert "Jane Doe" in content

    @pytest.mark.asyncio
    async def test_capture_rejects_existing(self, tmp_path, monkeypatch):
        """Should reject if entry already exists."""
        from ai_governance_mcp.server import _handle_capture_reference

        monkeypatch.chdir(tmp_path)
        (tmp_path / "documents").mkdir(exist_ok=True)
        (tmp_path / "documents" / "domains.json").write_text("{}")
        ref_dir = tmp_path / "reference-library" / "ai-coding"
        ref_dir.mkdir(parents=True)
        (ref_dir / "ref-ai-coding-existing.md").write_text("existing")

        result = await _handle_capture_reference(
            {
                "id": "ref-ai-coding-existing",
                "title": "Existing",
                "domain": "ai-coding",
                "tags": ["test"],
                "entry_type": "direct",
                "artifact": "content",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "ENTRY_EXISTS"

    @pytest.mark.asyncio
    async def test_capture_rejects_invalid_id(self, tmp_path, monkeypatch):
        """Should reject IDs not matching ref- prefix pattern."""
        from ai_governance_mcp.server import _handle_capture_reference

        monkeypatch.chdir(tmp_path)
        (tmp_path / "documents").mkdir(exist_ok=True)
        (tmp_path / "documents" / "domains.json").write_text("{}")
        result = await _handle_capture_reference(
            {
                "id": "bad-id-no-ref-prefix",
                "title": "Bad",
                "domain": "ai-coding",
                "tags": ["test"],
                "entry_type": "direct",
                "artifact": "content",
            }
        )
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "INVALID_ID_FORMAT"

    @pytest.mark.asyncio
    async def test_capture_rejects_missing_fields(self, tmp_path, monkeypatch):
        """Should reject when required fields are missing."""
        from ai_governance_mcp.server import _handle_capture_reference

        monkeypatch.chdir(tmp_path)
        (tmp_path / "documents").mkdir(exist_ok=True)
        (tmp_path / "documents" / "domains.json").write_text("{}")
        result = await _handle_capture_reference({"id": "ref-test"})
        response = json.loads(result[0].text.split("---")[0])
        assert response["error_code"] == "MISSING_REQUIRED_FIELDS"


class TestAutoLogGovernanceReasoning:
    """Tests for automatic reasoning logging in evaluate_governance."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_auto_logs_reasoning(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should auto-log a reasoning entry."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new logging function"},
                    )

                    # Should have auto-logged a reasoning entry
                    assert len(server_module._reasoning_log) == 1
                    entry = server_module._reasoning_log[0]
                    assert entry.auto_generated is True
                    assert entry.final_decision in [
                        "PROCEED",
                        "PROCEED_WITH_MODIFICATIONS",
                        "ESCALATE",
                    ]
                    assert len(entry.reasoning_entries) >= 1

    @pytest.mark.asyncio
    async def test_auto_log_audit_id_matches(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Auto-logged reasoning should share audit_id with audit entry."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Test action for audit ID match"},
                    )

                    assert len(server_module._audit_log) == 1
                    assert len(server_module._reasoning_log) == 1
                    assert (
                        server_module._audit_log[0].audit_id
                        == server_module._reasoning_log[0].audit_id
                    )

    @pytest.mark.asyncio
    async def test_manual_log_still_works_after_auto_log(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Manual log_governance_reasoning should still work alongside auto-log."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

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
                        {"planned_action": "Test action for manual log"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))
                    audit_id = parsed["audit_id"]

                    # Auto-log should exist
                    assert len(server_module._reasoning_log) == 1
                    assert server_module._reasoning_log[0].auto_generated is True

                    # Manual log should also work
                    await call_tool(
                        "log_governance_reasoning",
                        {
                            "audit_id": audit_id,
                            "reasoning": [
                                {
                                    "principle_id": "test-principle",
                                    "status": "COMPLIES",
                                    "reasoning": "Manual detailed analysis",
                                }
                            ],
                            "final_decision": "PROCEED",
                        },
                    )

                    # Both entries should exist
                    assert len(server_module._reasoning_log) == 2
                    assert server_module._reasoning_log[0].auto_generated is True
                    assert server_module._reasoning_log[1].auto_generated is False


class TestCitePrinciplesInBehavioralFloor:
    """Tests for cite-principles directive in tiers.json behavioral_floor."""

    def test_cite_principles_in_tiers_json(self):
        """tiers.json should include cite-principles directive."""
        tiers_path = Path(__file__).parent.parent / "documents" / "tiers.json"
        with open(tiers_path) as f:
            config = json.load(f)

        directives = config["behavioral_floor"]["directives"]
        ids = [d["id"] for d in directives]
        assert "cite-principles" in ids

    def test_build_universal_floor_includes_cite_principles(self):
        """_build_universal_floor should include cite-principles behavioral directive."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {"principles": [], "methods": []},
            "behavioral_floor": {
                "directives": [
                    {"id": "recommend-not-ask", "check": "Presenting recommendations?"},
                    {"id": "freeform-dialogue", "check": "Using natural dialogue?"},
                    {"id": "cite-principles", "check": "Referencing principle IDs?"},
                ]
            },
        }
        items = _build_universal_floor(config)
        behavioral = [i for i in items if i["type"] == "behavioral"]
        assert len(behavioral) == 3
        assert behavioral[2]["id"] == "cite-principles"
