---
id: ref-ai-coding-re-evaluation-protocol-case-study
title: "Re-evaluation Protocol Applied: Breaking Anchor Bias at Velocity Inflection"
domain: ai-coding
tags: ["decision-making", "anchor-bias", "velocity", "governance", "re-evaluation", "planning"]
status: current
entry_type: direct
summary: "Case study of applying the Re-evaluation Protocol (4 steps) at Week 16+ to break anchor bias toward custom-built UI — includes calibration questions, mode selection, lifecycle classification, and velocity dissipation check"
created: 2026-05-14
last_verified: 2026-05-14
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when a project reaches a velocity inflection point and the current approach may no longer be optimal. The Re-evaluation Protocol is especially valuable when the team has significant sunk cost in the current approach, creating anchor bias. Applied alongside 7 other ai-coding planning methods to provide comprehensive governance coverage for a mid-project architectural pivot.

## Artifact

## Re-evaluation Protocol (4 Steps)

### Step 1: Reframe
Strip away sunk cost. Ask: "If we were starting today with what we know now, would we build it this way?"

**Applied:** 16 weeks into ai-expert project, custom chat UI (message rendering, auto-scroll, code highlighting) was consuming cycles while RAG, governance, and billing waited. Reframing revealed: the custom UI work was commodity, not differentiation.

### Step 2: Generate Alternatives (≥3)
Force at least 3 structurally different options. Don't allow "current approach with tweaks" to count.

**Applied:**
- Option A: Continue fully custom (status quo)
- Option B: Fork an open-source platform (LibreChat, Open WebUI, etc.)
- Option C: Hybrid — keep custom backend, adopt component library for UI

### Step 3: Challenge (Contrarian Review)
Use a contrarian reviewer to attack each option's assumptions.

**Applied:** Contrarian reviewer found:
- Option A anchor bias: "we've already built X" is sunk cost reasoning
- Option B structural issues: no platform supports multi-tenant RLS
- Option C risks: shiki bundle size, missing server actions, old message rendering delta

### Step 4: Evaluate (Structured Scoring)
Use Elegance Equation (Effectiveness × Efficiency) — multiplicative to penalize imbalance.

**Applied:** Custom=45, Fork=15, Hybrid=72. Hybrid wins structurally.

## Companion Methods Applied

| Method | Purpose | Result |
|--------|---------|--------|
| Calibration Questions (4) | Reconfirm project parameters | No change post-pivot |
| Mode Selection Matrix | Assign governance mode per work category | STANDARD overall, ENHANCED for spike |
| Lifecycle Classification | Set quality gates | Spike=PROTOTYPE, Integration=PRODUCTION |
| Context Drift Detection | Find stale documentation | 6 of 7 docs had drift → remediated |
| Velocity Dissipation | Check project lifecycle window | Week 16+ = architecture reset window |
| Requirements Reconfirmation | Validate core requirements still hold | All 10 valid, 1 gap identified |
| Three-Subagent Review | Independent validation | Code + Contrarian + Security auditors |

## When to Trigger Re-evaluation

- Week 7+ of project (velocity dissipation model)
- >30% of sprint work is commodity (not differentiation)
- Team finds themselves "maintaining" instead of "building"
- New tools/libraries emerge that cover current custom work
- Scope change that invalidates prior assumptions

## Anti-Pattern: Partial Re-evaluation

Don't just evaluate the new option — re-evaluate ALL options including the current one. The current approach gets an unfair advantage from familiarity bias if you only scrutinize the alternatives.

## Lessons Learned

1. The 4-step protocol works but requires discipline — Step 1 (Reframe) is the hardest because it requires admitting sunk cost. 2. Generating 3+ alternatives prevents binary thinking (keep vs switch) which misses hybrid options. 3. Contrarian review found actionable issues in the winning option (shiki, missing actions, rendering delta) — it's not just for rejecting ideas. 4. The velocity dissipation model correctly predicted Week 16+ as an architecture reset window. 5. Context drift detection found 6/7 documents were stale after the pivot decision — documentation must be updated before code changes. 6. Requirements reconfirmation revealed a gap (source citations now depend on streamdown) that would have been discovered late otherwise.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
