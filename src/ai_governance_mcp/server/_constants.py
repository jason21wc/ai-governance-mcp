"""Static constants for the AI Governance MCP server.

Templates, metadata, safety keywords, and configuration constants.
Extracted from __init__.py to reduce monolith size (~1100 lines).
"""

import re

MAX_QUERY_LENGTH = 10000
MAX_LOG_CONTENT_LENGTH = 2000
MAX_RELEVANT_METHODS = 5

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
- **S-Series = Absolute Veto**: If S-Series triggers, you MUST escalate regardless of other factors

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

### Conversation Style
Default to **freeform conversational Q&A**, not structured option lists. When gathering requirements, exploring ideas, or discussing approaches, ask questions as natural conversation — not dropdowns or multiple choice. Structured options are appropriate ONLY when converging on a bounded selection (e.g., "which of these 3 specific configs?"). For discovery, exploration, and understanding the user's needs, use open-ended dialogue.

**WRONG** (do not do this during discovery): "Here are your options: A, B, or C. Which would you prefer?"
**RIGHT** (do this instead): "What does your app need to communicate with? Tell me about the data flow you're envisioning."

See Progressive Inquiry Protocol (§7.9).

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
If SESSION-STATE.md, PROJECT-MEMORY.md, and LEARNING-LOG.md are all missing,
suggest using `scaffold_project` to initialize the project with governance memory.
Do not auto-run scaffold_project — ask the user first.
""".strip()

GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Unless this was a read-only or non-sensitive query, did you call `evaluate_governance()`? Cite principle IDs. S-Series = veto.
🔍 Before implementing, query context engine for existing patterns."""

# =============================================================================
# Scaffold Project Templates
# =============================================================================

SCAFFOLD_SESSION_STATE = """# Session State

**Last Updated:** {date}
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

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

## Session Summary

*No sessions yet.*

## Next Actions

*Define during first session.*
"""

SCAFFOLD_PROJECT_MEMORY = """# Project Memory

**Memory Type:** Semantic (accumulates)
**Lifecycle:** Grows with project per §7.0.4
**Project:** {project_name}
**Created:** {date}

> Record decisions and their rationale here. When in doubt, write it down.

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

SCAFFOLD_AGENTS_MD = """# {project_name}

**Description:** [Brief project description]
**Framework:** AI Coding Methods (current version)
**Mode:** Standard

## Session Start

1. Read `SESSION-STATE.md` — current position, quick reference, next actions
2. Read `PROJECT-MEMORY.md` — decisions, constraints, gotchas
3. Read `LEARNING-LOG.md` — active lessons
4. Run existing tests (if applicable) — establish known-good baseline

## Key Commands

- `pytest tests/ -v` — run tests
- [Add project-specific commands here]

## Project Structure

[Document key directories and files as the project grows]
"""

SCAFFOLD_CLAUDE_MD = """# {project_name}

Also read AGENTS.md for project context.

## Governance

If ai-governance MCP server is connected:
- `evaluate_governance(planned_action="...")` — before any non-read action
- `query_project(query="...")` — before creating or modifying code/content

## Subagents

See `.claude/agents/` for installed subagents.
"""

SCAFFOLD_COMPLETION_CHECKLIST = """# Post-Change Completion Checklist

## Code changes

1. Run tests — full test suite
2. Code review if substantial
3. Update SESSION-STATE.md (version, counts, summary)
4. Commit and push
5. Verify CI green

## Content changes

1. Run tests — full test suite
2. Update SESSION-STATE.md
3. Commit and push

## Documentation-only changes

1. Update SESSION-STATE.md if applicable
2. Commit and push
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

## Session Protocol

1. Read SESSION-STATE.md first
2. Check PROJECT-MEMORY.md for constraints
3. Check LEARNING-LOG.md for relevant lessons
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

> **Starter template — populate as your project matures.** Leave bracketed placeholders until you have real items to add (do not auto-populate — leaving placeholders visible is correct).
> This file tracks discussion items and deferred work. It is **NOT** session state — session state lives in `SESSION-STATE.md`. Prospective memory that persists across sessions lives here.

## Active (Implement Now/Soon)

[Items you've committed to implementing. None yet — add as they emerge.]

## Deferred/Future — Discussion

[Items under discussion; not committed to implementation. Flesh out intent, determine if you want to implement, define scope.]

---

*Convention: items move Active ↔ Deferred as priorities shift. Shipped or migrated items are removed from this file — no redirect stubs (commit history is the record).*
"""

SCAFFOLD_CORE_FILES = {
    "code": [
        ("SESSION-STATE.md", SCAFFOLD_SESSION_STATE),
        ("PROJECT-MEMORY.md", SCAFFOLD_PROJECT_MEMORY),
        ("LEARNING-LOG.md", SCAFFOLD_LEARNING_LOG),
        ("AGENTS.md", SCAFFOLD_AGENTS_MD),
    ],
    "document": [
        ("_ai-context/SESSION-STATE.md", SCAFFOLD_SESSION_STATE),
        ("_ai-context/PROJECT-MEMORY.md", SCAFFOLD_PROJECT_MEMORY),
        ("_ai-context/LEARNING-LOG.md", SCAFFOLD_LEARNING_LOG),
        ("_ai-context/README.md", SCAFFOLD_AI_CONTEXT_README),
    ],
}

SCAFFOLD_STANDARD_EXTRAS = {
    "code": [
        ("CLAUDE.md", SCAFFOLD_CLAUDE_MD),
        ("ARCHITECTURE.md", SCAFFOLD_ARCHITECTURE),
        ("SPECIFICATION.md", SCAFFOLD_SPECIFICATION),
        (
            ".claude/skills/completion-sequence/checklist.md",
            SCAFFOLD_COMPLETION_CHECKLIST,
        ),
        ("BACKLOG.md", SCAFFOLD_BACKLOG),
    ],
    "document": [],
}

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
    "code-reviewer": "0a480a1ca6f02a835c813bdb83d307b1f36578f3b4d87e630151ffedbc7806c0",
    "coherence-auditor": "51bd1f2608347d5a134d658715fdb912108bf307492cc338ded2b92ad9b5664b",
    "continuity-auditor": "217a9057bc03cc932d95d6038d1020a9be07cfd35a2ab61a71c66d40968ef76f",
    "contrarian-reviewer": "243c24bdb96d000b1bcbbd2a3570968be68eacec507ba601be279e10e904c3f9",
    "documentation-writer": "c1f1e0d5617d10c6b61cb3fb8e7e436a9ffe18c06f629c2d1201f3da3d998ad0",
    "orchestrator": "101cb68c5b3fb36db357080ec3c42806cb57808eafee9b061b8b00b02ca10501",
    "security-auditor": "5c2217d0a3041ad8afee3b46ae8c66e9e375ebbb9059b7637421037609d0ad27",
    "test-generator": "33efe5ea111cdcf0b613d52a1444420cb21fda8023a89d42a16f93e66c33c489",
    "validator": "4015ea6c86e5ed29db56f9bc5cefcf48bf2b92e65438156640644e7ebb016a03",
    "voice-coach": "3b634f624453c570783c90ea942432ac8557e355002a2797ebee831ba7b2a13a",
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

CRITICAL_SAFETY_KEYWORDS = {
    "credential",
    "password",
    "secret",
    "api key",
    "private key",
    "access token",
    "encryption key",
    "pii",
    "personal data",
    "irreversible",
    "destructive",
}

ADVISORY_SAFETY_KEYWORDS = {
    "delete",
    "remove",
    "drop",
    "destroy",
    "wipe",
    "purge",
    "erase",
    "truncate",
    "clear",
    "reset",
    "overwrite",
    "deploy",
    "token",
    "security",
    "authentication",
    "authorization",
    "permission",
    "external api",
    "production",
    "database",
    "user data",
    "sensitive",
    "confidential",
}

_SAFE_CONTEXT_LEADERS = re.compile(
    r"\b("
    r"no|without|purely|"
    r"describing|description\s+of|class\s+of|category\s+of|"
    r"example\s+of|meta-?description\s+of|kind\s+of|"
    r"documents?|catalogs?|tracks?|enumerates?|references?|notes?|records?|"
    r"prior|previous|historical|past|former|hypothetical|theoretical|"
    r"discussion\s+of|review\s+of|audit\s+of"
    r")\b",
    re.IGNORECASE,
)

_IMPERATIVE_ACTION_VERBS = re.compile(
    r"\b("
    r"ship|deploy|delete|drop|truncate|wipe|rm|erase|purge|"
    r"execute|run|apply|merge|push|force|force-push|"
    r"override|bypass|disable|kill|"
    r"nuke|format|chmod|chown|sudo|flush|revoke|terminate|expire|unset|mv|"
    r"rotate|replace|migrate|modify|restart|restore|clone|copy|move|"
    r"expose|leak|dump"
    r")\b",
    re.IGNORECASE,
)

_SENTENCE_BOUNDARY = re.compile(r"[.!?;\n]+|\s[—–]\s")
