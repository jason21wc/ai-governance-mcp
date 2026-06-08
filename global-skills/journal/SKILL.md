---
description: |
  Scan the current session for unpersisted decisions, constraints, and lessons, then
  propose memory file updates. Use when you want to capture what was discussed but not
  yet written to memory files. Triggers: "journal", "capture memory", "update memory",
  "what did we discuss", "persist session state".
  Does NOT activate for: reading memory files, session-start loading, end-of-session
  updates that are already part of the completion sequence.
disable-model-invocation: true
allowed-tools: Bash Read Agent
---

# /journal — Session Memory Capture

Analyzes the current session transcript for decisions, constraints, lessons, and
context that have not been persisted to memory files. Returns structured proposals
categorized by target file. Does NOT write directly — you review and apply.

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Project:** !`pwd`
**Memory file sizes:**
!`wc -l SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md BACKLOG.md OPERATIONS.md 2>/dev/null || echo "No memory files found"`

**Current session transcript:**
!`for dir in ~/.claude/projects/*/; do jsonl=$(ls -t "$dir"*.jsonl 2>/dev/null | head -1); if [ -n "$jsonl" ]; then cwd=$(head -1 "$jsonl" 2>/dev/null | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('cwd','unknown'))" 2>/dev/null); if [ "$cwd" = "$(pwd)" ]; then echo "Transcript: $jsonl"; fi; fi; done`

## Instructions

### Quick Start

1. Discover the current session's transcript path from the dynamic context above.
   If that shows nothing, list `~/.claude/projects/` directories and check which
   `.jsonl` files have recent modification times matching this session.

2. Spawn a **background Agent** with these parameters:
   - `model: "sonnet"` (extraction task — Sonnet is appropriate)
   - `run_in_background: true` (don't block the user's work)
   - Prompt: include the transcript path and current memory file contents summary

3. The Agent's task (include in its prompt):
   > Read the transcript JSONL file at [path], focusing on the last 500 lines.
   > Read the current contents of SESSION-STATE.md, PROJECT-MEMORY.md,
   > LEARNING-LOG.md, BACKLOG.md, OPERATIONS.md, and ARCHITECTURE.md.
   >
   > Identify items from the conversation that are NOT yet captured in any
   > memory file:
   > - **Decisions** (with rationale) → propose for PROJECT-MEMORY.md
   > - **Lessons learned** (actionable rules from mistakes or discoveries) → propose for LEARNING-LOG.md
   > - **Position/state changes** (current task, blockers, next actions) → propose for SESSION-STATE.md
   > - **Deferred work items** → propose for BACKLOG.md
   > - **Operational commitments** (recurring reviews, tripwires) → propose for OPERATIONS.md
   > - **Architecture changes** (system design, data flow) → propose for ARCHITECTURE.md
   >
   > For each proposal, provide:
   > - Target file
   > - Proposed content (ready to append/insert)
   > - Why it should be persisted (what would be lost without it)
   >
   > Return ONLY structured proposals. Do NOT write to any files.

4. When the background agent completes, review its proposals. Apply the ones
   you agree with using Edit (append to appropriate section).

### What NOT to Journal

- Information already in memory files (check before proposing)
- Ephemeral debugging steps or failed attempts (unless they produced a lesson)
- Code that was written (git tracks that)
- Information derivable from `git log` or current file state
