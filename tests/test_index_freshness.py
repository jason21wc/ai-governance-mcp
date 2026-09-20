"""Tests for scripts/check_index_freshness.py — index freshness gate (BACKLOG #206).

The freshness checker compares principle/method counts parsed from documents/
source against the built index at ~/.ai-governance/index/. References are
excluded — the reference library path is environment-dependent (contrarian
review finding, session-274).

Tests verify the COMPARISON LOGIC. Parsing accuracy is the extractor's own
test suite's responsibility.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import check_index_freshness  # noqa: E402


class TestCompare:
    """Pure comparison logic — no external deps."""

    def test_fresh(self):
        comp = {("ai-coding", "principles"): 12, ("ai-coding", "methods"): 45}
        assert check_index_freshness.compare(comp, comp) == []

    def test_stale_source_ahead(self):
        source = {("ai-coding", "methods"): 10}
        index = {("ai-coding", "methods"): 8}
        result = check_index_freshness.compare(source, index)
        assert len(result) == 1
        assert result[0] == ("ai-coding", "methods", 10, 8)

    def test_extra_in_index(self):
        source = {("constitution", "principles"): 5}
        index = {("constitution", "principles"): 7}
        result = check_index_freshness.compare(source, index)
        assert len(result) == 1
        assert result[0] == ("constitution", "principles", 5, 7)

    def test_missing_domain_in_index(self):
        source = {
            ("ai-coding", "principles"): 12,
            ("multi-agent", "methods"): 3,
        }
        index = {("ai-coding", "principles"): 12}
        result = check_index_freshness.compare(source, index)
        assert len(result) == 1
        assert result[0] == ("multi-agent", "methods", 3, 0)

    def test_multiple_mismatches(self):
        source = {
            ("ai-coding", "principles"): 12,
            ("ai-coding", "methods"): 45,
            ("constitution", "principles"): 20,
        }
        index = {
            ("ai-coding", "principles"): 12,
            ("ai-coding", "methods"): 43,
            ("constitution", "principles"): 22,
        }
        result = check_index_freshness.compare(source, index)
        assert len(result) == 2

    def test_empty_both(self):
        assert check_index_freshness.compare({}, {}) == []


class TestMain:
    """End-to-end with monkeypatched composition functions."""

    def _patch_settings(self, monkeypatch, index_path: Path):
        settings = MagicMock()
        settings.index_path = index_path
        monkeypatch.setattr(check_index_freshness, "_make_settings", lambda: settings)
        return settings

    def _create_index_dir(self, tmp_path: Path) -> Path:
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        (index_dir / "global_index.json").write_text("{}")
        return index_dir

    def test_fresh_exits_0(self, monkeypatch, tmp_path):
        index_dir = self._create_index_dir(tmp_path)
        self._patch_settings(monkeypatch, index_dir)
        comp = {("ai-coding", "principles"): 12, ("ai-coding", "methods"): 45}
        monkeypatch.setattr(check_index_freshness, "source_composition", lambda s: comp)
        monkeypatch.setattr(check_index_freshness, "index_composition", lambda p: comp)
        assert check_index_freshness.main(["--check"]) == 0

    def test_stale_exits_1(self, monkeypatch, tmp_path):
        index_dir = self._create_index_dir(tmp_path)
        self._patch_settings(monkeypatch, index_dir)
        monkeypatch.setattr(
            check_index_freshness,
            "source_composition",
            lambda s: {("ai-coding", "methods"): 10},
        )
        monkeypatch.setattr(
            check_index_freshness,
            "index_composition",
            lambda p: {("ai-coding", "methods"): 8},
        )
        assert check_index_freshness.main(["--check"]) == 1

    def test_extra_in_index_exits_1(self, monkeypatch, tmp_path):
        index_dir = self._create_index_dir(tmp_path)
        self._patch_settings(monkeypatch, index_dir)
        monkeypatch.setattr(
            check_index_freshness,
            "source_composition",
            lambda s: {("ai-coding", "principles"): 5},
        )
        monkeypatch.setattr(
            check_index_freshness,
            "index_composition",
            lambda p: {("ai-coding", "principles"): 7},
        )
        assert check_index_freshness.main(["--check"]) == 1

    def test_missing_index_exits_3(self, monkeypatch, tmp_path):
        self._patch_settings(monkeypatch, tmp_path / "nonexistent")
        assert check_index_freshness.main(["--check"]) == 3

    def test_unknown_flag_exits_2(self):
        assert check_index_freshness.main(["--bogus"]) == 2
