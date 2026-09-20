# {{CHANNEL_NAME}} — pairing channel ({{IMPLEMENTER_HOST}} IMPLEMENTER ↔ {{REVIEWER_HOST}} REVIEWER)

Temporary and untracked. This file is the ONLY channel between the two
sessions. It is deleted at teardown, after the Decisions ledger has been
routed (rule 14). Full procedure: the `pair-channel` skill's `procedure.md`.
Write to this file only through `channel.py` (`append`, `fill`, `ledger`);
read your turn only through `channel.py watch` or `channel.py state`. The
sidecar `<this file>.lock` is the writers' lock; leave it alone.
Cadence: ordinary channel messages and turn flips are standing-authorized;
before every append, report the four-field status in rule 2 and proceed.

## STATE — read this before doing anything

```
TURN: REVIEWER
NEXT_SEQ: 1
OPEN: none
ESCALATED: none
```

STATE carries only what the other side cannot observe for itself: whose turn
it is, the next sequence number, which proposals are open, what is with the
human. Everything else (SHAs, tree state, test results) is observable — run
the command. `TURN:` appears on exactly one line in this file, here.

Roles (fixed for the life of this file):

| Role | Session | Worktree | May write |
|---|---|---|---|
| IMPLEMENTER | {{IMPLEMENTER_HOST}} | `{{IMPLEMENTER_WORKTREE}}` | its own worktree + this file |
| REVIEWER | {{REVIEWER_HOST}} | `{{REVIEWER_WORKTREE}}` | **this file only** (+ scratch dirs) |

Transcripts (readable evidence; own pair by default — rule 12):

| Role | Absolute transcript path |
|---|---|
| IMPLEMENTER | `{{IMPLEMENTER_TRANSCRIPT}}` |
| REVIEWER | `{{REVIEWER_TRANSCRIPT}}` |

## Rules

1. **Append-only thread.** Never edit or delete a message — not the other
   side's, not your own once the turn has passed. Corrections are new
   messages. The trail is the only evidence that consensus was reached rather
   than assumed. **Carve-out:** the STATE block (updated by `append`),
   placeholder cells in the Roles and Transcripts tables (`channel.py fill`),
   and new rows in the Decisions ledger (`channel.py ledger`) are mutable by
   the turn holder; the Rules section changes only by a consensus recorded in
   the thread. Every write goes through `channel.py`, at end-of-file for
   messages; never anchor an append on text that can repeat.
2. **One writer at a time.** `TURN:` in STATE names the only session that may
   write, and STATE is the only place a line may begin with `TURN:` — quote
   protocol syntax only inside a fenced code block, and close every fence you
   open in the same message (`append` refuses an odd count, because one open
   fence would hide every later heading). Hand over with `--flip-to`
   as part of your append. Once the human explicitly establishes the pairing,
   ordinary channel messages and turn flips are standing-authorized for both
   roles; neither waits for per-message approval. Before every `append`, the
   sender gives the human a brief, human-visible status with four fields:
   **Accomplished**, **Current task**, **Other AI**, and **Next**, then proceeds
   without waiting. This is notification, not an approval request. Review
   stays at phase boundaries, not every choice. A watch that wakes you is a
   signal to re-check write eligibility: `append` re-reads STATE under a lock
   and refuses an out-of-turn write. The lock serialises writers; TURN decides
   who may write. This grant covers coordination only; irreversible or
   external effects remain separately human-authorized under rule 15.
3. **Sequence numbers.** Every message begins `## #<n> <ROLE> <TYPE …>` with
   `n` equal to `NEXT_SEQ`. `append` refuses a wrong or duplicate number and
   re-verifies the sequence after writing. If `check` ever reports a
   duplicate or a gap, both sides stop; the human decides.
4. **Message types.** `PROPOSE` · `CONFIRM` · `OBJECT` · `QUESTION` · `ANSWER`
   · `DONE` · `ESCALATE`. Proposals get ids `P1, P2, …`; every later message
   names the id it is about.
5. **Proposal shape** (`PROPOSE`): what changes (files), why (≤3 lines), and
   the observable that will prove it — command + expected result. No
   confidence language. Volunteer what you have not checked, marked
   `UNVERIFIED`.
6. **Confirmation must be earned.** A `CONFIRM` restates the proposal in the
   confirmer's own words and names one thing that would falsify it or one
   thing checked. A bare "agree / ACK / LGTM" is not a confirmation and the
   proposal stays open. Two models told to agree will agree; the restatement
   is the proof they understood the same thing.
7. **Objection shape** (`OBJECT`): what specifically, the evidence, and either
   an alternative or a question. Suggestive register — "consider", "what
   about" — never directive. Disagreement is a result, not a failure.
8. **Round cap.** Three `OBJECT` rounds on one proposal id, then `ESCALATE`
   with both positions standing, unedited, and `--set-escalated`. The human
   adjudicates. Consensus is never reached by exhaustion or by whoever
   writes last.
9. **Consensus before implementation.** IMPLEMENTER edits tracked files only
   under a `CONFIRM`ed proposal id. Size a proposal to one commit. Trivia
   inside a confirmed proposal (typos, formatting, implied test scaffolding)
   needs no round — declare it in `DONE`. Reviewer rounds buy independent
   judgment at load-bearing boundaries — a plan, a design choice, a completed
   unit of work — not at every small choice.
10. **REVIEWER writes no tracked file, anywhere.** Not a one-line fix. The
    moment it edits code it is an author and its next review is
    self-attestation. REVIEWER may propose an *approach*; it never writes the
    *patch*. It reads IMPLEMENTER's worktree by absolute path at a named SHA.
    Mutation probes go in scratch dirs only; never the index, never
    `~/.claude` / `~/.codex`.
11. **`DONE` shape** (IMPLEMENTER): proposal id, commit SHA, the command run,
    the observed output. REVIEWER re-runs it read-only against that SHA and
    answers `CONFIRM` (closes) or `OBJECT` (continues). Observation before
    interpretation: command, exit code, excerpt, then verdict. `COULD NOT RUN`
    is a valid result and is not a pass.
12. **Transcripts are readable evidence, not a decision channel.** Either side
    may read this pair's transcripts by default; another pair's only when the
    human explicitly asks for outside help. This file is the sole record:
    transcript content counts only after it is restated here, cited by
    absolute path and line. A `CONFIRM` rests on an observable in the
    worktree, never on the other side's reasoning.
13. **No live agents at the flip.** Before handing over, none of your own
    background subagents may still be writing into the worktree the other
    side is about to read. `git status` cannot tell in-flight work from
    residue.
14. **Route first, then delete.** Before this file is deleted: IMPLEMENTER
    folds every ledger line into the commit messages and memory files it
    belongs to (decisions, lessons, deferred work); REVIEWER `CONFIRM`s the
    routing; then either side deletes the file. An unrouted ledger is the
    only record of why the code looks the way it does.
15. **The governance floor still applies to both sides**: governance checks
    before non-read actions, discovery before changing code, per-push
    authorization from the human, one writer per checkout.
16. **Timestamp every message.** `append` writes `Reviewed: <local time>` as
    the last line (`--tz` for a named zone). It is the human's recency signal
    after stepping away.

## Decisions ledger — one row per closed proposal, appended by IMPLEMENTER

| Id | Decision | Commit |
|---|---|---|

## Thread — append-only, chronological
