    # AI Governance MCP Server — Specification v4

**Version:** 4.0
**Date:** 2025-12-26
**Status:** Draft — Pending PO Approval
**Phase:** SPECIFY

---

## 1. Problem Statement

AI assistants are generalists. To make them effective for specific workflows, you need to provide principles and methods — but loading all documents into context is inefficient and doesn't scale.

**This MCP solves that problem** by acting as a "second brain" that retrieves only the relevant principles for any given query, using semantic understanding rather than requiring exact keyword matches.

---

## 2. Target Users

**Primary:** You (Jason) — using AI assistants (Claude, GPT, Gemini) for various domains.

**Future:** Others who want to use or license access to the governance framework.

---

## 3. Core Features

| # | Feature | What It Does |
|---|---------|--------------|
| 1 | **Smart Domain Routing** | Identifies which domain(s) a query relates to before searching |
| 2 | **Hybrid Search** | Combines keyword matching (BM25) with semantic understanding (embeddings) |
| 3 | **Cross-Encoder Reranking** | Re-scores top results for higher precision |
| 4 | **Hierarchy Awareness** | Always checks constitution; respects principle precedence |
| 5 | **Confidence Scoring** | Returns confidence levels so AI knows how much to trust results |
| 6 | **Feedback Logging** | Tracks retrieval quality for continuous improvement |
| 7 | **Multi-Domain Support** | Scales to 10+ domains with consistent retrieval quality |

---

## 4. How It Works (High Level)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  AI Query    │ ──→ │  MCP Server  │ ──→ │  Relevant    │
│              │     │              │     │  Principles  │
│ "moving too  │     │ 1. Route     │     │              │
│  fast..."    │     │ 2. Search    │     │ • Spec       │
│              │     │ 3. Rerank    │     │   Completeness│
│              │     │ 4. Return    │     │ • Discovery  │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Build time:** Documents are parsed, indexed, and embedded once.
**Runtime:** Queries hit the index, not the original documents.

---

## 5. MCP Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `query_governance` | Main retrieval — find relevant principles for a query | Ranked principles with confidence |
| `get_principle` | Direct lookup by principle name or ID | Single principle with full context |
| `list_domains` | Show available domains | Domain names and descriptions |
| `get_domain_summary` | Overview of a specific domain | Principle count, key themes |
| `log_feedback` | Record retrieval quality feedback | Confirmation |
| `get_metrics` | Retrieval performance stats | Miss rate, query counts |

---

## 6. Success Criteria

| Metric | Target | How Measured |
|--------|--------|--------------|
| **Miss Rate** | <1% | Feedback logging + periodic review |
| **Retrieval Latency** | <100ms | Timed at query execution |
| **User Experience** | "Asked and got what I needed" | Qualitative — does it work? |

---

## 7. Technical Approach

### Retrieval Pipeline

1. **Domain Routing** — Embedding similarity identifies relevant domain(s)
2. **Hybrid Search** — BM25 (keyword) + dense vectors (semantic) combined
3. **Reranking** — Cross-encoder scores top candidates for precision
4. **Hierarchy Filter** — Constitution always included; S-Series prioritized

### Why Hybrid?

- **BM25 alone:** Misses semantic relationships ("moving fast" ≠ "specification completeness")
- **Embeddings alone:** Can miss exact keyword matches
- **Hybrid:** Best of both — industry standard for high-stakes retrieval

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Server | FastMCP | Official MCP SDK |
| Embeddings | sentence-transformers | Industry standard, local inference |
| Keyword Search | rank-bm25 | Proven BM25 implementation |
| Reranking | sentence-transformers CrossEncoder | Same library, quality rerankers |
| Data Models | Pydantic | Validation and type safety |
| Storage | In-memory (JSON + NumPy) | Sufficient for our scale |

---

## 8. Domains (Initial + Planned)

| Domain | Status | Description |
|--------|--------|-------------|
| ai-interaction (meta) | Exists | Constitution — universal principles |
| ai-coding | Exists | Software development principles/methods |
| multi-agent | Exists | Multi-agent system principles/methods |
| prompt-engineering | Planned | Prompt design principles/methods |
| rag-optimization | Planned | RAG system principles/methods |
| writing-fiction | Planned | Sci-fi/fantasy writing principles |
| hotel-analysis | Planned | Hotel evaluation principles |
| [more as needed] | Future | Extensible by design |

---

## 9. Out of Scope (v1)

| Item | Why Deferred |
|------|--------------|
| Multi-user authentication | Future monetization phase |
| Knowledge graph relationships | Tier 3 — architected for, not implemented |
| LLM-assisted routing | Adds latency/cost; embedding routing sufficient |
| Active learning from feedback | Tier 3 — logging now enables it later |
| Web UI | MCP is the interface; AI is the UI |

---

## 10. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Startup Time** | <5 seconds (model loading) |
| **Memory Footprint** | Reasonable for modern hardware (no artificial limit) |
| **Deployment** | Local-first, cloud-deployable |
| **Extensibility** | New domain = add docs + rebuild index |
| **Stateless** | No server-side session state (scales horizontally) |

---

## 11. Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.10+ | Type hints, modern features |
| Local embedding inference | No external API dependencies for core function |
| Stateless design | Future horizontal scaling for multi-user |

---

## 12. Future Phases (Noted, Not Scoped)

| Phase | What | When |
|-------|------|------|
| **Multi-User Access** | Authentication, user isolation | When ready to share publicly |
| **Monetization** | Stripe integration, access tiers | After multi-user |
| **Knowledge Graph** | Principle relationships across domains | When value demonstrated |
| **Active Learning** | Improve from feedback automatically | When enough feedback collected |

---

## 13. Acceptance Criteria

The MCP is complete when:

- [ ] All 6 tools implemented and functional
- [ ] Hybrid search returns relevant principles for test queries
- [ ] Latency <100ms for typical queries
- [ ] Feedback logging captures retrieval quality
- [ ] New domain can be added by: add docs → run extractor → restart
- [ ] Passes test suite with >80% coverage

---

## 14. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Embedding model size (~200MB) | Certain | Low | Accept — quality requires it |
| Cold start latency | Medium | Low | Pre-warm on startup |
| Document drift (stale index) | Medium | Medium | Rebuild index on doc changes |
| Query ambiguity | Medium | Low | Return multi-domain results |

---

## Approval

**Product Owner Review:**

- [ ] Problem statement accurate
- [ ] Features match vision
- [ ] Success criteria acceptable
- [ ] Out of scope items agreed
- [ ] Ready to proceed to PLAN phase

**PO Notes:** _[To be filled]_

**Date:** _[To be filled]_
