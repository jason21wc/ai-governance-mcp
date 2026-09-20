# Paired-session protocol — IMPLEMENTER + REVIEWER, one channel file

## Intent

Two live sessions work one task. The IMPLEMENTER writes code and tracked files
in its own worktree. The REVIEWER is read-only: it reviews the implementer's
worktree at named SHAs and writes exactly one file, the channel. They never
read each other's chat and the human relays nothing between them. Every change
is proposed, confirmed by the other side in its own words, and only then
implemented. Either role can be Claude Code or Codex CLI; the roles are defined
by what a session may do, not by which tool runs it.

Why a second session rather than a subagent: a subagent inherits the author's
framing through its prompt. A separate session gets its whole context from the
channel, so its confirmation is evidence rather than an echo.

Trial record: one pairing on the ai-governance repo (2026-09-02/03, 23
messages, 4 proposals). The reviewer caught a union merge that would have
silently resurrected 26 deliberately deleted log entries, a backlog ID
collision between two branches, and its own invented worktree slug. The
channel file was reordered twice by a patch tool that anchored on repeated
text. One trial, with evidence; not a track record.

## 0. Setup

1. Each mutating session owns a worktree and topic branch (`/start-worktree`).
   The reviewer's worktree will end with zero commits; that is expected.
2. The REVIEWER creates the channel outside both worktrees in a gitignored
   location both sessions can reach, with `channel.py init`, and confirms it is
   invisible to `git status` in every worktree. Number channels per pair
   (`tempcom1`, `tempcom2`, …); a pair reads and writes only its own.
3. Message #1 is a channel test: the implementer must `touch` the file and
   report the exit code, fill its worktree and transcript rows with
   `channel.py fill`, and state its task in one line. A sandbox that cannot write the path is a finding, not a
   failure; the fallback is to move the file into the implementer's worktree
   root.
4. The human gives each session one prompt pointing at the file (§7). From
   then on the file carries all content between the sessions, and ordinary
   channel messages and turn flips are standing-authorized. Before every
   `append`, the sender gives the human the four-field status in §3 and
   proceeds without waiting; no per-message approval is required.

## 1. File structure

- **Header:** what the file is, that it is untracked and temporary.
- **STATE** (one fenced block): `TURN`, `NEXT_SEQ`, `OPEN`, `ESCALATED`. STATE
  carries only what the other side cannot observe. SHAs, tree state and test
  results are observable by running a command; a copy of them here goes
  stale. **`TURN:` exists on exactly one line in the whole file, inside
  STATE.** `channel.py check` fails a file with two.
- **Roles** table: role, host, absolute worktree path, what it may write.
- **Transcripts** table: each session's absolute transcript path, confirmed by
  that session from its own status, never guessed. Claude Code:
  `~/.claude/projects/<escaped-repo-path>[--claude-worktrees-<name>]/<uuid>.jsonl`.
  Codex CLI: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, whose line 1
  `"cwd"` names the project.
- **Rules** (the section below, verbatim in the file so the channel is
  self-contained; a test keeps the two copies byte-identical).
- **Decisions ledger:** one row per closed proposal, appended by the
  implementer, routed at teardown (rule 14).
- **Thread:** append-only, chronological; every message begins
  `## #<n> <ROLE> <TYPE …>` and ends with the `Reviewed:` timestamp that
  `append` writes. Nothing in the thread begins with `TURN:`.

## 2. Rules

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

## 3. Human relay, cadence, and out-of-turn messages

**Cadence (from the V-016 experiment definition, which governs this
protocol's trial):** the REVIEWER is consulted at four boundaries — initial
communication calibration, one substantive plan review before
implementation, completed-work review at a named commit, and final
decision-routing at close-out — not for routine implementation choices a
reviewed plan already implies. Once the human explicitly establishes the
pairing, ordinary messages and turn flips are standing-authorized. Before
every `append`, either role gives the human a brief status containing
**Accomplished**, **Current task**, **Other AI**, and **Next**, then proceeds
without waiting. The status is a tracking update, not an approval request.
The receiving role wakes through its watch or host queue. The flip is the wake
signal, while STATE remains the source of write eligibility.

The human talks to one session, usually the reviewer. A directive the other
side must see goes into the channel as `ANSWER` with "human-directed, written
out of turn, rule 2 exception" in its heading, through
`append --out-of-turn`. It bumps `NEXT_SEQ` and leaves `TURN` where it is; it
may not flip. `append` re-reads STATE first; if the file changed since you
read it, it refuses and you re-read.

An out-of-turn relay is the one moment two writers can be live at once, by
construction: the turn holder may be mid-append. The trial hit this on its
23rd message — the relay and the implementer's `DONE` both took #23 and a
human-authorized reconstruction renumbered one. `channel.py` closes it: every
mutating command holds an exclusive lock on `<channel>.lock` across its read,
validation and atomic write, so the second writer waits, then sees the new
`NEXT_SEQ` and is refused with the reason. It re-reads STATE and retries with
the next number. The lock serialises cooperating writers on one machine; it
does not protect against a session that edits the file with some other tool,
which rule 1 forbids and `check` detects afterward.

Authorization — a push, publish, merge, deletion, destructive cleanup, or
other irreversible or external effect — is the human's.
When the implementer reaches such a step it writes a `QUESTION` addressed to
the human; the reviewer puts it in front of the human and relays the answer
out of turn. Advance authorization must be scoped in the relay message (which
branch, which action, which helper) so its edge is visible later.

## 4. Waiting without polling by hand

```bash
python3 "$PC/channel.py" watch <channel> --role REVIEWER    # or IMPLEMENTER
```

Run it in the background and re-arm after every message you write. It reads
STATE's `TURN:` line only, so text in the thread cannot match. Exit 0 means
STATE names your role; exit 2 means the channel file is gone (a deleted
channel is otherwise indistinguishable from a quiet one); exit 3 means
`--timeout` elapsed. Being woken does not override STATE: `append` checks it
again and refuses if the turn moved.

Claude Code: `Bash` with `run_in_background: true`; the session is re-invoked
when the watch exits. Codex CLI: run it as a foreground command with a
`--timeout` that matches the host's command limit and re-arm on exit 3.

## 5. Execution constraints — decide the executor up front

A sandboxed session may be unable to run the project's publication gate:
network for a dependency audit, a local model for retrieval checks, a tool that
is simply not installed. Ask each session to probe its limits in the first two
messages (`COULD NOT RUN` is a valid result) and name the executor for the
final gate and push before any proposal depends on it. If the executor is the
reviewer, record it in the ledger as a rule-10 exception with the human's
direction quoted; the reviewer's writes are still limited to the gate's own
gitignored records and temp staging, never a tracked file. The push itself
carries the human's per-push authorization regardless of who types it.

## 6. Teardown

In order, each under the human's authorization where it is a push or a
deletion:

1. **Route the ledger** (rule 14): lessons to the learning log, decisions to
   the decisions record, deferred work to the backlog, everything else into
   the commit messages that already carry it. One small commit; a second push.
2. **Clean up worktrees** with the project's lifecycle script, from outside
   each target, owner acknowledged. Never touch a tree that is not this pair's.
3. **Retire remote topic branches** — reported, never automated; a push.
4. **Delete the channel** last, after the reviewer `CONFIRM`s the routing.

## 7. Prompts to give the two sessions

Reviewer: point it at this skill and the channel path; it creates the file and
writes #1. Implementer, once #1 exists — the whole prompt, nothing from the
reviewer's chat:

```
You are the IMPLEMENTER in a two-session pairing; a separate read-only
REVIEWER session reviews your work. Your only channel is <absolute channel
path>. Read it completely, follow its Rules, and use the pair-channel skill's
channel.py for every write (`append`) and every wait (`watch --role
IMPLEMENTER`). Answer message #1 as "## #2 IMPLEMENTER CONFIRM P0": touch the
file and report the exit code, fill your worktree and transcript rows with
`channel.py fill --role IMPLEMENTER --set IMPLEMENTER_WORKTREE=… --set
IMPLEMENTER_TRANSCRIPT=…`, state your task in one line, give the human the
four-field status from §3, then
`append --flip-to REVIEWER --set-open none`. No tracked-file edits until a
proposal id is CONFIRMed. If the write fails, stop and tell me.
```

## 8. Hazards the trial hit

- **Union-merge files** (`merge=union` in `.gitattributes`) resurrect
  deletions on merge. If the branch deletes lines the default branch still
  has, plan to re-apply the deletions after the merge and prove it: every
  deleted heading absent, every heading the default added present once, no
  duplicate headings.
- **Two branches allocate the same backlog IDs** after a long split. Renumber
  the unlanded side to verified-free IDs; check sibling branches too.
- **A dead-owner worktree** is reclaimed through the lifecycle script's
  `continue`, never by hand, and a reviewer never invents a branch slug —
  the skill's own rule says the slug is the human's.
- **Patch tools that anchor on a literal** reorder the channel when the
  literal repeats. `append` writes at end-of-file only.
- **STATE and a per-message marker disagreed** after a reconstruction: the
  message said the turn had moved, STATE said it had not, and the waiting
  session's watch correctly stayed asleep. That is why this revision keeps
  one location. If you inherit a file with both, STATE wins and the
  disagreement is itself an `ESCALATE`.

## 9. Errata — what changed since the first written spec, and why

**The §4 watch was unsound as specified.** The first distilled spec told the
waiting session to `grep -q '^TURN: REVIEWER' <file>` and, separately, to end
every message with a TURN marker. A faithful implementation of both produces a
file that contains both role strings permanently from message #2 on, so the
watch matches immediately and forever for either role. Another project
reproduced this on a live three-message channel; the report is the origin of
this revision.

**Why the trial did not hit it, answered from the file rather than from
memory:** the trial channel had exactly one line beginning `TURN:` (the STATE
block) across 23 messages, because its trailing markers were written as
`*(TURN → ROLE)*`, which does not begin a line with `TURN:`. The §4 command was
run as written eight times in that trial and woke correctly each time. So the
documented protocol was the protocol that ran — but the document omitted the
one formatting fact that made it sound, and a reader who followed the rules as
written would build an unsound file. That is a spec defect, not a false trial
report, and it is the class of defect that a rule cannot fix and an instrument
can.

**What this revision does about it.** TURN has one home (STATE), the trailing
marker is gone, `append` refuses any thread line beginning with `TURN:`
outside a fenced quote, `watch` reads STATE only, and `check` fails a file
that breaks the invariant. The rule-1 carve-out for STATE, placeholder cells
and ledger rows is stated, and each has its own guarded command (`append`,
`fill`, `ledger`) so "write only through the tool" is true for every write a
pairing needs. Rule 3's duplicate-sequence check remains the detector of last
resort, but it is no longer the only guard: every mutating command runs under
an exclusive lock, refuses the out-of-turn write before it happens, and a test
races two writers through the widened window to prove exactly one lands.

A fresh-context review of the first draft of this revision found that its
size check narrowed the race without closing it, and that two of the three
carve-out writes had no command and would have gone through a raw editor. Both
are fixed above; the review is why the lock and the `fill`/`ledger` verbs exist.

Second-location alternatives considered and rejected: a separate one-line
"turn file" doubles the state that must agree; keeping both locations with a
precedence rule keeps the failure mode and adds a rule about it.
