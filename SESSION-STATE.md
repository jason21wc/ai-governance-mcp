# Session State

**Last Updated:** 2026-02-01
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position

- **Phase:** Maintenance
- **Mode:** Standard
- **Active Task:** None
- **Blocker:** None

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.7.0** (server), **v2.3** (Constitution), **v2.5.0** (ai-coding-methods), **v2.10.0** (multi-agent-methods), **v1.0.0** (multimodal-rag) |
| Tests | **365 passing** |
| Coverage | ~90% |
| Tools | **11 MCP tools** |
| Domains | **5** (constitution, ai-coding, multi-agent, storytelling, multimodal-rag) |
| Index | **99 principles + 351 methods (450 total)** |

## Recent Session (2026-02-01)

### Governance Trigger Criteria — Skip-List Inversion (v1.7.0)

Replaced vague "significant action" governance trigger criteria with a deny-by-default skip-list approach across all operational instruction surfaces.

**Problem:** "Significant action" was subjective and circular — the AI decided when to check its own oversight. The project's own principles (`meta-operational-explicit-over-implicit`, `meta-governance-measurable-success-criteria`) argued against it.

**Solution:** Inverted from positive-list ("evaluate for these 7 actions") to skip-list-only ("evaluate for everything UNLESS it is one of these 4 exceptions"):
- Reading files, searching, or exploring code
- Answering questions that do not involve security-sensitive information
- Trivial formatting (whitespace or comment text changes that do not alter behavior)
- Human user explicitly says "skip governance" with documented reason

**Files changed (7):**

| File | Changes |
|------|---------|
| `src/ai_governance_mcp/server.py` | SERVER_INSTRUCTIONS, GOVERNANCE_REMINDER, `evaluate_governance` tool description, 4 operational strings |
| `.claude/agents/orchestrator.md` | Skip list, description, body references |
| `documents/agents/orchestrator.md` | Template copy — same changes |
| `CLAUDE.md` | Mandatory checkpoints section |
| `README.md` | Orchestrator description |
| `src/ai_governance_mcp/__init__.py` | Version bump to v1.7.0 |

**Key improvements from contrarian review:**
- All three instruction surfaces (SERVER_INSTRUCTIONS, CLAUDE.md, orchestrator.md) now carry identical skip lists
- "When in doubt, evaluate" catch-all added to prevent safe-harbor reasoning
- "Skip governance" bypass requires "documented reason" everywhere (was inconsistent)
- "Answering questions" narrowed to exclude security-sensitive information
- GOVERNANCE_REMINDER updated to reference skip-list logic
- `evaluate_governance` tool description now states when to call it

**Tests:** 341 passed (24 slow deselected). SERVER_INSTRUCTIONS validation passed.

## Previous Session (2026-01-30)

### Prompt Engineering Refinements — Methods v3.7.0

Added three targeted improvements to Title 11 (Prompt Engineering Techniques) based on gap analysis from @alex_prompter thread review.

**Commit:**
- `5cdd745` — `content: Add prompt engineering refinements to methods v3.7.0`

| Change | Description |
|--------|-------------|
| §11.1.4 Few-Shot Chain-of-Thought | New subsection with worked examples template, Wei et al. 2022 basis, contrast with standard few-shot |
| Graduated Framing Model (§11.3.2) | Context-dependent framing table: absolute negatives for safety, mixed for boundaries, positive for general |
| Part 11.7 Model Parameter Guidance | Temperature and top-p ranges, model-dependency caveat, when tuning matters vs. defaults |

**Index:** Rebuilt to 450 items (99 principles + 351 methods). All new content discoverable via retrieval (top scores 0.77–0.91).

**Tests:** 365 passing.

### CI Fix — real_index Test Timeouts

All `@pytest.mark.real_index` test classes caused `httpx.ReadTimeout` on CI runners. These tests load sentence-transformers + cross-encoder ML models which time out during download on GitHub Actions.

**Commits:**
- `6355434` — `fix(ci): Mark real_index tests as slow to skip in CI`
- `17f1609` — `fix(ci): Mark all real_index tests as slow, add post-push CI hook`

**Fix:** Added `@pytest.mark.slow` to all 5 `real_index` classes across `test_retrieval_integration.py` (1 class, 8 tests) and `test_retrieval_quality.py` (4 classes, 13 tests). CI deselects 24 tests, 341 selected — all passing. CI green on `17f1609` and `737edee`.

### Post-Push CI Hook

Added Claude Code hook to automatically surface CI status after `git push`.

| File | Purpose |
|------|---------|
| `.claude/settings.json` | `PostToolUse` hook config on `Bash` matcher |
| `.claude/hooks/post-push-ci-check.sh` | Detects git push, waits 5s, fetches latest CI run via `gh run list` |

Hook takes effect on next session start (config is snapshotted at session init).

## Previous Session (2026-01-26)

### Security Hardening v2 — Prompt Injection Defenses

Implemented balanced 80/20 security hardening responding to ike.io exploit disclosure:

**Commits:**
- `14e69f5` — `security: Harden prompt injection defenses (v2)`
- `560bad3` — `fix(ci): Refine content security patterns to reduce false positives`
- `096fb95` — `fix(ci): Use output check instead of exit code for security patterns`

| Change | Description |
|--------|-------------|
| Example bypass fix | CRITICAL patterns now detected even with "example" in line context |
| Unicode normalization | NFKC + invisible char stripping prevents homoglyph attacks |
| SERVER_INSTRUCTIONS validation | Runtime check at module load for compromised instructions |
| Domain description scanning | `domains.json` descriptions validated during extraction |
| CI pattern refinement | Reduced false positives on legitimate documentation |

**New tests added (10):**
- `TestContentSecurityPatterns` (2) — Example bypass behavior
- `TestUnicodeNormalization` (4) — NFKC and invisible char handling
- `TestServerInstructionsValidation` (2) — Runtime validation
- `TestDomainDescriptionValidation` (2) — domains.json scanning

**CI improvements:**
- Added `server.py` and `domains.json` to scan targets
- Refined patterns to exclude documentation contexts (Watch for, example, Python regexes)
- Fixed pipeline logic: use `[ -n "$OUTPUT" ]` instead of exit code

**Deferred (high false-positive risk):**
- "supersedes"/"overrides" patterns (6 legitimate uses in docs)
- "from now on" pattern (too common in normal text)
- Scan inside code blocks (docs show attack examples)

## Older Sessions

- **2026-01-25:** Security hardening v1 — Initial ike.io response (commit `e934a5f`)

## Next Actions

1. **(Optional)** Implement cosign for Docker image signing
2. **(Optional)** Develop storytelling coaching playbook
3. **(Optional)** Add platform-specific playbooks (TikTok, LinkedIn, long-form)
4. **(Optional)** Expand multimodal-rag with video retrieval (Phase 2)
5. **(Optional)** Add image generation domain when reliable methods exist

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
