# AI Governance MCP — Architecture

**Version:** 1.7.0
**Date:** 2026-02-01
**Memory Type:** Structural (reference)

> System design, component responsibilities, data flow.
> For decisions/rationale → PROJECT-MEMORY.md

**Phase:** COMPLETE (364 tests, 90% coverage, 11 tools)

---

## System Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI GOVERNANCE MCP                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   server    │───→│  retrieval  │───→│   models    │    │   config    │  │
│  │             │    │             │    │             │    │             │  │
│  │ MCP tools   │    │ Router      │    │ Pydantic    │    │ Settings    │  │
│  │ exposed to  │    │ Hybrid      │    │ schemas     │    │ Paths       │  │
│  │ AI clients  │    │ Reranker    │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                                                │
│         │                  ▼                                                │
│         │           ┌─────────────┐                                         │
│         │           │   index     │  (loaded at startup)                    │
│         │           │             │                                         │
│         │           │ principles  │                                         │
│         │           │ embeddings  │                                         │
│         │           │ domains     │                                         │
│         │           └─────────────┘                                         │
│         │                  ▲                                                │
│         │                  │ (built offline)                                │
│         │           ┌─────────────┐                                         │
│         │           │  extractor  │───→ Parses markdown docs                │
│         │           └─────────────┘                                         │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                            │
│  │  feedback   │  (append-only log)                                         │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | What It Does | Why Separate |
|-----------|--------------|--------------|
| **server.py** | Exposes MCP tools, handles requests | Single entry point for AI clients |
| **retrieval.py** | Domain routing, hybrid search, reranking | Core intelligence, testable in isolation |
| **extractor.py** | Parses docs, builds index, generates embeddings | Runs offline, not at runtime |
| **models.py** | Pydantic schemas for principles, domains, results | Type safety, validation, serialization |
| **config.py** | Settings, paths, environment config | Centralized configuration |
| **index/** | Pre-built JSON + embeddings | Fast startup, no runtime parsing |
| **feedback.jsonl** | Append-only retrieval feedback log | Enables future improvement |

---

## Data Flow

**Build Time (offline, when docs change):**
```
documents/*.md  →  extractor.py  →  index/global_index.json
                                 →  index/content_embeddings.npy
                                 →  index/domain_embeddings.npy
```

**Runtime (every query):**
```
AI query  →  server.py  →  retrieval.py  →  index (in memory)  →  results
```

---

## File Structure

```
ai-governance-mcp/
├── src/
│   └── ai_governance_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP server, tool definitions
│       ├── retrieval.py       # Search logic
│       ├── extractor.py       # Doc parsing, index building
│       ├── models.py          # Pydantic schemas
│       ├── config.py          # Settings
│       ├── config_generator.py # Multi-platform MCP configs
│       └── validator.py       # Principle ID validation
│
├── Dockerfile                 # Multi-stage build for Docker distribution
├── docker-compose.yml         # Local testing configuration
├── .dockerignore              # Docker build exclusions
│
├── index/                     # Generated
│   ├── global_index.json      # Serialized GlobalIndex
│   ├── content_embeddings.npy # Principle/method embeddings (450, 384)
│   └── domain_embeddings.npy  # Domain embeddings for routing (5, 384)
│
├── documents/                 # Source markdown docs
│
├── logs/
│   └── feedback.jsonl         # Retrieval feedback
│
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── fixtures/                    # Test data files
│   ├── test_models.py               # Model tests (48)
│   ├── test_config.py               # Config tests (17)
│   ├── test_server.py               # Server unit tests (103)
│   ├── test_server_integration.py   # Server integration (11)
│   ├── test_extractor.py            # Extractor tests (60)
│   ├── test_extractor_integration.py # Extractor pipeline (11)
│   ├── test_retrieval.py            # Retrieval unit (46)
│   ├── test_retrieval_integration.py # Retrieval pipeline (23)
│   ├── test_retrieval_quality.py    # MRR/Recall benchmarks (13)
│   ├── test_config_generator.py     # Platform configs (17)
│   └── test_validator.py            # Principle validation (15)
│
├── pyproject.toml
└── README.md
```

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate extractor** | Docs change rarely; don't parse at runtime |
| **In-memory index** | Fast queries (<100ms target); rebuild is cheap |
| **Retrieval isolated** | Can test/tune search without MCP complexity |
| **Pydantic models** | Validation, IDE support, clean serialization |
| **Append-only feedback** | Simple, no DB needed, enables future learning |

---

## Docker Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCKER BUILD (Multi-Stage)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Stage 1: BUILDER                     Stage 2: RUNTIME                      │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │ python:3.11-slim    │              │ python:3.11-slim    │               │
│  │                     │              │                     │               │
│  │ - Install deps      │              │ - Install deps      │               │
│  │ - Build index       │──────────────│ - Copy index/       │               │
│  │ - Generate embeds   │  (copy)      │ - Non-root user     │               │
│  └─────────────────────┘              │ - Health check      │               │
│                                       └─────────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Component | Purpose |
|-----------|---------|
| **Multi-stage build** | Separate build (gcc, index generation) from runtime |
| **CPU-only PyTorch** | Avoids 2GB+ CUDA dependencies |
| **Non-root user** | Security hardening (appuser) |
| **Pre-built index** | No model loading during build; copied from builder |
| **Health check** | Container monitoring for orchestration |

**Image size:** ~1.6GB (dominated by ML dependencies)

---

## Security Architecture (v1)

| Aspect | Approach | Rationale |
|--------|----------|-----------|
| **Authentication** | None (v1) | Local use; future phase adds auth |
| **Data access** | Read-only from index | No writes to source docs |
| **Feedback logging** | Append-only, local file | No sensitive data stored |
| **Network exposure** | Local stdio only (MCP) | No HTTP server in v1 |
| **Dependencies** | Verified packages only | Per spec §11 |

**Future phase** (multi-user): Add authentication layer, user isolation, rate limiting.

---

## Integration Points

| Integration | Protocol | Notes |
|-------------|----------|-------|
| AI Clients (Claude, etc.) | MCP (JSON-RPC over stdio) | Standard MCP interface |
| Source Documents | File system read | Markdown files in documents/ |
| Index | File system read | JSON + NumPy at startup |
| Feedback Log | File system append | JSONL format |

---

## Test Architecture

| Category | Files | Purpose |
|----------|-------|---------|
| **Unit** | test_models, test_config, test_validator | Isolated component validation |
| **Server** | test_server, test_server_integration | All 11 MCP tools, dispatcher routing |
| **Extractor** | test_extractor, test_extractor_integration | Parsing, embeddings, index build |
| **Retrieval** | test_retrieval, test_retrieval_integration | Hybrid search, reranking, pipeline |
| **Config** | test_config_generator | Multi-platform MCP configurations |

### Test Markers (pyproject.toml)

| Marker | Purpose |
|--------|---------|
| `@pytest.mark.slow` | Tests requiring actual ML models (~30s each) |
| `@pytest.mark.integration` | End-to-end pipeline tests |
| `@pytest.mark.real_index` | Tests using production index data |

### Mocking Strategy

ML models (SentenceTransformer, CrossEncoder) are mocked via `conftest.py` fixtures:
- Patch at `sentence_transformers.*` level (lazy-loaded imports)
- Mock returns numpy arrays with correct shapes via `side_effect`
- Fixed random seed for reproducible tests

### Coverage by Module

| Module | Coverage | Notes |
|--------|----------|-------|
| models.py | 100% | Full validation coverage |
| config.py | 98% | Env edge case uncovered |
| server.py | 90% | async run_server uncovered |
| extractor.py | 89% | CLI main uncovered |
| retrieval.py | 84% | Rare filesystem errors uncovered |
| config_generator.py | 100% | Full coverage |
| validator.py | 100% | Full coverage |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| mcp | >=1.0.0 | MCP SDK (FastMCP) |
| pydantic | >=2.0.0 | Data models |
| pydantic-settings | >=2.0.0 | Configuration |
| sentence-transformers | >=2.2.0 | Embeddings + reranking |
| rank-bm25 | >=0.2.0 | BM25 keyword search |
| numpy | >=1.24.0 | Vector operations |
| pytest | >=7.0.0 | Testing (dev) |

---

## Test File Map

| File | Tests | Purpose |
|------|-------|---------|
| tests/conftest.py | - | Shared fixtures (mock_embedder, saved_index, etc.) |
| tests/test_models.py | 48 | Model validation, constraints, enums |
| tests/test_config.py | 17 | Settings, env vars, path handling |
| tests/test_server.py | 103 | All 11 tools, formatting, metrics, governance, agent installation |
| tests/test_server_integration.py | 11 | Dispatcher routing, end-to-end flows |
| tests/test_extractor.py | 60 | Parsing, embeddings, metadata, validation |
| tests/test_extractor_integration.py | 11 | Full pipeline, index persistence |
| tests/test_retrieval.py | 46 | Unit tests + edge cases |
| tests/test_retrieval_integration.py | 23 | Pipeline, utilities, performance |
| tests/test_retrieval_quality.py | 13 | MRR, Recall@K benchmarks |
| tests/test_config_generator.py | 17 | Platform configs, CLI commands |
| tests/test_validator.py | 15 | Principle ID validation, fuzzy matching |

---

## Source File Map

| File | Purpose | Lines |
|------|---------|-------|
| src/ai_governance_mcp/models.py | Pydantic data structures | ~350 |
| src/ai_governance_mcp/config.py | Settings management | ~224 |
| src/ai_governance_mcp/extractor.py | Document parsing + embeddings | ~450 |
| src/ai_governance_mcp/retrieval.py | Hybrid search engine | ~500 |
| src/ai_governance_mcp/server.py | MCP server + 11 tools | ~1900 |
| src/ai_governance_mcp/config_generator.py | Multi-platform MCP configs | ~150 |
| src/ai_governance_mcp/validator.py | Principle ID validation | ~350 |
