# Backlog

**Memory Type:** Prospective (intentions)
**Lifecycle:** Items are added when discovered, removed when implemented or abandoned. Git commit history is the archive for closed items (`git log --grep="backlog #N"`).

> **Staleness rule (2026-04-14):** Discussion items with no activity for 90+ days are flagged for review during the next compliance review (workflows/COMPLIANCE-REVIEW.md Check 8). User decides: keep, close, or reframe.

---

### Open Backlog

> **Backlog Philosophy (2026-03-30, updated 2026-05-03):** This file holds **discrete projects** — work with a start and an end. Items fall into two categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it."
>
> **Taxonomy (2026-05-03).** The project maintains two files for forward-looking work, distinguished by lifecycle:
> - **BACKLOG.md (this file)** — **Projects.** Discrete tasks with start and end. Close on completion or abandonment. Git history is the archive.
> - **OPERATIONS.md** — **Operational items.** Indefinite-lifecycle recurring commitments: cadences (periodic reviews), tripwires (conditional re-evaluations), verification experiments (time-bound hypothesis tests), effectiveness metrics (system health indicators), scheduled operations (automated tasks). These are never "done" — their recurrence is the point.
>
> When a tripwire fires and creates discrete work, that work comes here as a project. When a project reveals a need for ongoing monitoring, the monitoring item goes to OPERATIONS.md. Items with "Moved to OPERATIONS.md" redirect stubs were migrated from this file — git history preserves their original content.
>
> **Anticipatory items are valid.** Not all backlog items need a triggered condition. Three valid reasons to keep an item: need it now (active problem), plan to use soon (near-future need), anticipate needing later (want it ready when the time comes). When reviewing the backlog, present items with summaries so the user can decide — don't assume items without fired triggers should be closed.
>
> **No closed/completed items in this file.** When an item is closed, remove it from this file entirely. Git commit history is the archive — commit messages document what was closed and why. Maintaining closed item lists, completed tables, or historical detail sections in a working document is redundant with version control and causes unbounded file growth. If you need closure context for a past item, use `git log --grep="backlog #N"` or search commit messages.
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

---

119. **Moved to OPERATIONS.md** → T-119 (Revised-plan-after-rejection heuristic tripwire).

78. **Moved to OPERATIONS.md** → C-078 (Governance Compliance Review cadence).

113. **Moved to OPERATIONS.md** → T-113 (Plan-stage pre-edit battery effectiveness tripwire).

112. **Moved to OPERATIONS.md** → T-112 (Q7 retroactive audit — remaining pre-Q7 US-legal labels tripwire).

111. **Moved to OPERATIONS.md** → T-111 (Post-edit review scope expansion tripwire).

110. **Moved to OPERATIONS.md** → T-110 (F-P2-01 + R-01 priority-inversion retrospective tripwire).

109. **Moved to OPERATIONS.md** → C-109 (Deferred-with-trigger cadence audit).

108. **Moved to OPERATIONS.md** → T-108 (strict_domain_check block-mode escalation tripwire).

107. **Moved to OPERATIONS.md** → T-107 (Tool/Model Appendix index tripwire).

106. **Moved to OPERATIONS.md** → T-106 (Implements: backfill tripwire).

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

---

#### 150. Semantic-retrieval false-positive — `meta-safety-transparent-limitations` matches housekeeping actions `D2 Discussion`

**Filed:** 2026-05-01 (session-142, carrying forward diagnostic notes from BACKLOG #129 close).

**What.** `evaluate_governance` semantic retrieval returns `s_series_check.principles=["meta-safety-transparent-limitations"]` for benign housekeeping actions whose text contains rule-citation language (e.g., `"per X rule"`, `"per 'no closed items' rule"`). The principle is genuinely an S-Series Bill of Rights Amendment per `documents/constitution.md` §"Framework Overview: The Constitutional Structure" + `rules-of-procedure §3.4.2/§3.4.3` (the `meta-safety-` ID prefix IS the S-Series slugifier output) — so the scanner returning a Bill of Rights principle for `s_series_check.triggered = true` is **expected behavior**, not misclassification. The FP is a relevance-threshold issue: housekeeping action text shouldn't semantically rank `meta-safety-transparent-limitations` highly enough to S-Series-promote.

**Distinct from BACKLOG #129 (closed 2026-05-01, keyword scanner FP):** different fix surface — retrieval scoring / S-Series-promotion gate, not the keyword scanner. The just-shipped sentence-level safe-context allowlist in `_detect_safety_concerns` does NOT address Path B; verified during plan #129 contrarian review (`a9b708b023588ef2f`) that the keyword-scanner fix does NOT coincidentally suppress Path B (the session-142 repro string does not contain a sentence-level safe-context leader from the allowlist).

## Reproduction (carried from #129)

**Session-142 (2026-05-01) trigger** — `evaluate_governance(planned_action="Ship BACKLOG #147 ... Remove BACKLOG #147 entry from BACKLOG.md per 'no closed items' rule")` returned ESCALATE with `s_series_check.principles=["meta-safety-transparent-limitations"]` and `safety_concerns=["Action mentions 'remove' — may require safety review"]`. The keyword `"remove"` is in ADVISORY, not CRITICAL. ADVISORY alone wouldn't escalate. But semantic retrieval ALSO returned Transparent Limitations (an S-Series Bill of Rights principle).

**Cumulative semantic re-trips:** n=1 (session-142). Watching for additional instances to confirm whether this generalizes or remains an isolated case.

## Verification during plan #129 (2026-05-01)

Verified during BACKLOG #129 plan review (subagent: coherence-auditor `a8730552c214c010f`, contrarian-reviewer `afac4381fd32e8721`) that `meta-safety-transparent-limitations` is genuinely an S-Series Bill of Rights Amendment per `constitution.md` §Framework Overview + `RoP §3.4.2/§3.4.3` — semantic retrieval is functioning as designed; the FP is a relevance-threshold issue, not a misclassification. Verified during plan #129 contrarian review round 1 (`a9b708b023588ef2f`) that the keyword-scanner fix does NOT coincidentally suppress Path B: the session-142 repro string does not contain any sentence-level safe-context leader from the allowlist; semantic-retrieval surface remains observably triggered post-fix (regression-locked by `test_evaluate_governance_field_bridging_does_not_demote` which uses similar text).

## Hypothesis

Rule-citation language ("per X rule", "per 'no closed items' rule") embeds near transparency/honesty content in the BGE-small embedding space. The semantic retrieval scoring threshold for S-Series-promotion is currently sensitive enough that this matches `meta-safety-transparent-limitations` (which itself is about epistemic honesty / "state uncertainty where it exists"). Investigation needed:
- What's the actual cosine similarity between rule-citation phrasings and Transparent Limitations content?
- Where is the S-Series-promotion threshold? Is it tunable?
- Are there false-positives on OTHER S-Series principles (Non-Maleficence, Bias Awareness) that we just haven't observed yet?

## Possible interventions (for discussion)

1. **Threshold tuning** — raise the S-Series-promotion score threshold so weak semantic matches don't promote. Risk: tunes false-negatives on real S-Series content if threshold is too aggressive.
2. **Two-stage S-Series promotion** — semantic match alone is "tentative S-Series"; promote to vetoing only when at least one other signal (CRITICAL keyword OR multiple S-Series principles in top-K) corroborates.
3. **Action-class classifier** — separate fast classifier (housekeeping vs. operational vs. authoring vs. destructive) gates whether semantic retrieval can promote to S-Series. Risk: classifier itself becomes a fix surface.
4. **Embedding-time corpus augmentation** — add anti-pattern documents to retrieval corpus that explicitly distance Transparent Limitations from rule-citation language. Risk: hard to scope without false-negatives.

## Trigger to act

ANY of:
1. Same FP class observed n≥2 in production (currently n=1 — session-142).
2. Retrieval-quality benchmark work (`tests/benchmarks/`) lands a related improvement.
3. User-directed prioritization (e.g., adopter feedback on FP friction).

## Done when

S-Series-promotion threshold or relevance gate prevents `meta-safety-transparent-limitations` (and similar floor S-Series principles) from triggering on benign housekeeping actions, AND a regression test in `tests/test_server.py::TestEvaluateGovernance` asserts the session-142 repro string no longer ESCALATEs, AND this entry is removed per "no closed items" rule.

**Why D2 Discussion (not D1 Fix):** scope unclear (4 alternatives above), evidence base n=1, fix surface different from #129. Plan mode required if/when re-opened.

**Origin.** Session-142 (2026-05-01) governance evaluation during BACKLOG #147 close authoring. Filed during BACKLOG #129 close as the Path-B-out-of-scope follow-up. Governance: `gov-08d77289210e` (BACKLOG #129 implementation arc).

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

#### 148. ~~Execution Framework — operationalization~~ CLOSED `D3 Improvement`

**Filed:** 2026-04-29 (session-139). **Closed:** 2026-05-03 (session-145). All 4 phases complete.

**What was delivered:**
- **Phase 1:** First skill (`.claude/skills/compliance-review/SKILL.md`), 8-bucket model empirically validated (§2.3), decision matrix (§3.7).
- **Phase 2:** `OPERATIONS.md` (7th memory type), 2 cadences + 12 tripwires + V-series migrated, 5 effectiveness metrics (M-001–M-005), context retention policy (§7).
- **Phase 3:** `EXECUTION-FRAMEWORK.md` restructured chronological→thematic (v1.0.0). §6 Memory Interface Contracts added. Coherence-auditor PASS (4/4).
- **Phase 4:** Scheduling mechanism assessment (CronCreate session-local, cloud routines remote), 3 scheduled operations defined (SO-001–SO-003), session-end automation deferred (no on-session-end hook), gap analysis updated.

**Remaining open items** (not blockers — tracked elsewhere):
- Storage location decision: EXECUTION-FRAMEWORK.md §11 item 1.
- Full scheduling automation: blocked by mechanism constraints (§7.2), tracked in OPERATIONS.md SO-001–SO-003.
- OPERATIONS.md documentation quality: BACKLOG #154.

**Origin.** Sessions 139–145. Governance: `gov-1ce1278cc85e`, `gov-a2d2b84d5b99`, `gov-5ba8aa3ff93b`, `gov-266235bbac6e`, `gov-9452d3f7e513`, `gov-4282d90a079e`, `gov-96960cffeec6`. See `EXECUTION-FRAMEWORK.md` §12 for design history.

---

#### 154. OPERATIONS.md documentation quality pass `D1 Docs`

**Filed:** 2026-05-03 (session-145, user request during Execution Framework plan Phase 2 execution).

**What.** Ensure OPERATIONS.md is well-documented: clear section descriptions, consistent formatting across all entries, cross-references verified, and the file's role in the project's memory taxonomy is explained for future readers and adopters. Review each section (Cadences, Tripwires, Verification Experiments, Effectiveness Metrics, Scheduled Operations) for completeness and clarity. Verify that every entry has consistent fields (trigger conditions, origin, inline audit log where applicable).

**Done when.** OPERATIONS.md passes a documentation review — all sections have clear preamble blockquotes, all entries have consistent structure, and a reader unfamiliar with the project can understand the file's purpose and navigate to any item's canonical procedure.

**Origin.** User request during session-145 Phase 2 execution.

---

#### 153. Effectiveness metrics analysis script `D1 New Capability`

**Filed:** 2026-05-03 (session-145, Execution Framework plan Phase 2 Task 2.5).

**What.** `scripts/analyze-governance-metrics.py` — automated computation of the 5 effectiveness metrics defined in OPERATIONS.md (M-001 through M-005). Currently, metrics are evaluated manually during compliance reviews. The script would parse session transcripts and hook logs to compute governance influence rate, principle citation frequency, retrieval relevance trend, S-Series trip rate, and hook denial rate.

**Trigger.** Implement when data volume warrants trend analysis: n>1000 `evaluate_governance` audit entries across sessions, OR when manual metric computation during compliance review takes >10 minutes.

**Done when.** Script exists at `scripts/analyze-governance-metrics.py`, computes all 5 OPERATIONS.md metrics, outputs a summary table consumable by compliance review.

**Origin.** Plan Phase 2 Task 2.5 deferral per contrarian finding: "Defer metrics script until data volume warrants it" (~200-500 audit entries currently, premature for trend analysis).

---

#### 134. **Moved to OPERATIONS.md** → T-134 (PR-workflow infrastructure tripwire).

---

#### 135. Bypass-envvar audit-log invariant — refactor 6 hook bypasses to shared `audit_bypass()` helper `D2 Improvement`

**Filed:** 2026-04-25 (session-127, security-auditor B2 finding from §8.3.4-self-application plan review).

**What.** Six envvars currently bypass hooks; only one (`PLAN_CONTRARIAN_SKIP_HOOK=1`) writes to a deny-log. The others (`QUALITY_GATE_SKIP=true`, `PLAN_CONTRARIAN_CONFIRMED=1`, `GOVERNANCE_SOFT_MODE=true`, `CE_SOFT_MODE=true`, `TDD_TEST_EXISTENCE_SKIP=1`) bypass silently. Cumulative bypass surface lacks observability — the maintainer (or a prompt-injected AI) can quietly disable enforcement without auditable evidence.

**Structural fix per `meta-core-systemic-thinking`.** Replace per-hook bypass logging with a shared `audit_bypass()` helper that writes a single canonical log line (timestamp, hook, env var, reason) for every bypass invocation across the 6 envvars. Pattern: `audit_bypass "$0" "QUALITY_GATE_SKIP" "user override at line N"` → appends to `~/.claude/hook-bypass-audit.log` with rotation.

**Why deferred from session-127.** Independent of the §8.3.4-self-application plan; affects 3 hook files (`pre-push-quality-gate.sh`, `pre-tool-governance-check.sh`, `pre-exit-plan-mode-gate.sh`) plus a new `lib/audit-bypass.sh` helper. D2 effort with its own scope, test surface, and propagation to title-10 §9.3.10 hook-authoring guidance.

**Scope (when implemented).**
1. Create `.claude/hooks/lib/audit-bypass.sh` with the shared helper function
2. Migrate `QUALITY_GATE_SKIP`, `GOVERNANCE_SOFT_MODE`, `CE_SOFT_MODE`, `TDD_TEST_EXISTENCE_SKIP`, `PLAN_CONTRARIAN_CONFIRMED` to use it
3. `PLAN_CONTRARIAN_SKIP_HOOK` already audit-logs; refactor to use the shared helper for consistency
4. Add a periodic V-series item in COMPLIANCE-REVIEW.md: "audit-log entries within last 30 days" — surface frequency, drift, anomalous patterns
5. Update §9.3.10 hook-authoring guidance: new hooks with bypass envvars MUST use `audit_bypass()`

**Trigger.** Next hook addition (would be the 7th hook with a bypass) OR Compliance Review #5 / #6 finding evidence of silent bypass.

**Trigger fired:** 2026-05-03 (session-140). `pre-tool-content-security.sh` shipped with `CONTENT_SECURITY_SKIP=1` bypass — 7th hook, 7th bypass envvar. This item is now eligible for implementation.

**Origin:** Session-127 push-workflow plan security review. Audit ID: `a44b7638cf3d43b52` (security-auditor B2 BLOCKER for the original 6-component proposal; downgraded to BACKLOG when the plan scope was reduced). Governance: `gov-7083d6c85ffc`.

**Done when.** All 7 bypasses use shared helper + canonical log entries + V-series item active in COMPLIANCE-REVIEW.md.

---

#### 145. **Moved to OPERATIONS.md** → T-145 (Citation-form check hardening tripwire).

---

#### 143. **Moved to OPERATIONS.md** → T-143 (OOM-gate quoted-region false-positive tripwire).

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

**Recommended approach** *(superseded — see Status (2026-04-15) block below; now ONE of two deferred candidates pending a contrarian-reviewed design spike):* Shared embedding service — a single lightweight process loads BGE-small once, other processes call it via IPC/HTTP socket. Benefits: (1) memory drops from 5× to 1× model load, (2) other 4 processes no longer need PyTorch at all (dramatic footprint reduction), (3) no accuracy tradeoffs since it's already the same model everywhere.

**Other approaches considered:**
1. Lazy unloading — saves memory between queries but adds ~2-3s latency per query burst
2. Smaller model — all-MiniLM-L6-v2 (23 MB) but lower quality; evaluated and rejected (2026-02-14, MRR 0.569 vs BGE 0.627)
3. Single unified MCP server — merge governance + CE into one process; breaking architectural change
4. Process pooling — multiple sessions share one server; MCP protocol may not support natively

**Origin:** Session 48 (2026-04-03). macOS low-memory warning with 2 concurrent sessions. Initial investigation incorrectly dismissed Activity Monitor's GB numbers as "just virtual memory" — 26 GB swap + macOS warning proved impact is real.

**Status (2026-04-25) — PHASE2_TRIGGERED FIRED, under 7-day monitoring (corrected post-coherence-audit):**

Compliance Review #5 (Check 6b.2, 2026-04-25) found `~/.context-engine/PHASE2_TRIGGERED` marker present, fired 2026-04-25 10:00:01Z. Triggers fired: T1 (steady_mb=9420 > 1.5×5800=8700 = ≥50% growth above post-Phase-2 equilibrium), T3 (peak_mb=10752 > 7500 post-Phase-2 cap), T4 (cross_process_total_mb=11544 > 8192 combined cap). Measured slope = 6948.2 MB/h over 5.88h uptime. T2 leak-rate trigger disabled per noise-floor rule (baseline_slope_mb_per_h=0).

**Initial-draft correction (caught before action):** First-pass analysis claimed baseline was still pre-Phase-2 and proposed rebasing it as the cheapest test. That was wrong. Reading `~/.context-engine/logs/phase0-baseline.txt` directly confirmed: **baseline was already recalibrated 2026-04-17** (session-109) to post-Phase-2 values (`baseline_steady_mb=5800`, `baseline_peak_mb=6700`, with T3 raised 3072→7500 in `scripts/measure-watcher-footprint.sh`). Recalibration shipped between Compliance Review #3 (which flagged the action item) and Review #4 (whose row staled-out by saying "still pending"). The 9420/10752/11544 measurements really do represent ≥50% growth above the post-Phase-2 equilibrium — this is a real signal.

**Daily measurement-log trend (`~/.context-engine/logs/phase0-measurements.log`, last 8 readings):**

| Date | steady (MB) | peak (MB) | total (MB) | Triggers |
|------|-------------|-----------|------------|----------|
| 2026-04-17 | 5939 | 6860 | 7184 | (initial post-Phase-2 cal) |
| 2026-04-18 | 5427 | 6348 | 6731 | clean |
| 2026-04-19 | 1536 | 1638 | 2829 | clean |
| 2026-04-20 | 6041 | 7372 | 7484 | clean |
| 2026-04-21 | 3788 | 4812 | 4593 | clean |
| 2026-04-22 | 152 | 152 | 2313 | clean |
| 2026-04-23 | 146 | 147 | 2377 | clean |
| 2026-04-24 | 1638 | 1843 | 3682 | clean |
| **2026-04-25** | **9420** | **10752** | **11544** | **T1+T3+T4** |

Today's spike is 1.5× the prior week peak (cross-process total). **Snapshot taken during this review (~04:30Z) via `ps aux` shows current cross-process total = 6.0 GB**, already back inside healthy post-Phase-2 range (5 ai-context-engine processes 4.6 GB + watcher 1.1 GB + 5 governance procs 0.4 GB).

**Revised cause analysis:**
1. ~~**Stale baseline thresholds.**~~ ELIMINATED. Baseline IS post-Phase-2 (5800/6700, recalibrated 2026-04-17).
2. **Workload variance.** **STRONGEST HYPOTHESIS.** Daily 04:00 measurement caught a peak-concurrent-session moment (e.g., 2× Claude Code + 2× Claude Desktop + index-rebuild + multiple query batches overlapping). Week range was 2.3–7.5 GB; today's 11.5 GB spike is plausible for transient peak overlap before the 12h self-restart flush. Current snapshot 6.0 GB consistent with healthy state.
3. **Phase 2 regression.** Unlikely but not refuted by a single spike — would need 2+ T1 fires within a short window or a process found loading torch when it shouldn't (e.g., IPC client crash → silent fallback to in-process load).

**Marker NOT cleared** — preserves measurement evidence for the 7-day re-test per `meta-core-systemic-thinking` (do not remove obstacle by removing evidence) + `meta-quality-verification-validation` (one spike is not a confirmed signal; need re-test to distinguish workload variance from regression).

**Action plan (current recommendation):**
- (a) **Monitor next 7 daily measurements** (2026-04-26 through 2026-05-02). If T1 stays clear (steady_mb < 8700) on ≥6/7 days, **clear marker as workload-variance confirmed** + record outcome here.
- (b) **If T1 re-fires within 7 days**, escalate to cause (3) regression investigation: run `ps aux | grep -iE '(governance|context-engine|embedding)'` at the moment of fire (cron-augment the measurement script) + per-process torch-loading audit via `lsof -p <pid> | grep -i torch` to confirm whether any process is loading torch outside the embedding daemon. Schedule contrarian-reviewed design spike if regression confirmed.
- (c) **Original spike option preserved**: if (3) confirmed, schedule shared embedding service v2 OR direct optimum + tokenizers rewrite per the original Status (2026-04-15) deferred spike.

**Status (2026-05-02) — 7-day monitor CLEAR, marker cleared, workload-variance confirmed:**

7-day monitor window (2026-04-26 through 2026-05-02) completed per BACKLOG #137 close-out procedure. T1 (primary steady-state regression indicator, threshold 8700 MB) fired **0 of 7 days** — clean the entire window. T3/T4 fired on 2 of 7 days (path (c) in decision tree — ambiguous case surfaced to user per procedure):

| Date | steady (MB) | peak (MB) | total (MB) | Triggers |
|------|-------------|-----------|------------|----------|
| 2026-04-26 | 4812 | 5632 | 8416 | T4 |
| 2026-04-27 | 3686 | 4505 | 4340 | clean |
| 2026-04-28 | 8192 | 9113 | 10203 | T3+T4 |
| 2026-04-29 | 1536 | 1536 | 3552 | clean |
| 2026-04-30 | 1536 | 2150 | 3463 | clean |
| 2026-05-01 | 154 | 154 | 1490 | clean |
| 2026-05-02 | 148 | 148 | 2179 | clean |

Pattern: episodic spikes correlating with heavy concurrent sessions (multiple Claude Code + Desktop instances), followed by 4 consecutive clean days with final 2 near-idle (148-154 MB steady). The 04-28 spike (steady=8192, peak=9113, total=10203) matches the same workload-variance profile as the original 04-25 fire — high concurrent usage at measurement time, not a leak or architectural regression. T1 clean across entire window confirms steady-state memory is within post-Phase-2 equilibrium.

**Decision:** User reviewed measurements and confirmed workload-variance hypothesis. `~/.context-engine/PHASE2_TRIGGERED` marker cleared 2026-05-02. Ongoing daily measurement plist continues — marker will re-fire automatically if thresholds are exceeded again. Per BACKLOG #137 close-out procedure, COMPLIANCE-REVIEW.md Check 6b.2 row 5 recorded. Governance: `gov-912600878510`.

**Status (2026-04-16) — Phase 2 COMPLETE, verified in session-108:**

Phase 2 (shared embedding service via IPC) shipped in sessions 106-108. Commits `07a1e54`–`ec4ea55` (Steps 1-5) + verification in session-108. Results:
- Governance servers: **85 MB** phys_footprint (down from ~800 MB = **~715 MB saved per instance**)
- Model load time: **80ms** via IPC (was ~9s cold start = **112x improvement**)
- MRR: method=0.646, principle=0.750 — all pass regression thresholds
- IPC confirmed: "Using embedding server (IPC)" in logs for both encoding and reranking
- CE servers: 552-683 MB (tree-sitter + index data, no torch loaded)
- Total across all processes: ~4.0 GB (daemon 2.6G + 2× Desktop + 2× Code servers)

**Latent issues found during verification:**
1. `extractor.py:106-108` calls `get_sentence_embedding_dimension()` on `self.model` which could be `EmbeddingClient` (no such method). Crashes index rebuilds when daemon running.
2. 20 embedding-mock tests fail when daemon running — `EmbeddingClient.available()` returns True, intercepting mock patches. Need `AI_CONTEXT_ENGINE_EMBED_SOCKET=none` in test env or mock the client.

Forcing functions remain active (daily plist + deny log + calendar trigger 2026-06-15) as a safety net.

**Status (2026-04-15) — explored routes, shipped mitigations, design spike forcing function:**

**Explored route (NOT shipped):** ONNX backend via `sentence-transformers` native `backend="onnx"` parameter + `optimum[onnxruntime]` dependency. 10-file plumbing diff built and preserved at `staging/onnx-backend-attempt-2026-04-15.patch` + explainer at `staging/onnx-backend-attempt-2026-04-15.md`. Rejected after envelope math: `sentence-transformers` 5.2.0 imports `torch` unconditionally at module load via the `transformers` hard dependency (verified empirically at `sentence_transformers/SentenceTransformer.py:17,25-26` and `Transformer.py:17-18`). The `backend` kwarg only picks model *weights* at inference time, not module init. Savings: BGE-small ≈130 MB + reranker ≈90 MB, 50% savings × 5 processes = **~550 MB** — roughly **2% of the 27 GB symptom**. The other ~98% is torch/transformers runtime duplication (~500 MB–1 GB × 5 processes = 2.5–5 GB per ONNX investigation), which a weights-only swap cannot address — this is why the real fix must eliminate the runtime duplication (Remaining candidates below), not just the weight duplication. Shipping ONNX under the #49 banner would have violated `meta-safety-transparent-limitations`. Two independent contrarian-reviewer passes on 2026-04-15 validated rejection.

**Shipped (independent of the real #49 fix):**
1. **Structural pre-test OOM prevention gate** at `.claude/hooks/pre-test-oom-gate.sh` — PreToolUse hook on Bash that blocks bare `pytest tests/` invocations when the watcher daemon is alive OR other torch-holding Python processes are detected. Prevents the class of OOM that hit this box on 2026-04-15 from recurring via AI-initiated Bash. **23 unit tests** at `tests/test_pre_test_oom_gate_hook.py` (10 test classes; one parametrized). Bypasses: `PYTEST_ALLOW_HEAVY=1` (semantic: "I intend the heavy suite"), `PYTEST_SKIP_OOM_GATE=1` (structural: "the gate itself is broken"). Expected-workflow escape hatch: `pytest tests/ -v -m "not slow"`. LEARNING-LOG precedent: "Hard-Mode Hooks Prove Deterministic Enforcement Works" (2026-02-28).
2. **Indexer stale-default correctness fix** (commit `b702296`) — unrelated latent bug discovered during investigation: `Indexer.__init__` had stale defaults `nomic-ai/nomic-embed-text-v1.5`/768d from an evaluated-but-never-deployed trial. Production used `BAAI/bge-small-en-v1.5`/384d everywhere else via config overrides. Committed independently.

**Remaining (design spike required, deferred to a dedicated session):** Two candidates for the real per-process fix:
1. **Shared embedding service via IPC** (original backlog recommendation above). Single process owns the model; others call via Unix socket / HTTP. Much larger surface area — process lifecycle, serialization, startup ordering, crash recovery.
2. **Direct `optimum.onnxruntime.ORTModelForFeatureExtraction` + `tokenizers`** layer that skips the `transformers` import entirely, eliminating the torch/transformers runtime duplication. Smaller surface than option 1 (~300–500 lines replacing `retrieval.py` + `extractor.py` + `context_engine/indexer.py` embedder code + reranker replacement) but reimplements pooling/normalization and loses `SentenceTransformer.encode()` + `CrossEncoder` affordances.

Decide via contrarian-reviewed design spike, NOT implementation-first. Both options touch critical code paths.

**Forcing function — anti-procrastination (per `meta-core-systemic-thinking`):** The shipped OOM gate removes the acute pain of this ticket, which is EXACTLY why the real fix would otherwise get forgotten (forward-continuation-bias trap per LEARNING-LOG). The design spike acceptance criterion is **whichever comes first**:

- **Activity trigger:** the pre-test OOM gate denies ≥3 pytest invocations in practice. Each deny appends to `~/.context-engine/oom-gate-denies.log` (format: `<ts> deny daemon_alive=<bool> torch_procs=<n> cmd=<cmd>`). **Current automation state (2026-04-15):** the deny log is written on every deny (verified by `tests/test_pre_test_oom_gate_hook.py::TestDenyLogSideEffect`), but no agent currently reads it automatically. The activity trigger fires when a future session explicitly greps the log at session start — either a human notices, or a future enhancement teaches the orchestrator/coherence-auditor to include this check. **Instruction for the next session at `count >= 3`:** re-enter this backlog item, re-read the ONNX investigation artifact, schedule a contrarian-reviewed design spike. Log location is stable; the promise is that a future reader will find it, not that an agent will find it unprompted. Treat this as the honest floor of "check a file" rather than a background daemon.
- **Capacity trigger:** any proposal to add a 6th torch-loading process (new MCP server, second watcher variant, worker pool) blocks on this spike first. The symptom math gets proportionally worse with more processes; adding another before the real fix would be negligent.
- **Calendar trigger:** 2026-06-15 unconditional review. If neither activity nor capacity has fired by then, re-enter the backlog item for fresh contrarian review and concrete spike scheduling.
- **Phase 0 outcome trigger (measurement-automated, added 2026-04-15):** the second launchd plist `com.ai-governance.context-engine-measure` runs `scripts/measure-watcher-footprint.sh` daily at 04:00 and evaluates four independent thresholds against the baseline captured in `~/.context-engine/logs/phase0-baseline.txt`. If any threshold is exceeded, the script writes `~/.context-engine/PHASE2_TRIGGERED` as a boolean marker. The four thresholds:
  1. **Steady-state drop:** post-Phase-0 steady phys_footprint must be < 60% of baseline (≥40% reduction). Baseline 4.1 GB → must drop below ~2.5 GB.
  2. **Leak rate (measurement-derived, per Contrarian Finding 3):** post-Phase-0 slope must be ≤ 50% of the `baseline_slope_mb_per_h` captured during a fresh-daemon 2h sample. If baseline slope is <8 MB/hr, this trigger is disabled (noise floor).
  3. **Session peak:** any 24h-window peak phys_footprint must be < 3.0 GB.
  4. **Cross-process total (cause #2 direct):** summed phys_footprint across all `context-engine-watcher` + `ai_governance_mcp` + `ai-context-engine` processes must be < 8.0 GB. Phase 0 cannot by construction fix model duplication, so this trigger routes straight to Phase 2 when duplication dominates.

  Check 6b.2 in `workflows/COMPLIANCE-REVIEW.md` reads the marker file as a boolean (`test -f PHASE2_TRIGGERED`). When the marker is present, re-enter this backlog item and schedule the design spike. Clear the marker after escalation: `rm ~/.context-engine/PHASE2_TRIGGERED`. This is fully structural (launchd runs, script evaluates, marker is written) — no human memory required for evaluation, though someone still has to run the compliance review to read it.

The capacity, calendar, and Phase 0 outcome triggers are fully structural (no human memory required — they're encoded as rules future sessions will read, and in the case of Phase 0 outcome, evaluated automatically by a scheduled job). The activity trigger is "check a file" rather than "remember a rule" — the deny log write is automatic and tested, but a human or future enhancement must read it. Honest limitation documented above; this is a floor, not a ceiling, on the forcing function.

**Relevant files:**
- Hook: `.claude/hooks/pre-test-oom-gate.sh`
- Hook tests: `tests/test_pre_test_oom_gate_hook.py`
- Deny log: `~/.context-engine/oom-gate-denies.log`
- ONNX investigation artifact: `staging/onnx-backend-attempt-2026-04-15.{patch,md}`
- Incident entry: `LEARNING-LOG.md` — "Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)"

#### 19. Content-Level Security Enforcement — partial-close `D2 Improvement` *(Rampart tripwire portion → OPERATIONS.md T-019)*

**Shipped (2026-05-03, session-143).** Two-layer credential-access gate:
- **Layer 1 (Read deny rules):** Already present in user-level `~/.claude/settings.json` — blocks `Read(~/.ssh/**)`, `Read(~/.aws/credentials)`, `Read(~/.gnupg/**)`, `Read(~/.netrc)`, `Read(**/.env)`, `Read(**/.env.*)`, `Read(~/.docker/config.json)`, `Read(~/.kube/config)`, `Read(~/.npmrc)`.
- **Layer 2 (Custom hook):** `.claude/hooks/pre-tool-content-security.sh` — blocks Bash commands accessing the same credential paths (cat, head, cp, scp, curl, base64, etc.) plus bare directory references (tar ~/.ssh, ls ~/.aws). 44 tests in `tests/test_content_security_hook.py`. Positioned after governance hooks in PreToolUse array.

**Gap addressed:** Claude Code can read files outside the project directory without prompting. `~/.ssh/id_rsa` and `~/.aws/credentials` were accessible via both the Read tool and Bash commands. Layer 1 + Layer 2 close both paths.

**Known limitation:** Path traversal bypass (e.g., `cat /tmp/../../home/user/.ssh/id_rsa`) evades string-matching. Fixing requires path canonicalization (realpath), significant scope expansion. Acceptable for defense-in-depth: the threat model is naive AI access, not adversarial evasion of its own hooks.

**Not shipped (deferred to Rampart tripwire):** Path canonicalization, network exfiltration filtering, output secret scanning, comprehensive OWASP coverage. Contrarian review (`a3c863d49f04b447d`, REVISIT verdict) correctly identified full Rampart integration as disproportionate to current attack surface (zero credential files in repo, zero outbound network calls, public code, single developer).

**Rampart tripwire — reopen when ANY fires:**
1. Project adds credential files (`.env`, API keys, service accounts)
2. External contributors appear (≥1 external issue/PR)
3. Rampart reaches 1.0 with broader adoption (500+ stars, multiple contributing orgs)
4. A credential leak occurs that Layer 1+2 would not have caught

**Rampart landscape (as of 2026-05-03):** github.com/peg/rampart v0.9.22, Apache 2.0, Go binary, 67 stars, 777 commits. Native Claude Code PreToolUse integration. Alternatives: Microsoft Agent Governance Toolkit (OWASP-complete), Meta LlamaFirewall (guardrail framework).

**Origin:** Session-48 (2026-04-04) original filing. Session-143 (2026-05-03) research + contrarian review + proportional implementation. Plan: `~/.claude/plans/review-with-subagents-to-sorted-bear.md`. Governance: `gov-20465bfec14a`.

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

