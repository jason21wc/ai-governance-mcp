---
description: Run the test authoring checklist — 9-step gate extending the test-generator agent protocol with project-specific gates for failure-mode registry integration, observability asserts, validation-chain preservation, and before-commit lint/map sequence. Invoke when writing new tests or reviewing test quality.
disable-model-invocation: true
allowed-tools: Bash Read Edit Write Agent
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Test count:** !`python3 -c "import subprocess; r=subprocess.run(['pytest','tests/','-q','--co','-m','not slow'],capture_output=True,text=True); print(r.stdout.strip().split(chr(10))[-1] if r.returncode==0 else 'error')" 2>/dev/null || echo "(count unavailable)"`
**Failure mode registry:** !`wc -l documents/failure-mode-registry.md 2>/dev/null || echo "(not found)"`

```!
echo "=== Recent test files ==="
git log --oneline -5 --diff-filter=A -- 'tests/test_*.py' 2>/dev/null || echo "(no recent test files)"
```

## Instructions

You are running the test authoring checklist. Read `checklist.md` in this skill folder for the full 9-step gate.

### Execution Protocol

1. **Read `checklist.md`** — it extends the test-generator agent protocol (`documents/agents/test-generator.md`) with project-specific gates.

2. **Execute all 9 steps** in order. Steps marked [NOVEL] are unique to this project. Steps marked [→ SEE] delegate to their canonical source.

3. **For each test being written:**
   - Step 1: Name the failure mode BEFORE writing `def test_…`
   - Steps 2-4: Check fixtures, level, echo-chamber (delegate to canonical sources)
   - Step 5: Assert observable state changed, not just return value
   - Step 6: Environment skips + validation-chain preservation
   - Steps 7-8: Apply markers + `Covers:` annotation
   - Step 9: Before-commit verification (name, local run, lint, map regen)

### Key Principle

Per `coding-quality-testing-integration` (Q3): tests must catch failure modes, not echo the implementation. If a WRONG implementation would still pass the test, rewrite it.

### Canonical Sources

- **Agent protocol:** `documents/agents/test-generator.md` — 6-step Test Creation Protocol
- **CFR testing methods:** `documents/title-10-ai-coding-cfr.md` §5.2
- **Failure-mode registry:** `documents/failure-mode-registry.md`
