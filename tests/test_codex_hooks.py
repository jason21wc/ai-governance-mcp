"""Unit tests for ai_governance_mcp.codex_hooks — the Codex CLI PreToolUse gate.

Ports the act-intrinsic content-security enforcement to OpenAI Codex CLI. The
module reads a Codex PreToolUse JSON payload on stdin and DENIES (Codex deny
contract: ``permissionDecision: "deny"`` on stdout + exit 2) when the tool call's
argument VALUES carry a secret value or credential path, via the shared
``safety_scan`` core. See BACKLOG #176a / plan misty-waddling-hellman.md.

Test coverage:
  1. Deny — secret VALUES (the unique surface vs the OS sandbox path-deny).
  2. Deny — credential paths (defense-in-depth half).
  3. Allow — benign commands.
  4. Payload-shape robustness — secret under varied/unknown wrapper keys.
  5. Fail-closed on malformed JSON; empty stdin allows.
  6. Bypass env var + audit log.
  7. Governance/MCP self-deny guard.
  8. Deny-message shape.
  9. Import isolation — no heavy modules; fast cold-start (the hot-path guard).

Run targeted (``pytest tests/test_codex_hooks.py``) — stdlib-only, no ``slow``
marker, but a bare ``pytest`` token trips the OOM gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from tests.hook_fixtures import is_allow, is_deny

MODULE = "ai_governance_mcp.codex_hooks"

# Fake-but-well-formed secret VALUES (matching safety_scan._SECRET_VALUE_PATTERNS).
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
OPENAI_KEY = "sk-proj-" + "A1b2C3d4E5f6G7h8I9j0K1l2"
GITHUB_TOKEN = "ghp_" + "a" * 36
PEM = "-----BEGIN RSA PRIVATE KEY-----"


def run_hook(
    payload: dict | None = None,
    *,
    raw: str | None = None,
    env_overrides: dict[str, str] | None = None,
    extra_args: list[str] | None = None,
) -> tuple[int, dict | None]:
    """Invoke the module as a subprocess with a JSON (or raw) stdin payload."""
    stdin = raw if raw is not None else json.dumps(payload)
    env = {**os.environ}
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-m", MODULE, *(extra_args or [])],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    response = None
    if result.stdout.strip():
        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            pass
    return result.returncode, response


def _bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


# ---------------------------------------------------------------------------
# 1. Deny — secret VALUES (the hook's unique surface: the sandbox is blind here)
# ---------------------------------------------------------------------------


class TestSecretValueDeny:
    @pytest.mark.parametrize(
        "secret",
        [AWS_KEY, OPENAI_KEY, GITHUB_TOKEN, PEM],
        ids=["aws-key", "openai-key", "github-token", "pem-block"],
    )
    def test_deny_secret_value_in_bash(self, secret: str) -> None:
        rc, resp = run_hook(_bash(f"echo {secret} >> notes.txt"))
        assert is_deny(resp), f"Expected deny for secret value: {secret[:12]}…"
        assert rc == 2

    def test_deny_secret_value_in_apply_patch(self) -> None:
        payload = {
            "tool_name": "apply_patch",
            "tool_input": {"patch": f"+++ config\n+API_KEY={AWS_KEY}\n"},
        }
        rc, resp = run_hook(payload)
        assert is_deny(resp)


# ---------------------------------------------------------------------------
# 2. Deny — credential paths (defense-in-depth; sandbox-redundant)
# ---------------------------------------------------------------------------


class TestCredentialPathDeny:
    @pytest.mark.parametrize(
        "command",
        [
            "cat ~/.ssh/id_rsa",
            "cat $HOME/.aws/credentials",
            "cat ${HOME}/.gnupg/secring.gpg",
            "cat /etc/ssl/private/server.key",
        ],
        ids=["ssh", "aws-dollar-home", "gnupg-braced", "etc-ssl"],
    )
    def test_deny_credential_path(self, command: str) -> None:
        rc, resp = run_hook(_bash(command))
        assert is_deny(resp), f"Expected deny for: {command}"


# ---------------------------------------------------------------------------
# 3. Allow — benign commands
# ---------------------------------------------------------------------------


class TestBenignAllow:
    @pytest.mark.parametrize(
        "command",
        [
            "ls -la",
            "git status",
            "grep -r ssh src/",
            "echo hello world",
            "python3 -c 'print(1)'",
        ],
        ids=["ls", "git-status", "grep-ssh", "echo", "python"],
    )
    def test_allow_benign(self, command: str) -> None:
        rc, resp = run_hook(_bash(command))
        assert is_allow(resp, rc), f"Expected allow for: {command}"


# ---------------------------------------------------------------------------
# 4. Payload-shape robustness — the leaf-walk catches the secret regardless of
#    Codex's actual field name (unverified until phase-1 capture).
# ---------------------------------------------------------------------------


class TestPayloadShapeRobustness:
    @pytest.mark.parametrize(
        "payload",
        [
            {"tool_input": {"command": f"echo {AWS_KEY}"}},
            {"arguments": {"cmd": f"echo {AWS_KEY}"}},
            {"input": {"x": {"y": f"echo {AWS_KEY}"}}},
            {"params": {"arguments": {"z": f"echo {AWS_KEY}"}}},
            {"some_unknown_wrapper": {"deep": {"field": f"echo {AWS_KEY}"}}},
        ],
        ids=[
            "tool_input",
            "arguments",
            "nested-input",
            "params-arguments",
            "unknown-key",
        ],
    )
    def test_deny_regardless_of_field_name(self, payload: dict) -> None:
        rc, resp = run_hook(payload)
        assert is_deny(resp), f"Expected deny for shape: {list(payload)}"


# ---------------------------------------------------------------------------
# 5. Fail-closed on malformed JSON; empty stdin allows
# ---------------------------------------------------------------------------


class TestFailClosed:
    def test_malformed_json_with_secret_denies(self) -> None:
        rc, resp = run_hook(raw=f"this is not json but contains {AWS_KEY} somewhere")
        assert is_deny(resp), "Malformed JSON carrying a secret must still deny"

    def test_malformed_json_benign_allows(self) -> None:
        rc, resp = run_hook(raw="this is not json and is benign")
        assert is_allow(resp, rc)

    def test_empty_stdin_allows(self) -> None:
        rc, resp = run_hook(raw="")
        assert is_allow(resp, rc)

    def test_whitespace_stdin_allows(self) -> None:
        rc, resp = run_hook(raw="   \n  ")
        assert is_allow(resp, rc)


# ---------------------------------------------------------------------------
# 6. Bypass + audit
# ---------------------------------------------------------------------------


class TestBypass:
    def test_bypass_allows_secret(self) -> None:
        rc, resp = run_hook(
            _bash(f"echo {AWS_KEY}"),
            env_overrides={"CONTENT_SECURITY_SKIP": "1"},
        )
        assert is_allow(resp, rc)

    def test_bypass_emits_warning(self) -> None:
        rc, resp = run_hook(
            _bash(f"echo {AWS_KEY}"),
            env_overrides={"CONTENT_SECURITY_SKIP": "1"},
        )
        assert resp is not None
        ctx = resp.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "bypass" in ctx.lower() or "CONTENT_SECURITY_SKIP" in ctx

    def test_bypass_writes_audit_log(self, tmp_path) -> None:
        run_hook(
            _bash(f"echo {AWS_KEY}"),
            env_overrides={"CONTENT_SECURITY_SKIP": "1", "HOME": str(tmp_path)},
        )
        log_file = tmp_path / ".claude" / "hook-bypass-audit.log"
        assert log_file.exists(), "bypass should write the shared audit log"
        content = log_file.read_text()
        assert "codex_hooks" in content
        assert "CONTENT_SECURITY_SKIP=1" in content


# ---------------------------------------------------------------------------
# 7. Governance/MCP self-deny guard — a governance MCP call whose args describe a
#    credential path must NOT be denied by this hook.
# ---------------------------------------------------------------------------


class TestGovernanceSelfDenyGuard:
    def test_evaluate_governance_path_in_planned_action_allowed(self) -> None:
        payload = {
            "tool_name": "mcp__ai-governance__evaluate_governance",
            "tool_input": {"planned_action": "rotate the key in ~/.ssh/config"},
        }
        rc, resp = run_hook(payload)
        assert is_allow(resp, rc), "governance MCP call must not self-deny"

    def test_query_project_call_allowed(self) -> None:
        payload = {
            "tool_name": "mcp__context-engine__query_project",
            "tool_input": {"query": "where do we read ~/.aws/credentials"},
        }
        rc, resp = run_hook(payload)
        assert is_allow(resp, rc)

    def test_bash_still_denied_even_named_like_tool(self) -> None:
        # A real Bash call carrying a secret is still denied (guard is name-scoped).
        rc, resp = run_hook(_bash(f"echo {AWS_KEY}"))
        assert is_deny(resp)

    def test_non_governance_mcp_tool_with_secret_denied(self) -> None:
        # Session-240 cross-vendor finding: a blanket mcp__ exemption let ANY MCP
        # tool carry a secret past the scan. Only the exact governance/CE names
        # are exempt now.
        payload = {
            "tool_name": "mcp__filesystem__write_file",
            "tool_input": {"path": "/tmp/x", "content": f"key={AWS_KEY}"},
        }
        rc, resp = run_hook(payload)
        assert is_deny(resp), "non-governance MCP tool must not bypass the scan"

    def test_lookalike_tool_name_not_exempt(self) -> None:
        # Substring matching would exempt "query_project_exfil"; exact/suffix
        # matching must not.
        payload = {
            "tool_name": "query_project_exfil",
            "tool_input": {"data": f"token={AWS_KEY}"},
        }
        rc, resp = run_hook(payload)
        assert is_deny(resp), "lookalike tool name must not be exempt"

    def test_bare_governance_tool_name_still_exempt(self) -> None:
        # Codex-side naming may drop the mcp__<server>__ prefix; the bare
        # satisfier name stays exempt.
        payload = {
            "tool_name": "evaluate_governance",
            "tool_input": {"planned_action": "audit ~/.aws/credentials handling"},
        }
        rc, resp = run_hook(payload)
        assert is_allow(resp, rc)

    def test_all_allowlisted_names_exempt_across_separator_shapes(self) -> None:
        # Pins every allowlist entry (incl. verify_governance_compliance) across
        # the separator shapes a host might use, plus case-insensitivity.
        names = [
            "mcp__ai-governance__verify_governance_compliance",
            "ai-governance.evaluate_governance",
            "ai-governance/query_project",
            "Mcp__Ai-Governance__Evaluate_Governance",
        ]
        for name in names:
            payload = {
                "tool_name": name,
                "tool_input": {"planned_action": "rotate ~/.ssh/id_rsa"},
            }
            rc, resp = run_hook(payload)
            assert is_allow(resp, rc), f"{name} must stay exempt (self-deny guard)"

    def test_dotted_lookalike_still_denied(self) -> None:
        # Separator widening must not reopen a substring hole.
        payload = {
            "tool_name": "evil.query_project_exfil",
            "tool_input": {"data": f"token={AWS_KEY}"},
        }
        rc, resp = run_hook(payload)
        assert is_deny(resp)


# ---------------------------------------------------------------------------
# 8. Deny-message shape
# ---------------------------------------------------------------------------


class TestDenyMessageShape:
    def test_deny_message_contract(self) -> None:
        rc, resp = run_hook(_bash(f"echo {AWS_KEY}"))
        hso = resp["hookSpecificOutput"]
        assert hso["hookEventName"] == "PreToolUse"
        assert hso["permissionDecision"] == "deny"
        reason = hso["permissionDecisionReason"].lower()
        assert "secret" in reason or "credential" in reason


# ---------------------------------------------------------------------------
# 8b. Capture mode — reconnaissance via --capture <path> (argv, preferred) or
#     CODEX_HOOK_CAPTURE (env, fallback). Argv wins so it does not depend on
#     Codex preserving the hook's environment.
# ---------------------------------------------------------------------------


class TestCaptureMode:
    def test_capture_flag_writes_payload(self, tmp_path) -> None:
        dest = tmp_path / "cap.jsonl"
        run_hook(_bash("ls -la"), extra_args=["--capture", str(dest)])
        assert dest.exists()
        line = json.loads(dest.read_text().strip())
        assert line["decision"] == "allow"
        assert "ls -la" in line["raw_stdin"]

    def test_capture_flag_records_deny(self, tmp_path) -> None:
        dest = tmp_path / "cap.jsonl"
        run_hook(_bash(f"echo {AWS_KEY}"), extra_args=["--capture", str(dest)])
        line = json.loads(dest.read_text().strip())
        assert line["decision"] == "deny"
        assert line["matched_reason"] is not None

    def test_capture_env_fallback(self, tmp_path) -> None:
        dest = tmp_path / "cap.jsonl"
        run_hook(_bash("ls -la"), env_overrides={"CODEX_HOOK_CAPTURE": str(dest)})
        assert dest.exists()

    def test_capture_off_by_default(self, tmp_path) -> None:
        # No --capture, no env → no capture file created anywhere under tmp.
        run_hook(_bash("ls -la"), env_overrides={"CODEX_HOOK_CAPTURE": ""})
        assert not list(tmp_path.iterdir())


# ---------------------------------------------------------------------------
# 9. Import isolation — the hot-path guard (contrarian change 2). A PreToolUse
#    hook runs on EVERY tool call; a future heavy import in __init__.py would
#    cold-start the embedding model each time. Spawn a FRESH interpreter so other
#    tests' imports don't pollute sys.modules.
# ---------------------------------------------------------------------------


class TestImportIsolation:
    def test_no_heavy_modules_loaded(self) -> None:
        code = (
            "import sys\n"
            "import ai_governance_mcp.codex_hooks\n"
            "heavy = [m for m in "
            "('torch', 'transformers', 'sentence_transformers', 'numpy') "
            "if m in sys.modules]\n"
            "assert not heavy, f'heavy modules loaded: {heavy}'\n"
            "assert 'ai_governance_mcp.server' not in sys.modules\n"
            "assert 'ai_governance_mcp.retrieval' not in sys.modules\n"
            "assert 'ai_governance_mcp.enforcement' not in sys.modules\n"
            "assert 'ai_governance_mcp.safety_scan' in sys.modules\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout

    def test_import_is_fast(self) -> None:
        # Import-only timing (excludes interpreter startup). Real is ~10ms; a torch
        # regression would be seconds. Lenient threshold to avoid CI jitter flakes.
        code = (
            "import time\n"
            "t = time.perf_counter()\n"
            "import ai_governance_mcp.codex_hooks\n"
            "dt = (time.perf_counter() - t) * 1000\n"
            "print(f'{dt:.1f}')\n"
            "assert dt < 1000, f'import too slow: {dt:.0f}ms (heavy import regression?)'\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stdout + result.stderr
