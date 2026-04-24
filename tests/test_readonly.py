"""Tests for Context Engine read-only mode.

Covers:
- ReadOnlyFilesystemStorage: init without writes, blocked saves, safe load
- Indexer readonly flag: blocked indexing, no model download
- ProjectManager readonly flag: query with pre-built index, skip auto-indexing
- Server: auto-detection, env var override, tool handler readonly behavior
"""

import json
import os
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from ai_governance_mcp.context_engine.models import (
    ContentChunk,
    ProjectQueryResult,
)
from ai_governance_mcp.context_engine.storage.filesystem import (
    FilesystemStorage,
    ReadOnlyFilesystemStorage,
    ReadOnlyStorageError,
)


# =============================================================================
# ReadOnlyFilesystemStorage Tests
# =============================================================================


class TestReadOnlyFilesystemStorage:
    """Test ReadOnlyFilesystemStorage init and operations."""

    def test_init_does_not_create_directory(self, tmp_path):
        """Init should NOT create the base directory."""
        non_existent = tmp_path / "does_not_exist" / "indexes"
        storage = ReadOnlyFilesystemStorage(base_path=non_existent)
        assert storage.base_path == non_existent.resolve()
        assert not non_existent.exists()

    def test_init_does_not_chmod(self, tmp_path):
        """Init should NOT modify permissions on existing directory."""
        base = tmp_path / "indexes"
        base.mkdir(mode=0o755)
        original_mode = base.stat().st_mode
        ReadOnlyFilesystemStorage(base_path=base)
        assert base.stat().st_mode == original_mode

    def test_init_does_not_cleanup_tmp(self, tmp_path):
        """Init should NOT delete orphaned .tmp files."""
        base = tmp_path / "indexes"
        base.mkdir()
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir()
        tmp_file = project_dir / "metadata.tmp"
        tmp_file.write_text("orphaned")

        ReadOnlyFilesystemStorage(base_path=base)
        assert tmp_file.exists()  # Should still exist

    def test_save_embeddings_raises(self, tmp_path):
        """Write must raise ReadOnlyStorageError under read-only storage.

        Covers: FM-READONLY-WRITE-ESCAPE
        """
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError, match="read-only mode"):
            storage.save_embeddings("abcdef1234567890", np.array([1.0]))

    def test_save_bm25_index_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError):
            storage.save_bm25_index("abcdef1234567890", {"corpus": []})

    def test_save_metadata_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError):
            storage.save_metadata("abcdef1234567890", {"key": "value"})

    def test_save_chunks_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError):
            storage.save_chunks("abcdef1234567890", [])

    def test_save_file_manifest_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError):
            storage.save_file_manifest("abcdef1234567890", {})

    def test_delete_project_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        with pytest.raises(ReadOnlyStorageError):
            storage.delete_project("abcdef1234567890")

    def test_load_embeddings_from_existing_index(self, tmp_path):
        """Read-only storage should load pre-built embeddings normally."""
        base = tmp_path / "indexes"
        # Create index using writable storage first
        writable = FilesystemStorage(base_path=base)
        embeddings = np.random.rand(10, 384).astype(np.float32)
        writable.save_embeddings("abcdef1234567890", embeddings)

        # Read using read-only storage
        readonly = ReadOnlyFilesystemStorage(base_path=base)
        loaded = readonly.load_embeddings("abcdef1234567890")
        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, embeddings)

    def test_load_metadata_from_existing_index(self, tmp_path):
        base = tmp_path / "indexes"
        writable = FilesystemStorage(base_path=base)
        metadata = {"project_id": "abcdef1234567890", "total_chunks": 100}
        writable.save_metadata("abcdef1234567890", metadata)

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        loaded = readonly.load_metadata("abcdef1234567890")
        assert loaded == metadata

    def test_load_chunks_from_existing_index(self, tmp_path):
        base = tmp_path / "indexes"
        writable = FilesystemStorage(base_path=base)
        chunks = [{"content": "test", "source_path": "test.py"}]
        writable.save_chunks("abcdef1234567890", chunks)

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        loaded = readonly.load_chunks("abcdef1234567890")
        assert loaded == chunks

    def test_load_bm25_from_existing_index(self, tmp_path):
        base = tmp_path / "indexes"
        writable = FilesystemStorage(base_path=base)
        bm25_data = [["hello", "world"], ["test"]]
        writable.save_bm25_index("abcdef1234567890", bm25_data)

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        loaded = readonly.load_bm25_index("abcdef1234567890")
        assert loaded == bm25_data

    def test_project_exists_on_existing_index(self, tmp_path):
        base = tmp_path / "indexes"
        writable = FilesystemStorage(base_path=base)
        writable.save_metadata("abcdef1234567890", {"test": True})

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        assert readonly.project_exists("abcdef1234567890")

    def test_project_exists_missing(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        readonly = ReadOnlyFilesystemStorage(base_path=base)
        assert not readonly.project_exists("abcdef1234567890")

    def test_list_projects(self, tmp_path):
        base = tmp_path / "indexes"
        writable = FilesystemStorage(base_path=base)
        writable.save_metadata("abcdef1234567890", {"test": True})
        writable.save_metadata("1234567890abcdef", {"test": True})

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        projects = readonly.list_projects()
        assert set(projects) == {"abcdef1234567890", "1234567890abcdef"}

    def test_corrupt_embeddings_logs_warning_no_unlink(self, tmp_path):
        """Corrupt files should log warning but NOT be deleted in read-only mode.

        Covers: FM-READONLY-CORRUPT-FILE-NO-UNLINK
        """
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        corrupt_file = project_dir / "content_embeddings.npy"
        corrupt_file.write_text("not valid numpy data")

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        result = readonly.load_embeddings("abcdef1234567890")
        assert result is None
        assert corrupt_file.exists()  # NOT deleted

    def test_corrupt_bm25_logs_warning_no_unlink(self, tmp_path):
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        corrupt_file = project_dir / "bm25_index.json"
        corrupt_file.write_text("{invalid json")

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        result = readonly.load_bm25_index("abcdef1234567890")
        assert result is None
        assert corrupt_file.exists()  # NOT deleted

    def test_corrupt_metadata_logs_warning_no_unlink(self, tmp_path):
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        corrupt_file = project_dir / "metadata.json"
        corrupt_file.write_text("{broken")

        readonly = ReadOnlyFilesystemStorage(base_path=base)
        result = readonly.load_metadata("abcdef1234567890")
        assert result is None
        assert corrupt_file.exists()  # NOT deleted


# =============================================================================
# Indexer Readonly Tests
# =============================================================================


class TestIndexerReadonly:
    """Test Indexer behavior in read-only mode."""

    def test_embedding_model_returns_none_when_readonly(self, tmp_path):
        from ai_governance_mcp.context_engine.indexer import Indexer

        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        indexer = Indexer(storage=storage, readonly=True)
        assert indexer.embedding_model is None

    def test_index_project_raises_when_readonly(self, tmp_path):
        """Indexer.index_project must raise RuntimeError when readonly=True.

        Covers: FM-READONLY-INDEX-BLOCKING
        """
        from ai_governance_mcp.context_engine.indexer import Indexer

        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        indexer = Indexer(storage=storage, readonly=True)
        with pytest.raises(RuntimeError, match="read-only mode"):
            indexer.index_project(tmp_path, "abcdef1234567890")

    def test_incremental_update_raises_when_readonly(self, tmp_path):
        from ai_governance_mcp.context_engine.indexer import Indexer

        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        indexer = Indexer(storage=storage, readonly=True)
        with pytest.raises(RuntimeError, match="read-only mode"):
            indexer.incremental_update(tmp_path, "abcdef1234567890", [])


# =============================================================================
# ProjectManager Readonly Tests
# =============================================================================


class TestProjectManagerReadonly:
    """Test ProjectManager behavior in read-only mode."""

    def _make_manager(self, storage, readonly=True):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        return ProjectManager(storage=storage, readonly=readonly)

    def test_startup_watchers_returns_zero(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        manager = self._make_manager(storage)
        assert manager.startup_watchers() == 0

    def test_reindex_project_raises(self, tmp_path):
        storage = ReadOnlyFilesystemStorage(base_path=tmp_path)
        manager = self._make_manager(storage)
        with pytest.raises(RuntimeError, match="read-only mode"):
            manager.reindex_project(tmp_path)

    def test_query_missing_project_returns_empty_with_message(self, tmp_path):
        """Query for unindexed project in readonly mode returns message, not error."""
        base = tmp_path / "indexes"
        base.mkdir()
        storage = ReadOnlyFilesystemStorage(base_path=base)
        manager = self._make_manager(storage)

        result = manager.query_project("test query", project_path=tmp_path)
        assert result.total_results == 0
        assert result.readonly_message is not None
        assert "not indexed" in result.readonly_message.lower()

    def test_query_existing_project_works(self, tmp_path):
        """Query for pre-built index in readonly mode should return results."""
        base = tmp_path / "indexes"

        # Build index using writable storage
        writable_storage = FilesystemStorage(base_path=base)
        writable_manager = self._make_manager(writable_storage, readonly=False)

        # Create a simple project to index
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "test.py").write_text("def hello():\n    return 'world'\n")

        # Index it
        writable_manager.get_or_create_index(project_dir)
        writable_manager.shutdown()

        # Now query with read-only storage
        readonly_storage = ReadOnlyFilesystemStorage(base_path=base)
        readonly_manager = self._make_manager(readonly_storage)

        result = readonly_manager.query_project(
            "hello function", project_path=project_dir
        )
        # Should load the pre-built index and return results (or at least not crash)
        assert result.readonly_message is None
        readonly_manager.shutdown()


# =============================================================================
# Server Readonly Detection Tests
# =============================================================================


class TestReadonlyDetection:
    """Test _detect_readonly_mode function."""

    def test_explicit_true(self):
        from ai_governance_mcp.context_engine.server import _detect_readonly_mode

        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_READONLY": "true"}):
            assert _detect_readonly_mode() is True

    def test_explicit_false(self):
        from ai_governance_mcp.context_engine.server import _detect_readonly_mode

        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_READONLY": "false"}):
            assert _detect_readonly_mode() is False

    def test_auto_writable_directory(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _detect_readonly_mode

        writable_dir = tmp_path / "indexes"
        writable_dir.mkdir()

        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_READONLY": "auto"}):
            assert _detect_readonly_mode(writable_dir) is False

    def test_auto_nonexistent_creatable(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _detect_readonly_mode

        creatable_dir = tmp_path / "new_dir"

        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_READONLY": "auto"}):
            assert _detect_readonly_mode(creatable_dir) is False
            assert creatable_dir.exists()  # Should have been created by probe

    def test_auto_non_writable(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _detect_readonly_mode

        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_READONLY": "auto"}):
            with patch("os.access", return_value=False):
                readonly_dir = tmp_path / "readonly"
                readonly_dir.mkdir()
                assert _detect_readonly_mode(readonly_dir) is True


# =============================================================================
# Server Tool Handler Readonly Tests
# =============================================================================


class TestServerHandlersReadonly:
    """Test server tool handlers in read-only mode."""

    @pytest.mark.asyncio
    async def test_index_project_returns_error_in_readonly(self):
        from ai_governance_mcp.context_engine.server import _handle_index_project

        manager = Mock()
        manager.readonly = True

        result = await _handle_index_project(manager)
        assert len(result) == 1
        output = json.loads(result[0].text)
        assert "error" in output
        assert "read-only" in output["error"].lower()
        assert "hint" in output

    @pytest.mark.asyncio
    async def test_query_includes_readonly_message(self):
        from ai_governance_mcp.context_engine.server import _handle_query_project

        mock_result = ProjectQueryResult(
            query="test",
            project_id="abc123",
            project_path="/tmp/test",
            results=[],
            total_results=0,
            readonly_message="Project not indexed. Index from a writable environment first.",
        )

        manager = Mock()
        manager.readonly = True
        manager.query_project = Mock(return_value=mock_result)

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_result)
            result = await _handle_query_project(manager, {"query": "test"})

        output = json.loads(result[0].text)
        assert output["message"] == mock_result.readonly_message

    @pytest.mark.asyncio
    async def test_stale_warning_readonly_phrasing(self):
        """Staleness warning in readonly should NOT suggest index_project."""
        from ai_governance_mcp.context_engine.models import QueryResult
        from ai_governance_mcp.context_engine.server import _handle_query_project

        chunk = ContentChunk(
            content="def test(): pass",
            source_path="test.py",
            start_line=1,
            end_line=10,
            content_type="code",
        )
        qr = QueryResult(
            chunk=chunk,
            semantic_score=0.8,
            keyword_score=0.5,
            combined_score=0.8,
        )
        mock_result = ProjectQueryResult(
            query="test",
            project_id="abc123",
            project_path="/tmp/test",
            results=[qr],
            total_results=1,
            query_time_ms=10.0,
            last_indexed_at="2026-01-01T00:00:00+00:00",
            index_age_seconds=7200.0,  # 2 hours old
        )

        manager = Mock()
        manager.readonly = True

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_result)
            result = await _handle_query_project(manager, {"query": "test"})

        output = json.loads(result[0].text)
        assert "staleness_warning" in output
        assert "writable environment" in output["staleness_warning"]
        assert "index_project" not in output["staleness_warning"]
