"""Tests for the SessionStart genesis-detector hook + shared genesis.sh library.

The hook (`.claude/hooks/session-start-genesis.sh`) fires at session start when a
directory looks like a real project (`.git` or source/doc files) but has NO
governance memory files (SESSION-STATE.md). It injects ONE advisory
`additionalContext` nudge that **inlines the minimal founding questions** — so the
model can act on the prose directly, since it cannot auto-invoke the user-only
`/start-project` skill (`disable-model-invocation: true`). The hook is stateless
and self-clearing (stops once memory files exist), suppressible (a
`.start-project-dismissed` marker or `START_PROJECT_NUDGE_*` env), and must never
block startup (always exit 0). It uses the nested `hookSpecificOutput` envelope
(the flat form is silently dropped by Claude Code — FM-HOOK-OUTPUT-ENVELOPE).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "session-start-genesis.sh"
GENESIS_LIB = REPO / ".claude" / "hooks" / "lib" / "genesis.sh"


def make_dir(
    tmp_path,
    *,
    git=False,
    sources=False,
    session_state=False,
    ai_context_state=False,
    dismissed=False,
    name="proj",
) -> Path:
    d = tmp_path / name
    d.mkdir()
    if git:
        (d / ".git").mkdir()
    if sources:
        (d / "main.py").write_text("print('x')\n")
    if session_state:
        (d / "SESSION-STATE.md").write_text("# state\n")
    if ai_context_state:
        ac = d / "_ai-context"
        ac.mkdir(exist_ok=True)
        (ac / "SESSION-STATE.md").write_text("# state\n")
    if dismissed:
        (d / ".start-project-dismissed").write_text("")
    return d


def run(source="startup", project_dir=None, env=None):
    payload = {"source": source}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    e = os.environ.copy()
    # Strip inherited genesis env + the real repo's CLAUDE_PROJECT_DIR.
    for k in list(e):
        if k.startswith("START_PROJECT_") or k == "CLAUDE_PROJECT_DIR":
            e.pop(k)
    if project_dir is not None:
        e["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env:
        e.update(env)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=e,
        timeout=15,
    )


def context(result):
    """Injected additionalContext, or None if silent. Asserts the nested envelope."""
    out = result.stdout.strip()
    if not out:
        return None
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]  # KeyError if someone reverts to the flat form
    assert hso["hookEventName"] == "SessionStart"
    return hso.get("additionalContext")


class TestSessionStartGenesisHook:
    def test_genesis_fires_when_no_memory_files(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        r = run(project_dir=d)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None and "/start-project" in ctx

    def test_nudge_inlines_founding_questions(self, tmp_path):
        # The contrarian fix: the nudge must carry the questions so the model can
        # act on prose directly (it cannot auto-invoke the user-only skill).
        d = make_dir(tmp_path, git=True)
        low = (context(run(project_dir=d)) or "").lower()
        for token in ("goal", "done", "non-goal", "document"):
            assert token in low, token

    def test_silent_when_session_state_exists(self, tmp_path):
        # Self-clearing: stops nudging once the project is onboarded.
        d = make_dir(tmp_path, git=True, session_state=True)
        assert context(run(project_dir=d)) is None

    def test_silent_in_non_project_folder(self, tmp_path):
        # FP guard: a bare scratch dir (no .git, no sources) stays silent.
        d = make_dir(tmp_path)
        assert context(run(project_dir=d)) is None

    def test_fires_when_source_files_present_no_git(self, tmp_path):
        d = make_dir(tmp_path, sources=True)
        assert context(run(project_dir=d)) is not None

    def test_document_genesis_fires_and_detects_type(self, tmp_path):
        d = tmp_path / "doc"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "brief.md").write_text("# brief\n")
        ctx = context(run(project_dir=d)) or ""
        assert ctx and "document" in ctx.lower()

    def test_code_genesis_detects_type(self, tmp_path):
        # Code project (git, no _ai-context/) — assert the explicit type marker,
        # not the bare "document" token (which also appears in founding question 4).
        d = make_dir(tmp_path, git=True)
        ctx = context(run(project_dir=d)) or ""
        assert "Detected type: code" in ctx

    def test_silent_when_ai_context_state_exists(self, tmp_path):
        d = tmp_path / "doc"
        d.mkdir()
        ac = d / "_ai-context"
        ac.mkdir()
        (ac / "SESSION-STATE.md").write_text("# state\n")
        assert context(run(project_dir=d)) is None

    def test_dismiss_marker_suppresses(self, tmp_path):
        d = make_dir(tmp_path, git=True, dismissed=True)
        assert context(run(project_dir=d)) is None

    def test_dismiss_env_suppresses(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        assert (
            context(run(project_dir=d, env={"START_PROJECT_NUDGE_DISMISS": "1"}))
            is None
        )

    def test_skip_env_silent_and_audited(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        audit = tmp_path / "bypass.log"
        r = run(
            project_dir=d,
            env={"START_PROJECT_NUDGE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)},
        )
        assert r.returncode == 0
        assert context(r) is None
        assert audit.exists() and "START_PROJECT_NUDGE_SKIP=1" in audit.read_text()

    def test_compact_source_silent(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        assert context(run(source="compact", project_dir=d)) is None

    @pytest.mark.parametrize("source", ["startup", "resume", "clear", ""])
    def test_fires_on_boundary_sources(self, tmp_path, source):
        d = make_dir(tmp_path, git=True)
        assert context(run(source=source, project_dir=d)) is not None

    def test_output_uses_nested_envelope(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        payload = json.loads(run(project_dir=d).stdout.strip())
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert (
            "additionalContext" not in payload
        )  # NOT the flat (silently-dropped) form

    def test_never_blocks(self, tmp_path):
        d = make_dir(tmp_path, git=True)
        assert run(project_dir=d).returncode == 0

    def test_malformed_stdin_never_crashes(self, tmp_path):
        d = make_dir(tmp_path, session_state=True)  # silent case
        e = os.environ.copy()
        for k in list(e):
            if k.startswith("START_PROJECT_") or k == "CLAUDE_PROJECT_DIR":
                e.pop(k)
        e["CLAUDE_PROJECT_DIR"] = str(d)
        for bad in ["", "not json", "{"]:
            r = subprocess.run(
                ["bash", str(HOOK)],
                input=bad,
                capture_output=True,
                text=True,
                env=e,
                timeout=15,
            )
            assert r.returncode == 0


def _lib_call(snippet: str) -> str:
    script = f'source "{GENESIS_LIB}"; {snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=10
    ).stdout.strip()


class TestGenesisLib:
    def test_is_project_dir_true_for_git(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        (d / ".git").mkdir()
        assert _lib_call(f"is_project_dir {d}") == "yes"

    def test_is_project_dir_true_for_sources(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        (d / "a.py").write_text("x")
        assert _lib_call(f"is_project_dir {d}") == "yes"

    def test_is_project_dir_false_for_bare(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        assert _lib_call(f"is_project_dir {d}") == "no"

    def test_memory_files_present_code(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        (d / "SESSION-STATE.md").write_text("x")
        assert _lib_call(f"memory_files_present {d}") == "yes"

    def test_memory_files_present_document(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "_ai-context" / "SESSION-STATE.md").write_text("x")
        assert _lib_call(f"memory_files_present {d}") == "yes"

    def test_memory_files_absent(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        assert _lib_call(f"memory_files_present {d}") == "no"

    def test_detect_project_type_document(self, tmp_path):
        """Document project = _ai-context/ + prose files, NO root loader, NO code
        markers. Under the unified layout (v2.62.0) _ai-context/ presence alone no
        longer implies document — but prose-only content must NOT read as code
        (contrarian abd7249bc39fc8171 mixed case)."""
        d = tmp_path / "p"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "notes.md").write_text("market research")
        (d / "analysis.txt").write_text("findings")
        assert _lib_call(f"detect_project_type {d}") == "document"

    def test_detect_project_type_code(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        assert _lib_call(f"detect_project_type {d}") == "code"

    def test_detect_project_type_code_with_ai_context_and_loader(self, tmp_path):
        """Unified layout: a code repo carries _ai-context/ too — the root loader
        (AGENTS.md/CLAUDE.md) is the code signature and must win."""
        d = tmp_path / "p"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "AGENTS.md").write_text("# loader")
        assert _lib_call(f"detect_project_type {d}") == "code"

    def test_detect_project_type_code_with_ai_context_and_manifest(self, tmp_path):
        """A pre-loader code repo (manifest present) with _ai-context/ is code."""
        d = tmp_path / "p"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "pyproject.toml").write_text("[project]")
        assert _lib_call(f"detect_project_type {d}") == "code"

    def test_detect_project_type_code_with_ai_context_and_sources(self, tmp_path):
        """A code repo (source files) with _ai-context/ is code; prose extensions
        must NOT count as code signal (they'd misfile document projects)."""
        d = tmp_path / "p"
        d.mkdir()
        (d / "_ai-context").mkdir()
        (d / "src").mkdir()
        (d / "src" / "main.py").write_text("print('x')")
        assert _lib_call(f"detect_project_type {d}") == "code"

    def test_is_dismissed_marker(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        (d / ".start-project-dismissed").write_text("")
        assert _lib_call(f"is_dismissed {d}") == "yes"

    def test_is_dismissed_env(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        assert _lib_call(f"START_PROJECT_NUDGE_DISMISS=1 is_dismissed {d}") == "yes"

    def test_is_dismissed_false(self, tmp_path):
        d = tmp_path / "p"
        d.mkdir()
        assert _lib_call(f"is_dismissed {d}") == "no"
