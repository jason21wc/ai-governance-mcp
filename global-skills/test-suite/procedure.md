# /test-suite Procedure

Three phases: generate tests, verify them against known AI failure modes, revise until clean. Phase 2 is the skill's core value — do not abbreviate or skip it.

---

## Phase 1: Generate Tests

Read the target code and write a test draft. This phase uses your existing test-writing capabilities with specific constraints that correct for known AI biases.

### 1.1 Detect Framework

Use the context snapshot detection result. If "unknown", check for:

| Signal | Framework | Key Idioms |
|--------|-----------|------------|
| `conftest.py`, `pyproject.toml [tool.pytest]`, `pytest.ini` | pytest | fixtures, `conftest.py`, `@pytest.mark.parametrize`, markers |
| `vitest.config.ts/js/mts` or `vite.config.ts` with test block | vitest | `describe`/`it`, `vi.hoisted()` for mock factories, `test.each` |
| `jest.config.ts/js` or `"jest"` in package.json | jest | `describe`/`it`, `jest.mock()`, `jest.fn()` |
| `playwright.config.ts` | playwright | Page Object Model, `test.use()`, `expect(locator)` |
| `*_test.go` files | go testing | table-driven tests, `t.Run()`, `t.Parallel()` |
| `Cargo.toml` with test dependencies | Rust | `#[cfg(test)]`, `#[test]`, `assert_eq!` |

If still unknown, ask the user.

### 1.2 Understand the Target

Read the target code. Identify:
- **Public API** — exported functions, methods, classes, endpoints
- **Inputs and outputs** — parameter types, return types, side effects
- **Error conditions** — what can go wrong? Invalid input, missing dependencies, network failures, edge cases
- **Dependencies** — what external systems or modules does it rely on?

If acceptance criteria exist (doc comments, type signatures, README), use them. If not, derive from observable behavior and note the gap.

### 1.3 Generate Test Draft

Write tests following these constraints:

**Test level selection:**

| Target characteristic | Level | Rationale |
|-----------------------|-------|-----------|
| Pure function, clear inputs/outputs | Unit | Logic is the value |
| Multiple components wired together | Integration | Wiring is the value |
| User-facing workflow or API endpoint | E2E / API | User experience is the value |
| Database or external API interaction | Integration | Boundary behavior is the value |

Default: integration over unit for code with dependencies. Unit for pure logic.

**Test case categories (all required):**

| Category | What to test | Guidance |
|----------|-------------|----------|
| Happy path | Normal successful operation | At least 1 test |
| Error paths | Expected failures handled correctly | For code with external inputs or side effects, aim for at least as many error tests as happy-path tests. For pure transformations with narrow input domains, fewer are acceptable — document why. |
| Edge cases | Boundary conditions: empty, null, zero, max length, single item, duplicates | At least 2 tests |
| Integration points | Component interactions, external services | When applicable |

**Before writing code, output a test case table:**

| # | Category | Test Name | What It Verifies |
|---|----------|-----------|-----------------|
| 1 | Happy | test_parse_valid_input_returns_ast | Correct output for well-formed input |
| 2 | Error | test_parse_malformed_input_raises_syntax_error | SyntaxError on unclosed bracket |
| ... | ... | ... | ... |

**Test writing rules:**
- **AAA pattern** — Arrange, Act, Assert. One clear section each.
- **One reason to fail** per test. If multiple unrelated assertions could fail, split.
- **Naming:** `test_<function>_<scenario>_<expected>` (Python/Go) or `describe > it should <behavior>` (JS/TS)
- **Existing fixtures first** — scan for `conftest.py`, `test/helpers`, or shared setup before creating new fixtures.

**Test doubles — real by default:**

| Approach | When to use | When NOT to use |
|----------|------------|-----------------|
| Real dependencies | Default | Paid APIs, slow external services |
| Fakes | Architectural boundaries (e.g., in-memory DB, msw for HTTP) | When fake diverges from real behavior |
| Stubs | Controlling return values for specific scenarios | When verifying a call was made |
| Mocks | Side effect IS the behavior (email sent, webhook fired) | When testing return values |

**Mock smell:** If mock setup exceeds 5 lines or mocks more than 2 dependencies, the code likely has a testability problem. Flag it for the user rather than papering over it with more mocks.

**Framework-specific idioms:**

**pytest:**
- Check `conftest.py` for existing fixtures before defining new ones
- Use `@pytest.mark.parametrize` for data-driven tests — don't copy-paste similar tests
- Mark slow tests with `@pytest.mark.slow` or `@pytest.mark.integration`
- Use `tmp_path` fixture for filesystem tests, not manual tempdir management

**vitest:**
- `vi.hoisted()` is REQUIRED for mock variables inside `vi.mock()` factories — the factory runs at hoist time, before imports
- `beforeEach(() => { vi.clearAllMocks() })` for cleanup
- `test.each` for parameterized tests
- Use `msw` for HTTP mocking, not manual fetch stubs

**jest:**
- `jest.mock()` at module level for module mocking
- `jest.fn()` for function mocks; prefer `mockReturnValue` over `mockImplementation` for simple cases
- `beforeEach(() => { jest.clearAllMocks() })` for cleanup

**playwright:**
- Page Object Model for multi-page workflows
- `test.use()` for fixture configuration
- `expect(locator)` over `expect(page)` for specific assertions
- Use `test.describe` for logical grouping

**go:**
- Table-driven tests: `[]struct{ name string; input X; want Y }` with `t.Run(tt.name, ...)`
- `t.Parallel()` for concurrent-safe tests
- `t.Helper()` in shared assertion functions
- `testify/assert` or `testify/require` for readable assertions

---

## Phase 2: Verify

**This phase is the skill's core value. Do not abbreviate or skip it.**

Review every test from Phase 1 against three checks. Report results in structured format.

### 2a. Echo-Chamber Check

The #1 AI test generation failure mode. For each assertion, ask:

> "Does this test the **specification** or the **implementation**? Could I write a WRONG implementation that still passes this test?"

**Echo-chamber (BAD):**
```python
def test_calculate_total():
    result = calculate_total(unit_price=10, quantity=3, tax_rate=0.1)
    assert result == 10 * 3 * (1 + 0.1)  # mirrors the implementation formula
```

The assertion recalculates `10 * 3 * 1.1` — the same arithmetic the function uses. A bug in the formula (e.g., adding tax instead of multiplying) would produce the same wrong answer in both the code and the test.

**Specification-based (GOOD):**
```python
def test_calculate_total():
    result = calculate_total(unit_price=10, quantity=3, tax_rate=0.1)
    assert result == 33.0  # known-good expected value from requirements
```

The assertion uses a pre-computed expected value. If the implementation is wrong, the test catches it.

**How to fix echo-chamber tests:**
- Replace calculated assertions with literal expected values
- Derive expected values from requirements, documentation, or manual calculation done BEFORE reading the code
- For complex outputs, use snapshot/golden-file testing rather than recomputing

Mark each test: PASS (specification-based) or FAIL (echo-chamber).

### 2b. Error-Path Balance Check

Count the tests by category:

| Category | Count |
|----------|-------|
| Happy path | ? |
| Error path | ? |
| Edge case | ? |
| Integration | ? |
| **Ratio (happy:error)** | **?:?** |

**Assessment:**
- For code with external inputs, side effects, or multiple failure modes: error tests should be >= happy-path tests. If not, identify the missing error paths.
- For pure transformations with narrow input domains (e.g., a formatter, a simple getter): fewer error tests are acceptable. State why the ratio is appropriate.
- If the ratio exceeds 3:1 (happy:error), something is almost certainly undertested.

### 2c. Mutation Mindset Check

For each key assertion, ask:

> "What single-character change in the source code would break correctness? Does this test catch it?"

Examples:
- Change `>` to `>=` in a boundary check — does a test fail?
- Change `+` to `-` in arithmetic — does a test fail?
- Remove a null check — does a test fail?
- Change an array index — does a test fail?

If a plausible single-character mutation would NOT be caught, the assertion is too weak. Flag it.

### Verification Report

After all three checks, output:

```
### Self-Check Results

- **Echo-chamber:** [PASS — all assertions use specification-based expected values]
  OR [FAIL — tests N, M use implementation-mirroring assertions; revised in Phase 3]
- **Error-path ratio:** [X happy : Y error — PASS (balanced)]
  OR [X happy : Y error — FAIL (undertested); added N error tests in Phase 3]
- **Mutation check:** [PASS — key mutations would be caught]
  OR [FAIL — mutation "<description>" not caught by any test; strengthened in Phase 3]
```

---

## Phase 3: Revise

For each test that failed a Phase 2 check:

1. Rewrite the specific failing test(s)
2. Re-run ONLY the failed check(s) on the rewrite
3. If still failing, iterate once more — if a check is genuinely inapplicable (e.g., a pure mapper has no meaningful error paths), document why and mark as N/A

Do not skip this phase. The value of the skill is that it catches and fixes problems that ad-hoc test generation misses.

---

## Output Format

Deliver the final test suite in this format:

```markdown
## Test Suite: [Component/Feature Name]

**Framework:** [detected] | **Level:** [unit/integration/E2E/mixed] | **Target:** [file or function]

### Test Case Summary

| # | Category | Test Name | What It Verifies |
|---|----------|-----------|-----------------|
| 1 | Happy | ... | ... |
| 2 | Error | ... | ... |
| ... | ... | ... | ... |

### Self-Check Results

- **Echo-chamber:** [result + evidence]
- **Error-path ratio:** [X:Y + assessment]
- **Mutation check:** [result + evidence]

### Test Code

[Complete test file(s)]

### Notes (if applicable)
- [Testability issues found in the target code]
- [Dependencies that were hard to test — suggestions for the user]
- [Tests that were marked N/A on a check, with explanation]
```

---

## Escalation — When to Stop and Ask

- Target code has no clear public API or testable behavior
- Framework cannot be detected and user hasn't specified one
- Target depends on external services with no obvious mock/fake strategy
- Existing tests conflict with new tests (naming collision, fixture conflict)
- Target code appears to have a bug — generating tests for buggy code produces misleading coverage

---

## Optional: Governance Enhancement

If the ai-governance MCP server is available in this session (check if `search_references` tool exists), you can enhance framework detection:

1. Query: `search_references(query="<framework> testing patterns", domain="ai-coding")`
2. Incorporate returned patterns into Phase 1 framework-specific idioms
3. Example: for vitest, this surfaces `ref-ai-coding-vitest-hoisted-mocks` with the `vi.hoisted()` pattern

The skill is fully functional without this. Governance is an enhancement, not a dependency.
