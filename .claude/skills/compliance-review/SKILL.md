---
description: Run the governance compliance review workflow — 12 checks covering hook integrity, enforcement mode, effectiveness tracking, behavioral canary prompts, MCP health, OOM gate activity, backlog staleness, constitutional register integrity, and CI storage budget. Cadence is every 10-15 days or immediately after hook/behavioral-floor modifications.
disable-model-invocation: true
allowed-tools: Bash Read Edit Agent
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Current hooks:** !`ls .claude/hooks/ 2>/dev/null | sort`
**Enforcement vars:** !`echo "GOVERNANCE_SOFT_MODE=${GOVERNANCE_SOFT_MODE:-unset} CE_SOFT_MODE=${CE_SOFT_MODE:-unset} QUALITY_GATE_SKIP=${QUALITY_GATE_SKIP:-unset} CONTENT_SECURITY_SKIP=${CONTENT_SECURITY_SKIP:-unset}"`
**OOM deny log lines:** !`wc -l ~/.context-engine/oom-gate-denies.log 2>/dev/null || echo "0 (no log)"`
**Phase 2 marker:** !`test -f ~/.context-engine/PHASE2_TRIGGERED && echo "FIRED — read contents" || echo "clear"`

```!
echo "=== Last 3 compliance review commits ==="
git log --oneline --grep="[Cc]ompliance" -3 2>/dev/null || echo "(no matches)"
echo ""
echo "=== LEARNING-LOG entries >60 days ==="
CUTOFF=$(date -v-60d "+%Y-%m-%d" 2>/dev/null || date -d "60 days ago" "+%Y-%m-%d" 2>/dev/null)
echo "60-day cutoff: $CUTOFF"
```

## Instructions

You are running a governance compliance review per `workflows/COMPLIANCE-REVIEW.md`. This is the canonical procedure — read that file now to get current check definitions, pass/fail criteria, and review history tables.

### Execution Protocol

1. **Call `evaluate_governance(planned_action="compliance review execution")`** before any writes.

2. **Read `workflows/COMPLIANCE-REVIEW.md`** in full — it contains the check definitions, pass/fail thresholds, and review history tables you will update.

3. **Determine the next review number** from the Review Log table at the bottom of COMPLIANCE-REVIEW.md.

4. **Execute each Ongoing Check (1 through 10)** in order. For each check:
   - Read the check definition and pass/fail criteria from COMPLIANCE-REVIEW.md
   - Run the required commands (many are pre-populated in the Context Snapshot above)
   - Evaluate the result against the criteria
   - Record PASS, FAIL, or N/A with concise notes

5. **For Check 5 (Behavioral canary prompts + session audit):**
   - Decide whether canary prompts (a-c) should run this review or be deferred per the execution-only session precedent (Reviews #3-6)
   - For session audit (d): spawn a **validator subagent** with the Check 5d evaluation rubric from COMPLIANCE-REVIEW.md. The subagent needs fresh context per `multi-quality-validation-independence`.
   - If insufficient session scope exists for meaningful audit (e.g., session-start review), document the deferral with rationale per proportional rigor.

6. **For Check 6b/6b.2 (OOM gate + Phase 0 watcher):**
   - Read the deny log and marker file (pre-populated in Context Snapshot)
   - Compare against previous review's line count/state from COMPLIANCE-REVIEW.md tables
   - Apply the escalation thresholds defined in the check

7. **For Check 9 (Constitutional Analogy Register):**
   - Read `documents/rules-of-procedure.md` §9.7.7
   - Spot-check borrowed entries via grep
   - Re-evaluate not-borrowed trigger prerequisites
   - Append audit-log entry to §9.7.7

8. **Update Active Verification Items** (V-005 through V-008):
   - Check each V-series item's current state
   - Record any new data points in their tracking tables
   - Evaluate against confirm/refute thresholds

9. **Write results** to COMPLIANCE-REVIEW.md:
   - Add a row to each check's review history table
   - Add a row to the Review Log summary table
   - Include governance audit ID in the Review Log notes

10. **Report summary** to the user: checks passed/failed/deferred, any FAIL items with actions taken, V-series updates, next review target date.

### Governance

Cite principle IDs that influence your evaluation. Key principles for compliance review:
- `meta-quality-verification-validation` — the review itself is a verification gate
- `meta-governance-continuous-learning-adaptation` — periodic system health review
- `meta-core-systemic-thinking` — address root causes of any failures, not symptoms

### Important

- **Do NOT extract check definitions** from COMPLIANCE-REVIEW.md into this skill. COMPLIANCE-REVIEW.md is the single source of truth for check definitions and thresholds. This skill orchestrates execution; it does not duplicate content.
- **Record honest results.** If a check fails, document the failure and the fix. FAIL→FIXED is a healthy pattern.
- **Proportional rigor.** If the session is too young for a meaningful session audit (Check 5d), defer with rationale rather than rubber-stamping.
