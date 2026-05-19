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

#### 48. Generic Cross-Project Skill Suite (Discussion — Skills Architecture) `D3 New Capability`

**What:** Create a suite of generic, project-agnostic skills for `~/.claude/skills/` that work across any codebase. Two tiers: (1) standalone skills that work without ai-governance MCP, (2) governance-enhanced skills that leverage ai-governance when connected but degrade gracefully without it.

**Why:** Current skills (completion-sequence, compliance-review, test-authoring) are project-locked — they reference ai-governance MCP tools, specific governance documents, and project-specific hooks. Only content-enhancer is portable today (copied to global, session-177). The structural cause: skills were built for ai-governance's own use, not designed for distribution. Generic versions would make ai-governance's patterns useful across all projects without requiring the full framework.

**Systemic design — skill/subagent orchestration model:** Skills are user-invoked workflows in main context (application programs); subagents are isolated coprocessors. Effective generic skills orchestrate *multiple subagents in sequence*, each with a focused concern. This mirrors proven CI pipeline architecture (lint → build → test → security → deploy) but applied at the AI interaction layer, where the "pipeline" runs inside the conversation.

**Candidate skill suite (research needed to validate and scope):**

| Skill | Purpose | Subagents Used | Standalone? |
|-------|---------|---------------|-------------|
| `/code-review` | Multi-pass code review pipeline — orchestrates specialized reviewers in sequence | Lint pass, structure/organization pass, quality pass, security pass | Yes |
| `/pre-commit` | Generic post-change completion sequence — tests, lint, secrets scan, diff review | None (direct checks) | Yes |
| `/test-suite` | Test authoring with coverage analysis — generates tests, validates coverage, checks edge cases | test-generator | Yes |
| `/security-scan` | Security-focused review — OWASP top 10, dependency audit, secrets detection, auth patterns | security-auditor | Yes |
| `/content-enhancer` | Transform raw content into structured reference documents | None (already global) | Yes (done) |
| `/architecture-review` | Evaluate structural decisions — coupling, cohesion, separation of concerns, SOLID | code-reviewer + validator | Yes |
| `/refactor-audit` | Pre-refactor impact analysis — dependency mapping, blast radius, migration path | code-reviewer | Yes |
| `/doc-gen` | Generate/update documentation from code — README, API docs, inline docs | documentation-writer | Yes |

**The `/code-review` pipeline (highest value, research-driven):** This is the skill the user specifically wants to research. The concept: a single `/code-review` invocation runs multiple specialized passes over a diff, each focused on a different concern. Candidate passes (need external research to validate industry best practices):

1. **Lint/style pass** — formatting, naming conventions, import organization, dead code. Fast, mechanical, high signal-to-noise.
2. **Structure/organization pass** — file placement, module boundaries, abstraction levels, separation of concerns. Maps to ai-coding Part 9 (code architecture patterns) and the recent structure/organization updates.
3. **Logic/quality pass** — correctness, edge cases, error handling, performance anti-patterns. The "does this code do what it claims?" check.
4. **Test coverage pass** — are changes tested? Are edge cases covered? Are tests testing behavior or implementation?
5. **Security pass** — injection vectors, auth/authz patterns, secrets exposure, dependency vulnerabilities. Maps to OWASP top 10.
6. **API/contract pass** — backward compatibility, breaking changes, type safety, serialization. Relevant for library/service code.
7. **Observability pass** — logging, metrics, error reporting. Is the code debuggable in production?

Each pass produces a focused report. The orchestrating skill aggregates findings by severity and presents a unified review. The key insight: specialized passes catch things that a single "review this code" prompt misses, because each pass has a focused instruction set and doesn't dilute attention across concerns.

**Governance-enhanced tier:** When ai-governance MCP is connected, skills can optionally call `evaluate_governance()` for principle-aware review and `search_references()` for pattern matching against the reference library. The skill detects MCP availability and enhances — but doesn't require — governance integration.

**Distribution path:** Generic skills ship as files in the ai-governance repo under a `skills/` or `global-skills/` directory. Users copy to `~/.claude/skills/` manually, or a future `install_skill` MCP tool (analogous to `install_agent`) provides them programmatically. README documents availability. Skills are optional — the MCP server works without them.

**Research needed:** External research on AI code review best practices — what passes are most effective? What does industry use? (CodeRabbit, Cursor, Cody, Codex review patterns.) Which passes catch the most real bugs vs. generating noise? What's the optimal pass ordering?

**Progress (session-178):** `/code-review` and `/security-scan` shipped as global skills. `/code-review` uses 3-pass parallel subagent dispatch (correctness, security, architecture) with severity-gated reconciliation and evidence requirements. 2 optional passes (performance, test-coverage) available via "full review". `/security-scan` scoped to secrets detection + dependency audit + basic auth patterns (mechanical, portable concerns). Both self-contained — no MCP dependency. Canonical source in `global-skills/` directory, installed to `~/.claude/skills/`. Research-backed: fan-out/fan-in (Osmani, O'Reilly 2026), severity gating (Jet Xu), evidence requirement (Ellipsis). `/content-enhancer` already global (session-177).

**Progress (session-182):** `/test-suite` shipped as global skill. 3-phase protocol (generate → verify → revise) shaped by contrarian review — Phase 2 (verify) is the skill's core value, structurally separated and non-skippable. Three mandatory self-checks: echo-chamber detection (specification-based assertions, not implementation-mirroring), error-path balance (weighted guidance with domain sensitivity), mutation mindset (single-character mutation coverage). Auto-detects pytest/vitest/jest/playwright/go/rust. Framework-specific idioms inline. No MCP dependency (optional governance enhancement gated on availability). Remaining skills (`/pre-commit`, `/architecture-review`, `/refactor-audit`, `/doc-gen`) stay in Discussion.

**Dependency:** Benefits from existing subagent definitions (code-reviewer, security-auditor, test-generator, documentation-writer) as templates for the specialized passes. Independent of #47 (Cognee).

**Origin:** Session-178 (2026-05-17). User identified that project-scoped skills don't carry to other projects; wants generic versions with multi-agent code review pipeline.

---


