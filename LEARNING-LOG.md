# AI Governance MCP - Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> When lesson graduates: Add to methods doc, mark "Graduated to §X.Y"
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

### Bold Text Drives Method Retrieval Surfacing (2026-02-07)

New method sections get generic chunk titles from the extractor (e.g., "Purpose", "Trigger Conditions"). The extractor picks up **bold text** as `trigger_phrases` (max 4 words, >5 chars). Without bold key terms, method chunks won't surface for natural-language queries.

**Rule:** When adding new method sections, bold the 2-3 most distinctive terms in the content (e.g., `**documentation drift**`, `**coherence audit**`). Verify after index rebuild with `query_governance()`. Server restart required (Gotcha #15).

---

### Transitive Dependency Drift in Docker (2026-02-02)

Docker `pip install .` resolves fresh dependency trees that may differ from local environments. `huggingface-hub>=1.0` dropped `requests`, but `sentence-transformers` still imports it. Locally worked because older `huggingface-hub` was cached.

**Rule:** Pin or explicitly declare any library your code (or its dependencies) imports at runtime. See Gotcha #19.

---

### CI Must Install All Test-Relevant Extras (2026-02-07)

CI installed `.[dev]` but context engine tests need `pathspec` (in `.[context-engine]` extras). All 200 CE tests failed with `ModuleNotFoundError`.

**Rule:** When adding optional dependency groups, update CI to install them if tests cover that code. See Gotcha #23.

---

### Cognitive Function Labels Must Be Distinct Across Agents (2026-02-08)

Validator and code-reviewer both initially used "Analytical validation" as cognitive function label. Contrarian reviewer caught the collision — identical labels undermine the distinctness argument. Renamed validator to "Checklist verification."

**Rule:** When creating a new subagent, verify its cognitive function label is unique across all agent definitions. Same mental operation = extend existing agent; different operation = different label.

---

### Instruction vs Content Surface Distinction (2026-02-02)

Governance concepts have two surfaces: instruction surfaces (SERVER_INSTRUCTIONS, CLAUDE.md, agents) and content surfaces (documents/*.md). The skip-list change updated instructions but not source docs.

**Rule:** Changes to governance CONCEPTS must propagate to both surfaces. Grep source docs: `grep -rn "old term" documents/`. See Gotcha #17.

---

### Version Sync Discipline (2026-02-02)

`pyproject.toml` was at 1.6.1 while `__init__.py` was at 1.7.0. Version bumps must update both. See Gotcha #16.

---

### MCP Server Index Caching (2026-01-18)

After rebuilding the index, MCP queries returned stale results. Server caches engine at startup — restart required after `python -m ai_governance_mcp.extractor`. See Gotcha #15.

---

### Embedding Model Token Limits (2026-01-17)

Method retrieval quality was poor (MRR 0.34). `all-MiniLM-L6-v2` has 256 token max (not 512). Key content appeared after truncation.

**Rule:** When retrieval quality is poor, check token limits first. Upgraded to `BAAI/bge-small-en-v1.5` (512 tokens). MRR improved +112%.

---

### Docker Multi-Arch with ML Workloads (2026-01-18)

ARM64 Docker builds via QEMU make embedding generation ~500x slower. MKL-DNN can't detect ARM features under emulation.

**Rule:** Don't use QEMU for ML workloads. Accept AMD64-only or use native ARM runners. Apple Silicon runs AMD64 via Rosetta 2.

---

### External Evaluation Depth: Principles AND Methods (2026-01-18)

External evaluations initially checked principles shallowly and skipped methods. Methods define HOW (procedures), which is what external tutorials describe.

**Rule:** Always retrieve and read specific method content — don't just note method names. Compare external patterns against method procedures.

---

### Specification Documents Are Not Validated Requirements (2025-12-24) — CRITICAL

Implemented full server based on spec that said "~5% miss rate with keyword matching." PO review revealed this was unacceptable. Spec became a constraint instead of a starting point.

**Rule:** Run discovery questions with PO before implementing architectural decisions. Present options with tradeoffs. Wait for explicit approval.

---

### Custom Subagent Files Are Reference Docs, Not Invokable (2026-01-04)

Task tool has fixed `subagent_type` values. Custom `.claude/agents/*.md` files don't register as new types. Use `general-purpose` and inline the role instructions.

---

### Claude Desktop and CLI Have Separate MCP Configs (2026-01-04) — CRITICAL

User reported "0 domains" — server connected but returned empty data. CLI config (`~/.claude.json`) didn't have env vars; Desktop config did. They are independent systems.

**Rule:** When building MCP servers that depend on file paths, require explicit paths via env vars. Fail loudly when index files are missing.

---

### ML Model Mocking: Patch at Source (2025-12-27) — CRITICAL

Mocking at `ai_governance_mcp.retrieval.SentenceTransformer` fails — models are lazy-loaded. Patch at `sentence_transformers.SentenceTransformer`. Use `side_effect` returning `np.random.rand(len(texts), 384)` for correct batch shapes. See Gotchas #5, #6.

---

### MCP Stdio Transport Requires Immediate Exit (2025-12-29)

Async event coordination doesn't work for stdio transport (blocking I/O). Use `os._exit(0)` in signal handlers — standard pattern for MCP servers.

---

### Framework Bootstrap Needs Activation Layer (2025-12-29) — CRITICAL

A governance framework needs three things: rules (principles), procedures (methods), and activation (loader). Without CLAUDE.md as entry point, Claude Code had no way to discover the framework.

**Rule:** Always create an entry point document. Bootstrap: Tool Config → ai-instructions → Constitution → Domain → Methods.

---

### Per-Response Reminder Prevents Drift (2025-12-31)

SERVER_INSTRUCTIONS are only injected once. ~30 token self-check question appended to every tool response prevents AI clients from drifting over long conversations.

---

### Multi-Pass Reviews Catch Different Issue Classes (2026-01-04) — CRITICAL

Second-pass contrarian review caught issues first-pass missed (S-Series penalty risk, min ratings threshold). First pass reviews original design; second pass reviews the fixes.

**Rule:** After fixing HIGH/CRITICAL findings, run second-pass review on the fixes themselves.

---

### Security Hardening Is Layers (2026-01-04)

Rate limiting prevents DoS. Secrets redaction prevents data leaks. Error sanitization prevents info disclosure. Schema validation prevents injection. No single layer is sufficient.

---

### Research ≠ Governance (2026-01-13/15)

Evaluated RLM (MIT) and prompt repetition (Google). Both are interesting research but wrong layer — governance defines behavioral principles, not model-specific workarounds. Test: "If this research never existed, would the framework be incomplete?"

---

### Anchor Bias in Document Review (2025-12-29)

Working on documents creates familiarity blindness. Mitigate: search for gaps (what's missing), compare against external standards, check cross-references systematically.

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
