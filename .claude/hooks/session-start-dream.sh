#!/usr/bin/env bash
# SessionStart hook (USER-LEVEL / global) — dream cadence surfacer (ACTIVITY-BASED).
#
# REPO-CANONICAL: .claude/hooks/session-start-dream.sh (CI-tested). The user-level
# installs under ~/.claude/hooks and ~/.codex/hooks are SYMLINKS to it, so there is
# no second copy and nothing to mirror — edit here and it is live everywhere
# (BACKLOG #226). Guarded by scripts/check-installed-hooks.sh. Registration stays
# GLOBAL-ONLY (~/.claude/settings.json); do NOT also register in a repo
# .claude/settings.json (that would double-fire in this repo).
#
# Fires in ANY project using the governance memory system (SESSION-STATE.md or
# AGENTS.md present). At session start it counts how many SESSIONS have accumulated
# since the last /dream pass and, if >= the threshold, injects an AUTO-RUN directive
# to execute the dream pass now (analysis in background; proposals + commit stay
# user-approved). DREAM_AUTORUN=0 reverts to the advisory nudge. Silent otherwise.
# The trigger is STRUCTURAL (deterministic count); execution remains an ADVISORY
# directive the session model carries out — its compliance is measured via the fire
# log below against subsequent "/dream pass" commits (fired-vs-ran instrument,
# compliance-review sub-check). Cold-start (no prior pass) stays a nudge.
#
# ACTIVITY-ONLY: there is NO calendar trigger. The nudge fires on accumulated work
# (unmined sessions), not elapsed time — a low-activity project simply won't nudge
# until enough new sessions accumulate. This is a deliberate global change (it removes
# the former 14-day floor from every project this hook runs in).
#
# "Sessions" = flat top-level *.jsonl transcripts in THIS project's transcript dir
# (the single dir /dream itself mines — the one whose stored cwd == this project),
# newer than the last /dream pass commit, minus the current in-progress session. The
# boundary is read live from git (the /dream skill commits memory with a "/dream pass"
# message); the grep is HARDENED so a feature/doc commit that merely mentions /dream
# cannot reset it. STATELESS — no stamp file (avoids the C-109 calcification risk).
#
# Why SessionStart (not SessionEnd): SessionEnd runs async after termination with no
# agent left to run a skill. See ai-governance CFR §7.11 / EXECUTION-FRAMEWORK §7.2.
#
# Env vars:
#   DREAM_CADENCE_SKIP=1       — disable entirely (audit-logged)
#   DREAM_CADENCE_SESSIONS=4   — fire threshold (unmined sessions since the last pass;
#                                default ALIGNED to the /dream per-pass last-4 mining cap
#                                so a threshold fire doesn't systematically skip sessions)
#   DREAM_AUTORUN=0            — threshold fire becomes an advisory nudge (default: auto-run directive)
#   DREAM_FIRE_LOG=<path>      — fire log (default ~/.claude/dream-directive-fires.log;
#                                one line per threshold fire with mode=directive|nudge;
#                                capped ~100KB, tail-kept; the fired-vs-ran compliance
#                                sub-check reads this against /dream pass commits)
#   DREAM_CADENCE_DEBUG=true   — stderr debug logging
#
# Exit 0 always — never blocks startup.
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

# LIBRARY LOADING — one mechanism for every lib (BACKLOG #236).
#
# `repo-root.sh` used to be the only guarded load, while `audit-bypass.sh` and
# `cadence.sh` were sourced bare directly above it. Under `set -euo pipefail` a
# missing file there exits 1 BEFORE the careful guard runs, so the hook broke its
# own "Exit 0 always" contract and the guard's own failure path was unreachable
# in the case that actually matters. Measured: exit 1 from a lib-less copy.
#
# `lib/` is now a single symlink into the checkout, so a moved or renamed repo
# removes ALL of them at once, for every project this hook runs in. That makes
# the all-libs-missing case ordinary rather than exotic — the accepted cost of
# BACKLOG #226, which is why the guard has to cover the class, not one member.
#
# `bash -n` before sourcing, not mere presence: a TRUNCATED lib parses partially
# and defines the functions before the cut point but not after.
# `resolve_session_root` sits at the top of repo-root.sh and `has_memory_markers`
# well below it, so a mid-file truncation yields a hook that resolves its root
# correctly and then treats every project as unmanaged — silent, and
# indistinguishable from "nothing due".
#
# Degrades to silence, which is this surfacer's designed failure direction: a
# missed nudge costs a later reminder, a broken session start costs the session.
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

debug() { if [ "${DREAM_CADENCE_DEBUG:-false}" = "true" ]; then echo "[dream-cadence] $1" >&2; fi; }

if [ "${DREAM_CADENCE_SKIP:-}" = "1" ]; then
    audit_bypass "session-start-dream" "DREAM_CADENCE_SKIP=1" "structural-bypass"
    debug "DREAM_CADENCE_SKIP=1, exiting"
    exit 0
fi

INPUT=$(cat 2>/dev/null || echo '{}')

read_field() {  # read_field <key> — extract a top-level string field from the JSON input.
    # NOTE: $1 is always a hardcoded literal key (source/transcript_path/cwd), never
    # untrusted input, so interpolating it into the program text is injection-safe;
    # field VALUES are read from stdin JSON, not the program text.
    printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('$1', ''))
except Exception:
    print('')
" 2>/dev/null || echo ''
}

SOURCE=$(read_field source)
TRANSCRIPT_PATH=$(read_field transcript_path)

# Shared resolver (BACKLOG #214) — payload cwd first, CLAUDE_PROJECT_DIR last.
# This hook is the reason the whole premise collapsed: its own fire log records
# the root it resolved, and across 103 firings that was three different
# worktrees (80) and the primary (23). `CLAUDE_PROJECT_DIR` is launch-mode
# dependent, so ordering it first made the boundary read a checkout chosen by
# accident.
resolve_session_root "$INPUT"
PROJECT_DIR="$SESSION_ROOT"
debug "session root=$PROJECT_DIR via ${SESSION_ROOT_PROVENANCE:-unknown}"

# Fire on startup/resume/clear; skip compact (mid-session).
case "$SOURCE" in
    compact) debug "source=compact, skipping (mid-session)"; exit 0 ;;
esac

# Portability guard: only projects using the governance memory system.
# Marker list lives in lib/repo-root.sh (has_memory_markers) — this test used to
# be inline and had drifted from journal-reminder.sh's copy, missing the
# `_ai-context/` layout that v2.62.0 moved memory into.
if ! has_memory_markers "$PROJECT_DIR"; then
    debug "no memory files at $PROJECT_DIR, exiting"
    exit 0
fi

SESSIONS_THRESHOLD="${DREAM_CADENCE_SESSIONS:-4}"
# Boundary = the committer timestamp of the last genuine /dream pass, rendered in LOCAL
# time without a TZ offset so `find -newermt` accepts it on BSD (macOS) and GNU (CI).
# TWO CHANNELS, trailer first.
#
# CHANNEL 1 (authoritative) — a `Dream-Pass:` git TRAILER on the pass's own commit.
# A trailer is a structured field, so prose that merely DESCRIBES the convention (this
# comment, a LEARNING-LOG commit about dream passes, a hook fix) can never be mistaken
# for performing it. That self-reference class has now bitten this hook three times:
# session-224 tightened the TOKEN (dream -> /dream pass), b4aea69 tightened the SCOPE
# (whole message -> subject only), and session-262 still missed two genuine passes
# because the emitter dropped the slash. LEARNING-LOG 2026-06-21 ("A Self-Reference
# Guard Must Match Where Genuine Instances Live") already named a structured trailer as
# a valid scope; the two cheaper options have now each failed once, so take it.
# Emitted by /dream Phase 5 — see global-skills/dream/procedure.md.
#
# CHANNEL 2 (fallback) — the historical SUBJECT token, for every pass committed before
# the trailer convention and for anyone committing by hand. Two deliberate looseners
# versus the pre-session-262 pattern: the leading slash is OPTIONAL (the skill really
# does emit "docs(memory): dream pass sessions 258-260" and "docs(memory): session-261
# dream pass" under context pressure — both 2026-07-24, both genuine, both missed), and
# it stays PREFIX-AGNOSTIC because real passes have also shipped as "chore: apply /dream
# findings" (6effe05) and "docs(session-state): ... /dream pass summary" (931d1cb).
# Subject-only still holds: print "<ts>\t<subject>" and grep the line — the timestamp
# column has no letters, so a match can only land in the subject. That is what keeps a
# token-in-BODY commit (the one that introduced the convention while explaining it) from
# self-resetting the boundary. `sed -n 1p` reads the whole stream (no early close) to
# avoid a head/awk SIGPIPE under `pipefail`; the trailing `|| echo ''` maps a git-error /
# no-match (grep exit 1 under pipefail) to the empty "no prior pass" path.
#
# FAILURE DIRECTION (the ordering that should govern the next edit here). The two
# mistakes are NOT symmetric, and the pre-session-262 comment had them backwards by
# calling silence "cheap for a cosmetic nudge":
#   * Matcher too STRICT -> missed boundary -> OVER-FIRE. Loud, bounded (one background
#     batch under the last-4 mining cap), and self-correcting — the directive itself
#     tells the session to re-check for a newer pass, and Phase 5 forbids a boundary
#     commit when nothing was accepted. Since the session-241 AUTO-RUN upgrade this
#     costs real subagent tokens, so it is no longer free — but it is still bounded.
#   * Matcher too LOOSE -> false boundary -> SILENCE. Mute (a hook that does not fire
#     leaves no artifact), self-perpetuating (no fire -> no pass -> no new boundary),
#     and LOSSY — sessions accumulated during the silence are permanently discarded by
#     the last-3 cap. This is the documented 2026-06-21 incident: ~18 unmined sessions,
#     and it predates AUTO-RUN, so silence was already the worse direction back then.
# Hence: prefer generosity in the prose channel, and put PRECISION in the trailer.
PATTERN="/?dream pass|apply /dream findings"

# Channel 1. `%(trailers:key=...)` needs git >= 2.22; older git emits the placeholder
# LITERALLY, which would otherwise read as a boundary on EVERY commit — the `%\(trailers`
# reject makes that degrade to the prose channel instead of minting a false boundary.
# awk (not head) + `sed -n 1p` read the whole stream; an early close SIGPIPEs git under
# `pipefail`.
LAST_TS=$(git -C "$PROJECT_DIR" log --since="400 days ago" \
    --date=format-local:'%Y-%m-%d %H:%M:%S' \
    --format="%cd%x09%(trailers:key=Dream-Pass,valueonly,separator=%x20)" 2>/dev/null \
    | awk -F'\t' 'NF > 1 && $2 != "" && $2 !~ /%\(trailers/' | cut -f1 | sed -n '1p' || echo '')

if [ -n "$LAST_TS" ]; then
    # Trailer channel is live -> it is AUTHORITATIVE. A later pass that forgets the
    # trailer does not move the boundary, so the cadence over-fires until a trailered
    # pass lands: the loud, bounded direction by the ordering above, and the price of
    # making a prose false-boundary structurally impossible once the convention is in use.
    debug "boundary from Dream-Pass trailer: $LAST_TS"
else
    LAST_TS=$(git -C "$PROJECT_DIR" log --since="400 days ago" \
        --date=format-local:'%Y-%m-%d %H:%M:%S' --format='%cd%x09%s' 2>/dev/null \
        | grep -iE "$PATTERN" | cut -f1 | sed -n '1p' || echo '')
    [ -n "$LAST_TS" ] && debug "boundary from subject prose: $LAST_TS"
fi

if [ -z "$LAST_TS" ]; then
    MSG="Dream cadence: no prior /dream pass detected in this project. Consider running /dream to mine recent sessions for unpersisted decisions, lessons, or references."
else
    # Resolve THIS project's transcript dir — the single dir /dream mines (the one
    # whose stored cwd == this project). Prefer the exact dir from transcript_path
    # (robust to slug munging); fall back to the cwd->slug convention.
    TRANSCRIPT_DIR=""
    if [ -n "$TRANSCRIPT_PATH" ]; then
        cand=$(dirname "$TRANSCRIPT_PATH")
        [ -d "$cand" ] && TRANSCRIPT_DIR="$cand"
    fi
    if [ -z "$TRANSCRIPT_DIR" ]; then
        # Claude Code's slug replaces BOTH `/` and `.` with `-`. The old version
        # replaced only `/`, so for any worktree under `.claude/worktrees/` it
        # produced `...-mcp-.claude-...` where the real directory is
        # `...-mcp--claude-...` — a path that never exists. `sessions_since` then
        # returned its unassessable sentinel and the hook went quiet for the
        # wrong reason. Verified against both real directories on disk.
        slug=$(transcript_dir_slug "$PROJECT_DIR")
        TRANSCRIPT_DIR="$HOME/.claude/projects/$slug"
    fi
    # BASIS UNIFICATION (BACKLOG #214). The boundary above and the count below
    # must describe the SAME session scope. They used to be free to disagree:
    # the boundary came from PROJECT_DIR (CLAUDE_PROJECT_DIR-first) while the
    # count came from transcript_path's directory. The fire log caught them
    # apart — firings stamped with a `session-259` root while carrying counts
    # only the primary's 43-transcript directory can produce, for a worktree
    # that has no transcript directory at all. Both now derive from the same
    # payload, so a mismatch is a bug rather than the normal case.
    debug "boundary root=$PROJECT_DIR transcripts=$TRANSCRIPT_DIR"

    RAW=$(sessions_since "$LAST_TS" "$TRANSCRIPT_DIR")
    if [ "$RAW" -lt 0 ]; then
        # Cannot assess activity (transcript dir unreadable) and there is no calendar
        # floor -> stay quiet rather than nag every session.
        debug "transcript dir unreadable ($TRANSCRIPT_DIR), staying silent"
        exit 0
    fi
    N=$(( RAW - 1 ))            # exclude the current in-progress session
    [ "$N" -lt 0 ] && N=0
    if [ "$N" -lt "$SESSIONS_THRESHOLD" ]; then
        debug "${N} sessions since last /dream pass (< ${SESSIONS_THRESHOLD}), staying silent"
        exit 0
    fi
    # ── Concurrency check ──────────────────────────────────────────────
    # Is another session already running a dream pass? The strongest local
    # signal is a worktree whose BRANCH NAME contains "dream". Match on
    # the bracket-enclosed branch field only (`[wt/dream-*]`), not the
    # full line — the worktree's filesystem path may contain "dream" for
    # unrelated reasons (test directories, parent folder names). This hook
    # fires at SessionStart BEFORE the current session creates its own
    # worktree, so any match belongs to another session. A stale worktree
    # (finished session, not cleaned up) is a false positive — the message
    # tells the user how to clear it. Degrades silently if
    # `git worktree list` fails.
    DREAM_WT=$(git -C "$PROJECT_DIR" worktree list 2>/dev/null \
        | grep -vE '\[(main|master)\]' \
        | grep -iE '\[.*dream.*\]' \
        | sed -n '1p' || true)
    if [ -n "$DREAM_WT" ]; then
        DREAM_WT_PATH=$(echo "$DREAM_WT" | awk '{print $1}')
        MODE="skipped-concurrent"
        MSG="Dream cadence: ${N} sessions since the last /dream pass in this project (fires at >=${SESSIONS_THRESHOLD}), but another session appears to be running a dream pass (worktree: ${DREAM_WT_PATH}). Skipping auto-run to avoid duplicate work. If that session has finished, clean up with \`git worktree remove ${DREAM_WT_PATH} && git worktree prune\` and the next session will auto-run."
        debug "concurrent dream worktree detected: $DREAM_WT_PATH"
    elif [ "${DREAM_AUTORUN:-1}" = "0" ]; then
        MODE="nudge"
        MSG="Dream cadence: ${N} sessions since the last /dream pass in this project (fires at >=${SESSIONS_THRESHOLD}). Consider running /dream to mine recent sessions for unpersisted decisions, lessons, or references."
    else
        MODE="directive"
        MSG="Dream cadence: ${N} sessions since the last /dream pass in this project (fires at >=${SESSIONS_THRESHOLD}). AUTO-RUN: execute the dream pass now — read ~/.claude/skills/dream/procedure.md and follow it. Mine the last 4 sessions max; if more than 4 accumulated, tell the user how many older sessions were skipped, before the Phase 5 commit. Run the Phase 2 analysis subagents with run_in_background: true so the user's task is not blocked. Present the Phase 3 proposals for the user's approval at a natural boundary (when the current task completes — never mid-task), and do NOT apply or commit anything without that approval. Before the Phase 5 commit, re-check git log for a newer /dream pass (a concurrent session may have finished one). The Phase 5 commit MUST carry a \`Dream-Pass: sessions <range>\` trailer (last paragraph, own line) — that trailer IS the cadence boundary this hook reads; a subject-line phrasing is only a legacy fallback. Set DREAM_AUTORUN=0 to revert to advisory nudges."
    fi

    # Fire log (the FIRE half of the fired-vs-ran instrument; the RAN half is the
    # subsequent "/dream pass" commit). Best-effort — must never block the inject.
    FIRE_LOG="${DREAM_FIRE_LOG:-$HOME/.claude/dream-directive-fires.log}"
    {
        printf '%s %s fired mode=%s n=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PROJECT_DIR" "$MODE" "$N" >> "$FIRE_LOG"
        if [ "$(wc -c < "$FIRE_LOG" | tr -d ' ')" -gt 102400 ]; then
            tail -n 500 "$FIRE_LOG" > "${FIRE_LOG}.tmp" && mv "${FIRE_LOG}.tmp" "$FIRE_LOG"
        fi
    } 2>/dev/null || true
fi

python3 -c "import json, sys; sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$MSG" 2>/dev/null || true
exit 0
