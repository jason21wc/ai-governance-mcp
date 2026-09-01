# Concurrent worktree procedure

## Intent

Give every mutating Claude or Codex session its own checkout and topic branch,
publish the recovery handle before edits, and make interrupted startup retryable.
All hosts share the same Git invariants, but each host keeps its native checkout
lifecycle: Claude Code enters a framework-created tree, an authorized Codex CLI
session creates and targets its own tree (with an ordinary-shell fallback), and
Codex Desktop adopts its own detached tree.

Read-only or conversational sessions do not need a worktree.

## 1. Identify the host and current checkout

Run:

```bash
pwd -P
git rev-parse --show-toplevel
git rev-parse --git-common-dir
git branch --show-current
git worktree list --porcelain
```

Do not infer the host from the terminal application. Warp is a terminal; the host
inside it may be Claude Code or Codex CLI. Never silently adopt an existing
worktree. Re-entry is an explicit ownership action because another live session
may still own it.

Resolve the script once:

```bash
SW=~/.claude/skills/start-worktree
[ -f "$SW/prepare.sh" ] || SW=~/.codex/skills/start-worktree
[ -f "$SW/prepare.sh" ] || { echo "start-worktree skill is not installed"; exit 2; }
```

## 2. Refresh and choose the base explicitly

From the primary checkout, fetch the integration branch before creation:

```bash
git fetch origin
```

Determine the default branch from the live remote, not a hard-coded `main`, and
pass both the exact start point and its branch name to `prepare.sh`. A normal
fresh start uses `--base origin/<default> --default-ref <default>`. If reviewed,
unpushed local commits are intentionally part of the base, use the local branch
instead and say why.

`preflight.sh` returns 0 only when every required surface was checked. Exit 1 is
a known block. Exit 2 means a required fact could not be established and is not
permission to continue. `PREFLIGHT_OFFLINE=1` deliberately produces exit 2.

Branch names are `wt/<slug>-<nonce>`. Let `prepare.sh` generate the nonce; use
`--nonce` only for deterministic reproduction or tests. Exact local refs, every
registered worktree, and exact live remote refs are independent collision
surfaces.

The lifecycle also records task intent. By default creation derives
`task_key=slug:<work-slug>`. Use `--task-key <key>` when two differently named
worktrees implement the same task; keys match `[a-z0-9][a-z0-9._:/-]*` and are at
most 128 characters. A sequential duplicate active key refuses. Deliberate
parallel work must use an explicit key together with `--allow-parallel-task`, so
the exception remains visible to fleet diagnostics. This detects duplicate
intent; it is not a mutex and does not replace unique worktree paths.

## 3. Use the host adapter

### Claude Code

From the primary checkout:

```bash
bash "$SW/prepare.sh" claude-create \
  --slug <work-slug> \
  --base origin/<default> \
  --default-ref <default> \
  --owner-pid "$PPID"
```

Only after `READY`, call `EnterWorktree(path="<printed-absolute-path>")`. Then
verify `pwd -P`, `git rev-parse --show-toplevel`, and `git branch --show-current`.

To reclaim a previously prepared Claude tree after its recorded owner ended:

```bash
bash "$SW/prepare.sh" claude-resume --path <absolute-path> --owner-pid "$PPID"
```

The command refuses a different live owner. It never guesses that an existing
tree is abandoned.

### Codex CLI in Warp or another terminal

**Standard path — agent-managed creation.** When the active Codex profile permits
network access and writes to the repository's common Git directory, Codex creates
the worktree itself. The user does not run or remember this command. From the
primary checkout, Codex runs:

```bash
bash "$SW/prepare.sh" codex-cli-create \
  --slug <work-slug> \
  --base origin/<default> \
  --default-ref <default> \
  --owner-pid "$PPID"
```

After `READY`, Codex validates the printed path and anchors every subsequent file
and command operation to it; the conversation does not need to restart:

```bash
bash "$SW/prepare.sh" codex-cli-validate \
  --path <printed-absolute-path> \
  --owner-pid "$PPID"
```

The session's original workspace root and permissions do not move when its tools
target the new path. Worktree isolation remains a Git workflow invariant, not a
sandbox boundary against the primary checkout or sibling trees. This matches the
ordinary Claude Code trust model selected for writing peers.

**Fallback — an authorized ordinary shell.** If the active profile cannot write
the common Git directory or reach the remote, stop before editing. If the helper
printed `Recovery: ... continue --path ...`, worktree creation already mutated Git:
hand off that exact command, including its numeric owner PID, and do **not** run a
second create. The shell performs the denied transition on behalf of the same live
Codex owner; after `READY`, the current conversation validates and targets the path.

If no recovery command was printed and no worktree was registered, hand off the
original `codex-cli-create` command with the current Codex owner PID rendered as a
number rather than re-evaluating `$PPID` in the other shell. A pre-launch bootstrap
may instead use `--owner-pid "$$"` and then replace that shell so its PID becomes
the Codex PID:

```bash
exec codex -C <printed-absolute-path>
# or: exec codex fork -C <printed-absolute-path>
# or: exec codex resume -C <printed-absolute-path>
```

**Choose the session's authority at launch — it cannot be chosen later.** This is the
only place a Codex session is started, and until 2026-08-24 it said nothing about
permissions, so every session silently inherited whatever `default_permissions` was
configured. A session *told* to be read-only is not read-only; instructing it is a
request, and the profile is the restriction. Pick deliberately:

```bash
# Writing peer — the ordinary case, same standing as a Claude Code session.
exec codex -C <path>

# Reviewer that structurally cannot write, for read-only passes.
exec codex -C <path> -c default_permissions="governed-ro"
```

Two traps worth knowing: an explicit `-s <mode>` flag **overrides** the profile, and the
built-in modes carry none of the credential denies the framework profiles add; and a
`:workspace`-extending default also loosens a bare `codex exec` from read-only to
workspace-write. If you need to know what a running session actually has, read the
effective mode from inside it rather than inferring it from the launch line.

The writing profile may grant the repository's Git control plane through its
configured filesystem permissions. That is the whole shared control plane, not a
narrow branch-only capability. Do not add `--add-dir <common-git-dir>` here: the
profile-based route is the standard, and BACKLOG #348 tracks its remaining live
lifecycle verification.

If Codex was launched directly in a prepared worktree, validate before editing:

```bash
bash "$SW/prepare.sh" codex-cli-validate --owner-pid "$PPID"
```

Validation proves the checkout/branch/owner contract; it does not grant new
filesystem authority. In a managed profile that makes only the worktree checkout
writable, Codex can edit and test there but Git may still refuse `fetch`, `add`,
`commit`, ref updates, integration, and removal: a linked worktree's index and
refs live under the repository's **common Git directory**, not in the checkout.
Run those denied Git-control operations from an ordinary shell (or another
explicitly authorized environment) against the printed path. Do not report this
as a skill failure—the skill ran and exposed a lower-level permission boundary.

If an already-running conversation has common-Git authority, use the standard
agent-managed path above. If it does not, keep that conversation and use the
ordinary-shell fallback only for denied Git operations; the conversation then
validates and targets the prepared path. Fork/resume with `-C <path>` only for a
true pre-launch bootstrap or an intentional relaunch.

### Codex Desktop

Start the chat using Desktop's native per-chat Worktree environment, then attach
and publish a unique branch from that detached checkout:

```bash
bash "$SW/prepare.sh" codex-desktop-adopt \
  --slug <work-slug> \
  --default-ref <default>
```

The native detached `HEAD` must equal the live `origin/<default>` SHA. If it is
stale, recreate or refresh the Desktop-native worktree before adoption; the
framework will not silently root a topic branch at an obsolete commit.

The framework records and initializes the tree but does not lock, unlock, remove,
or relocate it. Codex Desktop retains checkout lifecycle ownership. A permanent
shared Desktop worktree is not a substitute for one checkout per mutating chat.

## 4. Recover partial startup

Framework creation atomically creates a locked worktree whose
`ai-worktree-v2` lock carries the journal's task and parallel-intent fields,
then records these transitions in a strict ordered v2 journal in the linked
gitdir. The older `ai-worktree-v1` label is legacy evidence, not a v2 lock:

```text
created -> published -> locked -> ready
                              \-> setup-failed
post-create duplicate race -> task-conflict
```

Codex Desktop writes `attached` ownership before switching branches, then uses
`attached -> published -> ready`. A failed framework transition retains its
atomic lock; a failed Desktop transition retains native ownership state. Both
print an exact `continue` command and can be inspected with:

```bash
bash "$SW/prepare.sh" status --path <absolute-path>
```

After correcting the reported cause, resume without recreating anything:

```bash
bash "$SW/prepare.sh" continue --path <absolute-path> --owner-pid <owner-pid>
```

`continue` is idempotent at `ready`, blocks a different live framework owner, and
retries only the incomplete transition. A `task-conflict` tree is locked and
non-ready: its recorded owner may continue only by repeating the explicit task
key with `--allow-parallel-task`, or may abandon the pristine tree through the
owner-acknowledged cleanup path below. Do not delete a partial tree as a first
response; its branch or checkout may already contain the only recovery handle.

## 5. Finalize a framework-owned worktree

After publication and from outside the target checkout, the recorded owner may
finish in one operation:

```bash
bash "$SW/cleanup.sh" <absolute-path> \
  --default-ref <default> \
  --owner-pid <recorded-owner-pid>
```

The PID is cooperative acknowledgement, not authentication. It works only for
a coherent v2 framework journal in `ready` or pristine `task-conflict`, with a
matching `ai-worktree-v2` Git lock, and is incompatible with `--force`. It
waives only the live-owner refusal; durability, integration completeness,
tracked cleanliness, and sensitive ignored-file checks still apply. Cleanup
rechecks the journal, lock, branch, HEAD, tracked state, and sensitive ignored
files immediately before removal. There is no persistent `released` state.

V1, legacy, and Desktop-owned trees cannot use this exception. Their existing
conservative lifecycle remains in force. If removal fails after runtime teardown,
the lock is restored but the runtime hook may already have run. If worktree
removal succeeds and only local branch deletion fails, the branch is the recovery
handle; the removed journal and lock cannot be restored.

## 6. Namespace resources Git does not isolate

A project may provide these tracked, optional hooks:

```text
.ai-worktree/setup.sh
.ai-worktree/teardown.sh
```

They receive `AI_WORKTREE_ID`, `AI_WORKTREE_PATH`, `AI_WORKTREE_BRANCH`, and
`AI_WORKTREE_DEFAULT_REF`; setup also receives `AI_WORKTREE_HOST` and
`AI_WORKTREE_PRIMARY`. Use them for per-tree ports, database names, caches,
containers, virtual environments, and generated local configuration. Setup and
teardown must be idempotent because an interrupted transition is retried.

Before trusting tests, verify the runtime resolves code from this checkout. For
Python, for example:

```bash
python -c 'import your_package; print(your_package.__file__)'
```

Inspect symlinks before editing because a symlink may still point into the primary
checkout.

## 6. Clean up only after integration

The completion sequence owns commit, refresh, integration, and push. Once the work
has landed, run cleanup from a different checkout:

```bash
bash "$SW/cleanup.sh" <absolute-worktree-path> --default-ref <default>
```

Use `--dry-run` first when state is unfamiliar; it never runs Desktop teardown.
`--force` skips only PID liveness;
it does not bypass commit durability, integration completeness, dirty files, or
ignored sensitive files. `--allow-unmerged` is only for deliberate discard after
the branch is durable on a remote.

For framework-owned trees, cleanup runs the teardown hook, unlocks, removes the
tree, and deletes the local topic branch. If removal fails after unlock, it restores
the original lock. If branch deletion fails, it returns an error and states that
the remaining branch is still recoverable. For Codex Desktop, cleanup runs only
the teardown hook and leaves checkout removal to Desktop.

## Handoff

Report the host, branch, absolute path, explicit base/default, upstream, lock or
native-owner status, recovery SHA, and any resource-isolation hook that ran. If a
matrix cell was not exercised live, name that exact gap; do not generalize a
hermetic test into a claim about every host UI.
