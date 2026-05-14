---
id: ref-ai-coding-hybrid-ui-architecture-decision
title: "Hybrid UI Architecture: When to Adopt Components vs Build Custom"
domain: ai-coding
tags: ["architecture", "build-vs-buy", "decision-framework", "velocity", "component-libraries", "saas"]
status: current
entry_type: direct
summary: "Decision framework for hybrid UI architecture — keep custom backend + adopt open-source UI components. Applied at Week 16+ velocity inflection in ai-expert project. Includes evaluation criteria, platform comparison, and structural reasoning."
created: 2026-05-14
last_verified: 2026-05-14
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when a project reaches a velocity inflection point where commodity UI work is blocking differentiated features. The hybrid pattern works when: (1) the backend has unique requirements that no off-the-shelf solution provides (multi-tenant RLS, custom auth, domain-specific pipeline), (2) the frontend has commodity components available (chat rendering, code highlighting, markdown), (3) the component library shares the same framework/stack (shadcn/ui compatibility). This pattern does NOT work when the frontend IS the differentiation (design-heavy products, novel interaction patterns).

## Artifact

## Decision Framework

### When Hybrid UI Makes Sense

| Signal | Threshold |
|--------|-----------|
| Project age | Week 7+ (velocity dissipation window) |
| Custom backend requirements | ≥3 features no platform provides |
| UI commodity ratio | >50% of remaining UI work is "standard chat UX" |
| Component library compatibility | Same framework + design system |
| License | Apache 2.0, MIT, or BSD (SaaS-compatible) |

### Evaluation Method (Applied)

1. **Re-evaluation Protocol** — Reframe (break anchor bias), Generate alternatives (≥3), Challenge (contrarian review), Evaluate (structured scoring)
2. **Elegance Equation** — Score = Effectiveness (0-10) × Efficiency (0-10). Multiplicative, not additive — a 9×3=27 loses to a 7×7=49. Penalizes imbalanced solutions.
3. **Three-subagent review** — Code reviewer (integration feasibility), Contrarian reviewer (challenge assumptions), Security auditor (supply chain + XSS surface)

### Platform Comparison (AI Chat SaaS, 2026-05)

| Platform | License | Backend | Multi-Tenant RLS | Verdict |
|----------|---------|---------|-------------------|---------|
| Open WebUI | Custom (restrictive) | Python | No | Rejected: license, wrong stack |
| LibreChat | MIT | Node.js + MongoDB | No | Rejected: MongoDB, no RLS |
| LobeChat | Restrictive for SaaS | Next.js | No | Rejected: license |
| AnythingLLM | MIT | Node.js | No | Rejected: no multi-tenancy |
| Chatbot UI | MIT | Next.js + Supabase | Partial | Rejected: stalled, no governance |
| Onyx | Apache 2.0 | Python | No | Rejected: search-first, wrong paradigm |
| Tiledesk | MIT | Node.js | Partial | Rejected: support-focused, not expert chat |

**Conclusion:** No open-source platform supports multi-tenant RLS + 3-layer expert system + governance gateway. Custom backend is structurally required. UI is where commodity components add value.

### Component Library Comparison

| Library | License | Pattern | Integration Friction |
|---------|---------|---------|---------------------|
| AI Elements | Apache 2.0 | shadcn/ui registry (source copy) | Zero (same team as AI SDK) |
| assistant-ui | MIT | Headless primitives + runtime | Low (but adds abstraction layer) |
| react-markdown | MIT | Component library | Medium (doesn't handle streaming well) |

### Scoring (Elegance Equation)

| Option | Effectiveness | Efficiency | Score |
|--------|--------------|------------|-------|
| Fully Custom | 8 | 3 | 45 (high capability, slow velocity) |
| Platform Fork | 3 | 5 | 15 (low fit, moderate speed) |
| Hybrid (AI Elements) | 8 | 9 | 72 (high fit, high speed) |

## Key Structural Insight

"The real question is not whether custom is better, but whether the delta justifies the velocity cost." Custom UI scores higher on theoretical effectiveness (10 vs 8) but the 2-point delta doesn't justify 3x the implementation time. The hybrid approach reaches "good enough" UI quality while freeing velocity for the features that actually differentiate the product.

## Lessons Learned

1. Anchor bias toward sunk cost is the #1 risk at velocity inflection points — the Re-evaluation Protocol breaks it by forcing structured alternatives. 2. No open-source AI chat platform (as of 2026-05) supports multi-tenant RLS — if you need database-enforced isolation, the backend must be custom. 3. The shadcn/ui registry pattern (source copy) eliminates the dependency management tradeoff — you get the code without the update risk. 4. Contrarian review was essential — it surfaced real issues (shiki bundle size, missing server actions, old message rendering delta) that pure analysis missed. 5. The Elegance Equation's multiplicative property correctly penalized the "very effective but slow" custom approach — additive scoring would have obscured this.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
