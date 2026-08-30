# Post-Change Completion Checklist

Run this after making changes and before pushing. Invoke via `/completion-sequence`.

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

7. **Route durable memory now; write the final session snapshot after refresh.** Decisions, lessons, work, and cadences may be recorded while implementing. On a topic branch, defer the final current-position snapshot to Option C so it is written on top of the latest live integration branch.

## Documentation-only changes

1. On a topic branch, defer the final session-state snapshot to Branch Completion after refresh.
2. Run **Branch Completion** below.

## Branch Completion

Final stage for any work session: decide what happens to the branch you're on. The five options below are mutually exclusive — pick one, run its checklist, then stop.

**Decision tree:**

```
Is the work complete (acceptance criteria met, tests green)?
├─ YES → Is human review required before this lands on trunk?
│        ├─ YES → Option B: OPEN PR
│        └─ NO  → Is this branch the trunk (main/master)?
│                 ├─ YES → Option A: COMMIT-AND-PUSH (push main)
│                 └─ NO  → Option C: MERGE (push to main, clean up branch)
└─ NO  → Is the work salvageable (worth resuming next session)?
         ├─ YES → Option D: KEEP OPEN (commit checkpoint, push, leave branch)
         └─ NO  → Option E: DISCARD (commit nothing, clean up local, document why)
```

### Option A — COMMIT-AND-PUSH (working on trunk)

Use when working directly on `main`/`master` and the work is complete.

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
- [ ] Resolve the completion helper and refresh from the explicit live default:
      `CS=~/.claude/skills/completion-sequence; [ -f "$CS/integrate.sh" ] || CS=~/.codex/skills/completion-sequence; bash "$CS/integrate.sh" refresh --default-ref <default>`
- [ ] If refresh integrated new commits, resolve conflicts and rerun affected tests
      **How to resolve a session-snapshot conflict, because "resolve conflicts" does not say:**
      the LATEST SESSION TO WRITE wins — that is *you*, the one resolving. Take the
      sibling's version of the snapshot file wholesale, then re-apply your own current
      position on top. Do not hand-merge the two into a blend, and do not keep yours by
      discarding theirs: their durable content was routed to the append-only files
      before they wrote, and yours is the state that is current at the moment of the merge.
      **Append-mostly memory files (backlog, lessons) may union-merge silently** — both
      sides survive with no conflict marker, which is usually right. The exception that
      is not right: if you CLOSED an entry (a full deletion) and a sibling edited that
      same entry, their edit wins and your closure is silently undone. Re-check any entry
      you closed after a cross-session merge.
      *(Added 2026-08-24, BACKLOG #348. This rule governed concurrent close-out while
      living in exactly one file that no close-out procedure loaded — so the sessions
      being graded by it were never given it.)*
- [ ] Now update the final session snapshot on top of the refreshed version; route durable decisions/lessons/work/cadences to their owning files first, then commit the closeout
- [ ] Publish with `bash "$CS/integrate.sh" publish --default-ref <default>`. Exit 3 is a concurrent winner, not completion: repeat refresh → affected tests → rewrite closeout snapshot → commit → publish. Any other nonzero exit is a stop.
- [ ] If in a framework-owned v2 worktree, leave it and run: `CL=~/.claude/skills/start-worktree/cleanup.sh; [ -f "$CL" ] || CL=~/.codex/skills/start-worktree/cleanup.sh; bash "$CL" <path> --default-ref <default> --owner-pid <recorded-owner-pid>`. This is cooperative owner acknowledgement, not authentication, and does not bypass any cleanup proof. For v1/legacy trees, omit `--owner-pid`; they retain the conservative proved-dead path.
  **Note:** Do NOT use `ExitWorktree(action: 'remove')` — it fails in continuation sessions due to session-identity ownership. Use `ExitWorktree(action: 'keep')` to detach the session, then run the cleanup script from the primary checkout.
- [ ] Delete the remote feature branch if previously pushed: `git push origin --delete <branch>`
- [ ] Verify trunk CI green after push

**Force-push trap:** Do not force-push either branch. `integrate.sh` merges the live default into the topic and publishes only a fast-forward refspec.

### Option D — KEEP OPEN (work continues next session)

Use when work is incomplete but worth resuming.

- [ ] Tests pass for the partial work (no broken-state checkpoint)
- [ ] Commit message starts with `wip:` or `checkpoint:`
- [ ] Push the checkpoint branch
- [ ] Update session state with: what's done, what's next, where to resume
- [ ] Do NOT open a PR for a checkpoint (signals false readiness)

### Option E — DISCARD (work didn't pan out)

Use when the approach was wrong and won't be resumed.

- [ ] Document what was tried and why it didn't work (in a learning log, commit message, or session notes)
- [ ] Clean up local changes (confirm with user before destructive operations)
- [ ] If in a worktree: run the cleanup script as in Option C, but **add `--allow-unmerged`** — discard means the work deliberately never landed, and the script refuses to remove an unlanded worktree without it. That refusal is how a *forgotten* branch gets caught, so the deliberate case has to say so explicitly. The remote branch survives; the local branch does not.
  **Do this BEFORE deleting the remote branch, if you delete it at all.** `git push origin --delete <branch>` also drops the local remote-tracking ref, which makes the commits unreachable from any remote — cleanup then refuses at the durability check, and `--allow-unmerged` does not bypass that one (nothing does: at that point this checkout holds the only copy).
- [ ] Update session state to remove the abandoned work
