# AI Governance MCP - Session State

**Last Updated:** 2025-12-27
**Current Phase:** COMPLETE
**Procedural Mode:** STANDARD

---

## Current Position

**Status:** Project complete - security hardening applied
**Next Action:** Phase 2 planning when ready for public hosting
**Context:** v4 hybrid retrieval fully implemented, tested, deployed. Security review completed with fixes applied.

---

## Recent Changes

### Security Hardening (2025-12-27)

**Review:** Comprehensive security review against governance principles (meta-S1, meta-G7, coding-Q2, coding-Q4).

**Findings & Fixes:**
| Issue | Severity | Fix Applied |
|-------|----------|-------------|
| Unpinned dependencies | MEDIUM | All dependencies now pinned to exact versions |
| MCP CVE-2025-66416 | MEDIUM | Updated mcp 1.15.0 → 1.25.0 |
| No security scanning | MEDIUM | Added pip-audit, bandit, safety to dev deps |

**Scan Results:**
- **Bandit (source code):** ✅ Clean - 0 issues in 1,495 lines
- **pip-audit (dependencies):** ✅ Project deps clean after MCP update

**Phase 2 Requirements Documented:**
- Authentication (JWT/API keys)
- HTTPS/TLS transport
- Rate limiting
- User isolation
- Audit logging

---

### Bug Fix: Forced Domain Parameter (2025-12-27)

**Issue:** When `domain` parameter was explicitly set in `query_governance`, the specified domain's principles were not included in search results.

**Root Cause:** In `retrieval.py:390-401`, when a domain was forced, `search_domains` was set to only `["constitution"]` instead of including the forced domain.

**Fix:** Updated domain routing logic to include the forced domain in `search_domains`:
```python
if domain:
    search_domains = [domain] if domain in self.index.domains else []
    if include_constitution:
        search_domains.append("constitution")
```

**Tests Added:** 3 new real_index tests for forced domain behavior
- `test_real_index_forced_domain_returns_domain_principles`
- `test_real_index_forced_domain_includes_constitution`
- `test_real_index_forced_domain_excludes_constitution`

---

## Phase Transition

| Phase | Status | Gate Artifact |
|-------|--------|---------------|
| SPECIFY | Complete | GATE-SPECIFY.md |
| PLAN | Complete | GATE-PLAN.md |
| TASKS | Complete | GATE-TASKS.md |
| IMPLEMENT | **Complete** | 196 tests, 93% coverage |
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
| T19-T22 | Tests (196 passing, 93% coverage) | Complete |
| T23 | Portfolio README | Complete |

---

## Deployment Status

| Component | Status | Location |
|-----------|--------|----------|
| GitHub Repository | Pushed | github.com/jason21wc/ai-governance-mcp |
| Global MCP Config | Configured | ~/.claude.json (root mcpServers) |
| Index Built | Ready | index/global_index.json + embeddings |
| Dependencies | Installed | pip install -e . |

### MCP Configuration

The server is configured globally (user scope) in `~/.claude.json`:
```json
"ai-governance": {
  "type": "stdio",
  "command": "python",
  "args": ["-m", "ai_governance_mcp.server"],
  "env": {
    "AI_GOVERNANCE_DOCUMENTS_PATH": "/Users/jasoncollier/Developer/ai-governance-mcp/documents",
    "AI_GOVERNANCE_INDEX_PATH": "/Users/jasoncollier/Developer/ai-governance-mcp/index"
  }
}
```

**Important:** MCP servers are project-scoped. Use `claude mcp add -s user` for global access across all projects. Restart Claude Code after config changes.

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

### Test Coverage (Q3 Compliance)
| Module | Tests | Coverage |
|--------|-------|----------|
| models.py | 24 | 100% |
| config.py | 17 | 98% |
| server.py | 59 | 97% |
| extractor.py | 38 | 93% |
| retrieval.py | 55 | 86% |
| **Total** | **196** | **93%** |

**Test Categories:**
- Unit tests with mocked dependencies
- Integration tests (`@pytest.mark.integration`)
- Real index tests (`@pytest.mark.real_index`)
- Slow embedding tests (`@pytest.mark.slow`)

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
| `tests/conftest.py` | Shared test fixtures |
| `tests/test_server.py` | Server unit tests (44) |
| `tests/test_server_integration.py` | Server integration tests (12) |
| `tests/test_extractor.py` | Extractor unit tests (35) |
| `tests/test_extractor_integration.py` | Extractor integration tests (11) |
| `tests/test_retrieval.py` | Retrieval unit tests (44) |
| `tests/test_retrieval_integration.py` | Retrieval integration tests (18) |
| `tests/test_models.py` | Model validation tests (24) |
| `tests/test_config.py` | Config tests (17) |

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

### Run Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest --cov=ai_governance_mcp --cov-report=html tests/

# Skip slow tests
pytest -m "not slow" tests/

# Real index tests only
pytest -m real_index tests/
```

---

## Key Decisions Made

1. **Hybrid retrieval** over pure semantic - reduces miss rate to <1%
2. **In-memory index** over vector DB - simpler, sufficient for single-user
3. **Cross-encoder reranking** - improves precision on top results
4. **60/40 semantic/keyword weight** - balances precision and recall
5. **S-Series always checked** - safety principles never missed
