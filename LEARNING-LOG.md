# AI Governance MCP - Learning Log

## Purpose
This log captures lessons learned during development. Review before making changes.

---

## Lessons

### 2026-01-04 - Custom Subagent Files Are Reference Documentation, Not Invokable Types

**Context:** Created 4 coding subagent definition files in `.claude/agents/` following §2.1 Subagent Definition Standard. Attempted to invoke them via Task tool.

**What Happened:**
```
Task tool error: Agent type 'code-reviewer' not found.
Available agents: general-purpose, statusline-setup, Explore, Plan, claude-code-guide, orchestrator
```

**Discovery:** The Task tool has a fixed set of built-in `subagent_type` values. Custom `.claude/agents/*.md` files do NOT automatically register as new invokable types.

**What Custom Agent Files Actually Do:**
1. Serve as **reference documentation** for the project
2. Can be read and their instructions provided to `general-purpose` agent
3. Define roles/personas that Claude can reference when asked
4. The `orchestrator` appears in the list because it's a **built-in** type, not because of our `.claude/agents/orchestrator.md` file

**Working Pattern for Custom Agents:**
```python
# Instead of:
Task(subagent_type="code-reviewer", prompt="Review this code")  # ❌ Fails

# Do this:
Task(
    subagent_type="general-purpose",
    prompt="""You are a Code Reviewer specialist. [Include role instructions]

    Review this code: ..."""
)  # ✓ Works
```

**Why This Matters:**
- Subagent definition files are still valuable as structured role documentation
- They follow prompt engineering best practices (cognitive function, boundaries, examples)
- They can be programmatically read and injected into prompts
- But they're not "registered agents" that the Task tool knows about

**Lesson:**
- Claude Code's Task tool has predefined agent types
- Custom `.claude/agents/` files are project-level role definitions/documentation
- To use custom roles, read the file and provide instructions inline to general-purpose agent
- The `install_agent` MCP tool creates files for project reference, not Task tool registration

---

### 2026-01-04 - Claude Desktop and CLI Have Separate MCP Configurations (CRITICAL)

**Context:** User reported "0 domains" when using ai-governance MCP from another project.

**What Happened:** Server connected successfully but returned empty data. Investigation revealed:
- Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`) had env vars ✓
- Claude Code CLI config (`~/.claude.json`) did NOT have env vars ✗
- Server silently fell back to CWD-based path detection, which failed from other directories

**Root Cause:** Assumption that configuring Claude Desktop also configured Claude Code CLI. They are completely independent systems with separate config files.

**Silent Failure Pattern:** The server connects and responds, but with no data. This is worse than a hard error because users think it's working but don't understand why it's empty.

**Diagnostic Commands That Revealed Issue:**
```bash
# Shows if env vars are set (look for empty "Environment:" section)
claude mcp get ai-governance

# Shows what paths the server actually resolves to
python -c "
from ai_governance_mcp.config import Settings
s = Settings()
print(f'index exists: {(s.index_path / \"global_index.json\").exists()}')
"
```

**Fixes Applied:**
1. Added troubleshooting section to README with diagnostic checklist
2. Added note in Claude Code CLI section about separate configs
3. Added startup logging showing resolved paths (so users can verify)
4. Config generator now auto-includes env vars with correct paths

**Lesson:** When building MCP servers that depend on file paths:
1. Never rely on CWD-based path detection for user-installed servers
2. Always require explicit paths via env vars or config
3. Log resolved paths at startup so users can verify
4. Fail loudly or warn when index files are missing, don't silently return empty data

---

### 2026-01-04 - Security Hardening Phase 2: Defense-in-Depth Patterns

**Context:** Implemented remaining high/medium priority items from Gemini security review.

**New Patterns Applied:**

1. **Token Bucket Rate Limiting** (H4)
   ```python
   RATE_LIMIT_TOKENS = 100  # Max requests in bucket
   RATE_LIMIT_REFILL_RATE = 10  # Tokens/second

   def _check_rate_limit() -> bool:
       global _rate_limit_tokens, _rate_limit_last_refill
       now = time.time()
       elapsed = now - _rate_limit_last_refill
       _rate_limit_tokens = min(RATE_LIMIT_TOKENS,
           _rate_limit_tokens + (elapsed * RATE_LIMIT_REFILL_RATE))
       if _rate_limit_tokens >= 1:
           _rate_limit_tokens -= 1
           return True
       return False
   ```
   - Simple in-process rate limiter (no Redis needed for single-instance)
   - Burst-friendly: allows 100 rapid requests before throttling
   - Self-recovering: refills at 10/sec

2. **Secrets Redaction Pattern** (M4)
   ```python
   SECRET_PATTERNS = [
       (re.compile(r'(?i)(api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?'),
        r'\1=***REDACTED***'),
       (re.compile(r'(?i)(bearer)\s+([a-zA-Z0-9_\-\.]{20,})'),
        r'\1 ***REDACTED***'),
       # ... more patterns
   ]

   def _sanitize_for_logging(content: str) -> str:
       for pattern, replacement in SECRET_PATTERNS:
           content = pattern.sub(replacement, content)
       return content
   ```
   - Apply BEFORE writing to logs, not after
   - Regex patterns for common secret formats
   - Better to over-redact than miss secrets

3. **Error Sanitization Pattern** (M6)
   ```python
   def _sanitize_error_message(error: Exception) -> str:
       message = str(error)
       # Remove absolute paths (keep filename only)
       message = re.sub(r'(?:[A-Za-z]:)?(?:[/\\][^/\\]+)+[/\\]([^/\\]+)', r'\1', message)
       # Remove line numbers
       message = re.sub(r', line \d+', '', message)
       return message
   ```
   - Never expose internal paths to users
   - Line numbers can reveal code structure
   - Memory addresses are implementation details

4. **JSON Schema Validation in MCP** (M5)
   ```python
   "query": {
       "type": "string",
       "maxLength": MAX_QUERY_LENGTH,  # Explicit limit
       "minLength": 1,                  # No empty strings
   },
   "domain": {
       "type": "string",
       "enum": ["constitution", "ai-coding", "multi-agent"],  # Allowlist
   }
   ```
   - MCP clients may validate schemas before sending
   - Defense-in-depth: validate at schema AND handler level
   - Enums prevent injection of arbitrary domain names

**Lesson:** Security is layers. Rate limiting prevents DoS. Secrets redaction prevents data leaks. Error sanitization prevents info disclosure. Schema validation prevents injection. No single layer is sufficient.

---

### 2026-01-03 - Security Hardening via External Review Pattern (CRITICAL)

**Context:** Requested comprehensive project review focusing on security. Used a sub-agent to provide "fresh eyes" perspective on the codebase.

**Review Findings:**

| Priority | ID | Issue | Fix Applied |
|----------|-----|-------|-------------|
| Critical | C1 | Unbounded `_audit_log` list | `deque(maxlen=1000)` |
| Critical | C2 | Path traversal in agent install | `.resolve()` + containment check |
| High | H1 | No query length limits | `MAX_QUERY_LENGTH = 10000` |
| High | H2 | Sync file I/O in async handlers | `asyncio.to_thread()` |
| High | H3 | `os._exit()` loses buffered logs | `_flush_all_logs()` + `os.fsync()` |

**Key Patterns Applied:**

1. **Bounded Collections for Long-Running Processes**
   ```python
   from collections import deque
   _audit_log: deque[GovernanceAuditLog] = deque(maxlen=1000)
   ```
   - Prevents memory growth in long sessions
   - FIFO eviction preserves recent entries
   - No performance penalty vs list

2. **Path Containment Check Pattern**
   ```python
   final_path = (base_path / f"{agent_name}.md").resolve()
   if not str(final_path).startswith(str(base_path.resolve())):
       raise ValueError("Path traversal detected")
   ```
   - Always validate agent_name against allowlist FIRST
   - Then resolve paths and verify containment
   - Defense in depth: allowlist + path check

3. **Async Logging with Explicit Flush**
   ```python
   async def log_query_async(query_log: QueryLog) -> None:
       await asyncio.to_thread(_write_log_sync, log_file, content)

   def _write_log_sync(log_file: Path, content: str) -> None:
       with open(log_file, "a") as f:
           f.write(content)
           f.flush()  # Explicit flush for shutdown safety
   ```
   - `asyncio.to_thread()` for non-blocking file I/O
   - Explicit `flush()` reduces data loss on shutdown
   - Separate sync helper enables clean async wrapper

4. **Graceful Shutdown with Log Flush**
   ```python
   def _flush_all_logs() -> None:
       for log_file in log_files:
           with open(log_file, "a") as f:
               f.flush()
               os.fsync(f.fileno())  # Force OS buffers to disk

   # Called in signal handler AND finally block
   _flush_all_logs()
   os._exit(0)
   ```
   - `os.fsync()` forces OS buffers to physical disk
   - Cover both shutdown paths (signal + pipe close)

**Lesson:** Regular security reviews by fresh perspectives catch issues that become invisible to primary developers. Pattern: schedule external review after major feature completions.

**False Positive Note:** `evaluate_governance()` returned ESCALATE for implementing security *fixes* due to keyword matching on "security". This was correctly overridden since implementing security improvements aligns with governance principles.

---

### 2026-01-03 - Governance Enforcement Patterns Research

**Context:** Explored how to make AI compliance with governance principles *automatic* rather than "hope-based" (AI might ignore instructions to call `evaluate_governance`).

**Research Findings:**

| Approach | Enforcement Level | Limitations |
|----------|------------------|-------------|
| **Instructions** (current) | Hope-based | AI can skip |
| **Claude Code Hooks** | Partial | Can block tools, cannot modify prompts or force agent routing |
| **MCP Proxy/Gateway** | Tool-level only | Enforces governance before tool calls, cannot enforce reasoning patterns |
| **LangChain Middleware** | Full (custom app) | Requires building wrapper app, not an MCP enhancement |
| **MCP Resources** | Client-dependent | Elegant but inconsistent client support |

**Key Insight:** "Governance rules won't live inside the agent—they'll sit above it, enforced by governance services or agent policy gateways." True enforcement requires architectural control, not better instructions.

**Claude Code Specifics:**
- `UserPromptSubmit` hook can see/block prompts but **cannot modify or reroute**
- `PreToolUse` hook can block writes until governance called (partial enforcement)
- Cannot force `/agent:orchestrator` routing programmatically
- Orchestrator agent exists but must be explicitly invoked

**Conclusion:** True automatic enforcement for all platforms requires either (a) wrapper application with LangChain/LiteLLM middleware, or (b) waiting for MCP ecosystem to mature with better client-side resource auto-loading.

**Sources:** [Claude Code Hooks Docs](https://docs.anthropic.com/en/docs/claude-code/hooks), [LangChain Middleware](https://medium.com/@pankaj_pandey/langchain-middleware-precise-control-around-the-agent-loop-1030a1c8e3ea), [Lasso MCP Gateway](https://github.com/lasso-security/mcp-gateway), [Portkey MCP Best Practices](https://portkey.ai/blog/best-practices-for-securing-and-governing-mcp-tools/)

---

### 2025-12-31 - Task Tracking Belongs in Working Memory (Research-Backed)
**Context:** User identified gap where SESSION-STATE referenced task IDs (T1, T2) without defining what those tasks are. Needed to decide where task definitions should live.
**Research:** Reviewed 2025 AI agent memory architecture best practices from AIS, Zep, MongoDB, IBM. Key finding: "Task decomposition creates a structure that memory can track. The list of subtasks becomes part of the agent's state."
**Analysis:** Considered four alternatives:
1. Inline in SESSION-STATE (working memory)
2. Separate TASK-LIST.md file
3. In PROJECT-MEMORY.md (semantic memory)
4. GitHub Issues (external system)
**Decision:** Project-specific tasks are ephemeral (created in Tasks phase, consumed in Implement phase, then cleared). Unlike reusable procedures, they belong in working memory for immediate access. Integrated Active Tasks table into main SESSION-STATE template (§7.1.2).
**Lesson:** Research before assuming first solution is correct. Working vs. semantic vs. procedural memory serve different purposes—match content to memory type.
**Sources:** [AIS Memory Patterns](https://www.ais.com/practical-memory-patterns-for-reliable-longer-horizon-agent-workflows/), [Zep AI Agents](https://www.getzep.com/ai-agents/introduction-to-ai-agents/), [MongoDB Agent Memory](https://www.mongodb.com/resources/basics/artificial-intelligence/agent-memory)

---

### 2025-12-24 - Specification Documents Are Not Validated Requirements (CRITICAL)
**Context:** Implemented full MCP server based on specification-v3.md which said "~5% miss rate with keyword matching"
**What Happened:** After implementation was complete, Product Owner review revealed:
- 5% miss rate is unacceptable for production compliance tool
- Semantic understanding is CRITICAL, not optional
- This is a showcase project, not minimal viable
- PO wants "advanced, effective" solution, not "skimping"

**Root Cause:** **Anchor Bias** - The specification document was treated as validated requirements instead of as input to a discovery process. The spec became a constraint rather than a starting point.

**Principles Violated:**
- **C1 (Specification Completeness):** "No Assumptions - flag and ask"
- **P4 (Human-AI Collaboration):** "Escalate with options, wait for explicit decision"
- **Constitution:** "Pause and request human clarification before proceeding"

**Lesson:** A specification document, even a detailed one, is NOT the same as validated Product Owner requirements. Before implementing architectural decisions:
1. Run discovery questions with PO
2. Present options with tradeoffs (per P4)
3. Wait for explicit approval
4. The spec informs the process but doesn't replace it

**Action:**
- Returning to SPECIFY phase for proper discovery
- Must complete discovery questions before redesigning
- Will implement hybrid retrieval (BM25 + semantic) based on actual PO requirements

**Framework Note:** The principles themselves are correct - the failure was in application. Consider adding explicit check to CLAUDE.md: "If entering mid-project, verify previous phase artifacts were properly validated with PO."

---

### 2025-12-22 - Specification Completeness Critical
**Context:** Beginning implementation of MCP server based on specification-v2.md
**What Happened:** Thorough review revealed specification was only ~70% complete. Critical gaps included undefined retrieval algorithm, missing S-Series triggers, unspecified output formats for 3 tools, and contradictory parameters.
**Lesson:** Even "complete" specifications may have gaps. Per C1 (Specification Completeness), verify specification completeness before implementation, not just at the start.
**Action:** Created specification-v3.md with all gaps addressed. Added specification review to standard workflow.

---

### 2025-12-22 - Miss Rate Analysis for Search Approaches
**Context:** Deciding between keyword, semantic, or hybrid search approaches
**What Happened:** Research showed pure keyword matching has 20-25% miss rate, semantic embeddings <3%, but semantic adds PyTorch (~2GB dependency).
**Lesson:** There's a middle ground: expanded metadata (synonyms, aliases, failure_indicators) achieves ~5% miss rate with zero heavy dependencies.
**Action:** Chose expanded keyword approach. Added synonyms, aliases, failure_indicators to principle schema.

---

### 2025-12-22 - Multi-Domain Retrieval Needed
**Context:** Designing domain detection behavior
**What Happened:** Realized queries like "implement a multi-agent code review system" touch both ai-coding and multi-agent domains. Single-domain selection would miss relevant principles.
**Lesson:** Real-world queries often span domains. Design should support multi-domain retrieval, not force single-domain selection.
**Action:** Updated domain resolution to return list of domains. Added conflict resolution logic for ties.

---

### 2025-12-22 - stdout Reserved for MCP
**Context:** Researching MCP SDK best practices
**What Happened:** MCP protocol uses stdout for JSON-RPC messages. Logging to stdout would break protocol.
**Lesson:** Always log to stderr when building MCP servers.
**Action:** Added logging configuration requirement: `stream=sys.stderr`.

---

### 2025-12-27 - ML Model Mocking Pattern for Tests (CRITICAL)

**Context:** Writing comprehensive tests for retrieval engine with SentenceTransformer and CrossEncoder.

**What Happened:** Initial mock at `ai_governance_mcp.retrieval.SentenceTransformer` failed with `AttributeError: module does not have attribute`.

**Root Cause:** Models are lazy-loaded inside property methods, not imported at module level. The import happens when the property is first accessed.

**Solution:** Patch at the source: `sentence_transformers.SentenceTransformer` instead of where it's used.

**Pattern:**
```python
with patch("sentence_transformers.SentenceTransformer", mock_st):
    with patch("sentence_transformers.CrossEncoder", mock_ce):
        # Test code here
```

**Lesson:** When mocking lazy-loaded dependencies, patch at the source module level, not at the consumer module level.

---

### 2025-12-27 - Mock Embedder Array Shape (CRITICAL)

**Context:** Mock embedder was returning a static numpy array.

**What Happened:** Tests failed with `TypeError: only length-1 arrays can be converted to Python scalars` when batch operations were performed.

**Root Cause:** Mock returned same array regardless of input size. Batch embedding expects array shape `(num_texts, embedding_dim)`.

**Solution:** Use `side_effect` function that dynamically returns correctly-shaped arrays:
```python
def mock_encode(texts, *args, **kwargs):
    if isinstance(texts, str):
        return np.random.rand(384).astype(np.float32)
    return np.random.rand(len(texts), 384).astype(np.float32)
embedder.encode = Mock(side_effect=mock_encode)
```

**Lesson:** When mocking functions that handle variable-size inputs, use `side_effect` with a function, not `return_value`.

---

### 2025-12-27 - Falsy Values in Validation Tests

**Context:** Testing rating validation in log_feedback with rating=0.

**What Happened:** Rating=0 triggered "required field" error before the range validation check.

**Root Cause:** In Python, `if not rating:` treats 0 as falsy, same as missing.

**Solution:** Use rating=-1 to test invalid low values (clearly invalid but not falsy).

**Lesson:** When testing validation boundaries, consider Python's truthiness rules. Zero is falsy.

---

### 2025-12-27 - Shared Test Fixtures Pattern

**Context:** Multiple test files needed same fixtures (mock embedder, sample principles, test settings).

**What Happened:** Initially duplicated fixture code across test files.

**Solution:** Created `tests/conftest.py` with comprehensive shared fixtures:
- `sample_principle`, `sample_s_series_principle` - Model fixtures
- `mock_embedder`, `mock_reranker` - ML model mocks
- `test_settings`, `saved_index` - Configuration fixtures
- `reset_server_state` - Server singleton cleanup

**Lesson:** Invest in `conftest.py` early. Shared fixtures reduce duplication and ensure consistent test behavior.

---

## Patterns That Worked

| Pattern | Context | Why It Worked |
|---------|---------|---------------|
| Fix spec first | Spec had gaps | Prevented implementation rework |
| Research before deciding | Search approach | Found better middle-ground option |
| Gate artifacts | Phase transitions | Clear validation checkpoints |
| **Process Map visualization** | Discovery phase | PO visibility into workflow position |
| **conftest.py fixtures** | Test suite | Shared fixtures, 205 tests, 90% coverage |
| **side_effect for mocks** | ML model mocking | Handles variable input sizes correctly |
| **Patch at source** | Lazy-loaded deps | Works when imports are inside methods |
| **CPU-only PyTorch in CI** | ML project CI/CD | Avoids 4GB CUDA deps that fill disk |
| **fail-fast: false** | Matrix debugging | See all failures, not just first |
| **Per-response reminder** | MCP governance | Uniform reinforcement prevents drift |
| **os._exit(0) for stdio** | MCP shutdown | Stdio transport can't be gracefully cancelled |
| **Explicit checkpoints** | Governance enforcement | Tell AI WHEN to query, not just WHAT |

### 2025-12-26 - Process Map Visualization Pattern (PO APPROVED)

**Context:** During SPECIFY discovery phase, PO requested more visibility into where we are in the process.

**What Worked:** ASCII process map showing:
- Current phase and sub-steps
- Checkmarks for completed items
- Arrow marker for current position
- Preview of upcoming phases

**Example Format:**
```
SPECIFY PHASE — Discovery (§2.1)
─────────────────────────────────────────────────────────────────────────────
├── [✓] Completed item
├── [✓] Another completed item
├── [~] Current item ◄── CURRENT QUESTION
├── [ ] Upcoming item
└── [ ] Final item in section

NEXT PHASE (after gate)
─────────────────────────────────────────────────────────────────────────────
├── Future work preview
└── GATE-*.md
```

**PO Feedback:** "That Process Map is perfect."

**Application Rule:** Show updated process map:
- After major accomplishments
- On request for updates
- At phase transitions
- Periodically during long discovery conversations

**Why It Works:**
1. Provides context without requiring PO to ask
2. Helps PO "think accordingly" based on where we are
3. Shows progress momentum
4. Previews what's coming next

### 2025-12-26 - Communication Level Calibration (PO APPROVED)

**Context:** Technical discussions were getting too detailed for efficient PO review.

**PO Guidance:** "Interview-ready" level — what and why in brief sentences. Enough to explain to others, not implementation details. PO will ask for deeper dives when needed.

**Application Rule:**
- Default: High-level what/why (1-2 sentences per concept)
- On request: Mid-level detail (our recent exchanges)
- Deep dive: Only when explicitly requested

**Example:**
- Too detailed: "We use sentence-transformers with all-MiniLM-L6-v2 which produces 384-dimensional embeddings..."
- Right level: "We use industry-standard embedding models to convert text to vectors for semantic search."

### 2025-12-26 - Portfolio-Ready README Pattern (PO APPROVED)

**Context:** Project will be showcased as portfolio item for recruiters, customers, and SME audiences.

**Insight:** Specification (internal planning doc) ≠ README (external showcase). Different audiences, different framing.

**Multi-Audience README Structure:**
1. **Headline + Hook** — What it does in one line
2. **Problem Statement** — Relatable pain point
3. **Solution Overview** — What it does
4. **Key Innovation** — The differentiator (for this project: the governance framework)
5. **Tech Stack** — Skills showcase (recruiters look here)
6. **Architecture** — System design credibility
7. **How It Works** — Technical depth
8. **Results/Metrics** — Quantifiable outcomes
9. **Getting Started** — Proves it's real and usable
10. **The Methodology** — Thought leadership content
11. **About** — Positioning

**Differentiator Statement (template):**
> "Most people use AI as-is. I built a governance framework that makes AI collaboration systematic, repeatable, and production-ready — then built an MCP that operationalizes it."

**Audience Priorities (in order):**
1. Recruiters — skills match, problem-solving, modern stack
2. Customers — methodology, results, professionalism
3. SME/Presenters — novel approach, depth, teachable
4. General — clear explanations, reproducible patterns

**Application Rule:** For portfolio-worthy projects, create README.md as derived artifact from spec, formatted for external audience.

### 2025-12-27 - GitHub Actions CI/CD Lessons (CRITICAL)

**Context:** Setting up CI pipeline for automated testing, linting, and security scanning.

**Issues Encountered:**

1. **Lint Failures - Unused Imports (F401)**
   - Ruff flagged unused imports we hadn't noticed locally
   - Fix: Run `ruff check --fix src/ tests/` before committing
   - Lesson: Add pre-commit hooks or run linter locally before push

2. **Lint Failures - Ambiguous Variable Name (E741)**
   - `O = "O"` in enum flagged as confusable with zero
   - Fix: Renamed to `OPER = "O"`
   - Lesson: Linters catch issues humans miss; embrace them

3. **Disk Space Exhaustion (Errno 28)**
   - `sentence-transformers` pulls PyTorch with CUDA (~900MB torch + ~3GB nvidia-*)
   - GitHub Actions runners have ~14GB disk; CUDA dependencies filled it
   - Fix: Pre-install CPU-only PyTorch before other deps:
     ```yaml
     pip install torch --index-url https://download.pytorch.org/whl/cpu
     pip install -e ".[dev]"
     ```
   - Lesson: ML libraries default to GPU builds; explicitly use CPU for CI

4. **Matrix Job Cancellation (fail-fast)**
   - Default `fail-fast: true` cancels sibling matrix jobs on first failure
   - Made debugging harder (couldn't see if 3.11/3.12 would pass)
   - Fix: Add `fail-fast: false` to matrix strategy
   - Lesson: Disable fail-fast during debugging; re-enable for faster CI later

**Best Practices Established:**
- Run `ruff check src/ tests/ && ruff format --check src/ tests/` locally before push
- Use CPU-only PyTorch in CI for ML projects
- Set `continue-on-error: true` for informational checks (pip-audit)
- Use `fail-fast: false` initially, optimize later

### 2025-12-28 - Regex Quantifier Bug in Method Extraction

**Context:** Methods from ai-coding-methods-v1.1.0.md weren't being extracted despite extractor code existing.

**What Happened:** Extractor reported "0 methods" for ai-coding. Investigation revealed regex `\d+(?:\.\d+)?` only matched 1-2 level section numbers (like `1.2`) but not 3-level (like `1.2.3`).

**Root Cause:** Regex quantifier `?` means "0 or 1", not "0 or more". The pattern needed `*` instead.

**Fix:** Changed `\d+(?:\.\d+)?` to `\d+(?:\.\d+)*`

**Lesson:** When matching repeating patterns like version numbers or section numbers, use `*` (zero or more) not `?` (zero or one). Test regex patterns with actual document samples before assuming they work.

---

### 2025-12-28 - Domain Routing Threshold and Fallback

**Context:** Queries like "unit tests in Python" weren't being routed to ai-coding domain, so ai-coding methods weren't returned.

**What Happened:** Domain similarity threshold was 0.5, but typical query-to-domain similarities were 0.25-0.40. Also, when no domain passed threshold, system only searched constitution.

**Fixes Applied:**
1. Lowered threshold from 0.5 to 0.25
2. Added fallback: search ALL domains when no specific match
3. Enriched domain descriptions with common query terms

**Lesson:** Semantic similarity thresholds need empirical tuning. Default fallback behavior (searching all vs searching none) matters more than threshold precision. Domain descriptions should include the vocabulary users actually query with, not just formal category terms.

---

### 2025-12-28 - Large File Operations Can Cause Session Hangs

**Context:** Restructuring Constitution (2,578 lines) to separate principles from methods.

**What Happened:** Previous session got stuck while attempting to create a new Constitution v2.0 file. The approach was: read file in chunks, construct content in memory, write entire file with Write tool.

**Root Cause:** Large file Write operations (potentially 1,600+ lines) may timeout or cause issues in Claude Code.

**Solution:** Use shell tools for large file manipulation:
```bash
# Extract only lines to keep (safer than large Write)
sed -n '1,67p; 393,1721p; 2523,$p' old.md > new.md
```

Then use Edit tool for small, targeted changes (version headers, amendment entries).

**Lesson:** For large file restructuring:
1. Copy original file first (`cp old.md new.md`)
2. Use `sed -n` to extract sections, OR use `sed -d` to delete sections
3. Use Edit tool for small targeted changes
4. Avoid constructing large files in-memory and writing all at once

**Principles Applied:**
- Break complex operations into atomic steps
- Use the right tool for the job (shell for bulk, Edit for precision)
- Document approach in SESSION-STATE so recovery is possible if session fails

---

### 2025-12-28 - Constitution/Methods Separation Pattern

**Context:** AI interaction principles document was 2,578 lines mixing WHAT (principles) with HOW (procedures).

**What Happened:** Document was hard to navigate, hard to maintain, and violated Single Source of Truth principle (procedural content was duplicated or inconsistent with methods docs).

**Pattern Applied:** Legal system analogy - separate Constitution (principles, immutable law) from Procedures (methods, operational implementation).

**Result:**
- Constitution: 2,578 → 1,476 lines (42 principles only)
- Methods: 835 → 1,489 lines (added TITLEs 7/8/9)
- Clear separation of concerns
- Each document has single purpose

**Lesson:** For governance frameworks:
1. Principles define WHAT (rules, constraints, requirements)
2. Methods define HOW (procedures, workflows, checklists)
3. Keep them in separate documents
4. Reference via clear cross-links
5. Version independently (principles change rarely, methods evolve)

**Framework Impact:** Domain principles should follow same pattern - domain-principles.md for rules, domain-methods.md for procedures.

---

### 2025-12-29 - Framework Bootstrap/Activation Problem (CRITICAL)

**Context:** Comprehensive review of governance framework for completeness and proper AI integration.

**What Happened:** Despite having a complete governance framework (Constitution, 2 domains, methods for each), a fresh Claude Code session had no automatic way to:
1. Know the governance framework exists
2. Know to query the MCP server
3. Follow the activation protocol

**Root Cause:** The framework had all the rules (principles) and procedures (methods), but no **entry point**. It's like having laws but no way to tell citizens the laws exist.

**Solution - Three-Layer Activation:**

1. **CLAUDE.md** (auto-loaded by Claude Code)
   - Tool-specific entry point
   - Points to ai-instructions and MCP
   - Created in project root

2. **ai-instructions-v2.3.md** (loader document)
   - Full activation protocol
   - Domain detection rules
   - First response protocol
   - Now includes multi-agent domain and MCP integration

3. **ai-governance-methods "Framework Activation" section**
   - Documents the bootstrap sequence
   - References ai-instructions as the canonical loader
   - Closes the documentation loop

**Bootstrap Sequence:**
```
Tool Config (CLAUDE.md) → ai-instructions → Constitution → Domain → Methods
```

**Lesson:** A governance framework needs THREE things:
1. **Rules** (principles) - WHAT to do
2. **Procedures** (methods) - HOW to do it
3. **Activation** (loader) - HOW TO GET STARTED

The third is often forgotten. Without explicit activation, the framework exists but isn't used.

**Pattern:** For any governance/ruleset system:
- Always create an entry point document
- Document how AI/users discover and activate the rules
- Reference the loader from the methods so the documentation is complete

---

### 2025-12-29 - Anchor Bias in Document Review

**Context:** Reviewing governance documents that I had been working on in the same session.

**What Happened:** User explicitly requested "fresh eyes" and "avoiding anchor bias" when reviewing documents. This was a reminder that working on documents creates familiarity that can blind you to issues.

**Mitigation Strategies Used:**
1. Query external best practices (web search) for comparison
2. Test MCP retrieval to see how it performs
3. Check version references systematically (found several outdated)
4. Look for missing pieces, not just errors in existing pieces

**Lesson:** When reviewing your own work:
- Explicitly search for gaps (what's missing) not just errors (what's wrong)
- Compare against external standards
- Check cross-references systematically
- The user asking to "avoid anchor bias" is a signal to use external validation

---

### 2025-12-31 - Per-Response Governance Reminder Pattern (PO APPROVED)

**Context:** AI clients may drift from governance principles over long conversations since SERVER_INSTRUCTIONS are only injected once at MCP initialization.

**Research Conducted:**
- MCP specification has no built-in per-response reminder mechanism
- Claude Code uses `<system-reminder>` tags repeatedly — validates the pattern
- Token cost (~30 tokens) is trivial in 100K+ context windows

**Solution:** Append compact, action-oriented reminder to every tool response.

**Implementation Pattern:**
```python
GOVERNANCE_REMINDER = """

---
⚖️ **Governance Check:** Did you `query_governance()` before this action? Cite influencing principle IDs. S-Series = veto authority."""

def _append_governance_reminder(result: list[TextContent]) -> list[TextContent]:
    """Append governance reminder to tool response."""
    if result and result[0].text:
        result[0] = TextContent(type="text", text=result[0].text + GOVERNANCE_REMINDER)
    return result

# In call_tool(): always call _append_governance_reminder(result) before return
```

**Test Pattern:** When testing responses with appended reminders, use helper to extract primary content:
```python
def extract_json_from_response(text: str) -> str:
    """Extract JSON portion from response, stripping governance reminder."""
    separator = "\n\n---\n⚖️"
    if separator in text:
        return text.split(separator)[0]
    return text
```

**Design Principles:**
- Self-check question triggers reflection better than statements
- ~35 tokens (minimal overhead)
- Covers: query reminder, citation requirement, S-Series veto

**Why It Works:** Uniform reinforcement at every interaction ensures AI clients don't drift, even in long conversations.

**Note:** Later optimized from passive statement (📋) to self-check question (⚖️) — see "MCP Instruction Optimization" entry below.

---

### 2025-12-29 - MCP Server Shutdown: Stdio Transport Requires Immediate Exit

**Context:** AI governance MCP server wouldn't exit cleanly when Claude App quit.

**Investigation Process:**
1. Initially suspected sentence-transformers threads keeping process alive
2. Added SIGTERM/SIGINT handlers with asyncio coordination
3. Found that asyncio coordination doesn't work for stdio transport (synchronous I/O)
4. Research found Postgres MCP server uses `os._exit(0)` pattern

**Root Cause:** MCP stdio transport uses synchronous I/O that can't be gracefully interrupted or cancelled. Async event coordination doesn't help when the underlying I/O is blocking.

**Solution:** Use `os._exit(0)` for immediate termination:
```python
import os
import signal

def handle_shutdown(signum, frame):
    logger.info(f"Received signal {signum}, forcing exit...")
    os._exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Also in finally block for pipe closure:
try:
    await server.run()
finally:
    os._exit(0)
```

**Lesson:** For MCP servers using stdio transport, don't try to gracefully shutdown — use immediate exit. This is the standard pattern used by production MCP servers (e.g., Postgres MCP).

---

### 2025-12-29 - Claude App Quit Bug is NOT MCP Server Issue

**Context:** After implementing graceful shutdown, Claude App still hung on quit.

**Investigation:**
1. MCP server logs showed clean exit: "Received signal 15, forcing exit..."
2. Process list showed no orphaned ai-governance processes
3. Tested with MCP config removed — same hang behavior
4. Claude App main.log showed: stuck after "marking readyForQuit" — never fires final quit

**Conclusion:** Claude App has an Electron bug where it marks `readyForQuit` but never fires the final quit handler. This is NOT caused by MCP servers.

**Lesson:** When debugging multi-component systems, isolate each component. Remove suspected causes one at a time. The obvious suspect isn't always the culprit.

---

## Patterns That Failed

| Pattern | Context | Why It Failed |
|---------|---------|---------------|
| Spec-as-requirements | Treated spec v3 as validated requirements | Spec was a starting point, not PO approval. Built wrong architecture. |
| Optimize for stated constraints | Optimized for "~5% miss rate" in spec | Never verified PO actually wanted that constraint. |
| Skip discovery for existing docs | Had detailed spec, skipped discovery questions | Spec authors' assumptions ≠ PO's actual requirements |

---

## Future Considerations

1. ~~**Hybrid retrieval implementation:**~~ COMPLETE - all-MiniLM-L6-v2 for embeddings, ms-marco-MiniLM-L-6-v2 for reranking, 60/40 semantic/keyword fusion.
2. **Cross-tool synchronization:** Multi-agent domain mentions claude.md ↔ gemini.md sync. Not in v1 scope but may need future support.
3. **Hot reload:** Currently requires server restart for domain changes. Could add file watcher.
4. **Public deployment:** PO wants this online for others. Need to consider hosting, API rate limits, and scalability.
5. **Additional domains:** Prompt engineering, RAG optimization, sci-fi/fantasy writing, hotel analysis planned.
6. **Knowledge graph tier:** Tier 3 enhancement for relationship-based retrieval if needed.

---

### 2025-12-31 - Memory Architecture Research: Cognitive Types and Industry Patterns (CRITICAL)

**Context:** Reviewing gaps in ai-coding-methods memory architecture to determine best practices.

**Research Conducted:**
- AI agent memory systems (Mem0, IBM, Medium/Navyasree Potluri)
- Architecture Decision Records (AWS, adr.github.io, Microsoft, MADR)
- Phase gate patterns (Sonar, Teamwork, ZetCode)
- Context file patterns (Anthropic, HumanLayer, Softcery)
- Task tracking (GitHub Docs, TrackDown)

**Key Findings:**

**1. Cognitive Memory Types (CoALA Framework)**
AI agents benefit from three distinct memory types, mirroring human cognition:
- **Semantic Memory** — facts and knowledge (decisions, architecture, constraints)
- **Episodic Memory** — events and experiences (lessons learned, what happened)
- **Procedural Memory** — how to do things (workflows, methods, checklists)
- Plus: **Working Memory** — what's active right now (session state)

Source: Princeton's "Cognitive Architectures for Language Agents" paper; IBM; Medium

**2. ADR Best Practices**
- ADRs are **immutable** once accepted — new decisions supersede, don't modify
- Store as numbered files: `decisions/NNNN-title.md`
- Answer: What, Why, When, Who, Alternatives, Consequences
- ADRs are for *decisions*, not checkpoints

Source: AWS Prescriptive Guidance; adr.github.io; Microsoft Azure Well-Architected

**3. Context File Patterns (CLAUDE.md)**
- CLAUDE.md is the "constitution" — AI's primary source of truth for a repo
- **Progressive disclosure**: tell AI how to find info, not all info upfront
- **Less is more**: fewer instructions are better
- Hierarchical: root + subdirectory files for scoped context

Source: Anthropic Claude Code Best Practices; HumanLayer

**4. Gate Artifacts vs Inline Tracking**
- Gates are checkpoints, not decisions — different from ADRs
- Quality gates integrate with CI/CD for automated enforcement
- Hybrid agile + gate approach is industry standard
- Excessive separate files create coordination overhead

Source: Sonar Quality Gates; Teamwork Phase-Gate

**5. Task Tracking**
- GitHub task lists auto-update when referenced issues close
- TrackDown: markdown-based issue tracking versioned with code
- Tasks are working memory — should live close to session state

Source: GitHub Docs; TrackDown project

**6. Memory Pruning**
- Need explicit eviction/pruning policies to avoid bloat
- "Never rely on LLM's implicit weights alone for anything you need to recall with fidelity"
- Priority scoring and contextual tagging to decide what gets stored

Source: Mem0; Medium/Nayeem Islam

**Implications for ai-coding-methods:**
1. Map memory files to cognitive types explicitly
2. Eliminate separate gate artifact files — integrate into semantic memory (PROJECT-MEMORY)
3. Formalize CLAUDE.md as "loader" using progressive disclosure
4. Tasks belong in working memory (SESSION-STATE) or external system (GitHub Issues)
5. Add principles-based pruning guidance, not line-count rules

**Sources:**
- [Mem0: Memory in AI Agents](https://mem0.ai/blog/memory-in-agents-what-why-and-how)
- [IBM: What Is AI Agent Memory](https://www.ibm.com/think/topics/ai-agent-memory)
- [Medium: Semantic vs Episodic vs Procedural Memory](https://medium.com/womenintechnology/semantic-vs-episodic-vs-procedural-memory-in-ai-agents-and-why-you-need-all-three-8479cd1c7ba6)
- [AWS: Architecture Decision Records](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/welcome.html)
- [adr.github.io](https://adr.github.io/)
- [Microsoft: ADR Well-Architected](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)
- [Anthropic: Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [HumanLayer: Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Sonar: Quality Gates](https://www.sonarsource.com/learn/quality-gate/)
- [GitHub: Planning and Tracking](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

---

### 2025-12-31 - Pre-Flight Validation Pattern for Configuration Errors

**Context:** After updating ai-coding-methods.md from v1.1.1 to v2.0.0, the extractor silently produced "0 methods" because domains.json still referenced the old filename.

**What Happened:** The extractor would gracefully handle missing files (return empty list), which meant configuration errors were silently ignored. User discovered the issue only by checking extraction output.

**Root Cause:** Fail-silent vs fail-fast design. The original design prioritized "graceful handling" but this hid configuration errors that should be immediately visible.

**Solution - Pre-Flight Validation Pattern:**
```python
class ExtractorConfigError(Exception):
    """Raised when extractor configuration is invalid (e.g., missing files)."""
    pass

def validate_domain_files(self) -> None:
    """Pre-flight validation: ensure all configured files exist.

    Lists ALL missing files, not just the first one found.
    Provides actionable guidance (check domains.json).
    """
    missing_files: list[str] = []

    for domain_config in self.domains:
        principles_path = self.settings.documents_path / domain_config.principles_file
        if not principles_path.exists():
            missing_files.append(f"  - {domain_config.name}: principles file '{domain_config.principles_file}'")
        # ... check methods file too

    if missing_files:
        raise ExtractorConfigError(
            f"Domain configuration references missing files:\n{...}\n\n"
            f"Check documents/domains.json and ensure file versions match."
        )

def extract_all(self) -> GlobalIndex:
    # Pre-flight validation: fail fast if files are missing
    self.validate_domain_files()  # <-- First thing!
    # ... rest of extraction
```

**Key Pattern Elements:**
1. **Fail fast** — Check configuration BEFORE expensive operations
2. **Report ALL errors** — Collect all missing files, not just first
3. **Actionable message** — Tell user WHERE to look (domains.json)
4. **CI test coverage** — Add tests that verify validation works

**Tests Added:**
- `test_validate_domain_files_passes_for_valid_config`
- `test_validate_domain_files_raises_for_missing_principles`
- `test_validate_domain_files_raises_for_missing_methods`
- `test_validate_domain_files_reports_all_missing`
- `test_validate_domain_files_suggests_checking_domains_json`

**Lesson:** For configuration-driven systems (like domain registries), validate configuration at startup, not during operation. Silent failures hide problems; clear errors fix them.

**Pattern Application:** Any system that loads external configuration should:
1. Validate all config references exist before starting work
2. Report ALL problems in one error, not one at a time
3. Include remediation hints in error messages
4. Have CI tests that verify validation catches bad configs

---

### 2025-12-31 - Governance Reminder Present ≠ Governance Applied (CRITICAL)

**Context:** After implementing per-response governance reminders ("📋 **Governance:** Query on decisions/concerns..."), tested whether the reminder actually changed behavior.

**What Happened:** User asked me to review whether I followed the governance principles during the session. Self-audit revealed:

1. **Did not query MCP at session start** — CLAUDE.md says "Query ai-governance MCP for relevant principles" but I skipped this
2. **Did not cite influencing principles** — Made decision on confidence thresholds without citing the governance principle that guided it
3. **Did not query before implementation** — Added detection heuristics without querying for relevant principles/methods
4. **Did not pause on format gaps** — Made formatting decisions (e.g., "*Detect via:*" style) without checking template standards

**Root Cause:** The reminder tells me WHAT to do, but doesn't force me to do it. I received the instructions but proceeded with implementation without actively querying the MCP.

**Analogy:** Having a speed limit sign doesn't make you slow down. Having a governance reminder doesn't make you query governance.

**Lesson:** Passive reminders are necessary but not sufficient. Active mechanisms may be needed:
1. The reminder exists (✓)
2. The AI reads the reminder (✓)
3. The AI acts on the reminder (✗ — this failed)

**Solution Implemented (Phase 1):**

1. **Enhanced Governance Reminder** — Changed from passive statement to explicit action triggers:
   ```
   📋 **Governance Checkpoints:**
   - **Before implementing** → `query_governance("your task")`
   - **Before decisions** → query, then cite influencing principle
   - **On uncertainty** → pause and clarify with user
   ```

2. **Explicit Checkpoints in CLAUDE.md** — Added mandatory query points:
   - Starting any implementation task
   - Making architectural or configuration decisions
   - Modifying governance documents or templates
   - Phase transitions

**Phase 2 Planned (With Multi-Agent):**
- Governance Agent as specialized agent in multi-agent architecture
- Pre-action check, principle injection, post-action audit
- Based on GaaS and Superagent Safety Agent patterns

**Key Insight:** Industry research (2025) shows passive reminders are necessary but insufficient. The progression is:
1. Passive reminders (tell AI what to do) — necessary baseline
2. Explicit checkpoints (tell AI WHEN to do it) — Phase 1
3. Interceptive enforcement (force compliance) — Phase 2

**Sources:**
- [Governance-as-a-Service](https://arxiv.org/html/2508.18765v2)
- [Superagent Safety Agent](https://www.helpnetsecurity.com/2025/12/29/superagent-framework-guardrails-agentic-ai/)
- [Agentic AI Safety Playbook 2025](https://dextralabs.com/blog/agentic-ai-safety-playbook-guardrails-permissions-auditability/)

---

### 2026-01-01 - Multi-Agent Domain v2.0.0 Research Synthesis (CRITICAL)

**Context:** Comprehensive update to multi-agent domain principles and methods, moving from v1.3.0 (parallel coordination only) to v2.0.0 (individual/sequential/parallel coverage).

**Research Conducted:**
- Anthropic Multi-Agent Research System (engineering blog)
- Google ADK "Architecting Efficient Context-Aware Multi-Agent Framework" (developer blog)
- Cognition "Don't Build Multi-Agents" (practitioner blog)
- LangChain "How and When to Build Multi-Agent Systems" (vendor blog)
- Microsoft Multi-Agent Reference Architecture (documentation)
- Vellum "Multi-Agent Context Engineering" (vendor blog)

**Key Findings:**

**1. Anthropic Multi-Agent Research System**
- Achieved 90.2% improvement over single-agent baseline
- BUT: 15x token usage (cost/latency tradeoff)
- Orchestrator-worker pattern with specialization
- Key insight: improvement comes from specialization, not just parallelization

**2. Cognition "Don't Build Multi-Agents"**
- "Actions carry implicit decisions. Conflicting decisions carried by conflicting actions carry bad results."
- Problem: Parallel agents make independent implicit decisions that conflict
- Solution: Read-Write Division — parallelize reads, serialize writes
- Solution: Shared Assumptions Protocol before parallel execution
- Key insight: Sequential (linear) is safer default; parallel requires validation

**3. Google ADK Context Engineering**
- "A focused 300-token context often outperforms an unfocused 113,000-token context."
- Two handoff patterns: Agents-as-Tools (stateless) vs Agent-Transfer (stateful)
- Four context strategies: Write, Select, Compress, Isolate
- `include_contents` configuration determines what transfers between agents

**4. LangChain "When to Build Multi-Agent"**
- Multi-agent justified ONLY when task exceeds single-agent capability
- Justifications: context window limits, parallelization opportunity, cognitive mismatch, quality improvement
- "Specialization" applies even to sequential single-agent workflows
- Multi-agent overhead must be justified by proportional value

**5. Vellum Context Engineering**
- Context compression at boundaries is critical
- Preserve: decisions, constraints, artifacts
- Compress: reasoning chains, exploratory dead ends

**Synthesis — Resolution of Apparent Contradictions:**

Anthropic shows 90% improvement; Cognition warns against multi-agent. Both are correct:
- **Read-heavy tasks** (research, analysis): Parallelize with shared assumptions → major gains
- **Write-heavy tasks** (synthesis, decisions): Serialize to single agent → avoid conflicts
- **Sequential specialization**: Use specialized agent configs sequentially without parallel overhead

**Principles Derived:**
| Principle | Source | Constitutional Basis |
|-----------|--------|----------------------|
| Justified Complexity | Cognition, LangChain | Resource Efficiency |
| Context Engineering Discipline | Google ADK, Vellum | Context Engineering |
| Read-Write Division | Cognition, LangChain | Role Specialization |
| Shared Assumptions Protocol | Cognition | Standardized Collaboration |
| Linear-First Orchestration | Industry consensus | Discovery Before Commitment |

**Key Concept — Modular Personalities:**
An agent is not a separate program — it's a specialized *configuration* of the same underlying model. Think of it as a "hat" the AI wears: different system prompt, different tools, different cognitive focus. The same base model becomes a coder, validator, or orchestrator based on its agent definition.

This reframing explains why:
- Specialization helps even for single-agent sequential workflows
- Agents don't need separate infrastructure — just configuration
- The "multi-agent" domain covers individual specialized agents too

**Sources:**
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Google ADK Context Engineering](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Cognition: Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
- [LangChain: How and When to Build Multi-Agent](https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/)
- [Microsoft Multi-Agent Reference Architecture](https://microsoft.github.io/multi-agent-reference-architecture/docs/context-engineering/Context-Engineering.html)
- [Vellum: Multi-Agent Context Engineering](https://www.vellum.ai/blog/multi-agent-systems-building-with-context-engineering)

---

### 2026-01-01 - Governance Agent Implementation: evaluate_governance Tool (CRITICAL)

**Context:** Implementing active governance enforcement through the Governance Agent pattern from multi-agent-methods-v2.0.0 (§4.3 and §2.2.6).

**Governance Queried Before Implementation:**
- `multi-method-governance-agent-pattern` — Assess compliance before action
- `multi-method-agent-definition-standard` — Required agent components
- `meta-quality-verification-mechanisms-before-action` — Validate before acting

**Design Decisions Made:**

| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| Retrieval approach | Use existing `retrieve()` | DRY, tested, maintained |
| S-Series detection | Dual-path (principles + keywords) | Veto authority demands active checking |
| Confidence scoring | Retrieval scores + S-Series override | Match quality = assessment quality |

**Implementation Components:**

1. **Pydantic Models** — `AssessmentStatus`, `ComplianceStatus`, `RelevantPrinciple`, `ComplianceEvaluation`, `SSeriesCheck`, `GovernanceAssessment`

2. **S-Series Keyword Detection** — 25 safety-related keywords (delete, credential, password, security, production, deploy, database, user data, pii, sensitive, etc.)

3. **Dual-Path S-Series Checking:**
   - Check returned principles for `series_code="S"`
   - Keyword scan action description for safety terms
   - Either path triggers ESCALATE

4. **Confidence Logic:**
   - S-Series triggered → HIGH (safety is not uncertain)
   - Best score ≥0.7 → HIGH
   - Best score ≥0.4 → MEDIUM
   - Otherwise → LOW

**Key Pattern: Active vs. Passive Enforcement**

| Approach | Mechanism | Guarantee |
|----------|-----------|-----------|
| Passive | GOVERNANCE_REMINDER | Suggests but can be ignored |
| Active | `evaluate_governance` | Validates before action proceeds |

**Lesson:** Passive reminders are insufficient for critical governance. Active enforcement through pre-action validation provides stronger guarantees. The Governance Agent pattern from multi-agent-methods-v2.0.0 provides a reusable design for this.

---

### 2026-01-01 - MCP Instruction Optimization: Constraint-Based + Model-Specific Patterns (CRITICAL)

**Context:** Reviewing SERVER_INSTRUCTIONS and GOVERNANCE_REMINDER for optimization. Previous version was "passive" — described what to do but didn't enforce it. Self-assessment earlier in session confirmed AI ignored reminders in practice.

**Governance Queried Before Implementation:**
- `meta-operational-constraint-based-prompting` — explicit constraints reduce ambiguity
- `meta-method-instructions-content` — required sections (Overview, When to Use, Hierarchy, Behaviors, Quick Start)
- `meta-method-server-instructions` — server provides behavioral instructions to AI clients

**Key Optimizations Applied:**

**1. Action Framing: Suggestive → Mandatory**
| Before | After |
|--------|-------|
| "When to Use" (optional) | "Required Actions" (mandatory) |
| "Key Behaviors" (passive) | "Forbidden Actions" (explicit constraints) |
| "Cite principles..." (suggestion) | "Do NOT proceed without querying..." (constraint) |

**2. Forbidden Actions Section Added**
Explicit constraints per `meta-operational-constraint-based-prompting`:
```
### Forbidden Actions
- Do NOT proceed with implementation without querying applicable principles
- Do NOT make product/business/timeline decisions — escalate to user
- Do NOT ignore S-Series principles under any circumstances
```

**3. Model-Specific Guidance Added**
Different frontier models have different instruction-following patterns:

| Model | Optimization |
|-------|-------------|
| Claude | Extended thinking for governance analysis |
| GPT-4/o1 | Sandwich method — query at start, verify before finalizing |
| Gemini | Hierarchical headers for citations |
| Llama/Mistral | Repeat S-Series at decision points |
| All | "When unsure whether to query — query. False positives are cheap." |

**4. Self-Check Prompt Pattern**
Changed reminder from statement to question:
```
Before: 📋 **Governance Checkpoints:** ...
After:  ⚖️ **Governance Check:** Did you `query_governance()` before this action?
```
Questions trigger reflection; statements can be ignored.

**5. Token Efficiency**
- Removed duplicate hierarchy (was in both instructions and reminder)
- Instructions: ~200 → ~380 tokens (more content, but only injected once)
- Reminder: ~40 → ~35 tokens (tighter, per-response)
- Net effect: Better guidance with minimal token overhead

**Implementation Notes:**

1. Test separator changed: `📋` → `⚖️` in `extract_json_from_response()` helper
2. All 220 tests pass after update
3. Comments in code cite applicable principles:
   ```python
   # Per meta-operational-constraint-based-prompting: explicit constraints reduce ambiguity.
   # Per meta-method-instructions-content: includes Overview, When to Use, Hierarchy, Behaviors, Quick Start.
   ```

**Lesson:** System instructions are not just documentation — they're behavioral contracts. Apply prompt engineering principles:
1. **Constraint-based**: Explicit forbidden actions, not just suggestions
2. **Model-specific**: Different models need different optimization patterns
3. **Self-check**: Questions ("Did you...?") trigger reflection better than statements
4. **Action-oriented**: "Required Actions" not "When to Use"

**Pattern for Future MCP Servers:**
```python
SERVER_INSTRUCTIONS = """
### Required Actions
1. Action 1 — Call tool_name("param") before X
2. Action 2 — Reference IDs when Y

### Hierarchy (Binding Order)
| Priority | Source | Scope |
|----------|--------|-------|
| 1 | Critical | Veto authority |
| 2 | Standard | Apply always |

### Forbidden Actions
- Do NOT X without Y
- Do NOT make Z decisions — escalate

### Model-Specific Guidance
**Claude**: ...
**GPT-4**: ...
"""

GOVERNANCE_REMINDER = """
---
⚖️ **Check:** Did you do X? Cite IDs. Critical = veto.
"""
```

**Sources Applied:**
- `meta-operational-constraint-based-prompting` (governance principle)
- `meta-method-instructions-content` (governance method)
- Prompt engineering sandwich method (GPT-4 optimization)
- Self-check questioning pattern (behavioral psychology)

---

### 2026-01-03 - Docker Distribution Pattern for MCP Servers

**Context:** Implementing Docker containerization for easy distribution to end users who may not have Python environments set up.

**Key Decisions Made:**

1. **Multi-Stage Build** — Separate builder (gcc, index generation) from runtime
   - Builder stage: Installs gcc, builds index, generates embeddings
   - Runtime stage: Minimal image with pre-built index copied over
   - Result: Faster startup, smaller final image

2. **CPU-Only PyTorch** — Critical for image size
   ```dockerfile
   RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
   ```
   - Default PyTorch pulls CUDA (~2GB)
   - CPU-only version is ~200MB
   - Saves ~1.8GB per image

3. **Non-Root User** — Security hardening
   ```dockerfile
   RUN useradd --create-home --shell /bin/bash appuser
   USER appuser
   ```
   - Containers shouldn't run as root
   - Creates dedicated user for the application

4. **Pre-Built Index** — Avoid runtime model loading
   - Builder stage runs extractor to generate embeddings
   - Runtime stage copies pre-built index
   - First query still loads ML models, but index is ready

5. **README.md Dependency** — pyproject.toml quirk
   - `pyproject.toml` has `readme = "README.md"`
   - pip install fails if README.md isn't present
   - Must COPY README.md alongside pyproject.toml

**MCP-Specific Considerations:**

- MCP uses stdio (stdin/stdout), not HTTP
- Container must run with `-i` flag (interactive)
- Health check imports server module, doesn't start it
- docker-compose.yml includes `stdin_open: true` and `tty: true`

**CI/CD Pattern:**

```yaml
# Trigger on version tags
on:
  push:
    tags:
      - 'v*.*.*'

# Publish to Docker Hub with version + latest
tags: |
  ${{ env.IMAGE_NAME }}:${{ steps.version.outputs.version }}
  ${{ env.IMAGE_NAME }}:latest
```

**Image Size Breakdown:**

| Component | Size |
|-----------|------|
| Base Python 3.11-slim | ~150MB |
| PyTorch CPU | ~200MB |
| sentence-transformers | ~500MB |
| Other deps | ~300MB |
| Index + documents | ~50MB |
| **Total** | **~1.6GB** |

**Lesson:** For ML-based MCP servers, Docker distribution trades image size (~1.6GB) for installation simplicity. The multi-stage build pattern and CPU-only PyTorch are essential optimizations.

**Pattern Reusable For:** Any MCP server with ML dependencies.

---

## Research Links (from 2025-12-24 session)

Hybrid retrieval best practices:
- [Elastic Hybrid Search Guide](https://www.elastic.co/what-is/hybrid-search)
- [Genzeon: Hybrid Retrieval and Reranking](https://www.genzeon.com/hybrid-retrieval-deranking-in-rag-recall-precision/)
- [Microsoft: Common RAG Techniques](https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/02/04/common-retrieval-augmented-generation-rag-techniques-explained/)
- [Unstructured: RAG Without Embeddings](https://unstructured.io/blog/rethinking-rag-without-embeddings)
- [Security Boulevard: Smart Retrieval for Compliance](https://securityboulevard.com/2025/04/why-smart-retrieval-is-critical-for-compliance-success/)

Embedding models:
- [all-MiniLM-L6-v2 on HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) - 22MB, 384 dimensions, good baseline
- [Sentence Transformers Documentation](https://sbert.net/docs/quickstart.html)

---

## 2026-01-01 - Claude Code Agent Definitions (Research)

### What Are Claude Code Agents?

Claude Code agents are **specialized AI configurations** — not separate programs, but focused "personalities" with:
- Their own system prompt defining behavior
- Restricted (or full) tool access
- Their own context window (isolated from main conversation)
- Optionally a different model (haiku for speed, opus for depth)

**Key insight:** An agent is essentially a prompt + tool constraints applied to the same underlying model.

### File Format: Markdown with YAML Frontmatter

```markdown
---
name: agent-name
description: When/why to use this agent (triggers automatic invocation)
tools: Tool1, Tool2, Tool3  # Optional - omit to inherit all
model: sonnet              # Optional - sonnet, opus, haiku, or inherit
permissionMode: default    # Optional - default, acceptEdits, bypassPermissions
skills: skill1, skill2     # Optional - skills to auto-load
---

System prompt goes here. This defines the agent's personality,
role, and instructions. Can be multiple paragraphs.

When invoked:
1. Do this first
2. Then do this
...
```

### Storage Locations

| Location | Scope | Priority | Use Case |
|----------|-------|----------|----------|
| `.claude/agents/*.md` | Project | **Highest** | Team-shared, checked into git |
| `~/.claude/agents/*.md` | User | Lower | Personal, all projects |

Project-level agents override user-level agents with the same name.

### Agent Definition Fields (Complete Reference)

| Field | Required | Description |
|-------|----------|-------------|
| `name` | **Yes** | Unique identifier (lowercase + hyphens) |
| `description` | **Yes** | Natural language for when to invoke. Use "PROACTIVELY" to encourage auto-delegation |
| `tools` | No | Comma-separated list. Omit to inherit all tools |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | `default`, `acceptEdits`, `bypassPermissions`, `plan`, `ignore` |
| `skills` | No | Skills to auto-load (agents don't inherit parent's skills) |

### How to Create Agents

**Method 1: Interactive (Recommended)**
```bash
/agents
# Select "Create New Agent"
# Choose project or user scope
# Describe purpose
# Select tools interactively
```

**Method 2: Manual File Creation**
```bash
mkdir -p .claude/agents
cat > .claude/agents/my-agent.md << 'EOF'
---
name: my-agent
description: Description here
tools: Read, Edit, Bash
---
System prompt here
EOF
```

**Method 3: CLI Flag (Session-specific)**
```bash
claude --agents '{
  "agent-name": {
    "description": "...",
    "prompt": "...",
    "tools": ["Read", "Grep"]
  }
}'
```

### How Agents Get Invoked

1. **Automatic**: Claude reads `description` and matches to task
2. **Explicit**: User says "Use the X agent to..."
3. **Task tool**: `subagent_type: "agent-name"` in programmatic calls

### Built-in Agents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| general-purpose | Sonnet | All | Complex multi-step tasks |
| Plan | Sonnet | Read-only | Research in plan mode |
| Explore | Haiku | Read-only | Fast codebase search |

### Example: Code Reviewer Agent

```markdown
---
name: code-reviewer
description: Expert code review specialist. PROACTIVELY reviews code after writing or modifying. Use immediately after code changes.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer ensuring high standards of quality and security.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets or API keys
- Input validation implemented
- Good test coverage

Provide feedback by priority:
- Critical (must fix)
- Warnings (should fix)
- Suggestions (consider)

Include specific examples of how to fix issues.
```

### Tool Restriction Enforcement

| Platform | Enforcement Level |
|----------|------------------|
| Claude Code | **Hard** — CLI enforces tool restrictions |
| Other LLMs via MCP | **Soft** — LLM must honor guidance |

For non-Claude-Code LLMs, tool restrictions are advisory. Mitigation:
- Layer 1: Prompt says "don't use X"
- Layer 2: `evaluate_governance` should be called first
- Layer 3: `verify_governance_compliance` catches bypasses
- Layer 4: Audit log records everything

### LLM-Agnostic Agent Design

Claude Code agents (`.claude/agents/`) are platform-specific. For LLM-agnostic agents:

| Approach | How It Works |
|----------|--------------|
| MCP Resources | Expose `resource://ai-governance/agents/orchestrator` |
| MCP Tool | `get_agent_definition("orchestrator")` returns structured definition |
| Document-based | Store in `documents/agents/`, retrieve via `query_governance` |
| SERVER_INSTRUCTIONS | Include role guidance in MCP init |

**Recommended hybrid:**
1. Source of truth in `documents/agents/*.md`
2. Claude Code gets `.claude/agents/` (platform-specific)
3. MCP tool `get_agent_definition()` for LLM-agnostic access

### Sources

- [Claude Code Subagents Documentation](https://code.claude.com/docs/en/sub-agents)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference.md)
- [Building agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Agent Skills Documentation](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

## 2026-01-01 - Cross-Platform Agent Installation: Only Claude Code Has Local Agents (CRITICAL)

### Context
Designing how to install Orchestrator and Governance agents across multiple AI platforms (Claude Code, Gemini CLI, ChatGPT, Grok, Perplexity).

### Research Findings

**Platform Agent Support Matrix:**

| Platform | Local Agent Files? | Agent Mechanism | Notes |
|----------|-------------------|-----------------|-------|
| **Claude Code** | ✅ `.claude/agents/*.md` | YAML frontmatter + system prompt | Project or user scope |
| **Gemini CLI** | ❌ None | SERVER_INSTRUCTIONS only | No equivalent discovered |
| **ChatGPT Desktop** | ❌ None | Custom GPTs (cloud-based) | Not local file-based |
| **Grok** | ❌ None | Cloud-only | No local config |
| **Perplexity** | ❌ None | Cloud-only | No local config |

### Key Insight: MCP Is the LLM-Agnostic Layer

Claude Code's `.claude/agents/` is platform-specific. For true LLM-agnostic support:

1. **SERVER_INSTRUCTIONS** — Injected at MCP connection, all platforms receive this
2. **MCP Resources** — Expose `agent://orchestrator` as downloadable template
3. **MCP Tools** — `install_agent()` for Claude Code users; graceful message for others

### Architectural Decision

**Hybrid Approach with User Confirmation:**

```
User: "Set up the orchestrator agent"
              ↓
AI calls: install_agent("orchestrator")
              ↓
┌─────────────────────────────────────────────────────────┐
│  Tool returns preview (does NOT install yet):           │
│                                                         │
│  "I will create: .claude/agents/orchestrator.md        │
│   This enables governance-first workflow enforcement.   │
│                                                         │
│   Options:                                              │
│   1. Install automatically                              │
│   2. Show manual instructions                           │
│   3. Cancel"                                            │
└─────────────────────────────────────────────────────────┘
              ↓
User chooses option
              ↓
┌──────────────┬───────────────────────┬──────────────────┐
│  Option 1    │  Option 2             │  Option 3        │
│  confirmed   │  manual               │  cancel          │
├──────────────┼───────────────────────┼──────────────────┤
│  Write file  │  Return content +     │  Done            │
│  Return ✓    │  path + instructions  │                  │
└──────────────┴───────────────────────┴──────────────────┘
```

**For Non-Claude Platforms:**

```
User: "Set up the orchestrator agent"
              ↓
AI calls: install_agent("orchestrator")
              ↓
Tool returns:
  "For Gemini/ChatGPT/Grok: The Orchestrator protocol is already
   active via SERVER_INSTRUCTIONS. No file installation needed.

   The server automatically provides governance guidance on every
   interaction through the Required Actions and Forbidden Actions
   in its instructions."
```

### Why This Matters

1. **Security**: User confirms before file write (MCP servers writing files is unusual)
2. **Transparency**: User sees exactly what will be created
3. **Fallback**: Manual option works even if permissions fail
4. **Platform-aware**: Doesn't confuse users on platforms without agent files

### Implementation Notes

- `install_agent(agent_name, confirmed?, manual?)` parameters
- First call: `confirmed` and `manual` both None → return preview
- Second call: `confirmed=true` → write file; `manual=true` → show instructions
- Detect platform? Or just check if `.claude/` path pattern is usable?

### Lesson

Cross-platform support requires understanding platform capabilities. Don't assume Claude Code patterns work everywhere — MCP protocol is universal, but client implementations vary significantly.

### Open Questions (For User)

1. **Agent scope**: Just `orchestrator` and `governance-agent`, or more?
2. **Uninstall**: Include `uninstall_agent()` capability?
3. **Platform detection**: Auto-detect and skip file install for non-Claude platforms?

---

### 2026-01-02 - Script vs AI Judgment Layers for Governance Assessment (CRITICAL)

**Context:** Testing `evaluate_governance()` tool to verify all three assessment paths work (PROCEED, PROCEED_WITH_MODIFICATIONS, ESCALATE).

**What Happened:** Testing revealed the current implementation has a binary pattern:
- S-Series keywords detected → ESCALATE
- No S-Series triggers → PROCEED
- PROCEED_WITH_MODIFICATIONS never triggers

The tool found relevant principles (e.g., `coding-quality-testing-integration` for "deploy without tests") but couldn't generate specific required modifications.

**Root Cause Analysis:** The implementation places judgment in the script layer:

```
┌─────────────────────────────────────────────────────────────┐
│                    evaluate_governance()                     │
│                      (Python script)                         │
├─────────────────────────────────────────────────────────────┤
│  1. Semantic search → find relevant principles               │
│  2. Keyword check → S-Series triggers (delete, production)   │
│  3. Decision logic → PROCEED or ESCALATE                     │  ← Script decides
│  4. Return structured JSON                                   │
└─────────────────────────────────────────────────────────────┘
```

The script can find principles but lacks the reasoning capability to:
- Detect conflicts between action and principles
- Generate specific modifications
- Handle nuanced compliance evaluation

**Key Insight — Separation of Concerns:**

| Layer | Responsibility | Capability Needed |
|-------|---------------|-------------------|
| Script | Safety guardrails | Deterministic keyword matching |
| Script | Data retrieval | Semantic search + ranking |
| AI | Nuanced judgment | Reasoning about principle conflicts |
| AI | Modification generation | Context-aware recommendations |

**Solution — Hybrid Approach:**

```
┌─────────────────────────────────────────────────────────────┐
│                    evaluate_governance()                     │
│                   (Data provider + safety net)               │
├─────────────────────────────────────────────────────────────┤
│  1. Semantic search → find relevant principles               │
│  2. S-Series keyword check → HARD safety guardrail           │
│  3. Return: principles + context (let AI determine verdict)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI (Orchestrator/Client)                  │
│                   (Judgment layer)                           │
├─────────────────────────────────────────────────────────────┤
│  • Reads full principle content                              │
│  • Reasons about compliance                                  │
│  • Determines: PROCEED / MODIFY / ESCALATE                   │
│  • Generates specific required modifications                 │
└─────────────────────────────────────────────────────────────┘
```

**S-Series Remains Script-Enforced:**

The S-Series safety net MUST remain in the script layer because:
1. Deterministic — no reasoning variance between models
2. Non-negotiable — veto authority shouldn't depend on AI judgment quality
3. Fail-safe — works even if AI reasoning fails

**Model Capability Considerations:**

Different AI models have different reasoning capabilities:

| Model Tier | Script Reliance | AI Judgment Quality |
|------------|-----------------|---------------------|
| Opus/GPT-4/Gemini Pro | Safety only | Excellent nuanced reasoning |
| Sonnet/GPT-4o | Safety + some heuristics | Good, occasional misses |
| Haiku/GPT-4o-mini | More scripted rules | May need explicit checklists |

The hybrid approach should be model-aware: more capable models get more judgment latitude; less capable models get more scripted guidance.

**Lesson:** For governance enforcement systems:
1. **Safety = Script** — Deterministic, non-negotiable, always enforced
2. **Nuance = AI** — Context-aware, model-dependent, requires reasoning
3. **Data = Script** — Retrieval, ranking, structured output
4. **Judgment = AI** — Compliance assessment, modification generation

Don't try to script nuanced judgment. Don't let AI override safety guardrails.

**Pattern Applied:** Added to roadmap as "AI-driven modification assessment (hybrid approach)"

**Method Update:** Added §4.6.1 "Assessment Responsibility Layers" to multi-agent-methods

---
