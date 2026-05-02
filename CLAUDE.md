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
  - **Anticipatory work is valid even without observed harm.** "Solving a phantom problem" is the wrong filter for proactive/preventive/improvement-class work — the test is whether the work matches *anticipated* stakes, not whether stakes have already manifested as harm. Per BACKLOG.md philosophy block: *"Anticipatory items are valid. Three valid reasons: need it now (active problem), plan to use soon (near-future need), anticipate needing later (want it ready when the time comes)."* Demanding "concrete instance of harm" before validating anticipatory work misapplies proportional-rigor and contradicts the framework's own stated rule. (Origin: BACKLOG #147 filed session-140 after pattern observed n=3 in one arc.)
- **Cite principles:** Are you referencing principle IDs when they influence your approach?
  - WRONG: "This is a root-cause analysis problem" with no principle reference
  - RIGHT: "Per `meta-core-systemic-thinking`, address the structural cause (autoregressive generation) not the symptom (skipped calls)"
- **Effort, not time:** Are you estimating future work in time units (minutes/hours/days/sessions) or observable effort indicators?
  - WRONG: "This will take 2-3 hours" or "this is a multi-session task"
  - RIGHT: "This is D2 effort: 4-6 file surfaces, requires plan mode" — uses observable indicators per `meta-method-effort-not-time-estimation` (rules-of-procedure §7.12)
  - **Scope:** rule applies to estimating future AI work. Does NOT apply to calendar/cadence dates (BACKLOG triggers), historical durations in audit logs, timeout values in code, or explicit user request for time framing.
- **BLUF for user-facing briefs:** Are you leading with the recommendation, or burying it in caveats?
  - WRONG: 5-page analysis where the recommendation appears in the middle of section 4
  - RIGHT: 2-3 sentence Bottom Line Up Front, then context, then 2-3 alternatives with embedded risk per `meta-method-bluf-pyramid-briefing` (rules-of-procedure §7.13)
  - **Scope:** rule applies to user-facing decision briefs and recommendations. Does NOT apply to internal technical artifacts (plan files, ADRs, spec documents, audit logs).

Detail for each: `coding-process-human-ai-collaboration-model` (Decision Authority Matrix), Progressive Inquiry Protocol (§7.9), Effort-Not-Time Estimation (§7.12), BLUF-Pyramid Briefing (§7.13).

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content
- `contrarian-reviewer` via Task subagent — required before `ExitPlanMode` (per pre-exit-plan-mode-gate hook, session-122). Invoke unprompted during plan-writing to pressure-test the approach BEFORE approval. Bypasses: `PLAN_CONTRARIAN_CONFIRMED=1` (semantic) + `PLAN_CONTRARIAN_SKIP_HOOK=1` (structural, audit-logged).

**Skip list (narrow):** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE". Note: analysis tasks that determine what to change (propagation checks, audit reviews) are NOT read-only — they lead to writes. Call governance before analysis, not just before the write.

**Eat your own dogfood:** Use governance tools AND subagents for your own analysis work — propagation checks, compliance audits, documentation reviews. The coherence-auditor catches cross-file drift that manual grep misses. The validator catches structural defects. Don't reserve subagents only for user-requested reviews.

After evaluating: cite principle IDs that influence your approach.

**CE vs Grep:** Use `query_project` for semantic discovery (what exists? what's related? how does X work?). Use Grep/Glob for deterministic lookup (find this exact string, check this file, count occurrences). When creating new content or investigating unfamiliar areas, CE first.

**Known hook workaround — OOM-gate FP on `pytest` in commit messages:** When a `git commit` message body contains `pytest` inside a quoted region (heredoc body or alternation argument), the OOM gate (`pre-test-oom-gate.sh`) false-positives because its token-anchored matcher cannot distinguish executable position from quoted-region content. Write the message to a tempfile via the Write tool and commit via `git commit -F <messagefile>`. Tracked as BACKLOG #143 (deferred — asymmetric cost: hook modification risks TP-regression vs. low workaround friction).

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
| **Defer (with tracking)** | Add to BACKLOG.md discussion section with enough detail to reconstruct. | New capability, domain addition, architectural change |
| **Ask the user** | Present what you found; let the user decide. | Anticipatory work, fixes touching >3 files, ambiguous scope |

**Why this rule exists:** Forward-continuation bias makes "fix it later" the AI's path of least resistance. Session discontinuity means "later" often means "never." But unbounded "fix everything now" causes scope creep. This rule balances both failure modes: fix what's cheap and known, track what's not, never surprise the user with unsolicited large changes.

## Session Lifecycle

**At session start:** Read all three memory files: SESSION-STATE.md (current position), PROJECT-MEMORY.md (constraints and decisions), LEARNING-LOG.md (mistakes to avoid). Then prune SESSION-STATE.md if >300 lines: remove old session summaries (keep only most recent), clear stale context, route decisions to PROJECT-MEMORY.md, lessons to LEARNING-LOG.md. Target: <300 lines per §7.0.4.

**At session end:** Update SESSION-STATE.md with current position and session summary. If >300 lines, apply §7.0.4 distillation before committing.

**Backlog items:** Discussion and deferred items live in BACKLOG.md, not SESSION-STATE.md.

## Plan Mode

For architecture decisions, use the plan template at `.claude/plan-template.md`. The template structure puts contrarian review, research verification, and simpler-alternatives evaluation BEFORE the recommended approach — making verification part of the generation flow, not an afterthought. (Per Systemic Thinking + autoregressive forward-continuation bias research.)

**Action atomicity** (template Section: Recommended Approach): each task entry must name a single action category from `{write failing test, run test, implement minimal code, refactor, verify}` and include `**Files:**` + `**Verification:**` lines. Combined tasks ("implement and test") must split. Vague verbs ("update", "improve", "handle") are not action categories. Advisory until the WARN-mode hook gate ships; structural enforcement deferred per V-004 advisory→structural arc.

## Quick Recall — Behavioral Floor (see top of file)

Root cause over symptoms. Recommend, don't ask. Freeform dialogue. Proportional rigor. Cite principle IDs. Effort-not-time. BLUF for user-facing briefs.
