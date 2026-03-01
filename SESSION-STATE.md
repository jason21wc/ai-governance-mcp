# Session State

**Last Updated:** 2026-02-28
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Implement
- **Mode:** Standard
- **Active Task:** None — Tiered Principle Activation Phase 1.5 complete (Phase 2 not needed)

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v1.2.1** (watcher auto-start on boot fix) |
| Content | **v2.4.1** (Constitution), **v3.12.0** (meta-methods), **v2.17.1** (ai-coding methods), **v2.3.4** (ai-coding principles), **v2.1.1** (multi-agent principles), **v2.12.3** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v2.1.0** (multimodal-rag principles), **v2.1.1** (multimodal-rag methods), **v2.5** (ai-instructions) |
| Tests | **810 pass** (non-slow), 0 failures |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **15 MCP tools** (11 governance + 4 context engine) |
| Domains | **5** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag) |
| Index | **124 principles + 498 methods** (622 total; see `tests/benchmarks/` for current totals; taxonomy: 27 codes) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **3** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check with recency window) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | **MRR=0.664**, **Recall@5=0.850**, **Recall@10=1.000** (v1.1.0, 16 queries, v2.0 baseline `ce_baseline_2026-02-14.json`, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-02-28)

### Completed This Session

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

**Part C: Effectiveness Analytics** (measurement)
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

### 5. Backlog — Add UI/UX Domain (Priority: TBD, Recommended: 1st)
New governance domain for UI/UX design principles and methods. **Separate domain** from ai-coding — ai-coding §2.4/§2.5 cover *process* (when to do UX work); this domain covers *substance* (what good UX is).

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

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
