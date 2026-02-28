# Session State

**Last Updated:** 2026-02-28
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Complete
- **Mode:** Standard
- **Active Task:** None — all changes committed and pushed

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v1.2.0** (eager watcher startup, not_loaded status) |
| Content | **v2.4.1** (Constitution), **v3.12.0** (meta-methods), **v2.17.1** (ai-coding methods), **v2.3.4** (ai-coding principles), **v2.1.1** (multi-agent principles), **v2.12.3** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v2.1.0** (multimodal-rag principles), **v2.1.1** (multimodal-rag methods), **v2.5** (ai-instructions) |
| Tests | **759 pass** (non-slow), 0 failures |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **15 MCP tools** (11 governance + 4 context engine) |
| Domains | **5** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag) |
| Index | **124 principles + 498 methods** (622 total; see `tests/benchmarks/` for current totals; taxonomy: 27 codes) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **3** (PostToolUse CI check, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | **MRR=0.664**, **Recall@5=0.850**, **Recall@10=1.000** (v1.1.0, 16 queries, v2.0 baseline `ce_baseline_2026-02-14.json`, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-02-28)

### Completed This Session

1. **Confirmed Context Engine v1.2.0 realtime mode working**
   - Verified `index_mode: "realtime"` env var picked up after Claude Code restart
   - Watcher initially showed "stopped" — re-index resolved it, watcher now "running"
   - Index refreshed: 138 files / 3,427 chunks (up from 129/3,339)
   - Cleared pending manual action from previous session

2. **Atlas framework comparison** (research, no changes)
   - Researched syahiidkamil's ATLAS (Adaptive Technical Learning and Architecture System, 280 GitHub stars)
   - Compared against our ai-coding domain (12 principles, 6,665 lines of methods, 80+ research citations)
   - Ran contrarian reviewer on 5 candidate incorporations — all rejected or reframed
   - Conclusion: Atlas reveals no gaps in our framework; our evidence-based, failure-mode-grounded approach covers all substantive concerns with greater rigor
   - Broader web research confirmed our framework aligns with 2026 context engineering best practices

3. **Three new candidate domains added to backlog**
   - **#7 Training & Instructional Design** — replaced thin "Procedures" placeholder; covers SOPs, tutorials, onboarding, courses, assessments, job aids; evidence base includes TWI, Bloom's Taxonomy, ADDIE, Kirkpatrick, Merrill, Gagné, Mayer, Toyota Kata, spaced repetition research
   - **#8 UI/UX** — interactive software interfaces (web sites, web apps, desktop apps, mobile apps); scoped separately from ai-coding (§2.4/§2.5 cover process, this covers substance); includes Figma MCP connectors and AI tooling integration
   - **#9 Visual Communication** — presentations, documents, reports, infographics, print design; separate from UI/UX due to different failure mode clusters; evidence base includes Tufte, Duarte, Reynolds

## Next Actions

### 1. Backlog — Enforcement & Compliance Infrastructure (Priority: MEDIUM)
Unified initiative covering enforcement improvements, cross-platform reach, and effectiveness measurement. Rolled up from four related items — tackling together enables systems-level view, avoids unexpected interactions, and identifies synergies between approaches.

**Goal:** Empirical evidence that our enforcement layers work, measurable compliance rates, and governance enforcement that works across any AI client — not just Claude Code.

**Part A: Hook Improvements** (tactical, low effort)
Two improvements identified by contrarian review:
1. **Recency heuristic** — PreToolUse hook currently uses session-level check (any governance/CE call in transcript = pass). For long sessions with task pivots, scan only the last ~500 transcript lines instead. One-line change to Python scanning logic (`collections.deque(f, maxlen=500)`).
2. **Suppress reminder after governance established** — UserPromptSubmit hook currently injects ~225 tokens on every prompt regardless. Add transcript check (same logic as PreToolUse) to suppress the reminder once both `evaluate_governance()` and `query_project()` have been called. Saves ~11K tokens/session over 50 turns.

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

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
