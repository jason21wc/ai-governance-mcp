"""Shared behavioral-floor constants — SSOT for cross-platform hooks.

The FRAME string is the per-turn reasoning re-anchor injected by the Claude Code
UserPromptSubmit hook (`.claude/hooks/user-prompt-governance-inject.sh`) and, since
the Codex FRAME hook (`ai_governance_mcp.codex_frame`), by Codex CLI too. This module
is the SSOT the Codex hook imports; the bash hook keeps its own inline copy (a
user-level hook can't import the package without adding a subprocess to every Claude
prompt), and `tests/test_frame_ssot.py` asserts the two stay byte-identical.

ASCII-ONLY INVARIANT (load-bearing): under a non-UTF-8 locale (C/POSIX) an emit path's
decode/encode can raise on a multi-byte char and silently drop the FRAME. Both platforms
depend on the string staying pure ASCII; the drift-guard test enforces `FRAME.encode("ascii")`.
"""

from __future__ import annotations

# Byte-identical to `.claude/hooks/user-prompt-governance-inject.sh` FRAME='...' (line 55).
# Guarded by tests/test_frame_ssot.py — edit BOTH together or the drift test fails.
FRAME = (
    "FRAME (every turn): eat our own dogfood (governance tools + subagents on your "
    "OWN analysis, not just code) and think systemically -- root-cause + big-picture "
    "(meta-core-systemic-thinking) | intent-over-literal (serve the intent, not just "
    "the literal ask) | verify-before-asserting from the source, not memory "
    "(meta-quality-verification-validation) | make-the-call (recommend-not-ask) | "
    "match-effort-to-stakes (proportional-rigor) | state-uncertainty "
    "(meta-safety-transparent-limitations) | dogfood-your-analysis."
)
