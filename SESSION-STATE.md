# Session State

**Last Updated:** 2026-04-15 (session 105)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Session-106 complete. Phase 0 **shipped** (commit `a86d571`). Phase 2 **planned and approved** (plan `jiggly-honking-cascade.md`, Path A activated). Implementation starts next session at Step 1 (`embedding_ipc.py`).
- **Mode:** Standard
- **Active Task:** Phase 2 Step 1 — `embedding_ipc.py` (EmbeddingServer + EmbeddingClient + queue worker + tests). See plan file for full 6-step implementation order.

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, BAAI/bge-small-en-v1.5 384d (same model as governance server), metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v4.1.0** (Constitution — 24 principles: C:6, O:6, Q:4, G:5, S:3), **v3.26.7** (rules-of-procedure), **v2.38.0** (title-10-ai-coding-cfr), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.17.1** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.2** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.2** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v2.6** (ai-instructions). **Filenames renamed to Constitutional naming** (Phase 4): `constitution.md`, `rules-of-procedure.md`, `title-NN-*.md`, `title-NN-*-cfr.md`. Versions in YAML frontmatter (since v3.20.0). |
| Tests | **1255 passing** (session-106: +64 Phase 0 tests on 1191 baseline; run `pytest tests/ -v -m "not slow"` for current) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 675 methods + 13 references** (818 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **5** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM prevention gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Last Session (2026-04-15)

105. **Backlog #49 Reset + Structural OOM Prevention Gate**
   - **Inherited state:** previous session crashed mid-pytest with a 10-file ONNX backend diff in the working tree. Root-cause investigation revealed `sentence-transformers` `backend="onnx"` does NOT avoid torch import (transitive via `transformers`); envelope math showed ~2% of the 27 GB symptom. Two contrarian passes validated rejection.
   - **Actions:** Stopped stale watcher daemon (PID 1302 → respawned 6846 → 7082, disabled launchd plist, later reloaded at new PID 11077). Preserved ONNX diff at `staging/onnx-backend-attempt-2026-04-15.{patch,md}`. Rolled back 10 files. Verified HEAD green (1168 passing, 30 deselected). Cherry-picked stale-default fix (commit `b702296`): `indexer.py` defaults nomic→bge-small, 768d→384d. Built `.claude/hooks/pre-test-oom-gate.sh` (PreToolUse Bash hook) + **23 unit tests** at `tests/test_pre_test_oom_gate_hook.py` + registered in `settings.json` (hook count 4→5). Final full safe-subset run: **1191 passed, 30 deselected** (baseline 1168 + 23 hook tests).
   - **Backlog #49 reframed:** Status 2026-04-15 block added with explored/shipped/remaining sections + three-trigger forcing function (activity: ≥3 hook denies; capacity: 6th torch process proposal; calendar: 2026-06-15). Design spike deferred with two candidates: shared IPC service OR direct `optimum+tokenizers` layer skipping transformers.
   - **LEARNING-LOG entry:** "Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)" — 2-cause framing (stale daemon + no structural gate), cites `meta-core-systemic-thinking` and "Hard-Mode Hooks" precedent.
   - **Plan + contrarian reviews:** `~/.claude/plans/giggly-humming-starlight.md`. Two contrarian-reviewer passes + one coherence-auditor pass. First contrarian rejected partial-win framing; second validated revised direction with 4 actionable fixes (all applied).
   - **Governance:** `gov-1280a6eae041` (reconstruction), `gov-9115af02fc89` (plan rewrite). Subagent battery completed: contrarian×2 (partial-win rejection + revised-plan pressure-test), coherence-auditor×2 (plan file + shipped artifacts two-pass), validator×2 (12-criteria plan pass on both shipped state and after-fixes state), code-reviewer (14 findings, 7 actioned), security-auditor (2 LOW, 1 actioned). All findings addressed via structured Agree/Modify/Reject table.
   - **Double-check outcomes:** First coherence+validator pass → 2 HIGH + 4 MEDIUM + 3 LOW + 2 NIT, all addressed. Second coherence+validator pass → 0 HIGH, 1 MEDIUM (COMPLIANCE-REVIEW Check 6b missing) + 1 NIT (`PID_PATH` dead var), both addressed. **COMPLIANCE-REVIEW.md Check 1 updated to 5 hooks; new Check 6b added for the BACKLOG #49 forcing-function activity trigger.** Caught real bug: `printf %q` on bash 3.2 was byte-escaping unicode bullets in `SIGNALS` → deny log UTF-8 corruption; fixed to plain ASCII key=value format. `TestDenyLogSideEffect` test class added to catch future regressions of this class.
   - **Final state:** 1191 tests passing (+23 hook tests on 1168 baseline), 30 deselected, 0 OOM events, 5 hooks registered, daemon PID 11077 running on new code with `BAAI/bge-small-en-v1.5` / 384d defaults. Commit `b702296` landed. Other files (hook script, hook tests, settings.json, BACKLOG, LEARNING-LOG, SESSION-STATE, COMPLIANCE-REVIEW, indexer.py allowlist comment, staging artifacts) staged but not committed — awaiting user decision.
   - **Follow-up items captured in BACKLOG #91:** 10 hook-hardening and ops items from the session-end brainstorm (deny-log rotation, jq fail-open guard, hook-timeout contract, plan-file preservation, etc.). None are blockers.
   - **Self-audit finding (2026-04-15, user-caught):** bulk-logging all 10 brainstorm items to BACKLOG violated CLAUDE.md Defer-vs-Fix rule (`CLAUDE.md:52-63`, `rules-of-procedure §7.11`). 7 of the 10 sub-items met fix-now criteria (≤1 file, unambiguous, no cascade) and should have been fixed in session-105, not deferred. BACKLOG #91 has been reclassified with `[FIX-NOW]` / `[ASK]` / `[DEFER]` tags per the audit. **Session 106 should pick up the 7 [FIX-NOW] items as immediate work before doing anything else.** New LEARNING-LOG entry "Session-End Deferral Bias (2026-04-15)" captures the pattern.

104. **Prospective Memory + Platform Memory Boundary**
   - **Prospective Memory (v2.38.0):** Added as 6th cognitive type in §7.0.2 taxonomy, mapped to BACKLOG.md. Root cause: prospective memory (intentions) was homeless, stored in working memory (SESSION-STATE), contributing to 1,441-line bloat. Corrected CoALA attribution ("extending" not "from"). Fixed 3 pre-existing stale references (§7.5.1 "CoALA 4-type", Appendix L.1 "three-type", PROJECT-MEMORY "Fifth"). Added Reference Memory row to Overview table.
   - **Platform Memory Hands-Off (v3.26.7):** Evolved ADR-10 from "pointer only" to "hands off." Framework files are authoritative; LLM platform memory is the platform's concern. CLAUDE.md is the bridge. Rewrote Appendix G.5. Filled 2 gaps previously only in Claude Code memory: anticipatory backlog review rule (→ BACKLOG.md), dogfood subagent instruction (→ CLAUDE.md). Cleaned MEMORY.md to minimal bridge.
   - **6-agent review battery:** 2 contrarian (PROCEED WITH REQUIRED CHANGES → all findings fixed), 2 coherence (7 findings → all fixed), 1 validator (6/7 PASS, 1 FAIL on CoALA attribution → fixed).
   - **Governance:** `gov-b1edf6f3bf5c`, `gov-a1dc1aaeec8b`.
   - **Tests:** 1198 passing.

103. **Memory File Lifecycle Fix + Framework Propagation + Permission Architecture Rewrite**
   - **SESSION-STATE cleanup:** 1,441→54 lines. Backlog separated to BACKLOG.md (499 lines). Security Currency moved to COMPLIANCE-REVIEW.md.
   - **Structural prevention:** Session lifecycle instructions added to CLAUDE.md, AGENTS.md, MEMORY.md. Completion Checklist item 16 updated ("Update and prune"). COMPLIANCE-REVIEW Check 8 (backlog staleness) + V-005 (pruning verification) added.
   - **CFR updates:** New §7.1.6 (Backlog File Structure template). §7.6.1/§7.6.2 strengthened. §1.5.2 Standard Kit expanded (4→8 files). §7.0.4 distillation triggers expanded (BACKLOG.md 600-line review). §7.0.2 "three"→"five" cognitive types fixed. Appendix L.8 updated. Version: v2.37.0.
   - **A.5 Permission Architecture rewrite:** Solo developer as default (user-level single source of truth, project-local empty). Four principles (deny credentials, deny force push, ask governance files, allow everything routine). Cross-repo hook caveat + broad wildcard trade-off documented. A.5.3 git checkout contradiction fixed. Accretion threshold kept at 50.
   - **3-agent review battery:** Contrarian (PROCEED WITH CAUTION → all 3 findings fixed), validator (10/10 PASS), coherence auditor (4 Misleading → all fixed).
   - **LEARNING-LOG:** Two-cause framing (wrong surface + incomplete instruction). V-005 monitors whether advisory is sufficient.
   - **Governance:** `gov-3647578d83e4`, `gov-4161c87b2faa`, `gov-27d43175eded`, `gov-fdc3b899bc2c`, `gov-1bcdde1fc826`, `gov-26b750a21fc4`.
   - **Tests:** 1198 passing. Plan: `.claude/plans/stateful-imagining-matsumoto.md`.

102. **Compliance Review #2 + Canary Evaluation Redesign** — 7/7 checks passed. Canary evaluation redesigned (human→validator subagent). V-004: contrarian escalation deferred per user. Governance: `gov-428138c5b82d`.

101. **Context Engine Tool Selection Improvement** — Tool description rewrite + SERVER_INSTRUCTIONS scenarios + CLAUDE.md CE vs Grep criteria. 3-surface approach (dropped tiers.json + AGENTS.md per contrarian). Tests: 1198 passing. Governance: `gov-99c22976df80`, `gov-aa29a46bfa7e`, `gov-1cd425aa6027`.

*Previous session summaries pruned per §7.1.5 (session state is transient). Decisions and lessons routed to PROJECT-MEMORY.md and LEARNING-LOG.md. Full history available via `git log`.*

## Next Actions

**Immediate (next session — Phase 2 implementation):**

1. **Phase 2 Step 1: `embedding_ipc.py`** — EmbeddingServer (AF_UNIX socket, single-worker queue, JSON+base64 protocol) + EmbeddingClient (.encode/.predict matching SentenceTransformer/CrossEncoder signatures) + `test_embedding_ipc.py`. Security hardening: socket 0o600 permissions, input size limits, path containment. Est. 4-6h. Plan: `~/.claude/plans/jiggly-honking-cascade.md`.
2. **Phase 2 Steps 2-6** — wire into daemon, governance server, CE server, add CrossEncoder to daemon, measure memory. Est. 12-17h over 1-2 additional sessions.
3. **BACKLOG #91 [FIX-NOW] sub-items** (7 items deferred from session-105). Still valid. Can interleave or handle in a separate session.

**Short-term:**
- **BACKLOG #78 (Compliance Review)** — next due ~2026-04-24. First exercise of Check 6b + 6b.2 (Phase 0 outcome trigger).
- **Phase 0 48h soak (Verification step 10)** — the daily measurement plist runs at 04:00. First automated data point expected 2026-04-16. Slope capture script (nohup PID 77563) may have completed — check `~/.context-engine/logs/phase0-baseline.txt`.

**BACKLOG #49 status:** Phase 2 activated by user decision (Path A). Forcing function NOT overridden — it continues running (daily measurement plist stays active as ongoing monitoring even after Phase 2 ships).

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
