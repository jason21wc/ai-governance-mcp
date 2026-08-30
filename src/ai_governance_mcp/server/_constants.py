"""Static constants for the AI Governance MCP server.

Templates, metadata, safety keywords, and configuration constants.
Extracted from __init__.py to reduce monolith size (~1100 lines).
"""

import re

# Safety topic-keyword sets + demotion gates moved to the dep-light top-level
# `safety_scan` module (so the enforcement proxy can import them torch-free).
# Re-exported here for back-compat with existing importers.
from ..safety_scan import (
    ADVISORY_SAFETY_KEYWORDS as ADVISORY_SAFETY_KEYWORDS,
    CRITICAL_SAFETY_KEYWORDS as CRITICAL_SAFETY_KEYWORDS,
    _EGRESS_VERBS as _EGRESS_VERBS,
    _IMPERATIVE_ACTION_VERBS as _IMPERATIVE_ACTION_VERBS,
    _SAFE_CONTEXT_LEADERS as _SAFE_CONTEXT_LEADERS,
    _SENTENCE_BOUNDARY as _SENTENCE_BOUNDARY,
)

MAX_QUERY_LENGTH = 10000
MAX_LOG_CONTENT_LENGTH = 2000
MAX_RELEVANT_METHODS = 5

# evaluate_governance principle-body budget (chars). Bounds the response so it
# never exceeds the MCP per-tool-result token cap when many principles match
# (the 112 KB hard-error class — Cowork report + 3 reproductions). Triggered
# S-Series bodies are allocated first (safety must stay visible on ESCALATE),
# then highest score, until this budget is consumed; the rest go reference-only
# (content=None — fetch via get_principle). ~40K chars ≈ ~10K tokens, leaving
# ample headroom under the working ~25K-token cap estimate for the verdict header,
# floors, and methods. A single body exceeding the whole budget is
# paragraph-truncated. (That cap figure is an estimate — the outage it comes from is
# observed, the number is not pinned anywhere in this repo. See _content_budget.py.)
#
# Corpus figures live in `server/_content_budget.py`'s module docstring — one source,
# not a copy here. A copy at this spot had already drifted to a stale date.
# The previous note here claimed "largest observed ≈ 29K chars" — that was
# false when written and got worse: units absorbed every section following them,
# so `meta-safety-transparent-limitations` carried constitution.md's whole
# changelog at 74,441 chars, exceeding this entire budget. It therefore either
# consumed 99.5% of the budget (starving every other principle) or, once earlier
# allocations had spent any of it, fell to content=None. Fixed at the source in
# extractor.py rather than by raising this number.
PRINCIPLE_CONTENT_BUDGET_CHARS = 40000

# No SINGLE body may consume the whole budget, in either governance tool. Without
# this, one oversized unit is truncated to `budget - 200` and then eats ~99.5% of
# the allocation, starving every other unit of content — measured before the
# extractor boundary fix (5802cf8), when `meta-safety-transparent-limitations`
# carried 74,441 chars and either did exactly that or fell to content=None
# depending on allocation order.
#
# Sized 24000 to sit above the largest unit of EITHER kind in the corpus (figures in
# `server/_content_budget.py`), so it is a true corpus ceiling rather than a
# principles-only one. 16000 would cover every principle but falls below the largest
# method, so one constant could not serve both.
#
# Two honest caveats a reader needs before trusting this number at a call site:
#   1. No code path allocates METHOD bodies today — `evaluate_governance` passes
#      principles only, and `query_governance` renders methods title-only. The method
#      half of the sizing above is forward-looking, not currently binding.
#   2. This is a CEILING, not automatically a per-unit protection. A caller whose
#      budget is BELOW this value gets no starvation protection from passing it — see
#      the `per_unit_max` discussion in `_content_budget.py`, which spells out why
#      `query_governance` is exactly that case.
PER_UNIT_CONTENT_MAX_CHARS = 24000

# query_governance body budget. DELIBERATELY LOWER than the evaluate_governance
# budget above, and the divergence is the point: the two tools have different jobs.
# `evaluate_governance` fires once per mutation and its principle bodies ARE the
# judgment input (§4.6.1 Assessment Responsibility Layers makes delivering them its
# job). `query_governance` is a discovery tool the model calls freely, several times a
# session, and the caller normally acts on the top one to three matches.
#
# A budget is required at the DEFAULT max_results of 10, not merely at the 50 ceiling:
# the 10 largest principles together sit at the working cap. Corpus figures are NOT
# restated here on purpose — `server/_content_budget.py`'s module docstring is their
# single source, and a review already caught a duplicated copy of them drifting to a
# different date (meta-core-single-source-of-truth).
#
# 20000 measured against the RENDERED markdown — not just `content`, because per-item
# headers, score lines, match reasons and the omission footer are themselves part of
# the payload a budget exists to bound. n=10 representative queries, 2026-08-11:
#
#   budget | median rendered | max rendered | ~max tok | bodies complete
#    8,000 |          10,120 |       11,187 |    2,796 |  12/35
#   12,000 |          13,040 |       14,886 |    3,721 |  17/35
#   20,000 |          21,770 |       22,782 |    5,695 |  27/35   <-- chosen
#   40,000 |          25,080 |       40,131 |   10,032 |  35/35
#
# Why not 40000 (the value first committed here): it is justified only against the
# protocol cap, and the measurement shows that cap is not the binding constraint —
# nothing gets close to it. What it buys is 8 tail bodies for nearly double the token
# ceiling, and ADR-29 thinned CLAUDE.md 151->28 lines to cut exactly that cost on the
# instruction path. Re-inflating it on the retrieval path gives the tokens back.
#
# Why not 12000 (the value the plan targeted): too tight against measured reality. It
# withholds half the bodies, and because real queries return 3-6 principles rather than
# 10, the units it drops are second and third matches the caller often does need.
#
# READ THE TABLE'S SCOPE, IT IS NOT A CEILING. Those figures are the DEFAULT
# max_results=10 case, and `used` counts body chars only. Headers, score lines, match
# reasons, the withheld notes and the references section are all outside this budget and
# scale with max_results, which clamps to 50 PER LIST. A static worst case over the live
# index — reachable only when the reranker is unavailable and the candidate set is not
# capped to rerank_top_k=20 — measured **~87,500 chars (~21.9k tok)**, of which at most
# 20,000 is body. That is a pre-existing exposure this budget IMPROVES (the same path
# under the old 600-char preview reached ~97,500), not one it creates.
#
# ⚠️ THAT 87,500 IS A PRE-CAP MEASUREMENT and is now an overstatement: two of its five
# named contributors have since been capped — the query echo (10,000 -> 300) and the
# reference summaries inside the ~22,570-char references section (-> 300 each). Roughly
# 30,000 chars of it no longer exists. It has NOT been re-measured, so it is left as the
# pre-cap number rather than replaced by a guess. Re-measure before using it to size
# anything; BACKLOG #333 tracks that, and its open question about the protocol cap is
# currently sized on this superseded figure.
#
# WHAT THIS BUDGET DOES AND DOES NOT PROMISE. It delivers 77% of bodies complete at the
# default, and the top match complete in the ordinary case — but allocation is
# priority-then-score, NOT score-ordered, so the guarantee is conditional and the
# earlier version of this comment overstated it. See `_allocate_result_content` for the
# priority rule and its measured bound.
QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS = 20000

# Render-time caps on the two `query_governance` components that sat OUTSIDE the body
# budget and scaled independently of it (BACKLOG #333, from the security audit).
#
# Neither is a body, so neither belongs in QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS — but
# "not a body" was doing the work of "not worth bounding", which is how the query echo
# came to accept 10,000 caller-supplied chars and the references section came to be the
# single largest unbudgeted contributor (~22,570 chars at the measured worst case).
#
# 300 each: enough for the echo to confirm what was searched and for a summary to say
# what an entry is, which is all either one is for. A clip is always MARKED — see
# `_clip` — because an unmarked clip is exactly the defect #325 removed.
QUERY_ECHO_MAX_CHARS = 300
REFERENCE_SUMMARY_MAX_CHARS = 300

RATE_LIMIT_TOKENS = 100
RATE_LIMIT_REFILL_RATE = 10

SECRET_PATTERNS = [
    (
        re.compile(
            r'(?i)(api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?'
        ),
        r"\1=***REDACTED***",
    ),
    (
        re.compile(r'(?i)(password|passwd|pwd)["\s:=]+["\']?([^\s"\']{8,})["\']?'),
        r"\1=***REDACTED***",
    ),
    (
        re.compile(r'(?i)(secret|token)["\s:=]+["\']?([a-zA-Z0-9_\-]{16,})["\']?'),
        r"\1=***REDACTED***",
    ),
    (re.compile(r"(?i)(bearer)\s+([a-zA-Z0-9_\-\.]{20,})"), r"\1 ***REDACTED***"),
    (
        re.compile(r'(?i)(authorization)["\s:=]+["\']?([^\s"\']{20,})["\']?'),
        r"\1=***REDACTED***",
    ),
    (
        re.compile(r'(?i)(private[_-]?key)["\s:=]+["\']?([^\s"\']{20,})["\']?'),
        r"\1=***REDACTED***",
    ),
    (re.compile(r"(?i)(AKIA[A-Z0-9]{16})"), r"***AWS_KEY_REDACTED***"),
    (
        re.compile(r"(?<![a-zA-Z0-9])([a-zA-Z0-9]{32,})(?![a-zA-Z0-9])"),
        r"***POSSIBLE_SECRET_REDACTED***",
    ),
]

AUDIT_LOG_MAX_SIZE = 1000

SERVER_INSTRUCTIONS = """
## AI Governance MCP Server

Semantic retrieval of AI governance principles and methods. Query before acting.

### Orchestrator Protocol (Default Behavior)

Call `evaluate_governance(planned_action="your task")` before any action UNLESS it is:
- Reading files, searching, or exploring code
- Answering questions that do not involve security-sensitive information
- Trivial formatting (whitespace or comment text changes that do not alter behavior)
- Human user explicitly says "skip governance" with documented reason

When in doubt, evaluate.

**Act on assessment (this is a routing decision, not a checkbox):**
- PROCEED: Continue with the task
- REVIEW: Relevant principles found — read them, adjust if conflicts exist, then continue
- ESCALATE: STOP. Inform user. Wait for explicit approval.
- **S-Series principle = Absolute Veto**: when a real S-Series (safety) *principle* triggers, you MUST escalate regardless of other factors. A bare safety-*keyword* match (rationale says "Safety keyword match … no S-Series principle retrieved", `principles: []`) escalates for visibility only — a heuristic advisory to down-weight when the action is benign or user-authorized (M-004 keyword false-positive class), NOT a principle veto — **unless adjudicated `genuine`/`floor` (next bullet), which are high-signal**.
- **Keyword-only adjudication (BACKLOG #73)**: a keyword-only trigger is adjudicated server-side (`s_series_check.keyword_adjudication`) — the Layer-0 insecure-persistence net is deterministic (no Codex needed); the Layer-1 fresh-context judge needs the Codex CLI, and without it the verdict is `unavailable`. Verdicts: `floor` (deterministic insecure-persistence match) and `genuine` (judge flagged a real concern) → ESCALATE, **high-signal, do not down-weight**; `benign` (topic mention) → REVIEW; `unavailable` (judge unreachable → failed-safe ESCALATE) → the SAME heuristic keyword class as the bare-keyword bullet, NOT a stronger signal, do not up-weight it.

The assessment output determines your next action — it is not an acknowledgment before doing what you planned anyway.

### Critical Reasoning Disciplines

Five reasoning disciplines to demonstrate (not just acknowledge) in every evaluation:

1. **Find the structural cause** — What system, process, or design produced this? Name the structural cause, not the visible symptom. Your fix should target that.
2. **Verify before acting** — What assumption are you making right now? How have you confirmed it — from the actual source, not a review note or agent convergence?
3. **State what you don't know** — Where is your uncertainty? Name it explicitly before proceeding. "I don't know" is a successful output.
4. **Make the call** — Present your best recommendation with rationale. Don't ask what you should decide. Don't defer what you can resolve now.
5. **Match effort to stakes** — Is this a 3-file fix or a new subsystem? Act on what it actually is, not what it might theoretically become.

### Required Actions
1. **Evaluate before acting** — `evaluate_governance(planned_action="...")` for any action not on the skip list
2. **Query for guidance** — `query_governance("your concern")` when you need principles to inform decisions
3. **Cite influencing principles** — Reference principle IDs when they guide your approach
4. **Pause on uncertainty** — If requirements are unclear, ask the user before proceeding
5. **Query project context** — Before implementing, call `query_project("...")` via the Context Engine MCP to discover existing patterns
6. **Search for precedent** — Before implementing code, call `search_references(query="what you're about to build")` to surface proven patterns from the Reference Library. This is separate from governance (principles) and query_project (existing code) — it surfaces implementation know-how from prior work
7. **Capture reusable precedent** — After you solve a non-obvious, reusable problem (a debugged integration, a library-selection call, a gotcha + its fix, an architecture decision) whose lesson would help future work in THIS or ANOTHER project, call `capture_reference(...)` to add it to the Reference Library. Captures land in the **central** library regardless of which project you are working in — this is how cross-project know-how accumulates. Quality bar: capture the *non-obvious and reusable*, not routine steps or project-specific trivia (one entry per durable lesson). Curation governance (intake paths, §15.4) and the maturity/decay cycle keep the library healthy

### Conversation Style
Default to **freeform conversational Q&A**, not structured option lists. When gathering requirements, exploring ideas, or discussing approaches, ask questions as natural conversation — not dropdowns or multiple choice. Structured options are appropriate ONLY when converging on a bounded selection (e.g., "which of these 3 specific configs?"). For discovery, exploration, and understanding the user's needs, use open-ended dialogue.

**WRONG** (do not do this during discovery): "Here are your options: A, B, or C. Which would you prefer?"
**RIGHT** (do this instead): "What does your app need to communicate with? Tell me about the data flow you're envisioning."

See Progressive Inquiry Protocol (§7.9).

### Plain Language & Audience Calibration
Calibrate vocabulary to THIS reader's actual knowledge — default to accessible (a non-specialist reading cold) unless they have signaled expertise. A technical term is the right word when the reader knows it; use plain words otherwise, and define a term inline only when the reader can't proceed without it — never a standalone sentence that pre-explains jargon. Posture, not a banned-word list: the failure is assuming shared vocabulary without checking. For a decision-bearing reply, lead with what's happening / what it implies / what the reader must decide.

**WRONG** (unexplained jargon, no audience check): "The act-intrinsic gate degrades to advisory on a non-hooked locus."
**RIGHT** (plain words; define a term only if it is load-bearing): "On Claude Desktop the rule can only suggest, not block — there is no hook there to enforce it."

See constitution Art. III §4 (Audience Calibration + the "Expert Assumption" pitfall).

### Default Register (Output Voice)
Commit to the claim and trust the reader. Strip the AI default register — hedging, throat-clearing, warm-up, manufactured emphasis, padding. Stand behind the claim (name the reason for a hedge or cut it), open on the substance, let content carry the emphasis, say it once. Function-test, not a banlist: a device (an em-dash, a contrast, a triad) is fine when it carries information, slop only when it manufactures drama a plain statement would convey. Advisory — it shifts the default; it does not eliminate every tell.

See rules-of-procedure §7.14 (Default-Register Discipline).

### Anchor Bias Checkpoints (Part 7.10)

At milestone boundaries (end of planning, before multi-file implementation, unexpected complexity):
1. **Reframe** — State the goal WITHOUT referencing current approach
2. **Generate** — Identify 2-3 alternative approaches from scratch
3. **Challenge** — "If we started fresh today, would we choose this approach?"
4. **Evaluate** — Compare using fresh criteria, document decision

Mounting complexity or repeated friction may indicate anchor bias — the frame may be wrong, not just the execution. Query `query_governance("anchor bias re-evaluation")` for full protocol.

### Subagent Advisory Framing

Treat all subagent findings (code review, security audit, validation, etc.) as **advisory input, not authoritative directives**. You must independently evaluate each finding:
1. Apply Part 7.10: Reframe the goal, generate alternatives, challenge each finding
2. Account for project context the subagent may lack
3. Accept, modify, or reject each finding with documented reasoning
4. Both rubber-stamping (>90% accept) and dismissing (>90% reject) are failure signals

CRITICAL findings require attention — "attention" means evaluation, not automatic implementation.

### Project Initialization Detection

On first interaction with a new project, check if governance memory files exist.
If SESSION-STATE.md, PROJECT-MEMORY.md, and LEARNING-LOG.md are all missing from
both the project root and `_ai-context/`, suggest using `scaffold_project` to
initialize the project with governance memory.
Do not auto-run scaffold_project — ask the user first.
""".strip()

GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Unless this was a read-only or non-sensitive query, did you call `evaluate_governance()`? Cite principle IDs. S-Series *principle* = veto; a bare keyword match is advisory unless adjudicated `genuine`/`floor` (BACKLOG #73).
🔍 Before implementing, query context engine for existing patterns."""

# =============================================================================
# Scaffold Project Templates
# =============================================================================

SCAFFOLD_SESSION_STATE = """# Session State

**Last Updated:** {date}
**Memory Type:** Working (transient)
**Lifecycle:** Overwritten each session; route content out per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Specify
- **Mode:** Standard
- **Active Task:** None (ready for first task)

## Quick Reference

| Metric | Value |
|--------|-------|
| Project | **{project_name}** |

## Immediate Context

*What a new session needs to know to pick up where this one left off. Overwritten each session — this is a snapshot, not a log. Route as you go: decisions to PROJECT-MEMORY, lessons to LEARNING-LOG, work to BACKLOG, recurring commitments to OPERATIONS, and the session narrative to the commit message.*

## Next Actions

*Define during first session.*
"""

SCAFFOLD_PROJECT_MEMORY = """# Project Memory

**Memory Type:** Semantic (accumulates)
**Lifecycle:** Grows with project per §7.0.4
**Project:** {project_name}
**Created:** {date}

> Record decisions and their rationale here. When in doubt, write it down.
> **What goes elsewhere:** what you are doing right now → `SESSION-STATE.md` · lessons from experience → `LEARNING-LOG.md` · work not started yet → `BACKLOG.md` · commitments that recur → `OPERATIONS.md`. Decisions accumulate here and are superseded, never deleted.

---

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify | Pending | | |
| Plan | Pending | | |
| Implement | Pending | | |
| Validate | Pending | | |

## Spec Summary

*Fill in after Specify phase.*

## Key Decisions

| Decision | Date | Rationale |
|----------|------|-----------|
| | | |

## Tech Stack

*Fill in after Plan phase.*

## Constraints

*Document any constraints discovered during work.*

## Known Gotchas

| # | Gotcha | Date |
|---|--------|------|
| | | |
"""

SCAFFOLD_LEARNING_LOG = """# Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

*No lessons yet. Add entries as you learn from mistakes and discoveries.*

---

## Graduated Patterns

| Pattern | Graduated To | Date |
|---------|-------------|------|
| | | |
"""

# AGENTS.md is the shared BODY every tool's loader points at (Codex/Cursor read it
# natively; CLAUDE.md/GEMINI.md import it). SAFETY BOUNDARY (title-10 Appendix A/K.3):
# only platform-neutral memory + session-start + governance *guidance* lives here.
# Governance/hook ENFORCEMENT and S-Series stop-rules stay in the CLAUDE.md overlay,
# never in this imported body. Keep it lean (Codex project_doc_max_bytes ~32 KiB).
SCAFFOLD_AGENTS_MD = """# {project_name}

**Description:** [Brief project description]
**Framework:** AI Coding Methods (current version)
**Mode:** Standard

## Memory Files

Project memory lives in `_ai-context/` and is committed to git (shared memory,
not scratch — nothing auto-discovers these files; this loader is the pointer):
- `_ai-context/SESSION-STATE.md` — current position, quick reference, next actions
- `_ai-context/PROJECT-MEMORY.md` — decisions, constraints, gotchas
- `_ai-context/LEARNING-LOG.md` — active lessons
- `_ai-context/BACKLOG.md` — deferred work that finishes (standard kit and above)
- `_ai-context/OPERATIONS.md` — recurring commitments that never finish: cadences, tripwires, standing authorizations, metrics (standard kit and above)

The host tool's own built-in memory is separate — leave it to the host.

## Session Start

1. Read `_ai-context/SESSION-STATE.md` — current position, next actions
2. Read `_ai-context/PROJECT-MEMORY.md` — decisions, constraints, gotchas
3. Read `_ai-context/LEARNING-LOG.md` — active lessons
4. If present, check `_ai-context/OPERATIONS.md` for cadences now due and tripwires whose condition has become true
5. Run existing tests (if applicable) — establish known-good baseline

## Governance

Guidance for any host with the ai-governance MCP server connected (the
*enforcement* mechanism, where one exists, lives in the platform overlay such as
CLAUDE.md — not here):
- `evaluate_governance(planned_action="...")` — before any non-read action
- `query_project(query="...")` — before creating or modifying code/content
- `search_references(query="...")` — before implementing a pattern, to reuse proven precedent from the shared Reference Library
- `capture_reference(...)` — after solving a non-obvious, reusable problem, to bank the lesson in the shared, central Reference Library

## Key Commands

- [Add project commands here — build, test, lint, run]

## Project Structure

[Document key directories and files as the project grows]

## Concurrency

Each mutating session owns one checkout and one topic branch. Run the
`start-worktree` skill before edits; read-only sessions may share a checkout.
Claude Code, Codex CLI, and Codex Desktop use different host adapters, but the
Git contract is the same: publish the topic branch before work, refresh from an
explicit live `origin/<default>` before writing final session memory, then
publish with an optimistic fast-forward and retry if another session wins.

Framework creation records recovery metadata atomically with the Git worktree
lock before writing lifecycle state. Codex Desktop records native ownership
before attaching a branch. Validation must match the recorded host, path,
branch, upstream, and owner; cleanup refreshes remote refs before treating them
as durability evidence.

A Git worktree lock is a deletion guard, not a session mutex. It does not make
two writers in one checkout safe. Worktrees also do not isolate ports, databases,
daemons, caches, editable installs, user configuration, ignored files, or symlink
targets; namespace those separately when the project uses them.
"""

# Thin Claude Code overlay. Imports the AGENTS.md body via `@AGENTS.md` (a hard,
# deterministic include — Claude Code memory docs) AND carries the prose "Also read
# AGENTS.md" fallback, so a tool/version that does not resolve the import degrades to
# reading the body rather than losing it (belt-and-suspenders). Holds ONLY
# Claude-Code-specific mechanics — hook enforcement + S-Series stay here, never in the
# imported body (safety boundary, title-10 Appendix A/K.3).
SCAFFOLD_CLAUDE_MD = """# {project_name}

Also read AGENTS.md for project context.
@AGENTS.md

The shared project body — memory-file pointers, session-start protocol, and
governance guidance — is imported from `AGENTS.md` above. Keep only
Claude-Code-specific mechanics below; do not duplicate the body here.

## Governance — ENFORCED BY HOOK (Claude Code)

On Claude Code a PreToolUse hook BLOCKS Bash/Edit/Write until the required
governance tools are called — structural, not advisory. S-Series (safety) stop
rules and MCP-requirement enforcement live here, never in the imported body. On
other hosts this degrades to advisory.

## Plan Mode

Use plan mode for architecture-bearing or multi-file work; get a contrarian
review before leaving plan mode.

## Subagents & Skills

- `.claude/agents/` — installed subagents
- `.claude/skills/` — invoke via `/skill-name`
"""

# Thin Gemini CLI overlay. Same belt-and-suspenders shape as CLAUDE.md, using
# Gemini's relative import literal `@./AGENTS.md` (Gemini memport docs). Emitted in
# the code core kit so a default project auto-loads on Gemini too; a Claude-only
# project simply carries an unused thin file (cheap clutter vs a silently missing
# loader).
SCAFFOLD_GEMINI_MD = """# {project_name}

Also read AGENTS.md for project context.
@./AGENTS.md

The shared project body is imported from `AGENTS.md` above. Keep only
Gemini-specific bits below; do not duplicate the body here.

## Gemini-Specific

- `/memory show` inspects loaded context; `/memory refresh` after editing
  `AGENTS.md` or this file.
- Checkpointing is available for multi-step edits.
"""

SCAFFOLD_COMPLETION_CHECKLIST = """# Post-Change Completion Checklist

For topic branches, make the default branch explicit. Do not infer it from a
possibly stale local `main` or `master`.

## Code changes

1. Run tests — full test suite
2. Code review if substantial
3. Commit the implementation so the topic tree is clean
4. Fetch and merge the explicit live `origin/<default>` into the topic branch
5. Rerun affected tests if refresh integrated new commits
6. Route durable memory, then overwrite _ai-context/SESSION-STATE.md on that refreshed base
7. Commit the close-out and publish only as a fast-forward to the default branch
8. If publication is rejected because origin advanced, repeat refresh → tests → memory → commit → publish; never force-push
9. Verify CI green

## Content changes

1. Run tests — full test suite
2. Commit the content change so the topic tree is clean
3. Refresh from the explicit live `origin/<default>`
4. Route durable memory, then overwrite _ai-context/SESSION-STATE.md
5. Commit and publish with the same optimistic retry rule; never force-push

## Documentation-only changes

1. Commit the documentation change so the topic tree is clean
2. Refresh from the explicit live `origin/<default>`
3. Update _ai-context/SESSION-STATE.md if applicable
4. Commit and publish with the same optimistic retry rule; never force-push
"""

SCAFFOLD_AI_CONTEXT_README = """# {project_name} — AI Context

**Created:** {date}
**Type:** Document project

## Project Description

[Brief description of this project]

## Memory Files

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| SESSION-STATE.md | Current work state | Every session |
| PROJECT-MEMORY.md | Decisions and rationale | When decisions are made |
| LEARNING-LOG.md | Lessons from experience | When lessons emerge |
| BACKLOG.md (if present) | Deferred items and future work | When items emerge or resolve |
| OPERATIONS.md (if present) | Recurring commitments: reviews, tripwires, standing decisions, metrics | When a commitment starts, fires, or is retired |

## Session Protocol

1. Read SESSION-STATE.md first
2. Check PROJECT-MEMORY.md for constraints
3. Check LEARNING-LOG.md for relevant lessons
4. If present, check OPERATIONS.md for recurring commitments now due

## Tailoring

These starter files are deliberately neutral. Tell the AI your use case — what
kind of work lives in this project — and it will propose specialized memory
files to add alongside the core set (for example: an architecture document for
software, a property register for real estate, a style guide for writing).

## Subfolders

A subfolder may carry its own `_ai-context/` for state that only matters inside
it. When working within that subtree, the nearest `_ai-context/` governs; this
folder holds project-wide memory. This convention binds the AI reading these
files — automated tools detect only the top-level `_ai-context/` folder.
"""

# Document-project template variants (session-243). Deliberately use-case-neutral:
# memory files are the highest-priority context an AI loads at session start, and
# section headings act as instructions — a "Tech Stack" heading steers a
# hotel-operations folder toward a software-delivery frame. The code-path
# templates above deliberately KEEP the coding frame (Phase Gates / Tech Stack):
# the CFR pre-seeds and updates that table at defined transitions (§1.4, §7.8.4).
# Guarded both directions by tests/test_scaffold_neutrality.py.

SCAFFOLD_SESSION_STATE_DOC = """# Session State

**Last Updated:** {date}
**Memory Type:** Working (transient)
**Lifecycle:** Overwritten each session; route content out

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Focus

*What is being worked on right now. None yet — ready for the first session.*

## Quick Reference

| Metric | Value |
|--------|-------|
| Project | **{project_name}** |

## Immediate Context

*What a new session needs to know to pick up where this one left off. Overwritten each session — this is a snapshot, not a log. Route as you go: decisions to PROJECT-MEMORY, lessons to LEARNING-LOG, work to BACKLOG, recurring commitments to OPERATIONS, and the session narrative to the commit message.*

## Next Steps

*Define during first session.*
"""

SCAFFOLD_PROJECT_MEMORY_DOC = """# Project Memory

**Memory Type:** Semantic (accumulates)
**Lifecycle:** Grows with project
**Project:** {project_name}
**Created:** {date}

> Record decisions and their rationale here. When in doubt, write it down.
> **What goes elsewhere:** what you are doing right now → `SESSION-STATE.md` · lessons from experience → `LEARNING-LOG.md` · work not started yet → `BACKLOG.md` · commitments that recur → `OPERATIONS.md`. Decisions accumulate here and are superseded, never deleted.

---

## Purpose

[One paragraph: what this project is and what it is for.]

## Key Decisions

| Decision | Date | Rationale |
|----------|------|-----------|
| | | |

## Constraints

*Document any constraints discovered during work — requirements, limits, rules
the work must respect.*

## Gotchas

| # | Gotcha | Date |
|---|--------|------|
| | | |
"""

SCAFFOLD_LEARNING_LOG_DOC = """# Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Distill recurring lessons into standing guidance

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> Route other content: decisions → PROJECT-MEMORY; durable project facts → the relevant reference file.

---

## Active Lessons

*No lessons yet. Add entries as you learn from mistakes and discoveries.*

---

## Recurring Patterns

| Pattern | Promoted To | Date |
|---------|-------------|------|
| | | |
"""

SCAFFOLD_ARCHITECTURE = """# Architecture

> **Starter template — populate as your project matures.** Leave bracketed placeholders until you have real content to add (do not auto-populate with hallucinated architecture — leaving placeholders visible is correct).
> Start with rough shapes; refine as implementation reveals constraints. Per `title-10-ai-coding-cfr.md §1.5.3` (Enhanced Kit evaluation thresholds), consider promoting to `DATA-REFERENCE.md` / `PRODUCT-CONTEXT.md` as complexity grows.

## Overview

[One paragraph: what does this system do, at the highest level?]

## System Structure

[Major components or subsystems. Bullet list or small diagram.]

## Component Responsibilities

[For each component: what it owns, what it does not own.]

## Data Flow

[How data moves through the system at a high level.]

## Dependencies

[External libraries, services, APIs this system depends on.]

## Security Architecture

[Auth model, data access, network exposure, trust boundaries.]

## Architecture Decisions

[ADR-style entries: decision, rationale, consequences. Add as decisions are made.]
"""

SCAFFOLD_SPECIFICATION = """# Specification

> **Starter template — populate as your project matures.** Leave bracketed placeholders until you have real content to add (do not auto-populate — leaving placeholders visible is correct).
> Start with what you know; iterate as the problem is better understood. Specifications firm up through discovery.

## Problem Statement

[What problem does this system solve? Who has the problem?]

## Features

[Primary capabilities. Bullet list or numbered requirements.]

## Scope

**In scope:**
- [Bounded capability 1]

**Out of scope:**
- [Explicit non-goal]

## Success Criteria

[How will you know this system is working as intended? Measurable where possible.]

## Constraints

[Technical, regulatory, resource, or time constraints.]

## Assumptions

[What are you assuming about environment, users, data that, if wrong, would invalidate this spec?]
"""

SCAFFOLD_BACKLOG = """# Backlog

**Memory Type:** Prospective (intentions to act)
**Lifecycle:** Items are removed when done or abandoned — completion is the point.

> **Starter template — populate as your project matures.** Leave bracketed placeholders until you have real items to add (do not auto-populate — leaving placeholders visible is correct).
> This file tracks discussion items and deferred work. It is **NOT** session state — session state lives in `SESSION-STATE.md`. Prospective memory that persists across sessions lives here.

## Active (Implement Now/Soon)

[Items you've committed to implementing. None yet — add as they emerge.]

## Deferred/Future — Discussion

[Items under discussion; not committed to implementation. Flesh out intent, determine if you want to implement, define scope.]

---

*Convention: items move Active ↔ Deferred as priorities shift. Shipped or migrated items are removed from this file — no redirect stubs (commit history is the record).*
"""

SCAFFOLD_OPERATIONS = """# Operations

**Memory Type:** Prospective (recurring commitments)
**Lifecycle:** Items persist indefinitely and are retired only with a documented reason — recurrence is the point, so these are never "done."

> **Starter template — populate as your project matures.** Leave bracketed placeholders until you have real items to add (do not auto-populate — leaving placeholders visible is correct).
> This file tracks **recurring commitments** — the things that are never "done" because recurrence is the point. Deferred work that finishes lives in `BACKLOG.md`; both are prospective memory, split by lifecycle.

## Cadences

[Recurring reviews and their intervals. Record what is reviewed, how often, and when it was last done — a cadence with no last-run date cannot tell you it is overdue. None yet.]

## Tripwires

[Conditions that trigger a re-evaluation when they become true, rather than on a schedule. Record the condition and what to do when it fires. When a tripwire fires and creates discrete work, that work goes to `BACKLOG.md`; the tripwire stays here if it can fire again. None yet.]

## Standing Authorizations

[Durable decisions the human has granted that outlive a single session, so they do not have to be re-asked each time. Record what was granted, its limits, and when. None yet.]

## Metrics

[Health indicators worth tracking over time, each with its definition and baseline. A metric with no baseline cannot show a change. None yet.]

---

*Convention: items are retired with a documented reason, never silently deleted — an entry that vanished and one that was never there look identical later.*
"""


SCAFFOLD_SAAS_OPS_SOP = """# SaaS Production-Operations SOP — {project_name}

**Created:** {date}
**Scope:** This app takes money and/or holds customer data. This file is the
operator's per-app incident card — a per-app instance of the `saas-ops` governance
domain (title-45). The authoritative, maintained gates live in that domain; query it
mid-incident. Fill in the bracketed fields below.

> AI on-call, a designated human as the gate. Mitigate first (you need only the
> *location* of a fault to mitigate, not the root cause), then diagnose. Declare an
> incident early — when a second person is needed, the problem is customer-visible, or
> it is unresolved after a short bounded interval.

## Designated approver (the gate)

- **Accountable approver:** [NAME] — signs off every money / auth / customer-data /
  schema-migration action before it reaches production.
- **On-call human:** [NAME] (solo founder: the same person).

On any personnel change, rotate shared secrets AND remove the departing person's
dashboard / repo / console access (the Production Access & Offboarding gate). This is
where the team-shape RACI seam binds — see `title-45-saas-ops.md`.

## Failure-class router (route by symptom)

Find your symptom, then get the live gate (detect -> respond -> STOP) via
`query_governance("<your symptom>")` against the `saas-ops` domain, or read the
*Situation Index* in `title-45-saas-ops-cfr.md`. Gates are named (not section-numbered)
so this card stays valid as the domain evolves.

| Symptom | Gate |
|---------|------|
| Errors or latency spiked right after a deploy | Bad Deploy |
| Database / connection-pool / quota errors; timeouts | DB & Connection-Pool Exhaustion |
| Session id in the URL; cookie not rotating after login; old cookie still works after logout | Auth & Session Misconfiguration |
| A webhook failed; a customer paid but wasn't provisioned (or was charged twice) | Payment Integrity |
| A secret, API key, or backend key may be exposed, leaked, or expired | Secret & Key Leak |
| A downstream / third-party service is timing out or rate-limiting us | External-Dependency Outage |
| We need to change the database schema / run a migration | Data-Migration Safety |
| A teammate is leaving, or we need to manage production access | Production Access & Offboarding |
| One tenant can see another tenant's data; a table is exposed without row-level security | Multi-Tenant Data-Isolation Breach |
| Data may be lost or silently corrupted; is our backup good? | Data Durability |
| What to do first / when to declare an incident | Cross-Cutting Incident Rules |
| Is this a reportable breach / what about PCI / SOC2? | Compliance Boundary |

## STOP — bring in the designated human

The AI must STOP and get the designated approver before acting when:

- **Money / auth / customer-data / schema-migration** -> never run autonomously;
  mandatory approval by the designated human (the autonomy carve-out — a specialization
  of the title-20 AO-series; do not re-derive the levels).
- **Suspected personal-data breach** -> STOP, bring in the human, and start the
  legal / notification clock. The AI holds only the escalation gate; the notification
  regime itself is counsel-owned.

## Vendor specifics

Concrete numbers — tier limits, connection ceilings, retry windows, backup retention,
the platform's row-level-security mechanics — live in the founder-owned reference, not
here: the `saas-ops` reference library (`reference-library/saas-ops/`), vendor-maintained.
The gate states the decision; the reference holds the number.
"""

# Internal tool-loader registry (v2.63.0). Adding a future AI tool's loader is a
# one-line entry here. Each overlay imports the shared AGENTS.md body. This is NOT a
# user-facing `tools=` arg: every code project emits ALL loaders so a tool is never
# silently missing (the exact defect this arc fixes — a `tools=` opt-in would let a
# user unknowingly omit the loader their tool needs). AGENTS.md is the body itself and
# is listed directly in the core kit below, not in this registry.
SCAFFOLD_TOOL_LOADERS = [
    ("CLAUDE.md", SCAFFOLD_CLAUDE_MD),
    ("GEMINI.md", SCAFFOLD_GEMINI_MD),
]

SCAFFOLD_CORE_FILES = {
    # Unified layout (v2.62.0, reverses v2.36.0): memory files live in
    # _ai-context/ for BOTH project types; only loaders stay at root. Code core
    # emits the AGENTS.md body + the tool-overlay loaders (v2.63.0) so a default
    # scaffold auto-loads on Claude Code, Codex, and Gemini out of the box. Code
    # keeps the CODING templates — layout and template flavor are independent axes.
    "code": [
        ("_ai-context/SESSION-STATE.md", SCAFFOLD_SESSION_STATE),
        ("_ai-context/PROJECT-MEMORY.md", SCAFFOLD_PROJECT_MEMORY),
        ("_ai-context/LEARNING-LOG.md", SCAFFOLD_LEARNING_LOG),
        ("AGENTS.md", SCAFFOLD_AGENTS_MD),
        *SCAFFOLD_TOOL_LOADERS,
    ],
    "document": [
        ("_ai-context/SESSION-STATE.md", SCAFFOLD_SESSION_STATE_DOC),
        ("_ai-context/PROJECT-MEMORY.md", SCAFFOLD_PROJECT_MEMORY_DOC),
        ("_ai-context/LEARNING-LOG.md", SCAFFOLD_LEARNING_LOG_DOC),
        ("_ai-context/README.md", SCAFFOLD_AI_CONTEXT_README),
    ],
}

SCAFFOLD_STANDARD_EXTRAS = {
    "code": [
        # CLAUDE.md moved to the core kit (v2.63.0) — a Claude Code project needs its
        # loader at every tier. Standard extras now equal the CFR §1.5.2 kit exactly.
        ("ARCHITECTURE.md", SCAFFOLD_ARCHITECTURE),
        ("SPECIFICATION.md", SCAFFOLD_SPECIFICATION),
        (
            ".claude/skills/completion-sequence-aigov/checklist.md",
            SCAFFOLD_COMPLETION_CHECKLIST,
        ),
        ("_ai-context/BACKLOG.md", SCAFFOLD_BACKLOG),
        ("_ai-context/OPERATIONS.md", SCAFFOLD_OPERATIONS),
    ],
    # Deferred-work tracking is use-case-neutral (SCAFFOLD_BACKLOG carries no
    # coding frame). Pinned by tests/test_scaffold_parity.py::TestDocumentTierExtras
    # and stated as prose in CFR §1.5.2 (never a table row — the code-tier parity
    # parser slurps any |-line in that section).
    "document": [
        ("_ai-context/BACKLOG.md", SCAFFOLD_BACKLOG),
        ("_ai-context/OPERATIONS.md", SCAFFOLD_OPERATIONS),
    ],
}

# BACKLOG #71 Phase C2: the saas-ops kit tier (= standard + the per-app SOP stub).
# A SEPARATE kit key on purpose — never folded into SCAFFOLD_STANDARD_EXTRAS, which is
# pinned to CFR §1.5.2 by tests/test_scaffold_parity.py. The SOP is saas-ops-specific
# (a per-app instance of the title-45 domain), not a universal standard-kit file.
# Code-only: a money-taking SaaS is always a code project; document gets no extras.
SCAFFOLD_SAAS_OPS_EXTRAS = {
    "code": [
        ("SAAS-OPS-SOP.md", SCAFFOLD_SAAS_OPS_SOP),
    ],
    "document": [],
}

# =============================================================================
# Scaffold Template Versioning (BACKLOG #190)
# =============================================================================
#
# A scaffolded project ages the moment it is created: `scaffold_project` skips
# files that already exist, so a later template improvement never reaches it.
# `mode="sync"` reports that staleness — but it deliberately does NOT diff a
# project's file against today's template.
#
# Why not: these files are SUPPOSED to diverge. They accumulate real project
# content, get distilled at 300 lines per §7.0.4, outgrow starter sections, and
# rename headings as the project matures. A structural diff against the current
# template was prototyped and measured against this repo's own memory files:
# 23 "drift" findings, ZERO true positives — and it was blind to the very change
# that motivated the item (the §7.0.4 lifecycle citation lives in the VALUE of
# `**Lifecycle:**`, not the key, and both files legitimately carry different
# values). A file that diverges by design cannot be its own drift baseline.
#
# What sync does instead: each scaffolded file is stamped at birth with the
# template version it was born from. Sync reports the changelog entries NEWER
# than that stamp. Zero false positives by construction — nothing is inferred —
# and each entry carries the maintainer's INTENT ("remove Phase Gates BECAUSE
# headings act as instructions"), which no diff can recover.
#
# Maintainer duty: change a SCAFFOLD_* template → bump SCAFFOLD_TEMPLATE_VERSION
# and append a changelog entry. This is enforced, not advised: the template
# fingerprint test in tests/test_scaffold_sync.py fails when a template's hash
# changes without a new entry (per the LEARNING-LOG lesson that a hand-synced
# list plus a "keep this updated" comment is not an enforcement mechanism).

SCAFFOLD_TEMPLATE_VERSION = "2.69.0"

# Stamp written as the first line of every scaffolded file. HTML comment —
# invisible in rendered markdown, cheap to parse, survives content edits.
SCAFFOLD_STAMP_FORMAT = (
    "<!-- scaffold: {project_type}/{kit_tier} template-v{template_version} {date} -->"
)

# Append-only. Newest last. `applies_to` names the project types an entry is
# relevant to, so a document project is never told to adopt a coding-frame change.
SCAFFOLD_TEMPLATE_CHANGELOG = [
    {
        "version": "2.61.0",
        "date": "2026-07-11",
        "applies_to": ["document"],
        "files": ["_ai-context/PROJECT-MEMORY.md", "_ai-context/SESSION-STATE.md"],
        "change": (
            "Document projects got use-case-neutral memory templates. PROJECT-MEMORY "
            "lost 'Phase Gates', 'Tech Stack', and 'Spec Summary'; SESSION-STATE's "
            "'Current Phase' became 'Current Focus'."
        ),
        "why": (
            "Memory-file headings act as instructions. The coding-primed headings were "
            "steering document projects (hotels, research folders) toward a "
            "software-delivery frame that did not fit the work."
        ),
        "action": (
            "If this project is not software, remove those sections. Keep any content "
            "under them that still matters — move it to 'Key Decisions' or 'Constraints'."
        ),
    },
    {
        "version": "2.62.0",
        "date": "2026-07-11",
        "applies_to": ["code", "document"],
        "files": ["_ai-context/"],
        "change": (
            "Memory files moved from the project root into `_ai-context/` for ALL "
            "project types (unified layout). Only loaders — AGENTS.md, CLAUDE.md — "
            "stay at the root."
        ),
        "why": (
            "The prior split conflated instruction files (root-bound; tools auto-discover "
            "them) with memory files (nothing auto-discovers them — the loader points at "
            "them). Reverses the v2.36.0 split."
        ),
        "action": (
            "Grandfathered projects keep working: root-layout memory files are still "
            "read, and re-running scaffold will NOT create _ai-context/ duplicates. "
            "Migrate with `git mv` when convenient; update your loader's pointers."
        ),
    },
    {
        "version": "2.63.0",
        "date": "2026-07-15",
        "applies_to": ["code"],
        "files": ["AGENTS.md", "CLAUDE.md", "GEMINI.md"],
        "change": (
            "AGENTS.md is now the shared body; CLAUDE.md and the new GEMINI.md are "
            "thin overlays that import it (`@AGENTS.md` / `@./AGENTS.md`) with a prose "
            "'Also read AGENTS.md' fallback. Both overlays moved into the CORE kit so a "
            "default scaffold auto-loads on Claude Code, Codex, and Gemini."
        ),
        "why": (
            "Claude Code auto-loads only CLAUDE.md and Gemini only GEMINI.md, so an "
            "AGENTS.md-only core left a default project with no loader on those tools. "
            "One shared body (Codex reads it natively) removes the duplication and the gap."
        ),
        "action": (
            "Re-run scaffold to add the missing loaders (GEMINI.md, plus AGENTS.md if "
            "absent); existing files are never overwritten. Safety boundary: keep "
            "governance ENFORCEMENT (hooks, S-Series) in CLAUDE.md — never move it into "
            "the imported AGENTS.md."
        ),
    },
    {
        "version": "2.64.0",
        "date": "2026-08-16",
        "applies_to": ["code", "document"],
        "files": ["_ai-context/OPERATIONS.md", "AGENTS.md", "_ai-context/README.md"],
        "change": (
            "The standard kit now creates `_ai-context/OPERATIONS.md` for recurring "
            "commitments: cadences, tripwires, standing authorizations, and metrics. "
            "The AGENTS.md loader and the document README now also name the "
            "standard-tier memory files, which they previously omitted."
        ),
        "why": (
            "Recurring commitments are prospective memory whose lifecycle is "
            "recurrence rather than completion (CFR 7.0.2), so they belong beside "
            "BACKLOG.md in the same tier, not inside it: filing a cadence in BACKLOG "
            "either closes it, losing the commitment, or leaves it permanently open, "
            "making the backlog unreadable. The loader gap was a separate defect that "
            "already affected you — AGENTS.md listed only the three CORE memory files, "
            "so a standard-kit project got a BACKLOG.md that nothing told the AI to "
            "read. A memory file the loader omits is a file the AI never opens."
        ),
        "action": (
            "Re-run scaffold to add OPERATIONS.md; existing files are never "
            "overwritten. If your AGENTS.md predates this version, add the two "
            "standard-tier lines by hand — scaffold will not rewrite a file you "
            "already have. Recurring items currently parked in BACKLOG.md can move "
            "over as you touch them; there is no need to migrate them in one pass."
        ),
    },
    {
        "version": "2.65.0",
        "date": "2026-08-16",
        "applies_to": ["code", "document"],
        "files": ["_ai-context/PROJECT-MEMORY.md"],
        "change": (
            "PROJECT-MEMORY's header now says what does NOT belong in it, routing "
            "current work to SESSION-STATE, lessons to LEARNING-LOG, unstarted work "
            "to BACKLOG, and recurring commitments to OPERATIONS."
        ),
        "why": (
            "CFR Appendix B.0 defines a three-field header contract — Memory Type, "
            "Lifecycle, and Routing — because those three lines are the ONLY part of a "
            "memory file that survives being read by an agent with no framework "
            "tooling: Codex, ChatGPT, Gemini, or a plain editor. Routing is the field "
            "that does the work and the one that gets skipped. A file that says what it "
            "holds but never what it does not hold reads, to a cold agent, as the place "
            "for anything it is unsure about — which is how a semantic memory file "
            "becomes a dumping ground. Both PROJECT-MEMORY templates had type and "
            "lifecycle and no routing at all."
        ),
        "action": (
            "Add the routing line to your PROJECT-MEMORY.md header; scaffold will not "
            "rewrite a file you already have. If your other memory files predate this, "
            "check them against Appendix B.0 too — the contract is three fields, and "
            "the third is the one to look for."
        ),
    },
    {
        "version": "2.66.0",
        "date": "2026-08-16",
        "applies_to": ["code", "document"],
        "files": ["_ai-context/SESSION-STATE.md"],
        "change": (
            "SESSION-STATE's '## Session Summary' section is now '## Immediate "
            "Context', with routing guidance instead of a place to stack per-session "
            "entries."
        ),
        "why": (
            "A per-session log inside working memory is the region two concurrent "
            "close-outs collide on: both sessions extend the same block, so every "
            "parallel close-out conflicts there. Working memory is overwritten by "
            "definition (CFR 7.0.2) — content that accumulates is episodic or "
            "prospective and has not been routed yet. This repo removed its own "
            "stack for that reason and the template kept shipping it."
        ),
        "action": (
            "Rename the heading and route what is under it: decisions to "
            "PROJECT-MEMORY, lessons to LEARNING-LOG, work to BACKLOG, recurring "
            "commitments to OPERATIONS, narrative to the commit message. Safe to "
            "leave as-is if you never run two sessions at once."
        ),
    },
    {
        "version": "2.67.0",
        "date": "2026-08-17",
        "applies_to": ["code", "document"],
        "files": ["_ai-context/SESSION-STATE.md"],
        "change": (
            "SESSION-STATE's Lifecycle field now reads 'Overwritten each session; "
            "route content out' instead of 'Prune at session start'."
        ),
        "why": (
            "Lifecycle is a contract field (CFR Appendix B.0) — it is one of three "
            "lines an agent with no framework tooling reads to learn how the file "
            "behaves. 'Prune' and 'overwritten' describe different behaviours: prune "
            "implies selective trimming of a file that persists, which invites the "
            "accumulation CFR 7.0.2 says working memory does not do. The taxonomy and "
            "this repo's own file already said overwritten; the templates said prune."
        ),
        "action": (
            "Update the Lifecycle line in your SESSION-STATE.md header. Wording only — "
            "no structural change, and safe to skip if you are not seeing the file grow."
        ),
    },
    {
        "version": "2.68.0",
        "date": "2026-08-17",
        "applies_to": ["code", "document"],
        "files": ["AGENTS.md", "_ai-context/README.md"],
        "change": (
            "The generated session-start protocols now say to check OPERATIONS.md "
            "for cadences that are due and tripwires whose condition has become true."
        ),
        "why": (
            "v2.64.0 added OPERATIONS.md to the kit and named it in the loaders' "
            "file tables, but neither start protocol told the agent to open it. A "
            "cadence nobody checks is worse than one that does not exist, because "
            "the file's presence reads as coverage. Naming a memory file and "
            "instructing someone to read it are different things, and only the "
            "second one makes a recurring commitment recur."
        ),
        "action": (
            "Add the OPERATIONS line to your session-start section. If you have no "
            "OPERATIONS.md the line is inert — it is written 'if present'."
        ),
    },
    {
        "version": "2.69.0",
        "date": "2026-08-18",
        "applies_to": ["code"],
        "files": [
            "AGENTS.md",
            ".claude/skills/completion-sequence/checklist.md",
        ],
        "change": (
            "Generated code projects now define one mutating session per checkout "
            "and topic branch, name the worktree/runtime isolation boundary, and "
            "use recovery-before-mutation startup, owner-bound validation, fresh-remote "
            "cleanup, and refresh-first optimistic publication when origin moves."
        ),
        "why": (
            "A branch alone does not isolate an index or working tree, a worktree "
            "lock only guards deletion, cached local defaults can be stale, and two "
            "correct sessions can race between fetch and push. Interrupted creation "
            "also needs durable recovery evidence before the first mutable gap. The "
            "lifecycle must state these boundaries or it reads as stronger than Git is."
        ),
        "action": (
            "Add the Concurrency section to AGENTS.md and reorder branch close-out "
            "to commit implementation, refresh explicit origin default, retest, "
            "write memory, and publish with retry on a concurrent fast-forward race. "
            "Use a lifecycle helper that records ownership before mutation and refreshes "
            "remote refs before destructive cleanup."
        ),
    },
]


SUBAGENT_EXPLANATION = """
## AI Governance Subagent Installation

### What is a Subagent?

A subagent is a specialized configuration that guides how your AI assistant approaches tasks.
Think of it as giving your AI a specific "role" with clear responsibilities and boundaries —
like hiring a specialist who follows particular protocols.

### Why Install Subagents?

Without structured guidance, AI assistants can:
- Skip validation steps in complex workflows
- Make assumptions instead of asking for clarification
- Apply inconsistent approaches across similar problems
- Miss critical safety considerations

Subagents encode specialized cognitive functions with explicit protocols — making
the discipline of each function auditable rather than relying on ad-hoc prompting.

### What Will Be Installed?

A single markdown file (.claude/agents/<agent_name>.md) containing:
- Role definition and responsibilities
- Tool access permissions appropriate to the agent's function
- Protocol for handling the agent's specific cognitive task

This file stays in your project. You can review, modify, or remove it at any time.
It does not send data anywhere — it only configures how Claude Code behaves when
working in this project.
"""

AVAILABLE_AGENTS = {
    "code-reviewer",
    "coherence-auditor",
    "continuity-auditor",
    "contrarian-reviewer",
    "documentation-writer",
    "orchestrator",
    "security-auditor",
    "test-generator",
    "validator",
    "voice-coach",
}

AGENT_TEMPLATE_HASHES = {
    "code-reviewer": "2252886abbc3d38e21ea5e9f5ff828127be27b76d81cd05076a490766931bd7c",
    "coherence-auditor": "5e42125a1d6e33b3de2184f27d6473c945194b505f0b915d60bd984dcecb20ed",
    "continuity-auditor": "6d6e6115e0370fd1fe65edd3d3e85e53838c463d12bedda867d557566a68d45d",
    "contrarian-reviewer": "237e0b9bbb967c3115ce9bfe0207847cd3fd8dc23e07f9e40fe9212150ce8c67",
    "documentation-writer": "ce76c80212e89048f19061c80938dd9d4d5836dbdfa1841f17d599ace8649d82",
    "orchestrator": "aee04038c316b94a1dda0e84f67d4b4848de48ce5eda5e6f35dc1841ad2c45f4",
    "security-auditor": "25da637835a44a99611c0e28b31cb0cfd1a02a1ffbfc76b22e487a294d3d05b5",
    "test-generator": "611e801f46b3f78b5c412811f925e0e24425997fbd654497e81fdd7dc7de29e8",
    "validator": "f960c9f3abe3b8118df02ea9cd3280198271f750a7f21075aa1c549fd34b4d44",
    "voice-coach": "cbdfd76c83a4cc8c1394a9141c17f5531608d4bb02ea82188a66d04b63a7ca55",
}

# AGENT_METADATA: Summary projections for install_agent and list_agents responses.
# Canonical source: documents/agents/{agent_name}.md
# These are intentionally condensed summaries, not full copies.
# When updating a canonical agent file, check whether action_summary,
# short_description, or applicable_domains here needs a corresponding update.
AGENT_METADATA = {
    "code-reviewer": {
        "short_description": "Fresh-context code review specialist",
        "action_summary": (
            "- Review code against explicit acceptance criteria with fresh eyes\n"
            "- Identify issues by severity (CRITICAL/HIGH/MEDIUM/LOW) with file:line locations\n"
            "- Provide actionable fixes and acknowledge what works well"
        ),
        "activation_message": (
            "The Code Reviewer subagent will activate on your next Claude Code session.\n"
            "It provides independent quality assessment against explicit criteria.\n\n"
            "To verify: Look for 'code-reviewer' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='code-reviewer')"
        ),
        "applicable_domains": ["ai-coding", "ui-ux"],
        "canonical_source": "documents/agents/code-reviewer.md",
    },
    "coherence-auditor": {
        "short_description": "Documentation drift detector",
        "action_summary": (
            "- Detect where documents have silently diverged from system state\n"
            "- Apply 5 generic checks plus file-type-specific checks per Part 4.3\n"
            "- Report staleness, cross-file contradictions, and volatile metric issues"
        ),
        "activation_message": (
            "The Coherence Auditor subagent will activate on your next Claude Code session.\n"
            "It systematically detects documentation drift and cross-file contradictions.\n\n"
            "To verify: Look for 'coherence-auditor' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='coherence-auditor')"
        ),
        "applicable_domains": ["*"],
        "canonical_source": "documents/agents/coherence-auditor.md",
    },
    "continuity-auditor": {
        "short_description": "Narrative consistency verifier",
        "action_summary": (
            "- Check manuscripts against Story Bible for continuity errors\n"
            "- Detect character drift, timeline conflicts, and knowledge-state leaks\n"
            "- Verify world rule compliance and object tracking consistency"
        ),
        "activation_message": (
            "The Continuity Auditor subagent will activate on your next Claude Code session.\n"
            "It verifies narrative consistency against Story Bible entries.\n\n"
            "To verify: Look for 'continuity-auditor' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='continuity-auditor')"
        ),
        "applicable_domains": ["storytelling"],
        "canonical_source": "documents/agents/continuity-auditor.md",
    },
    "contrarian-reviewer": {
        "short_description": "Devil's advocate for high-stakes decisions",
        "action_summary": (
            "- Challenge unstated assumptions and surface blind spots\n"
            "- Identify the highest-leverage concern with full causal chain\n"
            "- Suggest alternative approaches with actionable recommendations"
        ),
        "activation_message": (
            "The Contrarian Reviewer subagent will activate on your next Claude Code session.\n"
            "It challenges assumptions and surfaces overlooked risks before commitment.\n\n"
            "To verify: Look for 'contrarian-reviewer' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='contrarian-reviewer')"
        ),
        "applicable_domains": ["*"],
        "canonical_source": "documents/agents/contrarian-reviewer.md",
    },
    "documentation-writer": {
        "short_description": "Documentation specialist for technical writing",
        "action_summary": (
            "- Write README files, docstrings, guides, and API documentation\n"
            "- Verify all claims against code before documenting\n"
            "- Structure information for the target audience"
        ),
        "activation_message": (
            "The Documentation Writer subagent will activate on your next Claude Code session.\n"
            "It creates accurate, well-structured technical documentation.\n\n"
            "To verify: Look for 'documentation-writer' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='documentation-writer')"
        ),
        "applicable_domains": ["*"],
        "canonical_source": "documents/agents/documentation-writer.md",
    },
    "orchestrator": {
        "short_description": "Governance coordination agent",
        "action_summary": (
            "- Ensure evaluate_governance() is called before any action not on the skip list\n"
            "- Have restricted tools (read + governance only, no edit/write/bash)\n"
            "- Escalate to you when S-Series (safety) principles trigger"
        ),
        "activation_message": (
            "The Orchestrator subagent will activate on your next Claude Code session.\n"
            "It will ensure governance is checked before any action not on the skip list.\n\n"
            "To verify: Look for 'orchestrator' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='orchestrator')"
        ),
        "applicable_domains": ["*"],
        "canonical_source": "documents/agents/orchestrator.md",
    },
    "security-auditor": {
        "short_description": "Security-focused vulnerability detection",
        "action_summary": (
            "- Scan code for OWASP Top 10 and Python-specific vulnerabilities\n"
            "- Classify findings by severity with specific remediation guidance\n"
            "- Think adversarially about trust boundaries and attack surfaces"
        ),
        "activation_message": (
            "The Security Auditor subagent will activate on your next Claude Code session.\n"
            "It identifies security vulnerabilities with an adversarial mindset.\n\n"
            "To verify: Look for 'security-auditor' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='security-auditor')"
        ),
        "applicable_domains": ["ai-coding"],
        "canonical_source": "documents/agents/security-auditor.md",
    },
    "test-generator": {
        "short_description": "Test creation specialist for behavior validation",
        "action_summary": (
            "- Design test cases covering happy paths, errors, and edge cases\n"
            "- Write tests that validate behavior, not implementation details\n"
            "- Track and report coverage impact"
        ),
        "activation_message": (
            "The Test Generator subagent will activate on your next Claude Code session.\n"
            "It creates comprehensive test suites focused on behavior validation.\n\n"
            "To verify: Look for 'test-generator' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='test-generator')"
        ),
        "applicable_domains": ["ai-coding"],
        "canonical_source": "documents/agents/test-generator.md",
    },
    "validator": {
        "short_description": "Criteria-based quality validator",
        "action_summary": (
            "- Validate any artifact against an explicit criteria checklist\n"
            "- Systematically check each criterion with evidence\n"
            "- Report PASS / PASS WITH NOTES / FAIL with actionable fixes"
        ),
        "activation_message": (
            "The Validator subagent will activate on your next Claude Code session.\n"
            "It validates artifacts against explicit criteria with fresh context.\n\n"
            "To verify: Look for 'validator' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='validator')"
        ),
        "applicable_domains": ["*"],
        "canonical_source": "documents/agents/validator.md",
    },
    "voice-coach": {
        "short_description": "Character voice analyst for dialogue distinction",
        "action_summary": (
            "- Evaluate whether characters sound distinct from each other\n"
            "- Detect voice drift from established Character Voice Profiles\n"
            "- Apply the cover-the-attribution voice distinction test"
        ),
        "activation_message": (
            "The Voice Coach subagent will activate on your next Claude Code session.\n"
            "It detects voice convergence and drift from character voice profiles.\n\n"
            "To verify: Look for 'voice-coach' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='voice-coach')"
        ),
        "applicable_domains": ["storytelling"],
        "canonical_source": "documents/agents/voice-coach.md",
    },
}

# R3a / BACKLOG #73 Path B: the two reasoning-discipline S-Series amendments
# (Bias Awareness & Fairness = Amend. II, Transparent Limitations = Amend. III)
# carry NO automatic semantic-retrieval veto. They still surface for REVIEW and
# (III) sit in the universal floor on every call; their stop-the-line authority is
# preserved — exercised by judgment, not by this gate. Genuine harm stays gated by
# Amendment I (Non-Maleficence), which is absent from this set and therefore
# veto-eligible by default. Index-INDEPENDENT by design: the handler consults this
# set at call time, so a stale/un-rebuilt index cannot silently re-fang II/III (the
# failure mode a parsed Principle.veto_eligible field would have introduced).
# Constitution SSOT declares the same classification (Amendments II/III carry a
# "Veto-Eligible: No" tag); the drift-guard test
# `test_veto_ineligible_ids_resolve_to_s_series_principles` asserts these ids stay
# live S-Series principles so a rename/removal can't silently re-fang the gate.
VETO_INELIGIBLE_S_SERIES_IDS = frozenset(
    {
        "meta-safety-bias-awareness-fairness",
        "meta-safety-transparent-limitations",
    }
)

# NOTE: CRITICAL_SAFETY_KEYWORDS, ADVISORY_SAFETY_KEYWORDS, _SAFE_CONTEXT_LEADERS,
# _IMPERATIVE_ACTION_VERBS, _EGRESS_VERBS, _SENTENCE_BOUNDARY moved to the
# dep-light top-level `ai_governance_mcp.safety_scan` module and are re-exported
# at the top of this file (so the enforcement proxy can import them torch-free).
