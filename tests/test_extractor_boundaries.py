"""Structural-boundary tests for principle/method extraction.

WHY THIS FILE EXISTS: units used to run until the next heading their OWN pattern
recognised — or to EOF. Everything in between belonged to them. `## Historical
Amendments` in constitution.md therefore lived inside
`meta-safety-transparent-limitations`, giving it a 74,441-char body for ~41 lines
of real text; `coding-method-incident-review-checklist` reached 160,230 chars.

That is not cosmetic. `_generate_metadata` mines trigger_phrases /
failure_indicators from the body and `retrieval.py` appends those to the BM25 text
UNCAPPED, so a document's changelog was contributing search tokens to a safety
principle. `get_principle` on the 160K method also exceeded the MCP per-tool-result
cap outright.

The existing suite stayed green because `tests/test_extractor.py` asserts unit
COUNTS, never that a body excludes the section after it. These tests assert the
boundary itself.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _principles(test_settings, text: str):
    """Extract principles from `text` written into the temp corpus."""
    from ai_governance_mcp.extractor import DocumentExtractor
    from ai_governance_mcp.models import DomainConfig

    test_settings.documents_path.mkdir(parents=True, exist_ok=True)
    (test_settings.documents_path / "b-principles.md").write_text(text)
    with patch("sentence_transformers.SentenceTransformer"):
        extractor = DocumentExtractor(test_settings)
        return extractor._extract_principles(
            DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="b-principles.md",
                description="boundary fixture",
                priority=0,
            )
        )


def _methods(test_settings, text: str):
    """Extract methods from `text` written into the temp corpus."""
    from ai_governance_mcp.extractor import DocumentExtractor
    from ai_governance_mcp.models import DomainConfig

    test_settings.documents_path.mkdir(parents=True, exist_ok=True)
    (test_settings.documents_path / "b-principles.md").write_text("# Empty\n")
    (test_settings.documents_path / "b-methods.md").write_text(text)
    with patch("sentence_transformers.SentenceTransformer"):
        extractor = DocumentExtractor(test_settings)
        return extractor._extract_methods(
            DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="b-principles.md",
                methods_file="b-methods.md",
                description="boundary fixture",
                priority=0,
            )
        )


PRINCIPLE_BODY = """**Definition**
The AI must state uncertainty rather than guess.

**How the AI Applies This Principle**
- Say so when unsure
"""


class TestPrincipleBoundaries:
    def test_last_principle_does_not_absorb_trailing_changelog(self, test_settings):
        """The constitution.md defect, reproduced at fixture scale.

        Amendment III was the final principle heading, so it swallowed the whole
        `## Historical Amendments` section to EOF.
        """
        doc = f"""# Doc

## Bill of Rights

### Transparent Limitations
{PRINCIPLE_BODY}
## Historical Amendments (Constitutional History)

#### **v8.3.0 (August 2026)**
*   Added a thing.

#### **v1.1 (November 2025)**
*   Added another thing.
"""
        ps = _principles(test_settings, doc)
        assert len(ps) == 1
        body = ps[0].content
        assert "Historical Amendments" not in body
        assert "v8.3.0" not in body
        assert "state uncertainty" in body
        # end_line is the line BEFORE the boundary heading
        boundary = (
            doc.split("\n").index("## Historical Amendments (Constitutional History)")
            + 1
        )
        assert ps[0].line_range[1] == boundary - 1

    def test_last_principle_closes_at_eof_when_nothing_follows(self, test_settings):
        """The EOF save is still the terminal case, not dead code."""
        doc = f"""# Doc

## Bill of Rights

### Transparent Limitations
{PRINCIPLE_BODY}"""
        ps = _principles(test_settings, doc)
        assert len(ps) == 1
        assert "state uncertainty" in ps[0].content

    def test_boundary_ignores_headings_inside_code_fences(self, test_settings):
        """A fenced template must not truncate the principle that contains it.

        Real hazard: rules-of-procedure.md ships `### [Section Number]: [Method
        Name]` and `# TITLE 16 END` inside fences.
        """
        doc = f"""# Doc

## Bill of Rights

### Transparent Limitations
{PRINCIPLE_BODY}
Example template:

```markdown
# TITLE 16 END
## Historical Amendments
### [Section Number]: [Method Name]
```

Tail sentence that must survive.
"""
        ps = _principles(test_settings, doc)
        assert len(ps) == 1
        assert "Tail sentence that must survive." in ps[0].content

    def test_deeper_subheading_does_not_close_principle(self, test_settings):
        """`#### How the AI Applies...` is the corpus convention — must be kept."""
        doc = f"""# Doc

## Bill of Rights

### Transparent Limitations
{PRINCIPLE_BODY}
#### Common Pitfalls
The pitfall text.
"""
        ps = _principles(test_settings, doc)
        assert len(ps) == 1
        assert "The pitfall text." in ps[0].content

    def test_unclosed_fence_loses_every_later_unit_and_warns(
        self, test_settings, caplog
    ):
        """An unclosed fence does NOT degrade to pre-fix behavior — it is worse.

        `if in_fence: continue` skips the whole loop body, so header detection
        stops too: no further unit is opened and the last open unit absorbs the
        rest of the file. Pre-fix behavior was over-absorption with every unit
        still PRESENT; this is silent unit loss.

        This test pins the real consequence, not just the log line — an earlier
        version asserted only the warning and its docstring claimed the failure
        was benign, which is how the wrong belief survived review.

        The corpus-level guard is the fence-parity check in test_repo_hygiene.py;
        this documents what happens if that guard is ever removed.
        """
        doc = f"""# Doc

## Bill of Rights

### Transparent Limitations
{PRINCIPLE_BODY}
```markdown
never closed

### Verification And Validation
{PRINCIPLE_BODY}"""
        with caplog.at_level("WARNING"):
            ps = _principles(test_settings, doc)

        titles = [p.title for p in ps]
        assert "Verification And Validation" not in titles, (
            "expected the post-fence principle to be LOST — if this now passes, "
            "the degradation policy changed and the warning text must change too"
        )
        assert len(ps) == 1
        assert any("unclosed code fence" in r.message for r in caplog.records)


class TestMethodBoundaries:
    def test_last_method_does_not_absorb_appendix(self, test_settings):
        doc = """# Methods

## 1 Cold Start Kit
Procedure for initializing new projects.

## Appendix A: Optional Ecosystem Tools
A long appendix that is not part of the method.
"""
        ms = _methods(test_settings, doc)
        assert len(ms) == 1
        assert "Appendix A" not in ms[0].content
        assert "initializing new projects" in ms[0].content

    def test_part_prefixed_heading_becomes_its_own_method(self, test_settings):
        """`## Part 7.8: Progressive Application` was never a unit before.

        Without this, closing units at boundaries would make every `Part N.M`
        section reachable through no tool at all — including sections README.md
        and CLAUDE.md cite as retrievable.
        """
        doc = """# Methods

## Part 7.7: Anchor Bias Prevention
First part body.

## Part 7.8: Progressive Application (Proportional Response)
Second part body.
"""
        ms = _methods(test_settings, doc)
        titles = [m.title for m in ms]
        assert "Progressive Application (Proportional Response)" in titles
        assert len(ms) == 2
        prog = next(m for m in ms if m.title.startswith("Progressive"))
        assert "Second part body." in prog.content
        assert "First part body." not in prog.content

    def test_fenced_headings_are_not_methods(self, test_settings):
        """Template headings inside fences produced phantom units.

        Ten shipped in the real index this way (`stor-method-characters`,
        `kmpd-method-branch-scenario`, ...), all from ```markdown templates.
        """
        doc = """# Methods

## 1 Cold Start Kit
Procedure text.

Full template:

```markdown
# Story Bible: [Project Name]

## 1 Story Foundation (IMMUTABLE)
[Premise]

## 2 Characters
[Who]
```

Closing prose.
"""
        ms = _methods(test_settings, doc)
        assert len(ms) == 1
        titles = [m.title for m in ms]
        assert "Story Foundation (IMMUTABLE)" not in titles
        assert "Characters" not in titles

    def test_skipped_title_closes_previous_method(self, test_settings):
        """A skipped structure section used to glue its body onto the prior method."""
        doc = """# Methods

## 1 Cold Start Kit
Procedure text.

## 2 Glossary
Terms that belong to nobody.
"""
        ms = _methods(test_settings, doc)
        assert len(ms) == 1
        assert "Terms that belong to nobody." not in ms[0].content


class TestHeadingLevelHelper:
    @pytest.mark.parametrize(
        "line,expected",
        [
            ("# One", 1),
            ("### Three", 3),
            ("###### Six", 6),
            ("#hashtag", None),  # no space — not a heading
            ("#!/usr/bin/env bash", None),
            ("not a heading", None),
            ("", None),
        ],
    )
    def test_heading_level(self, line, expected):
        from ai_governance_mcp.extractor import _heading_level

        assert _heading_level(line) == expected
