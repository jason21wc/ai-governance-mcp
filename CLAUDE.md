# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Coding Methods v2.7.0
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

This project IS the AI Governance MCP. Primary tools: `evaluate_governance` (pre-action check), `query_governance` (get principles), `log_governance_reasoning` (audit trail). Secondary: `verify_governance_compliance`, `get_principle`, `log_feedback`, `list_domains`, `get_domain_summary`, `get_metrics`.

### Mandatory Governance Checkpoints

Call `evaluate_governance()` before any action UNLESS it is:
- Reading files, searching, or exploring code
- Answering questions that do not involve security-sensitive information
- Trivial formatting (whitespace or comment text changes that do not alter behavior)
- Human user explicitly says "skip governance" with documented reason

When in doubt, evaluate.

**After evaluating:** Cite the principle ID when it influences your approach.

## Key Commands

```bash
# Development
python -m ai_governance_mcp.extractor  # Rebuild index
pytest tests/ -v                        # Run tests
python -m ai_governance_mcp.server      # Run governance server
python -m ai_governance_mcp.context_engine.server  # Run context engine server

# Docker
docker build -t ai-governance-mcp .     # Build image
docker run -i --rm ai-governance-mcp    # Run container
```

## Project Structure

- `src/ai_governance_mcp/` — Governance server source code
- `src/ai_governance_mcp/context_engine/` — Context Engine MCP server (4 tools)
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
| Artifact validation | `validator.md` | Criteria-based validation of any artifact against explicit checklist |
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
- [ ] LEARNING-LOG.md exceeds 200 lines
- [ ] Before major releases

**Action:** Apply distillation triggers per §7.0.4 — each memory type has a named significance test (Working Memory §7.1.1, Decision Significance §7.2.1, Future Action §7.3.1).

**Quick Check:**
```bash
wc -l SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md
```

## Pre-Release Security Checklist

Per §5.3.2, apply before tagging a release:

**Input Handling:**
- [ ] No hardcoded secrets or credentials in source
- [ ] All user input validated (query length limits, parameter bounds)
- [ ] No direct file path construction from user input (path traversal prevention)

**Content Security:**
- [ ] CI content scan passes (no prompt injection in `documents/`, `CLAUDE.md`, `.claude/agents/`)
- [ ] Agent template hashes match expected values (advisory — see SECURITY.md limitations)
- [ ] No external URLs added without justification

**Dependencies:**
- [ ] `pip audit` or equivalent — zero HIGH/CRITICAL vulnerabilities
- [ ] No new dependencies without justification
- [ ] Docker image builds and runs as non-root

**Scanning:**
- [ ] `ruff check` passes
- [ ] Full test suite passes (`pytest tests/ -v`)
- [ ] Security CI job green

## Jurisdiction

**AI Coding** applies:
- 4-phase workflow: Specify → Plan → Tasks → Implement
- Record gates in PROJECT-MEMORY.md (not separate files)
- Keep changes atomic (≤15 files per task)

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions-v2.4.md for full activation protocol.*
