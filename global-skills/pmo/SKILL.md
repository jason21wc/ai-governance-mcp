---
description: Apply the Purpose-Method-Outcomes (PMO) lens to a project that turns inputs into outputs — either BUILD a project's PMO charter (who it serves, the mechanisms that deliver value, the artifacts + how you verify the purpose was actually delivered) or REVIEW an existing project against that lens (trace purpose↔method↔outcome, run the audit checklist, classify gaps, propose fixes read-only). Invoke when the user says "PMO", "purpose method outcomes", "PMO charter", "PMO review", "write a project charter", "does this project actually deliver its purpose", "is anything here waste", "trace purpose to outcome", or "audit this project/library/tool against its purpose". Do NOT use for diff-based code review (use /code-review), codebase structure (use /architecture-review), refactoring safety (use /refactor-audit), or reviewing an external article/tool against governance (use /source-review).
disable-model-invocation: true  # user-only: charter mode WRITES a charter (side effect) and both modes are judgment-bearing; invoke explicitly per §9.5.3. Write is justified (charter mode is the build action), not a least-privilege defect.
allowed-tools: Bash Read Write Grep
---

## Runtime Context

After the skill loads, inspect the project root, top-level structure, and likely
charter locations with ordinary read-only calls. No charter found is a valid
result; distinguish it from paths that could not be inspected.

## Instructions

This skill applies ONE lens — **Purpose · Method · Outcomes** — in one of two directions. It is the canonical home of that lens; a project's own filled-in charter lives in that project and points here for the method.

Every project that turns inputs into outputs has three latent layers:
- **PURPOSE** — who receives value, and why this beats their best alternative.
- **METHOD** — the mechanisms that produce the value (rules, pipelines, schemas, data sources, adjustments).
- **OUTCOMES** — the deliverable as its audience experiences it, **plus how you know the purpose was actually delivered** (the closed loop most frameworks omit).

Read `procedure.md` in this skill folder for the full protocol before running either mode.

### Quick Start

1. **Collect the Runtime Context above and determine the mode + target.**
   - If the user said "charter" / "write a charter" / "capture this project's purpose" → **charter mode** (build). (For standing up a brand-new project from scratch, that's `/start-project`, not this.)
   - If the user said "review" / "audit" / "does this deliver its purpose" → **review mode**.
   - If they said "PMO" with no direction, ask which. If they named a project/path, use it; else use the current project.
2. **Read `procedure.md`** for the mode's phases.
3. **Run the mode's phases in order** (both start with a governance check).
4. **Deliver** — a charter (charter mode) or a findings report (review mode).

### The two modes

- **Charter (build)** — extract the project's Purpose, Method map, and Outcomes from what already exists, then write a ≤12-line charter block (template in `procedure.md`) into the project. Pointers to method docs, never restatements; a "verified by" line is mandatory (a charter without it is decoration).
- **Review (audit)** — run the four-direction traceability trace + the P/M/O/X checklist against the project, citing file-level evidence for every verdict, classify each gap into one of four classes, and report **read-only** with minimal proposed fixes. Fixes are governed separately.

### Key Principles

- **The closed loop is the point.** "The spreadsheet shipped" is an *output*, not an *outcome*. Every headline purpose claim needs a check that it was actually delivered, and that measurement must route back into method (calibration, rule updates). Without it, PMO is open-loop.
- **Evidence per verdict.** Every checklist answer cites a file, a line, an artifact, or a computed check. "Looks fine" is not a verdict — an unbacked checkbox manufactures false confidence.
- **Charters point, never restate.** One home per rule (single source of truth). A charter that copies rules from the method docs is a duplicate-SSOT defect — the exact anti-pattern this lens exists to catch.
- **Judge usability against Purpose, per audience.** Value that is produced but buried in the deliverable is a gap. A renovator needs scope detail where a buyer needs the go/no-go picture — same project, different visibility.
- **Retrofit sparingly, never big-bang.** The lens is applied at review/build time; explicit charter blocks are added only where they'll be maintained. Stamping headers on every doc rots.

### Skill Composition

- **charter mode** → "What is this project for, and how will we know it worked?" (build the charter)
- **review mode** → "Does this project actually deliver its purpose, with no waste and no open loops?" (audit)
- `/architecture-review` → structural health of the code (a different lens)
- `/source-review` → evaluate an external idea against governance (not a project audit)

### What This Skill Does NOT Do

- **Review code diffs or structure** — use `/code-review` (diffs) or `/architecture-review` (structure).
- **Restate a project's method rules inside the charter** — charters point; the rules stay in their own docs.
- **Apply the fixes it finds** — review mode is read-only; each fix runs under its own governance evaluation.
- **Force a format onto every document** — the lens serves review; review does not serve the format.
