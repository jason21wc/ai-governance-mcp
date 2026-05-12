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

from helpers import extract_json_from_response

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

        server_module._state._settings = test_settings

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

        server_module._state._settings = test_settings

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

        server_module._state._settings = None

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
        server_module._state._settings = test_settings

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
        server_module._state._settings = test_settings

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
        server_module._state._settings = test_settings

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

        server_module._state._settings = test_settings

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

        server_module._state._settings = None

        # Should not raise
        log_feedback_entry(sample_feedback)


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
                        "ai_governance_mcp.server._app._handle_query_governance",
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


class TestGovernanceAuditLog:
    """Tests for governance audit logging functionality."""

    @pytest.fixture(autouse=True)
    def reset_audit_log(self):
        """Reset audit log before each test."""
        from ai_governance_mcp import server

        server._audit_log.clear()
        yield
        server._audit_log.clear()

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
                        AssessmentStatus.REVIEW,
                        AssessmentStatus.ESCALATE,
                    ]


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
    async def test_list_tools_returns_all(self):
        """list_tools should return all governance tools."""
        from ai_governance_mcp.server import list_tools

        tools = await list_tools()

        assert len(tools) == 16
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
        assert "search_references" in tool_names

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

        server_module._security._rate_limit_tokens = server_module.RATE_LIMIT_TOKENS

        assert _check_rate_limit() is True

    def test_rate_limit_exhaustion(self):
        """Rapid requests should eventually be rate limited (excess blocked).

        Covers: FM-RATE-LIMITER-BLOCKS-EXCESS
        """
        import ai_governance_mcp.server as server_module
        from ai_governance_mcp.server import _check_rate_limit

        # Exhaust the token bucket
        server_module._security._rate_limit_tokens = 1
        assert _check_rate_limit() is True  # Uses last token
        assert _check_rate_limit() is False  # No tokens left

        # Reset for other tests
        server_module._security._rate_limit_tokens = server_module.RATE_LIMIT_TOKENS


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
