"""Parity tests for scaffold_project output vs framework's own published kit.

Closes F-C-03 (Cohort 5 Session 5-2, v5.0.6).

Source of truth: `documents/title-10-ai-coding-cfr.md` §1.5.2 Standard Kit
enumeration — the CFR's published list of required files for Standard-tier
projects. NOT adopter CLAUDE.md (which is tool-specific overlay per §1.5.5).

Design:
- Parse §1.5.2 Standard Kit table at test runtime (auto-updates when CFR
  changes; no hardcoded file list to drift)
- Compare against `SCAFFOLD_STANDARD_EXTRAS["code"]` output
- Bidirectional assertion: scaffold output = §1.5.2 kit + CLAUDE.md overlay
  (the +1 CLAUDE.md is documented in §1.5.5 as a tool-specific addition)

Re-evaluation trigger: if CFR §1.5.2 changes format (e.g., moves from a
markdown table to prose), this test's parser will fail loudly — update the
parser, do not silently pin to a hardcoded list.
"""

from __future__ import annotations

import re
from pathlib import Path


from ai_governance_mcp.server import SCAFFOLD_STANDARD_EXTRAS


# CLAUDE.md is a §1.5.5 tool-specific overlay, not a §1.5.2 Standard Kit entry.
# Scaffold adds it for Claude Code adopters; it is excluded from the parity
# comparison against the §1.5.2 source of truth.
_OVERLAY_FILES = frozenset({"CLAUDE.md"})


def _cfr_path() -> Path:
    """Locate the AI Coding CFR document."""
    return (
        Path(__file__).resolve().parent.parent
        / "documents"
        / "title-10-ai-coding-cfr.md"
    )


def _parse_standard_kit_files() -> list[str]:
    """Parse CFR §1.5.2 Standard Kit table, returning the file list.

    Returns the `Additional File` column values from the markdown table under
    the §1.5.2 heading, preserving order. If the CFR structure changes such
    that the parser can't locate the section or table, raises explicitly —
    silent failure would hide drift.
    """
    content = _cfr_path().read_text()
    section_match = re.search(
        r"^### 1\.5\.2 Standard Kit.*?(?=^### 1\.5\.3)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not section_match:
        raise RuntimeError(
            "Could not locate §1.5.2 Standard Kit section in CFR. "
            "Parser expects heading `### 1.5.2 Standard Kit` followed by "
            "content up to `### 1.5.3`. Update parser if CFR structure changed."
        )
    section = section_match.group(0)
    files: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        first = cells[0]
        if first and not first.startswith("-") and first != "Additional File":
            files.append(first)
    if not files:
        raise RuntimeError(
            "Parsed §1.5.2 Standard Kit section but found zero file entries. "
            "Table structure may have changed; update parser."
        )
    return files


def _scaffold_code_files() -> list[str]:
    """Return the filenames SCAFFOLD_STANDARD_EXTRAS produces for code projects."""
    return [name for (name, _content) in SCAFFOLD_STANDARD_EXTRAS["code"]]


class TestScaffoldParityWithCFR152:
    """F-C-03: scaffold_project output must match CFR §1.5.2 Standard Kit."""

    def test_cfr_152_parser_finds_files(self) -> None:
        """Parser successfully extracts file list from CFR §1.5.2."""
        files = _parse_standard_kit_files()
        assert files, "CFR §1.5.2 Standard Kit parse returned empty list"
        # Sanity check: Standard Kit currently has 4 files (per §1.5.2 text
        # "Total: 8 files = 4 core + 4 standard additions"). Failing here means
        # either the CFR changed intentionally (update expected count or
        # remove this assertion) or the parser drifted.
        assert len(files) == 4, (
            f"Expected 4 files in §1.5.2 Standard Kit table, got {len(files)}: {files}"
        )

    def test_scaffold_covers_cfr_152_kit(self) -> None:
        """Every file in CFR §1.5.2 Standard Kit is produced by scaffold (superset)."""
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        missing = cfr_kit - scaffold
        assert not missing, (
            f"Scaffold is missing files from CFR §1.5.2 Standard Kit: {missing}. "
            f"Scaffold emits: {sorted(scaffold)}. "
            f"CFR §1.5.2 requires: {sorted(cfr_kit)}."
        )

    def test_scaffold_has_no_extra_files_beyond_overlay(self) -> None:
        """Scaffold emits nothing beyond §1.5.2 + approved overlays (subset)."""
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        extras = scaffold - cfr_kit - _OVERLAY_FILES
        assert not extras, (
            f"Scaffold emits files not in CFR §1.5.2 and not an approved "
            f"overlay: {extras}. Either add the file to §1.5.2 (if it "
            f"should be kit-standard) or to _OVERLAY_FILES in this test "
            f"(if it's a documented §1.5.5 overlay like CLAUDE.md)."
        )

    def test_scaffold_parity_is_bidirectional(self) -> None:
        """Bidirectional assertion: scaffold = §1.5.2 kit + approved overlays.

        Equivalent to test_scaffold_covers_cfr_152_kit +
        test_scaffold_has_no_extra_files_beyond_overlay combined. Kept as a
        distinct test so a single assertion documents the full invariant.
        """
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        expected = cfr_kit | _OVERLAY_FILES
        assert scaffold == expected, (
            f"Scaffold/CFR §1.5.2 parity violated.\n"
            f"  Scaffold output:  {sorted(scaffold)}\n"
            f"  Expected (CFR §1.5.2 + overlays): {sorted(expected)}\n"
            f"  Missing from scaffold: {expected - scaffold}\n"
            f"  Extra in scaffold:     {scaffold - expected}"
        )
