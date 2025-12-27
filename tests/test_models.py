"""Tests for Pydantic models (T19).

Per specification v4: Validates data model structures and constraints.
"""

import pytest
from pydantic import ValidationError

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.models import (
    SeriesCode,
    ConfidenceLevel,
    PrincipleMetadata,
    Principle,
    Method,
    DomainConfig,
    DomainIndex,
    GlobalIndex,
    ScoredPrinciple,
    ScoredMethod,
    RetrievalResult,
    Feedback,
    QueryLog,
    Metrics,
    ErrorResponse,
)


class TestEnums:
    """Test enum definitions."""

    def test_series_codes(self):
        """SeriesCode should have all expected values."""
        assert SeriesCode.S == "S"
        assert SeriesCode.C == "C"
        assert SeriesCode.Q == "Q"
        assert SeriesCode.O == "O"
        assert SeriesCode.G == "G"
        assert SeriesCode.MA == "MA"

    def test_confidence_levels(self):
        """ConfidenceLevel should have high, medium, low."""
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"


class TestPrincipleMetadata:
    """Test PrincipleMetadata model."""

    def test_default_values(self):
        """Should have empty lists as defaults."""
        meta = PrincipleMetadata()
        assert meta.keywords == []
        assert meta.synonyms == []
        assert meta.trigger_phrases == []
        assert meta.failure_indicators == []
        assert meta.aliases == []

    def test_with_values(self):
        """Should accept provided values."""
        meta = PrincipleMetadata(
            keywords=["spec", "requirements"],
            trigger_phrases=["missing requirements"],
        )
        assert "spec" in meta.keywords
        assert "missing requirements" in meta.trigger_phrases


class TestPrinciple:
    """Test Principle model."""

    def test_required_fields(self):
        """Should require id, domain, series_code, number, title, content, line_range."""
        with pytest.raises(ValidationError):
            Principle()  # Missing required fields

    def test_valid_principle(self):
        """Should accept valid principle data."""
        p = Principle(
            id="coding-C1",
            domain="ai-coding",
            series_code="C",
            number=1,
            title="Test Principle",
            content="Content here",
            line_range=(1, 10),
        )
        assert p.id == "coding-C1"
        assert p.embedding_id is None  # Optional

    def test_with_embedding_id(self):
        """Should accept embedding_id."""
        p = Principle(
            id="meta-S1",
            domain="constitution",
            series_code="S",
            number=1,
            title="Safety",
            content="Safety content",
            line_range=(1, 5),
            embedding_id=42,
        )
        assert p.embedding_id == 42


class TestMethod:
    """Test Method model."""

    def test_valid_method(self):
        """Should accept valid method data."""
        m = Method(
            id="coding-M1",
            domain="ai-coding",
            title="Cold Start Kit",
            content="Method content",
            line_range=(100, 150),
        )
        assert m.id == "coding-M1"
        assert m.keywords == []


class TestDomainConfig:
    """Test DomainConfig model."""

    def test_required_fields(self):
        """Should require name, display_name, principles_file."""
        with pytest.raises(ValidationError):
            DomainConfig()

    def test_valid_config(self):
        """Should accept valid config."""
        config = DomainConfig(
            name="ai-coding",
            display_name="AI Coding",
            principles_file="ai-coding-principles.md",
            description="Software development with AI",
        )
        assert config.name == "ai-coding"
        assert config.priority == 100  # Default
        assert config.methods_file is None  # Optional


class TestScoredPrinciple:
    """Test ScoredPrinciple model."""

    @pytest.fixture
    def sample_principle(self):
        """Create a sample principle."""
        return Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Test",
            content="Content",
            line_range=(1, 5),
        )

    def test_default_scores(self, sample_principle):
        """Should have default scores of 0."""
        sp = ScoredPrinciple(principle=sample_principle)
        assert sp.semantic_score == 0.0
        assert sp.keyword_score == 0.0
        assert sp.combined_score == 0.0
        assert sp.rerank_score is None
        assert sp.confidence == ConfidenceLevel.LOW

    def test_score_constraints(self, sample_principle):
        """Semantic and combined scores should be 0-1."""
        with pytest.raises(ValidationError):
            ScoredPrinciple(principle=sample_principle, semantic_score=1.5)

        with pytest.raises(ValidationError):
            ScoredPrinciple(principle=sample_principle, combined_score=-0.1)


class TestFeedback:
    """Test Feedback model."""

    def test_rating_constraints(self):
        """Rating must be 1-5."""
        with pytest.raises(ValidationError):
            Feedback(
                query="test",
                principle_id="meta-C1",
                rating=0,  # Invalid
                timestamp="2025-01-01T00:00:00Z",
            )

        with pytest.raises(ValidationError):
            Feedback(
                query="test",
                principle_id="meta-C1",
                rating=6,  # Invalid
                timestamp="2025-01-01T00:00:00Z",
            )

    def test_valid_feedback(self):
        """Should accept valid feedback."""
        f = Feedback(
            query="test query",
            principle_id="coding-C1",
            rating=5,
            timestamp="2025-01-01T00:00:00Z",
            comment="Very helpful!",
        )
        assert f.rating == 5
        assert f.comment == "Very helpful!"


class TestMetrics:
    """Test Metrics model."""

    def test_default_values(self):
        """Should have sensible defaults."""
        m = Metrics()
        assert m.total_queries == 0
        assert m.avg_retrieval_time_ms == 0.0
        assert m.s_series_trigger_count == 0
        assert m.feedback_count == 0
        assert m.avg_feedback_rating is None

    def test_confidence_distribution_default(self):
        """Should have high/medium/low keys."""
        m = Metrics()
        assert "high" in m.confidence_distribution
        assert "medium" in m.confidence_distribution
        assert "low" in m.confidence_distribution


class TestRetrievalResult:
    """Test RetrievalResult model."""

    def test_default_values(self):
        """Should have empty lists as defaults."""
        r = RetrievalResult(query="test", domains_detected=[])
        assert r.constitution_principles == []
        assert r.domain_principles == []
        assert r.methods == []
        assert r.s_series_triggered is False
        assert r.retrieval_time_ms is None


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error(self):
        """Should accept valid error response."""
        e = ErrorResponse(
            error_code="NOT_FOUND",
            message="Principle not found",
            suggestions=["Check ID format"],
        )
        assert e.error_code == "NOT_FOUND"
        assert len(e.suggestions) == 1
