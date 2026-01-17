"""Shared pytest fixtures for AI Governance MCP Server tests.

Per governance framework Q3 (Testing Integration): Fixtures support test isolation
and reproducibility across unit, integration, and behavior tests.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.models import (
    ConfidenceLevel,
    DomainConfig,
    DomainIndex,
    ErrorResponse,
    Feedback,
    GlobalIndex,
    Method,
    Metrics,
    Principle,
    PrincipleMetadata,
    QueryLog,
    RetrievalResult,
    ScoredMethod,
    ScoredPrinciple,
)
from ai_governance_mcp.config import Settings


# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def test_settings(temp_dir):
    """Settings pointing to temporary directories for isolated tests."""
    settings = Settings()
    # Override paths to use temp directories
    settings.documents_path = temp_dir / "documents"
    settings.index_path = temp_dir / "index"
    settings.logs_path = temp_dir / "logs"

    # Create directories
    settings.documents_path.mkdir(parents=True)
    settings.index_path.mkdir(parents=True)
    settings.logs_path.mkdir(parents=True)

    return settings


# =============================================================================
# Model Fixtures - Principles
# =============================================================================


@pytest.fixture
def sample_principle():
    """Minimal valid Principle for unit tests."""
    return Principle(
        id="meta-C1",
        domain="constitution",
        series_code="C",
        number=1,
        title="Test Principle",
        content="This is test content for the principle. It contains enough text to be meaningful for testing purposes.",
        line_range=(1, 10),
        metadata=PrincipleMetadata(
            keywords=["test", "sample", "principle"],
            synonyms=["example"],
            trigger_phrases=["test scenario"],
            failure_indicators=["test failure"],
            aliases=["C1"],
        ),
        embedding_id=0,
    )


@pytest.fixture
def sample_s_series_principle():
    """S-Series safety principle for testing priority and triggering."""
    return Principle(
        id="meta-S1",
        domain="constitution",
        series_code="S",
        number=1,
        title="Safety First",
        content="Safety content that should always be prioritized. S-Series principles take precedence over all other series.",
        line_range=(1, 5),
        metadata=PrincipleMetadata(
            keywords=["safety", "priority", "harm"],
            trigger_phrases=["safety concern"],
            failure_indicators=["safety violation"],
        ),
        embedding_id=1,
    )


@pytest.fixture
def sample_quality_principle():
    """Q-Series quality principle for testing hierarchy."""
    return Principle(
        id="meta-Q1",
        domain="constitution",
        series_code="Q",
        number=1,
        title="Quality Standards",
        content="Quality standards for verification and testing.",
        line_range=(20, 30),
        metadata=PrincipleMetadata(keywords=["quality", "testing"]),
        embedding_id=2,
    )


@pytest.fixture
def sample_coding_principle():
    """Domain-specific principle for ai-coding domain."""
    return Principle(
        id="coding-C1",
        domain="ai-coding",
        series_code="C",
        number=1,
        title="Code Quality",
        content="Maintain high code quality standards in all implementations.",
        line_range=(10, 20),
        metadata=PrincipleMetadata(keywords=["code", "quality", "implementation"]),
        embedding_id=3,
    )


# =============================================================================
# Model Fixtures - Methods
# =============================================================================


@pytest.fixture
def sample_method():
    """Minimal valid Method for unit tests."""
    return Method(
        id="coding-M1",
        domain="ai-coding",
        title="Cold Start Kit",
        content="Method content describing the cold start procedure for new projects.",
        line_range=(100, 150),
        keywords=["cold", "start", "initialization"],
        embedding_id=10,
    )


@pytest.fixture
def sample_method_2():
    """Second method for testing multiple methods."""
    return Method(
        id="coding-M2",
        domain="ai-coding",
        title="Gate Validation",
        content="Procedure for validating phase transition gates.",
        line_range=(160, 200),
        keywords=["gate", "validation", "phase"],
        embedding_id=11,
    )


# =============================================================================
# Model Fixtures - Domain Configuration
# =============================================================================


@pytest.fixture
def sample_domain_config():
    """Minimal DomainConfig for constitution domain."""
    return DomainConfig(
        name="constitution",
        display_name="Constitution",
        principles_file="test-principles.md",
        methods_file=None,
        description="Universal behavioral rules for AI interaction.",
        priority=0,
        embedding_id=0,
    )


@pytest.fixture
def sample_coding_domain_config():
    """DomainConfig for ai-coding domain."""
    return DomainConfig(
        name="ai-coding",
        display_name="AI Coding",
        principles_file="test-coding-principles.md",
        methods_file="test-coding-methods.md",
        description="Software development with AI assistance.",
        priority=10,
        embedding_id=1,
    )


# =============================================================================
# Model Fixtures - Index Structures
# =============================================================================


@pytest.fixture
def sample_domain_index(
    sample_principle, sample_s_series_principle, sample_quality_principle
):
    """DomainIndex for constitution domain with multiple principles."""
    return DomainIndex(
        domain="constitution",
        principles=[
            sample_principle,
            sample_s_series_principle,
            sample_quality_principle,
        ],
        methods=[],
        last_extracted="2025-01-01T00:00:00Z",
        version="1.0",
    )


@pytest.fixture
def sample_coding_domain_index(sample_coding_principle, sample_method, sample_method_2):
    """DomainIndex for ai-coding domain with principles and methods."""
    return DomainIndex(
        domain="ai-coding",
        principles=[sample_coding_principle],
        methods=[sample_method, sample_method_2],
        last_extracted="2025-01-01T00:00:00Z",
        version="1.0",
    )


@pytest.fixture
def sample_global_index(
    sample_domain_index,
    sample_coding_domain_index,
    sample_domain_config,
    sample_coding_domain_config,
):
    """GlobalIndex with two domains for integration tests."""
    return GlobalIndex(
        domains={
            "constitution": sample_domain_index,
            "ai-coding": sample_coding_domain_index,
        },
        domain_configs=[sample_domain_config, sample_coding_domain_config],
        created_at="2025-01-01T00:00:00Z",
        version="1.0",
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_dimensions=384,
    )


# =============================================================================
# Model Fixtures - Scored Results
# =============================================================================


@pytest.fixture
def scored_principle(sample_principle):
    """ScoredPrinciple with realistic scores for testing."""
    return ScoredPrinciple(
        principle=sample_principle,
        semantic_score=0.75,
        keyword_score=0.60,
        combined_score=0.69,
        rerank_score=0.72,
        confidence=ConfidenceLevel.MEDIUM,
        match_reasons=["strong semantic similarity", "keyword match: test"],
    )


@pytest.fixture
def scored_s_series(sample_s_series_principle):
    """Scored S-Series principle with high confidence."""
    return ScoredPrinciple(
        principle=sample_s_series_principle,
        semantic_score=0.85,
        keyword_score=0.70,
        combined_score=0.79,
        rerank_score=0.82,
        confidence=ConfidenceLevel.HIGH,
        match_reasons=["safety concern detected"],
    )


@pytest.fixture
def scored_method(sample_method):
    """ScoredMethod for testing method retrieval."""
    return ScoredMethod(
        method=sample_method,
        semantic_score=0.65,
        keyword_score=0.55,
        combined_score=0.61,
        confidence=ConfidenceLevel.MEDIUM,
    )


@pytest.fixture
def sample_retrieval_result(scored_principle, scored_s_series, scored_method):
    """Complete RetrievalResult for testing formatters and handlers."""
    return RetrievalResult(
        query="test query for governance",
        domains_detected=["constitution", "ai-coding"],
        domain_scores={"constitution": 0.85, "ai-coding": 0.72},
        constitution_principles=[scored_s_series, scored_principle],
        domain_principles=[],
        methods=[scored_method],
        s_series_triggered=True,
        retrieval_time_ms=45.5,
    )


# =============================================================================
# Embedding Fixtures (Mocked)
# =============================================================================


@pytest.fixture
def mock_embeddings():
    """Mock content embeddings array (5 items, 384 dims).

    Use deterministic random seed for reproducibility.
    """
    np.random.seed(42)
    return np.random.rand(5, 384).astype(np.float32)


@pytest.fixture
def mock_domain_embeddings():
    """Mock domain embeddings (3 domains, 384 dims)."""
    np.random.seed(43)
    return np.random.rand(3, 384).astype(np.float32)


@pytest.fixture
def mock_query_embedding():
    """Mock embedding for a query (384 dims)."""
    np.random.seed(44)
    return np.random.rand(384).astype(np.float32)


@pytest.fixture
def mock_embedder():
    """Mocked SentenceTransformer that returns consistent embeddings."""
    embedder = Mock()
    np.random.seed(45)

    def mock_encode(texts, *args, **kwargs):
        """Return embeddings matching input shape."""
        if isinstance(texts, str):
            return np.random.rand(384).astype(np.float32)
        return np.random.rand(len(texts), 384).astype(np.float32)

    embedder.encode = Mock(side_effect=mock_encode)
    embedder.get_sentence_embedding_dimension = Mock(return_value=384)
    return embedder


@pytest.fixture
def mock_reranker():
    """Mocked CrossEncoder that returns plausible rerank scores."""
    reranker = Mock()

    def mock_predict(pairs, *args, **kwargs):
        """Return scores matching input length."""
        if isinstance(pairs, list):
            return np.array([0.8 - i * 0.1 for i in range(len(pairs))])
        return np.array([0.5])

    reranker.predict = Mock(side_effect=mock_predict)
    return reranker


# =============================================================================
# File Fixtures - Test Documents
# =============================================================================


@pytest.fixture
def sample_principles_md(temp_dir):
    """Create a minimal principles markdown file for extraction testing."""
    content = """# Test Principles Document

## Series S: Safety

### S1. Safety First
**Definition**
Safety is paramount and must be considered in all decisions.

**How the AI Applies This Principle**
- Check for safety implications
- Escalate safety concerns immediately

## Series C: Core

### C1. Test Principle One
**Definition**
This is the first test principle with enough content to test extraction.

**How the AI Applies This Principle**
- Apply consistently
- Document everything

### C2. Test Principle Two
**Definition**
This is the second test principle.

**Failure Mode: Coverage Gaming**
Writing tests that exercise code but don't validate behavior.

## Series Q: Quality

### Q1. Quality Standards
**Definition**
Maintain quality in all outputs.
"""
    path = temp_dir / "documents" / "test-principles.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


@pytest.fixture
def sample_methods_md(temp_dir):
    """Create a minimal methods markdown file for extraction testing."""
    content = """# Test Methods Document

## 1 Cold Start Kit
Procedure for initializing new projects.

### Step 1
Create required files.

### Step 2
Run initial setup.

## 2 Gate Validation
Procedure for validating phase gates.

### Checklist
- [ ] All tests passing
- [ ] Coverage meets threshold
"""
    path = temp_dir / "documents" / "test-methods.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


@pytest.fixture
def sample_coding_principles_md(temp_dir):
    """Create a minimal AI coding principles markdown file for extraction testing."""
    content = """# AI Coding Domain Principles

## C1: Code Quality First

**Definition:** Prioritize maintainable, readable code.

All code must be well-tested and documented.

## C2: Test Coverage

**Definition:** Maintain adequate test coverage.

Tests should validate behavior, not just exercise code.
"""
    path = temp_dir / "documents" / "test-coding-principles.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


@pytest.fixture
def sample_domains_json(
    temp_dir, sample_principles_md, sample_coding_principles_md, sample_methods_md
):
    """Create a domains.json configuration file for testing."""
    domains = [
        {
            "name": "constitution",
            "display_name": "Constitution",
            "principles_file": "test-principles.md",
            "methods_file": None,
            "description": "Universal behavioral rules.",
            "priority": 0,
        },
        {
            "name": "ai-coding",
            "display_name": "AI Coding",
            "principles_file": "test-coding-principles.md",
            "methods_file": "test-methods.md",
            "description": "Software development with AI.",
            "priority": 10,
        },
    ]
    path = temp_dir / "documents" / "domains.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(domains, indent=2))
    return path


# =============================================================================
# Integration Fixtures - Saved Index
# =============================================================================


@pytest.fixture
def saved_index(
    test_settings, sample_global_index, mock_embeddings, mock_domain_embeddings
):
    """Save a complete index to disk for integration tests.

    Returns the settings pointing to the saved index.
    """
    # Save JSON index
    index_file = test_settings.index_path / "global_index.json"
    with open(index_file, "w") as f:
        json.dump(sample_global_index.model_dump(), f)

    # Save embeddings
    np.save(test_settings.index_path / "content_embeddings.npy", mock_embeddings)
    np.save(test_settings.index_path / "domain_embeddings.npy", mock_domain_embeddings)

    return test_settings


# =============================================================================
# Server State Fixtures
# =============================================================================


@pytest.fixture
def reset_server_state():
    """Reset global server state before and after each test.

    Critical for server tests to ensure test isolation.
    """
    import ai_governance_mcp.server as server_module

    # Reset before test
    server_module._settings = None
    server_module._engine = None
    server_module._metrics = None

    yield

    # Reset after test (cleanup)
    server_module._settings = None
    server_module._engine = None
    server_module._metrics = None


@pytest.fixture
def sample_metrics():
    """Pre-populated Metrics for testing metrics endpoints."""
    return Metrics(
        total_queries=100,
        avg_retrieval_time_ms=45.2,
        s_series_trigger_count=15,
        domain_query_counts={"constitution": 100, "ai-coding": 75, "multi-agent": 25},
        confidence_distribution={"high": 30, "medium": 50, "low": 20},
        feedback_count=10,
        avg_feedback_rating=4.2,
    )


@pytest.fixture
def sample_query_log():
    """Sample QueryLog for testing logging functions."""
    return QueryLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        query="test query",
        domains_detected=["constitution", "ai-coding"],
        principles_returned=["meta-C1", "coding-C1"],
        methods_returned=["coding-M1"],
        s_series_triggered=False,
        retrieval_time_ms=42.5,
        top_confidence=ConfidenceLevel.HIGH,
    )


@pytest.fixture
def sample_feedback():
    """Sample Feedback for testing feedback logging."""
    return Feedback(
        query="test query",
        principle_id="meta-C1",
        rating=4,
        comment="Helpful result",
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id="test-session-123",
    )


# =============================================================================
# Real Index Fixtures (for @pytest.mark.real_index tests)
# =============================================================================


@pytest.fixture
def real_index_path():
    """Path to the production index for real integration tests.

    Only used with @pytest.mark.real_index decorator.
    """
    project_root = Path(__file__).parent.parent
    index_path = project_root / "index"

    if not (index_path / "global_index.json").exists():
        pytest.skip("Production index not found - run extractor first")

    return index_path


@pytest.fixture
def real_settings(real_index_path):
    """Settings pointing to real production index."""
    project_root = Path(__file__).parent.parent
    settings = Settings()
    settings.documents_path = project_root / "documents"
    settings.index_path = real_index_path
    settings.logs_path = project_root / "logs"
    return settings


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def iso_timestamp():
    """Generate a valid ISO timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_error_response():
    """Sample ErrorResponse for testing error handling."""
    return ErrorResponse(
        error_code="PRINCIPLE_NOT_FOUND",
        message="Principle 'meta-X99' not found",
        suggestions=["Try 'meta-C1'", "Use list_domains to see available principles"],
    )
