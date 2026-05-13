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

#### 162. Accounting Domain `D3 New Capability`

**Filed:** 2026-05-12 (session-168).

**What:** Governance domain for accounting work — principles and methods covering double-entry integrity, reconciliation patterns, chart of accounts design, audit trail requirements, GAAP/cash-vs-accrual considerations, financial data security, and API integration patterns for financial systems. Evidence base: accounting standards (GAAP, IFRS), open-source accounting projects, QuickBooks/financial API ecosystems.

**Why domain (not project):** Generalizable principles that apply across multiple projects — QuickBooks connector, open-source ledger tools, invoicing systems, tax prep workflows, financial reporting. The QuickBooks integration is the first project that would consume this domain.

**Discussion needed:** Scope candidate principles and methods, evidence base review, failure mode identification. Full planning process per COMPLETION-CHECKLIST domain creation.

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

---

#### 6. Visual Communication Domain (Discussion → Full Planning) `D3 New Capability`

**What:** Governance for non-coding visual artifacts: presentations, reports, infographics, print design. Separate from UI/UX (different failure modes, evidence bases, tooling). Tufte, Duarte, Reynolds evidence base.

**Status:** Anticipatory — building this before active use so it's ready when needed.

**Discussion needed:** Full planning process per COMPLETION-CHECKLIST domain creation. Scope candidate principles and methods, evidence base review, failure mode identification.

**Scope note (2026-04-03):** Structured document production (Excel workbooks, data-heavy reports, financial spreadsheets) is handled by AI Coding Part 9.4 (Document Generation Patterns). Visual Communication stays scoped to visual design artifacts: presentations, infographics, print design — the Tufte/Duarte/Reynolds evidence base. The distinction: Part 9.4 covers *how to generate and serve document files reliably*; Visual Communication covers *how to design visually effective communication*.

#### 53. Modular Domain Architecture (Discussion) `D3 New Capability`

**What:** Make ai-governance modular so users can spin up with just meta-principles and methods, or with meta + selected domains. Domains should be addable/removable without affecting the core framework.

**Why:** Currently the framework ships as a monolith — all 7 domains are always loaded. A user building only Python web apps doesn't need Storytelling or Multimodal RAG domains. A user focused on content creation doesn't need AI Coding. Modular domains would let users start minimal (constitution + methods only) and add domains as their needs grow.

**Root cause:** The framework was built by accretion — each domain was added as a new file, but the architecture assumes all domains are always present. The extractor, retrieval, and domains.json all treat the domain set as fixed.

**Discussion needed:**
1. Can `domains.json` be made user-configurable (enable/disable per domain)?
2. How does the extractor handle missing domain files gracefully?
3. Should tiers.json principle activation be domain-aware (only activate principles from enabled domains)?
4. What's the minimum viable framework? Constitution + meta-methods + ai-coding? Just constitution + meta-methods?
5. How do cross-domain references work when a referenced domain isn't loaded?
6. Impact on retrieval quality — fewer domains = less noise in results?

**Origin:** User request (2026-04-04). Anticipatory architecture improvement for adoption scalability.

---

#### 11. Autonomous Operations Domain (Discussion) `D3 New Capability`

**What:** Autonomous agent patterns (AO-Series, currently 4 principles in Multi-Agent) may eventually outgrow the multi-agent domain. This would create a dedicated domain for autonomous operation governance — financial compliance, regulatory frameworks, agent marketplace governance, cross-org federation.

**Discussion needed:** Is this anticipatory need real? What would trigger the split? The Domain Creation Criteria (§5.1.0) already defines when to create domains, but the user wants to understand if the AO-Series trajectory warrants keeping this on the radar.

#### 41. Reference Library Auto-Staging Proposals (Discussion — Self-Improvement) `D2 Improvement`

**What:** After sessions involving complex problem-solving (5+ tool calls, novel governance patterns, or trial-and-error workflows), the system proposes reference library entries to the `staging/` directory with `maturity: seedling`. Human reviews staging during completion sequence.

**Why:** The reference library staging infrastructure exists (`staging/` directory, `_criteria.yaml` per domain, completion sequence prompt) but is dormant — `.gitkeep` placeholder, never activated. Hermes Agent's procedural memory (autonomous skill creation) demonstrates the value of automated capture, but their approach lacks quality gates. Our staging path provides the human gate that prevents noise while closing the capture gap.

**What's involved:** (1) Define trigger criteria — what constitutes "worth capturing" (session complexity, novel pattern, user correction that changed approach), (2) Activate `_criteria.yaml` with per-domain capture rules, (3) Build the staging proposal mechanism (likely a new MCP tool or extension to completion sequence), (4) Define the staging review workflow.

**Dependency:** None — staging infrastructure already exists.

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

#### 160. Structural root_cause Artifact in log_governance_reasoning (Discussion) `D2 Improvement`

**What:** Add a `root_cause` field to `log_governance_reasoning` tool that requires naming the structural cause distinct from the triggering symptom. If empty or matches planned_action text (restated symptom), flag it. Creates a verifiable artifact per LEARNING-LOG "Codified Rules Need Structural Anti-Theater Gates."

**Why deferred:** The critical-5 scaffold format is a prompt-level hint; this field is the structural enforcement complement. Ship scaffold first, assess scaffold theater prevalence at Compliance Review #8.

**Trigger:** Scaffold theater detected — >50% of critical-5 scaffold responses are pro-forma restated symptoms rather than genuine root-cause analysis. Check at Compliance Review #8 (~2026-06-09).

**Origin:** Critical 5 reasoning scaffold plan (2026-05-10). Contrarian C1 (scaffold theater risk).

#### 161. Claude App Enforcement Effectiveness (Discussion) `D2 Improvement`

**What:** Investigate and improve governance enforcement effectiveness for Claude App users. Current state: no hooks, no CLAUDE.md, only SERVER_INSTRUCTIONS + tool responses + enforcement proxy (if configured). See EXECUTION-FRAMEWORK.md §8.4 for the full layer matrix and gap analysis.

**Possible directions:** (1) Enforcement proxy adoption guide for Claude App users, (2) Enhanced SERVER_INSTRUCTIONS with critical-5 re-injection patterns, (3) Tool-response-level enforcement — refuse to return results from other tools until governance called (requires enforcement proxy), (4) Investigate whether Claude App supports any hook-like mechanism.

**Trigger:** User actively uses ai-governance from Claude App and reports enforcement gaps.

**Origin:** Critical 5 reasoning scaffold plan (2026-05-10). Cross-platform enforcement gap analysis.

