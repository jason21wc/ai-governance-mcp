"""Unit tests for feedback loop analysis handler (thin reader)."""

import json
from datetime import datetime, timedelta, timezone

import pytest


class TestAnalyzeFeedbackLoop:
    """Tests for analyze_feedback_loop tool handler."""

    @pytest.mark.asyncio
    async def test_returns_precomputed_analysis(self, tmp_path, monkeypatch):
        from ai_governance_mcp.server.handlers.analysis import (
            _handle_analyze_feedback_loop,
        )

        analysis = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "effectiveness_metrics": {"m001": {"influence_rate": 0.175}},
            "actionable_recommendations": [],
        }
        analysis_file = tmp_path / "feedback_loop_analysis.json"
        analysis_file.write_text(json.dumps(analysis))

        monkeypatch.setattr(
            "ai_governance_mcp.server.handlers.analysis._get_analysis_path",
            lambda: analysis_file,
        )

        result = await _handle_analyze_feedback_loop({})
        assert len(result) == 1
        response = json.loads(result[0].text.split("\n---")[0])
        assert response["effectiveness_metrics"]["m001"]["influence_rate"] == 0.175

    @pytest.mark.asyncio
    async def test_missing_file_returns_error(self, tmp_path, monkeypatch):
        from ai_governance_mcp.server.handlers.analysis import (
            _handle_analyze_feedback_loop,
        )

        monkeypatch.setattr(
            "ai_governance_mcp.server.handlers.analysis._get_analysis_path",
            lambda: tmp_path / "nonexistent.json",
        )

        result = await _handle_analyze_feedback_loop({})
        text = result[0].text
        assert "not found" in text.lower() or "run scripts" in text.lower()

    @pytest.mark.asyncio
    async def test_stale_file_warns(self, tmp_path, monkeypatch):
        from ai_governance_mcp.server.handlers.analysis import (
            _handle_analyze_feedback_loop,
        )

        old_date = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()
        analysis = {
            "computed_at": old_date,
            "effectiveness_metrics": {},
            "actionable_recommendations": [],
        }
        analysis_file = tmp_path / "feedback_loop_analysis.json"
        analysis_file.write_text(json.dumps(analysis))

        monkeypatch.setattr(
            "ai_governance_mcp.server.handlers.analysis._get_analysis_path",
            lambda: analysis_file,
        )

        result = await _handle_analyze_feedback_loop({})
        text = result[0].text
        assert "stale" in text.lower() or "outdated" in text.lower()

    @pytest.mark.asyncio
    async def test_section_filter(self, tmp_path, monkeypatch):
        from ai_governance_mcp.server.handlers.analysis import (
            _handle_analyze_feedback_loop,
        )

        analysis = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "effectiveness_metrics": {"m001": {"influence_rate": 0.175}},
            "dead_principles": {"count": 0, "items": []},
            "actionable_recommendations": [],
        }
        analysis_file = tmp_path / "feedback_loop_analysis.json"
        analysis_file.write_text(json.dumps(analysis))

        monkeypatch.setattr(
            "ai_governance_mcp.server.handlers.analysis._get_analysis_path",
            lambda: analysis_file,
        )

        result = await _handle_analyze_feedback_loop(
            {"section": "effectiveness_metrics"}
        )
        response = json.loads(result[0].text.split("\n---")[0])
        assert "effectiveness_metrics" in response
        assert "dead_principles" not in response

    @pytest.mark.asyncio
    async def test_invalid_section_returns_error(self, tmp_path, monkeypatch):
        from ai_governance_mcp.server.handlers.analysis import (
            _handle_analyze_feedback_loop,
        )

        analysis = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "effectiveness_metrics": {},
        }
        analysis_file = tmp_path / "feedback_loop_analysis.json"
        analysis_file.write_text(json.dumps(analysis))

        monkeypatch.setattr(
            "ai_governance_mcp.server.handlers.analysis._get_analysis_path",
            lambda: analysis_file,
        )

        result = await _handle_analyze_feedback_loop({"section": "nonexistent_key"})
        text = result[0].text
        assert "not found" in text.lower() or "available" in text.lower()
