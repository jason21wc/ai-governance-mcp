"""Portable invocation helpers for launching our own MCP modules.

GUI MCP hosts (Claude Desktop, ChatGPT Desktop, Cursor, Windsurf) launch
servers with a minimal PATH that excludes the virtualenv's ``bin``/``Scripts``
directory, so a bare ``python`` or a console-script name (``ai-governance-proxy``)
fails with ``spawn ENOENT`` and no tools appear. Always invoke our own modules
through an ABSOLUTE interpreter path (``sys.executable``) plus ``-m <module>`` —
absolute, PATH-independent, and free of Windows ``.exe`` console-script variance.

See: reference-library/ai-coding/ref-ai-coding-connect-local-mcp-server-to-claude-surfaces.md
"""

from __future__ import annotations

import sys
from typing import Optional


def resolve_python(python_path: Optional[str] = None) -> str:
    """Return an absolute interpreter path for launching our modules.

    Defaults to the interpreter running this process (``sys.executable``) — the
    one guaranteed to have ``ai_governance_mcp`` installed. An explicit
    ``python_path`` (e.g. generating a config that targets a different machine)
    is returned unchanged so the caller stays in control.
    """
    return python_path or sys.executable


def python_module_argv(module: str, python_path: Optional[str] = None) -> list[str]:
    """Build ``[<abs-python>, "-m", <module>]`` for a subprocess or config entry."""
    return [resolve_python(python_path), "-m", module]
