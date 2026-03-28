"""Tests for governance enforcement middleware (Layer 3).

Tests the GovernanceEnforcer state machine and StdioProxy protocol handling.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.enforcement import (
    GovernanceEnforcer,
    StdioProxy,
)


class TestGovernanceEnforcer:
    """Unit tests for GovernanceEnforcer state machine."""

    def test_governed_tool_blocked_without_governance(self):
        """Action tools should be blocked if evaluate_governance not called."""
        enforcer = GovernanceEnforcer()
        # Check precondition BEFORE record_call (mirrors proxy ordering)
        result = enforcer.check_precondition("scaffold_project")
        assert not result.allowed
        assert "GOVERNANCE REQUIRED" in result.message
        assert "evaluate_governance" in result.message

    def test_governed_tool_allowed_after_governance(self):
        """Action tools should succeed after evaluate_governance is called."""
        enforcer = GovernanceEnforcer()
        enforcer.record_call("evaluate_governance")
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed
        assert result.message is None
        enforcer.record_call("scaffold_project")

    def test_governance_satisfiers_always_pass(self):
        """Governance tools themselves should never be blocked."""
        enforcer = GovernanceEnforcer()
        for tool in enforcer.GOVERNANCE_SATISFIERS:
            enforcer.record_call(tool)
            result = enforcer.check_precondition(tool)
            assert result.allowed, f"{tool} should always be allowed"

    def test_always_allowed_tools_pass(self):
        """Read-only/query tools should never be blocked."""
        enforcer = GovernanceEnforcer()
        for tool in enforcer.ALWAYS_ALLOWED:
            enforcer.record_call(tool)
            result = enforcer.check_precondition(tool)
            assert result.allowed, f"{tool} should always be allowed"

    def test_all_governed_tools_blocked_without_governance(self):
        """Every governed tool should be blocked without governance."""
        enforcer = GovernanceEnforcer()
        for tool in enforcer.GOVERNED_TOOLS:
            result = enforcer.check_precondition(tool)
            assert not result.allowed, f"{tool} should be blocked without governance"

    def test_all_governed_tools_allowed_after_governance(self):
        """Every governed tool should be allowed after governance."""
        for tool in GovernanceEnforcer().GOVERNED_TOOLS:
            enforcer = GovernanceEnforcer()
            enforcer.record_call("evaluate_governance")
            result = enforcer.check_precondition(tool)
            assert result.allowed, f"{tool} should be allowed after governance"

    def test_recency_window_expires(self):
        """Governance should expire after recency_window tool calls."""
        enforcer = GovernanceEnforcer(recency_window=5)
        enforcer.record_call("evaluate_governance")

        # 5 more calls (at boundary of window=5, using <=)
        for _ in range(5):
            enforcer.record_call("query_governance")
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed, "Should still be within recency window (at boundary)"

        # 1 more call pushes past window
        enforcer.record_call("query_governance")
        result = enforcer.check_precondition("scaffold_project")
        assert not result.allowed, "Should be outside recency window"

    def test_recency_resets_on_new_governance_call(self):
        """A new governance call should reset the recency window."""
        enforcer = GovernanceEnforcer(recency_window=3)
        enforcer.record_call("evaluate_governance")

        # Expire the window
        for _ in range(5):
            enforcer.record_call("query_governance")

        # New governance call resets
        enforcer.record_call("evaluate_governance")
        enforcer.record_call("scaffold_project")
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed

    def test_soft_mode_warns_not_blocks(self):
        """Soft mode should allow through with a warning message."""
        enforcer = GovernanceEnforcer(soft_mode=True)
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed
        assert result.message is not None
        assert "WARNING" in result.message

    def test_disabled_allows_everything(self):
        """Disabled enforcement should allow all tools through."""
        enforcer = GovernanceEnforcer(enabled=False)
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed
        assert result.message is None

    def test_unknown_tools_pass_through(self):
        """Tools not in any list should pass through (extensibility)."""
        enforcer = GovernanceEnforcer()
        result = enforcer.check_precondition("future_new_tool")
        assert result.allowed

    def test_blocked_call_does_not_erode_window(self):
        """Blocked calls should not consume recency window slots."""
        enforcer = GovernanceEnforcer(recency_window=3)
        enforcer.record_call("evaluate_governance")

        # 10 blocked attempts should NOT erode the window
        for _ in range(10):
            result = enforcer.check_precondition("scaffold_project")
            # Don't call record_call for blocked calls (mirrors proxy behavior)

        # The window should still be intact since only 1 call recorded
        enforcer.record_call("scaffold_project")  # Record the allowed call
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed, "Blocked calls should not erode recency window"

    def test_call_counter_increments(self):
        """Call counter should increment on each record_call."""
        enforcer = GovernanceEnforcer()
        assert enforcer._call_counter == 0
        enforcer.record_call("query_governance")
        assert enforcer._call_counter == 1
        enforcer.record_call("evaluate_governance")
        assert enforcer._call_counter == 2

    def test_verify_governance_compliance_satisfies(self):
        """verify_governance_compliance should also satisfy the precondition."""
        enforcer = GovernanceEnforcer()
        enforcer.record_call("verify_governance_compliance")
        result = enforcer.check_precondition("scaffold_project")
        assert result.allowed

    def test_tool_name_whitespace_stripped(self):
        """Tool names with whitespace should be handled correctly."""
        enforcer = GovernanceEnforcer()
        result = enforcer.check_precondition("  evaluate_governance  ")
        # Whitespace-padded names don't match sets — proxy strips before checking
        # At the enforcer level, this is an unknown tool (passes through)
        assert result.allowed


class TestGovernanceEnforcerFromEnv:
    """Tests for environment variable configuration."""

    def test_default_values(self):
        """Should have sensible defaults when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.enabled is True
            assert enforcer.soft_mode is False
            assert enforcer.recency_window == 50

    def test_disabled_via_env(self):
        """GOVERNANCE_ENFORCEMENT_ENABLED=false should disable."""
        with patch.dict(os.environ, {"GOVERNANCE_ENFORCEMENT_ENABLED": "false"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.enabled is False

    def test_soft_mode_via_env(self):
        """GOVERNANCE_ENFORCEMENT_SOFT_MODE=true should enable soft mode."""
        with patch.dict(os.environ, {"GOVERNANCE_ENFORCEMENT_SOFT_MODE": "true"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.soft_mode is True

    def test_recency_window_via_env(self):
        """GOVERNANCE_RECENCY_WINDOW should set the window size."""
        with patch.dict(os.environ, {"GOVERNANCE_RECENCY_WINDOW": "100"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.recency_window == 100

    def test_invalid_recency_window_uses_default(self):
        """Invalid GOVERNANCE_RECENCY_WINDOW should fall back to default."""
        with patch.dict(os.environ, {"GOVERNANCE_RECENCY_WINDOW": "not_a_number"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.recency_window == 50


class TestStdioProxy:
    """Tests for StdioProxy JSON-RPC message handling."""

    @pytest.fixture
    def proxy(self):
        """Create a proxy with a test enforcer."""
        enforcer = GovernanceEnforcer(recency_window=50)
        return StdioProxy(server_cmd=["echo", "test"], enforcer=enforcer)

    @pytest.mark.asyncio
    async def test_non_tool_messages_forwarded(self, proxy):
        """Non-tools/call messages should pass through (return None)."""
        msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}).encode()
        result = await proxy._handle_client_message(msg)
        assert result is None  # None means "forward to server"

    @pytest.mark.asyncio
    async def test_governed_tool_blocked(self, proxy):
        """tools/call for governed tool without governance → error response."""
        msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 42,
                "method": "tools/call",
                "params": {"name": "scaffold_project", "arguments": {}},
            }
        ).encode()
        result = await proxy._handle_client_message(msg)
        assert result is not None  # Non-None means "return this to client"

        response = json.loads(result)
        assert response["id"] == 42
        assert response["result"]["isError"] is True
        assert "GOVERNANCE REQUIRED" in response["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_governed_tool_allowed_after_governance(self, proxy):
        """tools/call for governed tool after governance → forwarded."""
        # First: governance call
        gov_msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "evaluate_governance", "arguments": {}},
            }
        ).encode()
        result = await proxy._handle_client_message(gov_msg)
        assert result is None  # Forwarded

        # Then: governed tool
        tool_msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "scaffold_project", "arguments": {}},
            }
        ).encode()
        result = await proxy._handle_client_message(tool_msg)
        assert result is None  # Forwarded (allowed)

    @pytest.mark.asyncio
    async def test_read_only_tools_always_forwarded(self, proxy):
        """Read-only tools should always be forwarded."""
        for tool in ["query_governance", "get_principle", "list_domains"]:
            msg = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool, "arguments": {}},
                }
            ).encode()
            result = await proxy._handle_client_message(msg)
            assert result is None, f"{tool} should be forwarded"

    @pytest.mark.asyncio
    async def test_invalid_json_forwarded(self, proxy):
        """Non-JSON messages should be forwarded as-is."""
        result = await proxy._handle_client_message(b"not json at all")
        assert result is None

    @pytest.mark.asyncio
    async def test_error_response_format(self, proxy):
        """Error responses should follow JSON-RPC format with isError flag."""
        msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {"name": "install_agent", "arguments": {}},
            }
        ).encode()
        result = await proxy._handle_client_message(msg)
        response = json.loads(result)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 99
        assert "result" in response
        assert response["result"]["isError"] is True
        assert len(response["result"]["content"]) == 1
        assert response["result"]["content"][0]["type"] == "text"


class TestEnforcementToolCoverage:
    """Verify tool classification is comprehensive and correct."""

    def test_no_tool_in_multiple_sets(self):
        """No tool should appear in more than one classification set."""
        enforcer = GovernanceEnforcer()
        all_sets = [
            enforcer.GOVERNED_TOOLS,
            enforcer.GOVERNANCE_SATISFIERS,
            enforcer.ALWAYS_ALLOWED,
        ]
        for i, set_a in enumerate(all_sets):
            for j, set_b in enumerate(all_sets):
                if i != j:
                    overlap = set_a & set_b
                    assert not overlap, f"Overlap between sets {i} and {j}: {overlap}"

    def test_governed_tools_are_state_modifying(self):
        """Governed tools should all be state-modifying operations."""
        enforcer = GovernanceEnforcer()
        # These are tools that create files, install things, or log data
        for tool in enforcer.GOVERNED_TOOLS:
            assert tool in {
                "scaffold_project",
                "capture_reference",
                "install_agent",
                "uninstall_agent",
                "log_feedback",
                "log_governance_reasoning",
            }, f"Unexpected governed tool: {tool}"

    def test_always_allowed_are_read_only(self):
        """Always-allowed tools should all be read-only operations."""
        enforcer = GovernanceEnforcer()
        for tool in enforcer.ALWAYS_ALLOWED:
            assert tool in {
                "query_governance",
                "get_principle",
                "list_domains",
                "get_domain_summary",
                "get_metrics",
            }, f"Unexpected always-allowed tool: {tool}"
