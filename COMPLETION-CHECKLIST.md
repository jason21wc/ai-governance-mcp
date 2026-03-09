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
4. Update SESSION-STATE.md (version, counts, summary)
5. README check: if principle/method counts or domains changed → update README domain table
6. Commit and push
7. Verify CI green
8. Docker check: if content significantly changed or code also changed → rebuild and push

## Documentation-only changes (memory files, README)

1. Update SESSION-STATE.md if applicable
2. Commit and push
