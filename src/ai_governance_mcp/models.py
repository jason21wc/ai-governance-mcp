"""Pydantic data models for AI Governance MCP Server.

Per specification v3: All data structures use Pydantic for validation.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SeriesCode(str, Enum):
    """Constitution series codes with hierarchy order."""

    S = "S"  # Safety - supreme priority
    C = "C"  # Core behavioral
    Q = "Q"  # Quality standards
    O = "O"  # Operational
    G = "G"  # Growth
    MA = "MA"  # Meta-awareness


class PrincipleMetadata(BaseModel):
    """Expanded metadata for principle matching.

    Per specification v3 §3.2: Enables ~5% miss rate via expanded keywords.
    """

    keywords: list[str] = Field(default_factory=list, description="Primary trigger keywords")
    synonyms: list[str] = Field(default_factory=list, description="Alternative terms (0.8 weight)")
    trigger_phrases: list[str] = Field(
        default_factory=list, description="Multi-word phrases (2.0 weight)"
    )
    failure_indicators: list[str] = Field(
        default_factory=list, description="Problem symptoms (1.5 weight)"
    )
    aliases: list[str] = Field(default_factory=list, description="Common abbreviations")


class Principle(BaseModel):
    """A single governance principle with full metadata."""

    id: str = Field(..., description="Unique identifier, e.g., 'meta-C1', 'coding-C1'")
    domain: str = Field(..., description="Domain name: 'constitution', 'ai-coding', 'multi-agent'")
    series_code: str = Field(..., description="Series identifier: S, C, Q, O, G, MA, A, P, D, T")
    number: int = Field(..., description="Principle number within series")
    title: str = Field(..., description="Full principle title")
    content: str = Field(..., description="Complete principle text")
    line_range: tuple[int, int] = Field(..., description="Source document line numbers (start, end)")
    metadata: PrincipleMetadata = Field(
        default_factory=PrincipleMetadata, description="Matching metadata"
    )


class Method(BaseModel):
    """A procedural method from domain methods document."""

    id: str = Field(..., description="Unique identifier, e.g., 'coding-M1', 'multi-M1'")
    domain: str = Field(..., description="Domain name")
    title: str = Field(..., description="Method title")
    content: str = Field(..., description="Complete method text")
    line_range: tuple[int, int] = Field(..., description="Source document line numbers")
    keywords: list[str] = Field(default_factory=list, description="Trigger keywords")


class DomainConfig(BaseModel):
    """Configuration for a single domain."""

    name: str = Field(..., description="Domain identifier")
    display_name: str = Field(..., description="Human-readable name")
    principles_file: str = Field(..., description="Principles document filename")
    methods_file: Optional[str] = Field(None, description="Methods document filename")
    trigger_keywords: list[str] = Field(default_factory=list, description="Domain detection keywords")
    trigger_phrases: list[str] = Field(default_factory=list, description="Multi-word triggers")
    priority: int = Field(default=100, description="Conflict resolution priority (lower = higher priority)")


class DomainIndex(BaseModel):
    """Index of all principles and methods for a domain."""

    domain: str
    principles: list[Principle] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    last_extracted: str = Field(..., description="ISO timestamp of last extraction")


class ScoredPrinciple(BaseModel):
    """A principle with its relevance score."""

    principle: Principle
    score: float = Field(..., ge=0.0, description="Relevance score")
    match_reasons: list[str] = Field(default_factory=list, description="Why this matched")


class RetrievalResult(BaseModel):
    """Result from a governance retrieval query."""

    query: str
    domains_detected: list[str]
    constitution_principles: list[ScoredPrinciple] = Field(default_factory=list)
    domain_principles: list[ScoredPrinciple] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    s_series_triggered: bool = Field(default=False, description="Whether S-Series safety principles apply")
    total_tokens_saved: Optional[int] = Field(None, description="Estimated tokens saved vs full load")


class ErrorResponse(BaseModel):
    """Structured error response per specification v3."""

    error_code: str
    message: str
    suggestions: list[str] = Field(default_factory=list)


class AuditLogEntry(BaseModel):
    """Audit log entry for governance queries."""

    timestamp: str = Field(..., description="ISO timestamp")
    tool_name: str
    query: str
    domains_detected: list[str]
    principles_returned: list[str] = Field(default_factory=list, description="Principle IDs returned")
    s_series_triggered: bool = False
