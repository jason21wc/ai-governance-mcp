---
description: |
  Mine completed session transcripts for unpersisted decisions, lessons, and context.
  Enriches and fact-checks memory files with HITL review. Use between sessions or when
  memory files feel stale relative to recent work. Triggers: "dream", "mine transcripts",
  "memory enrichment", "harvest sessions", "what did we miss".
  Does NOT activate for: within-session journaling (use /journal), reading memory files,
  regular session-start loading.
disable-model-invocation: true
allowed-tools: Bash Read Edit Agent
---

# /dream — Cross-Session Memory Enrichment

Analyzes completed session transcripts to find decisions, lessons, and context that
were discussed but never captured in memory files. Spawns per-session analysis agents,
aggregates findings, and presents proposed changes for your review before applying.

## Runtime Context

After the skill loads, follow `procedure.md` to resolve the active memory layout,
measure memory files, and discover completed transcripts whose recorded working
directory matches this project. Missing host transcript storage is a scope limit,
not a reason for skill loading to fail.

## Instructions

Collect the Runtime Context above, then follow `procedure.md` (loaded on demand). The procedure has
5 phases: Session Discovery → Transcript Analysis → HITL Review → Quality Check
→ Commit (cadence boundary).

**Auto-run:** the SessionStart dream-cadence hook may inject an AUTO-RUN
directive for this procedure when enough unmined sessions accumulate (title-10
§7.11.4). That deterministic trigger is the sanctioned automatic entry;
`disable-model-invocation: true` stays — the model must not semantically
self-fire a subagent-spawning skill (per the §9.5.3 two-prong bar). HITL on
apply/commit is unchanged in auto-run.

**Key constraints:**
- All subagents are READ-ONLY — they return proposals, never write directly
- Use default model (Opus) for analysis subagents — this is deeper reasoning than journaling
- Present ALL proposals before applying any — the user reviews the full picture first
- After applying approved changes, check for duplicates or contradictions
