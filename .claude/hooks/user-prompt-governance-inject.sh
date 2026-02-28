#!/usr/bin/env bash
# UserPromptSubmit hook — conditionally injects governance reminder
# Outputs JSON with additionalContext ONLY when governance/CE not yet established.
# Silent (no output) when both tools have been called recently — saves ~128 tokens/prompt.
#
# Environment variables:
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

# If we have a transcript, check compliance
if [ -n "$TRANSCRIPT_PATH" ] && [ -r "$TRANSCRIPT_PATH" ]; then
  GOV_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"
  CE_TOOL="${CE_TOOL_NAME:-mcp__context-engine__query_project}"
  RECENCY_WINDOW="${GOVERNANCE_RECENCY_WINDOW:-200}"

  SCAN_RESULT=$(python3 "$HOOK_DIR/scan_transcript.py" "$GOV_TOOL" "$CE_TOOL" "$TRANSCRIPT_PATH" "$RECENCY_WINDOW" 2>/dev/null) || SCAN_RESULT="neither"

  if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
    echo "[governance-hook] UserPromptSubmit scan result: $SCAN_RESULT" >&2
  fi

  # If both found recently, suppress reminder (save tokens)
  if [ "$SCAN_RESULT" = "both" ]; then
    exit 0
  fi
fi

# Not compliant or no transcript — inject shortened reminder
REMINDER='GOVERNANCE: evaluate_governance() required before Bash|Edit|Write. CE: query_project() required before creating/modifying code. Both enforced by hard-mode hook.'

# Output JSON with additionalContext — python3 for safe serialization
python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({'additionalContext': msg}))
" "$REMINDER" 2>/dev/null || true
