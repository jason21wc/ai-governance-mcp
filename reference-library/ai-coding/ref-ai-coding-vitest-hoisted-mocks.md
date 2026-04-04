---
id: ref-ai-coding-vitest-hoisted-mocks
title: "Vitest vi.hoisted() for Mock Variables in vi.mock() Factories"
domain: ai-coding
tags: ["vitest", "testing", "mocking", "typescript", "vi-mock"]
status: current
entry_type: direct
summary: "Vitest vi.mock() factories are hoisted above imports — variables referenced inside must use vi.hoisted() or they will be undefined"
created: 2026-04-01
last_verified: 2026-04-01
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
related: [ref-ai-coding-pytest-fixture-patterns]
---

## Context

Vitest hoists vi.mock() to top of file before imports. Variables in normal scope are undefined when factory runs. vi.hoisted() creates co-hoisted variables. Proven in ai-expert (L045, 104 tests).

## Artifact

const { mockSupabase } = vi.hoisted(() => ({
  mockSupabase: {
    auth: { getUser: vi.fn(), getSession: vi.fn() },
    from: vi.fn(),
  },
}))

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(() => Promise.resolve(mockSupabase)),
}))

beforeEach(() => { vi.clearAllMocks() })

## Lessons Learned

- vi.mock() is hoisted above all imports — by design, same as Jest
- ALL mock variables inside vi.mock() must use vi.hoisted()
- "Cannot read properties of undefined" inside vi.mock() is almost always this

## Do / Don't

**Do:** Use `vi.hoisted()` for all mock variables referenced inside `vi.mock()` factories. This co-hoists the variables with the mock declaration so they're defined when the factory runs.

**Don't:** Declare mock variables in normal module scope and reference them inside `vi.mock()` factories — they will be `undefined` because `vi.mock()` is hoisted above all imports and variable declarations. The error "Cannot read properties of undefined" inside `vi.mock()` is almost always this.

## Cross-References

- Principles: coding-quality-testing-integration
- Methods: §5.2 (Testing Integration)
- See also: ref-ai-coding-pytest-fixture-patterns
