"""Unit tests for agent install/uninstall handlers.

Extracted from test_server.py during server package decomposition (Phase 3).
Covers: install_agent, uninstall_agent, Claude Code detection, project path
resolution, agent overwrite warnings, and multi-agent consistency checks.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from helpers import extract_json_from_response


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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        from ai_governance_mcp.server import _state
        from mcp.server.lowlevel.server import request_ctx

        # Reset roots cache so each test gets a fresh lookup
        _state._cached_roots_path = None

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
        from ai_governance_mcp.server import _state
        from mcp.server.lowlevel.server import request_ctx

        _state._cached_roots_path = None
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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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


class TestAgentOverwriteWarning:
    """Tests for M2 FIX: Agent overwrite content comparison."""

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        from ai_governance_mcp.server import _state

        _state._cached_roots_path = None
        yield
        _state._cached_roots_path = None

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

        result = await server_module._handle_install_agent(
            {"agent_name": "orchestrator"}
        )

        response = json.loads(result[0].text.split("---")[0])
        assert response["status"] == "preview"
        assert response["already_installed"] is False
        assert response["content_differs"] is False
        assert "warning" not in response


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

        required_keys = {
            "short_description",
            "action_summary",
            "activation_message",
            "applicable_domains",
            "canonical_source",
        }

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

    def test_agent_metadata_short_description_alignment(self):
        """AGENT_METADATA short_description terms should appear in canonical file."""
        import re

        from ai_governance_mcp.server import AGENT_METADATA, AVAILABLE_AGENTS

        project_root = Path(__file__).parent.parent
        agents_dir = project_root / "documents" / "agents"

        for agent_name in AVAILABLE_AGENTS:
            template = agents_dir / f"{agent_name}.md"
            assert template.exists(), f"Canonical file missing for '{agent_name}'"

            content = template.read_text()
            frontmatter_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            assert frontmatter_match, (
                f"No YAML frontmatter in '{agent_name}' canonical file"
            )
            frontmatter = frontmatter_match.group(1).lower()

            desc = AGENT_METADATA[agent_name]["short_description"].lower()
            significant_words = [w for w in desc.split() if len(w) >= 4]
            present = [w for w in significant_words if w in frontmatter]
            assert len(present) >= 1, (
                f"AGENT_METADATA short_description for '{agent_name}' has drifted "
                f"from canonical frontmatter. No significant terms from "
                f"'{AGENT_METADATA[agent_name]['short_description']}' found in "
                f"frontmatter description."
            )

    def test_agent_metadata_canonical_source_exists(self):
        """Every canonical_source path in AGENT_METADATA must point to a real file."""
        from ai_governance_mcp.server import AGENT_METADATA, AVAILABLE_AGENTS

        project_root = Path(__file__).parent.parent

        for agent_name in AVAILABLE_AGENTS:
            canonical = AGENT_METADATA[agent_name]["canonical_source"]
            path = project_root / canonical
            assert path.exists(), (
                f"canonical_source '{canonical}' for '{agent_name}' does not exist"
            )

    @pytest.fixture(autouse=True)
    def _reset_roots_cache(self):
        from ai_governance_mcp.server import _state

        _state._cached_roots_path = None
        yield
        _state._cached_roots_path = None

    @pytest.mark.asyncio
    async def test_non_claude_response_includes_agent_content(
        self, tmp_path, monkeypatch, real_settings
    ):
        """Non-Claude install_agent response should include agent definition content."""
        import ai_governance_mcp.server as server_module

        # No .claude dir -> non-Claude environment
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        # But need settings so template path resolves
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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
        monkeypatch.setattr(server_module._state, "_settings", real_settings)

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


class TestListAgents:
    """Tests for list_agents tool."""

    @pytest.mark.asyncio
    async def test_list_agents_returns_all_agents(self):
        """list_agents should return all 10 available agents."""
        from ai_governance_mcp.server import _handle_list_agents

        result = await _handle_list_agents({})

        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response["total_agents"] == 10
        assert len(response["agents"]) == 10

        for agent in response["agents"]:
            assert "name" in agent
            assert "short_description" in agent
            assert "applicable_domains" in agent
            assert "canonical_source" in agent
            assert "action_summary" not in agent

        assert "cross_platform_note" in response

    @pytest.mark.asyncio
    async def test_list_agents_include_details(self):
        """list_agents with include_details=True should include action_summary."""
        from ai_governance_mcp.server import _handle_list_agents

        result = await _handle_list_agents({"include_details": True})

        response = json.loads(result[0].text)
        for agent in response["agents"]:
            assert "action_summary" in agent
            assert len(agent["action_summary"]) > 0

    @pytest.mark.asyncio
    async def test_list_agents_canonical_source_paths_exist(self):
        """Every canonical_source in list_agents output must point to a real file."""
        from ai_governance_mcp.server import _handle_list_agents

        project_root = Path(__file__).parent.parent
        result = await _handle_list_agents({})
        response = json.loads(result[0].text)

        for agent in response["agents"]:
            path = project_root / agent["canonical_source"]
            assert path.exists(), (
                f"canonical_source '{agent['canonical_source']}' for "
                f"'{agent['name']}' does not exist"
            )

    @pytest.mark.asyncio
    async def test_list_agents_sorted_alphabetically(self):
        """Agents should be returned in alphabetical order."""
        from ai_governance_mcp.server import _handle_list_agents

        result = await _handle_list_agents({})
        response = json.loads(result[0].text)
        names = [a["name"] for a in response["agents"]]
        assert names == sorted(names)
