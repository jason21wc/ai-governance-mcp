# DOE Calibration Procedure

Step-by-step protocol for running DOE calibration chunks. The session model
(you) follows these steps to dispatch runs via the Claude Code Agent tool.

## Arguments

Parse from the user's invocation:
- `replicate N` — which replicate to run (1, 2, or 3)
- `tasks M-P` — which task blocks to run (1-indexed, e.g., `1-3`, `5`, `8-11`)
- `progress` — show overall progress instead of running

## Procedure

### Step 1: Get the run list

Run the matrix expansion script to get the pending runs for this chunk:

```bash
python examples/doe-calibration/doe_runner.py --json --replicate {N} --tasks {M-P}
```

Parse the JSON output. Each entry has: `run_id`, `model`, `effort`, `task_id`,
`category`, `replicate`, `prompt`, `expected_properties`.

If the list is empty, report "All runs in this chunk are complete" and stop.

### Step 2: Execute runs sequentially

For each run in the list (already randomized by the script):

#### 2a. Spawn the subject

Dispatch depends on the run's `model` field.

**Claude models (sonnet/opus/fable) — use a Workflow script, NOT the Agent tool.**
The Agent tool has no `effort` parameter (confirmed against the live schema), so
Agent-tool dispatch is structurally unable to vary the factor this experiment
exists to measure. Every effort-bearing cell must go through Workflow:

```javascript
agent(run.prompt, { model: run.model, effort: run.effort })
```

Effort levels under test are `low` / `medium` / `high` / `xhigh`. Haiku is not in
the model set — it exposes no effort parameter, so it could contribute nothing to
the factor being measured.

**Codex — dispatch via `mcp__codex__codex`, not the Agent tool.** Codex is not a
Claude Code model alias. Its runs carry `effort: "none"` (a flat factor, one cell
per task) because the tool exposes `model` but not `effort`.

Run sequentially (`run_in_background: false` / await each `agent()`), and capture
the response text.

#### 2b. Spawn the judge Agent

Use the Agent tool with:
- `model`: "fable" (primary judge) — BUT for the calibration cross-check
  (10% of runs, at least 1 per task type), use "opus" with effort "max"
- `effort`: "medium" (for fable judge) or "max" (for opus cross-check)
- `prompt`: Build using the judge prompt template. Include:
  - The original task prompt
  - The expected properties from the golden case
  - The subject's response
  - The judge system prompt and scoring instructions
- `run_in_background: false`

Parse the judge's JSON response to extract scores.

#### 2c. Record the result

Write one JSON line to `examples/doe-calibration/results.jsonl`:

```json
{
  "run_id": "sonnet-high-T01-code-impl-simple-r1",
  "model": "sonnet",
  "effort": "high",
  "task_id": "T01-code-impl-simple",
  "category": "code-implementation-simple",
  "replicate": 1,
  "scores": {
    "judge_quality": 4,
    "spec_adherence": 4,
    "completed": true,
    "code_correctness": 4,
    "reasoning_depth": 3,
    "conciseness": 4,
    "edge_case_coverage": 3,
    "false_positive_count": 0,
    "false_negative_count": 1,
    "brief_rationale": "..."
  },
  "judge_model": "fable",
  "judge_effort": "medium",
  "response_length": 1234,
  "timestamp": "2026-07-23T12:00:00Z"
}
```

Use the Write tool (append mode not available — read existing file, add the
new line, write back; or use Bash `echo '...' >> results.jsonl`).

### Step 3: Report completion

After all runs in the chunk:
- Report: runs completed, any failures, total progress
- Run: `python examples/doe-calibration/doe_runner.py --progress`

## Calibration cross-check schedule

For judge independence, 10% of runs use Opus at max instead of Fable at medium.
Select runs for cross-check: within each task block, the first run (after
randomization) of each unique task_id gets the Opus cross-check. This ensures
at least 1 per task type per chunk.

Mark cross-check runs with `"judge_model": "opus"` in results.jsonl so the
analysis script can compare Fable vs Opus scoring and flag Fable-judged-Fable
rows.

## Error handling

- If an Agent call fails (returns null or errors), record the run with
  `"completed": false` and `"error": "<description>"` in results.jsonl.
  Continue to the next run.
- If the judge response can't be parsed as JSON, retry once with a reminder
  to respond with only JSON. If still unparseable, record scores as null
  with `"judge_error": "<description>"`.

## Stopping

The user can interrupt at any time. Progress is tracked per-run in
results.jsonl, so the next invocation picks up where this one left off.
