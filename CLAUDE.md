# AI Governance MCP Server

Also read AGENTS.md for project context.
@AGENTS.md

## Governance — ENFORCED BY HOOK

Hard-mode hook **BLOCKS** Bash|Edit|Write until both tools are called. This is structural, not advisory.

- `evaluate_governance(planned_action="...")` — required before any non-read action
- `query_project(query="...")` — required before creating or modifying code/content
- `contrarian-reviewer` via Task subagent — required before `ExitPlanMode`

S-Series principle = absolute veto. Keyword-only matches without a retrieved S-Series principle are topic mentions — adjudicated server-side per BACKLOG #73.

**Skip list:** reading files, non-sensitive questions, trivial formatting, user says "skip governance/CE". Analysis tasks that determine what to change are NOT read-only.

**Search default: CE first.** Use `query_project` for discovery and "what exists?" queries. Use Grep only for exact-string lookup in a known file.

## Reference Library

`search_references(query="...")` before implementing code patterns. `capture_reference(...)` after solving non-obvious, reusable problems — two-gate rule: mechanical gates pass + fresh-context reviewer accepts. Human-gated: deletions and edits. Full procedure: `query_governance("reference library curation §15.4")`.
