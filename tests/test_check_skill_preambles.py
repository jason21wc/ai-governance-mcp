"""Unit tests for scripts/check-skill-preambles.py — the executable-preamble gate.

Per BACKLOG #356. The script blocks commits, so the FALSE-POSITIVE tests below
matter more than the true-positive ones: a gate that fires on correct work
trains its own bypass (the V-004 arc, per tests/test_check_commit_promises.py).

The specific false positive that would sink this gate is prose that *documents*
the syntax. ``global-skills/all-clear/SKILL.md`` literally contains the sentence
"Do not use Claude Code's ``!`cmd``` inline-injection syntax here" — correct,
desirable content that a naive regex flags. If this gate cannot read its own
policy documentation without failing, nobody will keep it enabled.

These are parser-and-policy fixtures. They assert what THIS REPOSITORY forbids
in authored markdown. They deliberately make no claim about which shell
constructs a particular Claude Code release accepts at load time — that question
is unfalsifiable by inspection (see the script's module docstring) and is settled
by a live same-session worktree invocation, not by a unit test.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check-skill-preambles.py"


def _load_module():
    """Load the hyphenated script as a module.

    It must be registered in ``sys.modules`` BEFORE ``exec_module``: the script
    uses ``@dataclass``, and dataclasses resolves type annotations by looking its
    own module up in ``sys.modules``, which raises ``AttributeError`` if the
    module is not yet registered.
    """
    spec = importlib.util.spec_from_file_location("check_skill_preambles", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module()
find = mod.find_executable_preambles


def scan(text: str):
    return find(text, Path("SKILL.md"))


# --------------------------------------------------------------------------
# True positives — the gate must actually detect the real constructs.
# --------------------------------------------------------------------------


def test_detects_inline_preamble():
    """Covers: FM-SKILL-EXECUTABLE-PREAMBLE"""
    findings = scan('**Today:** !`date "+%Y-%m-%d"`\n')
    assert len(findings) == 1
    assert findings[0].kind == mod.INLINE
    assert findings[0].command == 'date "+%Y-%m-%d"'


def test_detects_fenced_preamble():
    text = "```!\necho hi\ngit log --oneline -1\n```\n"
    findings = scan(text)
    assert len(findings) == 1
    assert findings[0].kind == mod.FENCED
    assert findings[0].line == 1


def test_detects_multiple_findings_in_document_order():
    text = "**A:** !`pwd`\n\n**B:** !`date`\n\n```!\necho x\n```\n"
    findings = scan(text)
    assert [f.kind for f in findings] == [mod.INLINE, mod.INLINE, mod.FENCED]
    assert [f.line for f in findings] == [1, 3, 5]


def test_reports_line_and_column():
    findings = scan("prefix text !`pwd`\n")
    assert findings[0].line == 1
    assert findings[0].column == len("prefix text ") + 1


def test_detects_preamble_after_frontmatter_with_correct_line_numbers():
    text = "---\ndescription: a skill\nallowed-tools: Bash\n---\n\n!`pwd`\n"
    findings = scan(text)
    assert len(findings) == 1
    # Frontmatter occupies lines 1-4; the preamble is on line 6 of the file.
    assert findings[0].line == 6


def test_detects_indented_fenced_preamble():
    findings = scan("  ```!\n  echo hi\n  ```\n")
    assert len(findings) == 1
    assert findings[0].kind == mod.FENCED


def test_handles_crlf_line_endings():
    findings = scan("**Today:** !`date`\r\n")
    assert len(findings) == 1
    assert findings[0].command == "date"


# --------------------------------------------------------------------------
# False positives — these matter more. Everything here is CORRECT content.
# --------------------------------------------------------------------------


def test_a_marker_inside_a_double_backtick_span_IS_a_finding():
    """INVERTED 2026-08-29. This test previously asserted the opposite.

    It pinned an exemption for prose documenting the syntax, on the reasoning that
    a gate firing on correct work trains its own bypass. The premise was false and
    `all-clear/SKILL.md` disproved it: line 11 was the ONLY `!` in that skill, sat
    inside a double-backtick span, in a sentence saying not to use the syntax —
    and invoking the skill produced

        Shell command failed for pattern "!`cmd`": command not found: cmd

    with `cmd` appearing nowhere else in the file. Claude Code's extractor is raw
    text; it has no CommonMark awareness for this gate to model. The exemption was
    also why #356's cleanup commits skipped that file — the guard excused it rather
    than missing it.

    So the spanned form is not correct work, and this assertion is the load-bearing
    one: restore the exemption and this test goes red.

    Covers: FM-SKILL-EXECUTABLE-PREAMBLE
    """
    text = "Do not use Claude Code's `` !`cmd` `` inline-injection syntax here;\n"

    findings = scan(text)

    assert len(findings) == 1
    assert findings[0].kind == mod.INLINE
    assert findings[0].command == "cmd"


def test_the_parenthetical_note_form_is_also_a_finding():
    """Same shape, the form three skills used before #356 removed it."""
    text = (
        "*(The `` !`cmd` `` lines below are Claude Code inline-injection. "
        "On hosts that don't execute them — e.g. Codex — run the commands "
        "yourself and use their output.)*\n"
    )

    assert len(scan(text)) == 1


def test_spelling_the_syntax_out_is_the_supported_way_to_document_it():
    """The remedy, pinned — otherwise the rule has no legal way to be explained.

    This is what `all-clear/SKILL.md` now says. The first draft of BOTH this test
    and that file wrote the marker as a backtick-quoted bang, which is itself a
    bang immediately followed by a backtick — so the "safe" phrasing was a finding,
    and the newly-strict gate caught it on its first run. Describe the characters;
    do not print them adjacent.
    """
    text = (
        "Do not use Claude Code's bang-backtick inline-injection syntax here\n"
        "(an exclamation mark immediately followed by a backtick-quoted command).\n"
    )

    assert scan(text) == []


def test_ordinary_shell_fence_containing_an_example_is_legal():
    text = "```sh\n!`date`\necho not executed\n```\n"
    assert scan(text) == []


def test_outer_four_backtick_fence_containing_an_example_is_legal():
    text = "````markdown\n```!\necho example\n```\n````\n"
    assert scan(text) == []


def test_tilde_fence_containing_an_example_is_legal():
    text = "~~~markdown\n!`date`\n~~~\n"
    assert scan(text) == []


def test_bang_in_ordinary_prose_is_legal():
    assert scan("This is important! `code` follows.\n") == []


def test_ordinary_code_span_without_bang_is_legal():
    assert scan("Run `git status` first.\n") == []


def test_bang_before_multi_backtick_span_is_legal():
    """``!``cmd``` is not the injection marker; only a single-backtick run is."""
    assert scan("Not a preamble: !``date``\n") == []


def test_frontmatter_description_containing_the_marker_is_legal():
    text = "---\ndescription: explains the !`cmd` syntax to authors\n---\n\nBody.\n"
    assert scan(text) == []


def test_fence_info_string_that_merely_starts_with_bang_is_legal():
    text = "```!python\nprint('x')\n```\n"
    assert scan(text) == []


# --------------------------------------------------------------------------
# Fail-closed behaviour — an unparseable near-miss is not evidence of absence.
# --------------------------------------------------------------------------


def test_unterminated_inline_marker_raises():
    with pytest.raises(ValueError):
        scan("**Today:** !`date\n")


def test_unterminated_frontmatter_raises():
    with pytest.raises(ValueError):
        scan("---\ndescription: never closed\n")


# --------------------------------------------------------------------------
# Shared-recognizer parity — the drift class extractor.py documents.
# --------------------------------------------------------------------------


def test_fence_recognizer_parity_with_extractor():
    """This file must not become a fourth, divergent fence recognizer.

    extractor.py records that two disagreeing fence recognizers were a reachable
    security hole: ``str.strip()`` removes all Unicode whitespace while
    ``^[ \\t]*`` does not, so a fence indented with U+00A0 was a fence for one
    consumer and not the other. The gate duplicates the pattern rather than
    importing it (pre-commit gates in this repo import nothing from the package,
    so they still run when it is mid-refactor); this test is what makes the
    duplication safe.
    """
    extractor_src = (
        REPO_ROOT / "src" / "ai_governance_mcp" / "extractor.py"
    ).read_text(encoding="utf-8")
    match = re.search(r"^_FENCE_RE = re\.compile\((r\".*?\")\)", extractor_src, re.M)
    assert match, "could not locate _FENCE_RE in extractor.py"
    assert match.group(1) == 'r"^[ \\t]*(?:```|~~~)"'
    assert mod._FENCE_LINE_RE.pattern == r"^[ \t]*(?:```|~~~)"


def test_nbsp_indented_fence_is_refused_not_silently_skipped():
    """U+00A0 indentation is ambiguous, so the gate refuses the file.

    This is the drift class extractor.py documents, and here it is sharper
    than a disagreement between consumers. ``_FENCE_LINE_RE`` does not match
    a U+00A0-indented fence, so the line is not a fence — but its three
    backticks then pair as an ordinary inline code span, making everything
    up to the next such run opaque. A preamble hidden that way would be
    reported CLEAN, which is the one answer this gate must never give
    wrongly. So it fails closed instead.

    Ordinary-space indentation IS a fence; see
    ``test_detects_indented_fenced_preamble``.
    """
    nbsp = "\u00a0"
    text = nbsp + "```sh\n!`date`\n" + nbsp + "```\n"
    with pytest.raises(ValueError, match="ambiguous"):
        scan(text)


def test_exceptions_list_is_empty():
    """There are no exceptions, deliberately — see the script docstring.

    An exception re-opens 'which shell grammar is safe?', which is the
    unanswerable question the zero-preamble policy exists to avoid.

    Covers: FM-SKILL-EXECUTABLE-PREAMBLE
    """
    assert mod.EXCEPTIONS == frozenset()


def test_exit_0_on_clean_tree(tmp_path: Path):
    skill = tmp_path / ".claude" / "skills" / "clean" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\ndescription: x\n---\n\nRun `git status` when needed.\n")
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_exit_1_and_actionable_message_on_findings(tmp_path: Path):
    skill = tmp_path / "global-skills" / "dirty" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\ndescription: x\n---\n\n**Today:** !`date`\n")
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "SKILL.md:5" in result.stdout
    # The message must tell the author what to do instead, not merely refuse.
    assert "ordinary step" in result.stdout


def test_exit_3_when_no_skills_found(tmp_path: Path):
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3


def test_repo_tree_is_clean():
    """The whole point: after #356's fix, the real tree carries no preambles.

    This is the regression lock. It fails loudly while the fix is incomplete,
    which is correct — it is the acceptance condition for the policy arm.

    Covers: FM-SKILL-EXECUTABLE-PREAMBLE
    """
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_checker_is_wired_to_public_authoring_gate():
    """Covers: FM-SKILL-EXECUTABLE-PREAMBLE"""
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "python3 scripts/check-skill-preambles.py" in config
