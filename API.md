# API Reference

The AI Governance MCP project exposes two MCP servers with a combined 23 tools. The **Governance Server** provides semantic retrieval of AI governance principles, pre-action evaluation, and compliance auditing. The **Context Engine Server** provides semantic search across project content for code and documentation discovery.

## Governance Server (16 Tools)

Run with: `python -m ai_governance_mcp.server`

### evaluate_governance

**Purpose:** Evaluate a planned action against governance principles before execution.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `planned_action` | string | Yes | Description of the action you plan to take (max 10,000 chars) |
| `context` | string | No | Relevant background context (max 2,000 chars) |
| `concerns` | string | No | Specific areas of uncertainty or concern (max 1,000 chars) |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | string | Unique identifier for tracking (format: `gov-{12 hex chars}`) |
| `timestamp` | string | ISO timestamp of the assessment |
| `action_reviewed` | string | The planned action that was assessed |
| `assessment` | string | `PROCEED`, `REVIEW`, or `ESCALATE` |
| `confidence` | string | `high`, `medium`, or `low` |
| `relevant_principles` | array | Principles relevant to the action, each with `id`, `title`, `content` (string **or `null`**), `relevance`, `score`, `series_code`, `domain`. `content` is **bounded to a size budget** so the result stays under the per-tool-result token cap: triggered S-Series + top-scoring bodies are inline; lower-ranked are reference-only (`content: null`) — fetch via `get_principle(id)`. |
| `principle_content_note` | string (optional) | Present only when one or more principle bodies were omitted/truncated to fit size limits — lists the IDs to fetch via `get_principle`. |
| `relevant_methods` | array | Procedural methods relevant to the action (up to 5), each with `id`, `title`, `domain`, `score`, `confidence` |
| `compliance_evaluation` | array | Per-principle compliance status with `principle_id`, `principle_title`, `status`, `finding` |
| `required_modifications` | array | Modifications needed for compliance (if any) |
| `s_series_check` | object | Safety check result with `triggered` (bool), `principles` (array), `safety_concerns` (array) |
| `rationale` | string | Explanation of the assessment |
| `requires_ai_judgment` | boolean | Whether the AI should determine the final assessment |
| `ai_judgment_guidance` | string or null | Instructions for AI when `requires_ai_judgment` is true |
| `reasoning_guidance` | string | Guidance for externalizing governance reasoning to the audit trail |

**Example:**

```json
{"name": "evaluate_governance", "arguments": {"planned_action": "Add user authentication with JWT tokens"}}
```

---

### query_governance

**Purpose:** Retrieve relevant AI governance principles and methods using hybrid search (BM25 + semantic).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | The situation, task, or concern to get governance guidance for (1-10,000 chars) |
| `domain` | string | No | Force a specific domain. One of: `constitution`, `ai-coding`, `multi-agent`, `storytelling`, `multimodal-rag`, `ui-ux`, `kmpd`, `accounting`, `saas-ops`, `visual-communication` |
| `include_constitution` | boolean | No | Include constitution principles in response (default: `true`) |
| `include_methods` | boolean | No | Include procedural methods in response (default: `true`) |
| `max_results` | integer | No | Maximum principles per domain, 1-50 (default: `10`) |

**Returns:** Formatted markdown containing:

- Query metadata (domains detected, domain scores, retrieval time)
- Constitution principles (with confidence level, scores, full body)
- Domain principles (with domain, series, combined score, full body)
- Applicable methods (ID, title, confidence — title-only, with a `get_principle` hint)
- S-Series warning header (if safety principles triggered)
- An omitted-bodies footer naming every ID to fetch, when any body did not arrive whole

**Principle bodies are returned in full, within a shared size budget.** Bodies are
allocated across both principle lists up to **20,000 chars total**, ordered by
S-Series-first then descending score. A body that would overflow the remaining budget is
replaced by a pointer naming `get_principle('<id>')`; an oversized single body is cut at
a paragraph boundary with an inline marker naming the same call. Either way the ID also
appears in the footer, so a partial response is never indistinguishable from a complete
one. A unit whose indexed body is empty says so explicitly rather than rendering blank.

Two things this ordering does **not** promise, stated because an earlier version of this
section implied both:

- **It is not pure score order.** Any principle with `series_code == "S"` allocates ahead
  of higher-scoring matches, so a weakly-matching safety principle can displace a strong
  match's body. The displaced body is always named with its fetch call. The corpus bounds
  this today: 3 S-Series principles, 13,172 chars in total, so with one retrieved the top
  match fits. **That bound is a measurement (2026-08-11), not a guarantee** — it goes false
  the moment a fourth S-Series principle lands. Source and re-measure point:
  `server/_content_budget.py`. The code that owns the bound says explicitly to re-measure
  it rather than re-quote it, so treat this line as a snapshot.
- **The per-body ceiling is not below the total.** On this tool it resolves to the budget
  itself, so it does not prevent one large body from consuming most of the allowance. No
  principle in the corpus is large enough to do that today (largest 13,894).

The 20,000 figure bounds **bodies only**. Headers, score lines, match reasons, the
withheld notes and the references section sit outside it and scale with `max_results`,
which clamps to 50 *per list*. In normal operation reranking caps the combined pool well
below that; see BACKLOG #333 for the unbudgeted components on the reranker-unavailable
path.

Before this change bodies were cut at 600 chars with a bare `...` — no marker, no ID, no
fetch path (BACKLOG #325). Methods are the deliberate exception: they render title-only,
not because methods are typically large (the median method is *smaller* than the median
principle) but because a query returns many of them and their tail is heavy — ten methods
at p90 exceeds this whole budget. That is a token-budget decision, not an application of
§4.6.1, which governs `evaluate_governance` only.

**Example:**

```json
{"name": "query_governance", "arguments": {"query": "handling incomplete specifications", "max_results": 5}}
```

---

### verify_governance_compliance

**Purpose:** Verify that governance was consulted for a completed action (post-action audit).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `action_description` | string | Yes | Description of the action that was completed (max 10,000 chars) |
| `expected_principles` | array of strings | No | Principle IDs that should have been consulted (max 20 items, each max 100 chars) |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `action_description` | string | The action that was verified |
| `status` | string | `COMPLIANT`, `NON_COMPLIANT`, or `PARTIAL` |
| `matching_audit_id` | string or null | Audit ID of the matching governance check if found |
| `finding` | string | Explanation of the verification result |
| `timestamp` | string | ISO timestamp of the verification |

**Example:**

```json
{"name": "verify_governance_compliance", "arguments": {"action_description": "Added JWT authentication module"}}
```

---

### log_governance_reasoning

**Purpose:** Record per-principle governance reasoning trace to the audit trail, linked to an `evaluate_governance` assessment.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `audit_id` | string | Yes | Audit ID from `evaluate_governance` response (format: `gov-{12 hex chars}`) |
| `reasoning` | array | Yes | Per-principle reasoning entries (max 20 items). Each entry requires `principle_id` (string), `status` (`COMPLIES`, `NEEDS_MODIFICATION`, or `VIOLATION`), and `reasoning` (string, max 1,000 chars) |
| `final_decision` | string | Yes | `PROCEED`, `REVIEW`, or `ESCALATE` |
| `modifications_applied` | array of strings | No | List of modifications applied, if any (max 10 items, each max 500 chars) |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"logged"` on success |
| `audit_id` | string | The audit ID this reasoning is linked to |
| `entries_logged` | integer | Number of reasoning entries recorded |
| `final_decision` | string | The final governance decision |
| `modifications_count` | integer | Number of modifications recorded |
| `message` | string | Confirmation message |

**Example:**

```json
{
  "name": "log_governance_reasoning",
  "arguments": {
    "audit_id": "gov-a1b2c3d4e5f6",
    "reasoning": [
      {"principle_id": "meta-core-informational-readiness", "status": "COMPLIES", "reasoning": "Action follows context engineering guidelines"}
    ],
    "final_decision": "PROCEED"
  }
}
```

---

### get_principle

**Purpose:** Get the full content of a specific governance principle or method by ID.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `principle_id` | string | Yes | The principle or method ID (1-100 chars). Examples: `meta-core-informational-readiness`, `coding-quality-testing`, `meta-method-header-hierarchy` |

**Returns (principle):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Principle identifier |
| `type` | string | `"principle"` |
| `domain` | string | Source domain |
| `series` | string or null | Series code (S, C, Q, O, G, MA) |
| `number` | integer | Principle number within its series |
| `title` | string | Principle title |
| `content` | string | Full principle text |
| `line_range` | string | Line range in source document |
| `keywords` | array | Extracted keywords |

**Returns (method):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Method identifier |
| `type` | string | `"method"` |
| `domain` | string | Source domain |
| `title` | string | Method title |
| `content` | string | Full method text |
| `line_range` | string | Line range in source document |
| `keywords` | array | Extracted keywords |

**Example:**

```json
{"name": "get_principle", "arguments": {"principle_id": "meta-core-informational-readiness"}}
```

---

### list_domains

**Purpose:** List all available governance domains with statistics (principle counts, descriptions, priorities).

**Parameters:** None.

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `total_domains` | integer | Number of available domains |
| `domains` | object | Domain details keyed by domain name, with principle counts and descriptions |

**Example:**

```json
{"name": "list_domains", "arguments": {}}
```

---

### get_domain_summary

**Purpose:** Get detailed information about a specific domain including all principles and methods.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | string | Yes | Domain name. One of: `constitution`, `ai-coding`, `multi-agent`, `storytelling`, `multimodal-rag`, `ui-ux`, `kmpd`, `accounting`, `saas-ops`, `visual-communication` |

**Returns:** JSON object with detailed domain information including all principles and methods in that domain.

**Example:**

```json
{"name": "get_domain_summary", "arguments": {"domain": "ai-coding"}}
```

---

### log_feedback

**Purpose:** Log feedback on retrieval quality to improve future results. High-rated principles get boosted in subsequent queries.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | The original query (1-10,000 chars) |
| `principle_id` | string | Yes | The principle being rated (1-100 chars) |
| `rating` | integer | Yes | Rating from 1 (not helpful) to 5 (very helpful) |
| `comment` | string | No | Optional feedback comment (max 1,000 chars) |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"logged"` |
| `feedback_id` | string | Timestamp-based identifier |
| `message` | string | Confirmation message |

**Example:**

```json
{"name": "log_feedback", "arguments": {"query": "error handling", "principle_id": "coding-quality-testing", "rating": 5}}
```

---

### get_metrics

**Purpose:** Get retrieval performance metrics including query counts, latency, confidence distribution, and governance overhead.

**Parameters:** None.

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `total_queries` | integer | Total number of queries processed |
| `avg_retrieval_time_ms` | float | Average retrieval time in milliseconds |
| `s_series_trigger_count` | integer | Number of times S-Series safety principles were triggered |
| `domain_query_counts` | object | Query counts per domain |
| `confidence_distribution` | object | Counts by confidence level (`high`, `medium`, `low`) |
| `feedback_count` | integer | Total feedback entries received |
| `avg_feedback_rating` | float or null | Average feedback rating (1-5) |
| `governance_overhead` | object | Contains `governance_evaluations`, `avg_governance_time_ms`, `total_governance_time_ms`, and `assessment_breakdown` (counts of proceed, review, escalate) |

**Example:**

```json
{"name": "get_metrics", "arguments": {}}
```

---

### install_agent

**Purpose:** Install a governance subagent for Claude Code. Creates a subagent definition file in `.claude/agents/`. Only works in Claude Code environments; other platforms receive governance guidance via server instructions automatically.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_name` | string | Yes | Name of subagent to install. Available agents listed in enum |
| `scope` | string | No | Installation scope: `"project"` (`.claude/agents/`) or `"user"` (`~/.claude/agents/`). Default: `"project"` |
| `confirmed` | boolean | No | Set to `true` to confirm installation after preview |
| `show_manual` | boolean | No | Set to `true` to get manual installation instructions instead of automatic install |
| `project_path` | string | No | Absolute path to the target project directory. Auto-detected from MCP roots if available; falls back to `AI_GOVERNANCE_MCP_PROJECT` env var, then CWD. Use when the MCP server's CWD differs from the target project. |
| `domain` | string | No | Active governance domain for the target project (e.g., `"ai-coding"`, `"storytelling"`, `"multi-agent"`, `"ui-ux"`, `"kmpd"`, `"multimodal-rag"`). If provided AND the agent's `applicable_domains` frontmatter excludes this domain, a WARN message is included in the response (Phase-1: WARN + allow; installation proceeds regardless). Omit to skip domain-fit checking. Added v5.0.6 per F-C-04. |

**Returns:** Varies by state. All Claude Code responses include:

- **`applicable_domains`** (array of strings): The domains the agent declares itself for (from agent frontmatter). Values: domain keys (from frontmatter discovery) or `["*"]` for domain-agnostic agents. Added v5.0.6 per F-C-04.
- **`domain_warning`** (string, optional): Present only when caller supplied `domain` AND it doesn't match the agent's `applicable_domains`. Human-readable warning; install proceeds regardless (Phase-1 WARN+allow). Added v5.0.6 per F-C-04.

State-specific returns:

- **Preview** (default, `confirmed` not set): Returns explanation, action summary (with `⚠️  DOMAIN NOTE:` prepended if `domain_warning` is present), install path, integrity hash check, `applicable_domains`, optional `domain_warning`, and options to confirm, get manual instructions, or cancel.
- **Installed** (`confirmed=true`): Returns status `"installed"`, install path, integrity information, `applicable_domains`, and optional `domain_warning`.
- **Manual** (`show_manual=true`): Returns step-by-step manual installation instructions with the full template content.
- **Not applicable** (non-Claude Code environment): Returns guidance for using governance tools directly plus `applicable_domains` and optional `domain_warning` for the referenced agent (v5.0.6 patch — adopters on non-Claude platforms now see domain-fit metadata too).

**Example:**

```json
{"name": "install_agent", "arguments": {"agent_name": "orchestrator", "confirmed": true}}
```

---

### uninstall_agent

**Purpose:** Remove a previously installed governance subagent.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_name` | string | Yes | Name of subagent to uninstall. Available agents listed in enum |
| `scope` | string | No | Scope to uninstall from: `"project"` or `"user"`. Default: `"project"` |
| `confirmed` | boolean | No | Set to `true` to confirm uninstallation |
| `project_path` | string | No | Absolute path to the target project directory. Same resolution as `install_agent`. |

**Returns:** Varies by state:

- **Confirm** (default, `confirmed` not set): Returns warning about what will change and instructions to confirm.
- **Uninstalled** (`confirmed=true`): Returns status `"uninstalled"` with confirmation message.
- **Not installed**: Returns status `"not_installed"` if the agent file does not exist at the expected path.

**Example:**

```json
{"name": "uninstall_agent", "arguments": {"agent_name": "orchestrator", "confirmed": true}}
```

---

### list_agents

**Purpose:** List all available governance agent definitions with summaries. Works across all MCP-compatible platforms (Claude Code, Gemini CLI, Cursor, Windsurf, ChatGPT Desktop). Use `install_agent()` for full definitions with platform-specific adaptation guidance.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `include_details` | boolean | No | Include full `action_summary` for each agent (default: false) |

**Returns:** JSON with `total_agents`, `agents` array (each with `name`, `short_description`, `applicable_domains`, `canonical_source`), and `cross_platform_note`. When `include_details=true`, each agent also includes `action_summary`.

**Example:**

```json
{"name": "list_agents", "arguments": {}}
```

```json
{"name": "list_agents", "arguments": {"include_details": true}}
```

---

### scaffold_project

**Purpose:** Initialize governance memory files for a new project. Creates `_ai-context/SESSION-STATE.md`, `_ai-context/PROJECT-MEMORY.md`, `_ai-context/LEARNING-LOG.md` (unified layout for all project types), and project instruction files at the root. Two-step flow: call without `confirmed` for preview, then with `confirmed=true` to create files.

`mode="sync"` (BACKLOG #190) serves the other half of the lifecycle: an **already-scaffolded** project never receives later template improvements, because `create` skips files that already exist. Sync reports that staleness. It is **report-only — it never writes**.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mode` | string | No | `"create"` (default) initializes a project, skipping existing files. `"sync"` is report-only for an existing project: lists missing kit files and template changes made since it was scaffolded. Cannot be combined with `confirmed` or `show_manual`. |
| `project_name` | string | No | Project name, max 100 chars (defaults to directory name) |
| `project_type` | string | No | `"code"` for repositories or `"document"` for folder-based projects. Default: `"code"`. **In sync mode this is read from the file's stamp and the stamp wins** — a caller's guess never overrides it. Required only for unstamped (pre-#190) projects. |
| `kit_tier` | string | No | `"core"` (code: 6 files — memory + AGENTS.md/CLAUDE.md/GEMINI.md loaders so a default project auto-loads on Claude Code, Codex, and Gemini; document: 4 files — memory + README, use-case-neutral), `"standard"` (code: 11 files; adds ARCHITECTURE.md + SPECIFICATION.md + .claude/skills/completion-sequence-aigov/ + `_ai-context/BACKLOG.md` + `_ai-context/OPERATIONS.md` per `title-10-ai-coding-cfr.md §1.5.2`; document: 6 files; adds `_ai-context/BACKLOG.md` + `_ai-context/OPERATIONS.md`), or `"saas-ops"` (12 files; standard + SAAS-OPS-SOP.md, a per-app SaaS production-operations SOP for a money-taking SaaS — the per-app instance of the `title-45` saas-ops domain; code projects only). Default: `"core"` |
| `confirmed` | boolean | No | Set to `true` to create files after preview |
| `project_path` | string | No | Absolute path to the target project directory. Auto-detected from MCP roots if available; falls back to `AI_GOVERNANCE_MCP_PROJECT` env var, then CWD. |
| `show_manual` | boolean | No | Set to `true` to get file contents for manual creation. Use in sandboxed environments (Cowork) where the MCP server cannot write to the project directory. |

**Returns:** Varies by state:

- **Preview** (default, `confirmed` not set): Returns file list with actions (create/skip), project root, resolved paths, and options to confirm or cancel.
- **Scaffolded** (`confirmed=true`): Returns status `"scaffolded"`, files created, files skipped, and project root.
- **Manual** (`show_manual=true`): Returns file paths and full contents for the LLM to create manually. Works even when project_path is invalid.
- **Sync report** (`mode="sync"`): Returns status `"sync_report"` with `missing_kit_files` (kit files added to the template since this project was scaffolded) and `pending_template_changes` (changelog entries newer than the project's stamp, each with what changed, **why**, and a suggested action). Nothing is written.
- **Error**: Returns error code (`INVALID_PROJECT_PATH`, `INVALID_PROJECT_TYPE`, `INVALID_KIT_TIER`, `INVALID_MODE`, `INVALID_MODE_COMBINATION`, `SYNC_PROJECT_TYPE_UNKNOWN`) with suggestions.

**How sync avoids false positives.** It does **not** diff your files against the current templates. Memory files are *supposed* to diverge — they accumulate real content, get distilled at 300 lines per §7.0.4, and outgrow starter sections. (A structural-diff prototype was measured against this repo's own memory files: 23 "drift" findings, zero of them real.) Instead, every scaffolded file is stamped at birth with its template version:

```
<!-- scaffold: code/standard template-v2.63.0 2026-07-15 -->
```

Sync reports only the maintainer-written changelog entries *newer than that stamp*. Nothing is inferred, so there are no false positives — and each entry carries the intent behind the change, which a diff cannot recover. Projects scaffolded before stamping existed have no stamp; sync says so, lists the full history for their project type, and tells you to review rather than apply blindly.

**Examples:**

```json
{"name": "scaffold_project", "arguments": {"project_type": "code", "kit_tier": "standard", "confirmed": true}}
```

```json
{"name": "scaffold_project", "arguments": {"mode": "sync"}}
```

---

### capture_reference

**Purpose:** Create a new Reference Library entry. Generates a markdown file with YAML frontmatter in `reference-library/{domain}/`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | Yes | Unique entry ID: lowercase, hyphens allowed, must start with `ref-` (e.g., `ref-ai-coding-my-pattern`) |
| `title` | string | Yes | Human-readable title (max 200 chars) |
| `domain` | string | Yes | Domain this entry belongs to — lowercase alphanumeric with hyphens (e.g., `ai-coding`, `kmpd`) |
| `tags` | array | Yes | Faceted tags, 1-10 strings |
| `applies_to` | array | No | Stack/platform/language tokens this entry is relevant to (e.g., `["python", "nextjs"]`), max 10. Omit for universal patterns. An environment filter used by `search_references`' `stack` — distinct from `tags` (which affect content search) |
| `entry_type` | string | Yes | `"direct"` (artifact in library) or `"reference"` (pointer to external source) |
| `artifact` | string | Yes | The actual code, template, config, or curated summary (max 10,000 chars) |
| `summary` | string | No | One-line description for search (max 300 chars) |
| `context` | string | No | When to use this and why it exists (max 2,000 chars) |
| `lessons` | string | No | What worked, what didn't, edge cases (max 2,000 chars) |
| `maturity` | string | No | `"seedling"`, `"budding"`, or `"evergreen"`. Default: `"seedling"` |
| `external_url` | string | No | URL for reference entries (max 500 chars) |
| `external_author` | string | No | Author for reference entries (max 100 chars) |

**Returns:** Status `"captured"` with entry_id, file_path, domain, entry_type, maturity, and next_steps (rebuild index to make searchable). Files are created in the governance server's reference library, not in the calling project. Returns error `ENTRY_EXISTS` if an entry with that ID already exists.

**Example:**

```json
{
  "name": "capture_reference",
  "arguments": {
    "id": "ref-ai-coding-my-pattern",
    "title": "My Reusable Pattern",
    "domain": "ai-coding",
    "tags": ["pattern", "reusable", "example"],
    "entry_type": "direct",
    "artifact": "## Pattern\n\nDescription of the reusable pattern..."
  }
}
```

### search_references

**Purpose:** Search the Reference Library for implementation precedent before writing code. Returns proven patterns, code templates, and lessons learned from prior implementations. Separate from governance (principles) and query_project (existing code).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Implementation-specific search (e.g., `"playwright auth setup"`) |
| `domain` | string | No | Filter to specific domain (e.g., `"ai-coding"`, `"kmpd"`) |
| `tags` | array | No | Boost results matching these technology tags (e.g., `["playwright", "nextjs"]`) |
| `stack` | array | No | Boost entries whose `applies_to` matches the current project's stack/platform/language (e.g., `["python"]`). Entries without `applies_to` are universal and unaffected. Boost-only — a mismatch is never penalized |
| `max_results` | integer | No | Maximum results to return (default 5, max 20) |

**Returns:** JSON with `query`, `domain_filter`, `tag_filter`, `stack_filter`, `result_count`, `results` array (each with `id`, `title`, `summary`, `domain`, `tags`, `applies_to`, `status`, `maturity`, `confidence`, `score`), and a `hint` to use `get_principle(principle_id)` for full content.

**Example:**

```json
{
  "name": "search_references",
  "arguments": {
    "query": "playwright auth setup",
    "domain": "ai-coding",
    "tags": ["playwright", "testing"]
  }
}
```

### analyze_feedback_loop

Read precomputed feedback loop analysis of governance server logs. Shows effectiveness metrics (M-001/M-003/M-004), dead principles, false-positive patterns, retrieval gaps, and actionable recommendations. Run `scripts/analyze_feedback_loop.py` first to generate the analysis.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `section` | string | No | Return only this section (e.g., `effectiveness_metrics`, `dead_principles`, `false_positives`, `retrieval_gaps`, `actionable_recommendations`) |

**Response:** The precomputed analysis JSON, or an error with instructions to run the script if the file is missing. Includes a staleness warning if the analysis is >30 days old.

**Example:**

```json
{
  "name": "analyze_feedback_loop",
  "arguments": {
    "section": "effectiveness_metrics"
  }
}
```

---

## Context Engine Server (7 Tools)

Run with: `python -m ai_governance_mcp.context_engine.server`

**Configuration (environment variables):**

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_CONTEXT_ENGINE_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |
| `AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS` | `384` | Embedding dimensions |
| `AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT` | `0.7` | Semantic vs keyword weight (0.0-1.0) |
| `AI_CONTEXT_ENGINE_INDEX_PATH` | `~/.context-engine/indexes` | Index storage path |
| `AI_CONTEXT_ENGINE_INDEX_MODE` | `ondemand` | `ondemand` (manual re-index) or `realtime` (file watcher with incremental updates) |
| `AI_CONTEXT_ENGINE_READONLY` | `auto` | `true` (force read-only), `false` (force writable), `auto` (probe filesystem) |
| `AI_CONTEXT_ENGINE_DEFAULT_PROJECT` | *(none)* | Fallback project path when CWD is not the project (e.g., in Cowork VM) |
| `AI_CONTEXT_ENGINE_LOG_LEVEL` | `INFO` | Logging level |

**CLI tools:**

| Command | Purpose |
|---------|---------|
| `ai-context-engine` | Run the MCP server (stdio) |
| `context-engine-watcher` | Standalone watcher daemon (keeps indexes fresh) |
| `context-engine-service` | Install/manage watcher as a system service |

### query_project

**Purpose:** Search project content using semantic and keyword matching. Returns ranked results with file paths and line numbers.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Natural language query or keyword search (1-10,000 chars). Examples: `"where do we handle authentication?"`, `"validate_token function"`, `"error handling patterns"` |
| `max_results` | integer | No | Maximum results to return, 1-50 (default: `10`) |
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. Use in sandboxed environments where CWD is not the project. |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The original query |
| `total_results` | integer | Number of results returned |
| `query_time_ms` | float | Query execution time in milliseconds |
| `last_indexed_at` | string\|null | ISO timestamp of when the index was last updated |
| `index_age_seconds` | float\|null | Seconds since the index was last updated |
| `results` | array | Ranked results, each containing `file` (relative path), `lines` (line range), `type` (content type), `score` (relevance 0-1), `heading` (section/function name), `content` (first 500 chars) |

**Example:**

```json
{"name": "query_project", "arguments": {"query": "where do we handle authentication?", "max_results": 5}}
```

---

### index_project

**Purpose:** Trigger a full re-index of the current project. Use when files have changed and the index may be stale, or after initial project setup. Rate limited to 5 requests per minute. Returns an error in read-only mode.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | `"Project indexed successfully"` |
| `project_path` | string | Absolute path to the indexed project |
| `total_files` | integer | Number of files indexed |
| `total_chunks` | integer | Number of content chunks created |
| `embedding_model` | string | Model used for embeddings |

**Example:**

```json
{"name": "index_project", "arguments": {}}
```

---

### list_projects

**Purpose:** Show all indexed projects with basic stats.

**Parameters:** None.

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `projects` | array | List of indexed projects, each with `project_id`, `project_path`, `total_files`, `total_chunks`, `last_updated` (ISO timestamp), `index_mode` (`"realtime"` or `"ondemand"`) |

**Example:**

```json
{"name": "list_projects", "arguments": {}}
```

---

### project_status

**Purpose:** Get detailed index statistics for the current project. Also reports standalone watcher daemon status if a heartbeat file exists.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | string | Unique project identifier |
| `project_path` | string | Absolute path to project root |
| `total_files` | integer | Number of indexed files |
| `total_chunks` | integer | Number of indexed chunks |
| `index_mode` | string | Current indexing mode (`"realtime"` or `"ondemand"`) |
| `last_updated` | string or null | ISO timestamp of last index update |
| `index_size_bytes` | integer | Total index size on disk |
| `embedding_model` | string | Model used for embeddings |
| `chunking_version` | string | Chunking strategy version (e.g., `"tree-sitter-v2"`, `"line-based-v1"`) |
| `watcher_status` | string | File watcher state: `running`, `stopped`, `circuit_broken`, or `disabled` |

**Example:**

```json
{"name": "project_status", "arguments": {}}
```

---

### find_references

**Purpose:** Find structural code references for a symbol — who imports it, calls it, or extends it — from the code reference graph built during indexing.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `symbol` | string | Yes | Symbol name to find references for (1-200 chars). Examples: `"CodeConnector"`, `"parse"`, `"BaseStorage"` |
| `direction` | string | No | `"callers"` (who references this symbol), `"callees"` (what it references), or `"all"` (default) |
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. |

---

### build_knowledge_graph

**Purpose:** Build a knowledge graph for the current project using Cognee — extracts entities and relationships from indexed content via LLM. Opt-in: requires the `knowledge-graph` extra (`pip install -e ".[knowledge-graph]"`) and uses LLM calls with real cost (default providers LM Studio/Ollama are free/local; cloud providers incur API charges — configure via `AI_CONTEXT_ENGINE_COGNEE_*` env vars). Requires the project to be indexed first via `index_project`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. |

---

### query_knowledge_graph

**Purpose:** Query the knowledge graph for entity and relationship information — concept connections semantic search might miss. Requires `build_knowledge_graph` to have been run first.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Natural-language question about entities/relationships in the project |
| `project_path` | string | No | Absolute path to the project directory. Defaults to CWD. |

---

## Enforcement Proxy

The enforcement proxy (`ai-governance-proxy`) is a Layer 3 protocol-level gate for any MCP client. It intercepts JSON-RPC `tools/call` requests at the stdio level. In **hard mode** it blocks an action tool until `evaluate_governance()` has been called within the recency window; in **soft mode** (`--soft-mode` / `GOVERNANCE_ENFORCEMENT_SOFT_MODE=true`, used by configs generated with `--enforce`) it only appends a warning and lets the call through. Either way it gates the model's *call order* — it is model-satisfiable (the model can call `evaluate_governance()` itself), **not** a human approval gate. On GUI auto-run hosts (Claude Desktop) a soft warning arrives *after* the tool runs, so the real human gate is the host's own per-tool approval prompt (see `ref-ai-coding-connect-local-mcp-server-to-claude-surfaces` — `search_references("ref-ai-coding-connect-local-mcp-server-to-claude-surfaces")`). Works with Claude App, Cursor, Gemini CLI, ChatGPT Desktop, and any other MCP-compatible client.

### CLI Entry Point

```
ai-governance-proxy [options] -- <server-command> [server-args...]
```

### Usage Examples

```bash
# Phase 1 — wrap the governance server (default if no command given):
ai-governance-proxy -- python -m ai_governance_mcp.server

# Phase 1 — with soft mode (warn instead of block):
ai-governance-proxy --soft-mode -- python -m ai_governance_mcp.server

# Phase 2 — wrap GitHub MCP with governance enforcement:
ai-governance-proxy --govern-all \
    --always-allow "get_file_contents,list_issues,search_code" \
    -- npx @modelcontextprotocol/server-github

# Phase 2 — with config file:
ai-governance-proxy --config github-governance.yaml \
    -- npx @modelcontextprotocol/server-github
```

> **GUI-host configs need an absolute interpreter.** The examples above use the bare `ai-governance-proxy` / `python` names, which resolve only in an interactive shell (venv `bin` on PATH). A GUI MCP host (Claude Desktop, etc.) launches with a minimal PATH and would `spawn ENOENT`. Generate those configs with `python -m ai_governance_mcp.config_generator --json claude [--enforce]` — it emits an absolute `sys.executable -m …` form.

### CLI Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--soft-mode` | `false` | Warn instead of block (advisory enforcement) |
| `--disabled` | `false` | Pass through without enforcement (testing) |
| `--recency-window` | `50` | Tool calls before governance expires |
| `--config` | — | YAML config file specifying governed/allowed tools |
| `--govern-all` | `false` | Govern ALL tools not explicitly exempted (Phase 2) |
| `--always-allow` | — | Comma-separated tools exempt from governance |
| `--cross-mcp` | `false` | Enable shared state file for cross-process coordination |
| `--state-file` | `~/.ai-governance/enforcement-state.json` | Shared state file path |
| `--state-ttl` | `300` | Shared state TTL in seconds |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOVERNANCE_ENFORCEMENT_ENABLED` | `true` | Master toggle — set `false` to disable completely |
| `GOVERNANCE_ENFORCEMENT_SOFT_MODE` | `false` | Warn instead of block (post-hoc on GUI auto-run hosts; set `true` by configs generated with `--enforce`) |
| `GOVERNANCE_RECENCY_WINDOW` | `50` | Tool calls before governance expires |
| `GOVERNANCE_STATE_FILE` | `~/.ai-governance/enforcement-state.json` | Shared state file path |
| `GOVERNANCE_STATE_TTL` | `300` | Shared state TTL in seconds |

Environment variables are overridden by CLI flags when both are provided.

### Phase 1 Tool Classification

In Phase 1 (self-enforcement), the proxy applies these default tool sets:

| Category | Tools | Behavior |
|----------|-------|----------|
| **Governed** (require prior governance) | `scaffold_project`, `capture_reference`, `install_agent`, `uninstall_agent`, `log_feedback`, `log_governance_reasoning` | Blocked until `evaluate_governance()` called within recency window |
| **Satisfiers** (count as governance) | `evaluate_governance`, `verify_governance_compliance` | Reset the recency counter |
| **Always Allowed** (read-only pass-through) | `query_governance`, `get_principle`, `list_domains`, `get_domain_summary`, `get_metrics`, `list_agents`, `search_references`, `analyze_feedback_loop` | Pass through unconditionally |

### Phase 2 Config File Format

For cross-MCP enforcement, provide a YAML config:

```yaml
# github-governance.yaml
governed_tools:
  - create_pull_request
  - push_files
  - create_issue
  - merge_pull_request
always_allowed:
  - get_file_contents
  - list_issues
  - search_code
  - list_commits
govern_all: true  # Govern ALL tools not in always_allowed
```

### Shared State Coordination

Phase 2 cross-MCP mode uses a shared state file for cross-process coordination. When `evaluate_governance()` is called on the governance proxy instance, it writes a timestamp to `~/.ai-governance/enforcement-state.json`. Other proxy instances (wrapping GitHub, filesystem, etc.) read this file to determine if governance has been satisfied. The TTL (default 300s) prevents stale governance from persisting indefinitely. File writes are atomic (write-to-temp + rename) with fail-closed security — if the state file is unreadable, governance is considered unsatisfied.
