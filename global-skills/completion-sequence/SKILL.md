---
description: Run the post-change completion sequence — checks for code changes, documentation-only changes, and branch completion. Invoke after making changes and before pushing. Invoke when the user says "completion sequence", "completion checklist", "run the checklist", "pre-push checks", "ready to push", or "wrap up".
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

1. **Read `checklist.md`** — it contains all checks organized by change type.

2. **Determine which sections apply** based on what changed this session:
   - Code changes (most common) → Code changes section
   - Documentation/README-only changes → Documentation-only section

3. **Execute applicable checks** in order.

4. **Run Branch Completion** (always applies) — pick Option A/B/C/D/E based on work completeness and review needs.

### Key Principles

- **The checklist is a safety net, not a ceremony.** Skip items that genuinely don't apply. Don't check boxes for the sake of checking boxes.
- **Branch Completion is the real deliverable.** The decision tree at the end ensures every session ends with a clear handoff — committed and pushed, PR opened, checkpoint saved, or cleanly discarded.
- **Scale to the change.** A one-line typo fix doesn't need the full battery. A multi-file refactor does.
