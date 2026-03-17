# AI Governance MCP Server

Also read AGENTS.md for project context.

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content

**Skip list (narrow):** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE"

After evaluating: cite principle IDs that influence your approach.

## Subagents

10 specialized agents in `.claude/agents/`. Read the agent file and apply its instructions when a task matches:

code-reviewer, test-generator, security-auditor, documentation-writer, orchestrator, validator, contrarian-reviewer, coherence-auditor, continuity-auditor, voice-coach

Edit `documents/agents/` (canonical source) first, then copy to `.claude/agents/`. CI verifies byte-match.

- `.claude/agents/` — Local agent installations (synced from `documents/agents/`)
