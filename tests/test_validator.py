"""Tests for cross-reference validator + failure-mode-registry lint."""

import ast
import re
from pathlib import Path

import pytest
import yaml

from ai_governance_mcp.validator import (
    extract_constitution_principles,
    extract_derives_from_references,
    find_fuzzy_match,
    is_template_placeholder,
    normalize_principle_name,
    build_principle_index,
)


class TestExtractConstitutionPrinciples:
    """Tests for extracting principle names from constitution."""

    def test_extracts_h3_headings(self):
        content = """
### Context Engineering
**Definition**
Some content here.

### Single Source of Truth
**Definition**
More content.
"""
        principles = extract_constitution_principles(content)
        assert "Context Engineering" in principles
        assert "Single Source of Truth" in principles

    def test_excludes_non_principle_headings(self):
        content = """
### Framework Overview
Not a principle.

### Context Engineering
**Definition**
A real principle.

### How the AI Applies This
Content.
"""
        principles = extract_constitution_principles(content)
        assert "Context Engineering" in principles
        assert "Framework Overview" not in principles
        assert "How the AI Applies This" not in principles


class TestExtractDerivesFromReferences:
    """Tests for extracting 'Derives from' references."""

    def test_extracts_references_with_colon(self):
        content = "- Derives from **Context Engineering:** Some description"
        refs = extract_derives_from_references(content, "test.md")
        assert len(refs) == 1
        assert refs[0]["reference"] == "Context Engineering"
        assert refs[0]["file"] == "test.md"

    def test_extracts_multiple_references(self):
        content = """
- Derives from **Context Engineering:** Description 1
- Derives from **Single Source of Truth:** Description 2
"""
        refs = extract_derives_from_references(content, "test.md")
        assert len(refs) == 2

    def test_captures_line_numbers(self):
        content = "line 1\n- Derives from **Test:** desc\nline 3"
        refs = extract_derives_from_references(content, "test.md")
        assert refs[0]["line_number"] == 2


class TestIsTemplatePlaceholder:
    """Tests for template placeholder detection."""

    def test_detects_placeholder(self):
        assert is_template_placeholder("[Meta-Principle Full Name]")
        assert is_template_placeholder("[Something]")

    def test_rejects_non_placeholder(self):
        assert not is_template_placeholder("Context Engineering")
        assert not is_template_placeholder("[partial")
        assert not is_template_placeholder("partial]")


class TestNormalizePrincipleName:
    """Tests for principle name normalization."""

    def test_removes_meta_principle_prefix(self):
        assert (
            normalize_principle_name("Meta-Principle Context Engineering")
            == "context engineering"
        )

    def test_lowercases(self):
        assert normalize_principle_name("Context Engineering") == "context engineering"

    def test_normalizes_whitespace(self):
        assert (
            normalize_principle_name("Context   Engineering") == "context engineering"
        )


class TestFuzzyMatching:
    """Tests for fuzzy matching of principle references."""

    def test_exact_match(self):
        index = build_principle_index({"Context Engineering"})
        match = find_fuzzy_match("context engineering", index)
        assert match == "Context Engineering"

    def test_prefix_match(self):
        index = build_principle_index({"Verification Mechanisms Before Action"})
        match = find_fuzzy_match("verification mechanisms", index)
        assert match == "Verification Mechanisms Before Action"

    def test_abbreviation_map_match(self):
        index = build_principle_index({"Atomic Task Decomposition"})
        match = find_fuzzy_match("atomic decomposition", index)
        assert match == "Atomic Task Decomposition"

    def test_no_match_returns_none(self):
        index = build_principle_index({"Context Engineering"})
        match = find_fuzzy_match("completely different", index)
        assert match is None


class TestBuildPrincipleIndex:
    """Tests for principle index building."""

    def test_builds_normalized_index(self):
        principles = {"Context Engineering", "Single Source of Truth"}
        index = build_principle_index(principles)
        assert "context engineering" in index
        assert index["context engineering"] == "Context Engineering"


# ---------------------------------------------------------------------------
# Failure-mode registry lint (TestFailureModeCoverage)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "documents" / "failure-mode-registry.md"
TESTS_DIR = PROJECT_ROOT / "tests"
_COVERS_RE = re.compile(r"Covers:\s*([A-Z][A-Z0-9_\-, ]+)", re.MULTILINE)


def _load_registry_entries() -> dict[str, dict]:
    """Parse YAML frontmatter from the failure-mode registry; return {id: entry}."""
    text = REGISTRY_PATH.read_text()
    assert text.startswith("---\n"), "registry missing YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end != -1, "registry YAML frontmatter unterminated"
    meta = yaml.safe_load(text[4:end]) or {}
    entries = meta.get("entries") or []
    return {e["id"]: e for e in entries if e.get("id")}


def _parse_covers(docstring: str | None) -> list[str]:
    """Extract FM-* IDs from a docstring's Covers: line(s)."""
    if not docstring:
        return []
    ids: list[str] = []
    for match in _COVERS_RE.finditer(docstring):
        for raw in match.group(1).split(","):
            ident = raw.strip().rstrip(".\"' \t")
            if ident and ident.startswith("FM-"):
                ids.append(ident)
    return ids


def _collect_annotations() -> list[tuple[str, str, list[str]]]:
    """Return list of (relative_file, test_qualname, [covered_ids])."""
    annotations: list[tuple[str, str, list[str]]] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for klass in ast.walk(tree):
            if isinstance(klass, ast.ClassDef):
                for method in klass.body:
                    if isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) and method.name.startswith("test_"):
                        ids = _parse_covers(ast.get_docstring(method))
                        if ids:
                            annotations.append(
                                (rel, f"{klass.name}::{method.name}", ids)
                            )
        # Module-level test functions (rare in this codebase).
        for fn in tree.body:
            if isinstance(
                fn, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and fn.name.startswith("test_"):
                ids = _parse_covers(ast.get_docstring(fn))
                if ids:
                    annotations.append((rel, fn.name, ids))
    return annotations


class TestFailureModeCoverage:
    """Failure-mode registry lint — ensures `Covers:` annotations stay honest.

    Prevents the class of bug where `Covers:` annotations turn into theatre:
    typos coin new "IDs" that lint-pattern-match but aren't in the registry,
    refactors rename IDs without updating annotations, must_cover entries drift
    into zero-coverage state without anyone noticing.

    Three checks:
    1. Every `Covers:` ID across tests/ must exist in the registry (unknown = fail).
    2. Every registry entry with must_cover: true must have ≥1 annotation (fail).
    3. Annotations citing retired entries emit a warning (not a failure — gives
       migration window).
    """

    @pytest.fixture(scope="class")
    def registry(self) -> dict[str, dict]:
        return _load_registry_entries()

    @pytest.fixture(scope="class")
    def annotations(self) -> list[tuple[str, str, list[str]]]:
        return _collect_annotations()

    def test_every_covers_id_exists_in_registry(self, registry, annotations):
        """Covers: IDs must resolve to a registry entry — no typos, no ghosts.

        Covers: FM-REGISTRY-UNKNOWN-ID-REJECTED
        """
        unknown: list[str] = []
        for rel, qualname, ids in annotations:
            for eid in ids:
                if eid not in registry:
                    unknown.append(f"{rel}::{qualname} cites unknown id {eid}")
        assert not unknown, (
            "tests cite failure-mode IDs that are not in "
            "documents/failure-mode-registry.md:\n  " + "\n  ".join(unknown)
        )

    def test_every_must_cover_entry_has_annotation(self, registry, annotations):
        """Every must_cover: true registry entry must have ≥1 annotated test.

        Covers: FM-REGISTRY-MUST-COVER-HAS-ANNOTATION
        """
        annotated_ids: set[str] = set()
        for _, _, ids in annotations:
            annotated_ids.update(ids)
        missing: list[str] = []
        for eid, entry in registry.items():
            if entry.get("must_cover") and not entry.get("retired"):
                if eid not in annotated_ids:
                    missing.append(f"{eid} — {entry.get('description', '')}")
        assert not missing, (
            "registry entries with must_cover: true have no annotated tests. "
            "Either add a test annotated with `Covers: <id>` in its docstring, "
            "or flip the entry to must_cover: false if coverage isn't required:\n  "
            + "\n  ".join(missing)
        )

    def test_retired_ids_emit_warning_only(self, registry, annotations, recwarn):
        """Annotations citing retired IDs produce deprecation warnings, not failures."""
        retired = {eid for eid, e in registry.items() if e.get("retired")}
        if not retired:
            pytest.skip("no retired registry entries yet — nothing to test")
        for rel, qualname, ids in annotations:
            for eid in ids:
                if eid in retired:
                    import warnings

                    warnings.warn(
                        f"{rel}::{qualname} cites retired id {eid} "
                        f"(retired {registry[eid].get('retired')})",
                        DeprecationWarning,
                        stacklevel=1,
                    )
        # Soft check — collect warnings but don't fail. Captures awareness surface.
        # If a future pass wants to enforce migration, add: assert not recwarn.list

    def test_registry_yaml_parses(self, registry):
        """Registry YAML frontmatter must be valid and contain entries."""
        assert registry, "registry has zero entries — check YAML frontmatter"
        for eid, entry in registry.items():
            assert entry.get("description"), f"{eid} missing description"
            assert "must_cover" in entry, f"{eid} missing must_cover field"
            # Must be a real bool — YAML `"true"` (string) is truthy but silently
            # wrong; explicit isinstance catches schema drift. (Per contrarian
            # MEDIUM-5, session-123.)
            assert isinstance(entry["must_cover"], bool), (
                f"{eid} must_cover must be bool, got {type(entry['must_cover']).__name__}"
            )
            assert entry.get("introduced"), f"{eid} missing introduced date"
