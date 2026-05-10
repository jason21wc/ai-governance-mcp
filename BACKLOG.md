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
> **No closed/completed/moved items in this file.** When an item is closed, migrated to another file, or completed, remove it from this file entirely. Do not leave redirect stubs ("Moved to X") — they accumulate as noise and contradict single-source-of-truth (per `coding-method-archive-vs-delete-decision-matrix` §6.5.5). Git commit history is the archive — commit messages document what was closed, moved, and why. If you need closure context for a past item, use `git log --grep="backlog #N"` or search commit messages.
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

*No active items. All former items migrated to OPERATIONS.md — see git history.*

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

---

#### 149. Contrarian-reviewer over-generation tendency — quota or precedence mechanism `D2 Discussion`

**Filed:** 2026-05-01 (session-142, contrarian-reviewer post-edit double-check on BACKLOG #147 fold-in).

**What.** Contrarian-reviewer subagent invocation `afac4381fd32e8721` raised a meta-observation while pressure-testing the BACKLOG #147 fix: session-140's Execution Framework brainstorm produced **five challenge tracks in a single contrarian arc** (F-P2-08 invocation, Rule of Three, retroactive grouping, phantom failure mode, proactive-vs-reactive bias). Only one (proactive-vs-reactive) produced an actionable BACKLOG entry. The other four were either category errors, anchor-bias-driven, or mild observations.

**Hypothesis.** The contrarian-reviewer agent may have an over-generation tendency: rather than identifying the highest-leverage concern (its stated cognitive function — "Depth over breadth — one deeply investigated concern beats five shallow ones"), it generates a list of five concerns and lets the consuming context pick. This contradicts the agent's own "Bad Example — Formulaic Contrarianism" rules (*"Table-filling: 5 mild concerns instead of investigating the 1 that matters"*) but the agent itself doesn't enforce a quota or precedence mechanism on the way out.

**Why D2 Discussion (not D1 Fix).** N=1 evidence base. Session-140 was an unusually broad architectural brainstorm where multiple challenge tracks were arguably appropriate. Acting on n=1 by adding a quota/precedence mechanism to the agent definition would itself be over-investment per the proactive-stakes-match test (BACKLOG #147 / `rules-of-procedure §7.8.1`) — anticipated stakes are unclear from one observation. Ironic to file a fix-now item against the contrarian here for a behavior that may not generalize.

**Possible interventions (for discussion, not yet adopted).**

1. **Top-1 enforcement** — modify `documents/agents/contrarian-reviewer.md` Output Format to require a *single* "Highest-Leverage Concern" field above the multi-finding tables, with an explicit instruction that the multi-finding section is OPTIONAL and SHOULD be empty unless 2+ concerns genuinely meet the depth-over-breadth threshold.
2. **Precedence ranking** — require findings to be ordered by leverage with explicit numeric weight, so consuming agents/users can see the contrarian's own ranking rather than treating each finding as independently actionable.
3. **Self-audit quota** — add a Step 8 "Quota Check" to the Review Protocol asking "Did I generate >2 findings? If so, what is the depth-over-breadth justification for each?"
4. **Steel-man the alternative** — accept current behavior as deliberate redundancy. The consuming context (parent agent or user) can always filter; better to over-generate and filter than under-generate and miss. This may be the right design.

**Re-open prerequisites:**
1. Evidence base N≥2 multi-challenge contrarian arcs where the filed-bias is one symptom of a broader over-generation pattern (not just one symptom of one bias).
2. OR: post-#147 contrarian invocation produces ≥4 findings on a clearly-scoped narrow review (where breadth is anomalous to the work scope).
3. OR: user/adopter reports that contrarian-reviewer findings are systematically being treated as formulaic / dismissable.

**Origin.** Contrarian-reviewer audit `afac4381fd32e8721` MEDIUM finding raised during BACKLOG #147 post-edit double-check pressure test (session-142). Per the new `rules-of-procedure §7.8.1` rule: anticipatory items are valid; this is a "anticipate needing later" item. Filed per CLAUDE.md "Defer (with tracking)" rather than acted on now because n=1 + ironic-self-application risk (acting on contrarian's over-generation observation by adding more contrarian protocol = potentially proving the bias).

**Why D2 Discussion (not Fix or Improvement):** Open question whether the pattern is real, and the right intervention is unclear (4 alternatives above). Plan-mode required if/when re-opened. Not D3 because it's a single-file agent definition change; no new infrastructure.

---

#### 127. Document-Extractor Integration-Test Coverage Gap `D2 Capability`

**Filed:** 2026-04-23 (session-123 Commit L, BACKLOG #122 Case 8 deferral).

**What.** Phase 1 inventory for BACKLOG #122 Case 8 flagged `TestDocumentConnector::test_parse_markdown` (test_context_engine.py:437-ish) as a unit test with no paired integration test covering the end-to-end document-extractor parsing pipeline. Search for `test_extractor_integration.py` returns nothing — the file doesn't exist. Case 8 in #122 was disposed as "DEFER, don't fabricate a consolidation for a coverage gap."

**Scope.** Either (a) add a new integration test in `tests/test_extractor_integration.py` (or existing integration test file) exercising the full extractor pipeline on a realistic document — parse → chunk → classify → emit `ContentChunk`s with correct metadata; OR (b) decide the unit test IS sufficient coverage and document the decision in a test docstring.

**Trigger.** When adding new extractor features OR when extractor behavior changes semantically OR when triaging retrieval-quality regressions tied to parsing.

**Done when.** Either an integration test lands OR `TestDocumentConnector::test_parse_markdown` docstring explicitly documents why unit-level coverage is sufficient per CFR §5.2.3 (unit vs integration boundary).

---

#### 125-b. scaffold_project Framework Registry Seeding `D2 Capability`

**Filed:** 2026-04-23 (session-123 Commit J follow-up).

**What.** #125 shipped Commit J adding `scope: framework | project` to all 19 registry entries + lint assertion. Classification: 8 framework-universal + 11 project-specific. Registry is now positioned for scaffold-safety but `scaffold_project` itself does NOT yet seed a registry file for new adopter projects.

**Scope.** (a) Extend `src/ai_governance_mcp/server.py` SCAFFOLD_STANDARD_EXTRAS with a new template entry for `documents/failure-mode-registry.md` containing ONLY entries with `scope: framework`. (b) Adopter registry can then extend via their own entries with `scope: project`. (c) Lint in adopter project works as-is because `_load_registry_entries()` reads one YAML file.

**Design note.** Simplest approach: generate the framework-subset registry from the canonical one at scaffold time, not hardcode. Or: ship a small `documents/scaffold-templates/failure-mode-registry-framework-seed.md` that the canonical entries tag-sync to.

**Trigger.** External adopter feedback on registry bloat OR next `scaffold_project` feature addition.

---

#### 16. Governance Retrieval Quality Assessment (Discussion) `D2 Improvement`

**What:** Both governance server and Context Engine use BGE-small-en-v1.5 (384d). We don't know if the current model is underperforming — users may not notice degraded retrieval quality. Better models exist (nomic-embed 768d, higher benchmarks) but upgrade hasn't been justified with data.

**Discussion needed:** Related to #22 (closed — effectiveness measurement resolved by `scripts/analyze_feedback_loop.py`). How do we measure current retrieval quality for governance queries specifically? Is there a way to benchmark governance retrieval that would tell us if an upgrade is justified? Determine justification first, then implement if needed, drop if not — but with a way to measure effectiveness going forward.

**Possible directions:** Governance-specific benchmark queries, MRR/Recall measurements on governance corpus, A/B comparison with nomic-embed on representative queries.

**Outcome:** Either justify the upgrade with data and implement, or confirm current model is sufficient and close.


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

#### 12. Operational / Deployment Runbook Domain (Discussion) `D2 New Capability`

**What:** Framework covers how AI produces code but not how AI handles deployment, infrastructure, and operations. 3 solid practices from viral "AI vibe coding security rules" analysis couldn't be placed in existing domains.

**Discussion needed:** Is this a full domain or should the 3 orphaned practices just be filed in an appendix? Decision factors: are we using AI for deployment workflows? Is the gap growing? Domain vs standalone runbook vs appendix to AI Coding methods?

#### 41. Reference Library Auto-Staging Proposals (Discussion — Self-Improvement) `D2 Improvement`

**What:** After sessions involving complex problem-solving (5+ tool calls, novel governance patterns, or trial-and-error workflows), the system proposes reference library entries to the `staging/` directory with `maturity: seedling`. Human reviews staging during completion sequence.

**Why:** The reference library staging infrastructure exists (`staging/` directory, `_criteria.yaml` per domain, completion sequence prompt) but is dormant — `.gitkeep` placeholder, never activated. Hermes Agent's procedural memory (autonomous skill creation) demonstrates the value of automated capture, but their approach lacks quality gates. Our staging path provides the human gate that prevents noise while closing the capture gap.

**What's involved:** (1) Define trigger criteria — what constitutes "worth capturing" (session complexity, novel pattern, user correction that changed approach), (2) Activate `_criteria.yaml` with per-domain capture rules, (3) Build the staging proposal mechanism (likely a new MCP tool or extension to completion sequence), (4) Define the staging review workflow.

**Dependency:** None — staging infrastructure already exists.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes auto-creates skills every 15 tool-calling iterations via background review agent. Our adaptation: auto-propose to staging with human gate, leveraging our richer metadata model (maturity, decay classes, KeyCite currency).

---

#### 43. Progressive Disclosure for Reference Library (Discussion — Retrieval Efficiency) `D2 Improvement`

**What:** Currently, matched reference library entries return full content in evaluation results. Adopt a tiered retrieval model: Tier 1 (in evaluation results) shows ID, title, summary, maturity/status, confidence — as we do now. Tier 2 (on demand) provides full artifact content via a new `get_reference(id)` tool. Tier 3 (deep dive) includes related references, cross-references, principle links.

**Why:** As the reference library grows, dumping full artifacts into every evaluation result will bloat context. Hermes's 3-tier progressive disclosure (skill index → `skill_view(name)` → linked files) keeps token cost low while making full content available when needed. Our current 9 entries are manageable; at 50+ this becomes a real problem.

**What's involved:** (1) New `get_reference` MCP tool returning full artifact content by ID, (2) Modify evaluation output to show Tier 1 summaries only, (3) Optionally add Tier 3 with cross-reference expansion. Relatively straightforward — the data model already has `summary` fields and cross-reference metadata.

**Dependency:** None — can implement independently.

**Origin:** Hermes Agent evaluation (2026-04-01). Their skill_view progressive loading pattern adapted to our retrieval model.

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

#### ~~54.~~ Closed. Superpowers reference library entry shipped + CFR Part 9.5 Skills Taxonomy. `git log --grep="backlog #54"`

#### ~~55.~~ Closed. Skills as standardized work — 3 skills shipped (compliance-review, completion-sequence, test-authoring), CFR Part 9.5 method section, `workflows/` directory removed. `git log --grep="backlog #55"`

#### 58. Session Lifecycle Automation — Mid-Session Re-Injection (Discussion — from UBDA Review) `D2 Improvement`

**What:** Context degradation accelerates past critical thresholds. Thresholds exist (50/60/80/32K) but no automation triggers behavioral floor re-injection mid-session. UserPromptSubmit hook could check context utilization and re-inject.

**Revisit trigger:** If measurement shows degradation despite few-shot improvement from #77.

**Origin:** Perplexity Deep Research UBDA review (2026-04-07). Research: arxiv 2601.04170 (episodic memory consolidation — 51.9% drift reduction).

#### 59. Single-Session Intent Alignment Drift (Discussion — from UBDA Review) `D2 Improvement`

**What:** Multi-agent immutability rules handle cross-agent intent preservation. But single-session intent drift within one agent's long task is a distinct failure mode (arxiv 2602.07338). User's progressive expression of intent diverges from model's interpretation over turns. Degradation is ~constant regardless of model size.

**Revisit trigger:** If observed in measurement or if sessions regularly exceed 40+ turns on a single task.

**Origin:** Perplexity Deep Research UBDA review (2026-04-07). Research: arxiv 2602.07338 (Liu et al., challenges Laban et al. framing).

#### 60. Semantic Compliance Monitoring — Supervisor Agent (Discussion — from UBDA Review) `D2 Improvement`

**What:** Current measurement is binary (was evaluate_governance called? yes/no). A supervisor LLM checking semantic compliance after each governance call would detect "was this actually a recommendation or a question-disguised-as-recommendation?" NeMo Guardrails implements this as policy compliance rate metric.

**Revisit trigger:** Productionization or multi-user deployment.

**Origin:** Perplexity Deep Research + Gemini UBDA review (2026-04-07). Both flagged quality-of-compliance vs occurrence gap.

#### 85. Content Enhancer Integration + Multi-System Orchestration (Discussion) `D2 Improvement`

**What:** Two related concepts:

1. **Content Enhancer integration** — Integrate the High-Fidelity Educational Content Enhancer 3.0 into the ai-governance framework. The Content Enhancer is a 4-phase pipeline for transforming raw content into cognitively-optimized reference documents. Source files: `~/Documents/Reference/AI/AI High-Fidelity Educational Content Enhancer/`. Plan-mode exploration (2026-04-10) identified three viable paths: (A) governance constraints only (Part 14.7 + reference + CE indexing), (B) Content Enhancer as a skill, (C) hybrid.

2. **Multi-system orchestration (future)** — n8n-style workflows orchestrating across multiple external systems (CI/CD, notifications, deployments). This is the "Orchestration" layer of the 4-layer execution taxonomy (EXECUTION-FRAMEWORK.md §3.7, CFR Part 9.5). Not yet needed — current repeatable procedures are skills. Revisit when cross-system automation needs emerge.

**Context update (2026-05-09):** #55 (Workflow Codification) closed — skills infrastructure shipped (3 skills, CFR Part 9.5 method section). The Content Enhancer could now be implemented as a skill (path B). The "workflow" concept in EXECUTION-FRAMEWORK.md §3.7 has been redefined as future multi-system orchestration, distinct from skills (single-system repeatable procedures).

**Origin:** Content Enhancer: plan-mode exploration (2026-04-10). Multi-system orchestration: EXECUTION-FRAMEWORK.md §3.7 taxonomy update (2026-05-09).

**Origin:** User-initiated (2026-04-10). Plan mode exploration completed but implementation paused for deeper workflow pattern discussion.

