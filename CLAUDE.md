# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Coding Methods v2.0.0

## On Session Start

1. Load SESSION-STATE.md for current position
2. Follow Next Actions listed there
3. Reference PROJECT-MEMORY.md for constraints and decisions

## Memory (Cognitive Types)

| Type | File | Purpose |
|------|------|---------|
| Working | SESSION-STATE.md | Current position, next actions |
| Semantic | PROJECT-MEMORY.md | Decisions, architecture, gates |
| Episodic | LEARNING-LOG.md | Lessons learned |

## Governance Integration

This project IS the AI Governance MCP. Use these tools:

| Tool | Purpose |
|------|---------|
| `query_governance` | Get principles for current task |
| `get_principle` | Get full content by ID |
| `list_domains` | See available domains |

## Key Commands

```bash
python -m ai_governance_mcp.extractor  # Rebuild index
pytest tests/ -v                        # Run tests (205, 90% coverage)
python -m ai_governance_mcp.server      # Run server
```

## Project Structure

- `src/ai_governance_mcp/` — Source code
- `documents/` — Governance content (indexed)
- `index/` — Generated embeddings
- `tests/` — Test suite

## Jurisdiction

**AI Coding** applies:
- 4-phase workflow: Specify → Plan → Tasks → Implement
- Record gates in PROJECT-MEMORY.md (not separate files)
- Keep changes atomic (≤15 files per task)

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions-v2.4.md for full activation protocol.*
