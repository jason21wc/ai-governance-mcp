---
description: Assess a codebase or module's structural organization and health. Maps entry points, module responsibilities, dependency directions, and layering patterns, then evaluates coupling hotspots, cohesion gaps, and growth capacity. Invoke when the user says "architecture review", "architecture overview", "assess the architecture", "how is this codebase organized", "structural health", "module structure", or "dependency map". Do NOT use for diff-based code review (use /code-review), refactoring readiness (use /refactor-audit), test generation (use /test-suite), or security auditing (use /security-scan).
disable-model-invocation: false  # read-only (Bash Read Grep); model-invocable per §9.5.3 per-skill flip, Compliance Review #14 (2026-07-01)
allowed-tools: Bash Read Grep
---

## Runtime Context

After the skill loads, inspect the project root, top-level structure, representative
file types, file count, and framework manifests with ordinary read-only calls.
Derive the framework from the evidence; do not rely on eager injected output.

## Instructions

You are performing a codebase architecture review. This skill answers: **"How is this codebase organized, and is the architecture healthy?"**

Read `procedure.md` in this skill folder for the full 3-phase protocol.

### Quick Start

1. **Collect the Runtime Context above and determine the scope.** If the user specified a module or subsystem, focus there. If they said "review the architecture" without qualification, assess the entire codebase. If the codebase is very large (>500 files), recommend scoping to a subsystem.

2. **Read `procedure.md`** for the full protocol.

3. **Execute all three phases in order:**
   - **Phase 1: Map** — module structure, entry points, dependency graph, layer identification
   - **Phase 2: Assess** — layering integrity, cohesion, coupling hotspots, anti-patterns, growth capacity
   - **Phase 3: Report** — structural map + health assessment + prioritized recommendations

4. **Deliver the report** with the structural map, health findings, and refactoring priorities.

### Key Principles

- **The structural map is the core deliverable.** A dependency graph and module responsibility inventory that the user can reference for future decisions. Findings without the map are opinions; the map with findings is actionable intelligence.
- **Tool-assisted mapping over manual reading.** Use grep and import analysis to build the dependency graph. Manual code reading fills gaps but the skeleton comes from tooling.
- **Honest about scope limitations.** Grep finds imports and call sites, not runtime behavior. Dynamic dispatch, dependency injection, and event-driven patterns create invisible dependencies. Flag these as UNVERIFIED, same as `/refactor-audit` does for invisible contracts.
- **Assessment, not prescription.** Report what IS, evaluate its health, prioritize what to improve. Don't redesign the architecture — that's the user's job with this assessment as input.

### Skill Composition

*(Portability: slash-command references name companion skills; on hosts where one isn't installed, perform the equivalent manually.)*

This skill creates a progression with other skills:
- `/architecture-review` → "How is it organized? Where are the problems?" (this skill)
- `/refactor-audit` → "Is it safe to change module X?" (readiness assessment)
- Refactor the code (normal coding)
- `/code-review` → "Did the refactoring maintain correctness?" (diff review)

### What This Skill Does NOT Do

- **Diff-based review** — it assesses structure, not recent changes. Use `/code-review` for that.
- **Refactoring readiness** — it identifies what SHOULD change, not whether it's SAFE to change. Use `/refactor-audit` for that.
- **Generate tests** — use `/test-suite`.
- **Security auditing** — use `/security-scan`.
- **Redesign the architecture** — it diagnoses; the user and their team design.
