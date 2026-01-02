"""Tests for MCP configuration generator."""

import json


from ai_governance_mcp.config_generator import (
    generate_claude_config,
    generate_chatgpt_config,
    generate_gemini_config,
    generate_mcp_config,
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

    def test_uses_default_python(self):
        """Should use 'python' as default command."""
        config = generate_gemini_config()
        assert config["mcpServers"]["ai-governance"]["command"] == "python"

    def test_uses_custom_python_path(self):
        """Should use custom Python path when provided."""
        config = generate_gemini_config("/usr/local/bin/python3")
        assert (
            config["mcpServers"]["ai-governance"]["command"] == "/usr/local/bin/python3"
        )

    def test_args_include_module(self):
        """Args should specify the server module."""
        config = generate_gemini_config()
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

    def test_uses_custom_python_path(self):
        """Should use custom Python path when provided."""
        config = generate_claude_config("/opt/python")
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


class TestCLICommands:
    """Tests for CLI command generation."""

    def test_gemini_cli_command(self):
        """Should generate valid gemini mcp add command."""
        cmd = get_gemini_cli_command()
        assert "gemini mcp add" in cmd
        assert "-s user" in cmd
        assert "ai-governance" in cmd

    def test_claude_cli_command(self):
        """Should generate valid claude mcp add command."""
        cmd = get_claude_cli_command()
        assert "claude mcp add" in cmd
        assert "-s user" in cmd
        assert "ai-governance" in cmd
