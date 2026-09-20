#!/usr/bin/env python3
"""Reject early-closing consumers in pipelines inside pipefail-enabled hooks.

Under ``set -o pipefail``, a consumer that exits before reading its full input can
turn an otherwise successful decision into status 141 when the producer receives
SIGPIPE.  Claude hook harnesses interpret an unasserted deny as allow, so this is
an enforcement failure rather than a cosmetic shell error.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path


PIPEFAIL_SET = re.compile(r"(?m)^[ \t]*set\b[^\n#]*\bpipefail\b")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SED_QUIT = re.compile(r"(?:^|[;[:space:]])(?:[0-9$]+(?:,[0-9$]+)?)?q(?:[;[:space:]]|$)")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    command: str
    reason: str


def _is_quiet_grep(args: list[str]) -> bool:
    for arg in args:
        if arg == "--":
            return False
        if arg == "--quiet" or arg.startswith("--quiet="):
            return True
        if arg.startswith("-") and not arg.startswith("--") and "q" in arg[1:]:
            return True
    return False


def _awk_exits_early(args: list[str]) -> bool:
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"-v", "-F", "-f"}:
            i += 2
            continue
        if arg == "--":
            i += 1
            continue
        if arg.startswith("-") or ASSIGNMENT.match(arg):
            i += 1
            continue
        return re.search(r"\bexit\b", arg) is not None
    return False


def _sed_quits_early(args: list[str]) -> bool:
    scripts: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"-e", "--expression"} and i + 1 < len(args):
            scripts.append(args[i + 1])
            i += 2
            continue
        if arg.startswith("--expression="):
            scripts.append(arg.split("=", 1)[1])
        elif not arg.startswith("-"):
            scripts.append(arg)
            break
        i += 1
    return any(SED_QUIT.search(script) for script in scripts)


def _early_consumer(command: str, args: list[str]) -> str | None:
    base = Path(command).name
    if base == "head":
        return "head closes its input after the requested prefix"
    if base == "grep" and _is_quiet_grep(args):
        return "grep -q/--quiet closes its input after the first match"
    if base == "sed" and _sed_quits_early(args):
        return "sed q closes its input before end-of-stream"
    if base == "awk" and _awk_exits_early(args):
        return "awk exit closes its input before end-of-stream"
    return None


def scan_text(path: Path, text: str) -> list[Finding]:
    """Return unsafe pipeline consumers from one shell source file."""
    if not PIPEFAIL_SET.search(text):
        return []

    lexer = shlex.shlex(text, posix=True, punctuation_chars="|;&()")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    tokens: list[tuple[str, int]] = []
    try:
        # Iteration distinguishes a quoted empty-string token from EOF. A truthy
        # ``while get_token()`` loop stops at ``""`` and silently leaves the rest
        # of the hook unscanned — exactly the fail-open direction this checker
        # exists to prevent.
        for token in lexer:
            tokens.append((token, lexer.lineno))
    except ValueError as exc:
        raise ValueError(f"{path}: shell tokenization failed: {exc}") from exc

    findings: list[Finding] = []
    i = 0
    while i < len(tokens):
        token, line = tokens[i]
        if token not in {"|", "|&"}:
            i += 1
            continue

        i += 1
        while i < len(tokens) and (
            tokens[i][0] in {"!", "{"} or ASSIGNMENT.match(tokens[i][0])
        ):
            i += 1
        if i >= len(tokens):
            break

        command, command_line = tokens[i]
        i += 1
        args: list[str] = []
        while i < len(tokens) and tokens[i][0] not in {
            "|",
            "|&",
            "||",
            ";",
            "&",
            "&&",
            ")",
            "(",
        }:
            args.append(tokens[i][0])
            i += 1
        reason = _early_consumer(command, args)
        if reason:
            findings.append(Finding(path, command_line or line, command, reason))
    return findings


def scan_paths(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_text(path, path.read_text()))
    return findings


def _default_paths(repo: Path) -> list[Path]:
    return sorted((repo / ".claude" / "hooks").rglob("*.sh"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    paths = args.paths or _default_paths(args.repo)
    try:
        findings = scan_paths(paths)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"pipefail early-consumer check could not run: {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        print(
            f"{finding.path}:{finding.line}: {finding.command}: {finding.reason}; "
            "use a here-string/builtin matcher or a whole-stream preview consumer",
            file=sys.stderr,
        )
    if findings:
        print(
            f"FAIL: {len(findings)} unsafe pipefail pipeline consumer(s)",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: {len(paths)} hook script(s) contain no unsafe pipefail consumers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
