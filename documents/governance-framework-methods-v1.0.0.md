# Governance Framework Methods
## Operational Procedures for Framework Maintenance

**Version:** 1.0.0
**Status:** Active
**Effective Date:** 2025-12-27
**Governance Level:** Constitution Methods (implements meta-principles)

---

## Preamble

### Document Purpose

This document defines operational procedures for maintaining the AI Governance Framework itself. It translates constitutional principles into executable workflows for document versioning, index management, and framework evolution.

**Governance Hierarchy:**
```
+-------------------------------------------------------------+
|  ai-interaction-principles.md (CONSTITUTION)                |
|  Meta-Principles: Universal behavioral rules. Immutable.    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|  THIS DOCUMENT: governance-framework-methods.md             |
|  Constitution Methods: HOW to maintain the framework.       |
|  Procedures for versioning, indexing, and evolution.        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|  Domain Methods: ai-coding-methods.md, multi-agent-methods.md|
|  Domain-specific operational procedures.                     |
+-------------------------------------------------------------+
```

**Regulatory Authority:** These methods derive authority from Constitutional principles. They govern HOW the framework itself evolves while principles govern WHAT behavior is required.

**Relationship to Domain Methods:**
- **This Document** defines framework-level maintenance (applies to all domains)
- **Domain Methods** define domain-specific operations (apply within domains)
- **Constitution** governs both and resolves conflicts

### Importance Tags Legend

This document uses importance tags to enable efficient partial loading:

| Tag | Meaning | Loading Guidance |
|-----|---------|------------------|
| CRITICAL | Essential for document effectiveness | Always load |
| IMPORTANT | Significant value, not essential | Load when relevant |
| OPTIONAL | Nice to have, first to cut | Load on demand only |

### Legal System Analogy

This document functions as Constitutional Amendments Procedure in the US Legal System:

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Constitution | ai-interaction-principles.md | Foundational, universal, immutable |
| **Amendment Process** | **This document** | **How to evolve the framework itself** |
| Federal Statutes | Domain principles | Domain-specific binding law |
| CFR (Regulations) | Domain methods | Operational rules implementing statutes |

---

### CRITICAL: How AI Should Use This Document

**Importance: CRITICAL - This section is essential for document effectiveness**

#### When to Load

Load this document when:
- Updating any governance document
- Adding or modifying MCP index content
- Creating new domain principles or methods
- Archiving old document versions
- Performing framework health checks

#### Situation Index - What To Do When...

**Use this index to jump directly to relevant procedures:**

| Situation | Go To | Key Procedure |
|-----------|-------|---------------|
| Updating a methods document | Title 2 | Document Update Workflow |
| Updating a principles document | Title 2 | Principles Update (requires review) |
| Adding content to MCP index | Title 3 | Index Rebuild Procedure |
| Validating index integrity | Title 4 | Index Validation |
| Archiving old versions | Title 2 | Archive Procedure |
| Creating new domain | Title 5 | Domain Creation Workflow |
| Framework health check | Title 4 | Validation Checklist |
| Version number question | Title 1 | Semantic Versioning Rules |

---

# TITLE 1: VERSIONING STANDARDS

**Importance: CRITICAL - Foundation for change management**

## Part 1.1: Semantic Versioning

### 1.1.1 Version Format

All governance documents use semantic versioning: `MAJOR.MINOR.PATCH`

```
v2.1.3
 | | |
 | | +-- PATCH: Clarifications, typo fixes, formatting
 | +---- MINOR: New sections, expanded content, new procedures
 +------ MAJOR: Breaking changes, restructuring, philosophy shifts
```

### 1.1.2 Version Increment Rules

| Change Type | Increment | Examples |
|-------------|-----------|----------|
| **PATCH** | X.Y.Z+1 | Fix typo, clarify wording, formatting |
| **MINOR** | X.Y+1.0 | Add new section, new procedure, expand coverage |
| **MAJOR** | X+1.0.0 | Restructure document, change philosophy, break compatibility |

### 1.1.3 Version in Filename

Documents include version in filename for clarity:
- `ai-coding-methods-v1.0.3.md`
- `ai-interaction-principles-v1.4.md`
- `governance-framework-methods-v1.0.0.md`

### 1.1.4 Cross-Reference Compatibility

When updating documents, verify cross-references remain valid:
- [ ] Referenced documents still exist
- [ ] Referenced sections still exist
- [ ] Version compatibility documented in loader (CLAUDE.md)

---

## Part 1.2: Change Classification

### 1.2.1 Constitutional Changes (Principles)

Changes to principle documents require:
- Careful consideration of downstream effects
- Review of all dependent documents
- MAJOR version if philosophy changes
- Update to CLAUDE.md loader version references

### 1.2.2 Methods Changes

Changes to methods documents:
- Can be updated more frequently
- Should maintain compatibility with principles
- MINOR version for new procedures
- PATCH version for clarifications

### 1.2.3 Index Changes

Changes to MCP index:
- Rebuild required after document changes
- Validation required after rebuild
- No version number (generated artifact)

---

# TITLE 2: DOCUMENT UPDATE WORKFLOW

**Importance: CRITICAL - Ensures consistent updates**

## Part 2.1: Update Procedure

### 2.1.1 Pre-Update Checklist

Before modifying any governance document:

- [ ] Identify document to update
- [ ] Determine change type (PATCH/MINOR/MAJOR)
- [ ] Review current version number
- [ ] Check cross-references from other documents
- [ ] Plan archive of old version

### 2.1.2 Update Steps

**Step 1: Create New Version**
```
1. Copy current document
2. Rename with new version: document-vX.Y.Z.md
3. Update version in document header
4. Update effective date
5. Make content changes
6. Update version history section
```

**Step 2: Update References**
```
1. Update domains.json with new filename
2. Update CLAUDE.md version references
3. Update any cross-references in other documents
```

**Step 3: Archive Old Version**
```
1. Move old version to documents/archive/
2. Maintain original filename
3. Do NOT modify archived documents
```

**Step 4: Rebuild Index**
```
1. Run: python -m ai_governance_mcp.extractor
2. Verify index rebuilt successfully
3. Validate new content is searchable
```

**Step 5: Validate**
```
1. Run validation tests
2. Query for new content
3. Verify cross-references work
4. Test MCP tools
```

### 2.1.3 Archive Structure

```
documents/
  |- ai-coding-methods-v1.1.0.md      (current)
  |- ai-coding-domain-principles-v2.1.md (current)
  |- archive/
      |- ai-coding-methods-v1.0.3.md  (archived)
      |- ai-coding-methods-v1.0.2.md  (archived)
      |- ai-coding-methods-v1.0.1.md  (archived)
```

---

## Part 2.2: Domain Configuration Updates

### 2.2.1 domains.json Structure

The `documents/domains.json` file defines domain configurations:

```json
{
  "domain-name": {
    "name": "domain-name",
    "display_name": "Human Readable Name",
    "principles_file": "domain-principles-vX.Y.md",
    "methods_file": "domain-methods-vX.Y.Z.md",
    "description": "Domain description for routing...",
    "priority": 10
  }
}
```

### 2.2.2 Updating domains.json

When document versions change:

1. Update `principles_file` or `methods_file` to new version
2. Verify file exists in documents directory
3. Rebuild index to pick up changes

### 2.2.3 Priority Values

Priority controls search ordering:
- `0` - Constitution (always highest priority)
- `10` - Primary domains (ai-coding)
- `20` - Secondary domains (multi-agent)
- Higher values = lower priority

---

# TITLE 3: INDEX MANAGEMENT

**Importance: CRITICAL - Enables semantic retrieval**

## Part 3.1: Index Architecture

### 3.1.1 Index Components

The MCP index consists of:

| File | Purpose | Format |
|------|---------|--------|
| `global_index.json` | Principle metadata, text, structure | JSON |
| `content_embeddings.npy` | Semantic vectors for principles | NumPy |
| `domain_embeddings.npy` | Domain description vectors for routing | NumPy |

### 3.1.2 Index Location

Default: `index/` directory in project root

Configurable via: `AI_GOVERNANCE_INDEX_PATH` environment variable

### 3.1.3 When to Rebuild

Rebuild index when:
- Any governance document is updated
- domains.json is modified
- Embedding model is changed
- Index corruption suspected

---

## Part 3.2: Rebuild Procedure

### 3.2.1 Standard Rebuild

```bash
# From project root
python -m ai_governance_mcp.extractor

# Expected output:
# - Parsing documents...
# - Generating embeddings...
# - Building index...
# - Index saved to index/
```

### 3.2.2 Rebuild Verification

After rebuild, verify:

```bash
# Test query
python -m ai_governance_mcp.server --test "test query"

# Check file timestamps
ls -la index/

# Verify file sizes are reasonable
wc -c index/global_index.json
```

### 3.2.3 Rebuild Checklist

- [ ] Documents directory contains all referenced files
- [ ] domains.json is valid JSON
- [ ] Extractor completes without errors
- [ ] All three index files generated
- [ ] Test query returns results
- [ ] MCP server starts successfully

---

## Part 3.3: Index Integrity

### 3.3.1 Integrity Checks

Before using index:
- [ ] `global_index.json` exists and is valid JSON
- [ ] `content_embeddings.npy` exists and matches principle count
- [ ] `domain_embeddings.npy` exists and matches domain count
- [ ] Embeddings dimensions are consistent (384 for MiniLM)

### 3.3.2 Common Issues

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Missing principles in results | Document not in domains.json | Update domains.json, rebuild |
| Stale content returned | Index not rebuilt after update | Rebuild index |
| Empty results | Index corruption | Delete index/, rebuild |
| Dimension mismatch errors | Embedding model changed | Delete index/, rebuild |
| Parse errors | Malformed document | Fix document syntax, rebuild |

### 3.3.3 Recovery Procedure

If index is corrupted:

```bash
# Remove existing index
rm -rf index/

# Rebuild from scratch
python -m ai_governance_mcp.extractor

# Verify
python -m ai_governance_mcp.server --test "safety principles"
```

---

# TITLE 4: VALIDATION PROCEDURES

**Importance: IMPORTANT - Ensures framework integrity**

## Part 4.1: Post-Update Validation

### 4.1.1 Validation Checklist

After any framework update:

**Document Validation:**
- [ ] New version number in header
- [ ] Version history updated
- [ ] No broken internal links
- [ ] Formatting consistent
- [ ] Importance tags present where needed

**Reference Validation:**
- [ ] domains.json updated
- [ ] CLAUDE.md version references current
- [ ] Cross-document references valid

**Index Validation:**
- [ ] Index rebuilt successfully
- [ ] New content searchable
- [ ] Existing content still searchable
- [ ] Domain routing works correctly

**Functional Validation:**
- [ ] MCP server starts
- [ ] All 6 tools respond
- [ ] Query returns expected principles
- [ ] Confidence scores reasonable

### 4.1.2 Validation Commands

```bash
# Test MCP tools
python -m ai_governance_mcp.server --test "security requirements"

# Run test suite
pytest tests/ -v -m "not slow"

# Verify specific content
python -m ai_governance_mcp.server --test "CI/CD pipeline"
```

---

## Part 4.2: Framework Health Check

### 4.2.1 Periodic Health Check

Run periodically (monthly recommended):

**Completeness Check:**
- [ ] All documents in domains.json exist
- [ ] All documents have current versions
- [ ] Archive contains previous versions
- [ ] Index matches document content

**Consistency Check:**
- [ ] Loader (CLAUDE.md) references correct versions
- [ ] Cross-references between documents valid
- [ ] Hierarchy diagrams accurate
- [ ] Priority values appropriate

**Performance Check:**
- [ ] Query latency < 100ms
- [ ] Index size reasonable
- [ ] Embedding dimensions correct

### 4.2.2 Health Check Report Template

```markdown
# Framework Health Check
**Date:** [Date]
**Performed By:** [AI/Human]

## Documents
| Document | Current Version | Last Updated | Status |
|----------|-----------------|--------------|--------|
| Constitution | v1.4 | [date] | OK |
| AI Coding Principles | v2.1 | [date] | OK |
| AI Coding Methods | v1.1.0 | [date] | OK |
| [etc.] | | | |

## Index
- Principle count: 65
- Domain count: 3
- Last rebuilt: [date]
- Index size: [size]

## Validation Results
- [ ] All queries return results
- [ ] Domain routing accurate
- [ ] MCP tools functional

## Issues Found
[List any issues]

## Actions Taken
[List remediation actions]
```

---

# TITLE 5: DOMAIN MANAGEMENT

**Importance: IMPORTANT - Enables framework extension**

## Part 5.1: Adding New Domains

### 5.1.1 New Domain Checklist

To add a new domain:

- [ ] Create domain principles document
- [ ] Create domain methods document (optional)
- [ ] Add entry to domains.json
- [ ] Set appropriate priority
- [ ] Rebuild index
- [ ] Validate domain routing

### 5.1.2 Domain Document Requirements

**Principles Document (Required):**
- Follow established principle structure (Series codes, ID format)
- Include domain-specific guidance
- Reference constitution where appropriate

**Methods Document (Optional):**
- Follow methods document structure
- Include situation index
- Reference principles it implements

### 5.1.3 domains.json Entry

```json
{
  "new-domain": {
    "name": "new-domain",
    "display_name": "New Domain",
    "principles_file": "new-domain-principles-v1.0.md",
    "methods_file": "new-domain-methods-v1.0.0.md",
    "description": "Description used for semantic routing...",
    "priority": 30
  }
}
```

---

## Part 5.2: Domain Deprecation

### 5.2.1 Deprecation Procedure

To deprecate a domain:

1. Mark domain as deprecated in description
2. Update priority to low value (100+)
3. Maintain in index for historical queries
4. Archive documents after transition period
5. Remove from domains.json after full deprecation

### 5.2.2 Deprecation Timeline

- **Announcement:** Note deprecation in version history
- **Transition Period:** 2-3 versions or 90 days
- **Archive:** Move to archive/, keep in index
- **Removal:** Remove from domains.json, rebuild

---

# TITLE 6: CI/CD INTEGRATION

**Importance: IMPORTANT - Automated framework validation**

## Part 6.1: Automated Validation

### 6.1.1 CI Pipeline Integration

Include framework validation in CI:

```yaml
# Example GitHub Actions job
framework-validation:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install dependencies
      run: pip install -e .
    - name: Validate domains.json
      run: python -c "import json; json.load(open('documents/domains.json'))"
    - name: Rebuild index
      run: python -m ai_governance_mcp.extractor
    - name: Test MCP tools
      run: pytest tests/ -v -m "not slow"
```

### 6.1.2 Pre-Commit Hooks

Consider adding pre-commit validation:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-domains
        name: Validate domains.json
        entry: python -c "import json; json.load(open('documents/domains.json'))"
        language: system
        files: domains.json
```

---

## Part 6.2: Security Scanning

### 6.2.1 Dependency Scanning

Regularly scan framework dependencies:

```bash
# Scan for vulnerabilities
pip-audit --strict

# Source code security
bandit -r src/

# Check for known issues
safety check
```

### 6.2.2 Update Procedure

When vulnerabilities found:
1. Identify affected dependency
2. Check for available update
3. Test update compatibility
4. Update pyproject.toml
5. Rebuild and test
6. Document in version history

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-27 | Initial release. Document versioning, index management, validation procedures, domain management, CI/CD integration. |

---

## Document Governance

**Authority:** This document implements ai-interaction-principles.md. Methods cannot contradict constitutional principles.

**Updates:** This document may be updated independently of domain methods. Version increments follow semantic versioning.

**Scope:** Applies to all framework maintenance activities across all domains.

**Feedback:** Document gaps, conflicts, or improvement suggestions for inclusion in next version.
