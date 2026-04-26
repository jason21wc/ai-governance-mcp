# 05 — Remediation Plan

> # ⚠ ANALYSIS ARTIFACT — DO NOT APPLY WITHOUT SEPARATE REVIEW SESSION
>
> This document proposes remediation for the 31 findings in this review. Each item should be separately governance-evaluated, contrarian-reviewed, and user-approved before any authoring changes. The plan is a map of options and trade-offs, not a commit list.

**Ranking method:** per §III of `04-intent-engineering-synthesis.md`, ordered by leverage-then-severity. Each item: finding-ids addressed, effort (Low/Medium/High/Very High), change-risk (Low/Medium/High), dependency chain, rationale.

---

## Tier 1 — Critical-severity / Highest-leverage (recommend first)

### R-01 — Build outcome-benchmark harness for value proposition claim

- **Addresses:** F-P2-01 (Critical), F-C-02
- **Effort:** High
- **Change-risk:** Medium (could reveal framework underperforms on measured tasks)
- **Dependencies:** None (can start immediately)
- **What:** Design a stable task set, run two harnesses (framework-guided AI vs. same model without framework context), compare on pre-registered outcome metrics (task completion correctness, safety-violation rate, self-correction rate). Report effect size + confidence interval per cohort.
- **Why first:** every other finding's severity is calibrated against whether the framework produces demonstrable improvement. Without this data, the Declaration's claim (`constitution.md:38`) is unverifiable and contradicts the framework's own rejection of unfalsifiable claims (per PROJECT-MEMORY:85 "rejected 'coherent alternative' escape clause"). Skeleton exists at `staging/benchmark_ab_test.py`; wire it up.
- **Escape hatch (lower-cost alternative):** soften the claim to "mechanism-quality improvement, not outcome-quality" and replace Declaration line 38 with "consistent application of standards" rather than "consistent, reliable results."

---

## Tier 2 — High-severity structural fixes

### R-02 — Amend 7-layer declared hierarchy to include Enforcement Architecture layer

- **Addresses:** F-P1-02 (High), partial F-C-06, partial F-P2-08
- **Effort:** Medium
- **Change-risk:** Medium
- **Dependencies:** blocks nothing; useful after R-01 (outcome data may inform naming)
- **What:** Add a layer (or cross-reference document) naming hooks, CI, subagents, scaffold templates, pre-push gates as "Structural Enforcement" alongside the existing layers. Update `constitution.md:82-92`, `README.md:42`, `rules-of-procedure.md` to point at it.
- **Why:** the declared hierarchy is the canonical answer to "what binds agents here?"; omission of the actual binding layer makes "how does enforcement happen?" unanswerable from hierarchy text alone.

### R-03 — Merge Risk Mitigation by Design into Non-Maleficence

- **Addresses:** F-P2-09 (High)
- **Effort:** Medium
- **Change-risk:** Medium (changes constitutional count 24→23 + G-Series count 5→4; v5.x bump)
- **Dependencies:** None
- **What:** Apply coherence-auditor recommendation: fold Risk Mitigation by Design into Non-Maleficence's Compliance-by-Default section, or demote to Methods. Preserve content coverage (verify per LEARNING-LOG "Demotion Decisions Require Constitutional Coverage Verification" 2026-03-29).
- **Why:** shared failure-mode content and near-verbatim bullets at `constitution.md:777` and `972`. Merge signal per LEARNING-LOG graduated pattern.

---

## Tier 3 — Medium-severity fixes (recommend batched)

### R-04 — Rename "Case Law" → "Reference Library (Secondary Authority)" in constitution hierarchy

- **Addresses:** F-P1-01 (Medium)
- **Effort:** Low (text edit + alias-cleanup)
- **Change-risk:** Low (cosmetic; no behavioral change)
- **Dependencies:** None
- **What:** `constitution.md:92` rename; reconcile lines 101, 112 descriptions; update `README.md:42` to drop "Case Law" label; adjust `rules-of-procedure.md` if it aliases.
- **Why:** label creates expectation of binding precedent that the framework explicitly disclaims (lines 101, 112). Fixing the label aligns reader expectation with actual semantics.

### R-05 — Add Admission Test Q7: Semantic-Label Risk

- **Addresses:** F-C-01 (Medium), preventive against future F-P1-01-class errors
- **Effort:** Low
- **Change-risk:** Low
- **Dependencies:** R-04 (do the existing rename first; then add the rule to prevent recurrence)
- **What:** Add question to `rules-of-procedure.md` §9.8 Admission Test: "Does the proposed name import US-Constitutional semantics that the framework does not implement? If yes, rename, add an explicit disclaimer, or coin a new term."
- **Why:** LEARNING-LOG has two entries on metaphor-hazard (2026-02-28, 2026-04-12); both are reactive. A preventive test question converts repeated reactive catches into a structural gate.

### R-06 — Update `scaffold_project` to match CFR §1.5.2 Standard Kit (add ARCHITECTURE, SPECIFICATION, BACKLOG)

- **Addresses:** F-P1-08 (Medium, upgraded in Step 10)
- **Effort:** Medium (templates + tests + version bump)
- **Change-risk:** Low (adopter-facing only)
- **Dependencies:** None
- **What:** Extend `SCAFFOLD_STANDARD_EXTRAS["code"]` in `src/ai_governance_mcp/server.py:861` to include `ARCHITECTURE.md`, `SPECIFICATION.md`, `BACKLOG.md`. Write templates matching the framework's own conventions. Update tests.
- **Why:** `BACKLOG.md:614-617` self-declares this as a pre-existing CFR-violation. Fix resolves framework self-contradiction.

### R-07 — Fill Relations purpose gap at principle level

- **Addresses:** F-P2-13 (Medium)
- **Effort:** Medium
- **Change-risk:** Medium (new or promoted principle)
- **Dependencies:** None blocking
- **What:** Option A: promote existing Methods Part 9.7.6 (Full Faith and Credit) to G-Series principle; Option B: draft a new Relations-purpose principle covering cross-domain coherence. Run full Admission Test.
- **Why:** Preamble names Relations as one of 5 governance purposes (`constitution.md:45`); current principle coverage is 2 principles, one of which (Structural Foundations) is architecture-layer not relations-layer. Preamble-as-tiebreaker function weakens for Relations-heavy edge cases.

### R-08 — Establish per-document CHANGELOG convention

- **Addresses:** F-P1-06 (Medium), partial F-P2-06, partial F-P2-14, partial F-P2-17
- **Effort:** High (backfill 10+ documents; author rule requiring forward-linking)
- **Change-risk:** Low (additive)
- **Dependencies:** R-01 not blocking but desirable — outcome data adds amendment-gravity signal
- **What:** Add one of: (a) per-document `Historical Amendments` section matching constitution.md pattern; (b) root `CHANGELOG.md` with per-document subsections. Backfill rules-of-procedure + 5 domain principles + 5 domain CFR + tiers.json + domains.json. Forward-going: every amendment entry cites the rules-of-procedure audit_id that authorized it.
- **Why:** amendment history is the longitudinal audit trail. Framework has it for constitution only; 10+ documents have no history. For a framework that ships to adopters, "how did we get here?" should be answerable without git archaeology.

### R-09 — Add per-method `enabling_authority` frontmatter field; populate for CFR methods

- **Addresses:** F-P1-04 (Medium)
- **Effort:** High (200+ methods; validation)
- **Change-risk:** Medium (surfaces orphan methods)
- **Dependencies:** None blocking
- **What:** Extend CFR frontmatter schema with `enabling_authority: meta-core-xxx` (or array). Populate per-method. Add a pre-commit check: CFR methods must cite at least one active principle.
- **Why:** US CFR's most load-bearing property is that every regulation traces to a statute. Without that trace, regulations can drift. Framework's CFR methods mostly lack this trace today (F-P1-04 evidence).
- **STATUS (2026-04-19, session-118):** **DEFERRED — partial coverage retained; documentary-only.** Phase 4b planning (`~/.claude/plans/create-a-plan-following-cached-canyon.md` v3) ran pre-edit 3-agent battery; contrarian REJECTED execution, validator surfaced Q7 Semantic-Label Risk FAIL. Ground Truth reveals `src/ai_governance_mcp/extractor.py:1686-1699` parses `Applies To` only — zero `Implements:` regex; field is purely documentary. F-P1-04's severity was sized on presumed programmatic consumer that does not exist. Re-severity: MEDIUM-at-most (partial-coverage cosmetic ambiguity, not load-bearing traceability). Re-open tracked at BACKLOG #106 with two prerequisites: (a) a consumer emerges (query surface or compliance audit that loads the field); (b) Q7 remediation ships first (rename `**Implements:**` → `**Traces To:**` OR documentary disclaimer). Phase 4a closed the non-backfill F-P1-04-adjacent findings (F-P1-06, F-P2-06, F-P2-14, F-P2-17) via constitution v5.0.3/v5.0.4, rules-of-procedure v3.27.2, ai-instructions v2.7.

### R-10 — Correct document-body Article ordering to match Framework Overview's announced sequence

- **Addresses:** F-P2-15 (Medium)
- **Effort:** Low (section reorder in constitution.md)
- **Change-risk:** Very Low (cosmetic; no principle ID changes)
- **Dependencies:** None
- **What:** Re-order constitution.md so Article II O-Series appears before Article III Q-Series, matching Framework Overview (`constitution.md:131-144`). Verify no inbound references use line numbers.
- **Why:** predictable navigation. Article IV comes after Article III which comes after Article II which comes after Article I is the universal expectation.

---

## Tier 4 — Low-severity cleanups (recommend at cadence)

### R-11 — Normalize "Constitutional Basis" vs "Constitutional Derivation" terminology

- **Addresses:** F-P2-05 (Low)
- **Effort:** Low (one file: title-40-multimodal-rag.md, 32 replacements)
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Global replace in `title-40-multimodal-rag.md`. Remove alias in rules-of-procedure §3.5.1 once convergence is achieved.

### R-12 — Correct historical amendment records

- **Addresses:** F-P2-14 (Low), F-P2-17 (Low)
- **Effort:** Low
- **Change-risk:** Very Low
- **Dependencies:** None
- **What:** Add correction-entry to v2.8.0 noting "Rich but Not Verbose" demotion was insufficient and required Effective & Efficient Communication promotion. Add entry narrating MA-Series dissolution in a v4.x entry.
- **Status (2026-04-26):** R-12 is **NOT addressed** by the v5.0.0 rename of `meta-quality-effective-efficient-communication` → `meta-quality-effective-efficient-outputs`. The two are orthogonal: R-12 concerns historical-record correction (v2.8.0 amendment narrative + MA-Series dissolution narrative); the v5.0.0 rename is current scope expansion. R-12 remains open as a separate item. Per the contrarian-reviewer pre-ExitPlanMode pressure-test on `~/.claude/plans/this-is-back-and-tidy-crescent.md` (2026-04-26), claiming subsumption was incorrect; carved out explicitly here to prevent false-closure of R-12 in the tracker.

### R-13 — Add domain-applicability metadata to subagents; filter `install_agent` by project domain

- **Addresses:** F-C-04 (Low)
- **Effort:** Medium
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Add `applicable_domains` field to each subagent's frontmatter. Update `install_agent` MCP tool to warn when installing a subagent outside its domain.

### R-14 — Resolve "harness" terminology question

- **Addresses:** F-P2-08 (Low)
- **Effort:** Low
- **Change-risk:** Low
- **Dependencies:** Author-level literature read on Intent Engineering 4-step formulation
- **What:** Either (a) incorporate "harness" into Declaration's 3-step progression (constitution.md:26-36) making it 4-step; (b) author a rationale-note explaining why framework uses 3-step and what "harness" would add if incorporated.

### R-15 — Remove orphan "Multi-agent collaboration principles reside in the Multi-Agent Domain Principles document" sentence

- **Addresses:** F-P2-16 (Low)
- **Effort:** Very Low (one line)
- **Change-risk:** None
- **Dependencies:** None
- **What:** Delete or rewrite `constitution.md:146` trailing sentence. If retention desired, expand to clarify cross-domain principle placement generally.

### R-16 — Evaluate Goal-First Dependency Mapping for Methods demotion

- **Addresses:** F-P2-11 (Medium — placed here for dependency reasons)
- **Effort:** Medium (Admission Test re-application + potential migration)
- **Change-risk:** Medium (changes O-Series count)
- **Dependencies:** R-03 (if Risk Mitigation demoted first, set precedent; otherwise Goal-First becomes first demotion)
- **What:** Re-apply Admission Test Q2 (Placement: "not too narrow, should be an appendix") to Goal-First Dependency Mapping. If it reads method-level under current criteria, demote to Methods under Structural Foundations. Verify coverage.

### R-17 — Resolve Discovery Before Commitment ↔ Systemic Thinking boundary

- **Addresses:** F-P2-10 (Medium — placed here because cosmetic)
- **Effort:** Medium (edit both principles)
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Edit `constitution.md:298-345` (DBC) and `349-391` (ST) to sharpen the reframe-mechanics boundary. Remove duplicate framing. Add an explicit "DBC is about *when*, ST is about *how*" cross-reference.

### R-18 — Add BACKLOG #41 activation (auto-staging for reference library)

- **Addresses:** Partial F-P1-07
- **Effort:** Medium
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Activate the dormant `reference-library/staging/` infrastructure. Wire `capture_reference` MCP tool to propose seedling entries to staging.
- **Why:** `BACKLOG.md:350-356` explicitly names the infrastructure as existing-but-dormant. Activation unblocks organic library growth.

### R-19 — Document Preamble's self-referential granting authority or add consent clause

- **Addresses:** F-P2-02 (Low)
- **Effort:** Low
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Add paragraph to `constitution.md:56-62` stating: "By adopting this framework (installing the MCP server, scaffolding memory files, or citing its principles), the adopter grants operative authority to this framework over AI behavior in the adopter's scope."
- **Why:** closes the authority-grant gap for third-party adopters.

### R-20 — Add structural FM-code convention to meta-principles (match domain discipline)

- **Addresses:** F-P2-03 (Low)
- **Effort:** Medium
- **Change-risk:** Low
- **Dependencies:** None
- **What:** Retrofit each meta-principle's "Common Pitfalls or Failure Modes" section with coded FMs (e.g., `C-F1 Context Drift Across Sessions`, `Q-F1 Silent Failure`). Enables automated overlap detection at meta level.

---

## Tier 5 — Deferred / Policy-level decisions

### R-21 — Decide whether to introduce stare-decisis-binding artifact

- **Addresses:** F-P1-05 (High)
- **Effort:** Very High (philosophy + infrastructure)
- **Change-risk:** High (reverses `constitution.md:101, 112` deliberate design)
- **Dependencies:** Requires author-level governance decision, not engineering
- **What:** Two paths:
  - **Path A:** Admit binding precedent. Design stare-decisis-style mechanism: accreted reference-library entries become binding after N retrievals / M sessions / years. Infrastructure: promotion rules, conflict-resolution with principles.
  - **Path B:** Explicitly document "the framework deliberately excludes binding precedent" as a design choice. Rename "Case Law" to remove implication. (This is R-04 + documentation of the choice.)
- **Why:** framework's deepest structural gap vs US-Constitution §1. Either admit precedent-binding or own the non-admission explicitly. Current state is admitted-in-label + stripped-in-operation, which is internally contradictory.

### R-22 — Populate reference-library for 5 remaining domains

- **Addresses:** F-P1-07 (Medium)
- **Effort:** Very High (content creation; requires real patterns)
- **Change-risk:** Low (additive)
- **Dependencies:** Real-world usage generating patterns; cannot synthesize from nothing
- **What:** Populate `reference-library/{multi-agent,kmpd,storytelling,multimodal-rag,ui-ux}/` with real patterns as they emerge. Add `_criteria.yaml` per domain.
- **Why:** secondary-authority layer functional for only 1 of 6 domains. Can't be rushed; requires actual use generating patterns.

---

## §III — Finding-ID coverage matrix

**Cohort 5 milestone (2026-04-20):** 31 actionable findings triaged + actioned-or-documented-with-rationale. The matrix below has **32 rows** because F-P1-09 is listed for completeness as a synthesis/definitional row (not a fix-required finding; marked N/A). Final status column reflects post-Cohort-5 disposition.

### Closure Typology Breakdown (added v5.0.7 per cross-cohort meta-review)

The "28 closed" headline conflates structurally-different closure types. Honest breakdown:

| Closure Type | Count | Description | Examples |
|---|---|---|---|
| **Structural change** | ~12 | Principle added/removed/renamed, schema change, code change, test added | F-P1-05 (Case Law rename), F-P2-09 (Risk Mit/Non-Mal dedup), F-P1-08 (scaffold expand), F-P2-15 (Article reorder), F-C-03 (parity test), F-C-04 (applicable_domains schema), F-C-05 (governance_level removal), F-C-01 (Q7 added) |
| **Editorial (cross-reference / disposition record)** | ~14 | Prose clarification, cross-reference addition, Q7 PASS record documenting existing behavior, no schema/behavior change | F-P2-10/-12 (boundary cross-refs), F-P2-11 (Q2 KEEP rationale), F-P2-16 (trailing-clause rewrite), F-P2-02 (consent clause), F-P2-04 (Q7 PASS), F-P2-08 (harness rationale), F-P1-03 (architectural note), F-P2-14/-17 (amendment-record backfill), F-P1-06 (changelog formalization), F-P2-06 (audit_id rule), F-P2-13 (Preamble purpose-surface LEARNING-LOG), F-P1-02 (Structural Enforcement subsection), F-P2-05 (terminology sweep) |
| **Accepted residual** | 1 | Finding acknowledged but not operationally closed; re-open trigger documented | F-P2-03 (FM-code retrofit, Q7 FAIL) |
| **Deferred with trigger** | 3 | Finding scoped to future work with concrete re-open prerequisites | F-P1-04 (BACKLOG #106), F-P1-07 (BACKLOG #41/#43/#44/#46), F-P2-07 (BACKLOG #58/#59/#60) |
| **N/A (synthesis row)** | 1 | Not a fix-required finding | F-P1-09 |
| **Plus: 2 additional deferrals filed during Cohort 5** | — | F-C-06 → BACKLOG #107; F-C-04 Phase-2 → BACKLOG #108 | — |

**Per contrarian meta-review (agent `afe0ecba1e867d95d`):** Editorial closures are real but different in kind from structural ones. Depth-reading 14 editorial closures shows the framework got more *legible* (clearer documentation, better cross-references, honest Q7 records) without necessarily getting more *capable*. Structural closures (12) are where capability changed. The distinction matters for assessing whether the review's "100% remediated"-style framings are earned.

**Recurring audit:** BACKLOG #109 tracks deferred-with-trigger items on a ~30-day cadence to prevent passive-trigger calcification.

| Finding | Remediation item(s) | Status | Final disposition |
|---|---|---|---|
| F-P1-01 | R-04 | Low-effort; recommended first-batch | **CLOSED** — Cohort 2 (Case Law → Secondary Authority rename) |
| F-P1-02 | R-02 | Medium structural | **CLOSED** — Cohort 2 (Structural Enforcement subsection added) |
| F-P1-03 | R-05 indirect (preventive); partial documentation in R-02 | Ambiguity noted; preventive fix via R-05 | **CLOSED** — Cohort 5 Session 5-2 (architectural note at §9.7.1 documenting framework's single Rules-of-Procedure layer vs. US-Constitutional distribution) |
| F-P1-04 | R-09 | High effort; high traceability value | **DEFERRED** — Cohort 4 Phase 4b tracked at BACKLOG #106 (re-open on consumer demand + Q7 remediation). Re-severity MEDIUM-at-most (extractor doesn't parse `Implements:`) |
| F-P1-05 | R-21 | Policy decision required | **CLOSED** — Cohort 2 (Case Law rename to Secondary Authority + Q7 formalized Cohort 3) |
| F-P1-06 | R-08 | High effort longitudinal infrastructure | **CLOSED** — Cohort 4 Phase 4a (ai-instructions.md Changelog; §2.1.1 version-history-required rule) |
| F-P1-07 | R-18 + R-22 | Activate infrastructure + organic fill | **DEFERRED** — tracked at BACKLOG #41/#43/#44/#46 (auto-staging + progressive disclosure + auto-maturity + stack metadata). Reference library infrastructure is scaffolded but dormant; re-open on activation decision |
| F-P1-08 | R-06 | Medium effort; self-contradiction closure | **CLOSED** — Cohort 3 (scaffold_project expanded: 3 new templates + BACKLOG.md + CLAUDE.md overlay) |
| F-P1-09 | (definitional) | No-op | **N/A** — synthesis finding |
| F-P2-01 | R-01 | Critical; #1 priority | **CLOSED** — Cohort 1 (README rewrite + Declaration/Preamble as purpose surfaces) |
| F-P2-02 | R-19 | Low effort | **CLOSED** — Cohort 5 Session 5-2 (Adoption and Authority subsection in Framework Structure; consent via adopter activation, not Preamble self-authorization) |
| F-P2-03 | R-20 | Medium effort | **ACCEPTED RESIDUAL** — Cohort 5 Session 5-2 (Q7 FAIL: FM-code retrofit on meta-principles would imply machine enforcement that doesn't exist; extractor doesn't parse codes. Re-open on consumer demand + parser implementation together) |
| F-P2-04 | R-05 (preventive) | Preventive | **CLOSED via Q7 PASS** — Cohort 5 Session 5-2 (Q7 (a)(b)(c) record in Bill of Rights intro; framework has Absolute Veto matching outside pattern) |
| F-P2-05 | R-11 | Low effort | **CLOSED** — Cohort 3 (32 "Constitutional Derivation" → "Constitutional Basis" normalization in title-40) |
| F-P2-06 | R-08 partial | Longitudinal infrastructure | **CLOSED** — Cohort 4 Phase 4a (audit_id citation rule formalized in §2.1.1 Notes) |
| F-P2-07 | (deferred — no specific R item) | Low priority | **DEFERRED** — tracked at BACKLOG #58/#59/#60 (UBDA adopter-drift work). No cross-session drift subagent built; re-open if measurement shows drift persists |
| F-P2-08 | R-14 | Low effort definitional | **CLOSED** — Cohort 5 Session 5-2 (AI-Interaction Model note: 3-step Prompt→Context→Intent is canonical; 4-step "harness" proposal considered and not adopted because "harness" is operationally indistinct from Context Engineering) |
| F-P2-09 | R-03 | Medium structural | **CLOSED** — Cohort 2 (Risk Mitigation ↔ Non-Maleficence Path B de-duplicated; principle count unchanged) |
| F-P2-10 | R-17 | Medium effort boundary | **CLOSED** — Cohort 5 Session 5-1 (DBC ↔ Systemic Thinking boundary sharpened; parallel cross-references articulating "DBC = when+what, ST = how") |
| F-P2-11 | R-16 | Medium structural | **CLOSED (KEEP with Q2 rationale)** — Cohort 5 Session 5-1 (GFDM retained in O-Series; Q2 BORDERLINE → KEEP per §7.8; inline rationale + full Q2 record in v5.0.5 Historical Amendments) |
| F-P2-12 | (included in R-17 style boundary work) | Bundle | **CLOSED** — Cohort 5 Session 5-1 (VR&T ↔ EOI "surface assumptions" cross-references added clarifying output-side vs input-side) |
| F-P2-13 | R-07 | Medium structural | **CLOSED** — Cohort 3 Path B (Preamble purposes recognized as interpretive tiebreakers, not principle-count targets; LEARNING-LOG entry) |
| F-P2-14 | R-12 | Low effort record-correction | **CLOSED** — Cohort 4 Phase 4a (v5.0.3 amendment entry: Effective & Efficient Communication from commit 8dd6d6e / PR #21) |
| F-P2-15 | R-10 | Low effort reorder | **CLOSED** — Cohort 5 Session 5-1 (Article II ↔ III body swap; retrieval.py _CONSTITUTION_HIERARCHY updated; tests updated; fixture preserved as intentional regression guard) |
| F-P2-16 | R-15 | Very low effort | **CLOSED** — Cohort 5 Session 5-1 (trailing orphan Multi-Agent clause generalized to reference all 6 domain principle docs with pointer to Framework Structure table) |
| F-P2-17 | R-12 | Low effort record-correction | **CLOSED** — Cohort 4 Phase 4a (v5.0.3 amendment entry: MA-Series formal dissolution, retroactive to v3.0.0) |
| F-C-01 | R-05 | Preventive | **CLOSED** — Cohort 3 (Q7 Semantic-Label Risk added to Admission Test, rules-of-procedure v3.27.0) |
| F-C-02 | R-01 | Same as F-P2-01 | **CLOSED** — bundled with F-P2-01 (Cohort 1) |
| F-C-03 | R-06 partial + (add parity-test) | Adopter-parity | **CLOSED** — Cohort 5 Session 5-2 (new `tests/test_scaffold_parity.py` with 4 tests: bidirectional assertion, runtime-parse of CFR §1.5.2 Standard Kit; passes) |
| F-C-04 | R-13 | Medium effort | **CLOSED (Phase-1)** — Cohort 5 Session 5-2 (`applicable_domains` frontmatter on all 10 agents; `install_agent` WARN+allow filter with named escalation trigger `strict_domain_check`; documented as deliberate Phase-1) |
| F-C-05 | (deferred — no specific R item) | Infrastructure cleanup | **CLOSED** — Cohort 5 Session 5-2 (`governance_level` frontmatter removed from rules-of-procedure.md; grep confirmed zero code consumers) |
| F-C-06 | R-02 partial | Hierarchy amendment | **DEFERRED** — Cohort 5 Session 5-2 (Situation Index covers *procedures*, not Tool/Model Appendices A-L; residual gap tracked at BACKLOG #107 with re-open criteria) |

## §IV — Recommended sequencing

**Sprint 1 (highest leverage):** R-01 (build benchmark harness — wire up `staging/benchmark_ab_test.py`).
**Sprint 2 (low-effort high-value cleanup):** R-04, R-10, R-11, R-12, R-15 (cosmetic + record fixes). Batchable.
**Sprint 3 (structural fixes):** R-02, R-03, R-05, R-06, R-07. These interact — do them as one coordinated minor-version bump.
**Sprint 4 (longitudinal infrastructure):** R-08, R-09. High effort but essential for framework longevity. Can be incremental.
**Sprint 5 (policy decision):** R-21. Requires author-level decision, not engineering. Result of the decision sets trajectory.
**Background / organic:** R-18, R-22. Pace matches real-use pattern generation.
**Low priority — do when touching adjacent code:** R-13, R-14, R-16, R-17, R-19, R-20.

---

## §V — Change-risk assessment and guardrails

High-change-risk items (R-21 stare-decisis decision; R-01 outcome-benchmark that could show framework underperforms) should go through full three-agent subagent review battery (contrarian + validator + coherence-auditor) before authoring. LEARNING-LOG 2026-03-29 "Three-Agent Assessment Battery Is Non-Negotiable" graduated this as practice.

Medium-change-risk items (R-02, R-03, R-06, R-07, R-09, R-16) should have at minimum contrarian review.

Low-change-risk items may be processed with standard governance evaluation + code-review.

**One guardrail:** R-01 outcome benchmark design should be pre-registered (metrics + task set + analysis plan) BEFORE running the first pass. Without pre-registration, the temptation to cherry-pick metrics that favor the framework is high. Per F-P2-01 evidence — if the benchmark is designed ad hoc, it inherits the same unfalsifiability problem it was meant to fix.

