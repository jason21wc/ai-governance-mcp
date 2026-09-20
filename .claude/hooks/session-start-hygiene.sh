#!/usr/bin/env bash
# SessionStart: surface standing repo hygiene — the BACKSTOP seam (BACKLOG #200).
#
# The PRIMARY seam is pre-push Check 9: a close-out IS a push, and that is where the
# human is present, engaged, and in the literal act of closing out. This hook covers the
# one case pre-push cannot see: a hand-back that ends with NO push at all.
#
# Why SessionStart and not Stop/SessionEnd:
#   * SessionEnd runs async AFTER termination and CANNOT inject context — there is no
#     agent left to read it (EXECUTION-FRAMEWORK §7.2; deliberately not used).
#   * Stop is the only hook shape that can TRAP the user (its sole lever is
#     {"decision":"block"}), so it must fail silent — which is only affordable with a
#     backstop underneath it. This is that backstop. Stop remains the named escalation.
#   * Residue sat ~30 sessions. Catching it one session "late" is noise.
#
# SILENT WHEN CLEAN, always. A checker that chirps on a tidy repo gets tuned out, and
# this repo has the scar (T-169: a genuinely red CI job dismissed for days behind an
# "expected background" label). Never blocks; always exit 0.
#
# Bypass: HYGIENE_SKIP=1 (audit-logged).

set -uo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[ -f "$HOOK_DIR/lib/audit-bypass.sh" ] && . "$HOOK_DIR/lib/audit-bypass.sh"
INPUT=$(cat 2>/dev/null || echo '{}')

# Escape hatch FIRST — it must not depend on anything below it working.
if [ "${HYGIENE_SKIP:-}" = "1" ]; then
    if command -v audit_bypass >/dev/null 2>&1; then
        audit_bypass "session-start-hygiene" "HYGIENE_SKIP=1" "advisory-skip"
    fi
    exit 0
fi

# Shared resolver (BACKLOG #214). Hygiene is where this mattered most: every
# finding it reports (uncommitted files, unpushed commits, current branch) is
# CHECKOUT-VARIANT, so reading another checkout reports a DIFFERENT session's
# work as yours. Measured while fixing this: from the primary it announced
# "7 uncommitted file(s)" belonging to a concurrent session, while this worktree
# was clean and had unpushed commits of its own that went unmentioned.
# A missing lib degrades to silence rather than an unbound-variable death at the
# PROJECT_DIR assignment (this hook runs without `set -e`).
# shellcheck source=/dev/null
[ -f "$HOOK_DIR/lib/repo-root.sh" ] || exit 0
# shellcheck source=/dev/null
. "$HOOK_DIR/lib/repo-root.sh"
resolve_session_root "$INPUT"
PROJECT_DIR="${SESSION_ROOT:-$PWD}"

SCRIPT="$PROJECT_DIR/scripts/repo_hygiene.py"
[ -f "$SCRIPT" ] || exit 0   # not this project (or a scaffold copy) — stay silent

# repo_hygiene.py exits 1 to mean "findings present" — a RESULT, not an error. Capture
# the rc without letting it abort us. (rc 2/3 = the tool broke; a broken tool must never
# read as "the repo is clean", so we say so rather than staying silent.)
OUT=""
RC=0
OUT=$(python3 "$SCRIPT" --repo "$PROJECT_DIR" --min-severity warn 2>/dev/null) || RC=$?

# ---------------------------------------------------------------------------
# REFERENCE LIBRARY WATCH (BACKLOG #301)
# ---------------------------------------------------------------------------
# `capture_reference` writes a file and stops. Six entries accumulated untracked
# across sessions 267-272, four of them for days, and nothing noticed — the
# advisory half was fixed (the tool now names the library path in next_steps) but
# nothing CHECKED.
#
# Why this is worth surfacing only now: until session-272 the library had no
# remote, so "committed" still meant "one disk", and a watch would have been
# guarding a repo that could not be saved by watching it. #300 fixed the split
# destination and the library now has a private remote, so uncommitted-or-unpushed
# is a real, closable gap rather than a nag.
#
# Path resolution is deliberately a SHORT KNOWN LIST, not config parsing. The
# configured path lives in the MCP host's config (~/.claude.json et al.) and a
# SessionStart hook does not inherit the server's environment — that unresolvable
# lookup is exactly why #301 sat open. Two locations cover reality: the configured
# one and the default.
LIB_MSG=""
for _lib in "$HOME/dev-tools/reference-library" "$HOME/.ai-governance/reference-library"; do
    [ -d "$_lib" ] || continue
    _root=$(git -C "$_lib" rev-parse --show-toplevel 2>/dev/null) || continue
    _dirty=$(git -C "$_root" status --porcelain -- '*ref-*.md' 2>/dev/null | wc -l | tr -d ' ')
    # shellcheck disable=SC1083  # `@{push}`/`@{u}` is git revision syntax;
    # the braces are literal on purpose. Quoting or escaping them breaks the ref.
    _ahead=$(git -C "$_root" rev-list --count @{u}..HEAD 2>/dev/null || echo 0)
    if [ "${_dirty:-0}" -gt 0 ]; then
        LIB_MSG="Reference Library: ${_dirty} uncommitted entr$([ "$_dirty" = 1 ] && echo y || echo ies) in ${_root} — commit them; a capture that is not committed is not saved."
    elif [ "${_ahead:-0}" -gt 0 ]; then
        LIB_MSG="Reference Library: ${_ahead} commit(s) not pushed in ${_root} — push; committed-but-local is still one disk."
    fi
    break   # first existing library wins; do not double-report the same corpus
done
if [ -n "$LIB_MSG" ]; then
    OUT="${OUT:+$OUT
}$LIB_MSG"
fi

# rc 0 means no ALARMING finding — but the tool also emits a presence channel
# ("Another session is working here: <branch> (<path>)"), which is deliberately
# excluded from `clean` because a busy teammate is not a defect in your tree. That
# line is the ONE concurrency signal this project wants surfaced, and gating purely
# on rc discarded it: a presence-only report exits 0, so the message was written,
# returned, and thrown away here. Test at the library level passed; the system never
# showed it (session-268 code review, H2).
#
# Still silent when there is genuinely nothing to say — `$OUT` is empty on a clean
# repo with no siblings, which stays the common case.
if [ "$RC" -eq 0 ] && [ -z "$OUT" ]; then
    exit 0   # clean AND nothing to announce — the common case, and it stays quiet.
fi

if [ "$RC" -eq 0 ]; then
    # Presence only: no alarming finding, but the tool printed something — the
    # concurrency line. Falls through to the SHARED emitter below rather than
    # printing here, because a flat write is silently discarded for SessionStart.
    MSG="$OUT

(Checkout: $PROJECT_DIR — no action needed; another session is simply active.)"
elif [ "$RC" -gt 1 ]; then
    MSG="Repo hygiene check could not run (rc=$RC). This is NOT 'the repo is clean' — run: python3 scripts/repo_hygiene.py"
else
    MSG="$OUT

(Checkout: $PROJECT_DIR)
(Standing loose ends, computed from git/gh — not recalled from a memory file. This is why
'ACTION ON RESUME: nothing pending' is EARNED, not asserted. Mark a deliberate keep with a
'keep: <ref>' line in _ai-context/BACKLOG.md, next to the reason. Advisory — act when it fits.)"
fi

# The nested envelope is the contract: a flat {"additionalContext"} is silently DISCARDED
# by Claude Code for SessionStart.
python3 -c "
import json, sys
sys.stdout.write(json.dumps({'hookSpecificOutput': {
    'hookEventName': 'SessionStart',
    'additionalContext': sys.argv[1],
}}))
" "$MSG" 2>/dev/null || true

exit 0
