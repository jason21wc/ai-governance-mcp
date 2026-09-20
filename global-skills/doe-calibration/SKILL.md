---
name: doe-calibration
description: Run DOE calibration chunks for model/effort routing (BACKLOG #209)
disable-model-invocation: true
---

# DOE Calibration Skill

Run bite-sized chunks of the DOE model/effort routing experiment. Each invocation
dispatches Agent subagents for a specified task block within a replicate, judges the
results, and appends to results.jsonl.

## Usage

```
/doe-calibration replicate 1 tasks 1-3
/doe-calibration replicate 2 tasks 4-7
/doe-calibration progress
```

See `global-skills/doe-calibration/procedure.md` for the step-by-step protocol.
