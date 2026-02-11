# Specification

**Project:** AI Governance MCP Server
**Version:** 1.7.0
**Status:** Complete

> **Staleness warning:** This file is a point-in-time snapshot from v1.7.0. For current information:
> - **User-facing setup**: See `README.md` (authoritative)
> - **Architecture details**: See `ARCHITECTURE.md` (authoritative)
> - **Live metrics**: Run `pytest --cov`, `pytest --collect-only -q`, or see `tests/benchmarks/`
> - **Index counts**: See `SESSION-STATE.md` Quick Reference
>
> Metrics and counts below may have drifted from current values.

> Defines WHAT the system does and for whom. For HOW it works, see ARCHITECTURE.md.
> For user-facing setup and usage, see README.md.

---

## Problem Statement

AI assistants lack structured access to domain-specific governance principles. Without guidance, they hallucinate requirements, skip validation steps, apply inconsistent approaches, and miss safety considerations.

Loading full governance documents (~55K+ tokens) into context is wasteful and often exceeds limits. Simple keyword search misses semantically related concepts. There is no standardized way to deliver governance principles to AI assistants at query time with low latency.

## User Personas

| Persona | Role | Primary Need |
|---------|------|--------------|
| **AI Assistants** | Primary consumer | Retrieve relevant governance principles in real time (<100ms) to guide actions |
| **Developers** | Configure and extend | Set up the MCP server, add domains, tune retrieval, write connectors |
| **Organizations** | Deploy governance at scale | Enforce consistent AI behavior across teams and platforms via Docker |

## Features

### Governance Server (11 tools)

- **Hybrid retrieval** -- BM25 keyword search + dense semantic vectors with weighted score fusion (60/40)
- **Cross-encoder reranking** -- Top-20 candidates refined by cross-encoder model
- **Smart domain routing** -- Query embedding similarity identifies relevant knowledge domains
- **Pre-action compliance** (`evaluate_governance`) -- Returns PROCEED / PROCEED_WITH_MODIFICATIONS / ESCALATE
- **Post-action audit** (`verify_governance_compliance`) -- Returns COMPLIANT / NON_COMPLIANT / PARTIAL
- **S-Series safety enforcement** -- Deterministic keyword detection; S-Series violations force ESCALATE
- **Governance reasoning audit trail** (`log_governance_reasoning`) -- Per-principle reasoning traces
- **Principle lookup** (`get_principle`) -- Full content by ID for both principles and methods
- **Domain exploration** (`list_domains`, `get_domain_summary`) -- Domain stats and summaries
- **Quality tracking** (`log_feedback`, `get_metrics`) -- Feedback collection and analytics
- **Subagent installation** (`install_agent`, `uninstall_agent`) -- Orchestrator agent for Claude Code

### Context Engine Server (4 tools)

- **Project-level semantic search** (`query_project`) -- Hybrid search across project source code and documents
- **On-demand indexing** (`index_project`) -- Trigger re-index of current project (rate-limited: 5/min)
- **Multi-project management** (`list_projects`, `project_status`) -- Per-project indexes, auto-detected by working directory
- **File watching** -- Real-time index updates with circuit breaker and bounded pending changes
- **Pluggable connectors** -- Code (tree-sitter), markdown/text, PDF, spreadsheet, image metadata
- **`.contextignore` support** -- Same syntax as `.gitignore`

### Governance Framework (5 domains — see README.md for current counts)

| Domain | Coverage |
|--------|----------|
| Constitution | Universal AI behavior, safety, quality |
| AI Coding | Software development, testing, deployment |
| Multi-Agent | Agent orchestration, handoffs, evaluation |
| Storytelling | Creative writing, narrative, voice preservation |
| Multimodal RAG | Image retrieval, visual presentation |

## Scope Boundaries

### In Scope

- Semantic retrieval of governance principles and methods via MCP protocol
- Pre-action and post-action governance compliance checking
- Offline index building from markdown source documents
- Hybrid search (BM25 + semantic) with cross-encoder reranking
- Multi-domain routing with S-Series safety prioritization
- Project-level code and document indexing (Context Engine)
- Docker-based distribution for cross-platform deployment
- Multi-platform MCP client configuration generation

### Out of Scope

- **No content generation** -- Retrieval only; does not generate or modify governance text
- **No authentication** (v1) -- No user auth, API keys, or access control
- **No persistent storage beyond files** -- In-memory index loaded from JSON + NumPy at startup
- **No multi-user scaling** (v1) -- Single-process, in-memory; vector DB deferred to future
- **No server-side enforcement** -- Governance is advisory; true enforcement requires wrapper/gateway (deferred)
- **No ARM64 Docker images** -- AMD64 only; Apple Silicon uses Rosetta 2

## Success Criteria

| Metric | Target | Achieved |
|--------|--------|----------|
| Retrieval miss rate | <1% | <1% (hybrid retrieval) |
| Query latency | <100ms | ~50ms typical |
| Token savings vs. full context | >90% | ~98% (1-3K vs 55K+) |
| Test coverage (governance) | 80% | ~90% |
| Method MRR | >= 0.60 | See `tests/benchmarks/` for current |
| Principle MRR | >= 0.50 | See `tests/benchmarks/` for current |
| Method Recall@10 | >= 0.75 | See `tests/benchmarks/` for current |
| Principle Recall@10 | >= 0.85 | See `tests/benchmarks/` for current |
| Model load time | <= 15s | ~9s |

## Constraints

| Constraint | Detail |
|------------|--------|
| **Latency** | <100ms per query after model load (~9s cold start) |
| **Memory** | Entire index held in-memory (JSON + NumPy arrays) |
| **Python** | 3.10+ required (type hint syntax) |
| **Transport** | MCP stdio transport (JSON-RPC over stdin/stdout) |
| **Docker** | AMD64 architecture only |
| **Index size** | See `tests/benchmarks/` for current totals across 5 domains |
| **Embedding model** | BAAI/bge-small-en-v1.5, 384 dimensions, 512 token limit |
| **Rate limits** | `index_project` capped at 5 requests/minute |
| **Stdout** | Reserved for JSON-RPC; all logging to stderr |

## Assumptions

- Index is built offline via `python -m ai_governance_mcp.extractor` before server start
- MCP stdio transport is the delivery mechanism (no HTTP server in v1)
- Single-process deployment; no horizontal scaling
- Source documents are markdown files in the `documents/` directory
- MCP server is restarted after index rebuilds (cached at startup)
- AI clients support the MCP protocol (Claude, Cursor, Windsurf, ChatGPT, Gemini, etc.)
- Docker users accept AMD64 emulation on ARM64 platforms
