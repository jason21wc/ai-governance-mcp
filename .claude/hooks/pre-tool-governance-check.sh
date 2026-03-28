#!/usr/bin/env bash
# PreToolUse hook — checks transcript for evaluate_governance() AND query_project() calls
# before allowing file-modifying operations (Bash|Edit|Write)
#
# Scans for both tools using shared scan_transcript.py with adaptive output.
#
# Modes:
#   Hard (default): Returns permissionDecision: "deny" for missing tool(s)
#   Soft (opt-in): Injects additionalContext reminder for missing tool(s)
#
# Environment variables:
#   GOVERNANCE_SOFT_MODE=true    — Use soft mode for governance (reminder instead of block)
#   CE_SOFT_MODE=true            — Use soft mode for CE (reminder instead of block)
#   GOVERNANCE_HARD_MODE=false   — Legacy: same as GOVERNANCE_SOFT_MODE=true
#   CE_HARD_MODE=false           — Legacy: same as CE_SOFT_MODE=true
#   GOVERNANCE_RECENCY_WINDOW=200 — Only scan last N transcript lines (0 = scan all)
#   GOVERNANCE_TOOL_NAME=...     — Override governance tool name (default: mcp__ai-governance__evaluate_governance)
#   CE_TOOL_NAME=...             — Override CE tool name (default: mcp__context-engine__query_project)
#   GOVERNANCE_HOOK_DEBUG=true   — Enable stderr debug logging
#
# Exit 0 always when outputting JSON. Fail-closed on errors (hard mode default).

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

debug() {
  if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
    echo "[governance-hook] $1" >&2
  fi
}

# Read hook input from stdin
INPUT=$(cat)

debug "PreToolUse hook invoked"

# Extract transcript_path from hook JSON
# Try jq first (matches existing CI hook pattern), fall back to python3
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

# Determine enforcement mode
# New defaults: hard mode ON. Soft mode is the opt-in escape hatch.
# Support both new (SOFT_MODE) and legacy (HARD_MODE) env vars.
GOV_SOFT="${GOVERNANCE_SOFT_MODE:-false}"
CE_SOFT="${CE_SOFT_MODE:-false}"

# Legacy compat: HARD_MODE=false means soft mode
if [ "${GOVERNANCE_HARD_MODE:-}" = "false" ]; then
  GOV_SOFT="true"
fi
if [ "${CE_HARD_MODE:-}" = "false" ]; then
  CE_SOFT="true"
fi

# Handle missing/unreadable transcript
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -r "$TRANSCRIPT_PATH" ]; then
  if [ "$GOV_SOFT" = "true" ] && [ "$CE_SOFT" = "true" ]; then
    # Both soft: fail-open — allow silently
    debug "Transcript missing/unreadable, both soft mode: allowing"
    exit 0
  fi
  # At least one hard mode: fail-closed — block when transcript unavailable
  debug "Transcript missing/unreadable, hard mode active: blocking"
  python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': 'Compliance check unavailable: transcript missing or unreadable. Cannot verify governance/CE compliance.'
    }
}))
" 2>/dev/null || true
  exit 0
fi

# Scan transcript using shared scanner with recency window
GOV_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"
CE_TOOL="${CE_TOOL_NAME:-mcp__context-engine__query_project}"
RECENCY_WINDOW="${GOVERNANCE_RECENCY_WINDOW:-500}"

debug "Scanning transcript for $GOV_TOOL and $CE_TOOL (window=$RECENCY_WINDOW)"

SCAN_RESULT=$(python3 "$HOOK_DIR/scan_transcript.py" "$GOV_TOOL" "$CE_TOOL" "$TRANSCRIPT_PATH" "$RECENCY_WINDOW" 2>/dev/null) || SCAN_RESULT="neither"

debug "Scan result: $SCAN_RESULT"

# If both found, allow silently
if [ "$SCAN_RESULT" = "both" ]; then
  debug "Both governance and CE found — allowing"
  exit 0
fi

# Build adaptive reminder based on what's missing
GOV_REMINDER=""
CE_REMINDER=""

if [ "$SCAN_RESULT" = "ce_only" ] || [ "$SCAN_RESULT" = "neither" ]; then
  GOV_REMINDER='GOVERNANCE NOT DETECTED: No evaluate_governance() call found in recent transcript. You MUST call evaluate_governance(planned_action="...") before proceeding with file-modifying actions.'
fi

if [ "$SCAN_RESULT" = "gov_only" ] || [ "$SCAN_RESULT" = "neither" ]; then
  CE_REMINDER='CONTEXT ENGINE NOT DETECTED: No query_project() call found in recent transcript. You MUST call query_project(query="...") before creating or modifying code or content to discover existing patterns.'
fi

# Combine reminders
if [ -n "$GOV_REMINDER" ] && [ -n "$CE_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER $CE_REMINDER"
elif [ -n "$GOV_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER"
else
  FULL_REMINDER="$CE_REMINDER"
fi

# Determine if we should deny based on mode
SHOULD_DENY="false"

# Deny if governance is missing and governance is NOT soft mode
if [ -n "$GOV_REMINDER" ] && [ "$GOV_SOFT" != "true" ]; then
  SHOULD_DENY="true"
fi
# Deny if CE is missing and CE is NOT soft mode
if [ -n "$CE_REMINDER" ] && [ "$CE_SOFT" != "true" ]; then
  SHOULD_DENY="true"
fi

if [ "$SHOULD_DENY" = "true" ]; then
  debug "Hard mode active for missing tool(s) — blocking"
  python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': msg
    }
}))
" "$FULL_REMINDER" 2>/dev/null || true
else
  # Soft mode: inject reminder as additionalContext
  debug "Soft mode — injecting reminder for missing tool(s)"
  python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'additionalContext': msg
}))
" "$FULL_REMINDER" 2>/dev/null || true
fi
