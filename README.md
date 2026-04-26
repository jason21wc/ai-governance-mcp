# AI Governance MCP Server

[![CI](https://github.com/jason21wc/ai-governance-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jason21wc/ai-governance-mcp/actions/workflows/ci.yml)

> **A semantic retrieval system that gives AI assistants on-demand access to domain-specific governance principles — a queryable "second brain" of encoded standards.**

## Why this exists

The engineering stack for AI systems has five layers:

- **Prompt engineering** — how you phrase the request.
- **Retrieval engineering** — grounding the model in information it wasn't trained on (vector stores, chunking, reranking, hybrid search).
- **Context engineering** — dynamically assembling memory, tool outputs, conversation history, and reference material into each inference.
- **Harness engineering** — the operational environment around the model: orchestration, guardrails, approval gates, feedback sensors, observability, durable state.
- **Intent engineering** — principles, methods, and enforcement that run across every layer. What the system is optimizing for, including in cases no one anticipated.

The first four form a structural stack — each layer contains the ones below it. Intent engineering runs across all of them, defining what the system is ultimately trying to accomplish. Without it, the other layers optimize without knowing what for.

Most AI tools stop at the first three. They phrase prompts, retrieve reference material, and assemble context. They don't tell the AI what judgment to apply — which standards matter, which constraints can't be traded off, what "done" looks like.

This project is infrastructure for the intent layer. It doesn't make AI smarter. It encodes the principles and methods that define what good work looks like, makes them retrievable at the moment of the AI's decision through MCP tools, and gates file-modifying actions on prior consultation through hooks.

For the founding intent in the author's voice, see the Declaration in [`documents/constitution.md`](documents/constitution.md).

## The Problem

AI assistants are powerful, but without structured guidance they can:
- Hallucinate requirements instead of asking for clarification
- Skip validation steps in complex workflows
- Apply inconsistent approaches across similar problems
- Miss critical safety considerations

Loading full governance documents (~55K+ tokens) into context is wasteful and often exceeds limits. Simple keyword search misses semantically related concepts.

## The Solution

This MCP server provides **hybrid semantic retrieval** of governance principles:

- **Near-zero miss rate** in hybrid retrieval for in-domain queries — combined keyword + semantic search with reranking. See [`tests/benchmarks/`](tests/benchmarks/) for formal Recall@K measurements on a fixed query set.
- **Sub-100ms retrieval latency** in typical use on a developer laptop; reproduce via `python -m ai_governance_mcp.server --test "<query>"`.
- **Smart domain routing** — automatic identification of relevant knowledge domains.
- **Cross-encoder reranking** — most relevant principles surface first.

```
Query: "how do I handle incomplete specifications?"
→ Routes to: ai-coding domain
→ Returns: coding-context-specification-completeness with HIGH confidence
→ Time: 45ms

Query: "help me develop my protagonist's character arc"
→ Routes to: storytelling domain
→ Returns: storytelling-ST3-transformation-arc with HIGH confidence
→ Time: 48ms
```

## The Governance Framework

Most people use AI as-is. This project implements a systematic governance framework that is retrievable, auditable, and structurally enforceable at the moment of the AI's decision — then operationalizes it through an MCP server.

The framework uses a 7-layer governance hierarchy modeled on the US Constitutional system: immutable Safety Principles (Bill of Rights), Constitution, Domain Statutes, Rules of Procedure, Domain Regulations, Tool SOPs, and accumulating Secondary Authority (Reference Library). See [`documents/constitution.md`](documents/constitution.md) for the full operative hierarchy and the Declaration of founding intent.

### Available Domains

<!-- Verify counts: python -c "import json; d=json.load(open('index/global_index.json'))['domains']; [print(f'{k}: {len(v.get(\"principles\",[]))}p, {len(v.get(\"methods\",[]))}m') for k,v in d.items()]" -->
| Domain | Principles | Methods | Coverage |
|--------|------------|---------|----------|
| **Constitution** | 24 | 214 | Universal AI behavior, safety, quality |
| **AI Coding** | 12 | 231 | Software development, testing, deployment |
| **Multi-Agent** | 17 | 54 | Agent orchestration, handoffs, autonomous operation |
| **Storytelling** | 15 | 42 | Creative writing, narrative, voice preservation |
| **Multimodal RAG** | 32 | 64 | Image retrieval, visual presentation, agentic retrieval |
| **UI/UX** | 20 | 43 | Visual hierarchy, accessibility, interaction design |
| **KM&PD** | 10 | 40 | Knowledge management, people development, training |

## Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| Server | MCP Python SDK | Official MCP SDK (`mcp.server.Server`) |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`) | Semantic similarity |
| Keyword Search | rank-bm25 | BM25 keyword matching |
| Reranking | CrossEncoder | Result refinement |
| Data Models | Pydantic | Validation & typing |
| Storage | In-memory (NumPy) | Fast retrieval |

```
Build Time:
  documents/*.md → extractor.py → global_index.json + embeddings.npy

Runtime:
  Query → Domain Router → Hybrid Search → Reranker → Hierarchy Filter → Results
          (semantic)    (BM25+semantic)  (cross-encoder)
```

**Retrieval pipeline:**

1. **Domain Routing** — query embedding similarity identifies relevant domains
2. **Hybrid Search** — BM25 (keywords) + dense vectors (semantic) in parallel
3. **Score Fusion** — weighted combination (60% semantic, 40% keyword)
4. **Reranking** — cross-encoder scores top 20 candidates
5. **Hierarchy Filter** — S-Series (safety) always prioritized

## How It Works

### 17 MCP Tools (2 Servers)

**Governance Server (13 tools):**

| Tool | Purpose |
|------|---------|
| `evaluate_governance` | **Pre-action** compliance check — PROCEED/MODIFY/ESCALATE |
| `query_governance` | Main retrieval with confidence scores |
| `verify_governance_compliance` | **Post-action** audit verification |
| `get_principle` | Full content by ID |
| `list_domains` | Available domains with stats |
| `get_domain_summary` | Domain exploration |
| `log_feedback` | Quality tracking |
| `get_metrics` | Performance analytics |
| `install_agent` | Install governance subagent (Claude Code only) |
| `uninstall_agent` | Remove installed subagent |
| `log_governance_reasoning` | Record per-principle reasoning traces for audit |
| `scaffold_project` | Create governance memory files for new projects |
| `capture_reference` | Create Reference Library entries from real application |

**Context Engine Server (4 tools):**

| Tool | Purpose |
|------|---------|
| `query_project` | Semantic + keyword search across project content |
| `index_project` | Trigger re-index of current project |
| `list_projects` | Show all indexed projects |
| `project_status` | Index stats for current project |

**Governance enforcement:**

- `evaluate_governance` evaluates planned actions against principles BEFORE execution, auto-detects S-Series (safety) concerns, and returns PROCEED, PROCEED_WITH_MODIFICATIONS, or ESCALATE. S-Series violations force ESCALATE with human review. Every call logs an `audit_id`.
- `verify_governance_compliance` checks whether governance was consulted for a completed action — catches bypassed checks after the fact.
- `log_governance_reasoning` captures per-principle reasoning traces for the audit trail.

**Subagent installation (Claude Code):**

The `install_agent` tool provides 10 specialized subagents:

- **orchestrator** — governance coordination (ensures `evaluate_governance()` is called)
- **code-reviewer** — fresh-context code review against explicit criteria
- **security-auditor** — OWASP-aligned vulnerability detection
- **test-generator** — behavior-focused test creation
- **documentation-writer** — technical writing specialist
- **validator** — criteria-based quality validation
- **contrarian-reviewer** — devil's advocate for high-stakes decisions
- **coherence-auditor** — documentation drift detection
- **continuity-auditor** — narrative consistency verification
- **voice-coach** — character voice distinction analysis

Other platforms receive agent definitions as adaptable reference material via `install_agent`.

### Example Usage

Add the MCP server to your AI assistant's configuration:

```json
{
  "mcpServers": {
    "ai-governance": {
      "command": "python",
      "args": ["-m", "ai_governance_mcp.server"]
    }
  }
}
```

Then the AI invokes governance automatically:

```
User: "I need to implement a login system"

AI uses query_governance("implementing authentication system")
→ Returns coding-quality-security-first-development + coding-context-specification-completeness
→ AI knows to: verify security requirements, ask about auth method preferences
```

## Results

| Metric | Target | Observed (approximate) |
|--------|--------|------------------------|
| Miss Rate | <1% | Near-zero on in-domain queries (hybrid retrieval; see `tests/benchmarks/` for Recall@K) |
| Latency | <100ms | ~50ms typical (author-observed on a developer laptop) |
| Token Savings | >90% | ~98% (1-3K retrieved vs 55K+ if full docs loaded into context) |
| Test Coverage | 80% | **~90%** governance, **~65%** context engine (run `pytest --cov` for current metrics) |

> *Metrics are author-observed on a developer laptop and are not a controlled benchmark. Reproduce via `pytest --cov` for coverage, `python -m ai_governance_mcp.server --test "<query>"` for retrieval latency, and `tests/benchmarks/` for formal retrieval-quality measurements.*

## Quick Start

The fastest path is Docker + Claude Desktop:

1. **Install Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop/).
2. **Pull the image**: `docker pull jason21wc/ai-governance-mcp:latest`
3. **Edit your Claude Desktop config** file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
4. **Add the MCP server** (merge into your existing `mcpServers` block):
   ```json
   {
     "mcpServers": {
       "ai-governance": {
         "command": "docker",
         "args": ["run", "-i", "--rm", "jason21wc/ai-governance-mcp:latest"]
       }
     }
   }
   ```
5. **Restart Claude Desktop** and test: *"Query governance for handling incomplete specifications"*.

<details>
<summary><b>Step-by-step walkthroughs: Windows, macOS, Windsurf</b></summary>

### Windows (Docker Desktop)

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. In Docker Desktop → Search → `jason21wc/ai-governance-mcp` → Pull
3. Open File Explorer → paste `%APPDATA%\Claude` → open `claude_desktop_config.json` in Notepad
4. Add the `"ai-governance"` block shown above under `"mcpServers"` (remember the comma if you have other servers)
5. Save, restart Claude Desktop, test

### macOS (Docker Desktop)

```bash
docker pull jason21wc/ai-governance-mcp:latest
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add the `"ai-governance"` block under `"mcpServers"`, save, restart Claude Desktop.

### Windsurf

Windsurf supports MCP through Cascade. Config file: `~/.codeium/windsurf/mcp_config.json`. Add the same `"ai-governance"` block. In Cascade chat → hammer icon → Configure → View raw config.

</details>

## First Five: Day-One Essentials from the Universal Floor

Every `evaluate_governance` call returns a **universal floor** — items that hold regardless of whether the AI is writing code, drafting a story, or building a RAG pipeline. The full floor (defined in [`documents/tiers.json`](documents/tiers.json)) has four constitutional principles, five method references, and a subagent-applicability check. The five below are the *day-one essentials* — the smallest set that gets an external adopter productive without first learning Constitutional naming or the 7-layer hierarchy.

| Rule | What it asks of the AI | Canonical reference |
|------|------------------------|---------------------|
| **Epistemic honesty** | When uncertain, say so. Never present a best guess as fact. Reporting "I cannot do this confidently" is a successful outcome. | principle: `meta-safety-transparent-limitations` |
| **Visible reasoning** | Show your work. Cite sources for factual claims. Make assumptions explicit before producing the output. | principle: `meta-quality-visible-reasoning-traceability` |
| **Verification before action** | Define what "done" looks like before starting. Validate in small increments. Fail fast. | principle: `meta-quality-verification-validation` |
| **Root cause over symptoms** | Distinguish what triggered a problem from what structurally enables it. Fix the latter, not the former. | principle: `meta-core-systemic-thinking` |
| **Proportional rigor** | Match procedural ceremony to stakes. Simple tasks get simple checks; high-stakes work gets full protocol. | method: `rules-of-procedure §7.8` |

Use `get_principle` for principle IDs; methods like §7.8 are reachable through `query_governance`:

```
get_principle("meta-core-systemic-thinking")
query_governance("proportional rigor")
```

**Sample queries to run on day one** (each surfaces additional floor items beyond the table above — e.g., the second query exercises the testing-integration method):

```
query_governance("how do I handle incomplete specifications")
query_governance("when should I write tests")
query_governance("how to do a security review")
query_governance("refactoring approach for legacy code")
evaluate_governance(planned_action="ship a new feature to production")
```

Once these feel natural, the full hierarchy in [`documents/constitution.md`](documents/constitution.md) becomes navigable rather than imposing — you'll already recognize the principles you're being asked to extend.

## Use via RAG (No MCP Server)

If you already have a RAG infrastructure or want to use the governance content in a non-MCP environment (ChatGPT Custom GPT, Claude Projects, Perplexity Spaces, NotebookLM, OpenAI Assistants, custom bots), you can load the `documents/` folder directly as a knowledge source — no server, no hooks, no installation.

**Pattern:**

1. Clone or download the `documents/` folder from this repo.
2. Load `documents/ai-instructions.md` into your platform's system prompt or "AI Instructions" field — it tells the AI how to consult the governance content.
3. Load the rest of `documents/*.md` (constitution, rules-of-procedure, title-NN-*.md) as the reference/knowledge corpus.

**Platform mapping:**

| Platform | Instructions field → `ai-instructions.md` | Knowledge/sources → other `documents/*.md` |
|---|---|---|
| ChatGPT Custom GPT | "Instructions" field | "Knowledge" file uploads |
| Claude Projects | Project system prompt | Project knowledge |
| Perplexity Spaces | "AI Instructions" | Uploaded files |
| OpenAI Assistants API | `instructions` parameter | File Search tool |
| NotebookLM | *(use first message as instructions)* | Source documents |
| Poe / custom bots | System prompt | Vector store |

**Note on platform instruction-field limits:** `documents/ai-instructions.md` is ~230 lines with structured XML-tag blocks. ChatGPT Custom GPT "Instructions" fields cap at 8K characters; Perplexity Spaces is tighter. If your platform's instruction field is too small, paste only the `<primary_directive>` + `<first_response_protocol>` + `<mcp_integration>` blocks into Instructions, and move the rest (hierarchy, memory-architecture, version-reference tables) into the knowledge corpus.

**Trade-off (be explicit about it):**

- ✅ **You get:** principles + methods content, retrieval grounding, the AI can cite specific principles by name.
- ❌ **You don't get:** `evaluate_governance` scoring + S-Series veto, hierarchy filter, `verify_governance_compliance` audit trail, the structural hook enforcement that blocks unconsulted file-modifying actions, or the 10 installable subagents.

In 5-layer terms: you're adopting the **intent-engineering** content with your own **retrieval engineering** around it. You're skipping the **harness-engineering** layer the MCP server provides. Fine for advisory use and assistants that summarize or answer questions; not sufficient when you need deterministic blocking of risky actions in an autonomous agent.

**License:** Framework content (`documents/`) is **CC BY-NC-ND 4.0** — attribution required, non-commercial use only, no derivatives (you may load the files as reference; you may not modify and redistribute). Code (`src/`) is Apache-2.0. See [`LICENSE-CONTENT`](LICENSE-CONTENT) for the framework-content license terms.

## Platform Configuration

Use the config generator for platform-specific setup — it auto-detects your installation path and generates correct environment variables:

```bash
python -m ai_governance_mcp.config_generator --platform claude    # Claude Code CLI
python -m ai_governance_mcp.config_generator --platform gemini    # Gemini CLI
python -m ai_governance_mcp.config_generator --platform chatgpt   # ChatGPT Desktop
python -m ai_governance_mcp.config_generator --platform cursor    # Cursor
python -m ai_governance_mcp.config_generator --platform windsurf  # Windsurf
python -m ai_governance_mcp.config_generator --all                # All platforms
python -m ai_governance_mcp.config_generator --json claude        # JSON output
```

> **For pip users:** the config generator automatically includes `AI_GOVERNANCE_INDEX_PATH` and `AI_GOVERNANCE_DOCUMENTS_PATH` environment variables. These are required when running the server from a different directory than the project root. Docker users don't need this — paths are baked into the image.

**Web-based platforms** (Perplexity, Grok, Google AI Studio): use the [MCP SuperAssistant Chrome Extension](https://github.com/srbhptl39/MCP-SuperAssistant) to bridge MCP to web clients.

**Claude Code CLI and Claude Desktop have separate MCP configurations.** If you use both, configure each independently.

## Local Installation

For development or customization:

```bash
git clone https://github.com/jason21wc/ai-governance-mcp.git
cd ai-governance-mcp
pip install -e .                       # install with dependencies
python -m ai_governance_mcp.extractor  # build the index (first time)
python -m ai_governance_mcp.server     # run the server
```

**Quick test:**

```bash
python -m ai_governance_mcp.server --test "how do I handle incomplete specs"
```

## Configuration

**Governance Server environment variables:**

```bash
export AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/documents
export AI_GOVERNANCE_INDEX_PATH=/path/to/index
export AI_GOVERNANCE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
export AI_GOVERNANCE_SEMANTIC_WEIGHT=0.6
```

**Context Engine Server environment variables:**

```bash
export AI_CONTEXT_ENGINE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
export AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS=384
export AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT=0.6
export AI_CONTEXT_ENGINE_INDEX_PATH=~/.context-engine/indexes
export AI_CONTEXT_ENGINE_INDEX_MODE=realtime    # 'ondemand' or 'realtime' (file watcher)
export AI_CONTEXT_ENGINE_READONLY=auto          # 'true', 'false', or 'auto' (sandbox detection)
```

## Context Engine Server

The Context Engine is a separate MCP server that provides semantic search across your project's source code and documents. It complements the Governance Server by providing project-specific content awareness.

| Aspect | Governance Server | Context Engine |
|--------|------------------|----------------|
| Content | Governance principles & methods | Your project's files |
| Index | Pre-built, ships with image | Built per-project on first use |
| Purpose | "What should I do?" | "What exists and where?" |

**Quick setup** (ask your AI coding assistant to run these):

```bash
claude mcp add ai-context-engine -- python -m ai_governance_mcp.context_engine.server
context-engine-service install --projects /path/to/your/project
context-engine-service status
```

The watcher daemon keeps indexes fresh automatically. It auto-restarts every ~12h (configurable via `--max-uptime-hours`) to flush the PyTorch CPU allocator cache. Platform-specific service installation: LaunchAgent (macOS), systemd user service (Linux), Task Scheduler (Windows).

**Sandboxed environments (Cowork, Docker, CI):** the engine auto-detects read-only filesystems and enters read-only mode — queries work against pre-built indexes; writes are blocked. Pattern: *index once, query everywhere*. Build indexes from a writable environment; all environments query the same indexes at `~/.context-engine/indexes/`.

**Features:** file watcher with debounce/cooldown, circuit breaker on consecutive failures, hybrid search (semantic + keyword), code/markdown/PDF/spreadsheet/image support, `.contextignore` file support, atomic file writes, corrupt file recovery, LRU project eviction.

## Troubleshooting

**"0 domains" or empty principles:** CLI and Desktop configs are separate systems. Check both have `AI_GOVERNANCE_DOCUMENTS_PATH` and `AI_GOVERNANCE_INDEX_PATH` set (pip installs only; Docker bakes paths into the image).

**S-Series false positives:** `evaluate_governance` flags safety-adjacent keywords in `planned_action` text. If `s_series_check.principles` is empty but `triggered=true`, the trigger is keyword-only — document the override in your reasoning trace and proceed.

**CI failing on hook tests:** hooks require shell matching `Bash|Edit|Write`. Verify `.claude/settings.json` PreToolUse matcher includes all three.

**Index stale after document edit:** the extractor rebuilds the full index in ~30 seconds. For incremental updates during development, restart the MCP server — indexes are in-memory and reload on server start.

## Project Structure

```
ai-governance-mcp/
├── src/ai_governance_mcp/
│   ├── models.py            # Pydantic data structures
│   ├── config.py            # Settings management
│   ├── extractor.py         # Document parsing + embeddings
│   ├── retrieval.py         # Hybrid search engine
│   ├── server.py            # Governance MCP server + 13 tools
│   ├── config_generator.py  # Multi-platform MCP configs
│   ├── validator.py         # Principle ID validation
│   └── context_engine/      # Context Engine MCP (4 tools)
├── documents/               # Governance documents (Constitutional naming)
│   ├── constitution.md      # Meta-Principles (Articles I-IV, Bill of Rights)
│   ├── rules-of-procedure.md # Constitution Methods (amendment process, authoring)
│   ├── title-NN-domain.md   # Domain principles (Federal Statutes)
│   ├── title-NN-domain-cfr.md # Domain methods (Code of Federal Regulations)
│   └── domains.json         # Domain configurations
├── workflows/               # Operational procedures (completion sequence, compliance review)
├── reference-library/       # Accumulating applied patterns (secondary authority)
├── .claude/
│   ├── agents/              # Installed subagents
│   └── hooks/               # Enforcement hooks (PreToolUse, UserPromptSubmit, pre-push)
├── index/                   # Generated index + embeddings
└── tests/                   # ~1300 tests across governance + context engine
```

## Dogfooding

This project is built using its own governance framework. Development follows the AI Coding framework (SPECIFY → PLAN → TASKS → IMPLEMENT) encoded in [`documents/title-10-ai-coding.md`](documents/title-10-ai-coding.md), with explicit gate criteria per phase. Decisions are logged through `evaluate_governance` + `log_governance_reasoning`. The framework's own hooks enforce governance consultation on source edits to this repo. Lessons from applying the framework to itself are captured in [`LEARNING-LOG.md`](LEARNING-LOG.md) — including corrections when the framework fails its own standards.

## Development

```bash
pip install -e ".[dev]"   # install dev dependencies
pre-commit install        # enable pre-commit hooks
```

**Test suite** covers governance (~90% coverage) and context engine (~65%). Run `pytest --collect-only -q | tail -1` for current count.

```bash
pytest tests/ -v                                           # full suite
pytest -m "not slow" tests/                                # fast tests only (skip real ML models)
pytest --cov=ai_governance_mcp --cov-report=html tests/    # coverage report
pytest -m real_index tests/                                # real-index tests only
```

Tests include real index validation and actual ML model tests (marked `@pytest.mark.slow`).

**Security scanning** (included in dev dependencies):

```bash
pip-audit       # scan dependencies for vulnerabilities
bandit -r src/  # scan source code for security issues
safety check    # check for known vulnerabilities
```

## Roadmap

**Distribution & Deployment**
- [x] Docker containerization with security hardening
- [x] Docker Hub publishing (`jason21wc/ai-governance-mcp:latest`)
- [ ] Public API with authentication

**Architecture Enhancements**
- [x] AI-driven modification assessment (hybrid: script-layer S-Series detection + AI-layer principle conflict analysis)
- [x] Improved method embedding quality (MRR 0.0 → 0.698)
- [x] Context Engine MCP server with watcher daemon
- [ ] Governance effectiveness measurement (see [BACKLOG.md](BACKLOG.md) #22 for scope)

**Content**
- [x] 7 active domains (constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd)
- [ ] Visual communication domain (presentations, reports, print design — see BACKLOG #6)
- [ ] Autonomous operations domain (see BACKLOG #11)

Full roadmap discussion and open questions live in [BACKLOG.md](BACKLOG.md).

## About

Built by Jason as a showcase of:
- **Semantic retrieval patterns** for knowledge-intensive applications
- **AI governance frameworks** for retrievable, enforceable governance principles
- **MCP integration** for extending AI assistant capabilities

The governance framework itself is the key innovation — the MCP server is its operational implementation.

*Built with the AI Governance Framework — Constitution, Rules of Procedure, Title 10 (AI Coding), Title 15 (UI/UX), Title 20 (Multi-Agent), Title 25 (KM&PD), Title 30 (Storytelling), Title 40 (Multimodal RAG). See [`documents/domains.json`](documents/domains.json) for current versions.*

## License

This project uses dual licensing:

- **Source code** (`src/`, `tests/`, `scripts/`, build files): [Apache License 2.0](LICENSE)
- **Framework content** (`documents/`, `index/`): [CC BY-NC-ND 4.0](LICENSE-CONTENT) — Copyright (c) 2026 Jason Collier
