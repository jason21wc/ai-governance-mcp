"""Unit tests for scaffold and reference library handlers.

Extracted from test_server.py as part of server.py decomposition (Phase 3, Task 3.4).
"""

import json
from unittest.mock import Mock

import pytest


class TestScaffoldProject:
    """Tests for scaffold_project tool."""

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        from ai_governance_mcp.server import _state

        _state._cached_roots_path = None
        yield
        _state._cached_roots_path = None

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
        + .claude/skills/completion-sequence/checklist + BACKLOG). See server.py
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
        assert ".claude/skills/completion-sequence/checklist.md" in paths
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
        from ai_governance_mcp.server import _state
        from mcp.server.lowlevel.server import request_ctx

        _state._cached_roots_path = None
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
