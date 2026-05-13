"""Tests for MCP configuration generator."""

import json

import pytest

from ai_governance_mcp.config_generator import (
    generate_claude_config,
    generate_chatgpt_config,
    generate_cursor_config,
    generate_gemini_config,
    generate_mcp_config,
    generate_windsurf_config,
    get_claude_cli_command,
    get_gemini_cli_command,
)


class TestGenerateGeminiConfig:
    """Tests for Gemini CLI configuration generation."""

    def test_generates_valid_structure(self):
        """Config should have mcpServers with ai-governance."""
        config = generate_gemini_config()
        assert "mcpServers" in config
        assert "ai-governance" in config["mcpServers"]

    def test_includes_timeout(self):
        """Gemini config should include timeout setting."""
        config = generate_gemini_config()
        server = config["mcpServers"]["ai-governance"]
        assert server["timeout"] == 30000

    def test_default_uses_proxy(self):
        """Default config should use enforcement proxy."""
        config = generate_gemini_config()
        assert config["mcpServers"]["ai-governance"]["command"] == "ai-governance-proxy"

    def test_no_enforce_uses_python(self):
        """Advisory config should use python directly."""
        config = generate_gemini_config(enforce=False)
        assert config["mcpServers"]["ai-governance"]["command"] == "python"

    def test_uses_custom_python_path_in_proxy_args(self):
        """Custom python path should appear in proxy args."""
        config = generate_gemini_config("/usr/local/bin/python3")
        server = config["mcpServers"]["ai-governance"]
        assert server["command"] == "ai-governance-proxy"
        assert "/usr/local/bin/python3" in server["args"]

    def test_uses_custom_python_path_no_enforce(self):
        """Should use custom Python path as command when not enforced."""
        config = generate_gemini_config("/usr/local/bin/python3", enforce=False)
        assert (
            config["mcpServers"]["ai-governance"]["command"] == "/usr/local/bin/python3"
        )

    def test_no_enforce_args_include_module(self):
        """Advisory args should specify the server module directly."""
        config = generate_gemini_config(enforce=False)
        args = config["mcpServers"]["ai-governance"]["args"]
        assert args == ["-m", "ai_governance_mcp.server"]


class TestGenerateClaudeConfig:
    """Tests for Claude Desktop configuration generation."""

    def test_generates_valid_structure(self):
        """Config should have mcpServers with ai-governance."""
        config = generate_claude_config()
        assert "mcpServers" in config
        assert "ai-governance" in config["mcpServers"]

    def test_no_timeout(self):
        """Claude config should not include timeout."""
        config = generate_claude_config()
        server = config["mcpServers"]["ai-governance"]
        assert "timeout" not in server

    def test_uses_custom_python_path_no_enforce(self):
        """Should use custom Python path when not enforced."""
        config = generate_claude_config("/opt/python", enforce=False)
        assert config["mcpServers"]["ai-governance"]["command"] == "/opt/python"


class TestGenerateChatGPTConfig:
    """Tests for ChatGPT Desktop configuration generation."""

    def test_generates_valid_structure(self):
        """Config should have mcpServers with ai-governance."""
        config = generate_chatgpt_config()
        assert "mcpServers" in config
        assert "ai-governance" in config["mcpServers"]

    def test_serializable_to_json(self):
        """Config should be valid JSON."""
        config = generate_chatgpt_config()
        json_str = json.dumps(config)
        parsed = json.loads(json_str)
        assert parsed == config


class TestGenerateMCPConfig:
    """Tests for the unified generate_mcp_config function."""

    def test_gemini_platform(self):
        """Should generate Gemini config for 'gemini' platform."""
        config = generate_mcp_config("gemini")
        assert config is not None
        assert "timeout" in config["mcpServers"]["ai-governance"]

    def test_claude_platform(self):
        """Should generate Claude config for 'claude' platform."""
        config = generate_mcp_config("claude")
        assert config is not None
        assert "timeout" not in config["mcpServers"]["ai-governance"]

    def test_chatgpt_platform(self):
        """Should generate ChatGPT config for 'chatgpt' platform."""
        config = generate_mcp_config("chatgpt")
        assert config is not None

    def test_unknown_platform_returns_none(self):
        """Should return None for unknown platforms."""
        config = generate_mcp_config("unknown")
        assert config is None

    def test_superassistant_returns_none(self):
        """SuperAssistant has no JSON config, should return None."""
        config = generate_mcp_config("superassistant")
        assert config is None

    def test_enforce_passed_through(self):
        """generate_mcp_config should respect enforce parameter."""
        enforced = generate_mcp_config("claude", enforce=True)
        advisory = generate_mcp_config("claude", enforce=False)
        assert (
            enforced["mcpServers"]["ai-governance"]["command"] == "ai-governance-proxy"
        )
        assert advisory["mcpServers"]["ai-governance"]["command"] == "python"


class TestCLICommands:
    """Tests for CLI command generation."""

    def test_gemini_cli_command_default_uses_proxy(self):
        """Default gemini CLI command should use enforcement proxy."""
        cmd = get_gemini_cli_command()
        assert "gemini mcp add" in cmd
        assert "ai-governance-proxy" in cmd

    def test_gemini_cli_command_no_enforce(self):
        """Advisory gemini CLI command should use python directly."""
        cmd = get_gemini_cli_command(enforce=False)
        assert "ai-governance-proxy" not in cmd
        assert "python -m ai_governance_mcp.server" in cmd

    def test_claude_cli_command_default_uses_proxy(self):
        """Default claude CLI command should use enforcement proxy."""
        cmd = get_claude_cli_command()
        assert "claude mcp add" in cmd
        assert "ai-governance-proxy" in cmd

    def test_claude_cli_command_no_enforce(self):
        """Advisory claude CLI command should use python directly."""
        cmd = get_claude_cli_command(enforce=False)
        assert "ai-governance-proxy" not in cmd
        assert "python -m ai_governance_mcp.server" in cmd


class TestEnforcementProxy:
    """Tests for enforcement proxy config generation."""

    def test_enforced_config_uses_proxy_command(self):
        """Enforced configs should use ai-governance-proxy as command."""
        config = generate_claude_config(enforce=True)
        assert config["mcpServers"]["ai-governance"]["command"] == "ai-governance-proxy"

    def test_enforced_config_wraps_server_in_args(self):
        """Enforced args should wrap the server command after '--'."""
        config = generate_claude_config(enforce=True)
        args = config["mcpServers"]["ai-governance"]["args"]
        assert args[0] == "--"
        assert "-m" in args
        assert "ai_governance_mcp.server" in args

    def test_enforced_config_includes_soft_mode(self):
        """Enforced configs should include GOVERNANCE_ENFORCEMENT_SOFT_MODE."""
        config = generate_claude_config(enforce=True)
        env = config["mcpServers"]["ai-governance"]["env"]
        assert env["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] == "true"

    def test_advisory_config_no_soft_mode_env(self):
        """Advisory configs should not include enforcement env vars."""
        config = generate_claude_config(enforce=False)
        env = config["mcpServers"]["ai-governance"]["env"]
        assert "GOVERNANCE_ENFORCEMENT_SOFT_MODE" not in env

    @pytest.mark.parametrize(
        "generator",
        [
            generate_gemini_config,
            generate_claude_config,
            generate_chatgpt_config,
            generate_cursor_config,
            generate_windsurf_config,
        ],
    )
    def test_all_platforms_enforce_by_default(self, generator):
        """All platform generators should default to enforcement proxy."""
        config = generator()
        server = config["mcpServers"]["ai-governance"]
        assert server["command"] == "ai-governance-proxy"
        assert server["env"]["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] == "true"

    @pytest.mark.parametrize(
        "generator",
        [
            generate_gemini_config,
            generate_claude_config,
            generate_chatgpt_config,
            generate_cursor_config,
            generate_windsurf_config,
        ],
    )
    def test_all_platforms_advisory_mode(self, generator):
        """All platforms should produce direct-server configs with enforce=False."""
        config = generator(enforce=False)
        server = config["mcpServers"]["ai-governance"]
        assert server["command"] == "python"
        assert "GOVERNANCE_ENFORCEMENT_SOFT_MODE" not in server["env"]

    def test_enforced_config_preserves_env_vars(self):
        """Enforced configs should still include index/docs path env vars."""
        config = generate_claude_config(enforce=True)
        env = config["mcpServers"]["ai-governance"]["env"]
        assert "AI_GOVERNANCE_DOCUMENTS_PATH" in env
        assert "AI_GOVERNANCE_INDEX_PATH" in env
