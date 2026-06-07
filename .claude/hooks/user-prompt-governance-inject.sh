#!/usr/bin/env bash
# UserPromptSubmit hook — injects a systemic-thinking / dogfood reasoning FRAME on every prompt
# (turn-start re-anchor), plus the governance/CE reminder when governance is not yet established
# and a startup-reads nudge early in a session. Accumulate-then-emit: one JSON additionalContext.
#
# The FRAME re-anchors the reasoning stance at turn-start — the gap between session-boot decay
# (CLAUDE.md) and the next evaluate_governance call (whose critical_5 scaffolds steer at the action
# locus). It COMPLEMENTS, it does NOT replace, the gov-call scaffolds (different form, different
# locus). See EXECUTION-FRAMEWORK §8.4 "delivery-cadence axis" and plan joyful-dancing-pebble.md.
#
# Environment variables:
#   FRAME_INJECT_INTERVAL=1   — 1 (default) injects the FRAME every prompt; 0 disables it (off-switch
#                               / dial-back-to-zero). Values >1 (every-Nth throttle) are RESERVED, not
#                               yet implemented (needs user-turn counting); build only if the
#                               kill-criterion fires (see plan). v1 treats any non-zero value as "every prompt."
#   GOVERNANCE_HOOK_DEBUG=true       — Enable stderr debug logging
#   GOVERNANCE_RECENCY_WINDOW=200    — Recency window for transcript scanning
#   GOVERNANCE_TOOL_NAME=...         — Override governance tool name
#   CE_TOOL_NAME=...                 — Override CE tool name
#
# Exit 0 always — never blocks, never errors

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

debug() {
  if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
    echo "[governance-hook] UserPromptSubmit hook invoked" >&2
  fi
}

debug

# Read hook input from stdin
INPUT=$(cat)

# Extract transcript_path from hook JSON
TRANSCRIPT_PATH=""
if command -v jq &>/dev/null; then
  TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null) || true
else
  TRANSCRIPT_PATH=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('transcript_path', ''))
" <<< "$INPUT" 2>/dev/null) || true
fi

# --- FRAME: turn-start reasoning re-anchor (every prompt unless disabled) ---
# Refs carry the density (constitution effect): naming a principle activates it cheaply.
# ASCII-only payload by design: under a non-UTF-8 locale (C/POSIX) the emit path's argv
# decode + stdout write can raise on multi-byte chars, and the guarded emit would then
# silently drop the FRAME. Keep separators ASCII (' | ', ' -- ') so the frame always lands.
FRAME='FRAME (every turn): eat our own dogfood (governance tools + subagents on your OWN analysis, not just code) and think systemically -- root-cause + big-picture (meta-core-systemic-thinking) | intent-over-literal (serve the intent, not just the literal ask) | verify-before-asserting from the source, not memory (meta-quality-verification-validation) | make-the-call (recommend-not-ask) | match-effort-to-stakes (proportional-rigor) | state-uncertainty (meta-safety-transparent-limitations) | dogfood-your-analysis.'

MSG=""
if [ "${FRAME_INJECT_INTERVAL:-1}" != "0" ]; then
  MSG="$FRAME"
fi

# --- Compliance + startup-reads state ---
GOV_MSG=""
STARTUP_MSG=""
COMPLIANT="no"
if [ -n "$TRANSCRIPT_PATH" ] && [ -r "$TRANSCRIPT_PATH" ]; then
  GOV_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"
  CE_TOOL="${CE_TOOL_NAME:-mcp__context-engine__query_project}"
  RECENCY_WINDOW="${GOVERNANCE_RECENCY_WINDOW:-200}"

  SCAN_RESULT=$(python3 "$HOOK_DIR/scan_transcript.py" "$GOV_TOOL" "$CE_TOOL" "$TRANSCRIPT_PATH" "$RECENCY_WINDOW" 2>/dev/null) || SCAN_RESULT="neither"

  if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
    echo "[governance-hook] UserPromptSubmit scan result: $SCAN_RESULT" >&2
  fi

  if [ "$SCAN_RESULT" = "both" ]; then
    COMPLIANT="yes"
    # Startup-reads nudge — only in the first ~50 transcript lines (early session)
    STARTUP_WINDOW=50
    LINE_COUNT=$(wc -l < "$TRANSCRIPT_PATH" 2>/dev/null | tr -d ' ') || LINE_COUNT=9999
    if [ "$LINE_COUNT" -le "$STARTUP_WINDOW" ]; then
      PM_READ=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "PROJECT-MEMORY" "$TRANSCRIPT_PATH" "$STARTUP_WINDOW" 2>/dev/null) || PM_READ="false"
      LL_READ=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "LEARNING-LOG" "$TRANSCRIPT_PATH" "$STARTUP_WINDOW" 2>/dev/null) || LL_READ="false"
      if [ "$PM_READ" = "false" ] || [ "$LL_READ" = "false" ]; then
        MISSING=""
        [ "$PM_READ" = "false" ] && MISSING="PROJECT-MEMORY.md"
        [ "$LL_READ" = "false" ] && MISSING="${MISSING:+$MISSING, }LEARNING-LOG.md"
        STARTUP_MSG="STARTUP READS: You have not yet read $MISSING this session. Per AGENTS.md On Session Start, read all 3 memory files (SESSION-STATE, PROJECT-MEMORY, LEARNING-LOG) before proceeding."
      fi
    fi
  fi
fi

# Not compliant (or no transcript) — append the governance/CE reminder
if [ "$COMPLIANT" != "yes" ]; then
  GOV_MSG='GOVERNANCE: evaluate_governance() required before Bash|Edit|Write. CE: query_project() required before creating/modifying code. Both enforced by hard-mode hook.'
fi

# Accumulate path-specific messages onto the FRAME base
[ -n "$STARTUP_MSG" ] && MSG="${MSG:+$MSG }$STARTUP_MSG"
[ -n "$GOV_MSG" ] && MSG="${MSG:+$MSG }$GOV_MSG"

# Emit one JSON object if there is anything to say
if [ -n "$MSG" ]; then
  python3 -c "
import json, sys
sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': sys.argv[1]}}))
" "$MSG" 2>/dev/null || true
fi

exit 0
