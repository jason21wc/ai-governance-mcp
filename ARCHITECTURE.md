# AI Governance MCP — Architecture

**Version:** 1.1
**Date:** 2025-12-27
**Phase:** COMPLETE (196 tests, 93% coverage)

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
documents/*.md  →  extractor.py  →  index/principles.json
                                 →  index/embeddings.npy
                                 →  index/domains.json
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
│       └── config.py          # Settings
│
├── index/                     # Generated
│   ├── global_index.json      # Serialized GlobalIndex
│   ├── content_embeddings.npy # Principle/method embeddings (65, 384)
│   └── domain_embeddings.npy  # Domain embeddings for routing (3, 384)
│
├── documents/                 # Source markdown docs
│
├── logs/
│   └── feedback.jsonl         # Retrieval feedback
│
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── fixtures/                    # Test data files
│   ├── test_models.py               # Model tests (24)
│   ├── test_config.py               # Config tests (17)
│   ├── test_server.py               # Server unit tests (44)
│   ├── test_server_integration.py   # Server integration (12)
│   ├── test_extractor.py            # Extractor tests (35)
│   ├── test_extractor_integration.py # Extractor pipeline (11)
│   ├── test_retrieval.py            # Retrieval unit (44)
│   └── test_retrieval_integration.py # Retrieval pipeline (18)
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
| **Unit** | test_models, test_config | Isolated component validation |
| **Server** | test_server, test_server_integration | All 6 MCP tools, dispatcher routing |
| **Extractor** | test_extractor, test_extractor_integration | Parsing, embeddings, index build |
| **Retrieval** | test_retrieval, test_retrieval_integration | Hybrid search, reranking, pipeline |

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
| server.py | 97% | async run_server uncovered |
| extractor.py | 93% | CLI main uncovered |
| retrieval.py | 86% | Rare filesystem errors uncovered |
