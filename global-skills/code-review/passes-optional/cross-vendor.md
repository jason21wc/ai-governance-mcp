# Cross-Vendor Second Opinion Pass (Opt-In, orchestrator-run)

An INDEPENDENT review of the same diff by a *different model lineage* (OpenAI Codex / gpt),
so a blind spot the whole Claude lineage shares does not pass unchallenged. The Claude
passes already run in fresh context (they clear the self-review ceiling); a different vendor
adds escape from same-lineage correlated blind spots.

This is **NOT a Claude subagent** — unlike the other passes, the orchestrator runs it via
**Bash** and folds its findings into reconciliation. Trigger: the user says "cross-vendor",
"codex review", "second opinion", or "full review".

## When to run

- Preconditions (always): the `codex` CLI is on PATH AND the primary session is not itself
  Codex/gpt (a same-vendor peer adds no diversity). The harness guard enforces both; if it
  skips, so do you.
- **Default where `scripts/codex_review.py` exists (this repo): run the `security` role on
  every review**, in parallel with the subagent dispatch. Measured session-240 (13 runs over
  10 shipped commits, blind-re-audited): median 24s/run, ≤1 non-genuine surviving finding
  per clean commit, and it caught a real scan-bypass Claude review had missed. The
  measurement covered only this harness path, so the default is scoped to it.
- **Everywhere else (the manual `codex exec` path below): opt-in only** — user says
  "cross-vendor", "codex review", "second opinion", or "full review". The manual path and
  non-Python codebases are unmeasured; do not default them on.
- `correctness` / `architecture` stay opt-in everywhere: correctness is usually empty on
  solid code (normal, not a miss) and duplicative when it fires (its one measured hit was
  the same issue the security role found); architecture is unmeasured.

## How to run (orchestrator, via Bash — in parallel with the Claude subagent dispatch)

In the ai-governance repo, use the shared harness (it does not block the Claude passes):

    python scripts/codex_review.py --staged --role security --json
    # or --commit <ref> / --range <a>..<b> to match the review scope; repeat --role as needed

Anywhere else (no harness present), run each pass's own instructions through Codex directly —
always close stdin (`< /dev/null`) so `codex exec` does not hang:

    codex exec --sandbox read-only -o /tmp/codex_review.json < /dev/null "$(cat <<'PROMPT'
    <paste the contents of passes/<role>.md>

    Return ONLY a JSON array of findings, each {severity, location (file:line), issue,
    evidence (1-5 lines), fix}. Return [] if none. Do not manufacture findings.

    DIFF:
    <the diff under review>
    PROMPT
    )"

If `codex` is absent or the guard skips, **silently omit this pass** — never block the review.

## How to fold the findings (into Step 5 reconciliation)

Codex returns a JSON array of findings per role. Treat them as **advisory candidate input**,
run through the SAME reconciliation as every other pass:

1. **Deduplicate by file + line window (±2) + same issue class — NOT exact `file:line`.**
   The two vendors anchor the same finding to adjacent lines (one cites the `def` line, the
   other the body — observed live, session-240 fold test), so literal line equality
   double-reports a confirmed finding instead of merging it. A finding BOTH lineages raise
   is higher-confidence — merge and mark it `(claude+codex — confirmed cross-vendor)`.
2. **A Codex-only finding is a candidate, not a verdict.** Apply the same evidence gate (drop
   if it lacks `file:line` + quoted code) and the same severity calibration. Over-flagging
   without audience context is the known cross-vendor failure mode; the evidence gate is the
   filter — do NOT auto-inflate the finding count with unfiltered Codex output.
3. **Attribute the source** on surviving findings (`(codex)` / `(claude+codex)`) so the reader
   can weigh an unconfirmed cross-vendor finding accordingly.

Do NOT let Codex findings gate the review — they are advisory, reconciled like everything else.
