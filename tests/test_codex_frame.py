"""Unit tests for ai_governance_mcp.codex_frame — the Codex UserPromptSubmit FRAME hook.

Injects the behavioral-floor FRAME as developer context each turn, in EVERY project
(global — the floor is unconditional; the user wants ai-governance active regardless of
project). Never blocks a prompt. Off-switch: FRAME_INJECT_INTERVAL=0.

Run targeted (``pytest tests/test_codex_frame.py``) — stdlib-only, a bare ``pytest``
token trips the OOM gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from ai_governance_mcp.frame import FRAME

MODULE = "ai_governance_mcp.codex_frame"


def run_hook(
    payload: dict | None = None,
    *,
    raw: str | None = None,
    env_overrides: dict[str, str] | None = None,
    extra_args: list[str] | None = None,
    run_cwd: str = "/",
) -> tuple[int, dict | None]:
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
        cwd=run_cwd,
        timeout=30,
    )
    response = None
    if result.stdout.strip():
        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            pass
    return result.returncode, response


def _additional_context(resp: dict | None):
    if not resp:
        return None
    return resp.get("hookSpecificOutput", {}).get("additionalContext")


# ---------------------------------------------------------------------------
# Global injection — fires in every project, regardless of markers
# ---------------------------------------------------------------------------


class TestGlobalInjection:
    def test_injects_with_cwd(self, tmp_path) -> None:
        rc, resp = run_hook({"cwd": str(tmp_path)})
        assert rc == 0
        assert _additional_context(resp) == FRAME
        assert resp["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    def test_injects_in_non_framework_dir(self, tmp_path) -> None:
        # No SESSION-STATE.md / PROJECT-MEMORY.md anywhere — must STILL inject (global).
        rc, resp = run_hook({"cwd": str(tmp_path)}, run_cwd=str(tmp_path))
        assert _additional_context(resp) == FRAME

    def test_injects_when_cwd_missing(self) -> None:
        rc, resp = run_hook({"some": "payload"})
        assert _additional_context(resp) == FRAME

    def test_injects_on_empty_stdin(self) -> None:
        rc, resp = run_hook(raw="")
        assert rc == 0
        assert _additional_context(resp) == FRAME

    def test_injects_on_malformed_json(self) -> None:
        rc, resp = run_hook(raw="not json at all")
        assert _additional_context(resp) == FRAME


# ---------------------------------------------------------------------------
# Off-switch + never-block
# ---------------------------------------------------------------------------


class TestOffSwitchAndNeverBlock:
    def test_interval_zero_disables(self, tmp_path) -> None:
        rc, resp = run_hook(
            {"cwd": str(tmp_path)}, env_overrides={"FRAME_INJECT_INTERVAL": "0"}
        )
        assert rc == 0
        assert resp is None

    def test_never_emits_block(self) -> None:
        # A UserPromptSubmit block is {"decision":"block"} — this hook must never do that.
        rc, resp = run_hook(raw="{bad json")
        assert rc == 0
        assert resp is None or resp.get("decision") != "block"


# ---------------------------------------------------------------------------
# Capture recon
# ---------------------------------------------------------------------------


class TestCapture:
    def test_capture_flag_records_inject(self, tmp_path) -> None:
        dest = tmp_path / "cap.jsonl"
        run_hook({"cwd": str(tmp_path)}, extra_args=["--capture", str(dest)])
        assert dest.exists()
        line = json.loads(dest.read_text().strip())
        assert line["decision"] == "inject"
        assert line["cwd"] == str(tmp_path)

    def test_capture_off_by_default(self, tmp_path) -> None:
        run_hook({"cwd": str(tmp_path)})
        assert not (tmp_path / "cap.jsonl").exists()


# ---------------------------------------------------------------------------
# Import isolation — the per-turn hot-path guard
# ---------------------------------------------------------------------------


class TestImportIsolation:
    def test_no_heavy_modules(self) -> None:
        code = (
            "import sys\n"
            "import ai_governance_mcp.codex_frame\n"
            "heavy = [m for m in "
            "('torch', 'transformers', 'sentence_transformers', 'numpy') "
            "if m in sys.modules]\n"
            "assert not heavy, f'heavy modules loaded: {heavy}'\n"
            "assert 'ai_governance_mcp.server' not in sys.modules\n"
            "assert 'ai_governance_mcp.frame' in sys.modules\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
