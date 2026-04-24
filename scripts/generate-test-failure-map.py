#!/usr/bin/env python3
"""Generate documents/test-failure-mode-map.md from test docstring annotations.

Walks tests/, harvests `Covers: <id>[, <id>...]` from test docstrings, joins
against documents/failure-mode-registry.md's YAML frontmatter, and emits a
markdown map grouped by registry entry.

Rot-immune: the map is derived every run, not hand-maintained. Annotations
referencing unknown registry IDs are surfaced in the output (they'll also be
caught by TestFailureModeCoverage lint). Entries without annotations are
listed under "unannotated" — this is expected for must_cover: false entries
and intentional for the must_cover: true entries flagged by the lint.

Usage:
    python3 scripts/generate-test-failure-map.py
"""

from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml


COVERS_RE = re.compile(r"Covers:\s*([A-Z][A-Z0-9_\-, ]+)", re.MULTILINE)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_registry(path: Path) -> tuple[dict[str, dict], str]:
    """Read registry markdown, return (entries_by_id, raw_yaml_header_text)."""
    text = path.read_text()
    # YAML frontmatter: between first two `---` lines.
    if not text.startswith("---\n"):
        raise SystemExit(f"registry missing YAML frontmatter: {path}")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise SystemExit(f"registry YAML frontmatter unterminated: {path}")
    header = text[4:end]
    meta = yaml.safe_load(header) or {}
    entries = meta.get("entries") or []
    by_id: dict[str, dict] = {}
    for entry in entries:
        eid = entry.get("id")
        if not eid:
            continue
        by_id[eid] = entry
    return by_id, header


def iter_test_files(tests_dir: Path) -> Iterable[Path]:
    for p in sorted(tests_dir.rglob("test_*.py")):
        yield p


def parse_covers(docstring: str) -> list[str]:
    """Extract `Covers: ID[, ID]` IDs from a docstring."""
    if not docstring:
        return []
    ids: list[str] = []
    for match in COVERS_RE.finditer(docstring):
        chunk = match.group(1)
        for raw in chunk.split(","):
            ident = raw.strip()
            # Trim trailing whitespace / periods / quotes
            ident = ident.rstrip(".\"' \t")
            if ident and ident.startswith("FM-"):
                ids.append(ident)
    return ids


def collect_annotations(tests_dir: Path) -> list[tuple[str, str, str, list[str]]]:
    """Return list of (relative_file, classname_or_empty, test_name, [covered_ids]).

    Direct-iteration design (not ast.walk): iterates the tree top-down once per
    file and tracks enclosing-class context explicitly. Avoids the O(N*M)
    quadratic blow-up where the annotation sweep expands. Handles module-level
    test functions + class-nested test methods; nested classes NOT traversed
    (pytest collects them but they're uncommon in this codebase; add explicit
    support if they appear).
    """
    out: list[tuple[str, str, str, list[str]]] = []
    for path in iter_test_files(tests_dir):
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(repo_root()).as_posix()
        for top in tree.body:
            if isinstance(top, ast.ClassDef):
                for method in top.body:
                    if isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) and method.name.startswith("test_"):
                        ids = parse_covers(ast.get_docstring(method) or "")
                        if ids:
                            out.append((rel, top.name, method.name, ids))
            elif isinstance(
                top, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and top.name.startswith("test_"):
                ids = parse_covers(ast.get_docstring(top) or "")
                if ids:
                    out.append((rel, "", top.name, ids))
    return out


def build_map(
    entries_by_id: dict[str, dict],
    annotations: list[tuple[str, str, str, list[str]]],
) -> tuple[dict[str, list[tuple[str, str, str]]], list[tuple[str, str, str, str]]]:
    """Group annotations by registry ID.

    Returns (covered_by_id, unknown_annotations).
      covered_by_id: {id: [(file, class, test), ...]}
      unknown_annotations: [(file, class, test, bad_id), ...]
    """
    covered: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    unknown: list[tuple[str, str, str, str]] = []
    for rel, classname, test, ids in annotations:
        for eid in ids:
            if eid in entries_by_id:
                covered[eid].append((rel, classname, test))
            else:
                unknown.append((rel, classname, test, eid))
    return covered, unknown


def format_map(
    entries_by_id: dict[str, dict],
    covered: dict[str, list[tuple[str, str, str]]],
    unknown: list[tuple[str, str, str, str]],
) -> str:
    lines: list[str] = []
    lines.append("# Test → Failure-Mode Coverage Map")
    lines.append("")
    lines.append(
        "**AUTO-GENERATED.** Do not edit. Regenerate via "
        "`python3 scripts/generate-test-failure-map.py`."
    )
    lines.append("")
    lines.append(
        "**Coverage reflects ANNOTATED tests only.** An empty cell does NOT mean "
        '"failure mode uncovered" — it means "no test carries a `Covers: <id>` '
        'annotation yet." Full annotation sweep deferred to BACKLOG; this map '
        "documents the state of the annotation convention, not the state of test "
        "coverage."
    )
    lines.append("")
    lines.append("**Source registry:** `documents/failure-mode-registry.md`")
    lines.append("")

    # Split entries into must_cover and advisory for readability.
    must_cover = [eid for eid, e in entries_by_id.items() if e.get("must_cover")]
    advisory = [eid for eid, e in entries_by_id.items() if not e.get("must_cover")]
    retired = [eid for eid, e in entries_by_id.items() if e.get("retired")]

    def write_section(title: str, ids: list[str]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not ids:
            lines.append("_(none)_")
            lines.append("")
            return
        for eid in sorted(ids):
            entry = entries_by_id[eid]
            desc = entry.get("description", "")
            tests = covered.get(eid, [])
            retired_date = entry.get("retired")
            badge = " **[RETIRED]**" if retired_date else ""
            lines.append(f"### `{eid}`{badge}")
            lines.append("")
            lines.append(f"> {desc}")
            lines.append("")
            if tests:
                for rel, classname, test in sorted(tests):
                    pretty = f"{classname}::{test}" if classname else test
                    lines.append(f"- `{rel}` → `{pretty}`")
            else:
                lines.append("_No annotated tests yet._")
            lines.append("")

    write_section("Must-Cover Entries", [e for e in must_cover if e not in retired])
    write_section("Advisory Entries", [e for e in advisory if e not in retired])
    if retired:
        write_section("Retired Entries", retired)

    if unknown:
        lines.append("## Unknown Annotations (registry miss — lint will flag)")
        lines.append("")
        for rel, classname, test, bad_id in sorted(unknown):
            pretty = f"{classname}::{test}" if classname else test
            lines.append(f"- `{rel}` → `{pretty}` cites unknown id `{bad_id}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    root = repo_root()
    registry_path = root / "documents" / "failure-mode-registry.md"
    tests_dir = root / "tests"
    out_path = root / "documents" / "test-failure-mode-map.md"

    if not registry_path.exists():
        print(f"registry not found: {registry_path}", file=sys.stderr)
        return 2

    entries_by_id, _ = load_registry(registry_path)
    annotations = collect_annotations(tests_dir)
    covered, unknown = build_map(entries_by_id, annotations)
    out_text = format_map(entries_by_id, covered, unknown)
    out_path.write_text(out_text)
    print(
        f"wrote {out_path.relative_to(root)}: "
        f"{len(entries_by_id)} registry entries, "
        f"{sum(len(v) for v in covered.values())} annotations across "
        f"{len({a for a_list in covered.values() for a in a_list})} tests, "
        f"{len(unknown)} unknown-id annotations"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
