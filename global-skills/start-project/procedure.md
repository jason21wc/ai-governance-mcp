# Start-Project Procedure — Founding-First Project Onboarding

Authority: this skill operationalizes the project-initialization doctrine already in
`documents/title-10-ai-coding-cfr.md` — §1.3.2 Calibration Questions, §1.3.5 Brainstorming
Method (the **minimal founding floor**, depth-scaled), §7.8.2 Initialization Checklist — plus the
`scaffold_project` MCP tool. It does not restate those rules; it sequences them, founding-first.

**Core stance:** *No commitment without framing.* Project initialization is the founding
commitment that Discovery Before Commitment exists for — so the minimal founding questions run at
EVERY init, app or document, regardless of mode. Depth scales; the floor does not.

**Mode:** NEW (greenfield) only in this version. ADOPT (augment an existing project's vanilla
CLAUDE.md without clobbering it) is a deferred fast-follow — if asked to adopt, say so and stop.

---

## Phase 0 — Govern

Call `evaluate_governance(planned_action="initialize and onboard a new project")`. Proceed per its
routing (PROCEED/REVIEW/ESCALATE). This is a setup task; it will normally PROCEED.

## Phase 1 — Calibrate (mode + app-vs-document)

1. **Mode** — run the §1.3.2 Calibration Questions: Novelty (known pattern / similar / genuinely
   novel), Requirements certainty (HIGH/MEDIUM/LOW), Stakes (LOW/MEDIUM/HIGH), Longevity
   (short/medium/long). Map to a procedural mode via §1.3.3 (EXPEDITED / STANDARD / ENHANCED).
2. **App vs. document** — decide `project_type`:
   - **code** — a software repository; loaders (AGENTS.md/CLAUDE.md) at the repo root point into
     `_ai-context/`, where the memory files live (unified layout, v2.62.0).
   - **document** — a non-code/document project (research, writing, analysis); memory files live in
     `_ai-context/`, and the `README.md` there is the instruction file.
   Memory location is the SAME for both types; `project_type` selects the template flavor and
   loader files (§7.8.2 File Location). Pre-v2.62.0 projects with root-level memory files are
   grandfathered — tooling recognizes both layouts.
3. **Money-taking SaaS?** — for a **code** project, ask whether this app will take payments, hold
   customer data, be multi-tenant, or run as a production-deployed service. If yes, it inherits the
   SaaS-ops operating layer: use `project_type="code"` AND `kit_tier="saas-ops"` (Phase 3), which adds a
   per-app `SAAS-OPS-SOP.md`. (This is the per-app instance of the `saas-ops` governance domain,
   title-45.) If it's an internal tool, a library, or otherwise takes no money and holds no customer
   data, use `standard`.

Ask conversationally; do not present a dropdown.

## Phase 2 — Minimal founding questions (CFR §1.3.5 floor — depth-scaled, never skipped)

Ask the user the founding set, even if the request seems clear:

1. **Goal** — what problem does this solve, and for whom?
2. **Done-looks-like** — what is the success signal; when do we stop?
3. **Non-goals** — what should this deliberately NOT do?
4. (carried from Phase 1) **App vs. document** — confirmed.

**Depth scales with the Phase-1 calibration:**
- **EXPEDITED** (known pattern, low stakes) — answer each in a line or two, inline; proceed.
- **STANDARD** — add brief rationale per answer; note any open question.
- **ENHANCED or no-precedent** (`query_project("similar implementation in this project")` returns no
  strong match) — expand into the full §1.3.5 Socratic Q&A (latent requirements, implicit
  boundaries, non-user stakeholders, unnamed failure modes, the MVP cliff, anti-goals).

Use freeform dialogue (`freeform-dialogue`). If 3+ rounds produce no change to the frame, you are
either not in ENHANCED or you are anchoring — name it (the "compliance brainstorm" anti-pattern).

## Phase 3 — Scaffold (non-destructive gap-fill)

1. **Preview** — call `scaffold_project(project_type="<code|document>", kit_tier="<core|standard|saas-ops>",
   project_path="<dir>")` WITHOUT `confirmed`. For **code** projects, `kit_tier="standard"` adds
   CLAUDE.md / ARCHITECTURE.md / SPECIFICATION.md / a completion-sequence checklist / `_ai-context/BACKLOG.md` on
   top of the core memory files (recommended). For a **money-taking SaaS** (Phase 1 step 3), use
   `kit_tier="saas-ops"` — it adds `SAAS-OPS-SOP.md` (the per-app incident card) on top of standard.
   For **document** projects the templates are use-case-neutral (no coding vocabulary);
   `kit_tier="standard"` adds `_ai-context/BACKLOG.md` for deferred-work tracking (recommended).
   After scaffolding, ask what kind of work the project holds and propose specialized memory
   files to add alongside the core set (the scaffold's `next_steps` prompts this tailoring).
2. **Review the preview** — it lists `files_to_create` vs `files_to_skip` (existing files are
   skipped; the tool never overwrites). Confirm the set with the user if anything would surprise them.
3. **Confirm** — re-call with `confirmed=true` to write the missing files.

If the folder already has governance memory (Context Snapshot showed it), confirm intent before
scaffolding — it is non-destructive, but a fresh scaffold on an onboarded project is usually a sign
the user wanted something else.

## Phase 4 — Seed the founding brief / design doc

Capture the Phase-2 answers so they outlive the session:
- **EXPEDITED/STANDARD** — record Goal / Done / Non-goals in the scaffolded `PROJECT-MEMORY.md`
  (or `_ai-context/PROJECT-MEMORY.md`) under a short "Founding Context" note.
- **ENHANCED/no-precedent** — write the full §1.3.5 one-page design doc at
  `documents/design/<project-name>.md` (What / Why / Non-goals / Open-questions / Design-decisions),
  which becomes the input to plan-mode.
- **Money-taking SaaS (`saas-ops` tier)** — fill in the designated **approver** + on-call human in the
  scaffolded `SAAS-OPS-SOP.md` (the bracketed `[NAME]` fields). That human is the gate for every
  money / auth / customer-data / schema-migration action; route incidents via the `saas-ops` domain.

## Phase 5 — Hand off to plan-mode

Point the user at the next step: for any non-trivial build, enter plan-mode
(`.claude/plan-template.md`) with the founding brief / design doc as input. The plan's Recommended
Approach targets the documented Goal and Non-goals. For a trivial EXPEDITED task, proceed directly to
implementation under the normal governance flow.

## Phase 6 — Point at the shared Reference Library (cross-project)

The scaffolded `standard` CLAUDE.md points the project's AI at `search_references` (reuse
proven precedent *before* implementing) and `capture_reference` (bank a reusable, non-obvious
lesson *after* solving it). Both read/write the **central** Reference Library shared across all
the user's projects — there is no per-project setup, because the global `ai-governance` MCP server
provides the reach. Encourage their use during the build: this is how cross-project know-how
accumulates (and how the library's signal stops being single-project-biased).

---

## Escalation / stop points

- **ADOPT requested** (existing project with a hand-written CLAUDE.md) → stop; adopt mode is a
  deferred fast-follow (it must *augment*, never overwrite, the existing file). Tell the user.
- **ESCALATE from Phase 0 governance** → stop, surface to the user.
- **Folder already fully onboarded** → confirm the user actually wants to re-initialize before scaffolding.
- **project_path ambiguity** (sandboxed env, MCP cwd differs) → pass `project_path` explicitly to
  `scaffold_project` (§7.8.2 / Appendix L guidance).
