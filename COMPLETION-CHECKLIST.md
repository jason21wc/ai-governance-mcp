# Post-Change Completion Checklist

Per §5.1.6, run this project's completion sequence after changes. Say "run the completion sequence" to trigger.

> **Enforcement Tiers:** Items marked ENFORCED are backed by hooks, CI, or structural gates —
> non-compliance is physically blocked. Items marked BEST-EFFORT are advisory with ~85% expected
> compliance. Occasional misses on best-effort items are acceptable; misses on enforced items
> indicate a system failure. Per LEARNING-LOG: "advisory fails at 87%; structural blocking
> achieves near-100%." (See: normative drift under agentic pressure, arxiv 2603.14975)

## Code changes

### ENFORCED (structurally blocked if skipped)

1. **Tests run before push** — pre-push quality gate hook blocks `git push` if `pytest` not found in session transcript
2. **Subagent review for risky changes** — pre-push quality gate hook blocks push if core code changed without code-reviewer or security-auditor invocation:
   - New MCP tool or handler → code-reviewer + security-auditor
   - Changes to server.py, extractor.py, retrieval.py, config.py → code-reviewer
   - New file-handling code path → security-auditor
   - Content expansion (new principles/methods) → coherence-auditor + validator
   - Changes >5 files → code-reviewer
   - See §5.1.7 for full trigger table
3. **Governance evaluation before file modifications** — PreToolUse governance hook blocks Bash|Edit|Write until `evaluate_governance()` called
4. **Context Engine query before code changes** — PreToolUse governance hook blocks until `query_project()` called
5. **CI passes** — GitHub branch protection (when configured)
6. **README tool count matches actual** — `TestReadmePropagation` CI assertion

### BEST-EFFORT (advisory, ~85% compliance expected)

7. Tests written WITH implementation, not after (§5.2.2 — TDD recommended)
8. SESSION-STATE updated progressively during session, not just at end (§7.1)
9. Benchmark baseline captured before index/retrieval changes
10. **New code path security check** (if adding code that reads files, parses external data, or handles user-controlled input):
    - [ ] Is the new code path included in `validate_content_security()` scan? (extractor.py)
    - [ ] Does it validate/sanitize file paths? (symlink protection, path traversal, size limits)
    - [ ] Does it use safe parsing? (`yaml.safe_load()`, not `yaml.load()`; `json.loads()`, not `eval()`)
    - [ ] Does it have dedicated tests? (NOT just passing through existing tests)
    - [ ] If it returns content to AI clients, is the content scanned for prompt injection?
11. README/SPEC/ARCH propagation for domain counts, file trees, version references
12. Docker rebuild if `src/`, `pyproject.toml`, or `Dockerfile` changed

### ALWAYS (regardless of enforcement tier)

13. Update SESSION-STATE.md (version, counts, summary) — at minimum at session end
14. Commit and push
15. Verify CI green (`gh run watch`)

## Content changes (governance documents)

### ENFORCED

1. `python -m ai_governance_mcp.extractor` — rebuild index
2. `pytest tests/ -v` — full test suite

### BEST-EFFORT

3. Spot-check: `query_governance("new content topic")` → verify it surfaces
4. Reference doc staleness check per §14.2
5. README check: if principle/method counts or domains changed → update README domain table
6. Update SESSION-STATE.md
7. Commit and push
8. Verify CI green
9. Docker check: if content significantly changed or code also changed → rebuild and push

## Domain changes (adding/removing/renaming domains)

> **Renames change principle ID prefixes** — this is a breaking change.
> Downstream consumers keyed on IDs (tiers.json, benchmarks, feedback logs) will break.
> Prefer add-then-deprecate over in-place rename.
> If rename is necessary, update tiers.json, benchmarks, and feedback logs to use the new prefix before deploying.

> **`TestDomainConsistency` catches source-of-truth and enum/prefix consistency (items 1-5) at CI time.**
> Items 6-20 require manual verification.

**Source of truth:**
1. Update `documents/domains.json` (name, display_name, files, description, priority)

**Code surfaces:**
2. `src/ai_governance_mcp/config.py` — `_default_domains()` fallback
3. `src/ai_governance_mcp/server.py` — tool schema enums (`query_governance` + `get_domain_summary`)
4. `src/ai_governance_mcp/server.py` — handler-level `valid_domains` sets (separate from enums)
5. `src/ai_governance_mcp/extractor.py` — `DOMAIN_PREFIXES` class constant
6. `src/ai_governance_mcp/extractor.py` — `CATEGORY_SERIES_MAP` entries for new domain's categories
7. `src/ai_governance_mcp/extractor.py` — `is_series_header` keyword list in `_extract_principles_from_domain()` (if domain uses series headers)
8. `src/ai_governance_mcp/extractor.py` — `category_mapping` dict in `_get_category_from_section()` (if domain has category keywords). **IMPORTANT: Check for substring collisions** — longer series names MUST come before shorter ones in dict insertion order (e.g., `ka-series` before `a-series`). See Gotcha #33 in PROJECT-MEMORY.md.

**Test surfaces:**
9. `tests/test_config.py` — `TestDefaultDomains` count and name list
10. `tests/test_extractor.py` — `TestGetDomainPrefix` for new domain
11. `tests/test_extractor.py` — `TestCategorySeriesMap` assertions for new domain
12. `tests/test_server.py` — domain integration test class (follow `TestUiUxDomainIntegration`)
13. `tests/benchmarks/retrieval_quality.json` — benchmark queries for new domain

**Documentation:**
14. `SPECIFICATION.md` — domain count and table
15. `ARCHITECTURE.md` — domain count references and benchmark methodology
16. `README.md` — footer domain list
17. `PROJECT-MEMORY.md` — domain decisions section

**Verification:**
18. `python -m ai_governance_mcp.extractor` — rebuild index
19. Spot-check: verify new domain principles have correct `series_code` values (not null) in index
20. `pytest tests/ -v` — full test suite (includes `TestDomainConsistency`)
21. Update `SESSION-STATE.md` domain count

## Principle changes (adding/modifying constitutional or domain principles)

> **Per Systemic Thinking (Constitution):** Before adding a new principle, verify the frame.
> A new principle is justified only when an actual behavioral gap exists that existing principles
> and methods cannot cover. If the gap is discoverability (how principles relate to each other),
> the fix is cross-references, not a new principle. If the gap is enforcement (principles exist
> but aren't applied), the fix is hooks/enforcement, not more principles.

### BEST-EFFORT (advisory)

**Before writing the principle (see Part 9.8 Content Quality Framework for full procedure):**
1. **Admission Test (§9.8.1):** Pass all 6 questions — coverage, placement, derivation, evidence, enforceability, stability.
2. **Duplication Check (§9.8.2):** Query `query_governance()` and `query_project()` — does something already cover this at any level?
3. **Structural Requirements (§9.8.3):** Use the correct template for the content type.
4. **Concept Loss Prevention (§9.8.6):** If modifying/removing existing content, verify every concept has a home.

**After writing the principle:**
6. **S-Series compliance check:** Does the new/modified principle comply with all S-Series (safety) principles? Amendments that weaken safety constraints require heightened scrutiny: contrarian review + coherence audit + human sign-off.
7. **Contrarian review:** Mandatory for constitutional amendments. Apply the principle to its own creation — does it pass its own tests?
8. **Coherence audit:** Template compliance, voice consistency, legal analogy fits framework pattern, no contradictions with existing principles.
9. **Federal preemption cleanup:** If the new principle covers ground already partially stated in domain methods, add references up and trim duplication. Use Context Engine to find all scattered references.
10. **Version propagation:** Update `version` and `effective_date` in YAML frontmatter. Add version history entry.
11. **Index rebuild + spot-check:** `python -m ai_governance_mcp.extractor`, then verify the principle surfaces via `query_governance`.

## Plan-mode architecture decisions

> **Schema enforcement via template:** Advisory checklists are skipped ~15% of the time due to
> autoregressive forward-continuation bias (LEARNING-LOG 2026-03-28). The plan template addresses
> this structurally: required sections before the recommended approach make verification part of
> the generation flow rather than an optional interruption.

For architecture decisions, use the plan template at **`.claude/plan-template.md`**. The template puts contrarian review, research verification, and simpler-alternatives evaluation BEFORE the recommended approach — making them part of the forward generation path, not afterthoughts.

**Origin:** CE Phase 4 planning skipped contrarian review and research, leading to a plan that would have built RRF + cross-encoder reranking to fix a benchmark specification error. The contrarian then caught the original fix (rewriting 9 advisory sections) as itself being the Shifting the Burden pattern — better advisory language when the fix should be structural.

## Propagation awareness

When modifying shared project context, check whether changes need to propagate:
- **AGENTS.md** ↔ **CLAUDE.md**: shared content lives in AGENTS.md; Claude-specific content in CLAUDE.md. If you change project context (commands, structure, memory files), update AGENTS.md. If you change governance enforcement or subagent registry, update CLAUDE.md.

## Documentation-only changes (memory files, README)

1. Update SESSION-STATE.md if applicable
2. Commit and push
