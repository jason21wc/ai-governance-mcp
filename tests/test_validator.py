"""Tests for cross-reference validator."""

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
