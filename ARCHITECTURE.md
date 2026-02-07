# AI Governance MCP — Architecture

**Version:** 1.9.0
**Date:** 2026-02-08
**Memory Type:** Structural (reference)

> System design, component responsibilities, data flow.
> For decisions/rationale → PROJECT-MEMORY.md
> Avoid volatile metrics here (test counts, coverage %, dependency versions) — use canonical sources (`pytest`, `pytest --cov`, `pyproject.toml`).

**Phase:** COMPLETE — 15 tools across 2 MCP servers

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
│   ├── content_embeddings.npy # Principle/method embeddings (384-dim)
│   └── domain_embeddings.npy  # Domain embeddings for routing (384-dim)
│
├── documents/                 # Source markdown docs
│
├── logs/
│   └── feedback.jsonl         # Retrieval feedback
│
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── fixtures/                    # Test data files
│   ├── test_models.py               # Model validation
│   ├── test_config.py               # Config + env vars
│   ├── test_server.py               # All MCP tools, formatting, governance
│   ├── test_server_integration.py   # Dispatcher routing, end-to-end flows
│   ├── test_extractor.py            # Parsing, embeddings, metadata
│   ├── test_extractor_integration.py # Full pipeline, index persistence
│   ├── test_retrieval.py            # Hybrid search, reranking, edge cases
│   ├── test_retrieval_integration.py # Pipeline, utilities, performance
│   ├── test_retrieval_quality.py    # MRR/Recall benchmarks
│   ├── test_config_generator.py     # Platform config generation
│   ├── test_validator.py            # Principle ID validation, fuzzy matching
│   └── test_context_engine.py       # Full context engine coverage
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
| **Dependency pinning** | Core deps exact-pinned for reproducibility; optional deps range-pinned for compatibility (see pyproject.toml) |

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

### Known Test Boundaries

Deliberately uncovered areas (run `pytest --cov` for current percentages):
- server.py: `async run_server()` — entry point, tested via integration
- extractor.py: CLI `main()` — invoked manually
- retrieval.py: Rare filesystem error paths

---

## Dependencies

| Package | Purpose |
|---------|---------|
| mcp | MCP SDK (FastMCP) |
| pydantic / pydantic-settings | Data models + configuration |
| sentence-transformers | Embeddings + reranking |
| rank-bm25 | BM25 keyword search |
| numpy | Vector operations |
| requests | HTTP (required by sentence-transformers) |
| pytest / ruff | Testing + linting (dev) |

See `pyproject.toml` for pinned versions.

---

## Context Engine MCP Server

A second MCP server providing semantic search across project content. Complements the governance MCP server (principles/methods) with project-specific content awareness.

### System Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTEXT ENGINE MCP                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   server    │───→│  project    │───→│   indexer   │                     │
│  │             │    │  manager    │    │             │                     │
│  │ 4 MCP tools │    │             │    │ Embedding   │                     │
│  │ Validation  │    │ Multi-proj  │    │ BM25 build  │                     │
│  │ Rate limit  │    │ Hybrid QRY  │    │ Connectors  │                     │
│  │ Sanitize    │    │ RLock sync  │    │             │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                            │                  │                             │
│                            ▼                  ▼                             │
│                     ┌─────────────┐    ┌─────────────┐                     │
│                     │   watcher   │    │ connectors  │                     │
│                     │             │    │             │                     │
│                     │ watchdog    │    │ code (TS)   │                     │
│                     │ debounce    │    │ document    │                     │
│                     │ incremental │    │ PDF         │                     │
│                     └─────────────┘    │ spreadsheet │                     │
│                                        │ image meta  │                     │
│                            │           └─────────────┘                     │
│                            ▼                                               │
│                     ┌─────────────┐                                         │
│                     │  storage    │  (~/.context-engine/indexes/{id}/)      │
│                     │             │                                         │
│                     │ filesystem  │  embeddings.npy, bm25.json,            │
│                     │ JSON-based  │  metadata.json, manifest.json          │
│                     └─────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | What It Does | Why Separate |
|-----------|--------------|--------------|
| **server.py** | 4 MCP tools, input validation, rate limiting, error sanitization | Entry point, security boundary |
| **project_manager.py** | Multi-project lifecycle, hybrid search (semantic + BM25), score fusion | Core query logic, thread-safe |
| **indexer.py** | File discovery, connector orchestration, embedding generation, BM25 build | Indexing pipeline, heavy compute |
| **watcher.py** | File system monitoring, debounced change callbacks | Real-time updates, decoupled |
| **connectors/** | Content-type-specific parsing (code, doc, PDF, spreadsheet, image) | Pluggable, independently testable |
| **storage/** | Index persistence (filesystem-backed, JSON + NumPy) | Swappable backends |
| **models.py** | Pydantic schemas (ContentChunk, ProjectIndex, QueryResult, etc.) | Type safety, validation |

### Data Flow

**Index Time (per project):**
```
project files  →  indexer._discover_files()  →  connectors.parse()  →  ContentChunks
                                                                            │
                   storage.save_*()  ←  BM25 index + embeddings  ←─────────┘
```

**Query Time (per request):**
```
AI query  →  server.py (validate)  →  project_manager.query_project()
                                            │
                 ┌──────────────────────────┤
                 ▼                          ▼
          semantic_search()          bm25_search()
          (cosine similarity)        (keyword matching)
                 │                          │
                 └──────────┬───────────────┘
                            ▼
                     _fuse_scores()  →  ranked QueryResult[]
```

**Real-time Update (file watcher):**
```
file change  →  watchdog event  →  debounce (500ms)  →  incremental_update()
                                                              │
                                                     reload search indexes
```

### Security Features

| Feature | Implementation | Location |
|---------|---------------|----------|
| **Input validation** | Type checks, length limits, bounds clamping | server.py |
| **Rate limiting** | Token bucket (5 req/min) for index_project | server.py |
| **Error sanitization** | Strip paths, line numbers, memory addresses, module paths | server.py |
| **Path traversal prevention** | Hex-only project IDs, resolve + is_relative_to containment | storage/filesystem.py |
| **Pickle deserialization** | allow_pickle=False on all np.load calls | storage/filesystem.py |
| **JSON serialization** | BM25 index stored as JSON, not pickle | storage/filesystem.py |
| **Symlink filtering** | Skip symlinks during file discovery, list_projects, delete_project | indexer.py, storage/filesystem.py |
| **File size limits** | 10MB max per file during indexing | indexer.py |
| **File count limits** | 10,000 max files per project | indexer.py |
| **Thread safety** | RLock protecting shared index state; Lock guarding rate limiter | project_manager.py, server.py |
| **Decompression bomb guard** | PIL MAX_IMAGE_PIXELS limit set at connector init | connectors/image.py |
| **Relative paths in output** | source_path computed relative to project root, not absolute | connectors/*.py |
| **Log sanitization** | Truncate content before logging | server.py |
| **Env var robustness** | try/except with fallback defaults for all env config | server.py |
| **.env* filtering** | .env and all variants (.env.local, etc.) excluded by default | indexer.py |

### Context Engine File Structure

```
src/ai_governance_mcp/context_engine/
├── __init__.py
├── server.py            # MCP server (4 tools, validation, rate limiting)
├── project_manager.py   # Multi-project management, hybrid query
├── indexer.py           # Core indexing pipeline
├── watcher.py           # File system watcher (watchdog)
├── models.py            # Pydantic data models
├── connectors/
│   ├── __init__.py
│   ├── base.py          # BaseConnector interface
│   ├── code.py          # Code parsing (tree-sitter)
│   ├── document.py      # Markdown/text parsing
│   ├── pdf.py           # PDF extraction
│   ├── spreadsheet.py   # CSV/Excel parsing
│   └── image.py         # Image metadata extraction
└── storage/
    ├── __init__.py
    ├── base.py          # BaseStorage interface
    └── filesystem.py    # Local filesystem storage
```

### Context Engine Test Coverage

All context engine tests are in `test_context_engine.py`. Run `pytest tests/test_context_engine.py -v` for current counts.

| Category | Coverage Areas |
|----------|---------------|
| **Models** | ContentChunk, FileMetadata, ProjectIndex, QueryResult validation and constraints |
| **Storage** | Filesystem round-trips, security (path traversal, symlinks), directory permissions, JSON size limits |
| **Connectors** | Code/document/PDF/spreadsheet/image parsing, relative paths, resource cleanup |
| **Indexer** | File discovery, ignore patterns (.contextignore, .env*), symlink filtering, file count limits, BM25 tokenization |
| **Project Manager** | Score fusion, BM25 query, RLock thread safety, lifecycle (create/load/reindex/list/status/delete) |
| **Server** | Error sanitization, rate limiting, input validation, env var parsing, handler routing |
| **Watcher** | Start/stop, debounce, ignore spec passthrough, circuit breaker, status reporting |
| **Integration** | Full index-query pipeline, .contextignore respect |

### Context Engine Dependencies

| Package | Purpose |
|---------|---------|
| sentence-transformers / rank-bm25 / numpy | Shared with governance server (embeddings, BM25, vectors) |
| watchdog | File system monitoring for real-time indexing |
| tree-sitter | Language-aware code parsing |
| pymupdf / pdfplumber | PDF content extraction (primary / fallback) |
| openpyxl | Excel file parsing |
| Pillow | Image metadata extraction |
| pathspec | Gitignore-style pattern matching for .contextignore |

See `pyproject.toml [project.optional-dependencies]` for versions.
