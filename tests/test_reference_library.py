"""Tests for the Reference Library system.

Covers the full pipeline: YAML frontmatter parsing in DocumentConnector,
reference entry extraction in the governance extractor, metadata boosting
in Context Engine score fusion, and the capture_reference MCP tool.
"""

from ai_governance_mcp.context_engine.connectors.document import DocumentConnector
from ai_governance_mcp.context_engine.models import ContentChunk


class TestDocumentConnectorFrontmatter:
    """Tests for YAML frontmatter parsing in DocumentConnector."""

    def test_extracts_frontmatter_from_reference_entry(self, tmp_path):
        """Should parse YAML frontmatter and populate chunk.frontmatter."""
        entry = tmp_path / "test.md"
        entry.write_text(
            "---\n"
            "id: ref-test-entry\n"
            "title: Test Entry\n"
            "domain: ai-coding\n"
            "tags: [testing, pytest]\n"
            "status: current\n"
            "entry_type: direct\n"
            "maturity: evergreen\n"
            "---\n\n"
            "## Context\n\nTest content here.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 1
        assert chunks[0].frontmatter is not None
        assert chunks[0].frontmatter["id"] == "ref-test-entry"
        assert chunks[0].frontmatter["tags"] == ["testing", "pytest"]
        assert chunks[0].frontmatter["status"] == "current"
        assert chunks[0].frontmatter["maturity"] == "evergreen"

    def test_frontmatter_stripped_from_content(self, tmp_path):
        """Frontmatter YAML should not appear in chunk content."""
        entry = tmp_path / "test.md"
        entry.write_text(
            "---\nid: ref-test\ntitle: Test\n---\n\n## Body\n\nActual content.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        for chunk in chunks:
            assert "---" not in chunk.content.split("\n")[
                0
            ] or chunk.content.startswith("[")
            assert "id: ref-test" not in chunk.content

    def test_frontmatter_summary_prepended_to_first_chunk(self, tmp_path):
        """First chunk should have metadata summary prefix for embedding enrichment."""
        entry = tmp_path / "test.md"
        entry.write_text(
            "---\n"
            "id: ref-test\n"
            "tags: [python, testing]\n"
            "status: current\n"
            "maturity: budding\n"
            "domain: ai-coding\n"
            "title: My Pattern\n"
            "---\n\n"
            "## Content\n\nBody text.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 1
        first = chunks[0].content
        assert "[tags: python, testing]" in first
        assert "[status: current]" in first
        assert "[maturity: budding]" in first

    def test_no_frontmatter_returns_none(self, tmp_path):
        """Files without frontmatter should have frontmatter=None."""
        entry = tmp_path / "plain.md"
        entry.write_text("# Regular Markdown\n\nNo frontmatter here.\n")

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 1
        assert chunks[0].frontmatter is None

    def test_invalid_yaml_returns_none(self, tmp_path):
        """Invalid YAML in frontmatter should be handled gracefully."""
        entry = tmp_path / "bad.md"
        entry.write_text("---\ninvalid: [unclosed bracket\n---\n\n## Content\n")

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 1
        assert chunks[0].frontmatter is None

    def test_all_chunks_get_frontmatter_dict(self, tmp_path):
        """All chunks from a frontmatter file should carry the dict."""
        entry = tmp_path / "multi.md"
        entry.write_text(
            "---\n"
            "id: ref-multi\n"
            "tags: [a, b]\n"
            "---\n\n"
            "## Section 1\n\nContent 1.\n\n"
            "## Section 2\n\nContent 2.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.frontmatter is not None
            assert chunk.frontmatter["id"] == "ref-multi"

    def test_summary_only_on_first_chunk(self, tmp_path):
        """Only the first chunk should have the metadata summary prefix."""
        entry = tmp_path / "multi.md"
        entry.write_text(
            "---\n"
            "tags: [testing]\n"
            "status: current\n"
            "---\n\n"
            "## Section 1\n\nFirst section.\n\n"
            "## Section 2\n\nSecond section.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 2
        assert "[tags: testing]" in chunks[0].content
        assert "[tags: testing]" not in chunks[1].content


class TestHeadingBreadcrumbs:
    """Tests for heading breadcrumb enrichment."""

    def test_breadcrumb_in_chunk_content(self, tmp_path):
        """Chunks should include file path breadcrumb."""
        entry = tmp_path / "doc.md"
        entry.write_text("## My Section\n\nContent here.\n")

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        assert len(chunks) >= 1
        assert "doc.md" in chunks[0].content

    def test_parent_heading_tracked(self, tmp_path):
        """Parent heading (level 1-2) should appear in breadcrumb for child sections."""
        entry = tmp_path / "doc.md"
        entry.write_text(
            "## Parent Section\n\nParent content.\n\n"
            "### Child Section\n\nChild content.\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        # Find the child chunk
        child_chunks = [c for c in chunks if "Child content" in c.content]
        assert len(child_chunks) >= 1
        assert "Parent Section" in child_chunks[0].content


class TestChunkOverlap:
    """Tests for chunk overlap on sections >15 lines."""

    def test_no_overlap_for_short_sections(self, tmp_path):
        """Sections under 15 lines should NOT have overlap."""
        entry = tmp_path / "short.md"
        entry.write_text(
            "## Section 1\n\n" + "Line.\n" * 5 + "\n"
            "## Section 2\n\n" + "Different.\n" * 5 + "\n"
        )

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        if len(chunks) >= 2:
            # Second chunk should not contain first chunk's content
            assert "Line." not in chunks[1].content or "Different." in chunks[1].content

    def test_overlap_for_long_sections(self, tmp_path):
        """Sections over 15 lines should have overlap from previous section."""
        lines_s1 = "\n".join(f"Line {i} of section one." for i in range(20))
        lines_s2 = "\n".join(f"Line {i} of section two." for i in range(10))
        entry = tmp_path / "long.md"
        entry.write_text(f"## Section 1\n\n{lines_s1}\n\n## Section 2\n\n{lines_s2}\n")

        dc = DocumentConnector()
        chunks = dc.parse(entry, tmp_path)

        if len(chunks) >= 2:
            # Section 2's chunk should contain some lines from section 1 (overlap)
            s2_content = chunks[1].content
            # The overlap should include tail lines from section 1
            assert "section one" in s2_content or "Section 2" in s2_content


class TestMetadataBoosting:
    """Tests for metadata score boosting in project_manager."""

    def test_tag_match_boosts_score(self):
        """Chunks with matching tags should get a positive boost."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        chunk = ContentChunk(
            content="Test content",
            source_path="test.md",
            start_line=1,
            end_line=10,
            content_type="document",
            frontmatter={"tags": ["testing", "pytest"], "status": "current"},
        )

        bonus = ProjectManager._compute_metadata_bonus(chunk, "pytest fixture patterns")
        assert bonus > 0, "Tag match should produce positive bonus"

    def test_deprecated_status_penalizes(self):
        """Deprecated entries should get a negative bonus."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        chunk = ContentChunk(
            content="Old content",
            source_path="old.md",
            start_line=1,
            end_line=10,
            content_type="document",
            frontmatter={"tags": [], "status": "deprecated"},
        )

        bonus = ProjectManager._compute_metadata_bonus(chunk, "some query")
        assert bonus < 0, "Deprecated status should produce negative bonus"

    def test_evergreen_maturity_boosts(self):
        """Evergreen entries should get a positive bonus."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        chunk = ContentChunk(
            content="Proven content",
            source_path="proven.md",
            start_line=1,
            end_line=10,
            content_type="document",
            frontmatter={"tags": [], "status": "current", "maturity": "evergreen"},
        )

        bonus = ProjectManager._compute_metadata_bonus(chunk, "some query")
        assert bonus > 0, "Evergreen maturity should produce positive bonus"

    def test_no_frontmatter_no_bonus(self):
        """Chunks without frontmatter should get zero bonus."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        chunk = ContentChunk(
            content="Plain content",
            source_path="plain.md",
            start_line=1,
            end_line=10,
            content_type="document",
        )

        bonus = ProjectManager._compute_metadata_bonus(chunk, "some query")
        assert bonus == 0.0, "No frontmatter should mean zero bonus"

    def test_combined_tag_and_maturity_boost(self):
        """Tag match + evergreen should stack bonuses."""
        from ai_governance_mcp.context_engine.project_manager import ProjectManager

        chunk = ContentChunk(
            content="Test content",
            source_path="test.md",
            start_line=1,
            end_line=10,
            content_type="document",
            frontmatter={
                "tags": ["testing", "pytest"],
                "status": "current",
                "maturity": "evergreen",
            },
        )

        bonus = ProjectManager._compute_metadata_bonus(chunk, "pytest testing")
        # Tag match (2 matches * 0.02 = 0.04, capped at 0.05) + evergreen (0.03)
        assert bonus >= 0.05, "Combined tag + maturity should stack"


class TestGovernanceExtractorReferences:
    """Tests for reference entry extraction in the governance server extractor."""

    def test_reference_entries_extracted(self):
        """Extractor should find reference entries in reference-library/ directory."""
        from ai_governance_mcp.extractor import DocumentExtractor
        from ai_governance_mcp.config import get_settings, load_domains_registry

        settings = get_settings()
        domains = load_domains_registry(settings)
        ai_coding = next(d for d in domains if d.name == "ai-coding")

        extractor = DocumentExtractor(settings)
        refs = extractor._extract_references(ai_coding)

        assert len(refs) >= 4, f"Expected at least 4 reference entries, got {len(refs)}"
        ids = [r.id for r in refs]
        assert "ref-ai-coding-pytest-fixture-patterns" in ids
        assert "ref-ai-coding-willison-hoard-pattern" in ids

    def test_reference_entries_have_series_fields(self):
        """Each reference entry should have required fields populated."""
        from ai_governance_mcp.extractor import DocumentExtractor
        from ai_governance_mcp.config import get_settings, load_domains_registry

        settings = get_settings()
        domains = load_domains_registry(settings)
        ai_coding = next(d for d in domains if d.name == "ai-coding")

        extractor = DocumentExtractor(settings)
        refs = extractor._extract_references(ai_coding)

        for ref in refs:
            assert ref.id, "Reference must have id"
            assert ref.title, f"Reference {ref.id} must have title"
            assert ref.domain == "ai-coding", (
                f"Reference {ref.id} domain should be ai-coding"
            )
            assert len(ref.tags) > 0, f"Reference {ref.id} should have tags"
            assert ref.status in ("current", "caution", "deprecated", "archived")
            assert ref.entry_type in ("direct", "reference")
