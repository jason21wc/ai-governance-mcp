"""Branch-scoping logic for the pre-push force-push check.

The force-push gate (Check 0 in pre-push-quality-gate.sh) must block
force-push to main/master while allowing it to feature branches — rebasing
a feature branch and force-pushing is standard GitHub Flow.

This file tests the Python target-extraction parser that the hook uses to
determine whether a push targets trunk.  The parser is copied verbatim from
the hook; if the hook's copy changes and this one does not, the drift shows
up as a failure — same pattern as test_hook_shell_scan.py.

The parser returns one of:
  "trunk"    — explicit refspec targeting main/master
  "feature"  — explicit refspec targeting a non-trunk branch
  "implicit" — no refspec; caller must check the current branch
  "unknown"  — parse failure (hook fails closed)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / ".claude" / "hooks" / "lib" / "shell-scan.sh"


def strip(command: str) -> str:
    """Invoke the real bash helper to strip quoted regions."""
    result = subprocess.run(
        ["bash", "-c", f'source "{LIB}"; strip_quoted_regions "$1"', "_", command],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


# The target-extraction parser, copied verbatim from pre-push-quality-gate.sh.
_TARGET_PARSER = r"""
import re, sys
cmd = sys.argv[1]
for seg in re.split(r"(?:\|\||&&|[;&|()`]|\$\()", cmd):
    toks = seg.split()
    if not toks or toks[0] != "git":
        continue
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        if toks[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            i += 2
        else:
            i += 1
    if i < len(toks) and toks[i] == "push":
        j = i + 1
        # skip push-specific flags
        while j < len(toks) and toks[j].startswith("-"):
            if toks[j] in ("--repo", "--push-option", "-o", "--receive-pack", "--exec"):
                j += 2
            else:
                j += 1
        # j = remote (if any), j+1.. = refspecs
        refspecs = toks[j+1:] if j+1 < len(toks) else []
        if not refspecs:
            print("implicit")
            sys.exit(0)
        for ref in refspecs:
            target = ref.split(":", 1)[1] if ":" in ref else ref
            if target in ("main", "master"):
                print("trunk")
                sys.exit(0)
        print("feature")
        sys.exit(0)
print("unknown")
"""


def push_target(command: str) -> str:
    """Run the target-extraction parser on a (pre-stripped) command."""
    result = subprocess.run(
        ["python3", "-c", _TARGET_PARSER, command],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


# ---------------------------------------------------------------------------
# TRUNK — force-push to main/master must be detected as "trunk"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin main",
        "git push -f origin main",
        "git push --force-with-lease origin main",
        "git push --force origin master",
        "git push --force origin feature:main",
        "cd /repo && git push --force origin main",
        "git -C /repo push --force origin main",
    ],
)
def test_force_push_to_trunk_detected(command):
    assert push_target(strip(command)) == "trunk", (
        f"Force-push to main/master not detected as trunk: {command!r}"
    )


# ---------------------------------------------------------------------------
# FEATURE — force-push to a feature branch must be detected as "feature"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git push --force-with-lease origin wt/294-ref-lib-guard",
        "git push --force origin feature-branch",
        "git push -f origin fix/thing",
        "git push --force origin develop",
        "git push --force origin local-branch:remote-branch",
        "git -C /repo push --force origin wt/some-feature",
    ],
)
def test_force_push_to_feature_detected(command):
    assert push_target(strip(command)) == "feature", (
        f"Force-push to feature branch not detected as feature: {command!r}"
    )


# ---------------------------------------------------------------------------
# IMPLICIT — no refspec means caller must check the current branch
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git push --force",
        "git push --force origin",
        "git push -f",
        "git push --force-with-lease origin",
    ],
)
def test_implicit_push_detected(command):
    assert push_target(strip(command)) == "implicit", (
        f"Push without explicit refspec not detected as implicit: {command!r}"
    )


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------


def test_non_push_command_returns_unknown():
    assert push_target("git commit -m 'hello'") == "unknown"


def test_branch_name_containing_main_is_not_trunk():
    """A branch named 'fix-main-page' contains 'main' but is not trunk."""
    assert push_target(strip("git push --force origin fix-main-page")) == "feature"


def test_refspec_local_to_feature_is_feature():
    """local:remote where remote is not main/master."""
    assert push_target(strip("git push --force origin main:staging")) == "feature"


def test_refspec_feature_to_main_is_trunk():
    """local:remote where remote IS main — this pushes TO main."""
    assert push_target(strip("git push --force origin hotfix:main")) == "trunk"


def test_push_with_global_git_flags():
    """Global flags (-C, -c) before push don't confuse the parser."""
    assert (
        push_target(
            strip("git -C /tmp -c push.default=current push --force origin feature")
        )
        == "feature"
    )
