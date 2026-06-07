"""MCP configuration generator for multiple platforms.

Generates platform-specific configuration snippets for:
- Gemini CLI
- Claude Code CLI
- Claude Desktop
- ChatGPT Desktop (Developer Mode)
- Cursor
- Windsurf
- Other platforms via MCP SuperAssistant

By default, configs use the enforcement proxy (ai-governance-proxy) which
wraps the governance server with structural enforcement in soft mode (warns
but does not block). Use --no-enforce for advisory-only configs.

IMPORTANT: Generated configs include environment variables pointing to the
index and documents directories. This ensures the server works when called
from any working directory (not just the project root).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


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


def get_python_command() -> str:
    """Get the Python command that's running this script."""
    return sys.executable


def _build_server_entry(
    python_path: Optional[str] = None,
    enforce: bool = True,
    **extra_fields: object,
) -> dict:
    """Build a single MCP server config entry.

    When enforce=True, wraps the server with ai-governance-proxy in soft mode.
    """
    python_cmd = python_path or "python"
    env = get_env_vars()

    if enforce:
        env["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
        entry: dict = {
            "command": "ai-governance-proxy",
            "args": ["--", python_cmd, "-m", "ai_governance_mcp.server"],
            "env": env,
        }
    else:
        entry = {
            "command": python_cmd,
            "args": ["-m", "ai_governance_mcp.server"],
            "env": env,
        }

    entry.update(extra_fields)
    return entry


def generate_gemini_config(
    python_path: Optional[str] = None, enforce: bool = True
) -> dict:
    """Generate Gemini CLI MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce, timeout=30000),
        }
    }


def generate_claude_config(
    python_path: Optional[str] = None, enforce: bool = True
) -> dict:
    """Generate Claude Desktop MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_chatgpt_config(
    python_path: Optional[str] = None, enforce: bool = True
) -> dict:
    """Generate ChatGPT Desktop MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_cursor_config(
    python_path: Optional[str] = None, enforce: bool = True
) -> dict:
    """Generate Cursor MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def generate_windsurf_config(
    python_path: Optional[str] = None, enforce: bool = True
) -> dict:
    """Generate Windsurf MCP configuration."""
    return {
        "mcpServers": {
            "ai-governance": _build_server_entry(python_path, enforce),
        }
    }


def get_gemini_cli_command(enforce: bool = True) -> str:
    """Get the gemini mcp add command with env vars."""
    env_vars = get_env_vars()
    if enforce:
        env_vars["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
    env_args = " ".join(f'--env {k}="{v}"' for k, v in env_vars.items())
    if enforce:
        return f"gemini mcp add -s user {env_args} ai-governance ai-governance-proxy -- python -m ai_governance_mcp.server"
    return f"gemini mcp add -s user {env_args} ai-governance python -m ai_governance_mcp.server"


def get_claude_cli_command(enforce: bool = True) -> str:
    """Get the claude mcp add command with env vars."""
    env_vars = get_env_vars()
    if enforce:
        env_vars["GOVERNANCE_ENFORCEMENT_SOFT_MODE"] = "true"
    env_args = " ".join(f'--env {k}="{v}"' for k, v in env_vars.items())
    if enforce:
        return f"claude mcp add ai-governance -s user {env_args} -- ai-governance-proxy -- python -m ai_governance_mcp.server"
    return f"claude mcp add ai-governance -s user {env_args} -- python -m ai_governance_mcp.server"


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
    platform: str, python_path: Optional[str] = None, enforce: bool = True
) -> None:
    """Print configuration instructions for a specific platform."""
    mode = "ENFORCED" if enforce else "ADVISORY"
    print(f"\n{'=' * 60}")
    print(f"  {platform.upper()} MCP CONFIGURATION ({mode})")
    print(f"{'=' * 60}\n")

    if enforce:
        print("  Mode: Enforcement proxy (soft mode — warns, does not block)")
        print("  Use --no-enforce for advisory-only (no enforcement).\n")

    if platform == "gemini":
        print("Option 1: CLI Command (Recommended)")
        print("-" * 40)
        print(f"  {get_gemini_cli_command(enforce)}")
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
        print(f"  {get_claude_cli_command(enforce)}")
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
        print("MCP SuperAssistant Chrome Extension")
        print("-" * 40)
        print(
            "  For: Grok, Perplexity, Google AI Studio, OpenRouter, DeepSeek, Mistral AI"
        )
        print("\n  1. Install MCP SuperAssistant:")
        print("     https://github.com/srbhptl39/MCP-SuperAssistant")
        print("\n  2. Start the MCP server locally:")
        if enforce:
            print("     ai-governance-proxy -- python -m ai_governance_mcp.server")
        else:
            print("     python -m ai_governance_mcp.server")
        print("\n  3. Connect via the extension's bridge interface")

    else:
        print(f"Unknown platform: {platform}")
        print(
            "Supported platforms: gemini, claude, chatgpt, cursor, windsurf, superassistant"
        )


def print_all_configs(python_path: Optional[str] = None, enforce: bool = True) -> None:
    """Print configuration for all supported platforms."""
    platforms = ["gemini", "claude", "chatgpt", "cursor", "windsurf", "superassistant"]
    for platform in platforms:
        print_platform_config(platform, python_path, enforce)
    print()


def generate_mcp_config(
    platform: str, python_path: Optional[str] = None, enforce: bool = True
) -> Optional[dict]:
    """Generate MCP configuration dictionary for a platform.

    Args:
        platform: Target platform (gemini, claude, chatgpt, cursor, windsurf)
        python_path: Optional Python executable path
        enforce: Use enforcement proxy (default: True, soft mode)

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
  python -m ai_governance_mcp.config_generator --platform claude --no-enforce
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
        help="Python executable path to use in configs (default: python)",
    )
    parser.add_argument(
        "--no-enforce",
        action="store_true",
        help="Generate advisory-only configs (no enforcement proxy)",
    )

    args = parser.parse_args()
    enforce = not args.no_enforce

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
