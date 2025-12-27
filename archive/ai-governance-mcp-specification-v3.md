# AI Governance MCP Server - Complete Specification

**Document Version:** 3.0.0
**Created:** 2025-12-21
**Updated:** 2025-12-22 (v3 - Specification completeness fixes)
**Status:** Specification Complete - Ready for Implementation
**Governance Level:** This document serves as the SPECIFY phase output
**Author:** Jason + Claude (Planning Session)

---

## Changelog (v2 → v3)

| Change | Section | Rationale |
|--------|---------|-----------|
| Added explicit retrieval algorithm | §Retrieval Algorithm | Algorithm was undefined |
| Added S-Series trigger keywords | §S-Series Detection | Triggers were unspecified |
| Added multi-domain conflict resolution | §Multi-Domain Conflict Resolution | Behavior undefined |
| Clarified include_constitution parameter | §Tool 3 | Parameter contradicted "always applies" |
| Added output schemas for Tools 4-6 | §MCP Tools 4-6 | Formats were missing |
| Added expanded metadata schema | §principles.json | Miss rate reduction |
| Specified string matching strategy | §String Matching | Strategy undefined |
| Added edge case handling | §Edge Case Handling | 10+ scenarios undefined |
| Added multi-agent domain | §domains.json | New domain support |
| Added FRAMEWORK-EVALUATION.md | §Documentation | Meta-evaluation tracking |

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
- Five governance documents totaling ~55-65K tokens
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

**Structured Metadata + Expanded Keyword Matching MCP Server**

- Documents remain unchanged (human-readable)
- Metadata index makes them machine-queryable
- **Expanded metadata** (synonyms, aliases, failure_indicators) reduces miss rate to ~5%
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
│  AI CODING DOMAIN     │ │  MULTI-AGENT DOMAIN   │ │  [FUTURE] OTHER       │
│  ai-coding-domain-    │ │  multi-agent-domain-  │ │  DOMAINS              │
│  principles.md        │ │  principles.md        │ │                       │
│  ai-coding-methods.md │ │  multi-agent-methods  │ │                       │
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

---

## Retrieval Algorithm (NEW in v3)

### Scoring Algorithm

```python
def score_principle(principle: Principle, query: str, config: Config) -> float:
    """
    Calculate relevance score for a principle against a query.
    Returns: Float score where higher = more relevant.
    """
    score = 0.0
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # 1. Keyword matching (weight: 1.0)
    for keyword in principle.keywords:
        if _word_match(keyword.lower(), query_words):
            score += 1.0

    # 2. Synonym matching (weight: 0.8)
    for synonym in principle.synonyms:
        if _word_match(synonym.lower(), query_words):
            score += 0.8

    # 3. Phrase matching (weight: 2.0)
    for phrase in principle.trigger_phrases:
        if phrase.lower() in query_lower:
            score += 2.0

    # 4. Failure indicator matching (weight: 1.5)
    for indicator in principle.failure_indicators:
        if _word_match(indicator.lower(), query_words):
            score += 1.5

    # 5. Applies_when matching (weight: 1.2)
    for condition in principle.applies_when:
        if any(word in query_lower for word in condition.lower().split()):
            score += 1.2

    # 6. S-Series priority boost
    if principle.series_code == "S":
        score *= 10.0  # S-Series always surfaces

    return score

def _word_match(target: str, query_words: set) -> bool:
    """
    Case-insensitive whole-word matching.
    'code' matches 'code' but not 'decode' or 'coder'.
    """
    return target in query_words
```

### String Matching Strategy (NEW in v3)

| Aspect | Strategy | Example |
|--------|----------|---------|
| **Case sensitivity** | Case-insensitive | "Code" matches "code" |
| **Word boundaries** | Whole-word only | "code" does NOT match "decode" |
| **Stemming** | None | "coding" does NOT match "code" (add as synonym) |
| **Fuzzy matching** | None | "cod" does NOT match "code" |
| **Phrase matching** | Substring | "write code" matches "help me write code for" |

### Domain Resolution

```python
def resolve_domains(query: str, explicit_domain: str | None, config: Config) -> list[str]:
    """
    Determine which domains are active for this query.
    Returns: List of active domain IDs (can be multiple).
    """
    # 1. Explicit declaration wins
    if explicit_domain:
        if explicit_domain == "general":
            return []  # Constitution only
        if explicit_domain in config.domains:
            return [explicit_domain]
        # Unknown domain - fall through to detection

    # 2. Context-based detection
    domain_scores = {}
    query_lower = query.lower()
    query_words = set(query_lower.split())

    for domain_id, domain in config.domains.items():
        if domain_id == "general":
            continue

        score = 0

        # Keyword matches
        for keyword in domain.trigger_keywords:
            if _word_match(keyword.lower(), query_words):
                score += 1

        # Phrase matches (boost)
        for phrase in domain.trigger_phrases:
            if phrase.lower() in query_lower:
                score += config.phrase_match_boost  # 2.0

        if score >= config.min_keyword_matches:  # Default: 1
            domain_scores[domain_id] = score

    # 3. Multi-domain conflict resolution (NEW in v3)
    return _resolve_domain_conflicts(domain_scores, config)

def _resolve_domain_conflicts(domain_scores: dict, config: Config) -> list[str]:
    """
    When multiple domains match, determine which to activate.
    """
    if not domain_scores:
        # No matches - use default or Constitution only
        if config.default_domain and config.default_domain != "general":
            return [config.default_domain]
        return []

    if len(domain_scores) == 1:
        return list(domain_scores.keys())

    # Multiple matches - check for tie
    max_score = max(domain_scores.values())
    top_domains = [d for d, s in domain_scores.items() if s == max_score]

    if len(top_domains) == 1:
        # Clear winner
        return top_domains

    # Tie - use priority from config
    top_domains.sort(key=lambda d: config.domains[d].priority)

    if top_domains[0] != top_domains[1]:  # Different priorities
        return [top_domains[0]]  # Highest priority wins

    # Still tied - return BOTH domains (multi-domain retrieval)
    return top_domains
```

---

## S-Series Detection (NEW in v3)

### S-Series Trigger Keywords

The S-Series (Bill of Rights) represents supreme safety principles. These triggers ALWAYS activate S-Series search:

```json
{
  "s_series_triggers": {
    "S1_privacy": {
      "keywords": ["data", "personal", "privacy", "user data", "collect", "store", "share", "PII", "GDPR", "consent"],
      "phrases": ["user information", "personal data", "data collection", "privacy concern"]
    },
    "S2_security": {
      "keywords": ["security", "vulnerability", "exploit", "attack", "breach", "injection", "XSS", "CSRF", "auth", "credential"],
      "phrases": ["security risk", "vulnerable to", "might expose", "security concern"]
    },
    "S3_harm": {
      "keywords": ["illegal", "discriminate", "abuse", "harm", "dangerous", "malicious", "fraud", "deceptive"],
      "phrases": ["could harm", "might abuse", "illegal activity", "discriminatory"]
    },
    "S4_transparency": {
      "keywords": ["honest", "transparent", "disclose", "mislead", "deceive"],
      "phrases": ["be transparent", "should disclose", "misleading"]
    }
  }
}
```

### S-Series Detection Algorithm

```python
def check_s_series_relevance(query: str, s_triggers: dict) -> list[str]:
    """
    Check if query triggers any S-Series principles.
    Returns: List of triggered S-Series IDs.
    """
    triggered = []
    query_lower = query.lower()
    query_words = set(query_lower.split())

    for s_id, triggers in s_triggers.items():
        matched = False

        # Check keywords
        for keyword in triggers["keywords"]:
            if _word_match(keyword.lower(), query_words):
                matched = True
                break

        # Check phrases
        if not matched:
            for phrase in triggers["phrases"]:
                if phrase.lower() in query_lower:
                    matched = True
                    break

        if matched:
            triggered.append(s_id)

    return triggered
```

---

## Edge Case Handling (NEW in v3)

### Defined Error Behaviors

| Scenario | Behavior | Response |
|----------|----------|----------|
| **No documents in documents/** | Server fails to start | Error: "No governance documents found" |
| **Corrupted JSON index** | Regenerate from documents | Warning logged, fresh extraction |
| **Principle not in cache** | Extract on demand | Create cache file, then return |
| **Unknown principle_id** | Return error | `{"error": "Principle not found", "id": "unknown-X1"}` |
| **Empty query string** | Return governance summary | Same as get_governance_summary() |
| **Query > 10,000 chars** | Truncate to 10,000 | Warning in response |
| **No principles match** | Return empty with guidance | `{"matches": [], "suggestion": "Try broader terms"}` |
| **max_results > total** | Return all available | No padding, just fewer results |
| **Document version mismatch** | Warning, continue | Include version warning in response |
| **Domain not found** | Fall back to Constitution | Warning: "Domain 'x' not found, using Constitution only" |
| **include_constitution=false** | Constitution NOT in output | But S-Series still checked internally |

### include_constitution Clarification (v3 Resolution)

**The Contradiction:** v2 said "Constitution always applies" but had `include_constitution` parameter.

**Resolution:**
- Constitution is **always searched** (cannot disable)
- S-Series is **always checked** (cannot disable)
- `include_constitution` controls **output only**:
  - `true` (default): Constitution principles appear in response
  - `false`: Constitution principles omitted from response BUT still influence relevance

**Example:**
```python
# Query about incomplete specs
get_relevant_principles("specs seem incomplete", include_constitution=False)

# Internal: Searches Constitution, finds meta-C1
# Output: Only shows domain-C1 (meta-C1 omitted from output)
# But: meta-C1 was still used for relevance ranking
```

---

## Source Documents

### Document Inventory (Updated v3)

| Document | Hierarchy Level | Size (est.) | Status |
|----------|----------------|-------------|--------|
| ai-interaction-principles-v1.4.md | Constitution | ~35-40K tokens | Complete |
| ai-coding-domain-principles-v2.1.md | Domain Principles | ~20-25K tokens | Complete |
| ai-coding-methods-v1.0.3.md | Methods | ~35K tokens | Complete |
| **multi-agent-domain-principles-v1.0.1.md** | Domain Principles | ~15K tokens | Complete |
| **multi-agent-methods-v1.0.0.md** | Methods | ~12K tokens | Complete |

---

## File Structure

```
/Users/jasoncollier/Developer/ai-governance-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py                  # Main MCP server (FastMCP)
│   ├── retrieval.py               # Domain resolution, matching, ordering
│   ├── extractor.py               # Metadata extraction utility
│   ├── models.py                  # Pydantic data models
│   └── config.py                  # Configuration management
│
├── documents/                     # Source governance documents
│   ├── ai-interaction-principles-v1.4.md
│   ├── ai-coding-domain-principles-v2.1.md
│   ├── ai-coding-methods-v1.0.3.md
│   ├── multi-agent-domain-principles-v1.0.1.md
│   └── multi-agent-methods-v1.0.0.md
│
├── index/                         # Generated metadata (created by extractor)
│   ├── domains.json               # Domain registry and signatures
│   ├── principles.json            # All principles with metadata
│   └── methods.json               # Method references by domain
│
├── cache/                         # Extracted principle text (for fast retrieval)
│   ├── meta-C1.md
│   ├── coding-C1.md
│   ├── multi-A1.md
│   └── ...
│
├── docs/                          # Detailed documentation
│   ├── tool-reference.md
│   ├── schema-reference.md
│   └── troubleshooting.md
│
├── logs/                          # Retrieval audit logs
│   └── retrievals.jsonl
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_retrieval.py
│   ├── test_server.py
│   └── test_integration.py
│
├── README.md
├── ARCHITECTURE.md
├── EXTENDING.md
├── PROJECT-MEMORY.md
├── LEARNING-LOG.md
├── FRAMEWORK-EVALUATION.md        # NEW in v3
├── pyproject.toml
├── requirements.txt
└── config.json
```

---

## Metadata Schema

### domains.json (Updated v3)

```json
{
  "schema_version": "2.0.0",
  "last_updated": "2025-12-22T00:00:00Z",

  "constitution": {
    "document": "ai-interaction-principles-v1.4.md",
    "version": "1.4.0",
    "always_search": true,
    "description": "Meta-Principles - Universal behavioral rules"
  },

  "s_series_triggers": {
    "S1_privacy": {
      "keywords": ["data", "personal", "privacy", "user data", "collect", "store", "share", "PII", "GDPR", "consent"],
      "phrases": ["user information", "personal data", "data collection"]
    },
    "S2_security": {
      "keywords": ["security", "vulnerability", "exploit", "attack", "breach", "injection", "XSS", "credential"],
      "phrases": ["security risk", "vulnerable to", "might expose"]
    },
    "S3_harm": {
      "keywords": ["illegal", "discriminate", "abuse", "harm", "dangerous", "malicious"],
      "phrases": ["could harm", "might abuse", "illegal activity"]
    }
  },

  "domains": {
    "ai-coding": {
      "name": "AI Coding",
      "description": "AI-assisted software development",
      "documents": {
        "principles": "ai-coding-domain-principles-v2.1.md",
        "methods": "ai-coding-methods-v1.0.3.md"
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

    "multi-agent": {
      "name": "Multi-Agent",
      "description": "Multi-agent AI system design and orchestration",
      "documents": {
        "principles": "multi-agent-domain-principles-v1.0.1.md",
        "methods": "multi-agent-methods-v1.0.0.md"
      },
      "versions": {
        "principles": "1.0.1",
        "methods": "1.0.0"
      },
      "trigger_keywords": [
        "multi-agent", "agent", "orchestrator", "orchestration",
        "coordination", "handoff", "context isolation", "specialist",
        "validator", "generator-critic", "cognitive function",
        "agent swarm", "parallel agents", "hierarchical agents"
      ],
      "trigger_phrases": [
        "multiple agents", "agent coordination", "orchestrate agents",
        "agent handoff", "context pollution", "validation independence",
        "agent specialization", "cognitive specialization"
      ],
      "priority": 2
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

  "default_domain": null,

  "detection_config": {
    "min_keyword_matches": 1,
    "phrase_match_boost": 2.0,
    "case_sensitive": false,
    "whole_word_only": true
  }
}
```

### principles.json (Expanded Schema v3)

```json
{
  "schema_version": "2.0.0",
  "last_updated": "2025-12-22T00:00:00Z",

  "principles": {
    "coding-C1": {
      "id": "coding-C1",
      "name": "Specification Completeness",
      "nickname": "The Requirements Act",
      "document": "ai-coding-domain-principles-v2.1.md",
      "document_type": "domain",
      "domain": "ai-coding",
      "series": "Context",
      "series_code": "C",
      "hierarchy_level": 3,

      "summary": "Don't code without complete specifications - AI will hallucinate to fill gaps",

      "keywords": [
        "specification", "requirements", "complete", "gaps",
        "unclear", "ambiguous", "incomplete", "missing"
      ],

      "synonyms": [
        "specs", "spec", "reqs", "requirements doc",
        "feature request", "user story"
      ],

      "aliases": [
        "C1", "requirements act", "spec completeness"
      ],

      "failure_indicators": [
        "guessing", "assuming", "unclear", "not sure",
        "probably", "might be", "I think"
      ],

      "trigger_phrases": [
        "specifications seem", "requirements are unclear",
        "spec is incomplete", "not enough detail"
      ],

      "failure_modes": [
        "incomplete specifications",
        "hallucinated implementation",
        "ambiguous requirements"
      ],

      "applies_when": [
        "starting implementation",
        "requirements seem incomplete",
        "about to write code",
        "specifications have gaps"
      ],

      "escalation_triggers": [
        "specification gaps detected",
        "ambiguous requirements",
        "missing user behavior definitions"
      ],

      "derives_from": ["meta-C1", "meta-C2", "meta-Q1"],
      "derived_by": [],

      "line_range": [245, 380],
      "cache_file": "cache/coding-C1.md"
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
- ai-coding: AI-assisted software development (12 principles)
- multi-agent: Multi-agent system orchestration (11 principles)

**Immediate Escalation Triggers:**
- S-Series violation (security, privacy, harm)
- Specification gaps preventing safe implementation
- Repeated failures (2+ attempts)

**To retrieve principles:** Use get_relevant_principles(context)
```

---

### Tool 2: `get_principle`

**Purpose:** Retrieve single complete principle by ID.

**Parameters:**
- `principle_id` (string, required): e.g., "meta-C1", "coding-C1", "multi-A1"

**Returns:** Complete principle text from cache file, never chunked.

**Error Response (NEW v3):**
```json
{
  "error": "Principle not found",
  "id": "unknown-X1",
  "suggestion": "Use get_active_domains() to see available principles"
}
```

---

### Tool 3: `get_relevant_principles`

**Purpose:** Context-aware retrieval with multi-domain support.

**Parameters:**
- `context` (string, required): Current situation description
- `domain` (string, optional): Explicit domain override ("ai-coding", "multi-agent", "general", or null for auto-detect)
- `include_constitution` (bool, optional, default=True): Include Constitution principles in **output** (Constitution always searched internally)
- `include_methods` (bool, optional, default=False): Include relevant methods
- `max_results` (int, optional, default=5): Maximum principles to return per category

**Returns:**
```markdown
---
## Governance Principles Retrieved

**Active Domain(s):** AI Coding, Multi-Agent
**Detection Method:** Auto-detected from keywords ["implement", "multi-agent"]

### S-Series (SAFETY - Supreme Authority)
[If any S-Series triggered, shown FIRST]

---

### Constitution (Always Applies)

#### meta-C1: Context Engineering
[Full principle text]

---

### AI Coding Domain

#### coding-C1: Specification Completeness (The Requirements Act)
[Full principle text]

---

### Multi-Agent Domain

#### multi-A1: Cognitive Function Specialization
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

---

### Tool 4: `get_validation_criteria` (Output Schema NEW v3)

**Purpose:** Get quality gates for a specific phase.

**Parameters:**
- `phase` (string, required): "specify", "plan", "tasks", "implement"
- `domain` (string, optional): Domain context (default: ai-coding)

**Returns:**
```json
{
  "phase": "implement",
  "domain": "ai-coding",
  "criteria": [
    {
      "id": "impl-1",
      "name": "Tests Pass",
      "description": "All unit and integration tests pass",
      "severity": "required",
      "check": "Run pytest and verify 0 failures"
    },
    {
      "id": "impl-2",
      "name": "No Security Vulnerabilities",
      "description": "No HIGH or CRITICAL security issues",
      "severity": "required",
      "check": "Run security scanner, review results"
    },
    {
      "id": "impl-3",
      "name": "Documentation Updated",
      "description": "README and inline docs reflect changes",
      "severity": "required",
      "check": "Review documentation for accuracy"
    }
  ],
  "gate_artifact": "GATE-IMPLEMENT.md",
  "source_document": "ai-coding-methods-v1.0.3.md",
  "source_section": "Title 5: Implement Procedures"
}
```

---

### Tool 5: `get_escalation_triggers` (Output Schema NEW v3)

**Purpose:** All conditions requiring human intervention.

**Parameters:**
- `category` (string, optional): "safety", "security", "process", "technical"
- `domain` (string, optional): Domain-specific triggers

**Returns:**
```json
{
  "triggers": [
    {
      "id": "esc-s1",
      "category": "safety",
      "severity": "critical",
      "trigger": "S-Series violation detected",
      "action": "STOP immediately, flag to human, do not proceed",
      "source": "ai-interaction-principles (S-Series)"
    },
    {
      "id": "esc-p1",
      "category": "process",
      "severity": "high",
      "trigger": "Specification gaps preventing safe execution",
      "action": "Pause implementation, request clarification",
      "source": "ai-coding-domain-principles (C1)"
    },
    {
      "id": "esc-t1",
      "category": "technical",
      "severity": "medium",
      "trigger": "Multiple valid approaches with significant implications",
      "action": "Present options to Product Owner with recommendation",
      "source": "ai-coding-methods (Title 1)"
    }
  ],
  "categories": ["safety", "security", "process", "technical"],
  "severity_levels": ["critical", "high", "medium", "low"]
}
```

---

### Tool 6: `search_governance` (Output Schema NEW v3)

**Purpose:** Keyword search across all documents.

**Parameters:**
- `query` (string, required): Search terms
- `document_filter` (string, optional): "constitution", "domain", "methods", or null for all
- `domain` (string, optional): Limit domain scope
- `max_results` (int, optional, default=5)

**Returns:**
```json
{
  "query": "specification gaps",
  "document_filter": null,
  "results": [
    {
      "principle_id": "coding-C1",
      "name": "Specification Completeness",
      "relevance_score": 4.5,
      "match_reasons": [
        "keyword: specification",
        "failure_indicator: gaps"
      ],
      "excerpt": "Don't code without complete specifications...",
      "document": "ai-coding-domain-principles-v2.1.md"
    }
  ],
  "total_found": 3,
  "search_strategy": "keyword_phrase_metadata"
}
```

---

### Tool 7: `get_active_domains`

**Purpose:** List available domains and current state.

**Parameters:** None

**Returns:**
```json
{
  "available_domains": [
    {
      "id": "ai-coding",
      "name": "AI Coding",
      "principle_count": 12,
      "trigger_keywords_sample": ["code", "implement", "test"]
    },
    {
      "id": "multi-agent",
      "name": "Multi-Agent",
      "principle_count": 11,
      "trigger_keywords_sample": ["agent", "orchestrator", "handoff"]
    }
  ],
  "default_domain": null,
  "constitution_document": "ai-interaction-principles-v1.4.md",
  "constitution_principle_count": 12
}
```

---

### Tool 8: `set_session_domain`

**Purpose:** Set domain for subsequent retrievals in this session.

**Parameters:**
- `domain` (string, required): Domain identifier, "general" for Constitution-only, or null to reset to auto-detect

**Returns:** Confirmation with domain principle count.

**Note:** Session-level setting. Does not persist across conversations.

---

### Tool 9: `get_cold_start_prompt`

**Purpose:** Retrieve ready-to-use prompts from methods.

**Parameters:**
- `scenario` (string, required): "new_project", "resume_work", "recovery"
- `domain` (string, optional, default from config)

**Returns:** Copy-paste prompt template from methods document.

**Error Response:**
```json
{
  "error": "Scenario not found",
  "scenario": "training_model",
  "available_scenarios": ["new_project", "resume_work", "recovery"]
}
```

---

## Test Scenarios (Updated v3)

### Scenario 1: Domain Auto-Detection (AI Coding)
**Input:** `get_relevant_principles("specs seem incomplete, should I proceed?")`
**Expected:** Domain = "ai-coding", returns coding-C1 + meta-C1

### Scenario 2: Domain Auto-Detection (Multi-Agent)
**Input:** `get_relevant_principles("how should I orchestrate these agents?")`
**Expected:** Domain = "multi-agent", returns multi-A1, multi-R2

### Scenario 3: Multi-Domain Overlap (NEW v3)
**Input:** `get_relevant_principles("implement a multi-agent code review system")`
**Expected:** Domains = ["ai-coding", "multi-agent"], returns principles from BOTH

### Scenario 4: Constitution Only
**Input:** `get_relevant_principles("help me think through this problem", domain="general")`
**Expected:** Only Constitution principles returned

### Scenario 5: S-Series Priority
**Input:** `get_relevant_principles("this might expose user data")`
**Expected:** S-Series (Privacy) returned FIRST, then others

### Scenario 6: Methods Retrieval
**Input:** `get_relevant_principles("starting new project", include_methods=True)`
**Expected:** Returns principles + Cold Start procedure from methods

### Scenario 7: Unknown Domain Keyword
**Input:** `get_relevant_principles("write a blog post about AI")`
**Expected:** No domain match, Constitution only

### Scenario 8: Empty Query (NEW v3)
**Input:** `get_relevant_principles("")`
**Expected:** Returns governance summary (same as get_governance_summary)

### Scenario 9: Principle Not Found (NEW v3)
**Input:** `get_principle("unknown-X1")`
**Expected:** Error response with suggestion

---

## Success Criteria (Updated v3)

### Functional
- [ ] All 35+ principles indexed with complete metadata (including synonyms, aliases)
- [ ] Domain auto-detection works for both ai-coding and multi-agent keywords
- [ ] Multi-domain queries return principles from all matching domains
- [ ] Constitution always searched (even if include_constitution=false)
- [ ] S-Series principles appear first when relevant
- [ ] Principles returned complete (never chunked)
- [ ] New domain can be added without code changes
- [ ] Works with Claude Code CLI

### Performance
- [ ] Retrieval < 500ms
- [ ] Typical response: 1,500-3,000 tokens (vs 55K full load)
- [ ] Server startup < 2 seconds
- [ ] **Miss rate < 5%** (with expanded metadata)

### Quality
- [ ] Match explanations provided
- [ ] Compliance prompt included
- [ ] Hierarchy clearly indicated in response

### Documentation (Required for Completion)
- [ ] README.md enables setup in < 10 minutes
- [ ] EXTENDING.md validated by following steps
- [ ] ARCHITECTURE.md explains all major design decisions
- [ ] PROJECT-MEMORY.md reflects current state
- [ ] LEARNING-LOG.md captures lessons from development
- [ ] **FRAMEWORK-EVALUATION.md** captures meta-observations (NEW v3)
- [ ] docs/tool-reference.md documents all 9 MCP tools
- [ ] docs/schema-reference.md documents all JSON schemas
- [ ] docs/troubleshooting.md covers common issues

---

## Documentation Requirements

### Required Documentation Deliverables (Updated v3)

```
/Users/jasoncollier/Developer/ai-governance-mcp/
├── README.md                      # Human-facing: Setup, usage
├── ARCHITECTURE.md                # Technical design and rationale
├── EXTENDING.md                   # How to add domains
├── PROJECT-MEMORY.md              # AI context: Decisions, patterns
├── LEARNING-LOG.md                # Lessons learned
├── FRAMEWORK-EVALUATION.md        # Meta-observations about framework (NEW v3)
└── docs/
    ├── tool-reference.md          # Complete MCP tool documentation
    ├── schema-reference.md        # JSON schema documentation
    └── troubleshooting.md         # Common issues and solutions
```

### FRAMEWORK-EVALUATION.md Template (NEW v3)

```markdown
# Framework Evaluation - Meta-Observations

## Purpose
Track observations about how well the AI Governance Framework works in practice.
This is meta-evaluation: evaluating the framework itself, not project-specific lessons.

## Observations

### [Date] - [Category]
**Principle/Method Evaluated:** [e.g., C1 Specification Completeness]
**Context:** What we were doing
**Observation:** What worked or didn't work
**Recommendation:** Potential framework improvement

---

### Categories
- **Principle Effectiveness:** Did the principle prevent the failure mode it addresses?
- **Method Usability:** Was the procedure easy to follow?
- **Trigger Accuracy:** Did escalation triggers fire appropriately?
- **Gap Identified:** Missing principle or method needed
- **Over-engineering:** Principle/method more complex than needed

## Summary Statistics
| Category | Count |
|----------|-------|
| Principles that worked well | 0 |
| Principles that need revision | 0 |
| Methods that worked well | 0 |
| Methods that need revision | 0 |
| Gaps identified | 0 |
```

---

## Configuration

### config.json (Updated v3)

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
    "always_search_constitution": true,
    "always_check_s_series": true,
    "semantic_ranking_enabled": false,
    "semantic_model": "all-MiniLM-L6-v2"
  },

  "logging": {
    "enabled": true,
    "format": "jsonl",
    "include_context": false,
    "destination": "stderr"
  },

  "domains": {
    "default": null,
    "auto_detect": true
  }
}
```

---

## Implementation Requirements

### Dependencies

```toml
[project]
name = "ai-governance-mcp"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-asyncio>=0.21.0"]
semantic = ["sentence-transformers>=2.2.0"]
```

### MCP Best Practices (from research)

1. **Use FastMCP 2.0** - Decorator-based, handles schema generation
2. **Error handling via isError flag** - Not protocol-level errors
3. **Logging to stderr** - stdout reserved for JSON-RPC messages
4. **Two-tool pattern** - search (get_relevant_principles) + fetch (get_principle)

---

## Phase Outputs

This specification serves as the **SPECIFY phase output** (v3 complete).

**Next Phases:**

1. **PLAN:** Define architecture, technology choices, component design
2. **TASKS:** Break into atomic implementation tasks (≤15 files each)
3. **IMPLEMENT:** Write → Run → Validate cycle

**Validation Gate (GATE-SPECIFY v3):**
- [x] Problem clearly defined
- [x] Solution architecture specified
- [x] All tools documented with parameters/returns and output schemas
- [x] Extensibility mechanism defined
- [x] Test scenarios provided (including edge cases)
- [x] Success criteria measurable
- [x] Documentation deliverables defined with templates
- [x] **Retrieval algorithm explicitly specified** (NEW v3)
- [x] **S-Series triggers defined** (NEW v3)
- [x] **Multi-domain conflict resolution defined** (NEW v3)
- [x] **Edge case handling documented** (NEW v3)

---

**End of Specification v3**
