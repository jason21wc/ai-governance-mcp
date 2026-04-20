# 04 — Intent Engineering Synthesis

**Method per spec Step 9:** Aggregate all findings by threatened property. Property(ies) appearing most often = root-cause signal. State explicitly. Distinguish structural root causes (how the framework is organized) from content root causes (what it says).

---

## §I — Threatened-property aggregation (all 31 findings)

| Rank | Property | Count | Findings |
|---|---|---|---|
| 1 | **predictable** | **12** | F-P1-01, F-P1-03, F-P1-04, F-P2-01, F-P2-03, F-P2-04, F-P2-05, F-P2-09, F-P2-11, F-P2-15, F-C-01, F-C-05 |
| 2 | **effective** | **11** | F-P1-01, F-P1-02, F-P1-05, F-P1-07, F-P1-08, F-P2-01, F-P2-08, F-P2-13, F-C-02, F-C-03, F-C-06 |
| 3 | dependable | 9 | F-P1-02, F-P1-04, F-P1-05, F-P1-06, F-P2-02, F-P2-06, F-P2-09, F-P2-13, F-P2-17 |
| 4 | repeatable | 6 | F-P1-05, F-P1-06, F-P1-07, F-P2-06, F-P2-07, F-P2-10 |
| 5 | reliable | 5 | F-P1-02, F-P2-01, F-P2-10, F-P2-14, F-P2-16 |
| 6 | efficient | 3 | F-P2-09, F-P2-12, F-C-04 |

### §I.1 — Root-cause signal

**`predictable` (12) and `effective` (11) are tied within 1 count.**

The spec defines the root-cause signal as "property(ies) appearing most often." Two properties qualify. Both are reported.

**Interpretation:**
- **predictable** threatens reader/agent ability to anticipate framework behavior from its description. When labels mean less than they appear ("Case Law" that doesn't bind), when layers are announced in one order and presented in another (Q before O in document body), when terminology varies one-off (Constitutional Derivation vs Basis), adopters form inaccurate mental models.
- **effective** threatens the framework's ability to produce demonstrable output improvement. When the value proposition is not testable (F-P2-01), when enforcement mechanisms are hidden off-hierarchy (F-P1-02), when adopter provisioning lags framework self-use (F-C-03), the framework cannot prove to skeptics (or to itself) that it improves outcomes.

### §I.2 — Definition-divergence note (`constitution.md:42-46` + plan line 36-48 five purposes vs spec's six Intent Engineering properties)

Per F-P1-09: the framework names its own 5-purpose goal set (Authority, Process, Protection, Relations, Continuity — APPRC) at a different abstraction than the spec's 6-property set (reliable, predictable, dependable, repeatable, effective, efficient — RPDREE). The synthesis below treats both:

| Framework purpose (APPRC) | Findings primarily threatening | Spec properties in tension |
|---|---|---|
| Authority | F-P1-02 (enforcement off-hierarchy), F-P2-02 (self-referential grant) | reliable, dependable |
| Process | F-P1-06 (amendment history), F-P2-06 (process-invocation trace), F-P1-04 (enabling-authority), F-P2-11 (Goal-First Dependency Mapping placement) | dependable, repeatable, predictable |
| Protection | F-P2-04 (S-Series metaphor framing), F-P2-09 (Risk Mitigation ↔ Non-Maleficence duplication) | predictable, efficient |
| **Relations** | F-P2-13 (under-operationalized), F-C-06 (Appendix discovery) — **thinnest coverage at principle level** | effective, dependable |
| Continuity | F-P1-05 (no precedent), F-P2-17 (MA-Series orphan), F-C-01 (no metaphor-prevention rule) | repeatable, dependable, predictable |

**Relations is the weakest purpose both by principle-count (only 2 constitutional principles operationalize it per coherence-auditor) and by finding-weight (3 distinct findings touch Relations-adjacent content).**

---

## §II — Structural vs content root causes

### §II.1 — Structural root causes (organizational, not text)

**Structural RC-1: Declared hierarchy omits enforcement mechanisms**

Findings: F-P1-02, F-C-06.
What it means: the 7-layer canonical hierarchy (constitution.md:82-92, echoed in README.md:42) names principles, methods, regulations, case law — but not the mechanisms that actually bind (hooks, CI, subagents, scaffold, pre-push gates). An adopter reading the hierarchy cannot answer "where is enforcement defined?" from hierarchy alone. Operational binding exists (and works), but the declared structure doesn't reflect it.

Why it persists: the hierarchy inherited the US-Constitution shape, which has no runtime-hook equivalent; adding a layer for novel-to-US mechanisms would break the pattern-level symmetry. The framework chose symmetry over completeness.

Fix class: amend the declared hierarchy to include a "Structural Enforcement" layer, or add a separate "Enforcement Architecture" document that parallels the hierarchy. Either preserves the pattern while completing the picture.

**Structural RC-2: Longitudinal auditability deferred**

Findings: F-P1-04, F-P1-05, F-P1-06, F-P2-06, F-P2-14, F-P2-17.
What it means: the framework manages state-of-the-moment well. It manages over-time evolution weakly. Per-method statute citations don't exist. Precedent doesn't bind. Amendment history is asymmetric (constitution has it; nothing else does) and not cross-linked to audit IDs. Orphan artifacts (MA-Series reference) remain in logs.

Why it persists: state-of-the-moment is the framework's use case today (one-shot evaluate_governance calls, current-session context). Longitudinal discipline requires tooling that wasn't needed until recently. The framework's own maturity-monitoring (compliance-review at 10-15 day cadence) IS a longitudinal mechanism, but operates on the framework's state, not on amendment-trace linkage.

Fix class: establish (a) per-method enabling-authority frontmatter field; (b) standardized per-document CHANGELOG subheading or separate changelog-per-document; (c) amendment-entry audit_id linkage convention.

**Structural RC-3: Adopter-facing provisioning lags framework-self-use**

Findings: F-P1-08, F-C-03, F-C-04.
What it means: framework self-use (this repo) exceeds what scaffold_project provisions for adopters. BACKLOG scaffolded-not (but used heavily); subagents installable regardless of domain applicability; no parity test.

Why it persists: single-primary-author workflow — the author encounters and fixes their own friction immediately but doesn't experience adoption friction. Feedback loop from adopters is indirect.

Fix class: audit scaffold against CLAUDE.md workflow requirements + add domain-applicability metadata to subagents + add a parity test.

**Structural RC-4: No preventive rule against metaphor-label inheritance**

Findings: F-P1-01, F-P1-03, F-P2-04, F-C-01.
What it means: framework corrects metaphor-errors reactively (contrarian review, LEARNING-LOG entries) but has no admission-test question that preventively screens a proposed label for "does this US-Constitutional name import semantics the framework doesn't implement?"

Why it persists: each metaphor-error is treated as a one-off. The shape of the preventive rule is clear (it would be a new Admission Test question); it hasn't been authored.

Fix class: add Admission Test Q7 "Semantic-Label Risk: does the proposed name import §1-equivalent content that the framework does not implement? If yes, rename or add a disclaimer."

### §II.2 — Content root causes (text, not organization)

**Content RC-1: Reference Library labelled "Case Law" while stripped of override**

Findings: F-P1-01.
Fix class: rename to "Reference Library (Secondary Authority)" in the hierarchy table; remove "Case Law" label; retain label elsewhere only where clearly pedagogical.

**Content RC-2: Risk Mitigation by Design duplicates Non-Maleficence**

Findings: F-P2-09.
Fix class: merge Risk Mitigation into Non-Maleficence's "Compliance by Default" section, or demote Risk Mitigation to Methods (Part X.Y under Non-Maleficence).

**Content RC-3: Relations purpose under-operationalized**

Findings: F-P2-13.
Fix class: promote an existing Methods item (Full Faith and Credit — currently at Methods Part 9.7.6 per v4.1.0 history) to a principle in G-Series, or draft a new Relations-purpose principle.

**Content RC-4: Historical amendment records have inaccuracies and orphan artifacts**

Findings: F-P2-14, F-P2-17.
Fix class: add a correction-entry to v2.8.0 noting "Rich but Not Verbose" demotion was supplemented by Effective & Efficient Communication addition; add a v4.x entry narrating MA-Series dissolution.

**Content RC-5: Terminology inconsistency (`Constitutional Basis` vs `Constitutional Derivation`)**

Findings: F-P2-05.
Fix class: normalize on `Constitutional Basis` across all domain principle files (editing the one outlier, title-40-multimodal-rag); remove the alias from rules-of-procedure §3.5.1 once convergence is achieved.

### §II.3 — Mixed structural + content root cause

**Mixed RC-1: Value proposition claim is unfalsifiable**

Findings: F-P2-01 (Critical), F-C-02.

This is the single highest-leverage finding in the review.

- **Content side:** Declaration (`constitution.md:38`) and README both claim "consistent, reliable results that actually deliver on the potential." The claim is made.
- **Structural side:** no test harness exists that compares framework-guided AI outputs vs. unguided outputs. `staging/benchmark_ab_test.py` is an early skeleton, not wired. All other tests measure mechanism (retrieval MRR, hook behavior) — not outcome.

Fix class: either (a) build an outcome benchmark that produces a governed-vs-unguided effect-size measurement on a stable task set, or (b) soften the claim to "mechanism-quality, not outcome-quality." Path (a) is higher leverage; path (b) is lower cost.

---

## §III — Root-cause priority ranking for remediation

Applying two lenses:
- **Property-weight** (how many findings share threatened properties)
- **Leverage** (how many *other* findings become easier to address if this one is addressed first)

| Rank | Root cause | Threatened properties | Leverage | Addresses findings |
|---|---|---|---|---|
| 1 | **Mixed RC-1: Value proposition unfalsifiable** | effective, reliable, predictable | Highest — every other finding's severity depends on whether the framework actually improves outcomes; without the measurement, all other work is uncalibrated | F-P2-01, F-C-02 directly; indirectly re-scopes Themes A/B/C/D/E |
| 2 | **Structural RC-1: Enforcement off-hierarchy** | reliable, dependable, effective | High — once enforcement is named in the declared structure, adopters can locate binding force and other findings (F-P1-02, F-C-06, F-P2-08) cluster cleanly | F-P1-02, F-C-06, partial F-P2-08 |
| 3 | **Structural RC-2: Longitudinal auditability** | dependable, repeatable, predictable | Medium-high — 6 findings addressed by one structural pass (enabling-authority field + per-document CHANGELOG + amendment-id link) | F-P1-04, F-P1-05, F-P1-06, F-P2-06, F-P2-14, F-P2-17 |
| 4 | **Structural RC-4: Metaphor-prevention admission gate** | predictable | Medium — prevents future F-P1-01-class errors; does not fix existing ones | F-C-01; prevents future analogs of F-P1-01, F-P1-03, F-P2-04 |
| 5 | **Content RC-1: Reference Library rename** | predictable, effective | Medium — one-line fix unblocks F-P1-01 directly | F-P1-01 |
| 6 | **Content RC-3: Relations operationalization** | effective, dependable | Medium — fills the thinnest Preamble purpose | F-P2-13 |
| 7 | **Content RC-2: Risk Mitigation / Non-Maleficence merge** | predictable, efficient | Medium — one-off consolidation | F-P2-09 |
| 8 | **Structural RC-3: Adopter-facing parity** | effective | Lower (small adopter-side cost per finding; many small items) | F-P1-08, F-C-03, F-C-04 |
| 9 | **Content RC-4: Amendment record corrections** | dependable, reliable | Low (cosmetic per framework's own stance that history "carries no force of law") | F-P2-14, F-P2-17 |
| 10 | **Content RC-5: Constitutional Basis/Derivation normalization** | predictable | Low (well-documented alias) | F-P2-05 |

Remediation plan (Step 11) orders against this ranking.

---

## §IV — What the root-cause signal tells us about the framework's current state

The framework is **strong at state-of-the-moment correctness** (mechanism tests pass, principles are well-written, S-Series is operationally pre-emptive, hooks block as designed) and **weak at two things**: (a) proving that state-of-the-moment correctness translates to downstream outcome quality, and (b) maintaining cross-time discipline (precedent, amendment history, enabling-authority).

Framed against the framework's own APPRC purposes:
- Authority: covered, slightly self-referential (F-P2-02).
- Process: covered operationally; longitudinal-process traceability weak.
- Protection: **strongest purpose** — S-Series + Risk Mitigation + Non-Maleficence overlap give over-coverage, not under-coverage (F-P2-09 is a consolidation opportunity).
- **Relations: thinnest purpose — 2 principles, 3 findings, identified gap.**
- Continuity: partial — Continuous Learning principle exists but precedent-binding infrastructure doesn't (F-P1-05).

Framed against spec's RPDREE properties:
- The framework is least predictable (12 findings) and least demonstrably-effective (11 findings + F-P2-01 Critical).
- Most reliable + efficient (fewer findings).

**One-sentence synthesis:** the framework is maturely built for individual-moment correctness but under-built for cross-time and cross-adopter scaling — and the most acute shortfall is that its core value claim (framework-guided AI produces better outcomes than unguided AI) is asserted in the Declaration but not falsifiable by any test.

