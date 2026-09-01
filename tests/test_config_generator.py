"""Tests for the MCP configuration generator.

Contract (post Desktop-launch fix):
- Default is ADVISORY: ``<abs-python> -m ai_governance_mcp.server`` (no proxy).
- ``enforce=True`` wraps the server in the proxy, with an ABSOLUTE interpreter
  at BOTH levels (outer proxy + inner wrapped server) so a GUI host's minimal
  PATH never has to resolve a bare name.
- The CLI label must not oversell soft-mode enforcement.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

from ai_governance_mcp.config_generator import (
    generate_chatgpt_config,
    generate_claude_config,
    generate_cursor_config,
    generate_gemini_config,
    generate_mcp_config,
    generate_windsurf_config,
    get_claude_cli_command,
    get_gemini_cli_command,
    print_platform_config,
)

# Hermetic seam: pin the resolved interpreter so shape assertions are
# deterministic across machines + CI (mirrors test_service.py's shutil.which patch).
RESOLVE = "ai_governance_mcp.config_generator.resolve_python"
FAKE_PY = "/venv/bin/python"


def _fake_resolve(python_path=None):
    return python_path or FAKE_PY


ADVISORY_ARGS = ["-m", "ai_governance_mcp.server"]
PROXY_ARGS = [
    "-m",
    "ai_governance_mcp.enforcement",
    "--",
    FAKE_PY,
    "-m",
    "ai_governance_mcp.server",
]

JSON_GENERATORS = [
    generate_gemini_config,
    generate_claude_config,
    generate_chatgpt_config,
    generate_cursor_config,
    generate_windsurf_config,
]


class TestDefaultIsAdvisory:
    """Default (no opt-in) = direct server, no proxy, no soft-mode env."""

    @pytest.mark.parametrize("gen", JSON_GENERATORS)
    def test_default_advisory_shape(self, gen):
        with patch(RESOLVE, _fake_resolve):
            server = gen()["mcpServers"]["ai-governance"]
        assert server["command"] == FAKE_PY
        assert server["args"] == ADVISORY_ARGS
        assert "GOVERNANCE_ENFORCEMENT_SOFT_MODE" not in server["env"]

    @pytest.mark.parametrize("gen", JSON_GENERATORS)
    def test_default_command_is_absolute_unmocked(self, gen):
        # NON-mocked: a regression back to bare "python" (the original bug) is
        # caught here even though the hermetic patch above would hide it.
        server = gen()["mcpServers"]["ai-governance"]
        assert os.path.isabs(server["command"])
        assert server["command"] == sys.executable


class TestEnforceOptIn:
    """enforce=True wraps the server in the proxy with absolute python at both levels."""

    @pytest.mark.parametrize("gen", JSON_GENERATORS)
    def test_enforce_proxy_shape(self, gen):
        with patch(RESOLVE, _fake_resolve):
            server = gen(enforce=True)["mcpServers"]["ai-governance"]
        assert server["command"] == FAKE_PY
        assert server["args"] == PROXY_ARGS
        assert server["env"]["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] == "true"

    def test_enforce_wrap_order(self):
        with patch(RESOLVE, _fake_resolve):
            args = generate_claude_config(enforce=True)["mcpServers"]["ai-governance"][
                "args"
            ]
        # proxy module named, then '--', then the wrapped server module
        assert args.index("ai_governance_mcp.enforcement") < args.index("--")
        assert args.index("--") < args.index("ai_governance_mcp.server")

    @pytest.mark.parametrize("gen", JSON_GENERATORS)
    def test_enforce_both_interpreters_absolute_unmocked(self, gen):
        server = gen(enforce=True)["mcpServers"]["ai-governance"]
        assert os.path.isabs(server["command"])
        inner = server["args"][server["args"].index("--") + 1]
        assert os.path.isabs(inner)  # inner wrapped server also needs absolute python


class TestCustomPythonPath:
    """An explicit python_path flows through to command AND the inner wrapped server."""

    def test_advisory_custom_path(self):
        server = generate_claude_config("/opt/python")["mcpServers"]["ai-governance"]
        assert server["command"] == "/opt/python"
        assert server["args"] == ["-m", "ai_governance_mcp.server"]

    def test_enforce_custom_path_both_levels(self):
        server = generate_claude_config("/opt/python", enforce=True)["mcpServers"][
            "ai-governance"
        ]
        assert server["command"] == "/opt/python"
        assert server["args"] == [
            "-m",
            "ai_governance_mcp.enforcement",
            "--",
            "/opt/python",
            "-m",
            "ai_governance_mcp.server",
        ]


class TestStructure:
    def test_gemini_includes_timeout(self):
        server = generate_gemini_config()["mcpServers"]["ai-governance"]
        assert server["timeout"] == 30000

    def test_claude_no_timeout(self):
        server = generate_claude_config()["mcpServers"]["ai-governance"]
        assert "timeout" not in server

    def test_chatgpt_serializable(self):
        config = generate_chatgpt_config()
        assert json.loads(json.dumps(config)) == config

    @pytest.mark.parametrize("enforce", [False, True])
    def test_path_env_vars_present(self, enforce):
        env = generate_claude_config(enforce=enforce)["mcpServers"]["ai-governance"][
            "env"
        ]
        assert "AI_GOVERNANCE_DOCUMENTS_PATH" in env
        assert "AI_GOVERNANCE_INDEX_PATH" in env


class TestGenerateMCPConfig:
    def test_gemini_platform(self):
        config = generate_mcp_config("gemini")
        assert "timeout" in config["mcpServers"]["ai-governance"]

    def test_claude_platform(self):
        config = generate_mcp_config("claude")
        assert "timeout" not in config["mcpServers"]["ai-governance"]

    def test_chatgpt_platform(self):
        assert generate_mcp_config("chatgpt") is not None

    def test_unknown_platform_returns_none(self):
        assert generate_mcp_config("unknown") is None

    def test_superassistant_returns_none(self):
        assert generate_mcp_config("superassistant") is None

    def test_enforce_passed_through(self):
        with patch(RESOLVE, _fake_resolve):
            default = generate_mcp_config("claude")["mcpServers"]["ai-governance"]
            enforced = generate_mcp_config("claude", enforce=True)["mcpServers"][
                "ai-governance"
            ]
        assert default["args"] == ADVISORY_ARGS
        assert "ai_governance_mcp.enforcement" in enforced["args"]


class TestCLICommands:
    def test_gemini_default_is_advisory(self):
        cmd = get_gemini_cli_command()
        assert "gemini mcp add" in cmd
        assert "ai_governance_mcp.enforcement" not in cmd
        assert "-m ai_governance_mcp.server" in cmd

    def test_gemini_enforce_uses_proxy(self):
        cmd = get_gemini_cli_command(enforce=True)
        assert "ai_governance_mcp.enforcement" in cmd

    def test_claude_default_is_advisory(self):
        cmd = get_claude_cli_command()
        assert "claude mcp add" in cmd
        assert "ai_governance_mcp.enforcement" not in cmd
        assert "-m ai_governance_mcp.server" in cmd

    def test_claude_enforce_uses_proxy(self):
        cmd = get_claude_cli_command(enforce=True)
        assert "ai_governance_mcp.enforcement" in cmd

    def test_cli_quotes_interpreter_path(self):
        # Spaces in the interpreter path (e.g. "/Application Support/") must be
        # quoted so the printed shell command survives copy-paste.
        with patch(RESOLVE, lambda p=None: p or "/App Support/py"):
            cmd = get_claude_cli_command()
        assert '"/App Support/py"' in cmd


class TestLabelHonesty:
    """The CLI must not oversell soft-mode enforcement (the user's complaint)."""

    def test_enforce_label_not_oversold(self, capsys):
        print_platform_config("claude", enforce=True)
        out = capsys.readouterr().out
        assert "ENFORCED" not in out
        assert "STRUCTURAL" not in out
        assert "does not block" in out.lower()
        assert "approval" in out.lower()
        assert "ref-ai-coding-connect-local-mcp-server-to-claude-surfaces" in out

    def test_advisory_default_label(self, capsys):
        print_platform_config("claude", enforce=False)
        out = capsys.readouterr().out
        assert "ADVISORY" in out
