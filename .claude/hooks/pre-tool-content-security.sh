#!/usr/bin/env bash
# PreToolUse hook — Content-level credential path gate
# Blocks Bash commands that access credential file paths on the host machine.
# Defense-in-depth Layer 2 alongside Read-tool deny rules in settings (Layer 1).
#
# Credential paths blocked:
#   ~/.ssh/*  ~/.aws/*  ~/.gnupg/*  ~/.netrc  ~/.docker/config.json
#   ~/.kube/config  ~/.npmrc  /etc/ssl/private/*  *.key (private keys)
#
# Threat model: AI-initiated Bash commands that read credential files the
# machine holds. User-level Read deny rules (Layer 1) cover the Read tool;
# this hook covers Bash cat/head/tail/less/cp/scp/curl/base64 etc.
#
# Escape hatch:
#   CONTENT_SECURITY_SKIP=1  — bypass when the gate is wrong
#
# Author: Claude Opus 4.6 + Jason Collier, 2026-05-03
# Origin: BACKLOG #19 (Content-Level Security Enforcement)

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# GUARDED — a failed `source` exits 1, which the harness reads as ALLOW, and
# `trap ... ERR` does NOT cover it (measured, bash 3.2). `lib/` is one symlink
# into the checkout, so moving the repo removes every library at once: the
# ordinary consequence of moving a directory, not an exotic case. BACKLOG #299.
if [ -r "$HOOK_DIR/lib/audit-bypass.sh" ]; then
    source "$HOOK_DIR/lib/audit-bypass.sh"
else
    echo "[pre-tool-content-security] WARNING: lib/audit-bypass.sh missing — degraded, bypasses will not be audited" >&2
    audit_bypass() { :; }
fi

# Shared with pre-test-oom-gate.sh. See lib/redact.sh for why it is not copied.
if [ -r "$HOOK_DIR/lib/redact.sh" ]; then
    source "$HOOK_DIR/lib/redact.sh"
else
    echo "[content-security] WARNING: lib/redact.sh missing — deny log unredacted" >&2
    redact_secrets() { cat; }
fi

# Deny log. Derived from $HOME so the suite's autouse `isolate_home` fixture
# (tests/conftest.py) redirects it automatically — the 100 bogus
# CONTENT_SECURITY_SKIP entries in the bypass audit log came from test writes to
# a production path, and a NEW log with its own override variable would just
# reintroduce that at a fresh call site.
DENY_LOG="${HOME:-}/.claude/content-security-denies.log"

# Fail-closed: unhandled errors → exit 2 (deny)
trap 'exit 2' ERR

# ---------------------------------------------------------------------------
# Parse stdin
# ---------------------------------------------------------------------------

# THE BYPASS IS CHECKED BEFORE THE PARSE, AND THE ORDER IS THE WHOLE POINT.
#
# `CONTENT_SECURITY_SKIP` reads this hook's OWN ENVIRONMENT — it needs no parser.
# It used to sit BELOW the parse block, underneath a deny that fires when neither
# jq nor python3 can read the payload. Since that deny's condition matches every
# Claude Code Bash payload, a machine with both parsers broken denied EVERY Bash
# call — `ls`, `git`, even `brew install jq` — while the deny message told the
# user to escape with a variable that was checked ten lines further down and
# therefore unreachable. Recovery meant editing settings.json from outside the
# session. Measured session-272; the reviewer found it by reading control flow.
#
# The two-fault case is not hypothetical here: jq and python3 resolve to the same
# conda prefix on this machine, so ONE broken environment takes out both.
if [ "${CONTENT_SECURITY_SKIP:-}" = "1" ]; then
    audit_bypass "pre-tool-content-security" "CONTENT_SECURITY_SKIP=1" "full-bypass"
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ Content security gate bypassed via CONTENT_SECURITY_SKIP=1. Credential path access allowed."}}'
    exit 0
fi

# PARSER SELECTED BY SUCCESS, NOT BY PRESENCE.
#
# `if command -v jq` asks whether the binary EXISTS. A jq that exists and is
# broken — a shim, a bad build, a half-upgraded package, a dead conda prefix —
# won that selection and returned nothing, making the python3 fallback
# unreachable in precisely the case it was written for. COMMAND came back empty
# and this gate exited 0.
#
# Measured session-272 with jq stubbed to exit 127, and again with jq stubbed to
# exit 0 silently: 50/50 credential reads ALLOWED, no error, no log line. A full
# silent bypass of the credential gate. On this machine jq and python3 resolve to
# the same conda prefix, so one broken environment takes out both parsers — which
# is why an unparseable input has to deny rather than fall through.
_parse_with_jq() { jq -r '.tool_input.command // ""' 2>/dev/null; }
_parse_with_python() {
    python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
        2>/dev/null
}

INPUT=$(cat)
COMMAND=""
# _PARSE_OK tracks whether a parser RAN SUCCESSFULLY, which is a different
# question from whether it returned anything. An empty `tool_input.command` is
# ordinary input that parses fine and must ALLOW; input that no parser could read
# leaves the gate blind and must DENY. Conflating them denied every empty
# command — caught by the existing suite's edge-case test.
_PARSE_OK=0
if command -v jq >/dev/null 2>&1; then
    if COMMAND=$(printf '%s\n' "$INPUT" | _parse_with_jq); then
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
    if COMMAND=$(printf '%s\n' "$INPUT" | _parse_with_python); then
        _PARSE_OK=1
    else
        COMMAND=""
    fi
fi

if [ "$_PARSE_OK" = "0" ]; then
    # NO PARSER — AND THE ANSWER IS NEITHER "ALLOW" NOR "DENY EVERYTHING".
    #
    # Allowing was the original bug: a blind credential gate waving every command
    # through. But denying outright bricks the session, and this repo already
    # rejected exactly that trade once — see the HOME sentinel above, and
    # LEARNING-LOG 2026-06-10: where a legitimate context structurally cannot
    # satisfy a gate, degrade LOUDLY rather than block. A first attempt at this
    # deny made every Bash call fail on a machine with a broken conda prefix.
    #
    # The dilemma is false. A credential path appears LITERALLY in the raw JSON
    # payload, so the gate does not need a parser to see one — it needs a
    # haystack. Scanning the unparsed payload keeps real enforcement with no
    # brick: `ls -la` matches nothing and passes, a credential read still matches
    # and is denied. Coarser than parsed matching (it also sees other JSON
    # fields), and coarse in the over-blocking direction, which is the correct
    # one for a safety gate.
    printf '%s\n' "content-security: input unparseable by jq AND python3 — scanning the RAW payload instead (coarse, still enforcing)" >&2
    COMMAND="$INPUT"
fi

if [ -z "$COMMAND" ]; then
    exit 0
fi

# (The CONTENT_SECURITY_SKIP bypass was moved ABOVE the parse block — see the
# comment there. It must not sit behind a deny it is the documented escape for.)

# ---------------------------------------------------------------------------
# Credential path detection
# ---------------------------------------------------------------------------
# Expand ~ and $HOME to the literal home directory for matching.
# Match against both symbolic forms (~/, $HOME/, ${HOME}/) and the expanded path.

# HERE `HOME` IS A DECISION INPUT, NOT A LOG PATH — so the remedy differs from
# the one used in pre-test-oom-gate.sh and pre-exit-plan-mode-gate.sh, where it
# only places a log file.
#
# A SENTINEL, not a default and not a refusal. Three options were tried; the
# first two are both wrong, and the tests caught the second one.
#
#   ${HOME}          abort under `set -u` -> rc 1 -> ALLOW. The gate silently
#                    stops existing. This is what shipped.
#   ${HOME:-}        the home value becomes empty, so "${HOME_LITERAL}/.npmrc"
#                    degrades to the bare substring "/.npmrc" and denies any
#                    absolute path containing it. Measured: `cat /srv/app/.npmrc`
#                    flips allow -> deny. A new false-positive class on a gate
#                    that fires on every Bash call, and a gate that cries wolf
#                    trains the bypass that disables all of it.
#   deny outright    fail-closed, but it denies EVERY Bash call in any context
#                    with no HOME (a container, cron, `env -i`). LEARNING-LOG
#                    2026-06-10: where a legitimate context structurally cannot
#                    satisfy a gate, degrade LOUDLY rather than block.
#
# The sentinel leaves the pattern array and regex shapes exactly as they are
# while matching nothing real, so the expanded-path patterns go quiet. The
# symbolic forms (~/, $HOME/, ${HOME}/) below do not depend on this value and
# keep enforcing. Narrow degradation, announced on stderr. BACKLOG #299 Stage A.
#
# TWO FORMS, AND USING THE WRONG ONE SILENTLY DISABLES SEVEN PATTERNS.
#   HOME_LITERAL — raw. For the CRED_PATTERNS array, which is matched as a
#                  FIXED STRING (`grep -qF` / `case`). A regex-escaped value here
#                  looks for a literal backslash that is not in the command.
#   HOME_ESCAPED — regex-metacharacters escaped. For BARE_DIR_PATTERN only,
#                  which is matched as an ERE.
#
# The array used HOME_ESCAPED until session-272. Measured: with
# HOME=/Users/jane.doe the escaped value is `/Users/jane\.doe`, and all seven
# expanded-path credential patterns stopped matching — a credential read was
# ALLOWED. `first.last` is a standard corporate username shape, and `+` and `(`
# are legal in a home path too, so this is ordinary input, not a degraded
# environment. Found by an independent audit of the Stage A diff; the bug is
# older than that diff, which had rewritten this exact block without noticing it.
if [ -n "${HOME:-}" ]; then
    HOME_DIR="${HOME}"
    HOME_LITERAL="${HOME_DIR}"
    # `|| HOME_ESCAPED=""` IS LOAD-BEARING, NOT DEFENSIVE NOISE. Under `set -e`
    # plus `trap 'exit 2' ERR`, a failing `sed` makes this top-level assignment
    # non-zero, the trap fires, and the gate exits 2 — DENYING EVERY BASH CALL
    # before the emptiness guard below can run. Measured: with sed stubbed to 127,
    # `echo hi` returned rc=2. The fallback that was written to handle a broken
    # sed was unreachable *because* sed was broken.
    HOME_ESCAPED=$(printf '%s' "$HOME_DIR" | sed 's/[.[\*^$()+?{|]/\\&/g') || HOME_ESCAPED=""
    # An empty value would turn "${HOME_ESCAPED}/.npmrc" into the bare substring
    # "/.npmrc" and deny ordinary project paths. Fall back to the sentinel:
    # narrower enforcement, never a false deny.
    if [ -z "$HOME_ESCAPED" ]; then
        HOME_ESCAPED='__HOME_UNSET_NO_MATCH_SENTINEL__'
        printf '%s\n' "content-security: could not escape HOME — bare-directory pattern disabled" >&2
    fi
else
    HOME_DIR=""
    HOME_LITERAL='__HOME_UNSET_NO_MATCH_SENTINEL__'
    HOME_ESCAPED='__HOME_UNSET_NO_MATCH_SENTINEL__'
    printf '%s\n' "content-security: HOME unset/empty — literal home-path patterns disabled; ~/ and \$HOME symbolic forms still enforced" >&2
fi

# Build the credential path patterns. Each pattern is checked against the
# command string. A match anywhere in the command triggers a deny.
#
# Scoping: only MACHINE-LEVEL credential paths (~/.<dir>). Project-relative
# .env files are covered by Read deny rules and are not this hook's scope
# (project .env may be legitimate; ~/.ssh is never legitimate for AI access).
# shellcheck disable=SC2088  # the tilde MUST stay literal — see below
#
# SC2088 ("tilde does not expand in quotes") fires on the seven `~/...` entries
# and is a FALSE POSITIVE here, silenced deliberately rather than left to be
# rediscovered. These are not filesystem paths this script opens; they are
# patterns matched against the COMMAND TEXT at line 322. The hook is looking for
# the literal characters `~/.ssh/` in a command the model wants to run, so
# expanding them would DEFEAT that arm. The expanded form is already covered
# separately by the `${HOME_LITERAL}/...` entries below, and the `$HOME/` and
# `${HOME}/` symbolic forms by their own entries — three parallel spellings on
# purpose. `tests/test_enforcement.py` asserts the literal `~/.ssh/id_rsa` form
# is caught.
#
# Recorded because the obvious "fix" is a silent security regression: changing
# `~/` to `$HOME/` here would delete a real detection arm while making a linter
# happy. Flagged 2026-08-15 when shellcheck was first run against this repo and
# initially mis-triaged as the BACKLOG #324 path-resolution class — it is not.
CRED_PATTERNS=(
    '~/.ssh/'
    '~/.aws/'
    '~/.gnupg/'
    '~/.netrc'
    '~/.docker/config.json'
    '~/.kube/config'
    '~/.npmrc'
    "\$HOME/.ssh/"
    "\${HOME}/.ssh/"
    "\$HOME/.aws/"
    "\${HOME}/.aws/"
    "\$HOME/.gnupg/"
    "\${HOME}/.gnupg/"
    "\$HOME/.netrc"
    "\${HOME}/.netrc"
    "\$HOME/.docker/config.json"
    "\${HOME}/.docker/config.json"
    "\$HOME/.kube/config"
    "\${HOME}/.kube/config"
    "\$HOME/.npmrc"
    "\${HOME}/.npmrc"
    "${HOME_LITERAL}/.ssh/"
    "${HOME_LITERAL}/.aws/"
    "${HOME_LITERAL}/.gnupg/"
    "${HOME_LITERAL}/.netrc"
    "${HOME_LITERAL}/.docker/config.json"
    "${HOME_LITERAL}/.kube/config"
    "${HOME_LITERAL}/.npmrc"
    '/etc/ssl/private/'
)

# Also match private key file extensions anywhere in the path
KEY_PATTERN='\.key([[:space:]]|$)'

# WHEN `grep` IS THE MATCHER, A BROKEN `grep` IS A TOTAL SILENT BYPASS.
#
# Every match below ran as `if ... | grep -q ...; then`. `grep` exits 0 on match,
# 1 on no-match, and 2+ on ERROR — and an `if` condition collapses all three into
# true/false, so "grep could not run" became "found nothing dangerous". Measured
# session-272 with grep stubbed to 127: a credential read was ALLOWED, rc 0, no
# error, no log line. This is a cleaner instance of the BACKLOG #298 class than
# #298 itself, and nothing probed it because the matrix stubbed only python3/jq.
#
# The fix cannot be "deny when grep fails" alone: with grep dead the gate cannot
# tell a credential read from `echo hi`, so that would deny every Bash call and
# brick the session. Both directions have to hold.
#
# Bash builtins cannot go missing. `case` is exactly `grep -qF` for a fixed
# string, and `[[ =~ ]]` is ERE like `grep -qE`. So health-check grep ONCE and
# route through builtins if it is unusable — the gate keeps discriminating with
# no external dependency at all. BACKLOG #299 Stage A.
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
    printf '%s\n' "content-security: grep unusable — matching with bash builtins" >&2
fi

_match_fixed() {  # <haystack> <needle>
    if [ "$_GREP_OK" = "1" ]; then
        grep -qF -- "$2" 2>/dev/null <<< "$1"
    else
        case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac
    fi
}

_match_regex() {  # <haystack> <ERE>
    if [ "$_GREP_OK" = "1" ]; then
        grep -qE -- "$2" 2>/dev/null <<< "$1"
    else
        [[ "$1" =~ $2 ]]
    fi
}

MATCHED_PATH=""

for pattern in "${CRED_PATTERNS[@]}"; do
    if _match_fixed "$COMMAND" "$pattern"; then
        MATCHED_PATH="$pattern"
        break
    fi
done

if [ -z "$MATCHED_PATH" ]; then
    if _match_regex "$COMMAND" "$KEY_PATTERN"; then
        MATCHED_PATH="*.key (private key file)"
    fi
fi

if [ -z "$MATCHED_PATH" ]; then
    BARE_DIR_PATTERN="(~|\\\$HOME|\\\$\{HOME\}|${HOME_ESCAPED})/\.(ssh|aws|gnupg)([[:space:];|&><)\`]|$)"
    if _match_regex "$COMMAND" "$BARE_DIR_PATTERN"; then
        MATCHED_PATH="credential directory (bare reference)"
    fi
fi

# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

if [ -z "$MATCHED_PATH" ]; then
    exit 0
fi

printf '%s\n' "content-security: denied [${MATCHED_PATH}]" >&2

# ---------------------------------------------------------------------------
# Record the deny
# ---------------------------------------------------------------------------
# WHY THIS EXISTS
# ---------------
# Until now this hook denied to stderr and stopped. Nothing persisted, so its
# production false-positive rate was unmeasurable BY CONSTRUCTION — the one
# question a compliance review needs to answer about a gate ("is it crying
# wolf?") could not be asked. The OOM gate has had a deny log throughout, and it
# is precisely why its FP class could be quantified (9 TP / 4 FP of 13 denies)
# and then fixed with a corpus rather than argued about.
#
# This matters more here than elsewhere: this hook is the only safety hook that
# does NOT use lib/shell-scan.sh, so it still matches raw command text and
# cannot tell an executable path from one quoted inside a grep pattern or a
# commit message. That is the same class T-143 closed for the other gates. The
# fix is deliberately NOT bundled here — T-143's own precedent is that a safety
# matcher gets changed against a real TP/FP corpus, not a synthetic one, and
# this log is what produces that corpus.
#
# Purely additive: it records a decision already made and changes no outcome.
# Every failure path is absorbed (`|| true`) because losing a diagnostic line
# must never turn a deny into an allow.
#
# The command text is redacted and truncated. It contains credential PATHS, not
# credential CONTENTS — the blocked command never ran — but paths are still
# local diagnostics, not something to publish.
if [ -n "${HOME:-}" ]; then
    {
        mkdir -p "$(dirname "$DENY_LOG")" 2>/dev/null || true
        # Cap at 100KB, rotate by tailing 500 lines. `wc -c` not `stat`
        # (macOS/Linux flag divergence) — same approach as lib/audit-bypass.sh.
        if [ -f "$DENY_LOG" ]; then
            _sz=$(wc -c < "$DENY_LOG" 2>/dev/null | tr -d ' ' || echo 0)
            if [ "${_sz:-0}" -gt 102400 ]; then
                tail -n 500 "$DENY_LOG" > "$DENY_LOG.tmp" 2>/dev/null \
                    && mv "$DENY_LOG.tmp" "$DENY_LOG" 2>/dev/null || true
            fi
        fi
        _cmd=$(printf '%s' "$COMMAND" | tr '\n\r' '  ' | redact_secrets | cut -c1-300)
        printf '%s deny pattern=%s cwd=%s cmd=%s\n' \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            "$MATCHED_PATH" \
            "${PWD:-unknown}" \
            "$_cmd" >> "$DENY_LOG" 2>/dev/null || true
    } || true
fi

REASON="CREDENTIAL ACCESS BLOCKED: command references a credential path.

This hook blocks Bash commands that access machine-level credential files
(~/.ssh/*, ~/.aws/*, ~/.gnupg/*, ~/.netrc, ~/.docker/config.json,
~/.kube/config, ~/.npmrc, /etc/ssl/private/*, *.key).

These files contain secrets that should never be read by AI agents.

If this is a false positive (e.g., you genuinely need to access this path):
  CONTENT_SECURITY_SKIP=1 <your command>

Origin: BACKLOG #19 (Content-Level Security Enforcement, Layer 2)"

# CAPTURE-AND-CHECK, not `if ! python3` — see the identical note in
# pre-test-oom-gate.sh. The old guard fired only on a NONZERO exit, so a python3
# that exits 0 printing nothing emitted no JSON and fell through to `exit 0`,
# allowing a credential access this gate had already decided to deny. Same
# defect as BACKLOG #298 at the emission point. Deny-path only: an allowed
# command never reaches here, so this cannot brick a session.
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

echo "CREDENTIAL ACCESS BLOCKED. python3 unavailable or emitted no JSON; use CONTENT_SECURITY_SKIP=1 to bypass." >&2
exit 2
