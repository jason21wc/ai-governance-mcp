# Session State

**Last Updated:** 2026-05-14 (session-172 — BACKLOG #162 Accounting Domain).

**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## RESUMPTION — Where to Pick Up (read this first)

**Session-172 (2026-05-14) — BACKLOG #162 Accounting Domain.**

**ACTION ON RESUME (session-173):** Time-cued: **Compliance Review #9** (~2026-05-22–2026-05-27, includes first Check 12 constraint retirement review). **C-109 deferred-cadence audit** (~2026-05-25). **C-012 Security Posture Review** first due ~2026-08-08. Docker image rebuild needed (src/ changed across sessions 168-172).

**Critical state for next session:**
- **Accounting Domain shipped** — BACKLOG #162 closed. 8th governance domain: 12 principles across 4 series (LE: Ledger Integrity, EC: Entity & Classification, TC: Temporal & Compliance, RC: Reconciliation & Controls). Methods/CFR with 9 sections including QBO integration (Appendix A) and domain-tools ecosystem catalog (Appendix B).
- **19 files changed** — 2 created (title-22-accounting.md, title-22-accounting-cfr.md), 17 modified (extractor.py, config.py, domains.json, ai-instructions.md, README.md, ARCHITECTURE.md, SPECIFICATION.md, EXECUTION-FRAMEWORK.md, SESSION-STATE.md, BACKLOG.md, test_extractor.py, test_config.py, test_server_governance.py, retrieval_quality.json).
- **1724 tests passing** (up from 1710 — 14 new tests for accounting prefix, series map, S-Series safety, principle extraction, integration).
- **Coherence audit** completed: 1D + 8M + 3C findings, all resolved. Dangerous: ARCHITECTURE.md benchmark coverage claim fixed. Key extractor fix: substring collision in category_mapping (le-series matched e-series → "safety"; ec/tc/rc-series matched c-series → "context").
- **Docker rebuild still needed** from sessions 168-172.
- **Context Engine index** should be refreshed (`index_project`) to pick up new accounting documents.

---

## Current Position

- **Phase:** Session-172 (2026-05-14) — BACKLOG #162 Accounting Domain.
- **Mode:** Normal operation.
- **Active Task:** None. Next: Compliance Review #9 (~2026-05-22), C-109 deferred-cadence audit (~2026-05-25).

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.1.0** (reranking, MMR diversity, RRF opt-in, chunk quality filter, candidate pool cap, per-file dedup configurable cap=3, expanded 35-query benchmark) |
| Content | **v8.0.1** (Constitution — 24 principles; Art. I §1 renamed to Informational Readiness v8.0.0, v8.0.1 added operational considerations for project initialization + validate before action), **v3.31.5** (rules-of-procedure), **v2.45.1** (title-10-ai-coding-cfr), **v2.8.1** (ai-coding principles — 15), **v2.7.3** (multi-agent principles — 17), **v2.18.0** (multi-agent methods), **v1.4.2** (storytelling principles — 15), **v1.1.3** (storytelling methods), **v2.4.3** (multimodal-rag principles — 32), **v2.1.3** (multimodal-rag methods), **v1.2.2** (ui-ux principles — 20), **v1.1.0** (ui-ux methods), **v1.4.2** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v1.0.0** (accounting principles — 12), **v1.0.0** (accounting methods), **v4.0.6** (ai-instructions), **v2.1.0** (tiers.json — critical_5 scaffold + external-input-gap-analysis + conflicting-patterns directives). |
| Execution Framework | **v2.0.0** (`EXECUTION-FRAMEWORK.md` — permanent blueprint, 10-subsystem architecture) |
| OPERATIONS.md | **v2** (3 cadences, 17 tripwires, 3 V-series, 5 metrics, 3 scheduled operations) |
| Tests | **1724 passing** (non-slow subset) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **20 MCP tools** (16 governance + 4 context engine) |
| Domains | **8 shipped** (modular — filesystem-discovered from frontmatter, custom domains supported) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **145 principles + 764 methods + 18 references** (927 total) |
| Subagents | **10** (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Skills | **4** (`/compliance-review`, `/completion-sequence`, `/test-authoring`, `/content-enhancer`) |
| Hooks | **7** (PostToolUse CI, UserPromptSubmit governance+CE inject, PreToolUse governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM gate, PreToolUse pre-exit-plan-mode gate, PreToolUse content-security Layer 2) |
| CI | Last push: session-168. Session-171 changes unpushed. |

---

## Last Session (2026-05-14)

172. **Session-172 (2026-05-14): BACKLOG #162 Accounting Domain.**
   - **New domain shipped:** 8th governance domain — "Accounting" with 12 principles across 4 series (LE/EC/TC/RC), methods/CFR with 9 sections including QBO integration appendix and domain-tools ecosystem catalog.
   - **19 files changed:** 2 created (principles + CFR), 4 code files (extractor.py, config.py, domains.json, ai-instructions.md), 5 documentation files (README, ARCHITECTURE, SPECIFICATION, EXECUTION-FRAMEWORK, BACKLOG), 4 test files.
   - **14 new tests:** `TestGetDomainPrefixAccounting` (1), `TestAccountingCategorySeriesMap` (7), `TestAccountingPrincipleExtraction` (1), `TestAccountingDomainIntegration` (3), updated `TestDefaultDomains` (1 modified), benchmark queries (5 added).
   - **Extractor fix:** Substring collision in `category_mapping` — `le-series` matched `e-series` → "safety", `ec/tc/rc-series` matched `c-series` → "context". Fixed by adding accounting entries before shorter colliding patterns.
   - **Coherence audit:** 1D + 8M + 3C findings, all resolved. Propagated domain count 7→8 across SPECIFICATION.md, EXECUTION-FRAMEWORK.md. Added accounting to `_static_series` and `_static_skip` fallback lists.
   - **Double-check audit (3 subagents):** coherence-auditor (0D+3M+2C), code-reviewer (1H+3M), validator (27/28 pass). Fixed: ARCHITECTURE.md file tree (6→7 domain files, added title-22 entries), ai-instructions.md version pins + changelog entry for v4.0.6, substring collision regression test (4 accounting pairs added to `test_no_substring_collisions_in_ordering`), Success Criteria sections added to all 12 accounting principles.
   - **Tests:** 1724 passing (up from 1710). Index: 145 principles + 764 methods + 18 references (927 total).

---

## Previous Sessions

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
1. **Compliance Review #9** — due ~2026-05-22–2026-05-27 (10-15 days from Review #8 on 2026-05-12). Invoke `/compliance-review`.
2. **C-109 deferred-cadence audit** — due ~2026-05-25. See OPERATIONS.md.
3. **C-155 feedback loop analysis** — next run due ~2026-06-07. See OPERATIONS.md.
4. **Docker image rebuild** — sessions 168-172 changed src/ files. Rebuild and push.
5. **Context Engine re-index** — new accounting documents need indexing for `query_project` discovery.

**Trigger-gated (tracked in OPERATIONS.md):**
- **T-149** — CE-first compliance measurement (3-5 sessions, <85% activates Phase 2 hook). CE-First Phase 2 (grep/glob advisory hook) activates only if this fires.
- **T-152** — Subagent transcript isolation — upstream fix (Claude Code agentId in hook input)
- See OPERATIONS.md for T-019, T-049, T-106–T-113, T-119, T-134, T-143, T-145, T-161, T-163, C-078, C-109, C-155.

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
