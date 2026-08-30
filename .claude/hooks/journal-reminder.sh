#!/usr/bin/env bash
# UserPromptSubmit hook — journal reminder for memory maintenance (Layer 2, title-10 §7.11.3)
# Injects a JOURNAL directive when no memory file updates are detected recently.
# Silent (no output) when memory was recently written or project doesn't use memory files.
#
# REPO-CANONICAL: this file lives at .claude/hooks/journal-reminder.sh. The
# installs under ~/.claude/hooks and ~/.codex/hooks are SYMLINKS to it — edit
# here and the change is live everywhere, with nothing to copy or keep in sync
# (BACKLOG #226; the same call made for global-skills in #163). Registration
# stays GLOBAL-ONLY in ~/.claude/settings.json (UserPromptSubmit); do NOT also
# register it in a project's .claude/settings.json — that would double-fire.
#
# INSTALL DEPENDENCY: this hook sources lib/repo-root.sh, and lib/ must be linked
# too. `dirname $0` resolves to the SYMLINK's directory, so a linked hook beside a
# COPIED lib/ silently sources the stale lib — verified empirically 2026-07-25.
# Guarded by scripts/check-installed-hooks.sh. See the guarded source below for
# what happens if an install lands without a usable lib.
#
# Environment variables:
#   JOURNAL_SKIP=true           — Disable journaling entirely
#   JOURNAL_MIN_LINES=250       — Minimum transcript lines before triggering
#   JOURNAL_RECENCY=400         — Recency window for memory write detection
#   JOURNAL_FIRE_LOG=<path>     — Fire log (default ~/.claude/journal-reminder-fires.log;
#                                 one line per injection; capped ~100KB, tail-kept.
#                                 The fired-vs-ran compliance sub-check reads this.)
#   JOURNAL_DEBUG=true          — Enable stderr debug logging
#
# Exit 0 always — advisory only, never blocks

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

debug() {
  if [ "${JOURNAL_DEBUG:-false}" = "true" ]; then
    echo "[journal-hook] $1" >&2
  fi
}

if [ "${JOURNAL_SKIP:-false}" = "true" ]; then
  debug "JOURNAL_SKIP=true, exiting"
  exit 0
fi

INPUT=$(cat 2>/dev/null || echo '{}')

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

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -r "$TRANSCRIPT_PATH" ]; then
  debug "No readable transcript, exiting"
  exit 0
fi

MIN_LINES="${JOURNAL_MIN_LINES:-250}"
RECENCY="${JOURNAL_RECENCY:-400}"

LINE_COUNT=$(wc -l < "$TRANSCRIPT_PATH" 2>/dev/null | tr -d ' ') || LINE_COUNT=0

if [ "$LINE_COUNT" -lt "$MIN_LINES" ]; then
  debug "Transcript too short ($LINE_COUNT < $MIN_LINES), exiting"
  exit 0
fi

# --- Session root (BACKLOG #214 shared resolver) ----------------------------
# This hook was the LAST one still gating on raw $PWD, and the price was SILENCE:
# an identical violating transcript fired from the repo root and said nothing from
# `src/` or `tests/`, because a UserPromptSubmit hook inherits the session's cwd —
# wherever the human happened to `cd`. Silence is this hook's worst failure
# direction; the memory maintenance it guards only happens when it speaks.
#
# Placed HERE, below the cheap gates, on purpose: this hook runs on EVERY user
# prompt, and in a live session the transcript is always readable, so a resolver
# at the top of the file would charge every prompt a python3 + a git fork against
# a 5s hook timeout. Below the line-count gate, only candidate prompts pay.
#
# The lib is VALIDATED before sourcing, not just existence-tested. `cp` is not
# atomic, so the failure a mirror can actually produce is a TRUNCATED lib — and
# under `set -e` a parse error in a sourced file kills the parent outright: exit 2,
# no output, and `|| true` does NOT catch it (measured). For UserPromptSubmit, an
# exit 2 BLOCKS the user's prompt. A corrupt mirror must degrade, not eat prompts.
#
# Degradation is to the OLD raw-$PWD behaviour rather than `exit 0` (what the
# dream hook does): if a mirror lands without a usable lib, "fires only from the
# repo root" is strictly better than "never fires at all".
if [ -f "$HOOK_DIR/lib/repo-root.sh" ] && "${BASH:-bash}" -n "$HOOK_DIR/lib/repo-root.sh" 2>/dev/null; then
  # shellcheck source=lib/repo-root.sh
  source "$HOOK_DIR/lib/repo-root.sh"
fi

# Same guarded-degrade contract as resolve_session_root below: if the lib did not
# load, define the marker test locally rather than calling an undefined function.
# `if ! undefined_fn` would evaluate to TRUE (127 negated), i.e. "no markers" —
# which exits 0 and disables the hook silently. Silence is this hook's worst
# failure direction, so the fallback must fail toward FIRING, not toward quiet.
if ! declare -F has_memory_markers >/dev/null 2>&1; then
  has_memory_markers() {
    local root="${1:-}"
    [ -n "$root" ] || return 1
    [ -f "$root/_ai-context/SESSION-STATE.md" ] && return 0
    [ -f "$root/SESSION-STATE.md" ] && return 0
    [ -f "$root/AGENTS.md" ] && return 0
    return 1
  }
fi

if declare -F resolve_session_root >/dev/null 2>&1; then
  # payload cwd -> $PWD -> CLAUDE_PROJECT_DIR, each normalized through
  # `git rev-parse --show-toplevel`, so a session sitting in a subdirectory still
  # finds the markers at the top of its tree.
  resolve_session_root "$INPUT"
else
  SESSION_ROOT="$PWD"
  SESSION_ROOT_PROVENANCE="raw \$PWD (lib/repo-root.sh unusable — root-only firing)"
fi
debug "session root=$SESSION_ROOT via ${SESSION_ROOT_PROVENANCE:-unknown}"

# Only fire for projects that use the governance memory system.
# Marker list lives in lib/repo-root.sh (has_memory_markers). It was inline here
# and inline again in session-start-dream.sh, and the two had already diverged —
# this copy knew about the v2.62.0 `_ai-context/` layout and dream's did not.
if ! has_memory_markers "$SESSION_ROOT"; then
  debug "No SESSION-STATE.md (root or _ai-context/) or AGENTS.md in $SESSION_ROOT, exiting"
  exit 0
fi

# Inline Python: check if any memory file was written recently
MEMORY_WRITTEN=$(python3 -c "
import json, sys
from collections import deque

transcript_path = sys.argv[1]
window_size = int(sys.argv[2])

memory_files = {
    'SESSION-STATE.md', 'PROJECT-MEMORY.md', 'LEARNING-LOG.md',
    'BACKLOG.md', 'OPERATIONS.md', 'ARCHITECTURE.md'
}

try:
    with open(transcript_path, 'r', errors='replace') as f:
        lines = deque(f, maxlen=window_size)

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '\"Edit\"' not in line and '\"Write\"' not in line:
            continue
        try:
            entry = json.loads(line)
            content = entry.get('message', {}).get('content', [])
            if isinstance(content, str):
                continue
            for block in content:
                if block.get('type') != 'tool_use':
                    continue
                name = block.get('name', '')
                if name not in ('Edit', 'Write'):
                    continue
                inp = block.get('input', {})
                file_path = inp.get('file_path', '') or inp.get('path', '')
                for mf in memory_files:
                    if file_path.endswith(mf):
                        print('true')
                        sys.exit(0)
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            continue

    print('false')
except Exception:
    print('false')
" "$TRANSCRIPT_PATH" "$RECENCY" 2>/dev/null) || MEMORY_WRITTEN="false"

if [ "$MEMORY_WRITTEN" = "true" ]; then
  debug "Recent memory write found, exiting"
  exit 0
fi

# ── Concurrency check ──────────────────────────────────────────────────
# If a dream pass is running (worktree whose BRANCH NAME contains "dream"),
# suppress the journal reminder. Dream mines all recent sessions more
# thoroughly than journal mines the current one — running both wastes
# tokens and risks conflicting memory-file edits. Match on the
# bracket-enclosed branch field only, not the full line — the filesystem
# path may contain "dream" for unrelated reasons.
# Degrades silently: if `git worktree list` fails, skip the check.
DREAM_WT=$(git -C "$SESSION_ROOT" worktree list 2>/dev/null \
    | grep -vE '\[(main|master)\]' \
    | grep -iE '\[.*dream.*\]' \
    | sed -n '1p' || true)
if [ -n "$DREAM_WT" ]; then
  debug "Dream worktree detected ($(echo "$DREAM_WT" | awk '{print $1}')), suppressing journal — dream subsumes"
  exit 0
fi

debug "No recent memory writes — injecting journal reminder"

# Fire log (the FIRE half of the fired-vs-ran instrument; compliance-review
# compares these lines against subsequent memory-file writes). Must never
# block the injection — best-effort, capped ~100KB by tail-keep.
# Logs $SESSION_ROOT, not $PWD: the instrument counts fires PER PROJECT, and a
# raw cwd would split one repo across as many identities as the session visited
# subdirectories.
FIRE_LOG="${JOURNAL_FIRE_LOG:-$HOME/.claude/journal-reminder-fires.log}"
{
  printf '%s %s fired\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SESSION_ROOT" >> "$FIRE_LOG"
  if [ "$(wc -c < "$FIRE_LOG" | tr -d ' ')" -gt 102400 ]; then
    tail -n 500 "$FIRE_LOG" > "${FIRE_LOG}.tmp" && mv "${FIRE_LOG}.tmp" "$FIRE_LOG"
  fi
} 2>/dev/null || true

python3 -c "
import json, sys
transcript_path = sys.argv[1]
msg = (
    'JOURNAL: No memory file updates detected in the last '
    + sys.argv[2]
    + ' transcript lines. Spawn a background Agent (model: sonnet, '
    + 'run_in_background: true) to analyze the transcript for unpersisted '
    + 'decisions, constraints, or lessons. The agent should: (1) Read the '
    + 'transcript at ' + transcript_path + ' focusing on the last ~500 lines, '
    + '(2) Read the current memory files (SESSION-STATE.md, PROJECT-MEMORY.md, '
    + 'LEARNING-LOG.md, BACKLOG.md, OPERATIONS.md, ARCHITECTURE.md), '
    + '(3) Return structured proposals categorized by target file — decisions '
    + 'to PROJECT-MEMORY.md, lessons to LEARNING-LOG.md, position/state to '
    + 'SESSION-STATE.md, deferred work to BACKLOG.md, operational commitments '
    + 'to OPERATIONS.md, and reusable non-obvious patterns to the Reference '
    + 'Library via capture_reference (high bar: non-obvious + reusable, per '
    + 'curation governance) — the subagent must NOT write to files or call '
    + 'capture_reference directly. Apply the memory-file proposals you agree '
    + 'with; Reference Library captures require the user\'s approval before '
    + 'calling capture_reference (if the ai-governance MCP is unavailable in '
    + 'this project, surface those proposals as notes instead).'
)
sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': msg}}))
" "$TRANSCRIPT_PATH" "$RECENCY" || true
