"""Tests for configuration management (T19).

Per specification v4: Validates settings and configuration loading.
"""

import os
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.config import (
    Settings,
    load_settings,
    load_domains_registry,
    setup_logging,
    ensure_directories,
    get_settings,
    _default_domains,
)


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Should have sensible defaults."""
        settings = Settings()
        assert settings.log_level == "INFO"
        assert settings.embedding_model == "all-MiniLM-L6-v2"
        assert settings.embedding_dimensions == 384
        assert settings.semantic_weight == 0.6
        assert settings.max_results == 10

    def test_embedding_settings(self):
        """Should have embedding configuration."""
        settings = Settings()
        assert "MiniLM" in settings.embedding_model
        assert settings.embedding_dimensions == 384
        assert settings.rerank_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert settings.rerank_top_k == 20

    def test_retrieval_thresholds(self):
        """Should have retrieval thresholds."""
        settings = Settings()
        assert settings.min_score_threshold == 0.3
        assert settings.confidence_high_threshold == 0.7
        assert settings.confidence_medium_threshold == 0.4
        assert settings.domain_similarity_threshold == 0.5

    def test_performance_target(self):
        """Should have latency target."""
        settings = Settings()
        assert settings.latency_target_ms == 100.0

    def test_semantic_weight_constraints(self):
        """Semantic weight should be 0-1."""
        # Valid values
        settings = Settings(semantic_weight=0.0)
        assert settings.semantic_weight == 0.0

        settings = Settings(semantic_weight=1.0)
        assert settings.semantic_weight == 1.0

    def test_paths_are_path_objects(self):
        """Paths should be Path objects."""
        settings = Settings()
        assert isinstance(settings.documents_path, Path)
        assert isinstance(settings.index_path, Path)
        assert isinstance(settings.logs_path, Path)


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_env_prefix(self):
        """Settings should use AI_GOVERNANCE_ prefix."""
        settings = Settings()
        assert settings.model_config.get("env_prefix") == "AI_GOVERNANCE_"


class TestDefaultDomains:
    """Test default domain configurations."""

    def test_three_default_domains(self):
        """Should have constitution, ai-coding, multi-agent."""
        domains = _default_domains()
        assert len(domains) == 3
        names = [d.name for d in domains]
        assert "constitution" in names
        assert "ai-coding" in names
        assert "multi-agent" in names

    def test_constitution_highest_priority(self):
        """Constitution should have priority 0."""
        domains = _default_domains()
        constitution = next(d for d in domains if d.name == "constitution")
        assert constitution.priority == 0

    def test_domains_have_descriptions(self):
        """All domains should have descriptions for semantic routing."""
        domains = _default_domains()
        for domain in domains:
            assert domain.description != ""
            assert len(domain.description) > 50

    def test_domain_files_specified(self):
        """Each domain should have principles file."""
        domains = _default_domains()
        for domain in domains:
            assert domain.principles_file.endswith(".md")


class TestLogging:
    """Test logging configuration."""

    def test_setup_logging_returns_logger(self):
        """Should return a logger instance."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "ai_governance_mcp"

    def test_setup_logging_level(self):
        """Should set log level correctly."""
        import logging
        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG

        logger = setup_logging("WARNING")
        assert logger.level == logging.WARNING


class TestLoadSettings:
    """Test settings loading functions."""

    def test_load_settings(self):
        """Should load settings successfully."""
        settings = load_settings()
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_get_settings_caches(self):
        """get_settings should cache instance."""
        # Clear any cached instance
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # Same instance


class TestLoadDomainsRegistry:
    """Test domain registry loading."""

    def test_load_returns_list(self):
        """Should return list of DomainConfig."""
        settings = Settings()
        domains = load_domains_registry(settings)
        assert isinstance(domains, list)
        assert len(domains) >= 3  # Default domains


class TestEnsureDirectories:
    """Test directory creation."""

    def test_creates_directories(self, tmp_path):
        """Should create required directories."""
        settings = Settings()
        settings.documents_path = tmp_path / "docs"
        settings.index_path = tmp_path / "index"
        settings.logs_path = tmp_path / "logs"

        ensure_directories(settings)

        assert settings.documents_path.exists()
        assert settings.index_path.exists()
        assert settings.logs_path.exists()
