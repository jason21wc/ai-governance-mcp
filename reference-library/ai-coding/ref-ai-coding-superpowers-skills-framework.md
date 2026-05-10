---
id: ref-ai-coding-superpowers-skills-framework
title: "Superpowers v5.1.0 — Skills Framework for Claude Code"
domain: ai-coding
tags: ["skills", "claude-code", "superpowers", "procedural-knowledge", "workflow", "slash-commands"]
status: current
entry_type: reference
summary: "Skills framework patterns from Superpowers (obra/superpowers) — 14 skills across 4 categories demonstrating skill authoring best practices, progressive disclosure, and mandatory workflow enforcement"
created: 2026-05-10
last_verified: 2026-05-10
maturity: budding
decay_class: framework
source: "github.com/obra/superpowers — Jesse Vincent"
---

## Context

Use when authoring new skills, evaluating skill design, or deciding whether a repeatable process should become a skill. Superpowers is the reference implementation for Claude Code skills — it demonstrates patterns this project's CFR §9.5 codifies as standards.

## Artifact

### Superpowers v5.1.0 — Key Patterns

**Repository:** github.com/obra/superpowers
**Skills:** 14 across 4 categories (Testing, Debugging, Collaboration, Meta)
**Platform:** Claude Code SKILL.md standard

### Design Principles

1. **"No skill without a failing test first"** — watch the agent fail without the skill before writing one. Prevents speculative skills that add overhead without demonstrated value.

2. **Description is routing, not summary** — the description field drives auto-invocation. Write triggering conditions only. Workflow summaries cause agents to shortcut past full instructions ("Claude Search Optimization" — the agent reads the summary and skips the detailed steps).

3. **Skills are mandatory workflows, not suggestions** — once codified, the skill defines *the* way to perform the task. Deviation requires explicit override, not casual ignoring.

4. **Multi-host support** — skills work across Claude Code CLI, desktop app, and web. Design for the minimal common surface.

### Category Inventory (v5.1.0)

| Category | Skills | Purpose |
|----------|--------|---------|
| Testing | writing-tests, debugging-test-failures | TDD workflow, test failure investigation |
| Debugging | ultrathink, investigating-bugs | Deep reasoning, systematic bug investigation |
| Collaboration | writing-plans, finishing-a-development-branch, git-rewrite-history, summarize-changes | Planning, branch management, history cleanup |
| Meta | self-improvement, review-skills | Skill quality assurance |

### Authoring Patterns Observed

- **Thin SKILL.md + reference files** — orchestration shell in SKILL.md, detailed procedures in supporting files
- **Dynamic context injection** — `!`git diff``, `!`git status``, `!`date`` for real-time state
- **Progressive disclosure** — metadata at startup (Level 1), full SKILL.md on activation (Level 2), reference files on demand (Level 3)
- **Self-improvement skill** — a meta-skill that lets the agent propose improvements to its own skills (with human approval gate)

## Lessons Learned

1. Description quality determines invocation reliability. Vague descriptions ("helps with testing") cause false negatives (skill not triggered). Overly broad descriptions cause false positives (wrong skill triggered). 2. Skills that try to do too much ("and also") should be split. The "and also" signal is the strongest indicator of a skill that needs decomposition. 3. The `disable-model-invocation: true` flag is safer for complex procedures — forces explicit user invocation rather than relying on auto-routing. 4. Skill compaction (5,000 tokens/skill, 25,000 combined) means SKILL.md body must be lean. Procedure detail belongs in reference files.

## Cross-References

- Principles: `coding-quality-workflow-integrity`, `meta-governance-continuous-learning-adaptation`
- Methods: CFR §9.5 (Skills & Execution Layer), EXECUTION-FRAMEWORK.md §3.7 (Decision Matrix)
- See also: Wang 2026 ("Why do AI agents still need so much hand-holding?" — procedural knowledge taxonomy)
