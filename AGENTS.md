# AI Governance MCP Server

**Description:** Semantic retrieval system for AI governance principles and methods.
**Framework:** AI Coding Methods
**Mode:** Standard

## Memory Files

Memory files live in **`_ai-context/`** (unified layout, v2.62.0 session-243 migration — nothing auto-discovers them; this loader is the pointer):

| File | Purpose |
|------|---------|
| _ai-context/SESSION-STATE.md | Current position, next actions |
| _ai-context/BACKLOG.md | Discrete projects (start, work, finish) |
| _ai-context/OPERATIONS.md | Recurring operational commitments (cadences, tripwires, metrics) |
| _ai-context/PROJECT-MEMORY.md | Decisions, constraints, gates |
| _ai-context/LEARNING-LOG.md | Lessons learned |
| _ai-context/SESSION-HANDOFF.md | Channel between a two-session IMPLEMENTER/VERIFIER split. **Not a memory file** — a transient protocol channel; read it only when running that split. Scope question filed as BACKLOG #233. |
| ARCHITECTURE.md | System design, data flow (structural doc — stays at root) |
| `.claude/skills/completion-sequence-aigov/` | Post-change steps including rename procedure for principle ID changes (invoke via `/completion-sequence-aigov`) |
| `.claude/skills/compliance-review/` | Periodic governance health (invoke via `/compliance-review`) |

**Data that is NOT in this repo (session-268).** The Reference Library and the search index are user data / build artifacts and live outside the checkout — `~/dev-tools/reference-library/` and `~/.ai-governance/index/` on this machine, `~/.ai-governance/` by default for anyone else. `index/` and `reference-library/` are gitignored, so their absence from `git status` is correct. Rebuild the index with `python -m ai_governance_mcp.extractor` after changing `documents/`; nothing does it automatically. **That command needs an interpreter carrying `sentence-transformers`, and `python` may not be it.** Measured 2026-08-30 on this machine: `python` resolves to `/opt/anaconda3/bin/python3`, which has it, while the project's own `.venv/bin/python` does not — so the documented command works by PATH ordering, not by design. The extractor now names the running interpreter and the fix when the import fails, instead of raising a bare `ModuleNotFoundError`. It also retries a failed model load with `local_files_only=True`, because sentence-transformers contacts Hugging Face for repo metadata even when every weight is cached, and a transient 403 should not fail a rebuild that needs nothing from the network. **Also pass the reference-library path** — the MCP host injects it and a shell does not inherit it: `AI_GOVERNANCE_REFERENCE_LIBRARY_PATH=$(python3 scripts/resolve_reference_library.py | head -1 | cut -d= -f2)`, or the shrink guard will refuse the build (correctly). Rationale + settings: `ARCHITECTURE.md` → "Data that lives outside the checkout".

**Scope — what counts as a "memory file":** these are the framework's own governance-managed, user-editable files — the cognitive-state set (SESSION-STATE / PROJECT-MEMORY / LEARNING-LOG / BACKLOG / OPERATIONS) plus the CLAUDE.md loader; ARCHITECTURE is a structural reference doc, listed above for session-load convenience. The host LLM's own built-in memory (e.g. Claude Code's `~/.claude/projects/*/memory/`) is **separate and off-limits** — leave it to the host. Canonical definition: `EXECUTION-FRAMEWORK.md §6.4` (repo root); binding boundary: `rules-of-procedure §G.5`.

Memory updates come from three sources: manual writes (Layer 1), journal subagent proposals triggered by the UserPromptSubmit hook (Layer 2, `/journal`), and dream skill passes mining completed transcripts (Layer 3, `/dream`). All automated sources are read-only — they propose changes that the main agent or user applies. A SessionStart hook additionally checks due cadences at session start: the **dream** cadence injects an AUTO-RUN directive at its activity threshold (execute the analysis now, background; apply/commit stays user-approved; `DREAM_AUTORUN=0` reverts to a nudge; fires logged for the fired-vs-ran compliance sub-check), while judgment-bearing cadences (compliance review, feedback-loop) remain structural surfacing + advisory action. See CFR §7.11 and EXECUTION-FRAMEWORK §7.2.

## On Session Start

1. Load `_ai-context/SESSION-STATE.md` for current position
2. Keep it a snapshot: **route first, then overwrite** — decisions to PROJECT-MEMORY, lessons to LEARNING-LOG, work to BACKLOG, cadences to OPERATIONS, session narrative to the commit message. Never append a per-session block; that stack was deleted 2026-08-15 because it was what concurrent close-outs collided on.
3. Follow Next Actions listed there
4. Reference `_ai-context/PROJECT-MEMORY.md` for constraints and decisions
5. Check `_ai-context/LEARNING-LOG.md` before repeating past mistakes
6. Check `_ai-context/OPERATIONS.md` for active cadence due dates and tripwire triggers

## Disposition (applies to every session)

**Reasoning posture:** Think systemically — address the structural cause, not the visible symptom. Recommend, don't ask. Match effort to stakes. Cite principle IDs when they influence your approach. Pick one pattern when two conflict. Volunteer a better path when you see one, then defer to the human.

**Communication style:** Lead with the outcome and the decision ask (BLUF). Calibrate vocabulary to this reader. Commit to claims — strip unearned hedging, earn emphasis with content. Use freeform prose, not structured option lists.

For the full behavioral floor (15 directives with worked examples), two calls: `query_governance("behavioral floor directives")` names the unit, then `get_principle('meta-method-behavioral-floor-directives')` returns it. `query_governance` does not inline method bodies.

## Key Commands

```bash
python -m ai_governance_mcp.extractor  # Rebuild index (needs sentence-transformers)
pytest tests/ -v                        # Run tests
python -m ai_governance_mcp.server      # Run governance server
python -m ai_governance_mcp.context_engine.server  # Run CE server
```

## Subagents and Skills

10 specialized agents in `.claude/agents/`: code-reviewer, test-generator, security-auditor, documentation-writer, orchestrator, validator, contrarian-reviewer, coherence-auditor, continuity-auditor, voice-coach. Edit `documents/agents/` (canonical source) first, then copy to `.claude/agents/`. CI verifies byte-match. `list_agents` MCP tool provides cross-platform agent discovery.

Decision matrix for skill vs hook vs subagent vs workflow: EXECUTION-FRAMEWORK.md §3.7.

## Project Structure

- `src/ai_governance_mcp/` — Governance server source
- `src/ai_governance_mcp/context_engine/` — Context Engine MCP (7 tools)
- `documents/` — Governance content (indexed)
- `documents/agents/` — Canonical agent templates (edit here first, then sync to `.claude/agents/`)
- `.claude/skills/` — Project skills (invoke via `/skill-name`)
- `global-skills/` — Canonical source for user-level skills at `~/.claude/skills/` (edit here first, then `scripts/sync-global-skills.sh link`; `--check` guards drift). A compatible subset also links to `~/.codex/skills` via `SKILLS_ONLY` (title-10 Appendix N.4)
- *(no `index/` or `reference-library/` here — both live outside the checkout; see above)*
- `tests/` — Test suite

## Jurisdiction

AI Coding applies: Specify → Plan → Tasks → Implement. Record gates in PROJECT-MEMORY.md. Keep changes atomic (≤15 files).

## Concurrency (multiple sessions on any shared repo)

> **Design of record: ADR-31** in `_ai-context/PROJECT-MEMORY.md` — delete the shared write anchor, refresh before writing, detect rather than lock. The rules below are its implementation; ADR-31 carries the measurements behind each one (including why `merge=union` was rejected for a shared session log, and why all three close-out orderings were tested rather than reasoned about). It also states its own limit: no two sessions have yet run in parallel under these rules. BACKLOG #348 is the item that will observe it.

**Scope: EVERY repository this machine writes to, not only this one.** The heading said "on one repo" until 2026-08-30, and that reading cost something real: refresh-before-writing was applied religiously here and not to `~/dev-tools`, where a commit onto local `main` without fetching first diverged it from a remote a sibling session had already advanced by four commits. The archive landed safely on a side branch, but it now needs a cherry-pick instead of a fast-forward. **`dev-tools` holds the Reference Library and is written by several sessions and hosts — treat it exactly like this repo: fetch, then write.** A rule scoped to the repository that happens to define it is a rule with a hole in it.

Standard Git branching is the shared lifecycle: every **mutating** session owns one checkout and one topic branch (`wt/<slug>-<nonce>` — let `prepare.sh` generate the nonce, do not hand-name it), then publishes to `main`. Read-only sessions may share a checkout. Run the `start-worktree` skill before edits, using the host-specific invocation it documents.

- **One writer per checkout.** A branch without a separate worktree still shares the working tree and index. A Git worktree lock is only a deletion guard; it is not a session mutex and does not make two writers in one checkout safe.
- **Host adapters differ; Git invariants do not.** Claude Code creates/enters a framework worktree, Codex Desktop adopts its native per-chat worktree, and Codex CLI creates/claims one from an ordinary shell when its sandbox cannot write the repository's common Git directory. A skill can run while the underlying Git mutation is denied: linked-worktree index and ref writes live under the common Git directory, outside the checkout.
- **`main` is the integration point.** Don't do mutating work directly on `main` — a dirty primary blocks integration and a shared primary is not isolated.
- **Refresh from an explicit live `origin/main` BEFORE writing final close-out memory.** Use the completion helper (resolve it the way the checklists do — `CS=~/.claude/skills/completion-sequence; [ -f "$CS/integrate.sh" ] || CS=~/.codex/skills/completion-sequence; [ -f "$CS/integrate.sh" ] || CS=global-skills/completion-sequence`): `bash "$CS/integrate.sh" refresh --default-ref main`. `git fetch` moves the remote-tracking ref, not local `main`, so merging a local default can use an arbitrarily stale base. Refresh-first removes the avoidable same-base snapshot conflict; it does **not** guarantee conflict-free integration when two sessions changed the same substantive content.
- **Publish optimistically and retry.** `bash "$CS/integrate.sh" publish --default-ref main` (same `$CS` resolution as above) fetches again, proves the push is a fast-forward, and verifies the live result. Exit 3 means a sibling won the fetch-to-push race: repeat refresh → affected tests → close-out memory → commit → publish. Never force-push the integration branch.
- **Worktrees isolate tracked checkout state, not runtime resources.** Ports, databases, daemons, caches, editable installs, user configuration, ignored files, and symlink targets remain shared unless the project namespaces them.
- **Shared memory files** (`BACKLOG.md`, `LEARNING-LOG.md`) auto-resolve via `merge=union` in `.gitattributes`.
- **SESSION-STATE conflicts resolve latest-session-wins.** It is deliberately NOT `merge=union` — union duplicates a replaced line into corruption — so a concurrent close-out gives you one hand-resolved hunk. **"Latest" means latest to WRITE, i.e. you, the one resolving:** take the other session's version wholesale, then re-apply your own Current Position / Immediate Context / Next Actions on top, because yours is the state that is current at the moment of the merge. Then re-run `scripts/gen_quick_reference.py` to settle the generated blocks. *(Stated explicitly because "latest-session-wins" is ambiguous between latest-to-write and latest-to-arrive, and this file and the completion-sequence checklist briefly gave opposite readings of it.)* This rule is here because `cc0c46f` resolved a real conflict "per AGENTS.md" and the rule had since been lost from it. The hunk is small by construction now that the per-session narrative is gone; if it stops being small, someone is appending to this file again.
- **Push `main` only with permission.** Topic branches can be pushed freely for durability.

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions.md for full activation protocol.*
