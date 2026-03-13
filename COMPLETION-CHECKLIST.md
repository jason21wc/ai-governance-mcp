# Post-Change Completion Checklist

Per §5.1.6, run this project's completion sequence after changes. Say "run the completion sequence" to trigger.

## Code changes

1. `pytest tests/ -v` — full test suite
2. Code review (code-reviewer subagent) if substantial
3. Update SESSION-STATE.md (version, counts, summary)
4. Commit and push
5. Verify CI green (`gh run watch`)
6. Docker check: if `src/`, `pyproject.toml`, or `Dockerfile` changed since last image build → rebuild and push

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

1. Update `documents/domains.json`
2. Update `src/ai_governance_mcp/config.py` `_default_domains()` fallback
3. Update `src/ai_governance_mcp/server.py` tool schema enums (query_governance, get_domain_summary)
4. Update `tests/test_config.py` domain count assertion and name list
5. Update `SPECIFICATION.md` domain count and table
6. Update `ARCHITECTURE.md` domain count references and benchmark methodology
7. Update `README.md` footer domain list
8. `python -m ai_governance_mcp.extractor` — rebuild index
9. `pytest tests/ -v` — full test suite
10. Update SESSION-STATE.md domain count

## Documentation-only changes (memory files, README)

1. Update SESSION-STATE.md if applicable
2. Commit and push
