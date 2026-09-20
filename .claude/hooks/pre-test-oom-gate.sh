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
# Design rationale: BACKLOG.md #49 (CLOSED) + LEARNING-LOG
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

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# GUARDED — a failed `source` exits 1, which the harness reads as ALLOW, and
# `trap ... ERR` does NOT cover it (measured, bash 3.2). `lib/` is one symlink
# into the checkout, so moving the repo removes every library at once: the
# ordinary consequence of moving a directory, not an exotic case. BACKLOG #299.
if [ -r "$HOOK_DIR/lib/audit-bypass.sh" ]; then
    source "$HOOK_DIR/lib/audit-bypass.sh"
else
    echo "[pre-test-oom-gate] WARNING: lib/audit-bypass.sh missing — degraded, bypasses will not be audited" >&2
    audit_bypass() { :; }
fi

# ${HOME:-} — NOT ${HOME}. Under `set -u` an unset HOME aborts here with rc 1,
# which the harness reads as ALLOW, so this gate silently stopped existing.
# Measured session-272: a bare full-suite pytest returned rc=1 / 0 bytes with
# HOME unset, versus a deny with it set. The `trap 'exit 2' ERR` above does NOT
# fire on an unbound-variable abort — that is the whole trap of this class.
#
# Neither path is a decision input. An unreadable heartbeat reads as "daemon
# absent", which is the ordinary no-daemon case the gate already handles, and
# the ps-based trigger is unaffected. Strictly better than aborting and allowing
# EVERYTHING. BACKLOG #299 Stage A.
HEARTBEAT_PATH="${HOME:-}/.context-engine/watcher-heartbeat.json"
DENY_LOG="${HOME:-}/.context-engine/oom-gate-denies.log"
HEARTBEAT_MAX_AGE_SECONDS=300  # 5 minutes — matches _read_daemon_heartbeat semantics

debug() {
    if [ "${OOM_GATE_DEBUG:-false}" = "true" ]; then
        echo "[oom-gate] $1" >&2
    fi
}

# ---------------------------------------------------------------------------
# Read stdin and short-circuit non-pytest commands
# ---------------------------------------------------------------------------

# EXPORTED-ENV BYPASSES ARE CHECKED BEFORE THE PARSE. Order is the whole point:
# these read the hook's own environment and need no parser, and they used to sit
# BELOW a deny that fires when neither jq nor python3 can read the payload. That
# deny's condition matches every Claude Code Bash payload, so with both parsers
# broken this gate denied EVERY Bash call while telling the user to escape via a
# variable checked further down and therefore unreachable. jq and python3 resolve
# to the same conda prefix here, so one broken environment breaks both.
#
# The INLINE forms (`PYTEST_ALLOW_HEAVY=1 pytest ...`) still need SCAN_COMMAND
# and stay below — they are a question about the command, not the environment.
if [ "${PYTEST_SKIP_OOM_GATE:-}" = "1" ]; then
    audit_bypass "pre-test-oom-gate" "PYTEST_SKIP_OOM_GATE=1" "structural-bypass"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ OOM gate STRUCTURALLY bypassed via PYTEST_SKIP_OOM_GATE=1. Use this only if the gate itself is broken. If you meant '"'"'I want the heavy suite,'"'"' use PYTEST_ALLOW_HEAVY=1 instead."}}'
    exit 0
fi
if [ "${PYTEST_ALLOW_HEAVY:-}" = "1" ]; then
    audit_bypass "pre-test-oom-gate" "PYTEST_ALLOW_HEAVY=1" "semantic-bypass"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ OOM gate bypassed via PYTEST_ALLOW_HEAVY=1. Intentional heavy-suite run. Ensure no other Claude Code sessions or MCP processes are holding torch."}}'
    exit 0
fi

# JSON parsing: try jq, then python3. SELECTED BY SUCCESS, NOT BY PRESENCE.
#
# This used to bind the parser with `if command -v jq`, which asks whether the
# binary EXISTS. A jq that exists and is broken — wrong build, bad shared lib, a
# shim, a half-finished package upgrade — therefore won the selection and then
# returned nothing, and the python3 fallback was unreachable in exactly the case
# it was written for. `COMMAND` came back empty and the gate exited 0.
#
# Measured session-272: with jq stubbed to exit 127, and again with jq stubbed to
# exit 0 silently, 15/15 bare full-suite runs were ALLOWED — the gate fully off,
# no error, no log line. The push gate had already named this class in a comment
# and fixed it for itself only; it was live here and in the credential gate.
#
# Realism note: on this machine jq and python3 both resolve to the same conda
# prefix, so one broken environment degrades both parsers at once. That is why
# an unparseable input must DENY rather than fall through.
_parse_with_jq() { jq -r '.tool_input.command // ""' 2>/dev/null; }
_parse_with_python() {
    python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
        2>/dev/null
}

INPUT=$(cat)
COMMAND=""
# _PARSE_OK tracks whether a parser RAN SUCCESSFULLY — a different question from
# whether it returned anything. An empty `tool_input.command` parses fine and
# must ALLOW; input no parser could read leaves the gate blind and must DENY.
_PARSE_OK=0
if command -v jq >/dev/null 2>&1; then
    if COMMAND=$(printf '%s' "$INPUT" | _parse_with_jq); then
        # EXIT 0 IS NOT ENOUGH. A silent jq exits 0 and prints nothing, so
        # accepting a successful-but-empty result as authoritative made the
        # python3 fallback unreachable again and re-opened the bypass — the
        # BACKLOG #298 lesson recurring at a new call site. Only a NON-EMPTY jq
        # result ends the search; empty always falls through to python3, which
        # is then the authority on whether the command is genuinely empty.
        if [ -n "$COMMAND" ]; then
            _PARSE_OK=1
        fi
    else
        COMMAND=""
    fi
fi
if [ "$_PARSE_OK" = "0" ]; then
    debug "jq unusable, trying python3"
    if COMMAND=$(printf '%s' "$INPUT" | _parse_with_python); then
        _PARSE_OK=1
    else
        COMMAND=""
    fi
fi

if [ "$_PARSE_OK" = "0" ]; then
    # NO PARSER — scan the RAW payload rather than choosing between "allow
    # everything" and "deny everything". A pytest invocation appears literally in
    # the JSON, so the gate needs a haystack, not a parser. Denying outright
    # bricked every Bash call on a machine with a broken conda prefix (both jq
    # and python3 come from the same prefix here), and this repo already rejected
    # that trade for the HOME case: degrade LOUDLY, do not block.
    #
    # Coarse in the over-blocking direction only: a payload merely MENTIONING a
    # full-suite run can trip the gate, which costs one explained deny with a
    # documented bypass. Missing a real one costs the OOM this gate exists for.
    printf '%s\n' "[pre-test-oom-gate] input unparseable by jq AND python3 — scanning the RAW payload instead (coarse, still enforcing)" >&2

    # BUILTIN-ONLY TRIAGE. The normal pipeline cannot be reused on a raw payload:
    # its detector wants an executable position and its safe-subset analysis wants
    # command segments, and inside JSON the command is quoted, so `pytest` is
    # preceded by `"` rather than whitespace and the detector sees nothing.
    # Feeding it the payload therefore ALLOWED a bare full-suite run — measured.
    #
    # `case` only: grep, python3 and jq are all candidates for the thing that is
    # broken, so nothing here may depend on an external binary.
    case "$INPUT" in
    *pytest*) ;;                      # might be a test run — keep looking
    *) debug "no pytest in raw payload, allowing"; exit 0 ;;
    esac
    # NO TARGETED-SHAPE ESCAPE HERE, DELIBERATELY, AND THIS IS THE HONEST LIMIT.
    #
    # The obvious move is to allow payloads containing a targeted shape
    # (`tests/test_x.py`, `::`, `-m `, `-k `). It was written that way first and
    # it is WRONG, for the same reason the parsed path needed segments:
    #
    #   git commit -m "fix tests/test_a.py" && pytest tests/
    #
    # contains a targeted shape and is a bare full-suite run. Deciding WHOSE
    # argument a substring is requires parsing the command — and this branch
    # exists precisely because nothing can parse it. Substring triage cannot
    # answer the question, so it must not pretend to.
    #
    # So a blind gate treats any pytest-shaped payload as a full-suite run and
    # sends it to the environment risk checks. That over-blocks a genuinely
    # targeted run while both parsers are broken. The trade is deliberate: an
    # over-block costs one explained deny with a bypass that is REACHABLE (the
    # exported-env checks now run above the parse), while an under-block costs
    # the OOM this gate exists to prevent. Over-block, never under-block.
    # Looks like a full-suite run. Fall through to the environment risk checks
    # below, which decide on daemon/torch state — the same ones the parsed path
    # uses. SCAN_COMMAND is set to the payload so the bypass patterns still match.
    COMMAND="$INPUT"
    _RAW_TRIAGE=1
fi

# SCAN_COMMAND = the command with QUOTED-REGION CONTENTS removed, so the *detection*
# matcher below sees executable position only.
#
# This retires the accepted false positive documented below (`echo "run pytest tests/"`)
# and OPERATIONS T-143 (`pytest` inside a quoted commit message). Observed n=3 in one
# session — including a block on a read-only `echo` issued while reading THIS FILE to fix
# the very defect. Root cause + residuals: lib/shell-scan.sh.
#
# CRITICAL SPLIT — detection vs. argument analysis:
#   * DETECTION ("is this an executable pytest invocation?")  -> SCAN_COMMAND (stripped)
#   * ARGUMENT ANALYSIS ("what args did it get?")             -> COMMAND (raw)
# The safe-subset checks look for `-m "not slow"`, which is LEGITIMATELY QUOTED. Running
# those against the stripped string would erase the marker filter and start blocking the
# gate's own recommended happy path. Args stay raw; only the executable-position question
# uses the stripped string.
#
# Fail-safe: on any failure the helper returns the ORIGINAL string, so the gate degrades
# to its previous over-blocking behaviour — never to under-blocking.
# GUARDED — a failed `source` exits 1, which the harness reads as ALLOW, and
# `trap ... ERR` does NOT cover it (measured, bash 3.2). `lib/` is one symlink
# into the checkout, so moving the repo removes every library at once: the
# ordinary consequence of moving a directory, not an exotic case. BACKLOG #299.
if [ -r "$HOOK_DIR/lib/shell-scan.sh" ]; then
    source "$HOOK_DIR/lib/shell-scan.sh"
else
    echo "[pre-test-oom-gate] WARNING: lib/shell-scan.sh missing — degraded, matching against the RAW command (over-blocks)" >&2
    strip_quoted_regions() { printf '%s' "$1"; }
fi
SCAN_COMMAND=$(strip_quoted_regions "$COMMAND")

# GREP HEALTH CHECK + BUILTIN FALLBACK — see the identical block in
# pre-tool-content-security.sh for the full reasoning.
#
# `grep` is this gate's matcher and every call sits inside an `if`, which
# collapses match(0) / no-match(1) / ERROR(2+) into true/false. So "grep could
# not run" became "not a pytest command" and the gate ALLOWED a bare full-suite
# run. Measured session-272 with grep stubbed to 127.
#
# Bash's `[[ =~ ]]` is ERE and cannot go missing, so health-check grep once and
# route through the builtin when it is unusable. Every matching site below uses
# _match_regex — routing only the detector would leave the safe-subset checks
# failing, which would DENY a legitimate targeted run and trade a fail-open for
# a false positive on ordinary work. BACKLOG #299 Stage A.
# The probe tests BOTH directions. A stub that always exits 0 would pass a
# match-only probe while being useless — and "always matches" is as broken as
# "never matches". Requiring a correct match AND a correct non-match catches it.
# PROBE THE OPTION FORMS ACTUALLY IN USE, IN BOTH DIRECTIONS.
#
# This used to probe `grep -q` (a BRE match) while every real matcher below uses
# `-qE` or `-qF`. A grep that accepts plain -q but rejects -E/-F — a busybox or
# shim grep, a locale/regex-library breakage, a wrapper — passed the probe,
# _GREP_OK stayed 1, the builtin fallback was never engaged, and every match
# silently returned no-match. Measured session-272: 50/50 credential reads and
# 15/15 heavy pytest runs ALLOWED with the probe reporting healthy.
#
# Both directions matter for both forms: a stub that always exits 0 is as broken
# as one that never matches, and a match-only probe passes it.
if grep -qE 'pro[b]e' 2>/dev/null <<< 'probe' \
   && ! grep -qE 'ZZ_AB[S]ENT_ZZ' 2>/dev/null <<< 'probe' \
   && grep -qF -- 'rob' 2>/dev/null <<< 'probe' \
   && ! grep -qF -- 'ZZ_ABSENT_ZZ' 2>/dev/null <<< 'probe'; then
    _GREP_OK=1
else
    _GREP_OK=0
    printf '%s\n' "[oom-gate] grep unusable — matching with bash builtins" >&2
fi

_match_regex() {  # <haystack> <ERE>
    if [ "$_GREP_OK" = "1" ]; then
        grep -qE -- "$2" 2>/dev/null <<< "$1"
    else
        [[ "$1" =~ $2 ]]
    fi
}

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
# RETIRED FALSE POSITIVE (2026-07-13): this matcher used to run against the RAW command,
# so it also matched `echo "run pytest tests/"` and a commit message mentioning pytest
# (OPERATIONS T-143). That was documented as an accepted trade — "we'd rather block a
# harmless echo than miss a real invocation" — and it was defensible at n=1. At n=3 it
# was costing real friction, and friction is not free: a gate that cries wolf trains its
# users to reach for the bypass. Matching SCAN_COMMAND (quoted regions stripped) keeps
# every true positive and drops the class.
if [ "${_RAW_TRIAGE:-0}" != "1" ] && ! _match_regex "$SCAN_COMMAND" '(^|[[:space:]]|&&|;|\|)[[:space:]]*(pytest[[:space:]]|python[23]?[[:space:]]+-m[[:space:]]*pytest([[:space:]]|$))'; then
    debug "not a pytest command, allowing: $COMMAND"
    exit 0
fi

debug "pytest command detected: $COMMAND"

# ---------------------------------------------------------------------------
# Bypass env vars — structural and semantic
# ---------------------------------------------------------------------------
# We check BOTH the command string (inline env prefix: `PYTEST_ALLOW_HEAVY=1 pytest ...`)
# AND the hook's own environment (`PYTEST_ALLOW_HEAVY=1` exported in shell).
# The inline-prefix check matches SCAN_COMMAND, not COMMAND. "Is there a bypass
# assignment in EXECUTABLE POSITION?" is a detection question, and against the raw
# string a quoted MENTION of the variable — `git commit -m "set PYTEST_ALLOW_HEAVY=1
# to skip"` — silently bypassed the gate. Same defect class as the safe-subset
# scoping below, found in the same session-272 audit.
if _match_regex "$SCAN_COMMAND" '(^|[[:space:]])PYTEST_SKIP_OOM_GATE=1([[:space:]]|$)'; then
    debug "PYTEST_SKIP_OOM_GATE bypass triggered"
    audit_bypass "pre-test-oom-gate" "PYTEST_SKIP_OOM_GATE=1" "structural-bypass"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ OOM gate STRUCTURALLY bypassed via PYTEST_SKIP_OOM_GATE=1. Use this only if the gate itself is broken. If you meant '"'"'I want the heavy suite,'"'"' use PYTEST_ALLOW_HEAVY=1 instead."}}'
    exit 0
fi

if _match_regex "$SCAN_COMMAND" '(^|[[:space:]])PYTEST_ALLOW_HEAVY=1([[:space:]]|$)'; then
    debug "PYTEST_ALLOW_HEAVY bypass triggered"
    audit_bypass "pre-test-oom-gate" "PYTEST_ALLOW_HEAVY=1" "semantic-bypass"
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

# SCOPE — these patterns are evaluated against ONE pytest invocation's own
# segment, never against the whole command line.
#
# They used to match $COMMAND (raw), which is every command on the line at once.
# Measured consequence, no degraded environment required:
#
#   git commit -m "fix tests/test_server.py" && pytest tests/   -> ALLOWED
#   echo "touched tests/test_a.py" && pytest -v                 -> ALLOWED
#
# A path in a commit message does not make a run targeted, but the raw-string
# match could not tell whose argument it was. Quote characters are removed and
# their contents kept (shell_arg_segments), because `-m "not slow"` is a
# legitimately quoted argument that the detection view would erase.
#
# EVERY pytest segment must be safe for the run to be exempt. `pytest
# tests/test_a.py && pytest tests/` is not a targeted run just because its first
# half is.
_segment_is_safe() {  # <segment>
    local _seg="$1"
    # -m "not slow" in any quoting style (quotes already removed by this view)
    if _match_regex "$_seg" '-m[[:space:]]+["'"'"']?not[[:space:]]+slow["'"'"']?'; then
        debug "safe: marker filter 'not slow' detected"
        return 0
    fi
    # -k <expr> keyword selection
    if _match_regex "$_seg" '-k[[:space:]]+[^[:space:]]+'; then
        debug "safe: -k keyword selection detected"
        return 0
    fi
    # Explicit class/method selection via ::
    if _match_regex "$_seg" 'tests/[^[:space:]]*::'; then
        debug "safe: :: class/method selection detected"
        return 0
    fi
    # Single-file invocation (`pytest tests/test_X.py`, not `pytest tests/`).
    # No quote terminator is needed in the class any more: this view has already
    # removed the quote characters, so the path ends at whitespace or end of
    # segment. That terminator widening is what exposed the scoping defect above.
    if _match_regex "$_seg" 'tests/test_[A-Za-z0-9_]+\.py([[:space:]]|$)'; then
        debug "safe: single-file invocation detected"
        return 0
    fi
    return 1
}

# IS THIS SEGMENT A PYTEST INVOCATION? FIRST-TOKEN ANALYSIS, NOT A SUBSTRING MATCH.
#
# This was a substring regex, and that reintroduced — one layer down — the exact
# false-positive class the top-level detector retired at T-143. Segments keep
# their quoted CONTENTS (that is what makes them the argument view), so a quoted
# MENTION of pytest in a neighbouring command became a phantom pytest segment,
# and because every pytest segment must be safe, one phantom sank an otherwise
# targeted run. Measured — all three DENIED before this fix:
#
#   git commit -m "ran pytest tests/ before this" && pytest tests/test_a.py
#   grep -rn "pytest tests/" .claude/hooks && pytest tests/test_hooks.py
#   echo "remember to run pytest tests/" && pytest tests/test_a.py
#
# A gate that blocks a targeted test run because the commit message mentions
# pytest is the friction that trains bypass use, which is what the whole
# workstream exists to avoid.
#
# The structural answer is the one the push gate already uses: ask what the
# command IS, not what it contains. Skip leading `VAR=value` assignments, then
# require the first real token to be pytest (or python -m pytest). A mention
# inside an argument can never be in first-token position.
_segment_is_pytest() {  # <segment>
    local _rest="$1" _tok
    while :; do
        _rest="${_rest#"${_rest%%[![:space:]]*}"}"   # ltrim
        [ -n "$_rest" ] || return 1
        _tok="${_rest%%[[:space:]]*}"
        case "$_tok" in
        # env-var assignment prefix: strip and look at the next token
        [A-Za-z_]*=*)
            [ "$_tok" = "$_rest" ] && return 1
            _rest="${_rest#"$_tok"}"
            continue
            ;;
        # Command wrappers that precede the real executable. Skip the
        # wrapper, then skip its option-like args (dash-prefixed) and
        # bare durations (e.g. timeout 60, timeout 30s).
        timeout|time|nice|nohup|command|exec|env|stdbuf|ionice|taskset|chrt)
            [ "$_tok" = "$_rest" ] && return 1
            _rest="${_rest#"$_tok"}"
            _rest="${_rest#"${_rest%%[![:space:]]*}"}"
            [ -n "$_rest" ] || return 1
            _tok="${_rest%%[[:space:]]*}"
            while [[ "$_tok" == -* ]] || [[ "$_tok" =~ ^[0-9]+[smhd]?$ ]]; do
                [ "$_tok" = "$_rest" ] && return 1
                _rest="${_rest#"$_tok"}"
                _rest="${_rest#"${_rest%%[![:space:]]*}"}"
                [ -n "$_rest" ] || return 1
                _tok="${_rest%%[[:space:]]*}"
            done
            continue
            ;;
        esac
        break
    done
    case "$_tok" in
    pytest | */pytest) return 0 ;;
    python | python2 | python3 | */python | */python2 | */python3)
        # `python -m pytest`, with or without a space after -m
        _match_regex "$_rest" '^[^[:space:]]+[[:space:]]+-m[[:space:]]*pytest([[:space:]]|$)'
        return $?
        ;;
    esac
    return 1
}

_TOTAL_SEGMENTS_SEEN=0
_PYTEST_SEGMENTS_SEEN=0
_ALL_PYTEST_SEGMENTS_SAFE=1
while IFS= read -r _seg; do
    [ -n "$_seg" ] || continue
    _TOTAL_SEGMENTS_SEEN=$((_TOTAL_SEGMENTS_SEEN + 1))
    _segment_is_pytest "$_seg" || continue
    _PYTEST_SEGMENTS_SEEN=$((_PYTEST_SEGMENTS_SEEN + 1))
    if ! _segment_is_safe "$_seg"; then
        _ALL_PYTEST_SEGMENTS_SAFE=0
        debug "unsafe pytest segment: $_seg"
    fi
done <<EOF
$(shell_arg_segments "$COMMAND")
EOF

if [ "$_PYTEST_SEGMENTS_SEEN" -gt 0 ] && [ "$_ALL_PYTEST_SEGMENTS_SAFE" = "1" ]; then
    IS_SAFE_SUBSET=true
fi
# In raw-triage mode the segment loop sees JSON, not commands, so its verdict is
# meaningless. The builtin triage above already answered "targeted or not" and
# only a NOT-targeted payload reaches here.
if [ "${_RAW_TRIAGE:-0}" = "1" ]; then
    IS_SAFE_SUBSET=false
fi

# The top-level detector (line 316) is a SUBSTRING match that trades false
# positives for no false negatives. When it fires but the segment-level
# first-token analysis finds zero pytest segments, the command is NOT a pytest
# invocation — `grep pytest Makefile`, `rg pytest src/`, etc. Allow it.
# Guard: only when the splitter actually produced segments (_TOTAL > 0). If the
# splitter is broken/missing (shell-scan.sh absent), _TOTAL stays 0 and we fall
# through to environment checks — fail-closed, not fail-open.
if [ "$_PYTEST_SEGMENTS_SEEN" = "0" ] && [ "$_TOTAL_SEGMENTS_SEEN" -gt 0 ] && [ "${_RAW_TRIAGE:-0}" != "1" ]; then
    debug "no pytest invocation in executable position, allowing"
    exit 0
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
    # NORMALIZE EMPTY / NON-NUMERIC TO parse_error. THIS IS A FAIL-OPEN FIX.
    #
    # `|| echo "parse_error"` above fires only on a NONZERO exit. A python3 that
    # exits 0 printing nothing leaves DAEMON_AGE EMPTY — which is not
    # "parse_error", fails the numeric `-lt` test below (silenced by its own
    # `2>/dev/null`), and falls through to the `else` branch that reads
    # "stale — not blocking". The gate then allows a bare full-suite run while
    # its own comment above claims it assumes fresh on parse failure.
    #
    # BACKLOG #298 verbatim — "produced nothing" is not "produced a result" — at
    # a site this branch never swept. Measured in a Linux container: heartbeat
    # present and fresh, python3 stubbed silent, `pytest tests/` ALLOWED with
    # debug showing `heartbeat age: ` and `stale (s old)`.
    #
    # It survived five review rounds and the GATES × DEGRADATIONS matrix because
    # the author's machine had 13 torch-holding processes, so the unrelated
    # ps-based risk signal fired and masked it. A clean CI runner has neither
    # signal, which is why CI caught what every local run could not.
    #
    # Scoped deliberately to EMPTY and NON-NUMERIC only: a real numeric stale
    # reading still takes the not-blocking path exactly as before, so a crashed
    # daemon does not start blocking legitimate full-suite runs.
    case "$DAEMON_AGE" in
    '' | *[!0-9]*) DAEMON_AGE="parse_error" ;;
    esac
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

# `redact_secrets` now lives in lib/redact.sh — the content-security hook's deny
# log needs the identical function, and two copies of a redactor (one guarding a
# SECURITY log) would drift the moment a pattern is added to only one of them.
# Sourced defensively: if the lib is missing, fall back to a pass-through that
# still logs, because losing the deny record is worse than an unredacted one on a
# local diagnostic file — and the missing lib announces itself on stderr.
if [ -r "$HOOK_DIR/lib/redact.sh" ]; then
    source "$HOOK_DIR/lib/redact.sh"
else
    echo "[oom-gate] WARNING: lib/redact.sh missing — deny log will not be redacted" >&2
    redact_secrets() { cat; }
fi

# Record the deny for the OOM gate monitoring log (COMPLIANCE-REVIEW.md Check 6b).
# Use plain ASCII key=value format — avoid `printf %q` (bash 3.2 on macOS
# byte-escapes non-ASCII characters, corrupting the unicode bullets in SIGNALS).
# Fields: timestamp (ISO8601 UTC), daemon_alive flag, torch_proc_count,
# and the command with newlines replaced by spaces for single-line logging.
mkdir -p "$(dirname "$DENY_LOG")"
DENY_LINE_CMD=$(printf '%s' "$COMMAND" | tr '\n\r' '  ' | redact_secrets | cut -c1-500)
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
# CAPTURE-AND-CHECK, not `if ! python3`. The old guard fired only on a NONZERO
# exit, so a python3 that exits 0 printing NOTHING emitted no JSON, skipped the
# fallback, and fell through to `exit 0` — silently allowing a command this gate
# had ALREADY DECIDED to deny. Same defect as BACKLOG #298 one layer down: for a
# deny-by-assertion contract, "produced nothing" and "succeeded" cannot be the
# same thing. Verified session-272 by stubbing the emitter.
#
# Deny-path only, so this cannot brick a session: an allowed command never
# reaches this code, and the only new behaviour is denying when we already
# decided to deny but could not say so.
_DENY_JSON=$(python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$REASON" 2>/dev/null) || _DENY_JSON=""

if [ -n "$_DENY_JSON" ]; then
    printf '%s' "$_DENY_JSON"
    exit 0
fi

# python3 unavailable, crashed, or produced nothing. Fall back to plain stderr +
# non-zero exit, which Claude Code treats as a structural deny. Intentionally
# terse — we cannot emit the rich multi-line REASON without a working encoder.
echo "OOM PREVENTION GATE: blocked. python3 unavailable or emitted no JSON; see .claude/hooks/pre-test-oom-gate.sh and use PYTEST_SKIP_OOM_GATE=1 to emergency-bypass." >&2
exit 2
