"""Unit tests for scripts/check-public-release.py — the public-release leak-guard.

Part of the public/private two-repo split (RELEASE.md). The guard is fail-closed:
a public tree may contain ONLY allowlisted paths, no private domain/proprietary
content. Three layers: path-allowlist (always), content-denylist (with
--forbidden), structural-invariant (always). Exit 0 clean / 2 violation.

Mirrors tests/test_citation_check.py (subprocess + synthetic tree + exit-code
contract), so the guard is verified the same way the citation check is.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "check-public-release.py"
)

# A minimal allowlist covering the synthetic trees below.
ALLOWLIST = """\
src/**/* | engine
tests/**/* | tests
documents/constitution.md | meta
documents/.public-allowlist | this file
README.md | docs
"""

# Fake markers (NOT the real client/sibling names) so this test file carries no
# real proprietary strings and is itself publishable. The real markers live in the
# private-only documents/.release-forbidden.
FORBIDDEN = """\
\\bAcmeHotelCo\\b | fake client marker
\\bFAKEKPI\\b | fake hospitality KPI marker
fakesiblingrepo | fake sibling-repo marker
"""


def make_tree(
    tmp_path: Path,
    files: dict[str, str],
    *,
    allowlist: str = ALLOWLIST,
    forbidden: str | None = None,
) -> tuple[Path, Path | None]:
    """Build a synthetic repo tree. Returns (root, forbidden_path).

    `root` is a subdir of tmp_path; the denylist (if any) is written OUTSIDE root
    (mirroring reality — the private build script passes an absolute path to the
    private repo's documents/.release-forbidden, which is never in the published
    tree because it is not allowlisted).
    """
    root = tmp_path / "repo"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    (root / "documents").mkdir(parents=True, exist_ok=True)
    (root / "documents" / ".public-allowlist").write_text(allowlist, encoding="utf-8")
    fpath: Path | None = None
    if forbidden is not None:
        fpath = tmp_path / ".release-forbidden"  # outside root, as in production
        fpath.write_text(forbidden, encoding="utf-8")
    return root, fpath


def run_guard(
    root: Path, forbidden: Path | None = None
) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", str(SCRIPT_PATH), "--root", str(root)]
    if forbidden is not None:
        cmd += ["--forbidden", str(forbidden)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def test_clean_allowlisted_tree_passes(tmp_path: Path) -> None:
    root, _ = make_tree(
        tmp_path,
        {
            "src/ai_governance_mcp/config.py": "def discover_domains(): ...\n",
            "documents/constitution.md": "# Constitution\n",
            "README.md": "# Project\n",
        },
    )
    result = run_guard(root)
    assert result.returncode == 0, result.stderr


def test_non_allowlisted_private_file_fails(tmp_path: Path) -> None:
    """A domain title file is not allowlisted -> path-layer violation."""
    root, _ = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# Constitution\n",
            "documents/title-10-ai-coding.md": "# AI Coding domain\n",
        },
    )
    result = run_guard(root)
    assert result.returncode == 2
    assert "title-10-ai-coding.md" in result.stderr
    assert "path-allowlist" in result.stderr


def test_index_artifact_fails(tmp_path: Path) -> None:
    """A committed index artifact (domain plaintext/embeddings) is caught."""
    root, _ = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "index/content_embeddings.npy": "binary-ish",
        },
    )
    result = run_guard(root)
    assert result.returncode == 2
    assert "index/content_embeddings.npy" in result.stderr


def test_memory_file_fails(tmp_path: Path) -> None:
    root, _ = make_tree(
        tmp_path,
        {"documents/constitution.md": "# C\n", "SESSION-STATE.md": "private notes\n"},
    )
    result = run_guard(root)
    assert result.returncode == 2
    assert "SESSION-STATE.md" in result.stderr


def test_forbidden_content_caught_with_denylist(tmp_path: Path) -> None:
    """A proprietary string inside an allowlisted file -> content-layer violation."""
    root, fpath = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "tests/test_x.py": 'fixture = "Extract FAKEKPI from AcmeHotelCo data"\n',
        },
        forbidden=FORBIDDEN,
    )
    result = run_guard(root, forbidden=fpath)
    assert result.returncode == 2
    assert "forbidden-content" in result.stderr
    assert "tests/test_x.py" in result.stderr


def test_forbidden_content_not_scanned_without_denylist(tmp_path: Path) -> None:
    """Without --forbidden the content layer is off (public-CI mode)."""
    root, _ = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "tests/test_x.py": 'fixture = "FAKEKPI AcmeHotelCo"\n',
        },
    )
    result = run_guard(root)  # no --forbidden
    assert result.returncode == 0, result.stderr


def test_guard_script_excluded_from_content_scan(tmp_path: Path) -> None:
    """The guard script + allowlist legitimately name markers; the content scan
    excludes them by name (CONTENT_SCAN_EXCLUDED_NAMES) so they don't self-flag."""
    root, fpath = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            # An allowlisted file named like the guard, containing a marker:
            "scripts/check-public-release.py": "# pattern: \\bAcmeHotelCo\\b\n",
        },
        allowlist=ALLOWLIST + "scripts/**/* | release tooling\n",
        forbidden=FORBIDDEN,
    )
    result = run_guard(root, forbidden=fpath)
    assert result.returncode == 0, result.stderr


def test_structural_invariant_default_domains_fails(tmp_path: Path) -> None:
    """_default_domains in config.py is a re-leak vector -> invariant violation."""
    root, _ = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "src/ai_governance_mcp/config.py": (
                "def discover_domains(): ...\n"
                "def _default_domains():\n    return ['ai-coding', 'kmpd']\n"
            ),
        },
    )
    result = run_guard(root)
    assert result.returncode == 2
    assert "structural-invariant" in result.stderr
    assert "config.py" in result.stderr


def test_config_without_default_domains_passes(tmp_path: Path) -> None:
    root, _ = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "src/ai_governance_mcp/config.py": "def discover_domains(): ...\n",
        },
    )
    result = run_guard(root)
    assert result.returncode == 0, result.stderr


def test_missing_allowlist_errors(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    result = run_guard(tmp_path)
    assert result.returncode == 2
    assert "allowlist not found" in result.stderr


def test_git_dir_ignored(tmp_path: Path) -> None:
    """.git contents are skipped, not flagged as non-allowlisted."""
    root, _ = make_tree(
        tmp_path,
        {"documents/constitution.md": "# C\n", ".git/config": "[core]\n"},
    )
    result = run_guard(root)
    assert result.returncode == 0, result.stderr


def test_denylist_regex_with_alternation(tmp_path: Path) -> None:
    """A denylist regex containing `(a|b)` must parse (delimiter is ' | ', not '|')."""
    root, fpath = make_tree(
        tmp_path,
        {
            "documents/constitution.md": "# C\n",
            "tests/test_x.py": 'note = "FAKEKPI report attached"\n',
        },
        forbidden="FAKEKPI (report|summary|data) | contextual marker with alternation\n",
    )
    result = run_guard(root, forbidden=fpath)
    assert result.returncode == 2
    assert "forbidden-content" in result.stderr
    # And the inverse: a non-matching context passes (proves the regex compiled).
    root2, fpath2 = make_tree(
        tmp_path / "b",
        {
            "documents/constitution.md": "# C\n",
            "tests/test_x.py": 'note = "FAKEKPI dashboard"\n',
        },
        forbidden="FAKEKPI (report|summary|data) | contextual marker with alternation\n",
    )
    result2 = run_guard(root2, forbidden=fpath2)
    assert result2.returncode == 0, result2.stderr
