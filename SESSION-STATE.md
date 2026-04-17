# Session State

**Last Updated:** 2026-04-17 (session 110)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Session-110 complete. CFR v2.38.1 landed + Phase 2 soak passed.
- **Mode:** Standard
- **Active Task:** None.

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, BAAI/bge-small-en-v1.5 384d (same model as governance server), metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v4.1.0** (Constitution — 24 principles: C:6, O:6, Q:4, G:5, S:3), **v3.26.7** (rules-of-procedure), **v2.38.0** (title-10-ai-coding-cfr), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.17.1** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.2** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.2** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v2.6** (ai-instructions). **Filenames renamed to Constitutional naming** (Phase 4): `constitution.md`, `rules-of-procedure.md`, `title-NN-*.md`, `title-NN-*-cfr.md`. Versions in YAML frontmatter (since v3.20.0). |
| Tests | **1308 passing** safe subset (`pytest tests/ -v -m "not slow"`); embedding-mock tests no longer intercepted by daemon (autouse conftest fixture forces local path). Run `pytest tests/ -v` for full count. |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 676 methods + 13 references** (819 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **5** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM prevention gate) |
| CI | **Green.** Both session-106 pre-existing failures fixed and verified on main in session-109: reconnect flake resolved by releasing accepted conns on shutdown; bandit exit-1 resolved by suppressing non-crypto B311 jitter and cleaning up unused B506 nosec on `yaml.safe_load()`. Last push: `5c890aa` (2m55s CI, 1m17s CodeQL). |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Last Session (2026-04-17)

110. **Session-110: CFR v2.38.1 — Dynamic A.5.5 Threshold + Phase 2 Soak (4 commits)**
   - **Problem:** Fixed 50-entry permission trigger fired on legitimate baseline growth (MCP ecosystem, new memory files) across 2+ reviews with "category-legitimate, not accretion" disposition. Symptom-level patch (prune to fit) would have masked the structural issue.
   - **Root cause (systemic reframe):** entry count is a proxy for accretion, not the signal itself. Proxies drift when the ecosystem grows. Fixed thresholds on moving references produce false positives until ignored.
   - **Fix (`5c6ae84`):** CFR §A.5.5 v2.38.1 replaces fixed-50 with `post_cleanup_baseline + 20`, reset after each cleanup. Design mirrors multi-agent §6.4 (Autonomous Drift Monitoring) + multimodal-rag §6.3 (Drift Detection). Added one-shots-found per review as second-order signal. §A.5.6 defers to §A.5.5 for single source of truth. COMPLIANCE-REVIEW.md Check 7 expanded with 6-step procedure + 4 new table columns (Current Count / Baseline / One-shots / Next Trigger).
   - **Audit (pre-commit):** scanned `~/.claude/settings.json` (123 allow entries) per §A.5.6 one-shot definition — **0 one-shots found**. Also applied systemic-thinking pass ("over-specific → generalize") — nothing fit; every narrower pattern is intentionally narrower than its wildcard parent to exclude a dangerous sibling (`git push`, `pip install`, `docker push`, `gh auth login`). List is pattern-dominated and disciplined; confirms the reframe is structural, not a patch.
   - **Lessons:** LEARNING-LOG "Thresholds Are Signal Detectors, Not Count Gates" — rule for future threshold design (specify the signal, not the unit).
   - **First Baseline/Next Trigger:** recorded at next compliance review (~2026-04-27, Review #4), per v2.38.1 initial-adoption clause.
   - **Batch-window rule (`d342bdd` + auto-memory):** captured the anti-pattern of stacking version bumps on unpushed commits. Durable feedback rule persisted to `~/.claude/projects/.../memory/feedback_unpushed_version_bumps.md` (indexed in MEMORY.md, loads every turn).
   - **Phase 2 soak:** PHASE2_TRIGGERED marker CLEAR. Most recent T1 fire (2026-04-17T02:07Z) self-resolved in 44 sec when sliding-window slope stabilized post-recalibration. No escalation. Observation: `phase0-measurements.log` hasn't written since 02:08Z — daily 04:00 PDT plist should have fired at least once since; verify at Review #4 Check 6b.
   - **Governance:** `gov-e7a5904991cc` (plan + execution), `gov-00bfd4008438` (close-out + drift audit) — both PROCEED, no S-Series. Principles cited: `meta-core-systemic-thinking`, `meta-method-domain-staleness-thresholds`, `coding-method-cleanup-triggers`, `meta-method-documentation-drift-detection`, `coding-method-session-end-procedure`.
   - **Plan:** `~/.claude/plans/should-we-create-a-vectorized-scott.md` (approved, executed, marked Complete).

109. **Session-109: Session-108 Immediate Items Closed + Compliance Review #3 (8 commits)**
   - **#3+#4 (`00b1be8`):** Added `get_sentence_embedding_dimension()` to `EmbeddingClient` (server-side `dimension` op, lazy-cached via dummy encode probe); autouse conftest fixture sets `AI_CONTEXT_ENGINE_EMBED_SOCKET=none` so a live daemon doesn't intercept `SentenceTransformer` mocks; made `_resolve_socket_path` treat `"none"` as unset. Unblocks extractor.py:106-108 dimensions call when daemon is running and restores ~20 previously-intercepted embedding-mock tests.
   - **#2 (`1cf416d`):** Real bandit exit-1 cause was B311 `random.uniform` for daemon restart jitter (non-crypto) — added `# nosec B311`. Also cleaned up unused `# nosec B506` from `yaml.safe_load()` calls (B506 targets `yaml.load`, not `safe_load`); moved prose out of nosec lines so bandit doesn't tokenize it as test IDs.
   - **#1 (`953a005`):** Reconnect test flake was NOT "CI resource constraints" — it was a deterministic race between two matched 30s timers (server handler's `result_event.wait` vs client's `conn.settimeout`). Fix: track accepted conns in `EmbeddingServer`, SHUT_RDWR them on shutdown so handlers exit recv promptly. Test runtime dropped 33.54s→3.53s.
   - **Code review hardening (`0b3af90`, `7b6352d`):** Closed accept-race window (stop_event recheck under `_conns_lock`), split OSError/ValueError exception handling so non-shutdown errors are logged not swallowed, dropped assumption that `encode_fn` accepts `normalize_embeddings` kwarg, replaced hedge assertion with deterministic 1s spin-wait, documented autouse fixture opt-out pattern.
   - **Docs (`603d56f`):** session-109 state + LEARNING-LOG "Matched Timeouts on Both Sides of an RPC" lesson (`meta-core-systemic-thinking` — rejected "flaky due to CI resource constraints" framing as symptom-level).
   - **Compliance Review #3 (`ca59dcd`):** 10/10 ongoing checks pass after 3 FAIL→FIXED: (1) Check 4 LEARNING-LOG "Passive MCP Instructions" marked ACTIVE; (2) Check 6b.2 stale PHASE2_TRIGGERED marker cleared; (3) Check 8 closed BACKLOG #92/#93 removed. Validator subagent audit 8/9 PASS.
   - **Phase 2 measurement recalibration (`5c890aa`):** Phase 0 measurement plist was calibrated against pre-Phase-0 references; Phase 2 moved torch+models INTO the watcher (per-process footprint up, cross-process total down). Flipped Trigger 1 from verify-fix semantics ("steady dropped ≥40%") to regression-detect semantics ("steady grew ≥50%"); raised Trigger 3 peak threshold 3072→7500 MB. Baseline file updated with post-Phase-2 values. Script now exits 0 clean.
   - **Permissions update:** Added 18 entries to `~/.claude/settings.json` allow list — Edit/Write for memory files (SESSION-STATE/LEARNING-LOG/PROJECT-MEMORY/BACKLOG + user auto-memory) and 8 read-only Bash utilities (sleep/stat/file/which/env/uname/du/tree). 123 total entries — over CFR A.5.5 threshold of 50, prune pass deferred to next compliance review.
   - **Net:** safe subset 1284→1308 (+24: 3 dimension tests, 1 regression test, +20 unblocked mock tests). Full test runtime ~70s→~41s (flake alone was 30s of every run).
   - **Governance:** `gov-2c2519ada107` (session start), `gov-ce3f9d35b287` (compliance review fixes) — both PROCEED, no S-Series.

108. **Session-108: Phase 2 Verified + OOM Gate Hardened**
   - **WS1 (Phase 2 Step 6 — verification):** Daemon alive (PID 93280), IPC socket healthy, all MCP servers confirmed using IPC ("Using embedding server (IPC)" in logs). Governance servers: **85 MB** phys_footprint (down from ~800 MB, ~715 MB saved per instance). Model load time: **80ms** (was ~9s, 112x improvement). MRR: method=0.646, principle=0.750 (pass all thresholds). Method MRR drop from 0.711 predates Phase 2 (content changes). CE servers: 552-683 MB (tree-sitter + index data, no torch).
   - **WS2 (BACKLOG #91 fix-now items):** 6 improvements to OOM gate hook (`7cd727f`): ERR trap (fail-closed), jq→python3 fallback, PYTEST_CURRENT_TEST guard, secret redaction, log rotation (100KB cap), -k docs. 7 new tests (30 total). All pass.
   - **WS3 (housekeeping):** Updated SESSION-STATE, BACKLOG, PROJECT-MEMORY metrics. Cross-platform `stat` fix for log rotation on Linux CI (`1d73fd1`).
   - **CI status:** 2 pre-existing failures identified (both present since session-106 push): (1) `test_client_reconnects_after_server_restart` flaky worker timeout on CI; (2) bandit `nosec` exit code 1. Neither from session-108 changes. Log rotation test was failing on Linux CI (`stat -f%z` macOS-only) — fixed with `stat -c%s` fallback.
   - **Pre-existing test issue noted:** 20 embedding-mock tests fail when daemon is running locally (IPC client intercepts mock patches). CI doesn't have a daemon, so these pass there.
   - **Governance:** `gov-d33150d934df` (S-Series false positive on "secret" — keyword, no principles).

107. **Plan-Only — Phase 2 Verification + OOM Gate Hardening** — Plan created at `~/.claude/plans/nifty-twirling-pike.md`. Contrarian found stale MRR baselines (0.694→0.711 actual), silent fallback risk, and extractor dimensions bug.

*Sessions 101-106 pruned per §7.1.5. Decisions in PROJECT-MEMORY.md, lessons in LEARNING-LOG.md. Full history via `git log`.*

## Next Actions

**Immediate:** None.

**Short-term:**
- **BACKLOG #78 (Compliance Review)** — next due ~2026-04-27 (10-15 days from Review #3 on 2026-04-17).
- **CFR A.5.5 permissions prune** — `~/.claude/settings.json` has 123 allow entries. Per v2.38.1 dynamic threshold (`post_cleanup_baseline + 20`), the first Baseline and Next Trigger are recorded at the next compliance review (Check 7). Initial audit performed 2026-04-17 found 0 one-shots — list is pattern-dominated.
- **Phase 2 soak** — daily measurement plist at 04:00 now calibrated for post-Phase-2 architecture. Review `~/.context-engine/logs/phase0-measurements.log` weekly for Trigger 4 cross-process drift. **Session-110 check (2026-04-17):** marker clear, no escalation; but log hasn't written since 02:08Z — verify plist health at Review #4 Check 6b.

**BACKLOG #49 status:** Phase 2 COMPLETE and verified. Phase 0 forcing functions retired/recalibrated in session-109.

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
