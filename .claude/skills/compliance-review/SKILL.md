---
description: Run the governance compliance review workflow — 14 checks covering hook integrity, enforcement mode, effectiveness tracking, behavioral canary prompts, MCP health, OOM gate activity, permission coverage, backlog staleness, constitutional register integrity, CI storage budget, and feedback loop health. Cadence is every 10-15 days or immediately after hook/behavioral-floor modifications.
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

You are running a governance compliance review. This skill folder contains all procedure and data files:

- **`procedure.md`** — check definitions 1-11, pass/fail criteria, review history tables (read this first)
- **`audit-log.md`** — Review Log summary table, Security Currency Reviews, Governance Performance Metrics
- **`verification.md`** — active and retired V-series verification items

### Execution Protocol

1. **Call `evaluate_governance(planned_action="compliance review execution")`** before any writes.

2. **Read `procedure.md`** — it contains the check definitions, pass/fail thresholds, and review history tables you will update.

3. **Determine the next review number** from the Review Log table in `audit-log.md`.

4. **Execute each Ongoing Check (1 through 11)** in order. For each check:
   - Read the check definition and pass/fail criteria from `procedure.md`
   - Run the required commands (many are pre-populated in the Context Snapshot above)
   - Evaluate the result against the criteria
   - Record PASS, FAIL, or N/A with concise notes

5. **For Check 5 (Behavioral canary prompts + session audit):**
   - Decide whether canary prompts (a-c) should run this review or be deferred per the execution-only session precedent (Reviews #3-6)
   - For session audit (d): spawn a **validator subagent** with the Check 5d evaluation rubric from `procedure.md`. The subagent needs fresh context per `multi-quality-validation-independence`.
   - If insufficient session scope exists for meaningful audit (e.g., session-start review), document the deferral with rationale per proportional rigor.

6. **For Check 6b/6b.2 (OOM gate + Phase 0 watcher):**
   - Read the deny log and marker file (pre-populated in Context Snapshot)
   - Compare against previous review's line count/state from `procedure.md` tables
   - Apply the escalation thresholds defined in the check

7. **For Check 9 (Constitutional Analogy Register):**
   - Read `documents/rules-of-procedure.md` §9.7.7
   - Spot-check borrowed entries via grep
   - Re-evaluate not-borrowed trigger prerequisites
   - Append audit-log entry to §9.7.7

8. **Update Active Verification Items** (V-006 through V-009):
   - Read `verification.md` for current state
   - Record any new data points in their tracking tables
   - Evaluate against confirm/refute thresholds

9. **Check feedback loop analysis staleness** (C-155):
   - Read the precomputed analysis via `analyze_feedback_loop` MCP tool (or check `logs/feedback_loop_analysis.json` directly)
   - If the file is missing or >30 days old, re-run: `python scripts/analyze_feedback_loop.py --print-summary`
   - Review `analyze_feedback_loop(section="actionable_recommendations")` for any items needing attention
   - Note key metrics (M-001, M-003, M-004) in the review

10. **Write results:**
   - Add a row to each check's review history table in `procedure.md`
   - Add a row to the Review Log summary table in `audit-log.md`
   - Update V-series items in `verification.md`
   - Include governance audit ID in the Review Log notes

11. **Report summary** to the user: checks passed/failed/deferred, any FAIL items with actions taken, V-series updates, next review target date.

### Governance

Cite principle IDs that influence your evaluation. Key principles for compliance review:
- `meta-quality-verification-validation` — the review itself is a verification gate
- `meta-governance-continuous-learning-adaptation` — periodic system health review
- `meta-core-systemic-thinking` — address root causes of any failures, not symptoms

### Important

- **Procedure content lives in reference files**, not this SKILL.md. `procedure.md` is the source of truth for check definitions and thresholds. This skill orchestrates execution.
- **Record honest results.** If a check fails, document the failure and the fix. FAIL→FIXED is a healthy pattern.
- **Proportional rigor.** If the session is too young for a meaningful session audit (Check 5d), defer with rationale rather than rubber-stamping.
