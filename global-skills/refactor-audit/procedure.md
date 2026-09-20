# /refactor-audit Procedure

Three phases: map the structural contract and blast radius, assess readiness against prerequisites, report with a verdict. Phase 1 is the skill's core value — do not abbreviate or skip it.

---

## Phase 1: Map

This phase identifies what must be preserved and maps the blast radius. The skill answers one question: "Is this code ready to be safely refactored?"

### 1a. Structural Contract Mapping (tool-assisted)

For the target code, identify what grep CAN confirm must not change. Each item must have file:line evidence from a grep or read command.

**Public API surface:**
```bash
grep -rn "export\|^def \|^class \|^func \|public " <target>
```
Identify exported functions, their signatures, return types. These are structural commitments to callers.

**Observable side effects:**
```bash
grep -rn "write\|insert\|update\|delete\|send\|emit\|log\|fetch\|request" <target>
```
Database writes, network calls, file I/O, events emitted, logging, metrics. Side effects are the most dangerous things to silently remove during refactoring.

**Error behavior:**
```bash
grep -rn "throw\|raise\|reject\|Error\|Exception\|panic" <target>
```
What errors are thrown/returned, under what conditions. Callers may depend on specific error types or messages.

**Integration points:**
```bash
grep -rn "import.*<target>\|require.*<target>\|from.*<target>" .
```
Who calls this code? What do they depend on? This feeds directly into blast radius.

**Output:** A structural contract table — each row is a grep-confirmed obligation with file:line evidence.

### 1b. Invisible Contracts Warning

Grep finds syntax, not semantics. This section flags potential contracts that grep CANNOT verify. **Label each as UNVERIFIED.**

| Category | What to look for | Why grep misses it |
|----------|-----------------|-------------------|
| **Ordering guarantees** | Must-call-before relationships, initialization sequences | Order is implicit in control flow, not declared |
| **State machine invariants** | Valid state transitions, preconditions for method calls | State machines are emergent from branching logic |
| **Concurrency contracts** | Thread safety, mutex protocols, atomic operation ordering | Concurrency semantics aren't syntactically visible |
| **Protocol compliance** | Handshake sequences, retry-then-fallback patterns | Protocols span multiple functions/files |
| **Implicit coupling** | Shared mutable state, global configuration dependencies | Coupling through globals has no import trace |

Use Claude's code comprehension to identify POTENTIAL invisible contracts from code patterns (e.g., a function that always calls `init()` before `process()` — ordering guarantee). But never claim verification.

**Honest reporting:**
- "3 potential invisible contracts identified (UNVERIFIED)" — good
- "All contracts verified" — confidence trap, never output this
- "No invisible contracts detected" — acceptable only for trivially simple code (pure functions, no state)

### 1c. Map Blast Radius (tool-assisted)

**Direct dependents:**
```bash
grep -rn "import.*<target>\|require.*<target>\|from.*<target>" .
```
Count files that directly import the target.

**Transitive dependents (one level deep):**
For each direct dependent, who imports THEM?
```bash
grep -rn "import.*<dependent>\|require.*<dependent>" .
```

**Test coverage:**
```bash
grep -rn "<target_name>" tests/ test/ __tests__/ spec/
```
What tests exercise this code? Count and list them.

**Dynamic dispatch detector:**
```bash
grep -rn "@Injectable\|container\.resolve\|container\.get\|reflect\|Reflect\.\|eval(\|\.on(\|\.emit(\|addEventListener\|removeEventListener\|subscribe(\|publish(" <target_dir>
```
If any match: mark blast radius as **"INCOMPLETE — dynamic dispatch detected"** with specifics. DI containers, reflection, event emitters, and string-based routing create calling relationships invisible to import-based grep.

**Risk classification:**

| Blast Radius | Criteria | Review Depth |
|--------------|----------|--------------|
| **L0 (Local)** | No external callers, internal to one file | Light — structural contract only |
| **L1 (Module)** | Called within same module/package | Standard — contract + test coverage |
| **L2 (Cross-module)** | Called from other modules | Deep — contract + coverage + caller analysis |
| **L3 (Public API)** | Part of public API, external consumers | Full — contract + coverage + callers + breaking change analysis |

### 1d. Test Coverage Prerequisite Check

This is a structural gate, not advice.

- **STOP** — No tests exist for the target code. Refactoring without tests is unsafe (industry data: 37% AI refactoring correctness rate without test verification). Recommend running `/test-suite` first to generate baseline tests.
- **WARN** — Tests exist but are thin (< 3 test cases for the target). Partial coverage means some behavioral drift will be undetected.
- **PASS** — Good test coverage exists. Proceed to Phase 2 with confidence.

To check:
```bash
grep -rn "<target_function_or_class>" tests/ test/ __tests__/ spec/ *_test.go
```

If STOP: the audit can still continue (to show the developer what's at stake), but the verdict in Phase 2 must be NOT READY.

---

## Phase 2: Assess

Synthesize Phase 1 findings into a readiness verdict.

### 2a. Prerequisite Gate

Report whether ALL prerequisites are met:
- [ ] Test coverage: PASS or WARN (not STOP)
- [ ] Structural contract: at least 1 grep-confirmed item (code has identifiable obligations)
- [ ] Blast radius: classified (L0–L3)
- [ ] Dynamic dispatch: either "none detected" or explicitly marked INCOMPLETE

If test coverage is STOP, the verdict is NOT READY regardless of other factors.

### 2b. Risk Classification

Classify the proposed refactoring by safety level:

| Refactoring Type | Risk Level | Rationale |
|-----------------|------------|-----------|
| Rename (identifier) | Low | Mechanical, IDE-verifiable |
| Extract function/method | Low | Creates new abstraction, preserves callers |
| Inline function | Medium | Removes abstraction, may affect callers |
| Move to different module | Medium | Changes import paths, affects dependents |
| Change function signature | High | Breaks all callers |
| Restructure control flow | High | May alter timing, ordering, error paths |
| Merge/split classes | High | Changes inheritance, composition contracts |

If the user described their intended refactoring, classify it. If not, report what classification WOULD apply to common refactorings of this code.

### 2c. Readiness Verdict

Based on structural contract + blast radius + test coverage + risk level + invisible contracts. **Never output bare "SAFE."**

Three verdicts:

**STRUCTURALLY READY** (invisible contracts not verified)
- Prerequisites met (tests exist, contract mapped, blast radius classified)
- Structural contract items are all preservable with the proposed change
- Proceed with awareness of unverified invisible contracts
- Strongest possible verdict — explicitly acknowledges the limits of tool-assisted verification

**CONDITIONALLY READY**
- Prerequisites partially met
- Specific conditions must be fulfilled before proceeding
- Examples: "Generate baseline tests for untested error paths," "Resolve ambiguous ordering contract in init sequence," "Verify thread-safety assumption manually"

**NOT READY**
- Prerequisites not met (usually: no test coverage)
- Specific blockers identified
- Clear next steps to reach readiness

**The value this provides that developers cannot easily do themselves:**
- Exhaustive transitive caller enumeration (tedious manual work)
- Invisible contract identification (requires reading with suspicion, not just reading)
- The structural STOP signal when prerequisites aren't met (prevents "just refactor it" impulse)
- Risk classification with reasoning specific to the proposed refactoring

---

## Phase 3: Report

Output in this format:

```markdown
## Refactor Audit: [Target]

**Blast Radius:** [L0/L1/L2/L3] — [N direct dependents, M transitive, T tests]
**Dynamic Dispatch:** [None detected / INCOMPLETE — details]
**Test Coverage:** [PASS / WARN — details / STOP — no tests found]

### Structural Contract (grep-verified)

| # | Must Preserve | Evidence | Confidence |
|---|--------------|----------|------------|
| 1 | [exported function X with signature Y] | [file:line — grep output] | Verified |
| 2 | [side effect: writes to table Z] | [file:line — grep output] | Verified |
| 3 | [throws ValueError on negative input] | [file:line — grep output] | Verified |

### Invisible Contracts (UNVERIFIED)

| # | Potential Contract | Evidence Pattern | Risk if Broken |
|---|-------------------|-----------------|----------------|
| 1 | [ordering: init() before process()] | [init called on line N, process on line M] | [process fails silently without init state] |
| 2 | [state: connection must be open] | [no explicit check, assumed by caller] | [runtime error in production] |

### Risk Assessment

- **Proposed refactoring:** [what the user intends to do, or "not specified"]
- **Refactoring type:** [classification from table]
- **Risk level:** [Low / Medium / High]
- **Verdict:** [STRUCTURALLY READY / CONDITIONALLY READY / NOT READY]
- **Conditions (if applicable):** [specific blockers or prerequisites]

### Recommendations

- [Actionable next steps]
- [Which invisible contracts to manually verify before proceeding]
- [Skill composition: run /test-suite if coverage is thin, /code-review after refactoring]
```

---

## Escalation — When to Stop and Ask

- Target code has no tests AND no clear structural contract (can't assess safety at all)
- Refactoring crosses module boundaries in a codebase with no integration tests
- Public API change with unknown external consumers
- Refactoring appears to intentionally change behavior (not a pure refactoring — needs different review)
- Dynamic dispatch detected and blast radius fundamentally cannot be determined
- Code and its tests contradict each other — which represents intended behavior?

---

## Optional: Governance Enhancement

If the ai-governance MCP server is available in this session (check if `search_references` tool exists), you can enhance the assessment:

1. Query: `search_references(query="refactoring safety patterns", domain="ai-coding")`
2. Incorporate returned patterns into risk classification and invisible contract detection
3. Example: surfaces blast radius classification (AO-1), deployment governance approval patterns

The skill is fully functional without this. Governance is an enhancement, not a dependency.
