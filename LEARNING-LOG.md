# AI Governance MCP - Learning Log

## Purpose
This log captures lessons learned during development. Review before making changes.

---

## Lessons

### 2025-12-24 - Specification Documents Are Not Validated Requirements (CRITICAL)
**Context:** Implemented full MCP server based on specification-v3.md which said "~5% miss rate with keyword matching"
**What Happened:** After implementation was complete, Product Owner review revealed:
- 5% miss rate is unacceptable for production compliance tool
- Semantic understanding is CRITICAL, not optional
- This is a showcase project, not minimal viable
- PO wants "advanced, effective" solution, not "skimping"

**Root Cause:** **Anchor Bias** - The specification document was treated as validated requirements instead of as input to a discovery process. The spec became a constraint rather than a starting point.

**Principles Violated:**
- **C1 (Specification Completeness):** "No Assumptions - flag and ask"
- **P4 (Human-AI Collaboration):** "Escalate with options, wait for explicit decision"
- **Constitution:** "Pause and request human clarification before proceeding"

**Lesson:** A specification document, even a detailed one, is NOT the same as validated Product Owner requirements. Before implementing architectural decisions:
1. Run discovery questions with PO
2. Present options with tradeoffs (per P4)
3. Wait for explicit approval
4. The spec informs the process but doesn't replace it

**Action:**
- Returning to SPECIFY phase for proper discovery
- Must complete discovery questions before redesigning
- Will implement hybrid retrieval (BM25 + semantic) based on actual PO requirements

**Framework Note:** The principles themselves are correct - the failure was in application. Consider adding explicit check to CLAUDE.md: "If entering mid-project, verify previous phase artifacts were properly validated with PO."

---

### 2025-12-22 - Specification Completeness Critical
**Context:** Beginning implementation of MCP server based on specification-v2.md
**What Happened:** Thorough review revealed specification was only ~70% complete. Critical gaps included undefined retrieval algorithm, missing S-Series triggers, unspecified output formats for 3 tools, and contradictory parameters.
**Lesson:** Even "complete" specifications may have gaps. Per C1 (Specification Completeness), verify specification completeness before implementation, not just at the start.
**Action:** Created specification-v3.md with all gaps addressed. Added specification review to standard workflow.

---

### 2025-12-22 - Miss Rate Analysis for Search Approaches
**Context:** Deciding between keyword, semantic, or hybrid search approaches
**What Happened:** Research showed pure keyword matching has 20-25% miss rate, semantic embeddings <3%, but semantic adds PyTorch (~2GB dependency).
**Lesson:** There's a middle ground: expanded metadata (synonyms, aliases, failure_indicators) achieves ~5% miss rate with zero heavy dependencies.
**Action:** Chose expanded keyword approach. Added synonyms, aliases, failure_indicators to principle schema.

---

### 2025-12-22 - Multi-Domain Retrieval Needed
**Context:** Designing domain detection behavior
**What Happened:** Realized queries like "implement a multi-agent code review system" touch both ai-coding and multi-agent domains. Single-domain selection would miss relevant principles.
**Lesson:** Real-world queries often span domains. Design should support multi-domain retrieval, not force single-domain selection.
**Action:** Updated domain resolution to return list of domains. Added conflict resolution logic for ties.

---

### 2025-12-22 - stdout Reserved for MCP
**Context:** Researching MCP SDK best practices
**What Happened:** MCP protocol uses stdout for JSON-RPC messages. Logging to stdout would break protocol.
**Lesson:** Always log to stderr when building MCP servers.
**Action:** Added logging configuration requirement: `stream=sys.stderr`.

---

## Patterns That Worked

| Pattern | Context | Why It Worked |
|---------|---------|---------------|
| Fix spec first | Spec had gaps | Prevented implementation rework |
| Research before deciding | Search approach | Found better middle-ground option |
| Gate artifacts | Phase transitions | Clear validation checkpoints |
| **Process Map visualization** | Discovery phase | PO visibility into workflow position |

### 2025-12-26 - Process Map Visualization Pattern (PO APPROVED)

**Context:** During SPECIFY discovery phase, PO requested more visibility into where we are in the process.

**What Worked:** ASCII process map showing:
- Current phase and sub-steps
- Checkmarks for completed items
- Arrow marker for current position
- Preview of upcoming phases

**Example Format:**
```
SPECIFY PHASE — Discovery (§2.1)
─────────────────────────────────────────────────────────────────────────────
├── [✓] Completed item
├── [✓] Another completed item
├── [~] Current item ◄── CURRENT QUESTION
├── [ ] Upcoming item
└── [ ] Final item in section

NEXT PHASE (after gate)
─────────────────────────────────────────────────────────────────────────────
├── Future work preview
└── GATE-*.md
```

**PO Feedback:** "That Process Map is perfect."

**Application Rule:** Show updated process map:
- After major accomplishments
- On request for updates
- At phase transitions
- Periodically during long discovery conversations

**Why It Works:**
1. Provides context without requiring PO to ask
2. Helps PO "think accordingly" based on where we are
3. Shows progress momentum
4. Previews what's coming next

### 2025-12-26 - Communication Level Calibration (PO APPROVED)

**Context:** Technical discussions were getting too detailed for efficient PO review.

**PO Guidance:** "Interview-ready" level — what and why in brief sentences. Enough to explain to others, not implementation details. PO will ask for deeper dives when needed.

**Application Rule:**
- Default: High-level what/why (1-2 sentences per concept)
- On request: Mid-level detail (our recent exchanges)
- Deep dive: Only when explicitly requested

**Example:**
- Too detailed: "We use sentence-transformers with all-MiniLM-L6-v2 which produces 384-dimensional embeddings..."
- Right level: "We use industry-standard embedding models to convert text to vectors for semantic search."

### 2025-12-26 - Portfolio-Ready README Pattern (PO APPROVED)

**Context:** Project will be showcased as portfolio item for recruiters, customers, and SME audiences.

**Insight:** Specification (internal planning doc) ≠ README (external showcase). Different audiences, different framing.

**Multi-Audience README Structure:**
1. **Headline + Hook** — What it does in one line
2. **Problem Statement** — Relatable pain point
3. **Solution Overview** — What it does
4. **Key Innovation** — The differentiator (for this project: the governance framework)
5. **Tech Stack** — Skills showcase (recruiters look here)
6. **Architecture** — System design credibility
7. **How It Works** — Technical depth
8. **Results/Metrics** — Quantifiable outcomes
9. **Getting Started** — Proves it's real and usable
10. **The Methodology** — Thought leadership content
11. **About** — Positioning

**Differentiator Statement (template):**
> "Most people use AI as-is. I built a governance framework that makes AI collaboration systematic, repeatable, and production-ready — then built an MCP that operationalizes it."

**Audience Priorities (in order):**
1. Recruiters — skills match, problem-solving, modern stack
2. Customers — methodology, results, professionalism
3. SME/Presenters — novel approach, depth, teachable
4. General — clear explanations, reproducible patterns

**Application Rule:** For portfolio-worthy projects, create README.md as derived artifact from spec, formatted for external audience.

## Patterns That Failed

| Pattern | Context | Why It Failed |
|---------|---------|---------------|
| Spec-as-requirements | Treated spec v3 as validated requirements | Spec was a starting point, not PO approval. Built wrong architecture. |
| Optimize for stated constraints | Optimized for "~5% miss rate" in spec | Never verified PO actually wanted that constraint. |
| Skip discovery for existing docs | Had detailed spec, skipped discovery questions | Spec authors' assumptions ≠ PO's actual requirements |

---

## Future Considerations

1. **Hybrid retrieval implementation:** NOW REQUIRED - not optional. Research best embedding models (all-MiniLM-L6-v2, e5-base-v2, etc.) and reranking strategies.
2. **Cross-tool synchronization:** Multi-agent domain mentions claude.md ↔ gemini.md sync. Not in v1 scope but may need future support.
3. **Hot reload:** Currently requires server restart for domain changes. Could add file watcher.
4. **Public deployment:** PO wants this online for others. Need to consider hosting, API rate limits, and scalability.

## Research Links (from 2025-12-24 session)

Hybrid retrieval best practices:
- [Elastic Hybrid Search Guide](https://www.elastic.co/what-is/hybrid-search)
- [Genzeon: Hybrid Retrieval and Reranking](https://www.genzeon.com/hybrid-retrieval-deranking-in-rag-recall-precision/)
- [Microsoft: Common RAG Techniques](https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/02/04/common-retrieval-augmented-generation-rag-techniques-explained/)
- [Unstructured: RAG Without Embeddings](https://unstructured.io/blog/rethinking-rag-without-embeddings)
- [Security Boulevard: Smart Retrieval for Compliance](https://securityboulevard.com/2025/04/why-smart-retrieval-is-critical-for-compliance-success/)

Embedding models:
- [all-MiniLM-L6-v2 on HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) - 22MB, 384 dimensions, good baseline
- [Sentence Transformers Documentation](https://sbert.net/docs/quickstart.html)
