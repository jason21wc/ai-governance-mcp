# Session State

**Last Updated:** 2026-05-07 (session-152 close — Read-Only Bash Allowlist shipped).

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-152 (2026-05-07) shipped Read-Only Bash Allowlist** — governance hook now skips provably read-only Bash commands (`git log`, `ls`, `grep`, etc.), unblocking read-only subagents (contrarian-reviewer, security-auditor). 19 new tests. 1512 tests pass. FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION registered. T-152 tripwire added.

**ACTION ON RESUME (session-153):** **No blocking items.** Time-cued items: **Compliance Review #8** (~2026-05-15) → **C-109 deferred-cadence audit** (~2026-05-25) → **T-049 calendar review** (2026-06-15). **T-149 CE-first compliance measurement** — observe CE-vs-grep ratio for 3-5 sessions before activating Phase 2.

**Critical state for next session:**
- **Commits ahead of origin:** 0 (clean push).
- **Read-only Bash allowlist active NOW** — `git log`, `ls`, `grep`, etc. skip governance enforcement.
- **DAS in universal floor NOW** — every `evaluate_governance` includes design-first check.
- **Domain floor active NOW** — ai-coding detection triggers CED+LPG guaranteed delivery.
- **Tests:** 1512 passing (non-slow subset).
- **Compliance Review #8** — due ~2026-05-15.
- **V-005 CONFIRMED** (session pruning advisory works — 5/5 under 300 lines). Move to Retired in COMPLIANCE-REVIEW.md.

**Open BACKLOG (post-session-152):** Same as session-151. See BACKLOG.md for full list.

---

## Current Position

- **Phase:** Session-152 (2026-05-07) — Read-Only Bash Allowlist shipped.
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
| Tests | **1512 passing** (non-slow subset) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **133 principles + 715 methods + 14 references** (862 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **1** (`compliance-review` — invoke via `/compliance-review`) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | **Green.** Last push: session-152. All commits pushed. |

---

## Last Session (2026-05-07)

152. **Session-152 (2026-05-07): Read-Only Bash Allowlist shipped.**
   - **10-agent governance effectiveness test:** Spawned 10 identical subagents with a simple coding task to test whether DAS/CED/LPG principles influence behavior without explicit instruction. Result: 10/10 behavioral compliance (all called `evaluate_governance` + `query_project` unprompted), but 10/10 hook-denied.
   - **Root cause:** Subagent MCP calls recorded in subagent transcript (`subagents/agent-<id>.jsonl`), not parent. Governance hook scans only parent transcript. Scanner logic correct; wrong file scanned.
   - **Contrarian review:** Rejected recency-based heuristic (parent enforcement regression). Adopted deterministic read-only Bash command allowlist (zero enforcement regression, independently valuable).
   - **Read-only Bash allowlist:** Conservative check in `pre-tool-governance-check.sh` — rejects chaining (`&&`, `||`, `;`), redirects (`>`, `>>`), requires all pipe segments to match known-safe command list. `READONLY_BASH_SKIP=true` to disable.
   - **Residual limitation:** Mutation subagents (test-generator, documentation-writer) remain blocked. Tracked as T-152 tripwire.
   - **Tests:** 19 new (1512 total passing).
   - **Files modified:** pre-tool-governance-check.sh, test_hooks.py, failure-mode-registry.md, test-failure-mode-map.md, CLAUDE.md, OPERATIONS.md.
   - **Bug fixed:** `BASH_COMMAND` reserved variable collision — Bash built-in auto-overwrites; renamed to `TOOL_CMD`.

---

## Previous Sessions

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
- **#135** — Bypass-envvar audit-log refactor (trigger fired, eligible project-class work)
- **IPC predict length validation** — Defense-in-depth (security-auditor M1, D1 Improvement)
- **Doc propagation** — API.md, title-10 `query_project` description alignment (cosmetic, D1)

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook)
- **T-152** — Subagent transcript isolation — upstream fix (Claude Code agentId in hook input)
- See OPERATIONS.md Tripwires section for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145.
- See OPERATIONS.md Cadences section for C-078, C-109.

**Working artifacts:**
- `~/.claude/plans/no-create-the-plan-unified-octopus.md` — session-152 Read-Only Bash Allowlist plan (COMPLETE).
- `~/.claude/plans/do-online-research-and-reflective-rabbit.md` — session-151 Domain Floor Injection plan (COMPLETE).
- `~/.claude/plans/i-told-claude-app-rosy-rivest.md` — session-149 CE-First Search plan (Phase 1 shipped, Phase 2 conditional).

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
