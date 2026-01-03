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
```

## Key Innovation

**The Governance Framework**: Most people use AI as-is. This project implements a systematic governance framework that makes AI collaboration repeatable and production-ready - then operationalizes it through an MCP server.

The framework has three layers:
1. **Constitution** - Universal behavioral rules (safety, honesty, quality)
2. **Domain Principles** - Context-specific guidance (coding, multi-agent, etc.)
3. **Methods** - Procedural workflows (Specify → Plan → Tasks → Implement)

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

### 10 MCP Tools

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

**Agent Installation (Claude Code):**

The `install_agent` tool provides structural governance enforcement for Claude Code:
- Installs the Orchestrator agent to `.claude/agents/orchestrator.md`
- Orchestrator has restricted tools (read + governance only, no edit/write/bash)
- Ensures `evaluate_governance()` is called before significant actions
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
| Test Coverage | 80% | **90%** (279 tests) |

## Getting Started

### Option 1: Docker (Recommended)

The easiest way to run the MCP server. Everything is pre-built and ready to go.

```bash
# Pull the image
docker pull jason21wc/ai-governance-mcp:latest

# Test it works
docker run --rm jason21wc/ai-governance-mcp:latest python -c "print('Ready!')"
```

**Configure your AI client** (add to your MCP settings):

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

MCP is now supported across major AI platforms. Use the config generator for platform-specific setup:

```bash
# Generate config for any platform
python -m ai_governance_mcp.config_generator --platform gemini
python -m ai_governance_mcp.config_generator --platform claude
python -m ai_governance_mcp.config_generator --platform chatgpt
python -m ai_governance_mcp.config_generator --all  # Show all platforms
```

#### Gemini CLI

```bash
# Add to user config (available in all projects)
gemini mcp add -s user ai-governance python -m ai_governance_mcp.server

# Or manually add to ~/.gemini/settings.json
```

```json
{
  "mcpServers": {
    "ai-governance": {
      "command": "python",
      "args": ["-m", "ai_governance_mcp.server"],
      "timeout": 30000
    }
  }
}
```

Restart Gemini CLI after configuration.

#### Claude Code CLI

```bash
# Global installation (available in all projects)
claude mcp add ai-governance -s user -- python -m ai_governance_mcp.server

# With environment variables
claude mcp add ai-governance -s user \
  --env AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/documents \
  --env AI_GOVERNANCE_INDEX_PATH=/path/to/index \
  -- python -m ai_governance_mcp.server
```

#### Claude Desktop App

Edit the config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop after saving.

#### ChatGPT Desktop (Developer Mode)

1. Open ChatGPT Desktop → Settings → Developer Mode (enable)
2. Add MCP server configuration:

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

#### Cursor

Cursor has native MCP support. Add to your Cursor settings:

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

See [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol) for details.

#### Windsurf

Windsurf supports MCP through Cascade. Add to your Windsurf MCP configuration:

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

See [Windsurf MCP Documentation](https://docs.windsurf.com/windsurf/cascade/mcp) for details.

#### Other Platforms (Grok, Perplexity, Google AI Studio)

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

```bash
export AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/documents
export AI_GOVERNANCE_INDEX_PATH=/path/to/index
export AI_GOVERNANCE_EMBEDDING_MODEL=all-MiniLM-L6-v2
export AI_GOVERNANCE_SEMANTIC_WEIGHT=0.6
```

## Project Structure

```
ai-governance-mcp/
├── src/ai_governance_mcp/
│   ├── models.py        # Pydantic data structures
│   ├── config.py        # Settings management
│   ├── extractor.py     # Document parsing + embeddings
│   ├── retrieval.py     # Hybrid search engine
│   └── server.py        # MCP server + tools
├── documents/           # Governance documents
│   └── domains.json     # Domain configurations
├── index/               # Generated index + embeddings
├── logs/                # Query + feedback logs
└── tests/
    ├── conftest.py      # Shared fixtures
    ├── test_models.py   # Model validation (35 tests)
    ├── test_config.py   # Config tests (17 tests)
    ├── test_server.py   # Server unit tests (71 tests)
    ├── test_server_integration.py   # Dispatcher + flows (11 tests)
    ├── test_extractor.py            # Extractor tests (45 tests)
    ├── test_extractor_integration.py # Pipeline tests (11 tests)
    ├── test_retrieval.py            # Retrieval unit (36 tests)
    ├── test_retrieval_integration.py # Retrieval pipeline (21 tests)
    ├── test_config_generator.py     # Platform configs (17 tests)
    └── test_validator.py            # Principle validation (15 tests)
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

279 tests across 10 test files with 90% coverage:

| Category | Tests | Purpose |
|----------|-------|---------|
| Unit | 236 | Isolated component testing |
| Integration | 43 | Full pipeline flows |

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
- [ ] Docker Hub publishing (pending secrets setup)
- [ ] Public API with authentication

**Architecture Enhancements**
- [x] AI-driven modification assessment (hybrid approach) ✓
  - Script layer: S-Series keyword detection (deterministic safety guardrails)
  - AI layer: Nuanced principle conflict analysis for PROCEED_WITH_MODIFICATIONS
  - Model-aware: More capable models get more judgment latitude
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

*Built with the AI Governance Framework - Constitution v2.1, Methods v3.3.0*
