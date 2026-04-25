#!/usr/bin/env bash
# PreToolUse hook — Pre-exit-plan-mode gate
# Blocks ExitPlanMode tool calls unless contrarian-reviewer has been invoked
# for the current plan (since the most recent prior ExitPlanMode, or first
# plan of session = bootstrap allow).
#
# Shipped per BACKLOG #116 (V-004 escalation, 3/5 session-failure threshold
# met 2026-04-22). Structural enforcement for the behavior LEARNING-LOG
# 2026-02-28 ("Hard-Mode Hooks Prove Deterministic Enforcement Works")
# documents as the answer when advisory compliance fails.
#
# Design notes:
#   - Scanner extension in scan_transcript.py does the plan-scoped matching
#     (--contrarian-after-last-plan mode). This hook is the decision surface.
#   - Follows pre-push-quality-gate.sh pattern: JSON permissionDecision + exit 0.
#   - Applies CFR §9.3.10 "Hook Implementation Prerequisites & Fail-Closed
#     Recipe" (title-10 v2.38.4): ERR trap, timeout wrapper, escape hatches,
#     self-diagnosing fallback.
#
# Escape hatches (in decreasing order of preference):
#   1. PREFERRED — invoke contrarian-reviewer via Task subagent_type.
#   2. Semantic bypass: PLAN_CONTRARIAN_CONFIRMED=1
#      ("I did invoke contrarian-reviewer and the scanner missed it"). Audit-logged.
#   3. Structural bypass: PLAN_CONTRARIAN_SKIP_HOOK=1
#      ("The hook itself is broken, get out of my way"). Audit-logged with deny-log entry.
#
# Environment variables:
#   PLAN_CONTRARIAN_CONFIRMED=1  — Semantic bypass (documented override).
#   PLAN_CONTRARIAN_SKIP_HOOK=1  — Structural bypass (gate is broken).
#   PLAN_CONTRARIAN_DEBUG=true   — Enable stderr debug logging.
#
# Author: Claude Opus 4.7 (1M context) + Jason Collier, 2026-04-23
# Design rationale: BACKLOG #116 + pre-edit 3-agent battery (session-122) +
#   CFR §9.3.10 canonical recipe.

set -euo pipefail

# Claude Code exit semantics: exit 0 = allow-default (decision may be in JSON
# stdout), exit 2 = hard deny. This trap converts unhandled `set -e` failures
# to exit 2 so the hook fails CLOSED (deny) on errors, not fail-open.
# See LEARNING-LOG "Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed"
# (2026-04-16) and "Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout"
# (2026-04-21).
#
# Timeout semantics: SIGKILL on hook timeout bypasses this trap. The scanner
# call below is internally wrapped with `timeout 7` so the hook self-denies
# before Claude Code's 10s SIGKILL fires and would be treated as exit-1
# non-blocking allow.
trap 'exit 2' ERR

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="$HOOK_DIR/scan_transcript.py"
DENY_LOG="${HOME}/.context-engine/plan-contrarian-denies.log"

debug() {
    if [ "${PLAN_CONTRARIAN_DEBUG:-false}" = "true" ]; then
        echo "[plan-contrarian-gate] $1" >&2
    fi
}

# Write a single audit-log line to the deny-log with size cap (100KB).
# Mirrors pre-test-oom-gate.sh rotation pattern. Captures all three outcomes
# (deny, semantic-bypass, structural-bypass) for V-006 instrumentation.
_audit_log() {
    local tag="$1"
    mkdir -p "$(dirname "$DENY_LOG")" 2>/dev/null || return 0
    # Cap log at 100KB — rotate by tailing last 500 lines.
    if [ -f "$DENY_LOG" ]; then
        # Portable byte-count via `wc -c`. `stat` differs macOS (-f %z) vs
        # Linux (-c %s); `stat -f` on Linux queries the filesystem, not the
        # file, and silently returns unexpected content — CI caught this on
        # 2026-04-23. `wc -c` is POSIX and works identically on both.
        local size
        size=$(wc -c < "$DENY_LOG" 2>/dev/null | tr -d ' ' || echo 0)
        if [ "${size:-0}" -gt 102400 ]; then
            tail -n 500 "$DENY_LOG" > "$DENY_LOG.tmp" 2>/dev/null && mv "$DENY_LOG.tmp" "$DENY_LOG" 2>/dev/null || true
        fi
    fi
    printf '%s %s transcript=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$tag" "${TRANSCRIPT:-<none>}" >> "$DENY_LOG" 2>/dev/null || true
}

# Emit a structured deny JSON and exit 0 (decision in JSON per pre-push-quality-gate pattern).
# If python3 fails/OOMs, fall back to stderr + exit 2 (hard deny) — do NOT silently
# fail-open. This is the single point where all documented fail-closed paths route;
# a fail-open here defeats every other fail-closed guarantee. See LEARNING-LOG
# 2026-04-16 "Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed."
emit_deny() {
    local reason="$1"
    _audit_log "deny"
    if ! python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$reason" 2>/dev/null; then
        echo "[plan-contrarian-gate] python3 unavailable or failed while emitting deny JSON — falling back to exit 2 (hard deny). Set PLAN_CONTRARIAN_SKIP_HOOK=1 to bypass if persistent." >&2
        exit 2
    fi
    exit 0
}

# Emit an allow (no JSON; harness defaults to allow on silent exit-0).
emit_allow() {
    local note="${1:-}"
    if [ -n "$note" ]; then
        debug "allow: $note"
    fi
    exit 0
}

# ---------------------------------------------------------------------------
# Read stdin and extract transcript_path
# ---------------------------------------------------------------------------

INPUT=$(cat)

# Parse transcript_path from the hook payload. jq preferred, python3 fallback.
if command -v jq >/dev/null 2>&1; then
    TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
else
    debug "jq not found, using python3 JSON fallback"
    TRANSCRIPT=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    print(d.get('transcript_path', ''))
except Exception:
    print('')
" <<<"$INPUT" 2>/dev/null || echo "")
fi

debug "transcript_path=$TRANSCRIPT"

# ---------------------------------------------------------------------------
# Bypass envs (checked BEFORE scanner — these are the designated overrides)
# ---------------------------------------------------------------------------

if [ "${PLAN_CONTRARIAN_CONFIRMED:-}" = "1" ]; then
    # Semantic bypass: "I invoked contrarian; scanner missed it." Audit-logged symmetrically
    # with structural bypass (per post-commit contrarian review) so usage-as-muscle-memory
    # is visible in the same log.
    _audit_log "semantic-bypass"
    echo "[plan-contrarian-gate] SEMANTIC BYPASS: PLAN_CONTRARIAN_CONFIRMED=1 (user confirmed contrarian invoked) — logged to $DENY_LOG" >&2
    emit_allow "semantic bypass"
fi

if [ "${PLAN_CONTRARIAN_SKIP_HOOK:-}" = "1" ]; then
    # Structural bypass: hook itself is broken.
    _audit_log "structural-bypass"
    echo "[plan-contrarian-gate] STRUCTURAL BYPASS: PLAN_CONTRARIAN_SKIP_HOOK=1 — gate treated as broken, logged to $DENY_LOG" >&2
    emit_allow "structural bypass"
fi

# ---------------------------------------------------------------------------
# Transcript presence check
# ---------------------------------------------------------------------------

if [ -z "$TRANSCRIPT" ]; then
    debug "transcript_path missing from payload — fail-closed deny"
    emit_deny "pre-exit-plan-mode-gate: hook payload missing transcript_path. This suggests a malformed PreToolUse event. If persistent, set PLAN_CONTRARIAN_SKIP_HOOK=1 to bypass and file a bug report."
fi

if [ ! -f "$TRANSCRIPT" ]; then
    debug "transcript file absent at $TRANSCRIPT — fail-closed deny"
    emit_deny "pre-exit-plan-mode-gate: transcript file not found at '$TRANSCRIPT'. Cannot verify contrarian-reviewer was invoked. If this is your first action in a fresh session and contrarian was invoked, re-invoke it before ExitPlanMode, or set PLAN_CONTRARIAN_CONFIRMED=1 for this turn."
fi

# ---------------------------------------------------------------------------
# Platform timeout detection (CFR §9.3.10 step 2)
# ---------------------------------------------------------------------------

_TIMEOUT_CMD=""
if command -v timeout >/dev/null 2>&1; then
    _TIMEOUT_CMD="timeout 7"
elif command -v gtimeout >/dev/null 2>&1; then
    _TIMEOUT_CMD="gtimeout 7"
else
    # Self-diagnosing fallback (CFR §9.3.10 step 5): surface the gap once.
    echo "[plan-contrarian-gate] WARNING: no timeout/gtimeout binary found; scanner is unguarded. Install coreutils ('brew install coreutils' on macOS) to close the fail-open-on-timeout gap." >&2
fi

# ---------------------------------------------------------------------------
# Invoke scanner (plan-scoped contrarian check)
# ---------------------------------------------------------------------------

if SCAN_OUTPUT=$($_TIMEOUT_CMD python3 "$SCANNER" --contrarian-after-last-plan "$TRANSCRIPT" 2>/dev/null); then
    :
else
    _RC=$?
    if [ "$_RC" = "124" ]; then
        echo "[plan-contrarian-gate] scanner exceeded 7s internal timeout — failing closed" >&2
        emit_deny "pre-exit-plan-mode-gate: scanner timeout (>7s). Fail-closed. If persistent, set PLAN_CONTRARIAN_SKIP_HOOK=1 to bypass."
    fi
    debug "scanner non-zero exit ($_RC) with no output — treating as error"
    SCAN_OUTPUT="error"
fi

debug "scanner result: $SCAN_OUTPUT"

# ---------------------------------------------------------------------------
# Action-atomicity WARN-mode integration (Commit 6 of Superpowers plan)
# ---------------------------------------------------------------------------
# After the contrarian gate passes (allow/bootstrap), additionally scan the
# plan text for action-atomicity violations per plan-template Recommended
# Approach section. This is WARN-only — surfaces findings on stderr but does
# not block. Promotion to BLOCK is event-driven (V-007 in COMPLIANCE-REVIEW.md):
# "promote to BLOCK after first coherence-audit finding flags WARN-mode pattern
# actually firing on real code." Bypass via PLAN_ACTION_ATOMICITY_SKIP=1.
_warn_action_atomicity() {
    if [ "${PLAN_ACTION_ATOMICITY_SKIP:-}" = "1" ]; then
        debug "action-atomicity WARN scan skipped (PLAN_ACTION_ATOMICITY_SKIP=1)"
        return 0
    fi
    # Extract the plan text from the hook payload's tool_input.plan field.
    local plan_text
    if command -v jq >/dev/null 2>&1; then
        plan_text=$(echo "$INPUT" | jq -r '.tool_input.plan // ""' 2>/dev/null || echo "")
    else
        plan_text=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    print(d.get('tool_input', {}).get('plan', ''))
except Exception:
    print('')
" <<<"$INPUT" 2>/dev/null || echo "")
    fi
    if [ -z "$plan_text" ]; then
        debug "action-atomicity: no tool_input.plan in payload — skip"
        return 0
    fi
    local atom_status
    atom_status=$(printf '%s' "$plan_text" | $_TIMEOUT_CMD python3 "$SCANNER" --plan-action-atomicity - 2>&1 >/dev/null && true || true)
    # Re-run capturing stdout for status, stderr for findings (separately).
    local atom_stdout atom_stderr
    atom_stdout=$(printf '%s' "$plan_text" | $_TIMEOUT_CMD python3 "$SCANNER" --plan-action-atomicity - 2>/dev/null || echo "error")
    atom_stderr=$(printf '%s' "$plan_text" | $_TIMEOUT_CMD python3 "$SCANNER" --plan-action-atomicity - 2>&1 >/dev/null || true)
    case "$atom_stdout" in
        warn)
            echo "[plan-action-atomicity] WARN — Recommended Approach section has action-atomicity issues (advisory; bypass with PLAN_ACTION_ATOMICITY_SKIP=1):" >&2
            echo "$atom_stderr" >&2
            ;;
        pass|skip|error|"")
            debug "action-atomicity status: $atom_stdout"
            ;;
    esac
    return 0
}

case "$SCAN_OUTPUT" in
    allow)
        _warn_action_atomicity
        emit_allow "contrarian-reviewer invoked for current plan"
        ;;
    bootstrap)
        echo "[plan-contrarian-gate] bootstrap: no prior ExitPlanMode in transcript — allowing (first plan of session)" >&2
        _warn_action_atomicity
        emit_allow "bootstrap case"
        ;;
    deny)
        emit_deny "pre-exit-plan-mode-gate: contrarian-reviewer was not invoked for this plan. Before approving, invoke it via Task(subagent_type='contrarian-reviewer', ...) to pressure-test the plan (per .claude/plan-template.md section 'Contrarian Review Output'). Bypasses: PLAN_CONTRARIAN_CONFIRMED=1 if you did invoke contrarian and the scanner missed it; PLAN_CONTRARIAN_SKIP_HOOK=1 if the hook itself is broken (audit-logged)."
        ;;
    error)
        emit_deny "pre-exit-plan-mode-gate: transcript read/parse failure. Fail-closed. If persistent, set PLAN_CONTRARIAN_SKIP_HOOK=1 to bypass."
        ;;
    *)
        debug "scanner returned unexpected output '$SCAN_OUTPUT' — fail-closed"
        emit_deny "pre-exit-plan-mode-gate: scanner returned unexpected output. Fail-closed. If persistent, set PLAN_CONTRARIAN_SKIP_HOOK=1 to bypass."
        ;;
esac
