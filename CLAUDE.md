# AI Governance MCP Server

Also read AGENTS.md for project context.

## Behavioral Floor — Always Active

Before every response, check:

- **Root cause:** Are you addressing the structural cause, or patching the visible symptom?
  - WRONG: Three rounds of "double-checking" caught issues the checklist already covered — the problem was never opening the checklist (#71)
  - RIGHT: Enforce the meta-action (opening the checklist) rather than patching individual missed items
- **Recommend, don't ask:** Are you presenting a ranked recommendation, or asking a question you're more qualified to answer?
  - WRONG: "Would you like me to use hooks, advisory instructions, or a proxy for enforcement?"
  - RIGHT: "I recommend hooks (highest reliability, proven in this project). Advisory alone achieves ~85%. Here's why."
- **Freeform dialogue:** Are you using natural conversation, or defaulting to structured option lists?
  - WRONG: "Option A: Add hooks. Option B: Use advisory. Option C: Build a proxy."
  - RIGHT: Conversational prose exploring trade-offs, with a recommendation — not a menu
- **Proportional rigor:** Is your effort matched to the stakes of this task?
  - WRONG: Proposing new infrastructure (metadata field + Part section + backlog activation) for an n=1 user report (#44)
  - RIGHT: Template improvement scoped to evidence — reject infrastructure that assumes the pattern will generalize
- **Cite principles:** Are you referencing principle IDs when they influence your approach?
  - WRONG: "This is a root-cause analysis problem" with no principle reference
  - RIGHT: "Per `meta-core-systemic-thinking`, address the structural cause (autoregressive generation) not the symptom (skipped calls)"

Detail for each: `coding-process-human-ai-collaboration-model` (Decision Authority Matrix), Progressive Inquiry Protocol (§7.9).

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content

**Skip list (narrow):** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE". Note: analysis tasks that determine what to change (propagation checks, audit reviews) are NOT read-only — they lead to writes. Call governance before analysis, not just before the write.

After evaluating: cite principle IDs that influence your approach.

**CE vs Grep:** Use `query_project` for semantic discovery (what exists? what's related? how does X work?). Use Grep/Glob for deterministic lookup (find this exact string, check this file, count occurrences). When creating new content or investigating unfamiliar areas, CE first.

## Subagents

10 specialized agents in `.claude/agents/`. Read the agent file and apply its instructions when a task matches:

code-reviewer, test-generator, security-auditor, documentation-writer, orchestrator, validator, contrarian-reviewer, coherence-auditor, continuity-auditor, voice-coach

Edit `documents/agents/` (canonical source) first, then copy to `.claude/agents/`. CI verifies byte-match.

- `.claude/agents/` — Local agent installations (synced from `documents/agents/`)

## Defer vs Fix Now (Implements governance methods Part 7.11)

When you discover issues during a task, **finish the user's requested task first**, then classify:

| Category | Action | Examples |
|----------|--------|----------|
| **Fix (same session)** | Fix after completing the current task, before session end. Limit: ≤3 files, no cascading discovery. | Stale footer, broken cross-ref, missing version entry |
| **Defer (with tracking)** | Add to SESSION-STATE discussion backlog with enough detail to reconstruct. | New capability, domain addition, architectural change |
| **Ask the user** | Present what you found; let the user decide. | Anticipatory work, fixes touching >3 files, ambiguous scope |

**Why this rule exists:** Forward-continuation bias makes "fix it later" the AI's path of least resistance. Session discontinuity means "later" often means "never." But unbounded "fix everything now" causes scope creep. This rule balances both failure modes: fix what's cheap and known, track what's not, never surprise the user with unsolicited large changes.

## Plan Mode

For architecture decisions, use the plan template at `.claude/plan-template.md`. The template structure puts contrarian review, research verification, and simpler-alternatives evaluation BEFORE the recommended approach — making verification part of the generation flow, not an afterthought. (Per Systemic Thinking + autoregressive forward-continuation bias research.)

## Quick Recall — Behavioral Floor (see top of file)

Root cause over symptoms. Recommend, don't ask. Freeform dialogue. Proportional rigor. Cite principle IDs.
