# Session State

**Last Updated:** 2026-03-31
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
| Content | **v3.0.0** (Constitution — 22 principles, 5 series), **v3.18.0** (meta-methods), **v2.31.0** (ai-coding methods), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.16.1** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.1** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.1** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.0** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.0** (kmpd methods), **v2.5** (ai-instructions) |
| Tests | Run `pytest tests/ -v` for current count |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **128 principles + 662 methods + 4 references** (794 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **4** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-03-31)

### Completed This Session

32. **#31 Template Alignment — EXECUTED**
   - **Phase 1 — Template consolidation (governance methods v3.18.0):**
     - Consolidated 3 competing templates (Parts 3.5.1, 9.4, 9.4.1) → single canonical source at Part 3.5.1
     - Restored "Definition" as separate field from "Domain Application" (contrarian catch from planning session)
     - Added Required/Recommended/Optional field tiers + alias table for variant field names
     - Added "Known Limitation" note (extractor is field-name agnostic, no 128-principle retrofit needed)
     - Refactored Part 9.4.1 → redirect to Part 3.5.1; updated Part 9.4.0 summary
     - Updated all cross-references: §9.8.3, Part 9.5.1, Situation Index, COMPLETION-CHECKLIST ("7 questions" → "6 questions")
     - Added missing v3.17.0 version history entry
   - **Phase 2 — Header standardization (4 domain files → PATCH bumps):**
     - "Research-Based" → "Evidence-Based" in derivation formula (ai-coding, multi-agent, storytelling, multimodal-rag)
     - Added Truth Source Hierarchy to all 4 files (ui-ux + kmpd already had it)
     - Added Cross-Domain Dependencies sections to ai-coding, storytelling, multimodal-rag (kmpd already had it; multi-agent has PEER DOMAIN RELATIONSHIP)
   - **3-agent assessment battery (contrarian + validator + coherence):**
     - Contrarian: alias table re-merge risk → fixed with "reading vs authoring" clarification
     - Validator: all 7 criteria PASS
     - Coherence: 4 stale footers caught (2 ours fixed, 2 pre-existing from session #29 flagged)
     - Part 9.4.2 example "Failure Mode" → "Failure Mode(s)" fixed
   - **Version bumps:** governance methods v3.18.0, ai-coding v2.7.1, multi-agent v2.7.1, storytelling v1.4.1, multimodal-rag v2.4.1
   - **Validation:** 1026 tests pass, index rebuilt (128 principles + 662 methods), governance query spot-check confirmed
   - **Pre-existing gaps flagged (not #31 scope):** UI/UX v1.2.0 + KM&PD v1.4.0 missing changelog entries and stale footers from session #29

33. **Session Retrospective** — governance compliance self-review
   - Logged governance reasoning trace (`gov-149fdb65ea80`) — was skipped during execution, corrected
   - Added #39 (test_compare_models pre-existing failure) to discussion backlog
   - Added #40 (completion checklist trivial-change escape hatch) to discussion backlog
   - Backlog: Active (0) / Discussion (18) / Closed (4)

### Previous Session (2026-03-30)

28. **Backlog Quick Cleanup** — 4 items completed
   - #20: Dependabot config for GitHub Actions (weekly, grouped, PR limit 5)
   - #30: Cross-domain overlap audit (4 justified, 2 needed cross-refs)
   - #28: Cross-domain template consistency audit (7 inconsistencies, 4 structural)
   - #27: TITLE 8 / Part 9.8 forward references (governance methods v3.17.0)
   - Settings: `.github/*` moved from hard-deny to prompt-per-use

29. **Cross-Domain References** — 7 cross-refs added across 6 domain principle files
   - Session Continuity: AI Coding C3 ↔ Multi-Agent State Persistence (bidirectional)
   - Accessibility: UI/UX ACC1 ↔ Multimodal RAG P5 ↔ Storytelling A3 ↔ KM&PD TL1
   - Voice/Authenticity: KM&PD TL1 → Storytelling E1 (SME voice preservation)
   - Fixed stale P6→P5 reference in UI/UX ACC1
   - Version bumps: AI Coding v2.7.0, Multi-Agent v2.7.0, Storytelling v1.4.0, Multimodal RAG v2.4.0, UI/UX v1.2.0, KM&PD v1.4.0

30. **Backlog Restructure** — Contrarian review of entire backlog
   - New structure: Active (1) / Discussion (16) / Closed (3)
   - Closed: #3 (quantized vector search), #15 (CE Phase 4), #1B Phase 1 (complete)
   - Merged: #26 + #29 (content quality governance), #14 into #31 (template alignment)
   - New items: #33 (defer vs fix now), #34 (Epistemic Integrity), #35 (Stripe Projects CLI), #36 (Part 9.8 Reference Library gap), #37 (Domain Classification definition), #38 (version-in-filename evaluation)
   - Backlog philosophy defined: fix shipped work now, defer new capabilities, default new todos to discussion
   - Feedback memories saved: anticipatory work policy, todo philosophy

31. **#31 Template Alignment — COMPLETE** (see session 32 above for details)

### Previous Session (2026-03-29)

### Completed

23. **Constitutional Principle Consolidation v3.0.0** (Backlog #21) — MAJOR version
   - Constitution: 47→22 principles, 6→5 series (MA-Series dissolved)
   - 10-phase execution: alias infrastructure, 12 merges + 2 moves, 9 domain demotions, 6 methods demotions, MA dissolution, 178+ cross-reference cascade, polish/rewrite, code/infrastructure updates, dogfooding fixes, final validation
   - Phase 5 agents updated all domain principle files (ai-coding v2.5.0, multi-agent v2.5.0, storytelling v1.2.0, multimodal-rag v2.2.0, ui-ux v1.1.0, kmpd v1.2.0) + methods files (governance v3.15.0, ai-coding v2.31.0, multi-agent v2.16.0)
   - Alias infrastructure: `aliases` field on Principle model, alias resolution in retrieval
   - "Effective & Efficient Communication" promoted back from methods to Q-Series (was incorrectly demoted as style guide)
   - Discovery Before Commitment: proportionality signals moved to front of principle
   - Dogfooding fixes: S-Series amendment gate, pre-push hook constitution trigger, accessibility clause in Bias Awareness
   - Security auditor: 0 critical, 0 high. S-Series veto confirmed intact (uses series_code, not ID prefix)
   - 6 subagent review rounds: contrarian (3), coherence (3), validator (1), voice-coach (1), security (1)
   - 1026 tests passing, retrieval quality benchmarks stable (MRR 0.688, Recall 0.875)

24. **Part 9.8 Content Quality Framework** — NEW governance method
   - Universal quality gate for authoring AND reviewing all framework content (principles, methods, appendices)
   - 6-question Admission Test, Duplication Check, Unified Quality Checklist, Concept Loss Prevention
   - §9.8.8 Required Subagent Reviews: all 3 mandatory agents (contrarian, validator, coherence) at both assessment AND post-change phases
   - Empirically validated: KM&PD primary assessor rated 100% KEEP, contrarian caught 3 issues → 13→10
   - Supersedes Part 9.5 (Validation Checklist, principles-only)

25. **Domain Principle Consolidation** — Applied Part 9.8 to all 6 domains
   - KM&PD: 13→10 (2 merges, 1 demotion). TL3+QA1 shared failure mode, PD2 into KA3, PD3 to methods.
   - AI Coding: 14→12 (2 merges). Idempotency→Production-Ready (shared C3), Established Solutions→Supply Chain (overlapping verification). 5 citation fixes, FM code collision fixed.
   - Storytelling: 19→15 (4 merges, 1 rewrite). A2→ST2, C4→E2, M2+M3→M1 (all shared FM codes). A3 rewritten for storytelling-specific accessibility. Citation format overhaul (slug→title). Crosswalk table added.
   - UI/UX: 20→20 (skip gate at 100% KEEP). Hygiene fixes only: stale names, truncated citations, DS1 duplicate basis.
   - Multi-Agent: 22→17 (4 merges, 1 demotion). CFS+RST (shared MA-A1), RACI→Handoff, Read-Write→Orchestration, Blameless→Fault Tolerance. Standardized Collaboration→methods. Most complex domain — resolved Phase 2 integration debt.
   - Multimodal RAG: 35→32 (3 merges). P4→P5 (shared MR-F6), CT3→CT1 (shared MR-F16), EV3+O2→combined monitoring (shared MR-F14/F22). Skip gate passed at 91.4%. Hygiene: 4 duplicate derivations fixed, footer updated.
   - **Total across all domains: 170→128 principles (-25%)**
   - 3-agent review battery at every domain (assessment + post-change = 6 reviews per domain)
   - 1026 tests passing throughout

26. **S-Series False Positive Reduction** — Hybrid dual-signal escalation
   - Root cause: flat 26-keyword set with OR logic treated "remove section" same as "steal credentials" (~87% false positive rate)
   - Fix: hybrid approach — 11 critical keywords always escalate, 24 advisory keywords produce warnings only when semantic retrieval doesn't find S-Series principle
   - Empirically validated: 8 dangerous queries tested against semantic path; 5/8 caught semantically, 3/8 need critical keywords
   - Contrarian + security-auditor reviewed plan; initial tiered approach rejected for simpler dual-signal logic
   - Expected: ~75% false positive reduction, 0% false negative increase

27. **Session Meta-Review** — Governance compliance self-assessment
   - Identified: ESCALATE false positives silently dismissed, log_governance_reasoning never called, early phases lacked 3-agent review
   - Self-grade: B+ (structural compliance good, audit trail gaps)

### Previous Session (2026-03-28)

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
| 20 | GitHub Actions Pin Currency (Dependabot) | 2026-03-29 |
| 21 | Principle Consolidation Pass v3.0.0 (47→22 principles, MA dissolved) | 2026-03-29 |
| 27 | TITLE 8 / Part 9.8 Forward References (v3.17.0) | 2026-03-30 |
| 28 | Cross-Domain Template Consistency Audit (7 inconsistencies, 4 structural) | 2026-03-29 |
| 30 | Cross-Domain Overlap Audit (4 justified, 2 need cross-refs) | 2026-03-29 |

### Open Backlog

> **Backlog Philosophy (2026-03-30):** Items fall into three categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop, (3) **Closed** — done, dropped, or moved to reference. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it." See also #33.

---

### Active (Implement Now/Soon)

*No active items — all moved to Discussion or Closed.*

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

#### 22. Governance Effectiveness Measurement (Discussion)

**What:** The framework can measure whether `evaluate_governance` was *called* but not whether it *influenced decisions*. Can we measure the framework's actual effectiveness?

**Discussion needed:** Explore what meaningful metrics look like. This isn't about creating a metric for metric's sake — it's about understanding whether governance adds value and how. Could be several smaller metrics tracking different effectiveness aspects. May conclude some aspects aren't measurable and that's fine.

**Possible directions:** Track behavior-changing evaluations (PROCEED_WITH_MODIFICATIONS, ESCALATE), measure retrieval relevance scores over time, track principle citation frequency vs actual influence, qualitative session reviews.

**Outcome:** Either define metrics worth implementing, or conclude the value is qualitative and close this item.

#### 26+29. Content Quality Governance — Enforcement + Periodic Review (Discussion)

**What (merged from #26 and #29):** Two related concerns about keeping framework content healthy over time:
- **New content gate:** Part 9.8 Admission Test is advisory. Should it be structurally enforced?
- **Existing content review:** Nothing forces periodic review. The 47→22 consolidation proved accretion happens silently.

**Root-cause framing:** The real goal is *continuous content quality improvement* — both preventing bad content from entering (enforcement) and ensuring existing content stays relevant (review). These are two sides of the same problem: content quality governance.

**Discussion needed:** What's the right structural mechanism? Options:
1. CI assertion on principle count ceiling (e.g., 25 per domain) — structural, zero ongoing effort
2. PreToolUse hook enforcing Admission Test before governance doc edits — per-edit enforcement
3. Version-milestone trigger (every MAJOR bump triggers cross-domain audit)
4. Combination approach

**Outcome:** Define a unified content quality governance mechanism that handles both new and existing content.

#### 16. Governance Retrieval Quality Assessment (Discussion)

**What:** Governance server uses BGE-small (384d) while Context Engine uses nomic-embed (768d, better benchmarks). But we don't know if the current model is underperforming — users may not notice degraded retrieval quality.

**Discussion needed:** Related to #22 (effectiveness measurement). How do we measure current retrieval quality for governance queries specifically? Is there a way to benchmark governance retrieval that would tell us if an upgrade is justified? Determine justification first, then implement if needed, drop if not — but with a way to measure effectiveness going forward.

**Possible directions:** Governance-specific benchmark queries, MRR/Recall measurements on governance corpus, A/B comparison with nomic-embed on representative queries.

**Outcome:** Either justify the upgrade with data and implement, or confirm current model is sufficient and close.

#### 1B-P2. Cross-MCP Governance Enforcement (Discussion + Research)

**What:** Phase 1 (enforcement on governance server's own tools) is complete. Phase 2 would enforce governance before tool calls to OTHER MCP servers (GitHub, filesystem, etc.).

**Context:** Hooks already cover Bash/Edit/Write at ~100%. Contrarian review found MCP protocol isolation makes cross-MCP enforcement architecturally difficult. But the MCP ecosystem is evolving rapidly.

**Discussion needed:** Online research into current MCP proxy/gateway patterns, Lasso MCP Gateway progress, Envoy AI Gateway, and whether the MCP protocol has evolved to support cross-server enforcement natively.

**Outcome:** Either find a viable approach that justifies implementation, or confirm hooks are sufficient and close.

#### 6. Visual Communication Domain (Discussion → Full Planning)

**What:** Governance for non-coding visual artifacts: presentations, reports, infographics, print design. Separate from UI/UX (different failure modes, evidence bases, tooling). Tufte, Duarte, Reynolds evidence base.

**Status:** Anticipatory — building this before active use so it's ready when needed.

**Discussion needed:** Full planning process per COMPLETION-CHECKLIST domain creation. Scope candidate principles and methods, evidence base review, failure mode identification.

#### 7. Security Content Currency Process (Discussion)

**What:** AI security evolves fast. Our security content (§5.3-§5.11, security-auditor subagent) is comprehensive today but will go stale without a review mechanism.

**Discussion needed:** Design a lightweight review process. Possible approach: quarterly online research of key security resources (maintain a log of sources reviewed + open search), compare against current security content, apply security-auditor subagent to projects near completion. Define what "key security resources" means (OWASP, NIST, major CVE databases, AI-specific threat reports).

**Outcome:** Define the review process and resource list, then implement as a recurring practice.

#### 19. Rampart Integration — Client-Side Enforcement (Discussion)

**What:** Rampart provides shell-level security enforcement (credential theft, exfiltration, destructive commands). Complements MCP proxy and hooks — different root cause. Hooks enforce "did you consult governance?" (process gate); Rampart enforces "is this command safe?" (security gate). Defense-in-depth.

**Discussion needed:** Evaluate whether the incremental security value justifies the setup for a single-developer Claude Code project. Research current Rampart capabilities and rule set.

#### 13. Governance-Aware Output Compression (Discussion)

**What:** Long Bash output wastes context window tokens. Build a PostToolUse hook that compresses verbose output while preserving governance/security lines and structured data.

**Discussion needed:** Is this still relevant as context windows grow? Measure actual context consumption from Bash output. If >20% threshold is hit, define the compression approach (per §3.1.4 "build our own" mode to avoid third-party information intermediary risk per §5.6.8).

#### 10. UI/UX Tool-Specific Integration Guides (Discussion)

**What:** Write integration guides for AI-assisted design tools (Figma MCP, Storybook MCP, Axe MCP, Playwright MCP, etc.) as they're adopted. Research already done (candidate tools, risks, token costs documented in SESSION-STATE #10 archive).

**Discussion needed:** Which tools are most likely to be adopted first? What format should integration guides take? Reference the existing research.

#### 9P3. Tiered Principle Activation — Phase 3: Accountable Reasoning (Discussion)

**What:** Phases 0-1.5 shipped, Phase 2 cancelled. Remaining question: should the accountable reasoning pattern (currently synthesized via tier config) become a formal principle?

**Discussion needed:** Understand the original intent before deciding. The contrarian argues this contradicts the "fewer principles" lesson from consolidation. But the tier config synthesis may have limitations the user wants to explore.

**Note:** Want to understand the original intent before closing. May close after discussion.

#### 25. Principle Authoring Checklist Enforcement (Discussion)

**What:** The principle-authoring checklist in COMPLETION-CHECKLIST is BEST-EFFORT (~85% compliance). Should it be converted to ENFORCED via hook?

**Discussion needed:** Understand the tradeoff. Consolidation pass catches drift retroactively. Hook would prevent drift proactively but adds friction to an already-rare event (principle additions). What's the right level of enforcement for low-frequency, high-impact events?

**Note:** Want to understand more before closing.

#### 11. Autonomous Operations Domain (Discussion)

**What:** Autonomous agent patterns (AO-Series, currently 4 principles in Multi-Agent) may eventually outgrow the multi-agent domain. This would create a dedicated domain for autonomous operation governance — financial compliance, regulatory frameworks, agent marketplace governance, cross-org federation.

**Discussion needed:** Is this anticipatory need real? What would trigger the split? The Domain Creation Criteria (§5.1.0) already defines when to create domains, but the user wants to understand if the AO-Series trajectory warrants keeping this on the radar.

#### 12. Operational / Deployment Runbook Domain (Discussion)

**What:** Framework covers how AI produces code but not how AI handles deployment, infrastructure, and operations. 3 solid practices from viral "AI vibe coding security rules" analysis couldn't be placed in existing domains.

**Discussion needed:** Is this a full domain or should the 3 orphaned practices just be filed in an appendix? Decision factors: are we using AI for deployment workflows? Is the gap growing? Domain vs standalone runbook vs appendix to AI Coding methods?

#### 33. Define "Defer vs Fix Now" Philosophy (Discussion)

**What:** AI tendency to say "do when files are next touched" can cause known issues to persist indefinitely due to session discontinuity and forgetting. Need clear criteria for when to defer vs fix immediately.

**Discussion needed:** Define the boundary:
- **Fix now:** Existing shipped work with known inconsistencies, broken references, template mismatches
- **Defer:** New capabilities the user isn't actively considering
- **Gray area:** Anticipatory work (user decides case-by-case)

**Outcome:** Add clear guidance to CLAUDE.md or COMPLETION-CHECKLIST so AI applies this consistently.

---

#### 36. Part 9.8 Coverage Gap — Reference Library Entries (Discussion)

**What:** Part 9.8 (Content Quality Framework) covers principles, methods, and appendices — but NOT Reference Library entries (TITLE 15). The Reference Library was added in v3.14.0; Part 9.8 was added in v3.16.0 but didn't incorporate it. Two separate quality processes exist with no explicit relationship.

**The gap:** §9.8.3 (Structural Requirements by Content Type) lists 4 content types: Constitutional Principles, Domain Principles, Methods, Appendices. Reference Library entries are missing. TITLE 15 has its own curation governance (Part 15.4: three intake paths, maturity pipeline, KeyCite currency tracking) but it's disconnected from the unified quality gate.

**Discussion needed:** Two approaches:
1. **Expand 9.8** — Add Reference Library as a 5th content type in §9.8.3. Point to TITLE 15's entry template (Part 15.3) and curation governance (Part 15.4). Apply the Admission Test and Duplication Check to Reference Library entries. This unifies all content types under one quality gate.
2. **Cross-reference only** — Keep TITLE 15's curation governance as the authoritative process for Reference Library entries. Add a note in 9.8 acknowledging that Reference Library entries follow TITLE 15 instead. Simpler, but two parallel quality processes.

**Root-cause consideration:** Per Single Source of Truth, one unified quality gate is better than two parallel ones. But Reference Library entries are structurally different from principles/methods (concrete artifacts vs governance rules). The Admission Test questions ("does this fill a gap?", "correct hierarchy level?") may not map cleanly to curated artifacts.

**Outcome:** Either expand 9.8 or formalize the relationship between 9.8 and TITLE 15.

#### 37. Domain Classification System Definition (Discussion)

**What:** UI/UX declares itself "Type A (context-intensive)" and KM&PD declares "Type B (proprietary)." The #31 plan proposed adding Domain Classification to 4 more domains but the contrarian reviewer found Type A and Type B are on different axes — Type A describes operational complexity, Type B describes access control. They're not mutually exclusive.

**Discussion needed:** Define what the classification system actually means before propagating it. Options:
1. Single axis with clear values (e.g., complexity: low/medium/high)
2. Multi-axis system (complexity + access + tooling intensity)
3. Drop it — if every public domain is "Type A," the classification carries no information

**Origin:** Contrarian review of #31 plan (2026-03-30).

#### 38. Version-in-Filename vs Version-in-Header (Discussion)

**What:** Every governance document version bump requires: archive old file, rename file, update domains.json, update config.py, rebuild index. For 5 files, that's 30+ mechanical steps where any can be missed. The propagation tax is O(n) per bump across n references.

**Discussion needed:** Evaluate whether version metadata should live inside the file (header `version:` field) while filenames stay stable (e.g., `ai-coding-domain-principles.md`). This would eliminate the archive/rename/domains.json/config.py cascade. Tradeoff: lose at-a-glance version identification in file listings.

**Origin:** Contrarian review of #31 plan (2026-03-30). Systemic concern — affects every future version bump across the project.

---

#### 39. `test_compare_models` Pre-Existing Failure (Discussion — Bug)

**What:** `tests/test_context_engine_quality.py::TestCompareModels::test_compare_models` fails with `TypeError: Object of type date is not JSON serializable`. The test indexes the project, then tries to serialize results containing `datetime.date` objects to JSON. Discovered 2026-03-31 during #31 validation — confirmed pre-existing (not caused by template alignment changes).

**Discussion needed:** Is this a test bug (missing JSON serializer for dates) or a code bug (date objects leaking into serializable output)? Low priority since all other 1026 tests pass and this test is a model comparison benchmark, not a functional test.

---

#### 40. Completion Checklist Trivial-Change Escape Hatch (Discussion)

**What:** COMPLETION-CHECKLIST requires code-reviewer for any config.py change. During #31, config.py changes were trivial filename string updates (e.g., `v2.7.0` → `v2.7.1`). Invoking code-reviewer for this would be pure ceremony — the validator already confirmed correctness.

**Discussion needed:** Should the checklist have a "trivial change" qualifier? Options: (1) Add "substantive changes" qualifier to the trigger, (2) Keep as-is and accept occasional over-triggering, (3) Let the 3-agent battery substitute when it provides equivalent or better coverage. Risk of option 1: defining "trivial" is subjective and creates a loophole.

---

#### 35. Evaluate Stripe Projects CLI for Appendices (Discussion)

**What:** Stripe Projects CLI (launched 2026-03-27, developer preview) lets developers and AI agents provision third-party services, manage credentials, and handle billing from the terminal. Evaluate whether it belongs in the ai-governance appendices as tool-specific guidance.

**Origin:** Claude.ai research conversation. Preliminary assessment produced WITHOUT governance tooling — treat as research input, not validated conclusions.

**Why it matters for governance:** This tool lets AI agents trigger real financial transactions (paid-tier upgrades via Shared Payment Tokens) and provision infrastructure autonomously. That's squarely in AO-Series (autonomous operations) and S-Series (safety/security) territory.

**Preliminary mapping (UNVALIDATED — needs `evaluate_governance()` and subagent review):**
- `coding-method-agent-to-service-integration-patterns` — standardizes provisioning workflows
- `coding-method-credential-isolation-and-secrets-management` — vault-based credential storage
- `coding-method-service-identity-and-credential-lifecycle` — provider account association
- `meta-safety-non-maleficence-privacy-security` (S-Series) — credential handling, financial action authority
- `coding-process-established-solutions-first` — but developer preview maturity is a concern

**Key governance concerns to resolve:**
1. **Agent autonomy on financial actions.** Agents can select paid tiers triggering real charges. Which principles govern this? What HITL enforcement mechanism?
2. **Maturity risk.** Developer preview, US/EU/UK/Canada only, expanding provider catalog. Does "Established Solutions First" apply to a tool this new?
3. **Shared Payment Token security model.** Tokenized payment credentials passed to providers. Security-auditor evaluation needed.
4. **Vendor dependency.** Does the framework endorse specific vendors or just document patterns?

**Research sources:** Stripe docs (docs.stripe.com/projects), projects.dev, Stripe X announcement, HN discussion (47532148), Karpathy blog post that motivated it.

**When discussed:** Run full governance evaluation, contrarian-reviewer (does it belong at all?), coherence-auditor (appendix fit), security-auditor (credential/payment model). Three possible outcomes: add now, add with conditions, or do not add.

---

#### 34. Epistemic Integrity — Constitutional Principle (Discussion)

**What:** Proposed new Q-Series constitutional principle addressing AI sycophancy — the tendency to validate flawed assumptions, reinforce suboptimal approaches, or present outputs with unearned confidence. Core requirement: analytical accuracy over conversational agreeability.

**Origin:** Independent research via Claude app (no anchor bias from existing framework). Reviewed against Part 9.8 Admission Test — passes all 6 questions. Contrarian review and coherence audit completed (see draft below).

**The gap:** Three existing principles touch adjacent territory but none address the core failure mode:
- **Transparent Limitations (S-Series):** Covers "I don't know" — NOT "I agree but shouldn't"
- **Discovery Before Commitment (C-Series):** Covers AI's own investigation process — NOT AI's evaluative posture toward human claims
- **Visible Reasoning & Traceability (Q-Series):** Covers making reasoning auditable — NOT whether reasoning prioritizes accuracy over agreeability

**Key question to resolve: consolidation vs addition.** If this becomes a principle, does it REPLACE or ABSORB aspects of the three above? Per Single Source of Truth, if Epistemic Integrity subsumes the "epistemic honesty" aspect of Transparent Limitations, the "challenge the frame" aspect of Discovery Before Commitment, and the "self-scrutiny" aspect of Visible Reasoning — should those principles be narrowed to avoid redundancy? The goal is one authoritative home for each concept, not three principles each partially covering honesty.

**Possible outcomes:**
1. **New principle + narrow the three** — Epistemic Integrity becomes the single source for intellectual honesty; TL, DBC, VR&T retain their non-overlapping scopes
2. **Expand one existing principle** — e.g., expand Visible Reasoning to include "quality of reasoning, not just visibility of reasoning"
3. **Method only** — Create the Performance Assessment Protocol method under an existing principle without a new constitutional addition
4. **Close** — Existing principles + contrarian-reviewer subagent already cover this adequately

**Draft principle:** Full draft available (reviewed by contrarian + coherence auditor). Key components:
- Challenge Before Confirm (earned agreement, not default agreement)
- Self-Scrutiny Before Delivery (apply same standard to own outputs)
- Evidence-Grounded Assessment (benchmarks over pleasantries)
- Constructive Alternatives Over Rejection (better outcomes, not intellectual sparring)
- Proportional Scrutiny (calibrate pushback to stakes)

**Revisions needed before implementation (from review):**
1. Soften "at least one material risk" threshold → "demonstrated consideration of alternatives" (avoid checkbox behavior)
2. Add Intent Preservation boundary: challenges target methods/assumptions, not the human's underlying goals
3. Verify Q-series numbering (Q8?) against current count

**Related:** Would also create `meta-method-performance-assessment-protocol` (behavioral rules for honest feedback) and add `constitutional_basis` to contrarian-reviewer subagent definition.

---

### Closed / Reference

#### 3. Quantized Vector Search — CLOSED (2026-03-30)

Closed per backlog review. 800 vectors vs 500K trigger — structurally unreachable for a governance framework corpus. Phased approach documented in PROJECT-MEMORY.md > ADR-14 if ever needed.

#### 15. Context Engine Phase 4 — CLOSED (2026-03-30)

Investigation complete (2026-03-28). MRR gap was a benchmark specification error, not algorithm problem. Corrected MRR: 0.802. Remaining improvement options preserved as reference in PROJECT-MEMORY.md: (1) weight grid search, (2) score normalization, (3) RRF with scaled bonuses, (4) code-trained cross-encoder.

#### 1B. Model-Agnostic Governance Enforcement — Phase 1 COMPLETE (2026-03-28)

stdio JSON-RPC interceptor proxy (`enforcement.py`). Enforces governance preconditions on governance server's own action tools. Zero new dependencies, works with any MCP client. Entry point: `ai-governance-proxy`. ADR-14 in PROJECT-MEMORY.md. Phase 2 tracked as discussion item above.

#### 31. Cross-Domain Template Alignment — COMPLETE (2026-03-31)

Consolidated 3 competing domain principle templates (Parts 3.5.1, 9.4, 9.4.1) → single canonical source at Part 3.5.1. Restored Definition as separate field from Domain Application. Added tiered fields (Required/Recommended/Optional) + alias table. Standardized 4 domain file headers (Evidence-Based, Truth Source Hierarchy, Cross-Domain Dependencies). 3-agent battery validated. governance methods v3.18.0, ai-coding v2.7.1, multi-agent v2.7.1, storytelling v1.4.1, multimodal-rag v2.4.1. #14 absorbed.

---

### Historical Detail (pre-restructure backlog items, 2026-03-30)

> The detailed descriptions below are from the pre-restructure backlog. Active items have been moved to the new structure above. These are preserved for context on decisions, contrarian findings, and implementation details.

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

#### 20. GitHub Actions Pin Currency Process — COMPLETE (2026-03-29)

Dependabot for GitHub Actions ecosystem. `.github/dependabot.yml` created with weekly Monday schedule, grouped updates, PR limit 5. Pip ecosystem deferred (pyproject.toml uses loose pins; Dependabot PRs wouldn't be actionable). Settings updated to move `.github/*` from hard-deny to prompt-per-use.

#### 21. Principle Consolidation Pass — COMPLETE (2026-03-29)

**Problem:** Constitutional test ("does this govern reasoning across ALL domains?") found 20 of 47 principles are questionable. The constitution claims "a small set of high-leverage meta-principles" but has grown by accretion to include domain-specific concepts and methods masquerading as principles.

**Analysis complete (2026-03-28):** 20 principles categorized into 4 action buckets:

**Category 1 — Demote to domain principles (8):**
- Role Specialization & Topology → multi-agent domain
- Hybrid Interaction & RACI → multi-agent domain
- Standardized Collaboration Protocols → multi-agent domain
- Synchronization & Observability → multi-agent domain
- Idempotency by Design → ai-coding domain
- Atomic Task Decomposition → ai-coding domain
- Goal-First Dependency Mapping → ai-coding domain
- Structured Output Enforcement → ai-coding domain

**Category 2 — Demote to methods (5):**
- Progressive Inquiry Protocol → questioning method
- Constraint-Based Prompting → prompt engineering technique
- Iterative Planning and Delivery → project management method
- Rich but Not Verbose Communication → style preference
- Accessibility and Inclusiveness → operational guidance

**Category 3 — Consolidate overlapping (4):**
- Verifiable Outputs → merge into Verification Mechanisms Before Action
- Incremental Validation → merge into Fail-Fast Validation
- Continuous Learning (O-Series) → merge with Continuous Learning & Adaptation (G-Series)
- Project Reference Persistence → merge into Single Source of Truth

**Category 4 — Borderline, needs deeper analysis (3):**
- Separation of Instructions and Data
- Structured Organization with Clear Boundaries
- Accessibility and Inclusiveness (also in Category 2 — decide: demote or keep with narrower scope)

**Target:** 47 → ~27 constitutional principles. Apply principle-authoring checklist in reverse (same rigor to remove as to add). Run contrarian review before executing. Version bump to v3.0.0 (MAJOR — removing principles is breaking).

**Implementation:** Dedicated session. Each demotion requires: moving content to the appropriate domain document, updating cross-references, version bumping affected files, index rebuild. Contrarian review on the full set before any changes.

#### 22. Outcome Measurement Framework (Priority: MEDIUM)

**Problem:** The framework claims to prevent governance drift but cannot demonstrate this. Compliance analytics measure call PRESENCE (was evaluate_governance called?) but not call QUALITY (did the cited principles actually influence the decision?). The claim is unfalsifiable without outcome measurement.

**Scope:** Define 5-10 measurable AI behavior outcomes the framework should produce. Instrument them. Report periodically. Add/remove framework content based on what moves the metrics.

**Trigger:** When the framework is used across multiple projects and the value proposition needs evidence.

#### 23. Plan-Mode Architecture Checklist — COMPLETE (2026-03-28)

Added to COMPLETION-CHECKLIST: 4-item BEST-EFFORT checklist for plan-mode architecture decisions (contrarian review, research if novel, verify assumptions, simpler alternatives first). Includes the CE Phase 4 concrete failure case as the documented justification.

#### 24. Verification-as-Workflow Reframing — COMPLETE (2026-03-28)

**Problem:** Research (Agent Drift arxiv 2601.04170, LLMs Get Lost arxiv 2505.06120, QualityFlow arxiv 2501.17167) confirms that advisory verification steps are structurally low-probability generations for autoregressive models. The framework currently treats reviews, contrarian checks, and research as "also do this" steps bolted onto the workflow. They should be reframed as the workflow itself — verification determines what happens next (control flow), not just whether output is good (checkpoint).

**Root cause:** "Velocity pressure" was a rationalization. The actual mechanism is forward-continuation bias: each completed token raises the probability of the next token continuing forward. Verification breaks this trajectory and is thus naturally deprioritized. This is structural, not motivational.

**Scope:** Reframe advisory steps across the framework from "interruptions" to "phase transitions":
- COMPLETION-CHECKLIST: advisory items reframed as routing decisions ("contrarian review determines whether to proceed, revise, or escalate" vs "run contrarian review")
- SERVER_INSTRUCTIONS: governance evaluation framed as the step that unlocks the next phase, not a separate check
- Subagent reviews framed as control flow (review output determines next action) not checkpoints (review happens, then continue regardless)
- Research techniques to apply: gate-token transitions, Chain-of-Verification prompting, verification-as-control-flow (QualityFlow pattern)

**Trigger:** Next major framework methods update.

**Implementation requirements:** Methods-level changes to how advisory steps are described. Potentially structural changes to how subagent reviews are integrated (review output as routing decision). LEARNING-LOG entry captures the root cause and research.

#### 26. Part 9.8 Structural Enforcement (Priority: MEDIUM)

**Problem:** Part 9.8 (Content Quality Framework) is entirely advisory. The project's own data shows advisory compliance ~85% vs structural blocking ~100%. The Admission Test could be enforced via a PreToolUse hook that checks whether 9.8.1 questions were answered before content modifications to governance documents.

**Scope:** PreToolUse hook for Edit/Write on governance document files. Check transcript for evidence of Admission Test completion before allowing modifications.

**Trigger:** If content is added that fails the Admission Test retrospectively (same pattern as the 47-principle bloat).

#### 27. TITLE 8 / Part 9.8 Relationship Clarification — COMPLETE (2026-03-29)

Added forward references from Parts 8.2, 8.3, 8.4 to Part 9.8. Clarified sequencing in Part 9.8: "Use Part 9.8 first for the unified workflow, then consult Parts 8.2-8.4 for constitutional-specific considerations." Version bump v3.17.0→v3.17.0. Updated domains.json, config.py. 1031 tests passing (1 pre-existing CE quality benchmark failure unrelated to changes).

#### 25. Principle Authoring Checklist Enforcement (Priority: LOW)

**Problem:** The meta-dogfood review of Backlog #18 found that "adding a principle" is a parameter-level fix unless accompanied by structural enforcement of the authoring process. The COMPLETION-CHECKLIST now has a 10-item principle-authoring checklist but it's BEST-EFFORT.

**Trigger:** If principles start being added without the checklist process, convert to ENFORCED.

#### 28. Cross-Domain Template Consistency — COMPLETE (2026-03-29)

**Audit Completed:** 2026-03-29

**Field Presence Matrix:**

| Section | Const | Code | MA | Story | MR | UI/UX | KM&PD |
|---------|:-----:|:----:|:--:|:-----:|:--:|:-----:|:-----:|
| System Instruction block | Y | Y | Y | Y | Y | Y | Y |
| Status/Version | Y | Y | Y | Y | Y | Y | Y |
| Hierarchy/Supremacy | Y | Y | Y | Y | Y | Y | Y |
| Derivation Formula | - | Y | Y | Y | Y | Y | Y |
| Scope (In/Out) | - | Y | Y | Y | Y | Y | Y |
| Domain Context | Y* | Y | Y | Y | Y | Y | Y |
| Evidence Base | Y | Y | Y | Y | Y | Y | Y |
| Failure Mode Taxonomy | - | - | Y | Y | Y | Y | Y |
| Framework Overview | Y | Y | - | Y | - | ~ | Y |
| Domain Classification | - | - | - | - | - | Y | Y |
| Truth Source Hierarchy | - | - | - | - | - | Y | Y |
| Cross-Domain Dependencies | - | - | Y | - | - | - | Y |

*Constitution uses "Design Philosophy" instead of "Domain Context" (appropriate — root doc, not derived)

**Inconsistencies Found (7):**

1. **Derivation formula wording:** AI Coding, Multi-Agent, Storytelling, Multimodal RAG use "Research-Based Prevention". UI/UX and KM&PD use "Evidence-Based Prevention". Recommend standardizing on "Evidence-Based" (more accurate).

2. **Truth Source Hierarchy:** Only UI/UX (line 25) and KM&PD (line 25) include this field. Defines external reference priority (Constitution > Domain > Methods > External). Should be in all domain files.

3. **Domain Classification:** Only UI/UX ("Type A context-intensive") and KM&PD ("Type B proprietary"). Useful metadata for AI agents selecting how to approach a domain. Should be in all domain files.

4. **Cross-Domain Dependencies:** Only Multi-Agent ("Peer Domain Relationship" block) and KM&PD (storytelling cross-refs). Domains with known peer relationships should document them.

5. **Failure Mode Taxonomy placement:** Constitution and AI Coding lack failure mode taxonomy in opening sections. Constitution omission is justified (root doc). AI Coding could benefit from adding one for consistency.

6. **Series naming conventions:** Ad hoc across domains (C/P/Q-Series, ST-Series, ACC/DS/PL, KA-Series). No standard naming convention documented. Low impact — each domain's naming is internally consistent.

7. **Framework Overview heading:** Inconsistent naming ("Framework Overview: The Five Principle Series" vs "KA-Series Principles" vs inline). Cosmetic.

**Severity Assessment:**
- Items 1-4: Structural (newer domains have fields older ones lack — template evolved over time)
- Items 5-7: Cosmetic (no functional impact on governance retrieval)

**Recommendation:** Batch template alignment into a single session when any domain file is next modified. Prioritize items 1-4 (structural). Items 5-7 are optional polish. Each change is a minor version bump to the affected domain file.

#### 31. Cross-Domain Template Alignment (Priority: LOW)

**Problem:** Backlog #28 audit (2026-03-29) found 7 template inconsistencies across domain principle files, 4 structural. Newer domains (UI/UX, KM&PD) have fields (Truth Source Hierarchy, Domain Classification, Cross-Domain Dependencies) that older domains lack. Template evolved over time but was never retroactively standardized.

**Scope:** Add missing structural fields to 4-5 domain files. Specific items:
1. Standardize derivation formula wording → "Evidence-Based Prevention" (affects AI Coding, Multi-Agent, Storytelling, Multimodal RAG)
2. Add Truth Source Hierarchy to AI Coding, Multi-Agent, Storytelling, Multimodal RAG (use UI/UX + KM&PD pattern)
3. Add Domain Classification (Type A/B) to AI Coding, Multi-Agent, Storytelling, Multimodal RAG
4. Add Cross-Domain Dependencies section where peer relationships exist

**Implementation:** Minor version bump to each affected file, domains.json + config.py updates, index rebuild, tests. Batch all changes in one session. Items 5-7 from #28 audit (series naming, framework overview heading, evidence base structure) are cosmetic and optional.

**Trigger:** When domain files are next modified for any other reason, or as a standalone cleanup session.

#### 29. Part 9.8 Periodic Review Trigger (Priority: MEDIUM)

**Problem:** Part 9.8 gates new content (authoring mode) and can review existing content (audit mode), but nothing compels periodic review. The same accretion pattern will recur without a scheduled cadence or quantitative trigger.

**Options:** (1) Principle count threshold: when any domain exceeds 25 principles, mandatory review. (2) Calendar cadence: quarterly or semi-annual. (3) Version milestone: every major version bump triggers cross-domain audit.

**Trigger:** When the framework is used across multiple projects and bloat patterns re-emerge.

#### 30. Cross-Domain Overlap Audit — COMPLETE (2026-03-29)

**Audit Completed:** 2026-03-29

| Overlap Area | Domains | Principle IDs | Verdict | Action |
|---|---|---|---|---|
| Graceful Degradation | Multi-Agent, Multimodal RAG | MA-Q2, F1 | JUSTIFIED | None — different architectural layers (orchestration vs. data retrieval) |
| Session Continuity | AI Coding, Multi-Agent | C3, AC2 | JUSTIFIED | Add mutual cross-references (one-way refs exist, need bidirectional) |
| Accessibility | UI/UX, Multimodal RAG, Storytelling, KM&PD | ACC*, P5, A3, TL1 | NEEDS CROSS-REF | Four distinct specializations (technical/content/narrative/instructional), no mutual citations |
| Audience Understanding | Storytelling, Multimodal RAG, KM&PD | A1, P4, TL1 | JUSTIFIED | None — cross-refs already exist (KM&PD→Storytelling explicit) |
| Context Engineering | Constitution, Multi-Agent, AI Coding | C-Series meta, 4 strategies, C1/C2/C3 | JUSTIFIED | None — exemplary hierarchical overlap (meta→strategies→constraints) |
| Voice/Authenticity | Storytelling, KM&PD | E1/E2, KA3 | NEEDS CROSS-REF | Add KM&PD TL1→Storytelling E1 for SME-authored instruction voice preservation |

**Key findings:**
- 4 of 6 overlaps are justified domain-specific applications of the same concept — no redundancy
- 2 overlaps need cross-references added (Accessibility across 4 domains, Voice/Authenticity KM&PD→Storytelling)
- Session Continuity has one-way references; should be made bidirectional
- Context Engineering is the strongest example of proper hierarchical overlap governance

**Follow-up work:** Cross-references COMPLETE (2026-03-30) — added 7 cross-refs across 6 domain files in commit `49fdbe3`. Template alignment tracked as backlog #31.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
