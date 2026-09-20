"""Codex CLI UserPromptSubmit hook — per-turn behavioral-floor FRAME re-anchor.

Injects the FRAME (the reasoning re-anchor from `ai_governance_mcp.frame`) as
developer context on each Codex turn, so the behavioral floor is re-anchored per turn
instead of only at session boot (the static `~/.codex/AGENTS.md` load decays over a
long session — same research basis as the Claude Code UserPromptSubmit hook,
`.claude/hooks/user-prompt-governance-inject.sh`). Deliberately MINIMAL: it injects the
FRAME only, WITHOUT that hook's transcript-dependent governance/startup nudges, so it
has NO Codex-rollout-format dependency and can't break on a format change — it reads
no transcript; `cwd` is captured for recon only.

Run as: python -m ai_governance_mcp.codex_frame
Registered in ~/.codex/config.toml [[hooks.UserPromptSubmit]].

GLOBAL by design (user directive, 2026-07-04): injects in EVERY Codex project, so
ai-governance is active regardless of project — matching how governance is always on in
Claude Code. The behavioral floor is unconditional per `~/.codex/AGENTS.md` ("always, any
project"), so global injection is consistent. Off-switch: `FRAME_INJECT_INTERVAL=0`.
(An earlier revision marker-gated this to framework projects; reverted to global on the
user's explicit request that it run everywhere.)

Codex UserPromptSubmit injection contract (confirmed from developers.openai.com/codex/hooks):
  {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "<text>"}}
This hook NEVER blocks a prompt (a block would be `{"decision":"block"}`); malformed/empty
stdin → silent exit 0.

Stdlib-only + `ai_governance_mcp.frame` (torch-free hot path; import-isolation guarded in
tests/test_codex_frame.py). Do NOT add a heavy import.
"""

from __future__ import annotations

import json
import os
import sys
import time

from ai_governance_mcp.frame import FRAME

HOOK_EVENT = "UserPromptSubmit"

# Off-switch, mirroring the Claude hook's FRAME_INJECT_INTERVAL=0.
_INTERVAL_ENV = "FRAME_INJECT_INTERVAL"
_CAPTURE_ENV = "CODEX_FRAME_CAPTURE"
_DEFAULT_CAPTURE = "logs/codex-frame-capture.jsonl"


def _capture_dest():
    """`--capture <path>` (argv, wins) or CODEX_FRAME_CAPTURE (env). `1` → default path."""
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


def _capture(raw_text, cwd, decision):
    """Debug recon: log whether the FRAME injected + the payload's cwd. OFF by default.

    The first live run uses this to confirm the UserPromptSubmit payload actually
    carries `cwd` (the marker-gate depends on it). No secrets involved (prompts only);
    still gitignored `logs/` by default.
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
                        "cwd": cwd,
                        "decision": decision,
                    }
                )
                + "\n"
            )
    except OSError:
        pass


def _payload_cwd(raw_text):
    """Best-effort cwd from the payload — capture/recon only (no longer gates injection)."""
    if not raw_text.strip():
        return None
    try:
        payload = json.loads(raw_text)
    except (ValueError, TypeError):
        return None
    return payload.get("cwd") if isinstance(payload, dict) else None


def _emit_frame() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "additionalContext": FRAME,
                }
            }
        )
    )


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")

    if os.environ.get(_INTERVAL_ENV) == "0":
        _capture(raw, None, "disabled")
        return 0

    # GLOBAL: inject the behavioral-floor FRAME in EVERY project (no marker gate). The
    # floor is unconditional per ~/.codex/AGENTS.md; the user wants ai-governance active
    # regardless of project. cwd is captured for recon only, not used to gate.
    _emit_frame()
    _capture(raw, _payload_cwd(raw), "inject")
    return 0


if __name__ == "__main__":
    sys.exit(main())
