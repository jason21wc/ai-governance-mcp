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
import shlex
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ai_governance_mcp import config_generator
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


@pytest.fixture
def isolated_generator_paths(monkeypatch, tmp_path):
    """Separate installed documents, launch CWD, user data, and ambient .env."""
    for name in tuple(os.environ):
        if name.startswith("AI_GOVERNANCE_"):
            monkeypatch.delenv(name)
    root = tmp_path.resolve()
    module_root, cwd, home = (root / name for name in ("installed", "launch", "home"))
    for path in (module_root / "documents", module_root / "index", cwd, home):
        path.mkdir(parents=True)
    (module_root / "documents" / "constitution.md").write_text("# Constitution\n")
    # A plausible legacy index must never override the configured/default path.
    (module_root / "index" / "global_index.json").write_text("{}")
    monkeypatch.setattr(
        config_generator, "__file__", str(module_root / "src" / "config_generator.py")
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(cwd)
    return module_root, cwd, home


class TestRuntimeIndexSelection:
    @pytest.mark.parametrize("source", ["environment", "dotenv", "default"])
    def test_library_paths_are_preserved(
        self, source, isolated_generator_paths, monkeypatch
    ):
        _, cwd, home = isolated_generator_paths
        expected = {
            "AI_GOVERNANCE_REFERENCE_LIBRARY_PATH": home
            / ".ai-governance"
            / "reference-library",
            "AI_GOVERNANCE_PRIVATE_REFERENCE_LIBRARY_PATH": home
            / ".ai-governance"
            / "private-reference-library",
        }
        if source != "default":
            expected = {key: cwd / f"library {i}" for i, key in enumerate(expected)}
            if source == "environment":
                for key, value in expected.items():
                    monkeypatch.setenv(key, str(value))
            else:
                (cwd / ".env").write_text(
                    "\n".join(
                        f"{key}={json.dumps(str(value))}"
                        for key, value in expected.items()
                    )
                )
        result = config_generator.get_env_vars()
        for key, value in expected.items():
            assert result[key] == str(value)

    @pytest.mark.parametrize(
        "case",
        [
            "explicit_present",
            "explicit_missing",
            "user_root",
            "default_home",
            "relative_index",
            "tilde_index",
            "relative_user_root",
            "tilde_user_root",
        ],
    )
    def test_index_path_precedence_and_normalization(
        self, case, isolated_generator_paths, monkeypatch
    ):
        module_root, cwd, home = isolated_generator_paths
        cases = {
            "explicit_present": ("INDEX_PATH", str(home / "built"), home / "built"),
            "explicit_missing": ("INDEX_PATH", str(home / "missing"), home / "missing"),
            "user_root": (
                "USER_DATA_ROOT",
                str(home / "data"),
                home / "data" / "index",
            ),
            "default_home": (None, None, home / ".ai-governance" / "index"),
            "relative_index": ("INDEX_PATH", "relative-index", cwd / "relative-index"),
            "tilde_index": ("INDEX_PATH", "~/selected-index", home / "selected-index"),
            "relative_user_root": ("USER_DATA_ROOT", "data", cwd / "data" / "index"),
            "tilde_user_root": ("USER_DATA_ROOT", "~/data", home / "data" / "index"),
        }
        key, value, expected = cases[case]
        if key is not None:
            monkeypatch.setenv(f"AI_GOVERNANCE_{key}", value)
        if case.startswith("explicit_"):
            monkeypatch.setenv("AI_GOVERNANCE_USER_DATA_ROOT", str(home / "other-data"))
        if case == "explicit_present":
            expected.mkdir()
            (expected / "global_index.json").write_text("{}")

        env = config_generator.get_env_vars()

        assert env["AI_GOVERNANCE_INDEX_PATH"] == str(expected)
        assert env["AI_GOVERNANCE_DOCUMENTS_PATH"] == str(module_root / "documents")
        if case == "explicit_missing":
            assert not expected.exists()  # No silent fallback or creation.

    @pytest.mark.parametrize("environment_override", [False, True])
    def test_dotenv_index_is_below_process_environment(
        self, environment_override, isolated_generator_paths, monkeypatch
    ):
        _, cwd, home = isolated_generator_paths
        (cwd / ".env").write_text("AI_GOVERNANCE_INDEX_PATH=./dotenv-index\n")
        expected = cwd / "dotenv-index"
        if environment_override:
            expected = home / "process-index"
            monkeypatch.setenv("AI_GOVERNANCE_INDEX_PATH", str(expected))
        assert config_generator.get_env_vars()["AI_GOVERNANCE_INDEX_PATH"] == str(
            expected
        )

    def test_dotenv_user_data_root_does_not_gain_new_support(
        self, isolated_generator_paths
    ):
        _, cwd, home = isolated_generator_paths
        (cwd / ".env").write_text("AI_GOVERNANCE_USER_DATA_ROOT=./dotenv-data\n")
        assert config_generator.get_env_vars()["AI_GOVERNANCE_INDEX_PATH"] == str(
            home / ".ai-governance" / "index"
        )

    def test_module_documents_keep_precedence_over_ambient_paths(
        self, isolated_generator_paths, monkeypatch
    ):
        module_root, cwd, home = isolated_generator_paths
        monkeypatch.setenv("AI_GOVERNANCE_DOCUMENTS_PATH", str(home / "ambient-docs"))
        (cwd / ".env").write_text("AI_GOVERNANCE_DOCUMENTS_PATH=./dotenv-docs\n")
        (cwd / "documents").mkdir()
        (cwd / "documents" / "constitution.md").write_text("# Unrelated project\n")
        assert config_generator.get_env_vars()["AI_GOVERNANCE_DOCUMENTS_PATH"] == str(
            module_root / "documents"
        )

    def test_invalid_runtime_setting_is_not_silently_ignored(
        self, isolated_generator_paths, monkeypatch
    ):
        monkeypatch.setenv("AI_GOVERNANCE_EMBEDDING_DIMENSIONS", "not-an-integer")
        with pytest.raises(ValidationError, match="embedding_dimensions"):
            config_generator.get_env_vars()

    @pytest.mark.parametrize("enforce", [False, True])
    @pytest.mark.parametrize(
        "emit", [*JSON_GENERATORS, get_claude_cli_command, get_gemini_cli_command]
    )
    def test_every_emitter_uses_the_selected_index(
        self, emit, enforce, isolated_generator_paths, monkeypatch
    ):
        _, _, home = isolated_generator_paths
        selected = home / "index with spaces"
        monkeypatch.setenv("AI_GOVERNANCE_INDEX_PATH", str(selected))
        result = emit(enforce=enforce, python_path=FAKE_PY)
        if isinstance(result, dict):
            assert result["mcpServers"]["ai-governance"]["env"][
                "AI_GOVERNANCE_INDEX_PATH"
            ] == str(selected)
        else:
            assert f"AI_GOVERNANCE_INDEX_PATH={selected}" in shlex.split(result)


def test_ci_index_build_and_test_consumers_share_effective_path():
    """YAML scope matters: a build-step env does not reach either pytest step."""
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text())
    job = workflow["jobs"]["test"]
    steps = {step.get("name"): step for step in job["steps"]}
    for name in (
        "Build the governance index",
        "Run tests",
        "Run tests with coverage",
    ):
        effective_env = {
            **workflow.get("env", {}),
            **job.get("env", {}),
            **steps[name].get("env", {}),
        }
        assert effective_env.get("AI_GOVERNANCE_INDEX_PATH") == (
            "${{ github.workspace }}/index"
        ), name


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


class TestCodexToml:
    @pytest.mark.parametrize("enforce", [False, True])
    def test_round_trip_absolute_command_and_literal_paths(
        self, enforce, isolated_generator_paths, monkeypatch
    ):
        root, _, home = isolated_generator_paths
        library = home / 'library "quoted" \\ $literal 🪶'
        monkeypatch.setenv("AI_GOVERNANCE_REFERENCE_LIBRARY_PATH", str(library))
        interpreter = str(home / 'python "quoted" 🪶')
        config = tomllib.loads(
            config_generator.generate_codex_config(interpreter, enforce)
        )
        server = config["mcp_servers"]["ai-governance"]
        assert server["command"] == interpreter
        assert server["env"]["AI_GOVERNANCE_REFERENCE_LIBRARY_PATH"] == str(library)
        assert server["env"]["AI_GOVERNANCE_DOCUMENTS_PATH"] == str(root / "documents")
        if enforce:
            assert server["args"] == [
                "-m",
                "ai_governance_mcp.enforcement",
                "--",
                interpreter,
                "-m",
                "ai_governance_mcp.server",
            ]
            assert server["env"]["GOVERNANCE_ENFORCE_ACTS"] == "true"
        else:
            assert server["args"] == ADVISORY_ARGS

    def test_cli_prints_toml_without_overwriting_existing_config(
        self, isolated_generator_paths, monkeypatch, capsys
    ):
        _, _, home = isolated_generator_paths
        config = home / ".codex" / "config.toml"
        config.parent.mkdir()
        config.write_text('model = "existing"\n')
        monkeypatch.setattr(sys, "argv", ["generate", "--toml", "codex"])
        config_generator.main()
        result = tomllib.loads(capsys.readouterr().out)
        assert os.path.isabs(result["mcp_servers"]["ai-governance"]["command"])
        assert config.read_text() == 'model = "existing"\n'

    def test_platform_instructions_preserve_existing_tables(self, capsys):
        print_platform_config("codex")
        result = capsys.readouterr().out
        assert "Codex CLI and Desktop" in result
        assert "preserve all other settings" in result
        assert "instead of adding duplicates" in result


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
        assert "/App Support/py" in shlex.split(cmd)

    @pytest.mark.parametrize("source", ["environment", "dotenv"])
    @pytest.mark.parametrize("enforce", [False, True])
    @pytest.mark.parametrize(
        "platform, emit, json_emit",
        [
            ("claude", get_claude_cli_command, generate_claude_config),
            ("gemini", get_gemini_cli_command, generate_gemini_config),
        ],
    )
    def test_shell_preserves_literal_configured_paths(
        self,
        platform,
        emit,
        json_emit,
        enforce,
        source,
        isolated_generator_paths,
        monkeypatch,
    ):
        """Exercise a real shell: shlex.split alone cannot detect expansion.

        Both host names are shell functions, not installed CLIs. The only
        command-substitution payload is an inert printf; PATH is empty as an
        additional guard against accidentally invoking external programs.
        """
        module_root, cwd, home = isolated_generator_paths
        literal = "$P9_LITERAL $(printf substituted) `printf substituted` ; \"double\" 'single'"
        selected = home / f"index {literal}"
        interpreter = str(home / f"python {literal}")
        if source == "environment":
            monkeypatch.setenv("AI_GOVERNANCE_INDEX_PATH", str(selected))
        else:
            (cwd / ".env").write_text(
                f"AI_GOVERNANCE_INDEX_PATH={json.dumps(str(selected))}\n"
            )

        server = json_emit(enforce=enforce, python_path=interpreter)["mcpServers"][
            "ai-governance"
        ]
        # Independent expectations prevent the JSON comparison masking a
        # shared path-normalization or Settings-loading regression.
        expected_env = {
            "AI_GOVERNANCE_DOCUMENTS_PATH": str(module_root / "documents"),
            "AI_GOVERNANCE_INDEX_PATH": str(selected),
            "AI_GOVERNANCE_REFERENCE_LIBRARY_PATH": str(
                home / ".ai-governance" / "reference-library"
            ),
            "AI_GOVERNANCE_PRIVATE_REFERENCE_LIBRARY_PATH": str(
                home / ".ai-governance" / "private-reference-library"
            ),
        }
        if enforce:
            expected_env.update(
                GOVERNANCE_ENFORCEMENT_SOFT_MODE="true",
                GOVERNANCE_ENFORCE_ACTS="true",
            )
        assert server["env"] == expected_env
        assert server["command"] == interpreter
        env_args = [
            part
            for key, value in expected_env.items()
            for part in ("--env", f"{key}={value}")
        ]
        if platform == "claude":
            expected = ["mcp", "add", "ai-governance", "-s", "user", *env_args, "--"]
        else:
            expected = ["mcp", "add", "-s", "user", *env_args, "ai-governance"]
        expected.extend([server["command"], *server["args"]])

        stubs = (
            'claude() { printf "%s\\0" "$@"; }; gemini() { printf "%s\\0" "$@"; };\n'
        )
        result = subprocess.run(
            ["/bin/sh", "-c", stubs + emit(enforce=enforce, python_path=interpreter)],
            capture_output=True,
            check=False,
            timeout=10,
            env={"PATH": "", "HOME": str(home), "P9_LITERAL": "expanded"},
        )
        assert result.returncode == 0, result.stderr.decode()
        assert result.stderr == b""
        assert result.stdout.decode().split("\0") == [*expected, ""]


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

    def test_enforce_turns_on_the_act_intrinsic_gate(self):
        """The one non-model-satisfiable tier must actually ship enabled.

        It did not until 2026-09-02: enforcement.py's docstring claimed the
        generated config enabled it while this module had no reference to it at
        all, so the only real control was deployed nowhere. Assert the value, do
        not describe it (ADR-38).
        """
        cfg = generate_claude_config(python_path="/usr/bin/python3", enforce=True)
        env = cfg["mcpServers"]["ai-governance"]["env"]
        assert env["GOVERNANCE_ENFORCE_ACTS"] == "true"

        for cmd in (
            get_claude_cli_command(enforce=True, python_path="/usr/bin/python3"),
            get_gemini_cli_command(enforce=True, python_path="/usr/bin/python3"),
        ):
            assert "GOVERNANCE_ENFORCE_ACTS" in cmd

    def test_advisory_default_does_not_enable_the_act_gate(self):
        """Off by default in code stays true for the no-proxy path."""
        cfg = generate_claude_config(python_path="/usr/bin/python3", enforce=False)
        assert (
            "GOVERNANCE_ENFORCE_ACTS" not in cfg["mcpServers"]["ai-governance"]["env"]
        )

    def test_enforce_output_names_the_act_gate_as_the_hard_one(self, capsys):
        print_platform_config("claude", enforce=True)
        out = capsys.readouterr().out.lower()
        assert "act-intrinsic" in out
        assert "gates call order" in out or "call order" in out


class TestProxyHelpHonesty:
    """The proxy's own --help is a user-visible surface and overclaimed for
    longer than any document did: it said "default: hard block" and "Govern ALL"
    with no mention that the recency gate is model-satisfiable, while the honest
    three-tier account sat 650 lines above it in the same file (ADR-38)."""

    def _help_text(self):
        import subprocess
        import sys as _sys
        from pathlib import Path

        src = str(Path(__file__).parent.parent / "src")
        env = dict(os.environ, PYTHONPATH=src)
        proc = subprocess.run(
            [_sys.executable, "-m", "ai_governance_mcp.enforcement", "--help"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        assert proc.returncode == 0, proc.stderr
        return proc.stdout.lower()

    def test_help_states_the_recency_gate_is_model_satisfiable(self):
        out = self._help_text()
        assert "model-satisfiable" in out
        assert "call order" in out

    def test_help_does_not_claim_to_be_an_approval_gate(self):
        out = self._help_text()
        assert "not a human approval gate" in out or "not approval" in out

    def test_help_names_the_act_intrinsic_gate_as_the_hard_tier(self):
        out = self._help_text()
        assert "--enforce-acts" in out
        assert "hard even in soft mode" in out
