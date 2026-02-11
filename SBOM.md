# Software Bill of Materials (SBOM)

**Project:** ai-governance-mcp
**Version:** 1.7.0
**Generated:** 2026-02-07
**Python:** >=3.10
**License:** MIT
**Build System:** hatchling

## Core Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| mcp | 1.25.0 | MIT | MCP Python SDK (`mcp.server.Server`) |
| pydantic | 2.11.9 | MIT | Data validation and schemas |
| pydantic-settings | 2.11.0 | MIT | Settings management |
| sentence-transformers | 5.2.0 | Apache 2.0 | Embedding generation and cross-encoder reranking |
| rank-bm25 | 0.2.2 | Apache 2.0 | BM25 keyword search |
| numpy | 1.26.4 | BSD-3-Clause | Vector operations |
| requests | >=2.28.0 | Apache 2.0 | HTTP client (required by sentence-transformers) |

## Context Engine Dependencies (Optional)

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pathspec | >=1.0.0,<2 | MPL 2.0 | Gitignore-style pattern matching |
| watchdog | >=4.0.0 | Apache 2.0 | File system monitoring |
| tree-sitter | >=0.21.0 | MIT | Language-aware code parsing |
| pymupdf | >=1.24.0 | AGPL-3.0 | PDF extraction (primary) |
| pdfplumber | >=0.10.0 | MIT | PDF extraction (fallback) |
| openpyxl | >=3.1.0 | MIT | Excel file parsing |
| Pillow | >=10.0.0 | HPND | Image metadata extraction |

## Dev Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pytest | >=7.0.0 | MIT | Test framework |
| pytest-asyncio | >=0.21.0 | Apache 2.0 | Async test support |
| pytest-cov | >=4.0.0 | MIT | Coverage reporting |
| pip-audit | >=2.7.0 | Apache 2.0 | Dependency vulnerability scanning |
| bandit | >=1.7.0 | Apache 2.0 | Source code security scanning |
| safety | >=3.0.0 | MIT | Known vulnerability checking |
| ruff | 0.12.0 | MIT | Linting and formatting |
| pre-commit | >=4.0.0 | MIT | Git hook management |

## Build Platform

- **Docker Image:** `jason21wc/ai-governance-mcp:latest` (AMD64 only)
- **Base Image:** `python:3.11-slim`
- **PyTorch:** CPU-only (no CUDA)
- **Container User:** Non-root (`appuser`)
- **Image Size:** ~1.6GB

## Security Notes

- Zero known vulnerabilities (`pip-audit` — run `pip-audit` for current status)
- No hardcoded secrets or credentials in source
- All user input validated (query length limits, parameter bounds)
- Pickle deserialization disabled (`allow_pickle=False`)
- Docker runs as non-root user
