# AI Governance MCP Server

[![CI](https://github.com/jason21wc/ai-governance-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jason21wc/ai-governance-mcp/actions/workflows/ci.yml)

> **A semantic retrieval system that gives AI assistants access to domain-specific governance principles - a "second brain" for consistent, high-quality AI collaboration.**

## The Problem

AI assistants are powerful, but without structured guidance they can:
- Hallucinate requirements instead of asking for clarification
- Skip validation steps in complex workflows
- Apply inconsistent approaches across similar problems
- Miss critical safety considerations

Loading full governance documents (~55K+ tokens) into context is wasteful and often exceeds limits. Simple keyword search misses semantically related concepts.

## The Solution

This MCP server provides **hybrid semantic retrieval** of governance principles:

- **<1% miss rate** through combined keyword + semantic search
- **<100ms latency** for real-time retrieval during conversations
- **Smart domain routing** automatically identifies relevant knowledge domains
- **Cross-encoder reranking** ensures the most relevant principles surface first

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

## Key Innovation

**The Governance Framework**: Most people use AI as-is. This project implements a systematic governance framework that makes AI collaboration repeatable and production-ready - then operationalizes it through an MCP server.

The framework has three layers:
1. **Constitution** - Universal behavioral rules (safety, honesty, quality)
2. **Domain Principles** - Context-specific guidance (coding, multi-agent, storytelling)
3. **Methods** - Procedural workflows (Specify → Plan → Tasks → Implement)

### Available Domains

<!-- Verify counts: python -c "import json; d=json.load(open('index/global_index.json'))['domains']; [print(f'{k}: {len(v.get(\"principles\",[]))}p, {len(v.get(\"methods\",[]))}m') for k,v in d.items()]" -->
| Domain | Principles | Methods | Coverage |
|--------|------------|---------|----------|
| **Constitution** | 44 | 132 | Universal AI behavior, safety, quality |
| **AI Coding** | 12 | 142 | Software development, testing, deployment |
| **Multi-Agent** | 14 | 43 | Agent orchestration, handoffs, evaluation |
| **Storytelling** | 17 | 20 | Creative writing, narrative, voice preservation |
| **Multimodal RAG** | 12 | 21 | Image retrieval, visual presentation, inline visuals |

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Server | FastMCP | Official MCP SDK |
| Embeddings | sentence-transformers | Semantic similarity |
| Keyword Search | rank-bm25 | BM25 keyword matching |
| Reranking | CrossEncoder | Result refinement |
| Data Models | Pydantic | Validation & typing |
| Storage | In-memory (NumPy) | Fast retrieval |

## Architecture

```
Build Time:
  documents/*.md → extractor.py → global_index.json + embeddings.npy

Runtime:
  Query → Domain Router → Hybrid Search → Reranker → Hierarchy Filter → Results
          (semantic)    (BM25+semantic)  (cross-encoder)
```

### Retrieval Pipeline

1. **Domain Routing** - Query embedding similarity identifies relevant domains
2. **Hybrid Search** - BM25 (keywords) + dense vectors (semantic) in parallel
3. **Score Fusion** - Weighted combination (60% semantic, 40% keyword)
4. **Reranking** - Cross-encoder scores top 20 candidates
5. **Hierarchy Filter** - S-Series (safety) always prioritized

## How It Works

### 15 MCP Tools (2 Servers)

**Governance Server (11 tools):**

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
| `install_agent` | Install Orchestrator agent (Claude Code only) |
| `uninstall_agent` | Remove installed agent |
| `log_governance_reasoning` | Record per-principle reasoning traces for audit |

**Context Engine Server (4 tools):**

| Tool | Purpose |
|------|---------|
| `query_project` | Semantic + keyword search across project content |
| `index_project` | Trigger re-index of current project |
| `list_projects` | Show all indexed projects |
| `project_status` | Index stats for current project |

**Governance Enforcement:**

The `evaluate_governance` tool implements pre-action compliance checking:
- Evaluates planned actions against principles BEFORE execution
- Auto-detects S-Series (safety) concerns via keyword scanning
- Returns PROCEED, PROCEED_WITH_MODIFICATIONS, or ESCALATE
- S-Series violations force ESCALATE with human review required
- Logs audit trail with unique `audit_id` for tracking

The `verify_governance_compliance` tool enables post-action auditing:
- Checks if governance was consulted for a completed action
- Returns COMPLIANT, NON_COMPLIANT, or PARTIAL
- Catches bypassed governance checks after the fact

**Subagent Installation (Claude Code):**

The `install_agent` tool provides structural governance enforcement for Claude Code:
- Installs the Orchestrator subagent definition to `.claude/agents/orchestrator.md`
- Orchestrator has restricted tools (read + governance only, no edit/write/bash)
- Ensures `evaluate_governance()` is called before any action not on the skip list (reads, non-sensitive questions, trivial formatting)
- Other platforms receive governance via SERVER_INSTRUCTIONS (no installation needed)

### Example Usage

```python
# In your AI assistant's MCP configuration
{
  "mcpServers": {
    "ai-governance": {
      "command": "python",
      "args": ["-m", "ai_governance_mcp.server"]
    }
  }
}
```

```
User: "I need to implement a login system"

AI uses query_governance("implementing authentication system")
→ Returns coding-quality-security-by-default + coding-context-specification-completeness
→ AI knows to: verify security requirements, ask about auth method preferences
```

## Results

| Metric | Target | Achieved |
|--------|--------|----------|
| Miss Rate | <1% | <1% (hybrid retrieval) |
| Latency | <100ms | ~50ms typical |
| Token Savings | >90% | ~98% (1-3K vs 55K+) |
| Test Coverage | 80% | **~90%** governance, **~65%** context engine (500+ tests) |

## Quick Start (Docker)

<details>
<summary><b>Windows Step-by-Step</b></summary>

### Step 1: Install Docker Desktop

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows**
3. Run the installer and follow the prompts
4. Restart your computer when prompted
5. Open Docker Desktop and wait for it to fully start (whale icon appears in taskbar)

### Step 2: Pull the Image

1. In Docker Desktop, click the **Search** bar at the top
2. Type: `jason21wc/ai-governance-mcp`
3. Click **Pull** next to the result

### Step 3: Edit Claude Desktop Config

1. Open **File Explorer**
2. Click the address bar and paste: `%APPDATA%\Claude`
3. Press Enter
4. Right-click `claude_desktop_config.json` → **Open with** → **Notepad**

### Step 4: Add the MCP Server

Find the line that says `"mcpServers": {`

Add a comma `,` after the `}` of the last server entry, then paste this on a new line:

```json
    "ai-governance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "jason21wc/ai-governance-mcp:latest"]
    }
```

**Example** — if your file looks like this:
```json
{
  "mcpServers": {
    "other-server": {
      "command": "something"
    }
  }
}
```

Change it to:
```json
{
  "mcpServers": {
    "other-server": {
      "command": "something"
    },
    "ai-governance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "jason21wc/ai-governance-mcp:latest"]
    }
  }
}
```

> **Note:** Don't forget the comma after the `}` of the previous server entry!

### Step 5: Save and Restart

1. Save the file (Ctrl+S)
2. Close and reopen Claude Desktop

### Step 6: Test It

Ask Claude: *"Query governance for handling incomplete specifications"*

</details>

<details>
<summary><b>macOS Step-by-Step</b></summary>

### Step 1: Install Docker Desktop

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Mac** (choose Apple Silicon or Intel)
3. Open the downloaded `.dmg` file
4. Drag Docker to Applications
5. Open Docker from Applications and wait for it to start (whale icon appears in menu bar)

### Step 2: Pull the Image

Open Terminal and run:
```bash
docker pull jason21wc/ai-governance-mcp:latest
```

### Step 3: Edit Claude Desktop Config

Open Terminal and run:
```bash
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 4: Add the MCP Server

Find the line that says `"mcpServers": {`

Add a comma `,` after the `}` of the last server entry, then paste this on a new line:

```json
    "ai-governance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "jason21wc/ai-governance-mcp:latest"]
    }
```

**Example** — if your file looks like this:
```json
{
  "mcpServers": {
    "other-server": {
      "command": "something"
    }
  }
}
```

Change it to:
```json
{
  "mcpServers": {
    "other-server": {
      "command": "something"
    },
    "ai-governance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "jason21wc/ai-governance-mcp:latest"]
    }
  }
}
```

> **Note:** Don't forget the comma after the `}` of the previous server entry!

### Step 5: Save and Restart

1. Save the file (Cmd+S)
2. Close and reopen Claude Desktop

### Step 6: Test It

Ask Claude: *"Query governance for handling incomplete specifications"*

</details>

<details>
<summary><b>Claude Code CLI (Quick)</b></summary>

```bash
docker pull jason21wc/ai-governance-mcp:latest
claude mcp add ai-governance -s user -- docker run -i --rm jason21wc/ai-governance-mcp:latest
```
</details>

<details>
<summary><b>Cursor / ChatGPT Desktop</b></summary>

1. Install Docker Desktop and pull the image (see Windows/macOS steps above)
2. Add to your MCP settings:

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
</details>

<details>
<summary><b>Windsurf</b></summary>

### Step 1: Install Docker Desktop

**Mac:**
1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Mac** (choose Apple Silicon or Intel based on your Mac)
3. Open the downloaded `.dmg` file
4. Drag Docker to Applications
5. Open Docker from Applications
6. Wait for Docker to fully start (whale icon stops animating in menu bar)

**Windows:**
1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows**
3. Run the installer and follow the prompts
4. Restart your computer when prompted
5. Open Docker Desktop and wait for it to fully start

### Step 2: Pull the Image

Open Terminal (Mac) or PowerShell (Windows) and run:
```bash
docker pull jason21wc/ai-governance-mcp:latest
```

Verify it downloaded:
```bash
docker images | grep ai-governance
```

### Step 3: Add the MCP Server to Windsurf

1. Open **Windsurf**
2. Look for the **plug icon** (MCP) in the top-right of the Cascade chat panel
3. Click the plug icon → **Configure** or **View raw config**
4. This opens the file `~/.codeium/windsurf/mcp_config.json`
5. Add this configuration (or merge with existing servers):

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

6. **Save the file** (Cmd+S on Mac, Ctrl+S on Windows)

### Step 4: Restart Windsurf

Close and reopen Windsurf for the MCP server to load.

### Step 5: Verify

Ask Cascade: *"Query governance for handling incomplete specifications"*

You should see the 11 governance tools available (query_governance, evaluate_governance, etc.)

> **Note:** Windsurf has a 100 tool limit across all MCPs. This server provides 11 tools.

</details>

<details>
<summary><b>Perplexity / Grok / Google AI Studio (Web-based)</b></summary>

Web-based AI platforms require the MCP SuperAssistant browser extension.

1. Install [MCP SuperAssistant](https://github.com/srbhptl39/MCP-SuperAssistant) Chrome extension
2. Install Docker Desktop and pull the image:
   ```bash
   docker pull jason21wc/ai-governance-mcp:latest
   ```
3. Click the SuperAssistant extension icon in Chrome
4. Add MCP server with command:
   ```
   docker run -i --rm jason21wc/ai-governance-mcp:latest
   ```
5. Go to Perplexity/Grok/AI Studio and use governance tools through the extension
</details>

---

## Getting Started (Detailed)

### Option 1: Docker (Recommended)

The easiest way to run the MCP server. Everything is pre-built and ready to go.

```bash
# Pull the image
docker pull jason21wc/ai-governance-mcp:latest

# Test it works
docker run --rm jason21wc/ai-governance-mcp:latest python -c "print('Ready!')"
```

**Update to latest version:**
```bash
docker pull jason21wc/ai-governance-mcp:latest
```

### Option 2: Local Installation

For development or customization.

```bash
# Clone the repository
git clone https://github.com/jason21wc/ai-governance-mcp.git
cd ai-governance-mcp

# Install with dependencies
pip install -e .

# Build the index (first time)
python -m ai_governance_mcp.extractor
```

### Quick Test

```bash
# Test retrieval (local install)
python -m ai_governance_mcp.server --test "how do I handle incomplete specs"

# Test retrieval (Docker)
docker run --rm jason21wc/ai-governance-mcp:latest \
  python -m ai_governance_mcp.server --test "how do I handle incomplete specs"
```

### Run as MCP Server

```bash
# Local install
python -m ai_governance_mcp.server

# Docker
docker run -i --rm jason21wc/ai-governance-mcp:latest
```

### Platform Configuration

MCP is now supported across major AI platforms. **Use the config generator** for platform-specific setup—it auto-detects your installation path and generates the correct environment variables:

```bash
# Generate config for any platform (includes correct paths!)
python -m ai_governance_mcp.config_generator --platform gemini
python -m ai_governance_mcp.config_generator --platform claude
python -m ai_governance_mcp.config_generator --platform chatgpt
python -m ai_governance_mcp.config_generator --all  # Show all platforms

# Get JSON config for manual setup
python -m ai_governance_mcp.config_generator --json claude
```

> **Important for pip users**: The config generator automatically includes `AI_GOVERNANCE_INDEX_PATH` and `AI_GOVERNANCE_DOCUMENTS_PATH` environment variables. These are required when running the server from a different directory than the project root. Docker users don't need this—paths are baked into the image.

#### Gemini CLI

Use the command from the config generator, or:

```bash
# Add to user config (includes env vars for path resolution)
gemini mcp add -s user \
  --env AI_GOVERNANCE_DOCUMENTS_PATH="/path/to/ai-governance-mcp/documents" \
  --env AI_GOVERNANCE_INDEX_PATH="/path/to/ai-governance-mcp/index" \
  ai-governance python -m ai_governance_mcp.server
```

Restart Gemini CLI after configuration.

#### Claude Code CLI

Use the command from the config generator, or:

```bash
# Global installation (includes env vars for path resolution)
claude mcp add ai-governance -s user \
  --env AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/ai-governance-mcp/documents \
  --env AI_GOVERNANCE_INDEX_PATH=/path/to/ai-governance-mcp/index \
  -- python -m ai_governance_mcp.server
```

> **Note:** Claude Code CLI and Claude Desktop have **separate** MCP configurations. If you use both, configure each one independently. See [Troubleshooting](#troubleshooting) for details.

#### Claude Desktop App

Edit the config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Use the output from `python -m ai_governance_mcp.config_generator --json claude` which includes the correct paths, or manually add:

```json
{
  "mcpServers": {
    "ai-governance": {
      "command": "python",
      "args": ["-m", "ai_governance_mcp.server"],
      "env": {
        "AI_GOVERNANCE_DOCUMENTS_PATH": "/path/to/ai-governance-mcp/documents",
        "AI_GOVERNANCE_INDEX_PATH": "/path/to/ai-governance-mcp/index"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

#### ChatGPT Desktop (Developer Mode)

1. Open ChatGPT Desktop → Settings → Developer Mode (enable)
2. Get config: `python -m ai_governance_mcp.config_generator --json chatgpt`
3. Add the MCP server configuration (includes env vars for path resolution)

#### Cursor

Cursor has native MCP support. Get config: `python -m ai_governance_mcp.config_generator --json cursor`

See [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol) for details.

#### Windsurf

Windsurf supports MCP through Cascade. Configuration file: `~/.codeium/windsurf/mcp_config.json`

**Docker (recommended—no path configuration needed):**
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

**Local install:** Get config with `python -m ai_governance_mcp.config_generator --json windsurf`

**Access the config:**
1. In Cascade chat, click the hammer icon (MCP servers)
2. Click **Configure** → **View raw config**
3. Or directly edit `~/.codeium/windsurf/mcp_config.json`

See [Windsurf MCP Documentation](https://docs.windsurf.com/windsurf/cascade/mcp) for details.

#### Perplexity, Grok, Google AI Studio (Web-based)

Use the [MCP SuperAssistant Chrome Extension](https://github.com/srbhptl39/MCP-SuperAssistant) to bridge MCP to web-based AI platforms.

Supported platforms via SuperAssistant:
- Grok
- Perplexity
- Google AI Studio
- OpenRouter
- DeepSeek
- Mistral AI
- And more...

### Environment Variables

**Governance Server:**
```bash
export AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/documents
export AI_GOVERNANCE_INDEX_PATH=/path/to/index
export AI_GOVERNANCE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
export AI_GOVERNANCE_SEMANTIC_WEIGHT=0.6
```

**Context Engine Server:**
```bash
export AI_CONTEXT_ENGINE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
export AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS=384
export AI_CONTEXT_ENGINE_SEMANTIC_WEIGHT=0.6
export AI_CONTEXT_ENGINE_INDEX_PATH=~/.context-engine/indexes
export AI_CONTEXT_ENGINE_LOG_LEVEL=INFO
```

### Context Engine Server

The Context Engine is a separate MCP server that provides semantic search across your project's source code and documents. It complements the Governance Server by providing project-specific content awareness.

**Running the Context Engine:**

```bash
# Run standalone
python -m ai_governance_mcp.context_engine.server

# Or add to your MCP client config alongside governance server
```

**MCP Client Configuration (Claude Code):**

```bash
claude mcp add ai-context-engine -- python -m ai_governance_mcp.context_engine.server
```

**Features:**
- Auto-indexes current working directory on first query
- File watcher for real-time index updates (code projects)
- Hybrid search (semantic + keyword) with configurable weights
- Support for code, markdown, PDF, spreadsheet, and image metadata
- `.contextignore` file support (same syntax as `.gitignore`)

**How it differs from Governance Server:**
| Aspect | Governance Server | Context Engine |
|--------|------------------|----------------|
| Content | Governance principles & methods | Your project's files |
| Index | Pre-built, ships with image | Built per-project on first use |
| Purpose | "What should I do?" | "What exists and where?" |

### Troubleshooting

#### "0 domains" or Empty Principles

If the server connects but returns no data, the paths aren't configured correctly.

**Quick diagnostic checklist:**

```bash
# 1. Is MCP connected?
claude mcp list

# 2. Are env vars set? (check Environment section in output)
claude mcp get ai-governance

# 3. Are paths resolving correctly?
python -c "
from ai_governance_mcp.config import Settings
s = Settings()
print(f'documents_path: {s.documents_path}')
print(f'index_path: {s.index_path}')
print(f'index exists: {(s.index_path / \"global_index.json\").exists()}')
"

# 4. Does the index exist?
ls /path/to/ai-governance-mcp/index/global_index.json
```

**Common causes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Empty `Environment:` in `claude mcp get` | Env vars not set | Re-add with `-e` flags |
| `index exists: False` | Wrong path | Check `AI_GOVERNANCE_INDEX_PATH` |
| Works in Desktop, not CLI | Separate configs | Configure both (see below) |

**Important: Desktop and CLI have separate configs**

Claude Desktop and Claude Code CLI maintain independent MCP configurations:

| Application | Config Location |
|-------------|-----------------|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code CLI | `~/.claude.json` (user scope via `claude mcp add -s user`) |

Configuring one does **not** configure the other. If you use both, add the MCP server to each.

**Fix for CLI:**
```bash
claude mcp remove ai-governance -s user
claude mcp add ai-governance -s user \
  -e AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/ai-governance-mcp/documents \
  -e AI_GOVERNANCE_INDEX_PATH=/path/to/ai-governance-mcp/index \
  -- python -m ai_governance_mcp.server
```

**Restart your session** after any config change—MCP configs are loaded at session start.

## Project Structure

```
ai-governance-mcp/
├── src/ai_governance_mcp/
│   ├── models.py            # Pydantic data structures
│   ├── config.py            # Settings management
│   ├── extractor.py         # Document parsing + embeddings
│   ├── retrieval.py         # Hybrid search engine
│   ├── server.py            # Governance MCP server + 11 tools
│   ├── config_generator.py  # Multi-platform MCP configs
│   ├── validator.py         # Principle ID validation
│   └── context_engine/      # Context Engine MCP server
│       ├── server.py        # Context Engine server + 4 tools
│       ├── project_manager.py # Multi-project management
│       ├── indexer.py       # Core indexing pipeline
│       ├── watcher.py       # File system watcher
│       ├── models.py        # Context engine data models
│       ├── connectors/      # Pluggable content parsers
│       │   ├── code.py      # Code parsing (tree-sitter)
│       │   ├── document.py  # Markdown/text parsing
│       │   ├── pdf.py       # PDF extraction
│       │   ├── spreadsheet.py # CSV/Excel parsing
│       │   └── image.py     # Image metadata extraction
│       └── storage/
│           └── filesystem.py # Local filesystem storage
├── documents/               # Governance documents
│   └── domains.json         # Domain configurations
├── index/                   # Generated index + embeddings
├── logs/                    # Query + feedback logs
└── tests/
    ├── conftest.py                  # Shared fixtures
    ├── test_models.py               # Model validation
    ├── test_config.py               # Config tests
    ├── test_server.py               # Server unit tests
    ├── test_server_integration.py   # Dispatcher + flows
    ├── test_extractor.py            # Extractor tests
    ├── test_extractor_integration.py # Pipeline tests
    ├── test_retrieval.py            # Retrieval unit
    ├── test_retrieval_integration.py # Retrieval pipeline
    ├── test_retrieval_quality.py    # MRR/Recall benchmarks
    ├── test_config_generator.py     # Platform configs
    ├── test_validator.py            # Principle validation
    └── test_context_engine.py       # Context engine tests
```

## The Methodology

This project follows the AI Coding Methods framework:

1. **SPECIFY** - Requirements discovery with Product Owner
2. **PLAN** - Architecture and technology selection
3. **TASKS** - Decomposition into testable units
4. **IMPLEMENT** - Code with continuous validation

Each phase has explicit gate criteria before proceeding. This ensures:
- No implementation without validated requirements
- Clear architectural decisions documented
- Traceable progress through the codebase

## Development

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Enable pre-commit hooks (auto-formats code on commit)
pre-commit install
```

### Test Suite

500+ tests covering governance (~90% coverage) and context engine (~65%):

| Category | Purpose |
|----------|---------|
| Governance Unit | Isolated component testing (models, config, server, extractor, retrieval, validator) |
| Governance Integration | Full pipeline flows (dispatcher, retrieval pipeline, extractor pipeline) |
| Context Engine | Models, connectors, indexer, watcher, server, security |

Tests include real index validation and actual ML model tests (marked `@pytest.mark.slow`).

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest --cov=ai_governance_mcp --cov-report=html tests/

# Fast tests only (skip ML models)
pytest -m "not slow" tests/

# Real index tests only
pytest -m real_index tests/
```

### Security Scanning

Security tools are included in dev dependencies:

```bash
# Scan dependencies for vulnerabilities
pip-audit

# Scan source code for security issues
bandit -r src/

# Check for known vulnerabilities
safety check
```

## Roadmap

**Distribution & Deployment**
- [x] Docker containerization with security hardening ✓
- [x] Docker Hub publishing ✓ — `jason21wc/ai-governance-mcp:latest`
- [ ] Public API with authentication

**Architecture Enhancements**
- [x] AI-driven modification assessment (hybrid approach) ✓
  - Script layer: S-Series keyword detection (deterministic safety guardrails)
  - AI layer: Nuanced principle conflict analysis for PROCEED_WITH_MODIFICATIONS
  - Model-aware: More capable models get more judgment latitude
- [x] **Improved Method Embedding Quality** ✓ — MRR 0.0 → 0.698
  - [x] Content-based keyword extraction (via MethodMetadata: purpose_keywords, applies_to, guideline_keywords; legacy `keywords` field remains title-derived)
  - [x] Increase embedding text limit (1000/500 → 1500 chars)
  - [x] Add trigger_phrase support for methods (like principles have)
- [ ] **Governance Proxy Mode** — Platform-agnostic enforcement via MCP gateway
  - Wraps other MCP servers, enforces governance before forwarding requests
  - Enables architectural enforcement for non-Claude platforms (OpenAI, Gemini, etc.)
  - Integrates with Lasso MCP Gateway, Envoy AI Gateway, or custom proxy
  - See §4.6.2 in multi-agent-methods for pattern documentation
- [ ] Multi-agent orchestration (specialized agents using this MCP)
- [ ] Vector database for multi-user scaling
- [ ] GraphRAG for relationship-aware retrieval
- [ ] Active learning from feedback

## About

Built by Jason as a showcase of:
- **Semantic retrieval patterns** for knowledge-intensive applications
- **AI governance frameworks** for production-quality AI collaboration
- **MCP integration** for extending AI assistant capabilities

The governance framework itself is the key innovation - the MCP server is its operational implementation.

---

*Built with the AI Governance Framework - Constitution v2.4, AI Coding Methods v2.7.0, Governance Methods v3.7.0, Multi-Agent Methods v2.10.0, Storytelling v1.0.0, Multimodal RAG v1.0.0*
