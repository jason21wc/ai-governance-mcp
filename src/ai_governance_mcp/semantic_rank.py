"""Local chunk + embed + rank filter for fetched web content (BACKLOG #186 Stage 1).

A semantic filter that runs BEFORE fetched content enters an agent's context
(filter-before-read): a question plus one or more fetched pages go in, the most
relevant passages come out. It is the *replicable* half of Exa's pipeline — chunk-level
embed-and-rank — mapped onto this project's shared embedding daemon
(``embedding_ipc.EmbeddingClient``). It does NOT fetch: the name ``semantic_rank`` is a
contract, not a description of convenience.

Design rules (evidence-anchored, wf_b3316576-2d8):

* **bge query prefix on QUERIES ONLY.** ``QUERY_PREFIX`` is prepended to the query, never
  to chunks (asymmetric bge-small usage). Default on; the CLI ``--no-query-prefix`` turns
  it off. This module only — the shared governance index does not use the prefix.
* **normalize_embeddings=True**, so cosine similarity == dot product.
* **Two ceilings, guard the RIGHT one.** The IPC transport rejects text above 6000 chars
  (``embedding_ipc.MAX_TEXT_LENGTH``) with a loud error, but bge-small *silently* truncates
  at 512 tokens ≈ ~2000 chars of English (~4 chars/token). The real hazard is the silent
  one, so ``MAX_CHUNK_CHARS = 2000`` is the hard ceiling for ``chunk_chars`` — text above
  it is rejected, never silently truncated. The ~4-chars/token assumption is **English-only**;
  CJK collapses the ratio and even the defaults would truncate.
* **The query is the un-chunked text — bound it too.** The query is embedded whole with the
  prefix prepended, so a long query could itself blow past the 512-token wall with no signal.
  ``MAX_QUERY_CHARS`` bounds the *raw* query so the prefixed query stays within
  ``MAX_CHUNK_CHARS``; the ceiling therefore shifts with ``use_query_prefix`` (documented on
  ``rank_chunks``), and the raw query is prechecked with a query-specific error.
* **No fixed cosine threshold.** For bge only relative order is meaningful, so ranking exposes
  top-k + score + ``gap_to_top`` + optional z-score, plus a ``stats`` distribution to feed
  Stage-2 calibration — never an absolute cut.

Reranking (cross-encoder ``predict()``) is Stage 2 and measurement-gated; this module is the
bi-encoder Stage 1 only.
"""

from __future__ import annotations

import os
import socket
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #

# Asymmetric bge-small usage: prefix the QUERY only, never the passages/chunks.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

DEFAULT_CHUNK_CHARS = 1000  # ~250 tokens English
# Hard token-safety ceiling (~500 tokens English). NOT the IPC bound (6000): bge-small
# silently truncates at 512 tokens ≈ ~2000 chars, so we reject above this rather than let
# a chunk be silently halved. See module docstring, "Two ceilings".
MAX_CHUNK_CHARS = 2000
DEFAULT_OVERLAP_CHARS = 350  # overlap helps 384-dim embedders retain boundary context
DEFAULT_TOP_K = 8

# Recursive-splitter separator ladder, highest-preference first. Each separator keeps its
# trailing occurrence attached to the preceding piece so pieces tile the document exactly
# (contiguous, gap-free) — that is what makes every emitted chunk an exact slice.
_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " "]


def _int_env(name: str, default: int) -> int:
    """Read a positive-int override from the environment, falling back on bad values.

    Pattern mirrors scripts/codex_review.py:_int_env (scripts don't import each other).
    """
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


# Input bounds — oversize input yields a clean typed error, never an OOM. Env-overridable.
MAX_TOTAL_INPUT_BYTES = _int_env("SEMANTIC_RANK_MAX_TOTAL_BYTES", 50 * 1024 * 1024)
MAX_DOCUMENTS = _int_env("SEMANTIC_RANK_MAX_DOCUMENTS", 200)
MAX_DOC_BYTES = _int_env("SEMANTIC_RANK_MAX_DOC_BYTES", 10 * 1024 * 1024)
MAX_TOTAL_CHUNKS = _int_env("SEMANTIC_RANK_MAX_TOTAL_CHUNKS", 20_000)

# Raw-query ceiling so the *prefixed* query stays within MAX_CHUNK_CHARS (see docstring).
MAX_QUERY_CHARS = MAX_CHUNK_CHARS - len(QUERY_PREFIX)

# Batch cap matches embedding_ipc.MAX_TEXTS_PER_REQUEST (kept local; no server import).
_EMBED_BATCH = 1000

# Default daemon socket (mirrors embedding_ipc.DEFAULT_SOCKET_PATH); resolved lazily.
_DEFAULT_SOCKET = Path.home() / ".context-engine" / "embed.sock"
_PROBE_TIMEOUT = 0.25  # seconds; single non-retrying liveness probe


class EmbedderUnavailableError(RuntimeError):
    """No embedding backend is available (daemon down and local fallback not permitted)."""


# --------------------------------------------------------------------------- #
# Chunking                                                                     #
# --------------------------------------------------------------------------- #


def chunk_text(
    text: str, *, chunk_chars: int, overlap_chars: int
) -> list[tuple[str, int]]:
    """Split ``text`` into overlapping chunks that are EXACT slices of the input.

    Returns a list of ``(chunk, start)`` pairs where the invariant
    ``text[start:start + len(chunk)] == chunk`` holds for every pair — offsets are
    provenance-grade, so there is no whitespace normalization inside a chunk. ``start``
    is a Python **codepoint** index (str slicing), not a UTF-8 byte offset; a consumer
    indexing raw bytes of a multibyte document must convert.

    The splitter walks a separator ladder (paragraph → line → sentence → word), packing
    greedily up to ``chunk_chars`` and preferring higher boundaries. Overlap is the exact
    trailing suffix of the previous chunk, aligned to a piece boundary (never a mid-word
    cut). A run with no separator (e.g. a minified blob) is hard-sliced at ``chunk_chars``.

    Raises ``ValueError`` unless ``0 < chunk_chars <= MAX_CHUNK_CHARS`` and
    ``0 <= overlap_chars < chunk_chars`` (a chunk above the ceiling would be silently
    truncated by bge; overlap ≥ chunk cannot make forward progress).
    """
    if chunk_chars <= 0:
        raise ValueError(f"chunk_chars must be positive, got {chunk_chars}")
    if chunk_chars > MAX_CHUNK_CHARS:
        raise ValueError(
            f"chunk_chars {chunk_chars} exceeds MAX_CHUNK_CHARS {MAX_CHUNK_CHARS} "
            f"(bge-small silently truncates above ~512 tokens ≈ {MAX_CHUNK_CHARS} chars)"
        )
    if overlap_chars < 0:
        raise ValueError(f"overlap_chars must be non-negative, got {overlap_chars}")
    if overlap_chars >= chunk_chars:
        raise ValueError(
            f"overlap_chars {overlap_chars} must be less than chunk_chars {chunk_chars}"
        )

    if not text.strip():
        return []

    pieces = _split_into_pieces(text, 0, chunk_chars, _SEPARATORS)
    return _pack_pieces(text, pieces, chunk_chars, overlap_chars)


def _split_into_pieces(
    text: str, offset: int, chunk_chars: int, separators: list[str]
) -> list[tuple[int, int]]:
    """Recursively cut ``text`` into contiguous, gap-free (start, end) spans.

    Every returned span is ≤ ``chunk_chars`` and abuts its neighbour (piece[i].end ==
    piece[i+1].start), so the spans tile ``text`` exactly. Spans are relative to the whole
    document via ``offset``.
    """
    if len(text) <= chunk_chars:
        return [(offset, offset + len(text))]

    for idx, sep in enumerate(separators):
        if sep not in text:
            continue
        pieces: list[tuple[int, int]] = []
        segments = _cut_after(text, sep)
        for seg_start, seg_end in segments:
            segment = text[seg_start:seg_end]
            if len(segment) <= chunk_chars:
                pieces.append((offset + seg_start, offset + seg_end))
            else:
                pieces.extend(
                    _split_into_pieces(
                        segment, offset + seg_start, chunk_chars, separators[idx + 1 :]
                    )
                )
        return pieces

    # No separator present: hard-slice into chunk_chars-sized contiguous spans.
    return [
        (offset + i, offset + min(i + chunk_chars, len(text)))
        for i in range(0, len(text), chunk_chars)
    ]


def _cut_after(text: str, sep: str) -> list[tuple[int, int]]:
    """Cut ``text`` into contiguous (start, end) spans, ending each after a ``sep``.

    The separator stays attached to the piece it follows, so the spans tile ``text``.
    """
    spans: list[tuple[int, int]] = []
    start = 0
    pos = text.find(sep)
    while pos != -1:
        end = pos + len(sep)
        spans.append((start, end))
        start = end
        pos = text.find(sep, start)
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def _pack_pieces(
    text: str,
    pieces: list[tuple[int, int]],
    chunk_chars: int,
    overlap_chars: int,
) -> list[tuple[str, int]]:
    """Greedily pack contiguous pieces into ≤ chunk_chars chunks with piece-aligned overlap."""
    chunks: list[tuple[str, int]] = []
    n = len(pieces)
    i = 0
    while i < n:
        cur_start = pieces[i][0]
        j = i
        while j < n and (pieces[j][1] - cur_start) <= chunk_chars:
            j += 1
        if j == i:  # defensive: a single piece already exceeds the ceiling
            j = i + 1
        chunk_end = pieces[j - 1][1]
        chunks.append((text[cur_start:chunk_end], cur_start))
        if j >= n:
            break
        # Back up to include a trailing suffix of pieces within overlap_chars, aligned to a
        # piece boundary. Guarantee forward progress: never re-consume the whole chunk.
        m = j
        while m > i + 1 and (chunk_end - pieces[m - 1][0]) <= overlap_chars:
            m -= 1
        i = m
    return chunks


# --------------------------------------------------------------------------- #
# Ranking (PURE — no I/O; embed_fn is injected)                                #
# --------------------------------------------------------------------------- #


def _embed_batched(embed_fn, texts: list[str]) -> np.ndarray:
    """Embed ``texts`` in batches of ``_EMBED_BATCH``, guarding the silent-truncation wall.

    Belt-and-suspenders: chunk_text already keeps chunks ≤ MAX_CHUNK_CHARS, but any text
    that would be silently truncated by bge-small is rejected loudly here before it reaches
    the model. A mid-batch error propagates (no partial results).
    """
    for t in texts:
        if len(t) > MAX_CHUNK_CHARS:
            raise ValueError(
                f"text of {len(t)} chars exceeds MAX_CHUNK_CHARS {MAX_CHUNK_CHARS} "
                f"(would be silently truncated by the embedder)"
            )
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    rows = []
    for start in range(0, len(texts), _EMBED_BATCH):
        batch = texts[start : start + _EMBED_BATCH]
        rows.append(np.asarray(embed_fn(batch), dtype=np.float64))
    return np.vstack(rows)


def _check_query(query: str, use_query_prefix: bool) -> str:
    """Validate the query and return the (optionally prefixed) text to embed.

    The query is the one text that is never chunked, so it is bounded here. The effective
    ceiling shifts with ``use_query_prefix`` because the prefix eats into the 512-token wall.
    """
    if not query.strip():
        raise ValueError("query must be a non-empty string")
    ceiling = MAX_QUERY_CHARS if use_query_prefix else MAX_CHUNK_CHARS
    if len(query) > ceiling:
        prefix_note = (
            f" (prefix adds {len(QUERY_PREFIX)} chars toward the {MAX_CHUNK_CHARS}-char wall)"
            if use_query_prefix
            else ""
        )
        raise ValueError(
            f"query of {len(query)} chars exceeds the query ceiling {ceiling}{prefix_note}; "
            f"shorten the query or (last resort) pass --no-query-prefix"
        )
    return QUERY_PREFIX + query if use_query_prefix else query


def _validate_documents(documents: list[dict]) -> None:
    """Enforce input bounds so oversize input fails cleanly instead of OOMing."""
    if not documents:
        raise ValueError("documents must be a non-empty list")
    if len(documents) > MAX_DOCUMENTS:
        raise ValueError(
            f"too many documents: {len(documents)} > MAX_DOCUMENTS {MAX_DOCUMENTS}"
        )
    total = 0
    for i, doc in enumerate(documents):
        # Typed error for direct (non-CLI) callers: the CLI normalizes documents, but a
        # library caller passing a malformed dict should get a clean ValueError, not a
        # raw KeyError/AttributeError downstream (session-241 review LOW).
        if not isinstance(doc, dict) or "doc_id" not in doc or "text" not in doc:
            raise ValueError(
                f"documents[{i}] must be a dict with 'doc_id' and 'text' keys"
            )
        if not isinstance(doc["text"], str):
            raise ValueError(f"documents[{i}] 'text' must be a str")
        nbytes = len(doc["text"].encode("utf-8"))
        if nbytes > MAX_DOC_BYTES:
            raise ValueError(
                f"document {doc.get('doc_id')!r} is {nbytes} bytes > "
                f"MAX_DOC_BYTES {MAX_DOC_BYTES}"
            )
        total += nbytes
    if total > MAX_TOTAL_INPUT_BYTES:
        raise ValueError(
            f"total input {total} bytes > MAX_TOTAL_INPUT_BYTES {MAX_TOTAL_INPUT_BYTES}"
        )


def _stats(scores: np.ndarray, backend: str, n_docs: int, n_deduped: int) -> dict:
    """Distribution summary, safe for n=0 (empty) and n=1 (std=0). Never NaN/inf."""
    n = int(scores.size)
    base = {
        "n_docs": n_docs,
        "n_chunks": n,
        "n_deduped": n_deduped,
        "backend": backend,
    }
    if n == 0:
        base.update(
            {"min": None, "max": None, "mean": None, "std": None, "percentiles": None}
        )
        return base
    base.update(
        {
            "min": float(scores.min()),
            "max": float(scores.max()),
            "mean": float(scores.mean()),
            "std": float(scores.std()),  # population std; 0.0 for n=1, always finite
            "percentiles": {
                "p50": float(np.percentile(scores, 50)),
                "p90": float(np.percentile(scores, 90)),
                "p99": float(np.percentile(scores, 99)),
            },
        }
    )
    return base


def rank_chunks(
    query: str,
    documents: list[dict],
    *,
    embed_fn,
    top_k: int = DEFAULT_TOP_K,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    use_query_prefix: bool = True,
    zscore: bool = False,
    backend: str = "unknown",
) -> dict:
    """Rank every chunk of every document against ``query``; return the top ``top_k``.

    PURE: all embedding I/O flows through the injected ``embed_fn`` (a callable
    ``list[str] -> ndarray`` that MUST already normalize, so cosine == dot). ``documents``
    is a list of ``{"doc_id": str, "text": str}`` — id/url precedence is the CLI's job.

    Guarantees the plan pins: the raw query is bounded (ceiling shifts with
    ``use_query_prefix``); the prefix is applied to the QUERY only; exact-duplicate chunk
    texts are collapsed (first kept, ``n_deduped`` counted; near-dups from overlap rank
    adjacently); ties break deterministically by (score desc, document order, chunk_index);
    ``gap_to_top`` is 0 at rank 1 and shared by ties; stats are NaN-free at n=0 and n=1.
    ``backend`` always appears in the result and in ``stats``.
    """
    q_text = _check_query(query, use_query_prefix)
    _validate_documents(documents)

    # Chunk each document independently — overlap never bleeds across documents.
    records: list[dict] = []
    seen_texts: set[str] = set()
    n_deduped = 0
    for doc_order, doc in enumerate(documents):
        doc_id = doc["doc_id"]
        for chunk_index, (chunk, start) in enumerate(
            chunk_text(
                doc["text"], chunk_chars=chunk_chars, overlap_chars=overlap_chars
            )
        ):
            if chunk in seen_texts:
                n_deduped += 1
                continue
            seen_texts.add(chunk)
            records.append(
                {
                    "doc_id": doc_id,
                    "doc_order": doc_order,
                    "chunk_index": chunk_index,
                    "chunk_start": start,
                    "text": chunk,
                }
            )
            # Enforce the cap INCREMENTALLY: a pathological chunk/overlap ratio
            # (e.g. chunk_chars 2000 / overlap 1999 → ~1 char advance) would otherwise
            # materialize tens of GB before a post-loop check ever ran (both reviewers,
            # session-241). Raise as soon as the count crosses the bound.
            if len(records) > MAX_TOTAL_CHUNKS:
                raise ValueError(
                    f"total chunks exceeded MAX_TOTAL_CHUNKS {MAX_TOTAL_CHUNKS} "
                    "(reduce input size or raise --overlap-chars headroom)"
                )

    if not records:
        return {
            "query": query,
            "backend": backend,
            "results": [],
            "stats": _stats(np.zeros(0), backend, len(documents), n_deduped),
        }

    q_emb = _embed_batched(embed_fn, [q_text])[0]
    chunk_embs = _embed_batched(embed_fn, [r["text"] for r in records])
    scores = chunk_embs @ q_emb  # cosine == dot (embed_fn normalized)

    mean = float(scores.mean())
    std = float(scores.std())
    top_score = float(scores.max())

    for rec, score in zip(records, scores):
        rec["score"] = float(score)
        rec["gap_to_top"] = top_score - float(score)
        if zscore:
            rec["zscore"] = 0.0 if std == 0.0 else (float(score) - mean) / std

    # Deterministic order: score desc, then document order, then chunk_index.
    ordered = sorted(
        records, key=lambda r: (-r["score"], r["doc_order"], r["chunk_index"])
    )

    results = []
    for rank, rec in enumerate(ordered[:top_k], start=1):
        out = {
            "doc_id": rec["doc_id"],
            "chunk_index": rec["chunk_index"],
            "chunk_start": rec["chunk_start"],
            "text": rec["text"],
            "score": rec["score"],
            "gap_to_top": rec["gap_to_top"],
            "rank": rank,
        }
        if zscore:
            out["zscore"] = rec["zscore"]
        results.append(out)

    return {
        "query": query,
        "backend": backend,
        "results": results,
        "stats": _stats(scores, backend, len(documents), n_deduped),
    }


# --------------------------------------------------------------------------- #
# Embedder backends (IPC-first, local torch only behind allow_local)           #
# --------------------------------------------------------------------------- #


def _probe_socket(path: Path) -> bool:
    """Single non-retrying liveness probe for the embedding daemon socket.

    Deliberately NOT ``EmbeddingClient.available()``: that path retries 5× with backoff
    and, on a *stale* socket file (daemon killed by OOM/crash, so its unlink never ran),
    runs that loop twice — ~6s of dead wait in exactly the N-parallel-agents scenario this
    module targets. One connect with a short timeout fails fast instead.
    """
    if not path.exists():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(_PROBE_TIMEOUT)
        sock.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _make_ipc_embed_fn(path: Path):
    """Wrap the daemon client's encode as a normalize-on embed_fn (label 'ipc')."""
    from ai_governance_mcp.embedding_ipc import EmbeddingClient  # numpy/stdlib only

    client = EmbeddingClient(socket_path=path)

    def _embed(texts: list[str]) -> np.ndarray:
        return client.encode(texts, normalize_embeddings=True)

    return _embed


def _load_local_embed_fn():
    """Lazily load a local SentenceTransformer as embed_fn (label 'local').

    Import is deferred to call time so ``import semantic_rank`` never pulls torch — the
    OOM-gate guarantee for N background agents. Monkeypatch seam: tests replace this attr.
    """
    from sentence_transformers import SentenceTransformer  # lazy — heavy (torch)

    model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        trust_remote_code=False,
        model_kwargs={"use_safetensors": True},
    )

    def _embed(texts: list[str]) -> np.ndarray:
        return model.encode(texts, normalize_embeddings=True)

    return _embed


def make_embed_fn(allow_local: bool = False):
    """Resolve an embedding backend, IPC-first. Returns ``(embed_fn, label)``.

    Order: honor the ``AI_CONTEXT_ENGINE_EMBED_SOCKET=none`` disable sentinel (caller-gated
    per embedding_ipc), else probe the daemon socket once (fast-fail) and wrap its client
    ("ipc"). If no daemon is reachable, raise ``EmbedderUnavailableError`` UNLESS
    ``allow_local`` — only then load a local SentenceTransformer ("local"), so N parallel
    background agents never trigger surprise N×torch loads. A missing local dependency
    surfaces as ``EmbedderUnavailableError``, not a raw ImportError.
    """
    socket_env = os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip()
    if socket_env.lower() != "none":
        path = Path(socket_env).expanduser() if socket_env else _DEFAULT_SOCKET
        if _probe_socket(path):
            return _make_ipc_embed_fn(path), "ipc"

    if allow_local:
        try:
            return _load_local_embed_fn(), "local"
        except ImportError as exc:
            raise EmbedderUnavailableError(
                f"local embedder unavailable (sentence-transformers not installed): {exc}"
            ) from exc

    raise EmbedderUnavailableError(
        "no embedding daemon reachable; start the watcher daemon or pass --allow-local"
    )
