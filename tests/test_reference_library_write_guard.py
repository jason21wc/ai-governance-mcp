"""Unit tests for the reference-library write-guard helpers in conftest.

BACKLOG #294 — the guard's detection logic must be exercised independently of
the session-scoped fixture wiring so a regression in ``_snapshot_dir`` or
``_diff_snapshots`` is caught by a fast, deterministic test rather than a
silent pass of the fixture.
"""

from conftest import _diff_snapshots, _snapshot_dir


class TestDiffSnapshots:
    """``_diff_snapshots`` detects new and modified files."""

    def test_detects_new_file(self):
        assert _diff_snapshots({}, {"ai-coding/x.md": 100}) == ["ai-coding/x.md"]

    def test_detects_modified_file(self):
        assert _diff_snapshots({"x.md": 100}, {"x.md": 200}) == ["x.md"]

    def test_empty_when_unchanged(self):
        assert _diff_snapshots({"x.md": 100}, {"x.md": 100}) == []

    def test_ignores_deleted_file(self):
        assert _diff_snapshots({"x.md": 100}, {}) == []

    def test_multiple_changes_sorted(self):
        before = {"b.md": 1, "a.md": 1}
        after = {"b.md": 2, "a.md": 2, "c.md": 3}
        assert _diff_snapshots(before, after) == ["a.md", "b.md", "c.md"]


class TestSnapshotDir:
    """``_snapshot_dir`` captures file-level mtimes recursively."""

    def test_returns_empty_for_missing_dir(self, tmp_path):
        assert _snapshot_dir(tmp_path / "nonexistent") == {}

    def test_returns_empty_for_empty_dir(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        assert _snapshot_dir(d) == {}

    def test_captures_nested_files(self, tmp_path):
        d = tmp_path / "lib"
        (d / "ai-coding").mkdir(parents=True)
        (d / "ai-coding" / "entry.md").write_text("content")
        (d / "top.md").write_text("content")
        snap = _snapshot_dir(d)
        assert set(snap.keys()) == {"ai-coding/entry.md", "top.md"}
        assert all(isinstance(v, int) for v in snap.values())

    def test_excludes_directories_from_snapshot(self, tmp_path):
        d = tmp_path / "lib"
        (d / "subdir").mkdir(parents=True)
        snap = _snapshot_dir(d)
        assert "subdir" not in snap
