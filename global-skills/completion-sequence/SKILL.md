---
name: completion-sequence
description: Run post-change validation and finish a branch safely, including concurrent worktree refresh, optimistic fast-forward publication, retry, checkpoint, PR, or discard paths. Use after changes and before pushing, merging, handing off, or cleaning up a worktree.
---

# Completion Sequence

Read `checklist.md` completely and apply the sections matching the actual change.
For a completed topic worktree, use `integrate.sh`; it makes the default branch
explicit and distinguishes a concurrent publish race (exit 3) from other failures.

The load-bearing order (design of record: **ADR-31**, which carries the scratch-repo evidence for why this ordering and not another) is:

```text
commit implementation -> refresh live origin default -> integrate -> retest
-> write closeout memory on that base -> commit -> publish -> retry if origin moved
```

Do not write the final shared-memory snapshot before refresh, do not merge a
possibly stale local default branch, and do not force-push the integration branch.
The helper is optimistic: it detects and repeats after a sibling wins the race
instead of serializing all sessions behind a global lock.
