# AI Governance MCP - Project Memory

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Centralized multi-domain AI governance document retrieval
- **Owner:** Jason
- **Status:** PLAN phase complete, entering TASKS
- **Procedural Mode:** STANDARD
- **Quality Target:** Showcase/production-ready, public-facing tool
- **Portfolio Goal:** Showcase for recruiters, consulting customers, SME presentations
- **Repository:** github.com/[username]/ai-governance-mcp (private, future public)

## Architecture Summary

```
Query → Domain Resolution → Constitution Search (always) → Domain Search → Hierarchy Order → Response
```

**Core Components:**
- `server.py` - FastMCP server with 9 tools
- `retrieval.py` - Scoring, matching, ordering logic
- `extractor.py` - Document parsing, index generation
- `models.py` - Pydantic data structures
- `config.py` - Configuration management

**Data Flow:**
1. documents/*.md → extractor.py → index/*.json + cache/*.md
2. Query → retrieval.py → scored principles → server.py → formatted response

## Key Decisions Log

### Decision: Architecture Direction Confirmed via Industry Research
- **Date:** 2025-12-26
- **Status:** CONFIRMED - Awaiting tier selection
- **Research Conducted:** Legal AI, Medical CDSS, Multi-Domain KB patterns
- **Industry Consensus:**
  - Hybrid retrieval (BM25 + semantic) is standard for high-stakes retrieval
  - Router/Controller pattern scales to hundreds of knowledge bases
  - Rich domain metadata enables accurate routing
  - Hierarchical document structure important
- **Architecture Direction:** Single MCP with intelligent routing + hybrid retrieval
- **Sources:** Harvard JOLT, Stanford HAI, PMC, InfoQ Domain-Driven RAG

### Decision: Scale Requirements Clarified
- **Date:** 2025-12-26
- **Status:** CONFIRMED
- **PO Requirements:**
  - Many domains planned: ai-coding, multi-agent, prompt engineering, RAG optimization, sci-fi/fantasy writing, hotel analysis, and more
  - Each domain similar size to ai-coding (principles + methods)
  - Must scale to 10+ domains
  - Open to dependencies for quality ("as comfortable as you are")
  - Brainstorm first, constrain later approach
- **Implication:** Design must handle many domains with smart routing

### Decision: REVISED - Hybrid Retrieval Required (Keyword-Only Rejected)
- **Date:** 2025-12-24
- **Status:** CONFIRMED by 2025-12-26 research
- **Context:** Original decision for keyword-only was made without PO validation
- **PO Requirements (now captured):**
  - Miss rate must be industry-standard (~1% or less), not 5%
  - Semantic understanding is CRITICAL - users won't remember exact keywords
  - This is a showcase project for public use, not minimal viable
  - Effectiveness > minimal dependencies
- **New Direction:** Hybrid retrieval (BM25 + semantic reranking)
- **Implication:** Need to redesign retrieval.py with embedding model

### Decision: SUPERSEDED - Expanded Keyword-Based Matching
- **Date:** 2025-12-22
- **Status:** SUPERSEDED by above - keyword-only insufficient for PO requirements
- **Original Rationale:** Pure keyword: 20-25% miss rate. Expanded keyword: ~5% miss rate with zero heavy dependencies.
- **Why Superseded:** 5% miss rate unacceptable for production compliance tool. Semantic understanding required for natural language queries.

### Decision: Multi-Domain Retrieval (Return All Matching)
- **Date:** 2025-12-22
- **Rationale:** Queries like "multi-agent code review" touch both ai-coding and multi-agent domains. Returning both provides complete guidance.
- **Implication:** Domain resolution can return list, not just single domain.

### Decision: Fix Specification Before Implementation
- **Date:** 2025-12-22
- **Rationale:** Specification was ~70% complete with critical gaps (retrieval algorithm, S-Series triggers, output formats). Fixing first prevents rework.
- **Implication:** Created v3 specification with ~4-6 hours additional work upfront.

### Decision: Single MCP for All Domains
- **Date:** 2025-12-22
- **Rationale:** Constitution always applies. Cross-domain retrieval needed. Simpler deployment.
- **Implication:** Internal domain isolation via domains.json registry.

### Decision: FRAMEWORK-EVALUATION.md for Meta-Observations
- **Date:** 2025-12-22
- **Rationale:** Track effectiveness of the governance framework itself, not project-specific lessons.
- **Implication:** New documentation file added to requirements.

## Patterns and Conventions

### Naming
- Principle IDs: `meta-C1`, `coding-C1`, `multi-A1` (internal use only)
- Cache files: `cache/[prefix]-[code].md`
- Domain names: lowercase, hyphenated (`ai-coding`, `multi-agent`)

### Cross-Document Reference Convention
**Internal codes (C1, Q2, P3) are for retrieval/indexing only.**
When one document references another, use the **principle name**:
- ✓ "Per Specification Completeness, verify before implementation"
- ✓ "Derives from Context Engineering (Constitution)"
- ✗ "Per C1..." (ambiguous - which C1? meta-C1? coding-C1?)

This convention is documented in ai-coding-domain-principles §Reference Convention.

### Code Style
- Python 3.10+
- Pydantic for data models
- FastMCP for server
- Type hints throughout
- Logging to stderr (stdout reserved for JSON-RPC)

### Error Handling
- Return isError flag for tool errors (not protocol errors)
- Structured error responses with suggestions
- Edge cases explicitly defined in spec v3

## Known Gotchas

### Gotcha 1: Line Range Drift
If source documents are edited, line_range in index becomes stale.
**Solution:** Always run extraction after document edits.

### Gotcha 2: Domain Detection False Positives
"Write code" contains "write" which might trigger ai-writing (future domain).
**Solution:** Phrase matching has priority; whole-word matching prevents "code" matching "decode".

### Gotcha 3: S-Series Must Always Be Checked
Even with include_constitution=False, S-Series triggers must be checked.
**Solution:** Constitution search always runs internally; parameter only controls output.

### Gotcha 4: stdout Reserved
MCP protocol uses stdout for JSON-RPC. All logging must go to stderr.
**Solution:** Configure logging with stream=sys.stderr.

### Gotcha 5: Spec Documents Are Not Validated Requirements
A specification document, even a detailed one, is NOT the same as validated Product Owner requirements.
**What Happened:** Spec v2/v3 said "~5% miss rate with keyword matching" and this was implemented without confirming the PO actually wanted that approach.
**Solution:** Always run discovery questions with PO before treating spec as requirements. Per C1/P4, clarify and present options.

## Current State

### Completed (Needs Rework)
- [x] Specification v3 creation (needs v4 with hybrid retrieval)
- [x] Full keyword-only implementation (architecturally wrong)
- [x] 24 tests passing (will need updates for hybrid)
- [x] Documentation (will need updates)

### Current Position
- Returning to SPECIFY phase for proper requirements discovery
- Keyword-only implementation exists but doesn't meet PO requirements
- Need to implement hybrid retrieval (BM25 + semantic)

### Next Steps
1. [ ] Complete PO discovery questions
2. [ ] Research and present hybrid retrieval options
3. [ ] Create specification v4 with validated requirements
4. [ ] Redesign retrieval architecture
5. [ ] Implement hybrid retrieval
6. [ ] Update tests for semantic functionality
7. [ ] Final validation

## File Map

| File | Purpose | Status |
|------|---------|--------|
| ai-governance-mcp-specification-v3.md | Complete specification | Done |
| SESSION-STATE.md | Current position | Done |
| PROJECT-MEMORY.md | This file | Done |
| LEARNING-LOG.md | Lessons learned | Pending |
| FRAMEWORK-EVALUATION.md | Meta-observations | Pending |
| GATE-PLAN.md | Plan phase gate | Pending |

## Dependencies

| Package | Version | Why |
|---------|---------|-----|
| mcp | >=1.0.0 | MCP SDK (FastMCP) |
| pydantic | >=2.0.0 | Data models, validation |
| pytest | >=7.0.0 | Testing (dev) |

## Testing Notes

### How to Test
```bash
# After implementation:
pytest tests/
python -m src.server --test "specs seem incomplete"
```

### Test Scenarios (from spec v3)
1. Domain auto-detection (ai-coding)
2. Domain auto-detection (multi-agent)
3. Multi-domain overlap
4. Constitution only
5. S-Series priority
6. Methods retrieval
7. Unknown domain
8. Empty query
9. Principle not found
