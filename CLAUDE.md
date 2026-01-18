# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Coding Methods v2.3.0
**Mode:** Standard

## On Session Start

1. Load SESSION-STATE.md for current position
2. Follow Next Actions listed there
3. Reference PROJECT-MEMORY.md for constraints and decisions

## Memory (Cognitive Types)

| Type | File | Purpose |
|------|------|---------|
| Working | SESSION-STATE.md | Current position, next actions |
| Semantic | PROJECT-MEMORY.md | Decisions, constraints, gates |
| Episodic | LEARNING-LOG.md | Lessons learned |
| Structural | ARCHITECTURE.md | System design, component responsibilities, data flow |
| Charter | README.md | Project purpose, scope, public contract. Validate features fit; flag scope drift. |

## Governance Integration

This project IS the AI Governance MCP. Use these tools:

| Tool | Purpose |
|------|---------|
| `evaluate_governance` | Pre-action compliance check (Governance Subagent) |
| `query_governance` | Get principles for current task |
| `verify_governance_compliance` | Post-action audit |
| `get_principle` | Get full content by ID |
| `list_domains` | See available domains |
| `install_agent` | Install Orchestrator subagent (Claude Code only) |

### Mandatory Governance Checkpoints

Query `query_governance()` BEFORE:
- [ ] Starting any implementation task
- [ ] Making architectural or configuration decisions
- [ ] Modifying governance documents or templates
- [ ] Phase transitions (Specify → Plan → Tasks → Implement)

**After querying:** Cite the principle ID when it influences your approach.

## Key Commands

```bash
# Development
python -m ai_governance_mcp.extractor  # Rebuild index
pytest tests/ -v                        # Run tests (350, 90% coverage)
python -m ai_governance_mcp.server      # Run server

# Docker
docker build -t ai-governance-mcp .     # Build image
docker run -i --rm ai-governance-mcp    # Run container
```

## Project Structure

- `src/ai_governance_mcp/` — Source code
- `documents/` — Governance content (indexed)
- `index/` — Generated embeddings
- `tests/` — Test suite
- `.claude/agents/` — Subagent definitions

## Subagents

This project has specialized subagent definitions in `.claude/agents/`. When a task matches a cognitive function below, read the agent file and apply its instructions.

| Task Type | Agent File | When to Use |
|-----------|------------|-------------|
| Code review | `code-reviewer.md` | After writing or modifying code |
| Test creation | `test-generator.md` | When tests need to be written |
| Security review | `security-auditor.md` | Before releases, auth/security changes, sensitive data handling |
| Documentation | `documentation-writer.md` | README updates, docstrings, technical writing |
| Governance coordination | `orchestrator.md` | Complex multi-step tasks requiring governance checks |
| Devil's advocate | `contrarian-reviewer.md` | High-stakes decisions, architectural choices, challenge assumptions |

**How to use:**
1. Read the agent file (e.g., `.claude/agents/code-reviewer.md`)
2. Apply the role, cognitive function, and output format from that file
3. Use Task tool with `general-purpose` if spawning a focused subprocess

**Note:** Custom agent files are reference documentation — they define roles but aren't automatically invokable via Task tool's `subagent_type` parameter.

## Memory Hygiene Checkpoints

Check memory health WHEN:
- [ ] SESSION-STATE.md exceeds 300 lines
- [ ] PROJECT-MEMORY.md exceeds 800 lines
- [ ] Before major releases

**Action:** Apply §7.0.4 distillation triggers

**Quick Check:**
```bash
wc -l SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md
```

## Jurisdiction

**AI Coding** applies:
- 4-phase workflow: Specify → Plan → Tasks → Implement
- Record gates in PROJECT-MEMORY.md (not separate files)
- Keep changes atomic (≤15 files per task)

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions-v2.4.md for full activation protocol.*
