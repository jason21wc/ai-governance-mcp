"""Tests for Pydantic models (T19).

Per specification v4: Validates data model structures and constraints.
"""

import pytest
from pydantic import ValidationError

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.models import (
    AssessmentStatus,
    SeriesCode,
    ConfidenceLevel,
    PrincipleMetadata,
    Principle,
    Method,
    DomainConfig,
    ScoredPrinciple,
    RetrievalResult,
    Feedback,
    Metrics,
    ErrorResponse,
    GovernanceAssessment,
    GovernanceAuditLog,
    VerificationResult,
    VerificationStatus,
    generate_audit_id,
    generate_timestamp,
)


class TestEnums:
    """Test enum definitions."""

    def test_series_codes(self):
        """SeriesCode should have all expected values."""
        assert SeriesCode.S == "S"
        assert SeriesCode.C == "C"
        assert SeriesCode.Q == "Q"
        assert SeriesCode.OPER == "O"
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


class TestAuditFunctions:
    """Test audit helper functions."""

    def test_generate_audit_id_format(self):
        """Audit ID should have gov- prefix and 12 hex chars."""
        audit_id = generate_audit_id()
        assert audit_id.startswith("gov-")
        assert len(audit_id) == 16  # "gov-" + 12 hex chars

    def test_generate_audit_id_unique(self):
        """Each audit ID should be unique."""
        ids = {generate_audit_id() for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_generate_timestamp_iso_format(self):
        """Timestamp should be valid ISO format."""
        ts = generate_timestamp()
        # Should contain date separator and time separator
        assert "T" in ts
        assert "-" in ts
        assert ":" in ts


class TestGovernanceAssessment:
    """Test GovernanceAssessment model with audit fields."""

    def test_auto_generates_audit_id(self):
        """Should auto-generate audit_id if not provided."""
        assessment = GovernanceAssessment(
            action_reviewed="Test action",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
            rationale="Test rationale",
        )
        assert assessment.audit_id.startswith("gov-")

    def test_auto_generates_timestamp(self):
        """Should auto-generate timestamp if not provided."""
        assessment = GovernanceAssessment(
            action_reviewed="Test action",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
            rationale="Test rationale",
        )
        assert "T" in assessment.timestamp  # ISO format indicator

    def test_accepts_all_assessment_statuses(self):
        """Should accept all three assessment statuses."""
        for status in AssessmentStatus:
            assessment = GovernanceAssessment(
                action_reviewed="Test",
                assessment=status,
                confidence=ConfidenceLevel.MEDIUM,
                rationale="Test",
            )
            assert assessment.assessment == status

    def test_requires_ai_judgment_field(self):
        """Should have requires_ai_judgment field (§4.6.1)."""
        assessment = GovernanceAssessment(
            action_reviewed="Test action",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
            rationale="Test rationale",
            requires_ai_judgment=True,
            ai_judgment_guidance="Review principles for conflicts",
        )
        assert assessment.requires_ai_judgment is True
        assert assessment.ai_judgment_guidance is not None

    def test_requires_ai_judgment_defaults_to_false(self):
        """requires_ai_judgment should default to False."""
        assessment = GovernanceAssessment(
            action_reviewed="Test action",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
            rationale="Test rationale",
        )
        assert assessment.requires_ai_judgment is False
        assert assessment.ai_judgment_guidance is None


class TestRelevantPrinciple:
    """Tests for enhanced RelevantPrinciple model (§4.6.1)."""

    def test_relevant_principle_includes_content(self):
        """RelevantPrinciple should include content field for AI reasoning."""
        from ai_governance_mcp.models import RelevantPrinciple

        principle = RelevantPrinciple(
            id="test-C1",
            title="Test Principle",
            content="Full principle text for AI reasoning",
            relevance="Semantic match",
            score=0.85,
            domain="constitution",
        )
        assert principle.content == "Full principle text for AI reasoning"
        assert principle.domain == "constitution"

    def test_relevant_principle_optional_series_code(self):
        """series_code should be optional."""
        from ai_governance_mcp.models import RelevantPrinciple

        principle = RelevantPrinciple(
            id="test-C1",
            title="Test Principle",
            content="Full text",
            relevance="Match",
            score=0.5,
            domain="constitution",
        )
        assert principle.series_code is None

        principle_with_code = RelevantPrinciple(
            id="test-S1",
            title="Safety Principle",
            content="Safety text",
            relevance="Match",
            score=0.5,
            series_code="S",
            domain="constitution",
        )
        assert principle_with_code.series_code == "S"


class TestComplianceEvaluation:
    """Tests for enhanced ComplianceEvaluation model (§4.6.1)."""

    def test_compliance_evaluation_suggested_modification(self):
        """ComplianceEvaluation should have optional suggested_modification."""
        from ai_governance_mcp.models import ComplianceEvaluation, ComplianceStatus

        eval_without_mod = ComplianceEvaluation(
            principle_id="test-C1",
            principle_title="Test Principle",
            status=ComplianceStatus.COMPLIANT,
            finding="Action complies",
        )
        assert eval_without_mod.suggested_modification is None

        eval_with_mod = ComplianceEvaluation(
            principle_id="test-C1",
            principle_title="Test Principle",
            status=ComplianceStatus.GAP,
            finding="Action has gap",
            suggested_modification="Add tests before proceeding",
        )
        assert eval_with_mod.suggested_modification == "Add tests before proceeding"


class TestGovernanceAuditLog:
    """Test GovernanceAuditLog model."""

    def test_valid_audit_log(self):
        """Should accept valid audit log entry."""
        log = GovernanceAuditLog(
            audit_id="gov-abc123def456",
            timestamp="2026-01-01T10:00:00Z",
            action="Implementing new feature",
            assessment=AssessmentStatus.PROCEED,
            principles_consulted=["coding-C1", "coding-Q1"],
            s_series_triggered=False,
            confidence=ConfidenceLevel.HIGH,
        )
        assert log.audit_id == "gov-abc123def456"
        assert len(log.principles_consulted) == 2
        assert log.modifications is None
        assert log.escalation_reason is None

    def test_audit_log_with_escalation(self):
        """Should capture escalation reason."""
        log = GovernanceAuditLog(
            audit_id="gov-abc123def456",
            timestamp="2026-01-01T10:00:00Z",
            action="Dangerous action",
            assessment=AssessmentStatus.ESCALATE,
            principles_consulted=["meta-S1"],
            s_series_triggered=True,
            escalation_reason="S-Series violation detected",
            confidence=ConfidenceLevel.HIGH,
        )
        assert log.s_series_triggered is True
        assert log.escalation_reason == "S-Series violation detected"


class TestVerificationResult:
    """Test VerificationResult model."""

    def test_compliant_result(self):
        """Should create compliant verification result."""
        result = VerificationResult(
            action_description="Created new file",
            status=VerificationStatus.COMPLIANT,
            matching_audit_id="gov-abc123",
            finding="Governance was consulted",
        )
        assert result.status == VerificationStatus.COMPLIANT
        assert result.matching_audit_id is not None

    def test_non_compliant_result(self):
        """Should create non-compliant verification result."""
        result = VerificationResult(
            action_description="Modified code without check",
            status=VerificationStatus.NON_COMPLIANT,
            finding="No matching governance check found",
        )
        assert result.status == VerificationStatus.NON_COMPLIANT
        assert result.matching_audit_id is None

    def test_partial_result(self):
        """Should create partial verification result."""
        result = VerificationResult(
            action_description="Implemented feature",
            status=VerificationStatus.PARTIAL,
            matching_audit_id="gov-abc123",
            finding="Check found but scope mismatch",
        )
        assert result.status == VerificationStatus.PARTIAL

    def test_auto_generates_timestamp(self):
        """Should auto-generate timestamp."""
        result = VerificationResult(
            action_description="Test",
            status=VerificationStatus.COMPLIANT,
            finding="Test",
        )
        assert "T" in result.timestamp
