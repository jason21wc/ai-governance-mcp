#!/usr/bin/env bash
# PreToolUse hook — Content-level credential path gate
# Blocks Bash commands that access credential file paths on the host machine.
# Defense-in-depth Layer 2 alongside Read-tool deny rules in settings (Layer 1).
#
# Credential paths blocked:
#   ~/.ssh/*  ~/.aws/*  ~/.gnupg/*  ~/.netrc  ~/.docker/config.json
#   ~/.kube/config  ~/.npmrc  /etc/ssl/private/*  *.key (private keys)
#
# Threat model: AI-initiated Bash commands that read credential files the
# machine holds. User-level Read deny rules (Layer 1) cover the Read tool;
# this hook covers Bash cat/head/tail/less/cp/scp/curl/base64 etc.
#
# Escape hatch:
#   CONTENT_SECURITY_SKIP=1  — bypass when the gate is wrong
#
# Author: Claude Opus 4.6 + Jason Collier, 2026-05-03
# Origin: BACKLOG #19 (Content-Level Security Enforcement)

set -euo pipefail

# Fail-closed: unhandled errors → exit 2 (deny)
trap 'exit 2' ERR

# ---------------------------------------------------------------------------
# Parse stdin
# ---------------------------------------------------------------------------

if command -v jq >/dev/null 2>&1; then
    _parse_command() { jq -r '.tool_input.command // ""' 2>/dev/null || echo ""; }
else
    _parse_command() {
        python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
            2>/dev/null || echo ""
    }
fi

INPUT=$(cat)
COMMAND=$(printf '%s\n' "$INPUT" | _parse_command)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# ---------------------------------------------------------------------------
# Bypass
# ---------------------------------------------------------------------------

if [ "${CONTENT_SECURITY_SKIP:-}" = "1" ]; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ Content security gate bypassed via CONTENT_SECURITY_SKIP=1. Credential path access allowed."}}'
    exit 0
fi

# ---------------------------------------------------------------------------
# Credential path detection
# ---------------------------------------------------------------------------
# Expand ~ and $HOME to the literal home directory for matching.
# Match against both symbolic forms (~/, $HOME/, ${HOME}/) and the expanded path.

HOME_DIR="$HOME"
HOME_ESCAPED=$(printf '%s' "$HOME_DIR" | sed 's/[.[\*^$()+?{|]/\\&/g')

# Build the credential path patterns. Each pattern is checked against the
# command string. A match anywhere in the command triggers a deny.
#
# Scoping: only MACHINE-LEVEL credential paths (~/.<dir>). Project-relative
# .env files are covered by Read deny rules and are not this hook's scope
# (project .env may be legitimate; ~/.ssh is never legitimate for AI access).
CRED_PATTERNS=(
    '~/.ssh/'
    '~/.aws/'
    '~/.gnupg/'
    '~/.netrc'
    '~/.docker/config.json'
    '~/.kube/config'
    '~/.npmrc'
    "\$HOME/.ssh/"
    "\${HOME}/.ssh/"
    "\$HOME/.aws/"
    "\${HOME}/.aws/"
    "\$HOME/.gnupg/"
    "\${HOME}/.gnupg/"
    "\$HOME/.netrc"
    "\${HOME}/.netrc"
    "\$HOME/.docker/config.json"
    "\${HOME}/.docker/config.json"
    "\$HOME/.kube/config"
    "\${HOME}/.kube/config"
    "\$HOME/.npmrc"
    "\${HOME}/.npmrc"
    "${HOME_ESCAPED}/.ssh/"
    "${HOME_ESCAPED}/.aws/"
    "${HOME_ESCAPED}/.gnupg/"
    "${HOME_ESCAPED}/.netrc"
    "${HOME_ESCAPED}/.docker/config.json"
    "${HOME_ESCAPED}/.kube/config"
    "${HOME_ESCAPED}/.npmrc"
    '/etc/ssl/private/'
)

# Also match private key file extensions anywhere in the path
KEY_PATTERN='\.key([[:space:]]|$)'

MATCHED_PATH=""

for pattern in "${CRED_PATTERNS[@]}"; do
    if printf '%s\n' "$COMMAND" | grep -qF "$pattern" 2>/dev/null; then
        MATCHED_PATH="$pattern"
        break
    fi
done

if [ -z "$MATCHED_PATH" ]; then
    if printf '%s\n' "$COMMAND" | grep -qE "$KEY_PATTERN" 2>/dev/null; then
        MATCHED_PATH="*.key (private key file)"
    fi
fi

if [ -z "$MATCHED_PATH" ]; then
    BARE_DIR_PATTERN="(~|\\\$HOME|\\\$\{HOME\}|${HOME_ESCAPED})/\.(ssh|aws|gnupg)([[:space:];|&><)\`]|$)"
    if printf '%s\n' "$COMMAND" | grep -qE "$BARE_DIR_PATTERN" 2>/dev/null; then
        MATCHED_PATH="credential directory (bare reference)"
    fi
fi

# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

if [ -z "$MATCHED_PATH" ]; then
    exit 0
fi

printf '%s\n' "content-security: denied [${MATCHED_PATH}]" >&2

REASON="CREDENTIAL ACCESS BLOCKED: command references a credential path.

This hook blocks Bash commands that access machine-level credential files
(~/.ssh/*, ~/.aws/*, ~/.gnupg/*, ~/.netrc, ~/.docker/config.json,
~/.kube/config, ~/.npmrc, /etc/ssl/private/*, *.key).

These files contain secrets that should never be read by AI agents.

If this is a false positive (e.g., you genuinely need to access this path):
  CONTENT_SECURITY_SKIP=1 <your command>

Origin: BACKLOG #19 (Content-Level Security Enforcement, Layer 2)"

if ! python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$REASON"; then
    echo "CREDENTIAL ACCESS BLOCKED. python3 unavailable; use CONTENT_SECURITY_SKIP=1 to bypass." >&2
    exit 2
fi

exit 0
