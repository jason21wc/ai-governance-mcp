"""Single resolver for the built governance index used by real-index tests.

WHY THIS EXISTS. The index location was replicated as a hardcoded
``Path(__file__).parent.parent / "index"`` across eight call sites. When the index
moved out of the checkout in session-268, every one of them became wrong at once —
and because each expresses a miss as ``pytest.skip``, the failure surfaced as
silence rather than red. Measured 2026-08-10: 25 tests skipping, including the
entire MRR / Recall@10 / Precision@5 benchmark, which is why session-300 recorded
the post-rebuild retrieval baseline as "unmeasured".

A replicated path is a single decision written down eight times; it only takes one
move to invalidate all of them, and nothing forces the eighth to be updated with
the first. Resolve here, import everywhere.

``isolate_home`` (autouse in conftest) pins ``AI_GOVERNANCE_INDEX_PATH`` to the real
user-data index *before* it redirects ``$HOME``, so ``Settings()`` resolves correctly
inside a test.

**This module consolidates the TEST side only — two other resolvers exist and one
deliberately disagrees.** Naming them here so the divergence is one documented
decision rather than three silent ones (BACKLOG #329 tracks consolidation):

- ``scripts/gen_quick_reference.py`` tries **repo-local first**, on a stated and
  good reason: an explicit in-tree artifact should beat ambient config, or a test
  building a synthetic repo silently compares it against the operator's real index.
  That order is correct *for a generator that may be pointed at a scratch repo*.
- ``scripts/check_index_freshness.py`` uses ``Settings().index_path`` alone, no
  fallback.

Tests want the opposite of the generator: ``Settings().index_path`` first, because
that is what the *server* reads, so the suite measures the artifact production
actually consumes. Preferring an in-tree copy would assert against something
nothing loads. The orders differ on purpose; they are only dangerous when both
locations hold an index, which is why the divergence is written down rather than
quietly tolerated.

**Not checked here: freshness.** A resolved index may be stale relative to
``documents/``. Exact-count assertions that were silently skipping now run against
whatever was last built — see BACKLOG #329.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_governance_mcp.config import Settings  # noqa: E402


def index_dir_candidates() -> list[Path]:
    """Every location a built index may legitimately live, in priority order."""
    return [
        Settings().index_path,  # env / user-data default (session-268 layout)
        Path(__file__).resolve().parent.parent / "index",  # legacy in-tree layout
    ]


def resolve_index_dir() -> Path | None:
    """Directory containing a built ``global_index.json``, or None if not built.

    Returning None rather than skipping keeps the skip decision — and its message —
    at the call site, where the test can say what it actually needed.
    """
    for candidate in index_dir_candidates():
        if (candidate / "global_index.json").is_file():
            return candidate
    return None


def index_staleness_reason(index_dir: Path) -> str | None:
    """Reason the index is older than the corpus, or None if it is current.

    Restoring the real-index tests turned exact-count assertions back on
    (``== 12`` accounting principles, ``== 4`` AO-Series, the domain ceiling).
    Those now read whatever was last built, so a developer who edits
    ``documents/`` without rebuilding would get a GREEN run asserted against the
    pre-edit corpus — false confidence pointing exactly the wrong way ("no rebuild
    needed"). Counts that silently skipped for weeks becoming counts that silently
    lie is not an improvement.

    Deliberately advisory here: the call site skips with this reason, while
    ``scripts/check_index_freshness.py`` (wired into ``scripts/check.sh``) stays the
    hard gate. A test cannot honestly assert a count against a stale artifact, but
    it also should not fail a developer's loop mid-edit — the loud skip says which
    it is, and check.sh refuses the push.

    **Known limitation, verified by negative control:** mtime is a coarse proxy for
    content. A content-neutral ``touch documents/constitution.md`` produces a false
    STALE (observed while testing this guard), and conversely an index rebuilt from
    an unchanged corpus refreshes the timestamp without changing anything. The
    error direction is the safe one — false STALE degrades to a loud skip, never to
    a green assertion against wrong data — which is why mtime is acceptable here
    while ``check_index_freshness.py`` does the real comparison by composition.
    """
    # COMPOSITION, not mtime. An earlier version of this compared global_index.json
    # mtime against the newest documents/*.md and was wrong in the way that matters:
    # `git worktree add` / `clone` / `checkout` rewrite mtimes without touching
    # content, so it reported STALE in every fresh worktree. This repo's concurrency
    # model is a worktree per session, so that would have silently skipped 13
    # real-index tests in every new session — re-creating the exact silent-skip
    # defect this module was written to remove. Measured: 4 skips became 17 the first
    # time the guard met a new worktree. A safe error direction does not redeem a
    # guard that fires on the normal workflow.
    # Restore sys.path rather than leaving `scripts/` permanently at position 0 for the
    # rest of the session. `scripts/semantic_rank.py` shares a name with a package
    # submodule, so a leaked prefix entry is a live shadowing hazard, not a tidiness nit.
    scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        from check_index_freshness import (  # noqa: PLC0415
            compare,
            index_composition,
            source_composition,
        )
    except ImportError:
        return None  # freshness is check.sh's hard gate; absence here is not fatal
    finally:
        try:
            sys.path.remove(scripts_dir)
        except ValueError:  # pragma: no cover - another caller already removed it
            pass

    settings = Settings()
    try:
        src = source_composition(settings)
        idx = index_composition(index_dir)
    except Exception:
        return None  # a malformed index is resolve/other checks' problem, not this
    mismatches = compare(src, idx)
    if not mismatches:
        return None
    detail = ", ".join(
        f"{domain}/{kind} source={s} index={i}" for domain, kind, s, i in mismatches
    )
    return (
        f"governance index at {index_dir} is STALE — its composition does not match "
        f"{settings.documents_path}, so count assertions would be measured against a "
        f"different corpus than the one on disk ({detail[:300]}). "
        "Run `python -m ai_governance_mcp.extractor`."
    )


def index_not_built_reason() -> str:
    """Uniform skip message naming where we looked, so a miss is diagnosable."""
    looked = " or ".join(str(c) for c in index_dir_candidates())
    return (
        f"governance index not built — looked in {looked}. "
        "Run `python -m ai_governance_mcp.extractor` first."
    )
