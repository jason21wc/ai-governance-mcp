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

### 2025-12-27 - ML Model Mocking Pattern for Tests (CRITICAL)

**Context:** Writing comprehensive tests for retrieval engine with SentenceTransformer and CrossEncoder.

**What Happened:** Initial mock at `ai_governance_mcp.retrieval.SentenceTransformer` failed with `AttributeError: module does not have attribute`.

**Root Cause:** Models are lazy-loaded inside property methods, not imported at module level. The import happens when the property is first accessed.

**Solution:** Patch at the source: `sentence_transformers.SentenceTransformer` instead of where it's used.

**Pattern:**
```python
with patch("sentence_transformers.SentenceTransformer", mock_st):
    with patch("sentence_transformers.CrossEncoder", mock_ce):
        # Test code here
```

**Lesson:** When mocking lazy-loaded dependencies, patch at the source module level, not at the consumer module level.

---

### 2025-12-27 - Mock Embedder Array Shape (CRITICAL)

**Context:** Mock embedder was returning a static numpy array.

**What Happened:** Tests failed with `TypeError: only length-1 arrays can be converted to Python scalars` when batch operations were performed.

**Root Cause:** Mock returned same array regardless of input size. Batch embedding expects array shape `(num_texts, embedding_dim)`.

**Solution:** Use `side_effect` function that dynamically returns correctly-shaped arrays:
```python
def mock_encode(texts, *args, **kwargs):
    if isinstance(texts, str):
        return np.random.rand(384).astype(np.float32)
    return np.random.rand(len(texts), 384).astype(np.float32)
embedder.encode = Mock(side_effect=mock_encode)
```

**Lesson:** When mocking functions that handle variable-size inputs, use `side_effect` with a function, not `return_value`.

---

### 2025-12-27 - Falsy Values in Validation Tests

**Context:** Testing rating validation in log_feedback with rating=0.

**What Happened:** Rating=0 triggered "required field" error before the range validation check.

**Root Cause:** In Python, `if not rating:` treats 0 as falsy, same as missing.

**Solution:** Use rating=-1 to test invalid low values (clearly invalid but not falsy).

**Lesson:** When testing validation boundaries, consider Python's truthiness rules. Zero is falsy.

---

### 2025-12-27 - Shared Test Fixtures Pattern

**Context:** Multiple test files needed same fixtures (mock embedder, sample principles, test settings).

**What Happened:** Initially duplicated fixture code across test files.

**Solution:** Created `tests/conftest.py` with comprehensive shared fixtures:
- `sample_principle`, `sample_s_series_principle` - Model fixtures
- `mock_embedder`, `mock_reranker` - ML model mocks
- `test_settings`, `saved_index` - Configuration fixtures
- `reset_server_state` - Server singleton cleanup

**Lesson:** Invest in `conftest.py` early. Shared fixtures reduce duplication and ensure consistent test behavior.

---

## Patterns That Worked

| Pattern | Context | Why It Worked |
|---------|---------|---------------|
| Fix spec first | Spec had gaps | Prevented implementation rework |
| Research before deciding | Search approach | Found better middle-ground option |
| Gate artifacts | Phase transitions | Clear validation checkpoints |
| **Process Map visualization** | Discovery phase | PO visibility into workflow position |
| **conftest.py fixtures** | Test suite | Shared fixtures, 193 tests, 93% coverage |
| **side_effect for mocks** | ML model mocking | Handles variable input sizes correctly |
| **Patch at source** | Lazy-loaded deps | Works when imports are inside methods |
| **CPU-only PyTorch in CI** | ML project CI/CD | Avoids 4GB CUDA deps that fill disk |
| **fail-fast: false** | Matrix debugging | See all failures, not just first |

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

### 2025-12-27 - GitHub Actions CI/CD Lessons (CRITICAL)

**Context:** Setting up CI pipeline for automated testing, linting, and security scanning.

**Issues Encountered:**

1. **Lint Failures - Unused Imports (F401)**
   - Ruff flagged unused imports we hadn't noticed locally
   - Fix: Run `ruff check --fix src/ tests/` before committing
   - Lesson: Add pre-commit hooks or run linter locally before push

2. **Lint Failures - Ambiguous Variable Name (E741)**
   - `O = "O"` in enum flagged as confusable with zero
   - Fix: Renamed to `OPER = "O"`
   - Lesson: Linters catch issues humans miss; embrace them

3. **Disk Space Exhaustion (Errno 28)**
   - `sentence-transformers` pulls PyTorch with CUDA (~900MB torch + ~3GB nvidia-*)
   - GitHub Actions runners have ~14GB disk; CUDA dependencies filled it
   - Fix: Pre-install CPU-only PyTorch before other deps:
     ```yaml
     pip install torch --index-url https://download.pytorch.org/whl/cpu
     pip install -e ".[dev]"
     ```
   - Lesson: ML libraries default to GPU builds; explicitly use CPU for CI

4. **Matrix Job Cancellation (fail-fast)**
   - Default `fail-fast: true` cancels sibling matrix jobs on first failure
   - Made debugging harder (couldn't see if 3.11/3.12 would pass)
   - Fix: Add `fail-fast: false` to matrix strategy
   - Lesson: Disable fail-fast during debugging; re-enable for faster CI later

**Best Practices Established:**
- Run `ruff check src/ tests/ && ruff format --check src/ tests/` locally before push
- Use CPU-only PyTorch in CI for ML projects
- Set `continue-on-error: true` for informational checks (pip-audit)
- Use `fail-fast: false` initially, optimize later

### 2025-12-28 - Regex Quantifier Bug in Method Extraction

**Context:** Methods from ai-coding-methods-v1.1.0.md weren't being extracted despite extractor code existing.

**What Happened:** Extractor reported "0 methods" for ai-coding. Investigation revealed regex `\d+(?:\.\d+)?` only matched 1-2 level section numbers (like `1.2`) but not 3-level (like `1.2.3`).

**Root Cause:** Regex quantifier `?` means "0 or 1", not "0 or more". The pattern needed `*` instead.

**Fix:** Changed `\d+(?:\.\d+)?` to `\d+(?:\.\d+)*`

**Lesson:** When matching repeating patterns like version numbers or section numbers, use `*` (zero or more) not `?` (zero or one). Test regex patterns with actual document samples before assuming they work.

---

### 2025-12-28 - Domain Routing Threshold and Fallback

**Context:** Queries like "unit tests in Python" weren't being routed to ai-coding domain, so ai-coding methods weren't returned.

**What Happened:** Domain similarity threshold was 0.5, but typical query-to-domain similarities were 0.25-0.40. Also, when no domain passed threshold, system only searched constitution.

**Fixes Applied:**
1. Lowered threshold from 0.5 to 0.25
2. Added fallback: search ALL domains when no specific match
3. Enriched domain descriptions with common query terms

**Lesson:** Semantic similarity thresholds need empirical tuning. Default fallback behavior (searching all vs searching none) matters more than threshold precision. Domain descriptions should include the vocabulary users actually query with, not just formal category terms.

---

### 2025-12-28 - Large File Operations Can Cause Session Hangs

**Context:** Restructuring Constitution (2,578 lines) to separate principles from methods.

**What Happened:** Previous session got stuck while attempting to create a new Constitution v2.0 file. The approach was: read file in chunks, construct content in memory, write entire file with Write tool.

**Root Cause:** Large file Write operations (potentially 1,600+ lines) may timeout or cause issues in Claude Code.

**Solution:** Use shell tools for large file manipulation:
```bash
# Extract only lines to keep (safer than large Write)
sed -n '1,67p; 393,1721p; 2523,$p' old.md > new.md
```

Then use Edit tool for small, targeted changes (version headers, amendment entries).

**Lesson:** For large file restructuring:
1. Copy original file first (`cp old.md new.md`)
2. Use `sed -n` to extract sections, OR use `sed -d` to delete sections
3. Use Edit tool for small targeted changes
4. Avoid constructing large files in-memory and writing all at once

**Principles Applied:**
- Break complex operations into atomic steps
- Use the right tool for the job (shell for bulk, Edit for precision)
- Document approach in SESSION-STATE so recovery is possible if session fails

---

### 2025-12-28 - Constitution/Methods Separation Pattern

**Context:** AI interaction principles document was 2,578 lines mixing WHAT (principles) with HOW (procedures).

**What Happened:** Document was hard to navigate, hard to maintain, and violated Single Source of Truth principle (procedural content was duplicated or inconsistent with methods docs).

**Pattern Applied:** Legal system analogy - separate Constitution (principles, immutable law) from Procedures (methods, operational implementation).

**Result:**
- Constitution: 2,578 → 1,476 lines (42 principles only)
- Methods: 835 → 1,489 lines (added TITLEs 7/8/9)
- Clear separation of concerns
- Each document has single purpose

**Lesson:** For governance frameworks:
1. Principles define WHAT (rules, constraints, requirements)
2. Methods define HOW (procedures, workflows, checklists)
3. Keep them in separate documents
4. Reference via clear cross-links
5. Version independently (principles change rarely, methods evolve)

**Framework Impact:** Domain principles should follow same pattern - domain-principles.md for rules, domain-methods.md for procedures.

---

### 2025-12-29 - Framework Bootstrap/Activation Problem (CRITICAL)

**Context:** Comprehensive review of governance framework for completeness and proper AI integration.

**What Happened:** Despite having a complete governance framework (Constitution, 2 domains, methods for each), a fresh Claude Code session had no automatic way to:
1. Know the governance framework exists
2. Know to query the MCP server
3. Follow the activation protocol

**Root Cause:** The framework had all the rules (principles) and procedures (methods), but no **entry point**. It's like having laws but no way to tell citizens the laws exist.

**Solution - Three-Layer Activation:**

1. **CLAUDE.md** (auto-loaded by Claude Code)
   - Tool-specific entry point
   - Points to ai-instructions and MCP
   - Created in project root

2. **ai-instructions-v2.3.md** (loader document)
   - Full activation protocol
   - Domain detection rules
   - First response protocol
   - Now includes multi-agent domain and MCP integration

3. **ai-governance-methods "Framework Activation" section**
   - Documents the bootstrap sequence
   - References ai-instructions as the canonical loader
   - Closes the documentation loop

**Bootstrap Sequence:**
```
Tool Config (CLAUDE.md) → ai-instructions → Constitution → Domain → Methods
```

**Lesson:** A governance framework needs THREE things:
1. **Rules** (principles) - WHAT to do
2. **Procedures** (methods) - HOW to do it
3. **Activation** (loader) - HOW TO GET STARTED

The third is often forgotten. Without explicit activation, the framework exists but isn't used.

**Pattern:** For any governance/ruleset system:
- Always create an entry point document
- Document how AI/users discover and activate the rules
- Reference the loader from the methods so the documentation is complete

---

### 2025-12-29 - Anchor Bias in Document Review

**Context:** Reviewing governance documents that I had been working on in the same session.

**What Happened:** User explicitly requested "fresh eyes" and "avoiding anchor bias" when reviewing documents. This was a reminder that working on documents creates familiarity that can blind you to issues.

**Mitigation Strategies Used:**
1. Query external best practices (web search) for comparison
2. Test MCP retrieval to see how it performs
3. Check version references systematically (found several outdated)
4. Look for missing pieces, not just errors in existing pieces

**Lesson:** When reviewing your own work:
- Explicitly search for gaps (what's missing) not just errors (what's wrong)
- Compare against external standards
- Check cross-references systematically
- The user asking to "avoid anchor bias" is a signal to use external validation

---

## Patterns That Failed

| Pattern | Context | Why It Failed |
|---------|---------|---------------|
| Spec-as-requirements | Treated spec v3 as validated requirements | Spec was a starting point, not PO approval. Built wrong architecture. |
| Optimize for stated constraints | Optimized for "~5% miss rate" in spec | Never verified PO actually wanted that constraint. |
| Skip discovery for existing docs | Had detailed spec, skipped discovery questions | Spec authors' assumptions ≠ PO's actual requirements |

---

## Future Considerations

1. ~~**Hybrid retrieval implementation:**~~ COMPLETE - all-MiniLM-L6-v2 for embeddings, ms-marco-MiniLM-L-6-v2 for reranking, 60/40 semantic/keyword fusion.
2. **Cross-tool synchronization:** Multi-agent domain mentions claude.md ↔ gemini.md sync. Not in v1 scope but may need future support.
3. **Hot reload:** Currently requires server restart for domain changes. Could add file watcher.
4. **Public deployment:** PO wants this online for others. Need to consider hosting, API rate limits, and scalability.
5. **Additional domains:** Prompt engineering, RAG optimization, sci-fi/fantasy writing, hotel analysis planned.
6. **Knowledge graph tier:** Tier 3 enhancement for relationship-based retrieval if needed.

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
