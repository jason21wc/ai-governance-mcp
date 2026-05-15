---
id: ref-ai-coding-skill-authoring-tips
title: "8 Tips for Writing Agent Skills — Gap Analysis"
domain: ai-coding
tags: ["skills", "skill-authoring", "claude-code", "progressive-disclosure", "constraint-retirement", "capability-vs-preference", "directive-style"]
status: current
entry_type: reference
summary: "Gap analysis of 8-tip skill authoring article. 5 of 8 tips already covered by §9.5. Three gaps incorporated: directive writing style, goal-over-path clarification, and skill retirement with capability/preference distinction."
created: 2026-05-15
last_verified: 2026-05-15
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when authoring new skills, reviewing existing skills for retirement candidates, or evaluating skill instruction quality. Complements the Superpowers reference (ref-ai-coding-superpowers-skills-framework) which covers structural patterns. This reference covers writing quality and lifecycle.

## Artifact

## Three Gaps Incorporated into §9.5

**1. Directive writing style (§9.5.3):**
Write actionable directives, not informational prose. `"Always use interactions.create()"` is an instruction the agent follows; `"The Interactions API is the recommended approach"` is trivia it ignores. Lead with code examples over explanations. Explain WHY when rules are non-obvious — the reason helps the agent generalize.

**2. Goal over path (§9.5.4 annotation):**
"Repeatable steps" (property 2) means the outcome and constraints are consistent — not that the skill must dictate every step. Define what to achieve, let the agent choose the approach. If step ordering is the only source of complexity, write a shell script, not a skill.

**3. Skill retirement (§9.5.5):**
Two skill categories with different lifecycles:
- *Capability skills* fill a gap the base model can't handle. These have a shelf life — as models improve, the gap closes. Test: run evals without the skill; if outcomes are equivalent, retire it.
- *Preference skills* encode your specific workflow. These are durable but must stay in sync with your actual process.

Retirement reviews complement Check 12 (constraint retirement for enforcement-layer components) during compliance reviews (C-078).

## Already Covered (5 of 8 tips)

| Tip | Coverage |
|-----|----------|
| Know What a Skill Is (folder structure) | §9.5.6 |
| Nail the Description (trigger quality) | §9.5.3 "routing, not summary" |
| Keep It Lean (progressive disclosure) | §9.5.3 progressive disclosure table, token budgets |
| Don't Skip Negative Cases (negative triggers) | Added as one-liner to §9.5.3 description guidance |
| Test Before Shipping (eval methodology) | Partially covered by §9.5.4 five properties; article's multi-trial eval methodology not incorporated (deferred — no observed need) |

## Subagent Review Findings

Contrarian-reviewer: flagged property 2 rename as citation integrity risk (Wang 2026 attribution). Resolved by keeping original property name and adding annotation below. Also caught Check 12 scope mismatch (Layer 1 enforcement, not Layer 2 skills). Resolved by softening cross-reference to C-078 cadence.

Coherence-auditor: confirmed no cross-file contradictions. Flagged index staleness (re-index required) and bold triggers update (applied).

## Lessons Learned

The contrarian review caught a subtle but real problem: renaming an attributed property (Wang 2026) silently mutates what the framework claims the source said. The fix — annotation rather than rename — preserves attribution while delivering the same actionable guidance. This pattern (annotate vs. rename) is worth remembering when modifying attributed content.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
