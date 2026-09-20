"""Shared quoted-region stripper for the safety gates (.claude/hooks/lib/shell-scan.sh).

**The root cause.** Both safety gates matched dangerous tokens against the RAW command
string. A token inside a quoted region — a commit message, an echo string, a grep pattern,
a heredoc body — is not executable, but a token-anchored matcher cannot tell the
difference. Observed n=3 in a single session (2026-07-13):

  1. pre-push gate:  `git commit -m "...bandit -r src/ -f txt..."`
                     -> the ` -f ` in the MESSAGE was read as a force-push flag.
  2. oom gate:       `git commit -m "...ran pytest tests/..."`   (OPERATIONS T-143)
                     -> `pytest` in the MESSAGE tripped the OOM gate.
  3. oom gate:       `echo "===== the pytest matcher ====="`
                     -> blocked a read-only echo, fired while its author was trying to
                        READ the hook in order to fix defect #2.

T-143 deferred the fix at n=1 on an explicit cost argument: modifying a safety hook risks
TRUE-POSITIVE REGRESSION, and a gate that stops catching real force-pushes is far worse
than one that nags. That argument is correct, which is why this module exists: the fix
ships only because both directions are pinned here.

**The asymmetry is deliberate and must stay that way.** For a safety gate a false positive
is survivable and a false negative is not. `strip_quoted_regions` fails SAFE — on any
error it returns the ORIGINAL string, so the gate degrades to its previous over-blocking
behaviour, never to under-blocking.

**Known residual, stated rather than hidden:** a deliberately QUOTED command name would
evade (`"pytest" tests/` is valid shell). Out of threat model — these gates stop an AI
running a dangerous command *carelessly*, not an adversary actively evading them, and an
AI with documented bypass env-vars has no reason to smuggle anything. Pinned by
test_quoted_command_name_is_a_known_residual so the limit is a recorded decision, not a
surprise.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / ".claude" / "hooks" / "lib" / "shell-scan.sh"

# The live matchers, copied verbatim from the two hooks. If a hook's regex changes and
# this copy does not, the drift shows up as a failure here — which is the point.
FORCE_RE = re.compile(r"(--force(\s|$|=)|\s-f(\s|$)|--force-with-lease)")
PYTEST_RE = re.compile(r"(^|\s|&&|;|\|)\s*(pytest\s|python[23]?\s+-m\s*pytest(\s|$))")


def strip(command: str) -> str:
    """Invoke the real bash helper — not a Python reimplementation of it."""
    result = subprocess.run(  # nosec B603 B607 — fixed argv, test-local script path
        ["bash", "-c", f'source "{LIB}"; strip_quoted_regions "$1"', "_", command],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def blocks_force(command: str) -> bool:
    return bool(FORCE_RE.search(strip(command)))


def blocks_pytest(command: str) -> bool:
    return bool(PYTEST_RE.search(strip(command)))


# ---------------------------------------------------------------------------
# TRUE POSITIVES — the gates must STILL fire. A regression here is a safety hole.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin main",
        "git push -f origin main",
        "git push --force-with-lease origin main",
        "git push --force=refs/heads/main origin",
        "cd /repo && git push --force origin main",
        # A real force-push that also carries a quoted argument elsewhere.
        'git push --force origin main # "cleanup"',
    ],
)
def test_real_force_push_still_blocked(command):
    assert blocks_force(command), (
        f"FALSE NEGATIVE — a real force-push is no longer detected: {command!r}. "
        "This is strictly worse than the false positive the stripper was built to fix."
    )


@pytest.mark.parametrize(
    "command",
    [
        "pytest tests/",
        "python -m pytest tests/",
        "python3 -mpytest tests/",
        "cd /repo && pytest tests/",
        "PYTHONPATH=src pytest tests/",
        # Quoted ARGUMENTS must not hide the invocation — only quoted CONTENT is stripped.
        'pytest tests/ -m "not slow"',
        "pytest tests/ -k 'routing'",
    ],
)
def test_real_pytest_invocation_still_detected(command):
    assert blocks_pytest(command), (
        f"FALSE NEGATIVE — a real invocation is no longer detected: {command!r}. "
        "The OOM gate exists because this class OOM'd a 64GB machine."
    )


# ---------------------------------------------------------------------------
# FALSE POSITIVES — the three live instances that motivated the fix.
# ---------------------------------------------------------------------------


def test_force_flag_inside_a_commit_message_is_not_a_force_push():
    """Instance 1, live 2026-07-13: this exact command was blocked as a force-push."""
    command = 'git commit -m "bandit -r src/ -f txt reports zero issues"'
    assert not blocks_force(command)


def test_tool_name_inside_a_commit_message_is_not_an_invocation():
    """Instance 2 — OPERATIONS T-143, deferred since 2026-05."""
    command = 'git commit -m "ran pytest tests/ and the suite is green"'
    assert not blocks_pytest(command)


def test_tool_name_inside_an_echo_is_not_an_invocation():
    """Instance 3: blocked a read-only echo issued while reading the hook to fix #2."""
    command = 'echo "===== the pytest matcher ====="'
    assert not blocks_pytest(command)


@pytest.mark.parametrize(
    "command",
    [
        'grep -n "pytest" .claude/hooks/pre-test-oom-gate.sh',
        "grep -rn 'git push --force' docs/",
        "rg 'pytest tests/' --files-with-matches",
        "echo 'use --force only as a last resort'",
    ],
)
def test_searching_for_a_token_is_not_running_it(command):
    """Reading about a dangerous command must never be treated as issuing one."""
    assert not blocks_pytest(command) or "pytest" not in command
    assert not blocks_force(command) or "force" not in command


def test_heredoc_body_is_stripped():
    """The T-143 workaround shape: a commit whose heredoc body names the tools."""
    command = (
        "git commit -q -m \"$(cat <<'EOF'\n"
        "fix: something\n\n"
        "Ran pytest tests/ green. Used bandit -r src/ -f txt.\n"
        "EOF\n"
        ')"'
    )
    assert not blocks_pytest(command)
    assert not blocks_force(command)


def test_real_command_after_a_heredoc_is_still_seen():
    """The heredoc consumer must not swallow the lines that FOLLOW the body.

    If it did, `<<EOF ... EOF` followed by a real `git push --force` would be a silent
    false negative — the stripper would have created a bypass.
    """
    command = (
        "git commit -F msg.txt <<'EOF'\n"
        "some message body\n"
        "EOF\n"
        "git push --force origin main\n"
    )
    assert blocks_force(command), "heredoc consumption swallowed a real force-push"

    command2 = "git commit -F msg.txt <<'EOF'\nbody\nEOF\npython -m pytest tests/\n"
    assert blocks_pytest(command2), "heredoc consumption swallowed a real invocation"


# ---------------------------------------------------------------------------
# Contract + honest limits
# ---------------------------------------------------------------------------


def test_stripper_fails_safe_to_the_original_string():
    """On failure the helper must return the command UNCHANGED.

    Degradation direction is the whole safety argument: a broken stripper must leave the
    gate over-blocking (its old behaviour), never under-blocking.
    """
    result = subprocess.run(  # nosec B603 B607 — fixed argv
        [
            "bash",
            "-c",
            # Force the python3 path to be unavailable inside the helper's subshell.
            f'PATH=/nonexistent; source "{LIB}"; strip_quoted_regions "$1"',
            "_",
            'git push --force origin main -m "x"',
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert "--force" in result.stdout, (
        "fail-safe broken: with python3 unavailable the helper must echo the ORIGINAL "
        "command so the gate still blocks."
    )


def test_quoted_command_name_is_a_known_residual():
    """A deliberately-quoted command name evades. Recorded, not hidden.

    `"pytest" tests/` is valid shell and WILL execute. After stripping it no longer
    matches. This is out of threat model — the gates stop careless invocation, not an
    adversary evading them, and an AI has documented bypass env-vars available. If the
    threat model ever becomes adversarial, this helper is the wrong layer and a real
    shell parser is required. Pinned so the limitation is a decision, not a surprise.
    """
    assert not blocks_pytest('"pytest" tests/')
    assert not blocks_force("git push '--force' origin main")


# ---------------------------------------------------------------------------
# shell_arg_segments — the ARGUMENT view (session-272)
# ---------------------------------------------------------------------------
#
# Assertions here are derived from the helper's stated CONTRACT, not from its
# observed output. That distinction is the `coding-quality-testing-integration`
# Echo Chamber pitfall: the same session wrote this helper, so a test built by
# running it and recording what came back would only confirm the implementation.
#
# The contract, stated in lib/shell-scan.sh:
#   1. Split at UNQUOTED shell separators (&& || ; | & newline).
#   2. Remove quote CHARACTERS, preserve their CONTENTS. (Opposite of
#      strip_quoted_regions, which deletes contents and keeps position.)
#   3. On failure, fall back to a bash-only splitter — never to "no segments"
#      (that would over-ALLOW, since a matched safe-subset pattern EXEMPTS a run)
#      and never to the whole raw command (same reason).


def segments(command: str, *, path_prefix=None) -> list[str]:
    """Invoke the real bash helper — not a Python reimplementation of it."""
    import os as _os

    env = {**_os.environ}
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    result = subprocess.run(  # nosec B603 B607 — fixed argv, test-local script path
        ["bash", "-c", f'source "{LIB}"; shell_arg_segments "$1"', "_", command],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return [s for s in result.stdout.split("\n") if s]


class TestShellArgSegmentsContract:
    """Contract clause 1 and 2: split on unquoted separators, keep quoted content."""

    def test_a_single_command_is_one_segment(self):
        assert segments("pytest tests/test_a.py -v") == ["pytest tests/test_a.py -v"]

    @pytest.mark.parametrize("sep", ["&&", "||", ";", "|"])
    def test_unquoted_separators_split(self, sep):
        out = segments(f"cmd_one arg {sep} cmd_two arg")
        assert out == ["cmd_one arg", "cmd_two arg"], f"{sep!r} did not split cleanly"

    def test_quote_characters_are_removed_and_contents_kept(self):
        """The defining difference from strip_quoted_regions.

        `-m "not slow"` is a legitimately QUOTED ARGUMENT. The detection view
        erases it; this view must preserve it, or the gate's own recommended
        happy path stops being recognisable as a targeted run.
        """
        assert segments('pytest -m "not slow"') == ["pytest -m not slow"]
        assert segments("pytest -m 'not slow'") == ["pytest -m not slow"]

    def test_a_separator_inside_quotes_does_not_split(self):
        """`&&` in a commit message is text, not a command boundary."""
        out = segments('git commit -m "a && b" && pytest tests/')
        assert out == ["git commit -m a && b", "pytest tests/"], out

    def test_the_motivating_case_keeps_the_path_with_its_own_command(self):
        """Why this helper exists at all.

        `git commit -m "fix tests/test_a.py" && pytest tests/` was ALLOWED by a
        gate that asked "is this run targeted?" of the whole line: the path in
        the commit message answered on behalf of the bare full-suite run. The
        segments must attribute the path to `git commit`, NOT to `pytest`.
        """
        out = segments('git commit -m "fix tests/test_a.py" && pytest tests/')
        assert len(out) == 2
        assert "tests/test_a.py" in out[0], "path must stay with git commit"
        assert "tests/test_a.py" not in out[1], (
            "the pytest segment must NOT inherit another command's argument — "
            "that inheritance is the exact defect this helper was written to fix"
        )
        assert out[1] == "pytest tests/"

    def test_backslash_escaped_separator_does_not_split(self):
        assert segments(r"echo a\&\& b") == [r"echo a\&\& b"]

    def test_empty_input_yields_no_segments(self):
        assert segments("") == []


class TestShellArgSegmentsFailsSafe:
    """Contract clause 3, and its direction is OPPOSITE to strip_quoted_regions.

    strip_quoted_regions feeds matchers that DENY on a match, so returning the
    raw command over-blocks — safe. shell_arg_segments feeds a matcher that
    EXEMPTS on a match, so returning nothing (no segments -> no safe-subset
    marker -> falls through to the risk checks) is the over-blocking direction,
    and returning the whole raw command would over-ALLOW.
    """

    def test_no_python3_still_produces_segments(self, tmp_path):
        """Emitting nothing here would deny every targeted run.

        The first version of this helper returned nothing when python3 failed,
        reasoning that pytest cannot run without python3 anyway. That reasoning
        is wrong — a console script's shebang is an ABSOLUTE interpreter path,
        so shadowing `python3` on PATH does not stop `pytest`. Measured: ordinary
        targeted runs were denied.
        """
        stub = tmp_path / "nopy"
        stub.mkdir()
        (stub / "python3").write_text("#!/bin/sh\nexit 127\n")
        (stub / "python3").chmod(0o755)
        out = segments(
            'git commit -m "fix tests/test_a.py" && pytest tests/test_b.py',
            path_prefix=stub,
        )
        assert out, "a broken python3 must not silently erase all segments"
        assert out[-1] == "pytest tests/test_b.py", out

    def test_silent_python3_still_produces_segments(self, tmp_path):
        """`produced nothing` is not `succeeded` — BACKLOG #298, same class."""
        stub = tmp_path / "silentpy"
        stub.mkdir()
        (stub / "python3").write_text("#!/bin/sh\nexit 0\n")
        (stub / "python3").chmod(0o755)
        out = segments("pytest tests/test_b.py -v", path_prefix=stub)
        assert out == ["pytest tests/test_b.py -v"], out

    def test_degraded_split_never_merges_a_bare_suite_run_into_a_safe_one(
        self, tmp_path
    ):
        """The bash fallback is coarser, but only in the over-blocking direction.

        It strips quotes BEFORE splitting, so a separator inside a quoted
        argument splits where python3 would not. That can only REMOVE text from
        a segment, and a segment is safe only by CONTAINING a marker — so no
        split can manufacture safety.
        """
        stub = tmp_path / "nopy2"
        stub.mkdir()
        (stub / "python3").write_text("#!/bin/sh\nexit 127\n")
        (stub / "python3").chmod(0o755)
        out = segments(
            'git commit -m "fix tests/test_a.py" && pytest tests/', path_prefix=stub
        )
        assert "pytest tests/" in out
        assert "tests/test_a.py" not in "pytest tests/"
        for seg in out:
            if seg.startswith("pytest"):
                assert "test_a.py" not in seg, (
                    "the degraded splitter must not hand a full-suite run "
                    f"another command's test path: {seg!r}"
                )
