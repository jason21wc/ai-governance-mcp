# Test → Failure-Mode Coverage Map

**AUTO-GENERATED.** Do not edit. Regenerate via `python3 scripts/generate-test-failure-map.py`.

**Coverage reflects ANNOTATED tests only.** An empty cell does NOT mean "failure mode uncovered" — it means "no test carries a `Covers: <id>` annotation yet." Full annotation sweep deferred to BACKLOG #121; this map documents the state of the annotation convention, not the state of test coverage.

**Freshness IS pre-commit-enforced** via the `regen-test-failure-mode-map` hook in `.pre-commit-config.yaml` (session-123 Commit F, BACKLOG #123 closed). The hook regenerates this map on any change to the registry, test files, or the generator itself, and fails the commit if the regenerated output differs from the staged version. If this map disagrees with the registry, trust the registry and re-stage after running the generator.

**Source registry:** `documents/failure-mode-registry.md`

## Must-Cover Entries

### `FM-AUDIT-ID-FORMAT-INVARIANT`

> Governance audit IDs must have `gov-` prefix + 12 hex chars (16 total) and be unique across calls — contract consumed by `scripts/analyze_compliance.py` and external compliance tooling.

- `tests/test_models.py` → `TestAuditFunctions::test_generate_audit_id_format`

### `FM-EMBEDDING-LAZY-LOAD-SINGLE`

> Embedding model must lazy-load once and be cached thereafter — double-load would cost memory + risk non-atomic init under threading.

- `tests/test_extractor.py` → `TestEmbeddingGeneratorLazyLoad::test_model_property_returns_cached`

### `FM-FEEDBACK-RATING-BOUNDS`

> log_feedback must reject rating values outside 1..5 (bounds validation at the MCP boundary).

- `tests/test_server.py` → `TestHandleLogFeedback::test_handle_log_feedback_invalid_rating_low`

### `FM-HOOK-CONTRARIAN-REQUIRED`

> pre-exit-plan-mode-gate must deny when contrarian-reviewer was not invoked for the current plan.

- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestDenyPath::test_deny_when_prior_exit_plan_and_no_contrarian`

### `FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE`

> Scanner must recognize contrarian-reviewer invocation via BOTH Task and Agent tools (Claude Code's native + Agent variants share input.subagent_type shape).

- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_allow_with_agent_tool_underscore_variant`
- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_allow_with_agent_tool_variant`
- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_deny_when_agent_tool_has_wrong_subagent_type`

### `FM-HOOK-FAIL-CLOSED-EXIT-2`

> Hard-mode hooks must fail closed on exit 2 (not exit 1, which Claude Code treats as fail-open).

- `tests/test_pre_test_oom_gate_hook.py` → `TestFailClosedOnUnexpectedError::test_err_trap_converts_failures_to_exit_2`

### `FM-HOOK-GOVERNANCE-GATE-REQUIRED`

> pre-tool-governance-check hook must deny (exit 2) when evaluate_governance() AND query_project() are not both recently invoked in transcript — structural parallel to FM-HOOK-CONTRARIAN-REQUIRED but for the governance+CE gate.

- `tests/test_hooks.py` → `TestPreToolDeniesBothMissing::test_pretool_denies_both_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesCEMissing::test_pretool_denies_ce_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesGovernanceMissing::test_pretool_denies_governance_missing`

### `FM-PROJECT-ID-PATH-TRAVERSAL`

> Project-id validation must reject path-traversal sequences (`../`, `..\`, etc.) to prevent filesystem escape.

- `tests/test_context_engine.py` → `TestProjectIdValidation::test_rejects_path_traversal`

### `FM-PROJECT-ID-SLASHES`

> Project-id validation must reject slashes and backslashes — accepted ids map to subdirectory names and slashes break that mapping.

- `tests/test_context_engine.py` → `TestProjectIdValidation::test_rejects_slashes`

### `FM-RATE-LIMITER-BLOCKS-EXCESS`

> RateLimiter must enforce per-window bounds — first N allowed, subsequent rejected until window rolls.

- `tests/test_context_engine.py` → `TestServerSecurity::test_rate_limiter_blocks_excess`

### `FM-REGISTRY-MUST-COVER-HAS-ANNOTATION`

> Every registry entry with must_cover: true must have at least one test annotated with `Covers: <id>` — enforces that critical failure modes actually have coverage.

- `tests/test_validator.py` → `TestDemotionRationale::test_registry_history_fully_available`
- `tests/test_validator.py` → `TestFailureModeCoverage::test_every_must_cover_entry_has_annotation`

### `FM-REGISTRY-UNKNOWN-ID-REJECTED`

> TestFailureModeCoverage lint must reject `Covers:` annotations with IDs not present in the registry — prevents typo drift (FM-X vs FM-x, FM-FOO vs FM-FOO-BAR).

- `tests/test_validator.py` → `TestFailureModeCoverage::test_every_covers_id_exists_in_registry`

### `FM-SCANNER-SUBSTRING-FALSE-MATCH`

> Transcript scanner must parse tool_use blocks, not substring-match raw line content — guards against file reads that MENTION the target tool name without invoking it.

- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_deny_on_substring_false_match`

### `FM-SERIES-CODE-SUBSTRING-COLLISION`

> `category_mapping` dict iteration must place longer keys before shorter keys when one is a substring of the other — `keyword in section_lower` matching otherwise misroutes (e.g., `ev-series` → `verification` instead of `evaluation`; `sec-series` → `context` instead of `security`).

- `tests/test_extractor.py` → `TestCategoryMappingSubstringCollisions::test_no_substring_collisions_in_ordering`

## Advisory Entries

### `FM-HOOK-SIGKILL-TIMEOUT-NOT-COVERED`

> Bash ERR trap does not cover SIGKILL (Claude Code hook-timeout mechanism) — hooks relying solely on ERR trap for fail-closed will fail-open on timeout.

_No annotated tests yet._

### `FM-ML-MODEL-MOCK-AT-SOURCE`

> Mock ML models at the import site (the module that uses them), not at the library root — patches at the wrong level silently miss.

_No annotated tests yet._

### `FM-REGISTRY-RETIRED-ID-DEPRECATION`

> TestFailureModeCoverage lint must emit a deprecation warning (not a hard failure) when tests cite a retired registry ID — gives migration window.

_No annotated tests yet._

### `FM-S-SERIES-KEYWORD-FALSE-POSITIVE`

> Governance S-Series semantic match should not trigger on keyword presence in negation context (e.g. 'NOT removing production data').

_No annotated tests yet._

### `FM-TEST-ECHO-CHAMBER`

> Tests must fail against a WRONG implementation, not just pass against the current one — tautological tests give false assurance.

_No annotated tests yet._

### `FM-TEST-ENVIRONMENT-AWARE`

> Tests that depend on optional dependencies (daemon, network, real ML model) must skip or mock cleanly — not hard-fail on CI.

_No annotated tests yet._

### `FM-TEST-FULL-VALIDATION-CHAIN`

> Test inputs must traverse the full production validation chain — bypassing validation for convenience hides bugs in the validation path.

_No annotated tests yet._

### `FM-TEST-SIDE-EFFECTS`

> Observability tests must assert state changes / side effects, not just return values (a function can return success while failing to write its file).

_No annotated tests yet._

