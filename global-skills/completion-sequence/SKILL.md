---
name: completion-sequence
description: Run post-change validation and finish a branch safely, including concurrent worktree refresh, optimistic fast-forward publication, retry, checkpoint, PR, or discard paths. Use after changes and before pushing, merging, handing off, or cleaning up a worktree.
---

# Completion Sequence

Read `checklist.md` completely and apply the sections matching the actual change.
Its Continue or hand off rule separates per-change validation and durable checkpoints
from ending the authorized task. Continue remaining work after a checkpoint; do not
turn a progress update into a request to proceed.
For a completed topic worktree, use `integrate.sh`; it makes the default branch
explicit and distinguishes a concurrent publish race (exit 3) from other failures.

The load-bearing order (design of record: **ADR-31**, which carries the scratch-repo evidence for why this ordering and not another) is:

```text
commit implementation -> refresh live origin default -> integrate -> retest
-> write closeout memory on that base -> commit -> publish exact topic HEAD
-> run the internal full check -> fast-forward default -> retry if origin moved
```

Do not write the final shared-memory snapshot before refresh, do not merge a
possibly stale local default branch, and do not force-push the integration branch.
The helper is optimistic: it detects and repeats after a sibling wins the race
instead of serializing all sessions behind a global lock.
Where the repository declares the local publication gate, direct default-branch
pushes are blocked and the helper supplies a one-shot exact-HEAD token only after
the repository's internal full check passes without moving `HEAD` or dirtying the
tree, and its structured record reports zero failed or unavailable checks. GitHub
checks are optional clean-runner evidence, not publication authority.
A client hook can still be bypassed deliberately with
`--no-verify`; pre-commit also evaluates only the first non-deletion ref of a
multi-ref push. The helper's supported path uses one-ref pushes. This is
accidental-change prevention, not server-side protection.
