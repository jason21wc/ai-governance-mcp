# Test → Failure-Mode Coverage Map

**AUTO-GENERATED.** Do not edit. Regenerate via `python3 scripts/generate-test-failure-map.py`. Generated artifact — exempt from the rules-of-procedure §2.1.1 version-history requirement (history lives in the generator + registry).

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

### `FM-EMBEDDING-SPACE-DIVERGENCE-AT-LOAD`

> Index loaders must verify build-space == query-space BEHAVIORALLY at the trust boundary (re-encode stored canary texts via the real query encoder, compare cosine), not only structurally (model label / row count / dimension) — a divergent embedding space is structurally indistinguishable from a good one and silently kills semantic search (governance session-205→209 silent-BM25 incident). On divergence or any gate error: discard embeddings loudly and degrade to BM25-only; never crash the load, never trigger a rebuild from a transient condition (re-index-storm surface). Canary text must be the EXACT string fed to encode() at build (prefix + truncation transform), or the gate false-fails healthy indexes. Applies to both subsystems: retrieval.py _load_index (#58) and context_engine project_manager._canary_check_passes (#59).

- `tests/test_context_engine.py` → `TestEmbeddingCanaryGate::test_load_gate_discards_divergent_embeddings`
- `tests/test_retrieval.py` → `TestCanaryGate::test_canary_failure_coldstart_falls_to_bm25`

### `FM-FEEDBACK-RATING-BOUNDS`

> log_feedback must reject rating values outside 1..5 (bounds validation at the MCP boundary).

- `tests/test_models.py` → `TestFeedback::test_rating_constraints`
- `tests/test_server_retrieval.py` → `TestHandleLogFeedback::test_handle_log_feedback_invalid_rating_high`
- `tests/test_server_retrieval.py` → `TestHandleLogFeedback::test_handle_log_feedback_invalid_rating_low`

### `FM-FUSION-RENORMALIZE-ON-MISSING-SIGNAL`

> Hybrid score fusion must renormalize weights onto the signals actually present. When one retriever returns no results for the whole query (BM25-only read-only/no-embeddings mode, or embedding daemon down so semantic_search returns []), applying the full semantic_weight/bm25_weight split caps every combined score at the surviving signal's weight (e.g. BM25-only <= 1 - semantic_weight = 0.4) and drops all results below min_score_threshold (0.3, scaled for fused scores) — forced-domain retrieve() then returns zero principles. Renormalize on WHOLE-LIST emptiness (a retriever produced nothing), NOT per-item absence (an item simply missing from a working retriever's top-k keeps a legitimate 0.0). Both fusion sites (fuse_scores + search_references inline fusion) must stay in lockstep. Fix the fusion math, never lower the threshold (Symptom Sprint Trap).

- `tests/test_retrieval.py` → `TestScoreFusion::test_fusion_bm25_only_renormalizes_when_semantic_unavailable`

### `FM-HOOK-CONTRARIAN-REQUIRED`

> pre-exit-plan-mode-gate must deny when contrarian-reviewer was not invoked for the current plan.

- `tests/test_pre_exit_plan_mode_gate_hook.py` → `TestDenyPath::test_deny_when_prior_exit_plan_and_no_contrarian`

### `FM-HOOK-CONTRARIAN-SCANNER-TOOL-COVERAGE`

> Scanner must recognize contrarian-reviewer invocation via BOTH Task and Agent tools (Claude Code's native + Agent variants share input.subagent_type shape).

- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_allow_with_agent_tool_underscore_variant`
- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_allow_with_agent_tool_variant`
- `tests/test_hooks.py` → `TestContrarianAfterLastPlan::test_deny_when_agent_tool_has_wrong_subagent_type`

### `FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS`

> The read-only Bash allowlist must not blanket-allow coreutils commands that are read-only in bare form but MUTATING with specific flags. Commands in READONLY_CMDS with known mutation flags (find -delete/-exec/-execdir/-ok/-okdir, sort -o/--output) must be checked against the MUTATION_FLAGS dict; the mutating form must fall through to evaluate_governance. Handles both --flag value and --flag=value forms.

- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_find_delete_denied`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_find_exec_denied`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_find_execdir_denied`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_find_readonly_still_allows`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_sort_long_output_flag_denied`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_sort_output_flag_denied`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_sort_readonly_still_allows`

### `FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS`

> The read-only Bash allowlist (pre-tool-governance-check.sh) must not blanket-allow dual-use git subcommands that are read-only in bare/list form but MUTATING with arguments. Only enumerated read-only (subcommand, next-token) pairs in GIT_READONLY_PAIRS may skip the governance gate; bare `git stash`, `git branch -D/-m`, `git tag <name>/-d`, and `git remote add/remove/set-url` must fall through to evaluate_governance. Listing such a subcommand in the blanket GIT_READONLY set is fail-OPEN — the pair-check becomes structurally unreachable and the mutating form bypasses the gate.

- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_branch_create_still_requires_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_branch_force_delete_still_requires_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_remote_add_still_requires_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_remote_remove_still_requires_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_tag_create_still_requires_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_write_git_tag_delete_still_requires_governance`

### `FM-HOOK-FAIL-CLOSED-EXIT-2`

> Hard-mode hooks must fail closed on exit 2 (not exit 1, which Claude Code treats as fail-open).

- `tests/test_pre_test_oom_gate_hook.py` → `TestFailClosedOnUnexpectedError::test_err_trap_converts_failures_to_exit_2`
- `tests/test_pre_test_oom_gate_hook.py` → `TestInternalPsTimeout::test_ps_timeout_fails_closed`

### `FM-HOOK-GOVERNANCE-GATE-REQUIRED`

> pre-tool-governance-check hook must deny (exit 2) when evaluate_governance() AND query_project() are not both recently invoked in transcript — structural parallel to FM-HOOK-CONTRARIAN-REQUIRED but for the governance+CE gate.

- `tests/test_hooks.py` → `TestPreToolDeniesBothMissing::test_pretool_denies_both_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesCEMissing::test_pretool_denies_ce_missing`
- `tests/test_hooks.py` → `TestPreToolDeniesGovernanceMissing::test_pretool_denies_governance_missing`

### `FM-HOOK-OOM-GATE-SUBSTRING-FP`

> The OOM gate top-level pytest detector is a SUBSTRING regex that matches 'pytest ' anywhere in the command string. When pytest appears as an argument (not in executable position) — e.g. `grep pytest Makefile`, `rg pytest src/` — the gate enters, the segment-level first-token analysis correctly finds 0 pytest segments, but the missing early exit causes fallthrough to environment risk checks → deny. The segment-level verdict (_PYTEST_SEGMENTS_SEEN=0) must exit-allow before environment checks when not in raw-triage mode.

- `tests/test_pre_test_oom_gate_hook.py` → `TestPytestSubstringFalsePositiveAllow::test_chained_grep_pytest_then_real_pytest_still_denied`
- `tests/test_pre_test_oom_gate_hook.py` → `TestPytestSubstringFalsePositiveAllow::test_pytest_as_argument_allowed`
- `tests/test_pre_test_oom_gate_hook.py` → `TestPytestSubstringFalsePositiveAllow::test_wrapped_pytest_still_denied`

### `FM-HOOK-OUTPUT-ENVELOPE`

> Context-injecting hooks (UserPromptSubmit, SessionStart, PreToolUse soft-mode) must emit additionalContext NESTED under hookSpecificOutput with the correct hookEventName. Claude Code silently discards a flat top-level {additionalContext} object (exit 0, no error), so the injected context never reaches the model. Tests must assert the nested CONSUMER shape (and hookEventName), not the emitted shape, or the no-op ships green.

- `tests/test_hooks.py` → `TestFrameInjection::test_frame_outputs_valid_json`
- `tests/test_hooks.py` → `TestPreToolValidJSONOutput::test_pretool_valid_json_soft_mode`

### `FM-HOOK-PIPEFAIL-EARLY-CONSUMER`

> In a pipefail-enabled hook, a pipeline must not feed an early-closing consumer (grep -q/--quiet, head, sed q, or awk exit). Early success can SIGPIPE the producer, turn the pipeline nonzero, and skip or erase a deny. Use a here-string or Bash builtin for decisions and a whole-stream consumer for previews; enforce the class across the full hook corpus.

- `tests/test_hooks.py` → `TestBypassAuditLog::test_check10_denies_push_of_non_bijective_domain_index`
- `tests/test_hooks.py` → `TestBypassAuditLog::test_check10_denies_push_of_non_bijective_index`
- `tests/test_hooks.py` → `TestBypassAuditLog::test_check10_passes_healthy_index`
- `tests/test_pipefail_early_consumers.py` → `test_rejects_early_consumers_after_a_pipe`
- `tests/test_pipefail_early_consumers.py` → `test_repository_hook_corpus_is_clean`

### `FM-INDEX-SILENT-NARROWING`

> An index rebuild must not silently replace the live index with a materially smaller one. A misconfigured path (the MCP host's AI_GOVERNANCE_* env is not inherited by a shell) rebuilds against defaults, exits 0, and degrades retrieval with nothing announcing it. Guard at the write: refuse on a per-category shrink beyond INDEX_SHRINK_TOLERANCE unless --force, and print the resolved paths plus per-kind counts every run.

- `tests/test_index_shrink_guard.py` → `TestTheGuardBlocksTheRealIncident::test_reference_collapse_is_refused`

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

> Governance S-Series keyword scanner must demote matches when (a) every sentence containing the keyword also contains a safe-context leader phrase (negation incl. no/not/never/cannot and the n't contraction suffix, meta-description, governance-prose idiom, temporal-distancing) AND (b) no danger verb threatens the keyword across TWO tiers with DIFFERENT scoping: a MUTATION verb (`_IMPERATIVE_ACTION_VERBS`: delete/drop/rm/nuke/...) anywhere in the action blocks demotion FIELD-WIDE; an EGRESS/disclosure verb (`_EGRESS_VERBS`: send/email/publish/upload/exfiltrate/transmit/disclose/expose/leak/dump/export/...) blocks only when co-located in the keyword's own sentence. Field-wide mutation catches 'delete the prod DB; credentials not affected' (dangerous clause has no critical keyword); sentence-scoped egress closes 'not destructive, send the credential' WITHOUT re-flagging 'publish the notes; no credentials'. The SAME predicate suppresses ADVISORY-keyword warnings in safe context (zero veto impact — advisory never escalates alone). Sentence-boundary regex must include em-dash, en-dash, semicolon, and newline (not just `[.!?]`). Field-bridging guard: per-field calls to `_detect_safety_concerns` (planned_action / context / concerns separately) prevent leaders in one field from covering keywords in another. Leader list, mutation-verb list, and egress-verb list co-evolve — widening the leader list (e.g. negation forms) requires auditing BOTH verb tiers. Residual (lexical limit): exotic egress verbs + cross-sentence pronoun reference — tracked under BACKLOG #73 (semantic retrieval precision).

- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_critical_safety_keywords_pinned_for_co_evolution`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_egress_verbs_cover_disclosure_family`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_colocated_mutation_still_escalates`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_contraction_leader_demotes_critical`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_egress_verb_in_separate_clause_demotes`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_egress_verb_with_leader_still_escalates`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_em_dash_separates_sentences`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_field_bridging_does_not_demote`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_imperative_inside_envelope_known_overtrigger`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_imperative_overrides_safe_envelope`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_meta_description_does_not_escalate`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_multi_word_critical_in_safe_context`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_mutation_verb_separate_clause_still_escalates`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_negated_advisory_warning_suppressed`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_negation_leader_demotes_critical`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_no_destructive_implications_passes`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_partial_wrap_per_sentence_rule_fires`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_r1_two_field_payload_does_not_escalate`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_evaluate_governance_safe_context_demotes_critical_keyword`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_imperative_action_verbs_covers_common_mutations`
- `tests/test_server_governance.py` → `TestEvaluateGovernance::test_safe_context_leaders_negation_boundary`

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

### `FM-SKILL-EXECUTABLE-PREAMBLE`

> A first-party SKILL.md must not execute shell while loading. Claude's worktree guard is closed-source, argument-sensitive, and version-sensitive; one refused preamble prevents the skill from loading, while Codex renders the syntax literally. Live context must be gathered by ordinary instructions after load, where failures can be split, retried, or reported.

- `tests/test_check_skill_preambles.py` → `test_a_marker_inside_a_double_backtick_span_IS_a_finding`
- `tests/test_check_skill_preambles.py` → `test_checker_is_wired_to_public_authoring_gate`
- `tests/test_check_skill_preambles.py` → `test_detects_inline_preamble`
- `tests/test_check_skill_preambles.py` → `test_exceptions_list_is_empty`
- `tests/test_check_skill_preambles.py` → `test_repo_tree_is_clean`
- `tests/test_skill_preamble_private_wiring.py` → `test_private_check_sh_invokes_skill_preamble_checker`

### `FM-STATE-EXPIRY-BOUNDARY-INCLUSIVE`

> Cross-MCP governance state file must enforce strict TTL boundary: age=(TTL-1) accepts, age=(TTL+1) rejects. Off-by-one at the boundary is a classic security-adjacent bug class for time-based authorization.

- `tests/test_enforcement.py` → `TestSharedState::test_shared_state_within_ttl`

### `FM-UNGUARDED-CWD-READ`

> A process outlives its working directory: once that directory is unlinked, Path.cwd()/os.getcwd() raise for the process lifetime. All cwd reads must route through path_resolution.safe_cwd() (returns None), and callers must fail safe — a scope check drops cwd from its allowed set (stricter, never wider); a write path with no destination refuses rather than guessing.

- `tests/test_deleted_cwd_resilience.py` → `TestSafeCwd::test_returns_none_instead_of_raising`

### `FM-VERDICT-DISCARDED-BY-FAILED-SIDE-EFFECT`

> A computed governance verdict must survive a failed durable telemetry write. Audit/reasoning persistence is best-effort (absorbed as OSError/LogPathOutOfScope and counted in _telemetry_failures); only configuration and security invariants may be fatal, and they must fail before the first verdict exists.

- `tests/test_deleted_cwd_resilience.py` → `TestTelemetryFailureDoesNotDiscardTheRecord::test_audit_write_survives_dead_cwd`

### `FM-WATCHER-DAEMON-SYMLINK-ESCAPE`

> Watcher daemon project discovery must filter symlinked directories to prevent escape from the index-storage base_path. Parallels FM-PROJECT-ID-PATH-TRAVERSAL for daemon-scan operations.

- `tests/test_watcher_daemon.py` → `TestDiscoverProjects::test_discover_skips_symlinks`

### `FM-WORKTREE-DUPLICATE-TASK`

> Distinct worktree paths do not prove distinct intent. Sequential duplicate active task keys must refuse; explicit parallel work requires an explicit key and remains visible; optimistic simultaneous creation must select one deterministic winner while locked task-conflict losers continue blocking sequential duplicates until explicitly resolved or safely abandoned.

- `tests/test_prepare_worktree.py` → `test_post_create_race_marks_loser_conflicted_and_continue_can_resolve`

### `FM-WORKTREE-JOURNAL-V2-STRICT`

> Framework-owned worktree lifecycle v2 must use one strict ordered journal schema and a matching ai-worktree-v2 Git lock across prepare, cleanup, all-clear, and repository-hygiene consumers. Missing, reordered, malformed, control-character-bearing, or incoherent evidence must fail closed rather than be guessed or downgraded to legacy ownership.

- `tests/test_prepare_worktree.py` → `test_continue_refuses_v2_lock_with_unexpected_fields`
- `tests/test_worktree_journal_contract.py` → `test_all_journal_consumers_declare_one_ordered_v2_schema`
- `tests/test_worktree_journal_contract.py` → `test_prepare_writer_emits_the_declared_schema_in_order`
- `tests/test_worktree_journal_contract.py` → `test_v2_lock_contract_is_named_v2_in_every_reader_and_writer`

### `FM-WORKTREE-OWNER-ACK-FINALIZE`

> A live framework owner may finalize only through one atomic cleanup invocation whose --owner-pid exactly matches a coherent v2 ready journal and corroborating lock (or a pristine task-conflict). The acknowledgement waives only the live-owner veto; durability, integration, cleanliness, sensitive-ignored, and final evidence rechecks still apply, and --force cannot be combined with it.

- `tests/test_cleanup_worktree.py` → `TestOwnerAcknowledgedFinalize::test_matching_live_owner_can_finalize_strict_v2`
- `tests/test_worktree_ownership.py` → `test_matching_live_v2_owner_can_finalize_atomically`

## Advisory Entries

### `FM-DOC-VERSION-SURFACE-DRIFT`

> Every body version/date surface of a frontmatter-versioned governance document (H1 trailing version, body **Version:**/**Effective Date:** lines, footer *Version X*, changelog current-row) must agree with frontmatter; the validator must scan the whole fence-stripped body (a header-region scope misses the real post-H2 shape) and must not over-fire on changelog history rows, version-bump prose, placeholders, or fenced template examples.

- `tests/test_extractor.py` → `TestBodyVersionSurfaces::test_decoy_fenced_example_changelog_ignored`
- `tests/test_extractor.py` → `TestBodyVersionSurfaces::test_h1_trailing_version_drift_detected`
- `tests/test_extractor.py` → `TestBodyVersionSurfaces::test_version_line_after_h2_subtitle_is_still_checked`

### `FM-EMBEDDING-MODEL-ALLOWLIST-AT-INIT`

> Non-allowlisted embedding models must be rejected at `__init__` (eager validation), not at inference / first encode call. Lazy rejection wastes a model-load attempt and surfaces the failure far from its cause.

- `tests/test_extractor.py` → `TestEmbeddingGeneratorInit::test_init_rejects_non_allowlisted_model`

### `FM-HEARTBEAT-THREAD-RACE-CONDITION`

> `_heartbeat_loop` must execute each tick atomically with respect to `stop_event` checks — no gap where elapsed crosses `hard_cap` but thread misses `stop_event` until next iteration.

- `tests/test_watcher_daemon.py` → `TestHeartbeatLoopSelfExit::test_loop_sets_stop_event_when_hard_cap_fires`

### `FM-HOOK-SIGKILL-TIMEOUT-NOT-COVERED`

> Bash ERR trap is necessary and NOT sufficient for fail-closed hooks. It does not fire on SIGKILL (the Claude Code hook-timeout mechanism), on a failed `source`, or on an unbound variable under `set -u` — the latter two measured on bash 3.2.57, both exit 1, which the harness treats as ALLOW, and both abort before any decision logic runs. Naming only the timeout implied the trap covered the rest. Hooks need the trap PLUS guarded `source` with an inline fallback PLUS `${VAR:-}` defaults.

- `tests/test_pre_test_oom_gate_hook.py` → `TestInternalPsTimeout::test_ps_timeout_fails_closed`

### `FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION`

> Governance hook reads parent transcript; subagent MCP calls live in separate files. Read-only Bash allowlist solves read-only subagents (contrarian-reviewer, security-auditor). Mutation subagents (test-generator, documentation-writer) remain blocked until upstream fix (Claude Code agentId in hook input).

- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_readonly_gh_api_get_allows_without_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_readonly_gh_pr_view_allows_without_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_readonly_gh_repo_view_allows_without_governance`
- `tests/test_hooks.py` → `TestPreToolReadOnlyBashAllowlist::test_readonly_gh_run_list_allows_without_governance`
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

