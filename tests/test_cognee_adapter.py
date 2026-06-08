"""Tests for the CogneeAdapter — isolation boundary for Cognee KG interactions.

Covers:
- Availability detection (import probing)
- Configuration (storage paths, LLM/embedding provider setup, env vars)
- Add + Cognify operations (chunk feeding, KG construction)
- Search operations (query wrapping, SearchType mapping)
- Cleanup + storage coordination (data removal, existence checks)
"""

import asyncio
import importlib.util
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_HAS_KG_EXTRAS = importlib.util.find_spec("litellm") is not None
_skip_without_kg = pytest.mark.skipif(
    not _HAS_KG_EXTRAS,
    reason="knowledge-graph extras not installed (litellm required)",
)


# =============================================================================
# Availability Tests (Tasks 1-2)
# =============================================================================


class TestCogneeAvailability:
    """CogneeAdapter availability detection via import probing."""

    def test_is_available_true_when_cognee_importable(self):
        with patch("importlib.import_module") as mock_import:
            mock_import.return_value = MagicMock()
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            assert CogneeAdapter.is_available() is True

    def test_is_available_false_when_import_error(self):
        with patch("importlib.import_module", side_effect=ImportError("no cognee")):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            assert CogneeAdapter.is_available() is False

    def test_constructor_stores_project_index_path(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=True,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            adapter = CogneeAdapter(project_index_path=tmp_path)
            assert adapter._project_index_path == tmp_path
            assert adapter._cognee_data_path == tmp_path / "cognee"

    def test_constructor_raises_when_unavailable(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=False,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            with pytest.raises(ImportError, match="cognee"):
                CogneeAdapter(project_index_path=tmp_path)


# =============================================================================
# Configuration Tests (Tasks 3-4)
# =============================================================================


_COGNEE_ENV_VARS = [
    "AI_CONTEXT_ENGINE_COGNEE_LLM_PROVIDER",
    "AI_CONTEXT_ENGINE_COGNEE_LLM_MODEL",
    "AI_CONTEXT_ENGINE_COGNEE_LLM_API_KEY",
    "AI_CONTEXT_ENGINE_COGNEE_LLM_ENDPOINT",
    "AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE",
    "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_PROVIDER",
    "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_MODEL",
    "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS",
    "AI_CONTEXT_ENGINE_EMBEDDING_MODEL",
    "AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS",
]


@_skip_without_kg
class TestCogneeConfiguration:
    """CogneeAdapter.configure() sets up Cognee storage and LLM/embedding."""

    @pytest.fixture(autouse=True)
    def _clean_env(self):
        saved = {k: os.environ.pop(k, None) for k in _COGNEE_ENV_VARS}
        yield
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    @pytest.fixture()
    def adapter(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=True,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            return CogneeAdapter(project_index_path=tmp_path)

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_sets_storage_path(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.system_root_directory.assert_called_once_with(
                str(adapter._cognee_data_path)
            )

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_sets_data_root_directory(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.data_root_directory.assert_called_once_with(
                str(adapter._cognee_data_path / "data")
            )

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_defaults_to_ollama_provider(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_provider.assert_called_once()
            call_args = mock_config.set_llm_provider.call_args
            assert call_args[0][0] == "ollama"

    @patch.dict(
        os.environ,
        {
            "AI_CONTEXT_ENGINE_COGNEE_LLM_PROVIDER": "anthropic",
            "AI_CONTEXT_ENGINE_COGNEE_LLM_API_KEY": "sk-test",
        },
        clear=False,
    )
    def test_configure_reads_provider_from_env(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            call_args = mock_config.set_llm_provider.call_args
            assert call_args[0][0] == "anthropic"

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_LLM_PROVIDER": "anthropic"},
        clear=False,
    )
    def test_configure_raises_without_api_key_for_cloud_provider(self, adapter):
        mock_config = MagicMock()
        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
                return_value=mock_config,
            ),
            pytest.raises(ValueError, match="API key"),
        ):
            adapter.configure()

    @patch.dict(
        os.environ,
        {
            "AI_CONTEXT_ENGINE_COGNEE_LLM_PROVIDER": "anthropic",
            "AI_CONTEXT_ENGINE_COGNEE_LLM_API_KEY": "sk-test-key",
        },
        clear=False,
    )
    def test_configure_accepts_cloud_provider_with_api_key(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_provider.assert_called_once()

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_sets_fastembed_embedding(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_provider.assert_called_once_with("fastembed")
            mock_config.set_embedding_model.assert_called_once_with(
                "BAAI/bge-small-en-v1.5"
            )
            mock_config.set_embedding_dimensions.assert_called_once_with(384)

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_sets_env_vars_for_cognee(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            assert os.environ.get("ENABLE_BACKEND_ACCESS_CONTROL") == "false"
            assert os.environ.get("COGNEE_SKIP_CONNECTION_TEST") == "true"

    # --- LLM endpoint ---

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_LLM_ENDPOINT": "http://localhost:11434"},
        clear=False,
    )
    def test_configure_reads_llm_endpoint_from_env(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_endpoint.assert_called_once_with(
                "http://localhost:11434"
            )

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_skips_endpoint_when_unset(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_endpoint.assert_not_called()

    # --- LLM temperature ---

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE": "0.1"},
        clear=False,
    )
    def test_configure_reads_temperature_from_env(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_config.assert_called_once_with({"llm_temperature": 0.1})

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE": "hot"},
        clear=False,
    )
    def test_configure_rejects_invalid_temperature(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_llm_config.assert_not_called()

    def test_configure_rejects_out_of_range_temperature(self, adapter, caplog):
        os.environ["AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE"] = "3.0"
        mock_config = MagicMock()
        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
                return_value=mock_config,
            ),
            caplog.at_level(
                logging.WARNING,
                logger="ai_governance_mcp.context_engine.cognee_adapter",
            ),
        ):
            adapter.configure()
            mock_config.set_llm_config.assert_not_called()
        assert any("out of range" in r.message.lower() for r in caplog.records)

    # --- Embedding model (unified with CE vars) ---

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_MODEL": "nomic-embed-text"},
        clear=False,
    )
    def test_configure_reads_embedding_model_from_env(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_model.assert_called_once_with("nomic-embed-text")

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_EMBEDDING_MODEL": "custom-model"},
        clear=False,
    )
    def test_configure_embedding_model_falls_back_to_ce_var(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_model.assert_called_once_with("custom-model")

    @patch.dict(os.environ, {}, clear=False)
    def test_configure_embedding_model_defaults_when_no_vars(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_model.assert_called_once_with(
                "BAAI/bge-small-en-v1.5"
            )

    # --- Embedding dimensions (unified with CE vars) ---

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS": "768"},
        clear=False,
    )
    def test_configure_reads_embedding_dimensions_from_env(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(768)

    @patch.dict(
        os.environ,
        {"AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS": "bad"},
        clear=False,
    )
    def test_configure_rejects_invalid_embedding_dimensions(self, adapter):
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(384)

    # --- Embedding divergence warning ---

    @patch.dict(
        os.environ,
        {
            "AI_CONTEXT_ENGINE_EMBEDDING_MODEL": "bge-small",
            "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_MODEL": "nomic-embed-text",
        },
        clear=False,
    )
    def test_configure_logs_warning_on_embedding_divergence(self, adapter, caplog):
        mock_config = MagicMock()
        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
                return_value=mock_config,
            ),
            caplog.at_level(
                logging.INFO, logger="ai_governance_mcp.context_engine.cognee_adapter"
            ),
        ):
            adapter.configure()

        assert any(
            "diverge" in record.message.lower() or "differ" in record.message.lower()
            for record in caplog.records
        )
        mock_config.set_embedding_model.assert_called_once_with("nomic-embed-text")

    # --- Embedding dimensions priority (COGNEE_ overrides CE) ---

    def test_configure_embedding_dimensions_cognee_overrides_ce(self, adapter):
        os.environ["AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS"] = "512"
        os.environ["AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS"] = "768"
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(768)

    # --- Embedding dimensions CE fallback (M3) ---

    def test_configure_embedding_dimensions_falls_back_to_ce_var(self, adapter):
        os.environ["AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS"] = "512"
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(512)

    # --- Zero/negative dimension rejection (M4) ---

    def test_configure_rejects_zero_embedding_dimensions(self, adapter):
        os.environ["AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS"] = "0"
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(384)

    def test_configure_rejects_negative_embedding_dimensions(self, adapter):
        os.environ["AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS"] = "-1"
        mock_config = MagicMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
            return_value=mock_config,
        ):
            adapter.configure()
            mock_config.set_embedding_dimensions.assert_called_once_with(384)


# =============================================================================
# Add + Cognify Tests (Tasks 5-8)
# =============================================================================


class TestCogneeAddCognify:
    """CogneeAdapter.add_chunks() and cognify() operations."""

    @pytest.fixture()
    def adapter(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=True,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            return CogneeAdapter(project_index_path=tmp_path)

    def test_add_chunks_calls_cognee_add(self, adapter):
        from ai_governance_mcp.context_engine.models import ContentChunk

        chunks = [
            ContentChunk(
                content="def hello(): pass",
                source_path="src/main.py",
                start_line=1,
                end_line=1,
                content_type="code",
                heading="hello",
            ),
            ContentChunk(
                content="# Introduction\nThis is a doc.",
                source_path="docs/readme.md",
                start_line=1,
                end_line=2,
                content_type="document",
            ),
        ]

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            result = asyncio.run(
                adapter.add_chunks(chunks, dataset_name="test-project")
            )

        assert result == 2
        mock_cognee.add.assert_called_once()
        call_args = mock_cognee.add.call_args
        texts = call_args[0][0]
        assert len(texts) == 2
        assert "hello" in texts[0]
        assert "src/main.py" in texts[0]

    def test_add_chunks_includes_heading_for_code(self, adapter):
        from ai_governance_mcp.context_engine.models import ContentChunk

        chunks = [
            ContentChunk(
                content="class Foo:\n    pass",
                source_path="src/foo.py",
                start_line=1,
                end_line=2,
                content_type="code",
                heading="Foo",
            ),
        ]

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            asyncio.run(adapter.add_chunks(chunks, dataset_name="test-project"))

        texts = mock_cognee.add.call_args[0][0]
        assert texts[0].startswith("# Foo\n")

    def test_add_chunks_includes_source_path(self, adapter):
        from ai_governance_mcp.context_engine.models import ContentChunk

        chunks = [
            ContentChunk(
                content="some content",
                source_path="docs/guide.md",
                start_line=1,
                end_line=1,
                content_type="document",
            ),
        ]

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            asyncio.run(adapter.add_chunks(chunks, dataset_name="test-project"))

        texts = mock_cognee.add.call_args[0][0]
        assert "docs/guide.md" in texts[0]

    def test_add_chunks_passes_dataset_name(self, adapter):
        from ai_governance_mcp.context_engine.models import ContentChunk

        chunks = [
            ContentChunk(
                content="x",
                source_path="a.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
        ]

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            asyncio.run(adapter.add_chunks(chunks, dataset_name="my-dataset"))

        call_kwargs = mock_cognee.add.call_args[1]
        assert call_kwargs["dataset_name"] == "my-dataset"

    def test_add_chunks_returns_zero_for_empty(self, adapter):
        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            result = asyncio.run(adapter.add_chunks([], dataset_name="empty"))

        assert result == 0
        mock_cognee.add.assert_not_called()

    def test_cognify_calls_cognee_cognify(self, adapter):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock(return_value=None)
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            result = asyncio.run(adapter.cognify(dataset_name="test-project"))

        assert result["status"] == "success"
        assert result["dataset_name"] == "test-project"
        assert "duration_seconds" in result
        mock_cognee.cognify.assert_called_once()

    def test_cognify_returns_error_on_failure(self, adapter):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock(side_effect=RuntimeError("LLM timeout"))
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            result = asyncio.run(adapter.cognify(dataset_name="test-project"))

        assert result["status"] == "error"
        assert "LLM timeout" in result["error"]

    def test_cognify_includes_duration(self, adapter):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock(return_value=None)
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
            return_value=mock_cognee,
        ):
            result = asyncio.run(adapter.cognify(dataset_name="test-project"))

        assert isinstance(result["duration_seconds"], float)
        assert result["duration_seconds"] >= 0


# =============================================================================
# Search Tests (Tasks 9-10)
# =============================================================================


class TestCogneeSearch:
    """CogneeAdapter.search() wraps Cognee's search API."""

    @pytest.fixture()
    def adapter(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=True,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            return CogneeAdapter(project_index_path=tmp_path)

    def test_search_calls_cognee_search(self, adapter):
        mock_cognee = MagicMock()
        mock_search_type = MagicMock()
        mock_search_type.GRAPH_COMPLETION = "GRAPH_COMPLETION"
        mock_cognee.search = AsyncMock(
            return_value=[
                {"text": "result 1", "score": 0.9},
                {"text": "result 2", "score": 0.7},
            ]
        )

        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
                return_value=mock_cognee,
            ),
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_search_type",
                return_value=mock_search_type.GRAPH_COMPLETION,
            ),
        ):
            results = asyncio.run(
                adapter.search(
                    "knowledge graph integration", search_type="GRAPH_COMPLETION"
                )
            )

        assert isinstance(results, list)
        mock_cognee.search.assert_called_once()

    def test_search_empty_results_returns_empty_list(self, adapter):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=[])

        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
                return_value=mock_cognee,
            ),
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_search_type",
                return_value="GRAPH_COMPLETION",
            ),
        ):
            results = asyncio.run(adapter.search("nonexistent query"))

        assert results == []

    def test_search_invalid_type_raises(self, adapter):
        with (
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._import_cognee",
                return_value=MagicMock(),
            ),
            patch(
                "ai_governance_mcp.context_engine.cognee_adapter._get_search_type",
                side_effect=ValueError("Invalid search type: BOGUS"),
            ),
            pytest.raises(ValueError, match="Invalid search type"),
        ):
            asyncio.run(adapter.search("test", search_type="BOGUS"))


# =============================================================================
# Cleanup + Storage Tests (Tasks 11-12)
# =============================================================================


class TestCogneeCleanup:
    """CogneeAdapter cleanup and has_knowledge_graph() checks."""

    @pytest.fixture()
    def adapter(self, tmp_path):
        with patch(
            "ai_governance_mcp.context_engine.cognee_adapter.CogneeAdapter.is_available",
            return_value=True,
        ):
            from ai_governance_mcp.context_engine.cognee_adapter import (
                CogneeAdapter,
            )

            return CogneeAdapter(project_index_path=tmp_path)

    def test_cleanup_removes_cognee_directory(self, adapter):
        adapter._cognee_data_path.mkdir(parents=True)
        (adapter._cognee_data_path / "cognee.db").write_text("fake db")
        assert adapter._cognee_data_path.exists()

        asyncio.run(adapter.cleanup())
        assert not adapter._cognee_data_path.exists()

    def test_cleanup_noop_on_nonexistent_path(self, adapter):
        assert not adapter._cognee_data_path.exists()
        asyncio.run(adapter.cleanup())  # should not raise

    def test_has_knowledge_graph_true_with_data(self, adapter):
        adapter._cognee_data_path.mkdir(parents=True)
        (adapter._cognee_data_path / "databases").mkdir()
        (adapter._cognee_data_path / "databases" / "cognee_db").write_text("data")

        assert adapter.has_knowledge_graph() is True

    def test_has_knowledge_graph_false_when_empty(self, adapter):
        assert adapter.has_knowledge_graph() is False

    def test_has_knowledge_graph_false_when_dir_empty(self, adapter):
        adapter._cognee_data_path.mkdir(parents=True)
        assert adapter.has_knowledge_graph() is False


# =============================================================================
# Thinking Block Pre-Filter Tests
# =============================================================================


class TestThinkingBlockPreFilter:
    """Defensive filter for reasoning model thinking blocks in LLM responses.

    Grammar-constrained decoding (Outlines/GBNF) is the primary defense.
    This filter is the secondary defense for misconfigurations and server bugs.
    """

    @staticmethod
    def _make_response(content="", reasoning_content=None):
        """Build a minimal mock response matching litellm's ModelResponse shape."""
        message = MagicMock()
        message.content = content
        if reasoning_content is not None:
            message.reasoning_content = reasoning_content
        else:
            message.reasoning_content = None
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        return response

    def test_strip_removes_qwen_think_tags(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response('<think>reasoning here</think>{"entity": "test"}')
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"entity": "test"}'

    def test_strip_removes_gemma_channel_tags(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response(
            '<|channel>thought\nsome reasoning<channel|>{"entity": "test"}'
        )
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"entity": "test"}'

    def test_strip_preserves_clean_json(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response('{"entity": "test", "score": 0.9}')
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"entity": "test", "score": 0.9}'

    def test_strip_recovers_json_from_reasoning_content(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response(
            content="", reasoning_content='{"entity": "recovered"}'
        )
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"entity": "recovered"}'

    def test_strip_prefers_content_over_reasoning(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response(
            content='<think>x</think>{"from": "content"}',
            reasoning_content='{"from": "reasoning"}',
        )
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"from": "content"}'

    def test_strip_handles_multiline_thinking(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _strip_thinking_blocks,
        )

        resp = self._make_response(
            '<think>\nline 1\nline 2\nline 3\n</think>{"result": true}'
        )
        result = _strip_thinking_blocks(resp)
        assert result.choices[0].message.content == '{"result": true}'

    def test_strip_json_object_for_lm_studio(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _transform_request_kwargs,
        )

        kwargs = {
            "model": "lm_studio/qwen3.6-35b-a3b-ud-mlx",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": "test"}],
        }
        result = _transform_request_kwargs(kwargs)
        assert "response_format" not in result

    def test_preserve_json_schema_for_lm_studio(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _transform_request_kwargs,
        )

        schema_rf = {
            "type": "json_schema",
            "json_schema": {"name": "test", "schema": {"type": "object"}},
        }
        kwargs = {
            "model": "lm_studio/qwen3.6-35b-a3b-ud-mlx",
            "response_format": schema_rf,
            "messages": [{"role": "user", "content": "test"}],
        }
        result = _transform_request_kwargs(kwargs)
        assert result["response_format"] == schema_rf

    def test_preserve_json_object_for_non_lm_studio(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _transform_request_kwargs,
        )

        kwargs = {
            "model": "ollama/qwen3:30b-a3b",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": "test"}],
        }
        result = _transform_request_kwargs(kwargs)
        assert result["response_format"] == {"type": "json_object"}

    def test_prefilter_is_idempotent(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _THINKING_PATCHED,
            _apply_thinking_prefilter,
        )

        litellm = pytest.importorskip("litellm")
        original = litellm.acompletion
        try:
            _apply_thinking_prefilter()
            first_wrapper = litellm.acompletion
            assert getattr(first_wrapper, _THINKING_PATCHED, False) is True

            _apply_thinking_prefilter()
            second_wrapper = litellm.acompletion
            assert first_wrapper is second_wrapper
        finally:
            litellm.acompletion = original

    def test_configure_applies_prefilter(self):
        from ai_governance_mcp.context_engine.cognee_adapter import (
            _THINKING_PATCHED,
        )

        litellm = pytest.importorskip("litellm")
        original = litellm.acompletion
        try:
            mock_config = MagicMock()
            with (
                patch(
                    "ai_governance_mcp.context_engine.cognee_adapter._get_cognee_config",
                    return_value=mock_config,
                ),
                patch.dict(os.environ, {}, clear=False),
            ):
                from ai_governance_mcp.context_engine.cognee_adapter import (
                    CogneeAdapter,
                )
                from pathlib import Path

                adapter = CogneeAdapter.__new__(CogneeAdapter)
                adapter._project_index_path = Path("/tmp/test")
                adapter._cognee_data_path = Path("/tmp/test/cognee")
                adapter.configure()

            assert getattr(litellm.acompletion, _THINKING_PATCHED, False) is True
        finally:
            litellm.acompletion = original
