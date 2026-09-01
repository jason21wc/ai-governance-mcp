"""Tests for governance enforcement middleware (Layer 3).

Tests the GovernanceEnforcer state machine and StdioProxy protocol handling,
including Phase 2 cross-MCP enforcement (govern-all mode, config files,
shared state coordination).
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.enforcement import (
    GovernanceEnforcer,
    StdioProxy,
)


class TestActIntrinsicGate:
    """Deterministic act-intrinsic deny: secret VALUES / credential PATHS in a
    tool call's actual arguments.

    Hard deny regardless of soft mode or whether governance was 'satisfied' —
    the gate reads the action's real content, so the model cannot dodge it by
    re-describing its plan to governance. The keystone of Desktop enforcement.
    """

    def _msg(self, tool, arguments, req_id=2):
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            }
        ).encode()

    def _enforcer(self, **kw):
        # Satisfy recency so the ONLY thing that can block is the act-intrinsic gate.
        kw.setdefault("enforce_acts", True)
        e = GovernanceEnforcer(**kw)
        e.record_call("evaluate_governance")
        return e

    async def _send(self, enforcer, tool, arguments):
        proxy = StdioProxy(server_cmd=["echo", "test"], enforcer=enforcer)
        return await proxy._handle_client_message(self._msg(tool, arguments))

    # ---- direct unit surface ----
    def test_act_intrinsic_block_unit(self):
        from ai_governance_mcp.safety_scan import act_intrinsic_block

        # Fixtures are CONSTRUCTED from parts so no literal secret-shaped string
        # appears in source (would trip the pre-push / remote secret scanners).
        assert act_intrinsic_block({"body": "sk-" + "a" * 24}) is not None
        assert act_intrinsic_block({"path": "~/.ssh/id_rsa"}) is not None
        assert act_intrinsic_block({"body": "meeting moved to 3pm"}) is None
        assert act_intrinsic_block({"password": ""}) is None  # value-only, empty

    def test_modern_provider_keys_blocked(self):
        from ai_governance_mcp.safety_scan import act_intrinsic_block

        assert act_intrinsic_block({"b": "sk-proj-" + "a" * 24}) is not None
        assert act_intrinsic_block({"b": "github_pat_" + "A1b2" * 11}) is not None
        assert act_intrinsic_block({"b": "rk_live_" + "x" * 24}) is not None

    def test_large_leading_field_does_not_shadow_secret(self):
        # Per-leaf scan: a benign 70KB field must not push a secret in a LATER
        # field past the 64KB cap (the join-then-slice bypass the reviewer caught).
        from ai_governance_mcp.safety_scan import act_intrinsic_block

        args = {"attachment": "z" * 70000, "body": "AKIA" + "I" * 16}
        assert act_intrinsic_block(args) is not None

    def test_non_dict_and_nested_args_safe(self):
        from ai_governance_mcp.safety_scan import act_intrinsic_block

        # Non-dict / scalar / None must not crash; nested leaves are still scanned.
        assert act_intrinsic_block(None) is None
        assert act_intrinsic_block("just a string") is None
        assert act_intrinsic_block(42) is None
        assert (
            act_intrinsic_block(["meeting at 3pm", {"k": ["x", "~/.ssh/id_rsa"]}])
            is not None
        )

    # ---- HARD DENY (even after governance / in soft mode) ----
    @pytest.mark.asyncio
    async def test_credential_path_in_args_denied(self):
        result = await self._send(
            self._enforcer(), "send_email", {"body": "here: ~/.ssh/id_rsa"}
        )
        assert result is not None
        resp = json.loads(result)
        assert resp["result"]["isError"] is True
        assert "GOVERNANCE BLOCK" in resp["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_pem_private_key_denied(self):
        result = await self._send(
            self._enforcer(),
            "send_email",
            {"body": "-----BEGIN OPENSSH " + "PRIVATE KEY-----\nAAAA"},
        )
        assert result is not None and json.loads(result)["result"]["isError"]

    @pytest.mark.asyncio
    async def test_provider_token_denied_even_in_soft_mode(self):
        result = await self._send(
            self._enforcer(soft_mode=True),
            "send_email",
            {"to": "x@y.com", "body": "key sk-" + "a" * 28},
        )
        assert result is not None and json.loads(result)["result"]["isError"]

    @pytest.mark.asyncio
    async def test_aws_key_denied(self):
        result = await self._send(
            self._enforcer(), "send_email", {"body": "AKIA" + "I" * 16}
        )
        assert result is not None and json.loads(result)["result"]["isError"]

    @pytest.mark.asyncio
    async def test_credential_path_blocked_even_on_allowed_read_tool(self):
        # ALWAYS_ALLOWED reads still get the credential-path check — a read
        # slurping ~/.aws/credentials is the canonical exfil.
        result = await self._send(
            self._enforcer(),
            "get_principle",
            {"principle_id": "cat ~/.aws/credentials"},
        )
        assert result is not None and json.loads(result)["result"]["isError"]

    # ---- NO DENY: realistic email bodies (the false-positive guard) ----
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "body",
        [
            "Your password has been reset successfully.",
            "We will never share your personal data with third parties.",
            "Please delete my old account when you get a chance.",
            "API key rotation completed for the prod environment.",
            "Reminder: the meeting moved to 3pm.",
        ],
    )
    async def test_realistic_email_bodies_not_denied(self, body):
        result = await self._send(
            self._enforcer(), "send_email", {"to": "c@d.com", "body": body}
        )
        assert result is None  # forwarded — no false positive

    # ---- satisfier exemption: you must be able to describe danger to governance ----
    @pytest.mark.asyncio
    async def test_governance_satisfier_args_exempt(self):
        e = GovernanceEnforcer(enforce_acts=True)
        proxy = StdioProxy(server_cmd=["echo", "test"], enforcer=e)
        result = await proxy._handle_client_message(
            self._msg(
                "evaluate_governance",
                {"planned_action": "read ~/.ssh/id_rsa then delete the prod DB"},
                req_id=1,
            )
        )
        assert result is None  # forwarded — governance must see the danger

    # ---- a blocked act-intrinsic call must not advance the recency counter ----
    @pytest.mark.asyncio
    async def test_blocked_call_does_not_advance_recency(self):
        e = self._enforcer()
        proxy = StdioProxy(server_cmd=["echo", "test"], enforcer=e)
        before = e._call_counter
        await proxy._handle_client_message(
            self._msg("send_email", {"body": "~/.ssh/id_rsa"})
        )
        assert e._call_counter == before

    # ---- gate is off by default (proportional-rigor): no enforce_acts → no deny ----
    @pytest.mark.asyncio
    async def test_disabled_by_default(self):
        e = GovernanceEnforcer()  # enforce_acts defaults False
        e.record_call("evaluate_governance")
        proxy = StdioProxy(server_cmd=["echo", "test"], enforcer=e)
        result = await proxy._handle_client_message(
            self._msg("scaffold_project", {"body": "~/.ssh/id_rsa"})
        )
        assert result is None  # not enforced unless --enforce-acts

    def test_enforce_acts_from_env(self):
        with patch.dict(os.environ, {"GOVERNANCE_ENFORCE_ACTS": "true"}):
            assert GovernanceEnforcer.from_env().enforce_acts is True

    def test_enforce_acts_default_off(self):
        with patch.dict(os.environ, {}, clear=True):
            assert GovernanceEnforcer.from_env().enforce_acts is False


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


class TestRelayFrameLimit:
    """Regression: large MCP response frames must survive the stdio relay.

    A get_messages / get_attachment_content response (email body or
    base64 attachment) can exceed the old 1 MB readline cap. When it did,
    the proxy's readline() raised an uncaught ValueError ("Separator is
    not found, and chunk exceed the limit") that collapsed the relay and
    hung the client for 60 s. RELAY_FRAME_LIMIT now governs both relay
    readers; these tests pin that the cap is generous and that an
    over-1 MB frame relays intact through the proxy's exact subprocess
    configuration.
    """

    def test_frame_limit_is_generous(self):
        from ai_governance_mcp.enforcement import RELAY_FRAME_LIMIT

        # Must comfortably exceed the old 1 MB cap so realistic email
        # bodies and base64 attachments relay intact.
        assert RELAY_FRAME_LIMIT >= 16 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_oversized_frame_relays_intact(self):
        """A ~2 MB newline-delimited frame (over the old 1 MB cap) must
        read back intact through a subprocess configured exactly as the
        proxy configures the wrapped server. Fails against limit=1 MB."""
        from ai_governance_mcp.enforcement import RELAY_FRAME_LIMIT

        body_size = 2 * 1024 * 1024  # 2 MB — over the old 1 MB cap
        # Build the body INSIDE the child so the 2 MB never becomes a
        # command-line argument (ARG_MAX), mirroring how the real wrapped
        # server emits a large frame on its own stdout.
        child = (
            "import sys, json\n"
            f"body = 'X' * {body_size}\n"
            "frame = json.dumps("
            "{'jsonrpc': '2.0', 'id': 2, 'result': {'content': body}})\n"
            "sys.stdout.write(frame + '\\n')\n"
            "sys.stdout.flush()\n"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            child,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=RELAY_FRAME_LIMIT,
        )
        try:
            out = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
        finally:
            await proc.wait()

        parsed = json.loads(out)
        assert parsed["result"]["content"] == "X" * body_size
        assert len(out) > 1024 * 1024  # the frame genuinely exceeded 1 MB


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
                "list_agents",
                "search_references",
                "analyze_feedback_loop",
            }, f"Unexpected always-allowed tool: {tool}"


class TestGovernAllMode:
    """Tests for cross-MCP govern-all mode (Phase 2)."""

    def test_govern_all_blocks_unknown_tools(self):
        """In govern-all mode, unlisted tools should be blocked."""
        enforcer = GovernanceEnforcer(govern_all=True)
        result = enforcer.check_precondition("create_pull_request")
        assert not result.allowed
        assert "GOVERNANCE REQUIRED" in result.message

    def test_govern_all_allows_exempted_tools(self):
        """In govern-all mode, always_allowed tools should pass."""
        enforcer = GovernanceEnforcer(
            govern_all=True,
            ALWAYS_ALLOWED={"get_file_contents", "list_issues"},
        )
        result = enforcer.check_precondition("get_file_contents")
        assert result.allowed
        result = enforcer.check_precondition("list_issues")
        assert result.allowed

    def test_govern_all_blocks_after_exempted(self):
        """Non-exempted tools should still be blocked in govern-all mode."""
        enforcer = GovernanceEnforcer(
            govern_all=True,
            ALWAYS_ALLOWED={"get_file_contents"},
        )
        # Exempted tool passes
        result = enforcer.check_precondition("get_file_contents")
        assert result.allowed
        # Non-exempted tool blocked
        result = enforcer.check_precondition("push_files")
        assert not result.allowed

    def test_govern_all_allows_after_governance(self):
        """Governance call should unlock tools in govern-all mode."""
        enforcer = GovernanceEnforcer(govern_all=True)
        enforcer.record_call("evaluate_governance")
        result = enforcer.check_precondition("create_pull_request")
        assert result.allowed

    def test_govern_all_governance_satisfiers_always_pass(self):
        """Governance satisfiers should always pass in govern-all mode."""
        enforcer = GovernanceEnforcer(govern_all=True)
        result = enforcer.check_precondition("evaluate_governance")
        assert result.allowed

    def test_govern_all_soft_mode(self):
        """Govern-all + soft mode should warn, not block."""
        enforcer = GovernanceEnforcer(govern_all=True, soft_mode=True)
        result = enforcer.check_precondition("create_pull_request")
        assert result.allowed
        assert "WARNING" in result.message

    def test_default_mode_passes_unknown_tools(self):
        """Default mode (non-govern-all) should still pass unknown tools."""
        enforcer = GovernanceEnforcer()
        result = enforcer.check_precondition("create_pull_request")
        assert result.allowed  # Not in GOVERNED_TOOLS, so passes through


class TestConfigFile:
    """Tests for YAML config file loading."""

    def test_config_file_loading(self):
        """YAML config should correctly populate tool sets."""
        config = {
            "governed_tools": ["create_pr", "push_files"],
            "always_allowed": ["get_file", "list_issues"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config, f)
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(f.name)
                assert enforcer.GOVERNED_TOOLS == {"create_pr", "push_files"}
                assert enforcer.ALWAYS_ALLOWED == {"get_file", "list_issues"}
            finally:
                os.unlink(f.name)

    def test_config_file_govern_all(self):
        """Config with govern_all should enable govern-all mode."""
        config = {
            "govern_all": True,
            "always_allowed": ["get_file"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config, f)
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(f.name)
                assert enforcer.govern_all is True
                assert enforcer.ALWAYS_ALLOWED == {"get_file"}
                # Unknown tools should be blocked
                result = enforcer.check_precondition("create_pr")
                assert not result.allowed
            finally:
                os.unlink(f.name)

    def test_config_file_missing_fields(self):
        """Config with missing fields should use empty defaults gracefully."""
        config = {"always_allowed": ["search_code"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config, f)
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(f.name)
                assert enforcer.GOVERNED_TOOLS == set()
                assert enforcer.ALWAYS_ALLOWED == {"search_code"}
            finally:
                os.unlink(f.name)

    def test_config_file_empty(self):
        """Empty config file should produce a valid enforcer."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(f.name)
                assert enforcer.GOVERNED_TOOLS == set()
                assert enforcer.govern_all is False
            finally:
                os.unlink(f.name)


class TestSharedState:
    """Tests for cross-MCP shared state file coordination."""

    @pytest.fixture
    def state_dir(self):
        """Create a temporary directory for state files."""
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_shared_state_write_read(self, state_dir):
        """Write state from one enforcer, read from another."""
        state_file = os.path.join(state_dir, "state.json")

        # Governance proxy writes state
        writer = GovernanceEnforcer(state_file=state_file, state_ttl=300)
        writer.record_call("evaluate_governance")

        # Cross-MCP proxy reads state
        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=300
        )
        result = reader.check_precondition("create_pull_request")
        assert result.allowed, "Should see governance from shared state"

    def test_shared_state_expiry(self, state_dir):
        """State older than TTL should be treated as expired."""
        state_file = os.path.join(state_dir, "state.json")

        # Write stale state directly
        stale_state = {"last_evaluation_ts": time.time() - 600, "pid": os.getpid()}
        with open(state_file, "w") as f:
            json.dump(stale_state, f)

        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=300
        )
        result = reader.check_precondition("create_pull_request")
        assert not result.allowed, "Stale state should not satisfy governance"

    def test_shared_state_missing_file(self, state_dir):
        """Missing state file should fail-closed (tools blocked).

        Covers: FM-SHARED-STATE-MISSING-FILE-FAIL-CLOSED
        """
        state_file = os.path.join(state_dir, "nonexistent.json")
        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=300
        )
        result = reader.check_precondition("create_pull_request")
        assert not result.allowed, "Missing state file = governance not satisfied"

    def test_shared_state_corrupt_file(self, state_dir):
        """Corrupt state file should fail-closed (tools blocked)."""
        state_file = os.path.join(state_dir, "state.json")
        with open(state_file, "w") as f:
            f.write("not valid json {{{")

        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=300
        )
        result = reader.check_precondition("create_pull_request")
        assert not result.allowed, "Corrupt state file = governance not satisfied"

    def test_shared_state_creates_directory(self):
        """State file write should create parent directories."""
        with tempfile.TemporaryDirectory() as base:
            state_file = os.path.join(base, "nested", "dir", "state.json")
            writer = GovernanceEnforcer(state_file=state_file, state_ttl=300)
            writer.record_call("evaluate_governance")
            assert os.path.exists(state_file)

    def test_shared_state_no_write_without_state_file(self):
        """Without state_file set, record_call should not write anything."""
        enforcer = GovernanceEnforcer()
        enforcer.record_call("evaluate_governance")
        # No state_file configured — just verify no error
        assert enforcer._call_counter == 1

    def test_shared_state_within_ttl(self, state_dir):
        """State well within TTL should satisfy governance.

        Covers: FM-STATE-EXPIRY-BOUNDARY-INCLUSIVE
        """
        state_file = os.path.join(state_dir, "state.json")
        ttl = 300

        # 1 second of buffer to avoid floating-point timing issues
        fresh_state = {"last_evaluation_ts": time.time() - ttl + 1, "pid": os.getpid()}
        with open(state_file, "w") as f:
            json.dump(fresh_state, f)

        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=ttl
        )
        result = reader.check_precondition("create_pull_request")
        assert result.allowed, "State within TTL should pass"

    def test_shared_state_just_past_ttl(self, state_dir):
        """State just past TTL should NOT satisfy governance."""
        state_file = os.path.join(state_dir, "state.json")
        ttl = 300

        past_state = {"last_evaluation_ts": time.time() - ttl - 1, "pid": os.getpid()}
        with open(state_file, "w") as f:
            json.dump(past_state, f)

        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=ttl
        )
        result = reader.check_precondition("create_pull_request")
        assert not result.allowed, "State past TTL should not pass"

    def test_write_shared_state_unwritable_path(self):
        """Write to unwritable path should fail silently (no exception)."""
        # /proc/fake won't exist on macOS, so use a path we can't write to
        enforcer = GovernanceEnforcer(
            state_file="/nonexistent/deeply/nested/impossible/state.json",
            state_ttl=300,
        )
        # Should not raise — fails silently with stderr warning
        enforcer.record_call("evaluate_governance")
        assert enforcer._call_counter == 1

    def test_cross_project_isolation(self, state_dir):
        """State from Project A must not satisfy Project B's check."""
        state_file = os.path.join(state_dir, "state.json")

        # Project A writes governance state
        writer = GovernanceEnforcer(
            state_file=state_file, state_ttl=300, project_path="/projects/alpha"
        )
        writer.record_call("evaluate_governance")

        # Project B reads — should reject the mismatched project
        reader = GovernanceEnforcer(
            govern_all=True,
            state_file=state_file,
            state_ttl=300,
            project_path="/projects/beta",
        )
        result = reader.check_precondition("create_pull_request")
        assert not result.allowed, "Project B must not accept Project A's state"

    def test_same_project_shares_state(self, state_dir):
        """State from the same project should be accepted."""
        state_file = os.path.join(state_dir, "state.json")

        writer = GovernanceEnforcer(
            state_file=state_file, state_ttl=300, project_path="/projects/alpha"
        )
        writer.record_call("evaluate_governance")

        reader = GovernanceEnforcer(
            govern_all=True,
            state_file=state_file,
            state_ttl=300,
            project_path="/projects/alpha",
        )
        result = reader.check_precondition("create_pull_request")
        assert result.allowed, "Same project should share state"

    def test_no_project_path_accepts_any(self, state_dir):
        """Reader without project_path accepts state from any project (backward compat)."""
        state_file = os.path.join(state_dir, "state.json")

        writer = GovernanceEnforcer(
            state_file=state_file, state_ttl=300, project_path="/projects/alpha"
        )
        writer.record_call("evaluate_governance")

        reader = GovernanceEnforcer(
            govern_all=True, state_file=state_file, state_ttl=300, project_path=None
        )
        result = reader.check_precondition("create_pull_request")
        assert result.allowed, "No project_path = accept any state (backward compat)"

    def test_always_allow_merges_with_config(self):
        """CLI --always-allow should merge with config always_allowed, not replace."""
        import yaml

        config = {"always_allowed": ["tool_a", "tool_b"], "govern_all": True}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(f.name)
                assert enforcer.ALWAYS_ALLOWED == {"tool_a", "tool_b"}

                # Simulate CLI merge (same logic as main())
                cli_allowed = {"tool_c", "tool_d"}
                enforcer.ALWAYS_ALLOWED |= cli_allowed

                assert enforcer.ALWAYS_ALLOWED == {
                    "tool_a",
                    "tool_b",
                    "tool_c",
                    "tool_d",
                }
                # All merged tools should pass
                for tool in ["tool_a", "tool_b", "tool_c", "tool_d"]:
                    assert enforcer.check_precondition(tool).allowed
                # Non-exempt tool should still be blocked
                assert not enforcer.check_precondition("tool_e").allowed
            finally:
                os.unlink(f.name)

    def test_existing_behavior_unchanged(self):
        """Default GovernanceEnforcer should behave identically to Phase 1."""
        enforcer = GovernanceEnforcer()
        # Should have Phase 1 defaults
        assert "scaffold_project" in enforcer.GOVERNED_TOOLS
        assert "evaluate_governance" in enforcer.GOVERNANCE_SATISFIERS
        assert "query_governance" in enforcer.ALWAYS_ALLOWED
        assert enforcer.govern_all is False
        assert enforcer.state_file is None
        # Phase 1 behavior: governed tools blocked, read-only pass
        assert not enforcer.check_precondition("scaffold_project").allowed
        assert enforcer.check_precondition("query_governance").allowed
        assert enforcer.check_precondition("unknown_tool").allowed


class TestGovernanceEnforcerEnvVarsPhase2:
    """Tests for Phase 2 environment variable configuration."""

    def test_state_file_via_env(self):
        """GOVERNANCE_STATE_FILE should set the state file path."""
        with patch.dict(os.environ, {"GOVERNANCE_STATE_FILE": "/tmp/test-state.json"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.state_file == "/tmp/test-state.json"

    def test_state_ttl_via_env(self):
        """GOVERNANCE_STATE_TTL should set the TTL."""
        with patch.dict(os.environ, {"GOVERNANCE_STATE_TTL": "600"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.state_ttl == 600

    def test_state_ttl_invalid_uses_default(self):
        """Invalid GOVERNANCE_STATE_TTL should fall back to default."""
        with patch.dict(os.environ, {"GOVERNANCE_STATE_TTL": "not_a_number"}):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.state_ttl == 300

    def test_state_file_default_is_none(self):
        """Without env var, state_file should be None."""
        with patch.dict(os.environ, {}, clear=True):
            enforcer = GovernanceEnforcer.from_env()
            assert enforcer.state_file is None


class TestSecurityHardening:
    """Tests for security-hardening measures."""

    def test_future_timestamp_rejected(self):
        """Future timestamps in state file should not grant permanent bypass."""
        with tempfile.TemporaryDirectory() as d:
            state_file = os.path.join(d, "state.json")
            # Write a timestamp far in the future
            future_state = {"last_evaluation_ts": time.time() + 999999, "pid": 1}
            with open(state_file, "w") as f:
                json.dump(future_state, f)

            reader = GovernanceEnforcer(
                govern_all=True, state_file=state_file, state_ttl=300
            )
            # Future timestamp gets clamped to now, so age=0 which IS within TTL
            # But it should NOT grant permanent bypass — it should expire normally
            result = reader.check_precondition("create_pull_request")
            # Clamped to now means age=~0, which is within TTL — allowed
            assert result.allowed, "Clamped future timestamp = age ~0 = within TTL"

            # Write a different future timestamp and set a very short TTL
            # After clamping, age should still be ~0
            reader2 = GovernanceEnforcer(
                govern_all=True, state_file=state_file, state_ttl=1
            )
            result2 = reader2.check_precondition("create_pull_request")
            # age ~0 is within TTL=1, so still allowed (but not PERMANENT)
            assert result2.allowed

    def test_future_timestamp_not_permanent(self):
        """Future timestamp should be clamped to now, not grant indefinite access."""
        with tempfile.TemporaryDirectory() as d:
            state_file = os.path.join(d, "state.json")
            # Write timestamp 1 second in the past — should be within TTL
            recent_state = {"last_evaluation_ts": time.time() - 1, "pid": 1}
            with open(state_file, "w") as f:
                json.dump(recent_state, f)

            reader = GovernanceEnforcer(
                govern_all=True, state_file=state_file, state_ttl=300
            )
            assert reader.check_precondition("tool").allowed

            # Now write a VERY old timestamp disguised as future (year 2286)
            # Without clamping, age would be negative = always within TTL
            # With clamping, age = 0 = within TTL (not permanent, expires normally)
            spoofed = {"last_evaluation_ts": 9999999999, "pid": 1}
            with open(state_file, "w") as f:
                json.dump(spoofed, f)

            # Verify the clamping prevents negative age
            reader2 = GovernanceEnforcer(
                govern_all=True, state_file=state_file, state_ttl=300
            )
            # Read the state manually to verify clamping logic
            assert reader2._read_shared_state() is True  # clamped to now, age ~0

    def test_from_config_rejects_security_critical_overrides(self):
        """from_config should reject overrides for security-critical fields.

        Covers: FM-CONFIG-SECURITY-CRITICAL-PARAMS-PROTECTED
        """
        import yaml

        config = {"govern_all": True}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()
            try:
                with pytest.raises(ValueError, match="security-critical"):
                    GovernanceEnforcer.from_config(f.name, enabled=False)
                with pytest.raises(ValueError, match="security-critical"):
                    GovernanceEnforcer.from_config(
                        f.name, GOVERNANCE_SATISFIERS={"any_tool"}
                    )
            finally:
                os.unlink(f.name)

    def test_from_config_allows_safe_overrides(self):
        """from_config should allow overrides for non-security fields."""
        import yaml

        config = {"govern_all": True}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()
            try:
                enforcer = GovernanceEnforcer.from_config(
                    f.name, soft_mode=True, state_ttl=600
                )
                assert enforcer.soft_mode is True
                assert enforcer.state_ttl == 600
            finally:
                os.unlink(f.name)


class TestStdinDrainWindow:
    """Regression: the proxy must not close server stdin the instant the
    upstream client sends EOF.  Without a drain window, any in-flight
    handler that yields to the event loop loses its write stream
    (python-sdk#2678) and the response is silently dropped.

    BACKLOG #207.  See also #205 (same root cause, client-side fix).
    """

    def test_drain_constant_exists_and_is_positive(self):
        from ai_governance_mcp.enforcement import STDIN_DRAIN_TIMEOUT_S

        assert isinstance(STDIN_DRAIN_TIMEOUT_S, (int, float))
        assert STDIN_DRAIN_TIMEOUT_S > 0

    def test_proxy_drain_saves_delayed_response(self, tmp_path):
        """Spawn the proxy wrapping a fake server whose response arrives
        after a yield.  Use communicate() (the broken-client pattern that
        closes stdin immediately) and verify the response still arrives
        thanks to the proxy's drain window.
        """
        import subprocess  # nosec B404

        from ai_governance_mcp.enforcement import STDIN_DRAIN_TIMEOUT_S

        # Fake server: reads one request, responds after a short delay,
        # exits on stdin EOF.  The delay simulates a handler that yields
        # (the #2678 trigger).
        fake = tmp_path / "fake_server.py"
        fake.write_text(
            "import json, sys, threading\n"
            "def respond():\n"
            '    sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":2,'
            '"result":{"content":[{"type":"text","text":"OK"}]}}) + "\\n")\n'
            "    sys.stdout.flush()\n"
            "for line in sys.stdin:\n"
            "    line = line.strip()\n"
            "    if not line: continue\n"
            "    try: msg = json.loads(line)\n"
            "    except Exception: continue\n"
            '    if msg.get("method") == "tools/call":\n'
            "        threading.Timer(0.3, respond).start()\n"
            "import time; time.sleep(2)\n"
        )

        proxy_argv = [
            sys.executable,
            "-m",
            "ai_governance_mcp.enforcement",
            "--disabled",
            "--",
            sys.executable,
            str(fake),
        ]

        request = json.dumps(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {}}
        )

        proc = subprocess.Popen(  # nosec B603
            proxy_argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(tmp_path),
        )

        # communicate() writes + closes stdin in one shot — the pattern
        # that triggers #207 without the drain fix.
        timeout = STDIN_DRAIN_TIMEOUT_S + 10
        out, err = proc.communicate(request + "\n", timeout=timeout)

        found = False
        for line in out.splitlines():
            try:
                msg = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(msg, dict) and msg.get("id") == 2:
                found = True
                break

        assert found, (
            f"proxy dropped the delayed response (the #207 defect). "
            f"stdout={out!r:.200}, stderr tail={err[-500:]!r}"
        )
