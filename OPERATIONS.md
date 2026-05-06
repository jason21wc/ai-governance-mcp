# Operations

**Memory Type:** Operational (recurring commitments)
**Lifecycle:** Items persist indefinitely unless retired with documented rationale. Review cadences are the point — these items are never "done."

> **Scope.** This file is the registry for recurring operational commitments: cadences (periodic reviews), tripwires (conditional re-evaluations), verification experiments (time-bound hypothesis tests), effectiveness metrics (system health indicators), and scheduled operations (automated tasks). Detailed procedures stay in their canonical homes (e.g., check definitions in `workflows/COMPLIANCE-REVIEW.md`). This file is the index, not the procedure repository.
>
> **Relationship to BACKLOG.md.** BACKLOG holds discrete projects (start, work, finish). OPERATIONS holds indefinite-lifecycle items (cadences that recur, tripwires that watch, metrics that accumulate). When a tripwire fires and creates discrete work, that work goes to BACKLOG as a project; the tripwire entry here records the firing and may remain active if the trigger can re-fire.
>
> **Origin.** Created 2026-05-03 per EXECUTION-FRAMEWORK.md gap analysis (Bucket 5/8 — Orchestration/Lifecycle) and BACKLOG #146 taxonomy split decision. Evaluated 4 alternatives (tag-only, two-file split, single file, fold into PROJECT-MEMORY) — single file with internal taxonomy selected.

---

## Cadences

> Periodic reviews on a fixed schedule. The cadence is the point — these are never "done."

### C-078. Governance Compliance Review

**Cadence:** Every 10-15 calendar days. Event triggers: hook/CLAUDE.md/tiers.json modification.
**Procedure:** `workflows/COMPLIANCE-REVIEW.md` (12 checks). Invoke via `/compliance-review` skill.
**Reviews completed:** #1-7 (most recent: 2026-05-05).
**Next review due:** ~2026-05-15.
**Origin:** BACKLOG #78 (migrated 2026-05-03).

---

### C-109. Deferred-with-trigger cadence audit

**Cadence:** Every ~30 calendar days, OR whenever a session's work plausibly satisfies a trigger.
**What:** Several review findings across Cohorts 4-5 were deferred with "re-open when consumer emerges" triggers. Without a watch-list, principled deferrals quietly calcify into silent abandonment.

**Deferred items tracked (as of 2026-04-20):**
- **BACKLOG #41 / #43 / #44 / #46** — Reference library improvements (auto-staging, progressive disclosure, auto-maturity, stack metadata).
- **BACKLOG #58 / #59 / #60** — UBDA adopter-drift review items.
- **T-106** — `Implements:` backfill (prerequisites: consumer + Q7 remediation).
- **T-107** — Tool/Model Appendix index (prerequisites: consumer OR appendix count >15).
- **T-108** — `strict_domain_check` block-mode (prerequisites: observed adopter harm OR CI enforcement request).
- **T-110** — F-P2-01 + R-01 retrospective (prerequisites: R-01 ships + retrospective).
- **T-111** — Post-edit review scope expansion (prerequisites: 2+ more cohorts OR adopter report).
- **T-112** — Q7 retroactive audit (prerequisites: session capacity OR new finding).
- **T-113** — Plan-stage battery effectiveness (prerequisites: N≥6 cohorts OR adopter-reported failure).
- **F-P2-03 accepted residual** — FM-code retrofit (prerequisites: consumer + parser).

**Audit procedure:**
1. For each item, re-read the trigger prerequisites literally.
2. Answer "still deferred?" in ≤1 sentence per item.
3. If ANY trigger met: promote to BACKLOG project and assign work.
4. If no triggers met: record audit date inline.
5. Update this entry's inline audit log with results.

**Inline audit log:**
- *2026-04-20 (initial filing):* All items in active deferral. No triggers fired. Next: ~2026-05-20.
- *2026-04-25 (Compliance Review #5):* 0/14 triggers fired. Per-item detail in git history (`git log --grep="109"`).
- *Next audit due: ~2026-05-25.*

**Origin:** BACKLOG #109 (migrated 2026-05-03). Cross-cohort meta-review (session-119) contrarian finding: passive triggers calcify without periodic review.

---

## Tripwires

> Conditional re-evaluations. Watch indefinitely. Close on event-trigger firing (promotes to BACKLOG project) OR accepted-residual decision. Each entry has explicit trigger conditions.
>
> **When a trigger fires:** Record the firing date and evidence in the tripwire entry. If the triggered work is discrete (implement, fix, design spike), file it as a BACKLOG project. The tripwire entry remains here if the trigger can re-fire; close it if the condition is permanently resolved.

### T-149. CE-first compliance measurement (Phase 2 activation gate)

**Trigger conditions:** (1) CE-vs-grep ratio for discovery queries stays below 85% after 3-5 sessions with Phase 1 advisory changes deployed, OR (2) user reports persistent grep-over-CE behavior despite Phase 1 improvements.
**What:** Phase 1 of CE-First Search plan shipped tool description ("Default search tool"), SERVER_INSTRUCTIONS ("When to Use Grep Instead"), and CLAUDE.md ("Search default: CE first") improvements. Phase 2 (Grep/Glob PreToolUse advisory hook) activates ONLY if Phase 1 proves insufficient. Measurement: observe CE-vs-grep usage in session transcripts. If ≥85% CE compliance, Phase 2 is unnecessary.
**Origin:** Session-149 (2026-05-05). CE-First Search plan, contrarian Challenge 1 (measurement gate between phases).

---

### T-119. Revised-plan-after-rejection heuristic

**Trigger conditions:** (1) Observed case of revised-plan-without-fresh-contrarian producing actually-bad approval, OR (2) design session settles on workable plan-revision detection signal.
**What:** Scanner's `scan_contrarian_after_last_plan` uses "most recent prior ExitPlanMode" as anchor. Plan revisions after user rejection satisfy the anchor without fresh contrarian pressure-test.
**Origin:** BACKLOG #119 (migrated 2026-05-03). Session-122 post-commit contrarian HIGH.

---

### T-134. PR-workflow infrastructure

**Trigger conditions:** (1) ≥3 external watchers OR ≥1 external issue/PR, (2) documented incident where pre-push battery missed a defect PR review would have caught, (3) maintainer wants time-separation review.
**What:** CODEOWNERS, branch protection paths, pre-push routing hook for high-blast-radius paths. Deferred — repo is single-maintainer with 0 external engagement.
**Origin:** BACKLOG #134 (migrated 2026-05-03). Session-127 push-workflow plan.

---

### T-143. OOM-gate quoted-region false-positive

**Trigger conditions:** (1) A maintenance commit touches `pre-test-oom-gate.sh` for any other reason (cluster the fix), OR (2) FP volume causes material friction (currently low — workaround: Write tempfile + `git commit -F`).
**What:** Pre-test OOM gate's token-anchored matcher cannot distinguish `pytest` in executable position from quoted-region content (heredoc bodies, grep alternation). Known workaround documented in CLAUDE.md.
**Origin:** BACKLOG #143 (migrated 2026-05-03). Session-136/139.

---

### T-145. Citation-form check hardening

**Trigger conditions:** (1) First observed false-positive in production (fenced code), (2) first wrong-§-anchor citation surviving review, (3) first normative section with exclusion-substring heading, (4) real bug items 1-3 would have caught by missing tests, (5) maintenance commit touching `scripts/check-citations.py`.
**What:** Four hardening items from BACKLOG #144 post-arc double-check: fenced-code-block exclusion, §-anchor accuracy verification, hostile-heading false-exclusion, test edge-case gaps.
**Origin:** BACKLOG #145 (migrated 2026-05-03). Session-138.

---

### T-113. Plan-stage pre-edit battery effectiveness

**Trigger conditions:** (1) Evidence base N≥6 cohorts (currently n=4), OR (2) adopter-reported plan failure battery didn't catch.
**What:** 4-of-4 pre-edit 3-agent batteries caught major pivots in first-draft plans. Pattern suggests first-draft plans are systematically under-rigored, with battery compensating.
**Origin:** BACKLOG #113 (migrated 2026-05-03). Session-119 cross-cohort meta-review.

---

### T-112. Q7 retroactive audit — remaining pre-Q7 US-legal labels

**Trigger conditions:** (1) Sufficient session capacity for focused Q7 pass, OR (2) new finding of operational-mismatch harm on one of the labels.
**What:** 4-6 pre-Q7 US-legal labels remain unchecked (Supremacy Clause, Elastic Clause, Full Faith and Credit, Jacobson v. Massachusetts, Bill of Rights generic, Impeachment fast-path).
**Origin:** BACKLOG #112 (migrated 2026-05-03). Session-119.

---

### T-111. Post-edit review scope expansion

**Trigger conditions:** (1) At least 2 more cohorts where post-commit battery finds same class of drift (currently n=4), OR (2) adopter report of post-commit drift causing user-visible harm.
**What:** 100% post-commit PATCH rate across 4 cohorts suggests post-edit scope is structurally gapped (misses adopter-facing surface propagation).
**Origin:** BACKLOG #111 (migrated 2026-05-03). Session-119.

---

### T-110. F-P2-01 + R-01 priority-inversion retrospective

**Trigger conditions:** (1) R-01 outcome benchmark ships (or declared unmeasurable), AND (2) retrospective on whether 28 closed findings need re-severity.
**What:** Critical finding closed by claim-softening (Declaration rewrite) without shipping measurement (R-01 outcome benchmark). Contrarian: "arc inverted priority."
**Origin:** BACKLOG #110 (migrated 2026-05-03). Session-119.

---

### T-108. strict_domain_check block-mode escalation

**Trigger conditions:** (1) Observed adopter harm from domain mismatch, OR (2) CI surface requests block-mode enforcement.
**What:** `install_agent` shipped with WARN+allow domain-fit semantics (Phase 1). Phase 2 escalation to block-mode deferred until evidence of harm.
**Origin:** BACKLOG #108 (migrated 2026-05-03). Session-119.

---

### T-107. Tool/Model Appendix index

**Trigger conditions:** (1) A consumer emerges needing Appendix-level discovery, OR (2) appendix count exceeds >15 (currently 13, A through M).
**What:** Tool/Model Appendices embedded inside `documents/title-10-ai-coding-cfr.md` have no standalone index. Situation Index covers procedures but not Appendix discoverability.
**Origin:** BACKLOG #107 (migrated 2026-05-03). Session-119.

---

### T-106. Implements: backfill across 6 CFR files

**Trigger conditions:** (1) A consumer emerges that loads `Implements:` field (extractor gains structured support), AND (2) Q7 remediation ships first (rename or disclaimer).
**What:** 406 of 455 CFR methods lack `Implements:` field. Deferred by pre-edit battery (consumer-before-build pattern). Both prerequisites required.
**Origin:** BACKLOG #106 (migrated 2026-05-03). Session-118 Cohort 4 Phase 4b.

---

### T-049. Embedding memory — calendar review

**Trigger conditions:** (1) 2026-06-15 unconditional review date, (2) PHASE2_TRIGGERED marker re-fires (`~/.context-engine/PHASE2_TRIGGERED`), (3) proposal to add a 6th torch-loading process.
**What:** BACKLOG #49 closed with Phase 2 IPC service shipped and verified. Daily measurement plist (`com.ai-governance.context-engine-measure`) and OOM gate hook continue running independently. This tripwire preserves the calendar review forcing function from the closed backlog entry: if no automated trigger fires by 2026-06-15, review current memory measurements and confirm the shared embedding architecture remains healthy.
**Origin:** BACKLOG #49 close (session-147, 2026-05-04). Calendar trigger migrated from BACKLOG to OPERATIONS on close.

---

### T-019. Rampart agent firewall adoption

**Trigger conditions:** (1) Project adds credential files, (2) external contributors appear (≥1 issue/PR), (3) Rampart reaches 1.0 with broad adoption, (4) credential leak Layer 1+2 would not have caught.
**What:** Layer 1 (Read deny) + Layer 2 (content-security hook) shipped. Full Rampart integration deferred — disproportionate to current attack surface (single developer, public code, no credentials in repo).
**Landscape:** Rampart v0.9.22, 67 stars. Alternatives: Microsoft Agent Governance Toolkit, Meta LlamaFirewall.
**Origin:** BACKLOG #19 tripwire portion (new OPERATIONS entry 2026-05-03). Main work shipped session-143.

---

## Verification Experiments

> Time-bound hypothesis tests tracking whether recently-introduced mechanisms are working. Each has success/failure criteria and an expiration condition. Definitions and execution history live in `workflows/COMPLIANCE-REVIEW.md` (self-contained per navigability principle). This section is the registry/index.

| ID | Name | Status | Defined In | Added |
|----|------|--------|------------|-------|
| V-005 | SESSION-STATE pruning compliance | **CONFIRMED** | `workflows/COMPLIANCE-REVIEW.md` | 2026-04-14 |
| V-006 | Pre-exit-plan-mode-gate hook-denial rate | OPEN | `workflows/COMPLIANCE-REVIEW.md` | 2026-04-23 |
| V-007 | Plan-action-atomicity WARN-mode firing rate | OPEN | `workflows/COMPLIANCE-REVIEW.md` | 2026-04-25 |
| V-008 | TDD test-existence WARN-mode firing rate | OPEN | `workflows/COMPLIANCE-REVIEW.md` | 2026-04-25 |

**Retired:** V-001 (RETIRED → replaced by session-audit), V-002 (CONFIRMED), V-003 (CONFIRMED), V-004 (REFUTED → escalated to hook). See `workflows/COMPLIANCE-REVIEW.md` Retired section for dispositions.

---

## Effectiveness Metrics

> System health indicators measured periodically. Script automation deferred until data volume warrants it (n>1000 audit entries). See BACKLOG for `scripts/analyze-governance-metrics.py` tracking item.

### M-001. Governance Influence Rate

**What:** Fraction of `evaluate_governance` calls that return PROCEED_WITH_MODIFICATIONS or ESCALATE (i.e., governance actually changed the planned action, not just rubber-stamped it).
**Data source:** `evaluate_governance` response `recommendation` field across session transcripts.
**Computation:** `count(PROCEED_WITH_MODIFICATIONS + ESCALATE) / count(all evaluations)` per review period.
**Baseline:** Not yet established. First compliance review after n≥50 evaluations sets baseline.
**Review cadence:** Every compliance review (C-078).

### M-002. Principle Citation Frequency

**What:** How often principle IDs appear in session output, indicating governance is influencing reasoning rather than being called and ignored.
**Data source:** Session transcripts — grep for `meta-*`, `coding-*`, `s_series_*` ID patterns.
**Computation:** Unique principle IDs cited per session, averaged across review period.
**Baseline:** Not yet established. Expect 3-8 unique IDs per substantive session.
**Review cadence:** Every compliance review (C-078).

### M-003. Retrieval Relevance Trend

**What:** Whether semantic retrieval quality is stable, improving, or degrading over time.
**Data source:** `get_metrics` MCP tool — returns `avg_relevance_score` from governance server query history.
**Computation:** Rolling average relevance score per review period. Flag if >10% decline from baseline.
**Baseline:** MRR method=0.646, principle=0.750 (established 2026-04-16, Phase 2 verification).
**Review cadence:** Every compliance review (C-078). Deeper analysis when retrieval-related BACKLOG items are active.

### M-004. S-Series Trip Rate

**What:** How often S-Series (Bill of Rights) principles trigger during governance evaluation — signals either genuine safety catches or false-positive noise.
**Data source:** `evaluate_governance` response `s_series_check.triggered` field.
**Computation:** `count(s_series_triggered=true) / count(all evaluations)` per review period. Decompose by principle ID to distinguish real triggers from FP patterns (cf. BACKLOG #150).
**Baseline:** Not yet established. Expected low rate (<5%). Sustained high rate indicates retrieval FP problem.
**Review cadence:** Every compliance review (C-078).

### M-005. Hook Denial Rate

**What:** How often hooks block actions — indicates whether enforcement is functioning and whether false-positive friction is acceptable.
**Data source:** Hook deny logs — `~/.context-engine/oom-gate-denies.log` (OOM gate), `~/.claude/hook-bypass-audit.log` (when #135 ships), hook stderr output in session transcripts.
**Computation:** Denials per hook per review period. Classify TP vs FP where possible.
**Baseline:** OOM gate: 6 total denials across 14 days (4 FP, 2 TP) as of 2026-04-28. Other hooks: no centralized deny log yet (pending BACKLOG #135).
**Review cadence:** Every compliance review (C-078). Individual hook FP rates tracked in their respective tripwire entries (T-143 for OOM gate).

---

## Scheduled Operations

> Automated or semi-automated tasks on defined cadences. Three available mechanisms, each with constraints:
>
> | Mechanism | Where it runs | MCP access | Hooks | Lifetime | Best for |
> |-----------|--------------|------------|-------|----------|----------|
> | **CronCreate** (session-local) | Current REPL, fires when idle | Yes (local servers) | Yes | 7-day auto-expiry (recurring) | Within-session reminders, periodic checks during active work |
> | **Cloud routines** (claude.ai/code/routines) | Remote clone from GitHub | Connected connectors only | No | Persistent | Repo-only tasks not needing local MCP |
> | **Hooks** (`.claude/settings.json`) | Local, on tool invocation | No (pre/post tool) | N/A | Permanent | Enforcement gates, pre-commit checks |
>
> **Current constraint:** This project's governance and context-engine MCP servers are local processes. Cloud routines cannot call them. CronCreate can, but expires after 7 days. Consequence: cadences longer than 7 days (C-078 at 10-15 days, C-109 at 30 days) cannot be fully automated with current mechanisms. The session-start protocol in CLAUDE.md is the primary enforcement point.

### SO-001. Compliance review staleness check

**Mechanism:** Session-start protocol (CLAUDE.md § Session Lifecycle) + `/compliance-review` skill.
**Cadence:** Every 10-15 calendar days (per C-078).
**Current trigger:** Manual — operator says "run compliance review" or invokes `/compliance-review`.
**Automation status:** Semi-automated. The compliance-review skill (`.claude/skills/compliance-review/SKILL.md`) automates execution once invoked. Full automation blocked by: (a) local MCP server dependency prevents cloud routines, (b) 7-day CronCreate expiry is shorter than the 10-day cadence. The skill's staleness check (`git log --since` injection) surfaces overdue reviews when invoked.
**Demonstrated:** CronCreate job configured (daily 09:23, staleness check via `git log --grep`). Confirmed session-only — `durable: true` parameter not honored. Job expires with session or after 7 days. Demonstrates the mechanism but does not replace manual invocation for the 10-15 day cadence.
**Proposed improvement:** When CronCreate gains persistence beyond 7 days OR cloud routines gain local MCP forwarding, configure automated invocation.

### SO-002. Deferred-cadence audit reminder

**Mechanism:** Session-start protocol + C-109 inline audit log.
**Cadence:** ~30 calendar days (per C-109).
**Current trigger:** Manual — during session-start review of OPERATIONS.md, operator checks C-109 "Next audit due" date.
**Automation status:** Manual. 30-day cadence far exceeds CronCreate's 7-day expiry. Cloud routines could run the audit (grep-based, no MCP dependency) but would need push access to update the inline audit log.
**Proposed improvement:** File as cloud routine candidate when the project has a GitHub remote with push access configured for routines.

### SO-003. Session-end memory update

**Mechanism:** Session Closer Protocol (`multi-method-session-closer-protocol`).
**Cadence:** Every session.
**Current trigger:** Manual — operator says "update session state" or session naturally ends.
**Automation status:** Manual. Session-end detection is the hard problem — Claude Code has no "on-exit" hook. CronCreate could set a periodic reminder during active sessions, but the operator must still initiate the update. The `/loop` mechanism with `<<autonomous-loop-dynamic>>` could theoretically poll for idle-then-close, but this is fragile and not recommended.
**Proposed improvement:** If Claude Code adds an `on-session-end` hook event, configure automatic SESSION-STATE.md update. Until then, the session-start pruning protocol (CLAUDE.md § Session Lifecycle) is the compensating control — it catches what the prior session missed.

---

## Version History

| Date | Change | Session |
|------|--------|---------|
| 2026-05-03 | Created. Scaffold with 5 sections. Cadences, tripwires, V-series migrated from BACKLOG.md. | 145 |
| 2026-05-03 | Scheduled Operations populated (SO-001–SO-003). Mechanism constraint table added. | 145 |
