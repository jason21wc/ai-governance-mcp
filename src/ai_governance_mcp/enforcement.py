"""Governance enforcement proxy for MCP servers (Layer 3).

Intercepts MCP JSON-RPC tool calls at the stdio protocol level to enforce
governance preconditions. Works with ANY AI client (Cursor, Gemini CLI, etc.)
— not just Claude Code.

What this does:
    Any AI client connecting to the governance server through this proxy must
    call evaluate_governance() before using action tools (scaffold_project,
    capture_reference, install_agent, uninstall_agent). Read-only tools
    (query_governance, get_principle, etc.) are always allowed.

What this does NOT do:
    This proxy only wraps the governance MCP server. Tool calls to OTHER MCP
    servers (GitHub, filesystem, etc.) are separate stdio connections that this
    proxy does not see. Cross-MCP enforcement is Phase 2 — see Backlog #1B.

Architecture:
    Layer 1 (Advisory): SERVER_INSTRUCTIONS + GOVERNANCE_REMINDER (~13%)
    Layer 2 (Claude Code hooks): Pre-tool transcript scanning (~100%, Claude only)
    Layer 3 (This module): Protocol-level enforcement (~100%, all clients)

Usage:
    # As a proxy wrapping the governance server:
    python -m ai_governance_mcp.enforcement -- python -m ai_governance_mcp.server

    # Or via the entry point:
    ai-governance-proxy -- ai-governance-mcp

Environment variables:
    GOVERNANCE_ENFORCEMENT_ENABLED: Master toggle (default: true)
    GOVERNANCE_ENFORCEMENT_SOFT_MODE: Warn instead of block (default: false)
    GOVERNANCE_RECENCY_WINDOW: Tool calls before governance expires (default: 50)
"""

import asyncio
import json
import os
import signal
import sys
from dataclasses import dataclass, field


@dataclass
class EnforcementResult:
    """Result of a governance precondition check."""

    allowed: bool
    message: str | None = None


@dataclass
class GovernanceEnforcer:
    """Tracks governance preconditions per session.

    Counts tool calls (not transcript lines) for transport-agnostic
    recency tracking. Mirrors the hook env var patterns for consistency.
    """

    # Tools that require governance precondition before use
    GOVERNED_TOOLS: set[str] = field(
        default_factory=lambda: {
            "scaffold_project",
            "capture_reference",
            "install_agent",
            "uninstall_agent",
            "log_feedback",
            "log_governance_reasoning",
        }
    )

    # Tools that satisfy the governance precondition
    GOVERNANCE_SATISFIERS: set[str] = field(
        default_factory=lambda: {
            "evaluate_governance",
            "verify_governance_compliance",
        }
    )

    # Read-only/query tools — always allowed without governance
    ALWAYS_ALLOWED: set[str] = field(
        default_factory=lambda: {
            "query_governance",
            "get_principle",
            "list_domains",
            "get_domain_summary",
            "get_metrics",
        }
    )

    recency_window: int = 50
    soft_mode: bool = False
    enabled: bool = True

    # Session state
    _call_counter: int = field(default=0, init=False)
    _last_governance_at: int = field(default=-1, init=False)

    def record_call(self, tool_name: str) -> None:
        """Record a tool call and update governance state.

        Should be called AFTER check_precondition to avoid advancing the
        counter for blocked calls (which would erode the recency window).
        """
        self._call_counter += 1
        if tool_name in self.GOVERNANCE_SATISFIERS:
            self._last_governance_at = self._call_counter

    def _governance_recent(self) -> bool:
        """Check if governance was called within the recency window."""
        if self._last_governance_at < 0:
            return False
        return (self._call_counter - self._last_governance_at) <= self.recency_window

    def check_precondition(self, tool_name: str) -> EnforcementResult:
        """Check if a tool call is allowed based on governance preconditions.

        Returns EnforcementResult with allowed=True if the call should proceed,
        or allowed=False with an error message if blocked.
        """
        if not self.enabled:
            return EnforcementResult(allowed=True)

        # Governance tools and read-only tools always pass through
        if tool_name in self.GOVERNANCE_SATISFIERS or tool_name in self.ALWAYS_ALLOWED:
            return EnforcementResult(allowed=True)

        # Governed tools require recent governance evaluation
        if tool_name in self.GOVERNED_TOOLS and not self._governance_recent():
            msg = (
                f'GOVERNANCE REQUIRED: Call evaluate_governance(planned_action="...") '
                f"before using '{tool_name}'. This enforcement ensures governance "
                f"principles are evaluated before state-modifying actions."
            )
            if self.soft_mode:
                return EnforcementResult(
                    allowed=True,
                    message=f"⚠️ GOVERNANCE WARNING: {msg}",
                )
            return EnforcementResult(allowed=False, message=msg)

        # Unknown tools: allow through (don't break extensibility)
        return EnforcementResult(allowed=True)

    @classmethod
    def from_env(cls) -> "GovernanceEnforcer":
        """Create an enforcer from environment variables."""
        enabled_str = os.environ.get("GOVERNANCE_ENFORCEMENT_ENABLED", "true").lower()
        soft_mode = os.environ.get("GOVERNANCE_ENFORCEMENT_SOFT_MODE", "false").lower()
        window = os.environ.get("GOVERNANCE_RECENCY_WINDOW", "50")

        enabled = enabled_str not in ("false", "0", "no")
        if not enabled:
            sys.stderr.write(
                "WARNING: Governance enforcement DISABLED via "
                "GOVERNANCE_ENFORCEMENT_ENABLED environment variable.\n"
            )

        raw_window = int(window) if window.isdigit() else 50
        return cls(
            enabled=enabled,
            soft_mode=soft_mode in ("true", "1", "yes"),
            recency_window=max(1, min(raw_window, 10000)),
        )


class StdioProxy:
    """MCP stdio proxy that enforces governance preconditions.

    Sits between an AI client and an MCP server, intercepting JSON-RPC
    messages over stdin/stdout. Blocks governed tool calls that lack
    the governance precondition.

    This proxy works with ANY MCP server — not just the governance server.
    In Phase 2, it can wrap third-party MCP servers for cross-MCP enforcement.
    """

    def __init__(
        self, server_cmd: list[str], enforcer: GovernanceEnforcer | None = None
    ):
        self.server_cmd = server_cmd
        self.enforcer = enforcer or GovernanceEnforcer.from_env()
        self._process: asyncio.subprocess.Process | None = None

    def _make_error_response(self, request_id: int | str, message: str) -> bytes:
        """Create a JSON-RPC error response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": message}],
                "isError": True,
            },
        }
        data = json.dumps(response)
        return data.encode("utf-8")

    def _make_warning_prefix(self, result_data: dict, warning: str) -> dict:
        """Prepend a warning to the first text content in a result."""
        content = result_data.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            content[0]["text"] = f"{warning}\n\n---\n\n{content[0]['text']}"
        return result_data

    async def _handle_client_message(self, line: bytes) -> bytes | None:
        """Process a message from the client. Returns bytes to send back
        to the client if the request should be blocked, or None to forward."""
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            sys.stderr.write(
                f"[enforcement] WARNING: forwarding non-JSON line ({len(line)} bytes)\n"
            )
            return None  # Not JSON, forward as-is

        # Only intercept tools/call requests
        if msg.get("method") != "tools/call":
            return None

        params = msg.get("params", {})
        tool_name = params.get("name", "").strip()
        request_id = msg.get("id")

        # Check precondition BEFORE recording (so blocked calls don't erode window)
        result = self.enforcer.check_precondition(tool_name)

        if not result.allowed:
            # Don't record blocked calls — they shouldn't consume recency window
            if request_id is None:
                return None  # JSON-RPC notifications get no response
            return self._make_error_response(request_id, result.message)

        # Record only forwarded calls
        self.enforcer.record_call(tool_name)

        # Soft mode warning is handled after server response
        if result.message and request_id is not None:
            self._pending_warnings[request_id] = result.message

        return None  # Forward to server

    async def _relay_with_warning(self, line: bytes) -> bytes:
        """Check if a server response needs a soft-mode warning prepended."""
        if not self._pending_warnings:
            return line

        try:
            msg = json.loads(line)
            req_id = msg.get("id")
            if req_id in self._pending_warnings:
                warning = self._pending_warnings.pop(req_id)
                msg = self._make_warning_prefix(msg, warning)
                return json.dumps(msg).encode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return line

    async def run(self) -> int:
        """Start the proxy: spawn server subprocess, relay messages."""
        self._pending_warnings: dict[int | str, str] = {}

        # Spawn the real MCP server
        self._process = await asyncio.create_subprocess_exec(
            *self.server_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Relay stderr directly (logging, not protocol)
        async def relay_stderr():
            while self._process.stderr and not self._process.stderr.at_eof():
                line = await self._process.stderr.readline()
                if line:
                    sys.stderr.buffer.write(line)
                    sys.stderr.buffer.flush()

        # Client → Server (with enforcement)
        async def client_to_server():
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            loop = asyncio.get_running_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)

            try:
                while not reader.at_eof():
                    line = await reader.readline()
                    if not line:
                        break

                    # Check if we should block this message
                    block_response = await self._handle_client_message(line)
                    if block_response:
                        # Send error directly back to client
                        sys.stdout.buffer.write(block_response + b"\n")
                        sys.stdout.buffer.flush()
                        continue

                    # Forward to server
                    if self._process.stdin:
                        self._process.stdin.write(line)
                        await self._process.stdin.drain()
            finally:
                # Client closed stdin — close server stdin too
                if self._process.stdin:
                    self._process.stdin.close()

        # Server → Client (with soft-mode warning injection)
        async def server_to_client():
            while self._process.stdout and not self._process.stdout.at_eof():
                line = await self._process.stdout.readline()
                if not line:
                    break

                # Check for soft-mode warning injection
                line = await self._relay_with_warning(line)

                out = line if isinstance(line, bytes) else line.encode("utf-8")
                sys.stdout.buffer.write(out)
                if not out.endswith(b"\n"):
                    sys.stdout.buffer.write(b"\n")
                sys.stdout.buffer.flush()

        # Run all relay tasks concurrently
        try:
            await asyncio.gather(
                client_to_server(),
                server_to_client(),
                relay_stderr(),
            )
        except (BrokenPipeError, ConnectionResetError):
            sys.stderr.write("[enforcement] Connection closed.\n")

        # Wait for server to exit
        return await self._process.wait()


def main():
    """Entry point for the governance enforcement proxy."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP Governance Enforcement Proxy",
        usage="%(prog)s [options] -- <server-command> [server-args...]",
    )
    parser.add_argument(
        "--soft-mode",
        action="store_true",
        default=False,
        help="Warn instead of block (default: hard block)",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        default=False,
        help="Pass through without enforcement (for testing)",
    )
    parser.add_argument(
        "--recency-window",
        type=int,
        default=None,
        help="Tool calls before governance expires (default: 50)",
    )
    parser.add_argument(
        "server_cmd",
        nargs=argparse.REMAINDER,
        help="Server command (after --)",
    )

    args = parser.parse_args()

    # Strip leading '--' from server command
    server_cmd = args.server_cmd
    if server_cmd and server_cmd[0] == "--":
        server_cmd = server_cmd[1:]

    if not server_cmd:
        # Default: wrap the governance server
        server_cmd = [sys.executable, "-m", "ai_governance_mcp.server"]

    # Create enforcer from env vars, with CLI overrides
    enforcer = GovernanceEnforcer.from_env()
    if args.soft_mode:
        enforcer.soft_mode = True
    if args.disabled:
        enforcer.enabled = False
    if args.recency_window is not None:
        enforcer.recency_window = args.recency_window

    proxy = StdioProxy(server_cmd, enforcer)

    # Handle signals gracefully
    def handle_signal(signum, _frame):
        if proxy._process:
            proxy._process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    exit_code = asyncio.run(proxy.run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
