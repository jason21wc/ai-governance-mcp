# Session State

**Last Updated:** 2026-05-13 (session-170 — Execution Framework 8-bucket → 10-subsystem restructuring).

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-170 (2026-05-13) — Execution Framework 8-bucket → 10-subsystem restructuring.**

**ACTION ON RESUME (session-171):** Time-cued: **C-109 deferred-cadence audit** (~2026-05-25). **Compliance Review #9** (~2026-05-22–2026-05-27, includes first Check 12 constraint retirement review). **C-012 Security Posture Review** first due ~2026-08-08. Docker image rebuild needed (Dockerfile CMD changed + enforcement.py updated).

**Critical state for next session:**
- **EXECUTION-FRAMEWORK.md v2.0.0** — Restructured from 8-bucket to 10-subsystem architecture. Memory (Bucket 2) split into Working Memory (Subsystem 3), Persistent Storage (Subsystem 4), Reference Storage (Subsystem 5). Reordered by architectural dependency. "Bucket" → "subsystem", "sub-bucket" → "sub-component". CoALA provenance preserved. Procedural memory reclassified to Persistent Storage per contrarian review. §4 System Map restructured (all 7 CoALA types now have rows). §6 Memory Contracts split into 3 subsections. §12 Design History preserved with terminology conversion note.
- **OPERATIONS.md** — Single reference updated (Bucket 5/8 → Subsystem 8/10).
- **1691 tests passing** (non-slow). No code changes — docs only.
- **Docker rebuild still needed** from session-168.

---

## Current Position

- **Phase:** Session-170 (2026-05-13) — Execution Framework restructuring.
- **Mode:** Normal operation.
- **Active Task:** None. Next: C-109 deferred-cadence audit (~2026-05-25), Compliance Review #9 (~2026-05-22).

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.1.0** (reranking, MMR diversity, RRF opt-in, chunk quality filter, candidate pool cap, per-file dedup configurable cap=3, expanded 35-query benchmark) |
| Content | **v8.0.1** (Constitution — 24 principles; Art. I §1 renamed to Informational Readiness v8.0.0, v8.0.1 added operational considerations for project initialization + validate before action), **v3.31.5** (rules-of-procedure), **v2.45.1** (title-10-ai-coding-cfr), **v2.8.1** (ai-coding principles — 15), **v2.7.3** (multi-agent principles — 17), **v2.18.0** (multi-agent methods), **v1.4.2** (storytelling principles — 15), **v1.1.3** (storytelling methods), **v2.4.3** (multimodal-rag principles — 32), **v2.1.3** (multimodal-rag methods), **v1.2.2** (ui-ux principles — 20), **v1.1.0** (ui-ux methods), **v1.4.2** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v4.0.5** (ai-instructions), **v2.1.0** (tiers.json — critical_5 scaffold + external-input-gap-analysis + conflicting-patterns directives). |
| Execution Framework | **v2.0.0** (`EXECUTION-FRAMEWORK.md` — permanent blueprint, 10-subsystem architecture) |
| OPERATIONS.md | **v2** (3 cadences, 17 tripwires, 3 V-series, 5 metrics, 3 scheduled operations) |
| Tests | **1691 passing** (non-slow subset) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **20 MCP tools** (16 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **133 principles + 735 methods + 18 references** (886 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **4** (`/compliance-review`, `/completion-sequence`, `/test-authoring`, `/content-enhancer`) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | **Green.** Last push: session-168. All pushed. |

---

## Last Session (2026-05-13)

170. **Session-170 (2026-05-13): EXECUTION-FRAMEWORK.md 8-bucket → 10-subsystem restructuring.**
   - **EXECUTION-FRAMEWORK.md v2.0.0:** Memory (Bucket 2) split into Working Memory (Subsystem 3), Persistent Storage (Subsystem 4), Reference Storage (Subsystem 5). 10 subsystems ordered by architectural dependency. Contrarian-reviewed: Procedural memory reclassified to Persistent Storage, S-Series collision avoided (Subsystem N in full), §2.3 empirical reconciliation note. §4 System Map restructured (all 7 CoALA types). §6 split into 3 subsections. §12 preserved with terminology note. 13-step plan, 3 verification agents — all checks passed.
   - **OPERATIONS.md:** Single reference updated (Bucket 5/8 → Subsystem 8/10).
   - **Tests:** 1691 passing (unchanged — docs-only change).

169. **Session-169 (2026-05-12): Behavioral floor directives + harness engineering article + constraint retirement check.**
   - Behavioral floor expanded (2 new directives). BACKLOG #159 implemented. Harness engineering article evaluated. Check 12 added. T-163 tripwire added. 1691 tests.

---

## Previous Sessions

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
1. **Compliance Review #9** — due ~2026-05-22–2026-05-27 (10-15 days from Review #8 on 2026-05-12). Invoke `/compliance-review`.
2. **C-109 deferred-cadence audit** — due ~2026-05-25. See OPERATIONS.md.
3. **C-155 feedback loop analysis** — next run due ~2026-06-07. See OPERATIONS.md.
4. **Docker image rebuild** — Dockerfile CMD changed + enforcement.py updated. Rebuild and push.

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook). CE-First Phase 2 (grep/glob advisory hook) activates only if this fires.
- **T-152** — Subagent transcript isolation — upstream fix (Claude Code agentId in hook input)
- See OPERATIONS.md for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145, T-161, T-163, C-078, C-109, C-155.

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
