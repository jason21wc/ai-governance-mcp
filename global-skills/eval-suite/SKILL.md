---
description: Build an eval suite for a probabilistic / LLM-powered feature whose output has no single correct answer (generation, extraction, estimation, summarization, classification over natural-language input). Defines golden cases across three categories (control / edge / capability-limit), a scored rubric with deterministic graders plus an LLM-as-judge for subjective dimensions, a pass threshold recorded as a rate, and threshold-gated CI regression. Implements CFR §5.2.8 Eval-Driven Development (the Layer-B complement to TDD). Invoke when the user says "write evals", "eval this", "eval-driven development", "how do I test this AI feature", "build golden cases", "is this output good", or "score the model output". Do NOT use for deterministic code (use /test-suite or TDD per §5.2.2), general code review (use /code-review), security scanning (use /security-scan), or running existing tests (use the test runner directly).
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep
---

## Runtime Context

After the skill loads, inspect the branch, dependency manifests, and existing eval
files with ordinary read-only calls. Select tooling from the detected stack; an
empty eval corpus is a valid greenfield result.

## Instructions

You are building an eval suite for a **probabilistic** feature — one whose output quality is a matter of degree, not equality. This is Eval-Driven Development (EDD), the Layer-B complement to TDD. Read `procedure.md` in this skill folder for the full protocol; the authority is CFR §5.2.8.

### Quick Start

1. **Collect the Runtime Context above, then confirm it's actually a Layer-B feature.** If the output has one correct value computable from the input, this is the wrong skill — use TDD (`/test-suite`, CFR §5.2.2, assert equality). EDD is for outputs that are one of many acceptable answers (generated text, extracted fields from messy input, estimates, classifications).

2. **Read `procedure.md`** for the full EDD loop.

3. **Execute the loop in order:**
   - **Golden cases** — curate ~5+ representative inputs across the three categories (control / edge / capability-limit), with expected *properties* anchored to the spec, not exact strings.
   - **Rubric** — scored dimensions; prefer **deterministic graders** (arithmetic, schema, grounding-by-substring) and reserve an LLM-as-judge for genuinely subjective dimensions.
   - **Judge + threshold** — score each output, pass = aggregate ≥ threshold, recorded as a *rate* (cases-passed ÷ cases). A capability-limit case that fabricates a value is an automatic fail.
   - **CI regression** — store a dated baseline; fail when the pass-rate drops >~15% below it. Marker-gate judge-based evals out of default CI.

4. **Surface the golden cases + rubric for human approval BEFORE trusting the eval as a gate** (the Red/Green checkpoint — see Key Principles).

### Key Principles

- **Anchor to the spec, not the model's output.** The Echo Chamber trap (`coding-quality-testing-integration`) is worse here than in TDD — there is no compiler to catch a tautological eval. Never derive an expected property from what the model happened to produce.
- **Deterministic graders first.** Anything checkable in code (totals add up, every figure traces to a source, schema valid) is a deterministic grader. The LLM-as-judge is the expensive, drifting fallback for subjective quality only.
- **Who evals the evaluator?** The judge is itself probabilistic. Pin and version the judge model + prompt, keep a small human-scored calibration set, and re-confirm the judge when its model changes.
- **The cases are the definition of done.** Golden cases + rubric must be human-approved before the eval gates anything — exactly as failing tests are approved under TDD.
- **Tool-agnostic.** Recommend the capability, not a tool. DeepEval (pytest-native, Python) and promptfoo (YAML, polyglot) are current starting points, not endorsements — pick what matches the stack.

### What This Skill Does NOT Do

- **Test deterministic code** — use `/test-suite` or TDD per CFR §5.2.2.
- **Measure the governance framework's own behavior** — that is the *inward* application of the same machinery, tracked in BACKLOG #48. This skill is the *outward* application (an adopter's product output).
- **Pick or install your eval tool for you** — it recommends the capability; you choose DeepEval / promptfoo / other per stack.
- **Run a model in production** — it builds the harness around model calls, not the feature itself.
