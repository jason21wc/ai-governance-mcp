"""One guarded accessor for the working directory — asserted, not documented.

WHY THIS TEST EXISTS AND WHY IT IS A TEST, NOT A CI GREP
--------------------------------------------------------
This is the THIRD time an unguarded working-directory read has broken something
in this repo. The 2026-04-10 LEARNING-LOG entry (itself labelled "SECOND
OCCURRENCE") already named the structural fix:

    "Shared module + CI grep check for Path.cwd() in server files is the
     structural path. Documentation alone doesn't prevent code duplication bugs."

Half of that shipped. `path_resolution.py` became the shared module — and then
the unguarded call moved *inside* it, which concentrated the blast radius
instead of removing it. The check never shipped at all. So the lesson was
written, read, half-applied, and the bug recurred: the "Write-Only Memory"
failure mode named in `meta-governance-continuous-learning-adaptation`.

A CI GREP WAS THE OBVIOUS FORM AND IT WAS REJECTED, deliberately. Measured
against the 15 pre-fix call sites, a grep for `Path.cwd()` would have flagged 8
sites that are legitimate or docstrings — a ~53% false-positive rate, rising to
100% once the real sites were fixed. This repo has already recorded that exact
hazard firing: a false-positive quality gate drove routine use of
`QUALITY_GATE_SKIP=true`, whose only escape ALSO disables the secret scanner
(LEARNING-LOG, "a false positive in a cosmetic check trains a bypass of a
security check"). A permanently-red gate is a bypass in waiting.

This assertion has a 0% false-positive rate by construction: it does not judge
whether a call is safe, it asserts there is exactly ONE place that reads cwd.
That is a property with a single obvious repair — route the new site through
`safe_cwd()` — and it runs where developers already are.

IF THIS TEST FAILS, DO NOT ADD AN EXEMPTION. Route the new call site through
`safe_cwd()`. The exemption list below is EMPTY and should stay that way — the
one exemption this fix originally granted turned out to be concealing a real
startup crash (see the note on `EXEMPTIONS`).

WHAT THIS CANNOT SEE — stated because the argument above is about false
POSITIVES and would otherwise read as a completeness claim. A dead working
directory also breaks *implicit* cwd reads, which contain no `Path.cwd()` to
match: `Path("relative").resolve()`, `.absolute()`, `os.path.abspath()`,
relative `open()`, and any child process that inherits the dead cwd and calls
`getcwd()` (git, /bin/sh, the Codex CLI). Live instances: `handlers/agents.py`
and `context_engine/server.py` both call `Path(raw).resolve()` on a
CALLER-SUPPLIED path, so a relative `project_path` argument on a dead cwd still
raises. Deliberately not matched here — a `.resolve()` matcher would flag ~40
legitimate call sites and become the false-positive machine this file exists to
avoid being. Tracked in BACKLOG instead.
"""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "ai_governance_mcp"

# The one place allowed to read the working directory.
ACCESSOR_FILE = SRC / "path_resolution.py"

# Closed exemption list — CURRENTLY EMPTY, and that is the goal.
#
# `enforcement.py` was exempted in the first version of this fix, on the reasoning
# that a proxy starting up necessarily has a valid working directory. Cross-vendor
# review showed that reasoning was both unverified and wrong — and worse, that the
# call was `os.environ.get("GOVERNANCE_PROJECT_PATH", os.getcwd())`, whose default
# argument is evaluated EAGERLY, so it read cwd even when the env var was set. The
# exemption was hiding a real startup crash. It is now routed through safe_cwd()
# like everything else.
#
# The lesson worth keeping: an exemption is where a checker goes to die. Prefer
# making the site conform.
EXEMPTIONS: dict[Path, str] = {}

# Matches a real call, not the words in a docstring or comment.
CWD_CALL = re.compile(r"(?:Path\.cwd|os\.getcwd)\s*\(\s*\)")


def _strip_comments_and_docstrings(source: str) -> str:
    """Blank out comments and triple-quoted strings.

    Prose about `Path.cwd()` is not a call, and this repo's docstrings discuss it
    at length precisely because it is dangerous. A checker that cannot tell an
    explanation from an invocation is the false-positive machine this test was
    written to avoid being.

    LINE NUMBERS ARE PRESERVED. A removed docstring is replaced by the newlines it
    occupied, not collapsed — the first version of this collapsed them and
    reported `config.py:59` for a call on line 75, sending the reader to the wrong
    place. A checker whose output you cannot trust to navigate is a checker people
    stop reading.
    """

    def _blank(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    without_docstrings = re.sub(
        r'""".*?"""|\'\'\'.*?\'\'\'', _blank, source, flags=re.DOTALL
    )
    return re.sub(r"#[^\n]*", "", without_docstrings)


def _call_sites() -> dict[Path, list[int]]:
    found: dict[Path, list[int]] = {}
    for py in sorted(SRC.rglob("*.py")):
        code = _strip_comments_and_docstrings(py.read_text(encoding="utf-8"))
        lines = [
            i for i, line in enumerate(code.splitlines(), 1) if CWD_CALL.search(line)
        ]
        if lines:
            found[py] = lines
    return found


def test_only_the_shared_accessor_reads_the_working_directory():
    """Exactly one non-exempt file may call Path.cwd()/os.getcwd()."""
    offenders = {
        path: lines
        for path, lines in _call_sites().items()
        if path != ACCESSOR_FILE and path not in EXEMPTIONS
    }
    assert not offenders, (
        "Unguarded working-directory read(s) outside path_resolution.safe_cwd():\n"
        + "\n".join(
            f"  {p.relative_to(SRC.parent.parent)}:{','.join(map(str, ls))}"
            for p, ls in offenders.items()
        )
        + "\n\nA process outlives its working directory: delete the directory it was "
        "launched in and Path.cwd() raises FileNotFoundError for the life of the "
        "process. This has broken this repo three times.\n"
        "FIX: import safe_cwd from path_resolution and handle its None return. "
        "Do NOT add an exemption — see the module docstring."
    )


def test_the_accessor_itself_is_the_single_guarded_call():
    """path_resolution.py must contain exactly one cwd read — inside safe_cwd()."""
    sites = _call_sites().get(ACCESSOR_FILE, [])
    assert len(sites) == 1, (
        f"path_resolution.py has {len(sites)} cwd calls at lines {sites}; expected "
        "exactly 1 (inside safe_cwd). Concentrating the read is the whole point — "
        "a second one here recreates the blast radius the accessor removed."
    )


def test_safe_cwd_guards_the_call():
    """The one call must actually be wrapped — not merely be the only one."""
    source = ACCESSOR_FILE.read_text(encoding="utf-8")
    body = source.split("def safe_cwd")[1].split("\ndef ")[0]
    assert "try:" in body and "except OSError" in body, (
        "safe_cwd() must wrap its cwd read in `try/except OSError`. Without the "
        "guard this test suite would enforce a single unguarded call site — "
        "tidier, equally broken."
    )


def test_exemptions_are_still_accurate():
    """An exemption for a file that no longer reads cwd is stale — drop it.

    Keeps the closed list honest: exemptions are the part of a checker that rots,
    because they outlive the reason they were granted.
    """
    sites = _call_sites()
    stale = [p for p in EXEMPTIONS if p not in sites]
    assert not stale, (
        "These files are exempted but no longer read the working directory; "
        f"remove them from EXEMPTIONS: {[str(p.name) for p in stale]}"
    )
