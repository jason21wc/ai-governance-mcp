#!/usr/bin/env python3
"""Public-release leak-guard — fail-closed check that a tree contains ONLY
public-allowlisted content, no private/domain/proprietary material.

Part of the public/private two-repo split (RELEASE.md). The private repo is the
primary; the public repo is an allowlist extraction containing engine +
meta-framework + infra only — no subject-matter domains, no third-party
proprietary content. Publishing is an L3 external-irreversible action
(`multi-autonomous-action-blast-radius-classification`); this guard is the
structural compensating control, run both in the private build script (before
any push) and in the public repo's own CI.

Mirrors scripts/check-citations.py (allowlist file + exit 0/2 + stdlib only).

Three layers:
  (a) PATH ALLOWLIST (fail-closed, always): every file in the tree must match a
      glob in documents/.public-allowlist, else it is a violation. Catches stray
      private FILES (title-*.md, index/*.npy, reference-library/ai-coding, memory
      files) — anything not consciously allowlisted.
  (b) CONTENT DENYLIST (only with --forbidden): regex-scan allowlisted text files
      for proprietary strings that leaked INTO an otherwise-public file. The
      denylist (documents/.release-forbidden) is PRIVATE-ONLY and supplied by the
      private build script; the public CI does not run this layer (shipping the
      denylist would leak the very names it lists).
  (c) STRUCTURAL INVARIANT (always): src/ai_governance_mcp/config.py must not
      define `_default_domains` — that function enumerates the private domains and
      is one git-revert away from re-leaking their descriptions, which the content
      denylist (string-based) cannot see. The de-domain transform deletes it; this
      asserts the deletion held.

Exit 0 = clean; 2 = violation(s) or error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWLIST_RELATIVE_PATH = "documents/.public-allowlist"
CONFIG_RELATIVE_PATH = "src/ai_governance_mcp/config.py"
DEFAULT_DOMAINS_MARKER = "def _default_domains"

# Files excluded from the CONTENT scan because they legitimately name the
# forbidden markers (the denylist, the allowlist, and this guard itself).
CONTENT_SCAN_EXCLUDED_NAMES = frozenset(
    {".release-forbidden", ".public-allowlist", "check-public-release.py"}
)

# Extensions skipped by the content scan (binary / embeddings / images).
BINARY_SUFFIXES = frozenset(
    {
        ".npy",
        ".npz",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".pdf",
        ".ico",
        ".woff",
        ".woff2",
        ".pyc",
        ".so",
        ".bin",
        ".lock",
    }
)

# Directories never walked (VCS / build / venv noise).
SKIP_DIR_PARTS = frozenset({".git", "__pycache__", ".pytest_cache", ".ruff_cache"})


@dataclass(frozen=True)
class Violation:
    layer: str
    path: str
    detail: str

    def format(self) -> str:
        return f"[{self.layer}] {self.path}: {self.detail}"


def _parse_pipe_file(path: Path) -> list[str]:
    """Return the first field of each non-comment line.

    Delimiter is ' | ' (space-pipe-space), NOT a bare '|', so a denylist regex may
    contain alternation `(a|b)` without the reason-splitter eating it. Globs and
    bare patterns (no ' | reason') return the whole stripped line.
    """
    if not path.exists():
        return []
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        field = stripped.split(" | ", 1)[0].strip()
        if field:
            out.append(field)
    return out


def load_allowlist(root: Path) -> set[Path]:
    """Expand the allowlist globs into the concrete set of permitted files."""
    allowed: set[Path] = set()
    for glob in _parse_pipe_file(root / ALLOWLIST_RELATIVE_PATH):
        for p in root.glob(glob):
            if p.is_file():
                allowed.add(p.resolve())
    return allowed


def load_forbidden(path: Path) -> list[tuple[re.Pattern[str], str]]:
    """Load (compiled-regex, raw) pairs from a denylist file (case-insensitive)."""
    out: list[tuple[re.Pattern[str], str]] = []
    for raw in _parse_pipe_file(path):
        try:
            out.append((re.compile(raw, re.IGNORECASE), raw))
        except re.error as exc:  # pragma: no cover - guards malformed denylist
            print(f"error: bad denylist regex {raw!r}: {exc}", file=sys.stderr)
    return out


def walk_files(root: Path) -> list[Path]:
    """All files under root, skipping VCS/build dirs, sorted for stability."""
    out: list[Path] = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIR_PARTS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            out.append(p)
    return sorted(out)


def check_path_allowlist(root: Path, allowed: set[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for p in walk_files(root):
        if p.resolve() not in allowed:
            violations.append(
                Violation(
                    "path-allowlist",
                    p.relative_to(root).as_posix(),
                    "not in documents/.public-allowlist (private by default)",
                )
            )
    return violations


def check_forbidden_content(
    root: Path, allowed: set[Path], forbidden: list[tuple[re.Pattern[str], str]]
) -> list[Violation]:
    violations: list[Violation] = []
    for p in sorted(allowed):
        if p.name in CONTENT_SCAN_EXCLUDED_NAMES:
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for pattern, raw in forbidden:
            if pattern.search(text):
                violations.append(
                    Violation("forbidden-content", rel, f"matches denylist /{raw}/")
                )
    return violations


def check_structural_invariant(root: Path) -> list[Violation]:
    config = root / CONFIG_RELATIVE_PATH
    if config.exists() and DEFAULT_DOMAINS_MARKER in config.read_text(
        encoding="utf-8", errors="replace"
    ):
        return [
            Violation(
                "structural-invariant",
                CONFIG_RELATIVE_PATH,
                f"contains `{DEFAULT_DOMAINS_MARKER}` — de-domain transform must "
                "remove it (it enumerates private domains)",
            )
        ]
    return []


def find_violations(root: Path, forbidden_path: Path | None) -> list[Violation]:
    allowed = load_allowlist(root)
    violations = check_path_allowlist(root, allowed)
    violations += check_structural_invariant(root)
    if forbidden_path is not None:
        forbidden = load_forbidden(forbidden_path)
        violations += check_forbidden_content(root, allowed, forbidden)
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed public-release leak-guard (path allowlist + "
        "optional content denylist + structural invariant).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Tree to check (default: repo root inferred from script location).",
    )
    parser.add_argument(
        "--forbidden",
        type=Path,
        default=None,
        help="Optional PRIVATE content-denylist file (enables the content layer).",
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.exists():
        print(f"error: root not found: {root}", file=sys.stderr)
        return 2
    if not (root / ALLOWLIST_RELATIVE_PATH).exists():
        print(
            f"error: allowlist not found at {root / ALLOWLIST_RELATIVE_PATH}",
            file=sys.stderr,
        )
        return 2

    violations = find_violations(root, args.forbidden)
    if not violations:
        return 0

    for v in violations:
        print(v.format(), file=sys.stderr)
    print(
        f"\n{len(violations)} public-release violation(s) found. "
        f"Tree is NOT safe to publish. See RELEASE.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
