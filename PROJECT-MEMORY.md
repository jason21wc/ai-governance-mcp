# AI Governance MCP - Project Memory

**Memory Type:** Semantic (accumulates)
**Lifecycle:** Prune when decisions superseded per §7.0.4

> Preserves significant decisions and rationale.
> Mark superseded decisions with date and replacement link.
> For structural details → ARCHITECTURE.md

---

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Semantic retrieval MCP for domain-specific principles/methods
- **Owner:** Jason
- **Status:** COMPLETE - All phases done, 365 tests, 90% coverage, 11 tools
- **Repository:** github.com/jason21wc/ai-governance-mcp

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ✓ Passed | 2025-12-26 | Option C (Tier 1 + best of Tier 2) |
| Plan → Tasks | ✓ Passed | 2025-12-26 | Architecture approved |
| Tasks → Implement | ✓ Passed | 2025-12-27 | 90+ test target set |
| Implement → Complete | ✓ Passed | 2025-12-29 | 355 tests, 90% coverage |

---

## Key Decisions (Condensed)

### Architecture

| Decision | Date | Summary |
|----------|------|---------|
| Option C Selected | 2025-12-26 | Hybrid retrieval (BM25 + semantic) + reranking. ~95% quality, clean upgrade path. |
| In-Memory Storage | 2025-12-26 | Fits in memory for v1; designed for easy vector DB migration later. |
| Embedding Model Upgrade | 2026-01-17 | `all-MiniLM-L6-v2` → `BAAI/bge-small-en-v1.5` (512 tokens). MRR +112%. |
| Docker AMD64-Only | 2026-01-18 | ARM64 removed (QEMU too slow). Apple Silicon uses Rosetta 2. |

### Governance Enforcement

| Decision | Date | Summary |
|----------|------|---------|
| Per-Response Reminder | 2025-12-31 | ~30 token reminder appended to every tool response. |
| Hybrid AI Judgment | 2026-01-02 | Script handles S-Series (safety). AI handles principle conflict analysis. |
| Orchestrator-First | 2026-01-02 | Governance structural via orchestrator, not optional. |
| Reasoning Externalization | 2026-01-10 | `log_governance_reasoning` tool for audit trail. |

### Multi-Agent Domain

| Decision | Date | Summary |
|----------|------|---------|
| Scope Expansion v2.0.0 | 2026-01-01 | Covers individual agents, sequential, and parallel patterns. |
| Agent Definition Standard | 2026-01-01 | Required: name, description, cognitive_function, tools, system prompt. |
| Justified Complexity | 2026-01-01 | 15x token cost rule — must justify multi-agent over generalist. |
| Linear-First Default | 2026-01-01 | Sequential is safe default. Parallel requires explicit validation. |
| Task Dependency DAG | 2026-01-24 | Deadlock prevention added to §3.3. Graph traversal, depth tracking, timeout escalation. |

### Multimodal RAG Domain

| Decision | Date | Summary |
|----------|------|---------|
| Domain Created | 2026-01-24 | v1.0.0 — 12 principles (P/R/A/F series), 21 methods. Priority 40. |
| Retrieval-Only Scope | 2026-01-24 | No generation. Architect for future extensibility. |
| Mayer-Based Image Selection | 2026-01-24 | Three-Test Framework (Coherence, Unique Value, Proximity) replaces arbitrary thresholds. |
| Hierarchy Separation | 2026-01-24 | Principles platform-agnostic. Platform-specific content in appendices only. |

### Security

| Decision | Date | Summary |
|----------|------|---------|
| Security Hardening | 2026-01-03 | Bounded audit log, path traversal prevention, rate limiting, log sanitization. |
| Pause Auto-Enforcement | 2026-01-03 | True automatic enforcement needs wrapper app or mature MCP clients. Deferred. |

### AI Coding Methods Framework

| Decision | Date | Summary |
|----------|------|---------|
| Memory = Cognitive Types | 2025-12-31 | SESSION-STATE (working), PROJECT-MEMORY (semantic), LEARNING-LOG (episodic). |
| Inline Phase Gates | 2025-12-31 | Record in PROJECT-MEMORY table, not separate GATE-*.md files. |
| Principles-Based Pruning | 2025-12-31 | "Memory serves reasoning, not archival." Prune what only describes the past. |

### Implementation Details

| Decision | Date | Summary |
|----------|------|---------|
| Mock Strategy | 2025-12-27 | Patch `sentence_transformers.SentenceTransformer` (lazy-loaded). |
| Confidence Thresholds | 2025-12-31 | HIGH ≥0.7, MEDIUM ≥0.4, LOW ≥0.3. Validated — keep defaults. |
| Pre-Flight Validation | 2025-12-31 | `validate_domain_files()` — fail fast on missing config files. |
| Multi-Platform Configs | 2026-01-01 | `config_generator.py` — Gemini, Claude, ChatGPT, Cursor, Windsurf, SuperAssistant. |

---

## Metrics Registry

Systematic tracking of performance metrics. See also: ARCHITECTURE.md for test coverage.

### Retrieval Quality Thresholds

| Metric | Current | Threshold | Rationale |
|--------|---------|-----------|-----------|
| Method MRR | 0.72 | ≥ 0.60 | Primary method discovery signal |
| Principle MRR | 0.61 | ≥ 0.50 | Primary principle discovery signal |
| Method Recall@10 | 0.88 | ≥ 0.75 | Breadth of relevant results |
| Principle Recall@10 | 1.00 | ≥ 0.85 | Breadth of relevant results |
| Model Load Time | ~9s | ≤ 15s | User experience bound |

### When to Record New Baseline

- Embedding model changes
- Major index changes (new domain, significant rewrites)
- Retrieval algorithm changes
- Before releases

---

## Roadmap

### Completed Consolidations

| Topic | Status | Location |
|-------|--------|----------|
| Prompt Engineering | ✅ | Title 11 in ai-governance-methods |
| RAG Optimization | ✅ | Title 12 in ai-governance-methods |

### Future Considerations

- Prompt Engineering domain (when created, move system prompt best practices from multi-agent)
- Gateway-Based Enforcement (§4.6.2) — server-side governance for all platforms
- Vector DB migration (when scale requires)

---

## Patterns and Conventions

| Pattern | Description |
|---------|-------------|
| Communication Level | Default "Interview-ready"; deep dive on request |
| Principle IDs | `{domain}-{category}-{title-slug}` |
| Domain names | lowercase, hyphenated |
| Code Style | Python 3.10+, Pydantic, FastMCP, type hints, logging to stderr |

---

## Known Gotchas

### Active Gotchas

| # | Issue | Solution |
|---|-------|----------|
| 2 | stdout reserved for JSON-RPC | Log to stderr only |
| 3 | S-Series must always be checked | Even with domain filtering |
| 5 | ML Model mocking | Patch at `sentence_transformers.*` not import location |
| 6 | Mock embedder shape | Use `side_effect` returning `np.random.rand(len(texts), 384)` |
| 8 | MCP servers project-scoped | Use `-s user` for global scope |
| 9 | First query latency | ~9s model load. Subsequent ~50ms. |
| 10 | get_principle retrieves both | Must search both principles AND methods collections |
| 12 | evaluate_governance false positives | Security fixes trigger ESCALATE on keywords — check principles array |
| 13 | Index architecture | JSON has `embedding_id` references; vectors in `.npy` files |
| 15 | MCP caches index at startup | Restart server after `python -m ai_governance_mcp.extractor` |

### Resolved Gotchas

| # | Issue | Resolution |
|---|-------|------------|
| 14 | Method keywords title-only | ✓ Fixed — MethodMetadata + BGE model upgrade (2026-01-17) |

---

## References

- **Architecture:** ARCHITECTURE.md — system design, component responsibilities, file maps
- **Current State:** SESSION-STATE.md — working memory, next actions
- **Lessons:** LEARNING-LOG.md — episodic memory, graduated patterns
