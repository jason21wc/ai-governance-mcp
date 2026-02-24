#!/usr/bin/env bash
# PreToolUse hook — checks transcript for evaluate_governance() AND query_project() calls
# before allowing file-modifying operations (Bash|Edit|Write)
#
# Scans for both tools in a single transcript pass with adaptive output.
#
# Modes:
#   Soft (default): Injects additionalContext reminder for missing tool(s)
#   Hard (GOVERNANCE_HARD_MODE / CE_HARD_MODE): Returns permissionDecision: "deny"
#
# Environment variables:
#   GOVERNANCE_HARD_MODE=true    — Block tool calls when no governance found
#   CE_HARD_MODE=true            — Block tool calls when no CE query found
#   GOVERNANCE_TOOL_NAME=...     — Override governance tool name (default: mcp__ai-governance__evaluate_governance)
#   CE_TOOL_NAME=...             — Override CE tool name (default: mcp__context-engine__query_project)
#   GOVERNANCE_HOOK_DEBUG=true   — Enable stderr debug logging
#
# Exit 0 always when outputting JSON. Fail-open on errors (soft mode) / fail-closed (hard mode).

set -euo pipefail

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

# Handle missing/unreadable transcript
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -r "$TRANSCRIPT_PATH" ]; then
  GOV_HARD="${GOVERNANCE_HARD_MODE:-false}"
  CE_HARD="${CE_HARD_MODE:-false}"
  if [ "$GOV_HARD" = "true" ] || [ "$CE_HARD" = "true" ]; then
    # Hard mode: fail-closed — block when transcript unavailable
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
  # Soft mode: fail-open — allow silently
  debug "Transcript missing/unreadable, soft mode: allowing"
  exit 0
fi

# Session-level check: scan transcript for BOTH tool calls in one pass
# Fast string pre-filter before JSON parse — skips ~99% of lines
GOV_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"
CE_TOOL="${CE_TOOL_NAME:-mcp__context-engine__query_project}"

debug "Scanning transcript for $GOV_TOOL and $CE_TOOL"

# Output: "both", "gov_only", "ce_only", or "neither"
SCAN_RESULT=$(python3 -c "
import json, sys

gov_target = sys.argv[1]
ce_target = sys.argv[2]
transcript = sys.argv[3]

gov_found = False
ce_found = False

try:
    with open(transcript, 'r') as f:
        for line in f:
            # Fast pre-filter: skip lines that contain neither target
            if gov_target not in line and ce_target not in line:
                continue
            # Only parse lines that contain at least one target string
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            # Check assistant tool_use entries
            msg = entry.get('message', {})
            if not isinstance(msg, dict):
                continue
            for block in msg.get('content', []):
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'tool_use':
                    name = block.get('name', '')
                    if name == gov_target:
                        gov_found = True
                    elif name == ce_target:
                        ce_found = True
            # Early exit if both found
            if gov_found and ce_found:
                break
except Exception:
    pass

if gov_found and ce_found:
    print('both')
elif gov_found:
    print('gov_only')
elif ce_found:
    print('ce_only')
else:
    print('neither')
" "$GOV_TOOL" "$CE_TOOL" "$TRANSCRIPT_PATH" 2>/dev/null) || SCAN_RESULT="neither"

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
  GOV_REMINDER='GOVERNANCE NOT DETECTED: No evaluate_governance() call found in this session. You MUST call evaluate_governance(planned_action="...") before proceeding with file-modifying actions.'
fi

if [ "$SCAN_RESULT" = "gov_only" ] || [ "$SCAN_RESULT" = "neither" ]; then
  CE_REMINDER='CONTEXT ENGINE NOT DETECTED: No query_project() call found in this session. You MUST call query_project(query="...") before creating or modifying code or content to discover existing patterns.'
fi

# Combine reminders
if [ -n "$GOV_REMINDER" ] && [ -n "$CE_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER $CE_REMINDER"
elif [ -n "$GOV_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER"
else
  FULL_REMINDER="$CE_REMINDER"
fi

# Check if hard mode should block
GOV_HARD="${GOVERNANCE_HARD_MODE:-false}"
CE_HARD="${CE_HARD_MODE:-false}"
SHOULD_DENY="false"

# Deny if governance is missing and governance hard mode is on
if [ -n "$GOV_REMINDER" ] && [ "$GOV_HARD" = "true" ]; then
  SHOULD_DENY="true"
fi
# Deny if CE is missing and CE hard mode is on
if [ -n "$CE_REMINDER" ] && [ "$CE_HARD" = "true" ]; then
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
  # Soft mode (default): inject reminder as additionalContext
  debug "Soft mode — injecting reminder for missing tool(s)"
  python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'additionalContext': msg
}))
" "$FULL_REMINDER" 2>/dev/null || true
fi
