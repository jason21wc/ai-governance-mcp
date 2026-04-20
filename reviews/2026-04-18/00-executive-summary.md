# 00 — Executive Summary

**Review:** ai-governance-mcp Framework Self-Review
**Date:** 2026-04-18
**Reviewer:** Claude Opus 4.7 (1M context), max effort
**Spec:** 12-step execution plan (user-provided, in-conversation)
**Output files:** 8 (this file + 01…06 + 99)

---

## One-sentence synthesis

The framework is maturely built for individual-moment correctness but under-built for cross-time and cross-adopter scaling — and the most acute shortfall is that its core value claim (framework-guided AI produces better outcomes than unguided AI) is asserted in the Declaration but not falsifiable by any test.

---

## Top 3 root causes

### RC-1 (Critical) — Value proposition is unfalsifiable

The Declaration claims "consistent, reliable results that actually deliver on the potential" (`constitution.md:38`) and the README reiterates it. No test in `tests/` compares framework-guided AI outputs against unguided AI outputs. Existing benchmarks (`tests/benchmarks/baseline_*.json`) measure retrieval MRR — the mechanism, not the outcome. A skeleton A/B test exists at `staging/benchmark_ab_test.py` but is unwired.

This is the single highest-leverage finding. Every other improvement's severity is calibrated against whether the framework actually improves outcomes. Also internally inconsistent: the framework has explicitly rejected "unfalsifiable coherent alternative" escape clauses in session-111 (`PROJECT-MEMORY.md:85`) but has not applied the same discipline to its own Declaration.

**Findings:** F-P2-01, F-C-02
**Fix class:** R-01 (build outcome benchmark), alternatively R-01-B (soften the claim)

### RC-2 (High, structural) — Declared 7-layer hierarchy omits the mechanisms that actually bind

The canonical governance hierarchy — Bill of Rights (S-Series) → Constitution → Federal Statutes → Rules of Procedure → Federal Regulations → Agency SOPs → Case Law (`constitution.md:82-92`, `README.md:42`) — names principles/methods/regulations/case-law layers. It does NOT name hooks, CI, subagents, scaffold templates, or pre-push gates. Those are the layers that do the actual binding (empirically: advisory compliance ~13%, hard-mode ~90%+ per `PROJECT-MEMORY.md:54`).

The hierarchy inherited US-Constitutional shape, which has no runtime-hookable equivalent. When the framework added novel enforcement, the hierarchy was not amended. An adopter reading the canonical description cannot locate where rules become binding.

**Findings:** F-P1-02 (High), partial F-C-06, partial F-P2-08
**Fix class:** R-02 (amend hierarchy to include Enforcement Architecture layer)

### RC-3 (High, structural) — Longitudinal infrastructure is under-built

The framework manages state-of-the-moment well (principles, methods, retrieval, hooks). It manages over-time evolution weakly:
- No binding stare-decisis precedent (F-P1-05 — deepest gap vs §1; reference-library explicitly stripped of override at `constitution.md:101, 112`)
- No per-document CHANGELOG — only constitution has embedded amendment history (F-P1-06)
- CFR methods lack per-method enabling-authority citation (F-P1-04) — breaks the US-CFR traceability property
- Amendment entries don't link to rules-of-procedure audit IDs (F-P2-06)
- Historical amendment records have accuracy gaps (F-P2-14, F-P2-17)

Cross-sectional (now-view) quality is strong; longitudinal (over-time view) quality is thin.

**Findings:** F-P1-04, F-P1-05, F-P1-06, F-P2-06, F-P2-14, F-P2-17
**Fix class:** R-08 (per-document CHANGELOG convention), R-09 (per-method enabling_authority field), R-21 (policy decision on binding precedent)

---

## Finding counts

| Severity | Count |
|---|---|
| **Critical** | 1 |
| **High** | 3 |
| **Medium** | 11 |
| **Low** | 16 |
| **Total** | **31** |

## Threatened-property distribution (all findings)

| Rank | Property | Count |
|---|---|---|
| 1 | predictable | 12 |
| 2 | effective | 11 |
| 3 | dependable | 9 |
| 4 | repeatable | 6 |
| 5 | reliable | 5 |
| 6 | efficient | 3 |

**Root-cause signal:** `predictable` and `effective` are tied within 1 count — the framework's highest-leverage gaps cluster around making itself more predictable to adopters (label/semantics alignment, consistent terminology, declared hierarchy completeness) and more demonstrably-effective at the outcome level (falsifiable value proposition, parity between framework self-use and adopter provisioning).

## Framework-purpose coverage (APPRC — Authority, Process, Protection, Relations, Continuity)

| Purpose | State |
|---|---|
| Authority | covered (slightly self-referential — F-P2-02) |
| Process | covered operationally; longitudinal-traceability weak |
| Protection | **strongest purpose** — S-Series + Risk Mitigation + Non-Maleficence give over-coverage (F-P2-09 merge signal) |
| **Relations** | **thinnest purpose** — 2 constitutional principles, 3 findings touch it (F-P2-13, F-C-06, F-P2-16) |
| Continuity | partial — principle exists but precedent-binding infrastructure does not (F-P1-05) |

---

## What the framework does well

This review is forensic; most findings are corrections. The positives are evidence-based and worth naming:

1. **Self-correcting discipline is active.** LEARNING-LOG has 2+ year of graduated patterns. v4.1.0 reclassification of Unenumerated Rights + Reserved Powers from S-Series to G-Series shows the metaphor-correction loop works reactively. Contrarian review catches most mis-classifications.

2. **Dogfooding is real.** Self-review uses the framework's own subagents (contrarian-reviewer, coherence-auditor). Governance evaluation is hard-enforced via hook. Hard-mode hooks empirically moved compliance from ~13% to ~90%+ (PROJECT-MEMORY:54) — a 7x improvement at the mechanism level.

3. **Declaration is well-written and honest.** Lines 18–53 articulate a specific problem (AI has knowledge without judgment), a specific journey (prompt → context → intent engineering), and acknowledge borrowing the US Constitution "as architecture, not metaphor." This is unusual clarity for a governance framework.

4. **Derivation chain discipline is enforced in 5 of 6 domains.** Domain principles cite Constitutional Basis (ai-coding 18, ui-ux 22, multi-agent 18, kmpd 12, storytelling 17). One outlier (multimodal-rag uses "Constitutional Derivation" as alias — documented alias, not a bug).

5. **Admission Test has teeth.** v4.1.0 removed Q0 (Purpose Alignment) after it failed its own Q4 (Evidence). Framework's quality gates are applied to framework's own content (LEARNING-LOG 2026-04-12 "Dogfooding Catches What Reviews Miss").

---

## Protocol & compliance

| Dimension | Result |
|---|---|
| Dogfood gate (Step 0) | PROCEED, confidence=high |
| Subagents used | 2 / 3 cap (contrarian-reviewer, coherence-auditor) |
| Forbidden-set exposures | 2 logged (E-01 minor CE snippet; E-02 contrarian read mapping tables during Step 3) |
| Read-only compliance outside `reviews/` | PASS |
| Protocol bypasses | None |
| verify_governance_compliance | PARTIAL (tool-matching limitation; reasoning trace has floor principles but `relevant_principles` list in gov-9af8ad5addff does not) |

Budget consumed: ~50 msg-equivalents of ~720 allocated; ~130 min of ~3.5h allocated. Substantial headroom remained; no step was truncated.

---

## Recommendations summary

Tier 1 (single Critical finding): build outcome-benchmark harness (R-01). Skeleton exists at `staging/benchmark_ab_test.py` — wire it up with pre-registered metrics.

Tier 2 (structural high): amend hierarchy to name Enforcement Architecture (R-02); merge Risk Mitigation into Non-Maleficence (R-03).

Tier 3 (medium, batchable): rename Case Law → Secondary Authority (R-04); add Admission Test Q7 Semantic-Label Risk (R-05); sync scaffold_project with CFR Standard Kit (R-06); fill Relations gap (R-07); per-document CHANGELOG convention (R-08); enabling_authority CFR frontmatter (R-09); reorder Articles in body to match announced sequence (R-10).

Tier 4 (low, do at cadence): terminology normalization (R-11); record corrections (R-12); domain-applicability for subagents (R-13); harness-terminology decision (R-14); orphan sentence cleanup (R-15); Goal-First demotion eval (R-16); DBC/ST boundary sharpening (R-17); reference-library auto-staging activation (R-18); Preamble consent clause (R-19); meta-principle FM codes (R-20).

Tier 5 (policy-level): stare-decisis admission decision (R-21); organic reference-library growth across domains (R-22).

Full plan at `05-remediation-plan.md`.

---

## Closing stance

The framework is operationally mature. Its state-of-the-moment correctness is high. Its gaps are longitudinal, outcome-measurable, and declarative-vs-operational — all three fixable without architectural overhaul. The Critical finding (F-P2-01, value proposition falsifiability) is also the highest-leverage opportunity: once the framework can empirically demonstrate the outcome improvement it claims, every other finding's severity re-calibrates against real data.

