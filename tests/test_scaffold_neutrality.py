"""Use-case neutrality guards for scaffold templates.

The document-path templates (`*_DOC` variants + the _ai-context README) must stay
use-case-neutral: memory files are the highest-priority context an AI loads at
session start, and section headings act as instructions — a "Tech Stack" heading
steers a hotel-operations folder toward a software-delivery frame (the observed
harm this suite pins, session-243).

This is a snapshot-style regression guard on repo-owned string constants, NOT a
banlist on generated prose (the class rejected in session-237). Markers are
format-anchored to the exact removed artifacts (headings, bold field markers,
filenames) so ordinary lowercase prose ("plan", "specify") stays legal.

The code-path templates deliberately KEEP their coding frame (Phase Gates /
Tech Stack) — the CFR pre-seeds and updates that table at defined transitions
(title-10 §1.4/§7.8.4). The reverse guard below pins that too, so neither
direction regresses silently. Contrarian finding C1, session-243.
"""

import pytest

from ai_governance_mcp.server import _constants

# Document-path templates that must carry no coding priming.
_DOC_TEMPLATE_ATTRS = [
    "SCAFFOLD_SESSION_STATE_DOC",
    "SCAFFOLD_PROJECT_MEMORY_DOC",
    "SCAFFOLD_LEARNING_LOG_DOC",
    "SCAFFOLD_AI_CONTEXT_README",
]

# Format-anchored markers of the coding frame (multi-word / heading / filename
# forms only — never bare English words, which would rot into false positives).
_CODING_MARKERS = [
    "## Phase Gates",
    "## Tech Stack",
    "## Spec Summary",
    "Tech Stack",
    "pytest",
    "**Phase:**",
    "ARCHITECTURE.md",
    "SPECIFICATION.md",
    "| Specify",
]

# Every scaffold template constant — rendered via str.format at scaffold time
# (handlers/scaffold.py), so a literal brace in any of them crashes the tool.
_ALL_TEMPLATE_ATTRS = [
    "SCAFFOLD_SESSION_STATE",
    "SCAFFOLD_PROJECT_MEMORY",
    "SCAFFOLD_LEARNING_LOG",
    "SCAFFOLD_AGENTS_MD",
    "SCAFFOLD_CLAUDE_MD",
    "SCAFFOLD_GEMINI_MD",
    "SCAFFOLD_COMPLETION_CHECKLIST",
    "SCAFFOLD_AI_CONTEXT_README",
    "SCAFFOLD_ARCHITECTURE",
    "SCAFFOLD_SPECIFICATION",
    "SCAFFOLD_BACKLOG",
    "SCAFFOLD_OPERATIONS",
    "SCAFFOLD_SAAS_OPS_SOP",
    "SCAFFOLD_SESSION_STATE_DOC",
    "SCAFFOLD_PROJECT_MEMORY_DOC",
    "SCAFFOLD_LEARNING_LOG_DOC",
]


def _template(attr: str) -> str:
    template = getattr(_constants, attr, None)
    if template is None:
        pytest.fail(f"{attr} is not defined in server._constants")
    return template


class TestDocumentTemplateNeutrality:
    """The document path must not prime any specific use case."""

    @pytest.mark.parametrize("attr", _DOC_TEMPLATE_ATTRS)
    @pytest.mark.parametrize("marker", _CODING_MARKERS)
    def test_document_templates_contain_no_coding_vocabulary(self, attr, marker):
        assert marker not in _template(attr), (
            f"{attr} contains coding-priming marker {marker!r} — document "
            "templates must stay use-case-neutral (session-243 design)"
        )

    def test_document_project_memory_neutral_sections(self):
        template = _template("SCAFFOLD_PROJECT_MEMORY_DOC")
        for heading in (
            "## Purpose",
            "## Key Decisions",
            "## Constraints",
            "## Gotchas",
        ):
            assert heading in template

    @pytest.mark.parametrize(
        "attr",
        ["SCAFFOLD_SESSION_STATE_DOC", "SCAFFOLD_PROJECT_MEMORY_DOC"],
    )
    def test_document_templates_keep_interpolation_anchors(self, attr):
        template = _template(attr)
        # SESSION-STATE carries both anchors; PROJECT-MEMORY at least the date.
        assert "{date}" in template
        if attr == "SCAFFOLD_SESSION_STATE_DOC":
            assert "{project_name}" in template

    def test_learning_log_doc_routing_is_neutral(self):
        template = _template("SCAFFOLD_LEARNING_LOG_DOC")
        assert "ARCHITECTURE.md" not in template
        assert "PROJECT-MEMORY" in template

    def test_ai_context_readme_nearest_wins_and_tailoring(self):
        readme = _template("SCAFFOLD_AI_CONTEXT_README")
        # Subfolder convention: binds the READING agent; automated loaders
        # detect the top-level folder only (contrarian C4).
        assert "nearest" in readme.lower()
        assert "_ai-context" in readme
        # Conversational tailoring replaces baked verticals.
        assert "use case" in readme.lower()


class TestCodeTemplatesKeepCodingFrame:
    """Reverse guard: the code path IS the coding overlay (contrarian C1)."""

    def test_code_templates_keep_phase_gates(self):
        assert "## Phase Gates" in _constants.SCAFFOLD_PROJECT_MEMORY
        assert "## Tech Stack" in _constants.SCAFFOLD_PROJECT_MEMORY
        assert "**Phase:**" in _constants.SCAFFOLD_SESSION_STATE

    def test_agents_md_commands_are_bracketed_placeholder(self):
        # A pytest example primes Python even for code projects; K.2's template
        # already uses a bracketed placeholder — the trio converges.
        assert "pytest" not in _constants.SCAFFOLD_AGENTS_MD
        assert "## Key Commands" in _constants.SCAFFOLD_AGENTS_MD
        commands_section = _constants.SCAFFOLD_AGENTS_MD.split("## Key Commands")[1]
        assert "[" in commands_section.split("##")[0]


class TestTemplateFormatSafety:
    """Templates render via str.format — literal braces crash scaffold_project."""

    @pytest.mark.parametrize("attr", _ALL_TEMPLATE_ATTRS)
    def test_templates_format_cleanly(self, attr):
        _template(attr).format(project_name="x", date="2026-01-01")


class TestDocumentKitWiring:
    """Document core points at the _DOC variants; code core untouched."""

    def test_document_core_uses_doc_variants(self):
        doc_core = dict(_constants.SCAFFOLD_CORE_FILES["document"])
        assert (
            doc_core["_ai-context/SESSION-STATE.md"]
            == _constants.SCAFFOLD_SESSION_STATE_DOC
        )
        assert (
            doc_core["_ai-context/PROJECT-MEMORY.md"]
            == _constants.SCAFFOLD_PROJECT_MEMORY_DOC
        )
        assert (
            doc_core["_ai-context/LEARNING-LOG.md"]
            == _constants.SCAFFOLD_LEARNING_LOG_DOC
        )

    def test_code_core_uses_coding_templates(self):
        # Unified layout (v2.62.0): code memory files also live in _ai-context/,
        # but keep the CODING templates (phase-framed) — layout and template
        # flavor are independent axes.
        code_core = dict(_constants.SCAFFOLD_CORE_FILES["code"])
        assert (
            code_core["_ai-context/SESSION-STATE.md"]
            == _constants.SCAFFOLD_SESSION_STATE
        )
        assert (
            code_core["_ai-context/PROJECT-MEMORY.md"]
            == _constants.SCAFFOLD_PROJECT_MEMORY
        )
        assert (
            code_core["_ai-context/LEARNING-LOG.md"] == _constants.SCAFFOLD_LEARNING_LOG
        )
        assert code_core["AGENTS.md"] == _constants.SCAFFOLD_AGENTS_MD
