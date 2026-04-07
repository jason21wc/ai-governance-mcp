"""Governance enforcement proxy for MCP servers (Layer 3).

Intercepts MCP JSON-RPC tool calls at the stdio protocol level to enforce
governance preconditions. Works with ANY AI client (Cursor, Gemini CLI, etc.)
— not just Claude Code.

Phase 1 (Self-Enforcement):
    Wraps the governance MCP server. Requires evaluate_governance() before
    action tools (scaffold_project, capture_reference, etc.). Read-only tools
    are always allowed.

Phase 2 (Cross-MCP Enforcement):
    Wraps ANY third-party MCP server (GitHub, filesystem, etc.) to enforce
    governance before consequential tool calls. Uses shared state file for
    cross-process coordination — the governance proxy writes timestamps when
    evaluate_governance() is called, and cross-MCP proxies read them.

Architecture:
    Layer 1 (Advisory): SERVER_INSTRUCTIONS + GOVERNANCE_REMINDER (~13%)
    Layer 2 (Claude Code hooks): Pre-tool transcript scanning (~100%, Claude only)
    Layer 3 (This module): Protocol-level enforcement (~100%, all clients)

Usage:
    # Phase 1 — wrap the governance server:
    ai-governance-proxy -- ai-governance-mcp

    # Phase 2 — wrap GitHub MCP with governance enforcement:
    ai-governance-proxy --govern-all \
        --always-allow "get_file_contents,list_issues,search_code" \
        -- npx @modelcontextprotocol/server-github

    # Phase 2 — with config file:
    ai-governance-proxy --config github-governance.yaml \
        -- npx @modelcontextprotocol/server-github

Environment variables:
    GOVERNANCE_ENFORCEMENT_ENABLED: Master toggle (default: true)
    GOVERNANCE_ENFORCEMENT_SOFT_MODE: Warn instead of block (default: false)
    GOVERNANCE_RECENCY_WINDOW: Tool calls before governance expires (default: 50)
    GOVERNANCE_STATE_FILE: Shared state file path (default: ~/.ai-governance/enforcement-state.json)
    GOVERNANCE_STATE_TTL: Shared state TTL in seconds (default: 300)
"""

import asyncio
import json
import os
import signal
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnforcementResult:
    """Result of a governance precondition check."""

    allowed: bool
    message: str | None = None


@dataclass
class GovernanceEnforcer:
    """Tracks governance preconditions per session.

    Supports two modes:
    - Self-enforcement (Phase 1): Wraps the governance server. Tool sets are
      hardcoded defaults. Governance satisfiers are tracked in-process.
    - Cross-MCP enforcement (Phase 2): Wraps any third-party server. Tool sets
      are configurable via YAML config or CLI args. Governance state is read
      from a shared state file written by the governance proxy instance.

    Counts tool calls (not transcript lines) for transport-agnostic
    recency tracking. Mirrors the hook env var patterns for consistency.
    """

    # Default tool sets (Phase 1 — governance server)
    _DEFAULT_GOVERNED: set[str] = field(
        default_factory=lambda: {
            "scaffold_project",
            "capture_reference",
            "install_agent",
            "uninstall_agent",
            "log_feedback",
            "log_governance_reasoning",
        },
        repr=False,
    )

    _DEFAULT_SATISFIERS: set[str] = field(
        default_factory=lambda: {
            "evaluate_governance",
            "verify_governance_compliance",
        },
        repr=False,
    )

    _DEFAULT_ALLOWED: set[str] = field(
        default_factory=lambda: {
            "query_governance",
            "get_principle",
            "list_domains",
            "get_domain_summary",
            "get_metrics",
        },
        repr=False,
    )

    # Active tool sets (may be overridden by config)
    GOVERNED_TOOLS: set[str] = field(default_factory=set)
    GOVERNANCE_SATISFIERS: set[str] = field(default_factory=set)
    ALWAYS_ALLOWED: set[str] = field(default_factory=set)

    recency_window: int = 50
    soft_mode: bool = False
    enabled: bool = True

    # Cross-MCP mode: govern ALL tools not in ALWAYS_ALLOWED
    govern_all: bool = False

    # Shared state file for cross-MCP coordination
    state_file: str | None = None
    state_ttl: int = 300  # seconds

    # Session state
    _call_counter: int = field(default=0, init=False)
    _last_governance_at: int = field(default=-1, init=False)

    def __post_init__(self):
        """Apply defaults when tool sets are empty (Phase 1 mode)."""
        if not self.GOVERNED_TOOLS and not self.govern_all:
            self.GOVERNED_TOOLS = set(self._DEFAULT_GOVERNED)
        if not self.GOVERNANCE_SATISFIERS:
            self.GOVERNANCE_SATISFIERS = set(self._DEFAULT_SATISFIERS)
        if not self.ALWAYS_ALLOWED and not self.govern_all:
            self.ALWAYS_ALLOWED = set(self._DEFAULT_ALLOWED)

    def record_call(self, tool_name: str) -> None:
        """Record a tool call and update governance state.

        Should be called AFTER check_precondition to avoid advancing the
        counter for blocked calls (which would erode the recency window).
        """
        self._call_counter += 1
        if tool_name in self.GOVERNANCE_SATISFIERS:
            self._last_governance_at = self._call_counter
            self._write_shared_state()

    def _governance_recent(self) -> bool:
        """Check if governance was called within the recency window.

        In cross-MCP mode, also checks the shared state file written by
        the governance proxy instance.
        """
        # In-process check (Phase 1, or governance proxy in Phase 2)
        if self._last_governance_at >= 0:
            if (self._call_counter - self._last_governance_at) <= self.recency_window:
                return True

        # Cross-MCP shared state check (Phase 2 — other proxy instances)
        if self.state_file:
            return self._read_shared_state()

        return False

    def _write_shared_state(self) -> None:
        """Write governance evaluation timestamp to shared state file.

        Called when a governance satisfier is recorded. Other proxy
        instances read this file to check if governance was evaluated
        recently across the MCP ecosystem.
        """
        if not self.state_file:
            return

        state = {
            "last_evaluation_ts": time.time(),
            "pid": os.getpid(),
        }

        try:
            state_path = Path(self.state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: temp file + rename
            fd, tmp_path = tempfile.mkstemp(dir=str(state_path.parent), suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(state, f)
                os.replace(tmp_path, str(state_path))
            except BaseException:
                # Clean up temp file on any error
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as e:
            sys.stderr.write(
                f"[enforcement] WARNING: Could not write shared state: {e}\n"
            )

    def _read_shared_state(self) -> bool:
        """Read governance state from shared file. Fail-closed on errors."""
        if not self.state_file:
            return False

        try:
            with open(self.state_file) as f:
                state = json.load(f)

            ts = state.get("last_evaluation_ts", 0)
            now = time.time()
            ts = min(ts, now)  # Reject future timestamps (spoofing defense)
            age = now - ts
            return age <= self.state_ttl
        except (OSError, json.JSONDecodeError, TypeError, KeyError):
            # Fail-closed: missing/corrupt state = governance not satisfied (tools blocked)
            return False

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

        # Determine if this tool requires governance
        needs_governance = False
        if self.govern_all:
            # Cross-MCP mode: ALL tools require governance unless exempted
            needs_governance = True
        elif tool_name in self.GOVERNED_TOOLS:
            # Explicit mode: only listed tools require governance
            needs_governance = True

        if needs_governance and not self._governance_recent():
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

        # Unknown tools in non-govern-all mode: allow through
        return EnforcementResult(allowed=True)

    @classmethod
    def from_env(cls) -> "GovernanceEnforcer":
        """Create an enforcer from environment variables."""
        enabled_str = os.environ.get("GOVERNANCE_ENFORCEMENT_ENABLED", "true").lower()
        soft_mode = os.environ.get("GOVERNANCE_ENFORCEMENT_SOFT_MODE", "false").lower()
        window = os.environ.get("GOVERNANCE_RECENCY_WINDOW", "50")
        state_file = os.environ.get("GOVERNANCE_STATE_FILE")
        state_ttl = os.environ.get("GOVERNANCE_STATE_TTL", "300")

        enabled = enabled_str not in ("false", "0", "no")
        if not enabled:
            sys.stderr.write(
                "WARNING: Governance enforcement DISABLED via "
                "GOVERNANCE_ENFORCEMENT_ENABLED environment variable.\n"
            )

        raw_window = int(window) if window.isdigit() else 50
        raw_ttl = int(state_ttl) if state_ttl.isdigit() else 300
        return cls(
            enabled=enabled,
            soft_mode=soft_mode in ("true", "1", "yes"),
            recency_window=max(1, min(raw_window, 10000)),
            state_file=state_file,
            state_ttl=max(1, min(raw_ttl, 86400)),
        )

    @classmethod
    def from_config(cls, config_path: str, **overrides) -> "GovernanceEnforcer":
        """Create an enforcer from a YAML config file.

        Config format:
            governed_tools:     # Tools requiring governance (optional with govern_all)
              - create_pull_request
              - push_files
            always_allowed:     # Read-only tools exempt from governance
              - get_file_contents
              - list_issues
            govern_all: true    # Govern ALL tools not in always_allowed
        """
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        governed = set(config.get("governed_tools", []))
        allowed = set(config.get("always_allowed", []))
        govern_all = config.get("govern_all", False)

        # Start from env vars for enforcement settings, then apply overrides
        base = cls.from_env()
        base.GOVERNED_TOOLS = governed
        base.ALWAYS_ALLOWED = allowed
        base.govern_all = govern_all

        # Apply CLI overrides (validate keys against dataclass fields)
        import dataclasses

        valid_keys = {f.name for f in dataclasses.fields(cls)}
        # Security-critical fields that must not be overridden via config
        non_overridable = {
            "enabled",
            "_call_counter",
            "_last_governance_at",
            "GOVERNANCE_SATISFIERS",
            "_DEFAULT_GOVERNED",
            "_DEFAULT_SATISFIERS",
            "_DEFAULT_ALLOWED",
        }
        for key, value in overrides.items():
            if key not in valid_keys:
                raise ValueError(f"Unknown config override: {key}")
            if key in non_overridable:
                raise ValueError(f"Cannot override security-critical field: {key}")
            if value is not None:
                setattr(base, key, value)

        return base


class StdioProxy:
    """MCP stdio proxy that enforces governance preconditions.

    Sits between an AI client and an MCP server, intercepting JSON-RPC
    messages over stdin/stdout. Blocks governed tool calls that lack
    the governance precondition.

    Works with ANY MCP server:
    - Phase 1: Wraps the governance server (default tool sets)
    - Phase 2: Wraps third-party servers (configurable tool sets + shared state)
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


def _default_state_file() -> str:
    """Return the default shared state file path."""
    return str(Path.home() / ".ai-governance" / "enforcement-state.json")


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

    # Phase 2: Cross-MCP enforcement
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="YAML config file specifying governed/allowed tools",
    )
    parser.add_argument(
        "--govern-all",
        action="store_true",
        default=False,
        help="Govern ALL tools not explicitly exempted (cross-MCP mode)",
    )
    parser.add_argument(
        "--always-allow",
        type=str,
        default=None,
        help="Comma-separated tools exempt from governance",
    )
    parser.add_argument(
        "--cross-mcp",
        action="store_true",
        default=False,
        help="Enable shared state file for cross-MCP coordination",
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Shared state file path (default: ~/.ai-governance/enforcement-state.json)",
    )
    parser.add_argument(
        "--state-ttl",
        type=int,
        default=None,
        help="Shared state TTL in seconds (default: 300)",
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

    # Determine if cross-MCP mode should be auto-enabled
    is_cross_mcp = args.cross_mcp or args.govern_all or args.config is not None

    # Build enforcer
    if args.config:
        enforcer = GovernanceEnforcer.from_config(
            args.config,
            soft_mode=args.soft_mode or None,
            state_ttl=args.state_ttl,
        )
    else:
        enforcer = GovernanceEnforcer.from_env()

    # CLI overrides
    if args.soft_mode:
        enforcer.soft_mode = True
    if args.disabled:
        enforcer.enabled = False
    if args.recency_window is not None:
        enforcer.recency_window = args.recency_window
    if args.govern_all:
        enforcer.govern_all = True
    if args.always_allow:
        cli_allowed = {t.strip() for t in args.always_allow.split(",") if t.strip()}
        enforcer.ALWAYS_ALLOWED |= cli_allowed  # Merge with config, not replace
    if args.state_ttl is not None:
        enforcer.state_ttl = max(1, min(args.state_ttl, 86400))

    # Enable shared state file for cross-MCP coordination
    if is_cross_mcp or enforcer.govern_all:
        enforcer.state_file = (
            args.state_file
            or os.environ.get("GOVERNANCE_STATE_FILE")
            or _default_state_file()
        )

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
