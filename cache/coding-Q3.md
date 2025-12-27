#### Q3. Testing Integration (The Verification Standards Act)

**Failure Mode(s) Addressed:**
- **B2: Inadequate Testing → Vulnerability Exposure** — Insufficient test coverage leaves vulnerabilities and bugs undetected until production.

**Constitutional Basis:**
- Derives from **Q1 (Verification):** Output must match requirements—tests verify this
- Derives from **Q4 (Testing):** Tests prevent defects from reaching users
- Derives from **Q2 (Evidence Standards):** Tests provide evidence of correctness

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle Q4 states "tests prevent defects" but doesn't specify **when tests must be created** relative to implementation or **what coverage threshold** is acceptable for AI-generated code. Traditional development often allows test-after approaches. AI coding cannot—the volume of generated code makes after-the-fact testing impractical. This domain principle establishes: (1) tests generated WITH implementation, (2) coverage thresholds (≥80%), and (3) what "tested" means beyond just coverage percentage.

**Domain Application:**
Tests must be generated simultaneously with implementation, not as afterthought. Test coverage threshold (default ≥80%) must be met before code is considered complete. Tests must validate actual behavior against specifications, not just exercise code paths. Testing is part of "done," not a separate phase.

**Relationship to P2 (Validation Gates):**
- **P2:** Defines WHEN validation must occur (at phase boundaries)
- **Q3:** Defines WHAT "passing tests" means (coverage, behavior validation, test types)

**Testing Requirements:**
- **Unit Tests:** Individual functions/methods tested in isolation
- **Integration Tests:** Component interactions tested
- **Behavior Tests:** User-facing behavior validated against specifications
- **Error Case Tests:** Error handling paths explicitly tested
- **Edge Case Tests:** Boundary conditions covered

**Truth Sources:**
- Test coverage requirements (default ≥80%, configurable)
- Specification documents (what behavior tests should validate)
- Acceptance criteria (what must be true for feature to be "done")
- Error handling specifications (what error cases must be tested)

**How AI Applies This Principle:**
- **Test WITH Implementation:**
  * Generate test file BEFORE or simultaneously with implementation
  * Do not consider implementation complete until tests written
  * Tests are not optional—every function needs tests
- **Coverage Tracking:**
  * Track coverage as implementation progresses
  * If coverage drops below threshold, add tests before continuing
  * Coverage must meet threshold before moving to next task
- **Behavior Validation:**
  * Tests must validate BEHAVIOR from specifications, not just exercise code
  * Include tests for what should happen AND what shouldn't happen
  * Tests should fail if specification is violated
- **Error and Edge Cases:**
  * Explicitly test error handling paths
  * Test boundary conditions (empty inputs, max values, invalid formats)
  * Test failure scenarios, not just success paths
- **Test Quality:**
  * Tests should be readable (clear intent, meaningful assertions)
  * Tests should be maintainable (not brittle, not over-mocked)
  * Tests should be deterministic (same input = same result)

**Why This Principle Matters:**
Tests are evidence; evidence must be contemporaneous. *This corresponds to "Chain of Custody"—evidence collected after the fact is suspect. Tests written alongside implementation capture the specification while it's fresh; tests retrofit after implementation often test what was built rather than what was intended. Testing-with prevents the gap between intent and implementation from going undetected.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Coverage threshold cannot be met (structural issue or specification gap)
- ⚠️ Test requirements unclear (what scenarios to test)
- ⚠️ Specification ambiguity preventing behavior test definition
- ⚠️ Coverage vs. timeline tradeoff decision

**Common Pitfalls or Failure Modes:**
- **The "Coverage Gaming" Trap:** Writing tests that exercise code but don't validate behavior. High coverage, low value. *Prevention: Tests must assert against specifications, not just call functions.*
- **The "Test Later" Trap:** Writing implementation first, planning to "add tests after." Tests never achieve meaningful coverage. *Prevention: Tests WITH implementation, not after.*
- **The "Happy Path Only" Trap:** Testing only success scenarios, leaving errors untested. *Prevention: Error case tests required for every error handling path.*
- **The "Brittle Tests" Trap:** Tests so tightly coupled to implementation that any change breaks them. *Prevention: Test behavior, not implementation details.*

**Success Criteria:**
- ✅ Test coverage ≥80% (configurable threshold)
- ✅ Tests generated WITH implementation, not after
- ✅ All acceptance criteria have corresponding tests
- ✅ Error handling paths explicitly tested
- ✅ Edge cases and boundary conditions covered
- ✅ Tests validate behavior against specifications

---
