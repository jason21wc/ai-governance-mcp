"""Retrieval engine for AI Governance documents.

Hybrid retrieval with BM25 + semantic search + reranking.
"""

import hashlib
import json
import logging
import re
import threading
import time
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi

from .config import Settings, load_settings, setup_logging
from .models import (
    ConfidenceLevel,
    GlobalIndex,
    Method,
    Principle,
    ReferenceEntry,
    RetrievalResult,
    ScoredMethod,
    ScoredPrinciple,
    ScoredReference,
)

logger = setup_logging()

# Security: Allowlists for ML models to prevent loading untrusted code.
# Only vetted models may be loaded. Override with env vars for testing only.
ALLOWED_EMBEDDING_MODELS = {
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "BAAI/bge-large-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "sentence-transformers/paraphrase-MiniLM-L6-v2",
    "nomic-ai/nomic-embed-text-v1.5",  # 768 dims, 8K context, MTEB 86.2
}
ALLOWED_RERANKER_MODELS = {
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "cross-encoder/ms-marco-TinyBERT-L-2-v2",
    "BAAI/bge-reranker-base",
    "BAAI/bge-reranker-large",
}

# BACKLOG #58 load-time canary gate thresholds. A canary re-encoded via the
# query encoder should cosine ~1.0 against its stored canonical vector; the
# divergence incident measured 0.01, so the floor has a ~94-point margin. Below
# the floor → fall back to BM25-only (build/query embedder divergence). The warn
# band flags same-model backend/precision drift (e.g. fp16 daemon vs fp32 local)
# without forcing a fallback.
CANARY_COSINE_FLOOR = 0.95
CANARY_COSINE_WARN = 0.999


class RetrievalEngine:
    """Hybrid retrieval engine with BM25 + semantic search + reranking."""

    _CONSTITUTION_HIERARCHY: dict[str, int] = {
        "S": 0,  # Bill of Rights (Amendments) — immutable safety guardrails
        "C": 1,  # Article I: Core Architecture (Legislative)
        "O": 2,  # Article II: Operational Efficiency (Executive)
        "Q": 3,  # Article III: Quality & Integrity (Judicial)
        "G": 4,  # Article IV: Governance & Evolution (Administrative)
        # MA-Series dissolved in v3.0.0 — multi-agent principles moved to domain
        # Order updated v5.0.5 per F-P2-15: priority now matches canonical
        # Framework Overview order (I → II → III → IV), which constitution.md
        # body order also matches post-reorder. Prior O=3/Q=2 reflected the
        # drifted body order (I → III → II → IV) that v5.0.5 corrected.
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.index: Optional[GlobalIndex] = None
        self.content_embeddings: Optional[np.ndarray] = None
        self.domain_embeddings: Optional[np.ndarray] = None
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_docs: list[tuple[str, str, int]] = []  # (domain, type, local_idx)
        # Row-indexed view of the SAME items, keyed by each item's stored
        # embedding_id: semantic_docs[row] is the item whose vector lives at
        # content_embeddings[row]. Distinct from bm25_docs, which is keyed by
        # BM25 corpus position. The two coincided until the index JSON began
        # being written with sort_keys=True; they are no longer interchangeable.
        self.semantic_docs: list[tuple[str, str, int]] = []
        # Same idea for the routing matrix (BACKLOG #218): domain_rows[row] is
        # the position in index.domain_configs whose vector is
        # domain_embeddings[row]. Empty means "not attributable" → no routing.
        self.domain_rows: list[int] = []
        self._embedder = None
        self._reranker = None
        self._model_lock = threading.Lock()
        self._index_lock = threading.Lock()
        self._index_mtime: float = 0.0
        self._reload_failures: int = 0
        self._feedback_ratings: dict[str, tuple[float, int]] = {}  # id -> (avg, count)
        self._load_index()
        self._load_feedback_ratings()

    @property
    def embedder(self):
        """Lazy-load embedding model for query encoding.

        Phase 2: tries EmbeddingClient (daemon socket) first. Falls back to
        local SentenceTransformer only if AI_CONTEXT_ENGINE_EMBED_SOCKET=none
        (Docker/CI) or the import fails. The default path preserves the memory
        guarantee: MCP servers never load torch when the daemon is available.
        """
        if self._embedder is None:
            with self._model_lock:
                if self._embedder is None:  # Double-checked locking
                    if self._try_embedding_client():
                        return self._embedder
                    # Fallback: local model (Docker, CI, daemon unavailable)
                    from sentence_transformers import SentenceTransformer

                    model_name = self.settings.embedding_model
                    if model_name not in ALLOWED_EMBEDDING_MODELS:
                        raise ValueError(
                            f"Embedding model '{model_name}' not in allowlist. "
                            f"Allowed: {sorted(ALLOWED_EMBEDDING_MODELS)}"
                        )
                    logger.info("Loading embedding model locally: %s", model_name)
                    self._embedder = SentenceTransformer(
                        model_name,
                        trust_remote_code=False,
                        model_kwargs={"use_safetensors": True},
                    )
        return self._embedder

    @property
    def reranker(self):
        """Lazy-load cross-encoder reranking model.

        Phase 2: tries EmbeddingClient (daemon socket) first. Falls back to
        local CrossEncoder only in Docker/CI mode.
        """
        if self._reranker is None:
            with self._model_lock:
                if self._reranker is None:  # Double-checked locking
                    if self._try_reranker_client():
                        return self._reranker
                    # Fallback: local model
                    from sentence_transformers import CrossEncoder

                    model_name = self.settings.rerank_model
                    if model_name not in ALLOWED_RERANKER_MODELS:
                        raise ValueError(
                            f"Reranker model '{model_name}' not in allowlist. "
                            f"Allowed: {sorted(ALLOWED_RERANKER_MODELS)}"
                        )
                    logger.info("Loading reranking model locally: %s", model_name)
                    self._reranker = CrossEncoder(
                        model_name,
                        trust_remote_code=False,
                    )
        return self._reranker

    def _try_embedding_client(self) -> bool:
        """Try to connect to the daemon's embedding server for encode().

        Returns True if client connected and set self._embedder. Returns False
        if disabled, unavailable, or socket doesn't exist — caller falls back.
        Checks socket file existence FIRST to avoid retry-backoff delay (~3s)
        when the daemon isn't running.
        """
        import os

        if (
            os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip().lower()
            == "none"
        ):
            return False
        try:
            from .embedding_ipc import DEFAULT_SOCKET_PATH, EmbeddingClient

            sock_path = os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip()
            check_path = sock_path if sock_path else str(DEFAULT_SOCKET_PATH)
            if not os.path.exists(check_path):
                return False
            if EmbeddingClient.available():
                self._embedder = EmbeddingClient()
                logger.info("Using embedding server (IPC) for encoding")
                return True
        except Exception as e:
            logger.debug("Embedding IPC client not available: %s", e)
        return False

    def _try_reranker_client(self) -> bool:
        """Try to connect to the daemon's embedding server for predict().

        Returns True if client connected and set self._reranker. Falls back
        on any failure. Checks socket file first (same fast-fail pattern).
        """
        import os

        if (
            os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip().lower()
            == "none"
        ):
            return False
        try:
            from .embedding_ipc import DEFAULT_SOCKET_PATH, EmbeddingClient

            sock_path = os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip()
            check_path = sock_path if sock_path else str(DEFAULT_SOCKET_PATH)
            if not os.path.exists(check_path):
                return False
            if EmbeddingClient.available():
                self._reranker = EmbeddingClient()
                logger.info("Using embedding server (IPC) for reranking")
                return True
        except Exception as e:
            logger.debug("Reranker IPC client not available: %s", e)
        return False

    def _load_index(self) -> None:
        """Load global index and embeddings from disk.

        Called from __init__ (pre-concurrent, no lock needed) and from
        _check_index_freshness (already holding _index_lock).

        Uses temp-and-swap: loads into temporaries, validates structure,
        then atomically swaps all state — or rolls back entirely if the
        reload would degrade from working semantic search to BM25-only.
        """
        index_path = self.settings.index_path / "global_index.json"
        content_emb_path = self.settings.index_path / "content_embeddings.npy"
        domain_emb_path = self.settings.index_path / "domain_embeddings.npy"

        if not index_path.exists():
            # LOUD, NOT QUIET — the precondition for untracking `index/` (session-268).
            #
            # This used to `logger.warning(...)` and return. With the index committed
            # that was nearly unreachable, so the softness never showed. Untracking it
            # makes "no index yet" the NORMAL state of a fresh clone, and a warning on
            # stderr that nobody reads would mean `evaluate_governance` returns an EMPTY
            # principle set while the enforcement hook records a satisfied governance
            # call. Silent governance degradation is strictly worse than the merge pain
            # untracking removes — BACKLOG #249(f) named this as the reason not to
            # untrack, so untracking is only safe once this path is loud.
            #
            # `content_embeddings` stays None, so `semantic_available` is already False
            # (:1355) and the DEGRADED banner fires — an empty result is never mistaken
            # for a healthy one. This raises the LOG level to match that severity; it
            # does not invent new state.
            logger.error(
                "GOVERNANCE INDEX MISSING at %s — retrieval will return NOTHING. "
                "This is not a warning: an empty principle set looks identical to "
                "'no principles apply'. Build it with `python -m ai_governance_mcp.extractor` "
                "(set AI_GOVERNANCE_INDEX_PATH first if the index lives outside the repo; "
                "the index is a build artifact and is no longer committed).",
                index_path,
            )
            return

        try:
            current_mtime = index_path.stat().st_mtime
        except OSError:
            current_mtime = self._index_mtime

        # 1. Load into temporaries
        try:
            with open(index_path) as f:
                data = json.load(f)
                new_index = GlobalIndex(**data)
        except Exception as e:
            logger.warning("Failed to parse index JSON, keeping previous state: %s", e)
            self._index_mtime = current_mtime
            return
        logger.info(f"Loaded index with {len(new_index.domains)} domains")

        new_content_emb = None
        if content_emb_path.exists():
            try:
                # Loaded as-is (no cast). Contract: the index is float32 —
                # enforced at the save chokepoint (extractor._save_embeddings) and
                # matching the float32 query vectors from embedding_ipc. If a
                # legacy/hand-built index were float64, similarity would silently
                # upcast; the producer-side cast is what keeps this correct.
                new_content_emb = np.load(content_emb_path, allow_pickle=False)
                logger.info(f"Loaded content embeddings: {new_content_emb.shape}")
            except Exception as e:
                logger.warning(
                    "Corrupt content embeddings file, falling back to BM25-only: %s",
                    e,
                )

        new_domain_emb = None
        if domain_emb_path.exists():
            try:
                new_domain_emb = np.load(domain_emb_path, allow_pickle=False)
                logger.info(f"Loaded domain embeddings: {new_domain_emb.shape}")
            except Exception as e:
                logger.warning(
                    "Corrupt domain embeddings file, falling back to BM25-only: %s",
                    e,
                )

        # 2. H3 FIX: Check embedding model mismatch on temps
        model_mismatch = False
        if new_index and new_content_emb is not None:
            stored_model = getattr(new_index, "embedding_model", None)
            if stored_model and stored_model != self.settings.embedding_model:
                logger.warning(
                    "Embedding model mismatch: index has '%s' but configured '%s'. "
                    "Falling back to BM25-only. Rebuild index to use semantic search.",
                    stored_model,
                    self.settings.embedding_model,
                )
                new_content_emb = None
                new_domain_emb = None
                model_mismatch = True

        # 3. Structural validation (R1) — convert shape problems to None
        if new_index and new_content_emb is not None:
            expected_items = sum(
                len(d.principles) + len(d.methods) + len(d.references)
                for d in new_index.domains.values()
            )
            if new_content_emb.shape[0] != expected_items:
                logger.warning(
                    "Embedding row count mismatch: %d embeddings vs %d index items. "
                    "Discarding embeddings.",
                    new_content_emb.shape[0],
                    expected_items,
                )
                new_content_emb = None
                new_domain_emb = None
            elif (
                new_index.embedding_dimensions
                and len(new_content_emb.shape) > 1
                and new_content_emb.shape[1] != new_index.embedding_dimensions
            ):
                logger.warning(
                    "Embedding dimension mismatch: %d vs expected %d. "
                    "Discarding embeddings.",
                    new_content_emb.shape[1],
                    new_index.embedding_dimensions,
                )
                new_content_emb = None
                new_domain_emb = None

        # 3b. Behavioral canary gate (BACKLOG #58): verify build-space ==
        # query-space. The structural gates above (model-label / row-count /
        # dimension) cannot detect a divergent embedding space — vectors
        # orthogonal to the query encoder are structurally indistinguishable
        # from good ones and walk through all of them (the session-205→209
        # silent BM25 incident). Re-encode the build-time canary texts via the
        # REAL query encoder and compare to their stored canonical vectors.
        #
        # Wrapped broadly because _load_index runs in __init__ with no outer
        # guard: a gate failure must DEGRADE (fall back to BM25), never crash.
        # On failure we deliberately keep model_mismatch=False so the rollback
        # guard below RETAINS a previously-working index — routing through the
        # model_mismatch branch would set model_mismatch=True and bypass
        # rollback, discarding the working index and causing the very silent-
        # BM25 failure this gate prevents (contrarian a8aae6860f5e64a13).
        canaries = getattr(new_index, "embedding_canaries", None) if new_index else None
        if new_content_emb is not None and canaries:
            canary_failed = False
            try:
                texts = [c.text for c in canaries]
                stored = np.asarray([c.vector for c in canaries], dtype=np.float32)
                encoded = np.asarray(
                    self.embedder.encode(texts, normalize_embeddings=True),
                    dtype=np.float32,
                )
                cosines = [
                    self._cosine_similarity(encoded[i], stored[i])
                    for i in range(len(canaries))
                ]
                min_cos = min(cosines) if cosines else 1.0
                if min_cos < CANARY_COSINE_FLOOR:
                    canary_failed = True
                    logger.error(
                        "Embedding-space canary check FAILED (min cosine %.4f < "
                        "%.2f): the index's vectors do not match the query "
                        "encoder's space (build/query embedder divergence, "
                        "BACKLOG #58). Falling back to BM25-only — rebuild the "
                        "index with the canonical local model.",
                        min_cos,
                        CANARY_COSINE_FLOOR,
                    )
                elif min_cos < CANARY_COSINE_WARN:
                    logger.warning(
                        "Embedding-space canary check passed but low (min cosine "
                        "%.4f); possible backend/precision drift between build "
                        "and query encoders.",
                        min_cos,
                    )
            except Exception as e:  # noqa: BLE001 — gate must never crash load
                canary_failed = True
                logger.error(
                    "Embedding-space canary check errored (%s); treating as "
                    "failure and falling back to BM25-only to stay fail-safe.",
                    e,
                )
            if canary_failed:
                # Keep model_mismatch=False (see comment above) so the rollback
                # guard retains a working index; only cold-start goes BM25.
                new_content_emb = None
                new_domain_emb = None

        # 3c. Row-identity gate — verify the index can say WHICH item owns each
        # embedding row, and discard the vectors if it cannot. The gates above
        # are all cardinality/space checks: row count, dimension, model label
        # and canary cosine all pass on a PERMUTATION, because a permuted
        # matrix has the right shape, the right model and the right vectors —
        # just attached to the wrong documents. That is exactly how 1041/1041
        # misattributed rows shipped on main and were misread as a ranking
        # regression (BACKLOG #216).
        #
        # Same degrade posture as the canary gate: keep model_mismatch=False so
        # the rollback guard below RETAINS a previously-working index rather
        # than swapping in one whose vectors we cannot attribute.
        new_semantic_docs: list[tuple[str, str, int]] = []
        if new_index and new_content_emb is not None:
            mapped = self._build_semantic_docs(new_index, new_content_emb.shape[0])
            if mapped is None:
                new_content_emb = None
                new_domain_emb = None
            else:
                new_semantic_docs = mapped

        # 3c-bis. Same gate for the DOMAIN routing matrix (BACKLOG #218).
        # `domain_configs` is a JSON *list*, and `sort_keys=True` does not reorder
        # list elements — which is the only reason routing escaped the #216 defect.
        # That is a property of the serialization format, not a guarantee anyone
        # designed, so the positional assumption is removed here rather than left
        # as the last one standing. `DomainConfig.embedding_id` was already being
        # stamped by the extractor and never read.
        new_domain_rows: list[int] = []
        if new_index and new_domain_emb is not None and new_index.domain_configs:
            mapped_domains = self._build_domain_rows(new_index, new_domain_emb.shape[0])
            if mapped_domains is None:
                # Routing degrades to "no routing" (empty scores), which callers
                # already handle — never to silently WRONG routing.
                new_domain_emb = None
            else:
                new_domain_rows = mapped_domains

        # 3d. Canary ROW check — model-free, and strictly stronger than 3c.
        # The extractor stores each canary's vector as a verbatim copy of a
        # specific embedding row (extractor.py: rows sorted({0, n//2, n-1})), so
        # comparing the stored vector against the row it should occupy proves
        # the JSON and the matrix describe the SAME BUILD. 3c only proves the
        # ids are internally consistent, which a stale JSON paired with a fresh
        # same-shape matrix also satisfies (BACKLOG #217) — and after 3c that
        # pairing would carry more apparent authority, not less.
        #
        # Distinct from gate 3b: 3b re-encodes the canary TEXT to check the
        # embedding SPACE and needs the model; this compares stored vectors to
        # stored rows, costs three array comparisons, and checks GENERATION.
        if new_content_emb is not None and canaries:
            n_rows = new_content_emb.shape[0]
            expected_rows = sorted({0, n_rows // 2, n_rows - 1}) if n_rows else []
            if len(expected_rows) != len(canaries):
                # Canary layout is not the one this check knows how to locate
                # (older index, or the extractor's selection changed). Skip
                # rather than guess — 3b still covers embedding-space drift.
                logger.debug(
                    "Skipping canary-row check: %d canaries for %d rows does not "
                    "match the expected layout %s.",
                    len(canaries),
                    n_rows,
                    expected_rows,
                )
            else:
                for row, canary in zip(expected_rows, canaries):
                    stored = np.asarray(canary.vector, dtype=np.float32)
                    if stored.shape != new_content_emb[row].shape or not np.allclose(
                        stored, new_content_emb[row], atol=1e-5
                    ):
                        logger.error(
                            "Canary row %d does not match its stored vector: the "
                            "index JSON and the embedding matrix are from "
                            "different builds. Falling back to BM25-only — "
                            "rebuild the index.",
                            row,
                        )
                        new_content_emb = None
                        new_domain_emb = None
                        new_semantic_docs = []
                        break

        # ── gate 3e: build-generation digest check (deterministic) ──
        digests = getattr(new_index, "matrix_digests", None) if new_index else None
        if digests and (new_content_emb is not None or new_domain_emb is not None):
            try:
                checks = []
                if new_content_emb is not None and "content_embeddings" in digests:
                    checks.append(("content_embeddings", new_content_emb))
                if new_domain_emb is not None and "domain_embeddings" in digests:
                    checks.append(("domain_embeddings", new_domain_emb))
                for name, arr in checks:
                    actual = hashlib.sha256(
                        np.asarray(arr, dtype=np.float32).tobytes()
                    ).hexdigest()
                    if actual != digests[name]:
                        logger.error(
                            "Build-generation check FAILED for %s: loaded array "
                            "digest (%s…) does not match the digest stamped at "
                            "build time (%s…). The index files are from different "
                            "builds. Falling back to BM25-only — rebuild the index.",
                            name,
                            actual[:16],
                            digests[name][:16],
                        )
                        new_content_emb = None
                        new_domain_emb = None
                        new_semantic_docs = []
                        break
            except Exception as e:
                logger.error(
                    "Build-generation digest check errored (%s); treating as "
                    "failure and falling back to BM25-only to stay fail-safe.",
                    e,
                )
                new_content_emb = None
                new_domain_emb = None
                new_semantic_docs = []

        # 3d-bis. If the canary-row or digest gate discarded the content matrix above,
        # the domain matrix went with it — drop its mapping too so state stays coherent.
        if new_domain_emb is None:
            new_domain_rows = []

        # 4. Rollback guard — don't swap partial state (new index without matching embeddings)
        if (
            self.content_embeddings is not None
            and new_content_emb is None
            and not model_mismatch
        ):
            self._reload_failures += 1
            level = logging.ERROR if self._reload_failures > 1 else logging.WARNING
            logger.log(
                level,
                "Index reload would lose semantic embeddings — keeping previous "
                "state to prevent degradation (consecutive failures: %d). "
                "Rebuild index to update.",
                self._reload_failures,
            )
            self._index_mtime = current_mtime
            return

        # 5. Atomic swap
        self._reload_failures = 0
        self.index = new_index
        self.content_embeddings = new_content_emb
        self.domain_embeddings = new_domain_emb
        self.semantic_docs = new_semantic_docs
        self.domain_rows = new_domain_rows
        self._build_bm25_index()
        self._index_mtime = current_mtime

    def _check_index_freshness(self) -> None:
        """Reload index if the on-disk file has changed since last load.

        Uses global_index.json mtime as the commit signal — the extractor
        saves embeddings first, JSON last, so a JSON mtime change means
        all index files are ready (see extractor.py save order).
        """
        index_path = self.settings.index_path / "global_index.json"
        try:
            current_mtime = index_path.stat().st_mtime
        except OSError:
            return  # File missing or inaccessible — keep current index

        if current_mtime != self._index_mtime:
            with self._index_lock:
                # Double-checked locking — defensive for future threading
                try:
                    recheck_mtime = index_path.stat().st_mtime
                except OSError:
                    return
                if recheck_mtime != self._index_mtime:
                    logger.info(
                        "Index file changed on disk (mtime: %.2f → %.2f), reloading...",
                        self._index_mtime,
                        recheck_mtime,
                    )
                    self._load_index()
                    self._load_feedback_ratings()

    @staticmethod
    def _build_semantic_docs(
        index: GlobalIndex, n_rows: int
    ) -> list[tuple[str, str, int]] | None:
        """Map each embedding row to the item that owns it, via `embedding_id`.

        Returns a list of length `n_rows` where element `r` is the
        `(domain, item_type, local_idx)` whose vector is `content_embeddings[r]`,
        or None if the index cannot be trusted to describe those rows.

        Why identity and not position: the extractor assigns `embedding_id` in
        build order and writes the vectors in that order, but serializes the
        JSON with `sort_keys=True`, which reorders the `domains` mapping
        alphabetically. Walking the JSON and pairing by enumeration position
        therefore attributes every vector to the wrong item as soon as the two
        orders diverge — the defect that shipped on main between 2026-07-19 and
        2026-07-25, misattributing all 1041 rows. JSON object order is not an
        identity contract; `embedding_id` is.

        The invariant checked here is a bijection: the ids must cover
        [0, n_rows) exactly once. That subsumes missing, duplicate,
        out-of-range and permuted-with-holes ids. It deliberately does NOT
        assert `embedding_id == traversal position` — that would re-codify the
        broken assumption and reject the sorted JSON this mapping exists to
        support.
        """
        return RetrievalEngine._slot_assign(
            [
                (f"{domain_name}/{item_type}[{i}]", (domain_name, item_type, i), eid)
                for domain_name, item_type, i, eid in RetrievalEngine._walk_items(index)
            ],
            n_rows,
            noun="item",
            degrade="Falling back to BM25-only — rebuild the index.",
        )

    @staticmethod
    def _walk_items(index: GlobalIndex) -> list[tuple[str, str, int, object]]:
        """Traverse every embedded item in JSON order, carrying its stamped id."""
        return [
            (domain_name, item_type, i, getattr(item, "embedding_id", None))
            for domain_name, domain_index in index.domains.items()
            for item_type, items in (
                ("principle", domain_index.principles),
                ("method", domain_index.methods),
                ("reference", domain_index.references),
            )
            for i, item in enumerate(items)
        ]

    @staticmethod
    def _build_domain_rows(index: GlobalIndex, n_rows: int) -> list[int] | None:
        """Map each domain-embedding row to the domain_config that owns it.

        BACKLOG #218. Returns a list of length `n_rows` where element `r` is the
        position in `index.domain_configs` whose vector is `domain_embeddings[r]`,
        or None if the matrix cannot be attributed and routing must be disabled.

        `domain_configs` is a JSON list, so `sort_keys=True` leaves its order
        alone and positional pairing happened to survive the #216 defect. That is
        a coincidence of the serialization format — a list could be reordered by
        any future producer change, and nothing would report it. The extractor
        already stamps `DomainConfig.embedding_id`; this reads it.
        """
        return RetrievalEngine._slot_assign(
            [
                (
                    f"domain_configs[{i}] ({dc.name})",
                    i,
                    getattr(dc, "embedding_id", None),
                )
                for i, dc in enumerate(index.domain_configs)
            ],
            n_rows,
            noun="domain",
            degrade="Disabling domain routing — rebuild the index.",
        )

    @staticmethod
    def _slot_assign(entries, n_rows: int, noun: str, degrade: str):
        """Assign each stamped entry to its own row, proving a bijection.

        `entries` is a list of `(label, payload, raw_id)`. Returns a list of
        length `n_rows` holding each row's payload, or None if the ids do not
        cover `[0, n_rows)` exactly once.

        Shared by the content-embedding and domain-embedding mappings so the two
        cannot drift: a second hand-written copy of this validation is how the
        original defect survived — the orphaned first attempt fixed one consumer
        and missed the other.
        """
        stamped = [
            e for e in entries if isinstance(e[2], int) and not isinstance(e[2], bool)
        ]

        # Legacy format: NO entry carries an id. There is no identity information
        # to use, so positional pairing (the pre-existing behaviour) is both the
        # only option and not a regression for such an index. Accepted only when
        # ids are UNIFORMLY absent — a positively identified legacy shape.
        # Partial stamping is corruption and falls through to the checks below.
        # Guard against this path becoming load-bearing again: the current
        # extractor always stamps ids, and the committed-index bijection test
        # fails if that ever stops being true.
        if not stamped and len(entries) == n_rows:
            logger.warning(
                "Index carries no embedding_id on any %s (legacy format); "
                "pairing %s rows by position. Rebuild the index to get "
                "identity-checked retrieval.",
                noun,
                noun,
            )
            return [payload for _, payload, _ in entries]

        slots: list = [None] * n_rows
        labels: list = [None] * n_rows

        for label, payload, row in entries:
            if not isinstance(row, int) or isinstance(row, bool):
                logger.error(
                    "Index %s %s has no usable embedding_id (%r) while others "
                    "do; cannot map embedding rows to items. %s",
                    noun,
                    label,
                    row,
                    degrade,
                )
                return None
            if not 0 <= row < n_rows:
                logger.error(
                    "Index %s %s has embedding_id %d outside the %s matrix "
                    "(%d rows). %s",
                    noun,
                    label,
                    row,
                    noun,
                    n_rows,
                    degrade,
                )
                return None
            if slots[row] is not None:
                # Checked BEFORE assignment: a silent overwrite would leave a
                # hole elsewhere and orphan one entry's vector.
                logger.error(
                    "Duplicate embedding_id %d (claimed by both %s and %s). %s",
                    row,
                    labels[row],
                    label,
                    degrade,
                )
                return None
            slots[row] = payload
            labels[row] = label

        missing = [r for r, v in enumerate(slots) if v is None]
        if missing:
            logger.error(
                "%d embedding row(s) claimed by no index %s (first: %d). The "
                "index and the %s matrix describe different corpora. %s",
                len(missing),
                noun,
                missing[0],
                noun,
                degrade,
            )
            return None

        return slots

    def _build_bm25_index(self) -> None:
        """Build BM25 index from loaded documents."""
        if not self.index:
            return

        corpus = []
        self.bm25_docs = []

        for domain_name, domain_index in self.index.domains.items():
            for i, principle in enumerate(domain_index.principles):
                # Tokenize for BM25 — strip punctuation for consistent matching
                text = self._get_bm25_text(principle)
                tokens = re.findall(r"\w+", text.lower())
                corpus.append(tokens)
                self.bm25_docs.append((domain_name, "principle", i))

            for i, method in enumerate(domain_index.methods):
                text = self._get_method_bm25_text(method)
                tokens = re.findall(r"\w+", text.lower())
                corpus.append(tokens)
                self.bm25_docs.append((domain_name, "method", i))

            for i, ref in enumerate(domain_index.references):
                text = self._get_reference_bm25_text(ref)
                tokens = re.findall(r"\w+", text.lower())
                corpus.append(tokens)
                self.bm25_docs.append((domain_name, "reference", i))

        if corpus:
            self.bm25_index = BM25Okapi(corpus)
            logger.info(f"Built BM25 index with {len(corpus)} documents")

    def _load_feedback_ratings(self) -> None:
        """Load feedback ratings from feedback.jsonl for adaptive retrieval.

        Per contrarian review: activates dormant feedback infrastructure.
        Calculates average rating per principle for score boosting.
        """
        if not self.settings.enable_feedback_adaptation:
            logger.debug("Feedback adaptation disabled")
            return

        feedback_path = self.settings.logs_path / "feedback.jsonl"
        if not feedback_path.exists():
            logger.debug("No feedback file found - adaptive retrieval inactive")
            return

        # Collect ratings per principle
        ratings_by_id: dict[str, list[int]] = {}

        try:
            with open(feedback_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        principle_id = entry.get("principle_id", "")
                        rating = entry.get("rating", 0)
                        if principle_id and 1 <= rating <= 5:
                            if principle_id not in ratings_by_id:
                                ratings_by_id[principle_id] = []
                            ratings_by_id[principle_id].append(rating)
                            # Cap per-principle ratings to prevent feedback poisoning
                            if len(ratings_by_id[principle_id]) > 100:
                                ratings_by_id[principle_id] = ratings_by_id[
                                    principle_id
                                ][-100:]
                    except json.JSONDecodeError:
                        continue  # Skip malformed entries

            # Calculate averages
            for principle_id, ratings in ratings_by_id.items():
                avg = sum(ratings) / len(ratings)
                self._feedback_ratings[principle_id] = (avg, len(ratings))

            if self._feedback_ratings:
                logger.info(
                    f"Loaded feedback for {len(self._feedback_ratings)} principles"
                )
        except Exception as e:
            logger.warning(f"Failed to load feedback: {e}")

    def reload_feedback_ratings(self) -> None:
        """Reload feedback ratings from disk.

        Call this to pick up new feedback without restarting the server.
        """
        self._feedback_ratings = {}
        self._load_feedback_ratings()

    def get_feedback_adjustment(self, principle_id: str) -> float:
        """Get score adjustment for a principle based on feedback.

        Returns:
            Positive value for boost, negative for penalty, 0 for no adjustment.
        """
        if not self.settings.enable_feedback_adaptation:
            return 0.0

        if principle_id not in self._feedback_ratings:
            return 0.0

        avg_rating, count = self._feedback_ratings[principle_id]

        # Require minimum ratings for confidence
        if count < self.settings.feedback_min_ratings:
            return 0.0

        if avg_rating >= self.settings.feedback_boost_threshold:
            return self.settings.feedback_boost_amount
        elif avg_rating <= self.settings.feedback_penalty_threshold:
            return -self.settings.feedback_penalty_amount

        return 0.0

    def _get_bm25_text(self, principle: Principle) -> str:
        """Create text for BM25 indexing."""
        parts = [
            principle.title,
            principle.content[:3000],
            " ".join(principle.metadata.keywords),
            " ".join(principle.metadata.synonyms),
            " ".join(principle.metadata.trigger_phrases),
            " ".join(principle.metadata.failure_indicators),
        ]
        return " ".join(parts)

    def _get_method_bm25_text(self, method: Method) -> str:
        """Create text for BM25 indexing from a method.

        Includes metadata fields for improved keyword matching.
        """
        parts = [
            method.title,
            method.content[:1500],  # Increased from 500
            " ".join(method.keywords),  # Legacy keywords
        ]

        # Add metadata fields for richer keyword matching
        meta = method.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases))
        if meta.purpose_keywords:
            parts.append(" ".join(meta.purpose_keywords))
        if meta.applies_to:
            parts.append(" ".join(meta.applies_to))
        if meta.guideline_keywords:
            parts.append(" ".join(meta.guideline_keywords))

        return " ".join(parts)

    def _get_reference_bm25_text(self, ref: ReferenceEntry) -> str:
        """Create text for BM25 indexing from a reference entry."""
        parts = [
            ref.title,
            ref.summary,
            " ".join(ref.tags),
            ref.content[:1500],
        ]
        meta = ref.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases))
        if meta.purpose_keywords:
            parts.append(" ".join(meta.purpose_keywords))
        if meta.applies_to:
            parts.append(" ".join(meta.applies_to))
        return " ".join(parts)

    # =========================================================================
    # T6: Domain Router
    # =========================================================================

    def route_domains(self, query: str) -> dict[str, float]:
        """Route query to relevant domains using semantic similarity.

        Returns dict of domain_name -> similarity_score.
        """
        if self.domain_embeddings is None or not self.index:
            return {}

        # Encode query — fall back to empty results if daemon unavailable
        try:
            query_embedding = self.embedder.encode([query], normalize_embeddings=True)[
                0
            ]
        except (ConnectionError, RuntimeError) as e:
            logger.warning("Domain routing unavailable (embedding failed): %s", e)
            return {}

        # Calculate similarity with each domain. Rows are attributed by
        # `domain_rows` (embedding_id-keyed, BACKLOG #218), not by position —
        # see _build_domain_rows. An empty mapping means the gate could not
        # attribute the matrix, so routing returns nothing rather than guessing.
        if not self.domain_rows:
            return {}

        scores = {}
        for row, config_idx in enumerate(self.domain_rows):
            if config_idx >= len(self.index.domain_configs):
                continue
            domain_config = self.index.domain_configs[config_idx]
            similarity = self._cosine_similarity(
                query_embedding, self.domain_embeddings[row]
            )
            if similarity >= self.settings.domain_similarity_threshold:
                scores[domain_config.name] = float(similarity)

        # Sort by score and limit
        sorted_scores = dict(
            sorted(scores.items(), key=lambda x: -x[1])[: self.settings.max_domains]
        )

        return sorted_scores

    # =========================================================================
    # T7: BM25 Search
    # =========================================================================

    def bm25_search(
        self, query: str, domains: list[str] | None = None, top_k: int = 50
    ) -> list[tuple[str, str, int, float]]:
        """BM25 keyword search.

        Returns list of (domain, type, local_idx, score).
        """
        if not self.bm25_index:
            return []

        tokens = re.findall(r"\w+", query.lower())
        scores = self.bm25_index.get_scores(tokens)

        # Filter by domains if specified
        results = []
        for idx, score in enumerate(scores):
            if score > 0:
                domain, item_type, local_idx = self.bm25_docs[idx]
                if domains is None or domain in domains:
                    results.append((domain, item_type, local_idx, float(score)))

        # Sort and limit
        results.sort(key=lambda x: -x[3])
        return results[:top_k]

    # =========================================================================
    # T8: Semantic Search
    # =========================================================================

    def semantic_search(
        self, query: str, domains: list[str] | None = None, top_k: int = 50
    ) -> list[tuple[str, str, int, float]]:
        """Semantic search using embeddings.

        Returns list of (domain, type, local_idx, score).
        """
        if self.content_embeddings is None or not self.index:
            return []

        # Encode query — fall back to empty results if daemon unavailable
        try:
            query_embedding = self.embedder.encode([query], normalize_embeddings=True)[
                0
            ]
        except (ConnectionError, RuntimeError) as e:
            logger.warning("Semantic search unavailable (embedding failed): %s", e)
            return []

        # Calculate similarities. Indexed by semantic_docs (embedding_id-keyed),
        # NOT bm25_docs (BM25-corpus-position-keyed) — the two orders diverge
        # whenever the index JSON's domain ordering differs from build order.
        results = []
        for idx in range(len(self.content_embeddings)):
            if idx >= len(self.semantic_docs):
                break

            domain, item_type, local_idx = self.semantic_docs[idx]
            if domains is None or domain in domains:
                similarity = self._cosine_similarity(
                    query_embedding, self.content_embeddings[idx]
                )
                if similarity > 0:
                    results.append((domain, item_type, local_idx, float(similarity)))

        # Sort and limit
        results.sort(key=lambda x: -x[3])
        return results[:top_k]

    # =========================================================================
    # T9: Score Fusion
    # =========================================================================

    def fuse_scores(
        self,
        bm25_results: list[tuple[str, str, int, float]],
        semantic_results: list[tuple[str, str, int, float]],
    ) -> dict[tuple[str, str, int], tuple[float, float, float]]:
        """Fuse BM25 and semantic scores.

        Returns dict of (domain, type, local_idx) -> (bm25_norm, semantic_score, combined).
        """
        # Normalize BM25 scores to 0-1
        max_bm25 = max((r[3] for r in bm25_results), default=1.0)
        bm25_norm = {
            (r[0], r[1], r[2]): r[3] / max_bm25 if max_bm25 > 0 else 0
            for r in bm25_results
        }

        # Semantic scores are already 0-1
        semantic_scores = {(r[0], r[1], r[2]): r[3] for r in semantic_results}

        # Get all keys
        all_keys = set(bm25_norm.keys()) | set(semantic_scores.keys())

        # Renormalize weights onto the signals that are actually present.
        # The configured semantic_weight assumes BOTH retrievers contribute.
        # When one yields nothing — BM25-only read-only mode (no embeddings) or
        # the embedding daemon being down — keeping the full split would cap the
        # surviving signal at its weight (e.g. BM25-only ≤ 1 - semantic_weight =
        # 0.4) and drop every result below min_score_threshold, which is scaled
        # for fused 0-1 scores. Renormalizing keeps the combined score on a 0-1
        # scale comparable to the threshold. (BACKLOG #52.)
        if bm25_results and semantic_results:
            sem_weight = self.settings.semantic_weight
            bm25_weight = 1 - self.settings.semantic_weight
        elif semantic_results:
            sem_weight, bm25_weight = 1.0, 0.0
        else:  # bm25-only (or both empty → no keys, loop is a no-op)
            sem_weight, bm25_weight = 0.0, 1.0

        # Fuse with the (possibly renormalized) weights
        fused = {}
        for key in all_keys:
            bm25_score = bm25_norm.get(key, 0.0)
            sem_score = semantic_scores.get(key, 0.0)

            combined = sem_weight * sem_score + bm25_weight * bm25_score

            fused[key] = (bm25_score, sem_score, combined)

        return fused

    # =========================================================================
    # T10: Cross-Encoder Reranking
    # =========================================================================

    def rerank(
        self, query: str, candidates: list[tuple[str, str, int, float]]
    ) -> list[tuple[str, str, int, float]]:
        """Rerank candidates using cross-encoder.

        Takes top candidates by combined score and reranks with cross-encoder.
        """
        if not candidates or not self.index:
            return candidates

        # Limit to top-k for reranking
        top_candidates = candidates[: self.settings.rerank_top_k]

        # Prepare pairs for cross-encoder
        pairs = []
        for domain, item_type, local_idx, _ in top_candidates:
            text = self._get_candidate_text(domain, item_type, local_idx)
            pairs.append((query, text))

        # Score with cross-encoder — skip reranking if daemon unavailable
        if pairs:
            try:
                rerank_scores = self.reranker.predict(pairs)
            except (ConnectionError, RuntimeError) as e:
                logger.warning(
                    "Reranking unavailable: %s — returning unranked results", e
                )
                return candidates

            # Combine with new scores
            reranked = []
            for i, (domain, item_type, local_idx, _) in enumerate(top_candidates):
                # Normalize cross-encoder score to 0-1 (sigmoid-like)
                score = float(1 / (1 + np.exp(-rerank_scores[i])))
                reranked.append((domain, item_type, local_idx, score))

            # Sort by rerank score
            reranked.sort(key=lambda x: -x[3])
            return reranked

        return top_candidates

    def _get_candidate_text(self, domain: str, item_type: str, local_idx: int) -> str:
        """Get text for a candidate for reranking."""
        if not self.index or domain not in self.index.domains:
            return ""

        domain_index = self.index.domains[domain]

        if item_type == "principle" and local_idx < len(domain_index.principles):
            p = domain_index.principles[local_idx]
            return f"{p.title}\n{p.content[:500]}"
        elif item_type == "method" and local_idx < len(domain_index.methods):
            m = domain_index.methods[local_idx]
            return f"{m.title}\n{m.content[:500]}"
        elif item_type == "reference" and local_idx < len(domain_index.references):
            r = domain_index.references[local_idx]
            return f"{r.title}\n{r.summary}\n{r.content[:500]}"

        return ""

    # =========================================================================
    # T11: Hierarchy Filter
    # =========================================================================

    def apply_hierarchy(
        self, principles: list[ScoredPrinciple]
    ) -> list[ScoredPrinciple]:
        """Apply governance hierarchy ordering.

        S-Series > Constitution > Domain principles.
        Within same level, sort by score.

        Constitution series codes get priority 0-5 (S highest).
        Domain principles all get priority 10 (sorted by score within).
        Series codes like C/Q are shared across domains, so domain
        context is used to disambiguate hierarchy level.
        """

        def sort_key(sp: ScoredPrinciple) -> tuple:
            series = sp.principle.series_code
            is_constitution = sp.principle.domain == "constitution"
            if is_constitution and series:
                hierarchy = self._CONSTITUTION_HIERARCHY.get(series, 6)
            elif series:
                hierarchy = 10  # All domain principles below constitution
            else:
                hierarchy = 99  # No series code — sort by score only
            return (hierarchy, -sp.combined_score, sp.principle.number or 0)

        return sorted(principles, key=sort_key)

    # =========================================================================
    # Main Retrieval Pipeline
    # =========================================================================

    def retrieve(
        self,
        query: str,
        domain: str | None = None,
        include_constitution: bool = True,
        include_methods: bool = True,
        max_results: int | None = None,
    ) -> RetrievalResult:
        """Full hybrid retrieval pipeline.

        1. Route to domains (or use explicit domain)
        2. BM25 keyword search
        3. Semantic search
        4. Score fusion
        5. Reranking
        6. Hierarchy filtering
        """
        start_time = time.time()
        max_results = max_results or self.settings.max_results
        self._check_index_freshness()

        if not self.index:
            return RetrievalResult(
                query=query,
                domains_detected=[],
                domain_scores={},
                constitution_principles=[],
                domain_principles=[],
                methods=[],
                s_series_triggered=False,
                retrieval_time_ms=0,
                semantic_available=False,
                index_loaded=False,
            )

        # Step 1: Route to domains
        if domain:
            # Forced domain - include it in search
            domain_scores = {domain: 1.0} if domain in self.index.domains else {}
            detected_domains = []
            search_domains = [domain] if domain in self.index.domains else []
            if include_constitution and "constitution" not in search_domains:
                search_domains.append("constitution")
        else:
            domain_scores = self.route_domains(query)
            detected_domains = list(domain_scores.keys())
            if detected_domains:
                # Search detected domains plus constitution
                search_domains = list(set(detected_domains + ["constitution"]))
            else:
                # No confident domain match - search ALL domains
                search_domains = list(self.index.domains.keys())

        # Step 2-3: Hybrid search
        bm25_results = self.bm25_search(query, search_domains)
        semantic_results = self.semantic_search(query, search_domains)

        # Step 4: Fuse scores
        fused = self.fuse_scores(bm25_results, semantic_results)

        # Step 5: Prepare candidates for reranking
        candidates = [
            (key[0], key[1], key[2], scores[2])  # domain, type, idx, combined
            for key, scores in fused.items()
            if scores[2] >= self.settings.min_score_threshold
        ]
        candidates.sort(key=lambda x: -x[3])

        # Step 6: Rerank top candidates
        reranked = self.rerank(query, candidates)

        # Step 7: Build scored principles/methods
        constitution_principles: list[ScoredPrinciple] = []
        domain_principles: list[ScoredPrinciple] = []
        methods: list[ScoredMethod] = []
        references: list[ScoredReference] = []
        s_series_triggered = False

        for domain_name, item_type, local_idx, rerank_score in reranked:
            domain_index = self.index.domains.get(domain_name)
            if not domain_index:
                continue

            # Get original scores
            key = (domain_name, item_type, local_idx)
            bm25_norm, sem_score, combined = fused.get(key, (0, 0, rerank_score))

            if item_type == "principle" and local_idx < len(domain_index.principles):
                principle = domain_index.principles[local_idx]

                # Check S-Series
                if principle.series_code == "S":
                    s_series_triggered = True

                # Apply feedback-based score adjustment
                # Per contrarian review: adaptive retrieval based on user feedback
                # S-Series exemption: NEVER penalize safety principles (per second contrarian review)
                feedback_adj = self.get_feedback_adjustment(principle.id)
                if principle.series_code == "S" and feedback_adj < 0:
                    feedback_adj = 0.0  # S-Series exempt from penalties
                adjusted_combined = min(1.0, max(0.0, combined + feedback_adj))
                adjusted_rerank = min(1.0, max(0.0, rerank_score + feedback_adj))

                # Add feedback boost to match reasons if applied
                match_reasons = self._get_match_reasons(bm25_norm, sem_score)
                if feedback_adj > 0:
                    match_reasons.append("feedback boost")
                elif feedback_adj < 0:
                    match_reasons.append("feedback penalty")

                scored = ScoredPrinciple(
                    principle=principle,
                    semantic_score=sem_score,
                    keyword_score=bm25_norm,
                    combined_score=adjusted_combined,
                    rerank_score=adjusted_rerank,
                    confidence=self._get_confidence(adjusted_rerank),
                    match_reasons=match_reasons,
                )

                if domain_name == "constitution":
                    if include_constitution:
                        constitution_principles.append(scored)
                else:
                    domain_principles.append(scored)

            elif item_type == "method" and include_methods:
                if local_idx < len(domain_index.methods):
                    method = domain_index.methods[local_idx]
                    scored_method = ScoredMethod(
                        method=method,
                        semantic_score=sem_score,
                        keyword_score=bm25_norm,
                        combined_score=combined,
                        confidence=self._get_confidence(combined),
                    )
                    methods.append(scored_method)

            elif item_type == "reference":
                if local_idx < len(domain_index.references):
                    ref = domain_index.references[local_idx]
                    # Apply maturity/status score adjustments
                    maturity_adj = {"evergreen": 0.1, "budding": 0.0, "seedling": -0.05}
                    status_adj = {
                        "current": 0.0,
                        "caution": -0.1,
                        "deprecated": -0.2,
                        "archived": -0.3,
                    }
                    adj = (
                        combined
                        + maturity_adj.get(ref.maturity, 0.0)
                        + status_adj.get(ref.status, 0.0)
                    )
                    adj = min(1.0, max(0.0, adj))
                    scored_ref = ScoredReference(
                        reference=ref,
                        semantic_score=sem_score,
                        keyword_score=bm25_norm,
                        combined_score=adj,
                        confidence=self._get_confidence(adj),
                    )
                    references.append(scored_ref)

        # Step 8: Apply hierarchy and limit
        constitution_principles = self.apply_hierarchy(constitution_principles)[
            :max_results
        ]
        domain_principles = self.apply_hierarchy(domain_principles)[:max_results]

        retrieval_time = (time.time() - start_time) * 1000

        return RetrievalResult(
            query=query,
            domains_detected=detected_domains,
            domain_scores=domain_scores,
            constitution_principles=constitution_principles,
            domain_principles=domain_principles,
            methods=methods[:max_results] if include_methods else [],
            references=sorted(references, key=lambda r: r.combined_score, reverse=True)[
                :max_results
            ],
            s_series_triggered=s_series_triggered,
            retrieval_time_ms=retrieval_time,
            # Report the degrade rather than only logging it. Every degrade path
            # (model mismatch, canary failure, row-identity failure) previously
            # returned a response byte-identical to a healthy one, so a caller
            # believed it was governed at full recall while running on keywords
            # alone. That silence is why #216 survived six days on main; the
            # posture (degrade, don't crash) is only defensible if the caller
            # can see it.
            semantic_available=self.content_embeddings is not None,
        )

    # =========================================================================
    # Reference Search
    # =========================================================================

    def search_references(
        self,
        query: str,
        domain: str | None = None,
        tags: list[str] | None = None,
        max_results: int = 5,
        stack: list[str] | None = None,
    ) -> list[ScoredReference]:
        """Search reference library entries only.

        Dedicated retrieval channel for implementation precedent — uses the
        same BM25 + semantic infrastructure but filters to reference entries
        only, so principles and methods don't compete.

        ``stack`` is an optional caller-supplied environment filter (e.g.
        ``["python", "nextjs"]``). When provided, entries whose ``applies_to``
        overlaps are boosted (BACKLOG #46). Boost-only by design: a mismatch is
        neutral, never a de-rank — entries without ``applies_to`` are universal.
        Scoped to this channel only (``retrieve()`` does no attribute filtering
        of references). De-rank-on-mismatch is deferred behind a measurement
        gate.
        """
        self._check_index_freshness()
        if not self.index or not self.bm25_index:
            return []

        start_time = time.time()

        # Determine which domains to search
        search_domains: set[str] | None = None
        if domain:
            if domain not in self.index.domains:
                return []
            search_domains = {domain}

        # --- BM25 search (reference-only) ---
        query_tokens = re.findall(r"\w+", query.lower())
        bm25_scores_raw = self.bm25_index.get_scores(query_tokens)

        bm25_ref_scores: dict[tuple[str, int], float] = {}
        for idx, score in enumerate(bm25_scores_raw):
            if idx >= len(self.bm25_docs):
                break
            doc_domain, item_type, local_idx = self.bm25_docs[idx]
            if item_type != "reference":
                continue
            if search_domains and doc_domain not in search_domains:
                continue
            if score > 0:
                bm25_ref_scores[(doc_domain, local_idx)] = score

        # Normalize BM25 scores
        max_bm25 = max(bm25_ref_scores.values()) if bm25_ref_scores else 1.0
        for key in bm25_ref_scores:
            bm25_ref_scores[key] /= max_bm25

        # --- Semantic search (reference-only) ---
        sem_ref_scores: dict[tuple[str, int], float] = {}
        if self.content_embeddings is not None:
            try:
                query_embedding = self.embedder.encode(
                    [query], normalize_embeddings=True
                )[0]
            except (ConnectionError, RuntimeError) as e:
                logger.warning("Reference semantic search unavailable: %s", e)
                query_embedding = None

            if query_embedding is not None:
                # semantic_docs, not bm25_docs — the second semantic consumer.
                # Fixing only semantic_search() would leave reference retrieval
                # silently misattributed.
                for idx in range(len(self.content_embeddings)):
                    if idx >= len(self.semantic_docs):
                        break
                    doc_domain, item_type, local_idx = self.semantic_docs[idx]
                    if item_type != "reference":
                        continue
                    if search_domains and doc_domain not in search_domains:
                        continue
                    similarity = self._cosine_similarity(
                        query_embedding, self.content_embeddings[idx]
                    )
                    if similarity > 0:
                        sem_ref_scores[(doc_domain, local_idx)] = similarity

        # --- Score fusion ---
        all_keys = set(bm25_ref_scores.keys()) | set(sem_ref_scores.keys())
        results: list[ScoredReference] = []

        # Renormalize weights onto the present signals — mirrors fuse_scores()
        # so BM25-only mode (no embeddings / daemon down) doesn't artificially
        # halve every reference score. (BACKLOG #52, same root cause.)
        if bm25_ref_scores and sem_ref_scores:
            sem_weight = self.settings.semantic_weight
            bm25_weight = 1 - self.settings.semantic_weight
        elif sem_ref_scores:
            sem_weight, bm25_weight = 1.0, 0.0
        else:  # bm25-only (or both empty → no keys)
            sem_weight, bm25_weight = 0.0, 1.0

        for key in all_keys:
            doc_domain, local_idx = key
            domain_index = self.index.domains.get(doc_domain)
            if not domain_index or local_idx >= len(domain_index.references):
                continue

            ref = domain_index.references[local_idx]

            # Status filter — exclude archived and deprecated
            if ref.status in ("archived", "deprecated"):
                continue

            bm25_norm = bm25_ref_scores.get(key, 0.0)
            sem_score = sem_ref_scores.get(key, 0.0)
            combined = sem_weight * sem_score + bm25_weight * bm25_norm

            # Maturity adjustments match retrieve(); status subset since deprecated/archived are pre-filtered
            maturity_adj = {"evergreen": 0.1, "budding": 0.0, "seedling": -0.05}
            status_adj = {"current": 0.0, "caution": -0.1}
            adj = (
                combined
                + maturity_adj.get(ref.maturity, 0.0)
                + status_adj.get(ref.status, 0.0)
            )
            adj = min(1.0, max(0.0, adj))

            # Tag filter — boost matching tags
            if tags:
                ref_tags_lower = {t.lower() for t in ref.tags}
                query_tags_lower = {t.lower() for t in tags}
                overlap = ref_tags_lower & query_tags_lower
                if overlap:
                    adj = min(1.0, adj + 0.05 * len(overlap))

            # Stack filter (BACKLOG #46) — boost-only environment match.
            # Entries without applies_to are universal (no adjustment); a
            # caller stack that does not overlap is neutral, never penalized.
            if stack and ref.applies_to:
                ref_stack = {s.lower() for s in ref.applies_to}
                query_stack = {s.lower() for s in stack}
                stack_overlap = ref_stack & query_stack
                if stack_overlap:
                    adj = min(1.0, adj + 0.05 * len(stack_overlap))

            results.append(
                ScoredReference(
                    reference=ref,
                    semantic_score=sem_score,
                    keyword_score=bm25_norm,
                    combined_score=adj,
                    confidence=self._get_confidence(adj),
                )
            )

        results.sort(key=lambda r: r.combined_score, reverse=True)

        retrieval_time = (time.time() - start_time) * 1000
        logger.info(
            "Reference search: query=%r domain=%s results=%d time=%.1fms",
            query,
            domain or "all",
            len(results),
            retrieval_time,
        )

        return results[:max_results]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.

        Clamps to [0, 1] to prevent float-precision overflow (e.g., 1.0000000149)
        from causing Pydantic ValidationError on fields with le=1.0.
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.clip(np.dot(a, b) / (norm_a * norm_b), 0.0, 1.0))

    def _get_confidence(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if score >= self.settings.confidence_high_threshold:
            return ConfidenceLevel.HIGH
        elif score >= self.settings.confidence_medium_threshold:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _get_match_reasons(self, bm25_score: float, semantic_score: float) -> list[str]:
        """Generate human-readable match reasons."""
        reasons = []
        if bm25_score > 0.5:
            reasons.append("strong keyword match")
        elif bm25_score > 0.2:
            reasons.append("keyword match")
        if semantic_score > 0.7:
            reasons.append("strong semantic similarity")
        elif semantic_score > 0.4:
            reasons.append("semantic similarity")
        return reasons

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_principle_by_id(self, principle_id: str) -> Principle | None:
        """Get a specific principle by its ID.

        Also resolves aliases: if principle_id matches a former ID stored
        in a principle's aliases list, the canonical principle is returned.
        """
        self._check_index_freshness()
        if not self.index:
            return None

        # Search all domains — avoids prefix collision (e.g., "multi" vs "mult")
        for domain_index in self.index.domains.values():
            for principle in domain_index.principles:
                if principle.id == principle_id:
                    return principle

        # Alias resolution: check if the ID matches a former principle ID
        for domain_index in self.index.domains.values():
            for principle in domain_index.principles:
                if principle_id in principle.aliases:
                    return principle

        return None

    def get_method_by_id(self, method_id: str) -> Method | None:
        """Get a specific method by its ID.

        Also resolves aliases: if method_id matches a former ID stored in a
        method's aliases list, the canonical method is returned.
        """
        self._check_index_freshness()
        if not self.index:
            return None

        # Search all domains — avoids prefix collision (e.g., "multi" vs "mult")
        for domain_index in self.index.domains.values():
            for method in domain_index.methods:
                if method.id == method_id:
                    return method

        # Alias resolution: check if the ID matches a former method ID
        for domain_index in self.index.domains.values():
            for method in domain_index.methods:
                if method_id in method.aliases:
                    return method

        return None

    def get_reference_by_id(self, ref_id: str) -> ReferenceEntry | None:
        """Get a specific reference entry by its ID."""
        self._check_index_freshness()
        if not self.index:
            return None

        for domain_index in self.index.domains.values():
            for ref in domain_index.references:
                if ref.id == ref_id:
                    return ref

        return None

    def list_domains(self) -> list[dict]:
        """List all available domains with stats."""
        self._check_index_freshness()
        if not self.index:
            return []

        result = []
        for domain_config in self.index.domain_configs:
            domain_index = self.index.domains.get(domain_config.name)
            result.append(
                {
                    "name": domain_config.name,
                    "display_name": domain_config.display_name,
                    "description": (
                        domain_config.description[:100] + "..."
                        if len(domain_config.description) > 100
                        else domain_config.description
                    ),
                    "principles_count": len(domain_index.principles)
                    if domain_index
                    else 0,
                    "methods_count": len(domain_index.methods) if domain_index else 0,
                    "priority": domain_config.priority,
                }
            )
        return result

    def get_domain_summary(self, domain_name: str) -> dict | None:
        """Get detailed summary of a domain."""
        self._check_index_freshness()
        if not self.index or domain_name not in self.index.domains:
            return None

        domain_index = self.index.domains[domain_name]
        config = next(
            (c for c in self.index.domain_configs if c.name == domain_name), None
        )

        if not config:
            return None

        return {
            "name": domain_name,
            "display_name": config.display_name,
            "description": config.description,
            "principles": [
                {"id": p.id, "title": p.title, "series": p.series_code}
                for p in domain_index.principles
            ],
            "methods": [{"id": m.id, "title": m.title} for m in domain_index.methods],
            "last_extracted": domain_index.last_extracted,
        }


def main():
    """Test retrieval engine."""
    import sys

    settings = load_settings()
    engine = RetrievalEngine(settings)

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "how do I handle incomplete specifications"
    )

    print(f"Query: {query}", file=sys.stderr)
    print("\nDomain routing:", file=sys.stderr)
    for domain, score in engine.route_domains(query).items():
        print(f"  {domain}: {score:.3f}", file=sys.stderr)

    result = engine.retrieve(query)

    print(f"\nRetrieval time: {result.retrieval_time_ms:.1f}ms", file=sys.stderr)
    print(f"S-Series triggered: {result.s_series_triggered}", file=sys.stderr)

    print(f"\nConstitution ({len(result.constitution_principles)}):", file=sys.stderr)
    for sp in result.constitution_principles[:3]:
        print(
            f"  [{sp.confidence.value}] {sp.principle.id}: {sp.principle.title}",
            file=sys.stderr,
        )
        print(
            f"    Scores: BM25={sp.keyword_score:.2f}, Semantic={sp.semantic_score:.2f}, "
            f"Combined={sp.combined_score:.2f}",
            file=sys.stderr,
        )

    print(f"\nDomain ({len(result.domain_principles)}):", file=sys.stderr)
    for sp in result.domain_principles[:5]:
        print(
            f"  [{sp.confidence.value}] {sp.principle.id}: {sp.principle.title}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
