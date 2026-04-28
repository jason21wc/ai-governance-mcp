#!/usr/bin/env python3
"""Citation form check — rejects bare `<file>.md:<line>` citations.

Per `rules-of-procedure.md` §9.8.9 Citation Discipline (v3.31.3, 2026-04-28):
prefer `§X.Y.Z` section anchors over line numbers; use `§X.Y.Z (line N)`
hybrid form for specific blocks; treat line-only citations as drift-vulnerable.

This script enforces the discipline by REJECTING new bare `file.md:N` citations
in scanned content. Existing citations needing to remain in line-number form
are listed in `documents/.citation-allowlist` with a documented reason.

Background: BACKLOG #100's 6-commit arc hit citation drift twice in the same
arc; documentation guidance alone (the lesson + §9.8.9 subsection) was not
sufficient to prevent recurrence. Per `meta-core-systemic-thinking`: structural
prevention (this check) ends the failure class. Per the contrarian-reviewer
challenge that produced this design: a *detector* for the deprecated form
legitimizes it; *forbid-and-migrate* is the structural fix.

Filed: BACKLOG #144 (closed session-138).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CITATION_PATTERN = re.compile(r"[a-zA-Z0-9_-]+\.md:[0-9]+(?:[-/][0-9]+)*")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

EXCLUDED_HEADING_SUBSTRINGS = (
    "version history",
    "changelog",
    "historical amendments",
    "closed items",
    "archive",
)

INCLUDED_PATH_PATTERNS = (
    "documents/*.md",
    "BACKLOG.md",
    "workflows/*.md",
)

EXCLUDED_PATH_SUBSTRINGS = (
    "documents/archive/",
    "documents/migration/",
    "documents/test-failure-mode-map.md",
)

ALLOWLIST_RELATIVE_PATH = "documents/.citation-allowlist"


@dataclass(frozen=True)
class Violation:
    source_path: Path
    source_line: int
    citation: str

    def format(self, root: Path, allowlist_path: Path) -> str:
        rel_source = self.source_path.relative_to(root)
        rel_allowlist = allowlist_path.relative_to(root)
        return (
            f"{rel_source}:{self.source_line}: bare line-number citation "
            f"`{self.citation}` is forbidden.\n"
            f"  Use `§X.Y.Z` section-anchor form per "
            f"`rules-of-procedure.md` §9.8.9 (Citation Discipline), e.g.:\n"
            f"    `constitution.md §Bill of Rights` (drop the line number), or\n"
            f"    `constitution.md §Bill of Rights (F-P2-04 Q7 PASS block)` "
            f"(hybrid form).\n"
            f"  If a line-number citation is genuinely required, add it to "
            f"`{rel_allowlist}` with a documented reason."
        )


def load_allowlist(allowlist_path: Path) -> set[str]:
    """Read the allowlist file and return the set of permitted citations.

    Format: `<citation> | <reason> | <session>` per line. Comments (`#`) and
    blank lines are skipped. If the file is missing, returns an empty set.
    """
    if not allowlist_path.exists():
        return set()

    permitted: set[str] = set()
    for raw_line in allowlist_path.read_text().splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        citation = stripped.split("|", 1)[0].strip()
        if citation:
            permitted.add(citation)
    return permitted


def is_excluded_heading(heading_text: str) -> bool:
    """Return True if a heading title contains any excluded substring (case-insensitive)."""
    lower = heading_text.lower()
    return any(s in lower for s in EXCLUDED_HEADING_SUBSTRINGS)


def collect_files(root: Path) -> list[Path]:
    """Walk the corpus root and return files in scope, sorted for stability."""
    paths: set[Path] = set()
    for pattern in INCLUDED_PATH_PATTERNS:
        for p in root.glob(pattern):
            if p.is_file():
                paths.add(p)

    def is_excluded(p: Path) -> bool:
        rel = p.relative_to(root).as_posix()
        return any(sub in rel for sub in EXCLUDED_PATH_SUBSTRINGS)

    return sorted(p for p in paths if not is_excluded(p))


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return (line_number, citation) tuples for every bare citation in the
    file, skipping lines under excluded headings.

    Heading context is tracked at any depth (H1-H6); an H2 "## Version History"
    excludes everything until the next H1 or H2 at or above its depth.
    """
    violations: list[tuple[int, str]] = []
    excluded_depth: int | None = None

    for idx, line in enumerate(path.read_text().splitlines(), start=1):
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            depth = len(heading_match.group(1))
            title = heading_match.group(2)
            if excluded_depth is not None and depth <= excluded_depth:
                excluded_depth = None
            if excluded_depth is None and is_excluded_heading(title):
                excluded_depth = depth
            continue

        if excluded_depth is not None:
            continue

        for match in CITATION_PATTERN.finditer(line):
            violations.append((idx, match.group(0)))

    return violations


def find_violations(root: Path) -> list[Violation]:
    allowlist_path = root / ALLOWLIST_RELATIVE_PATH
    permitted = load_allowlist(allowlist_path)

    out: list[Violation] = []
    for path in collect_files(root):
        for line_no, citation in scan_file(path):
            if citation in permitted:
                continue
            out.append(
                Violation(source_path=path, source_line=line_no, citation=citation)
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject bare <file>.md:<line> citations per §9.8.9 Citation Discipline.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Corpus root (default: repo root inferred from script location).",
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.exists():
        print(f"error: corpus root not found: {root}", file=sys.stderr)
        return 2

    allowlist_path = root / ALLOWLIST_RELATIVE_PATH
    violations = find_violations(root)

    if not violations:
        return 0

    for v in violations:
        print(v.format(root, allowlist_path), file=sys.stderr)
    print(
        f"\n{len(violations)} citation violation(s) found. "
        f"See `rules-of-procedure.md` §9.8.9 for guidance.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
