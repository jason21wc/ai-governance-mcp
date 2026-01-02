# AI Governance MCP - Project Memory

## Project Identity

- **Name:** AI Governance MCP Server
- **Purpose:** Semantic retrieval MCP for domain-specific principles/methods — "second brain" for AI
- **Owner:** Jason
- **Status:** COMPLETE - All phases done, 271 tests, 90% coverage, 10 tools
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
| Implement → Complete | ✓ Passed | 2025-12-29 | 205 tests, 90% coverage, all features working |

## Architecture Summary

```
Build Time:  documents/*.md → extractor.py → index/ + embeddings.npy
Runtime:     Query → Domain Router → Hybrid Search → Reranker → Results
```

**Core Components:**
- `server.py` - FastMCP server with 10 tools
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
- **Date:** 2026-01-01
- **Status:** CONFIRMED
- **Problem:** MCP is now supported by multiple AI platforms (Gemini CLI, Claude, ChatGPT, others via SuperAssistant), but each requires different configuration format or CLI commands.
- **Solution:** Created `config_generator.py` module with:
  - CLI tool: `python -m ai_governance_mcp.config_generator --platform <name>`
  - Programmatic API: `generate_mcp_config(platform)` returns dict
  - Platforms: gemini, claude, chatgpt, superassistant
  - Options: `--all` (all platforms), `--json` (raw JSON output)
- **Implementation:**
  - New module: `src/ai_governance_mcp/config_generator.py`
  - 17 tests in `tests/test_config_generator.py`
  - README updated with Platform Configuration section
- **Verified:** Gemini CLI integration tested — `gemini mcp add` successful, server connected
- **Governance Gap:** Did NOT query governance before implementation (violated CLAUDE.md checkpoint)

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

### Decision: Phase 2 Governance Agent Architecture (Orchestrator-First)
- **Date:** 2026-01-02
- **Status:** COMPLETE (271 tests, 10 tools)
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

## Roadmap

### Planned Domains
| Domain | Status | Reference Documents |
|--------|--------|---------------------|
| Prompt Engineering | Planned | `documents/prompt-engineering-best-practices-guide-v3.md` |
| RAG Optimization | Planned | `documents/rag-document-optimization-best-practices-v3b.md`, `documents/AI-instructions-prompt-engineering-and-rag-optimization.md` |

*These reference documents will be converted to domain principles and methods files.*

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
| T12-T18 | Server + 10 MCP tools | Complete |
| T19-T22 | Tests (271 passing, 90% coverage) | Complete |
| T23 | Portfolio README | Complete |

### Test Coverage
| Module | Tests | Coverage |
|--------|-------|----------|
| models.py | 24 | 100% |
| config.py | 17 | 98% |
| server.py | 68 | 90% |
| extractor.py | 45 | 89% |
| retrieval.py | 55 | 84% |
| config_generator.py | 17 | 100% |
| server_integration.py | 12 | - |
| extractor_integration.py | 11 | - |
| retrieval_integration.py | 18 | - |
| **Total** | **271** | **90%** |

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
| src/ai_governance_mcp/models.py | Pydantic data structures | ~350 |
| src/ai_governance_mcp/config.py | Settings management | ~224 |
| src/ai_governance_mcp/extractor.py | Document parsing + embeddings | ~450 |
| src/ai_governance_mcp/retrieval.py | Hybrid search engine | ~500 |
| src/ai_governance_mcp/server.py | MCP server + 10 tools | ~1530 |
| src/ai_governance_mcp/config_generator.py | Multi-platform MCP configs | ~150 |

### Test Files
| File | Tests | Purpose |
|------|-------|---------|
| tests/conftest.py | - | Shared fixtures (mock_embedder, saved_index, etc.) |
| tests/test_models.py | 24 | Model validation, constraints, enums |
| tests/test_config.py | 17 | Settings, env vars, path handling |
| tests/test_server.py | 68 | All 10 tools, formatting, metrics, governance, agent installation |
| tests/test_server_integration.py | 12 | Dispatcher routing, end-to-end flows |
| tests/test_extractor.py | 35 | Parsing, embeddings, metadata, validation |
| tests/test_extractor_integration.py | 11 | Full pipeline, index persistence |
| tests/test_retrieval.py | 44 | Unit tests + edge cases |
| tests/test_retrieval_integration.py | 18 | Pipeline, utilities, performance |
| tests/test_config_generator.py | 17 | Platform configs, CLI commands |

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
