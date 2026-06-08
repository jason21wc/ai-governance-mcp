---
description: Assess whether code is ready to be safely refactored. Maps structural contracts (what grep CAN verify must not change), warns about invisible contracts (what grep CANNOT detect — ordering, invariants, state machines), checks blast radius, and gates on test coverage prerequisites. Invoke when the user says "refactor audit", "is this refactoring safe", "refactor safety", "blast radius", "safe to refactor", "refactoring readiness", or "refactoring review". Do NOT use for performing the refactoring itself (normal coding), post-refactor diff review (use /code-review), test generation (use /test-suite, though this skill may recommend it), or security auditing (use /security-scan).
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Branch:** !`git branch --show-current`
**Framework:** !`test -f vitest.config.ts -o -f vitest.config.js -o -f vitest.config.mts && echo "vitest" || (test -f jest.config.ts -o -f jest.config.js -o -f jest.config.mjs && echo "jest" || (test -f conftest.py -o -f pytest.ini && echo "pytest" || (grep -q '"pytest"' pyproject.toml 2>/dev/null && echo "pytest" || (test -f playwright.config.ts && echo "playwright" || (ls *_test.go 2>/dev/null | head -1 | grep -q . && echo "go" || (test -f Cargo.toml && echo "rust" || echo "unknown"))))))`
**Git diff stat:** !`git diff --stat HEAD 2>/dev/null | tail -1`

## Instructions

You are performing a refactoring readiness assessment. This skill answers one question: **"Is this code ready to be safely refactored?"**

Read `procedure.md` in this skill folder for the full 3-phase protocol.

### Quick Start

1. **Determine the target.** If the user specified a file, module, or function, use that. If they said "is this safe to refactor?" after viewing code, assess that code. If ambiguous, ask.

2. **Read `procedure.md`** for the full protocol.

3. **Execute all three phases in order:**
   - **Phase 1: Map** — structural contract mapping (grep-verified), invisible contracts warning (UNVERIFIED), blast radius + dynamic dispatch detection, test coverage prerequisite gate
   - **Phase 2: Assess** — prerequisite gate, risk classification, readiness verdict
   - **Phase 3: Report** — structured output with evidence and recommendations

4. **Deliver the assessment** with structural contracts, invisible contract warnings, and readiness verdict.

### Key Principles

- **Structural contract mapping is the core value.** Identify what grep CAN confirm must not change — exported functions, side effects, error behavior, integration points. Each item gets file:line evidence.
- **Invisible contracts are an honest warning, not a claim.** Grep finds syntax, not semantics. Ordering guarantees, state machine invariants, concurrency contracts — flag as UNVERIFIED. "3 potential invisible contracts identified (UNVERIFIED)" is honest. "All contracts verified" is a confidence trap.
- **Test coverage is a prerequisite, not a post-check.** If no tests exist for the target, the verdict is STOP — not a suggestion to "maybe add tests." Recommend `/test-suite` for baseline generation.
- **Never output bare "SAFE."** Strongest verdict: STRUCTURALLY READY (invisible contracts not verified). The skill is honest about what tool-assisted verification can and cannot establish.

### Skill Composition

This skill creates a clear workflow with other skills:
- `/refactor-audit` → "Is it ready?" (this skill)
- Refactor the code (normal coding)
- `/code-review` → "Did it work?" (post-refactor diff review)
- `/test-suite` → Generate baseline tests if coverage prerequisite fails

### What This Skill Does NOT Do

- **Perform refactoring** — it assesses readiness. The refactoring itself is normal coding.
- **Post-refactor verification** — use `/code-review` for diff-based review after refactoring.
- **Generate tests** — use `/test-suite` for that (though this skill may recommend it as a prerequisite).
- **Security auditing** — use `/security-scan` for that.
- **Formal semantic equivalence proofs** — intractable for LLMs. The skill is honest about this limitation.
