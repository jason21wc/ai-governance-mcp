# Source-Review Procedure — Intent-First External-Source Evaluation

Authority: this skill operationalizes the external-content evaluation discipline already in
`documents/rules-of-procedure.md` §9.8 (Admission Test §9.8.1, Duplication Check §9.8.2,
enumeration-verification + method-level-reflection §9.8.5) and the `external-input-gap-analysis`
behavioral floor. It does not restate those rules — it sequences them, leading with intent.

**Core stance:** *Intent is the unit of comparison.* Evaluate the abstracted intent against
coverage; the surface item (a named principle/method/tool) is only the evidence that points to it.
**Propose, never write** — this skill has no Edit/Write tool; the human applies approved verdicts.

---

## Phase 0 — Govern

Call `evaluate_governance(planned_action="review external source against ai-governance")`. Proceed
per its routing (PROCEED/REVIEW/ESCALATE). This is a read-and-propose task; it will normally PROCEED.

## Phase 1 — Ingest

Acquire the source by whichever channel the user provided:
- **Pasted text** — use as-is.
- **Local file** — `Read` the path (PDF/DOCX/MD/HTML/etc.).
- **URL** — `WebFetch` the page.
- **Topic only** — `WebSearch` to locate, then `WebFetch` the best source; confirm the chosen source with the user.

Record the source's identity (title, author/org, URL/path, date) — it becomes the INFLUENCES row's
"Source" field.

## Phase 2 — Extract (face value)

Enumerate the discrete items the source asserts — principles, methods, tools, conventions, claims —
WITHOUT yet judging coverage. Apply the §9.8.5 enumeration-verification discipline: do two passes
(a **Concepts** pass and an **Artifacts/tools** pass) and state explicitly **"N items identified."**
List each as a short surface description. Do not merge or pre-filter; that happens after intent
abstraction.

**Third pass — the ASSEMBLY.** Item enumeration extracts *nodes* and is structurally blind to the
*graph*. Ask explicitly: **does the source assert an ORDER, a lifecycle, or a set of dependencies
between its items — and is that ordering itself a claim?** Record it as its own item if so. A source
whose every individual method you already cover can still contribute the sequence in which they run,
and that contribution is invisible to a per-item coverage check by construction — every node returns
"covered" while the edges are never examined. *(Observed session-267: a review returned "adopt
nothing" on 32 individually-covered concepts; the user asked "does it give a workflow?" and the
source's real contribution turned out to be sequencing — evaluate before you improve, select before
you evaluate, tune last — against a framework that classifies lifecycle rigor but prescribes no
build order.)*

## Phase 3 — Abstract-to-intent (the crux)

For each extracted item, write its **intent**: the failure-mode it prevents or the goal it serves,
*above* the surface form. Use `meta-core-systemic-thinking` (name the structural cause/goal, not the
visible mechanism) and the Intent Discovery 5-level model (stated form → underlying need). Two items
with different surface forms may share one intent; record the intent, not the wording.

> Example — surface item "a `/plan` skill that blocks coding until a design doc exists" → intent
> "force design-before-implementation." Surface differs from our plan-mode; intent may already be
> covered by `coding-process-design-architecture-supremacy`.

## Phase 4 — Coverage-check each intent

For each distinct intent, check whether ai-governance already covers it — querying the *intent*, not
the source's wording:
- `query_governance("<intent>")` — principles/methods that already encode it.
- `search_references("<intent>")` — Reference Library precedent.
- `query_project("<intent>")` — prose/code where it's operationalized.

Apply the **§9.8.2 Duplication Check** decision tree to the result. Record, per intent: the covering
IDs/files found, and a coverage verdict — **covered / partially-covered / not-covered**.

**Match the ALTITUDE of the incumbent to the altitude of the item.** §9.8.2 step 3 already says
"check all levels"; this names the failure that ignoring it produces. For an *operational* external
item (a procedure, a loop, a workflow), the coverage evidence must include at least one
**methods-layer** citation (`*-cfr.md`) — or an explicit *"searched the methods layer with
`query_project`/`query_governance`, nothing found,"* **naming the tool actually used.** A `grep`
does not discharge this clause. Grep matches strings; coverage is a question about *concepts*, and
an incumbent that words the idea differently is invisible to it — which is exactly the case the
altitude rule exists to catch. CLAUDE.md's search rule already says to use CE for concept
discovery and grep only for exact strings in a known file; this is that rule at the one step where
violating it silently manufactures a false negative. **Treat "nothing found" as a claim requiring
evidence, not an escape hatch** — it is an unfalsifiable negative about your own thoroughness
(§9.8.8.1), checkable only by someone re-running the search. A coverage verdict whose only cited incumbent is a `meta-*` constitutional principle is
**incomplete, not merely thin**: constitutional principles are general by design, so any specific
external framing will look sharper than its incumbent, and the review systematically over-includes.
That is the precise mechanism by which intellectual-generosity bias operates here — not "I want to
like this," but "I compared against the wrong altitude." *(Observed session-267: an external
"metrics-driven development" framing was compared against `meta-quality-verification-validation`
and nearly promoted, while `title-10-ai-coding-cfr` §5.2.8 Eval-Driven Development — forty lines of
directly competing, strictly more operational content — went uncited. A contrarian pass found it.)*
*(Observed again, session-267, the very next `/source-review`: the escape hatch was taken —
"searched the methods layer, nothing found" — on the strength of a **grep** for output-*filtering*
vocabulary. The incumbent, `title-40-multimodal-rag-cfr` §9.1's `Response generation | Verify all
images in response are accessible to user`, contains none of those words and sat in the section
whose Purpose line reads "Procedures for implementing DG1." A coherence audit found it, after the
false claim had already shipped into a changelog and an INFLUENCES row. **n=2 in one session, both
on the first pass, both self-certified** — which is why the clause above now names the tool.)*

**Citation integrity.** Before the verdict report ships, verify every string presented in quotation marks against the actual stored content of the cited principle or method (via `query_governance` or direct read). A paraphrase presented as a direct quote is a fabricated citation — actively misleading in a way an absent search is merely incomplete. If the quoted string does not appear verbatim or near-verbatim, downgrade to a paraphrase and re-examine whether the underlying claim holds without the manufactured authority. *(Third variant of the same self-certification weakness this Phase's n=2 clause addresses: not "I didn't search hard enough" and not "I compared against the wrong altitude" but "I manufactured supporting evidence." Origin: Agent Plugins v1.0.0 source-review.)*

## Phase 5 — Classify + gate (the "genuinely new" *and* the Adopt path)

Map each intent to one of the four INFLUENCES.md attribution categories, or to "genuinely new":
- **Adopted** — we should take the pattern substantially as-is (intent + good surface form).
- **Inspired-by + modified** — the intent is worth acting on but our implementation would diverge.
- **Independently-developed equivalent** — we already cover the intent via different mechanics. (But check: does the source package the same intent *better*? A cleaner surface form, a more memorable framing, a specific technique worth grafting → promote to **Inspired-by + modified**.)

For **every "independently-developed equivalent" verdict**, answer three close-out questions before finalizing:
1. **Best-for-any-user.** Does the source package this intent better for *any* user of the framework — not just the current project? The framework is modular across different projects, tools, and uses; evaluate coverage from that scope, not the project you're sitting in.
2. **Future coverage.** Is the framework's coverage sufficient for uses it doesn't serve yet? A gap that doesn't matter today can matter when a user's project consumes third-party plugins, designs an API, or targets a platform the framework hasn't touched.
3. **Industry convergence.** If multiple major vendors converge on this pattern, is alignment valuable even when existing coverage works? Convergence is external validation; unexamined divergence is a portability liability.

If any answer is "yes," promote to **Inspired-by + modified** (graft the technique) or re-evaluate as **Genuinely new**. The parenthetical above is the entry point; these three questions are the forcing function that prevents "covered" from being a terminal verdict.

*(Origin: Agent Plugins v1.0.0 source-review — first pass classified 14 intents as independently-developed without asking these questions; corrected pass found 3 confirmed gaps and 1 weak gap at the methods layer.)*
- **Considered and rejected** — intent already covered, or fails our bar; cite the covering ID / the reason.
- **Genuinely new** — no existing principle/method covers the intent.

For **every "genuinely new" candidate**, before proposing it:
1. Run the **§9.8.1 Admission Test (7 questions)** — Coverage / Placement / Derivation / Evidence / Enforceability / Stability / Semantic-Label-Risk. Cite it; answer each question. (Do not restate the test.)
2. Dispatch a **`contrarian-reviewer`** subagent (Agent tool) to attack the "it's new" claim and the "we should adopt it" claim — explicitly guarding **intellectual-generosity bias** (LEARNING-LOG 2026-02-28: the desire to find value in external work biases toward false inclusion). Demote to "Considered and rejected" / "Independently-developed" if the contrarian refutes novelty or value.

For **every "Adopt" candidate** (take the pattern substantially as-is), run a lighter **source-quality gate** before proposing it. The Admission Test + coverage-check above examined only our *internal* coverage and the *novelty* claim; neither examined the *source's own quality*, yet Adopt imports an external **surface form** wholesale — the higher-risk verdict:
1. **Best-in-class.** Coverage-check answered "do *we* already have this intent?" — not "is *this source* the strongest exemplar of the intent, or merely the one presented?" Scan for a stronger external exemplar (a quick `WebSearch`); if one plausibly exists, prefer *Inspired-by + modified* over *Adopt-as-is*, or flag the survey gap. Best-in-class + supersession doctrine already lives at `title-10 §3.1.4` (Tool Content Model; cf. §5.6.5) — cite it, don't restate. Novel-to-us ≠ best available.
2. **Currency.** In a fast-moving domain (AI tooling, model capabilities, framework APIs) discount surface claims by the source's age and verify time-sensitive claims still hold against the latest before adopting — *intents* are durable, *surface claims* go stale (constitution "Stale Record" pitfall). This is a second use for the Phase-1 source date: a staleness input here, not only the INFLUENCES "Source" field.

Fold both into the same `contrarian-reviewer` dispatch as the novelty gate — one pass covering the genuinely-new *and* the Adopt candidates.

This gate is the highest-value step: it is what prevents the framework absorbing redundant, unjustified, superseded, or second-best additions. (Structural note: pre-this-rule the skill gated "genuinely new" hard but let "Adopt as-is" through *ungated* — the higher-risk path, since it imports a surface form wholesale. This closes that gap.)

## Phase 6 — Propose (never write)

Emit the **verdict report** (shape below). For each item, propose where it lands, per the routing the
INFLUENCES.md "How to extend" section defines:

| Verdict | Proposed action (human applies) |
|---|---|
| Already covered | INFLUENCES "Considered and rejected" **or** "Independently-developed equivalent" row, citing the covering ID. (Optionally: a §9.8.5 method-level-improvement note if the source packages the same intent better.) |
| Covered-but-improvable | Method improvement to the existing surface (no Admission Test — §9.8.5) + INFLUENCES "Inspired-by + modified" row. |
| Adopt (passed the source-quality gate) | INFLUENCES "Adopted" row + the target surface (file + section it would land in). |
| Genuinely new (passed §9.8.1 + contrarian) | A **BACKLOG.md Discussion item** ("genuinely-new intent → consider"), NOT a framework edit. Anticipatory items are valid. |
| Worth preserving as artifact | A `capture_reference` proposal (domain + title + content seed) for the Reference Library. |

Close with a **dogfood disclosure**: which governance/CE tools were queried, and the contrarian
verdict on each "genuinely new" candidate.

---

## Verdict report shape (output template)

```
# Source Review — <title> (<author/org>, <date>) — <url/path>

Items identified: N

## Per-item verdicts
1. Surface item: <one line>
   Intent: <the failure-mode/goal above it>
   Coverage: covered | partial | none — evidence: <IDs / files from query_governance/search_references/query_project>
   §9.8.5 method-level: <no improvement | source packages better — describe what to graft>
   Verdict: <Adopted | Inspired-by+modified | Independently-developed | Considered-and-rejected | Genuinely-new>
   Proposed action: <INFLUENCES row (category) | method improvement | BACKLOG item | capture_reference | none>
   [If Genuinely-new] Admission Test: <Q1..Q7 answers>; Contrarian verdict: <real-new / refuted + why>
... (repeat per item)

## Proposed INFLUENCES.md row(s)
<ready-to-paste row(s), to ship in the same commit as any influenced method>

## Proposed BACKLOG item(s) / capture_reference call(s)
<for genuinely-new intents / preserve-worthy artifacts>

## Dogfood disclosure
Tools queried: <...>. Contrarian pass on "new" verdicts: <...>.
```

## Escalation / stop points

- Source unreadable or paywalled → report what was accessible; do not fabricate the source's content.
- ESCALATE from Phase 0 governance → stop, surface to the user.
- A "genuinely new" candidate that touches safety (S-Series) → flag for explicit human decision, do not propose adoption.
- More than ~10 items → process the highest-signal first; state what was deferred (no silent truncation).
