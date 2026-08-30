"""Tests for the SessionStart hygiene backstop hook (BACKLOG #230f).

The hook (`.claude/hooks/session-start-hygiene.sh`) fires at session start and
surfaces standing repo hygiene findings by running `scripts/repo_hygiene.py`.
It also watches the Reference Library for uncommitted or unpushed entries.

Key behavioral contract:
- Always exit 0 (never blocks startup).
- Silent when clean (no output, no JSON envelope).
- Emits JSON via the nested ``hookSpecificOutput`` envelope (the flat form is
  silently dropped by Claude Code for SessionStart -- FM-HOOK-OUTPUT-ENVELOPE).
- Suppressible via ``HYGIENE_SKIP=1`` (audit-logged).
- Degrades silently when shared libraries are missing or the hygiene script
  does not exist (not this project).
- Interprets ``repo_hygiene.py`` exit codes:
  rc=0 empty output -> clean, silent;
  rc=0 with output  -> presence-only, "no action needed" footer;
  rc=1              -> findings present, "Standing loose ends" footer;
  rc>1              -> tool broken, "could not run" message.

Tests derived from hook source code and its documented behavior in the hook
header. The ``repo_hygiene.py`` script is NOT called -- a mock script with
controlled exit code and output is placed in the test's ``tmp_path``.
"""

import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "session-start-hygiene.sh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_project(tmp_path, *, hygiene_script=None, name="proj") -> Path:
    """Create a minimal project directory.

    ``hygiene_script`` is a string to write into ``scripts/repo_hygiene.py``.
    If None, no script is created (simulates "not this project").
    """
    d = tmp_path / name
    d.mkdir()
    if hygiene_script is not None:
        scripts = d / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        script = scripts / "repo_hygiene.py"
        script.write_text(hygiene_script)
    return d


def run(project_dir=None, env=None):
    """Invoke the hygiene hook with a controlled project directory."""
    payload = {"source": "startup"}
    if project_dir is not None:
        payload["cwd"] = str(project_dir)
    e = os.environ.copy()
    # Strip inherited env that could leak from the real repo.
    for k in list(e):
        if k.startswith("HYGIENE_") or k == "CLAUDE_PROJECT_DIR":
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
    """Return the injected additionalContext string, or None if the hook was silent.

    Asserts the SessionStart OUTPUT CONTRACT: the nested ``hookSpecificOutput``
    envelope with ``hookEventName == "SessionStart"``. A flat ``{"additionalContext"}``
    is silently dropped by Claude Code for SessionStart, so parsing via this helper
    (not ``.get("additionalContext")`` on the top level) makes that regression fail.
    """
    out = result.stdout.strip()
    if not out:
        return None
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]  # KeyError if someone reverts to the flat form
    assert hso["hookEventName"] == "SessionStart"
    return hso.get("additionalContext")


# A mock repo_hygiene.py that exits clean, no output.
MOCK_CLEAN = "#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n"

# A mock repo_hygiene.py that exits 0 with presence-only output (e.g. sibling session).
MOCK_PRESENCE = (
    "#!/usr/bin/env python3\nimport sys\n"
    "print('Another session is working here: wt/backlog-2 (/path/to/worktree)')\n"
    "sys.exit(0)\n"
)

# A mock repo_hygiene.py that exits 1 with findings.
MOCK_FINDINGS = (
    "#!/usr/bin/env python3\nimport sys\n"
    "print('3 uncommitted file(s)')\nprint('1 unpushed commit(s)')\n"
    "sys.exit(1)\n"
)

# A mock repo_hygiene.py that exits 2 (tool broken).
MOCK_BROKEN = "#!/usr/bin/env python3\nimport sys\nsys.exit(2)\n"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSessionStartHygieneHook:
    """Core control-flow branches of the hygiene backstop hook."""

    # --- Branch 1: HYGIENE_SKIP bypass ---

    def test_hygiene_skip_exits_zero_and_is_silent(self, tmp_path):
        """HYGIENE_SKIP=1 exits 0 immediately, no JSON output."""
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        r = run(project_dir=proj, env={"HYGIENE_SKIP": "1"})
        assert r.returncode == 0
        assert context(r) is None

    def test_hygiene_skip_writes_audit_log(self, tmp_path):
        """HYGIENE_SKIP=1 writes to the bypass audit log."""
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        audit = tmp_path / "bypass.log"
        r = run(
            project_dir=proj,
            env={"HYGIENE_SKIP": "1", "BYPASS_AUDIT_LOG": str(audit)},
        )
        assert r.returncode == 0
        assert context(r) is None
        assert audit.exists(), "HYGIENE_SKIP should write to bypass audit log"
        content = audit.read_text()
        assert "session-start-hygiene" in content
        assert "HYGIENE_SKIP=1" in content

    # --- Branch 2: Missing lib/repo-root.sh ---

    def test_missing_repo_root_lib_exits_zero_silently(self, tmp_path):
        """When lib/repo-root.sh is absent the hook degrades silently (exit 0)."""
        import shutil

        # Copy the hook to a temp location so we can control its lib directory.
        hook_dir = tmp_path / "hooks"
        hook_dir.mkdir()
        hook_copy = hook_dir / "session-start-hygiene.sh"
        shutil.copy(HOOK, hook_copy)
        # Copy audit-bypass.sh but NOT repo-root.sh
        lib_dir = hook_dir / "lib"
        lib_dir.mkdir()
        audit_lib = REPO / ".claude" / "hooks" / "lib" / "audit-bypass.sh"
        if audit_lib.exists():
            shutil.copy(audit_lib, lib_dir / "audit-bypass.sh")
        # No repo-root.sh -> the `[ -f "$HOOK_DIR/lib/repo-root.sh" ] || exit 0` fires.

        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        payload = {"source": "startup", "cwd": str(proj)}
        e = os.environ.copy()
        for k in list(e):
            if k.startswith("HYGIENE_") or k == "CLAUDE_PROJECT_DIR":
                e.pop(k)
        e["CLAUDE_PROJECT_DIR"] = str(proj)
        r = subprocess.run(
            ["bash", str(hook_copy)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=e,
            timeout=15,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    # --- Branch 3: Missing repo_hygiene.py ---

    def test_missing_hygiene_script_exits_zero_silently(self, tmp_path):
        """When scripts/repo_hygiene.py does not exist, hook exits 0 silently."""
        proj = make_project(tmp_path, hygiene_script=None)
        r = run(project_dir=proj)
        assert r.returncode == 0
        assert context(r) is None

    # --- Branch 4: repo_hygiene.py rc=0, empty output (clean) ---

    def test_clean_repo_is_silent(self, tmp_path):
        """rc=0 with no output -> exit 0, no JSON (the common case)."""
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj)
        assert r.returncode == 0
        assert context(r) is None

    # --- Branch 5: repo_hygiene.py rc=0, with output (presence-only) ---

    def test_presence_only_output_emits_no_action_needed(self, tmp_path):
        """rc=0 with output (sibling session presence) -> JSON with 'no action needed'."""
        proj = make_project(tmp_path, hygiene_script=MOCK_PRESENCE)
        r = run(project_dir=proj)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None, "presence-only output should produce JSON context"
        assert "no action needed" in ctx
        assert "Another session" in ctx

    # --- Branch 6: repo_hygiene.py rc=1, findings present ---

    def test_findings_emit_standing_loose_ends(self, tmp_path):
        """rc=1 with output -> JSON with findings and 'Standing loose ends' footer."""
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        r = run(project_dir=proj)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None, "findings should produce JSON context"
        assert "uncommitted" in ctx
        assert "Standing loose ends" in ctx

    def test_findings_include_checkout_path(self, tmp_path):
        """The findings message includes the checkout path for disambiguation."""
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        ctx = context(run(project_dir=proj))
        assert ctx is not None
        assert "Checkout:" in ctx

    # --- Branch 7: repo_hygiene.py rc>1 (tool broken) ---

    def test_broken_tool_emits_could_not_run(self, tmp_path):
        """rc>1 -> JSON with 'could not run' message (a broken tool must not read as clean)."""
        proj = make_project(tmp_path, hygiene_script=MOCK_BROKEN)
        r = run(project_dir=proj)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None, "broken tool should produce JSON context"
        assert "could not run" in ctx
        assert "rc=2" in ctx

    def test_broken_tool_rc3(self, tmp_path):
        """rc=3 also reports 'could not run' with the actual rc."""
        mock_rc3 = "#!/usr/bin/env python3\nimport sys\nsys.exit(3)\n"
        proj = make_project(tmp_path, hygiene_script=mock_rc3)
        ctx = context(run(project_dir=proj))
        assert ctx is not None
        assert "could not run" in ctx
        assert "rc=3" in ctx

    # --- Output envelope ---

    def test_output_uses_nested_envelope(self, tmp_path):
        """Output is the nested hookSpecificOutput envelope, not the flat form."""
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        payload = json.loads(run(project_dir=proj).stdout.strip())
        assert "hookSpecificOutput" in payload
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        # NOT the flat (silently-dropped) form
        assert "additionalContext" not in payload

    # --- Never blocks ---

    def test_never_blocks_on_clean(self, tmp_path):
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        assert run(project_dir=proj).returncode == 0

    def test_never_blocks_on_findings(self, tmp_path):
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        assert run(project_dir=proj).returncode == 0

    def test_never_blocks_on_broken_tool(self, tmp_path):
        proj = make_project(tmp_path, hygiene_script=MOCK_BROKEN)
        assert run(project_dir=proj).returncode == 0

    def test_never_blocks_on_missing_script(self, tmp_path):
        proj = make_project(tmp_path, hygiene_script=None)
        assert run(project_dir=proj).returncode == 0

    # --- Malformed stdin ---

    def test_malformed_stdin_never_crashes(self, tmp_path):
        """Bad/empty/partial JSON on stdin must not crash or emit."""
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        e = os.environ.copy()
        for k in list(e):
            if k.startswith("HYGIENE_") or k == "CLAUDE_PROJECT_DIR":
                e.pop(k)
        e["CLAUDE_PROJECT_DIR"] = str(proj)
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


class TestReferenceLibraryWatch:
    """Branch 8 and 9: Reference Library uncommitted/unpushed detection.

    Override ``$HOME`` to a tmp directory so tests never read the real library.
    """

    _GIT_ID = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def _make_ref_lib(
        self, tmp_path, *, location="dev-tools", dirty=False, ahead=False
    ):
        """Create a git repo at one of the two known Reference Library locations.

        Returns the fake HOME directory. ``dirty`` means uncommitted ref-*.md files.
        ``ahead`` means commits not pushed (requires a fake remote).
        """
        home = tmp_path / "home"
        home.mkdir()
        if location == "dev-tools":
            lib_dir = home / "dev-tools" / "reference-library"
        else:
            lib_dir = home / ".ai-governance" / "reference-library"
        lib_dir.mkdir(parents=True)

        env = os.environ.copy()
        env.update(self._GIT_ID)
        env["HOME"] = str(home)

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=lib_dir, check=True, env=env
        )
        # Initial committed file
        (lib_dir / "README.md").write_text("# Reference Library\n")
        subprocess.run(["git", "add", "-A"], cwd=lib_dir, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"], cwd=lib_dir, check=True, env=env
        )

        if ahead:
            # Create a bare remote and push, then add a local commit
            bare = tmp_path / "remote.git"
            subprocess.run(
                ["git", "init", "-q", "--bare", "-b", "main", str(bare)],
                check=True,
                env=env,
            )
            subprocess.run(
                ["git", "remote", "add", "origin", str(bare)],
                cwd=lib_dir,
                check=True,
                env=env,
            )
            subprocess.run(
                ["git", "push", "-q", "-u", "origin", "main"],
                cwd=lib_dir,
                check=True,
                env=env,
            )
            # Add an unpushed commit
            (lib_dir / "ref-new-entry.md").write_text("# New reference\n")
            subprocess.run(["git", "add", "-A"], cwd=lib_dir, check=True, env=env)
            subprocess.run(
                ["git", "commit", "-q", "-m", "add ref"],
                cwd=lib_dir,
                check=True,
                env=env,
            )
        elif dirty:
            # Create an uncommitted ref-*.md file
            (lib_dir / "ref-dirty-entry.md").write_text("# Uncommitted reference\n")

        return home

    def test_uncommitted_ref_entries_surfaced(self, tmp_path):
        """Uncommitted ref-*.md files in the library produce a warning."""
        home = self._make_ref_lib(tmp_path, dirty=True)
        # Use a project with a clean hygiene script so only the lib watch fires
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None, "uncommitted ref entries should produce context"
        assert "Reference Library" in ctx
        assert "uncommitted" in ctx

    def test_unpushed_ref_commits_surfaced(self, tmp_path):
        """Committed but unpushed ref library commits produce a warning."""
        home = self._make_ref_lib(tmp_path, ahead=True)
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None, "unpushed ref commits should produce context"
        assert "Reference Library" in ctx
        assert "not pushed" in ctx

    def test_clean_ref_library_stays_silent(self, tmp_path):
        """A clean (committed and pushed) library produces no ref library message."""
        # A committed library with no remote has _ahead=0 by default (no upstream).
        # Just a committed, clean repo with no dirty files.
        home = tmp_path / "home"
        home.mkdir()
        lib_dir = home / "dev-tools" / "reference-library"
        lib_dir.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self._GIT_ID)
        env["HOME"] = str(home)
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=lib_dir, check=True, env=env
        )
        (lib_dir / "README.md").write_text("# Reference Library\n")
        subprocess.run(["git", "add", "-A"], cwd=lib_dir, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"], cwd=lib_dir, check=True, env=env
        )
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        assert context(r) is None

    def test_no_ref_library_stays_silent(self, tmp_path):
        """When no ref library exists at either path, no ref library message."""
        home = tmp_path / "home"
        home.mkdir()
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        assert context(r) is None

    def test_alt_location_also_detected(self, tmp_path):
        """The .ai-governance/reference-library path is also checked."""
        home = self._make_ref_lib(tmp_path, location="ai-governance", dirty=True)
        proj = make_project(tmp_path, hygiene_script=MOCK_CLEAN)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None
        assert "Reference Library" in ctx
        assert "uncommitted" in ctx

    def test_ref_library_message_appends_to_hygiene_findings(self, tmp_path):
        """Ref library message is combined with hygiene findings from repo_hygiene.py."""
        home = self._make_ref_lib(tmp_path, dirty=True)
        proj = make_project(tmp_path, hygiene_script=MOCK_FINDINGS)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None
        # Both the hygiene findings AND the ref library message should appear
        assert "uncommitted file(s)" in ctx  # from MOCK_FINDINGS
        assert "Reference Library" in ctx  # from the watch
        assert "Standing loose ends" in ctx  # the rc=1 footer


class TestHygieneHookEdgeCases:
    """Edge cases and interaction behaviors."""

    def test_hygiene_script_receives_repo_and_min_severity_args(self, tmp_path):
        """The hook passes --repo and --min-severity to repo_hygiene.py."""
        # A mock script that prints its own arguments so we can verify the call.
        mock = (
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print(' '.join(sys.argv[1:]))\n"
            "sys.exit(1)\n"
        )
        proj = make_project(tmp_path, hygiene_script=mock)
        ctx = context(run(project_dir=proj))
        assert ctx is not None
        assert "--repo" in ctx
        assert "--min-severity" in ctx
        assert "warn" in ctx

    def test_hygiene_script_stderr_suppressed(self, tmp_path):
        """repo_hygiene.py stderr is redirected to /dev/null (2>/dev/null in hook)."""
        mock = (
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print('finding on stdout', file=sys.stdout)\n"
            "print('error on stderr', file=sys.stderr)\n"
            "sys.exit(1)\n"
        )
        proj = make_project(tmp_path, hygiene_script=mock)
        r = run(project_dir=proj)
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None
        assert "finding on stdout" in ctx
        # stderr from repo_hygiene.py should NOT leak to the hook's stderr
        # (the hook uses 2>/dev/null on the python3 call)

    def test_presence_and_ref_library_combined(self, tmp_path):
        """Presence-only output (rc=0) combined with ref library watch."""
        home = self._make_ref_lib(tmp_path, dirty=True)
        proj = make_project(tmp_path, hygiene_script=MOCK_PRESENCE)
        r = run(project_dir=proj, env={"HOME": str(home)})
        assert r.returncode == 0
        ctx = context(r)
        assert ctx is not None
        # Should have both the presence message and the ref library warning
        assert "Another session" in ctx
        assert "Reference Library" in ctx

    _GIT_ID = TestReferenceLibraryWatch._GIT_ID

    def _make_ref_lib(self, tmp_path, *, dirty=False):
        """Delegate to TestReferenceLibraryWatch._make_ref_lib for reuse."""
        home = tmp_path / "home"
        home.mkdir()
        lib_dir = home / "dev-tools" / "reference-library"
        lib_dir.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self._GIT_ID)
        env["HOME"] = str(home)
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=lib_dir, check=True, env=env
        )
        (lib_dir / "README.md").write_text("# Reference Library\n")
        subprocess.run(["git", "add", "-A"], cwd=lib_dir, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"], cwd=lib_dir, check=True, env=env
        )
        if dirty:
            (lib_dir / "ref-dirty-entry.md").write_text("# Uncommitted reference\n")
        return home
