# Session State

**Last Updated:** 2026-04-12
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Implementation (Constitutional Framework Alignment — Phases 0-4 complete, Phase 5 next)
- **Mode:** Standard
- **Active Task:** Constitutional Framework Alignment — Phases 0-4 complete. Gates tagged: `const/gate-1` (Phase 1), `const/gate-2` (Phase 2), `const/gate-3` (Phase 3), `const/gate-4` (Phase 4). **Phase 5 (cross-references, documentation & polish) is next** — low-risk phase, ~2-3 hours. Plan at `.claude/plans/project-constitutional-framework-alignment.md`. Content Enhancer integration (#85) and workflow pattern (#55) remain paused. Compliance review due ~2026-04-20.

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.8.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, BAAI/bge-small-en-v1.5 384d (same model as governance server), metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v4.1.0** (Constitution — 24 principles: C:6, O:6, Q:4, G:5, S:3), **v3.24.0** (meta-methods), **v2.36.0** (ai-coding methods), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.17.0** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.1** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.1** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.0** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.0** (kmpd methods), **v2.5** (ai-instructions). **Filenames renamed to Constitutional naming** (Phase 4): `constitution.md`, `rules-of-procedure.md`, `title-NN-*.md`, `title-NN-*-cfr.md`. Versions in YAML frontmatter (since v3.20.0). |
| Tests | **1175 passing** (run `pytest tests/ -v` for current) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 675 methods + 13 references** (818 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **4** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Session Summary (2026-04-12)

### Completed This Session

94. **Constitutional Framework Alignment — Phase 4 COMPLETE**
   - **14 files renamed** to Constitutional naming: `constitution.md`, `rules-of-procedure.md`, 6 `title-NN-domain.md` + 6 `title-NN-domain-cfr.md`. Git tracks all as renames (R099/R100) — blame history preserved.
   - **`domains.json` + `config.py`** updated to new filenames. `governance_level` YAML frontmatter: `domain-principles`→`federal-statute`, `domain-methods`→`federal-regulations`, `constitution-methods`→`rules-of-procedure`.
   - **Cross-references updated across 30 files:** preambles, hierarchy diagrams, subordination clauses, agent definitions (voice-coach, continuity-auditor, coherence-auditor), templates in rules-of-procedure, ai-instructions.md, COMPLETION-CHECKLIST, README.
   - **Key finding — context engine catches what grep misses:** Initial grep found all `.md`-extension references. Context engine + extensionless grep found 17 additional references using old names without extension (e.g., `ai-coding-methods §5.3.6`, `storytelling-methods §15`). Root cause: file renames are a concept replacement problem, not a string replacement problem. Grep finds literal patterns; context engine finds semantic references.
   - **Pre-push hook regex updated:** `.claude/hooks/pre-push-quality-gate.sh` line 66 — two-stage grep for new filename patterns (bash ERE doesn't support lookbehinds). Test regex at `test_hooks.py` uses Python lookbehind equivalent.
   - **Technique stack:** Golden baseline (130p/675m), Expand-Migrate-Contract (Fowler), side-by-side diff verification, 4-agent review battery (contrarian HIGH, code-reviewer HIGH, coherence-auditor HIGH, validator HIGH).
   - **Agent template hashes updated:** coherence-auditor, voice-coach, continuity-auditor (3 of 10).
   - **Gate 4 tagged:** `const/gate-4`. Revert: `git reset --hard const/gate-3`.
   - **Governance:** PROCEED (`gov-5edd3be84850`, `gov-32ee5170dd6d`, `gov-20cb64e8792a`, `gov-21e4e6faeadc`).
   - **Tests:** 1175 passing (30 new from including previously-deselected slow tests).
   - **Deferred to Phase 5:** Principle counts in ai-instructions.md (stale), missing UI/UX+KMPD from ai-instructions.md, body version mismatches in ai-coding-cfr/multi-agent-cfr, move v3/v4 parallel docs to archive, Article ordering (user decision), old section names in Historical Amendments.
   - **Next:** Phase 5 (cross-references, documentation & polish) — low-risk, ~2-3 hours.

93. **Constitutional Framework Alignment — Phase 3 COMPLETE**
   - **New principles:** Unenumerated Rights (Art. IV, § 4) and Reserved Powers (Art. IV, § 5) as G-Series. Originally drafted as S-Series Amendments IV-V, reclassified by contrarian review — S-Series = safety-critical harm prevention, these are governance-structural.
   - **New methods:** Elastic Clause (Part 8.7) — derived authority for novel situations with 5-step procedure + overuse signal. Full Faith and Credit (Part 9.7.6) — cross-domain output recognition with fraud exception.
   - **Surgical edits:** Equal Protection sentence (Part 9.7), Impeachment emergency fast-path (Part 9.6.3), Evidence question numbering fix (§9.8.1 "Question 5" → "Question 4").
   - **Q0 removed (dogfooding result):** Admission Test Q0 (Purpose Alignment) failed its own Q4 (Evidence — no concrete failure case). Research confirmed preambles are interpretive tiebreakers, not standalone filters. Replaced with interpretive tiebreaker paragraph in §9.8.1. Admission Test stays at 6 questions.
   - **Counts:** 22→24 principles, G:3→G:5, S:3 unchanged. Version: constitution v4.0.0→v4.1.0, methods v3.23.2→v3.24.0.
   - **3-agent review battery (3 rounds):** All HIGH confidence, all PASS. Coherence auditor found 6 stale count references (all fixed). Contrarian caught S-Series misclassification + Q0 rubber-stamp problem.
   - **Gate 3 tagged:** `const/gate-3`. Revert: `git reset --hard const/gate-2`.
   - **Governance:** PROCEED (`gov-ffe9ae782b13`, `gov-6d5e2ca7301a`, `gov-8b26e03def61`, `gov-90f25de1e710`).
   - **Tests:** 1145 passing.
   - **Next:** Phase 4 (file renames + domain restructuring) — start in fresh session. Second highest-risk phase.

92. **Constitutional Framework Alignment — Phase 2 COMPLETE**
   - **Core structural change:** Reorganized constitution headers from descriptive naming to Constitutional structure. Article I-IV + Bill of Rights (Amendments). Section N: prefix for Article principles, Amendment N: for Bill of Rights.
   - **Dual-mode extractor:** Handles both old and new document formats simultaneously. Title-stripping regex (colon-anchored lookahead per contrarian F2), Article/Amendment category mappings (longest-first ordering for substring collision prevention), constitutional_ref generation (Art. I, § 1 / Amend. I).
   - **Technique stack:** Golden file snapshot (22-principle regression baseline), parallel document construction (v4.0.0 alongside v3.0.0), Expand-Migrate-Contract pattern (Fowler), transformation map, migration log.
   - **constitutional_ref field:** Added to Principle and RelevantPrinciple models. Plumbed through query_governance, evaluate_governance, get_principle outputs.
   - **46 new tests:** 22 parametrized title regression, category mapping, substring collision, 4 integration tests for constitutional_ref.
   - **4 subagent reviews:** Contrarian (PROCEED WITH CAUTION, HIGH), code-reviewer (PASS, HIGH), coherence-auditor (1 ERROR: Article ordering — deferred as user decision, kept current order), validator (PASS WITH NOTES, HIGH). 7 of 9 findings fixed.
   - **Framework Overview rewritten** to Article/Amendment language. Version bump v3.0.0→v4.0.0.
   - **Gate 2 tagged:** `const/gate-2`. Revert: `git reset --hard const/gate-1`.
   - **Governance:** PROCEED (`gov-74bcb12469b6`, `gov-8b26e03def61`).
   - **Tests:** 1144 passing (after Phase 2, before Phase 3).
   - **Deferred to Phase 5:** Article ordering non-sequential (I, III, II, IV — preserves original reading flow), old section names in Historical Amendments, missing v3.0.0 history entry (Q:3→Q:4).

### Previous Session (2026-04-11)

91. **Constitutional Framework Alignment — Phase 0 + Phase 1 COMPLETE**
   - **Phase 0 (Safety Net):** Tagged `v1.8.0-pre-constitutional` (pushed to remote). Archived constitution v3.0.0 and methods v3.23.2. Created migration tracker. Revert strategy designed (contrarian-reviewed, HIGH confidence): gate-aligned tags on main, not feature branch (contrarian: branch would remove CI from highest-risk phases).
   - **Phase 1 (Declaration + Preamble + Framework Structure):**
     - **Declaration:** User-authored personal narrative — experiential opening ("almost right, which is worse"), first-person journey through prompt→context→intent engineering, five root purposes, US Constitutional provenance ("Not as a metaphor. As an architecture.").
     - **Preamble – Purpose Statement:** User-authored — flows from Declaration, weaves five root purposes into prose, validation clause ("Any content that contradicts them is invalid"), self-application commitment, bridge line ("Here's how it's built.").
     - **Framework Structure:** Replaced old "Legal Analogy Interpretation Guide" (5-level numbered table) with named 7-layer hierarchy. Two-part table: contextual (non-operative) + operative hierarchy. Added Rules of Procedure and Case Law. Integrated SYSTEM INSTRUCTION as blockquote (contrarian required: preserve "SYSTEM INSTRUCTION FOR AI AGENTS" heading). Deleted Design Philosophy section (migrated "consolidated from 47" and "living document" to Framework Structure).
     - **Extractor:** Defensive category mappings for 'declaration', 'preamble', 'framework structure'.
   - **Subagent reviews:** 3 contrarian reviews (all HIGH confidence), 1 coherence audit (2 cross-file stale refs found → deferred to Phase 5), 1 validator (10/10 PASS on revert strategy).
   - **Deferred to Phase 5:** ai-governance-methods.md Part 9.7.1 still says "5-level" (needs 7-layer), Part 9.7.4 Supremacy Clause missing "Rules of Procedure", domain methods preamble tables still 4-row.
   - **Gate 1 tagged:** `const/gate-1`. Revert: `git reset --hard const/gate-1` (or `v1.8.0-pre-constitutional` for full rollback).
   - **Governance:** PROCEED (`gov-946721ddcb74`, `gov-33056c7b8a06`, `gov-a844ec04701c`, `gov-d108a9d75d23`).
   - **Tests:** 1098 passing (30 slow deselected). 128 principles (22 constitution) — all IDs preserved.
   - **Next:** Phase 2 (Articles/Amendments restructuring) — start in fresh session. Highest-risk phase.

90. **AI-Optimized Project Structure Standard — IMPLEMENTED**
   - **Trigger:** Root had 12+ markdown files with mixed purposes (AI memory, human docs, process checklists, tool config). User wanted generalized project organization template for all project types.
   - **Key decisions:** (1) Keep code/document split per Appendix L (contrarian-reviewed — the split was intentionally designed). (2) `staging/` always present for temporary AI input. (3) `workflows/` for process checklists (precursor to future workflow definitions). (4) `documents/` standardized as default project content folder with image co-location per multimodal-RAG R1. (5) `docs/` available as ecosystem standard for human-facing docs. (6) `.claude/plans/` supports multiple plans with Status header lifecycle. (7) API.md, SBOM.md, ARCHITECTURE.md, SPECIFICATION.md classified as AI memory files (structural).
   - **Changes:** Created `staging/` (with .gitkeep) and `workflows/`. Moved COMPLETION-CHECKLIST.md and COMPLIANCE-REVIEW.md to `workflows/` with header notes. Moved `project-constitutional-framework-alignment.md` to `.claude/plans/`. Updated cross-references in AGENTS.md, ARCHITECTURE.md, SESSION-STATE.md, PROJECT-MEMORY.md, MEMORY.md (external), ai-governance-methods.md, ai-coding-methods.md. Added L.8 AI-Optimized Project Structure Standard to Appendix L. Version bump ai-coding-methods v2.35.1 → v2.36.0.
   - **Also:** Pinned contrarian-reviewer subagent to `model: opus` (adversarial reviews always use full reasoning power). Updated hash in server.py.
   - **Governance:** PROCEED (`gov-578ab2229caf`). Key principles: `coding-process-atomic-task-decomposition`, `multi-architecture-agent-specialization-topology`, multimodal-RAG R1 (Image-Text Collocation).
   - **Tests:** 1128 passing.

89. **Context Engine Circuit Breaker Race Condition Fix — IMPLEMENTED**
   - **Trigger:** Context Engine `project_status` showed `watcher_status: circuit_broken` — auto-indexing disabled. User requested health check.
   - **Root cause:** `_atomic_write_json` (filesystem.py) used deterministic temp filenames (e.g., `chunks.tmp`). When two callers — overlapping watcher flushes, daemon + MCP server, or watcher + manual reindex — ran concurrently, the first rename succeeded but the second got `ENOENT` (`.tmp` already moved). After 3 consecutive failures, the circuit breaker tripped permanently. Error logs confirmed: `[Errno 2] No such file or directory: '.../chunks.tmp' -> '.../chunks.json'` pattern across multiple projects.
   - **Fix (two layers):**
     - **Root cause (filesystem.py):** `_atomic_write_json` and `save_embeddings` now use `{pid}.{thread_id}` in temp filenames — concurrent callers (including cross-process) can't collide. Existing `_cleanup_tmp_files` glob (`*.tmp*`) handles new naming.
     - **Defense-in-depth (watcher.py):** `_flush_lock` serializes `_do_flush` invocations — prevents redundant concurrent incremental updates. Non-blocking acquire with re-queue on contention. `try/finally` guarantees release.
     - **Consistency fix (watcher.py):** Error re-queue changed from `_debounce_timer` to `_cooldown_timer` (pre-existing bug: `_debounce_timer` shared with normal debounce path, new file events could cancel the error retry).
   - **Tests:** 3 new tests (concurrent flush re-queue, lock release on success, lock release on error). 1127 total passing (1 pre-existing contrarian-reviewer hash mismatch from other session).
   - **Recovery:** Called `index_project` to reset circuit breaker — watcher back to `running`, index freshly built (4606 chunks).
   - **Review battery:** code-reviewer (2 passes, PASS HIGH confidence), contrarian-reviewer (caught root cause was in `_atomic_write_json` not watcher — led to fixing the structural defect, not just the symptom).
   - **Governance:** PROCEED (`gov-21a5e5fa2deb`). Key principles: `meta-core-systemic-thinking` (root cause: deterministic temp filenames, not concurrent flushes), `meta-core-context-engineering`, `coding-method-circuit-breaker-pattern`.
   - **Deferred:** Circuit breaker auto-recovery (exponential backoff). Currently tripped state is permanent until manual reindex or server restart. Worth adding but out of scope for this fix.
   - **Also explored (not implemented):** `documents/` → `content/` rename analysis. Contrarian review revealed `content` collides with the most-used field name in the codebase. User decided to keep `documents/`.

88. **Constitutional Framework Alignment — PLAN COMPLETE**
   - **Trigger:** User wants to align ai-governance with US Constitutional governance pattern. Two reference docs: `AI_Governance_Detailed_Summary_v4.md` (intent engineering framing, Constitutional mapping), `US_Constitutional_Gap_Analysis.md` (8 missing concepts).
   - **Key decisions:** (1) Full structural alignment, not cosmetic. (2) Dual-layer IDs — slug IDs for machines + Constitutional citations (`Art. I, § 1`) for humans. (3) Title-based domain naming (`title-10-ai-coding.md`). (4) Pattern not analogy — adopt the governance framework pattern, express it for AI governance. (5) Five root purposes (Authority, Process, Protection, Relations, Continuity) in Declaration. (6) Preamble = interpretive context (not operative), enforced via Admission Test Question 0. (7) Storytelling principles apply to Declaration only (communication purpose), not operative governance. (8) Cross-domain numbering collisions fixed via Title-based section numbers.
   - **Plan:** 7 phases (0-6), 5 review gates, ~16-23 hours. Phases 2 (Articles/Amendments) and 4 (file renames) are highest risk. Plan saved at `.claude/plans/project-constitutional-framework-alignment.md`.
   - **8 Constitutional concepts disposition:** 4 additions (Elastic Clause, Unenumerated Rights as Amend. IV, Reserved Powers as Amend. V, Full Faith and Credit) + Admission Test Q0 + 2 surgical edits (Equal Protection sentence, Impeachment fast-path paragraph) + 2 clean cuts (Separation of Powers, Right to Petition — already structurally covered).
   - **Review battery:** 5 contrarian reviews (all HIGH confidence), 1 coherence audit (11 findings, all fixed), 1 validator pass (21/21 PASS). 13 execution-level fixes applied. 0 design-level issues found.
   - **Governance:** PROCEED (`gov-bc32cdf42a50`, `gov-8f560416bc52`, `gov-53ac23d94eeb`). Key principles: `meta-core-structural-foundations`, `meta-core-systemic-thinking`, `meta-method-breaking-changes-major`, `meta-method-framework-hierarchy-reference`.

### Previous Session (2026-04-10)

86. **Context Engine CWD Fallback Bug Fix — IMPLEMENTED**
   - **Trigger:** `query_project` fails with `[Errno 13] Permission denied: 'weakpass_edit'` when called from Claude.ai without `project_path`. User-discovered diagnostic.
   - **Root cause:** `_resolve_project_path()` fell through to `Path.cwd()` unconditionally. MCP server runs on host — CWD is arbitrary, not the caller's project. Same bug class as governance server #50 (fixed 2026-04-05), not propagated to Context Engine.
   - **Fix:** (1) `_looks_like_project()` validates CWD has project markers before using as fallback. (2) Three handlers (`query_project`, `index_project`, `project_status`) return actionable errors with `list_projects` hint when no path resolves. (3) SERVER_INSTRUCTIONS + tool schema descriptions updated for web client guidance. (4) Fixed hardcoded `Path.cwd()` in project_status "not indexed" message.
   - **Tests:** 14 new (7 marker detection, 4 resolver CWD fallback, 3 handler None-path). 1125 total passing.
   - **Contrarian review (documentation approach):** REVISIT (HIGH confidence). "This isn't a documentation problem, it's a code duplication problem." Two servers implement path resolution independently. LEARNING-LOG entry added as rationale record. Shared resolver deferred as structural prevention (new backlog item #87).
   - **Governance:** `meta-governance-continuous-learning-adaptation` (capture + learn from recurrence), `meta-core-systemic-thinking` (root cause = code duplication, not missing docs). PROCEED.

84. **README Rewrite — Content Captured to Backlog**
   - User working on new README in Claude app with "intent engineering" framing. Draft content captured as Discussion item #84 to prevent session loss. 7 core components, governing philosophy, differentiator, open architecture.

85. **Content Enhancer Integration — Plan Mode Exploration → Workflow Pattern Discovery**
   - **Trigger:** User wants Content Enhancer (standalone methodology at `~/Documents/Reference/AI/`) integrated into ai-governance.
   - **Plan mode:** Initial proposal (TITLE 17) → contrarian REVISIT (HIGH confidence) → user reframed structurally.
   - **Key insight:** The Content Enhancer may be an instance of a workflow pattern, not a standalone integration. Framework already has unlabeled workflows (Completion Sequence, Compliance Review, Session Protocols). #55 (Workflow Codification) may be the infrastructure layer; Content Enhancer the first concrete instance.
   - **Open question:** What distinguishes a "workflow" from a "method"? Paused for deeper discussion before implementation.
   - **Three paths remain:** (A) governance constraints only, (B) first instance of #55 workflow infrastructure, (C) hybrid from #55 discussion.
   - Backlog #55 updated with cross-reference. New item #85 created with full exploration context.
   - **Governance:** `meta-core-systemic-thinking` (user's reframing was more structural than initial placement analysis), `meta-core-context-engineering` (content preservation). PROCEED.

### Previous Session (2026-04-09)

82. **Happy Engineering Appendix F.1 Review + Appendix Template Fix — IMPLEMENTED**
   - **Trigger:** User-requested dogfooding review — did we follow our own templates when adding F.1?
   - **3-agent assessment battery:** contrarian-reviewer, validator, coherence-auditor. Found entry structurally sound but lacking practical detail (prerequisites, framework integration, version pin, discovery keywords, verification date). Coherence audit found SESSION-STATE #57 stale (title, appendix reference, terminology).
   - **Root cause (systemic):** Framework's §9.8.3 appendix template had no guidance for external/third-party tools. F.1 gaps were symptoms of this structural gap, not a one-off miss.
   - **Contrarian review of plan (round 2):** Challenged template expansion scope — n=1 insufficient to expand base template from 5→11 items. Accepted: affirm base template, add surgical extension for external tools. Defer full redesign until n>=3.
   - **F.1 fixes:** Keywords line, Maturity row, verified date, prerequisites (Node.js/npm), version pin (happy@1.1.4), GitHub repo (github.com/slopus/happy), framework integration note, updated risk note (crossed v1.0, 49 versions).
   - **Template fix:** §9.8.3 base template affirmed (removed "since no formal template exists yet"), external-tool extension added (4 items).
   - **SESSION-STATE #57:** Title updated (removed Happy, added Sequential Thinking), body fixed (count, appendix reference, terminology).
   - **Governance:** `meta-core-systemic-thinking` (root cause: template gap, not F.1-specific), `meta-quality-verification-validation` (3-agent battery + 2 contrarian rounds), `multi-quality-validation-independence` (independent subagent reviews). PROCEED.
   - ai-coding-methods v2.35.0 → v2.35.1. governance-methods v3.23.1 → v3.23.2.

83. **Happy Engineering Security Review — COMPLETED (no file changes)**
   - **Trigger:** User requested security due diligence before using the tool on iPhone.
   - **Online research:** 17.6K GitHub stars, maintainers verified (ex-Telegram engineer, Robinhood AI engineer), no CVEs, no security incidents, no Snyk/Socket.dev advisories. Not endorsed by Anthropic. No formal security audit disclosed.
   - **Security-auditor code review:** 11 findings (2 critical, 4 high, 4 medium, 1 low). Critical findings are by-design (bash RPC = full shell access is the tool's purpose; relay sees metadata but not content under new encryption). Key actionable: verify `~/.happy/access.key` is `0o600`, treat mobile app as root-equivalent credential.
   - **Secure patterns confirmed:** E2E encryption is real (AES-256-GCM, client-generated keys), Zod schema validation, Ed25519 device auth, path traversal protection on file handlers, open-source relay (self-hostable).
   - **User decision:** Acceptable risk given iPhone biometric auth + iOS sandboxing. Setup confirmed working.
   - **Governance:** ESCALATE (S-Series triggered correctly for security review of third-party tool with filesystem access). Proceeded with user authorization.

### Previous Session (2026-04-08)

81. **Session Compliance Audit → Systemic Interventions — IMPLEMENTED**
   - Validator subagent audit: 64% structural, 67% semantic compliance. Root cause: advisory instructions degrade under cognitive load (same as ADR-13, #71).
   - 3 structural fixes (none depend on broken LEARNING-LOG): (1) Plan template gate text strengthened for contrarian review, (2) CLAUDE.md skip list clarified — analysis ≠ read-only, (3) UserPromptSubmit hook enhanced — startup read check for PROJECT-MEMORY + LEARNING-LOG in first 50 transcript lines.
   - V-004 added: contrarian compliance over 3 sessions (validator subagent evaluates).
   - 2 LEARNING-LOG entries: contrarian-skip pattern + analysis-not-read-only.
   - Governance: `meta-core-systemic-thinking`, `meta-governance-continuous-learning-adaptation`. Contrarian + validator reviewed plan (4 rounds of refinement).

80. **Difficulty Classification (D1-D3) — IMPLEMENTED**
   - 3-level scale added to Backlog Philosophy. All 20 items tagged with difficulty + type (Fix/Improvement/New Capability/Docs/Maintenance). Contrarian-reviewed: simplified from 4 to 3 levels, dropped unpredictable "files touched" anchor.

79a. **Happy Engineering — Installed + Documented in Appendix F.1**
   - Installed via `npm i -g happy`. Documented in `ai-coding-methods.md` Appendix F.1 with 3-way comparison table (/remote-control vs Happy vs Dispatch), setup references, principle alignment (`multi-reliability-state-persistence-protocol`, `multi-reliability-observability-protocol`), and risk note.
   - SESSION-STATE #57 updated — Happy items complete, Warp/cc-status-line/Sequential Thinking still pending.
   - Governance: PROCEED. 1111 tests passing.

78. **Governance Compliance Review Checklist — IMPLEMENTED**
   - **Root cause:** No recurring mechanism to verify governance system health. Behavioral regression checks were ad-hoc (buried in plan steps). Per `meta-core-systemic-thinking`, the structural gap is "no verification loop" not "forgot one check."
   - **Research:** Perplexity Deep Research (38 citations) + contrarian-reviewer subagent. NIST AI RMF, ISO 42001, EU AI Act all validate periodic review. Contrarian REVISIT verdict: cut 12 items to 7, eliminated AI self-assessment (sycophancy bias), focused on verification experiments as primary value.
   - **Changes:** (1) COMPLIANCE-REVIEW.md created — 7 observable ongoing items, 3 behavioral canary prompts (user evaluates, not AI), 3 verification experiments (V-001 UBDA few-shot, V-002 checklist hook, V-003 startup reads), governance performance metrics landing zone, review log. (2) AGENTS.md updated — Memory Files table. (3) SESSION-STATE.md updated — Active backlog item #78 with first review due ~2026-04-20. (4) PROJECT-MEMORY.md updated — compliance review decision + governance metrics home.
   - **Key design decisions:** Hybrid cadence (10-15 days + event triggers). User spot-check via canary prompts addresses sycophancy bias (Science 2026). Verification items expire to prevent checklist ossification. <15 min target per Gawande (5-9 items). No hooks — advisory proportional to 1-person project.
   - **Governance:** `meta-governance-continuous-learning-adaptation`, `meta-quality-verification-validation`, `multi-quality-validation-independence`. PROCEED.

77. **UBDA External Review Improvements — IMPLEMENTED**
   - **Three independent reviews:** Perplexity Deep Research (47 citations), Gemini 2.5 Flash, Perplexity meta-review of our plan. Architecture validated by all three. Causal model flagged as oversimplified.
   - **Key insight:** Framework already documented 3.5/5 degradation mechanisms — scattered without unified model. Fix was connecting existing knowledge, not discovering new mechanisms.
   - **Changes:** (1) Few-shot WRONG/RIGHT examples in CLAUDE.md from real project failures, (2) reminder anchor at end of CLAUDE.md (recency bias, avoids competing representations per arxiv 2602.07338), (3) causal model corrected to 5-mechanism in LEARNING-LOG with mechanism→intervention mapping, (4) Surface 4 classification criteria updated with mechanism dimension in COMPLETION-CHECKLIST, (5) review findings captured in reference memory.
   - **Deferred:** Session lifecycle automation, semantic compliance monitor, Agent Stability Index, context pollution automation, single-session intent alignment drift — all with revisit triggers.
   - **Governance:** `meta-method-validation-protocol`, `coding-method-project-instruction-file-pattern`. PROCEED.

76. **Close Advisory Governance Compliance Gaps — IMPLEMENTED**
   - **Root cause:** Advisory behaviors skip under autoregressive forward-continuation bias. Existing #73 architecture (behavioral floor + tiers.json) handles this — gaps were an unused surface + a design improvement, not a new problem.
   - **Contrarian review:** Hook proliferation risk accepted → zero new hooks. Auto-log replaces ceremony. Session startup deferred to measurement.
   - **Changes:** (1) `evaluate_governance` auto-logs reasoning entry (server.py) — eliminates `log_governance_reasoning` compliance gap by design, (2) cite-principles added to tiers.json behavioral_floor — Layer 2 reinforcement using #73 architecture, (3) reasoning_guidance text updated to reflect auto-logging, (4) session startup compliance tracker added to effectiveness tracking.
   - **Governance:** `multi-method-governance-enforcement-architecture`, `meta-method-validation-protocol`. PROCEED.
   - tiers.json v1.3.0 → v1.4.0. 5 new tests, 1 updated.

75. **Task Tools Auto-Approve — settings.local.json updated**
   - 6 tools added to project allow list: TaskCreate, TaskGet, TaskList, TaskOutput, TaskStop, TaskUpdate. All internal conversation management with no external side effects. Follows same pattern as #74.

74. **Auto-Approve Governance + CE MCP Tools — settings.local.json updated**
   - 13 tools added to allow list: all governance read-only tools, context engine tools, WebSearch. Eliminates ~20-30 manual approval prompts per session. Requires session restart.
   - Kept blocked: scaffold_project, capture_reference, install_agent, uninstall_agent (create files). Edit/Write .claude/hooks/* (protect safety mechanisms).

73. **Unified Behavioral Directive Architecture — IMPLEMENTED**
   - **Root cause:** Always-active directives scattered across 19 surfaces. No classification system. CLAUDE.md used verbose paragraphs when check-question format is more effective.
   - **Contrarian review (REVISIT → revised):** Universal floor only fires on governance calls; behavioral directives needed during non-action interactions. CLAUDE.md must remain primary surface. tiers.json is additive reinforcement, not replacement.
   - **Implementation:** (1) CLAUDE.md Behavioral Floor section (top of file, compact check-question format), (2) tiers.json behavioral_floor (additive reinforcement, separate from universal_floor), (3) server.py extended to inject behavioral items, (4) Classification system added to COMPLETION-CHECKLIST, (5) Verbose Conversation Style and Technical Decision Presentation sections removed from CLAUDE.md.
   - **Architecture:** CLAUDE.md = primary (always loaded, every interaction). tiers.json behavioral_floor = reinforcement (governance calls). Feedback memories = staging area. Hooks = structural gates for mechanical checks.
   - tiers.json v1.2.0 → v1.3.0. 3 new tests (1106 total).

72. **Technical Decision Presentation — IMPLEMENTED**
   - CLAUDE.md section added with WRONG/RIGHT anti-patterns. Feedback memory saved. Same approach as conversation style fix (~85% compliance via redundant surfaces).
   - Per `coding-process-human-ai-collaboration-model` Decision Authority Matrix. Not hook-enforceable (can't detect question type in transcript grep).

71. **Completion Sequence Structural Enforcement — IMPLEMENTED**
   - **Root cause (systemic thinking):** COMPLETION-CHECKLIST.md was never opened during #1B-P2 implementation. 3 rounds of user-requested "double checks" caught security vulnerabilities, doc drift, index staleness, test gaps — all covered by existing checklist. Meta-action failure (0% — never opened), not item-level compliance (85%).
   - **Contrarian review:** Advisory-only rejected (own LEARNING-LOG says advisory is weakest intervention). #47 single-action precedent inapplicable to multi-step checklists.
   - **Implementation:** (1) Pre-push hook Check 4 blocks push if COMPLETION-CHECKLIST not read, (2) Security checklist item 12 promoted to ENFORCED, (3) PROJECT-MEMORY added to propagation awareness, (4) LEARNING-LOG entry, (5) MEMORY.md step 5 added, (6) Effectiveness tracking table below.
   - **Governance:** `coding-process-validation-gates` (Checkpoint Act), `coding-method-post-change-completion-sequence`, `meta-core-systemic-thinking`. PROCEED.

70. **Backlog #47 Plan Mode Enforcement Gap — CLOSED (Phase 0 success)**
   - Memory effectiveness test: 3/3 sessions, contrarian review invoked unprompted every time. Advisory + feedback memory is sufficient. Phase 1 hook not needed.

69. **Backlog #1B-P2 Cross-MCP Governance Enforcement — IMPLEMENTED**
   - **Research verdict:** Real gap, not AI over-caution. 30 CVEs in 60 days, real incidents (Supabase, Asana). Authorization (OAuth/HITL) != governance evaluation — orthogonal concerns no gateway addresses natively.
   - **Contrarian review (HIGH confidence):** Rescoped from "build gateway product" to "make existing proxy configurable." enforcement.py was already a generic stdio proxy — Phase 2 = ~130 lines to make GovernanceEnforcer data-driven + shared state coordination.
   - **Implementation:** `--govern-all`, `--config`, `--always-allow`, `--cross-mcp` CLI flags. Shared state file (`~/.ai-governance/enforcement-state.json`) for cross-process coordination. YAML config support. Example config for GitHub MCP.
   - **Documentation:** §4.6.2 updated (2026 gateway table, auth vs governance distinction, fixed decision tree dead-end), SPECIFICATION.md scope updated, ARCHITECTURE.md diagram updated.
   - **Tests:** 32 new tests (59 total in test_enforcement.py), 1103 total passing. Code review: PASS WITH NOTES, all HIGH items fixed. Validation: 6 subagent reviews (validator x2, coherence auditor, test validator, security auditor, extractor check), all findings addressed. Security hardening: future timestamp clamping (M5), non-overridable field denylist (H1). Index rebuilt (813 entries).
   - **Governance:** `meta-core-systemic-thinking` (root cause: agents taking actions without governance consultation), `multi-method-gateway-based-enforcement-platform-agnostic`, `coding-method-mcp-compliance-enforcement-patterns`. PROCEED.

68. **Backlog #56 Context Window Management — CLOSED (no changes)**
   - **Root cause analysis:** Premise was factually incorrect — "comprehensive theory but no concrete threshold" is wrong. Framework already has 4 concrete thresholds: 50% distillation (multi-agent-methods.md:1770), 60% prune (ai-coding-domain-principles.md:504), 80% offload (ai-coding-domain-principles.md:504), 32K hard limit (ai-coding-domain-principles.md:527). Sub-agent dispatch for context overflow already explicit in MA-J1 Justified Complexity. cc-status-line is tooling scoped to #57.
   - **Contrarian review (HIGH confidence):** All 5 challenges accepted. Video validated existing content rather than revealing gaps. Adding 50% threshold would create threshold proliferation and layer a content-creator's rule of thumb alongside research-backed thresholds.
   - **Governance:** `meta-core-systemic-thinking` (root cause over symptoms), `evaluate_governance` PROCEED.

---

## Session Summary (2026-04-06)

### Completed This Session (2026-04-06)

66. **Backlog #26+29 Content Quality Governance — CLOSED**
   - Both sub-items resolved by existing structural mechanisms (pre-push gate, CI ceiling, §14.2.7 for security, coherence-auditor, §9.8.5 on-demand). Version-milestone trigger rejected as disproportionate — non-security content lacks external standard anchors to drift from.

67. **SESSION-STATE cleanup — remove closed/historical sections**
   - **Root cause:** Working document accumulated historical state redundant with git history in 3 places: closed items in Discussion, Closed/Reference section, Historical Detail section (~430 lines total).
   - Removed all closed backlog items, Completed Backlog Items table, Closed/Reference section, Historical Detail section.
   - Added backlog philosophy guidance: "When an item is closed, remove it entirely. Git is the archive."
   - Fixed: duplicate #53 header, stale #10 archive reference, stale "Closed" category references.

65. **Security Content Currency Process (Backlog #7) — CLOSED**
   - **Root cause:** Governance content (methods, principles, subagent definitions) had no staleness detection against external security standards (OWASP, MITRE ATLAS, NIST). Reference library had KeyCite currency (§15.4.4), project docs had §14.2, but governance methods had nothing.
   - **Research:** AI security evolves fast — OWASP now has 3 Top 10 lists (LLM 2025, Agentic Dec 2025, MCP 2025), MITRE ATLAS updates monthly-quarterly (v5.3.0 added MCP cases Jan 2026), NIST has multiple parallel AI security tracks. 43% of public MCP implementations had command injection flaws.
   - **Design:** Extended Part 14.2 (not new Part 9.9) per contrarian review — reuses existing staleness pattern, avoids 3-way fragmentation. Visible currency map table, 3-tier source monitoring (category-based), event-triggered review with 90-day fallback, coherence-auditor integration (advisory, honest about enforcement level).
   - **Contrarian review:** REVISIT → accepted 5/6 challenges. Key: Part 14.2 extension vs new Part (~70% less surface area), visible table vs invisible HTML comments, event-triggered primary vs quarterly ceremony, category-based sources vs hardcoded names, connect gap detection to §9.6 Modification Protocol.
   - **Inaugural review:** All security content current against OWASP LLM 2025, OWASP Agentic 2025, OWASP MCP 2025, MITRE ATLAS v5.3.0, NIST SP 800-207. No gaps found.
   - **Files:** ai-governance-methods.md (§14.2.7, v3.23.1), coherence-auditor (currency map check), security-auditor (currency awareness), server.py (hashes). 1073 tests passing.

## Session Summary (2026-04-05)

### Completed This Session (2026-04-05)

64. **scaffold_project Cowork Fix — show_manual + Path Resolution + Mount Documentation**
   - **Two independent root causes:** (1) MCP server runs on host Mac, sandbox paths don't exist on host — path resolution failed silently or resolved to wrong directory. (2) Cowork sandbox paths can exist without being mounted — files written to unmounted paths don't persist.
   - **Code fixes:** Priority reorder (explicit arg > MCP roots), `show_manual=true` mode returns file contents so LLM creates files with its own sandbox-accessible tools, observability (resolved_path/project_root in responses), diagnostic logging.
   - **Documentation:** Appendix L updated — corrected "runs inside sandbox" to "runs on host", documented show_manual workflow, added mount prerequisite warning to Cowork Project Instructions template.
   - **Tested in Cowork:** Confirmed fix works — scaffold_project with show_manual returns content, LLM creates files in mounted workspace.
   - **Reviews:** Contrarian review challenged architecture redesign proposal (don't write files at all) — correctly identified install_agent show_manual as proven pattern to copy. Code reviewer PASS.
   - **Tests:** 3 new tests. 1073 total passing.

63. **External Content Evaluation Methodology Improvement**
   - **Root cause:** The LEARNING-LOG "Start from Gaps, Not Borrowing" rule (from Atlas evaluation) was over-generalized — correctly scoped for principle-level admission but over-applied to method-level quality evaluation. Result: "7/10 covered" summaries filter out implementation-quality improvements.
   - **Fix (Deliverable 1):** (1) Added scope boundary to LEARNING-LOG rule distinguishing principle-level admission (Admission Test applies) from method-level improvement (content improvement, no Admission Test needed). (2) Added "Method-level reflection" prompt to Part 9.8 evaluation workflow — for each covered concept, ask whether the external implementation suggests a more concrete threshold, actionable workflow, or better packaging.
   - **Contrarian-reviewed:** Challenged 4 assumptions. Key finding: the Admission Test is fine (it already distinguishes levels via "at this level") — the blockage was evaluator behavior shaped by an over-generalized lesson, not a methodology gap. Rejected formal "quality comparison step" as scope creep that reopens intellectual generosity bias. Accepted targeted fixes instead.
   - **Deliverable 2 captured:** Video re-analysis produced 4 backlog items (#54 Superpowers reference, #55 workflow codification, #56 context threshold + sub-agent framing, #57 tooling appendix — Warp, cc-status-line, Happy Engineering, Sequential Thinking) with full research context preserved.
   - **Double-check finding:** Sequential Thinking MCP server was missed by both original and re-analysis — only caught by contrarian reviewer. Root cause: no enumeration verification step in Part 9.8 for unstructured sources. Fix: added two-pass extraction (concepts pass + artifacts pass) with explicit item count before coverage assessment. This is a recall problem (items not found) vs. the earlier precision problem (items found but not deeply analyzed).

62. **Content Quality Structural Enforcement (Backlog #25) — CLOSED**
   - **Root cause analysis:** The principle authoring checklist is advisory (~85% compliance). A full PreToolUse hook was rejected — it can only enforce mechanical compliance (agent invocation) not substantive quality (Admission Test honesty), creating false confidence. The contrarian reviewer is the real quality gate.
   - **Three mechanisms implemented:** (1) Pre-push gate requires contrarian-reviewer, coherence-auditor, or validator for governance principle file changes (constitution + domain principles). (2) CI principle count ceiling (35/domain) catches accretion structurally — multimodal-rag at 32 triggers a warning. (3) Existing consolidation pass (Part 9.8.5) remains the systemic cleanup.
   - **Also fixed:** Broken constitution regex in pre-push hook (`ai-interaction-principles-.*\.md` matched zero files).
   - **Research:** Gawande Checklist Manifesto (automate the automatable), industry shift from checklists to continuous assurance, AI agent gateway patterns.
   - **Reviews:** Contrarian review challenged 6 assumptions — accepted narrowing reviewers to governance-specific agents, simpler counting approach, excluding methods files.
   - **Tests:** 17 new tests (1 ceiling + 16 regex parametrized). 1053+ total.

61. **Fix Path.cwd() Bug Class — install_agent, uninstall_agent, scaffold_project (Backlog #50) — COMPLETE**
   - **Root cause:** Missing caller-context propagation. `Path.cwd()` in MCP server resolved to server's directory, not calling session's project. Context Engine had already solved this with `_resolve_project_path()`.
   - **Fix:** 4-tier project path resolution via `_resolve_caller_project_path()`: (1) MCP roots via `list_roots()` (cached per session), (2) `project_path` tool argument, (3) `AI_GOVERNANCE_MCP_PROJECT` env var, (4) CWD fallback with warning. Applied to `install_agent`, `uninstall_agent`, `scaffold_project`, and `_detect_claude_code_environment()`.
   - **Security hardening:** `_is_within_allowed_scope()` path validation, `asyncio.wait_for` timeout on `list_roots()`, proper URI parsing via `urllib.parse.urlparse` + `unquote`.
   - **Structural prevention:** Renamed resolver `_resolve_agent_project_path` → `_resolve_caller_project_path` with docstring: "Any MCP tool that writes files to the CALLER'S project must use this resolver."
   - **Performance:** Cached `list_roots()` result per session to avoid 2s timeout on every tool call when client doesn't support roots.
   - **Reviews:** 3-agent battery (code-reviewer, security-auditor, coherence-auditor) on initial fix. Second code-reviewer + coherence-auditor pass after scaffold fix. Contrarian review challenged 5 assumptions — accepted 2 (roots caching, CI grep check), deferred 1 (env var consolidation), acknowledged 2 (CWD fallback design, capture_reference audit).
   - **Tests:** 15 new tests across 4 classes. 1052 total passing.
   - **Deferred:** (1) CI grep check for `Path.cwd()` allowlist — genuinely structural prevention. (2) API.md tool count staleness (11→13, 15→17) + missing scaffold_project/capture_reference docs — pre-existing. (3) Env var consolidation (AI_GOVERNANCE_MCP_PROJECT vs AI_CONTEXT_ENGINE_DEFAULT_PROJECT) — UX paper cut.

60. **Continuity Auditor + Voice Coach Subagent Rewrites (Backlog #51, Agents 8-9 of 9) — #51 COMPLETE**
   - **Continuity auditor improvements:** (1) Knowledge ledger as core analytical technique — build per-character fact tracker (character, fact, source scene, how learned) before any checking. (2) Confidence tiers on all findings (high/medium/low) with presentation guidance. (3) Added checks: causal chain integrity, dangling threads, spatial consistency. (4) AI difficulty ratings per check (knowledge-state = hardest, object tracking = easiest). (5) Input contract. (6) Creative intent respect — flag with confidence, don't assert.
   - **Voice coach improvements:** (1) Cover test elevated as highest-value capability. (2) AI-specific voice failure checklist: over-articulation, therapy-speak, emotional over-labeling, register uniformity, loss of silence, vocabulary flattening — with why each happens. (3) Multi-dimensional voice analysis table (diction, syntax, register, pragmatics, markers). (4) Confidence tiers with creative intent guidance. (5) Input contract. (6) "Less is more" for markers — flag both insufficient AND excessive density.
   - **Research:** Professional continuity editing (TV writers' rooms, script supervisors), knowledge-state formal model, linguistics of idiolect/register/diction, voice convergence detection, AI creative writing failure modes.
   - **Backlog #51 COMPLETE.** All 9 agents rewritten: code-reviewer, security-auditor, contrarian-reviewer, test-generator, validator, coherence-auditor, documentation-writer, orchestrator, continuity-auditor, voice-coach. (10 counting the code-reviewer done earlier in the session.)
   - Synced to all three locations. Hashes updated.

59. **Orchestrator Subagent Rewrite (Backlog #51, Agent 7 of 9)**
   - **Root cause:** Agent was governance-first (correct) but lacked task classification, delegation heuristics, conflict reconciliation, and specialist input contracts. Would over-delegate simple tasks and under-coordinate complex ones.
   - **Key changes:** (1) Orchestrator Separation Principle — explicit "you NEVER do domain work" with reasoning. (2) Task coupling classification — independent (parallel), sequential, tightly-coupled (don't split). (3) Effort scaling heuristics — simple=in-context, single-domain=1 agent, multi-concern=sequential, complex=parallel. (4) Delegation complexity floor — don't delegate when overhead exceeds value. (5) Specialist input contracts — what each agent needs when delegated to. (6) Shared assumptions brief for parallel delegation. (7) Conflict reconciliation protocol — when subagents contradict, check evidence strength, tiebreaker agent, or escalate. (8) Task classification in output format.
   - **Research:** LangGraph/CrewAI/AutoGen patterns, UC Berkeley MAST taxonomy (79% failures are coordination), Anthropic research system, Cognition counter-position (context > parallelism for coupled tasks), Factory.ai context compression, DeepMind delegation paper.
   - Synced to all three locations. Hash updated.

58. **Documentation Writer Subagent Rewrite (Backlog #51, Agent 6 of 9)**
   - **Root cause:** Agent was generic "write clearly" without the decision heuristics that separate good from great documentation — no Divio quadrant classification, no anti-padding discipline, no AI failure mode awareness, no audience-first protocol.
   - **Key changes:** (1) Divio 4-quadrant classification (tutorial/how-to/reference/explanation) — required before writing, never blend. (2) Anti-padding discipline — banned filler words (simply, just, easily, comprehensive, robust), value test per sentence. (3) AI failure mode self-check — padding, signature parroting, fabricated examples, obvious-over-surprising, copy-paste test. (4) Input contract. (5) Documentation proportionality — match investment to interface stability. (6) Format-specific patterns expanded — README checklist, Python Google-style and TypeScript JSDoc with good/bad contrasts showing semantic value vs signature restatement. (7) Scope boundary with coherence-auditor.
   - **Research:** Google Developer Documentation Style Guide, Divio/Diataxis documentation system, Microsoft Writing Style Guide, AI documentation failure modes research, README best practices, documentation-as-code principles.
   - Synced to all three locations. Hash updated.

57. **Coherence Auditor Subagent Rewrite (Backlog #51, Agent 5 of 9)**
   - **Root cause:** Agent was already the strongest — had tiered audits, 5-check protocol, severity classification. But lacked cross-file semantic checks (SSOT violations, terminology inconsistency, ripple analysis), input contract, severity calibration guidance, sampling honesty, and evidence standards.
   - **Key changes:** (1) Input contract — scope, tier, trigger. (2) Cross-file consistency checks elevated to Step 4: SSOT violation detection (references vs restatements), terminology consistency (same concept/different names), ripple analysis (change-triggered downstream checks), completeness parity (parallel docs missing elements). (3) Volatile facts inventory — build per-file list of hardcoded values with canonical sources. (4) Severity calibration guidance — same staleness type has different severity depending on context. (5) Evidence standard tightened — exact file:line and text, not "seems outdated." (6) Sampling honesty — state what was audited vs what exists. (7) Terminology inconsistency section in output format.
   - **Research:** Stripe/AWS/Microsoft drift detection, cross-reference integrity (markdown-link-check, remark), legal cross-reference systems (CFR), SSOT detection patterns, terminology concordance analysis, AI false-positive/negative patterns in coherence checking.
   - Synced to all three locations. Hash updated.

56. **Validator Subagent Rewrite (Backlog #51, Agent 4 of 9)**
   - **Root cause:** Agent was a simple pass/fail checker without meta-validation (evaluating criteria quality), evidence requirements (PASS without evidence = rubber stamp), or uncertainty handling (collapsing ambiguity into PASS).
   - **Key changes:** (1) Meta-validation Step 0 — evaluate criteria themselves before checking artifact. Flag vague predicates, uncheckable items, missing negative criteria. (2) Three verdicts: PASS/FAIL/CANNOT DETERMINE (suppress uncertain-to-PASS collapse). (3) Evidence with every verdict — PASS explains what was found, not just "looks good." (4) Structural vs semantic classification — report separately for honest confidence. (5) Severity tiers: BLOCKER/WARNING/NOTE. (6) Anti-sycophancy framing — "your job is to find what's wrong, not certify what's right." (7) Checklist fatigue guard — batches of 5-7 for long checklists, extra skepticism on later items. (8) Substantive PASS reasoning — "PASS" alone is indistinguishable from rubber stamp. (9) Input contract. (10) Expanded scope boundaries with all sibling agents.
   - **Research:** Gawande Checklist Manifesto, IEEE 1012 V&V, SOC2/ISO 27001 audit methodology, CodeRabbit/SonarQube quality gates, ATDD acceptance criteria structure.
   - Synced to all three locations. Hash updated.

55. **Test Generator Subagent Rewrite (Backlog #51, Agent 3 of 9)**
   - **Root cause:** Agent generated tests but lacked decision heuristics — no test-level selection (unit vs integration vs E2E), no echo chamber self-check, no test doubles strategy, no framework detection, no AI-specific bias correction for under-tested error paths.
   - **Key changes:** (1) Input contract — what to test, acceptance criteria, framework. (2) Test-level selection heuristic — classify by where value lives (logic=unit, wiring=integration, flow=E2E). Testing Trophy model. (3) Echo chamber self-check — "could a wrong implementation pass these tests?" #1 AI test failure mode. (4) Test doubles decision tree — real > fake > stub > mock, mock smell at >5 lines setup. (5) AI error-path bias correction — at least 1 error test per happy-path test. (6) Mutation mindset check — "what single-char change breaks correctness?" (7) Framework detection with idiomatic features (pytest fixtures, vitest vi.hoisted, playwright POM). (8) Property-based testing trigger for transformations/parsers. (9) Scope boundary with code-reviewer. (10) Parsimony principle (Beck) — don't over-test trivial code.
   - **Research:** Google Test Pyramid/Trophy, TDD (Kent Beck), echo chamber (ThoughtWorks ASSESS 2025, CodeRabbit), property-based testing (Hypothesis/fast-check), mutation testing, test doubles strategy.
   - Synced to all three locations. Hash updated.

54. **Contrarian Reviewer Subagent Rewrite (Backlog #51, Agent 2 of 9)**
   - **Root cause:** Agent was procedural ("do 6 steps") without a core analytical technique. Produced formulaic tables that looked thorough but lacked depth. Anchor bias check at Step 6 was structurally undermined — by then, the reviewer had generated hundreds of tokens within the frame being reviewed.
   - **Key changes:** (1) Reframed from "constructive devil's advocate" to "pre-mortem analyst" — "assume failure, explain why" produces sharper analysis than "find what others missed." (2) Moved anchor bias to Step 0 (before analysis, not after). (3) Added input contract. (4) Added core analytical techniques: pre-mortem failure narratives, consequence tracing (3 steps out), steel-man alternative (argue FOR the best competing approach). (5) Added AI-specific failure pattern checks (forward-continuation bias, sycophancy, complexity escalation, framing anchor, "looks complete" fallacy). (6) Added diagnostic indicators from CIA Key Assumptions Check ("how would you KNOW this is wrong?"). (7) Added decision process evaluation (was the right process followed, not just the right answer reached). (8) Added Bash for git history analysis. (9) Added 4th verdict: PROCEED WITH REQUIRED CHANGES. (10) Required substantive PROCEED reasoning — silent approval is a failure mode.
   - **Research:** Pre-mortem (Gary Klein), CIA Structured Analytic Techniques (KAC, ACH, Devil's Advocacy), Red Team methodology, LLM self-critique research (sycophancy as dominant failure mode), Annie Duke/Tetlock decision quality, Amazon "Have Backbone."
   - Synced to all three locations. Hash updated.

53. **Security Auditor Subagent Rewrite (Backlog #51, Agent 1 of 9)**
   - **Root cause:** Agent was a standalone OWASP checker when it should be a technology-aware audit orchestrator using the framework's own security methods (§5.7-§5.8, which are more comprehensive than the agent itself).
   - **6 changes:** (1) Input contract — technology stack, trust boundaries, sensitive data, public vs internal. (2) Framework-routed checklist — 5 always-check + 7 when-relevant items referencing §5.7-§5.8 instead of standalone OWASP table. (3) Data-flow tracing protocol — enumerate inputs → trace to sinks → identify missing sanitization at trust boundaries. Core analytical technique replacing vague "adversarial mindset." (4) Prescribed Bash usage — dependency audit, secret scanning, config checks only. (5) Scope boundary with code-reviewer — code-reviewer catches security basics, security-auditor does deep systematic analysis. (6) Context-dependent severity calibration — same vulnerability class can span severities based on actual exploitability.
   - **New coverage:** AI-generated code patterns (§5.3.5, 2.74x CodeRabbit finding), MCP/LLM tool security (§5.6.5, §9.3), language-specific patterns for JS/TS/Go/Rust (§5.8.2), database/RLS security (§5.8.5), container security (§5.8.6).
   - **Research:** OWASP LLM Top 10 (2025), Agentic Top 10 (2026), Snyk 2026 (340% prompt injection surge), CodeRabbit study, NIST SSDF SP 800-218.
   - Synced to `documents/agents/`, `.claude/agents/`, `~/.claude/agents/`. Hash updated.

52. **Lossy Compression Trap — Context Window Management**
   - Added new pitfall to ai-coding-domain-principles.md Context Window Management section: "The Lossy Compression Trap" — context compaction asymmetrically preserves confident hallucinations while losing nuanced correctness.
   - **Source:** Video evaluation (2026-04-04) — YouTube tutorial on Claude Code workflow. Speaker's "friends don't let friends compact" stance surfaced a failure mode our "context rot" taxonomy didn't name: degradation from lossy compression is mechanistically different from degradation from overflow.
   - **Root cause insight:** Summarization algorithms (and LLM self-summarization) favor confident, simple assertions over hedged, conditional reasoning. When a hallucination was stated confidently 500 tokens ago, it survives compaction. When the correct nuanced answer was stated with caveats, the caveats are stripped.
   - **Framework gap filled:** "Context rot" (A3 failure mode) covered degradation from overflow. This trap covers degradation from compression — a different mechanism with a different prevention (session breaks > compaction, re-verify against sources not summaries).
   - **Video evaluation summary:** 7/10 concepts already covered by framework, 2 not relevant (tool preferences), 1 gap found (this trap). Framework is well-positioned.

51. **Permission Configuration Best Practices (A.5.6 + A.5.7)**
   - **Root cause:** Framework treated permissions as one-time setup with no shared baseline. Every project started from scratch, permissions grew by accretion.
   - **7 changes to ai-coding-methods.md:** (1) A.5.6 Recommended Permission Architecture — layered model, three principles (deny credentials, ask governance files, allow read-only), baselines with JSON examples, accretion problem, never-allow list. (2) A.5.7 Platform-Specific Notes (Claude Code, Gemini, other MCP platforms). (3) A.5.3 hard rule amended — governance files denied at project-level, ask at user-level. (4) Accretion trigger added to A.5.5 (>50 entries). (5) D.6 Gemini permission configuration. (6) Cold Start Kit Scenario A post-scaffold note. (7) Situation Index entry.
   - **Contrarian-reviewed:** Scoped from two templates to one, deny list framed as not-exhaustive, scaffold template mod dropped. Security-audited (resolved A.5.3 contradiction). Coherence-audited.
   - AI-coding methods v2.34.0 → v2.35.0.

50. **Code Reviewer Subagent Rewrite**
   - **Root cause:** Agent was designed around defect detection (6-item checklist) when effective code review is about code improvement and maintainability (Google, Microsoft research). Covered ~60% of what a coding expert reviewer should check.
   - **7 changes:** (1) Input contract — what invoking agent must/must not provide. (2) Keep read-only tools (no Bash — provide diff via contract). (3) Expanded checklist — 8 always-check items + 2 when-relevant, tiered. Added Performance (AI: 8x I/O), Test Quality (echo chamber detection), API Consistency, Dependency Hygiene. Merged Concurrency into Edge Cases, Duplication into Maintainability. (4) Fresh perspective checks — 4 explicit questions leveraging independent context. (5) AI failure patterns folded into checklist as indicators, not separate pass. (6) Severity redefined by impact (CRITICAL = data loss/security/system failure, not just security). (7) Strengthened "fresh context" framing with input contract (kept over "independent judgment" per contrarian).
   - **Synced to:** `documents/agents/`, `.claude/agents/`, `~/.claude/agents/`. Hash updated in server.py.
   - **Research:** Google code review guidelines, CodeRabbit AI vs Human study, Microsoft Bacchelli & Bird 2013, SonarQube/CodeClimate coverage analysis.
   - **Contrarian-reviewed:** 6 challenges accepted (tiered checklist, no Bash, keep fresh context, fold AI patterns, explicit fallback, severity divergence noted). Coherence-audited, validated.

49. **Global Subagent Availability**
   - **Root cause:** Agents were project-local (`.claude/agents/`) when they should be user-level. Claude Code natively supports `~/.claude/agents/` with merge-with-override resolution (project overrides user).
   - **Fix:** Copied all 10 agents from `documents/agents/` to `~/.claude/agents/`. Available in all projects immediately.
   - **Bug found:** `install_agent(scope="project")` uses `Path.cwd()` which resolves to the MCP server's directory, not the calling project. Cross-project project-scope installation is silently broken. Tracked as backlog #50.
   - **Contrarian-reviewed:** Original plan (modify install_agent tool) was REVISITED after cwd bug discovery. Simplified to native file copy.

48. **Structured Q&A Default — Negative Examples for Freeform Conversation**
   - **Root cause investigation:** Three hypotheses — (1) RLHF training bias (confirmed by research as well-documented phenomenon), (2) instruction not surfaced effectively (SERVER_INSTRUCTIONS ~13% compliance, context decay), (3) governance response priming (structured JSON from evaluate_governance primes structured thinking).
   - **Fix 1:** Added negative example (WRONG/RIGHT contrast) to SERVER_INSTRUCTIONS conversation style section in server.py. WRONG example uses prose form, not numbered list, to avoid priming the anti-pattern.
   - **Fix 2:** Added same negative example to CLAUDE.md conversation style section.
   - **Dropped:** GOVERNANCE_REMINDER addition — contrarian correctly identified it mixes formatting preference with safety enforcement in premium real estate.
   - **Testing plan:** Pre-implementation diagnostic (Test D: compare format before vs after governance calls). Post-implementation observation over 2-3 sessions with baseline ~60-70% structured, success threshold <30%. If no improvement, H3 (governance response priming) becomes primary investigation.
   - **Research sources:** Ouyang et al. 2022, Bai et al. 2022, Perez et al. 2023, Liu et al. 2023 (Lost in the Middle), Anthropic prompting guide, Simon Willison, community consensus.

47. **Document Generation Patterns (Part 9.4 + Reference Library)**
   - **Root cause:** Framework assumed "AI outputs" means "code." Web apps frequently produce document artifacts (Excel, PDF, Word) as primary products with zero governance coverage — no methods, no reference entries, no Situation Index entry, no routing keywords.
   - **Part 9.4** added under TITLE 9 (Deployment & Distribution): data/format separation architecture, template assets & branding, download serving patterns (decision tree: direct/streaming/pre-signed URL/background job), library selection quick reference (Python + Node.js with key gotchas), output validation.
   - **2 Reference Library entries created:** `ref-ai-coding-python-pdf-generation` (WeasyPrint vs ReportLab + Docker deployment gotcha), `ref-ai-coding-web-app-file-downloads` (serving patterns with FastAPI/Next.js/Express examples).
   - **2 additional Reference Library entries created (#48):** `ref-ai-coding-node-excel-generation` (ExcelJS over SheetJS CE), `ref-ai-coding-node-pdf-generation` (PDFKit vs Puppeteer vs jsPDF vs pdf-lib decision tree). Research was already done; no reason to defer.
   - **Routing:** Situation Index entry added. `domains.json` keywords updated for document generation terms.
   - **Backlog #6 scope note:** Visual Communication stays scoped to visual design (Tufte/Duarte/Reynolds). Structured document production handled by Part 9.4.
   - **Contrarian-reviewed:** Scoped down from TITLE 10 (5 Parts) to Part 9.4 (5 subsections). Deferred Node.js entries as anticipatory. Coherence-audited, validated.
   - AI-coding methods v2.33.0 → v2.34.0.

46. **Corrective & Cross-Cutting Change Guidance (Session Retrospective)**
   - **Root cause:** Framework quality gates assumed content changes are additive, but mature framework changes are increasingly corrective/editorial. Three symptoms from session 45.
   - **Edit 1:** Added editorial correction scope note to §9.8.5 with bright-line test — changes that alter requires/permits/prohibits/detects need the Admission Test; scope clarifications, navigational cross-references, and factual accuracy fixes are editorial (PATCH without Admission Test). Includes navigational vs. substantive cross-reference distinction.
   - **Edit 2:** Added cross-TITLE scope check to §9.8.5 authoring mode (advisory) — broad scope claims must verify each TITLE's existing coverage via grep + query_governance.
   - **Edit 3-4:** Added bidirectional cross-references between §9.3.1 (truth-source hierarchy) and §9.7.1 (content-classification hierarchy).
   - **Edit 5 (coherence audit fix):** Added forward reference from §9.8.1 to §9.8.5 editorial exemption — "ANY content" → "ANY new or substantially modified content" with see-also for editorial corrections.
   - **Contrarian-reviewed:** Tightened bright-line test from "requires/permits/prohibits" to include "detects violations." Removed "wording improvements" from editorial categories (too generous — agent self-evaluation escape hatch). Added navigational vs. substantive cross-reference distinction.
   - Meta-methods v3.22.1 → v3.23.0. 1037 tests passing. Index rebuilt (803 items).

45. **#36 Part 9.8 Scope Clarification + TITLE 15 Cross-References**
   - **Root cause:** Part 9.8 (v3.16.0) claimed "unified quality gate for all framework content" but only covered governance-normative content. TITLE 15 (v3.14.0) had its own quality process with zero cross-references. Two disconnected quality systems from rapid development (2 versions apart, never reconciled).
   - **Fix:** Scope-clarified "all framework content" → "all governance content" (header + opening paragraph). Added bidirectional cross-references: "Relationship to TITLE 15" in Part 9.8, "Relationship to Part 9.8" in TITLE 15 header.
   - **NOT done (intentional):** Did not expand 9.8 to cover Reference Library — contrarian reviewer confirmed this would be a category error (Admission Test questions like Derivation/Enforceability don't apply to curated artifacts). TITLE 15's quality process (maturity pipeline, KeyCite currency, decay classes) is more appropriate for artifacts.
   - **Subagent reviews:** 2 contrarian reviews (pre-plan + plan), 2 coherence audits (pre-change finding + post-change verification — all 5 checks PASS), governance evaluation (PROCEED).
   - **Coherence auditor finding deferred:** 9.7.1 vs 9.3.1 hierarchy table inconsistency — separate root cause, not in scope.
   - Meta-methods v3.22.0 → v3.22.1. 1037 tests passing. Index rebuilt (803 items).

44. **Reference Library: Doc Corrections & Do/Don't Format**
   - **Trigger:** Context7 Skill Wizard video analysis + user's real Vercel doc-bug experience
   - **Root cause:** Reference Library lacked explicit structure for experiential corrections (where official docs are wrong); existing entries buried do/don't knowledge in prose
   - **Contrarian-reviewed:** 2 contrarian reviews scoped initial 4-infrastructure-change proposal down to proportional template improvements. Rejected: new method section (premature from n=1), backlog #41 activation (wrong trigger criteria), `corrects_docs` boolean (dead metadata). Relocated §7.10.8 → §3.1.5 (wrong section home).
   - **Changes:**
     - Part 15.1: Expanded role description — named "experiential corrections" as knowledge type, articulated complementary relationship with doc-freshness tools
     - Part 15.3.2: Added optional Do/Don't section to entry body template
     - New §3.1.5 Library-Specific Knowledge Sources (ai-coding methods): current docs → known corrections → capture new corrections
     - All 9 reference library entries brought to template compliance: 7 got Do/Don't sections, 6 got placeholder cross-references filled, 6 got `related:` frontmatter added/fixed, HTML entities fixed, stale test counts updated
     - `_criteria.yaml`: New correction-specific suggestion trigger
   - **Subagents used:** 2 contrarian reviews, 1 plan agent, 1 validator, 2 coherence auditors, 1 code reviewer, 1 explore agent
   - **Versions:** governance methods v3.21.0 → v3.22.0, ai-coding methods v2.32.0 → v2.33.0
   - **Tests:** 1037 passing (no code changes)

40. **#38 Version-in-Frontmatter Migration (Backlog #38)**
   - Root cause: version metadata in file paths created O(n) propagation cascade (~30 steps per version bump)
   - Structural fix: filenames handle identity, YAML frontmatter handles metadata
   - Added YAML frontmatter (version, status, effective_date, domain, governance_level) to all 15 governance documents
   - Renamed 15 files to stable names (stripped -vX.Y.Z suffixes)
   - Updated domains.json, config.py _default_domains(), all cross-references
   - Rewrote extractor._check_file_version() for frontmatter-primary validation
   - Deleted documents/archive/ (57 files — git is the archive)
   - Rewrote governance methods §1.1.3, §2.1.1, §5.1.4 for new convention (v3.20.0)
   - 3-agent review caught 4 code issues + 1 dangerous self-contradiction in §1.1.3 — all fixed
   - Tests: 1037 passing (+4 new)
   - Added backlog #47 (Plan Mode Enforcement Gap) from planning session observation

41. **#37 Remove Type A/Type B Domain Classification (Backlog #37)**
   - Root cause: broken taxonomy — Type A (complexity) and Type B (access control) on different axes, only 2/7 domains used it, superseded by §9.1.2's 5-factor table
   - Applied framework's own Part 9.8 Admission Test to evaluate: fails Q1 (gap already covered by §9.1.2), Q3 (no evidence/failure-mode basis)
   - Removed §9.1.1 from governance methods, renamed Part 9.1 "Domain Types" → "Domain Complexity"
   - Removed Type A label from UI/UX principles (current-state only, changelog preserved per §4.3.4)
   - Replaced Type B with standalone "Access: Proprietary" note in KM&PD (concept preserved, taxonomy removed)
   - §9.8.6 Concept Loss Prevention documented in v3.21.0 changelog
   - 2 contrarian reviews: decision validation + execution plan review (4 findings: historical preservation, #31/#28 cross-refs, verification wording, concept loss documentation)
   - Governance methods v3.20.0 → v3.21.0

42. **#40 Completion Checklist Trivial-Change Escape Hatch — CLOSED**
   - Root cause eliminated by #38: the trigger (version-bump string changes in config.py) no longer exists with stable filenames
   - Pre-push hook config.py gate now only fires for substantive changes — escape hatch unnecessary
   - Updated COMPLETION-CHECKLIST.md line 127 (stale version propagation step from #38)
   - Updated #47 cross-reference (removed #40 mention)
   - Backlog: Active (0) / Discussion (20) / Closed (10)

43. **#9P3 Tiered Principle Activation Phase 3 — CLOSED**
   - Admission Test (§9.8.1): fails Q1 (gap covered by Visible Reasoning + tier config) and Q4 (duplication)
   - Contrarian identified visibility-soundness gap: "visible reasoning" ≠ "sound reasoning" — but #34 (Epistemic Integrity) already tracks this
   - Fixed misleading tiers.json label: "Accountable reasoning" → "Visible reasoning" (matches canonical principle name)
   - Cross-referenced #34 as the carrier for reasoning quality concept
   - Backlog: Active (0) / Discussion (20) / Closed (10)

### Previous Session (2026-04-01)

37. **Hermes Agent Evaluation + Self-Improvement Backlog**
   - Thorough evaluation of NousResearch/hermes-agent comparing architecture, procedural memory, governance, feedback loops against ai-governance-mcp
   - Added 6 backlog items (#41-46): auto-staging proposals, feedback loop analysis, progressive disclosure, auto-maturity proposals, content security scanning, conditional metadata
   - Key finding: Hermes auto-creates skills (procedural memory) but with no quality gate; our reference library has better metadata model but no auto-capture. Items bridge this gap.

38. **#39 Bug Fix — CE Date Serialization (Root Cause)**
   - Root cause: `yaml.safe_load()` auto-parses bare dates as `datetime.date` — fails `json.dump()` downstream when chunks persisted to storage
   - Systemic boundary fix: recursive `_normalize_frontmatter_values()` in `DocumentConnector._extract_frontmatter()` converts date/datetime to ISO strings
   - Governance extractor had ad-hoc per-field handling (lines 780-786); CE connector had none — two parse boundaries, only one was guarded
   - Test: `test_date_values_normalized_to_strings` covering flat/nested/list dates + `json.dumps` proof

39. **Universal Floor — Systemic Thinking + Selection Criteria (tiers.json v1.2.0)**
   - Added `meta-core-systemic-thinking` to universal floor: "Root cause: Are you addressing the structural cause, or patching the visible symptom?"
   - Applied root cause analysis to the decision itself: reviewed all 12 constitutional principles against floor criteria. Systemic Thinking was the only always-relevant principle missing.
   - Added `_selection_criteria` field documenting what qualifies for floor: (1) constitutional, (2) applies to every action type, (3) failing to check can't be recovered later
   - Backlog: Active (0) / Discussion (22) / Closed (7)

### Previous Session (2026-03-31)

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

33. **Session Retrospective + #33 Defer vs Fix Now** — governance compliance self-review + philosophy codified
   - Logged governance reasoning trace (`gov-149fdb65ea80`) — was skipped during execution, corrected
   - Added #39 (test_compare_models pre-existing failure) to discussion backlog
   - Added #40 (completion checklist trivial-change escape hatch) to discussion backlog
   - #33 Defer vs Fix Now: codified in CLAUDE.md as decision table (Fix ≤3 files / Defer with tracking / Ask user). Contrarian-reviewed: added scope boundary, task-completion priority, and safe-deferral path. Addresses autoregressive forward-continuation bias + session discontinuity root causes.
   - Part 7.11 (Discovered Issue Triage): promoted #33 to framework-level method in governance methods v3.19.0. 4-category triage (Fix/Defer/Note/Ask), S-Series override, durable deferral requirements, balanced scope signals, cascading discovery limit, batch presentation. Contrarian-reviewed. Cross-referenced from ai-coding §5.1.6. CLAUDE.md references Part 7.11.

34. **Cross-Session Epistemic Hygiene** — 4 debugging governance gaps from external project
   - Root cause: AI treats cached knowledge as fact; framework manages document staleness (Part 14.2) but not technical conclusion staleness
   - **§5.13.2:** Prior Knowledge Audit — pre-diagnostic step with trigger conditions, structured audit template, 5-step differential for documented-pattern-fails. Scoped to protocol entry (§5.13.4 governs mid-protocol resets). Flows into Instrumentation-First (§5.13.3) when cause unclear.
   - **§5.13.6:** 2 new anti-patterns (Stale Conclusion, Documented Pattern Bypass) + 2 checklist items
   - **§5.1.7:** Auth/session/cookie runtime review trigger (content-based, flags for runtime verification)
   - **Code-reviewer agent:** Runtime-sensitive patterns checklist item (flag, don't assert)
   - 3-agent plan review: contrarian (moved from §5.13.4 to §5.13.2, expanded to 5-step, dropped A5), validator (6/6 PASS), coherence (3 findings addressed: scoping vs §5.13.4, ordering vs §5.13.3, trigger conditions for proportionality)
   - ai-coding methods v2.32.0

35. **capture_reference bug fix** — files not written to disk
   - Root cause: handler used `Path.cwd()` then `_find_project_root()`, neither reads `AI_GOVERNANCE_DOCUMENTS_PATH` env var from MCP config. When server runs from client project, falls back to `~/.ai-governance/` or client CWD.
   - Fix: use `_settings.documents_path.parent` (matches extractor, reads env vars). Added post-write verification + absolute_path/project_root in response for debugging.
   - Cleaned stale copies from ai-expert project and ~/.ai-governance/ fallback.
   - 5 reference library entries successfully captured from ai-expert session (9 total).

36. **External framework evaluations** (logged to memory, not framework changes)
   - Vercel "Agent Responsibly" (2026-03-30): validates executable guardrails approach. 2 minor gaps (Production Environment Blindness pitfall, 3-Question PR Checklist for human-AI interaction).
   - CodeRabbit AI vs Human study (2025-12-17, 470 PRs): AI code 1.7x more issues, 2.74x security, 8x I/O. Validates framework, 1 minor gap (Clarity-Over-Efficiency pitfall). Metrics methodology applicable to Backlog #22.
   - Backlog: Active (0) / Discussion (17) / Closed (5)

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

## Security Currency Reviews

#### Security Currency Review — 2026-04-06
**Trigger:** Inaugural review (§14.2.7 implementation)
**Sources checked:** OWASP LLM Top 10 (2025), OWASP Agentic Top 10 (2025/Dec), OWASP MCP Top 10 (2025), MITRE ATLAS (v5.3.0, Jan 2026), NIST SP 800-207, NIST AI 600-1, CWE Top 25 (2024)
**Gaps found:** 0 | **Actions:** None — all content current. Framework already references OWASP Agentic (§5.11.6 ASI01-ASI09), OWASP MCP (§5.6.4), MITRE ATLAS. LLM08:2025 (Vector/Embedding Weaknesses) covered by SEC-Series in multimodal-rag domain.
**Next trigger watch:** OWASP Agentic Top 10 v2 (new list, may update quickly), MITRE ATLAS v5.4+ (agent-focused techniques, Feb 2026), NIST COSAIS final publication

## Next Actions

### Open Backlog

> **Backlog Philosophy (2026-03-30, updated 2026-04-08):** Items fall into two categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it." See also #33.
>
> **No closed/completed items in SESSION-STATE.** When an item is closed, remove it from this file entirely. Git commit history is the archive — commit messages document what was closed and why. Maintaining closed item lists, completed tables, or historical detail sections in a working document is redundant with version control and causes unbounded file growth. If you need closure context for a past item, use `git log --grep="backlog #N"` or search commit messages.
>
> **Difficulty classification (D1-D3).** Every backlog item gets a difficulty tag. Per `meta-quality-verification-validation`, criteria must be observable, not subjective.
>
> | Level | Label | Definition | Observable Indicators |
> |-------|-------|-----------|----------------------|
> | **D1** | Single-session | Completable in one session without plan mode | Docs-only OR known pattern, no new infrastructure, no dependencies |
> | **D2** | Multi-session | Requires plan mode OR spans multiple sessions | New tool/hook/section, moderate research, or depends on 1-2 other items |
> | **D3** | Architecture | Plan mode + external review + broad changes | New domain, cross-cutting refactor, new service, heavy research |
>
> **Rules:** Default to D1 unless indicators push higher. Plan mode → at least D2. New domain or cross-cutting → D3. When uncertain, pick higher. Re-evaluate when starting work — tags are estimates, not commitments.
>
> **Type tags:** Fix, Improvement, New Capability, Docs, Maintenance. Ranked order: fixes first → improvements → new capabilities.

---

### Active (Implement Now/Soon)

78. **Governance Compliance Review — first review due ~2026-04-20** `D1 Maintenance` (10-15 calendar days from creation). See workflows/COMPLIANCE-REVIEW.md. Event triggers: hook/CLAUDE.md/tiers.json modification.

87. **Shared MCP Path Resolver — Structural Prevention for CWD Bug Class** `D1 Fix`
    - **What:** Extract a shared `resolve_project_path()` into a common module (e.g., `src/ai_governance_mcp/path_resolution.py`) that both the governance server and Context Engine import. One implementation, one set of tests, one place to fix.
    - **Why:** The CWD fallback bug occurred twice in 5 days (#50 governance server, #86 Context Engine) because two servers independently implement path resolution. The governance server has a 4-tier resolver (`_resolve_caller_project_path` with MCP roots, project_path arg, env var, validated CWD). The Context Engine has a weaker 3-tier version missing MCP roots support. Documentation didn't prevent recurrence — shared code would.
    - **Also consider:** CI grep check for `Path.cwd()` in server files (flag any usage not in an approved context). This is the structural enforcement equivalent of the PreToolUse hook.
    - **Origin:** Contrarian review of #86 documentation approach (2026-04-10). REVISIT verdict: "This isn't a documentation problem, it's a code duplication problem."

---

### Effectiveness Tracking

**Completion Checklist Consultation (started 2026-04-07):**
Pre-push hook Check 4 now blocks push if COMPLETION-CHECKLIST.md was not read. Track actual effectiveness.

| Session | Date | Task | Checklist Read? | Triggered by Hook? | Notes |
|---------|------|------|----------------|-------------------|-------|
| 1 | 2026-04-08 | #78 Compliance Review | Y | N | Read docs-only section before push |
| 2 | 2026-04-09 | #82 F.1 review + template fix | Y | N | Read content changes section, worked through items |
| 3 | 2026-04-10 | #84 README capture, #85 Content Enhancer exploration | N/A | N/A | No code changes — backlog capture + plan mode only |
| 4 | 2026-04-11 | #89 CE circuit breaker fix | Y | N | Read code changes section, worked through items |
| 5 | 2026-04-11 | #91 Constitutional Alignment Phase 0+1 | Y | N | Read content changes + code changes sections at session end |

**Escalation threshold:** If 2/5 sessions skip → escalate to include specific item verification in hook.
**Success:** 4/5 consulted → close tracking, keep hook as-is.

**Session Startup Read Compliance (started 2026-04-07):**
MEMORY.md says read SESSION-STATE + PROJECT-MEMORY + LEARNING-LOG on session start. Track whether all 3 are read and whether PROJECT-MEMORY/LEARNING-LOG reads change session behavior.

| Session | Date | SESSION-STATE | PROJECT-MEMORY | LEARNING-LOG | Changed Behavior? | Notes |
|---------|------|:---:|:---:|:---:|:---:|-------|
| 1 | 2026-04-07 | Y | N | N | — | Only read SESSION-STATE; missed 2/3 |
| 2 | 2026-04-08 | Y | N | N | — | Only read SESSION-STATE again |
| 3 | 2026-04-09 | Y | Y | Y | Y | All 3 read. LEARNING-LOG informed governance compliance approach; PROJECT-MEMORY informed version bump conventions |
| 4 | 2026-04-10 | Y | N | Y | N | SESSION-STATE + LEARNING-LOG read. PROJECT-MEMORY too large (searched key sections). No behavior change — session was backlog capture + planning, not implementation |
| 5 | 2026-04-11 | Y | Y | Y | Y | All 3 read at session start ("get up to speed from memory files"). LEARNING-LOG informed revert strategy design (multi-mechanism model, advisory compliance ~85%). PROJECT-MEMORY informed Constitutional Alignment plan review context. |

**Decision threshold:** If PROJECT-MEMORY or LEARNING-LOG reads change behavior <2/5 sessions → remove from required protocol (keep as optional). If ≥3/5 → add Layer 3 enforcement.
**Result (5/5 complete):** 3/5 sessions where PM/LL reads changed behavior (sessions 3, 5, and this one). Meets ≥3/5 threshold — consider Layer 3 enforcement.

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

#### 90. Context Engine Circuit Breaker Auto-Recovery (Discussion) `D1 Improvement`

**What:** The circuit breaker in `project_manager.py` has no auto-recovery. After 3 consecutive watcher failures, auto-indexing is permanently disabled until a manual `index_project` call or server restart. A transient burst of rapid edits (e.g., `git checkout` of a large branch) can trip it.

**Discussion needed:** Should the circuit breaker use exponential backoff with retry (e.g., 30s, 60s, 120s, then permanent trip)? This would make transient failures self-healing while still protecting against persistent failures. Trade-off: retries consume resources if the underlying issue is real (not transient).

**Origin:** Contrarian review of #89 race condition fix (2026-04-11). Rated MEDIUM severity.

#### 22. Governance Effectiveness Measurement (Discussion) `D1 Improvement`

**What:** The framework can measure whether `evaluate_governance` was *called* but not whether it *influenced decisions*. Can we measure the framework's actual effectiveness?

**Discussion needed:** Explore what meaningful metrics look like. This isn't about creating a metric for metric's sake — it's about understanding whether governance adds value and how. Could be several smaller metrics tracking different effectiveness aspects. May conclude some aspects aren't measurable and that's fine.

**Possible directions:** Track behavior-changing evaluations (PROCEED_WITH_MODIFICATIONS, ESCALATE), measure retrieval relevance scores over time, track principle citation frequency vs actual influence, qualitative session reviews.

**Outcome:** Either define metrics worth implementing, or conclude the value is qualitative and close this item.

#### 16. Governance Retrieval Quality Assessment (Discussion) `D2 Improvement`

**What:** Governance server uses BGE-small (384d) while Context Engine uses nomic-embed (768d, better benchmarks). But we don't know if the current model is underperforming — users may not notice degraded retrieval quality.

**Discussion needed:** Related to #22 (effectiveness measurement). How do we measure current retrieval quality for governance queries specifically? Is there a way to benchmark governance retrieval that would tell us if an upgrade is justified? Determine justification first, then implement if needed, drop if not — but with a way to measure effectiveness going forward.

**Possible directions:** Governance-specific benchmark queries, MRR/Recall measurements on governance corpus, A/B comparison with nomic-embed on representative queries.

**Outcome:** Either justify the upgrade with data and implement, or confirm current model is sufficient and close.


#### 6. Visual Communication Domain (Discussion → Full Planning) `D3 New Capability`

**What:** Governance for non-coding visual artifacts: presentations, reports, infographics, print design. Separate from UI/UX (different failure modes, evidence bases, tooling). Tufte, Duarte, Reynolds evidence base.

**Status:** Anticipatory — building this before active use so it's ready when needed.

**Discussion needed:** Full planning process per COMPLETION-CHECKLIST domain creation. Scope candidate principles and methods, evidence base review, failure mode identification.

**Scope note (2026-04-03):** Structured document production (Excel workbooks, data-heavy reports, financial spreadsheets) is handled by AI Coding Part 9.4 (Document Generation Patterns). Visual Communication stays scoped to visual design artifacts: presentations, infographics, print design — the Tufte/Duarte/Reynolds evidence base. The distinction: Part 9.4 covers *how to generate and serve document files reliably*; Visual Communication covers *how to design visually effective communication*.

#### 53. Modular Domain Architecture (Discussion) `D3 New Capability`

**What:** Make ai-governance modular so users can spin up with just meta-principles and methods, or with meta + selected domains. Domains should be addable/removable without affecting the core framework.

**Why:** Currently the framework ships as a monolith — all 7 domains are always loaded. A user building only Python web apps doesn't need Storytelling or Multimodal RAG domains. A user focused on content creation doesn't need AI Coding. Modular domains would let users start minimal (constitution + methods only) and add domains as their needs grow.

**Root cause:** The framework was built by accretion — each domain was added as a new file, but the architecture assumes all domains are always present. The extractor, retrieval, and domains.json all treat the domain set as fixed.

**Discussion needed:**
1. Can `domains.json` be made user-configurable (enable/disable per domain)?
2. How does the extractor handle missing domain files gracefully?
3. Should tiers.json principle activation be domain-aware (only activate principles from enabled domains)?
4. What's the minimum viable framework? Constitution + meta-methods + ai-coding? Just constitution + meta-methods?
5. How do cross-domain references work when a referenced domain isn't loaded?
6. Impact on retrieval quality — fewer domains = less noise in results?

**Origin:** User request (2026-04-04). Anticipatory architecture improvement for adoption scalability.

#### 49. Embedding Model Memory Sharing Across Processes (Discussion — Performance) `D3 Improvement`

**What:** Each MCP server process (governance server, Context Engine server, CE watcher) loads its own copy of the same embedding model (BGE-small-en-v1.5) into memory independently. With 2 concurrent Claude Code sessions, this means 5 Python processes each loading the same model + PyTorch runtime — macOS charged ~27 GB across them and triggered a low-memory warning on a 64 GB machine. A 16 GB machine would be unusable with 2 sessions.

**Root cause:** The MCP protocol runs each server as an isolated process with no shared memory mechanism. All 5 processes use the same model (BGE-small, confirmed via metadata.json), but each loads its own copy + its own PyTorch runtime. The duplication is purely architectural — no technical reason these can't share.

**Key finding:** Both governance server and Context Engine already use the same model (BGE-small-en-v1.5, 384d). SESSION-STATE previously documented CE as using nomic-embed — that was stale; nomic-embed was evaluated but never deployed. This simplifies the fix: one model, one process, all consumers call it.

**Why it matters:** Scaling barrier for adoption. Single-session is fine (~130 MB RSS), but multi-session or machines <32 GB will hit memory pressure. macOS low-memory warning triggered on a 64 GB machine with 2 sessions + Docker + normal apps.

**Recommended approach:** Shared embedding service — a single lightweight process loads BGE-small once, other processes call it via IPC/HTTP socket. Benefits: (1) memory drops from 5× to 1× model load, (2) other 4 processes no longer need PyTorch at all (dramatic footprint reduction), (3) no accuracy tradeoffs since it's already the same model everywhere.

**Other approaches considered:**
1. Lazy unloading — saves memory between queries but adds ~2-3s latency per query burst
2. Smaller model — all-MiniLM-L6-v2 (23 MB) but lower quality; evaluated and rejected (2026-02-14, MRR 0.569 vs BGE 0.627)
3. Single unified MCP server — merge governance + CE into one process; breaking architectural change
4. Process pooling — multiple sessions share one server; MCP protocol may not support natively

**Origin:** Session 48 (2026-04-03). macOS low-memory warning with 2 concurrent sessions. Initial investigation incorrectly dismissed Activity Monitor's GB numbers as "just virtual memory" — 26 GB swap + macOS warning proved impact is real.

#### 19. Rampart Integration — Client-Side Enforcement (Discussion) `D1 New Capability`

**What:** Rampart provides shell-level security enforcement (credential theft, exfiltration, destructive commands). Complements MCP proxy and hooks — different root cause. Hooks enforce "did you consult governance?" (process gate); Rampart enforces "is this command safe?" (security gate). Defense-in-depth.

**Discussion needed:** Evaluate whether the incremental security value justifies the setup for a single-developer Claude Code project. Research current Rampart capabilities and rule set.

#### 13. Governance-Aware Output Compression (Discussion) `D1 Fix`

**What:** Long Bash output wastes context window tokens. Build a PostToolUse hook that compresses verbose output while preserving governance/security lines and structured data.

**Discussion needed:** Is this still relevant as context windows grow? Measure actual context consumption from Bash output. If >20% threshold is hit, define the compression approach (per §3.1.4 "build our own" mode to avoid third-party information intermediary risk per §5.6.8).

#### 10. UI/UX Tool-Specific Integration Guides (Discussion) `D1 New Capability`

**What:** Write integration guides for AI-assisted design tools (Figma MCP, Storybook MCP, Axe MCP, Playwright MCP, etc.) as they're adopted. Research already done (candidate tools, risks, token costs documented in git history — search commits for "backlog #10").

**Discussion needed:** Which tools are most likely to be adopted first? What format should integration guides take? Reference the existing research.

#### 11. Autonomous Operations Domain (Discussion) `D3 New Capability`

**What:** Autonomous agent patterns (AO-Series, currently 4 principles in Multi-Agent) may eventually outgrow the multi-agent domain. This would create a dedicated domain for autonomous operation governance — financial compliance, regulatory frameworks, agent marketplace governance, cross-org federation.

**Discussion needed:** Is this anticipatory need real? What would trigger the split? The Domain Creation Criteria (§5.1.0) already defines when to create domains, but the user wants to understand if the AO-Series trajectory warrants keeping this on the radar.

#### 12. Operational / Deployment Runbook Domain (Discussion) `D2 New Capability`

**What:** Framework covers how AI produces code but not how AI handles deployment, infrastructure, and operations. 3 solid practices from viral "AI vibe coding security rules" analysis couldn't be placed in existing domains.

**Discussion needed:** Is this a full domain or should the 3 orphaned practices just be filed in an appendix? Decision factors: are we using AI for deployment workflows? Is the gap growing? Domain vs standalone runbook vs appendix to AI Coding methods?

#### 35. Evaluate Stripe Projects CLI for Appendices (Discussion) `D1 New Capability`

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

#### 79. Apple Mail MCP Server — Tool-Specific Governance Guidance (Discussion) `D1 New Capability`

**What:** Add governance guidance for the [apple-mail-mcp](https://github.com/s-morgan-jeffries/apple-mail-mcp) open-source MCP server (MIT license, pre-release). Enables AI to read, search, compose, send, and manage emails via Apple Mail.app on macOS. 14 exposed tools across read/search, compose/send, attachments, and organization.

**Why it matters for governance:** AI accessing email is a high-sensitivity capability — S-Series (privacy/security), AO-Series (autonomous actions with real-world consequences like sending emails). The server runs locally (no cloud routing) and requires explicit macOS Automation permission, which is good, but it grants access to all configured mail accounts once approved.

**Key governance concerns:**
1. **Placement:** Does this fit as an appendix to an existing domain (multi-agent? ai-coding?), or is there a broader "tool-specific MCP governance" pattern emerging? See also #35 (Stripe Projects CLI) and #10 (UI/UX tool guides) — three tool-specific items may indicate a pattern.
2. **Autonomy on destructive actions:** `send_email`, `delete_messages`, `forward_message` have real-world blast radius. What HITL enforcement? The server has confirmation flows, but governance should define when AI can vs. cannot act autonomously.
3. **Scope of access:** All mail accounts, not per-account. Governance should recommend dedicated AI mail account.
4. **Pre-release maturity risk:** No version tags, 2 contributors, 23 open issues. Same "Established Solutions First" concern as #35.
5. **AppleScript injection surface:** Input sanitization exists but should be security-auditor reviewed.

**Architecture:** Python FastMCP → AppleScript bridge → Apple Mail.app. Local only, no credentials stored, audit logging included.

**When discussed:** Run governance evaluation, consider whether #35 + #79 + #10 indicate a "Tool Integration Governance" appendix or domain pattern. Security-auditor review of the AppleScript bridge.

---

#### 34. Epistemic Integrity — Constitutional Principle (Discussion) `D1 Improvement`

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

**Note (from #9P3 closure, 2026-04-02):** #9P3 closed — the "reasoning quality vs reasoning visibility" concept is now tracked here. Visible Reasoning (Q-Series) covers *visibility* of reasoning; this item covers *quality/soundness* of reasoning. If #34 is closed without shipping, the soundness gap needs re-evaluation.

---

#### 41. Reference Library Auto-Staging Proposals (Discussion — Self-Improvement) `D2 Improvement`

**What:** After sessions involving complex problem-solving (5+ tool calls, novel governance patterns, or trial-and-error workflows), the system proposes reference library entries to the `staging/` directory with `maturity: seedling`. Human reviews staging during completion sequence.

**Why:** The reference library staging infrastructure exists (`staging/` directory, `_criteria.yaml` per domain, completion sequence prompt) but is dormant — `.gitkeep` placeholder, never activated. Hermes Agent's procedural memory (autonomous skill creation) demonstrates the value of automated capture, but their approach lacks quality gates. Our staging path provides the human gate that prevents noise while closing the capture gap.

**What's involved:** (1) Define trigger criteria — what constitutes "worth capturing" (session complexity, novel pattern, user correction that changed approach), (2) Activate `_criteria.yaml` with per-domain capture rules, (3) Build the staging proposal mechanism (likely a new MCP tool or extension to completion sequence), (4) Define the staging review workflow.

**Dependency:** None — staging infrastructure already exists.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes auto-creates skills every 15 tool-calling iterations via background review agent. Our adaptation: auto-propose to staging with human gate, leveraging our richer metadata model (maturity, decay classes, KeyCite currency).

---

#### 42. Feedback Loop Analysis Tool (Discussion — Self-Improvement) `D2 Improvement`

**What:** New MCP tool (e.g., `analyze_feedback_loop()`) that reads existing log files (`feedback.jsonl`, `governance_reasoning.jsonl`, `governance_audit.jsonl`, `queries.jsonl`) and produces actionable proposals: dead principle detection, false positive pattern identification, retrieval gap reports, principle health scoring.

**Why:** We log everything but never analyze the logs to improve the system. The feedback infrastructure exists and is underused (contrarian review finding). Closing the feedback loop is the core mechanism for self-improvement — the system surfaces what it's learned from its own evaluation history, proposing refinements rather than silently modifying itself.

**What's involved:** (1) Define analysis queries (which patterns are actionable), (2) Implement log parsing and pattern detection, (3) Define output format (proposals with evidence, not automated changes), (4) Determine trigger — on-demand tool call vs. periodic analysis. Specific analyses: principles never retrieved in N days, S-Series triggers with >50% false positive rate, queries consistently returning <0.3 confidence, principles with high retrieval but low feedback scores.

**Dependency:** Partially related to #22 (Governance Effectiveness Measurement) — this tool would provide concrete data for that discussion.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes closes the loop via trajectory compression → model training. We can't fine-tune Claude, but we can close the loop by analyzing our own logs to surface improvement proposals.

---

#### 43. Progressive Disclosure for Reference Library (Discussion — Retrieval Efficiency) `D2 Improvement`

**What:** Currently, matched reference library entries return full content in evaluation results. Adopt a tiered retrieval model: Tier 1 (in evaluation results) shows ID, title, summary, maturity/status, confidence — as we do now. Tier 2 (on demand) provides full artifact content via a new `get_reference(id)` tool. Tier 3 (deep dive) includes related references, cross-references, principle links.

**Why:** As the reference library grows, dumping full artifacts into every evaluation result will bloat context. Hermes's 3-tier progressive disclosure (skill index → `skill_view(name)` → linked files) keeps token cost low while making full content available when needed. Our current 9 entries are manageable; at 50+ this becomes a real problem.

**What's involved:** (1) New `get_reference` MCP tool returning full artifact content by ID, (2) Modify evaluation output to show Tier 1 summaries only, (3) Optionally add Tier 3 with cross-reference expansion. Relatively straightforward — the data model already has `summary` fields and cross-reference metadata.

**Dependency:** None — can implement independently.

**Origin:** Hermes Agent evaluation (2026-04-01). Their skill_view progressive loading pattern adapted to our retrieval model.

---

#### 44. Auto-Maturity Proposals from Usage Data (Discussion — Self-Improvement) `D2 Improvement`

**What:** Automate maturity promotion proposals for reference library entries based on usage signals: seedling → budding (retrieved 3+ times with positive feedback), budding → evergreen (retrieved across 2+ projects, no negative feedback in 6+ months), any → caution/deprecated (not retrieved in N months based on decay_class).

**Why:** The maturity pipeline (seedling → budding → evergreen) and KeyCite currency tracking exist but are entirely manual. Usage data from query logs and feedback could drive proposals. This makes the reference library self-curating — entries that prove useful get promoted, entries that go stale get flagged.

**What's involved:** (1) Track per-reference retrieval counts and feedback scores (may need to enhance logging), (2) Define promotion/demotion thresholds per maturity level and decay class, (3) Surface proposals — likely as part of #42's analysis tool output rather than a separate mechanism.

**Dependency:** Benefits from #42 (Feedback Loop Analysis) — the analysis tool would be the natural home for maturity proposals. Could also work standalone with simpler log parsing.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes skills have no maturity tracking at all — all skills are equal weight. Our maturity model is better but currently manual. Automation closes the gap.

---

#### 45. Content Security Scanning for Staging Entries (Discussion — Security) `D2 New Capability`

**What:** Add content security scanning for reference library entries proposed to `staging/`, similar to Hermes's skills_guard (100+ threat patterns across categories: prompt injection, exfiltration, destructive commands, role hijacking, credential exposure, obfuscation).

**Why:** If #41 (auto-staging) is implemented, AI-generated content enters the reference library pipeline without full human review at the capture stage. Content scanning provides defense in depth — catch prompt injection, embedded credentials, or destructive patterns before they land in staging. Currently `capture_reference` has path traversal protection and yaml.safe_load but no content-level threat scanning.

**What's involved:** (1) Define threat pattern categories relevant to reference library content (prompt injection in artifacts, embedded secrets, destructive command patterns in code samples), (2) Implement scanning — could be regex-based like Hermes or leverage existing security-auditor subagent, (3) Integrate with capture_reference tool and staging workflow. Scope is narrower than Hermes's full skills_guard since our entries are markdown + code snippets, not executable scripts.

**Dependency:** Becomes important when #41 (auto-staging) is implemented. Lower priority without it since manual capture already has human oversight.

**Origin:** Hermes Agent evaluation (2026-04-01). Their skills_guard scans every skill write with 100+ patterns, rolls back on block. Our adaptation would be proportional to the actual threat surface.

---

#### 46. Stack/Platform Conditional Metadata for References (Discussion — Retrieval Quality) `D2 Improvement`

**What:** Add optional frontmatter fields to reference library entries indicating technology stack or platform requirements (e.g., `requires_stack: [nextjs, supabase]`, `applies_to: [typescript, javascript]`). Use these in retrieval to filter or de-rank entries irrelevant to the current project context.

**Why:** A Next.js auth pattern is useless in a Python project. We already have domain routing; this adds stack-level filtering within a domain. As the reference library grows across multiple projects and tech stacks, retrieval precision depends on context-appropriate results. Hermes skills declare `requires_toolsets` and `platforms` for conditional activation — same concept applied to our retrieval model.

**What's involved:** (1) Define frontmatter fields (stack, language, platform, framework), (2) Add to ReferenceEntry model and capture_reference validation, (3) Implement retrieval scoring adjustments (similar to existing maturity/status adjustments), (4) Determine how to detect current project context (from Context Engine index? from project files?). The metadata boosting infrastructure already exists in retrieval.py and project_manager.py.

**Dependency:** None — can implement independently. Benefits from Context Engine project awareness for automatic context detection.

**Origin:** Hermes Agent evaluation (2026-04-01). Their conditional activation metadata adapted to our retrieval-based model.

---

#### 54. Superpowers Plugin — Reference Library Entry + Method Assessment (Discussion — from Video Re-Analysis) `D1 Improvement`

**What:** The Superpowers plugin (github.com/obra/superpowers, v4.3.0, 93K+ developers, Anthropic-endorsed) is a methodology-as-code framework implementing a brainstorm→write-plan→execute-plan pipeline using SKILL.md files. It packages several ai-governance principles (orchestration, context isolation, spec-driven development, sequential phase dependencies, atomic task decomposition) into three executable commands that enforce the workflow structurally.

**Why it matters:** Our framework has the principles; Superpowers has the packaging. It implements our Sequential Phase Dependencies as *the only path available* rather than advisory guidance. Plans include "complete, runnable code for each task" — more concrete than our method-level guidance which stops at "decompose into atomic tasks." Sub-agents implement each task with two-stage review, matching our multi-agent architecture patterns.

**Root concept:** This is the most significant third-party implementation of our multi-agent and ai-coding principles working together. Worth studying as a precedent case — not for what principles it covers (we already have those) but for how concretely it implements them.

**Actions:**
1. Create a Reference Library entry: what Superpowers implements from our framework, where its implementation is more concrete than our methods, patterns worth adopting
2. Assess whether our ai-coding methods should have more concrete "plan format" guidance (Superpowers plans specify exact file paths, terminal commands, failing tests, and git commit messages for each task)
3. Evaluate the brainstorm→write-plan→execute-plan pattern against our development sequence planning method for method-level improvements

**Research done:** Builder.io blog, GitHub repo, Geeky Gadgets review, SAP Community guide, ddewhurst blog analysis. Key architecture: SKILL.md files with YAML frontmatter (trigger conditions, process, guardrails) — same pattern as our `.claude/agents/*.md` subagent definitions.

**Origin:** Claude Code workflow video re-analysis (2026-04-05). Previously evaluated as "covered" — re-examined with method-level quality lens per §9.8.2 scope boundary.

#### 55. Workflow Codification — Skills as Standardized Work (Discussion — from Video Re-Analysis) `D1 Improvement`

**What:** Claude Code skills (SKILL.md files) enable repeatable workflow codification — the discipline of identifying, designing, codifying, validating, and iterating AI-assisted workflows. The video's "creature-forge" example shows a user who identified a repeatable process, built a skill, ran it, got failures, iterated with feedback, and now has a reliable automated workflow. This is the PDCA cycle applied to AI workflows.

**Why it matters:** The framework covers learning from failures (Continuous Learning & Adaptation) but not packaging successes into reusable workflows. Skills, n8n workflows, SOPs, work instructions, and subagent patterns are all implementations of the same root concept: standardized work.

**Framework gap:** No formal guidance on WHEN to create a skill, HOW to design one well, or what governance should apply to skill creation. The `install_agent` mechanism is the closest analog but is scoped to governance agents, not general workflow templates.

**Actions:**
1. Add a method section in ai-coding Appendix A (Claude Code Configuration) covering: when to create a skill (repeatable process done 3+ times), skill design principles (self-contained, include error handling, reference governance), the iteration cycle (expect first run to fail, iterate with feedback)
2. Cross-reference to existing `update-config` skill as an example
3. Assess whether this warrants a broader "workflow codification" method or is adequately scoped as Claude Code-specific guidance
4. Determine governance guidance for skill creation: should workflows reference governance principles? What review process?

**Research done:** Official Claude Code skills docs (code.claude.com/docs/en/skills), claude-code-skill-factory GitHub, awesome-claude-code curated list, ProductTalk guide, batsov.com essential skills guide. Key feature: `disable-model-invocation: true` for workflows with side effects (/deploy, /send-slack-message).

**Cross-reference (2026-04-10):** The Content Enhancer integration discussion (#84) surfaced a broader pattern. The framework already has multiple workflows (Completion Sequence, Compliance Review, Session Protocols, Domain Creation, Content Authoring) but no infrastructure for defining and governing workflows as a category. The Content Enhancer may be the first concrete instance of a codified workflow — making this item (#55) potentially the infrastructure layer and the Content Enhancer (#84) a specific workflow running on it. This reframing elevates #55 from "Claude Code skills guidance" to "workflow codification as a framework concept" — with skills being one implementation mechanism. Discussion needed: what distinguishes a "workflow" from a "method" in the framework? See #84 for full discussion context.

**Origin:** Claude Code workflow video re-analysis (2026-04-05).

#### 57. Recommended Tooling Appendix Entries — Warp, cc-status-line, Sequential Thinking (Discussion — from Video Re-Analysis) `D1 Docs`

**What:** Four tools from the Claude Code workflow video that implement existing framework principles as concrete tooling. Happy Engineering documented in Appendix F.1 (2026-04-08). Three remaining candidates for ai-coding appendix entries.

**Warp Terminal (warp.dev):**
- AI-native terminal with side panel for viewing repo files alongside Claude Code conversation, split panes for multiple Claude instances, tabbed sessions
- Implements: `multi-reliability-observability-protocol` (visibility into agent progress), human-in-the-loop review (see plans/specs/code in real-time while talking to Claude)
- Key value: review generated plans and code without leaving the terminal — supports the "don't just click yes to everything" discipline the video emphasizes
- Free, not sponsored

**cc-status-line plugin (`npx cc-status-line@latest`):**
- Adds real-time status bar: model name, context window %, session cost, session duration, git branch, work tree
- Implements: `coding-context-context-window-management` (The Token Economy Act), `coding-method-context-monitoring`
- Key value: makes context % visible without checking manually — directly enables the 50% threshold rule (backlog #56)
- Pairs with #56 — the threshold is useless without a way to see it

**Happy Engineering (happy.engineering):**
- Free, open-source remote Claude Code terminal control from mobile
- Unlike official Claude mobile app: runs on your actual machine, full access to all plugins (superpowers, context7, etc.) and local files
- Implements: `multi-reliability-state-persistence-protocol` (session continuity), `multi-reliability-observability-protocol` (remote monitoring)
- Alternative to Anthropic's Dispatch/remote pairing feature (user has had reliability issues with Dispatch)
- iOS/Android + web app

**Sequential Thinking MCP server:**
- Chain-of-thought reasoning tool that forces step-by-step decomposition for Claude
- Video recommends installing alongside Superpowers to "upgrade thinking powers"
- Implements: `meta-core-systemic-thinking` (structured reasoning), plan-mode workflow principles
- Install: `claude` → "please install sequential thinking MCP server"
- Pairs with Superpowers — enhances brainstorming quality

**Actions:**
1. ~~Evaluate each for Appendix A entry — recommended tooling section~~ → Happy Engineering documented in Appendix F.1 (2026-04-08)
2. For cc-status-line: include the user's exact line 1/line 2 config from the video as a recommended setup
3. ~~For Happy Engineering: compare against Anthropic's Dispatch feature for reliability and governance compliance~~ → Done: 3-way comparison table (/remote-control vs Happy vs Dispatch) in Appendix F.1
4. For Sequential Thinking: evaluate whether it complements or conflicts with our plan-mode template approach
5. Remaining: Warp, cc-status-line, Sequential Thinking still need evaluation

**Origin:** Claude Code workflow video re-analysis (2026-04-05). Low priority — tooling recommendations, not framework changes.

#### 58. Session Lifecycle Automation — Mid-Session Re-Injection (Discussion — from UBDA Review) `D2 Improvement`

**What:** Context degradation accelerates past critical thresholds. Thresholds exist (50/60/80/32K) but no automation triggers behavioral floor re-injection mid-session. UserPromptSubmit hook could check context utilization and re-inject.

**Revisit trigger:** If measurement shows degradation despite few-shot improvement from #77.

**Origin:** Perplexity Deep Research UBDA review (2026-04-07). Research: arxiv 2601.04170 (episodic memory consolidation — 51.9% drift reduction).

#### 59. Single-Session Intent Alignment Drift (Discussion — from UBDA Review) `D2 Improvement`

**What:** Multi-agent immutability rules handle cross-agent intent preservation. But single-session intent drift within one agent's long task is a distinct failure mode (arxiv 2602.07338). User's progressive expression of intent diverges from model's interpretation over turns. Degradation is ~constant regardless of model size.

**Revisit trigger:** If observed in measurement or if sessions regularly exceed 40+ turns on a single task.

**Origin:** Perplexity Deep Research UBDA review (2026-04-07). Research: arxiv 2602.07338 (Liu et al., challenges Laban et al. framing).

#### 60. Semantic Compliance Monitoring — Supervisor Agent (Discussion — from UBDA Review) `D2 Improvement`

**What:** Current measurement is binary (was evaluate_governance called? yes/no). A supervisor LLM checking semantic compliance after each governance call would detect "was this actually a recommendation or a question-disguised-as-recommendation?" NeMo Guardrails implements this as policy compliance rate metric.

**Revisit trigger:** Productionization or multi-user deployment.

**Origin:** Perplexity Deep Research + Gemini UBDA review (2026-04-07). Both flagged quality-of-compliance vs occurrence gap.

#### 84. README Rewrite — Intent Engineering Framing (Discussion — In Progress in Claude App) `D1 Docs`

**What:** New README for the ai-governance project, being drafted in a Claude app conversation. Frames the project as "intent engineering" infrastructure — encoding goals, constraints, quality standards, and decision-making boundaries so AI understands purpose, not just instructions.

**Status:** Active draft in Claude app. Content below is a snapshot to prevent session loss.

**Key framing:** The industry has moved through three phases: prompt engineering (how you phrase a request) → context engineering (what information AI has access to) → intent engineering (what must be achieved and how success is measured). This project operates at the third level.

**7 core components identified in draft:**
1. **Content Enhancer** (High-Fidelity Educational Content Enhancer 3.0) — processing engine for turning raw material into structured knowledge. Separates principles (immutable) from approaches (adaptable). Grounded in Mayer's multimedia learning, cognitive load theory, retrieval practice.
2. **AI-Assisted Development Framework** — 5 core principles (specification prevents iteration, AI is implementation tool not architect, verify everything, quality accelerates delivery, production standards from start), 8-phase sequential process. Technology-agnostic.
3. **Knowledge Domains** — each follows same structure (principles separated from approaches, evidence-based, cognitive load optimized). Anyone can create their own domains.
4. **AI Instructions Layer** — system-level instructions: classification protocols, risk assessment, fidelity requirements, enhancement tags, QA checklists, confidence scoring.
5. **Memory System** — persistent context across interactions: project-level (CLAUDE.md), domain-level (knowledge bases), interaction-level (working style/preferences/decisions).
6. **Workflow & Compliance Layer** — sequential phase requirements, verification checkpoints (DO-CONFIRM checklists), quality gates, documentation standards.
7. **Transparency and Attribution System** — tagging of original vs enhanced content, external research sourcing, reorganization tracking.

**Governing philosophy:** Not making AI smarter — giving it judgment. The infrastructure acts as a filter for contradictory internet knowledge, telling AI what quality looks like and how to evaluate conflicting information.

**Differentiator:** Most AI tools are destination-specific (guide toward a specific outcome). This infrastructure is destination-agnostic — upgrades how AI performs for whatever you're doing. "The GPS, the road kit, the reliability layer — not the route itself."

**Open architecture:** Built-in instructions for others to create, change, and remove their own principles and standards.

**Research context:** Claude app conversation explored "intent engineering" as a term and researched public usage of the concept.

**Origin:** User-initiated README rewrite (2026-04-10). In progress — do not implement without further user direction.

---

#### 85. Content Enhancer Integration — Workflow Pattern Discovery (Discussion) `D2 Improvement`

**What:** Integrate the High-Fidelity Educational Content Enhancer 3.0 into the ai-governance framework. The Content Enhancer is a methodology for transforming raw content (transcripts, lectures, notes, docs, research) into cognitively-optimized reference documents. It currently lives outside the repo as two standalone files.

**Source files:** `~/Documents/Reference/AI/AI High-Fidelity Educational Content Enhancer/`
- `high-fidelity-educational-content-nehancer-3.0-ai-instructions-prompt.md` — system prompt version (for Claude projects)
- `high-fidelity-educational-content-nehancer-3.0-rag-optimized.md` — detailed spec for knowledge base ingestion

**Content Enhancer architecture:**
- **K-Store/A-Store separation** — principles (immutable, 100% fidelity) vs approaches (optimizable). Mirrors the framework's own principles/methods split.
- **4-phase pipeline** — Strategic Analysis & Classification → Content Extraction & Organization → Cognitive Optimization → Enhancement Implementation
- **Evidence base** — Mayer's 12 Multimedia Learning Principles, Cognitive Load Theory, Retrieval Practice, Universal Design for Learning
- **Enhancement tagging** — [SOURCE], [ENHANCEMENT], [EXTERNAL_ENHANCEMENT], [REORGANIZED], [LEARNING_ENHANCEMENT], [CLARIFICATION_NEEDED]
- **Confidence scoring** — 0.0-1.0 for all enhancements
- **Content-type protocols** — video/audio transcripts, technical docs, academic/research
- **Multi-layer QA** — fidelity verification, enhancement quality, learning science compliance
- **Risk classification** — High (medical, legal, safety) / Medium (business, academic) / Low (general educational)

**Plan mode exploration (2026-04-10) — three key findings:**

1. **Initial proposal: TITLE 17 in ai-governance-methods.** Contrarian review returned REVISIT (HIGH confidence). The Content Enhancer is a production workflow, not governance. Full absorption would cause: (a) bloat — 250-400 lines in an already 4,642-line file, (b) atrophy — governance versioning overhead slows the Enhancer's independent evolution, (c) precedent — every methodology becomes a TITLE. Contrarian's steel-manned alternative: governance constraints only (~40-60 line Part 14.7 covering fidelity standards, enhancement tagging, QA criteria) + full methodology stays standalone with Reference Library entry + Context Engine indexing.

2. **User reframed more structurally: "Is the Content Enhancer an instance of a pattern?"** The framework already has multiple workflows that aren't called workflows: Completion Sequence (COMPLETION-CHECKLIST.md), Compliance Review (COMPLIANCE-REVIEW.md), Session Start/End Protocols, Domain Creation (§5.1.0 + Part 9.8), Content Authoring (Part 9.8 + 3-agent battery). Backlog #55 (Workflow Codification) is about building infrastructure for codifying repeatable processes. The Content Enhancer may be a specific workflow running on a workflow infrastructure — #55 being the infrastructure, Content Enhancer being the first concrete instance.

3. **Open question (needs discussion before implementation):** What distinguishes a "workflow" from a "method" in the framework? The completion sequence is a checklist. The compliance review is a guided audit. The Content Enhancer is a 4-phase pipeline. Are these the same kind of thing, or meaningfully different? This determines whether the Content Enhancer gets its own treatment or fits into a broader workflow pattern that also encompasses the existing workflows.

**Three viable paths remain:**
- **(A) Governance constraints only** — Part 14.7 + standalone reference + CE indexing. Simplest. Treats Content Enhancer as external tool with governance guardrails.
- **(B) Content Enhancer as first instance of #55 workflow infrastructure** — Define what a "workflow" is in the framework first (#55), then the Content Enhancer becomes a specific workflow with a standard structure. More systemic but requires #55 to be resolved first.
- **(C) Hybrid** — Something that emerges from deeper #55 discussion. The workflow/method distinction may clarify what the right container is.

**Relationship to other items:**
- **#55 (Workflow Codification)** — potential infrastructure layer; updated with cross-reference
- **#84 (README)** — references Content Enhancer as "Component 1" of the broader AI infrastructure, but the README describes the system; this item is about integrating the Enhancer itself

**Origin:** User-initiated (2026-04-10). Plan mode exploration completed but implementation paused for deeper workflow pattern discussion.

---

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
