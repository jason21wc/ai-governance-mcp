# [Task Name]

## Context
[Why this change is needed — problem, trigger, intended outcome]

## Contrarian Review Output
[REQUIRED GATE — DO NOT populate "Recommended Approach" until this section has content
from an actual contrarian-reviewer subagent invocation. This is not a placeholder to fill
in later. Run the subagent NOW, before writing the approach.]

Key challenges raised and how each was addressed or accepted:
- Challenge 1: [challenge] → [resolution]
- Challenge 2: [challenge] → [resolution]
- If no challenges raised: document why the approach is straightforward enough that no fundamental issues exist.

## Research Verification
[If the approach introduces an algorithm, model, library, or architectural pattern not previously
used in this project: what was researched, what was found, how it informed the approach.
Write "N/A — no novel elements, using established project patterns" if not applicable.]

## Simpler Alternatives Evaluated
[What simpler approaches were considered and why the proposed approach was chosen over them.
"None evaluated" is a signal to pause and evaluate before proceeding.]

## Recommended Approach
[The implementation plan — populated AFTER the above sections contain content]

## Verification
[How to test the changes end-to-end]

## Files Modified
[List of files to create/modify]

## Plain-English Summary

[REQUIRED — one of the last sections populated. This is the human's entry point for approval.
Write for someone who wants to approve the right thing without parsing the technical detail
above. Every plan gets this section; "small" plans get shorter summaries, not omitted ones.]

- **What's changing (plain verbs, no jargon):** 1-2 short paragraphs. No principle IDs,
  pattern names, or file-path manifests — those live in sections above.
- **What you're being asked to approve:** the one material decision, stated as a yes/no
  question or a recommendation the user can accept or redirect.
- **Trade-off in one sentence:** why this approach over the simpler/smaller alternative
  (or why we're doing it at all rather than deferring).
- **What I'm deliberately NOT doing:** explicit non-goals — anything a reader might expect
  that's out of scope, with a brief reason (usually proportional rigor, or deferred to
  another backlog item).
- **What you should know before approving:** honest limitations, scope-reality-check,
  blast-radius note if relevant.

Rationale: plans written in plan mode optimize for AI execution (principle IDs, pattern
refs, file manifests). Dense for human review. Plain-English summary lets the user engage
with material choices without wading through execution detail. Placement at end so AI
execution context reads top-to-bottom; human scrolls to the summary for the decision.
