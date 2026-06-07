# Post-Change Completion Checklist

Run this after making changes and before pushing. Invoke via `/completion-sequence`.

## Code changes

1. **Tests pass** — run the project's test suite before pushing. Don't push code that breaks existing tests.
2. **Tests written for new behavior** — new features and bug fixes should have tests. Write tests WITH the implementation, not after.
3. **No credentials staged** — check `git diff --cached` for API keys, tokens, passwords, `.env` files, or private keys. Remove before committing.
4. **Code review for substantial changes** — for changes touching >5 files, security-sensitive code, or complex logic, get a review (human or automated) before merging.
5. **README/docs updated** — if the change affects user-facing behavior, CLI usage, configuration, or API surface, update documentation to match.
6. **Commit message explains why** — subject line ≤72 chars describes WHAT; body explains WHY. Future readers need the motivation, not a restatement of the diff.

### Mid-execution checkpoint

When a task exceeds a complexity threshold (≥5 file changes OR multi-phase plan), pause at a natural boundary:

- Re-read the plan or task description end-to-end
- Compare what's been delivered vs. what was planned
- Decide: continue as planned, adjust the plan, or stop and regroup

### Session state

7. **Update session state** — if the project tracks session state (a SESSION-STATE.md, TODO list, or equivalent), update it with current position and what's next. Future sessions (or future you) need a clear resumption point.

## Documentation-only changes

1. Update session state if applicable.
2. Run **Branch Completion** below.

## Branch Completion

Final stage for any work session: decide what happens to the branch you're on. The five options below are mutually exclusive — pick one, run its checklist, then stop.

**Decision tree:**

```
Is the work complete (acceptance criteria met, tests green)?
├─ YES → Is this branch the trunk (main/master)?
│        ├─ YES → Option A: COMMIT-AND-PUSH (no merge needed)
│        └─ NO  → Is human review required before this lands on trunk?
│                 ├─ YES → Option B: OPEN PR
│                 └─ NO  → Option C: MERGE (delete branch after)
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

- [ ] All applicable checks above are satisfied
- [ ] Push branch and wait for CI green before merging
- [ ] Merge (squash/merge/rebase per project convention)
- [ ] Delete the feature branch after merge
- [ ] Verify trunk CI green after merge

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
- [ ] Update session state to remove the abandoned work
