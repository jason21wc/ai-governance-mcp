#!/usr/bin/env bash
# State-based worktree cleanup. Checks observable state (PID liveness, commit
# durability, merge completeness, clean tree) before removing — does NOT rely on
# Claude Code's session-identity ownership model, which breaks in continuation
# sessions.
#
# Unlike repo_hygiene.py (which NEVER mutates), this script EXECUTES destructive
# operations (worktree removal, branch deletion). The state-based pre-checks
# replace the identity-based ownership model that ExitWorktree relies on.
#
# EXIT CODES
#   0  completed  — framework tree removed, or Desktop runtime released/previewed
#   1  REFUSED    — a safety check failed; the refusal reason is printed
#   2  ERROR      — path not found, git failure, or usage error
#
# SAFETY HIERARCHY
# A false "safe to remove" destroys work. A false "not safe" is inconvenient.
# Every ambiguous case degrades toward "not safe."

set -uo pipefail

export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -oBatchMode=yes -oConnectTimeout=10}"

# --- output helpers (matching preflight.sh convention) ----------------------
say()    { printf '%s\n' "$*"; }
ok()     { printf 'ok     %s\n' "$*"; }
refuse() { printf 'REFUSE %s\n' "$*"; }
note()   { printf 'note   %s\n' "$*"; }

# --- argument parsing -------------------------------------------------------
FORCE=0
DRY_RUN=0
ALLOW_UNMERGED=0
ALLOW_IGNORED=0
OWNER_ACK_PID=""
TARGET=""
DEFAULT_NAME=""

usage() {
    say "Usage: cleanup.sh <worktree-path> [--default-ref <name>] [--owner-pid <pid>] [--force] [--dry-run] [--allow-unmerged]"
    say ""
    say "Safely remove a git worktree after verifying:"
    say "  - No live session owns it (PID check on lock)"
    say "  - DURABILITY:    all commits are represented on a remote"
    say "  - COMPLETENESS:  all commits have landed in the default branch"
    say "  - Working tree is clean (no uncommitted changes)"
    say "  - No irreplaceable IGNORED files (.env, keys) about to be deleted"
    say ""
    say "Flags:"
    say "  --force           Skip the PID liveness check (for PID-reuse false positives)"
    say "  --owner-pid PID   Cooperatively finalize a strict v2 framework worktree"
    say "                    while its recorded owner is still live"
    say "  --dry-run         Print what would happen without removing anything"
    say "  --allow-unmerged  Remove even though the work never landed in the default"
    say "                    branch. For the DELIBERATE discard case only. The branch"
    say "                    survives on its remote; the local branch does not."
    say "  --allow-ignored   Delete ignored files that look irreplaceable (.env, keys)"
    say "                    along with the worktree. They are on one disk only."
    say "  --default-ref     Exact integration branch name (preferred; otherwise read"
    say "                    from ai-worktree-state, then derive for legacy trees)"
    say "  --help            Show this message"
    say ""
    say "Exit codes: 0=completed, 1=refused (safety check failed), 2=error"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --force)          FORCE=1 ;;
        --dry-run)        DRY_RUN=1 ;;
        --allow-unmerged) ALLOW_UNMERGED=1 ;;
        --allow-ignored)  ALLOW_IGNORED=1 ;;
        --owner-pid)
            [ "$#" -ge 2 ] || { say "--owner-pid requires a PID"; exit 2; }
            OWNER_ACK_PID="$2"
            shift
            ;;
        --default-ref)
            [ "$#" -ge 2 ] || { say "--default-ref requires a branch name"; exit 2; }
            DEFAULT_NAME="$2"
            shift
            ;;
        --help|-h) usage; exit 0 ;;
        -*)        say "Unknown flag: $1"; usage; exit 2 ;;
        *)
            if [ -z "$TARGET" ]; then
                TARGET="$1"
            else
                say "Too many arguments"; usage; exit 2
            fi
            ;;
    esac
    shift
done

if [ -n "$OWNER_ACK_PID" ]; then
    case "$OWNER_ACK_PID" in
        *[!0-9]*|'') say "--owner-pid requires an integer greater than 1"; exit 2 ;;
    esac
    [ "$OWNER_ACK_PID" -gt 1 ] 2>/dev/null || {
        say "--owner-pid requires an integer greater than 1"; exit 2; }
fi
if [ "$FORCE" -eq 1 ] && [ -n "$OWNER_ACK_PID" ]; then
    say "--owner-pid and --force are incompatible"
    exit 2
fi

if [ -z "$TARGET" ]; then
    usage
    exit 0
fi

command -v git >/dev/null 2>&1 || { say "FATAL: git not found"; exit 2; }

# --- resolve paths ----------------------------------------------------------
TARGET_RESOLVED=$(realpath "$TARGET" 2>/dev/null || echo "$TARGET")
CWD_RESOLVED=$(realpath "$PWD" 2>/dev/null || echo "$PWD")

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

# --- parse git worktree list --porcelain ------------------------------------
PORCELAIN=$(git worktree list --porcelain 2>/dev/null) || {
    say "FATAL: not inside a git repository or git worktree list failed"; exit 2; }

FOUND=0
WT_BRANCH=""
WT_LOCKED=0
WT_LOCK_REASON=""
WT_LOCK_PID=""
WT_DETACHED=0

# Parse the porcelain output block by block.
# Each worktree block is separated by a blank line.
CURRENT_PATH=""
CURRENT_BRANCH=""
CURRENT_LOCKED=0
CURRENT_LOCK_REASON=""
CURRENT_DETACHED=0

_check_block() {
    if [ -z "$CURRENT_PATH" ]; then return; fi
    local resolved
    resolved=$(realpath "$CURRENT_PATH" 2>/dev/null || echo "$CURRENT_PATH")
    if [ "$resolved" = "$TARGET_RESOLVED" ]; then
        FOUND=1
        WT_BRANCH="$CURRENT_BRANCH"
        WT_LOCKED=$CURRENT_LOCKED
        WT_LOCK_REASON="$CURRENT_LOCK_REASON"
        WT_DETACHED=$CURRENT_DETACHED
        if [ -n "$WT_LOCK_REASON" ]; then
            WT_LOCK_PID=$(_lock_reason_pid "$WT_LOCK_REASON" || true)
        fi
    fi
}

while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
        "worktree "*)
            _check_block
            CURRENT_PATH="${line#worktree }"
            CURRENT_BRANCH=""
            CURRENT_LOCKED=0
            CURRENT_LOCK_REASON=""
            CURRENT_DETACHED=0
            ;;
        "branch "*)
            CURRENT_BRANCH="${line#branch refs/heads/}"
            ;;
        "detached")
            CURRENT_DETACHED=1
            ;;
        locked*)
            CURRENT_LOCKED=1
            local_reason="${line#locked}"
            CURRENT_LOCK_REASON="${local_reason# }"
            ;;
        "")
            _check_block
            CURRENT_PATH=""
            ;;
    esac
done <<< "$PORCELAIN"
_check_block  # handle last block (porcelain may not end with blank line)

# --- lifecycle metadata -----------------------------------------------------
# State lives in the linked worktree gitdir, outside the removable checkout.
# Legacy worktrees have no state record and continue through the conservative
# compatibility path below.
STATE_FILE=""
STATE_VERSION=""
STATE_HOST=""
LIFECYCLE_OWNER=""
STATE_PATH=""
STATE_BRANCH=""
STATE_BASE_SHA=""
STATE_DEFAULT=""
STATE_OWNER_PID=""
STATE_SESSION_ID=""
STATE_TASK_KEY=""
STATE_PARALLEL_TASK=""
STATE_LIFECYCLE_STATE=""
STATE_UPDATED_AT=""
STATE_FILE_HASH_INITIAL=""
JOURNAL_V2_KEYS="version host lifecycle_owner path branch base_sha default_ref owner_pid session_id task_key parallel_task state updated_at"
: "$JOURNAL_V2_KEYS"  # contract marker consumed by cross-consumer parity tests

_state_has_control_bytes() {
    LC_ALL=C od -An -t u1 "$1" 2>/dev/null | awk '
        { for (i = 1; i <= NF; i++) if (($i < 32 && $i != 10) || $i == 127) bad = 1 }
        END { exit bad ? 0 : 1 }
    '
}

_state_error() {
    STATE_PARSE_ERROR="$1"
    return 1
}

# Version 2 is an inter-process safety record, not a best-effort config file.
# Its fixed order makes truncation, duplicate fields, parser disagreement and
# schema drift observable. Do not loosen this parser with "first match wins".
_parse_v2_state() {
    local line line_no=0 stamp_digits
    STATE_PARSE_ERROR=""
    if _state_has_control_bytes "$STATE_FILE"; then
        _state_error "contains control bytes"
        return 1
    fi
    while IFS= read -r line || [ -n "$line" ]; do
        line_no=$((line_no + 1))
        case "$line_no" in
            1) [ "$line" = "version=2" ] || { _state_error "line 1 must be version=2"; return 1; } ;;
            2) case "$line" in host=*) STATE_HOST="${line#host=}" ;; *) _state_error "line 2 must be host"; return 1 ;; esac ;;
            3) case "$line" in lifecycle_owner=*) LIFECYCLE_OWNER="${line#lifecycle_owner=}" ;; *) _state_error "line 3 must be lifecycle_owner"; return 1 ;; esac ;;
            4) case "$line" in path=*) STATE_PATH="${line#path=}" ;; *) _state_error "line 4 must be path"; return 1 ;; esac ;;
            5) case "$line" in branch=*) STATE_BRANCH="${line#branch=}" ;; *) _state_error "line 5 must be branch"; return 1 ;; esac ;;
            6) case "$line" in base_sha=*) STATE_BASE_SHA="${line#base_sha=}" ;; *) _state_error "line 6 must be base_sha"; return 1 ;; esac ;;
            7) case "$line" in default_ref=*) STATE_DEFAULT="${line#default_ref=}" ;; *) _state_error "line 7 must be default_ref"; return 1 ;; esac ;;
            8) case "$line" in owner_pid=*) STATE_OWNER_PID="${line#owner_pid=}" ;; *) _state_error "line 8 must be owner_pid"; return 1 ;; esac ;;
            9) case "$line" in session_id=*) STATE_SESSION_ID="${line#session_id=}" ;; *) _state_error "line 9 must be session_id"; return 1 ;; esac ;;
            10) case "$line" in task_key=*) STATE_TASK_KEY="${line#task_key=}" ;; *) _state_error "line 10 must be task_key"; return 1 ;; esac ;;
            11) case "$line" in parallel_task=*) STATE_PARALLEL_TASK="${line#parallel_task=}" ;; *) _state_error "line 11 must be parallel_task"; return 1 ;; esac ;;
            12) case "$line" in state=*) STATE_LIFECYCLE_STATE="${line#state=}" ;; *) _state_error "line 12 must be state"; return 1 ;; esac ;;
            13) case "$line" in updated_at=*) STATE_UPDATED_AT="${line#updated_at=}" ;; *) _state_error "line 13 must be updated_at"; return 1 ;; esac ;;
            *) _state_error "contains unknown or duplicate fields"; return 1 ;;
        esac
    done < "$STATE_FILE"
    [ "$line_no" -eq 13 ] || { _state_error "is truncated or missing fields"; return 1; }
    : "$STATE_SESSION_ID"  # opaque but ordered; control bytes were rejected above

    case "$STATE_HOST:$LIFECYCLE_OWNER" in
        claude:framework|codex-cli:framework|codex-desktop:codex-desktop) : ;;
        *) _state_error "has an unsupported host/lifecycle_owner pair"; return 1 ;;
    esac
    case "$STATE_PATH" in /*) : ;; *) _state_error "path is not absolute"; return 1 ;; esac
    git check-ref-format --branch "$STATE_BRANCH" >/dev/null 2>&1 || {
        _state_error "branch is malformed"; return 1; }
    git check-ref-format --branch "$STATE_DEFAULT" >/dev/null 2>&1 || {
        _state_error "default_ref is malformed"; return 1; }
    case "$STATE_BASE_SHA" in ''|*[!0-9a-f]*) _state_error "base_sha is malformed"; return 1 ;; esac
    case "${#STATE_BASE_SHA}" in 40|64) : ;; *) _state_error "base_sha is malformed"; return 1 ;; esac
    case "$STATE_OWNER_PID" in *[!0-9]*) _state_error "owner_pid is malformed"; return 1 ;; esac
    if [ -n "$STATE_OWNER_PID" ]; then
        [ "$STATE_OWNER_PID" -gt 1 ] 2>/dev/null || { _state_error "owner_pid is malformed"; return 1; }
    fi
    case "$STATE_TASK_KEY" in [a-z0-9]*) : ;; *) _state_error "task_key is malformed"; return 1 ;; esac
    case "$STATE_TASK_KEY" in *[!a-z0-9._:/-]*) _state_error "task_key is malformed"; return 1 ;; esac
    [ "${#STATE_TASK_KEY}" -le 128 ] || { _state_error "task_key is too long"; return 1; }
    case "$STATE_PARALLEL_TASK" in 0|1) : ;; *) _state_error "parallel_task must be 0 or 1"; return 1 ;; esac
    case "$STATE_LIFECYCLE_STATE" in created|published|locked|ready|setup-failed|attached|task-conflict) : ;;
        *) _state_error "state is malformed"; return 1 ;;
    esac
    case "$STATE_UPDATED_AT" in ????-??-??T??:??:??Z) : ;; *) _state_error "updated_at is malformed"; return 1 ;; esac
    stamp_digits=$(printf '%s\n' "$STATE_UPDATED_AT" | tr -d -- '-:TZ')
    case "$stamp_digits" in ''|*[!0-9]*) _state_error "updated_at is malformed"; return 1 ;; esac
    return 0
}

_validate_v2_coherence() {
    local current_branch lock_prefix lock_stamp lock_stamp_digits
    [ "$STATE_PATH" = "$TARGET_RESOLVED" ] || {
        STATE_PARSE_ERROR="recorded path does not match the target"; return 1; }
    current_branch=$(git -C "$TARGET_RESOLVED" branch --show-current 2>/dev/null) || {
        STATE_PARSE_ERROR="could not read the current branch"; return 1; }
    if [ "$LIFECYCLE_OWNER" = "framework" ]; then
        [ "$STATE_BRANCH" = "$WT_BRANCH" ] && [ "$STATE_BRANCH" = "$current_branch" ] || {
            STATE_PARSE_ERROR="recorded branch does not match Git"; return 1; }
    elif [ -n "$current_branch" ]; then
        [ "$STATE_BRANCH" = "$WT_BRANCH" ] && [ "$STATE_BRANCH" = "$current_branch" ] || {
            STATE_PARSE_ERROR="recorded Desktop branch does not match Git"; return 1; }
    else
        [ "$STATE_LIFECYCLE_STATE" = "attached" ] \
            && [ "$(git -C "$TARGET_RESOLVED" rev-parse HEAD 2>/dev/null)" = "$STATE_BASE_SHA" ] || {
            STATE_PARSE_ERROR="detached Desktop checkout does not match its attached base"; return 1; }
    fi
    git -C "$TARGET_RESOLVED" cat-file -e "$STATE_BASE_SHA^{commit}" 2>/dev/null || {
        STATE_PARSE_ERROR="base_sha is not a commit in this repository"; return 1; }
    if [ -n "$DEFAULT_NAME" ] && [ "$DEFAULT_NAME" != "$STATE_DEFAULT" ]; then
        STATE_PARSE_ERROR="--default-ref does not match the journal"
        return 1
    fi
    if [ "$LIFECYCLE_OWNER" = "framework" ]; then
        [ -n "$STATE_OWNER_PID" ] || {
            STATE_PARSE_ERROR="framework v2 journal has no owner_pid"; return 1; }
        [ "$WT_LOCKED" -eq 1 ] || {
            STATE_PARSE_ERROR="framework v2 worktree is missing its Git lock"; return 1; }
        lock_prefix="ai-worktree-v2 host=$STATE_HOST lifecycle=framework branch=$STATE_BRANCH default=$STATE_DEFAULT base=$STATE_BASE_SHA pid=$STATE_OWNER_PID task=$STATE_TASK_KEY parallel=$STATE_PARALLEL_TASK start="
        case "$WT_LOCK_REASON" in "$lock_prefix"*) : ;; *) STATE_PARSE_ERROR="Git lock does not match the journal"; return 1 ;; esac
        lock_stamp="${WT_LOCK_REASON#"$lock_prefix"}"
        case "$lock_stamp" in ????-??-??T??:??:??Z) : ;; *) STATE_PARSE_ERROR="Git lock timestamp is malformed"; return 1 ;; esac
        lock_stamp_digits=$(printf '%s\n' "$lock_stamp" | tr -d -- '-:TZ')
        case "$lock_stamp_digits" in ''|*[!0-9]*) STATE_PARSE_ERROR="Git lock timestamp is malformed"; return 1 ;; esac
        [ "$WT_LOCK_PID" = "$STATE_OWNER_PID" ] || {
            STATE_PARSE_ERROR="Git lock owner does not match the journal"; return 1; }
    fi
    return 0
}
TARGET_GITDIR=$(git -C "$TARGET_RESOLVED" rev-parse --git-dir 2>/dev/null || true)
if [ -n "$TARGET_GITDIR" ]; then
    case "$TARGET_GITDIR" in /*) : ;; *) TARGET_GITDIR="$TARGET_RESOLVED/$TARGET_GITDIR" ;; esac
    STATE_FILE="$TARGET_GITDIR/ai-worktree-state"
    # Present but UNREADABLE is not absent. A journal naming a LIVE owner that
    # cannot be read would otherwise be skipped, letting a dead pid in the lock
    # reason decide the verdict — that path removed a live worktree.
    if [ -e "$STATE_FILE" ] && [ ! -r "$STATE_FILE" ]; then
        refuse "Ownership evidence exists but cannot be read: $STATE_FILE"
        note "Fix the permissions, or inspect the worktree by hand before removing it"
        exit 1
    fi
    if [ -f "$STATE_FILE" ]; then
        STATE_VERSION=$(sed -n '1s/^version=//p' "$STATE_FILE")
        if [ -z "$STATE_VERSION" ] \
            && grep -Eq '^(task_key|parallel_task|updated_at)=' "$STATE_FILE"; then
            refuse "Invalid framework lifecycle journal: v2 schema is missing version=2"
            exit 1
        fi
        case "$STATE_VERSION" in
            2)
                if ! _parse_v2_state || ! _validate_v2_coherence; then
                    refuse "Invalid framework lifecycle journal: $STATE_PARSE_ERROR"
                    exit 1
                fi
                ;;
            1|'')
                LIFECYCLE_OWNER=$(sed -n 's/^lifecycle_owner=//p' "$STATE_FILE" | head -1)
                STATE_DEFAULT=$(sed -n 's/^default_ref=//p' "$STATE_FILE" | head -1)
                # The journal is the lifecycle's OWN record of who owns this
                # checkout. Exactly one field is required: first-match parsing
                # lets a duplicated dead PID hide a later live owner.
                if [ "$LIFECYCLE_OWNER" = "codex-desktop" ]; then
                    STATE_OWNER_PID=""
                else
                    _legacy_owner_lines=$(grep -c '^owner_pid=' "$STATE_FILE" || true)
                    [ "${_legacy_owner_lines:-0}" -eq 1 ] || {
                        refuse "Invalid legacy lifecycle journal: owner_pid must appear exactly once"
                        exit 1
                    }
                    STATE_OWNER_PID=$(sed -n 's/^owner_pid=//p' "$STATE_FILE")
                    case "$STATE_OWNER_PID" in ''|*[!0-9]*)
                        refuse "Invalid legacy lifecycle journal: owner_pid is malformed"
                        exit 1
                        ;;
                    esac
                    [ "$STATE_OWNER_PID" -gt 1 ] 2>/dev/null || {
                        refuse "Invalid legacy lifecycle journal: owner_pid is malformed"
                        exit 1
                    }
                fi
                ;;
            *)
                refuse "Unsupported lifecycle journal version: $STATE_VERSION"
                exit 1
                ;;
        esac
        STATE_FILE_HASH_INITIAL=$(git hash-object "$STATE_FILE" 2>/dev/null) || {
            refuse "Could not fingerprint lifecycle journal"
            exit 1
        }
    fi
fi
if [ ! -f "$STATE_FILE" ]; then
    case "$WT_LOCK_REASON" in
        "ai-worktree-v2 "*)
            refuse "Invalid framework lifecycle journal: v2 Git lock has no journal"
            exit 1
            ;;
    esac
fi

run_teardown_hook() {
    local hook="$TARGET_RESOLVED/.ai-worktree/teardown.sh"
    [ -f "$hook" ] || return 0
    note "Running optional runtime hook: .ai-worktree/teardown.sh"
    AI_WORKTREE_ID="${WT_BRANCH#wt/}" \
    AI_WORKTREE_PATH="$TARGET_RESOLVED" \
    AI_WORKTREE_BRANCH="$WT_BRANCH" \
    AI_WORKTREE_DEFAULT_REF="$DEFAULT_NAME" \
        bash "$hook"
}

# --- pre-check 1: path exists in worktree list -----------------------------
if [ "$FOUND" -eq 0 ]; then
    say "ERROR: $TARGET is not a registered worktree"
    exit 2
fi

# This is a cooperative acknowledgement, not authentication: the caller says
# "the recorded owner is deliberately ending now." It is therefore available
# only when a strict v2 journal and its Git deletion guard agree exactly. Older
# records lack enough structure to distinguish acknowledgement from a bypass.
OWNER_ACKNOWLEDGED=0
if [ -n "$OWNER_ACK_PID" ]; then
    if [ "$STATE_VERSION" != "2" ] || [ "$LIFECYCLE_OWNER" != "framework" ]; then
        refuse "--owner-pid requires a strict v2 framework lifecycle journal"
        exit 1
    fi
    case "$STATE_LIFECYCLE_STATE" in
        ready) : ;;
        task-conflict)
            _conflict_head=$(git -C "$TARGET_RESOLVED" rev-parse HEAD 2>/dev/null || true)
            _conflict_dirty=$(git -C "$TARGET_RESOLVED" status --porcelain 2>/dev/null) || {
                refuse "Could not verify task-conflict worktree is pristine"
                exit 1
            }
            if [ "$_conflict_head" != "$STATE_BASE_SHA" ] || [ -n "$_conflict_dirty" ]; then
                refuse "task-conflict worktree is no longer pristine"
                exit 1
            fi
            ;;
        *)
            refuse "--owner-pid finalize requires lifecycle state ready or pristine task-conflict"
            exit 1
            ;;
    esac
    if [ "$OWNER_ACK_PID" != "$STATE_OWNER_PID" ] || [ "$OWNER_ACK_PID" != "$WT_LOCK_PID" ]; then
        refuse "--owner-pid does not match the coherent journal and Git lock owner"
        exit 1
    fi
    OWNER_ACKNOWLEDGED=1
fi

# Codex Desktop owns its native per-chat checkout lifecycle. The framework may
# release project runtime resources, but must never remove or unlock that tree.
if [ "$LIFECYCLE_OWNER" = "codex-desktop" ]; then
    [ -n "$DEFAULT_NAME" ] || DEFAULT_NAME="$STATE_DEFAULT"
    if [ "$DRY_RUN" -eq 1 ]; then
        ok "Dry run — would release runtime resources; Codex Desktop would retain checkout ownership"
        [ -f "$TARGET_RESOLVED/.ai-worktree/teardown.sh" ] && note "Would run: .ai-worktree/teardown.sh"
        exit 0
    fi
    if ! run_teardown_hook; then
        refuse "runtime teardown failed; Codex Desktop worktree was left intact"
        exit 1
    fi
    ok "Released runtime resources; Codex Desktop retains checkout lifecycle ownership"
    exit 0
fi

# --- pre-check 2: has a branch (not detached HEAD) -------------------------
if [ "$WT_DETACHED" -eq 1 ] || [ -z "$WT_BRANCH" ]; then
    refuse "Detached HEAD worktree — cannot verify commit safety; use manual cleanup"
    exit 1
fi

# --- pre-check 3: not the current worktree ----------------------------------
if [ "$CWD_RESOLVED" = "$TARGET_RESOLVED" ]; then
    refuse "Cannot remove the current worktree (you are in $TARGET_RESOLVED)"
    exit 1
fi

# --- pre-check 4: no live owner (tri-state ownership) -----------------------
#
# THE LOCK IS EVIDENCE, NOT THE DEFINITION. This check used to live entirely
# inside `if [ "$WT_LOCKED" -eq 1 ]`, so an UNLOCKED worktree got no ownership
# check at all — absence of a lock was read as proof the owner was gone. A lock
# can be released by hand, lost to a crash, or never taken by a host that does
# not use one, and the lifecycle journal that prepare.sh writes was sitting
# right there unread.
#
# Two sources, consulted whether or not the tree is locked: the lifecycle
# journal's owner_pid, which prepare.sh writes and which survives an unlock,
# and the Git lock reason, which corroborates it. Any ONE proving life
# refuses, and the two naming DIFFERENT owners refuses as well.
OWNER_EVIDENCE=""
for _p in $STATE_OWNER_PID $WT_LOCK_PID; do
    OWNER_EVIDENCE="$OWNER_EVIDENCE $_p"
done

if [ "$FORCE" -eq 1 ]; then
    note "PID check skipped (--force)"
else
    LIVE_OWNER=""
    for _p in $OWNER_EVIDENCE; do
        if pid_alive "$_p"; then LIVE_OWNER="$_p"; break; fi
    done
    if [ -n "$LIVE_OWNER" ]; then
        if [ "$OWNER_ACKNOWLEDGED" -eq 1 ] && [ "$LIVE_OWNER" = "$OWNER_ACK_PID" ]; then
            note "Recorded owner pid $LIVE_OWNER acknowledged finalization"
        else
            refuse "Live owner detected (pid $LIVE_OWNER is active)"
            [ -n "$WT_LOCK_REASON" ] && note "Lock reason: $WT_LOCK_REASON"
            [ -n "$STATE_OWNER_PID" ] && note "Journal owner_pid: $STATE_OWNER_PID"
            note "Use --owner-pid only when that strict v2 owner is ending this session"
            note "Use --force only for a verified PID-reuse false positive"
            exit 1
        fi
    fi
    # Two recorded owners that disagree are not a coherent lifecycle record.
    # One of them describes a session this tool cannot see, so fail closed
    # rather than pick the convenient one.
    #
    # A SET check, not a ladder of pairs. This was a pairwise ladder while a
    # third evidence source existed, and it silently skipped one of the three
    # pairs — a blank journal, which `write_state` can leave behind if
    # interrupted, short-circuited both guards and let a real disagreement
    # through. Counting distinct values cannot omit a pair, and stays correct
    # if a source is ever added back.
    # Word splitting is the point: OWNER_EVIDENCE is a space-separated pid list
    # and each pid must become its own line before `sort -u`. Quoting it, as
    # SC2086 suggests, would count one line and never detect a conflict.
    # shellcheck disable=SC2086
    DISTINCT_OWNERS=$(printf '%s\n' $OWNER_EVIDENCE | sort -u | grep -c .)
    if [ "${DISTINCT_OWNERS:-0}" -gt 1 ]; then
        refuse "Conflicting ownership evidence —$OWNER_EVIDENCE name different owners"
        [ -n "$STATE_OWNER_PID" ] && note "Journal: pid $STATE_OWNER_PID"
        [ -n "$WT_LOCK_PID" ] && note "Lock:    pid $WT_LOCK_PID"
        note "Resolve which session owns this checkout before removing it"
        exit 1
    fi
    if [ "$WT_LOCKED" -eq 1 ] && [ -z "$OWNER_EVIDENCE" ]; then
        # Locked, but nothing names an owner — degrade to alive (safe direction).
        refuse "Locked worktree with unparseable lock reason — cannot verify owner liveness"
        note "Lock reason: $WT_LOCK_REASON"
        note "Use --force to skip PID check"
        exit 1
    fi
    if [ -n "$OWNER_EVIDENCE" ] && [ -z "$LIVE_OWNER" ]; then
        note "Recorded owner(s)$OWNER_EVIDENCE proved dead — proceeding"
    fi
fi

# --- default-branch candidates (shared by pre-checks 5 and 5b) ---------------
#
# TWO DISTINCT PROPERTIES, AND CONFLATING THEM IS THE DEFECT THIS SOLVES.
#   DURABILITY   = the commits exist somewhere other than this disk (pre-check 5)
#   COMPLETENESS = the commits reached the branch everyone else reads (pre-check 5b)
# Neither implies the other. `start-worktree` step 4c publishes every branch AT
# CREATION to reserve the name, so DURABILITY is satisfied from birth for every
# worktree this skill makes — which made pre-check 5 alone a check that could never
# fail for the workflow it was guarding. Reproduced 2026-08-14: a branch pushed to
# `origin/wt/demo` and never merged was removed with rc=0 and its local branch
# deleted, leaving the work reachable only from a remote ref nobody tracks.
# That is the proxy-substitution class: a cheap observable reported AS the
# expensive property.
#
# RESOLVE ONE DEFAULT BRANCH NAME, THEN ACCEPT ONLY ITS OWN TWO REFS.
# An earlier version of this block collected `origin/HEAD, origin/main,
# origin/master, main, master` as five independent candidates and returned "landed"
# on the FIRST match. That conflates "names a default branch might have" with "refs
# whose contents count as landed". Reproduced 2026-08-14: in a repo whose real
# default is `develop` and which still carries a legacy `master`, a branch whose
# work existed ONLY in `master` was reported landed and removed with its local
# branch deleted. Resolve the NAME once; the local and remote forms of THAT name
# are the only things that count.
#
# Both forms count for COMPLETENESS on purpose: a solo flow that merges into
# local `main` and has not pushed yet is genuinely landed, and refusing there
# would be a false alarm — a check that cries wolf gets bypassed (T-169).
# DURABILITY is stricter: its content-equivalence fallback accepts refreshed
# remote refs only. A local-only default branch is still on this disk.
#
# Refresh every configured remote before asking either question. Cached
# Cached remote-tracking refs are not durability evidence: another clone may
# have rewritten or deleted a branch while this checkout retains the old ref.
# Refresh every configured remote's complete head namespace, then compare only
# against the captured live-ref set. Unknown freshness must fail closed.
REMOTE_NAMES=$(git remote 2>/dev/null) || {
    refuse "Could not enumerate remotes — commit durability is unknown"
    exit 1
}
if [ -z "$REMOTE_NAMES" ]; then
    refuse "No remote is configured — commit durability cannot be established"
    exit 1
fi
LIVE_REMOTE_REFS=""
while IFS= read -r _remote; do
    [ -n "$_remote" ] || continue
    # Override configured fetch refspecs for this safety check. Otherwise a
    # narrow refspec can leave deleted topic refs cached under refs/remotes.
    # The old global `--remotes` reachability query mistook that cache for a
    # live off-disk copy. This mapping refreshes and prunes every branch before
    # the captured live-ref set is built.
    if ! git fetch --no-tags --prune "$_remote" \
        "+refs/heads/*:refs/remotes/$_remote/*"; then
        refuse "Could not refresh remote '$_remote' — refusing destructive cleanup on stale evidence"
        exit 1
    fi
    _live_refs=$(git for-each-ref --format='%(refname)' "refs/remotes/$_remote/") || {
        refuse "Could not enumerate refreshed refs for '$_remote' — commit durability is unknown"
        exit 1
    }
    while IFS= read -r _live_ref; do
        [ -n "$_live_ref" ] || continue
        LIVE_REMOTE_REFS="${LIVE_REMOTE_REFS}${LIVE_REMOTE_REFS:+ }$_live_ref"
    done <<EOF
$_live_refs
EOF
done <<EOF
$REMOTE_NAMES
EOF

[ -n "$DEFAULT_NAME" ] || DEFAULT_NAME="$STATE_DEFAULT"
if [ -z "$DEFAULT_NAME" ]; then
    DEFAULT_NAME=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
fi
if [ -z "$DEFAULT_NAME" ]; then
    # No origin/HEAD (never set, or no remote). Fall back only to the two
    # conventional names, and only if such a ref actually exists.
    for _c in main master; do
        if git rev-parse --verify --quiet "origin/$_c" >/dev/null 2>&1 \
           || git rev-parse --verify --quiet "$_c" >/dev/null 2>&1; then
            DEFAULT_NAME="$_c"; break
        fi
    done
fi
DEFAULT_REFS=""
REMOTE_DEFAULT_REFS=""
_add_ref() { git rev-parse --verify --quiet "$1" >/dev/null 2>&1 && DEFAULT_REFS="${DEFAULT_REFS}${DEFAULT_REFS:+ }$1"; }
_add_remote_ref() { git rev-parse --verify --quiet "$1" >/dev/null 2>&1 && REMOTE_DEFAULT_REFS="${REMOTE_DEFAULT_REFS}${REMOTE_DEFAULT_REFS:+ }$1"; }
if [ -n "$DEFAULT_NAME" ]; then
    while IFS= read -r _remote; do
        [ -n "$_remote" ] || continue
        # Fully qualified names prevent a local branch such as `backup/main`
        # from masquerading as a missing remote-tracking ref.
        _add_remote_ref "refs/remotes/$_remote/$DEFAULT_NAME"
    done <<EOF
$REMOTE_NAMES
EOF
    _add_ref "refs/remotes/origin/$DEFAULT_NAME"
    _add_ref "refs/heads/$DEFAULT_NAME"
fi

# --- pre-check 4b: never delete the default branch itself -------------------
# A secondary worktree can sit ON the default branch. `landed_in` then trivially
# succeeds (`main..main` is empty), every other check passes, and the script
# reached `git branch -D main`. Reproduced 2026-08-14: local `main` was deleted.
# `git worktree remove` only protects the PRIMARY worktree, so nothing upstream
# of here catches it.
if [ -n "$DEFAULT_NAME" ] && [ "$WT_BRANCH" = "$DEFAULT_NAME" ]; then
    refuse "$WT_BRANCH is this repository's default branch — refusing to delete it"
    say "       Remove the worktree by hand if that is really what you want:"
    say "       git worktree remove $TARGET_RESOLVED"
    exit 1
fi

# `landed_in <ref>`: 0 when nothing on the branch is missing from <ref>, either by
# ancestry or by content. The content arm is what makes squash- and rebase-merges
# pass — their SHAs differ from anything on the branch, so ancestry alone would
# report perfectly-landed work as unmerged.
landed_in() {
    local ref="$1" n
    n=$(git rev-list --count "$ref..$WT_BRANCH" 2>/dev/null) || return 1
    [ "${n:-1}" = "0" ] && return 0
    git diff --quiet "$ref" "$WT_BRANCH" 2>/dev/null && return 0
    return 1
}

# --- pre-check 5: DURABILITY — all commits represented on a remote ----------
if [ -n "$LIVE_REMOTE_REFS" ]; then
    # Word splitting is intentional: ref names cannot contain whitespace.
    # shellcheck disable=SC2086
    if ! UNPUSHED=$(git log --oneline "$WT_BRANCH" --not $LIVE_REMOTE_REFS -- 2>/dev/null); then
        refuse "Could not compare $WT_BRANCH with refreshed remote refs — commit durability is unknown"
        exit 1
    fi
else
    if ! UNPUSHED=$(git log --oneline "$WT_BRANCH" -- 2>/dev/null); then
        refuse "Could not inspect $WT_BRANCH — commit durability is unknown"
        exit 1
    fi
fi
if [ -n "$UNPUSHED" ]; then
    COMMIT_COUNT=$(echo "$UNPUSHED" | wc -l | tr -d ' ')
    # Content-equivalence fallback: unreachable SHAs are harmless only when the
    # content already exists on a freshly fetched REMOTE default ref. A matching
    # local default branch is completeness evidence, not off-disk durability.
    SQUASHED=""
    for _ref in $REMOTE_DEFAULT_REFS; do
        if git diff --quiet "$_ref" "$WT_BRANCH" 2>/dev/null; then SQUASHED="$_ref"; break; fi
    done
    if [ -n "$SQUASHED" ]; then
        note "Commits not reachable from remotes, but content is identical to $SQUASHED (squash-merged)"
    else
        if [ -z "$REMOTE_DEFAULT_REFS" ]; then
            refuse "$COMMIT_COUNT commit(s) on $WT_BRANCH not represented on any remote"
        else
            refuse "$COMMIT_COUNT commit(s) on $WT_BRANCH not represented on any remote (content differs from the remote default branch)"
        fi
        say "$UNPUSHED"
        # DELIBERATELY does not offer --allow-unmerged: that flag skips the
        # COMPLETENESS check, never this one, and nothing bypasses this one. These
        # commits exist on exactly one disk, so removing the worktree and deleting
        # the branch would destroy them outright — that is a different failure from
        # stranding landed-but-unmerged work. A refusal must name a remedy that
        # actually works (test_refusal_names_the_escape_hatch pins the sibling case).
        say "       These commits exist ONLY here. Push the branch first:"
        say "         git -C $TARGET_RESOLVED push -u origin $WT_BRANCH"
        say "       If you deleted the remote branch already, re-push it before cleaning up."
        exit 1
    fi
fi

# --- pre-check 5b: COMPLETENESS — the work actually landed ------------------
if [ "$ALLOW_UNMERGED" -eq 1 ]; then
    note "Completeness check SKIPPED (--allow-unmerged) — removing regardless of merge state"
elif [ -z "$DEFAULT_REFS" ]; then
    # An unrun check is not a passed check (this skill's own stated rule). No
    # resolvable default branch means merge state is UNKNOWN, not fine.
    refuse "Could not resolve a default branch (tried origin/HEAD, then origin/main and origin/master) — cannot verify $WT_BRANCH landed"
    say "       Re-run with --allow-unmerged if you are deliberately discarding this work."
    exit 1
else
    LANDED=""
    for _ref in $DEFAULT_REFS; do
        if landed_in "$_ref"; then LANDED="$_ref"; break; fi
    done
    if [ -z "$LANDED" ]; then
        CMP_REF=${DEFAULT_REFS%% *}
        AHEAD=$(git rev-list --count "$CMP_REF..$WT_BRANCH" 2>/dev/null || echo "?")
        refuse "$AHEAD commit(s) on $WT_BRANCH have NOT landed in $CMP_REF — removing now strands the work on its remote branch with no local trace"
        git log --oneline "$CMP_REF..$WT_BRANCH" 2>/dev/null | head -20
        # Fetch is named FIRST because in a multi-session fleet the commonest way to
        # reach this refusal is a stale local view — a sibling landed the work, or a
        # PR merged on the host — not genuinely unmerged work. Reaching for
        # --allow-unmerged in that state makes the flag mean "I gave up checking",
        # which is exactly what it must not come to mean.
        say "       If a sibling session or a PR already landed this, your view is stale:"
        say "         git fetch origin   # then re-run"
        say "       Otherwise merge it (see the completion sequence's Branch Completion),"
        say "       or re-run with --allow-unmerged if you are deliberately discarding it."
        exit 1
    fi
    note "Work has landed in $LANDED"
fi

# --- pre-check 6: clean working tree ---------------------------------------
DIRTY=$(git -C "$TARGET_RESOLVED" status --porcelain 2>/dev/null)
DIRTY_RC=$?
if [ "$DIRTY_RC" -ne 0 ]; then
    refuse "Could not check working tree status (git status failed) — treating as dirty"
    exit 1
fi
if [ -n "$DIRTY" ]; then
    DIRTY_COUNT=$(echo "$DIRTY" | wc -l | tr -d ' ')
    refuse "Working tree has $DIRTY_COUNT uncommitted file(s)"
    say "$DIRTY"
    exit 1
fi

# --- pre-check 6b: irreplaceable IGNORED files ------------------------------
#
# `git status --porcelain` does NOT list ignored files, so pre-check 6 calls a
# worktree "clean" while it still holds everything .gitignore covers — and
# `git worktree remove` then deletes the directory outright. Reproduced
# 2026-08-14: a worktree holding a `.env` with a live-looking key was removed with
# rc=0 under the word "clean". Ignored files are the one class that exists on
# exactly one disk BY DESIGN, which makes this the sharpest work-destruction path
# in the script.
#
# Blanket-refusing on any ignored file would fire on every worktree carrying a
# venv or __pycache__ — constant false alarms, and a check that cries wolf gets
# bypassed (T-169). So: NOTE the regenerable bulk, REFUSE on a small high-signal
# list of names that are almost never regenerable.
#
# THIS LIST IS A HEURISTIC AND IS NOT A GUARANTEE. It is a name match, not a
# content scan — it will miss a secret in a file called `notes.txt`. It buys the
# common case cheaply; it does not make removal safe in general. Said plainly here
# because an unstated proxy reported as a guarantee is this codebase's recurring
# defect.
_read_ignored_files() {
    local ignored_raw _p _base
    ignored_raw=$(git -C "$TARGET_RESOLVED" clean -ndX 2>/dev/null) || return 1
    IGNORED=$(printf '%s\n' "$ignored_raw" | sed 's|^Would remove ||')
    SENSITIVE=""
    while IFS= read -r _p; do
        [ -z "$_p" ] && continue
        _base=$(basename "${_p%/}")
        case "$_base" in
            .env|.env.*|*.pem|*.key|*.p12|*.pfx|*.keystore|*.jks|id_rsa*|id_ecdsa*|id_ed25519*|credentials|credentials.*|secrets|secrets.*|.netrc|.npmrc|.pypirc)
                SENSITIVE="${SENSITIVE}${SENSITIVE:+
}$_p"
                ;;
        esac
    done <<EOF
$IGNORED
EOF
}

if ! _read_ignored_files; then
    refuse "Could not inspect ignored files — removal safety is unknown"
    exit 1
fi
if [ -n "$IGNORED" ]; then
    IGNORED_COUNT=$(printf '%s\n' "$IGNORED" | grep -c . || true)
    if [ -n "$SENSITIVE" ] && [ "$ALLOW_IGNORED" -eq 0 ]; then
        refuse "Ignored file(s) here look irreplaceable — removing this worktree DELETES them"
        printf '%s\n' "$SENSITIVE" | sed 's|^|         |'
        say "       These are invisible to \`git status\`, so \"clean\" above did not cover them."
        say "       Move or copy them out, then re-run — or pass --allow-ignored to delete them."
        exit 1
    fi
    note "$IGNORED_COUNT ignored file(s)/dir(s) will be deleted with the worktree (build artifacts, caches, venvs)"
fi

_read_current_target_record() {
    local snapshot line path resolved in_target=0
    snapshot=$(git worktree list --porcelain 2>/dev/null) || return 1
    CHECK_FOUND=0
    CHECK_BRANCH=""
    CHECK_LOCKED=0
    CHECK_LOCK_REASON=""
    CHECK_DETACHED=0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            "worktree "*)
                path="${line#worktree }"
                resolved=$(realpath "$path" 2>/dev/null || echo "$path")
                if [ "$resolved" = "$TARGET_RESOLVED" ]; then
                    in_target=1
                    CHECK_FOUND=1
                else
                    in_target=0
                fi
                ;;
            "branch "*) [ "$in_target" -eq 1 ] && CHECK_BRANCH="${line#branch refs/heads/}" ;;
            detached) [ "$in_target" -eq 1 ] && CHECK_DETACHED=1 ;;
            locked*)
                if [ "$in_target" -eq 1 ]; then
                    CHECK_LOCKED=1
                    CHECK_LOCK_REASON="${line#locked}"
                    CHECK_LOCK_REASON="${CHECK_LOCK_REASON# }"
                fi
                ;;
            "") [ "$in_target" -eq 1 ] && break ;;
        esac
    done <<< "$snapshot"
    return 0
}

_restore_deletion_guard() {
    [ "$WT_LOCKED" -eq 1 ] || return 0
    if _read_current_target_record && [ "$CHECK_LOCKED" -eq 1 ]; then
        # A concurrent actor may have installed a different lock. It still
        # protects the checkout; never overwrite another owner's evidence.
        if [ "$CHECK_LOCK_REASON" != "$WT_LOCK_REASON" ]; then
            note "Cleanup stopped with a different Git lock in place; left it untouched"
        fi
        return 0
    fi
    if git worktree lock --reason "$WT_LOCK_REASON" "$TARGET_RESOLVED" 2>/dev/null; then
        note "Restored the original worktree lock"
        return 0
    fi
    return 1
}

_final_pre_remove_check() {
    local current_hash current_head current_status
    if [ -n "$STATE_FILE_HASH_INITIAL" ]; then
        [ -f "$STATE_FILE" ] || { refuse "Lifecycle journal disappeared during teardown"; return 1; }
        current_hash=$(git hash-object "$STATE_FILE" 2>/dev/null) || {
            refuse "Could not re-read lifecycle journal after teardown"; return 1; }
        [ "$current_hash" = "$STATE_FILE_HASH_INITIAL" ] || {
            refuse "Lifecycle journal changed during teardown"; return 1; }
        if [ "$STATE_VERSION" = "2" ]; then
            if ! _parse_v2_state || ! _validate_v2_coherence; then
                refuse "Lifecycle journal no longer coheres with Git: $STATE_PARSE_ERROR"
                return 1
            fi
        fi
    fi
    _read_current_target_record || {
        refuse "Could not re-read Git worktree registration after teardown"; return 1; }
    [ "$CHECK_FOUND" -eq 1 ] || { refuse "Worktree registration disappeared during teardown"; return 1; }
    [ "$CHECK_DETACHED" -eq 0 ] && [ "$CHECK_BRANCH" = "$WT_BRANCH" ] || {
        refuse "Worktree branch changed during teardown"; return 1; }
    [ "$CHECK_LOCKED" -eq "$WT_LOCKED" ] || {
        refuse "Worktree lock state changed during teardown"; return 1; }
    if [ "$WT_LOCKED" -eq 1 ] && [ "$CHECK_LOCK_REASON" != "$WT_LOCK_REASON" ]; then
        refuse "Worktree lock owner changed during teardown"
        return 1
    fi
    current_head=$(git -C "$TARGET_RESOLVED" rev-parse HEAD 2>/dev/null) || {
        refuse "Could not re-read worktree HEAD after teardown"; return 1; }
    [ "$current_head" = "$PRE_REMOVE_HEAD" ] || {
        refuse "Worktree HEAD changed during teardown"; return 1; }
    current_status=$(git -C "$TARGET_RESOLVED" status --porcelain 2>/dev/null) || {
        refuse "Could not re-check working tree after teardown"; return 1; }
    [ -z "$current_status" ] || {
        refuse "Working tree changed during teardown"; return 1; }
    _read_ignored_files || {
        refuse "Could not re-check ignored files after teardown"; return 1; }
    if [ -n "$SENSITIVE" ] && [ "$ALLOW_IGNORED" -eq 0 ]; then
        refuse "Sensitive ignored files appeared during teardown"
        printf '%s\n' "$SENSITIVE" | sed 's|^|         |'
        return 1
    fi
    return 0
}

# --- all checks passed — perform cleanup ------------------------------------
if [ "$DRY_RUN" -eq 1 ]; then
    ok "Dry run — would remove worktree at $TARGET_RESOLVED"
    if [ "$WT_LOCKED" -eq 1 ]; then
        note "Would unlock worktree first"
    fi
    note "Would run: git worktree remove $TARGET_RESOLVED"
    note "Would run: git branch -D $WT_BRANCH"
    exit 0
fi

PRE_REMOVE_HEAD=$(git -C "$TARGET_RESOLVED" rev-parse HEAD 2>/dev/null) || {
    refuse "Could not snapshot worktree HEAD before teardown"
    exit 1
}

if ! run_teardown_hook; then
    refuse "runtime teardown failed; worktree remains locked and intact"
    _restore_deletion_guard || say "ERROR: teardown failed and the original lock could not be restored"
    exit 1
fi

# The proofs above can go stale while an arbitrary project teardown hook runs.
# Re-check every mutable local fact after that hook and immediately before the
# unlock/remove pair. Remote durability and landing were already proven and do
# not become less safe if their refs move after the target HEAD is frozen here.
if ! _final_pre_remove_check; then
    _restore_deletion_guard || say "ERROR: final validation failed and the original lock could not be restored"
    exit 1
fi

# Unlock if locked
if [ "$WT_LOCKED" -eq 1 ]; then
    if ! git worktree unlock "$TARGET_RESOLVED" 2>/dev/null; then
        say "ERROR: could not unlock worktree"
        _restore_deletion_guard || say "ERROR: the original lock could not be restored"
        exit 2
    fi
fi

# Remove worktree
if ! git worktree remove "$TARGET_RESOLVED" 2>/dev/null; then
    if ! _restore_deletion_guard; then
        say "ERROR: removal failed and the original lock could not be restored"
        exit 2
    fi
    say "ERROR: git worktree remove failed"
    exit 2
fi

# Delete branch
if ! git branch -D "$WT_BRANCH" 2>/dev/null; then
    say "ERROR: worktree removed but branch $WT_BRANCH could not be deleted"
    say "       The checkout is gone; the branch remains recoverable. Delete it after resolving the Git error."
    exit 2
fi

ok "Removed worktree $TARGET_RESOLVED (branch $WT_BRANCH)"
exit 0
