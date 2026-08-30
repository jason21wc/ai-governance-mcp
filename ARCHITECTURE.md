# AI Governance MCP — Architecture

**Version:** 2.0.0
**Date:** 2026-04-12
**Memory Type:** Structural (reference)

> System design, component responsibilities, data flow.
> For decisions/rationale → PROJECT-MEMORY.md
> Avoid volatile metrics here (test counts, coverage %, dependency versions) — use canonical sources (`pytest`, `pytest --cov`, `pyproject.toml`).

**Phase:** COMPLETE — 23 tools across 2 MCP servers (16 governance + 7 context engine)

---

## System Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI GOVERNANCE MCP                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   server    │───→│  retrieval  │───→│   models    │    │   config    │  │
│  │             │    │             │    │             │    │             │  │
│  │ MCP tools   │    │ Router      │    │ Pydantic    │    │ Settings    │  │
│  │ exposed to  │    │ Hybrid      │    │ schemas     │    │ Paths       │  │
│  │ AI clients  │    │ Reranker    │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                                                │
│         │                  ▼                                                │
│         │           ┌─────────────┐                                         │
│         │           │   index     │  (loaded at startup, auto-reloaded)     │
│         │           │             │                                         │
│         │           │ principles  │                                         │
│         │           │ embeddings  │                                         │
│         │           │ domains     │                                         │
│         │           └─────────────┘                                         │
│         │                  ▲                                                │
│         │                  │ (built offline)                                │
│         │           ┌─────────────┐                                         │
│         │           │  extractor  │───→ Parses markdown docs                │
│         │           └─────────────┘                                         │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                            │
│  │  feedback   │  (append-only log)                                         │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | What It Does | Why Separate |
|-----------|--------------|--------------|
| **server/** | Exposes MCP tools, handles requests (11-module package) | Single entry point for AI clients |
| **retrieval.py** | Domain routing, hybrid search, reranking | Core intelligence, testable in isolation |
| **extractor.py** | Parses docs, builds index, generates embeddings | Runs offline, not at runtime |
| **models.py** | Pydantic schemas for principles, domains, results | Type safety, validation, serialization |
| **path_resolution.py** | Scope checking, project detection, and `safe_cwd()` — the single guarded working-directory read for the whole package | Shared by BOTH servers so neither reimplements it; `safe_cwd()` is asserted to be the only cwd read by `tests/test_no_unguarded_cwd.py` (see Orchestrator Failure Modes) |
| **config.py** | Settings, paths, environment config | Centralized configuration |
| **index/** | JSON + embeddings, built by `extractor.py` | Fast startup, no runtime parsing. **Not committed** — see below |
| **feedback.jsonl** | Append-only retrieval feedback log | Enables future improvement |

### Data that lives outside the checkout

Two directories the server reads are deliberately **not** in this repository (session-268).
Both were previously stored beside `documents/`, which made one directory serve two
incompatible roles — product content and per-user runtime data.

| Directory | Default location | Setting | Why it is not in the repo |
|---|---|---|---|
| **Reference Library** | `~/.ai-governance/reference-library/` | `AI_GOVERNANCE_REFERENCE_LIBRARY_PATH` | **User data.** Written at runtime by `capture_reference` and accumulating one person's lessons across *all* their projects. Stored in-repo, a capture made while working in an unrelated project landed in this working tree — so the tree was never clean, and a dirty checkout blocks a concurrent session's fast-forward merge. Worse for adopters: their captures would land inside their clone of *this* repo, and their next `git pull` is refused (uncommitted index) or hits an unmergeable `.npy` conflict. |
| **Index** | `~/.ai-governance/index/` | `AI_GOVERNANCE_INDEX_PATH` | **Build artifact, and user-specific by construction** — it is embedded from `documents/` *plus* the reference library, so two people with this same checkout legitimately hold different indexes. Rebuild with `python -m ai_governance_mcp.extractor`. The public repo already treated it this way. |

A missing index is **loud**, not silent (`retrieval.py`): an empty principle set is
indistinguishable from "no principles apply", so the enforcement hook would record a
satisfied governance call over a server that retrieved nothing. That failure had to be
made visible before the index could stop being committed.

`documents/` stays in the repo — it *is* the product, identical for every user.

---

## Data Flow

**Build Time (offline, when docs change):**
```
documents/*.md  →  extractor.py  →  index/global_index.json
                                 →  index/content_embeddings.npy
                                 →  index/domain_embeddings.npy
```

**Runtime (every query):**
```
AI query  →  server/  →  retrieval.py  →  index (in memory)  →  results
```

**Index load (startup + auto-reload on `global_index.json` mtime change):** `retrieval.py:_load_index` validates before swapping the in-memory index, using temp-and-swap with a rollback guard so a bad index never displaces a working one:
1. **Model-label** — stored `embedding_model` vs configured.
2. **Row-count** — embedding rows == index item count.
3. **Dimension** — embedding width == declared dimensions.
4. **Embedding-space canary gate** (BACKLOG #58) — re-encode the index's stored `embedding_canaries` (text→vector probes written at build) via the *real query encoder* and require cosine ≥ `CANARY_COSINE_FLOOR` (0.95). This catches build/query embedder **divergence** that the label check cannot: a divergent index with the correct label passes label/shape/dtype but retrieves nothing (the silent BM25-only failure class). The build is force-local, so the committed index is always in the canonical embedding space.
5. **Rollback guard** — on any structural or canary failure, retain the previously-working index (cold-start with no prior index falls back to BM25-only). Every fallback logs loudly.

---

## File Structure

```
ai-governance-mcp/
├── src/
│   └── ai_governance_mcp/
│       ├── __init__.py
│       ├── server/             # MCP server package (16 tools)
│       │   ├── __init__.py    # Public API re-exports
│       │   ├── _app.py        # MCP setup, list_tools, call_tool, main
│       │   ├── _state.py      # Mutable globals, get_engine, get_metrics
│       │   ├── _logging.py    # Audit/reasoning logs, rotation
│       │   ├── _security.py   # Sanitization, rate limiting, instruction validation
│       │   ├── _constants.py  # Templates, metadata, keywords
│       │   └── handlers/      # Tool handler implementations
│       │       ├── retrieval.py   # query_governance, get_principle, list_domains, search_references
│       │       ├── governance.py  # evaluate_governance, verify_governance
│       │       ├── agents.py      # install/uninstall/list agents
│       │       ├── scaffold.py    # scaffold_project, capture_reference
│       │       └── analysis.py    # analyze_feedback_loop
│       ├── retrieval.py       # Hybrid search + index load-time validation (canary gate)
│       ├── extractor.py       # Doc parsing, index building
│       ├── models.py          # Pydantic schemas
│       ├── config.py          # Settings
│       ├── config_generator.py # Multi-platform MCP configs
│       └── validator.py       # Principle ID validation
│
│                              # NOTE: index/ and reference-library/ are NOT in the
│                              # repo — see "Data that lives outside the checkout" below.
│
├── documents/                 # Source markdown docs (Constitutional naming)
│   ├── constitution.md        # Meta-Principles (Articles I-V, Amendments)
│   ├── rules-of-procedure.md  # Meta-Methods (governance procedures)
│   ├── title-10-ai-coding.md  # Domain principles (Federal Statutes)
│   ├── title-10-ai-coding-cfr.md # Domain methods (Code of Federal Regs)
│   ├── title-15-ui-ux.md      # ... (one principles + one CFR file per titled domain;
│   ├── title-15-ui-ux-cfr.md  #      domains discovered from frontmatter at runtime — see `list_domains`)
│   ├── title-20-multi-agent.md
│   ├── title-20-multi-agent-cfr.md
│   ├── title-22-accounting.md
│   ├── title-22-accounting-cfr.md
│   ├── title-25-kmpd.md
│   ├── title-25-kmpd-cfr.md
│   ├── title-30-storytelling.md
│   ├── title-30-storytelling-cfr.md
│   ├── title-35-visual-communication.md
│   ├── title-35-visual-communication-cfr.md
│   ├── title-40-multimodal-rag.md
│   ├── title-40-multimodal-rag-cfr.md
│   ├── title-45-saas-ops.md
│   ├── title-45-saas-ops-cfr.md
│   └── domains.json           # Optional domain overrides (domains discovered from files)
│
├── logs/
│   ├── feedback.jsonl         # Retrieval feedback
│   ├── queries.jsonl          # Query audit log
│   ├── governance_audit.jsonl # Governance evaluation audit trail
│   └── governance_reasoning.jsonl # Per-principle reasoning traces
│
├── scripts/                           # Utility scripts
│
├── tests/
│   ├── conftest.py                    # Shared fixtures
│   ├── fixtures/                      # Test data files
│   ├── benchmarks/                    # Baseline metrics (MRR, Recall)
│   ├── test_models.py                 # Model validation
│   ├── test_config.py                 # Config + env vars
│   ├── test_server.py                 # Dispatcher, infrastructure, security
│   ├── test_server_retrieval.py       # Retrieval handler tests
│   ├── test_server_governance.py      # Governance handler tests
│   ├── test_server_agents.py          # Agent handler tests
│   ├── test_server_scaffold.py        # Scaffold handler tests
│   ├── test_server_integration.py     # Dispatcher routing, end-to-end flows
│   ├── test_extractor.py             # Parsing, embeddings, metadata
│   ├── test_extractor_integration.py  # Full pipeline, index persistence
│   ├── test_retrieval.py             # Hybrid search, reranking, edge cases
│   ├── test_retrieval_integration.py  # Pipeline, utilities, performance
│   ├── test_retrieval_quality.py     # MRR/Recall benchmarks
│   ├── test_config_generator.py      # Platform config generation
│   ├── test_validator.py             # Principle ID validation, fuzzy matching
│   ├── test_hooks.py                 # Hook enforcement tests
│   ├── test_enforcement.py          # Layer 3 enforcement proxy tests
│   ├── test_analyze_compliance.py    # Compliance analysis tests
│   ├── test_context_engine.py        # Full context engine coverage
│   ├── test_context_engine_quality.py # CE MRR/Recall benchmarks
│   ├── test_watcher_daemon.py        # Watcher daemon tests
│   ├── test_readonly.py              # Read-only mode tests
│   ├── test_reference_library.py     # Reference library tests
│   └── test_service.py               # Platform service installer tests
│
├── .claude/hooks/                     # Pre/post tool use hooks
│
├── staging/                    # Temporary AI input (always present)
├── .claude/skills/
│   ├── completion-sequence-aigov/ # Post-change steps (invoke via /completion-sequence-aigov)
│   ├── compliance-review/     # Periodic governance health (invoke via /compliance-review)
│   ├── test-authoring/        # Test creation protocol (invoke via /test-authoring)
│   └── verify-handoff/        # Handoff verification (invoke via /verify-handoff)
├── pyproject.toml
└── README.md
```

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate extractor** | Docs change rarely; don't parse at runtime |
| **In-memory index** | Fast queries (<100ms target); rebuild is cheap |
| **Retrieval isolated** | Can test/tune search without MCP complexity |
| **Pydantic models** | Validation, IDE support, clean serialization |
| **Append-only feedback** | Simple, no DB needed, enables future learning |
| **Dependency pinning** | Core deps exact-pinned for reproducibility; optional deps range-pinned for compatibility (see pyproject.toml) |

---

### Concurrent Session Isolation

Parallel Claude Code, Codex CLI, and Codex Desktop sessions share one Git
repository but must not share a writable checkout. The lifecycle separates two
planes:

| Plane | Isolated per mutating session | Still shared |
|-------|-------------------------------|--------------|
| **Git data plane** | Checkout, index, HEAD, topic branch (`wt/*`) | Object database, refs namespace, remote, integration branch |
| **Runtime plane** | Only resources explicitly namespaced by `.ai-worktree/setup.sh` | Ports, databases, daemons, caches, editable installs, user configuration, ignored files, symlink targets |

`global-skills/start-worktree/prepare.sh` is the host-adapter boundary. Claude
Code creates and enters a framework-owned tree; Codex Desktop adopts its native
per-chat tree; Codex CLI bootstraps from an ordinary shell when the managed
sandbox cannot write the repository's common Git directory. Framework creation
uses `git worktree add --lock --reason`: checkout creation and a parseable
host/branch/base/owner recovery record are one Git mutation, before the state
file can fail. Desktop writes its `attached` ownership state before `switch -c`.
Validation matches recorded host, path, branch, exact upstream, and owner. Git's
worktree lock remains a deletion guard and recovery record, not mutual exclusion.
Framework-owned trees get **no** separate claim artifact, deliberately. A
contested-claim protocol lived here through five reproduced defects across six
review rounds — an atomic claim directory, a recovery mutex, an age floor,
generation numbering — and it was removed rather than repaired a sixth time. Two
facts settled it. It could not enforce anything: nothing stops a human or a
process that never runs the script from editing the tree, so the record was
always advisory while it was being hardened to the standard of a lock it could
not be. And sharing is prevented upstream by construction: `claude-create`
generates a unique nonce, so every worker gets its own path and never contends.
The contested path only opens when someone points two sessions at one `--path` by
hand, which has never been observed outside a test harness.

What is left is advisory evidence read only to REFUSE, never to seize. The
lifecycle journal at `<gitdir>/ai-worktree-state` names the owner; the Git lock
reason corroborates it. A live different owner refuses, a proved-dead owner
permits the explicitly requested continuation, and anything unreadable,
malformed, conflicting, or ambiguous refuses and names what to inspect. Adding a
third ownership record alongside those two is what produced the
evidence-conflict problem in the first place, so no replacement was introduced.

The three-times-repeated failure is worth keeping even though its code is gone: a
rename-based steal took fresh live claims, an age floor evicted a marker whose
holder was still alive, and a pre-delete verification still left a check/use
window. Read-verify-delete is not compare-and-delete. The deeper lesson is the one
that ended the effort — prevent resource sharing through unique allocation before
building ownership detection on top of sharing you did not need.

The owner pid is the whole of identity, so a retry by the same session is granted
re-entrantly — and so are two concurrent workers sharing one parent pid, which
`procedure.md` produces via `--owner-pid "$PPID"` (measured: parallel tool calls
have distinct `$$` and identical `$PPID`). Sub-session isolation comes from giving
each writing worker its **own** worktree, which the generated nonce guarantees.

The lifecycle journal and Git lock are the two ownership evidence surfaces:
framework cleanup fails closed when they conflict or remain indeterminate. For
advisory hygiene, ownership is live/dead/unknown, and `repo_hygiene.py` offers a
destructive removal command only for a proved-dead, clean worktree; unknown
evidence stays visible but non-destructive.

Framework-created checkouts write a strict ordered v2 journal with host,
lifecycle owner, path, branch, base, default, owner PID, session, task key,
parallel-intent bit, state, and timestamp. An `ai-worktree-v2` Git lock carries
the same task and parallel intent; `ai-worktree-v1` remains legacy evidence.
Consumers reject unknown, missing, duplicate, reordered, malformed,
control-character-bearing, or Git-incoherent fields. V1 and unjournaled
worktrees remain readable only through conservative compatibility paths; they
cannot use the live-owner finalization exception.

The recorded owner can request atomic finalization by supplying its matching PID.
This is cooperative acknowledgement, not authentication: a readable PID is not a
credential. It waives only the liveness veto inside one cleanup operation after
the v2 journal, Git lock, durability, completeness, tracked cleanliness and
sensitive-ignored-file checks agree. No persistent `released` state exists. A
pre-removal failure leaves or restores `ready` plus the lock; a teardown/removal
failure restores the lock and reports that runtime teardown may already have
run; a branch-deletion failure after successful removal leaves the branch as the
recovery handle.

Unique nonces prevent shared checkout paths, while task keys detect duplicate
intent across those isolated paths. Sequential duplicate keys refuse. An
explicit parallel override is recorded rather than hidden. A simultaneous
creation race is detected by a post-create scan: the loser becomes locked,
non-ready `task-conflict` and must either continue with explicit parallel intent
or be abandoned by its recorded owner. This is detection, not a global mutex.
`all-clear` and `repo_hygiene.py` report duplicate active keys and ambiguous
legacy same-slug candidates without auto-removal.

Close-out is optimistic rather than globally serialized.
`global-skills/completion-sequence/integrate.sh` refreshes from an explicit live
`origin/<default>` before final shared-memory authorship, then fetches again and
publishes only when `HEAD` still fast-forwards the live default. A rejected race
returns a distinct retry result; force-push is never the recovery path.
Cleanup fetches and prunes every configured remote before using tracking refs as
durability evidence, so a remote rewrite or branch deletion cannot be hidden by
stale local refs. Desktop dry-run never executes teardown.

The host permission boundary is independent of skill loading. In a linked
worktree, staging/index and ref mutations target the common Git directory, so a
sandbox can permit checkout edits and tests while denying `fetch`, `add`,
`commit`, integration, and cleanup. Those operations must run in an environment
with explicit common-directory write authority.

---

## Governance Enforcement Architecture

Three-layer enforcement stack ensuring governance compliance:

```
AI CLIENT (Claude Code, Cursor, Gemini CLI, etc.)
    │
    │         ┌─────────────────────────────────────────────────────┐
    │ Layer 2 │ Claude Code hooks (.claude/hooks/) — Claude only    │
    │         │ PreToolUse: blocks Bash|Edit|Write without gov call │
    │         └─────────────────────────────────────────────────────┘
    │
    ├── ai-governance-mcp (via proxy) ◄── Layer 3 Phase 1
    │       │
    │       ▼
    │   ┌─────────────────────────────────────────────────────────┐
    │   │ ENFORCEMENT PROXY (enforcement.py)                      │
    │   │ Intercepts JSON-RPC tools/call at stdio protocol level  │
    │   │ Hard mode blocks / soft mode warns on action tools that │
    │   │ lack a prior evaluate_governance() call (model-order     │
    │   │ gate, not human approval). ANY client — Cursor, etc.    │
    │   │ Writes shared state on governance calls ──────────┐     │
    │   └───────────────┬───────────────────────────────────│─────┘
    │                   ▼                                   │
    │   ┌─────────────────────────────────────────────────────────┐
    │   │ GOVERNANCE MCP SERVER (server/) — Layer 1 (advisory)    │
    │   │ SERVER_INSTRUCTIONS + GOVERNANCE_REMINDER per response   │
    │   │ evaluate_governance(): principle retrieval + assessment  │
    │   └─────────────────────────────────────────────────────────┘
    │                                                       │
    │                                  shared state file ◄──┘
    │                              (~/.ai-governance/enforcement-state.json)
    │                                         │
    ├── github MCP (via proxy --govern-all) ◄─┤ Layer 3 Phase 2
    ├── filesystem MCP (via proxy --config) ◄─┤ reads shared state
    └── other MCP servers (via proxy)       ◄─┘
```

| Layer | Mechanism | What it enforces | Coverage |
|-------|-----------|-----------------|----------|
| **1: Advisory** | SERVER_INSTRUCTIONS + GOVERNANCE_REMINDER | Asks AI to call evaluate_governance() | All clients (~13% compliance) |
| **2: Hooks** | PreToolUse transcript scanning (.claude/hooks/) | Blocks Bash/Edit/Write without governance | Claude Code (~100%); Codex CLI also runs an act-intrinsic content-security PreToolUse hook (`ai_governance_mcp.codex_hooks`) — verified 2026-07-03, both interactive + `codex exec` (title-10 N.5) |
| **3: Proxy (Phase 1)** | stdio JSON-RPC interceptor (enforcement.py) | Governance-call-before-action on the governance server's tools | All clients — hard blocks / soft warns; model-satisfiable, not a human gate |
| **3: Proxy (Phase 2)** | Same proxy wrapping third-party servers | Governance-call-before-action on any MCP server's tools | All clients — hard blocks / soft warns; model-satisfiable, not a human gate |

> **What the proxy is and isn't.** It gates the *model's call order* (call `evaluate_governance()` before an action tool) — hard mode blocks, soft mode (used by most generated configs) only warns. It is **model-satisfiable** (the model can call governance itself) and is **not** a human approval gate. On GUI auto-run hosts (Claude Desktop) a soft warning is post-hoc, so the host's own per-tool approval prompt is the real human gate. See ``ref-ai-coding-connect-local-mcp-server-to-claude-surfaces` (via `search_references`)`.

**Phase 1 — Self-enforcement:** Any AI client connecting to the governance server through the proxy must call `evaluate_governance()` before using action tools (`scaffold_project`, `capture_reference`, `install_agent`, `uninstall_agent`, `log_feedback`, `log_governance_reasoning`). This works regardless of which AI model or IDE is used.

**Phase 2 — Cross-MCP enforcement:** The same proxy wraps third-party MCP servers (GitHub, filesystem, etc.) to enforce governance before their state-modifying tools. Uses a shared state file for cross-process coordination — the governance proxy writes timestamps when `evaluate_governance()` is called, and cross-MCP proxy instances read them. See `examples/github-governance.yaml` for config format.

```bash
# Phase 2 usage:
ai-governance-proxy --govern-all \
    --always-allow "get_file_contents,list_issues,search_code" \
    -- npx @modelcontextprotocol/server-github
```

**Entry points:**
- Direct: `ai-governance-mcp` (server only, Layer 1)
- Enforced: `ai-governance-proxy` (proxy + server, Layers 1+3)
- Cross-MCP: `ai-governance-proxy --govern-all -- <server-cmd>` (Phase 2)
- Claude Code: hooks provide Layer 2 regardless of entry point

> **GUI-host configs:** the console-script names above (`ai-governance-proxy`, bare `python`) resolve only where the venv `bin`/`Scripts` dir is on PATH — i.e. an interactive shell. A GUI MCP host (Claude Desktop, etc.) launches with a minimal PATH and would `spawn ENOENT`. For those, generate the config with `python -m ai_governance_mcp.config_generator --json claude [--enforce]`, which emits an absolute `sys.executable -m …` form.

**Configuration:** `GOVERNANCE_ENFORCEMENT_ENABLED`, `GOVERNANCE_ENFORCEMENT_SOFT_MODE`, `GOVERNANCE_RECENCY_WINDOW`, `GOVERNANCE_STATE_FILE`, `GOVERNANCE_STATE_TTL`

### Hook Operational Notes

**Content-security hook (Layer 2):** `pre-tool-content-security.sh` blocks Bash commands accessing machine-level credential paths (`~/.ssh/*`, `~/.aws/*`, `~/.gnupg/*`, `~/.netrc`, `~/.docker/config.json`, `~/.kube/config`, `~/.npmrc`, `/etc/ssl/private/*`, `*.key`). Layer 1 (Read deny rules in user settings) covers the Read tool. Bypass: `CONTENT_SECURITY_SKIP=1`. Origin: BACKLOG #19.

**Cloud/CCR auto-degrade:** `pre-tool-governance-check.sh` auto-degrades each gate (governance / CE) to advisory when that MCP server is not configured in any session config surface (`.mcp.json`, `~/.claude.json`, `.claude/settings*.json`) — a session that cannot call the gated tools cannot satisfy a fail-closed gate (cloud routines, CCR clones, fresh checkouts would deadlock). The degrade is audit-logged (`soft-mode-auto`) and announced in the injected reminder. `MCP_DETECT_SKIP=true` restores strict fail-closed. Origin: session-211.

**Subagent transcript isolation (T-152):** When subagents call `evaluate_governance` and `query_project`, those calls are recorded in the subagent's transcript, not the parent's. The governance hook scans only the parent transcript, so subagent compliance is invisible to enforcement. A read-only Bash command allowlist (`git log`, `ls`, `grep`, etc.) lets read-only subagents (contrarian-reviewer, security-auditor) bypass governance enforcement for provably safe commands. Mutation subagents (test-generator, documentation-writer) remain blocked until Claude Code adds agent context to hook input. Disable the allowlist with `READONLY_BASH_SKIP=true`.

---

## Security Architecture

| Aspect | Approach | Rationale |
|--------|----------|-----------|
| **Authentication** | None (v1) | Local use; future phase adds auth |
| **Data access** | Read-only from index; `scaffold_project` and `capture_reference` write to project directory | Source docs read-only; project scaffolding writes to caller's CWD |
| **Feedback logging** | Append-only, local file, mode 0600 | **Stores free-text user content** — `feedback.jsonl` carries the `query` field verbatim (measured: up to 549 chars), and `governance_reasoning.jsonl` / `governance_audit.jsonl` carry `planned_action` and `context`. Not redacted. Acceptable for a single-operator local install on the same disk as the source it describes; **state this rather than claiming otherwise** (`meta-safety-transparent-limitations`). Corrected session-266 — the row previously read "No sensitive data stored", which was false. |
| **Network exposure** | Local stdio only (MCP) | No HTTP server in v1 |
| **Dependencies** | Verified packages only | Per spec §11 |

**Future phase** (multi-user): Add authentication layer, user isolation. Rate limiting is implemented (token bucket algorithm).

---

## Integration Points

| Integration | Protocol | Notes |
|-------------|----------|-------|
| AI Clients (Claude, etc.) | MCP (JSON-RPC over stdio) | Standard MCP interface |
| Source Documents | File system read | Markdown files in documents/ |
| Index | File system read | JSON + NumPy at startup |
| Feedback Log | File system append | JSONL format |

---

## Test Architecture

| Category | Files | Purpose |
|----------|-------|---------|
| **Unit** | test_models, test_config, test_validator | Isolated component validation |
| **Server** | test_server, test_server_integration | All 16 governance MCP tools, dispatcher routing |
| **Extractor** | test_extractor, test_extractor_integration | Parsing, embeddings, index build |
| **Retrieval** | test_retrieval, test_retrieval_integration | Hybrid search, reranking, pipeline |
| **Quality** | test_retrieval_quality | MRR/Recall benchmarks |
| **Config** | test_config_generator | Multi-platform MCP configurations |
| **Hooks** | test_hooks | Hook enforcement validation |
| **Compliance** | test_analyze_compliance | Compliance analysis |
| **Context Engine** | test_context_engine | Full context engine coverage |
| **CE Quality** | test_context_engine_quality | CE MRR/Recall benchmarks |
| **Resilience** | test_deleted_cwd_resilience, test_no_unguarded_cwd | A process outliving its working directory: the contract that a failed durable telemetry write never discards a computed verdict, plus the assertion that `safe_cwd()` stays the only cwd read. Drives the real condition (deletes a temp cwd out from under the process) rather than mocking it |

### Test Markers (pyproject.toml)

| Marker | Purpose |
|--------|---------|
| `@pytest.mark.slow` | Tests requiring actual ML models (~30s each) |
| `@pytest.mark.integration` | End-to-end pipeline tests |
| `@pytest.mark.real_index` | Tests using production index data |
| `@pytest.mark.model_eval` | Model evaluation benchmarks |

### Mocking Strategy

ML models (SentenceTransformer, CrossEncoder) are mocked via `conftest.py` fixtures:
- Patch at `sentence_transformers.*` level (lazy-loaded imports)
- Mock returns numpy arrays with correct shapes via `side_effect`
- Fixed random seed for reproducible tests

### Known Test Boundaries

Deliberately uncovered areas (run `pytest --cov` for current percentages):
- server/_app.py: `async run_server()` — entry point, tested via integration
- extractor.py: CLI `main()` — invoked manually
- retrieval.py: Rare filesystem error paths

---

## Dependencies

| Package | Purpose |
|---------|---------|
| mcp | MCP Python SDK (`mcp.server.Server`) |
| pydantic / pydantic-settings | Data models + configuration |
| sentence-transformers | Embeddings + reranking |
| rank-bm25 | BM25 keyword search |
| numpy | Vector operations |
| requests | HTTP (required by sentence-transformers) |
| pytest / ruff | Testing + linting (dev) |

See `pyproject.toml` for pinned versions.

---

## Context Engineering Strategy

How the project's memory files implement the cognitive memory architecture (title-10-ai-coding-cfr §7.0).

### Memory Types and Loading

| Cognitive Type | File | Loaded When | Content |
|----------------|------|-------------|---------|
| **Working** | `_ai-context/SESSION-STATE.md` | Always at session start | Current position, active task, blockers, next actions |
| **Semantic** | `_ai-context/PROJECT-MEMORY.md` | Always at session start | Decisions, constraints, gotchas, patterns |
| **Episodic** | `_ai-context/LEARNING-LOG.md` | Always at session start | Lessons learned, active and graduated |
| **Prospective** (one-shot) | `_ai-context/BACKLOG.md` | On demand (deferred work) | Intentions to act, deferred capabilities, future work |
| **Prospective** (recurring) | `_ai-context/OPERATIONS.md` | Session start (cadence surfacer) | Cadences, tripwires, standing authorizations, metrics, verification items |
| **Procedural** | Methods documents in `documents/` | Via MCP retrieval | How to do things (governance, coding, multi-agent) |
| **Reference** | Context Engine index | Via MCP query | Project content, semantically searchable |
| **Structural** | `ARCHITECTURE.md` (this file) | On demand (design questions) | System design, components, data flow |
| **Charter** | `README.md` | On demand (scope questions) | Project purpose, public contract, scope boundaries |

*Canonical source: CFR Part 7. "Structural" and "Charter" are organizational shortcuts rather than cognitive types (CFR §7.5.5 states this); the other six are the taxonomy. **Corrected 2026-08-16 (twice):** the Operational row pointed at `.claude/skills/compliance-review/` — the *procedure* — while `OPERATIONS.md`, the registry, appeared nowhere in this file at all (`grep -c OPERATIONS` returned 0). Paths were also pre-`_ai-context/` migration. The first correction then filed `OPERATIONS.md` under a NEW seventh type, "Operational Memory"; that type was superseded the same day and both files are Prospective, split by lifecycle — see CFR §7.0.2. Derived/generated status (`STATUS.md`) is a sibling category outside this table: memory is what you cannot recompute.*

### Loading Sequence

```
Session Start:
  1. CLAUDE.md (auto-loaded by Claude Code → points to memory files)
  2. SESSION-STATE.md (where are we? what's next?)
  3. PROJECT-MEMORY.md (what constraints apply?)
  4. LEARNING-LOG.md (what mistakes to avoid?)
  5. OPERATIONS.md (what is due, and has any tripwire fired?)
       — surfaced automatically by .claude/hooks/session-start-cadence.sh, but
         listed here because the hook is Claude-Code-only; every other host
         reads this sequence instead.

On Demand:
  6. ARCHITECTURE.md (how does the system work?)
  7. README.md (does this feature fit the project scope?)
  8. query_governance() / get_principle() (what do the methods say?)
  8. query_project() (what code/content exists where?)
  9. /compliance-review skill (is the governance system healthy?)
 10. BACKLOG.md (what's deferred? what needs discussion?)
```

### Memory Consistency Rules

- **Single Source of Truth**: Each fact has exactly one canonical location. Don't duplicate across files.
- **Platform memory is hands-off**: LLM platform memory (e.g., Claude Code's `~/.claude/.../MEMORY.md`) is the platform's concern, not ours. Framework files are authoritative. CLAUDE.md is the bridge. See Appendix G.5 in rules-of-procedure.
- **Lifecycle alignment**: Working memory is overwritten each session. Semantic memory accumulates. Episodic memory prunes when lessons graduate to methods.
- **Distillation triggers**: SESSION-STATE >300 lines, PROJECT-MEMORY >800 lines, LEARNING-LOG ~200 lines trigger review (not hard ceilings).

---

## Failure Mode Mapping

Known failure modes for the multi-agent and orchestration patterns used in this project (title-20-multi-agent-cfr §3.3).

### Orchestrator Failure Modes

| Failure Mode | Cause | Detection | Mitigation |
|--------------|-------|-----------|------------|
| **Governance bypass** | Orchestrator skip-list too broad; action not evaluated | `verify_governance_compliance()` returns NON_COMPLIANT | Narrow skip-list; default to evaluate when in doubt |
| **False ESCALATE** | S-Series keyword scan triggers on benign terms (e.g., "security fix") | Review `principles` array in assessment — keywords triggered but no real violation | CRITICAL/ADVISORY tiering filters most cases; sentence-level safe-context allowlist (per FM-S-SERIES-KEYWORD-FALSE-POSITIVE re-registered 2026-05-01) demotes a keyword when every sentence containing it has a safe-context leader — including negation forms (not/never/cannot + the n't contraction) — and no danger verb threatens it. Two danger tiers: a MUTATION verb anywhere in the action blocks demotion field-wide (catches "delete the prod DB; credentials not affected"); an EGRESS/disclosure verb (send/email/publish/exfiltrate/…) blocks only when co-located in the keyword's sentence (closes "not destructive, send the credential" without re-flagging "publish the notes; no credentials"). The same predicate also suppresses ADVISORY-keyword warnings in safe context (zero veto impact — advisory never escalates alone). Residual (lexical limit) + Path B (semantic retrieval FP for housekeeping actions) tracked separately (BACKLOG #73). **Honest labeling (2026-07-04):** a keyword-only trigger (a CRITICAL keyword matched but no S-Series principle was retrieved) is labeled in the rationale as a heuristic match, NOT a principle veto. **Keyword-only adjudication (#73, 2026-07-05, `keyword_judge_mode`):** a keyword-only trigger is now routed through a two-layer decision — Layer 0, a deterministic sentence-scoped insecure-persistence floor (store/save/hardcode/persist/plaintext co-located with a CRITICAL keyword → ESCALATE, judge never consulted); Layer 1, a fresh-context keyless-Codex judge (benign→REVIEW / genuine→ESCALATE); Layer 2 fail-safe (judge missing/timeout/unparseable → ESCALATE = today's behavior). Mode: `off` (skip), `shadow` (run + record `keyword_adjudication`, routing unchanged), `active` (route on the verdict — **the default since Stage-2 flip, session-258**; gate: `scripts/eval_keyword_adjudicator.py` **passed 2026-07-05** — 13/13 recall, 8/8 precision, 0/3 adversarial; `logs/keyword_adjudicator_eval_2026-07-05.md`). The semantic S-Series veto and `act_intrinsic_block` are never adjudicated (the judge only ever downgrades the weakest keyword-only class). **Advisory-host residual (honest):** a judged-`benign` keyword-only trigger routes to REVIEW ("read and proceed"), removing the security-specific STOP. On advisory hosts (Desktop, no blocking hook) the act-intrinsic gate does NOT backstop this — it matches literal secret *values/paths*, while the adjudicated class is *descriptions* ("store the password in plaintext") carrying no literal value — so the only residual human gate there is the host's generic per-tool approval prompt. Path B (semantic retrieval FP for housekeeping actions) remains open (BACKLOG #73). |
| **Verdict discarded by a failed side effect** | A non-essential side effect sat on the tool's critical return path: the audit-log write ran *after* the assessment was built, and any exception from it propagated out of the handler, so the dispatcher converted a finished verdict into `TOOL_ERROR`. Observed live — a session deleted the worktree its own server was launched in, `Path.cwd()` raised for the process lifetime, and every `evaluate_governance` call answered `[Errno 2]` for a whole session. | `verify_governance_compliance()` reports `durable_telemetry_gaps` (non-empty = the in-memory trail is intact but `logs/*.jsonl` has holes). A single WARNING per failure kind per process. Silence is the healthy state. | **Ordering rule:** commit the authoritative verdict *and the in-memory enforcement state* first; durable persistence is best-effort after it — `_logging._guarded_write{,_async}` absorb `OSError` and `LogPathOutOfScope` and count them in `_telemetry_failures`. Configuration and security invariants move earlier instead: a traversal sequence in a configured write path fails at `Settings` construction, and `LogPathTraversal` stays fatal (attack signal) while `LogPathOutOfScope` is absorbed (environment fact). Note the distinction that makes this precise — the in-memory audit append is *enforcement state*, not optional telemetry; only disk durability degrades. `FM-VERDICT-DISCARDED-BY-FAILED-SIDE-EFFECT`. |
| **Unguarded working-directory read** | A process outlives its working directory. Once that directory is unlinked (`ExitWorktree`, `git worktree remove`, `rm -rf` elsewhere), `Path.cwd()`/`os.getcwd()` raise `FileNotFoundError` for the rest of the process's life. Third occurrence of this class. | `tests/test_no_unguarded_cwd.py` asserts exactly one raw cwd read exists in `src/`, with an **empty** exemption list. `tests/test_deleted_cwd_resilience.py` drives the real condition (deletes a temp cwd out from under the process). | Single guarded accessor: `path_resolution.safe_cwd() -> Path | None`. Callers must fail safe — a *scope* check drops cwd from its allowed set (stricter, never wider); a *write* path with no destination refuses rather than guessing. Rejected the CI grep the earlier lesson prescribed (~53% false positives; this repo has recorded FP gates training `QUALITY_GATE_SKIP`, which also disables the secret scanner). **Known blind spot:** implicit reads (`Path("rel").resolve()`, child processes inheriting the dead cwd) carry no matchable token — BACKLOG #291. `FM-UNGUARDED-CWD-READ`. |
| **Stale index** | Server caches index at startup; index rebuilt but server not restarted | Queries return outdated or missing results | Auto-reload: server checks index mtime on each query and reloads when changed. No restart needed. |
| **Context overflow** | Long conversation exceeds context window; governance instructions lost | AI stops calling `evaluate_governance()`; responses drift from framework | Per-response reminder (~30 tokens) appended to every tool response |

### Subagent Failure Modes

| Failure Mode | Cause | Detection | Mitigation |
|--------------|-------|-----------|------------|
| **Token limit exceeded** | Subagent task too broad; output exceeds max_turns | Agent returns truncated or incomplete results | Scope tasks narrowly; set appropriate max_turns |
| **Tool unavailability** | Subagent type doesn't have required tool (e.g., documentation-writer can't run Bash) | Tool call rejected | Check agent tool list before delegating; use general-purpose if mixed tools needed |
| **Context loss** | Custom agent files (.claude/agents/) are reference docs, not auto-loaded | Agent doesn't follow role instructions | Inline role instructions in Task prompt; or read agent file first (LEARNING-LOG lesson) |
| **Stale delegation** | Orchestrator delegates based on outdated understanding of codebase | Subagent produces incorrect output | Load SESSION-STATE before delegating; include current context in handoff |

### Circuit Breaker Scenarios

| Scenario | Trigger | Recovery |
|----------|---------|----------|
| **Repeated validation failure** | Same gate fails 3+ times | Escalate to user — indicates systemic issue |
| **Index corruption** | `global_index.json` malformed or embeddings shape mismatch | Re-run `python -m ai_governance_mcp.extractor` from source docs |
| **Feedback loop** | `log_feedback()` boosts irrelevant principles, degrading future retrieval | Review feedback.jsonl; remove erroneous entries; rebalance boost/penalty weights |
| **Memory file bloat** | SESSION-STATE >300 lines, causing slow context loading | Apply distillation triggers (§7.0.4); prune completed work |

---

## Proof-of-Concept Results

Key technical decisions validated through prototyping and benchmarking (title-10-ai-coding-cfr §3.1.4).

### Embedding Model Selection

| Model | Token Limit | MRR (Methods) | Decision |
|-------|-------------|---------------|----------|
| `all-MiniLM-L6-v2` | 256 | 0.330 | **Rejected** — key content truncated beyond 256 tokens |
| `BAAI/bge-small-en-v1.5` | 512 | 0.698 | **Selected** — +112% MRR improvement |

**Why BGE won:** Method chunks frequently exceed 256 tokens. MiniLM truncated critical content (purpose, applies_to fields) that appeared after the token limit. BGE's 512-token window captures the full chunk content needed for accurate semantic matching. Both models produce 384-dimension embeddings, so the switch required no infrastructure changes.

### Retrieval Quality Benchmarks

Current metrics (see `tests/benchmarks/` for latest baseline, model: `BAAI/bge-small-en-v1.5`):

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Method MRR | 0.694 | >= 0.60 | Pass |
| Principle MRR | 0.688 | >= 0.50 | Pass |
| Method Recall@10 | 0.833 | >= 0.75 | Pass |
| Principle Recall@10 | 0.875 | >= 0.85 | Pass |

**Methodology:** 13 principle + 12 method benchmark queries covering 4 of 10 domains (constitution, ai-coding, multi-agent, accounting). Each query has expected top results. MRR measures average reciprocal rank of first correct result. Recall@10 measures whether the correct result appears in top 10. Canonical source: `tests/benchmarks/`.

### Hybrid Search Validation

| Approach | Miss Rate | Notes |
|----------|-----------|-------|
| BM25 only | ~5% | Misses semantic synonyms |
| Semantic only | ~3% | Misses exact terminology |
| Hybrid (60/40) | <1% | Complementary strengths |

The 60% semantic / 40% keyword weight was determined empirically. Semantic search handles paraphrased queries ("how to handle incomplete specs" → specification-completeness). BM25 handles exact matches ("S-Series" → safety principles). Combined, they achieve <1% miss rate.

### Latency Profile

| Operation | Typical | Target | Notes |
|-----------|---------|--------|-------|
| Model load (first query) | ~9s | <=15s | One-time cost at startup |
| Subsequent queries | ~50ms | <100ms | In-memory search + reranking |
| Index rebuild | ~30s | N/A | Offline operation |

### Storage Architecture Decision

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| In-memory (NumPy) | Fast queries, simple | Full reload at startup | **Selected** for v1 |
| Vector DB (e.g., ChromaDB) | Incremental updates, scalability | Additional dependency, deployment complexity | Deferred to roadmap |

**Rationale:** At the current scale (roughly a thousand indexed items, single-digit MB of embeddings — see the `STATUS.md` generated count block for the live number), in-memory storage provides <100ms query latency with minimal complexity. Vector DB migration is designed-for but deferred until scale requires it.

---

## Context Engine MCP Server

A second MCP server providing semantic search across project content. Complements the governance MCP server (principles/methods) with project-specific content awareness.

### System Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTEXT ENGINE MCP                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   server    │───→│  project    │───→│   indexer   │                     │
│  │             │    │  manager    │    │             │                     │
│  │ 7 MCP tools │    │             │    │ Embedding   │                     │
│  │ Validation  │    │ Multi-proj  │    │ BM25 build  │                     │
│  │ Rate limit  │    │ Hybrid QRY  │    │ Connectors  │                     │
│  │ Sanitize    │    │ RLock sync  │    │             │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                            │                  │                             │
│                            ▼                  ▼                             │
│                     ┌─────────────┐    ┌─────────────┐                     │
│                     │   watcher   │    │ connectors  │                     │
│                     │             │    │             │                     │
│                     │ watchdog    │    │ code        │                     │
│                     │ debounce 2s │    │ document    │                     │
│                     │ cooldown 5s │    │ PDF         │                     │
│                     │ circuit brk │    │ spreadsheet │                     │
│                     └─────────────┘    │ image       │                     │
│                            │           └─────────────┘                     │
│                            ▼                                               │
│                     ┌─────────────┐                                         │
│                     │  storage    │  (~/.context-engine/indexes/{id}/)      │
│                     │             │                                         │
│                     │ filesystem  │  content_embeddings.npy,               │
│                     │ JSON-based  │  bm25_index.json, metadata.json,       │
│                     │             │  chunks.json, file_manifest.json       │
│                     └─────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | What It Does | Why Separate |
|-----------|--------------|--------------|
| **server.py** | 7 MCP tools, input validation, rate limiting, error sanitization | Entry point, security boundary |
| **project_manager.py** | Multi-project lifecycle, hybrid search (semantic + BM25), score fusion, cross-encoder reranking, MMR diversity, per-file dedup | Core query logic, thread-safe |
| **indexer.py** | File discovery, connector orchestration, embedding generation, BM25 build | Indexing pipeline, heavy compute |
| **watcher.py** | File system monitoring, debounced change callbacks (2s), post-index cooldown (5s), circuit breaker (3 failures) | Real-time updates, decoupled |
| **connectors/** | Content-type-specific parsing (code, doc, PDF, spreadsheet, image) | Pluggable, independently testable |
| **storage/** | Index persistence (filesystem-backed, JSON + NumPy) | Swappable backends |
| **models.py** | Pydantic schemas (ContentChunk, ProjectIndex, QueryResult, etc.) | Type safety, validation |

### Data Flow

**Index Time (per project):**
```
project files  →  indexer._discover_files()  →  connectors.parse()  →  ContentChunks
                                                                            │
                   storage.save_*()  ←  BM25 index + embeddings  ←─────────┘
```

**Query Time (per request):**
```
AI query  →  server.py (validate)  →  project_manager.query_project()
                                            │
                 ┌──────────────────────────┤
                 ▼                          ▼
          semantic_search()          bm25_search()
          (cosine similarity)        (keyword matching)
                 │                          │
                 └──────────┬───────────────┘
                            ▼
                     _fuse_scores()  (linear or RRF fusion + metadata bonuses)
                            ▼
                     _rerank_results()  (cross-encoder via IPC, graceful fallback)
                            ▼
                     _apply_mmr()  (adaptive diversity, threshold 0.85)
                            ▼
                     _deduplicate_per_file()  →  ranked QueryResult[]
```

**Real-time Update (file watcher — opt-in via `AI_CONTEXT_ENGINE_INDEX_MODE=realtime`):**
```
file change  →  watchdog event  →  debounce (2s)  →  incremental_update()
                                                              │
                                                     reuse unchanged embeddings
                                                     generate only for changed files
                                                              │
                                                     reload search indexes
                                                              │
                                                     cooldown (5s) before next re-index
```

**Self-Restart Lifecycle (Phase 0 — plan jiggly-honking-cascade.md):**
```
daemon start  →  heartbeat loop (60s ticks)  →  uptime check each tick
                                                        │
               ┌────────── elapsed < target ────────────┤ → continue (no-op)
               │                                        │
               │   elapsed ≥ target AND idle ≥ 5min  ──→ stop_event.set()  →  clean exit (0)
               │                                        │
               │   elapsed ≥ target × 1.5 (hard cap) ──→ stop_event.set()  →  clean exit (0)
               │                                        │
               └────────────────────────────────────────┘
                                                        │
         launchd KeepAlive=true  →  respawn (ThrottleInterval 30s)  →  fresh process
```

The self-restart mechanism flushes the PyTorch CPU allocator cache, which accumulates monotonically in long-running processes (sentence-transformers issues #1795, #487). Default: 12h target with ±10% jitter, 1h floor, 5-min idle gate / 1.5× hard cap. During the ~30s respawn window, file changes are not watched but are caught on next heartbeat via mtime replay. File deletions during the window are not recovered until the next full reindex — a documented accepted trade-off.

### Security Features

| Feature | Implementation | Location |
|---------|---------------|----------|
| **Input validation** | Type checks, length limits, bounds clamping | server.py |
| **Rate limiting** | Token bucket (5 req/min) for index_project | server.py |
| **Error sanitization** | Strip paths, line numbers, memory addresses, module paths | server.py |
| **Path traversal prevention** | Hex-only project IDs, resolve + is_relative_to containment | storage/filesystem.py |
| **Pickle deserialization** | allow_pickle=False on all np.load calls | storage/filesystem.py |
| **JSON serialization** | BM25 index stored as JSON, not pickle | storage/filesystem.py |
| **Symlink filtering** | Skip symlinks during file discovery, list_projects, delete_project | indexer.py, storage/filesystem.py |
| **File size limits** | 10MB max per file during indexing | indexer.py |
| **File count limits** | 10,000 max files per project | indexer.py |
| **Thread safety** | RLock protecting shared index state; Lock guarding rate limiters (both servers) | project_manager.py, server.py |
| **Decompression bomb guard** | PIL MAX_IMAGE_PIXELS limit set at connector init | connectors/image.py |
| **Relative paths in output** | source_path computed relative to project root, not absolute | connectors/*.py |
| **Log sanitization** | Truncate content before logging | server.py |
| **Env var robustness** | try/except with fallback defaults for all env config | server.py |
| **.env* filtering** | .env and all variants (.env.local, etc.) excluded by default | indexer.py |
| **Atomic writes** | JSON: tmp + fsync + rename. NumPy: tmp + rename. Orphaned .tmp cleanup on init | storage/filesystem.py |
| **Corrupt file recovery** | All load methods: try/except → log warning → delete corrupt file → return None | storage/filesystem.py |
| **BM25 empty corpus guard** | Check `any(len(doc) > 0 for doc in corpus)` before BM25Okapi construction | project_manager.py |
| **Column/row limits** | CSV/Excel: 500 columns max, 11 rows max (header + 10 sample) | connectors/spreadsheet.py |
| **Chunk force-splitting** | Markdown and plain text force-split at 200 lines | connectors/document.py |
| **Timer lifecycle** | Daemon threads for debounce/cooldown timers, cancel on stop(), running guard | watcher.py |
| **Circuit breaker** | 3 consecutive watcher failures stops watcher, marks project circuit_broken | project_manager.py |
| **LRU eviction** | Max 10 loaded projects, least-recently-used evicted | project_manager.py |
| **JSON file size limits** | 100MB max for BM25 index, metadata, file manifest files | storage/filesystem.py |
| **Watcher debounce + cooldown** | 2s debounce batches rapid changes; 5s cooldown prevents re-index storms | watcher.py |
| **Watcher force-flush** | 10,000 pending changes triggers immediate flush (prevents unbounded memory) | watcher.py |
| **Watcher change re-queue** | Failed callback changes re-added to pending set for retry | watcher.py |
| **Daemon timer threads** | All Timer threads marked daemon (prevents blocking process exit) | watcher.py |
| **Corrupt metadata recovery** | Pydantic validation failure → fallback to minimal empty ProjectIndex | project_manager.py |
| **Orphan tmp cleanup** | On startup, removes .tmp files left by crashed atomic writes | storage/filesystem.py |
| **Embedding model mismatch** | Warn on load if stored model differs from configured model (label only — cannot see same-label divergence) | project_manager.py |
| **Embedding-space canary gate** | At load, re-encode ≤3 build-time (text, vector) probes via the live query encoder; cosine < 0.95 or error → discard embeddings, BM25-only (BACKLOG #59, port of governance #58; unlike #58 no force-local build — the CE index is machine-local, so the invariant is build==query self-consistency) | project_manager.py / indexer.py |
| **Embedding model allowlist** | 8 vetted models; custom requires `AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true` | indexer.py |
| **Chunk limits** | MAX_TOTAL_CHUNKS (100K), MAX_CHUNK_CONTENT_CHARS (10K), EMBEDDING_BATCH_SIZE (1K) | indexer.py |
| **Cosine similarity clamping** | `np.clip(..., 0.0, 1.0)` prevents float32 overflow past Pydantic bounds | project_manager.py |

### Context Engine File Structure

```
src/ai_governance_mcp/context_engine/
├── __init__.py
├── server.py            # MCP server (7 tools, validation, rate limiting)
├── project_manager.py   # Multi-project management, hybrid query
├── indexer.py           # Core indexing pipeline
├── watcher.py           # File system watcher (watchdog)
├── watcher_daemon.py    # Standalone watcher daemon (CLI)
├── service.py           # Platform service installer (launchd/systemd/schtasks)
├── models.py            # Pydantic data models
├── connectors/
│   ├── __init__.py
│   ├── base.py          # BaseConnector interface
│   ├── code.py          # Code parsing (keyword-based, tree-sitter prepared)
│   ├── document.py      # Markdown/text parsing
│   ├── pdf.py           # PDF extraction
│   ├── spreadsheet.py   # CSV/Excel parsing
│   └── image.py         # Image metadata extraction
└── storage/
    ├── __init__.py
    ├── base.py          # BaseStorage interface
    └── filesystem.py    # Local filesystem storage
```

### Context Engine Test Coverage

All context engine tests are in `test_context_engine.py`. Run `pytest tests/test_context_engine.py -v` for current counts.

| Category | Coverage Areas |
|----------|---------------|
| **Models** | ContentChunk, FileMetadata, ProjectIndex, QueryResult validation and constraints |
| **Storage** | Filesystem round-trips, security (path traversal, symlinks), directory permissions, JSON size limits |
| **Connectors** | Code/document/PDF/spreadsheet/image parsing, relative paths, resource cleanup |
| **Indexer** | File discovery, ignore patterns (.contextignore, .env*), symlink filtering, file count limits, BM25 tokenization |
| **Project Manager** | Score fusion, BM25 query, RLock thread safety, lifecycle (create/load/reindex/list/status/delete) |
| **Server** | Error sanitization, rate limiting, input validation, env var parsing, handler routing |
| **Watcher** | Start/stop, debounce, cooldown, force-flush, ignore spec passthrough, circuit breaker, daemon timers, status reporting |
| **Integration** | Full index-query pipeline, .contextignore respect |

### Context Engine Dependencies

| Package | Purpose |
|---------|---------|
| sentence-transformers / rank-bm25 / numpy | Shared with governance server (embeddings, BM25, vectors) |
| watchdog | File system monitoring for real-time indexing |
| tree-sitter | Language-aware code parsing |
| pymupdf / pdfplumber | PDF content extraction (primary / fallback) |
| openpyxl | Excel file parsing |
| Pillow | Image metadata extraction |
| pathspec | Gitignore-style pattern matching for .contextignore |

See `pyproject.toml [project.optional-dependencies]` for versions.
