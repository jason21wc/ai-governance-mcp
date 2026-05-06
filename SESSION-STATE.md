# Session State

**Last Updated:** 2026-05-05 (session-149 close — CE-First Search Phase 1 shipped). Governance: `gov-1dcce9b35ff5`.

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-149 (2026-05-05) shipped CE-First Search Phase 1** + **Compliance Review #7** (12/12 PASS, V-005 CONFIRMED). Double-checked by 3 subagents (code-reviewer, coherence-auditor, validator) — 4 issues found and fixed. Phase 2 (Grep/Glob advisory hook) conditional on T-149 measurement.

**ACTION ON RESUME (session-150):** **No blocking items.** Time-cued items: **Compliance Review #8** (~2026-05-15) → **C-109 deferred-cadence audit** (~2026-05-25) → **T-049 calendar review** (2026-06-15). **T-149 CE-first compliance measurement** — observe CE-vs-grep ratio for 3-5 sessions before activating Phase 2.

**Critical state for next session:**
- **Commits ahead of origin:** 0 (after this push).
- **CE-First advisory changes active NOW** — tool descriptions and CLAUDE.md loaded at session start, SERVER_INSTRUCTIONS appended to every CE response. No restart needed.
- **Tests:** 1481 passing (non-slow subset) + 30 deselected slow.
- **Compliance Review #8** — due ~2026-05-15.
- **V-005 CONFIRMED** (session pruning advisory works — 5/5 under 300 lines). Move to Retired in COMPLIANCE-REVIEW.md.
- **Deferred documentation propagation:** API.md, README.md, title-10-ai-coding-cfr.md still use old `query_project` description text. Cosmetic — no behavioral impact.

**Open BACKLOG (post-session-149):** Same as session-148 plus deferred doc propagation (cosmetic). See BACKLOG.md for full list.

---

## Current Position

- **Phase:** Session-149 (2026-05-05) — CE-First Search Phase 1 shipped + Compliance Review #7 completed. Phase 2 conditional on measurement.
- **Mode:** Normal operation. No active monitors.
- **Active Task:** None. Next time-cued: Compliance Review #8 (~2026-05-15).

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.1.0** (reranking, MMR diversity, RRF opt-in, chunk quality filter, candidate pool cap, per-file dedup configurable cap=3, expanded 35-query benchmark) |
| Content | **v8.0.0** (Constitution — 24 principles; Art. I §1 renamed to Informational Readiness v8.0.0), **v3.31.5** (rules-of-procedure), **v2.43.3** (title-10-ai-coding-cfr), **v2.7.6** (ai-coding principles — 12), **v2.7.3** (multi-agent principles — 17), **v2.17.3** (multi-agent methods), **v1.4.2** (storytelling principles — 15), **v1.1.3** (storytelling methods), **v2.4.3** (multimodal-rag principles — 32), **v2.1.3** (multimodal-rag methods), **v1.2.2** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.2** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v4.0.0** (ai-instructions), **v1.6.0** (tiers.json). |
| Execution Framework | **v1.1.0** (`EXECUTION-FRAMEWORK.md` — permanent blueprint, thematic structure) |
| OPERATIONS.md | **v1** (2 cadences, 14 tripwires, 4 V-series, 5 metrics, 3 scheduled operations) |
| Tests | **1511 total** (1481 passing non-slow subset + 30 deselected slow) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 689 methods + 14 references** (833 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **1** (`compliance-review` — invoke via `/compliance-review`) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | **Green.** Last push: session-148. |

---

## Last Session (2026-05-05)

149. **Session-149 (2026-05-05): CE-First Search — Phase 1 (advisory layer) shipped.**
   - **Tool description:** "Default search tool" framing, explicit scope, competitive framing vs Grep, unified 4-item Grep-only exception list.
   - **SERVER_INSTRUCTIONS:** Added "When to Use Grep Instead" section with 4 specific Grep-only cases + default-search-tool reinforcement. Updated Tools table.
   - **CLAUDE.md:** Replaced "CE vs Grep" with "Search default: CE first" directive.
   - **Double-check:** 3 subagents (code-reviewer, coherence-auditor, validator) found 4 issues — all fixed: exception list mismatch across 3 surfaces, stale Tools table, module docstring, vague "piping output" bullet.
   - **Phase 2 (Grep/Glob advisory hook):** Conditional on T-149 tripwire. Plan designed, contrarian-reviewed (3 IMPORTANT findings adopted: measurement gate, heuristic precision, advisory fatigue risk).
   - **Compliance Review #7:** 12/12 PASS (1 PASS_WITH_NOTES — startup-read token-limit, n=3 recurring). V-005 CONFIRMED (5/5 under 300). V-006 sessions 2-4 recorded (3 denies in sessions 2-3, 0 in session 4). OOM gate +3 TPs (total 9).
   - **Files modified:** context_engine/server.py, CLAUDE.md, COMPLIANCE-REVIEW.md, OPERATIONS.md, rules-of-procedure.md §9.7.7.
   - **Governance:** `gov-1dcce9b35ff5`, `gov-f9dc791e90fd`.

---

## Previous Sessions

*Session-148 (2026-05-05) completed CE Retrieval Architecture Upgrade (4-phase: reranking, MMR, RRF evaluation, embedding model evaluation). MRR +30%. CE v2.1.0.*

*Session-147 (2026-05-04) closed BACKLOG #49 (Embedding Model Memory Sharing). Phase 2 IPC service shipped and verified.*

*Sessions 144-146 pruned per §7.0.4. Highlights: session-146 Appendix M.1 Warp Terminal update. Session-145 BACKLOG #148 closed (Execution Framework plan, OPERATIONS.md created). Session-144 BACKLOG #152 closed (principle rename, constitution v8.0.0). Decisions → PROJECT-MEMORY.md, lessons → LEARNING-LOG.md. Full history via `git log`.*

*Sessions 101-143 pruned per §7.0.4. Full history via `git log`.*

---

## Next Actions

**Time-cued:**
1. **Compliance Review #8** — due ~2026-05-15 (10-15 days from Review #7 on 2026-05-05). Invoke `/compliance-review`.
2. **C-109 deferred-cadence audit** — due ~2026-05-25. See OPERATIONS.md.

**Ready-to-work (user-directed):**
- **CE-First Phase 2** — Grep/Glob advisory hook (D2, conditional on T-149 measurement)
- **#154** — OPERATIONS.md documentation quality pass (D1 Docs)
- **#153** — Effectiveness metrics analysis script (D1 New Capability, deferred until n>1000 audit entries)
- **#150** — Semantic-retrieval FP investigation (D2 Discussion)
- **#149** — Contrarian-reviewer over-generation tendency (D2 Discussion)
- **#135** — Bypass-envvar audit-log refactor (trigger fired, eligible project-class work)
- **IPC predict length validation** — Defense-in-depth (security-auditor M1, D1 Improvement)
- **Doc propagation** — API.md, README.md, title-10 `query_project` description alignment (cosmetic, D1)

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook)
- See OPERATIONS.md Tripwires section for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145.
- See OPERATIONS.md Cadences section for C-078, C-109.

**Working artifacts:**
- `~/.claude/plans/i-told-claude-app-rosy-rivest.md` — session-149 CE-First Search plan (Phase 1 shipped, Phase 2 conditional).

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
