"""Codex CLI PreToolUse hook — act-intrinsic secret-value-egress gate (#176a).

Ports the act-intrinsic half of ``.claude/hooks/pre-tool-content-security.sh`` to
OpenAI Codex CLI (codex-cli 0.142.5). Reads a Codex ``PreToolUse`` JSON payload on
stdin, scans the tool call's argument VALUES for a secret value or credential path
via the shared ``safety_scan`` core, and DENIES (Codex deny contract) on a match,
else allows.

Run as::

    python -m ai_governance_mcp.codex_hooks

Registered in ``~/.codex/config.toml`` ``[[hooks.PreToolUse]]`` (see title-10
Appendix N). Implements ``multi-method-hook-based-enforcement-client-side-deterministic``
and ``coding-method-mcp-compliance-enforcement-patterns``.

SCOPE / HONESTY (BACKLOG #176a):

* The genuinely-new enforcement is **secret-VALUE egress** (an ``AKIA…``/``sk-…``/
  PEM block already sitting in a ``Bash``/``apply_patch`` argument, sourced from
  somewhere the OS sandbox does not gate — a workspace ``.env``, an env var, a
  pasted secret). Credential-PATH denial is already provided — more strongly — by
  the ``[permissions.governed]`` sandbox profile in ``~/.codex/config.toml``
  (undefeatable by string obfuscation, inherited by ``codex exec``); this hook's
  path matching is **defense-in-depth, not the primary layer**.
* Defense-in-depth, NOT a boundary: deliberate obfuscation (splitting, base64,
  homoglyphs) defeats literal matching. Same disclaimer as
  ``safety_scan.act_intrinsic_block``.
* Registration should scope to ``Bash``/``apply_patch`` (NOT MCP calls): an
  ``evaluate_governance(planned_action="… ~/.ssh/config …")`` MCP call would else
  self-deny. ``_is_exempt_tool`` is a secondary guard (skips recognizable
  governance/MCP calls) while Codex's tool-name field is unconfirmed; MCP-call
  scanning proper is deferred until phase-1 capture reveals that field so the
  proxy's ``GOVERNANCE_SATISFIERS`` exemption can be ported.

DELIBERATELY torch-free / stdlib-only + ``safety_scan`` — a PreToolUse hook runs on
EVERY tool call, so it must cold-start fast. ``tests/test_codex_hooks.py`` has an
import-isolation guard asserting no heavy module (torch/transformers/…) loads and
that only ``safety_scan`` is pulled from the package. Do NOT add a heavy import
here or to ``ai_governance_mcp/__init__.py``.
"""

from __future__ import annotations

import json
import os
import sys
import time

from ai_governance_mcp.safety_scan import scan_tool_values

HOOK_EVENT = "PreToolUse"

# Candidate keys that may hold the tool-call arguments across Codex payload shapes.
# Field names are UNVERIFIED (phase-1 capture confirms them); tried in priority
# order so safety_scan's per-leaf / leaf-count caps land on the real args. On no
# match we scan the whole payload's string leaves, so an unknown field name never
# silently disables the gate.
_ARG_KEYS = ("tool_input", "arguments", "input", "command")

# Best-effort tool-name fields, for the governance/MCP self-deny guard.
_TOOL_NAME_KEYS = ("tool_name", "tool", "name")

# Exact-name allowlist for the self-deny guard: only the governance/CE tools whose
# args LEGITIMATELY describe credential paths or secrets (a planned_action or search
# query must be able to *name* danger). Matched as the bare tool name or a
# "<server>__<tool>" suffix — never a bare "mcp__" prefix or a substring: a blanket
# MCP exemption would let any OTHER MCP tool carry a secret past the scan
# (session-240 cross-vendor measurement finding, confirmed by both review roles).
# Entries MUST be lowercase — the comparison lowers the input, not the constant
# (a mixed-case entry would silently never match; fails toward scanning).
_EXEMPT_TOOL_SUFFIXES = (
    "evaluate_governance",
    "verify_governance_compliance",
    "query_project",
)

# Separators a host may use between server and tool name ("mcp__srv__tool",
# "srv.tool", "srv/tool") — Codex's real shape is unconfirmed until phase-1
# capture, and a missed separator here is a self-deny regression, not a bypass.
_EXEMPT_NAME_FORMS = tuple(
    sep + suffix for suffix in _EXEMPT_TOOL_SUFFIXES for sep in ("__", ".", "/")
)

# Reuse the SAME bypass var as the Claude Code content-security hook so one escape
# hatch documents both platforms.
_BYPASS_ENV = "CONTENT_SECURITY_SKIP"
_CAPTURE_ENV = "CODEX_HOOK_CAPTURE"
_DEFAULT_CAPTURE = "logs/codex-hook-capture.jsonl"


def _is_exempt_tool(payload) -> bool:
    """True only for an exact-named governance/CE tool call (skip the scan).

    Prevents the hook self-denying an ``evaluate_governance`` call whose
    ``planned_action`` text names a credential path. Exemption is an EXACT-name
    match against ``_EXEMPT_TOOL_SUFFIXES`` (bare name or ``<server>__<tool>``
    suffix) — never a ``mcp__`` prefix or substring, so a non-governance MCP tool
    (or a lookalike name) carrying a secret is still scanned. Registration SHOULD
    scope to ``Bash``/``apply_patch`` via the matcher; this is a secondary guard
    while Codex's tool-name field is unconfirmed (BACKLOG #176a). Best-effort: if
    no tool-name field is found, we do NOT exempt (fail toward scanning).
    """
    if not isinstance(payload, dict):
        return False
    for key in _TOOL_NAME_KEYS:
        val = payload.get(key)
        if isinstance(val, str):
            low = val.lower()
            if low in _EXEMPT_TOOL_SUFFIXES or low.endswith(_EXEMPT_NAME_FORMS):
                return True
    return False


def _extract_scan_target(payload):
    """Best-effort locate the tool-args subtree; else return the whole payload.

    ``scan_tool_values`` walks every string leaf, so returning the whole payload
    is a safe fallback — a credential anywhere is still caught. Never raises.
    """
    if isinstance(payload, dict):
        for key in _ARG_KEYS:
            if key in payload:
                return payload[key]
        params = payload.get("params")
        if isinstance(params, dict) and "arguments" in params:
            return params["arguments"]
    return payload


def _decide(raw_text):
    """Return a deny reason string, or None to allow.

    Fail-CLOSED on a shape surprise: if JSON parses, scan the targeted subtree then
    (defensively) the whole payload; if it does NOT parse, scan the raw stdin
    string (``safety_scan`` accepts a bare string leaf) so a secret is caught
    regardless of structure. Empty input allows (no action to gate).
    """
    if not raw_text or not raw_text.strip():
        return None
    try:
        payload = json.loads(raw_text)
    except (ValueError, TypeError):
        # Malformed payload — do NOT deny-all; scan the raw bytes for a secret.
        return scan_tool_values(raw_text)
    if _is_exempt_tool(payload):
        return None
    target = _extract_scan_target(payload)
    reason = scan_tool_values(target)
    if reason is None and target is not payload:
        # Defense in depth: args may have sat under a key we didn't recognize.
        reason = scan_tool_values(payload)
    return reason


def _deny_message(reason: str) -> str:
    return (
        f"GOVERNANCE BLOCK (Codex act-intrinsic hook): this action's content "
        f"matched a {reason}. Exfiltration of credentials/secrets is blocked. If "
        f"this is a genuine false positive, a human must approve it explicitly, or "
        f"set {_BYPASS_ENV}=1 for this run."
    )


def _emit_deny(reason: str) -> int:
    # Emit the deny JSON on stdout AND the reason on stderr AND exit 2 — both of
    # Codex's documented deny channels fire (belt-and-suspenders while exec-mode
    # channel handling is unverified; phase-1 capture confirms which Codex honors).
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _deny_message(reason),
                }
            }
        )
    )
    print(f"codex-hook: denied [{reason}]", file=sys.stderr)
    return 2


def _emit_bypass_warning() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "additionalContext": (
                        f"content-security bypassed via {_BYPASS_ENV}=1 "
                        "(credential/secret scan skipped)"
                    ),
                }
            }
        )
    )


def _audit_bypass(reason: str) -> None:
    """Append a bypass line to the shared hook-bypass audit log (best-effort)."""
    try:
        log_dir = os.path.join(os.path.expanduser("~"), ".claude")
        os.makedirs(log_dir, exist_ok=True)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(os.path.join(log_dir, "hook-bypass-audit.log"), "a") as f:
            f.write(f"{ts} codex_hooks {_BYPASS_ENV}=1 {reason}\n")
    except OSError:
        pass


def _capture_dest():
    """Resolve the capture path from ``--capture <path>`` (argv) or the env var.

    argv wins: a hook's arguments are guaranteed to reach the process, whereas its
    environment depends on host behavior we can't assume Codex preserves. ``1``
    (either source) means the default ``logs/`` path. Returns None when unset.
    """
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--capture" and i + 1 < len(argv):
            dest = argv[i + 1]
            break
        if arg.startswith("--capture="):
            dest = arg.split("=", 1)[1]
            break
    else:
        dest = os.environ.get(_CAPTURE_ENV)
    if not dest:
        return None
    return _DEFAULT_CAPTURE if dest == "1" else dest


def _capture(raw_text: str, decision: str, reason) -> None:
    """Debug-only reconnaissance: log the raw payload so the first live run reveals
    Codex's field names + whether conversation history is present. OFF by default,
    enabled via ``--capture <path>`` (preferred) or ``CODEX_HOOK_CAPTURE``.

    SECURITY: the captured payload may contain the secret it just blocked. Writes
    only to a caller-chosen path (default ``logs/``, gitignored). Never commit.
    """
    dest = _capture_dest()
    if not dest:
        return
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "a") as f:
            f.write(
                json.dumps(
                    {
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "raw_stdin": raw_text,
                        "decision": decision,
                        "matched_reason": reason,
                    }
                )
                + "\n"
            )
    except OSError:
        pass


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")

    if os.environ.get(_BYPASS_ENV) == "1":
        _audit_bypass("skip")
        _emit_bypass_warning()
        _capture(raw, "bypass", None)
        return 0

    reason = _decide(raw)
    if reason is None:
        _capture(raw, "allow", None)
        return 0
    rc = _emit_deny(reason)
    _capture(raw, "deny", reason)
    return rc


if __name__ == "__main__":
    sys.exit(main())
