"""Tests for governance tool handlers.

Split from test_server.py during Phase 3 server decomposition.
Covers: evaluate_governance, verify_governance_compliance,
log_governance_reasoning, safety detection, tiers/floor building.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from helpers import extract_json_from_response

# =============================================================================
# Evaluate Governance Tests (Governance Agent)
# =============================================================================


class TestEvaluateGovernance:
    """Tests for evaluate_governance tool (Governance Agent).

    Per multi-method-governance-agent-pattern (§4.3).
    """

    @pytest.mark.asyncio
    async def test_evaluate_governance_returns_assessment_structure(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return proper assessment structure."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new logging function"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Verify structure
                    assert "action_reviewed" in parsed
                    assert "assessment" in parsed
                    assert "confidence" in parsed
                    assert "relevant_principles" in parsed
                    assert "relevant_methods" in parsed
                    assert "compliance_evaluation" in parsed
                    assert "s_series_check" in parsed
                    assert "rationale" in parsed

                    # Assessment should be one of the valid statuses
                    assert parsed["assessment"] in [
                        "PROCEED",
                        "REVIEW",
                        "ESCALATE",
                    ]

    @pytest.mark.asyncio
    async def test_evaluate_governance_detects_safety_keywords(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should trigger ESCALATE for safety keywords."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Action with safety keyword
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Delete user credentials from database"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # S-Series should be triggered
                    assert parsed["s_series_check"]["triggered"] is True
                    assert len(parsed["s_series_check"]["safety_concerns"]) > 0
                    # Assessment should be ESCALATE
                    assert parsed["assessment"] == "ESCALATE"
                    # Confidence should be HIGH (safety is not uncertain)
                    assert parsed["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_evaluate_governance_missing_planned_action(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return error if planned_action missing."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool("evaluate_governance", {})

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
                    assert "planned_action" in parsed["message"]

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_context(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should accept optional context and concerns."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Refactor authentication module",
                            "context": "Legacy code needs modernization",
                            "concerns": "Breaking changes to API",
                        },
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Should process without error
                    assert "action_reviewed" in parsed
                    assert parsed["action_reviewed"] == "Refactor authentication module"

    @pytest.mark.asyncio
    async def test_evaluate_governance_normal_action_proceeds(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return PROCEED for normal actions without safety keywords."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Normal action without safety concerns - very neutral language
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Format code with prettier"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # No safety keyword concerns should be detected from the action
                    assert len(parsed["s_series_check"]["safety_concerns"]) == 0
                    # No S-Series → no ESCALATE. REVIEW is acceptable when
                    # non-S-Series principles score above review_score_threshold.
                    if not parsed["s_series_check"]["principles"]:
                        assert parsed["assessment"] in ("PROCEED", "REVIEW")

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_principle_content(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include full principle content for AI reasoning (§4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement user authentication"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # If principles were found, verify content is included
                    if parsed["relevant_principles"]:
                        first_principle = parsed["relevant_principles"][0]
                        assert "content" in first_principle
                        assert len(first_principle["content"]) > 0
                        assert "domain" in first_principle
                        assert "series_code" in first_principle

    @pytest.mark.asyncio
    async def test_evaluate_governance_sets_requires_ai_judgment(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should set requires_ai_judgment for non-S-Series cases (§4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Non-safety action that should match principles
                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor the code structure"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # If principles found and no S-Series, should require AI judgment
                    if (
                        parsed["relevant_principles"]
                        and not parsed["s_series_check"]["triggered"]
                    ):
                        assert parsed["requires_ai_judgment"] is True
                        assert parsed["ai_judgment_guidance"] is not None

    @pytest.mark.asyncio
    async def test_evaluate_returns_review_when_principles_found(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should return REVIEW when principles score above threshold (#155, #158)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor the code structure"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    if (
                        parsed["relevant_principles"]
                        and not parsed["s_series_check"]["triggered"]
                    ):
                        top_score = max(
                            p["score"] for p in parsed["relevant_principles"]
                        )
                        if top_score >= test_settings.review_score_threshold:
                            assert parsed["assessment"] == "REVIEW"
                        else:
                            assert parsed["assessment"] == "PROCEED"

    @pytest.mark.asyncio
    async def test_evaluate_returns_proceed_when_principles_below_threshold(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Principles below review_score_threshold yield PROCEED, not REVIEW (#158).

        combined_score (BM25+semantic fused) determines best_score, not rerank_score.
        Patch retrieve() to return principles with controlled combined_score < 0.5.
        """
        from ai_governance_mcp.models import (
            ConfidenceLevel,
            Principle,
            RetrievalResult,
            ScoredPrinciple,
        )

        low_result = RetrievalResult(
            query="Refactor the code structure",
            domains_detected=["ai-coding"],
            domain_scores={"ai-coding": 0.8},
            constitution_principles=[
                ScoredPrinciple(
                    principle=Principle(
                        id="meta-Q1",
                        domain="constitution",
                        series_code="Q",
                        title="Quality Standard",
                        content="Test quality principle.",
                        line_range=(1, 5),
                    ),
                    combined_score=0.35,
                    confidence=ConfidenceLevel.LOW,
                ),
            ],
            domain_principles=[
                ScoredPrinciple(
                    principle=Principle(
                        id="coding-C1",
                        domain="ai-coding",
                        series_code="C",
                        title="Coding Standard",
                        content="Test coding principle.",
                        line_range=(1, 5),
                    ),
                    combined_score=0.40,
                    confidence=ConfidenceLevel.MEDIUM,
                ),
            ],
            methods=[],
            s_series_triggered=False,
            retrieval_time_ms=5.0,
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool
                    from ai_governance_mcp.server._state import get_engine

                    engine = get_engine()
                    with patch.object(engine, "retrieve", return_value=low_result):
                        result = await call_tool(
                            "evaluate_governance",
                            {"planned_action": "Refactor the code structure"},
                        )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["relevant_principles"]
                    assert not parsed["s_series_check"]["triggered"]
                    assert parsed["assessment"] == "PROCEED"
                    assert "below REVIEW threshold" in parsed["rationale"]

    @pytest.mark.asyncio
    async def test_s_series_semantic_below_threshold_does_not_escalate(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Low-score S-Series semantic match should not trigger ESCALATE (#150).

        Regression test: session-142 repro — benign housekeeping action
        matched meta-safety-transparent-limitations at low score, causing
        false ESCALATE. With s_series_score_threshold gate, low-score S-Series
        principles appear in results but don't trigger veto.
        """
        from ai_governance_mcp.models import (
            ConfidenceLevel,
            Principle,
            RetrievalResult,
            ScoredPrinciple,
        )

        low_s_series_result = RetrievalResult(
            query="Remove BACKLOG #147 entry per 'no closed items' rule",
            domains_detected=[],
            domain_scores={},
            constitution_principles=[
                ScoredPrinciple(
                    principle=Principle(
                        id="meta-safety-transparent-limitations",
                        domain="constitution",
                        series_code="S",
                        title="Transparent Limitations",
                        content="Acknowledge limitations honestly.",
                        line_range=(1, 5),
                    ),
                    combined_score=0.42,
                    confidence=ConfidenceLevel.MEDIUM,
                ),
                ScoredPrinciple(
                    principle=Principle(
                        id="meta-Q1",
                        domain="constitution",
                        series_code="Q",
                        title="Quality Standard",
                        content="Maintain quality.",
                        line_range=(6, 10),
                    ),
                    combined_score=0.35,
                    confidence=ConfidenceLevel.LOW,
                ),
            ],
            domain_principles=[],
            methods=[],
            s_series_triggered=False,
            retrieval_time_ms=5.0,
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool
                    from ai_governance_mcp.server._state import get_engine

                    engine = get_engine()
                    with patch.object(
                        engine, "retrieve", return_value=low_s_series_result
                    ):
                        result = await call_tool(
                            "evaluate_governance",
                            {
                                "planned_action": (
                                    "Remove BACKLOG #147 entry from BACKLOG.md "
                                    "per 'no closed items' rule"
                                )
                            },
                        )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert not parsed["s_series_check"]["triggered"], (
                        "S-Series should not trigger when all S-Series principle "
                        "scores are below s_series_score_threshold"
                    )
                    assert parsed["assessment"] == "PROCEED"

    @pytest.mark.asyncio
    async def test_evaluate_governance_escalate_does_not_require_ai_judgment(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """S-Series ESCALATE should not require AI judgment (script-enforced, §4.6.1)."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Delete all user credentials"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # S-Series ESCALATE is script-enforced, not AI judgment
                    assert parsed["assessment"] == "ESCALATE"
                    assert parsed["requires_ai_judgment"] is False

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_methods(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include relevant_methods as a list."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement project initialization workflow"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # relevant_methods should always be present as a list
                    assert "relevant_methods" in parsed
                    assert isinstance(parsed["relevant_methods"], list)

                    # If methods were found, verify each entry has correct fields
                    for method in parsed["relevant_methods"]:
                        assert isinstance(method["id"], str)
                        assert isinstance(method["title"], str)
                        assert isinstance(method["domain"], str)
                        assert isinstance(method["score"], (int, float))
                        assert 0.0 <= method["score"] <= 1.0
                        assert method["confidence"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_evaluate_governance_methods_in_ai_guidance(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """ai_judgment_guidance should mention methods only when relevant_methods is non-empty."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor the authentication module"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))

                    if parsed.get("ai_judgment_guidance"):
                        if parsed["relevant_methods"]:
                            # When methods present, guidance should mention them
                            assert "method" in parsed["ai_judgment_guidance"].lower()
                        else:
                            # When no methods, guidance should not mention them
                            assert (
                                "method" not in parsed["ai_judgment_guidance"].lower()
                            )

    # =========================================================================
    # FM-S-SERIES-KEYWORD-FALSE-POSITIVE coverage tests (BACKLOG #129).
    # Sentence-level safe-context allowlist; demotes CRITICAL keyword matches
    # to ADVISORY when (a) every sentence containing the keyword has a leader
    # phrase, AND (b) no imperative-action verb appears in the action.
    # Imperative + safe-context re-escalates (bypass guard).
    # =========================================================================

    @pytest.mark.asyncio
    async def test_evaluate_governance_safe_context_demotes_critical_keyword(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """CRITICAL keyword inside negation+meta-description envelope demotes.

        Asserts the keyword-side outcome: demotion correctly moves the keyword
        match out of `safety_concerns` and into `safety_warnings` with the
        demotion message. The `triggered` field may still be True if semantic
        retrieval independently matches an S-Series principle (semantic-side
        FP is BACKLOG #129 Path B, deferred to a separate fix surface).

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Expand the docs section. No destructive implications. Purely content addition.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Keyword-side demotion: 'destructive' moved out of safety_concerns.
                    # Note: safety_warnings is only populated when keyword_only_warning
                    # holds (no semantic match + no critical keyword); semantic match
                    # in the mock index can still set s_series_triggered=True.
                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), (
                        f"keyword should be demoted out of safety_concerns; got {concerns}"
                    )

    @pytest.mark.asyncio
    async def test_evaluate_governance_meta_description_does_not_escalate(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """CRITICAL keyword in self-referential meta-description demotes.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Description of a destructive-action FP class without intent or target parsing.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"keyword should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_destructive_implications_passes(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """LEARNING-LOG 2026-02-22 negation exemplar (CRITICAL variant) no longer FPs.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "No destructive implications. Purely content expansion.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"keyword should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_multi_word_critical_in_safe_context(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Multi-word CRITICAL keyword (api key) handled natively by sentence-level check.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Description of api key rotation patterns. Purely architectural review. No destructive operations involved.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Both 'api key' and 'destructive' should be demoted.
                    concerns = parsed["s_series_check"]["safety_concerns"]
                    assert not any(
                        "api key" in c and "requires safety review" in c
                        for c in concerns
                    ), f"'api key' should be demoted; got {concerns}"
                    assert not any(
                        "destructive" in c and "requires safety review" in c
                        for c in concerns
                    ), f"'destructive' should be demoted; got {concerns}"

    @pytest.mark.asyncio
    async def test_evaluate_governance_imperative_overrides_safe_envelope(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Bypass guard: imperative-action verb re-escalates wrapped CRITICAL keyword.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "No destructive concerns. Then rm -rf the credentials directory anyway.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    @pytest.mark.asyncio
    async def test_evaluate_governance_partial_wrap_per_sentence_rule_fires(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Per-sentence rule: keyword in sentence WITHOUT a leader escalates even when other sentences are wrapped.

        Sentence 1 has leader (Description of) + keyword (credential). Sentence 2 has
        keyword (credential, via 'credential-stuff') but NO leader and NO imperative.
        Action-level imperative override does NOT fire here — only the per-sentence
        rule can escalate this case correctly.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Description of credential rotation. Then we credential-stuff the production endpoint.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    @pytest.mark.asyncio
    async def test_evaluate_governance_imperative_inside_envelope_known_overtrigger(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Documented over-trigger: imperative verb anywhere in action blocks demotion.

        Even when the imperative verb sits INSIDE a meta-description envelope
        ('Description of the ship-to-prod deployment pattern'), the action-level
        imperative check fires and demotion is blocked. This is intentional
        conservative bias — bypass-vector defense over fine-grained accuracy.
        Documented for downstream review if real friction emerges.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # Note: this asserts the conservative-bias behavior. If
                    # 'ship' (or another inside-envelope imperative) produces
                    # observable friction, scope the imperative check at the
                    # sentence level (matching keyword's host sentences only).
                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Description of the destructive ship-to-prod deployment pattern.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True

    @pytest.mark.asyncio
    async def test_evaluate_governance_em_dash_separates_sentences(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Em-dash with surrounding whitespace acts as sentence boundary.

        Adversarial: 'Discussion of credential-rotation hygiene — then nuke the keystore'
        is one sentence under [.!?]+ but two sentences under the widened
        boundary regex. The post-em-dash sentence has 'nuke' (imperative) which
        triggers the action-level override. Defense in depth.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "Discussion of credential-rotation hygiene — then nuke the keystore.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"

    def test_imperative_action_verbs_covers_common_mutations(self):
        """`_IMPERATIVE_ACTION_VERBS` must cover common mutation/disclosure verbs.

        Defends silent-FN class: a CRITICAL keyword wrapped in a safe-context
        sentence (no imperative verb in that sentence) but paired with a
        destructive action elsewhere in the action string. Per FM-S-SERIES
        co-evolution rule (registry description) — failure here forces
        deliberate audit when imperative list drifts.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        from ai_governance_mcp.server import _IMPERATIVE_ACTION_VERBS

        required_verbs = (
            "ship",
            "deploy",
            "delete",
            "drop",
            "truncate",
            "wipe",
            "rm",
            "erase",
            "purge",
            "kill",
            "nuke",
            "format",
            "chmod",
            "sudo",
            "flush",
            "revoke",
            "terminate",
            "rotate",
            "replace",
            "migrate",
            "modify",
            "restart",
            "restore",
            "clone",
            "expose",
            "leak",
            "dump",
        )
        for verb in required_verbs:
            assert _IMPERATIVE_ACTION_VERBS.search(verb), (
                f"common mutation/disclosure verb {verb!r} missing from "
                f"_IMPERATIVE_ACTION_VERBS — drift risks silent FN per "
                f"BACKLOG #129 post-arc contrarian audit a8e2e0926f756db45 HIGH #1"
            )

        # Word-boundary regression guard (per code-reviewer audit
        # a5c776ac67944436a MEDIUM #2): the imperative regex MUST use `\b...\b`
        # anchors so verbs don't accidentally match inside larger words. If a
        # future maintainer replaced `\b(...)\b` with `(...)`, the positive
        # assertions above would still pass but these negative cases would
        # fail — forcing the boundary discipline back in.
        non_verb_substrings = (
            "exposed",  # contains 'expose' as prefix
            "restoration",  # contains 'restore' as prefix
            "deployment",  # contains 'deploy' as prefix
            "modifying",  # contains 'modify' as prefix
        )
        for word in non_verb_substrings:
            assert not _IMPERATIVE_ACTION_VERBS.fullmatch(word), (
                f"_IMPERATIVE_ACTION_VERBS word-boundary discipline broken: "
                f"{word!r} matches via fullmatch — boundary-anchored regex would "
                f"reject it. A maintainer dropped \\b...\\b anchors."
            )

    def test_critical_safety_keywords_pinned_for_co_evolution(self):
        """Pin CRITICAL keyword set so growth forces imperative-list audit.

        When this test fails, the author MUST audit `_IMPERATIVE_ACTION_VERBS`
        for newly-needed mutation/disclosure verbs paired with the new CRITICAL
        keyword, then update both `expected_critical` here AND the imperative
        list in `server.py`. Per FM-S-SERIES co-evolution rule.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        from ai_governance_mcp.server import CRITICAL_SAFETY_KEYWORDS

        expected_critical = frozenset(
            {
                "credential",
                "password",
                "secret",
                "api key",
                "private key",
                "access token",
                "encryption key",
                "pii",
                "personal data",
                "irreversible",
                "destructive",
            }
        )
        actual = frozenset(CRITICAL_SAFETY_KEYWORDS)
        assert actual == expected_critical, (
            f"CRITICAL_SAFETY_KEYWORDS changed (added: {actual - expected_critical}, "
            f"removed: {expected_critical - actual}). Audit `_IMPERATIVE_ACTION_VERBS` "
            f"for newly-needed verbs paired with the change, then update both "
            f"expected_critical in this test AND the imperative list in server.py. "
            f"FM-S-SERIES co-evolution rule (registry description)."
        )

    @pytest.mark.asyncio
    async def test_evaluate_governance_field_bridging_does_not_demote(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Per-field calls prevent leader in `context` from covering keyword in `planned_action`.

        Without per-field call refactor (round-2 contrarian HIGH #1), a benign-
        looking 'Discussion of cleanup procedures' in `context` could silently
        cover a real CRITICAL keyword in `planned_action`. With per-field calls,
        each field is its own sentence stream — no bridging.

        Covers: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
        """
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {
                            "planned_action": "rm -rf /var/log/credentials",
                            "context": "Discussion of cleanup procedures.",
                        },
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert parsed["s_series_check"]["triggered"] is True
                    assert parsed["assessment"] == "ESCALATE"


# =============================================================================
# Audit Log Tests (Phase 2: Governance Enforcement)
# =============================================================================


class TestVerifyGovernanceCompliance:
    """Tests for verify_governance_compliance tool."""

    @pytest.fixture(autouse=True)
    def reset_audit_log(self):
        """Reset audit log before each test."""
        from ai_governance_mcp import server

        server._audit_log.clear()
        yield
        server._audit_log.clear()

    @pytest.mark.asyncio
    async def test_verify_returns_non_compliant_when_no_audit(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should return NON_COMPLIANT when no audit log."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "verify_governance_compliance",
                        {"action_description": "Made some changes"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert parsed["status"] == "NON_COMPLIANT"
                    assert "No governance checks" in parsed["finding"]

    @pytest.mark.asyncio
    async def test_verify_returns_compliant_after_evaluate(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should return COMPLIANT after evaluate_governance."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    # First, call evaluate_governance
                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Implement config generator feature"},
                    )

                    # Then verify compliance
                    result = await call_tool(
                        "verify_governance_compliance",
                        {"action_description": "Implemented config generator feature"},
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert parsed["status"] == "COMPLIANT"
                    assert parsed["matching_audit_id"] is not None

    @pytest.mark.asyncio
    async def test_verify_requires_action_description(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """verify_governance_compliance should require action_description."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "verify_governance_compliance",
                        {},  # Missing action_description
                    )

                    parsed = json.loads(extract_json_from_response(result[0].text))
                    assert "error_code" in parsed
                    assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"


# =============================================================================
# Entry Point Tests
# =============================================================================


# =============================================================================
# Governance Reasoning Externalization Tests
# =============================================================================


class TestLogGovernanceReasoning:
    """Tests for log_governance_reasoning tool."""

    @pytest.fixture(autouse=True)
    def reset_logs(self):
        """Reset audit and reasoning logs before each test."""
        from ai_governance_mcp import server

        server._audit_log.clear()
        server._reasoning_log.clear()
        yield
        server._audit_log.clear()
        server._reasoning_log.clear()

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_audit_id(self, reset_server_state):
        """Should return error when audit_id is missing."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning({})
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "audit_id" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_reasoning(self, reset_server_state):
        """Should return error when reasoning array is empty."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-123456789012",
                "reasoning": [],
                "final_decision": "PROCEED",
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "reasoning" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_missing_final_decision(self, reset_server_state):
        """Should return error when final_decision is missing."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-123456789012",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Test",
                    }
                ],
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "final_decision" in parsed["message"]

    @pytest.mark.asyncio
    async def test_log_reasoning_invalid_audit_id(self, reset_server_state):
        """Should return error when audit_id doesn't exist."""
        from ai_governance_mcp.server import _handle_log_governance_reasoning

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-nonexistent1",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Test",
                    }
                ],
                "final_decision": "PROCEED",
            }
        )
        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["error_code"] == "AUDIT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_log_reasoning_success(self, reset_server_state):
        """log_governance_reasoning should log reasoning trace successfully."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry directly (simpler than mocking full pipeline)
        audit_id = "gov-success12345"
        audit_entry = GovernanceAuditLog(
            audit_id=audit_id,
            timestamp="2026-01-01T00:00:00Z",
            action="Test action for reasoning",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Now call log_governance_reasoning with that audit_id
        result = await _handle_log_governance_reasoning(
            {
                "audit_id": audit_id,
                "reasoning": [
                    {
                        "principle_id": "meta-C1",
                        "status": "COMPLIES",
                        "reasoning": "Action follows quality standards.",
                    },
                    {
                        "principle_id": "coding-Q1",
                        "status": "NEEDS_MODIFICATION",
                        "reasoning": "Should add input validation.",
                    },
                ],
                "final_decision": "REVIEW",
                "modifications_applied": ["Added input validation"],
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert parsed["audit_id"] == audit_id
        assert parsed["entries_logged"] == 2
        assert parsed["final_decision"] == "REVIEW"
        assert parsed["modifications_count"] == 1

        # Verify reasoning log contains the entry
        reasoning_log = get_reasoning_log()
        assert len(reasoning_log) == 1
        assert reasoning_log[0].audit_id == audit_id
        assert len(reasoning_log[0].reasoning_entries) == 2
        assert reasoning_log[0].final_decision == "REVIEW"

    @pytest.mark.asyncio
    async def test_log_reasoning_review_decision(self, reset_server_state):
        """log_governance_reasoning should accept REVIEW as final_decision (#155)."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        audit_id = "gov-review12345"
        audit_entry = GovernanceAuditLog(
            audit_id=audit_id,
            timestamp="2026-01-01T00:00:00Z",
            action="Test review decision",
            assessment=AssessmentStatus.REVIEW,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": audit_id,
                "reasoning": [
                    {
                        "principle_id": "meta-C1",
                        "status": "COMPLIES",
                        "reasoning": "Reviewed principle and adjusted approach.",
                    },
                ],
                "final_decision": "REVIEW",
                "modifications_applied": ["Adjusted approach per principle guidance"],
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert parsed["final_decision"] == "REVIEW"

        reasoning_log = get_reasoning_log()
        assert reasoning_log[-1].final_decision == "REVIEW"

    @pytest.mark.asyncio
    async def test_log_reasoning_sanitizes_input(self, reset_server_state):
        """Should sanitize reasoning text to prevent injection."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry directly
        audit_entry = GovernanceAuditLog(
            audit_id="gov-sanitize123",
            timestamp="2026-01-01T00:00:00Z",
            action="Test sanitization",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Call with potentially dangerous input
        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-sanitize123",
                "reasoning": [
                    {
                        "principle_id": "test-id",
                        "status": "COMPLIES",
                        "reasoning": "Normal text <script>alert('xss')</script> more text",
                    }
                ],
                "final_decision": "PROCEED",
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"

        # Verify the reasoning was logged (sanitization doesn't reject, just cleans)
        reasoning_log = get_reasoning_log()
        assert len(reasoning_log) == 1

    @pytest.mark.asyncio
    async def test_log_reasoning_limits_entries(self, reset_server_state):
        """Should limit reasoning entries to 20."""
        from ai_governance_mcp.server import (
            _handle_log_governance_reasoning,
            get_reasoning_log,
            log_governance_audit,
        )
        from ai_governance_mcp.models import (
            GovernanceAuditLog,
            AssessmentStatus,
            ConfidenceLevel,
        )

        # Create an audit entry
        audit_entry = GovernanceAuditLog(
            audit_id="gov-limit1234567",
            timestamp="2026-01-01T00:00:00Z",
            action="Test limits",
            assessment=AssessmentStatus.PROCEED,
            confidence=ConfidenceLevel.HIGH,
        )
        log_governance_audit(audit_entry)

        # Create 25 reasoning entries
        many_entries = [
            {
                "principle_id": f"test-{i}",
                "status": "COMPLIES",
                "reasoning": f"Entry {i}",
            }
            for i in range(25)
        ]

        result = await _handle_log_governance_reasoning(
            {
                "audit_id": "gov-limit1234567",
                "reasoning": many_entries,
                "final_decision": "PROCEED",
            }
        )

        parsed = json.loads(extract_json_from_response(result[0].text))
        assert parsed["status"] == "logged"
        assert parsed["entries_logged"] == 20  # Limited to 20

        reasoning_log = get_reasoning_log()
        assert len(reasoning_log[0].reasoning_entries) == 20


# =============================================================================
# Governance Reminder CE Nudge Tests (Fix 3)
# =============================================================================


# =============================================================================
# Universal Floor (Tier 1) Tests
# =============================================================================


class TestTiersConfig:
    """Tests for tiers.json loading and universal floor building."""

    def test_load_tiers_config_from_documents(self, reset_server_state, test_settings):
        """Should load tiers.json from documents directory."""
        import ai_governance_mcp.server as srv

        # Write a minimal tiers.json
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Are you honest?",
                            }
                        ],
                        "methods": [],
                    }
                }
            )
        )

        srv._state._settings = test_settings
        srv._state._tiers_config = None  # Reset cache

        config = srv._load_tiers_config()
        assert config is not None
        assert "universal_floor" in config
        assert len(config["universal_floor"]["principles"]) == 1

    def test_load_tiers_config_missing_file(self, reset_server_state, test_settings):
        """Should return None when tiers.json doesn't exist."""
        import ai_governance_mcp.server as srv

        srv._state._settings = test_settings
        srv._state._tiers_config = None

        config = srv._load_tiers_config()
        assert config is None

    def test_load_tiers_config_caches(self, reset_server_state, test_settings):
        """Should cache config after first load."""
        import ai_governance_mcp.server as srv

        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(json.dumps({"universal_floor": {"principles": []}}))

        srv._state._settings = test_settings
        srv._state._tiers_config = None

        config1 = srv._load_tiers_config()
        config2 = srv._load_tiers_config()
        assert config1 is config2  # Same object (cached)

    def test_load_tiers_config_invalid_json(self, reset_server_state, test_settings):
        """Should return None for invalid JSON."""
        import ai_governance_mcp.server as srv

        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text("not valid json{{{")

        srv._state._settings = test_settings
        srv._state._tiers_config = None

        config = srv._load_tiers_config()
        assert config is None

    def test_build_universal_floor_all_types(self):
        """Should build items for principles, methods, and subagent check."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "test-principle", "check": "Did you check?"}],
                "methods": [{"ref": "§7.8", "id": None, "check": "Proportional?"}],
                "subagent_check": {"check": "Would a subagent help?"},
            }
        }
        items = _build_universal_floor(config)

        assert len(items) == 3
        assert items[0]["type"] == "principle"
        assert items[0]["id"] == "test-principle"
        assert items[1]["type"] == "method"
        assert items[1]["ref"] == "§7.8"
        assert items[2]["type"] == "subagent_check"

    def test_build_universal_floor_empty_config(self):
        """Should return empty list for empty config."""
        from ai_governance_mcp.server import _build_universal_floor

        items = _build_universal_floor({})
        assert items == []

    def test_build_universal_floor_no_subagent(self):
        """Should work without subagent_check."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
            }
        }
        items = _build_universal_floor(config)
        assert len(items) == 1
        assert items[0]["type"] == "principle"

    def test_build_universal_floor_includes_behavioral(self):
        """Should include behavioral_floor directives with type 'behavioral'."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
            },
            "behavioral_floor": {
                "directives": [
                    {"id": "recommend-not-ask", "check": "Presenting recommendations?"},
                    {"id": "freeform-dialogue", "check": "Using natural dialogue?"},
                ]
            },
        }
        items = _build_universal_floor(config)
        assert len(items) == 3  # 1 principle + 2 behavioral
        behavioral = [i for i in items if i["type"] == "behavioral"]
        assert len(behavioral) == 2
        assert behavioral[0]["id"] == "recommend-not-ask"
        assert behavioral[1]["id"] == "freeform-dialogue"

    def test_build_universal_floor_no_behavioral(self):
        """Should work without behavioral_floor section (backward compatible)."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {
                "principles": [{"id": "p1", "check": "check1"}],
                "methods": [],
                "subagent_check": {"check": "Would a subagent help?"},
            }
        }
        items = _build_universal_floor(config)
        assert len(items) == 2  # principle + subagent_check
        types = {i["type"] for i in items}
        assert "behavioral" not in types

    def test_build_universal_floor_empty_behavioral(self):
        """Should handle empty behavioral_floor directives list."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {"principles": [], "methods": []},
            "behavioral_floor": {"directives": []},
        }
        items = _build_universal_floor(config)
        assert items == []


class TestDomainFloor:
    """Tests for _build_domain_floor domain-specific floor injection."""

    def test_build_domain_floor_single_domain(self):
        """Should return items for a single detected domain."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [
                        {"id": "coding-context-ced", "check": "CED check"},
                        {"id": "coding-process-lpg", "check": "LPG check"},
                    ],
                    "methods": [],
                }
            }
        }
        items = _build_domain_floor(config, ["ai-coding"])
        assert len(items) == 2
        assert all(i["type"] == "domain_principle" for i in items)
        assert all(i["domain"] == "ai-coding" for i in items)
        assert items[0]["id"] == "coding-context-ced"
        assert items[1]["id"] == "coding-process-lpg"

    def test_build_domain_floor_no_domains_detected(self):
        """Should return empty list when no domains detected."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [{"id": "test", "check": "test"}],
                    "methods": [],
                }
            }
        }
        items = _build_domain_floor(config, [])
        assert items == []

    def test_build_domain_floor_domain_not_in_config(self):
        """Should return empty list when detected domain has no floor config."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [{"id": "test", "check": "test"}],
                    "methods": [],
                }
            }
        }
        items = _build_domain_floor(config, ["storytelling"])
        assert items == []

    def test_build_domain_floor_multiple_domains(self):
        """Should return items from all detected domains that have floors."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [
                        {"id": "coding-1", "check": "check 1"},
                        {"id": "coding-2", "check": "check 2"},
                    ],
                    "methods": [],
                },
                "storytelling": {
                    "principles": [{"id": "story-1", "check": "check 3"}],
                    "methods": [],
                },
            }
        }
        items = _build_domain_floor(config, ["ai-coding", "storytelling"])
        assert len(items) == 3
        ai_items = [i for i in items if i["domain"] == "ai-coding"]
        story_items = [i for i in items if i["domain"] == "storytelling"]
        assert len(ai_items) == 2
        assert len(story_items) == 1

    def test_build_domain_floor_no_domain_floors_section(self):
        """Should return empty list when tiers config has no domain_floors key."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {"universal_floor": {"principles": [], "methods": []}}
        items = _build_domain_floor(config, ["ai-coding"])
        assert items == []

    def test_build_domain_floor_empty_domain(self):
        """Should return empty list when domain floor has empty arrays."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {"domain_floors": {"ai-coding": {"principles": [], "methods": []}}}
        items = _build_domain_floor(config, ["ai-coding"])
        assert items == []

    def test_build_domain_floor_with_methods(self):
        """Should handle domain floor methods with ref field."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [],
                    "methods": [
                        {
                            "ref": "ai-coding §2.6",
                            "id": "coding-method-design-first",
                            "check": "Design-first check",
                        }
                    ],
                }
            }
        }
        items = _build_domain_floor(config, ["ai-coding"])
        assert len(items) == 1
        assert items[0]["type"] == "domain_method"
        assert items[0]["ref"] == "ai-coding §2.6"
        assert items[0]["id"] == "coding-method-design-first"
        assert items[0]["domain"] == "ai-coding"

    def test_build_domain_floor_includes_domain_field(self):
        """Every returned item must have a domain field."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "ai-coding": {
                    "principles": [{"id": "p1", "check": "c1"}],
                    "methods": [{"id": "m1", "check": "c2"}],
                }
            }
        }
        items = _build_domain_floor(config, ["ai-coding"])
        assert len(items) == 2
        assert all("domain" in i for i in items)
        assert all(i["domain"] == "ai-coding" for i in items)

    def test_build_domain_floor_skips_selection_criteria_string(self):
        """Should skip _selection_criteria string key in domain_floors."""
        from ai_governance_mcp.server import _build_domain_floor

        config = {
            "domain_floors": {
                "_selection_criteria": "A string, not a dict",
                "ai-coding": {
                    "principles": [{"id": "p1", "check": "c1"}],
                    "methods": [],
                },
            }
        }
        items = _build_domain_floor(config, ["ai-coding", "_selection_criteria"])
        assert len(items) == 1
        assert items[0]["domain"] == "ai-coding"


class TestUniversalFloorInEvaluateGovernance:
    """Tests for universal floor injection in evaluate_governance responses."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_universal_floor(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include universal_floor when tiers.json exists."""
        # Write tiers.json to test documents dir
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Epistemic check",
                            }
                        ],
                        "methods": [
                            {"ref": "§7.8", "id": None, "check": "Proportional check"}
                        ],
                        "subagent_check": {"check": "Subagent check"},
                    }
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new helper function"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    floor = parsed["universal_floor"]
                    assert len(floor) == 3
                    assert floor[0]["type"] == "principle"
                    assert floor[0]["check"] == "Epistemic check"
                    assert floor[1]["type"] == "method"
                    assert floor[2]["type"] == "subagent_check"

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_floor_without_tiers(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should not include universal_floor when tiers.json missing."""
        # No tiers.json written — should gracefully omit
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Format code with prettier"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" not in parsed

    @pytest.mark.asyncio
    async def test_universal_floor_separate_from_max_results(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Universal floor items should NOT reduce the max_results=10 retrieval count."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {"id": "floor-p1", "check": "check1"},
                            {"id": "floor-p2", "check": "check2"},
                        ],
                        "methods": [],
                    }
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor database module"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    # Floor items are separate
                    if "universal_floor" in parsed:
                        assert len(parsed["universal_floor"]) == 2

                    # relevant_principles still has up to 10
                    # (won't be reduced by floor items)
                    assert "relevant_principles" in parsed


class TestDomainFloorInEvaluateGovernance:
    """Tests for domain floor injection in evaluate_governance responses."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_domain_floor(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include domain_floor when domain is detected."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Epistemic check",
                            }
                        ],
                        "methods": [],
                    },
                    "domain_floors": {
                        "ai-coding": {
                            "principles": [{"id": "test-ced", "check": "CED check"}],
                            "methods": [],
                        }
                    },
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new helper function"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    # Domain floor appears if ai-coding domain was detected
                    if parsed.get("domain_floor"):
                        assert any(
                            i["id"] == "test-ced" for i in parsed["domain_floor"]
                        )

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_domain_floor_without_detection(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should omit domain_floor when no matching domain detected."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-core-systemic-thinking",
                                "check": "Root cause check",
                            }
                        ],
                        "methods": [],
                    },
                    "domain_floors": {
                        "nonexistent-domain-xyz": {
                            "principles": [{"id": "should-not-appear", "check": "c"}],
                            "methods": [],
                        }
                    },
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new helper function"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    domain_floor = parsed.get("domain_floor", [])
                    assert not any(
                        i.get("id") == "should-not-appear" for i in domain_floor
                    )

    @pytest.mark.asyncio
    async def test_evaluate_governance_domain_floor_separate_from_max_results(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """domain_floor items should not reduce relevant_principles count."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "c",
                            }
                        ],
                        "methods": [],
                    },
                    "domain_floors": {
                        "ai-coding": {
                            "principles": [
                                {"id": "df-1", "check": "c1"},
                                {"id": "df-2", "check": "c2"},
                            ],
                            "methods": [],
                        }
                    },
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor database module"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    if "domain_floor" in parsed:
                        assert len(parsed["domain_floor"]) == 2

                    assert "relevant_principles" in parsed


class TestTiersPrincipleIdValidation:
    """CI validation: all principle IDs in tiers.json must exist in the index."""

    def test_tiers_principle_ids_exist_in_index(self):
        """Every principle ID in tiers.json must exist in the production index."""
        tiers_path = Path(__file__).parent.parent / "documents" / "tiers.json"
        index_path = Path(__file__).parent.parent / "index" / "global_index.json"

        if not tiers_path.exists():
            pytest.skip("tiers.json not found")
        if not index_path.exists():
            pytest.skip("Production index not found")

        with open(tiers_path) as f:
            tiers = json.load(f)
        with open(index_path) as f:
            index = json.load(f)

        # Collect all principle IDs from index
        all_ids = set()
        for domain_data in index.get("domains", {}).values():
            for p in domain_data.get("principles", []):
                all_ids.add(p["id"])

        # Validate tier principle IDs
        floor = tiers.get("universal_floor", {})
        missing = []
        for p in floor.get("principles", []):
            pid = p.get("id")
            if pid and pid not in all_ids:
                missing.append(pid)

        # Also validate method IDs that reference principles
        for m in floor.get("methods", []):
            mid = m.get("id")
            if mid and mid not in all_ids:
                missing.append(mid)

        # Validate domain floor IDs
        for domain_name, domain_floor in tiers.get("domain_floors", {}).items():
            if not isinstance(domain_floor, dict):
                continue
            for p in domain_floor.get("principles", []):
                pid = p.get("id")
                if pid and pid not in all_ids:
                    missing.append(f"{pid} (domain_floor:{domain_name})")
            for m in domain_floor.get("methods", []):
                mid = m.get("id")
                if mid and mid not in all_ids:
                    missing.append(f"{mid} (domain_floor:{domain_name})")

        # Validate critical_5 principle_refs (only those that are principle IDs,
        # not behavioral directives or method references)
        behavioral_ids = {
            d.get("id") for d in tiers.get("behavioral_floor", {}).get("directives", [])
        }
        for item in tiers.get("critical_5", {}).get("items", []):
            ref = item.get("principle_ref", "")
            if ref and ref not in behavioral_ids and ref not in all_ids:
                missing.append(f"{ref} (critical_5)")

        assert not missing, (
            f"tiers.json references IDs not in index: {missing}. "
            f"Update tiers.json or rebuild index."
        )


# =============================================================================
# UI/UX Domain Integration Tests
# =============================================================================


class TestAutoLogGovernanceReasoning:
    """Tests for automatic reasoning logging in evaluate_governance."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_auto_logs_reasoning(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should auto-log a reasoning entry."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new logging function"},
                    )

                    # Should have auto-logged a reasoning entry
                    assert len(server_module._reasoning_log) == 1
                    entry = server_module._reasoning_log[0]
                    assert entry.auto_generated is True
                    assert entry.final_decision in [
                        "PROCEED",
                        "REVIEW",
                        "ESCALATE",
                    ]
                    assert len(entry.reasoning_entries) >= 1

    @pytest.mark.asyncio
    async def test_auto_log_audit_id_matches(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Auto-logged reasoning should share audit_id with audit entry."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Test action for audit ID match"},
                    )

                    assert len(server_module._audit_log) == 1
                    assert len(server_module._reasoning_log) == 1
                    assert (
                        server_module._audit_log[0].audit_id
                        == server_module._reasoning_log[0].audit_id
                    )

    @pytest.mark.asyncio
    async def test_manual_log_still_works_after_auto_log(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Manual log_governance_reasoning should still work alongside auto-log."""
        from ai_governance_mcp import server as server_module

        server_module._reasoning_log.clear()
        server_module._audit_log.clear()

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Test action for manual log"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))
                    audit_id = parsed["audit_id"]

                    # Auto-log should exist
                    assert len(server_module._reasoning_log) == 1
                    assert server_module._reasoning_log[0].auto_generated is True

                    # Manual log should also work
                    await call_tool(
                        "log_governance_reasoning",
                        {
                            "audit_id": audit_id,
                            "reasoning": [
                                {
                                    "principle_id": "test-principle",
                                    "status": "COMPLIES",
                                    "reasoning": "Manual detailed analysis",
                                }
                            ],
                            "final_decision": "PROCEED",
                        },
                    )

                    # Both entries should exist
                    assert len(server_module._reasoning_log) == 2
                    assert server_module._reasoning_log[0].auto_generated is True
                    assert server_module._reasoning_log[1].auto_generated is False


class TestCitePrinciplesInBehavioralFloor:
    """Tests for cite-principles directive in tiers.json behavioral_floor."""

    def test_cite_principles_in_tiers_json(self):
        """tiers.json should include cite-principles directive."""
        tiers_path = Path(__file__).parent.parent / "documents" / "tiers.json"
        with open(tiers_path) as f:
            config = json.load(f)

        directives = config["behavioral_floor"]["directives"]
        ids = [d["id"] for d in directives]
        assert "cite-principles" in ids

    def test_build_universal_floor_includes_cite_principles(self):
        """_build_universal_floor should include cite-principles behavioral directive."""
        from ai_governance_mcp.server import _build_universal_floor

        config = {
            "universal_floor": {"principles": [], "methods": []},
            "behavioral_floor": {
                "directives": [
                    {"id": "recommend-not-ask", "check": "Presenting recommendations?"},
                    {"id": "freeform-dialogue", "check": "Using natural dialogue?"},
                    {"id": "cite-principles", "check": "Referencing principle IDs?"},
                ]
            },
        }
        items = _build_universal_floor(config)
        behavioral = [i for i in items if i["type"] == "behavioral"]
        assert len(behavioral) == 3
        assert behavioral[2]["id"] == "cite-principles"


class TestCritical5:
    """Tests for _build_critical_5 scaffold-format reasoning items."""

    def test_build_critical_5_all_items(self):
        """Should build scaffold-format items from critical_5 section."""
        from ai_governance_mcp.server import _build_critical_5

        config = {
            "critical_5": {
                "items": [
                    {
                        "id": "structural-cause",
                        "principle_ref": "meta-core-systemic-thinking",
                        "label": "Find the structural cause",
                        "scaffold": "What system produced this? Name it.",
                    },
                    {
                        "id": "verify-before-acting",
                        "principle_ref": "meta-quality-verification-validation",
                        "label": "Verify before acting",
                        "scaffold": "What assumption are you making?",
                    },
                ]
            }
        }
        items = _build_critical_5(config)

        assert len(items) == 2
        assert items[0]["type"] == "critical"
        assert items[0]["id"] == "structural-cause"
        assert items[0]["principle_ref"] == "meta-core-systemic-thinking"
        assert items[0]["label"] == "Find the structural cause"
        assert items[0]["scaffold"] == "What system produced this? Name it."

    def test_build_critical_5_empty_config(self):
        """Should return empty list for empty config."""
        from ai_governance_mcp.server import _build_critical_5

        items = _build_critical_5({})
        assert items == []

    def test_build_critical_5_missing_section(self):
        """Should return empty list when critical_5 section is absent."""
        from ai_governance_mcp.server import _build_critical_5

        config = {"universal_floor": {"principles": []}}
        items = _build_critical_5(config)
        assert items == []

    def test_build_critical_5_empty_items(self):
        """Should return empty list when items array is empty."""
        from ai_governance_mcp.server import _build_critical_5

        config = {"critical_5": {"items": []}}
        items = _build_critical_5(config)
        assert items == []

    def test_build_critical_5_preserves_all_fields(self):
        """Each item should have type, id, principle_ref, label, scaffold."""
        from ai_governance_mcp.server import _build_critical_5

        config = {
            "critical_5": {
                "items": [
                    {
                        "id": "test-id",
                        "principle_ref": "test-principle",
                        "label": "Test Label",
                        "scaffold": "Test scaffold prompt.",
                    }
                ]
            }
        }
        items = _build_critical_5(config)
        assert len(items) == 1
        item = items[0]
        assert set(item.keys()) == {"type", "id", "principle_ref", "label", "scaffold"}


class TestCritical5InEvaluateGovernance:
    """Tests for critical_5 scaffold injection in evaluate_governance responses."""

    @pytest.mark.asyncio
    async def test_evaluate_governance_includes_critical_5(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should include critical_5 when tiers.json has that section."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [
                            {
                                "id": "meta-safety-transparent-limitations",
                                "check": "Epistemic check",
                            }
                        ],
                        "methods": [],
                    },
                    "critical_5": {
                        "items": [
                            {
                                "id": "structural-cause",
                                "principle_ref": "meta-core-systemic-thinking",
                                "label": "Find the structural cause",
                                "scaffold": "What system produced this?",
                            },
                            {
                                "id": "verify-before-acting",
                                "principle_ref": "meta-quality-verification-validation",
                                "label": "Verify before acting",
                                "scaffold": "What assumption are you making?",
                            },
                        ]
                    },
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add a new helper function"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "critical_5" in parsed
                    c5 = parsed["critical_5"]
                    assert len(c5) == 2
                    assert c5[0]["type"] == "critical"
                    assert c5[0]["id"] == "structural-cause"
                    assert c5[0]["label"] == "Find the structural cause"
                    assert c5[0]["scaffold"] == "What system produced this?"
                    assert c5[0]["principle_ref"] == "meta-core-systemic-thinking"

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_critical_5_without_tiers(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should not include critical_5 when tiers.json missing."""
        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Format code"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "critical_5" not in parsed

    @pytest.mark.asyncio
    async def test_evaluate_governance_no_critical_5_without_section(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """evaluate_governance should not include critical_5 when tiers.json lacks that section."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [{"id": "floor-p1", "check": "check1"}],
                        "methods": [],
                    }
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Refactor module"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    assert "critical_5" not in parsed

    @pytest.mark.asyncio
    async def test_critical_5_coexists_with_universal_floor(
        self,
        reset_server_state,
        test_settings,
        saved_index,
        mock_embedder,
        mock_reranker,
    ):
        """Both critical_5 and universal_floor should appear — no breaking change."""
        tiers_path = test_settings.documents_path / "tiers.json"
        tiers_path.write_text(
            json.dumps(
                {
                    "universal_floor": {
                        "principles": [{"id": "floor-p1", "check": "Floor check"}],
                        "methods": [],
                    },
                    "critical_5": {
                        "items": [
                            {
                                "id": "test-scaffold",
                                "principle_ref": "test-ref",
                                "label": "Test",
                                "scaffold": "Demonstrate this.",
                            }
                        ]
                    },
                }
            )
        )

        mock_st = Mock(return_value=mock_embedder)
        mock_ce = Mock(return_value=mock_reranker)

        with patch(
            "ai_governance_mcp.server.load_settings", return_value=test_settings
        ):
            with patch("sentence_transformers.SentenceTransformer", mock_st):
                with patch("sentence_transformers.CrossEncoder", mock_ce):
                    from ai_governance_mcp.server import call_tool

                    result = await call_tool(
                        "evaluate_governance",
                        {"planned_action": "Add tests"},
                    )
                    parsed = json.loads(extract_json_from_response(result[0].text))

                    assert "universal_floor" in parsed
                    assert "critical_5" in parsed
                    # Verify formats are different
                    assert parsed["universal_floor"][0]["type"] == "principle"
                    assert parsed["critical_5"][0]["type"] == "critical"
                    assert "scaffold" in parsed["critical_5"][0]
                    assert "scaffold" not in parsed["universal_floor"][0]
