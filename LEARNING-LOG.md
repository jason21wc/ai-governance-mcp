# AI Governance MCP - Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> When lesson graduates: Add to methods doc, mark "Graduated to §X.Y"
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

### Editable Install Doesn't Fix Running MCP Server Processes (2026-02-12)

After implementing tree-sitter parsing, re-indexing via the live MCP server produced chunks with `heading: null`. The package is installed in editable mode (`pip install -e .`), so the server reads source files directly — but the already-running process had the OLD `connectors/code.py` cached in Python's module cache. Re-indexing used the stale line-based parser, not the new tree-sitter code. Pytest worked because it spawns a fresh process.

**Rule:** After modifying source code used by a running MCP server, restart Claude Code (or the server process) before testing via MCP tools. Editable installs don't help — Python caches imported modules for the lifetime of the process. See Gotcha #27.

---

### Go type_declaration Names Are on type_spec Child (2026-02-12)

Tree-sitter Go grammar: `type_declaration` wraps a `type_spec` node which holds the `name` field. `child_by_field_name("name")` on the parent returns None — must iterate children to find `type_spec` first.

**Rule:** When adding tree-sitter support for a new language, verify the actual AST node structure with a live parser before assuming field names exist on the expected node.

---

### BM25Okapi Can Return Negative Scores (2026-02-12)

BM25Okapi returns negative IDF scores for common terms in small corpora. When `max_score <= 0`, normalization doesn't fire, leaving raw negatives that violate Pydantic `ge=0.0` constraints.

**Rule:** Always clamp BM25 scores with `np.clip(scores, 0.0, 1.0)` after normalization. Don't assume score range is [0, 1].

---

### Environment-Aware Tests for Optional Dependencies (2026-02-12)

Tests for `_get_chunking_version()` failed because tree-sitter IS installed in dev but not CI. Hardcoded `"line-based-v1"` broke when the actual connector detected tree-sitter.

**Rule:** Tests that depend on optional package availability should either: (1) explicitly force the flag (`c._tree_sitter_available = False`), or (2) dynamically detect the actual value. Never hardcode expected values for environment-dependent behavior.

---

### Standalone MCP Config Files Aren't Picked Up by Claude Code (2026-02-11)

Config at `~/.claude/mcp-servers/context-engine.json` was never loaded — Claude Code reads MCP servers from `~/.claude.json` under `mcpServers`. The standalone file format is not a Claude Code convention. See also Gotcha #8 (project vs user scope) and the CRITICAL lesson "Claude Desktop and CLI Have Separate MCP Configs."

**Rule:** Always register MCP servers in `~/.claude.json` `mcpServers` for Claude Code. Verify tools appear after restart before assuming connection works.

---

### Test Inputs Must Traverse the Full Validation Chain (2026-02-11)

Two test bugs: (1) `"nonexistent00"` has non-hex chars — hit project_id hex validation before reaching the "not found" path we intended to test. (2) `cooldown_seconds=0.0` caused infinite retry cascade — each failed callback re-queued and the 0s timer fired immediately, chaining endlessly and spamming logs.

**Rule:** When writing tests for code with layered validation, trace the full call path to ensure your test input reaches the code path you intend to test. For timer-based retry tests, use a high cooldown (e.g., 60s) so the retry timer never fires during the test, and call `_running.clear()` in cleanup.

---

### Guard-Then-Load Pattern: Don't Undo Your Own Safety Checks (2026-02-10)

`_load_project` correctly discarded incompatible embeddings on model mismatch. Then immediately called `_load_search_indexes` which reloaded them unconditionally — undoing the safety check. Similarly, `get_principle_by_id` used a prefix→domain map where "multi" (multi-agent) and "mult" (multimodal-rag) collided because Python dict lookup stops at the first prefix match.

**Rule:** When a function sets a safety state (discarding data, marking flags), audit all subsequent calls to verify they don't silently reverse that state. When mapping IDs to domains, prefer exhaustive search over prefix heuristics — domain count is small, correctness matters more than lookup speed.

---

### Context Engine Hardening: Defense-in-Depth for Indexing Systems (2026-02-09)

File watcher, storage, and parsing systems need layered defenses even for local-use tools: (1) BM25Okapi crashes on empty corpus — guard with `any(len(doc) > 0 for doc in corpus)` before construction, (2) Timer threads must be daemon to prevent blocking process exit, tracked for cancellation in `stop()`, and guarded with `_running.is_set()` checks, (3) All persistent file loads need corrupt-file recovery (try/except → log → delete → return None), (4) CSV/XLSX parsers need column limits (`row[:500]`), plain text parsers need force-split at max lines.

**Rule:** When building indexing/search systems: extract duplicate guard logic into helpers, make all timers daemon with lifecycle tracking, implement circuit breakers for repeated failures (3 strikes), add atomic writes (tmp+rename) for all persisted data, and column/row/size limits for all file parsers.

---

### Bold Text Drives Method Retrieval Surfacing (2026-02-07)

New method sections get generic chunk titles from the extractor (e.g., "Purpose", "Trigger Conditions"). The extractor picks up **bold text** as `trigger_phrases` (max 4 words, >5 chars). Without bold key terms, method chunks won't surface for natural-language queries.

Three additional extraction traps discovered during Part 4.3 tuning:
1. **Skip-list titles** — `"purpose"` is in `skip_method_titles` (extractor.py:1008). Sections titled "Purpose" get absorbed into the preceding chunk. Fix: use a descriptive title instead.
2. **Short bold terms** — Bold text ≤5 chars (e.g., `**Quick**`, `**Full**`, `**Note:**`) fails the `len(b) > 5` filter. Fix: bold multi-word phrases instead (e.g., `**Quick tier**`).
3. **`Applies To:` field** — The extractor parses `**Applies To:**` lines (extractor.py:1123-1136) into both BM25 and embedding text. Adding this field helps methods surface for `evaluate_governance()` queries.

**Rule:** When adding new method sections: (a) avoid skip-list titles ("purpose", "overview", etc.), (b) bold 2-3 distinctive phrases >5 chars, (c) add `**Applies To:**` with natural-language use cases. Verify after index rebuild + server restart (Gotcha #15).

---

### Transitive Dependency Drift in Docker (2026-02-02)

Docker `pip install .` resolves fresh dependency trees that may differ from local environments. `huggingface-hub>=1.0` dropped `requests`, but `sentence-transformers` still imports it. Locally worked because older `huggingface-hub` was cached.

**Rule:** Pin or explicitly declare any library your code (or its dependencies) imports at runtime. See Gotcha #19.

---

### CI Must Install All Test-Relevant Extras (2026-02-07)

CI installed `.[dev]` but context engine tests need `pathspec` (in `.[context-engine]` extras). All 200 CE tests failed with `ModuleNotFoundError`.

**Rule:** When adding optional dependency groups, update CI to install them if tests cover that code. See Gotcha #23.

---

### Version History Entries Can Be Silently Dropped (2026-02-08)

Coherence audit found v3.7.0 missing from version history table and v3.7.0.1 orphaned at end of file. During edits, version history entries can be accidentally deleted or displaced without anyone noticing — the table is long and entries look similar.

**Rule:** Add a version-history-completeness check to pre-release audits: verify descending order, no gaps, and no orphaned entries outside the table. Grep for `### v` outside the table section.

---

### Cognitive Function Labels Must Be Distinct Across Agents (2026-02-08)

Validator and code-reviewer both initially used "Analytical validation" as cognitive function label. Contrarian reviewer caught the collision — identical labels undermine the distinctness argument. Renamed validator to "Checklist verification."

**Rule:** When creating a new subagent, verify its cognitive function label is unique across all agent definitions. Same mental operation = extend existing agent; different operation = different label.

---

---

---

### Specification Documents Are Not Validated Requirements (2025-12-24) — CRITICAL

Implemented full server based on spec that said "~5% miss rate with keyword matching." PO review revealed this was unacceptable. Spec became a constraint instead of a starting point.

**Rule:** Run discovery questions with PO before implementing architectural decisions. Present options with tradeoffs. Wait for explicit approval.

---

### Claude Desktop and CLI Have Separate MCP Configs (2026-01-04) — CRITICAL

User reported "0 domains" — server connected but returned empty data. CLI config (`~/.claude.json`) didn't have env vars; Desktop config did. They are independent systems.

**Rule:** When building MCP servers that depend on file paths, require explicit paths via env vars. Fail loudly when index files are missing.

---

### ML Model Mocking: Patch at Source (2025-12-27) — CRITICAL

Mocking at `ai_governance_mcp.retrieval.SentenceTransformer` fails — models are lazy-loaded. Patch at `sentence_transformers.SentenceTransformer`. Use `side_effect` returning `np.random.rand(len(texts), 384)` for correct batch shapes. See Gotchas #5, #6.

---

### Multi-Pass Reviews Catch Different Issue Classes (2026-01-04) — CRITICAL

Second-pass contrarian review caught issues first-pass missed (S-Series penalty risk, min ratings threshold). First pass reviews original design; second pass reviews the fixes.

**Rule:** After fixing HIGH/CRITICAL findings, run second-pass review on the fixes themselves.

---

---

## Graduated Patterns

| Pattern | Graduated To | Date |
|---------|-------------|------|
| Process Map visualization | PO preference in PROJECT-MEMORY | 2025-12-26 |
| Communication Level calibration | PROJECT-MEMORY Patterns | 2025-12-26 |
| Portfolio-Ready README | PROJECT-MEMORY Patterns | 2025-12-26 |
| Spec completeness verification | Gotcha #17, CLAUDE.md workflow | 2025-12-22 |
| conftest.py fixtures | ARCHITECTURE.md Mocking Strategy | 2025-12-27 |
| CPU-only PyTorch in CI | ci.yml, Gotcha #9 | 2025-12-27 |
| Domain routing threshold tuning | retrieval.py implementation | 2025-12-28 |
| Constitution/Methods separation | ARCHITECTURE.md, document structure | 2025-12-28 |
| Index architecture verification | Gotcha #13, ARCHITECTURE.md | 2026-01-17 |
| Feedback score boost/penalty | retrieval.py, PROJECT-MEMORY decisions | 2026-01-04 |
| Governance enforcement research | PROJECT-MEMORY decisions | 2026-01-03 |
| Version sync discipline | Gotcha #16, PROJECT-MEMORY | 2026-02-10 |
| MCP server index caching | Gotcha #15 | 2026-02-10 |
| Security hardening is layers | ARCHITECTURE.md Security Features | 2026-02-10 |
| Research ≠ governance test | PROJECT-MEMORY decisions | 2026-02-10 |
| Anchor bias in document review | meta-methods Part 7.10 | 2026-02-10 |
| Instruction vs content surfaces | Gotcha #17 | 2026-02-12 |
| Embedding model token limits | ADR-2 in PROJECT-MEMORY | 2026-02-12 |
| Docker multi-arch ML | ADR-9 in PROJECT-MEMORY | 2026-02-12 |
| External eval depth | General knowledge (active since Jan) | 2026-02-12 |
| Custom subagent files not invokable | CLAUDE.md subagents note | 2026-02-12 |
| MCP stdio immediate exit | server.py implementation | 2026-02-12 |
| Per-response reminder prevents drift | server.py implementation | 2026-02-12 |
| Framework bootstrap activation layer | CLAUDE.md + ai-instructions | 2026-02-12 |
