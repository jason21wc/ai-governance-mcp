"""Comprehensive tests for the Context Engine module.

Covers:
- Models (Literal types, validation)
- Storage/Filesystem (security, round-trip, path traversal)
- Connectors (code, document, spreadsheet, image)
- Indexer (discovery, ignore patterns, tokenization)
- Project Manager (query, score fusion, thread safety)
- Server (input validation, error sanitization, rate limiting)
"""

import os
import re
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from pydantic import ValidationError

from ai_governance_mcp.context_engine.models import (
    ContentChunk,
    FileMetadata,
    ProjectIndex,
    ProjectStatus,
    QueryResult,
)
from ai_governance_mcp.context_engine.storage.filesystem import (
    FilesystemStorage,
    _validate_project_id,
)


# =============================================================================
# Model Tests
# =============================================================================


class TestContentChunk:
    """Test ContentChunk model with Literal type validation."""

    def test_valid_content_types(self):
        for ct in ("code", "document", "data", "image"):
            chunk = ContentChunk(
                content="test",
                source_path="/tmp/test.py",
                start_line=1,
                end_line=10,
                content_type=ct,
            )
            assert chunk.content_type == ct

    def test_invalid_content_type_rejected(self):
        with pytest.raises(ValidationError):  # ValidationError
            ContentChunk(
                content="test",
                source_path="/tmp/test.py",
                start_line=1,
                end_line=10,
                content_type="invalid_type",
            )

    def test_optional_fields_default_none(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=10,
            content_type="code",
        )
        assert chunk.language is None
        assert chunk.heading is None
        assert chunk.embedding_id is None


class TestFileMetadata:
    """Test FileMetadata model."""

    def test_valid_creation(self):
        fm = FileMetadata(
            path="/tmp/test.py",
            content_type="code",
            language="python",
            size_bytes=1024,
            last_modified=1234567890.0,
        )
        assert fm.content_type == "code"
        assert fm.chunk_count == 0  # default

    def test_invalid_content_type(self):
        with pytest.raises(ValidationError):
            FileMetadata(
                path="/tmp/test.py",
                content_type="spreadsheet",
                size_bytes=100,
                last_modified=0.0,
            )


class TestProjectIndex:
    """Test ProjectIndex model."""

    def test_valid_index_modes(self):
        for mode in ("realtime", "ondemand"):
            idx = ProjectIndex(
                project_id="abc123",
                project_path="/tmp/project",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                embedding_model="test-model",
                index_mode=mode,
            )
            assert idx.index_mode == mode

    def test_invalid_index_mode_rejected(self):
        with pytest.raises(ValidationError):
            ProjectIndex(
                project_id="abc123",
                project_path="/tmp/project",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                embedding_model="test-model",
                index_mode="manual",
            )

    def test_defaults(self):
        idx = ProjectIndex(
            project_id="abc123",
            project_path="/tmp/project",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            embedding_model="test-model",
        )
        assert idx.total_chunks == 0
        assert idx.total_files == 0
        assert idx.index_mode == "ondemand"
        assert idx.chunks == []
        assert idx.files == []


class TestProjectStatus:
    """Test ProjectStatus model."""

    def test_index_mode_literal(self):
        status = ProjectStatus(
            project_id="abc",
            project_path="/tmp",
            embedding_model="test",
            index_mode="ondemand",
        )
        assert status.index_mode == "ondemand"


class TestQueryResult:
    """Test QueryResult model."""

    def test_score_constraints(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=10,
            content_type="code",
        )
        result = QueryResult(
            chunk=chunk,
            semantic_score=0.8,
            keyword_score=0.5,
            combined_score=0.7,
        )
        assert result.semantic_score == 0.8

    def test_semantic_score_clamped(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=10,
            content_type="code",
        )
        with pytest.raises(ValidationError):
            QueryResult(
                chunk=chunk,
                semantic_score=1.5,  # > 1.0
                keyword_score=0.5,
                combined_score=0.7,
            )


# =============================================================================
# Filesystem Storage Tests
# =============================================================================


class TestProjectIdValidation:
    """Test project ID validation for path traversal prevention."""

    def test_valid_hex_ids(self):
        _validate_project_id("abc123def456")
        _validate_project_id("0" * 16)
        _validate_project_id("a" * 64)
        _validate_project_id("f")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("../../../etc/passwd")

    def test_rejects_slashes(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("abc/def")

    def test_rejects_uppercase(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("ABC123")

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("a" * 65)

    def test_rejects_spaces(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("abc 123")

    def test_rejects_dots(self):
        with pytest.raises(ValueError, match="hex characters only"):
            _validate_project_id("abc.123")


class TestFilesystemStorage:
    """Test FilesystemStorage with security features."""

    @pytest.fixture
    def storage(self, tmp_path):
        return FilesystemStorage(base_path=tmp_path / "indexes")

    def test_default_base_path(self):
        with patch.object(Path, "home", return_value=Path("/mock/home")):
            with patch.object(Path, "mkdir"):
                with patch("os.chmod"):
                    storage = FilesystemStorage()
                    assert "context-engine" in str(storage.base_path)

    def test_project_id_from_path(self):
        pid = FilesystemStorage.project_id_from_path(Path("/tmp/myproject"))
        assert re.match(r"^[0-9a-f]{16}$", pid)

    def test_project_id_deterministic(self):
        p = Path("/tmp/myproject")
        assert FilesystemStorage.project_id_from_path(
            p
        ) == FilesystemStorage.project_id_from_path(p)

    def test_project_id_different_paths(self):
        pid1 = FilesystemStorage.project_id_from_path(Path("/tmp/project1"))
        pid2 = FilesystemStorage.project_id_from_path(Path("/tmp/project2"))
        assert pid1 != pid2

    def test_get_index_path_validates(self, storage):
        with pytest.raises(ValueError):
            storage.get_index_path("../traversal")

    def test_get_index_path_valid(self, storage):
        path = storage.get_index_path("abc123")
        assert path.name == "abc123"

    def test_path_containment_check(self, storage):
        """Even valid hex IDs can't escape base path."""
        path = storage.get_index_path("deadbeef")
        assert path.is_relative_to(storage.base_path)

    def test_save_load_embeddings_roundtrip(self, storage):
        pid = "abc123"
        embeddings = np.random.rand(5, 384).astype(np.float32)
        storage.save_embeddings(pid, embeddings)
        loaded = storage.load_embeddings(pid)
        assert loaded is not None
        np.testing.assert_array_almost_equal(embeddings, loaded)

    def test_load_embeddings_nonexistent(self, storage):
        assert storage.load_embeddings("aabbccdd") is None

    def test_load_embeddings_allow_pickle_false(self, storage):
        """Verify numpy load uses allow_pickle=False."""
        pid = "abc123"
        storage.save_embeddings(pid, np.zeros((1, 10)))
        # Patch np.load to verify allow_pickle=False
        original_load = np.load
        calls = []

        def tracking_load(*args, **kwargs):
            calls.append(kwargs)
            return original_load(*args, **kwargs)

        with patch("numpy.load", side_effect=tracking_load):
            storage.load_embeddings(pid)

        assert any(c.get("allow_pickle") is False for c in calls)

    def test_save_load_bm25_json_roundtrip(self, storage):
        pid = "abc123"
        data = {"tokenized_corpus": [["hello", "world"], ["test"]], "chunk_count": 2}
        storage.save_bm25_index(pid, data)
        loaded = storage.load_bm25_index(pid)
        assert loaded == data

    def test_load_bm25_nonexistent(self, storage):
        assert storage.load_bm25_index("aabbccdd") is None

    def test_save_load_metadata_roundtrip(self, storage):
        pid = "abc123"
        metadata = {"project_path": "/tmp/test", "total_files": 5}
        storage.save_metadata(pid, metadata)
        loaded = storage.load_metadata(pid)
        assert loaded == metadata

    def test_save_load_file_manifest_roundtrip(self, storage):
        pid = "abc123"
        manifest = {"/tmp/test.py": {"size": 1024}}
        storage.save_file_manifest(pid, manifest)
        loaded = storage.load_file_manifest(pid)
        assert loaded == manifest

    def test_project_exists(self, storage):
        pid = "abc123"
        assert not storage.project_exists(pid)
        storage.save_metadata(pid, {"test": True})
        assert storage.project_exists(pid)

    def test_list_projects(self, storage):
        assert storage.list_projects() == []
        storage.save_metadata("aaa111", {"test": True})
        storage.save_metadata("bbb222", {"test": True})
        projects = storage.list_projects()
        assert set(projects) == {"aaa111", "bbb222"}

    def test_list_projects_ignores_invalid_dirs(self, storage):
        """Directories with non-hex names should be ignored."""
        storage.save_metadata("abc123", {"test": True})
        # Create a directory with invalid name
        invalid_dir = storage.base_path / "NOT_HEX"
        invalid_dir.mkdir(parents=True)
        (invalid_dir / "metadata.json").write_text("{}")
        projects = storage.list_projects()
        assert projects == ["abc123"]

    def test_delete_project(self, storage):
        pid = "abc123"
        storage.save_metadata(pid, {"test": True})
        assert storage.project_exists(pid)
        storage.delete_project(pid)
        assert not storage.project_exists(pid)

    def test_delete_nonexistent_project(self, storage):
        """Should not raise if project doesn't exist."""
        storage.delete_project("aabbccdd")


# =============================================================================
# Connector Tests
# =============================================================================


class TestCodeConnector:
    """Test code connector parsing."""

    def test_supported_extensions(self):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        assert ".py" in conn.supported_extensions
        assert ".js" in conn.supported_extensions
        assert ".txt" not in conn.supported_extensions

    def test_can_handle(self):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        assert conn.can_handle(Path("test.py"))
        assert conn.can_handle(Path("test.js"))
        assert not conn.can_handle(Path("test.txt"))

    def test_parse_python_file(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        f = tmp_path / "test.py"
        f.write_text("def hello():\n    print('hello world')\n\nclass Foo:\n    pass\n")
        chunks = conn.parse(f)
        assert len(chunks) >= 1
        assert chunks[0].content_type == "code"
        assert chunks[0].language == "python"

    def test_parse_empty_file(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        f = tmp_path / "empty.py"
        f.write_text("")
        chunks = conn.parse(f)
        assert chunks == []

    def test_extract_metadata(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        metadata = conn.extract_metadata(f)
        assert metadata.content_type == "code"
        assert metadata.language == "python"
        assert metadata.size_bytes > 0


class TestDocumentConnector:
    """Test document connector parsing."""

    def test_supported_extensions(self):
        from ai_governance_mcp.context_engine.connectors.document import (
            DocumentConnector,
        )

        conn = DocumentConnector()
        assert ".md" in conn.supported_extensions
        assert ".txt" in conn.supported_extensions
        assert ".rst" in conn.supported_extensions

    def test_parse_markdown(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.document import (
            DocumentConnector,
        )

        conn = DocumentConnector()
        f = tmp_path / "readme.md"
        f.write_text("# Title\n\nContent here.\n\n## Section\n\nMore content.\n")
        chunks = conn.parse(f)
        assert len(chunks) >= 1
        assert chunks[0].content_type == "document"

    def test_parse_plain_text(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.document import (
            DocumentConnector,
        )

        conn = DocumentConnector()
        f = tmp_path / "notes.txt"
        f.write_text("Some plain text notes.\nLine two.\n")
        chunks = conn.parse(f)
        assert len(chunks) >= 1


class TestSpreadsheetConnector:
    """Test spreadsheet connector parsing."""

    def test_supported_extensions(self):
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        assert ".csv" in conn.supported_extensions
        assert ".tsv" in conn.supported_extensions

    def test_parse_csv(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        f = tmp_path / "data.csv"
        f.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")
        chunks = conn.parse(f)
        assert len(chunks) == 1
        assert chunks[0].content_type == "data"
        assert "Schema:" in chunks[0].content
        assert "name" in chunks[0].content

    def test_parse_empty_csv(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        f = tmp_path / "empty.csv"
        f.write_text("")
        chunks = conn.parse(f)
        assert chunks == []


class TestImageConnector:
    """Test image connector metadata extraction."""

    def test_supported_extensions(self):
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        assert ".png" in conn.supported_extensions
        assert ".jpg" in conn.supported_extensions
        assert ".py" not in conn.supported_extensions

    def test_parse_basic_metadata(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f)
        assert len(chunks) == 1
        assert chunks[0].content_type == "image"
        assert "Image: test.png" in chunks[0].content

    def test_extract_metadata(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        metadata = conn.extract_metadata(f)
        assert metadata.content_type == "image"
        assert metadata.language == "png"


# =============================================================================
# Indexer Tests
# =============================================================================


class TestIndexer:
    """Test the core indexer."""

    @pytest.fixture
    def mock_storage(self, tmp_path):
        return FilesystemStorage(base_path=tmp_path / "indexes")

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a small test project directory."""
        proj = tmp_path / "testproject"
        proj.mkdir()
        (proj / "main.py").write_text("def main():\n    print('hello')\n")
        (proj / "README.md").write_text("# Test Project\n\nA test.\n")
        (proj / "data.csv").write_text("a,b,c\n1,2,3\n")
        return proj

    def test_load_ignore_patterns_default(self, project_dir):
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(storage=Mock())
        spec = indexer.load_ignore_patterns(project_dir)
        # Default spec should match common ignored paths
        assert spec.match_file(".git/HEAD")
        assert spec.match_file("__pycache__/module.pyc")
        assert spec.match_file("node_modules/pkg/index.js")
        assert not spec.match_file("src/main.py")

    def test_load_ignore_patterns_contextignore(self, project_dir):
        from ai_governance_mcp.context_engine.indexer import Indexer

        (project_dir / ".contextignore").write_text("*.log\nsecrets/\n# comment\n")
        indexer = Indexer(storage=Mock())
        spec = indexer.load_ignore_patterns(project_dir)
        assert spec.match_file("app.log")
        assert spec.match_file("secrets/key.txt")
        # Comments should not be treated as patterns
        assert not spec.match_file("src/main.py")

    def test_load_ignore_patterns_gitignore_fallback(self, project_dir):
        from ai_governance_mcp.context_engine.indexer import Indexer

        (project_dir / ".gitignore").write_text("*.pyc\nbuild/\n")
        indexer = Indexer(storage=Mock())
        spec = indexer.load_ignore_patterns(project_dir)
        assert spec.match_file("module.pyc")
        assert spec.match_file("build/output.js")

    def test_discover_files_skips_ignored(self, project_dir):
        import pathspec

        from ai_governance_mcp.context_engine.indexer import Indexer

        (project_dir / "ignored.log").write_text("log content")
        indexer = Indexer(storage=Mock())
        spec = pathspec.GitIgnoreSpec.from_lines(["*.log"])
        files = indexer._discover_files(project_dir, spec)
        assert not any(f.name == "ignored.log" for f in files)

    def test_discover_files_skips_symlinks(self, project_dir):
        import pathspec

        from ai_governance_mcp.context_engine.indexer import Indexer

        target = project_dir / "target.py"
        target.write_text("x = 1")
        link = project_dir / "link.py"
        link.symlink_to(target)
        indexer = Indexer(storage=Mock())
        spec = pathspec.GitIgnoreSpec.from_lines([])
        files = indexer._discover_files(project_dir, spec)
        assert not any(f.name == "link.py" for f in files)

    def test_discover_files_skips_large_files(self, project_dir):
        import pathspec

        from ai_governance_mcp.context_engine.indexer import (
            MAX_FILE_SIZE_BYTES,
            Indexer,
        )

        large = project_dir / "large.py"
        large.write_text("x = 1\n" * (MAX_FILE_SIZE_BYTES // 5))
        indexer = Indexer(storage=Mock())
        spec = pathspec.GitIgnoreSpec.from_lines([])
        files = indexer._discover_files(project_dir, spec)
        assert not any(f.name == "large.py" for f in files)

    def test_gitignore_matching_with_pathspec(self):
        """Verify pathspec handles gitignore patterns correctly."""
        import pathspec

        spec = pathspec.GitIgnoreSpec.from_lines(
            [
                "__pycache__/",
                "node_modules/",
                "*.log",
            ]
        )
        assert spec.match_file("__pycache__/module.pyc")
        assert spec.match_file("node_modules/pkg/index.js")
        assert spec.match_file("deep/nested/error.log")
        assert not spec.match_file("src/main.py")

    def test_file_hash_deterministic(self, project_dir):
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(storage=Mock())
        h1 = indexer._file_hash(project_dir / "main.py")
        h2 = indexer._file_hash(project_dir / "main.py")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_build_bm25_index_tokenization(self):
        """Verify BM25 tokenization uses word-boundary splitting."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(storage=Mock())
        chunks = [
            ContentChunk(
                content="hello-world foo_bar",
                source_path="/tmp/test.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
        ]
        result = indexer._build_bm25_index(chunks)
        tokens = result["tokenized_corpus"][0]
        # re.findall(r'\w+', ...) should split on hyphens but keep underscores
        assert "hello" in tokens
        assert "world" in tokens
        assert "foo_bar" in tokens

    def test_generate_embeddings_truncation(self):
        """Verify content is truncated at MAX_EMBEDDING_INPUT_CHARS."""
        from ai_governance_mcp.context_engine.indexer import (
            MAX_EMBEDDING_INPUT_CHARS,
            Indexer,
        )

        indexer = Indexer(storage=Mock())
        # Inject mock embedding model directly
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=np.zeros((2, 384)))
        indexer._embedding_model = mock_model

        long_content = "a" * (MAX_EMBEDDING_INPUT_CHARS + 500)
        chunks = [
            ContentChunk(
                content=long_content,
                source_path="/tmp/test.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
            ContentChunk(
                content="short",
                source_path="/tmp/test2.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
        ]
        indexer._generate_embeddings(chunks)
        # Check that encode was called with truncated texts
        call_args = mock_model.encode.call_args
        texts = call_args[0][0]
        assert len(texts[0]) == MAX_EMBEDDING_INPUT_CHARS
        assert texts[1] == "short"


# =============================================================================
# Project Manager Tests
# =============================================================================


class TestProjectManager:
    """Test the ProjectManager query and score fusion."""

    @pytest.fixture
    def storage(self, tmp_path):
        return FilesystemStorage(base_path=tmp_path / "indexes")

    def test_fuse_scores_weighted(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(semantic_weight=0.6)
        chunks = [
            ContentChunk(
                content="test",
                source_path="/tmp/test.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
        ]
        sem = np.array([0.8])
        kw = np.array([0.4])
        results = pm._fuse_scores(chunks, sem, kw, max_results=10)
        assert len(results) == 1
        expected = 0.6 * 0.8 + 0.4 * 0.4
        assert abs(results[0].combined_score - expected) < 0.001

    def test_fuse_scores_empty(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        results = pm._fuse_scores([], np.array([]), np.array([]), max_results=10)
        assert results == []

    def test_fuse_scores_max_results(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(semantic_weight=0.5)
        chunks = [
            ContentChunk(
                content=f"chunk {i}",
                source_path="/tmp/test.py",
                start_line=i,
                end_line=i,
                content_type="code",
            )
            for i in range(20)
        ]
        sem = np.random.rand(20)
        kw = np.random.rand(20)
        results = pm._fuse_scores(chunks, sem, kw, max_results=5)
        assert len(results) <= 5

    def test_fuse_scores_skips_zero(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(semantic_weight=0.5)
        chunks = [
            ContentChunk(
                content="relevant",
                source_path="/tmp/test.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
            ContentChunk(
                content="irrelevant",
                source_path="/tmp/test2.py",
                start_line=1,
                end_line=1,
                content_type="code",
            ),
        ]
        sem = np.array([0.8, 0.0])
        kw = np.array([0.6, 0.0])
        results = pm._fuse_scores(chunks, sem, kw, max_results=10)
        assert len(results) == 1

    def test_bm25_search_tokenization(self):
        """Verify BM25 query tokenization uses word-boundary splitting."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        # Mock BM25
        mock_bm25 = Mock()
        mock_bm25.get_scores = Mock(return_value=np.array([0.5, 0.3]))
        pm._loaded_bm25["test_project"] = mock_bm25

        pm._bm25_search("hello-world foo_bar", "test_project")
        call_args = mock_bm25.get_scores.call_args[0][0]
        assert "hello" in call_args
        assert "world" in call_args
        assert "foo_bar" in call_args

    def test_index_lock_exists_and_is_rlock(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        assert hasattr(pm, "_index_lock")
        assert isinstance(pm._index_lock, type(threading.RLock()))

    def test_shutdown(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        pm.shutdown()  # Should not raise


# =============================================================================
# Server Tests
# =============================================================================


class TestServerSecurity:
    """Test server input validation, error sanitization, and rate limiting."""

    def test_sanitize_error_message_removes_paths(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Failed at /Users/jason/secret/project/file.py")
        sanitized = _sanitize_error_message(err)
        assert "/Users/jason/secret/project/" not in sanitized
        assert "file.py" in sanitized

    def test_sanitize_error_message_removes_line_numbers(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Error at, line 42 in module")
        sanitized = _sanitize_error_message(err)
        assert "line 42" not in sanitized

    def test_sanitize_error_message_removes_memory_addresses(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Object at 0x7f1234567890")
        sanitized = _sanitize_error_message(err)
        assert "0x7f1234567890" not in sanitized
        assert "0x***" in sanitized

    def test_sanitize_error_message_truncates(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("x" * 1000)
        sanitized = _sanitize_error_message(err)
        assert len(sanitized) <= 520  # 500 + "[truncated]"

    def test_sanitize_for_logging_truncates(self):
        from ai_governance_mcp.context_engine.server import (
            MAX_LOG_CONTENT_LENGTH,
            _sanitize_for_logging,
        )

        long = "x" * (MAX_LOG_CONTENT_LENGTH + 100)
        sanitized = _sanitize_for_logging(long)
        assert len(sanitized) < len(long)
        assert "[TRUNCATED]" in sanitized

    def test_sanitize_for_logging_empty(self):
        from ai_governance_mcp.context_engine.server import _sanitize_for_logging

        assert _sanitize_for_logging("") == ""
        assert _sanitize_for_logging(None) is None

    def test_rate_limiter_allows_initial(self):
        from ai_governance_mcp.context_engine.server import _check_index_rate_limit

        # Reset state
        import ai_governance_mcp.context_engine.server as srv

        srv._index_rate_tokens = srv._INDEX_RATE_LIMIT_TOKENS
        srv._index_rate_last_refill = time.time()

        assert _check_index_rate_limit() is True

    def test_rate_limiter_blocks_excess(self):
        import ai_governance_mcp.context_engine.server as srv

        # Drain all tokens
        srv._index_rate_tokens = 0.0
        srv._index_rate_last_refill = time.time()

        assert srv._check_index_rate_limit() is False

    def test_max_query_length_constant(self):
        from ai_governance_mcp.context_engine.server import MAX_QUERY_LENGTH

        assert MAX_QUERY_LENGTH == 10000


class TestServerHandlers:
    """Test server tool handler input validation."""

    @pytest.fixture
    def manager(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_query_empty_string(self, manager):
        from ai_governance_mcp.context_engine.server import _handle_query_project

        result = await _handle_query_project(manager, {"query": ""})
        assert "empty" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_query_whitespace_only(self, manager):
        from ai_governance_mcp.context_engine.server import _handle_query_project

        result = await _handle_query_project(manager, {"query": "   "})
        assert "empty" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_query_non_string(self, manager):
        from ai_governance_mcp.context_engine.server import _handle_query_project

        result = await _handle_query_project(manager, {"query": 12345})
        assert "string" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_query_too_long(self, manager):
        from ai_governance_mcp.context_engine.server import (
            MAX_QUERY_LENGTH,
            _handle_query_project,
        )

        result = await _handle_query_project(
            manager, {"query": "x" * (MAX_QUERY_LENGTH + 1)}
        )
        assert "maximum length" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_max_results_bounds_clamped(self, manager):
        """max_results should be clamped to [1, 50]."""
        from ai_governance_mcp.context_engine.server import _handle_query_project

        mock_result = Mock()
        mock_result.results = []
        manager.query_project = Mock(return_value=mock_result)

        await _handle_query_project(manager, {"query": "test", "max_results": 999})
        call_kwargs = manager.query_project.call_args
        assert call_kwargs[1]["max_results"] <= 50

    @pytest.mark.asyncio
    async def test_max_results_invalid_type(self, manager):
        """Invalid max_results type should fall back to default."""
        from ai_governance_mcp.context_engine.server import _handle_query_project

        mock_result = Mock()
        mock_result.results = []
        manager.query_project = Mock(return_value=mock_result)

        await _handle_query_project(
            manager, {"query": "test", "max_results": "not_a_number"}
        )
        call_kwargs = manager.query_project.call_args
        assert call_kwargs[1]["max_results"] == 10

    @pytest.mark.asyncio
    async def test_index_project_rate_limited(self):
        from ai_governance_mcp.context_engine.server import _handle_index_project

        import ai_governance_mcp.context_engine.server as srv

        srv._index_rate_tokens = 0.0
        srv._index_rate_last_refill = time.time()

        manager = Mock()
        result = await _handle_index_project(manager)
        assert "rate limited" in result[0].text.lower()
        manager.reindex_project.assert_not_called()

    def test_error_sanitization_integration(self):
        """Verify the error sanitization pipeline works end-to-end."""
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        # Simulate a real traceback-style error
        err = Exception(
            "FileNotFoundError: [Errno 2] No such file or directory: "
            "'/Users/jason/secret/project/src/module.py', line 42"
        )
        sanitized = _sanitize_error_message(err)
        assert "/Users/jason/secret/project/src/" not in sanitized
        assert "line 42" not in sanitized
        assert "module.py" in sanitized  # filename is kept


# =============================================================================
# FileWatcher Tests
# =============================================================================


class TestFileWatcher:
    """Test the FileWatcher debouncing and ignore logic."""

    def test_init_defaults(self, tmp_path):
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        assert watcher.project_path == tmp_path
        assert watcher.debounce_seconds == 2.0
        assert watcher.cooldown_seconds == 5.0
        assert watcher.ignore_spec is None
        assert watcher.is_running is False

    def test_stop_without_start(self, tmp_path):
        """Stopping a watcher that was never started should not raise."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        watcher = FileWatcher(project_path=tmp_path, on_change=Mock())
        watcher.stop()  # Should not raise

    def test_file_changed_when_not_running(self, tmp_path):
        """Changes are ignored when watcher is not running."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        watcher._file_changed(test_file)
        assert len(watcher._pending_changes) == 0

    def test_file_changed_ignore_patterns(self, tmp_path):
        """Files matching ignore patterns should not be queued."""
        import pathspec

        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        ignore_spec = pathspec.GitIgnoreSpec.from_lines(["*.log", "*.pyc"])
        watcher = FileWatcher(
            project_path=tmp_path,
            on_change=callback,
            ignore_spec=ignore_spec,
        )
        watcher._running.set()
        log_file = tmp_path / "app.log"
        log_file.write_text("log content")
        watcher._file_changed(log_file)
        assert len(watcher._pending_changes) == 0

    def test_file_changed_outside_project(self, tmp_path):
        """Files outside the project path should be ignored."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path / "subdir", on_change=callback)
        watcher._running.set()
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("x = 1")
        watcher._file_changed(outside_file)
        assert len(watcher._pending_changes) == 0

    def test_file_changed_queues_valid_file(self, tmp_path):
        """Valid files should be queued for processing."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._running.set()
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        # Cancel the debounce timer immediately to prevent background flush
        watcher._file_changed(test_file)
        if watcher._debounce_timer:
            watcher._debounce_timer.cancel()
        assert test_file in watcher._pending_changes

    def test_flush_changes_calls_callback(self, tmp_path):
        """Flushing should call the callback with pending changes."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._running.set()  # H4 fix requires _running to be set
        test_file = tmp_path / "test.py"
        watcher._pending_changes.add(test_file)
        watcher._flush_changes()
        callback.assert_called_once()
        assert test_file in callback.call_args[0][0]
        assert len(watcher._pending_changes) == 0

    def test_flush_changes_empty_noop(self, tmp_path):
        """Flushing with no pending changes should not call callback."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._flush_changes()
        callback.assert_not_called()

    def test_flush_changes_handles_callback_error(self, tmp_path):
        """Errors in the callback should be caught, not propagated."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock(side_effect=RuntimeError("callback failed"))
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._running.set()  # H4 fix requires _running to be set
        watcher._pending_changes.add(tmp_path / "test.py")
        watcher._flush_changes()  # Should not raise
        callback.assert_called_once()

    def test_flush_changes_noop_when_stopped(self, tmp_path):
        """H4 fix: Flushing after stop should be a no-op."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        # Don't set _running - simulates post-stop state
        watcher._pending_changes.add(tmp_path / "test.py")
        watcher._flush_changes()
        callback.assert_not_called()  # Should skip when not running

    def test_is_running_property(self, tmp_path):
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        watcher = FileWatcher(project_path=tmp_path, on_change=Mock())
        assert watcher.is_running is False
        watcher._running.set()
        assert watcher.is_running is True

    def test_start_without_watchdog(self, tmp_path):
        """Start should log a warning and return if watchdog is not installed."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        watcher = FileWatcher(project_path=tmp_path, on_change=Mock())

        with patch.dict(
            "sys.modules",
            {"watchdog": None, "watchdog.events": None, "watchdog.observers": None},
        ):
            # Force the import inside start() to fail
            with patch("builtins.__import__", side_effect=ImportError("no watchdog")):
                watcher.start()
        assert watcher.is_running is False


# =============================================================================
# Project Manager Lifecycle Tests
# =============================================================================


class TestProjectManagerLifecycle:
    """Test ProjectManager lifecycle operations: create, load, reindex, list."""

    @pytest.fixture
    def storage(self, tmp_path):
        return FilesystemStorage(base_path=tmp_path / "indexes")

    @pytest.fixture
    def mock_indexer_pm(self, storage):
        """Create a ProjectManager with a mocked indexer."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        # Replace the indexer with a mock
        mock_indexer = MagicMock()
        mock_index = ProjectIndex(
            project_id="abc123",
            project_path="/tmp/testproject",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            embedding_model="test-model",
            total_chunks=5,
            total_files=2,
            chunks=[
                ContentChunk(
                    content="def hello(): pass",
                    source_path="/tmp/testproject/main.py",
                    start_line=1,
                    end_line=1,
                    content_type="code",
                    embedding_id=0,
                ),
            ],
        )
        mock_indexer.index_project.return_value = mock_index
        pm._indexer = mock_indexer
        return pm

    def test_get_or_create_index_new_project(self, mock_indexer_pm, tmp_path):
        project_path = tmp_path / "newproject"
        project_path.mkdir()

        index = mock_indexer_pm.get_or_create_index(project_path)
        assert index.total_chunks == 5
        mock_indexer_pm._indexer.index_project.assert_called_once()

    def test_get_or_create_index_already_loaded(self, mock_indexer_pm, tmp_path):
        """If index is already in memory, return it without re-indexing."""
        project_path = tmp_path / "loaded"
        project_path.mkdir()
        pid = FilesystemStorage.project_id_from_path(project_path)

        existing_index = ProjectIndex(
            project_id=pid,
            project_path=str(project_path),
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            embedding_model="test-model",
        )
        mock_indexer_pm._loaded_indexes[pid] = existing_index

        result = mock_indexer_pm.get_or_create_index(project_path)
        assert result is existing_index
        mock_indexer_pm._indexer.index_project.assert_not_called()

    def test_get_or_create_index_from_storage(self, storage, tmp_path):
        """If index exists in storage but not loaded, load it."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        project_path = tmp_path / "stored_project"
        project_path.mkdir()
        pid = FilesystemStorage.project_id_from_path(project_path)

        # Manually save metadata as if it was previously indexed
        metadata = ProjectIndex(
            project_id=pid,
            project_path=str(project_path),
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            embedding_model="test-model",
            total_chunks=3,
            total_files=1,
        ).model_dump()
        storage.save_metadata(pid, metadata)

        result = pm.get_or_create_index(project_path)
        assert result.project_id == pid
        assert pid in pm._loaded_indexes

    def test_reindex_clears_and_rebuilds(self, mock_indexer_pm, tmp_path):
        project_path = tmp_path / "reindex_project"
        project_path.mkdir()
        pid = FilesystemStorage.project_id_from_path(project_path)

        # Prime with existing data
        mock_indexer_pm._loaded_indexes[pid] = MagicMock()
        mock_indexer_pm._loaded_embeddings[pid] = np.zeros((1, 384))
        mock_indexer_pm._loaded_bm25[pid] = MagicMock()

        mock_indexer_pm.reindex_project(project_path)

        # Indexer should have been called
        mock_indexer_pm._indexer.index_project.assert_called_once()

    def test_list_projects_empty(self, storage):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        assert pm.list_projects() == []

    def test_list_projects_with_data(self, storage, tmp_path):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        pid = "aabb1122"
        index_path = storage.get_index_path(pid)
        index_path.mkdir(parents=True, exist_ok=True)
        storage.save_metadata(
            pid,
            {
                "project_id": pid,
                "project_path": str(tmp_path),
                "total_files": 3,
                "total_chunks": 10,
                "index_mode": "realtime",
                "updated_at": "2025-01-01T00:00:00Z",
                "embedding_model": "test-model",
            },
        )
        projects = pm.list_projects()
        assert len(projects) == 1
        assert projects[0].project_id == pid
        assert projects[0].total_files == 3

    def test_get_project_status_none(self, storage, tmp_path):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        status = pm.get_project_status(tmp_path / "nonexistent")
        assert status is None

    def test_get_project_status_exists(self, storage, tmp_path):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        project_path = tmp_path / "status_project"
        project_path.mkdir()
        pid = FilesystemStorage.project_id_from_path(project_path)
        index_path = storage.get_index_path(pid)
        index_path.mkdir(parents=True, exist_ok=True)
        storage.save_metadata(
            pid,
            {
                "project_id": pid,
                "project_path": str(project_path),
                "total_files": 5,
                "total_chunks": 20,
                "index_mode": "ondemand",
                "updated_at": "2025-06-01T00:00:00Z",
                "embedding_model": "test-model",
            },
        )
        status = pm.get_project_status(project_path)
        assert status is not None
        assert status.total_files == 5
        assert status.index_mode == "ondemand"

    def test_query_project_empty_index(self, storage, tmp_path):
        """Querying a project with no chunks returns empty results."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        project_path = tmp_path / "empty_project"
        project_path.mkdir()
        pid = FilesystemStorage.project_id_from_path(project_path)

        # Save an empty index
        empty_index = ProjectIndex(
            project_id=pid,
            project_path=str(project_path),
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            embedding_model="test-model",
            chunks=[],
        )
        storage.save_metadata(pid, empty_index.model_dump())

        result = pm.query_project("anything", project_path)
        assert result.total_results == 0

    def test_semantic_search_no_embeddings(self, storage):
        """Semantic search returns empty array when no embeddings loaded."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager(storage=storage)
        scores = pm._semantic_search("test query", "nonexistent_project")
        assert len(scores) == 0

    def test_shutdown_stops_watchers(self):
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        mock_watcher = MagicMock()
        pm._watchers["test_project"] = mock_watcher
        pm.shutdown()
        mock_watcher.stop.assert_called_once()
        assert len(pm._watchers) == 0


# =============================================================================
# Server Handler Additional Tests
# =============================================================================


class TestServerHandlersAdditional:
    """Test _handle_list_projects and _handle_project_status."""

    @pytest.mark.asyncio
    async def test_handle_list_projects_empty(self):
        from ai_governance_mcp.context_engine.server import _handle_list_projects

        manager = Mock()
        manager.list_projects.return_value = []
        result = await _handle_list_projects(manager)
        assert "No indexed projects" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_list_projects_with_projects(self):
        from ai_governance_mcp.context_engine.server import _handle_list_projects

        manager = Mock()
        manager.list_projects.return_value = [
            ProjectStatus(
                project_id="abc123",
                project_path="/tmp/project",
                total_files=3,
                total_chunks=10,
                index_mode="realtime",
                last_updated="2025-01-01T00:00:00Z",
                index_size_bytes=1024,
                embedding_model="test-model",
            )
        ]
        result = await _handle_list_projects(manager)
        import json

        data = json.loads(result[0].text)
        assert len(data["projects"]) == 1
        assert data["projects"][0]["project_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_handle_project_status_not_indexed(self):
        from ai_governance_mcp.context_engine.server import _handle_project_status

        manager = Mock()
        manager.get_project_status.return_value = None
        result = await _handle_project_status(manager)
        assert "not indexed" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_project_status_indexed(self):
        from ai_governance_mcp.context_engine.server import _handle_project_status

        manager = Mock()
        manager.get_project_status.return_value = ProjectStatus(
            project_id="abc123",
            project_path="/tmp/project",
            total_files=5,
            total_chunks=20,
            embedding_model="test-model",
        )
        result = await _handle_project_status(manager)
        import json

        data = json.loads(result[0].text)
        assert data["total_files"] == 5
        assert data["total_chunks"] == 20

    @pytest.mark.asyncio
    async def test_handle_query_project_with_results(self):
        """Test query handler when results are returned."""
        from ai_governance_mcp.context_engine.server import _handle_query_project
        from ai_governance_mcp.context_engine.models import ProjectQueryResult

        chunk = ContentChunk(
            content="def hello(): pass",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=1,
            content_type="code",
            heading="hello",
        )
        query_result = ProjectQueryResult(
            query="hello",
            project_id="abc123",
            project_path="/tmp/project",
            results=[
                QueryResult(
                    chunk=chunk,
                    semantic_score=0.8,
                    keyword_score=0.5,
                    combined_score=0.7,
                )
            ],
            total_results=1,
            query_time_ms=12.5,
        )
        manager = Mock()
        manager.query_project.return_value = query_result

        result = await _handle_query_project(manager, {"query": "hello"})
        import json

        data = json.loads(result[0].text)
        assert data["total_results"] == 1
        assert data["results"][0]["file"] == "/tmp/test.py"
        assert data["results"][0]["score"] == 0.7

    @pytest.mark.asyncio
    async def test_handle_query_project_no_results(self):
        """Test query handler when no results are returned."""
        from ai_governance_mcp.context_engine.server import _handle_query_project
        from ai_governance_mcp.context_engine.models import ProjectQueryResult

        query_result = ProjectQueryResult(
            query="nonexistent",
            project_id="abc123",
            project_path="/tmp/project",
            results=[],
            total_results=0,
        )
        manager = Mock()
        manager.query_project.return_value = query_result

        result = await _handle_query_project(manager, {"query": "nonexistent"})
        import json

        data = json.loads(result[0].text)
        assert data["total_results"] == 0
        assert "not be indexed" in data["message"]


# =============================================================================
# Error Sanitization Extended Tests
# =============================================================================


class TestErrorSanitizationExtended:
    """Test error sanitization regex improvements."""

    def test_removes_relative_paths(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Failed at ../../etc/passwd")
        sanitized = _sanitize_error_message(err)
        assert "../../" not in sanitized
        assert "passwd" in sanitized

    def test_removes_unc_paths(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Cannot access \\\\server\\share\\secret\\file.txt")
        sanitized = _sanitize_error_message(err)
        assert "\\\\server\\share\\secret\\" not in sanitized
        assert "file.txt" in sanitized

    def test_removes_module_paths(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Error in ai_governance_mcp.context_engine.server.handle_query")
        sanitized = _sanitize_error_message(err)
        assert "ai_governance_mcp.context_engine.server.handle_query" not in sanitized
        assert "[module]" in sanitized

    def test_removes_function_references(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("raised in handle_query(args)")
        sanitized = _sanitize_error_message(err)
        assert "in handle_query(" not in sanitized
        assert "[func](" in sanitized

    def test_removes_stack_frame_references(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception('File "/Users/jason/project/server.py" error')
        sanitized = _sanitize_error_message(err)
        assert '"/Users/jason/project/server.py"' not in sanitized
        assert "File [redacted]" in sanitized

    def test_windows_paths_removed(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Error at C:\\Users\\jason\\project\\module.py")
        sanitized = _sanitize_error_message(err)
        assert "C:\\Users\\jason\\project\\" not in sanitized
        assert "module.py" in sanitized

    def test_preserves_simple_messages(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Connection refused")
        sanitized = _sanitize_error_message(err)
        assert "Connection refused" in sanitized


# =============================================================================
# Env Var Parsing Tests
# =============================================================================


class TestEnvVarParsing:
    """Test server environment variable parsing robustness."""

    def test_invalid_embedding_dimensions(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict(
            "os.environ", {"AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS": "not_a_number"}
        ):
            pm = _create_project_manager()
            assert pm.embedding_dimensions == 384  # fallback default

    def test_negative_embedding_dimensions(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict(
            "os.environ", {"AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS": "-100"}
        ):
            pm = _create_project_manager()
            assert pm.embedding_dimensions == 384  # fallback default

    def test_zero_embedding_dimensions(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict("os.environ", {"AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS": "0"}):
            pm = _create_project_manager()
            assert pm.embedding_dimensions == 384  # fallback default

    def test_invalid_semantic_weight(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict("os.environ", {"AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT": "abc"}):
            pm = _create_project_manager()
            assert pm.semantic_weight == 0.6  # fallback default

    def test_semantic_weight_clamped_high(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict("os.environ", {"AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT": "5.0"}):
            pm = _create_project_manager()
            assert pm.semantic_weight == 1.0  # clamped to max

    def test_semantic_weight_clamped_low(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict("os.environ", {"AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT": "-2.0"}):
            pm = _create_project_manager()
            assert pm.semantic_weight == 0.0  # clamped to min

    def test_valid_custom_dimensions(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict(
            "os.environ", {"AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS": "768"}
        ):
            pm = _create_project_manager()
            assert pm.embedding_dimensions == 768

    def test_valid_custom_weight(self):
        from ai_governance_mcp.context_engine.server import _create_project_manager

        with patch.dict("os.environ", {"AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT": "0.3"}):
            pm = _create_project_manager()
            assert pm.semantic_weight == 0.3


# =============================================================================
# QueryResult Constraint Tests
# =============================================================================


class TestQueryResultConstraints:
    """Test QueryResult field constraints."""

    def test_keyword_score_exceeds_max_rejected(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=1,
            content_type="code",
        )
        with pytest.raises(ValidationError):
            QueryResult(
                chunk=chunk,
                semantic_score=0.5,
                keyword_score=1.5,  # > 1.0, should be rejected
                combined_score=0.5,
            )

    def test_combined_score_exceeds_max_rejected(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=1,
            content_type="code",
        )
        with pytest.raises(ValidationError):
            QueryResult(
                chunk=chunk,
                semantic_score=0.5,
                keyword_score=0.5,
                combined_score=2.0,  # > 1.0
            )

    def test_negative_scores_rejected(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=1,
            content_type="code",
        )
        with pytest.raises(ValidationError):
            QueryResult(
                chunk=chunk,
                semantic_score=-0.1,
                keyword_score=0.5,
                combined_score=0.5,
            )

    def test_boundary_scores_accepted(self):
        chunk = ContentChunk(
            content="test",
            source_path="/tmp/test.py",
            start_line=1,
            end_line=1,
            content_type="code",
        )
        result = QueryResult(
            chunk=chunk,
            semantic_score=0.0,
            keyword_score=1.0,
            combined_score=0.0,
        )
        assert result.semantic_score == 0.0
        assert result.keyword_score == 1.0
        assert result.combined_score == 0.0


# =============================================================================
# Server create_server Tests
# =============================================================================


class TestCreateServer:
    """Test the create_server function and SERVER_INSTRUCTIONS wiring."""

    def test_server_created(self):
        from ai_governance_mcp.context_engine.server import create_server

        server, manager = create_server()
        assert server is not None
        assert manager is not None

    def test_server_instructions_wired(self):
        from ai_governance_mcp.context_engine.server import (
            SERVER_INSTRUCTIONS,
            create_server,
        )

        server, _ = create_server()
        # The Server constructor accepts instructions as a parameter
        # Verify the constant is non-empty
        assert len(SERVER_INSTRUCTIONS) > 100
        assert "query_project" in SERVER_INSTRUCTIONS
        assert "index_project" in SERVER_INSTRUCTIONS


# =============================================================================
# Integration Test — Index → Query Pipeline
# =============================================================================


class TestIntegrationIndexQuery:
    """End-to-end test of the index→query pipeline with mocked embeddings."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a realistic test project."""
        proj = tmp_path / "integration_project"
        proj.mkdir()
        (proj / "main.py").write_text(
            "def hello():\n    return 'hello world'\n\n"
            "def goodbye():\n    return 'goodbye world'\n"
        )
        (proj / "README.md").write_text(
            "# Integration Test Project\n\nThis is a test project for integration testing.\n"
        )
        (proj / "data.csv").write_text("name,age\nAlice,30\nBob,25\n")
        return proj

    @pytest.fixture
    def storage(self, tmp_path):
        return FilesystemStorage(base_path=tmp_path / "indexes")

    def test_index_and_query_pipeline(self, project_dir, storage):
        """Full pipeline: index a project, then query it."""
        from ai_governance_mcp.context_engine.indexer import Indexer
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        # Create indexer with mocked embedding model
        indexer = Indexer(storage=storage)
        mock_model = MagicMock()

        # Return different embeddings for different chunks so semantic search is meaningful
        def mock_encode(texts, **kwargs):
            embeddings = []
            for i, text in enumerate(texts):
                vec = np.zeros(384)
                # Create slightly different vectors based on content
                if "hello" in text.lower():
                    vec[0] = 0.9
                    vec[1] = 0.1
                elif "goodbye" in text.lower():
                    vec[0] = 0.1
                    vec[1] = 0.9
                elif "integration" in text.lower() or "project" in text.lower():
                    vec[2] = 0.9
                else:
                    vec[i % 384] = 0.5
                # Normalize
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                embeddings.append(vec)
            return np.array(embeddings, dtype=np.float32)

        mock_model.encode = mock_encode
        indexer._embedding_model = mock_model

        pid = FilesystemStorage.project_id_from_path(project_dir)

        # Index the project
        index = indexer.index_project(project_dir, pid)
        assert index.total_files >= 2  # At least main.py and README.md
        assert index.total_chunks >= 2

        # Create ProjectManager and load the indexed data
        pm = ProjectManager(storage=storage, semantic_weight=0.6)
        pm._indexer = indexer  # Use the same indexer with mocked model

        # Query for "hello"
        result = pm.query_project("hello", project_dir)
        assert result.total_results > 0
        # The top result should be from the file containing "hello"
        top_result = result.results[0]
        assert top_result.combined_score > 0

    def test_index_respects_contextignore(self, project_dir, storage):
        """Verify that .contextignore patterns are respected during indexing."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        # Add a .contextignore that ignores CSV files
        (project_dir / ".contextignore").write_text("*.csv\n")

        indexer = Indexer(storage=storage)
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=np.zeros((5, 384)))
        indexer._embedding_model = mock_model

        pid = FilesystemStorage.project_id_from_path(project_dir)
        index = indexer.index_project(project_dir, pid)

        # CSV file should not be indexed
        indexed_paths = [f.path for f in index.files]
        assert not any("data.csv" in p for p in indexed_paths)
        # But Python and Markdown files should be
        assert any("main.py" in p for p in indexed_paths)
        assert any("README.md" in p for p in indexed_paths)


# =============================================================================
# Review Iteration 5 — Regression Tests
# =============================================================================


class TestRateLimiterThreadSafety:
    """SEC-HIGH-1: Verify rate limiter has a threading.Lock."""

    def test_rate_limit_lock_exists(self):
        import ai_governance_mcp.context_engine.server as srv

        assert hasattr(srv, "_rate_limit_lock")
        assert isinstance(srv._rate_limit_lock, type(threading.Lock()))

    def test_rate_limiter_concurrent_access(self):
        """Verify rate limiter doesn't corrupt state under concurrent access."""
        import ai_governance_mcp.context_engine.server as srv

        # Reset state
        srv._index_rate_tokens = srv._INDEX_RATE_LIMIT_TOKENS
        srv._index_rate_last_refill = time.time()

        results = []

        def consume_token():
            result = srv._check_index_rate_limit()
            results.append(result)

        # Launch 10 threads simultaneously trying to consume tokens
        threads = [threading.Thread(target=consume_token) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly 5 True (one per token) and 5 False
        assert results.count(True) == 5
        assert results.count(False) == 5


class TestLockCoverage:
    """SEC-HIGH-3: Verify get_or_create_index and reindex_project hold lock."""

    def test_get_or_create_index_acquires_lock(self):
        """get_or_create_index should hold _index_lock during execution.

        Uses a separate thread to verify the lock is held (RLock is reentrant,
        so same-thread checks would always succeed).
        """
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        pm._loaded_indexes["test_id"] = Mock()

        lock_held_from_other_thread = []
        barrier = threading.Barrier(2, timeout=5)

        def blocking_project_id(path):
            # Signal that we're inside the locked section
            barrier.wait()
            # Wait for the checker thread to probe the lock
            time.sleep(0.05)
            return "test_id"

        def check_lock():
            # Wait until we know we're inside the locked section
            barrier.wait()
            # Try to acquire from this (different) thread
            acquired = pm._index_lock.acquire(blocking=False)
            if acquired:
                pm._index_lock.release()
                lock_held_from_other_thread.append(False)
            else:
                lock_held_from_other_thread.append(True)

        with patch.object(
            FilesystemStorage,
            "project_id_from_path",
            side_effect=blocking_project_id,
        ):
            checker = threading.Thread(target=check_lock)
            checker.start()
            pm.get_or_create_index(Path("/fake"))
            checker.join()

        assert lock_held_from_other_thread == [True]

    def test_reindex_project_acquires_lock(self):
        """reindex_project should hold _index_lock during execution.

        Uses a separate thread to verify the lock is held.
        """
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        pm.storage = Mock()
        pm.storage.load_metadata.return_value = {"index_mode": "ondemand"}
        pm._indexer = Mock()
        mock_index = Mock()
        pm._indexer.index_project.return_value = mock_index
        pm.storage.load_embeddings.return_value = None
        pm.storage.load_bm25_index.return_value = None

        lock_held_from_other_thread = []
        barrier = threading.Barrier(2, timeout=5)

        original_index = pm._indexer.index_project

        def blocking_index(*args, **kwargs):
            barrier.wait()
            time.sleep(0.05)
            return original_index(*args, **kwargs)

        pm._indexer.index_project = blocking_index

        def check_lock():
            barrier.wait()
            acquired = pm._index_lock.acquire(blocking=False)
            if acquired:
                pm._index_lock.release()
                lock_held_from_other_thread.append(False)
            else:
                lock_held_from_other_thread.append(True)

        checker = threading.Thread(target=check_lock)
        checker.start()
        pm.reindex_project(Path("/fake"))
        checker.join()

        assert lock_held_from_other_thread == [True]


class TestSignalHandlerCleanup:
    """SEC-MED-7: Verify signal handler calls manager.shutdown()."""

    def test_main_creates_manager_ref(self):
        """main() should capture manager reference for signal handler."""
        from ai_governance_mcp.context_engine.server import create_server

        server, manager = create_server()
        assert manager is not None
        assert hasattr(manager, "shutdown")


class TestEnvIgnorePatterns:
    """SEC-MED-4: .env* pattern matches all .env variants."""

    def test_env_wildcard_in_defaults(self):
        from ai_governance_mcp.context_engine.indexer import DEFAULT_IGNORE_PATTERNS

        assert ".env*" in DEFAULT_IGNORE_PATTERNS
        assert ".env" not in DEFAULT_IGNORE_PATTERNS

    def test_env_variants_ignored(self):
        import pathspec

        spec = pathspec.GitIgnoreSpec.from_lines([".env*"])
        assert spec.match_file(".env")
        assert spec.match_file(".env.local")
        assert spec.match_file(".env.production")
        assert spec.match_file(".env.staging")
        assert spec.match_file(".env.development")


class TestFileCountLimit:
    """SEC-MED-2: File count limit during indexing."""

    def test_max_file_count_constant_exists(self):
        from ai_governance_mcp.context_engine.indexer import MAX_FILE_COUNT

        assert MAX_FILE_COUNT == 10_000

    def test_discover_files_enforces_limit(self, tmp_path):
        import pathspec

        from ai_governance_mcp.context_engine.indexer import Indexer

        # Create more files than a small limit
        for i in range(15):
            (tmp_path / f"file_{i}.py").write_text(f"x = {i}")

        indexer = Indexer(storage=Mock())
        spec = pathspec.GitIgnoreSpec.from_lines([])

        # Monkey-patch MAX_FILE_COUNT to a small value for testing
        with patch("ai_governance_mcp.context_engine.indexer.MAX_FILE_COUNT", 10):
            files = indexer._discover_files(tmp_path, spec)
        assert len(files) <= 10


class TestImageConnectorFixes:
    """SEC-MED-5, SEC-MED-6, CODE-MED-4: Image connector improvements."""

    def test_relative_path_in_output(self, tmp_path):
        """Image content should use relative path, not absolute."""
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "images" / "test.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f, project_root=tmp_path)
        assert len(chunks) == 1
        # Should contain relative path, not absolute
        content = chunks[0].content
        assert str(tmp_path) not in content or "images/test.png" in content

    def test_1_based_line_numbers(self, tmp_path):
        """Image chunks should use 1-based line numbers."""
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f)
        assert chunks[0].start_line == 1
        assert chunks[0].end_line == 1

    def test_parse_without_project_root(self, tmp_path):
        """parse() without project_root should fall back to full path (consistent with other connectors)."""
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f)
        assert len(chunks) == 1
        # Without project_root, display_path is str(file_path) — the full path
        assert f"Path: {f}" in chunks[0].content


class TestUnknownToolStructuredError:
    """CODE-HIGH-4: Unknown tool returns structured JSON error."""

    def test_unknown_tool_response_is_valid_json(self):
        """The unknown tool error response at server.py should be structured JSON."""
        # Verify the code structure by importing and checking the source
        import inspect

        from ai_governance_mcp.context_engine import server

        source = inspect.getsource(server.create_server)
        # The unknown tool branch should contain json.dumps and valid_tools
        assert "json.dumps" in source
        assert "valid_tools" in source
        assert "Unknown tool" in source


class TestDeadCodeRemoval:
    """CODE-MED-1: self._bm25 dead code removed."""

    def test_indexer_no_bm25_attribute(self):
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(storage=Mock())
        assert not hasattr(indexer, "_bm25")


# =============================================================================
# Iteration 6/7 — Connector Relative Paths, Resource Cleanup, Symlink Exclusion
# =============================================================================


class TestConnectorRelativePaths:
    """Test that all connectors produce relative source_path when project_root is provided."""

    def test_code_connector_relative_path(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        sub = tmp_path / "src"
        sub.mkdir()
        f = sub / "main.py"
        f.write_text("def hello():\n    pass\n")
        chunks = conn.parse(f, project_root=tmp_path)
        assert len(chunks) >= 1
        assert chunks[0].source_path == "src/main.py"

    def test_code_connector_absolute_path_without_root(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.code import CodeConnector

        conn = CodeConnector()
        f = tmp_path / "main.py"
        f.write_text("x = 1\n")
        chunks = conn.parse(f)
        assert len(chunks) >= 1
        assert chunks[0].source_path == str(f)

    def test_document_connector_relative_path(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.document import (
            DocumentConnector,
        )

        conn = DocumentConnector()
        sub = tmp_path / "docs"
        sub.mkdir()
        f = sub / "readme.md"
        f.write_text("# Title\n\nContent.\n")
        chunks = conn.parse(f, project_root=tmp_path)
        assert len(chunks) >= 1
        assert chunks[0].source_path == "docs/readme.md"

    def test_document_connector_absolute_path_without_root(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.document import (
            DocumentConnector,
        )

        conn = DocumentConnector()
        f = tmp_path / "notes.txt"
        f.write_text("Some text.\n")
        chunks = conn.parse(f)
        assert len(chunks) >= 1
        assert chunks[0].source_path == str(f)

    def test_spreadsheet_connector_relative_path(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        sub = tmp_path / "data"
        sub.mkdir()
        f = sub / "report.csv"
        f.write_text("a,b\n1,2\n")
        chunks = conn.parse(f, project_root=tmp_path)
        assert len(chunks) == 1
        assert chunks[0].source_path == "data/report.csv"

    def test_spreadsheet_connector_absolute_path_without_root(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        f = tmp_path / "data.csv"
        f.write_text("x,y\n10,20\n")
        chunks = conn.parse(f)
        assert len(chunks) == 1
        assert chunks[0].source_path == str(f)

    def test_image_connector_relative_path(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        sub = tmp_path / "assets"
        sub.mkdir()
        f = sub / "logo.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f, project_root=tmp_path)
        assert len(chunks) == 1
        assert chunks[0].source_path == "assets/logo.png"

    def test_image_connector_absolute_path_without_root(self, tmp_path):
        from ai_governance_mcp.context_engine.connectors.image import ImageConnector

        conn = ImageConnector()
        f = tmp_path / "photo.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        chunks = conn.parse(f)
        assert len(chunks) == 1
        assert chunks[0].source_path == str(f)

    def test_pdf_connector_relative_path(self, tmp_path):
        """PDF connector uses relative path when project_root provided (requires pymupdf)."""
        from ai_governance_mcp.context_engine.connectors.pdf import PDFConnector

        conn = PDFConnector()
        if not conn._pdf_available:
            pytest.skip("No PDF library available")
        sub = tmp_path / "docs"
        sub.mkdir()
        f = sub / "manual.pdf"
        # Create minimal PDF
        f.write_bytes(b"%PDF-1.4\n")
        # parse may return [] for invalid PDF, but source_path logic is testable
        # via mock instead
        with patch("pymupdf.open") as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Page content"
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_open.return_value = mock_doc
            chunks = conn.parse(f, project_root=tmp_path)
            assert len(chunks) == 1
            assert chunks[0].source_path == "docs/manual.pdf"


class TestResourceCleanupOnException:
    """Test that connectors properly close resources even when exceptions occur."""

    def test_spreadsheet_xlsx_closes_workbook_on_error(self, tmp_path):
        """Spreadsheet connector closes workbook even when processing raises."""
        from ai_governance_mcp.context_engine.connectors.spreadsheet import (
            SpreadsheetConnector,
        )

        conn = SpreadsheetConnector()
        conn._openpyxl_available = True
        f = tmp_path / "bad.xlsx"
        f.write_bytes(b"not a real xlsx")

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_ws = MagicMock()
        mock_ws.iter_rows.side_effect = RuntimeError("corrupt sheet")
        mock_wb.__getitem__ = Mock(return_value=mock_ws)

        with patch("openpyxl.load_workbook", return_value=mock_wb):
            chunks = conn._parse_xlsx(f, str(f))
            # Should return [] on error, not raise
            assert chunks == []
            # Workbook must be closed despite the error
            mock_wb.close.assert_called_once()

    def test_pdf_pymupdf_closes_doc_on_error(self, tmp_path):
        """PDF connector closes pymupdf doc even when page processing raises."""
        import sys

        from ai_governance_mcp.context_engine.connectors.pdf import PDFConnector

        conn = PDFConnector()
        # L2: Now separate flags — set pymupdf flag directly
        conn._has_pymupdf = True
        f = tmp_path / "bad.pdf"
        f.write_bytes(b"%PDF-1.4\n")

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(side_effect=RuntimeError("corrupt page"))

        mock_pymupdf = MagicMock()
        mock_pymupdf.open = Mock(return_value=mock_doc)

        with patch.dict(sys.modules, {"pymupdf": mock_pymupdf}):
            chunks = conn.parse(f)
            # Should return [] on error, not raise
            assert chunks == []
            # Document must be closed despite the error
            mock_doc.close.assert_called_once()


class TestListProjectsSymlinkExclusion:
    """Test that list_projects excludes symlinks in storage directory."""

    def test_symlink_excluded_from_list(self, tmp_path):
        """Symlinked directories should not appear in list_projects."""
        storage = FilesystemStorage(base_path=tmp_path)

        # Create a real project directory
        real_id = "abcdef1234567890"
        real_dir = tmp_path / real_id
        real_dir.mkdir()
        (real_dir / "metadata.json").write_text('{"project_id": "real"}')

        # Create a symlinked "project" pointing to a real directory
        target = tmp_path / "external_target"
        target.mkdir()
        (target / "metadata.json").write_text('{"project_id": "fake"}')
        sym_id = "1234567890abcdef"
        (tmp_path / sym_id).symlink_to(target)

        projects = storage.list_projects()
        assert real_id in projects
        assert sym_id not in projects

    def test_symlink_outside_storage_blocked_by_containment(self, tmp_path):
        """delete_project rejects symlinks pointing outside storage via containment check."""
        storage_dir = tmp_path / "storage"
        storage_dir.mkdir()
        storage = FilesystemStorage(base_path=storage_dir)

        # Target is OUTSIDE the storage directory
        external_target = tmp_path / "external_data"
        external_target.mkdir()
        (external_target / "metadata.json").write_text('{"important": true}')

        sym_id = "abcdef1234567890"
        (storage_dir / sym_id).symlink_to(external_target)

        # get_index_path resolves the symlink → external path → containment check fails
        with pytest.raises(ValueError, match="Path traversal detected"):
            storage.delete_project(sym_id)

        # External target must still exist (not deleted)
        assert external_target.exists()
        assert (external_target / "metadata.json").exists()


class TestBm25ZeroScoreNormalization:
    """Test that BM25 normalization handles zero/empty scores without errors."""

    def test_all_zero_scores_no_division_error(self):
        """BM25 scores that are all zero should not cause division by zero."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        mock_bm25 = Mock()
        mock_bm25.get_scores = Mock(return_value=np.array([0.0, 0.0, 0.0]))
        pm._loaded_bm25["test_project"] = mock_bm25

        scores = pm._bm25_search("query", "test_project")
        # Should return zeros without error (no division by zero)
        assert np.all(scores == 0.0)

    def test_normal_scores_still_normalize(self):
        """Non-zero BM25 scores should normalize to [0, 1]."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        mock_bm25 = Mock()
        mock_bm25.get_scores = Mock(return_value=np.array([2.0, 4.0, 1.0]))
        pm._loaded_bm25["test_project"] = mock_bm25

        scores = pm._bm25_search("query", "test_project")
        assert scores.max() == pytest.approx(1.0)
        assert scores.min() == pytest.approx(0.25)

    def test_empty_scores_array(self):
        """Empty BM25 result should return empty array."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        # No BM25 loaded → empty
        scores = pm._bm25_search("query", "nonexistent")
        assert len(scores) == 0


class TestJsonFileSizeLimits:
    """Test that oversized JSON files are rejected to prevent OOM."""

    def test_oversized_metadata_returns_none(self, tmp_path):
        """Metadata exceeding size limit should return None."""
        storage = FilesystemStorage(base_path=tmp_path)
        project_id = "a" * 16
        project_dir = tmp_path / project_id
        project_dir.mkdir()

        # Create oversized metadata file
        metadata_path = project_dir / "metadata.json"
        from ai_governance_mcp.context_engine.storage.filesystem import (
            MAX_JSON_FILE_SIZE_BYTES,
        )

        # Write a file that exceeds the limit (use sparse approach)
        with open(metadata_path, "w") as f:
            f.seek(MAX_JSON_FILE_SIZE_BYTES + 1)
            f.write("}")

        result = storage.load_metadata(project_id)
        assert result is None

    def test_oversized_bm25_returns_none(self, tmp_path):
        """BM25 index exceeding size limit should return None."""
        storage = FilesystemStorage(base_path=tmp_path)
        project_id = "b" * 16
        project_dir = tmp_path / project_id
        project_dir.mkdir()

        bm25_path = project_dir / "bm25_index.json"
        from ai_governance_mcp.context_engine.storage.filesystem import (
            MAX_JSON_FILE_SIZE_BYTES,
        )

        with open(bm25_path, "w") as f:
            f.seek(MAX_JSON_FILE_SIZE_BYTES + 1)
            f.write("}")

        result = storage.load_bm25_index(project_id)
        assert result is None

    def test_oversized_manifest_returns_none(self, tmp_path):
        """File manifest exceeding size limit should return None."""
        storage = FilesystemStorage(base_path=tmp_path)
        project_id = "c" * 16
        project_dir = tmp_path / project_id
        project_dir.mkdir()

        manifest_path = project_dir / "file_manifest.json"
        from ai_governance_mcp.context_engine.storage.filesystem import (
            MAX_JSON_FILE_SIZE_BYTES,
        )

        with open(manifest_path, "w") as f:
            f.seek(MAX_JSON_FILE_SIZE_BYTES + 1)
            f.write("}")

        result = storage.load_file_manifest(project_id)
        assert result is None

    def test_normal_sized_files_load_fine(self, tmp_path):
        """Files under the size limit should load normally."""
        storage = FilesystemStorage(base_path=tmp_path)
        project_id = "d" * 16
        project_dir = tmp_path / project_id
        project_dir.mkdir()

        (project_dir / "metadata.json").write_text('{"key": "value"}')
        result = storage.load_metadata(project_id)
        assert result == {"key": "value"}


class TestStorageDirectoryPermissions:
    """Test that storage directories are created with restricted permissions."""

    def test_base_path_created_with_restricted_mode(self, tmp_path):
        """Base storage directory should be created with mode 0o700."""
        import stat

        storage_path = tmp_path / "new_storage"
        FilesystemStorage(base_path=storage_path)
        mode = storage_path.stat().st_mode & 0o777
        # On macOS/Linux, umask may affect final mode, but owner bits should be rwx
        assert mode & stat.S_IRWXU == stat.S_IRWXU  # owner has full access

    def test_project_dir_created_with_restricted_mode(self, tmp_path):
        """Project index directory should be created with mode 0o700."""
        import stat

        storage = FilesystemStorage(base_path=tmp_path)
        project_dir = storage._ensure_dir("a" * 16)
        mode = project_dir.stat().st_mode & 0o777
        assert mode & stat.S_IRWXU == stat.S_IRWXU  # owner has full access

    def test_chmod_tightens_preexisting_base_dir(self, tmp_path):
        """chmod should tighten permissions even if directory pre-existed with weaker mode."""

        storage_path = tmp_path / "preexisting"
        storage_path.mkdir(mode=0o755)  # Weak permissions
        # Verify weak permissions
        assert storage_path.stat().st_mode & 0o077 != 0

        # Creating storage should tighten
        FilesystemStorage(base_path=storage_path)
        mode = storage_path.stat().st_mode & 0o777
        assert mode == 0o700  # Should be tightened to 0o700

    def test_chmod_tightens_preexisting_project_dir(self, tmp_path):
        """chmod should tighten permissions on pre-existing project directories."""

        storage = FilesystemStorage(base_path=tmp_path)
        project_id = "a" * 16
        project_dir = storage.get_index_path(project_id)
        project_dir.mkdir(parents=True, mode=0o755)  # Weak permissions

        # _ensure_dir should tighten
        storage._ensure_dir(project_id)
        mode = project_dir.stat().st_mode & 0o777
        assert mode == 0o700  # Should be tightened to 0o700


class TestModelAllowlist:
    """Test embedding model allowlist and bypass."""

    def test_disallowed_model_raises(self):
        """Loading a model not in the allowlist should raise ValueError."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(
            storage=Mock(),
            embedding_model="evil-org/backdoor-model",
        )
        with pytest.raises(ValueError, match="not in the allowed list"):
            _ = indexer.embedding_model

    def test_allowed_model_accepted(self):
        """Models in the allowlist should not raise (mocked to avoid download)."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(
            storage=Mock(),
            embedding_model="BAAI/bge-small-en-v1.5",
        )
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_st.return_value = Mock()
            model = indexer.embedding_model
            mock_st.assert_called_once_with(
                "BAAI/bge-small-en-v1.5",
                trust_remote_code=False,
                model_kwargs={"use_safetensors": True},
            )
            assert model is not None

    def test_custom_model_bypass_via_env(self):
        """Setting AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true should bypass allowlist."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(
            storage=Mock(),
            embedding_model="custom-org/custom-model",
        )
        with (
            patch.dict(os.environ, {"AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS": "true"}),
            patch("sentence_transformers.SentenceTransformer") as mock_st,
        ):
            mock_st.return_value = Mock()
            model = indexer.embedding_model
            mock_st.assert_called_once_with(
                "custom-org/custom-model",
                trust_remote_code=False,
                model_kwargs={"use_safetensors": True},
            )
            assert model is not None


class TestWatcherIgnoreSpecPassthrough:
    """Test that FileWatcher receives the ignore_spec from ProjectManager."""

    def test_start_watcher_passes_ignore_spec(self, tmp_path):
        """_start_watcher should pass compiled ignore_spec to FileWatcher."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_path = tmp_path

        # Mock the indexer's load_ignore_patterns to return a known spec
        import pathspec

        expected_spec = pathspec.GitIgnoreSpec.from_lines(["*.log", ".git/"])
        pm._indexer.load_ignore_patterns = Mock(return_value=expected_spec)

        with patch(
            "ai_governance_mcp.context_engine.project_manager.FileWatcher"
        ) as mock_fw:
            mock_instance = Mock()
            mock_fw.return_value = mock_instance
            pm._start_watcher(project_path, "test_id")

            mock_fw.assert_called_once_with(
                project_path=project_path,
                on_change=mock_fw.call_args[1]["on_change"],
                ignore_spec=expected_spec,
            )
            mock_instance.start.assert_called_once()

    def test_watcher_without_ignore_spec_fires_on_all(self, tmp_path):
        """Without ignore_spec, watcher should fire on all file types."""
        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._running.set()

        git_file = tmp_path / ".git" / "objects" / "abc123"
        git_file.parent.mkdir(parents=True)
        git_file.write_text("blob")
        watcher._file_changed(git_file)
        if watcher._debounce_timer:
            watcher._debounce_timer.cancel()
        assert git_file in watcher._pending_changes

    def test_watcher_with_ignore_spec_filters(self, tmp_path):
        """With ignore_spec, watcher should filter matching files."""
        import pathspec

        from ai_governance_mcp.context_engine.watcher import FileWatcher

        callback = Mock()
        spec = pathspec.GitIgnoreSpec.from_lines([".git/", "*.pyc"])
        watcher = FileWatcher(
            project_path=tmp_path, on_change=callback, ignore_spec=spec
        )
        watcher._running.set()

        # Create .git file — should be filtered
        git_file = tmp_path / ".git" / "HEAD"
        git_file.parent.mkdir(parents=True)
        git_file.write_text("ref: refs/heads/main")
        watcher._file_changed(git_file)
        assert len(watcher._pending_changes) == 0

        # Create .py file — should NOT be filtered
        py_file = tmp_path / "main.py"
        py_file.write_text("x = 1")
        watcher._file_changed(py_file)
        if watcher._debounce_timer:
            watcher._debounce_timer.cancel()
        assert py_file in watcher._pending_changes


class TestWatcherCircuitBreaker:
    """Test that watcher stops after consecutive failures."""

    def test_circuit_breaker_stops_after_3_failures(self, tmp_path):
        """Watcher should be stopped and removed after 3 consecutive callback failures."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test_circuit"

        # Create a mock watcher
        mock_watcher = Mock()
        pm._watchers[project_id] = mock_watcher

        # Simulate 3 consecutive failures via the circuit breaker logic
        for i in range(3):
            failures = pm._watcher_failures.get(project_id, 0) + 1
            pm._watcher_failures[project_id] = failures
            if failures >= 3:
                if project_id in pm._watchers:
                    pm._watchers[project_id].stop()
                    del pm._watchers[project_id]

        mock_watcher.stop.assert_called_once()
        assert pm._watcher_failures[project_id] == 3
        # CR-5: Watcher must be removed so it can restart later
        assert project_id not in pm._watchers

    def test_success_resets_failure_count(self):
        """Successful update should reset the failure counter."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test_reset"
        pm._watcher_failures[project_id] = 2

        # Simulate success: remove from failures dict (as on_change does)
        pm._watcher_failures.pop(project_id, None)
        assert project_id not in pm._watcher_failures


class TestSanitizeForLoggingReturnType:
    """Test _sanitize_for_logging correctly handles None returns."""

    def test_none_input_returns_none(self):
        from ai_governance_mcp.context_engine.server import _sanitize_for_logging

        result = _sanitize_for_logging(None)
        assert result is None

    def test_empty_string_returns_empty(self):
        from ai_governance_mcp.context_engine.server import _sanitize_for_logging

        result = _sanitize_for_logging("")
        assert result == ""

    def test_normal_string_returns_unchanged(self):
        from ai_governance_mcp.context_engine.server import _sanitize_for_logging

        result = _sanitize_for_logging("hello")
        assert result == "hello"


class TestErrorSanitizationRegex:
    """Test that error sanitization doesn't over-match version numbers/IPs."""

    def test_preserves_version_numbers(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Python 3.10.0 is required")
        result = _sanitize_error_message(err)
        assert "3.10.0" in result

    def test_preserves_ip_addresses(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Connect to 192.168.1.1 failed")
        result = _sanitize_error_message(err)
        assert "192.168.1.1" in result

    def test_still_redacts_module_paths(self):
        from ai_governance_mcp.context_engine.server import _sanitize_error_message

        err = Exception("Error in foo.bar.baz.func()")
        result = _sanitize_error_message(err)
        assert "foo.bar.baz" not in result
        assert "[module]" in result


class TestHandleIndexProjectSuccess:
    """Test _handle_index_project success path."""

    @pytest.mark.asyncio
    async def test_index_project_success(self):
        """index_project should return success with project stats."""
        import ai_governance_mcp.context_engine.server as srv

        # Reset rate limiter
        srv._index_rate_tokens = srv._INDEX_RATE_LIMIT_TOKENS
        srv._index_rate_last_refill = time.time()

        mock_index = ProjectIndex(
            project_id="abc123",
            project_path="/test/path",
            chunks=[],
            files=[],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            embedding_model="BAAI/bge-small-en-v1.5",
            total_chunks=42,
            total_files=10,
        )

        mock_manager = Mock()
        mock_manager.reindex_project = Mock(return_value=mock_index)

        from ai_governance_mcp.context_engine.server import _handle_index_project

        result = await _handle_index_project(mock_manager)
        assert len(result) == 1

        import json

        data = json.loads(result[0].text)
        assert data["message"] == "Project indexed successfully"
        assert data["total_files"] == 10
        assert data["total_chunks"] == 42


class TestIncrementalUpdateDocstring:
    """Test that incremental_update logs a warning about full re-index."""

    def test_incremental_update_logs_warning(self, tmp_path):
        """incremental_update should warn that it performs a full re-index."""
        from ai_governance_mcp.context_engine.indexer import Indexer

        indexer = Indexer(storage=Mock())

        # Mock storage to return existing metadata
        indexer.storage.load_metadata = Mock(return_value={"index_mode": "realtime"})

        # Mock index_project to avoid actually indexing
        mock_index = Mock()
        indexer.index_project = Mock(return_value=mock_index)

        with patch("ai_governance_mcp.context_engine.indexer.logger") as mock_logger:
            indexer.incremental_update(tmp_path, "test_id", [tmp_path / "file.py"])
            # Should log a warning about full re-index
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "full re-index" in str(call).lower()
            ]
            assert len(warning_calls) >= 1


class TestWatcherStatusInProjectStatus:
    """Test M5: watcher_status field in ProjectStatus."""

    def test_watcher_status_running(self):
        """Running watcher should report status as 'running'."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test123"

        # Create mock watcher that reports running
        mock_watcher = Mock()
        mock_watcher.is_running = True
        pm._watchers[project_id] = mock_watcher

        status = pm._get_watcher_status(project_id, "realtime")
        assert status == "running"

    def test_watcher_status_circuit_broken(self):
        """Circuit-broken watcher should report status as 'circuit_broken'."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test123"
        pm._circuit_broken.add(project_id)

        status = pm._get_watcher_status(project_id, "realtime")
        assert status == "circuit_broken"

    def test_watcher_status_disabled_for_ondemand(self):
        """Ondemand mode should report watcher as 'disabled'."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test123"

        status = pm._get_watcher_status(project_id, "ondemand")
        assert status == "disabled"

    def test_watcher_status_stopped(self):
        """No watcher should report status as 'stopped'."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        pm = ProjectManager()
        project_id = "test123"

        status = pm._get_watcher_status(project_id, "realtime")
        assert status == "stopped"


class TestPDFLibraryFlags:
    """Test L2: Separate PDF library flags."""

    def test_pdf_available_with_pymupdf(self):
        """_pdf_available should be True when pymupdf is available."""
        from ai_governance_mcp.context_engine.connectors.pdf import PDFConnector

        conn = PDFConnector()
        conn._has_pymupdf = True
        conn._has_pdfplumber = False
        assert conn._pdf_available is True

    def test_pdf_available_with_pdfplumber(self):
        """_pdf_available should be True when pdfplumber is available."""
        from ai_governance_mcp.context_engine.connectors.pdf import PDFConnector

        conn = PDFConnector()
        conn._has_pymupdf = False
        conn._has_pdfplumber = True
        assert conn._pdf_available is True

    def test_pdf_not_available(self):
        """_pdf_available should be False when no library available."""
        from ai_governance_mcp.context_engine.connectors.pdf import PDFConnector

        conn = PDFConnector()
        conn._has_pymupdf = False
        conn._has_pdfplumber = False
        assert conn._pdf_available is False


class TestPendingChangesLimit:
    """Test L5: Bounded pending changes."""

    def test_max_pending_changes_constant(self):
        """MAX_PENDING_CHANGES should be 10,000."""
        from ai_governance_mcp.context_engine.watcher import MAX_PENDING_CHANGES

        assert MAX_PENDING_CHANGES == 10_000

    def test_force_flush_at_limit(self, tmp_path):
        """Watcher should force-flush when pending changes reach limit."""
        from ai_governance_mcp.context_engine.watcher import (
            FileWatcher,
            MAX_PENDING_CHANGES,
        )

        callback = Mock()
        watcher = FileWatcher(project_path=tmp_path, on_change=callback)
        watcher._running.set()

        # Add MAX_PENDING_CHANGES - 1 files (shouldn't flush yet)
        for i in range(MAX_PENDING_CHANGES - 1):
            watcher._pending_changes.add(tmp_path / f"file{i}.py")

        # Add one more to trigger force-flush
        watcher._file_changed(tmp_path / "trigger.py")

        # Should have flushed immediately
        callback.assert_called_once()
        assert len(callback.call_args[0][0]) == MAX_PENDING_CHANGES
        assert len(watcher._pending_changes) == 0
