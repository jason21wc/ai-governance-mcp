"""MCP configuration generator for multiple platforms.

Generates platform-specific configuration snippets for:
- Gemini CLI
- Claude Code CLI
- Claude Desktop
- ChatGPT Desktop (Developer Mode)
- Other platforms via MCP SuperAssistant
"""

import argparse
import json
import sys
from typing import Optional


def get_python_command() -> str:
    """Get the Python command that's running this script."""
    return sys.executable


def generate_gemini_config(python_path: Optional[str] = None) -> dict:
    """Generate Gemini CLI MCP configuration."""
    python_cmd = python_path or "python"
    return {
        "mcpServers": {
            "ai-governance": {
                "command": python_cmd,
                "args": ["-m", "ai_governance_mcp.server"],
                "timeout": 30000,
            }
        }
    }


def generate_claude_config(python_path: Optional[str] = None) -> dict:
    """Generate Claude Desktop MCP configuration."""
    python_cmd = python_path or "python"
    return {
        "mcpServers": {
            "ai-governance": {
                "command": python_cmd,
                "args": ["-m", "ai_governance_mcp.server"],
            }
        }
    }


def generate_chatgpt_config(python_path: Optional[str] = None) -> dict:
    """Generate ChatGPT Desktop MCP configuration."""
    python_cmd = python_path or "python"
    return {
        "mcpServers": {
            "ai-governance": {
                "command": python_cmd,
                "args": ["-m", "ai_governance_mcp.server"],
            }
        }
    }


def get_gemini_cli_command() -> str:
    """Get the gemini mcp add command."""
    return "gemini mcp add -s user ai-governance python -m ai_governance_mcp.server"


def get_claude_cli_command() -> str:
    """Get the claude mcp add command."""
    return "claude mcp add ai-governance -s user -- python -m ai_governance_mcp.server"


def get_config_file_path(platform: str) -> str:
    """Get the config file path for a platform."""
    paths = {
        "gemini": "~/.gemini/settings.json",
        "claude": "~/Library/Application Support/Claude/claude_desktop_config.json (macOS)\n"
        "         %APPDATA%\\Claude\\claude_desktop_config.json (Windows)",
        "chatgpt": "ChatGPT Desktop → Settings → Developer Mode → MCP Configuration",
    }
    return paths.get(platform, "Platform-specific")


def print_platform_config(platform: str, python_path: Optional[str] = None) -> None:
    """Print configuration instructions for a specific platform."""
    print(f"\n{'=' * 60}")
    print(f"  {platform.upper()} MCP CONFIGURATION")
    print(f"{'=' * 60}\n")

    if platform == "gemini":
        print("Option 1: CLI Command (Recommended)")
        print("-" * 40)
        print(f"  {get_gemini_cli_command()}")
        print("\nOption 2: Manual Configuration")
        print("-" * 40)
        print(f"  Edit: {get_config_file_path('gemini')}")
        print("\n  Add this configuration:")
        config = generate_gemini_config(python_path)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")
        print("\n  Then restart Gemini CLI.")

    elif platform == "claude":
        print("Option 1: Claude Code CLI (Recommended)")
        print("-" * 40)
        print(f"  {get_claude_cli_command()}")
        print("\nOption 2: Claude Desktop Manual Configuration")
        print("-" * 40)
        print(f"  Edit: {get_config_file_path('claude')}")
        print("\n  Add this configuration:")
        config = generate_claude_config(python_path)
        print(f"  {json.dumps(config, indent=2).replace(chr(10), chr(10) + '  ')}")
        print("\n  Then restart Claude Desktop.")

    elif platform == "chatgpt":
        print("ChatGPT Desktop (Developer Mode)")
        print("-" * 40)
        print("  1. Open ChatGPT Desktop")
        print("  2. Go to Settings → Developer Mode (enable)")
        print("  3. Add MCP server configuration:\n")
        config = generate_chatgpt_config(python_path)
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
        print("     python -m ai_governance_mcp.server")
        print("\n  3. Connect via the extension's bridge interface")

    else:
        print(f"Unknown platform: {platform}")
        print("Supported platforms: gemini, claude, chatgpt, superassistant")


def print_all_configs(python_path: Optional[str] = None) -> None:
    """Print configuration for all supported platforms."""
    platforms = ["gemini", "claude", "chatgpt", "superassistant"]
    for platform in platforms:
        print_platform_config(platform, python_path)
    print()


def generate_mcp_config(
    platform: str, python_path: Optional[str] = None
) -> Optional[dict]:
    """Generate MCP configuration dictionary for a platform.

    Args:
        platform: Target platform (gemini, claude, chatgpt)
        python_path: Optional Python executable path

    Returns:
        Configuration dictionary or None for non-JSON platforms
    """
    generators = {
        "gemini": generate_gemini_config,
        "claude": generate_claude_config,
        "chatgpt": generate_chatgpt_config,
    }

    if platform in generators:
        return generators[platform](python_path)
    return None


def main() -> None:
    """CLI entry point for config generator."""
    parser = argparse.ArgumentParser(
        description="Generate MCP configurations for AI platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ai_governance_mcp.config_generator --platform gemini
  python -m ai_governance_mcp.config_generator --platform claude
  python -m ai_governance_mcp.config_generator --all
  python -m ai_governance_mcp.config_generator --json gemini
        """,
    )

    parser.add_argument(
        "--platform",
        "-p",
        choices=["gemini", "claude", "chatgpt", "superassistant"],
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
        choices=["gemini", "claude", "chatgpt"],
        help="Output raw JSON configuration for a platform",
    )
    parser.add_argument(
        "--python-path",
        help="Python executable path to use in configs (default: python)",
    )

    args = parser.parse_args()

    if args.json:
        config = generate_mcp_config(args.json, args.python_path)
        if config:
            print(json.dumps(config, indent=2))
        return

    if args.all:
        print_all_configs(args.python_path)
    elif args.platform:
        print_platform_config(args.platform, args.python_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
