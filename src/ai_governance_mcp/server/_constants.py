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
# Why not 40000 (the value first committed here): the measurements above show
# diminishing returns. It buys 8 tail bodies for nearly double the rendered size, and ADR-29 thinned CLAUDE.md 151->28 lines to cut exactly that cost on the
# instruction path. Re-inflating it on the retrieval path gives the tokens back.
#
# Why not 12000 (the value the plan targeted): too tight against measured reality. It
# withholds half the bodies, and because real queries return 3-6 principles rather than
# 10, the units it drops are second and third matches the caller often does need.
#
# These are historical ordinary-query measurements, not an output ceiling.
# QUERY_RESPONSE_MAX_CHARS separately bounds the complete rendered response,
# including headers, metadata, omission notices and the dispatcher's reminder.
#
# WHAT THIS BUDGET DOES AND DOES NOT PROMISE. It delivers 77% of bodies complete at the
# default, and the top match complete in the ordinary case — but allocation is
# priority-then-score, NOT score-ordered, so the guarantee is conditional and the
# earlier version of this comment overstated it. See `_allocate_result_content` for the
# priority rule and its measured bound.
QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS = 20000

# Product limit on query_governance's complete TextContent.text, including the
# dispatcher's reminder. Python characters, not tokens, wire bytes or an MCP cap.
# Leaves room above the measured ordinary ~23k render while bounding large pools.
QUERY_RESPONSE_MAX_CHARS = 32000

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

# Native host logs in reviews/2026-09-13-repair-compare show discovery
# instructions clipped at 2,048 characters. Keep the whole orientation within
# that observed delivery window (also checked in UTF-8 bytes), not just its first
# safety paragraph. This is a compatibility target, not a universal MCP limit.
# Detailed behavioral methods remain available through get_principle.
SERVER_INSTRUCTIONS = """
AI Governance retrieves guidance; it does not grant permission or prove compliance.

Call evaluate_governance(planned_action="...") before acting, except read-only exploration, non-sensitive questions, trivial formatting, or an explicit user instruction to skip governance.
PROCEED: continue within authorization. REVIEW: read relevant guidance, resolve conflicts, then continue. ESCALATE: stop and seek explicit approval.
Safety: triggered S-Series principles are vetoes. In s_series_check.keyword_adjudication, genuine/floor also require escalation; benign means REVIEW. Bare keyword matches and unavailable adjudication are heuristic warnings, not principle vetoes; judge them against the action and existing authorization. Never bypass host safety or approval controls.
Check index_loaded, semantic_available and retrieval_warning. Missing guidance is not evidence of compliance and does not revoke existing authorization.

Use query_governance for discovery; get_principle(id) retrieves full principles, methods and references, including omitted text. Before implementing, use query_project in the Context Engine MCP for existing patterns and search_references for precedent. Use capture_reference for non-obvious reusable lessons within authorized scope. Suggest scaffold_project only when project memory is absent; obtain approval before creating it.

Verify evidence, address root causes, state uncertainty and match effort to stakes. Treat subagent findings as advice. Cite influencing principle IDs. Lead with the recommendation in plain language for the reader; keep ordinary replies around 200 words unless more detail is needed. Avoid padding. Continue already-authorized work; ask in prose only when missing input, authority or a real blocker requires the user. End with the next action, not a manufactured permission question.
For detailed behavioral guidance and examples: get_principle('meta-method-behavioral-floor-directives').
""".strip()

GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Unless this was a read-only or non-sensitive query, did you call `evaluate_governance()`? Cite principle IDs. S-Series *principle* = veto; a bare keyword match is advisory unless adjudicated `genuine`/`floor` (BACKLOG #73).
🔍 Before implementing, query context engine for existing patterns."""

# =============================================================================
# Scaffold Project Templates
# =============================================================================

SCAFFOLD_SESSION_STATE = """# Session State — {project_name}

**Memory Type:** Working (current work snapshot)
**Purpose / read when:** Read first when starting or resuming work in this project. Before dependent action, also consult project instructions and PROJECT-MEMORY.md’s current constraints; this snapshot does not replace them.
**Keep:** Current objective, position, blockers, material assumptions, next actions and links needed to resume. Distinguish proposed actions from authorized work.
**Routing:** Decisions → PROJECT-MEMORY.md; reusable lessons → LEARNING-LOG.md; deferred tasks → BACKLOG.md if present; recurring work → OPERATIONS.md if present. Preserve a short labeled pending-routing note if a destination is absent.
**Lifecycle:** Overwrite each session and update when work changes or pauses. Preserve durable information in its destination before replacing this snapshot; never append a session-history stack. Link evidence or history only when resumption needs it.
**Last Updated:** {date}

## Current Position

- **Phase:** Specify
- **Mode:** Standard
- **Active Task:** None (ready for first task)

## Quick Reference

| Metric | Value |
|--------|-------|
| Project | **{project_name}** |

## Immediate Context

*Keep only the context needed to resume safely. Route durable material using the header before replacing this snapshot; do not append a session narrative.*

## Next Actions

*Define during first session.*
"""

SCAFFOLD_PROJECT_MEMORY = """# Project Memory — {project_name}

**Memory Type:** Semantic (durable decisions and constraints)
**Purpose / read when:** Consult current constraints before acting and relevant decisions before changing direction. This file explains choices future sessions must understand.
**Keep:** Decisions with date, rationale, scope and status; binding constraints with their source; pointers to authoritative project documents. Label proposals and unknowns; do not infer approval.
**Routing:** Current progress → SESSION-STATE.md; actionable lessons → LEARNING-LOG.md; tasks → BACKLOG.md if present; recurrence → OPERATIONS.md if present. Link detailed sources instead of copying them. If an existing decision record elsewhere is authoritative, link it rather than create a second record here. Keep absent-destination items briefly labeled pending routing.
**Lifecycle:** Update on a real decision or constraint change. Condense supporting detail; preserve decision records. Mark replaced decisions superseded with date and replacement link; never silently delete their rationale.
**Created:** {date}

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify | Pending | | |
| Plan | Pending | | |
| Implement | Pending | | |
| Validate | Pending | | |

## Spec Summary

*Link the authoritative specification after Specify; do not copy it here.*

## Source Documents

| File | Purpose | Consult When |
|------|---------|--------------|
| | | |

*Register only existing authoritative documents, using links relative to this file.
State what each document owns and when to consult it. Update links when files move;
keep approval and verification status in the source document, not a duplicate table.*

## Key Decisions

| Decision or canonical link | Date | Rationale | Scope / Status |
|----------------------------|------|-----------|----------------|
| | | | |

## Tech Stack

*Fill in after Plan phase.*

## Constraints

*Current binding constraints, their scope and source; unknown is not none.*

*Document any constraints discovered during work.*

## Known Gotchas

| # | Gotcha | Date |
|---|--------|------|
| | | |
"""

SCAFFOLD_LEARNING_LOG = """# Learning Log — {project_name}

**Memory Type:** Episodic (experience that changes future action)
**Purpose / read when:** Before similar work, consult relevant lessons to avoid repeating a mistake or losing a proven approach.
**Keep:** A concise trigger, what was learned and the action to take next time; normally no more than five lines. Include a source link when needed to verify applicability.
**Routing:** Decisions → PROJECT-MEMORY.md; current progress → SESSION-STATE.md; detailed evidence → its linked record. A rule already maintained elsewhere needs a pointer, not another full copy. If a destination is absent, retain a short pending-routing note.
**Lifecycle:** Add only when the lesson changes future behavior. Graduate to standing guidance when patterns emerge. Remove only per §7.3.4: when obsolete, no longer actionable, or incorporated into an identified maintained rule/reference that future work will consult; retain its link. An evidence archive alone is not a replacement for an active lesson. Never prune for size alone.

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
SCAFFOLD_AGENTS_MD = """# Project Working Instructions — {project_name}

**Purpose / read when:** Read when starting work here; these are shared project instructions and document pointers, not session memory.
**Keep:** Enduring project rules, verified commands and where to find current constraints and task-relevant sources. Identify the project scope and label unverified setup claims.
**Routing:** Current work → _ai-context/SESSION-STATE.md; decisions → _ai-context/PROJECT-MEMORY.md; lessons → _ai-context/LEARNING-LOG.md; detailed domain facts → registered source documents. Host-specific mechanics belong in the host adapter. If a required file is unavailable, disclose the gap and resolve it before dependent work.
**Lifecycle:** Update when rules, commands or paths change; replace obsolete instructions. Link detailed references instead of importing their entire contents for every task. No statement here creates host permissions or proves a hook is installed or running.
**Description:** [Brief project description]
**Framework:** AI Coding Methods (current version)
**Mode:** Standard

## Memory Files

Project memory lives in `_ai-context/` (shared project records, not scratch).
In Git projects these files are committed, not ignored scratch. This loader supplies the pointers;
file access and automatic loading depend on the host:
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
5. If `SAAS-OPS-SOP.md` exists, read its service profile, evidence gaps and operating routes before SaaS work
6. Run existing tests (if applicable) — establish known-good baseline

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

For a project without Git, coordinate one writer per shared working file and
preserve important changes in its established dated records. Do not initialize
a repository or publish anything merely to follow these instructions.

The following checkout and branch procedure applies to Git projects only.
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
SCAFFOLD_CLAUDE_MD = """# Claude Project Adapter — {project_name}

**Purpose / read when:** Entry instructions for Claude hosts that read this file; shared project guidance lives in AGENTS.md.
**Keep:** Verified Claude-specific setup and behavior. Do not duplicate shared rules, project facts or session history.
**Use / routing:** Read AGENTS.md; the import below is a convenience. If the host cannot resolve it, open the file explicitly. If it is unavailable, report the missing guidance before dependent work; do not invent its contents.
**Lifecycle:** Recheck after host, hook or instruction changes; remove obsolete setup claims. Hook enforcement is unverified unless supported by current installation and execution evidence. This adapter does not grant permissions.

Also read AGENTS.md for project context.
@AGENTS.md

## Governance — Hook Status (Claude Code)

Hook installation and execution are UNVERIFIED for this generated project.
If configured and verified, a Claude Code PreToolUse hook can gate tool calls;
do not infer that protection from this file. Keep actual host-specific enforcement
configuration and S-Series (safety) stop rules here, never in the imported body.
Safety stop rules still apply when no hook is running; guidance is not enforcement.

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
SCAFFOLD_GEMINI_MD = """# Gemini Project Adapter — {project_name}

**Purpose / read when:** Entry instructions for Gemini hosts that read this file; shared project guidance lives in AGENTS.md.
**Keep:** Verified Gemini-specific setup and behavior. Do not duplicate shared rules, project facts or session history.
**Use / routing:** Read AGENTS.md; the import below is a convenience. If the host cannot resolve it, open the file explicitly. If it is unavailable, report the missing guidance before dependent work; do not invent its contents.
**Lifecycle:** Recheck after host or instruction changes; replace obsolete commands and setup claims. Verify what the host actually loaded. This adapter does not grant permissions.

Also read AGENTS.md for project context.
@./AGENTS.md

## Gemini-Specific

- `/memory show` inspects loaded context; `/memory refresh` after editing
  `AGENTS.md` or this file.
- Checkpointing is available for multi-step edits.
"""

SCAFFOLD_COMPLETION_CHECKLIST = """# Post-Change Completion Checklist — {project_name}

**Purpose / read when:** Reusable procedure for validating and closing a change in this project; consult before declaring work complete or publishing.
**Keep:** Applicable checks, their commands or evidence requirements, prerequisites and failure routes. Separate code, content and document checks where they differ.
**Routing:** Current run results belong in a dated evidence record, with a short pointer in _ai-context/SESSION-STATE.md. Decisions belong in _ai-context/PROJECT-MEMORY.md. If a destination is absent, retain a labeled temporary result until a durable location is established.
**Lifecycle:** Update when checks or project workflows change. Do not accumulate completed runs or reuse an old pass as proof for a new revision. Mark inapplicable checks with reasons; do not silently skip them. Publication and destructive actions still require their applicable authorization.

Paths below are relative to the project root. For topic branches, make the
default branch explicit; do not infer it from a stale local `main` or `master`.
Run the applicable checks, then publish only within existing authorization.

For a project without Git: run the applicable validation, save dated evidence in
its established records location, route durable decisions and lessons, then
replace the session snapshot. Deliver only through the project's authorized
process. Do not initialize a repository or publish merely to complete this list.
The commit, branch and remote steps below apply to Git projects only.

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

SCAFFOLD_AI_CONTEXT_README = """# Project Context Guide — {project_name}

**Purpose / read when:** Start here to find this project's continuity files and reference documents. This is a routing guide, not another store of their contents.
**Keep:** Existing file links, each file's role and when to consult it. Project references are listed in PROJECT-MEMORY.md's Source Documents table.
**Use / routing:** Read SESSION-STATE.md and constraints in PROJECT-MEMORY.md; then consult task-relevant lessons and references. Check OPERATIONS.md for due work when present. Do not assume an absent optional file exists or create it merely to fill this index. Disclose missing required context before dependent work.
**Lifecycle:** Update links when files are added, moved or removed. Replace stale descriptions; do not append activity logs. Access to these files and automatic loading depend on the host and must be verified separately.
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
kind of work lives in this project — and it can propose specialized reference
documents when needed (for example: an architecture document for
software, a property register for real estate, a style guide for writing).
Register their authoritative locations in PROJECT-MEMORY.md; do not copy their
contents into memory or create empty documents merely to fill a folder.

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

SCAFFOLD_SESSION_STATE_DOC = """# Session State — {project_name}

**Memory Type:** Working (current work snapshot)
**Purpose / read when:** Read first when starting or resuming work in this project. Before dependent action, also consult project instructions and PROJECT-MEMORY.md’s current constraints; this snapshot does not replace them.
**Keep:** Current objective, position, blockers, material assumptions, next actions and links needed to resume. Distinguish proposed actions from authorized work.
**Routing:** Decisions → PROJECT-MEMORY.md; reusable lessons → LEARNING-LOG.md; deferred tasks → BACKLOG.md if present; recurring work → OPERATIONS.md if present. Preserve a short labeled pending-routing note if a destination is absent.
**Lifecycle:** Overwrite each session and update when work changes or pauses. Preserve durable information in its destination before replacing this snapshot; never append a session-history stack. Link evidence or history only when resumption needs it.
**Last Updated:** {date}

## Current Focus

*What is being worked on right now. None yet — ready for the first session.*

## Quick Reference

| Metric | Value |
|--------|-------|
| Project | **{project_name}** |

## Immediate Context

*Keep only the context needed to resume safely. Route durable material using the header before replacing this snapshot; do not append a session narrative.*

## Next Steps

*Define during first session.*
"""

SCAFFOLD_PROJECT_MEMORY_DOC = """# Project Memory — {project_name}

**Memory Type:** Semantic (durable decisions and constraints)
**Purpose / read when:** Consult current constraints before acting and relevant decisions before changing direction. This file explains choices future sessions must understand.
**Keep:** Decisions with date, rationale, scope and status; binding constraints with their source; pointers to authoritative project documents. Label proposals and unknowns; do not infer approval.
**Routing:** Current progress → SESSION-STATE.md; actionable lessons → LEARNING-LOG.md; tasks → BACKLOG.md if present; recurrence → OPERATIONS.md if present. Link detailed sources instead of copying them. If an existing decision record elsewhere is authoritative, link it rather than create a second record here. Keep absent-destination items briefly labeled pending routing.
**Lifecycle:** Update on a real decision or constraint change. Condense supporting detail; preserve decision records. Mark replaced decisions superseded with date and replacement link; never silently delete their rationale.
**Created:** {date}

## Purpose

[One paragraph: what this project is and what it is for.]

## Source Documents

| File | Purpose | Consult When |
|------|---------|--------------|
| | | |

*Register only existing authoritative documents, using links relative to this file.
State what each document owns and when to consult it. Update links when files move;
keep approval and verification status in the source document, not a duplicate table.*

## Key Decisions

| Decision or canonical link | Date | Rationale | Scope / Status |
|----------------------------|------|-----------|----------------|
| | | | |

## Constraints

*Current binding constraints, their scope and source; unknown is not none.*

*Document any constraints discovered during work — requirements, limits, rules
the work must respect.*

## Gotchas

| # | Gotcha | Date |
|---|--------|------|
| | | |
"""

SCAFFOLD_LEARNING_LOG_DOC = """# Learning Log — {project_name}

**Memory Type:** Episodic (experience that changes future action)
**Purpose / read when:** Before similar work, consult relevant lessons to avoid repeating a mistake or losing a proven approach.
**Keep:** A concise trigger, what was learned and the action to take next time; normally no more than five lines. Include a source link when needed to verify applicability.
**Routing:** Decisions → PROJECT-MEMORY.md; current progress → SESSION-STATE.md; detailed evidence → its linked record. A rule already maintained elsewhere needs a pointer, not another full copy. If a destination is absent, retain a short pending-routing note.
**Lifecycle:** Add only when the lesson changes future behavior. Graduate to standing guidance when patterns emerge. Remove only per §7.3.4: when obsolete, no longer actionable, or incorporated into an identified maintained rule/reference that future work will consult; retain its link. An evidence archive alone is not a replacement for an active lesson. Never prune for size alone.

## Active Lessons

*No lessons yet. Add entries as you learn from mistakes and discoveries.*

---

## Recurring Patterns

| Pattern | Promoted To | Date |
|---------|-------------|------|
| | | |
"""

SCAFFOLD_ARCHITECTURE = """# Architecture — {project_name}

**Purpose / scope:** Reference for this project's current structure, component responsibilities, boundaries and data flow.
**Read when:** Planning or changing structure, interfaces, dependencies or security boundaries.
**Keep:** Verified design facts and invariants, with source links; label proposed designs and unknowns. Explain relationships that cannot be understood from one component alone.
**Routing:** Requirements → SPECIFICATION.md if present; decisions and rationale → _ai-context/PROJECT-MEMORY.md or its registered canonical decision record; progress → _ai-context/SESSION-STATE.md. Link those records instead of duplicating them. Preserve a brief pending-routing note if a destination is absent.
**Lifecycle:** Recheck affected sections after structural changes; replace outdated descriptions and link consequential decisions. Keep historical diagrams in linked records when needed, not interleaved as current design.
**Verified against:** [Revision or named source and date; unverified until checked]

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

[Link canonical decisions in _ai-context/PROJECT-MEMORY.md or its registered decision-record location. Describe current architectural consequences here; do not duplicate decision records.]
"""

SCAFFOLD_SPECIFICATION = """# Specification — {project_name}

**Purpose / scope:** Defines this project's intended outcomes, boundaries and acceptance criteria.
**Read when:** Planning work, resolving scope or deciding whether an outcome meets the request.
**Keep:** Requirements with status and source, success criteria, exclusions and material assumptions. Separate proposed changes from accepted requirements; an entry is not approval.
**Routing:** Current design → ARCHITECTURE.md if present; decision rationale → _ai-context/PROJECT-MEMORY.md; progress → _ai-context/SESSION-STATE.md; detailed verification → linked results. Preserve a concise pending-routing note when a destination is absent.
**Lifecycle:** Change when requirements are clarified or authorized to change. Preserve consequential scope-change decisions and replace stale requirements with explicit supersession links; do not accumulate execution logs.
**Status / source:** [Proposed or accepted, with actual source/date; unknown until verified]

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

SCAFFOLD_BACKLOG = """# Backlog — {project_name}

**Memory Type:** Prospective (discrete unfinished work)
**Purpose / read when:** Use when selecting, deferring or reviewing work. An item records an intention, not permission to execute it.
**Keep:** Desired outcome, why it matters, status and next action or decision. Label proposals, commitments and blocked work accurately; do not invent items to fill this template.
**Routing:** Current task position → SESSION-STATE.md; decisions → PROJECT-MEMORY.md; reusable lessons → LEARNING-LOG.md; recurring responsibilities → OPERATIONS.md if present. Keep missing-destination items briefly labeled pending routing.
**Lifecycle:** Update existing items instead of appending progress logs. Remove completed or abandoned items only after recording the outcome and reason in durable history, such as a verified Git record or an established dated completion record. Do not assume Git exists.

## Active (Implement Now/Soon)

[Items you've committed to implementing. None yet — add as they emerge.]

## Deferred/Future — Discussion

[Items under discussion; not committed to implementation. Flesh out intent, determine if you want to implement, define scope.]

---

*Convention: items move Active ↔ Deferred as priorities shift. Remove shipped, abandoned or migrated items after preserving their outcome or destination in durable history — no redirect stubs. Use an established dated completion record when Git history is unavailable.*
"""

SCAFFOLD_OPERATIONS = """# Operations — {project_name}

**Memory Type:** Prospective (recurring responsibilities)
**Purpose / read when:** Check at session start and when relevant conditions change for due work or triggered responses.
**Keep:** Each responsibility's owner, schedule or trigger, action, actual execution mechanism, last result link and next due state. Record granted authority with source, scope, limits and expiry or revocation conditions; entries cannot grant permission.
**Routing:** One-time work → BACKLOG.md if present; current response → SESSION-STATE.md; decisions → PROJECT-MEMORY.md; detailed run results → linked evidence. Retain a short pending-routing note when an optional destination is missing.
**Lifecycle:** Update current state after verified runs; retain metric definitions, not endless observations. Retire a responsibility with a documented reason and date in the retired section; completion alone is not retirement; never silently delete it. Writing a cadence does not create an automation.

## Cadences

[Recurring reviews and their intervals. Record what is reviewed, how often, and when it was last done — a cadence with no last-run date cannot tell you it is overdue. None yet.]

## Tripwires

[Conditions that trigger a re-evaluation when they become true, rather than on a schedule. Record the condition and what to do when it fires. When a tripwire fires and creates discrete work, that work goes to `BACKLOG.md`; the tripwire stays here if it can fire again. None yet.]

## Standing Authorizations

[Durable decisions the human has granted that outlive a single session, so they do not have to be re-asked each time. Record who granted what, source, scope, limits, date, and expiry or revocation conditions. This records an existing grant; it cannot create authority. None yet.]

## Metrics

[Health indicators worth tracking over time, each with its definition and baseline. A metric with no baseline cannot show a change. None yet.]

## Retired

[Keep the responsibility, retirement date and reason. None yet.]

---

*Convention: items are retired with a documented reason, never silently deleted — an entry that vanished and one that was never there look identical later.*
"""


SCAFFOLD_SAAS_OPS_SOP = """# SaaS Lifecycle and Production-Operations SOP — {project_name}

**Purpose / read when:** Consult before launch, production changes, incidents or retirement; this records this service's operating routes and evidence.
**Keep:** Owners, recovery routes, approval sources, cost limits and dated evidence tied to the actual release and environment. Start NOT READY / UNVERIFIED until the required evidence exists.
**Routing:** One-time improvements → _ai-context/BACKLOG.md if present; recurring schedules → _ai-context/OPERATIONS.md if present; decisions → _ai-context/PROJECT-MEMORY.md. Link detailed results; never store credentials or raw customer data. Retain short pending-routing notes for absent destinations.
**Lifecycle:** Recheck after changes to the service, provider, release, ownership or recovery path. Mark invalidated evidence and link retained historical results. If a required authority or gate reference is unavailable, resolve it before the dependent action; a completed template cannot substitute for it.
**Created:** {date}
**Readiness:** NOT READY — required evidence is UNVERIFIED until exercised.
**Scope:** Paid SaaS or a service holding customer data, including pilots.
This is per-app state; title-45 `saas-ops` owns the decision gates. Fill fields with
verified facts and links. A generated checklist or an AI assertion is not proof.

## Service profile and authority

- User, buyer, first useful outcome and critical journeys: [RECORD]
- Data sensitivity, individual/organization ownership and forbidden access: [RECORD]
- Customer promise; acceptable outage and data-loss window: [RECORD AND JUSTIFY]
- Accountable approver: [NAME AND CONTACT]. Approval is authority, not technical proof.
- Response coverage, human responder, alternate and escalation trigger: [RECORD]
- Actual unattended monitoring/job mechanism and delivery test: [RECORD]. A chat
  session is not an always-on engineer; missing coverage limits the service promise.
- Owner-controlled accounts, recovery identities and access-vault locations: [LINKS;
  NO SECRETS]. Remove departing access and rotate shared secrets with approval.

Ordinary payments/logins run under the approved application design. Engineering-agent
production interventions touching money, auth, customer data or schema require the
designated human's approval under the title-45 carve-out and title-20 authority rules.

## Capability and cost ledger

Show costs before requesting a spending decision. Use current primary pricing sources;
separate shared subscriptions, per-app/environment charges, usage and transaction fees.

| Capability and chosen provider/plan | Launch required / optional / growth trigger | Fixed + usage unit, currency/tax/billing term | Shared vs app/environment | Source + verified date | Owner, limit alert and response |
|---|---|---|---|---|---|
| [Hosting, database, files/recovery, identity, billing, email, logs/alerts, CI, domain, AI engineering/API, support, legal/accounting] | [NEED AND TRIGGER] | [COST OR QUOTE NEEDED] | [ALLOCATION] | [URL + DATE] | [CONTROL] |

Price a base case and plausible usage/recovery growth. Unknown costs remain explicit;
free-tier limits and unsupported spend caps do not establish cost containment.

## Stack and starter maintenance

- Coherent stack and comparison with a conventional managed monolith: [FIT + TRADEOFFS].
- Starter, if used: [LICENSE/SUPPORT, UPSTREAM UPDATE ROUTE, CUSTOMIZATION BOUNDARY,
  TEST QUALITY, MAINTAINER/SPECIALIST AND VENDOR-EXIT PATH].
- Isolated representative upstream upgrade with one app customization: [REVISION,
  MIGRATION/JOURNEY/RECOVERY RESULTS]. Unexercised maintenance remains UNVERIFIED.

## Agent operating recipe

Link the app's normal tooling; keep handoffs in existing framework memory.

| Operation | Exact command/control + scoped synthetic identity | Expected result / failure report |
|---|---|---|
| Install/bootstrap + supported runtime/tool versions | [RECORD] | [BASELINE] |
| Validate configuration + per-worktree ports/databases | [RECORD] | [FAIL EXPLICITLY; NO PRODUCTION FALLBACK] |
| Synthetic seed/reset | [RECORD] | [ISOLATED STATE] |
| Start/stop + browser access | [RECORD] | [CUSTOMER JOURNEY] |
| Tests + redacted logs | [RECORD] | [RESULT + DIAGNOSTIC LOCATION] |

Fresh authorized agent from clean checkout: [REVISION, COMMANDS, BASELINE, JOURNEY,
HARMLESS SEEDED-FAILURE DIAGNOSIS IN ISOLATION, RESET RESULT]. Recheck after tooling or
environment changes. Written commands alone are UNVERIFIED.

## Recovery authority

| Asset (data/files, backups, keys, source/releases, identity, DNS, billing) | Identity + actual API/CLI/MCP delete/disable route | Protected recovery route + evidence |
|---|---|---|
| [ASSET] | [SCOPE; NO CREDENTIAL VALUES] | [PERMISSION CHECK + DISPOSABLE DRILL] |

Prove ordinary development/repair credentials cannot destroy every recovery route;
dashboard restrictions alone are insufficient. Use non-destructive permission checks
and disposable environments; never destroy real customer data to rehearse recovery.
Separately exercise restore and alternate account recovery. Record retention/deletion
obligations and prefer managed protection or scoped independent copies over custom systems.

## Customer-facing AI release contract — conditional

Applicability: [YES / NO + RATIONALE]. Required only when a model produces a customer
result or takes an application action; AI used only to build the app does not qualify.

- Acceptable/unacceptable outcomes and representative evaluation cases: [LINK].
- Versioned model/prompt/tool/retrieval configuration and permitted data/actions: [LINK].
- Latency, per-task/customer cost, concurrency/retry/token bounds: [LIMIT + CONTROL].
- Fallback and customer-visible failure behavior: [TESTED RESULT].
- Repeated variable cases, actual resulting state, allowed/forbidden actions and
  calibrated graders: [EVIDENCE]. Model agreement is not ground truth. Use the
  title-20 Agent Evaluation Framework; configuration changes invalidate affected evidence.

## Evidence register

Statuses: PASS / FAIL / UNVERIFIED / NOT APPLICABLE (with rationale and approver).
Required FAIL or UNVERIFIED prevents the dependent launch/change. Record what evidence
is invalidated by a change; rerun it against the release, configuration and environment.

| Requirement and applicable risk | Status | Artifact/test result + revision/environment/date | Reviewer/owner | Invalidation trigger + next verification |
|---|---|---|---|---|
| Critical browser journeys before paid/customer-data exposure, onboarding, accessibility and support | UNVERIFIED | [LINK] | [NAME] | [CHANGE] |
| Identity recovery, permissions and forbidden cross-user/tenant access | UNVERIFIED | [LINK] | [NAME] | [AUTH/DATA CHANGE] |
| Billing/entitlement reconciliation, duplicates/reorder/crash, cancellation/refund | UNVERIFIED | [LINK] | [NAME] | [PAYMENT/QUEUE CHANGE] |
| Complete isolated restore, files/config, measured recovery and external reconciliation | UNVERIFIED | [LINK] | [NAME] | [SCHEMA/PROVIDER CHANGE] |
| Synthetic probes, failed jobs, alert delivery and responder exercise | UNVERIFIED | [LINK] | [NAME] | [MONITOR/CONTACT CHANGE] |
| Release gates, preview isolation, representative load and compatible rollback | UNVERIFIED | [LINK] | [NAME] | [RELEASE/CONFIG CHANGE] |
| Privacy, terms, tax/commerce applicability, retention/export/deletion | UNVERIFIED | [LINK] | [NAME] | [MARKET/DATA/CONTRACT CHANGE] |
| Cost controls, ownership/account recovery and specialist handoff | UNVERIFIED | [LINK] | [NAME] | [PLAN/ACCESS/COVERAGE CHANGE] |
| Fresh-agent recipe, harmless failure diagnosis and reset | UNVERIFIED | [LINK] | [NAME] | [TOOLING/ENVIRONMENT CHANGE] |
| Recovery survives ordinary agent delete/disable authority | UNVERIFIED | [LINK] | [NAME] | [IDENTITY/API/ASSET CHANGE] |
| Starter upgrade rehearsal, if used | UNVERIFIED | [LINK OR N/A RATIONALE] | [NAME] | [UPSTREAM/CUSTOMIZATION CHANGE] |
| Customer-facing AI release contract, only if applicable | UNVERIFIED | [LINK OR N/A RATIONALE] | [NAME] | [MODEL/PROMPT/TOOL/RETRIEVAL CHANGE] |

Automate critical browser journeys where material cookie, redirect, multi-page or
client/server/billing risks require them. Use synthetic identities and provider
sandboxes; live probes must not create uncontrolled charges or messages.

## Lifecycle router

Use `query_governance` for discovery, then `get_principle` for the full returned method;
or read the named gate in `title-45-saas-ops-cfr.md`. Keep an accessible reference copy.

| Decision | Gate |
|---|---|
| Define users, risks, service promises and response ownership | Service Capability and Ownership |
| Select proven tools and price launch/optional/growth capabilities | Platform Selection and Costed Capabilities |
| Admit customers or charge money | Launch Evidence |
| Onboard, bill, support, export or delete a customer's data | Commercial and Customer Lifecycle |
| Ship a feature, patch, migration or recovery | Continuous Delivery and Recovery |
| Run maintenance, arrange support and rehearse continuity | Maintenance and Support Continuity |
| Close the app or leave a provider | Service Retirement |

## Failure-class router

| Symptom | Gate |
|---|---|
| Errors/latency after release | Bad Deploy |
| Connection/queue/quota exhaustion | DB & Connection-Pool Exhaustion |
| Identity/session weakness | Auth & Session Misconfiguration |
| Failed webhook, wrong entitlement, duplicate charge | Payment Integrity |
| Exposed/expired key | Secret & Key Leak |
| Dependency timeout/throttling | External-Dependency Outage |
| Schema/data change | Data-Migration Safety |
| Production access or departing contributor | Production Access & Offboarding |
| Unauthorized cross-user/tenant access | Multi-Tenant Data-Isolation Breach |
| Lost, corrupted or unrestorable data | Data Durability |
| Incident declaration/first response | Cross-Cutting Incident Rules |
| Suspected reportable breach | Compliance Boundary |

STOP for unapproved money/auth/customer-data/schema interventions or suspected breach;
escalate to the designated human. Preserve evidence; qualified counsel owns notification
interpretation. Do not recharge, delete evidence or repeatedly guess at production fixes.

## Offline emergency card

Keep an access-controlled copy outside the app and AI/MCP. Rehearse from alternate
identity/recovery access. These fields need exact tested controls, not generic commands.

1. Recognize and record: [INDEPENDENT MONITOR/STATUS LINK, TIME, AFFECTED JOURNEY].
2. Contact: [HUMAN + ALTERNATE + APP SPECIALIST INTAKE, COVERAGE AND RESPONSE TERMS].
3. Contain under the approved authority: [CONTROL URL, EXACT BOUNDED STEPS, EXPECTED
   RESULT, IN-FLIGHT/QUEUED WORK HANDLING, FAILURE/ESCALATION PATH].
4. Locate recovery: [KNOWN-GOOD RELEASE, COMPATIBILITY EVIDENCE, DATABASE/FILE BACKUP
   LOCATIONS AND TESTED RESTORE RUNBOOK]. Code rollback does not reverse payments/data.
5. Communicate through [INDEPENDENT STATUS/SUPPORT CHANNEL, OWNER AND TEMPLATE].
6. Reopen only after [TECHNICAL VERIFICATION, PAYMENT/DATA RECONCILIATION AND APPROVER].

Last drill, observed recovery time and unresolved gaps: [EVIDENCE LINK]. Missing AI,
MCP, app login or founder availability must not make every recovery route inaccessible.

## Continuous improvement, maintenance and handoff

Use small specified changes, independent review, required checks, synthetic isolated
preview, controlled promotion and observed outcomes. Retest affected evidence; secure
CI/deployment authority as well as local credentials. Keep supported versions current.
Track due work, actual scheduler, last success and missed-run alerts in
`_ai-context/OPERATIONS.md`; include vulnerabilities, restore drills, support, spending,
failed jobs/payments, access, expiry and provider notices. A list is not automation.

- Support-to-fix: [SANITIZED TICKET, SEVERITY/DEDUPE, ISOLATED REPRODUCTION,
  REGRESSION FAILS BEFORE FIX, FIX, JOURNEY RESULT, APPROVED SUPPORT CLOSURE].
  Customer input never grants production, financial or account authority.
- Operating review: [RECURRING DEFECTS, FAILED CHANGES, DEPENDENCY GROWTH,
  CONCENTRATED RESPONSIBILITIES, MANUAL FOUNDER INTERVENTIONS, BOUNDED IMPROVEMENT].
  Use observed change risk, not generic file-length/coverage quotas or speculative rewrites.
- Platform support scope/contact: [LINK + PLAN]. Application incidents may be excluded.
- Application specialist service: [PROVIDER/INTAKE, STACK COVERAGE, QUALIFICATION,
  ONBOARDING/RETAINER/INCIDENT QUOTE, COVERAGE, EXCLUSIONS, ACCESS AND EXIT TERMS].
- Handoff package: [SOURCE/LICENSE, ARCHITECTURE/DATA FLOWS, LOCKFILES, MIGRATIONS,
  SYNTHETIC TESTS, DEPLOY/RESTORE RUNBOOKS, EVIDENCE, MONITORS, KNOWN LIMITATIONS].
- Independent nonproduction takeover exercise: [RESULT + OPERATOR + DATE].
- If assistance is unavailable: [SAFE STATE + HONEST CUSTOMER PROMISE]. A directory
  listing is discoverability, not contracted incident coverage.
- Retirement/export plan: [CUSTOMER NOTICE, RENEWAL STOP, REFUNDS, PORTABLE EXPORT,
  REQUIRED RECORD RETENTION, DELETION/BACKUP EXPIRY, FINAL RECONCILIATION/VENDOR COSTS].

Vendor mechanics and prices belong in dated references and this app's verified ledger;
the domain remains vendor-neutral. Never store credentials or raw customer data here.
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
# content, receive policy-specific review per §7.0.4, outgrow starter sections, and
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

SCAFFOLD_TEMPLATE_VERSION = "2.73.0"

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
    {
        "version": "2.70.0",
        "date": "2026-09-20",
        "applies_to": ["code", "document"],
        "files": [
            "_ai-context/SESSION-STATE.md",
            "_ai-context/PROJECT-MEMORY.md",
            "_ai-context/LEARNING-LOG.md",
        ],
        "change": (
            "Lifecycle declarations now explicitly reject session-history stacks, "
            "preserve decisions while condensing supporting detail, date and link "
            "supersession, and restrict lesson removal to §7.3.4 without size-only pruning."
        ),
        "why": (
            "A valid type name or nonempty lifecycle can still contradict policy. "
            "These declarations expose the obligations from CFR §7.0.4 and §§7.1–7.3 "
            "to readers using the files without framework tooling."
        ),
        "action": (
            "Review the three lifecycle fields against current policy and update "
            "their declarations while preserving project-specific routing and content. "
            "Scaffold sync reports this change but does not rewrite existing files."
        ),
    },
    {
        "version": "2.71.0",
        "date": "2026-09-23",
        "applies_to": ["code"],
        "files": ["AGENTS.md", "SAAS-OPS-SOP.md"],
        "change": "SaaS lifecycle evidence, cost visibility, offline recovery and support handoff; conditional session-start loader.",
        "why": "An incident card alone cannot establish launch readiness or keep evidence current through continuous changes.",
        "action": "For SaaS projects, retain per-app facts while adding lifecycle/evidence/cost/offline fields and the conditional AGENTS.md pointer. Start new evidence UNVERIFIED. Sync reports changes without overwriting existing files.",
    },
    {
        "version": "2.72.0",
        "date": "2026-09-24",
        "applies_to": ["code"],
        "files": ["SAAS-OPS-SOP.md"],
        "change": "SaaS agent operating recipe, prospective browser tests, protected recovery, conditional AI contract, starter upgrade and support loop.",
        "why": "Solo operation needs executable evidence that a fresh agent can diagnose safely and that its authority cannot erase all recovery paths.",
        "action": "For SaaS projects, preserve owner facts and add the new operating/evidence fields. Mark AI-feature and starter requirements NOT APPLICABLE only with rationale when absent; new required evidence starts UNVERIFIED. Sync reports changes without rewriting existing files.",
    },
    {
        "version": "2.73.0",
        "date": "2026-09-25",
        "applies_to": ["code", "document"],
        "files": [
            "_ai-context/SESSION-STATE.md",
            "_ai-context/PROJECT-MEMORY.md",
            "_ai-context/LEARNING-LOG.md",
            "_ai-context/BACKLOG.md",
            "_ai-context/OPERATIONS.md",
            "_ai-context/README.md",
            "ARCHITECTURE.md",
            "SPECIFICATION.md",
            "SAAS-OPS-SOP.md",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".claude/skills/completion-sequence-aigov/checklist.md",
        ],
        "change": "Standalone purpose, reading, inclusion, routing and maintenance guidance in every template; source registry in both project-memory variants.",
        "why": "Copied files must remain usable without the manual, Git history or optional destinations. References must not duplicate decision records; generated host text must not claim unverified hook enforcement.",
        "action": "Review and adapt headers to existing content; do not overwrite customized files. Preserve binding constraints, canonical decision records and useful lessons. Add only real sources to the registry. No folder migration or host-setting change is required.",
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
