#!/usr/bin/env bash
# PreToolUse hook — Memory file size guard
# Reports memory files that exceed their spec targets when a git commit is run.
# Only the LEARNING-LOG arm blocks; BACKLOG count and SESSION-STATE size are
# ADVISORY and never block — see the rationale at each check.
#
# Prevents the re-accumulation that consumed two full sessions of manual
# cleanup (2,665→1,284→386 lines). The structural root-cause fix for
# unbounded memory file growth.
#
# Thresholds (from title-10 CFR §7.0.4 + §7.3 targets, adjusted for
# the graduated-patterns table which grows monotonically):
#   LEARNING-LOG active entries: 500 lines (≈125 entries at ≤5 lines each)
#   BACKLOG items: 60 discrete items  (ADVISORY — reported, never blocking)
#   SESSION-STATE: 300 lines (per §7.0.4)  (ADVISORY — reported, never blocking)
#
# Bypass: MEMORY_SIZE_SKIP=1 (audit-logged).
#
# TWO EMISSION MODES, ONE MEASUREMENT (--direct, added 2026-08-24).
# The measurement below is host-agnostic; only the way a refusal is COMMUNICATED
# is host-specific. Claude Code invokes this as a PreToolUse hook: it reads the
# tool call from stdin as JSON, keys on the command containing `git commit`, and
# always exits 0 because a refusal travels as {"decision":"block"} on stdout.
# That protocol is invisible to any other host, so a Codex session committing
# in-session bypassed the guard entirely — and BACKLOG #348's `--add-dir` work
# exists specifically to let Codex commit in-session, which would have opened an
# ungated commit path into the memory files.
#
# `--direct` runs the same checks with no stdin and no command detection, prints
# plain text, and EXITS NON-ZERO on the blocking arm. That is what pre-commit
# understands, and pre-commit is a seam every host honours. Deliberately not a
# second copy of the thresholds: duplicated safety logic drifts, which is the
# defect class this repo fixed in repo_hygiene/cleanup.sh the same week.

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
WARNINGS=""   # blocking arm
NOTICES=""    # advisory arm — reported, commit proceeds

# --- LEARNING-LOG: count lines in active section only ---
LL="$CTX/LEARNING-LOG.md"
if [ -f "$LL" ]; then
    GRAD_LINE=$(grep -n -m1 '^## Graduated' "$LL" | cut -d: -f1)
    if [ -n "$GRAD_LINE" ]; then
        ACTIVE_LINES=$((GRAD_LINE - 1))
    else
        ACTIVE_LINES=$(wc -l < "$LL")
    fi
    LL_LIMIT=500
    if [ "$ACTIVE_LINES" -gt "$LL_LIMIT" ]; then
        WARNINGS="${WARNINGS}LEARNING-LOG active section: ${ACTIVE_LINES} lines (limit: ${LL_LIMIT}). Condense entries to ≤5 lines or graduate patterns.\n"
    fi
fi

# --- BACKLOG: count discrete items — ADVISORY, never blocking ---
#
# WHY THIS ONE DOES NOT BLOCK (changed 2026-08-13, session-305, by user decision).
# A blocking count pressures the agent to make the NUMBER go down, and the cheapest
# way to do that is to merge items that should stay separate. That happened: this
# guard blocked a commit at 61/60 and the merge it produced had to be reverted the
# same day. A backlog is a queue of real work — its length is information for the
# human, not a condition the agent should be resolving on its own initiative.
#
# So: report it and let the human decide. The count is also a PROXY — it counts
# `^#### ` headings, so a sub-heading inside an entry reads as an item, which is
# another reason not to gate on it.
#
# SESSION-STATE joined this advisory arm on 2026-08-15 (user decision) for the same
# reason, and the paragraph that used to sit here — claiming the size limits block
# because they "are fixed by condensing prose (no information lost)" — was the thing
# that needed correcting, not just the severity. Pruning SESSION-STATE is NOT lossless
# condensation. It is deciding, line by line, whether content is stale, obsolete, or
# still live — the same judgment the backlog arm was demoted for, applied to a file
# where the cheapest way to satisfy a block is to delete information a future session
# needed. Blocking there does not buy a smaller file; it buys a faster deletion.
# So: report it, name the number, and let the human decide whether to prune or route.
# Reviewed under BACKLOG #343 question 3, which asked this exact question.
#
# LEARNING-LOG still blocks, and that remaining asymmetry is now the narrow one: its
# active section has a defined non-destructive outlet (graduate an entry to the
# Graduated Patterns table, which stays in the file), so the cheap fix and the correct
# fix coincide. That is a weaker argument than it looks — graduating is also a
# judgment — and #343 owns the question of whether it should be demoted too. It is
# left blocking rather than swept along, because nobody asked for that and no
# instance of it firing wrongly has been observed.
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
    # Plain-text emission for pre-commit. Same arms, same thresholds, same
    # asymmetry: LEARNING-LOG blocks, the others report.
    [ -n "$NOTICES" ] && printf 'Memory size guard (advisory):\n%b' "$NOTICES"
    if [ -n "$WARNINGS" ]; then
        printf 'Memory file size guard — files exceed spec targets:\n%b' "$WARNINGS"
        printf 'Bypass: MEMORY_SIZE_SKIP=1 (condense first if possible).\n'
        exit 1
    fi
    exit 0
fi

if [ -n "$WARNINGS" ]; then
    # A blocking warning wins: emit it, and fold the advisory notices in so a single
    # message carries everything rather than a notice being lost behind a block.
    REASON="Memory file size guard — files exceed spec targets:\\n${WARNINGS}"
    [ -n "$NOTICES" ] && REASON="${REASON}${NOTICES}"
    # NOTE the shape: top-level {"decision":"block"}, where five sibling hooks use
    # hookSpecificOutput.permissionDecision="deny". A review flagged this as an
    # unverifiable dependency on a possibly-deprecated field. VERIFIED WORKING
    # 2026-08-14: this exact emission blocked a real `git commit` in session-305
    # (backlog at 61/60) — observed, not inferred. Left as-is rather than churned
    # during a close-out; if it ever stops blocking, the five siblings are the
    # pattern to copy.
    echo "{\"decision\": \"block\", \"reason\": \"${REASON}Bypass: MEMORY_SIZE_SKIP=1 (condense first if possible).\"}"
    exit 0
fi

if [ -n "$NOTICES" ]; then
    # Advisory only — the commit proceeds. Surfaced as context so the agent reports it
    # to the human instead of acting on it.
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"${NOTICES}\"}}"
    exit 0
fi

exit 0
