# All clear — procedure

Run Step 1 every time. Steps 2–4 are how you read the result and what to do about
each finding class. Every step is mechanical; none of it requires judgment about
whether work is "done."

---

## 1. Run the check

```bash
AC=~/.claude/skills/all-clear/allclear.sh
[ -f "$AC" ] || AC=~/.codex/skills/all-clear/allclear.sh
bash "$AC"
```

| rc | Meaning | Do |
|----|---------|-----|
| 0 | All clear | Report it, including the scope line if `repo_hygiene.py` was absent. Done. |
| 1 | Findings | Work Step 3. Each finding carries its own `→` command. |
| 2 | Undetermined | A check could not run. Report the `?????` lines. **Never call this clear.** |
| 3 | Not a git repository | Say so. Nothing else to do. |
| other | Script missing (127) or crashed | **Stop and tell the user.** Do not improvise. |

Useful flags: `--repo <path>` to inspect a different checkout, `--prefix <str>` if
this project's session branches are not named `wt/`, `--quiet` for findings only.

---

## 2. Read the sections in order — they are ordered by what destroys work

**WORKTREES.** `DIRTY` means uncommitted files, which is the only class here that
exists on exactly one disk and dies with the directory. `live` means a session still
owns that worktree — leave it alone; it is presence, not residue. `done` means clean
and landed, so the worktree has outlived its purpose and can be removed.

**BRANCHES.** `LOCAL` means commits that exist on no remote — still one disk, still
losable. `OPEN` means commits that exist on a remote but have not landed in the
default branch: not lost, but stranded where nothing will look for them again.
`note` means a branch outside the session prefix — a bot's, a collaborator's, a PR's.
It is listed for visibility and deliberately does not gate the verdict.

**STASHES.** A stash survives a clean `git status`, which is what makes it easy to
forget. Never drop one to clear the report.

**MEMORY.** `STALE` means commits landed after the handoff directory was last
touched, so resuming from it means resuming from a description of an older repo.
The report gives you the `git log` range that covers the gap. This section is a
**check, not a write** — updating the notes is the completion sequence's job
(item 17), and this skill deliberately authors nothing. Absent directory: skipped
silently, since most repos keep none.

**STANDING HYGIENE.** Delegated to `repo_hygiene.py` (open PRs, unpushed tags,
keep-markers, stale-branch evidence) when the repo has it. When it does not, the
report says which surfaces went unexamined — read that line before calling anything
clear.

---

## 3. Resolve findings, in this order

Work the classes in the order they can lose work, not the order they are printed.

1. **Uncommitted files** — commit them, or stash them deliberately with a message
   that says why. Do not `git clean` anything you have not looked at.
2. **Local-only commits** — `git push -u origin <branch>`. Committed-but-local is
   still one disk.
3. **Unlanded branches** — merge them, one at a time. Read the `git log` handle the
   report gives you first; the point is to see *what* is unlanded before deciding it
   should land. If several sessions are landing in sequence, each one after the first
   needs a `git fetch` before it can fast-forward.
4. **Clean, landed worktrees** — remove with `cleanup.sh` from the `start-worktree`
   skill. It re-runs its own safety pre-checks; that duplication is intentional.
5. **Stale memory** — update the handoff files yourself (or run the completion
   sequence, which walks them). Read the `git log` range the report prints first; the
   point is to write what actually happened, not to touch the files so the check
   goes quiet. This tool will never write them for you.
6. **Stashes and foreign branches** — decide, do not clear. These are the two classes
   where "make the report go green" is the wrong instinct.

**Never delete a branch because this report listed it.** Ancestry lies after a rebase
or squash: a branch can be fully landed and still look unmerged, and it can look
merged when substantive work differs. That is why no delete command appears anywhere
in the output, and why one should not appear in your response either.

---

## 4. Report to the user

One short block:

- the verdict and its exit code
- what is outstanding, grouped by the class above, worst-first
- what was **not** checked (the scope line, when `repo_hygiene.py` was absent)
- how many sessions are still live, if any

If the verdict is 0, say so plainly and name the scope. "All clear on worktrees,
branches and stashes; PRs and tags not examined" is an honest all-clear. "All clear"
with an unstated scope is the hand-written claim this skill was built to replace.

---

## Notes

**"Can I pick up where I left off?" — what this does and does not answer.** It tells
you the tree is clean, everything landed, nothing is stranded, and the handoff notes
are not describing an older repo. It cannot tell you the notes are *useful*: that is
prose, written by whoever did the work. Run the completion sequence when you want the
notes written; run this when you want to know whether anything was left behind.

**Why this is not part of the completion sequence.** They answer different questions
at different frequencies. The completion sequence's unit is *a change* — tests,
review, docs, memory files — and it can run several times in a session. This skill's
unit is *the repository across all sessions*, and it runs once, usually after the
last session in a fleet is finished. Folding a derived binary check into a long
advisory checklist buries it, and coupling them forces the expensive one to run
whenever you want the cheap one.

**Relationship to the other two scripts.** `preflight.sh` opens a worktree's
lifecycle, `cleanup.sh` closes one, and this closes the *fleet*. All three share the
same safety hierarchy: a false "you are clear" is expensive, a false "not clear" is
merely inconvenient, so every ambiguous case degrades toward "not clear."

**On running it mid-session.** It is read-only and cheap, so there is no reason not
to. Expect findings — your own in-flight work is uncommitted by definition. It is
most useful at the moment you think you are finished.

"Cheap" has one caveat worth knowing: where `repo_hygiene.py` is present it is run
without `--offline`, so a `gh pr list` goes out on a 5-second timeout. Everything
else is local git. Reads use `--no-optional-locks`, so running this alongside a live
sibling session cannot contend for `index.lock`.
