---
description: Run a multi-pass code review on staged changes, a branch diff, or specific files. Dispatches three specialized reviewers (correctness, security, architecture) in parallel, then reconciles findings into a severity-gated report. Invoke when the user says "code review", "review my code", "review this PR", "review these changes", or "review the diff". Do NOT use for security-only audits (use /security-scan) or test generation (use /test-authoring).
disable-model-invocation: true
allowed-tools: Bash Read Agent
---

## Runtime Context

After the skill loads, establish the branch and inspect staged and unstaged diffs
with ordinary read-only Git calls. Distinguish a clean diff from a Git error.

## Instructions

You are running a multi-pass code review. Read `procedure.md` in this skill folder for the full orchestration protocol.

### Quick Start

1. **Collect the Runtime Context above and determine review scope.** If the user specified files or a diff range, use that. Otherwise:
   - Staged changes exist → review staged changes (`git diff --cached`)
   - On a branch other than main → review branch diff (`git diff main...HEAD`)
   - Neither → ask the user what to review

2. **Read `procedure.md`** for the full orchestration and reconciliation protocol.

3. **Read pass instruction files** from `passes/` directory. Each file contains focused review instructions for one subagent.

4. **Dispatch 3 Agent subagents in parallel** — correctness, security, architecture. Each gets the shared assumptions brief + its pass-specific instructions.

5. **Reconcile findings** per the reconciliation protocol in procedure.md. Deduplicate, apply evidence gate, enforce severity gating and output cap.

6. **Present the unified review** in the output format defined in procedure.md.

### Opt-In Passes

When the user says "full review", "include performance", or "include test coverage":
- Read additional pass files from `passes-optional/`
- Dispatch additional subagents alongside the core 3
- Include their findings in reconciliation

**Cross-vendor second opinion** (`passes-optional/cross-vendor.md`) — an independent review
from a different model lineage (OpenAI Codex / gpt). **Default where `scripts/codex_review.py`
exists in the repo AND `codex` is on PATH: run the `security` role automatically** (promoted
from opt-in on the session-240 measurement — cheap, low-noise, caught a real miss). Elsewhere
it is opt-in: run when the user says "cross-vendor", "codex review", "second opinion", or
"full review". Unlike the other passes this is NOT a Claude subagent: the orchestrator runs it
via **Bash** (in parallel with the subagent dispatch) and folds its JSON findings into
reconciliation. It self-skips silently when `codex` is absent or the primary session is itself
Codex, so it is safe to leave on by default.

### Output Defaults

- **Default:** Tier 1 (Blocking) + Tier 2 (Important) findings only
- **Full review:** All tiers including Tier 3 (Informational)
- **Max findings:** 15 in default mode, 25 in full review mode
- **Evidence required:** Every finding must cite `file:line` + quoted code

### Key Principles

- **Evidence over assertion.** Findings without specific code citations are dropped.
- **Noise is the enemy.** 60-80% of AI review comments are noise. Severity gating and evidence requirements are the primary filters.
- **Specialized passes catch more.** Each pass has focused instructions that prevent attention dilution across concerns.
- **Reconciliation is the value.** Raw subagent output is not the deliverable — the deduplicated, severity-ordered, evidence-gated report is.
