"""Unit tests for F-C-04 Phase-1 domain-fit helpers.

Closes post-edit contrarian finding HIGH #3 (zero unit tests for
`_parse_applicable_domains` and `_check_domain_fit`).

Covers the edge cases the Phase-1 parser claims to handle:
- Missing frontmatter entirely
- Missing `applicable_domains` field
- Inline flow form `["*"]`, `["ai-coding", "ui-ux"]`
- Block-form YAML list (hyphen-prefixed)
- Scalar string form
- Empty list `[]`
- Trailing comment
- Malformed YAML
- `_check_domain_fit` semantics (wildcard match, exact match, no project domain)
"""

from __future__ import annotations

import pytest

from ai_governance_mcp.server import (
    _check_domain_fit,
    _parse_applicable_domains,
)


class TestParseApplicableDomains:
    """Verify the parser handles the documented edge cases."""

    def test_no_frontmatter_defaults_to_wildcard(self) -> None:
        assert _parse_applicable_domains("# Not an agent file") == ["*"]

    def test_frontmatter_without_field_defaults_to_wildcard(self) -> None:
        content = "---\nname: foo\ndescription: bar\n---\n\nbody"
        assert _parse_applicable_domains(content) == ["*"]

    def test_inline_flow_single(self) -> None:
        content = '---\nname: foo\napplicable_domains: ["ai-coding"]\n---'
        assert _parse_applicable_domains(content) == ["ai-coding"]

    def test_inline_flow_multiple(self) -> None:
        content = '---\nname: foo\napplicable_domains: ["ai-coding", "ui-ux"]\n---'
        assert _parse_applicable_domains(content) == ["ai-coding", "ui-ux"]

    def test_inline_flow_wildcard(self) -> None:
        content = '---\nname: foo\napplicable_domains: ["*"]\n---'
        assert _parse_applicable_domains(content) == ["*"]

    def test_block_form_yaml_list(self) -> None:
        """Block-form YAML list must parse (was a CRITICAL gap in regex-only parser)."""
        content = "---\nname: foo\napplicable_domains:\n  - ai-coding\n  - ui-ux\n---"
        assert _parse_applicable_domains(content) == ["ai-coding", "ui-ux"]

    def test_scalar_string_form_wraps_as_list(self) -> None:
        """Ergonomic tolerance: scalar string becomes one-element list."""
        content = "---\nname: foo\napplicable_domains: ai-coding\n---"
        assert _parse_applicable_domains(content) == ["ai-coding"]

    def test_empty_list_defaults_to_wildcard(self) -> None:
        content = "---\nname: foo\napplicable_domains: []\n---"
        assert _parse_applicable_domains(content) == ["*"]

    def test_trailing_comment_stripped_by_yaml(self) -> None:
        """YAML parser strips line comments; regex parser would have failed here."""
        content = '---\nname: foo\napplicable_domains: ["*"] # domain-agnostic\n---'
        assert _parse_applicable_domains(content) == ["*"]

    def test_malformed_yaml_fails_open_to_wildcard(self) -> None:
        """WARN+allow semantics: parse failure → fail open (wildcard)."""
        content = "---\nname: foo\napplicable_domains: [unclosed\n---"
        assert _parse_applicable_domains(content) == ["*"]

    def test_null_value_defaults_to_wildcard(self) -> None:
        content = "---\nname: foo\napplicable_domains:\n---"
        assert _parse_applicable_domains(content) == ["*"]

    def test_non_string_list_entries_filtered(self) -> None:
        content = (
            "---\nname: foo\napplicable_domains: [ai-coding, 42, null, ui-ux]\n---"
        )
        assert _parse_applicable_domains(content) == ["ai-coding", "ui-ux"]


class TestCheckDomainFit:
    """Verify WARN+allow semantics."""

    def test_no_project_domain_always_fits(self) -> None:
        fits, warning = _check_domain_fit(["ai-coding"], None)
        assert fits is True
        assert warning is None

    def test_wildcard_agent_always_fits(self) -> None:
        fits, warning = _check_domain_fit(["*"], "storytelling")
        assert fits is True
        assert warning is None

    def test_exact_match_fits(self) -> None:
        fits, warning = _check_domain_fit(["ai-coding", "ui-ux"], "ai-coding")
        assert fits is True
        assert warning is None

    def test_mismatch_returns_warning_but_still_fits_semantically(self) -> None:
        """Phase-1 WARN+allow: caller ALWAYS proceeds; warning is surfaced only."""
        fits, warning = _check_domain_fit(["storytelling"], "ai-coding")
        assert fits is False
        assert warning is not None
        assert "storytelling" in warning
        assert "ai-coding" in warning
        assert "Phase-1" in warning or "WARN" in warning

    def test_empty_agent_domains_fits(self) -> None:
        """Empty list should not trigger WARN (caller treats as unknown)."""
        fits, warning = _check_domain_fit([], "ai-coding")
        assert fits is True
        assert warning is None

    def test_multi_domain_overlap_any_match_fits(self) -> None:
        """If project_domain is in agent_domains, fits=True regardless of list length."""
        fits, warning = _check_domain_fit(
            ["ai-coding", "ui-ux", "multi-agent"], "ui-ux"
        )
        assert fits is True
        assert warning is None


class TestIntegrationWithShippedAgents:
    """Spot-check the 10 shipped agent templates parse as expected."""

    @pytest.mark.parametrize(
        "agent_name,expected",
        [
            ("code-reviewer", ["ai-coding", "ui-ux"]),
            ("coherence-auditor", ["*"]),
            ("continuity-auditor", ["storytelling"]),
            ("contrarian-reviewer", ["*"]),
            ("documentation-writer", ["*"]),
            ("orchestrator", ["*"]),
            ("security-auditor", ["ai-coding"]),
            ("test-generator", ["ai-coding"]),
            ("validator", ["*"]),
            ("voice-coach", ["storytelling"]),
        ],
    )
    def test_shipped_agent_domains(self, agent_name: str, expected: list[str]) -> None:
        from pathlib import Path

        agent_path = (
            Path(__file__).resolve().parent.parent
            / "documents"
            / "agents"
            / f"{agent_name}.md"
        )
        content = agent_path.read_text()
        assert _parse_applicable_domains(content) == expected
