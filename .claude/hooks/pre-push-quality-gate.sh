#!/usr/bin/env bash
# PreToolUse hook — Pre-push quality gate
# Blocks git push unless tests were run and subagent reviews performed for risky changes.
#
# Per LEARNING-LOG: "advisory failed at 87%; structural blocking achieves near-100%"
# Hard mode from day one. Emergency skip: QUALITY_GATE_SKIP=true
#
# Checks:
#   0. Force-push attempts blocked (defense-in-depth — also denied at settings.json)
#   1. Tests run this session (pytest in transcript)
#   2. Subagent review for risky changes (core code files or new src files)
#   3. Governance content review for principle file changes
#   4. Completion checklist consulted (/completion-sequence-aigov skill invoked)
#   5. RETIRED (BACKLOG #202, session-252): multi-commit acknowledgment — never fired
#      (role-blind scanner, self-satisfying from its own deny message, ~6% vocab match);
#      its intent is covered by Check 6's range-wide scan. Number kept to avoid renumbering
#      references. The $RANGE-undeterminable guard it held was retained for Check 6.
#   6. Diff secret-scan — high-precision regex against AWS keys, OpenAI keys, GitHub
#      tokens, JWTs (replaces visual diff inspector function the user-mediated push
#      provided; per BACKLOG #140 §8.3.4 amendment 2026-04-26 enabling AI auto-push
#      on explicit user authorization). RUNS FIRST, ABOVE THE DOCS-ONLY HATCH — it
#      reads the diff, not the transcript, so nothing sequences it later, and below
#      the hatch it never saw a `.md`/`.json`-only push (BACKLOG #232b).
#   7. (WARN-only, advisory — not a blocking gate): TDD test-existence scan for new
#      src/*.py files. Bypass via TDD_TEST_EXISTENCE_SKIP=1; promotion to BLOCK is
#      event-driven via V-008 in .claude/skills/compliance-review/verification.md.
#   9. (WARN-only, session-251, BACKLOG #200): repo-hygiene inventory + firing log.
#   Escape hatch: docs-only changes skip review requirement (except governance + memory)
#
# Environment variables:
#   QUALITY_GATE_SKIP=true — Emergency skip (documented override, not silent bypass)
#   QUALITY_GATE_DEBUG=true — Enable stderr debug logging

set -euo pipefail

# Fail-closed on an unhandled error: exit 2 (deny), never exit 1 (which the
# harness reads as ALLOW). Required of every security-relevant hook by
# LEARNING-LOG 2026-04-16; these two gates never applied it.
#
# NECESSARY, NOT SUFFICIENT — measured session-272: this trap does NOT fire on a
# failed `source` or on an unbound variable under `set -u`. Those are handled by
# the guarded sources above and by `${VAR:-}` defaults. Full coverage would need
# `trap ... EXIT` with a transported-verdict flag, which changes the ALLOW path
# of every gate (BACKLOG #299 shipped both stages; this residual gap is accepted).
trap 'exit 2' ERR


HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# GUARDED — a failed `source` exits 1, which the harness reads as ALLOW, and
# `trap ... ERR` does NOT cover it (measured, bash 3.2). `lib/` is one symlink
# into the checkout, so moving the repo removes every library at once: the
# ordinary consequence of moving a directory, not an exotic case. BACKLOG #299.
if [ -r "$HOOK_DIR/lib/audit-bypass.sh" ]; then
    source "$HOOK_DIR/lib/audit-bypass.sh"
else
    echo "[pre-push-quality-gate] WARNING: lib/audit-bypass.sh missing — degraded, bypasses will not be audited" >&2
    audit_bypass() { :; }
fi

debug() {
  if [ "${QUALITY_GATE_DEBUG:-false}" = "true" ]; then
    echo "[quality-gate] $1" >&2
  fi
}

# ---------------------------------------------------------------------------
# emit_deny <reason> — the ONLY way this gate says no.
#
# Every deny used to be its own `python3 -c "...json..." 2>/dev/null || true`
# followed by `exit 0`. For a deny-by-assertion contract that is a silent
# fail-open: `|| true` catches a NONZERO exit, but a python3 that exits 0 having
# printed nothing leaves stdout empty, and empty stdout plus exit 0 IS AN ALLOW.
# The decision was correctly computed and then thrown away.
#
# Measured session-272 with a python3 that works generally but fails on the emit
# call: `git push --force origin main` returned rc 0 with 0 bytes. That discards
# the force-push block and, at Check 6, a DETECTED SECRET IN THE DIFF.
#
# The `_PY_OK` probe above narrows the window; it does not close it. It proves
# python3 worked ONCE, EARLIER. A python3 killed later — OOM under the memory
# pressure these gates exist for, a resource limit, a broken json module — passes
# the probe and then drops the verdict.
#
# So: capture, check, and fall back to exit 2, which the harness treats as a deny
# regardless of stdout. The fallback message is deliberately plain — without a
# working encoder we cannot emit the rich reason, and a terse deny beats a lost
# one. Same shape as pre-test-oom-gate.sh and pre-tool-content-security.sh; the
# push gate was the one that did not get it, and it holds the secret scanner.
emit_deny() {
    local _reason="$1" _json
    _json=$(python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$_reason" 2>/dev/null) || _json=""
    if [ -n "$_json" ]; then
        printf '%s' "$_json"
        exit 0
    fi
    printf '%s\n' "[pre-push-quality-gate] python3 could not emit the verdict; denying structurally. Reason: $_reason" >&2
    exit 2
}


# Read stdin (hook input JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

# THREE INDEPENDENT FULL-BYPASS CONDITIONS LIVED HERE. Measured session-272:
# with EITHER `jq` OR `python3` degraded, `git push --force origin main` returned
# rc 0 with 0 bytes — an ALLOW. That is the force-push block AND the diff secret
# scanner, both off, silently.
#
#   jq broken      -> COMMAND empty -> the detector finds no push -> exit 0
#   python3 broken -> the detector below IS python3; `if ! python3` treats 127 as
#                     "not a push" -> exit 0
#   python3 silent -> same, via exit 0 with no output
#
# The trap worth naming: "add a python3 fallback to the jq parse" fixes NOTHING
# for a broken python3, because the DETECTOR is itself python3. A contrarian
# caught that before it shipped.
#
# So: fall back to python3 for the parse, then health-check BOTH tools. If the
# toolchain is dead we cannot run a single check — and a push whose secret
# scanner did not run must not read as a pass. Detection then falls back to a
# SHELL-ONLY match on the raw payload (never python3, which is the tool under
# test), and a match denies.
#
# Scoped so it cannot brick: the deny is reachable only when the raw payload
# looks like a git push. Every other Bash call still exits at the detector below,
# untouched. Verified against 10 ordinary commands.
if [ -z "$COMMAND" ]; then
    COMMAND=$(echo "$INPUT" | python3 -c \
        "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
        2>/dev/null || echo "")
fi

# TWO TOOLS, TWO FLAGS. This was one flag named _TOOLCHAIN_OK, probed by piping
# python3 INTO grep — so a broken grep set the flag and the gate reported
# "python3 unusable". Worse, the degraded detector below was written as `grep -qE`
# and described in its own comment as "SHELL-ONLY ... never python3, which is the
# tool under test". grep is not shell-only; it is an external binary, and it was
# the OTHER binary the probe had just conflated. So a broken grep routed to a
# fallback implemented in the broken tool, and 13/15 force-pushes were ALLOWED.
#
# Reachability is ordinary, not exotic: user-writable directories precede
# /usr/bin on this PATH, so anything dropping a `grep` there shadows the system
# binary for every hook. Found by an independent audit of the Stage A diff — the
# same diff had added a grep health check to two OTHER gates for exactly this
# reason and left this one worse than it found it.
# THE PROBE CHECKS OUTPUT, NOT JUST EXIT STATUS. A python3 that exits 0 and
# prints nothing passes an exit-code-only probe, so _PY_OK stayed 1 and the
# python3-based detector below then found no push and allowed. Measured: 2/2
# force-pushes ALLOWED with a silent python3 while the probe reported healthy.
# Same defect as BACKLOG #298 — "produced nothing" is not "succeeded" — and it
# was reintroduced here at a fresh call site, which is why the cross-product
# matrix exists rather than a per-gate list.
_PY_OK=0
_PY_PROBE=$(printf 'probe' | python3 -c 'import sys; sys.stdout.write(sys.stdin.read())' 2>/dev/null) || _PY_PROBE=""
[ "$_PY_PROBE" = "probe" ] && _PY_OK=1

if [ "$_PY_OK" = "0" ]; then
    # Push detection with a BASH BUILTIN. `case` cannot go missing and cannot be
    # shadowed, which is the entire point: this path exists because an external
    # tool failed, so it must not depend on another one.
    #
    # Prefer the parsed COMMAND when a parser survived; fall back to the raw
    # payload when none did.
    _CAND="$COMMAND"
    [ -n "$_CAND" ] || _CAND="$INPUT"
    # Tighter than the old `git[^"]{0,80}push` regex, which also denied
    # `git help push`, `cat docs/git-push-policy.md` and
    # `git config --get remote.origin.pushurl` — 4 of 18 ordinary commands, in a
    # path whose only escape ALSO disables the secret scanner. Requiring the
    # adjacent form drops all four while keeping every real push.
    # `*"git "*" push "*` was here too and was too loose: it denied
    # `git commit -m "fix the push gate"`. The anti-brick test caught it.
    # `git push` adjacent, or `git <flags> push`, covers every real invocation.
    case "$_CAND" in
    *"git push"* | *"git -"*"push"*)
        printf '%s\n' "[pre-push-quality-gate] python3 unusable — no pre-push check can run" >&2
        printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"QUALITY GATE: python3 is unavailable or non-functional, so NOT ONE pre-push check ran — including the diff secret scanner. A gate that could not run must not read as a pass. Fix python3, push from your own shell, or set QUALITY_GATE_SKIP=true (audited)."}}'
        exit 0
        ;;
    esac
    debug "python3 degraded but not a push — allowing"
    exit 0
fi

# grep health, probed in the OPTION FORMS this gate actually uses and in BOTH
# directions. A grep that always exits 0 is as broken as one that never matches.
# Every grep-matched decision below routes through _match_regex so a dead grep
# degrades to the bash builtin instead of silently reporting "no match".
if grep -qE 'pro[b]e' 2>/dev/null <<< 'probe' \
   && ! grep -qE 'ZZ_AB[S]ENT_ZZ' 2>/dev/null <<< 'probe'; then
    _GREP_OK=1
else
    _GREP_OK=0
    printf '%s\n' "[quality-gate] grep unusable — matching with bash builtins" >&2
fi

_match_regex() {  # <haystack> <ERE>
    if [ "$_GREP_OK" = "1" ]; then
        grep -qE -- "$2" 2>/dev/null <<< "$1"
    else
        [[ "$1" =~ $2 ]]
    fi
}

# SCAN_COMMAND = the command with QUOTED-REGION CONTENTS removed, so token matchers see
# executable position only. A `-f` inside a commit message is not a force-push flag.
# (Live FP, 2026-07-13: `git commit -m "...bandit -r src/ -f txt..."` was blocked as a
# force-push. See lib/shell-scan.sh for the full root cause, n=3.)
# Fail-safe: on any failure the helper returns the ORIGINAL string, so the gate degrades
# to its previous over-blocking behaviour — never to under-blocking.
# GUARDED — a failed `source` exits 1, which the harness reads as ALLOW, and
# `trap ... ERR` does NOT cover it (measured, bash 3.2). `lib/` is one symlink
# into the checkout, so moving the repo removes every library at once: the
# ordinary consequence of moving a directory, not an exotic case. BACKLOG #299.
if [ -r "$HOOK_DIR/lib/shell-scan.sh" ]; then
    source "$HOOK_DIR/lib/shell-scan.sh"
else
    echo "[pre-push-quality-gate] WARNING: lib/shell-scan.sh missing — degraded, matching against the RAW command (over-blocks)" >&2
    strip_quoted_regions() { printf '%s' "$1"; }
fi
SCAN_COMMAND=$(strip_quoted_regions "$COMMAND")

# Only gate on git push commands.
#
# THE ANCHOR USED TO BE `^\s*git\s+push`, AND THAT BYPASSED THE ENTIRE GATE.
# Anything before `git` defeated a start-of-string anchor, so all three of these
# skipped ALL eleven checks — including the force-push block and the secret
# scanner — while doing exactly what the gate exists to catch:
#
#     git -C /some/path push --force
#     cd /tmp && git push --force
#     (git push --force origin main)
#
# Measured 2026-07-25 by mutation probe; the first form is a normal thing to type
# when working across worktrees, not an exotic evasion. This is also correlated
# with the settings.json `deny` rule, which anchors the same way — two layers
# sharing one assumption is not defence in depth.
#
# Matched against SCAN_COMMAND (quoted regions already stripped) so a commit
# message or an echo string mentioning a push is not treated as one. Detection
# is per COMMAND SEGMENT: `git` must open a segment, and `push` must be its
# subcommand after any global options (-C path, -c k=v, --git-dir=...).
if ! python3 -c '
import re, sys
cmd = sys.argv[1]
# Split on shell separators; a segment is a candidate command position.
for seg in re.split(r"(?:\|\||&&|[;&|()`]|\$\()", cmd):
    toks = seg.split()
    if not toks or toks[0] != "git":
        continue
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        # global options that take a separate value
        if toks[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            i += 2
        else:
            i += 1
    if i < len(toks) and toks[i] == "push":
        sys.exit(0)
sys.exit(1)
' "$SCAN_COMMAND" 2>/dev/null; then
    debug "Not a git push command, skipping"
    exit 0
fi

debug "Git push detected, running quality gate checks"

# Check 0: Force-push to main/master — defense-in-depth branch scoping.
#
# ENFORCEMENT-LAYER PRECEDENCE (as of 2026-08-08):
#   1. Anthropic auto-mode classifier — categorically blocks force-push (no
#      branch qualifier). This prevents ALL force-push from reaching any hook.
#   2. settings.json deny rules — also block force-push at the tool-permission
#      layer, before the hook runs.
#   3. This hook (HERE) — scopes force-push by branch: blocks main/master,
#      allows feature branches.
#
# Currently, layers 1 and 2 prevent force-push commands from ever reaching
# this code. This logic is DEFENSE-IN-DEPTH: it activates if either upstream
# layer gains branch-aware scoping (e.g. settings.json scoped to main only,
# or Anthropic adds per-branch classifiers). The code and tests (187 lines in
# tests/test_force_push_branch_scoping.py) are maintained for that eventuality.
#
# Two-step detection:
#   (a) Are force-push flags present? (regex on SCAN_COMMAND, quoted regions
#       already stripped — a `-f` in a commit message is not a flag.)
#   (b) Does the push target main/master? (Python parser extracts refspecs
#       from the command, same tokenization strategy as the push-detection
#       parser above. Falls back to current branch for implicit pushes.
#       Fails closed: parser failure → block.)
#
# _match_regex, not a bare `grep -qE`: an `if grep` collapses match(0) /
# no-match(1) / ERROR(2+) into true/false, so "grep could not run" read as
# "not a force-push" and this deny silently stopped existing. `\s` is spelled
# [[:space:]] because the same pattern is evaluated by bash's `[[ =~ ]]` on
# the fallback path, and BSD ERE does not understand `\s`.
# Flag detection guarded by tests/test_hook_shell_scan.py.
# Branch scoping guarded by tests/test_force_push_branch_scoping.py.
if _match_regex "$SCAN_COMMAND" '(--force([[:space:]]|$|=)|[[:space:]]-f([[:space:]]|$)|--force-with-lease)'; then
    debug "Force-push flags detected, checking target branch"
    _FORCE_CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
    [ -z "$_FORCE_CWD" ] && _FORCE_CWD="$PWD"

    _FORCE_TARGET=$(python3 -c '
import re, sys
cmd = sys.argv[1]
for seg in re.split(r"(?:\|\||&&|[;&|()`]|\$\()", cmd):
    toks = seg.split()
    if not toks or toks[0] != "git":
        continue
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        if toks[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            i += 2
        else:
            i += 1
    if i < len(toks) and toks[i] == "push":
        j = i + 1
        # skip push-specific flags
        while j < len(toks) and toks[j].startswith("-"):
            if toks[j] in ("--repo", "--push-option", "-o", "--receive-pack", "--exec"):
                j += 2
            else:
                j += 1
        # j = remote (if any), j+1.. = refspecs
        refspecs = toks[j+1:] if j+1 < len(toks) else []
        if not refspecs:
            print("implicit")
            sys.exit(0)
        for ref in refspecs:
            target = ref.split(":", 1)[1] if ":" in ref else ref
            if target in ("main", "master"):
                print("trunk")
                sys.exit(0)
        print("feature")
        sys.exit(0)
print("unknown")
' "$SCAN_COMMAND" 2>/dev/null || echo "unknown")

    case "$_FORCE_TARGET" in
        trunk)
            debug "Force-push targets main/master — blocking"
            emit_deny "QUALITY GATE: Force-push to main/master blocked (defense-in-depth for trunk protection). Force-push to feature branches is allowed."
            ;;
        feature)
            debug "Force-push to feature branch — allowed"
            ;;
        implicit)
            _CURRENT_BRANCH=$(git -C "$_FORCE_CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
            if [ "$_CURRENT_BRANCH" = "main" ] || [ "$_CURRENT_BRANCH" = "master" ]; then
                debug "Force-push from trunk (implicit target) — blocking"
                emit_deny "QUALITY GATE: Force-push blocked — no explicit branch and current branch is $_CURRENT_BRANCH. Specify the target branch explicitly, or push from a feature branch."
            else
                debug "Force-push to feature branch ($_CURRENT_BRANCH, implicit) — allowed"
            fi
            ;;
        *)
            debug "Force-push target undeterminable — fail-closed"
            emit_deny "QUALITY GATE: Force-push blocked — could not determine target branch (fail-closed). Specify the branch explicitly or set QUALITY_GATE_SKIP=true."
            ;;
    esac
fi

# Emergency skip
if [ "${QUALITY_GATE_SKIP:-false}" = "true" ]; then
    audit_bypass "pre-push-quality-gate" "QUALITY_GATE_SKIP=true" "emergency-skip"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ QUALITY GATE SKIPPED via QUALITY_GATE_SKIP=true"}}'
    exit 0
fi

# Get transcript path from hook input
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
    debug "Transcript not available, fail-closed"
    emit_deny "QUALITY GATE: Transcript unavailable — cannot verify pre-push checks. Set QUALITY_GATE_SKIP=true to override."
fi

# Resolve the PUSHING worktree — every check below must validate the tree the push
# actually comes from, not whichever tree this script file happens to live in.
#
# Claude Code invokes hooks by their `$CLAUDE_PROJECT_DIR` path, so `$0` (and therefore
# HOOK_DIR) always points at the PRIMARY checkout even when the push originates in a
# sibling worktree. Anything resolved from HOOK_DIR — and any bare `git` call relying on
# ambient process cwd — can silently validate the wrong tree. Observed 2026-07-24: a
# concurrent session's UNCOMMITTED work in the primary checkout made Check 8 deny an
# unrelated worktree's push, and the only escape (QUALITY_GATE_SKIP=true) exits at the
# top of this file and disables the SECRET SCANNER — precisely the footgun the Check 5
# retirement note warns about training. Same structural class as LEARNING-LOG 2026-07-12
# "The SessionStart Cadence Hook Reads the PRIMARY Checkout, Not Your Worktree".
#
# Resolution order is deliberate: the tool call's own cwd first, then the process cwd,
# and `CLAUDE_PROJECT_DIR` LAST. (Session-262 correction: that variable is NOT reliably
# the primary checkout — measured across 103 hook firings it resolved to three different
# worktrees and the primary. It is simply unreliable, which is a stronger reason to rank
# it last, not a weaker one. Canonical resolver + the full rationale: lib/repo-root.sh;
# this copy predates it and is deliberately left standalone because a BLOCKING gate
# should not gain a new source-time dependency — see BACKLOG.) It is the
# wrong answer in exactly the case this exists to fix. It remains as a final fallback so
# an unresolvable root degrades to the previous behaviour rather than to no gate at all.
PUSH_CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
[ -z "$PUSH_CWD" ] && PUSH_CWD="$PWD"
REPO_ROOT=$(git -C "$PUSH_CWD" rev-parse --show-toplevel 2>/dev/null || echo "")
[ -z "$REPO_ROOT" ] && REPO_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
debug "push cwd=$PUSH_CWD -> repo root=$REPO_ROOT (hook dir=$HOOK_DIR)"

# Determine commit-range for diff/count operations.
# Try @{push} first (tracks upstream), then origin/main..HEAD, then HEAD~1..HEAD.
# Factored as RANGE so all checks (CHANGED_FILES, NEW_SRC_FILES, Check 6 secret-scan)
# share the same fallback chain. Fail-closed: if no range can be
# determined, RANGE stays empty and downstream checks treat that as "scan range
# undeterminable" rather than silently scanning nothing.
# shellcheck disable=SC1083  # `@{push}`/`@{u}` is git revision syntax;
# the braces are literal on purpose. Quoting or escaping them breaks the ref.
if git -C "$REPO_ROOT" rev-parse @{push} >/dev/null 2>&1; then
    RANGE="@{push}..HEAD"
elif git -C "$REPO_ROOT" rev-parse origin/main >/dev/null 2>&1; then
    RANGE="origin/main..HEAD"
elif git -C "$REPO_ROOT" rev-parse HEAD~1 >/dev/null 2>&1; then
    RANGE="HEAD~1..HEAD"
else
    RANGE=""
fi
debug "Commit range: ${RANGE:-(undeterminable)}"

CHANGED_FILES=""
if [ -n "$RANGE" ]; then
    CHANGED_FILES=$(git -C "$REPO_ROOT" diff --name-only $RANGE 2>/dev/null || echo "")
fi

# Range-undeterminable guard — BEFORE the empty-CHANGED_FILES exit (#232a).
# An empty RANGE means we could not compute the commit range, so CHANGED_FILES
# is empty by construction (line 357), not because nothing changed. A range we
# cannot compute means we cannot scan the diff, and that must WARN, not
# silently no-op (fail-closed, per BACKLOG #140 §8.3.4).
if [ -z "$RANGE" ]; then
    debug "Range undeterminable — secret-scan cannot run; fail-closed"
    ISSUES="${ISSUES}Push range undeterminable (no @{push}, no origin/main, no HEAD~1). Cannot run the diff secret-scan. Verify upstream branch tracking is set, or set QUALITY_GATE_SKIP=true to override. "
fi

if [ -z "$CHANGED_FILES" ] && [ -n "$RANGE" ]; then
    debug "No changed files detected, allowing push"
    exit 0
fi

debug "Changed files: $(echo "$CHANGED_FILES" | tr '\n' ' ')"

# Check 6: Diff secret-scan — high-precision regex against AWS keys, OpenAI keys,
# Anthropic keys, GitHub tokens, JWT-shaped tokens, PEM private keys. Replaces the
# visual diff inspection the user-mediated push used to provide (per BACKLOG #140
# §8.3.4 amendment 2026-04-26: once the user stops typing `! git push`, nobody is
# eyeballing the diff before it leaves the machine).
#
# IT RUNS HERE — ABOVE THE DOCS-ONLY ESCAPE HATCH — AND THAT POSITION *IS* THE CHECK.
# It used to sit ~330 lines below the hatch, so any push whose changed files were all
# `.md`/`.json` exited at the hatch and shipped UNSCANNED. Measured 2026-07-25 by
# mutation probe (BACKLOG #232b): the SAME AWS key denied in `leak.py` and ALLOWED in
# `creds.json`. `.json` is exactly where a credential lives — service-account blobs,
# `*.credentials.json`, an MCP config with an inline token — so the blind spot covered
# the likeliest case, not an exotic one.
#
# Nothing ever forced the old position: this check reads the DIFF. Unlike Checks 1/2/3/4
# it needs no transcript and no subagent review, so it has zero dependency on anything
# the hatch guards. The hatch's governance-file and memory-file exemptions below are
# untouched — this check is simply upstream of all of them.
#
# It also sits above Checks 8/10/11 deliberately. Those deny on count drift, index
# identity and known-red records; a cheap cosmetic deny that pre-empts a credential
# report is the same masking failure this file keeps re-learning in a new costume
# (see the repeated "…and that flag also disables the secret scanner" notes below).
# The strongest check reports first.
#
# DENIES INLINE instead of appending to $ISSUES: $ISSUES is declared below the hatch and
# only reported at the end of the file, so an accumulating check cannot live up here.
# This matches Checks 8/10/11, which each emit their own decision. Accepted consequence:
# a push carrying BOTH a credential and (say) an unrun test suite now reports the
# credential alone — the right priority order, and the rest surfaces on the retry.
# The exit ALSO skips the WARN-only Checks 7 and 9, including Check 9's hygiene firing
# log. That is not new behaviour introduced here — every early exit in this file
# (Checks 8/10/11 and the docs-only hatch itself) already skips them, so the firing log
# was never written on all pushes and its ">=2 consecutive" escalation rule is already
# computed over an incomplete record. Naming it rather than fixing it: log continuity
# spans five exits, so patching only this one would be the symptom, not the cause.
#
# Still fail-closed on an undeterminable range, and still guarded below (Check 5's
# retained range guard). False positives are acceptable here — pre-push, recoverable by
# amend. Bypass: QUALITY_GATE_SKIP=true, which exits at the top of this file.
SECRET_PATTERNS='AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9_-]{40,}|ghp_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{20,}|gho_[a-zA-Z0-9]{20,}|ghs_[a-zA-Z0-9]{20,}|eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}|-----BEGIN [A-Z]+ PRIVATE KEY-----'
SECRETS_FOUND=""
if [ -n "$RANGE" ]; then
    SECRETS_FOUND=$(git -C "$REPO_ROOT" diff $RANGE 2>/dev/null | grep -E '^[+]' | grep -E "$SECRET_PATTERNS" 2>/dev/null | sed -n '1,3p' || true)
fi
if [ -n "$SECRETS_FOUND" ]; then
    # This used to feed `head -1` from `echo`. Under pipefail, head's early success
    # could SIGPIPE echo and kill the hook after the secret was detected but before
    # the deny was emitted. Measured 2026-07-25 with large matched lines. The current
    # `sed -n 1p` reads the whole here-string, so no producer is closed early; the
    # class guard in scripts/check_pipefail_early_consumers.py prevents regression.
    SECRETS_PREVIEW=$(sed -n '1p' <<< "$SECRETS_FOUND" | cut -c1-80 | tr -d '\n' || true)
    debug "Potential secret detected: $SECRETS_PREVIEW"
    emit_deny "QUALITY GATE: Potential secret/credential detected in diff (preview: ${SECRETS_PREVIEW}...). Review and redact before pushing — use  git rebase -i  to amend, or  git filter-repo  if it already landed. If false positive, set QUALITY_GATE_SKIP=true."
fi

# Check 13: unresolved merge-conflict markers in tracked files.
#
# IT SCANS THE TREE, NOT THE DIFF — and that choice *is* the check. The incident
# that produced it (session-301 root-cause): markers entered at 6ff104a, a merge of
# origin/main into a topic branch, and then rode along in five further commits. By
# the time session-300 pushed 8fdafcc..5fe553b, BOTH ends of the range already
# contained them, so they are not added lines and a Check-6-style diff scan reports
# clean. Corruption that predates the range is exactly what a diff cannot see.
#
# IT ALSO RUNS ABOVE THE DOCS-ONLY ESCAPE HATCH, for the same reason Check 6 does.
# The markers landed in `_ai-context/SESSION-STATE.md` — a memory file, on a push
# whose changed files were all `.md`. Placed below the hatch this check would have
# been a no-op against the very defect it exists to prevent.
#
# MATCHES ONLY `<<<<<<< ` AND `>>>>>>> `, NEVER A BARE `=======`. A line of equals
# signs is a valid setext heading underline in Markdown, so keying on it can fire on
# correct prose, and a gate that fires on correct work trains its own bypass.
# CITATION CORRECTED (Compliance Review #18): this comment first read "(the V-004
# arc)", which is wrong and was inherited from a shorthand that has drifted across
# this repo. V-004 records the OPPOSITE lesson — an *advisory* gate that scored 50%
# compliance over 5 sessions, hit its failure threshold, and was escalated to a hard
# PreToolUse hook. The false-positive argument stands on its own merits and is left
# uncited rather than mis-cited: its original grounding (the LEARNING-LOG entry
# "False Positives Train You to Ignore" and BACKLOG #253) was pruned by session-273,
# which is precisely how the shorthand came loose from its anchor.
# Measured 2026-08-09: this repo
# currently has ZERO such lines, so the exposure is latent rather than live — the
# marker is dropped because it buys no detection, not because it is firing today.
# Git always emits all three markers together, so two of the three suffice.
CONFLICT_MARKERS=$(git -C "$REPO_ROOT" grep -I -n -E '^(<<<<<<<|>>>>>>>) ' -- . 2>/dev/null | sed -n '1,3p' || true)
if [ -n "$CONFLICT_MARKERS" ]; then
    MARKER_PREVIEW=$(sed -n '1p' <<< "$CONFLICT_MARKERS" | cut -c1-100 | tr -d '\n' || true)
    debug "Merge-conflict markers detected: $MARKER_PREVIEW"
    emit_deny "QUALITY GATE: unresolved merge-conflict markers in tracked files (${MARKER_PREVIEW}). A botched conflict resolution is about to become shared history — resolve the file and amend. Find them all with:  git grep -n -E '^(<<<<<<<|>>>>>>>) '  . If false positive, set QUALITY_GATE_SKIP=true."
fi

# Check 13b: a BACKLOG entry that `merge=union` silently resurrected (BACKLOG #348).
#
# SIBLING OF CHECK 13, AND ITS BLIND SPOT. Check 13 finds conflicts git could not
# resolve. This finds the opposite failure: a merge git resolved TOO well. `merge=union`
# keeps both sides' lines, so when one session closes an item (a full deletion, per
# BACKLOG's own procedure) while another edits it, the edit wins and the closure is
# undone — with NO markers, because union never conflicts. Check 13 is structurally
# blind to it, and so is check.sh's `backlog hygiene`, whose assertions are all
# single-snapshot greps: in the working tree a resurrected entry and one that was
# never closed look exactly the same. Only history separates them.
#
# THIS ARM IS DEFENCE-IN-DEPTH, NOT THE AUTHORITATIVE ONE (corrected 2026-08-24).
# It was originally the ONLY invocation, which made a guard against a repository-wide
# hazard fire only for Claude — a Codex or ordinary-shell push bypassed it completely.
# That is the identical host-coupling defect as the memory size guard, committed in the
# same change that fixed the memory size guard. The authoritative invocation is now the
# git pre-push stage in `.pre-commit-config.yaml`, which fires for any pusher and reads
# the range ACTUALLY being published from PRE_COMMIT_FROM_REF/PRE_COMMIT_TO_REF.
#
# Kept here anyway because it fires earlier and with better messaging for the host most
# pushes come from. Note its range is weaker: $RANGE prefers `@{push}..HEAD`, the topic
# branch's own upstream, which is EMPTY for a branch already pushed to its upstream even
# while publication to the default branch is pending — and the empty-CHANGED_FILES exit
# above returns before this point in exactly that case. Do not rely on this arm alone.
#
# WHY NOT IN check.sh. The test needs a merge commit with both parents. Keyed
# on "HEAD is a merge" it would almost never fire: measured against logs/check-runs.jsonl,
# of 22 BACKLOG-touching merges only 2 had a check.sh run at the merge commit. Close-out
# refreshes and then commits the snapshot ON TOP, so HEAD is a merge only in a window
# nobody runs check.sh in. $RANGE is the seam that sees the merge — the same reason
# Check 13 scans the tree rather than the diff.
#
# SCOPED TO THE PUSH RANGE ON PURPOSE. Over full history this fires on 8ff6293
# (resurrected #206b, 2026-07), which was found and re-removed by f095366 and is
# settled. A gate that fires forever on a closed incident trains its own bypass.
#
# rc 1 = found; rc 3 = could-not-run (unreadable BACKLOG at an endpoint, >2 parents,
# multiple merge-bases) and is NOT a pass; rc 2 = usage/git error.
RESURRECT="$REPO_ROOT/scripts/check_backlog_resurrection.py"
if [ "${QUALITY_GATE_SKIP:-false}" != "true" ] && [ -f "$RESURRECT" ] && [ -n "$RANGE" ]; then
    RES_RC=0
    RES_OUT=$(python3 "$RESURRECT" --repo "$REPO_ROOT" --range "$RANGE" 2>&1) || RES_RC=$?
    if [ "$RES_RC" -eq 1 ]; then
        debug "Backlog resurrection: $RES_OUT"
        emit_deny "QUALITY GATE: $(sed -n '1,2p' <<< "$RES_OUT" | tr '\n' ' ') If this closure was meant to be undone, say so in the commit message; otherwise re-delete the entry. If false positive, set QUALITY_GATE_SKIP=true."
    elif [ "$RES_RC" -eq 3 ]; then
        # Could-not-run is not a pass, but it is also not a reason to block a push:
        # surfaced so it is visible rather than absorbed.
        printf '%s\n' "NOTE: backlog resurrection check could not run — $RES_OUT" >&2
    fi
fi

# Check 8: SESSION-STATE Quick Reference generated count block must match source
# (BACKLOG #70 — derive-the-derivable SSOT). Runs BEFORE the docs-only escape hatch
# because a skill/agent/index change is itself a docs-only change that shifts the
# counts, so the block can go stale on a push the other checks would wave through.
# Single guard surface (pre-push only, not CI) per proportional-rigor. Skipped when
# the generator is absent (scaffold copies). Bypass: QUALITY_GATE_SKIP=true.
# Resolved from the PUSHING worktree, not HOOK_DIR: the generator derives its own repo
# root from __file__, so running the primary checkout's copy validates the primary
# checkout no matter which tree is being pushed. HOOK_DIR stays as the fallback for
# scaffold copies whose tree has no scripts/ directory.
GENQR="$REPO_ROOT/scripts/gen_quick_reference.py"
[ -f "$GENQR" ] || GENQR="$HOOK_DIR/../../scripts/gen_quick_reference.py"
if [ "${QUALITY_GATE_SKIP:-false}" != "true" ] && [ -f "$GENQR" ]; then
    # Distinguish genuine drift (rc 1 → "run the generator") from a structural
    # failure (rc 2 usage / rc 3 missing-or-malformed index / partial scaffold),
    # for which that advice would loop the user. set -e-safe capture: init 0,
    # capture rc only on non-zero.
    QR_RC=0
    QR_OUT=$(python3 "$GENQR" --check 2>&1) || QR_RC=$?
    if [ "$QR_RC" -eq 1 ]; then
        debug "Quick Reference / README count drift: $QR_OUT"
        # rc 1 covers TWO distinct drifts — the generated SESSION-STATE count block AND
        # the hand-curated README domain table — and only the first is fixed by running
        # the generator. Naming just that one sent a real 2026-07-24 push in a circle
        # ("run the generator" → "already current" → still denied), so report what the
        # checker ACTUALLY said instead of asserting which drift it was.
        QR_PREVIEW=$(printf '%s' "$QR_OUT" | tr '\n' ' ' | cut -c1-240)
        emit_deny "QUALITY GATE: derived-count drift (BACKLOG #70 SSOT) — ${QR_PREVIEW} . If the STATUS.md generated block drifted, run  python scripts/gen_quick_reference.py  and re-commit STATUS.md; if the README domain table drifted, edit those integers by hand (the generator never writes them). Bypass: QUALITY_GATE_SKIP=true."
    elif [ "$QR_RC" -ne 0 ]; then
        debug "Quick Reference count check errored (rc=$QR_RC), not drift"
        QR_PREVIEW=$(sed -n '1p' <<< "$QR_OUT" | cut -c1-160)
        emit_deny "QUALITY GATE: the SESSION-STATE quick-ref count check could not run (NOT a drift — likely a missing/malformed index or partial scaffold): ${QR_PREVIEW} . Fix the underlying error, or set QUALITY_GATE_SKIP=true to override."
    fi
fi

# Check 10: index row-identity probe — only when index/ is in the changed set.
#
# BACKLOG #219. The row-misattribution defect reached origin/main and served every
# query against the wrong document for six days. A CI job built for exactly this
# class (`Index Retrieval Behavior`) existed the whole time and never ran: CI fails
# in 3-4s on the exhausted Actions quota (T-169), so its red was indistinguishable
# from the expected red. A guard behind a dead runner is not a guard.
#
# This is the general lesson, not just this bug: while CI is unavailable, any guard
# that only exists in CI is advisory. The default test suite now covers this too
# (tests/test_index_row_identity.py), but a docs-only push carrying a rebuilt index
# does not require a test run, so the pre-push surface is the one that always sees it.
#
# Model-free and O(n): it reads stamped ids and matrix shapes, no embedding model.
# Fails SAFE — any structural problem reading the artifacts skips the check rather
# than blocking a push (over-blocking here would train a QUALITY_GATE_SKIP habit,
# and that same flag also disables the secret scanner). Detect the changed path with
# shell builtins: feeding `grep -q` from a pipeline lets its early success SIGPIPE
# the producer under pipefail, turning "index changed" into false.
INDEX_CHANGED=false
while IFS= read -r _changed_path; do
    case "$_changed_path" in index/*) INDEX_CHANGED=true; break ;; esac
done <<< "$CHANGED_FILES"
if [ "${QUALITY_GATE_SKIP:-false}" != "true" ] \
   && [ "$INDEX_CHANGED" = "true" ]; then
    IDX_RC=0
    IDX_OUT=$(cd "$REPO_ROOT" && python3 -c '
import json, sys, pathlib
try:
    import numpy as np
except ImportError:
    sys.exit(0)  # no numpy in this env — not our call to block the push
root = pathlib.Path("index")
jp, cp, dp = root/"global_index.json", root/"content_embeddings.npy", root/"domain_embeddings.npy"
if not jp.exists() or not cp.exists():
    sys.exit(0)
try:
    data = json.loads(jp.read_text())
    n = np.load(cp, mmap_mode="r").shape[0]
except Exception:
    sys.exit(0)  # unreadable artifacts are Check 8 territory, not this probe
# Everything below runs inside try/except: an unexpected artifact SHAPE
# (domains not a mapping, an item that is not a dict, domain_configs not a
# list) must SKIP, never deny. Over-blocking here trains QUALITY_GATE_SKIP,
# which also disables the secret scanner — a strictly worse outcome than
# missing one broken index. Only a computed mismatch exits 1.
verdict = None
try:
    ids = [it.get("embedding_id")
           for dom in data.get("domains", {}).values()
           for key in ("principles", "methods", "references")
           for it in dom.get(key, [])]
    stamped = sorted(x for x in ids if x is not None)
    if stamped and stamped != list(range(n)):
        verdict = (f"content embedding_ids are not a bijection onto [0,{n}): "
                   f"{len(stamped)} stamped id(s), {len(set(stamped))} distinct")
    if verdict is None and dp.exists():
        dn = np.load(dp, mmap_mode="r").shape[0]
        dids = sorted(c.get("embedding_id") for c in data.get("domain_configs", [])
                      if c.get("embedding_id") is not None)
        if dids and dids != list(range(dn)):
            verdict = (f"domain_configs embedding_ids are not a bijection onto "
                       f"[0,{dn}) — domain routing would score against the wrong "
                       f"descriptions")
except Exception:
    sys.exit(0)
if verdict:
    print(verdict)
    sys.exit(1)
' 2>&1) || IDX_RC=$?
    if [ "$IDX_RC" -eq 1 ]; then
        debug "Index row-identity probe failed: $IDX_OUT"
        IDX_PREVIEW=$(printf '%s' "$IDX_OUT" | tr '\n' ' ' | cut -c1-240)
        emit_deny "QUALITY GATE: the committed index cannot say which item owns which embedding row (BACKLOG #219) — ${IDX_PREVIEW} . Retrieval would score queries against the WRONG documents while looking healthy. Rebuild with  python -m ai_governance_mcp.extractor  . The index is NOT committed (session-268) — it is a build artifact derived from documents/ + your reference library, so it is user-specific; do not re-add it to git. Bypass: QUALITY_GATE_SKIP=true."
    fi
fi

# NON_DOC_FILES — computed here (above Check 11/12) because Check 12 gates on it.
# Also used by the docs-only escape hatch (below) and Check 1.
NON_DOC_FILES=$(echo "$CHANGED_FILES" | grep -v -E '\.(md|json)$' | grep -v 'tests/benchmarks/' || true)

# Check 11: never push a KNOWN-RED local check run.
#
# Deliberately NOT "you must have run check.sh". That would add friction to every
# push and friction is how a gate trains its own bypass — the QUALITY_GATE_SKIP
# lesson, which also disables the secret scanner. Absence of a run record is not
# an offence here.
#
# What IS an offence: a run record for THIS commit that reported failures, and a
# push anyway. It closes the loop the run log exists for — observation that
# nothing reads is the defect this whole layer was built to end.
#
# NOT false-positive-proof, and the first draft of this comment said it was.
# The record is keyed on the commit, not the tree: run check.sh red at HEAD, fix
# the working tree WITHOUT a new commit, and the stale red record still denies.
# Recovery is re-running check.sh (which appends a fresh record) or the audited
# bypass. Keyed on the FULL sha — `--short` abbreviation length is dynamic, so a
# record written before the repo crossed a length threshold would silently stop
# matching and the gate would fail open without saying so.
#
# THIS CHECK SHIPPED DEAD AND NOTHING NOTICED. The rename to HEAD_SHA missed the
# use site, leaving an unbound variable under `set -u`. It did not crash the hook:
# the reference sits inside `$(...) 2>/dev/null || echo ""`, so the subshell died,
# stderr was swallowed, and LAST_RED was empty on every push — a check that always
# allows, which is indistinguishable from a check that found nothing. Found by
# mutation probe, not by review. Hence the test below it: a check with no test
# asserting it can DENY is a check that cannot be shown to work.
if [ "${QUALITY_GATE_SKIP:-false}" != "true" ] && [ -f "$REPO_ROOT/logs/check-runs.jsonl" ]; then
    HEAD_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "")
    if [ -n "$HEAD_SHA" ]; then
        LAST_RED=$(python3 -c '
import json, sys
sha, path = sys.argv[1], sys.argv[2]
worst = None
try:
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("commit") == sha:
            worst = rec          # last record for this commit wins
except OSError:
    sys.exit(0)
if worst and worst.get("fail", 0) > 0:
    failed = [c.get("check") for c in worst.get("checks", []) if c.get("status") == "fail"]
    print(f'"'"'{worst["fail"]} failing: {", ".join(x for x in failed if x)[:120]}'"'"')
' "$HEAD_SHA" "$REPO_ROOT/logs/check-runs.jsonl" 2>/dev/null || echo "")
        if [ -n "$LAST_RED" ]; then
            debug "Known-red local check run at HEAD: $LAST_RED"
            emit_deny "QUALITY GATE: your own local check run at this commit reported failures and you are pushing anyway — ${LAST_RED} . Re-run  bash scripts/check.sh  and fix, or set QUALITY_GATE_SKIP=true to override (audited)."
        fi
    fi
fi

# Check 12 (WARN-only): no check.sh run record at HEAD.
#
# Pairs with Check 11 (known-red blocks). Check 11 blocks when you KNOW the run
# failed; Check 12 warns when you DON'T KNOW because you never ran it. Together
# they close the loop: running check.sh is guided (completion-sequence skill
# step 5), observed (JSONL record), and surfaced (this WARN).
#
# WARN, not BLOCK — per the V-004 advisory→structural arc. Phase 1 advisory
# improvements (completion-sequence instruction, verification chain) should be
# measured for effectiveness (V-014) before any promotion to BLOCK. A gate that
# blocks on "you didn't run check.sh" trains QUALITY_GATE_SKIP=true, which
# disables the secret scanner (Check 6). Advisory first, evidence second.
#
# Gated on NON_DOC_FILES: doc-only pushes don't need a full check.sh run.
if [ "${QUALITY_GATE_SKIP:-false}" != "true" ] && [ -n "$NON_DOC_FILES" ]; then
    CHECK12_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "")
    if [ -n "$CHECK12_SHA" ]; then
        HAS_RECORD="false"
        if [ -f "$REPO_ROOT/logs/check-runs.jsonl" ]; then
            HAS_RECORD=$(python3 -c '
import json, sys
sha, path = sys.argv[1], sys.argv[2]
try:
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("commit") == sha:
            print("true")
            sys.exit(0)
except OSError:
    pass
print("false")
' "$CHECK12_SHA" "$REPO_ROOT/logs/check-runs.jsonl" 2>/dev/null || echo "false")
        fi
        if [ "$HAS_RECORD" = "false" ]; then
            echo "[check-run-evidence] WARN — no check.sh run record at HEAD ($CHECK12_SHA). Run  bash scripts/check.sh  before pushing (advisory; V-014 tracking)." >&2
        fi
    fi
fi

# Governance files require subagent review (contrarian/coherence/validator).
#
# BACKLOG #221: this used to match only `constitution.md` and the `title-N-*` family
# — a SHAPE heuristic. But the corpus's core documents are NAMED, not shaped:
# `rules-of-procedure.md` (the framework's binding procedural law), `ai-instructions.md`
# and `INFLUENCES.md` all fell through, and none matched MEMORY_FILES either, so a push
# touching only those got ordinary-doc treatment and Check 3 never fired. The file where
# session-264 found a FABRICATED governance audit ID was one of them. Named documents get
# an explicit allowlist; the title-N family keeps its pattern because it is genuinely open-
# ended. `tests/test_hooks.py::TestGovernanceFileMatcher` derives the expected set from
# the corpus, so the next core document added fails loudly instead of silently escaping.
GOVERNANCE_FILES=$(echo "$CHANGED_FILES" | grep -E '(^|/)(constitution|rules-of-procedure|ai-instructions|failure-mode-registry|INFLUENCES)\.md$|(^|/)title-[0-9]+-[a-z][-a-z]*\.md$' | grep -v '\-cfr\.md' || true)
debug "Governance files: $(echo "$GOVERNANCE_FILES" | tr '\n' ' ')"

# Memory-file pushes are CLOSE-OUT pushes, and close-outs are exactly where housekeeping
# residue rides in. Session-250 measured it: every commit whose subject contains
# "close-out" is docs-only (dac55da, a2479a5, 9ba4eea, 6267162 — all zero non-doc files),
# so the one push where the aperture sweep matters most was structurally the one push
# that took the hatch below and never demanded it. Both layouts (_ai-context/ and the
# grandfathered root) are matched. (BACKLOG #200)
MEMORY_FILES=$(echo "$CHANGED_FILES" | grep -E '^(_ai-context/)?(SESSION-STATE|BACKLOG|LEARNING-LOG|PROJECT-MEMORY|OPERATIONS)\.md$' || true)
debug "Memory files: $(echo "$MEMORY_FILES" | tr '\n' ' ')"

# Escape hatch: docs-only changes (only .md files, .json config, or benchmark files)
# BUT governance principle files are NOT exempt — they require review
# AND memory files are NOT exempt — they are the close-out signature (above)
# (NON_DOC_FILES computed above Check 11/12, which gates on it.)
if [ -z "$NON_DOC_FILES" ] && [ -z "$GOVERNANCE_FILES" ] && [ -z "$MEMORY_FILES" ]; then
    debug "Docs/config-only changes (no governance/memory content), skipping review requirement"
    exit 0
fi

ISSUES=""

# Check 1: Were tests run this session?
# Gated on NON_DOC_FILES: narrowing the hatch must not start demanding `pytest` for a
# SESSION-STATE edit. (The Check 5 that once shared this gate was retired — BACKLOG #202.)
if [ -n "$NON_DOC_FILES" ]; then
    TESTS_RUN=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "pytest" "$TRANSCRIPT" 2>/dev/null || echo "false")
    debug "Tests run: $TESTS_RUN"
    if [ "$TESTS_RUN" = "false" ]; then
        ISSUES="${ISSUES}Tests not run this session. Run pytest before pushing. "
    fi
fi

# Check 2: Risky files changed without subagent review?
RISKY_FILES=$(echo "$CHANGED_FILES" | grep -E '(server\.py|extractor\.py|retrieval\.py|config\.py)$' || true)
NEW_SRC_FILES=""
if [ -n "$RANGE" ]; then
    NEW_SRC_FILES=$(git -C "$REPO_ROOT" diff --diff-filter=A --name-only $RANGE 2>/dev/null | grep -E '^src/' 2>/dev/null || true)
fi

debug "Risky files: $(echo "$RISKY_FILES" | tr '\n' ' ')"
debug "New src files: $(echo "$NEW_SRC_FILES" | tr '\n' ' ')"

# --subagent, NOT --pattern, and with no recency window. Both halves are one change
# (BACKLOG #334). `--pattern` matched a string against the serialised input of ANY tool
# call, so *mentioning* a reviewer satisfied this gate: measured in one session, 7 real
# dispatches against 29 non-dispatch calls that each independently passed it — including
# 6 `evaluate_governance` calls whose only content was describing the intended work.
#
# WHY THE WINDOW HAD TO GO IN THE SAME EDIT. Mentions cluster right before a push so
# they survive a trailing window; a real dispatch happens once, early, and scrolls out.
# The hole was propping the window up. Narrowing alone leaves only about a THIRD of
# eligible pushes passing; narrowing plus window removal lands at parity. That ~3x gap is
# the finding. Narrowing alone would have flipped this gate to near-always-block, and the
# only escape is QUALITY_GATE_SKIP, which exits ABOVE the Check 6 secret scanner —
# trading a fake review check for a real credential leak.
#
# Deliberately no counts here: the corpus is live host state and grows, so pasted numbers
# drift (they already disagreed across four surfaces on first write). Run
# scripts/measure_review_gate.py — and read its CHURN lines, not the net delta: ~7 pushes
# are newly blocked, which is the figure that matters for bypass risk, since a
# newly-passed push does not cancel a newly-blocked one.
if [ -n "$RISKY_FILES" ] || [ -n "$NEW_SRC_FILES" ]; then
    REVIEW_DONE="false"
    for AGENT_TYPE in "code-reviewer" "security-auditor"; do
        FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --subagent "$AGENT_TYPE" "$TRANSCRIPT" 2>/dev/null || echo "false")
        if [ "$FOUND" = "true" ]; then
            REVIEW_DONE="true"
            break
        fi
    done
    debug "Review done: $REVIEW_DONE"
    if [ "$REVIEW_DONE" = "false" ]; then
        ISSUES="${ISSUES}Risky changes (core code or new src files) without subagent review — no code-reviewer or security-auditor DISPATCH found in this session (a mention no longer counts). If you did review via an untyped Agent dispatch, re-run it with subagent_type set, which is what this check can see. Note what it does NOT verify: that the review examined the diff being pushed, or that its findings were acted on. "
    fi
fi

# Check 3: Governance content files changed without governance subagent review?
# Same --subagent switch as Check 2, same reason.
#
# HONEST LIMIT, and the population matters: this check is weaker than it looks, because
# pre-exit-plan-mode-gate COMPELS a contrarian-reviewer dispatch before every
# ExitPlanMode, so any plan-mode session satisfies Check 3 via another hook's compelled
# output. Do NOT reason from "15/15 plan-mode sessions have one" to "Check 3 is already
# satisfied" — that is a base-rate error: only 6 of 22 governance-file-editing sessions
# used plan mode at all, so for the other 16 this check is doing real work. Making it
# meaningful in the plan-mode case is a separate question, deliberately not bundled here.
if [ -n "$GOVERNANCE_FILES" ]; then
    GOV_REVIEW_DONE="false"
    for AGENT_TYPE in "contrarian-reviewer" "coherence-auditor" "validator"; do
        FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --subagent "$AGENT_TYPE" "$TRANSCRIPT" 2>/dev/null || echo "false")
        if [ "$FOUND" = "true" ]; then
            GOV_REVIEW_DONE="true"
            break
        fi
    done
    debug "Governance review done: $GOV_REVIEW_DONE"
    if [ "$GOV_REVIEW_DONE" = "false" ]; then
        ISSUES="${ISSUES}Governance principle files changed without subagent review — no contrarian-reviewer, coherence-auditor or validator DISPATCH found (a mention no longer counts). "
    fi
fi

# Check 4: Was the completion checklist consulted this session?
# DELIBERATELY NOT gated on NON_DOC_FILES (unlike Check 1). Making a memory-only close-out
# push REACH this check is the whole point of #200's hatch-narrowing — a close-out SHOULD
# consult the completion checklist, and this check is self-resolving (run
# /completion-sequence-aigov and retry; the pattern then matches). It does not require the
# rare vocabulary that got the now-retired Check 5 (#202) into trouble, so it does not
# train QUALITY_GATE_SKIP. Do not "fix" this by gating it — that would re-open the seam
# #200 closed. (code-review MEDIUM)
CHECKLIST_READ="false"
for PATTERN in "COMPLETION-CHECKLIST" "completion-sequence-aigov" "completion-sequence" "completion sequence" "completion checklist"; do
    FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "$PATTERN" "$TRANSCRIPT" 2>/dev/null || echo "false")
    if [ "$FOUND" = "true" ]; then
        CHECKLIST_READ="true"
        break
    fi
done
debug "Completion checklist consulted: $CHECKLIST_READ"
if [ "$CHECKLIST_READ" = "false" ]; then
    ISSUES="${ISSUES}Completion checklist not consulted. Run /completion-sequence-aigov and verify applicable items before pushing. "
fi

# Check 5 (multi-commit acknowledgment) — RETIRED session-252, BACKLOG #202.
# It never fired in its entire history, for two reasons that still hold: its
# "push all"/"ship all" vocabulary matched ~6% of how the user actually authorizes a push
# (5 of 77 measured — they type "push"); and even working it was a weak speed-bump that
# made the human affirm a COUNT, never verifying per-commit review. Its one concrete
# intent — a secret slipped into a LATER commit of a bundle — is fully covered by Check 6
# below, which scans the ENTIRE $RANGE (not just HEAD); per-push authorization is the human
# gate. Keeping it was a footgun: a tightening that denies ~95% of natural pushes → user
# reaches for QUALITY_GATE_SKIP=true → which exits at the top of this file and disables the
# SECRET SCANNER. That dynamic is real and is the binding constraint on every check here.
#
# TWO CLAIMS THIS BLOCK USED TO MAKE ARE FALSE AND ARE CORRECTED (BACKLOG #334, 2026-08-12):
#   1. It called --pattern "role-BLIND (substring-matches ANY transcript line — tool_results
#      and this hook's own deny message included)". Not true: scan_for_pattern filters
#      `role == "assistant"` and `type == "tool_use"`, added precisely so a deny message
#      cannot self-satisfy on retry (#231). The real defect was narrower and worse-named —
#      it matched the serialised input of any tool call, so a MENTION passed.
#   2. It called Checks 1/2/4 "advisory". Check 2 appends to $ISSUES, which reaches
#      emit_deny: it BLOCKS. Calling a blocking gate advisory is the mislabel class #334
#      exists to fix, and it sat in the same sentence as the fix's own justification.
# It also cited #202 as the disposition that knowingly left this hole. #202 no longer
# exists in BACKLOG.md — a dangling pointer. #334 is that hole's re-discovery.
#
# Checks 2/3 now use --subagent (a real dispatch). Check 1 (pytest) and Check 4 (checklist)
# deliberately still use --pattern, and Check 1's hole is real but measured NON-BINDING:
# of 367 pushes passing Check 1 in-window, 23 (6%) pass with no actual pytest run in that
# window, against 1018 real runs corpus-wide. The authoritative evidence for "tests ran" is
# logs/check-runs.jsonl, which Checks 11/12 already read. Do not describe Check 1's matcher
# as "legitimate" — it is a known small-but-real hole left in place on cost/benefit
# grounds. (Percentages omitted on purpose; see the note above about pasted counts.)
#
# The range-undeterminable guard has moved ABOVE the empty-CHANGED_FILES exit (#232a).
# It was unreachable here — RANGE="" makes CHANGED_FILES empty, and the old
# empty-CHANGED_FILES exit sat above this point.

# Check 6 (diff secret-scan) USED TO LIVE HERE. It now runs ABOVE the docs-only escape
# hatch — see its block just after CHANGED_FILES is computed. Reason, in one line: at
# this position a push of only `.md`/`.json` files exited at the hatch and was never
# scanned, and `.json` is where credentials live (BACKLOG #232b, measured 2026-07-25).
# Do NOT move it back below the hatch.

# Check 7 (WARN-only, Commit 6 of Superpowers plan): TDD test-existence
# scan for new src/*.py files. Surfaces unpaired src files on stderr; does
# NOT add to ISSUES (no block). Promotion to BLOCK is event-driven (V-008
# in .claude/skills/compliance-review/verification.md): "promote to BLOCK after first coherence-audit
# finding flags WARN-mode pattern actually firing on real code." Bypass
# via TDD_TEST_EXISTENCE_SKIP=1.
if [ "${TDD_TEST_EXISTENCE_SKIP:-}" = "1" ] && [ -n "$NEW_SRC_FILES" ]; then
    audit_bypass "pre-push-quality-gate" "TDD_TEST_EXISTENCE_SKIP=1" "advisory-skip"
fi
if [ "${TDD_TEST_EXISTENCE_SKIP:-}" != "1" ] && [ -n "$NEW_SRC_FILES" ]; then
    TDD_OUT=$(printf '%s\n' "$NEW_SRC_FILES" | python3 "$HOOK_DIR/scan_transcript.py" --tdd-test-existence - 2>/dev/null || echo "error")
    if [ "$TDD_OUT" = "warn" ]; then
        TDD_FINDINGS=$(printf '%s\n' "$NEW_SRC_FILES" | python3 "$HOOK_DIR/scan_transcript.py" --tdd-test-existence - 2>&1 >/dev/null || true)
        echo "[tdd-test-existence] WARN — new src files lack paired test files (advisory; bypass with TDD_TEST_EXISTENCE_SKIP=1):" >&2
        echo "$TDD_FINDINGS" >&2
        echo "[tdd-test-existence] If this WARN later turns out to pre-figure a real defect (the unpaired src file shipped a regression paired tests would have caught), file the trigger event in V-008 row of .claude/skills/compliance-review/verification.md — closes the event-driven WARN→BLOCK promotion loop without depending on human memory." >&2
    fi
fi

# Check 9 (WARN-only): standing repo hygiene — the computed close-out inventory (#200).
#
# WHY IT WARNS AND DOES NOT BLOCK. A stale branch from 30 sessions ago is not a defect in
# the commit being pushed, so blocking would halt unrelated work and earn
# QUALITY_GATE_SKIP=true — which disables the secret scanner above. There is also ZERO
# evidence that a WARN at this seam is insufficient, and there cannot be any: the seam
# was closed by the docs-only hatch until this commit. Escalating to a gate on a hunch is
# exactly what the V-004 advisory→structural arc exists to prevent. Ship advisory,
# MEASURE, escalate on evidence.
#
# WHY IT LOGS ITS OWN FIRINGS — this is the part that makes "escalate on evidence" real.
# Check 7 above hangs its promotion on V-008, which asks a human to go file a trigger
# event. Check 7 has fired on ~10 pushes and V-008 records ZERO of them (0-for-10). This
# repo has 23 tripwires and 21 have never recorded a firing: a trigger nobody computes
# never fires, whatever its shape. So Check 9 writes its own evidence:
#
#   THE SAME FINDING-REF IN >=2 CONSECUTIVE CLOSE-OUT PUSHES *IS* "THE WARN WAS WALKED
#   PAST" — derivable by grep, never remembered by a human.
#
# Escalation (pre-specified in the #200 plan, mechanical to build when the log says so):
# an acknowledgment gate keyed on `promptSource` — NOT on `role`, because 6,914 of 7,668
# role:user transcript entries are tool results, including this hook's own deny message.
# A role-keyed ack would let the gate's own output unlock the gate.
HYGIENE_SCRIPT="$(dirname "$HOOK_DIR")/../scripts/repo_hygiene.py"
if [ "${HYGIENE_SKIP:-}" = "1" ]; then
    audit_bypass "pre-push-quality-gate" "HYGIENE_SKIP=1" "advisory-skip"
elif [ -f "$HYGIENE_SCRIPT" ]; then
    # CRITICAL: this file runs under `set -euo pipefail`, and repo_hygiene.py exits 1 to
    # mean "findings present" — a RESULT, not an error. A bare `OUT=$(...)` assignment
    # would therefore ABORT THE WHOLE HOOK the moment the repo had any loose ends,
    # silently skipping the ISSUES report below and FAILING THE GATE OPEN — an advisory
    # check would have disabled the secret scanner. Caught by dogfooding this on itself.
    # The `|| HYG_RC=$?` form keeps the pipeline "successful" so set -e stays out of it.
    HYG_OUT=""
    HYG_RC=0
    HYG_OUT=$(python3 "$HYGIENE_SCRIPT" --repo "$PWD" --min-severity high 2>/dev/null) || HYG_RC=$?
    # rc 1 = findings (a RESULT). rc 0 = clean. rc 2/3 = the tool broke — and a broken
    # tool must NEVER read as "the repo is clean" (the T-169 bug class), so we say so.
    if [ "$HYG_RC" -eq 1 ] && [ -n "$HYG_OUT" ]; then
        echo "[repo-hygiene] WARN — standing loose ends at close-out (advisory; bypass with HYGIENE_SKIP=1):" >&2
        echo "$HYG_OUT" >&2
        echo "[repo-hygiene] Mark a deliberate keep with a 'keep: <ref>' line in _ai-context/BACKLOG.md, next to the reason." >&2

        # The firing log. Same 100KB tail-keep convention as the dream/journal fire logs.
        FIRE_LOG="${HYGIENE_FIRE_LOG:-$HOME/.claude/repo-hygiene-fires.log}"
        # GUARD (code-review HIGH): this file is `set -euo pipefail`. An unguarded
        # `$(… | shasum …)` aborts the hook if shasum is ever absent — re-introducing,
        # one line down, the exact fail-OPEN the block above was written to prevent.
        # The `|| SESSION_KEY=unknown` keeps set -e out of it; the use site tolerates it.
        SESSION_KEY=$(printf '%s' "${TRANSCRIPT:-unknown}" | shasum 2>/dev/null | cut -c1-8) || SESSION_KEY=unknown
        if [ -w "$(dirname "$FIRE_LOG")" ] 2>/dev/null || [ -w "$FIRE_LOG" ] 2>/dev/null; then
            python3 "$HYGIENE_SCRIPT" --repo "$PWD" --min-severity high --json 2>/dev/null \
                | python3 -c "
import json, sys, datetime
try:
    rep = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
for f in rep.get('findings', []):
    print(f\"{ts} {sys.argv[1]} session={sys.argv[2]} finding={f['id']}\")
" "$PWD" "${SESSION_KEY:-unknown}" >> "$FIRE_LOG" 2>/dev/null || true
            if [ -f "$FIRE_LOG" ] && [ "$(wc -c < "$FIRE_LOG" 2>/dev/null || echo 0)" -gt 102400 ]; then
                tail -n 500 "$FIRE_LOG" > "${FIRE_LOG}.tmp" 2>/dev/null && mv "${FIRE_LOG}.tmp" "$FIRE_LOG" 2>/dev/null || true
            fi
        fi
    elif [ "$HYG_RC" -gt 1 ]; then
        echo "[repo-hygiene] check could not run (rc=$HYG_RC) — this is NOT 'repo is clean'." >&2
    fi
fi

# Report issues
if [ -n "$ISSUES" ]; then
    debug "BLOCKING: $ISSUES"
    emit_deny "QUALITY GATE: ${ISSUES}"
else
    debug "All checks passed, allowing push"
fi

exit 0
