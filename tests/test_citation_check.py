"""Unit tests for scripts/check-citations.py — the citation-form check.

Per BACKLOG #144. The script enforces `rules-of-procedure.md` §9.8.9
Citation Discipline by rejecting bare `<file>.md:<line-number>` citations
outside an explicit allowlist, forcing authors toward stable `§X.Y.Z`
section-anchor citations that don't drift when content shifts.

Background: BACKLOG #100's 6-commit arc hit the line-citation drift class
twice (Commit 2's SSOT note shifted Article header lines +2; Commit 4
fold-in had to correct again). The contrarian-reviewer finding that
prompted this script's design is that detecting drift in a deprecated
form *legitimizes the form*; forbid-and-migrate ends the failure class.

Test coverage — 13 cases:
  Forbid path (3):
    test_rejects_bare_line_citation
    test_rejects_range_form
    test_rejects_multi_cite_form
  Accept path (3):
    test_accepts_section_anchor_form
    test_accepts_hybrid_form
    test_accepts_allowlisted_citation
  File-scope exclusion (1):
    test_excludes_archive_files
  Section-scope exclusion (3):
    test_excludes_changelog_section
    test_excludes_version_history_section
    test_excludes_historical_amendments_section
  Output / exit code contract (3):
    test_emits_actionable_error_message
    test_exit_code_2_on_failures
    test_exit_code_0_on_clean_corpus
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check-citations.py"


def run_check(root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the citation-check script against a synthetic corpus root.

    Returns the CompletedProcess with stdout/stderr captured as text.
    """
    return subprocess.run(
        ["python3", str(SCRIPT_PATH), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=10,
    )


def make_corpus(
    tmp_path: Path,
    *,
    files: dict[str, str],
    allowlist: list[str] | None = None,
) -> Path:
    """Build a synthetic corpus root.

    `files` maps repo-relative path → file content. Required structural dirs
    are created automatically. If `allowlist` is provided, it's written to
    `documents/.citation-allowlist` (one entry per line).
    """
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "documents").mkdir()
    (root / "workflows").mkdir()

    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    if allowlist is not None:
        (root / "documents" / ".citation-allowlist").write_text(
            "\n".join(allowlist) + "\n"
        )

    return root


# ---------------------------------------------------------------------------
# Forbid path — bare line-number citations are rejected
# ---------------------------------------------------------------------------


def test_rejects_bare_line_citation(tmp_path: Path) -> None:
    """`constitution.md:177` (single line) is rejected."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": "# Foo\n\nSee `constitution.md:177` for details.\n",
        },
    )
    result = run_check(root)
    assert result.returncode == 2
    assert "constitution.md:177" in result.stderr


def test_rejects_range_form(tmp_path: Path) -> None:
    """`constitution.md:177-180` (line range) is rejected."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": "# Foo\n\nSee `constitution.md:177-180` here.\n",
        },
    )
    result = run_check(root)
    assert result.returncode == 2
    assert "constitution.md:177-180" in result.stderr


def test_rejects_multi_cite_form(tmp_path: Path) -> None:
    """`constitution.md:177/424/629/816` (slash-separated multi-cite) is rejected."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nArticles: `constitution.md:177/424/629/816`.\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 2
    assert "constitution.md:177/424/629/816" in result.stderr


# ---------------------------------------------------------------------------
# Accept path — §-anchor and allowlisted citations pass
# ---------------------------------------------------------------------------


def test_accepts_section_anchor_form(tmp_path: Path) -> None:
    """`constitution.md §Bill of Rights` (no line number) passes."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nSee `constitution.md §Bill of Rights` for the S-Series header.\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_accepts_hybrid_form(tmp_path: Path) -> None:
    """Hybrid `constitution.md §Bill of Rights (F-P2-04 Q7 PASS block)` passes.

    Per §9.8.9 rule 2, parenthetical block-name inside a §-anchored citation
    is allowed because the §-anchor is the stable reference; the block name
    locates the discrete sub-block.
    """
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nSee `constitution.md §Bill of Rights (F-P2-04 Q7 PASS block)`.\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_accepts_allowlisted_citation(tmp_path: Path) -> None:
    """A bare `file.md:N` citation listed in `.citation-allowlist` is allowed."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": "# Foo\n\nSee `constitution.md:99` (legacy).\n",
        },
        allowlist=[
            "# documents/.citation-allowlist",
            "# Format: <citation> | <reason> | <session>",
            "constitution.md:99 | spans non-section content | session-138",
        ],
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# File-scope exclusion
# ---------------------------------------------------------------------------


def test_excludes_archive_files(tmp_path: Path) -> None:
    """Citations under `documents/archive/` are not scanned."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/archive/old.md": (
                "# Old\n\nLegacy citation `constitution.md:177` (frozen).\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# Section-scope exclusion — historical / changelog headings are not scanned
# ---------------------------------------------------------------------------


def test_excludes_changelog_section(tmp_path: Path) -> None:
    """Citations under `## Changelog` heading are not scanned."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nNormative content (no citations).\n\n"
                "## Changelog\n\n"
                "| v1 | 2026-01-01 | constitution.md:177 historical entry |\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_excludes_version_history_section(tmp_path: Path) -> None:
    """Citations under `## Version History` heading are not scanned."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nNormative content.\n\n"
                "## Version History\n\n"
                "| v1 | 2026-01-01 | constitution.md:998 historical citation |\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_excludes_historical_amendments_section(tmp_path: Path) -> None:
    """Citations under `## Historical Amendments` heading are not scanned.

    constitution.md uses this heading for past amendment audit logs which
    contain by-design historical citations to past line numbers. The
    section-exclusion match is case-insensitive substring on the H2 title.
    """
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nNormative content.\n\n"
                "## Historical Amendments (Constitutional History)\n\n"
                "*   **H1 (BLOCKING):** `rules-of-procedure.md:4370` past audit finding.\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# Output / exit code contract
# ---------------------------------------------------------------------------


def test_emits_actionable_error_message(tmp_path: Path) -> None:
    """Failure stderr names file:line of source, the offending citation,
    points at §9.8.9, and tells the author about the allowlist."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": "# Foo\n\nSee `constitution.md:177` here.\n",
        },
    )
    result = run_check(root)
    assert result.returncode == 2
    err = result.stderr
    # Source-location anchor
    assert "documents/foo.md" in err
    # The offending citation echoed back
    assert "constitution.md:177" in err
    # Pointer to the discipline rule
    assert "9.8.9" in err
    # Allowlist guidance
    assert ".citation-allowlist" in err


def test_exit_code_2_on_failures(tmp_path: Path) -> None:
    """Script exits 2 (not 1) when violations are found.

    Exit 2 matches the convention in `scripts/generate-test-failure-map.py`
    and `scripts/analyze_compliance.py` for tooling-detected failures —
    distinct from exit 1 (Python uncaught exception).
    """
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": "# Foo\n\nBad: `constitution.md:177`.\n",
        },
    )
    result = run_check(root)
    assert result.returncode == 2


def test_exit_code_0_on_clean_corpus(tmp_path: Path) -> None:
    """Script exits 0 when no bare `file.md:N` citations remain."""
    root = make_corpus(
        tmp_path,
        files={
            "documents/foo.md": (
                "# Foo\n\nSee `constitution.md §Bill of Rights` for header.\n"
            ),
            "BACKLOG.md": (
                "# Backlog\n\nItem references `rules-of-procedure.md §9.8.9`.\n"
            ),
            "workflows/EXAMPLE.md": (
                "# Example workflow\n\nNo line-form citations here.\n"
            ),
        },
    )
    result = run_check(root)
    assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# Sanity — script exists at the expected path
# ---------------------------------------------------------------------------


def test_script_path_resolves() -> None:
    """The constant SCRIPT_PATH points at scripts/check-citations.py.

    Sanity check; no executability assertion (script is `python3 <path>`,
    not a chmod +x entry point).
    """
    assert SCRIPT_PATH.name == "check-citations.py"
    assert SCRIPT_PATH.parent.name == "scripts"
