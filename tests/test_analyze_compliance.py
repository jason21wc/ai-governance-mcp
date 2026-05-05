"""Tests for scripts/analyze_compliance.py — effectiveness analytics."""

import json
from datetime import date, datetime
from pathlib import Path

import pytest

# Import from scripts — add to path (intentional for script-level non-package code)
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from analyze_compliance import (
    RECENCY_WINDOW,
    _classify_session_length,
    _classify_quality,
    _compute_aggregates,
    _compute_avg_proximity,
    _fmt_delta,
    _fmt_pct,
    _nearest_preceding,
    analyze_transcript,
    compare_baselines,
    print_report,
    save_baseline,
)


def _make_line(tool_name: str) -> str:
    """Create a JSONL line with a tool_use entry."""
    entry = {
        "message": {"content": [{"type": "tool_use", "name": tool_name, "input": {}}]}
    }
    return json.dumps(entry)


def _write_transcript(tmp_path: Path, lines: list[str], name: str = "t.jsonl") -> Path:
    """Write lines to a JSONL file in tmp_path and return its path."""
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n" if lines else "")
    return path


# --- analyze_transcript: basic classification ---


class TestClassification:
    def test_empty_transcript(self, tmp_path):
        path = _write_transcript(tmp_path, [])
        result = analyze_transcript(path)
        assert result["classification"] == "COMPLIANT"
        assert result["gov_calls"] == 0
        assert result["ce_calls"] == 0
        assert result["file_mod_calls"] == 0
        assert result["gaps"] == []
        assert result["gov_gaps"] == []
        assert result["ce_gaps"] == []

    def test_gov_only(self, tmp_path):
        path = _write_transcript(
            tmp_path,
            [
                _make_line("mcp__ai-governance__evaluate_governance"),
                _make_line("Edit"),
            ],
        )
        result = analyze_transcript(path)
        assert result["classification"] == "PARTIAL"
        assert result["gov_calls"] == 1
        assert result["ce_calls"] == 0

    def test_ce_only(self, tmp_path):
        path = _write_transcript(
            tmp_path,
            [
                _make_line("mcp__context-engine__query_project"),
                _make_line("Write"),
            ],
        )
        result = analyze_transcript(path)
        assert result["classification"] == "PARTIAL"
        assert result["gov_calls"] == 0
        assert result["ce_calls"] == 1

    def test_both_gov_and_ce(self, tmp_path):
        path = _write_transcript(
            tmp_path,
            [
                _make_line("mcp__ai-governance__evaluate_governance"),
                _make_line("mcp__context-engine__query_project"),
                _make_line("Edit"),
            ],
        )
        result = analyze_transcript(path)
        assert result["classification"] == "COMPLIANT"
        assert result["gov_calls"] == 1
        assert result["ce_calls"] == 1

    def test_neither_with_file_mods(self, tmp_path):
        path = _write_transcript(
            tmp_path,
            [
                _make_line("Edit"),
                _make_line("Write"),
                _make_line("Bash"),
            ],
        )
        result = analyze_transcript(path)
        assert result["classification"] == "NON_COMPLIANT"
        assert result["file_mod_calls"] == 3

    def test_no_file_mods_is_compliant(self, tmp_path):
        """Sessions with no file modifications are always COMPLIANT."""
        path = _write_transcript(
            tmp_path,
            [
                _make_line("Read"),
                _make_line("Glob"),
            ],
        )
        result = analyze_transcript(path)
        assert result["classification"] == "COMPLIANT"
        assert result["file_mod_calls"] == 0


# --- Gap detection ---


class TestGapDetection:
    def test_within_window_no_gap(self, tmp_path):
        """Gov + CE within recency window before file-mod = no gap."""
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),
            _make_line("mcp__context-engine__query_project"),
            _make_line("Edit"),
        ]
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        assert result["gaps"] == []
        assert result["gov_gaps"] == []
        assert result["ce_gaps"] == []

    def test_outside_window_has_gap(self, tmp_path):
        """Gov + CE calls outside recency window = gap."""
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),
            _make_line("mcp__context-engine__query_project"),
        ]
        # Pad with non-tool lines to push beyond window
        for _ in range(RECENCY_WINDOW + 1):
            lines.append(json.dumps({"message": {"content": []}}))
        lines.append(_make_line("Edit"))
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        assert len(result["gaps"]) == 1

    def test_split_gaps_gov_present_ce_missing(self, tmp_path):
        """Gov present but CE missing = ce_gap only (combined gap too)."""
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),
            _make_line("Edit"),
        ]
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        assert result["gov_gaps"] == []
        assert result["ce_gaps"] == [2]  # line 2 is the Edit
        assert result["gaps"] == [2]  # combined gap

    def test_split_gaps_ce_present_gov_missing(self, tmp_path):
        """CE present but gov missing = gov_gap only."""
        lines = [
            _make_line("mcp__context-engine__query_project"),
            _make_line("Edit"),
        ]
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        assert result["gov_gaps"] == [2]
        assert result["ce_gaps"] == []
        assert result["gaps"] == [2]

    def test_custom_recency_window(self, tmp_path):
        """Custom window size is respected."""
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),
            _make_line("mcp__context-engine__query_project"),
        ]
        # Pad with 5 empty lines
        for _ in range(5):
            lines.append(json.dumps({"message": {"content": []}}))
        lines.append(_make_line("Edit"))
        path = _write_transcript(tmp_path, lines)

        # Window=10 should cover the gap
        result = analyze_transcript(path, recency_window=10)
        assert result["gaps"] == []

        # Window=3 should NOT cover the gap (Edit at line 8, gov at line 1)
        result = analyze_transcript(path, recency_window=3)
        assert len(result["gaps"]) == 1


# --- Session length categories ---


class TestSessionLengthCategories:
    @pytest.mark.parametrize(
        "mods, expected",
        [
            (0, "trivial"),
            (1, "short"),
            (10, "short"),
            (11, "medium"),
            (50, "medium"),
            (51, "long"),
            (100, "long"),
            (101, "very_long"),
            (500, "very_long"),
        ],
    )
    def test_session_length_boundaries(self, mods, expected):
        assert _classify_session_length(mods) == expected


# --- Compliance quality ---


class TestComplianceQuality:
    def test_high_quality(self):
        assert _classify_quality(0.1, 10, 5, 5) == "high"

    def test_moderate_quality(self):
        assert _classify_quality(0.5, 10, 2, 2) == "moderate"

    def test_low_quality_high_gap(self):
        assert _classify_quality(0.8, 10, 2, 2) == "low"

    def test_low_quality_no_calls(self):
        """Zero gov and ce calls with file mods = low."""
        assert _classify_quality(1.0, 10, 0, 0) == "low"

    def test_high_quality_no_mods(self):
        """Zero file mods = high regardless."""
        assert _classify_quality(0.0, 0, 0, 0) == "high"

    def test_boundary_030(self):
        """Gap rate exactly 0.3 is moderate, not high (high is < 0.3)."""
        assert _classify_quality(0.3, 10, 1, 1) == "moderate"

    def test_boundary_070(self):
        """Gap rate exactly 0.7 is moderate, not low (low is > 0.7)."""
        assert _classify_quality(0.7, 10, 1, 1) == "moderate"


# --- Enforcement era ---


class TestEnforcementEra:
    def test_pre_enforcement(self, tmp_path):
        path = _write_transcript(tmp_path, [_make_line("Edit")])
        # Set mtime to a date before deployment
        import os

        old_ts = datetime(2025, 1, 1).timestamp()
        os.utime(path, (old_ts, old_ts))
        result = analyze_transcript(path, deployment_date=date(2026, 1, 1))
        assert result["enforcement_era"] == "pre"

    def test_post_enforcement(self, tmp_path):
        path = _write_transcript(tmp_path, [_make_line("Edit")])
        # File was just created, mtime is today
        result = analyze_transcript(path, deployment_date=date(2020, 1, 1))
        assert result["enforcement_era"] == "post"

    def test_no_deployment_date(self, tmp_path):
        path = _write_transcript(tmp_path, [_make_line("Edit")])
        result = analyze_transcript(path)
        assert result["enforcement_era"] == "unknown"


# --- Proximity ---


class TestProximity:
    def test_nearest_preceding_basic(self):
        assert _nearest_preceding(10, [3, 7, 15]) == 3  # 10 - 7

    def test_nearest_preceding_no_preceding(self):
        assert _nearest_preceding(2, [5, 10]) is None

    def test_nearest_preceding_exact(self):
        assert _nearest_preceding(5, [5]) == 0

    def test_avg_proximity(self):
        # File mods at 10, 20; gov calls at 5, 15
        # Distances: 10-5=5, 20-15=5 -> avg=5.0
        result = _compute_avg_proximity([10, 20], [5, 15])
        assert result == 5.0

    def test_avg_proximity_no_calls(self):
        assert _compute_avg_proximity([10, 20], []) is None

    def test_avg_proximity_no_file_mods(self):
        assert _compute_avg_proximity([], [5, 15]) is None

    def test_proximity_in_transcript(self, tmp_path):
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),  # line 1
            _make_line("mcp__context-engine__query_project"),  # line 2
            _make_line("Edit"),  # line 3
        ]
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        # Edit at line 3, gov at line 1: distance 2
        assert result["avg_gov_proximity"] == 2.0
        # Edit at line 3, CE at line 2: distance 1
        assert result["avg_ce_proximity"] == 1.0


# --- Gap rates ---


class TestGapRates:
    def test_zero_file_mods(self, tmp_path):
        path = _write_transcript(tmp_path, [])
        result = analyze_transcript(path)
        assert result["gov_gap_rate"] == 0.0
        assert result["ce_gap_rate"] == 0.0
        assert result["combined_gap_rate"] == 0.0

    def test_all_gaps(self, tmp_path):
        path = _write_transcript(
            tmp_path,
            [
                _make_line("Edit"),
                _make_line("Write"),
            ],
        )
        result = analyze_transcript(path)
        assert result["gov_gap_rate"] == 1.0
        assert result["ce_gap_rate"] == 1.0
        assert result["combined_gap_rate"] == 1.0

    def test_partial_coverage(self, tmp_path):
        """Gov covers first edit, CE covers neither."""
        lines = [
            _make_line("mcp__ai-governance__evaluate_governance"),  # line 1
            _make_line("Edit"),  # line 2 — gov recent, CE not
        ]
        path = _write_transcript(tmp_path, lines)
        result = analyze_transcript(path)
        # gov_gap_rate = 0/1 = 0.0 (gov is recent)
        assert result["gov_gap_rate"] == 0.0
        # ce_gap_rate = 1/1 = 1.0 (CE never called)
        assert result["ce_gap_rate"] == 1.0
        # combined = 1/1 = 1.0 (either missing = gap)
        assert result["combined_gap_rate"] == 1.0


# --- Aggregates ---


class TestAggregates:
    def _make_result(self, **overrides):
        base = {
            "path": "/tmp/test.jsonl",
            "gov_calls": 0,
            "ce_calls": 0,
            "file_mod_calls": 0,
            "gov_positions": [],
            "ce_positions": [],
            "file_mod_positions": [],
            "gaps": [],
            "gov_gaps": [],
            "ce_gaps": [],
            "classification": "COMPLIANT",
            "gov_gap_rate": 0.0,
            "ce_gap_rate": 0.0,
            "combined_gap_rate": 0.0,
            "avg_gov_proximity": None,
            "avg_ce_proximity": None,
            "session_length": "trivial",
            "compliance_quality": "high",
            "enforcement_era": "unknown",
        }
        base.update(overrides)
        return base

    def test_median_gap_rate(self):
        results = [
            self._make_result(
                file_mod_calls=10,
                gaps=[1, 2, 3],
                combined_gap_rate=0.3,
                session_length="short",
                compliance_quality="high",
            ),
            self._make_result(
                file_mod_calls=10,
                gaps=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                combined_gap_rate=0.9,
                session_length="short",
                compliance_quality="low",
            ),
            self._make_result(
                file_mod_calls=10,
                gaps=[1, 2, 3, 4, 5],
                combined_gap_rate=0.5,
                session_length="short",
                compliance_quality="moderate",
            ),
        ]
        agg = _compute_aggregates(results)
        assert agg["median_gap_rate"] == 0.5  # median of [0.3, 0.9, 0.5] = 0.5

    def test_by_session_length(self):
        results = [
            self._make_result(
                file_mod_calls=5,
                gaps=[1, 2],
                gov_gaps=[1, 2],
                ce_gaps=[1, 2],
                session_length="short",
                combined_gap_rate=0.4,
            ),
            self._make_result(
                file_mod_calls=20,
                gaps=list(range(15)),
                gov_gaps=list(range(15)),
                ce_gaps=list(range(15)),
                session_length="medium",
                combined_gap_rate=0.75,
            ),
        ]
        agg = _compute_aggregates(results)
        assert agg["by_session_length"]["short"]["count"] == 1
        assert agg["by_session_length"]["medium"]["count"] == 1
        assert agg["by_session_length"]["trivial"]["count"] == 0

    def test_errors_excluded(self):
        results = [
            self._make_result(),
            {"error": "bad file", "path": "/tmp/bad.jsonl"},
        ]
        agg = _compute_aggregates(results)
        assert agg["total_sessions"] == 1

    def test_gap_totals_exposed(self):
        """Aggregate dict includes total_gaps, total_gov_gaps, total_ce_gaps."""
        results = [
            self._make_result(
                file_mod_calls=10,
                gaps=[1, 2, 3],
                gov_gaps=[1, 2],
                ce_gaps=[1, 2, 3],
                session_length="short",
            ),
        ]
        agg = _compute_aggregates(results)
        assert agg["total_gaps"] == 3
        assert agg["total_gov_gaps"] == 2
        assert agg["total_ce_gaps"] == 3


# --- Baseline save/load ---


class TestBaseline:
    def test_save_and_load(self, tmp_path):
        results = [
            {
                "path": "/tmp/test.jsonl",
                "gov_calls": 2,
                "ce_calls": 1,
                "file_mod_calls": 5,
                "gov_positions": [1, 3],
                "ce_positions": [2],
                "file_mod_positions": [4, 5, 6, 7, 8],
                "gaps": [6, 7, 8],
                "gov_gaps": [6, 7, 8],
                "ce_gaps": [4, 5, 6, 7, 8],
                "classification": "COMPLIANT",
                "gov_gap_rate": 0.6,
                "ce_gap_rate": 1.0,
                "combined_gap_rate": 0.6,
                "avg_gov_proximity": 3.0,
                "avg_ce_proximity": 4.0,
                "session_length": "short",
                "compliance_quality": "moderate",
                "enforcement_era": "post",
            }
        ]
        out_path = tmp_path / "baseline.json"
        save_baseline(results, out_path, label="test")
        with open(out_path) as f:
            loaded = json.load(f)

        assert loaded["label"] == "test"
        assert loaded["aggregate"]["total_sessions"] == 1
        assert loaded["aggregate"]["gap_rate"] == 0.6
        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["gov_gap_count"] == 3
        assert loaded["sessions"][0]["ce_gap_count"] == 5


# --- Comparison ---


class TestComparison:
    def test_compare_two_baselines(self, tmp_path, capsys):
        before = {
            "label": "pre-enforcement",
            "date": "2026-02-28",
            "aggregate": {
                "total_sessions": 69,
                "compliant": 10,
                "compliance_rate": 0.1449,
                "gap_rate": 0.9718,
                "median_gap_rate": 0.98,
                "total_file_mods": 3727,
            },
        }
        after = {
            "label": "post-enforcement",
            "date": "2026-03-01",
            "aggregate": {
                "total_sessions": 75,
                "compliant": 46,
                "compliance_rate": 0.6133,
                "gap_rate": 0.35,
                "median_gap_rate": 0.22,
                "gov_gap_rate": 0.28,
                "ce_gap_rate": 0.32,
                "total_file_mods": 4100,
                "by_bucket": {
                    "short": {"count": 15, "gap_rate": 0.12},
                    "medium": {"count": 32, "gap_rate": 0.30},
                },
            },
        }

        pa = tmp_path / "before.json"
        pb = tmp_path / "after.json"
        pa.write_text(json.dumps(before))
        pb.write_text(json.dumps(after))

        compare_baselines(pa, pb)
        output = capsys.readouterr().out

        assert "pre-enforcement" in output
        assert "post-enforcement" in output
        assert "Gap rate" in output
        assert "Sessions:" in output

    def test_old_format_baseline_graceful(self, tmp_path, capsys):
        """Old-format baseline missing new fields doesn't crash."""
        old = {
            "date": "2026-02-28",
            "aggregate": {
                "total_sessions": 69,
                "compliant": 10,
                "compliance_rate": 0.1449,
                "gap_rate": 0.9718,
                "total_file_mod_calls": 3727,  # old field name
            },
        }
        new = {
            "label": "new",
            "date": "2026-03-01",
            "aggregate": {
                "total_sessions": 5,
                "compliant": 3,
                "compliance_rate": 0.6,
                "gap_rate": 0.4,
                "gov_gap_rate": 0.3,
                "ce_gap_rate": 0.35,
                "total_file_mods": 100,
            },
        }

        pa = tmp_path / "old.json"
        pb = tmp_path / "new.json"
        pa.write_text(json.dumps(old))
        pb.write_text(json.dumps(new))

        # Should not raise
        compare_baselines(pa, pb)
        output = capsys.readouterr().out

        assert "N/A" in output or "\u2014" in output  # graceful missing fields
        assert "Gov/CE split not available" in output


# --- print_report smoke test ---


class TestPrintReport:
    def test_smoke_no_crash(self, tmp_path, capsys):
        """print_report does not crash and contains expected sections."""
        path = _write_transcript(
            tmp_path,
            [
                _make_line("mcp__ai-governance__evaluate_governance"),
                _make_line("mcp__context-engine__query_project"),
                _make_line("Edit"),
                _make_line("Write"),
            ],
        )
        results = [analyze_transcript(path)]
        print_report(results)
        output = capsys.readouterr().out

        assert "GOVERNANCE COMPLIANCE REPORT" in output
        assert "BREAKDOWN BY SESSION LENGTH" in output
        assert "BREAKDOWN BY COMPLIANCE QUALITY" in output
        assert "SPLIT GAP RATES" in output
        assert "Total sessions:" in output


# --- Format helpers ---


class TestFormatHelpers:
    def test_fmt_pct(self):
        assert _fmt_pct(0.5) == "50.0%"
        assert _fmt_pct(None) == "N/A"
        assert _fmt_pct(0.0) == "0.0%"
        assert _fmt_pct(1.0) == "100.0%"

    def test_fmt_delta(self):
        assert _fmt_delta(0.5, 0.3) == "-20.0pp"
        assert _fmt_delta(0.3, 0.5) == "+20.0pp"
        assert _fmt_delta(None, 0.5) == "\u2014"
        assert _fmt_delta(0.5, None) == "\u2014"
