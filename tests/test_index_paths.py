"""Tests for the shared index resolver and its staleness guard.

The staleness guard earned a test the hard way. Its first implementation compared
`global_index.json` mtime against the newest `documents/*.md`, which is wrong for
this repo: `git worktree add` rewrites mtimes without touching content, and the
concurrency model here is a worktree per session. Measured — suite skips went 4 to
17 the first time that guard met a new worktree, silently disabling every
real-index test. That is the same silent-skip defect `index_paths` exists to remove,
reintroduced by the guard meant to harden it.

So these tests pin the property that actually matters: STALE must mean "the index
describes a different corpus than the one on disk," never "the files were touched."
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.index_paths import (  # noqa: E402
    index_not_built_reason,
    index_staleness_reason,
    resolve_index_dir,
)


class TestResolveIndexDir:
    def test_returns_none_rather_than_skipping_when_absent(self, tmp_path, monkeypatch):
        """None keeps the skip decision at the call site, where it can say why."""
        monkeypatch.setenv("AI_GOVERNANCE_INDEX_PATH", str(tmp_path / "nope"))
        monkeypatch.setattr(
            "tests.index_paths.index_dir_candidates",
            lambda: [tmp_path / "nope", tmp_path / "also-nope"],
        )
        assert resolve_index_dir() is None

    def test_reason_names_where_it_looked(self, tmp_path, monkeypatch):
        """A miss must be diagnosable — 'not found' with no path is not."""
        monkeypatch.setattr(
            "tests.index_paths.index_dir_candidates",
            lambda: [tmp_path / "a", tmp_path / "b"],
        )
        reason = index_not_built_reason()
        assert str(tmp_path / "a") in reason
        assert "extractor" in reason


class TestStalenessGuard:
    def test_touching_a_document_does_not_make_the_index_stale(self):
        """THE REGRESSION TEST. mtime churn is not a corpus change.

        `git worktree add`, `clone` and `checkout` all rewrite mtimes. If this
        assertion ever fails, the guard has gone back to a timestamp comparison and
        every worktree session will silently skip its real-index tests.
        """
        index_dir = resolve_index_dir()
        if index_dir is None:
            import pytest

            pytest.skip(index_not_built_reason())

        before = index_staleness_reason(index_dir)
        docs = Path(__file__).parent.parent / "documents"
        target = next(iter(sorted(docs.glob("*.md"))))
        target.touch()  # content-neutral, mtime-changing — exactly the worktree case
        after = index_staleness_reason(index_dir)

        assert after == before, (
            "touching a document changed the staleness verdict — the guard is "
            "comparing timestamps again, which false-positives in every fresh "
            f"worktree (before={before!r} after={after!r})"
        )

    def test_a_real_composition_mismatch_is_reported(self, tmp_path):
        """And the guard must still FIRE when the corpus genuinely differs.

        Verified against the comparison the guard actually delegates to, rather than
        by mutating the real corpus — a test that edits `documents/` to prove a point
        is a test that can leave the repo dirty.
        """
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from check_index_freshness import compare

        src = {("ai-coding", "principles"): 16, ("constitution", "methods"): 327}
        idx = {("ai-coding", "principles"): 16, ("constitution", "methods"): 300}
        mismatches = compare(src, idx)

        assert mismatches == [("constitution", "methods", 327, 300)], (
            "the guard's underlying comparison no longer detects a count mismatch"
        )
