#!/usr/bin/env bash
# Deterministic, resumable worktree preparation for concurrent AI sessions.
#
# Framework-owned checkouts (Claude Code and Codex CLI) are created, published,
# locked, and runtime-initialized here. Codex Desktop creates its own detached
# checkout; this script only attaches/publishes a branch and initializes runtime.
# Every completed transition is recorded in the linked worktree's gitdir so a
# failed push, lock, or setup hook can be retried without recreating anything.
#
# Exit codes: 0 ready; 1 blocked by known state; 2 undetermined/partial/error.

set -uo pipefail

export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -oBatchMode=yes -oConnectTimeout=10}"

say()   { printf '%s\n' "$*"; }
ok()    { printf 'ok     %s\n' "$*"; }
note()  { printf 'note   %s\n' "$*"; }
block() { printf 'BLOCK  %s\n' "$*"; }
undet() { printf '?????  %s\n' "$*"; }

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

usage() {
  cat <<'EOF'
Usage:
  prepare.sh claude-create --slug <slug> --base <ref> --default-ref <name> --owner-pid <pid> [--task-key <key>] [--allow-parallel-task]
  prepare.sh codex-cli-create --slug <slug> --base <ref> --default-ref <name> --owner-pid <pid> [--session-id <id>] [--task-key <key>] [--allow-parallel-task]
  prepare.sh continue --path <path> [--owner-pid <pid>] [--task-key <key>] [--allow-parallel-task]
  prepare.sh claude-resume --path <path> --owner-pid <pid>
  prepare.sh codex-cli-validate [--path <path>] --owner-pid <pid>
  prepare.sh codex-desktop-adopt --slug <slug> --default-ref <name>
  prepare.sh status [--path <path>]

Common options:
  --branch <wt/name>     Exact branch instead of generated wt/<slug>-<nonce>
  --path <path>          Exact worktree path
  --nonce <text>         Deterministic suffix (tests/reproduction)
  --task-key <key>       Logical task identity (default: slug:<slug>)
  --allow-parallel-task  Explicitly permit another checkout for --task-key
  --allow-local-only     Permit ready state when the repository has no origin

Creation never rolls back automatically. A failed transition preserves the
checkout and prints a `continue` command. `claude-resume` is only for reclaiming
a previously ready Claude checkout whose recorded owner is no longer live.
EOF
}

MODE="${1:-}"
[ -n "$MODE" ] || { usage; exit 2; }
shift || true

SLUG=""
BASE=""
BASE_SHA=""
DEFAULT_REF=""
OWNER_PID=""
TARGET=""
BRANCH=""
NONCE="${AI_WORKTREE_NONCE:-}"
SESSION_ID=""
REQUESTED_TASK_KEY=""
TASK_KEY=""
TASK_KEY_EXPLICIT=0
ALLOW_PARALLEL_TASK=0
PARALLEL_TASK=0
ALLOW_LOCAL_ONLY=0
HOST=""
LIFECYCLE_OWNER=""
RECORDED_PATH=""
RECORDED_PID=""
RECORDED_VERSION=""
# Public source marker consumed by cross-consumer schema parity tests.
# shellcheck disable=SC2034
JOURNAL_V2_KEYS="version host lifecycle_owner path branch base_sha default_ref owner_pid session_id task_key parallel_task state updated_at"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --slug) [ "$#" -ge 2 ] || { usage; exit 2; }; SLUG="$2"; shift 2 ;;
    --base) [ "$#" -ge 2 ] || { usage; exit 2; }; BASE="$2"; shift 2 ;;
    --default-ref) [ "$#" -ge 2 ] || { usage; exit 2; }; DEFAULT_REF="$2"; shift 2 ;;
    --owner-pid) [ "$#" -ge 2 ] || { usage; exit 2; }; OWNER_PID="$2"; shift 2 ;;
    --path) [ "$#" -ge 2 ] || { usage; exit 2; }; TARGET="$2"; shift 2 ;;
    --branch) [ "$#" -ge 2 ] || { usage; exit 2; }; BRANCH="$2"; shift 2 ;;
    --nonce) [ "$#" -ge 2 ] || { usage; exit 2; }; NONCE="$2"; shift 2 ;;
    --session-id) [ "$#" -ge 2 ] || { usage; exit 2; }; SESSION_ID="$2"; shift 2 ;;
    --task-key) [ "$#" -ge 2 ] || { usage; exit 2; }; REQUESTED_TASK_KEY="$2"; TASK_KEY_EXPLICIT=1; shift 2 ;;
    --allow-parallel-task) ALLOW_PARALLEL_TASK=1; shift ;;
    --allow-local-only) ALLOW_LOCAL_ONLY=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) say "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

command -v git >/dev/null 2>&1 || { say "FATAL: git not found"; exit 2; }
ACTING="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  say "FATAL: not inside a Git repository"; exit 2; }
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" || exit 2
case "$COMMON" in /*) : ;; *) COMMON="$ACTING/$COMMON" ;; esac
PRIMARY="$(cd "$COMMON/.." 2>/dev/null && pwd -P)" || {
  say "FATAL: cannot resolve primary checkout from $COMMON"; exit 2; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PREFLIGHT="$SCRIPT_DIR/preflight.sh"

absolute_path() {
  local value="$1" parent base
  case "$value" in /*) : ;; *) value="$PRIMARY/$value" ;; esac
  if [ -d "$value" ]; then (cd "$value" && pwd -P); return; fi
  parent="$(dirname "$value")"; base="$(basename "$value")"
  if [ -d "$parent" ]; then printf '%s/%s\n' "$(cd "$parent" && pwd -P)" "$base"; else printf '%s\n' "$value"; fi
}

gitdir_for() {
  local path="$1" gd
  gd="$(git -C "$path" rev-parse --git-dir 2>/dev/null)" || return 1
  case "$gd" in /*) printf '%s\n' "$gd" ;; *) printf '%s/%s\n' "$path" "$gd" ;; esac
}

state_file_for() { local gd; gd="$(gitdir_for "$1")" || return 1; printf '%s/ai-worktree-state\n' "$gd"; }
read_state() {
  local path="$1" key="$2" sf
  sf="$(state_file_for "$path")" || return 1
  [ -f "$sf" ] || return 1
  awk -v wanted="$key" 'index($0, wanted "=") == 1 { print substr($0, length(wanted) + 2); exit }' "$sf"
}

validate_task_key() {
  # LC_ALL=C, because `case` glob RANGES ARE LOCALE-SENSITIVE. Under en_US.UTF-8
  # `[a-z0-9]` matches uppercase, so `--task-key Upper` walked straight through
  # this validator and the worktree was created before anything complained;
  # `tests/test_prepare_worktree.py::test_create_rejects_invalid_task_keys[Upper]`
  # fails without this and passes with it. Measured on this machine: default
  # locale ACCEPTS `Upper`, LC_ALL=C REJECTS it, and both still accept `lower`,
  # `slug:demo`, `a.b_c`, `x1/y-2`.
  #
  # `validate_v2_state_file` below already runs `LC_ALL=C awk` for the same
  # reason, so the hazard was known in this file — just not applied here.
  local LC_ALL=C
  local value="$1"
  [ "${#value}" -le 128 ] || { say "ERROR: task key must be at most 128 characters"; return 2; }
  case "$value" in
    ""|[!a-z0-9]*|*[!a-z0-9._:/-]*)
      say "ERROR: task key must match [a-z0-9][a-z0-9._:/-]*"
      return 2
      ;;
  esac
}

validate_v2_state_file() {
  local sf="$1"
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
  ' "$sf"
}

legacy_task_from_branch() {
  local value="$1"
  if [[ "$value" =~ ^wt/(.+)-[0-9a-f]{8}$ ]]; then
    printf 'slug:%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

write_state() {
  local path="$1" state="$2" sf tmp
  sf="$(state_file_for "$path")" || return 1
  validate_task_key "$TASK_KEY" >/dev/null || {
    undet "cannot write v2 lifecycle state without a valid task key"
    return 2
  }
  tmp="${sf}.tmp.$$"
  # Subshell, because `umask` is PROCESS state and `{ ... }` is not a subshell.
  # Unscoped, it leaked out of this function into everything that ran after it —
  # including `run_hook setup`, so every venv, cache and build artifact a
  # project's setup hook created came out 0700/0600 and unreadable by any other
  # uid. Invisible until the day it matters.
  (
  umask 077
  {
    printf 'version=2\n'
    printf 'host=%s\n' "$HOST"
    printf 'lifecycle_owner=%s\n' "$LIFECYCLE_OWNER"
    printf 'path=%s\n' "$path"
    printf 'branch=%s\n' "$BRANCH"
    printf 'base_sha=%s\n' "$BASE_SHA"
    printf 'default_ref=%s\n' "$DEFAULT_REF"
    printf 'owner_pid=%s\n' "$OWNER_PID"
    printf 'session_id=%s\n' "$SESSION_ID"
    printf 'task_key=%s\n' "$TASK_KEY"
    printf 'parallel_task=%s\n' "$PARALLEL_TASK"
    printf 'state=%s\n' "$state"
    printf 'updated_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >"$tmp"
  ) || return 1
  if ! validate_v2_state_file "$tmp"; then
    rm -f "$tmp"
    undet "refusing to persist lifecycle values that violate the v2 journal schema"
    return 2
  fi
  mv "$tmp" "$sf"
}

load_state() {
  local path="$1" sf version legacy_task
  sf="$(state_file_for "$path")" || return 1
  [ -f "$sf" ] || return 1
  version="$(read_state "$path" version 2>/dev/null || true)"
  RECORDED_VERSION="$version"
  case "$version" in
    2)
      validate_v2_state_file "$sf" || return 2
      ;;
    1)
      # Version 1 predates task identity. It remains readable, but a task key is
      # inferred only from the exact branch form the generator produced: an
      # eight-lowercase-hex nonce. Anything else stays unknown.
      ;;
    *) return 2 ;;
  esac
  HOST="$(read_state "$path" host 2>/dev/null || true)"
  LIFECYCLE_OWNER="$(read_state "$path" lifecycle_owner 2>/dev/null || true)"
  BRANCH="$(read_state "$path" branch 2>/dev/null || true)"
  BASE_SHA="$(read_state "$path" base_sha 2>/dev/null || true)"
  DEFAULT_REF="$(read_state "$path" default_ref 2>/dev/null || true)"
  RECORDED_PATH="$(read_state "$path" path 2>/dev/null || true)"
  RECORDED_PID="$(read_state "$path" owner_pid 2>/dev/null || true)"
  SESSION_ID="$(read_state "$path" session_id 2>/dev/null || true)"
  if [ "$version" = "2" ]; then
    TASK_KEY="$(read_state "$path" task_key 2>/dev/null || true)"
    PARALLEL_TASK="$(read_state "$path" parallel_task 2>/dev/null || true)"
  else
    legacy_task="$(legacy_task_from_branch "$BRANCH" 2>/dev/null || true)"
    TASK_KEY="$legacy_task"
    PARALLEL_TASK=0
  fi
  git check-ref-format --branch "$DEFAULT_REF" >/dev/null 2>&1 || return 2
  [ -n "$HOST" ] && [ -n "$LIFECYCLE_OWNER" ] && [ -n "$RECORDED_PATH" ] \
    && [ -n "$BRANCH" ] && [ -n "$BASE_SHA" ]
}

run_hook() {
  local phase="$1" path="$2" hook
  hook="$path/.ai-worktree/${phase}.sh"
  [ -f "$hook" ] || return 0
  note "Running optional runtime hook: .ai-worktree/${phase}.sh"
  AI_WORKTREE_ID="${BRANCH#wt/}" \
  AI_WORKTREE_HOST="$HOST" \
  AI_WORKTREE_PATH="$path" \
  AI_WORKTREE_PRIMARY="$PRIMARY" \
  AI_WORKTREE_BRANCH="$BRANCH" \
  AI_WORKTREE_DEFAULT_REF="$DEFAULT_REF" \
    bash "$hook"
}

generate_branch() {
  [ -n "$BRANCH" ] && return 0
  [ -n "$SLUG" ] || { say "ERROR: --slug is required"; return 2; }
  case "$SLUG" in *[!a-z0-9-]*|""|-*|*-) say "ERROR: slug must use lowercase letters, digits, and internal hyphens"; return 2 ;; esac
  if [ -z "$NONCE" ]; then
    NONCE="$(printf '%s' "$PRIMARY|$SLUG|$(date -u +%Y%m%dT%H%M%S)|$$|${RANDOM:-0}" | git hash-object --stdin | cut -c1-8)"
  fi
  case "$NONCE" in ""|*[!A-Za-z0-9-]*) say "ERROR: nonce contains characters unsafe for a branch"; return 2 ;; esac
  BRANCH="wt/$SLUG-$NONCE"
}

validate_owner_pid() {
  case "$OWNER_PID" in ""|*[!0-9]*) say "ERROR: --owner-pid must be a positive integer"; return 2 ;; esac
  [ "$OWNER_PID" -gt 1 ] 2>/dev/null || { say "ERROR: --owner-pid must be greater than 1"; return 2; }
}

registered_block() {
  local path="$1" normalized
  normalized="$(absolute_path "$path")"
  git worktree list --porcelain 2>/dev/null | awk -v want="$normalized" '
    /^worktree / { in_block=($0 == "worktree " want) }
    in_block { print }
    in_block && /^$/ { exit }
  '
}

task_state_is_active() {
  case "$1" in
    attached|created|published|locked|ready|setup-failed|task-conflict) return 0 ;;
    *) return 1 ;;
  esac
}

# Populate INSPECT_KIND (match, ambiguous, none) for one registered worktree.
# Version 2 is authoritative only when its complete ordered schema validates.
# Version 1 can identify a task only when its branch ends in the generator's
# eight-lowercase-hex nonce. A same-slug noncanonical legacy branch is not
# guessed: it is ambiguity that a sequential creation must resolve first.
inspect_task_path() {
  local path="$1" wanted="$2" sf version branch task state raw_count slug
  local lifecycle recorded_path recorded_branch base default owner parallel block_text
  INSPECT_KIND=none; INSPECT_STATE=""; INSPECT_DETAIL=""
  sf="$(state_file_for "$path" 2>/dev/null || true)"
  branch="$(git -C "$path" branch --show-current 2>/dev/null || true)"
  if [ -n "$sf" ] && [ -f "$sf" ]; then
    version="$(awk -F= '$1 == "version" { print substr($0, 9); exit }' "$sf")"
    if [ "$version" = "2" ]; then
      if validate_v2_state_file "$sf"; then
        task="$(awk -F= '$1 == "task_key" { print substr($0, 10); exit }' "$sf")"
        state="$(awk -F= '$1 == "state" { print substr($0, 7); exit }' "$sf")"
        if [ "$task" = "$wanted" ] && task_state_is_active "$state"; then
          lifecycle="$(awk -F= '$1 == "lifecycle_owner" { print substr($0, 17); exit }' "$sf")"
          recorded_path="$(awk -F= '$1 == "path" { print substr($0, 6); exit }' "$sf")"
          recorded_branch="$(awk -F= '$1 == "branch" { print substr($0, 8); exit }' "$sf")"
          base="$(awk -F= '$1 == "base_sha" { print substr($0, 10); exit }' "$sf")"
          default="$(awk -F= '$1 == "default_ref" { print substr($0, 13); exit }' "$sf")"
          owner="$(awk -F= '$1 == "owner_pid" { print substr($0, 11); exit }' "$sf")"
          parallel="$(awk -F= '$1 == "parallel_task" { print substr($0, 15); exit }' "$sf")"
          if [ "$recorded_path" != "$path" ]; then
            INSPECT_KIND=ambiguous
            INSPECT_DETAIL="v2 lifecycle record does not match its registered worktree"
          elif [ "$lifecycle" = "framework" ]; then
            if [ "$recorded_branch" != "$branch" ]; then
              INSPECT_KIND=ambiguous
              INSPECT_DETAIL="v2 lifecycle record does not match its registered worktree"
              return 0
            fi
            block_text="$(registered_block "$path")"
            lock_fields "$block_text"
            if [ "$LOCK_VERSION" != "2" ] || ! validate_v2_lock_reason \
              || [ "$LOCK_BRANCH" != "$branch" ] || [ "$LOCK_DEFAULT" != "$default" ] \
              || [ "$LOCK_BASE" != "$base" ] || [ "$LOCK_PID" != "$owner" ] \
              || [ "$LOCK_TASK" != "$task" ] || [ "$LOCK_PARALLEL" != "$parallel" ]; then
              INSPECT_KIND=ambiguous
              INSPECT_DETAIL="v2 lifecycle journal and Git lock are not coherent"
            else
              INSPECT_KIND=match; INSPECT_STATE="$state"
            fi
          elif [ -n "$branch" ] && [ "$recorded_branch" != "$branch" ]; then
            INSPECT_KIND=ambiguous
            INSPECT_DETAIL="v2 Desktop lifecycle record does not match its registered worktree"
          else
            INSPECT_KIND=match; INSPECT_STATE="$state"
          fi
        fi
        return 0
      fi
      raw_count="$(awk -v wanted="$wanted" '$0 == "task_key=" wanted { n++ } END { print n + 0 }' "$sf")"
      if [ "$raw_count" -gt 0 ]; then
        INSPECT_KIND=ambiguous
        INSPECT_DETAIL="malformed v2 lifecycle record names this task"
      fi
      return 0
    fi
    if [ "$version" = "1" ]; then
      task="$(legacy_task_from_branch "$branch" 2>/dev/null || true)"
      state="$(awk -F= '$1 == "state" { print substr($0, 7); exit }' "$sf")"
      if [ -n "$task" ] && [ "$task" = "$wanted" ] && task_state_is_active "$state"; then
        INSPECT_KIND=match; INSPECT_STATE="$state"
        return 0
      fi
    fi
  fi
  case "$wanted" in
    slug:*)
      slug="${wanted#slug:}"
      case "$branch" in
        "wt/$slug-"*)
          if ! legacy_task_from_branch "$branch" >/dev/null 2>&1; then
            INSPECT_KIND=ambiguous
            INSPECT_DETAIL="legacy same-slug branch has no recognizable generated nonce"
          fi
          ;;
      esac
      ;;
  esac
}

scan_task_collisions() {
  local LC_ALL=C phase="$1" line path normalized winner="" matches=0
  [ "$ALLOW_PARALLEL_TASK" -eq 0 ] || {
    note "Parallel task override recorded for '$TASK_KEY'"
    return 0
  }
  while IFS= read -r line; do
    case "$line" in
      worktree\ *)
        path="${line#worktree }"
        normalized="$(absolute_path "$path")"
        [ "$phase" != "pre" ] || [ "$normalized" != "$TARGET" ] || continue
        inspect_task_path "$normalized" "$TASK_KEY"
        case "$INSPECT_KIND" in
          ambiguous)
            undet "task '$TASK_KEY' is ambiguous at $normalized: $INSPECT_DETAIL"
            return 2
            ;;
          match)
            if [ "$phase" = "pre" ]; then
              block "task '$TASK_KEY' already has an active worktree at $normalized (state $INSPECT_STATE)"
              return 1
            fi
            matches=$((matches + 1))
            # Every contender computes the same winner from shared evidence;
            # path order is stable and independent of scan/arrival order.
            if [ -z "$winner" ] || [[ "$normalized" < "$winner" ]]; then winner="$normalized"; fi
            ;;
        esac
        ;;
    esac
  done < <(git worktree list --porcelain 2>/dev/null)
  if [ "$phase" = "post" ] && [ "$matches" -gt 1 ] && [ "$winner" != "$TARGET" ]; then
    write_state "$TARGET" task-conflict || return 2
    block "task '$TASK_KEY' raced with another creation; $winner won and this checkout is locked in state task-conflict"
    note "Recovery: continue with --allow-parallel-task only if duplicate implementation is intentional"
    return 1
  fi
}

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

lock_fields() {
  local block_text="$1"
  LOCK_REASON="$(printf '%s\n' "$block_text" | sed -n 's/^locked //p' | head -1)"
  case "$LOCK_REASON" in
    ai-worktree-v1\ *) LOCK_VERSION=1 ;;
    ai-worktree-v2\ *) LOCK_VERSION=2 ;;
    *) LOCK_VERSION="" ;;
  esac
  LOCK_HOST="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* host=\([^ ]*\).*/\1/p')"
  LOCK_BRANCH="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* branch=\([^ ]*\).*/\1/p')"
  LOCK_DEFAULT="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* default=\([^ ]*\).*/\1/p')"
  LOCK_BASE="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* base=\([^ ]*\).*/\1/p')"
  LOCK_TASK="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* task=\([^ ]*\).*/\1/p')"
  LOCK_PARALLEL="$(printf '%s\n' "$LOCK_REASON" | sed -n 's/.* parallel=\([^ ]*\).*/\1/p')"
  # Was a greedy sed that silently took the LAST pid token, which is the exact
  # first-vs-last divergence already fixed in the other three consumers — this
  # one was missed because the parity test did not cover prepare.sh. Every
  # LOCK_PID consumer below fails SAFE on an empty value: the state-less
  # recovery path requires it non-empty (undetermined), the live-owner check
  # treats empty as alive (refuses), and the Codex CLI path demands an exact
  # match (undetermined). So ambiguity refusing is strictly the right direction.
  LOCK_PID="$(_lock_reason_pid "$LOCK_REASON" || true)"
}

validate_v2_lock_reason() {
  local prefix stamp stamp_digits
  prefix="ai-worktree-v2 host=$LOCK_HOST lifecycle=framework branch=$LOCK_BRANCH default=$LOCK_DEFAULT base=$LOCK_BASE pid=$LOCK_PID task=$LOCK_TASK parallel=$LOCK_PARALLEL start="
  case "$LOCK_REASON" in "$prefix"*) : ;; *) return 1 ;; esac
  stamp="${LOCK_REASON#"$prefix"}"
  case "$stamp" in ????-??-??T??:??:??Z) : ;; *) return 1 ;; esac
  stamp_digits="$(printf '%s\n' "$stamp" | tr -d -- '-:TZ')"
  case "$stamp_digits" in ''|*[!0-9]*) return 1 ;; esac
}

framework_lock_reason() {
  printf 'ai-worktree-v2 host=%s lifecycle=framework branch=%s default=%s base=%s pid=%s task=%s parallel=%s start=%s\n' \
    "$HOST" "$BRANCH" "$DEFAULT_REF" "$BASE_SHA" "$OWNER_PID" "$TASK_KEY" "$PARALLEL_TASK" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

resolve_live_default() {
  local snapshot live_name live_sha
  snapshot="$(git ls-remote --symref origin HEAD "refs/heads/$DEFAULT_REF" 2>/dev/null)" || return 1
  live_name="$(printf '%s\n' "$snapshot" | sed -n 's#^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$#\1#p' | head -1)"
  live_sha="$(printf '%s\n' "$snapshot" | awk -v ref="refs/heads/$DEFAULT_REF" '$1 != "ref:" && $2 == ref {print $1; exit}')"
  [ "$live_name" = "$DEFAULT_REF" ] && [ -n "$live_sha" ] || return 1
  BASE_SHA="$live_sha"
}

recovery_hint() {
  if [ -n "$OWNER_PID" ]; then
    note "Recovery: bash '$SCRIPT_DIR/prepare.sh' continue --path '$TARGET' --owner-pid '$OWNER_PID'"
  else
    note "Recovery: bash '$SCRIPT_DIR/prepare.sh' continue --path '$TARGET'"
  fi
}

reconcile_framework_state() {
  local block_text current_branch current_sha dirty inferred_task
  block_text="$(registered_block "$TARGET")"
  [ -n "$block_text" ] || { undet "missing state and $TARGET is not a registered worktree"; return 2; }
  lock_fields "$block_text"
  if [ "$LOCK_VERSION" = "2" ] && ! validate_v2_lock_reason; then
    undet "v2 recovery lock is malformed or has unexpected fields"
    return 2
  fi
  [ -n "$LOCK_VERSION" ] && [ -n "$LOCK_REASON" ] && [ -n "$LOCK_HOST" ] && [ -n "$LOCK_BRANCH" ] \
    && [ -n "$LOCK_DEFAULT" ] && [ -n "$LOCK_BASE" ] && [ -n "$LOCK_PID" ] || {
      undet "missing state and lock metadata is not a complete ai-worktree recovery record"; return 2; }
  case "$LOCK_HOST" in claude|codex-cli) : ;; *) undet "unsupported recovery host '$LOCK_HOST'"; return 2 ;; esac
  git check-ref-format --branch "$LOCK_BRANCH" >/dev/null 2>&1 || return 2
  git check-ref-format --branch "$LOCK_DEFAULT" >/dev/null 2>&1 || return 2
  current_branch="$(git -C "$TARGET" branch --show-current 2>/dev/null)"
  current_sha="$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || true)"
  dirty="$(git -C "$TARGET" status --porcelain 2>/dev/null)" || {
    undet "could not verify the state-less worktree is clean"; return 2; }
  [ "$current_branch" = "$LOCK_BRANCH" ] && [ "$current_sha" = "$LOCK_BASE" ] && [ -z "$dirty" ] || {
    block "state-less worktree no longer matches its atomic creation record; manual review required"; return 1; }
  if [ "$LOCK_PID" != "$OWNER_PID" ] && pid_alive "$LOCK_PID"; then
    block "another live owner holds this worktree (pid $LOCK_PID)"; return 1
  fi
  HOST="$LOCK_HOST"; LIFECYCLE_OWNER="framework"; BRANCH="$LOCK_BRANCH"
  DEFAULT_REF="$LOCK_DEFAULT"; BASE_SHA="$LOCK_BASE"
  if [ "$LOCK_VERSION" = "2" ]; then
    validate_task_key "$LOCK_TASK" || return $?
    case "$LOCK_PARALLEL" in 0|1) : ;; *) undet "v2 recovery lock has an invalid parallel-task flag"; return 2 ;; esac
    TASK_KEY="$LOCK_TASK"
  elif [ "$TASK_KEY_EXPLICIT" -eq 1 ]; then
    TASK_KEY="$REQUESTED_TASK_KEY"
  elif [ -n "$LOCK_TASK" ]; then
    # A v1 label cannot make later fields authoritative. Treat this only as
    # legacy evidence and require it to agree with the generated branch.
    inferred_task="$(legacy_task_from_branch "$BRANCH" 2>/dev/null || true)"
    [ -n "$inferred_task" ] && [ "$inferred_task" = "$LOCK_TASK" ] || {
      undet "v1 recovery lock carries ambiguous task metadata; pass --task-key after review"
      return 2
    }
    TASK_KEY="$inferred_task"
  else
    inferred_task="$(legacy_task_from_branch "$BRANCH" 2>/dev/null || true)"
    [ -n "$inferred_task" ] || {
      undet "missing state has no task identity; pass --task-key after verifying the legacy checkout"
      return 2
    }
    TASK_KEY="$inferred_task"
  fi
  validate_task_key "$TASK_KEY" || return $?
  if [ "$LOCK_VERSION" = "2" ]; then PARALLEL_TASK="$LOCK_PARALLEL"; else PARALLEL_TASK=0; fi
  write_state "$TARGET" created || { undet "could not reconstruct lifecycle state"; return 2; }
  note "Recovered the creation journal from the atomic Git worktree lock"
}

publish_branch() {
  local path="$1"
  if git remote get-url origin >/dev/null 2>&1; then git -C "$path" push -u origin "$BRANCH"; return $?; fi
  if [ "$ALLOW_LOCAL_ONLY" -eq 1 ]; then note "No origin remote; proceeding local-only by explicit override"; return 0; fi
  undet "no origin remote — use --allow-local-only only when one-disk durability is intentional"
  return 2
}

ready_report() {
  ok "READY: $HOST worktree prepared"
  say "branch   : $BRANCH"
  say "path     : $TARGET"
  say "default  : $DEFAULT_REF"
  say "recovery : $(git -C "$TARGET" rev-parse --short HEAD)"
  if [ "$HOST" = "claude" ]; then
    note "Claude adapter: call EnterWorktree(path=\"$TARGET\") and verify cwd/branch"
  elif [ "$HOST" = "codex-cli" ]; then
    note "Codex CLI active-session next: bash '$SCRIPT_DIR/prepare.sh' codex-cli-validate --path '$TARGET' --owner-pid '$OWNER_PID'; then anchor every subsequent tool to '$TARGET'"
    note "Codex CLI ordinary-shell bootstrap only: launch, fork, or resume Codex with -C '$TARGET'"
  else
    note "Codex Desktop retains native checkout lifecycle ownership"
  fi
}

# --- ownership evidence: the lifecycle journal, corroborated by the Git lock --
#
# There is NO separate claim artifact, deliberately. A contested-claim protocol
# lived here through five reproduced defects and six review rounds — atomic
# claim dirs, a recovery mutex, age-based eviction, generation numbering — and
# it was removed rather than fixed again. Two facts settled it:
#
#   1. It could not enforce anything. Nothing stops a human or a process that
#      never calls this script from editing the tree, so the record was always
#      ADVISORY. It was being hardened to the standard of a lock it could not be.
#   2. Sharing is prevented by construction. `claude-create` generates a unique
#      nonce, so every worker gets its own path and never contends. The contested
#      path only opens when someone points two sessions at one `--path` by hand,
#      which has never been observed outside test harnesses.
#
# Adding a third ownership record alongside the journal and the lock is what
# produced the evidence-conflict problem in the first place, so the journal is
# the single record and the lock reason corroborates it.
#
# Owner identity is `owner_pid` in the journal. Liveness is advisory and used
# only to REFUSE, never to seize or delete: a live different owner refuses, a
# proved-dead owner permits the explicitly requested continuation, and anything
# unreadable, malformed or conflicting refuses and names what to inspect.
#
# Deferred, with a trigger: contested same-path coordination, cross-host
# identity, and automatic takeover. Revisit only if a real collision is observed
# or the roadmap introduces deliberate shared-path parallelism (BACKLOG #349).

# Named for the GIT lock it claims, not for the deleted claim artifact: this
# refreshes the deletion guard and refuses a live different owner. Nothing else.
claim_framework_lock() {
  local block_text reason pid refresh_metadata=0
  LOCK_RECLAIMED=0
  block_text="$(registered_block "$TARGET")"
  [ -n "$block_text" ] || { undet "$TARGET is not a registered worktree"; return 2; }
  lock_fields "$block_text"; reason="$LOCK_REASON"; pid="$LOCK_PID"
  if [ -n "$reason" ]; then
    case "$LOCK_VERSION" in 1|2) : ;; *) undet "lock is not a recognized ai-worktree lifecycle record"; return 2 ;; esac
    if [ "$LOCK_VERSION" = "2" ] && ! validate_v2_lock_reason; then
      undet "v2 lock is malformed or has unexpected fields"
      return 2
    fi
    [ -n "$pid" ] && [ "$LOCK_HOST" = "$HOST" ] && [ "$LOCK_BRANCH" = "$BRANCH" ] \
      && [ "$LOCK_DEFAULT" = "$DEFAULT_REF" ] && [ "$LOCK_BASE" = "$BASE_SHA" ] || {
        undet "lock metadata does not match recorded lifecycle state"; return 2; }
    if [ "$LOCK_VERSION" = "2" ]; then
      if [ -z "$LOCK_TASK" ] || { [ "$LOCK_PARALLEL" != "0" ] && [ "$LOCK_PARALLEL" != "1" ]; }; then
        undet "v2 lock is missing task lifecycle metadata"
        return 2
      fi
    fi
    [ -z "$LOCK_TASK" ] || [ "$LOCK_TASK" = "$TASK_KEY" ] || {
      undet "lock task identity does not match recorded lifecycle state"; return 2; }
    if [ -n "$LOCK_PARALLEL" ] && [ "$LOCK_PARALLEL" != "$PARALLEL_TASK" ]; then
      if [ "$ALLOW_PARALLEL_TASK" -eq 1 ] && [ "$LOCK_PARALLEL" = "0" ] && [ "$PARALLEL_TASK" = "1" ]; then
        refresh_metadata=1
      else
        undet "lock parallel-task flag does not match recorded lifecycle state"; return 2
      fi
    fi
  fi
  # The lock reason CORROBORATES the journal. A live different owner refuses;
  # that refusal is the whole of the coordination this script performs.
  if [ -n "$pid" ] && [ "$pid" != "$OWNER_PID" ] && pid_alive "$pid"; then
    block "another live owner holds this worktree (pid $pid)"; return 1
  fi
  # Already ours and still live: leave the lock ALONE. LOCK_RECLAIMED stays 0,
  # which is how `advance_existing` knows nothing changed and a ready checkout
  # can short-circuit to ready_report rather than re-running the setup hook.
  if [ "$refresh_metadata" -eq 0 ] && [ -n "$pid" ] && [ "$pid" = "$OWNER_PID" ] && pid_alive "$pid"; then
    return 0
  fi
  # Refresh Git's deletion guard. Git defines this lock as protection against
  # `worktree remove`, and that is all it is claimed to be here — it is not an
  # editing mutex and describing it as one is what started this.
  [ -z "$reason" ] || git -C "$PRIMARY" worktree unlock "$TARGET" 2>/dev/null || true
  git -C "$PRIMARY" worktree lock \
    --reason "$(framework_lock_reason)" \
    "$TARGET" || { undet "could not refresh the worktree deletion guard"; return 2; }
  LOCK_RECLAIMED=1
}

advance_existing() {
  local state current_branch recorded_pid requested_task="$REQUESTED_TASK_KEY"
  TARGET="$(absolute_path "$TARGET")"
  if ! load_state "$TARGET"; then
    if [ -f "$(state_file_for "$TARGET" 2>/dev/null || true)" ]; then
      undet "lifecycle state exists but is malformed or unsupported; refusing recovery inference"
      return 2
    fi
    validate_owner_pid || return $?
    reconcile_framework_state || return $?
    load_state "$TARGET" || return 2
  fi
  if [ "$TASK_KEY_EXPLICIT" -eq 1 ]; then
    if [ -n "$TASK_KEY" ] && [ "$TASK_KEY" != "$requested_task" ]; then
      block "requested task key '$requested_task' does not match recorded '$TASK_KEY'"
      return 1
    fi
    [ -n "$TASK_KEY" ] || TASK_KEY="$requested_task"
  fi
  [ -z "$RECORDED_PATH" ] || [ "$RECORDED_PATH" = "$TARGET" ] || {
    block "recorded path '$RECORDED_PATH' does not match '$TARGET'"; return 1; }
  state="$(read_state "$TARGET" state 2>/dev/null || true)"
  current_branch="$(git -C "$TARGET" branch --show-current 2>/dev/null)"

  if [ "$LIFECYCLE_OWNER" = "codex-desktop" ] && [ "$state" = "attached" ] && [ -z "$current_branch" ]; then
    [ -n "$BASE_SHA" ] && [ "$(git -C "$TARGET" rev-parse HEAD 2>/dev/null)" = "$BASE_SHA" ] || {
      block "detached Desktop checkout no longer matches its recorded live base"; return 1; }
    git -C "$TARGET" switch -c "$BRANCH" || { undet "branch attachment failed; state remains attached"; return 2; }
    current_branch="$BRANCH"
  fi
  [ "$current_branch" = "$BRANCH" ] || { block "current branch '$current_branch' does not match recorded '$BRANCH'"; return 1; }

  if [ "$LIFECYCLE_OWNER" = "framework" ]; then
    validate_owner_pid || return $?
    recorded_pid="$(read_state "$TARGET" owner_pid 2>/dev/null || true)"
    if [ -n "$recorded_pid" ] && [ "$recorded_pid" != "$OWNER_PID" ] && pid_alive "$recorded_pid"; then
      block "recorded owner pid $recorded_pid is still live"; return 1
    fi
    if [ "$state" = "task-conflict" ]; then
      [ "$ALLOW_PARALLEL_TASK" -eq 1 ] || {
        block "task-conflict is non-ready; continue with --allow-parallel-task only if duplicate implementation is intentional"
        return 1
      }
      PARALLEL_TASK=1
      write_state "$TARGET" created || return 2
      state=created
      note "Explicitly resolving task-conflict as parallel work for '$TASK_KEY'"
    fi
    case "$state" in
      created)
        publish_branch "$TARGET" || { undet "publication failed; state remains created"; return 2; }
        write_state "$TARGET" published || return 2; state="published" ;;
      published|locked|setup-failed|ready) : ;;
      *) undet "unsupported framework state '$state'"; return 2 ;;
    esac
    claim_framework_lock || return $?
    if [ "$state" = "ready" ] && [ "$LOCK_RECLAIMED" -eq 0 ]; then
      ready_report
      return 0
    fi
    write_state "$TARGET" locked || return 2
    if ! run_hook setup "$TARGET"; then
      write_state "$TARGET" setup-failed >/dev/null 2>&1 || true
      undet "runtime setup failed; checkout remains locked and is NOT ready"
      return 2
    fi
    write_state "$TARGET" ready || return 2
  elif [ "$LIFECYCLE_OWNER" = "codex-desktop" ]; then
    case "$state" in
      attached)
        publish_branch "$TARGET" || { undet "publication failed; state remains attached"; return 2; }
        write_state "$TARGET" published || return 2 ;;
      published|setup-failed|ready) : ;;
      *) undet "unsupported Codex Desktop state '$state'"; return 2 ;;
    esac
    if [ "$state" = "ready" ]; then ready_report; return 0; fi
    if ! run_hook setup "$TARGET"; then
      write_state "$TARGET" setup-failed >/dev/null 2>&1 || true
      undet "runtime setup failed; native worktree remains but is NOT ready"
      return 2
    fi
    write_state "$TARGET" ready || return 2
  else
    undet "unknown lifecycle owner '$LIFECYCLE_OWNER'"; return 2
  fi
  ready_report
}

create_framework_worktree() {
  local requested_host requested_branch requested_default requested_base requested_task requested_parallel block_text sf rc
  HOST="$1"; LIFECYCLE_OWNER="framework"
  validate_owner_pid || return $?
  [ -n "$BASE" ] || { say "ERROR: --base is required"; return 2; }
  [ -n "$DEFAULT_REF" ] || { say "ERROR: --default-ref is required"; return 2; }
  git check-ref-format --branch "$DEFAULT_REF" >/dev/null 2>&1 || {
    say "ERROR: invalid default ref $DEFAULT_REF"; return 2; }
  generate_branch || return $?
  if [ "$TASK_KEY_EXPLICIT" -eq 1 ]; then TASK_KEY="$REQUESTED_TASK_KEY"; else TASK_KEY="slug:$SLUG"; fi
  validate_task_key "$TASK_KEY" || return $?
  if [ "$ALLOW_PARALLEL_TASK" -eq 1 ] && [ "$TASK_KEY_EXPLICIT" -eq 0 ]; then
    say "ERROR: --allow-parallel-task requires an explicit --task-key"
    return 2
  fi
  PARALLEL_TASK="$ALLOW_PARALLEL_TASK"
  git check-ref-format --branch "$BRANCH" >/dev/null 2>&1 || { say "ERROR: invalid branch $BRANCH"; return 2; }
  [ -n "$TARGET" ] || TARGET="$PRIMARY/.claude/worktrees/${BRANCH#wt/}"
  TARGET="$(absolute_path "$TARGET")"
  BASE_SHA="$(git rev-parse "$BASE^{commit}" 2>/dev/null)" || { undet "could not resolve base '$BASE'"; return 2; }
  if [ -e "$TARGET" ]; then
    requested_host="$HOST"; requested_branch="$BRANCH"
    requested_default="$DEFAULT_REF"; requested_base="$BASE_SHA"
    requested_task="$TASK_KEY"; requested_parallel="$PARALLEL_TASK"
    sf="$(state_file_for "$TARGET" 2>/dev/null || true)"
    if load_state "$TARGET"; then
      if [ "$HOST" != "$requested_host" ] || [ "$BRANCH" != "$requested_branch" ] \
        || [ "$DEFAULT_REF" != "$requested_default" ] || [ "$BASE_SHA" != "$requested_base" ] \
        || { [ -n "$TASK_KEY" ] && [ "$TASK_KEY" != "$requested_task" ]; }; then
        block "existing lifecycle does not match this create request; use explicit continue or the recorded host resume command"
        return 1
      fi
      [ -n "$TASK_KEY" ] || TASK_KEY="$requested_task"
      [ "$requested_parallel" -eq 0 ] || PARALLEL_TASK=1
    elif [ -n "$sf" ] && [ -f "$sf" ]; then
      undet "existing lifecycle state is malformed or unsupported; refusing lock-based reconstruction"
      return 2
    else
      block_text="$(registered_block "$TARGET")"; lock_fields "$block_text"
      [ "$LOCK_HOST" = "$requested_host" ] && [ "$LOCK_BRANCH" = "$requested_branch" ] \
        && [ "$LOCK_DEFAULT" = "$requested_default" ] && [ "$LOCK_BASE" = "$requested_base" ] || {
          block "state-less recovery lock does not match this create request; use explicit continue after verifying ownership"
          return 1
        }
      HOST="$requested_host"; BRANCH="$requested_branch"
      DEFAULT_REF="$requested_default"; BASE_SHA="$requested_base"
      TASK_KEY="$requested_task"; PARALLEL_TASK="$requested_parallel"
    fi
    advance_existing; return $?
  fi
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    block "branch already exists without the requested worktree path; choose a new branch"
    return 1
  fi
  bash "$PREFLIGHT" "$BRANCH" || return $?
  if git remote get-url origin >/dev/null 2>&1; then
    resolve_live_default || { undet "--default-ref '$DEFAULT_REF' is not the live origin default"; return 2; }
  fi
  BASE_SHA="$(git rev-parse "$BASE^{commit}" 2>/dev/null)" || { undet "could not resolve base '$BASE'"; return 2; }
  scan_task_collisions pre || return $?
  mkdir -p "$COMMON/info" || return 2
  grep -qxF '.claude/worktrees/' "$COMMON/info/exclude" 2>/dev/null || printf '.claude/worktrees/\n' >>"$COMMON/info/exclude" || return 2
  git -C "$PRIMARY" worktree add --lock --reason "$(framework_lock_reason)" \
    -b "$BRANCH" "$TARGET" "$BASE" || return 2
  write_state "$TARGET" created || {
    undet "worktree exists under an atomic recovery lock, but state could not be recorded"
    recovery_hint
    return 2
  }
  scan_task_collisions post
  rc=$?
  if [ "$rc" -ne 0 ]; then recovery_hint; return "$rc"; fi
  advance_existing
  rc=$?
  [ "$rc" -eq 0 ] || recovery_hint
  return "$rc"
}

continue_existing() {
  [ -n "$TARGET" ] || { say "ERROR: --path is required"; return 2; }
  if [ "$TASK_KEY_EXPLICIT" -eq 1 ]; then validate_task_key "$REQUESTED_TASK_KEY" || return $?; fi
  advance_existing
}

resume_claude() {
  [ -n "$TARGET" ] || { say "ERROR: --path is required"; return 2; }
  TARGET="$(absolute_path "$TARGET")"
  load_state "$TARGET" || { undet "missing or incomplete state; refusing to guess ownership"; return 2; }
  [ "$HOST" = "claude" ] && [ "$LIFECYCLE_OWNER" = "framework" ] || {
    block "this is not a framework-owned Claude worktree"; return 1; }
  advance_existing
}

codex_cli_validate() {
  [ -n "$OWNER_PID" ] || { say "ERROR: codex-cli-validate requires --owner-pid"; return 2; }
  validate_owner_pid || return $?
  [ -n "$TARGET" ] || TARGET="$ACTING"
  TARGET="$(absolute_path "$TARGET")"
  [ "$TARGET" != "$PRIMARY" ] || { block "Codex CLI is on the primary checkout; run codex-cli-create before validation"; return 1; }
  load_state "$TARGET" || { undet "missing or incomplete lifecycle state"; return 2; }
  [ "$RECORDED_VERSION" = "2" ] || { undet "Codex CLI validation requires a v2 lifecycle journal"; return 2; }
  [ "$HOST" = "codex-cli" ] && [ "$LIFECYCLE_OWNER" = "framework" ] || {
    block "recorded host/owner is not framework-owned Codex CLI"; return 1; }
  [ "$RECORDED_PATH" = "$TARGET" ] || { block "recorded path does not match this checkout"; return 1; }
  [ "$RECORDED_PID" = "$OWNER_PID" ] || { block "recorded owner pid does not match the current Codex owner"; return 1; }
  local current_branch upstream block_text state
  state="$(read_state "$TARGET" state 2>/dev/null || true)"
  [ "$state" = "ready" ] || { block "lifecycle state is '$state', not ready; run continue before editing"; return 1; }
  current_branch="$(git -C "$TARGET" branch --show-current 2>/dev/null)"
  [ "$current_branch" = "$BRANCH" ] || { block "current branch does not match recorded branch '$BRANCH'"; return 1; }
  upstream="$(git -C "$TARGET" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  [ "$upstream" = "origin/$BRANCH" ] || { undet "upstream '$upstream' is not exact origin/$BRANCH"; return 2; }
  block_text="$(registered_block "$TARGET")"; lock_fields "$block_text"
  [ "$LOCK_VERSION" = "2" ] && validate_v2_lock_reason \
    && [ "$LOCK_HOST" = "codex-cli" ] && [ "$LOCK_BRANCH" = "$BRANCH" ] \
    && [ "$LOCK_DEFAULT" = "$DEFAULT_REF" ] && [ "$LOCK_BASE" = "$BASE_SHA" ] \
    && [ "$LOCK_PID" = "$OWNER_PID" ] && [ "$LOCK_TASK" = "$TASK_KEY" ] \
    && [ "$LOCK_PARALLEL" = "$PARALLEL_TASK" ] \
    || { undet "Codex CLI lock does not exactly match v2 lifecycle state and owner"; return 2; }
  pid_alive "$LOCK_PID" || { undet "lock owner pid $LOCK_PID is not live"; return 2; }
  ok "READY: Codex CLI is isolated on $BRANCH at $TARGET (upstream $upstream, owner pid $LOCK_PID)"
}

codex_desktop_adopt() {
  local current_sha rc
  HOST="codex-desktop"; LIFECYCLE_OWNER="codex-desktop"; OWNER_PID=""
  [ "$ACTING" != "$PRIMARY" ] || { block "Codex Desktop adoption requires a native per-chat Worktree, not Local"; return 1; }
  TARGET="$ACTING"
  if [ -f "$(state_file_for "$TARGET" 2>/dev/null || true)" ]; then
    load_state "$TARGET" || { block "checkout already has a branch but no matching Codex Desktop state"; return 1; }
    [ "$HOST" = "codex-desktop" ] && [ "$LIFECYCLE_OWNER" = "codex-desktop" ] || return 1
    advance_existing; return $?
  fi
  [ -z "$(git branch --show-current 2>/dev/null)" ] || {
    block "checkout already has a branch but no matching Codex Desktop state"; return 1; }
  [ -n "$DEFAULT_REF" ] || { say "ERROR: --default-ref is required"; return 2; }
  git check-ref-format --branch "$DEFAULT_REF" >/dev/null 2>&1 || {
    say "ERROR: invalid default ref $DEFAULT_REF"; return 2; }
  generate_branch || return $?
  if [ "$TASK_KEY_EXPLICIT" -eq 1 ]; then TASK_KEY="$REQUESTED_TASK_KEY"; else TASK_KEY="slug:$SLUG"; fi
  validate_task_key "$TASK_KEY" || return $?
  if [ "$ALLOW_PARALLEL_TASK" -eq 1 ] && [ "$TASK_KEY_EXPLICIT" -eq 0 ]; then
    say "ERROR: --allow-parallel-task requires an explicit --task-key"
    return 2
  fi
  PARALLEL_TASK="$ALLOW_PARALLEL_TASK"
  bash "$PREFLIGHT" "$BRANCH" || return $?
  scan_task_collisions pre || return $?
  resolve_live_default || { undet "--default-ref '$DEFAULT_REF' is not the live origin default"; return 2; }
  current_sha="$(git rev-parse HEAD 2>/dev/null || true)"
  [ "$current_sha" = "$BASE_SHA" ] || {
    block "native Desktop checkout is stale: HEAD $current_sha != live origin/$DEFAULT_REF $BASE_SHA"; return 1; }
  write_state "$TARGET" attached || { undet "could not record Desktop ownership before branch attachment"; return 2; }
  scan_task_collisions post
  rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  advance_existing
  rc=$?
  [ "$rc" -eq 0 ] || recovery_hint
  return "$rc"
}

show_status() {
  [ -n "$TARGET" ] || TARGET="$ACTING"
  TARGET="$(absolute_path "$TARGET")"
  local sf; sf="$(state_file_for "$TARGET" 2>/dev/null || true)"
  if [ -n "$sf" ] && [ -f "$sf" ]; then cat "$sf"; else note "no ai-worktree-state record for $TARGET"; fi
  git -C "$TARGET" status --short --branch 2>/dev/null || true
  registered_block "$TARGET"
}

case "$MODE" in
  claude-create) create_framework_worktree claude ;;
  codex-cli-create) create_framework_worktree codex-cli ;;
  continue) continue_existing ;;
  claude-resume) resume_claude ;;
  codex-cli-validate) codex_cli_validate ;;
  codex-desktop-adopt) codex_desktop_adopt ;;
  status) show_status ;;
  *) say "Unknown mode: $MODE"; usage; exit 2 ;;
esac
