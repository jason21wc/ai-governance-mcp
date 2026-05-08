# Session State

**Last Updated:** 2026-05-07 (session-153 close — server.py decomposition complete).

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-153 (2026-05-07) completed server.py decomposition** — 4141-line monolith → 11-file `server/` package. Phase 0 (#135 bypass audit-log), Phase 1 (constants extraction), Phase 2 (state/logging/security extraction), Phase 3 (handler extraction + test split), Phase 4 (app extraction + helper dedup). 1522 tests pass. Code-reviewer verified each phase (all criteria PASS).

**ACTION ON RESUME (session-154):** **No blocking items.** Time-cued items: **Compliance Review #8** (~2026-05-15) → **C-109 deferred-cadence audit** (~2026-05-25) → **T-049 calendar review** (2026-06-15). **T-149 CE-first compliance measurement** — observe CE-vs-grep ratio for 3-5 sessions before activating Phase 2.

**Critical state for next session:**
- **Commits ahead of origin:** 0 (clean push).
- **server/ is a package NOW** — `server.py` replaced by `server/` with 11 modules. `__init__.py` is a 122-line re-export surface. Handlers in `server/handlers/`. Tests split: `test_server_retrieval.py`, `test_server_governance.py`, `test_server_agents.py`, `test_server_scaffold.py`.
- **Read-only Bash allowlist active NOW** — `git log`, `ls`, `grep`, etc. skip governance enforcement.
- **DAS in universal floor NOW** — every `evaluate_governance` includes design-first check.
- **Domain floor active NOW** — ai-coding detection triggers CED+LPG guaranteed delivery.
- **Tests:** 1522 passing (non-slow subset).
- **Compliance Review #8** — due ~2026-05-15.
- **V-005 CONFIRMED** (session pruning advisory works — 5/5 under 300 lines). Move to Retired in COMPLIANCE-REVIEW.md.

**Open BACKLOG (post-session-153):** #135 DONE. See BACKLOG.md for remaining items.

---

## Current Position

- **Phase:** Session-153 (2026-05-07) — server.py decomposition complete.
- **Mode:** Normal operation. No active monitors.
- **Active Task:** None. Next time-cued: Compliance Review #8 (~2026-05-15).

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.1.0** (reranking, MMR diversity, RRF opt-in, chunk quality filter, candidate pool cap, per-file dedup configurable cap=3, expanded 35-query benchmark) |
| Content | **v8.0.0** (Constitution — 24 principles; Art. I §1 renamed to Informational Readiness v8.0.0), **v3.31.5** (rules-of-procedure), **v2.44.0** (title-10-ai-coding-cfr), **v2.8.0** (ai-coding principles — 15), **v2.7.3** (multi-agent principles — 17), **v2.17.3** (multi-agent methods), **v1.4.2** (storytelling principles — 15), **v1.1.3** (storytelling methods), **v2.4.3** (multimodal-rag principles — 32), **v2.1.3** (multimodal-rag methods), **v1.2.2** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.2** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v4.0.1** (ai-instructions), **v1.9.0** (tiers.json). |
| Execution Framework | **v1.1.0** (`EXECUTION-FRAMEWORK.md` — permanent blueprint, thematic structure) |
| OPERATIONS.md | **v1** (2 cadences, 15 tripwires, 4 V-series, 5 metrics, 3 scheduled operations) |
| Tests | **1522 passing** (non-slow subset) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **18 MCP tools** (14 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **133 principles + 715 methods + 14 references** (862 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **1** (`compliance-review` — invoke via `/compliance-review`) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | **Green.** Last push: session-153. All commits pushed. |

---

## Last Session (2026-05-07)

153. **Session-153 (2026-05-07): server.py decomposition complete.**
   - **Decomposition:** 4141-line `server.py` monolith → 11-file `server/` package. Phases 0-4 executed per approved plan.
   - **Phase 0:** #135 bypass audit-log — shared `audit-bypass.sh` helper, all 9 hook bypass envvars now audit-logged.
   - **Phase 1:** Constants extraction — `_constants.py` (~1100 lines of templates, metadata, keywords).
   - **Phase 2:** Utility extraction — `_state.py`, `_logging.py`, `_security.py`. `reset()` function for test fixtures. 22 attribute-assignment sites in tests updated.
   - **Phase 3:** Handler extraction — `handlers/retrieval.py`, `handlers/governance.py`, `handlers/agents.py`, `handlers/scaffold.py`. Tests split into 4 new files.
   - **Phase 4:** App extraction — `_app.py` (MCP setup, list_tools, call_tool, main). `__init__.py` → 122-line re-export surface. `extract_json_from_response` deduped to `tests/helpers.py`.
   - **Key fix:** Patch target `ai_governance_mcp.server._handle_query_governance` → `ai_governance_mcp.server._app._handle_query_governance` (1 test site).
   - **Code-reviewer:** All 6 criteria PASS for both Phase 3 and Phase 4.
   - **Tests:** 10 new (1522 total passing).
   - **Plan file:** `~/.claude/plans/let-s-plan-the-server-py-hidden-map.md` (COMPLETE).

---

## Previous Sessions

*Session-152 (2026-05-07) shipped Read-Only Bash Allowlist — governance hook skips provably read-only Bash commands, unblocking read-only subagents. 1512 tests.*

*Session-151 (2026-05-06) shipped Domain Floor Injection — DAS universal floor, `_build_domain_floor()` mechanism, CED+LPG ai-coding floor, tiers.json v1.9.0, 1493 tests.*

*Session-150 (2026-05-05) shipped AI Coding Design Philosophy Integration — 3 new principles (CED, DAS, LPG), 8 CFR methods, preamble, 4 principle extensions.*

*Session-149 (2026-05-05) shipped CE-First Search Phase 1 (advisory layer) + Compliance Review #7 (12/12 PASS, V-005 CONFIRMED).*

*Session-148 (2026-05-05) completed CE Retrieval Architecture Upgrade (4-phase: reranking, MMR, RRF evaluation, embedding model evaluation). MRR +30%. CE v2.1.0.*

*Sessions 101-147 pruned per §7.0.4. Full history via `git log`.*

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
- **#135** — DONE (session-153, Phase 0)
- **IPC predict length validation** — Defense-in-depth (security-auditor M1, D1 Improvement)
- **Doc propagation** — API.md, title-10 `query_project` description alignment (cosmetic, D1)

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook)
- **T-152** — Subagent transcript isolation — upstream fix (Claude Code agentId in hook input)
- See OPERATIONS.md Tripwires section for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145.
- See OPERATIONS.md Cadences section for C-078, C-109.

**Working artifacts:**
- `~/.claude/plans/let-s-plan-the-server-py-hidden-map.md` — session-153 server.py decomposition plan (COMPLETE).
- `~/.claude/plans/no-create-the-plan-unified-octopus.md` — session-152 Read-Only Bash Allowlist plan (COMPLETE).
- `~/.claude/plans/i-told-claude-app-rosy-rivest.md` — session-149 CE-First Search plan (Phase 1 shipped, Phase 2 conditional).

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
