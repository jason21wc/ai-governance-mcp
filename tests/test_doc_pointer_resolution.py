"""Every retrieval pointer in CLAUDE.md / AGENTS.md must actually resolve.

WHY THIS FILE EXISTS. The #313 migration thinned CLAUDE.md 151->28 lines and moved
the behavioral floor into `tiers.json`, leaving the pointer
`query_governance("behavioral floor directives")` behind. The data shipped. The
pointer shipped. The indexing never existed, so the query returns five unrelated
ui-ux principles. It survived a merge and a compliance review (BACKLOG #325).

The lesson was already in the reference library before the failure happened —
`ref-ai-coding-ssot-loader-shared-body-thin-overlay-imports` says: *"CI can assert
the literal is PRESENT; it cannot assert it RESOLVES — resolution is a manual
live-run gate."* It recurred anyway. A manual gate is not a gate. This file is the
structural version.

TWO PROPERTIES, and the second is the load-bearing one:

1. Every declared pointer resolves to content that is actually about what the
   pointer claims. A non-empty check is NOT sufficient — the failing pointer
   returned five results. The expectation must name what has to come back.

2. Pointers are DISCOVERED from the docs, not listed by hand. Adding a pointer to
   CLAUDE.md without declaring what it should return fails
   `test_every_discovered_pointer_has_a_declared_expectation`. Without that, this
   file would decay into a stale list of the pointers that happened to exist the
   day it was written — which is the same class of defect it exists to catch.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent

# Files whose pointers are CONTRACTS the model is told to run for specific content.
# compliance-review/procedure.md is in scope deliberately: its Check 3 pass criterion
# is the same `behavioral floor directives` pointer, asserted BY HAND — which is why
# a compliance review looked at the dead pointer and recorded PASS.
#
# Deliberately OUT of scope: README.md (5 illustrative example queries demonstrating
# the tool, not contracts) and title-10-ai-coding-cfr.md (prose restating AGENTS.md's
# recovery pointer). Forcing declared expectations on demonstrations would be scope
# creep and would make the table meaningless.
POINTER_DOCS = (
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/skills/compliance-review/procedure.md",
)

# `query_governance(...)` with a literal argument, positional OR keyword.
#
# The keyword form is not hypothetical: CLAUDE.md:28 writes the SIBLING tools that
# way (`search_references(query="...")`, `query_project(query="...")`), so an author
# following house style would produce a pointer an anchored-positional regex cannot
# see — and an undiscovered pointer never trips the has-an-expectation test either,
# so the gap would be silent. That is the exact class this file exists to close.
# Straight and typographic quotes both accepted; `\s` spans newlines, so multi-line
# calls match.
_POINTER_RE = re.compile(
    r"""query_governance\(\s*(?:query\s*=\s*)?["'“]([^"'”]{2,})["'”]\s*\)"""
)

# Template syntax showing how to CALL the tool, not a pointer at content. Matched
# explicitly rather than via a length floor — a floor silently also drops short real
# queries like `query_governance("S1")`.
_PLACEHOLDERS = frozenset({"...", "…", "query", "your query here"})


def _discover_pointers() -> dict[str, list[str]]:
    """Map each literal query string to the docs that point at it."""
    found: dict[str, list[str]] = {}
    for doc in POINTER_DOCS:
        path = REPO_ROOT / doc
        if not path.exists():
            continue
        for match in _POINTER_RE.finditer(path.read_text()):
            query = match.group(1).strip()
            if query.lower() in _PLACEHOLDERS:
                continue
            found.setdefault(query, []).append(doc)
    return found


# `get_principle('<id>')` is the OTHER pointer shape, and it is the one #325's fix
# introduced. Unlike a `query_governance` query — which is a search string that can
# resolve to the wrong content — this names an exact ID, so it fails in the simplest
# possible way: a typo, or an ID that changes when a heading is reworded. Nothing
# guarded it, so closing #325's dead pointer had added two new pointers of the same
# class in `documents/`.
#
# Scope is `documents/*.md` PLUS `POINTER_DOCS`, because the governance corpus is where
# prose hands a caller a literal ID. `_PLACEHOLDERS` covers the template forms; ids are
# additionally required to look like ids (a dotted prefix), so `get_principle(id)`
# written as illustration is not mistaken for a contract.
_ID_POINTER_RE = re.compile(
    r"""get_principle\(\s*(?:principle_id\s*=\s*)?["'“]([a-z][a-z0-9-]{4,})["'”]\s*\)"""
)


def _discover_id_pointers() -> dict[str, list[str]]:
    """Map each literal `get_principle` ID to the docs that hand it to a caller."""
    paths = [REPO_ROOT / doc for doc in POINTER_DOCS]
    paths += sorted((REPO_ROOT / "documents").glob("*.md"))
    found: dict[str, list[str]] = {}
    for path in paths:
        if not path.exists():
            continue
        for match in _ID_POINTER_RE.finditer(path.read_text()):
            unit_id = match.group(1).strip()
            if unit_id.lower() in _PLACEHOLDERS or "-" not in unit_id:
                continue
            rel = str(path.relative_to(REPO_ROOT))
            if rel not in found.setdefault(unit_id, []):
                found[unit_id].append(rel)
    return found


# What each pointer MUST surface. Values are substrings matched against the ids of
# everything the query returns (principles, methods, references).
#
# Keep these loose enough to survive rewording and tight enough to fail when the
# query lands in the wrong neighbourhood. "behavioral floor directives" returning
# five ui-ux principles must fail; it must not pass merely by being non-empty.
EXPECTATIONS: dict[str, tuple[str, ...]] = {
    # BACKLOG #325 blocker (a), CLOSED 2026-08-13. `rules-of-procedure.md` Part 7.15
    # is the indexed unit — `meta-method-behavioral-floor-directives`. This entry was
    # xfail(strict=True) until then, and strict mode forced the marker's removal.
    # NOTE this assertion matches an ID SUBSTRING and nothing more, so it is green on
    # a correctly-titled but empty unit. `tests/test_behavioral_floor_section.py`
    # carries the content check; do not let this one stand in for it.
    "behavioral floor directives": ("behavioral-floor", "floor-directive"),
    # rules-of-procedure Part 15.4 — the reference-library curation procedure.
    "reference library curation §15.4": (
        "intake-paths",
        "bloat-prevention",
        "reference-entry",
    ),
    # AGENTS.md recovery pointer. Pinned to the ai-coding recovery methods rather
    # than a bare "recovery" token: method ids are `{domain}-method-{title-slug}`,
    # and at least five unrelated headings slug to something containing "recovery"
    # (storytelling "9 Recovery Protocol", multi-agent "Recovery Information",
    # constitution "Failure Recovery & Resilience"). A storytelling revision
    # protocol satisfying this assertion is not the guarantee this file claims.
    "framework recovery": ("coding-method-recovery", "recovery-procedure"),
    # compliance-review Check 6 canary.
    "which principle governs validation before action?": ("verification-validation",),
}

# Pointers documented but not yet resolvable. An entry here is marked xfail(strict=True)
# below, so the day the pointer starts working the XPASS fails the suite and forces the
# entry's removal — the marker retires itself instead of ossifying into an accepted
# failure. Empty is the healthy state; it held `behavioral floor directives` from
# session-302 until BACKLOG #325 blocker (a) closed on 2026-08-13. Kept rather than
# deleted with its last entry: the next pointer added ahead of its content needs this,
# and rebuilding the mechanism from memory is how the self-retiring property gets lost.
KNOWN_BROKEN: dict[str, str] = {}


def _returned_ids(engine, query: str) -> list[str]:
    result = engine.retrieve(query=query, include_methods=True)
    ids: list[str] = []
    for scored in result.constitution_principles + result.domain_principles:
        ids.append(scored.principle.id)
    for scored in result.methods:
        ids.append(scored.method.id)
    for scored in result.references:
        ids.append(scored.reference.id)
    return ids


def test_every_discovered_pointer_has_a_declared_expectation():
    """A pointer added to the docs without an expectation is an untested assertion.

    This is what stops the file from decaying. It needs no index and no model, so
    it runs in the ordinary suite rather than only under `-m real_index`.
    """
    discovered = _discover_pointers()
    assert discovered, (
        "no query_governance pointers found in "
        f"{POINTER_DOCS} — the discovery regex has probably drifted from the docs"
    )
    undeclared = sorted(set(discovered) - set(EXPECTATIONS))
    assert not undeclared, (
        "these pointers appear in the docs with no declared expectation in "
        "EXPECTATIONS — declare what each must surface, or the pointer is an "
        f"untested assertion: {undeclared}"
    )


def test_known_broken_entries_are_real_pointers():
    """A KNOWN_BROKEN key that is not in EXPECTATIONS is a silent no-op.

    The xfail is applied by looking the query up in KNOWN_BROKEN inside the
    parametrized test, and the parametrization comes from EXPECTATIONS — so a typo'd
    or reworded key marks nothing, the test runs strictly, and nobody learns the
    marker was ignored.
    """
    orphaned = sorted(set(KNOWN_BROKEN) - set(EXPECTATIONS))
    assert not orphaned, (
        f"KNOWN_BROKEN names pointers absent from EXPECTATIONS, so they mark nothing: "
        f"{orphaned}"
    )


@pytest.mark.real_index
@pytest.mark.slow  # loads real embedding + rerank models, same as the queries above
def test_documented_unit_ids_resolve(real_settings):
    """Every `get_principle('<id>')` a document hands a caller must actually resolve.

    Discovered, not hand-listed, for the same reason the query pointers are: a listed
    set decays into the pointers that existed the day it was written. This is the check
    that would catch a heading reword silently changing a unit's ID out from under the
    prose that names it.
    """
    from ai_governance_mcp.retrieval import RetrievalEngine

    discovered = _discover_id_pointers()
    assert discovered, (
        "no get_principle ID pointers found — the discovery regex has probably drifted "
        "from the docs"
    )

    engine = RetrievalEngine(real_settings)
    dead = {
        unit_id: docs
        for unit_id, docs in discovered.items()
        if engine.get_principle_by_id(unit_id) is None
        and engine.get_method_by_id(unit_id) is None
    }
    assert not dead, (
        f"these documents hand callers an ID that resolves to nothing: {dead}. "
        "Fix the prose, or rebuild the index if the unit was just added."
    )


def test_no_stale_expectations():
    """An expectation for a pointer that no longer exists is dead weight.

    Scoped to the docs THIS TREE ACTUALLY SHIPS. The public release build stages an
    allowlisted subset and does not include `.claude/skills/`, so the compliance-review
    canary pointer was undiscoverable there and its expectation read as stale — the
    build failed on a difference in tree contents rather than on any drift. An
    expectation is stale when the file that declared it still exists and no longer
    names it; a file that is absent from the tree says nothing either way.
    """
    missing = [doc for doc in POINTER_DOCS if not (REPO_ROOT / doc).exists()]
    if missing:
        # Cannot tell "removed from a doc" from "the doc is not in this tree", and
        # guessing produces a false failure in the public build rather than a finding.
        # Registered so the skip is visible instead of reading as a pass.
        pytest.skip(f"pointer sources absent from this tree: {missing}")

    stale = sorted(set(EXPECTATIONS) - set(_discover_pointers()))
    assert not stale, (
        f"EXPECTATIONS names pointers that are no longer in {POINTER_DOCS}: {stale}"
    )


@pytest.mark.real_index
@pytest.mark.slow  # loads real embedding + rerank models, same as test_retrieval_quality
@pytest.mark.parametrize("query", sorted(EXPECTATIONS))
def test_documented_pointer_resolves(query, real_settings, request):
    """Run the exact call the docs tell the model to run; assert what comes back."""
    if query in KNOWN_BROKEN:
        request.node.add_marker(
            pytest.mark.xfail(strict=True, reason=KNOWN_BROKEN[query])
        )

    from ai_governance_mcp.retrieval import RetrievalEngine

    engine = RetrievalEngine(real_settings)
    ids = _returned_ids(engine, query)
    expected = EXPECTATIONS[query]

    assert ids, f'query_governance("{query}") returned nothing at all'
    matched = [i for i in ids if any(token in i for token in expected)]
    assert matched, (
        f'query_governance("{query}") is documented in '
        f"{_discover_pointers().get(query)} but resolves to the wrong content.\n"
        f"  expected an id containing one of: {list(expected)}\n"
        f"  got: {ids[:10]}\n"
        "A pointer that returns plausible-looking but unrelated results is worse "
        "than one that returns nothing — the caller cannot tell."
    )
