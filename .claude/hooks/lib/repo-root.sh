#!/usr/bin/env bash
# Shared session-root resolution for SessionStart hooks (BACKLOG #214).
#
# WHY THIS EXISTS
# ---------------
# Every SessionStart hook used to open with its own copy of:
#
#     PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"        # <- WRONG FIRST CHOICE
#     [ -z "$PROJECT_DIR" ] && PROJECT_DIR=<payload cwd>
#     [ -z "$PROJECT_DIR" ] && PROJECT_DIR="$PWD"
#
# That order rests on a premise this project believed for months and which is
# FALSE: that `CLAUDE_PROJECT_DIR` names the primary checkout. The dream hook
# records the root it resolved on every firing, and that log shows FOUR
# different roots across 103 firings — three separate worktrees (80) and the
# primary (23). The variable is launch-mode dependent, not a constant. Any
# policy phrased as "use CLAUDE_PROJECT_DIR for project-wide facts" is
# therefore not a policy; it is a coin flip that reads as one.
#
# THE AXIS THAT ACTUALLY DISCRIMINATES
# ------------------------------------
# Not "project-scoped vs tree-scoped" (a judgment call), and not "committed vs
# uncommitted" (which fails: two committed branches disagree, so a due-date in
# a versioned file is still checkout-variant). The workable axis is:
#
#   CHECKOUT-VARIANT ...... differs between working copies OR between branches:
#                           uncommitted files, current branch, HEAD position,
#                           and the contents of ANY versioned file.
#                           -> read from the ACTING checkout (session_root).
#
#   REPOSITORY-INVARIANT .. identical from every worktree because it lives in
#                           the shared git dir: refs/heads, refs/stash, the
#                           worktree list, remotes, tags.
#                           -> any root works; prefer session_root for clarity.
#
# A fact that is meant to be one-per-repository but is stored in a versioned
# file (a cadence due-date) is checkout-variant, so it needs a NAMED CANONICAL
# AUTHORITY — see canonical_snapshot() below. "Whatever the primary checkout
# happens to contain" is not an authority; it is an unmaintained proxy for one
# (measured while writing this: 16 commits behind origin/main and 7 files dirty).
#
# Usage:
#   source "$HOOK_DIR/lib/repo-root.sh"
#   resolve_session_root "$INPUT"          # sets SESSION_ROOT + SESSION_ROOT_PROVENANCE
#   debug "root=$SESSION_ROOT via $SESSION_ROOT_PROVENANCE"
#
# NOTE the call shape: this sets GLOBALS, it does not echo. Calling it as
# `X=$(resolve_session_root ...)` runs it in a subshell, so the provenance
# assignment dies there and every caller reports "unknown" — which is exactly
# what the first draft of this file did, and the diagnostic the whole class of
# bugs most needs was silently useless.

# resolve_session_root <input_json>
#   Sets SESSION_ROOT to the acting checkout, and SESSION_ROOT_PROVENANCE to how it
#   was found, so a surprising reminder is diagnosable in one line instead of two
#   sessions (the 2026-07-12 incident cost exactly that).
#
#   Order: payload cwd -> $PWD -> CLAUDE_PROJECT_DIR. Each candidate is normalized
#   through `git rev-parse --show-toplevel` so a subdirectory resolves to its
#   worktree root; a non-git candidate is used as-is rather than discarded (hooks
#   also run in scaffold copies and plain folders).
#
#   CLAUDE_PROJECT_DIR is LAST on purpose. It is not "the project" — it is
#   whatever the harness happened to set, and the whole class of bugs this file
#   closes came from trusting it first. It stays in the chain only so a hook
#   invoked with no payload and no usable cwd still has something.
# Pre-declared so a `set -u` caller can reference them even if resolution is
# skipped or the function is unavailable.
SESSION_ROOT="${SESSION_ROOT:-}"
SESSION_ROOT_PROVENANCE="${SESSION_ROOT_PROVENANCE:-unknown}"
CANONICAL_SNAPSHOT_REF="${CANONICAL_SNAPSHOT_REF:-}"

resolve_session_root() {
    local input="${1:-}" cand root

    cand=$(printf '%s' "$input" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('cwd', '') or '')
except Exception:
    print('')
" 2>/dev/null || echo '')
    if [ -n "$cand" ] && [ -d "$cand" ]; then
        SESSION_ROOT_PROVENANCE="payload cwd"
        root=$(git -C "$cand" rev-parse --show-toplevel 2>/dev/null || echo '')
        [ -n "$root" ] || root="$cand"
        SESSION_ROOT="$root"
        return 0
    fi

    if [ -n "${PWD:-}" ] && [ -d "${PWD:-}" ]; then
        SESSION_ROOT_PROVENANCE="\$PWD (no payload cwd)"
        root=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || echo '')
        [ -n "$root" ] || root="$PWD"
        SESSION_ROOT="$root"
        return 0
    fi

    SESSION_ROOT_PROVENANCE="CLAUDE_PROJECT_DIR fallback (may be a DIFFERENT checkout)"
    SESSION_ROOT="${CLAUDE_PROJECT_DIR:-}"
    # Never return empty: genesis would then test a RELATIVE `.git` against the hook
    # process's cwd and could announce "new project" inside a real one.
    [ -n "$SESSION_ROOT" ] || { SESSION_ROOT="${PWD:-.}"; SESSION_ROOT_PROVENANCE="last-resort \$PWD (no cwd, no CLAUDE_PROJECT_DIR)"; }
}

# canonical_snapshot <root> <relpath> <dest_file>
#   Materialize the repository-canonical version of a versioned file, for facts
#   that are meant to be one-per-repository (cadence due dates) rather than
#   per-branch. Returns 0 and writes <dest_file> on success, 1 otherwise.
#
#   Authority order: local main -> origin/main -> (caller falls back to the
#   working tree). BOTH live in the shared git dir, so both read identically from
#   every worktree — that invariance is the property the old primary-checkout
#   shortcut was reaching for and failing to get.
#
#   LOCAL main is FIRST, and the order matters (code-reviewer HIGH, session-262).
#   This project asks before every push, so a completed cadence routinely sits
#   committed-but-unpushed. Reading `origin/main` first would then keep announcing
#   a review that is already done — every session, in every checkout, until someone
#   pushes. That is a worse false-fire than the one this whole change removes, and
#   it is the tune-out failure the hygiene hook's own header warns about. Local
#   `main` is invariant AND fresher-or-equal; `origin/main` remains as the fallback
#   for a checkout that has no local main.
#
#   NEVER fetches. A SessionStart hook has no business doing network I/O, so
#   this reads whatever the last fetch/push left behind; a slightly stale ref
#   still beats an arbitrary working tree, and the caller's working-tree
#   fallback covers a repo that has never fetched.
# has_memory_markers <root>  ->  0 if <root> is a project using the governance
# memory system, 1 otherwise. SSOT for "is this one of ours?".
#
# WHY THIS IS A FUNCTION AND NOT AN INLINE TEST IN EACH HOOK: it was inline in
# each hook, and the two copies disagreed. `journal-reminder.sh` learned about
# `_ai-context/` when memory moved there in v2.62.0; `session-start-dream.sh`
# did not, so dream stayed gated on root-level markers only. Any project that
# completed the v2.62.0 migration and has no root AGENTS.md got its dream
# cadence SILENTLY disabled — this repo masked the bug purely because a root
# `AGENTS.md` happens to still exist here.
#
# Two hand-kept lists that must agree is the same defect class as two hand-kept
# file copies (BACKLOG #226). Same fix: keep one, derive the rest.
#
# Order matters only for cost, not correctness: `_ai-context/` first because it
# is the current layout, so the common case exits on the first test.
has_memory_markers() {
    local root="${1:-}"
    [ -n "$root" ] || return 1
    [ -f "$root/_ai-context/SESSION-STATE.md" ] && return 0
    [ -f "$root/SESSION-STATE.md" ] && return 0        # pre-v2.62.0 layout
    [ -f "$root/AGENTS.md" ] && return 0               # loader present, memory elsewhere
    return 1
}

canonical_snapshot() {
    local root="${1:-}" rel="${2:-}" dest="${3:-}" ref
    [ -n "$root" ] && [ -n "$rel" ] && [ -n "$dest" ] || return 1
    for ref in main origin/main; do
        if git -C "$root" cat-file -e "$ref:$rel" 2>/dev/null; then
            if git -C "$root" show "$ref:$rel" >"$dest" 2>/dev/null && [ -s "$dest" ]; then
                CANONICAL_SNAPSHOT_REF="$ref"
                return 0
            fi
            # Empty or unreadable: fall through rather than handing the caller a
            # zero-byte file it would parse as "no dates found" and then report
            # three "no due date found" lines against a file that has them.
        fi
    done
    return 1
}

# transcript_dir_slug <path>
#   Claude Code's per-project transcript directory name. VERIFIED SCOPE: `/` and `.`
#   both map to `-`, checked against the two real directories on this machine. Other
#   non-alphanumerics are NOT characterized — do not widen the class blind; a wrong
#   slug fails safe (nonexistent dir -> `sessions_since` returns -1 -> silence).
#   Replacing BOTH `/` and `.` is why a worktree under `.claude/worktrees/`
#   lands on a doubled dash (`...-mcp--claude-worktrees-session-262`). The prior
#   slug replaced only `/`, so it could never name a worktree's directory — it
#   silently produced a path that does not exist, the caller read that as
#   "activity unassessable", and the hook went quiet for the wrong reason.
transcript_dir_slug() {
    printf '%s' "${1:-}" | sed 's#[/.]#-#g'
}
