# AI Governance MCP Server

Also read AGENTS.md for project context.
@./AGENTS.md

The shared project body is imported from `AGENTS.md` above — memory-file
pointers, session-start protocol, disposition, key commands, and the
concurrency rules. Keep only Gemini-specific content below; do not duplicate
the body here (CFR title-10 Appendix K.3, one-copy invariant).

## Gemini-Specific

- `/memory show` inspects the loaded context; run `/memory refresh` after
  editing `AGENTS.md` or this file.
- Checkpointing is available for multi-step edits (`/restore list`,
  `/restore <id>`).

## Governance is ADVISORY here, not enforced

This is the one thing a Gemini session must not get wrong. The governance
floor described in `AGENTS.md` is *enforced* only under Claude Code, by
`PreToolUse` hooks registered in `.claude/settings.json` that block
`Bash|Edit|Write` until `evaluate_governance()` and `query_project()` have
run. **Gemini CLI loads no such hook**, so here those calls are a discipline
you keep, not a gate that stops you.

Two consequences worth stating plainly, because a session that assumes the
gate exists will act as though it has already been checked:

- Call `evaluate_governance(planned_action="...")` before any non-read action
  and `query_project(query="...")` before creating or modifying code, on your
  own initiative. Nothing will remind you.
- An S-Series (safety) principle is still an absolute veto. The veto is a
  rule about what you may do, not a property of the tooling, so it binds
  identically whether or not a hook is present.

Per the safety-boundary binding (CFR title-10 v2.63.0, Appendix A / K.3),
enforcement detail belongs in a tool overlay rather than the shared body —
which is why this section names what does *not* run here instead of implying
the Claude Code behaviour carries over.
