---
id: ref-ai-coding-prompt-quality-patterns
title: "Prompt Quality Patterns — Gap Analysis of 40-Prompt Collection"
domain: ai-coding
tags: ["prompt-engineering", "patterns", "variant-generation", "negative-few-shot", "self-challenge", "quality-techniques", "prompt-master"]
status: current
entry_type: reference
summary: "Gap analysis of a 40-prompt collection identified 3 meta-techniques implicit in Prompt Master but not explicitly named: variant generation, negative few-shot (grounded constraints), and self-challenge framing. Added as patterns 38-40."
created: 2026-05-15
last_verified: 2026-05-15
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Source article presented 40 domain-specific prompts (writing, analysis, technical, productivity, communication). Structural analysis per meta-core-systemic-thinking revealed the prompts work because they fill specification completeness gaps — role, audience, task, format, quality criteria, constraints. Prompt Master's 9-dimension intent extraction already captures this structurally. The three genuinely new insights were meta-techniques that enhance output quality beyond specification completeness.

## Artifact

## Three Quality Patterns Extracted

**Pattern 38 — Variant Generation (general technique):**
Request 2-3 output versions with different parameters (tone, energy level, approach). Not just for creative work — applies to emails, pitches, apologies, analysis. Forces the model to explore more of the output space, gives comparison material, reduces anchoring bias. Previously captured only in CRISPE template's Experiment field (creative-only framing).

**Pattern 39 — Negative Few-Shot (grounded constraints):**
When stating negative constraints, include 2-3 specific examples of what to avoid. "No filler phrases ('it is important to note', 'in today's world')" is strictly stronger than "no filler phrases" — the examples transform a vague style rule into a concrete pattern match. Complements Template F (positive few-shot) with the negative counterpart.

**Pattern 40 — Self-Challenge Framing (analysis prompts):**
For diagnosis and analysis tasks, instruct the model to question the user's framing: "Do NOT accept my initial framing at face value. The real problem is often not the one I described." Applies meta-core-systemic-thinking (root cause over symptoms) as a user-facing prompt technique. Users naturally describe symptoms; this instruction activates the model's reframing capability.

## Lessons Learned

The 40 prompts are well-constructed instances of patterns Prompt Master already captures (specification completeness, role assignment, structured output, audience specification). The value was not in the prompts themselves but in three meta-techniques that were implicit in the infrastructure but not explicitly named. Gap analysis (per external-input-gap-analysis behavioral floor) was the right frame — coverage analysis would have dismissed the article as "already covered."

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
