"""Context Engine MCP Server.

Separate entry point from the governance MCP server. Provides tools
for querying and managing project content indexes via MCP protocol.

Tools exposed:
- query_project: Semantic + keyword search across project content
- index_project: Trigger manual re-index of current project
- list_projects: Show all indexed projects
- project_status: Index stats for current project

Security:
- Input validation on all tool arguments (length, type, bounds)
- Error messages sanitized to prevent information leakage
- Rate limiting on index_project to prevent resource exhaustion
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
import threading
import time
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .project_manager import ProjectManager

logger = logging.getLogger("ai_governance_mcp.context_engine.server")

# ─── Security constants ───

# Maximum query length to prevent memory/performance issues
MAX_QUERY_LENGTH = 10000

# Maximum log content length to prevent log bloat
MAX_LOG_CONTENT_LENGTH = 2000

# Rate limiting for index_project (token bucket algorithm)
# Conservative: indexing is expensive, limit to 5 requests per minute
_INDEX_RATE_LIMIT_TOKENS = 5.0
_INDEX_RATE_LIMIT_REFILL_RATE = 5 / 60  # 5 per minute
_index_rate_tokens = _INDEX_RATE_LIMIT_TOKENS
_index_rate_last_refill = time.time()
_rate_limit_lock = threading.Lock()


def _check_index_rate_limit() -> bool:
    """Check if index_project request is within rate limit.

    Uses token bucket algorithm. Returns True if allowed.
    Thread-safe: guarded by _rate_limit_lock since MCP server
    runs handlers via run_in_executor thread pool.

    Limitation: Single-process only. Multiple server instances (e.g.,
    separate Claude Code windows) each maintain independent rate limits.
    Distributed rate limiting would require external coordination (Redis,
    filesystem lock, etc.) — not implemented for v1 simplicity.
    """
    global _index_rate_tokens, _index_rate_last_refill

    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _index_rate_last_refill
        _index_rate_last_refill = now

        _index_rate_tokens = min(
            _INDEX_RATE_LIMIT_TOKENS,
            _index_rate_tokens + (elapsed * _INDEX_RATE_LIMIT_REFILL_RATE),
        )

        if _index_rate_tokens >= 1:
            _index_rate_tokens -= 1
            return True
        return False


def _sanitize_error_message(error: Exception) -> str:
    """Sanitize error message to prevent information leakage.

    Removes internal paths (absolute, relative, UNC), line numbers,
    memory addresses, and module paths from error messages before
    returning to client.
    """
    message = str(error)

    # Remove absolute paths (keep only filename)
    # Handles Unix paths, Windows paths (C:\), and paths with spaces in quotes
    message = re.sub(
        r'(?:[A-Za-z]:)?(?:[/\\][^/\\:*?"<>|\n]+)+[/\\]([^/\\:*?"<>|\s]+)',
        r"\1",
        message,
    )

    # Remove relative path traversals (../../etc/passwd)
    message = re.sub(
        r'(?:\.\.[/\\])+([^/\\:*?"<>|\s]+)',
        r"\1",
        message,
    )

    # Remove Windows UNC paths (\\server\share\file.txt)
    message = re.sub(
        r'\\\\[^\\:*?"<>|\s]+(?:\\[^\\:*?"<>|\s]+)*\\([^\\:*?"<>|\s]+)',
        r"\1",
        message,
    )

    # Remove line numbers from tracebacks
    message = re.sub(r", line \d+", "", message)

    # Remove memory addresses
    message = re.sub(r"0x[0-9a-fA-F]+", "0x***", message)

    # Remove Python module paths (e.g., "foo.bar.baz.function")
    # Require alphabetic start per segment to avoid matching version numbers/IPs
    message = re.sub(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){2,}\b", "[module]", message)

    # Remove function references in tracebacks
    message = re.sub(r"\bin\s+\w+\s*\(", "in [func](", message)

    # Remove stack frame references
    message = re.sub(r'File\s+["\'][^"\']+["\']', "File [redacted]", message)

    # Truncate very long messages
    max_error_length = 500
    if len(message) > max_error_length:
        message = message[:max_error_length] + "...[truncated]"

    return message


def _sanitize_for_logging(content: str | None) -> str | None:
    """Sanitize content before logging to prevent sensitive data exposure."""
    if not content:
        return content
    if len(content) > MAX_LOG_CONTENT_LENGTH:
        return content[:MAX_LOG_CONTENT_LENGTH] + "...[TRUNCATED]"
    return content


# Server instructions injected into every response
SERVER_INSTRUCTIONS = """## Context Engine MCP Server

Semantic search across project content. Query to discover what already exists before implementing.

### When to Query
Call `query_project(query="...")` before creating or modifying code:
- **Before creating** a new file, function, class, or module — check for existing implementations
- **Before modifying** existing code — understand related patterns and dependencies
- **When you hear** "where does X happen?", "do we already have Y?", "what pattern do we use for Z?"
- **During planning** — build a context inventory of affected areas

### Required Behavior
1. **Query before creating** — `query_project("existing [thing] implementation")`
2. **Query before modifying** — `query_project("how does [component] work")`
3. **Cite findings** — Reference file paths and patterns found, or confirm nothing relevant exists
4. **Check freshness** — If `project_status` shows stale index, call `index_project` first

### Tools
| Tool | Purpose |
|------|---------|
| `query_project` | Search project content by meaning or keyword |
| `index_project` | Trigger re-index of current project |
| `list_projects` | Show all indexed projects |
| `project_status` | Index stats for current project |

### Companion: AI Governance MCP
Query governance for *how* to approach a task (principles, methods).
Query context engine for *what already exists* (code, patterns, files).
"""


_CE_CRITICAL_PATTERNS = {
    "prompt_injection": re.compile(
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


def _validate_ce_server_instructions(instructions: str) -> None:
    """Validate CE SERVER_INSTRUCTIONS for prompt injection patterns.

    Called at module load time to ensure the instruction block
    sent to AI clients is clean. Mirrors the governance server's
    _validate_server_instructions pattern.

    Raises:
        RuntimeError: If critical patterns are detected.
    """
    for pattern_name, pattern in _CE_CRITICAL_PATTERNS.items():
        matches = pattern.findall(instructions)
        if matches:
            raise RuntimeError(
                f"CRITICAL: CE SERVER_INSTRUCTIONS contains {pattern_name} pattern"
            )


_validate_ce_server_instructions(SERVER_INSTRUCTIONS)


def _setup_logging() -> None:
    """Configure logging to stderr (stdout reserved for MCP JSON-RPC)."""
    log_level = os.environ.get("AI_CONTEXT_ENGINE_LOG_LEVEL", "INFO")
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger("ai_governance_mcp.context_engine")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(handler)


def _create_project_manager() -> ProjectManager:
    """Create and configure the project manager from environment.

    Environment variables:
        AI_CONTEXT_ENGINE_EMBEDDING_MODEL: Model name (default: BAAI/bge-small-en-v1.5)
        AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS: Integer dimensions (default: 384)
        AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT: Float 0.0-1.0 (default: 0.7)
        AI_CONTEXT_ENGINE_INDEX_PATH: Custom index storage path (default: ~/.context-engine/indexes/)
        AI_CONTEXT_ENGINE_INDEX_MODE: 'ondemand' (default) or 'realtime' (enables file watcher)
    """
    embedding_model = os.environ.get(
        "AI_CONTEXT_ENGINE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
    )

    try:
        embedding_dimensions = int(
            os.environ.get("AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS", "384")
        )
        if embedding_dimensions <= 0:
            raise ValueError("must be positive")
    except (ValueError, TypeError) as e:
        logger.warning(
            "Invalid AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS: %s. Using default 384.",
            e,
        )
        embedding_dimensions = 384

    try:
        semantic_weight = float(
            os.environ.get("AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT", "0.7")
        )
        semantic_weight = max(0.0, min(1.0, semantic_weight))
    except (ValueError, TypeError) as e:
        logger.warning(
            "Invalid AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT: %s. Using default 0.7.",
            e,
        )
        semantic_weight = 0.7

    index_path = os.environ.get("AI_CONTEXT_ENGINE_INDEX_PATH")
    if index_path:
        resolved = Path(index_path).resolve()
        # Validate custom path is under user home to prevent writing to system dirs
        home = Path.home().resolve()
        if not str(resolved).startswith(str(home)):
            logger.warning(
                "Custom index path %s is outside user home directory (%s). "
                "Ignoring — using default path for safety.",
                resolved,
                home,
            )
            index_path = None
        else:
            logger.info(
                "Using custom index path: %s (set via AI_CONTEXT_ENGINE_INDEX_PATH)",
                resolved,
            )

    # Parse index mode (ondemand or realtime)
    index_mode_raw = os.environ.get("AI_CONTEXT_ENGINE_INDEX_MODE", "ondemand").lower()
    if index_mode_raw in ("ondemand", "realtime"):
        default_index_mode = index_mode_raw
    else:
        logger.warning(
            "Invalid AI_CONTEXT_ENGINE_INDEX_MODE: '%s'. "
            "Must be 'ondemand' or 'realtime'. Using default 'ondemand'.",
            index_mode_raw,
        )
        default_index_mode = "ondemand"

    if default_index_mode == "realtime":
        logger.info(
            "Index mode set to 'realtime' — file watcher will be enabled for new projects"
        )

    from .storage.filesystem import FilesystemStorage

    storage = FilesystemStorage(base_path=Path(index_path) if index_path else None)

    return ProjectManager(
        storage=storage,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        semantic_weight=semantic_weight,
        default_index_mode=default_index_mode,
    )


def create_server() -> tuple[Server, ProjectManager]:
    """Create and configure the MCP server with all tools."""
    server = Server("context-engine", instructions=SERVER_INSTRUCTIONS)
    manager = _create_project_manager()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="query_project",
                description=(
                    "Search project content using semantic and keyword matching. "
                    "Returns ranked results with file paths and line numbers. "
                    "Use for: finding code patterns, locating implementations, "
                    "discovering related files, understanding project structure."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural language query or keyword search. "
                                "Examples: 'where do we handle authentication?', "
                                "'validate_token function', 'error handling patterns'"
                            ),
                            "minLength": 1,
                            "maxLength": MAX_QUERY_LENGTH,
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results to return (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="index_project",
                description=(
                    "Trigger a full re-index of the current project. "
                    "Use when: files have changed and index may be stale, "
                    "or after initial project setup."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_projects",
                description="Show all indexed projects with basic stats.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="project_status",
                description=(
                    "Get detailed index statistics for the current project: "
                    "file count, chunk count, last updated, index size, "
                    "watcher status, and embedding model."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "query_project":
                return await _handle_query_project(manager, arguments)
            elif name == "index_project":
                return await _handle_index_project(manager)
            elif name == "list_projects":
                return await _handle_list_projects(manager)
            elif name == "project_status":
                return await _handle_project_status(manager)
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Unknown tool: {name[:50]}",
                                "valid_tools": [
                                    "query_project",
                                    "index_project",
                                    "list_projects",
                                    "project_status",
                                ],
                            },
                            indent=2,
                        ),
                    )
                ]
        except Exception as e:
            logger.error(
                "Error in tool %s: %s",
                name,
                _sanitize_for_logging(str(e)),
                exc_info=True,
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": _sanitize_error_message(e), "tool": name},
                        indent=2,
                    ),
                )
            ]

    return server, manager


async def _handle_query_project(
    manager: ProjectManager, arguments: dict
) -> list[TextContent]:
    """Handle query_project tool call."""
    # Validate query argument
    query = arguments.get("query", "")
    if not isinstance(query, str):
        return [TextContent(type="text", text="Error: query must be a string")]
    query = query.strip()
    if not query:
        return [TextContent(type="text", text="Error: query cannot be empty")]
    if len(query) > MAX_QUERY_LENGTH:
        return [
            TextContent(
                type="text",
                text=f"Error: query exceeds maximum length of {MAX_QUERY_LENGTH}",
            )
        ]

    # Validate max_results argument
    raw_max_results = arguments.get("max_results", 10)
    try:
        max_results = min(max(int(raw_max_results), 1), 50)
    except (TypeError, ValueError):
        max_results = 10

    # Run indexing/query in thread pool (CPU-bound)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: manager.query_project(query=query, max_results=max_results),
    )

    if not result.results:
        # Differentiate: indexed-but-no-match vs truly-not-indexed
        if result.last_indexed_at is not None:
            message = "No matching results found — try rephrasing your query."
        else:
            message = (
                "No results found. The project may not be indexed yet. "
                "Use index_project to create the index."
            )
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "query": query,
                        "message": message,
                        "total_results": 0,
                    },
                    indent=2,
                ),
            )
        ]

    # Format results
    formatted_results = []
    for r in result.results:
        formatted_results.append(
            {
                "file": r.chunk.source_path,
                "lines": f"{r.chunk.start_line}-{r.chunk.end_line}",
                "type": r.chunk.content_type,
                "score": round(r.combined_score, 3),
                "heading": r.chunk.heading,
                "content": r.chunk.content[:500],  # Truncate to 500 chars for display
            }
        )

    output = {
        "query": query,
        "total_results": result.total_results,
        "query_time_ms": result.query_time_ms,
        "last_indexed_at": result.last_indexed_at,
        "index_age_seconds": result.index_age_seconds,
        "results": formatted_results,
    }

    # Warn if index is stale (>1 hour old)
    if result.index_age_seconds is not None and result.index_age_seconds > 3600:
        hours = result.index_age_seconds / 3600
        output["staleness_warning"] = (
            f"Index is {hours:.1f} hours old. Run index_project to refresh."
        )

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_index_project(manager: ProjectManager) -> list[TextContent]:
    """Handle index_project tool call."""
    # Rate limit indexing requests (expensive operation)
    if not _check_index_rate_limit():
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "Rate limited (max 5 per minute). index_project is an expensive operation. "
                        "Please wait before trying again.",
                    },
                    indent=2,
                ),
            )
        ]

    project_path = Path.cwd()

    loop = asyncio.get_running_loop()
    index = await loop.run_in_executor(
        None, lambda: manager.reindex_project(project_path)
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "message": "Project indexed successfully",
                    "project_path": str(project_path),
                    "total_files": index.total_files,
                    "total_chunks": index.total_chunks,
                    "embedding_model": index.embedding_model,
                },
                indent=2,
            ),
        )
    ]


async def _handle_list_projects(manager: ProjectManager) -> list[TextContent]:
    """Handle list_projects tool call."""
    loop = asyncio.get_running_loop()
    projects = await loop.run_in_executor(None, manager.list_projects)

    if not projects:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"message": "No indexed projects found", "projects": []},
                    indent=2,
                ),
            )
        ]

    formatted = [
        {
            "project_id": p.project_id,
            "project_path": p.project_path,
            "total_files": p.total_files,
            "total_chunks": p.total_chunks,
            "last_updated": p.last_updated,
            "index_mode": p.index_mode,
        }
        for p in projects
    ]

    return [
        TextContent(
            type="text",
            text=json.dumps({"projects": formatted}, indent=2),
        )
    ]


async def _handle_project_status(
    manager: ProjectManager,
) -> list[TextContent]:
    """Handle project_status tool call."""
    loop = asyncio.get_running_loop()
    status = await loop.run_in_executor(None, manager.get_project_status)

    if status is None:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "message": "Current project is not indexed. "
                        "Use index_project to create the index.",
                        "project_path": str(Path.cwd()),
                    },
                    indent=2,
                ),
            )
        ]

    return [
        TextContent(
            type="text",
            text=json.dumps(status.model_dump(), indent=2),
        )
    ]


def main() -> None:
    """Entry point for the context engine MCP server."""
    _setup_logging()
    logger.info("Starting Context Engine MCP Server")

    # H3 fix: Signal handlers must only call async-signal-safe functions.
    # logging.info() and manager.shutdown() can deadlock if signal arrives
    # while locks are held. Use minimal handler — just exit immediately.
    # The finally block in _run() handles graceful cleanup for normal exits.
    def _signal_handler(sig, frame):
        # Only async-signal-safe: set flag and exit
        # Don't call logger (uses locks) or manager.shutdown() (acquires locks)
        os._exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        server, manager = create_server()

        async def _run() -> None:
            try:
                async with stdio_server() as (read_stream, write_stream):
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
            finally:
                manager.shutdown()

        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, shutting down")
    finally:
        # Force exit: MCP Python SDK asyncio cleanup can hang indefinitely
        # (see github.com/modelcontextprotocol/python-sdk/issues/514)
        os._exit(0)


if __name__ == "__main__":
    main()
