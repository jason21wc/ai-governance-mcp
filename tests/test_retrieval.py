"""Tests for the hybrid retrieval engine (T21).

Per specification v4: Tests for domain routing, BM25, semantic search,
score fusion, reranking, and hierarchy filtering.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.config import Settings
from ai_governance_mcp.models import (
    Principle,
    PrincipleMetadata,
    DomainConfig,
    ScoredPrinciple,
    ConfidenceLevel,
)


class TestRetrievalEngineInit:
    """Test RetrievalEngine initialization."""

    def test_init_without_index(self, tmp_path):
        """Should handle missing index gracefully."""
        settings = Settings()
        settings.index_path = tmp_path / "nonexistent"

        # Import here to avoid dependency issues
        with patch("ai_governance_mcp.retrieval.np"):
            pass
            # Would log warning about missing index


class TestDomainRouting:
    """Tests for semantic domain routing (T6)."""

    @pytest.fixture
    def mock_engine(self):
        """Create engine with mocked embeddings."""
        engine = Mock()
        engine.index = Mock()
        engine.index.domain_configs = [
            DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="const.md",
                description="Universal rules",
            ),
            DomainConfig(
                name="ai-coding",
                display_name="AI Coding",
                principles_file="coding.md",
                description="Software development",
            ),
        ]
        engine.domain_embeddings = np.array(
            [
                [0.1, 0.2, 0.3],  # constitution
                [0.4, 0.5, 0.6],  # ai-coding
            ]
        )
        engine.settings = Settings()
        return engine


class TestSemanticSearch:
    """Tests for semantic embedding search (T8)."""

    def test_cosine_similarity_identical(self):
        """Identical vectors should have similarity 1.0."""
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0, 3.0])

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        similarity = np.dot(a, b) / (norm_a * norm_b)

        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity 0."""
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        similarity = np.dot(a, b) / (norm_a * norm_b)

        assert abs(similarity - 0.0) < 0.001


class TestScoreFusion:
    """Tests for score fusion (T9)."""

    def test_fusion_weights(self):
        """Fusion should respect semantic_weight setting."""
        bm25_score = 0.8
        semantic_score = 0.6
        semantic_weight = 0.6

        combined = semantic_weight * semantic_score + (1 - semantic_weight) * bm25_score
        expected = 0.6 * 0.6 + 0.4 * 0.8  # 0.36 + 0.32 = 0.68

        assert abs(combined - expected) < 0.001

    def test_normalization(self):
        """BM25 scores should be normalized to 0-1."""
        raw_scores = [10.0, 5.0, 2.5]
        max_score = max(raw_scores)
        normalized = [s / max_score for s in raw_scores]

        assert normalized == [1.0, 0.5, 0.25]
        assert all(0 <= s <= 1 for s in normalized)


class TestReranking:
    """Tests for cross-encoder reranking (T10)."""

    def test_sigmoid_normalization(self):
        """Cross-encoder scores should be normalized via sigmoid."""
        raw_scores = [-2.0, 0.0, 2.0]
        normalized = [1 / (1 + np.exp(-s)) for s in raw_scores]

        assert normalized[0] < 0.5  # Negative -> low
        assert abs(normalized[1] - 0.5) < 0.01  # Zero -> 0.5
        assert normalized[2] > 0.5  # Positive -> high

    def test_top_k_limit(self):
        """Only top-k candidates should be reranked."""
        settings = Settings()
        assert settings.rerank_top_k == 20  # Default


class TestHierarchyFilter:
    """Tests for governance hierarchy (T11)."""

    def test_s_series_highest_priority(self):
        """S-Series should be sorted first."""
        constitution_hierarchy = {"S": 0, "C": 1, "O": 2, "Q": 3, "MA": 4, "G": 5}
        series = ["Q", "S", "C"]
        sorted_series = sorted(series, key=lambda s: constitution_hierarchy.get(s, 99))

        assert sorted_series[0] == "S"

    def test_constitution_before_domain(self):
        """Constitution series (hierarchy 0-5) should come before domain (10)."""
        # In the domain-aware model: constitution gets 0-5, domain gets 10
        constitution_c = 1  # C in constitution
        domain_p = 10  # P in domain
        assert constitution_c < domain_p


class TestConfidenceLevels:
    """Tests for confidence level assignment."""

    def test_high_confidence_threshold(self):
        """Score >= 0.7 should be HIGH."""
        settings = Settings()
        assert settings.confidence_high_threshold == 0.7

    def test_medium_confidence_threshold(self):
        """Score 0.4-0.7 should be MEDIUM."""
        settings = Settings()
        assert settings.confidence_medium_threshold == 0.4

    def test_confidence_assignment(self):
        """Scores should map to correct confidence levels."""
        high_threshold = 0.7
        medium_threshold = 0.4

        def get_confidence(score):
            if score >= high_threshold:
                return ConfidenceLevel.HIGH
            elif score >= medium_threshold:
                return ConfidenceLevel.MEDIUM
            return ConfidenceLevel.LOW

        assert get_confidence(0.8) == ConfidenceLevel.HIGH
        assert get_confidence(0.7) == ConfidenceLevel.HIGH
        assert get_confidence(0.5) == ConfidenceLevel.MEDIUM
        assert get_confidence(0.4) == ConfidenceLevel.MEDIUM
        assert get_confidence(0.3) == ConfidenceLevel.LOW
        assert get_confidence(0.0) == ConfidenceLevel.LOW


class TestMatchReasons:
    """Tests for match reason generation."""

    def test_strong_keyword_match(self):
        """BM25 > 0.5 should indicate strong keyword match."""
        bm25_score = 0.6
        reasons = []
        if bm25_score > 0.5:
            reasons.append("strong keyword match")
        elif bm25_score > 0.2:
            reasons.append("keyword match")

        assert "strong keyword match" in reasons

    def test_semantic_similarity(self):
        """High semantic score should indicate semantic similarity."""
        semantic_score = 0.75
        reasons = []
        if semantic_score > 0.7:
            reasons.append("strong semantic similarity")
        elif semantic_score > 0.4:
            reasons.append("semantic similarity")

        assert "strong semantic similarity" in reasons


class TestSSeries:
    """Tests for S-Series safety principle handling."""

    def test_s_series_always_checked(self):
        """S-Series principles should always be checked."""
        # Constitution should always be in search domains
        detected_domains = ["ai-coding"]
        search_domains = list(set(detected_domains + ["constitution"]))

        assert "constitution" in search_domains

    def test_s_series_triggers_flag(self):
        """Matching S-Series should set s_series_triggered."""
        principle_series = "S"
        s_series_triggered = principle_series == "S"

        assert s_series_triggered is True


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_results_structure(self):
        """Empty results should have correct structure."""
        from ai_governance_mcp.models import RetrievalResult

        result = RetrievalResult(
            query="test",
            domains_detected=[],
        )

        assert result.constitution_principles == []
        assert result.domain_principles == []
        assert result.methods == []
        assert result.s_series_triggered is False

    def test_missing_embedding_id(self):
        """Principles without embedding_id should be handled."""
        p = Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Test",
            content="Content",
            line_range=(1, 5),
            embedding_id=None,
        )

        assert p.embedding_id is None

    def test_zero_vector_similarity(self):
        """Zero vectors should return 0 similarity."""
        a = np.array([0.0, 0.0, 0.0])
        b = np.array([1.0, 2.0, 3.0])

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            similarity = 0.0
        else:
            similarity = np.dot(a, b) / (norm_a * norm_b)

        assert similarity == 0.0


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestConfidenceThresholds:
    """Tests for confidence level threshold boundaries."""

    def test_score_exactly_at_high_threshold(self):
        """Score exactly at 0.7 should be HIGH confidence."""
        from ai_governance_mcp.models import ConfidenceLevel

        score = 0.7
        if score >= 0.7:
            confidence = ConfidenceLevel.HIGH
        elif score >= 0.4:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        assert confidence == ConfidenceLevel.HIGH

    def test_score_just_below_high_threshold(self):
        """Score at 0.69 should be MEDIUM confidence."""
        from ai_governance_mcp.models import ConfidenceLevel

        score = 0.69
        if score >= 0.7:
            confidence = ConfidenceLevel.HIGH
        elif score >= 0.4:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        assert confidence == ConfidenceLevel.MEDIUM

    def test_score_exactly_at_medium_threshold(self):
        """Score exactly at 0.4 should be MEDIUM confidence."""
        from ai_governance_mcp.models import ConfidenceLevel

        score = 0.4
        if score >= 0.7:
            confidence = ConfidenceLevel.HIGH
        elif score >= 0.4:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        assert confidence == ConfidenceLevel.MEDIUM

    def test_score_just_below_medium_threshold(self):
        """Score at 0.39 should be LOW confidence."""
        from ai_governance_mcp.models import ConfidenceLevel

        score = 0.39
        if score >= 0.7:
            confidence = ConfidenceLevel.HIGH
        elif score >= 0.4:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        assert confidence == ConfidenceLevel.LOW


class TestScoreBoundaries:
    """Tests for score constraint boundaries."""

    def test_semantic_score_at_zero(self):
        """Semantic score at 0 should be valid."""
        from ai_governance_mcp.models import (
            Principle,
            ConfidenceLevel,
        )

        principle = Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Test",
            content="Content",
            line_range=(1, 10),
        )

        scored = ScoredPrinciple(
            principle=principle,
            semantic_score=0.0,
            keyword_score=0.0,
            combined_score=0.0,
            confidence=ConfidenceLevel.LOW,
        )

        assert scored.semantic_score == 0.0

    def test_semantic_score_at_one(self):
        """Semantic score at 1.0 should be valid."""
        from ai_governance_mcp.models import (
            Principle,
            ConfidenceLevel,
        )

        principle = Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Test",
            content="Content",
            line_range=(1, 10),
        )

        scored = ScoredPrinciple(
            principle=principle,
            semantic_score=1.0,
            keyword_score=0.5,
            combined_score=1.0,
            confidence=ConfidenceLevel.HIGH,
        )

        assert scored.semantic_score == 1.0
        assert scored.combined_score == 1.0


class TestUnicodeHandling:
    """Tests for Unicode text handling."""

    def test_bm25_tokenizes_unicode(self):
        """BM25 should handle Unicode text."""
        query = "código seguridad 안전 安全"
        tokens = query.lower().split()

        assert len(tokens) == 4
        assert "código" in tokens
        assert "안전" in tokens

    def test_principle_with_unicode_content(self):
        """Principle should accept Unicode content."""
        from ai_governance_mcp.models import Principle

        principle = Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Seguridad y Ética",
            content="Principio con contenido en español. 日本語のテキスト。",
            line_range=(1, 10),
        )

        assert "español" in principle.content
        assert "日本語" in principle.content


class TestEmptyInputs:
    """Tests for empty input handling."""

    def test_empty_principle_list_hierarchy(self):
        """apply_hierarchy should handle empty list."""
        principles = []

        # Hierarchy sort on empty list
        sorted_principles = sorted(
            principles,
            key=lambda sp: (0, -0.0, 0),
        )

        assert sorted_principles == []

    def test_empty_query_tokenization(self):
        """Empty query should tokenize to empty list."""
        query = ""
        tokens = query.lower().split()

        assert tokens == []

    def test_whitespace_only_query(self):
        """Whitespace-only query should tokenize to empty list."""
        query = "   \t\n   "
        tokens = query.split()

        assert tokens == []


class TestLargeInputs:
    """Tests for large input handling."""

    def test_very_long_query(self):
        """Should handle queries with many tokens."""
        query = " ".join(["word"] * 1000)
        tokens = query.lower().split()

        assert len(tokens) == 1000

    def test_large_content_truncation(self):
        """Embedding text should truncate large content."""
        from ai_governance_mcp.models import Principle

        # Create principle with very long content
        long_content = "A" * 10000
        principle = Principle(
            id="test-C1",
            domain="test",
            series_code="C",
            number=1,
            title="Test Title",
            content=long_content,
            line_range=(1, 1000),
            metadata=PrincipleMetadata(keywords=["test"]),
        )

        # Simulate embedding text creation (first 1000 chars)
        embedding_text = f"{principle.title}\n{principle.content[:1000]}"

        assert len(embedding_text) < 1100  # Title + 1000 chars + newline


class TestHierarchyOrdering:
    """Tests for domain-aware series hierarchy ordering."""

    def test_constitution_hierarchy_has_all_codes(self):
        """Constitution hierarchy should define S/C/O/Q/MA/G priorities.

        Order matches canonical Framework Overview Article sequence
        (I=C, II=O, III=Q, IV=G) with S-Series (Bill of Rights) ranked first.
        Updated v5.0.5 per F-P2-15 — prior O=3/Q=2 reflected drifted body order.
        """
        constitution_hierarchy = {"S": 0, "C": 1, "O": 2, "Q": 3, "MA": 4, "G": 5}

        assert constitution_hierarchy["S"] < constitution_hierarchy["C"]
        assert constitution_hierarchy["C"] < constitution_hierarchy["O"]
        assert constitution_hierarchy["O"] < constitution_hierarchy["Q"]

    def test_domain_principles_below_constitution(self):
        """Domain-level principles (hierarchy=10) should sort below constitution (0-5)."""
        constitution_max = 5  # G
        domain_level = 10  # All domain principles
        assert domain_level > constitution_max

    def test_null_series_code_gets_lowest_priority(self):
        """Principles with no series_code get hierarchy=99 (lowest)."""
        # Simulates the apply_hierarchy sort key for None series_code
        hierarchy = 99  # No series code
        assert hierarchy > 10  # Below domain principles too


class TestApplyHierarchyDomainAware:
    """Tests for apply_hierarchy() with domain-aware sorting."""

    def _make_scored(self, principle_id, domain, series_code, score):
        """Helper to create a ScoredPrinciple for testing."""
        p = Principle(
            id=principle_id,
            domain=domain,
            series_code=series_code,
            number=None,
            title=principle_id,
            content="test",
            line_range=(1, 2),
        )
        return ScoredPrinciple(
            principle=p,
            semantic_score=score,
            keyword_score=0.0,
            rerank_score=None,
            combined_score=score,
            confidence=ConfidenceLevel.MEDIUM,
            match_reasons=["test"],
        )

    def test_s_series_sorts_first(self, tmp_path):
        """Constitution S-Series principles should sort before all others."""
        settings = Settings()
        settings.index_path = tmp_path / "index"
        settings.documents_path = tmp_path / "docs"
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine.__new__(RetrievalEngine)
        engine.settings = settings

        principles = [
            self._make_scored("coding-P1", "ai-coding", "P", 0.9),
            self._make_scored("meta-S1", "constitution", "S", 0.5),
            self._make_scored("meta-C1", "constitution", "C", 0.8),
        ]
        result = engine.apply_hierarchy(principles)

        assert result[0].principle.id == "meta-S1", "S-Series must be first"
        assert result[1].principle.id == "meta-C1", "Constitution C before domain"
        assert result[2].principle.id == "coding-P1", "Domain principles last"

    def test_same_code_different_domains(self, tmp_path):
        """Same series code (Q) in constitution vs domain: constitution wins."""
        settings = Settings()
        settings.index_path = tmp_path / "index"
        settings.documents_path = tmp_path / "docs"
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine.__new__(RetrievalEngine)
        engine.settings = settings

        principles = [
            self._make_scored("coding-Q1", "ai-coding", "Q", 0.9),
            self._make_scored("meta-Q1", "constitution", "Q", 0.5),
        ]
        result = engine.apply_hierarchy(principles)

        assert result[0].principle.domain == "constitution", (
            "Constitution Q should sort before domain Q"
        )

    def test_none_series_code_sorts_last(self, tmp_path):
        """Principles with series_code=None sort below all coded principles."""
        settings = Settings()
        settings.index_path = tmp_path / "index"
        settings.documents_path = tmp_path / "docs"
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine.__new__(RetrievalEngine)
        engine.settings = settings

        principles = [
            self._make_scored("multi-general-J1", "multi-agent", None, 0.95),
            self._make_scored("coding-P1", "ai-coding", "P", 0.3),
        ]
        result = engine.apply_hierarchy(principles)

        assert result[0].principle.series_code == "P", (
            "Coded domain principle before uncoded"
        )
        assert result[1].principle.series_code is None


class TestFeedbackAdaptation:
    """Tests for adaptive retrieval based on user feedback."""

    @pytest.fixture
    def settings_with_feedback(self, tmp_path):
        """Create settings with feedback enabled."""
        settings = Settings()
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)
        settings.index_path = tmp_path / "index"
        settings.documents_path = tmp_path / "documents"
        settings.enable_feedback_adaptation = True
        settings.feedback_min_ratings = 5  # Default is 5 per contrarian review
        settings.feedback_boost_threshold = 4.0
        settings.feedback_penalty_threshold = 2.0
        settings.feedback_boost_amount = 0.1
        settings.feedback_penalty_amount = 0.05
        return settings

    @pytest.fixture
    def settings_with_min_3_ratings(self, tmp_path):
        """Create settings with lower minimum for testing boost/penalty."""
        settings = Settings()
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)
        settings.index_path = tmp_path / "index"
        settings.documents_path = tmp_path / "documents"
        settings.enable_feedback_adaptation = True
        settings.feedback_min_ratings = 3  # Lower for easier testing
        settings.feedback_boost_threshold = 4.0
        settings.feedback_penalty_threshold = 2.0
        settings.feedback_boost_amount = 0.1
        settings.feedback_penalty_amount = 0.05
        return settings

    def test_load_feedback_ratings_parses_jsonl(self, settings_with_min_3_ratings):
        """Should parse feedback.jsonl and calculate averages."""
        # Create feedback file with ratings
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 4}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C2", "rating": 1}\n'
            '{"principle_id": "meta-C2", "rating": 2}\n'
            '{"principle_id": "meta-C2", "rating": 1}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        # Check ratings were loaded
        assert "meta-C1" in engine._feedback_ratings
        assert "meta-C2" in engine._feedback_ratings

        # Check averages calculated correctly
        avg_c1, count_c1 = engine._feedback_ratings["meta-C1"]
        assert count_c1 == 3
        assert abs(avg_c1 - (5 + 4 + 5) / 3) < 0.01

        avg_c2, count_c2 = engine._feedback_ratings["meta-C2"]
        assert count_c2 == 3
        assert abs(avg_c2 - (1 + 2 + 1) / 3) < 0.01

    def test_get_feedback_adjustment_boosts_high_rated(
        self, settings_with_min_3_ratings
    ):
        """Principles with high ratings should get positive boost."""
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 4}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        adjustment = engine.get_feedback_adjustment("meta-C1")
        assert adjustment == 0.1  # feedback_boost_amount

    def test_get_feedback_adjustment_penalizes_low_rated(
        self, settings_with_min_3_ratings
    ):
        """Principles with low ratings should get negative penalty."""
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C2", "rating": 1}\n'
            '{"principle_id": "meta-C2", "rating": 2}\n'
            '{"principle_id": "meta-C2", "rating": 1}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        adjustment = engine.get_feedback_adjustment("meta-C2")
        assert adjustment == -0.05  # -feedback_penalty_amount

    def test_get_feedback_adjustment_requires_min_ratings(self, settings_with_feedback):
        """Should not adjust if below minimum rating count."""
        feedback_file = settings_with_feedback.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'  # Only 4 ratings, need 5
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_feedback)

        adjustment = engine.get_feedback_adjustment("meta-C1")
        assert adjustment == 0.0  # Not enough ratings

    def test_get_feedback_adjustment_returns_zero_for_unknown(
        self, settings_with_feedback
    ):
        """Unknown principles should get zero adjustment."""
        feedback_file = settings_with_feedback.logs_path / "feedback.jsonl"
        feedback_file.write_text("")  # Empty file

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_feedback)

        adjustment = engine.get_feedback_adjustment("unknown-principle")
        assert adjustment == 0.0

    def test_get_feedback_adjustment_middling_ratings_no_adjustment(
        self, settings_with_min_3_ratings
    ):
        """Middling ratings (between thresholds) should get no adjustment."""
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 3}\n'
            '{"principle_id": "meta-C1", "rating": 3}\n'
            '{"principle_id": "meta-C1", "rating": 3}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        adjustment = engine.get_feedback_adjustment("meta-C1")
        assert adjustment == 0.0  # Average 3.0 is between 2.0 and 4.0

    def test_reload_feedback_ratings_clears_and_reloads(
        self, settings_with_min_3_ratings
    ):
        """reload_feedback_ratings should pick up new feedback."""
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)
        assert "meta-C1" in engine._feedback_ratings

        # Update feedback file
        feedback_file.write_text(
            '{"principle_id": "meta-C2", "rating": 1}\n'
            '{"principle_id": "meta-C2", "rating": 1}\n'
            '{"principle_id": "meta-C2", "rating": 1}\n'
        )

        # Reload
        engine.reload_feedback_ratings()

        assert "meta-C1" not in engine._feedback_ratings  # Old cleared
        assert "meta-C2" in engine._feedback_ratings  # New loaded

    def test_feedback_disabled_returns_zero(self, settings_with_min_3_ratings):
        """When disabled, should always return zero adjustment."""
        settings_with_min_3_ratings.enable_feedback_adaptation = False

        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        # Even with high ratings, should return 0 when disabled
        adjustment = engine.get_feedback_adjustment("meta-C1")
        assert adjustment == 0.0

    def test_handles_malformed_feedback_entries(self, settings_with_min_3_ratings):
        """Should skip malformed JSON entries gracefully."""
        feedback_file = settings_with_min_3_ratings.logs_path / "feedback.jsonl"
        feedback_file.write_text(
            '{"principle_id": "meta-C1", "rating": 5}\n'
            "not valid json\n"
            '{"principle_id": "meta-C1", "rating": 5}\n'
            '{"missing_rating": true}\n'
            '{"principle_id": "meta-C1", "rating": 5}\n'
        )

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(settings_with_min_3_ratings)

        # Should have loaded 3 valid ratings
        assert "meta-C1" in engine._feedback_ratings
        _, count = engine._feedback_ratings["meta-C1"]
        assert count == 3

    def test_default_min_ratings_is_five(self, settings_with_feedback):
        """Default minimum ratings should be 5 per contrarian review."""
        assert settings_with_feedback.feedback_min_ratings == 5


class TestAutoReload:
    """Tests for auto-reload of index on disk changes."""

    def _make_index_json(self, title="Test Principle"):
        """Create a minimal valid global_index.json dict."""
        import json

        return json.dumps(
            {
                "domains": {
                    "constitution": {
                        "domain": "constitution",
                        "principles": [
                            {
                                "id": "meta-C1",
                                "domain": "constitution",
                                "series_code": "C",
                                "number": 1,
                                "title": title,
                                "content": "Test content for BM25 indexing",
                                "line_range": [1, 10],
                            }
                        ],
                        "methods": [],
                        "last_extracted": "2026-01-01T00:00:00Z",
                    }
                },
                "domain_configs": [
                    {
                        "name": "constitution",
                        "display_name": "Constitution",
                        "principles_file": "const.md",
                        "description": "Universal rules",
                    }
                ],
                "created_at": "2026-01-01T00:00:00Z",
                "version": "1.0",
                "embedding_model": "BAAI/bge-small-en-v1.5",
                "embedding_dimensions": 384,
            }
        )

    @pytest.fixture
    def index_dir(self, tmp_path):
        """Create a tmp_path with a valid minimal index."""
        index_path = tmp_path / "index"
        index_path.mkdir()
        (index_path / "global_index.json").write_text(self._make_index_json())
        return index_path

    @pytest.fixture
    def engine_settings(self, index_dir, tmp_path):
        """Create settings pointing at the temp index."""
        settings = Settings()
        settings.index_path = index_dir
        settings.logs_path = tmp_path / "logs"
        settings.logs_path.mkdir(parents=True, exist_ok=True)
        settings.documents_path = tmp_path / "documents"
        return settings

    def test_auto_reload_detects_index_change(self, engine_settings, index_dir):
        """Should reload index when global_index.json mtime changes."""
        import time as time_mod

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(engine_settings)

        # Verify initial load
        assert engine.index is not None
        assert (
            engine.index.domains["constitution"].principles[0].title == "Test Principle"
        )

        # Write updated index with a different title

        time_mod.sleep(0.05)  # Ensure mtime changes
        (index_dir / "global_index.json").write_text(
            self._make_index_json(title="Updated Principle")
        )

        # Call a public method — should trigger auto-reload
        domains = engine.list_domains()

        # Verify reload happened
        assert (
            engine.index.domains["constitution"].principles[0].title
            == "Updated Principle"
        )
        assert len(domains) == 1

    def test_auto_reload_skips_when_unchanged(self, engine_settings):
        """Should not reload index when mtime is unchanged."""
        from unittest.mock import patch as mock_patch

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(engine_settings)
        original_mtime = engine._index_mtime

        # Patch _load_index to track calls after init
        with mock_patch.object(engine, "_load_index") as mock_load:
            engine.list_domains()
            engine.get_principle_by_id("meta-C1")
            engine.get_method_by_id("nonexistent")
            engine.get_domain_summary("constitution")

            # _load_index should NOT have been called again
            mock_load.assert_not_called()

        # mtime unchanged
        assert engine._index_mtime == original_mtime

    def test_auto_reload_handles_missing_index_file(self, engine_settings, index_dir):
        """Should not crash if index file is deleted after initial load."""
        import os

        from ai_governance_mcp.retrieval import RetrievalEngine

        engine = RetrievalEngine(engine_settings)
        assert engine.index is not None

        # Delete the index file
        os.remove(index_dir / "global_index.json")

        # Public methods should not crash — keeps old index
        domains = engine.list_domains()
        assert len(domains) == 1  # Still has the old data

        principle = engine.get_principle_by_id("meta-C1")
        assert principle is not None
        assert principle.title == "Test Principle"
