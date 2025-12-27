# AI Governance MCP Server

An MCP (Model Context Protocol) server for retrieving AI governance principles and methods. Reduces full document loading (~55-65K tokens) to targeted retrieval (~1-3K tokens per query).

## Features

- **Multi-domain support**: Constitution, AI Coding, Multi-Agent domains
- **Automatic domain detection**: Queries trigger appropriate domain searches
- **S-Series priority**: Safety/ethics principles get supreme authority
- **Expanded keyword matching**: ~5% miss rate without heavy dependencies
- **9 specialized tools**: From basic retrieval to failure mode search

## Installation

```bash
pip install -e .
```

## Quick Start

### Run the MCP Server

```bash
python -m ai_governance_mcp.server
```

### Test Mode

```bash
python -m ai_governance_mcp.server --test "specification seems incomplete"
```

### Extract Documents

```bash
python -m ai_governance_mcp.extractor
```

## Tools

### Core Tools (1-5)

| Tool | Purpose |
|------|---------|
| `retrieve_governance` | Main retrieval - auto-detects domains, returns scored principles |
| `detect_domain` | Domain detection only - shows which domains match a query |
| `get_principle` | Get full content of a specific principle by ID |
| `list_principles` | List all available principles, optionally filtered by domain |
| `list_domains` | List all domains with statistics |

### Extended Tools (6-9)

| Tool | Purpose |
|------|---------|
| `refresh_index` | Re-extract documents after modification |
| `validate_hierarchy` | Check for conflicts between governance documents |
| `get_escalation_triggers` | List situations requiring human escalation |
| `search_by_failure` | Find principles by failure mode/symptom |

## Configuration

Set environment variables to customize:

```bash
export AI_GOVERNANCE_DOCUMENTS_PATH=/path/to/documents
export AI_GOVERNANCE_LOG_LEVEL=DEBUG
export AI_GOVERNANCE_AUDIT_ENABLED=true
```

Or create `documents/domains.json` to configure domains.

## Document Structure

```
documents/
├── domains.json                    # Domain registry
├── ai-interaction-principles.md    # Constitution
├── ai-coding-domain-principles.md  # AI Coding domain
├── ai-coding-methods.md           # AI Coding procedures
├── multi-agent-domain-principles.md
└── multi-agent-methods.md

index/                              # Generated indexes
├── constitution-index.json
├── ai-coding-index.json
└── multi-agent-index.json

cache/                              # Individual principle content
├── meta-C1.md
├── coding-C1.md
└── ...
```

## Scoring Algorithm

```python
score = (keyword_matches × 1.0) +
        (synonym_matches × 0.8) +
        (phrase_matches × 2.0) +
        (failure_indicator_matches × 1.5)

# S-Series principles get 10x multiplier when triggered
```

## Testing

```bash
pytest tests/ -v
```

## Architecture

```
Query → Domain Detection → Constitution Search (always) → Domain Search → Hierarchy Order → Response
```

## Project Memory Files

- `SESSION-STATE.md` - Current position, next actions
- `PROJECT-MEMORY.md` - Decisions, architecture, gotchas
- `LEARNING-LOG.md` - Lessons learned
- `FRAMEWORK-EVALUATION.md` - Meta-observations about framework effectiveness
