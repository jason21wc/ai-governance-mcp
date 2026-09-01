#!/usr/bin/env bash
# all-clear — is every parallel session's work committed, landed, and cleaned up?
#
# WHY THIS EXISTS
# ---------------
# Running several sessions across worktrees is ordinary GitHub Flow, and the repo
# already had good machinery for STARTING that work (start-worktree/preflight.sh)
# and for REMOVING one worktree (cleanup.sh). What nothing computed was the
# fleet-level question a human actually asks at the end of a day: "is everything
# in, everywhere?"
#
# It has to be COMPUTED, never recalled. The scar this repo carries is a
# hand-written "ACTION ON RESUME: nothing pending" that sat in a memory file while
# 2 stale branches, an orphan worktree, 2 unpushed tags, an open PR and 5 unpushed
# commits accumulated behind it. A claim about derivable state rots the instant it
# is written. So this prints what git says, right now.
#
# THREE AXES, DELIBERATELY SEPARATE
#   CLEAN    — nothing uncommitted in the working tree
#   DURABLE  — the commits exist somewhere other than this disk
#   LANDED   — the commits reached the branch everyone else reads
# Conflating any two of these is the defect that motivated this tool: cleanup.sh
# checked DURABLE and reported it as safe-to-remove, so a branch that was pushed
# and never merged was removed with its local branch deleted (verified 2026-08-14).
# `start-worktree` step 4c publishes every branch at creation, which is why DURABLE
# is nearly always true here and is the weakest of the three signals.
#
# WHAT THIS TOOL WILL NOT DO
#   * It never mutates. It prints commands; a human runs them. Same invariant as
#     repo_hygiene.py, and for the same reason: per-push authorization is a
#     deliberate gate and a tool that pushed or deleted refs would walk through it.
#   * It never proposes deleting a branch on ancestry alone. Ancestry LIES after a
#     rebase or squash — `--no-merged` once called three branches unmerged when
#     every file they touched was byte-identical to main. Unlanded branches get
#     evidence and a merge command, never a delete command.
#   * It does not duplicate repo_hygiene.py. Where that script exists it is RUN,
#     and its findings are folded in. Where it does not, the surfaces only it
#     covers (PRs, tags, keep-markers) are reported as UNCHECKED — not as clean.
#
# EXIT CODES (aligned with scripts/repo_hygiene.py — callers key on the split)
#   0  all clear   — every check ran and nothing is outstanding
#   1  findings    — something is uncommitted, unpushed, unlanded, or left behind
#   2  undetermined— a check could not run. NOT clear. The human decides.
#   3  not a git repository
# Never conflate 2 with 0. "The tool broke" must never read as "you are clear."

set -uo pipefail
export GIT_TERMINAL_PROMPT=0
# Read-only means read-only. Without this, `git status` AND `git diff` (the content
# arm of the landed check) refresh the index stat cache — a real write, and a real
# `index.lock` contention hazard against the live sibling sessions this tool exists
# to report on. Set once here rather than per-call: two mechanisms for one property
# is how they drift apart. Caught by test_run_changes_nothing once it started
# snapshotting the index mtime; a per-call `--no-optional-locks` on `status` alone
# had missed `git diff` entirely.
export GIT_OPTIONAL_LOCKS=0

say()   { printf '%s\n' "$*"; }
hdr()   { printf '\n%s\n' "$*"; }
item()  { printf '  %s\n' "$*"; }
fix()   { printf '      → %s\n' "$*"; }

FINDINGS=0
UNDETERMINED=0
LIVE=0

# Cross-consumer contract. Keep this exact, ordered marker in parity with the
# producer, cleanup gate, and repo_hygiene.py.
# shellcheck disable=SC2034
JOURNAL_V2_KEYS="version host lifecycle_owner path branch base_sha default_ref owner_pid session_id task_key parallel_task state updated_at"
TASK_KEYS=()
TASK_PARALLEL=()
TASK_BRANCHES=()
TASK_PATHS=()
TASK_SOURCES=()
TASK_STATES=()
TASK_KEY_SET=""

usage() {
    say "Usage: allclear.sh [--repo <path>] [--prefix <str>] [--quiet]"
    say ""
    say "Reports whether every worktree and branch in this repository is"
    say "committed, durable (on a remote), and landed (in the default branch)."
    say "Read-only: it prints commands, it never runs them."
    say ""
    say "  --repo <path>    Repository to inspect (default: current directory)"
    say "  --prefix <str>   Session-branch prefix (default: wt/). Remote branches"
    say "                   outside it are listed but do not gate the verdict."
    say "  --memory <dir>   Handoff/memory directory to check for freshness"
    say "                   (default: _ai-context). Skipped silently if absent."
    say "                   CHECKED, never written — see the completion sequence."
    say "  --quiet          Print only findings and the verdict"
    say ""
    say "Exit: 0=all clear, 1=findings, 2=undetermined, 3=not a git repo"
}

REPO="."
QUIET=0
SESSION_PREFIX="wt/"
MEMORY_DIR="_ai-context"
# `shift 2` with only one argument left returns 1 and DOES NOT SHIFT. An earlier
# version wrote `shift 2 || true`, which swallowed that failure and left $1 as
# `--repo` forever — `bash allclear.sh --repo` hung with no output, before any git
# call. `${2:-}` had defused `set -u`, so nothing crashed either. Reproduced
# 2026-08-14 (10s timeout, rc=124). Require the value explicitly instead.
need_value() {
    [ "$2" -ge 2 ] || { say "FATAL: $1 requires a value"; usage; exit 2; }
}
while [ $# -gt 0 ]; do
    case "$1" in
        --repo)    need_value "$1" $#; REPO="$2"; shift 2 ;;
        --prefix)  need_value "$1" $#; SESSION_PREFIX="$2"; shift 2 ;;
        --memory)  need_value "$1" $#; MEMORY_DIR="$2"; shift 2 ;;
        --quiet)   QUIET=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *)         say "Unknown argument: $1"; usage; exit 2 ;;
    esac
done

command -v git >/dev/null 2>&1 || { say "FATAL: git not found"; exit 2; }
cd "$REPO" 2>/dev/null || { say "FATAL: no such path: $REPO"; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { say "not a git repository: $REPO"; exit 3; }

# Operate from the PRIMARY checkout. Every fact below is checkout-variant, and
# reading them from inside one worktree reports that worktree's state as the
# repository's. The common dir is shared by every worktree, so it identifies the
# repo regardless of which tree we were invoked from.
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)"
case "$COMMON" in /*) : ;; *) COMMON="$PWD/$COMMON" ;; esac
PRIMARY="$(cd "$COMMON/.." 2>/dev/null && pwd)" || {
    say "FATAL: could not resolve the primary checkout"; exit 2; }
cd "$PRIMARY" || { say "FATAL: could not enter $PRIMARY"; exit 2; }

[ "$QUIET" -eq 1 ] || say "repository : $PRIMARY"

# --- default-branch candidates ----------------------------------------------
# Both local and remote defaults count as "landed". A solo flow that merges into
# local main and defers the push (per-push authorization is deliberate here) has
# genuinely landed the work; refusing there would be a false alarm, and a check
# that cries wolf gets tuned out.
# Resolve the default branch NAME once, then accept only ITS local and remote
# forms. Collecting `origin/main, origin/master, main, master` as independent
# candidates and matching the first would mean a repo whose real default is
# `develop`, still carrying a legacy `master`, reports work that only ever reached
# `master` as landed. Reproduced 2026-08-14 in the sibling script, which had the
# same block.
DEFAULT_NAME=""
DEFAULT_NAME=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$DEFAULT_NAME" ]; then
    for _c in main master; do
        if git rev-parse --verify --quiet "origin/$_c" >/dev/null 2>&1 \
           || git rev-parse --verify --quiet "$_c" >/dev/null 2>&1; then
            DEFAULT_NAME="$_c"; break
        fi
    done
fi
DEFAULT_REFS=""
_add_ref() { git rev-parse --verify --quiet "$1" >/dev/null 2>&1 && DEFAULT_REFS="${DEFAULT_REFS}${DEFAULT_REFS:+ }$1"; }
if [ -n "$DEFAULT_NAME" ]; then
    _add_ref "origin/$DEFAULT_NAME"
    _add_ref "$DEFAULT_NAME"
fi
PRIMARY_REF=${DEFAULT_REFS%% *}

if [ -z "$DEFAULT_REFS" ]; then
    item "????? could not resolve a default branch (tried origin/HEAD, origin/main, origin/master, main, master)"
    fix "merge state is UNKNOWN for every branch below — this is not 'clear'"
    UNDETERMINED=1
fi

# landed <branch> -> 0 if nothing on <branch> is missing from any default ref.
# The content arm is what makes squash- and rebase-merges pass: their SHAs differ
# from everything on the branch, so ancestry alone would report landed work as not.
landed() {
    local br="$1" ref n
    [ -z "$DEFAULT_REFS" ] && return 1
    for ref in $DEFAULT_REFS; do
        n=$(git rev-list --count "$ref..$br" 2>/dev/null) || continue
        [ "${n:-1}" = "0" ] && return 0
        git diff --quiet "$ref" "$br" 2>/dev/null && return 0
    done
    return 1
}

# --- ai-worktree pid liveness — CANONICAL BLOCK ------------------------------
# Byte-identical in start-worktree/prepare.sh, start-worktree/cleanup.sh and
# all-clear/allclear.sh. tests/test_worktree_ownership.py::
# test_all_three_consumers_carry_a_byte_identical_liveness_rule fails on drift.
# Duplicated rather than sourced from a shared file ON PURPOSE:
# sync-global-skills.sh links each global-skills/<skill>/ directory on its own
# and SKILLS_ONLY installs a subset, so a cross-skill helper would simply be
# absent on a partial install and every consumer would break at once.
#
# Returns 0 = ALIVE or UNKNOWN (never take a destructive action)
#         1 = PROVED DEAD (ESRCH only)
# Only "no such process" proves death. EPERM means the process exists under
# another uid. Empty, non-numeric, <=1 and every unrecognised error are UNKNOWN,
# and UNKNOWN degrades to alive: a false "dead" hands someone a removal command
# for a tree another session is writing to, a false "alive" only leaves residue.
#
# `kill` runs ONCE, and under LC_ALL=C. Calling it twice — once to test, once to
# capture stderr — let a process exit between the two calls and read as PROVED
# DEAD, which is the destructive direction. The C locale matters because the
# match below is on English text: under a localised Linux runner nothing would
# ever prove dead, and every stale worktree would become permanently unclaimable.
pid_alive() {
  case "${1:-}" in
    ''|*[!0-9]*) return 0 ;;
  esac
  [ "$1" -gt 1 ] 2>/dev/null || return 0
  _pa_err="$(LC_ALL=C; export LC_ALL; kill -0 "$1" 2>&1)" && return 0
  case "$_pa_err" in
    *'o such process'*|*ESRCH*) return 1 ;;
    *) return 0 ;;
  esac
}
# --- end ai-worktree pid liveness --------------------------------------------

# =============================================================================
# 1. WORKTREES
# =============================================================================
# Exactly one pid token, or nothing. Zero means "no pid recorded"; MORE than
# one is AMBIGUOUS, and the two parsers disagreed about it — this one used a
# greedy sed and took the LAST token while repo_hygiene took the FIRST, so one
# reason yielded two different owners. Neither answer is defensible, so this
# returns neither and the caller treats ownership as unknown.
# `\b`, not `[[:<:]]`: the latter is a BSD extension GNU grep rejects, and
# this file runs on Linux runners too.
_lock_reason_pid() {
    local hits n
    hits=$(printf '%s\n' "$1" | grep -oE '\bpid[ =][0-9]+' | grep -oE '[0-9]+$')
    n=$(printf '%s\n' "$hits" | grep -c . || true)
    [ "${n:-0}" -eq 1 ] || return 1
    printf '%s\n' "$hits"
}

_journal_v2_candidate() {
    LC_ALL=C grep -Eq '^(version=2|task_key=|parallel_task=)' "$1" 2>/dev/null
}

_validate_v2_journal() {
    LC_ALL=C awk '
      BEGIN {
        expected[1]="version"; expected[2]="host"; expected[3]="lifecycle_owner"
        expected[4]="path"; expected[5]="branch"; expected[6]="base_sha"
        expected[7]="default_ref"; expected[8]="owner_pid"; expected[9]="session_id"
        expected[10]="task_key"; expected[11]="parallel_task"; expected[12]="state"
        expected[13]="updated_at"
      }
      {
        if (NR > 13 || index($0, "=") < 2) exit 1
        key=substr($0, 1, index($0, "=") - 1)
        value=substr($0, index($0, "=") + 1)
        if (key != expected[NR] || value ~ /[[:cntrl:]]/) exit 1
        if (NR == 1 && value != "2") exit 1
        if (NR == 2 && value !~ /^(claude|codex-cli|codex-desktop)$/) exit 1
        if (NR == 3 && value !~ /^(framework|codex-desktop)$/) exit 1
        if (NR == 4 && value !~ /^\//) exit 1
        if (NR == 5 && value == "") exit 1
        if (NR == 6 && ((length(value) != 40 && length(value) != 64) || value ~ /[^0-9a-f]/)) exit 1
        if (NR == 7 && value == "") exit 1
        if (NR == 8 && value != "" && (value ~ /[^0-9]/ || value + 0 <= 1)) exit 1
        if (NR == 10 && (length(value) < 1 || length(value) > 128 || value !~ /^[a-z0-9][a-z0-9._:\/-]*$/)) exit 1
        if (NR == 11 && value !~ /^[01]$/) exit 1
        if (NR == 12 && value !~ /^(attached|created|published|locked|ready|setup-failed|task-conflict)$/) exit 1
        if (NR == 13 && value !~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z$/) exit 1
      }
      END { if (NR != 13) exit 1 }
    ' "$1"
}

_journal_value() {
    awk -v wanted="$2" 'index($0, wanted "=") == 1 { print substr($0, length(wanted) + 2); exit }' "$1"
}

_legacy_task_from_branch() {
    if [[ "$1" =~ ^wt/(.+)-[0-9a-f]{8}$ ]]; then
        printf 'slug:%s\n' "${BASH_REMATCH[1]}"
        return 0
    fi
    return 1
}

_record_task() {
    local key="$1" parallel="$2" branch="$3" path="$4" source="$5" state="$6" i
    i=${#TASK_KEYS[@]}
    TASK_KEYS[i]="$key"
    TASK_PARALLEL[i]="$parallel"
    TASK_BRANCHES[i]="$branch"
    TASK_PATHS[i]="$path"
    TASK_SOURCES[i]="$source"
    TASK_STATES[i]="$state"
    case " $TASK_KEY_SET " in
        *" $key "*) : ;;
        *) TASK_KEY_SET="${TASK_KEY_SET}${TASK_KEY_SET:+ }$key" ;;
    esac
}

_report_task_collisions() {
    # Detection only, never a mutex: this read-only snapshot does not reserve a
    # task key and does not remove either side of a collision.
    local key count parallel_count baseline_count conflict_count intentional legacy_only i printed
    [ -z "$TASK_KEY_SET" ] && return 0
    printed=0
    for key in $TASK_KEY_SET; do
        count=0; parallel_count=0; baseline_count=0; conflict_count=0; intentional=0; legacy_only=1
        i=0
        while [ "$i" -lt "${#TASK_KEYS[@]}" ]; do
            if [ "${TASK_KEYS[$i]}" = "$key" ]; then
                count=$((count + 1))
                if [ "${TASK_SOURCES[$i]}" = "v2" ]; then
                    if [ "${TASK_PARALLEL[$i]}" = "1" ]; then
                        parallel_count=$((parallel_count + 1))
                    else
                        baseline_count=$((baseline_count + 1))
                    fi
                    [ "${TASK_STATES[$i]}" = "task-conflict" ] && conflict_count=$((conflict_count + 1))
                fi
                [ "${TASK_SOURCES[$i]}" = "legacy-derived" ] || legacy_only=0
            fi
            i=$((i + 1))
        done
        [ "$count" -gt 1 ] || continue
        if [ "$legacy_only" -eq 0 ] && [ "$baseline_count" -eq 1 ] \
           && [ "$parallel_count" -eq $((count - 1)) ] && [ "$conflict_count" -eq 0 ]; then
            intentional=1
        fi
        if [ "$printed" -eq 0 ]; then hdr "TASK COORDINATION"; printed=1; fi
        if [ "$legacy_only" -eq 1 ]; then
            item "COLLISION $key — $count legacy worktrees share a generated slug; ownership is ambiguous"
            FINDINGS=$((FINDINGS + 1))
        elif [ "$intentional" -eq 1 ]; then
            item "parallel $key — one baseline and $parallel_count explicitly authorized parallel worktree(s)"
        else
            item "COLLISION $key — $count active worktrees claim the same task without explicit parallel authorization"
            FINDINGS=$((FINDINGS + 1))
        fi
        i=0
        while [ "$i" -lt "${#TASK_KEYS[@]}" ]; do
            if [ "${TASK_KEYS[$i]}" = "$key" ]; then
                item "      ${TASK_BRANCHES[$i]} — ${TASK_PATHS[$i]} (${TASK_SOURCES[$i]}, state=${TASK_STATES[$i]}, parallel=${TASK_PARALLEL[$i]})"
            fi
            i=$((i + 1))
        done
    done
}

hdr "WORKTREES"
WT_PATH=""; WT_BRANCH=""; WT_HEAD=""; WT_DETACHED=0; WT_LOCK=""
flush_worktree() {
    [ -z "$WT_PATH" ] && return 0
    local label dirty dirty_out dirty_rc pidnum gd statepid evidence live_pid _p statefile taskkey parallel legacykey journal_kind lifecycle_owner legacy_lifecycle host base default expected_lock lock_start journal_branch journal_path state legacy_owner_lines
    label="${WT_BRANCH:-(detached)}"
    [ "$WT_PATH" = "$PRIMARY" ] && label="$label  [primary]"

    # Locking is handled once, globally, by GIT_OPTIONAL_LOCKS=0 at the top.
    #
    # rc is captured SEPARATELY from the output. The old form piped straight into
    # `grep -c . || true`, so a git failure (worktree directory deleted but not
    # pruned, index.lock held, permissions) produced empty output, `grep -c` printed
    # 0, and the worktree was reported "clean and landed; the worktree can be
    # removed". Reproduced 2026-08-14. An unrun check must never read as a passed
    # one — this file states that rule at the top and this line used to break it.
    dirty_out=$(git -C "$WT_PATH" status --porcelain 2>/dev/null)
    dirty_rc=$?
    # `pid[ =]`, not a literal space. Claude Code writes `pid 12345`;
    # prepare.sh's framework lock reason writes `pid=12345`. Matching only the
    # space form extracted NOTHING from any framework-created worktree, so this
    # tool's liveness check was reading an empty pid for exactly the trees the
    # framework owns. cleanup.sh had the correct form; this one had not.
    pidnum=$(_lock_reason_pid "$WT_LOCK" || true)

    if [ "$dirty_rc" -ne 0 ]; then
        item "????? $label — could NOT read the working tree; state unknown, not clean"
        item "      $WT_PATH"
        UNDETERMINED=1
        return 0
    fi
    dirty=$(printf '%s' "$dirty_out" | grep -c . || true)

    # Ownership is TRI-STATE: proved live, proved dead, or UNKNOWN. The lock is
    # one piece of evidence, not the definition. This tool reported a checkout a
    # live Codex session was actively writing to as an "Orphan worktree" purely
    # because that tree carried no framework lock — absence of a lock is not
    # proof the owner is gone. The lifecycle journal's owner_pid is the other
    # source, and either one proving life is enough.
    gd=$(git -C "$WT_PATH" rev-parse --git-dir 2>/dev/null || true)
    case "$gd" in ""|/*) : ;; *) gd="$WT_PATH/$gd" ;; esac
    statepid=""
    journal_kind="legacy"
    if [ -n "$gd" ]; then
        statefile="$gd/ai-worktree-state"
        if [ -f "$statefile" ]; then
            if _journal_v2_candidate "$statefile"; then
                journal_kind="v2"
                if _validate_v2_journal "$statefile"; then
                    statepid=$(_journal_value "$statefile" owner_pid)
                    taskkey=$(_journal_value "$statefile" task_key)
                    parallel=$(_journal_value "$statefile" parallel_task)
                    lifecycle_owner=$(_journal_value "$statefile" lifecycle_owner)
                    state=$(_journal_value "$statefile" state)
                    journal_branch=$(_journal_value "$statefile" branch)
                    journal_path=$(_journal_value "$statefile" path)
                    default=$(_journal_value "$statefile" default_ref)
                    base=$(_journal_value "$statefile" base_sha)
                    if ! git check-ref-format --branch "$journal_branch" >/dev/null 2>&1 \
                       || ! git check-ref-format --branch "$default" >/dev/null 2>&1; then
                        item "????? $label — v2 journal contains a malformed branch or default ref"
                        item "      $statefile"
                        UNDETERMINED=1
                        journal_kind="invalid-v2"
                    elif [ "$lifecycle_owner" = "framework" ]; then
                        host=$(_journal_value "$statefile" host)
                        expected_lock="ai-worktree-v2 host=$host lifecycle=framework branch=$WT_BRANCH default=$default base=$base pid=$statepid task=$taskkey parallel=$parallel start="
                        lock_start="${WT_LOCK#"$expected_lock"}"
                        if [ "$journal_path" = "$WT_PATH" ] \
                           && [ "$journal_branch" = "$WT_BRANCH" ] \
                           && [ "$lock_start" != "$WT_LOCK" ] \
                           && [[ "$lock_start" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
                            _record_task "$taskkey" "$parallel" "$WT_BRANCH" "$WT_PATH" "v2" "$state"
                        else
                            item "????? $label — valid v2 journal does not match its exact ai-worktree-v2 Git lock"
                            item "      $statefile"
                            UNDETERMINED=1
                        fi
                    elif [ "$journal_path" = "$WT_PATH" ] \
                         && { { [ "$WT_DETACHED" -eq 1 ] && [ "$state" = "attached" ] && [ "$WT_HEAD" = "$base" ]; } \
                              || { [ "$WT_DETACHED" -eq 0 ] && [ "$journal_branch" = "$WT_BRANCH" ]; }; }; then
                        _record_task "$taskkey" "$parallel" "$WT_BRANCH" "$WT_PATH" "v2" "$state"
                    else
                        item "????? $label — Codex Desktop v2 journal does not match its registered path and branch/HEAD"
                        item "      $statefile"
                        UNDETERMINED=1
                    fi
                else
                    journal_kind="invalid-v2"
                    item "????? $label — malformed v2 ai-worktree-state journal; lifecycle and task ownership are unknown"
                    item "      $statefile"
                    UNDETERMINED=1
                fi
            else
                legacy_owner_lines=$(grep -c '^owner_pid=' "$statefile" || true)
                if [ "${legacy_owner_lines:-0}" -ne 1 ]; then
                    journal_kind="invalid-legacy"
                    item "????? $label — legacy journal owner_pid must appear exactly once"
                    item "      $statefile"
                    UNDETERMINED=1
                else
                    statepid=$(sed -n 's/^owner_pid=//p' "$statefile")
                    legacy_lifecycle=$(sed -n 's/^lifecycle_owner=//p' "$statefile" | head -1)
                    if [ "$legacy_lifecycle" = "codex-desktop" ] && [ -z "$statepid" ]; then
                        : # Historical Desktop v1 deliberately recorded no process owner.
                    elif ! [ "$statepid" -gt 1 ] 2>/dev/null; then
                        journal_kind="invalid-legacy"
                        item "????? $label — legacy journal owner_pid is malformed"
                        item "      $statefile"
                        UNDETERMINED=1
                        statepid=""
                    fi
                fi
            fi
        fi
    fi
    if [ "$journal_kind" = "legacy" ]; then
        legacykey=$(_legacy_task_from_branch "$WT_BRANCH" || true)
        [ -n "$legacykey" ] && _record_task "$legacykey" "0" "$WT_BRANCH" "$WT_PATH" "legacy-derived" "legacy"
    fi
    evidence=""
    for _p in $pidnum $statepid; do evidence="$evidence $_p"; done
    live_pid=""
    for _p in $evidence; do
        if pid_alive "$_p"; then live_pid="$_p"; break; fi
    done

    if [ -n "$live_pid" ]; then
        # PRESENCE, NOT A FINDING. A teammate mid-flight is not residue, and
        # flagging it as one trains the reader to ignore this whole report.
        item "live  $label — in use by a live session (pid $live_pid)"
        item "      $WT_PATH"
        LIVE=$((LIVE + 1))
        return 0
    fi

    # No ownership evidence at all is NOT escalated here. This report is
    # advisory and prints commands the human runs; the destructive gate lives in
    # cleanup.sh, which does its own ownership check and refuses on live or
    # conflicting evidence. Escalating here only turns every ordinary worktree
    # into an UNDETERMINED verdict without preventing anything.

    if [ "${dirty:-0}" -gt 0 ]; then
        item "DIRTY $label — $dirty uncommitted file(s)"
        item "      $WT_PATH"
        fix "git -C '$WT_PATH' status"
        FINDINGS=$((FINDINGS + 1))
    elif [ "$WT_DETACHED" -eq 1 ]; then
        item "????? (detached HEAD) at $WT_PATH — cannot verify merge state"
        UNDETERMINED=1
    elif [ "$WT_PATH" != "$PRIMARY" ]; then
        if landed "$WT_BRANCH"; then
            item "done  $label — clean and landed; the worktree can be removed"
            fix "bash \"\$SKILL/cleanup.sh\" '$WT_PATH'   (start-worktree skill)"
            FINDINGS=$((FINDINGS + 1))
        fi
        # An unlanded worktree branch is reported once, in the BRANCHES section,
        # with its evidence. Reporting it here too would double-count it.
    fi
}
# Capture BEFORE the loop so the exit status is inspectable. Feeding the loop
# straight from a command substitution discards it, and an empty result then reads
# as "no worktrees" — indistinguishable from "the command failed". Same class as
# the status-rc bug above; there were four of these and this is one.
WT_LIST=$(git worktree list --porcelain 2>/dev/null)
WT_LIST_RC=$?
if [ "$WT_LIST_RC" -ne 0 ]; then
    item "????? could NOT list worktrees (git exited $WT_LIST_RC) — none were examined"
    UNDETERMINED=1
else
    while IFS= read -r line; do
        case "$line" in
            "worktree "*) flush_worktree; WT_PATH="${line#worktree }"; WT_BRANCH=""; WT_HEAD=""; WT_DETACHED=0; WT_LOCK="" ;;
            "HEAD "*)     WT_HEAD="${line#HEAD }" ;;
            "branch "*)   WT_BRANCH="${line#branch refs/heads/}" ;;
            "detached")   WT_DETACHED=1 ;;
            "locked "*)   WT_LOCK="${line#locked }" ;;
            "locked")     WT_LOCK="(no reason given)" ;;
        esac
    done <<EOF
$WT_LIST
EOF
    flush_worktree
fi

_report_task_collisions

# =============================================================================
# 2. BRANCHES — local, plus remote branches with no local counterpart
# =============================================================================
hdr "BRANCHES"
BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null)
BRANCHES_RC=$?
if [ "$BRANCHES_RC" -ne 0 ]; then
    # Without this, an empty BRANCHES makes `for b in $BRANCHES` iterate zero
    # times and NO branch is checked — while the verdict still reads ALL CLEAR.
    item "????? could NOT list local branches (git exited $BRANCHES_RC) — none were examined"
    UNDETERMINED=1
fi
# Strip from the FULL refname, not the short one. `%(refname:short)` of
# `refs/remotes/origin/HEAD` is the bare string `origin`, which sailed past a
# `grep -v '^HEAD$'` filter and produced a phantom branch named `origin/origin`
# in the first live run of this script.
REMOTE_ONLY=$(comm -13 \
    <(printf '%s\n' "$BRANCHES" | sort) \
    <(git for-each-ref --format='%(refname)' refs/remotes/origin/ 2>/dev/null \
        | sed 's|^refs/remotes/origin/||' | grep -v '^HEAD$' | sort) 2>/dev/null)

check_branch() {
    local br="$1" origin_label="$2" unpushed ahead ref
    # Skip the default branch itself — it is the thing others land INTO.
    for ref in $DEFAULT_REFS; do
        [ "$br" = "${ref#origin/}" ] && [ "$origin_label" = "local" ] && return 0
    done
    unpushed=$(git log --oneline "$br" --not --remotes 2>/dev/null | grep -c . || true)
    if [ "${unpushed:-0}" -gt 0 ]; then
        item "LOCAL $br — $unpushed commit(s) exist on NO remote (one disk)"
        fix "git push -u origin $br"
        FINDINGS=$((FINDINGS + 1))
    fi
    if [ -z "$DEFAULT_REFS" ]; then
        return 0   # already reported as undetermined at the top
    fi
    if ! landed "$br"; then
        ahead=$(git rev-list --count "$PRIMARY_REF..$br" 2>/dev/null || echo "?")
        # NO delete command is offered here, deliberately. Ancestry lies after a
        # rebase or squash, and a tool that proposes deletion on it is either
        # useless or destructive. The human adjudicates.
        case "$origin_label" in
            foreign)
                # Not session work — a PR branch, a bot branch, a collaborator's.
                # Listed as evidence, but it must NOT gate the verdict: "all clear"
                # has to mean "your sessions are in", not "the repo has zero open
                # branches", or it can never go green and stops being read.
                # repo_hygiene.py's stale-branch check owns these.
                item "note  $br — $ahead commit(s) not in $PRIMARY_REF (not a session branch; its PR or owner decides)"
                ;;
            *)
                item "OPEN  $br ($origin_label) — $ahead commit(s) not in $PRIMARY_REF"
                fix "git log --oneline $PRIMARY_REF..$br     # see what is unlanded"
                # The old hint said "(fast-forward)", which this script never
                # establishes — `landed()` proves the opposite direction, and once
                # the default branch has moved the push is simply rejected. Both
                # completion-sequence checklists gate exactly this with a
                # merge-base test; the hint now carries that gate instead of
                # asserting a property nothing checked.
                fix "git fetch origin && git merge-base --is-ancestor $PRIMARY_REF $br \\"
                fix "  && git push origin $br:${PRIMARY_REF#origin/}   # land it if it fast-forwards"
                FINDINGS=$((FINDINGS + 1))
                ;;
        esac
    fi
}
for b in $BRANCHES; do check_branch "$b" "local"; done
for b in $REMOTE_ONLY; do
    [ -z "$b" ] && continue
    # Session branches use the start-worktree naming scheme; anything else on the
    # remote belongs to someone or something that is not this fleet of sessions.
    case "$b" in
        "$SESSION_PREFIX"*) check_branch "origin/$b" "remote-only" ;;
        *)                  check_branch "origin/$b" "foreign" ;;
    esac
done

# =============================================================================
# 3. STASHES — uncommitted work that survives a clean `git status`
# =============================================================================
hdr "STASHES"
STASHES=$(git stash list 2>/dev/null)
STASH_RC=$?
if [ "$STASH_RC" -ne 0 ]; then
    item "????? could NOT read the stash list (git exited $STASH_RC) — not examined"
    UNDETERMINED=1
elif [ -n "$STASHES" ]; then
    printf '%s\n' "$STASHES" | while IFS= read -r s; do item "STASH $s"; done
    fix "git stash show -p <ref>   # inspect before deciding; never drop blind"
    FINDINGS=$((FINDINGS + $(printf '%s\n' "$STASHES" | grep -c .)))
fi

# =============================================================================
# 4. MEMORY — is the written handoff behind the work it describes?
# =============================================================================
#
# THE BOUNDARY, STATED ON PURPOSE: this CHECKS freshness, it does not WRITE.
# Whether the notes are any good is a judgment call, and the completion sequence
# owns it (item 17: SESSION-STATE / PROJECT-MEMORY / LEARNING-LOG). Making this
# script author prose would put a hand-written-claim generator inside the tool
# built to replace hand-written claims — the exact thing its header objects to.
#
# What IS derivable: how many commits landed after the memory directory was last
# touched. Zero means the handoff describes the tree you actually have. Nonzero
# means you will resume from a description of an older repo, which is the
# "ACTION ON RESUME: nothing pending" failure this whole file exists for, in its
# other form.
#
# Absent memory dir = silent skip, not a finding. Most repos do not keep one, and
# a check that fires everywhere it does not apply gets tuned out (T-169).
if [ -n "$MEMORY_DIR" ] && [ -d "$PRIMARY/$MEMORY_DIR" ]; then
    hdr "MEMORY"
    MEM_COMMIT=$(git log -1 --format=%H -- "$MEMORY_DIR" 2>/dev/null)
    if [ -z "$MEM_COMMIT" ]; then
        item "????? $MEMORY_DIR exists but has no commit history — cannot tell if it is current"
        UNDETERMINED=1
    else
        MEM_BEHIND=$(git rev-list --count "$MEM_COMMIT..HEAD" 2>/dev/null)
        MEM_RC=$?
        if [ "$MEM_RC" -ne 0 ]; then
            item "????? could NOT compare $MEMORY_DIR against HEAD (git exited $MEM_RC)"
            UNDETERMINED=1
        elif [ "${MEM_BEHIND:-0}" -gt 0 ]; then
            item "STALE $MEMORY_DIR is $MEM_BEHIND commit(s) behind HEAD — the handoff describes an older tree"
            fix "git log --oneline $MEM_COMMIT..HEAD    # what happened since it was written"
            fix "then update the memory files (completion sequence, item 17) — this tool will not write them"
            FINDINGS=$((FINDINGS + 1))
        else
            item "ok    $MEMORY_DIR is current with HEAD"
        fi
    fi
fi

# =============================================================================
# 5. DELEGATE — repo_hygiene.py owns PRs, tags, keep-markers, stale-branch evidence
# =============================================================================
hdr "STANDING HYGIENE"
HYG="$PRIMARY/scripts/repo_hygiene.py"
if [ -f "$HYG" ] && command -v python3 >/dev/null 2>&1; then
    # stderr is KEPT: on rc=2 repo_hygiene prints its exception there, and
    # discarding it left "could not run (rc=2)" with the reason thrown away.
    HYG_OUT=$(python3 "$HYG" --repo "$PRIMARY" --min-severity warn 2>&1)
    HYG_RC=$?
    if [ "$HYG_RC" -gt 1 ]; then
        item "????? repo_hygiene.py could not run (rc=$HYG_RC) — this is NOT 'clean'"
        printf '%s\n' "$HYG_OUT" | sed 's/^/        /' | head -5
        UNDETERMINED=1
    elif [ -n "$HYG_OUT" ]; then
        printf '%s\n' "$HYG_OUT" | sed 's/^/  /'
        [ "$HYG_RC" -eq 1 ] && FINDINGS=$((FINDINGS + 1))
    fi
else
    # SCOPE NOTE, not UNDETERMINED — and the distinction is deliberate.
    # "An unrun check is not a passed check" applies to surfaces THIS tool claims:
    # failing to resolve a default branch makes merge state unknown, so that one
    # returns 2. Open PRs and unpushed tags are not surfaces this tool claims —
    # they are a bonus when the richer script happens to be present. Most repos
    # will not have it, and if its absence forced UNDETERMINED everywhere, the
    # verdict could never go green outside this repo and would stop being read
    # (the T-169 failure mode). So: state the scope plainly and keep the verdict
    # meaningful for what was actually examined.
    item "scope repo_hygiene.py not present — open PRs, unpushed tags and keep-markers"
    item "      were NOT examined. The verdict below covers worktrees, branches and stashes."
fi

# =============================================================================
# VERDICT
# =============================================================================
hdr "-----------------------------------------------------------------------"
[ "$LIVE" -gt 0 ] && say "$LIVE session(s) still live — those worktrees are in use, not residue."
if [ "$UNDETERMINED" -eq 1 ]; then
    say "UNDETERMINED — a check could not run. This is NOT 'all clear'; see ????? above."
    exit 2
elif [ "$FINDINGS" -gt 0 ]; then
    say "$FINDINGS item(s) outstanding. Nothing was changed — run the → commands yourself."
    exit 1
else
    say "ALL CLEAR — every worktree clean, every branch landed, nothing stashed or stranded."
    exit 0
fi
