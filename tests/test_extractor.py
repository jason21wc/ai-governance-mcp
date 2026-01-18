"""Unit tests for the document extractor module.

Per specification v4: Tests for document parsing, embedding generation, and index building.
Per governance Q3 (Testing Integration): Comprehensive coverage for extractor.py.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# EmbeddingGenerator Tests
# =============================================================================


class TestEmbeddingGeneratorInit:
    """Tests for EmbeddingGenerator initialization."""

    def test_init_sets_model_name(self):
        """Should store model name without loading model."""
        from ai_governance_mcp.extractor import EmbeddingGenerator

        generator = EmbeddingGenerator("test-model")

        assert generator.model_name == "test-model"
        assert generator._model is None  # Not loaded yet

    def test_init_default_model(self):
        """Should use default model name if not specified."""
        from ai_governance_mcp.extractor import EmbeddingGenerator

        generator = EmbeddingGenerator()

        assert generator.model_name == "BAAI/bge-small-en-v1.5"


class TestEmbeddingGeneratorLazyLoad:
    """Tests for EmbeddingGenerator lazy loading behavior."""

    def test_model_property_loads_on_access(self, mock_embedder):
        """Model should be loaded on first access."""
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator("test-model")
            assert generator._model is None

            _ = generator.model

            mock_st.assert_called_once_with("test-model")
            assert generator._model is not None

    def test_model_property_returns_cached(self, mock_embedder):
        """Model should be cached after first load."""
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator("test-model")

            _ = generator.model
            _ = generator.model
            _ = generator.model

            mock_st.assert_called_once()  # Only loaded once


class TestEmbeddingGeneratorEmbed:
    """Tests for EmbeddingGenerator.embed() method."""

    def test_embed_empty_list(self, mock_embedder):
        """Should return empty array for empty input."""
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            result = generator.embed([])

            assert isinstance(result, np.ndarray)
            assert result.size == 0

    def test_embed_single_text(self, mock_embedder):
        """Should return embedding for single text."""
        mock_embedder.encode = Mock(return_value=np.random.rand(1, 384))
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            result = generator.embed(["test text"])

            mock_embedder.encode.assert_called_once()
            assert result.shape == (1, 384)

    def test_embed_multiple_texts(self, mock_embedder):
        """Should return embeddings for multiple texts."""
        mock_embedder.encode = Mock(return_value=np.random.rand(3, 384))
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            result = generator.embed(["text 1", "text 2", "text 3"])

            assert result.shape == (3, 384)

    def test_embed_shows_progress_bar_for_large_batches(self, mock_embedder):
        """Should show progress bar for >10 items."""
        mock_embedder.encode = Mock(return_value=np.random.rand(15, 384))
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            generator.embed(["text"] * 15)

            mock_embedder.encode.assert_called_once()
            call_kwargs = mock_embedder.encode.call_args[1]
            assert call_kwargs.get("show_progress_bar") is True

    def test_embed_no_progress_bar_for_small_batches(self, mock_embedder):
        """Should not show progress bar for <=10 items."""
        mock_embedder.encode = Mock(return_value=np.random.rand(5, 384))
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            generator.embed(["text"] * 5)

            call_kwargs = mock_embedder.encode.call_args[1]
            assert call_kwargs.get("show_progress_bar") is False


class TestEmbeddingGeneratorEmbedSingle:
    """Tests for EmbeddingGenerator.embed_single() method."""

    def test_embed_single_returns_1d_array(self, mock_embedder):
        """Should return 1D array for single text."""
        mock_embedder.encode = Mock(return_value=np.array([[0.1] * 384]))
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            result = generator.embed_single("test text")

            assert result.shape == (384,)


class TestEmbeddingGeneratorDimensions:
    """Tests for EmbeddingGenerator.dimensions property."""

    def test_dimensions_returns_model_dimension(self, mock_embedder):
        """Should return model's embedding dimension."""
        mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
        mock_st = Mock(return_value=mock_embedder)

        with patch("sentence_transformers.SentenceTransformer", mock_st):
            from ai_governance_mcp.extractor import EmbeddingGenerator

            generator = EmbeddingGenerator()
            dims = generator.dimensions

            assert dims == 384


# =============================================================================
# DocumentExtractor Initialization Tests
# =============================================================================


class TestDocumentExtractorInit:
    """Tests for DocumentExtractor initialization."""

    def test_init_loads_domains(self, test_settings, sample_domains_json):
        """Should load domain configurations on init."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)

            assert len(extractor.domains) >= 1

    def test_init_creates_embedder(self, test_settings, sample_domains_json):
        """Should create EmbeddingGenerator on init."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)

            assert extractor.embedder is not None
            assert extractor.embedder.model_name == test_settings.embedding_model


# =============================================================================
# Principle Extraction Tests
# =============================================================================


class TestExtractPrinciples:
    """Tests for _extract_principles() method."""

    def test_extract_principles_parses_headers(
        self, test_settings, sample_principles_md
    ):
        """Should parse principle headers from markdown."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="test-principles.md",
                description="Test domain",
                priority=0,
            )

            principles = extractor._extract_principles(domain_config)

            # Should find S1, C1, C2, Q1 from the sample file
            assert len(principles) >= 3
            series_codes = [p.series_code for p in principles]
            assert "S" in series_codes
            assert "C" in series_codes

    def test_extract_principles_captures_content(
        self, test_settings, sample_principles_md
    ):
        """Should capture content until next header."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="test-principles.md",
                description="Test domain",
                priority=0,
            )

            principles = extractor._extract_principles(domain_config)

            # Each principle should have content
            for p in principles:
                assert len(p.content) > 0
                assert p.title in p.content or "Definition" in p.content

    def test_extract_principles_sets_line_range(
        self, test_settings, sample_principles_md
    ):
        """Should set correct line range for each principle."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="test-principles.md",
                description="Test domain",
                priority=0,
            )

            principles = extractor._extract_principles(domain_config)

            for p in principles:
                start, end = p.line_range
                assert start > 0
                assert end >= start

    def test_extract_principles_missing_file(self, test_settings):
        """Should return empty list for missing file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="test",
                display_name="Test",
                principles_file="nonexistent.md",
                description="Test",
                priority=0,
            )

            principles = extractor._extract_principles(domain_config)

            assert principles == []

    def test_extract_principles_empty_file(self, test_settings, temp_dir):
        """Should return empty list for empty file."""
        # Create empty file
        empty_file = temp_dir / "documents" / "empty.md"
        empty_file.write_text("")

        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="test",
                display_name="Test",
                principles_file="empty.md",
                description="Test",
                priority=0,
            )

            principles = extractor._extract_principles(domain_config)

            assert principles == []


# =============================================================================
# Method Extraction Tests
# =============================================================================


class TestExtractMethods:
    """Tests for _extract_methods() method."""

    def test_extract_methods_parses_sections(self, test_settings, sample_methods_md):
        """Should parse numbered method sections."""
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

            methods = extractor._extract_methods(domain_config)

            # Should find at least 2 methods from sample
            assert len(methods) >= 2

    def test_extract_methods_builds_ids(self, test_settings, sample_methods_md):
        """Should create correct method IDs."""
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

            methods = extractor._extract_methods(domain_config)

            # IDs should follow pattern domain-method-{title-slug}
            assert len(methods) == 2
            assert methods[0].id == "coding-method-cold-start-kit"
            assert methods[1].id == "coding-method-gate-validation"

    def test_extract_methods_missing_file(self, test_settings):
        """Should return empty list for missing methods file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            domain_config = DomainConfig(
                name="test",
                display_name="Test",
                principles_file="test-principles.md",
                methods_file="nonexistent-methods.md",
                description="Test",
                priority=0,
            )

            methods = extractor._extract_methods(domain_config)

            assert methods == []


# =============================================================================
# Metadata Generation Tests
# =============================================================================


class TestGenerateMetadata:
    """Tests for _generate_metadata() method."""

    def test_generate_metadata_extracts_keywords(
        self, test_settings, sample_domains_json
    ):
        """Should extract keywords from title."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            metadata = extractor._generate_metadata(
                "meta-C1",
                "C",
                "Context Engineering Principle",
                "Content here",
            )

            # Words > 3 chars should be extracted
            assert "context" in metadata.keywords
            assert "engineering" in metadata.keywords
            assert "principle" in metadata.keywords

    def test_generate_metadata_creates_aliases(
        self, test_settings, sample_domains_json
    ):
        """Should create aliases from title slug."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            metadata = extractor._generate_metadata(
                "coding-core-context-engineering",
                "core",
                "Context Engineering Principle",
                "Content",
            )

            # Aliases are derived from title slug parts (> 3 chars)
            assert "context" in metadata.aliases
            assert "engineering" in metadata.aliases


class TestExtractPhrases:
    """Tests for _extract_phrases() method."""

    def test_extract_phrases_finds_quoted(self, test_settings, sample_domains_json):
        """Should extract quoted phrases."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            content = 'This is a "test phrase" and "another one" in content.'
            phrases = extractor._extract_phrases(content)

            assert "test phrase" in phrases
            assert "another one" in phrases

    def test_extract_phrases_finds_bold(self, test_settings, sample_domains_json):
        """Should extract bold phrases."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            content = "This has **bold phrase** and **another bold** text."
            phrases = extractor._extract_phrases(content)

            assert "bold phrase" in phrases
            assert "another bold" in phrases

    def test_extract_phrases_limits_to_ten(self, test_settings, sample_domains_json):
        """Should limit to 10 phrases."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            content = " ".join([f'"phrase {i}"' for i in range(20)])
            phrases = extractor._extract_phrases(content)

            assert len(phrases) <= 10


class TestExtractFailureIndicators:
    """Tests for _extract_failure_indicators() method."""

    def test_extract_failure_indicators_finds_section(
        self, test_settings, sample_domains_json
    ):
        """Should extract from Failure Mode sections."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            content = """
Some content here.

**Failure Mode: Coverage Gaming**
Writing tests that exercise code but don't actually validate behavior.
High coverage numbers with low value tests.
"""
            indicators = extractor._extract_failure_indicators(content)

            assert len(indicators) > 0
            # Should find relevant words
            assert any(
                "writing" in ind or "tests" in ind or "coverage" in ind
                for ind in indicators
            )


# =============================================================================
# Domain Prefix Tests
# =============================================================================


class TestGetDomainPrefix:
    """Tests for _get_domain_prefix() method."""

    def test_get_domain_prefix_constitution(self, test_settings, sample_domains_json):
        """Should return 'meta' for constitution domain."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            prefix = extractor._get_domain_prefix("constitution")

            assert prefix == "meta"

    def test_get_domain_prefix_ai_coding(self, test_settings, sample_domains_json):
        """Should return 'coding' for ai-coding domain."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            prefix = extractor._get_domain_prefix("ai-coding")

            assert prefix == "coding"

    def test_get_domain_prefix_multi_agent(self, test_settings, sample_domains_json):
        """Should return 'multi' for multi-agent domain."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            prefix = extractor._get_domain_prefix("multi-agent")

            assert prefix == "multi"

    def test_get_domain_prefix_unknown(self, test_settings, sample_domains_json):
        """Should return first 4 chars for unknown domain."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            prefix = extractor._get_domain_prefix("custom-domain")

            assert prefix == "cust"


# =============================================================================
# Embedding Text Tests
# =============================================================================


class TestGetEmbeddingText:
    """Tests for _get_embedding_text() method."""

    def test_get_embedding_text_structure(
        self, test_settings, sample_domains_json, sample_principle
    ):
        """Should combine title, content, and metadata."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            text = extractor._get_embedding_text(sample_principle)

            assert sample_principle.title in text
            assert sample_principle.content[:100] in text

    def test_get_embedding_text_truncates_content(
        self, test_settings, sample_domains_json
    ):
        """Should truncate content to 1500 chars (increased for BGE model)."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import Principle, PrincipleMetadata

            extractor = DocumentExtractor(test_settings)

            # Create principle with long content
            long_principle = Principle(
                id="meta-C1",
                domain="constitution",
                series_code="C",
                number=1,
                title="Test",
                content="A" * 2000,
                line_range=(1, 100),
                metadata=PrincipleMetadata(),
            )

            text = extractor._get_embedding_text(long_principle)

            # Should not contain full content (2000 chars)
            assert "A" * 2000 not in text
            # But should contain truncated content (1500 chars)
            assert "A" * 1500 in text


# =============================================================================
# Index Persistence Tests
# =============================================================================


class TestSaveIndex:
    """Tests for _save_index() method."""

    def test_save_index_writes_json(
        self, test_settings, sample_domains_json, sample_global_index
    ):
        """Should write global_index.json file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            extractor._save_index(sample_global_index)

            index_file = test_settings.index_path / "global_index.json"
            assert index_file.exists()

            # Should be valid JSON
            with open(index_file) as f:
                data = json.load(f)
            assert "domains" in data
            assert "created_at" in data


class TestSaveEmbeddings:
    """Tests for _save_embeddings() method."""

    def test_save_embeddings_writes_npy(self, test_settings, sample_domains_json):
        """Should write .npy file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)
            embeddings = np.random.rand(10, 384)

            extractor._save_embeddings(embeddings, "test_embeddings.npy")

            embeddings_file = test_settings.index_path / "test_embeddings.npy"
            assert embeddings_file.exists()

            # Should load correctly
            loaded = np.load(embeddings_file)
            assert loaded.shape == (10, 384)


# =============================================================================
# Slow Tests - Real Embedding Model
# =============================================================================


@pytest.mark.slow
class TestRealEmbeddings:
    """Tests using real embedding model. Run with: pytest -m slow"""

    def test_real_embedding_dimensions(self):
        """Verify BAAI/bge-small-en-v1.5 produces 384 dims."""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        emb = model.encode(["test"])

        assert emb.shape == (1, 384)

    def test_real_semantic_similarity(self):
        """Verify similar texts have higher similarity."""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        emb1 = model.encode(["write code"])
        emb2 = model.encode(["write software"])
        emb3 = model.encode(["cook dinner"])

        # Calculate similarities
        sim_12 = np.dot(emb1, emb2.T)[0][0]
        sim_13 = np.dot(emb1, emb3.T)[0][0]

        # Related topics should be more similar
        assert sim_12 > sim_13

    def test_real_batch_embedding_consistency(self):
        """Verify batch embedding produces consistent results."""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-small-en-v1.5")

        # Single vs batch should produce same result
        single = model.encode(["test query"])
        batch = model.encode(["test query", "other text"])

        # First embedding from batch should match single
        assert np.allclose(single[0], batch[0], atol=1e-5)


# =============================================================================
# Domain File Validation Tests
# =============================================================================


class TestValidateDomainFiles:
    """Tests for validate_domain_files() pre-flight validation."""

    def test_validate_domain_files_passes_for_valid_config(
        self, test_settings, sample_principles_md, sample_methods_md
    ):
        """Should not raise when all configured files exist."""
        # Create a minimal domains.json that only references existing fixtures
        domains_path = test_settings.documents_path / "domains.json"
        domains_data = [
            {
                "name": "constitution",
                "display_name": "Constitution",
                "principles_file": "test-principles.md",
                "methods_file": "test-methods.md",
                "description": "Test domain",
                "priority": 0,
            }
        ]
        import json

        domains_path.write_text(json.dumps(domains_data))

        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            extractor = DocumentExtractor(test_settings)

            # Should not raise - all files exist
            extractor.validate_domain_files()

    def test_validate_domain_files_raises_for_missing_principles(
        self, test_settings, sample_domains_json
    ):
        """Should raise ExtractorConfigError for missing principles file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)

            # Inject domain with missing file
            extractor.domains.append(
                DomainConfig(
                    name="test-missing",
                    display_name="Missing Domain",
                    principles_file="nonexistent-principles.md",
                    description="Test domain",
                    priority=99,
                )
            )

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_domain_files()

            assert "nonexistent-principles.md" in str(exc_info.value)
            assert "test-missing" in str(exc_info.value)

    def test_validate_domain_files_raises_for_missing_methods(
        self, test_settings, sample_domains_json, sample_principles_md
    ):
        """Should raise ExtractorConfigError for missing methods file."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)

            # Inject domain with valid principles but missing methods
            extractor.domains.append(
                DomainConfig(
                    name="test-missing-methods",
                    display_name="Missing Methods Domain",
                    principles_file="test-principles.md",  # This exists
                    methods_file="nonexistent-methods.md",
                    description="Test domain",
                    priority=99,
                )
            )

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_domain_files()

            assert "nonexistent-methods.md" in str(exc_info.value)
            assert "test-missing-methods" in str(exc_info.value)

    def test_validate_domain_files_reports_all_missing(
        self, test_settings, sample_domains_json
    ):
        """Should report ALL missing files, not just the first."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)

            # Inject multiple domains with missing files
            extractor.domains.append(
                DomainConfig(
                    name="bad-domain-1",
                    display_name="Bad 1",
                    principles_file="missing-1.md",
                    methods_file="missing-2.md",
                    description="Test",
                    priority=98,
                )
            )
            extractor.domains.append(
                DomainConfig(
                    name="bad-domain-2",
                    display_name="Bad 2",
                    principles_file="missing-3.md",
                    description="Test",
                    priority=99,
                )
            )

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_domain_files()

            error_msg = str(exc_info.value)
            # Should contain all missing files
            assert "missing-1.md" in error_msg
            assert "missing-2.md" in error_msg
            assert "missing-3.md" in error_msg
            assert "bad-domain-1" in error_msg
            assert "bad-domain-2" in error_msg

    def test_validate_domain_files_suggests_checking_domains_json(
        self, test_settings, sample_domains_json
    ):
        """Should provide actionable guidance in error message."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            extractor = DocumentExtractor(test_settings)
            extractor.domains.append(
                DomainConfig(
                    name="test",
                    display_name="Test",
                    principles_file="missing.md",
                    description="Test",
                    priority=99,
                )
            )

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_domain_files()

            assert "domains.json" in str(exc_info.value)


class TestExtractorConfigError:
    """Tests for ExtractorConfigError exception class."""

    def test_extractor_config_error_is_exception(self):
        """Should be a proper exception class."""
        from ai_governance_mcp.extractor import ExtractorConfigError

        assert issubclass(ExtractorConfigError, Exception)

    def test_extractor_config_error_message(self):
        """Should preserve error message."""
        from ai_governance_mcp.extractor import ExtractorConfigError

        error = ExtractorConfigError("Test error message")
        assert str(error) == "Test error message"


# =============================================================================
# Version Consistency Validation Tests
# =============================================================================


class TestValidateVersionConsistency:
    """Tests for validate_version_consistency() version validation."""

    def test_validate_version_consistency_passes_when_matching(
        self, test_settings, tmp_path
    ):
        """Should not raise when filename version matches header version."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            # Create a file with matching versions
            doc_file = tmp_path / "test-doc-v1.2.3.md"
            doc_file.write_text("# Test\n\n**Version:** 1.2.3\n\nContent here.")

            test_settings.documents_path = tmp_path
            extractor = DocumentExtractor(test_settings)
            extractor.domains = [
                DomainConfig(
                    name="test",
                    display_name="Test",
                    principles_file="test-doc-v1.2.3.md",
                    methods_file=None,
                    description="Test domain",
                    priority=0,
                )
            ]

            # Should not raise - versions match
            extractor.validate_version_consistency()

    def test_validate_version_consistency_raises_for_mismatch(
        self, test_settings, tmp_path
    ):
        """Should raise ExtractorConfigError when versions don't match."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            # Create a file with mismatched versions
            doc_file = tmp_path / "test-doc-v1.0.0.md"
            doc_file.write_text("# Test\n\n**Version:** 2.0.0\n\nContent here.")

            test_settings.documents_path = tmp_path
            extractor = DocumentExtractor(test_settings)
            extractor.domains = [
                DomainConfig(
                    name="test-mismatch",
                    display_name="Test Mismatch",
                    principles_file="test-doc-v1.0.0.md",
                    methods_file=None,
                    description="Test domain",
                    priority=0,
                )
            ]

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_version_consistency()

            error_msg = str(exc_info.value)
            assert "1.0.0" in error_msg  # Filename version
            assert "2.0.0" in error_msg  # Header version
            assert "test-mismatch" in error_msg

    def test_validate_version_consistency_skips_files_without_version_in_name(
        self, test_settings, tmp_path
    ):
        """Should skip validation for files without version in filename."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            # Create a file without version in name
            doc_file = tmp_path / "test-doc.md"
            doc_file.write_text("# Test\n\n**Version:** 1.0.0\n\nContent here.")

            test_settings.documents_path = tmp_path
            extractor = DocumentExtractor(test_settings)
            extractor.domains = [
                DomainConfig(
                    name="test",
                    display_name="Test",
                    principles_file="test-doc.md",
                    methods_file=None,
                    description="Test domain",
                    priority=0,
                )
            ]

            # Should not raise - no version in filename to compare
            extractor.validate_version_consistency()

    def test_validate_version_consistency_skips_files_without_header_version(
        self, test_settings, tmp_path
    ):
        """Should skip validation for files without version in header."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor
            from ai_governance_mcp.models import DomainConfig

            # Create a file with version in name but not in header
            doc_file = tmp_path / "test-doc-v1.0.0.md"
            doc_file.write_text("# Test\n\nNo version header here.\n\nContent.")

            test_settings.documents_path = tmp_path
            extractor = DocumentExtractor(test_settings)
            extractor.domains = [
                DomainConfig(
                    name="test",
                    display_name="Test",
                    principles_file="test-doc-v1.0.0.md",
                    methods_file=None,
                    description="Test domain",
                    priority=0,
                )
            ]

            # Should not raise - no header version to compare
            extractor.validate_version_consistency()

    def test_validate_version_consistency_checks_both_principles_and_methods(
        self, test_settings, tmp_path
    ):
        """Should check version consistency for both file types."""
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import (
                DocumentExtractor,
                ExtractorConfigError,
            )
            from ai_governance_mcp.models import DomainConfig

            # Create files with mismatched versions
            principles_file = tmp_path / "principles-v1.0.0.md"
            principles_file.write_text("# Principles\n\n**Version:** 1.0.0\n")

            methods_file = tmp_path / "methods-v2.0.0.md"
            methods_file.write_text("# Methods\n\n**Version:** 3.0.0\n")  # Mismatch!

            test_settings.documents_path = tmp_path
            extractor = DocumentExtractor(test_settings)
            extractor.domains = [
                DomainConfig(
                    name="test",
                    display_name="Test",
                    principles_file="principles-v1.0.0.md",
                    methods_file="methods-v2.0.0.md",
                    description="Test domain",
                    priority=0,
                )
            ]

            with pytest.raises(ExtractorConfigError) as exc_info:
                extractor.validate_version_consistency()

            error_msg = str(exc_info.value)
            assert "methods" in error_msg
            assert "2.0.0" in error_msg  # Filename version
            assert "3.0.0" in error_msg  # Header version
