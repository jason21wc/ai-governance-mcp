"""MCP Server for AI Governance document retrieval.

Per specification v4: FastMCP server with 6 tools for hybrid retrieval.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import Settings, ensure_directories, load_settings, setup_logging
from .models import ErrorResponse, Feedback, QueryLog, Metrics
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


def log_query(query_log: QueryLog) -> None:
    """Log query for analytics."""
    global _settings
    if _settings:
        log_file = _settings.logs_path / "queries.jsonl"
        with open(log_file, "a") as f:
            f.write(query_log.model_dump_json() + "\n")


def log_feedback_entry(feedback: Feedback) -> None:
    """Log feedback for future improvement."""
    global _settings
    if _settings:
        log_file = _settings.logs_path / "feedback.jsonl"
        with open(log_file, "a") as f:
            f.write(feedback.model_dump_json() + "\n")


# Server instructions injected into AI context at MCP initialization.
# Optimized 2026-01-01: Added Required/Forbidden actions, model-specific guidance.
# Per meta-operational-constraint-based-prompting: explicit constraints reduce ambiguity.
# Per meta-method-instructions-content: includes Overview, When to Use, Hierarchy, Behaviors, Quick Start.
SERVER_INSTRUCTIONS = """
## AI Governance MCP Server

Semantic retrieval of AI governance principles and methods. Query before acting.

### Required Actions
1. **Query before implementation** — Call `query_governance("your task")` before writing code or making changes
2. **Query before decisions** — Call before architectural, configuration, or significant choices
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
- Do NOT proceed with implementation without querying applicable principles
- Do NOT make product/business/timeline decisions — escalate to user
- Do NOT ignore S-Series principles under any circumstances

### Tools
| Tool | Purpose |
|------|---------|
| `query_governance(query)` | Get relevant principles + methods |
| `get_principle(id)` | Full content of principle or method |
| `list_domains()` | Explore available domains |
| `log_feedback(query, id, rating)` | Improve retrieval quality |

### Model-Specific Guidance

**Claude (Opus, Sonnet)**: Use extended thinking for governance analysis. Structure outputs with tags.

**GPT-4.1 / o1 / o3**: Sandwich method — query at start, verify compliance before finalizing. Literal instruction following.

**Gemini 2.5**: Use hierarchical headers for principle citations. Activate Deep Think for complex ethical analysis.

**Llama / Mistral**: Keep governance context in system position. Repeat S-Series constraints at decision points.

**All Models**: Query BEFORE acting, not after. Cite principle IDs explicitly. When unsure whether to query — query. False positives are cheap; governance violations are expensive.
""".strip()

# Compact reminder appended to every tool response for consistent governance reinforcement.
# Optimized 2026-01-01: Self-check question format, reduced tokens, removed duplicate hierarchy.
# Design: Self-check prompt triggers reflection; ~35 tokens.
# Per Learning Log 2025-12-31: Passive reminders need explicit action triggers.
GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Did you `query_governance()` before this action? Cite influencing principle IDs. S-Series = veto authority."""

# Create MCP server
server = Server("ai-governance-mcp", instructions=SERVER_INSTRUCTIONS)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools per spec v4."""
    return [
        # Tool 1: Main retrieval (T13)
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
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional: Force specific domain (ai-coding, multi-agent)",
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
                    },
                },
                "required": ["query"],
            },
        ),
        # Tool 2: Get specific principle (T14)
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
                    },
                },
                "required": ["domain"],
            },
        ),
        # Tool 5: Log feedback (T17)
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
                    },
                    "principle_id": {
                        "type": "string",
                        "description": "The principle being rated",
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
    ]


def _append_governance_reminder(result: list[TextContent]) -> list[TextContent]:
    """Append governance reminder to tool response for consistent reinforcement."""
    if result and result[0].text:
        result[0] = TextContent(type="text", text=result[0].text + GOVERNANCE_REMINDER)
    return result


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
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
        else:
            result = [TextContent(type="text", text=f"Unknown tool: {name}")]

        return _append_governance_reminder(result)

    except Exception as e:
        logger.error(f"Tool error: {e}")
        error = ErrorResponse(
            error_code="TOOL_ERROR",
            message=str(e),
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

    # Log query
    query_log = QueryLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        query=query,
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
    log_query(query_log)

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

    feedback = Feedback(
        query=query,
        principle_id=principle_id,
        rating=rating,
        comment=args.get("comment"),
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
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def run_server():
    """Run the MCP server with graceful shutdown handling."""
    import os

    logger.info("Starting AI Governance MCP Server v4")

    # Initialize engine on startup
    get_engine()

    def force_exit(signum, frame):
        """Force exit on signal - stdio streams can't be gracefully interrupted."""
        logger.info(f"Received signal {signum}, forcing exit...")
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
