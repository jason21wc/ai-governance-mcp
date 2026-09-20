#!/usr/bin/env python3
"""Reject executable dynamic-context preambles in first-party ``SKILL.md`` files.

Per BACKLOG #356. A *preamble* is Claude Code's skill-load-time shell injection:
an inline ``!`cmd``` marker, or a fenced block whose info string is ``!``. Claude
Code executes these when the skill loads, before any instruction runs.

WHY THIS ENFORCES A REPOSITORY POLICY AND NOT CLAUDE'S GUARD
------------------------------------------------------------
Claude Code refuses to run a preamble it cannot prove stays inside a worktree,
and a refused preamble kills the whole slash command rather than degrading it.
So in a worktree-isolated session — which ``AGENTS.md`` requires of every
mutating session — a skill carrying an unprovable preamble is simply dead.

The obvious fix is a lint that predicts what the guard rejects. That fix does
not work, and the reason is measured, not assumed. Fourteen live probes from
inside a worktree session on Claude Code 2.1.250 found the guard ACCEPTS
multi-stage pipes, ``&&``/``||`` chains, parenthesized subshells, ``2>/dev/null``
redirects, tilde paths, bare ``$VAR``, and ``main..HEAD`` / ``main...HEAD``
refspecs — while REFUSING ``$(...)`` and backtick substitution, ``${VAR:-default}``
brace expansion, ``for`` loops, and ``@{u}..HEAD``. That last one is the proof:
``@{u}..HEAD`` contains no substitution, no braces-with-modifier and no loop, so
every "conservative shell grammar" that would have admitted the accepted forms
also admits ``@{u}..HEAD`` — which is refused. The reject surface is
argument-sensitive and version-sensitive, it lives in a closed-source host, and
``claude plugin validate .`` returned ``Validation passed`` on a tree whose
``/compliance-review`` was refused at load in the same worktree, so there is no
vendor oracle to defer to either.

Mirroring an unfalsifiable external validator produces a lint that silently
false-greens. So this gate does not model the guard at all. It enforces a rule
this repository owns and can prove:

    Skills may instruct the agent to acquire live context.
    Skill LOADING must not execute anything.

Anything a preamble used to compute is available as an ordinary tool call in the
skill body, where it can be split, retried, or degraded when it fails — the
recovery asymmetry that makes an all-or-nothing preamble the wrong container.
Lazy acquisition is also more correct: eagerly injected context goes stale across
midnight or a long session, and Codex renders ``!`cmd``` literally rather than
executing it (CFR Appendix N.4), so a preamble is not portable anyway.

There are no exceptions, deliberately. Every exception re-opens "which shell
grammar is safe?", which is the unanswerable question this design exists to
avoid. ``EXCEPTIONS`` below is empty and should stay that way; it exists so the
policy is one named constant rather than scattered conditionals.

FENCE RECOGNITION
-----------------
``_FENCE_LINE_RE`` is deliberately identical to ``extractor.py::_FENCE_RE``.
``extractor.py`` documents (at its ``CRITICAL PATTERNS ARE NEVER FENCE-EXEMPT``
note) that a *second, divergent* fence recognizer was a reachable security hole:
one recognizer used ``str.strip()`` and another ``^[ \\t]*``, so a fence indented
with U+00A0 was a fence for one consumer and not the other. The fix was one
recognizer for all consumers, and this file must not become the exception.

It is duplicated rather than imported on purpose: every pre-commit gate in this
repo (``check-citations.py``, ``check-volatile-pins.py``,
``check-commit-promises.py``, ``check_backlog_resurrection.py``) imports nothing
from ``ai_governance_mcp``, so a gate still runs when the package is mid-refactor
or uninstalled. ``tests/test_check_skill_preambles.py`` asserts the two patterns
are byte-identical, so the duplication cannot drift undetected.

Fence *length* and *info string* handling is layered on top of that shared
recognizer, because ``_FENCE_RE`` is only a toggle and CommonMark lets a longer
fence contain a shorter one.

Exit codes:
  0 — clean (no executable preambles)
  1 — findings (executable preambles present)
  2 — usage error
  3 — IO/structural error (unreadable file, malformed input)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Must stay byte-identical to extractor.py::_FENCE_RE — see module docstring.
# Enforced by tests/test_check_skill_preambles.py::test_fence_recognizer_parity.
_FENCE_LINE_RE = re.compile(r"^[ \t]*(?:```|~~~)")

# Splits a fence-opening line into its delimiter run and its info string.
_FENCE_PARTS_RE = re.compile(r"^[ \t]*(?P<delim>`{3,}|~{3,})(?P<info>.*)$")

# Deliberately LOOSER than _FENCE_LINE_RE: Python's ``\s`` matches Unicode
# whitespace (U+00A0 included), ``[ \t]`` does not. A line matching this but not
# _FENCE_LINE_RE is the exact ambiguity extractor.py records as a reachable
# hole — and here it is worse than a disagreement between consumers, because a
# non-fence line carrying three backticks pairs them as an ordinary code span,
# which makes the region opaque and hides any preamble inside it. Rather than
# guess which reading Claude Code uses, refuse the file. See _reject_ambiguous.
_AMBIGUOUS_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")

REPO_GLOBS = (".claude/skills/*/SKILL.md", "global-skills/*/SKILL.md")

# Intentionally empty. See "There are no exceptions, deliberately" above.
EXCEPTIONS: frozenset[str] = frozenset()

INLINE = "inline"
FENCED = "fenced"


@dataclass(frozen=True)
class Finding:
    """One executable preamble, located precisely enough to fix."""

    path: Path
    line: int  # 1-indexed
    column: int  # 1-indexed
    kind: str  # INLINE | FENCED
    command: str

    def render(self) -> str:
        shown = self.command if len(self.command) <= 90 else self.command[:87] + "..."
        return f"{self.path}:{self.line}:{self.column}: {self.kind} preamble: {shown}"


def _strip_frontmatter(text: str) -> tuple[str, int]:
    """Drop a leading YAML frontmatter block. Returns (body, lines_removed).

    Frontmatter is data, not markdown body, and a ``!`` inside a description
    field is not an executable preamble.
    """
    if not text.startswith("---"):
        return text, 0
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return text, 0
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[i + 1 :]), i + 1
    # Unterminated frontmatter: structurally malformed. Fail closed rather than
    # guess where the body starts.
    raise ValueError("unterminated YAML frontmatter")


# `_code_span_regions` lived here and is DELETED, not kept "in case".
#
# It paired CommonMark backtick runs so that a marker inside a code span could be
# exempted. That exemption is gone (see the inline pass below), which leaves the
# helper with no consumer — and a function whose docstring explains a policy the
# code no longer implements is worse than no function: the next reader takes the
# docstring for the rule. Its reasoning survives in git and in the comment at the
# inline pass, which records why the premise was false.


def _reject_ambiguous_fences(lines: list[str], line_offset: int, where: Path) -> None:
    """Refuse a file whose fence indentation is readable two ways.

    A line indented with U+00A0 (or any other non-``[ \\t]`` whitespace) before a
    ``` or ~~~ run is not a fence to this gate, but its backtick run still pairs
    as an inline code span — which would silently hide a preamble between it and
    the next such run. Since a hidden preamble is indistinguishable from an
    absent one, and absence is what this gate certifies, the honest response is
    to refuse rather than to report clean.
    """
    for idx, line in enumerate(lines):
        if _AMBIGUOUS_FENCE_RE.match(line) and not _FENCE_LINE_RE.match(line):
            raise ValueError(
                f"line {idx + 1 + line_offset}: fence-like line indented with "
                f"non-standard whitespace is ambiguous; use spaces or tabs "
                f"({where})"
            )


def _offset_to_line_col(text: str, offset: int, line_offset: int) -> tuple[int, int]:
    prefix = text[:offset]
    line = prefix.count("\n") + 1 + line_offset
    last_nl = prefix.rfind("\n")
    column = offset - last_nl if last_nl >= 0 else offset + 1
    return line, column


def find_executable_preambles(text: str, path: Path | None = None) -> list[Finding]:
    """Locate every executable preamble in one markdown document.

    Mechanism only — this function reports what it finds and takes no view on
    whether findings are allowed. The policy ("there must be none") lives in
    :func:`main`, so the scanner stays testable against fixtures independently
    of the rule it serves.
    """
    where = path or Path("<memory>")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    body, line_offset = _strip_frontmatter(text)

    findings: list[Finding] = []
    lines = body.split("\n")
    _reject_ambiguous_fences(lines, line_offset, where)

    # --- pass 1: fenced blocks -------------------------------------------
    # Walk fences to learn which lines are inside one, and flag any fence whose
    # info string is exactly "!". Longer fences may contain shorter ones, so a
    # fence closes only on a same-character run at least as long as its opener.
    inside = [False] * len(lines)
    open_delim: str | None = None
    open_len = 0
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if _FENCE_LINE_RE.match(line):
            parts = _FENCE_PARTS_RE.match(line)
            if parts is None:  # pragma: no cover - _FENCE_LINE_RE implies a match
                raise ValueError(f"fence line did not parse: {line!r}")
            delim = parts.group("delim")
            info = parts.group("info").strip()
            if open_delim is None:
                open_delim = delim[0]
                open_len = len(delim)
                if info == "!":
                    findings.append(
                        Finding(
                            path=where,
                            line=idx + 1 + line_offset,
                            column=1,
                            kind=FENCED,
                            command=_fenced_body(lines, idx),
                        )
                    )
                inside[idx] = True
            elif delim[0] == open_delim and len(delim) >= open_len and not info:
                inside[idx] = True
                open_delim = None
                open_len = 0
            else:
                inside[idx] = True
        else:
            inside[idx] = open_delim is not None
        idx += 1

    # --- pass 2: inline markers outside fences ---------------------------
    # Scan the non-fenced text as one string so a code span spanning a line
    # break is still opaque.
    masked = "\n".join(
        ("\x00" * len(line)) if inside[i] else line for i, line in enumerate(lines)
    )
    # A CODE SPAN DOES NOT DISARM THE MARKER. This pass used to skip any marker
    # inside one, on the reasoning that prose *documenting* the syntax is correct
    # work and "a gate that fires on correct work trains its own bypass".
    #
    # The premise was false, and `all-clear/SKILL.md` — the file this exemption was
    # written for, and named in the docstring below — is the proof. Its line 11 was
    # the only `!` in the whole skill, sat inside a double-backtick span, in a
    # sentence saying not to use the syntax. Invoking `/all-clear` produced:
    #
    #     Shell command failed for pattern "!`cmd`": command not found: cmd
    #
    # `cmd` appears nowhere else in the file, so Claude Code did not merely parse
    # the span — it extracted and EXECUTED the text inside it. Its preamble
    # extractor is raw-text; it has no CommonMark awareness for this gate to model.
    # The exemption was also the reason #356's two cleanup commits skipped that
    # file: the guard did not miss it, the guard excused it.
    #
    # Fenced examples stay legal — that is the `inside[i]` masking above, a
    # different mechanism from code spans, and its tests are unchanged.
    #
    # Scoped before removing: exactly one file repo-wide carried a spanned marker,
    # so this costs zero false positives. To document the syntax, spell it out
    # ("a `!` immediately followed by a backticked command") or put it in a fence.
    for match in re.finditer(r"!`", masked):
        bang = match.start()
        tick = bang + 1
        # The marker is `!` followed by a run of exactly one backtick; a longer
        # run is ordinary markdown, not an injection.
        run_end = tick
        while run_end < len(masked) and masked[run_end] == "`":
            run_end += 1
        if run_end - tick != 1:
            continue
        close = masked.find("`", run_end)
        if close == -1:
            raise ValueError(
                f"unterminated inline preamble marker at offset {bang} in {where}"
            )
        line, column = _offset_to_line_col(masked, bang, line_offset)
        findings.append(
            Finding(
                path=where,
                line=line,
                column=column,
                kind=INLINE,
                command=masked[run_end:close],
            )
        )

    findings.sort(key=lambda f: (f.line, f.column))
    return findings


def _fenced_body(lines: list[str], open_idx: int) -> str:
    collected: list[str] = []
    for line in lines[open_idx + 1 :]:
        if _FENCE_LINE_RE.match(line):
            break
        collected.append(line.strip())
    joined = "; ".join(part for part in collected if part)
    return joined or "(empty block)"


def discover(root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in REPO_GLOBS:
        found.extend(sorted(root.glob(pattern)))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fail if any first-party SKILL.md carries an executable preamble."
    )
    ap.add_argument("paths", nargs="*", type=Path, help="SKILL.md files to check.")
    ap.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Repo root for discovery."
    )
    args = ap.parse_args(argv)

    targets = args.paths or discover(args.root)
    if not targets:
        print("check-skill-preambles: no SKILL.md files found", file=sys.stderr)
        return 3

    findings: list[Finding] = []
    for path in targets:
        if path.name != "SKILL.md":
            continue
        if str(path) in EXCEPTIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"check-skill-preambles: cannot read {path}: {exc}", file=sys.stderr)
            return 3
        try:
            findings.extend(find_executable_preambles(text, path))
        except ValueError as exc:
            # Fail closed: something resembling a preamble that we cannot parse
            # is not evidence of absence.
            print(f"check-skill-preambles: {path}: {exc}", file=sys.stderr)
            return 3

    if not findings:
        return 0

    print("Executable preambles are not permitted in SKILL.md (BACKLOG #356).\n")
    for finding in findings:
        print(f"  {finding.render()}")
    print(
        "\nSkill loading must not execute anything. Move the command into the skill\n"
        "body as an ordinary step the agent runs when it needs the value — that\n"
        "form can be split, retried, or degraded when it fails, and a preamble\n"
        "cannot: Claude Code refuses the entire slash command instead.\n"
        "Rationale and the probe evidence: scripts/check-skill-preambles.py docstring."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
