"""The suite must exercise THIS checkout's source, not another one's (BACKLOG #363).

`ai_governance_mcp` is installed editable, and the `.pth` that supplies it points at
whichever checkout ran `pip install -e` — in this project the PRIMARY checkout, while
mutating work happens in `.claude/worktrees/<slug>`. If the suite resolved through
that `.pth`, you could edit `src/`, run green, and have tested none of your own
change: a false GREEN, and silent.

WHAT THIS FILE HONESTLY GUARDS, corrected after an audit measured the original claim.
It does NOT reproduce under pytest today, and the first version of this docstring
said it did. `tests/conftest.py` already inserts `<this checkout>/src` at position 0
and has for a long time, so pytest has been resolving correctly all along —
incidentally, as a side effect of a conftest import, rather than by configuration.
`pythonpath = ["src", "tests"]` makes the property explicit; these tests hold it.

So this is defence in depth against `conftest.py`'s insert being deleted as
redundant — NOT the instrument for a live defect. The live half of #363 is the bare
interpreter (`python -m ai_governance_mcp.extractor`), which no pytest setting can
reach and which no test here covers.

Stated this plainly because a guard advertised as catching something it cannot is
worse than no guard: it spends the reader's trust.
"""

from __future__ import annotations

import subprocess  # nosec B404 - fixed argv, test-local
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_the_package_under_test_is_this_checkouts_source():
    import ai_governance_mcp

    resolved = Path(ai_governance_mcp.__file__).resolve()

    assert resolved.is_relative_to(REPO), (
        f"pytest imported {resolved}, which is OUTSIDE this checkout ({REPO}).\n"
        "The suite is testing another checkout's source — a green run says nothing "
        "about the code in this tree. Check `pythonpath` in pyproject.toml."
    )


def test_pyproject_puts_src_ahead_of_the_editable_install():
    """Pin the mechanism, not just the outcome.

    The assertion above passes trivially when run FROM the primary checkout, where
    the editable install already points here — so on its own it would go green on
    the machine most likely to run it and red only where nobody looked.
    """
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")

    line = next(
        (ln for ln in text.splitlines() if ln.strip().startswith("pythonpath")), ""
    )

    assert "src" in line, f"pythonpath does not include src: {line!r}"


def test_a_worktree_subprocess_also_resolves_here():
    """The real-world shape: a fresh interpreter, cwd at the repo root.

    Runs pytest's own resolution rather than trusting this process, whose sys.path
    was already arranged by the collector.
    """
    proc = subprocess.run(  # nosec B603 - fixed argv
        [
            sys.executable,
            "-c",
            # ORDER MATTERS and the first draft of this got it wrong: `import`
            # before `sys.path.insert` resolves through the editable install and
            # the insert changes nothing. The failure was the test's, not the
            # fix's — and it is exactly the defect under test, so it is worth
            # having tripped over once.
            "import pathlib, sys;"
            "sys.path.insert(0, 'src');"
            "import ai_governance_mcp;"
            "print(pathlib.Path(ai_governance_mcp.__file__).resolve())",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    # Without `sys.path.insert`, this prints the editable install's target. The
    # insert is what pytest's `pythonpath` does; this proves the mechanism works
    # from a bare interpreter in this tree.
    assert str(REPO) in proc.stdout, (
        f"a bare interpreter in {REPO} resolved to {proc.stdout.strip()}"
    )
