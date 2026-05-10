"""MCP application core — server instance, tool dispatch, and entry point."""

import asyncio
import os
import signal
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .. import __version__
from ..models import ErrorResponse
from ._constants import (
    AVAILABLE_AGENTS,
    GOVERNANCE_REMINDER,
    MAX_QUERY_LENGTH,
    SERVER_INSTRUCTIONS,
)
from ._security import (
    _check_rate_limit,
    _sanitize_error_message,
    _validate_server_instructions,
)
from ._logging import _flush_all_logs
from ._state import get_engine
from . import _state
from .handlers.retrieval import (
    _format_retrieval_result,
    _handle_get_domain_summary,
    _handle_get_metrics,
    _handle_get_principle,
    _handle_list_domains,
    _handle_log_feedback,
    _handle_query_governance,
)
from .handlers.governance import (
    _handle_evaluate_governance,
    _handle_log_governance_reasoning,
    _handle_verify_governance,
)
from .handlers.agents import (
    _handle_install_agent,
    _handle_uninstall_agent,
)
from .handlers.scaffold import (
    _handle_capture_reference,
    _handle_scaffold_project,
)
from .handlers.analysis import (
    _handle_analyze_feedback_loop,
)
from ..config import setup_logging

logger = setup_logging()

_validate_server_instructions(SERVER_INSTRUCTIONS)


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
                "IDs follow pattern: meta-core-informational-readiness, coding-quality-testing, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "principle_id": {
                        "type": "string",
                        "description": "The principle ID (e.g., 'meta-core-informational-readiness', 'coding-quality-testing')",
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
                "Returns compliance assessment with PROCEED, REVIEW, or ESCALATE. "
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
                    "domain": {
                        "type": "string",
                        "description": (
                            "Optional. Active governance domain for the target project "
                            "(e.g., 'ai-coding', 'storytelling'). If provided AND the agent's "
                            "applicable_domains frontmatter excludes this domain, a WARN message "
                            "is included in the response (Phase-1: WARN + allow; installation "
                            "proceeds regardless). Omit to skip domain-fit checking."
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
                            "REVIEW",
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
                        "description": "Kit tier: 'core' (4 files) or 'standard' (9 files; core + CLAUDE.md + ARCHITECTURE.md + SPECIFICATION.md + .claude/skills/completion-sequence/checklist.md + BACKLOG.md, per title-10-ai-coding-cfr.md §1.5.2 + §1.5.5 tool overlay)",
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
        # Tool 14: Feedback loop analysis (precomputed reader)
        Tool(
            name="analyze_feedback_loop",
            description=(
                "Read precomputed feedback loop analysis of governance server logs. "
                "Shows effectiveness metrics (M-001/M-003/M-004), dead principles, "
                "false-positive patterns, retrieval gaps, and actionable recommendations. "
                "Run scripts/analyze_feedback_loop.py first to generate the analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": (
                            "Optional: return only this section "
                            "(e.g., 'effectiveness_metrics', 'dead_principles', "
                            "'false_positives', 'retrieval_gaps', 'actionable_recommendations')"
                        ),
                        "maxLength": 50,
                    },
                },
                "required": [],
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
        elif name == "analyze_feedback_loop":
            result = await _handle_analyze_feedback_loop(arguments)
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


async def run_server():
    """Run the MCP server with graceful shutdown handling."""

    logger.info(f"Starting AI Governance MCP Server v{__version__}")

    # Initialize engine on startup
    get_engine()

    # Log resolved paths to help users verify configuration
    if _state._settings:
        logger.info(f"Documents path: {_state._settings.documents_path}")
        logger.info(f"Index path: {_state._settings.index_path}")
        index_file = _state._settings.index_path / "global_index.json"
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
