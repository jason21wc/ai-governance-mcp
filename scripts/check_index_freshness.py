"""Check that the search index matches documents/ source counts.

Compares principles and methods per domain between the source documents
and the built index. References are excluded — the reference library path
is environment-dependent (contrarian review, session-274).

Exit codes:
  0 — in sync (source counts match index)
  1 — stale (mismatch detected)
  2 — usage error
  3 — IO/structural error (index missing, etc.)

Part of the derive-and-check pattern (gen_quick_reference.py, gen_sbom.py).
Wired into scripts/check.sh. BACKLOG #206.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKED_KINDS = ("principles", "methods")


def _make_settings():
    from ai_governance_mcp.config import Settings

    return Settings()


def source_composition(settings) -> dict[tuple[str, str], int]:
    """Parse documents/ and return {(domain, kind): count} for principles/methods."""
    from ai_governance_mcp.extractor import DocumentExtractor

    extractor = DocumentExtractor(settings)
    comp: dict[tuple[str, str], int] = {}
    for dc in extractor.domains:
        domain_idx = extractor._extract_domain(dc)
        for kind in CHECKED_KINDS:
            items = getattr(domain_idx, kind, None) or []
            comp[(dc.name, kind)] = len(items)
    return comp


def index_composition(index_path: Path) -> dict[tuple[str, str], int]:
    """Load global_index.json and return {(domain, kind): count} for principles/methods."""
    from ai_governance_mcp.extractor import DocumentExtractor

    index_json = json.loads((index_path / "global_index.json").read_text())
    full = DocumentExtractor._composition_from_json(index_json)
    return {k: v for k, v in full.items() if k[1] in CHECKED_KINDS}


def compare(
    source: dict[tuple[str, str], int],
    index: dict[tuple[str, str], int],
) -> list[tuple[str, str, int, int]]:
    """Compare source and index compositions.

    Returns list of (domain, kind, source_count, index_count) for mismatches.
    """
    mismatches = []
    for key in sorted(set(source) | set(index)):
        s = source.get(key, 0)
        i = index.get(key, 0)
        if s != i:
            mismatches.append((key[0], key[1], s, i))
    return mismatches


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    valid_flags = {"--check"}
    unknown = set(argv) - valid_flags
    if unknown:
        print(f"Unknown flags: {unknown}", file=sys.stderr)
        print(f"Usage: {Path(sys.argv[0]).name} --check", file=sys.stderr)
        return 2

    check_mode = "--check" in argv

    try:
        settings = _make_settings()
    except Exception as e:
        print(f"Cannot load settings: {e}", file=sys.stderr)
        return 3

    index_file = settings.index_path / "global_index.json"
    if not index_file.exists():
        print(f"Index not found: {index_file}", file=sys.stderr)
        return 3

    try:
        src = source_composition(settings)
        idx = index_composition(settings.index_path)
    except Exception as e:
        print(f"Error computing compositions: {e}", file=sys.stderr)
        return 3

    mismatches = compare(src, idx)

    all_keys = sorted(set(src) | set(idx))
    for key in all_keys:
        s = src.get(key, 0)
        i = idx.get(key, 0)
        status = "OK" if s == i else "STALE"
        print(f"  {key[0]:20s} {key[1]:12s}  source={s:3d}  index={i:3d}  {status}")

    if mismatches:
        print(
            f"\n{len(mismatches)} mismatch(es) — rebuild: "
            "python -m ai_governance_mcp.extractor"
        )
        return 1 if check_mode else 0

    print("\nIndex is fresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
