"""MCP Server for AI Governance document retrieval.

Per specification v3: FastMCP 2.0 with 9 tools for governance retrieval.
Tools 1-5 are core tools implemented in this file.
"""

import json
import sys
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import ServerConfig, ensure_directories, load_config, setup_logging
from .extractor import DocumentExtractor
from .models import AuditLogEntry, ErrorResponse
from .retrieval import RetrievalEngine

logger = setup_logging()

# Global state
_config: ServerConfig | None = None
_engine: RetrievalEngine | None = None


def get_engine() -> RetrievalEngine:
    """Get or create the retrieval engine."""
    global _config, _engine
    if _engine is None:
        _config = load_config()
        ensure_directories(_config)
        _engine = RetrievalEngine(_config)
    return _engine


def log_audit(tool_name: str, query: str, domains: list[str], principles: list[str], s_series: bool):
    """Log tool invocation for audit purposes."""
    global _config
    if _config and _config.audit_log_enabled and _config.audit_log_path:
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            query=query,
            domains_detected=domains,
            principles_returned=principles,
            s_series_triggered=s_series,
        )
        with open(_config.audit_log_path, "a") as f:
            f.write(entry.model_dump_json() + "\n")


# Create MCP server
server = Server("ai-governance-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Tool 1: Main retrieval
        Tool(
            name="retrieve_governance",
            description=(
                "Retrieve relevant AI governance principles for a query. "
                "Auto-detects domain from query keywords. Returns scored principles "
                "from Constitution (always) and detected domains. Use this as the "
                "primary tool for getting governance guidance."
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
                        "description": "Include procedural methods in response (default: false)",
                        "default": False,
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
        # Tool 2: Domain detection
        Tool(
            name="detect_domain",
            description=(
                "Detect which governance domains apply to a query. "
                "Returns list of matching domains based on keywords and phrases. "
                "Use this to understand domain coverage before retrieval."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to analyze for domain detection",
                    },
                },
                "required": ["query"],
            },
        ),
        # Tool 3: Get specific principle
        Tool(
            name="get_principle",
            description=(
                "Get the full content of a specific governance principle by ID. "
                "Use after retrieve_governance to get complete principle text. "
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
        # Tool 4: List principles
        Tool(
            name="list_principles",
            description=(
                "List all available governance principles. "
                "Optionally filter by domain. Returns principle IDs, titles, and series."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional: Filter by domain (constitution, ai-coding, multi-agent)",
                    },
                },
            },
        ),
        # Tool 5: List domains
        Tool(
            name="list_domains",
            description=(
                "List all available governance domains with statistics. "
                "Shows principle counts, trigger keywords, and domain info."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tool 6: Refresh index
        Tool(
            name="refresh_index",
            description=(
                "Re-extract governance documents and rebuild indexes. "
                "Use after modifying source documents. Returns extraction summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Tool 7: Validate hierarchy
        Tool(
            name="validate_hierarchy",
            description=(
                "Check for conflicts between governance documents. "
                "Verifies domain principles comply with constitution. "
                "Returns any detected conflicts or violations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional: Check specific domain only",
                    },
                },
            },
        ),
        # Tool 8: Get escalation triggers
        Tool(
            name="get_escalation_triggers",
            description=(
                "Get list of situations that require human escalation. "
                "Returns escalation triggers from all domains with severity levels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional: Filter by domain",
                    },
                },
            },
        ),
        # Tool 9: Search by failure mode
        Tool(
            name="search_by_failure",
            description=(
                "Find principles that address a specific failure mode or symptom. "
                "Use when you observe something going wrong and need guidance. "
                "Searches failure_indicators metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "failure": {
                        "type": "string",
                        "description": "The failure symptom or problem observed",
                    },
                },
                "required": ["failure"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        engine = get_engine()

        if name == "retrieve_governance":
            return await _handle_retrieve(engine, arguments)
        elif name == "detect_domain":
            return await _handle_detect_domain(engine, arguments)
        elif name == "get_principle":
            return await _handle_get_principle(engine, arguments)
        elif name == "list_principles":
            return await _handle_list_principles(engine, arguments)
        elif name == "list_domains":
            return await _handle_list_domains(engine, arguments)
        elif name == "refresh_index":
            return await _handle_refresh_index(arguments)
        elif name == "validate_hierarchy":
            return await _handle_validate_hierarchy(engine, arguments)
        elif name == "get_escalation_triggers":
            return await _handle_get_escalation_triggers(engine, arguments)
        elif name == "search_by_failure":
            return await _handle_search_by_failure(engine, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool error: {e}")
        error = ErrorResponse(
            error_code="TOOL_ERROR",
            message=str(e),
            suggestions=["Check query syntax", "Verify domain name", "Run extraction first"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_retrieve(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle retrieve_governance tool."""
    query = args.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    result = engine.retrieve(
        query=query,
        domain=args.get("domain"),
        include_constitution=args.get("include_constitution", True),
        include_methods=args.get("include_methods", False),
        max_results=args.get("max_results"),
    )

    # Log audit
    principle_ids = [sp.principle.id for sp in result.constitution_principles + result.domain_principles]
    log_audit(
        "retrieve_governance",
        query,
        result.domains_detected,
        principle_ids,
        result.s_series_triggered,
    )

    # Format response
    output = _format_retrieval_result(result)
    return [TextContent(type="text", text=output)]


def _format_retrieval_result(result) -> str:
    """Format retrieval result as readable text."""
    lines = []

    # Header
    if result.s_series_triggered:
        lines.append("⚠️ **S-SERIES TRIGGERED** - Safety/Ethics principles apply")
        lines.append("")

    lines.append(f"**Query:** {result.query}")
    lines.append(f"**Domains Detected:** {', '.join(result.domains_detected) or 'None (using Constitution only)'}")
    lines.append("")

    # Constitution principles
    if result.constitution_principles:
        lines.append("## Constitution Principles")
        for sp in result.constitution_principles:
            p = sp.principle
            lines.append(f"### {p.id}: {p.title}")
            lines.append(f"*Score: {sp.score:.1f} | Series: {p.series_code}*")
            lines.append("")
            # Include first ~500 chars of content
            content_preview = p.content[:500] + "..." if len(p.content) > 500 else p.content
            lines.append(content_preview)
            lines.append("")

    # Domain principles
    if result.domain_principles:
        lines.append("## Domain Principles")
        for sp in result.domain_principles:
            p = sp.principle
            lines.append(f"### {p.id}: {p.title}")
            lines.append(f"*Score: {sp.score:.1f} | Domain: {p.domain} | Series: {p.series_code}*")
            lines.append("")
            content_preview = p.content[:500] + "..." if len(p.content) > 500 else p.content
            lines.append(content_preview)
            lines.append("")

    # Methods
    if result.methods:
        lines.append("## Applicable Methods")
        for m in result.methods:
            lines.append(f"- **{m.id}:** {m.title}")
        lines.append("")

    if not result.constitution_principles and not result.domain_principles:
        lines.append("*No matching principles found. Try rephrasing your query or specifying a domain.*")

    return "\n".join(lines)


async def _handle_detect_domain(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle detect_domain tool."""
    query = args.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    domains = engine.detect_domains(query)

    output = {
        "query": query,
        "detected_domains": domains,
        "domain_count": len(domains),
        "note": "Constitution always applies regardless of domain detection",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_principle(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle get_principle tool."""
    principle_id = args.get("principle_id", "")
    if not principle_id:
        return [TextContent(type="text", text="Error: principle_id is required")]

    # Get full content from cache
    content = engine.get_principle_content(principle_id)
    if content:
        return [TextContent(type="text", text=content)]

    # Fall back to principle object
    principle = engine.get_principle_by_id(principle_id)
    if principle:
        return [TextContent(type="text", text=principle.content)]

    error = ErrorResponse(
        error_code="PRINCIPLE_NOT_FOUND",
        message=f"Principle '{principle_id}' not found",
        suggestions=[
            "Use list_principles to see available IDs",
            "Check ID format: meta-C1, coding-C1, multi-A1",
        ],
    )
    return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_list_principles(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle list_principles tool."""
    domain = args.get("domain")
    principles = engine.list_principles(domain)

    output = {
        "domain_filter": domain or "all",
        "total_count": len(principles),
        "principles": principles,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_list_domains(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle list_domains tool."""
    domains = engine.list_domains()

    output = {
        "total_domains": len(domains),
        "domains": domains,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_refresh_index(args: dict) -> list[TextContent]:
    """Handle refresh_index tool - re-extract all documents."""
    global _config, _engine

    config = load_config()
    extractor = DocumentExtractor(config)
    indexes = extractor.extract_all()

    # Reload the engine with fresh indexes
    _engine = RetrievalEngine(config)

    summary = {
        "status": "success",
        "domains_extracted": len(indexes),
        "details": {},
    }

    for domain_name, index in indexes.items():
        summary["details"][domain_name] = {
            "principles": len(index.principles),
            "methods": len(index.methods),
        }

    return [TextContent(type="text", text=json.dumps(summary, indent=2))]


async def _handle_validate_hierarchy(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle validate_hierarchy tool - check for conflicts."""
    domain = args.get("domain")
    conflicts: list[dict] = []

    # Get all domains to check
    domains_to_check = [domain] if domain else [d for d in engine.indexes if d != "constitution"]

    # Get constitution principles for reference
    constitution_series = set()
    if "constitution" in engine.indexes:
        for p in engine.indexes["constitution"].principles:
            constitution_series.add(p.series_code)

    for domain_name in domains_to_check:
        if domain_name not in engine.indexes:
            continue

        for principle in engine.indexes[domain_name].principles:
            # Check 1: Domain principles should not use constitution-only series
            if principle.series_code in ["S", "MA", "G", "O"] and domain_name != "constitution":
                conflicts.append({
                    "type": "series_violation",
                    "principle": principle.id,
                    "message": f"Domain principle uses constitution series '{principle.series_code}'",
                    "severity": "warning",
                })

            # Check 2: S-Series references in domain should cite constitution
            if "S-Series" in principle.content or "S1" in principle.content or "S2" in principle.content:
                if "derives from" not in principle.content.lower() and "constitutional" not in principle.content.lower():
                    conflicts.append({
                        "type": "missing_derivation",
                        "principle": principle.id,
                        "message": "References S-Series without explicit constitutional derivation",
                        "severity": "info",
                    })

    output = {
        "domains_checked": domains_to_check,
        "conflicts_found": len(conflicts),
        "conflicts": conflicts,
        "status": "valid" if not conflicts else "issues_found",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_escalation_triggers(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle get_escalation_triggers tool - find escalation situations."""
    domain = args.get("domain")
    triggers: list[dict] = []

    # Search for escalation patterns in principle content
    escalation_patterns = [
        ("⚠️", "immediate"),
        ("Escalate to", "required"),
        ("IMMEDIATELY", "immediate"),
        ("Human Interaction Is Needed", "conditional"),
        ("Product Owner", "required"),
        ("Supreme Court", "immediate"),  # Legal analogy for human review
    ]

    domains_to_check = [domain] if domain else list(engine.indexes.keys())

    for domain_name in domains_to_check:
        if domain_name not in engine.indexes:
            continue

        for principle in engine.indexes[domain_name].principles:
            for pattern, severity in escalation_patterns:
                if pattern in principle.content:
                    # Extract context around the pattern
                    idx = principle.content.find(pattern)
                    start = max(0, idx - 50)
                    end = min(len(principle.content), idx + 150)
                    context = principle.content[start:end].strip()

                    triggers.append({
                        "principle_id": principle.id,
                        "principle_title": principle.title,
                        "domain": domain_name,
                        "severity": severity,
                        "context": context,
                    })
                    break  # One trigger per principle

    # Deduplicate and sort by severity
    severity_order = {"immediate": 0, "required": 1, "conditional": 2}
    triggers.sort(key=lambda t: severity_order.get(t["severity"], 99))

    output = {
        "domains_searched": domains_to_check,
        "triggers_found": len(triggers),
        "triggers": triggers,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_search_by_failure(engine: RetrievalEngine, args: dict) -> list[TextContent]:
    """Handle search_by_failure tool - find principles by failure indicators."""
    failure = args.get("failure", "").lower()
    if not failure:
        return [TextContent(type="text", text="Error: failure description is required")]

    failure_words = set(failure.split())
    matches: list[dict] = []

    for domain_name, index in engine.indexes.items():
        for principle in index.principles:
            matched_indicators = []

            for indicator in principle.metadata.failure_indicators:
                if indicator.lower() in failure or any(
                    word in indicator.lower() for word in failure_words
                ):
                    matched_indicators.append(indicator)

            if matched_indicators:
                matches.append({
                    "principle_id": principle.id,
                    "principle_title": principle.title,
                    "domain": domain_name,
                    "series": principle.series_code,
                    "matched_indicators": matched_indicators,
                    "all_indicators": principle.metadata.failure_indicators,
                })

    # Sort by number of matched indicators
    matches.sort(key=lambda m: -len(m["matched_indicators"]))

    output = {
        "failure_query": failure,
        "matches_found": len(matches),
        "matches": matches[:10],  # Limit to top 10
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting AI Governance MCP Server")

    # Initialize engine on startup
    get_engine()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    import asyncio

    # Handle --test mode for quick testing
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "specification incomplete"
        engine = get_engine()
        result = engine.retrieve(query)
        print(_format_retrieval_result(result))
        return

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
