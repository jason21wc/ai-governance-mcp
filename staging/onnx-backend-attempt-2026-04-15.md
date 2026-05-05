# ONNX Embedding Backend — Investigation Artifact (2026-04-15)

**Status:** Not shipped. Preserved as historical investigation artifact. BACKLOG #49 closed session-147 — shared IPC service shipped as the production solution.

## What this is

A 296-line git patch (`onnx-backend-attempt-2026-04-15.patch`) capturing a 10-file working-tree diff from a previous session that attempted to address backlog #49 ("Embedding Model Memory Sharing Across Processes") by adding a pluggable `backend="onnx"` parameter to `SentenceTransformer` / `CrossEncoder` via `optimum[onnxruntime]`.

Files touched:
- `pyproject.toml` — added `optimum[onnxruntime]>=1.24.0`
- `src/ai_governance_mcp/config.py` — new `embedding_backend` setting
- `src/ai_governance_mcp/retrieval.py` — backend-aware embedder + reranker loading
- `src/ai_governance_mcp/extractor.py` — `EmbeddingGenerator.backend` param
- `src/ai_governance_mcp/context_engine/indexer.py` — `Indexer.backend` param + **stale-default cleanup** (nomic-embed → bge-small, 768d → 384d)
- `src/ai_governance_mcp/context_engine/project_manager.py` — backend propagation
- `src/ai_governance_mcp/context_engine/server.py` — `AI_CONTEXT_ENGINE_EMBEDDING_BACKEND` env var
- `src/ai_governance_mcp/context_engine/watcher_daemon.py` — same env var wiring
- `tests/test_context_engine.py` / `tests/test_extractor.py` — assertion updates

The implementation itself was mechanically clean and the `CrossEncoder(backend=...)` contract was verified against the installed sentence-transformers 5.2.0 source.

## Why it was NOT shipped

**The envelope math invalidated it as a #49 answer.** Two contrarian-reviewer passes on 2026-04-15 established:

1. **`backend="onnx"` does not avoid loading PyTorch.** `sentence-transformers` imports `torch` unconditionally at module load (`SentenceTransformer.py:17,25-26`, `Transformer.py:17-18`) because `transformers` is a hard transitive dependency. The `backend` kwarg only routes `_load_model()` to either `AutoModel.from_pretrained()` (torch weights) or `ORTModelForFeatureExtraction.from_pretrained()` (ONNX weights) — at inference time, downstream of module init. The "lighter than PyTorch" framing in the original diff comment was technically false.

2. **Savings math:** BGE-small ≈130 MB + reranker (ms-marco-MiniLM-L-6-v2) ≈90 MB. At 50% model-weight savings on ONNX: ~110 MB × 5 processes = **~550 MB total savings**. The actual torch/transformers runtime duplication is ~500 MB–1 GB × 5 = **2.5–5 GB**, which this diff does not touch. Net: ~2% of the 27 GB symptom backlog #49 documents.

3. **Shipping it under the #49 banner would violate `meta-safety-transparent-limitations`.** The correct response to "the partial win is ~2% of the symptom" is *not* to ship the partial win with honest framing — it's to recognize forward-continuation bias and redirect effort to something that actually addresses the symptom.

Full reasoning captured in `BACKLOG.md` #49 (Status 2026-04-15 block) and `LEARNING-LOG.md` under "Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)".

## What's still useful in this patch

**One genuine correctness fix** was discovered during the investigation and is being cherry-picked independently as its own commit (NOT from this patch, but mirroring its contents):

- `src/ai_governance_mcp/context_engine/indexer.py` had stale defaults:
  - `embedding_model="nomic-ai/nomic-embed-text-v1.5"` — should be `"BAAI/bge-small-en-v1.5"`
  - `embedding_dimensions=768` — should be `384`
  - `MAX_EMBEDDING_INPUT_CHARS` comment referenced `nomic-embed-text-v1.5 (8K token context)` — should describe BGE-small's ~512-token limit.

These were left over from a "nomic-embed evaluated but never deployed" trial (see backlog #49 key finding). Production has always used `BAAI/bge-small-en-v1.5` / 384d via config overrides. The stale defaults would never trigger in normal operation but are a latent bug waiting for someone to instantiate `Indexer()` without args.

## How to use this artifact

**If you're a future session encountering memory regression:**
1. Read `OPERATIONS.md` T-049 for the current tripwire and calendar review date.
2. Read `BACKLOG.md` entry #49 (CLOSED) for the summary of what shipped.
3. Read `LEARNING-LOG.md` for "Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)".
4. Read this file for the ONNX-route investigation summary (rejected approach).
5. **Do not `git apply` this patch.** It was deliberately not shipped. The shared IPC service (Phase 2) was the production solution.
6. If you want to verify the envelope math yourself: `python -c "import sentence_transformers; print(sentence_transformers.__file__)"` → read `SentenceTransformer.py:17,25-26` and `Transformer.py:17-18` to confirm torch is imported unconditionally.

**If you're investigating a different question and wondering "why is there an ONNX patch here":**
The short answer: it's an investigation artifact, not abandoned work. The reasoning is in this file and in the plan document. Do not feel obligated to "finish" it.

## Alternatives considered (resolved)

1. **Shared embedding service via IPC** — shipped as Phase 2 (sessions 106-108). Single daemon loads BGE-small-en-v1.5 once; all other processes call via `EmbeddingClient` over Unix socket. Governance servers 800 MB → 85 MB. This is the production solution.
2. **Direct `optimum.onnxruntime.ORTModelForFeatureExtraction` + `tokenizers`** — not pursued. The IPC approach solved the problem without reimplementing the embedding pipeline.
