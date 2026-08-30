"""MCP configuration generator for multiple platforms.

Generates platform-specific configuration snippets for:
- Gemini CLI
- Claude Code CLI
- Claude Desktop
- ChatGPT Desktop (Developer Mode)
- Cursor
- Windsurf
- Other platforms via MCP SuperAssistant

Configs invoke the server through an ABSOLUTE interpreter (``sys.executable -m
ai_governance_mcp.server``). GUI hosts (Claude Desktop, etc.) launch with a
minimal PATH that excludes the venv ``bin``/``Scripts`` dir, so a bare
``python``/console-script name fails with spawn ENOENT — see ``_exec.py`` and
reference-library/ai-coding/ref-ai-coding-connect-local-mcp-server-to-claude-surfaces.md.

Default is ADVISORY (the server alone). Pass ``--enforce`` to wrap it in the
governance enforcement proxy (soft mode: appends a warning, does NOT block).
On GUI auto-run hosts that warning is post-hoc and gates nothing; the real
human gate is the host's own per-tool approval prompt.

Generated configs include environment variables pointing to the index and
documents directories so the server works from any working directory.
"""

import argparse
import json
from pathlib import Path
from typing import Optional

from ._exec import python_module_argv, resolve_python


def _has_governance_marker(path: Path) -> bool:
    """Check if a directory contains ai-governance document markers."""
    docs = path / "documents"
    if not docs.is_dir():
        return False
    if (docs / "constitution.md").exists():
        return True
    if any(docs.glob("title-*-*.md")):
        return True
    if (docs / "domains.json").exists():
        return True
    return False


def _find_project_root() -> Path:
    """Find the ai-governance-mcp data root directory.

    Searches from the directory containing this file (not CWD) looking for
    ai-governance markers: ``documents/constitution.md``, any
    ``documents/title-*-*.md``, or ``documents/domains.json``.
    """
    # Start from this file's location, not CWD
    start_path = Path(__file__).resolve().parent

    for path in [start_path] + list(start_path.parents):
        if _has_governance_marker(path):
            return path

    # Fallback to user directory
    return Path.home() / ".ai-governance"


def get_env_vars() -> dict[str, str]:
    """Get environment variables needed for the server to find its files."""
    root = _find_project_root()
    return {
        "AI_GOVERNANCE_DOCUMENTS_PATH": str(root / "documents"),
        "AI_GOVERNANCE_INDEX_PATH": str(root / "index"),
    }


def _build_server_entry(
    python_path: Optional[str] = None,
    enforce: bool = False,
    **extra_fields: object,
) -> dict:
    """Build a single MCP server config entry.

    Default (advisory): ``<abs-python> -m ai_governance_mcp.server``.
    ``enforce=True``: wrap the server in ``ai_governance_mcp.enforcement`` (soft
    mode), with the absolute interpreter at BOTH levels — the proxy spawns the
    inner server under the same minimal PATH, so a bare inner name would also
    ENOENT.
    """
    python_cmd = resolve_python(python_path)
    # [<abs-python>, "-m", "ai_governance_mcp.server"] — the inner server the
    # proxy spawns; the leading interpreter is absolute for the same reason.
    inner = python_module_argv("ai_governance_mcp.server", python_cmd)
    env = get_env_vars()

    if enforce:
        env["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
        entry: dict = {
            "command": python_cmd,
            "args": ["-m", "ai_governance_mcp.enforcement", "--", *inner],
            "env": env,
        }
    else:
        entry = {
            "command": python_cmd,
            "args": inner[
                1:
            ],  # ["-m", "ai_governance_mcp.server"] (command holds the python)
            "env": env,
        }

    entry.update(extra_fields)
    return entry


def generate_gemini_config(
    python_path: Optional[str] = None, enforce: bool = False
) -> dict:
    """Generate Gemini CLI MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce, timeout=30000),
        }
    }


def generate_claude_config(
    python_path: Optional[str] = None, enforce: bool = False
) -> dict:
    """Generate Claude Desktop MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_chatgpt_config(
    python_path: Optional[str] = None, enforce: bool = False
) -> dict:
    """Generate ChatGPT Desktop MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_cursor_config(
    python_path: Optional[str] = None, enforce: bool = False
) -> dict:
    """Generate Cursor MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_windsurf_config(
    python_path: Optional[str] = None, enforce: bool = False
) -> dict:
    """Generate Windsurf MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def get_gemini_cli_command(
    enforce: bool = False, python_path: Optional[str] = None
) -> str:
    """Get the gemini mcp add command with env vars."""
    env_vars = get_env_vars()
    if enforce:
        env_vars["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
    env_args = " ".join(f'--env {k}="{v}"' for k, v in env_vars.items())
    py = resolve_python(python_path)
    if enforce:
        return (
            f"gemini mcp add -s user {env_args} ai-governance "
            f'"{py}" -m ai_governance_mcp.enforcement -- '
            f'"{py}" -m ai_governance_mcp.server'
        )
    return (
        f"gemini mcp add -s user {env_args} ai-governance "
        f'"{py}" -m ai_governance_mcp.server'
    )


def get_claude_cli_command(
    enforce: bool = False, python_path: Optional[str] = None
) -> str:
    """Get the claude mcp add command with env vars."""
    env_vars = get_env_vars()
    if enforce:
        env_vars["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
    env_args = " ".join(f'--env {k}="{v}"' for k, v in env_vars.items())
    py = resolve_python(python_path)
    if enforce:
        return (
            f"claude mcp add ai-governance -s user {env_args} -- "
            f'"{py}" -m ai_governance_mcp.enforcement -- '
            f'"{py}" -m ai_governance_mcp.server'
        )
    return (
        f"claude mcp add ai-governance -s user {env_args} -- "
        f'"{py}" -m ai_governance_mcp.server'
    )


def get_config_file_path(platform: str) -> str:
    """Get the config file path for a platform."""
    paths = {
        "gemini": "~/.gemini/settings.json",
        "claude": "~/Library/Application Support/Claude/claude_desktop_config.json (macOS)\n"
        "         %APPDATA%\\Claude\\claude_desktop_config.json (Windows)",
        "chatgpt": "ChatGPT Desktop → Settings → Developer Mode → MCP Configuration",
        "cursor": "Cursor Settings → MCP Servers",
        "windsurf": "Windsurf Settings → Cascade → MCP",
    }
    return paths.get(platform, "Platform-specific")


def print_platform_config(
    platform: str, python_path: Optional[str] = None, enforce: bool = False
) -> None:
    """Print configuration instructions for a specific platform."""
    mode = "PROXY (opt-in, soft)" if enforce else "ADVISORY (default)"
    print(f"\n{'=' * 60}")
    print(f"  {platform.upper()} MCP CONFIGURATION ({mode})")
    print(f"{'=' * 60}\n")

    if enforce:
        print("  Mode: enforcement proxy, SOFT — appends a warning to action-tool")
        print("  responses; it does NOT block them. On GUI hosts (Claude Desktop,")
        print("  etc.) the warning arrives AFTER the tool runs, so the real human")
        print("  gate is the host's own per-tool approval prompt. For hard blocking,")
        print("  set GOVERNANCE_ENFORCEMENT_SOFT_MODE=false.")
        print(
            "  See: reference-library/ai-coding/"
            "ref-ai-coding-connect-local-mcp-server-to-claude-surfaces.md\n"
        )
    else:
        print("  Mode: advisory — the server alone (no proxy). Pass --enforce to")
        print("  wrap it in the governance proxy (soft mode; see --help).\n")

    if platform == "gemini":
        print("Option 1: CLI Command (Recommended)")
        print("-" * 40)
        print(f"  {get_gemini_cli_command(enforce, python_path)}")
        print("\nOption 2: Manual Configuration")
        print("-" * 40)
        print(f"  Edit: {get_config_file_path('gemini')}")
        print("\n  Add this configuration:")
        config = generate_gemini_config(python_path, enforce)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")
        print("\n  Then restart Gemini CLI.")

    elif platform == "claude":
        print("Option 1: Claude Code CLI (Recommended)")
        print("-" * 40)
        print(f"  {get_claude_cli_command(enforce, python_path)}")
        print("\nOption 2: Claude Desktop Manual Configuration")
        print("-" * 40)
        print(f"  Edit: {get_config_file_path('claude')}")
        print("\n  Add this configuration:")
        config = generate_claude_config(python_path, enforce)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")
        print("\n  Then restart Claude Desktop.")

    elif platform == "chatgpt":
        print("ChatGPT Desktop (Developer Mode)")
        print("-" * 40)
        print("  1. Open ChatGPT Desktop")
        print("  2. Go to Settings → Developer Mode (enable)")
        print("  3. Add MCP server configuration:\n")
        config = generate_chatgpt_config(python_path, enforce)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")

    elif platform == "cursor":
        print("Cursor (Native MCP Support)")
        print("-" * 40)
        print("  See: https://docs.cursor.com/context/model-context-protocol")
        print(f"\n  Configure in: {get_config_file_path('cursor')}")
        print("\n  Add this configuration:")
        config = generate_cursor_config(python_path, enforce)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")

    elif platform == "windsurf":
        print("Windsurf (Cascade MCP Support)")
        print("-" * 40)
        print("  See: https://docs.windsurf.com/windsurf/cascade/mcp")
        print(f"\n  Configure in: {get_config_file_path('windsurf')}")
        print("\n  Add this configuration:")
        config = generate_windsurf_config(python_path, enforce)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")

    elif platform == "superassistant":
        py = resolve_python(python_path)
        print("MCP SuperAssistant Chrome Extension")
        print("-" * 40)
        print(
            "  For: Grok, Perplexity, Google AI Studio, OpenRouter, DeepSeek, Mistral AI"
        )
        print("\n  1. Install MCP SuperAssistant:")
        print("     https://github.com/srbhptl39/MCP-SuperAssistant")
        print("\n  2. Start the MCP server locally:")
        if enforce:
            print(
                f'     "{py}" -m ai_governance_mcp.enforcement -- '
                f'"{py}" -m ai_governance_mcp.server'
            )
        else:
            print(f'     "{py}" -m ai_governance_mcp.server')
        print("\n  3. Connect via the extension's bridge interface")

    else:
        print(f"Unknown platform: {platform}")
        print(
            "Supported platforms: gemini, claude, chatgpt, cursor, windsurf, superassistant"
        )


def print_all_configs(python_path: Optional[str] = None, enforce: bool = False) -> None:
    """Print configuration for all supported platforms."""
    platforms = ["gemini", "claude", "chatgpt", "cursor", "windsurf", "superassistant"]
    for platform in platforms:
        print_platform_config(platform, python_path, enforce)
    print()


def generate_mcp_config(
    platform: str, python_path: Optional[str] = None, enforce: bool = False
) -> Optional[dict]:
    """Generate MCP configuration dictionary for a platform.

    Args:
        platform: Target platform (gemini, claude, chatgpt, cursor, windsurf)
        python_path: Optional interpreter path (default: sys.executable, absolute)
        enforce: Wrap in the enforcement proxy, soft mode (default: False/advisory)

    Returns:
        Configuration dictionary or None for non-JSON platforms
    """
    generators = {
        "gemini": generate_gemini_config,
        "claude": generate_claude_config,
        "chatgpt": generate_chatgpt_config,
        "cursor": generate_cursor_config,
        "windsurf": generate_windsurf_config,
    }

    if platform in generators:
        return generators[platform](python_path, enforce)
    return None


def main() -> None:
    """CLI entry point for config generator."""
    parser = argparse.ArgumentParser(
        description="Generate MCP configurations for AI platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ai_governance_mcp.config_generator --platform claude
  python -m ai_governance_mcp.config_generator --platform claude --enforce
  python -m ai_governance_mcp.config_generator --all
  python -m ai_governance_mcp.config_generator --json gemini
        """,
    )

    parser.add_argument(
        "--platform",
        "-p",
        choices=["gemini", "claude", "chatgpt", "cursor", "windsurf", "superassistant"],
        help="Target platform for configuration",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Show configuration for all platforms",
    )
    parser.add_argument(
        "--json",
        "-j",
        metavar="PLATFORM",
        choices=["gemini", "claude", "chatgpt", "cursor", "windsurf"],
        help="Output raw JSON configuration for a platform",
    )
    parser.add_argument(
        "--python-path",
        help="Interpreter path to use in configs (default: sys.executable, an "
        "absolute path so GUI hosts can launch it without shell PATH)",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Wrap the server in the governance enforcement proxy (SOFT mode: "
        "appends a warning, does NOT block; post-hoc on GUI auto-run hosts). "
        "Default is advisory — the server alone, no proxy.",
    )

    args = parser.parse_args()
    enforce = args.enforce

    if args.json:
        config = generate_mcp_config(args.json, args.python_path, enforce)
        if config:
            print(json.dumps(config, indent=2))
        return

    if args.all:
        print_all_configs(args.python_path, enforce)
    elif args.platform:
        print_platform_config(args.platform, args.python_path, enforce)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
