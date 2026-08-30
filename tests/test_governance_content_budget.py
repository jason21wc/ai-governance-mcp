"""Tests for evaluate_governance principle-body size bounding.

Regression coverage for the oversized-tool-result bug (Cowork report + 3 repros):
relevant_principles[] embedded every matched principle's FULL markdown body, so a
REVIEW/ESCALATE matching several principles produced 60-112 KB results that
exceeded the MCP per-tool-result token cap and HARD-ERRORED with no inline verdict.

`_allocate_principle_content` bounds the bodies: triggered S-Series first (safety
must stay visible on ESCALATE), then highest score, within a char budget; the rest
are reference-only (content=None, fetch via get_principle). These unit-test the pure
allocator directly so the S-Series-buried case is deterministic.
"""

from types import SimpleNamespace

from ai_governance_mcp.server.handlers.governance import _allocate_principle_content

BODY = "x" * 14000  # ~ average principle body size


def _entry(pid, content, score, is_s_series):
    """Build a (principle, score, relevance, is_s_series) entry the allocator reads."""
    return (SimpleNamespace(id=pid, content=content), score, "matched", is_s_series)


def test_total_content_bounded_when_many_principles():
    """8 average bodies (~112 KB raw) must allocate within the budget, rest omitted."""
    entries = [_entry(f"p{i}", BODY, 0.9 - i * 0.01, False) for i in range(8)]
    content_by_index, fetch_ids = _allocate_principle_content(entries, 40000)

    total = sum(len(c) for c in content_by_index.values() if c is not None)
    assert total <= 40000
    assert any(content_by_index[i] is None for i in range(8))  # some reference-only
    assert fetch_ids  # omitted IDs recorded for get_principle recovery


def test_s_series_retained_even_when_outscored(  # contrarian REQUIRED case
):
    """An S-Series principle that clears the threshold but ranks BELOW higher-scoring
    constitution principles must still get its body (safety visibility on ESCALATE).
    `all_principles` is hierarchy-ordered, not score-ordered, so this is the case
    the naive 'top-N by score' design would have dropped."""
    entries = [
        _entry("c1", BODY, 0.95, False),
        _entry("c2", BODY, 0.93, False),
        _entry("c3", BODY, 0.91, False),
        _entry("s-low", BODY, 0.55, True),  # S-Series, lowest score
    ]
    content_by_index, fetch_ids = _allocate_principle_content(entries, 40000)

    assert content_by_index[3] is not None, "S-Series body must be retained"
    assert "s-low" not in fetch_ids


def test_oversized_single_body_is_paragraph_truncated():
    """A single body larger than the WHOLE budget is truncated (marked), not dropped."""
    huge = "z\n\n" * 20000  # ~60 KB, exceeds the 40 KB budget
    entries = [_entry("big", huge, 0.9, False)]
    content_by_index, fetch_ids = _allocate_principle_content(entries, 40000)

    assert content_by_index[0] is not None
    assert len(content_by_index[0]) <= 40000
    assert "truncated" in content_by_index[0]
    assert "get_principle('big')" in content_by_index[0]
    assert "big" in fetch_ids


def test_all_small_bodies_kept_with_no_fetch_ids():
    """When everything fits, every body is inline and nothing needs get_principle."""
    entries = [_entry(f"p{i}", "short body", 0.9, False) for i in range(3)]
    content_by_index, fetch_ids = _allocate_principle_content(entries, 40000)

    assert all(content_by_index[i] is not None for i in range(3))
    assert fetch_ids == []


def test_highest_score_wins_budget_when_no_s_series():
    """With no S-Series, the highest-scoring bodies are kept; lower scores omitted —
    independent of input order (input is hierarchy-ordered, not score-ordered)."""
    entries = [
        _entry("low", BODY, 0.40, False),
        _entry("high", BODY, 0.99, False),
        _entry("mid", BODY, 0.70, False),
    ]
    content_by_index, fetch_ids = _allocate_principle_content(entries, 20000)

    # Budget ~20K fits exactly one 14K body — the highest score must win it.
    assert content_by_index[1] is not None  # "high"
    assert content_by_index[0] is None  # "low"
    assert "high" not in fetch_ids
    assert "low" in fetch_ids
