# Session State

**Last Updated:** 2026-04-14
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Implementation complete — **v2.0.0 released** (Constitutional Framework Alignment)
- **Mode:** Standard
- **Active Task:** None.

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v2.0.0** (server + pyproject.toml + ARCHITECTURE) |
| Context Engine | **v2.0.0** (YAML frontmatter parsing, metadata boosting, heading breadcrumbs, chunk overlap, BAAI/bge-small-en-v1.5 384d (same model as governance server), metadata_filter, read-only mode, watcher daemon, service installer, project_path parameter) |
| Content | **v4.1.0** (Constitution — 24 principles: C:6, O:6, Q:4, G:5, S:3), **v3.26.6** (rules-of-procedure), **v2.37.0** (title-10-ai-coding-cfr), **v2.7.1** (ai-coding principles — 12), **v2.7.1** (multi-agent principles — 17), **v2.17.1** (multi-agent methods), **v1.4.1** (storytelling principles — 15), **v1.1.2** (storytelling methods), **v2.4.1** (multimodal-rag principles — 32), **v2.1.2** (multimodal-rag methods), **v1.2.0** (ui-ux principles — 20), **v1.0.1** (ui-ux methods), **v1.4.0** (kmpd principles — 10), **v1.2.1** (kmpd methods), **v2.6** (ai-instructions). **Filenames renamed to Constitutional naming** (Phase 4): `constitution.md`, `rules-of-procedure.md`, `title-NN-*.md`, `title-NN-*-cfr.md`. Versions in YAML frontmatter (since v3.20.0). |
| Tests | **1198 passing** (run `pytest tests/ -v` for current) |
| Coverage | Run `pytest --cov` for current (last known: governance ~90%, context engine ~65%) |
| Tools | **17 MCP tools** (13 governance + 4 context engine) |
| Domains | **7** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd) |
| License | **Apache-2.0** (code), **CC-BY-NC-ND-4.0** (framework content) |
| Index | **130 principles + 675 methods + 13 references** (818 total; see `tests/benchmarks/` for current totals) |
| Subagents | **10** — all installable via `install_agent` (code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach) |
| Hooks | **4** (PostToolUse CI check, UserPromptSubmit conditional governance+CE inject, PreToolUse hard-mode governance+CE check, PreToolUse pre-push quality gate) |
| CI | All green (3.10, 3.11, 3.12 + security + lint + content scan); pip-audit scoped to project deps |
| CE Benchmark | See `tests/benchmarks/ce_baseline_*.json` for current values (v2.0, 16 queries, semantic_weight=0.7) |
| CE Chunking | **tree-sitter-v2** (import-enriched) |

## Last Session (2026-04-14)

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

See BACKLOG.md for open items. Active priority: #78 (Compliance Review, next due ~2026-04-24).

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
