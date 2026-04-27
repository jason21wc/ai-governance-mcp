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
#   4. Completion checklist consulted (COMPLETION-CHECKLIST.md read)
#   5. Multi-commit push requires explicit acknowledgment (closes review-attribution gap
#      where commits 1-2 had reviewer evidence but commit 3 was added later unreviewed)
#   6. Diff secret-scan — high-precision regex against AWS keys, OpenAI keys, GitHub
#      tokens, JWTs (replaces visual diff inspector function the user-mediated push
#      provided; per BACKLOG #140 §8.3.4 amendment 2026-04-26 enabling AI auto-push
#      on explicit user authorization)
#   7. (WARN-only, advisory — not a blocking gate): TDD test-existence scan for new
#      src/*.py files. Bypass via TDD_TEST_EXISTENCE_SKIP=1; promotion to BLOCK is
#      event-driven via V-008 in workflows/COMPLIANCE-REVIEW.md.
#   Escape hatch: docs-only changes skip review requirement (except governance)
#
# Environment variables:
#   QUALITY_GATE_SKIP=true — Emergency skip (documented override, not silent bypass)
#   QUALITY_GATE_DEBUG=true — Enable stderr debug logging

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

debug() {
  if [ "${QUALITY_GATE_DEBUG:-false}" = "true" ]; then
    echo "[quality-gate] $1" >&2
  fi
}

# Read stdin (hook input JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

# Only gate on git push commands — precise regex match, not substring
if ! echo "$COMMAND" | grep -qE '^\s*git\s+push(\s|$)'; then
    debug "Not a git push command, skipping"
    exit 0
fi

debug "Git push detected, running quality gate checks"

# Check 0: Force-push attempts blocked here as defense-in-depth (also denied at
# settings.json layer per Anthropic's documented Git Safety Protocol "NEVER force-push
# to main/master"). Belt-and-suspenders ensures the rule holds even if settings.json
# is loosened. Skip-bypass intentionally unavailable here — force-push to main is one
# of the few cases where structural-only blocking is correct.
if echo "$COMMAND" | grep -qE '(\-\-force(\s|$|=)|\s-f(\s|$)|\-\-force-with-lease)'; then
    debug "Force-push detected, blocking"
    python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': 'QUALITY GATE: Force-push attempts blocked per Anthropic Git Safety Protocol. If you genuinely need to force-push (rare — usually rebase + new commit is safer), have the user run it manually via shell.'
    }
}))
" 2>/dev/null || true
    exit 0
fi

# Emergency skip
if [ "${QUALITY_GATE_SKIP:-false}" = "true" ]; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ QUALITY GATE SKIPPED via QUALITY_GATE_SKIP=true"}}'
    exit 0
fi

# Get transcript path from hook input
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
    debug "Transcript not available, fail-closed"
    python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': 'QUALITY GATE: Transcript unavailable — cannot verify pre-push checks. Set QUALITY_GATE_SKIP=true to override.'
    }
}))
" 2>/dev/null || true
    exit 0
fi

# Determine commit-range for diff/count operations.
# Try @{push} first (tracks upstream), then origin/main..HEAD, then HEAD~1..HEAD.
# Factored as RANGE so all checks (CHANGED_FILES, NEW_SRC_FILES, Check 5 commit-count,
# Check 6 secret-scan) share the same fallback chain. Fail-closed: if no range can be
# determined, RANGE stays empty and downstream checks treat that as "scan range
# undeterminable" rather than silently scanning nothing.
if git rev-parse @{push} >/dev/null 2>&1; then
    RANGE="@{push}..HEAD"
elif git rev-parse origin/main >/dev/null 2>&1; then
    RANGE="origin/main..HEAD"
elif git rev-parse HEAD~1 >/dev/null 2>&1; then
    RANGE="HEAD~1..HEAD"
else
    RANGE=""
fi
debug "Commit range: ${RANGE:-(undeterminable)}"

CHANGED_FILES=""
if [ -n "$RANGE" ]; then
    CHANGED_FILES=$(git diff --name-only $RANGE 2>/dev/null || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    debug "No changed files detected, allowing push"
    exit 0
fi

debug "Changed files: $(echo "$CHANGED_FILES" | tr '\n' ' ')"

# Governance principle files require subagent review (contrarian/coherence/validator)
GOVERNANCE_FILES=$(echo "$CHANGED_FILES" | grep -E '(constitution\.md|title-[0-9]+-[a-z][-a-z]*\.md)$' | grep -v '\-cfr\.md' || true)
debug "Governance files: $(echo "$GOVERNANCE_FILES" | tr '\n' ' ')"

# Escape hatch: docs-only changes (only .md files, .json config, or benchmark files)
# BUT governance principle files are NOT exempt — they require review
NON_DOC_FILES=$(echo "$CHANGED_FILES" | grep -v -E '\.(md|json)$' | grep -v 'tests/benchmarks/' || true)
if [ -z "$NON_DOC_FILES" ] && [ -z "$GOVERNANCE_FILES" ]; then
    debug "Docs/config-only changes (no governance content), skipping review requirement"
    exit 0
fi

ISSUES=""

# Check 1: Were tests run this session?
TESTS_RUN=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "pytest" "$TRANSCRIPT" 2>/dev/null || echo "false")
debug "Tests run: $TESTS_RUN"
if [ "$TESTS_RUN" = "false" ]; then
    ISSUES="${ISSUES}Tests not run this session. Run pytest before pushing. "
fi

# Check 2: Risky files changed without subagent review?
RISKY_FILES=$(echo "$CHANGED_FILES" | grep -E '(server\.py|extractor\.py|retrieval\.py|config\.py)$' || true)
NEW_SRC_FILES=""
if [ -n "$RANGE" ]; then
    NEW_SRC_FILES=$(git diff --diff-filter=A --name-only $RANGE 2>/dev/null | grep -E '^src/' 2>/dev/null || true)
fi

debug "Risky files: $(echo "$RISKY_FILES" | tr '\n' ' ')"
debug "New src files: $(echo "$NEW_SRC_FILES" | tr '\n' ' ')"

if [ -n "$RISKY_FILES" ] || [ -n "$NEW_SRC_FILES" ]; then
    # Check if code-reviewer or security-auditor was invoked
    REVIEW_DONE="false"
    for PATTERN in "code-reviewer" "security-auditor" "code_reviewer" "security_auditor"; do
        FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "$PATTERN" "$TRANSCRIPT" 2>/dev/null || echo "false")
        if [ "$FOUND" = "true" ]; then
            REVIEW_DONE="true"
            break
        fi
    done
    debug "Review done: $REVIEW_DONE"
    if [ "$REVIEW_DONE" = "false" ]; then
        ISSUES="${ISSUES}Risky changes (core code or new src files) without subagent review. Run code-reviewer or security-auditor before pushing. "
    fi
fi

# Check 3: Governance content files changed without governance subagent review?
if [ -n "$GOVERNANCE_FILES" ]; then
    GOV_REVIEW_DONE="false"
    for PATTERN in "contrarian-reviewer" "contrarian_reviewer" "coherence-auditor" "coherence_auditor" "validator"; do
        FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "$PATTERN" "$TRANSCRIPT" 2>/dev/null || echo "false")
        if [ "$FOUND" = "true" ]; then
            GOV_REVIEW_DONE="true"
            break
        fi
    done
    debug "Governance review done: $GOV_REVIEW_DONE"
    if [ "$GOV_REVIEW_DONE" = "false" ]; then
        ISSUES="${ISSUES}Governance principle files changed without subagent review. Run contrarian-reviewer, coherence-auditor, or validator before pushing. "
    fi
fi

# Check 4: Was the completion checklist consulted this session?
CHECKLIST_READ="false"
for PATTERN in "COMPLETION-CHECKLIST" "completion sequence" "completion checklist"; do
    FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "$PATTERN" "$TRANSCRIPT" 2>/dev/null || echo "false")
    if [ "$FOUND" = "true" ]; then
        CHECKLIST_READ="true"
        break
    fi
done
debug "Completion checklist consulted: $CHECKLIST_READ"
if [ "$CHECKLIST_READ" = "false" ]; then
    ISSUES="${ISSUES}Completion checklist not consulted. Read COMPLETION-CHECKLIST.md and verify applicable items before pushing. "
fi

# Check 5: Multi-commit push requires explicit acknowledgment.
# Closes the per-commit review-attribution gap: existing checks (1-4) verify reviewer
# fired *somewhere* in transcript, but can't tell whether commits 1-2 had reviewers
# while commit 3 was added later unreviewed. For multi-commit pushes, require an
# explicit user utterance acknowledging the count or "all" — forces the user to
# confirm the full bundle, not just the first commit. (Per BACKLOG #140 §8.3.4
# amendment 2026-04-26 + pre-edit contrarian-reviewer audit `adf19d07b51fc2f3b`
# GAP-2.) Uses shared $RANGE for fallback consistency with Checks 2 + 6;
# fail-closed if range undeterminable.
if [ -n "$RANGE" ]; then
    COMMITS_AHEAD=$(git rev-list --count $RANGE 2>/dev/null || echo "0")
else
    COMMITS_AHEAD="0"
    debug "Range undeterminable — multi-commit check fail-closed"
    ISSUES="${ISSUES}Push range undeterminable (no @{push}, no origin/main, no HEAD~1). Cannot verify multi-commit acknowledgment or run secret-scan. Verify upstream branch tracking is set, or set QUALITY_GATE_SKIP=true to override. "
fi
debug "Commits ahead: $COMMITS_AHEAD"
if [ "$COMMITS_AHEAD" -gt 1 ] 2>/dev/null; then
    MULTI_ACK="false"
    for PATTERN in "push all" "ship all" "push ${COMMITS_AHEAD} commit" "push everything" "push every"; do
        FOUND=$(python3 "$HOOK_DIR/scan_transcript.py" --pattern "$PATTERN" "$TRANSCRIPT" 2>/dev/null || echo "false")
        if [ "$FOUND" = "true" ]; then
            MULTI_ACK="true"
            break
        fi
    done
    debug "Multi-commit ack: $MULTI_ACK"
    if [ "$MULTI_ACK" = "false" ]; then
        ISSUES="${ISSUES}Multi-commit push (${COMMITS_AHEAD} commits ahead). Confirm explicitly with 'push all', 'ship all', 'push ${COMMITS_AHEAD} commits', or 'push everything' so all commits are intentionally bundled. If false positive (e.g., bundle reviewed via other means), set QUALITY_GATE_SKIP=true. "
    fi
fi

# Check 6: Diff secret-scan — high-precision regex against AWS keys, OpenAI keys,
# Anthropic keys, GitHub tokens, JWT-shaped tokens, PEM private keys. Replaces the
# visual diff inspector function the user-mediated push provided (per BACKLOG #140
# §8.3.4 amendment 2026-04-26: when user no longer types `! git push`, they're not
# visually checking the diff before push; this is the structural replacement).
# Fail-closed: if range undeterminable, the warning above already added to ISSUES;
# skip scan rather than silently no-op. False positives acceptable — pre-push,
# recoverable via amend. Bypass via QUALITY_GATE_SKIP=true if a legitimate test
# fixture trips the regex.
SECRET_PATTERNS='AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9_-]{40,}|ghp_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{20,}|gho_[a-zA-Z0-9]{20,}|ghs_[a-zA-Z0-9]{20,}|eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}|-----BEGIN [A-Z]+ PRIVATE KEY-----'
SECRETS_FOUND=""
if [ -n "$RANGE" ]; then
    SECRETS_FOUND=$(git diff $RANGE 2>/dev/null | grep -E '^[+]' | grep -E "$SECRET_PATTERNS" 2>/dev/null | head -3 || true)
fi
if [ -n "$SECRETS_FOUND" ]; then
    SECRETS_PREVIEW=$(echo "$SECRETS_FOUND" | head -1 | cut -c1-80 | tr -d '\n')
    debug "Potential secret detected: $SECRETS_PREVIEW"
    ISSUES="${ISSUES}Potential secret/credential detected in diff (preview: ${SECRETS_PREVIEW}...). Review and redact before pushing — use 'git rebase -i' to amend or 'git filter-repo' if accidental. If false positive, set QUALITY_GATE_SKIP=true. "
fi

# Check 7 (WARN-only, Commit 6 of Superpowers plan): TDD test-existence
# scan for new src/*.py files. Surfaces unpaired src files on stderr; does
# NOT add to ISSUES (no block). Promotion to BLOCK is event-driven (V-008
# in COMPLIANCE-REVIEW.md): "promote to BLOCK after first coherence-audit
# finding flags WARN-mode pattern actually firing on real code." Bypass
# via TDD_TEST_EXISTENCE_SKIP=1.
if [ "${TDD_TEST_EXISTENCE_SKIP:-}" != "1" ] && [ -n "$NEW_SRC_FILES" ]; then
    TDD_OUT=$(printf '%s\n' "$NEW_SRC_FILES" | python3 "$HOOK_DIR/scan_transcript.py" --tdd-test-existence - 2>/dev/null || echo "error")
    if [ "$TDD_OUT" = "warn" ]; then
        TDD_FINDINGS=$(printf '%s\n' "$NEW_SRC_FILES" | python3 "$HOOK_DIR/scan_transcript.py" --tdd-test-existence - 2>&1 >/dev/null || true)
        echo "[tdd-test-existence] WARN — new src files lack paired test files (advisory; bypass with TDD_TEST_EXISTENCE_SKIP=1):" >&2
        echo "$TDD_FINDINGS" >&2
        echo "[tdd-test-existence] If this WARN later turns out to pre-figure a real defect (the unpaired src file shipped a regression paired tests would have caught), file the trigger event in V-008 row of workflows/COMPLIANCE-REVIEW.md — closes the event-driven WARN→BLOCK promotion loop without depending on human memory." >&2
    fi
fi

# Report issues
if [ -n "$ISSUES" ]; then
    debug "BLOCKING: $ISSUES"
    python3 -c "
import json, sys
msg = sys.argv[1]
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': 'QUALITY GATE: ' + msg
    }
}))
" "$ISSUES" 2>/dev/null || true
else
    debug "All checks passed, allowing push"
fi

exit 0
