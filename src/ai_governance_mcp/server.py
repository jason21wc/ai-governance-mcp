"""MCP Server for AI Governance document retrieval.

Per specification v4: FastMCP server with 10 tools for hybrid retrieval.
"""

import asyncio
import json
import os
import re
import signal
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import Settings, ensure_directories, load_settings, setup_logging
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
    RelevantPrinciple,
    SSeriesCheck,
    VerificationResult,
    VerificationStatus,
)
from .retrieval import RetrievalEngine

logger = setup_logging()

# Global state
_settings: Settings | None = None
_engine: RetrievalEngine | None = None
_metrics: Metrics | None = None


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

    # Log files must be within project root, user home, or system temp directory
    # (covers default logs/ dir, user-configured paths, and test environments)
    project_root = Path(__file__).parent.parent.parent.resolve()
    home_dir = Path.home().resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()

    is_in_project = str(resolved).startswith(str(project_root))
    is_in_home = str(resolved).startswith(str(home_dir))
    is_in_temp = str(resolved).startswith(str(temp_dir))

    if not (is_in_project or is_in_home or is_in_temp):
        raise ValueError(
            f"Log path must be within project root, home, or temp directory: {resolved}"
        )


def _write_log_sync(log_file: Path, content: str) -> None:
    """Synchronous log write helper for use with asyncio.to_thread.

    H2 FIX: Isolated sync function enables non-blocking async wrapper.
    M1 FIX: Validates path before writing.
    """
    _validate_log_path(log_file)  # M1 FIX: Path containment check
    with open(log_file, "a") as f:
        f.write(content)
        f.flush()  # H3 FIX: Explicit flush reduces data loss on shutdown


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

# H4 FIX: Rate limiting configuration (token bucket algorithm)
RATE_LIMIT_TOKENS = 100  # Maximum tokens (requests) in bucket
RATE_LIMIT_REFILL_RATE = 10  # Tokens added per second
_rate_limit_tokens = RATE_LIMIT_TOKENS
_rate_limit_last_refill = time.time()

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

    Returns:
        True if request is allowed, False if rate limited.
    """
    global _rate_limit_tokens, _rate_limit_last_refill

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
    message = re.sub(r"\b\w+(?:\.\w+){2,}\b", "[module]", message)

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
    return _audit_log


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
    logger.debug(f"Logged reasoning for audit {entry.audit_id}")

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


def get_reasoning_log() -> deque[GovernanceReasoningLog]:
    """Get the in-memory reasoning log for inspection."""
    return _reasoning_log


# Server instructions injected into AI context at MCP initialization.
# Optimized 2026-01-01: Added Required/Forbidden actions, model-specific guidance.
# Per meta-operational-constraint-based-prompting: explicit constraints reduce ambiguity.
# Per meta-method-instructions-content: includes Overview, When to Use, Hierarchy, Behaviors, Quick Start.
SERVER_INSTRUCTIONS = """
## AI Governance MCP Server

Semantic retrieval of AI governance principles and methods. Query before acting.

### Orchestrator Protocol (Default Behavior)

For significant actions, follow this protocol:

1. **Evaluate governance first**: Call `evaluate_governance(planned_action="your task")`
2. **Act on assessment**:
   - PROCEED: Continue with the task
   - PROCEED_WITH_MODIFICATIONS: Apply required changes, then continue
   - ESCALATE: STOP. Inform user. Wait for explicit approval.
3. **S-Series = Absolute Veto**: If S-Series triggers, you MUST escalate regardless of other factors

### Required Actions
1. **Evaluate before implementation** — Call `evaluate_governance(planned_action="...")` before writing code or making changes
2. **Query for guidance** — Call `query_governance("your concern")` when you need principles to inform decisions
3. **Cite influencing principles** — Reference principle IDs (e.g., `meta-core-context-engineering`) when they guide your approach
4. **Pause on uncertainty** — If requirements are unclear, ask the user before proceeding

### Hierarchy (Binding Order)
| Priority | Source | Scope |
|----------|--------|-------|
| 1 | S-Series (Safety) | Veto authority — overrides all other guidance |
| 2 | Constitution | Universal rules — always apply |
| 3 | Domain (ai-coding, multi-agent) | Context-specific — apply when detected |
| 4 | Methods | Procedural — workflows, patterns, templates |

### Forbidden Actions
- Do NOT proceed with significant actions without calling `evaluate_governance` first
- Do NOT ignore ESCALATE assessments — human approval required
- Do NOT make product/business/timeline decisions — escalate to user
- Do NOT ignore S-Series principles under any circumstances

### Anchor Bias Checkpoints (Part 7.10)

At milestone boundaries, apply the Anchor Bias Mitigation Protocol:

**Trigger Points:**
- End of planning phase (before implementation)
- Before significant implementation effort
- When encountering unexpected complexity/resistance
- At natural phase transitions

**Quick Protocol:**
1. **Reframe** — State the goal WITHOUT referencing current approach
2. **Generate** — Identify 2-3 alternative approaches from scratch
3. **Challenge** — "If we started fresh today, would we choose this approach?"
4. **Evaluate** — Compare using fresh criteria, document decision

**Signal to Watch:** Mounting complexity or repeated friction may indicate anchor bias — the frame may be wrong, not just the execution.

Query `query_governance("anchor bias re-evaluation")` for full protocol.

### AI Judgment Protocol (§4.6.1)

When `requires_ai_judgment=true` in the evaluate_governance response:

1. **Read principle content** — Each principle includes full text in the `content` field
2. **Analyze for conflicts** — Does the action conflict with any principle requirements?
3. **Determine outcome**:
   - No conflicts → Confirm PROCEED
   - Resolvable conflicts → PROCEED_WITH_MODIFICATIONS + list specific changes
   - (ESCALATE only comes from script via S-Series, never from AI judgment)
4. **Cite principle IDs** — Reference which principles informed your decision

When `requires_ai_judgment=false`: The script has made a definitive decision (S-Series ESCALATE or no principles found). Follow the assessment as-is.

### Governance Reasoning Protocol

After receiving an assessment from `evaluate_governance`, externalize your analysis:

**Action:** [Brief description of planned action]

**Principle Analysis:**
| Principle ID | Status | Reasoning |
|--------------|--------|-----------|
| principle-id | COMPLIES / NEEDS_MODIFICATION / VIOLATION | [Why this principle applies] |

**Decision:** [PROCEED / PROCEED_WITH_MODIFICATIONS / ESCALATE]
**Modifications Applied:** [List any modifications, or "None"]

After completing your analysis, call `log_governance_reasoning(audit_id, reasoning)` to record your trace.
This creates an auditable governance reasoning trail.

### Tools (11 Available)
| Tool | Purpose |
|------|---------|
| `evaluate_governance(planned_action)` | **Pre-action check** — returns assessment + principle content for AI judgment |
| `query_governance(query)` | Get relevant principles + methods |
| `verify_governance_compliance(action)` | **Post-action audit** — check if governance was consulted |
| `log_governance_reasoning(audit_id, reasoning)` | **Reasoning trace** — record per-principle analysis for audit trail |
| `get_principle(id)` | Full content of principle or method |
| `list_domains()` | Explore available domains |
| `get_domain_summary(domain)` | Details about a specific domain |
| `log_feedback(query, id, rating)` | **Improve retrieval** — rate principle relevance (1-5) |
| `get_metrics()` | Performance analytics |
| `install_agent(agent_name)` | Install Orchestrator subagent (Claude Code only) |
| `uninstall_agent(agent_name)` | Remove installed subagent |

### Feedback Collection
After receiving query results, use `log_feedback()` to rate relevance:
- **Rating 5**: Principle was exactly what was needed
- **Rating 4**: Principle was helpful
- **Rating 3**: Principle was somewhat relevant
- **Rating 2**: Principle was marginally useful
- **Rating 1**: Principle was not relevant

High-rated principles get boosted in future queries. Your feedback directly improves retrieval quality.

### Claude Code Users
Run `install_agent(agent_name="orchestrator")` to install the Orchestrator subagent.
This enables structural governance enforcement with restricted tool access.

### Model-Specific Guidance

**Claude (Opus, Sonnet)**: Use extended thinking for governance analysis. Structure outputs with tags.

**GPT-4.1 / o1 / o3**: Sandwich method — query at start, verify compliance before finalizing. Literal instruction following.

**Gemini 2.5**: Use hierarchical headers for principle citations. Activate Deep Think for complex ethical analysis.

**Llama / Mistral**: Keep governance context in system position. Repeat S-Series constraints at decision points.

**All Models**: Evaluate BEFORE acting, not after. Cite principle IDs explicitly. When unsure — evaluate. False positives are cheap; governance violations are expensive.
""".strip()

# Compact reminder appended to every tool response for consistent governance reinforcement.
# Optimized 2026-01-01: Self-check question format, reduced tokens, removed duplicate hierarchy.
# Design: Self-check prompt triggers reflection; ~35 tokens.
# Per Learning Log 2025-12-31: Passive reminders need explicit action triggers.
GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Did you `query_governance()` before this action? Cite influencing principle IDs. S-Series = veto authority."""

# Subagent installation explanation for users
# Per Phase 2B design: robust explanation for both experts and beginners
SUBAGENT_EXPLANATION = """
## AI Governance Subagent Installation

### What is a Subagent?

A subagent is a specialized configuration that guides how your AI assistant approaches tasks.
Think of it as giving your AI a specific "role" with clear responsibilities and boundaries —
like hiring a specialist who follows particular protocols.

### What Does the Orchestrator Do?

The Orchestrator ensures your AI checks governance principles BEFORE taking significant actions.
Instead of diving straight into tasks, it:

1. **Evaluates** what you're asking against governance principles
2. **Identifies** any safety concerns or required modifications
3. **Proceeds** only when governance requirements are satisfied
4. **Escalates** to you when human judgment is needed

### Why Is This Important?

Without structured guidance, AI assistants can:
- Skip validation steps in complex workflows
- Make assumptions instead of asking for clarification
- Apply inconsistent approaches across similar problems
- Miss critical safety considerations

The Orchestrator makes governance automatic, not optional — ensuring consistent,
high-quality AI collaboration every time.

### What Will Be Installed?

A single markdown file (.claude/agents/orchestrator.md) containing:
- Role definition and responsibilities
- Tool access permissions (governance tools + read operations)
- Protocol for handling different governance assessments

This file stays in your project. You can review, modify, or remove it at any time.
It does not send data anywhere — it only configures how Claude Code behaves when
working in this project.
"""

# Available agents for installation
AVAILABLE_AGENTS = {"orchestrator"}


def _detect_claude_code_environment() -> bool:
    """Detect if we're running in a Claude Code environment.

    Checks for indicators that suggest Claude Code is the client:
    1. Presence of .claude/ directory in current working directory
    2. Presence of CLAUDE.md file
    3. Environment variable set by Claude Code

    Returns True if Claude Code environment is detected.
    """
    cwd = Path.cwd()

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


def _get_agent_install_path(agent_name: str, scope: str = "project") -> Path:
    """Get the installation path for an agent.

    Args:
        agent_name: Name of the agent (e.g., 'orchestrator')
        scope: 'project' for .claude/agents/ or 'user' for ~/.claude/agents/

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
        base_path = Path.cwd() / ".claude" / "agents"

    # C2 FIX: Path containment check prevents path traversal attacks
    final_path = (base_path / f"{agent_name}.md").resolve()
    if not str(final_path).startswith(str(base_path.resolve())):
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
                        "description": "Optional: Force specific domain (ai-coding, multi-agent)",
                        "maxLength": 50,  # M5 FIX
                        "enum": ["constitution", "ai-coding", "multi-agent"],
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
                "IDs follow pattern: meta-C1, coding-C1, multi-A1, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "principle_id": {
                        "type": "string",
                        "description": "The principle ID (e.g., 'meta-C1', 'coding-Q2')",
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
                        "description": "Domain name (constitution, ai-coding, multi-agent)",
                        "enum": ["constitution", "ai-coding", "multi-agent"],  # M5 FIX
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
                "Returns compliance assessment with PROCEED, PROCEED_WITH_MODIFICATIONS, or ESCALATE. "
                "S-Series (safety) principles have veto authority - will force ESCALATE if triggered. "
                "Use this to validate actions before implementing them."
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
                "Available agents: orchestrator."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of subagent to install (e.g., 'orchestrator')",
                        "enum": ["orchestrator"],
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
                        "enum": ["orchestrator"],
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
        else:
            result = [TextContent(type="text", text=f"Unknown tool: {name}")]

        return _append_governance_reminder(result)

    except Exception as e:
        logger.error(f"Tool error: {e}")
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

    result = engine.retrieve(
        query=query,
        domain=args.get("domain"),
        include_constitution=args.get("include_constitution", True),
        include_methods=args.get("include_methods", True),
        max_results=args.get("max_results"),
    )

    # Update metrics
    metrics = get_metrics()
    metrics.total_queries += 1
    metrics.avg_retrieval_time_ms = (
        metrics.avg_retrieval_time_ms * (metrics.total_queries - 1)
        + result.retrieval_time_ms
    ) / metrics.total_queries
    if result.s_series_triggered:
        metrics.s_series_trigger_count += 1

    for domain in result.domains_detected:
        metrics.domain_query_counts[domain] = (
            metrics.domain_query_counts.get(domain, 0) + 1
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

    # Update confidence distribution
    for sp in result.constitution_principles + result.domain_principles:
        level = sp.confidence.value
        metrics.confidence_distribution[level] = (
            metrics.confidence_distribution.get(level, 0) + 1
        )

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
            "Check ID format: meta-C1, coding-C1, multi-A1",
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
        session_id=args.get("session_id"),
    )

    log_feedback_entry(feedback)

    # Update metrics
    metrics = get_metrics()
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
S_SERIES_KEYWORDS = {
    "delete",
    "remove",
    "drop",
    "destroy",
    "credential",
    "password",
    "secret",
    "api key",
    "token",
    "private key",
    "security",
    "authentication",
    "authorization",
    "permission",
    "external api",
    "production",
    "deploy",
    "database",
    "user data",
    "personal data",
    "pii",
    "sensitive",
    "confidential",
    "irreversible",
    "destructive",
}


def _detect_safety_concerns(action: str) -> list[str]:
    """Detect potential safety concerns from action description.

    Per meta-quality-verification-mechanisms-before-action:
    Actively check for safety keywords that may require S-Series review.
    """
    action_lower = action.lower()
    concerns = []

    for keyword in S_SERIES_KEYWORDS:
        if keyword in action_lower:
            concerns.append(f"Action mentions '{keyword}' - may require safety review")

    return concerns


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

    # S-Series keyword detection (dual-path checking)
    safety_concerns = _detect_safety_concerns(planned_action)
    if context:
        safety_concerns.extend(_detect_safety_concerns(context))

    # Build S-Series check result
    s_series_triggered = len(s_series_principles) > 0 or len(safety_concerns) > 0
    s_series_check = SSeriesCheck(
        triggered=s_series_triggered,
        principles=s_series_principles,
        safety_concerns=safety_concerns,
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
        rationale = (
            "S-Series (safety) principles triggered. "
            "Human review required before proceeding. "
            f"Triggered by: {', '.join(s_series_principles + safety_concerns)}"
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

    # Record governance overhead metrics
    governance_time_ms = (time.time() - governance_start_time) * 1000
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
                "All significant actions should be preceded by evaluate_governance()."
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

    # Check if Claude Code environment
    is_claude = _detect_claude_code_environment()

    if not is_claude:
        # Non-Claude platform: governance is via SERVER_INSTRUCTIONS
        output = {
            "status": "not_applicable",
            "platform": "non-claude",
            "message": (
                "Subagent installation is only needed for Claude Code. "
                "Your platform already receives governance guidance via server instructions. "
                "The Orchestrator protocol is active through the Required Actions and "
                "Forbidden Actions in the server instructions you received on connection."
            ),
            "guidance": (
                "To use governance effectively:\n"
                "1. Call query_governance() before significant actions\n"
                "2. Call evaluate_governance() to validate planned actions\n"
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

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope)

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
            "explanation": SUBAGENT_EXPLANATION.strip(),
            "action_summary": (
                f"Will {status} '{agent_name}' subagent for {scope_desc}.\n\n"
                f"File: {install_path}\n\n"
                "This subagent will:\n"
                "- Ensure evaluate_governance() is called before significant actions\n"
                "- Have restricted tools (read + governance only, no edit/write/bash)\n"
                "- Escalate to you when S-Series (safety) principles trigger\n"
            ),
            "options": {
                "install": "Call install_agent with confirmed=true to install",
                "manual": "Call install_agent with show_manual=true for manual instructions",
                "cancel": "Take no action to cancel",
            },
        }
        if overwrite_warning:
            output["warning"] = overwrite_warning  # M2 FIX: Add warning to output
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
            "message": (
                f"Successfully installed '{agent_name}' subagent.\n\n"
                "The Orchestrator subagent will activate on your next Claude Code session.\n"
                "It will ensure governance is checked before significant actions.\n\n"
                "To verify: Look for 'orchestrator' in the agents list when you start Claude Code.\n"
                "To remove: Use uninstall_agent(agent_name='orchestrator')"
            ),
        }
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
            message=f"Failed to install subagent: {str(e)}",
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

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope)

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
                f"This will remove the '{agent_name}' subagent.\n\n"
                "After removal:\n"
                "- Governance checks will no longer be automatically enforced\n"
                "- You'll need to manually call governance tools\n"
                "- SERVER_INSTRUCTIONS will still provide guidance\n\n"
                "To confirm: Call uninstall_agent with confirmed=true"
            ),
        }
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
                "To reinstall: Use install_agent(agent_name='orchestrator')"
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as e:
        error = ErrorResponse(
            error_code="UNINSTALL_FAILED",
            message=f"Failed to uninstall subagent: {str(e)}",
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


def _flush_all_logs() -> None:
    """Flush all log files to ensure data is persisted before exit.

    H3 FIX: Called before os._exit() to reduce data loss on shutdown.
    """
    global _settings
    if _settings:
        log_files = ["queries.jsonl", "feedback.jsonl", "governance_audit.jsonl"]
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

    logger.info("Starting AI Governance MCP Server v4")

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
        """Force exit on signal - stdio streams can't be gracefully interrupted."""
        logger.info(f"Received signal {signum}, forcing exit...")
        # H3 FIX: Flush logs before exit to prevent data loss
        _flush_all_logs()
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
