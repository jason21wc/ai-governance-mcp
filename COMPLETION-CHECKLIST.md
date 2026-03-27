# Post-Change Completion Checklist

Per §5.1.6, run this project's completion sequence after changes. Say "run the completion sequence" to trigger.

## Code changes

1. `pytest tests/ -v` — full test suite
2. **Subagent review** — required for risky changes (enforced by pre-push quality gate hook):
   - New MCP tool or handler → code-reviewer + security-auditor
   - Changes to server.py, extractor.py, retrieval.py, config.py → code-reviewer
   - New file-handling code path → security-auditor
   - Content expansion (new principles/methods) → coherence-auditor + validator
   - Changes >5 files → code-reviewer
   - See §5.1.7 for full trigger table
3. **New code path check** (if adding code that reads files, parses external data, or handles user-controlled input):
   - [ ] Is the new code path included in `validate_content_security()` scan? (extractor.py)
   - [ ] Does it validate/sanitize file paths? (symlink protection, path traversal, size limits)
   - [ ] Does it use safe parsing? (`yaml.safe_load()`, not `yaml.load()`; `json.loads()`, not `eval()`)
   - [ ] Does it have dedicated tests? (NOT just passing through existing tests)
   - [ ] If it returns content to AI clients, is the content scanned for prompt injection?
4. Update SESSION-STATE.md (version, counts, summary)
5. Commit and push
6. Verify CI green (`gh run watch`)
7. Docker check: if `src/`, `pyproject.toml`, or `Dockerfile` changed since last image build → rebuild and push

## Content changes (governance documents)

1. `python -m ai_governance_mcp.extractor` — rebuild index
2. `pytest tests/ -v` — full test suite
3. Spot-check: `query_governance("new content topic")` → verify it surfaces
4. Reference doc staleness check: if project has reference docs (DATA-REFERENCE, PRODUCT-CONTEXT, etc.), verify `Last Verified` dates are current per §14.2
5. Update SESSION-STATE.md (version, counts, summary)
6. README check: if principle/method counts or domains changed → update README domain table
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

## Propagation awareness

When modifying shared project context, check whether changes need to propagate:
- **AGENTS.md** ↔ **CLAUDE.md**: shared content lives in AGENTS.md; Claude-specific content in CLAUDE.md. If you change project context (commands, structure, memory files), update AGENTS.md. If you change governance enforcement or subagent registry, update CLAUDE.md.

## Documentation-only changes (memory files, README)

1. Update SESSION-STATE.md if applicable
2. Commit and push
