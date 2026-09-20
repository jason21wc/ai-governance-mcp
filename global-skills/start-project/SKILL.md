---
description: Onboard a project under the AI-governance framework — calibrate the mode, ask the minimal founding questions (Goal / Done-looks-like / Non-goals / app-vs-document), then lay down the governance + memory scaffolding via scaffold_project. Invoke when the user says "start a project", "new project", "set up this project", "onboard", or "project kickoff", or when a session begins in a folder with no governance memory files (the genesis hook nudges this). Works for code projects and document projects. Do NOT use for routine tasks inside an already-onboarded project, to read existing memory, or to adopt an existing project's hand-written CLAUDE.md (adopt mode is not yet implemented — a fast-follow).
disable-model-invocation: true
allowed-tools: Bash Read Write Edit
---

## Runtime Context

After the skill loads, inspect the current directory, governance-memory markers,
and Git state with ordinary read-only calls. Missing memory and missing Git history
are expected greenfield states, not failures.

## Instructions

You are onboarding a project so the work runs under the AI-governance framework from the start. The discriminating move is **discovery before commitment**: establish the founding context (Goal / Done-looks-like / Non-goals / app-vs-document) BEFORE any implementation, then lay down the governance + memory scaffolding. Read `procedure.md` in this skill folder for the full protocol; this is the orchestration shell.

### Quick Start

1. **Collect the Runtime Context above, then govern** — `evaluate_governance(planned_action="initialize and onboard a new project")`.
2. **Read `procedure.md`** and run its phases in order: govern → calibrate (mode + app-vs-document) → minimal founding questions (CFR §1.3.5 floor, depth-scaled) → `scaffold_project` (preview → confirm; non-destructive gap-fill) → seed the design doc → hand off to plan-mode.
3. **NEW mode only** in this version. If the folder already has governance memory, confirm with the user before re-scaffolding (scaffold_project is non-destructive, but don't surprise them).

### Key Principles

- **The founding floor is non-negotiable (CFR §1.3.5).** Even on a "clear" request, ask Goal / Done-looks-like / Non-goals / app-vs-document. Depth scales with calibration; the floor does not.
- **App vs. document drives templates + loaders, not memory location.** Memory files live in `_ai-context/` for BOTH types (unified layout v2.62.0); `project_type="code"` adds root loaders (AGENTS.md/CLAUDE.md) pointing in and coding-flavored templates. Decide this before scaffolding.
- **Non-destructive.** `scaffold_project` skips existing files — it fills gaps, never overwrites. Always run the preview (no `confirmed`) → confirm (`confirmed=true`) flow.
- **Freeform, not a menu.** Ask the founding questions as natural conversation, not an Option-A/B/C list (Behavioral Floor `freeform-dialogue`).

### What This Skill Does NOT Do

- **Adopt an existing project's hand-written CLAUDE.md** — augmenting (not clobbering) a vanilla CLAUDE.md is a deferred fast-follow; for now this is NEW-project onboarding.
- **Install enforcement hooks** — the structural governance gate + per-prompt FRAME are a separate capability (BACKLOG #68); this skill is the advisory front-half.
- **Run mid-project tasks** — use the normal governance flow for work inside an already-onboarded project.
