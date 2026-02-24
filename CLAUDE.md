# AI Governance MCP Server

**Project:** Semantic retrieval system for AI governance principles
**Framework:** AI Coding Methods v2.9.6
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
| Procedural | Methods documents | How to do things (via MCP retrieval) |
| Reference | Context Engine index | Project content, semantically searchable. Query before implementing. |

## Governance Integration

This project IS the AI Governance MCP. Primary tools: `evaluate_governance` (pre-action check), `query_governance` (get principles), `log_governance_reasoning` (audit trail). Secondary: `verify_governance_compliance`, `get_principle`, `log_feedback`, `list_domains`, `get_domain_summary`, `get_metrics`. Utility: `install_agent`, `uninstall_agent`.

### Mandatory Governance Checkpoints

Call `evaluate_governance()` before any action UNLESS it is:
- Reading files, searching, or exploring code
- Answering questions that do not involve security-sensitive information
- Trivial formatting (whitespace or comment text changes that do not alter behavior)
- Human user explicitly says "skip governance" with documented reason

When in doubt, evaluate.

**After evaluating:** Cite the principle ID when it influences your approach.

## Context Engine Integration

Query the context engine before creating or modifying code to discover existing patterns and prevent duplication.

### When to Query
- Before creating new files, functions, classes, or modules
- Before modifying code — understand related patterns first
- When searching for "where does X happen?" or "do we already have Y?"
- During planning phase — build a context inventory of affected areas

### After Querying
Cite file paths and patterns found, or confirm nothing relevant exists.

### Staleness
If working for an extended session, check `project_status`. If stale, call `index_project` before querying.

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

## Post-Change Completion Checklist

Per §5.1.6, run this project's completion sequence after changes. Say "run the completion sequence" to trigger.

**Code changes:**
1. `pytest tests/ -v` — full test suite
2. Code review (code-reviewer subagent) if substantial
3. Update SESSION-STATE.md (version, counts, summary)
4. Commit and push
5. Verify CI green (`gh run watch`)
6. Docker check: if `src/`, `pyproject.toml`, or `Dockerfile` changed since last image build → rebuild and push

**Content changes** (governance documents):
1. `python -m ai_governance_mcp.extractor` — rebuild index
2. `pytest tests/ -v` — full test suite
3. Spot-check: `query_governance("new content topic")` → verify it surfaces
4. Update SESSION-STATE.md (version, counts, summary)
5. Commit and push
6. Verify CI green
7. Docker check: if content significantly changed or code also changed → rebuild and push

**Documentation-only changes** (memory files, README):
1. Update SESSION-STATE.md if applicable
2. Commit and push

## Project Structure

- `src/ai_governance_mcp/` — Governance server source code
- `src/ai_governance_mcp/context_engine/` — Context Engine MCP server (4 tools)
- `documents/` — Governance content (indexed)
- `documents/agents/` — Canonical agent templates (distribution source — see Subagents below)
- `index/` — Generated embeddings
- `tests/` — Test suite
- `.claude/agents/` — Local agent installations (see Subagents below)

## Subagents

This project has specialized subagent definitions in `.claude/agents/`. When a task matches a cognitive function below, read the agent file and apply its instructions.

### Two Directories, Two Purposes

Agent definitions exist in two locations with distinct roles:

| Directory | Purpose | Consumer |
|-----------|---------|----------|
| `documents/agents/` | **Canonical source (distribution templates).** Ships with the package. The `install_agent` MCP tool reads from here to install agents on other users' machines. Also indexed by the Context Engine for semantic search. | `install_agent` tool, Context Engine, CI hash verification |
| `.claude/agents/` | **Local installation (operational).** Claude Code reads these files to apply subagent roles in this project. Created by `install_agent` or manual copy. | Claude Code (this project only) |

**Editing rule:** Always edit `documents/agents/` first (the canonical source), then copy to `.claude/agents/`. Never edit `.claude/agents/` directly — it will drift from the distribution templates. A CI test (`test_agent_templates_synced_with_local`) verifies both directories match byte-for-byte.

| Task Type | Agent File | When to Use |
|-----------|------------|-------------|
| Code review | `code-reviewer.md` | After writing or modifying code |
| Test creation | `test-generator.md` | When tests need to be written |
| Security review | `security-auditor.md` | Before releases, auth/security changes, sensitive data handling |
| Documentation | `documentation-writer.md` | README updates, docstrings, technical writing |
| Governance coordination | `orchestrator.md` | Complex multi-step tasks requiring governance checks |
| Artifact validation | `validator.md` | Criteria-based validation of any artifact against explicit checklist |
| Devil's advocate | `contrarian-reviewer.md` | High-stakes decisions, architectural choices, challenge assumptions |
| Coherence audit | `coherence-auditor.md` | Pre-release doc review, session-start drift check, cross-file consistency |
| Continuity audit | `continuity-auditor.md` | Narrative consistency — Story Bible vs. manuscript, character drift, timeline conflicts |
| Voice analysis | `voice-coach.md` | Character voice distinction, voice profile compliance, voice drift detection |

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

**Documentation:**
- [ ] Documentation coherence audit passes (meta-methods Part 4.3.2, full tier)

**Scanning:**
- [ ] `ruff check` passes
- [ ] Full test suite passes (`pytest tests/ -v`)
- [ ] Security CI job green

## Progressive Inquiry — Tool Mapping

When asking questions, match the interaction mechanism to the question tier (per meta-methods Part 7.9.1):

| Question Tier | Mechanism | Why |
|---------------|-----------|-----|
| **Foundation** (strategic scope) | Conversational text in your response — pose the question naturally and let the user respond freely | Answers are exploratory; pre-set options constrain discovery |
| **Branching** (conditional exploration) | Conversational text (default) or AskUserQuestion if narrowing between 2-4 known alternatives | Open-ended unless prior answers have bounded the options |
| **Refinement** (bounded details) | AskUserQuestion tool with structured options | Answer space is known; selection is efficient |

**Rule of thumb:** If the user's answer could surprise you, ask conversationally. If you're converging on specifics, use AskUserQuestion.

## Jurisdiction

**AI Coding** applies:
- 4-phase workflow: Specify → Plan → Tasks → Implement
- Record gates in PROJECT-MEMORY.md (not separate files)
- Keep changes atomic (≤15 files per task)

## Recovery

If context seems lost: `query_governance("framework recovery")`

---

*See documents/ai-instructions-v2.5.md for full activation protocol.*
