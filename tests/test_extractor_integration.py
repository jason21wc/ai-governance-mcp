"""Integration tests for the document extractor.

Per specification v4: Tests for the complete extraction pipeline.
Per governance Q3 (Testing Integration): End-to-end extraction validation.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# extract_all() Integration Tests
# =============================================================================


class TestExtractAll:
    """Tests for the complete extract_all() pipeline."""

    def test_extract_all_creates_global_index(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should create a complete GlobalIndex."""
        # Mock the embedding model to return consistent embeddings
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import GlobalIndex

            extractor = DocumentExtractor(test_settings)
            index = extractor.extract_all()

            assert isinstance(index, GlobalIndex)
            assert len(index.domains) >= 1
            assert index.embedding_model == test_settings.embedding_model
            assert index.embedding_dimensions == 384

    def test_extract_all_saves_index_file(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should save global_index.json to disk."""
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            extractor.extract_all()

            index_file = test_settings.index_path / "global_index.json"
            assert index_file.exists()

            # Should be valid JSON
            with open(index_file) as f:
                data = json.load(f)
            assert "domains" in data
            assert "created_at" in data

    def test_extract_all_saves_content_embeddings(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should save content_embeddings.npy to disk."""
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            extractor.extract_all()

            embeddings_file = test_settings.index_path / "content_embeddings.npy"
            assert embeddings_file.exists()

            # Should be loadable numpy array
            embeddings = np.load(embeddings_file)
            assert embeddings.ndim == 2
            assert embeddings.shape[1] == 384

    def test_extract_all_saves_domain_embeddings(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should save domain_embeddings.npy to disk."""
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(len(texts), 384)
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            extractor.extract_all()

            domain_embeddings_file = test_settings.index_path / "domain_embeddings.npy"
            assert domain_embeddings_file.exists()

    def test_extract_all_assigns_embedding_ids(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should assign embedding_id to all principles and methods."""
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

            # Check all principles have embedding IDs
            for domain_name, domain_index in index.domains.items():
                for principle in domain_index.principles:
                    assert principle.embedding_id is not None
                    assert principle.embedding_id >= 0

                for method in domain_index.methods:
                    assert method.embedding_id is not None
                    assert method.embedding_id >= 0

    def test_extract_all_assigns_domain_embedding_ids(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """extract_all() should assign embedding_id to domain configs."""
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

            for domain_config in index.domain_configs:
                assert domain_config.embedding_id is not None


# =============================================================================
# _extract_domain() Integration Tests
# =============================================================================


class TestExtractDomain:
    """Tests for single domain extraction."""

    def test_extract_domain_creates_domain_index(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """_extract_domain() should create a complete DomainIndex."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig, DomainIndex

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="test-principles.md",
                methods_file=None,
                description="Test domain",
                priority=0,
            )

            index = extractor._extract_domain(domain_config)

            assert isinstance(index, DomainIndex)
            assert index.domain == "constitution"
            assert len(index.principles) > 0

    def test_extract_domain_with_methods(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """_extract_domain() should include methods when methods_file is specified."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="ai-coding",
                display_name="AI Coding",
                principles_file="test-principles.md",
                methods_file="test-methods.md",
                description="Test domain",
                priority=10,
            )

            index = extractor._extract_domain(domain_config)

            assert len(index.methods) > 0


# =============================================================================
# Full Pipeline Integration Tests
# =============================================================================


@pytest.mark.integration
class TestFullPipeline:
    """Tests for the complete extraction-to-retrieval pipeline."""

    def test_extracted_index_is_retrievable(
        self,
        test_settings,
        sample_principles_md,
        sample_methods_md,
        sample_domains_json,
    ):
        """Index created by extractor should be usable by retrieval engine."""
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=lambda texts, **kwargs: np.random.rand(
                len(texts) if isinstance(texts, list) else 1, 384
            )
        )
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)

        mock_reranker = Mock()
        mock_reranker.predict = Mock(
            side_effect=lambda pairs, **kwargs: np.array(
                [0.5 - i * 0.1 for i in range(len(pairs))]
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            with patch("sentence_transformers.CrossEncoder", mock_ce):
                # Step 1: Extract
                from ai_governance_mcp.extractor import DocumentExtractor

                extractor = DocumentExtractor(test_settings)
                extractor.extract_all()

                # Step 2: Load and retrieve
                from ai_governance_mcp.retrieval import RetrievalEngine

                engine = RetrievalEngine(test_settings)
                result = engine.retrieve("test query")

                # Should return results from the extracted index
                assert result.query == "test query"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestExtractorErrorHandling:
    """Tests for extractor error handling."""

    def test_extract_all_handles_missing_documents_dir(self, test_settings):
        """extract_all() should handle missing documents directory gracefully."""
        # Remove documents directory
        import shutil

        if test_settings.documents_path.exists():
            shutil.rmtree(test_settings.documents_path)

        mock_embedder = Mock()
        mock_embedder.encode = Mock(return_value=np.array([]))
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            # Should not raise, but return empty or minimal index
            index = extractor.extract_all()

            assert index is not None

    def test_extract_all_handles_empty_domain(self, test_settings, temp_dir):
        """extract_all() should handle domains with no principles."""
        # Create empty principles file
        empty_file = temp_dir / "documents" / "empty-principles.md"
        empty_file.parent.mkdir(parents=True, exist_ok=True)
        empty_file.write_text("# Empty Document\n\nNo principles here.")

        # Create domains.json pointing to empty file
        domains_config = [
            {
                "name": "empty",
                "display_name": "Empty Domain",
                "principles_file": "empty-principles.md",
                "description": "An empty domain",
                "priority": 0,
            }
        ]
        domains_file = temp_dir / "documents" / "domains.json"
        domains_file.write_text(json.dumps(domains_config))

        mock_embedder = Mock()
        mock_embedder.encode = Mock(return_value=np.array([]).reshape(0, 384))
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            index = extractor.extract_all()

            assert index is not None
            # The empty domain should exist but have no principles
            if "empty" in index.domains:
                assert len(index.domains["empty"].principles) == 0
