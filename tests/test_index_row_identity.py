"""Embedding rows must be attributed to items by identity, not by position.

Regression suite for the row-misattribution defect that shipped on `main`
(2026-07-19 → 2026-07-25) and misattributed all 1041 embedding rows.

Root cause: the extractor assigns `embedding_id` in build order and writes
`content_embeddings.npy` in that order, but serializes the index JSON with
`sort_keys=True`, which reorders the `domains` mapping alphabetically.
Retrieval walked the JSON and paired vectors by enumeration position, so the
moment alphabetical order diverged from build order, every semantic score was
computed against another document's vector.

Every pre-existing structural gate — row count, dimension, model label, and the
BACKLOG #58 embedding-space canary — passes on a permutation: the matrix has the
right shape, the right space and the right vectors, merely attached to the wrong
items. Only a row-identity check catches it, which is what these tests pin.

Deliberately NOT asserted anywhere here: that `embedding_id` equals JSON
traversal position. That is the broken assumption; sorted JSON is intentional
(BACKLOG #187 determinism), and the mapping exists to make ordering irrelevant.
"""

import json
from unittest.mock import Mock, patch

import numpy as np
import pytest

from ai_governance_mcp.models import DomainIndex, GlobalIndex, Principle, ReferenceEntry
from ai_governance_mcp.retrieval import RetrievalEngine
from tests.index_paths import index_not_built_reason, resolve_index_dir

DIM = 384
# Must be allowlisted (retrieval.ALLOWED_EMBEDDING_MODELS) — the engine
# validates the configured name before falling back to a local model, and the
# index's stored label must match settings or the model-mismatch gate discards
# the vectors before the row-identity gate is reached.
TEST_MODEL = "BAAI/bge-small-en-v1.5"


def _one_hot(position: int) -> np.ndarray:
    vec = np.zeros(DIM, dtype=np.float32)
    vec[position] = 1.0
    return vec


def _filler_principles(count: int, first_row: int) -> list[Principle]:
    """Extra corpus so BM25 IDF is meaningful.

    BM25Okapi's IDF for a term appearing in 1 of 2 documents is exactly zero,
    so a two-document corpus can never produce a positive score and any
    keyword-search assertion over it would be vacuous.
    """
    return [
        Principle(
            id=f"filler-{n}",
            domain="alpha",
            series_code="F",
            title=f"Filler {n}",
            content=f"Unrelated filler corpus entry number {n} about {'topic ' * n}.",
            line_range=(1, 10),
            embedding_id=first_row + n,
        )
        for n in range(count)
    ]


def _make_index(
    *,
    embedding_ids: list[int | None],
    with_reference: bool = False,
    filler: int = 0,
    canaries=None,
):
    """Build a 2-domain index whose build order is the reverse of sorted order.

    "zeta" sorts AFTER "alpha" but is built FIRST, so the JSON's sorted domain
    order is the reverse of the embedding-row order — the exact divergence the
    production defect depended on. A fixture using alphabetically-ordered
    domains would pass either way and prove nothing.

    Item layout, in build order (and therefore embedding-row order):
        row 0 -> zeta/principle "zeta-first-built"
        row 1 -> alpha/principle "alpha-second-built"
    plus, when `with_reference`, a third item:
        row 2 -> zeta/reference "ref-zeta"

    `embedding_ids` overrides what each item claims, so corruption shapes can be
    injected without touching the vectors.
    """
    zeta_principle = Principle(
        id="zeta-first-built",
        domain="zeta",
        series_code="Z",
        title="Zeta First Built",
        content="This item's vector was written to embedding row zero.",
        line_range=(1, 10),
        embedding_id=embedding_ids[0],
    )
    alpha_principle = Principle(
        id="alpha-second-built",
        domain="alpha",
        series_code="A",
        title="Alpha Second Built",
        content="This item's vector was written to embedding row one.",
        line_range=(1, 10),
        embedding_id=embedding_ids[1],
    )

    zeta_refs = []
    if with_reference:
        zeta_refs.append(
            ReferenceEntry(
                id="ref-zeta-row-two",
                domain="zeta",
                title="Zeta Reference Row Two",
                tags=["identity"],
                status="current",
                entry_type="direct",
                content="Reference entry whose vector is at embedding row two.",
                artifact="Reference entry whose vector is at embedding row two.",
                embedding_id=embedding_ids[2],
            )
        )

    domains = {
        "zeta": DomainIndex(
            domain="zeta",
            principles=[zeta_principle],
            methods=[],
            references=zeta_refs,
            last_extracted="2026-07-25T00:00:00Z",
        ),
        "alpha": DomainIndex(
            domain="alpha",
            principles=[alpha_principle]
            + _filler_principles(filler, first_row=2 + int(with_reference)),
            methods=[],
            references=[],
            last_extracted="2026-07-25T00:00:00Z",
        ),
    }
    return GlobalIndex(
        domains=domains,
        domain_configs=[],
        created_at="2026-07-25T00:00:00Z",
        version="1.0",
        embedding_model=TEST_MODEL,
        embedding_dimensions=DIM,
        embedding_canaries=canaries or [],
    )


def _canaries_for(n_rows: int):
    """Canaries as the extractor writes them: rows sorted({0, n//2, n-1}).

    Each carries a verbatim copy of its row's vector, which is what makes a
    canary-to-row comparison a generation check.
    """
    from ai_governance_mcp.models import EmbeddingCanary

    rows = sorted({0, n_rows // 2, n_rows - 1}) if n_rows else []
    return [
        EmbeddingCanary(text=f"canary text for row {r}", vector=_one_hot(r).tolist())
        for r in rows
    ]


def _write_index(
    settings, index: GlobalIndex, n_rows: int, *, shift_rows: bool = False
) -> None:
    """Persist the index the way the real extractor does — sorted keys.

    `shift_rows` writes a matrix whose rows are rotated by one relative to what
    the JSON describes — the stale-JSON/fresh-matrix shape of BACKLOG #217. The
    ids still form a perfect bijection and the embedding space is unchanged, so
    only a canary-to-row comparison can detect it.
    """
    with open(settings.index_path / "global_index.json", "w") as f:
        # sort_keys=True mirrors extractor._save_index. This is what puts
        # "alpha" ahead of "zeta" in the JSON while row 0 still belongs to zeta.
        json.dump(index.model_dump(), f, sort_keys=True)

    # Row r is one-hot at position r, so a query vector of one-hot(r) scores 1.0
    # against row r and 0.0 against every other row. Attribution errors are then
    # unambiguous rather than a ranking nudge.
    rows = [
        _one_hot((r + 1) % n_rows) if shift_rows else _one_hot(r) for r in range(n_rows)
    ]
    np.save(settings.index_path / "content_embeddings.npy", np.stack(rows))
    np.save(
        settings.index_path / "domain_embeddings.npy", np.zeros((2, DIM), np.float32)
    )


def _engine(settings, query_row: int):
    """RetrievalEngine whose encoder always returns one-hot(query_row)."""

    def _encode_one(text: str) -> np.ndarray:
        # Canary texts must re-encode to the vector stored for their row, or
        # the pre-existing BACKLOG #58 embedding-space gate discards the
        # vectors before the row-identity and canary-row gates are reached.
        # Every other text is the query, and encodes to the row under test.
        if text.startswith("canary text for row "):
            return _one_hot(int(text.rsplit(" ", 1)[1]))
        return _one_hot(query_row)

    embedder = Mock()
    embedder.encode = Mock(
        side_effect=lambda texts, *a, **k: (
            _encode_one(texts)
            if isinstance(texts, str)
            else np.stack([_encode_one(t) for t in texts])
        )
    )
    embedder.get_sentence_embedding_dimension = Mock(return_value=DIM)

    reranker = Mock()
    reranker.predict = Mock(
        side_effect=lambda pairs, *a, **k: np.array([1.0] * len(pairs))
    )

    settings.embedding_model = TEST_MODEL
    from ai_governance_mcp.retrieval import RetrievalEngine

    # The mock must be in place DURING construction, because _load_index() runs
    # in __init__ and the BACKLOG #58 canary gate re-encodes canary text through
    # the real encoder. Installing it via _try_embedding_client sets the private
    # attribute, so the lazy `embedder` property short-circuits from then on and
    # the patch does not need to outlive construction.
    def _install(self):
        self._embedder = embedder
        return True

    with patch.object(RetrievalEngine, "_try_embedding_client", _install):
        engine = RetrievalEngine(settings)
    # Re-assert after the patch exits: if the canary gate never ran, _embedder
    # is still None and the property would fall through to a real model
    # download on the first query.
    engine._embedder = embedder
    engine._reranker = reranker
    return engine


class TestRowIdentityMapping:
    """The healthy path: rows resolve to their owner regardless of JSON order."""

    @pytest.mark.parametrize(
        "query_row,expected_id",
        [
            (0, "zeta-first-built"),
            (1, "alpha-second-built"),
        ],
    )
    def test_semantic_search_attributes_row_to_its_owner(
        self, test_settings, query_row, expected_id
    ):
        """A query matching row N must return the item whose embedding_id is N.

        Under the positional defect, querying row 0 returned
        "alpha-second-built" — the alphabetically-first item — because the JSON
        walk reached alpha first while row 0 belonged to zeta.
        """
        index = _make_index(embedding_ids=[0, 1])
        _write_index(test_settings, index, n_rows=2)
        engine = _engine(test_settings, query_row=query_row)

        results = engine.semantic_search("any query")

        assert results, "semantic search returned nothing — embeddings were discarded"
        top_domain, top_type, top_local_idx, score = results[0]
        assert top_type == "principle"
        principle = engine.index.domains[top_domain].principles[top_local_idx]
        assert principle.id == expected_id, (
            f"row {query_row} attributed to {principle.id!r}, expected {expected_id!r} "
            "— embedding rows are being paired by position, not identity"
        )
        assert score == pytest.approx(1.0)

    def test_reference_semantic_search_uses_identity_mapping(self, test_settings):
        """search_references() is the SECOND semantic consumer.

        The abandoned session-256 implementation fixed semantic_search() only
        and left this loop misattributed, so it is pinned separately.
        """
        index = _make_index(embedding_ids=[0, 1, 2], with_reference=True)
        _write_index(test_settings, index, n_rows=3)
        engine = _engine(test_settings, query_row=2)

        assert engine.semantic_docs[2] == ("zeta", "reference", 0)

        results = engine.search_references("any query")
        assert results, "reference search returned nothing"
        assert results[0].reference.id == "ref-zeta-row-two"

    def test_bm25_docs_and_semantic_docs_are_independently_ordered(self, test_settings):
        """The two mappings are not interchangeable — that is the whole point.

        bm25_docs is keyed by BM25 corpus position (JSON walk order);
        semantic_docs is keyed by embedding row. Asserting they differ here
        locks in the distinction, so a future refactor cannot quietly collapse
        them back into one list and reintroduce the defect.
        """
        index = _make_index(embedding_ids=[0, 1])
        _write_index(test_settings, index, n_rows=2)
        engine = _engine(test_settings, query_row=0)

        assert engine.semantic_docs[0] == ("zeta", "principle", 0)
        assert engine.bm25_docs[0] == ("alpha", "principle", 0)
        assert engine.bm25_docs != engine.semantic_docs


class TestRowIdentityCorruptionDegrades:
    """Unusable identity data must degrade to BM25-only, never serve guesses."""

    @pytest.mark.parametrize(
        "embedding_ids,label",
        [
            ([0, None], "missing id"),
            ([0, 0], "duplicate id"),
            ([0, 7], "out-of-range id"),
            ([1, 1], "gap — row 0 claimed by nobody"),
        ],
    )
    def test_corrupt_identity_discards_embeddings(
        self, test_settings, embedding_ids, label
    ):
        index = _make_index(embedding_ids=embedding_ids)
        _write_index(test_settings, index, n_rows=2)
        engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is None, (
            f"{label}: embeddings were kept despite an unusable row mapping — "
            "semantic scores would be attributed to the wrong items"
        )
        assert engine.semantic_search("any query") == []

    def test_degrade_keeps_keyword_search_working(self, test_settings):
        """Fail closed on semantics, open on the server.

        A governance server that refuses to start is worse than one with
        reduced recall: callers proceed with no governance at all.
        """
        index = _make_index(embedding_ids=[0, 0], filler=6)
        _write_index(test_settings, index, n_rows=8)
        engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is None
        assert engine.bm25_index is not None
        assert engine.bm25_search("zeta first built"), "BM25 should still serve"

    def test_uniformly_unstamped_legacy_index_falls_back_to_position(
        self, test_settings, caplog
    ):
        """An index with NO ids anywhere is legacy, not corrupt.

        There is no identity information to use, so positional pairing is the
        only option available and is exactly what such an index got before this
        change — degrading it would be a regression, not a safety win. Accepted
        only because absence is UNIFORM; that is a positively identified shape
        rather than a guess (contrast the partial case below).
        """
        index = _make_index(embedding_ids=[None, None])
        _write_index(test_settings, index, n_rows=2)

        with caplog.at_level("WARNING"):
            engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is not None, (
            "a uniformly unstamped legacy index was degraded — this breaks "
            "indexes that work correctly today"
        )
        assert engine.semantic_docs == engine.bm25_docs
        assert any("legacy format" in r.message for r in caplog.records), (
            "legacy positional pairing must announce itself"
        )

    def test_partially_stamped_index_is_corruption_not_legacy(self, test_settings):
        """Some ids present and some absent is unresolvable, so it degrades.

        This is the boundary of the legacy allowance: uniform absence is a
        format, mixed presence is damage. Pinned separately so a future
        loosening of the legacy branch cannot silently swallow it.
        """
        index = _make_index(embedding_ids=[0, None])
        _write_index(test_settings, index, n_rows=2)
        engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is None

    def test_corruption_is_logged_at_error(self, test_settings, caplog):
        """Silent degradation is the failure class this guard exists to end."""
        index = _make_index(embedding_ids=[0, 0])
        _write_index(test_settings, index, n_rows=2)

        with caplog.at_level("ERROR"):
            _engine(test_settings, query_row=0)

        assert any(
            "embedding_id" in r.message or "embedding row" in r.message
            for r in caplog.records
            if r.levelname == "ERROR"
        ), "degrade happened without an ERROR-level explanation"


class TestCanaryRowGeneration:
    """Stored canary vectors must match the rows they were copied from.

    This is the generation check the bijection cannot make: ids being
    internally consistent says nothing about whether the JSON and the matrix
    came from the same build. Model-free — it compares stored vectors to
    stored rows, unlike the BACKLOG #58 gate which re-encodes canary text.
    """

    def test_matching_canaries_pass(self, test_settings):
        index = _make_index(embedding_ids=[0, 1], canaries=_canaries_for(2))
        _write_index(test_settings, index, n_rows=2)
        engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is not None
        assert len(engine.semantic_docs) == 2

    def test_mismatched_canary_row_degrades(self, test_settings, caplog):
        """A stale JSON against a fresh same-shape matrix is otherwise invisible.

        Row count, dimension, model label and the id bijection all pass — this
        is the only gate that catches it (BACKLOG #217).
        """
        index = _make_index(embedding_ids=[0, 1], canaries=_canaries_for(2))
        # JSON (and its canaries) describe build A; the matrix is build B.
        _write_index(test_settings, index, n_rows=2, shift_rows=True)

        with caplog.at_level("ERROR"):
            engine = _engine(test_settings, query_row=0)

        assert engine.content_embeddings is None
        assert engine.semantic_docs == []
        assert any("different builds" in r.message for r in caplog.records)


class TestDegradeIsReported:
    """A degraded retrieval must be visible to the CALLER, not just the log.

    The #216 defect survived six days because a degraded response was
    byte-identical to a healthy one. Detection without reporting repeats it.
    """

    def test_healthy_index_reports_semantic_available(self, test_settings):
        index = _make_index(embedding_ids=[0, 1], filler=6)
        _write_index(test_settings, index, n_rows=8)
        engine = _engine(test_settings, query_row=0)

        assert engine.retrieve("zeta first built").semantic_available is True

    def test_degraded_index_reports_semantic_unavailable(self, test_settings):
        index = _make_index(embedding_ids=[0, 0], filler=6)
        _write_index(test_settings, index, n_rows=8)
        engine = _engine(test_settings, query_row=0)

        assert engine.retrieve("zeta first built").semantic_available is False

    def test_degraded_result_is_announced_in_tool_output(self, test_settings):
        """The flag has to reach the rendered response, not just the model."""
        from ai_governance_mcp.server.handlers.retrieval import (
            _format_retrieval_result,
        )

        index = _make_index(embedding_ids=[0, 0], filler=6)
        _write_index(test_settings, index, n_rows=8)
        engine = _engine(test_settings, query_row=0)

        output = _format_retrieval_result(engine.retrieve("zeta first built"))
        assert "DEGRADED" in output


class TestCommittedIndexRowIdentity:
    """The real committed index must satisfy the invariant.

    This is the cheap always-on structural counterpart to the golden-set
    quality gate: it needs no model, so it runs in the default suite and fails
    fast if a rebuild ever ships a broken mapping.
    """

    def test_committed_index_ids_are_a_bijection_onto_embedding_rows(self):
        index_dir = resolve_index_dir()
        if index_dir is None:
            pytest.skip(index_not_built_reason())
        index_path = index_dir / "global_index.json"
        emb_path = index_dir / "content_embeddings.npy"
        if not emb_path.exists():
            pytest.skip(
                "index built without embeddings — content_embeddings.npy absent"
            )

        with open(index_path) as f:
            data = json.load(f)
        n_rows = np.load(emb_path, mmap_mode="r").shape[0]

        ids = [
            item["embedding_id"]
            for domain in data["domains"].values()
            for key in ("principles", "methods", "references")
            for item in domain.get(key, [])
        ]

        assert sorted(x for x in ids if x is not None) == list(range(n_rows)), (
            "committed index embedding_ids are not a bijection onto "
            f"[0, {n_rows}) — semantic retrieval would be misattributed"
        )


class TestDomainRowIdentity:
    """BACKLOG #218 — the routing matrix must be attributed by identity too.

    `domain_configs` is a JSON *list*, and `sort_keys=True` does not reorder list
    elements, so positional pairing happened to survive the defect that scrambled
    the content matrix. That is a property of the serialization format, not a
    guarantee: nothing declared the order load-bearing, nothing checked it, and
    `DomainConfig.embedding_id` was already stamped and never read. These tests
    pin the mapping so routing cannot silently start scoring queries against the
    wrong domain's description vector.
    """

    @staticmethod
    def _index(embedding_ids):
        from ai_governance_mcp.models import DomainConfig

        return GlobalIndex(
            domains={},
            domain_configs=[
                DomainConfig(
                    name=name,
                    display_name=name.title(),
                    principles_file=f"{name}.md",
                    methods_file=f"{name}-cfr.md",
                    description=f"description for {name}",
                    priority=i * 10,
                    embedding_id=embedding_ids[i],
                )
                for i, name in enumerate(("zeta", "alpha"))
            ],
            created_at="2026-07-25T00:00:00Z",
            version="1.0",
            embedding_model=TEST_MODEL,
            embedding_dimensions=DIM,
        )

    def test_rows_follow_embedding_id_not_list_position(self):
        """The mapping must invert a stamped order that disagrees with position.

        zeta is listed first but claims row 1; alpha is listed second and claims
        row 0. A positional pairing returns [zeta, alpha]; identity returns
        [alpha, zeta]. This is the assertion that would have to be deleted for
        the positional assumption to come back.
        """
        rows = RetrievalEngine._build_domain_rows(self._index([1, 0]), 2)
        assert rows == [1, 0], (
            "row 0 belongs to the config claiming embedding_id 0 (alpha, at list "
            f"position 1) — got {rows}"
        )

    def test_identity_order_is_preserved_when_it_matches_position(self):
        rows = RetrievalEngine._build_domain_rows(self._index([0, 1]), 2)
        assert rows == [0, 1]

    @pytest.mark.parametrize(
        "ids,why",
        [
            ([0, 0], "duplicate id leaves a hole in the matrix"),
            ([0, 5], "id outside the matrix"),
            ([0, None], "partial stamping is corruption, not a legacy index"),
        ],
    )
    def test_unattributable_matrix_disables_routing(self, ids, why):
        """Degrade to NO routing, never to wrong routing."""
        assert RetrievalEngine._build_domain_rows(self._index(ids), 2) is None, why

    def test_uniformly_unstamped_index_keeps_positional_pairing(self):
        """A legacy index carries no identity information at all.

        Positional pairing is then the only option and not a regression, so it is
        accepted — but only when ids are UNIFORMLY absent, which is a positively
        identified shape rather than a guess.
        """
        assert RetrievalEngine._build_domain_rows(self._index([None, None]), 2) == [
            0,
            1,
        ]

    def test_committed_index_domain_ids_are_a_bijection(self):
        index_dir = resolve_index_dir()
        if index_dir is None:
            pytest.skip(index_not_built_reason())
        index_path = index_dir / "global_index.json"
        emb_path = index_dir / "domain_embeddings.npy"
        if not emb_path.exists():
            pytest.skip("index built without embeddings — domain_embeddings.npy absent")

        with open(index_path) as f:
            configs = json.load(f).get("domain_configs", [])
        n_rows = np.load(emb_path, mmap_mode="r").shape[0]
        ids = [c.get("embedding_id") for c in configs]

        assert sorted(x for x in ids if x is not None) == list(range(n_rows)), (
            f"committed domain_configs ids are not a bijection onto [0, {n_rows}) "
            "— domain routing would score against the wrong descriptions"
        )

    def test_route_domains_consumer_uses_the_mapping(self, monkeypatch):
        """The CONSUMER must honour identity, not just the mapping builder.

        `_build_domain_rows` being correct proves nothing if `route_domains`
        still enumerates `domain_configs` positionally — that revert would leave
        every other test in this class green. Here zeta is listed first but owns
        row 1, and only row 1's vector matches the query, so a positional
        consumer names "alpha" and an identity-keyed one names "zeta".
        """
        from ai_governance_mcp.config import Settings

        engine = RetrievalEngine.__new__(RetrievalEngine)
        engine.settings = Settings(domain_similarity_threshold=0.5, max_domains=5)
        engine.index = TestDomainRowIdentity._index([1, 0])
        engine.domain_embeddings = np.stack([_one_hot(0), _one_hot(1)])
        engine.domain_rows = RetrievalEngine._build_domain_rows(engine.index, 2)

        class _Enc:
            def encode(self, texts, normalize_embeddings=True):
                # Matches row 1 exactly, row 0 not at all.
                return np.stack([_one_hot(1)])

        monkeypatch.setattr(
            RetrievalEngine, "embedder", property(lambda self: _Enc()), raising=False
        )
        scores = engine.route_domains("anything")
        assert "zeta" in scores, (
            "route_domains attributed row 1 to the wrong domain — it is pairing "
            f"by list position, not by embedding_id. Got: {scores}"
        )
        assert "alpha" not in scores, f"alpha should not match row 1: {scores}"
