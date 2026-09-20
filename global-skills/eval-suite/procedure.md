# Eval-Suite Procedure — Eval-Driven Development (EDD)

Authority: **CFR §5.2.8 Eval-Driven Development** (title-10-ai-coding-cfr.md). This procedure
operationalizes the EDD loop for a single probabilistic feature. The reference implementation of
the regression discipline is this repo's own `tests/test_retrieval_quality.py`.

## When this applies

The feature's output is **non-deterministic / probabilistic** — generation, extraction,
summarization, classification, or estimation over natural-language input — where no single output
string is "correct." If the output has one correct value computable from the input, stop: use TDD
(CFR §5.2.2), not this.

## Step 1 — Golden cases (anchored to the spec)

Curate a small, representative set (~5+ to start) of inputs with expected **properties**, not exact
strings. Every property must trace to the specification, never to what the model happened to emit
(the Echo Chamber trap — `coding-quality-testing-integration`). Spread cases across three
categories (the taxonomy from `ref-ai-coding-anthropic-prompting-playbook`; BACKLOG #48 applies the
same taxonomy inward to governance instructions):

- **Control** — basic competence. Must always pass. (Clean, in-scope input → expected fields present, value in a plausible band.)
- **Edge** — past or anticipated failure modes the feature exists to prevent. Must not regress. (Missing input, ambiguous unit, conflicting sources → must flag, not silently guess.)
- **Capability-limit** — inputs where the correct output is to *escalate, decline, or flag low-confidence* rather than answer. (Illegible / out-of-scope input → must refuse to fabricate.)

Record each case as `{id, input, expected_properties, category}`.

## Step 2 — Rubric (deterministic graders first)

Define the scored dimensions and weights. For each dimension decide grader type:

- **Deterministic grader** — anything checkable in code: arithmetic sanity (totals = sum of parts),
  schema validity, grounding-by-substring (every figure traces to a supplied source), no
  out-of-vocabulary entities. Prefer these — they are cheap, stable, and don't drift.
- **LLM-as-judge** — reserve for genuinely subjective dimensions (coherence, tone, completeness of
  reasoning) that no deterministic check captures.

## Step 3 — Judge + threshold (record a rate)

Score each output against the rubric. Pass = aggregate score ≥ threshold. Record the result as
**occurrences over opportunities** (cases-passed ÷ cases) — the same rate discipline BACKLOG #48
uses. Hard rule: a **capability-limit case that fabricates a value is an automatic fail**,
regardless of aggregate score.

## Step 4 — CI regression

Store a dated baseline (per-case scores + aggregate rate). Fail CI when the pass-rate drops more
than ~15% below baseline. **Marker-gate judge-based evals out of default CI** (e.g.
`@pytest.mark.llm`, skip without an API key) — they cost tokens and are non-deterministic. Run them
as a separate, scheduled gate. Deterministic graders can stay in default CI.

## Step 5 — Human eval-case approval (the Red/Green checkpoint)

Before the eval is trusted as a gate, present the golden cases + rubric + threshold for human
sign-off. The cases **are the definition of done**; the human is approving that they capture the
requirement (not the current implementation), exactly as a human approves failing tests under TDD.
This is the Layer-B half of the `.claude/plan-template.md` "Test & Eval Definition Approval"
section. Advisory-first per the V-004 arc.

## Pitfall — who evals the evaluator?

The LLM-as-judge is itself a probabilistic, drifting grader; its scores move across model versions
and prompt edits. Mitigations:

1. Prefer deterministic graders for anything checkable in code.
2. Pin and version the judge model **and** its prompt.
3. Keep a small human-scored calibration set; re-confirm the judge against it when the judge model changes.
4. Keep judge evals out of default CI (cost + non-determinism); run as a separate scheduled gate.

## Tooling — capability, not tool

Recommend the **capability**: golden cases + deterministic graders + an LLM-as-judge for subjective
dimensions + threshold-gated CI regression. Current implementations, as starting points and not
endorsements (per CFR §3.3.4 tool-agnosticism — named tools rot):

- **DeepEval** — pytest-native, Python. Fits a Python project's existing test runner.
- **promptfoo** — YAML-declarative, language-agnostic. Fits polyglot projects.

Pick the one whose configuration surface matches the project's stack.

## Worked example

See `examples/hotel-pip-estimator/` in this repo for a runnable EDD harness on a real
no-single-correct-answer feature (estimating hotel renovation/PIP costs from uploaded scope docs).
