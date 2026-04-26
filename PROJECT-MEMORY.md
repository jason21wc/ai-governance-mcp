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
- **Status:** COMPLETE - All phases done, 17 tools (13 governance + 4 context engine). Run `pytest tests/ -v` for current test counts.
- **Repository:** github.com/jason21wc/ai-governance-mcp

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ✓ Passed | 2025-12-26 | Option C (Tier 1 + best of Tier 2) |
| Plan → Tasks | ✓ Passed | 2025-12-26 | Architecture approved |
| Tasks → Implement | ✓ Passed | 2025-12-27 | 90+ test target set |
| Implement → Complete | ✓ Passed | 2025-12-29 | Gate passed at 355 tests, 90% coverage (run `pytest` for current counts) |

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
| §8.3.4 Solo-Mode Self-Application + Push-Workflow Routing Rule | 2026-04-25 | Session-127 codified the framework's `coding-method-solo-mode-workflow` (§8.3.4) for this repo's own development. **Routing rule (now in `workflows/COMPLETION-CHECKLIST.md` Branch Completion preamble):** Trunk direct (Option A) is the default for solo work because the pre-push battery (§5.1.7.1 + §9.3.10 Layer 5) IS the review per §8.3.4 "gates combined but not eliminated." PR (Option B) is available **on-demand** for high-stakes architectural/security/schema-migration changes (time-separation review per §5.1.8 step 4) but is NOT required for any class. Pushes to main are user-mediated via `! git push origin main` — preserves the "AI cannot auto-push to main" structural invariant (the harness default-branch-protection block stays in place). **Pre-existing security gap closed (B1):** project-level `.claude/settings.json` now denies `Bash(gh pr merge:*)` + `Bash(gh pr review --approve:*)`, overriding the user-level `Bash(gh pr:*)` wildcard. Adopters who scaffold from this repo inherit the floor (no AI auto-merge to default branch). **Pre-existing security gap deferred (B2):** 6 hook-bypass envvars lack a uniform audit-log invariant; only `PLAN_CONTRARIAN_SKIP_HOOK=1` audit-logs today. Filed as BACKLOG #135 for shared `audit_bypass()` helper refactor. **Tripwire for re-evaluation:** BACKLOG #134 reopens PR-required-by-class infrastructure question when ≥3 external watchers OR ≥1 external issue/PR appear (today: 0 stars/forks/external PRs in 4 months). **Decision driver:** three independent subagent reviews (contrarian-reviewer audit `ac01f99ca9778410d`, security-auditor `a44b7638cf3d43b52`, coherence-auditor `a670ce08b44e0fe05`) converged on the same finding — adopting PR-required-by-class today would (1) violate §8.3.4's combined-gate rule, (2) add CI latency with no defect-class delta the pre-push battery doesn't already catch, (3) expand prompt-injection surface (PR comments are untrusted per `coding-quality-workflow-integrity §Q5`), (4) build infrastructure for a hypothesized adopter audience that doesn't exist yet. **Workflow Integrity §Q5 reminder added to Option B:** if PR is opened on-demand, subagent review of PR diffs MUST consume `gh pr diff` (code only), not `gh pr view` (description + comments). Plan: `~/.claude/plans/using-ai-governance-and-systemic-cryptic-blossom.md`. Governance: `gov-7083d6c85ffc`. |
| Superpowers Plan + Post-Ship Remediation Arc (5-commit structural-fix bundle) | 2026-04-25 | Session-126 shipped 8-commit Superpowers-informed plan + 5 post-ship remediation commits (Commits 9-13) closing 14 distinct findings across 2 contrarian batteries. Load-bearing structural rules now codified that future sessions must apply: **(1) Canonical pin-discipline rule** (COMPLETION-CHECKLIST item 7c, BACKLOG #130 close commit `4762962`): MINOR-on-MINOR / PATCH-on-PATCH / MAJOR-on-MAJOR for ai-instructions pin updates; pin-lag remediation exception is PATCH regardless of source. Authority: round-2 contrarian HIGH-2 on test-suite-optimization plan (commit `c22e35c`). **(2) §5.1.8 Mid-Execution Checkpoint Protocol with v2.42.1 step 3 written-artifact REQUIRED**: bare "no drift, PROCEED" assertions = checkpoint did not happen (the named anti-pattern). Step 4 external-evaluator pass REQUIRED when step 3 flags drift. Threshold ≥5 file changes OR runtime >30 min OR multi-phase. **(3) §1.3.5 Brainstorming Method gate widened (v2.42.1)** ENHANCED-mode-OR-no-precedent (`query_project("similar implementation in this project")` returns no strong matches) — closes AI-under-calibration anchor-bias gap. **(4) §7.12.1 5th exception + anti-example (v3.28.2)**: covered = research-anchored trigger thresholds with verbatim external-paper citation + automated-trigger function (e.g., §5.1.8's >30 min Agent Drift threshold); NOT covered = planning-band time estimates (e.g., §3.1.2's `Estimate: 2-8 hours`). Distinguishing test in §7.12.1. **(5) §5.1.7.1 Sequenced Two-Stage Review (v2.40)**: Stage 1 mutation-candidate reviewers (code-reviewer/security-auditor/contrarian) before Stage 2 coherence/validation; parallel battery across stages = anti-pattern. **(6) Hook gates `--plan-action-atomicity` + `--tdd-test-existence`** WARN-mode initial; promotion to BLOCK is event-driven via V-007/V-008 with in-band reminder mechanism (WARN messages point at V-series row). **(7) INFLUENCES.md** at repo root: 4-category attribution (Adopted / Inspired-by + modified / Independently-developed equivalent / Considered and rejected); enforcement: advisory|structural per row; 8-pattern Superpowers comparison + 10+ Other Influences. **(8) ai-instructions Changelog v2.8.1-v2.8.4 misbump documented**: kept in place per no-destructive-history-rewrite; canonical rule applies forward; v2.8.5+ correct under canonical rule. Versions shipping: rules-of-procedure v3.28.2, title-10 v2.42.2, ai-instructions v2.8.7. Tests 1395 passing safe subset. Plan: `~/.claude/plans/federated-plotting-karp.md`. Governance trail: `gov-9f960fac0d73`, `gov-71c1d6662fa7`, `gov-6c38e05ddaab`, `gov-adbf247c0f44`, `gov-0d9f7303cbd5`. Five contrarian invocations (v1, v3, post-ship batch 1, post-ship batch 2, plus Pattern G rejection in v3) + coherence-auditor on Commits 3/4/7/9/12. |
| Effort-Not-Time + BLUF-Pyramid Behavioral Floor | 2026-04-25 | Two new methods codified in `rules-of-procedure.md` v3.28.0 closing root-cause behavioral gaps. **§7.12 Effort-Not-Time Estimation** — AI must not estimate future work in time units (minutes/hours/days/sessions). Empirical observation: AI time estimates routinely overrun ground truth 50-100×, driving false-deferral. Permitted indicators: observable surface counts, Hybrid Intelligence Effort framework dimensions (Alaswad et al., Frontiers AI 2026), D1/D2/D3 effort tiers, token budget. Reference-Class Forecasting (Kahneman/Lovallo, PMI 2026; 70-80% empirical hit rate vs <20% inside-view) as calibration discipline. Scope boundary preserves calendar/cadence dates, audit-log durations, code timeouts, explicit user requests for time framing. **§7.13 BLUF-Pyramid Briefing** — User-facing decision briefs must lead with 2-3 sentence Bottom Line Up Front, present 2-3 alternatives max (Hick's Law: 4+ creates choice paralysis), embed risk per option (not separate). 4-5 sections, 3-5 bullets per, 10-20 words per bullet, 300-500 words for 1-pager / 800-1200 for 2-pager. Scope boundary excludes internal technical artifacts (plan files, ADRs, spec documents, audit logs). Both rules paired with: CLAUDE.md Behavioral Floor directives + tiers.json v1.5.0 → v1.6.0 `behavioral_floor.directives` entries + BACKLOG.md D1/D2/D3 definition cleanup (stripped time language). User-driven discovery: pushback on consistent AI time-estimate miscalibration (50-100× overrun) and request for technical-manager-targeted communication format. Web research validated both fixes (Alaswad 2026, Animalz BLUF, BetterUp Minto, Laws of UX Hick's Law, HBR 2026 Trendslop, ACM CHI 2026 LLM Cognitive Biases). Plan: `~/.claude/plans/federated-plotting-karp.md` Commit 1 (ship `7e7ce95`) + Commit 1.5 propagation (ship `b567032`). Governance trail: `gov-9f960fac0d73`, `gov-8e449341b2d3`. |
| Per-Response Reminder | 2025-12-31 | ~30 token reminder appended to every tool response. |
| Hybrid AI Judgment | 2026-01-02 | Script handles S-Series (safety). AI handles principle conflict analysis. |
| Orchestrator-First | 2026-01-02 | Governance structural via orchestrator, not optional. |
| Reasoning Externalization | 2026-01-10 | `log_governance_reasoning` tool for audit trail. |
| Skip-List Governance | 2026-02-01 | Deny-by-default: evaluate unless on skip-list (4 exceptions). Replaces subjective "significant action". |
| Governance Docs In-Place | 2026-02-02 | Source docs edited in-place with changelog notes (not file renames). |
| Methods in evaluate_governance | 2026-02-02 | Reference-only (id/title/domain/score/confidence). Full content via `get_principle(id)`. Top-5 cap. Audit log tracks `methods_surfaced`. |
| Advisory-Only Limitation | 2026-02-16 | Research confirmed: MCP server instructions are probabilistic, not deterministic. Models skip governance calls when confident, in long conversations, or with many tools. Need structural enforcement (hooks/proxy) beyond advisory instructions. See ADR-13. |
| Hard-Mode Enforcement | 2026-02-28 | Flipped PreToolUse hook from soft→hard default. Blocks Bash/Edit/Write until both `evaluate_governance()` and `query_project()` called. 200-line recency window forces re-evaluation after task pivots. Soft-mode escape hatches via env vars. Conditional UserPromptSubmit suppression saves ~11K tokens/50-turn session. Compliance: 13%→expected 90%+ (deterministic enforcement). |
| Subagent Advisory Framing | 2026-02-28 | All 10 subagent templates now include Advisory Output section. Orchestrator has Step 4: Evaluate Subagent Results with §7.10 protocol. SERVER_INSTRUCTIONS includes advisory framing. Findings are advisory input, not authoritative directives; 90% accept/reject threshold signals anchor bias. |
| Tiered Principle Activation | 2026-02-28 | Phase 0: Fixed dead `series_code` via `CATEGORY_SERIES_MAP` (28 entries, domain-aware). S-Series detection now works via metadata, not just keywords. Phase 1: Universal floor tier — `documents/tiers.json` with 3 principles + 3 methods + 1 subagent check injected as `universal_floor` section in every `evaluate_governance` response. Separate from `max_results=10`. Anti-pattern check format ("Did you...?") with principle ID citations. |
| Domain-Aware Hierarchy | 2026-02-28 | `apply_hierarchy()` now uses domain context: constitution principles (S=0,C=1,Q=2,O=3,MA=4,G=5) sort above domain principles (all at 10). Shared series codes (C, Q) no longer collide across domains. Storytelling ethics → "E" (not "S"), multimodal-rag security → "SEC" (not "S"). Only constitution safety → "S" triggers veto. |
| Compliance Review | 2026-04-08 | workflows/COMPLIANCE-REVIEW.md — periodic governance health check (every 10-15 days or on governance system changes). 8 ongoing items (Check 1b added 2026-04-13) + verification experiments. Governance performance metrics live here — only artifact with periodic review cadence. Contrarian-reviewed: AI self-assessment items removed (sycophancy bias); user evaluates canary prompts. |
| Permission Settings Alignment | 2026-04-13 | settings.local.json aligned with CFR Appendix A.5. Removed 3 CFR-violating auto-accepts (chmod, mv, docker push). Added 10 read-only auto-accepts (git status/diff/log/ls-files/show/branch, ls, python3, happy change_title, verify_governance_compliance). Added 8 deny rules (settings.json, CLAUDE.md, .github/*, git push --force). Root cause: settings grew by accretion (103 entries, CFR threshold 50) without CFR compliance checks. 4-agent battery: security auditor found hook bypass vectors, contrarian reframed as SSOT violation (proportional), coherence auditor confirmed CFR contradictions. |
| Failure-Mode Registry + Covers: Annotation Convention | 2026-04-23 | Session-123 shipped `documents/failure-mode-registry.md` (YAML frontmatter SSOT, **initial** 19 entries: 11 must_cover + 8 advisory) + `TestFailureModeCoverage` lint (unknown-id-rejected, must-cover-has-annotation, retired-id-warning, yaml-parses) + `scripts/generate-test-failure-map.py` (AST-based, rot-freshness enforced via pre-commit hook BACKLOG #123-closed) + `workflows/TEST-AUTHORING-CHECKLIST.md` (9-step author-time gate) + CFR §5.2.8 (normative Redundancy & Consolidation rule, MINOR v2.38.5 → v2.39.0). Closes the structural gap §5.2 had — autonomous test maintenance was fix-or-escalate with no consolidate guidance, so redundancy regrew after every cleanup pass. Round-2 contrarian caught original "presence-matching" lint as theatre → registry as ID SSOT closes the typo/ghost-match class; round-3 (2nd-pass post-commit) caught "rot-immune" derived-map claim as false → pre-commit hook closes that too. Known limitation (registry "Why this exists" section): ID-typo + missing-coverage theatre closed; body-vs-annotation semantic theatre requires periodic human sample audit — automation rejected (false-positive surface too broad). Scaffold-safety (framework-universal vs project-specific FM-ID split) deferred as BACKLOG #125 before next external adopter. **Extended session-124 (2026-04-24) via BACKLOG #121 complete-sweep + structural seed-at-creation gate + grandfathered-FM root-cause resolution + ref-lib doc reconciliation + parametrized traversal coverage — registry grew 19 → 39 entries (22 must_cover + 14 advisory active + 3 retired) from Phase 0 (3 must_cover gaps) + Phase 3 (16 gaps from 4-file residual walk) + battery-fix-2 (1 structural-gate FM) + grandfathered-FM cleanup (3 retirements). Annotations: 12 → 69 across 67 tests; 1381 passed + 0 skipped. Must-cover discipline text updated to codify "security/SLA contract" branch. Advisory seed-at-creation gate shipped as STRUCTURAL LINT (test_new_advisory_entries_have_annotation for entries introduced ≥ 2026-04-24). `placeholder: true` schema field added for dormant FMs. **Root cause of 4-month zero-annotation pattern identified + codified in LEARNING-LOG 2026-04-24: registry entries must be binary-checkable via assertion presence; 3 grandfathered FMs were category mismatches (anti-pattern / known-limitation / authoring-convention) retired with lessons preserved in LEARNING-LOG + BACKLOG #129 (S-Series production-fix trigger).** BACKLOG #128 filed for 2 advisory FMs deferred at Phase 0; #130 (ref-lib reconciliation) + #131 (parametrized traversal coverage) closed-shipped same session per fix-now discipline.** |

### Context Engine Cross-Environment

| Decision | Date | Summary |
|----------|------|---------|
| Read-Only Mode | 2026-03-22 | `ReadOnlyFilesystemStorage` subclass + `AI_CONTEXT_ENGINE_READONLY` env var (auto/true/false). Auto-detects read-only filesystems. Query path has zero writes — no mkdir, chmod, tmp cleanup, model download. BM25-only fallback if embeddings unavailable. |
| Project Path Parameter | 2026-03-22 | All 3 data tools (query_project, index_project, project_status) accept optional `project_path`. Resolution: args > `AI_CONTEXT_ENGINE_DEFAULT_PROJECT` env var > CWD. Required for Cowork where CWD=/ (MCP server runs on host, not in VM). |
| Standalone Watcher Daemon | 2026-03-22 | `context-engine-watcher` CLI keeps indexes fresh independently of AI client sessions. Heartbeat (60s), PID file, graceful shutdown. Reuses existing FileWatcher + ProjectManager infrastructure. |
| Platform Service Installer | 2026-03-22 | `context-engine-service` CLI with install/uninstall/status/logs. macOS launchd (RunAtLoad+KeepAlive), Linux systemd (user service+linger), Windows schtasks. Auto-detects platform. |
| Cowork Architecture Insight | 2026-03-22 | Cowork MCP servers run on the HOST, not inside the VM. VM filesystem is a read-only mount of host paths. CWD inside MCP server process is `/`, not the project directory. The fix was `project_path` parameter, not read-only mode (though read-only mode is still valuable for Docker/CI). |
| Repository Security Configuration | 2026-03-22 | New §6.4.10 (10-item checklist, 3 tiers, cross-platform table) and §6.4.11 (CodeQL setup, alternatives). Gap identified: framework said "run scans in CI" but didn't say "configure repository to block merges when scans fail." Appendix H expanded 14→16 items. |
| Design-Before-Build Elevation | 2026-03-22 | §2.4 UX Elaboration elevated from OPTIONAL to IMPORTANT for UI-facing projects. Named the anti-pattern (prompting AI for UI without design reference → rebuild loops). Fix: design artifact first, validate, then implement via Figma MCP. Catalyst: external newsletter analysis of vibe-coding community patterns. |
| Tool Content Model Update | 2026-03-22 | §3.1.4 expanded from "tools we use" to "tools we use or may use." Prospective tools noted as named references under evaluation with user consent before adoption. Prevents useful discoveries from being lost. |
| Intent Discovery (Constitutional) | 2026-03-23 | New C-Series meta-principle in Constitution v2.6.0. "Do industrial engineering on the customer" — assess whether stated request reflects actual need. Proportional skepticism with explicit Dig/Proceed signals. Sibling to Discovery Before Commitment (DBC explores within frame, ID questions the frame). Uses Progressive Inquiry Protocol as implementation mechanism. Evidence: VOC/CTQ, Kano model, Five Whys, XY Problem, IEEE 29148, McKinsey problem definition, Zou et al. 2022, Zhang/Knox/Choi ICLR 2025. Contrarian review: MODIFY accepted — signal list in Operational Considerations, domain calibration added. |
| Skill Preservation Addition | 2026-03-23 | Added Skill Preservation (Exoskeleton Effect) subsection to ai-coding Human-AI Collaboration principle. Cites Shen & Tamkin 2026 (n=52, 17% comprehension reduction with AI delegation). Three high-performing patterns (conceptual inquiry, hybrid code-explanation, generation-then-comprehension) vs three low-performing (delegation, progressive reliance, iterative debugging). Rule: stay cognitively engaged. |
| Folder-Based AI Memory (`_ai-context/`) | 2026-03-22 | New Appendix L in ai-coding methods v2.24.0. `_ai-context/` folder convention for non-CLI AI environments (Cowork, ChatGPT Desktop, any folder-based LLM). Underscore sorts to top, visible, self-documenting. README.md as loader (AGENTS.md equivalent). Memory files inside subfolder for document projects; redirect for code projects. Cowork Project Instructions template for GUI bootstrap. Three bootstrapping paths: conversational (primary), manual (fallback), MCP tool (future). Advisory enforcement only — no hooks in folder-based environments. |

### Content Architecture

| Decision | Date | Summary |
|----------|------|---------|
| AGENTS.md Overlay Pattern | 2026-03-17 | AGENTS.md holds shared project context (50 lines). CLAUDE.md is overlay with governance enforcement + subagent registry only. Governance hooks MUST stay in CLAUDE.md (safety-adjacent, cannot depend on "read another file" directive). ETH Zurich research: keep instruction files lean. |
| Document Kit Tiering | 2026-03-17 | §1.5 defines 3 tiers: Core (4 files, all modes), Standard (+4), Enhanced (+evaluated per §7.10). Avoids file proliferation — Enhanced additions are advisory, not mandatory. |
| Constitutional Framework Alignment | 2026-04-11 | Major restructuring: 14 document files renamed to Constitutional naming (constitution.md, rules-of-procedure.md, title-NN-*.md), headers restructured to Articles/Sections/Amendments, 4 new concepts added, dual-layer IDs (slug + Constitutional citation). 7 phases, 5 review gates, safety anchor at `v1.8.0-pre-constitutional`. Plan: `.claude/plans/project-constitutional-framework-alignment.md`. Revert: gate-aligned tags on main, contrarian-reviewed. |
| S-Series Scope Boundary | 2026-04-12 | S-Series = safety-critical harm prevention (protects users from maleficence, bias, deception). Governance-structural principles (framework integrity, authority distribution) belong in G-Series even when inspired by US Bill of Rights amendments. The operational criteria for S-Series classification is "does this prevent user harm?" not "is this in the Bill of Rights?" Established when contrarian review reclassified Unenumerated Rights and Reserved Powers from S-Series to G-Series. |
| Backlog Separation | 2026-04-14 | Backlog separated from SESSION-STATE.md into BACKLOG.md. Root cause: advisory pruning instructions in CFR (§7.0.4, §7.1.5, §7.6.1) invisible on always-loaded surfaces — SESSION-STATE grew to 1,441 lines (4.8x target). Backlog items are prospective memory (intentions that persist across sessions), not working memory (transient). Fix: pruning instructions added to CLAUDE.md, AGENTS.md, MEMORY.md. Staleness review for discussion items added to COMPLIANCE-REVIEW.md Check 8. Prospective Memory formalized as 6th cognitive type in v2.38.0 (2026-04-15). |
| Template Standardization | 2026-04-14 | All 5 authoring templates reviewed against AI best practices. Method template expanded 5→8 fields (added Applies To + Implements). Constitution template fixed (added elevator pitch). Appendix template formalized from bullets to code block. 648 Applies To entries added across all 7 files. A/B benchmark confirmed +19-61% BM25 score improvements. Best practices research validated Markdown+YAML as optimal format. Key lesson: script-generated content (keyword extraction) produces 0% quality — content comprehension required. Authoring guidance codified with 5 quality criteria. |
| Preamble as Interpretive Tiebreaker | 2026-04-12 | Preambles resolve ambiguity, they don't filter content. Research confirmed across US constitutional law (Joseph Story's Commentaries, Jacobson v. Massachusetts), EU treaty interpretation (Liav Orgad), and corporate governance (Elizabeth Pollman). Q0 (Purpose Alignment) was removed from the Admission Test — failed its own Q4 (Evidence). The Preamble's five purposes inform borderline Admission Test decisions as a tiebreaker, not as a standalone gate. Derivation chain (Q3) is the structural enforcement mechanism for the Preamble. |
| Textual-Function Classification (3 Surfaces, 3 Jobs) | 2026-04-18 | Framework carries three declarative-text surfaces with distinct textual functions. **Declaration** (`constitution.md:18-53`) — aspirational purpose in author's voice, human-first narrative; structurally analogous to US Declaration of Independence. Purposes are not assertions; evidence-check does NOT apply. **Preamble** (`constitution.md:56-62`) — distilled binding purposes, AI-first operative surface invoked as Admission Test tiebreaker per Jacobson v. Massachusetts pattern; human-second contextual reading. Same evidence-check exemption as Declaration. **Operative surfaces** (README, runtime prose, CFR, product-facing docs) — class (c) claim surface; evidence-check applies. Cohort 1 discovery: F-P2-01 failed because the review pattern-matched the Declaration into class (c) and ran an operative-claim evidence-check against aspirational content. Fix the classification before fixing the text. Captured structurally in `constitution.md:79-80` Contextual Layers table (belt-and-suspenders with LEARNING-LOG rule). Supersedes the implicit "all declarative text is claim" assumption that drove the initial F-P2-01 finding. |
| Structural Enforcement Is Cross-Cutting, Not a Hierarchy Row | 2026-04-19 | Constitution v5.0.0 added a "Structural Enforcement (Cross-Cutting)" subsection after the 7-layer Operative Hierarchy table, NOT a new 8th row. Root cause analysis per `meta-core-systemic-thinking`: normative layers answer "what is the rule?" — enforcement mechanisms answer "how is the rule made sticky?" Different questions. Conflating them into one table hides the answer to either. US Constitutional analog preserves the same distinction: Judicial and Executive Branches are *mechanisms applied to* the sources of law, not sources themselves. Framework follows the same pattern: principles and methods are the sources; hooks, CI, subagents, scaffold, Admission Test are the mechanisms. Cross-cutting subsection names all 6 mechanisms with binding-strength categorization (Structural / Advisory / Procedural). Establishes that "missing from the hierarchy" is not always a call to add a row — sometimes the right response is a different structural dimension. F-P1-02 resolution pattern for future similar findings. |
| Case Law → Secondary Authority (v5.0.0 Label Rename) | 2026-04-19 | Constitution v5.0.0 renamed the seventh hierarchy layer from "Case Law" to "Secondary Authority" with Authority column "Informative (non-overriding)". Path B chosen over Path A (admit binding precedent). F-P1-05 root cause per LEARNING-LOG 2026-04-12 "Metaphor-Driven Classification": "Case Law" imported stare-decisis semantics (binding precedent) that the framework explicitly rejects at `constitution.md:101, 112` (non-override). Rename closes the label/operation mismatch at zero new infrastructure cost. "Informative" alone considered; post-edit contrarian added "(non-overriding)" parenthetical to prevent soft-binding misread in isolation. Propagated across 15 files (rules-of-procedure, ai-instructions, README, 6 CFR, server.py). |
| Preamble Purpose Coverage Is Distributed, Not Concentrated (F-P2-13 Path B, v5.0.1) | 2026-04-19 | The Preamble's 5 purposes (Authority, Process, Protection, Relations, Continuity) operationalize distributed across multiple domain principles/methods, NOT via dedicated per-purpose principles. Per `constitution.md:80` Contextual Layers and PROJECT-MEMORY 2026-04-12 "Preamble as Interpretive Tiebreaker," the Preamble is class (b) — AI-first interpretive surface invoked at Admission Test borderline decisions, not a principle-count target. Cohort 3 resolution of F-P2-13 ("Relations thinly operationalized — only 2 principles"): the review applied operative-claim logic (counting principles per purpose) to a class (b) surface, repeating the same category error that produced F-P2-01 in Cohort 1. The fix is at the review layer, not the content layer. Path A (promote Full Faith and Credit method to G-Series principle) was rejected for the same reason: Preamble purposes don't need dedicated principles, and methods/principles are legitimately distinct per-scope abstractions. Rule for future reviews: flag Preamble purpose under-coverage as a finding ONLY if actual governance decisions are failing on that purpose (evidence-gated, not count-gated). BACKLOG #34 (Epistemic Integrity draft) route: closed as resolved-in-place across Cohorts 2 (Path B de-duplicate) + 3 (Path B documentation); no new Epistemic Integrity principle needed since neither cohort produced a gap the existing content doesn't cover. |
| Path B Over Path A for Risk Mit ↔ Non-Mal (F-P2-09, v5.0.0) | 2026-04-19 | Chose de-duplicate-in-place (Path B) over merge (Path A) for Risk Mitigation by Design and Non-Maleficence, Privacy & Security. Pre-edit contrarian steel-manned Path B; root-cause reframe under `meta-core-systemic-thinking` identified the shared *technique* (defense-in-depth, safe defaults, continuous monitoring) as the duplication, not the principles themselves. Each principle has a legitimate distinct *center* — Risk Mit = planning-time posture across all risk dimensions; Non-Mal = execution-time harm prevention. Path A would have imported Risk Mit's broader posture into S-Series, widening the S-Series Scope Boundary (PROJECT-MEMORY 2026-04-12 says "S-Series = does this prevent user harm?"). Path B preserves G-Series=5 + principle count=24, avoids series crossing, avoids `tests/test_extractor.py` breakage, avoids cross-ref churn in `rules-of-procedure.md §7.8` + `title-20-multi-agent.md`. Risk Mit trimmed to posture-only; Non-Mal gained cross-reference sentence + "Over-reliance on Single Defenses" failure mode. Pattern: when a principle-pair shows duplication, check whether it's *technique* duplication (fix by relocation) vs *scope* duplication (fix by merge). |
| Pre-Edit 3-Agent Battery as Defense-in-Depth (2026-04-19) | 2026-04-19 | Cohort 2 ran the 3-agent battery (contrarian xhigh + coherence high + validator high) at BOTH plan-stage and post-edit-stage, not just post-edit. Pre-edit battery surfaced blockers that would have been expensive to fix post-execution: Path B alternative (contrarian steel-manned the merge-vs-deduplicate choice), propagation-list gaps (coherence found 7 additional rules-of-procedure lines + server.py:2052 + README line 60 not 42), "Informative Only" downgrade concern (contrarian). Post-edit battery confirmed clean landing + one additional fix (§9.6.1 → §9.6.3 citation correction by validator). Lesson: for constitutional amendments, run battery pre-edit AND post-edit. The `coding-method-three-agent-assessment-battery` protocol is mandatory post-edit; making it pre-edit as well catches costlier issues cheaper. |
| README Role — Extra-Constitutional Infrastructure | 2026-04-18 | README is NOT a §1 Federalist Papers analog and NOT a duplicate of the Declaration. It's **extra-constitutional infrastructure** — a repository entry-point that serves a practical function no part of the Constitutional pattern serves. Reader model: humans arriving via GitHub browse, package registries, git clones. Questions answered: what is this? how do I run it? where do I learn more? Per `meta-method-single-source-of-truth`: README LINKS to Declaration and Preamble — does not paraphrase or duplicate them (drift risk). Target length: 400-500 lines. Structure: tagline → Problem → Solution → Quick Start → Framework overview (domain table + hierarchy with link) → Architecture → Tool reference → Docker → Contributing → License. Anti-anchor-bias filter applied to BACKLOG #84's 7-component breakdown rejected 2 components that described the not-in-repo Content Enhancer. Established when full rewrite elected mid-Cohort-1 (staging/readme-draft-v1.md, session 114). |
| Appendix M Canonical Home for Adopter-Facing Ecosystem Tools (Capability-vs-Tool Framing) | 2026-04-25 | Session-128 BACKLOG #57 close shipped title-10 v2.43.0 with §3.3.4 Status Bar Plugin sub-paragraph + new **Appendix M: Optional Ecosystem Tools** (M.1 Warp Terminal, M.2 Sequential Thinking MCP Server). **Pattern established (canonical home):** Appendix M holds third-party tool recommendations whose framework value is the principle-slot they occupy (single-best-of-best or category-of-one), structurally distinct from Appendix F (comparison-among-alternatives, multi-tool category like F.1 Happy/Dispatch/`/remote-control` for remote access) and Appendix G (single-tool deep config, framework-internal — Context Engine MCP setup). Entries capture **why we care, how we want to use it, AI-relevant gotchas** per user direction; vendor-resolvable detail (full feature lists, current pricing, full config syntax) deliberately deferred to source links rather than reproduced inline (rot-immune per `meta-method-single-source-of-truth`). **Capability-vs-tool framing (§3.3.4):** when the framework value is the principle (always-visible context telemetry implementing the 60%/80%/32K thresholds in `coding-context-context-window-management`), name the *capability*, list current implementations as starting points (`ccsp` / `@cometix/ccline` / `@hwwwww/pulse` as 2026-04 examples), and let adopters pick by maintainer cadence + config surface. Avoids endorsing a single tool that may rot before the framework version bumps. **Augmentation pattern preserved:** §3.3.4 augmentation did NOT renumber §3.3.5 — matches session-127 §8.3.4 augmentation precedent. **New BACKLOG #136 filed:** retroactive §9.8.3 field backfill across pre-existing appendices (A, F, K, L) authored before §9.8.3 field reference existed — D2 Maintenance, scope-deferred from #57 per `coding-method-defer-vs-fix-now` §7.11 (cascading multi-file audit, >3 surfaces). **Stage 2 battery:** validator 8/8 PASS; coherence-auditor 1 HIGH (BACKLOG #56 dangling-reference — the auto-defer-pattern dovetail; folded across §3.3.4 + Version History + SESSION-STATE in same change-set per the just-shipped feedback rule) + 1 LOW (cosmetic, accepted). **Behavioral-floor learning paired:** session-128 user pushback on auto-defer reflex codified as `feedback_decide_dont_defer.md` (auto-memory, indexed) + LEARNING-LOG entry 2026-04-25 — verdict on Sequential Thinking shipped inline in M.2 body rather than filed as separate evaluation. Versions shipping: title-10 v2.43.0 (MINOR, additive), ai-instructions v2.9.0 (MINOR-on-MINOR per COMPLETION-CHECKLIST item 7c). Session-128 commit `56a9dee`. Governance: `gov-3116c50bb6e7`. CI green (1395 passed safe subset, 2m55s CI / 1m17s CodeQL). |

### Multi-Agent Domain

| Decision | Date | Summary |
|----------|------|---------|
| Scope Expansion v2.0.0 | 2026-01-01 | Covers individual agents, sequential, and parallel patterns. |
| Agent Definition Standard | 2026-01-01 | Required: name, description, cognitive_function, tools, system prompt. |
| Justified Complexity | 2026-01-01 | 15x token cost rule — must justify multi-agent over generalist. |
| Linear-First Default | 2026-01-01 | Sequential is safe default. Parallel requires explicit validation. |
| Task Dependency DAG | 2026-01-24 | Deadlock prevention added to §3.3. Graph traversal, depth tracking, timeout escalation. |
| AO-Series v2.2.0 | 2026-03-09 | New Autonomous Operation series (AO1-AO4): Blast Radius Classification (L0-L3), HITL Removal Criteria (AL-0 through AL-3), Compensating Controls (circuit breakers, content review gates, rate limiting, audit trail, platform compliance), Autonomous Drift Monitoring. 4 failure modes (MA-AO1–MA-AO4). Methods TITLE 6 (§6.1-6.4). Catalyst: OpenClaw autonomous agent architecture analysis. Phase 1 extension — not a new domain yet. Future: full Autonomous Operations domain if evidence base grows sufficiently. Substring collision: `ao-series` must precede `o-series` in category_mapping. |

### Multimodal RAG Domain

| Decision | Date | Summary |
|----------|------|---------|
| Domain Created | 2026-01-24 | v1.0.0 — 12 principles (P/R/A/F series), 21 methods. Priority 40. |
| Retrieval-Only Scope | 2026-01-24 | No generation. Architect for future extensibility. |
| Mayer-Based Image Selection | 2026-01-24 | Three-Test Framework (Coherence, Unique Value, Proximity) replaces arbitrary thresholds. |
| Hierarchy Separation | 2026-01-24 | Principles platform-agnostic. Platform-specific content in appendices only. |
| Content Expansion v2.0.0 | 2026-02-21 | 12→29 principles (+17), ~21→54 methods, 10→23 failure modes. Six new series: V (Verification), EV (Evaluation), CT (Citation), SEC (Security), DG (Data Governance), O (Operations). Plus P6 (Accessibility) and A3 (Vision-Guided Chunking). MR-F23 (Retrieval-Limiting Caption) added post-review. Domain prefix changed `mult` → `mrag`. P-Series category fixed `process` → `presentation`. Research: RAG-Check, MM-PoisonRAG, VISA, CoRe-MMRAG, Vision-Guided Chunking, WCAG 2.1 AA. Extractor bugs fixed: category_mapping substring collisions (ev/v-series, sec/c-series), skip_keyword "operational" blocking O2. Contrarian review completed — 8 extraction tests added. |
| Content Expansion v2.1.0 | 2026-02-21 | 29→35 principles (+6), ~54→63 methods (+9), 23→27 failure modes (+4). One new series: AG (Agentic Retrieval) — AG1 (Adaptive Retrieval Strategy), AG2 (Query Decomposition), AG3 (Retrieval Sufficiency Evaluation). Extended series: V4 (Cross-Modal Reasoning Chain Integrity), A4 (Document-as-Image Retrieval), A5 (Knowledge Graph Integration). New failure modes: MR-F24 through MR-F27. New methods: Title 11 (Agentic Retrieval Patterns, §11.1-11.5), §3.7 (Late Interaction), §3.8 (Graph-Based Retrieval), §5.5 (Multi-Hop Verification). Research: MMA-RAG, MMhops-R1, ColPali, ColQwen2, ColEmbed V2, RAG-Anything, ACL 2025 survey. AG-Series category_mapping placed before A-Series (substring collision). |

### UI/UX Domain

| Decision | Date | Summary |
|----------|------|---------|
| Domain Created | 2026-03-08 | v1.0.0 — 19 principles (VH/DS/ACC/RD/IX/PL series), 36 methods, 16 failure modes. Priority 15. Scope: interactive software interfaces only. ai-coding §2.4/§2.5 = process; UI/UX = substance. |
| Scope Boundary | 2026-03-08 | Separate domain from ai-coding (PROJECT-MEMORY records this decision). Not part of Visual Communication (presentations/docs). Cross-references added in ai-coding §2.4.3 and §2.5.3. |
| AI-Specificity Gate | 2026-03-08 | Hard gate: UX-F4 (Over-Designed Interface) and UX-F11 (Information Architecture Failure) cut for insufficient AI-specific evidence. 16 of 18 survived. |
| Contrarian Review | 2026-03-08 | 4 MAJOR findings: (1) derivation honesty IX5/IX6 — deferred v1.1.0; (2) AI-specificity spectrum — deferred v1.1.0; (3) untestable VH criteria — rejected (checklists, not automated tests); (4) motion accessibility gap — accepted, `prefers-reduced-motion` added to ACC3. |
| Retrieval Quality | 2026-03-08 | All 13 benchmark tests pass post-domain addition. No MRR/Recall degradation. 8/8 spot-checks route to ui-ux as top domain. |

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
| Colon Header Pattern | 2026-02-08 | Storytelling uses `### ST1: Title` (colon). Old header pattern requires dot. Colon headers handled by `new_header_pattern` (line ~772) which catches both formats. Other domains unaffected. |
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
| AI Security Scanning — Distributed | 2026-02-23 | Triggered by Anthropic Claude Code Security announcement. Contrarian review found: (1) most content restates §6.4.9/§5.3.5 in new context, (2) vendor-sourced stats don't meet framework evidence standards, (3) vendor announcement trigger ≠ research/incident trigger. Distributed ~12 lines across §5.3.3, §5.3.5, §6.4.9 instead of new §5.3.7. Full section deferred pending independent benchmarks. Snyk 2.74x XSS finding added to §5.3.5. |
| Agent-to-Service Integration v2.16.0 | 2026-02-23 | New §5.6.7 (~50 lines) + 3 enrichments (~8 lines). Single section with bold-headed paragraphs (not §5.6.7/8/9) — four gaps are facets of one phenomenon. Agent-facing API checklist in §5.6.7 not §5.8.3 (agent-service integration ≠ defending APIs from attackers). WebMCP qualified as [EARLY PREVIEW]; guidance framed around generic "dynamically-discovered tools." Bustamante cited as "practitioner evidence" (lower bar); checklist items independently from OWASP. Contrarian confirmed ~70% genuinely new content. Validator found 2 missing back-references (§5.6.5, §5.6.6 → §5.6.7) — fixed. Tier 3 deferred: B2A procurement governance, agent memory standards, WebMCP standard tracking. Research: W3C WebMCP, Bustamante (2026), OWASP MCP/Agentic Top 10. |
| CE Compliance Enforcement v2.17.0 | 2026-02-23 | New §9.3.10 (~35 lines) documents 4-layer enforcement stack as reusable pattern. Implementation: PreToolUse hook extended for dual governance+CE scan (single pass, adaptive output), UserPromptSubmit adds CE nudge, CLAUDE.md advisory→mandatory, orchestrator gets CE tools. Independent hard modes (CE_HARD_MODE ≠ GOVERNANCE_HARD_MODE). Session-level check (known limitation: coarse granularity after task pivots). 14 hook tests added. Prompted by advisory-only compliance failure during v2.16.0 implementation. |

### Domain Expansion & Content Strategy

| Decision | Date | Summary |
|----------|------|---------|
| Tool-Specific Content Pattern | 2026-02-28 | Generalized/tool-agnostic guidance → methods sections. Specific tools we use and favor → appendix or tool-specific subsection. No comprehensive coverage of every tool — capture what we actively use; add new tools as we switch. Applies across all domains (security, UI/UX, etc.). |
| UI/UX Separate from AI-Coding | 2026-02-28 | UI/UX is a separate domain, not part of ai-coding. Different failure modes (bad interfaces vs. bad code), different evidence base (Nielsen, WCAG, HIG vs. OWASP, CWE), different truth sources (design systems vs. codebases). ai-coding §2.4/§2.5 cover *process* (when to do UX work); UI/UX domain covers *substance* (what good UX is). |
| Procedures → Training & Instructional Design | 2026-02-28 | Expanded thin "Procedures" placeholder into broader Training & Instructional Design domain. Procedures/SOPs are a type of training content — separate domain would be too narrow. Evidence base: TWI, Bloom's, ADDIE, Kirkpatrick, Mayer, etc. |
| Visual Communication Separate from UI/UX | 2026-02-28 | Presentations, documents, infographics, print design are separate from UI/UX. Different failure modes (narrative flow, information density vs. accessibility, interaction design), different evidence base (Tufte, Duarte vs. Nielsen, HIG), different tooling. |
| UI/UX Phase 6 External Review | 2026-03-08 | Perplexity Deep Research reviewed UI/UX domain plan+implementation. 14 findings: 7 ACCEPT, 3 ACCEPT IN PART, 1 REJECT, 3 DEFER. Key additions: IX7 (dark patterns/deceptive design — FTC categories, Serezlic & Quijada 2025), UX-F19 (motion accessibility), 6 evidence citations, 6 methods sections (§3.5 dark pattern screening, §3.6 Core Web Vitals, §6.4 platform convention currency, §9 microcopy governance). i18n deferred to v1.1.0. Agentic UX patterns deferred (too early). |
| Atlas Comparison — No Changes | 2026-02-28 | Evaluated syahiidkamil's ATLAS framework (280 GitHub stars, 33 commits, 0 tests, 0 citations). Contrarian reviewer challenged 5 candidate incorporations — all rejected. Framework reveals no gaps. Our evidence-based, failure-mode-grounded approach covers all substantive concerns with greater rigor. Risk of quality contamination from incorporating unvetted content into an evidence-based framework. |
| Backlog Consolidation (10 → 7) | 2026-02-28 | Rolled up hooks, MCP proxy, governance analytics, CE analytics into single Enforcement & Compliance Infrastructure initiative. Enables systems-level view, avoids unexpected interactions, identifies synergies. Reframed AI Security Scanning watch into Security Content Currency Process. |

### Implementation Details

| Decision | Date | Summary |
|----------|------|---------|
| Mock Strategy | 2025-12-27 | Patch `sentence_transformers.SentenceTransformer` (lazy-loaded). |
| Confidence Thresholds | 2025-12-31 | HIGH ≥0.7, MEDIUM ≥0.4, LOW ≥0.3. Validated — keep defaults. |
| Pre-Flight Validation | 2025-12-31 | `validate_domain_files()` — fail fast on missing config files. |
| Multi-Platform Configs | 2026-01-01 | `config_generator.py` — Gemini, Claude, ChatGPT, Cursor, Windsurf, SuperAssistant. |
| All 10 Agents Installable | 2026-02-21 | `install_agent`/`uninstall_agent` expanded from orchestrator-only to all 10 agents. `AGENT_METADATA` dict provides per-agent descriptions, action summaries, activation messages. Non-Claude users receive agent definition content as adaptable reference. Templates in `documents/agents/`. CI content scan covers `documents/agents/*.md`. |

### Context Engine

**Provenance:** Inspired by [Augment Code](https://www.augmentcode.com/context-engine)'s Context Engine — a cloud-hosted, per-developer semantic indexing system that maintains a live understanding of entire codebases. Our implementation adapts the core concept (semantic project search via embeddings + hybrid retrieval) for a local-first, single-user, privacy-preserving architecture. Key differences: Augment uses custom-trained code embeddings on cloud GPUs, quantized ANN search for 100M+ LOC scale, per-developer branch-aware indices, and cross-repo awareness. We use open-source models locally (BAAI/bge-small-en-v1.5), tree-sitter AST chunking, and per-project indexes with on-demand or file-watcher indexing. See ADR-12 for the full comparison analysis.

| Decision | Date | Summary |
|----------|------|---------|
| Reference Memory Concept | 2026-02-02 | Cognitive memory type: "what exists and where is it?" Complements Working/Semantic/Episodic/Procedural/Prospective. See ADR-5 for full taxonomy. |
| Shared Repo, Separate Entry | 2026-02-02 | Context engine lives in `src/ai_governance_mcp/context_engine/`. Separate MCP server entry point (`ai-context-engine`). |
| One Server, Multi-Project | 2026-02-02 | Single MCP server manages per-project indexes. Auto-detects by working directory (hash of absolute path). |
| Hybrid Search (reused) | 2026-02-02 | Same BM25 + semantic pattern as governance server. Configurable weight (default 0.7 semantic / 0.3 keyword; tuned from 0.6 on 2026-02-14). |
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
| Model Allowlists | 2026-02-10 | Embedding (6 models) and reranker (5 models) allowlists in `retrieval.py`. CrossEncoder now uses `trust_remote_code=False`. Mirrors context engine's allowlist pattern. |
| Symlink Protection | 2026-02-04 | `list_projects()` skips symlinks. `delete_project()` unlinks symlinks instead of `rmtree`. File discovery already filtered. |
| Atomic JSON Writes | 2026-02-06 | `_atomic_write_json()` uses tmp file + rename for crash safety. POSIX atomic guarantees. |
| Circuit Breaker Visibility | 2026-02-06 | `watcher_status` field in ProjectStatus exposes state (running/stopped/circuit_broken/disabled/not_loaded). |
| Eager Watcher Startup | 2026-02-27 | `startup_watchers()` method pre-warms embedding model and loads realtime projects at boot in daemon thread. Watcher no longer waits for first query. `"not_loaded"` status distinguishes unloaded from stopped. `AI_CONTEXT_ENGINE_INDEX_MODE` added to MCP config. |
| _ensure_watcher Helper | 2026-02-28 | Idempotent watcher lifecycle helper: no-op if running, restarts stale (in dict but dead), respects circuit breaker. Separate from `_start_watcher` (low-level primitive) because `reindex_project` explicitly clears circuit breaker before calling `_start_watcher` — adding CB checks to `_start_watcher` would break that flow. `is_running` hardened to check `_observer.is_alive()`. CE v1.2.1. |
| Bounded Pending Changes | 2026-02-06 | MAX_PENDING_CHANGES (10K) with force-flush prevents unbounded memory growth. |
| Language-Aware Chunking | 2026-02-06 | Code connector uses BOUNDARY_PATTERNS per language for better chunk boundaries. |
| CI Context-Engine Extras | 2026-02-07 | CI must install `.[dev,context-engine]` — `pathspec` in optional extras needed by tests. |
| Incremental Indexing | 2026-02-12 | File-level granularity: classify UNCHANGED/MODIFIED/ADDED/DELETED via content hash. Reuse embeddings for unchanged chunks. Manifest LAST save ordering (commit record). `content_hash=None` → MODIFIED (legacy safety). |
| Schema + Chunking Version | 2026-02-12 | `schema_version` (int) and `chunking_version` (str, e.g. "tree-sitter-v1") in ProjectIndex. Mismatch triggers full re-index in incremental path. |
| Tree-sitter Language Pack | 2026-02-12 | Replaced `tree-sitter>=0.21.0` with `tree-sitter-language-pack>=0.7.0,<1.0`. 6 priority languages (Python, JS, TS, Go, Rust, Java). Non-priority → line-based fallback. Large defs (>200 lines) split at nested boundaries. |
| File Watcher Env Var | 2026-02-12 | `AI_CONTEXT_ENGINE_INDEX_MODE` env var (ondemand/realtime). `reindex_project` uses env var, not stored metadata (fixes contrarian O9). |
| BM25 Negative Score Fix | 2026-02-12 | `np.clip(scores, 0.0, 1.0)` in `_bm25_search` — BM25Okapi can return negative IDF for common terms in small corpora. |
| Query Freshness Metadata | 2026-02-12 | `last_indexed_at` and `index_age_seconds` in query responses. Server differentiates indexed-but-no-match vs not-indexed. |
| CE Natural Usage | 2026-02-14 | Enforcement-oriented SERVER_INSTRUCTIONS (trigger phrases, required behaviors). CE nudge in governance reminder. CE cross-ref in Required Actions. CLAUDE.md CE Integration section. Security validation mirrors governance pattern. Stale index warning (>1hr). Realtime mode in MCP config. |
| CE Weight Tuning | 2026-02-14 | semantic_weight default 0.6 → 0.7 (+6.7% MRR, no recall loss). Embedding model eval confirmed bge-small-en-v1.5 outperforms bge-base and all-mpnet. Jina safetensors verified. Governance server weight unchanged (separate benchmarks). |
| CE Desktop Config | 2026-02-14 | Added context-engine to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`). Both governance + CE now available in Desktop and Cowork. Claude Code config (`~/.claude.json`) already had it. See LEARNING-LOG "Claude Desktop and CLI Have Separate MCP Configs." |

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
- **Decision:** Six memory types mapped to files: Working (SESSION-STATE), Semantic (PROJECT-MEMORY), Episodic (LEARNING-LOG), Procedural (methods docs), Prospective (BACKLOG, added 2026-04-15), Reference (Context Engine, added 2026-02-02).
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

### ADR-10: Platform-Native Memory — Hands Off
- **Status:** Accepted (2026-02-07), evolved 2026-04-15 (hands-off)
- **Context:** Claude Code's auto memory (`MEMORY.md`) duplicated facts from SESSION-STATE, PROJECT-MEMORY, and LEARNING-LOG, violating Single Source of Truth. Stale facts in auto memory anchored AI understanding before it read framework files. Phase 1 (2026-02-07): pointer-only approach. Phase 2 (2026-04-15): discovered that CLAUDE.md + AGENTS.md (both auto-loaded) already contain the session protocol, making the MEMORY.md pointer redundant. Additionally, behavioral feedback was routing to Claude Code memory instead of CLAUDE.md because no routing rule existed.
- **Decision:** Don't write to platform-native memory files at all. CLAUDE.md is the bridge between the LLM platform and our framework. Framework memory files (SESSION-STATE, PROJECT-MEMORY, LEARNING-LOG, BACKLOG) are the source of truth. If the LLM has its own memory, ours enhances it. If it doesn't, ours provides full capability. Behavioral instructions go in CLAUDE.md, not platform memory. Formalized in Appendix G.5.
- **Consequences:** (+) framework is fully LLM-agnostic, (+) eliminates dual-system management burden, (+) no stale-anchor risk from unmanaged platform memory, (-) platform memory may capture its own content that goes stale — accepted trade-off since we don't depend on it.

### ADR-12: Context Engine — Comparison with Augment Code and Industry Best Practices
- **Status:** Accepted (2026-02-13), expanded 2026-02-16 (deep Augment Code research)
- **Context:** Our context engine (v1.0.0) was inspired by Augment Code's Context Engine. After shipping all 5 phases (incremental indexing, tree-sitter, file watcher, benchmarks, freshness metadata), we conducted a systematic comparison against Augment Code's published architecture and industry best practices (sources: Augment Code blog, cAST paper EMNLP 2025, Modal embedding benchmarks, Sourcegraph Zoekt, Aider repo map, Continue.dev, Qodo, Milvus).

**Augment Code Architecture (for reference, not our target):**
- Founded 2022 by Igor Ostrovsky (ex-Pure Storage chief architect) + Guy Gur-Ari (ex-Google AI researcher). $252M funding, ~$977M valuation. Team from Google, Meta, NVIDIA, Microsoft.
- **Core thesis:** "Every AI uses the same models. Context is the difference." LLMs are commodity (they use Claude + GPT); the moat is the Context Engine.
- Cloud-hosted, per-developer semantic indexing on Google Cloud (PubSub, BigTable, AI Hypercomputer)
- Custom-trained embedding models (usefulness > similarity) — NOT generic embeddings. Trained to understand that callsites differ from definitions, docs may not resemble code.
- Quantized ANN search: binary quantization with two-phase retrieval (quantized candidates → full-precision rescoring). 8x memory reduction (2GB → 250MB for 100M LOC), sub-200ms latency (was 2+ seconds), 99.9% accuracy parity. Estimated 10-20M vectors for 100M LOC.
- Per-developer branch-aware indices, cross-repo awareness. Branch switches near-instant.
- Security: "Proof of Possession" — IDE must send crypto hash proving file knowledge before retrieval. Self-hosted embeddings (no third-party APIs, citing embedding inversion attacks: arXiv 2305.03010, 2004.00053).
- Context Lineage: commit history indexed via Gemini Flash summarization
- Compression: 4,456 sources → 682 relevant → 2,847 tokens used
- 70.6% SWE-bench accuracy (vs 56% for file-limited competitors)
- VS Code extension rebuilt with Redux-Saga state management, Svelte UI, parallel tool execution. 1.2-2x faster tool-heavy workflows.
- **MCP protocol support:** Context Engine exposed as MCP server (local via Auggie CLI or remote via HTTP). ~40-70 credits per query. Supports 12+ MCP clients including Claude Code, Cursor, Codex, Zed.
- **Pricing (credit-based, Oct 2025):** Indie $20/mo (40K credits), Standard $60/mo (130K credits), Max $200/mo (450K credits). Small task ~293 credits, medium ~860, complex ~4,261.
- **Sources:** augmentcode.com/context-engine, augmentcode.com/blog/a-real-time-index-for-your-codebase-secure-personal-scalable, augmentcode.com/blog/repo-scale-100M-line-codebase-quantized-vector-search, augmentcode.com/blog/rebuilding-state-management, docs.augmentcode.com/context-services/mcp/overview

**Our architecture (local-first, single-user):**
- Local CPU inference, privacy-preserving, no network dependency
- Open-source embeddings (BAAI/bge-small-en-v1.5, 384 dims)
- Hybrid BM25 + semantic with cross-encoder reranking
- Tree-sitter AST chunking for 6 priority languages
- Incremental indexing with content hashing, on-demand or file-watcher modes
- Handles projects up to 10K files / 100K chunks

**Comparison analysis (single-user priorities):**

| Dimension | Our Implementation | Best Practice | Gap | Priority |
|-----------|-------------------|---------------|-----|----------|
| **Chunking** | Tree-sitter AST, per-definition chunks, preamble chunks | Include imports + docstrings WITH each function chunk; include class context for methods (cAST EMNLP 2025, supermemory code-chunk) | Functions lack import context — embedding misses dependency signals (e.g., "this function uses pandas") | **High** |
| **Embedding model** | bge-small-en-v1.5 (general purpose, 384 dims) | Code-specific models: Jina Code Embeddings, CodeXEmbed-400M, or at minimum bge-base (768 dims). Modal benchmarks show CodeBERT/GraphCodeBERT are outdated. | ✓ Evaluated 2026-02-14: bge-small outperforms bge-base (MRR 0.627 vs 0.598) and all-mpnet (0.569) on our corpus. Cross-encoder reranking compensates effectively. | **Closed** |
| **Ranking signals** | Raw relevance scores only | File-type weighting (source > test > generated), recency bias, symbol-type boost, path proximity (Sourcegraph model) | All results treated equally regardless of file type, recency, or structural role | **Medium** |
| **Result deduplication** | None — overlapping chunks from same file can appear | Deduplicate overlapping chunks, keep higher-scored one | Minor issue with current chunk sizes but could matter for large files | **Low** |
| **Token budget** | Fixed max_results count | Budget-aware packing: rank all candidates, greedily fill a token budget, deduplicate (Aider model) | No token-aware result sizing | **Low** (users control via max_results) |
| **Repository map** | Not implemented | Lightweight symbol summary (Aider uses tree-sitter + PageRank for symbol importance) — cheap to produce, high value for LLM orientation | LLMs must search to understand project structure | **Medium** |
| **Incremental indexing** | File-level granularity, content hashing | Chunk-level granularity: re-parse AST, re-embed only changed chunks within a file (Meta Glean model) | Re-embeds ALL chunks from a modified file, even if only one function changed | **Low** (file-level is good enough for single-user) |
| **Debouncing** | File watcher batches via 30s flush interval | 3-5s debounce consensus (avoid embedding on every keystroke) | Our 30s is conservative — acceptable for single-user | **None** |
| **Security** | Model allowlists, symlink protection, path sanitization, rate limiting | Industry standard for local tools | Well covered | **None** |

**Decision:** No immediate changes needed — current implementation is solid for single-user use. Identified three improvement candidates for future consideration:

1. **Import-enriched chunks** (High) — ✓ DONE (CE v1.1.0, `eba8df6`). Prepends import block to each function chunk.
2. **Ranking signals** (Medium) — ✓ DONE (CE v1.1.0, `eba8df6`). File-type weighting in `project_manager.py:37-50`.
3. **Code-specific embedding model** (Medium) — ✓ EVALUATED (2026-02-14). bge-small-en-v1.5 outperforms bge-base (MRR 0.627 vs 0.598) and all-mpnet-base-v2 (0.569) on our corpus. Larger models don't justify 2x dimensions. Jina safetensors verified. No model change needed.

**What we deliberately skip (overkill for single-user):**
- Cloud-hosted inference (Augment's model)
- Cross-repo search
- Per-developer branch-aware indices
- Quantized ANN search (only needed at 100M+ LOC scale)
- Commit history indexing (LLM summarization)
- Repository map / symbol graph (useful but separate feature, not a retrieval improvement)

- **Consequences:** (+) Documented provenance and rationale, (+) clear improvement backlog with priorities, (+) validated that core architecture (hybrid search + tree-sitter + incremental) aligns with industry best practices, (-) embedding model is general-purpose rather than code-specific.

### ADR-13: Governance Enforcement — From Advisory to Structural
- **Status:** Accepted (2026-02-16)
- **Context:** Research confirmed that MCP server instructions are probabilistic, not deterministic. AI models skip governance calls when they don't perceive a governance concern, during long conversations, or when many tools compete for attention. The current advisory approach (CLAUDE.md instructions, MCP server instructions, per-response reminders) works most of the time in short conversations with few tools, but compliance degrades predictably. This project needs structural enforcement — mechanisms that run deterministically regardless of the AI's judgment.

**AI Instruction Compliance — Key Data Points:**
- IFEval benchmark: best models follow simple, single-turn instructions 85-92% of the time (sources: Scale AI Leaderboard, Vellum, LLM Stats)
- Anthropic's own tool selection accuracy: Opus 4 = **49% baseline** (improving to 74% with Tool Search Tool); Opus 4.5 = 79.5% baseline (improving to 88.1%). Source: anthropic.com/engineering/advanced-tool-use
- Berkeley Function Calling Leaderboard (BFCL): Claude Sonnet 4 = 70.29%, GPT-5 = 59.22%. Source: klavis.ai
- MCPMark (realistic multi-tool tasks): GPT-5 = ~52.6% pass@1, Claude Sonnet 4 = **28.1%** pass@1
- Multi-turn conversation degradation: **39% average performance drop** across 15 LLMs, 200K+ conversations. Even top models (Claude 3.7, Gemini 2.5, GPT-4.1) degrade 30-40%. Source: Microsoft Research, arxiv.org/abs/2505.06120
- Context rot: GPT-4.1 accuracy drops from 84% at 8K tokens to 50% at 1M tokens. Claude decays slowest but tends to abstain/skip rather than call incorrectly. Source: Chroma Research (research.trychroma.com/context-rot)
- Tool flooding threshold: degradation after ~40 tools, cliff at ~60 tools. Source: developer reports (arsturn.com, hackteam.io)
- **No published benchmark exists for MCP governance check compliance rates.** This is a confirmed data gap.

**Key failure modes for governance MCP specifically:**
1. Model skips `evaluate_governance()` when it doesn't perceive a governance concern (confident in internal knowledge)
2. Multi-turn degradation causes governance instructions to be "forgotten" over long sessions
3. Tool flooding from multiple MCP servers dilutes governance tool prominence
4. Claude specifically tends to silently abstain rather than call incorrectly — governance checks just don't happen

**Decision:** Move from advisory-only to layered enforcement:
- **Layer 1 (Advisory):** Current CLAUDE.md + MCP server instructions + per-response reminders — KEEP
- **Layer 2 (Structural — Claude-specific):** Claude Code hooks (PreToolUse, UserPromptSubmit) — deterministic, platform-enforced. Three hook types: command (shell scripts), prompt (fast LLM evaluation), agent (subagent with tool access). 14 hook events, regex matcher system for targeting specific tools.
- **Layer 3 (Structural — Model-agnostic):** MCP proxy/gateway that intercepts tool calls before forwarding to downstream servers. Candidates: Latch (latchagent.com), MCPTrust (github.com/mcptrust/mcptrust), FastMCP Middleware. Works with any MCP client.
- **Layer 4 (Audit):** Post-action verification via `verify_governance_compliance()` in CI/pre-commit hooks.

**Enforcement tools evaluated:**
| Tool | Type | Model-Agnostic | Blocks Actions | Effort |
|------|------|----------------|----------------|--------|
| Claude Code hooks | Platform hooks | No (Claude only) | Yes (PreToolUse) | Low |
| Claude Agent SDK hooks | Python SDK | No (Claude only) | Yes | Low-Med |
| Rampart (github.com/peg/rampart) | Agent firewall | Yes ($SHELL wrapping) | Yes (YAML policy) | Low |
| Latch (latchagent.com) | MCP proxy | Yes | Yes (policy-based) | Low-Med |
| MCPTrust (github.com/mcptrust/mcptrust) | MCP proxy | Yes | Yes (lockfile+CEL) | Low-Med |
| FastMCP Middleware | MCP framework | Yes | Yes | Low |
| Portkey AI Gateway | LLM proxy | Yes | Yes (guardrails) | Low |
| NeMo Guardrails (NVIDIA) | Guardrails DSL | Yes | Yes (Colang rules) | Medium |
| Guardrails AI | Validation framework | Yes | No (validates I/O) | Low-Med |
| OpenAI Agents SDK | Platform guardrails | No (OpenAI only) | Yes (tripwires) | Low-Med |

**Also evaluated and rejected:**
- Custom VS Code extension (Solution 1): Very high effort (3-6 months), rebuilds what Cline/Roo Code already do. Custom extension uses API pricing, not Max subscription.
- Fork Roo Code (Solution 2): Medium effort, gives custom modes, but high maintenance burden.
- Obsidian + AI plugin: Wrong ecosystem for governance enforcement, fragments workflow.
- Claude Desktop + MCP (Solution 5): Zero build effort but lacks agentic file editing capabilities.

**IDE plug-in cost caveat:** Max subscription ($100/mo) only covers Anthropic's own products (claude.ai, Claude Code). Custom VS Code extensions or Roo Code forks calling the Anthropic API directly use **API pricing** ($3/$15 per MTok for Sonnet 4.5). For weekend+evening usage, API cost estimated at ~$30-70/mo — potentially cheaper, but with variance risk.

**Philosophy:** The goal is compliance-by-architecture, not compliance-by-instruction. Advisory instructions serve as the first line but will inevitably degrade in long sessions. Structural enforcement (hooks, proxies) provides a deterministic safety net. The system should work with any frontier model, not just Claude.

### ADR-14: Layer 3 Enforcement — stdio Proxy over FastMCP Migration
- **Status:** Accepted (2026-03-28)
- **Context:** Backlog #1B required model-agnostic governance enforcement. Three approaches evaluated: (1) internal `call_tool` checks, (2) FastMCP middleware migration, (3) thin stdio JSON-RPC interceptor proxy.
- **Contrarian finding (critical):** The original plan proposed internal `call_tool` checks on 4 already-gated tools — a scope reduction that dodged the hard problem. The contrarian-reviewer caught this by applying §7.10: "If you started fresh today, would this be your answer?" The answer was no. This led to plan revision.
- **FastMCP middleware finding:** FastMCP v3.0 provides `on_call_tool` middleware hooks, but requires migrating from `mcp.server.Server` to FastMCP's own `FastMCP()` server class — a full rewrite of our 3000-line server.py. Not justified for this scope.
- **Decision:** Thin stdio JSON-RPC interceptor proxy (`enforcement.py`). Zero new dependencies, works with any MCP server over stdio, reusable for Phase 2 cross-MCP enforcement.
- **Key design choices:**
  - Recency window counts tool calls (not transcript lines) — transport-agnostic
  - Env vars mirror hooks for consistent user experience
  - Unknown tools pass through (extensibility-safe)
  - Error uses JSON-RPC `isError: true` result format (not JSON-RPC error code) for better AI client handling
- **Meta-lesson:** Architecture decisions must be reviewed by contrarian-reviewer. Added to §5.1.7 Subagent Review Triggers.

- **Consequences:** (+) Three enforcement vectors (advisory + structural + audit), (+) model-agnostic path via MCP proxy, (+) immediate low-effort option (Claude Code hooks), (-) Claude-specific hooks don't help other models, (-) MCP proxy adds infrastructure complexity.
- **Sources:** anthropic.com/engineering/advanced-tool-use, arxiv.org/abs/2505.06120, research.trychroma.com/context-rot, arxiv.org/abs/2411.07037 (LIFBench), code.claude.com/docs/en/hooks, github.com/peg/rampart, latchagent.com, github.com/mcptrust/mcptrust

### ADR-14: Quantized Vector Search — Premature for Current Scale
- **Status:** Deferred (2026-02-16)
- **Context:** Augment Code uses binary quantized vector search for 100M+ LOC codebases (10-20M vectors). Investigated whether our Context Engine should implement similar optimization.

**Our scale vs. Augment Code:**
| Metric | Context Engine | Augment Code |
|--------|----------------|--------------|
| Vectors | 10K-100K | 10-20 million |
| Scale multiplier | 1x | 100-200x larger |
| Memory (max) | 147 MB (100K × 384 × 4 bytes) | 2 GB → 250 MB after quantization |
| Brute-force latency (100K vectors) | **1-5 ms** | N/A (too slow at their scale) |
| Actual bottleneck | Embedding query (~50-100 ms) | Vector search (2+ seconds pre-optimization) |

**Quantization methods evaluated:**
| Method | Memory Reduction | Speed Improvement | Recall Loss | Complexity |
|--------|-----------------|-------------------|-------------|------------|
| Brute force f32 (current) | 1x | 1x | 0% | None |
| float16 (trivial change) | 2x | ~1.5x | Negligible | 1 line change |
| Scalar int8 | 4x | ~3-4x | 1-3% | Low |
| Binary | 32x | ~10-30x | 5-15% | Medium |
| Product Quantization | 48-192x | ~10-100x | 3-10% | High (training) |
| HNSW + SQ8 | ~0.5x (net save) | 100-1000x | 2-5% | Medium |

**Libraries evaluated:** FAISS (most mature, heavy dep), hnswlib (lightweight HNSW), USearch (single-file, f16/i8 native, 10-100x faster than FAISS claims), Annoy (older), ScaNN (Linux only).

**Decision:** Do not implement now. At 100K vectors, `np.dot` takes 1-5 ms — the embedding step (50-100 ms) is the bottleneck, not search. 147 MB memory is trivial.

**Phased implementation path (when needed):**
1. **Phase 1 (trivial):** Change `dtype=np.float32` to `dtype=np.float16` in indexer. 2x memory, negligible accuracy loss, zero deps.
2. **Phase 2 (moderate):** Add USearch (`pip install usearch`) as optional backend. Lightweight, cross-platform, f16/i8 + HNSW. Sub-ms at 10M vectors.
3. **Phase 3 (heavy):** FAISS with IVF+SQ8 for multi-workspace search at 1M+ vectors.

**Revisit triggers:**
- Context Engine evolves to index multiple projects simultaneously (500K+ vectors)
- Larger embedding models adopted (768+ dimensions)
- Users report perceptible latency on large projects
- ANN crossover point: ~500K-1M vectors for sub-100ms interactive requirement

- **Consequences:** (+) No premature complexity, (+) clear phased path when needed, (+) documented rationale prevents future re-investigation, (-) misses opportunity for storage optimization.
- **Sources:** augmentcode.com/blog/repo-scale-100M-line-codebase-quantized-vector-search, github.com/facebookresearch/faiss/wiki, ann-benchmarks.com, github.com/unum-cloud/USearch, huggingface.co/blog/embedding-quantization

---

## Metrics Registry

Systematic tracking of performance metrics. See also: ARCHITECTURE.md for test coverage.

### Retrieval Quality Thresholds

**Governance Server:**

| Metric | Current | Threshold | Rationale |
|--------|---------|-----------|-----------|
| Method MRR | 0.646 | ≥ 0.60 | Primary method discovery signal |
| Principle MRR | 0.750 | ≥ 0.50 | Primary principle discovery signal |
| Method Recall@10 | 0.833 | ≥ 0.75 | Breadth of relevant results |
| Principle Recall@10 | 0.875 | ≥ 0.85 | Breadth of relevant results |
| Model Load Time | ~80ms (IPC) | ≤ 15s | User experience bound |
| Gov Server Memory | ~85 MB (IPC) | < 300 MB | Phase 2 target (was ~800 MB pre-IPC) |

**Context Engine** (baseline 2026-03-13, saved in `tests/benchmarks/ce_baseline_2026-03-13.json`):

| Metric | Current | Threshold | Rationale |
|--------|---------|-----------|-----------|
| CE MRR | 0.58 | ≥ 0.50 | Primary content discovery signal |
| CE Recall@5 | 0.75 | ≥ 0.70 | Top-5 result coverage |
| CE Recall@10 | 0.95 | ≥ 0.80 | Top-10 result coverage |

Note: CE benchmark v2.0 uses this project's codebase as corpus with 16 queries (expanded from 8 in v1.0). MRR varies naturally as code evolves (~0.62-0.75 range observed). Benchmark file: `tests/benchmarks/context_engine_quality.json`. Tree-sitter was available during benchmark (pytest spawns fresh process with current code). Weight tuned to 0.7 on 2026-02-14 (+6.7% MRR).

### When to Record New Baseline

- Embedding model changes
- Major index changes (new domain, significant rewrites)
- Retrieval algorithm changes
- Tree-sitter language additions or chunking strategy changes
- Before releases

---

## Roadmap

### Structural Governance Enforcement (Priority: HIGH — ADR-13)

**Goal:** Move from advisory-only governance (AI might skip calls) to structural enforcement (deterministic, platform-enforced).

**Phase 1 — Claude Code Hooks (COMPLETE — 2026-02-18):**
- ✓ `PreToolUse` hook for `Bash|Edit|Write` — transcript-based governance verification
- ✓ `UserPromptSubmit` hook — governance reminder injection on every prompt
- ✓ Evaluated hook types: chose command (shell scripts, ~10-50ms latency, deterministic)
- ✓ Configured in `.claude/settings.json` (project-level, committable)
- ✓ Documented as §4.6.3 in title-20-multi-agent-cfr.md
- ✓ Soft enforcement (default) + hard mode via `GOVERNANCE_HARD_MODE=true`
- ✓ Configurable tool name via `GOVERNANCE_TOOL_NAME` env var
- ✓ Debug logging via `GOVERNANCE_HOOK_DEBUG=true`
- ✓ Reviewed by contrarian, code-reviewer, and coherence-auditor

**Phase 1b — Hook Improvements (COMPLETE — implemented as part of hard-mode enforcement 2026-02-28):**
- ✓ Recency heuristic: PreToolUse scans last ~200 transcript lines (GOVERNANCE_RECENCY_WINDOW). Catches task-boundary pivots in long sessions.
- ✓ Suppress UserPromptSubmit after governance established: inject hook is silent when both tools called recently. Saves ~128 tokens/prompt (~11K tokens/50-turn session).

**Phase 2 — Cross-MCP Proxy Enforcement (COMPLETE — 2026-04-07):**
- ✓ `enforcement.py` extended: `--govern-all`, `--config`, `--always-allow` CLI flags
- ✓ Shared state file (`~/.ai-governance/enforcement-state.json`) for cross-process coordination
- ✓ YAML config support for fine-grained tool classification (see `examples/github-governance.yaml`)
- ✓ Security hardening: future timestamp clamping, non-overridable field denylist, fail-closed error handling
- ✓ 59 tests in test_enforcement.py (32 new for Phase 2)
- ✓ §4.6.2 updated with auth vs governance distinction, 2026 gateway table, fixed decision tree

**Phase 3 — CI/Audit Integration (Prerequisite phases 1+2 complete):**
- Pre-commit hook calling `verify_governance_compliance()` to catch bypassed governance
- Governor (github.com/ulsc/governor) for security-auditing AI-generated code
- Governance validation step in CI pipeline

### Quantized Vector Search (Priority: LOW — ADR-14, Deferred)

Not needed at current scale. Phased approach documented in ADR-14. Revisit when CE reaches 500K+ vectors.

### ADR-15: Constitutional Principle Consolidation v3.0.0
- **Status:** Accepted (2026-03-29)
- **Context:** Constitution grew by accretion to 47 principles across 6 series. Constitutional test ("does this govern reasoning across ALL domains?") found 20+ principles were domain-specific, methods masquerading as principles, or redundant overlaps. The constitution claimed "a small set of high-leverage meta-principles" — with 47, this claim was false.

**Decision:** Systematic consolidation: 47→22 principles, 6→5 series.
- 12 merges within the constitution (facets of same concept combined)
- 9 demotions to domain documents (multi-agent: 6, ai-coding: 2)
- 5 demotions to governance methods TITLE 16 (procedural techniques)
- 1 promotion back (Effective & Efficient Communication — incorrectly demoted as style guide)
- MA-Series dissolved (all principles were multi-agent specific)
- Alias infrastructure for backward compatibility (old IDs resolve to new)

**Alternatives rejected:**
1. Just rewrite shorter — doesn't fix redundancy or domain leakage
2. Merge only obvious overlaps — leaves 43 principles, still violates "small set" claim
3. Full restructure into new series — maximum risk, current legal analogy is sound

**Outcome:** 22 principles, 5 series (S:3, C:6, Q:4, O:6, G:3). Retrieval quality stable (MRR 0.688, Recall 0.875). 1026 tests passing. 6 subagent review rounds with 0 critical/high findings.

### ADR-16: Part 9.8 Content Quality Framework + Domain Consolidation
- **Status:** Accepted (2026-03-29)
- **Context:** After constitutional consolidation (ADR-15), the root cause was identified: lack of rigorous authoring criteria, not lack of review process. Applied the same rigor to all 6 domains.

**Decision:** Formalized Part 9.8 as a universal quality gate, then applied it to every domain.
- Part 9.8: 7-question Admission Test (Q7 added in v3.27.0), Duplication Check, Quality Checklist, Concept Loss Prevention, Required Subagent Reviews (§9.8.8)
- KM&PD: 13→10, AI Coding: 14→12, Storytelling: 19→15, UI/UX: 20→20 (skip gate), Multi-Agent: 22→17, Multimodal RAG: 35→32
- Total: 170→128 principles (-25%)

**Key process learnings codified in §9.8.8:**
- All 3 mandatory agents (contrarian, validator, coherence) at BOTH assessment AND post-change phases
- Contrarian alone produces ~40% of findings; 3-agent assessment produces 2.4x findings
- Skip gate: >90% KEEP → document clean assessment and move on
- Concept Loss Prevention: directive-level granularity with tabular artifact

### ADR-17: Constitutional Principle Rename + Scope Expansion (Effective & Efficient Outputs)
- **Status:** Accepted (2026-04-26)
- **Context:** Constitutional principle `meta-quality-effective-efficient-communication` (Art. III §4) encoded the right joint-quality discipline (effectiveness × efficiency, lead-with-the-answer, no padding) but was artificially scoped to communication outputs only. When AI generated code, drafted plans, proposed architectures, or wrote reports, the principle did not bind — observable failures included orphaned helpers, four-file fixes, narrative-heavy reports, bloated summaries. Through dialogue with the user (originator of the proposal), the question evolved from "add a new principle for joint-quality across all outputs" (rejected on 5/7 Admission Test FAILs by contrarian-reviewer) to "rename and rescope the existing principle to remove the artificial communication scope" (passes Admission Test with the principle/method split).

**Decision:** Rename `meta-quality-effective-efficient-communication` → `meta-quality-effective-efficient-outputs`. Generalize scope from communication-only to all AI output forms (communication, code, plans, reports, architectures). Preserve communication-specific operational guidance verbatim as one named section; add parallel form-specific sections that **purely cross-reference** canonical sources (no smuggled new operational language). Add verbatim stop-condition language inside the principle text: *"Discipline applies during creation; once form-appropriate discipline has been applied, the output is done. When discipline gates pass, stop."* Add `Principle.aliases=["meta-quality-effective-efficient-communication"]` for backwards-compatible retrieval (precedent: Graceful Degradation rename). Concurrently add `meta-method-solution-comparison-effectiveness-efficiency-product` (rules-of-procedure §16.7) as the comparison-among-alternatives method, citing Collier (2026) "The Elegance Equation" working paper as Reference Library entry. Add Meta-Principle ↔ Domain crosswalk rows in 4 domains (ai-coding, ui-ux, multi-agent, kmpd); carve out storytelling (narrative density IS the value) and multimodal-rag (existing principles cover the ground).

**Alternatives rejected:**
1. Add as a new constitutional principle parallel to the existing one — rejected per ADR-15 consolidation philosophy and contrarian-reviewer's 5/7 Admission Test FAILs (Q1 Coverage = "concept exists, just artificially scoped"; Q2 Placement = comparison procedure is method-shaped; Q4 Evidence = n=1 working paper without operational evidence in this project; Q5 Enforceability = advisory-only without principle/method split; Q7 Semantic-Label = "Elegance" imports aesthetic baggage)
2. Absorb wholly into Resource Efficiency (Art. II §4) — rejected; the contribution is *evaluative* (joint quality of an output), not *minimization* (don't waste). Different axis.
3. Add as method-only without rename — rejected; methods derive from principles. With the existing principle scoped to communication, a method that bound on all outputs would have no derivation parent.
4. Decline the addition entirely — rejected; the failure modes the user named (orphaned helpers, four-file fix, narrative-heavy reports) are real and not addressed by the current toolkit when output form ≠ communication.

**Outcome:** Principle count stays flat (ADR-15 alignment preserved). Constitutional rule now binds across all output forms with explicit form-specific operational discipline and explicit stop-condition. Elegance Equation lands as a downstream method for the comparison case. Backwards-compatible retrieval preserved via aliases. Major version bump (v5.0.0) signals scope-of-binding change to downstream consumers tracking constitutional version history.

**Process learnings:**
- Contrarian-reviewer initial verdict was REJECT on the original "new principle" framing; subsequent dialogue surfaced the rescope alternative the contrarian (and I) had missed. **Lesson: when contrarian says REJECT but the user disagrees substantively, run the alternative framing through a fresh contrarian** rather than relying on the first verdict — the original framing may not have captured the structurally cleanest move.
- Q7 (Semantic-Label Risk) for the principle title was a separate question from Q7 for the method title. The principle's title borrowing (Drucker effectiveness/efficiency framing) was pre-existing; the method's title was renamed from "Elegance Equation Method" to "Solution Comparison via Effectiveness × Efficiency Product" to satisfy Q7 for new content.
- The pre-ExitPlanMode contrarian flagged 8 required modifications to the plan (version bump from minor to major, R-12 carve-out from claimed-subsumption, crosswalk reduction from 6→4 domains, verbatim stop-condition inside principle text, strip smuggled operational rules from form-specific sections, Q7 disposition for principle title, prose-string updates for the rename, and a worked example demonstrating Q1 Coverage sharpness). All applied before ship.

**Cross-ref:** `~/.claude/plans/this-is-back-and-tidy-crescent.md`; LEARNING-LOG entry "Generalize Existing Principle Before Minting a New One" (2026-04-26); rules-of-procedure §16.7; `reference-library/ai-coding/ref-ai-coding-collier-elegance-equation.md`; constitution v5.0.0 amendment (Art. III §4 rename + rescope); 4 domain title crosswalk additions (title-10/15/20/25); title-40 changelog v2.4.2 (rename note, no crosswalk row).

### Future Considerations

- Prompt Engineering domain (when created, move system prompt best practices from multi-agent)
- ~~Gateway-Based Enforcement (§4.6.2)~~ → implemented as Phase 2 cross-MCP proxy enforcement (2026-04-07)
- Vector DB migration (when scale requires) — see also ADR-14 Phase 3
- ~~Prompt Engineering consolidation~~ → Title 11 in ai-governance-methods (done)
- ~~RAG Optimization consolidation~~ → Title 12 in ai-governance-methods (done)
- Governance-aware PR review (GitHub Action + Claude API + governance principles, ~$0.02-0.03/review with Haiku) — see BACKLOG.md or `git log --grep="backlog #4"`

### Evidence Sources for Future Domain Updates

Reviewed 2026-03-22. These articles validate existing framework patterns. Filed for citation when updating ai-coding or multi-agent domains.

| Source | Date | Validates | Key Insight |
|--------|------|-----------|-------------|
| Lopopolo (OpenAI) "Harness Engineering: Leveraging Codex" | 2026-03 | AGENTS.md-as-map (Appendix K), enforcement-over-documentation (§9.3.10), graduated autonomy (AO-Series), automated hygiene (§6.5) | At scale, "golden principles" encoded mechanically beat documentation. Agent legibility is a first-class design criterion. 1M lines, 0 manually-written. |
| LangChain "Improving Deep Agents with Harness Engineering" | 2026-02 | Self-verification loops (§5.1.2), doom loop detection (§5.13.4), progressive context injection (§7.8), trace-based improvement | PreCompletionChecklistMiddleware = our completion sequence. LoopDetectionMiddleware = our fix decay protocol. "Reasoning sandwich" (xhigh-high-xhigh) for planning/execution/verification. |
| Anthropic "Effective Harnesses for Long-Running Agents" | 2025-11 | Session state persistence (§7.0 memory files), incremental progress (§4.1 atomic tasks), completion sequence (§5.1.6), feature tracking | claude-progress.txt = our SESSION-STATE.md. JSON feature list = structured acceptance criteria. "Test baseline before new work" pattern (implied by our §7.8 but not explicit). |
| Shen & Tamkin (Anthropic) "How AI Impacts Skill Formation" | 2026-01 | Human-AI Collaboration (Skill Preservation subsection) | Exoskeleton effect: AI erodes skills when users delegate fully. Added to ai-coding principles. arXiv:2601.20245. |
| Macnamara et al. "Does AI Accelerate Skill Decay?" | 2024 | Human-AI Collaboration (Skill Preservation subsection) | AI-induced skill decay operates outside performer awareness. PMC/Cognitive Research. |

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
| 15 | MCP caches index at startup | Resolved — auto-reload detects index changes via mtime check on each query |
| 16 | Version bumps need multiple files | `__init__.py`, `pyproject.toml`, `SBOM.md`, `SECURITY.md` must stay in sync |
| 17 | Operational changes need source docs | Skip-list/trigger changes must propagate to governance source documents, not just instruction surfaces |
| 18 | `domain_name[:4]` generates implicit prefixes | Resolved — `DOMAIN_PREFIXES` class constant in extractor.py; `TestDomainConsistency` enforces at CI (2026-03-13) |
| 19 | `huggingface-hub>=1.0` drops `requests` | `sentence-transformers` still imports it. Explicit `requests>=2.28.0` in pyproject.toml. |
| 20 | Float32 score precision | Fused scores can exceed 1.0 by ~1e-7. Clamp with `min(score, 1.0)` before Pydantic validation. |
| 21 | Context engine RLock, not Lock | query_project acquires lock for read phase. RLock needed because get_or_create_index may be called inside lock. |
| 22 | Env vars crash on invalid values | All `AI_CONTEXT_ENGINE_*` env vars wrapped in try/except with fallback defaults. |
| 23 | CI needs context-engine extras | `pip install -e ".[dev,context-engine]"` — tests import `pathspec` from optional group |
| 24 | Storytelling A-Series category collision | Multi-agent A-Series = "Architecture", Storytelling A-Series = "Audience" — both map to category `architecture`. Safe because different domain prefixes (`mult-` vs `stor-`) and storytelling uses colon headers (old format). Watch for new domains with A-Series. |
| 25 | `get_*_by_id` prefix collision | `"multi"` (multi-agent) and `"mult"` (multimodal-rag) shared a common prefix. Fixed two ways: (1) renamed multimodal-rag prefix `mult` → `mrag` in extractor, (2) replaced prefix→domain map with exhaustive search across all domains in retrieval.py. O(n) but n is small (~500 items). |
| 26 | `_load_search_indexes` undoes mismatch guard | `_load_project` discards embeddings on model mismatch, then calls `_load_search_indexes` which reloads them unconditionally. Fixed: skip embedding reload if already discarded. |
| 27 | MCP server caches code in memory | Even with editable pip install, a running MCP server process keeps old code in memory. Source changes (e.g., new tree-sitter parsing) won't take effect until the server process restarts. Restart Claude Code to restart all MCP servers. Re-index after restart. |
| 28 | Hook JSON stdout purity | Hook scripts must output ONLY valid JSON to stdout. Any debug output, shell profile noise, or stray `print()` corrupts the hook response. Use `sys.stdout.write()` (not `print`), redirect all stderr with `2>/dev/null`, and use `#!/usr/bin/env bash` (not zsh) to avoid profile pollution. |
| 29 | UserPromptSubmit ignores matcher | The `matcher` field on UserPromptSubmit hooks is ignored — the hook always fires. This is because UserPromptSubmit runs before tool selection, so there's no tool name to match against. |
| 30 | PreToolUse fires on read-only Bash | The `Bash` matcher catches `git status`, `ls`, `cat`, etc. In soft mode the AI contextualizes the reminder. In hard mode, this blocks read-only operations — hard mode requires a different approach to Bash matching. |
| 31 | PreToolUse uses hookSpecificOutput | PreToolUse hooks use `hookSpecificOutput.permissionDecision` (deny/allow/ask), NOT `decision: "block"`. Other events (PostToolUse, Stop) use top-level `decision: "block"`. Different JSON schemas for different events. |
| 32 | GOVERNANCE_HARD_MODE env var | Controls enforcement strictness. `false` (default) = soft enforcement via additionalContext. `true` = hard enforcement via permissionDecision deny. Also affects fail behavior: soft=fail-open, hard=fail-closed on missing transcript. |
| 33 | category_mapping substring collisions | `_get_category_from_section()` uses `keyword in section_lower`. Longer series (ev-series, sec-series) must appear BEFORE shorter substrings (v-series, c-series) in the dict. Fixed in v2.0.0 expansion. Also: `is_series_header` list uses `any()` so order doesn't matter there (True is correct for either match), but `category_mapping` is order-dependent. |
| 34 | skip_keywords too broad | "operational" in skip_keywords blocked "O2: Operational Observability". Removed — principle_indicators check (`**Definition**` etc.) already filters non-principles. Be specific with skip keywords. |
| 35 | ag-series ordering (defensive) | `"a-series" in "ag-series"` is actually False (no real substring collision). Ordering ag-series before a-series in `category_mapping` is defensive, not required. The real collisions are ev/v-series and sec/c-series (Gotcha #33). Test: `test_ag_series_not_architecture`. |
| 36 | Version validator scope | `validate_version_consistency()` only checks `content[:2000]` for `Version:? X.Y.Z` pattern. Title format (`v2.1.0`) and footer (`*Version 2.1.0*` at EOF) are NOT caught. Titles/footers must be updated manually when content version changes — the validator won't flag staleness. |
| 37 | F-Series / R-Series category fix | F-Series was unmapped (defaulted to `"general"`) and R-Series mapped to `"reliability"` for all domains. Fixed: added `"f-series": "fallback"` and `"reference": "reference"` (before `"r-series"`) to `category_mapping`. R-Series now correctly maps to `"reference"` for multimodal-RAG (header `R-Series: Reference`) and `"reliability"` for multi-agent (header `Coordination Principles (R-Series)` — no "reference" substring). |

### Resolved Gotchas

| # | Issue | Resolution |
|---|-------|------------|
| 14 | Method keywords title-only | ✓ Fixed — MethodMetadata + BGE model upgrade (2026-01-17) |

---

## References

- **Architecture:** ARCHITECTURE.md — system design, component responsibilities, file maps
- **Current State:** SESSION-STATE.md — working memory, next actions
- **Backlog:** BACKLOG.md — discussion items and deferred work
- **Lessons:** LEARNING-LOG.md — episodic memory, graduated patterns
