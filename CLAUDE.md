# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Governance Framework v2.4

## On Session Start

1. Load SESSION-STATE.md for current position
2. Query `ai-governance` MCP for relevant principles as needed
3. Follow governance principles from this project's own documents

## Governance Integration

This project IS the AI Governance MCP. Use the `ai-governance` MCP tools:

| Tool | Purpose |
|------|---------|
| `query_governance` | Retrieve relevant principles for current task |
| `get_principle` | Get full content of a specific principle |
| `list_domains` | See available domains (constitution, ai-coding, multi-agent) |
| `get_domain_summary` | Explore a domain's principles and methods |

## Project Context

- **Source:** `src/ai_governance_mcp/`
- **Documents:** `documents/` (governance content)
- **Index:** `index/` (generated embeddings)
- **Tests:** `tests/` (198 tests, 93% coverage)

## Key Commands

```bash
# Rebuild index after document changes
python -m ai_governance_mcp.extractor

# Run tests
pytest tests/ -v

# Run server
python -m ai_governance_mcp.server
```

## Jurisdiction

**AI Coding** applies (this is a software project):
- Follow 4-phase workflow: Specify → Plan → Tasks → Implement
- Validate with gates between phases
- Keep changes atomic (≤15 files per task)

## Memory Files

| File | Purpose |
|------|---------|
| SESSION-STATE.md | Current position, next actions |
| PROJECT-MEMORY.md | Architecture decisions |
| LEARNING-LOG.md | Lessons learned |

## Framework Check

If context seems lost, query:
```
query_governance("framework recovery session continuity")
```

---

*See documents/ai-instructions-v2.4.md for full framework activation protocol.*
