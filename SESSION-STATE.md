# Session State

**Last Updated:** 2026-03-25
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Implement
- **Mode:** Standard
- **Active Task:** None (ready for next task)

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, nomic-embed-text-v1.5 768d, metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v2.6.0** (Constitution), **v3.14.0** (meta-methods), **v2.29.0** (ai-coding methods), **v2.3.5** (ai-coding principles), **v2.3.0** (multi-agent principles), **v2.15.0** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v2.1.0** (multimodal-rag principles), **v2.1.1** (multimodal-rag methods), **v1.0.0** (ui-ux principles), **v1.0.0** (ui-ux methods), **v1.1.0** (kmpd principles), **v1.1.0** (kmpd methods), **v2.5** (ai-instructions) |
| Tests | Run `pytest tests/ -v` for current count |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **163 principles + 621 methods + 4 references** (788 total; see `tests/benchmarks/` for current totals; taxonomy: 37 codes) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **4** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan) |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-03-27)

### Completed This Session (continued from 2026-03-26)

5. **Autonomous Experimentation Protocol** — multi-agent methods v2.14.0→v2.15.0
   - New §6.5: Autonomous Experimentation Protocol (Karpathy autoresearch pattern)
   - §6.5.1: Research Protocol Document (program.md pattern) with template
   - §6.5.2: Permission Configuration for autonomous operation (3 approaches)
   - §6.5.3: Experimentation Loop with termination conditions
   - §6.5.4: Results Logging (TSV audit trail)
   - Reference Library entry for autoresearch pattern

6. **Permission Configuration** — ai-coding methods v2.27.0→v2.28.0
   - New Appendix A.5: Permission Configuration (5 subsections)
   - Hook-permission interaction documented (hooks fire BEFORE permissions)
   - Day-to-day development allowlist with governance-critical file hard deny rule
   - Contrarian-reviewed: verified hooks+permissions complementary, not conflicting
   - Configured .claude/settings.local.json with comprehensive allowlist

7. **scaffold_project MCP Tool** — Backlog #2 COMPLETE
   - New MCP tool: two-step flow (preview → confirm) for project initialization
   - Core kit (4 files) or standard kit (6 files), code or document project types
   - SERVER_INSTRUCTIONS: AI checks for missing governance files on first interaction
   - 10 new tests, hardened from code/security review (format injection, symlink, partial failure)
   - Tool count: 15→16 (12 governance + 4 CE)

8. **Article evaluations** — RAG chunking (no gaps), Cloudflare Dynamic Workers (no gaps), autoresearch (led to §6.5)

9. **capture_reference MCP tool** (Tool #13) — creates Reference Library entries via tool call
   - YAML frontmatter generation, ID/domain validation, path traversal protection
   - Hardened from code-reviewer + security-auditor: _escape_yaml_value() helper, domain regex
   - 5 tests (TestCaptureReference)

10. **Substring collision regression test** — 1 test covering 8 collision-prone category_mapping pairs

11. **Pre-push Quality Gate Hook** — structural enforcement for subagent reviews
   - Blocks git push unless tests run AND risky changes reviewed by subagents
   - Risk-based triggers: core code files + new src/ files
   - Docs-only escape hatch, emergency skip via QUALITY_GATE_SKIP=true
   - Hard mode from day one per LEARNING-LOG lessons
   - Methods §5.1.7 (Subagent Review Triggers), §9.3.11 (Layer 5 enforcement)
   - LEARNING-LOG: graduated 2 lessons to methods
   - COMPLETION-CHECKLIST: subagent review triggers integrated
   - Reviewed by: code-reviewer + security-auditor before push

12. **Permission Configuration** — comprehensive .claude/settings.local.json allowlist
   - Reviewed by explore + security-auditor subagents for completeness and risk
   - docker push added to allowlist (L1 blast radius, own registry)

13. **Context Engine v2.0** — 3 phases shipped
   - Phase 1: YAML frontmatter parsing, metadata field on ContentChunk, metadata score boosting
   - Phase 2: Heading breadcrumb enrichment, chunk overlap (>15 lines), parent heading tracking
   - Phase 3: Embedding model upgrade BGE-small→nomic-embed-text-v1.5 (768d, 8K context)
   - metadata_filter parameter added to query_project tool
   - 18 dedicated Reference Library tests (test_reference_library.py)
   - Deep research: QAM, Anthropic Contextual Retrieval, Vectara NAACL 2025, markdown-vault-mcp
   - Contrarian reviewed: accepted benchmark baseline, overlap threshold, deferred char limit

14. **Article evaluations** — OpenBrain (not relevant), RAG chunking (no gaps), Cloudflare Dynamic Workers (no gaps)

### Previous Session Items (2026-03-26)

1. **Agentic Engineering Patterns Integration** — ai-coding methods v2.26.0→v2.27.0, principles v2.3.4→v2.3.5
   - Source: Willison (2026) "Agentic Engineering Patterns" guide evaluation
   - §5.2.2: Red/green TDD elevated to RECOMMENDED for AI-assisted development (5 research sources)
   - §7.6.2: Added "Run existing tests" as session start step 3
   - §5.13.7: New Code Comprehension via Linear Walkthrough technique
   - Skill Preservation: Added "cognitive debt" concept (Willison 2026) alongside exoskeleton effect

2. **Reference Library (Case Law)** — meta-methods v3.13.0→v3.14.0 (NEW STRUCTURAL COMPONENT)
   - New TITLE 15: Reference Library — curated precedent system alongside principles/methods/appendices
   - Legal analogy: Case Law = concrete artifacts that worked in practice, indexed for retrieval and recombination
   - Entry template: YAML frontmatter (6 required + 6 recommended fields) + markdown body
   - Three intake paths: auto-capture (rule-based), staged suggestion (AI proposes), manual capture
   - Maturity pipeline: seedling → budding → evergreen (digital garden model)
   - Currency tracking: current/caution/deprecated/archived (KeyCite model) + decay classes
   - Code: ReferenceEntry/ScoredReference models, YAML extractor, retrieval integration, server output formatting
   - 3 example entries for ai-coding + _criteria.yaml auto-capture rules template
   - Updated §9.3.1 Truth Source Hierarchy (new level 4: Reference Library)
   - Deferred to v2: capture_reference MCP tool, auto-capture engine, staging workflow, decay enforcement

3. **Self-Review (3 rounds)** — comprehensive dogfooding audit of entire framework
   - Round 1 (4 agents): 36 findings, 11 fixed — propagation gaps, N-Series cross-ref, README counts
   - Round 2 (4 agents): 12 findings, 7 fixed — CRITICAL extraction bug (6/13 KMPD null series_code from substring collision), security hardening (project_path scope), principle quality
   - Round 3 (5 agents): 8 findings, 3 fixed — README counts, env var scope bypass, macOS /tmp mismatch
   - Post-Reference-Library review (5 agents): security scan gap, frontmatter parsing, symlink protection

### Previous Session (2026-03-25)

1. **KM&PD v1.0.0 → v1.1.0** — Added Situation Index (17 routing entries), expanded cross-domain Storytelling integration (A-Series, ST-Series, pacing/progressive revelation, scope boundary)
2. **Comprehensive Self-Review** — 4 subagents in parallel (coherence auditor, validator, contrarian reviewer, code reviewer). 36 findings total. Fixed 11 accepted findings:
   - CRITICAL: KM&PD "N-Series" cross-reference → corrected to "ST-Series" (3 files)
   - Propagation gaps: README/SPEC/ARCH domain counts (6→7), AGENTS.md version (v2.22→v2.26), file trees (+7 missing files)
   - Code: KMPD series headers added to extractor `is_series_header` + `skip_keywords`, sanitization regex fix, `exc_info=True` added to error handler
   - SESSION-STATE pruned: ~130 lines of historical session summaries removed per §7.1.5
3. **Cowork Brief** — Extracted KM&PD book + consulting practice items for Cowork handoff (tasks 3-4: book design, consulting go-to-market, trademark investigation)
4. **964 tests passing**, index rebuilt, spot-check verified (QA2 surfaces correctly)

### Previous Session (2026-03-22)

1. **Context Engine Cross-Environment Compatibility** — CE v1.3.0, ai-coding methods v2.22.0→v2.23.0
   - **Catalyst:** Claude Cowork VM could not use context engine — permission errors on query, CWD=/ indexing root filesystem
   - **Phase 1: Read-only mode** — `ReadOnlyFilesystemStorage` subclass, `readonly` flag on Indexer/ProjectManager/Server, `AI_CONTEXT_ENGINE_READONLY` env var with auto-detection, BM25-only fallback
   - **Phase 1 fix: project_path parameter** — Added `project_path` to `query_project`, `index_project`, `project_status` tools. Resolution: args > `AI_CONTEXT_ENGINE_DEFAULT_PROJECT` env var > CWD. Fixes Cowork CWD=/ issue.
   - **Phase 2: Standalone watcher daemon** — `context-engine-watcher` CLI with --all/--projects/--log-file. Heartbeat file (60s), PID file, graceful SIGTERM/SIGINT. Registered in pyproject.toml.
   - **Phase 3: Platform service installer** — `context-engine-service` CLI (install/uninstall/status/logs). macOS launchd plist, Linux systemd user service, Windows Task Scheduler. Auto-detects platform.
   - **Phase 4: Framework documentation** — Appendix G.11 (Cross-Environment Compatibility), G.12 (Standalone Watcher Daemon), G.13 (Platform Service Installation). Changelog entry.
   - **Phase 5: Installation docs** — README rewrite with Quick Start (AI-Assisted), Manual Setup, Sandboxed Environments sections. API.md updated with new env vars, CLI tools, project_path parameters. SERVER_INSTRUCTIONS Setup & Maintenance section for AI-assisted setup detection.
   - Key insight: Cowork MCP servers run on the host, not inside the VM. The issue was CWD=/ not sandbox writes.
   - Installed service on macOS: watching 4 projects, auto-starts on login
   - 964 tests passing (877 original + 34 readonly + 21 daemon + 32 service), 0 failures
   - Files changed: 15 files, ~2400 lines added
   - 5 new CLI entry points total: ai-governance-mcp, ai-governance-extract, ai-context-engine, context-engine-watcher, context-engine-service

2. **Folder-Based AI Environment Support** — ai-coding methods v2.23.0→v2.24.0
   - New Appendix L: `_ai-context/` folder convention for Cowork, ChatGPT Desktop, any folder-based LLM
   - L.1 Overview, L.2 Folder Structure (`_ai-context/` rationale), L.3 README.md Templates (standalone + hybrid redirect), L.4 Cowork Project Instructions template, L.5 Bootstrapping Protocol (conversational/manual/MCP tool), L.6 Non-Code Session State variant, L.7 Cross-Tool Coexistence matrix
   - Cross-references: §1.5.1, §1.5.5 (+_ai-context row), §7.8.4 (+folder variant), Situation Index (+1), Cold Start Kit (+Scenario E)
   - Partially resolves Backlog #2 (Project Initialization Part B) for folder-based environments
   - Validated by: coherence-auditor, validator subagents
   - 964 tests passing, 0 failures

3. **Repository Security Configuration** — ai-coding methods v2.24.0→v2.25.0
   - New §6.4.10: 10-item universal checklist (branch protection → CODEOWNERS), 3 enforcement tiers, cross-platform table (GitHub/GitLab/Bitbucket)
   - New §6.4.11: CodeQL workflow template, query suite guidance, platform alternatives (GitLab SAST, Semgrep, Bandit)
   - Appendix H expanded 14→16 items, §5.3.3 cross-ref, Situation Index +2

4. **Design-Before-Build & Tool Discovery** — ai-coding methods v2.25.0→v2.26.0
   - §2.4 UX Elaboration: OPTIONAL→IMPORTANT for UI-facing projects, anti-pattern description, Figma MCP cross-reference
   - §3.1.4 Tool Content Model: added "tools we may use" prospective evaluation path with user consent
   - Catalyst: Sean Kochel newsletter analysis on vibe-coding rebuild loops

5. **Skill Preservation (Exoskeleton Effect)** — ai-coding principles update
   - Added Skill Preservation subsection to Human-AI Collaboration principle
   - Cites Shen & Tamkin 2026 (Anthropic), Macnamara et al. 2024, MIT Media Lab EEG study
   - Three high-performing + three low-performing AI interaction patterns
   - Training domain backlog updated with contrarian reviewer REVISIT verdict

6. **Intent Discovery** — Constitution v2.5.0→v2.6.0 (NEW CONSTITUTIONAL PRINCIPLE)
   - New C-Series principle: assess whether stated request reflects actual underlying need
   - Proportional skepticism: Dig/Proceed signals calibrate investigation depth
   - Evidence: VOC/CTQ (Six Sigma), Kano model, Five Whys, XY Problem, IEEE 29148, McKinsey, Zou et al. 2022, Zhang/Knox/Choi ICLR 2025
   - 6 named traps (Therapist, I Know Better, Interrogation, Infinite Regress, Solution Prejudice, False Positive)
   - Relationship: sibling to Discovery Before Commitment (DBC explores within frame, ID questions the frame)
   - Contrarian review: MODIFY accepted — moved signal list to Operational Considerations, added domain calibration
   - Index: 150 principles + 579 methods (729 total)
   - 964 tests passing

7. **Knowledge Management & People Development Domain — Design** (no code yet)
   - Renamed from "Training & Instructional Design" — training is one activity within the scope
   - Jason's framework (novel synthesis): two pillars (Lead People / Manage Process), continuous knowledge scale, derivation chains, empowerment model (Luftig/BPE)
   - Deep research confirmed: no published framework combines all elements
   - Maturity model designed (6 levels), scope boundary defined, verification model established
   - 8 Q&A rounds captured, 18 book-worthy themes documented
   - Full design document: `.claude/plans/peaceful-pondering-dahl.md`
   - **COMPLETED:** Principles doc (13 principles, 4 series, 13 failure modes) + Methods doc (7 sections + appendices)
   - Validated by: validator (2 rounds), coherence-auditor (2 rounds), contrarian-reviewer (3 rounds: design, final, QA2)
   - All template fields complete, all constitutional derivations verified, all cross-references valid

11. **License Change** — MIT → Apache 2.0 (code) + CC-BY-NC-ND 4.0 (framework content)
    - Protects proprietary framework content while keeping code open
    - Research confirmed: publish framework (builds market), protect brand (trademark), sell implementation (consulting)
    - EOS/Sinek/Lencioni/Collins/Brown model: "give away the what, sell the how"

12. **QA2: Artifact Adoption Fitness** + **KM-F13: Adoption Failure**
    - New principle: artifacts must WIN the adoption competition against informal alternatives
    - Contrarian reviewed: MODIFY accepted (design quality as principle, co-creation stays in methods §7.4)
    - Methods §2.5 Adoption Fitness Check with 5-item checklist
    - Operationalizes Mayer's Multimedia Learning Principles

13. **Conversational Q&A Default Fix**
    - Problem: AI defaults to structured option lists instead of freeform dialogue for exploratory questions
    - Root cause: behavioral compliance gap, not framework content gap (Progressive Inquiry Protocol §7.9 already correct)
    - Fix: Added "Conversation Style" section to SERVER_INSTRUCTIONS and CLAUDE.md
    - Hooks evaluated but rejected (detecting question type in shell script unreliable)

14. **Final KM&PD Validation** — validator + coherence auditor on complete domain (PASS after 8 minor fixes)

8. **Domain Creation Criteria (§5.1.0)** — meta-methods update
   - Added "When to Create a Domain" section: active practice, planned practice, OR significant possibility
   - The test is "will AI-specific failure modes exist?" not "have I already hit them?"
   - Proactive governance is valid — building codes before construction

9. **Evidence sources filed** — 5 articles (Lopopolo/OpenAI, LangChain, Anthropic, Shen & Tamkin, Macnamara) validating existing framework patterns

10. **Agent-legibility + automated hygiene** — two small additions to ai-coding methods from OpenAI Codex article

*Previous session summaries pruned per §7.1.5 (session state is transient). Decisions and lessons routed to PROJECT-MEMORY.md and LEARNING-LOG.md. Full history available via `git log`.*

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

### 2. Backlog — Project Initialization Part B — COMPLETE (2026-03-27)
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

**Partial resolution (2026-03-22):** Appendix L (ai-coding methods v2.24.0) provides conversational bootstrapping for folder-based environments. The Cowork Project Instructions template includes "If _ai-context/ does not exist, ask if the user wants to set up AI memory." This addresses the folder-based bootstrapping gap. The `scaffold_project` MCP tool remains open for CLI-based environments.

### 3. Backlog — Quantized Vector Search (Deferred)
Not needed at current scale (10K-100K vectors, 1-5ms brute-force latency). Revisit when Context Engine reaches 500K+ vectors (multi-project indexing) or users report perceptible latency.

**Trigger conditions:** 500K+ vectors loaded, OR user-reported perceptible query latency (>100ms).

**Phased approach:** See PROJECT-MEMORY.md > Roadmap > Quantized Vector Search for full details (product quantization → scalar quantization → HNSW index progression).

### 4. Backlog — Knowledge Management & People Development Domain — COMPLETE (2026-03-25)
Domain v1.1.0 shipped. 13 principles (KA1-4, TL1-4, PD1-3, QA1-2), 13 failure modes, 7 methods sections, Situation Index (17 entries), cross-domain storytelling integration. Design document moved to Jason's personal documents folder for book/consulting work.

All design material is in Jason's personal documents folder (plan file). Domain documents: `kmpd-domain-principles-v1.1.0.md`, `kmpd-methods-v1.1.0.md`.

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
