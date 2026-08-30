"""Method aliases — parity with principles (BACKLOG #181).

Public-code consumption points for the new field:
- extractor: _build_method populates Method.aliases from `**Aliases:**`
- retrieval: get_method_by_id resolves a former ID via Method.aliases

The private-script consumer (analyze_feedback_loop dead-methods rescue) is tested
in test_feedback_loop_analysis.py, which is staged out of the public build.
"""

from unittest.mock import patch

from ai_governance_mcp.config import Settings
from ai_governance_mcp.models import DomainIndex, GlobalIndex, Method


def _extractor(test_settings):
    with patch("sentence_transformers.SentenceTransformer"):
        from ai_governance_mcp.extractor import DocumentExtractor

        return DocumentExtractor(test_settings)


class TestBuildMethodAliases:
    def test_build_method_populates_aliases(self, test_settings):
        extractor = _extractor(test_settings)
        data = {
            "title": "Some Method",
            "content": (
                "**Purpose:** Do a thing.\n\n"
                "**Aliases:** `coding-M125`, `coding-old-slug`"
            ),
            "domain": "ai-coding",
            "start_line": 1,
            "end_line": 5,
        }
        method = extractor._build_method(data, "coding")
        assert method.aliases == ["coding-M125", "coding-old-slug"]

    def test_build_method_no_aliases_defaults_empty(self, test_settings):
        extractor = _extractor(test_settings)
        data = {
            "title": "Plain Method",
            "content": "**Purpose:** No aliases declared here.",
            "domain": "ai-coding",
            "start_line": 1,
            "end_line": 3,
        }
        method = extractor._build_method(data, "coding")
        assert method.aliases == []


class TestGetMethodByIdAliases:
    def _engine(self, tmp_path, method):
        from ai_governance_mcp.retrieval import RetrievalEngine

        settings = Settings()
        settings.index_path = tmp_path
        settings.logs_path = tmp_path
        engine = RetrievalEngine(settings)
        engine.index = GlobalIndex(
            domains={
                "ai-coding": DomainIndex(
                    domain="ai-coding",
                    methods=[method],
                    last_extracted="2026-01-01T00:00:00Z",
                )
            },
            created_at="2026-01-01T00:00:00Z",
            embedding_model="test",
            embedding_dimensions=3,
        )
        engine._check_index_freshness = lambda: None
        return engine

    @staticmethod
    def _method():
        return Method(
            id="coding-method-new-name",
            domain="ai-coding",
            title="T",
            content="c",
            line_range=(1, 2),
            aliases=["coding-M125"],
        )

    def test_resolves_by_canonical_id(self, tmp_path):
        m = self._method()
        assert self._engine(tmp_path, m).get_method_by_id("coding-method-new-name") is m

    def test_resolves_by_alias(self, tmp_path):
        m = self._method()
        assert self._engine(tmp_path, m).get_method_by_id("coding-M125") is m

    def test_unknown_id_returns_none(self, tmp_path):
        m = self._method()
        assert self._engine(tmp_path, m).get_method_by_id("coding-nope") is None
