# Post-Change Completion Checklist

Run this after making changes and before pushing. Invoke via `/completion-sequence`.

## Continue or hand off

Run the applicable validation and recording steps after each change. A completed
step or durable checkpoint is not the end of an authorized task: if useful work
remains within scope, give a concise progress update and continue it in this task.
Do not request renewed permission merely because a check, commit, status report or
context compaction occurred. If one dependency is blocked, continue independent work;
record the blocked check honestly and do not advance through its dependent gate.

Use Branch Completion when a delivery/checkpoint operation is due or a real handoff
is needed. End the task only when its acceptance criteria are met, the user pauses or
cancels, necessary input/authority is unavailable, or a demonstrated runtime/resource
limit prevents further useful authorized work. Preserve the resumption point and
state the precise prerequisite when handing off. Publication and cleanup retain all
their existing approval, verification and ownership requirements.

If a real blocker prevents required validation, preserve an explicitly **unvalidated
local recovery checkpoint** before handing off: record what passed, failed or
could not run and the exact resumption prerequisite in a task-local note, then
commit locally with a `checkpoint:` prefix. Refresh when available before writing
final shared memory, then commit that snapshot too. If refresh or commit is blocked, retain
the working files and disclose that limitation. This is recovery, not a completed
Branch Completion operation: do not push through an unmet gate, publish, activate,
or claim remote durability. Source defects remain work to fix, not permission to
skip validation.

## Before any refresh

This applies to every refresh path, including local recovery, Option C and Option D.
Before the first refresh of an older union-configured branch, apply and commit the
current framework-memory `merge=text` rules in its `.gitattributes`, preserving
unrelated attributes. Verify `git check-attr merge -- <memory-path>` reports `text`.
Do this before any memory merge: the refresh that brings in text rules can itself
silently union-merge using the old attributes. Start the helper with a clean tree.

## Code changes

1. **Tests pass** — run the project's test suite before pushing. Don't push code that breaks existing tests.
2. **Tests written for new behavior** — new features and bug fixes should have tests. Write tests WITH the implementation, not after.
3. **No credentials staged** — check `git diff --cached` for API keys, tokens, passwords, `.env` files, or private keys. Remove before committing.
4. **Code review for substantial changes** — for changes touching >5 files, security-sensitive code, or complex logic, get a review (human or automated) before merging. **Review the diff you are actually pushing.** A review of an earlier state does not cover code written after it, and if you applied review findings the reviewed state is by definition not the pushed state — decide whether the delta needs another look. If your project automates this check, know what it verifies: most such checks can tell that a reviewer *ran*, not that it read the code you are shipping.
5. **README/docs updated** — if the change affects user-facing behavior, CLI usage, configuration, or API surface, update documentation to match.
6. **Commit message explains why** — subject line ≤72 chars describes WHAT; body explains WHY. Future readers need the motivation, not a restatement of the diff.

### Mid-execution checkpoint

When a task exceeds a complexity threshold (≥5 file changes OR multi-phase plan), pause at a natural boundary:

- Re-read the plan or task description end-to-end
- Compare what's been delivered vs. what was planned
- Decide: continue as planned, adjust the plan, or stop and regroup

### Session state

7. **Route durable memory now; write the final session snapshot after refresh.** Decisions, lessons, work, and cadences may be recorded while implementing. On a topic branch, defer the final current-position snapshot to the selected Branch Completion path after refresh so it is written on top of the latest live integration branch.

## Documentation-only changes

1. On a topic branch, defer the final session-state snapshot to Branch Completion after refresh.
2. Run **Branch Completion** below.

## Branch Completion

For the current branch operation, choose one of the five mutually exclusive paths
below and run its checklist. Completing that operation does not end other authorized
work; apply the Continue or hand off rule above.

**Decision tree:**

```
Is the work complete (acceptance criteria met, tests green)?
├─ YES → Is human review required before this lands on trunk?
│        ├─ YES → Option B: OPEN PR
│        └─ NO  → Is this branch the trunk (main/master)?
│                 ├─ YES → Option A: COMMIT-AND-PUSH (push main)
│                 └─ NO  → Option C: MERGE (push to main, clean up branch)
└─ NO  → Is the work salvageable (worth preserving and continuing)?
         ├─ YES → Option D: KEEP OPEN (commit checkpoint, push, leave branch)
         └─ NO  → Option E: DISCARD (commit nothing, clean up local, document why)
```

### Option A — COMMIT-AND-PUSH (working on trunk)

Use when working directly on `main`/`master` and the work is complete.

If the repository declares the default-branch publication gate, Option A is
blocked: move the work to an isolated topic worktree and use Option C.

- [ ] All applicable checks above are satisfied
- [ ] `git status` + `git diff` show the **intended diff** — no unintended files, and nothing stray (a regenerated artifact that changed *format* not content; a file touched by another process — surface it, don't commit or discard). Triage anything unexpected: fix now if small and known (≤~3 files, no cascade), else defer with tracking or flag to the user.
- [ ] Commit message follows project convention
- [ ] Push to remote
- [ ] Verify CI green (if CI is configured)

### Option B — OPEN PR (human review required)

Use when the branch needs review before merging.

- [ ] All applicable checks above are satisfied
- [ ] Push the branch with upstream tracking
- [ ] Create PR with summary and test plan
- [ ] Self-review the diff — would a reviewer follow the change without clarifying questions?
- [ ] Tag reviewers if needed
- [ ] Do NOT merge yourself unless authorized

### Option C — MERGE (feature branch, no review needed)

Use when work is complete on a non-trunk branch and you can merge directly.

- [ ] All applicable checks above are satisfied; commit the intended implementation so the tree is clean
- [ ] Apply the shared Before any refresh prerequisite above if this is an older union-configured branch
- [ ] Resolve the completion helper and refresh from the explicit live default:
      `CS=~/.claude/skills/completion-sequence; [ -f "$CS/integrate.sh" ] || CS=~/.codex/skills/completion-sequence; bash "$CS/integrate.sh" refresh --default-ref <default>`
- [ ] If refresh integrated new commits, resolve conflicts and rerun affected tests
      **How to resolve a session-snapshot conflict, because "resolve conflicts" does not say:**
      the LATEST SESSION TO WRITE wins — that is *you*, the one resolving. Take the
      sibling's version of the snapshot file wholesale, then re-apply your own current
      position on top. Do not hand-merge the two into a blend, and do not keep yours by
      discarding theirs: their durable content was routed to the append-only files
      before they wrote, and yours is the state that is current at the moment of the merge.
      **Tracked framework memory merges like code.** Resolve overlapping edits and
      deletion/edit conflicts deliberately; preserve each intended record once.
      Independent additions at the same boundary can conflict too. Review retained
      BACKLOG IDs reported by the detector against the intended resolution; the
      notice does not require re-deleting an intentionally kept entry.
- [ ] Now update the final session snapshot on top of the refreshed version; route durable decisions/lessons/work/cadences to their owning files first, then commit the closeout
- [ ] Publish with `bash "$CS/integrate.sh" publish --default-ref <default>`. The helper runs `scripts/check.sh --full` on exact topic `HEAD`, requires one new structured record with zero failed or unavailable checks, refuses if the check changes `HEAD` or dirties the tree, pushes that commit for durability, proves the live default did not move, then supplies the local one-shot token for the fast-forward default push. Exit 3 is a concurrent winner, not completion: repeat refresh → affected tests → rewrite closeout snapshot → commit → publish. Any other nonzero exit is a stop.
- [ ] If in a framework-owned v2 worktree, leave it and run: `CL=~/.claude/skills/start-worktree/cleanup.sh; [ -f "$CL" ] || CL=~/.codex/skills/start-worktree/cleanup.sh; bash "$CL" <path> --default-ref <default> --owner-pid <recorded-owner-pid>`. This is cooperative owner acknowledgement, not authentication, and does not bypass any cleanup proof. For v1/legacy trees, omit `--owner-pid`; they retain the conservative proved-dead path.
  **Note:** Do NOT use `ExitWorktree(action: 'remove')` — it fails in continuation sessions due to session-identity ownership. Use `ExitWorktree(action: 'keep')` to detach the session, then run the cleanup script from the primary checkout.
- [ ] Delete the remote feature branch if previously pushed: `git push origin --delete <branch>`
- [ ] Treat GitHub CI as optional clean-runner evidence when it runs; a billing-blocked or absent workflow does not override the internal exact-HEAD result

**Force-push trap:** Do not force-push either branch. `integrate.sh` merges the live default into the topic and publishes only a fast-forward refspec after the internal full check passes on exact `HEAD` and the live default stays unchanged.

**Local-hook boundary:** Supported publication uses the helper's one-ref pushes.
`--no-verify` and a multi-ref push can bypass the client hook because pre-commit
evaluates only the first non-deletion ref; neither is server-side protection.

### Option D — KEEP OPEN (durable checkpoint or handoff)

Use when incomplete work is worth preserving, during continued execution or at a
necessary handoff. After saving the checkpoint, continue available authorized work;
only a genuine handoff defers it to another session.

- [ ] Tests pass for the partial work (no broken-state checkpoint)
- [ ] Commit intended partial implementation locally with a `wip:` or `checkpoint:` message so refresh starts clean
- [ ] Refresh from the live default branch; resolve conflicts and retest affected changes
- [ ] Update session state with what's done, what's next and where to resume; commit the snapshot before pushing
- [ ] Push the checkpoint branch through existing gates; verify remote HEAD and clean tracked state before claiming remote durability
- [ ] Do NOT open a PR for a checkpoint (signals false readiness)

### Option E — DISCARD (work didn't pan out)

Use when the approach was wrong and won't be resumed.

- [ ] Document what was tried and why it didn't work (in a learning log, commit message, or session notes)
- [ ] Clean up local changes (confirm with user before destructive operations)
- [ ] If in a worktree: run the cleanup script as in Option C, but **add `--allow-unmerged`** — discard means the work deliberately never landed, and the script refuses to remove an unlanded worktree without it. That refusal is how a *forgotten* branch gets caught, so the deliberate case has to say so explicitly. The remote branch survives; the local branch does not.
  **Do this BEFORE deleting the remote branch, if you delete it at all.** `git push origin --delete <branch>` also drops the local remote-tracking ref, which makes the commits unreachable from any remote — cleanup then refuses at the durability check, and `--allow-unmerged` does not bypass that one (nothing does: at that point this checkout holds the only copy).
- [ ] Update session state to remove the abandoned work
