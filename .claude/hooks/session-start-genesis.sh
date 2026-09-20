#!/usr/bin/env bash
# SessionStart hook — new-project genesis detector + founding-question nudge.
#
# At session start, if the directory looks like a real project (.git or source/
# doc files) but has NO governance memory files (SESSION-STATE.md), inject ONE
# advisory nudge that INLINES the minimal founding questions (Goal / Done /
# Non-goals / App-vs-document, per CFR §1.3.5 founding floor) so the model asks
# them before implementing. Silent once the project is onboarded (self-clearing).
#
# Why inline the questions (not just point at /start-project): the skill fleet is
# `disable-model-invocation: true` (CFR §9.5.3) — the model cannot auto-invoke a
# skill, so a bare "run /start-project" nudge is a dead pointer. Inlining lets the
# model act on the prose directly; /start-project is offered as the optional
# fuller guided setup. Complements the MCP server's "Project Initialization
# Detection" instruction for sessions where the server is NOT connected (cold
# projects — the gap nothing else covers).
#
# Scope: STRUCTURAL surfacing (deterministic at session start) + ADVISORY action
# (the model decides). Never blocks.
#
# Env vars:
#   START_PROJECT_NUDGE_SKIP=1      — disable entirely (audit-logged)
#   START_PROJECT_NUDGE_DISMISS=1   — suppress for this session (same as the marker)
#   START_PROJECT_NUDGE_DEBUG=true  — stderr debug logging
# Per-project opt-out marker: .start-project-dismissed
#
# Exit 0 always — a SessionStart hook must never block startup.
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

# LIBRARY LOADING — one mechanism for every lib (BACKLOG #236). See the fuller
# rationale in session-start-dream.sh; the short version is that guarding only
# `repo-root.sh` while sourcing `audit-bypass.sh` and `genesis.sh` bare above it
# meant a missing lib exited 1 under `set -euo pipefail` before the guard ran,
# breaking this hook's own "Exit 0 always" contract. `lib/` is now one symlink
# into the checkout, so a moved repo removes every lib at once.
#
# This hook's guard was also weaker than the dream hook's — presence only, no
# `bash -n` — so a truncated lib passed it and then failed at source time. Both
# now use the same validated loader.
load_lib() {
    local lib="$HOOK_DIR/lib/$1"
    [ -f "$lib" ] || return 1
    "${BASH:-bash}" -n "$lib" 2>/dev/null || return 1
    # shellcheck source=/dev/null
    source "$lib" || return 1
}
for _lib in audit-bypass.sh genesis.sh repo-root.sh; do
    load_lib "$_lib" || exit 0
done

debug() { if [ "${START_PROJECT_NUDGE_DEBUG:-false}" = "true" ]; then echo "[genesis-hook] $1" >&2; fi; }

if [ "${START_PROJECT_NUDGE_SKIP:-}" = "1" ]; then
    audit_bypass "session-start-genesis" "START_PROJECT_NUDGE_SKIP=1" "structural-bypass"
    debug "START_PROJECT_NUDGE_SKIP=1, exiting"
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

# Shared resolver (BACKLOG #214) — payload cwd first, CLAUDE_PROJECT_DIR last.
# Genesis reads only presence-of-file facts, whose divergence set is empty in a
# normal repo, so it gets the resolver for consistency and nothing more.
resolve_session_root "$INPUT"
PROJECT_DIR="$SESSION_ROOT"
debug "session root=$PROJECT_DIR via ${SESSION_ROOT_PROVENANCE:-unknown}"

# Fire on startup/resume/clear; skip compact (mid-session, not a boundary).
case "$SOURCE" in
    compact) debug "source=compact, skipping (mid-session)"; exit 0 ;;
esac

# Gate: real project AND no governance memory AND not dismissed.
if [ "$(is_project_dir "$PROJECT_DIR")" != "yes" ]; then
    debug "not a project dir, exiting"; exit 0
fi
if [ "$(memory_files_present "$PROJECT_DIR")" = "yes" ]; then
    debug "memory files present (onboarded), exiting"; exit 0
fi
if [ "$(is_dismissed "$PROJECT_DIR")" = "yes" ]; then
    debug "dismissed, exiting"; exit 0
fi

PTYPE="$(detect_project_type "$PROJECT_DIR")"
# Layout detector (v2.62.0 unified layout): name the decisive branch so a
# misclassification is diagnosable from the debug log.
if [ -f "$PROJECT_DIR/AGENTS.md" ] || [ -f "$PROJECT_DIR/CLAUDE.md" ]; then
    debug "type=$PTYPE (root loader present)"
elif [ "$(has_code_signal "$PROJECT_DIR")" = "yes" ]; then
    debug "type=$PTYPE (code signal: manifest/sources/src|tests)"
elif [ -d "$PROJECT_DIR/_ai-context" ]; then
    debug "type=$PTYPE (_ai-context/ present, no code signal)"
else
    debug "type=$PTYPE (default)"
fi

MSG="NEW PROJECT DETECTED — no governance memory files here yet. Before implementing, calibrate and ask the user the minimal founding questions (CFR §1.3.5 founding floor); do NOT skip these even if the request seems clear:
  1. Goal — what problem does this solve, and for whom?
  2. Done-looks-like — what is the success signal; when do we stop?
  3. Non-goals — what should this deliberately NOT do?
  4. App or document — is this a code project or a document project?
Then scale depth to the answers (EXPEDITED: brief inline; ENHANCED/novel: full Socratic discovery per §1.3.5). Detected type: ${PTYPE}. For the full guided setup (calibrate -> scaffold_project -> design doc), the user can run /start-project. This nudge fires only until governance memory exists and complements the MCP server's init-detection for sessions where the server is not connected. (Suppress: create .start-project-dismissed or set START_PROJECT_NUDGE_SKIP=1.)"

python3 -c "import json, sys; sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$MSG" 2>/dev/null || true
exit 0
