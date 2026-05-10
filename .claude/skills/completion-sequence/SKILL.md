---
description: Run the post-change completion sequence — enforced and best-effort checks for code changes, content changes, domain changes, principle changes, principle rename, plan-mode decisions, documentation-only changes, and branch completion. Invoke after making changes and before pushing.
disable-model-invocation: true
allowed-tools: Bash Read Edit Agent
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Branch:** !`git branch --show-current 2>/dev/null`
**Staged changes:** !`git diff --cached --stat 2>/dev/null || echo "(nothing staged)"`
**Last commit:** !`git log -1 --oneline 2>/dev/null`
**Unpushed commits:** !`git log --oneline @{u}..HEAD 2>/dev/null || echo "(no upstream or no commits ahead)"`

```!
echo "=== Changed file types ==="
git diff --cached --name-only 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn || echo "(no staged changes)"
echo ""
echo "=== Files changed (unstaged + staged) ==="
git diff --name-only HEAD 2>/dev/null | head -20
```

## Instructions

You are running the post-change completion sequence. Read `checklist.md` in this skill folder for the full checklist.

### Execution Protocol

1. **Call `evaluate_governance(planned_action="completion sequence execution")`** before any writes.

2. **Read `checklist.md`** — it contains all enforced and best-effort checks organized by change type.

3. **Determine which sections apply** based on what changed this session:
   - Code changes (most common) → Code changes section
   - Governance document modifications → Content changes section
   - New/removed domains → Domain changes section
   - New/modified principles → Principle changes section
   - Principle ID renames → Principle rename section
   - Plan-mode architecture decisions → Plan-mode section
   - Memory/README-only changes → Documentation-only section

4. **Execute applicable checks** in order. For ENFORCED items, verify structural gates passed. For BEST-EFFORT items, apply with ~85% compliance expectation.

5. **Run Branch Completion** (always applies) — pick Option A/B/C/D/E based on work completeness and review needs.

### Key Distinctions

- **ENFORCED** items are backed by hooks, CI, or structural gates — non-compliance is physically blocked.
- **BEST-EFFORT** items are advisory with ~85% expected compliance.
- The meta-action of opening this checklist is ENFORCED by the pre-push quality gate hook.

### Governance

- `coding-quality-workflow-integrity` — the completion sequence maintains workflow consistency
- `meta-quality-verification-validation` — post-change verification gate
- `meta-core-systemic-thinking` — evaluate ripple effects across the system, not just the immediate change
