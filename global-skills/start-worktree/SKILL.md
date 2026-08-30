---
name: start-worktree
description: Safely start, resume, validate, or clean up an isolated Git worktree for a mutating Claude Code, Codex CLI, or Codex Desktop session. Use at the start of concurrent work, when moving a session off the primary checkout, when recovering a partially prepared worktree, or before removing a completed worktree.
---

# Start Worktree

Read `procedure.md` completely, identify the actual host, and follow that host's
adapter. The load-bearing behavior lives in the scripts beside this file:

- `preflight.sh` verifies exact local/worktree/live-remote name surfaces and base freshness.
- `prepare.sh` creates or adopts a checkout through recorded, retryable transitions and detects duplicate task intent across isolated paths.
- `cleanup.sh` refuses removal until ownership, durability, completeness, ignored-file, and cleanliness checks pass; a coherent v2 owner can acknowledge finalization atomically without `--force`.

Do not replace a failed or unavailable script with remembered Git commands. An
unrun check is not a pass. Report the script's exit code and findings.

The invariant is one mutating session per checkout and per `wt/*` topic branch.
Task keys detect two isolated sessions doing the same work; they do not replace
that checkout isolation or create a global lock.
A Git worktree isolates tracked files, the index, HEAD, and branch; it does not
isolate ports, databases, daemons, caches, editable installs, ignored files,
user configuration, or symlink targets. Use the optional runtime hooks described
in `procedure.md` when those shared resources need namespacing.

Host permissions remain separate from skill execution. In particular, a managed
Codex profile may permit checkout edits while denying the common Git-directory
writes needed for worktree creation, fetch, staging, commits, refs, and cleanup;
the Codex CLI adapter documents the ordinary-shell handoff for that case.
