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
#   READONLY_BASH_SKIP=true      — Disable read-only Bash allowlist (require governance for all Bash)
#
# Exit 0 always when outputting JSON. Fail-closed on errors (hard mode default).

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/audit-bypass.sh"

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

# ---------------------------------------------------------------------------
# Read-only Bash command allowlist
# Per governance skip list: "reading files" doesn't require governance.
# Provably read-only Bash commands (no redirects, no chaining, all segments
# match a known safe command list — including read-only `git` and `gh`
# subcommands) skip the governance check entirely.
# Disable with READONLY_BASH_SKIP=true.
# ---------------------------------------------------------------------------

TOOL_NAME=""
TOOL_CMD=""
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null) || true
  if [ "$TOOL_NAME" = "Bash" ]; then
    TOOL_CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null) || true
  fi
else
  TOOL_NAME=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_name', ''))
" <<< "$INPUT" 2>/dev/null) || true
  if [ "$TOOL_NAME" = "Bash" ]; then
    TOOL_CMD=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('command', ''))
" <<< "$INPUT" 2>/dev/null) || true
  fi
fi

if [ "$TOOL_NAME" = "Bash" ] && [ -n "$TOOL_CMD" ] && [ "${READONLY_BASH_SKIP:-false}" != "true" ]; then
  IS_READONLY=$(python3 -c "
import re, sys
cmd = sys.argv[1]
# Chaining operators make the command non-read-only
if re.search(r'&&|\|\||;', cmd):
    print('false')
    sys.exit(0)
# Strip safe stderr redirections before checking for output redirects
cleaned = re.sub(r'2>>[^ ;|&()<>]*|2>&[^ ;|&()<>]*|2>\s*[^ ;|&()<>]*', '', cmd)
if re.search(r'>>', cleaned) or re.search(r'>', cleaned):
    print('false')
    sys.exit(0)
# Split on pipe and check each segment
READONLY_CMDS = {
    'ls', 'find', 'grep', 'egrep', 'fgrep', 'wc', 'head', 'tail', 'cat',
    'file', 'stat', 'which', 'pwd', 'tree', 'du', 'df', 'diff', 'sort',
    'uniq', 'comm', 'jq', 'column', 'basename', 'dirname', 'realpath',
    'readlink', 'sha256sum', 'md5',
}
GIT_READONLY = {
    'log', 'blame', 'diff', 'show', 'status', 'branch', 'remote', 'tag',
    'rev-parse', 'ls-files', 'ls-tree', 'name-rev', 'shortlog', 'describe',
    'for-each-ref', 'stash',
}
# gh is dual-use (gh pr merge / gh repo delete mutate remote state), so the
# base command cannot be blanket-allowed. Allow only enumerated read-only
# (command, subcommand) pairs; gh api is GET-only unless a write flag appears.
GH_READONLY = {
    ('repo', 'view'), ('repo', 'list'),
    ('pr', 'view'), ('pr', 'list'), ('pr', 'diff'), ('pr', 'checks'), ('pr', 'status'),
    ('issue', 'view'), ('issue', 'list'), ('issue', 'status'),
    ('run', 'view'), ('run', 'list'), ('run', 'watch'),
    ('release', 'view'), ('release', 'list'),
    ('workflow', 'view'), ('workflow', 'list'),
    ('label', 'list'), ('cache', 'list'),
    ('auth', 'status'),
    ('search', 'prs'), ('search', 'issues'), ('search', 'repos'), ('search', 'code'),
}
GH_API_WRITE_PREFIXES = ('-X', '--method', '-f', '-F', '--field', '--raw-field', '--input')
for segment in cmd.split('|'):
    parts = segment.strip().split()
    if not parts:
        print('false')
        sys.exit(0)
    base = parts[0].rsplit('/', 1)[-1]
    if base == 'git':
        subcmd = parts[1] if len(parts) > 1 else ''
        if subcmd not in GIT_READONLY:
            print('false')
            sys.exit(0)
    elif base == 'gh':
        args = parts[1:]
        if not args:
            print('false')
            sys.exit(0)
        if args[0] == 'api':
            # gh api defaults to GET; a method/field write flag makes it a mutation
            if any(a.startswith(GH_API_WRITE_PREFIXES) for a in args[1:]):
                print('false')
                sys.exit(0)
        else:
            pair = (args[0], args[1] if len(args) > 1 else '')
            if pair not in GH_READONLY:
                print('false')
                sys.exit(0)
    elif base not in READONLY_CMDS:
        print('false')
        sys.exit(0)
print('true')
" "$TOOL_CMD" 2>/dev/null) || IS_READONLY="false"

  if [ "$IS_READONLY" = "true" ]; then
    debug "Read-only Bash command — governance check skipped"
    exit 0
  fi
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

if [ "$GOV_SOFT" = "true" ]; then
  audit_bypass "pre-tool-governance-check" "GOVERNANCE_SOFT_MODE=true" "soft-mode"
fi
if [ "$CE_SOFT" = "true" ]; then
  audit_bypass "pre-tool-governance-check" "CE_SOFT_MODE=true" "soft-mode"
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
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'additionalContext': msg
    }
}))
" "$FULL_REMINDER" 2>/dev/null || true
fi
