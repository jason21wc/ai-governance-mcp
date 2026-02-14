# Session State

**Last Updated:** 2026-02-13
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Complete
- **Mode:** Standard
- **Active Task:** None — Context Engine v1.1.0 implemented

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v1.1.0** (import enrichment, ranking signals, model eval tooling) |
| Content | **v2.4.1** (Constitution), **v3.10.3** (meta-methods), **v2.10.0** (ai-coding methods), **v2.3.2** (ai-coding principles), **v2.1.1** (multi-agent principles), **v2.12.2** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v1.0.1** (multimodal-rag), **v2.5** (ai-instructions) |
| Tests | **654 pass** (non-slow), 0 failures, deselected (slow/model_eval) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **15 MCP tools** (11 governance + 4 context engine) |
| Domains | **5** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag) |
| Index | **101 principles + 429 methods** (see `tests/benchmarks/` for current totals; taxonomy: 21 codes) |
| Subagents | **10** (code-reviewer, contrarian-reviewer, validator, security-auditor, documentation-writer, orchestrator, test-generator, coherence-auditor, continuity-auditor, voice-coach) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | **MRR=0.746**, **Recall@5=0.850**, **Recall@10=1.000** (v1.1.0, 16 queries, baseline `ce_baseline_2026-02-13.json`) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## What Was Done (2026-02-13)

### Context Engine v1.1.0 — Three Retrieval Improvements

**Improvement 1: Import-Enriched Chunks**
- Added `import_context` field to `ContentChunk` (models.py)
- Tree-sitter AST extracts Python imports, filters to referenced names only
- Max 5 imports, 400 chars cap; star imports always included; alias matching
- Composed at embedding time only — `content` stays clean for display/BM25
- Bumped chunking_version to `tree-sitter-v2` (triggers auto re-index)
- 10 new tests in `TestImportEnrichment`

**Improvement 2: Ranking Signals**
- File-type boost: source +0.02, test -0.02, other 0.0
- Recency boost: <7 days +0.01, >90 days -0.01
- Per-file deduplication: only top chunk per file in results
- Additive bonuses applied before `np.clip(0, 1)` — no Pydantic validation issues
- Added `boost_score` field to `QueryResult`
- 9 new tests in `TestRankingSignals`

**Improvement 3: Embedding Model Evaluation**
- Expanded benchmark queries from 8 to 16 (cross-file, natural language, etc.)
- Added `jinaai/jina-embeddings-v2-small-en` to embedding model allowlist
- Created `scripts/evaluate_embeddings.py` with model comparison and weight sweep
- Added `@pytest.mark.model_eval` marker for model comparison test
- Bumped benchmark version to 2.0

**Review Fixes (post-review):**
- H1: Fixed `_get_imported_names` — use `child_by_field_name("module_name")` for relative import safety
- M1: Fixed import context truncation — line boundary, not mid-import
- M2: Expanded test file detection — Go, Rust, JS/TS, `__tests__/`
- C1: Removed 3x fetch heuristic — fetch all candidates before dedup
- Added Jina model to `TestCompareModels.CANDIDATE_MODELS`
- 3 new tests added (relative imports, line-boundary truncation, expanded test detection)

**Total:** 654 tests pass (non-slow), 0 failures, ruff clean

### Benchmark Results (v1.1.0 vs v1.0.0)

| Metric | v1.0.0 | v1.1.0 | Change |
|--------|--------|--------|--------|
| MRR | 0.692 | **0.746** | +7.8% |
| Recall@5 | 0.800 | **0.850** | +6.3% |
| Recall@10 | 0.800 | **1.000** | +25.0% |

16 queries (was 8). 10/16 hit rank 1. Worst rank: 5. Baseline saved: `ce_baseline_2026-02-13.json`

## Next Actions

### 1. Run Embedding Model Evaluation (optional)
```bash
python scripts/evaluate_embeddings.py
python scripts/evaluate_embeddings.py --sweep-weights
```

### 3. Backlog — Project Initialization Part B
Three deferred approaches for closing the bootstrap gap beyond advisory guidance. Documented in PROJECT-MEMORY.md > Roadmap > Part B. Revisit when prioritized.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
