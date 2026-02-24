#!/usr/bin/env bash
# UserPromptSubmit hook — injects governance reminder on every prompt
# Outputs JSON with additionalContext to reinforce governance protocol
#
# Environment variables:
#   GOVERNANCE_HOOK_DEBUG=true — Enable stderr debug logging
#
# Exit 0 always — never blocks, never errors

set -euo pipefail

if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
  echo "[governance-hook] UserPromptSubmit hook invoked" >&2
fi

REMINDER='GOVERNANCE PROTOCOL ACTIVE: Call evaluate_governance(planned_action="...") before any Bash|Edit|Write action unless it is: reading files, answering non-sensitive questions, trivial formatting, or user explicitly says "skip governance". If you already called evaluate_governance() this session for the current task batch, you may proceed. Cite principle IDs when they influence your approach. CONTEXT ENGINE: Call query_project(query="...") before creating or modifying code or content to discover existing patterns.'

# Output JSON with additionalContext — python3 for safe serialization
python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({'additionalContext': msg}))
" "$REMINDER" 2>/dev/null || true
