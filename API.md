# API Reference

The AI Governance MCP project exposes two MCP servers with a combined 15 tools. The **Governance Server** provides semantic retrieval of AI governance principles, pre-action evaluation, and compliance auditing. The **Context Engine Server** provides semantic search across project content for code and documentation discovery.

## Governance Server (11 Tools)

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
| `assessment` | string | `PROCEED`, `PROCEED_WITH_MODIFICATIONS`, or `ESCALATE` |
| `confidence` | string | `high`, `medium`, or `low` |
| `relevant_principles` | array | Principles relevant to the action, each with `id`, `title`, `content`, `relevance`, `score`, `series_code`, `domain` |
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
| `domain` | string | No | Force a specific domain. One of: `constitution`, `ai-coding`, `multi-agent`, `storytelling`, `multimodal-rag` |
| `include_constitution` | boolean | No | Include constitution principles in response (default: `true`) |
| `include_methods` | boolean | No | Include procedural methods in response (default: `true`) |
| `max_results` | integer | No | Maximum principles per domain, 1-50 (default: `10`) |

**Returns:** Formatted markdown containing:

- Query metadata (domains detected, domain scores, retrieval time)
- Constitution principles (with confidence level, scores, content preview)
- Domain principles (with domain, series, combined score, content preview)
- Applicable methods (with ID, title, confidence)
- S-Series warning header (if safety principles triggered)

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
| `final_decision` | string | Yes | `PROCEED`, `PROCEED_WITH_MODIFICATIONS`, or `ESCALATE` |
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
      {"principle_id": "meta-core-context-engineering", "status": "COMPLIES", "reasoning": "Action follows context engineering guidelines"}
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
| `principle_id` | string | Yes | The principle or method ID (1-100 chars). Examples: `meta-core-context-engineering`, `coding-quality-testing`, `meta-method-header-hierarchy` |

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
{"name": "get_principle", "arguments": {"principle_id": "meta-core-context-engineering"}}
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
| `domain` | string | Yes | Domain name. One of: `constitution`, `ai-coding`, `multi-agent`, `storytelling`, `multimodal-rag` |

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
| `governance_overhead` | object | Contains `governance_evaluations`, `avg_governance_time_ms`, `total_governance_time_ms`, and `assessment_breakdown` (counts of proceed, proceed_with_modifications, escalate) |

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
| `agent_name` | string | Yes | Name of subagent to install. Currently only `"orchestrator"` is available |
| `scope` | string | No | Installation scope: `"project"` (`.claude/agents/`) or `"user"` (`~/.claude/agents/`). Default: `"project"` |
| `confirmed` | boolean | No | Set to `true` to confirm installation after preview |
| `show_manual` | boolean | No | Set to `true` to get manual installation instructions instead of automatic install |

**Returns:** Varies by state:

- **Preview** (default, `confirmed` not set): Returns explanation, action summary, install path, integrity hash check, and options to confirm, get manual instructions, or cancel.
- **Installed** (`confirmed=true`): Returns status `"installed"`, install path, and integrity information.
- **Manual** (`show_manual=true`): Returns step-by-step manual installation instructions with the full template content.
- **Not applicable** (non-Claude Code environment): Returns guidance for using governance tools directly.

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
| `agent_name` | string | Yes | Name of subagent to uninstall. Currently only `"orchestrator"` is available |
| `scope` | string | No | Scope to uninstall from: `"project"` or `"user"`. Default: `"project"` |
| `confirmed` | boolean | No | Set to `true` to confirm uninstallation |

**Returns:** Varies by state:

- **Confirm** (default, `confirmed` not set): Returns warning about what will change and instructions to confirm.
- **Uninstalled** (`confirmed=true`): Returns status `"uninstalled"` with confirmation message.
- **Not installed**: Returns status `"not_installed"` if the agent file does not exist at the expected path.

**Example:**

```json
{"name": "uninstall_agent", "arguments": {"agent_name": "orchestrator", "confirmed": true}}
```

---

## Context Engine Server (4 Tools)

Run with: `python -m ai_governance_mcp.context_engine.server`

**Configuration (environment variables):**

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_CONTEXT_ENGINE_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |
| `AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS` | `384` | Embedding dimensions |
| `AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT` | `0.6` | Semantic vs keyword weight (0.0-1.0) |
| `AI_CONTEXT_ENGINE_INDEX_PATH` | `~/.context-engine/indexes` | Index storage path |
| `AI_CONTEXT_ENGINE_INDEX_MODE` | `ondemand` | `ondemand` (manual re-index) or `realtime` (file watcher with incremental updates) |
| `AI_CONTEXT_ENGINE_LOG_LEVEL` | `INFO` | Logging level |

### query_project

**Purpose:** Search project content using semantic and keyword matching. Returns ranked results with file paths and line numbers.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Natural language query or keyword search (1-10,000 chars). Examples: `"where do we handle authentication?"`, `"validate_token function"`, `"error handling patterns"` |
| `max_results` | integer | No | Maximum results to return, 1-50 (default: `10`) |

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

**Purpose:** Trigger a full re-index of the current project. Use when files have changed and the index may be stale, or after initial project setup. Rate limited to 5 requests per minute.

**Parameters:** None.

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

**Purpose:** Get detailed index statistics for the current project.

**Parameters:** None.

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
| `watcher_status` | string | File watcher state: `running`, `stopped`, `circuit_broken`, or `disabled` |

**Example:**

```json
{"name": "project_status", "arguments": {}}
```
