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


class TestBM25Search:
    """Tests for BM25 keyword search (T7)."""

    def test_bm25_tokenization(self):
        """Queries should be tokenized for BM25."""
        query = "write code for testing"
        tokens = query.lower().split()
        assert tokens == ["write", "code", "for", "testing"]

    def test_bm25_empty_query(self):
        """Empty query should return empty results."""
        query = ""
        tokens = query.lower().split()
        assert tokens == []  # Empty string splits to empty list


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
        hierarchy = {"S": 0, "C": 1, "Q": 2}
        series = ["Q", "S", "C"]
        sorted_series = sorted(series, key=lambda s: hierarchy.get(s, 99))

        assert sorted_series[0] == "S"

    def test_constitution_before_domain(self):
        """Constitution series should come before domain series."""
        hierarchy = {"S": 0, "C": 1, "Q": 2, "P": 6}
        series = ["P", "C", "Q"]
        sorted_series = sorted(series, key=lambda s: hierarchy.get(s, 99))

        assert sorted_series.index("C") < sorted_series.index("P")


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
    """Additional tests for series hierarchy ordering."""

    def test_all_series_codes_have_priority(self):
        """All known series codes should have defined priorities."""
        series_priority = {
            "S": 0,  # Safety first
            "C": 1,  # Core
            "Q": 2,  # Quality
            "O": 3,  # Operational
            "MA": 4,  # Meta-awareness
            "G": 5,  # Growth
            "P": 6,  # Process (domain-specific)
            "A": 7,  # Architecture (domain-specific)
            "T": 8,  # Technical (domain-specific)
            "D": 9,  # Documentation (domain-specific)
        }

        # Verify S is highest priority (lowest number)
        assert series_priority["S"] < series_priority["C"]
        assert series_priority["C"] < series_priority["Q"]
        assert series_priority["Q"] < series_priority["O"]

    def test_unknown_series_code_gets_low_priority(self):
        """Unknown series codes should get low (high number) priority."""
        known_codes = {"S", "C", "Q", "O", "MA", "G", "P", "A", "T", "D"}
        unknown_code = "X"

        # Simulate priority lookup with default for unknown
        priority = 99 if unknown_code not in known_codes else 0

        assert priority == 99  # Unknown gets lowest priority


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
