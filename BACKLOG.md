# Backlog

**Purpose:** Track discussion items and deferred work across sessions.
**Lifecycle:** Items are added when discovered, closed when implemented or dropped. Git commit history is the archive for closed items (`git log --grep="backlog #N"`).

> **Staleness rule (2026-04-14):** Discussion items with no activity for 90+ days are flagged for review during the next compliance review (workflows/COMPLIANCE-REVIEW.md Check 8). User decides: keep, close, or reframe.

---

### Open Backlog

> **Backlog Philosophy (2026-03-30, updated 2026-04-08):** Items fall into two categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it." See also #33.
>
> **No closed/completed items in this file.** When an item is closed, remove it from this file entirely. Git commit history is the archive — commit messages document what was closed and why. Maintaining closed item lists, completed tables, or historical detail sections in a working document is redundant with version control and causes unbounded file growth. If you need closure context for a past item, use `git log --grep="backlog #N"` or search commit messages.
>
> **Difficulty classification (D1-D3).** Every backlog item gets a difficulty tag. Per `meta-quality-verification-validation`, criteria must be observable, not subjective.
>
> | Level | Label | Definition | Observable Indicators |
> |-------|-------|-----------|----------------------|
> | **D1** | Single-session | Completable in one session without plan mode | Docs-only OR known pattern, no new infrastructure, no dependencies |
> | **D2** | Multi-session | Requires plan mode OR spans multiple sessions | New tool/hook/section, moderate research, or depends on 1-2 other items |
> | **D3** | Architecture | Plan mode + external review + broad changes | New domain, cross-cutting refactor, new service, heavy research |
>
> **Rules:** Default to D1 unless indicators push higher. Plan mode → at least D2. New domain or cross-cutting → D3. When uncertain, pick higher. Re-evaluate when starting work — tags are estimates, not commitments.
>
> **Type tags:** Fix, Improvement, New Capability, Docs, Maintenance. Ranked order: fixes first → improvements → new capabilities.

---

### Active (Implement Now/Soon)

78. **Governance Compliance Review — ongoing, next review due ~2026-04-24** `D1 Maintenance` (every 10-15 calendar days). Reviews #1 (2026-04-13) and #2 (2026-04-14) complete. See workflows/COMPLIANCE-REVIEW.md. Event triggers: hook/CLAUDE.md/tiers.json modification.


---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

#### 90. Context Engine Circuit Breaker Auto-Recovery (Discussion) `D1 Improvement`

**What:** The circuit breaker in `project_manager.py` has no auto-recovery. After 3 consecutive watcher failures, auto-indexing is permanently disabled until a manual `index_project` call or server restart. A transient burst of rapid edits (e.g., `git checkout` of a large branch) can trip it.

**Discussion needed:** Should the circuit breaker use exponential backoff with retry (e.g., 30s, 60s, 120s, then permanent trip)? This would make transient failures self-healing while still protecting against persistent failures. Trade-off: retries consume resources if the underlying issue is real (not transient).

**Origin:** Contrarian review of #89 race condition fix (2026-04-11). Rated MEDIUM severity.

#### 22. Governance Effectiveness Measurement (Discussion) `D1 Improvement`

**What:** The framework can measure whether `evaluate_governance` was *called* but not whether it *influenced decisions*. Can we measure the framework's actual effectiveness?

**Discussion needed:** Explore what meaningful metrics look like. This isn't about creating a metric for metric's sake — it's about understanding whether governance adds value and how. Could be several smaller metrics tracking different effectiveness aspects. May conclude some aspects aren't measurable and that's fine.

**Possible directions:** Track behavior-changing evaluations (PROCEED_WITH_MODIFICATIONS, ESCALATE), measure retrieval relevance scores over time, track principle citation frequency vs actual influence, qualitative session reviews.

**Outcome:** Either define metrics worth implementing, or conclude the value is qualitative and close this item.

#### 16. Governance Retrieval Quality Assessment (Discussion) `D2 Improvement`

**What:** Both governance server and Context Engine use BGE-small-en-v1.5 (384d). We don't know if the current model is underperforming — users may not notice degraded retrieval quality. Better models exist (nomic-embed 768d, higher benchmarks) but upgrade hasn't been justified with data.

**Discussion needed:** Related to #22 (effectiveness measurement). How do we measure current retrieval quality for governance queries specifically? Is there a way to benchmark governance retrieval that would tell us if an upgrade is justified? Determine justification first, then implement if needed, drop if not — but with a way to measure effectiveness going forward.

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

#### 49. Embedding Model Memory Sharing Across Processes (Discussion — Performance) `D3 Improvement`

**What:** Each MCP server process (governance server, Context Engine server, CE watcher) loads its own copy of the same embedding model (BGE-small-en-v1.5) into memory independently. With 2 concurrent Claude Code sessions, this means 5 Python processes each loading the same model + PyTorch runtime — macOS charged ~27 GB across them and triggered a low-memory warning on a 64 GB machine. A 16 GB machine would be unusable with 2 sessions.

**Root cause:** The MCP protocol runs each server as an isolated process with no shared memory mechanism. All 5 processes use the same model (BGE-small, confirmed via metadata.json), but each loads its own copy + its own PyTorch runtime. The duplication is purely architectural — no technical reason these can't share.

**Key finding:** Both governance server and Context Engine already use the same model (BGE-small-en-v1.5, 384d). SESSION-STATE previously documented CE as using nomic-embed — that was stale; nomic-embed was evaluated but never deployed. This simplifies the fix: one model, one process, all consumers call it.

**Why it matters:** Scaling barrier for adoption. Single-session is fine (~130 MB RSS), but multi-session or machines <32 GB will hit memory pressure. macOS low-memory warning triggered on a 64 GB machine with 2 sessions + Docker + normal apps.

**Recommended approach:** Shared embedding service — a single lightweight process loads BGE-small once, other processes call it via IPC/HTTP socket. Benefits: (1) memory drops from 5× to 1× model load, (2) other 4 processes no longer need PyTorch at all (dramatic footprint reduction), (3) no accuracy tradeoffs since it's already the same model everywhere.

**Other approaches considered:**
1. Lazy unloading — saves memory between queries but adds ~2-3s latency per query burst
2. Smaller model — all-MiniLM-L6-v2 (23 MB) but lower quality; evaluated and rejected (2026-02-14, MRR 0.569 vs BGE 0.627)
3. Single unified MCP server — merge governance + CE into one process; breaking architectural change
4. Process pooling — multiple sessions share one server; MCP protocol may not support natively

**Origin:** Session 48 (2026-04-03). macOS low-memory warning with 2 concurrent sessions. Initial investigation incorrectly dismissed Activity Monitor's GB numbers as "just virtual memory" — 26 GB swap + macOS warning proved impact is real.

#### 19. Rampart Integration — Client-Side Enforcement (Discussion) `D1 New Capability`

**What:** Rampart provides shell-level security enforcement (credential theft, exfiltration, destructive commands). Complements MCP proxy and hooks — different root cause. Hooks enforce "did you consult governance?" (process gate); Rampart enforces "is this command safe?" (security gate). Defense-in-depth.

**Discussion needed:** Evaluate whether the incremental security value justifies the setup for a single-developer Claude Code project. Research current Rampart capabilities and rule set.

#### 13. Governance-Aware Output Compression (Discussion) `D1 Fix`

**What:** Long Bash output wastes context window tokens. Build a PostToolUse hook that compresses verbose output while preserving governance/security lines and structured data.

**Discussion needed:** Is this still relevant as context windows grow? Measure actual context consumption from Bash output. If >20% threshold is hit, define the compression approach (per §3.1.4 "build our own" mode to avoid third-party information intermediary risk per §5.6.8).

#### 10. UI/UX Tool-Specific Integration Guides (Discussion) `D1 New Capability`

**What:** Write integration guides for AI-assisted design tools (Figma MCP, Storybook MCP, Axe MCP, Playwright MCP, etc.) as they're adopted. Research already done (candidate tools, risks, token costs documented in git history — search commits for "backlog #10").

**Discussion needed:** Which tools are most likely to be adopted first? What format should integration guides take? Reference the existing research.

#### 11. Autonomous Operations Domain (Discussion) `D3 New Capability`

**What:** Autonomous agent patterns (AO-Series, currently 4 principles in Multi-Agent) may eventually outgrow the multi-agent domain. This would create a dedicated domain for autonomous operation governance — financial compliance, regulatory frameworks, agent marketplace governance, cross-org federation.

**Discussion needed:** Is this anticipatory need real? What would trigger the split? The Domain Creation Criteria (§5.1.0) already defines when to create domains, but the user wants to understand if the AO-Series trajectory warrants keeping this on the radar.

#### 12. Operational / Deployment Runbook Domain (Discussion) `D2 New Capability`

**What:** Framework covers how AI produces code but not how AI handles deployment, infrastructure, and operations. 3 solid practices from viral "AI vibe coding security rules" analysis couldn't be placed in existing domains.

**Discussion needed:** Is this a full domain or should the 3 orphaned practices just be filed in an appendix? Decision factors: are we using AI for deployment workflows? Is the gap growing? Domain vs standalone runbook vs appendix to AI Coding methods?

#### 35. Evaluate Stripe Projects CLI for Appendices (Discussion) `D1 New Capability`

**What:** Stripe Projects CLI (launched 2026-03-27, developer preview) lets developers and AI agents provision third-party services, manage credentials, and handle billing from the terminal. Evaluate whether it belongs in the ai-governance appendices as tool-specific guidance.

**Origin:** Claude.ai research conversation. Preliminary assessment produced WITHOUT governance tooling — treat as research input, not validated conclusions.

**Why it matters for governance:** This tool lets AI agents trigger real financial transactions (paid-tier upgrades via Shared Payment Tokens) and provision infrastructure autonomously. That's squarely in AO-Series (autonomous operations) and S-Series (safety/security) territory.

**Preliminary mapping (UNVALIDATED — needs `evaluate_governance()` and subagent review):**
- `coding-method-agent-to-service-integration-patterns` — standardizes provisioning workflows
- `coding-method-credential-isolation-and-secrets-management` — vault-based credential storage
- `coding-method-service-identity-and-credential-lifecycle` — provider account association
- `meta-safety-non-maleficence-privacy-security` (S-Series) — credential handling, financial action authority
- `coding-process-established-solutions-first` — but developer preview maturity is a concern

**Key governance concerns to resolve:**
1. **Agent autonomy on financial actions.** Agents can select paid tiers triggering real charges. Which principles govern this? What HITL enforcement mechanism?
2. **Maturity risk.** Developer preview, US/EU/UK/Canada only, expanding provider catalog. Does "Established Solutions First" apply to a tool this new?
3. **Shared Payment Token security model.** Tokenized payment credentials passed to providers. Security-auditor evaluation needed.
4. **Vendor dependency.** Does the framework endorse specific vendors or just document patterns?

**Research sources:** Stripe docs (docs.stripe.com/projects), projects.dev, Stripe X announcement, HN discussion (47532148), Karpathy blog post that motivated it.

**When discussed:** Run full governance evaluation, contrarian-reviewer (does it belong at all?), coherence-auditor (appendix fit), security-auditor (credential/payment model). Three possible outcomes: add now, add with conditions, or do not add.

---

#### 79. Apple Mail MCP Server — Tool-Specific Governance Guidance (Discussion) `D1 New Capability`

**What:** Add governance guidance for the [apple-mail-mcp](https://github.com/s-morgan-jeffries/apple-mail-mcp) open-source MCP server (MIT license, pre-release). Enables AI to read, search, compose, send, and manage emails via Apple Mail.app on macOS. 14 exposed tools across read/search, compose/send, attachments, and organization.

**Why it matters for governance:** AI accessing email is a high-sensitivity capability — S-Series (privacy/security), AO-Series (autonomous actions with real-world consequences like sending emails). The server runs locally (no cloud routing) and requires explicit macOS Automation permission, which is good, but it grants access to all configured mail accounts once approved.

**Key governance concerns:**
1. **Placement:** Does this fit as an appendix to an existing domain (multi-agent? ai-coding?), or is there a broader "tool-specific MCP governance" pattern emerging? See also #35 (Stripe Projects CLI) and #10 (UI/UX tool guides) — three tool-specific items may indicate a pattern.
2. **Autonomy on destructive actions:** `send_email`, `delete_messages`, `forward_message` have real-world blast radius. What HITL enforcement? The server has confirmation flows, but governance should define when AI can vs. cannot act autonomously.
3. **Scope of access:** All mail accounts, not per-account. Governance should recommend dedicated AI mail account.
4. **Pre-release maturity risk:** No version tags, 2 contributors, 23 open issues. Same "Established Solutions First" concern as #35.
5. **AppleScript injection surface:** Input sanitization exists but should be security-auditor reviewed.

**Architecture:** Python FastMCP → AppleScript bridge → Apple Mail.app. Local only, no credentials stored, audit logging included.

**When discussed:** Run governance evaluation, consider whether #35 + #79 + #10 indicate a "Tool Integration Governance" appendix or domain pattern. Security-auditor review of the AppleScript bridge.

---

#### 34. Epistemic Integrity — Constitutional Principle (Discussion) `D1 Improvement`

**What:** Proposed new Q-Series constitutional principle addressing AI sycophancy — the tendency to validate flawed assumptions, reinforce suboptimal approaches, or present outputs with unearned confidence. Core requirement: analytical accuracy over conversational agreeability.

**Origin:** Independent research via Claude app (no anchor bias from existing framework). Reviewed against Part 9.8 Admission Test — passes all 6 questions. Contrarian review and coherence audit completed (see draft below).

**The gap:** Three existing principles touch adjacent territory but none address the core failure mode:
- **Transparent Limitations (S-Series):** Covers "I don't know" — NOT "I agree but shouldn't"
- **Discovery Before Commitment (C-Series):** Covers AI's own investigation process — NOT AI's evaluative posture toward human claims
- **Visible Reasoning & Traceability (Q-Series):** Covers making reasoning auditable — NOT whether reasoning prioritizes accuracy over agreeability

**Key question to resolve: consolidation vs addition.** If this becomes a principle, does it REPLACE or ABSORB aspects of the three above? Per Single Source of Truth, if Epistemic Integrity subsumes the "epistemic honesty" aspect of Transparent Limitations, the "challenge the frame" aspect of Discovery Before Commitment, and the "self-scrutiny" aspect of Visible Reasoning — should those principles be narrowed to avoid redundancy? The goal is one authoritative home for each concept, not three principles each partially covering honesty.

**Possible outcomes:**
1. **New principle + narrow the three** — Epistemic Integrity becomes the single source for intellectual honesty; TL, DBC, VR&T retain their non-overlapping scopes
2. **Expand one existing principle** — e.g., expand Visible Reasoning to include "quality of reasoning, not just visibility of reasoning"
3. **Method only** — Create the Performance Assessment Protocol method under an existing principle without a new constitutional addition
4. **Close** — Existing principles + contrarian-reviewer subagent already cover this adequately

**Draft principle:** Full draft available (reviewed by contrarian + coherence auditor). Key components:
- Challenge Before Confirm (earned agreement, not default agreement)
- Self-Scrutiny Before Delivery (apply same standard to own outputs)
- Evidence-Grounded Assessment (benchmarks over pleasantries)
- Constructive Alternatives Over Rejection (better outcomes, not intellectual sparring)
- Proportional Scrutiny (calibrate pushback to stakes)

**Revisions needed before implementation (from review):**
1. Soften "at least one material risk" threshold → "demonstrated consideration of alternatives" (avoid checkbox behavior)
2. Add Intent Preservation boundary: challenges target methods/assumptions, not the human's underlying goals
3. Verify Q-series numbering (Q8?) against current count

**Related:** Would also create `meta-method-performance-assessment-protocol` (behavioral rules for honest feedback) and add `constitutional_basis` to contrarian-reviewer subagent definition.

**Note (from #9P3 closure, 2026-04-02):** #9P3 closed — the "reasoning quality vs reasoning visibility" concept is now tracked here. Visible Reasoning (Q-Series) covers *visibility* of reasoning; this item covers *quality/soundness* of reasoning. If #34 is closed without shipping, the soundness gap needs re-evaluation.

---

#### 41. Reference Library Auto-Staging Proposals (Discussion — Self-Improvement) `D2 Improvement`

**What:** After sessions involving complex problem-solving (5+ tool calls, novel governance patterns, or trial-and-error workflows), the system proposes reference library entries to the `staging/` directory with `maturity: seedling`. Human reviews staging during completion sequence.

**Why:** The reference library staging infrastructure exists (`staging/` directory, `_criteria.yaml` per domain, completion sequence prompt) but is dormant — `.gitkeep` placeholder, never activated. Hermes Agent's procedural memory (autonomous skill creation) demonstrates the value of automated capture, but their approach lacks quality gates. Our staging path provides the human gate that prevents noise while closing the capture gap.

**What's involved:** (1) Define trigger criteria — what constitutes "worth capturing" (session complexity, novel pattern, user correction that changed approach), (2) Activate `_criteria.yaml` with per-domain capture rules, (3) Build the staging proposal mechanism (likely a new MCP tool or extension to completion sequence), (4) Define the staging review workflow.

**Dependency:** None — staging infrastructure already exists.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes auto-creates skills every 15 tool-calling iterations via background review agent. Our adaptation: auto-propose to staging with human gate, leveraging our richer metadata model (maturity, decay classes, KeyCite currency).

---

#### 42. Feedback Loop Analysis Tool (Discussion — Self-Improvement) `D2 Improvement`

**What:** New MCP tool (e.g., `analyze_feedback_loop()`) that reads existing log files (`feedback.jsonl`, `governance_reasoning.jsonl`, `governance_audit.jsonl`, `queries.jsonl`) and produces actionable proposals: dead principle detection, false positive pattern identification, retrieval gap reports, principle health scoring.

**Why:** We log everything but never analyze the logs to improve the system. The feedback infrastructure exists and is underused (contrarian review finding). Closing the feedback loop is the core mechanism for self-improvement — the system surfaces what it's learned from its own evaluation history, proposing refinements rather than silently modifying itself.

**What's involved:** (1) Define analysis queries (which patterns are actionable), (2) Implement log parsing and pattern detection, (3) Define output format (proposals with evidence, not automated changes), (4) Determine trigger — on-demand tool call vs. periodic analysis. Specific analyses: principles never retrieved in N days, S-Series triggers with >50% false positive rate, queries consistently returning <0.3 confidence, principles with high retrieval but low feedback scores.

**Dependency:** Partially related to #22 (Governance Effectiveness Measurement) — this tool would provide concrete data for that discussion.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes closes the loop via trajectory compression → model training. We can't fine-tune Claude, but we can close the loop by analyzing our own logs to surface improvement proposals.

---

#### 43. Progressive Disclosure for Reference Library (Discussion — Retrieval Efficiency) `D2 Improvement`

**What:** Currently, matched reference library entries return full content in evaluation results. Adopt a tiered retrieval model: Tier 1 (in evaluation results) shows ID, title, summary, maturity/status, confidence — as we do now. Tier 2 (on demand) provides full artifact content via a new `get_reference(id)` tool. Tier 3 (deep dive) includes related references, cross-references, principle links.

**Why:** As the reference library grows, dumping full artifacts into every evaluation result will bloat context. Hermes's 3-tier progressive disclosure (skill index → `skill_view(name)` → linked files) keeps token cost low while making full content available when needed. Our current 9 entries are manageable; at 50+ this becomes a real problem.

**What's involved:** (1) New `get_reference` MCP tool returning full artifact content by ID, (2) Modify evaluation output to show Tier 1 summaries only, (3) Optionally add Tier 3 with cross-reference expansion. Relatively straightforward — the data model already has `summary` fields and cross-reference metadata.

**Dependency:** None — can implement independently.

**Origin:** Hermes Agent evaluation (2026-04-01). Their skill_view progressive loading pattern adapted to our retrieval model.

---

#### 44. Auto-Maturity Proposals from Usage Data (Discussion — Self-Improvement) `D2 Improvement`

**What:** Automate maturity promotion proposals for reference library entries based on usage signals: seedling → budding (retrieved 3+ times with positive feedback), budding → evergreen (retrieved across 2+ projects, no negative feedback in 6+ months), any → caution/deprecated (not retrieved in N months based on decay_class).

**Why:** The maturity pipeline (seedling → budding → evergreen) and KeyCite currency tracking exist but are entirely manual. Usage data from query logs and feedback could drive proposals. This makes the reference library self-curating — entries that prove useful get promoted, entries that go stale get flagged.

**What's involved:** (1) Track per-reference retrieval counts and feedback scores (may need to enhance logging), (2) Define promotion/demotion thresholds per maturity level and decay class, (3) Surface proposals — likely as part of #42's analysis tool output rather than a separate mechanism.

**Dependency:** Benefits from #42 (Feedback Loop Analysis) — the analysis tool would be the natural home for maturity proposals. Could also work standalone with simpler log parsing.

**Origin:** Hermes Agent evaluation (2026-04-01). Hermes skills have no maturity tracking at all — all skills are equal weight. Our maturity model is better but currently manual. Automation closes the gap.

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

#### 54. Superpowers Plugin — Reference Library Entry + Method Assessment (Discussion — from Video Re-Analysis) `D1 Improvement`

**What:** The Superpowers plugin (github.com/obra/superpowers, v4.3.0, 93K+ developers, Anthropic-endorsed) is a methodology-as-code framework implementing a brainstorm→write-plan→execute-plan pipeline using SKILL.md files. It packages several ai-governance principles (orchestration, context isolation, spec-driven development, sequential phase dependencies, atomic task decomposition) into three executable commands that enforce the workflow structurally.

**Why it matters:** Our framework has the principles; Superpowers has the packaging. It implements our Sequential Phase Dependencies as *the only path available* rather than advisory guidance. Plans include "complete, runnable code for each task" — more concrete than our method-level guidance which stops at "decompose into atomic tasks." Sub-agents implement each task with two-stage review, matching our multi-agent architecture patterns.

**Root concept:** This is the most significant third-party implementation of our multi-agent and ai-coding principles working together. Worth studying as a precedent case — not for what principles it covers (we already have those) but for how concretely it implements them.

**Actions:**
1. Create a Reference Library entry: what Superpowers implements from our framework, where its implementation is more concrete than our methods, patterns worth adopting
2. Assess whether our ai-coding methods should have more concrete "plan format" guidance (Superpowers plans specify exact file paths, terminal commands, failing tests, and git commit messages for each task)
3. Evaluate the brainstorm→write-plan→execute-plan pattern against our development sequence planning method for method-level improvements

**Research done:** Builder.io blog, GitHub repo, Geeky Gadgets review, SAP Community guide, ddewhurst blog analysis. Key architecture: SKILL.md files with YAML frontmatter (trigger conditions, process, guardrails) — same pattern as our `.claude/agents/*.md` subagent definitions.

**Origin:** Claude Code workflow video re-analysis (2026-04-05). Previously evaluated as "covered" — re-examined with method-level quality lens per §9.8.2 scope boundary.

#### 55. Workflow Codification — Skills as Standardized Work (Discussion — from Video Re-Analysis) `D1 Improvement`

**What:** Claude Code skills (SKILL.md files) enable repeatable workflow codification — the discipline of identifying, designing, codifying, validating, and iterating AI-assisted workflows. The video's "creature-forge" example shows a user who identified a repeatable process, built a skill, ran it, got failures, iterated with feedback, and now has a reliable automated workflow. This is the PDCA cycle applied to AI workflows.

**Why it matters:** The framework covers learning from failures (Continuous Learning & Adaptation) but not packaging successes into reusable workflows. Skills, n8n workflows, SOPs, work instructions, and subagent patterns are all implementations of the same root concept: standardized work.

**Framework gap:** No formal guidance on WHEN to create a skill, HOW to design one well, or what governance should apply to skill creation. The `install_agent` mechanism is the closest analog but is scoped to governance agents, not general workflow templates.

**Actions:**
1. Add a method section in ai-coding Appendix A (Claude Code Configuration) covering: when to create a skill (repeatable process done 3+ times), skill design principles (self-contained, include error handling, reference governance), the iteration cycle (expect first run to fail, iterate with feedback)
2. Cross-reference to existing `update-config` skill as an example
3. Assess whether this warrants a broader "workflow codification" method or is adequately scoped as Claude Code-specific guidance
4. Determine governance guidance for skill creation: should workflows reference governance principles? What review process?

**Research done:** Official Claude Code skills docs (code.claude.com/docs/en/skills), claude-code-skill-factory GitHub, awesome-claude-code curated list, ProductTalk guide, batsov.com essential skills guide. Key feature: `disable-model-invocation: true` for workflows with side effects (/deploy, /send-slack-message).

**Cross-reference (2026-04-10):** The Content Enhancer integration discussion (#84) surfaced a broader pattern. The framework already has multiple workflows (Completion Sequence, Compliance Review, Session Protocols, Domain Creation, Content Authoring) but no infrastructure for defining and governing workflows as a category. The Content Enhancer may be the first concrete instance of a codified workflow — making this item (#55) potentially the infrastructure layer and the Content Enhancer (#84) a specific workflow running on it. This reframing elevates #55 from "Claude Code skills guidance" to "workflow codification as a framework concept" — with skills being one implementation mechanism. Discussion needed: what distinguishes a "workflow" from a "method" in the framework? See #84 for full discussion context.

**Origin:** Claude Code workflow video re-analysis (2026-04-05).

#### 57. Recommended Tooling Appendix Entries — Warp, cc-status-line, Sequential Thinking (Discussion — from Video Re-Analysis) `D1 Docs`

**What:** Four tools from the Claude Code workflow video that implement existing framework principles as concrete tooling. Happy Engineering documented in Appendix F.1 (2026-04-08). Three remaining candidates for ai-coding appendix entries.

**Warp Terminal (warp.dev):**
- AI-native terminal with side panel for viewing repo files alongside Claude Code conversation, split panes for multiple Claude instances, tabbed sessions
- Implements: `multi-reliability-observability-protocol` (visibility into agent progress), human-in-the-loop review (see plans/specs/code in real-time while talking to Claude)
- Key value: review generated plans and code without leaving the terminal — supports the "don't just click yes to everything" discipline the video emphasizes
- Free, not sponsored

**cc-status-line plugin (`npx cc-status-line@latest`):**
- Adds real-time status bar: model name, context window %, session cost, session duration, git branch, work tree
- Implements: `coding-context-context-window-management` (The Token Economy Act), `coding-method-context-monitoring`
- Key value: makes context % visible without checking manually — directly enables the 50% threshold rule (backlog #56)
- Pairs with #56 — the threshold is useless without a way to see it

**Happy Engineering (happy.engineering):**
- Free, open-source remote Claude Code terminal control from mobile
- Unlike official Claude mobile app: runs on your actual machine, full access to all plugins (superpowers, context7, etc.) and local files
- Implements: `multi-reliability-state-persistence-protocol` (session continuity), `multi-reliability-observability-protocol` (remote monitoring)
- Alternative to Anthropic's Dispatch/remote pairing feature (user has had reliability issues with Dispatch)
- iOS/Android + web app

**Sequential Thinking MCP server:**
- Chain-of-thought reasoning tool that forces step-by-step decomposition for Claude
- Video recommends installing alongside Superpowers to "upgrade thinking powers"
- Implements: `meta-core-systemic-thinking` (structured reasoning), plan-mode workflow principles
- Install: `claude` → "please install sequential thinking MCP server"
- Pairs with Superpowers — enhances brainstorming quality

**Actions:**
1. ~~Evaluate each for Appendix A entry — recommended tooling section~~ → Happy Engineering documented in Appendix F.1 (2026-04-08)
2. For cc-status-line: include the user's exact line 1/line 2 config from the video as a recommended setup
3. ~~For Happy Engineering: compare against Anthropic's Dispatch feature for reliability and governance compliance~~ → Done: 3-way comparison table (/remote-control vs Happy vs Dispatch) in Appendix F.1
4. For Sequential Thinking: evaluate whether it complements or conflicts with our plan-mode template approach
5. Remaining: Warp, cc-status-line, Sequential Thinking still need evaluation

**Origin:** Claude Code workflow video re-analysis (2026-04-05). Low priority — tooling recommendations, not framework changes.

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

#### 84. README Rewrite — Intent Engineering Framing (Discussion — In Progress in Claude App) `D1 Docs`

**What:** New README for the ai-governance project, being drafted in a Claude app conversation. Frames the project as "intent engineering" infrastructure — encoding goals, constraints, quality standards, and decision-making boundaries so AI understands purpose, not just instructions.

**Status:** Active draft in Claude app. Content below is a snapshot to prevent session loss.

**Key framing:** The industry has moved through three phases: prompt engineering (how you phrase a request) → context engineering (what information AI has access to) → intent engineering (what must be achieved and how success is measured). This project operates at the third level.

**7 core components identified in draft:**
1. **Content Enhancer** (High-Fidelity Educational Content Enhancer 3.0) — processing engine for turning raw material into structured knowledge. Separates principles (immutable) from approaches (adaptable). Grounded in Mayer's multimedia learning, cognitive load theory, retrieval practice.
2. **AI-Assisted Development Framework** — 5 core principles (specification prevents iteration, AI is implementation tool not architect, verify everything, quality accelerates delivery, production standards from start), 8-phase sequential process. Technology-agnostic.
3. **Knowledge Domains** — each follows same structure (principles separated from approaches, evidence-based, cognitive load optimized). Anyone can create their own domains.
4. **AI Instructions Layer** — system-level instructions: classification protocols, risk assessment, fidelity requirements, enhancement tags, QA checklists, confidence scoring.
5. **Memory System** — persistent context across interactions: project-level (CLAUDE.md), domain-level (knowledge bases), interaction-level (working style/preferences/decisions).
6. **Workflow & Compliance Layer** — sequential phase requirements, verification checkpoints (DO-CONFIRM checklists), quality gates, documentation standards.
7. **Transparency and Attribution System** — tagging of original vs enhanced content, external research sourcing, reorganization tracking.

**Governing philosophy:** Not making AI smarter — giving it judgment. The infrastructure acts as a filter for contradictory internet knowledge, telling AI what quality looks like and how to evaluate conflicting information.

**Differentiator:** Most AI tools are destination-specific (guide toward a specific outcome). This infrastructure is destination-agnostic — upgrades how AI performs for whatever you're doing. "The GPS, the road kit, the reliability layer — not the route itself."

**Open architecture:** Built-in instructions for others to create, change, and remove their own principles and standards.

**Research context:** Claude app conversation explored "intent engineering" as a term and researched public usage of the concept.

**Origin:** User-initiated README rewrite (2026-04-10). In progress — do not implement without further user direction.

---

#### 85. Content Enhancer Integration — Workflow Pattern Discovery (Discussion) `D2 Improvement`

**What:** Integrate the High-Fidelity Educational Content Enhancer 3.0 into the ai-governance framework. The Content Enhancer is a methodology for transforming raw content (transcripts, lectures, notes, docs, research) into cognitively-optimized reference documents. It currently lives outside the repo as two standalone files.

**Source files:** `~/Documents/Reference/AI/AI High-Fidelity Educational Content Enhancer/`
- `high-fidelity-educational-content-nehancer-3.0-ai-instructions-prompt.md` — system prompt version (for Claude projects)
- `high-fidelity-educational-content-nehancer-3.0-rag-optimized.md` — detailed spec for knowledge base ingestion

**Content Enhancer architecture:**
- **K-Store/A-Store separation** — principles (immutable, 100% fidelity) vs approaches (optimizable). Mirrors the framework's own principles/methods split.
- **4-phase pipeline** — Strategic Analysis & Classification → Content Extraction & Organization → Cognitive Optimization → Enhancement Implementation
- **Evidence base** — Mayer's 12 Multimedia Learning Principles, Cognitive Load Theory, Retrieval Practice, Universal Design for Learning
- **Enhancement tagging** — [SOURCE], [ENHANCEMENT], [EXTERNAL_ENHANCEMENT], [REORGANIZED], [LEARNING_ENHANCEMENT], [CLARIFICATION_NEEDED]
- **Confidence scoring** — 0.0-1.0 for all enhancements
- **Content-type protocols** — video/audio transcripts, technical docs, academic/research
- **Multi-layer QA** — fidelity verification, enhancement quality, learning science compliance
- **Risk classification** — High (medical, legal, safety) / Medium (business, academic) / Low (general educational)

**Plan mode exploration (2026-04-10) — three key findings:**

1. **Initial proposal: TITLE 17 in ai-governance-methods.** Contrarian review returned REVISIT (HIGH confidence). The Content Enhancer is a production workflow, not governance. Full absorption would cause: (a) bloat — 250-400 lines in an already 4,642-line file, (b) atrophy — governance versioning overhead slows the Enhancer's independent evolution, (c) precedent — every methodology becomes a TITLE. Contrarian's steel-manned alternative: governance constraints only (~40-60 line Part 14.7 covering fidelity standards, enhancement tagging, QA criteria) + full methodology stays standalone with Reference Library entry + Context Engine indexing.

2. **User reframed more structurally: "Is the Content Enhancer an instance of a pattern?"** The framework already has multiple workflows that aren't called workflows: Completion Sequence (COMPLETION-CHECKLIST.md), Compliance Review (COMPLIANCE-REVIEW.md), Session Start/End Protocols, Domain Creation (§5.1.0 + Part 9.8), Content Authoring (Part 9.8 + 3-agent battery). Backlog #55 (Workflow Codification) is about building infrastructure for codifying repeatable processes. The Content Enhancer may be a specific workflow running on a workflow infrastructure — #55 being the infrastructure, Content Enhancer being the first concrete instance.

3. **Open question (needs discussion before implementation):** What distinguishes a "workflow" from a "method" in the framework? The completion sequence is a checklist. The compliance review is a guided audit. The Content Enhancer is a 4-phase pipeline. Are these the same kind of thing, or meaningfully different? This determines whether the Content Enhancer gets its own treatment or fits into a broader workflow pattern that also encompasses the existing workflows.

**Three viable paths remain:**
- **(A) Governance constraints only** — Part 14.7 + standalone reference + CE indexing. Simplest. Treats Content Enhancer as external tool with governance guardrails.
- **(B) Content Enhancer as first instance of #55 workflow infrastructure** — Define what a "workflow" is in the framework first (#55), then the Content Enhancer becomes a specific workflow with a standard structure. More systemic but requires #55 to be resolved first.
- **(C) Hybrid** — Something that emerges from deeper #55 discussion. The workflow/method distinction may clarify what the right container is.

**Relationship to other items:**
- **#55 (Workflow Codification)** — potential infrastructure layer; updated with cross-reference
- **#84 (README)** — references Content Enhancer as "Component 1" of the broader AI infrastructure, but the README describes the system; this item is about integrating the Enhancer itself

**Origin:** User-initiated (2026-04-10). Plan mode exploration completed but implementation paused for deeper workflow pattern discussion.

#### 99. Quick Start Guide for External Adopters (Discussion) `D1 New Capability`

**What:** The framework has no onboarding path between "install the MCP server" and "understand the full governance hierarchy." A Quick Start guide presenting the 5 most critical principles without requiring Constitutional naming knowledge would lower the adoption barrier.

**Origin:** Contrarian review during v2.0.0 post-release audit (2026-04-13). Pairs with #53 (Modular Domain Architecture).

#### 100. Legal System Analogy Embedding Impact Test (Discussion) `D1 Improvement`

**What:** Each principle includes a Legal System Analogy paragraph (~15-20% of token budget) mapping it to US legal concepts. These legal terms may create embedding vectors biased toward legal rather than practical governance. Test hypothesis: run retrieval benchmark with and without analogy text. If MRR/Recall doesn't drop, extract analogy text from embedding content while preserving it in full documents.

**Origin:** Contrarian review during v2.0.0 post-release audit (2026-04-13).

#### 102. scaffold_project Standard Kit Misalignment (Discussion) `D1 Fix`

**What:** The `scaffold_project` tool creates 6 files for standard tier (core 4 + CLAUDE.md + COMPLETION-CHECKLIST.md), but CFR §1.5.2 defines Standard Kit as 8 files (core 4 + ARCHITECTURE.md + SPECIFICATION.md + COMPLETION-CHECKLIST.md + BACKLOG.md). The tool creates a different set than the CFR defines. Pre-existing misalignment — predates the BACKLOG.md addition.

**Discussion needed:** Should scaffold_project create all Standard Kit files, or is it intentionally a "minimum viable" standard scaffolding? If the latter, document this in the tool description. If the former, add ARCHITECTURE.md, SPECIFICATION.md, and BACKLOG.md templates to `SCAFFOLD_STANDARD_EXTRAS` and update tests.

**Origin:** Coherence audit during BACKLOG.md propagation (2026-04-14).

---

#### 101. Template Divergence Documentation (Discussion) `D1 Docs`

**What:** AI Coding and Multi-Agent use the full principle template (FM codes, Truth Sources, Success Criteria). Four other domains (Storytelling, UI/UX, KM&PD, Multimodal RAG) use variants (Validation Criteria, narrative Failure Mode, Constitutional Derivation, no Truth Sources). Document the accepted variants in rules-of-procedure.md's template section so future authors know both patterns are valid. Don't force uniformity — content quality matters more than field name consistency.

**Origin:** Validator during v2.0.0 post-release audit (2026-04-13).

---
