---
name: pair-channel
description: Use when the user says "pair channel", "paired session", "implementer and reviewer sessions", "tempcom", "Codex/Claude pair", or wants a second AI session to review a first one's work as it happens. Runs a two-session pairing — an IMPLEMENTER session that writes code and a read-only REVIEWER session — through one untracked channel file, with consensus before implementation. Do NOT use for a single session's self-review (use /code-review), for the alternating IMPLEMENTER/VERIFIER handoff file (SESSION-HANDOFF.md), or for subagent review inside one session.
disable-model-invocation: true
allowed-tools: Bash Read Write
---

# Pair Channel

Read `procedure.md` completely before creating or joining a channel. It carries
the protocol; this file only tells you how to operate it.

**The instrument is `channel.py`, beside this file. Every write to the channel
and every wait goes through it.** The protocol's only concurrency guard is
"the session named by `TURN:` writes; the other waits." Written as a rule it
was voluntary and it failed in another project on the first day; as a script
it is checkable, and its mutating commands run under a lock.

```bash
PC=~/.claude/skills/pair-channel
[ -f "$PC/channel.py" ] || PC=~/.codex/skills/pair-channel

python3 "$PC/channel.py" init   <channel> --set CHANNEL_NAME=tempcom1 --set REVIEWER_HOST="Claude Code" ...
python3 "$PC/channel.py" state  <channel>                       # TURN / NEXT_SEQ / OPEN / ESCALATED
python3 "$PC/channel.py" append <channel> --role REVIEWER --message msg.md --flip-to IMPLEMENTER --set-open P1
python3 "$PC/channel.py" fill   <channel> --role IMPLEMENTER --set IMPLEMENTER_WORKTREE=/abs/path
python3 "$PC/channel.py" ledger <channel> --role IMPLEMENTER --id P1 --decision "…" --commit abc123
python3 "$PC/channel.py" watch  <channel> --role REVIEWER       # blocks; exit 0 = your turn, 2 = file gone
python3 "$PC/channel.py" check  <channel>                       # every invariant; run when anything looks odd
```

`append` refuses: an out-of-turn write, a wrong or duplicate sequence number,
two messages in one file, an unbalanced code fence, and any thread line
beginning with `TURN:` outside a fenced quote (TURN lives only in STATE). It
stamps the timestamp, updates STATE, and re-verifies. `fill` (header tables
only) and `ledger` are the rule-1 carve-outs with the same turn check. Every
mutating command holds `<channel>.lock`. `watch` reads STATE, never the thread.

## Starting a pairing (REVIEWER does this)

1. Both sessions already have their own worktrees (`/start-worktree`). The
   reviewer never writes a tracked file, so its worktree stays at zero commits.
2. Create the channel OUTSIDE both worktrees in a gitignored place both can
   reach — on this framework's repos, `<repo>/.claude/worktrees/<name>.md`, which
   `.git/info/exclude` hides. Confirm with `git status` in every worktree.
3. `init` with every placeholder you know; the implementer fills its own rows
   with `fill` when it holds the turn for message #2.
4. Write message #1 as a channel test (`procedure.md` §0), `append` it with
   `--flip-to IMPLEMENTER --set-open P0`, then `watch --role REVIEWER` in the
   background (Claude Code: `run_in_background: true`).
5. Give the human ONE prompt for the implementer session that points at the
   file (`procedure.md` §7). After that the human relays no content — the
   file carries it all. Establishing the pairing standing-authorizes ordinary
   channel messages and turn flips; neither role asks again per message. The
   V-016 cadence still limits review to four boundaries, not every choice.

## Every turn

- Woken by `watch`? Run `state` anyway before composing — the watch is a
  signal to re-check write eligibility, never a bypass of STATE.
- Before every `append`, give the human a brief, human-visible status with
  four fields: **Accomplished**, **Current task**, **Other AI**, and **Next**;
  then proceed without waiting. This is notification, not an approval request.
  This grant covers coordination only; irreversible or external effects remain
  separately human-authorized.
- Compose the message in a scratch file whose first line is
  `## #<NEXT_SEQ> <YOUR ROLE> <TYPE …>`. Verify claims from the source before
  writing them (rule 11). Then `append`, then re-arm `watch`.
- A human directive that the other side must see: `append --out-of-turn` with
  "out of turn" in the heading; it does not flip TURN (`procedure.md` §3).
- `append` says `REFUSED`? Do not work around it. Read the reason; if it names
  a duplicate or a gap, stop and escalate to the human.

## Ending a pairing

Rule 14: route the Decisions ledger into commit messages and memory files,
`CONFIRM` the routing, clean up worktrees and remote topic branches under the
human's authorization, delete the channel and its `.lock` last.
`procedure.md` §6.

## Governance

`evaluate_governance` before any non-read action stays in force for both
sessions (rule 15). Cite `multi-reliability-explicit-handoff-protocol` when the
channel's shape influences a decision; the channel is its Agents-as-Tools
pattern with the human as the only cross-session relay.
