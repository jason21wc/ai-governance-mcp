---
version: "1.0.0"
status: "active"
effective_date: "2026-04-23"
domain: "meta"
governance_level: "testing-framework"
schema_version: 1
entries:
  - id: FM-WORKTREE-JOURNAL-V2-STRICT
    description: "Framework-owned worktree lifecycle v2 must use one strict ordered journal schema and a matching ai-worktree-v2 Git lock across prepare, cleanup, all-clear, and repository-hygiene consumers. Missing, reordered, malformed, control-character-bearing, or incoherent evidence must fail closed rather than be guessed or downgraded to legacy ownership."
    must_cover: true
    scope: project
    introduced: "2026-08-28"
    source: "BACKLOG #359; ADR-31 decisions (f)-(g)"
  - id: FM-WORKTREE-OWNER-ACK-FINALIZE
    description: "A live framework owner may finalize only through one atomic cleanup invocation whose --owner-pid exactly matches a coherent v2 ready journal and corroborating lock (or a pristine task-conflict). The acknowledgement waives only the live-owner veto; durability, integration, cleanliness, sensitive-ignored, and final evidence rechecks still apply, and --force cannot be combined with it."
    must_cover: true
    scope: project
    introduced: "2026-08-28"
    source: "BACKLOG #359; ADR-31 decision (f)"
  - id: FM-WORKTREE-DUPLICATE-TASK
    description: "Distinct worktree paths do not prove distinct intent. Sequential duplicate active task keys must refuse; explicit parallel work requires an explicit key and remains visible; optimistic simultaneous creation must select one deterministic winner while locked task-conflict losers continue blocking sequential duplicates until explicitly resolved or safely abandoned."
    must_cover: true
    scope: project
    introduced: "2026-08-28"
    source: "BACKLOG #359; ADR-31 decision (g)"
  - id: FM-SKILL-EXECUTABLE-PREAMBLE
    description: "A first-party SKILL.md must not execute shell while loading. Claude's worktree guard is closed-source, argument-sensitive, and version-sensitive; one refused preamble prevents the skill from loading, while Codex renders the syntax literally. Live context must be gathered by ordinary instructions after load, where failures can be split, retried, or reported."
    must_cover: true
    scope: project
    introduced: "2026-08-28"
    source: "BACKLOG #356; live /compliance-review refusal plus cross-host portability audit"
  - id: FM-HOOK-FAIL-CLOSED-EXIT-2
    description: "Hard-mode hooks must fail closed on exit 2 (not exit 1, which Claude Code treats as fail-open)."
    must_cover: true
    scope: project
    introduced: "2026-04-16"
    source: "LEARNING-LOG: Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed (2026-04-16)"
  - id: FM-HOOK-PIPEFAIL-EARLY-CONSUMER
    description: "In a pipefail-enabled hook, a pipeline must not feed an early-closing consumer (grep -q/--quiet, head, sed q, or awk exit). Early success can SIGPIPE the producer, turn the pipeline nonzero, and skip or erase a deny. Use a here-string or Bash builtin for decisions and a whole-stream consumer for previews; enforce the class across the full hook corpus."
    must_cover: true
    scope: project
    introduced: "2026-08-28"
    source: "BACKLOG #358; Check 10 reproduced the same fail-open shape already fixed at a different pre-push site"
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
  - id: FM-HOOK-OUTPUT-ENVELOPE
    description: "Context-injecting hooks (UserPromptSubmit, SessionStart, PreToolUse soft-mode) must emit additionalContext NESTED under hookSpecificOutput with the correct hookEventName. Claude Code silently discards a flat top-level {additionalContext} object (exit 0, no error), so the injected context never reaches the model. Tests must assert the nested CONSUMER shape (and hookEventName), not the emitted shape, or the no-op ships green."
    must_cover: true
    scope: project
    introduced: "2026-06-04"
    source: "Worktree gha-storage-remediation: FRAME hook + pre-tool soft-warn shipped the flat envelope (silent no-op); same class as the SessionStart fix session-195. CFR Recommended Hook Patterns examples taught the flat form (corrected, title-20-cfr v2.19.1). Covered by test_hooks.py nested-shape + hookEventName assertions."
  - id: FM-HOOK-OOM-GATE-SUBSTRING-FP
    description: "The OOM gate top-level pytest detector is a SUBSTRING regex that matches 'pytest ' anywhere in the command string. When pytest appears as an argument (not in executable position) — e.g. `grep pytest Makefile`, `rg pytest src/` — the gate enters, the segment-level first-token analysis correctly finds 0 pytest segments, but the missing early exit causes fallthrough to environment risk checks → deny. The segment-level verdict (_PYTEST_SEGMENTS_SEEN=0) must exit-allow before environment checks when not in raw-triage mode."
    must_cover: true
    scope: project
    introduced: "2026-08-07"
    source: "BACKLOG #230(b) — 4 of 13 recent OOM-gate denies were this FP class per Compliance Review #17. Root cause: segment-level first-token analysis was authoritative but its zero-count verdict had no early exit path."
  - id: FM-HOOK-DUAL-USE-COREUTILS-ALLOWLIST-BYPASS
    description: "The read-only Bash allowlist must not blanket-allow coreutils commands that are read-only in bare form but MUTATING with specific flags. Commands in READONLY_CMDS with known mutation flags (find -delete/-exec/-execdir/-ok/-okdir, sort -o/--output) must be checked against the MUTATION_FLAGS dict; the mutating form must fall through to evaluate_governance. Handles both --flag value and --flag=value forms."
    must_cover: true
    scope: project
    introduced: "2026-08-07"
    source: "BACKLOG #230(a) — session-265 Batch 2 mutation probe found find/sort bypassing the governance gate. Same root cause as FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS (membership-based blanket allow) extended to coreutils."
  - id: FM-HOOK-DUAL-USE-GIT-ALLOWLIST-BYPASS
    description: "The read-only Bash allowlist (pre-tool-governance-check.sh) must not blanket-allow dual-use git subcommands that are read-only in bare/list form but MUTATING with arguments. Only enumerated read-only (subcommand, next-token) pairs in GIT_READONLY_PAIRS may skip the governance gate; bare `git stash`, `git branch -D/-m`, `git tag <name>/-d`, and `git remote add/remove/set-url` must fall through to evaluate_governance. Listing such a subcommand in the blanket GIT_READONLY set is fail-OPEN — the pair-check becomes structurally unreachable and the mutating form bypasses the gate."
    must_cover: true
    scope: project
    introduced: "2026-06-13"
    source: "BACKLOG #62 (git stash) + session-213 contrarian extension to branch/tag/remote (fail-open confirmed via classifier traces). Root cause = membership-based blanket allow, not stash-specific."
  - id: FM-DOC-VERSION-SURFACE-DRIFT
    description: "Every body version/date surface of a frontmatter-versioned governance document (H1 trailing version, body **Version:**/**Effective Date:** lines, footer *Version X*, changelog current-row) must agree with frontmatter; the validator must scan the whole fence-stripped body (a header-region scope misses the real post-H2 shape) and must not over-fire on changelog history rows, version-bump prose, placeholders, or fenced template examples."
    must_cover: false
    scope: project
    introduced: "2026-07-10"
    source: "Session-244 corpus-cleanup: 8 docs drifted inside the validator blind spot ACTIVE in LEARNING-LOG since 2026-02-21 (frontmatter-present early-return never read the body); fixed via extractor.py::_body_version_surface_problems, TDD + adversarial decoys; Codex close-out forced whole-body scan + constitution H4-row recognition."
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
    description: "Governance S-Series keyword scanner must demote matches when (a) every sentence containing the keyword also contains a safe-context leader phrase (negation incl. no/not/never/cannot and the n't contraction suffix, meta-description, governance-prose idiom, temporal-distancing) AND (b) no danger verb threatens the keyword across TWO tiers with DIFFERENT scoping: a MUTATION verb (`_IMPERATIVE_ACTION_VERBS`: delete/drop/rm/nuke/...) anywhere in the action blocks demotion FIELD-WIDE; an EGRESS/disclosure verb (`_EGRESS_VERBS`: send/email/publish/upload/exfiltrate/transmit/disclose/expose/leak/dump/export/...) blocks only when co-located in the keyword's own sentence. Field-wide mutation catches 'delete the prod DB; credentials not affected' (dangerous clause has no critical keyword); sentence-scoped egress closes 'not destructive, send the credential' WITHOUT re-flagging 'publish the notes; no credentials'. The SAME predicate suppresses ADVISORY-keyword warnings in safe context (zero veto impact — advisory never escalates alone). Sentence-boundary regex must include em-dash, en-dash, semicolon, and newline (not just `[.!?]`). Field-bridging guard: per-field calls to `_detect_safety_concerns` (planned_action / context / concerns separately) prevent leaders in one field from covering keywords in another. Leader list, mutation-verb list, and egress-verb list co-evolve — widening the leader list (e.g. negation forms) requires auditing BOTH verb tiers. Residual (lexical limit): exotic egress verbs + cross-sentence pronoun reference — tracked under BACKLOG #73 (semantic retrieval precision)."
    must_cover: true
    scope: project
    introduced: "2026-02-22"
    source: "BACKLOG #129 closed 2026-05-01 by sentence-level safe-context allowlist (server.py::_is_keyword_in_safe_context). Covers Paths A+C; Path B (semantic retrieval FP for meta-safety-transparent-limitations on housekeeping actions) tracked separately as new BACKLOG entry — distinct fix surface (retrieval scoring, not keyword scanner)."
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
    retired: "2026-04-24"
    source: "LEARNING-LOG: Test Inputs Must Traverse the Full Validation Chain. Retired session-124: describes an anti-pattern discipline (don't bypass validation) with no binary-checkable mechanism — compliant tests just silently don't bypass, with no positive assertion to annotate. Lesson retained at LEARNING-LOG 2026-02-11 + 2026-04-24 + TEST-AUTHORING-CHECKLIST step 6. Parametrized traversal-taxonomy test added 2026-04-24 (`tests/test_context_engine.py::test_rejects_traversal_patterns`) annotates against existing FM-PROJECT-ID-PATH-TRAVERSAL — re-registration of THIS FM not pursued because `_validate_project_id` is single-stage (no validation-chain ordering to assert)."
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
    description: "Bash ERR trap is necessary and NOT sufficient for fail-closed hooks. It does not fire on SIGKILL (the Claude Code hook-timeout mechanism), on a failed `source`, or on an unbound variable under `set -u` — the latter two measured on bash 3.2.57, both exit 1, which the harness treats as ALLOW, and both abort before any decision logic runs. Naming only the timeout implied the trap covered the rest. Hooks need the trap PLUS guarded `source` with an inline fallback PLUS `${VAR:-}` defaults."
    must_cover: false
    scope: project
    introduced: "2026-04-21"
    source: "LEARNING-LOG: Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout"
  - id: FM-ML-MODEL-MOCK-AT-SOURCE
    description: "Mock ML models at the import site (the module that uses them), not at the library root — patches at the wrong level silently miss."
    must_cover: false
    scope: framework
    introduced: "2025-12-27"
    retired: "2026-04-24"
    source: "LEARNING-LOG: ML Model Mocking: Patch at Source. Retired session-124: (a) patch-location is a test-authoring convention, not a binary-checkable failure mode; compliant tests just use the correct patch location with no positive assertion verifying compliance. (b) FM name (AT-SOURCE) vs description (import-site) had internal contradiction that would require empirical verification to rewrite safely. Lesson retained at LEARNING-LOG 2025-12-27 + CFR §5.2.5 + test-generator agent prompt. Reference-library doc (``ref-ai-coding-pytest-fixture-patterns` (via search_references)`) reconciled 2026-04-24 to match CFR + LEARNING-LOG (patch at source library)."
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
  - id: FM-HOOK-SUBAGENT-TRANSCRIPT-ISOLATION
    description: "Governance hook reads parent transcript; subagent MCP calls live in separate files. Read-only Bash allowlist solves read-only subagents (contrarian-reviewer, security-auditor). Mutation subagents (test-generator, documentation-writer) remain blocked until upstream fix (Claude Code agentId in hook input)."
    must_cover: false
    scope: project
    introduced: "2026-05-07"
    source: "session-152 empirical proof: 10/10 subagents governance-compliant but hook-denied due to transcript isolation."
  - id: FM-INDEX-SILENT-NARROWING
    description: "An index rebuild must not silently replace the live index with a materially smaller one. A misconfigured path (the MCP host's AI_GOVERNANCE_* env is not inherited by a shell) rebuilds against defaults, exits 0, and degrades retrieval with nothing announcing it. Guard at the write: refuse on a per-category shrink beyond INDEX_SHRINK_TOLERANCE unless --force, and print the resolved paths plus per-kind counts every run."
    must_cover: true
    scope: project
    introduced: "2026-07-29"
    source: "session-271: a documented-as-correct rebuild replaced 80 reference entries with the 3 default-location test stubs; search_references returned only stubs machine-wide. Caught by arithmetic, not by a control."
  - id: FM-VERDICT-DISCARDED-BY-FAILED-SIDE-EFFECT
    description: "A computed governance verdict must survive a failed durable telemetry write. Audit/reasoning persistence is best-effort (absorbed as OSError/LogPathOutOfScope and counted in _telemetry_failures); only configuration and security invariants may be fatal, and they must fail before the first verdict exists."
    must_cover: true
    scope: project
    introduced: "2026-07-29"
    source: "session-271: ExitWorktree deleted the worktree a live governance server was launched in; Path.cwd() then raised for the process lifetime and every evaluate_governance returned [Errno 2] for a whole session. Third occurrence of the unguarded-cwd class."
  - id: FM-UNGUARDED-CWD-READ
    description: "A process outlives its working directory: once that directory is unlinked, Path.cwd()/os.getcwd() raise for the process lifetime. All cwd reads must route through path_resolution.safe_cwd() (returns None), and callers must fail safe — a scope check drops cwd from its allowed set (stricter, never wider); a write path with no destination refuses rather than guessing."
    must_cover: true
    scope: framework
    introduced: "2026-07-29"
    source: "session-271, occurrence 3. The 2026-04-10 LEARNING-LOG entry (already labelled SECOND OCCURRENCE) prescribed shared-module + a check; the module shipped, the unguarded call moved inside it, and the check never did."
  - id: FM-SERIES-CODE-SUBSTRING-COLLISION
    description: "`category_mapping` dict iteration must place longer keys before shorter keys when one is a substring of the other — `keyword in section_lower` matching otherwise misroutes (e.g., `ev-series` → `verification` instead of `evaluation`; `sec-series` → `context` instead of `security`)."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 0 gap detection; BACKLOG #121; PROJECT-MEMORY Gotcha #33"
  - id: FM-READONLY-WRITE-ESCAPE
    description: "Write operations (save_embeddings/save_metadata/save_chunks/save_bm25_index/save_file_manifest/delete_project) must raise `ReadOnlyStorageError` when ReadOnlyFilesystemStorage is active — silent no-op or partial write is a contract violation that leaks reads masquerading as no-ops."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-READONLY-INDEX-BLOCKING
    description: "Indexer and ProjectManager must raise `RuntimeError` for index operations (`index_project`, `incremental_update`, `reindex_project`) when `readonly=True` — auto-indexing retry logic must not bypass the read-only constraint."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-READONLY-CORRUPT-FILE-NO-UNLINK
    description: "Read-only storage must NOT delete or repair corrupt index files on load failure — log warning, return None, leave the file on disk. Auto-unlink would violate no-side-effects contract and mask silent data corruption."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-STATE-EXPIRY-BOUNDARY-INCLUSIVE
    description: "Cross-MCP governance state file must enforce strict TTL boundary: age=(TTL-1) accepts, age=(TTL+1) rejects. Off-by-one at the boundary is a classic security-adjacent bug class for time-based authorization."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-SHARED-STATE-MISSING-FILE-FAIL-CLOSED
    description: "Missing or corrupt cross-MCP state file must fail-closed (block tools), not fail-open (default allow). Absence of state must never grant access — state file disappearance is a containment failure, not an implicit reset."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-CONFIG-SECURITY-CRITICAL-PARAMS-PROTECTED
    description: "`GovernanceEnforcer.from_config()` must raise `ValueError` when external config attempts to override security-critical parameters (`enabled`, `GOVERNANCE_SATISFIERS`). Config-injection bypass prevention — external YAML must not be able to disable the gate."
    must_cover: true
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-WATCHER-DAEMON-SYMLINK-ESCAPE
    description: "Watcher daemon project discovery must filter symlinked directories to prevent escape from the index-storage base_path. Parallels FM-PROJECT-ID-PATH-TRAVERSAL for daemon-scan operations."
    must_cover: true
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-WATCHER-CORRUPT-METADATA-RESILIENCE
    description: "Project discovery must silently skip entries with malformed metadata.json (corrupt/truncated/invalid-JSON) — daemon must tolerate filesystem entropy without crashing or partial-parsing."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-HEARTBEAT-THREAD-RACE-CONDITION
    description: "`_heartbeat_loop` must execute each tick atomically with respect to `stop_event` checks — no gap where elapsed crosses `hard_cap` but thread misses `stop_event` until next iteration."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IDLE-DETECTION-MTIME-BOUNDARY
    description: "Idle-detection metadata scan must return the MOST RECENT activity time (max of mtimes, smallest seconds-ago) across all projects, not min/average — otherwise one stale project defers restart for the whole daemon."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-MAX-UPTIME-ZERO-DISABLE-CONTRACT
    description: "`max_uptime_seconds=0` (or unset) must disable watcher self-exit entirely, not default to a safety floor. Operators rely on this for maintenance windows / multi-phase deployments."
    must_cover: false
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IPC-SOCKET-PATH-SYMLINK-RESOLUTION
    description: "Socket path resolution must call `.resolve()` to canonicalize symlinks before containment check — unresolved intermediate paths allow symlink-based containment escapes (macOS `/tmp` → `/private/var/...` is the canonical test case)."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IPC-CONCURRENT-QUEUE-SERIALIZATION
    description: "Concurrent client requests on the shared server queue must not corrupt message boundaries or interleave payloads — length-prefix framing or equivalent is required under multi-threaded load."
    must_cover: false
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IPC-SOCKET-OWNERSHIP-NOT-PRIVILEGED
    description: "Unix domain socket must be created with mode 0600 (owner read-write only) — 0644 or world-readable permissions enable TOCTOU attacks and socket hijacking by other local processes."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IPC-SHUTDOWN-RELEASES-BLOCKED-HANDLERS
    description: "Server shutdown must call `SHUT_RDWR` on accepted connections (not just close the listen socket) — handlers blocked on `recv()` otherwise don't release, causing shutdown deadlock / leak / 30s CI flake."
    must_cover: false
    scope: project
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
  - id: FM-IPC-MESSAGE-LENGTH-PREFIX-INVARIANT
    description: "Encoded IPC messages must have a 4-byte big-endian length prefix where `length == total_bytes - 4`, validated on decode. Silent mismatch causes message corruption under pipelining/concurrency."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 Phase 3 gap detection; BACKLOG #121"
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
    placeholder: true
  - id: FM-REGISTRY-ADVISORY-SEED-AT-CREATION
    description: "Every advisory registry entry introduced on or after 2026-04-24 must have at least one seeded `Covers:` annotation at creation time, unless explicitly marked `placeholder: true`. Structural gate replacing the prose-only seed-at-creation rule per session-124 contrarian HIGH-1 (organic-growth mechanism had 4-month track record of failing to retrofit advisory annotations)."
    must_cover: true
    scope: framework
    introduced: "2026-04-24"
    source: "session-124 battery-fix-2 per contrarian HIGH-1; BACKLOG #121"
  - id: FM-REGISTRY-MUST-COVER-HAS-ANNOTATION
    description: "Every registry entry with must_cover: true must have at least one test annotated with `Covers: <id>` — enforces that critical failure modes actually have coverage."
    must_cover: true
    scope: framework
    introduced: "2026-04-23"
    source: "v3 plan Phase 4"
  - id: FM-UNICODE-NORMALIZATION-PRE-PATTERN-MATCH
    description: "Zero-width / invisible / NFKC-compatibility characters must be stripped before security regex pattern matching — unnormalized input enables unicode-obfuscation bypass of S-Series and similar gates."
    must_cover: false
    scope: framework
    introduced: "2026-04-24"
    source: "BACKLOG #128 / session-124 Phase 0 deferred advisory candidate"
  - id: FM-EMBEDDING-MODEL-ALLOWLIST-AT-INIT
    description: "Non-allowlisted embedding models must be rejected at `__init__` (eager validation), not at inference / first encode call. Lazy rejection wastes a model-load attempt and surfaces the failure far from its cause."
    must_cover: false
    scope: project
    introduced: "2026-04-24"
    source: "BACKLOG #128 / session-124 Phase 0 deferred advisory candidate"
  - id: FM-EMBEDDING-SPACE-DIVERGENCE-AT-LOAD
    description: "Index loaders must verify build-space == query-space BEHAVIORALLY at the trust boundary (re-encode stored canary texts via the real query encoder, compare cosine), not only structurally (model label / row count / dimension) — a divergent embedding space is structurally indistinguishable from a good one and silently kills semantic search (governance session-205→209 silent-BM25 incident). On divergence or any gate error: discard embeddings loudly and degrade to BM25-only; never crash the load, never trigger a rebuild from a transient condition (re-index-storm surface). Canary text must be the EXACT string fed to encode() at build (prefix + truncation transform), or the gate false-fails healthy indexes. Applies to both subsystems: retrieval.py _load_index (#58) and context_engine project_manager._canary_check_passes (#59)."
    must_cover: true
    scope: project
    introduced: "2026-06-11"
    source: "BACKLOG #58 (session-210, cdf7176) + #59 (session-213, 54fe122); LEARNING-LOG 2026-06-10 'Guard at the Trust Boundary' + 2026-06-11 'A Port Is Not a Copy'; tests in test_retrieval.py canary gate tests + test_context_engine.py::TestEmbeddingCanaryGate"
  - id: FM-FUSION-RENORMALIZE-ON-MISSING-SIGNAL
    description: "Hybrid score fusion must renormalize weights onto the signals actually present. When one retriever returns no results for the whole query (BM25-only read-only/no-embeddings mode, or embedding daemon down so semantic_search returns []), applying the full semantic_weight/bm25_weight split caps every combined score at the surviving signal's weight (e.g. BM25-only <= 1 - semantic_weight = 0.4) and drops all results below min_score_threshold (0.3, scaled for fused scores) — forced-domain retrieve() then returns zero principles. Renormalize on WHOLE-LIST emptiness (a retriever produced nothing), NOT per-item absence (an item simply missing from a working retriever's top-k keeps a legitimate 0.0). Both fusion sites (fuse_scores + search_references inline fusion) must stay in lockstep. Fix the fusion math, never lower the threshold (Symptom Sprint Trap)."
    must_cover: true
    scope: project
    introduced: "2026-05-31"
    source: "BACKLOG #52 (closed session-200, commit 66e98f6); LEARNING-LOG 2026-05-31 'Renormalize Hybrid-Fusion Weights When a Retriever Yields Nothing'; tests in test_retrieval.py::TestScoreFusion + test_retrieval_integration.py::TestRealIndexRetrieval"
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
| `scope` | yes | `framework` → universal rule that would apply to any project adopting this governance framework (anti-patterns, registry-internal invariants). `project` → specific to this project's surface (hooks, scanner, MCP tools, hosted endpoints). |
| `introduced` | yes | ISO date the entry was added. |
| `source` | no | Provenance: LEARNING-LOG entry, BACKLOG item, principle reference, session log. |
| `retired` | no | ISO date the entry was retired. Annotations citing a retired ID emit deprecation warnings, not failures. |
| `supersedes` | no | ID(s) of prior entries this one replaces. Enables migration tracking. |
| `placeholder` | no | `true` → entry is dormant-until-triggered (e.g., FM-REGISTRY-RETIRED-ID-DEPRECATION activates only once a registry entry is retired). Exempt from the seed-at-creation rule (step 3 below). Use sparingly — most FMs should have seed annotations at creation. |

**Must-cover discipline.** Only flag `must_cover: true` when (a) the failure mode has already caused production harm OR has a specific LEARNING-LOG incident OR enforces a named security/SLA contract in code (e.g., path-traversal guard, rate-limit bound, authentication boundary), AND (b) at least one existing test covers it (so flipping the flag doesn't immediately break the lint). Flipping to `true` without coverage is a trap — file a BACKLOG item to add the test first, then flip. The "security/SLA contract" branch codifies pre-existing practice (FM-PROJECT-ID-PATH-TRAVERSAL cites "Security contract" as source without a LEARNING-LOG incident); use it for invariants that would be security/availability bugs if violated, not for preference-level contracts.

**Demotion discipline (`true` → `false`).** Because the `TestFailureModeCoverage::test_every_must_cover_entry_has_annotation` lint fails if a must_cover entry has no annotation, the path of least resistance when the lint reddens is to demote the flag. This would decay the registry's signal. Rule: any commit that flips an entry from `must_cover: true` to `must_cover: false` must include in its commit message either (a) rationale why the failure mode is no longer regression-critical, OR (b) a pointer to the BACKLOG item that will restore coverage. Reviewers should reject bare demotions. BACKLOG #124 tracks the future structural enforcement (either git-hook rationale-check or CFR §5.2.9 normative language).

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
3. **Seed at creation — MUST-cover AND advisory (STRUCTURALLY ENFORCED for entries introduced ≥ 2026-04-24).** If `must_cover: true`, ensure at least one existing test is already annotated — `TestFailureModeCoverage::test_every_must_cover_entry_has_annotation` enforces this. If `must_cover: false` (advisory), include at least one seeded `Covers:` annotation in the same commit — `TestFailureModeCoverage::test_new_advisory_entries_have_annotation` enforces this for entries with `introduced ≥ 2026-04-24`. The structural gate replaces the prose-only rule that preceded it (session-123 through session-124 pre-extension): 4-month track record showed advisory entries filed without seeds stayed at zero annotations indefinitely. If you genuinely cannot find a test that covers the FM, either (a) file a BACKLOG item to write the test first, then add the registry entry, or (b) mark the entry `placeholder: true` (reserved for dormant-until-triggered FMs — use sparingly).

    **Additional filter (post-session-124 LEARNING-LOG 2026-04-24):** Before adding an advisory entry, ask *"what specific assertion would fail if this FM's invariant broke?"* If the answer is "any test that doesn't do X" (anti-pattern discipline), "fixing a known bug" (production limitation), or "tests that set up mocks this way" (authoring convention), the entry belongs in LEARNING-LOG / BACKLOG / reference-library, NOT the registry. Registry entries must be binary-checkable via a concrete assertion mechanism (file-exists, threshold, marker presence, ValueError raised).

    **Grandfathered entries (pre-2026-04-24 advisory entries exempt from the gate):** After session-124 extension cleanup, only **2 entries** remain exempt: FM-TEST-ENVIRONMENT-AWARE (now annotated on `tests/test_retrieval_quality.py::test_method_mrr_threshold` via pytest.mark.slow+real_index) and FM-REGISTRY-RETIRED-ID-DEPRECATION (`placeholder: true`, dormant-until-triggered). Three other grandfathered entries were retired 2026-04-24 per the filter above: FM-TEST-FULL-VALIDATION-CHAIN (anti-pattern; lesson at LEARNING-LOG 2026-02-11 + 2026-04-24), FM-S-SERIES-KEYWORD-FALSE-POSITIVE (re-registered 2026-05-01 with `must_cover: true` after BACKLOG #129 close — sentence-level safe-context allowlist shipped), FM-ML-MODEL-MOCK-AT-SOURCE (authoring convention; reference-library doc reconciled 2026-04-24). Three other pre-cutoff advisory entries (FM-TEST-SIDE-EFFECTS, FM-TEST-ECHO-CHAMBER, FM-HOOK-SIGKILL-TIMEOUT-NOT-COVERED) were annotated during the #121 sweep and no longer need grandfather protection.
4. Run `python3 scripts/generate-test-failure-map.py` to regenerate `documents/test-failure-mode-map.md`.
5. Commit registry + regenerated map + seed annotation(s) together.

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

Full-suite annotation sweep was completed in BACKLOG #121 (closed session-124, 2026-04-24). The derived map's empty-cell semantics still apply going forward: empty = un-annotated, not uncovered.

**Cross-references.**

- `tests/test_validator.py::TestFailureModeCoverage` — lint enforcement.
- `scripts/generate-test-failure-map.py` — derived map generator.
- `documents/test-failure-mode-map.md` — derived, auto-generated.
- `/test-authoring` checklist — author-time skill that requires picking a failure mode before writing a test.
- CFR §5.2.9 (title-10-ai-coding-cfr.md) — normative "Redundancy & Consolidation" rule that references this registry.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-23 | Initial release (BACKLOG #121/#123 arc, session-123/124): machine-readable failure-mode registry (frontmatter entries + prose catalog) consumed by `TestFailureModeCoverage` lint, the `/test-authoring` skill, and the auto-generated coverage map. Version-history section added retroactively 2026-07-10 (session-244 corpus-cleanup; §2.1.1 requires one on every normative document — this file shipped without). Convention: individual registry ENTRIES accrete without version bumps — each carries its own `introduced:` date in frontmatter; this table tracks structural/schema changes only. |
