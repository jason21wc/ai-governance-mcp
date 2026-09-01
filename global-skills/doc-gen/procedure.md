# /doc-gen Procedure

Three phases: classify and generate a draft, verify every claim against actual code, revise until clean. Phase 2 is the skill's core value — do not abbreviate or skip it.

---

## Phase 1: Classify & Generate

### 1.1 Classify Documentation Type

Before writing a single word, classify using the Divio quadrant:

| Type | Purpose | Key Rule |
|------|---------|----------|
| **Tutorial** | Learning-oriented, guided experience | Never explain "why." Lead through concrete steps that produce a working result. |
| **How-to guide** | Task-oriented, solve a specific problem | Assume competence. Start with the goal, give numbered steps, skip backstory. |
| **Reference** | Information-oriented, dry facts | Complete, accurate, austere. Structure mirrors code structure. No narrative. |
| **Explanation** | Understanding-oriented, background | The ONLY place for "why." Design decisions, trade-offs, alternatives not chosen. |

**Never blend quadrants in a single section.** A README Quick Start is a tutorial. An API section is reference. A "Why we chose X" section is explanation. Keep them separate.

If the user specified a doc type, use it. If not, infer from context:
- "README for" → mixed-file (tutorial Quick Start + reference API + explanation Architecture)
- "docstrings for" → reference
- "guide for" → how-to or tutorial (ask if ambiguous)
- "API docs for" → reference

### 1.2 Identify Audience

| Audience | Calibration |
|----------|-------------|
| **Developer** | Peer-to-peer tone. Assume competence. Skip "what is an API." Working examples, parameter semantics, error codes, edge cases. |
| **Operator** | Procedural. Numbered steps. Config reference, env vars, health checks, expected outcomes. |
| **End user** | Supportive. No jargon without explanation. Task-based ("How do I export my data?"). |

Default: developer, unless context indicates otherwise.

### 1.3 Understand the Target

Read the target code. Identify:
- **Public API** — exported functions, classes, methods, endpoints
- **Types and signatures** — parameter types, return types, generics
- **Behavior beyond signatures** — side effects, caching, retry logic, auth requirements, rate limits, error recovery
- **Dependencies** — what external systems or modules does it rely on?
- **Configuration** — env vars, config files, feature flags

### 1.4 Generate Documentation Draft

Write the draft applying these corrective constraints — the things that structurally fix known AI documentation failure modes:

**Value test (applied per-sentence):**
> "What does this tell the reader that they can't learn faster by reading the code?"

If the answer is "nothing," delete the sentence. This is the single most important quality gate.

**Anti-padding discipline:**
Never use: "simply," "just," "easily," "comprehensive," "robust," "powerful," "straightforward," "of course," "seamless," "leverage." These words add no information. Every sentence must survive the value test.

**Signature enrichment (not parroting):**
- BAD: `user_id (str): The user ID.` — restates the name and type
- GOOD: `user_id (str): Supabase auth UID, not the database row ID. Must be non-empty.` — adds semantic meaning

**Non-obvious behavior priority:**
Document what's surprising BEFORE what's obvious. The reader can see parameter types in the signature — they cannot see:
- Cache-first-then-DB behavior
- Exponential backoff on retry
- Silent error swallowing
- Implicit ordering constraints
- Thread safety limitations
- Environment variable dependencies

**Writing rules:**
- Second person, active voice, present tense ("You configure..." not "The configuration can be...")
- One idea per sentence (target 26 words max)
- Task-based headings ("Create a cluster" not "Cluster creation" or "About clusters")
- Link, don't repeat — if documented elsewhere, link to it

Output: documentation draft + a list of factual claims made (defaults, return types, error conditions, parameter constraints, supported formats, etc.) for Phase 2 verification.

---

## Phase 2: Verify

**This phase is the skill's core value. Do not abbreviate or skip it.**

**Key insight:** Documentation validation is a specification-matching problem. Use Bash/Grep/Read to mechanically confirm claims against the actual code. Self-attestation ("yes I checked") is not verification — it is the same model that generated the claim re-reading its own output.

### 2a. Claim Verification Check (tool-assisted)

For each factual claim in the draft — every default value, return type, error condition, parameter constraint, header name, status code, or supported format:

> "Can I confirm this claim with a grep or file read? Execute the command and cite the output."

**Execute grep/read commands** for each claim. Cite file:line and the relevant code snippet.

**Examples:**

| Documented Claim | Verification Command | What to Check |
|-----------------|---------------------|---------------|
| "default timeout is 30s" | `grep -n "timeout" src/config.py` | Find the actual default assignment |
| "returns 201 on success" | `grep -n "201\|status" src/routes/users.py` | Find the actual status code |
| "accepts JSON and XML" | `grep -rn "xml\|XML" src/` | Find actual format handling |
| "throws ValueError on negative" | `grep -n "ValueError\|raise" src/calc.py` | Find the actual raise statement |
| "requires AUTH_TOKEN env var" | `grep -rn "AUTH_TOKEN" src/` | Confirm it's actually read |

If the grep output **contradicts** the documented claim, mark FAIL with the evidence showing what the code actually does.

If a claim **cannot be mechanically verified** (e.g., "this module handles user authentication" — a semantic summary), categorize it as self-reviewed.

**Output two categories:**
1. **Mechanically verified** — grep-confirmed with command + output cited
2. **Self-reviewed** — semantic descriptions, architectural summaries, not mechanically verifiable

Be transparent about which is which. "5 claims mechanically verified, 3 self-reviewed" is honest. "8/8 PASS" is a confidence trap.

### 2b. Example Validation Check (tool-assisted)

For each code example in the draft:

> "Do the function names, parameter names, import paths, and types in this example actually exist in the codebase?"

**Mechanically verify** by grepping for each function/class name used in examples:
- Confirm the function exists: `grep -rn "def function_name\|function function_name\|export.*function_name" src/`
- Confirm parameter names match: read the actual function signature
- Confirm import paths are valid: `ls src/module/path.py` or equivalent
- For doctest-style examples, run them if feasible

Mark FAIL if any example uses:
- Invented function or class names
- Wrong parameter names or types
- Non-existent import paths
- Fabricated output that doesn't match actual behavior

### 2c. Padding & Value Check

For each section of the draft:

> "Does every sentence add value beyond what the code shows? Are there banned words?"

Scan for:
- **Banned words:** simply, just, easily, comprehensive, robust, powerful, straightforward, of course, seamless, leverage
- **Signature parroting:** docstring descriptions that restate parameter names and types without adding semantic meaning
- **Obvious over surprising:** documenting what `get_user()` returns (obvious) while ignoring cache behavior (surprising)
- **Marketing language:** any sentence that sells rather than informs

This check is self-review (not mechanically verifiable) — label it as such in the report.

### 2d. Completeness Check

For the target code:

> "What non-obvious behavior exists in this code that is NOT documented?"

Scan the code for these categories of behavior that are commonly omitted:

| Category | What to look for |
|----------|-----------------|
| Side effects | Database writes, file I/O, network calls, logging, metrics emission |
| Caching | Memoization, cache keys, TTL, invalidation triggers |
| Retry/backoff | Retry counts, delay strategies, which errors trigger retry |
| Auth/authz | Required permissions, token types, header names |
| Rate limiting | Limits, windows, what happens when exceeded |
| Env dependencies | Environment variables read, config files loaded |
| Error recovery | Fallback behavior, circuit breakers, graceful degradation |
| Ordering constraints | Must-call-before relationships, initialization requirements |
| Thread safety | Mutex usage, atomic operations, concurrent access limitations |

Flag any non-obvious behavior that the draft omits. This catches the omission failure mode — documentation that looks complete but misses critical behavior a developer would need to know.

### Verification Report

After all four checks, output:

```
### Verification Results

**Mechanically verified (N claims):**
- [claim] — confirmed via `grep ...` → [evidence at file:line]
- ...

**Self-reviewed (M claims):**
- [claim] — semantic description, not mechanically verifiable
- ...

**Checks:**
- **Claim verification:** [X of Y claims mechanically verified — see evidence above]
  OR [FAIL — N claims contradicted by code; revised in Phase 3]
- **Example validation:** [PASS — all function names, params, imports grep-confirmed]
  OR [FAIL — examples N, M use non-existent APIs; revised in Phase 3]
- **Padding & value:** [PASS — no banned words, no signature parroting (self-reviewed)]
  OR [FAIL — banned words found in sections X, Y; revised in Phase 3]
- **Completeness:** [PASS — non-obvious behaviors documented]
  OR [FAIL — N non-obvious behaviors missing; added in Phase 3]
```

---

## Phase 3: Revise

For each check that failed in Phase 2:

1. Rewrite the specific failing section(s)
2. Re-run the failed check(s) on the rewrite — for claim verification, re-run the grep/read commands
3. If still failing, iterate once more — if a check is genuinely inapplicable (e.g., no code examples in a pure explanation doc), document why and mark as N/A

Do not skip this phase. The value of the skill is that it catches and fixes problems that ad-hoc documentation generation misses.

---

## Output Format

Deliver the final documentation in this format:

```markdown
## Documentation: [Component/Feature Name]

**Audience:** [Developer / Operator / End User] | **Type:** [Tutorial / How-to / Reference / Explanation / Mixed-file] | **Target:** [file or module]

### Verification Results

**Mechanically verified (N claims):**
- [claim] — [evidence]
- ...

**Self-reviewed (M claims):**
- [claim] — [reason not mechanically verifiable]
- ...

**Checks:**
- Claim verification: [result]
- Example validation: [result]
- Padding & value: [result]
- Completeness: [result]

### Documentation

[The actual documentation content]

### Notes (if applicable)
- [Discrepancies found between code and existing docs]
- [Non-obvious behaviors discovered during verification]
- [Suggestions for the user — e.g., code that behaves differently than its comments claim]
```

---

## Escalation — When to Stop and Ask

- Target code has no clear public API or documentable behavior
- Doc type cannot be determined and user hasn't specified one
- Code and existing documentation contradict each other — which is correct?
- Target is actively being refactored (volatile code better served by tests than docs)
- Mechanical verification reveals code behavior that contradicts the code's own comments/docstrings
- Target depends on external services with no local documentation or type stubs

---

## Optional: Governance Enhancement

If the ai-governance MCP server is available in this session (check if `search_references` tool exists), you can enhance documentation quality:

1. Query: `search_references(query="documentation patterns", domain="ai-coding")`
2. Incorporate returned patterns into Phase 1 writing constraints
3. Example: surfaces documentation-writer subagent patterns, Divio framework references

The skill is fully functional without this. Governance is an enhancement, not a dependency.

---

## Reference: Format-Specific Patterns

Consult this section when generating specific documentation types. Read only the relevant subsection, not all of them.

### README Pattern

1. Project name + one-line description (what it is, not "Welcome to...")
2. Quick start (fewest steps from clone to working — must be copy-paste-runnable)
3. Prerequisites (specific: "Node.js >= 18" not "recent Node")
4. Installation (exact commands)
5. Usage (most common use case with real example)
6. Configuration (env vars, config files, defaults, non-obvious options)
7. Architecture overview (if >5 files — one paragraph or diagram)
8. Contributing (how to run tests, code style, PR process)
9. License (one line)

### Python Docstring (Google Style)

```python
def function(arg1: str, arg2: int = 10) -> bool:
    """One-line summary in imperative mood.

    Add information NOT visible in the signature: behavior details,
    side effects, performance characteristics, thread safety.

    Args:
        arg1: What this means semantically, not just its type.
        arg2: Constraints, valid ranges, what happens at boundaries.
            Defaults to 10 (explain WHY 10 if non-obvious).

    Returns:
        What the return value represents. When it might be False.

    Raises:
        ValueError: When arg2 is negative — explain the constraint.

    Example:
        >>> function("test", 42)
        True
    """
```

### TypeScript/JSDoc

```typescript
/**
 * One-line summary of what this does.
 *
 * Add semantics beyond the types — the types say WHAT,
 * the doc says WHY and WHEN.
 *
 * @param userId - Supabase auth UID (not database row ID)
 * @returns The user's workspace memberships, empty array if none
 * @throws {AuthError} If the session token is expired
 *
 * @example
 * const memberships = await getUserWorkspaces("auth-uid-123");
 */
```

### API Reference

For each endpoint:
- Method + path (`POST /api/users`)
- One-line description
- Parameters table (name, type, required, description with constraints)
- Request body (with example)
- Response (status code, body with example)
- Error responses (status codes, error format, common causes)
- Authentication requirements
- Rate limits (if applicable)
