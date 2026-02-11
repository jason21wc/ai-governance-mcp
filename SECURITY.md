# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.8.x   | :white_check_mark: |
| < 1.8   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the repository maintainer. You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include:
- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Model

### Threat Model

This project is an **MCP server that serves governance principles to AI agents**. This creates a unique security consideration: our documents become part of the trust chain for downstream AI systems.

#### Attack Surfaces

| Surface | Risk | Mitigation |
|---------|------|------------|
| **Document Poisoning** | Malicious content in `documents/` served to all AI clients | CI content scanning, PR review |
| **Agent Template Injection** | Compromised agent definitions via `install_agent` | Hash verification, user confirmation |
| **Fork-Based Attacks** | Malicious forks with modified CLAUDE.md or agent files | User awareness, official repo verification |
| **PR Content Injection** | Prompt injection hidden in legitimate-looking governance principles | CI scanning, multi-reviewer policy |
| **Docker Image Poisoning** | Compromised dependencies or content at build time | Dependency scanning, image signing (planned) |

### The ike.io Attack Pattern

In January 2026, researchers disclosed a VSCode/Cursor vulnerability where malicious `tasks.json` files could:
1. Execute arbitrary code when a folder is opened
2. Search for and inject into AI instruction files (`.cursor/rules`)
3. Hijack AI agents to exfiltrate secrets or sabotage code

**Our exposure:**
- We do NOT use `tasks.json` or auto-execution triggers
- Our `CLAUDE.md` and `.claude/agents/` ARE instruction files loaded by Claude Code
- Our `documents/` content is served to AI agents as authoritative guidance

**Our mitigations:**
- CI scanning for prompt injection patterns
- Content validation during index extraction
- Hash verification for agent templates
- No auto-execution files in repository

### Prompt Injection Considerations

As a governance document server, we must guard against prompt injection at multiple levels:

1. **In our documents**: Malicious instructions hidden in governance principles
2. **Via our server**: Compromised `SERVER_INSTRUCTIONS` or tool responses
3. **In agent templates**: Malicious behavior in installed subagents

#### What We Scan For

Our CI pipeline and extraction process scan for:

**CRITICAL Patterns (Hard-fail)**
- Prompt injection phrases ("ignore previous instructions", "you are now", etc.)
- Hidden HTML comments with instructions

**ADVISORY Patterns (Warning)**
- Shell commands (`curl`, `wget`, `bash`, `eval`, etc.)
- Base64 encoded content
- Data exfiltration patterns
- External URLs (flagged for review)

**Scanned Files**
- `documents/*.md` — Governance principles and methods
- `CLAUDE.md` — Project instructions
- `.claude/agents/*.md` — Agent templates
- `src/ai_governance_mcp/server.py` — SERVER_INSTRUCTIONS block
- `documents/domains.json` — Domain descriptions for semantic routing

**Security Hardening (v2)**
- CRITICAL patterns are detected even with "example" context (prevents bypass)
- Unicode NFKC normalization before pattern matching (prevents homoglyph attacks)
- Runtime validation of SERVER_INSTRUCTIONS at module load
- Domain descriptions scanned during extraction

## Security Features

### Implemented

- **Rate limiting**: Token bucket algorithm prevents DoS (governance server + context engine)
- **Thread-safe rate limiters**: Both governance and context engine rate limiters guarded by `threading.Lock`
- **Path traversal prevention**: Validated paths for log files, agent installation, and project indexes (hex-only IDs)
- **Log sanitization**: Secrets redacted from logs via regex patterns (6-pass sanitization)
- **Bounded audit log**: Memory-bounded deque prevents unbounded growth
- **Input validation**: Length limits on queries and parameters
- **Non-root Docker**: Container runs as `appuser`, not root
- **Agent allowlist**: Only approved agent names can be installed
- **Pre-flight validation**: Index extraction fails fast on configuration errors
- **Content security scanning**: CI and extraction scan for prompt injection patterns
- **Critical pattern blocking**: Prompt injection phrases hard-fail extraction
- **Example bypass protection**: CRITICAL patterns flagged even with "example" in context
- **Unicode normalization**: NFKC normalization prevents homoglyph attacks (Cyrillic 'а' → Latin 'a')
- **SERVER_INSTRUCTIONS validation**: Runtime check at module load to prevent compromised instructions
- **Domain description scanning**: Validates `domains.json` descriptions used for semantic routing
- **Symlink filtering**: Context engine skips symlinks in file discovery, project listing, and deletion
- **File size/count limits**: Context engine enforces 10MB per file, 10K files per project
- **Decompression bomb guard**: PIL `MAX_IMAGE_PIXELS` limit set at connector initialization
- **JSON-only serialization**: Context engine BM25 index uses JSON (not pickle), NumPy loaded with `allow_pickle=False`
- **Relative paths in output**: Context engine returns relative paths, not absolute filesystem paths
- **.env variant filtering**: `.env*` pattern excludes all environment file variants from indexing
- **RLock thread safety**: Context engine shared index state protected by reentrant lock
- **Error message sanitization**: Context engine strips paths, line numbers, and module paths from error responses to prevent information leakage
- **Bounded pending changes**: Context engine watcher limits pending file changes (MAX_PENDING_CHANGES=10K) with force-flush to prevent unbounded memory growth
- **Embedding model allowlist**: 6 vetted models; bypass requires explicit `AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true` (logged at WARNING)
- **Model mismatch detection**: Semantic search disabled when stored embeddings were generated by a different model than configured
- **PDF page limit**: MAX_PDF_PAGES (500) prevents memory exhaustion on huge documents
- **Ignore file size limit**: `.contextignore`/`.gitignore` capped at 1MB to prevent memory abuse
- **Watcher circuit breaker**: File watcher stops after 3 consecutive failures, prevents infinite retry loops
- **Atomic file writes**: JSON and embedding persistence uses tmp+rename pattern (POSIX atomic)
- **Corrupt file recovery**: All persistent file loads (JSON, NumPy) handle corruption with log+delete+fallback

### Known Limitations

> **IMPORTANT: Hash Verification is Advisory Only**
>
> The `install_agent` tool includes SHA-256 hash verification for agent templates.
> However, **this provides limited supply chain protection** because:
>
> 1. The expected hashes are stored in `server.py` in the same repository
> 2. An attacker who can modify `documents/agents/orchestrator.md` can also modify `AGENT_TEMPLATE_HASHES`
> 3. This is "the fox guarding the henhouse"
>
> **What hash verification DOES provide:**
> - Detection of accidental modifications
> - Awareness that content differs from expected
> - A forcing function for intentional updates
>
> **What it does NOT provide:**
> - Protection against supply chain attacks
> - Cryptographic integrity verification
> - Defense against compromised repositories
>
> For true supply chain security, use the planned cryptographic signing (see below).

### Planned

- [ ] Docker image signing with cosign
- [ ] Cryptographic signing of governance documents
- [x] SBOM (Software Bill of Materials) for releases — see `SBOM.md`

## For Users

### Verify You're Using the Official Repository

Before using this project, verify:
```bash
# Check remote URL
git remote get-url origin
# Should be: https://github.com/jason21wc/ai-governance-mcp.git

# Verify latest release signature (when available)
gh release view --repo jason21wc/ai-governance-mcp
```

### Safe Docker Usage

```bash
# Pull from official source
docker pull jason21wc/ai-governance-mcp:latest

# Run without sensitive mounts
docker run -i --rm jason21wc/ai-governance-mcp

# AVOID mounting sensitive directories
# BAD: docker run -v ~/.ssh:/data -i --rm jason21wc/ai-governance-mcp
```

### Review Agent Installations

When using `install_agent`:
1. Review the preview before confirming
2. Use `show_manual=true` to see full content
3. Check the installation path is expected
4. Restart Claude Code to activate

## For Contributors

### Document Changes

Changes to `documents/` require extra scrutiny:
1. CI will scan for suspicious patterns
2. Reviewers should verify no hidden instructions
3. External URLs must be justified
4. No shell commands in governance content

### Security Checklist for PRs

- [ ] No hardcoded secrets or credentials
- [ ] No shell commands in document content
- [ ] No external URLs without justification
- [ ] No prompt injection patterns
- [ ] Tests pass including security job
