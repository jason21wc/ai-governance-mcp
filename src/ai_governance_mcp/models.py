"""Pydantic data models for AI Governance MCP Server.

Per specification v4: All data structures use Pydantic for validation.
Supports hybrid retrieval (BM25 + semantic embeddings + reranking).
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class SeriesCode(str, Enum):
    """Constitution series codes with hierarchy order."""

    S = "S"  # Safety - supreme priority
    C = "C"  # Core behavioral
    Q = "Q"  # Quality standards
    OPER = "O"  # Operational (named OPER to avoid E741 ambiguity with zero)
    G = "G"  # Growth
    MA = "MA"  # Meta-awareness


class ConfidenceLevel(str, Enum):
    """Confidence level for retrieval results."""

    HIGH = "high"  # Combined score >= 0.7
    MEDIUM = "medium"  # Combined score 0.4-0.7
    LOW = "low"  # Combined score < 0.4


# =============================================================================
# Core Data Models
# =============================================================================


class PrincipleMetadata(BaseModel):
    """Expanded metadata for principle matching.

    Used for BM25 keyword search component of hybrid retrieval.
    """

    keywords: list[str] = Field(
        default_factory=list, description="Primary trigger keywords"
    )
    synonyms: list[str] = Field(default_factory=list, description="Alternative terms")
    trigger_phrases: list[str] = Field(
        default_factory=list, description="Multi-word phrases"
    )
    failure_indicators: list[str] = Field(
        default_factory=list, description="Problem symptoms"
    )
    aliases: list[str] = Field(default_factory=list, description="Common abbreviations")


class Principle(BaseModel):
    """A single governance principle with full metadata.

    Embeddings are stored separately in NumPy arrays, indexed by embedding_id.
    """

    id: str = Field(..., description="Unique identifier, e.g., 'meta-C1', 'coding-C1'")
    domain: str = Field(
        ..., description="Domain name: 'constitution', 'ai-coding', 'multi-agent'"
    )
    series_code: str = Field(
        ..., description="Series identifier: S, C, Q, O, G, MA, A, P, D, T"
    )
    number: int = Field(..., description="Principle number within series")
    title: str = Field(..., description="Full principle title")
    content: str = Field(..., description="Complete principle text")
    line_range: tuple[int, int] = Field(
        ..., description="Source document line numbers (start, end)"
    )
    metadata: PrincipleMetadata = Field(
        default_factory=PrincipleMetadata, description="Matching metadata"
    )
    embedding_id: Optional[int] = Field(None, description="Index into embeddings array")


class Method(BaseModel):
    """A procedural method from domain methods document."""

    id: str = Field(..., description="Unique identifier, e.g., 'coding-M1', 'multi-M1'")
    domain: str = Field(..., description="Domain name")
    title: str = Field(..., description="Method title")
    content: str = Field(..., description="Complete method text")
    line_range: tuple[int, int] = Field(..., description="Source document line numbers")
    keywords: list[str] = Field(default_factory=list, description="Trigger keywords")
    embedding_id: Optional[int] = Field(None, description="Index into embeddings array")


class DomainConfig(BaseModel):
    """Configuration for a single domain.

    Domain embedding enables semantic routing.
    """

    name: str = Field(..., description="Domain identifier")
    display_name: str = Field(..., description="Human-readable name")
    principles_file: str = Field(..., description="Principles document filename")
    methods_file: Optional[str] = Field(None, description="Methods document filename")
    description: str = Field("", description="Domain description for semantic matching")
    priority: int = Field(
        default=100, description="Conflict resolution priority (lower = higher)"
    )
    embedding_id: Optional[int] = Field(
        None, description="Index into domain embeddings array"
    )


# =============================================================================
# Index Models
# =============================================================================


class DomainIndex(BaseModel):
    """Index of all principles and methods for a domain.

    Created at build time by extractor, loaded at runtime by server.
    """

    domain: str
    principles: list[Principle] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    last_extracted: str = Field(..., description="ISO timestamp of last extraction")
    version: str = Field(default="1.0", description="Index format version")


class GlobalIndex(BaseModel):
    """Complete index across all domains.

    Single file containing all domains for fast loading.
    """

    domains: dict[str, DomainIndex] = Field(default_factory=dict)
    domain_configs: list[DomainConfig] = Field(default_factory=list)
    created_at: str = Field(..., description="ISO timestamp")
    version: str = Field(default="1.0", description="Index format version")
    embedding_model: str = Field(..., description="Model used for embeddings")
    embedding_dimensions: int = Field(..., description="Embedding vector dimensions")


# =============================================================================
# Retrieval Models
# =============================================================================


class ScoredPrinciple(BaseModel):
    """A principle with hybrid retrieval scores."""

    principle: Principle
    semantic_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Semantic similarity score"
    )
    keyword_score: float = Field(
        0.0, ge=0.0, description="BM25 keyword score (normalized)"
    )
    combined_score: float = Field(0.0, ge=0.0, le=1.0, description="Fused score")
    rerank_score: Optional[float] = Field(
        None, description="Cross-encoder rerank score"
    )
    confidence: ConfidenceLevel = Field(
        ConfidenceLevel.LOW, description="Confidence level"
    )
    match_reasons: list[str] = Field(
        default_factory=list, description="Explanation of match"
    )


class ScoredMethod(BaseModel):
    """A method with hybrid retrieval scores."""

    method: Method
    semantic_score: float = Field(0.0, ge=0.0, le=1.0)
    keyword_score: float = Field(0.0, ge=0.0)
    combined_score: float = Field(0.0, ge=0.0, le=1.0)
    confidence: ConfidenceLevel = Field(ConfidenceLevel.LOW)


class RetrievalResult(BaseModel):
    """Result from a governance retrieval query."""

    query: str
    domains_detected: list[str]
    domain_scores: dict[str, float] = Field(
        default_factory=dict, description="Domain routing scores"
    )
    constitution_principles: list[ScoredPrinciple] = Field(default_factory=list)
    domain_principles: list[ScoredPrinciple] = Field(default_factory=list)
    methods: list[ScoredMethod] = Field(default_factory=list)
    s_series_triggered: bool = Field(
        default=False, description="Whether S-Series applies"
    )
    retrieval_time_ms: Optional[float] = Field(None, description="Total retrieval time")


# =============================================================================
# Feedback & Logging Models
# =============================================================================


class Feedback(BaseModel):
    """User feedback on retrieval quality.

    Logged for future retrieval improvement.
    """

    query: str = Field(..., description="Original query")
    principle_id: str = Field(..., description="Principle being rated")
    rating: int = Field(..., ge=1, le=5, description="1-5 rating")
    comment: Optional[str] = Field(None, description="Optional feedback text")
    timestamp: str = Field(..., description="ISO timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier")


class QueryLog(BaseModel):
    """Log entry for a governance query.

    Enables retrieval analytics and debugging.
    """

    timestamp: str = Field(..., description="ISO timestamp")
    query: str
    domains_detected: list[str]
    principles_returned: list[str] = Field(
        default_factory=list, description="Principle IDs"
    )
    methods_returned: list[str] = Field(default_factory=list, description="Method IDs")
    s_series_triggered: bool = False
    retrieval_time_ms: Optional[float] = None
    top_confidence: Optional[ConfidenceLevel] = None


class Metrics(BaseModel):
    """Aggregated retrieval metrics."""

    total_queries: int = 0
    avg_retrieval_time_ms: float = 0.0
    s_series_trigger_count: int = 0
    domain_query_counts: dict[str, int] = Field(default_factory=dict)
    confidence_distribution: dict[str, int] = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0}
    )
    feedback_count: int = 0
    avg_feedback_rating: Optional[float] = None


# =============================================================================
# Error Response
# =============================================================================


class ErrorResponse(BaseModel):
    """Structured error response."""

    error_code: str
    message: str
    suggestions: list[str] = Field(default_factory=list)
