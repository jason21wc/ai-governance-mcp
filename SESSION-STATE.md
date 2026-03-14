# Session State

**Last Updated:** 2026-03-13
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Implement
- **Mode:** Standard
- **Active Task:** Coherence Review and Repair

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v1.2.1** (watcher auto-start on boot fix) |
| Content | **v2.5.0** (Constitution), **v3.13.0** (meta-methods), **v2.20.0** (ai-coding methods), **v2.3.4** (ai-coding principles), **v2.3.0** (multi-agent principles), **v2.14.0** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v2.1.0** (multimodal-rag principles), **v2.1.1** (multimodal-rag methods), **v1.0.0** (ui-ux principles), **v1.0.0** (ui-ux methods), **v2.5** (ai-instructions) |
| Tests | Run `pytest tests/ -v` for current count |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **15 MCP tools** (11 governance + 4 context engine) |
| Domains | **6** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux) |
| Index | **149 principles + 572 methods** (721 total; see `tests/benchmarks/` for current totals; taxonomy: 37 codes) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **3** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check with recency window) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-03-13)

### Completed This Session

1. **Domain Consistency Enforcement** — automated test + expanded checklist
   - `TestDomainConsistency` (6 tests): validates domains.json matches config.py, server.py enums, handler valid_domains, extractor DOMAIN_PREFIXES, disk files, file paths
   - Promoted extractor `_get_domain_prefix()` local dict to `DOMAIN_PREFIXES` class constant for direct testability
   - COMPLETION-CHECKLIST.md: expanded domain changes section from 10→21 items (source of truth, code, test, doc, verification)
   - PROJECT-MEMORY.md: marked Gotcha #18 (implicit prefixes) as resolved
   - Reviewed by: code-reviewer (2 passes), contrarian-reviewer, coherence-auditor, validator — all pass
   - 877 tests passing, 0 failures

2. **Coherence Review and Repair** — 5-batch fix for ~25 audit findings
   - Batch 1: Added missing ui-ux domain to config.py fallback, server.py enum, test assertion; updated stale version refs in fallback
   - Batch 2: CLAUDE.md framework version v2.9.6→v2.20.0; meta-methods §1.1.3 filename examples; PROJECT-MEMORY metrics to baseline_2026-03-13; SESSION-STATE hardcoded values→pointers
   - Batch 3: Archived 4 superseded docs; renamed multimodal-rag files v2.0.0→v2.1.0/v2.1.1; updated all cross-references
   - Batch 4: ARCHITECTURE.md date, file tree, test table, markers, benchmarks, item count; SPECIFICATION.md domain count+table
   - Batch 5: README.md footer; tiers.json ref disambiguation; COMPLETION-CHECKLIST.md domain-change propagation checklist
   - Root cause: incomplete propagation when ui-ux domain was added — COMPLETION-CHECKLIST now prevents recurrence

### Previous Session (2026-03-12)

1. **§3.1.4 Tool Content Model** — ai-coding methods v2.18.0
   - New `####` subsection codifying the framework's implicit three-mode tool inclusion pattern
   - Three modes: named reference, appendix, build our own — each with criteria and examples
   - Discovery-driven philosophy: tools enter through usage, not market surveys
   - 5-item decision checklist + supersession rule
   - Cross-references: Appendix F, §5.6.5, §5.6.8
   - Document Governance updated with cross-reference to Tool Content Model
   - Changelog: combined entry for v2.18.0 (§3.1.4 expansion + Tool Content Model + §5.6.8)
   - Index rebuilt: 148 principles + 546 methods (694 total, no count change — subsection within existing method)
   - 871 tests passing, 0 failures
   - Context Engine retrieval verified: score 0.844
   - Files changed: `documents/ai-coding-methods-v2.18.0.md`, `SESSION-STATE.md` (backlog #13), `index/` (rebuilt)

2. **Backlog #13: Governance-Aware Output Compression** — added to SESSION-STATE.md
   - PostToolUse hook concept for compressing verbose Bash output
   - Trigger: >20% context consumed by terminal output (not hitting today)
   - Fits "build our own" mode — external tools (RTK) fail §5.6.8 vetting

3. **Multi-Agent Orchestrator-Absent Pattern Gaps** — v2.3.0 principles, v2.14.0 methods
   - Catalyst: OpenAI Symphony framework analysis (queue-to-isolated-agent dispatch, no orchestrator)
   - Aggregate Blast Radius rules in AO-1: escalation table for N concurrent agents at same level (N>3 → L(x+1)), mandatory review for concurrent L3
   - Decentralized Dispatch Variant under Parallel Pattern (§3.3): 4 compensating controls for orchestrator-absent topologies, 2 anti-patterns
   - Continuous Queue Consumption protocol in Task Ownership: post-task gates, aggregate review every N tasks, pool pause on failure
   - Isolation Blindspot pitfall in Context Isolation (MA-A2): isolation prevents cross-agent awareness of overlapping changes
   - Validated by contrarian-reviewer and coherence-auditor in planning phase
   - Index rebuilt: 148 principles + 546 methods (694 total, no count change — additions within existing sections)
   - 871 tests passing, 0 failures
   - Retrieval verified: all 3 queries surface correct top-hit principles
   - Files changed: `documents/multi-agent-domain-principles-v2.3.0.md` (renamed from v2.2.0), `documents/multi-agent-methods-v2.14.0.md` (renamed from v2.13.0), `documents/domains.json`, `SESSION-STATE.md`, `index/` (rebuilt)

### Previous Session (2026-03-11)

1. **§5.6.8 Third-Party Hook Vetting Procedure** — ai-coding methods v2.18.0
   - New section after §5.6.7 addressing governance gap: hooks have more privileged access than MCP servers but had zero vetting guidance
   - Pre-Installation Checklist: 6 items (source verification, behavior audit, governance interference check, information loss assessment, permission scope review, supply chain review)
   - Information Intermediary Warning: output compression tools can cause silent information loss during security scans
   - §5.6.5 updated with cross-reference to §5.6.8 for hook-based tools
   - Catalyst: RTK (Rust Token Killer) analysis — tool itself doesn't belong in framework (tool-agnostic), but exposed the hook vetting gap
   - Index rebuilt: 148 principles + 546 methods (694 total, +1 method)
   - 871 tests passing, 0 failures
   - Retrieval verified: `coding-method-third-party-hook-vetting-procedure` surfaces with HIGH confidence
   - Files changed: `documents/ai-coding-methods-v2.18.0.md`, `README.md` (count update), `index/` (rebuilt)

### Previous Session (2026-03-09)

1. **Multi-Agent AO-Series: Autonomous Operation Governance** — v2.2.0 principles, v2.13.0 methods
   - New AO-Series: 4 principles (AO1-AO4) — Blast Radius Classification, HITL Removal Criteria, Compensating Controls, Autonomous Drift Monitoring
   - 4 new failure modes (MA-AO1 through MA-AO4) addressing external-facing autonomous actions, premature HITL removal, compounding drift, platform/legal liability
   - New TITLE 6 in methods: §6.1-6.4 covering blast radius classification, autonomy level assessment, compensating controls checklist, drift monitoring procedures
   - Graduated Autonomy Levels: AL-0 (Supervised) → AL-1 (Batch Approved) → AL-2 (Monitored Autonomous) → AL-3 (Fully Autonomous)
   - Blast Radius Classification: L0 (Internal-Reversible) → L1 (Internal-Irreversible) → L2 (External-Reversible) → L3 (External-Irreversible)
   - Extractor: `("multi-agent", "autonomous"): "AO"` in CATEGORY_SERIES_MAP; `ao-series` before `o-series` in category_mapping (substring collision fix)
   - Evidence: CNBC 2026, Help Net Security 2026, Strata 2026, Singapore IMDA 2026, UC Berkeley 2026, HackerNoon 2026, Kore.ai 2026, SafePaaS 2026
   - Catalyst: Analysis of OpenClaw autonomous agent architectures (Jacob Klug's AI agent army article)
   - 4 new tests (3 extractor + 1 server), 871 total passing
   - Index rebuilt: 148 principles + 545 methods (693 total)
   - Files changed: `documents/multi-agent-domain-principles-v2.2.0.md` (renamed from v2.1.1), `documents/multi-agent-methods-v2.13.0.md` (renamed from v2.12.3), `documents/domains.json`, `src/ai_governance_mcp/extractor.py`, `tests/test_extractor.py`, `tests/test_server.py`, `index/` (rebuilt)

### Previous Session (2026-03-08)

1. **UI/UX Governance Domain** (Backlog #5) — v1.0.0 + Phase 6 External Review
   - New domain for interactive software interface design with AI assistance
   - **20 principles** across 6 series: VH (Visual Hierarchy, 3), DS (Design System, 3), ACC (Accessibility, 3), RD (Responsive, 2), IX (Interaction, 7), PL (Platform, 2)
   - **43 methods** across 9 sections: Design-to-Code Workflow, Component Library Governance, Design Review Gates (+ Dark Pattern Screening, Core Web Vitals), Accessibility Testing, Responsive Strategy, Cross-Platform Adaptation (+ Convention Currency), Design System Documentation, AI Tooling Integration, UX Content/Microcopy Governance
   - **18 AI-specific failure modes** (UX-F1-F3, F5-F10, F12-F19, F21; F4/F11 cut for insufficient AI-specificity; F20 rejected as already covered)
   - Phase 6 additions: IX7 (Ethical Interaction Design — dark patterns), UX-F19 (motion accessibility), UX-F21 (deceptive design), 6 new evidence citations (ISO 40500:2025, DTCG v2025.10, WCAG 2.5.8, MobileSoft 2025, Serezlic & Quijada 2025, FTC dark patterns), 6 new methods sections (§3.5, §3.6, §6.4, §9.1-9.3), i18n flagged for v1.1.0
   - Evidence base: WCAG 2.2/ISO 40500:2025, Nielsen 10 Heuristics, Laws of UX, Apple HIG, Material Design 3, GitClear 2025, WebAIM Million, Atomic Design, FTC Dark Patterns, DTCG v2025.10, MobileSoft 2025, Serezlic & Quijada 2025
   - Scope boundary: ai-coding §2.4/§2.5 = process (when); UI/UX = substance (what)
   - Technical integration: `domains.json`, `extractor.py` (prefix + 6 CATEGORY_SERIES_MAP + 12 category_mapping + is_series_header + skip_keywords), `server.py` (valid_domains + enum), constitution domain list updated
   - Cross-references added in ai-coding §2.4.3 and §2.5.3
   - 7 new tests (4 extractor + 3 server), 867 total passing
   - Multi-pass validation: validator (PASS — 1 cross-ref fix applied), coherence-auditor (3 findings fixed: constitutional derivation name, IX-Series description, RD2 MUST/SHOULD harmonization; 1 cosmetic rejected), contrarian-reviewer (4 findings — 1 accepted: motion accessibility added to ACC3; 2 deferred to v1.1.0; 1 rejected), code-reviewer (defensive improvements applied to extractor)
   - Retrieval quality: all 5 new spot-checks pass (dark patterns→IX7, CWV→§3.6, platform currency→§6.4, error messages→§9.2, animation accessibility→ACC3)
   - Perplexity Deep Research external review: 14 findings evaluated, 7 ACCEPT, 3 ACCEPT IN PART, 1 REJECT, 3 DEFER
   - Files changed: `documents/ui-ux-domain-principles-v1.0.0.md`, `documents/ui-ux-methods-v1.0.0.md`, `index/` (rebuilt)

### Previous Session (2026-03-01)

1. **§3.1.4 Technology Selection Expansion** (v2.18.0) — see git log for details

### Previous Session (2026-02-28)

1. **Tiered Governance Principle Activation (Phase 0 + Phase 1)** — Backlog #8
   - **Phase 0: Fixed dead `series_code`** — Added `CATEGORY_SERIES_MAP` (28 entries) in extractor.py `_build_principle()` to infer series_code from (domain, category) for new-format headers. Constitution safety → "S", storytelling ethics → "E", multimodal-rag security → "SEC". Restores `apply_hierarchy()` sorting and `p.series_code == "S"` detection in server.py.
   - **Phase 0: Domain-aware `apply_hierarchy()`** — Updated retrieval.py to use domain context for hierarchy sorting. Constitution principles (0-5) sort above domain principles (10). Shared codes like C/Q no longer collide across domains.
   - **Phase 1: Universal floor tier** — Created `documents/tiers.json` with 3 principles, 3 methods, 1 subagent check as compact anti-pattern checks. Added `_load_tiers_config()` and `_build_universal_floor()` to server.py. `evaluate_governance` now includes `universal_floor` section in every response (separate from `max_results=10` similarity results).
   - **25 new tests** (810 total passing) — 10 extractor tests (CATEGORY_SERIES_MAP, S-Series isolation, new-format inference), 3 retrieval tests (domain-aware hierarchy), 11 server tests (tiers loading, floor building, evaluate_governance integration, CI ID validation), 1 production index validation
   - **Index rebuilt** — All 124 principles now have series_code populated (only 1 None: multi-agent justification with "general" category)
   - Files changed: `extractor.py`, `retrieval.py`, `models.py`, `server.py`, `conftest.py`, `test_extractor.py`, `test_retrieval.py`, `test_server.py`, `documents/tiers.json` (new), `index/` (rebuilt)

2. **Unified Governance Enforcement System** — 9-step implementation addressing 87% hook non-compliance
   - **Shared scanner module** (`.claude/hooks/scan_transcript.py`) — reusable Python scanner with recency window support
   - **PreToolUse hook → hard mode default** — flipped from soft to hard; BLOCKS Bash|Edit|Write until both `evaluate_governance()` and `query_project()` called; 200-line recency window; soft-mode escape hatches via `GOVERNANCE_SOFT_MODE`/`CE_SOFT_MODE`
   - **UserPromptSubmit hook → conditional suppression** — silent when compliant (saves ~128 tokens/prompt), shortened reminder (~50 tokens) when not; reads transcript_path from stdin JSON
   - **CLAUDE.md slimmed** from 214 → 74 lines; Post-Change Checklist → `COMPLETION-CHECKLIST.md`; "ENFORCED BY HOOK" framing
   - **SERVER_INSTRUCTIONS slimmed** from ~148 → ~45 lines; removed retrievable sections; added Subagent Advisory Framing section
   - **Advisory Output section** added to all 10 agent templates (canonical + synced to local); orchestrator got Step 4: Evaluate Subagent Results with structured evaluation table and 90% threshold signals
   - **Template hashes updated** in `AGENT_TEMPLATE_HASHES`
   - **Compliance analysis script** (`scripts/analyze_compliance.py`) — parses JSONL transcripts, reports per-session and aggregate compliance rates
   - **18 new tests** (32 total hook tests, 785 total passing) — includes mixed enforcement mode tests and non-numeric window arg test
   - **Code review findings evaluated** using advisory framing: H1 (ValueError fix) accepted, H2 (mixed mode tests) accepted, M2 (CLAUDE.md pointers) rejected (intentional slimming), M4 (debug inconsistency) rejected (acceptable divergence)
   - Files changed: 33 files, +1512 -504 lines
   - **Docker image rebuilt and pushed** — `jason21wc/ai-governance-mcp:latest` (sha256:7dbc94c67272a3bd82afaecb709efc3b506d8b7844da469baa41ac4962528808)
   - CI: all green (3.10, 3.11, 3.12 + security + lint + content scan)

## Next Actions

### 1. Backlog — Enforcement & Compliance Infrastructure (Priority: MEDIUM)
Unified initiative covering enforcement improvements, cross-platform reach, and effectiveness measurement. Rolled up from four related items — tackling together enables systems-level view, avoids unexpected interactions, and identifies synergies between approaches.

**Goal:** Empirical evidence that our enforcement layers work, measurable compliance rates, and governance enforcement that works across any AI client — not just Claude Code.

**Part A: Hook Improvements** — COMPLETE (2026-02-28)
- Hard-mode default with recency window (200 lines), shared scanner module, conditional suppression
- See session summary above for details

**Part B: MCP Proxy for Model-Agnostic Enforcement** (research → implementation)
An MCP proxy sits between ANY AI client and MCP servers, intercepting tool calls to enforce governance policies regardless of which AI model or IDE is used.

*Proxy candidates:*
- **Latch** (latchagent.com) — open-source, Docker, natural language or rule-based policies
- **MCPTrust** (github.com/mcptrust/mcptrust) — lockfile enforcement, drift detection, CEL policy
- **FastMCP Middleware** — native framework middleware for request interception

*Target audiences (progressive):*
1. **Personal** — Governance enforcement across Claude Code, Cursor, Gemini CLI, and other AI clients Jason uses. Proving ground for policy design.
2. **Teams** — Shared governance policies across team members with consistent enforcement. Adds: centralized policy config, team onboarding docs, policy-as-code.
3. **Open-source consumers** — Easy way for anyone using the framework to get enforcement. Adds: distribution mechanism, setup guide, sensible defaults, documented customization.

*Open questions (to resolve when work begins):*
- Which proxy tool best fits our architecture? (Requires hands-on evaluation)
- What governance rules get enforced at proxy level vs. advisory level?
- How does proxy enforcement interact with existing hooks? (Complementary or replacement?)
- What's the configuration/policy format? (Natural language, CEL, custom DSL?)

*Evaluation criteria:*
- Works with stdio MCP transport (our primary)
- Open-source with active maintenance
- Policy language expressive enough for our skip-list and enforcement rules
- Minimal latency overhead on tool calls
- Can be distributed as part of the framework package

**Part C: Effectiveness Analytics** — COMPLETE (2026-03-01)
Enhanced `scripts/analyze_compliance.py` with argparse CLI (analyze/baseline/compare subcommands), split gap rates (gov vs CE), session buckets, compliance quality classification, enforcement era detection, proximity metrics. 48 new tests in `tests/test_analyze_compliance.py`. Post-enforcement baseline generated: 71 sessions, 94.2% combined gap rate (62.6% gov, 92.7% CE), 16.9% compliance rate. Only 2 sessions under hard-mode enforcement so far — delta will grow as more post-enforcement sessions accumulate.

*Original scope (retained for reference):*
Measure real-world compliance rates for both governance and Context Engine. Same methodology, two tracks.

*Governance track:*
- How often is `evaluate_governance()` actually called vs. skipped?
- Do hooks successfully nudge behavior? (Before/after comparisons)
- Correlation with session length/complexity (context rot effect on compliance)
- Aggregated metrics from `get_metrics()` over time

*Context Engine track:*
- Real-world `query_project()` usage rates per session
- Query-before-create compliance (does querying happen before file creation/modification?)
- Result relevance — does queried information influence decisions, or is it perfunctory?
- Query frequency correlation with code duplication rates

*Approach (both tracks):*
- Transcript analysis scripts (parse Claude Code transcripts for tool call patterns)
- Aggregated `get_metrics()` data over multiple sessions
- Before/after comparisons with hooks enabled/disabled
- Session length bucketing (short <10 turns, medium 10-50, long 50+)

*Success criteria:*
- Baseline compliance rates established for both governance and CE
- Measurable improvement from each enforcement layer (advisory → hooks → proxy)
- Data-driven decisions on where enforcement gaps remain

**Synergies across parts:**
- Part A (hook improvements) directly affects Part C (analytics) — better hooks should show measurable compliance improvement
- Part B (proxy) provides a second enforcement layer measurable in Part C
- Part C data informs which Part B proxy policies matter most
- All three share transcript analysis infrastructure

### 2. Backlog — Project Initialization Part B (Priority: TBD)
Closing the bootstrap gap — making it easier for new users to get governance memory files created when starting a new project. Part A shipped (`150e4e6`): advisory-only SERVER_INSTRUCTIONS with project initialization section, conversational trigger, consent step, and partial-init handling.

**Problem:** New users connecting the MCP server to a project for the first time don't automatically get governance memory files (SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md, project instructions file). Part A relies on the AI suggesting initialization — advisory only, no enforcement.

**Three candidate approaches (pick one or combine):**
1. **`scaffold_project` MCP tool** — New tool that auto-creates governance memory files. AI calls the tool; files are created server-side. Requires adding filesystem write capability to the MCP server. *Pros:* Works within MCP protocol, AI-initiated. *Cons:* Requires filesystem write (security consideration), depends on AI remembering to call it.
2. **Server-side first-run detection** — MCP server detects uninitialized projects (no governance files in working directory) and proactively triggers initialization protocol. *Pros:* Automatic, no AI cooperation needed. *Cons:* Requires filesystem read access, mechanism to signal AI client, may be surprising.
3. **Wrapper/web app/IDE plugin** — Move beyond MCP for scaffolding. CLI wrapper, web app, or IDE plugin handles project setup outside the MCP protocol. *Pros:* Decouples initialization from AI session entirely, best UX. *Cons:* Separate tool to build and maintain, platform-specific.

**Open questions:**
- Which approach best balances ease-of-use with security constraints?
- Should scaffold_project be opt-in (AI suggests) or opt-out (auto-detect)?
- How does this interact with existing `install_agent` tool patterns?

**Implementation requirements:** Depends on chosen approach. All require tests. Approach 1 requires new MCP tool + filesystem write. Approach 2 requires filesystem read + client signaling. Approach 3 requires separate tooling. See PROJECT-MEMORY.md > Roadmap > Part B for full analysis.

### 3. Backlog — Quantized Vector Search (Deferred)
Not needed at current scale (10K-100K vectors, 1-5ms brute-force latency). Revisit when Context Engine reaches 500K+ vectors (multi-project indexing) or users report perceptible latency.

**Trigger conditions:** 500K+ vectors loaded, OR user-reported perceptible query latency (>100ms).

**Phased approach:** See PROJECT-MEMORY.md > Roadmap > Quantized Vector Search for full details (product quantization → scalar quantization → HNSW index progression).

### 4. Backlog — Add Training & Instructional Design Domain (Priority: TBD, Recommended: 2nd)
**Recommended priority: 2nd** — Broad applicability. AI is increasingly used to generate training materials, SOPs, and tutorials. Strong evidence base already identified. Slightly lower urgency than UI/UX because it's less adjacent to day-to-day AI-assisted coding.
New governance domain for training, instructional design, and procedures. Replaces the original "Procedures Domain" placeholder — procedures are a type of training content and belong under this broader umbrella.

**Scope — Content types:**
- Standard Operating Procedures (SOPs) and runbooks
- Technical tutorials and how-to guides
- Onboarding materials (new hire, new project, new tool)
- Workshop and course design
- E-learning and self-paced training content
- Knowledge assessments and certification criteria
- Job aids, quick reference cards, cheat sheets

**Principles (candidate areas):**
- Learning objective alignment (every training artifact tied to measurable outcomes)
- Scaffolded complexity (progressive disclosure, prerequisite sequencing)
- Audience-appropriate design (novice vs. intermediate vs. expert paths)
- Active learning over passive consumption (practice, application, reflection)
- Assessment validity (testing understanding, not just recall)
- Procedure safety completeness (no skipped critical steps, exception handling)
- Knowledge retention design (spaced repetition, retrieval practice)
- Accessibility and inclusivity in training materials

**Methods (candidate areas):**
- Procedure/SOP authoring workflow (draft → review → validate → publish)
- Training needs analysis (gap identification, audience profiling)
- Course/module structure design
- Assessment design and rubric creation
- Training effectiveness measurement
- Knowledge transfer and handoff protocols
- Maintenance and currency review (keeping training materials up to date)

**AI-specific failure modes to address:**
- AI generating technically accurate but pedagogically poor content (information dump, no scaffolding)
- AI skipping critical safety steps in procedures
- AI not adapting detail level to audience expertise
- AI creating assessments that test recall rather than understanding or application
- AI generating procedures without exception/error handling paths
- AI producing training without explicit learning objectives
- AI over-relying on text when visual/interactive approaches would be more effective

**Evidence base and industry best practices to research:**
- **TWI (Training Within Industry)** — WWII-era methodology still foundational: Job Instruction (JI), Job Methods (JM), Job Relations (JR), Job Safety (JS). Four-step JI method (Prepare → Present → Try Out → Follow Up) is the gold standard for procedural training
- **Bloom's Taxonomy** — Cognitive domain hierarchy (Remember → Understand → Apply → Analyze → Evaluate → Create) for writing learning objectives and assessments
- **ADDIE Model** — Instructional design lifecycle (Analysis → Design → Development → Implementation → Evaluation)
- **SAM (Successive Approximation Model)** — Agile alternative to ADDIE with iterative prototyping
- **Kirkpatrick's Four Levels** — Training effectiveness evaluation (Reaction → Learning → Behavior → Results)
- **Merrill's First Principles of Instruction** — Task-centered learning, activation, demonstration, application, integration
- **Gagné's Nine Events of Instruction** — Structured instructional sequence from attention through retention/transfer
- **Lean/Toyota Kata** — Improvement and coaching routines for building organizational capability
- **ISO 10015** — Quality management guidelines for training
- **WCAG** — Accessibility standards applied to training materials
- **Mayer's Multimedia Learning Principles** — Cognitive load theory applied to multimedia instruction (coherence, signaling, redundancy, spatial contiguity, temporal contiguity)
- **Dreyfus Model of Skill Acquisition** — Novice → Advanced Beginner → Competent → Proficient → Expert progression for audience-appropriate design
- **Spaced Repetition Research** — Ebbinghaus, Leitner system, evidence base for retention design
- **Deliberate Practice** (Ericsson) — Structured practice with feedback for skill development

**Implementation requirements:** Domain config in `domains.json`, principle document(s), methods document(s), extractor support, index rebuild, tests. Framework content to be developed collaboratively — Jason to provide domain-specific context, AI to research and structure per framework standards.

### 5. Backlog — Add UI/UX Domain — COMPLETE (2026-03-08)
New governance domain for UI/UX design principles and methods. **Separate domain** from ai-coding — ai-coding §2.4/§2.5 cover *process* (when to do UX work); this domain covers *substance* (what good UX is). See session summary for details.

**Recommended priority: 1st** — Highest ai-coding adjacency. A huge amount of AI-assisted development involves building interfaces. Bridges naturally from existing §2.4/§2.5. Most immediate value for framework users.

**Scope — Interactive software interfaces only:**
- Web sites (marketing, content, e-commerce)
- Web apps (SaaS, dashboards, admin panels)
- Desktop apps (native, Electron/Tauri)
- Mobile apps (iOS, Android, cross-platform)

**Explicitly out of scope:** Presentations (slide decks, pitch decks), documents, reports, infographics, print design, and other non-interactive visual artifacts. These are different failure mode clusters (narrative flow and information density vs. accessibility, responsive layout, and interaction design) with different evidence bases and tooling. If needed, they belong in a separate Visual Communication domain — see backlog item #6.

**Principles (candidate areas):**
- Visual hierarchy and layout composition
- Consistency and design system adherence
- Accessibility (WCAG compliance, screen readers, color contrast, keyboard navigation)
- Responsive and adaptive design
- Information architecture and navigation patterns
- Interaction design (feedback, affordances, microinteractions)
- Typography and readability
- Color theory and theming (light/dark mode)
- Performance perception (skeleton screens, progressive loading)
- Platform convention compliance (Apple HIG, Material Design, web standards)

**Methods (candidate areas):**
- Design-to-code workflow (Figma → implementation)
- Component library governance (design tokens, atomic design)
- Design review and validation gates
- Accessibility testing and auditing procedures
- Responsive breakpoint strategy
- Cross-platform adaptation (shared design language, platform-specific adjustments)
- Design system documentation and maintenance

**AI tooling integration:**
- Figma MCP connectors (design context for Claude/frontier models)
- Anysphere/Cursor design integrations
- Design token extraction and code generation
- Screenshot-to-feedback loops (visual regression)

**Evidence base to research:**
- Nielsen's 10 Usability Heuristics
- WCAG 2.2 / upcoming 3.0
- Apple Human Interface Guidelines
- Google Material Design 3
- Laws of UX (Fitts's Law, Hick's Law, Jakob's Law, etc.)
- Baymard Institute e-commerce UX research

**AI-specific failure modes to address:**
- AI generating inaccessible markup (missing alt text, ARIA, semantic HTML)
- Inconsistent spacing/typography across generated components
- Platform convention violations (iOS patterns on Android, etc.)
- Over-designed UI (AI tendency toward visual complexity over usability)
- Design system drift (AI generating one-off styles vs. using tokens)

**Implementation requirements:** Domain config in `domains.json`, principle document(s), methods document(s), extractor support, index rebuild, tests. Cross-reference: ai-coding §2.4/§2.5 may need minor updates to reference the new domain.

### 6. Backlog — Add Visual Communication Domain (Priority: TBD, Recommended: 3rd)
New governance domain for non-coding visual artifacts: presentations, documents, reports, infographics, and print design. Separate from UI/UX (item #5) because different failure mode clusters, evidence bases, and tooling.

**Recommended priority: 3rd** — Narrower scope, fewer failure modes. Can inherit domain structure patterns established by UI/UX and Training domains. Less urgency since fewer people use AI for presentation/document design as a primary workflow.

**Scope — Artifact types:**
- Presentations (slide decks, pitch decks, keynotes)
- Documents and reports (executive summaries, technical reports, proposals)
- Infographics and data visualizations
- Print design (brochures, posters, one-pagers)

**Principles (candidate areas):**
- Narrative flow and story structure
- Information density and cognitive load (Tufte's data-ink ratio)
- Visual hierarchy for static layouts
- Audience-appropriate design (executive vs. technical vs. public)
- Brand consistency and style guide adherence
- Data visualization integrity (no misleading charts, appropriate chart types)
- Accessibility in documents (heading structure, alt text, color contrast, screen reader compatibility)

**Methods (candidate areas):**
- Slide deck composition workflow (outline → structure → design → review)
- Presentation review and validation gates
- Template and brand compliance checking
- Data visualization best practices
- Document accessibility auditing

**AI tooling integration:**
- Presentation generation tools (Gamma, Beautiful.ai, Tome, SlidesGPT)
- Document generation (Google Docs AI, Notion AI, markdown-to-PDF pipelines)
- Data visualization libraries (D3.js, Plotly, Matplotlib) — AI-generated chart code
- Brand asset management tools and template engines

**AI-specific failure modes to address:**
- AI generating text-heavy slides (wall of text vs. visual communication)
- Inconsistent styling across generated slides/pages
- Misleading or inappropriate data visualizations
- Poor narrative structure (information dump vs. story arc)
- Brand guideline violations

**Evidence base to research:**
- Edward Tufte (data visualization, information design)
- Nancy Duarte (presentation design, story structure)
- Garr Reynolds (Presentation Zen)
- WCAG document accessibility guidelines
- Data visualization research (Cleveland & McGill, Few)

**Implementation requirements:** Domain config in `domains.json`, principle document(s), methods document(s), extractor support, index rebuild, tests.

### 7. Backlog — Security Content Currency Process (Priority: LOW)
Periodic review method for keeping our security guidance (§5.3-§5.11, security-auditor subagent, pre-release checklist) current as the AI security landscape evolves. Replaces the narrow "wait for AI scanner benchmarks" watch item with a broader currency practice.

**Problem:** AI security is evolving rapidly — new tool categories emerge (e.g., Claude Code Security, 2026-02-20), attack patterns shift (prompt injection, supply chain, agent-specific threats), and standards update (OWASP, CWE). Our security content is comprehensive today but will go stale without a review cadence.

**Scope — What gets reviewed:**
- Existing methods coverage (§5.3 Security Validation, §5.6 AI Coding Tool Security, §5.7 Application Security Patterns, §5.8 Domain-Specific Security, §5.11 Zero Trust)
- Security-auditor subagent definition and checklist
- Pre-release security checklist in CLAUDE.md
- Evidence base citations — are referenced sources still current?

**Framework pattern for tool-specific content:**
- **Generalized guidance** (tool-agnostic) → methods sections (e.g., "how to evaluate AI security scanners" lives in §5.3 or §5.6)
- **Specific tool guidance** (tools we use and favor) → appendix or tool-specific subsection (e.g., "Claude Code Security configuration and usage" as an appendix to §5.3)
- We don't aim for comprehensive coverage of every tool — capture what we actively use. If we switch tools, add the new one accordingly.

**Inputs to monitor:**
- New AI security tool categories and independent benchmarks (OWASP, NIST, academic studies)
- Emerging attack patterns specific to AI-assisted development (agent-specific threats, MCP-specific vulnerabilities)
- Standards updates (OWASP Top 10 revisions, CWE/SANS updates, new CVE patterns)
- Our own security-auditor findings across sessions (recurring gaps = content gap)

**Current status of AI scanner question:** Claude Code Security launched 2026-02-20. Interim guidance distributed across §5.3.3, §5.3.5, §6.4.9 (v2.15.1). Still waiting for vendor-independent accuracy data to determine if AI-contextual scanners are categorically different from AI code reviewers. When benchmarks arrive, apply the generalized/tool-specific pattern above.

**Cadence:** TBD — quarterly review seems reasonable for security content, but frequency should match the pace of landscape change. Could be event-triggered (major tool launch, OWASP update) rather than calendar-driven.

**Implementation requirements:** Not a code change — this is a methods-level practice. May result in: updated methods sections, new appendices for favored tools, updated evidence base citations, revised security-auditor subagent instructions.

### 8. Backlog — Subagent Output Framing: Advisory, Not Authoritative — COMPLETE (2026-02-28)
Implemented as part of Unified Governance Enforcement System. Advisory Output section added to all 10 agent templates, orchestrator Step 4, and SERVER_INSTRUCTIONS Subagent Advisory Framing section. See session summary.

**Problem:** Current subagent definitions and orchestrator instructions don't make the advisory nature of subagent output explicit enough. An AI receiving a code review, security audit, or validation result from a subagent may treat those findings as requirements to implement wholesale, rather than expert opinions to evaluate critically. This creates two failure modes:
1. **Subagent anchor bias** — AI implements every subagent suggestion without critical evaluation, even when suggestions conflict with project context, user intent, or practical constraints
2. **Original output anchor bias** — AI dismisses subagent findings to preserve its initial approach, rationalizing why each suggestion doesn't apply

**Goal:** Crystal-clear framing at every layer — subagent definitions, orchestrator instructions, and SERVER_INSTRUCTIONS — that subagent output is input to a decision, not the decision itself. The main agent should apply the same anchor bias mitigation protocol (§7.10) to both its original work and subagent suggestions.

**Scope — What gets updated:**
- **Subagent definitions** (`documents/agents/*.md`) — Add explicit "Advisory Output" section to each agent template stating that findings are recommendations, not mandates. The consuming agent must evaluate each finding against project context before acting.
- **Orchestrator subagent** (`documents/agents/orchestrator.md`) — Add protocol for how the orchestrator should process subagent results: receive → evaluate independently → decide → document reasoning. Explicit instruction to avoid both anchor bias directions.
- **SERVER_INSTRUCTIONS** (governance server instructions) — Add guidance in the orchestrator protocol section about subagent output being advisory. Reference §7.10 anchor bias checkpoints for evaluating subagent suggestions.
- **Constitution or meta-methods** — Consider whether this needs a principle-level statement (e.g., "AI agents must independently evaluate delegated findings rather than implementing them uncritically") or if method-level guidance suffices.

**Anchor bias protocol integration:**
The existing §7.10 Anchor Bias Mitigation Protocol applies directly. When reviewing subagent output, the main agent should:
1. **Reframe** — State the goal without referencing the subagent's specific suggestions
2. **Generate** — Consider alternatives the subagent may not have suggested
3. **Challenge** — "Would I make this change if I discovered it myself vs. being told to?"
4. **Evaluate** — Compare subagent suggestion against project context, user intent, and practical constraints

**Key design decisions:**
- Should each subagent definition include the advisory framing, or should it be centralized in the orchestrator only? (Recommendation: both — belt and suspenders. Subagent definitions state "my output is advisory"; orchestrator states "evaluate subagent output critically".)
- How explicit should the "disagree and commit" protocol be? The main agent needs permission to reject subagent findings with documented reasoning.
- Should there be a structured output format for subagent evaluation? (e.g., "Finding: X | Agree/Disagree | Reasoning: Y | Action: Z")

**Implementation requirements:** Content changes to agent templates and SERVER_INSTRUCTIONS. Rebuild index after document changes. Tests for updated agent template content validation. No code changes expected — this is a governance content update. Sync `documents/agents/` → `.claude/agents/` after edits.

### 9. Backlog — Tiered Principle Activation (Priority: MEDIUM)
Multi-phase feature: intermediate governance tiers between S-Series veto and similarity-scored retrieval.

**Phase 0: Fix dead `series_code`** — COMPLETE (2026-02-28)
- Added `CATEGORY_SERIES_MAP` (28 entries) in extractor.py. Domain-aware `apply_hierarchy()` in retrieval.py.

**Phase 1: Universal Floor (Tier 1)** — COMPLETE (2026-02-28)
- `documents/tiers.json` with 3 principles + 3 methods + 1 subagent check as compact anti-pattern reminders.
- `evaluate_governance` injects `universal_floor` section in every response (separate from `max_results=10`).

**Phase 1.5: Measure Tool-Active Gap** — COMPLETE (2026-03-01)
- Ran 24 representative queries through `query_governance`. Results:
  - Context Engine "query first": 0/24 surfaced — NOT a retrieval gap (enforced by hooks, not in documents)
  - Testing Integration: 3/24 surfaced — MODERATE gap, addressed by adding testing check to universal floor
  - Security principles: 7/8 surfaced — SMALL gap, adequate retrieval
  - Multi-agent/subagent: 3/3 surfaced — NO gap
  - Post-action verification: 0/24 — MODERATE gap, addressed by adding §7.5 check to universal floor
- **Verdict: Phase 2 NOT NEEDED.** Gaps are cross-cutting procedural, not tool-specific.
- Added 2 items to `tiers.json` v1.1.0: testing reminder + post-action verification (9 total items)

**Phase 2: Tool-Active (Tier 2)** — CANCELLED per Phase 1.5 results
- Similarity-scored retrieval handles security and multi-agent guidance adequately.
- Remaining gaps (testing, post-action) addressed via universal floor additions.

**Phase 3: Accountable Reasoning combined principle** (deferred)
- After Phase 1 proves valuable, consider formal combined principle.
- Until then, tier config synthesizes both existing IDs.

### 10. Backlog — UI/UX Tool-Specific Integration Guides (Priority: LOW, Usage-Driven)
Add tool-specific appendices to ui-ux-methods §8 as tools are adopted. Per tool-specific content pattern: capture what we actively use, not catalog every option.

**Candidate tools (researched 2026-03-08, production-grade):**
- **Figma Official MCP** — read design context/tokens + write rendered UI back (March 2026). Token cost warning: 600K+ tokens for large designs.
- **Storybook MCP** (official, Aug 2025) — component manifests with metadata, variants, token bindings. Optimized payload reduces token cost vs. raw source parsing.
- **Deque Axe MCP** (official) — accessibility auditing. Would make ACC1-ACC3 validation criteria enforceable in-loop.
- **Microsoft Playwright MCP** (official) — browser automation, screenshots at any viewport. Enables RD1/RD2 responsive validation.
- **Percy via BrowserStack MCP** — visual regression with AI review agent. 3x faster review, 40% false positive reduction.
- **Playwright-Lighthouse MCP** (community) — Lighthouse audits + Playwright. Maps to §3.6 Core Web Vitals.

**Trigger:** When Jason adopts any of these tools in a real project, add integration guide with observed failure modes and token cost data.

**Known risks:** Token cost (Figma 15x estimate gap), design data privacy through AI APIs, fidelity gaps requiring manual adjustment, design system maturity as prerequisite.

### 11. Backlog — Autonomous Operations Domain (Priority: TBD, Future)
Full standalone domain if autonomous agent patterns grow beyond what multi-agent AO-Series can cover. Current AO-Series (4 principles, 4 methods sections) is Phase 1 — sufficient for current patterns (OpenClaw-style agent armies, cron-scheduled agents, always-on workflows).

**Trigger for domain creation:** When autonomous operation governance needs exceed multi-agent's scope — e.g., financial compliance (SOX), industry-specific regulatory frameworks, autonomous agent marketplace governance, cross-organization agent federation, or when AO-Series grows beyond 6-8 principles.

**Candidate additions beyond current AO-Series:**
- Financial governance and audit compliance (SOX, SOC 2)
- Industry-specific regulatory frameworks (healthcare HIPAA agents, financial FINRA agents)
- Agent marketplace and discovery governance
- Cross-organization agent trust and federation
- Autonomous agent insurance and liability frameworks
- Agent lifecycle management (provisioning, retirement, succession)

**Evidence to watch:** Regulatory frameworks specifically targeting autonomous AI agents (beyond general AI regulation). Current evidence base (CNBC, Strata, Singapore IMDA, UC Berkeley 2026) supports AO-Series but not yet a full domain.

### 12. Backlog — Operational / Deployment Runbook Domain (Priority: TBD)
A governance domain (or standalone document) covering post-deployment operations, infrastructure security, and ongoing maintenance — the concerns that fall OUTSIDE AI coding governance but are critical for shipping and running production applications.

**Definition:** An operational runbook provides structured, actionable procedures for deploying, monitoring, maintaining, securing, and recovering production systems. It governs what happens AFTER code is written and deployed — infrastructure, operations, incident response, compliance monitoring, and cost management. Since AI will be a major part of our operational workflow (deploying, maintaining, fixing), the runbook must address AI-assisted operations specifically.

**Problem:** Our AI governance framework comprehensively covers how AI produces code (principles, methods, security checklists) but explicitly scopes out infrastructure and operations. Analysis of 30 viral "AI vibe coding security rules" revealed 3 solid practices we couldn't place because they're operational, not coding concerns. This gap will grow as AI becomes central to deployment, maintenance, and incident response workflows.

**Open question:** Do we need this? Our framework currently governs AI coding assistants. If AI increasingly handles deployment, monitoring, and incident response, operational governance becomes essential. Decision factors:
- Are we using AI for deployment/maintenance workflows? (If yes → need this)
- Is this a governance domain (principles + methods) or a standalone runbook document?
- Should it live inside the ai-governance framework or as a separate project artifact?

**Seed items (from vibe coding analysis):**
- DDoS protection and edge/CDN configuration (Cloudflare, Vercel)
- Email infrastructure security (SPF/DKIM/DMARC records)
- Backup automation and restoration testing

**Scope — Candidate sections (from industry research):**

**Deployment & Release:**
- Pre-deployment verification checklist and sign-offs
- Deployment sequence, ordering, and rollback procedures
- Database migration procedures
- Feature flag and canary/blue-green deployment strategies
- Post-deployment smoke tests and health checks
- Performance baseline establishment

**Infrastructure Security (Post-Deployment):**
- DDoS protection and WAF configuration
- TLS/SSL certificate management and rotation
- Firewall rules and network segmentation
- Access control verification (RBAC, least privilege)
- Email infrastructure (SPF/DKIM/DMARC)
- Secret rotation verification in production

**Monitoring & Observability:**
- Application performance monitoring (APM)
- Error rate and exception tracking
- Log aggregation, retention, and analysis
- Distributed tracing
- Alerting rules and escalation procedures
- Resource utilization tracking

**Incident Response & Recovery:**
- Detection procedures (what signals indicate a problem)
- Severity classification and triage
- Investigation procedures (logs, dashboards, traces)
- Mitigation strategies (rollback, failover, scaling, feature flags)
- Communication and escalation procedures
- Post-incident review (PIR) process

**Backup & Disaster Recovery:**
- Backup frequency and retention policy
- Backup validation and restore testing schedule
- Recovery time/point objectives (RTO/RPO)
- Geographic redundancy and failover procedures

**Ongoing Maintenance:**
- Patch and security update procedures
- Dependency update cadence
- Certificate renewal schedule
- Configuration drift detection
- Database maintenance (optimization, cleanup)
- Capacity planning and forecasting

**AI-Assisted Operations (Key Differentiator):**
- AI-powered anomaly detection and alerting
- AI-suggested remediation with human approval gates
- Automated scaling decisions and validation
- Confidence thresholds for autonomous operational actions
- Human-in-the-loop requirements for irreversible infrastructure changes
- Fallback procedures when AI recommendations fail
- Integration with AO-Series (Blast Radius Classification applies to ops actions too)

**Compliance & Audit:**
- GDPR/HIPAA/SOC2 operational compliance monitoring
- Audit trail verification and retention
- EU AI Act operational requirements (full enforcement Aug 2026)
- Evidence collection for compliance reviews
- Regulatory reporting schedules

**Cost Management:**
- AI API cost monitoring and budget alerts
- Cloud resource utilization and waste detection
- Auto-scaling policy optimization
- Cost allocation tracking

**Evaluation criteria:**
- Does our team use AI for operational tasks beyond coding?
- Is the scope large enough to warrant a governance domain (6+ principles) or is a single methods appendix sufficient?
- Would this complement or duplicate existing AO-Series (autonomous operations) in multi-agent domain?
- Are there industry frameworks (SRE, ITIL) we should align with rather than building from scratch?

**Implementation requirements:** Decision on format first (domain vs. document vs. appendix). If domain: follows standard domain creation process (principles + methods + extractor rebuild). If standalone: simpler — a markdown document with checklists and procedures, not indexed by governance MCP. Content changes only — no code changes expected unless we create a new domain requiring extractor updates.

**Relationship to existing governance:**
- Complements AI Coding domain (coding stops at "code is ready to deploy"; this picks up from there)
- Connects to AO-Series in Multi-Agent domain (autonomous operations principles apply to operational AI agents too)
- Connects to S4 (Security, Privacy, Compliance by Default) for compliance monitoring
- Connects to §5.11 (Zero Trust Production Deployment) which currently has some operational overlap

### 13. Backlog — Governance-Aware Output Compression (PostToolUse Hook) (Priority: LOW)

**Problem:** Long Bash output wastes context window tokens. External tools (e.g., RTK) fail §5.6.8 Third-Party Hook Vetting (single maintainer, command rewriting capability, information intermediary risk — the tool sits between the AI and its own output, creating an opportunity to suppress security warnings or governance enforcement messages).

**Approach:** Build a PostToolUse hook (matcher: Bash) that compresses verbose terminal output while preserving:
- Security-relevant lines (warnings, errors, vulnerability notices)
- Governance enforcement output (hook pass/fail messages)
- Structured data (JSON, table output)
- First/last N lines of long output with "[X lines compressed]" summary

Fits the "build our own" mode from §3.1.4 Tool Content Model — tighter governance integration justifies building over adopting an external tool that can't be trusted with output filtering.

**Trigger:** Context window pressure from terminal output becomes measurable (>20% of context consumed by Bash output in typical sessions). Not hitting this today.

**Cross-references:** §5.6.8 (information intermediary warning), §9.3.10 (building hooks — enforcement stack), §3.1.4 (Tool Content Model — "build our own" mode)

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
