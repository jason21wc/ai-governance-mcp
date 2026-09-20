"""Build-generation identity: the index JSON and its .npy matrices must
provably come from the same build.

BACKLOG #217. The governance index is three files written separately
(content_embeddings.npy, domain_embeddings.npy, global_index.json). Before
this change, nothing bound them as a set — a crash, partial rebuild, or
mixed deployment could silently pair stale metadata with new vectors. The
existing canary-ROW check (3 of ~1048 rows) is probabilistic; this suite
pins a deterministic SHA-256 digest binding.
"""

import hashlib
import json
from unittest.mock import Mock, patch

import numpy as np

from ai_governance_mcp.models import (
    DomainConfig,
    DomainIndex,
    GlobalIndex,
    Principle,
)
from ai_governance_mcp.retrieval import RetrievalEngine

DIM = 384
TEST_MODEL = "BAAI/bge-small-en-v1.5"


def _one_hot(position: int) -> np.ndarray:
    vec = np.zeros(DIM, dtype=np.float32)
    vec[position] = 1.0
    return vec


def _make_index(*, n_items=2, matrix_digests=None, build_id=None):
    principles = [
        Principle(
            id=f"gen-{i}",
            domain="test",
            series_code="G",
            title=f"Generation Test {i}",
            content=f"Item {i} for generation identity testing.",
            line_range=(1, 10),
            embedding_id=i,
        )
        for i in range(n_items)
    ]
    return GlobalIndex(
        domains={
            "test": DomainIndex(
                domain="test",
                principles=principles,
                methods=[],
                references=[],
                last_extracted="2026-08-05T00:00:00Z",
            ),
        },
        domain_configs=[
            DomainConfig(
                name="test",
                display_name="Test",
                principles_file="test-principles.md",
                methods_file="test-methods.md",
                description="Test domain",
                embedding_id=0,
            ),
        ],
        created_at="2026-08-05T00:00:00Z",
        version="1.0",
        embedding_model=TEST_MODEL,
        embedding_dimensions=DIM,
        embedding_canaries=[],
        build_id=build_id,
        matrix_digests=matrix_digests,
    )


def _content_matrix(n_items=2):
    return np.stack([_one_hot(i) for i in range(n_items)])


def _domain_matrix(n_domains=1):
    return np.zeros((n_domains, DIM), dtype=np.float32)


def _digest(arr: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(arr, dtype=np.float32).tobytes()).hexdigest()


def _write_index(settings, index, content_emb, domain_emb):
    with open(settings.index_path / "global_index.json", "w") as f:
        json.dump(index.model_dump(), f, sort_keys=True)
    np.save(settings.index_path / "content_embeddings.npy", content_emb)
    np.save(settings.index_path / "domain_embeddings.npy", domain_emb)


def _engine(settings):
    embedder = Mock()
    embedder.encode = Mock(
        side_effect=lambda texts, *a, **k: (
            np.stack([_one_hot(0)] * (len(texts) if not isinstance(texts, str) else 1))
        )
    )
    embedder.get_sentence_embedding_dimension = Mock(return_value=DIM)

    settings.embedding_model = TEST_MODEL

    def _install(self):
        self._embedder = embedder
        return True

    with patch.object(RetrievalEngine, "_try_embedding_client", _install):
        engine = RetrievalEngine(settings)
    engine._embedder = embedder
    return engine


# =========================================================================
# Task 1, 12: Extractor stamps digest fields
# =========================================================================


class TestBuildGeneration:
    def test_digest_fields_exist(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            index = extractor.extract_all()

            assert index.build_id is not None
            assert isinstance(index.build_id, str)
            assert len(index.build_id) == 32  # UUID4 hex

            assert index.matrix_digests is not None
            assert "content_embeddings" in index.matrix_digests
            assert "domain_embeddings" in index.matrix_digests
            for key, val in index.matrix_digests.items():
                assert len(val) == 64  # SHA-256 hex

    def test_build_id_unique_per_build(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            id1 = extractor.extract_all().build_id
            id2 = extractor.extract_all().build_id
            assert id1 != id2

    def test_digest_matches_array_content(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            index = extractor.extract_all()

            content_emb = np.load(test_settings.index_path / "content_embeddings.npy")
            domain_emb = np.load(test_settings.index_path / "domain_embeddings.npy")

            assert index.matrix_digests["content_embeddings"] == _digest(content_emb)
            assert index.matrix_digests["domain_embeddings"] == _digest(domain_emb)


# =========================================================================
# Tasks 5-9, 13: Load-time digest gate
# =========================================================================


class TestDigestGate:
    def test_matching_digests_pass(self, test_settings):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index(
            matrix_digests={
                "content_embeddings": _digest(content),
                "domain_embeddings": _digest(domain),
            },
            build_id="test-build-001",
        )
        _write_index(test_settings, index, content, domain)

        engine = _engine(test_settings)
        assert engine.content_embeddings is not None

    def test_mismatched_content_digest_degrades(self, test_settings, caplog):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index(
            matrix_digests={
                "content_embeddings": _digest(content),
                "domain_embeddings": _digest(domain),
            },
            build_id="test-build-002",
        )

        different_content = np.stack([_one_hot(1), _one_hot(0)])
        _write_index(test_settings, index, different_content, domain)

        import logging

        with caplog.at_level(logging.ERROR):
            engine = _engine(test_settings)

        assert engine.content_embeddings is None
        assert any("different builds" in r.message for r in caplog.records)

    def test_mismatched_domain_digest_degrades(self, test_settings, caplog):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index(
            matrix_digests={
                "content_embeddings": _digest(content),
                "domain_embeddings": _digest(domain),
            },
            build_id="test-build-003",
        )

        different_domain = np.ones((1, DIM), dtype=np.float32)
        _write_index(test_settings, index, content, different_domain)

        import logging

        with caplog.at_level(logging.ERROR):
            engine = _engine(test_settings)

        assert engine.content_embeddings is None
        assert any("different builds" in r.message for r in caplog.records)

    def test_legacy_index_skips_digest_check(self, test_settings):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index()  # no matrix_digests
        _write_index(test_settings, index, content, domain)

        engine = _engine(test_settings)
        assert engine.content_embeddings is not None

    def test_digest_error_degrades_not_crashes(self, test_settings):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index(
            matrix_digests={
                "content_embeddings": _digest(content),
                "domain_embeddings": _digest(domain),
            },
            build_id="test-build-err",
        )
        _write_index(test_settings, index, content, domain)

        with patch("ai_governance_mcp.retrieval.hashlib") as mock_hashlib:
            mock_hashlib.sha256.side_effect = OSError("disk error")
            engine = _engine(test_settings)

        assert engine.content_embeddings is None

    def test_rollback_preserves_on_digest_mismatch(self, test_settings):
        content = _content_matrix()
        domain = _domain_matrix()
        index = _make_index(
            matrix_digests={
                "content_embeddings": _digest(content),
                "domain_embeddings": _digest(domain),
            },
            build_id="test-build-rollback",
        )
        _write_index(test_settings, index, content, domain)

        engine = _engine(test_settings)
        assert engine.content_embeddings is not None
        old_emb = engine.content_embeddings.copy()

        import time

        time.sleep(0.05)

        different_content = np.stack([_one_hot(1), _one_hot(0)])
        np.save(test_settings.index_path / "content_embeddings.npy", different_content)
        with open(test_settings.index_path / "global_index.json", "w") as f:
            json.dump(index.model_dump(), f, sort_keys=True)

        engine._check_index_freshness()

        assert engine.content_embeddings is not None
        np.testing.assert_array_equal(engine.content_embeddings, old_emb)
