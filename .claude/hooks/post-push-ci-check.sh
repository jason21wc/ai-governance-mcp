#!/bin/bash
# Post-push CI check hook for Claude Code
# Triggers after a Bash tool call that actually RUNS a git push (quoted mentions
# of one do not count — see the trigger note below).
# Outputs CI run status so Claude can monitor for failures

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# GUARDED — the last unguarded `source` in .claude/hooks/, found by a coherence
# audit of the amended fail-closed rule (session-272). This hook is NOT a
# fail-closed gate, so an unguarded source here could not open a security hole —
# but it violated THIS FILE'S OWN contract, stated 12 lines below: "A hook that
# dies on a machine without an optional dependency is not degrading, it is
# failing." A missing lib made it exit 1, which is exactly the death the exit-0
# contract forbids. It was also a live in-repo specimen of the pattern the
# amended rule warns against, sitting where an author would copy it.
#
# The fallback is a no-op stripper rather than an early exit: this hook only
# REPORTS, so degrading to a raw-string match costs an occasional imprecise
# trigger, while exiting would silently drop CI reporting altogether.
# shellcheck source=lib/shell-scan.sh
if [ -r "$HOOK_DIR/lib/shell-scan.sh" ]; then
    source "$HOOK_DIR/lib/shell-scan.sh"
else
    echo "[post-push-ci-check] WARNING: lib/shell-scan.sh missing — matching against the RAW command" >&2
    strip_quoted_regions() { printf '%s' "$1"; }
fi

input=$(cat)

# ---------------------------------------------------------------------------
# EXIT-0 CONTRACT. This hook runs after a user's Bash call and must never disturb
# it — but `set -euo pipefail` made two ordinary conditions fatal, both measured:
#
#   no `jq` on PATH   -> exit 127   (the guard further down at the lookback is
#                                    unreachable; jq is used before it)
#   malformed payload -> exit 5     (jq parse failure kills the assignment)
#
# A hook that dies on a machine without an optional dependency is not degrading,
# it is failing. Same class as BACKLOG #236 in the session-start hooks. Both paths
# now exit 0 quietly; the report is what is optional here, not the user's command.
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract the command from tool_input. `|| echo ""` because a payload jq cannot
# parse must yield "no command", not a dead hook.
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

# ---------------------------------------------------------------------------
# TRIGGER — matched against the QUOTED-REGION-STRIPPED command, not the raw one.
#
# The raw match read prose as an invocation. `git commit -m "...ask before every
# git push..."` pushes nothing, but the message contains both tokens, so this hook
# fired anyway and charged the session a 5s sleep plus up to 17 `gh` API calls for
# a report about somebody else's push. Same root cause the safety gates hit at n=3
# (lib/shell-scan.sh header): a token-anchored matcher cannot tell executable
# position from quoted content — so ask the shared stripper first.
#
# Detection only. Nothing downstream reads $command, so unlike the OOM gate there
# is no raw/stripped split to maintain here.
#
# Fail-safe on FAILURE: if the stripper is unavailable it returns the ORIGINAL
# string, so the trigger degrades to its previous over-firing behaviour — never to
# under-firing. For a REPORTING hook that is the cheap direction: a spurious CI
# report costs API calls, a missed one costs an unexamined red build (T-169 below).
#
# KNOWN RESIDUAL, stated plainly because the direction here is the expensive one:
# the stripper working AS DESIGNED hides a push whose invocation sits inside quotes
# — `bash -c "git push"`, `ssh host "cd repo && git push"`, or a push inside an
# executed heredoc body. Those are now MISSED. Accepted because this project pushes
# with a bare `git push` (the human authorizes each one, per the ask-before-push
# rule), so the quoted-invocation forms do not occur here; `lib/shell-scan.sh`
# documents the same residual for the safety gates. If they ever do occur, the fix
# is a real shell parser, not a looser regex — a looser regex re-admits the prose.
# ---------------------------------------------------------------------------
scan_command=$(strip_quoted_regions "$command")

# Only act on git push commands. Here-string, not a pipe: under `pipefail` a
# `grep -q` that matches early makes the writer take SIGPIPE, and the resulting
# non-zero pipeline status would send a REAL push down the `exit 0` path.
if ! grep -q 'git.*push' <<< "$scan_command"; then
  exit 0
fi

# Wait for GitHub to register the workflow run
sleep 5

# Try to get the latest CI run
if ! command -v gh &>/dev/null; then
  echo "[post-push hook] gh CLI not found — cannot check CI status"
  exit 0
fi

# Get the most recent workflow run. (NOT necessarily the one this push created —
# there is no branch, ref or head-SHA filter here. BACKLOG #239 tracks that.)
#
# `databaseId` is consumed by the classifier below. It was absent from this list for
# the classifier's entire life, so `run_id` was always empty and the branch never
# executed (BACKLOG #234). `gh` returns ONLY the fields named here.
#
# WHAT DOES AND DOES NOT CATCH A REPEAT. The test stub projects its fixture down to
# this list, so it no longer certifies fields nobody requested — that closes the
# fake. It does NOT make a missing field loud: every read below has a `//` default,
# so a dropped field silently becomes "unknown"/""/empty, which is precisely how
# #234 hid in plain sight. The only thing that reddens is an assertion on the VALUE,
# so every field here is pinned by `test_every_requested_field_reaches_the_report`.
# Add a field here and to that test in the same change, or the next one dies quietly.
#
# `createdAt` was requested and never read; removed rather than left as cargo.
run_info=$(gh run list --limit 1 --json databaseId,status,conclusion,name,headBranch,url 2>/dev/null) || {
  echo "[post-push hook] Could not fetch CI status"
  exit 0
}

# SHAPE, then emptiness. Every read below is `.[0].field`, which requires an ARRAY
# of run objects — and `jq length` does not establish that: it counts an object's
# KEYS just as happily. So `{"status":"completed"}` passed a length check, reached
# `.[0]`, and died with `Cannot index object with number` — exit 5 under `set -e`,
# from a `gh` call that SUCCEEDED. Measured; found by an independent verifier
# probing the boundary this hook's own UNVERIFIED list had named.
#
# ELEMENT shape too, not just array-ness. `type == "array"` alone still admits
# `[1]` and `["x"]`, whose `.[0].status` errors exactly as the object case did —
# same mechanism, same exit 5, narrower payload family. Checking `.[0]` is an
# object closes the family rather than one member of it. Found by code review
# after the first fix stopped one predicate short of the property its own comment
# named.
#
# `jq -e` sets the exit status from the result, so one call answers every question
# at once, and a jq FAILURE (unparseable output, empty stdin) lands in the same
# branch. Those are different states — no CI information versus no run yet — and
# the message says "empty or unrecognized" rather than pretending to distinguish
# them. Splitting them is BACKLOG #242.
if ! echo "$run_info" | jq -e 'type == "array" and length > 0 and (.[0] | type) == "object"' >/dev/null 2>&1; then
  echo "[post-push hook] No workflow run to report (empty or unrecognized gh output)."
  exit 0
fi

status=$(echo "$run_info" | jq -r '.[0].status // "unknown"')
conclusion=$(echo "$run_info" | jq -r '.[0].conclusion // "pending"')
name=$(echo "$run_info" | jq -r '.[0].name // "unknown"')
branch=$(echo "$run_info" | jq -r '.[0].headBranch // "unknown"')
url=$(echo "$run_info" | jq -r '.[0].url // ""')
# Parsed here, with the other fields, and used by BOTH the lookback and the
# classifier. Empty if gh did not supply it — every consumer degrades on that.
run_id=$(echo "$run_info" | jq -r '.[0].databaseId // empty')

echo "[post-push hook] CI run detected: ${name} on ${branch}"
echo "  Status: ${status} | Conclusion: ${conclusion}"
echo "  URL: ${url}"

if [ "$status" = "in_progress" ] || [ "$status" = "queued" ]; then
  echo "  CI is still running. Use 'gh run watch' to monitor, or check back shortly."
fi

# ---------------------------------------------------------------------------
# LOOKBACK — the discriminator below is correct and was one run deep.
#
# Checking only the LATEST run means a genuinely-failed run is surfaced exactly
# once, on the push that produced it. If that moment is missed and the next push
# hits the billing block, this hook truthfully reports "billing, no action" and
# the real failure is never mentioned again.
#
# That is not hypothetical. Run 30121645663 on main (2026-07-24) had two jobs
# that ran 3m37s and 3m52s and genuinely failed (test_no_unregistered_skills).
# Every later push was a billing block. The failure was fixed days later as
# incidental housekeeping — by luck, not because this hook reported it.
#
# So: scan back over recent runs for ANY that failed with a job that actually
# STARTED, not just the newest. Bounded at 15 to stay cheap. Fails quiet — a
# lookback that errors must never block the report on the current push.
#
# The 15 newest runs normally include the one reported above, so the current run is
# skipped here — it is classified on its own terms below. Without the skip a
# current-push failure is announced twice: once correctly, and once as an "EARLIER"
# run that "MAY BE UNEXAMINED", which is the run being examined. That collision was
# unobservable until #234 made the classifier reachable.
#
# "Normally", not "necessarily": these are two separate API calls, so a run landing
# between them can shift the window. The skip is then a no-op, which is the harmless
# direction. Skipping by ID and not by position is what keeps it harmless.
# ---------------------------------------------------------------------------
if command -v jq &>/dev/null; then
  recent=$(gh run list --limit 15 --json databaseId,conclusion,headSha,displayTitle 2>/dev/null || echo "")
  if [ -n "$recent" ]; then
    for rid in $(echo "$recent" | jq -r '.[] | select(.conclusion=="failure") | .databaseId' 2>/dev/null); do
      # Explicit `if`, not `[ ... ] && continue`: under `set -e` a false test as
      # the last command of the body would exit the hook.
      # A null/empty id would otherwise become a literal `gh run view null`.
      if [ -z "$rid" ] || [ "$rid" = "null" ]; then
        continue
      fi
      if [ -n "$run_id" ] && [ "$rid" = "$run_id" ]; then
        continue
      fi
      longest=$(gh run view "$rid" --json jobs 2>/dev/null | jq -r '
        [ .jobs[] | select(.conclusion=="failure")
          | select(.startedAt != null and .completedAt != null)
          | ((.completedAt|fromdateiso8601) - (.startedAt|fromdateiso8601)) ] | max // 0' 2>/dev/null || echo 0)
      if [ "${longest%.*}" -gt 30 ] 2>/dev/null; then
        title=$(echo "$recent" | jq -r --arg id "$rid" '.[] | select((.databaseId|tostring)==$id) | .displayTitle' 2>/dev/null | cut -c1-60)
        echo ""
        echo "  ############################################################"
        echo "  # AN EARLIER CI RUN FAILED FOR REAL AND MAY BE UNEXAMINED.  #"
        echo "  ############################################################"
        echo "  Run ${rid} — longest failed job ran ${longest%.*}s, so it STARTED and FAILED."
        echo "  Subject: ${title}"
        echo "  Investigate: gh run view ${rid} --log-failed"
        echo "  (Found by lookback, not by the latest-run check — a real red one"
        echo "   push back used to be invisible forever. OPERATIONS T-169.)"
        break
      fi
    done
  fi
fi

# ---------------------------------------------------------------------------
# Billing-vs-real classification (OPERATIONS T-169).
#
# WHY THIS IS IN THE HOOK AND NOT IN A POLICY DOCUMENT: the "GitHub Free billing
# is expected background, don't re-flag it" policy is correct — and it was applied
# as "don't look." The `security` job was GENUINELY red on main 2026-07-08 -> 07-11
# (six runs, bandit B404) and every session, including the ones that wrote the
# policy, dismissed it as billing. The discriminator was already documented in TWO
# places: a billing block kills jobs in 3-8s (they never start); those jobs ran
# 4m47s. Nobody applied it. A real defect sat on main for three days behind a label
# that says "don't look."
#
# A standing instruction not to re-flag something is a standing instruction to miss
# the day it is wrong. So the discriminator is computed here, structurally, instead
# of relying on an AI to remember to run it. Advisory did not hold; this is the
# advisory -> structural conversion.
# ---------------------------------------------------------------------------
#
# THE VERDICT IS TERNARY, NOT BINARY: billing / real / no-opinion. A failed run
# whose jobs carry no usable timings cannot be classified, and staying silent about
# it reproduces the exact failure this block exists to stop — an unexamined red read
# as reassurance. Could-not-run is its own state and is never a pass (the rule
# `scripts/check.sh` encodes as exit 3). This path became reachable only when #234
# made the classifier live, so it had never once been exercised.
# ---------------------------------------------------------------------------
if [ "$conclusion" = "failure" ]; then
  classified=""
  if [ -n "$run_id" ] && jobs_json=$(gh run view "$run_id" --json jobs 2>/dev/null); then
    # Duration in seconds for each FAILED job.
    durations=$(echo "$jobs_json" | jq -r '
      [ .jobs[]
        | select(.conclusion == "failure")
        | select(.startedAt != null and .completedAt != null)
        | ((.completedAt | fromdateiso8601) - (.startedAt | fromdateiso8601))
      ] | .[]' 2>/dev/null || true)

    if [ -n "$durations" ]; then
      classified=1
      longest=$(echo "$durations" | sort -n | tail -1)
      # A job that ran for more than ~30s STARTED and then failed. Billing blocks
      # never start (3-8s). Threshold is deliberately generous: a false "real"
      # costs one look; a false "billing" costs three days.
      if [ "${longest%.*}" -gt 30 ] 2>/dev/null; then
        echo ""
        echo "  ############################################################"
        echo "  # CI FAILURE IS **REAL** — NOT the billing background.      #"
        echo "  ############################################################"
        echo "  Longest failed job ran ${longest%.*}s. A billing block kills jobs in"
        echo "  3-8s because they never start. This one STARTED and FAILED."
        echo ""
        echo "  Do NOT apply the 'expected GitHub-Free billing' label to this run."
        echo "  Investigate it: gh run view ${run_id} --log-failed"
        echo "  (OPERATIONS T-169 — this check exists because a genuinely red"
        echo "   security job hid behind that label for three days.)"
      else
        echo "  Failed job(s) ended in ${longest%.*}s — consistent with the known"
        echo "  GitHub-Free billing block (jobs never started). Self-resets at the"
        echo "  billing cycle; no action needed (OPERATIONS T-169)."
      fi
    fi
  fi
  if [ -z "$classified" ]; then
    echo ""
    echo "  This run FAILED and the billing-vs-real check could NOT classify it:"
    echo "  no failed job carried both a start and a completion time (or the run"
    echo "  details could not be fetched). That is NOT a clean bill of health — it"
    echo "  is no opinion. Do not apply the 'expected billing' label on this basis."
    echo "  Check it: gh run view ${run_id:-<run id unavailable>} --log-failed"
    echo "  (OPERATIONS T-169.)"
  fi
fi

# Explicit, not inherited from whatever the last statement happened to return. This
# hook runs after a user's Bash call and must never disturb it.
exit 0
