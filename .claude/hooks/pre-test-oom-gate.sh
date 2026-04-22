#!/usr/bin/env bash
# PreToolUse hook — Pre-test OOM prevention gate
# Blocks bare `pytest tests/` (or equivalent full-suite invocations) when the
# Context Engine watcher daemon is alive OR other torch-holding Python processes
# are present, to prevent the class of OOM that hit this box on 2026-04-15.
#
# Per LEARNING-LOG "Hard-Mode Hooks Prove Deterministic Enforcement Works"
# (2026-02-28): "advisory failed at 87%; structural blocking achieves near-100%"
#
# Design notes:
#   - Threat model: AI-initiated Bash invocations of pytest that don't check the
#     environment first. Human users running pytest manually in a terminal
#     outside Claude Code are not the threat model (they know their own machine).
#   - PreToolUse is the only layer that sees AI-initiated Bash commands BEFORE
#     the subprocess launches. Blocking at the Bash layer means pytest's own
#     process never starts, avoiding the ~500 MB–1 GB torch+transformers
#     module-init cost even in the blocked case.
#   - Heartbeat staleness semantics mirror src/ai_governance_mcp/context_engine/
#     server.py:943-951 — 5 minutes (300s) is the "likely alive" threshold.
#     PID file present but heartbeat stale → daemon has crashed → do not block.
#
# Escape hatches (in decreasing order of preference):
#   1. PREFERRED — safe subset: `pytest tests/ -v -m "not slow"` (matches CI)
#   2. Targeted: `pytest tests/test_<file>.py::<Class>`
#   3. Semantic bypass: PYTEST_ALLOW_HEAVY=1 (intentional heavy run on quiet box)
#   4. Structural bypass: PYTEST_SKIP_OOM_GATE=1 (the gate itself is broken)
#   5. Stop daemon then retry (listed last — deliberately the less-attractive option)
#
# Environment variables:
#   PYTEST_ALLOW_HEAVY=1    — Semantic bypass: "I intend to run the heavy suite."
#   PYTEST_SKIP_OOM_GATE=1  — Structural bypass: "The gate is broken, get out of my way."
#   OOM_GATE_DEBUG=true     — Enable stderr debug logging
#
# Known limitation: `-k <expr>` accepts any expression without content
# validation. `-k test` matches every test. Acceptable per threat model:
# explicit `-k` usage implies targeted selection intent by the AI.
#
# Author: Claude Opus 4.6 (1M context) + Jason Collier, 2026-04-15
# Design rationale: BACKLOG.md #49 (Status 2026-04-15 block) + LEARNING-LOG
#   "Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)"

set -euo pipefail

# Claude Code exit semantics: exit 0=allow, exit 2=deny, exit 1=non-blocking
# allow. With set -e, unhandled failures exit 1 (fail-open). This trap converts
# all unhandled errors to exit 2 (fail-closed), matching the security gate model.
# See LEARNING-LOG "Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed".
#
# Timeout semantics (SIGKILL bypasses the ERR trap): if this hook exceeds the
# `timeout` configured in settings.json (currently 10s), Claude Code kills the
# process via SIGKILL — which bash CANNOT trap — and treats the timeout as a
# non-blocking allow (same as exit 1). Fail-closed is therefore conditional on
# decision logic completing within the timeout window. Slow steps (notably
# `ps -ax` under memory pressure, which is exactly when the gate is most needed)
# are bounded with internal `timeout 7` guards below so the hook can self-deny
# before the kill-switch fires. See LEARNING-LOG "Bash ERR Trap Does Not Cover
# SIGKILL / Hook Timeout" (2026-04-21).
trap 'exit 2' ERR

HEARTBEAT_PATH="${HOME}/.context-engine/watcher-heartbeat.json"
DENY_LOG="${HOME}/.context-engine/oom-gate-denies.log"
HEARTBEAT_MAX_AGE_SECONDS=300  # 5 minutes — matches _read_daemon_heartbeat semantics

debug() {
    if [ "${OOM_GATE_DEBUG:-false}" = "true" ]; then
        echo "[oom-gate] $1" >&2
    fi
}

# ---------------------------------------------------------------------------
# Read stdin and short-circuit non-pytest commands
# ---------------------------------------------------------------------------

# JSON parsing: prefer jq, fall back to python3. If both missing, ERR trap
# catches → exit 2 (fail-closed). Security gate must deny when input unparseable.
if command -v jq >/dev/null 2>&1; then
    _parse_command() { jq -r '.tool_input.command // ""' 2>/dev/null || echo ""; }
else
    debug "jq not found, using python3 JSON fallback"
    _parse_command() {
        python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
            2>/dev/null || echo ""
    }
fi

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | _parse_command)

if [ -z "$COMMAND" ]; then
    debug "no command in tool_input, allowing"
    exit 0
fi

# Match pytest invocations precisely. Covers:
#   - `pytest ...` (must have trailing whitespace → real invocation with args)
#   - `python -m pytest` / `python3 -mpytest` (with or without space after -m,
#     optionally followed by args or end-of-string)
#   - Commands with env-var prefixes: `FOO=1 pytest ...`
#   - Chained commands: `cd ... && pytest ...` or `... ; pytest ...`
#
# Does NOT match:
#   - `rg pytest`, `grep pytest` (string search, no trailing args after `pytest`)
#   - `echo pytest` (same — the word at end of string is not an invocation)
#   - `pytest` bare at end of string with no args: false negative accepted as
#     LOW-priority per code-reviewer finding #2. A bare `pytest` with no test
#     path fails pytest's own "no tests collected" behavior anyway.
#
# DOES match `echo "run pytest tests/"` — known false-positive in the threat
# model per code-reviewer finding #12 (we'd rather block a harmless echo than
# miss a real invocation). The user sees a clear deny message they can bypass.
if ! echo "$COMMAND" | grep -qE '(^|[[:space:]]|&&|;|\|)[[:space:]]*(pytest[[:space:]]|python[23]?[[:space:]]+-m[[:space:]]*pytest([[:space:]]|$))'; then
    debug "not a pytest command, allowing: $COMMAND"
    exit 0
fi

debug "pytest command detected: $COMMAND"

# ---------------------------------------------------------------------------
# Bypass env vars — structural and semantic
# ---------------------------------------------------------------------------
# We check BOTH the command string (inline env prefix: `PYTEST_ALLOW_HEAVY=1 pytest ...`)
# AND the hook's own environment (`PYTEST_ALLOW_HEAVY=1` exported in shell).
if [ "${PYTEST_SKIP_OOM_GATE:-}" = "1" ] || echo "$COMMAND" | grep -qE '(^|[[:space:]])PYTEST_SKIP_OOM_GATE=1[[:space:]]'; then
    debug "PYTEST_SKIP_OOM_GATE bypass triggered"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ OOM gate STRUCTURALLY bypassed via PYTEST_SKIP_OOM_GATE=1. Use this only if the gate itself is broken. If you meant '"'"'I want the heavy suite,'"'"' use PYTEST_ALLOW_HEAVY=1 instead."}}'
    exit 0
fi

if [ "${PYTEST_ALLOW_HEAVY:-}" = "1" ] || echo "$COMMAND" | grep -qE '(^|[[:space:]])PYTEST_ALLOW_HEAVY=1[[:space:]]'; then
    debug "PYTEST_ALLOW_HEAVY bypass triggered"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ OOM gate bypassed via PYTEST_ALLOW_HEAVY=1. Intentional heavy-suite run. Ensure no other Claude Code sessions or MCP processes are holding torch."}}'
    exit 0
fi

# ---------------------------------------------------------------------------
# Safe-subset detection — these patterns mean "this is not a full-suite run"
# ---------------------------------------------------------------------------
# - `-m "not slow"` or `-m 'not slow'` or `-m not\ slow` (marker filter matching CI)
# - `-k <expr>` (keyword selection — targeted)
# - `tests/test_<file>.py::<Class>` (explicit class/method selection)
# - `tests/test_<file>.py` alone (single-file, not the whole tests/ dir)
IS_SAFE_SUBSET=false

# -m "not slow" in any quoting style
if echo "$COMMAND" | grep -qE -- '-m[[:space:]]+["'"'"']?not[[:space:]]+slow["'"'"']?'; then
    IS_SAFE_SUBSET=true
    debug "safe: marker filter 'not slow' detected"
fi

# -k <expr> keyword selection
if echo "$COMMAND" | grep -qE -- '-k[[:space:]]+[^[:space:]]+'; then
    IS_SAFE_SUBSET=true
    debug "safe: -k keyword selection detected"
fi

# Explicit class/method selection via ::
if echo "$COMMAND" | grep -qE 'tests/[^[:space:]]*::'; then
    IS_SAFE_SUBSET=true
    debug "safe: :: class/method selection detected"
fi

# Single-file invocation (matches `pytest tests/test_X.py` but not `pytest tests/`)
if echo "$COMMAND" | grep -qE 'tests/test_[A-Za-z0-9_]+\.py([[:space:]]|$)'; then
    IS_SAFE_SUBSET=true
    debug "safe: single-file invocation detected"
fi

if [ "$IS_SAFE_SUBSET" = "true" ]; then
    debug "safe subset invocation, allowing"
    exit 0
fi

# ---------------------------------------------------------------------------
# At this point: pytest invocation that LOOKS LIKE a full-suite run.
# Now check whether the environment is safe for it.
# ---------------------------------------------------------------------------

# Check 1: Is the watcher daemon alive per heartbeat semantics?
# Fail-closed semantics: if we can't determine heartbeat age, assume fresh.
# Rationale: this hook's purpose is to block dangerous runs; silent-allow on
# parse failure would defeat the gate. Conservative default matches the threat
# model. Security-auditor finding S2 + code-reviewer finding #5.
DAEMON_ALIVE=false
DAEMON_SIGNAL=""
if [ -f "$HEARTBEAT_PATH" ]; then
    # Use Python for ISO8601 parsing — matches server.py:_read_daemon_heartbeat semantics
    DAEMON_AGE=$(python3 - "$HEARTBEAT_PATH" <<'PYEOF' 2>/dev/null || echo "parse_error"
import json, sys
from datetime import datetime, timezone
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    alive_at = data.get("alive_at", "")
    if not alive_at:
        print("parse_error")
        sys.exit(0)
    dt = datetime.fromisoformat(alive_at)
    age = (datetime.now(timezone.utc) - dt).total_seconds()
    # Negative age (clock skew, crafted future timestamp) is treated as fresh
    # per fail-closed policy.
    if age < 0:
        print("0")
    else:
        print(f"{age:.0f}")
except Exception:
    print("parse_error")
PYEOF
    )
    debug "heartbeat age: ${DAEMON_AGE}"
    if [ "$DAEMON_AGE" = "parse_error" ]; then
        # Fail-closed: heartbeat file exists but we can't parse it → assume daemon alive.
        DAEMON_ALIVE=true
        DAEMON_SIGNAL="watcher heartbeat file present but unparseable (fail-closed: assuming daemon alive)"
    elif [ "$DAEMON_AGE" -lt "$HEARTBEAT_MAX_AGE_SECONDS" ] 2>/dev/null; then
        DAEMON_ALIVE=true
        DAEMON_SIGNAL="watcher daemon heartbeat fresh (${DAEMON_AGE}s ago, threshold ${HEARTBEAT_MAX_AGE_SECONDS}s)"
    else
        debug "heartbeat present but stale (${DAEMON_AGE}s old) — daemon likely crashed, not blocking on this signal"
    fi
fi

# Check 2: Are there other Python processes holding torch/transformers?
# Exclude: grep itself, our own shell, our own python3 subprocess.
# Match: ai_governance_mcp (module with underscores), ai-context-engine (binary),
#        context-engine-watcher (binary), sentence_transformers (module).
# Note: the repo directory path `ai-governance-mcp` (with hyphens) does NOT match
# `ai_governance_mcp` (with underscores) — only the actual Python module invocation
# does. So pytest running in the repo dir is not a false positive.
#
# Test-only bypass: OOM_GATE_SKIP_PROCESS_SCAN=1 disables this check entirely.
# Used by the unit tests to isolate the heartbeat signal. NOT documented as a
# production bypass — this is a test hook only, per code-reviewer finding #7.
TORCH_PROC_COUNT=0
TORCH_PROC_LIST=""
if [ "${OOM_GATE_SKIP_PROCESS_SCAN:-}" = "1" ] && [ -n "${PYTEST_CURRENT_TEST:-}" ]; then
    debug "process scan skipped (OOM_GATE_SKIP_PROCESS_SCAN=1 + PYTEST_CURRENT_TEST set)"
else
    # Bound the slowest step internally: if ps hangs past 7s, self-deny (exit 2)
    # before Claude Code's 10s SIGKILL fires and is treated as fail-open.
    # macOS lacks GNU `timeout` by default; fall back to coreutils `gtimeout`
    # (from `brew install coreutils`) or to unguarded ps if neither is present.
    _OOM_PS="ps"
    if command -v timeout >/dev/null 2>&1; then
        _OOM_PS="timeout 7 ps"
    elif command -v gtimeout >/dev/null 2>&1; then
        _OOM_PS="gtimeout 7 ps"
    else
        # Self-diagnosing fallback: the fail-open-on-timeout gap this mitigation
        # was designed to close is OPEN on machines without a timeout binary.
        # Surface the gap once per invocation so the user sees it in transcripts.
        echo "[oom-gate] WARNING: no timeout/gtimeout binary found; ps is unguarded and the hook may fail-open under memory pressure. Install coreutils ('brew install coreutils' on macOS) to close the gap." >&2
    fi
    if _PS_OUTPUT=$($_OOM_PS -o pid=,command= -ax 2>/dev/null); then
        :  # ps succeeded
    else
        _PS_RC=$?
        if [ "$_PS_RC" = "124" ]; then
            echo "[oom-gate] ps exceeded 7s internal timeout — failing closed (exit 2)" >&2
            exit 2
        fi
        _PS_OUTPUT=""
    fi
    OTHER_TORCH_PROCS=$(echo "$_PS_OUTPUT" | \
        grep -E '(python|Python).*(ai_governance_mcp|ai-context-engine|context-engine-watcher|sentence_transformers)' | \
        grep -v 'grep' | \
        awk '{print $1}' | \
        sort -u || true)

    if [ -n "$OTHER_TORCH_PROCS" ]; then
        # Filter out our own PID and parent (the hook's own bash + python3 processes)
        MY_PID=$$
        # Single-PID lookup (much narrower scope than the -ax scan above); kernel
        # process-table walk is bounded. Left unguarded deliberately to keep the
        # control-flow simple. If memory-pressure evidence ever shows this stalls,
        # wrap with $_OOM_PS using the same 124→exit-2 pattern as the scan above.
        MY_PPID=$(ps -o ppid= -p $$ 2>/dev/null | tr -d ' ' || echo "0")
        while IFS= read -r pid; do
            if [ -z "$pid" ]; then continue; fi
            if [ "$pid" = "$MY_PID" ] || [ "$pid" = "$MY_PPID" ]; then continue; fi
            TORCH_PROC_COUNT=$((TORCH_PROC_COUNT + 1))
            TORCH_PROC_LIST="${TORCH_PROC_LIST}${pid} "
        done <<< "$OTHER_TORCH_PROCS"
    fi
fi
debug "other torch processes: count=${TORCH_PROC_COUNT} pids=${TORCH_PROC_LIST}"

# ---------------------------------------------------------------------------
# Decision: block only if at least one risk signal fired
# ---------------------------------------------------------------------------
SIGNALS=""
if [ "$DAEMON_ALIVE" = "true" ]; then
    SIGNALS="${SIGNALS}• ${DAEMON_SIGNAL}
"
fi
if [ "$TORCH_PROC_COUNT" -gt 0 ]; then
    SIGNALS="${SIGNALS}• ${TORCH_PROC_COUNT} other Python process(es) already holding torch/transformers: PIDs ${TORCH_PROC_LIST}
"
fi

if [ -z "$SIGNALS" ]; then
    debug "no risk signals fired, allowing"
    exit 0
fi

# ---------------------------------------------------------------------------
# Block with a rich deny message that leads with `-m "not slow"` as the
# expected workflow. Per contrarian review #2 (2026-04-15) UX trap finding:
# if "kill the daemon" becomes the path of least resistance, the OOM guarantee
# silently disappears in future sessions.
# ---------------------------------------------------------------------------

# Redact potential secrets from the command before logging. Layered patterns:
# 1. Specific token prefixes (OpenAI sk-, GitHub ghp_, AWS AKIA)
# 2. Bearer tokens
# 3. CLI flags (--api-key, --token, --secret, --password, --credential)
# 4. Generic KEY=VALUE environment variable patterns
# Trade-off: may redact legitimate args like --token-file=/path. Acceptable
# for a diagnostic log where false-redaction > leaked-secret.
redact_secrets() {
    sed -E \
        -e 's/(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9_-]*/\1<redacted>/g' \
        -e 's/(ghp_[a-zA-Z0-9]{4})[a-zA-Z0-9]*/\1<redacted>/g' \
        -e 's/AKIA[A-Z0-9]{12,}/AKIA<redacted>/g' \
        -e 's/(Bearer )[^ ]*/\1<redacted>/gI' \
        -e 's/(--(api[_-]?key|token|secret|password|credential)[= ])[^ ]*/\1<redacted>/gI' \
        -e 's/([A-Z_]*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)=)[^ ]*/\1<redacted>/g'
}

# Record the deny for the #49 forcing-function activity trigger.
# Use plain ASCII key=value format — avoid `printf %q` (bash 3.2 on macOS
# byte-escapes non-ASCII characters, corrupting the unicode bullets in SIGNALS).
# Fields: timestamp (ISO8601 UTC), daemon_alive flag, torch_proc_count,
# and the command with newlines replaced by spaces for single-line logging.
mkdir -p "$(dirname "$DENY_LOG")"
DENY_LINE_CMD=$(printf '%s' "$COMMAND" | tr '\n\r' '  ' | redact_secrets | head -c 500)
printf '%s deny daemon_alive=%s torch_procs=%d cmd=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$DAEMON_ALIVE" \
    "$TORCH_PROC_COUNT" \
    "$DENY_LINE_CMD" >> "$DENY_LOG" 2>/dev/null || true

# Cap deny log at 100KB to prevent unbounded growth. Atomic via temp+mv.
if [ -f "$DENY_LOG" ]; then
    _log_size=$(stat -f%z "$DENY_LOG" 2>/dev/null || stat -c%s "$DENY_LOG" 2>/dev/null || echo "0")
    if [ "${_log_size}" -gt 102400 ] 2>/dev/null; then
        tail -n 500 "$DENY_LOG" > "${DENY_LOG}.tmp" && mv "${DENY_LOG}.tmp" "$DENY_LOG"
    fi
fi

REASON="OOM PREVENTION GATE: bare full-suite pytest invocation blocked.

Why: running pytest here would load a new Python interpreter with torch + transformers + sentence-transformers on top of already-resident state:
${SIGNALS}
On 2026-04-15 a similar invocation OOM'd a 64 GB macOS machine. The fix class:

  EXPECTED workflow (the happy path — use this):
    pytest tests/ -v -m \"not slow\"
  This matches CI, excludes real-model tests, and does NOT require touching the daemon.

  Targeted alternatives (also always allowed):
    pytest tests/test_<file>.py -v
    pytest tests/test_<file>.py::<Class> -v
    pytest tests/ -k <expression> -v

  Intentional heavy-suite run (on a quiet machine, you've checked):
    PYTEST_ALLOW_HEAVY=1 pytest tests/

  Emergency — the gate itself is broken:
    PYTEST_SKIP_OOM_GATE=1 pytest ...   (semantically distinct from ALLOW_HEAVY)

  Last resort (not recommended): stop the daemon, then retry, then restart it.
  Prefer the marker filter above — it does the same job without the daemon-restart dance.

This block is deliberate. Background: LEARNING-LOG.md (incident) and backlog #49 (design spike for the real underlying fix)."

# Critical: if python3 fails to emit the deny JSON, we MUST NOT exit 0 —
# that would silently allow the dangerous command through. Per code-reviewer
# finding #13: "fail-open on python3 failure defeats the gate in the hot path."
# Claude Code interprets non-zero exit + stderr as a structural deny.
if ! python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$REASON"; then
    # python3 unavailable or crashed. Fall back to plain stderr + non-zero exit,
    # which Claude Code treats as deny. Intentionally terse — we cannot emit the
    # rich multi-line REASON safely without a working JSON encoder.
    echo "OOM PREVENTION GATE: blocked. python3 unavailable; see .claude/hooks/pre-test-oom-gate.sh and use PYTEST_SKIP_OOM_GATE=1 to emergency-bypass." >&2
    exit 2
fi

exit 0
