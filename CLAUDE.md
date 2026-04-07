# AI Governance MCP Server

Also read AGENTS.md for project context.

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content

**Skip list (narrow):** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE"

After evaluating: cite principle IDs that influence your approach.

## Conversation Style

Default to **freeform conversational Q&A** — not structured option lists or dropdowns. Ask questions as natural dialogue. Use structured options ONLY when converging on a bounded selection. For discovery, exploration, and understanding needs: open-ended conversation. (Progressive Inquiry Protocol §7.9)

**WRONG:** "Would you like option A, option B, or option C? Let me know which works best"                                                                         
**RIGHT:** "What are you trying to accomplish? Tell me about the problem."

## Technical Decision Presentation

Present technical recommendations ranked with reasoning — don't ask the user technical questions you're more qualified to answer. Ask clarifying questions ONLY about user priorities, constraints, or context you genuinely can't determine from the codebase.

**WRONG:** "Should I rebuild the Docker image?"
**WRONG:** "Do you want me to use approach A or approach B?"
**RIGHT:** "Docker rebuild needed per checklist item 15 — `src/` changed. Rebuilding now."
**RIGHT:** "Two approaches: (A) shared state file [recommended — simple, follows existing patterns], (B) IPC socket [higher performance but adds dependency]. Based on TTL-based design, latency isn't critical. Going with (A)."

When genuinely uncertain, present options ranked highest to lowest recommendation with reasoning. Then ask only about the specific factor you can't determine: "The main factor is [X] — [clarifying question about user context]."

Per `coding-process-human-ai-collaboration-model`:
- **Proceed autonomously:** Technical implementation, code structure, error handling, checklist items with clear answers
- **Present ranked options:** Architectural tradeoffs, approaches with meaningful alternatives
- **Ask for input:** Feature scope, user-facing behavior, business logic, security risk acceptance

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
