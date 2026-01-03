"""Pydantic data models for AI Governance MCP Server.

Per specification v4: All data structures use Pydantic for validation.
Supports hybrid retrieval (BM25 + semantic embeddings + reranking).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def generate_audit_id() -> str:
    """Generate a unique audit ID for governance assessments."""
    return f"gov-{uuid.uuid4().hex[:12]}"


def generate_timestamp() -> str:
    """Generate an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat()


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


class AssessmentStatus(str, Enum):
    """Governance assessment outcome status."""

    PROCEED = "PROCEED"  # Action complies with governance
    PROCEED_WITH_MODIFICATIONS = "PROCEED_WITH_MODIFICATIONS"  # Needs changes
    ESCALATE = "ESCALATE"  # Human review required


class ComplianceStatus(str, Enum):
    """Compliance status for individual principle evaluation."""

    COMPLIANT = "COMPLIANT"  # Action aligns with principle
    GAP = "GAP"  # Principle not fully addressed
    VIOLATION = "VIOLATION"  # Action conflicts with principle


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

    id: str = Field(
        ..., description="Unique identifier, e.g., 'meta-core-context-engineering'"
    )
    domain: str = Field(
        ..., description="Domain name: 'constitution', 'ai-coding', 'multi-agent'"
    )
    series_code: Optional[str] = Field(
        None, description="Legacy series identifier (S, C, Q, O, G, MA) - deprecated"
    )
    number: Optional[int] = Field(
        None, description="Legacy principle number - deprecated"
    )
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

    id: str = Field(
        ..., description="Unique identifier, e.g., 'coding-method-project-calibration'"
    )
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


# =============================================================================
# Governance Agent Models
# =============================================================================


class RelevantPrinciple(BaseModel):
    """A principle identified as relevant to a governance assessment.

    Per §4.6.1 Assessment Responsibility Layers: Script layer provides
    full principle content for AI judgment layer to reason about.
    """

    id: str = Field(..., description="Principle ID")
    title: str = Field(..., description="Principle title")
    content: str = Field(..., description="Full principle text for AI reasoning")
    relevance: str = Field(..., description="Why this principle is relevant")
    score: float = Field(..., ge=0.0, le=1.0, description="Retrieval relevance score")
    series_code: Optional[str] = Field(
        None, description="Series code (S, C, Q, O, G, MA) if applicable"
    )
    domain: str = Field(..., description="Source domain for hierarchy resolution")


class ComplianceEvaluation(BaseModel):
    """Evaluation of action compliance against a single principle.

    When requires_ai_judgment=True, AI populates these fields.
    When False, script provides placeholder guidance.
    """

    principle_id: str = Field(..., description="Principle ID")
    principle_title: str = Field(..., description="Principle title")
    status: ComplianceStatus = Field(..., description="Compliance status")
    finding: str = Field(..., description="Specific finding explanation")
    suggested_modification: Optional[str] = Field(
        None,
        description="AI-generated modification to achieve compliance (when status=GAP)",
    )


class SSeriesCheck(BaseModel):
    """Result of S-Series (safety) principle check."""

    triggered: bool = Field(
        default=False, description="Whether any S-Series principle was triggered"
    )
    principles: list[str] = Field(
        default_factory=list, description="S-Series principle IDs that were triggered"
    )
    safety_concerns: list[str] = Field(
        default_factory=list, description="Specific safety concerns identified"
    )


class GovernanceAssessment(BaseModel):
    """Complete governance assessment for a planned action.

    Per multi-method-governance-agent-pattern (§4.3) and §4.6 Governance Enforcement:
    - PROCEED: Action complies with governance
    - PROCEED_WITH_MODIFICATIONS: Apply modifications, then execute
    - ESCALATE: Human review required (automatic if S-Series triggered)

    Audit fields (§4.6 Audit Trail Requirements):
    - audit_id: Unique identifier for tracking and compliance verification
    - timestamp: When the assessment was made
    """

    # Audit fields for enforcement tracking
    audit_id: str = Field(
        default_factory=generate_audit_id,
        description="Unique audit identifier for tracking",
    )
    timestamp: str = Field(
        default_factory=generate_timestamp,
        description="ISO timestamp of assessment",
    )

    # Assessment fields
    action_reviewed: str = Field(
        ..., description="The planned action that was assessed"
    )
    assessment: AssessmentStatus = Field(..., description="Assessment outcome")
    confidence: ConfidenceLevel = Field(..., description="Assessment confidence level")
    relevant_principles: list[RelevantPrinciple] = Field(
        default_factory=list, description="Principles relevant to this action"
    )
    compliance_evaluation: list[ComplianceEvaluation] = Field(
        default_factory=list, description="Per-principle compliance evaluation"
    )
    required_modifications: list[str] = Field(
        default_factory=list, description="Modifications needed for compliance"
    )
    s_series_check: SSeriesCheck = Field(
        default_factory=SSeriesCheck, description="S-Series safety check result"
    )
    rationale: str = Field(..., description="Explanation of the assessment")

    # Hybrid assessment fields (§4.6.1 Assessment Responsibility Layers)
    requires_ai_judgment: bool = Field(
        default=False,
        description="True when AI should determine final assessment. "
        "False when script has made definitive decision (e.g., ESCALATE from S-Series).",
    )
    ai_judgment_guidance: Optional[str] = Field(
        None,
        description="Instructions for AI layer when requires_ai_judgment=True",
    )


class VerificationStatus(str, Enum):
    """Status of governance compliance verification.

    Per §4.6 Layer 3: Post-Action Verification.
    """

    COMPLIANT = "COMPLIANT"  # Governance was consulted with matching assessment
    NON_COMPLIANT = "NON_COMPLIANT"  # Action proceeded without governance check
    PARTIAL = "PARTIAL"  # Check performed but for different scope


class VerificationResult(BaseModel):
    """Result of governance compliance verification.

    Per §4.6 Governance Enforcement Architecture, Layer 3.
    Checks whether governance was consulted for a completed action.
    """

    action_description: str = Field(..., description="The action that was verified")
    status: VerificationStatus = Field(..., description="Compliance status")
    matching_audit_id: Optional[str] = Field(
        None, description="Audit ID of matching governance check if found"
    )
    finding: str = Field(..., description="Explanation of verification result")
    timestamp: str = Field(
        default_factory=generate_timestamp, description="Verification timestamp"
    )


class GovernanceAuditLog(BaseModel):
    """Audit log entry for governance assessments.

    Per §4.6 Audit Trail Requirements: Every evaluate_governance() call
    generates an audit record. Enables pattern analysis and bypass detection.
    """

    audit_id: str = Field(..., description="Unique audit identifier")
    timestamp: str = Field(..., description="ISO timestamp of assessment")
    action: str = Field(..., description="The planned action that was assessed")
    assessment: AssessmentStatus = Field(..., description="Assessment outcome")
    principles_consulted: list[str] = Field(
        default_factory=list, description="Principle IDs that were consulted"
    )
    s_series_triggered: bool = Field(
        default=False, description="Whether S-Series safety principles were triggered"
    )
    modifications: Optional[list[str]] = Field(
        None, description="Required modifications if PROCEED_WITH_MODIFICATIONS"
    )
    escalation_reason: Optional[str] = Field(
        None, description="Reason for escalation if ESCALATE"
    )
    confidence: ConfidenceLevel = Field(..., description="Assessment confidence level")
