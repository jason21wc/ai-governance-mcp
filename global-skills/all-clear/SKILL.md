---
name: all-clear
description: Fleet-level close-out check across every worktree and branch — is all work committed, durable on a remote, landed in the default branch, and are the finished worktrees removed? Read-only; it prints commands and never runs them. Invoke when the user says "all clear", "are we clear", "close everything out", "session close-out", "did everything land", "wrap up all sessions", "any loose ends", or after finishing several parallel worktree sessions.
---

## Instructions

Read `procedure.md` in this skill folder and follow it in order.

Resolve the date, repository, and worktree list with ordinary read-only commands
when needed. Do not use Claude Code's bang-backtick inline-injection syntax here
(an exclamation mark immediately followed by a backtick-quoted command); Codex
renders it as literal text, and Claude Code EXECUTES it at load — including inside
a code span, which is why this sentence describes the syntax rather than showing
it. Writing it out, even quoted, arms it.

The load-bearing step is `allclear.sh`, which ships beside `procedure.md`. **Run it and
report its exit code.** Do not substitute your own reasoning for it — the entire reason
this skill exists is that a hand-written "nothing pending" rots the moment it is written,
and an agent re-deriving the checks from memory reproduces exactly that failure.

```bash
AC=~/.claude/skills/all-clear/allclear.sh
[ -f "$AC" ] || AC=~/.codex/skills/all-clear/allclear.sh
bash "$AC"
#   0 = all clear — every check ran, nothing outstanding
#   1 = findings — something is uncommitted, unpushed, unlanded, or left behind
#   2 = undetermined — a check could not run. NOT clear. The human decides.
#   3 = not a git repository
#   anything else (127 = script not found) — stop and say so
```

If `allclear.sh` cannot be found, **stop and tell the user.** Do not improvise the
checks by hand.

### Key Principles

- **Three axes, and conflating any two is the defect this exists to catch.** *Clean* =
  nothing uncommitted. *Durable* = the commits exist off this disk. *Landed* = the
  commits reached the branch everyone else reads. None implies another. `cleanup.sh`
  once checked durability and reported it as safe-to-remove, so a branch that was pushed
  and never merged was removed with its local branch deleted — the work survived only on
  a remote ref nothing tracked.
- **Durability is nearly free here, so it is the weakest signal.** `start-worktree`
  step 4c publishes every branch at creation to reserve the name. Every worktree branch
  is therefore durable from birth, which is precisely why durability alone could never
  fail for the workflow it was supposed to guard.
- **Compute it; never recall it.** Every finding is derived from `git` at the moment you
  ask. This repo's scar is a memory file reading "ACTION ON RESUME: nothing pending"
  while two stale branches, an orphan worktree, two unpushed tags, an open PR and five
  unpushed commits accumulated behind it.
- **Presence is not a finding.** A worktree whose lock PID is alive belongs to a session
  that is still working. It is reported, it is counted in the summary, and it does not
  make the verdict red. A checker that flags a busy teammate as residue gets tuned out.
- **Duplicate task intent is a fleet finding, not a deletion license.** V2 journals
  expose task keys across otherwise-isolated worktrees. Unexpected duplicates make the
  report non-green; explicit parallel intent remains visible. Neither case authorizes
  cleanup, and legacy same-slug candidates are labelled ambiguous rather than guessed.
- **Ancestry lies — so report evidence, never a verdict.** After a rebase or squash,
  `--no-merged` will call a fully-landed branch unmerged. This skill offers a *merge*
  command and a `git log` handle for unlanded work. It never offers a delete command,
  in either direction.
- **An unrun check is not a passed check — but say which checks you claim.** Failure to
  resolve a default branch makes merge state unknown for everything, so that returns 2.
  Open PRs and unpushed tags are surfaces `repo_hygiene.py` owns; where that script is
  absent the report says so out loud and scopes its verdict, rather than either
  pretending it looked or refusing to ever go green.
- **It must be possible to go green.** A check that can never pass stops being read, and
  then the one time it matters nobody looks.

### What This Skill Does NOT Do

- **It does not mutate anything.** No push, no merge, no branch deletion, no worktree
  removal. It prints the commands; you run them. Per-push authorization is a deliberate
  gate in this project and a tool that pushed would walk straight through it.
- **It does not decide whether work is complete.** It reports whether work has *landed*.
  Whether the work was any good is the completion sequence's question, and the two are
  deliberately separate skills — you often want to check the repo without re-running a
  full completion checklist, and you often keep working after one.
- **It does not write your handoff notes.** It CHECKS whether the memory directory
  (`_ai-context` by default, `--memory` to change) is behind HEAD, and reports how many
  commits landed since it was last touched. It never authors the prose. Freshness is
  derivable; "what happened and what's next" is a judgment call, and the completion
  sequence owns it (item 17: SESSION-STATE / PROJECT-MEMORY / LEARNING-LOG). Putting a
  prose generator inside the tool built to replace hand-written claims would re-create
  the exact problem its header objects to. So: **a green verdict here means the repo is
  clean and the notes are not out of date — not that the notes are good.**
- **It does not remove worktrees.** When it finds a clean, landed worktree it names
  `cleanup.sh` from the `start-worktree` skill, which has its own safety pre-checks.
- **It does not assume any particular repo.** `git` is the only hard dependency, and
  `repo_hygiene.py` is used when present and reported as absent when not. **It is not
  strictly offline, though:** where `repo_hygiene.py` exists, this skill runs it *without*
  `--offline`, and that script shells out to `gh pr list` (its own docstring calls that
  "The ONLY network call") on a 5-second timeout. That is deliberate — an open PR is part
  of the close-out picture — but it means the check is not purely local. An earlier
  version of this bullet claimed `gh` is never called, which was simply false.
