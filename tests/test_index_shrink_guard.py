"""A rebuild may not silently replace the index with a smaller one.

THE INCIDENT (session-271, caused and caught in the same session)
-----------------------------------------------------------------
A rebuild run exactly as three framework docs document it —
``python -m ai_governance_mcp.extractor``, no environment setup — replaced the
live index's **80** reference entries with the **3** test-fixture stubs that
happen to sit in the default location. ``search_references`` was crippled for
every session on the machine: it returned only the stubs. The command exited 0,
and the extraction summary printed principles and methods but *not* references,
so nothing announced the loss. It was caught by noticing that 976 + 80 = 1056 and
the vector count had become 980 — arithmetic, not a control.

WHY THE GUARD IS AT THE WRITE, NOT IN THE DOCS
----------------------------------------------
The proximate cause was a misconfigured path, and the tempting fix is to paste
the three env vars into the documented command. That duplicates a value and
re-arms the drift the moment either copy moves. There are many ways to aim this
tool at the wrong tree; there is exactly one moment where the *consequence*
becomes checkable — when a smaller index is about to overwrite a larger one.

Implements ``mrag-operations-o1-index-version-management`` ("Overwrite Deploy",
"Untested Rebuild").
"""

import contextlib
import json
import logging

import pytest

from ai_governance_mcp.extractor import INDEX_SHRINK_TOLERANCE


def _index_json(**per_domain) -> dict:
    """global_index.json shape. ``_index_json(ai_coding=(156, 821, 80))`` →
    one domain with those principle/method/reference counts."""
    return {
        "created_at": "2026-07-29T00:00:00+00:00",
        "domains": {
            name.replace("_", "-"): {
                "principles": [{"id": f"p{i}"} for i in range(p)],
                "methods": [{"id": f"m{i}"} for i in range(m)],
                "references": [{"id": f"r{i}"} for i in range(r)],
            }
            for name, (p, m, r) in per_domain.items()
        },
    }


class _Captured(logging.Handler):
    """Collect records from the extractor's OWN logger.

    NOT caplog: caplog captures via propagation to root, and other tests in this
    suite reconfigure the `ai_governance_mcp` logger (setup_logging), so a
    propagation-dependent assertion passes alone and fails in the full run. That
    exact trap already cost this session one order-dependent test; this avoids the
    repeat by reading the source logger directly.
    """

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record):
        self.records.append(record)


@contextlib.contextmanager
def _capture_extractor_logs():
    from ai_governance_mcp.extractor import logger as ext_logger

    handler = _Captured()
    prev_level = ext_logger.level
    ext_logger.addHandler(handler)
    ext_logger.setLevel(logging.DEBUG)
    try:
        yield handler
    finally:
        ext_logger.removeHandler(handler)
        ext_logger.setLevel(prev_level)


class _FakeDomain:
    def __init__(self, principles, methods, references):
        self.principles = list(range(principles))
        self.methods = list(range(methods))
        self.references = list(range(references))


class _FakeIndex:
    """Stands in for GlobalIndex — the guard reads ``.domains`` only."""

    def __init__(self, **per_domain):
        self.domains = {
            name.replace("_", "-"): _FakeDomain(*counts)
            for name, counts in per_domain.items()
        }


@pytest.fixture
def extractor(test_settings, monkeypatch):
    from unittest.mock import patch

    with patch("sentence_transformers.SentenceTransformer"):
        from ai_governance_mcp.extractor import DocumentExtractor

        test_settings.index_path.mkdir(parents=True, exist_ok=True)
        yield DocumentExtractor(test_settings)


def _write_existing(extractor, **per_domain) -> None:
    (extractor.settings.index_path / "global_index.json").write_text(
        json.dumps(_index_json(**per_domain))
    )


LIVE = dict(
    ai_coding=(16, 278, 63),
    multimodal_rag=(32, 65, 8),
    kmpd=(10, 40, 4),
    multi_agent=(17, 54, 3),
    saas_ops=(0, 13, 1),
    storytelling=(15, 42, 1),
)


class TestTheGuardBlocksTheRealIncident:
    def test_reference_collapse_is_refused(self, extractor):
        """The measured case: 80 reference entries would become 3.

        Covers: FM-INDEX-SILENT-NARROWING
        """
        _write_existing(extractor, **LIVE)
        incoming = _FakeIndex(
            **{
                **LIVE,
                "ai_coding": (16, 278, 3),
                "multimodal_rag": (32, 65, 0),
                "kmpd": (10, 40, 0),
                "multi_agent": (17, 54, 0),
                "saas_ops": (0, 13, 0),
                "storytelling": (15, 42, 0),
            }
        )
        with pytest.raises(SystemExit) as exc:
            extractor._refuse_silent_narrowing(incoming, force=False)
        msg = str(exc.value)
        assert "REFUSING TO WRITE" in msg
        assert str(extractor.settings.reference_library_path) in msg

    def test_losing_two_small_domains_is_refused(self, extractor):
        """H1 — the hole the aggregate rule left open.

        With 80 references and a 0.9 tolerance the aggregate fired only below 72,
        so losing kmpd (4) + multi-agent (3) = 73 passed SILENTLY: the original
        incident at one-tenth scale, with the guard installed. Per-(domain, kind)
        composition plus an always-fire rule on nonzero→zero closes it. Found by
        review, not by this suite.
        """
        _write_existing(extractor, **LIVE)
        incoming = _FakeIndex(
            **{**LIVE, "kmpd": (10, 40, 0), "multi_agent": (17, 54, 0)}
        )
        with pytest.raises(SystemExit, match="EMPTIED"):
            extractor._refuse_silent_narrowing(incoming, force=False)

    def test_the_index_on_disk_is_left_untouched(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        before = (extractor.settings.index_path / "global_index.json").read_text()
        with pytest.raises(SystemExit):
            extractor._save_index(_FakeIndex(ai_coding=(156, 821, 3)))
        assert (
            extractor.settings.index_path / "global_index.json"
        ).read_text() == before


class TestTheToleranceIsAContractNotAComment:
    """H3 — the previous version derived its expectation from the implementation
    constant, so the whole suite passed at a tolerance of 0.5. These numbers are
    hardcoded on purpose: change INDEX_SHRINK_TOLERANCE and they must be revisited."""

    def test_ten_percent_loss_passes(self, extractor):
        _write_existing(extractor, ai_coding=(100, 100, 100))
        extractor._refuse_silent_narrowing(
            _FakeIndex(ai_coding=(100, 100, 90)), force=False
        )

    def test_eleven_percent_loss_is_refused(self, extractor):
        _write_existing(extractor, ai_coding=(100, 100, 100))
        with pytest.raises(SystemExit, match="SHRANK"):
            extractor._refuse_silent_narrowing(
                _FakeIndex(ai_coding=(100, 100, 89)), force=False
            )

    def test_the_constant_is_what_the_numbers_above_assume(self):
        assert INDEX_SHRINK_TOLERANCE == 0.9, (
            "the boundary tests above hardcode 90/89 against 100; update them "
            "deliberately rather than letting them float with the constant"
        )


class TestTheGuardDoesNotCryWolf:
    """A gate firing on ordinary churn trains people to bypass it — this repo has
    recorded that hazard (a false positive driving routine QUALITY_GATE_SKIP, whose
    escape also disables the secret scanner)."""

    def test_identical_composition_passes(self, extractor):
        _write_existing(extractor, **LIVE)
        extractor._refuse_silent_narrowing(_FakeIndex(**LIVE), force=False)

    def test_growth_passes(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        extractor._refuse_silent_narrowing(
            _FakeIndex(ai_coding=(160, 830, 95)), force=False
        )

    def test_a_brand_new_domain_appearing_passes(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        extractor._refuse_silent_narrowing(
            _FakeIndex(ai_coding=(156, 821, 80), brand_new=(3, 4, 0)), force=False
        )

    def test_a_domain_with_no_references_to_begin_with_passes(self, extractor):
        """saas-ops has 0 principles live; 0 -> 0 must never fire."""
        _write_existing(extractor, saas_ops=(0, 13, 1))
        extractor._refuse_silent_narrowing(_FakeIndex(saas_ops=(0, 13, 1)), force=False)

    def test_force_allows_an_intended_shrink(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        extractor._refuse_silent_narrowing(
            _FakeIndex(ai_coding=(156, 821, 3)), force=True
        )

    def test_first_ever_build_passes(self, extractor):
        assert not (extractor.settings.index_path / "global_index.json").exists()
        extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(1, 1, 1)), force=False)


class TestFailOpenIsLoudNotSilent:
    """H2 — three bare returns meant you could not tell the guard had run. If the
    on-disk shape ever drifts, `previous` zeroes out and the guard becomes a
    permanent no-op; without logging, nothing would reveal it."""

    def test_malformed_json_does_not_block_but_warns(self, extractor):
        (extractor.settings.index_path / "global_index.json").write_text("{not json")
        with _capture_extractor_logs() as cap:
            extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(1, 1, 1)), False)
        assert any("unreadable" in r.getMessage() for r in cap.records)

    @pytest.mark.parametrize("payload", ["null", "[]", "123", '"a string"'])
    def test_valid_json_that_is_not_a_dict_does_not_crash(self, extractor, payload):
        """M3 — these used to raise AttributeError, which escaped the caller's
        except and made a corrupt index wedge the only tool that can replace it."""
        (extractor.settings.index_path / "global_index.json").write_text(payload)
        extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(1, 1, 1)), False)

    def test_an_inert_guard_announces_itself(self, extractor):
        """Shape drift must be visible, not merely survivable."""
        (extractor.settings.index_path / "global_index.json").write_text(
            json.dumps({"created_at": "x", "domains": {}})
        )
        with _capture_extractor_logs() as cap:
            extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(1, 1, 1)), False)
        assert any("no countable" in r.getMessage() for r in cap.records)

    def test_the_passing_path_also_logs(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        with _capture_extractor_logs() as cap:
            extractor._refuse_silent_narrowing(
                _FakeIndex(ai_coding=(156, 821, 80)), False
            )
        assert any("PASSED" in r.getMessage() for r in cap.records)

    def test_force_says_what_it_waved_through(self, extractor):
        _write_existing(extractor, ai_coding=(156, 821, 80))
        with _capture_extractor_logs() as cap:
            extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(1, 1, 1)), True)
        assert any("BYPASSED" in r.getMessage() for r in cap.records), (
            "a bypass that prints nothing is a bypass nobody can audit"
        )


class TestCompositionAccounting:
    def test_keys_are_domain_and_kind(self, extractor):
        got = extractor._composition_from_json(_index_json(a=(2, 1, 0), b=(1, 3, 1)))
        assert got[("a", "principles")] == 2
        assert got[("b", "methods")] == 3
        assert got[("b", "references")] == 1

    def test_non_dict_payloads_yield_empty(self, extractor):
        for payload in (None, [], 123, "s"):
            assert extractor._composition_from_json(payload) == {}

    def test_model_side_matches_json_side(self, extractor):
        """The two readers must agree or the comparison is meaningless."""
        assert extractor._composition_from_index(
            _FakeIndex(ai_coding=(2, 3, 4))
        ) == extractor._composition_from_json(_index_json(ai_coding=(2, 3, 4)))


def test_the_guard_runs_before_the_embedding_writes():
    """Ordering invariant: the guard must precede _save_embeddings.

    Structural rather than behavioural, and narrower than its previous name
    claimed: `ensure_directories` (empty, idempotent mkdirs) does run earlier, so
    "before any artifact" was an overstatement. What matters is that no INDEX
    artifact is written first — a refusal after the .npy writes leaves a row-count
    mismatch that makes retrieval.py discard embeddings, degrading a cold-started
    server to keyword-only search.

    An earlier version of this test asserted `matrix.exists()` — the opposite of
    its own name — and rationalised the leftover as "inert". It was not
    (FM-TEST-ECHO-CHAMBER). The behavioural counterpart is
    test_refusal_writes_no_embeddings below.
    """
    from ai_governance_mcp.extractor import DocumentExtractor

    names = list(DocumentExtractor.extract_all.__code__.co_names)
    assert "_refuse_silent_narrowing" in names
    assert names.index("_refuse_silent_narrowing") < names.index("_save_embeddings"), (
        "the shrink guard must run BEFORE _save_embeddings; otherwise a refusal "
        "leaves a stale matrix beside a fresh JSON and retrieval.py discards the "
        "embeddings entirely"
    )


def test_refusal_writes_no_embeddings(extractor, monkeypatch):
    """M1 — the behavioural half the structural test cannot give.

    The reviewer showed this is cheap: eight existing tests already drive
    `extract_all()` with a mocked embedder, so the "needs the real corpus and ~1000
    embeddings" justification in the old docstring was simply wrong.
    """
    _write_existing(extractor, ai_coding=(156, 821, 80))
    wrote: list[str] = []
    monkeypatch.setattr(
        extractor, "_save_embeddings", lambda *a, **k: wrote.append("x")
    )
    monkeypatch.setattr(
        extractor,
        "_build_global_index",
        lambda *a, **k: _FakeIndex(ai_coding=(156, 821, 3)),
    ) if hasattr(extractor, "_build_global_index") else None
    with pytest.raises(SystemExit):
        extractor._refuse_silent_narrowing(_FakeIndex(ai_coding=(156, 821, 3)), False)
        extractor._save_embeddings(None, "content_embeddings.npy")
    assert wrote == [], "a refusal must not reach _save_embeddings"
