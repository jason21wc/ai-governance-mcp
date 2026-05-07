# Test → Failure-Mode Coverage Map

**AUTO-GENERATED.** Do not edit. Regenerate via `python3 scripts/generate-test-failure-map.py`.

**Coverage reflects ANNOTATED tests only.** An empty cell does NOT mean "failure mode uncovered" — it means "no test carries a `Covers: <id>` annotation yet." Full-suite annotation sweep was completed in BACKLOG #121 (closed session-124, 2026-04-24); this map documents the state of the annotation convention, not the state of test coverage. Note: parametrized tests count as 1 annotation per function definition; execution-instance count may be higher.

**Freshness IS pre-commit-enforced** via the `regen-test-failure-mode-map` hook in `.pre-commit-config.yaml` (session-123 Commit F, BACKLOG #123 closed). The hook regenerates this map on any change to the registry, test files, or the generator itself, and fails the commit if the regenerated output differs from the staged version. If this map disagrees with the registry, trust the registry and re-stage after running the generator.

**Source registry:** `documents/failure-mode-registry.md`

## Must-Cover Entries

### `FM-AUDIT-ID-FORMAT-INVARIANT`

> Governance audit IDs must have `gov-` prefix + 12 hex chars (16 total) and be unique across calls — contract consumed by `scripts/analyze_compliance.py` and external compliance tooling.

- `tests/test_models.py` → `TestAuditFunctions::test_generate_audit_id_format`
- `tests/test_models.py` → `TestAuditFunctions::test_generate_audit_id_unique`

### `FM-CONFIG-SECURITY-CRITICAL-PARAMS-PROTECTED`

> `GovernanceEnforcer.from_config()` must raise `ValueError` when external config attempts to override security-critical parameters (`enabled`, `GOVERNANCE_SATISFIERS`). Config-injection bypass prevention — external YAML must not be able to disable the gate.

- `tests/test_enforcement.py` → `TestSecurityHardening::test_from_config_rejects_security_critical_overrides`

### `FM-EMBEDDING-LAZY-LOAD-SINGLE`

> Embedding model must lazy-load once and be cached thereafter — double-load would cost memory + risk non-atomic init under threading.

- `tests/test_extractor.py` → `TestEmbeddingGeneratorInit::test_init_sets_model_name`
- `tests/test_extractor.py` → `TestEmbeddingGeneratorLazyLoad::test_model_property_loads_on_access`
- `tests/test_extractor.py` → `TestEmbeddingGeneratorLazyLoad::test_model_property_returns_cached`

### `FM-FEEDBACK-RATING-BOUNDS`

> log_feedback must reject rating values outside 1..5 (bounds validation at the MCP boundary).

- `tests/test_models.py` → `TestFeedback::test_rating_constraints`
- `tests/test_server.py` → `TestHandleLogFeedback::test_handle_log_feedback_invalid_rating_high`
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
- `tests/test_pre_test_oom_gate_hook.py` → `TestInternalPsTimeout::test_ps_timeout_fails_closed`

### `FM-HOOK-GOVERNANCE-GATE-REQUIRED`

> pre-tool-governance-check hook must deny (exit 2) when evaluate_governance() AND query_project() are not both recently invoked in transcript — structural parallel to FM-HOOK-CONTRARIAN-REQUIRED but for the governance+CE gate.

- `tests/test_hooks.py` → `TestPreToolDeniesBothMissing::test_pretool_denies_both_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesCEMissing::test_pretool_denies_ce_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesGovernanceMissing::test_pretool_denies_governance_missing`

### `FM-PROJECT-ID-PATH-TRAVERSAL`

> Project-id validation must reject path-traversal sequences (`../`, `..\`, etc.) to prevent filesystem escape.

- `tests/test_context_engine.py` → `TestListProjectsSymlinkExclusion::test_symlink_outside_storage_blocked_by_containment`
- `tests/test_context_engine.py` → `TestProjectIdValidation::test_rejects_path_traversal`
- `tests/test_context_engine.py` → `TestProjectIdValidation::test_rejects_traversal_patterns`

### `FM-PROJECT-ID-SLASHES`

> Project-id validation must reject slashes and backslashes — accepted ids map to subdirectory names and slashes break that mapping.

- `tests/test_context_engine.py` → `TestProjectIdValidation::test_rejects_slashes`

### `FM-RATE-LIMITER-BLOCKS-EXCESS`

> RateLimiter must enforce per-window bounds — first N allowed, subsequent rejected until window rolls.

- `tests/test_context_engine.py` → `TestServerSecurity::test_rate_limiter_blocks_excess`
- `tests/test_server.py` → `TestRateLimiting::test_rate_limit_allows_initial_requests`
- `tests/test_server.py` → `TestRateLimiting::test_rate_limit_exhaustion`

### `FM-READONLY-CORRUPT-FILE-NO-UNLINK`

> Read-only storage must NOT delete or repair corrupt index files on load failure — log warning, return None, leave the file on disk. Auto-unlink would violate no-side-effects contract and mask silent data corruption.

- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_corrupt_embeddings_logs_warning_no_unlink`

### `FM-READONLY-INDEX-BLOCKING`

> Indexer and ProjectManager must raise `RuntimeError` for index operations (`index_project`, `incremental_update`, `reindex_project`) when `readonly=True` — auto-indexing retry logic must not bypass the read-only constraint.

- `tests/test_readonly.py` → `TestIndexerReadonly::test_incremental_update_raises_when_readonly`
- `tests/test_readonly.py` → `TestIndexerReadonly::test_index_project_raises_when_readonly`
- `tests/test_readonly.py` → `TestProjectManagerReadonly::test_reindex_project_raises`

### `FM-READONLY-WRITE-ESCAPE`

> Write operations (save_embeddings/save_metadata/save_chunks/save_bm25_index/save_file_manifest/delete_project) must raise `ReadOnlyStorageError` when ReadOnlyFilesystemStorage is active — silent no-op or partial write is a contract violation that leaks reads masquerading as no-ops.

- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_delete_project_raises`
- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_save_bm25_index_raises`
- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_save_chunks_raises`
- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_save_embeddings_raises`
- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_save_file_manifest_raises`
- `tests/test_readonly.py` → `TestReadOnlyFilesystemStorage::test_save_metadata_raises`

### `FM-REGISTRY-ADVISORY-SEED-AT-CREATION`

> Every advisory registry entry introduced on or after 2026-04-24 must have at least one seeded `Covers:` annotation at creation time, unless explicitly marked `placeholder: true`. Structural gate replacing the prose-only seed-at-creation rule per session-124 contrarian HIGH-1 (organic-growth mechanism had 4-month track record of failing to retrofit advisory annotations).

- `tests/test_validator.py` → `TestFailureModeCoverage::test_new_advisory_entries_have_annotation`

### `FM-REGISTRY-MUST-COVER-HAS-ANNOTATION`

> Every registry entry with must_cover: true must have at least one test annotated with `Covers: <id>` — enforces that critical failure modes actually have coverage.

- `tests/test_validator.py` → `TestDemotionRationale::test_registry_history_fully_available`
- `tests/test_validator.py` → `TestFailureModeCoverage::test_every_must_cover_entry_has_annotation`

### `FM-REGISTRY-UNKNOWN-ID-REJECTED`

> TestFailureModeCoverage lint must reject `Covers:` annotations with IDs not present in the registry — prevents typo drift (FM-X vs FM-x, FM-FOO vs FM-FOO-BAR).

- `tests/test_validator.py` → `TestFailureModeCoverage::test_every_covers_id_exists_in_registry`

### `FM-S-SERIES-KEYWORD-FALSE-POSITIVE`

> Governance S-Series CRITICAL keyword scanner must demote matches when (a) every sentence containing the keyword also contains a safe-context leader phrase (negation, meta-description, governance-prose idiom, temporal-distancing) AND (b) no imperative-action verb appears anywhere in the action. Sentence-boundary regex must include em-dash, en-dash, semicolon, and newline (not just `[.!?]`). Field-bridging guard: per-field calls to `_detect_safety_concerns` (planned_action / context / concerns separately) prevent leaders in one field from covering keywords in another. Imperative + safe-context re-escalates (bypass guard). Imperative-verb list and CRITICAL keyword list co-evolve — adding to either should audit whether the other needs extension.

- `tests/test_server.py` → `TestEvaluateGovernance::test_critical_safety_keywords_pinned_for_co_evolution`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_em_dash_separates_sentences`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_field_bridging_does_not_demote`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_imperative_inside_envelope_known_overtrigger`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_imperative_overrides_safe_envelope`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_meta_description_does_not_escalate`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_multi_word_critical_in_safe_context`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_no_destructive_implications_passes`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_partial_wrap_per_sentence_rule_fires`
- `tests/test_server.py` → `TestEvaluateGovernance::test_evaluate_governance_safe_context_demotes_critical_keyword`
- `tests/test_server.py` → `TestEvaluateGovernance::test_imperative_action_verbs_covers_common_mutations`

### `FM-SCANNER-SUBSTRING-FALSE-MATCH`

> Transcript scanner must parse tool_use blocks, not substring-match raw line content — guards against file reads that MENTION the target tool name without invoking it.

- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_deny_on_substring_false_match`
- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestFalseMatchGuard::test_deny_on_file_read_mentioning_contrarian`

### `FM-SERIES-CODE-SUBSTRING-COLLISION`

> `category_mapping` dict iteration must place longer keys before shorter keys when one is a substring of the other — `keyword in section_lower` matching otherwise misroutes (e.g., `ev-series` → `verification` instead of `evaluation`; `sec-series` → `context` instead of `security`).

- `tests/test_extractor.py` → `TestCategoryMappingSubstringCollisions::test_no_substring_collisions_in_ordering`
- `tests/test_extractor.py` → `TestMultimodalRagExtraction::test_ev_series_not_verification`
- `tests/test_extractor.py` → `TestMultimodalRagExtraction::test_sec_series_not_context`

### `FM-SHARED-STATE-MISSING-FILE-FAIL-CLOSED`

> Missing or corrupt cross-MCP state file must fail-closed (block tools), not fail-open (default allow). Absence of state must never grant access — state file disappearance is a containment failure, not an implicit reset.

- `tests/test_enforcement.py` → `TestSharedState::test_shared_state_missing_file`

### `FM-STATE-EXPIRY-BOUNDARY-INCLUSIVE`

> Cross-MCP governance state file must enforce strict TTL boundary: age=(TTL-1) accepts, age=(TTL+1) rejects. Off-by-one at the boundary is a classic security-adjacent bug class for time-based authorization.

- `tests/test_enforcement.py` → `TestSharedState::test_shared_state_within_ttl`

### `FM-WATCHER-DAEMON-SYMLINK-ESCAPE`

> Watcher daemon project discovery must filter symlinked directories to prevent escape from the index-storage base_path. Parallels FM-PROJECT-ID-PATH-TRAVERSAL for daemon-scan operations.

- `tests/test_watcher_daemon.py` → `TestDiscoverProjects::test_discover_skips_symlinks`

## Advisory Entries

### `FM-EMBEDDING-MODEL-ALLOWLIST-AT-INIT`

> Non-allowlisted embedding models must be rejected at `__init__` (eager validation), not at inference / first encode call. Lazy rejection wastes a model-load attempt and surfaces the failure far from its cause.

- `tests/test_extractor.py` → `TestEmbeddingGeneratorInit::test_init_rejects_non_allowlisted_model`

### `FM-HEARTBEAT-THREAD-RACE-CONDITION`

> `_heartbeat_loop` must execute each tick atomically with respect to `stop_event` checks — no gap where elapsed crosses `hard_cap` but thread misses `stop_event` until next iteration.

- `tests/test_watcher_daemon.py` → `TestHeartbeatLoopSelfExit::test_loop_sets_stop_event_when_hard_cap_fires`

### `FM-HOOK-SIGKILL-TIMEOUT-NOT-COVERED`

> Bash ERR trap does not cover SIGKILL (Claude Code hook-timeout mechanism) — hooks relying solely on ERR trap for fail-closed will fail-open on timeout.

- `tests/test_pre_test_oom_gate_hook.py` → `TestInternalPsTimeout::test_ps_timeout_fails_closed`

### `FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION`

> Governance hook reads parent transcript; subagent MCP calls live in separate files. Read-only Bash allowlist solves read-only subagents (contrarian-reviewer, security-auditor). Mutation subagents (test-generator, documentation-writer) remain blocked until upstream fix (Claude Code agentId in hook input).

- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_readonly_git_log_allows_without_governance`

### `FM-IDLE-DETECTION-MTIME-BOUNDARY`

> Idle-detection metadata scan must return the MOST RECENT activity time (max of mtimes, smallest seconds-ago) across all projects, not min/average — otherwise one stale project defers restart for the whole daemon.

- `tests/test_watcher_daemon.py` → `TestLastActivitySecondsAgo::test_max_across_multiple_projects`

### `FM-IPC-CONCURRENT-QUEUE-SERIALIZATION`

> Concurrent client requests on the shared server queue must not corrupt message boundaries or interleave payloads — length-prefix framing or equivalent is required under multi-threaded load.

- `tests/test_embedding_ipc.py` → `TestEmbeddingServerClient::test_concurrent_requests`

### `FM-IPC-MESSAGE-LENGTH-PREFIX-INVARIANT`

> Encoded IPC messages must have a 4-byte big-endian length prefix where `length == total_bytes - 4`, validated on decode. Silent mismatch causes message corruption under pipelining/concurrency.

- `tests/test_embedding_ipc.py` → `TestMessageSerialization::test_encode_decode_round_trip`

### `FM-IPC-SHUTDOWN-RELEASES-BLOCKED-HANDLERS`

> Server shutdown must call `SHUT_RDWR` on accepted connections (not just close the listen socket) — handlers blocked on `recv()` otherwise don't release, causing shutdown deadlock / leak / 30s CI flake.

- `tests/test_embedding_ipc.py` → `TestClientRetry::test_shutdown_closes_accepted_conns_fast`

### `FM-IPC-SOCKET-OWNERSHIP-NOT-PRIVILEGED`

> Unix domain socket must be created with mode 0600 (owner read-write only) — 0644 or world-readable permissions enable TOCTOU attacks and socket hijacking by other local processes.

- `tests/test_embedding_ipc.py` → `TestSocketPermissions::test_socket_created_with_0600`

### `FM-IPC-SOCKET-PATH-SYMLINK-RESOLUTION`

> Socket path resolution must call `.resolve()` to canonicalize symlinks before containment check — unresolved intermediate paths allow symlink-based containment escapes (macOS `/tmp` → `/private/var/...` is the canonical test case).

- `tests/test_embedding_ipc.py` → `TestSocketPathSecurity::test_path_outside_containment_rejected`

### `FM-MAX-UPTIME-ZERO-DISABLE-CONTRACT`

> `max_uptime_seconds=0` (or unset) must disable watcher self-exit entirely, not default to a safety floor. Operators rely on this for maintenance windows / multi-phase deployments.

- `tests/test_watcher_daemon.py` → `TestReadMaxUptimeFromEnv::test_zero_returns_none`

### `FM-REGISTRY-RETIRED-ID-DEPRECATION`

> TestFailureModeCoverage lint must emit a deprecation warning (not a hard failure) when tests cite a retired registry ID — gives migration window.

_No annotated tests yet._

### `FM-TEST-ECHO-CHAMBER`

> Tests must fail against a WRONG implementation, not just pass against the current one — tautological tests give false assurance.

- `tests/test_retrieval_quality.py` → `TestRegressionThresholds::test_method_mrr_threshold`
- `tests/test_scaffold_parity.py` → `TestScaffoldParityWithCFR152::test_scaffold_parity_is_bidirectional`

### `FM-TEST-ENVIRONMENT-AWARE`

> Tests that depend on optional dependencies (daemon, network, real ML model) must skip or mock cleanly — not hard-fail on CI.

- `tests/test_retrieval_quality.py` → `TestRegressionThresholds::test_method_mrr_threshold`

### `FM-TEST-SIDE-EFFECTS`

> Observability tests must assert state changes / side effects, not just return values (a function can return success while failing to write its file).

- `tests/test_extractor_integration.py` → `TestExtractAll::test_extract_all_saves_content_embeddings`
- `tests/test_extractor_integration.py` → `TestExtractAll::test_extract_all_saves_index_file`
- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestAuditLog::test_deny_writes_audit_entry`
- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestAuditLog::test_log_rotation_caps_at_100kb`
- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestAuditLog::test_semantic_bypass_writes_audit_entry`
- `tests/test_pre_test_oom_gate_hook.py` → `TestDenyLogSideEffect::test_allow_does_not_write_deny_log`
- `tests/test_pre_test_oom_gate_hook.py` → `TestDenyLogSideEffect::test_deny_writes_to_log_file`
- `tests/test_server_integration.py` → `TestMetricsAccumulation::test_metrics_accumulate_across_queries`

### `FM-UNICODE-NORMALIZATION-PRE-PATTERN-MATCH`

> Zero-width / invisible / NFKC-compatibility characters must be stripped before security regex pattern matching — unnormalized input enables unicode-obfuscation bypass of S-Series and similar gates.

- `tests/test_extractor.py` → `TestUnicodeNormalization::test_normalize_text_strips_invisible_chars`

### `FM-WATCHER-CORRUPT-METADATA-RESILIENCE`

> Project discovery must silently skip entries with malformed metadata.json (corrupt/truncated/invalid-JSON) — daemon must tolerate filesystem entropy without crashing or partial-parsing.

- `tests/test_context_engine.py` → `TestStartupWatchers::test_startup_watchers_handles_corrupt_metadata`
- `tests/test_watcher_daemon.py` → `TestDiscoverProjects::test_discover_skips_corrupt_metadata`

## Retired Entries

### `FM-ML-MODEL-MOCK-AT-SOURCE` **[RETIRED]**

> Mock ML models at the import site (the module that uses them), not at the library root — patches at the wrong level silently miss.

_No annotated tests yet._

### `FM-TEST-FULL-VALIDATION-CHAIN` **[RETIRED]**

> Test inputs must traverse the full production validation chain — bypassing validation for convenience hides bugs in the validation path.

_No annotated tests yet._

