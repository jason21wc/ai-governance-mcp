---
description: Generate comprehensive tests for a target file, function, module, or diff. Works in three phases — generate tests with error-path emphasis, verify against known AI test-generation failure modes (echo-chamber assertions, error-path undercount, weak mutation coverage), and revise any that fail. Auto-detects test framework. Invoke when the user says "write tests", "generate tests", "test this", "add tests for", "test suite for", or "create tests". Do NOT use for general code review (use /code-review), security scanning (use /security-scan), or running existing tests (use the test runner directly).
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep
---

## Runtime Context

After the skill loads, inspect the branch, framework/test manifests, and existing
test files with ordinary read-only calls. Derive the framework from the repository
and treat an empty test corpus as a valid result.

## Instructions

You are generating a test suite. Read `procedure.md` in this skill folder for the full 3-phase protocol.

### Quick Start

1. **Collect the Runtime Context above and determine the target.** If the user specified a file, function, or module, use that. If they said "test this" after editing code, test the most recently modified files. If ambiguous, ask.

2. **Read `procedure.md`** for the full protocol.

3. **Execute all three phases in order:**
   - **Phase 1: Generate** — read target code, detect framework, write test draft with error-path emphasis
   - **Phase 2: Verify** — apply echo-chamber check, error-path balance, mutation mindset (non-skippable)
   - **Phase 3: Revise** — fix any tests that failed verification, re-check until clean

4. **Deliver the test file(s)** with the self-check results summary.

### Key Principles

- **Echo-chamber check is non-negotiable.** The #1 AI test failure mode: restating implementation logic in assertions. Every test must check a specification, not mirror the code.
- **Error-path balance.** AI systematically under-tests failures. For code with external inputs or side effects, error tests should match or exceed happy-path tests.
- **Test behavior, not implementation.** If a wrong implementation would still pass the test, the test is worthless. Rewrite it.
- **Real dependencies by default.** Only introduce test doubles when necessary (paid APIs, slow services, architectural boundaries). Mock smell: setup > 5 lines or > 2 mocked dependencies means the code has a testability problem.

### What This Skill Does NOT Do

- **Run tests** — it generates them. Run them yourself or with your test runner.
- **Review existing code** — use `/code-review` for that.
- **Audit existing test coverage** — planned for v2; for now, specify what to test.
- **Manage CI/CD** — out of scope.
