---
id: ref-ai-coding-autoresearch-pattern
title: "Karpathy's Autoresearch: Autonomous Agent Experimentation Pattern"
domain: ai-coding
tags: [autonomous-operation, experimentation, overnight-agents, program-md, research-protocol]
status: current
entry_type: reference
summary: "Pattern for AI agents running autonomous modify-test-evaluate-decide loops overnight, using a research protocol document"
created: 2026-03-26
last_verified: 2026-03-26
maturity: evergreen
decay_class: evergreen
source: "Analysis of Karpathy's autoresearch project (57K+ stars)"
external_url: "https://github.com/karpathy/autoresearch"
external_author: "Andrej Karpathy"
accessed_date: 2026-03-26
related: [ref-ai-coding-willison-hoard-pattern]
---

## Context

Andrej Karpathy's "autoresearch" demonstrates a powerful pattern: give an AI agent a constrained optimization problem with a measurable metric, and let it run experiments autonomously overnight. The agent modifies code, trains for exactly 5 minutes, evaluates the result, keeps improvements, discards failures, and repeats — producing ~100 experiments by morning.

The key innovation is NOT the ML training — it's the **workflow pattern** of human-as-architect, agent-as-executor with structured protocols.

## Artifact

**The pattern has four components:**

1. **program.md** — A research protocol document that defines objective, scope constraints, evaluation metric, time budget, keep/discard criteria, and termination conditions. The human writes this; the agent follows it.

2. **Permission configuration** — Pre-approved tool access matching the protocol's scope. Surgical allowlists (recommended) grant exactly what the agent needs.

3. **The experimentation loop** — modify → commit → run → evaluate → keep/discard → log → repeat. Git provides reversibility; the results log provides the audit trail.

4. **Termination conditions** — Maximum runtime, consecutive failure limits, metric degradation thresholds. The "NEVER STOP" directive must always be paired with circuit breakers.

**Karpathy's specific constraints that make this work:**
- Single editable file (`train.py`) — tight scope constraint
- Fixed 5-minute time budget — experiments are comparable
- Single metric (`val_bpb`) — unambiguous success criterion
- Git branch per run — complete reversibility
- `results.tsv` — structured audit trail

## Lessons Learned

- The research protocol (program.md) is the critical artifact — it defines the agent's entire operating space. A vague protocol produces vague results.
- Scope constraints must be explicit and narrow. "Only modify train.py" is clear. "Improve the model" is not.
- A single measurable metric eliminates subjective judgment from the loop. Multi-metric optimization requires human guidance at decision points.
- Conservative time budgets enable more experiments. 5 minutes × 12/hour × 8 hours = ~100 experiments overnight.
- The pattern generalizes beyond ML: any domain with measurable outcomes, constrained scope, and reversible experiments (test suites, performance benchmarks, configuration optimization).

## Cross-References

- Principles: multi-autonomous-action-blast-radius-classification (AO-1), multi-autonomous-hitl-removal-criteria (AO-2), multi-autonomous-compensating-controls-for-autonomous-operation (AO-3)
- Methods: multi-agent §6.5 (Autonomous Experimentation Protocol)
- See also: ref-ai-coding-willison-hoard-pattern
