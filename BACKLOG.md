# Backlog

**Memory Type:** Prospective (intentions)
**Lifecycle:** Items are added when discovered, removed when implemented or abandoned. Git commit history is the archive for closed items (`git log --grep="backlog #N"`).

> **Staleness rule (2026-04-14):** Discussion items with no activity for 90+ days are flagged for review during the next compliance review (workflows/COMPLIANCE-REVIEW.md Check 8). User decides: keep, close, or reframe.

---

### Open Backlog

> **Backlog Philosophy (2026-03-30, updated 2026-04-15):** Items fall into two categories: (1) **Active** — fix now or implement soon, (2) **Deferred/Future — Discussion** — needs fleshing out before deciding to implement or drop. New user-requested items default to Discussion unless they emerge from implementation (e.g., template fixes discovered during audit). Existing shipped work with known issues gets fixed now — don't defer fixes to "next time we touch it."
>
> **Anticipatory items are valid.** Not all backlog items need a triggered condition. Three valid reasons to keep an item: need it now (active problem), plan to use soon (near-future need), anticipate needing later (want it ready when the time comes). When reviewing the backlog, present items with summaries so the user can decide — don't assume items without fired triggers should be closed.
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

117. **Plans must include a plain-English summary for human review** `D1 Improvement`

**What:** User feedback this session (2026-04-21): *"Moving forward I need an easy to read summary of the plan. Can you show the plan again with the clear summary at the end and I can determine if I will approve."* The pattern was effective — added a plain-English summary section at the end of the Task 4 plan, user could engage with material choices (scope trade-offs, what's NOT being done, what needs their decision) without wading through the technical detail (principle citations, pattern references, file-by-file edit lists). Task 5 proactively included the same section; worked the same way.

**Problem:** Plans written in plan mode optimize for AI execution guidance — dense technical detail, principle IDs, pattern cross-references, file manifests. This serves execution but makes human review expensive. The human sits at the approval decision but has to extract the decision points from the execution detail. Without a consistent plain-English layer, users either ask for the summary (friction) or approve without full comprehension (risk).

**Proposed approach (needs discussion to pick home):**
- **Option A — Plan template only:** Extend `.claude/plan-template.md` with a mandatory "Plain-English Summary" section at end. Template enforcement is structural (plan-mode flow reads the template).
- **Option B — Behavioral floor:** Add to CLAUDE.md Behavioral Floor a "plans MUST include a plain-English summary of what's changing, the one judgment call, and trade-offs." Ambient pressure, may not consistently trigger.
- **Option C — Plan subagent:** Encode in `documents/agents/Plan.md` (if exists) or the equivalent. Only fires when Plan subagent is used.
- **Option D — Combination:** SSOT in plan template; cross-ref from CLAUDE.md + Plan agent.

**Summary content spec (for whichever home is chosen):**
- What's changing (plain verbs, no jargon)
- The one material decision the user is being asked to approve
- The trade-off (why this over alternatives, in 1-2 sentences)
- What's deliberately NOT being done (explicit non-goals)
- Length: ~5-10 short paragraphs, enough to decide, not exhaustive
- Placement: end of plan so AI execution context (file paths, patterns, principles) is on top, human scrolls to bottom

**Why D1 Improvement:** Docs-only change once approach chosen. Scope ≤2 files depending on Option.

**Re-open prerequisites:** None — ready to plan. User direction in this filing IS the consumer evidence per Ground-Truth rule.

**Origin:** Session-121 user-requested pattern (2026-04-21 Task 4 review + Task 5 proactive application). Filed at user's explicit request 2026-04-22.

116. **PreToolUse hook on ExitPlanMode enforces contrarian-reviewer invocation** `D2 New Capability`

**What:** V-004 (Contrarian review compliance before ExitPlanMode) escalation threshold met at Governance Compliance Review #4 (2026-04-22). Evidence: 3 sessions across the 5-session measurement window required user reminder to invoke contrarian-reviewer before ExitPlanMode (baseline 2026-04-08 session 1, session 3 2026-04-13, session 5 2026-04-21 Task 4). Plan template gate text ("DO NOT populate Recommended Approach until contrarian section has content") is advisory and non-deterministic.

**Prescribed escalation per V-004 disposition:** PreToolUse hook on ExitPlanMode that requires contrarian-reviewer transcript match before allowing plan approval. Similar structural-enforcement pattern to the pre-test-oom-gate hook (session-105) and pre-push-quality-gate hook (session-107).

**Scope sketch:** (1) new `.claude/hooks/pre-exit-plan-mode-contrarian-check.sh` or extension of existing pre-push-quality-gate; (2) scans transcript for `contrarian-reviewer` invocation after most recent plan-mode entry; (3) denies ExitPlanMode (exit 2) if absent; (4) documented bypass env var for contrarian-skip with rationale (e.g., `PLAN_CONTRARIAN_SKIP=true`); (5) unit tests following pre-test-oom-gate pattern (mock fake ExitPlanMode invocation; assert exit 2 when contrarian absent, exit 0 when present).

**Why D2 not D1:** Hook authoring with full ai-governance/systemic-thinking (pre-edit battery + contrarian review per LEARNING-LOG 2026-04-19 + CFR §9.3.10 Hook Implementation Prerequisites recipe) + unit tests. Estimated 1-2 sessions. Plan mode appropriate.

**Re-open prerequisites:** None — threshold already met; ready to plan.

**Origin:** Compliance Review #4 (2026-04-22), V-004 session 5 finding (session-121 Task 4 required user reminder). Convergent with CFR §9.3.10 Hook Implementation Prerequisites recipe canonicalized session-121 Task 5 — the recipe would be applied to the new hook.

115. **Add body-header + pin sync to CFR PATCH authoring template** `D1 Docs`

**What:** Body-header version drift (e.g., `documents/title-10-ai-coding-cfr.md:12` was `**Version:** 2.36.1` while frontmatter was `v2.38.4`) has been a recurring post-commit finding across sessions 117, 119, 121 Task 4, 121 Task 5. Coherence auditor ruling (session-121 Task 5 post-commit, agent `a00a1df2db9dfdd88`): *"body-header staleness is a recurring class of drift. Rather than fix once, consider a PATCH-authoring checklist item."* Similarly, `<document_versions>` pin drift in `documents/ai-instructions.md` has repeated across v2.7.1, v2.7.2, v2.7.3 (sessions 119, 119, 121).

**Structural fix proposal:** Add to `workflows/COMPLETION-CHECKLIST.md` "Content changes (governance documents)" tier a new checklist item: *"When bumping CFR frontmatter version, also update (a) body-header Version + Effective Date lines, (b) `ai-instructions.md <document_versions>` pin for that CFR, (c) SESSION-STATE Quick Reference content row. Verify all four surfaces move together before commit."*

**Scope:** 1 file (`workflows/COMPLETION-CHECKLIST.md`), ~1 checklist item added. ~15 minutes.

**Re-open trigger:** Next CFR PATCH/MINOR/MAJOR bump is the natural trigger — fold in while editing the CFR Version History to avoid stacking bumps (per user `feedback_unpushed_version_bumps` memory).

**Why not fix-now (session-121):** Current session already amended commit `73e8d07` with two convergent propagation fixes; adding a third surface (COMPLETION-CHECKLIST meta-fix) is proportional-rigor territory — next PATCH is the natural fold-in.

**Origin:** Session-121 Task 5 post-commit double-check convergent finding (contrarian `a21558a490dfcd8af` + coherence `a00a1df2db9dfdd88`). Recurring pattern observation per `meta-core-systemic-thinking`.

78. **Governance Compliance Review — ongoing, next review due ~2026-04-27** `D1 Maintenance` (every 10-15 calendar days). Reviews #1 (2026-04-13), #2 (2026-04-14), and #3 (2026-04-17) complete. See workflows/COMPLIANCE-REVIEW.md. Event triggers: hook/CLAUDE.md/tiers.json modification. **Recurring item by design** — never "done"; the cadence is the point. Structural: `D1 Maintenance` item that remains Active permanently.

113. **Plan-stage pre-edit battery effectiveness pattern — "4-of-4 catches suggest first-draft plans are systematically under-rigored"** `D2 Discussion`

**What:** Every pre-edit 3-agent battery run on a first-draft plan (Cohorts 2, 3, 4, 5) caught a major pivot:
- Cohort 2 v1 → Path B alternative discovered (Risk Mit ↔ Non-Mal Path B vs Path A merge)
- Cohort 3 v1 → F-P2-13 Path B (Preamble purpose-surface, not claim-surface)
- Cohort 4 v1 → Phase 4b Q7 FAIL killed the whole phase's central work
- Cohort 5 v1 → F-P2-02 Preamble location wrong, F-P2-03 Q7 FAIL, "100% milestone" framing dishonest

**Contrarian's reframing (cross-cohort meta-review):** *"4-of-4 pre-edit batteries catching big pivots is not validation of 'run the battery' — it's evidence that **first-draft plans are systematically under-rigored**, and the battery is compensating. The fix is better first-draft plan quality, not more trust that the battery will catch it."*

**Open questions:**
1. Is there a checklist or rule we could add to the first-draft planning process that would catch the pattern of issues the battery consistently catches? (E.g., "always run Q7 on new labels," "always verify line anchors," "always spec schema edge cases.")
2. Would splitting the plan-writing agent's scope (e.g., plan + adversarial self-critique before exit) reduce the rate?
3. Is the 4-of-4 rate actually a problem — maybe plans SHOULD be drafts that get revised, and the battery is the right mechanism?
4. Steel-man: plans → batteries → revised plans is a deliberate cheap-then-expensive design. Eliminating the first-draft/battery gap may trade "quick iteration with review" for "slow perfect first drafts" — worse overall.

**Possible interventions (for discussion, not yet adopted):**
- Add a "pre-battery self-checklist" to the plan template with items like: "Did you apply Q7 to any new labels?" "Did you verify all cited line anchors?" "Did you spec edge cases for new schema fields?"
- Require plan-writing agent to invoke adversarial self-critique before exit (mirror contrarian in the drafting loop).
- Accept the pattern as deliberate and document the "cheap draft, expensive battery" design choice explicitly.

**Re-open prerequisites:**
1. Evidence base N≥6 cohorts (we have 4; need 2 more to confirm pattern or see it drop).
2. OR: an adopter reports a failed plan that the battery didn't catch (which would reframe the question to "batteries are also insufficient").

**Why deferred (not D1 Fix):** Evidence base of 4 is suggestive but not conclusive per §7.8 proportional rigor. Implementing any intervention prematurely could degrade the current working pattern. Worth observation, not yet worth structural change.

**Origin:** Cross-cohort meta-review (session-119, 2026-04-20, contrarian agent `afe0ecba1e867d95d`) arc-level observation. Filed per user follow-up request that all contrarian META findings become actionable BACKLOG items, not just prose in Historical Amendments.

112. **Q7 comprehensive retroactive audit — remaining pre-Q7 US-legal labels** `D2 Discussion`

**What:** Cross-cohort meta-remediation PATCH (v5.0.7) retroactively applied Q7 Semantic-Label Risk to 2 of ~6 pre-Q7 US-legal labels flagged by contrarian (Structural Enforcement, Secondary Authority — both PASS). Selective retroactive application creates new drift: some pre-Q7 labels Q7-checked, others not. A principled retroactive pass would cover all of them.

**Labels still unchecked (not yet run through Q7):**
1. **"Supremacy Clause"** (`constitution.md` Operative Hierarchy section) — enforcement mechanism = §9.3.1 Truth Source Hierarchy + §9.8.5 bright-line. Expected PASS.
2. **"Elastic Clause"** (`rules-of-procedure §8.7`) — derived authority for novel situations. Enforcement mechanism = ? (may be Q7 FAIL — is this a specific operationalization, or aspirational prose?)
3. **"Full Faith and Credit"** (`rules-of-procedure §9.7.6`) — cross-domain output recognition. Enforcement mechanism = retrieval engine crosses domains, but is that what the clause names? Partial/unclear.
4. **"Jacobson v. Massachusetts pattern"** (cited in `constitution.md:80` Preamble classification) — Preamble as interpretive tiebreaker. Enforcement mechanism = Admission Test tiebreaker rule. Likely PASS.
5. **"Bill of Rights" (generic label)** — S-Series naming. Partially covered by F-P2-04 Q7 PASS (Cohort 5 Session 5-2), but that PASS was narrowly scoped to S-Series US-Constitutional PROSE framing, not the "Bill of Rights" label itself.
6. **"Impeachment fast-path"** (`rules-of-procedure §9.6.3`) — MAJOR version bump workflow. Enforcement mechanism = §9.6.3 text itself. Likely PASS.

**Re-open prerequisites:**
1. Sufficient session capacity for ~30-60 min focused Q7 pass on the 4-6 remaining labels.
2. OR: a new finding that one of these labels had operational mismatch harm.

**Why deferred (not D1 Fix):** Proportional rigor — contrarian flagged the pattern (selective retroactive) not specific labels beyond the two I addressed. Expected outcome is 4-5 PASSes + possibly 1 FAIL (Elastic Clause looks most at risk). Not urgent but worth completing so the framework can say "Q7 applied to all pre-Q7 US-legal labels" honestly rather than "applied to the 2 flagged by contrarian."

**Origin:** User follow-up to cross-cohort meta-review (session-119, 2026-04-20): "Review your findings again and see if there are any other gaps." Systemic-thinking observation: if Q7 retroactive is a principle, it should be applied comprehensively, not selectively. Filed for eventual completion.

111. **Post-edit review scope expansion — eliminate the "post-commit always finds something" pattern** `D2 Improvement`

**What:** Every single cohort (2, 3, 4-Phase-4a, 5) produced a post-commit PATCH because the post-commit 3-agent battery consistently found drift the post-edit battery missed. 100% rate across 4 cohorts. The contrarian's cross-cohort meta-review reframed this: it's not "post-commit pattern works well" — it's "post-edit scope is structurally gapped." Same class of drift every time: adopter-facing surface propagation (API.md schemas, ai-instructions `<document_versions>` pins, parallel tables in title-* CFRs, user-facing prose in README/CLAUDE.md).

**The structural gap (contrarian finding):** post-edit coherence-auditor runs against the explicit edit inventory the plan declared. Files NOT in the plan's explicit inventory — adopter-facing docs, parallel surfaces, version pins — systematically fall outside post-edit scope. The gap is the plan's inventory, not the battery's execution.

**Proposed fix (discussion needed before implementation):**
1. Expand the coherence-auditor agent's default scope to explicitly include an "adopter-facing surfaces" checklist regardless of plan inventory: `README.md`, `CLAUDE.md`, `API.md`, `SECURITY.md`, `documents/ai-instructions.md` `<document_versions>` block, and parallel tables in title-* CFR files.
2. Update `workflows/COMPLETION-CHECKLIST.md` Content-Changes tier: add "adopter-facing surface audit" item that runs before commit, not after.
3. Update `documents/agents/coherence-auditor.md` scope guidance so every post-edit coherence audit covers these surfaces by default.
4. Decision: Does this absorb the post-commit battery into post-edit scope (dropping the distinct post-commit pass), or does post-commit remain as a deliberate second look? Argue both.

**Alternative (steel-manned):** accept the pattern as-is. Post-commit catches are cheap (1-PATCH commit per cohort). Trying to eliminate them via post-edit expansion may just shift the gap elsewhere — if the post-edit scope becomes too wide, it loses focus on the actual changes. "Two passes at different scopes" is arguably the right design, not a defect.

**Re-open prerequisites:**
1. At least 2 more cohorts of data (if Cohort 6 + 7 post-commit batteries find the *same class* of drift, the pattern is confirmed structural).
2. OR: an adopter report of post-commit drift causing user-visible harm (not just cosmetic).

**Why deferred (not D1 Fix):** The pattern is low-severity — post-commit PATCHes have consistently been small, shipped within same session. No adopter harm. Restructuring the post-edit scope requires careful design to avoid trading one gap for another. Evidence base (n=4) is suggestive but not yet conclusive per §7.8 proportional rigor.

**Origin:** Cross-cohort meta-review (session-119, 2026-04-20, contrarian agent `afe0ecba1e867d95d`): *"The post-commit pattern is a structural gap, not a feature. 100% rate means post-edit scope is systematically gapped, not that the post-commit pattern is strong."*

110. **F-P2-01 + R-01 priority-inversion retrospective — "critical finding closed by claim-softening, not measurement"** `D2 Discussion`

**What:** The 2026-04-18 self-review identified **1 Critical finding** (F-P2-01): Declaration's value-proposition claim was unfalsifiable — framework measures *mechanism* (retrieval MRR, hook compliance) but Declaration claimed *outcome* (AI quality improvement). Cohort 1 closed F-P2-01 by rewriting the Declaration and README to make humbler claims (reframing the Declaration as a purpose statement, not a results claim). This closed the finding on the text side.

**Contrarian's cross-cohort critique:** The *structural* fix for F-P2-01 is the outcome benchmark (tracked separately as BACKLOG #22 Governance Effectiveness Measurement — still in Discussion state). The arc shipped Cohorts 1-5 without R-01. Contrarian framing: *"A rational actor optimizing for framework defensibility would have shipped R-01 before Cohort 2 and let the data re-triage everything downstream. The arc inverted the priority — did the cheap, legible editorial work first and left the expensive, diagnostic work for 'Sprint 1' that hasn't started."*

**Open questions:**
1. Is the claim-softening closure sufficient (honest scope reduction = real fix) OR insufficient (we still owe the measurement)?
2. Does BACKLOG #22's existing "Discussion" state cover the retrospective, or does F-P2-01 need its own standing item distinct from #22?
3. If R-01 ships and shows no measurable framework effectiveness, how many of the 28 closed findings get retroactively re-severity'd? (Contrarian: "9 of 28 closed findings become retroactively questionable.")
4. Is there a structural guardrail for "don't close Critical findings via claim-softening without also shipping the measurement that would validate the softening" — e.g., an Admission Test question or §9.8.1 addition?

**Re-open prerequisites:**
1. R-01 outcome benchmark ships (or is declared explicitly unmeasurable per BACKLOG #22 "may conclude some aspects aren't measurable" option), AND
2. Retrospective conducted on whether any of the 28 closed findings need re-severity based on measurement results.

**Why deferred (not D1 Fix):** This is a product-level retrospective, not a framework patch. Fixing requires either shipping R-01 (large work tracked at #22) or making a formal decision that measurement is out of scope. Both are multi-week commitments, not same-session fixes.

**Origin:** Cross-cohort meta-review (session-119, 2026-04-20, contrarian agent `afe0ecba1e867d95d`): *"F-P2-01 (Critical) closed by claim-softening, not measurement. R-01 outcome benchmark still unshipped. Arc inverted priority."*

**Relationship to BACKLOG #22:** Adjacent but distinct. #22 = "can we measure effectiveness?" (design question). This item = "did the arc's execution order respect the claim-verification relationship?" (retrospective question). Both need resolution before the self-review loop is fully trustworthy.

109. **Deferred-with-trigger cadence audit — re-read every ~30 days** `D1 Maintenance` (recurring — never "done")

**What:** Several review findings across Cohorts 4-5 were deferred with "re-open when consumer emerges" triggers but no owner or cadence to check whether conditions are met. Without a watch-list, principled deferrals quietly calcify into silent abandonment. This item establishes a recurring cadence to audit the deferred items — mirrors BACKLOG #78's Governance Compliance Review pattern.

**Deferred items tracked (as of 2026-04-20):**
- **BACKLOG #41 / #43 / #44 / #46** — Reference library auto-staging, progressive disclosure, auto-maturity, stack metadata (tracked as F-P1-07 deferral from Cohort 5).
- **BACKLOG #58 / #59 / #60** — UBDA adopter-drift review items (tracked as F-P2-07 deferral from Cohort 5).
- **BACKLOG #106** — Cohort 4 Phase 4b `Implements:` backfill (F-P1-04, prerequisites: consumer + Q7 remediation).
- **BACKLOG #107** — F-C-06 Tool/Model Appendix index (prerequisites: adopter-discoverability consumer OR appendix count >15).
- **BACKLOG #108** — F-C-04 Phase-2 `strict_domain_check` block-mode (prerequisites: observed adopter harm OR CI surface wants enforcement).
- **BACKLOG #110** — F-P2-01 + R-01 priority-inversion retrospective (prerequisites: R-01 ships OR declared unmeasurable + retrospective on 28 closed findings).
- **BACKLOG #111** — Post-edit review scope expansion (prerequisites: 2+ more cohorts of evidence OR adopter report of post-commit drift harm).
- **BACKLOG #112** — Q7 comprehensive retroactive audit for remaining pre-Q7 US-legal labels (prerequisites: session capacity OR new finding of operational mismatch).
- **BACKLOG #113** — Plan-stage battery effectiveness pattern (prerequisites: N≥6 cohorts of evidence OR adopter-reported plan failure).
- **F-P2-03 accepted residual** — FM-code retrofit (Cohort 5, prerequisites: consumer + parser implementation).

**Cadence:** every ~30 calendar days, OR whenever a session's work plausibly satisfies a trigger (e.g., reference-library consumer being built triggers #41/#43/#44/#46 re-read).

**Audit procedure:**
1. For each item, re-read the trigger prerequisites literally.
2. Answer "still deferred?" in ≤1 sentence per item.
3. If ANY trigger met: promote from `D3 Deferred` to `D2 New Capability` (or `D1 Fix` if urgent) and assign actual work.
4. If no triggers met: record audit date inline ("Reviewed 2026-MM-DD — still deferred, no triggers fired.").
5. Update this entry's inline audit log with results.

**Why D1 Maintenance (recurring):** Same rationale as BACKLOG #78 — the item is "never done" because the cadence IS the value. Each audit costs ≤15 min but prevents ~10-hour rework cycles when a trigger was missed for months.

**Origin:** Cross-cohort meta-review (session-119, 2026-04-20) contrarian finding (`afe0ecba1e867d95d`): "Re-open triggers on F-P1-04, F-P1-07, F-P2-07 are passive and will never fire on their own. 12 months from now, three deferrals quietly calcify into 'this is how it is.'" Absorbed as v5.0.7 Historical Amendment + this recurring audit.

**Inline audit log:**
- *2026-04-20 (initial filing, session-119):* All items listed above are in active deferral state. No triggers fired. Next audit due ~2026-05-20.

108. **F-C-04 Phase-2 — install_agent `strict_domain_check` block-mode escalation** `D3 Deferred`

**What:** Cohort 5 Session 5-2 shipped `install_agent` with Phase-1 WARN+allow domain-fit semantics (`applicable_domains` frontmatter + optional `domain` param on install_agent → warning if mismatch). The `_parse_applicable_domains` + `_check_domain_fit` helpers in `src/ai_governance_mcp/server.py` have a named escalation trigger `strict_domain_check` that is NOT currently wired to any input. This item tracks the Phase-2 escalation.

**Re-open prerequisites:**
1. **Observed adopter harm** — at least one credible report of a domain mismatch producing actually-wrong work (not just a wasted-context theoretical concern). Ideally 2-3 instances before promoting to block-mode.
2. **Or: CI surface that wants to enforce** — a downstream consumer (e.g., project validation pipeline) requests block-mode as a hard gate.

**Re-open workflow:**
1. Add `strict_domain_check: bool = false` parameter to `install_agent` tool schema.
2. When `strict_domain_check=True` AND `_check_domain_fit()` returns `fits=False`, raise error with structured code (not just a warning) and refuse to proceed with install.
3. Update `test_domain_fit.py` with block-mode cases.
4. Document in CLAUDE.md scaffold template + README adopter guidance.

**Why deferred (not short-term D2):** Phase-1 (WARN+allow) matches the Low-severity framing of F-C-04. No adopter harm has been reported. Block-mode without evidence of harm would be ceremony — the same "build-it-before-consumer-exists" pattern that killed Cohort 4 Phase 4b `Implements:` backfill. Phase-1 is deliberate phased implementation with a named escalation path, not incomplete design.

**Origin:** Cohort 5 Session 5-2 post-edit contrarian review (2026-04-20, session-119, agent `ad83517b730258151`). Contrarian MEDIUM finding: "escalation trigger floating in code comment only — file BACKLOG entry to prevent defer-it-later pattern." Filed per that recommendation.

107. **F-C-06 Tool/Model Appendix index — adopter discoverability for Appendices A-L** `D3 Deferred`

**What:** Tool/Model Appendices (A-L: Claude Code CLI config, prompt caching specs, Postgres/Supabase, permission architecture, production hardening, etc.) are embedded inside `documents/title-10-ai-coding-cfr.md` starting around line 7200+. No standalone index or discoverability mechanism exists. The Situation Index at `rules-of-procedure.md:92` and `title-10-ai-coding-cfr.md:104` fulfills entry-based discovery for *procedures*, but does NOT enumerate all Appendices. Adopters asking "how do I configure Claude Code CLI?" have no discoverable path without knowing to look inside §7200+.

**Re-open prerequisites:**
1. **A consumer emerges** that needs Appendix-level discovery — examples: (a) a retrieval pattern specifically queries "show all Tool Appendices for platform X"; (b) adopter rollout reveals friction with Appendix lookup; (c) Appendix count exceeds a practical threshold (e.g., >15 appendices) making embedded-in-CFR structure unwieldy.
2. **Decision on index location** — dedicated `documents/appendix-index.md` artifact vs. a section added to `README.md` vs. a new §9.7.3 in rules-of-procedure. Depends on what the triggering consumer needs.

**Why deferred (not short-term D2):** Current state is a low-severity gap. Situation Index fulfills most discovery needs (entry-based routing by task). Building a full Appendix index without a concrete consumer would be premature — risks the Phase 4b `Implements:` pattern (build-it-before-consumer-exists, end up with documentary-only artifact that nobody queries).

**Re-open workflow:**
1. Verify prerequisite (1) is met — a real consumer exists.
2. Decide location per prerequisite (2).
3. Build index + link from README + CLAUDE.md.
4. Consider whether to extract Appendices out of CFR files entirely vs. index-only approach.

**Origin:** Cohort 5 Session 5-2 planning (2026-04-20, session-119) — contrarian battery distinguished Situation Index (covers procedures) from Appendix discoverability (covers Tool/Model references); former ships, latter doesn't. Accepted as residual gap for Cohort 5 milestone. See `~/.claude/plans/create-a-plan-following-cached-canyon.md` v3.

106. **Cohort 4 Phase 4b re-open — `Implements:` backfill across 6 CFR files (406 methods)** `D3 Deferred`

**What:** Backfill of `**Implements:**` field was planned for 406 of 455 CFR methods (current coverage 10.8%; see `~/.claude/plans/create-a-plan-following-cached-canyon.md` v3). **Deferred** by pre-edit 3-agent battery analysis (2026-04-19, session-118). Not to be re-opened without meeting both prerequisites below.

**Prerequisites for re-open:**
1. **A consumer emerges** that loads `Implements:` — e.g., `MethodMetadata` gains structured `implements` field + extractor regex + `query_governance` surface that filters by parent principle; OR an external compliance audit requires machine-verifiable traceability.
2. **Q7 remediation ships first** — current field name inherits from US CFR's `enabling_authority` (legally enforceable) while operational reality is free-text. FAILS `rules-of-procedure §9.8.1` Q7 (Semantic-Label Risk). Choose (a) rename `**Implements:**` → `**Traces To:**` across the 49 existing entries + new backfills, OR (b) add documentary disclaimer at each CFR's head stating the field is not machine-enforced.

**Why deferred (not a short-term D2):** The battery REJECT was structural, not a scheduling issue. Extractor has never parsed the field (`src/ai_governance_mcp/extractor.py:1686-1699` parses `Applies To` only; grep confirmed zero `Implements:` references in tests). Executing 406 backfills before a consumer + Q7 remediation would cement both the coverage-ambiguity and the label/operation mismatch at scale. Phase 4a closed the substantive findings (F-P1-06, F-P2-06, F-P2-14, F-P2-17); F-P1-04 is re-severity'd to MEDIUM-at-most and recorded as "partial coverage retained; documentary-only."

**Re-open workflow:**
1. Verify both prerequisites met.
2. Re-read battery findings in `~/.claude/plans/create-a-plan-following-cached-canyon.md` v3 — especially validator's structured spot-check predicates and coherence-auditor's corrected chunk-count arithmetic (Parts 5-6 = 109 methods; Parts 7-9 = 80 not 50-65).
3. Run new pre-edit battery (context may have changed).
4. Execute per fallback path in that plan file (6 sessions, not 5; Q7 remediation as HARD prereq; 10-per-CFR spot-check with 4-predicate criteria).

**Origin:** Cohort 4 Phase 4b planning (session-118, 2026-04-19). Governance audit `gov-3e5998987962` (evaluate_governance PROCEED with no S-Series). Battery audit IDs: contrarian `a7e2b2716f06770cc`, coherence `ae0c4ea9057ea7dd7`, validator `a39dda1cd66beb441`.

104. **Cohort 1 remnant — runtime prose softening at `src/ai_governance_mcp/server.py:888-889`** `D1 Docs` — DONE / SHIPPED

**Status (2026-04-19, session-114): SHIPPED.** Applied replacement text per plan; smoke-check (`python -c "from ai_governance_mcp.server import AVAILABLE_AGENTS"`) confirms server imports cleanly with 10 agents registered. No test references to the old prose (grep confirmed clean outside BACKLOG + SESSION-STATE historical references). Cohort 1 of swift-hopping-corbato plan now fully closed: Edits 1-2 = no edit (purpose surfaces), Edits 3-5 shipped via full README rewrite, Edit 6 shipped here, Edits 7-8 obsolete.

**What:** The `install_agent` subagent-install prose at `server.py:888-889` currently reads: *"Subagents make specialized behaviors automatic, not optional — ensuring consistent, high-quality AI collaboration every time."* This string is injected into every MCP client at `install_agent` time. It re-asserts the same unfalsifiable outcome claim that was softened out of the README — classic laundering pattern (remove the claim from one surface, leave it on another).

**Proposed replacement:** *"Subagents encode specialized cognitive functions with explicit protocols — making the discipline of each function auditable rather than relying on ad-hoc prompting."*

**Systemic check:** class (c) surface (runtime-injected product-facing prose) per LEARNING-LOG 2026-04-18 "Declaration and Preamble Are Purpose Surfaces, Not Claim Surfaces" — evidence-check applies. "Auditable" is evidence-backed (audit trail + `log_governance_reasoning` exist). No outcome-quality claim.

**Steps:**
1. After README rewrite lands, edit `server.py:888-889` with the proposed text (or user-revised variant).
2. Verify via `grep -rn "consistent.*high-quality" src/` returns 0 matches outside test fixtures.
3. No tests fail (string is prose, not behavior).
4. Close this item with commit reference.

**Why D1 not D2:** Runtime prose ships to every MCP client. If the README softens but the runtime does not, the framework contradicts itself at install-time. Same urgency as the README fix.

**Origin:** session-114 swift-hopping-corbato Cohort 1 scope-expansion (coherence-auditor convergent finding with contrarian-reviewer during 3-agent battery on Declaration softening).

---

### Deferred/Future — Discussion

> Items below need discussion to flesh out intent, determine if we want to implement, and define scope. Not committed to implementation.

#### 91. Pre-Test OOM Gate Hardening — Session-105 Follow-ups (Discussion) `D1 Improvement`

**Status (2026-04-21, session-121):** 9 fix-now items shipped. Remaining: 1 item (sub-item 5).
- **Sub-items 1, 2, 6, 7, 8, 9, 10 — DONE** (session-108): ERR trap, jq fallback, secret redaction, plist verified, PYTEST_CURRENT_TEST guard, -k docs, SESSION-STATE baseline note. 30 tests (up from 23).
- **Sub-item 4 — DONE** (session-111): resolved structurally via `rules-of-procedure` v3.26.8 Appendix G.5.1 — platform-native plan files are session-scoped working memory; framework files no longer cite them as load-bearing references. Load-bearing reasoning promotes inline into BACKLOG/LEARNING-LOG/SESSION-STATE before session end.
- **Sub-item 3 — DONE** (session-121, 2026-04-21): Claude Code hook timeout semantics researched from official docs (code.claude.com/docs/en/hooks) = non-blocking allow (ERR trap does not catch SIGKILL). Hook hardened: internal `timeout 7 ps` guard added so hook self-denies (exit 2) before 10s SIGKILL fires. CFR §9.3.10 Layer-3 fail-behavior claim corrected to reflect the conditional fail-closed guarantee + new hook-authoring guidance. New LEARNING-LOG entry "Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout" (2026-04-21) captures the distinct rule. **Re-severity per LEARNING-LOG 2026-04-20 Entry B:** MED-at-filing (unknown semantics) → HIGH-at-close pre-remediation (fail-open correlated with threat: `ps` slowest under memory pressure = exactly when gate needed) → LOW-at-close post-remediation (internal `timeout` wrapper closes the gap). Files: `.claude/hooks/pre-test-oom-gate.sh`, `documents/title-10-ai-coding-cfr.md` (v2.38.3), `LEARNING-LOG.md`.
- **1 item legitimately deferred** (sub-item 5 — needs CI infra).

**Previous status (2026-04-15, user audit):** This entry was created by bulk-logging 10 brainstorm items at session-105 end, which violated CLAUDE.md Defer-vs-Fix rule. User audit reclassified 7 as fix-now, 1 as ask, 2 as defer.

See `LEARNING-LOG.md` entry "Session-End Deferral Bias (2026-04-15)" for the pattern this illustrates and the rule that was violated.

**What:** A grab-bag of hardening and ops items surfaced during the session-105 end-of-session "10 things I may have missed" brainstorm on `.claude/hooks/pre-test-oom-gate.sh`. None are blockers; the hook is functional and protective as-shipped.

**Sub-items (priority order, highest first — classification tags from 2026-04-15 user audit):**

1. **[FIX-NOW / MED] `jq` missing/failure = silent fail-open.** Line 61 of the hook: if `jq` errors, `COMMAND` becomes empty, the regex match fails, the hook exits 0 and allows. Mirrors the `python3` fail-open that code-reviewer #13 caught at the END of the hook (which was fixed to exit-2). Fix: check for `jq` at top-of-script and exit non-zero on missing. Or replace `jq` with a small Python parser (more dependencies-but-fail-closed). **Classification:** ≤1 file, unambiguous, symmetric to already-fixed bug → fix-now tier. Deferring was the violation.

2. **[FIX-NOW / MED] `oom-gate-denies.log` has no rotation or cap.** `printf ... >> $DENY_LOG` appends forever. Runaway loop or stuck automation could fill `~/.context-engine/`. Fix: add `tail -1000` pruning on write, or switch to a fixed-size circular log, or add to logrotate. **Classification:** ≤1 file (hook), known pattern → fix-now tier.

4. **[DONE session-111] Plan file lives outside the repo.** Resolved structurally: `rules-of-procedure` v3.26.8 Appendix G.5.1 defines platform-native plan files as session-scoped working memory that framework files must not cite as load-bearing. Load-bearing reasoning promotes inline into BACKLOG/LEARNING-LOG/SESSION-STATE before session end (already true for #49 content). Path references across repo removed session-111. Scales across all future plans without new infrastructure.

5. **[DEFER / LOW] No real-runner integration test.** All 23 hook tests shell out directly. Claude Code's real PreToolUse runner could parse the deny JSON differently or have edge-case stdin behavior that the direct-shell tests miss. First real organic deny would be the integration test. Consider adding a CI job that invokes the hook via a Claude-Code-like runner stub. **Classification:** requires CI infrastructure (runner stub), legitimate defer.

6. **[FIX-NOW / LOW] Deny-log may capture secret-bearing command strings.** `pytest --api-key=$SECRET tests/` would get logged verbatim (bounded to 500 chars). Fix: add a regex filter for `--[a-z-]*(key|token|secret|password)=\S+` → replace with `<redacted>` before appending. **Classification:** ≤1 file (hook), one-line regex addition, unambiguous → fix-now tier.

7. **[FIX-NOW / LOW] Launchd plist flag verification not captured.** Session-105 unloaded and reloaded the context-engine-watcher plist to disable auto-restart mid-session. Didn't verify `RunAtLoad` / `KeepAlive` flags are preserved across `unload`/`load`. On next machine reboot, if flags got lost, daemon won't auto-start. Fix: `plutil -p ~/Library/LaunchAgents/com.ai-governance.context-engine-watcher.plist` and document expected flags in `COMPLIANCE-REVIEW.md` Check 1. **Classification:** ≤1 file (docs), verifiable via `plutil` → fix-now tier.

8. **[FIX-NOW / LOW] `OOM_GATE_SKIP_PROCESS_SCAN` is test-only by comment convention only.** A future session grep-discovering the variable could mistake it for a third production bypass. Structural fix: rename to `_OOM_GATE_SKIP_PROCESS_SCAN` (underscore convention) or guard it with `[ -n "${PYTEST_CURRENT_TEST:-}" ]` so it can't leak outside a pytest process. **Classification:** 2 files (hook + tests), mechanical rename or one-line guard → fix-now tier.

9. **[FIX-NOW / LOW] `-k <expr>` safe-subset match is permissive.** `pytest tests/ -k test` matches every test (pytest collects all tests whose names contain "test"). Accepted per threat model, but not explicitly called out in the hook header. Document the limitation inline so future readers know the `-k` hatch is intent-based, not content-validated. **Classification:** ≤1 file (hook header comment), docs-only → fix-now tier.

10. **[FIX-NOW / LOW] SESSION-STATE Quick Reference baseline drift explanation missing.** Historical entries for sessions 101–104 show "1198 passing" while the updated Quick Reference now shows "1191 passing (session-105: +23 hook tests on 1168 baseline)". A future reader comparing numbers sees a ~7 delta with no explanation (1198 is full suite; 1191 is `-m "not slow"` subset + new hook tests). Fix: add a one-line note in Quick Reference explaining the semantics, or reconcile to a single canonical number. **Classification:** ≤1 file, one-line clarification → fix-now tier.

**[Bonus] Item 11:** Concurrent-session deny-log write safety. POSIX `>>` is atomic for writes <PIPE_BUF (512 bytes on macOS); log line is well under that, but not explicitly tested under concurrency. Low risk.

**[Bonus] Item 12:** Consider adding an ADR for the pre-test OOM gate pattern as a new class of structural enforcement (test-run safety vs governance enforcement). Would live alongside ADR-13 (Governance Enforcement — Advisory→Structural). Defer until the pattern is reused for a second purpose — not worth an ADR for a one-off.

**Discussion needed:**
- Which sub-items rise above the "nice to have" floor? Probably 1-2 are the real ones (sub-item 3 shipped session-121).
- Is the bonus ADR-17-for-hook-pattern worth doing now (aids future reuse) or deferring until pattern recurs (avoids speculation)?
- Should sub-item 4 (plan-file preservation) become its own `D2 Maintenance` item — it's about a class of "decisions-outside-repo" drift, not just this one plan file.

**Origin:** Session-105 end-of-session brainstorm (2026-04-15), two subagent review passes didn't surface these (they weren't in the review scope).

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

**Origin:** Independent research via Claude app (no anchor bias from existing framework). Reviewed against Part 9.8 Admission Test — passes all 7 questions (v3.27.0+). Contrarian review and coherence audit completed (see draft below).

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

**Disposition (2026-04-19, session-116 Cohort 3 close):** Parent swift-hopping-corbato plan bound F-P2-09 (Risk/Non-Mal redundancy) AND F-P2-13 (Relations gap) both to #34 as their Epistemic-Integrity-adjacent pre-registered tracking. Both resolved via Path B routes that preserved existing principle structure without adding Epistemic Integrity: F-P2-09 via Cohort 2 de-duplicate-in-place (v5.0.0); F-P2-13 via Cohort 3 documentation-only (Preamble-purpose-is-distributed-not-concentrated). See PROJECT-MEMORY "Preamble Purpose Coverage Is Distributed, Not Concentrated" (2026-04-19) + "Path B Over Path A for Risk Mit ↔ Non-Mal" (2026-04-19). Neither cohort produced a gap the existing content doesn't cover; no Epistemic Integrity principle needed. **#34 closed as resolved-in-place.** If a future review surfaces sycophancy/honesty gaps with fresh evidence, can be re-opened as a new entry (not re-open this one).

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

#### 84. README Rewrite — Intent Engineering Framing (DONE — SHIPPED) `D1 Docs`

**What:** Full rewrite of the ai-governance README. Frames the project as "intent engineering" infrastructure — encoding goals, constraints, quality standards, and decision-making boundaries so AI understands purpose, not just instructions.

**Status (2026-04-19, session-114): SHIPPED.** Live `README.md` replaced with the revised rewrite (461 lines, ~54% reduction from 1006). 5-layer engineering stack (prompt → retrieval → context → harness → intent) + new "Use via RAG (No MCP Server)" section + mechanism-property framing throughout. Source of truth was `staging/readme-draft-v1.md` post-Cached-Canyon remediation. 3-agent battery (contrarian xhigh, coherence high, validator high) returned findings → consolidated into 4 root causes via `~/.claude/plans/create-a-plan-following-cached-canyon.md` → 6 remediation edits applied → final coherence-auditor pass returned COHERENT, no drift. Option B chosen at merge time: forward reference to `documents/intent-engineering.md` stripped pending that file's arrival (user drafting in Claude app); reinstate line 23 second sentence when ready.

**Structural decisions captured** (see PROJECT-MEMORY "README Role — Extra-Constitutional Infrastructure" 2026-04-18):
- README is NOT a §1 Federalist Papers analog.
- README LINKS to Declaration and Preamble — does not paraphrase (SSOT).
- Humans-first practical; AI-occasional.

**Anti-anchor-bias findings on the original #84 component list** (applied during draft synthesis, load-bearing for future reviewers):
- **Rejected:** "Content Enhancer" (#1) — lives at `~/Documents/Reference/AI/...` per BACKLOG #85, NOT in this repo. Cannot claim presence of what isn't present.
- **Rejected:** "Transparency and Attribution System" (#7) — "enhancement tagging, external research sourcing" describes Content Enhancer functionality, not this repo's governance audit trail.
- **Needed rewording:** "AI Instructions Layer" (#4) — "fidelity requirements, enhancement tags" is Content-Enhancer language; this repo has `ai-instructions.md` + `CLAUDE.md` with different content.
- **Needed rewording:** "Workflow & Compliance Layer" (#6) — "sequential phase requirements" is Content-Enhancer language; this repo has `workflows/COMPLETION-CHECKLIST` + `COMPLIANCE-REVIEW` with governance focus.
- **Kept:** intent-engineering three-phase framing (prompt → context → intent), "judgment not smartness," destination-agnostic positioning, knowledge-domains component, memory-system component, AI-assisted-development-framework component.

**Key framing (kept):** The industry has moved through three phases — prompt engineering → context engineering → intent engineering. This project operates at the third level.

**Governing philosophy (kept):** Not making AI smarter — giving it judgment. The infrastructure acts as a filter for contradictory internet knowledge, telling AI what quality looks like and how to evaluate conflicting information.

**Differentiator (kept):** Most AI tools are destination-specific. This infrastructure is destination-agnostic — upgrades how AI performs for whatever you're doing. "The GPS, the road kit, the reliability layer — not the route itself."

**Surgical edits already applied to live README** (session-114, not yet subsumed by rewrite landing):
- `README.md:5` tagline → "queryable 'second brain' of encoded standards" (Edit 3).
- `README.md:40` Key Innovation → "retrievable, auditable, and structurally enforceable at the moment of the AI's decision" (Edit 4).

**Next steps:** user review → revision → 3-agent battery → replace live README → close this item.

**Origin:** Claude app draft + session-114 mid-Cohort-1 pivot. Draft location: `staging/readme-draft-v1.md`.

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

#### 102. scaffold_project Standard Kit Misalignment (DONE — SHIPPED Cohort 3, session-116) `D1 Fix`

**What:** The `scaffold_project` tool created 6 files for standard tier (core 4 + CLAUDE.md + COMPLETION-CHECKLIST.md); `title-10-ai-coding-cfr.md §1.5.2` defines Standard Kit as 8 files (core 4 + ARCHITECTURE.md + SPECIFICATION.md + workflows/COMPLETION-CHECKLIST.md + BACKLOG.md).

**Status (2026-04-19, session-116): SHIPPED.** Cohort 3 Change B added 3 skeletal templates (`SCAFFOLD_ARCHITECTURE`, `SCAFFOLD_SPECIFICATION`, `SCAFFOLD_BACKLOG` — 20-40 lines each with explicit "starter template — populate as your project matures" banners) to `SCAFFOLD_STANDARD_EXTRAS["code"]`. Also corrected `COMPLETION-CHECKLIST.md` path to `workflows/COMPLETION-CHECKLIST.md` (subdirectory per §1.5.2 literal). Scaffold Standard = 9 files: 4 core + 5 extras (CLAUDE + ARCHITECTURE + SPECIFICATION + workflows/COMPLETION-CHECKLIST + BACKLOG). CLAUDE.md retained as tool-specific overlay per §1.5.5 (§1.5.3 "Standard Kit + additions as warranted" authorizes this). Test `tests/test_server.py::TestScaffoldProject::test_preview_code_standard` updated from `files_to_create == 6` to `== 9`.

**Origin:** Coherence audit during BACKLOG.md propagation (2026-04-14); resolved in Cohort 3 per swift-hopping-corbato plan.

---
