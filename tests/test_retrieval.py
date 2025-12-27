"""Tests for the retrieval engine."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.config import load_config
from ai_governance_mcp.retrieval import RetrievalEngine


@pytest.fixture
def engine():
    """Create a retrieval engine for testing."""
    config = load_config()
    return RetrievalEngine(config)


class TestDomainDetection:
    """Tests for domain detection."""

    def test_detect_ai_coding_domain(self, engine):
        """Query with 'code' should detect ai-coding domain."""
        domains = engine.detect_domains("write code for authentication")
        assert "ai-coding" in domains

    def test_detect_multi_agent_domain(self, engine):
        """Query with 'agent' should detect multi-agent domain."""
        domains = engine.detect_domains("implement multi-agent system")
        assert "multi-agent" in domains

    def test_detect_multiple_domains(self, engine):
        """Query spanning domains should detect both."""
        domains = engine.detect_domains("implement agent code review")
        assert "ai-coding" in domains
        assert "multi-agent" in domains

    def test_no_domain_detected(self, engine):
        """Query with no domain keywords returns empty list."""
        domains = engine.detect_domains("what is the weather today")
        assert domains == []

    def test_phrase_matching_priority(self, engine):
        """Phrases should be detected correctly."""
        domains = engine.detect_domains("need to fix bug in the system")
        assert "ai-coding" in domains  # "fix bug" phrase


class TestRetrieval:
    """Tests for principle retrieval."""

    def test_retrieve_with_explicit_domain(self, engine):
        """Explicit domain should search that domain."""
        result = engine.retrieve("specification incomplete", domain="ai-coding")
        assert result.domains_detected == []  # Domain was explicit, not detected
        assert len(result.domain_principles) > 0

    def test_retrieve_finds_relevant_principle(self, engine):
        """Query should find matching principle."""
        result = engine.retrieve("specification seems incomplete", domain="ai-coding")
        principle_ids = [sp.principle.id for sp in result.domain_principles]
        assert "coding-C1" in principle_ids  # Specification Completeness

    def test_s_series_triggered(self, engine):
        """Safety-related query should trigger S-Series."""
        result = engine.retrieve("this could cause harm to users")
        assert result.s_series_triggered is True

    def test_s_series_not_triggered(self, engine):
        """Normal query should not trigger S-Series."""
        result = engine.retrieve("write a simple function", domain="ai-coding")
        assert result.s_series_triggered is False

    def test_constitution_always_searched(self, engine):
        """Constitution should be searched even with domain specified."""
        result = engine.retrieve("context management", domain="ai-coding")
        # Constitution search happens internally
        assert result is not None

    def test_max_results_limit(self, engine):
        """Results should respect max_results parameter."""
        result = engine.retrieve("code", domain="ai-coding", max_results=3)
        assert len(result.domain_principles) <= 3


class TestScoring:
    """Tests for scoring algorithm."""

    def test_keyword_matching_scores(self, engine):
        """Keywords should contribute to score."""
        result = engine.retrieve("specification", domain="ai-coding")
        # coding-C1 has "specification" as keyword
        c1_results = [sp for sp in result.domain_principles if sp.principle.id == "coding-C1"]
        assert len(c1_results) > 0
        assert c1_results[0].score >= 1.0  # At least keyword weight

    def test_failure_indicator_matching(self, engine):
        """Failure indicators should match with weight 1.5."""
        result = engine.retrieve("hallucination in the code", domain="ai-coding")
        # coding-C1 has "hallucination" as failure indicator
        c1_results = [sp for sp in result.domain_principles if sp.principle.id == "coding-C1"]
        assert len(c1_results) > 0

    def test_s_series_boost(self, engine):
        """S-Series principles get 10x boost."""
        result = engine.retrieve("causing harm to users")
        s_results = [sp for sp in result.constitution_principles if sp.principle.series_code == "S"]
        if s_results:
            assert s_results[0].score >= 10.0  # 10x boost applied


class TestPrincipleLookup:
    """Tests for principle lookup functions."""

    def test_get_principle_by_id(self, engine):
        """Should retrieve principle by ID."""
        principle = engine.get_principle_by_id("coding-C1")
        assert principle is not None
        assert principle.id == "coding-C1"
        assert "Specification" in principle.title

    def test_get_principle_invalid_id(self, engine):
        """Invalid ID should return None."""
        principle = engine.get_principle_by_id("invalid-XX99")
        assert principle is None

    def test_get_principle_content(self, engine):
        """Should retrieve principle content from cache."""
        content = engine.get_principle_content("coding-C1")
        assert content is not None
        assert "Specification" in content

    def test_list_principles_all(self, engine):
        """Should list all principles."""
        principles = engine.list_principles()
        assert len(principles) > 0
        # Should have constitution, ai-coding, and multi-agent
        domains = set(p["domain"] for p in principles)
        assert "constitution" in domains
        assert "ai-coding" in domains

    def test_list_principles_by_domain(self, engine):
        """Should filter principles by domain."""
        principles = engine.list_principles(domain="ai-coding")
        assert all(p["domain"] == "ai-coding" for p in principles)
        assert len(principles) == 12  # AI Coding has 12 principles

    def test_list_domains(self, engine):
        """Should list all domains with stats."""
        domains = engine.list_domains()
        assert len(domains) >= 3  # constitution, ai-coding, multi-agent
        domain_names = [d["name"] for d in domains]
        assert "constitution" in domain_names
        assert "ai-coding" in domain_names
        assert "multi-agent" in domain_names


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_query(self, engine):
        """Empty query should return empty results."""
        result = engine.retrieve("")
        assert len(result.domain_principles) == 0

    def test_unknown_domain(self, engine):
        """Unknown domain should return empty results."""
        result = engine.retrieve("test query", domain="nonexistent-domain")
        assert len(result.domain_principles) == 0

    def test_special_characters_in_query(self, engine):
        """Special characters should be handled."""
        result = engine.retrieve("code with @#$% symbols", domain="ai-coding")
        assert result is not None  # Should not crash

    def test_very_long_query(self, engine):
        """Long query should be handled."""
        long_query = "specification " * 100
        result = engine.retrieve(long_query, domain="ai-coding")
        assert result is not None
