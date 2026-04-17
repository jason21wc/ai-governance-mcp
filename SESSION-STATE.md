# Session State

**Last Updated:** 2026-04-16 (session 108)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Phase 2 COMPLETE. All 6 steps shipped and verified. BACKLOG #91 fix-now items shipped (`7cd727f`).
- **Mode:** Standard
- **Active Task:** None — session-108 complete.

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, BAAI/bge-small-en-v1.5 384d (same model as governance server), metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v4.1.0** (Constitution — 24 principles: C:6, O:6, Q:4, G:5, S:3), **v3.26.7** (rules-of-procedure), **v2.38.0** (title-10-ai-coding-cfr), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.17.1** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.2** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.2** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v2.6** (ai-instructions). **Filenames renamed to Constitutional naming** (Phase 4): `constitution.md`, `rules-of-procedure.md`, `title-NN-*.md`, `title-NN-*-cfr.md`. Versions in YAML frontmatter (since v3.20.0). |
| Tests | **1284 passing** safe subset (`pytest tests/ -v -m "not slow"`); 20 embedding-mock tests fail when daemon is running (pre-existing — IPC client intercepts mock patches). Run `pytest tests/ -v` for full count. |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 676 methods + 13 references** (819 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **5** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate, PreToolUse pre-test OOM prevention gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Last Session (2026-04-16)

108. **Session-108: Phase 2 Verified + OOM Gate Hardened**
   - **WS1 (Phase 2 Step 6 — verification):** Daemon alive (PID 93280), IPC socket healthy, all MCP servers confirmed using IPC ("Using embedding server (IPC)" in logs). Governance servers: **85 MB** phys_footprint (down from ~800 MB, ~715 MB saved per instance). Model load time: **80ms** (was ~9s, 112x improvement). MRR: method=0.646, principle=0.750 (pass all thresholds). Method MRR drop from 0.711 predates Phase 2 (content changes). CE servers: 552-683 MB (tree-sitter + index data, no torch).
   - **WS2 (BACKLOG #91 fix-now items):** 6 improvements to OOM gate hook (`7cd727f`): ERR trap (fail-closed), jq→python3 fallback, PYTEST_CURRENT_TEST guard, secret redaction, log rotation (100KB cap), -k docs. 7 new tests (30 total). All pass.
   - **WS3 (housekeeping):** Updated SESSION-STATE, BACKLOG, PROJECT-MEMORY metrics.
   - **Pre-existing test issue noted:** 20 embedding-mock tests fail when daemon is running (IPC client intercepts mock patches). Not a regression — track as new BACKLOG item alongside the extractor dimensions bug.
   - **Governance:** `gov-d33150d934df` (S-Series false positive on "secret" — keyword, no principles).

107. **Plan-Only — Phase 2 Verification + OOM Gate Hardening** — Plan created at `~/.claude/plans/nifty-twirling-pike.md`. Contrarian found stale MRR baselines (0.694→0.711 actual), silent fallback risk, and extractor dimensions bug.

*Sessions 101-106 pruned per §7.1.5. Decisions in PROJECT-MEMORY.md, lessons in LEARNING-LOG.md. Full history via `git log`.*

## Next Actions

**Immediate:**

1. **Fix 20 embedding-mock test failures.** When daemon is running, `EmbeddingClient.available()` returns True, intercepting the `SentenceTransformer` mock patch. Tests need to either: (a) set `AI_CONTEXT_ENGINE_EMBED_SOCKET=none` in test env, or (b) mock `EmbeddingClient.available` to return False. Track alongside extractor dimensions bug in BACKLOG.
2. **Track extractor dimensions bug in BACKLOG.** `extractor.py:106-108` calls `get_sentence_embedding_dimension()` on `self.model` which could be an `EmbeddingClient` (no such method). Crashes index rebuilds when daemon is running.

**Short-term:**
- **BACKLOG #78 (Compliance Review)** — next due ~2026-04-24.
- **Phase 0 48h soak** — daily measurement plist at 04:00. Check `~/.context-engine/logs/phase0-baseline.txt` for first data point.

**BACKLOG #49 status:** Phase 2 COMPLETE and verified. Forcing functions continue running (daily plist + deny log + calendar trigger 2026-06-15).

See BACKLOG.md for the full list of open items.

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
