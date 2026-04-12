#!/usr/bin/env bash
# PreToolUse hook — Pre-push quality gate
# Blocks git push unless tests were run and subagent reviews performed for risky changes.
#
# Per LEARNING-LOG: "advisory failed at 87%; structural blocking achieves near-100%"
# Hard mode from day one. Emergency skip: QUALITY_GATE_SKIP=true
#
# Checks:
#   1. Tests run this session (pytest in transcript)
#   2. Subagent review for risky changes (core code files or new src files)
#   3. Governance content review for principle file changes
#   4. Completion checklist consulted (COMPLETION-CHECKLIST.md read)\
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

# Emergency skip
if [ "${QUALITY_GATE_SKIP:-false}" = "true" ]; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠️ QUALITY GATE SKIPPED via QUALITY_GATE_SKIP=true"}}'
    exit 0
fi

# Get transcript path from hook input
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
    debug "Transcript not available, fail-open"
    exit 0  # Fail-open if transcript unavailable
fi

# Determine what files changed since last push
# Try @{push} first (tracks upstream), then origin/main..HEAD, then HEAD~1
CHANGED_FILES=$(git diff --name-only @{push}.. 2>/dev/null || git diff --name-only origin/main..HEAD 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")

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
NEW_SRC_FILES=$(git diff --diff-filter=A --name-only @{push}.. 2>/dev/null || git diff --diff-filter=A --name-only origin/main..HEAD 2>/dev/null || echo "")
NEW_SRC_FILES=$(echo "$NEW_SRC_FILES" | grep -E '^src/' 2>/dev/null || true)

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

# Report issues
if [ -n "$ISSUES" ]; then
    debug "BLOCKING: $ISSUES"
    # Escape for JSON
    ESCAPED_ISSUES=$(echo "$ISSUES" | sed 's/"/\\"/g' | tr '\n' ' ')
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"QUALITY GATE: ${ESCAPED_ISSUES}\"}}"
else
    debug "All checks passed, allowing push"
fi

exit 0
