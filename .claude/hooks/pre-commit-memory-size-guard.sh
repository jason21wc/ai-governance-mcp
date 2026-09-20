#!/usr/bin/env bash
# Memory size review — all checks are ADVISORY, never commit gates (#367).
# Counts surface a need for quality review; they do not justify merging, deleting,
# or graduating content solely to meet a number. Graduation is a judgment, not a
# non-destructive mechanical fix for a size limit.
#
# Targets: LEARNING-LOG 200 TOTAL lines, including Graduated Patterns (§7.0.4);
# BACKLOG 60 discrete items; SESSION-STATE 300 lines (§7.0.4).
# Bypass: MEMORY_SIZE_SKIP=1 (audit-logged).
#
# One measurement, two emission modes. Claude PreToolUse reads a `git commit`
# tool call from stdin and receives additionalContext JSON. --direct needs no
# stdin or command detection and prints plain text for pre-commit. Both exit 0;
# pre-commit's verbose setting keeps the passing hook's notices visible.

set -uo pipefail

DIRECT=0
if [ "${1:-}" = "--direct" ]; then
    DIRECT=1
fi

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[ -f "$HOOK_DIR/lib/audit-bypass.sh" ] && . "$HOOK_DIR/lib/audit-bypass.sh"

if [ "$DIRECT" -eq 1 ]; then
    # No tool call to read. resolve_session_root falls back to $PWD, which is the
    # repo root under pre-commit.
    INPUT='{}'
else
    INPUT=$(cat 2>/dev/null || echo '{}')
fi

if [ "${MEMORY_SIZE_SKIP:-}" = "1" ]; then
    if command -v audit_bypass >/dev/null 2>&1; then
        audit_bypass "pre-commit-memory-size-guard" "MEMORY_SIZE_SKIP=1" "advisory-skip"
    fi
    exit 0
fi

# --- Command detection (Claude PreToolUse only; --direct is already at a commit) ---
if [ "$DIRECT" -eq 0 ]; then
COMMAND=""
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
if [ -z "$COMMAND" ]; then
    COMMAND=$(echo "$INPUT" | python3 -c \
        "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
        2>/dev/null || echo "")
fi

case "$COMMAND" in
    *"git commit"*) ;;
    *) exit 0 ;;
esac
fi

# --- Resolve project root ---
# shellcheck source=/dev/null
if [ -f "$HOOK_DIR/lib/repo-root.sh" ]; then
    . "$HOOK_DIR/lib/repo-root.sh"
    resolve_session_root "$INPUT"
    PROJECT_DIR="${SESSION_ROOT:-$PWD}"
else
    PROJECT_DIR="$PWD"
fi

CTX="$PROJECT_DIR/_ai-context"
NOTICES=""    # advisory — report for quality review, commit proceeds

# --- LEARNING-LOG: total file lines, including graduated patterns ---
LL="$CTX/LEARNING-LOG.md"
if [ -f "$LL" ]; then
    LL_LINES=$(wc -l < "$LL" | tr -d ' ')
    LL_LIMIT=200
    if [ "$LL_LINES" -gt "$LL_LIMIT" ]; then
        NOTICES="${NOTICES}📋 LEARNING-LOG is at ${LL_LINES} total lines, including graduated patterns (target: ${LL_LIMIT}, §7.0.4). Not blocking. Review content quality and whether lessons are still useful; do NOT merge, delete, or graduate entries solely to meet the count.\\n"
    fi
fi

# --- BACKLOG: heading count is a proxy, reported for human triage ---
# A blocking count previously induced merging unrelated items to clear the gate.
# SESSION-STATE and LEARNING-LOG also require judgment about live information;
# none of these counts establishes that deleting or condensing content is safe.
BL="$CTX/BACKLOG.md"
if [ -f "$BL" ]; then
    # `grep -c` prints 0 AND exits 1 when there are no matches, so `|| echo "0"`
    # appends a SECOND zero — "0\n0" — which breaks the -gt comparison and would be
    # interpolated raw into the JSON below. Only reachable on an empty backlog, which
    # is why no fixture caught it.
    ITEM_COUNT=$(grep -c '^#### ' "$BL" 2>/dev/null || true)
    ITEM_COUNT=${ITEM_COUNT:-0}
    BL_LIMIT=60
    if [ "$ITEM_COUNT" -gt "$BL_LIMIT" ]; then
        NOTICES="${NOTICES}📋 BACKLOG is at ${ITEM_COUNT} items (soft target: ${BL_LIMIT}). Not blocking. Tell the user it is getting long and let them decide what to triage — do NOT merge or close items to bring the number down.\\n"
    fi
fi

# --- SESSION-STATE: total line count — ADVISORY, never blocking (see above) ---
SS="$CTX/SESSION-STATE.md"
if [ -f "$SS" ]; then
    SS_LINES=$(wc -l < "$SS")
    SS_LIMIT=300
    if [ "$SS_LINES" -gt "$SS_LIMIT" ]; then
        NOTICES="${NOTICES}📋 SESSION-STATE is at ${SS_LINES} lines (target: ${SS_LIMIT}, §7.0.4). Not blocking. Tell the user, and prune only after deciding what is genuinely stale — route live decisions to PROJECT-MEMORY and lessons to LEARNING-LOG rather than deleting them to hit the number.\\n"
    fi
fi

if [ "$DIRECT" -eq 1 ]; then
    [ -n "$NOTICES" ] && printf 'Memory size guard (advisory):\n%b' "$NOTICES"
    exit 0
fi

if [ -n "$NOTICES" ]; then
    # Advisory only — the commit proceeds. Surfaced as context so the agent reports it
    # to the human instead of acting on it.
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"${NOTICES}\"}}"
    exit 0
fi

exit 0
