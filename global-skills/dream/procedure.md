# Dream Procedure — Cross-Session Memory Enrichment

## Phase 1: Session Discovery

1. **Find the project's transcript directory.** List directories under
   `~/.claude/projects/`. For each directory, read the first line of the most
   recent `.jsonl` file and extract the `cwd` field. Match against the current
   project directory (`pwd`).

   ```bash
   # Discovery pattern — adapt as needed
   for dir in ~/.claude/projects/*/; do
     jsonl=$(ls -t "$dir"*.jsonl 2>/dev/null | head -1)
     [ -n "$jsonl" ] || continue
     cwd=$(head -1 "$jsonl" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('cwd',''))" 2>/dev/null)
     [ "$cwd" = "$(pwd)" ] && echo "$dir"
   done
   ```

2. **List available sessions.** Show the last 5 `.jsonl` files in the matched
   directory, sorted by modification time. Include date, size, and line count.

3. **User selects sessions.** Default: last 3 sessions. User can specify
   different sessions or a different count. Skip any session with < 50 lines
   (too short for meaningful analysis).

4. **Exclude the current session.** The active session's transcript is
   still being written — use `/journal` for within-session capture instead.

## Phase 2: Transcript Analysis

For each selected session, spawn an **Agent** subagent:

- **Model:** default (Opus — cross-session analysis benefits from deeper reasoning)
- **Run in background:** Yes, if analyzing multiple sessions (parallel analysis)
- **Prompt template:**

> You are a memory quality analyst. Your job is to read a completed session
> transcript and compare it against the project's current memory files to find
> information that was discussed but never persisted.
>
> **Transcript:** Read the file at [transcript_path]. Focus on entries where
> `message.role` is "assistant" or contains user messages. Skip thinking blocks
> and tool_use entries unless they contain decisions or lessons.
>
> **Memory files to read:** SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md,
> BACKLOG.md, OPERATIONS.md (all in the project root at [project_path]).
>
> **What to look for:**
> 1. Decisions with rationale that aren't in PROJECT-MEMORY.md
> 2. Lessons learned or mistakes that aren't in LEARNING-LOG.md
> 3. Deferred work items discussed but not tracked in BACKLOG.md
> 4. Operational commitments (cadences, triggers) not in OPERATIONS.md
> 5. Facts that contradict what's currently in memory files (stale entries)
> 6. Entries in memory files that reference things not supported by transcript
>    evidence (potential fabrication or drift)
> 7. Reference library candidates: reusable patterns validated during the session,
>    external research cited with evidence, architecture decisions with rationale,
>    tool evaluations with conclusions, or working implementations of non-obvious
>    techniques. Not every session produces these — look for: external papers or
>    articles discussed and validated, proven code patterns used across 2+ files,
>    tool comparisons with a clear winner, solutions to problems that recurred.
>    For these, set Target file to "REFERENCE_LIBRARY" with the domain
>    (ai-coding, multi-agent, etc.) and a suggested entry title.
>
> **For each finding, report:**
> - Target file (which memory file should be updated, or "REFERENCE_LIBRARY" for capture candidates)
> - Category: ADDITION (new entry), CORRECTION (fix existing), STALE (flag for removal), CAPTURE (reference library candidate)
> - Proposed content (ready to insert/replace)
> - Evidence (quote or paraphrase from transcript with approximate line position)
> - Confidence: HIGH (clear decision/lesson stated), MEDIUM (implied but not explicit),
>   LOW (interpretation — may need user confirmation)
>
> **Do NOT write to any files.** Return findings as a structured list.
> Skip findings where the information is already accurately captured in memory.

For large transcripts (> 2MB or > 5000 lines), instruct the subagent to read
only the last 2000 lines. Information from the beginning of very long sessions
is more likely to have been captured during the session itself.

## Phase 3: HITL Review

1. **Aggregate findings** from all subagents. Group by target file.
   Within each file, sort by confidence (HIGH first).

2. **Present the review.** Format as a structured diff-style report:

   ```
   ## Proposed Changes to PROJECT-MEMORY.md

   ### [HIGH] Decision: <title>
   Source: Session <id>, ~line <N>
   Proposed content:
   > <content ready to insert>

   ### [MEDIUM] Decision: <title>
   ...

   ## Proposed Changes to LEARNING-LOG.md
   ...

   ## Stale Entries Flagged
   ...
   ```

3. **User reviews.** For each proposal:
   - **Accept** — apply as-is
   - **Modify** — user adjusts the content, then apply
   - **Reject** — skip this proposal
   - **Accept all HIGH** — batch-accept all HIGH-confidence proposals

4. **Apply accepted changes** using Edit (append to appropriate section).
   For CORRECTION findings, use Edit to replace the stale content.
   For STALE findings, comment or remove as the user directs.
   For CAPTURE findings (reference library), call `capture_reference` with the
   proposed content. The user has already approved the proposal in the review
   step — proceed with capture. Include domain, suggested title, and evidence
   from the transcript as the entry's content seed.

## Phase 4: Quality Check

After applying all accepted changes:

1. **Deduplication scan.** Read each modified memory file. Check for entries
   that say the same thing in different words. Flag duplicates for the user.

2. **Contradiction check.** Look for entries in the same file or across files
   that contradict each other. Flag for the user to resolve.

3. **Report summary.** State how many proposals were made, accepted, rejected,
   and what files were modified. Note any quality issues found in the check.

## Edge Cases

- **No transcripts found:** Inform user that no completed sessions were found
  for this project. Suggest running `/dream` after completing at least one full
  session.

- **Very short sessions (< 50 lines):** Skip with a note. These sessions likely
  contained only quick lookups or configuration — low yield for memory mining.

- **Projects with non-standard memory files:** Check the AGENTS.md "Memory Files"
  table if it exists. Fall back to the standard 5 files (SESSION-STATE.md,
  PROJECT-MEMORY.md, LEARNING-LOG.md, BACKLOG.md, OPERATIONS.md).

- **Conflicting proposals from different sessions:** If two session analyses
  propose contradictory additions (e.g., one says a decision was X, another
  says it was Y), present both with their source sessions and let the user
  resolve. The more recent session's version is usually correct.
