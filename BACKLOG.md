# Backlog

**Memory Type:** Prospective (intentions)
**Lifecycle:** Items are added when discovered, removed when implemented, migrated, or abandoned. Git commit history is the archive (`git log --grep="backlog #N"`).

> **Staleness rule (2026-04-14):** Discussion items with no activity for 90+ days are flagged for review during the next compliance review (`/compliance-review` Check 8). User decides: keep, close, or reframe.

---

### Open Backlog

> **Backlog Philosophy (2026-03-30, updated 2026-05-03):** This file holds **discrete projects** — work with a start and an end. Items fall into two categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it."
>
> **Taxonomy (2026-05-03).** The project maintains two files for forward-looking work, distinguished by lifecycle:
> - **BACKLOG.md (this file)** — **Projects.** Discrete tasks with start and end. Close on completion or abandonment. Git history is the archive.
> - **OPERATIONS.md** — **Operational items.** Indefinite-lifecycle recurring commitments: cadences (periodic reviews), tripwires (conditional re-evaluations), verification experiments (time-bound hypothesis tests), effectiveness metrics (system health indicators), scheduled operations (automated tasks). These are never "done" — their recurrence is the point.
>
> When a tripwire fires and creates discrete work, that work comes here as a project. When a project reveals a need for ongoing monitoring, the monitoring item goes to OPERATIONS.md. Previously migrated items can be found via `git log --grep="backlog #N"`.
>
> **Anticipatory items are valid.** Not all backlog items need a triggered condition. Three valid reasons to keep an item: need it now (active problem), plan to use soon (near-future need), anticipate needing later (want it ready when the time comes). When reviewing the backlog, present items with summaries so the user can decide — don't assume items without fired triggers should be closed.
>
> **Closing items (procedure).** To close a backlog item: (1) delete the entire entry from this file — not strikethrough, not "Closed" stub, full deletion, (2) document the closure in the commit message (what shipped, why closed). Git history is the archive; `git log --grep="backlog #N"` retrieves closure context. Do not leave redirect stubs ("Moved to X") — they accumulate as noise and contradict single-source-of-truth (per `coding-method-archive-vs-delete-decision-matrix` §6.5.5). CI enforces: strikethrough (`~~`) in this file fails the build.
>
> **Difficulty classification (D1-D3).** Every backlog item gets a difficulty tag. Per `meta-quality-verification-validation` and `meta-method-effort-not-time-estimation` (rules-of-procedure §7.12), criteria must be observable, not time-based or subjective.
>
> | Level | Label | Definition | Observable Indicators |
> |-------|-------|-----------|----------------------|
> | **D1** | Low complexity | No plan mode required | Docs-only OR known pattern; no new infrastructure; no dependencies |
> | **D2** | Moderate complexity | Plan mode required | New tool/hook/section; moderate research; depends on 1-2 other items |
> | **D3** | High complexity | Plan mode + external review + broad changes | New domain; cross-cutting refactor; new service; heavy research |
>
> **Rules:** Default to D1 unless indicators push higher. Plan mode required → at least D2. New domain or cross-cutting refactor → D3. When uncertain, pick higher. Re-evaluate when starting work — tags reflect observable effort indicators, not time. **Do not size backlog items by hours, minutes, or "session count"** — those are time-units the AI miscalibrates by 50-100×.
>
> **Type tags:** Fix, Improvement, New Capability, Docs, Maintenance. Ranked order: fixes first → improvements → new capabilities.

---

### Active (Implement Now/Soon)

*(No active items.)*

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

---

#### 6. Visual Communication Domain (Discussion → Full Planning) `D3 New Capability`

**What:** Governance for non-coding visual artifacts: presentations, reports, infographics, print design. Separate from UI/UX (different failure modes, evidence bases, tooling). Tufte, Duarte, Reynolds evidence base.

**Status:** Anticipatory — building this before active use so it's ready when needed.

**Discussion needed:** Full planning process per COMPLETION-CHECKLIST domain creation. Scope candidate principles and methods, evidence base review, failure mode identification.

**Scope note (2026-04-03):** Structured document production (Excel workbooks, data-heavy reports, financial spreadsheets) is handled by AI Coding Part 9.4 (Document Generation Patterns). Visual Communication stays scoped to visual design artifacts: presentations, infographics, print design — the Tufte/Duarte/Reynolds evidence base. The distinction: Part 9.4 covers *how to generate and serve document files reliably*; Visual Communication covers *how to design visually effective communication*.

**Evidence note (2026-05-13):** Thariq Shihipar's "The Unreasonable Effectiveness of HTML" (https://thariqs.github.io/html-effectiveness/) — 20 AI-generated self-contained HTML artifacts (reports, diagrams, decks, editors) demonstrating that HTML output artifacts improve human engagement vs. markdown. Relevant as a modern instance of visual communication principles applied to AI output. Key distinction for this domain: HTML is effective as an *output rendering format* for human consumption, while Markdown remains better as *source format* for LLM input (per arXiv 2411.10541, web2md.org benchmarks showing +23-40% accuracy for Markdown input). This input/output format distinction is itself a candidate principle.

#### 11. Autonomous Operations Domain (Discussion) `D3 New Capability`

**What:** Autonomous agent patterns (AO-Series, currently 4 principles in Multi-Agent) may eventually outgrow the multi-agent domain. This would create a dedicated domain for autonomous operation governance — financial compliance, regulatory frameworks, agent marketplace governance, cross-org federation.

**Discussion needed:** Is this anticipatory need real? What would trigger the split? The Domain Creation Criteria (§5.1.0) already defines when to create domains, but the user wants to understand if the AO-Series trajectory warrants keeping this on the radar.

#### 41. Reference Library Auto-Staging Proposals (Discussion — Self-Improvement) `D2 Improvement`

**What:** Phased activation of reference library capture. Phase 1 (shipped session-174): behavioral trigger via completion-sequence prompt — AI evaluates sessions for capturable patterns and proposes entries via existing `capture_reference` tool. Phase 2 (conditional): staging infrastructure (`staging/` subdirectory write path, `pending-review` status, batch review workflow) — activates only if Phase 1 produces volume that makes inline review burdensome.

**Why:** Contrarian review (session-174) found the original plan built infrastructure to solve a behavioral problem. `capture_reference` works (9+ successful calls) but is never AI-initiated. The bottleneck is behavioral (AI doesn't evaluate sessions for capturable patterns), not infrastructural (no staging path). Phase 1 tests the behavioral hypothesis with a 1-file change before building plumbing.

**Phase 1 status (shipped session-174):** Completion-sequence checklist updated with "Reference Library capture check" in both Code changes and Content changes BEST-EFFORT sections. Surfaces `_criteria.yaml` trigger criteria inline. Human gate: AI proposes, user approves/rejects.

**Phase 2 trigger:** Phase 1 produces 3+ proposals per session consistently, making inline review burdensome. At that point, implement: `staging` param on `capture_reference`, handler write-to-staging path, `pending-review` status on ReferenceEntry model, staging dirs for all domains, staging-specific tests.

**Dependency:** None — Phase 1 uses existing tools. Phase 2 depends on Phase 1 validation.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes auto-creates skills every 15 tool-calling iterations via background review agent. Our adaptation: auto-propose to staging with human gate, leveraging our richer metadata model (maturity, decay classes, KeyCite currency).

---

#### 45. Content Security Scanning for Staging Entries (Discussion — Security) `D2 New Capability`

**What:** Add content security scanning for reference library entries proposed to `staging/`, similar to Hermes's skills_guard (100+ threat patterns across categories: prompt injection, exfiltration, destructive commands, role hijacking, credential exposure, obfuscation).

**Why:** If #41 (auto-staging) is implemented, AI-generated content enters the reference library pipeline without full human review at the capture stage. Content scanning provides defense in depth — catch prompt injection, embedded credentials, or destructive patterns before they land in staging. Currently `capture_reference` has path traversal protection and yaml.safe_load but no content-level threat scanning.

**What's involved:** (1) Define threat pattern categories relevant to reference library content (prompt injection in artifacts, embedded secrets, destructive command patterns in code samples), (2) Implement scanning — could be regex-based like Hermes or leverage existing security-auditor subagent, (3) Integrate with capture_reference tool and staging workflow. Scope is narrower than Hermes's full skills_guard since our entries are markdown + code snippets, not executable scripts.

**Dependency:** Becomes important when #41 (auto-staging) is implemented. Lower priority without it since manual capture already has human oversight.

**Origin:** Hermes Agent evaluation (2026-04-01). Their skills_guard scans every skill write with 100+ patterns, rolls back on block. Our adaptation would be proportional to the actual threat surface.

---

#### 46. Stack/Platform Conditional Metadata for References (Discussion — Retrieval Quality) `D2 Improvement`

**What:** Add optional frontmatter fields to reference library entries indicating technology stack or platform requirements (e.g., `requires_stack: [nextjs, supabase]`, `applies_to: [typescript, javascript]`). Use these in retrieval to filter or de-rank entries irrelevant to the current project context.

**Why:** A Next.js auth pattern is useless in a Python project. We already have domain routing; this adds stack-level filtering within a domain. As the reference library grows across multiple projects and tech stacks, retrieval precision depends on context-appropriate results. Hermes skills declare `requires_toolsets` and `platforms` for conditional activation — same concept applied to our retrieval model.

**What's involved:** (1) Define frontmatter fields (stack, language, platform, framework), (2) Add to ReferenceEntry model and capture_reference validation, (3) Implement retrieval scoring adjustments (similar to existing maturity/status adjustments), (4) Determine how to detect current project context (from Context Engine index? from project files?). The metadata boosting infrastructure already exists in retrieval.py and project_manager.py.

**Dependency:** None — can implement independently. Benefits from Context Engine project awareness for automatic context detection.

**Origin:** Hermes Agent evaluation (2026-04-01). Their conditional activation metadata adapted to our retrieval-based model.

---

#### 47. Cognee KG Pipeline Integration Spike (Discussion — Knowledge Graph) `D2 New Capability`

**What:** Evaluate Cognee (github topoteretes/cognee, Apache-2.0) as a concrete implementation of A5 Knowledge Graph Integration and §3.8 graph-based retrieval. Spike scope: install locally, run against a small test corpus, assess entity/relationship extraction quality, community detection output, search type effectiveness, and MCP server integration with Claude Code.

**Why:** A5 and §3.8 now describe community detection, multi-stage retrieval, and graph quality metrics, but no concrete tooling is integrated. Cognee implements the graph+vector+relational pipeline as an open-source library (15 search types, 38+ document formats, LLM-agnostic with 11 providers). The statistics education domain is the likely first use case — hundreds of raw documents requiring multi-hop retrieval across prerequisite chains. Research confirmed Cognee as the best-fit tool across 10+ candidates evaluated.

**What's involved:** (1) `pip install cognee` + configure with Anthropic or Ollama for LLM + Fastembed for embeddings, (2) Install cognee-mcp via Docker, (3) Test with sample statistics documents, (4) Evaluate graph quality against §3.8 metrics, (5) Assess whether community detection adds value at the initial corpus scale. Reference library entry `ref-multimodal-rag-kg-landscape-2024-2026` contains the full evaluation, tool comparison, and implementation path.

**Progress (session-177):** Cognee 1.0.9 installed as optional dependency (`pip install -e ".[cognee-spike]"`). Import verified. LLM provider options explored: Anthropic API (pennies per document, one-time ingest cost) or Ollama with local model (zero cost). Fastembed bundled. No test corpus run yet.

**Trigger:** When user is ready to invest in the statistics domain buildout or has API key / Ollama configured.

**Dependency:** None — spike is self-contained. Benefits from #41 (reference library auto-staging) for capturing spike findings.

**Origin:** Session-177 (2026-05-15). Two research agents evaluated knowledge graph RAG landscape; Cognee selected over Microsoft GraphRAG, LlamaIndex, R2R, Mem0, Zep, Letta, MemPalace, MindsDB, MemoryLake.

---


