#!/usr/bin/env bash
# PreToolUse hook — checks transcript for evaluate_governance() AND query_project() calls
# before allowing file-modifying operations (Bash|Edit|Write)
#
# Scans for both tools using shared scan_transcript.py with adaptive output.
#
# Modes:
#   Hard (default): Returns permissionDecision: "deny" for missing tool(s)
#   Soft (opt-in): Injects additionalContext reminder for missing tool(s)
#
# Environment variables:
#   GOVERNANCE_SOFT_MODE=true    — Use soft mode for governance (reminder instead of block)
#   CE_SOFT_MODE=true            — Use soft mode for CE (reminder instead of block)
#   GOVERNANCE_HARD_MODE=false   — Legacy: same as GOVERNANCE_SOFT_MODE=true
#   CE_HARD_MODE=false           — Legacy: same as CE_SOFT_MODE=true
#   GOVERNANCE_RECENCY_WINDOW=200 — Only scan last N transcript lines (0 = scan all)
#   GOVERNANCE_TOOL_NAME=...     — Override governance tool name (default: mcp__ai-governance__evaluate_governance)
#   CE_TOOL_NAME=...             — Override CE tool name (default: mcp__context-engine__query_project)
#   GOVERNANCE_HOOK_DEBUG=true   — Enable stderr debug logging
#   READONLY_BASH_SKIP=true      — Disable read-only Bash allowlist (require governance for all Bash)
#   MCP_DETECT_SKIP=true         — Disable MCP-availability auto-degrade (strict hard mode even when the MCP servers are not configured in this session)
#   GOVERNANCE_PROJECT_ROOT=...  — Override project root for MCP-config detection (test hermeticity)
#
# Exit 0 always when outputting JSON. Fail-closed on errors (hard mode default).

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
    echo "[pre-tool-governance-check] WARNING: lib/audit-bypass.sh missing — degraded, bypasses will not be audited" >&2
    audit_bypass() { :; }
fi

debug() {
  if [ "${GOVERNANCE_HOOK_DEBUG:-false}" = "true" ]; then
    echo "[governance-hook] $1" >&2
  fi
}

# ---------------------------------------------------------------------------
# emit_deny <reason> — the ONLY way this gate says no. BACKLOG #303 (plan tasks
# A4b + A10, approved in Stage A and never delivered).
#
# Each deny was `python3 -c "...json..." 2>/dev/null || true` followed by exit 0.
# `|| true` catches a NONZERO exit; a python3 that exits 0 printing nothing
# leaves stdout EMPTY, and empty stdout with exit 0 IS AN ALLOW under the harness
# contract. The decision was computed and then discarded. The other four gates
# got this fix in Stage A; this one — which fires on every Bash, Edit and Write —
# did not.
#
# WHY THE CALL SITE MATTERS MORE THAN THE HELPER (task A10's whole point): the
# deny emitter below shares an `if/else` with the SOFT-MODE ALLOW emitter. A
# fallback placed after the `fi` would deny every governed tool call in the
# repo. So emit_deny is called strictly INSIDE the `SHOULD_DENY` branch, and the
# `else` branch keeps its `|| true` — a soft-mode reminder that fails to
# serialise must still ALLOW, because it was never a denial.
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
    printf '%s\n' "[pre-tool-governance-check] python3 could not emit the verdict; denying structurally. Reason: $_reason" >&2
    exit 2
}

# Read hook input from stdin
INPUT=$(cat)

debug "PreToolUse hook invoked"


# _parse_field <jq-filter> <python-key-path> — PARSER SELECTED BY SUCCESS.
#
# Both extractions below used `if command -v jq`, which asks whether the binary
# EXISTS. A jq that exists and is broken therefore won the selection and returned
# nothing, making the python3 branch unreachable in exactly the case it was
# written for. Measured session-272: with jq stubbed, TRANSCRIPT_PATH came back
# empty, the gate took its "transcript missing" branch, and a FULLY COMPLIANT
# session was denied every Bash, Edit and Write — a brick, not a safety margin.
#
# This is the last live instance of the class fixed in the other four gates
# (#299 closed — both stages shipped; this instance accepted as residual).
_parse_field() {
    local _jqf="$1" _pykey="$2" _out=""
    if command -v jq >/dev/null 2>&1; then
        _out=$(printf '%s' "$INPUT" | jq -r "$_jqf" 2>/dev/null) || _out=""
        [ "$_out" = "null" ] && _out=""
    fi
    if [ -z "$_out" ]; then
        _out=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(''); raise SystemExit
cur = d
for k in '$_pykey'.split('.'):
    cur = cur.get(k, '') if isinstance(cur, dict) else ''
print(cur if isinstance(cur, str) else '')
" 2>/dev/null) || _out=""
    fi
    if [ -z "$_out" ]; then
        # BOTH PARSERS DEAD. Extracting a flat string field from JSON does not
        # actually require a parser — the value is right there in the bytes.
        # Without this, a dead jq AND python3 left TRANSCRIPT_PATH empty, the gate
        # took its "transcript unreadable" branch, and every Bash/Edit/Write in a
        # COMPLIANT session was denied. Fail-closed on paper, a brick in practice.
        #
        # Deliberately naive: flat `"key":"value"` only, no nesting, no escapes.
        # It exists to keep a working session working, not to be a JSON parser. A
        # miss here just leaves the field empty, which is where we already were.
        local _k="${_pykey##*.}" _rest
        case "$INPUT" in
        *"\"$_k\""*)
            _rest="${INPUT#*\"$_k\"}"      # after the key
            _rest="${_rest#*:}"             # after the colon
            _rest="${_rest#"${_rest%%[![:space:]]*}"}"
            case "$_rest" in
            '"'*)
                _rest="${_rest#\"}"
                _out="${_rest%%\"*}"
                ;;
            esac
            ;;
        esac
    fi
    printf '%s' "$_out"
}

# Extract transcript_path from hook JSON
# Try jq first (matches existing CI hook pattern), fall back to python3
TRANSCRIPT_PATH=$(_parse_field '.transcript_path // ""' 'transcript_path')

# ---------------------------------------------------------------------------
# Read-only Bash command allowlist
# Per governance skip list: "reading files" doesn't require governance.
# Provably read-only Bash commands (no redirects, no chaining, all segments
# match a known safe command list — including read-only `git` and `gh`
# subcommands) skip the governance check entirely.
# Disable with READONLY_BASH_SKIP=true.
# ---------------------------------------------------------------------------

TOOL_NAME=""
TOOL_CMD=""
TOOL_NAME=$(_parse_field '.tool_name // ""' 'tool_name')
if [ "$TOOL_NAME" = "Bash" ]; then
  TOOL_CMD=$(_parse_field '.tool_input.command // ""' 'tool_input.command')
fi

if [ "$TOOL_NAME" = "Bash" ] && [ -n "$TOOL_CMD" ] && [ "${READONLY_BASH_SKIP:-false}" != "true" ]; then
  IS_READONLY=$(python3 -c "
import re, sys
cmd = sys.argv[1]
# Chaining operators make the command non-read-only
if re.search(r'&&|\|\||;', cmd):
    print('false')
    sys.exit(0)
# Strip safe stderr redirections before checking for output redirects
cleaned = re.sub(r'2>>[^ ;|&()<>]*|2>&[^ ;|&()<>]*|2>\s*[^ ;|&()<>]*', '', cmd)
if re.search(r'>>', cleaned) or re.search(r'>', cleaned):
    print('false')
    sys.exit(0)
# Split on pipe and check each segment
READONLY_CMDS = {
    'ls', 'find', 'grep', 'egrep', 'fgrep', 'wc', 'head', 'tail', 'cat',
    'file', 'stat', 'which', 'pwd', 'tree', 'du', 'df', 'diff', 'sort',
    'uniq', 'comm', 'jq', 'column', 'basename', 'dirname', 'realpath',
    'readlink', 'sha256sum', 'md5',
}
MUTATION_FLAGS = {
    'find': {'-delete', '-exec', '-execdir', '-ok', '-okdir'},
    'sort': {'-o', '--output'},
}
GIT_READONLY = {
    'log', 'blame', 'diff', 'show', 'status',
    'rev-parse', 'ls-files', 'ls-tree', 'name-rev', 'shortlog', 'describe',
    'for-each-ref',
}
# Dual-use git subcommands: read-only in their bare/listing forms but MUTATING
# with other arguments (git stash, git branch -D, git tag -d, git remote add).
# Listing them in GIT_READONLY would blanket-allow the mutating forms to skip
# the governance gate, so they live here as explicit read-only (subcommand,
# next-token) pairs — anything unenumerated fails CLOSED and is forced through
# the gate. Mirrors the GH_READONLY pattern. (BACKLOG #62 = stash; extended to
# branch/tag/remote, session-213, after a fail-open contrarian review.)
GIT_READONLY_PAIRS = {
    ('stash', 'list'), ('stash', 'show'),
    ('branch', ''), ('branch', '-a'), ('branch', '-r'), ('branch', '-v'),
    ('branch', '-vv'), ('branch', '--all'), ('branch', '--remotes'),
    ('branch', '--list'), ('branch', '--show-current'),
    ('branch', '--contains'), ('branch', '--merged'), ('branch', '--no-merged'),
    ('tag', ''), ('tag', '-l'), ('tag', '--list'), ('tag', '-n'),
    ('tag', '--contains'), ('tag', '--points-at'),
    ('remote', ''), ('remote', '-v'), ('remote', '--verbose'),
    ('remote', 'show'), ('remote', 'get-url'),
}
# gh is dual-use (gh pr merge / gh repo delete mutate remote state), so the
# base command cannot be blanket-allowed. Allow only enumerated read-only
# (command, subcommand) pairs; gh api is GET-only unless a write flag appears.
GH_READONLY = {
    ('repo', 'view'), ('repo', 'list'),
    ('pr', 'view'), ('pr', 'list'), ('pr', 'diff'), ('pr', 'checks'), ('pr', 'status'),
    ('issue', 'view'), ('issue', 'list'), ('issue', 'status'),
    ('run', 'view'), ('run', 'list'), ('run', 'watch'),
    ('release', 'view'), ('release', 'list'),
    ('workflow', 'view'), ('workflow', 'list'),
    ('label', 'list'), ('cache', 'list'),
    ('auth', 'status'),
    ('search', 'prs'), ('search', 'issues'), ('search', 'repos'), ('search', 'code'),
}
GH_API_WRITE_PREFIXES = ('-X', '--method', '-f', '-F', '--field', '--raw-field', '--input')
for segment in cmd.split('|'):
    parts = segment.strip().split()
    if not parts:
        print('false')
        sys.exit(0)
    base = parts[0].rsplit('/', 1)[-1]
    if base == 'git':
        subcmd = parts[1] if len(parts) > 1 else ''
        if subcmd not in GIT_READONLY:
            pair = (subcmd, parts[2] if len(parts) > 2 else '')
            if pair not in GIT_READONLY_PAIRS:
                print('false')
                sys.exit(0)
    elif base == 'gh':
        args = parts[1:]
        if not args:
            print('false')
            sys.exit(0)
        if args[0] == 'api':
            # gh api defaults to GET; a method/field write flag makes it a mutation
            if any(a.startswith(GH_API_WRITE_PREFIXES) for a in args[1:]):
                print('false')
                sys.exit(0)
        else:
            pair = (args[0], args[1] if len(args) > 1 else '')
            if pair not in GH_READONLY:
                print('false')
                sys.exit(0)
    elif base in READONLY_CMDS:
        if base in MUTATION_FLAGS:
            flags = MUTATION_FLAGS[base]
            if any(p in flags or p.split('=', 1)[0] in flags for p in parts[1:]):
                print('false')
                sys.exit(0)
    else:
        print('false')
        sys.exit(0)
print('true')
" "$TOOL_CMD" 2>/dev/null) || IS_READONLY="false"

  if [ "$IS_READONLY" = "true" ]; then
    debug "Read-only Bash command — governance check skipped"
    exit 0
  fi
fi

# Determine enforcement mode
# New defaults: hard mode ON. Soft mode is the opt-in escape hatch.
# Support both new (SOFT_MODE) and legacy (HARD_MODE) env vars.
GOV_SOFT="${GOVERNANCE_SOFT_MODE:-false}"
CE_SOFT="${CE_SOFT_MODE:-false}"

# Legacy compat: HARD_MODE=false means soft mode
if [ "${GOVERNANCE_HARD_MODE:-}" = "false" ]; then
  GOV_SOFT="true"
fi
if [ "${CE_HARD_MODE:-}" = "false" ]; then
  CE_SOFT="true"
fi

if [ "$GOV_SOFT" = "true" ]; then
  audit_bypass "pre-tool-governance-check" "GOVERNANCE_SOFT_MODE=true" "soft-mode"
fi
if [ "$CE_SOFT" = "true" ]; then
  audit_bypass "pre-tool-governance-check" "CE_SOFT_MODE=true" "soft-mode"
fi

# ---------------------------------------------------------------------------
# MCP availability auto-degrade (cloud/CCR sessions)
# Hard mode assumes the gated MCP tools are callable. In a session whose
# config surfaces contain no entry for a server (cloud routine / CCR clone /
# fresh checkout), the model structurally CANNOT call it — fail-closed there
# is a deadlock, not enforcement. Degrade that tool's gate to soft mode
# (reminder) and audit-log the degrade. Detection is configuration presence,
# not server health.
#
# CORRECTION (2026-07-29, measured): this comment used to claim
# "configured-but-broken still fails loudly at call time." It does not. A broken
# server returns its error as a NORMAL tool result (error_code TOOL_ERROR /
# RATE_LIMITED, never the MCP protocol error channel, so is_error is unset), and
# scan_transcript.py credits a tool_use regardless of what came back — so a
# configured-but-broken server fails SILENTLY here: exit 0, no reminder. Verified
# by running this hook against synthetic transcripts for four failure shapes
# (TOOL_ERROR with and without is_error, RATE_LIMITED, and no result at all);
# all four were silently allowed.
#
# Deliberately NOT made fail-closed. The recency gate is documented as ADVISORY
# and model-satisfiable by design (PROJECT-MEMORY, "Act-Intrinsic Value/Locus
# Gate"), and a deny here would be unrecoverable: the model cannot restart an MCP
# server, and GOVERNANCE_SOFT_MODE is read from the parent process env, so it
# cannot be set from inside a blocked session. That is a deadlock, not
# enforcement — the same reasoning the block above applies to an absent server.
# The measurement-side fix landed instead, in scripts/analyze_compliance.py.
# MCP_DETECT_SKIP=true disables detection (strict hard mode regardless).
# ---------------------------------------------------------------------------
GOV_AUTO_DEGRADED="false"
CE_AUTO_DEGRADED="false"
if [ "${MCP_DETECT_SKIP:-false}" != "true" ]; then
  # GOVERNANCE_PROJECT_ROOT override exists for test hermeticity (tests point
  # it at a sandbox so they don't read the real repo's config surfaces).
  PROJECT_ROOT="${GOVERNANCE_PROJECT_ROOT:-$(cd "$HOOK_DIR/../.." && pwd)}"
  mcp_configured() {
    # $1 = MCP server name; match it as a quoted JSON key in any config
    # surface this session could have loaded. This is name-PRESENCE detection
    # (a disabled-but-listed server still reads as configured → stays hard,
    # the safe over-blocking direction), not server health.
    # ${HOME:-} guard: an unset HOME under set -u would abort the script,
    # which Claude Code treats as non-blocking — i.e. fail-OPEN. With the
    # guard, the path is simply absent and detection proceeds.
    local name="$1" f
    # `grep` missing outright cannot even reach the rc check below, and a missing
    # matcher must not read as "absent" either. Bash builtins cannot go missing.
    # A grep that ALWAYS exits 1 is indistinguishable from "genuinely absent" from the
    # exit code alone, so the rc>1 rule below cannot see it. Probe with a string
    # that must match; if the probe fails, grep's no-match is not evidence.
    if ! grep -q -- 'probe' 2>/dev/null <<< 'probe'; then
        printf '%s\n' "[governance-hook] grep unusable (failed its own probe) — matching config with bash builtins" >&2
        for f in "$PROJECT_ROOT/.mcp.json" "${HOME:-}/.claude.json" \
                 "$PROJECT_ROOT/.claude/settings.json" \
                 "$PROJECT_ROOT/.claude/settings.local.json"; do
            [ -f "$f" ] || continue
            [ -r "$f" ] || return 0
            case "$(cat "$f" 2>/dev/null)" in *"\"$name\""*) return 0 ;; esac
        done
        return 1
    fi
    if ! command -v grep >/dev/null 2>&1; then
      printf '%s\n' "[governance-hook] grep unavailable — matching config with bash builtins" >&2
      for f in "$PROJECT_ROOT/.mcp.json" "${HOME:-}/.claude.json" \
               "$PROJECT_ROOT/.claude/settings.json" \
               "$PROJECT_ROOT/.claude/settings.local.json"; do
        [ -f "$f" ] || continue
        [ -r "$f" ] || return 0
        case "$(cat "$f" 2>/dev/null)" in *"\"$name\""*) return 0 ;; esac
      done
      return 1
    fi
    for f in "$PROJECT_ROOT/.mcp.json" "${HOME:-}/.claude.json" \
             "$PROJECT_ROOT/.claude/settings.json" \
             "$PROJECT_ROOT/.claude/settings.local.json"; do
      if [ -f "$f" ]; then
        if [ ! -r "$f" ]; then
          # Present but unreadable: cannot prove absence — assume configured
          # (stay hard) rather than degrade on a permissions accident.
          return 0
        fi
        # DISTINGUISH "ABSENT" FROM "COULD NOT CHECK". This was `if grep -q ...`,
        # which collapses match(0) / no-match(1) / ERROR(2+) into true/false — so a
        # broken or shadowed `grep` read as "server not configured" and silently
        # auto-degraded this gate from hard to advisory. Measured session-272: with
        # grep stubbed to 127, a non-compliant Write was ALLOWED, and the debug log
        # said "ai-governance MCP not configured". Nothing about the config had
        # changed; only the tool doing the looking had.
        #
        # The correct rule is already stated three lines above for an unreadable
        # file — CANNOT PROVE ABSENCE, so assume configured and stay hard. A failed
        # grep is the same epistemic situation, so it takes the same branch.
        #
        # Exit codes, not truthiness:
        #   0    found        -> configured, stay hard
        #   1    not found    -> genuinely absent, the degrade is legitimate
        #   2+   grep errored -> cannot prove absence, stay hard
        #
        # Direction check, because getting this backwards is the dangerous half:
        # over-returning 0 keeps the gate HARD, which at worst asks for a
        # governance call that was already going to happen. Under-returning turns
        # the gate off. The legitimate degrade — a session with genuinely no MCP
        # configured, where forcing hard mode is a deadlock the bypass cannot
        # escape — still works, because that case exits 1, not 2.
        _mcp_rc=0
        grep -q -- "\"$name\"" "$f" 2>/dev/null || _mcp_rc=$?
        if [ "$_mcp_rc" -eq 0 ]; then
          return 0
        elif [ "$_mcp_rc" -gt 1 ]; then
          printf '%s\n' "[governance-hook] grep failed while checking $f (rc=$_mcp_rc) — cannot prove absence, staying HARD" >&2
          return 0
        fi
      fi
    done
    return 1
  }
  if [ "$GOV_SOFT" != "true" ] && ! mcp_configured "ai-governance"; then
    GOV_SOFT="true"
    GOV_AUTO_DEGRADED="true"
    audit_bypass "pre-tool-governance-check" "auto-degrade: ai-governance MCP server not configured in any session config surface" "soft-mode-auto"
    debug "ai-governance MCP not configured — gate auto-degraded to advisory"
  fi
  if [ "$CE_SOFT" != "true" ] && ! mcp_configured "context-engine"; then
    CE_SOFT="true"
    CE_AUTO_DEGRADED="true"
    audit_bypass "pre-tool-governance-check" "auto-degrade: context-engine MCP server not configured in any session config surface" "soft-mode-auto"
    debug "context-engine MCP not configured — gate auto-degraded to advisory"
  fi
fi

# Handle missing/unreadable transcript
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -r "$TRANSCRIPT_PATH" ]; then
  if [ "$GOV_SOFT" = "true" ] && [ "$CE_SOFT" = "true" ]; then
    # Both soft: fail-open — allow silently
    debug "Transcript missing/unreadable, both soft mode: allowing"
    exit 0
  fi
  # At least one hard mode: fail-closed — block when transcript unavailable
  debug "Transcript missing/unreadable, hard mode active: blocking"
  emit_deny "Compliance check unavailable: transcript missing or unreadable. Cannot verify governance/CE compliance."
fi

# Scan transcript using shared scanner with recency window
GOV_TOOL="${GOVERNANCE_TOOL_NAME:-mcp__ai-governance__evaluate_governance}"
CE_TOOL="${CE_TOOL_NAME:-mcp__context-engine__query_project}"
RECENCY_WINDOW="${GOVERNANCE_RECENCY_WINDOW:-500}"

debug "Scanning transcript for $GOV_TOOL and $CE_TOOL (window=$RECENCY_WINDOW)"

SCAN_RESULT=$(python3 "$HOOK_DIR/scan_transcript.py" "$GOV_TOOL" "$CE_TOOL" "$TRANSCRIPT_PATH" "$RECENCY_WINDOW" 2>/dev/null) || SCAN_RESULT="__scan_failed__"
# A SENTINEL, NOT "neither". The fallback used to be `|| SCAN_RESULT="neither"`,
# which substitutes a VALID result for a failure — so "the scanner could not run"
# became indistinguishable from "the scanner ran and found nothing", and the raw
# fallback below (which keys on an unexpected value) could never fire. Measured:
# a COMPLIANT session with python3 broken was denied, because the failure wore
# the costume of a legitimate answer.

# NORMALIZE ANYTHING UNEXPECTED TO "neither". THIRD INSTANCE OF ONE CLASS.
#
# `|| SCAN_RESULT="neither"` fires only on a NONZERO exit. A python3 that exits 0
# printing nothing leaves this EMPTY, and empty matches none of both/gov_only/
# ce_only/neither below — so both reminders stay empty, nothing is "missing", and
# a non-compliant call is ALLOWED. Measured: a non-compliant Write with python3
# stubbed silent was allowed by this gate.
#
# Same defect as BACKLOG #298 (strip_quoted_regions), as the push gate's parse,
# and as the OOM gate's heartbeat age — all in session-272, all `$(...)` with a
# `||` fallback that only catches nonzero exit. "Produced nothing" is not a
# result, and here the DETECTOR is python3, so a broken python3 blinds the gate
# before the emitter ever matters.
#
# "neither" is the conservative value: it assumes NO governance tool was called,
# which produces a reminder in soft mode and a deny in hard mode.
case "$SCAN_RESULT" in
both | gov_only | ce_only | neither) ;;
*)
    # SCANNER UNUSABLE — FALL BACK TO THE RAW TRANSCRIPT, DO NOT ASSUME "neither".
    #
    # Assuming "neither" is fail-CLOSED and was the first fix here. It is also a
    # brick: this gate fires on every Bash, Edit and Write, so a broken python3
    # denied EVERY action in the session, compliant or not, escapable only by an
    # env var. Measured — a fully compliant transcript was denied with the parser
    # stubbed.
    #
    # The dilemma is false, exactly as it was for the credential gate. A tool_use
    # entry names the tool LITERALLY in the transcript JSONL, so the scanner needs
    # a haystack, not a parser. Grep the file for the two tool names and derive
    # the same four-valued result. Coarser — it cannot honour the recency window,
    # so an old call counts — and coarse in the ALLOW direction, which is why it
    # is a fallback and not the primary path.
    #
    # `case` on file contents, not grep alone: grep is itself a candidate for the
    # broken tool, and a matcher that cannot run must not decide the gate is off.
    debug "scan unusable (${SCAN_RESULT:-<empty>}) — falling back to a raw transcript scan"
    _raw=""
    [ -r "$TRANSCRIPT_PATH" ] && _raw=$(cat "$TRANSCRIPT_PATH" 2>/dev/null)
    _gov_seen=0; _ce_seen=0
    case "$_raw" in *"$GOV_TOOL"*) _gov_seen=1 ;; esac
    case "$_raw" in *"$CE_TOOL"*) _ce_seen=1 ;; esac
    if [ "$_gov_seen" = 1 ] && [ "$_ce_seen" = 1 ]; then
        SCAN_RESULT="both"
    elif [ "$_gov_seen" = 1 ]; then
        SCAN_RESULT="gov_only"
    elif [ "$_ce_seen" = 1 ]; then
        SCAN_RESULT="ce_only"
    else
        SCAN_RESULT="neither"
    fi
    debug "raw fallback result: $SCAN_RESULT"
    ;;
esac

debug "Scan result: $SCAN_RESULT"

# If both found, allow silently
if [ "$SCAN_RESULT" = "both" ]; then
  debug "Both governance and CE found — allowing"
  exit 0
fi

# Build adaptive reminder based on what's missing
GOV_REMINDER=""
CE_REMINDER=""

if [ "$SCAN_RESULT" = "ce_only" ] || [ "$SCAN_RESULT" = "neither" ]; then
  GOV_REMINDER='GOVERNANCE NOT DETECTED: No evaluate_governance() call found in recent transcript. You MUST call evaluate_governance(planned_action="...") before proceeding with file-modifying actions.'
fi

if [ "$SCAN_RESULT" = "gov_only" ] || [ "$SCAN_RESULT" = "neither" ]; then
  CE_REMINDER='CONTEXT ENGINE NOT DETECTED: No query_project() call found in recent transcript. You MUST call query_project(query="...") before creating or modifying code or content to discover existing patterns.'
fi

# Combine reminders
if [ -n "$GOV_REMINDER" ] && [ -n "$CE_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER $CE_REMINDER"
elif [ -n "$GOV_REMINDER" ]; then
  FULL_REMINDER="$GOV_REMINDER"
else
  FULL_REMINDER="$CE_REMINDER"
fi

# Surface the auto-degrade so the model and user know enforcement is advisory
# in this session (and why), instead of silently weakening the gate.
if [ "$GOV_AUTO_DEGRADED" = "true" ] || [ "$CE_AUTO_DEGRADED" = "true" ]; then
  FULL_REMINDER="$FULL_REMINDER [NOTE: hard-mode gate auto-degraded to advisory — the required MCP server(s) are not configured in this session (cloud/CCR or fresh clone), so the gated tools cannot be called. On a configured machine this gate blocks. MCP_DETECT_SKIP=true restores fail-closed.]"
fi

# Determine if we should deny based on mode
SHOULD_DENY="false"

# Deny if governance is missing and governance is NOT soft mode
if [ -n "$GOV_REMINDER" ] && [ "$GOV_SOFT" != "true" ]; then
  SHOULD_DENY="true"
fi
# Deny if CE is missing and CE is NOT soft mode
if [ -n "$CE_REMINDER" ] && [ "$CE_SOFT" != "true" ]; then
  SHOULD_DENY="true"
fi

if [ "$SHOULD_DENY" = "true" ]; then
  debug "Hard mode active for missing tool(s) — blocking"
  emit_deny "$FULL_REMINDER"
else
  # Soft mode: inject reminder as additionalContext
  debug "Soft mode — injecting reminder for missing tool(s)"
  python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'additionalContext': msg
    }
}))
" "$FULL_REMINDER" 2>/dev/null || true
fi
