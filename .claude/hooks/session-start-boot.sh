#!/usr/bin/env bash
# SessionStart hook — boot layer for session-start protocol.
#
# Injects SESSION-STATE.md resumption context and session-start protocol
# instructions so the model has continuity context from the first turn,
# replacing advisory prose that was previously loaded every turn via CLAUDE.md.
#
# Also detects worktree checkouts and reminds to call EnterWorktree.
#
# Env vars:
#   BOOT_SKIP=1       — disable entirely (audit-logged)
#   BOOT_DEBUG=true   — stderr debug logging
#
# Exit 0 always — a SessionStart hook must never block startup.
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

load_lib() {
    local lib="$HOOK_DIR/lib/$1"
    [ -f "$lib" ] || return 1
    "${BASH:-bash}" -n "$lib" 2>/dev/null || return 1
    # shellcheck source=/dev/null
    source "$lib" || return 1
}
for _lib in audit-bypass.sh repo-root.sh; do
    load_lib "$_lib" || exit 0
done

debug() { if [ "${BOOT_DEBUG:-false}" = "true" ]; then echo "[boot-hook] $1" >&2; fi; }

if [ "${BOOT_SKIP:-}" = "1" ]; then
    audit_bypass "session-start-boot" "BOOT_SKIP=1" "structural-bypass"
    debug "BOOT_SKIP=1, exiting"
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

resolve_session_root "$INPUT"
PROJECT_DIR="$SESSION_ROOT"
debug "session root=$PROJECT_DIR via ${SESSION_ROOT_PROVENANCE:-unknown}"

case "$SOURCE" in
    compact) debug "source=compact, skipping (mid-session)"; exit 0 ;;
esac

# --- Build the boot message ---
MSG=""

# 1. Resumption context from SESSION-STATE.md
SS=""
if [ -f "$PROJECT_DIR/_ai-context/SESSION-STATE.md" ]; then
    SS="$PROJECT_DIR/_ai-context/SESSION-STATE.md"
elif [ -f "$PROJECT_DIR/SESSION-STATE.md" ]; then
    SS="$PROJECT_DIR/SESSION-STATE.md"
fi

if [ -n "$SS" ]; then
    # SELECT THE ORIENTING SECTIONS BY NAME. Never by document order.
    #
    # Two failed designs preceded this one, both defeated the same way — by a
    # heading, somewhere, not being where the rule assumed.
    #   v1 "start at `## RESUMPTION`, stop at the next `## ` or a `---`" worked
    #      only while one stacked block held everything. When that stack was
    #      deleted (2026-08-15) and the snapshot split across Current Position /
    #      Immediate Context / Next Actions, it stopped at the first and a
    #      resuming session got the position with no next actions.
    #   v2 "start there, stop at a known reference heading" fixed THIS repo and
    #      broke every scaffolded project: `SCAFFOLD_SESSION_STATE` orders
    #      Quick Reference BEFORE Next Actions, so extraction stopped early
    #      again — 456 chars, measured — and `SCAFFOLD_SESSION_STATE_DOC` leads
    #      with `## Current Focus`, matching no start token at all, injecting
    #      nothing. A code review caught it; the fixture had copied this repo's
    #      section order instead of the shipped template, so the tests agreed
    #      with the bug.
    #
    # Root cause of both: a span rule makes the injection depend on what sits
    # BETWEEN two headings, so any project that orders its sections differently,
    # or renames one heading, silently gets the wrong text. Selecting each wanted
    # section on its own removes the dependence — order-free, and tolerant of the
    # vocabulary differing across the project types this ships to.
    #
    # The cap is the backstop, and it is deliberately not defeatable by editing
    # markdown: whatever the headings say, this can never inject more than
    # BOOT_MAX_CHARS. Unbounded injection was v2's other failure (17,891 chars
    # measured against a file with no reference heading).
    RESUMPTION=$(python3 -c "
import sys

# Matched case-insensitively against the heading text, by prefix, so
# 'Next Actions' also catches 'Next Actions (this week)'. Covers the code
# scaffold, the document scaffold ('Current Focus'/'Next Steps'), and the
# grandfathered single-block shape.
WANT = (
    'resumption', 'current position', 'current focus', 'immediate context',
    'active task', 'next action', 'next step', 'blocker', 'session notes',
)
MAX_CHARS = 8000

lines, keep = [], False
with open(sys.argv[1], encoding='utf-8', errors='replace') as f:
    for line in f:
        if line.startswith('## '):
            head = line[3:].strip().rstrip(':').lower()
            keep = head.startswith(WANT)
            if keep:
                lines.append(line.rstrip())
            continue
        if keep:
            lines.append(line.rstrip())

out = '\n'.join(lines).strip()
if len(out) > MAX_CHARS:
    out = out[:MAX_CHARS].rstrip() + '\n[truncated — read _ai-context/SESSION-STATE.md in full]'
if out:
    print(out)
" "$SS" 2>/dev/null || echo '')
    if [ -n "$RESUMPTION" ]; then
        MSG="SESSION RESUMPTION CONTEXT:"$'\n'"$RESUMPTION"$'\n\n'
        debug "resumption block extracted ($(echo "$RESUMPTION" | wc -l | tr -d ' ') lines)"
    fi
fi

# 2. Session-start protocol
MSG="${MSG}SESSION-START PROTOCOL: Read _ai-context/ memory files (SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md, OPERATIONS.md). SESSION-STATE is the CURRENT snapshot — route decisions to PROJECT-MEMORY, lessons to LEARNING-LOG, work to BACKLOG, cadences to OPERATIONS, and session narrative to git rather than accumulating any of it there."

# 3. Worktree detection
if [ -f "$PROJECT_DIR/.git" ]; then
    MSG="$MSG"$'\n\n'"WORKTREE DETECTED: Call EnterWorktree(path=\"$PROJECT_DIR\") to register for cleanup."
    debug "worktree detected"
fi

python3 -c "import json, sys; sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$MSG" 2>/dev/null || true

exit 0
