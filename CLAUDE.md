# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Coding Methods v2.9.6
**Mode:** Standard

## On Session Start

1. Load SESSION-STATE.md for current position
2. Follow Next Actions listed there
3. Reference PROJECT-MEMORY.md for constraints and decisions
4. Check LEARNING-LOG.md before repeating past mistakes

## Memory Files

| File | Purpose |
|------|---------|
| SESSION-STATE.md | Current position, next actions |
| PROJECT-MEMORY.md | Decisions, constraints, gates |
| LEARNING-LOG.md | Lessons learned |
| ARCHITECTURE.md | System design, data flow |
| COMPLETION-CHECKLIST.md | Post-change steps (say "run the completion sequence") |

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content

**Skip list (narrow):** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE"

After evaluating: cite principle IDs that influence your approach.

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
- `.claude/agents/` — Local agent installations (synced from `documents/agents/`)

## Subagents

10 specialized agents in `.claude/agents/`. Read the agent file and apply its instructions when a task matches:

code-reviewer, test-generator, security-auditor, documentation-writer, orchestrator, validator, contrarian-reviewer, coherence-auditor, continuity-auditor, voice-coach

Edit `documents/agents/` (canonical source) first, then copy to `.claude/agents/`. CI verifies byte-match.

## Jurisdiction

AI Coding applies: Specify → Plan → Tasks → Implement. Record gates in PROJECT-MEMORY.md. Keep changes atomic (≤15 files).

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions-v2.5.md for full activation protocol.*
