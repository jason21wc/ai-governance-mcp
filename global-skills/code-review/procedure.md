# Code Review Orchestration Procedure

## Step 1: Determine Review Scope

Identify what code to review, in order of precedence:

1. **User-specified scope** — "review file X" or "review this PR" → use that scope
2. **Staged changes** — `git diff --cached` has content → review staged changes
3. **Branch diff** — current branch differs from main → `git diff main...HEAD`
4. **Fallback** — ask the user: "What would you like me to review? You can specify files, a commit range, or say 'review staged changes.'"

Capture the diff output and list of changed files. This becomes the review input for all passes.

## Step 2: Read Pass Instructions

Read the pass instruction files that will be injected into subagent prompts:

**Core passes (always):**
- `passes/correctness.md`
- `passes/security.md`
- `passes/architecture.md`

**Optional passes (when user requests "full review", "include performance", or "include test coverage"):**
- `passes-optional/performance.md`
- `passes-optional/test-coverage.md`

## Step 3: Construct Shared Assumptions Brief

Build a context block that every subagent receives. Include:

```
## Review Context
- **Scope:** [staged changes | branch diff from main | specific files]
- **Files changed:** [list of files]
- **Language/framework:** [detected from file extensions and imports]
- **Diff size:** [approximate line count]

## Your Task
Review the code below against your pass-specific checklist. For EVERY finding:
1. Cite the exact file:line
2. Quote the problematic code (1-5 lines)
3. Assign severity: CRITICAL, HIGH, MEDIUM, or LOW
4. Suggest a specific fix

If you find no issues, say so explicitly. Do NOT manufacture findings.

## Code to Review
[Insert the diff or file contents here]
```

## Step 4: Dispatch Subagents

Launch 3 Agent subagents **in a single message** (parallel dispatch):

Each agent receives:
- The shared assumptions brief (Step 3)
- Its pass-specific instructions (from the pass file)
- Tools: `Read` (to examine additional context in files referenced by the diff)

**Agent prompt template:**
```
You are a specialized code reviewer performing a [PASS_NAME] review.

[SHARED_ASSUMPTIONS_BRIEF]

[PASS_SPECIFIC_INSTRUCTIONS from passes/[pass].md]
```

If optional passes are activated, dispatch them in the same parallel batch.

## Step 5: Reconciliation

After all subagents return, reconcile their findings into a single report.

### 5.1 Deduplication

Multiple passes may flag the same code location. Deduplicate:

- **Same `file:line`** across passes → merge into a single finding. Use the highest severity. Combine the issue descriptions (e.g., "Correctness: missing null check; Security: potential null pointer dereference").
- **Adjacent lines (within 3 lines)** about the same logical issue → merge.
- **Different aspects of the same code** → keep separate only if the issues are genuinely independent (e.g., a function has both a logic bug AND a naming problem).

### 5.2 Evidence Gate

**Drop any finding that lacks:**
- A specific `file:line` citation
- A quoted code snippet (1-5 lines)

Findings with vague locations ("somewhere in the auth module") or no code evidence are unreliable and must be removed.

### 5.3 Cross-Pass Conflict Resolution

When passes give conflicting advice about the same code:

- **Architecture says "extract this function" + Correctness says "fix the logic in this function"** → present both findings with a sequencing note: "Fix the logic first, then extract."
- **Security says "add validation" + Architecture says "this function is too long"** → these are independent; keep both.
- **Two passes disagree on severity** → use the higher severity.

### 5.4 Severity Classification

| Tier | Severity | Meaning | Shown By Default? |
|------|----------|---------|-------------------|
| 1 | CRITICAL | Could cause data loss, security breach, or system failure in production | Yes |
| 1 | HIGH | Incorrect behavior that users or downstream systems will encounter | Yes |
| 2 | MEDIUM | Correct but fragile, hard to maintain, or deviating from project standards | Yes |
| 3 | LOW | Improvement opportunity, no current risk | No (opt-in via "full review") |

### 5.5 Output Cap

- **Default mode (Tier 1+2):** Maximum 15 findings. If more exist, keep the highest severity ones and note: "N additional Tier 2 findings omitted. Say 'full review' to see all."
- **Full review mode (all tiers):** Maximum 25 findings.

## Step 6: Format Output

Present the reconciled review in this format:

```markdown
## Code Review: [scope description]

**Files Reviewed:** [list]
**Passes Run:** correctness, security, architecture [+ optional passes]
**Findings:** [count by severity]

### CRITICAL (Must Fix)
- `file:line` — [Issue] → [Fix]
  ```
  [quoted code]
  ```

### HIGH (Should Fix)
- `file:line` — [Issue] → [Fix]
  ```
  [quoted code]
  ```

### MEDIUM (Recommended)
- `file:line` — [Issue] → [Fix]
  ```
  [quoted code]
  ```

### LOW (Informational) — shown in full review only
- `file:line` — [Observation]

### Positive Notes
- [What's done well — be specific]

### Summary
[1-2 sentences: overall assessment and most important action item]
```

## When to Escalate

Stop and ask the user before proceeding when:
- **Domain expertise required** — cryptographic implementations, regulatory compliance logic, financial calculations, or other specialized code where incorrect review is worse than no review
- **Ambiguous findings** — you are uncertain whether something is a genuine issue or an intentional design choice (e.g., unusual error handling that might be a workaround for a known platform bug)
- **Sensitive code** — authentication flows, payment processing, or PII handling where a false negative could have serious consequences
- **Contradictory passes** — two passes give directly conflicting recommendations and you cannot determine the correct sequencing

## Failure Modes

- **All passes return "no issues"** → report a clean review. Do not manufacture issues to fill the template.
- **A subagent times out or fails** → note which pass failed and present findings from the passes that completed. Suggest re-running the failed pass.
- **Diff is very large (>500 lines)** → warn the user that review quality may degrade. Suggest reviewing in smaller chunks or focusing on specific files.
- **No diff available** → ask the user to specify what to review.
