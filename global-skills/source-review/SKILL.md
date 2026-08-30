---
description: Review an external SOURCE (article, paper, repo, talk, tool, framework, blog post) against ai-governance. Extracts the source's items, abstracts each to the INTENT above the surface, checks whether the framework already covers that intent, and PROPOSES where each verdict lands (INFLUENCES.md row / reference capture / backlog item). Intent is the unit of comparison — not the surface item. Invoke when the user shares external material to evaluate against the framework ("review this article/paper/repo against our governance", "is this idea new to us?", "should we adopt anything from this?"). Do NOT use to review our own code (use /code-review) or to rewrite/clean up content (use /content-enhancer).
disable-model-invocation: true
allowed-tools: Bash Read Agent WebSearch WebFetch
---

## Runtime Context

After the skill loads, establish the project root and branch with ordinary
read-only calls. `INFLUENCES.md` at the repo root is the attribution SSOT;
verdicts are proposed for it and applied with any influenced method.

## Instructions

You are reviewing an **external source** against ai-governance. The discriminating move is **intent-abstraction**: a surface item (a named principle/method/tool) can look novel while its *intent* is already covered, or look familiar while its intent is genuinely new. **Intent is the unit of comparison.** Read `procedure.md` in this skill folder for the full 6-phase protocol; this is the orchestration shell.

This skill **proposes, it does not write** — it has no Edit/Write tool. It returns a verdict report; the human applies the approved rows/items (per the INFLUENCES.md same-commit discipline).

### Quick Start

1. **Collect the Runtime Context above and acquire the source.** Accept whichever the user provides: pasted text, a local file path (`Read`), a URL (`WebFetch`), or a topic to find first (`WebSearch` → `WebFetch`). If ambiguous, ask. For a long, local, or multi-page source, **filter before you read**: save or pipe the raw text and run `python scripts/semantic_rank.py --raw --query "<review question>" --stats < source.md`, then read only the top-ranked passages — do NOT ingest the full source into context first (the semantic filter runs *before* the content reaches you).

2. **Read `procedure.md`** for the full protocol, then run all six phases in order:
   - **(0) Govern** — `evaluate_governance(planned_action="review external source against governance")`.
   - **(1) Ingest** — load the source text.
   - **(2) Extract (face value)** — enumerate the discrete items (principles / methods / tools / claims); state "*N items identified*" (per rules-of-procedure §9.8.5 enumeration-verification).
   - **(3) Abstract-to-intent** — for each item write the *intent*: the failure-mode/goal above the surface (per `meta-core-systemic-thinking` + Intent Discovery). This is the crux.
   - **(4) Coverage-check the intent** — `query_governance` + `search_references` + `query_project` for each intent; apply the §9.8.2 Duplication Check.
   - **(5) Classify + gate the "new"** — map each intent to one of the four INFLUENCES categories or "genuinely new." For every "genuinely new" candidate, run the **§9.8.1 Admission Test (7 Qs)** and dispatch a **`contrarian-reviewer`** pass to guard against intellectual-generosity bias (LEARNING-LOG 2026-02-28).
   - **(6) Propose** — emit the verdict report; route each verdict per INFLUENCES.md "How to extend." Do not write.

### Key Principles

- **Intent is the unit, not the surface item.** Always evaluate the abstracted intent against coverage; the surface item is only evidence.
- **Gap analysis, not coverage analysis.** The frame is "what can we learn / what's new?" — not "do we already have this?" Coverage overlap ≠ zero value (`external-input-gap-analysis`).
- **Guard intellectual-generosity bias.** The desire to find value in external work biases toward false inclusion. Every "genuinely new" verdict must survive the §9.8.1 Admission Test *and* a contrarian pass.
- **Propose, never write.** The skill returns proposals; the human applies them — and an INFLUENCES.md row ships in the same commit as the method it influences.
- **Reuse, don't re-derive.** Coverage uses the existing retrieval tools; the new-principle decision uses the existing §9.8.1 Admission Test.
- **Gate the Adopt path too, not only "genuinely new."** Adopting an external surface *as-is* imports its form wholesale — before Adopt, run a source-quality check: best-in-class (is this the strongest exemplar, or just the one presented? `title-10 §3.1.4`) + currency (superseded in a fast-moving domain? constitution "Stale Record"). Intent-coverage answers "do we have it"; it does not answer "is this the *best* version of it, and is it *still true*."

### What This Skill Does NOT Do

- **Review our own code/branch** — use `/code-review`.
- **Rewrite or clean up the source into a reference doc** — use `/content-enhancer`.
- **Write to INFLUENCES.md / BACKLOG / the Reference Library** — it proposes; the human (or a follow-up commit) applies.
- **Admit a principle on its own authority** — it runs the §9.8.1 gate and a contrarian pass, then proposes.
