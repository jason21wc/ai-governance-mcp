#!/usr/bin/env bash
# PreToolUse hook — checks transcript for evaluate_governance() calls
# before allowing file-modifying operations (Bash|Edit|Write)
#
# Modes:
#   Soft (default): Injects additionalContext reminder if no governance found
#   Hard (GOVERNANCE_HARD_MODE=true): Returns permissionDecision: "deny"
#
# Environment variables:
#   GOVERNANCE_HARD_MODE=true    — Block tool calls when no governance found
#   GOVERNANCE_TOOL_NAME=...     — Override target tool name (default: mcp__ai-governance__evaluate_governance)
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
  if [ "${GOVERNANCE_HARD_MODE:-false}" = "true" ]; then
    # Hard mode: fail-closed — block when transcript unavailable
    debug "Transcript missing/unreadable, hard mode: blocking"
    python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': 'Governance check unavailable: transcript missing or unreadable. Cannot verify governance compliance.'
    }
}))
" 2>/dev/null || true
    exit 0
  fi
  # Soft mode: fail-open — allow silently
  debug "Transcript missing/unreadable, soft mode: allowing"
  exit 0
fi

# Session-level check: scan transcript for ANY evaluate_governance call
# Fast string pre-filter before JSON parse — skips 99% of lines
TARGET_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"

debug "Scanning transcript for $TARGET_TOOL"

FOUND=$(python3 -c "
import json, sys

target = sys.argv[1]
transcript = sys.argv[2]

try:
    with open(transcript, 'r') as f:
        for line in f:
            if target not in line:
                continue
            # Only parse lines that contain the target string
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
                if block.get('type') == 'tool_use' and block.get('name') == target:
                    print('yes')
                    sys.exit(0)
except Exception:
    pass
print('no')
" "$TARGET_TOOL" "$TRANSCRIPT_PATH" 2>/dev/null) || FOUND="no"

# If governance was found, allow silently
if [ "$FOUND" = "yes" ]; then
  debug "Governance call found — allowing"
  exit 0
fi

debug "No governance call found — enforcing"

# No governance call found — enforce
REMINDER="GOVERNANCE NOT DETECTED: No evaluate_governance() call found in this session. You MUST call evaluate_governance(planned_action=\"...\") before proceeding with file-modifying actions. This is a structural enforcement check — the hook system detected you are about to use a file-modifying tool without prior governance consultation."

if [ "${GOVERNANCE_HARD_MODE:-false}" = "true" ]; then
  # Hard mode: block the tool call via PreToolUse permissionDecision
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
" "$REMINDER" 2>/dev/null || true
else
  # Soft mode (default): inject reminder as additionalContext
  python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'additionalContext': msg
}))
" "$REMINDER" 2>/dev/null || true
fi
