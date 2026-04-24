---
version: "1.0.0"
status: "active"
effective_date: "2026-04-23"
domain: "meta"
governance_level: "testing-framework"
schema_version: 1
entries:
  - id: FM-HOOK-FAIL-CLOSED-EXIT-2
    description: "Hard-mode hooks must fail closed on exit 2 (not exit 1, which Claude Code treats as fail-open)."
    must_cover: true
    scope: project
    introduced: "2026-04-16"
    source: "LEARNING-LOG: Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed (2026-04-16)"
  - id: FM-HOOK-CONTRARIAN-REQUIRED
    description: "pre-exit-plan-mode-gate must deny when contrarian-reviewer was not invoked for the current plan."
    must_cover: true
    scope: project
    introduced: "2026-04-22"
    source: "BACKLOG #116 / V-004 escalation; session-122"
  - id: FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE
    description: "Scanner must recognize contrarian-reviewer invocation via BOTH Task and Agent tools (Claude Code's native + Agent variants share input.subagent_type shape)."
    must_cover: true
    scope: project
    introduced: "2026-04-23"
    source: "session-123 dogfood — Agent-tool false-negative blocked valid plan"
  - id: FM-PROJECT-ID-PATH-TRAVERSAL
    description: "Project-id validation must reject path-traversal sequences (`../`, `..\\`, etc.) to prevent filesystem escape."
    must_cover: true
    scope: project
    introduced: "2026-02-19"
    source: "Security contract — FilesystemStorage base_path"
  - id: FM-PROJECT-ID-SLASHES
    description: "Project-id validation must reject slashes and backslashes — accepted ids map to subdirectory names and slashes break that mapping."
    must_cover: true
    scope: project
    introduced: "2026-02-19"
  - id: FM-RATE-LIMITER-BLOCKS-EXCESS
    description: "RateLimiter must enforce per-window bounds — first N allowed, subsequent rejected until window rolls."
    must_cover: true
    scope: project
    introduced: "2026-03-15"
    source: "SLA contract for query endpoints"
  - id: FM-FEEDBACK-RATING-BOUNDS
    description: "log_feedback must reject rating values outside 1..5 (bounds validation at the MCP boundary)."
    must_cover: true
    scope: project
    introduced: "2026-02-15"
  - id: FM-EMBEDDING-LAZY-LOAD-SINGLE
    description: "Embedding model must lazy-load once and be cached thereafter — double-load would cost memory + risk non-atomic init under threading."
    must_cover: true
    scope: project
    introduced: "2026-02-12"
  - id: FM-SCANNER-SUBSTRING-FALSE-MATCH
    description: "Transcript scanner must parse tool_use blocks, not substring-match raw line content — guards against file reads that MENTION the target tool name without invoking it."
    must_cover: true
    scope: project
    introduced: "2026-04-22"
    source: "session-122 contrarian finding; test_hooks.py::test_deny_on_substring_false_match"
  - id: FM-S-SERIES-KEYWORD-FALSE-POSITIVE
    description: "Governance S-Series semantic match should not trigger on keyword presence in negation context (e.g. 'NOT removing production data')."
    must_cover: false
    scope: project
    introduced: "2026-02-22"
    source: "LEARNING-LOG: S-Series Keyword Trigger Produces False Positives on Negations"
  - id: FM-TEST-SIDE-EFFECTS
    description: "Observability tests must assert state changes / side effects, not just return values (a function can return success while failing to write its file)."
    must_cover: false
    scope: framework
    introduced: "2026-04-15"
    source: "LEARNING-LOG: Test Side Effects, Not Just Return Values"
  - id: FM-TEST-FULL-VALIDATION-CHAIN
    description: "Test inputs must traverse the full production validation chain — bypassing validation for convenience hides bugs in the validation path."
    must_cover: false
    scope: framework
    introduced: "2026-02-11"
    source: "LEARNING-LOG: Test Inputs Must Traverse the Full Validation Chain"
  - id: FM-TEST-ENVIRONMENT-AWARE
    description: "Tests that depend on optional dependencies (daemon, network, real ML model) must skip or mock cleanly — not hard-fail on CI."
    must_cover: false
    scope: framework
    introduced: "2026-02-12"
    source: "LEARNING-LOG: Environment-Aware Tests for Optional Dependencies"
  - id: FM-TEST-ECHO-CHAMBER
    description: "Tests must fail against a WRONG implementation, not just pass against the current one — tautological tests give false assurance."
    must_cover: false
    scope: framework
    introduced: "2026-03-29"
    source: "Q3 principle + coding-quality-testing-integration"
  - id: FM-HOOK-SIGKILL-TIMEOUT-NOT-COVERED
    description: "Bash ERR trap does not cover SIGKILL (Claude Code hook-timeout mechanism) — hooks relying solely on ERR trap for fail-closed will fail-open on timeout."
    must_cover: false
    scope: project
    introduced: "2026-04-21"
    source: "LEARNING-LOG: Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout"
  - id: FM-ML-MODEL-MOCK-AT-SOURCE
    description: "Mock ML models at the import site (the module that uses them), not at the library root — patches at the wrong level silently miss."
    must_cover: false
    scope: framework
    introduced: "2025-12-27"
    source: "LEARNING-LOG: ML Model Mocking: Patch at Source"
  - id: FM-AUDIT-ID-FORMAT-INVARIANT
    description: "Governance audit IDs must have `gov-` prefix + 12 hex chars (16 total) and be unique across calls — contract consumed by `scripts/analyze_compliance.py` and external compliance tooling."
    must_cover: true
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 0 gap detection; BACKLOG #121"
  - id: FM-HOOK-GOVERNANCE-GATE-REQUIRED
    description: "pre-tool-governance-check hook must deny (exit 2) when evaluate_governance() AND query_project() are not both recently invoked in transcript — structural parallel to FM-HOOK-CONTRARIAN-REQUIRED but for the governance+CE gate."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 0 gap detection; BACKLOG #121"
  - id: FM-SERIES-CODE-SUBSTRING-COLLISION
    description: "`category_mapping` dict iteration must place longer keys before shorter keys when one is a substring of the other — `keyword in section_lower` matching otherwise misroutes (e.g., `ev-series` → `verification` instead of `evaluation`; `sec-series` → `context` instead of `security`)."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 0 gap detection; BACKLOG #121; PROJECT-MEMORY Gotcha #33"
  - id: FM-REGISTRY-UNKNOWN-ID-REJECTED
    description: "TestFailureModeCoverage lint must reject `Covers:` annotations with IDs not present in the registry — prevents typo drift (FM-X vs FM-x, FM-FOO vs FM-FOO-BAR)."
    must_cover: true
    scope: framework
    introduced: "2026-04-23"
    source: "v3 plan round-2 BLOCKER-2"
  - id: FM-REGISTRY-RETIRED-ID-DEPRECATION
    description: "TestFailureModeCoverage lint must emit a deprecation warning (not a hard failure) when tests cite a retired registry ID — gives migration window."
    must_cover: false
    scope: framework
    introduced: "2026-04-23"
  - id: FM-REGISTRY-MUST-COVER-HAS-ANNOTATION
    description: "Every registry entry with must_cover: true must have at least one test annotated with `Covers: <id>` — enforces that critical failure modes actually have coverage."
    must_cover: true
    scope: framework
    introduced: "2026-04-23"
    source: "v3 plan Phase 4"
---

# Failure Mode Registry

**Purpose.** Single source of truth for failure-mode identifiers (`FM-*`) cited by test-docstring `Covers:` annotations. The registry is consumed by `TestFailureModeCoverage` (lint in `tests/test_validator.py`) and by `scripts/generate-test-failure-map.py` (derived map).

**Why this exists.** Without a registry, `Covers:` annotations turn into pattern-matched theatre — two authors coin `FM-B2` and `fm-b2` for different concepts; a refactor splits `FM-B2` into `FM-B2a`/`FM-B2b` but annotations never update; a derived map aggregates typos as "distinct" coverage. The registry makes IDs a contract: unknown = test failure, retired = deprecation warning, must_cover without any annotation = test failure.

**Known limitation (semantic theatre).** The registry closes *ID-typo theatre* and *missing-coverage theatre*. It does NOT close *semantic theatre* — a test annotated `Covers: FM-X` could assert something unrelated to `FM-X` and the lint won't notice, because the lint inspects docstrings not test bodies. The annotation is ultimately self-reported. Mitigation is human: when adding a `Covers:` annotation, verify the test body actually exercises the failure mode. Periodic sample audits of the derived map (walk random annotations, confirm the test's assertions match the registry description) catch drift. Automated body-inspection was considered and rejected — false-positive surface too broad; human sampling is cheaper and more accurate.

**Schema.** Each entry in the YAML frontmatter `entries` list has:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Uppercase identifier, `FM-` prefix. Treated as a contract — do not rename in-place; retire + introduce a new ID. |
| `description` | yes | One-line English description of the failure mode. |
| `must_cover` | yes | `true` → lint requires at least one test with `Covers: <this-id>`. `false` → advisory; annotations are accepted but not required. |
| `scope` | yes | `framework` → universal rule that would apply to any project adopting this governance framework (anti-patterns, registry-internal invariants). `project` → specific to this project's surface (hooks, scanner, MCP tools, hosted endpoints). Positions the registry for future scaffold-safe seeding via BACKLOG #125-b — scaffold_project would copy only `framework`-scope entries to new adopter projects. |
| `introduced` | yes | ISO date the entry was added. |
| `source` | no | Provenance: LEARNING-LOG entry, BACKLOG item, principle reference, session log. |
| `retired` | no | ISO date the entry was retired. Annotations citing a retired ID emit deprecation warnings, not failures. |
| `supersedes` | no | ID(s) of prior entries this one replaces. Enables migration tracking. |

**Must-cover discipline.** Only flag `must_cover: true` when (a) the failure mode has already caused production harm OR has a specific LEARNING-LOG incident, AND (b) at least one existing test covers it (so flipping the flag doesn't immediately break the lint). Flipping to `true` without coverage is a trap — file a BACKLOG item to add the test first, then flip.

**Demotion discipline (`true` → `false`).** Because the `TestFailureModeCoverage::test_every_must_cover_entry_has_annotation` lint fails if a must_cover entry has no annotation, the path of least resistance when the lint reddens is to demote the flag. This would decay the registry's signal. Rule: any commit that flips an entry from `must_cover: true` to `must_cover: false` must include in its commit message either (a) rationale why the failure mode is no longer regression-critical, OR (b) a pointer to the BACKLOG item that will restore coverage. Reviewers should reject bare demotions. BACKLOG #124 tracks the future structural enforcement (either git-hook rationale-check or CFR §5.2.8 normative language).

**Annotation format.** Tests cite entries in their docstring:

```python
def test_deny_on_substring_false_match(self):
    """Scanner must parse tool_use, not substring-match file-read content.

    Covers: FM-SCANNER-SUBSTRING-FALSE-MATCH
    """
```

Multiple IDs comma-separated **on a single line** (the current scanner regex is single-line; multi-line continuation is NOT supported — it will silently truncate. Use one `Covers:` line per annotation; if the list grows unwieldy, split into two docstring paragraphs with separate `Covers:` lines — each line is captured additively):

```python
"""
Covers: FM-HOOK-CONTRARIAN-REQUIRED, FM-HOOK-FAIL-CLOSED-EXIT-2
"""
```

**Adding a new entry.**

1. Ensure the failure mode is real — has caused a regression, is named in LEARNING-LOG or BACKLOG, or encodes a security/SLA contract.
2. Add an entry to the `entries:` YAML list above. Fill all required fields.
3. If `must_cover: true`, ensure at least one existing test is already annotated — run the lint to confirm.
4. Run `python3 scripts/generate-test-failure-map.py` to regenerate `documents/test-failure-mode-map.md`.
5. Commit registry + regenerated map together.

**Retiring an entry.**

1. Add `retired: YYYY-MM-DD` to the entry (keep the rest of the fields).
2. Optionally point new code at a replacement via `supersedes:` on the replacement entry.
3. Do not delete the entry — retained for historical annotations in older tests that haven't been migrated.
4. Annotations citing a retired ID will emit deprecation warnings until migrated.

**Seeding policy.** This initial registry (v1.0.0) seeds failure modes from:

- LEARNING-LOG anti-patterns that recur across ≥2 sessions.
- Security contracts (project-id validation, path-traversal guards).
- SLA / bounds contracts (rate limiter, feedback rating).
- Hook-enforcement invariants (fail-closed on exit 2, contrarian required, scanner tool coverage).
- Registry-itself invariants (unknown-id-rejected, must-cover-has-annotation).

Broader annotation sweep across the full suite is deferred to BACKLOG #121 — the derived map explicitly warns readers that empty cells reflect *un-annotated* tests, not *uncovered* failure modes.

**Cross-references.**

- `tests/test_validator.py::TestFailureModeCoverage` — lint enforcement.
- `scripts/generate-test-failure-map.py` — derived map generator.
- `documents/test-failure-mode-map.md` — derived, auto-generated.
- `workflows/TEST-AUTHORING-CHECKLIST.md` — author-time workflow that requires picking a failure mode before writing a test.
- CFR §5.2.8 (title-10-ai-coding-cfr.md) — normative "Redundancy & Consolidation" rule that references this registry.
