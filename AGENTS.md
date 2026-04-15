# AI Governance MCP Server

**Description:** Semantic retrieval system for AI governance principles and methods.
**Framework:** AI Coding Methods
**Mode:** Standard

## Memory Files

| File | Purpose |
|------|---------|
| SESSION-STATE.md | Current position, next actions |
| BACKLOG.md | Discussion items and deferred work |
| PROJECT-MEMORY.md | Decisions, constraints, gates |
| LEARNING-LOG.md | Lessons learned |
| ARCHITECTURE.md | System design, data flow |
| workflows/COMPLETION-CHECKLIST.md | Post-change steps (say "run the completion sequence") |
| workflows/COMPLIANCE-REVIEW.md | Periodic governance health (say "run compliance review") |

## On Session Start

1. Load SESSION-STATE.md for current position
2. Prune SESSION-STATE.md if >300 lines (remove old summaries, route decisions/lessons)
3. Follow Next Actions listed there
4. Reference PROJECT-MEMORY.md for constraints and decisions
5. Check LEARNING-LOG.md before repeating past mistakes

## Key Commands

```bash
python -m ai_governance_mcp.extractor  # Rebuild index
pytest tests/ -v                        # Run tests
python -m ai_governance_mcp.server      # Run governance server
python -m ai_governance_mcp.context_engine.server  # Run CE server
docker build -t ai-governance-mcp .     # Build image
docker run -i --rm ai-governance-mcp    # Run container
```

## Project Structure

- `src/ai_governance_mcp/` — Governance server source
- `src/ai_governance_mcp/context_engine/` — Context Engine MCP (4 tools)
- `documents/` — Governance content (indexed)
- `documents/agents/` — Canonical agent templates (edit here first, then sync to `.claude/agents/`)
- `index/` — Generated embeddings
- `tests/` — Test suite

## Jurisdiction

AI Coding applies: Specify → Plan → Tasks → Implement. Record gates in PROJECT-MEMORY.md. Keep changes atomic (≤15 files).

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions.md for full activation protocol.*
