# AI Governance MCP Server

**Description:** Semantic retrieval system for AI governance principles and methods.
**Framework:** AI Coding Methods v2.27.0
**Mode:** Standard

## Memory Files

| File | Purpose |
|------|---------|
| SESSION-STATE.md | Current position, next actions |
| PROJECT-MEMORY.md | Decisions, constraints, gates |
| LEARNING-LOG.md | Lessons learned |
| ARCHITECTURE.md | System design, data flow |
| workflows/COMPLETION-CHECKLIST.md | Post-change steps (say "run the completion sequence") |
| workflows/COMPLIANCE-REVIEW.md | Periodic governance health (say "run compliance review") |

## On Session Start

1. Load SESSION-STATE.md for current position
2. Follow Next Actions listed there
3. Reference PROJECT-MEMORY.md for constraints and decisions
4. Check LEARNING-LOG.md before repeating past mistakes

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
