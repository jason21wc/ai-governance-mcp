#!/usr/bin/env bash
# SessionStart hook — project cadence surfacer (ai-governance only).
#
# At session start, reads each project cadence's "Next due:" date from
# OPERATIONS.md (git as parse-fallback) and injects ONE consolidated reminder
# listing only the cadences that are DUE/OVERDUE. Silent when nothing is due.
#
# Scope of the guarantee (honest framing):
#   STRUCTURAL surfacing — the date-check happens deterministically every
#   session start, removing the "did I remember to read OPERATIONS.md?" gap.
#   ADVISORY action — acting on the nudge is still the agent's call. This is the
#   proportionate level for periodic *maintenance* cadences; a hard gate would
#   block unrelated work.
#
# Why SessionStart (not SessionEnd): SessionEnd runs async AFTER the session has
# terminated, with no agent left to run a skill. SessionStart can inject context
# at the start of the next session — the reliable seam. See EXECUTION-FRAMEWORK
# §7.2 and CFR §7.11.
#
# Env vars:
#   CADENCE_SKIP=1       — disable entirely (audit-logged)
#   CADENCE_DEBUG=true   — stderr debug logging
#
# Exit 0 always — a SessionStart hook must never block startup.
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/audit-bypass.sh
source "$HOOK_DIR/lib/audit-bypass.sh"
# shellcheck source=lib/cadence.sh
source "$HOOK_DIR/lib/cadence.sh"

debug() { if [ "${CADENCE_DEBUG:-false}" = "true" ]; then echo "[cadence-hook] $1" >&2; fi; }

if [ "${CADENCE_SKIP:-}" = "1" ]; then
    audit_bypass "session-start-cadence" "CADENCE_SKIP=1" "structural-bypass"
    debug "CADENCE_SKIP=1, exiting"
    exit 0
fi

INPUT=$(cat 2>/dev/null || echo '{}')

SOURCE=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('source', ''))
except Exception:
    print('')
" 2>/dev/null || echo '')

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('cwd', ''))
except Exception:
    print('')
" 2>/dev/null || echo '')
fi
[ -z "$PROJECT_DIR" ] && PROJECT_DIR="$PWD"

# Fire on startup/resume/clear; skip compact (mid-session, not a session boundary).
case "$SOURCE" in
    compact) debug "source=compact, skipping (mid-session)"; exit 0 ;;
esac

OPS="$PROJECT_DIR/OPERATIONS.md"
# Project-scope guard: this surfacer only applies where the cadence registry lives.
if [ ! -f "$OPS" ]; then
    debug "no OPERATIONS.md at $PROJECT_DIR, exiting (not an ai-governance project)"
    exit 0
fi

DUE_ITEMS=()

# check_cadence <anchor> <git_grep_pattern> <fallback_window_days> <label>
check_cadence() {
    local anchor="$1" grep_pat="$2" window="$3" label="$4"
    local due_date du gdate

    due_date=$(next_due_from_operations "$OPS" "$anchor")
    if [ -n "$due_date" ]; then
        du=$(days_until "$due_date")
        if [ "$du" -le 0 ]; then
            DUE_ITEMS+=("$label (due $due_date)")
        fi
        return 0
    fi

    # Fallback: last matching commit + cadence window.
    gdate=$(last_git_date "$PROJECT_DIR" "$grep_pat")
    if [ -n "$gdate" ]; then
        if [ "$(days_since "$gdate")" -ge "$window" ]; then
            DUE_ITEMS+=("$label (last activity $gdate, cadence ${window}d)")
        fi
        return 0
    fi

    # Neither source resolved — surface for manual verification (fail-toward).
    DUE_ITEMS+=("$label (no due date found — verify in OPERATIONS.md)")
    return 0
}

check_cadence "C-078" "compliance review" 10 "C-078 Compliance Review → run /compliance-review"
check_cadence "C-155" "feedback loop"     20 "C-155 Feedback Loop Analysis → run analyze_feedback_loop"
check_cadence "C-109" "deferred.cadence"  30 "C-109 Deferred-cadence audit → review OPERATIONS.md C-109"

if [ "${#DUE_ITEMS[@]}" -eq 0 ]; then
    debug "nothing due, staying silent"
    exit 0
fi

MSG="Session cadence check (ai-governance) — DUE:"
for item in "${DUE_ITEMS[@]}"; do
    MSG="$MSG"$'\n'"  • $item"
done
MSG="$MSG"$'\n'"(Surfaced automatically at session start; run when appropriate — these are periodic maintenance, not blocking.)"

python3 -c "import json, sys; sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$MSG" 2>/dev/null || true
exit 0
