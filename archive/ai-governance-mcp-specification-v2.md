# AI Governance MCP Server - Complete Specification

**Document Version:** 2.0.0  
**Created:** 2025-12-21  
**Status:** Specification Complete - Ready for Implementation  
**Governance Level:** This document serves as the SPECIFY phase output  
**Author:** Jason + Claude (Planning Session)

---

## Document Purpose

This specification defines a Multi-Domain AI Governance MCP Server that provides centralized, selective retrieval of AI governance documents. It follows the 4-phase workflow from ai-coding-methods.md:

```
SPECIFY (this document) → PLAN → TASKS → IMPLEMENT
```

**This document is the input for Claude Code CLI** to execute the remaining phases.

---

## Executive Summary

### Problem Statement

**Current State:**
- Three governance documents totaling ~55-65K tokens
- Must manually upload to each AI tool (Claude Projects, Windsurf, Cursor)
- Updates require re-uploading to multiple tools
- Full documents always loaded, consuming context even when 1-2 principles relevant
- No active compliance prompting
- No audit trail
- No multi-domain support - system assumes single domain

**Desired State:**
- Single source of truth for all governance documents
- Update once, propagate instantly to all connected tools
- Selective retrieval of only relevant principles (~1-3K tokens vs 55K)
- Multi-domain architecture: Constitution always applies, domains loaded contextually
- Active compliance prompting at retrieval time
- Extensible: Add new domains/methods without code changes
- Tool call logging for audit trail

### Solution Summary

**Structured Metadata + Lightweight Semantic Retrieval MCP Server**

- Documents remain unchanged (human-readable)
- Metadata index makes them machine-queryable
- Principles never chunked - returned as complete atomic units
- Constitution (ai-interaction-principles) always searched
- Domains activated by context detection or explicit declaration
- Local stdio transport - no web server needed

---

## Multi-Domain Architecture

### Document Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CONSTITUTION (Always Applies)                                          │
│  ai-interaction-principles.md                                           │
│  - Meta-Principles (C, Q, O, MA, G series)                              │
│  - Bill of Rights (S-Series) - Supreme authority                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│  AI CODING DOMAIN     │ │  [FUTURE] AI WRITING  │ │  [FUTURE] OTHER       │
│  ai-coding-domain-    │ │  ai-writing-domain-   │ │  DOMAINS              │
│  principles.md        │ │  principles.md        │ │                       │
│  ai-coding-methods.md │ │  ai-writing-methods.md│ │                       │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

### Legal Hierarchy (Override Order)

```
1. S-Series (Bill of Rights)     ← Supreme, always checked
2. Constitution (Meta-Principles) ← Always applies, all domains
3. Domain Principles              ← Domain-specific, when active
4. Methods                        ← Implementation procedures
```

**Conflict Resolution:** Higher level always wins. MCP enforces this in response ordering.

### Domain Activation

**Three Methods (Checked in Order):**

1. **Explicit Declaration:** `get_relevant_principles(context, domain="ai-coding")`
2. **Context Detection:** Keywords in query match domain signatures
3. **Default Domain:** From config file (optional fallback)

**No Domain Active = Constitution Only**

### Retrieval Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Multi-Domain Retrieval Pipeline                                        │
│                                                                         │
│  Input: context="specs seem incomplete", domain=None                    │
│                                                                         │
│  Step 1: Domain Resolution                                              │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  if domain explicitly provided → use it                           │ │
│  │  else if context matches domain signatures → detected_domain      │ │
│  │  else if default_domain in config → use default                   │ │
│  │  else → None (Constitution only)                                  │ │
│  │                                                                    │ │
│  │  Result: active_domain = "ai-coding"                              │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                           ↓                                             │
│  Step 2: Constitution Search (ALWAYS)                                   │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Search ai-interaction-principles.md                              │ │
│  │  Match against keywords, failure_modes, applies_when              │ │
│  │  Check S-Series triggers (safety first)                           │ │
│  │                                                                    │ │
│  │  Result: constitution_matches = [meta-C1, meta-S1]                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                           ↓                                             │
│  Step 3: Domain Search (if domain active)                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Search domain principles document                                 │ │
│  │  Search domain methods document (if exists)                        │ │
│  │                                                                    │ │
│  │  Result: domain_matches = [domain-C1, domain-P1]                  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                           ↓                                             │
│  Step 4: Hierarchy-Ordered Response                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  1. S-Series first (if any) - Supreme                             │ │
│  │  2. Other Constitution matches                                     │ │
│  │  3. Domain Principles                                              │ │
│  │  4. Domain Methods (if requested)                                  │ │
│  │  5. Compliance instruction block                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                           ↓                                             │
│  Output: Ordered principles + hierarchy indicator + compliance prompt   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Source Documents

### Document Inventory

| Document | Hierarchy Level | Size (est.) | Status |
|----------|----------------|-------------|--------|
| ai-interaction-principles-v1_4.md | Constitution | ~35-40K tokens | Complete |
| ai-coding-domain-principles-v2_1.md | Domain Principles | ~20-25K tokens | Complete |
| ai-coding-methods-v1_0_3.md | Methods | ~35K tokens | Complete |

### Document Structure (No Modification Needed)

Your documents already have consistent structure:

**ai-interaction-principles.md:**
```
## [Series Name] Principles
### [Code]. [Name]
**Definition:** ...
**How AI Applies:** ...
**Why This Matters:** ...
[etc.]
```

**ai-coding-domain-principles.md:**
```
### [Code]. [Name] (The [Nickname] Act)
**Failure Mode(s) Addressed:** ...
**Constitutional Basis:** ...
**Why Meta-Principles Alone Are Insufficient:** ...
**Domain Application:** ...
**Truth Sources:** ...
**How AI Applies This Principle:** ...
**Why This Principle Matters:** ...
**When Product Owner Interaction Is Needed:** ...
**Common Pitfalls:** ...
**Success Criteria:** ...
```

**ai-coding-methods.md:**
```
# TITLE [N]: [NAME]
**Importance:** [TAG]
**Implements:** [Principles]
## Part [N.M]: [Section]
### [N.M.P] [Subsection]
```

**Key Insight:** Documents are designed for AI consumption. The metadata layer extracts and indexes what's already there.

---

## File Structure

```
~/.ai-governance/
├── server.py                      # Main MCP server
├── extractor.py                   # Metadata extraction utility
├── requirements.txt               # Python dependencies
├── config.json                    # Server configuration
│
├── README.md                      # Human-facing setup and usage guide
├── ARCHITECTURE.md                # Technical design and rationale
├── EXTENDING.md                   # How to add domains/methods/principles
├── PROJECT-MEMORY.md              # AI context: decisions, patterns, state
├── LEARNING-LOG.md                # Lessons learned during development
│
├── documents/                     # Source governance documents (user provides)
│   ├── ai-interaction-principles.md
│   ├── ai-coding-domain-principles.md
│   └── ai-coding-methods.md
│
├── index/                         # Generated metadata (created by extractor)
│   ├── domains.json               # Domain registry and signatures
│   ├── principles.json            # All principles with metadata
│   └── methods.json               # Method references by domain
│
├── cache/                         # Extracted principle text (for fast retrieval)
│   ├── meta-C1.md
│   ├── meta-Q1.md
│   ├── domain-C1.md
│   └── ...
│
├── docs/                          # Detailed documentation
│   ├── tool-reference.md          # Complete MCP tool documentation
│   ├── schema-reference.md        # JSON schema documentation
│   └── troubleshooting.md         # Common issues and solutions
│
└── logs/                          # Retrieval audit logs
    └── retrievals.jsonl
```

---

## Metadata Schema

### domains.json

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-12-21T00:00:00Z",
  
  "constitution": {
    "document": "ai-interaction-principles.md",
    "version": "1.4.0",
    "always_search": true,
    "description": "Meta-Principles - Universal behavioral rules"
  },
  
  "domains": {
    "ai-coding": {
      "name": "AI Coding",
      "description": "AI-assisted software development",
      "documents": {
        "principles": "ai-coding-domain-principles.md",
        "methods": "ai-coding-methods.md"
      },
      "versions": {
        "principles": "2.1.0",
        "methods": "1.0.3"
      },
      "trigger_keywords": [
        "code", "coding", "implement", "function", "class", "method",
        "bug", "debug", "test", "testing", "deploy", "deployment",
        "refactor", "component", "API", "database", "frontend", "backend",
        "compile", "runtime", "error", "exception", "git", "commit",
        "build", "npm", "pip", "package", "dependency", "import"
      ],
      "trigger_phrases": [
        "write code", "fix the bug", "implement a", "build a",
        "create a component", "refactor this", "add a feature",
        "write a function", "debug this", "run the tests"
      ],
      "priority": 1
    },
    
    "general": {
      "name": "General",
      "description": "Constitution only - no domain-specific principles",
      "documents": {},
      "trigger_keywords": [],
      "trigger_phrases": [],
      "priority": 99
    }
  },
  
  "default_domain": "ai-coding",
  
  "detection_config": {
    "min_keyword_matches": 1,
    "phrase_match_boost": 2.0,
    "case_sensitive": false
  }
}
```

### principles.json

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-12-21T00:00:00Z",
  "extraction_source": "ai-coding-domain-principles-v2_1.md",
  
  "principles": {
    "meta-C1": {
      "id": "meta-C1",
      "name": "Context Engineering",
      "document": "ai-interaction-principles.md",
      "document_type": "constitution",
      "domain": null,
      "series": "Core Architecture",
      "series_code": "C",
      "hierarchy_level": 2,
      
      "summary": "Load necessary information to prevent hallucination",
      
      "keywords": [
        "context", "information", "knowledge", "load",
        "hallucination", "understanding", "awareness"
      ],
      
      "failure_modes": [
        "insufficient context",
        "hallucination",
        "missing information",
        "assumptions without verification"
      ],
      
      "applies_when": [
        "starting new task",
        "context seems incomplete",
        "making assumptions",
        "information gaps detected"
      ],
      
      "escalation_triggers": [
        "cannot determine required context",
        "conflicting information sources",
        "context exceeds capacity"
      ],
      
      "derives_from": [],
      "derived_by": ["domain-C1", "domain-C2", "domain-C3"],
      
      "line_range": [200, 350],
      "cache_file": "cache/meta-C1.md"
    },
    
    "domain-C1": {
      "id": "domain-C1",
      "name": "Specification Completeness",
      "nickname": "The Requirements Act",
      "document": "ai-coding-domain-principles.md",
      "document_type": "domain",
      "domain": "ai-coding",
      "series": "Context",
      "series_code": "C",
      "hierarchy_level": 3,
      
      "summary": "Don't code without complete specifications - AI will hallucinate to fill gaps",
      
      "keywords": [
        "specification", "requirements", "complete", "gaps",
        "unclear", "ambiguous", "incomplete", "missing",
        "user behavior", "business logic", "edge cases"
      ],
      
      "failure_modes": [
        "incomplete specifications",
        "hallucinated implementation",
        "ambiguous requirements",
        "missing user behavior definitions",
        "unspecified error handling",
        "unclear business logic"
      ],
      
      "applies_when": [
        "starting implementation",
        "requirements seem incomplete",
        "about to write code",
        "feature request is unclear",
        "specifications have gaps",
        "asked to implement without details"
      ],
      
      "escalation_triggers": [
        "specification gaps detected",
        "ambiguous requirements",
        "missing user behavior definitions",
        "unclear business logic",
        "unspecified edge cases",
        "no error handling requirements"
      ],
      
      "derives_from": ["meta-C1", "meta-C2", "meta-Q1", "meta-S1"],
      "derived_by": [],
      
      "line_range": [245, 380],
      "cache_file": "cache/domain-C1.md"
    }
  }
}
```

### methods.json

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-12-21T00:00:00Z",
  
  "methods_by_domain": {
    "ai-coding": {
      "document": "ai-coding-methods.md",
      "version": "1.0.3",
      
      "titles": {
        "title-1": {
          "id": "title-1",
          "name": "Calibration Procedures",
          "importance": "CRITICAL",
          "implements": ["Sequential Phase Dependencies"],
          "summary": "Project initialization and mode selection",
          "keywords": ["calibrate", "mode", "expedited", "standard", "enhanced", "new project"],
          "line_range": [250, 450]
        },
        "title-2": {
          "id": "title-2",
          "name": "Specify Procedures",
          "importance": "CRITICAL",
          "implements": ["Specification Completeness"],
          "summary": "Requirements gathering and specification writing",
          "keywords": ["specify", "requirements", "specification", "user stories"],
          "line_range": [451, 700]
        },
        "title-5": {
          "id": "title-5",
          "name": "Implement Procedures",
          "importance": "CRITICAL",
          "implements": ["Production-Ready Standards", "Security-First Development", "Testing Integration"],
          "summary": "Write → Run → Validate implementation cycle",
          "keywords": ["implement", "code", "write", "run", "validate", "test"],
          "line_range": [1100, 1500]
        }
      },
      
      "cold_start_prompts": {
        "new_project": {
          "description": "Start a new project",
          "line_range": [185, 220]
        },
        "resume_work": {
          "description": "Resume existing project",
          "line_range": [221, 255]
        },
        "recovery": {
          "description": "Recover from context loss",
          "line_range": [256, 290]
        }
      }
    }
  }
}
```

---

## MCP Tools Specification

### Tool 1: `get_governance_summary`

**Purpose:** Quick orientation - governance structure, domains, and escalation triggers.

**Parameters:** None

**Returns:** (~500 tokens)
```markdown
## AI Governance Framework

**Hierarchy:** S-Series (Safety) > Constitution > Domain Principles > Methods

**Available Domains:**
- ai-coding: AI-assisted software development

**Immediate Escalation Triggers:**
- S-Series violation (security, privacy, harm)
- MA4 "Stop the Line" 
- Specification gaps preventing safe implementation
- Repeated failures (2+ attempts)

**To retrieve principles:** Use get_relevant_principles(context)
```

---

### Tool 2: `get_principle`

**Purpose:** Retrieve single complete principle by ID.

**Parameters:**
- `principle_id` (string, required): e.g., "meta-C1", "domain-P4"

**Returns:** Complete principle text from cache file, never chunked.

**Example:**
```python
get_principle("domain-C1")
# Returns full text of Specification Completeness principle (~800 tokens)
```

---

### Tool 3: `get_relevant_principles`

**Purpose:** Context-aware retrieval with multi-domain support.

**Parameters:**
- `context` (string, required): Current situation description
- `domain` (string, optional): Explicit domain override ("ai-coding", "general", or null for auto-detect)
- `include_constitution` (bool, optional, default=True): Always search Constitution
- `include_methods` (bool, optional, default=False): Include relevant methods
- `max_results` (int, optional, default=5): Maximum principles to return

**Returns:**
```markdown
---
## Governance Principles Retrieved

**Active Domain:** AI Coding
**Detection Method:** Auto-detected from keywords ["implement", "specs"]

### Constitution (Always Applies)

#### meta-C1: Context Engineering
[Full principle text]

---

### AI Coding Domain

#### domain-C1: Specification Completeness (The Requirements Act)
[Full principle text]

---

**HIERARCHY REMINDER:**
S-Series (Safety) > Constitution > Domain Principles > Methods

**COMPLIANCE INSTRUCTION:**
Apply the above principles to your current task.
When principles influence your decisions, cite them: "Applying [CODE]: [rationale]"
If you encounter an escalation trigger, stop and request human input.
---
```

**Retrieval Logic:**
1. Resolve domain (explicit > detected > default > none)
2. Search Constitution (always, unless include_constitution=False)
3. Search active domain principles
4. Optionally search methods
5. Rank by match quality
6. Return complete principles ordered by hierarchy

---

### Tool 4: `get_validation_criteria`

**Purpose:** Get quality gates for a specific phase.

**Parameters:**
- `phase` (string, required): e.g., "specify", "plan", "tasks", "implement"
- `domain` (string, optional): Domain context

**Returns:** Success criteria, validation checklist, gate requirements from methods.

---

### Tool 5: `get_escalation_triggers`

**Purpose:** All conditions requiring human intervention.

**Parameters:**
- `category` (string, optional): Filter by "safety", "security", "process", "technical"
- `domain` (string, optional): Domain-specific triggers

**Returns:** Grouped escalation triggers with severity and action guidance.

---

### Tool 6: `search_governance`

**Purpose:** Keyword/semantic search across all documents.

**Parameters:**
- `query` (string, required): Search terms
- `document_filter` (string, optional): "constitution", "domain", "methods", or null for all
- `domain` (string, optional): Limit domain scope
- `max_results` (int, optional, default=5)

**Returns:** Matching sections with relevance scores.

---

### Tool 7: `get_active_domains`

**Purpose:** List available domains and current state.

**Parameters:** None

**Returns:**
```json
{
  "available_domains": ["ai-coding", "general"],
  "default_domain": "ai-coding",
  "constitution_document": "ai-interaction-principles.md"
}
```

---

### Tool 8: `set_session_domain`

**Purpose:** Set domain for subsequent retrievals.

**Parameters:**
- `domain` (string, required): Domain identifier or "general" for Constitution-only

**Returns:** Confirmation with domain principle count.

---

### Tool 9: `get_cold_start_prompt`

**Purpose:** Retrieve ready-to-use prompts from methods.

**Parameters:**
- `scenario` (string, required): "new_project", "resume_work", "recovery"
- `domain` (string, optional, default from config)

**Returns:** Copy-paste prompt template from methods document.

---

## Extensibility Design

### Adding a New Domain

**No code changes required.** Just:

1. **Create domain documents** (following existing structure):
   ```
   documents/
   ├── ai-writing-domain-principles.md  # Same 10-field structure
   └── ai-writing-methods.md            # Same title/part structure
   ```

2. **Run extraction script:**
   ```bash
   python extractor.py --document ai-writing-domain-principles.md --domain ai-writing
   ```

3. **Update domains.json** (or let extractor do it):
   ```json
   {
     "domains": {
       "ai-writing": {
         "name": "AI Writing",
         "documents": {
           "principles": "ai-writing-domain-principles.md",
           "methods": "ai-writing-methods.md"
         },
         "trigger_keywords": ["write", "draft", "blog", "article", "email"],
         "trigger_phrases": ["write a post", "draft an email"]
       }
     }
   }
   ```

4. **Restart MCP server** (or it hot-reloads on next request)

**Done.** All MCP tools now serve the new domain.

### Adding/Updating Methods

1. Update the methods document
2. Run: `python extractor.py --methods ai-coding-methods.md`
3. Methods index updated automatically

### Document Versioning

Each document tracks its version in metadata. When documents update:
- Bump version in document header
- Re-run extraction
- Index includes version info for debugging

---

## Implementation Requirements

### Dependencies

```
# requirements.txt
mcp>=1.0.0                    # MCP SDK
sentence-transformers>=2.2.0  # Semantic embeddings (optional, for Phase 3)
```

### Python Version

Python 3.10+

### No External Services

- No database (JSON file storage)
- No web server (stdio transport)
- No network (local only)

---

## Configuration

### config.json

```json
{
  "server": {
    "name": "ai-governance",
    "version": "1.0.0"
  },
  
  "paths": {
    "documents": "./documents",
    "index": "./index",
    "cache": "./cache",
    "logs": "./logs"
  },
  
  "retrieval": {
    "default_max_results": 5,
    "always_include_constitution": true,
    "semantic_ranking_enabled": true,
    "semantic_model": "all-MiniLM-L6-v2"
  },
  
  "logging": {
    "enabled": true,
    "format": "jsonl",
    "include_context": false
  },
  
  "domains": {
    "default": "ai-coding",
    "auto_detect": true
  }
}
```

### Client Configuration

**Claude Code CLI** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "governance": {
      "command": "python",
      "args": ["/Users/[username]/.ai-governance/server.py"]
    }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "governance": {
      "command": "python",
      "args": ["/Users/[username]/.ai-governance/server.py"]
    }
  }
}
```

---

## Test Scenarios

### Scenario 1: Domain Auto-Detection
**Input:** `get_relevant_principles("specs seem incomplete, should I proceed?")`  
**Expected:** Domain detected as "ai-coding", returns domain-C1 + meta-C1

### Scenario 2: Constitution Only
**Input:** `get_relevant_principles("help me think through this problem", domain="general")`  
**Expected:** Only Constitution principles returned

### Scenario 3: S-Series Priority
**Input:** `get_relevant_principles("this might expose user data")`  
**Expected:** S-Series (Privacy/Security) returned FIRST, then others

### Scenario 4: Methods Retrieval
**Input:** `get_relevant_principles("starting new project", include_methods=True)`  
**Expected:** Returns principles + Cold Start procedure from methods

### Scenario 5: Unknown Domain Keyword
**Input:** `get_relevant_principles("write a blog post about AI")`  
**Expected:** No ai-coding match, falls back to Constitution only (until ai-writing domain added)

---

## Success Criteria

### Functional
- [ ] All principles indexed with complete metadata
- [ ] Domain auto-detection works for ai-coding keywords
- [ ] Constitution always included unless explicitly disabled
- [ ] S-Series principles appear first when relevant
- [ ] Principles returned complete (never chunked)
- [ ] New domain can be added without code changes
- [ ] Works with Claude Code CLI and Claude Desktop

### Performance
- [ ] Retrieval < 500ms
- [ ] Typical response: 1,500-3,000 tokens (vs 55K full load)
- [ ] Server startup < 2 seconds

### Quality
- [ ] Match explanations provided
- [ ] Compliance prompt included
- [ ] Hierarchy clearly indicated in response

### Documentation (Required for Completion)
- [ ] README.md enables setup in < 10 minutes (tested)
- [ ] EXTENDING.md has been validated by following its steps
- [ ] ARCHITECTURE.md explains all major design decisions
- [ ] PROJECT-MEMORY.md reflects current state and all decisions
- [ ] LEARNING-LOG.md captures lessons from development
- [ ] docs/tool-reference.md documents all 9 MCP tools
- [ ] docs/schema-reference.md documents all JSON schemas
- [ ] docs/troubleshooting.md covers common issues

---

## Documentation Requirements

### Required Documentation Deliverables

Per ai-coding-methods Memory Architecture, this project MUST produce and maintain these documentation files:

```
~/.ai-governance/
├── README.md                      # Human-facing: Setup, usage, troubleshooting
├── ARCHITECTURE.md                # Technical design and rationale
├── EXTENDING.md                   # How to add domains, methods, principles
├── PROJECT-MEMORY.md              # AI context: Decisions, patterns, gotchas
├── LEARNING-LOG.md                # Lessons learned during development
└── docs/
    ├── tool-reference.md          # Complete MCP tool documentation
    ├── schema-reference.md        # JSON schema documentation
    └── troubleshooting.md         # Common issues and solutions
```

---

### README.md (Human-Facing)

**Purpose:** Primary entry point for humans. Setup to first successful use in < 10 minutes.

**Required Sections:**

```markdown
# AI Governance MCP Server

## What This Does
[One paragraph explanation]

## Quick Start (5 minutes)
1. Install dependencies
2. Copy your governance documents
3. Run extraction
4. Configure your AI tool
5. Test it works

## Prerequisites
- Python 3.10+
- Your governance documents
- Claude Code CLI or Claude Desktop

## Installation
[Step-by-step commands]

## Configuration
### Claude Code CLI
[Exact JSON to add]

### Claude Desktop  
[Exact JSON to add]

### Other MCP Clients
[Generic guidance]

## Basic Usage
[3-5 common commands with examples]

## Adding a New Domain
See EXTENDING.md for complete guide.

Quick version:
1. Create domain documents in documents/
2. Run: python extractor.py --add-domain [name]
3. Restart your AI tool

## Troubleshooting
See docs/troubleshooting.md

## Project Structure
[File tree with one-line descriptions]
```

---

### EXTENDING.md (Domain/Methods Addition Guide)

**Purpose:** Complete guide for adding new domains or updating existing ones. Written for both humans and AI.

**Required Sections:**

```markdown
# Extending the AI Governance MCP

## Overview
This MCP is designed for easy extension. No code changes needed to add domains.

## Adding a New Domain

### Step 1: Create Domain Documents

Your domain needs 1-2 documents following the governance structure:

**Required: Domain Principles Document**
File: `documents/ai-[domain]-domain-principles.md`

Must follow the 10-field principle template:
- Failure Mode(s) Addressed
- Constitutional Basis
- Why Meta-Principles Alone Are Insufficient
- Domain Application
- Truth Sources
- How AI Applies This Principle
- Why This Principle Matters
- When Product Owner Interaction Is Needed
- Common Pitfalls
- Success Criteria

**Optional: Domain Methods Document**
File: `documents/ai-[domain]-methods.md`

Must follow the Title/Part structure from ai-coding-methods.md.

### Step 2: Run the Extractor

```bash
cd ~/.ai-governance

# Add new domain with auto-detection of trigger keywords
python extractor.py --add-domain ai-writing \
  --principles documents/ai-writing-domain-principles.md \
  --methods documents/ai-writing-methods.md

# Or manually specify trigger keywords
python extractor.py --add-domain ai-writing \
  --principles documents/ai-writing-domain-principles.md \
  --triggers "write,draft,blog,article,email,essay,content"
```

### Step 3: Verify Extraction

```bash
# Check the domain was added
python extractor.py --list-domains

# Verify principles were indexed
python extractor.py --list-principles --domain ai-writing

# Test retrieval
python server.py --test "help me write a blog post"
```

### Step 4: Configure Trigger Keywords

Edit `index/domains.json` to refine auto-detection:

```json
{
  "domains": {
    "ai-writing": {
      "trigger_keywords": ["write", "draft", "blog", "article", ...],
      "trigger_phrases": ["write a post", "draft an email", ...]
    }
  }
}
```

### Step 5: Restart AI Tools

Claude Code CLI and Claude Desktop spawn fresh server instances, so just start a new conversation.

## Updating Existing Domains

### Update Principles
1. Edit the principles document
2. Run: `python extractor.py --refresh-domain ai-coding`
3. Cache and index automatically updated

### Update Methods
1. Edit the methods document
2. Run: `python extractor.py --refresh-methods ai-coding`

### Update Trigger Keywords
1. Edit `index/domains.json` directly
2. No extraction needed - changes take effect on next server start

## Adding Principles to Existing Domain

If adding a new principle to an existing domain document:

1. Add principle following the 10-field template
2. Run: `python extractor.py --refresh-domain [domain]`
3. New principle automatically indexed

## Removing a Domain

```bash
python extractor.py --remove-domain ai-writing
```

This removes from indexes but does NOT delete source documents.

## Document Structure Requirements

### Why Structure Matters
The extractor parses documents by looking for:
- `### [CODE]. [Name]` for principle headers
- `**[Field Name]:**` for field extraction
- `# TITLE [N]:` for methods sections

If your documents don't follow this structure, extraction will fail or be incomplete.

### Validation
```bash
# Validate document structure before extraction
python extractor.py --validate documents/ai-writing-domain-principles.md
```

## Troubleshooting Extension Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No principles found" | Document doesn't follow template | Check ### headers and ** field markers |
| Domain not auto-detected | Trigger keywords don't match | Add more keywords to domains.json |
| Principles incomplete | Missing required fields | Ensure all 10 fields present |
| Methods not loading | Wrong title format | Use `# TITLE N:` format |

## Example: Adding AI Writing Domain

Complete walkthrough:

1. Create `documents/ai-writing-domain-principles.md`:
   [Template provided]

2. Run extraction:
   ```bash
   python extractor.py --add-domain ai-writing \
     --principles documents/ai-writing-domain-principles.md
   ```

3. Add trigger keywords:
   Edit domains.json, add "write", "draft", etc.

4. Test:
   ```bash
   python server.py --test "help me draft a blog post"
   # Should return: Active Domain: AI Writing
   ```

5. Done! New domain active in all connected AI tools.
```

---

### ARCHITECTURE.md (Technical Design)

**Purpose:** Explain HOW and WHY the system is built this way. For developers and AI context.

**Required Sections:**

```markdown
# AI Governance MCP - Architecture

## Design Principles

### Why Structured Metadata, Not Vector RAG
[Explanation of the decision and trade-offs]

### Why Principles Are Never Chunked
[Atomic unit reasoning]

### Why Multi-Domain
[Extensibility rationale]

## System Architecture

### Component Diagram
[ASCII or description]

### Data Flow
1. Query received
2. Domain resolution
3. Constitution search (always)
4. Domain search (if active)
5. Hierarchy ordering
6. Response assembly

## Key Design Decisions

### Decision 1: Stdio Transport Over HTTP
- Rationale: [why]
- Trade-offs: [what we gave up]
- Alternatives considered: [what else we looked at]

### Decision 2: JSON Index + Source Extraction
- Rationale: Documents stay human-readable
- Trade-offs: Extraction step required
- Alternatives considered: Embedded metadata, database

[Continue for major decisions]

## Schema Design

### principles.json
[Schema with explanation of each field]

### domains.json
[Schema with explanation]

### methods.json
[Schema with explanation]

## Extension Points

### Adding Tools
How to add new MCP tools to server.py

### Modifying Retrieval Logic
Where retrieval algorithms live, how to tune

### Custom Domain Detection
How to implement domain-specific detection beyond keywords

## Performance Characteristics

### Memory Usage
[Expected footprint]

### Retrieval Latency
[Expected timing]

### Scaling Limits
[How many principles/domains before issues]
```

---

### PROJECT-MEMORY.md (AI Context)

**Purpose:** Persistent memory for AI sessions. What AI needs to know to work on this project effectively.

**Required Sections:**

```markdown
# AI Governance MCP - Project Memory

## Project Identity
- **Name:** AI Governance MCP Server
- **Purpose:** Centralized multi-domain AI governance document retrieval
- **Owner:** Jason
- **Status:** [Current phase]

## Architecture Summary
[Condensed version for quick AI loading]

## Key Decisions Log

### Decision: Structured Metadata over Vector RAG
- **Date:** 2025-12-21
- **Rationale:** Principles are atomic units that should never be chunked. Vector RAG would fragment them.
- **Implication:** Must maintain metadata index; extraction step required.

### Decision: Multi-Domain Architecture
- **Date:** 2025-12-21
- **Rationale:** Constitution always applies; domains are contextual. Enables future domains without code changes.
- **Implication:** Domain resolution logic in every retrieval.

[Continue for all major decisions]

## Patterns and Conventions

### Naming
- Principle IDs: `meta-C1`, `domain-C1`
- Cache files: `cache/[id].md`
- Domain names: lowercase, hyphenated

### Code Style
[Project-specific patterns]

### Error Handling
[How errors are handled]

## Known Gotchas

### Gotcha 1: Line Range Drift
If source documents are edited, line_range in index becomes stale.
**Solution:** Always run extraction after document edits.

### Gotcha 2: Domain Detection False Positives
"Write code" contains "write" which might trigger ai-writing.
**Solution:** Phrase matching has priority; keyword matching requires threshold.

[Continue for discovered issues]

## Current State

### Completed
- [ ] Specification (SPECIFY phase)
- [ ] [Updated as project progresses]

### In Progress
- [ ] [Current work]

### Blocked
- [ ] [Any blockers]

## File Map

| File | Purpose | Last Updated |
|------|---------|--------------|
| server.py | Main MCP server | [date] |
| extractor.py | Metadata extraction | [date] |
| [etc.] | | |

## Testing Notes

### How to Test
[Commands and expected results]

### Known Test Gaps
[What's not tested yet]

## Dependencies

| Package | Version | Why |
|---------|---------|-----|
| mcp | >=1.0.0 | MCP SDK |
| sentence-transformers | >=2.2.0 | Semantic ranking |
```

---

### LEARNING-LOG.md (Lessons Learned)

**Purpose:** Capture lessons during development for future reference.

**Required Sections:**

```markdown
# AI Governance MCP - Learning Log

## Purpose
This log captures lessons learned during development. Review before making changes.

## Lessons

### [Date] - [Title]
**Context:** What we were trying to do
**What Happened:** What went wrong or right
**Lesson:** What we learned
**Action:** What we changed or should do differently

---

### 2025-12-21 - Planning Phase Decisions
**Context:** Deciding between RAG approaches
**What Happened:** Analyzed Vector RAG, Graph RAG, Hybrid, Structured Metadata
**Lesson:** For small, structured corpora with atomic units, simple metadata beats complex RAG
**Action:** Chose Structured Metadata + Lightweight Semantic approach

[Continue as development progresses]
```

---

### docs/tool-reference.md (Complete Tool Docs)

**Purpose:** Comprehensive reference for all MCP tools.

**Format:** For each tool:
- Purpose
- Parameters (with types, defaults, examples)
- Returns (with format examples)
- Usage examples
- Error cases
- Related tools

---

### docs/schema-reference.md (JSON Schema Docs)

**Purpose:** Complete documentation of all JSON schemas.

**Format:** For each schema:
- Purpose
- Complete field reference
- Example documents
- Validation rules

---

### docs/troubleshooting.md (Problem Resolution)

**Purpose:** Common issues and solutions.

**Format:**
| Symptom | Cause | Solution |
|---------|-------|----------|

Plus detailed troubleshooting procedures for complex issues.

---

### Documentation Maintenance Rules

1. **README.md:** Update when user-facing behavior changes
2. **EXTENDING.md:** Update when extension process changes
3. **ARCHITECTURE.md:** Update when design decisions change
4. **PROJECT-MEMORY.md:** Update at end of every significant work session
5. **LEARNING-LOG.md:** Add entry when lesson is learned
6. **tool-reference.md:** Update when tools are added/modified
7. **schema-reference.md:** Update when schemas change
8. **troubleshooting.md:** Update when new issues discovered

### Documentation Validation

Before marking IMPLEMENT phase complete:
- [ ] All documentation files exist
- [ ] README enables setup in < 10 minutes
- [ ] EXTENDING.md has been tested by following it
- [ ] PROJECT-MEMORY.md reflects current state
- [ ] All tools documented in tool-reference.md

---

## Phase Outputs (For AI Coding Methods Workflow)

This specification serves as the **SPECIFY phase output**.

**Next Phases:**

1. **PLAN:** Define architecture, technology choices, component design
2. **TASKS:** Break into atomic implementation tasks (≤15 files each)
3. **IMPLEMENT:** Write → Run → Validate cycle

**Validation Gate (GATE-SPECIFY):**
- [x] Problem clearly defined
- [x] Solution architecture specified
- [x] All tools documented with parameters/returns
- [x] Extensibility mechanism defined
- [x] Test scenarios provided
- [x] Success criteria measurable
- [x] Documentation deliverables defined with templates
- [x] Memory files specified (PROJECT-MEMORY.md, LEARNING-LOG.md)

---

## Instructions for Claude Code CLI

### Starting the Project

Use this prompt to begin:

```
I'm starting implementation of the AI Governance MCP Server.

PROJECT: AI Governance MCP
DESCRIPTION: Local MCP server for multi-domain AI governance document retrieval

The complete specification is in: ai-governance-mcp-specification-v2.md

Calibration:
- Novelty: PARTIALLY (MCP servers exist, but this specific governance retrieval is novel)
- Requirements Certainty: HIGH (specification is complete)
- Stakes: MEDIUM (development tool, not production user-facing)
- Longevity: LONG (core infrastructure for all AI work)

Please:
1. Confirm procedural mode (recommend STANDARD)
2. Review the specification
3. Begin PLAN phase: Define architecture and technical decisions
4. Create PROJECT-MEMORY.md with key decisions
```

### Critical: Documentation is a Required Deliverable

Per the specification and ai-coding-methods best practices, the following documentation files are **required deliverables**, not optional:

| File | Purpose | When to Create |
|------|---------|----------------|
| README.md | Human setup guide | During IMPLEMENT |
| EXTENDING.md | How to add domains | During IMPLEMENT |
| ARCHITECTURE.md | Design rationale | During PLAN |
| PROJECT-MEMORY.md | AI context | Start of PLAN, update continuously |
| LEARNING-LOG.md | Lessons learned | Throughout, as lessons emerge |
| docs/tool-reference.md | Tool documentation | During IMPLEMENT |
| docs/schema-reference.md | Schema documentation | During IMPLEMENT |
| docs/troubleshooting.md | Issue resolution | During IMPLEMENT and testing |

**The project is NOT complete until all documentation passes validation:**
- README.md tested: Can a new user set up in < 10 minutes?
- EXTENDING.md tested: Can you add a domain by following the steps?
- All tools documented with examples

### Document Locations

After creating ~/.ai-governance/:
1. Copy ai-governance-mcp-specification-v2.md to ~/.ai-governance/
2. User will copy governance documents to ~/.ai-governance/documents/
3. Create PROJECT-MEMORY.md immediately at PLAN phase start
4. Proceed through PLAN → TASKS → IMPLEMENT phases
5. Create remaining documentation during/after IMPLEMENT

### Memory File Maintenance

Per ai-coding-methods.md Memory Architecture:

**PROJECT-MEMORY.md:** Update at end of each work session with:
- Decisions made and rationale
- Current state and next steps
- Any new gotchas discovered

**LEARNING-LOG.md:** Add entry whenever:
- Something unexpected happens
- A better approach is discovered
- A mistake is made and corrected

### Phase-Specific Documentation Tasks

**PLAN Phase:**
- Create PROJECT-MEMORY.md with initial decisions
- Create ARCHITECTURE.md with design rationale
- Start LEARNING-LOG.md

**TASKS Phase:**
- Update PROJECT-MEMORY.md with task breakdown decisions
- Add any lessons to LEARNING-LOG.md

**IMPLEMENT Phase:**
- Create README.md (test with fresh setup)
- Create EXTENDING.md (test by following steps)
- Create docs/tool-reference.md
- Create docs/schema-reference.md
- Create docs/troubleshooting.md
- Final update to PROJECT-MEMORY.md
- Final update to LEARNING-LOG.md

### Validation Before Completion

Before declaring the project complete, verify:

```bash
# Documentation exists
ls README.md EXTENDING.md ARCHITECTURE.md PROJECT-MEMORY.md LEARNING-LOG.md
ls docs/tool-reference.md docs/schema-reference.md docs/troubleshooting.md

# Test README (have someone follow it from scratch)
# Test EXTENDING.md (actually add a test domain following steps)
```

---

**End of Specification**
