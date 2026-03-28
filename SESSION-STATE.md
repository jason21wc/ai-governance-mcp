# Session State

**Last Updated:** 2026-03-28
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
| Content | **v2.7.0** (Constitution), **v3.14.1** (meta-methods), **v2.30.0** (ai-coding methods), **v2.3.6** (ai-coding principles), **v2.3.1** (multi-agent principles), **v2.15.0** (multi-agent methods), **v1.1.2** (storytelling principles), **v1.1.1** (storytelling methods), **v2.1.0** (multimodal-rag principles), **v2.1.1** (multimodal-rag methods), **v1.0.0** (ui-ux principles), **v1.0.0** (ui-ux methods), **v1.1.0** (kmpd principles), **v1.1.0** (kmpd methods), **v2.5** (ai-instructions) |
| Tests | Run `pytest tests/ -v` for current count |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **164 principles + 632 methods + 4 references** (800 total; see `tests/benchmarks/` for current totals; taxonomy: 37 codes) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **4** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-03-28)

### Completed This Session

17. **Dependency CVE Remediation** — 33→2 unfixable vulnerabilities
   - Direct deps: mcp 1.25→1.26, requests >=2.33.0, Pillow >=12.1.1,<13
   - 16 transitive deps upgraded, CI pip-audit scoped to project deps
   - Security-auditor reviewed, 969 tests passing

18. **Backlog Restructure** — 7 completed items collapsed, 4 new items (#14-17) added, all normalized

19. **GitHub Actions Node.js 20→24 Migration** (Backlog #17) — 19 SHA pins updated across 3 workflows

20. **Layer 3 Governance Enforcement** (Backlog #1B Phase 1)
   - stdio JSON-RPC interceptor proxy (enforcement.py)
   - GovernanceEnforcer state machine + StdioProxy protocol handler
   - 29 tests, hardened from code-reviewer + security-auditor (8 fixes)
   - ADR-14 in PROJECT-MEMORY.md (contrarian caught scope reduction)
   - Architecture section in ARCHITECTURE.md with 3-layer diagram

21. **Systemic Thinking Constitutional Amendment** (Backlog #18)
   - New C-Series meta-principle (#47) in constitution v2.7.0
   - Federal preemption cleanup: 2 HIGH trims + 6 MEDIUM references across 5 documents
   - 5 documents version-bumped, old versions archived
   - Principle-authoring checklist added to COMPLETION-CHECKLIST
   - 6 subagent reviews: 2 contrarian (incl meta-dogfood), 2 coherence, 1 validator
   - New backlog items: #19 (Rampart), #20 (Pin Currency), #21 (Authoring Checklist Enforcement)

22. **CE Phase 4 Investigation** — MRR gap was benchmark error, not algorithm
   - Diagnosed 3 outlier queries: docs ranked above code (correct for natural language queries)
   - Corrected benchmark expectations: MRR 0.646 → 0.802 with zero code changes
   - RRF + reranking deferred — research found tuned linear beats RRF, ms-marco wrong for code
   - Systemic Thinking prevented building unnecessary algorithmic complexity

### Previous Session (2026-03-27)

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

15. **Governance Enforcement Improvements** — root cause analysis of compliance gaps
   - COMPLETION-CHECKLIST: tiered ENFORCED (6) vs BEST-EFFORT (6) items
   - TestReadmePropagation: CI assertion for README tool count
   - Governance recency window: 200→500
   - LEARNING-LOG: normative drift under agentic pressure (arxiv 2603.14975)

16. **Dependency CVE Remediation** — 33→2 unfixable (conda-managed PyJWT, no-fix pygments)
   - Direct deps: mcp 1.25→1.26, requests >=2.33.0, Pillow >=12.1.1
   - Transitive: upgraded aiohttp, authlib, cryptography, starlette, python-multipart, filelock, flask, markdown, nbconvert, nltk, pyasn1, pynacl, pyopenssl, tornado, ujson, urllib3, werkzeug, wheel, virtualenv
   - CI: pip-audit scoped to project deps only (not entire conda env)
   - 969 tests passing after mcp 1.26 upgrade

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

### Completed Backlog Items

| # | Item | Completed |
|---|------|-----------|
| 1A | Hook Improvements | 2026-02-28 |
| 1C | Effectiveness Analytics | 2026-03-01 |
| 2 | Project Initialization (scaffold_project) | 2026-03-27 |
| 4 | KM&PD Domain v1.1.0 | 2026-03-25 |
| 5 | UI/UX Domain v1.0.0 | 2026-03-08 |
| 8 | Subagent Output Framing (Advisory) | 2026-02-28 |
| 9 | Tiered Principle Activation (Phases 0-1.5; Phase 2 cancelled) | 2026-03-01 |

### Open Backlog

#### 1B. Model-Agnostic Governance Enforcement (Priority: MEDIUM) — Phase 1 COMPLETE (2026-03-28)

**Phase 1 (COMPLETE):** stdio JSON-RPC interceptor proxy (`enforcement.py`). Enforces governance preconditions on the governance server's own action tools. Zero new dependencies, works with any MCP client. Entry point: `ai-governance-proxy`. ADR-14 in PROJECT-MEMORY.md.

**Phase 2 (OPEN):** Cross-MCP enforcement — enforcing governance before tool calls to OTHER MCP servers (GitHub, filesystem, etc.), not just the governance server.

**Contrarian finding:** Original plan proposed internal call_tool checks on already-gated tools — caught by contrarian-reviewer as scope reduction that dodged the hard problem. Led to plan revision (ADR-14).

#### 1B-P2. Cross-MCP Governance Enforcement (Priority: DEFERRED)

**Status:** Deferred per Systemic Thinking analysis (2026-03-28). Contrarian review found:
1. MCP stdio connections are fundamentally isolated (protocol-level architecture) — shared state is a workaround, not a structural fix
2. Shared state files introduce race conditions, session identity problems, and security gaps
3. Claude Code hooks (Layer 2) already cover Bash/Edit/Write at ~100% — the incremental value is small
4. Better alternatives exist: expand Claude Code hooks for MCP tool names, or Rampart (#19) at the shell level

**Trigger:** When Jason encounters a real situation where a non-Claude client calls a third-party MCP server's action tool without governance being evaluated, and the existing hooks don't catch it. Evidence of the gap in practice, not theoretical coverage concern.

#### 3. Quantized Vector Search (Priority: DEFERRED)

**Problem:** Brute-force vector search will become slow at scale.

**Trigger conditions:** 500K+ vectors loaded, OR user-reported perceptible query latency (>100ms). Not hitting this today (10K-100K vectors, 1-5ms latency).

**Phased approach:** Product quantization → scalar quantization → HNSW index progression. See PROJECT-MEMORY.md > Roadmap > Quantized Vector Search for full details.

**Implementation requirements:** Changes to retrieval.py and indexer. Benchmark before/after. No urgency.

#### 6. Visual Communication Domain (Priority: LOW)

**Problem:** No governance for non-coding visual artifacts: presentations, documents, reports, infographics, print design. Separate from UI/UX because different failure mode clusters, evidence bases, and tooling.

**Scope — Artifact types:** Presentations (slide decks, pitch decks), documents/reports, infographics/data visualizations, print design.

**Principles (candidate areas):**
- Narrative flow and story structure
- Information density and cognitive load (Tufte's data-ink ratio)
- Visual hierarchy for static layouts
- Audience-appropriate design (executive vs. technical vs. public)
- Brand consistency and style guide adherence
- Data visualization integrity (no misleading charts)
- Accessibility in documents (heading structure, alt text, contrast)

**Methods (candidate areas):**
- Slide deck composition workflow (outline → structure → design → review)
- Presentation review and validation gates
- Template and brand compliance checking
- Data visualization best practices
- Document accessibility auditing

**Evidence base:** Tufte (data visualization), Duarte (presentation design), Reynolds (Presentation Zen), WCAG document accessibility, Cleveland & McGill (data viz research).

**AI-specific failure modes:** Text-heavy slides, inconsistent styling, misleading visualizations, poor narrative structure, brand guideline violations.

**Implementation requirements:** Domain config in `domains.json`, principle + methods documents, extractor support, index rebuild, tests. Standard domain creation process per COMPLETION-CHECKLIST.

#### 7. Security Content Currency Process (Priority: LOW)

**Problem:** AI security evolves rapidly — new tool categories, shifting attack patterns, standards updates. Our security content (§5.3-§5.11, security-auditor subagent, pre-release checklist) is comprehensive today but will go stale without a review cadence.

**Scope — What gets reviewed:**
- Methods coverage (§5.3 Security Validation, §5.6 AI Coding Tool Security, §5.7 Application Security Patterns, §5.8 Domain-Specific Security, §5.11 Zero Trust)
- Security-auditor subagent definition and checklist
- Pre-release security checklist in CLAUDE.md
- Evidence base citations — are referenced sources still current?

**Framework pattern for tool-specific content:**
- **Generalized guidance** (tool-agnostic) → methods sections
- **Specific tool guidance** (tools we actively use) → appendix or tool-specific subsection
- Don't aim for comprehensive coverage — capture what we actively use

**Inputs to monitor:**
- New AI security tool categories and independent benchmarks (OWASP, NIST)
- Emerging attack patterns (agent-specific threats, MCP-specific vulnerabilities)
- Standards updates (OWASP Top 10 revisions, CWE/SANS updates)
- Our own security-auditor findings across sessions (recurring gaps = content gap)

**Current status of AI scanner question:** Claude Code Security launched 2026-02-20. Interim guidance in §5.3.3, §5.3.5, §6.4.9. Waiting for vendor-independent accuracy data.

**Cadence:** TBD — quarterly review or event-triggered (major tool launch, OWASP update).

**Implementation requirements:** Not a code change — methods-level practice. May result in: updated methods, new appendices, revised evidence base citations, updated security-auditor subagent.

#### 9P3. Tiered Principle Activation — Phase 3: Accountable Reasoning (Priority: LOW, DEFERRED)

**Problem:** Phases 0-1.5 shipped and Phase 2 was cancelled. Remaining: formal combined principle for accountable reasoning.

**Scope:** After Phase 1 proves valuable over time, consider a formal combined principle that synthesizes the accountable reasoning pattern. Until then, tier config synthesizes both existing IDs.

**Trigger:** When universal floor proves valuable across 20+ sessions and the pattern stabilizes.

**Implementation requirements:** New principle in constitution, methods guidance, index rebuild.

#### 10. UI/UX Tool-Specific Integration Guides (Priority: LOW, Usage-Driven)

**Problem:** UI/UX domain methods §8 needs tool-specific appendices as tools are adopted.

**Candidate tools (researched 2026-03-08, production-grade):**
- **Figma Official MCP** — design context/tokens + rendered UI. Token cost: 600K+ for large designs.
- **Storybook MCP** (official) — component manifests with metadata, variants, token bindings.
- **Deque Axe MCP** (official) — accessibility auditing. Would make ACC1-ACC3 enforceable in-loop.
- **Microsoft Playwright MCP** (official) — browser automation, screenshots. Enables RD1/RD2 responsive validation.
- **Percy via BrowserStack MCP** — visual regression with AI review. 3x faster, 40% false positive reduction.
- **Playwright-Lighthouse MCP** (community) — Lighthouse audits + Playwright. Maps to §3.6 Core Web Vitals.

**Trigger:** When Jason adopts any of these tools in a real project.

**Known risks:** Token cost (Figma 15x estimate gap), design data privacy through AI APIs, fidelity gaps, design system maturity prerequisite.

**Implementation requirements:** Integration guide per tool with observed failure modes and token cost data. Content changes only.

#### 11. Autonomous Operations Domain (Priority: FUTURE)

**Problem:** Autonomous agent patterns may outgrow multi-agent AO-Series (currently 4 principles, 4 methods sections).

**Trigger:** When autonomous operation governance needs exceed multi-agent's scope — e.g., financial compliance (SOX), industry-specific regulatory frameworks, agent marketplace governance, cross-organization federation, or AO-Series grows beyond 6-8 principles.

**Candidate additions beyond current AO-Series:**
- Financial governance and audit compliance (SOX, SOC 2)
- Industry-specific regulatory frameworks (HIPAA, FINRA)
- Agent marketplace and discovery governance
- Cross-organization agent trust and federation
- Agent lifecycle management (provisioning, retirement, succession)

**Evidence to watch:** Regulatory frameworks specifically targeting autonomous AI agents. Current evidence base (CNBC, Strata, Singapore IMDA, UC Berkeley 2026) supports AO-Series but not yet a full domain.

**Implementation requirements:** Standard domain creation process. Decision on scope first.

#### 12. Operational / Deployment Runbook Domain (Priority: TBD)

**Problem:** Our framework covers how AI produces code but scopes out infrastructure and operations. Analysis of 30 viral "AI vibe coding security rules" revealed 3 solid practices we couldn't place because they're operational concerns. Gap will grow as AI handles deployment, maintenance, and incident response.

**Open question:** Do we need this? Decision factors:
- Are we using AI for deployment/maintenance workflows?
- Governance domain (principles + methods) vs. standalone runbook document?
- Inside the ai-governance framework or separate project artifact?

**Scope — Candidate sections:**
- Deployment & Release (verification, rollback, migrations, feature flags, smoke tests)
- Infrastructure Security (DDoS, TLS, firewalls, RBAC, email infra, secret rotation)
- Monitoring & Observability (APM, errors, logs, tracing, alerting)
- Incident Response & Recovery (detection, triage, mitigation, communication, PIR)
- Backup & Disaster Recovery (frequency, validation, RTO/RPO, failover)
- Ongoing Maintenance (patching, deps, certs, drift detection, capacity)
- AI-Assisted Operations (anomaly detection, AI remediation with approval gates, confidence thresholds)
- Compliance & Audit (GDPR/HIPAA/SOC2, audit trails, EU AI Act Aug 2026)
- Cost Management (AI API costs, cloud waste detection, auto-scaling optimization)

**Relationship to existing governance:**
- Complements AI Coding domain (coding stops at "ready to deploy"; this picks up from there)
- Connects to AO-Series (autonomous operations principles apply to operational AI agents)
- Connects to S4 (Security, Privacy, Compliance by Default)
- Overlaps with §5.11 (Zero Trust Production Deployment)

**Implementation requirements:** Decision on format first. If domain: standard creation process. If standalone: simpler markdown document, not indexed by governance MCP.

#### 13. Governance-Aware Output Compression (Priority: LOW)

**Problem:** Long Bash output wastes context window tokens. External tools (e.g., RTK) fail §5.6.8 Third-Party Hook Vetting (information intermediary risk — could suppress security warnings or governance enforcement messages).

**Approach:** PostToolUse hook (matcher: Bash) that compresses verbose output while preserving security-relevant lines, governance enforcement output, structured data, and first/last N lines with "[X lines compressed]" summary.

**Trigger:** Context window pressure from terminal output becomes measurable (>20% of context consumed by Bash output). Not hitting this today.

**Cross-references:** §5.6.8 (information intermediary warning), §9.3.10 (enforcement stack), §3.1.4 (Tool Content Model — "build our own" mode).

**Implementation requirements:** PostToolUse hook script, tests, documentation. Fits "build our own" mode per §3.1.4.

#### 14. Storytelling Domain 9-Field Template Migration (Priority: LOW)

**Problem:** Storytelling principles reference a 9-field character/scene template structure but the domain content hasn't been migrated to fully use this format. Content migration needed to align principles with methods.

**Scope:** Review storytelling principles and methods documents. Identify sections referencing the 9-field template. Migrate content to consistently use the template structure. Validate cross-references with KM&PD storytelling integration (A-Series, ST-Series).

**Implementation requirements:** Content changes to storytelling principles/methods documents. Index rebuild. Coherence-auditor review to verify cross-domain references remain valid (KM&PD storytelling integration, multi-agent narrative patterns).

#### 15. Context Engine Phase 4 — Advanced Retrieval (Priority: DEFERRED)

**Status:** Investigated 2026-03-28. Systemic Thinking analysis found the MRR gap (0.646) was a benchmark specification error, not a retrieval algorithm problem. Correcting 3 benchmark queries (accepting documentation files as valid results for natural language queries) raised MRR from 0.646 to 0.802 with zero code changes.

**Research findings (contrarian + online):**
- Tuned weighted linear beats RRF when eval data exists (ACM study) — we have eval data
- ms-marco-MiniLM-L-6-v2 has ~20-point gap vs code-trained rerankers on CodeSearchNet — wrong model for this corpus
- RRF bonus scale mismatch would be a correctness bug (bonuses calibrated for [0,1] vs RRF's [0.016-0.033] range)
- LanceDB not needed until 100x+ growth (currently 800 vectors, <1ms queries)

**Remaining scope (if MRR needs to improve further):**
1. Weight grid search (5 configs, 30 min) — simplest intervention
2. Score normalization (2 lines) — fix distribution mismatch without algorithm change
3. RRF with scaled bonuses — only if simpler fixes insufficient
4. Cross-encoder with jina-reranker-v2 or bge-reranker-v2-m3 — only if >3-5 MRR point improvement

**Trigger:** When real-world retrieval quality complaints emerge, or MRR drops below 0.75 on corrected benchmark.

#### 16. Governance Server Embedding Model Upgrade (Priority: MEDIUM, DEFERRED)

**Problem:** Governance server still uses BGE-small-en-v1.5 (384d) while Context Engine upgraded to nomic-embed-text-v1.5 (768d, 8K context, MTEB 86.2). Upgrading would improve semantic retrieval quality for governance queries.

**Scope:** Upgrade `sentence-transformers` model in `extractor.py` and `retrieval.py` from `BAAI/bge-small-en-v1.5` to `nomic-embed-text-v1.5`. Requires full index rebuild since embedding dimensions change (384→768).

**Open questions:**
- Is the quality improvement measurable for governance queries specifically? (Governance documents are shorter and more structured than general code — BGE-small may be sufficient.)
- What's the model download size and cold-start latency impact?
- Should both servers (governance + CE) use the same model for consistency?

**Trigger:** After CE Phase 4 stabilizes, or if governance retrieval quality issues are reported.

**Implementation requirements:** Update `config.py` defaults (model name, dimensions), `extractor.py` (model loading), `retrieval.py` (ALLOWED_EMBEDDING_MODELS). Full index rebuild. Benchmark before/after with `tests/benchmarks/retrieval_quality.json`. Update SBOM.

#### 17. GitHub Actions Node.js 20 → 24 Migration — COMPLETE (2026-03-28)

Updated 19 action SHA pins across 3 workflow files (ci.yml, docker-publish.yml, codeql.yml) to Node.js 24-compatible versions. All actions re-pinned to full commit SHAs per supply chain security practice.

#### 18. Systemic Thinking Principle — COMPLETE (2026-03-28)

Constitutional amendment: added Systemic Thinking meta-principle to C-Series (47th principle). Federal preemption cleanup across 5 documents (2 HIGH trims, 6 MEDIUM references). Principle-authoring checklist added to COMPLETION-CHECKLIST. 6 subagent reviews (2 contrarian, 2 coherence, 1 validator, 1 meta-dogfood). ADR in Historical Amendments v2.7.0.

#### 19. Rampart Integration — Client-Side Enforcement (Priority: LOW, Usage-Driven)

**Problem:** Layer 3 (proxy) enforces at the MCP protocol level. Rampart (github.com/peg/rampart) enforces at the shell/client level — complementary coverage. Ships with 40+ rules for credential theft, exfiltration, and destructive commands.

**Scope:** Add `.rampart/policy.yaml` to the project with governance-specific deny rules. Document in ai-coding methods alongside Layer 3.

**Trigger:** When using AI clients in environments where MCP proxy is not configured (e.g., quick one-off sessions, new machine setup).

**Implementation requirements:** `.rampart/policy.yaml` config file, documentation in methods. No code changes.

#### 20. GitHub Actions Pin Currency Process (Priority: LOW)

**Problem:** Session review found the Node.js 20→24 migration (Backlog #17) fixed 19 stale pins but created no process to prevent recurrence. Per Systemic Thinking: treated the symptom (stale pins) without addressing the structural cause (no automated currency mechanism).

**Options:**
1. **Dependabot for Actions** — automated PRs when action versions update. GitHub-native, zero maintenance.
2. **Quarterly manual audit** — human-triggered review of all SHA pins against latest releases. Simple but relies on memory.

**Trigger:** Next time an action EOL warning appears in CI logs.

**Implementation requirements:** If Dependabot: enable in repo settings + `.github/dependabot.yml`. If manual: add to a quarterly review calendar.

#### 21. Principle Consolidation Pass (Priority: MEDIUM)

**Problem:** Systemic Thinking review found the constitution has 47 principles — "small set of high-leverage meta-principles" vs reality. Some may be domain methods elevated to constitutional status. Framework grows by accretion with no retirement mechanism. 164 principles + 632 methods = 800 indexed items.

**Scope:** Audit which constitutional principles have never been cited in a governance evaluation. Consider demoting, consolidating, or retiring principles that are redundant or domain-specific. Establish a retirement process for ineffective methods.

**Trigger:** Next major session focused on framework quality.

#### 22. Outcome Measurement Framework (Priority: MEDIUM)

**Problem:** The framework claims to prevent governance drift but cannot demonstrate this. Compliance analytics measure call PRESENCE (was evaluate_governance called?) but not call QUALITY (did the cited principles actually influence the decision?). The claim is unfalsifiable without outcome measurement.

**Scope:** Define 5-10 measurable AI behavior outcomes the framework should produce. Instrument them. Report periodically. Add/remove framework content based on what moves the metrics.

**Trigger:** When the framework is used across multiple projects and the value proposition needs evidence.

#### 23. Plan-Mode Architecture Checklist — COMPLETE (2026-03-28)

Added to COMPLETION-CHECKLIST: 4-item BEST-EFFORT checklist for plan-mode architecture decisions (contrarian review, research if novel, verify assumptions, simpler alternatives first). Includes the CE Phase 4 concrete failure case as the documented justification.

#### 24. Principle Authoring Checklist Enforcement (Priority: LOW)

**Problem:** The meta-dogfood review of Backlog #18 found that "adding a principle" is a parameter-level fix unless accompanied by structural enforcement of the authoring process. The COMPLETION-CHECKLIST now has a 10-item principle-authoring checklist but it's BEST-EFFORT.

**Trigger:** If principles start being added without the checklist process, convert to ENFORCED.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
