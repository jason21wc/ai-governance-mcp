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

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Project:** !`pwd`
**Memory file sizes:**
!`wc -l SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md BACKLOG.md OPERATIONS.md 2>/dev/null || echo "No memory files found"`

**Recent sessions (by modification time):**
!`for dir in ~/.claude/projects/*/; do jsonl=$(ls -t "$dir"*.jsonl 2>/dev/null | head -1); if [ -n "$jsonl" ]; then cwd=$(head -1 "$jsonl" 2>/dev/null | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('cwd','unknown'))" 2>/dev/null); if [ "$cwd" = "$(pwd)" ]; then echo "Directory: $dir"; ls -lt "$dir"*.jsonl 2>/dev/null | head -5; echo "---"; fi; fi; done`

## Instructions

Follow the procedure in `procedure.md` (loaded on demand). The procedure has
4 phases: Session Discovery → Transcript Analysis → HITL Review → Quality Check.

**Key constraints:**
- All subagents are READ-ONLY — they return proposals, never write directly
- Use default model (Opus) for analysis subagents — this is deeper reasoning than journaling
- Present ALL proposals before applying any — the user reviews the full picture first
- After applying approved changes, check for duplicates or contradictions
