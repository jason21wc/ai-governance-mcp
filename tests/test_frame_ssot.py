"""Drift guard for the FRAME SSOT.

The `ai_governance_mcp.frame.FRAME` constant and the Claude Code bash hook's inline
`FRAME='...'` literal (`.claude/hooks/user-prompt-governance-inject.sh:55`) are two
copies by necessity (a user-level bash hook can't import the package without adding a
subprocess to every Claude prompt). This test keeps them byte-identical and enforces
the load-bearing ASCII-only invariant both platforms depend on.
"""

from __future__ import annotations

import re
from pathlib import Path

from ai_governance_mcp.frame import FRAME

BASH_HOOK = (
    Path(__file__).resolve().parent.parent
    / ".claude"
    / "hooks"
    / "user-prompt-governance-inject.sh"
)


def _extract_bash_frame() -> str:
    """Pull the single-quoted FRAME='...' literal from the bash hook (one line, no
    internal single quotes)."""
    text = BASH_HOOK.read_text()
    m = re.search(r"^FRAME='(.*)'$", text, re.MULTILINE)
    assert m, "FRAME='...' literal not found in user-prompt-governance-inject.sh"
    return m.group(1)


def test_frame_matches_bash_literal() -> None:
    assert FRAME == _extract_bash_frame(), (
        "FRAME drifted from the bash hook literal — edit BOTH "
        "ai_governance_mcp/frame.py and user-prompt-governance-inject.sh:55."
    )


def test_frame_is_ascii() -> None:
    # A non-ASCII char silently drops the FRAME under a C/POSIX locale — both platforms rely on this.
    FRAME.encode("ascii")
