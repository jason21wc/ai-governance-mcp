# Session State

**Last Updated:** 2026-02-14
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Complete
- **Mode:** Standard
- **Active Task:** None — CE natural usage improvements shipped (6e81c77)

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v1.1.0** (import enrichment, ranking signals, model eval tooling) |
| Content | **v2.4.1** (Constitution), **v3.10.3** (meta-methods), **v2.10.0** (ai-coding methods), **v2.3.2** (ai-coding principles), **v2.1.1** (multi-agent principles), **v2.12.2** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v1.0.1** (multimodal-rag), **v2.5** (ai-instructions) |
| Tests | **703 pass** (non-slow), 0 failures, deselected (slow/model_eval) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **15 MCP tools** (11 governance + 4 context engine) |
| Domains | **5** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag) |
| Index | **101 principles + 429 methods** (see `tests/benchmarks/` for current totals; taxonomy: 21 codes) |
| Subagents | **10** (code-reviewer, contrarian-reviewer, validator, security-auditor, documentation-writer, orchestrator, test-generator, coherence-auditor, continuity-auditor, voice-coach) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | **MRR=0.746**, **Recall@5=0.850**, **Recall@10=1.000** (v1.1.0, 16 queries, baseline `ce_baseline_2026-02-13.json`) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Next Actions

### 1. Run Embedding Model Evaluation (optional)
```bash
python scripts/evaluate_embeddings.py
python scripts/evaluate_embeddings.py --sweep-weights
```

### 2. Verify Jina Model Safetensors (before recommending)
Manually confirm `jinaai/jina-embeddings-v2-small-en` publishes safetensors weights on HuggingFace. If not, remove from allowlist.

### 3. Backlog — Project Initialization Part B
Three deferred approaches for closing the bootstrap gap beyond advisory guidance. Documented in PROJECT-MEMORY.md > Roadmap > Part B. Revisit when prioritized.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
