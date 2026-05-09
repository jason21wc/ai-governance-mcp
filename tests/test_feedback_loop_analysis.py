"""Tests for scripts/analyze_feedback_loop.py — feedback loop analysis."""

import json
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from analyze_feedback_loop import (
    read_jsonl_logs,
    filter_by_time_range,
    compute_m001_influence_rate,
    compute_m003_relevance_trend,
    compute_m004_s_series_rate,
    detect_dead_principles,
    detect_retrieval_gaps,
    detect_false_positive_patterns,
    compute_maturity_proposals,
    generate_recommendations,
    run_analysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    """Write a list of dicts as JSONL to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _make_audit_entry(
    assessment="PROCEED",
    s_series_triggered=False,
    principles_consulted=None,
    timestamp=None,
    audit_id=None,
    action="test action",
):
    return {
        "audit_id": audit_id or "gov-test",
        "timestamp": timestamp or "2026-05-01T00:00:00+00:00",
        "action": action,
        "assessment": assessment,
        "principles_consulted": principles_consulted or [],
        "methods_surfaced": [],
        "s_series_triggered": s_series_triggered,
        "confidence": "high",
    }


def _make_query_entry(
    query="test query",
    principles_returned=None,
    top_confidence="low",
    timestamp=None,
):
    return {
        "timestamp": timestamp or "2026-05-01T00:00:00+00:00",
        "query": query,
        "domains_detected": [],
        "principles_returned": principles_returned or [],
        "methods_returned": [],
        "s_series_triggered": False,
        "retrieval_time_ms": 100.0,
        "top_confidence": top_confidence,
    }


def _make_reasoning_entry(
    audit_id="gov-test", principle_id="meta-test", status="COMPLIES"
):
    return {
        "audit_id": audit_id,
        "timestamp": "2026-05-01T00:00:00+00:00",
        "reasoning_entries": [
            {"principle_id": principle_id, "status": status, "reasoning": "test"}
        ],
        "final_decision": "PROCEED",
        "modifications_applied": [],
        "auto_generated": True,
    }


# ===========================================================================
# Phase 1: Log reader + time range filtering
# ===========================================================================


class TestReadJsonlLogs:
    """Tests for read_jsonl_logs()."""

    def test_reads_primary_file(self, tmp_path):
        entries = [{"a": 1}, {"a": 2}]
        _write_jsonl(tmp_path / "test.jsonl", entries)
        result = read_jsonl_logs(tmp_path, "test")
        assert len(result) == 2
        assert result[0]["a"] == 1
        assert result[1]["a"] == 2

    def test_reads_rotated_files_in_chronological_order(self, tmp_path):
        _write_jsonl(tmp_path / "test.jsonl", [{"seq": 3}])
        _write_jsonl(tmp_path / "test.jsonl.1", [{"seq": 2}])
        _write_jsonl(tmp_path / "test.jsonl.2", [{"seq": 1}])
        result = read_jsonl_logs(tmp_path, "test")
        assert [e["seq"] for e in result] == [1, 2, 3]

    def test_returns_empty_when_file_missing(self, tmp_path):
        result = read_jsonl_logs(tmp_path, "nonexistent")
        assert result == []

    def test_skips_malformed_lines(self, tmp_path):
        path = tmp_path / "test.jsonl"
        path.write_text('{"good": true}\nnot json\n{"also_good": true}\n')
        result = read_jsonl_logs(tmp_path, "test")
        assert len(result) == 2
        assert result[0]["good"] is True
        assert result[1]["also_good"] is True

    def test_skips_empty_lines(self, tmp_path):
        path = tmp_path / "test.jsonl"
        path.write_text('{"a": 1}\n\n{"a": 2}\n')
        result = read_jsonl_logs(tmp_path, "test")
        assert len(result) == 2

    def test_handles_only_rotated_files(self, tmp_path):
        _write_jsonl(tmp_path / "test.jsonl.1", [{"seq": 1}])
        result = read_jsonl_logs(tmp_path, "test")
        assert len(result) == 1
        assert result[0]["seq"] == 1


class TestFilterByTimeRange:
    """Tests for filter_by_time_range()."""

    @pytest.fixture
    def entries(self):
        return [
            {"timestamp": "2026-05-01T00:00:00+00:00"},
            {"timestamp": "2026-05-05T00:00:00+00:00"},
            {"timestamp": "2026-05-10T00:00:00+00:00"},
        ]

    def test_no_filter_returns_all(self, entries):
        result = filter_by_time_range(entries)
        assert len(result) == 3

    def test_start_filter(self, entries):
        result = filter_by_time_range(entries, start="2026-05-04")
        assert len(result) == 2

    def test_end_filter(self, entries):
        result = filter_by_time_range(entries, end="2026-05-06")
        assert len(result) == 2

    def test_both_filters(self, entries):
        result = filter_by_time_range(entries, start="2026-05-04", end="2026-05-06")
        assert len(result) == 1

    def test_empty_input(self):
        result = filter_by_time_range([])
        assert result == []


# ===========================================================================
# Phase 2: Effectiveness metrics
# ===========================================================================


class TestM001InfluenceRate:
    """Tests for compute_m001_influence_rate()."""

    def test_all_proceed(self):
        entries = [_make_audit_entry(assessment="PROCEED") for _ in range(10)]
        result = compute_m001_influence_rate(entries)
        assert result["value"] == 0.0
        assert result["total"] == 10
        assert result["insufficient_data"] is False

    def test_mixed_assessments(self):
        entries = [
            *[_make_audit_entry(assessment="PROCEED") for _ in range(8)],
            _make_audit_entry(assessment="ESCALATE"),
            _make_audit_entry(assessment="REVIEW"),
        ]
        result = compute_m001_influence_rate(entries)
        assert result["value"] == pytest.approx(0.2)
        assert result["breakdown"]["PROCEED"] == 8
        assert result["breakdown"]["ESCALATE"] == 1
        assert result["breakdown"]["REVIEW"] == 1

    def test_empty_list(self):
        result = compute_m001_influence_rate([])
        assert result["value"] is None
        assert result["total"] == 0
        assert result["insufficient_data"] is True

    def test_review_counts_as_influenced(self):
        """REVIEW assessment should count toward M-001 influence numerator (#155)."""
        entries = [
            *[_make_audit_entry(assessment="PROCEED") for _ in range(7)],
            _make_audit_entry(assessment="REVIEW"),
            _make_audit_entry(assessment="ESCALATE"),
            _make_audit_entry(assessment="REVIEW"),
        ]
        result = compute_m001_influence_rate(entries)
        assert result["value"] == pytest.approx(0.3)
        assert result["breakdown"]["REVIEW"] == 2
        assert result["breakdown"]["ESCALATE"] == 1

    def test_old_proceed_with_principles_retroactive(self):
        """Old PROCEED entries with principles_consulted should count as influenced (#155)."""
        entries = [
            _make_audit_entry(assessment="PROCEED", principles_consulted=[]),
            _make_audit_entry(assessment="PROCEED", principles_consulted=["meta-C1"]),
            _make_audit_entry(
                assessment="PROCEED", principles_consulted=["meta-C1", "coding-Q1"]
            ),
            _make_audit_entry(assessment="ESCALATE"),
        ]
        result = compute_m001_influence_rate(entries)
        # 2 old PROCEEDs with principles + 1 ESCALATE = 3 influenced out of 4
        assert result["value"] == pytest.approx(0.75)


class TestM003RelevanceTrend:
    """Tests for compute_m003_relevance_trend()."""

    def test_all_low(self):
        entries = [_make_query_entry(top_confidence="low") for _ in range(10)]
        result = compute_m003_relevance_trend(entries)
        assert result["current_avg"] == pytest.approx(0.2)
        assert result["insufficient_data"] is False

    def test_all_null_skipped(self):
        entries = [_make_query_entry(top_confidence=None) for _ in range(10)]
        result = compute_m003_relevance_trend(entries)
        assert result["current_avg"] is None
        assert result["insufficient_data"] is True

    def test_mixed_confidences(self):
        entries = [
            _make_query_entry(top_confidence="high"),
            _make_query_entry(top_confidence="medium"),
            _make_query_entry(top_confidence="low"),
        ]
        result = compute_m003_relevance_trend(entries)
        expected = (1.0 + 0.5 + 0.2) / 3
        assert result["current_avg"] == pytest.approx(expected, rel=0.01)

    def test_trend_improving(self):
        entries = [
            *[
                _make_query_entry(
                    top_confidence="low", timestamp=f"2026-05-0{i}T00:00:00+00:00"
                )
                for i in range(1, 4)
            ],
            *[
                _make_query_entry(
                    top_confidence="high", timestamp=f"2026-05-0{i}T00:00:00+00:00"
                )
                for i in range(4, 7)
            ],
        ]
        result = compute_m003_relevance_trend(entries)
        assert result["trend"] == "improving"

    def test_trend_stable(self):
        entries = [_make_query_entry(top_confidence="low") for _ in range(10)]
        result = compute_m003_relevance_trend(entries)
        assert result["trend"] == "stable"


class TestM004SSeriesRate:
    """Tests for compute_m004_s_series_rate()."""

    def test_no_triggers(self):
        entries = [_make_audit_entry(s_series_triggered=False) for _ in range(10)]
        result = compute_m004_s_series_rate(entries)
        assert result["value"] == 0.0
        assert result["insufficient_data"] is False

    def test_some_triggers(self):
        entries = [
            *[_make_audit_entry(s_series_triggered=False) for _ in range(8)],
            _make_audit_entry(
                s_series_triggered=True,
                principles_consulted=["meta-safety-transparent-limitations"],
            ),
            _make_audit_entry(
                s_series_triggered=True,
                principles_consulted=["meta-safety-non-maleficence"],
            ),
        ]
        result = compute_m004_s_series_rate(entries)
        assert result["value"] == pytest.approx(0.2)
        assert result["by_principle"]["meta-safety-transparent-limitations"] == 1
        assert result["by_principle"]["meta-safety-non-maleficence"] == 1

    def test_empty_list(self):
        result = compute_m004_s_series_rate([])
        assert result["value"] is None
        assert result["insufficient_data"] is True


# ===========================================================================
# Phase 3: Pattern detection
# ===========================================================================


class TestDeadPrincipleDetection:
    """Tests for detect_dead_principles()."""

    def test_all_principles_seen(self):
        entries = [
            _make_query_entry(principles_returned=["p1", "p2"]),
            _make_query_entry(principles_returned=["p3"]),
        ]
        result = detect_dead_principles(entries, {"p1", "p2", "p3"})
        assert result == []

    def test_principle_never_seen(self):
        entries = [_make_query_entry(principles_returned=["p1"])]
        result = detect_dead_principles(entries, {"p1", "p2"})
        assert len(result) == 1
        assert result[0]["id"] == "p2"
        assert result[0]["last_seen"] is None

    def test_principle_not_seen_recently(self):
        entries = [
            _make_query_entry(
                principles_returned=["p1"], timestamp="2026-01-01T00:00:00+00:00"
            ),
            _make_query_entry(
                principles_returned=["p2"], timestamp="2026-05-01T00:00:00+00:00"
            ),
        ]
        result = detect_dead_principles(entries, {"p1", "p2"}, days_threshold=30)
        assert len(result) == 1
        assert result[0]["id"] == "p1"
        assert result[0]["last_seen"] == "2026-01-01T00:00:00+00:00"

    def test_empty_queries(self):
        result = detect_dead_principles([], {"p1", "p2"})
        assert len(result) == 2
        assert result[0].get("insufficient_data") is True


class TestRetrievalGapDetection:
    """Tests for detect_retrieval_gaps()."""

    def test_consistently_low_query(self):
        entries = [
            _make_query_entry(query="same query", top_confidence="low")
            for _ in range(5)
        ]
        result = detect_retrieval_gaps(entries, min_occurrences=3)
        assert len(result) == 1
        assert result[0]["count"] == 5

    def test_mixed_confidence_excluded(self):
        entries = [
            *[_make_query_entry(query="mixed", top_confidence="low") for _ in range(3)],
            _make_query_entry(query="mixed", top_confidence="high"),
        ]
        result = detect_retrieval_gaps(entries, min_occurrences=3)
        assert len(result) == 0

    def test_below_min_occurrences(self):
        entries = [_make_query_entry(query="rare", top_confidence="low")]
        result = detect_retrieval_gaps(entries, min_occurrences=3)
        assert result == []

    def test_empty_input(self):
        result = detect_retrieval_gaps([])
        assert result == []


class TestFalsePositivePatterns:
    """Tests for detect_false_positive_patterns()."""

    def test_frequent_escalation_principle(self):
        audit_entries = [
            _make_audit_entry(
                assessment="ESCALATE",
                s_series_triggered=True,
                principles_consulted=["meta-safety-transparent-limitations"],
                audit_id=f"gov-{i}",
            )
            for i in range(5)
        ]
        reasoning_entries = [
            _make_reasoning_entry(
                audit_id=f"gov-{i}",
                principle_id="meta-safety-transparent-limitations",
                status="VIOLATION",
            )
            for i in range(5)
        ]
        result = detect_false_positive_patterns(
            audit_entries, reasoning_entries, min_triggers=3
        )
        assert len(result) == 1
        assert result[0]["principle_id"] == "meta-safety-transparent-limitations"
        assert result[0]["trigger_count"] == 5

    def test_below_threshold(self):
        audit_entries = [
            _make_audit_entry(
                assessment="ESCALATE",
                s_series_triggered=True,
                principles_consulted=["meta-test"],
                audit_id="gov-1",
            )
        ]
        result = detect_false_positive_patterns(audit_entries, [], min_triggers=3)
        assert result == []

    def test_empty_inputs(self):
        result = detect_false_positive_patterns([], [])
        assert result == []


class TestMaturityProposals:
    """Tests for compute_maturity_proposals()."""

    def test_empty_inputs_returns_insufficient_data(self):
        result = compute_maturity_proposals([], [], [])
        assert result["proposals"] == []
        assert result["field_present_entries"] == 0

    def test_promotion_candidate_seedling_retrieved_3_plus(self):
        query_entries = [
            {"references_returned": ["ref-ai-coding-foo"]},
            {"references_returned": ["ref-ai-coding-foo", "ref-ai-coding-bar"]},
            {"references_returned": ["ref-ai-coding-foo"]},
        ] + [{"references_returned": []} for _ in range(17)]
        reference_entries = [
            {"id": "ref-ai-coding-foo", "maturity": "seedling"},
            {"id": "ref-ai-coding-bar", "maturity": "seedling"},
        ]
        result = compute_maturity_proposals(query_entries, [], reference_entries)
        promo_ids = [
            p["reference_id"] for p in result["proposals"] if p["type"] == "promotion"
        ]
        assert "ref-ai-coding-foo" in promo_ids
        assert "ref-ai-coding-bar" not in promo_ids
        assert result["retrieval_counts"]["ref-ai-coding-foo"] == 3
        assert result["retrieval_counts"]["ref-ai-coding-bar"] == 1

    def test_decay_candidate_zero_retrievals(self):
        query_entries = [{"references_returned": []} for _ in range(20)]
        reference_entries = [
            {"id": "ref-ai-coding-unused", "maturity": "seedling"},
        ]
        result = compute_maturity_proposals(query_entries, [], reference_entries)
        decay_ids = [
            p["reference_id"] for p in result["proposals"] if p["type"] == "decay"
        ]
        assert "ref-ai-coding-unused" in decay_ids

    def test_insufficient_data_below_threshold(self):
        query_entries = [{"references_returned": []} for _ in range(5)]
        reference_entries = [
            {"id": "ref-ai-coding-foo", "maturity": "seedling"},
        ]
        result = compute_maturity_proposals(query_entries, [], reference_entries)
        assert result["proposals"] == []
        assert result["field_present_entries"] == 5

    def test_backward_compat_old_entries_without_field(self):
        old_entries = [{"query": "old query", "principles_returned": ["p1"]}] * 50
        new_entries = [
            {"references_returned": ["ref-ai-coding-foo"]},
            {"references_returned": ["ref-ai-coding-foo"]},
            {"references_returned": ["ref-ai-coding-foo"]},
        ] + [{"references_returned": []} for _ in range(17)]
        reference_entries = [
            {"id": "ref-ai-coding-foo", "maturity": "seedling"},
            {"id": "ref-ai-coding-bar", "maturity": "seedling"},
        ]
        result = compute_maturity_proposals(
            old_entries + new_entries, [], reference_entries
        )
        assert result["field_present_entries"] == 20
        assert result["retrieval_counts"]["ref-ai-coding-foo"] == 3
        promo_ids = [
            p["reference_id"] for p in result["proposals"] if p["type"] == "promotion"
        ]
        assert "ref-ai-coding-foo" in promo_ids

    def test_budding_not_promoted_by_count_alone(self):
        query_entries = [{"references_returned": ["ref-already-budding"]}] * 5 + [
            {"references_returned": []} for _ in range(15)
        ]
        reference_entries = [
            {"id": "ref-already-budding", "maturity": "budding"},
        ]
        result = compute_maturity_proposals(query_entries, [], reference_entries)
        promo_ids = [
            p["reference_id"] for p in result["proposals"] if p["type"] == "promotion"
        ]
        assert "ref-already-budding" not in promo_ids


# ===========================================================================
# Phase 4: Recommendations + pipeline
# ===========================================================================


class TestGenerateRecommendations:
    """Tests for generate_recommendations()."""

    def test_dead_principles_produce_recommendations(self):
        analysis = {
            "dead_principles": [
                {"id": "meta-test", "last_seen": None, "days_inactive": None}
            ],
            "false_positives": [],
            "retrieval_gaps": [],
        }
        result = generate_recommendations(analysis)
        assert len(result) == 1
        assert result[0]["type"] == "dead_principle"
        assert "meta-test" in result[0]["target"]

    def test_fp_patterns_produce_recommendations(self):
        analysis = {
            "dead_principles": [],
            "false_positives": [
                {
                    "principle_id": "meta-safety-transparent-limitations",
                    "trigger_count": 10,
                }
            ],
            "retrieval_gaps": [],
        }
        result = generate_recommendations(analysis)
        assert len(result) == 1
        assert result[0]["type"] == "false_positive"

    def test_retrieval_gaps_produce_recommendations(self):
        analysis = {
            "dead_principles": [],
            "false_positives": [],
            "retrieval_gaps": [
                {"query_pattern": "test query", "avg_confidence": 0.2, "count": 5}
            ],
        }
        result = generate_recommendations(analysis)
        assert len(result) == 1
        assert result[0]["type"] == "retrieval_gap"

    def test_no_issues_empty(self):
        analysis = {"dead_principles": [], "false_positives": [], "retrieval_gaps": []}
        result = generate_recommendations(analysis)
        assert result == []


class TestRunAnalysis:
    """Tests for run_analysis() — full pipeline."""

    def test_full_pipeline(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        _write_jsonl(
            log_dir / "governance_audit.jsonl",
            [
                _make_audit_entry(assessment="PROCEED"),
                _make_audit_entry(
                    assessment="ESCALATE",
                    s_series_triggered=True,
                    principles_consulted=["meta-safety-test"],
                ),
            ],
        )
        _write_jsonl(
            log_dir / "queries.jsonl",
            [_make_query_entry(principles_returned=["p1"], top_confidence="low")],
        )
        _write_jsonl(
            log_dir / "governance_reasoning.jsonl",
            [_make_reasoning_entry()],
        )

        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index = {
            "domains": {
                "test": {
                    "principles": [{"id": "p1"}, {"id": "p2"}],
                    "methods": [],
                    "references": [],
                }
            }
        }
        (index_dir / "global_index.json").write_text(json.dumps(index))

        output_path = tmp_path / "output.json"
        result = run_analysis(log_dir, index_dir, output_path)

        assert "computed_at" in result
        assert "time_range" in result
        assert "log_stats" in result
        assert result["log_stats"]["audit_entries"] == 2
        assert result["log_stats"]["query_entries"] == 1
        assert result["log_stats"]["feedback_entries"] == 0
        assert "effectiveness_metrics" in result
        assert "dead_principles" in result
        assert "false_positives" in result
        assert "retrieval_gaps" in result
        assert "maturity_proposals" in result
        assert "actionable_recommendations" in result

        assert output_path.exists()
        written = json.loads(output_path.read_text())
        assert written["computed_at"] == result["computed_at"]

    def test_handles_missing_feedback_gracefully(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        _write_jsonl(log_dir / "governance_audit.jsonl", [_make_audit_entry()])
        _write_jsonl(log_dir / "queries.jsonl", [_make_query_entry()])
        _write_jsonl(log_dir / "governance_reasoning.jsonl", [])

        index_dir = tmp_path / "index"
        index_dir.mkdir()
        (index_dir / "global_index.json").write_text(json.dumps({"domains": {}}))

        output_path = tmp_path / "output.json"
        result = run_analysis(log_dir, index_dir, output_path)
        assert result["log_stats"]["feedback_entries"] == 0
