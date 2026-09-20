"""Deterministic index serialization (BACKLOG #187).

The extractor's index is committed to git. Set iteration order varies by
PYTHONHASHSEED, so an unsorted set->list conversion churned the committed index
across processes (471/473 identical tag strings in different array positions).

Asserting the emitted ordering is *sorted* is equivalent to asserting it is
seed-independent — sorted output is identical under every hash seed — so these
tests need no subprocess.
"""

import json
from unittest.mock import patch

from ai_governance_mcp.models import (
    DomainIndex,
    GlobalIndex,
    Method,
    MethodMetadata,
)


def _extractor(test_settings):
    with patch("sentence_transformers.SentenceTransformer"):
        from ai_governance_mcp.extractor import DocumentExtractor

        return DocumentExtractor(test_settings)


class TestReferenceTagOrdering:
    """The tags->purpose_keywords merge (extractor.py ~1183) must be sorted."""

    def test_purpose_keywords_sorted_from_tags(self, test_settings):
        extractor = _extractor(test_settings)
        ref = test_settings.documents_path / "ref.md"
        ref.write_text(
            "---\n"
            "id: ref-x\n"
            "title: X\n"
            "domain: ai-coding\n"
            "tags: [zebra, mango, apple, delta, bravo, yankee]\n"
            "status: current\n"
            "entry_type: direct\n"
            "---\n"
            "Body without a Purpose section.\n"
        )
        entry = extractor._parse_reference_file(ref, "ai-coding")
        assert entry is not None
        pk = entry.metadata.purpose_keywords
        # sorted <=> seed-independent
        assert pk == sorted(pk)
        # and it genuinely reordered the (non-sorted) input
        assert pk != ["zebra", "mango", "apple", "delta", "bravo", "yankee"]
        assert {"apple", "bravo", "delta", "mango", "yankee", "zebra"} <= set(pk)


class TestSaveIndexDeterministic:
    """_save_index must serialize with sort_keys=True for seed-independent keys."""

    def test_save_index_sorts_json_keys(self, test_settings):
        extractor = _extractor(test_settings)
        method = Method(
            id="coding-method-x",
            domain="ai-coding",
            title="X",
            content="c",
            line_range=(1, 2),
            metadata=MethodMetadata(purpose_keywords=["b", "a", "c"]),
        )
        index = GlobalIndex(
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
        extractor._save_index(index)
        written = (test_settings.index_path / "global_index.json").read_text()

        # Byte-identical to a sort_keys dump: a regression (dropping sort_keys)
        # would emit pydantic field-definition order and fail this.
        assert written == json.dumps(index.model_dump(), indent=2, sort_keys=True)
        top_keys = list(json.loads(written).keys())
        assert top_keys == sorted(top_keys)
