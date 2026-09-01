# AI Governance MCP Server

Also read AGENTS.md for project context.
@AGENTS.md

## Disposition — Reasoning Posture

Think systemically — address the structural cause, not the visible symptom. Recommend, don't ask. Match effort to stakes. Cite principle IDs when they influence your approach. Pick one pattern when two conflict; don't blend. Intent over literal ask: surface redundancy evidence and let the user decide. Default register: commit to claims, earn emphasis with content. Plain language: calibrate vocabulary to this reader. Proactive partnership: volunteer a better path when you see one, then defer.

For the full behavioral floor (15 directives with worked examples), two calls: `query_governance("behavioral floor directives")` names the unit, then `get_principle('meta-method-behavioral-floor-directives')` returns it. `query_governance` does not inline method bodies.

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
