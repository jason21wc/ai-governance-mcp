# 03 — Cross-Cutting Findings & Value-Proposition Falsifiability

**Scope per spec:** redundancies within and across domains, conflicts between levels, orphans, ungrounded claims, value-proposition falsifiability.

---

## §I — Themes across findings

Phase 1 + Phase 2 produced 26 findings (9 + 17). Grouping by structural theme reveals five clusters:

### §I.1 — Theme A: Metaphor-Label Inheritance Despite Explicit "Pattern, Not Analogy" Stance

**Findings in cluster:** F-P1-01 (Case Law label/semantics conflict), F-P1-03 (Constitutional Methods as operative layer), F-P2-04 (S-Series uses US-Constitutional prose framing).

**Pattern:** Framework explicitly adopts a "pattern, not analogy" stance (plan file line 28-34), and the LEARNING-LOG has two entries specifically warning against metaphor-over-operational-criteria classification (2026-04-12 "Metaphor-Driven Classification", 2026-02-28 "S-Series Keyword Trigger"). Yet three findings show inherited US-Constitutional labels that create downstream comprehension risk: "Case Law" that doesn't bind, "Constitutional Methods" that has no US analog, S-Series framing that invites misclassification.

**Cross-cutting diagnosis:** the framework's self-corrective mechanism (contrarian review + LEARNING-LOG) catches metaphor-errors *after* they occur (v4.1.0 reclassification of Unenumerated Rights out of S-Series; v2.38.1 CFR threshold rename). But it hasn't produced a *preventive* rule that names which US labels are metaphor-safe vs. metaphor-hazardous. New framework additions continue to inherit metaphor-shaped labels by default.

**Threatened properties:** predictable (readers expect §1-definition content behind §1-named labels).

---

### §I.2 — Theme B: Longitudinal Infrastructure Under-Built (Precedent, Amendment History, Authority Traceability)

**Findings in cluster:** F-P1-04 (per-method enabling-authority missing), F-P1-05 (no stare-decisis binding artifact), F-P1-06 (asymmetric amendment history), F-P2-06 (amendment entries don't link to process invocations), F-P2-14 (historical-amendment rationale inaccuracy), F-P2-17 (MA-Series dissolution orphan).

**Pattern:** the framework captures *what* rules exist at point-in-time (principles, methods, subagents) but under-builds mechanisms that make rules auditable over time: (a) per-method citation trace from regulation to statute; (b) stare-decisis-binding precedent accretion; (c) centralized / consistent amendment log; (d) audit-id linkage between amendment entries and rules-of-procedure process invocations.

**Cross-cutting diagnosis:** cross-sectional (now-view) quality is strong — tests pass, retrieval works, content is thorough. Longitudinal (over-time view) quality is weaker — diffs between versions, traceability of regulations to statutes, accumulation of applied precedent are all either manual or not captured. This is the class of thing that erodes slowly until a 2027-era audit would have to reconstruct from git history.

**Threatened properties:** dependable, repeatable, predictable.

---

### §I.3 — Theme C: Domain-Scope Asymmetry (ai-coding is Best-Resourced; Other 5 Domains Are Under-Provisioned)

**Findings in cluster:** F-P1-07 (reference-library only in ai-coding), F-P2-05 (multimodal-rag alone uses "Constitutional Derivation"), partial F-P1-04 (ai-coding-cfr has 7 Constitutional Basis citations; others have 0–1).

**Additional evidence not tied to a specific finding:**
- Domain CFR line counts: ai-coding = 9000, multi-agent = 4878, multimodal-rag = 2317, storytelling = 2083, ui-ux = 1321, kmpd = 778. Factor of 11.5× between largest and smallest.
- Appendix count: ai-coding-cfr has 12 (A–L); rules-of-procedure has 4 (G–J); others have none.
- Frontmatter tags: ai-coding's `domains.json` description is ~190 words; kmpd's is ~30 words.

**Cross-cutting diagnosis:** ai-coding was (and remains) the framework's highest-churn use case. Other domains are represented but at a fraction of the depth. For adopters in non-ai-coding domains, the retrieval experience is materially thinner. Not a defect per se — framework is transparent about its maturity asymmetries — but it is a scaling limit worth naming.

**Threatened properties:** effective (non-ai-coding adopters receive a less-complete framework), repeatable (graduation pathway functional only in one domain).

**No new finding** (covered by F-P1-07 + F-P2-05); recorded here as theme.

---

### §I.4 — Theme D: Adopter vs Framework Self-Use Asymmetry

**Findings in cluster:** F-P1-08 (BACKLOG used but not scaffolded), F-P2-07 (no cross-session drift subagent for adopters).

**Additional evidence:**
- `install_agent` tool allows installing all 10 subagents. `continuity-auditor` (narrative consistency) and `voice-coach` (character voice) are storytelling-specific but shipped/installable regardless of domain. Adopters in non-storytelling projects can (and do) install subagents that would never be applicable.
- `COMPLETION-CHECKLIST.md` is scaffolded in Standard kit only — adopters choosing Core kit don't get it, even though the framework's own docs refer to "run the completion sequence" as a canonical workflow.
- `documents/tiers.json` defines the universal floor but is not scaffolded — adopters can't customize the floor for their own project without editing the framework's own file.

**Cross-cutting diagnosis:** the framework is primarily used by one person on several projects, so "framework self-use" and "adopter use" overlap. This creates blind-spots: the author encounters their own friction points immediately (hence the rich BACKLOG) but doesn't experience adoption friction. For an open-source framework with adoption ambition, adopter-facing provisioning lags framework-self-use by a consistent margin.

**Threatened properties:** effective (adopters are under-served relative to framework's own use).

---

### §I.5 — Theme E: Enforcement Mechanisms Off-Hierarchy

**Findings in cluster:** F-P1-02 (declared 7-layer hierarchy omits hooks/CI/subagents/scaffold templates).

**Additional supporting evidence:**
- README.md:42 presents the 7-layer hierarchy as the canonical governance description for external readers. External readers searching for "how does the framework bind agents?" get no answer from the hierarchy — they must read CLAUDE.md + inspect `.claude/hooks/` independently.
- `workflows/COMPLIANCE-REVIEW.md` is not in the 7-layer declared hierarchy. It is the primary self-audit mechanism. Users invoked via "run compliance review" won't find it in the hierarchy table.

**Cross-cutting diagnosis:** the declared hierarchy was inherited from the US-Constitution pattern, which has no runtime enforcement mechanism; when the framework added that mechanism, the hierarchy wasn't amended. The framework's *operational* hierarchy (enforcement-wise) is: hooks → CI → pre-push → compliance-review → principles/methods. Its *declared* hierarchy is: S-Series → Meta → Statutes → Rules of Procedure → Regulations → SOPs → Case Law. Two hierarchies, not cross-linked.

**Threatened properties:** reliable, dependable, effective.

---

## §II — Additional cross-cutting findings (one-per-cause)

The five themes above are expressions of the existing 26 findings. Below are genuinely cross-cutting findings not already captured in Phases 1 or 2:

---

### F-C-01 — No preventive rule against metaphor-label inheritance at content admission; corrective catches happen post-hoc via contrarian review

- **Severity:** Medium
- **Category:** gap
- **Threatened:** predictable
- **Evidence:**
  - LEARNING-LOG entries 2026-04-12 "Metaphor-Driven Classification" (corrective, after v4.1.0 reclassification); 2026-02-28 "S-Series Keyword Trigger Produces False Positives on Negations" (corrective, after observed FP rate).
  - `rules-of-procedure.md:53` — importance tags exist but no "metaphor-hazardous label" warning in admission criteria.
  - `rules-of-procedure.md` §9.8 (per MCP query in Step 0) defines Admission Test; no question asks "does this name import a US-Constitutional semantics that the framework doesn't implement?"
- **Root-cause hypothesis:** each metaphor-error is treated as a one-off and corrected ad-hoc. The pattern is graduated-recognition (LEARNING-LOG records) but the admission-test hasn't incorporated a metaphor-hazard question. Contrarian review catches most; some slip past (F-P1-01 Case Law is a prominent current example).

---

### F-C-02 — Value proposition not falsifiable (already filed as F-P2-01 Critical; re-affirmed here for cross-cutting synthesis)

- **Severity:** Critical (no change)
- **Category:** ungrounded
- **Threatened:** effective, reliable, predictable
- **Cross-cutting weight:** this is the single highest-leverage finding in the review. It touches every theme: metaphor inheritance (Theme A) relies on framework-produced improvement for credibility; longitudinal infrastructure (Theme B) has no outcome-benchmark to stabilize against; domain asymmetry (Theme C) is unmeasurable without per-domain outcome; adopter provisioning (Theme D) has no test that adopters' AI outputs improve; enforcement (Theme E) is justified by the claim of improved outcomes that isn't measured.
- **Spec Step 8 rule confirmation:** "Value-proposition falsifiability check: is 'following ai-governance yields better outcomes than not following' articulated somewhere, testably? Missing = Critical." Confirmed Critical.

---

### F-C-03 — Framework-self-use and adopter-provisioning are not cross-audited; no test verifies parity

- **Severity:** Low
- **Category:** gap
- **Threatened:** effective (for adopters)
- **Evidence:**
  - `src/ai_governance_mcp/server.py:846-867` — scaffold definitions.
  - `BACKLOG.md` at repo root (620 lines) — in active use; scaffold does not include BACKLOG.
  - No test in `tests/` verifies "the files the framework scaffolds for adopters are sufficient for the workflows CLAUDE.md describes."
- **Root-cause hypothesis:** scaffold templates grew organically; no structural rule ties "file class scaffolded" to "file class required by CLAUDE.md / rules-of-procedure." The asymmetry is invisible unless an adopter reports friction.

---

### F-C-04 — Storytelling subagents (continuity-auditor, voice-coach) are installable for all projects regardless of domain

- **Severity:** Low
- **Category:** loose-end
- **Threatened:** efficient (wasted context in adopter projects)
- **Evidence:**
  - `AVAILABLE_AGENTS = {code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach}` at `src/ai_governance_mcp/server.py:907-918`.
  - `install_agent` tool doesn't check whether the adopter's project uses the relevant domain.
- **Root-cause hypothesis:** `install_agent` was built before the framework had multi-domain subagents. Cross-domain applicability of each agent wasn't checked. Easy fix — `domains.json`-style metadata on each subagent — but not yet done.

---

### F-C-05 — Rules-of-procedure `governance_level: rules-of-procedure` is a frontmatter value with no operative counterpart in domains.json

- **Severity:** Low
- **Category:** orphan
- **Threatened:** predictable
- **Evidence:**
  - `documents/rules-of-procedure.md:6` — `governance_level: "rules-of-procedure"`.
  - `documents/domains.json` — has entries keyed by domain name; no row for "rules-of-procedure" as a special governance tier that the retrieval system needs to handle specially.
- **Root-cause hypothesis:** rules-of-procedure was named uniquely but retrieval treats it as part of the "constitution" domain per domains.json row "constitution" → `methods_file: "rules-of-procedure.md"`. The governance-level value "rules-of-procedure" is informational frontmatter that the retrieval doesn't use. Minor infrastructure debt.

---

### F-C-06 — "Tool/Model Appendices" layer (`constitution.md:91`) embeds into CFR documents rather than existing as standalone files; there is no index or cross-reference scheme for an adopter to discover them

- **Severity:** Low
- **Category:** misplacement
- **Threatened:** effective
- **Evidence:**
  - Appendices A–L embedded in `documents/title-10-ai-coding-cfr.md:7217+`.
  - Appendices G–J embedded in `documents/rules-of-procedure.md:4946+`.
  - No file in `documents/` named `appendix-*.md`; no index in `domains.json` or `README.md` enumerating Appendices.
  - An adopter searching for "how do I configure Claude Code CLI?" would have to know to look inside the CFR file at an unadvertised offset.
- **Root-cause hypothesis:** Appendices accreted inside CFR files during expansion. No separate indexing convention was established. Retrieval can find them semantically, but discovery by title is hampered.

---

### §II.0a — Amendments from Step 10 (post-hoc miss-check)

- **F-P1-08 severity upgraded Low → Medium** per §D.2a/A-01 in 01-phase1-structural.md. BACKLOG:614 documents self-declared CFR-vs-scaffold contradiction. Recalculate totals below.
- **F-C-03 partially subsumed by upgraded F-P1-08.** Both cover adopter-provisioning parity; F-C-03 remains for "no test verifies parity" (a distinct structural gap from the contradiction itself).
- **BACKLOG items #41 (auto-staging), #43 (progressive disclosure), #48 (content scanning), #52 (tech-stack metadata), #54 (Superpowers analysis) show framework awareness of reference-library maturation needs.** No finding reversal; awareness is tracked, execution lagging.

### §II.1 — Counts added by cross-cutting

| Severity | Count |
|---|---|
| Critical | 0 (F-P2-01 re-affirmed, not re-counted) |
| High | 0 |
| Medium | 1 (F-C-01) |
| Low | 4 (F-C-03, F-C-04, F-C-05, F-C-06) |

### §II.2 — Full review totals (post-Step-10 adjustment)

| Severity | Phase 1 | Phase 2 | Cross-Cutting | Total |
|---|---|---|---|---|
| Critical | 0 | 1 | 0 | **1** |
| High | 2 | 1 | 0 | **3** |
| Medium | **5** (F-P1-08 upgraded) | 5 | 1 | **11** |
| Low | **2** (F-P1-08 no longer Low) | 10 | 4 | **16** |
| **Total** | **9** | **17** | **5** | **31** |

### §II.3 — Full threatened-property distribution

| Property | Findings that threaten it |
|---|---|
| reliable | F-P1-02, F-P2-01, F-P2-10, F-P2-14, F-P2-16 — **5** |
| predictable | F-P1-01, F-P1-03, F-P1-04, F-P2-01, F-P2-03, F-P2-04, F-P2-05, F-P2-09, F-P2-11, F-P2-15, F-C-01, F-C-05 — **12** |
| dependable | F-P1-02, F-P1-04, F-P1-05, F-P1-06, F-P2-02, F-P2-06, F-P2-09, F-P2-13, F-P2-17 — **9** |
| repeatable | F-P1-05, F-P1-06, F-P1-07, F-P2-06, F-P2-07, F-P2-10 — **6** |
| effective | F-P1-01, F-P1-02, F-P1-05, F-P1-07, F-P1-08, F-P2-01, F-P2-08, F-P2-13, F-C-02, F-C-03, F-C-06 — **11** |
| efficient | F-P2-09, F-P2-12, F-C-04 — **3** |

Root-cause signal (all findings): **predictable** (12) and **effective** (11) lead; **dependable** (9), **repeatable** (6), **reliable** (5), **efficient** (3) follow. Synthesis in Step 9.

