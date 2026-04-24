# Test Authoring Checklist

**Purpose.** Author-time gate that pairs with the `test-generator` agent's protocol + CFR §5.2 testing methods + the failure-mode registry. Walk through this before writing a new test; walk through it again before committing.

**Cross-references.**
- **Canonical method:** `documents/title-10-ai-coding-cfr.md` §5.2 (Testing Integration) + §5.2.8 (Redundancy & Consolidation).
- **Registry:** `documents/failure-mode-registry.md` — source of truth for `FM-*` IDs.
- **Agent protocol:** `.claude/agents/test-generator.md` — 6-step authoring flow that this checklist short-circuits for straight-through cases.
- **Principle:** `coding-quality-testing-integration` (Q3) — echo-chamber avoidance, failure-mode-first, full-validation-chain.

---

## 1. Pre-Write — Name the failure mode

**Before writing `def test_…`:** state in one sentence what failure mode this test catches. If you cannot answer, the test is premature — either the code isn't there yet, or the test is speculative.

Check the registry at `documents/failure-mode-registry.md`:

- **Existing entry?** Note its ID; you'll cite it in the docstring (step 7).
- **No matching entry?** Decide: is this a real failure mode (regression history, security contract, SLA bound) or test-local behavior (fixture shape, model default)? If real, add a registry entry before writing the test; if test-local, skip the `Covers:` annotation.

---

## 2. Fixture check — Is there already a helper for this?

**Before defining new setup code:**

- Scan `tests/conftest.py` for existing fixtures. 36+ fixtures cover principles, methods, domains, index structures, mocked embeddings, paths, server state.
- Scan `tests/hook_fixtures.py` for transcript-building helpers (`create_transcript`, `make_task_entry`, `make_exit_plan_entry`).
- If a near-match exists, use it — do not fork a "slightly different" variant. Either extend the existing fixture or skip to step 3 if the divergence is semantic.

If you find yourself about to define the third copy of a helper across test files, stop and consolidate into conftest or a sibling shared module.

---

## 3. Level check — Where does this test belong?

Per §5.2 progressive testing: test at the lowest layer that catches the failure mode.

- **Unit:** single function / method, mocked deps. Fastest feedback.
- **Integration:** several modules collaborating, real-ish deps (tmp_path-backed storage, mocked embeddings).
- **Behavioral / E2E:** MCP endpoints, subprocess hook invocations, real index (`@pytest.mark.real_index`).

A failure-mode test that lives at e2e level when unit level would catch it is slow and obscures the diagnostic signal.

---

## 4. Echo-chamber self-check

**Ask:** if the production code were wrong (not syntactically broken, just semantically wrong), would this test fail?

A test that passes against both a correct and an incorrect implementation is tautological. Common traps:

- Asserting `len(result) > 0` when the function always returns ≥1 item.
- Asserting `returncode == 0` when the function never sets non-zero.
- Asserting an attribute exists without asserting its value.

If the test would pass against `def f(*args): return expected_return_value`, rewrite.

---

## 5. Side-effect check — Observe, don't just return

Per LEARNING-LOG `FM-TEST-SIDE-EFFECTS`: a function can return success while failing to write its file, emit its event, update its cache.

For observability-critical code (hooks, storage writes, metric emission, log writes):

- Assert the observable state changed (file exists, log line present, counter incremented).
- Do **not** assert only on return value.

---

## 6. Environment & validation-chain checks

- **Environment:** tests that need daemon / network / real ML model must skip (`pytest.skip` with reason) or mock cleanly. Use `@pytest.mark.slow` / `.integration` / `.real_index` markers when appropriate.
- **Validation chain:** inputs should traverse production validation layers. Bypassing validation (e.g., constructing a model via `__init__` to skirt Pydantic) hides bugs in the validation path itself.

---

## 7. Annotation — `Covers:` in docstring

If this test covers a registry entry, include the ID(s) in the docstring:

```python
def test_rejects_path_traversal(self):
    """Project-id validator must reject `../` path-traversal attempts.

    Covers: FM-PROJECT-ID-PATH-TRAVERSAL
    """
    ...
```

Multiple IDs comma-separated:

```python
"""
Covers: FM-HOOK-CONTRARIAN-REQUIRED, FM-HOOK-FAIL-CLOSED-EXIT-2
"""
```

Lint (`tests/test_validator.py::TestFailureModeCoverage`) enforces:

- Every `Covers:` ID resolves to a registry entry (unknown = test failure).
- Every `must_cover: true` registry entry has ≥1 `Covers:` annotation (missing = test failure).

Annotations are **voluntary** for advisory (`must_cover: false`) entries.

---

## 8. Markers — Choose the right pytest marker

- `@pytest.mark.slow` — tests that load real ML models or run >5s. Deselected by default (`-m "not slow"`).
- `@pytest.mark.integration` — collaborating components, real-ish deps.
- `@pytest.mark.real_index` — uses production index (`tests/fixtures/real_index`).
- `@pytest.mark.asyncio` — async test bodies (auto-applied via `asyncio_mode = "auto"` in pyproject.toml).
- `@pytest.mark.model_eval` — model comparison tests; never auto-run in CI.

---

## 9. Before commit

- **Name & ID:** test name describes behavior (`test_rejects_slashes`, not `test_1`). `Covers:` line, if present, is valid.
- **Runs locally:** `pytest path/to/file.py::ClassName::test_name -v` passes.
- **Lint passes:** `pytest tests/test_validator.py::TestFailureModeCoverage -v` green if you added/changed registry entries.
- **No fixture duplication:** you didn't copy-paste a helper from a sibling file.
- **Derived map regenerated** (only if you added/retired a registry entry): `python3 scripts/generate-test-failure-map.py`.
- **CFR §5.2.8** — if you deleted a test, the commit message explains WHY (regression risk / layered-coverage redundant / schema retired).

---

## Checklist summary (for quick recall)

1. **Name** the failure mode.
2. **Fixture** — reuse before creating.
3. **Level** — lowest that catches the failure.
4. **Echo** — would a WRONG implementation pass?
5. **Side effect** — assert observable state, not just returns.
6. **Environment & validation** — mark, skip, or pass through real validation.
7. **Annotate** `Covers: FM-<ID>` when applicable.
8. **Marker** — choose the right pytest mark.
9. **Commit** — name, local run, lint, map if registry changed.
