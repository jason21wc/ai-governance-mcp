---
id: ref-ai-coding-anthropic-skill-tool-investment
title: "Anthropic Engineering Video — Tool Investment Anti-Pattern"
domain: ai-coding
tags: ["skills", "skill-authoring", "tool-quality", "deterministic-scripts", "composability"]
status: current
entry_type: reference
summary: "Gap analysis of Anthropic engineering practices video on Claude Code skills. Key insight: 'instruction-heavy, tool-light' anti-pattern — people write detailed prompts but give bare-bones tools. One gap incorporated into §9.5.3."
created: 2026-05-17
last_verified: 2026-05-17
maturity: seedling
decay_class: framework
source: "YouTube video — Anthropic AI Code Summit engineering practices"
external_url: "https://www.youtube.com/watch?v=qOvc9IUKEIc"
external_author: "AI Code Summit presenter (referencing Anthropic engineers Barry and Eric)"
accessed_date: 2026-05-17
---

## Context

Use when authoring new skills, reviewing tool quality in existing skills, or evaluating whether a skill should embed deterministic scripts. Complements ref-ai-coding-skill-authoring-tips (writing quality and lifecycle) and ref-ai-coding-superpowers-skills-framework (structural patterns). This reference covers the tools layer — the third layer of skill anatomy that most people skip.

## Artifact

### Gap Incorporated into §9.5.3

**Tool investment — tools over instructions (§9.5.3):**
The video's sharpest insight comes from Anthropic engineer Eric: people put effort into "beautiful, detailed prompts" but give the model "incredibly bare-bones" tools — undocumented, with parameters named "A" and "B," unusable by a human engineer. Anthropic engineers do the opposite: they focus on tool quality. Incorporated as the "instruction-heavy, tool-light" anti-pattern with contrastive before/after examples in §9.5.3 Skill Authoring Standards (CFR v2.47.0).

### Two Additional Insights (Already Covered)

**Deterministic script reuse:**
Save scripts inside skills so Claude runs rather than regenerates each session. The video describes a slide-styling Python script that Claude kept rewriting — saving it in the skill folder made output consistent and cheaper. The general principle ("trade AI tokens for code compute") is expressed domain-specifically in accounting §7.4 (Deterministic Compute Pattern) and multi-agent §4.6.3 (deterministic enforcement). The §9.5.3 tool investment block references this pattern with the §9.5.4 "Goal over path" reconciliation.

**Composability over monolithic skills:**
Split large skills into focused, reusable units that chain together. Three reasons: issues easier to isolate, improvements compound across workflows, reuse replaces rebuilding. Already covered by §9.5 four-layer execution taxonomy, §9.5.5 "When to Codify" decision tree, and ref-ai-coding-superpowers-skills-framework lesson 2 ("Skills that try to do too much should be split").

## Already Covered (3 of 4 rules)

| Video Rule | Framework Coverage |
|------------|-------------------|
| Rule 1: Prompt skills, not Claude | §9.5 four-layer execution taxonomy; EXECUTION-FRAMEWORK.md §3.7 |
| Rule 3: Build composable, not custom | §9.5.5 "When to Codify"; ref-ai-coding-superpowers-skills-framework lesson 2 |
| Rule 4: Prompts get smarter every session | LEARNING-LOG + C-155 feedback loop + C-078 compliance review cadence |

Also covered: `disable_model_invocation` and `user_invocable` flags (§9.5.3 SKILL.md structure), description quality as routing (§9.5.3 "routing, not summary"), progressive disclosure (§9.5.3 three-level table).

## Subagent Review Findings

Contrarian-reviewer (plan-mode): Two verdict-changing findings absorbed — (1) match specificity bar of adjacent §9.5.3 blocks with concrete before/after examples, not just anti-pattern naming; (2) drop cross-references to accounting §7.4 and multi-agent §4.6.3 (thematically adjacent but operationally disconnected — linking them applies a cross-domain meta-principle through the back door when it was explicitly scoped out). Also flagged §9.5.4 "Goal over path" tension — reconciliation sentence added.

## Lessons Learned

The gap analysis process itself validated the behavioral floor directive "external input — gap analysis, not coverage analysis." Initial instinct was to map transcript rules to existing coverage and declare "mostly covered." The gap analysis frame ("what's new?") surfaced the genuine tool-quality gap that a coverage frame would have dismissed. Three of four rules mapped cleanly to existing coverage; the one that didn't produced an actionable method improvement.

## Cross-References

- Methods: §9.5.3 Skill Authoring Standards (tool investment block, CFR v2.47.0)
- See also: ref-ai-coding-skill-authoring-tips (writing quality), ref-ai-coding-superpowers-skills-framework (structural patterns)
