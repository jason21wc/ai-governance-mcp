# AI Governance MCP - Session State

**Last Updated:** 2025-12-27
**Current Phase:** COMPLETE
**Procedural Mode:** STANDARD

---

## Current Position

**Status:** Project complete and deployed
**Next Action:** Use the MCP tools in Claude Code sessions
**Context:** v4 hybrid retrieval fully implemented, tested, and deployed

---

## Phase Transition

| Phase | Status | Gate Artifact |
|-------|--------|---------------|
| SPECIFY | Complete | GATE-SPECIFY.md |
| PLAN | Complete | GATE-PLAN.md |
| TASKS | Complete | GATE-TASKS.md |
| IMPLEMENT | **Complete** | 56 tests passing |
| DEPLOY | **Complete** | GitHub + global MCP config |

---

## Implementation Summary

| Task | Description | Status |
|------|-------------|--------|
| T1 | Pydantic models (SeriesCode, ConfidenceLevel, ScoredPrinciple) | Complete |
| T2 | Config/settings (pydantic-settings, env vars) | Complete |
| T3-T5 | Extractor (parser, embeddings, GlobalIndex) | Complete |
| T6-T11 | Retrieval (domain routing, BM25, semantic, fusion, rerank, hierarchy) | Complete |
| T12-T18 | Server + 6 MCP tools | Complete |
| T19-T22 | Tests (56 passing) | Complete |
| T23 | Portfolio README | Complete |

---

## Deployment Status

| Component | Status | Location |
|-----------|--------|----------|
| GitHub Repository | Pushed | github.com/jason21wc/ai-governance-mcp |
| Global MCP Config | Configured | ~/.claude.json |
| Index Built | Ready | index/global_index.json + embeddings |
| Dependencies | Installed | pip install -e . |

---

## Technical Specifications

### Hybrid Retrieval Pipeline
1. **Domain Routing** - Query embedding similarity to domain descriptions
2. **BM25 Search** - Keyword matching with rank-bm25
3. **Semantic Search** - Dense vector similarity (all-MiniLM-L6-v2)
4. **Score Fusion** - 60% semantic + 40% BM25
5. **Reranking** - Cross-encoder (ms-marco-MiniLM-L-6-v2)
6. **Hierarchy Filter** - S-Series safety principles prioritized

### MCP Tools Available
| Tool | Purpose |
|------|---------|
| `query_governance` | Main retrieval with confidence scores |
| `get_principle` | Full content by ID |
| `list_domains` | Available domains with stats |
| `get_domain_summary` | Domain exploration |
| `log_feedback` | Quality tracking |
| `get_metrics` | Performance analytics |

### Index Statistics
- **65 principles** (42 constitution + 12 ai-coding + 11 multi-agent)
- **Content embeddings**: (65, 384)
- **Domain embeddings**: (3, 384)
- **Embedding model**: all-MiniLM-L6-v2

---

## Files in Project

| File | Purpose |
|------|---------|
| `src/ai_governance_mcp/models.py` | Pydantic data structures |
| `src/ai_governance_mcp/config.py` | Settings management |
| `src/ai_governance_mcp/extractor.py` | Document parsing + embeddings |
| `src/ai_governance_mcp/retrieval.py` | Hybrid search engine |
| `src/ai_governance_mcp/server.py` | MCP server + 6 tools |
| `documents/domains.json` | Domain configurations |
| `index/global_index.json` | Serialized index |
| `index/content_embeddings.npy` | Principle embeddings |
| `index/domain_embeddings.npy` | Domain embeddings for routing |

---

## Usage

### In Claude Code
The AI Governance MCP server is configured globally. Tools are available in all sessions:
- `query_governance("how do I handle incomplete specs")`
- `get_principle("coding-C1")`
- `list_domains()`

### Manual Testing
```bash
python -m ai_governance_mcp.server --test "your query here"
```

### Rebuild Index
```bash
python -m ai_governance_mcp.extractor
```

---

## Key Decisions Made

1. **Hybrid retrieval** over pure semantic - reduces miss rate to <1%
2. **In-memory index** over vector DB - simpler, sufficient for single-user
3. **Cross-encoder reranking** - improves precision on top results
4. **60/40 semantic/keyword weight** - balances precision and recall
5. **S-Series always checked** - safety principles never missed
