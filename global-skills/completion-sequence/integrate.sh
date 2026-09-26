#!/usr/bin/env bash
# Optimistic closeout helper for concurrent topic worktrees.
#
# Exit codes: 0 success; 1 known state block/conflict; 2 environment/Git error;
# 3 origin advanced during publish — refresh, re-integrate, re-test, and retry.

set -uo pipefail
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -oBatchMode=yes -oConnectTimeout=10}"

say()   { printf '%s\n' "$*"; }
ok()    { printf 'ok     %s\n' "$*"; }
note()  { printf 'note   %s\n' "$*"; }
block() { printf 'BLOCK  %s\n' "$*"; }

usage() {
  cat <<'EOF'
Usage:
  integrate.sh refresh --default-ref <branch>
  integrate.sh publish --default-ref <branch>

refresh: fetch origin and merge origin/<branch> into the current clean topic branch.
publish: run the repository's internal full check on exact topic HEAD, push that
         HEAD for durability, revalidate the live base, and fast-forward it to
         the default through the local push gate.

publish exit 3 means origin advanced inside the fetch-to-push race window. Run
refresh again, resolve/integrate, rerun affected tests, rewrite closeout memory on
top of the new state, commit it, and retry publish. Never force-push the default.
EOF
}

MODE="${1:-}"
[ -n "$MODE" ] || { usage; exit 2; }
shift || true
DEFAULT_REF=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --default-ref)
      [ "$#" -ge 2 ] || { say "--default-ref requires a branch name"; exit 2; }
      DEFAULT_REF="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) say "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

[ -n "$DEFAULT_REF" ] || { say "ERROR: --default-ref is required"; exit 2; }
git check-ref-format --branch "$DEFAULT_REF" >/dev/null 2>&1 || {
  say "ERROR: invalid default branch name '$DEFAULT_REF'"; exit 2; }
TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  say "ERROR: not inside a Git checkout"; exit 2; }
BRANCH="$(git branch --show-current 2>/dev/null)"
[ -n "$BRANCH" ] || { block "detached HEAD cannot be integrated"; exit 1; }
[ "$BRANCH" != "$DEFAULT_REF" ] || {
  block "current branch is the integration branch; this helper is for topic worktrees"; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { say "ERROR: origin remote is required"; exit 2; }

require_clean() {
  local dirty
  dirty="$(git -C "$TOPLEVEL" status --porcelain 2>/dev/null)" || return 2
  if [ -n "$dirty" ]; then
    block "working tree is not clean; commit the intended implementation before refresh/publish"
    printf '%s\n' "$dirty"
    return 1
  fi
}

fetch_default() {
  git fetch --no-tags origin "+refs/heads/$DEFAULT_REF:refs/remotes/origin/$DEFAULT_REF"
}

ensure_local_ci() {
  local checker="$TOPLEVEL/scripts/check.sh" record_file record_count_before
  local record_count_after checked_head
  [ -x "$checker" ] || {
    block "internal full-check runner is missing or not executable: $checker"
    return 1
  }
  record_file="$TOPLEVEL/logs/check-runs.jsonl"
  if [ -f "$record_file" ]; then
    record_count_before="$(awk 'END {print NR + 0}' "$record_file")" || return 2
  else
    record_count_before=0
  fi

  note "Running internal full check on exact head $HEAD_SHA"
  bash "$checker" --full || {
    block "internal full check did not pass; default branch was not updated"
    return 1
  }
  checked_head="$(git rev-parse HEAD 2>/dev/null)" || return 2
  if [ "$checked_head" != "$HEAD_SHA" ]; then
    block "HEAD changed while the internal full check ran ($HEAD_SHA -> $checked_head)"
    return 1
  fi
  require_clean || return $?
  [ -f "$record_file" ] || {
    block "internal full check produced no structured record at $record_file"
    return 1
  }
  record_count_after="$(awk 'END {print NR + 0}' "$record_file")" || return 2
  if [ "$record_count_after" -ne $((record_count_before + 1)) ]; then
    block "internal full check did not append exactly one structured record"
    return 1
  fi
  if ! python3 - "$record_file" "$HEAD_SHA" <<'PY'
import json
import sys

record_path, expected_head = sys.argv[1:]
try:
    with open(record_path, encoding="utf-8") as handle:
        record = json.loads(handle.readlines()[-1])
except (OSError, IndexError, json.JSONDecodeError) as exc:
    print(f"invalid internal full-check record: {exc}")
    raise SystemExit(1)

required = {
    "commit": expected_head,
    "dirty": False,
    "head_moved": False,
    "mode": "full",
    "fail": 0,
    "could_not_run": 0,
}
problems = [
    f"{key}={record.get(key)!r} (expected {expected!r})"
    for key, expected in required.items()
    if type(record.get(key)) is not type(expected) or record.get(key) != expected
]
if type(record.get("pass")) is not int or record["pass"] <= 0:
    problems.append(f"pass={record.get('pass')!r} (expected a positive integer)")
if problems:
    print("incomplete internal full-check evidence: " + "; ".join(problems))
    raise SystemExit(1)
PY
  then
    block "structured internal full-check evidence is not publication-eligible"
    return 1
  fi
}

verify_landed_after_advance() {
  local live_before="$1" live_after fetched
  live_after="$(git ls-remote origin "refs/heads/$DEFAULT_REF" 2>/dev/null | awk 'NR == 1 {print $1}')"
  [ -n "$live_after" ] || { say "ERROR: could not verify live origin/$DEFAULT_REF after publish"; return 2; }
  if [ "$live_after" = "$HEAD_SHA" ]; then return 0; fi
  fetch_default || { say "ERROR: could not fetch advanced origin/$DEFAULT_REF for ancestry verification"; return 2; }
  fetched="$(git rev-parse "origin/$DEFAULT_REF" 2>/dev/null)" || return 2
  if git merge-base --is-ancestor "$HEAD_SHA" "$fetched"; then
    note "Work landed at $HEAD_SHA; origin/$DEFAULT_REF subsequently advanced to $fetched"
    return 0
  fi
  if [ "$live_after" != "$live_before" ]; then
    say "RETRY: origin/$DEFAULT_REF advanced during publish without containing this work ($live_before -> $live_after)"
    say "       Run refresh, resolve/integrate, rerun affected tests, rewrite closeout memory, commit, and publish again."
    return 3
  fi
  say "ERROR: live origin/$DEFAULT_REF does not contain published HEAD"
  return 2
}

case "$MODE" in
  refresh)
    require_clean || exit $?
    fetch_default || { say "ERROR: fetch of origin/$DEFAULT_REF failed"; exit 2; }
    if git merge-base --is-ancestor "origin/$DEFAULT_REF" HEAD; then
      ok "HEAD already contains origin/$DEFAULT_REF"
      exit 0
    fi
    note "Merging origin/$DEFAULT_REF into $BRANCH"
    if ! git merge --no-edit "origin/$DEFAULT_REF"; then
      block "integration conflict; resolve it in this worktree, commit, and rerun refresh"
      exit 1
    fi
    ok "Integrated origin/$DEFAULT_REF into $BRANCH"
    ;;
  publish)
    require_clean || exit $?
    fetch_default || { say "ERROR: fetch of origin/$DEFAULT_REF failed"; exit 2; }
    OBSERVED_SHA="$(git rev-parse "origin/$DEFAULT_REF" 2>/dev/null)" || exit 2
    HEAD_SHA="$(git rev-parse HEAD 2>/dev/null)" || exit 2
    if ! git merge-base --is-ancestor "$OBSERVED_SHA" "$HEAD_SHA"; then
      block "HEAD does not contain live origin/$DEFAULT_REF; run refresh, test, and recommit closeout state"
      exit 1
    fi
    # Repositories adopting portable review evidence fail early, before the
    # expensive full gate. The raw Git hook rechecks the actual advertised base.
    if [ -f "$TOPLEVEL/scripts/pre_push.py" ]; then
      python3 "$TOPLEVEL/scripts/check_git_hook_contract.py" --raw-installed --repo "$TOPLEVEL" || {
        block "shared raw push hook is not active; coordinate explicit installation before publication"
        exit 1
      }
      python3 "$TOPLEVEL/scripts/publication_review.py" verify --repo "$TOPLEVEL" --base "$OBSERVED_SHA" --target "$HEAD_SHA" || {
        block "completed scoped reviews are missing or stale; prepare requests and retain accepted reports for these exact commits"
        exit 1
      }
    fi
    ensure_local_ci || exit $?
    git push origin "HEAD:refs/heads/$BRANCH" || {
      say "ERROR: could not publish exact topic HEAD $HEAD_SHA for durability"
      exit 2
    }
    fetch_default || { say "ERROR: post-check fetch of origin/$DEFAULT_REF failed"; exit 2; }
    LIVE_AFTER_CHECK="$(git rev-parse "origin/$DEFAULT_REF" 2>/dev/null)" || exit 2
    if [ "$LIVE_AFTER_CHECK" != "$OBSERVED_SHA" ]; then
      say "RETRY: origin/$DEFAULT_REF advanced while internal checks ran ($OBSERVED_SHA -> $LIVE_AFTER_CHECK)"
      say "       Run refresh, resolve/integrate, rerun affected tests, rewrite closeout memory, commit, and publish again."
      exit 3
    fi
    PUSH_OK=1
    AI_GOVERNANCE_GATED_PUBLISH="$HEAD_SHA" \
      git push origin "HEAD:refs/heads/$DEFAULT_REF" || PUSH_OK=0
    verify_landed_after_advance "$OBSERVED_SHA"
    VERIFY_RC=$?
    if [ "$VERIFY_RC" -ne 0 ]; then exit "$VERIFY_RC"; fi
    if [ "$PUSH_OK" -eq 0 ]; then
      note "The direct push failed, but live ancestry proves this work landed concurrently"
    fi
    ok "Published $BRANCH at $HEAD_SHA to origin/$DEFAULT_REF after internal full checks"
    ;;
  *) say "Unknown mode: $MODE"; usage; exit 2 ;;
esac
