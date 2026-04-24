# Test Authoring Checklist — Extensions to Test-Generator Agent Protocol

**Purpose.** This checklist extends `.claude/agents/test-generator.md` (6-step Test Creation Protocol) with author-time gates unique to this project — failure-mode registry integration, observability asserts, validation-chain preservation, and the before-commit lint/map sequence. Use both together: the agent's protocol for general test design (framework detection, level selection, echo-chamber self-check, test doubles); this checklist for project-specific gates below.

**Scope discipline.** Steps marked **[NOVEL]** are this checklist's unique contribution; steps marked **[→ SEE]** delegate to their canonical home to prevent drift. Consolidated session-123 Commit I after Phase 1 overlap analysis showed ~50% duplication across CFR §5.2, the agent prompt, and the previous 9-step checklist.

**Canonical sources.**
- **Agent protocol:** `documents/agents/test-generator.md` + `.claude/agents/test-generator.md` — 6-step Test Creation Protocol (framework, level, design, doubles, write, self-check).
- **CFR testing methods:** `documents/title-10-ai-coding-cfr.md` §5.2 (Testing Integration), §5.2.5 (Organization Patterns, fixtures, markers), §5.2.8 (Redundancy & Consolidation).
- **Failure-mode registry:** `documents/failure-mode-registry.md` — SSOT for `FM-*` IDs.
- **Lint:** `tests/test_validator.py::TestFailureModeCoverage` — enforces annotations.
- **Principle:** `coding-quality-testing-integration` (Q3) — echo-chamber avoidance, failure-mode-first, full-validation-chain.

---

## 1. Pre-Write — Name the failure mode [NOVEL]

**Before writing `def test_…`:** state in one sentence what failure mode this test catches. If you cannot answer, the test is premature — either the code isn't there yet, or the test is speculative.

Check `documents/failure-mode-registry.md`:

- **Existing entry?** Note its ID; you'll cite it in the docstring (step 4 below).
- **No matching entry?** Decide: is this a real failure mode (regression history, security contract, SLA bound, LEARNING-LOG anti-pattern) or test-local behavior (fixture shape, model default)? If real, add a registry entry before writing the test; if test-local, skip the `Covers:` annotation.

---

## 2. Fixture reuse [→ SEE CFR §5.2.5]

Scan `tests/conftest.py` (36+ shared fixtures) and `tests/hook_fixtures.py` (hook transcript helpers) before defining new setup code. If you're about to define the third copy of a helper across files, stop and consolidate. **Full fixture taxonomy + migration guidance:** CFR §5.2.5.

---

## 3. Level check [→ SEE test-generator agent §2]

Choose unit / integration / e2e per the decision table in `documents/agents/test-generator.md` Step 2 (Choose Test Level). Rule of thumb: test at the lowest layer that catches the failure mode.

---

## 4. Echo-chamber self-check [→ SEE test-generator agent §6]

"Would a WRONG implementation still pass this test?" — if yes, rewrite. Full procedure + common traps in `documents/agents/test-generator.md` Step 6 (Self-Check — Echo Chamber and Mutation). Principle: `coding-quality-testing-integration` Q3.

---

## 5. Side-effect check — Observe, don't just return [NOVEL]

Per LEARNING-LOG `FM-TEST-SIDE-EFFECTS`: a function can return success while failing to write its file, emit its event, update its cache.

For observability-critical code (hooks, storage writes, metric emission, log writes):

- Assert the observable state changed (file exists, log line present, counter incremented).
- Do **not** assert only on return value.

---

## 6. Environment & validation-chain check [NOVEL]

- **Environment:** tests that need daemon / network / real ML model must skip cleanly (`pytest.skip` with reason) or mock. Use project markers (see step 7).
- **Validation chain:** inputs should traverse production validation layers. Bypassing validation (e.g., constructing a Pydantic model via `__init__` to skirt field validators) hides bugs in the validation path itself.

---

## 7. Markers [→ SEE CFR §5.2.5]

Full marker table (`slow`, `integration`, `real_index`, `asyncio`, `model_eval`): CFR §5.2.5. Reminder: `asyncio` is auto-applied via `asyncio_mode = "auto"` in `pyproject.toml`.

---

## 8. `Covers:` annotation [→ SEE CFR §5.2.8 + registry]

If this test covers a registry entry, add `Covers: FM-<id>` to the docstring (single line; multiple IDs comma-separated; multiple `Covers:` lines are additive). Full annotation syntax + deletion protocol + `TestFailureModeCoverage` lint contract in `documents/failure-mode-registry.md` ("Annotation format" section) and CFR §5.2.8.

Shortcut: if `must_cover: true` entries lack annotations, the lint fails — and the registry's demotion-discipline rule means you can't dodge it by flipping the flag.

**When adding a new registry entry** (whether `must_cover: true` or `false`): include ≥1 seeded `Covers:` annotation in the same commit. Advisory entries introduced ≥ 2026-04-24 are structurally enforced by `TestFailureModeCoverage::test_new_advisory_entries_have_annotation` — prose-only rules failed for 4 months before this gate shipped. Exception: mark the entry `placeholder: true` if it's dormant-until-triggered (rare; currently only FM-REGISTRY-RETIRED-ID-DEPRECATION).

---

## 9. Before commit [NOVEL]

- **Name & ID valid:** test name describes behavior (`test_rejects_slashes`, not `test_1`). Any `Covers:` annotation resolves to a registry entry.
- **Runs locally:** `pytest path/to/file.py::ClassName::test_name -v` passes.
- **Lint green:** `pytest tests/test_validator.py::TestFailureModeCoverage -v` if you touched the registry or added annotations.
- **Map regeneration:** pre-commit hook (`regen-test-failure-mode-map`) runs automatically when the registry, any test file, or the generator changes. If you're working outside the pre-commit flow, run `python3 scripts/generate-test-failure-map.py` manually.
- **Test deletion rationale:** if you deleted a test, the commit message explains WHY (per CFR §5.2.8 deletion protocol) — regression risk / layered-coverage redundant / schema retired.

---

## Quick recall

**Novel to this checklist** (steps 1, 5, 6, 9): failure-mode naming + registry check; observability side-effect asserts; validation-chain preservation; before-commit lint/map regen.

**Delegated to canonical source** (steps 2, 3, 4, 7, 8): fixture reuse (CFR §5.2.5), level choice (agent §2), echo-chamber (agent §6), markers (CFR §5.2.5), `Covers:` annotation (CFR §5.2.8 + registry).

The canonical sources are the authoritative homes; this checklist ensures the project-specific gates don't get lost in the general agent protocol.
