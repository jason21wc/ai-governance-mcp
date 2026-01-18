# AI Governance MCP - Project Memory

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Semantic retrieval MCP for domain-specific principles/methods — "second brain" for AI
- **Owner:** Jason
- **Status:** COMPLETE - All phases done, 345 tests, 90% coverage, 11 tools
- **Procedural Mode:** STANDARD
- **Quality Target:** Showcase/production-ready, public-facing tool
- **Portfolio Goal:** Showcase for recruiters, consulting customers, SME presentations
- **Repository:** github.com/jason21wc/ai-governance-mcp (private, future public)

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ✓ Passed | 2025-12-26 | PO validated requirements, chose Option C (Tier 1 + best of Tier 2) |
| Plan → Tasks | ✓ Passed | 2025-12-26 | Architecture approved, hybrid retrieval design confirmed |
| Tasks → Implement | ✓ Passed | 2025-12-27 | Task decomposition approved, 90+ test target set |
| Implement → Complete | ✓ Passed | 2025-12-29 | 345 tests, 90% coverage, all features working |

## Architecture Summary

```
Build Time:  documents/*.md → extractor.py → index/ + embeddings.npy
Runtime:     Query → Domain Router → Hybrid Search → Reranker → Results
```

**Core Components:**
- `server.py` - FastMCP server with 11 tools
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

### Decision: Governance Enforcement Paradigm (Phased Approach)
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Problem:** Per-response governance reminder was present but AI didn't actively query governance before tasks. Passive reminders necessary but insufficient.
- **Research:** 2025 industry patterns show three enforcement paradigms:
  1. **Passive** — Reminder in response, AI chooses to act (current, insufficient alone)
  2. **Interceptive** — Separate layer evaluates actions before execution (GaaS, Safety Agent)
  3. **Proactive** — System injects relevant principles automatically
- **Choice:** Phased implementation:
  | Phase | Approach | When |
  |-------|----------|------|
  | 1 | Enhanced passive + explicit checkpoints | Now |
  | 2 | Governance Agent (interceptive) | With multi-agent build |
- **Phase 1 Implementation:**
  - Enhanced GOVERNANCE_REMINDER with specific action triggers
  - Explicit checkpoints in CLAUDE.md for mandatory query points
- **Phase 2 Design:** Governance Agent as specialized agent in multi-agent architecture
  - Pre-action check: Query principles before execution agents act
  - Inject context: Pass applicable principles to execution agents
  - Post-action audit: Verify outputs align with governance
- **Sources:** [GaaS Framework](https://arxiv.org/html/2508.18765v2), [Superagent Safety Agent](https://www.helpnetsecurity.com/2025/12/29/superagent-framework-guardrails-agentic-ai/)
- **Principles Applied:** meta-quality-structured-output-enforcement, meta-quality-verification-mechanisms-before-action

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

### Decision: Confidence Thresholds Validated (Keep Defaults)
- **Date:** 2025-12-31
- **Status:** CONFIRMED
- **Context:** External review suggested "LOW confidence might be too conservative"
- **Analysis Conducted:**
  - Tested 5 diverse queries (specs, security, multi-agent, context, testing)
  - Verified score distributions across constitution and domain principles
  - Checked what falls below 0.3 threshold (potential misses)
- **Findings:**
  | Threshold | Value | Observation |
  |-----------|-------|-------------|
  | HIGH | ≥0.7 | Correctly identifies highly relevant matches (reranked scores) |
  | MEDIUM | ≥0.4 | Captures useful context appropriately |
  | LOW/min | ≥0.3 | Some edge cases (e.g., "Risk Mitigation" at 0.29 for security query) but lowering would increase noise |
- **Decision:** Keep current thresholds unchanged
- **Rationale (80/20):** ~95% of queries work well; the ~5% edge cases don't justify adding noise to all results. Reranker correctly boosts truly relevant results above thresholds.

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

### Decision: Multi-Agent Domain v2.0.0 Scope Expansion
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** v1.x assumed "multi-agent" = parallel coordination only; missed individual specialized agents and sequential composition
- **Research:** Anthropic, Google ADK, Cognition, LangChain, Microsoft, Vellum (2025 patterns)
- **Key Insight:** Many benefits of "multi-agent" can be achieved with sequential single-agent workflows. The critical factor is *specialization*, not *parallelization*.
- **Scope Now Covers:**
  1. Individual specialized agents (single agent, focused cognitive function)
  2. Sequential agent composition (agents in sequence, output feeds next)
  3. Parallel multi-agent coordination (multiple agents simultaneously)
  4. Hybrid patterns
- **Version:** v1.3.0 → v2.0.0 (BREAKING — scope, new principles, agent definition standard)
- **Sources:** [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system), [Cognition "Don't Build Multi-Agents"](https://cognition.ai/blog/dont-build-multi-agents)

### Decision: Agent Definition Standard Adopted
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** Agents were defined ad-hoc without consistent structure
- **Choice:** Standardize agent definitions with required components:
  | Component | Required | Purpose |
  |-----------|----------|---------|
  | name | Yes | Unique identifier |
  | description | Yes | Auto-selection trigger |
  | cognitive_function | Yes | Mental model type |
  | tools | Yes | Permissions |
  | System Prompt | Yes | Structured: Who I Am, Who I Am NOT, Output Format |
- **Key Concept — Modular Personalities:** An agent is a specialized *configuration* of the same underlying model, not a separate program. Think of it as a "hat" the AI wears.
- **Sources:** [Anthropic Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-code/agents-sdk), [NetworkChuck AI-in-Terminal](https://github.com/theNetworkChuck/ai-in-the-terminal)

### Decision: Justified Complexity Principle Added
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** No guidance on when to use agents vs generalist
- **The 15x Rule:** Multi-agent workflows typically consume 15x the tokens. Must justify.
- **Justification Required:** Context window limits, parallelization opportunity, cognitive function mismatch, quality improvement, or isolation requirement
- **Constitutional Basis:** meta-operational-resource-efficiency-waste-reduction, meta-core-discovery-before-commitment
- **Sources:** [Cognition 15x Finding](https://cognition.ai/blog/dont-build-multi-agents), [LangChain When to Build Multi-Agent](https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/)

### Decision: Context Engineering Discipline Principle Added
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** No explicit guidance on context management across agent boundaries
- **Key Insight:** "A focused 300-token context often outperforms an unfocused 113,000-token context."
- **Four Strategies:** Write (store externally), Select (retrieve relevant), Compress (summarize at boundaries), Isolate (scope per agent)
- **Constitutional Basis:** meta-core-context-engineering, meta-operational-minimal-relevant-context
- **Sources:** [Vellum Multi-Agent Context Engineering](https://www.vellum.ai/blog/multi-agent-systems-building-with-context-engineering), [Google ADK](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)

### Decision: Read-Write Division Principle Added
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** No guidance on what operations can safely parallelize
- **Key Insight:** "Actions carry implicit decisions. Conflicting decisions carried by conflicting actions carry bad results."
- **Rule:** Parallelize read-heavy operations (research, analysis). Serialize write-heavy operations (synthesis, decisions) to single agent.
- **Constitutional Basis:** meta-multi-role-specialization-topology, meta-multi-standardized-collaboration-protocols
- **Sources:** [Cognition](https://cognition.ai/blog/dont-build-multi-agents), [LangChain](https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/)

### Decision: Shared Assumptions Protocol Added
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** Parallel agents could make conflicting implicit decisions
- **Solution:** Before parallel execution, establish Shared Assumptions Document covering: Intent, Decisions Already Made, Conventions, Boundaries Between Agents, Conflict Resolution
- **Extends:** Intent Propagation (A4) → full assumptions protocol
- **Sources:** [Cognition "conflicting assumptions" research](https://cognition.ai/blog/dont-build-multi-agents)

### Decision: Linear-First Orchestration Default
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** No clear default when orchestration pattern is unclear
- **Rule:** Sequential is the safe default. Parallel requires explicit validation: confirmed independence + shared assumptions + read-write analysis
- **Rationale:** Parallel introduces coordination complexity; only justified when validated
- **Sources:** [Cognition](https://cognition.ai/blog/dont-build-multi-agents), Industry consensus on "start simple"

### Decision: Agent Catalog with 6 Core Patterns
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** Agents created ad-hoc without reusable templates
- **Catalog:**
  | Agent | Cognitive Function | Purpose |
  |-------|-------------------|---------|
  | Orchestrator | Strategic | Coordinate, delegate, never execute domain work |
  | Specialist | Domain-specific | Execute domain tasks (parameterized) |
  | Validator | Analytical | Review outputs against explicit criteria |
  | Contrarian Reviewer | Critical | Challenge assumptions, surface blind spots |
  | Session Closer | Operational | State persistence, context sync |
  | Governance Agent | Evaluative | Assess compliance with principles |
- **Each includes:** Full agent definition template with system prompt structure

### Decision: Governance Agent Implementation (evaluate_governance Tool)
- **Date:** 2026-01-01
- **Status:** IMPLEMENTED
- **Problem:** Need active governance enforcement, not just passive reminders
- **Solution:** `evaluate_governance` tool implementing Governance Agent pattern (§4.3)
- **Governance Applied:**
  - `multi-method-governance-agent-pattern` — Pre-action compliance check
  - `multi-method-agent-definition-standard` — Agent components
  - `meta-quality-verification-mechanisms-before-action` — Validate before acting
- **Implementation:**
  - Tool: `evaluate_governance(planned_action, context?, concerns?)`
  - Output: `GovernanceAssessment` with assessment, confidence, compliance_evaluation, s_series_check
  - S-Series: Dual-path detection (principle codes + keyword scanning)
  - Assessment statuses: PROCEED, PROCEED_WITH_MODIFICATIONS, ESCALATE
  - S-Series triggers force ESCALATE (veto authority)
- **Tests Added:** 5 new tests, 225 total tests passing

### Decision: MCP Instruction Optimization v2 (Constraint-Based + Model-Specific)
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** Previous SERVER_INSTRUCTIONS were passive ("When to Use") — AI received instructions but didn't follow them. Self-assessment confirmed AI ignored reminders in practice.
- **Governance Applied:**
  - `meta-operational-constraint-based-prompting` — explicit constraints reduce ambiguity
  - `meta-method-instructions-content` — required sections for MCP instructions
- **Changes:**
  | Aspect | Before | After |
  |--------|--------|-------|
  | Action framing | "When to Use" (suggestive) | "Required Actions" (mandatory) |
  | Constraints | Implicit | "Forbidden Actions" section |
  | Model coverage | None | 5 frontier model families |
  | Reminder style | Statement | Self-check question ("Did you...?") |
  | Instructions tokens | ~200 | ~380 |
  | Reminder tokens | ~40 | ~35 |
- **Model-Specific Guidance Added:**
  - Claude: Extended thinking for governance analysis
  - GPT-4/o1: Sandwich method — verify before finalizing
  - Gemini: Hierarchical headers for citations
  - Llama/Mistral: Repeat S-Series at decision points
- **Test Updates:** Separator changed `📋` → `⚖️` in `extract_json_from_response()` helper
- **Rationale:** System instructions are behavioral contracts, not just documentation. Questions trigger reflection better than statements.

### Decision: Multi-Platform MCP Configuration Generator
- **Date:** 2026-01-01 (updated 2026-01-03)
- **Status:** CONFIRMED
- **Problem:** MCP is now supported by multiple AI platforms (Gemini CLI, Claude, ChatGPT, Cursor, Windsurf, others via SuperAssistant), but each requires different configuration format or CLI commands.
- **Solution:** Created `config_generator.py` module with:
  - CLI tool: `python -m ai_governance_mcp.config_generator --platform <name>`
  - Programmatic API: `generate_mcp_config(platform)` returns dict
  - Platforms: gemini, claude, chatgpt, cursor, windsurf, superassistant (6 total)
  - Options: `--all` (all platforms), `--json` (raw JSON output)
- **Implementation:**
  - New module: `src/ai_governance_mcp/config_generator.py`
  - 17 tests in `tests/test_config_generator.py`
  - README updated with Platform Configuration section
- **Verified:** Gemini CLI integration tested — `gemini mcp add` successful, server connected
- **Update 2026-01-03:** Added Cursor and Windsurf native MCP support (both now support MCP natively)

### Decision: Docker Containerization for Distribution
- **Date:** 2026-01-03
- **Status:** CONFIRMED
- **Problem:** Local pip installation requires Python environment setup; users want simpler deployment
- **Solution:** Docker multi-stage build with automated Docker Hub publishing
- **Architecture:**
  | Stage | Purpose |
  |-------|---------|
  | Builder | Install deps, gcc, build index, generate embeddings |
  | Runtime | Minimal image with pre-built index, non-root user, health check |
- **Key Decisions:**
  - CPU-only PyTorch (avoids 2GB+ CUDA dependencies)
  - Non-root user (appuser) for security
  - Pre-built index copied from builder stage
  - GitHub Actions workflow publishes on version tags
- **Implementation:**
  - `Dockerfile` — Multi-stage build
  - `docker-compose.yml` — Local testing
  - `.dockerignore` — Excludes tests, dev files
  - `.github/workflows/docker-publish.yml` — Automated publishing
- **Image:** ~1.6GB, 268 documents pre-indexed
- **Distribution:** Docker Hub (`jason21wc/ai-governance-mcp`) + Dockerfile in repo

### Decision: Docker AMD64-Only Build (ARM64 Removed)
- **Date:** 2026-01-18
- **Status:** CONFIRMED
- **Problem:** GitHub Actions Docker build for ARM64 timed out after 6+ hours
- **Root Cause:** GitHub's runners are x86_64. Building ARM64 requires QEMU emulation, which makes embedding generation ~500x slower:
  | Environment | Batch Time | Total (13 batches) |
  |-------------|------------|-------------------|
  | Native x86_64 | ~2 min | ~26 min |
  | QEMU ARM64 emulation | ~1.5 hours | ~19 hours |
- **Key Finding:** MKL-DNN (Intel's math library used by PyTorch) cannot detect ARM features under QEMU, falling back to unoptimized code paths
- **Solution:** Remove ARM64 from Docker build platforms (AMD64 only)
- **Apple Silicon Impact:** Minimal — Rosetta 2 emulation runs AMD64 containers efficiently
- **Alternative Considered:** Self-hosted ARM64 runner — rejected (complexity, cost)
- **Recommendation for Future Projects:**
  1. Test multi-arch builds with computationally intensive workloads early
  2. For ML models with embeddings: avoid QEMU emulation, use native runners
  3. AMD64-only is acceptable when emulation provides adequate fallback
- **Implementation:** `.github/workflows/docker-publish.yml` updated to `platforms: linux/amd64`

### Decision: Phase 2B LLM-Agnostic Agent Installation Architecture
- **Date:** 2026-01-02
- **Status:** IMPLEMENTED
- **Problem:** How to install Orchestrator/Governance agents across platforms (Claude, Gemini, ChatGPT, etc.)
- **Research Finding:** Only Claude Code has local agent files (`.claude/agents/`). Other platforms (Gemini CLI, ChatGPT Desktop, Grok, Perplexity) have no equivalent — they only receive SERVER_INSTRUCTIONS.
- **Solution — Hybrid with Platform Detection:**
  ```
  User calls: install_agent("orchestrator")
                     ↓
  Tool detects platform: _detect_claude_code_environment()
                     ↓
  Claude Code → Preview → User confirms → Write file
  Non-Claude  → Return "not_applicable" (governance via SERVER_INSTRUCTIONS)
  ```
- **Platform Matrix (Verified 2026-01):**
  | Platform | Agent Files? | What We Provide |
  |----------|--------------|-----------------|
  | Claude Code | ✅ `.claude/agents/` | install_agent tool writes files |
  | Codex CLI | ❌ (`AGENTS.md` = project instructions) | SERVER_INSTRUCTIONS only |
  | Gemini CLI | ❌ (`GEMINI.md` = instructions) | SERVER_INSTRUCTIONS only |
  | ChatGPT Desktop | ❌ Built-in agent mode | SERVER_INSTRUCTIONS only |
  | Grok/Perplexity | ❌ Cloud-based | SERVER_INSTRUCTIONS only |
- **Key Insight:** MCP is the LLM-agnostic layer. Agent definitions exposed via:
  1. SERVER_INSTRUCTIONS (inline Orchestrator protocol) — all platforms
  2. `install_agent` / `uninstall_agent` tools — Claude Code only
- **Implementation Details:**
  - `_detect_claude_code_environment()` — checks for `.claude/` dir or `CLAUDE.md` file
  - Agent template: `documents/agents/orchestrator.md` with YAML frontmatter
  - Confirmation flow: preview → (install | manual | cancel)
  - Robust user explanation via `AGENT_EXPLANATION` constant
- **Enforcement Levels:**
  | Level | Mechanism | Strength | Platform Coverage |
  |-------|-----------|----------|-------------------|
  | Tool Restrictions | YAML frontmatter | HARD | Claude Code only |
  | Behavioral Instructions | SERVER_INSTRUCTIONS | SOFT | All platforms |
  | Per-Response Reminders | Appended to responses | SOFT | All platforms |
- **Documentation:** multi-agent-methods-v2.1.0.md Appendix F: Cross-Platform Agent Support

### Decision: Hybrid Assessment for AI Judgment Layer (§4.6.1)
- **Date:** 2026-01-02
- **Status:** IMPLEMENTED (279 tests)
- **Problem:** evaluate_governance returns binary PROCEED/ESCALATE. PROCEED_WITH_MODIFICATIONS never triggers because script can't reason about principle conflicts.
- **Research Finding:** Scripts excel at deterministic tasks (safety keywords). AIs excel at reasoning about nuance (principle conflicts, modification generation).
- **Solution — Hybrid Responsibility Layers:**
  | Layer | Responsibility | Why This Layer |
  |-------|---------------|----------------|
  | Script | S-Series keyword detection | Deterministic, non-negotiable safety |
  | Script | Principle retrieval + ranking | Fast, consistent semantic search |
  | Script | Structured data output | Reliable format for AI consumption |
  | AI | Principle conflict analysis | Requires reasoning about context |
  | AI | Modification generation | Context-aware recommendations |
  | AI | Final assessment (PROCEED/MODIFY) | Nuanced judgment call |
- **Key Principle:** "Don't try to script nuanced judgment. Don't let AI override safety guardrails."
- **Implementation:**
  - Added `content`, `series_code`, `domain` to RelevantPrinciple model
  - Added `requires_ai_judgment`, `ai_judgment_guidance` to GovernanceAssessment model
  - Added `suggested_modification` to ComplianceEvaluation model
  - When no S-Series trigger: `requires_ai_judgment=true`, AI reads principle content
  - Added AI Judgment Protocol section to SERVER_INSTRUCTIONS
- **Governance Applied:**
  - `meta-governance-technical-focus-with-clear-escalation-boundaries` — Clear AI vs script boundaries
  - `meta-multi-hybrid-interaction-raci` — RACI between script and AI layers
  - `meta-quality-structured-output-enforcement` — Structured data for AI consumption
- **Tests Added:** 8 new tests (279 total)

### Decision: Phase 2 Governance Agent Architecture (Orchestrator-First)
- **Date:** 2026-01-02
- **Status:** COMPLETE (279 tests, 10 tools)
- **Problem:** Phase 1 `evaluate_governance` tool is voluntary — AI can ignore it. Evidence: implemented config_generator without governance check despite CLAUDE.md checkpoints.
- **Solution:** Orchestrator-First Architecture — make governance structural, not optional
- **Key Design:**
  ```
  User Request → Orchestrator Agent (default persona) → evaluate_governance()
                     ↓
     PROCEED → Delegate    |    MODS → Apply, delegate    |    ESCALATE → HALT
  ```
- **Enforcement Layers:**
  1. **Default Persona** — Orchestrator loads automatically, only has delegation tools
  2. **Governance Tool** — evaluate_governance returns binding assessment with audit_id
  3. **Post-Action Audit** — verify_governance_compliance catches bypasses
  4. **Per-Response Reminder** — Existing GOVERNANCE_REMINDER for self-correction
- **Bypass Authorization (Narrow):**
  - Pure read operations only
  - User explicitly authorizes with documented reason
  - Trivial formatting-only changes
- **Implementation Phases:**
  | Phase | Scope |
  |-------|-------|
  | 2-Pre | Documentation (PROJECT-MEMORY, methods v2.1.0) |
  | 2A | Audit infrastructure (audit_id, logging, verify tool) |
  | 2B | Agent definitions (.claude/agents/, CLAUDE.md update) |
  | 2C | Testing (PROCEED/MODS/ESCALATE paths) |
  | 2D | Final documentation |
- **Governance Applied:**
  - `multi-architecture-orchestrator-separation-pattern` — Orchestrator delegates, doesn't execute
  - `multi-architecture-cognitive-function-specialization` — One function per agent
  - `multi-reliability-explicit-handoff-protocol` — Structured handoffs with governance context
  - `multi-method-governance-agent-pattern` — Pre-action compliance check
- **Success Criteria:**
  - [ ] All significant actions pass through governance check
  - [ ] ESCALATE actually blocks execution
  - [ ] Audit trail captures all assessments
  - [ ] Bypasses are logged and detectable

### Decision: Governance Reasoning Externalization
- **Date:** 2026-01-10
- **Status:** IMPLEMENTED (335 tests, 11 tools)
- **Problem:** Governance compliance was a "black box" — AI evaluated principles but reasoning wasn't visible or auditable
- **Research:** Sequential Thinking MCP, Thinking Tool MCP, ThoughtMCP, industry observability patterns
- **Key Insight:** Externalized reasoning adds visibility without enforcement. The trace is for auditability, not compliance enforcement.
- **Solution — 3 Components:**
  | Component | Type | Purpose |
  |-----------|------|---------|
  | `log_governance_reasoning` tool | Tool | Record per-principle reasoning traces linked via audit_id |
  | `reasoning_guidance` field | Model field | Prompt AI to use Governance Reasoning Protocol |
  | Governance Reasoning Protocol | SERVER_INSTRUCTIONS | Structured format for principle analysis |
- **Implementation:**
  - New models: `ReasoningEntry`, `GovernanceReasoningLog`
  - New field: `reasoning_guidance` on `GovernanceAssessment`
  - Tool validates audit_id against existing audit log
  - Logs to `governance_reasoning.jsonl` alongside existing audit trail
- **Governance Applied:**
  - `meta-quality-verification-mechanisms-before-action` — Pre-action compliance check pattern
  - `meta-operational-continuous-learning` — Learning from industry research
  - `coding-quality-security-first-development` — Input validation, sanitization

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

### Decision: Multi-Agent Methods v2.5.0 Production Operations Expansion
- **Date:** 2026-01-05
- **Status:** CONFIRMED
- **Context:** Analyzed Google Cloud "Startup Technical Guide: AI Agents" (2025) against existing multi-agent framework. Validated findings with 2025-2026 industry research.
- **Key Finding:** Framework is well-designed and industry-aligned. Gaps were procedural (Methods) not architectural (Principles).
- **New Sections Added:**
  | Section | Purpose | Source |
  |---------|---------|--------|
  | §3.4.1 Memory Distillation | LLM-based compression for long sessions (80-95% reduction) | AWS AgentCore, Mem0, Google Titans |
  | §3.7.1 Production Observability | OpenTelemetry, session replay, alerting thresholds | IBM AgentOps, AgentOps.ai |
  | §3.8 ReAct Loop Configuration | Reason→Act→Observe controls, termination, runaway detection | IBM, AG2, Prompting Guide |
  | §4.7 Agent Evaluation Framework | 4-layer: Component/Trajectory/Outcome/System | Google Vertex AI, Confident AI, orq.ai |
  | §4.8 Production Safety Guardrails | Multi-layer defense, prompt injection, PII, RBAC | Dextra Labs, Superagent, OWASP 2025 |
  | Appendix D (Principles) | A2A Protocol Awareness (emerging, Linux Foundation) | Google A2A, Linux Foundation |
- **Governance Applied:**
  - `meta-operational-continuous-learning` — Learning from industry research
  - `meta-governance-risk-mitigation-by-design` — Safety Guardrails section
  - `meta-multi-synchronization-observability` — AgentOps patterns
- **Research URLs:** See MULTI-AGENT-ENHANCEMENT-REPORT.md for full source list
- **Impact:** Index updated (69 principles + 230 methods = 299 total items)

### Decision: Subagent Prompt Content Belongs in Prompt Domain
- **Date:** 2026-01-04
- **Status:** CONFIRMED (Future Implementation)
- **Context:** Subagent definition files (`.claude/agents/*.md`) combine:
  1. Platform mechanics (YAML frontmatter: name, tools, model)
  2. Prompt engineering (system prompt in markdown body)
- **Analysis:**
  | Content Type | Better Home | Rationale |
  |--------------|-------------|-----------|
  | System prompt structure, framing techniques, sandwich method, examples | **Prompt domain** | Applies to ALL prompts (subagents, CLAUDE.md, custom GPTs, etc.) |
  | YAML frontmatter specification | **Multi-agent** | Platform-specific (Claude Code) |
  | Tool scoping decisions | **Multi-agent** | Orchestration concern |
  | Subagent validation checklist | **Multi-agent** | Includes agent-to-agent integration testing |
- **Decision:** When Prompt Engineering domain is created:
  1. Move general prompt best practices (§2.1.1 content) to Prompt Methods
  2. Multi-agent §2.1.1 becomes reference: "For system prompt best practices, see Prompt Methods §X"
  3. Keep platform-specific content (YAML, tool scoping, validation) in Multi-agent
- **Rationale:** One source of truth for prompt engineering, referenced where needed. Follows governance framework's own anti-duplication principle.
- **Current State:** Prompt best practices remain in multi-agent-methods-v2.4.0.md until Prompt domain is created

### Decision: Gateway-Based Enforcement Pattern Documented
- **Date:** 2026-01-03
- **Status:** CONFIRMED
- **Problem:** Claude Code subagent pattern (`.claude/agents/`) is unique to Claude; OpenAI, Gemini, and other platforms lack parallel agent architecture for governance enforcement
- **Research:** MCP Gateway patterns are the platform-agnostic solution — Lasso MCP Gateway, Envoy AI Gateway, IBM ContextForge, Microsoft Windows 11 proxy pattern
- **Choice:** Document §4.6.2 Gateway-Based Enforcement in multi-agent-methods; add Governance Proxy Mode to roadmap for future implementation
- **Key Insight:** "Architecture beats hope" — server-side enforcement via gateway/proxy works across all platforms, unlike instruction-based approaches
- **Implementation Strategy:**
  | Approach | Enforcement | Platform |
  |----------|-------------|----------|
  | Subagent (§4.6) | Client-managed | Claude Code only |
  | Gateway (§4.6.2) | Server-managed | Any MCP client |
  | Instructions | Hope-based fallback | All platforms |
- **Future Work:** Governance Proxy Mode — wrap other MCP servers with governance checks before forwarding requests
- **Sources:** [Lasso MCP Gateway](https://lasso.security), [Envoy AI Gateway](https://aigateway.envoyproxy.io), [MCP Security Survival Guide](https://towardsdatascience.com)

### Decision: Security Hardening Implementation (Phase 1 & 2)
- **Date:** 2026-01-03 (Phase 1), 2026-01-04 (Phase 2)
- **Status:** COMPLETE
- **Context:** Comprehensive security review via Gemini sub-agent identified vulnerabilities in server.py

**Phase 1 - Critical & High Priority:**
  | ID | Issue | Fix | Principle |
  |----|-------|-----|-----------|
  | C1 | Unbounded audit log | `deque(maxlen=1000)` | Resource exhaustion prevention |
  | C2 | Path traversal risk | `.resolve()` + containment check | Input validation |
  | H1 | No query length limits | `MAX_QUERY_LENGTH = 10000` | DoS prevention |
  | H2 | Sync file I/O in async | `asyncio.to_thread()` | Non-blocking I/O |
  | H3 | Force exit loses data | `_flush_all_logs()` + `os.fsync()` | Data integrity |

**Phase 2 - High & Medium Priority:**
  | ID | Issue | Fix | File |
  |----|-------|-----|------|
  | H4 | No rate limiting | Token bucket (100 tokens, 10/sec) | server.py |
  | H5 | No dependency lock | `requirements.lock` | project root |
  | M1 | Unsanitized logging | Truncate to MAX_LOG_CONTENT_LENGTH | server.py |
  | M2 | Unstructured logs | `JSONFormatter` class | config.py |
  | M3 | No log rotation | `RotatingFileHandler` | config.py |
  | M4 | Secrets in logs | Regex redaction patterns | server.py |
  | M5 | Weak input validation | maxLength/minLength/enum in schemas | server.py |
  | M6 | Path leaks in errors | `_sanitize_error_message()` | server.py |
  | M7 | (Already in CI) | pip-audit, bandit, safety | ci.yml |

- **Governance Applied:** `coding-quality-security-first-development`, OWASP principles
- **Tests:** 290 passing (11 new security tests added)

### Decision: Pause Automatic Governance Enforcement Implementation
- **Date:** 2026-01-03
- **Status:** PAUSED
- **Goal:** Make AI compliance with governance automatic (AI can't skip `evaluate_governance`)
- **Research Summary:**
  | Approach | Can Enforce? | Limitation |
  |----------|--------------|------------|
  | Claude Hooks (`PreToolUse`) | Partial | Can block tools, cannot force orchestrator routing |
  | Claude Hooks (`UserPromptSubmit`) | No | Can block prompts, cannot modify or reroute |
  | MCP Proxy/Gateway | Tool-level | Gates tool calls, not reasoning patterns |
  | LangChain Middleware | Full | Requires separate wrapper app, not MCP enhancement |
  | MCP Resources | Depends | Inconsistent client auto-loading support |
- **Key Finding:** True automatic enforcement requires architectural control outside the MCP — either a wrapper app (LangChain/LiteLLM) or waiting for MCP clients to mature
- **Decision:** Pause implementation. Current instruction-based approach (SERVER_INSTRUCTIONS + reminders) is sufficient for now. Revisit when:
  - MCP clients add better resource auto-loading
  - Building a LangChain wrapper app becomes a priority
  - Claude Code hooks gain prompt modification capability
- **See Also:** LEARNING-LOG 2026-01-03 for detailed research findings

### Decision: Embedding Model Upgrade (BGE-small-en-v1.5)
- **Date:** 2026-01-17
- **Status:** CONFIRMED
- **Change:** `all-MiniLM-L6-v2` → `BAAI/bge-small-en-v1.5`
- **Rationale:**
  | Spec | Old Model | New Model |
  |------|-----------|-----------|
  | Max tokens | 256 | **512** |
  | Dimensions | 384 | 384 (unchanged) |
  | Quality | Good | Better (BGE family) |
- **Trigger:** Method retrieval quality investigation revealed content truncation
- **Impact:** Combined with MethodMetadata and text limit increases:
  - Method MRR: +112%
  - Method Recall@10: +76%
- **Breaking Change:** Existing indexes must be rebuilt (`python -m ai_governance_mcp.extractor`)
- **See Also:** Gotcha 14 (now resolved), SESSION-STATE.md

## Roadmap

### Completed Consolidations
| Topic | Status | Location | Archived From |
|-------|--------|----------|---------------|
| Prompt Engineering | ✅ Complete | Title 11 in `ai-governance-methods-v3.6.0.md` | `prompt-engineering-best-practices-guide-v3.md` |
| RAG Optimization | ✅ Complete | Title 12 in `ai-governance-methods-v3.6.0.md` | `rag-document-optimization-best-practices-v3b.md`, `AI-instructions-prompt-engineering-and-rag-optimization.md` |

*These were consolidated as techniques (methods), not separate domains. Underlying principles already existed in Constitution.*

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

**All phases complete:** Specify → Plan → Tasks → Implement → Test (345 tests, 90% coverage)

*Gate tracking is inline in Phase Gates table above. Task breakdown (T1-T23) archived — all 23 tasks complete.*

### Test Coverage
| Module | Tests | Coverage |
|--------|-------|----------|
| models.py | 49 | 100% |
| config.py | 17 | 98% |
| server.py | 103 | 90% |
| extractor.py | 45 | 89% |
| retrieval.py | 46 | 84% |
| config_generator.py | 17 | 100% |
| validator.py | 15 | 100% |
| server_integration.py | 11 | - |
| extractor_integration.py | 11 | - |
| retrieval_integration.py | 23 | - |
| retrieval_quality.py | 8 | - |
| **Total** | **345** | **90%** |

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
| ARCHITECTURE.md | System architecture | Active |
| SESSION-STATE.md | Current position | Active |
| PROJECT-MEMORY.md | This file | Active |
| LEARNING-LOG.md | Lessons learned | Active |
| CLAUDE.md | AI session loader | Active |
| README.md | Portfolio showcase | Active |

### Source Code
| File | Purpose | Lines |
|------|---------|-------|
| src/ai_governance_mcp/models.py | Pydantic data structures | ~350 |
| src/ai_governance_mcp/config.py | Settings management | ~224 |
| src/ai_governance_mcp/extractor.py | Document parsing + embeddings | ~450 |
| src/ai_governance_mcp/retrieval.py | Hybrid search engine | ~500 |
| src/ai_governance_mcp/server.py | MCP server + 11 tools | ~1900 |
| src/ai_governance_mcp/config_generator.py | Multi-platform MCP configs | ~150 |
| src/ai_governance_mcp/validator.py | Principle ID validation | ~350 |

### Test Files
| File | Tests | Purpose |
|------|-------|---------|
| tests/conftest.py | - | Shared fixtures (mock_embedder, saved_index, etc.) |
| tests/test_models.py | 49 | Model validation, constraints, enums |
| tests/test_config.py | 17 | Settings, env vars, path handling |
| tests/test_server.py | 103 | All 11 tools, formatting, metrics, governance, agent installation |
| tests/test_server_integration.py | 11 | Dispatcher routing, end-to-end flows |
| tests/test_extractor.py | 45 | Parsing, embeddings, metadata, validation |
| tests/test_extractor_integration.py | 11 | Full pipeline, index persistence |
| tests/test_retrieval.py | 36 | Unit tests + edge cases |
| tests/test_retrieval_integration.py | 21 | Pipeline, utilities, performance |
| tests/test_config_generator.py | 17 | Platform configs, CLI commands |
| tests/test_validator.py | 15 | Principle ID validation, fuzzy matching |

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

### Gotcha 12: evaluate_governance False Positives on Security-Related Actions
When implementing security *fixes*, `evaluate_governance()` may return ESCALATE due to keyword matching on terms like "security", "delete", "production". This is a false positive when the action is implementing improvements, not introducing risks.

**Resolution:** Check the `principles` array in the response. If empty or all show `status: "COMPLIANT"`, the ESCALATE is a keyword false positive and can be overridden. The action (implementing security fixes) aligns with principles like `coding-quality-security-first-development`.

**Pattern:** Security fixes align with governance — implementing them is exactly what the principles recommend.

### Gotcha 11: domains.json File References Must Match Actual Filenames
When updating governance document versions (e.g., `ai-coding-methods-v1.1.1.md` → `ai-coding-methods-v2.0.0.md`), you MUST update `documents/domains.json` to reference the new filename.

**Symptom:** Extractor shows "0 methods" for a domain that should have methods.

**Fix:** Update `domains.json` to reference correct filename, then rebuild index.

**Prevention:** Extractor now validates all file references at startup and fails fast with actionable error message listing ALL missing files.

### Gotcha 13: Index Architecture — JSON + NumPy Separation
The index stores metadata and embeddings separately:
- `global_index.json` — Contains `embedding_id` (integer index), NOT embedding vectors
- `content_embeddings.npy` — Contains actual vectors (406 × 384 dimensions)
- `domain_embeddings.npy` — Contains domain routing vectors

**Symptom:** Checking JSON for `embedding` field returns nothing. Assuming embeddings missing.

**Reality:** Embeddings ARE there, in `.npy` files. JSON only stores references.

**Verification:** See LEARNING-LOG "Index Architecture and Verification Pattern" for commands.

### Gotcha 14: Method Keywords Are Title-Only (Quality Issue) ✓ RESOLVED

**Problem:** Methods had poor semantic retrieval quality (0.28 similarity vs 0.46+ for principles).

**Root Causes:**
1. `all-MiniLM-L6-v2` has 256 token max — method content truncated
2. Method embedding text was only `title + content[:500]`
3. No metadata extraction for methods (unlike principles)

**Resolution (2026-01-17):**
1. Upgraded embedding model to `BAAI/bge-small-en-v1.5` (512 tokens)
2. Added `MethodMetadata` model with keywords, trigger_phrases, purpose_keywords, applies_to, guideline_keywords
3. Increased embedding text limit to 1500 chars
4. Enhanced BM25 to include method metadata

**Results:**
- Method MRR: 0.34 → **0.72** (+112%)
- Method Recall@10: 0.50 → **0.88** (+76%)

**See:** SESSION-STATE.md "Method Retrieval Quality Improvement"
