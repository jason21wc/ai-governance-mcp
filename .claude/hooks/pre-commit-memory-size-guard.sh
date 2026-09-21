#!/usr/bin/env bash
# Memory size review — all checks are ADVISORY, never commit gates (#367).
# Counts never justify merging, deleting, or graduating content solely for size.
# Targets: LEARNING-LOG 200 TOTAL lines, including Graduated Patterns (§7.0.4);
# BACKLOG 60 discrete items; SESSION-STATE 300 lines (§7.0.4).
# Entry ranking is descriptive, without a character ceiling (#369).
# Bypass: MEMORY_SIZE_SKIP=1 (audit-logged).
# --direct prints plain text without stdin; Claude PreToolUse receives JSON.
# pre-commit's verbose setting keeps these passing notices visible.
set -uo pipefail

DIRECT=0
[ "${1:-}" = "--direct" ] && DIRECT=1
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[ -f "$HOOK_DIR/lib/audit-bypass.sh" ] && . "$HOOK_DIR/lib/audit-bypass.sh"

if [ "$DIRECT" -eq 1 ]; then
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

# Fixed diagnostics must work even without Python or a usable JSON serializer.
inspection_unavailable() {
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"Memory size guard: command/root inspection unavailable; entry report unavailable. No checkout was measured."}}'
    exit 0
}

if [ "$DIRECT" -eq 0 ]; then
    COMMAND=""
    if COMMAND=$(printf '%s' "$INPUT" | jq -er '.tool_input.command // "" | strings' 2>/dev/null); then
        :
    elif COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import json,sys; c=json.load(sys.stdin).get("tool_input",{}).get("command", ""); assert isinstance(c,str); print(c)' 2>/dev/null); then
        :
    else
        inspection_unavailable
    fi
    case "$COMMAND" in
        *"git commit"*) ;;
        *) exit 0 ;;
    esac
    # The shared resolver uses Python for payload cwd. Never let its fallback
    # silently measure process PWD when that decoder cannot run.
    python3 -c 'import json' 2>/dev/null || inspection_unavailable
    [ -f "$HOOK_DIR/lib/repo-root.sh" ] || inspection_unavailable
    # shellcheck source=/dev/null
    . "$HOOK_DIR/lib/repo-root.sh"
    resolve_session_root "$INPUT"
    PROJECT_DIR="$SESSION_ROOT"
else
    # PWD is the explicit starting point; retain normal worktree-root resolution
    # even for a direct invocation from a subdirectory, without needing Python.
    PROJECT_DIR=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null) || PROJECT_DIR="$PWD"
    [ -n "$PROJECT_DIR" ] || PROJECT_DIR="$PWD"
fi

CTX="$PROJECT_DIR/_ai-context"
NOTICES=""
add_notice() {
    # Real newlines throughout: title backslash escapes must never be interpreted.
    NOTICES="${NOTICES}${1}"$'\n'
}

LL="$CTX/LEARNING-LOG.md"
REPORT_ENTRIES=0
if [ -f "$LL" ]; then
    LL_LIMIT=200
    if LL_LINES=$(wc -l < "$LL" 2>/dev/null | tr -d '[:space:]'); then
        if [ "$LL_LINES" -gt "$LL_LIMIT" ]; then
            REPORT_ENTRIES=1
            add_notice "📋 LEARNING-LOG is at ${LL_LINES} total lines, including graduated patterns (target: ${LL_LIMIT}, §7.0.4). Not blocking. Review content quality and whether lessons are still useful; do NOT merge, delete, or graduate entries solely to meet the count."
        fi
    else
        REPORT_ENTRIES=1
        add_notice 'LEARNING-LOG line count unavailable; entry report unavailable if the file cannot be read.'
    fi

    # A Git failure is unknown, not unchanged. The one expected outside-Git
    # error is distinguished from broken Git/permissions with a fixed locale.
    if GIT_SCOPE=$(LC_ALL=C git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree 2>&1); then
        if [ "$GIT_SCOPE" = true ]; then
            if LL_STATUS=$(git -C "$PROJECT_DIR" status --porcelain --untracked-files=all -- '_ai-context/LEARNING-LOG.md' 2>/dev/null); then
                [ -n "$LL_STATUS" ] && REPORT_ENTRIES=1
            else
                add_notice 'Git status unavailable; Learning Log change state is unknown. Inspecting entries.'
                REPORT_ENTRIES=1
            fi
        fi
    else
        case "$GIT_SCOPE" in
            *'not a git repository'*) [ "$DIRECT" -eq 1 ] && REPORT_ENTRIES=1 ;;
            *) add_notice 'Git status unavailable; Learning Log change state is unknown. Inspecting entries.'
               REPORT_ENTRIES=1 ;;
        esac
    fi

    if [ "$REPORT_ENTRIES" -eq 1 ] && [ -s "$LL" ]; then
        if ENTRY_REPORT=$(python3 "$HOOK_DIR/lib/memory-entry-size.py" "$LL" 2>/dev/null); then
            [ -n "$ENTRY_REPORT" ] && add_notice "$ENTRY_REPORT"
        else
            add_notice 'Learning Log entry report unavailable; available whole-file notices still apply.'
        fi
    fi
fi

BL="$CTX/BACKLOG.md"
if [ -f "$BL" ]; then
    ITEM_COUNT=$(grep -c '^#### ' "$BL" 2>/dev/null || true)
    ITEM_COUNT=${ITEM_COUNT:-0}
    BL_LIMIT=60
    if [ "$ITEM_COUNT" -gt "$BL_LIMIT" ]; then
        add_notice "📋 BACKLOG is at ${ITEM_COUNT} items (soft target: ${BL_LIMIT}). Not blocking. Tell the user it is getting long and let them decide what to triage — do NOT merge or close items to bring the number down."
    fi
fi

SS="$CTX/SESSION-STATE.md"
if [ -f "$SS" ]; then
    SS_LIMIT=300
    if SS_LINES=$(wc -l < "$SS" 2>/dev/null | tr -d '[:space:]'); then
        if [ "$SS_LINES" -gt "$SS_LIMIT" ]; then
            add_notice "📋 SESSION-STATE is at ${SS_LINES} lines (target: ${SS_LIMIT}, §7.0.4). Not blocking. Tell the user, and prune only after deciding what is genuinely stale — route live decisions to PROJECT-MEMORY and lessons to LEARNING-LOG rather than deleting them to hit the number."
        fi
    else
        add_notice 'SESSION-STATE line count unavailable.'
    fi
fi

if [ "$DIRECT" -eq 1 ]; then
    [ -n "$NOTICES" ] && printf 'Memory size guard (advisory):\n%s' "$NOTICES"
    exit 0
fi
if [ -n "$NOTICES" ]; then
    # Capture first: even a failing serializer's partial stdout is never emitted.
    if OUTPUT=$(printf '%s' "$NOTICES" | python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":sys.stdin.read()}}))'); then
        printf '%s\n' "$OUTPUT"
    else
        printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"Memory size guard output unavailable; entry report unavailable. Measurement notices could not be serialized."}}'
    fi
fi
exit 0
