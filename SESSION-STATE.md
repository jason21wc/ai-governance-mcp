# Session State

**Last Updated:** 2026-05-17 (session-178 — BACKLOG #48 `/code-review` + `/security-scan` global skills shipped).

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-178 (2026-05-17) — BACKLOG #48: `/code-review` and `/security-scan` global skills shipped.**

**ACTION ON RESUME (session-179):** Time-cued: **Compliance Review #9** (~2026-05-22–2026-05-27, includes first Check 12 constraint retirement review + Check 7b first review). **C-109 deferred-cadence audit** (~2026-05-25). **C-012 Security Posture Review** first due ~2026-08-08. Monitor Claude App enforcement proxy effectiveness (soft mode deployed session-173). Observe whether reference library capture check (item 18) produces proposals — validates BACKLOG #41 Phase 1 hypothesis.

**Critical state for next session:**
- **Backlog: 7 discussion items** — #6, #11, #41, #45, #46, #47, #48. #48 partially shipped (2 of 8 skills); remaining skills stay in Discussion.
- **Global skills shipped** — `/code-review` (3-pass parallel subagent: correctness, security, architecture + 2 opt-in: performance, test-coverage) and `/security-scan` (secrets detection, dependency audit, basic auth patterns). Canonical source in `global-skills/`, installed to `~/.claude/skills/`.
- **Contrarian agent calibrated** — precedent-vs-design-vs-evidence distinction added to contrarian-reviewer boundaries.
- **pyproject.toml** — cognee version capped to `<2` (was uncapped `>=1.0.9`).
- **#41 Phase 1 observation window still open** — shipped session-174.
- **Claude App enforcement proxy** — soft mode deployed session-173.

---

## Current Position

- **Phase:** Session-178 (2026-05-17) — BACKLOG #48 global skills (`/code-review` + `/security-scan`).
- **Mode:** Normal operation.
- **Active Task:** None. Next: Compliance Review #9 (~2026-05-22), C-109 deferred-cadence audit (~2026-05-25).

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.1.0** (reranking, MMR diversity, RRF opt-in, chunk quality filter, candidate pool cap, per-file dedup configurable cap=3, expanded 35-query benchmark) |
| Content | **v8.1.0** (Constitution — 24 principles; E&E comprehension scaffold obligation + engagement-depth choice), **v3.32.0** (rules-of-procedure — §16.8 Comprehension Scaffold Format), **v2.46.0** (title-10-ai-coding-cfr — 6 comprehension scaffold domain methods), **v2.9.0** (ai-coding principles — 15), **v2.7.3** (multi-agent principles — 17), **v2.18.0** (multi-agent methods), **v1.4.2** (storytelling principles — 15), **v1.1.3** (storytelling methods), **v2.5.0** (multimodal-rag principles — 32), **v2.2.0** (multimodal-rag methods), **v1.2.2** (ui-ux principles — 20), **v1.1.0** (ui-ux methods), **v1.4.2** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v1.0.0** (accounting principles — 12), **v1.0.0** (accounting methods), **v4.1.0** (ai-instructions), **v2.1.0** (tiers.json — critical_5 scaffold + external-input-gap-analysis + conflicting-patterns directives). |
| Execution Framework | **v2.0.0** (`EXECUTION-FRAMEWORK.md` — permanent blueprint, 10-subsystem architecture) |
| OPERATIONS.md | **v2** (3 cadences, 17 tripwires, 3 V-series, 5 metrics, 3 scheduled operations) |
| Tests | **1728 passing** (non-slow subset) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **20 MCP tools** (16 governance + 4 context engine) |
| Domains | **8 shipped** (modular — filesystem-discovered from frontmatter, custom domains supported) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **145 principles + 764 methods + 19 references** (928 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **6** (`/compliance-review`, `/completion-sequence`, `/test-authoring`, `/content-enhancer`, `/code-review` (global), `/security-scan` (global)) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | Last push: session-178. All pushed. |

---

## Last Session (2026-05-17)

178. **Session-178 (2026-05-17): BACKLOG #48 — Generic Cross-Project Skill Suite (partial).**
   - **Plan mode** — full plan with contrarian review. Contrarian used precedent-based reasoning ("no existing skill uses parallel dispatch") — correctly identified as non-systemic. Multi-pass architecture retained; design concerns (reconciliation spec, functional validation, scope inflation) adopted.
   - **`/code-review` shipped** — 3-pass parallel subagent dispatch (correctness, security, architecture) with severity-gated reconciliation. 2 optional passes (performance, test-coverage). Research-backed: fan-out/fan-in (Osmani, O'Reilly 2026), severity gating (Jet Xu), evidence requirement (Ellipsis). 7 files in `global-skills/code-review/`.
   - **`/security-scan` shipped** — secrets detection, dependency audit, basic auth pattern checks. 2 files in `global-skills/security-scan/`.
   - **Contrarian agent calibrated** — precedent-vs-design-vs-evidence distinction added to contrarian-reviewer boundaries.
   - **Double-checked** — coherence-auditor + validator. Portability issue fixed, escalation rules added, functional validation confirmed.
   - **pyproject.toml** — cognee version capped `>=1.0.9,<2`.
   - **Test suite fixed** — 183 failures traced to transformers 4.57.3 (TF backend removed from BACKENDS_MAPPING but TF model files still shipped); upgraded to 4.57.6. 11 errors traced to IPC socket routing bypassing test mocks; fixed with `AI_CONTEXT_ENGINE_EMBED_SOCKET=none` in fixture. Agent hash updated. 1728 tests passing, CI green.

---

## Previous Sessions

*Session-177 (2026-05-15) A5 KG research + §3.8 fixes + reference library entry + Cognee backlog. 1728 tests.*

*Session-176 (2026-05-14) Backlog review + #46 research + #11 analysis. No code changes.*

*Session-175 (2026-05-14) Modular domain architecture documentation propagation + hook regex fix. 1728 tests.*

*Session-174 (2026-05-14) BACKLOG #41 Phase 1 — behavioral trigger for reference library capture. Completion-sequence item 18 added. Contrarian pivoted 7-step plan to 1-file behavioral trigger.*

*Session-173 (2026-05-14) Operational cleanup + BACKLOG #160/#161 close. Docker v2.0.0 rebuilt. CE re-indexed. Claude App enforcement proxy (soft mode).*

*Session-172 (2026-05-14) BACKLOG #162 Accounting Domain — 8th domain, 12 principles, 4 series. 1724 tests.*

*Session-171 (2026-05-13) BACKLOG #53 Modular Domain Architecture — filesystem-based domain discovery. 1710 tests.*

*Session-170 (2026-05-13) Execution Framework 8-bucket → 10-subsystem restructuring. 1691 tests.*

*Session-169 (2026-05-12) Behavioral floor directives + harness engineering article + constraint retirement check. 1691 tests.*

*Session-168 (2026-05-12) SSOT + list_agents + Compliance Review #8 + BACKLOG #161 enforcement proxy default. 1686 tests.*

*Session-165 (2026-05-10) Governance Retrieval Quality Assessment + content enhancer application. BACKLOG #16 closed. 1612 tests.*

*Session-164 (2026-05-10) Content Enhancer skill + backlog cleanup. #85, #127, #125-b closed. 1611 tests.*

*Session-163 (2026-05-10) Critical 5 reasoning scaffold + Enforcement Layer Matrix. 1611 tests.*

*Session-162 (2026-05-10) BACKLOG #158+#150 threshold tuning — REVIEW alarm fatigue + S-Series semantic FP. 1632 tests.*

*Session-161 (2026-05-10) BACKLOG #158 REVIEW score threshold. 1631 tests.*

*Session-160 (2026-05-10) shipped BACKLOG #54+#55 Skills Taxonomy & Codification. 4-layer taxonomy, 3 skills, workflows/ deleted. 1600 tests.*

*Session-159 (2026-05-09) BACKLOG #154 OPERATIONS.md documentation quality pass.*

*Session-158 (2026-05-09) #10 tool integration governance pattern — domain-tool appendix shipped. ui-ux CFR v1.1.0.*

*Session-157 (2026-05-08) backlog hygiene + #10/#35/#79 consolidation. Anti-stub rule at 3 layers. CFR v2.44.1.*

*Session-156 (2026-05-08) shipped BACKLOG #157 (feedback workflow Check 11) + #44 (reference logging + maturity proposals). 1600 tests.*

*Session-155 (2026-05-08) shipped compliance metric two-defect fix, filed #158 REVIEW alarm fatigue. 1595 tests.*

*Session-154 (2026-05-08) shipped Feedback Loop Analysis + #156 retrieval fix + #155 REVIEW rename. 1576 tests.*

*Session-153 (2026-05-07) completed server.py decomposition — 4141-line monolith → 11-file server/ package. 1522 tests.*

*Session-152 (2026-05-07) shipped Read-Only Bash Allowlist — governance hook skips provably read-only Bash commands. 1512 tests.*

*Session-151 (2026-05-06) shipped Domain Floor Injection — DAS universal floor, CED+LPG ai-coding floor. 1493 tests.*

*Sessions 101-150 pruned per §7.0.4. Full history via `git log`.*

---

## Next Actions

**Time-cued:**
1. **Compliance Review #9** — due ~2026-05-22–2026-05-27 (10-15 days from Review #8 on 2026-05-12). Invoke `/compliance-review`. Includes first Check 12 (constraint retirement) + first Check 7b (permission coverage).
2. **C-109 deferred-cadence audit** — due ~2026-05-25. See OPERATIONS.md.
3. **C-155 feedback loop analysis** — next run due ~2026-06-07. See OPERATIONS.md.
4. **Monitor Claude App proxy** — soft mode deployed session-173. Observe whether warnings appear. Flip to hard mode when ready.
5. **Monitor #41 Phase 1** — observe whether reference library capture check produces proposals.

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook). CE-First Phase 2 (grep/glob advisory hook) activates only if this fires.
- **T-152** — Subagent transcript isolation — upstream fix (Claude Code agentId in hook input)
- See OPERATIONS.md for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145, T-161, T-163, C-078, C-109, C-155.

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
