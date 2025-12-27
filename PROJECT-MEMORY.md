# AI Governance MCP - Project Memory

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Semantic retrieval MCP for domain-specific principles/methods — "second brain" for AI
- **Owner:** Jason
- **Status:** IMPLEMENT phase - T1 in progress
- **Procedural Mode:** STANDARD
- **Quality Target:** Showcase/production-ready, public-facing tool
- **Portfolio Goal:** Showcase for recruiters, consulting customers, SME presentations
- **Repository:** github.com/jason21wc/ai-governance-mcp (private, future public)

## Architecture Summary

```
Build Time:  documents/*.md → extractor.py → index/ + embeddings.npy
Runtime:     Query → Domain Router → Hybrid Search → Reranker → Results
```

**Core Components:**
- `server.py` - FastMCP server with 6 tools
- `retrieval.py` - Domain routing, hybrid search, reranking
- `extractor.py` - Document parsing, embedding generation, index building
- `models.py` - Pydantic data structures
- `config.py` - Configuration management

**Retrieval Pipeline:**
1. Domain Routing — identify relevant domain(s)
2. Hybrid Search — BM25 (keyword) + dense vectors (semantic)
3. Reranking — cross-encoder scores top candidates
4. Hierarchy Filter — constitution always, S-Series priority

## Key Decisions Log

### Decision: Option C Selected - Tier 1 + Best of Tier 2
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **Choice:** Implement Tier 1 (semantic embeddings, hybrid search, smart routing) + best of Tier 2 (reranking, confidence scoring), architect for Tier 3 (knowledge graph, etc.)
- **Rationale:** ~95% retrieval quality with manageable complexity; clean upgrade path for Tier 3 later

### Decision: Architecture Direction Confirmed via Industry Research
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **Research Conducted:** Legal AI, Medical CDSS, Multi-Domain KB patterns
- **Industry Consensus:**
  - Hybrid retrieval (BM25 + semantic) is standard for high-stakes retrieval
  - Router/Controller pattern scales to hundreds of knowledge bases
  - Rich domain metadata enables accurate routing
- **Sources:** Harvard JOLT, Stanford HAI, PMC, InfoQ Domain-Driven RAG

### Decision: Scale Requirements Clarified
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **PO Requirements:**
  - Many domains planned: ai-coding, multi-agent, prompt engineering, RAG optimization, sci-fi/fantasy writing, hotel analysis, more
  - Must scale to 10+ domains
  - Open to dependencies for quality
- **Implication:** Design must handle many domains with smart routing

### Decision: In-Memory Storage for v1
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **Rationale:** Hundreds to low thousands of principles fits easily in memory; designed for easy migration to vector DB when multi-user phase comes

### Decision: Portfolio-Ready Documentation
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **Approach:** Spec is internal planning doc; README.md is external showcase (derived from spec)
- **Audiences (priority order):** Recruiters, customers, SME presenters, general

## Patterns and Conventions

### Communication Level (PO Approved)
- Default: "Interview-ready" — high-level what/why
- On request: Mid-level detail
- Deep dive: Only when explicitly requested

### Process Map Pattern (PO Approved)
Show updated process map:
- After major accomplishments
- On request for updates
- At phase transitions

### Naming
- Principle IDs: `meta-C1`, `coding-C1`, `multi-A1`
- Domain names: lowercase, hyphenated (`ai-coding`, `multi-agent`)

### Code Style
- Python 3.10+
- Pydantic for data models
- FastMCP for server
- Type hints throughout
- Logging to stderr (stdout reserved for JSON-RPC)

## Current State

### Phases Complete
- [x] SPECIFY — Specification v4 approved
- [x] PLAN — Architecture defined, GATE-PLAN.md approved
- [x] TASKS — 23 tasks defined, GATE-TASKS.md approved

### Implementation Progress
| Task | Description | Status |
|------|-------------|--------|
| T1 | Pydantic models | **In Progress** |
| T2 | Config/settings | Pending |
| T3-T5 | Extractor | Pending |
| T6-T11 | Retrieval | Pending |
| T12-T18 | Server + tools | Pending |
| T19-T22 | Tests | Pending |
| T23 | Portfolio README | Pending |

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

## File Map

| File | Purpose | Status |
|------|---------|--------|
| ai-governance-mcp-specification-v4.md | Complete specification | Approved |
| ARCHITECTURE.md | System architecture | Approved |
| GATE-SPECIFY.md | Specify phase gate | Complete |
| GATE-PLAN.md | Plan phase gate | Complete |
| GATE-TASKS.md | Tasks phase gate | Complete |
| SESSION-STATE.md | Current position | Active |
| PROJECT-MEMORY.md | This file | Active |
| LEARNING-LOG.md | Lessons learned | Active |

## Known Gotchas

### Gotcha 1: Existing Code Needs Rework
Previous implementation used keyword-only search. Models, retrieval, server all need updates for hybrid architecture.

### Gotcha 2: stdout Reserved
MCP protocol uses stdout for JSON-RPC. All logging must go to stderr.

### Gotcha 3: S-Series Must Always Be Checked
Even with domain filtering, S-Series (Safety) triggers must be checked.

### Gotcha 4: Spec ≠ Validated Requirements
Always run discovery with PO before treating spec as requirements.
