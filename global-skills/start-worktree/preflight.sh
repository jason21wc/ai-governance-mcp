#!/usr/bin/env bash
# Preconditions for creating a concurrent-session worktree. Repo-agnostic.
#
# WHY THIS IS A SCRIPT AND NOT A CHECKLIST
# ----------------------------------------
# Every check here is a mechanical fact about git state. An agent asked to
# "check for a name collision" will check the surface it happens to think of;
# the collision that destroyed three commits was on a surface nobody thought of
# (a branch that existed with unpushed work while no worktree and no process
# referenced it). Deterministic checks do not have good and bad days.
#
# EXIT CODES
#   0  clean          — every check ran, nothing blocking
#   1  BLOCKING       — do not create until resolved
#   2  UNDETERMINED   — a check could not run; a human decides
# Warnings alone do not fail. An UNRUN check is not a warning: it is rc 2.
#
# THE RULE THIS SCRIPT EXISTS TO OBEY
# -----------------------------------
# "Could not determine" is never reported as "clean". The first version of this
# file printed "RESULT: clean — safe to create" with rc 0 when origin was
# unreachable, having stated that exact rule in this header. The per-check line
# was honest and the verdict line was not — and the verdict line is the one the
# calling procedure acts on. Hence UNDETERMINED is now counted and returned.

set -uo pipefail

# Never hang an agent's shell on an SSH passphrase or host-key prompt.
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -oBatchMode=yes -oConnectTimeout=10}"

NAME="${1:-}"
BLOCKING=0
WARNINGS=0
UNDETERMINED=0
OFFLINE="${PREFLIGHT_OFFLINE:-0}"
HAS_ORIGIN=0
REMOTE_QUERY_OK=0
REMOTE_HEADS=""
LIVE_DEFAULT=""
LIVE_DEFAULT_SHA=""

say()   { printf '%s\n' "$*"; }
block() { printf 'BLOCK  %s\n' "$*"; BLOCKING=$((BLOCKING + 1)); }
warn()  { printf 'WARN   %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
undet() { printf '?????  %s\n' "$*"; UNDETERMINED=$((UNDETERMINED + 1)); }
ok()    { printf 'ok     %s\n' "$*"; }
note()  { printf 'note   %s\n' "$*"; }

command -v git >/dev/null 2>&1 || { say "FATAL: git not found"; exit 2; }

# --- 0. Are we in a git repo at all? -----------------------------------------
TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  say "FATAL: not inside a git repository"; exit 2; }

# The COMMON dir is shared by the primary checkout and every worktree, so it
# identifies the repository regardless of which tree we are standing in.
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)"
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac
if ! PRIMARY="$(cd "$COMMON/.." 2>/dev/null && pwd)"; then
  say "FATAL: could not resolve the primary checkout from $COMMON"; exit 2
fi

say "repository : $PRIMARY"
say "acting in  : $TOPLEVEL"
[ "$TOPLEVEL" != "$PRIMARY" ] && note "already inside a worktree, not the primary checkout"
say ""

# --- 1. Live remote/default branch, derived not assumed ----------------------
# One ls-remote call supplies BOTH name-collision data and the live default SHA.
# Contacting the remote and then comparing only a cached origin/* ref is a false
# freshness proof: another clone can advance the remote while our cache stays put.
if git remote get-url origin >/dev/null 2>&1; then
  HAS_ORIGIN=1
  if [ "$OFFLINE" = "1" ]; then
    undet "offline mode — live origin state NOT checked"
  elif REMOTE_HEADS="$(git ls-remote --symref origin HEAD 'refs/heads/*' 2>/dev/null)"; then
    REMOTE_QUERY_OK=1
    LIVE_DEFAULT="$(printf '%s\n' "$REMOTE_HEADS" | sed -n 's#^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$#\1#p' | head -1)"
    LIVE_DEFAULT_SHA="$(printf '%s\n' "$REMOTE_HEADS" | awk '$2 == "HEAD" && $1 !~ /^ref:/ {print $1; exit}')"
    if [ -z "$LIVE_DEFAULT" ] || [ -z "$LIVE_DEFAULT_SHA" ]; then
      undet "origin answered, but its default branch or live HEAD SHA could not be derived"
    else
      ok "live origin default: $LIVE_DEFAULT at ${LIVE_DEFAULT_SHA:0:12}"
    fi
  else
    undet "could not reach origin — remote names and live base freshness NOT verified"
  fi
fi

DEFAULT="$LIVE_DEFAULT"
if [ -z "$DEFAULT" ]; then
  DEFAULT="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
fi
if [ -z "$DEFAULT" ]; then
  DEFAULT="$(git config --get init.defaultBranch 2>/dev/null || true)"
  git show-ref --verify --quiet "refs/heads/$DEFAULT" 2>/dev/null || DEFAULT=""
fi
if [ -z "$DEFAULT" ]; then
  # Exactly one local branch is unambiguous; more than one is a guess, and a
  # hardcoded name list (main/master/trunk) is an assumption dressed as a
  # derivation — it silently omits dev, develop, and every house convention.
  ONLY="$(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null)"
  if [ "$(printf '%s\n' "$ONLY" | grep -c .)" = "1" ]; then DEFAULT="$ONLY"; fi
fi
if [ -z "$DEFAULT" ]; then
  undet "could not derive the default branch — pass an explicit start-point when creating"
else
  ok "default branch: $DEFAULT"
fi

# --- 2. Name collision, on ALL THREE surfaces --------------------------------
# A branch can exist with unpushed commits while NO worktree and NO process
# references it. That is the silent case: a pid lock cannot see it, because the
# owning session is finished. Checking one surface is checking none.
if [ -z "$NAME" ]; then
  undet "no branch name given — collision checks did not run (pass one as \$1)"
else
  COLLIDE=0
  REMOTE_CHECKED=0

  if ! git check-ref-format --branch "$NAME" >/dev/null 2>&1; then
    block "'$NAME' is not a valid git branch name — 'git worktree add' will reject it"
    COLLIDE=1
  fi

  if git show-ref --verify --quiet "refs/heads/$NAME"; then
    if UP_OUT="$(git log --oneline "$NAME" --not --remotes 2>/dev/null)"; then
      UNPUSHED="$(printf '%s' "$UP_OUT" | grep -c . || true)"
    else
      UNPUSHED=""
    fi
    if [ -z "$UNPUSHED" ]; then
      block "local branch '$NAME' exists; could NOT determine whether it has unpushed work"
    elif [ "${UNPUSHED:-0}" -gt 0 ]; then
      block "local branch '$NAME' exists and has $UNPUSHED commit(s) on NO remote"
      note  "  recovery handle (record this before doing anything): $(git rev-parse --short "$NAME" 2>/dev/null)"
      note  "  reusing this name can discard those commits. Pick another name."
    else
      block "local branch '$NAME' already exists (fully pushed, but still taken)"
    fi
    COLLIDE=1
  fi

  if [ "$HAS_ORIGIN" -eq 1 ]; then
    if [ "$REMOTE_QUERY_OK" -eq 1 ]; then
      REMOTE_CHECKED=1
      if printf '%s\n' "$REMOTE_HEADS" | awk -v ref="refs/heads/$NAME" '$2 == ref { found=1 } END { exit !found }'; then
        block "remote branch 'origin/$NAME' already exists"
        COLLIDE=1
      fi
    fi
  else
    note "no 'origin' remote — there is no remote surface to collide on"
    REMOTE_CHECKED=1
  fi

  # -F: $NAME is data, not a regex. Without it 'wt/fix.bug' matches 'wt/fixXbug'.
  if git worktree list --porcelain 2>/dev/null | grep -qxF "branch refs/heads/$NAME"; then
    block "a worktree is already checked out on branch '$NAME'"
    COLLIDE=1
  fi

  if [ "$COLLIDE" -eq 0 ]; then
    if [ "$REMOTE_CHECKED" -eq 1 ]; then
      ok "name '$NAME' is free on all three surfaces (local, remote, worktrees)"
    else
      warn "name '$NAME' is free LOCALLY (branches, worktrees) — remote NOT verified"
    fi
  fi
fi

# --- 3. Is the primary checkout dirty? ---------------------------------------
# Uncommitted work in the primary blocks a sibling's fast-forward merge, and is
# the single most common way a session's work is lost: it belongs to no branch.
# `2>/dev/null | wc -l` would report a FAILED status call as "0 files, clean";
# capture the status separately so a failure is undetermined, not clean.
if ! DIRTY_OUT="$(git -C "$PRIMARY" status --porcelain 2>&1)"; then
  undet "could not read the primary checkout's status — dirtiness NOT determined"
else
  DIRTY="$(printf '%s' "$DIRTY_OUT" | grep -c . || true)"
  if [ "${DIRTY:-0}" -gt 0 ]; then
    warn "primary checkout has $DIRTY uncommitted file(s)"
    printf '%s\n' "$DIRTY_OUT" | head -10 | sed 's/^/         /'
    note "  commit, stash, or discard these before another session merges over them"
  else
    ok "primary checkout is clean"
  fi
fi

# --- 4. Stale-base surface ---------------------------------------------------
# A clean result requires the cached tracking ref to equal the SHA observed live.
# If it differs, fetch first; otherwise even the ahead/behind calculation is
# answering a question about an obsolete remote state.
if [ -n "$DEFAULT" ]; then
  if [ "$HAS_ORIGIN" -eq 0 ]; then
    note "no origin remote — live base freshness has no remote surface"
  elif [ "$REMOTE_QUERY_OK" -ne 1 ] || [ -z "$LIVE_DEFAULT_SHA" ]; then
    : # The live-remote failure was already recorded above.
  elif ! TRACKING_SHA="$(git rev-parse --verify "refs/remotes/origin/$DEFAULT" 2>/dev/null)"; then
    undet "no origin/$DEFAULT tracking ref — fetch before choosing a base"
  elif [ "$TRACKING_SHA" != "$LIVE_DEFAULT_SHA" ]; then
    undet "origin/$DEFAULT is stale: cached $TRACKING_SHA, live $LIVE_DEFAULT_SHA — fetch before creating"
  else
    COUNTS="$(git rev-list --left-right --count "origin/$DEFAULT...$DEFAULT" 2>/dev/null || true)"
    if [ -z "$COUNTS" ]; then
      undet "could not compare $DEFAULT against origin/$DEFAULT"
    else
      BEHIND="$(printf '%s' "$COUNTS" | awk '{print $1}')"
      AHEAD="$(printf '%s' "$COUNTS" | awk '{print $2}')"
      if [ "${AHEAD:-0}" -gt 0 ]; then
        warn "local $DEFAULT is $AHEAD commit(s) AHEAD of origin/$DEFAULT"
        note "  branching from origin/$DEFAULT would EXCLUDE them; branch from $DEFAULT instead"
      fi
      if [ "${BEHIND:-0}" -gt 0 ]; then
        warn "local $DEFAULT is $BEHIND commit(s) BEHIND origin/$DEFAULT"
        note "  branching from $DEFAULT would start from a stale base; fetch first"
      fi
      if [ "${AHEAD:-0}" -eq 0 ] && [ "${BEHIND:-0}" -eq 0 ]; then
        ok "$DEFAULT and origin/$DEFAULT match the LIVE origin SHA — either base is safe"
      fi
    fi
  fi
fi

# --- 5. Commits that exist on no remote, anywhere -----------------------------
# Durability, not liveness. These die with the disk, and with the worktree if
# its branch name is ever reused.
if ! REFS="$(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null)"; then
  undet "could not enumerate local branches — stranded commits NOT determined"
else
  STRANDED=0
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    out="$(git log --oneline "$ref" --not --remotes 2>/dev/null || true)"
    n="$(printf '%s' "$out" | grep -c . || true)"
    if [ "${n:-0}" -gt 0 ]; then
      warn "branch '$ref' has $n commit(s) on no remote (tip $(git rev-parse --short "$ref"))"
      STRANDED=$((STRANDED + 1))
    fi
  done <<< "$REFS"
  [ "$STRANDED" -eq 0 ] && ok "every local branch is represented on a remote"
fi

# --- 6. Will the worktree dirty the primary? ---------------------------------
# `.claude/worktrees/` is gitignored in SOME repos and not others. Where it is
# not, creating the worktree there leaves the primary permanently dirty — which
# poisons check 3 above into a standing false positive, and a check that always
# fires is a check that gets ignored.
if git -C "$PRIMARY" check-ignore -q .claude/worktrees 2>/dev/null; then
  ok ".claude/worktrees/ is gitignored — a worktree there will not dirty the primary"
else
  warn ".claude/worktrees/ is NOT gitignored in this repo"
  note "  add it to .gitignore (or .git/info/exclude) before creating, or the new"
  note "  worktree shows up as untracked and the dirty-primary check above becomes noise"
fi

# --- 7. Sibling presence (informational — presence is not liveness) ----------
OTHERS="$(git worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)"
if [ "${OTHERS:-1}" -gt 1 ]; then
  note "$((OTHERS - 1)) other worktree(s) exist:"
  git worktree list 2>/dev/null | sed 's/^/         /'
  note "  a worktree on disk does not prove a session is running, or that it is not"
fi

say ""
if [ "$BLOCKING" -gt 0 ]; then
  say "RESULT: BLOCKED — $BLOCKING blocking, $UNDETERMINED unverified, $WARNINGS warning(s)"
  exit 1
fi
if [ "$UNDETERMINED" -gt 0 ]; then
  say "RESULT: COULD NOT DETERMINE — $UNDETERMINED check(s) did not run, $WARNINGS warning(s)"
  say "        This is NOT 'clean'. A human decides whether to proceed."
  exit 2
fi
say "RESULT: clean ($WARNINGS warning(s)) — safe to create"
exit 0
