# Dream Procedure — Cross-Session Memory Enrichment

> **Auto-run entry (hook-directed).** When this procedure is entered via the
> SessionStart AUTO-RUN directive (not a user `/dream` invocation): default to
> the **last 4 sessions** without waiting for Phase-1 user selection; run the
> Phase-2 analysis subagents with `run_in_background: true` so the user's actual
> task is not blocked; **hold Phase 3** — present the proposals for review at a
> natural boundary (when the user's current task completes), never mid-task.
> Everything from Phase 3 on is identical, including the blast-radius routing:
> L0 memory-file changes auto-apply and land in one revertible commit; Reference
> Library captures and BACKLOG deletions/closures still need the human.

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

3. **User selects sessions.** Default: last 4 sessions. User can specify
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
> BACKLOG.md, OPERATIONS.md — at [project_path], in `_ai-context/` (the unified
> layout) or at the project root (grandfathered pre-v2.62.0 layout); check both.
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

**Dispatch these analysts with a tool-restricted agent type — the prompt line above is
not sufficient on its own.** Use `subagent_type: "Explore"` (read-only; excludes
Edit/Write/NotebookEdit), or pass an explicit `allowed-tools` set. In session-261 a dream
analyst carrying exactly that "do NOT write" instruction used `Edit` three times anyway,
bypassing the Phase-3 approval gate. No content was damaged, but the control was
advisory when it needed to be structural — the same advisory-vs-structural gap this
framework flags everywhere else. The structural cause is unrestricted tool access, not
a disobedient subagent. (LEARNING-LOG 2026-07-24; `meta-core-systemic-thinking`.)
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

3. **Route each proposal by blast radius — do not treat them as one class.**

   Per `multi-autonomous-action-blast-radius-classification`, an **L0 Internal-Reversible**
   action (a local, git-tracked file write) warrants standard agent governance, *not* a
   human gate. Memory-file edits are L0: every one is a diff in version control, revertible
   with one command. Blocking on per-proposal approval for L0 work buys no safety and costs
   the cadence its momentum — which is why passes get skipped.

   | Class | Examples | Handling |
   |---|---|---|
   | **AUTO-APPLY (L0)** | ADDITION / CORRECTION / STALE in SESSION-STATE, LEARNING-LOG, PROJECT-MEMORY, OPERATIONS; BACKLOG *additions* and *corrections* | Apply directly. No per-item approval. **SESSION-STATE is narrower than the rest — see below.** |
   | **TWO-GATE (cross-project reach)** | `REFERENCE_LIBRARY` captures — *additive* | No longer blanket human-gated. Applies when the mechanical gates pass (registered domain, unique id, and `near_duplicate_check` not `likely_duplicate` — `unavailable` is NOT a pass) **and** a fresh-context reviewer accepts the entry against the §15.4 bar. The reviewer judges the ENTRY, never whether the author reasoned well: the parent writes the subagent's prompt, so self-attestation survives delegation. Deletions and edits to existing entries stay human-gated. See CLAUDE.md. |
   | **GATED — irreversible in practice** | BACKLOG *deletions* and *closures* | Human approval required. A wrongly-closed item does not come back on its own, and `merge=union` has silently resurrected a deleted entry — once, documented: `#206b`, which its own fix commit calls "the first observed instance". (This row said "twice (#64, #206b)" until 2026-08-24; `#64` is the item that DOCUMENTS the hazard, not a victim of it, and the likely intended second event is `#211`, a duplicate-ID collision — a different failure mode. The overstatement does not change the gate.) |
   | **OUT OF SCOPE** | `documents/*` governance docs, hooks, code | Never auto-applied by a dream pass. Versioned, propagating, pin-bearing — these need a version bump and propagation check, not a memory edit. |

   **SESSION-STATE is a snapshot, and an auto-applying writer is the likeliest thing to
   turn it back into an archive.** L0 writes to that file are confined to its snapshot
   fields — Current Position, Immediate Context, Next Actions — and **overwrite** them. Do
   not add a per-session block, a RESUMPTION section, or a narrative summary; that stack
   was deleted 2026-08-15 because it was the region concurrent close-outs collided on.
   Anything else a pass wants to record about SESSION-STATE routes to its owning file
   (decision → PROJECT-MEMORY, lesson → LEARNING-LOG, work → BACKLOG, cadence →
   OPERATIONS) or is dropped.

   A `STALE` finding against SESSION-STATE means **supersede the claim in place** — edit or
   delete it. It does NOT mean appending a correction underneath the stale text: that is
   how the file accumulated 14 mutually-contradicting claims, with a reader hitting the
   stale one first. The file's own removed warning said it: the entry point must carry the
   current answer.

   **When in doubt about a proposal's class, gate it.** Misrouting downward is the only
   error here that is expensive.

3b. **Auto-apply does not mean unreviewed — it means reviewed *after*, on a diff.**
   Apply the AUTO-APPLY set, then commit it as **one** clearly-labelled commit (Phase 5) so
   the entire pass is inspectable as a single diff and revertible with a single
   `git revert`. Report what was applied. The human's check moves from *blocking each item*
   to *reading one diff* — the same trade the pre-push gates already make.

   **Adversarial arm (recommended, not required):** before committing, run a fresh-context
   `validator` or `contrarian-reviewer` subagent over the **diff** — not over your own
   proposals list. A dream pass has no adversarial arm otherwise; the human reading the
   result afterwards is a check on the *outcome*, not on the *reasoning*. Fresh-context
   review over a diff is cheap and has repeatedly caught defects self-review does not.

3c. **Opt-out.** `DREAM_AUTOAPPLY=0` restores per-proposal approval for the L0 set. The
   gated classes above are never affected by this switch.

4. **Apply the changes** using Edit (append to appropriate section) — the AUTO-APPLY set
   directly, the gated set only after the human approves it.
   For CORRECTION findings, use Edit to replace the stale content.
   For STALE findings, comment or remove as the user directs.
   For CAPTURE findings (reference library), call `capture_reference` with the
   proposed content. The user has already approved the proposal in the review
   step — proceed with capture. Include domain, suggested title, and evidence
   from the transcript as the entry's content seed. If `capture_reference` is
   unavailable (the project has no ai-governance MCP connection), surface the
   CAPTURE finding as a note for the user instead of silently dropping it.

## Phase 4: Quality Check

After applying all accepted changes:

1. **Deduplication scan.** Read each modified memory file. Check for entries
   that say the same thing in different words. Flag duplicates for the user.

2. **Contradiction check.** Look for entries in the same file or across files
   that contradict each other. Flag for the user to resolve.

3. **Report summary.** State how many proposals were made, accepted, rejected,
   and what files were modified. Note any quality issues found in the check.

## Phase 5: Commit (cadence boundary)

After the user has reviewed and accepted changes, commit the modified memory files.

1. **The commit MUST carry a `Dream-Pass:` trailer, and its subject MUST contain the
   literal token `/dream pass`.** Copy this HEREDOC, filling the three placeholders — do
   not paraphrase it, and do not split it into multiple `-m` flags:

   ```bash
   git commit -m "$(cat <<'EOF'
   docs(memory): /dream pass over sessions <range> — <N> proposals applied

   Dream-Pass: sessions <range>
   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```

   **All trailers MUST be in the same last paragraph** (consecutive lines, no blank line
   between them). Git recognizes trailers only in the last paragraph of the commit message.
   The two-`-m` pattern previously used here put Dream-Pass in its own paragraph; when
   Co-Authored-By was added as a third paragraph, Dream-Pass ended up in the middle and git
   could not parse it — the cadence hook lost the boundary and over-fired for every
   subsequent session (session-282, n=1 at this defect class).

   This is **load-bearing, not cosmetic.** The SessionStart dream-cadence hook
   (`~/.claude/hooks/session-start-dream.sh`) reads git live to find the *last* pass and
   counts sessions since it (activity-based trigger). It resolves that boundary from the
   **`Dream-Pass:` trailer** — a structured field, so a commit that merely *describes* the
   convention (a hook fix, a LEARNING-LOG entry about dream passes) can never be mistaken
   for *performing* one.

   The subject token is a **legacy fallback channel** for passes committed before this
   convention. It still works, and since session-262 it is deliberately forgiving (leading
   slash optional, any conventional-commit prefix) because the two real 2026-07-24 passes
   dropped the slash and went unseen — but do not rely on it. Precision lives in the
   trailer; the subject is only a net.

   **Once any commit in the project carries a `Dream-Pass:` trailer, the trailer channel
   is authoritative and the prose channel is ignored entirely.** A later pass that forgets
   the trailer will not move the boundary, so the cadence over-fires until a trailered pass
   lands. That is the deliberate failure direction: over-firing is loud and bounded, while
   a false boundary is silent, self-perpetuating, and permanently loses the sessions that
   accumulate during the silence (the last-4 mining cap discards them).

1b. **Verify the boundary actually took — do not trust that you typed it correctly.**
   Prose alone did not hold at n=2 (two consecutive passes went unseen). The trailer is a
   far stronger channel, but a trailer can still be forgotten or malformed, and the
   failure is invisible at commit time. Confirm the mechanism fired:

   ```bash
   git log -1 --format='%(trailers:key=Dream-Pass)'   # must print your Dream-Pass line
   ```

   Empty output means the boundary is NOT set — amend (`git commit --amend`) and re-check.
   This is an external observable, not self-review: you are confirming a mechanism fired,
   not re-reading your own prose.

2. **If nothing was accepted**, do not commit (no boundary to set; the cadence correctly
   keeps counting from the prior pass).

2b. **Concurrent-session guard — check twice: before analyzing, and before committing.**
   Auto-run fires in *every* session at the threshold, so two sessions can dream over the
   same transcripts simultaneously and each apply the other's findings a second time.
   The SessionStart hook now checks for dream worktrees before injecting the AUTO-RUN
   directive (session-278), but this procedure-level guard is a defense in depth for
   manual `/dream` invocations and for the window between hook fire and worktree creation.

   **Pre-flight (before Phase 1 — cheap, do it first):**

   ```bash
   git worktree list | grep -iE '\[.*dream.*\]'   # branch name contains "dream"
   ```

   A worktree whose branch name contains "dream" means another session is likely
   running a dream pass. **Stop and tell the user** — a duplicate pass is wasted tokens
   at best and double-applied proposals at worst. If the worktree is stale (from a
   finished session), the user can clean up with `git worktree remove <path>` and
   re-invoke. Match on the bracket-enclosed branch field, not the full line — the
   filesystem path may contain "dream" for unrelated reasons.

   **Pre-commit:** re-check `git log --format='%s%n%(trailers:key=Dream-Pass)' -20` for a
   pass NEWER than the one this pass counted from. If one landed, present the situation to
   the user: usually keep only proposals the newer pass didn't already apply, and skip the
   boundary commit if nothing
   genuinely new remains.

3. **Commit the pass as ONE commit.** The AUTO-APPLY set (Phase 3) commits without
   per-item approval — the single labelled commit *is* the review surface, and
   `git revert` is the undo. Anything from the GATED classes goes in only after the human
   approved it. Pushing remains user-gated per project convention: commit freely, ask
   before `git push`.

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
