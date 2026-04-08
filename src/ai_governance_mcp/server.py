"""MCP Server for AI Governance document retrieval.

MCP server with 13 tools for hybrid retrieval of governance principles.
"""

import asyncio
import json
import os
import re
import signal
import sys
import tempfile
import threading
import urllib.parse
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from . import __version__
from .config import (
    Settings,
    _find_project_root,
    ensure_directories,
    load_settings,
    setup_logging,
)
from .models import (
    AssessmentStatus,
    ComplianceEvaluation,
    ComplianceStatus,
    ConfidenceLevel,
    ErrorResponse,
    Feedback,
    GovernanceAssessment,
    GovernanceAuditLog,
    GovernanceReasoningLog,
    Metrics,
    QueryLog,
    ReasoningEntry,
    RelevantMethod,
    RelevantPrinciple,
    SSeriesCheck,
    VerificationResult,
    VerificationStatus,
)
from .retrieval import RetrievalEngine

logger = setup_logging()


class ServerInstructionsSecurityError(Exception):
    """Raised when SERVER_INSTRUCTIONS contains suspicious patterns.

    This is a critical security check - if SERVER_INSTRUCTIONS is compromised,
    ALL AI clients consuming this server would be affected.
    """

    pass


# Critical patterns that should NEVER appear in SERVER_INSTRUCTIONS
# These patterns are more targeted than general document scanning because
# SERVER_INSTRUCTIONS is a controlled, hand-written block.
_CRITICAL_INSTRUCTION_PATTERNS = {
    "prompt_injection": re.compile(
        # Patterns must appear at start of sentence or after punctuation
        r"(?:^|[.!?]\s+)ignore\s+(?:previous|prior|above)\s+instructions|"
        r"(?:^|[.!?]\s+)you\s+are\s+now\s+|"
        r"(?:^|[.!?]\s+)disregard\s+(?:all|previous)|"
        r"(?:^|[.!?]\s+)forget\s+(?:everything|all|previous)|"
        r"(?:^|\*\s+)new\s+instructions:",
        re.IGNORECASE | re.MULTILINE,
    ),
    "hidden_instruction": re.compile(
        r"<!--[^>]*(?:instruction|execute|ignore|override)[^>]*-->",
        re.IGNORECASE,
    ),
}


def _validate_server_instructions(instructions: str) -> None:
    """Validate SERVER_INSTRUCTIONS contains no critical security patterns.

    This is called at module load time to ensure the instruction block
    that gets sent to ALL AI clients is clean.

    Args:
        instructions: The SERVER_INSTRUCTIONS string to validate

    Raises:
        ServerInstructionsSecurityError: If critical patterns are detected
    """
    for pattern_name, pattern in _CRITICAL_INSTRUCTION_PATTERNS.items():
        matches = pattern.findall(instructions)
        if matches:
            raise ServerInstructionsSecurityError(
                f"CRITICAL: SERVER_INSTRUCTIONS contains {pattern_name} pattern!\n"
                f"Match: {matches[0][:50]}...\n"
                f"This would compromise ALL AI clients. Blocking server start."
            )


# Global state
_settings: Settings | None = None
_engine: RetrievalEngine | None = None
_metrics: Metrics | None = None
_tiers_config: dict | None = None
_tiers_loaded: bool = False


def get_engine() -> RetrievalEngine:
    """Get or create the retrieval engine."""
    global _settings, _engine, _metrics
    if _engine is None:
        _settings = load_settings()
        ensure_directories(_settings)
        _engine = RetrievalEngine(_settings)
        _metrics = Metrics()
    return _engine


def get_metrics() -> Metrics:
    """Get metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


def _load_tiers_config() -> dict | None:
    """Load tiers.json configuration for universal floor injection.

    Returns the parsed config, or None if the file doesn't exist.
    Cached in module-level _tiers_config after first load.
    Uses _tiers_loaded flag to distinguish "never attempted" from "absent/failed".
    """
    global _tiers_config, _tiers_loaded
    if _tiers_loaded:
        return _tiers_config

    # Look for tiers.json in documents directory
    settings = _settings or load_settings()
    tiers_path = settings.documents_path / "tiers.json"
    if not tiers_path.exists():
        logger.debug(
            "tiers.json not found at %s — universal floor disabled", tiers_path
        )
        _tiers_loaded = True
        return None

    try:
        with open(tiers_path) as f:
            _tiers_config = json.load(f)
        logger.info("Loaded tiers config from %s", tiers_path)
        _tiers_loaded = True
        return _tiers_config
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load tiers.json: %s", e)
        _tiers_loaded = True
        return None


def _build_universal_floor(tiers_config: dict) -> list[dict]:
    """Build compact universal floor items from tiers config.

    Returns a list of check items in compact format:
    {"type": "principle"|"method"|"subagent_check", "id": str|null, "check": str}
    """
    floor_section = tiers_config.get("universal_floor", {})
    items: list[dict] = []

    for p in floor_section.get("principles", []):
        items.append(
            {
                "type": "principle",
                "id": p.get("id"),
                "check": p.get("check", ""),
            }
        )

    for m in floor_section.get("methods", []):
        items.append(
            {
                "type": "method",
                "ref": m.get("ref"),
                "id": m.get("id"),
                "check": m.get("check", ""),
            }
        )

    subagent = floor_section.get("subagent_check")
    if subagent:
        items.append(
            {
                "type": "subagent_check",
                "check": subagent.get("check", ""),
            }
        )

    # Behavioral floor — interaction-style directives (additive reinforcement)
    behavioral = tiers_config.get("behavioral_floor", {})
    for d in behavioral.get("directives", []):
        items.append(
            {
                "type": "behavioral",
                "id": d.get("id"),
                "check": d.get("check", ""),
            }
        )

    return items


def _validate_log_path(log_file: Path) -> None:
    """Validate log file path is within expected boundaries.

    M1 FIX: Prevents arbitrary file writes via manipulated log path env vars.

    Args:
        log_file: The log file path to validate.

    Raises:
        ValueError: If path contains traversal sequences or is outside expected bounds.
    """
    import tempfile

    # Check for path traversal sequences in the raw path string
    path_str = str(log_file)
    if ".." in path_str:
        raise ValueError("Path traversal sequence detected in log path")

    # Resolve to absolute path for containment check
    resolved = log_file.resolve()

    # Log files must be within project root, CWD, user home, or system temp directory
    # (covers default logs/ dir, user-configured paths, Docker /app, and test environments)
    project_root = _find_project_root().resolve()
    cwd = Path.cwd().resolve()
    home_dir = Path.home().resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()

    is_in_project = resolved.is_relative_to(project_root)
    is_in_cwd = resolved.is_relative_to(cwd)
    is_in_home = resolved.is_relative_to(home_dir)
    is_in_temp = resolved.is_relative_to(temp_dir)

    if not (is_in_project or is_in_cwd or is_in_home or is_in_temp):
        raise ValueError(
            f"Log path must be within project root, CWD, home, or temp directory: {resolved}"
        )


def _write_log_sync(log_file: Path, content: str) -> None:
    """Synchronous log write helper for use with asyncio.to_thread.

    H2 FIX: Isolated sync function enables non-blocking async wrapper.
    M1 FIX: Validates path before writing.
    """
    _validate_log_path(log_file)  # M1 FIX: Path containment check
    fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a") as f:
        f.write(content)
        f.flush()  # H3 FIX: Explicit flush reduces data loss on shutdown
        os.fsync(f.fileno())  # Ensure OS buffers are written to disk


async def log_query_async(query_log: QueryLog) -> None:
    """Log query for analytics (async, non-blocking).

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    global _settings
    if _settings:
        log_file = _settings.logs_path / "queries.jsonl"
        content = query_log.model_dump_json() + "\n"
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_query(query_log: QueryLog) -> None:
    """Log query for analytics (sync fallback for non-async contexts)."""
    global _settings
    if _settings:
        log_file = _settings.logs_path / "queries.jsonl"
        _write_log_sync(log_file, query_log.model_dump_json() + "\n")


async def log_feedback_async(feedback: Feedback) -> None:
    """Log feedback for future improvement (async, non-blocking).

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    global _settings
    if _settings:
        log_file = _settings.logs_path / "feedback.jsonl"
        content = feedback.model_dump_json() + "\n"
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_feedback_entry(feedback: Feedback) -> None:
    """Log feedback for future improvement (sync fallback)."""
    global _settings
    if _settings:
        log_file = _settings.logs_path / "feedback.jsonl"
        _write_log_sync(log_file, feedback.model_dump_json() + "\n")


# H1 FIX: Maximum query length to prevent memory/performance issues
MAX_QUERY_LENGTH = 10000

# M1/M4 FIX: Maximum length for logged content to prevent log bloat
MAX_LOG_CONTENT_LENGTH = 2000

# Maximum methods to include in evaluate_governance response (reference-only)
MAX_RELEVANT_METHODS = 5

# H4 FIX: Rate limiting configuration (token bucket algorithm)
RATE_LIMIT_TOKENS = 100  # Maximum tokens (requests) in bucket
RATE_LIMIT_REFILL_RATE = 10  # Tokens added per second
_rate_limit_tokens = RATE_LIMIT_TOKENS
_rate_limit_last_refill = time.time()
_rate_limit_lock = threading.Lock()

# M4 FIX: Patterns for detecting secrets in queries (to redact before logging)
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
    # AWS-style keys
    (re.compile(r"(?i)(AKIA[A-Z0-9]{16})"), r"***AWS_KEY_REDACTED***"),
    # Generic long alphanumeric strings that look like keys (32+ chars)
    (
        re.compile(r"(?<![a-zA-Z0-9])([a-zA-Z0-9]{32,})(?![a-zA-Z0-9])"),
        r"***POSSIBLE_SECRET_REDACTED***",
    ),
]


def _check_rate_limit() -> bool:
    """Check if request is within rate limit using token bucket algorithm.

    H4 FIX: Prevents DoS by limiting request rate.
    Thread-safe via _rate_limit_lock (defense-in-depth for run_in_executor).

    Returns:
        True if request is allowed, False if rate limited.
    """
    global _rate_limit_tokens, _rate_limit_last_refill

    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _rate_limit_last_refill
        _rate_limit_last_refill = now

        # Refill tokens based on elapsed time
        _rate_limit_tokens = min(
            RATE_LIMIT_TOKENS, _rate_limit_tokens + (elapsed * RATE_LIMIT_REFILL_RATE)
        )

        # Check if we have tokens available
        if _rate_limit_tokens >= 1:
            _rate_limit_tokens -= 1
            return True
        return False


def _sanitize_for_logging(content: str) -> str:
    """Sanitize content before logging to prevent sensitive data exposure.

    M1 FIX: Truncates long content.
    M4 FIX: Redacts potential secrets.

    Args:
        content: The content to sanitize.

    Returns:
        Sanitized content safe for logging.
    """
    if not content:
        return content

    # M4: Redact potential secrets
    sanitized = content
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    # M1: Truncate if too long
    if len(sanitized) > MAX_LOG_CONTENT_LENGTH:
        sanitized = sanitized[:MAX_LOG_CONTENT_LENGTH] + "...[TRUNCATED]"

    return sanitized


def _sanitize_error_message(error: Exception) -> str:
    """Sanitize error message to prevent information leakage.

    M6 FIX: Removes internal paths and sensitive information from error messages.
    M3 FIX: More aggressive sanitization for production deployments.

    Args:
        error: The exception to sanitize.

    Returns:
        Sanitized error message safe for external display.
    """
    message = str(error)

    # Remove absolute paths (keep only filename)
    # Pattern matches /path/to/file.py or C:\path\to\file.py
    message = re.sub(
        r'(?:[A-Za-z]:)?(?:[/\\][^/\\:*?"<>|\s]+)+[/\\]([^/\\:*?"<>|\s]+)',
        r"\1",
        message,
    )

    # Remove line numbers from tracebacks
    message = re.sub(r", line \d+", "", message)

    # Remove memory addresses
    message = re.sub(r"0x[0-9a-fA-F]+", "0x***", message)

    # M3 FIX: Additional sanitization patterns

    # Remove Python module paths (e.g., "foo.bar.baz.function")
    message = re.sub(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){2,}\b", "[module]", message)

    # Remove function references in tracebacks (e.g., "in function_name")
    message = re.sub(r"\bin\s+\w+\s*\(", "in [func](", message)

    # Remove stack frame references (e.g., "File 'filename.py'" in tracebacks)
    # Only match when quotes are present (traceback format), not general "File" usage
    message = re.sub(r'File\s+["\'][^"\']+["\']', "File [redacted]", message)

    # Remove internal exception chains
    message = re.sub(
        r"(?:During handling of|The above exception was)",
        "[exception chain]",
        message,
    )

    # Truncate very long messages (could contain embedded data)
    max_error_length = 500
    if len(message) > max_error_length:
        message = message[:max_error_length] + "...[truncated]"

    return message


# Governance audit log storage (in-memory for verification lookups)
# Per §4.6 Governance Enforcement Architecture: enables post-action verification
# C1 FIX: Bounded deque prevents unbounded memory growth in long sessions
AUDIT_LOG_MAX_SIZE = 1000
_audit_log: deque[GovernanceAuditLog] = deque(maxlen=AUDIT_LOG_MAX_SIZE)


async def log_governance_audit_async(audit_entry: GovernanceAuditLog) -> None:
    """Log governance assessment for audit trail (async, non-blocking).

    Per §4.6 Audit Trail Requirements: Every evaluate_governance() call
    generates an audit record for pattern analysis and bypass detection.

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    global _settings, _audit_log

    # Keep in-memory for verification lookups
    _audit_log.append(audit_entry)

    # Persist to file (non-blocking)
    if _settings:
        log_file = _settings.logs_path / "governance_audit.jsonl"
        content = audit_entry.model_dump_json() + "\n"
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_governance_audit(audit_entry: GovernanceAuditLog) -> None:
    """Log governance assessment for audit trail (sync fallback)."""
    global _settings, _audit_log

    # Keep in-memory for verification lookups
    _audit_log.append(audit_entry)

    # Persist to file
    if _settings:
        log_file = _settings.logs_path / "governance_audit.jsonl"
        _write_log_sync(log_file, audit_entry.model_dump_json() + "\n")


def get_audit_log() -> list[GovernanceAuditLog]:
    """Get the in-memory audit log for verification."""
    return list(_audit_log)


# Governance reasoning log storage (linked to audit entries by audit_id)
# Part of Governance Reasoning Externalization feature
_reasoning_log: deque[GovernanceReasoningLog] = deque(maxlen=AUDIT_LOG_MAX_SIZE)


async def log_reasoning_async(entry: GovernanceReasoningLog) -> None:
    """Log governance reasoning trace asynchronously.

    Links to existing audit entry via audit_id.
    Part of Governance Reasoning Externalization feature.
    """
    global _reasoning_log, _settings
    _reasoning_log.append(entry)
    logger.debug("Logged reasoning for audit %s", entry.audit_id)

    # Persist to file (non-blocking)
    if _settings:
        log_file = _settings.logs_path / "governance_reasoning.jsonl"
        content = entry.model_dump_json() + "\n"
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_reasoning_sync(entry: GovernanceReasoningLog) -> None:
    """Log governance reasoning trace synchronously (fallback)."""
    global _reasoning_log, _settings
    _reasoning_log.append(entry)

    if _settings:
        log_file = _settings.logs_path / "governance_reasoning.jsonl"
        _write_log_sync(log_file, entry.model_dump_json() + "\n")


def get_reasoning_log() -> list[GovernanceReasoningLog]:
    """Get the in-memory reasoning log for inspection."""
    return list(_reasoning_log)


# Server instructions injected into AI context at MCP initialization.
# Optimized 2026-01-01: Added Required/Forbidden actions, model-specific guidance.
# Per meta-operational-constraint-based-prompting: explicit constraints reduce ambiguity.
# Per meta-method-instructions-content: includes Overview, When to Use, Hierarchy, Behaviors, Quick Start.
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
- PROCEED_WITH_MODIFICATIONS: Apply required changes, then continue
- ESCALATE: STOP. Inform user. Wait for explicit approval.
- **S-Series = Absolute Veto**: If S-Series triggers, you MUST escalate regardless of other factors

The assessment output determines your next action — it is not an acknowledgment before doing what you planned anyway.

### Required Actions
1. **Evaluate before acting** — `evaluate_governance(planned_action="...")` for any action not on the skip list
2. **Query for guidance** — `query_governance("your concern")` when you need principles to inform decisions
3. **Cite influencing principles** — Reference principle IDs when they guide your approach
4. **Pause on uncertainty** — If requirements are unclear, ask the user before proceeding
5. **Query project context** — Before implementing, call `query_project("...")` via the Context Engine MCP to discover existing patterns

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

# Compact reminder appended to every tool response for consistent governance reinforcement.
# Optimized 2026-01-01: Self-check question format, reduced tokens, removed duplicate hierarchy.
# Design: Self-check prompt triggers reflection; ~35 tokens.
# Per Learning Log 2025-12-31: Passive reminders need explicit action triggers.
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
**Framework:** AI Coding Methods v2.28.0
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
        ("COMPLETION-CHECKLIST.md", SCAFFOLD_COMPLETION_CHECKLIST),
    ],
    "document": [],
}

# Subagent installation explanation for users
# Per Phase 2B design: robust explanation for both experts and beginners
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

Subagents make specialized behaviors automatic, not optional — ensuring consistent,
high-quality AI collaboration every time.

### What Will Be Installed?

A single markdown file (.claude/agents/<agent_name>.md) containing:
- Role definition and responsibilities
- Tool access permissions appropriate to the agent's function
- Protocol for handling the agent's specific cognitive task

This file stays in your project. You can review, modify, or remove it at any time.
It does not send data anywhere — it only configures how Claude Code behaves when
working in this project.
"""

# Validate SERVER_INSTRUCTIONS at module load time
# This catches tampering before any AI client receives the instructions
_validate_server_instructions(SERVER_INSTRUCTIONS)

# Available agents for installation
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

# SHA-256 hashes of known-good agent templates
# Update these when agent templates are intentionally modified
#
# SECURITY LIMITATION: These hashes are stored in the same repository as the
# templates they verify. This means an attacker who can modify the templates
# can also modify these hashes. This provides ADVISORY verification only:
# - Detects accidental modifications
# - Alerts users that content differs from expected
# - Does NOT provide supply chain attack protection
#
# For true integrity verification, see SECURITY.md "Planned" section for
# cryptographic signing roadmap.
AGENT_TEMPLATE_HASHES = {
    "code-reviewer": "271980799e5dd654dda61be5e27efe164df9963214b342a9a006bb345b849975",
    "coherence-auditor": "b79a49bb314b5d56e618cbd1b28eb4346f8da14f91ac43839684f1ef28799074",
    "continuity-auditor": "2ce4369c52d4736f1e3945edf0c0f20d58b26f9195e85beaee1efeb249b05fda",
    "contrarian-reviewer": "67d42bdd15e9300fc544336bdb64990a631968edd535654bca6ec5bd2d44ce85",
    "documentation-writer": "13494a5a13681ed93f9b529b364f6855dffa8ddc2b61ee7595ebd86cf9b414c9",
    "orchestrator": "f7b7945e896bc8e333f7a71fe5f32972d4e5886ab05a4bf4d975974904ecc3c1",
    "security-auditor": "5fe3957bdf3d7990333b00727ab86e58e0e7999b672bf03646e9dd4ef5bbeaf3",
    "test-generator": "033899e2db53f2b0cc86a0e3e452fa4f7d97559e1cfbc61fbf3a082df8e08608",
    "validator": "8712fce1b842da7f9c98aa7947fbe9d88019446922cb121416f93f670bdf2e32",
    "voice-coach": "38f9fe3ca1f123895ec2f8e861e28ffe92dbf3fe4de2877092878985c7051986",
}

# Agent metadata: short descriptions, action summaries, and activation messages
# Used for parameterized install/uninstall messages across all agents
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
    },
    "contrarian-reviewer": {
        "short_description": "Devil's advocate for high-stakes decisions",
        "action_summary": (
            "- Challenge unstated assumptions and surface blind spots\n"
            "- Identify coverage gaps and overlooked risks\n"
            "- Suggest alternative approaches with actionable recommendations"
        ),
        "activation_message": (
            "The Contrarian Reviewer subagent will activate on your next Claude Code session.\n"
            "It challenges assumptions and surfaces overlooked risks before commitment.\n\n"
            "To verify: Look for 'contrarian-reviewer' in the agents list when you start Claude Code.\n"
            "To remove: Use uninstall_agent(agent_name='contrarian-reviewer')"
        ),
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
    },
}


def _verify_template_hash(template_content: str, agent_name: str) -> tuple[bool, str]:
    """Verify agent template content against known-good hash.

    Args:
        template_content: The content of the template file.
        agent_name: Name of the agent to verify.

    Returns:
        Tuple of (is_valid, actual_hash).
        is_valid is True if hash matches or no hash is registered.
    """
    import hashlib

    actual_hash = hashlib.sha256(template_content.encode("utf-8")).hexdigest()
    expected_hash = AGENT_TEMPLATE_HASHES.get(agent_name)

    if expected_hash is None:
        # No hash registered - allow but warn
        return True, actual_hash

    return actual_hash == expected_hash, actual_hash


def _is_within_allowed_scope(p: Path) -> bool:
    """Check if a resolved path is within allowed scope (home, CWD, or temp dirs)."""
    home = Path.home().resolve()
    cwd = Path.cwd().resolve()
    tmp = Path(tempfile.gettempdir()).resolve()
    allowed = [home, cwd, tmp]
    # Also allow system /tmp explicitly (macOS symlinks it to /private/tmp,
    # which differs from tempfile.gettempdir() user-specific temp dir)
    system_tmp = Path("/tmp").resolve()  # nosec B108
    if system_tmp != tmp:
        allowed.append(system_tmp)
    return any(p.is_relative_to(base) for base in allowed)


# Cache for MCP roots result — avoids 2s timeout on every tool call when
# the client doesn't support roots (which is the common case today).
# None = not yet checked, False = checked and unavailable, Path = resolved root.
_cached_roots_path: Path | None | bool = None


async def _resolve_caller_project_path(arguments: dict) -> tuple[Path | None, bool]:
    """Resolve the calling session's project path for file-writing tools.

    Any MCP tool that writes files to the CALLER'S project (not the server's
    own directory) must use this resolver instead of Path.cwd(). Path.cwd()
    resolves to the MCP server's working directory, not the calling session's.

    Priority: arguments['project_path'] > MCP roots > AI_GOVERNANCE_MCP_PROJECT > CWD.
    Explicit caller intent always wins over auto-detection. MCP roots may
    point to platform-internal directories (e.g., Cowork uploads folder)
    that differ from the user's actual project.

    Returns (resolved_path, used_cwd_fallback).
    Returns (None, False) if an explicit path is invalid or outside allowed scope.
    """
    global _cached_roots_path  # noqa: PLW0603

    # Tier 1: Explicit tool argument (caller intent — highest priority)
    raw = arguments.get("project_path")
    if raw and isinstance(raw, str):
        p = Path(raw).resolve()
        if not p.exists() or not p.is_dir():
            logger.debug(
                "project_path '%s' does not exist or is not a directory (resolved: %s)",
                raw,
                p,
            )
            return None, False
        if not _is_within_allowed_scope(p):
            logger.debug("project_path '%s' is outside allowed scope", p)
            return None, False
        return p, False

    # Tier 2: MCP roots (protocol-level auto-detection)
    # Cached per-session to avoid 2s timeout on every call when client
    # doesn't support roots.
    if _cached_roots_path is None:
        try:
            roots_result = await asyncio.wait_for(
                server.request_context.session.list_roots(), timeout=2.0
            )
            if roots_result and roots_result.roots:
                if len(roots_result.roots) > 1:
                    logger.debug(
                        "Multiple MCP roots found (%d), using first: %s",
                        len(roots_result.roots),
                        roots_result.roots[0].uri,
                    )
                parsed = urllib.parse.urlparse(str(roots_result.roots[0].uri))
                if parsed.scheme == "file":
                    p = Path(urllib.parse.unquote(parsed.path)).resolve()
                    if p.exists() and p.is_dir() and _is_within_allowed_scope(p):
                        _cached_roots_path = p
            if _cached_roots_path is None:
                _cached_roots_path = False  # Checked but no usable root
        except Exception as e:
            logger.debug("MCP list_roots() unavailable: %s", e)
            _cached_roots_path = False  # Don't retry

    if isinstance(_cached_roots_path, Path):
        return _cached_roots_path, False

    # Tier 3: Environment variable
    default = os.environ.get("AI_GOVERNANCE_MCP_PROJECT")
    if default:
        p = Path(default).resolve()
        if not p.exists() or not p.is_dir():
            return None, False
        if not _is_within_allowed_scope(p):
            return None, False
        return p, False

    # Tier 4: CWD fallback (with warning flag)
    return Path.cwd(), True


def _detect_claude_code_environment(project_path: Path | None = None) -> bool:
    """Detect if we're running in a Claude Code environment.

    Checks for indicators that suggest Claude Code is the client:
    1. Presence of .claude/ directory in the project directory
    2. Presence of CLAUDE.md file
    3. Environment variable set by Claude Code

    Args:
        project_path: Explicit project directory to check. Falls back to CWD.

    Returns True if Claude Code environment is detected.
    """
    cwd = project_path if project_path is not None else Path.cwd()

    # Check for .claude directory
    if (cwd / ".claude").is_dir():
        return True

    # Check for CLAUDE.md file
    if (cwd / "CLAUDE.md").is_file():
        return True

    # Check parent directories (up to 3 levels) for .claude or CLAUDE.md
    current = cwd
    for _ in range(3):
        parent = current.parent
        if parent == current:  # Reached root
            break
        if (parent / ".claude").is_dir() or (parent / "CLAUDE.md").is_file():
            return True
        current = parent

    return False


def _get_agent_template_path(agent_name: str) -> Path | None:
    """Get the path to an agent template file.

    Agent templates are stored in documents/agents/ within the package.
    """
    global _settings
    if _settings is None:
        _settings = load_settings()

    template_path = _settings.documents_path / "agents" / f"{agent_name}.md"
    if template_path.is_file():
        return template_path
    return None


def _get_agent_install_path(
    agent_name: str, scope: str = "project", project_path: Path | None = None
) -> Path:
    """Get the installation path for an agent.

    Args:
        agent_name: Name of the agent (e.g., 'orchestrator')
        scope: 'project' for .claude/agents/ or 'user' for ~/.claude/agents/
        project_path: Explicit project directory for scope='project'. Falls back to CWD.

    Returns:
        Path where the agent file should be installed.

    Raises:
        ValueError: If agent_name is not in AVAILABLE_AGENTS or path traversal detected.
    """
    # C2 FIX: Validate agent name against allowlist before path construction
    if agent_name not in AVAILABLE_AGENTS:
        raise ValueError(f"Invalid agent: {agent_name}")

    if scope == "user":
        base_path = Path.home() / ".claude" / "agents"
    else:
        base_path = (
            (project_path if project_path is not None else Path.cwd())
            / ".claude"
            / "agents"
        )

    # C2 FIX: Path containment check prevents path traversal attacks
    final_path = (base_path / f"{agent_name}.md").resolve()
    if not final_path.is_relative_to(base_path.resolve()):
        raise ValueError("Path traversal detected")

    return final_path


# Create MCP server
server = Server("ai-governance-mcp", instructions=SERVER_INSTRUCTIONS)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools per spec v4."""
    return [
        # Tool 1: Main retrieval (T13)
        # M5 FIX: Added maxLength constraints for input validation
        Tool(
            name="query_governance",
            description=(
                "Retrieve relevant AI governance principles for a query using hybrid search. "
                "Auto-detects domain from query semantics. Returns scored principles from "
                "Constitution (always) and detected domains with confidence levels. "
                "Use this as the primary tool for getting governance guidance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The situation, task, or concern to get governance guidance for",
                        "maxLength": MAX_QUERY_LENGTH,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional: Force specific domain (e.g. ai-coding, storytelling, ui-ux)",
                        "maxLength": 50,  # M5 FIX
                        "enum": [
                            "constitution",
                            "ai-coding",
                            "multi-agent",
                            "storytelling",
                            "multimodal-rag",
                            "ui-ux",
                            "kmpd",
                        ],
                    },
                    "include_constitution": {
                        "type": "boolean",
                        "description": "Include constitution principles in response (default: true)",
                        "default": True,
                    },
                    "include_methods": {
                        "type": "boolean",
                        "description": "Include procedural methods in response (default: true)",
                        "default": True,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum principles per domain (default: 10)",
                        "default": 10,
                        "minimum": 1,  # M5 FIX
                        "maximum": 50,  # M5 FIX
                    },
                },
                "required": ["query"],
            },
        ),
        # Tool 2: Get specific principle (T14)
        # M5 FIX: Added maxLength constraint
        Tool(
            name="get_principle",
            description=(
                "Get the full content of a specific governance principle by ID. "
                "Use after query_governance to get complete principle text. "
                "IDs follow pattern: meta-core-context-engineering, coding-quality-testing, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "principle_id": {
                        "type": "string",
                        "description": "The principle ID (e.g., 'meta-core-context-engineering', 'coding-quality-testing')",
                        "maxLength": 100,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                },
                "required": ["principle_id"],
            },
        ),
        # Tool 3: List domains (T15)
        Tool(
            name="list_domains",
            description=(
                "List all available governance domains with statistics. "
                "Shows principle counts, descriptions, and domain priorities."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tool 4: Get domain summary (T16)
        # M5 FIX: Added enum constraint for domain validation
        Tool(
            name="get_domain_summary",
            description=(
                "Get detailed information about a specific domain including "
                "all principles and methods. Use for domain exploration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name (e.g. ai-coding, storytelling, ui-ux)",
                        "enum": [
                            "constitution",
                            "ai-coding",
                            "multi-agent",
                            "storytelling",
                            "multimodal-rag",
                            "ui-ux",
                            "kmpd",
                        ],  # M5 FIX
                    },
                },
                "required": ["domain"],
            },
        ),
        # Tool 5: Log feedback (T17)
        # M5 FIX: Added length constraints
        Tool(
            name="log_feedback",
            description=(
                "Log user feedback on retrieval quality. Use this to help improve "
                "future retrieval by recording which principles were helpful or not."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The original query",
                        "maxLength": MAX_QUERY_LENGTH,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                    "principle_id": {
                        "type": "string",
                        "description": "The principle being rated",
                        "maxLength": 100,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                    "rating": {
                        "type": "integer",
                        "description": "Rating from 1 (not helpful) to 5 (very helpful)",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional feedback comment",
                        "maxLength": 1000,  # M5 FIX
                    },
                },
                "required": ["query", "principle_id", "rating"],
            },
        ),
        # Tool 6: Get metrics (T18)
        Tool(
            name="get_metrics",
            description=(
                "Get retrieval performance metrics including query counts, "
                "average latency, confidence distribution, and feedback stats."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tool 7: Evaluate governance (Governance Agent)
        # Per multi-method-governance-agent-pattern (§4.3)
        # M5 FIX: Added length constraints
        Tool(
            name="evaluate_governance",
            description=(
                "Evaluate a planned action against governance principles BEFORE execution. "
                "Call this before any action that is not a read-only operation, non-sensitive question, or trivial formatting change. "
                "Returns compliance assessment with PROCEED, PROCEED_WITH_MODIFICATIONS, or ESCALATE. "
                "S-Series (safety) principles have veto authority - will force ESCALATE if triggered."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "planned_action": {
                        "type": "string",
                        "description": "Description of the action you plan to take",
                        "maxLength": MAX_QUERY_LENGTH,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional: Relevant background context",
                        "maxLength": 2000,  # M5 FIX
                    },
                    "concerns": {
                        "type": "string",
                        "description": "Optional: Specific areas of uncertainty or concern",
                        "maxLength": 1000,  # M5 FIX
                    },
                },
                "required": ["planned_action"],
            },
        ),
        # Tool 8: Verify governance compliance (Post-Action Audit)
        # Per §4.6 Governance Enforcement Architecture, Layer 3
        # M5 FIX: Added length constraints
        Tool(
            name="verify_governance_compliance",
            description=(
                "Verify that governance was consulted for a completed action. "
                "Checks audit log to confirm evaluate_governance was called. "
                "Returns COMPLIANT, NON_COMPLIANT, or PARTIAL. "
                "Use this to catch bypassed governance checks after the fact."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action_description": {
                        "type": "string",
                        "description": "Description of the action that was completed",
                        "maxLength": MAX_QUERY_LENGTH,  # M5 FIX
                        "minLength": 1,  # M5 FIX
                    },
                    "expected_principles": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 100},  # M5 FIX
                        "description": "Optional: Principle IDs that should have been consulted",
                        "maxItems": 20,  # M5 FIX
                    },
                },
                "required": ["action_description"],
            },
        ),
        # Tool 9: Install governance subagent (Claude Code only)
        # Per Phase 2B: LLM-agnostic agent architecture
        Tool(
            name="install_agent",
            description=(
                "Install a governance subagent for Claude Code. "
                "Creates subagent definition files in .claude/agents/. "
                "Only works in Claude Code environments - other platforms receive "
                "governance guidance via server instructions automatically. "
                "Available agents: " + ", ".join(sorted(AVAILABLE_AGENTS)) + "."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of subagent to install (e.g., 'orchestrator')",
                        "enum": sorted(AVAILABLE_AGENTS),
                    },
                    "scope": {
                        "type": "string",
                        "description": "Installation scope: 'project' (.claude/agents/) or 'user' (~/.claude/agents/)",
                        "enum": ["project", "user"],
                        "default": "project",
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Set to true to confirm installation after preview",
                    },
                    "show_manual": {
                        "type": "boolean",
                        "description": "Set to true to get manual installation instructions instead",
                    },
                    "project_path": {
                        "type": "string",
                        "description": (
                            "Absolute path to the target project directory. "
                            "Used when scope='project' and the MCP server's working directory "
                            "differs from the target project. Auto-detected from MCP roots if available."
                        ),
                    },
                },
                "required": ["agent_name"],
            },
        ),
        # Tool 10: Uninstall governance subagent
        Tool(
            name="uninstall_agent",
            description=(
                "Remove a previously installed governance subagent. "
                "Deletes the subagent definition file from .claude/agents/."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of subagent to uninstall (e.g., 'orchestrator')",
                        "enum": sorted(AVAILABLE_AGENTS),
                    },
                    "scope": {
                        "type": "string",
                        "description": "Scope to uninstall from: 'project' or 'user'",
                        "enum": ["project", "user"],
                        "default": "project",
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Set to true to confirm uninstallation",
                    },
                    "project_path": {
                        "type": "string",
                        "description": (
                            "Absolute path to the target project directory. "
                            "Used when scope='project' and the MCP server's working directory "
                            "differs from the target project. Auto-detected from MCP roots if available."
                        ),
                    },
                },
                "required": ["agent_name"],
            },
        ),
        # Tool 11: Log governance reasoning (Audit Trail Enhancement)
        # Part of Governance Reasoning Externalization feature
        Tool(
            name="log_governance_reasoning",
            description=(
                "Log your governance reasoning trace to the audit trail. "
                "Call after evaluate_governance to record per-principle analysis. "
                "Links to assessment via audit_id for audit trail completeness."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "audit_id": {
                        "type": "string",
                        "description": "Audit ID from evaluate_governance response",
                        "maxLength": 50,
                        "minLength": 1,
                        "pattern": "^gov-[a-f0-9]{12}$",
                    },
                    "reasoning": {
                        "type": "array",
                        "description": "Per-principle reasoning entries",
                        "maxItems": 20,
                        "items": {
                            "type": "object",
                            "properties": {
                                "principle_id": {
                                    "type": "string",
                                    "description": "Principle ID analyzed",
                                    "maxLength": 100,
                                    "minLength": 1,
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Assessment status for this principle",
                                    "enum": [
                                        "COMPLIES",
                                        "NEEDS_MODIFICATION",
                                        "VIOLATION",
                                    ],
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Explanation of how principle applies",
                                    "maxLength": 1000,
                                    "minLength": 1,
                                },
                            },
                            "required": ["principle_id", "status", "reasoning"],
                        },
                    },
                    "final_decision": {
                        "type": "string",
                        "description": "Your final governance decision",
                        "enum": [
                            "PROCEED",
                            "PROCEED_WITH_MODIFICATIONS",
                            "ESCALATE",
                        ],
                    },
                    "modifications_applied": {
                        "type": "array",
                        "description": "List of modifications applied (if any)",
                        "maxItems": 10,
                        "items": {
                            "type": "string",
                            "maxLength": 500,
                        },
                    },
                },
                "required": ["audit_id", "reasoning", "final_decision"],
            },
        ),
        # Tool 12: Scaffold project (Project Initialization Part B)
        Tool(
            name="scaffold_project",
            description=(
                "Initialize governance memory files for a new project. "
                "Creates SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md, "
                "and project instruction files. Two-step flow: call without "
                "confirmed for preview, then with confirmed=true to create files."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name (defaults to current directory name)",
                        "maxLength": 100,
                    },
                    "project_type": {
                        "type": "string",
                        "description": "Type: 'code' for repositories, 'document' for folder-based projects",
                        "enum": ["code", "document"],
                    },
                    "kit_tier": {
                        "type": "string",
                        "description": "Kit tier: 'core' (4 files) or 'standard' (6 files, adds CLAUDE.md + checklist)",
                        "enum": ["core", "standard"],
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "Set to true to create files after preview",
                    },
                    "project_path": {
                        "type": "string",
                        "description": (
                            "Absolute path to the target project directory. "
                            "Auto-detected from MCP roots if available; falls back to "
                            "AI_GOVERNANCE_MCP_PROJECT env var, then CWD."
                        ),
                    },
                    "show_manual": {
                        "type": "boolean",
                        "description": (
                            "Set to true to get file contents for manual creation "
                            "instead of writing files directly. Use in sandboxed "
                            "environments (Cowork) where the MCP server cannot "
                            "write to the project directory."
                        ),
                    },
                },
                "required": [],
            },
        ),
        # Tool 13: Capture reference library entry
        Tool(
            name="capture_reference",
            description=(
                "Create a new Reference Library entry (case law precedent). "
                "Generates a markdown file with YAML frontmatter in "
                "reference-library/{domain}/. Provide the content and metadata; "
                "the tool handles formatting and file creation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique entry ID, e.g., 'ref-ai-coding-my-pattern'",
                        "maxLength": 100,
                    },
                    "title": {
                        "type": "string",
                        "description": "Human-readable title",
                        "maxLength": 200,
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain this entry belongs to",
                        "maxLength": 50,
                    },
                    "tags": {
                        "type": "array",
                        "description": "Faceted tags (3-8)",
                        "items": {"type": "string", "maxLength": 50},
                        "maxItems": 10,
                    },
                    "entry_type": {
                        "type": "string",
                        "description": "direct (artifact in library) or reference (pointer to external source)",
                        "enum": ["direct", "reference"],
                    },
                    "summary": {
                        "type": "string",
                        "description": "One-line description for search",
                        "maxLength": 300,
                    },
                    "context": {
                        "type": "string",
                        "description": "When to use this and why it exists",
                        "maxLength": 2000,
                    },
                    "artifact": {
                        "type": "string",
                        "description": "The actual code/template/config or curated summary",
                        "maxLength": 10000,
                    },
                    "lessons": {
                        "type": "string",
                        "description": "What worked, what didn't, edge cases",
                        "maxLength": 2000,
                    },
                    "maturity": {
                        "type": "string",
                        "description": "seedling (new), budding (verified), evergreen (proven)",
                        "enum": ["seedling", "budding", "evergreen"],
                    },
                    "external_url": {
                        "type": "string",
                        "description": "URL for reference entries",
                        "maxLength": 500,
                    },
                    "external_author": {
                        "type": "string",
                        "description": "Author for reference entries",
                        "maxLength": 100,
                    },
                },
                "required": ["id", "title", "domain", "tags", "entry_type", "artifact"],
            },
        ),
    ]


def _append_governance_reminder(result: list[TextContent]) -> list[TextContent]:
    """Append governance reminder to tool response for consistent reinforcement."""
    if result and result[0].text:
        result[0] = TextContent(type="text", text=result[0].text + GOVERNANCE_REMINDER)
    return result


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    # H4 FIX: Rate limiting check
    if not _check_rate_limit():
        error = ErrorResponse(
            error_code="RATE_LIMITED",
            message="Too many requests. Please wait and try again.",
            suggestions=["Wait a few seconds before retrying"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    try:
        engine = get_engine()

        if name == "query_governance":
            result = await _handle_query_governance(engine, arguments)
        elif name == "get_principle":
            result = await _handle_get_principle(engine, arguments)
        elif name == "list_domains":
            result = await _handle_list_domains(engine, arguments)
        elif name == "get_domain_summary":
            result = await _handle_get_domain_summary(engine, arguments)
        elif name == "log_feedback":
            result = await _handle_log_feedback(arguments)
        elif name == "get_metrics":
            result = await _handle_get_metrics(arguments)
        elif name == "evaluate_governance":
            result = await _handle_evaluate_governance(engine, arguments)
        elif name == "verify_governance_compliance":
            result = await _handle_verify_governance(arguments)
        elif name == "install_agent":
            result = await _handle_install_agent(arguments)
        elif name == "uninstall_agent":
            result = await _handle_uninstall_agent(arguments)
        elif name == "log_governance_reasoning":
            result = await _handle_log_governance_reasoning(arguments)
        elif name == "scaffold_project":
            result = await _handle_scaffold_project(arguments)
        elif name == "capture_reference":
            result = await _handle_capture_reference(arguments)
        else:
            result = [TextContent(type="text", text=f"Unknown tool: {name[:50]}")]

        return _append_governance_reminder(result)

    except Exception as e:
        logger.error("Tool error: %s", e, exc_info=True)
        # M6 FIX: Sanitize error message to prevent information leakage
        error = ErrorResponse(
            error_code="TOOL_ERROR",
            message=_sanitize_error_message(e),
            suggestions=[
                "Check query syntax",
                "Verify domain name",
                "Run extractor first",
            ],
        )
        result = [TextContent(type="text", text=error.model_dump_json(indent=2))]
        return _append_governance_reminder(result)


async def _handle_query_governance(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle query_governance tool (T13)."""
    query = args.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    # H1 FIX: Validate query length to prevent memory/performance issues
    if len(query) > MAX_QUERY_LENGTH:
        return [
            TextContent(
                type="text",
                text=f"Error: query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
            )
        ]

    # Validate domain at handler level (defense-in-depth beyond schema enum)
    domain = args.get("domain")
    valid_domains = {
        "constitution",
        "ai-coding",
        "multi-agent",
        "storytelling",
        "multimodal-rag",
        "ui-ux",
        "kmpd",
    }
    if domain is not None and domain not in valid_domains:
        return [
            TextContent(
                type="text",
                text=f"Error: Invalid domain '{domain}'. Valid: {', '.join(sorted(valid_domains))}",
            )
        ]

    # Clamp max_results at handler level (defense-in-depth beyond schema bounds)
    max_results = args.get("max_results")
    if max_results is not None:
        try:
            max_results = min(max(int(max_results), 1), 50)
        except (ValueError, TypeError):
            max_results = 10

    result = engine.retrieve(
        query=query,
        domain=domain,
        include_constitution=args.get("include_constitution", True),
        include_methods=args.get("include_methods", True),
        max_results=max_results,
    )

    # Update metrics (thread-safe via lock — defense-in-depth for run_in_executor)
    metrics = get_metrics()
    retrieval_ms = result.retrieval_time_ms or 0.0
    with _rate_limit_lock:
        metrics.total_queries += 1
        metrics.avg_retrieval_time_ms = (
            metrics.avg_retrieval_time_ms * (metrics.total_queries - 1) + retrieval_ms
        ) / metrics.total_queries
        if result.s_series_triggered:
            metrics.s_series_trigger_count += 1

        for detected_domain in result.domains_detected:
            metrics.domain_query_counts[detected_domain] = (
                metrics.domain_query_counts.get(detected_domain, 0) + 1
            )

        # Confidence distribution — inside lock for thread safety
        for sp in result.constitution_principles + result.domain_principles:
            level = sp.confidence.value
            metrics.confidence_distribution[level] = (
                metrics.confidence_distribution.get(level, 0) + 1
            )

    # Log query (H2 FIX: use async version to avoid blocking)
    # M1/M4 FIX: Sanitize query before logging
    query_log = QueryLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        query=_sanitize_for_logging(query),
        domains_detected=result.domains_detected,
        principles_returned=[
            sp.principle.id
            for sp in result.constitution_principles + result.domain_principles
        ],
        methods_returned=[sm.method.id for sm in result.methods],
        s_series_triggered=result.s_series_triggered,
        retrieval_time_ms=result.retrieval_time_ms,
        top_confidence=result.constitution_principles[0].confidence
        if result.constitution_principles
        else None,
    )
    await log_query_async(query_log)

    # Format response
    output = _format_retrieval_result(result)
    return [TextContent(type="text", text=output)]


def _format_retrieval_result(result) -> str:
    """Format retrieval result as readable markdown."""
    lines = []

    # Header with S-Series warning
    if result.s_series_triggered:
        lines.append("## S-SERIES TRIGGERED - Safety/Ethics Principles Apply")
        lines.append("")

    lines.append(f"**Query:** {result.query}")
    lines.append(
        f"**Domains Detected:** {', '.join(result.domains_detected) or 'None (Constitution only)'}"
    )
    if result.domain_scores:
        scores = ", ".join(f"{d}: {s:.2f}" for d, s in result.domain_scores.items())
        lines.append(f"**Domain Scores:** {scores}")
    lines.append(f"**Retrieval Time:** {result.retrieval_time_ms:.1f}ms")
    lines.append("")

    # Constitution principles
    if result.constitution_principles:
        lines.append("## Constitution Principles")
        for sp in result.constitution_principles:
            p = sp.principle
            lines.append(f"### [{sp.confidence.value.upper()}] {p.id}: {p.title}")
            # Only show series if it exists (legacy format)
            series_info = f"Series: {p.series_code} | " if p.series_code else ""
            lines.append(
                f"*{series_info}Scores: BM25={sp.keyword_score:.2f}, Semantic={sp.semantic_score:.2f}, Combined={sp.combined_score:.2f}*"
            )
            if sp.match_reasons:
                lines.append(f"*Match: {', '.join(sp.match_reasons)}*")
            lines.append("")
            content_preview = (
                p.content[:600] + "..." if len(p.content) > 600 else p.content
            )
            lines.append(content_preview)
            lines.append("")

    # Domain principles
    if result.domain_principles:
        lines.append("## Domain Principles")
        for sp in result.domain_principles:
            p = sp.principle
            lines.append(f"### [{sp.confidence.value.upper()}] {p.id}: {p.title}")
            # Only show series if it exists (legacy format)
            series_info = f" | Series: {p.series_code}" if p.series_code else ""
            lines.append(
                f"*Domain: {p.domain}{series_info} | Combined: {sp.combined_score:.2f}*"
            )
            lines.append("")
            content_preview = (
                p.content[:600] + "..." if len(p.content) > 600 else p.content
            )
            lines.append(content_preview)
            lines.append("")

    # Methods
    if result.methods:
        lines.append("## Applicable Methods")
        for sm in result.methods:
            m = sm.method
            lines.append(f"- **{m.id}:** {m.title} (confidence: {sm.confidence.value})")
        lines.append("")

    # Reference Library (Case Law Precedent)
    if result.references:
        lines.append("## Relevant Precedent (Reference Library)")
        for sr in result.references:
            r = sr.reference
            status_icon = {
                "current": "🟢",
                "caution": "🟡",
                "deprecated": "🔴",
                "archived": "⬜",
            }
            icon = status_icon.get(r.status, "")
            lines.append(
                f"- {icon} **{r.id}:** {r.title} [{r.maturity}/{r.status}] "
                f"(confidence: {sr.confidence.value})"
            )
            if r.summary:
                lines.append(f"  {r.summary}")
        lines.append("")

    if not result.constitution_principles and not result.domain_principles:
        lines.append(
            "*No matching principles found. Try rephrasing your query or specifying a domain.*"
        )

    # Feedback prompt to activate dormant feedback collection
    # Per contrarian review finding: feedback infrastructure exists but is unused
    if result.constitution_principles or result.domain_principles:
        lines.append("---")
        lines.append(
            "*Help improve retrieval: Use `log_feedback(query, principle_id, rating)` "
            "to rate relevance (1-5). High-rated principles get boosted in future queries.*"
        )

    return "\n".join(lines)


async def _handle_get_principle(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle get_principle tool (T14).

    Retrieves both principles and methods by ID.
    Method IDs contain '-method-' (e.g., meta-method-header-hierarchy).
    """
    principle_id = args.get("principle_id", "")
    if not principle_id:
        return [TextContent(type="text", text="Error: principle_id is required")]

    # Try principle lookup first
    principle = engine.get_principle_by_id(principle_id)
    if principle:
        output = {
            "id": principle.id,
            "type": "principle",
            "domain": principle.domain,
            "series": principle.series_code,  # May be None for new format
            "number": principle.number,
            "title": principle.title,
            "content": principle.content,
            "line_range": principle.line_range,
            "keywords": principle.metadata.keywords,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Try method lookup (IDs contain '-method-')
    method = engine.get_method_by_id(principle_id)
    if method:
        output = {
            "id": method.id,
            "type": "method",
            "domain": method.domain,
            "title": method.title,
            "content": method.content,
            "line_range": method.line_range,
            "keywords": method.keywords,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    error = ErrorResponse(
        error_code="PRINCIPLE_NOT_FOUND",
        message=f"Principle '{principle_id}' not found",
        suggestions=[
            "Use list_domains to see available domains",
            "Check ID format: meta-core-context-engineering, coding-quality-testing",
        ],
    )
    return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_list_domains(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle list_domains tool (T15)."""
    domains = engine.list_domains()

    output = {
        "total_domains": len(domains),
        "domains": domains,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_domain_summary(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle get_domain_summary tool (T16)."""
    domain = args.get("domain", "")
    if not domain:
        return [TextContent(type="text", text="Error: domain is required")]

    # Validate domain at handler level (defense-in-depth beyond schema enum)
    valid_domains = {
        "constitution",
        "ai-coding",
        "multi-agent",
        "storytelling",
        "multimodal-rag",
        "ui-ux",
        "kmpd",
    }
    if domain not in valid_domains:
        return [
            TextContent(
                type="text",
                text=f"Error: Invalid domain '{domain}'. Valid: {', '.join(sorted(valid_domains))}",
            )
        ]

    summary = engine.get_domain_summary(domain)
    if summary:
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]

    error = ErrorResponse(
        error_code="DOMAIN_NOT_FOUND",
        message=f"Domain '{domain}' not found",
        suggestions=["Use list_domains to see available domains"],
    )
    return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_log_feedback(args: dict) -> list[TextContent]:
    """Handle log_feedback tool (T17)."""
    query = args.get("query", "")
    principle_id = args.get("principle_id", "")
    rating = args.get("rating", 0)

    if not query or not principle_id or not rating:
        return [
            TextContent(
                type="text", text="Error: query, principle_id, and rating are required"
            )
        ]

    if not 1 <= rating <= 5:
        return [TextContent(type="text", text="Error: rating must be 1-5")]

    # M1/M4 FIX: Sanitize query and comment before logging
    feedback = Feedback(
        query=_sanitize_for_logging(query),
        principle_id=principle_id,
        rating=rating,
        comment=_sanitize_for_logging(args.get("comment", ""))
        if args.get("comment")
        else None,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    await log_feedback_async(feedback)

    # Update metrics (thread-safe via lock)
    metrics = get_metrics()
    with _rate_limit_lock:
        metrics.feedback_count += 1
        if metrics.avg_feedback_rating is None:
            metrics.avg_feedback_rating = float(rating)
        else:
            metrics.avg_feedback_rating = (
                metrics.avg_feedback_rating * (metrics.feedback_count - 1) + rating
            ) / metrics.feedback_count

    output = {
        "status": "logged",
        "feedback_id": feedback.timestamp,
        "message": "Thank you for your feedback!",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_metrics(args: dict) -> list[TextContent]:
    """Handle get_metrics tool (T18)."""
    metrics = get_metrics()

    # Governance overhead metrics (addresses contrarian review finding)
    # Note: Token counting removed per YAGNI - can't accurately measure at MCP layer
    gov_overhead = metrics.governance_overhead
    governance_overhead_output = {
        "governance_evaluations": gov_overhead.governance_evaluations,
        "avg_governance_time_ms": round(gov_overhead.avg_governance_time_ms, 2),
        "total_governance_time_ms": round(gov_overhead.total_governance_time_ms, 2),
        "assessment_breakdown": {
            "proceed": gov_overhead.proceed_count,
            "proceed_with_modifications": gov_overhead.proceed_with_modifications_count,
            "escalate": gov_overhead.escalation_count,
        },
    }

    output = {
        "total_queries": metrics.total_queries,
        "avg_retrieval_time_ms": round(metrics.avg_retrieval_time_ms, 2),
        "s_series_trigger_count": metrics.s_series_trigger_count,
        "domain_query_counts": metrics.domain_query_counts,
        "confidence_distribution": metrics.confidence_distribution,
        "feedback_count": metrics.feedback_count,
        "avg_feedback_rating": round(metrics.avg_feedback_rating, 2)
        if metrics.avg_feedback_rating
        else None,
        "governance_overhead": governance_overhead_output,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


# S-Series safety keywords for automatic safety concern detection
# Per governance hierarchy: S-Series has veto authority
# Critical safety keywords that ALWAYS force escalation regardless of semantic
# retrieval results. These are inherently dangerous in any context.
# Empirically validated: the semantic retrieval path does NOT reliably catch
# queries containing only these terms (e.g., "exfiltrate API tokens" retrieves
# Design Token Architecture, not Non-Maleficence).
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

# Advisory safety keywords that produce warnings but do NOT force escalation
# on their own. These are common in safe contexts (e.g., "remove section",
# "deploy docs", "database schema update") and only escalate when the semantic
# retrieval path ALSO identifies an S-Series principle.
# Intentionally ignores negation — "do not delete" should still flag.
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


def _detect_safety_concerns(action: str) -> tuple[list[str], list[str]]:
    """Detect potential safety concerns with two confidence levels.

    Returns (critical_concerns, advisory_concerns):
    - critical_concerns: keywords that ALWAYS force escalation
    - advisory_concerns: keywords that produce warnings only (escalate
      only when semantic retrieval also finds S-Series principles)

    Intentionally ignores negation — "do not delete" should still flag,
    because negation-aware parsing creates bypass vectors.
    """
    action_lower = action.lower()
    critical = []
    advisory = []

    for keyword in CRITICAL_SAFETY_KEYWORDS:
        if keyword in action_lower:
            critical.append(f"Action mentions '{keyword}' - requires safety review")

    for keyword in ADVISORY_SAFETY_KEYWORDS:
        if keyword in action_lower:
            advisory.append(f"Action mentions '{keyword}' - may require safety review")

    return critical, advisory


def _determine_confidence(
    best_score: float, s_series_triggered: bool
) -> ConfidenceLevel:
    """Determine assessment confidence based on retrieval quality and S-Series.

    Per design decision: S-Series = HIGH (safety is not uncertain).
    Otherwise based on retrieval match quality.
    """
    if s_series_triggered:
        return ConfidenceLevel.HIGH  # Safety concerns are not uncertain
    if best_score >= 0.7:
        return ConfidenceLevel.HIGH
    if best_score >= 0.4:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


async def _handle_evaluate_governance(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle evaluate_governance tool (Governance Agent).

    Per multi-method-governance-agent-pattern (§4.3):
    - Evaluates planned actions against governance principles
    - Uses existing query_governance for retrieval
    - Auto-detects S-Series concerns with keyword scanning
    - Returns assessment with compliance status per principle
    """
    planned_action = args.get("planned_action", "")
    context = args.get("context", "")
    concerns = args.get("concerns", "")

    if not planned_action:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="planned_action is required",
            suggestions=["Provide a description of the action you plan to take"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # H1 FIX: Validate input lengths to prevent memory/performance issues
    total_length = len(planned_action) + len(context) + len(concerns)
    if total_length > MAX_QUERY_LENGTH:
        error = ErrorResponse(
            error_code="INPUT_TOO_LONG",
            message=f"Combined input exceeds maximum length of {MAX_QUERY_LENGTH} characters",
            suggestions=["Reduce the length of planned_action, context, or concerns"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Start timing for overhead measurement
    governance_start_time = time.time()

    # Build composite query from inputs
    query_parts = [planned_action]
    if context:
        query_parts.append(f"Context: {context}")
    if concerns:
        query_parts.append(f"Concerns: {concerns}")
    composite_query = " ".join(query_parts)

    # Use existing retrieval engine
    result = engine.retrieve(composite_query, max_results=10)

    # Collect relevant principles
    all_principles = result.constitution_principles + result.domain_principles
    relevant_principles: list[RelevantPrinciple] = []
    compliance_evaluations: list[ComplianceEvaluation] = []
    s_series_principles: list[str] = []

    # Track best score for confidence calculation
    best_score = 0.0

    for sp in all_principles[:10]:  # Limit to top 10
        p = sp.principle
        score = sp.combined_score
        if score > best_score:
            best_score = score

        # Check for S-Series
        if p.series_code == "S":
            s_series_principles.append(p.id)

        # Add to relevant principles
        relevance = (
            f"Matched via {', '.join(sp.match_reasons)}"
            if sp.match_reasons
            else "Semantic match"
        )
        relevant_principles.append(
            RelevantPrinciple(
                id=p.id,
                title=p.title,
                content=p.content,  # Full text for AI reasoning (§4.6.1)
                relevance=relevance,
                score=score,
                series_code=p.series_code,  # S, C, Q, O, G, MA
                domain=p.domain,  # Source domain for hierarchy
            )
        )

        # Evaluate compliance - default to COMPLIANT with guidance
        # Note: Full compliance evaluation would require deeper analysis
        # This provides the principle for the AI to apply
        compliance_evaluations.append(
            ComplianceEvaluation(
                principle_id=p.id,
                principle_title=p.title,
                status=ComplianceStatus.COMPLIANT,
                finding=f"Review action against: {p.title}. Apply this principle before proceeding.",
            )
        )

    # Collect relevant methods (reference-only)
    relevant_methods: list[RelevantMethod] = []
    for sm in result.methods[:MAX_RELEVANT_METHODS]:
        m = sm.method
        relevant_methods.append(
            RelevantMethod(
                id=m.id,
                title=m.title,
                domain=m.domain,
                score=sm.combined_score,
                confidence=sm.confidence.value,
            )
        )

    # S-Series keyword detection (dual-path: critical + advisory)
    # Concatenate action + context for comprehensive keyword checking
    composite_text = planned_action
    if context:
        composite_text = f"{planned_action} {context}"

    critical_concerns, advisory_concerns = _detect_safety_concerns(composite_text)

    # Determine S-Series triggering with hybrid logic:
    # - Semantic S-Series match → ALWAYS escalate (high confidence)
    # - Critical keyword match → ALWAYS escalate (inherently dangerous)
    # - Advisory keyword match ONLY → WARNING (noted, not forced)
    semantic_safety = len(s_series_principles) > 0
    critical_keyword = len(critical_concerns) > 0
    advisory_keyword = len(advisory_concerns) > 0

    s_series_triggered = semantic_safety or critical_keyword
    keyword_only_warning = advisory_keyword and not s_series_triggered

    # Build S-Series check result
    s_series_check = SSeriesCheck(
        triggered=s_series_triggered,
        principles=s_series_principles,
        safety_concerns=critical_concerns,
        safety_warnings=advisory_concerns if keyword_only_warning else [],
    )

    # Determine assessment status
    # Per §4.6.1 Assessment Responsibility Layers:
    # - S-Series = script-enforced (non-negotiable safety)
    # - Non-S-Series = AI judgment required for nuanced compliance
    required_modifications: list[str] = []
    requires_ai_judgment = False
    ai_judgment_guidance: str | None = None

    if s_series_triggered:
        # Script-enforced safety veto - no AI override possible
        assessment = AssessmentStatus.ESCALATE
        requires_ai_judgment = False
        trigger_details = s_series_principles + critical_concerns
        if semantic_safety and advisory_keyword:
            trigger_details.extend(advisory_concerns)
        rationale = (
            "S-Series (safety) principles triggered. "
            "Human review required before proceeding. "
            f"Triggered by: {', '.join(trigger_details)}"
        )
    elif not relevant_principles:
        # No principles found - safe to proceed
        assessment = AssessmentStatus.PROCEED
        requires_ai_judgment = False
        rationale = (
            "No strongly relevant governance principles found. "
            "Action may proceed but consider querying with more specific terms."
        )
    else:
        # Non-S-Series with relevant principles - AI judgment required
        # Script provides data, AI determines PROCEED vs PROCEED_WITH_MODIFICATIONS
        assessment = (
            AssessmentStatus.PROCEED
        )  # Default, AI may determine modifications needed
        requires_ai_judgment = True
        ai_judgment_guidance = (
            "Review each principle's content against the planned action. "
            "If the action conflicts with principle requirements and modifications can resolve it, "
            "communicate PROCEED_WITH_MODIFICATIONS with the specific changes needed. "
            "If the action fully complies with all principles, confirm PROCEED."
        )
        if relevant_methods:
            ai_judgment_guidance += (
                " Relevant methods are included as references — use get_principle(id) "
                "to retrieve full procedural content for any method that would help "
                "determine compliance."
            )
        top_principle = relevant_principles[0]
        rationale = (
            f"AI judgment required for {len(relevant_principles)} relevant principles. "
            f"Primary principle: {top_principle.title} (score: {top_principle.score:.2f}). "
            "Read principle content and determine if modifications are needed."
        )

    # Determine confidence
    confidence = _determine_confidence(best_score, s_series_triggered)

    # Build assessment
    governance_assessment = GovernanceAssessment(
        action_reviewed=planned_action,
        assessment=assessment,
        confidence=confidence,
        relevant_principles=relevant_principles,
        relevant_methods=relevant_methods,
        compliance_evaluation=compliance_evaluations,
        required_modifications=required_modifications,
        s_series_check=s_series_check,
        rationale=rationale,
        requires_ai_judgment=requires_ai_judgment,  # §4.6.1 hybrid assessment
        ai_judgment_guidance=ai_judgment_guidance,
    )

    # Log audit record (per §4.6 Audit Trail Requirements)
    # H2 FIX: use async version to avoid blocking
    # M1/M4 FIX: Sanitize action before logging
    audit_entry = GovernanceAuditLog(
        audit_id=governance_assessment.audit_id,
        timestamp=governance_assessment.timestamp,
        action=_sanitize_for_logging(planned_action),
        assessment=assessment,
        principles_consulted=[rp.id for rp in relevant_principles],
        methods_surfaced=[rm.id for rm in relevant_methods],
        s_series_triggered=s_series_triggered,
        modifications=required_modifications if required_modifications else None,
        escalation_reason=rationale
        if assessment == AssessmentStatus.ESCALATE
        else None,
        confidence=confidence,
    )
    await log_governance_audit_async(audit_entry)

    # Format output
    output = governance_assessment.model_dump()
    # Convert enums to strings for JSON serialization
    output["assessment"] = output["assessment"].value
    output["confidence"] = output["confidence"].value
    for ce in output["compliance_evaluation"]:
        ce["status"] = ce["status"].value

    # Inject universal floor (Tier 1) — separate section, not counted against max_results
    tiers_config = _load_tiers_config()
    if tiers_config:
        output["universal_floor"] = _build_universal_floor(tiers_config)

    # Record governance overhead metrics (thread-safe via lock)
    governance_time_ms = (time.time() - governance_start_time) * 1000
    with _rate_limit_lock:
        get_metrics().governance_overhead.record_evaluation(
            time_ms=governance_time_ms, assessment=output["assessment"]
        )

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_verify_governance(args: dict) -> list[TextContent]:
    """Handle verify_governance_compliance tool (Post-Action Audit).

    Per §4.6 Governance Enforcement Architecture, Layer 3:
    - Checks whether governance was consulted for a completed action
    - Returns COMPLIANT, NON_COMPLIANT, or PARTIAL
    - Enables detection of bypassed governance checks after the fact
    """
    action_description = args.get("action_description", "")
    expected_principles = args.get("expected_principles", [])

    if not action_description:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="action_description is required",
            suggestions=["Describe the action that was completed"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Get the audit log
    audit_log = get_audit_log()

    if not audit_log:
        # No governance checks have been performed in this session
        verification = VerificationResult(
            action_description=action_description,
            status=VerificationStatus.NON_COMPLIANT,
            matching_audit_id=None,
            finding=(
                "No governance checks have been performed in this session. "
                "All actions except reads, non-sensitive questions, and trivial formatting should be preceded by evaluate_governance()."
            ),
        )
        output = verification.model_dump()
        output["status"] = output["status"].value
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Search for matching audit entries
    # Simple keyword matching - could be enhanced with semantic similarity
    action_words = set(action_description.lower().split())
    best_match: GovernanceAuditLog | None = None
    best_overlap = 0

    for entry in reversed(audit_log):  # Check most recent first
        entry_words = set(entry.action.lower().split())
        overlap = len(action_words & entry_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = entry

    if not best_match or best_overlap < 2:
        # No matching governance check found
        verification = VerificationResult(
            action_description=action_description,
            status=VerificationStatus.NON_COMPLIANT,
            matching_audit_id=None,
            finding=(
                f"No governance check found matching this action. "
                f"Found {len(audit_log)} audit entries, but none matched. "
                "Action may have bypassed governance. Consider retroactive review."
            ),
        )
        output = verification.model_dump()
        output["status"] = output["status"].value
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Found a matching entry - check if expected principles were consulted
    if expected_principles:
        consulted = set(best_match.principles_consulted)
        expected = set(expected_principles)
        missing = expected - consulted

        if missing:
            verification = VerificationResult(
                action_description=action_description,
                status=VerificationStatus.PARTIAL,
                matching_audit_id=best_match.audit_id,
                finding=(
                    f"Governance was consulted (audit_id: {best_match.audit_id}), "
                    f"but expected principles were not all checked. "
                    f"Missing: {', '.join(missing)}. "
                    f"Assessment was: {best_match.assessment.value}."
                ),
            )
            output = verification.model_dump()
            output["status"] = output["status"].value
            return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Full compliance
    verification = VerificationResult(
        action_description=action_description,
        status=VerificationStatus.COMPLIANT,
        matching_audit_id=best_match.audit_id,
        finding=(
            f"Governance was consulted before this action. "
            f"Audit ID: {best_match.audit_id}. "
            f"Assessment: {best_match.assessment.value}. "
            f"Principles consulted: {len(best_match.principles_consulted)}."
        ),
    )
    output = verification.model_dump()
    output["status"] = output["status"].value
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_install_agent(args: dict) -> list[TextContent]:
    """Handle install_agent tool.

    Per Phase 2B LLM-Agnostic Agent Architecture:
    - Only installs for Claude Code environments
    - Other platforms skip (already have SERVER_INSTRUCTIONS)
    - Uses confirmation flow: preview -> user choice -> action
    """
    agent_name = args.get("agent_name", "")
    scope = args.get("scope", "project")
    confirmed = args.get("confirmed", False)
    show_manual = args.get("show_manual", False)

    # Validate agent name
    if agent_name not in AVAILABLE_AGENTS:
        error = ErrorResponse(
            error_code="INVALID_AGENT",
            message=f"Unknown agent: {agent_name}",
            suggestions=[f"Available agents: {', '.join(AVAILABLE_AGENTS)}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Resolve project path for scope="project"
    project_path = None
    used_cwd_fallback = False
    if scope == "project":
        project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
        if project_path is None:
            error = ErrorResponse(
                error_code="INVALID_PROJECT_PATH",
                message="Specified project_path does not exist or is outside allowed scope",
                suggestions=[
                    "Provide an absolute path to an existing directory within your home directory"
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Check if Claude Code environment
    is_claude = _detect_claude_code_environment(project_path)

    if not is_claude:
        # Non-Claude platform: provide agent content as reference material
        template_path = _get_agent_template_path(agent_name)
        agent_content = ""
        if template_path:
            agent_content = template_path.read_text()

        output = {
            "status": "not_applicable",
            "platform": "non-claude",
            "agent_name": agent_name,
            "message": (
                f"Subagent installation is only available for Claude Code. "
                f"However, here is the '{agent_name}' agent definition for reference. "
                f"You can adapt this for your platform."
            ),
            "agent_content": agent_content,
            "adaptation_guidance": (
                "To use this agent definition on other platforms:\n"
                "1. Extract the role and cognitive function from the content above\n"
                "2. Add the role description to your system prompt or agent configuration\n"
                "3. Adapt tool references to match your platform's available tools\n"
                "4. Follow the protocol and output format sections for structured behavior"
            ),
            "governance_guidance": (
                "To use governance effectively:\n"
                "1. Call evaluate_governance() before any action not on the skip list\n"
                "2. Call query_governance() when you need principles to inform decisions\n"
                "3. Follow the assessment (PROCEED/MODIFY/ESCALATE)\n"
                "4. S-Series principles have veto authority"
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Get template path
    template_path = _get_agent_template_path(agent_name)
    if not template_path:
        error = ErrorResponse(
            error_code="TEMPLATE_NOT_FOUND",
            message=f"Subagent template not found: {agent_name}",
            suggestions=["Ensure the MCP server is properly installed"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Read template content
    template_content = template_path.read_text()

    # Verify template integrity
    hash_valid, actual_hash = _verify_template_hash(template_content, agent_name)
    expected_hash = AGENT_TEMPLATE_HASHES.get(agent_name)

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope, project_path)

    # Check if already installed and if content differs
    # M2 FIX: Warn user before overwriting existing file with different content
    already_installed = install_path.is_file()
    content_differs = False
    existing_content = None
    if already_installed:
        try:
            existing_content = install_path.read_text()
            content_differs = existing_content != template_content
        except (OSError, PermissionError):
            # Can't read existing file - treat as content differs for safety
            content_differs = True

    # Handle manual instructions request
    if show_manual:
        # Build clear, actionable instructions
        instructions = f"""To install the {agent_name} subagent manually:

1. Create the agents directory:
   mkdir -p {install_path.parent}

2. Save the content (from the "content" field below) to:
   {install_path}

3. Restart Claude Code to activate the subagent

**One-liner alternative** (copy/paste the content field into this command):
```bash
mkdir -p {install_path.parent} && cat > {install_path} << 'EOF'
[paste content here]
EOF
```"""

        output = {
            "status": "manual_instructions",
            "agent_name": agent_name,
            "install_path": str(install_path),
            "instructions": instructions,
            "content": template_content,
            "note": "The 'content' field above contains the exact file contents to save.",
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Handle confirmation flow
    if not confirmed:
        # Return preview with explanation
        scope_desc = (
            "this project" if scope == "project" else "all your projects (user-level)"
        )
        status = "update" if already_installed else "install"

        # M2 FIX: Build warning if overwriting with different content
        overwrite_warning = None
        if content_differs:
            overwrite_warning = (
                "WARNING: Existing file has different content and will be overwritten. "
                "Use show_manual=true to see new content before installing."
            )

        output = {
            "status": "preview",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "already_installed": already_installed,
            "content_differs": content_differs,  # M2 FIX: Expose content diff status
            "integrity": {
                "hash_verified": hash_valid,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
            },
            "explanation": SUBAGENT_EXPLANATION.strip(),
            "action_summary": (
                f"Will {status} '{agent_name}' subagent for {scope_desc}.\n\n"
                f"File: {install_path}\n\n"
                f"This subagent will:\n"
                f"{AGENT_METADATA.get(agent_name, {}).get('action_summary', 'Provide specialized agent behavior')}"
            ),
            "options": {
                "install": "Call install_agent with confirmed=true to install",
                "manual": "Call install_agent with show_manual=true for manual instructions",
                "cancel": "Take no action to cancel",
            },
        }
        if overwrite_warning:
            output["warning"] = overwrite_warning  # M2 FIX: Add warning to output
        if not hash_valid:
            output["security_warning"] = (
                "SECURITY WARNING: Template hash does not match known-good value!\n"
                "The agent template may have been modified. This could indicate:\n"
                "1. An intentional update (maintainer should update AGENT_TEMPLATE_HASHES)\n"
                "2. A supply chain attack (template was tampered with)\n\n"
                "Use show_manual=true to review the content before installing."
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify install_path above is correct before confirming."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed: perform installation
    try:
        # Create directory if needed
        install_path.parent.mkdir(parents=True, exist_ok=True)

        # Write subagent file
        install_path.write_text(template_content)

        output = {
            "status": "installed",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "integrity": {
                "hash_verified": hash_valid,
                "installed_hash": actual_hash,
            },
            "message": (
                f"Successfully installed '{agent_name}' subagent.\n\n"
                + AGENT_METADATA.get(agent_name, {}).get(
                    "activation_message",
                    f"The '{agent_name}' subagent will activate on your next Claude Code session.\n\n"
                    f"To remove: Use uninstall_agent(agent_name='{agent_name}')",
                )
            ),
        }
        if not hash_valid:
            output["security_warning"] = (
                "Installed with UNVERIFIED hash. Review the installed content."
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Used CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "If the install landed in the wrong project, re-run with "
                "project_path='/path/to/your/project'."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except PermissionError:
        output = {
            "status": "error",
            "error": "Permission denied",
            "install_path": str(install_path),
            "suggestion": (
                "Cannot write to the installation path. Try:\n"
                "1. Check directory permissions\n"
                "2. Use show_manual=true to get the content for manual installation\n"
                "3. Try scope='user' to install in your home directory"
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as e:
        error = ErrorResponse(
            error_code="INSTALL_FAILED",
            message=f"Failed to install subagent: {_sanitize_error_message(e)}",
            suggestions=["Use show_manual=true for manual installation instructions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_uninstall_agent(args: dict) -> list[TextContent]:
    """Handle uninstall_agent tool.

    Removes a previously installed governance agent.
    """
    agent_name = args.get("agent_name", "")
    scope = args.get("scope", "project")
    confirmed = args.get("confirmed", False)

    # Validate agent name
    if agent_name not in AVAILABLE_AGENTS:
        error = ErrorResponse(
            error_code="INVALID_AGENT",
            message=f"Unknown agent: {agent_name}",
            suggestions=[f"Available agents: {', '.join(AVAILABLE_AGENTS)}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Resolve project path for scope="project"
    project_path = None
    used_cwd_fallback = False
    if scope == "project":
        project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
        if project_path is None:
            error = ErrorResponse(
                error_code="INVALID_PROJECT_PATH",
                message="Specified project_path does not exist or is outside allowed scope",
                suggestions=[
                    "Provide an absolute path to an existing directory within your home directory"
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope, project_path)

    # Check if installed
    if not install_path.is_file():
        output = {
            "status": "not_installed",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "message": f"Subagent '{agent_name}' is not installed at {install_path}",
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Handle confirmation flow
    if not confirmed:
        output = {
            "status": "confirm_uninstall",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "warning": (
                f"This will remove the '{agent_name}' subagent "
                f"({AGENT_METADATA.get(agent_name, {}).get('short_description', 'specialized agent')}).\n\n"
                "After removal:\n"
                f"- The '{agent_name}' behavior will no longer be automatically available\n"
                "- You can reinstall at any time\n"
                "- SERVER_INSTRUCTIONS will still provide governance guidance\n\n"
                "To confirm: Call uninstall_agent with confirmed=true"
            ),
        }
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify install_path above is correct before confirming."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed: perform uninstallation
    try:
        install_path.unlink()

        output = {
            "status": "uninstalled",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "message": (
                f"Successfully removed '{agent_name}' subagent.\n\n"
                "The subagent will no longer be active in new Claude Code sessions.\n"
                "Governance tools are still available via the MCP server.\n\n"
                f"To reinstall: Use install_agent(agent_name='{agent_name}')"
            ),
        }
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Used CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "If the uninstall targeted the wrong project, verify manually."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as e:
        error = ErrorResponse(
            error_code="UNINSTALL_FAILED",
            message=f"Failed to uninstall subagent: {_sanitize_error_message(e)}",
            suggestions=["Manually delete the file", f"Path: {install_path}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_log_governance_reasoning(args: dict) -> list[TextContent]:
    """Handle log_governance_reasoning tool (Audit Trail Enhancement).

    Records AI's governance reasoning trace linked to an audit entry.
    Part of Governance Reasoning Externalization feature.
    Enables observability and audit trail completeness.
    """
    audit_id = args.get("audit_id", "")
    reasoning = args.get("reasoning", [])
    final_decision = args.get("final_decision", "")
    modifications_applied = args.get("modifications_applied", [])

    # Validate required fields
    if not audit_id:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="audit_id is required",
            suggestions=["Provide the audit_id from evaluate_governance response"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if not reasoning:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="reasoning array is required and cannot be empty",
            suggestions=[
                "Provide at least one reasoning entry",
                "Each entry needs: principle_id, status, reasoning",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if not final_decision:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="final_decision is required",
            suggestions=["Provide PROCEED, PROCEED_WITH_MODIFICATIONS, or ESCALATE"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate audit_id exists in audit log
    audit_log = get_audit_log()
    matching_audit = None
    for entry in audit_log:
        if entry.audit_id == audit_id:
            matching_audit = entry
            break

    if not matching_audit:
        error = ErrorResponse(
            error_code="AUDIT_NOT_FOUND",
            message=f"No audit entry found with id: {audit_id}",
            suggestions=[
                "Ensure evaluate_governance was called first",
                "Use the audit_id from the evaluate_governance response",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Build reasoning entries with sanitization
    reasoning_entries = []
    for entry in reasoning[:20]:  # Limit to 20 entries
        reasoning_entries.append(
            ReasoningEntry(
                principle_id=str(entry.get("principle_id", ""))[:100],
                status=str(entry.get("status", "COMPLIES"))[:30],
                reasoning=_sanitize_for_logging(str(entry.get("reasoning", "")))[:1000],
            )
        )

    # Create reasoning log entry
    reasoning_log_entry = GovernanceReasoningLog(
        audit_id=audit_id,
        reasoning_entries=reasoning_entries,
        final_decision=final_decision,
        modifications_applied=[
            _sanitize_for_logging(str(m))[:500] for m in modifications_applied[:10]
        ],
    )

    # Log asynchronously
    await log_reasoning_async(reasoning_log_entry)

    # Return success response
    output = {
        "status": "logged",
        "audit_id": audit_id,
        "entries_logged": len(reasoning_entries),
        "final_decision": final_decision,
        "modifications_count": len(modifications_applied),
        "message": "Governance reasoning trace recorded successfully.",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_scaffold_project(args: dict) -> list[TextContent]:
    """Handle scaffold_project tool — initialize governance memory files for a new project.

    Two-step flow: preview (no confirmed) → create (confirmed=true).
    Follows install_agent pattern for safety and UX consistency.
    """
    show_manual = args.get("show_manual", False)
    project_type = args.get("project_type", "code")
    kit_tier = args.get("kit_tier", "core")
    confirmed = args.get("confirmed", False)

    # Resolve caller's project path (not server CWD)
    project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
    if project_path is None and not show_manual:
        error = ErrorResponse(
            error_code="INVALID_PROJECT_PATH",
            message="Specified project_path does not exist or is outside allowed scope",
            suggestions=[
                "Provide an absolute path to an existing directory within your home directory",
                "Use show_manual=true to get file contents for manual creation (recommended for Cowork/sandboxed environments)",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    project_name = str(
        args.get("project_name", "")
        or (project_path.name if project_path else "my-project")
    ).strip()[:100]
    if not project_name:
        project_name = project_path.name if project_path else "my-project"
    # Escape curly braces to prevent str.format() injection
    safe_project_name = project_name.replace("{", "{{").replace("}", "}}")

    # Validate parameters
    if project_type not in ("code", "document"):
        error = ErrorResponse(
            error_code="INVALID_PROJECT_TYPE",
            message=f"Invalid project_type: '{project_type}'. Must be 'code' or 'document'.",
            suggestions=[
                "Use project_type='code' for repositories",
                "Use project_type='document' for folder-based projects",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if kit_tier not in ("core", "standard"):
        error = ErrorResponse(
            error_code="INVALID_KIT_TIER",
            message=f"Invalid kit_tier: '{kit_tier}'. Must be 'core' or 'standard'.",
            suggestions=[
                "Use kit_tier='core' for 4 essential files",
                "Use kit_tier='standard' for 6 files (adds CLAUDE.md + checklist)",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # show_manual mode — return file contents for manual creation
    # Used in sandboxed environments (Cowork) where the MCP server
    # cannot write to the project directory.
    if show_manual:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        files = list(SCAFFOLD_CORE_FILES.get(project_type, []))
        if kit_tier == "standard":
            files.extend(SCAFFOLD_STANDARD_EXTRAS.get(project_type, []))

        file_contents = []
        for relative_path, template in files:
            content = template.format(project_name=safe_project_name, date=date_str)
            file_contents.append({"path": relative_path, "content": content})

        output = {
            "status": "manual_instructions",
            "project_name": project_name,
            "project_type": project_type,
            "kit_tier": kit_tier,
            "instructions": (
                "Create these files in your project directory. "
                "For document projects, all files go inside _ai-context/.\n\n"
                "The 'files' array below contains the path and full content "
                "for each file. Create them using your file-writing tools."
            ),
            "files": file_contents,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Build file manifest
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cwd = project_path.resolve()

    files = list(SCAFFOLD_CORE_FILES.get(project_type, []))
    if kit_tier == "standard":
        files.extend(SCAFFOLD_STANDARD_EXTRAS.get(project_type, []))

    manifest = []
    for relative_path, template in files:
        full_path = (cwd / relative_path).resolve()

        # Path validation — reject traversal attempts
        if not full_path.is_relative_to(cwd):
            logger.warning("Path traversal rejected: %s", relative_path)
            continue

        content = template.format(project_name=safe_project_name, date=date_str)
        exists = full_path.is_file()
        if exists:
            logger.info(
                "scaffold_project: file exists at %s (parent exists: %s, parent is_dir: %s)",
                full_path,
                full_path.parent.exists(),
                full_path.parent.is_dir(),
            )

        manifest.append(
            {
                "relative_path": relative_path,
                "full_path": str(full_path),
                "exists": exists,
                "action": "skip (already exists)" if exists else "create",
                "content_preview": content[:200] + "..."
                if len(content) > 200
                else content,
                "content": content,
            }
        )

    files_to_create = [f for f in manifest if not f["exists"]]
    files_to_skip = [f for f in manifest if f["exists"]]

    # Preview mode
    if not confirmed:
        output = {
            "status": "preview",
            "project_name": project_name,
            "project_type": project_type,
            "kit_tier": kit_tier,
            "project_root": str(cwd),
            "files": [
                {
                    "path": f["relative_path"],
                    "resolved_path": f["full_path"],
                    "action": f["action"],
                    "preview": f["content_preview"],
                }
                for f in manifest
            ],
            "files_to_create": len(files_to_create),
            "files_to_skip": len(files_to_skip),
            "options": {
                "create": "Call scaffold_project with confirmed=true to create files",
                "cancel": "Take no action to cancel",
            },
        }
        if not files_to_create:
            output["warning"] = (
                "All governance files already exist. No files will be created."
            )
        else:
            output["next_steps"] = (
                "After scaffolding:\n"
                "1. Fill in [bracketed placeholders] in the created files\n"
                "2. Run install_agent(agent_name='orchestrator') for governance orchestration\n"
                "3. Start working — the AI will read these files at session start"
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify file paths above are correct before confirming."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed mode — create files
    created = []
    skipped = []

    try:
        for f in manifest:
            full_path = Path(f["full_path"])

            # Re-verify existence at write time (don't trust cached manifest)
            if full_path.is_file():
                skipped.append(
                    {
                        "path": f["relative_path"],
                        "resolved_path": f["full_path"],
                        "reason": "already exists",
                    }
                )
                continue

            # Symlink check before write
            if full_path.exists() and full_path.is_symlink():
                skipped.append(
                    {
                        "path": f["relative_path"],
                        "resolved_path": f["full_path"],
                        "reason": "symlink detected",
                    }
                )
                continue

            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f["content"])
            created.append(
                {
                    "path": f["relative_path"],
                    "resolved_path": f["full_path"],
                }
            )

    except PermissionError as e:
        error = ErrorResponse(
            error_code="PERMISSION_ERROR",
            message=f"Cannot write files: {_sanitize_error_message(e)}. Files created before error: {created}",
            suggestions=["Check directory permissions", "Try a different directory"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except Exception as e:
        error = ErrorResponse(
            error_code="SCAFFOLD_ERROR",
            message=f"{_sanitize_error_message(e)}. Files created before error: {created}",
            suggestions=["Check file system permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    output = {
        "status": "scaffolded",
        "project_name": project_name,
        "project_type": project_type,
        "kit_tier": kit_tier,
        "project_root": str(cwd),
        "files_created": created,
        "files_skipped": skipped,
        "message": f"Successfully initialized governance memory for '{project_name}'.",
        "next_steps": (
            "Your project is set up! Next:\n"
            "1. Fill in [bracketed placeholders] in the created files\n"
            "2. Run install_agent(agent_name='orchestrator') to add governance orchestration\n"
            "3. Begin work — the AI will read these files at session start"
        ),
    }
    if used_cwd_fallback:
        output["cwd_fallback_warning"] = (
            "Used CWD as project directory (no MCP roots, project_path argument, "
            "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
            "If files were created in the wrong project, re-run with "
            "project_path='/path/to/your/project'."
        )
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _escape_yaml_value(value: str) -> str:
    """Escape a string for safe inclusion in double-quoted YAML values.

    Handles quotes, newlines, and other YAML-special characters.
    Applied uniformly to all user-supplied fields in YAML frontmatter.
    """
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", "")
    )


async def _handle_capture_reference(args: dict) -> list[TextContent]:
    """Handle capture_reference tool — create a Reference Library entry file.

    Creates a markdown file with YAML frontmatter in reference-library/{domain}/.
    """
    # Extract and validate required fields
    entry_id = str(args.get("id", ""))[:100].strip()
    title = str(args.get("title", ""))[:200].strip()
    domain = str(args.get("domain", ""))[:50].strip()
    tags = args.get("tags", [])
    entry_type = args.get("entry_type", "direct")
    artifact = str(args.get("artifact", ""))[:10000]

    if not entry_id or not title or not domain or not tags or not artifact:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELDS",
            message="Required fields: id, title, domain, tags, entry_type, artifact",
            suggestions=["Provide all required fields"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate domain format (safe directory name)
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", domain):
        error = ErrorResponse(
            error_code="INVALID_DOMAIN",
            message=f"Domain must be lowercase alphanumeric with hyphens: '{domain[:50]}'",
            suggestions=["Example: ai-coding, kmpd, storytelling"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate ID format
    if not re.match(r"^ref-[a-z0-9][a-z0-9-]*$", entry_id):
        error = ErrorResponse(
            error_code="INVALID_ID_FORMAT",
            message=f"ID must start with 'ref-' and contain only lowercase letters, numbers, hyphens: '{entry_id[:50]}'",
            suggestions=["Example: ref-ai-coding-my-pattern"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if entry_type not in ("direct", "reference"):
        error = ErrorResponse(
            error_code="INVALID_ENTRY_TYPE",
            message=f"entry_type must be 'direct' or 'reference': '{entry_type[:20]}'",
            suggestions=[
                "Use 'direct' for artifacts in the library",
                "Use 'reference' for external pointers",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Build file path — use settings-derived path (same as extractor),
    # not CWD or _find_project_root() directly. Settings respects
    # AI_GOVERNANCE_DOCUMENTS_PATH env var overrides.
    settings = _settings or load_settings()
    project_root = settings.documents_path.parent.resolve()
    ref_dir = project_root / "reference-library" / domain
    file_path = (ref_dir / f"{entry_id}.md").resolve()

    # Path validation
    if not file_path.is_relative_to(project_root):
        error = ErrorResponse(
            error_code="PATH_TRAVERSAL",
            message="Invalid domain or ID — path traversal detected",
            suggestions=["Use simple domain names and IDs without path separators"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Check if file already exists
    if file_path.is_file():
        error = ErrorResponse(
            error_code="ENTRY_EXISTS",
            message=f"Reference entry already exists: {entry_id} at {file_path}",
            suggestions=["Use a different ID", "Edit the existing file directly"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Build YAML frontmatter
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = str(args.get("summary", ""))[:300]
    context = str(args.get("context", ""))[:2000]
    lessons = str(args.get("lessons", ""))[:2000]
    maturity = args.get("maturity", "seedling")
    external_url = str(args.get("external_url", ""))[:500]
    external_author = str(args.get("external_author", ""))[:100]

    # Escape all user-supplied fields uniformly for YAML safety
    safe_title = _escape_yaml_value(title)
    tags_yaml = ", ".join(f'"{_escape_yaml_value(t[:50])}"' for t in tags[:10])

    lines = [
        "---",
        f"id: {entry_id}",
        f'title: "{safe_title}"',
        f"domain: {domain}",
        f"tags: [{tags_yaml}]",
        "status: current",
        f"entry_type: {entry_type}",
    ]
    if summary:
        lines.append(f'summary: "{_escape_yaml_value(summary)}"')
    lines.extend(
        [
            f"created: {date_str}",
            f"last_verified: {date_str}",
            f"maturity: {maturity if maturity in ('seedling', 'budding', 'evergreen') else 'seedling'}",
            "decay_class: framework",
            'source: "Captured via capture_reference tool"',
        ]
    )
    if entry_type == "reference" and external_url:
        lines.append(f'external_url: "{_escape_yaml_value(external_url)}"')
        if external_author:
            lines.append(f'external_author: "{_escape_yaml_value(external_author)}"')
        lines.append(f"accessed_date: {date_str}")
    lines.append("---")
    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(context if context else "[When to use this and why it exists]")
    lines.append("")
    lines.append("## Artifact")
    lines.append("")
    lines.append(artifact)
    lines.append("")
    lines.append("## Lessons Learned")
    lines.append("")
    lines.append(lessons if lessons else "[What worked, what didn't, edge cases]")
    lines.append("")
    lines.append("## Cross-References")
    lines.append("")
    lines.append("- Principles: [relevant principle IDs]")
    lines.append("- Methods: [relevant method section refs]")
    lines.append("- See also: [related entry IDs]")
    lines.append("")

    content = "\n".join(lines)

    # Create file
    try:
        ref_dir.mkdir(parents=True, exist_ok=True)
        if file_path.is_symlink():
            error = ErrorResponse(
                error_code="SYMLINK_DETECTED",
                message="Target path is a symlink — refusing to write",
                suggestions=["Remove the symlink and try again"],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
        file_path.write_text(content)
        # Post-write verification — confirm the file actually landed on disk
        if not file_path.is_file():
            error = ErrorResponse(
                error_code="WRITE_VERIFICATION_FAILED",
                message=f"File write appeared to succeed but file not found at: {file_path}",
                suggestions=[
                    "Check filesystem permissions",
                    "Check if path is on a read-only mount",
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except PermissionError as e:
        error = ErrorResponse(
            error_code="PERMISSION_ERROR",
            message=f"Cannot write file: {_sanitize_error_message(e)}",
            suggestions=["Check directory permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except Exception as e:
        error = ErrorResponse(
            error_code="CAPTURE_ERROR",
            message=_sanitize_error_message(e),
            suggestions=["Check file system permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    output = {
        "status": "captured",
        "entry_id": entry_id,
        "file_path": str(file_path.relative_to(project_root)),
        "absolute_path": str(file_path),
        "project_root": str(project_root),
        "domain": domain,
        "entry_type": entry_type,
        "maturity": maturity,
        "message": f"Reference entry '{title}' captured successfully.",
        "next_steps": (
            "Entry created. To make it searchable:\n"
            "1. Run `python -m ai_governance_mcp.extractor` to rebuild the index\n"
            "2. Verify with `query_governance` that the entry surfaces for relevant queries"
        ),
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _flush_all_logs() -> None:
    """Flush all log files to ensure data is persisted before exit.

    H3 FIX: Called before os._exit() to reduce data loss on shutdown.
    """
    global _settings
    if _settings:
        log_files = [
            "queries.jsonl",
            "feedback.jsonl",
            "governance_audit.jsonl",
            "governance_reasoning.jsonl",
        ]
        for log_name in log_files:
            log_file = _settings.logs_path / log_name
            try:
                if log_file.exists():
                    # Open and close with flush to ensure OS buffers are written
                    with open(log_file, "a") as f:
                        f.flush()
                        os.fsync(f.fileno())
            except Exception as e:
                logger.warning(f"Failed to flush {log_name}: {e}")


async def run_server():
    """Run the MCP server with graceful shutdown handling."""

    logger.info(f"Starting AI Governance MCP Server v{__version__}")

    # Initialize engine on startup
    get_engine()

    # Log resolved paths to help users verify configuration
    if _settings:
        logger.info(f"Documents path: {_settings.documents_path}")
        logger.info(f"Index path: {_settings.index_path}")
        index_file = _settings.index_path / "global_index.json"
        if index_file.exists():
            logger.info(f"Index loaded: {index_file}")
        else:
            logger.warning(f"Index NOT FOUND: {index_file} - run extractor first")

    def force_exit(signum, frame):
        """Force exit on signal - stdio streams can't be gracefully interrupted.

        Only async-signal-safe operations here. Do NOT call logger (uses locks)
        or _flush_all_logs (opens files) — either can deadlock if the signal
        arrives while a lock is held. The finally block handles cleanup for
        normal exits. Matches context_engine/server.py signal handler pattern.
        """
        os._exit(0)

    # Register signal handlers for immediate exit
    # Note: MCP stdio servers can't gracefully interrupt blocking I/O,
    # so we force exit when the parent process signals shutdown
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, force_exit)
        signal.signal(signal.SIGINT, force_exit)

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # H3 FIX: Flush logs before exit to prevent data loss
        _flush_all_logs()
        # Force exit to prevent sentence-transformers threads from keeping process alive
        logger.info("Server shutdown complete, forcing exit...")
        os._exit(0)


def main():
    """Entry point."""
    # Handle --test mode for quick testing
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        query = (
            " ".join(sys.argv[2:])
            if len(sys.argv) > 2
            else "how do I handle incomplete specs"
        )
        engine = get_engine()
        result = engine.retrieve(query)
        print(_format_retrieval_result(result))
        return

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
