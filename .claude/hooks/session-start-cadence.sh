#!/usr/bin/env bash
# SessionStart hook — project cadence surfacer (ai-governance only).
#
# At session start, reads each project cadence's "Next due:" date from the
# repository-canonical OPERATIONS.md (local `main`, then `origin/main`, then this
# checkout's working copy; git log as parse-fallback) and injects ONE consolidated reminder
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
#   CADENCE_CANONICAL_REF=0 — read OPERATIONS.md from THIS checkout's working copy
#                        instead of the canonical ref (escape hatch for a project
#                        whose cadence registry legitimately differs per branch)
#
# Exit 0 always — a SessionStart hook must never block startup.
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

# LIBRARY LOADING — one mechanism for every lib (BACKLOG #236).
#
# THIS HOOK WAS MISSED BY THE FIRST #236 FIX, which is the finding worth keeping.
# That fix repaired session-start-dream.sh and session-start-genesis.sh and shipped
# a test asserting it covered "the class" — while the test enumerated those same two
# hooks in a hardcoded dict, so this third SessionStart hook, carrying the identical
# defect in the same directory, was invisible to it. Fixing the members you already
# know about and calling it a class is the defect, one level up. The test now derives
# its hook list from this directory instead of restating it.
#
# The defect itself: `repo-root.sh` was guarded with a graceful degrade while
# `audit-bypass.sh` and `cadence.sh` were sourced bare directly above it, so under
# `set -euo pipefail` a missing lib exits 1 before the guard runs — in a file whose
# own header says "Exit 0 always."
load_lib() {
    local lib="$HOOK_DIR/lib/$1"
    [ -f "$lib" ] || return 1
    "${BASH:-bash}" -n "$lib" 2>/dev/null || return 1
    # shellcheck source=/dev/null
    source "$lib" || return 1
}
for _lib in audit-bypass.sh cadence.sh repo-root.sh; do
    load_lib "$_lib" || exit 0
done

debug() { if [ "${CADENCE_DEBUG:-false}" = "true" ]; then echo "[cadence-hook] $1" >&2; fi; }

if [ "${CADENCE_SKIP:-}" = "1" ]; then
    audit_bypass "session-start-cadence" "CADENCE_SKIP=1" "structural-bypass"
    debug "CADENCE_SKIP=1, exiting"
    exit 0
fi

INPUT=$(cat 2>/dev/null || echo '{}')

# `or ''` rather than a .get default: a key PRESENT with a JSON null returns None,
# and `print(None)` emits the string "None". That reached `dirname "None"` -> ".",
# which is a real directory, so the transcript count was silently taken from the
# hook's CWD instead of falling back to the project's transcript dir — a confident
# "~0 sessions" for a watch whose entire output is the count. Reproduced.
# (`$1` is interpolated into the program text, which is safe only because every
# call site passes a literal field name; keep it that way.)
read_field() {
    printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('$1') or '')
except Exception:
    print('')
" 2>/dev/null || echo ''
}

SOURCE=$(read_field source)
TRANSCRIPT_PATH=$(read_field transcript_path)

# Root resolution lives in lib/repo-root.sh (BACKLOG #214) — payload cwd first,
# CLAUDE_PROJECT_DIR last. It is not "the project": the dream fire log shows it
# resolving to three different worktrees AND the primary across 103 firings.
resolve_session_root "$INPUT"
PROJECT_DIR="$SESSION_ROOT"
debug "session root=$PROJECT_DIR via ${SESSION_ROOT_PROVENANCE:-unknown}"

# Fire on startup/resume/clear; skip compact (mid-session, not a session boundary).
case "$SOURCE" in
    compact) debug "source=compact, skipping (mid-session)"; exit 0 ;;
esac

# Project-scope guard: this surfacer only applies where the cadence registry
# lives. Unified layout (v2.62.0): check the root (grandfathered pre-v2.62.0
# layout) first, then _ai-context/ — and name which one matched (layout detector).
OPS=""
if [ -f "$PROJECT_DIR/OPERATIONS.md" ]; then
    OPS="$PROJECT_DIR/OPERATIONS.md"
    OPS_REL="OPERATIONS.md"
    debug "OPERATIONS.md found at project root (grandfathered layout)"
elif [ -f "$PROJECT_DIR/_ai-context/OPERATIONS.md" ]; then
    OPS="$PROJECT_DIR/_ai-context/OPERATIONS.md"
    OPS_REL="_ai-context/OPERATIONS.md"
    debug "OPERATIONS.md found in _ai-context/ (unified layout)"
else
    debug "no OPERATIONS.md at $PROJECT_DIR (root or _ai-context/), exiting (not an ai-governance project)"
    exit 0
fi

# A cadence due-date is meant to be ONE-PER-REPOSITORY, but it is stored in a
# versioned file — which makes it checkout-VARIANT (branches disagree), not the
# project-wide constant it reads as. Prefer the canonical ref so every worktree
# gets the same answer; fall back to this checkout's copy when there is no ref
# to read (fresh clone, no remote, or the file exists only in the working tree).
# The old code read whichever tree CLAUDE_PROJECT_DIR named, which is how a
# reminder fired in a worktree for a cadence that was not due (2026-07-12).
OPS_SOURCE="working tree"
if [ "${CADENCE_CANONICAL_REF:-1}" != "0" ]; then
    _ops_canon=$(mktemp 2>/dev/null || echo '')
    if [ -n "$_ops_canon" ]; then
        trap 'rm -f "$_ops_canon"' EXIT INT TERM
        if canonical_snapshot "$PROJECT_DIR" "$OPS_REL" "$_ops_canon"; then
            OPS="$_ops_canon"
            OPS_SOURCE="canonical ref ${CANONICAL_SNAPSHOT_REF:-?}"
        else
            rm -f "$_ops_canon"
        fi
    fi
fi
debug "reading cadence dates from $OPS_SOURCE"

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

# check_watch <anchor> <window_sessions> <label>
#   COUNT-BASED observation window (RW-series), the other kind of item OPERATIONS.md
#   carries. A cadence is due on a DATE; a watch is due after N SESSIONS, so nothing
#   above could ever surface one — and that is not a hypothetical. RW-313 sat at
#   "0 of 3" while sessions ran and closed, because the tally only moved if a session
#   remembered to hand-edit OPERATIONS.md at its own close. Session end is precisely
#   the seam this hook's header already documents as unreliable (SessionEnd runs after
#   the agent is gone), which is why the count is computed here instead of trusted
#   there.
#
#   SURFACES EVERY SESSION WHILE THE WATCH IS OPEN, not only when the window fills.
#   A session that never hears about the watch cannot decide whether it is a counted
#   session — that silence IS the failure being fixed. Per the failure-direction
#   analysis in session-start-dream.sh: a too-loud reminder is bounded and
#   self-correcting, silence is mute, self-perpetuating, and lossy. Self-cleaning:
#   delete the section from OPERATIONS.md when the watch is discharged and this goes
#   quiet on its own.
#
#   IT DOES NOT REPORT A TALLY, AND THAT RESTRAINT IS THE POINT. The first live run
#   printed "2 of 3", which happened to equal the hand-recorded tally — and was made
#   of the wrong sessions: transcript mtimes newer than the boundary were
#   {session-305, session-306}, where session-305 is the session the reset explicitly
#   EXCLUDES, and the current session being subtracted cancelled the error out. A
#   number that is right by cancellation is the proxy-substitution defect this
#   codebase keeps finding, so the message says what was OBSERVED (transcript
#   activity, with its bias named) and sends the reader to the tally table, which is
#   the record.
#
#   Two reasons the observation cannot be the tally. (1) mtime is last-write, not
#   session-start, and the boundary is day-granular, so a session that ended just
#   after midnight on the boundary date is counted even when it belongs to the window
#   before. (2) A counted session is one ASSESSED against the watch's criteria — a
#   judgment no hook makes. Structural surfacing, advisory action, as in this file's
#   header.
check_watch() {
    local anchor="$1" window="$2" label="$3"
    local since raw n cand tdir

    # Section absent -> the watch is discharged and deleted -> silent. That is the
    # ONLY silent path, and it is checked separately from the date on purpose: if
    # "no section" and "section with no date" both returned quietly, deleting or
    # renaming the date line would disable the surfacing without a trace — which is
    # the exact failure this whole function exists to repair, one level up.
    if ! section_exists_in_operations "$OPS" "$anchor"; then
        debug "$anchor: no section in $OPS (watch discharged or not present), silent"
        return 0
    fi

    since=$(date_field_from_operations "$OPS" "$anchor" 'Counting since')
    if [ -z "$since" ]; then
        DUE_ITEMS+=("$label — OPEN WATCH with no machine-readable start date. Restore a 'Counting since: YYYY-MM-DD' line in OPERATIONS.md ${anchor}, or the session count cannot be observed at all.")
        return 0
    fi

    tdir=""
    if [ -n "${TRANSCRIPT_PATH:-}" ]; then
        cand=$(dirname "$TRANSCRIPT_PATH")
        [ -d "$cand" ] && tdir="$cand"
    fi
    if [ -z "$tdir" ]; then
        tdir="$HOME/.claude/projects/$(transcript_dir_slug "$PROJECT_DIR")"
    fi

    # `find -newermt` wants a timestamp; the OPERATIONS date is a day, so anchor at
    # its start. Sessions on the counting-start day itself are therefore counted.
    raw=$(sessions_since "$since 00:00:00" "$tdir")
    if [ "$raw" -lt 0 ]; then
        DUE_ITEMS+=("$label — open watch, session count UNASSESSABLE (no transcript dir at $tdir); confirm the tally in OPERATIONS.md")
        return 0
    fi

    n=$(( raw - 1 ))            # exclude the current in-progress session
    [ "$n" -lt 0 ] && n=0

    local obs="~${n} session(s) have written transcripts since ${since} (approximate: mtime-based, day-granular boundary — it can include a session from just before the reset)"
    if [ "$n" -ge "$window" ]; then
        DUE_ITEMS+=("$label — OPEN WATCH, window may be full: ${obs}, against a ${window}-session window. Read the tally table in OPERATIONS.md ${anchor}; if the third counted session is done, record the verdict now — discharge the watch or trigger it — and do not leave it open a second time.")
    else
        DUE_ITEMS+=("$label — OPEN WATCH: ${obs}, against a ${window}-session window. The tally table in OPERATIONS.md ${anchor} is the record, not this count. Note that this session may count; ASSESS IT AT CLOSE against the watch criteria and write the row then — at session start there is no behaviour to assess yet, and a row written now would be the unassessed-tally failure this watch exists to avoid.")
    fi
    return 0
}

check_cadence "C-078" "compliance review" 10 "C-078 Compliance Review → run /compliance-review"
check_cadence "C-155" "feedback loop"     20 "C-155 Feedback Loop Analysis → run analyze_feedback_loop"
check_cadence "C-109" "deferred.cadence"  30 "C-109 Deferred-cadence audit → review OPERATIONS.md C-109"
check_cadence "C-012" "security posture"  90 "C-012 Security Posture Review → run OPERATIONS.md C-012 (OWASP/ATLAS/NIST/CISA currency)"

check_watch "RW-313" 3 "RW-313 #313 migration rollback watch"

if [ "${#DUE_ITEMS[@]}" -eq 0 ]; then
    debug "nothing due, staying silent"
    exit 0
fi

MSG="Session cadence check (ai-governance) — DUE / OPEN:"
for item in "${DUE_ITEMS[@]}"; do
    MSG="$MSG"$'\n'"  • $item"
done
MSG="$MSG"$'\n'"(Surfaced automatically at session start; run when appropriate — these are periodic maintenance, not blocking.)"

python3 -c "import json, sys; sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$MSG" 2>/dev/null || true
exit 0
