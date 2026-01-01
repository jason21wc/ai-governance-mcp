# AI Governance MCP - Project Memory

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Semantic retrieval MCP for domain-specific principles/methods — "second brain" for AI
- **Owner:** Jason
- **Status:** COMPLETE - All phases done, 205 tests, 90% coverage
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

### Decision: Comprehensive Testing Strategy (Q3 Compliance)
- **Date:** 2025-12-27
- **Status:** CONFIRMED
- **Choice:** Maximum coverage (~90+ tests) with real index tests and slow embedding tests included
- **Test Categories:**
  - Unit tests with mocked ML models
  - Integration tests for full pipeline flows
  - Edge case tests for boundary conditions
  - Real production index tests (`@pytest.mark.real_index`)
  - Slow embedding tests (`@pytest.mark.slow`)
- **Coverage Achieved:** 90% (exceeds 80% Q3 target)

### Decision: Mock Strategy for ML Models
- **Date:** 2025-12-27
- **Status:** CONFIRMED
- **Pattern:** Lazy-loaded models patched at `sentence_transformers.SentenceTransformer` level
- **Rationale:** Models are imported inside properties, not at module level
- **Fixture:** `mock_embedder` returns proper numpy arrays via `side_effect` function

### Decision: Per-Response Governance Reminder
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** SERVER_INSTRUCTIONS injected once at MCP init; AI clients may drift over long conversations
- **Research:** MCP spec has no built-in per-response mechanism; Claude Code uses repeated `<system-reminder>` tags (validates pattern)
- **Choice:** Append compact reminder (~30 tokens) to every tool response
- **Reminder Content:**
  ```
  📋 **Governance:** Query on decisions/concerns. Apply Constitution→Domain→Methods.
  Cite influencing principles. S-Series=veto. Pause on spec gaps. Escalate product decisions.
  ```
- **Implementation:** `GOVERNANCE_REMINDER` constant + `_append_governance_reminder()` helper in server.py
- **Rationale:** User requirements (repeatable, reliable, consistent, dependable) point to uniformity; token cost trivial in 100K+ context
- **Requirements Met:**
  | Requirement | How Addressed |
  |-------------|---------------|
  | Repeatable | Every tool response includes reminder |
  | Reliable | Single injection point in `call_tool()` |
  | Consistent | Same reminder across all 6 tools |
  | Dependable | Tested with dedicated unit test |

### Decision: MCP Server Instructions
- **Date:** 2025-12-29
- **Status:** CONFIRMED
- **Problem:** Claude App could see tools but received no behavioral guidance
- **Solution:** Added `instructions` parameter to MCP Server initialization
- **Content:** Governance overview, trigger conditions, hierarchy, key behaviors, quick start
- **Impact:** Documents updated (ai-governance-methods v3.1.0 → v3.2.0, ai-instructions v2.3 → v2.4)

### Decision: Graceful Shutdown with os._exit()
- **Date:** 2025-12-29
- **Status:** CONFIRMED
- **Problem:** Server didn't exit cleanly; sentence-transformers threads kept process alive
- **Research:** Postgres MCP server uses same pattern; stdio transport can't be gracefully interrupted
- **Solution:** SIGTERM/SIGINT handlers + finally block call `os._exit(0)` immediately
- **Rationale:** Synchronous I/O can't be cancelled; immediate exit is correct for stdio transport

### Decision: Pre-Flight Validation for Domain Configuration
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** Extractor silently produced "0 methods" when domains.json referenced missing files (stale version references after updates)
- **Solution:** Added `validate_domain_files()` method called at start of `extract_all()`:
  1. Checks all configured principles/methods files exist
  2. Reports ALL missing files in one error (not just first)
  3. Provides actionable guidance ("Check documents/domains.json and ensure file versions match")
- **Implementation:**
  - New `ExtractorConfigError` exception class
  - `validate_domain_files()` method in DocumentExtractor
  - 7 new tests in test_extractor.py
- **Rationale:** Fail-fast with clear errors > fail-silent with hidden problems
- **Pattern Applied:** Any config-driven system should validate external references at startup

---

## AI Coding Methods v2.0.0 Decisions

*The following decisions apply to the AI Coding Methods framework itself (ai-coding-methods.md), not just the MCP server.*

### Decision: Memory Architecture Aligned to Cognitive Types
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Research:** CoALA framework (Princeton), IBM, Mem0, industry patterns
- **Choice:** Explicitly map memory files to cognitive memory types:
  | Cognitive Type | File | Purpose |
  |----------------|------|---------|
  | Working Memory | SESSION-STATE.md | What's active now (transient) |
  | Semantic Memory | PROJECT-MEMORY.md | Facts, decisions, knowledge (accumulates) |
  | Episodic Memory | LEARNING-LOG.md | Events, experiences (prunable) |
  | Procedural Memory | Methods documents | How to do things (evolves) |
- **Rationale:** Cognitive framing clarifies purpose of each file; aligns with AI agent memory best practices
- **Sources:** [Mem0](https://mem0.ai), [IBM AI Agent Memory](https://www.ibm.com/think/topics/ai-agent-memory), [CoALA Framework](https://arxiv.org/abs/2309.02427)

### Decision: Eliminate Separate Gate Artifact Files
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Breaking Change:** Yes — projects using GATE-SPECIFY.md, GATE-PLAN.md, etc. must migrate
- **Previous:** Create separate GATE-*.md files for each phase transition, then archive
- **New:** Record gate status inline in PROJECT-MEMORY.md under "Phase Gates" section
- **Rationale:**
  1. Gates are checkpoints (facts about project state), not decisions (ADRs)
  2. Separate files create coordination overhead and sync issues
  3. Gate criteria live in procedural memory (methods doc) — no need to duplicate
  4. Industry pattern: quality gates integrate inline, not as separate documents
- **Migration:** Move gate status to PROJECT-MEMORY table; archive old GATE-*.md files
- **Sources:** [Sonar Quality Gates](https://www.sonarsource.com/learn/quality-gate/), ADR vs checkpoint distinction

### Decision: Task Tracking Tiered Approach
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** Methods doc didn't specify where task list lives during Implement phase
- **Choice:** Tiered approach based on project context:
  | Context | Approach |
  |---------|----------|
  | Team/Open Source | GitHub Issues + Projects |
  | Solo/Private | Active Tasks section in SESSION-STATE.md |
  | Hybrid | GitHub Issues for backlog, SESSION-STATE for current sprint |
- **Rationale:**
  1. Tasks are working memory — belong with session state
  2. GitHub Issues provide automation (auto-close, cross-references)
  3. Separate TASKS.md file creates unnecessary sync overhead
- **Sources:** [GitHub Planning and Tracking](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

### Decision: Project Instructions File (Loader Document)
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** Methods doc didn't formally define how AI discovers memory files
- **Choice:** Define tool-agnostic "Project Instructions File" concept with implementations:
  | Tool | File |
  |------|------|
  | Claude Code | CLAUDE.md |
  | Gemini CLI | GEMINI.md |
  | Cursor | .cursor/rules/ |
  | Cross-tool | AGENTS.md (emerging) |
- **Key Principle:** Progressive disclosure — loader points to memory, doesn't contain all info
- **Rationale:**
  1. CLAUDE.md is the "constitution" for AI working on a codebase
  2. Less is more — minimal loader, full context in memory files
  3. Enables tool-agnostic framework definition
- **Sources:** [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices), [HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

### Decision: Principles-Based Memory Pruning
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** No guidance on when/how to prune memory files
- **Choice:** Principles-based guidance, not size limits
- **Core Principle:** "Memory serves reasoning, not archival. Retain what informs future decisions; prune what only describes the past."
- **Pruning Triggers:**
  | Memory Type | Prune When |
  |-------------|------------|
  | Working (SESSION-STATE) | Every session start (overwrite) |
  | Semantic (PROJECT-MEMORY) | Decision is superseded or obsolete |
  | Episodic (LEARNING-LOG) | Lesson is internalized into procedures |
- **Anti-Principle:** Never prune for size alone — large memory indicates detail or scope issues
- **Sources:** [Mem0 priority scoring](https://mem0.ai), industry eviction policies

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
- Principle IDs: `{domain}-{category}-{title-slug}` (e.g., `meta-core-context-engineering`, `coding-context-specification-completeness`)
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
- [x] IMPLEMENT — All tasks complete, deployed to GitHub
- [x] TEST — 205 tests passing, 90% coverage

### Implementation Progress
| Task | Description | Status |
|------|-------------|--------|
| T1 | Pydantic models (SeriesCode, ConfidenceLevel, ScoredPrinciple) | Complete |
| T2 | Config/settings (pydantic-settings, env vars) | Complete |
| T3-T5 | Extractor (parser, embeddings, GlobalIndex) | Complete |
| T6-T11 | Retrieval (domain routing, BM25, semantic, fusion, rerank, hierarchy) | Complete |
| T12-T18 | Server + 6 MCP tools | Complete |
| T19-T22 | Tests (205 passing, 90% coverage) | Complete |
| T23 | Portfolio README | Complete |

### Test Coverage
| Module | Tests | Coverage |
|--------|-------|----------|
| models.py | 24 | 100% |
| config.py | 17 | 98% |
| server.py | 59 | 91% |
| extractor.py | 45 | 89% |
| retrieval.py | 55 | 84% |
| **Total** | **205** | **90%** |

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

### Documentation
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
| README.md | Portfolio showcase | Complete |

### Source Code
| File | Purpose | Lines |
|------|---------|-------|
| src/ai_governance_mcp/models.py | Pydantic data structures | ~110 |
| src/ai_governance_mcp/config.py | Settings management | ~62 |
| src/ai_governance_mcp/extractor.py | Document parsing + embeddings | ~194 |
| src/ai_governance_mcp/retrieval.py | Hybrid search engine | ~281 |
| src/ai_governance_mcp/server.py | MCP server + 6 tools | ~182 |

### Test Files
| File | Tests | Purpose |
|------|-------|---------|
| tests/conftest.py | - | Shared fixtures (mock_embedder, saved_index, etc.) |
| tests/test_models.py | 24 | Model validation, constraints, enums |
| tests/test_config.py | 17 | Settings, env vars, path handling |
| tests/test_server.py | 46 | All 6 tools, formatting, metrics, governance reminder |
| tests/test_server_integration.py | 12 | Dispatcher routing, end-to-end flows |
| tests/test_extractor.py | 42 | Parsing, embeddings, metadata, validation |
| tests/test_extractor_integration.py | 11 | Full pipeline, index persistence |
| tests/test_retrieval.py | 44 | Unit tests + edge cases |
| tests/test_retrieval_integration.py | 18 | Pipeline, utilities, performance |

## Known Gotchas

### Gotcha 1: Existing Code Needs Rework
Previous implementation used keyword-only search. Models, retrieval, server all need updates for hybrid architecture.

### Gotcha 2: stdout Reserved
MCP protocol uses stdout for JSON-RPC. All logging must go to stderr.

### Gotcha 3: S-Series Must Always Be Checked
Even with domain filtering, S-Series (Safety) triggers must be checked.

### Gotcha 4: Spec ≠ Validated Requirements
Always run discovery with PO before treating spec as requirements.

### Gotcha 5: ML Model Mocking Pattern
SentenceTransformer and CrossEncoder are lazy-loaded inside properties. Patch at `sentence_transformers.SentenceTransformer` not `ai_governance_mcp.retrieval.SentenceTransformer`.

### Gotcha 6: Mock Embedder Must Return Proper Arrays
Use `side_effect` function that returns `np.random.rand(len(texts), 384)` not a static array, otherwise batch operations fail.

### Gotcha 7: Rating=0 is Falsy
In log_feedback tests, rating=0 triggers "required" validation before range check. Use rating=-1 to test invalid low values.

### Gotcha 8: MCP Servers Are Project-Scoped
MCP servers configured under a project path in `~/.claude.json` only load when Claude Code runs from that directory. To make an MCP available everywhere:
- Use `claude mcp add <name> -s user -- <command>` for global (user) scope
- Or add to root-level `mcpServers` in `~/.claude.json` (not inside a project object)
- **Always restart Claude Code after config changes** - MCP servers load at startup.

### Gotcha 9: First Query Latency
First retrieval takes ~9s to load ML models (SentenceTransformer + CrossEncoder). Subsequent queries are ~50ms. Consider model preloading for production use.

### Gotcha 10: get_principle Must Retrieve Both Principles AND Methods
The `get_principle` tool must search both `principles` and `methods` collections. Method IDs returned by `query_governance` (e.g., `meta-method-version-format`) need to be retrievable.

**Architecture Pattern:**
```python
# In retrieval.py - need BOTH lookup functions:
def get_principle_by_id(self, id: str) -> Principle | None
def get_method_by_id(self, id: str) -> Method | None

# In server.py - handler tries both:
principle = engine.get_principle_by_id(id)
if principle:
    return principle_response
method = engine.get_method_by_id(id)
if method:
    return method_response
```

**ID Format:**
- Principles: `{prefix}-{category}-{slug}` (e.g., `meta-core-context-engineering`)
- Methods: `{prefix}-method-{slug}` (e.g., `coding-method-phase-1-specify`)

**Why This Matters:** If only `get_principle_by_id` is implemented, methods appear in query results but can't be retrieved individually - a confusing UX gap.

### Gotcha 11: domains.json File References Must Match Actual Filenames
When updating governance document versions (e.g., `ai-coding-methods-v1.1.1.md` → `ai-coding-methods-v2.0.0.md`), you MUST update `documents/domains.json` to reference the new filename.

**Symptom:** Extractor shows "0 methods" for a domain that should have methods.

**Fix:** Update `domains.json` to reference correct filename, then rebuild index.

**Prevention:** Extractor now validates all file references at startup and fails fast with actionable error message listing ALL missing files.
