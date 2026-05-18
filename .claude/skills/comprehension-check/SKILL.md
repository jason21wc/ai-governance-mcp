---
description: Run an on-demand comprehension check on recent AI-generated work — reviews uncommitted changes, last commit, or a user-specified scope, generates three-layer comprehension scaffolds (intent/boundaries/handoff) per rules-of-procedure §16.8, and collects human response. Invoke when you want to verify understanding of accumulated work before pushing, at session checkpoints, or when you realize you have been proceeding without full comprehension. Do NOT use for compliance reviews (/compliance-review) or content enhancement (/content-enhancer).
disable-model-invocation: true
allowed-tools: Bash Read Agent
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Branch:** !`git branch --show-current 2>/dev/null`
**Uncommitted changes:** !`git diff --stat HEAD 2>/dev/null | tail -1`
**Last commit:** !`git log --oneline -1 2>/dev/null`

```!
echo "=== Files changed since last push ==="
git diff --stat @{push}..HEAD 2>/dev/null || echo "(no upstream or no unpushed commits)"
echo ""
echo "=== Session work (last 5 commits) ==="
git log --oneline -5 2>/dev/null
```

## Instructions

You are running an on-demand comprehension check. Read `procedure.md` in this skill folder for the full protocol.

### Execution Protocol

1. **Call `evaluate_governance(planned_action="comprehension check")`** before any writes.

2. **Determine scope.** If the user specified what to check (a file, commit, or topic), use that. Otherwise, read the Context Snapshot above and recommend a scope — typically uncommitted changes or the last commit. Ask only if the scope is genuinely ambiguous.

3. **Read `procedure.md`** — it contains the scope analysis, scaffold generation, and response handling protocol.

4. **Execute the procedure:**
   - Step 1: **Scope** — identify what work to check, read the relevant files/diffs
   - Step 2: **Analyze** — understand the changes at the architectural level, not just the diff
   - Step 3: **Scaffold** — generate three-layer scaffolds per §16.8 format, one per logical unit of work
   - Step 4: **Present** — show scaffolds to the user, grouped by logical unit
   - Step 5: **Respond** — handle user response per the Human Response Taxonomy

5. **If the user says "Explain"** for any scaffold, produce a detailed walkthrough using the domain-appropriate technique (e.g., Linear Walkthrough for code per §5.13.7, narrative walkthrough for content).

### Key Principles

- **Comprehension tool, not approval gate.** The user can respond Understood, Acknowledged, Explain, or Continue. All responses are valid. Never block.
- **Scaffold Theater is the #1 risk.** Generic scaffolds that could apply to any output are worse than none. Every scaffold must name actual files, decisions, and constraints from this work.
- **Consolidate, don't enumerate.** If 10 files changed for one logical purpose, that is one scaffold — not 10. Group by intent.
- **Domain awareness.** Use domain-specific scaffold techniques when applicable (UI/UX §10, RAG §6.5, KM&PD §8.2, ai-coding §5.13.7). Fall back to universal §16.8 format.

### Governance Citations

- `meta-quality-effective-efficient-outputs` — parent principle; comprehension scaffold obligation
- `meta-governance-human-ai-authority-accountability` — comprehension enables human authority
- `meta-core-systemic-thinking` — scaffold targets structural cause (generation-comprehension gap), not symptom
