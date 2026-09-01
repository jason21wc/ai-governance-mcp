# PMO Procedure — Purpose · Method · Outcomes Lens

Authority: this lens operationalizes existing ai-governance principles — it adds none.
It draws on `meta-core-single-source-of-truth` (charters point, never restate),
`meta-core-structural-foundations` (one responsibility per layer),
`meta-core-systemic-thinking` (name the structural cause of a gap),
`meta-quality-verification-validation` (evidence per verdict; the closed loop),
`meta-operational-resource-efficiency-waste-reduction` (a mechanism serving no purpose is waste),
`kmpd-quality-assurance-qa2-artifact-adoption-fitness` (usability judged per audience),
`kmpd-training-tl1-audience-appropriate-design` (calibrate the charter to its reader),
and `coding-context-context-engineering-discipline` (charters are living, owned context artifacts with update triggers).

**This skill is the canonical home of the lens.** A project's own filled-in charter lives in
that project and points here; it does not copy this method.

**Applies to** any project that turns inputs into outputs — a data/knowledge library, a
transformer/product, a process/SOP, a memory-or-context kit. Asset- and domain-agnostic.

---

## The three slots, precisely

### Purpose — value-anchored, not a mission statement
Name three things, in 2–5 lines:
- **Audiences** — specific roles, not "users" (e.g. buyers, sellers, brokers, owners, renovators).
- **The alternative it beats** — what those audiences would otherwise use, and on which dimensions
  this wins (quality/extent of information, speed, analysis beyond the obvious, blind-spot surfacing).
- **Stability** — purpose changes rarely; if it churns, it was a feature list, not a purpose.

A purpose that can't fit 5 lines is hiding method inside it.

### Method — mechanisms, each earning its place
Method is the existing body of rules, pipelines, schemas, SOPs, adjustment rules, data-source
integrations, enrichment steps. The lens does NOT rewrite it. It asks two things of every mechanism:
- It traces to at least one purpose claim (a mechanism serving nothing is a waste/5S candidate —
  flag, don't delete unilaterally).
- It is checkable — a rule whose conformance cannot be verified will drift silently (a smell).

### Outcomes — artifact + usability + closed loop
Three components; most frameworks are missing the third:
- **Artifact(s)** — what concretely gets produced and where it lands (doc types, views, files).
- **Usability** — the purpose claims must be *visible* in the artifact, judged per audience. If
  blind-spot identification is a headline value, it cannot be a footnote. UI/UX is judged against
  Purpose, not taste.
- **Verification (the closed loop)** — how you know the purpose was delivered, not just that the
  artifact shipped. Two flavors by project type (below): *conformance invariants* for stewardship
  projects, *accuracy/feedback tracking* for transformer projects (e.g. estimate vs quote vs actual,
  when available). Measurements route back into Method (calibration, rule changes, learning log).
  A measure earns its place only if it is actually checked or queried — invariants and health
  signals, not vanity metrics.

---

## The traceability contract (the core of every review)

Run the trace in both directions:

| Direction | Question | Failure it catches |
|---|---|---|
| Purpose → Method | Which mechanism delivers each purpose claim? | Aspirational claims nothing produces (**unclaimed value**) |
| Method → Purpose | Which claim does each mechanism serve? | Waste / gold-plating (**unowned mechanism**) |
| Purpose → Outcome | Is each claim visible and usable in the artifact, per audience? | Value produced but buried (**buried value**) |
| Outcome → Purpose | What measurement shows the claim was delivered? | Open loop — shipping blind (**open loop**) |

The four failure names in bold are the four gap classes used in review mode.

## Instantiation by project type

Universal slots; type-specific content. Do not force one type's flavor onto another. Hybrids exist
(a product with an internal library) — give each part its own row rather than blending flavors.

| Project type | Purpose flavor | Outcome / verification flavor |
|---|---|---|
| **Stewardship / SSOT** (holds truth) | Trust + findability for people AND downstream products | **Conformance invariants** — structure stays true, drift is detectable |
| **Transformer / product** (inputs → deliverable) | Differentiated value to named external audiences | **Deliverable + usability + accuracy loop** (output vs reality over time) |
| **Process / SOP** (governs an activity) | Why this process shape prevents specific failure modes | **Gates passed** — each stage's exit condition is the outcome check |
| **Memory / context kit** (preserves context) | Continuity: any session can resume with full context | **Currency** — state matches reality; stale references flagged at start |

---

## Phase 0 — Govern (both modes)

Call `evaluate_governance(planned_action="PMO <charter|review> of <project>")`. Act on the assessment
(PROCEED / REVIEW / ESCALATE); cite the audit id in your output. After completion, call
`log_governance_reasoning` if the principles materially shaped a decision.

---

## CHARTER MODE (build)

**C1 — Inventory the surfaces.** List the project's artifacts: conventions, schemas, SOPs, templates,
generated views, memory files, scripts, and the actual corpus they govern (folders/files/outputs).

**C2 — Extract the implicit PMO.** From those surfaces, draft the project's Purpose, Method map, and
Outcomes as they *currently* exist, citing where each piece lives. Do not ask the owner to restate
what is already written; DO ask when a purpose claim is genuinely undiscoverable — that absence is
itself a finding.

**C3 — Classify the project type** (table above) so the Outcome/verification flavor is right.

**C4 — Write the charter** (template below) into the project — README or `_ai-context/`. Pointers to
method docs, never restatements (`meta-core-single-source-of-truth`); no volatile counts/dates-as-state
(those belong to generated views); calibrate the wording to the reader (`kmpd-training-tl1`). The
"verified by" line is mandatory.

**C5 — Stop at the charter.** Do not restructure the project's docs to match a format; the charter is
added at a natural touch, not big-bang. Any deeper fix is a separate, separately-governed change.

### Charter block template (≤ 12 lines)

```markdown
## Purpose · Method · Outcomes (charter)

**Purpose** — {audiences} get {value}, beating {their alternative} on {differentiators}. (2–5 lines)
**Method** — {mechanism → pointer to its doc}; {mechanism → pointer}; … (pointers only — never restate rules)
**Outcomes** — {artifacts + where they land}; {usability commitments per audience};
**verified by** {invariants list or accuracy loop + where the checks/measurements live}.
Last PMO review: {date, governance audit id}.
```

---

## REVIEW MODE (audit)

**R1 — Inventory the surfaces** (as C1). Reviews that read only the docs miss docs-vs-reality drift —
check the docs AND the corpus they govern.

**R2 — Extract the current PMO** (as C2), citing where each piece lives.

**R3 — Run the checklist** (below). Every verdict needs cited evidence: a file, a line, an artifact,
or a computed check. "Looks fine" is not a verdict.

**R4 — Classify each gap** into one of four classes, naming the *structural cause*, not the symptom
(`meta-core-systemic-thinking`):
- **(a) unclaimed value** — a purpose claim with no mechanism.
- **(b) unowned mechanism** — a method rule serving no claim (waste/5S — report, don't delete).
- **(c) buried value** — a claim delivered but invisible/unusable in the artifact.
- **(d) open loop** — no verification that the claim was delivered.

**R5 — Report read-only.** Findings first, with evidence and classification. Propose minimal fixes;
distinguish reversible/low-stakes (do under standing owner instructions, if given) from judgment calls
(owner decides). Do NOT apply fixes in this mode.

**R6 — Fixes are separately governed.** Each fix runs under its own `evaluate_governance` and lands in
the project's decision record. History shows the decision-log row is the step that gets skipped —
check all recording surfaces.

### The audit checklist

Every item requires cited evidence. ✔ / ✘ / N/A (justify N/A).

**Purpose**
- **P1** Purpose names its specific audiences.
- **P2** Purpose states why it beats each audience's best alternative (the differentiators).
- **P3** Purpose is ≤ 5 lines and stable (no feature-list churn).

**Method**
- **M1** Every purpose claim traces to ≥ 1 named mechanism.
- **M2** Every mechanism serves ≥ 1 purpose claim (violations = 5S flags, reported not deleted).
- **M3** Every method rule is checkable — a conformance test exists or can be stated.

**Outcomes**
- **O1** Outcome artifacts are named concretely, with where they land.
- **O2** Each headline purpose claim is visible and usable in the artifact, judged per audience.
- **O3** Verification exists: conformance invariants (stewardship) or accuracy/feedback measures
  (transformer), actually checked — not aspirational.
- **O4** The loop is closed: outcome measurements have a route back into method (calibration, rule
  updates, learning log).

**Cross-cutting**
- **X1** The PMO layer creates no duplicate homes — charters reference method docs, never restate them;
  cross-doc invariants live in exactly one place.
- **X2** Every checklist verdict cites evidence.
- **X3** Review was read-only; fixes went through governance separately.
- **X4** No hardcoded volatile values in the charter (counts, dates-as-state) — those belong to
  generated views.

---

## Anti-patterns (guard against each)

- **Boilerplate rot** — stamping PMO headers on every doc, which then go stale. Apply the lens at
  review time; add explicit blocks sparingly and only where maintained.
- **Duplicate SSOT** — a charter that restates rules from the method docs. Charters point; they never copy.
- **Checkbox theater** — running the checklist without evidence (X2 exists because an asserted checklist
  is worse than none — it manufactures false confidence).
- **Metric theater** — outcomes as vanity numbers nobody queries. Measured because used, or cut.
- **Open loop accepted as done** — "the artifact shipped" is an output, not an outcome (O3/O4).
- **Big-bang retrofit** — restructuring every doc to fit the format. The format serves review, not the reverse.

## Maintaining this lens

This skill is the lens's canonical home, so its evolution rule lives here. Propose an update — under
governance (`evaluate_governance` before, `log_governance_reasoning` after) — when:
- **(a)** a review surfaces a gap class the four classes don't cover;
- **(b)** a new project type doesn't fit the instantiation table (§ project-type table); or
- **(c)** a checklist item proves untestable in practice (it can't be answered with evidence).
Edits originate in this file only; each project's charter points here and is never the place to change
the method (`meta-core-single-source-of-truth`). This is NOT a restructuring mandate or a template to
stamp on every doc — existing docs get charter blocks only at their next natural touch.

## Escalation / stop points

- Purpose genuinely undiscoverable from the surfaces → report that absence as a finding; ask the owner.
- ESCALATE from Phase 0 governance → stop, surface to the owner.
- A proposed fix touches safety, money movement, or credentials → flag for explicit owner decision; do not apply.
- More than ~10 findings → report the highest-severity first; state what was deferred (no silent truncation).
