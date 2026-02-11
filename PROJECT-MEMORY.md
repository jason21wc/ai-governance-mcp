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
- **Status:** COMPLETE - All phases done, 15 tools (11 governance + 4 context engine). Run `pytest tests/ -v` for current test counts.
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
| Skip-List Governance | 2026-02-01 | Deny-by-default: evaluate unless on skip-list (4 exceptions). Replaces subjective "significant action". |
| Governance Docs In-Place | 2026-02-02 | Source docs edited in-place with changelog notes (not file renames). |
| Methods in evaluate_governance | 2026-02-02 | Reference-only (id/title/domain/score/confidence). Full content via `get_principle(id)`. Top-5 cap. Audit log tracks `methods_surfaced`. |

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

### Storytelling Domain

| Decision | Date | Summary |
|----------|------|---------|
| Domain Created | 2026-02-07 | v1.0.0 — 19 principles (A/ST/C/M/E series), methods for Story Bible, Session State, Revision Log, Story Log. Priority 30. |
| Comprehensive Audit v1.1.0 | 2026-02-08 | Fixed extractor bug (colon headers), strengthened trigger phrases across all 19 principles, added E1 skill erosion techniques, ST-F14 failure mode. Methods: 5 new sections (§14-§18) — Story Log Template, Character Voice Profiles, Genre Conventions Guide, Plot Consistency Checks, Coaching Question Taxonomy. Two new subagents (continuity-auditor, voice-coach). Index: 485 total items (was 460). |
| Colon Header Pattern | 2026-02-08 | Storytelling uses `### ST1: Title` (colon). Old header pattern required dot. Changed `\.` to `[.:]` in extractor. Other domains unaffected. |
| Category Collision (A-Series) | 2026-02-08 | Both multi-agent and storytelling have A-Series. Multi-agent: "Architecture" → category `architecture`. Storytelling: "Audience" → also maps to `architecture` via `"audience principle": "architecture"`. Acceptable: storytelling A-Series uses old header format (colon), which doesn't go through section header processing. Different ID prefixes (`mult-architecture-` vs `stor-architecture-`) prevent collision. |

### AI Coding Methods Framework

| Decision | Date | Summary |
|----------|------|---------|
| Memory = Cognitive Types | 2025-12-31 | SESSION-STATE (working), PROJECT-MEMORY (semantic), LEARNING-LOG (episodic). |
| Inline Phase Gates | 2025-12-31 | Record in PROJECT-MEMORY table, not separate GATE-*.md files. |
| Principles-Based Pruning | 2025-12-31 | "Memory serves reasoning, not archival." Prune what only describes the past. |
| Coherence Audit Method | 2026-02-07 | Part 4.3 in meta-methods v3.8.0. Operationalizes Context Engineering + SSOT + Periodic Re-eval. Quick/Full tiers. Method not principle — agents need HOW not more WHAT. |
| Vibe-Coding Security v2.8.0 | 2026-02-08 | 4 new sections (§5.3.5, §5.3.6, §5.4.5, §5.6) in Title 5. Implements Security-First Development, Supply Chain Integrity, Workflow Integrity principles. Research: Moltbook breach, Stanford false confidence, OWASP Agentic Top 10. Plan reviewed by 3 agents. "Coding tool injection defense" (not "prompt injection defense") avoids multi-agent domain collision. Platform checklists include staleness note. |
| App Security v2.9.0 | 2026-02-08 | 2 new Parts (§5.7, §5.8) with 10 subsections (~560 lines) in Title 5. Tier 1: application security patterns (auth/session, HTTP headers, CORS, error handling, crypto). Tier 2: domain-specific review (language patterns, API security, data protection, container security). Extends §5.3.5 blind spots into full procedures. Tier 3 (RAG poisoning, agent memory injection) deferred to multi-agent domain. Research: OWASP Top 10 2025, API Security Top 10, ASVS v5, Blue Shield of California breach (2025). |

### Implementation Details

| Decision | Date | Summary |
|----------|------|---------|
| Mock Strategy | 2025-12-27 | Patch `sentence_transformers.SentenceTransformer` (lazy-loaded). |
| Confidence Thresholds | 2025-12-31 | HIGH ≥0.7, MEDIUM ≥0.4, LOW ≥0.3. Validated — keep defaults. |
| Pre-Flight Validation | 2025-12-31 | `validate_domain_files()` — fail fast on missing config files. |
| Multi-Platform Configs | 2026-01-01 | `config_generator.py` — Gemini, Claude, ChatGPT, Cursor, Windsurf, SuperAssistant. |

### Context Engine

| Decision | Date | Summary |
|----------|------|---------|
| Reference Memory Concept | 2026-02-02 | Fifth cognitive memory type: "what exists and where is it?" Complements Working/Semantic/Episodic/Procedural. |
| Shared Repo, Separate Entry | 2026-02-02 | Context engine lives in `src/ai_governance_mcp/context_engine/`. Separate MCP server entry point (`ai-context-engine`). |
| One Server, Multi-Project | 2026-02-02 | Single MCP server manages per-project indexes. Auto-detects by working directory (hash of absolute path). |
| Hybrid Search (reused) | 2026-02-02 | Same BM25 + semantic pattern as governance server. Configurable weight (default 0.6 semantic / 0.4 keyword). |
| Pluggable Connectors | 2026-02-02 | BaseConnector interface. 5 implementations: code (tree-sitter), document (markdown/text), PDF, spreadsheet, image metadata. |
| JSON over Pickle | 2026-02-02 | BM25 index stored as JSON. NumPy loaded with `allow_pickle=False`. Prevents deserialization attacks. |
| Hex-Only Project IDs | 2026-02-02 | Project IDs are 16-char hex hashes. Regex-validated to prevent path traversal. |
| RLock for Thread Safety | 2026-02-02 | `threading.RLock` protects shared index state during watcher callbacks and queries. Reentrant for nested calls. |
| Token Bucket Rate Limiting | 2026-02-02 | `index_project` limited to 5 req/min. Expensive operation, prevents resource exhaustion. |
| Error Sanitization Parity | 2026-02-02 | Context engine mirrors governance server's error sanitization: strip paths, line numbers, addresses, module paths. |
| Score Clamping | 2026-02-02 | Float32 precision can push fused scores above 1.0. Scores clamped with `min(score, 1.0)` before validation. |
| .contextignore + .gitignore | 2026-02-02 | `.contextignore` takes precedence, falls back to `.gitignore`, then defaults. Follows fnmatch patterns. |
| Relative Paths in Output | 2026-02-04 | Connectors compute `source_path` relative to project root via `project_root` param. Prevents absolute path leakage. |
| Thread-Safe Rate Limiter | 2026-02-03 | Rate limiter globals guarded by `threading.Lock`. MCP runs handlers via `run_in_executor` thread pool. |
| Symlink Protection | 2026-02-04 | `list_projects()` skips symlinks. `delete_project()` unlinks symlinks instead of `rmtree`. File discovery already filtered. |
| Atomic JSON Writes | 2026-02-06 | `_atomic_write_json()` uses tmp file + rename for crash safety. POSIX atomic guarantees. |
| Circuit Breaker Visibility | 2026-02-06 | `watcher_status` field in ProjectStatus exposes state (running/stopped/circuit_broken/disabled). |
| Bounded Pending Changes | 2026-02-06 | MAX_PENDING_CHANGES (10K) with force-flush prevents unbounded memory growth. |
| Language-Aware Chunking | 2026-02-06 | Code connector uses BOUNDARY_PATTERNS per language for better chunk boundaries. |
| CI Context-Engine Extras | 2026-02-07 | CI must install `.[dev,context-engine]` — `pathspec` in optional extras needed by tests. |

---

## Architecture Decision Records

Expanded context for the most significant decisions. The condensed tables above serve as an index; these ADRs capture why and what changed.

### ADR-1: Hybrid Retrieval (Option C)
- **Status:** Accepted (2025-12-26)
- **Context:** Three retrieval approaches evaluated: (A) keyword-only, (B) semantic-only, (C) hybrid BM25 + semantic with reranking. PO required <1% miss rate.
- **Decision:** Option C — hybrid retrieval with cross-encoder reranking.
- **Consequences:** (+) <1% miss rate, (+) complementary strengths (keyword for exact terms, semantic for paraphrases), (-) higher latency than keyword-only (~50ms vs ~5ms), (-) requires ML model dependency.
- **Alternatives rejected:** A (~5% miss rate, insufficient), B (~3% miss rate, misses exact terminology).

### ADR-2: Embedding Model Upgrade
- **Status:** Accepted (2026-01-17), supersedes `all-MiniLM-L6-v2`
- **Context:** Method retrieval quality was poor (MRR 0.33). Root cause: MiniLM has 256-token limit, but method chunks frequently exceed this. Key content (purpose, applies_to) was truncated.
- **Decision:** Switch to `BAAI/bge-small-en-v1.5` (512-token limit, same 384 dimensions).
- **Consequences:** (+) MRR improved +112% (0.33 → 0.698), (+) no infrastructure changes needed (same dimensions), (-) slightly larger model (~33MB vs ~22MB), (-) requires model re-download on fresh installs.

### ADR-3: Hybrid AI Judgment for Governance
- **Status:** Accepted (2026-01-02)
- **Context:** Pure script-based enforcement produced too many false positives. Pure AI judgment risked missing safety violations. Needed deterministic safety with nuanced analysis.
- **Decision:** Script handles S-Series (safety) keyword detection deterministically. AI handles principle conflict analysis for non-safety principles.
- **Consequences:** (+) S-Series violations never missed (deterministic), (+) nuanced analysis for non-safety principles, (-) AI judgment depends on model capability, (-) requires `requires_ai_judgment` flag in responses.

### ADR-4: Skip-List Governance Model
- **Status:** Accepted (2026-02-01), supersedes "significant action" heuristic
- **Context:** "Evaluate for significant actions" was subjective — different AI models interpreted "significant" inconsistently. Needed deny-by-default with explicit exceptions.
- **Decision:** Evaluate governance for ALL actions unless on a narrow skip-list (4 exceptions: reads, non-sensitive questions, trivial formatting, explicit user skip).
- **Consequences:** (+) deterministic — no ambiguity about what requires evaluation, (+) consistent across AI models, (-) more governance calls for borderline actions, (-) skip-list must be maintained in sync across instruction surfaces (Gotcha #17).

### ADR-5: Cognitive Memory Architecture
- **Status:** Accepted (2025-12-31), extended 2026-02-02 (Reference Memory)
- **Context:** AI sessions are stateless. Needed external memory that maps to known cognitive science patterns. CoALA framework (Cognitive Architectures for Language Agents) provides taxonomy.
- **Decision:** Four memory types mapped to files: Working (SESSION-STATE), Semantic (PROJECT-MEMORY), Episodic (LEARNING-LOG), Procedural (methods docs). Fifth type (Reference Memory via Context Engine) added 2026-02-02.
- **Consequences:** (+) clear lifecycle per type (transient/accumulate/prune/evolve), (+) prevents "memory as archive" antipattern, (-) requires discipline to route content correctly, (-) new contributors must learn the taxonomy.

### ADR-6: Context Engine as Separate Server
- **Status:** Accepted (2026-02-02)
- **Context:** Governance server indexes governance content. Projects also need project-specific content awareness. Could be same server (add tools) or separate server (independent lifecycle).
- **Decision:** Shared repository, separate MCP entry point (`ai-context-engine`). Code lives in `src/ai_governance_mcp/context_engine/`.
- **Consequences:** (+) independent deployment and configuration, (+) shared dependencies (sentence-transformers, BM25), (+) separate rate limiting and security boundaries, (-) two servers to configure, (-) optional dependency group adds CI complexity (Gotcha #23).

### ADR-7: JSON over Pickle for Index Storage
- **Status:** Accepted (2026-02-02)
- **Context:** BM25 index and metadata need persistence. Pickle is Python's default serialization but allows arbitrary code execution on deserialization — a known security risk for files that could be tampered with.
- **Decision:** BM25 stored as JSON. NumPy arrays loaded with `allow_pickle=False`. No pickle anywhere in the project.
- **Consequences:** (+) eliminates deserialization attack vector, (+) human-readable index files for debugging, (-) JSON serialization slightly slower, (-) custom serialization needed for BM25 corpus.

### ADR-8: Coherence Audit as Method, Not Principle
- **Status:** Accepted (2026-02-07)
- **Context:** Documentation drift is a real problem — facts go stale across sessions. Three existing principles (Context Engineering, SSOT, Periodic Re-evaluation) address the "what" but agents need "how" — a concrete procedure.
- **Decision:** Part 4.3 in meta-methods: executable drift detection procedure with Quick (session start, advisory) and Full (pre-release, gate) tiers.
- **Consequences:** (+) operationalizes existing principles, (+) two tiers match urgency levels, (+) dedicated subagent (coherence-auditor) for fresh-context review, (-) method content must be tuned for retrieval surfacing (bold terms, descriptive titles, Applies To field).

### ADR-9: Docker AMD64-Only
- **Status:** Accepted (2026-01-18)
- **Context:** Multi-arch Docker builds via QEMU make embedding generation ~500x slower. MKL-DNN can't detect ARM features under emulation. Build time exceeded CI limits.
- **Decision:** AMD64-only images. Apple Silicon runs via Rosetta 2 translation.
- **Consequences:** (+) CI builds complete in reasonable time, (+) Rosetta 2 performance acceptable for stdio MCP, (-) no native ARM64 images, (-) ARM Linux servers can't run the image.

### ADR-11: Cross-Level Method References Are Valid (No Elevation)
- **Status:** Accepted (2026-02-08)
- **Context:** Meta-methods Part 4.3.3 Generic Checks #1 and #4 reference ai-coding methods (§7.5.1 Source Relevance Test, §7.8.3 File Creation Notes). v3.9.1 disambiguated with document qualifiers. Question: should these domain procedures be elevated to meta-methods since they serve a framework-level audit?
- **Decision:** Do not elevate. Cross-level references from meta-methods to domain-methods are architecturally valid per §9.7.5. Instead, inline the core decision criterion ("a fact belongs if removing it would cause someone to make a mistake") into the Generic Check #1 table cell, keeping the full procedure in ai-coding.
- **Rationale:** (1) §8.2 classifies these as Level 4 methods, not framework principles — classification doesn't distinguish meta-methods vs domain-methods. (2) §7.5.1 core is domain-agnostic but its framing uses ai-coding concepts (CoALA, pyproject.toml, §7.4.4). (3) Partial elevation (§7.5.1 yes, §7.8.3 no) creates worse asymmetry — auditor still needs ai-coding methods for Check #4. (4) No evidence of practical failure from cross-references. (5) v3.9.1 already solved the ambiguity problem.
- **Consequences:** (+) No content duplication, no drift risk, (+) auditors have decision criterion inline for Check #1, (+) clear precedent for future cross-level references, (-) auditors must load ai-coding methods for full §7.5.1 procedure and Check #4 templates.
- **TITLE 8 gap identified:** Framework lacks explicit criteria for when cross-level method references warrant elevation vs. when they're appropriate as-is. Deferred — current cross-references are sufficient.
- **Review agents:** 4 exploration agents (source text, meta-methods structure, TITLE 8 rules), contrarian reviewer (PROCEED WITH CAUTION toward lightest-touch), validator (PASS 7/7 criteria).

### ADR-10: Platform-Native Memory as Pointer Only
- **Status:** Accepted (2026-02-07)
- **Context:** Claude Code's auto memory (`MEMORY.md`) duplicated facts from SESSION-STATE, PROJECT-MEMORY, and LEARNING-LOG, violating Single Source of Truth. Stale facts in auto memory anchored AI understanding before it read framework files.
- **Decision:** Auto memory contains only pointers to framework files. No duplicated facts. Formalized in Appendix G.5 of meta-methods.
- **Consequences:** (+) eliminates drift between two persistence layers, (+) auto memory stays small (12 lines vs 28), (-) AI must read framework files to get context (can't rely on auto memory alone).

---

## Metrics Registry

Systematic tracking of performance metrics. See also: ARCHITECTURE.md for test coverage.

### Retrieval Quality Thresholds

| Metric | Current | Threshold | Rationale |
|--------|---------|-----------|-----------|
| Method MRR | 0.698 | ≥ 0.60 | Primary method discovery signal |
| Principle MRR | 0.604 | ≥ 0.50 | Primary principle discovery signal |
| Method Recall@10 | 0.875 | ≥ 0.75 | Breadth of relevant results |
| Principle Recall@10 | 0.875 | ≥ 0.85 | Breadth of relevant results |
| Model Load Time | ~9s | ≤ 15s | User experience bound |

### When to Record New Baseline

- Embedding model changes
- Major index changes (new domain, significant rewrites)
- Retrieval algorithm changes
- Before releases

---

## Roadmap

### Future Considerations

- Prompt Engineering domain (when created, move system prompt best practices from multi-agent)
- Gateway-Based Enforcement (§4.6.2) — server-side governance for all platforms
- Vector DB migration (when scale requires)
- ~~Prompt Engineering consolidation~~ → Title 11 in ai-governance-methods (done)
- ~~RAG Optimization consolidation~~ → Title 12 in ai-governance-methods (done)

### Project Initialization — Part B (Bootstrap Gap)

Part A shipped (`150e4e6`): strengthened SERVER_INSTRUCTIONS with a dedicated "Project Initialization" section, conversational trigger, consent step, and partial-init handling. Advisory only — no enforcement.

Three approaches to close the gap further:

1. **`scaffold_project` tool** — New MCP tool that auto-creates governance memory files (SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md, project instructions file). AI calls the tool; files are created server-side. Requires adding filesystem write capability to the MCP server.
2. **Server-side first-run detection** — MCP server detects uninitialized projects (e.g., no governance files in working directory) and proactively triggers initialization protocol. Requires filesystem read access and a mechanism to signal the AI client.
3. **Wrapper/web app/IDE plugin** — Move beyond MCP for scaffolding. A web app, CLI wrapper, or IDE plugin (e.g., Augment-style) handles project setup outside the MCP protocol. Decouples initialization from AI session entirely.

**Status:** Deferred. Revisit after additional improvements ship.

---

## Subagent Justifications (§1.1)

Per multi-agent methods §1.1, each subagent must justify its overhead vs. generalist. The 15x rule applies: multi-agent token cost must produce proportional value.

| Agent | Justification Type | Evidence | Expected Benefit |
|-------|-------------------|----------|------------------|
| code-reviewer | Cognitive + Isolation | Fresh context prevents writer bias; LSP tool access distinct from generalist | Objective code quality assessment without implementation anchoring |
| contrarian-reviewer | Isolation + Cognitive | Fresh context critical for objectivity; distinct critical-challenging cognitive function | Surfaces blind spots and assumptions that author cannot see |
| validator | Isolation + Quality | Fresh context for criteria objectivity; artifact-agnostic (docs, configs, plans) | Systematic checklist validation without author's reasoning bias |
| security-auditor | Quality + Isolation | Security expertise requires focused attention; restricted to read-only tools | Catches vulnerabilities that generalist development context misses |
| documentation-writer | Cognitive | Distinct writing cognitive function; focuses on clarity for external audience | Documentation quality improves when writer isn't also the implementer |
| orchestrator | Context Limit | Complex multi-step tasks exceed single-agent context; coordinates other agents | Manages governance compliance across multi-agent workflows |
| test-generator | Cognitive + Quality | Test design benefits from fresh perspective on code behavior; distinct from implementation | Better edge case coverage when tester hasn't seen implementation reasoning |
| coherence-auditor | Isolation + Cognitive | Fresh context essential — drift is invisible to the author who caused it; distinct analytical function (cross-file consistency) vs. validator (criteria checking) | Catches stale facts, contradictions, and volatile metric drift that familiarity conceals |
| continuity-auditor | Isolation + Quality | Fresh context catches character drift, timeline conflicts, world rule violations that the author is blind to after extended familiarity; distinct function (narrative consistency) vs. coherence-auditor (documentation consistency) | Systematic Story Bible vs. manuscript verification that writer's internalized knowledge conceals |
| voice-coach | Cognitive + Isolation | Distinct analytical function — comparing dialogue against voice profiles, not creating dialogue; writer familiarity makes voice convergence invisible | Detects when characters sound identical, voice drifts from profiles, or AI default style overtakes distinctiveness |

**Decision:** All current subagents justified. No subagent exists without at least one justification from the §1.1 checklist (Context Limit, Parallelization, Cognitive Mismatch, Quality Improvement, Isolation Requirement).

**Review trigger:** Re-evaluate when adding new agents or when usage patterns show a subagent is rarely invoked.

## Patterns and Conventions

| Pattern | Description |
|---------|-------------|
| Communication Level | Default "Interview-ready"; deep dive on request |
| Principle IDs | `{domain}-{category}-{title-slug}` |
| Domain names | lowercase, hyphenated |
| Code Style | Python 3.10+, Pydantic, MCP Python SDK, type hints, logging to stderr |

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
| 16 | Version bumps need multiple files | `__init__.py`, `pyproject.toml`, `SBOM.md`, `SECURITY.md` must stay in sync |
| 17 | Operational changes need source docs | Skip-list/trigger changes must propagate to governance source documents, not just instruction surfaces |
| 18 | `domain_name[:4]` generates implicit prefixes | Codify new domain prefixes in explicit maps (extractor, retrieval, server) |
| 19 | `huggingface-hub>=1.0` drops `requests` | `sentence-transformers` still imports it. Explicit `requests>=2.28.0` in pyproject.toml. |
| 20 | Float32 score precision | Fused scores can exceed 1.0 by ~1e-7. Clamp with `min(score, 1.0)` before Pydantic validation. |
| 21 | Context engine RLock, not Lock | query_project acquires lock for read phase. RLock needed because get_or_create_index may be called inside lock. |
| 22 | Env vars crash on invalid values | All `AI_CONTEXT_ENGINE_*` env vars wrapped in try/except with fallback defaults. |
| 23 | CI needs context-engine extras | `pip install -e ".[dev,context-engine]"` — tests import `pathspec` from optional group |
| 24 | Storytelling A-Series category collision | Multi-agent A-Series = "Architecture", Storytelling A-Series = "Audience" — both map to category `architecture`. Safe because different domain prefixes (`mult-` vs `stor-`) and storytelling uses colon headers (old format). Watch for new domains with A-Series. |

### Resolved Gotchas

| # | Issue | Resolution |
|---|-------|------------|
| 14 | Method keywords title-only | ✓ Fixed — MethodMetadata + BGE model upgrade (2026-01-17) |

---

## References

- **Architecture:** ARCHITECTURE.md — system design, component responsibilities, file maps
- **Current State:** SESSION-STATE.md — working memory, next actions
- **Lessons:** LEARNING-LOG.md — episodic memory, graduated patterns
